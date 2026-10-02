#!/usr/bin/env python3
"""Locate MilitaryView expense caches by process reads only; research data.

This tool does not own a CK3 session or verify the native before/after frame.
The caller must supply a managed-session receipt and perform those postchecks.
No result from this tool is a war cash receipt or a future-cost upper bound.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

from war_film_retreat_paused_sample import EXE_SHA, WindowsReadOnlyProcess

VIEW_VTABLE_RVA = 0x4135EE0
VIEW_SECONDARY_VTABLE_RVA = 0x4135FB0
PLAYED_CHARACTER_ID_GLOBAL_RVA = 0x4FE7EE0
VIEW_SUBJECT_OFFSET = 0x248
CURRENT_RAW_OFFSET = 0x2E0
CURRENT_SCALE_OFFSET = 0x2E8
CURRENT_BACK_POINTER_OFFSET = 0x2F8
PREDICTED_RAW_OFFSET = 0x740
PREDICTED_SCALE_OFFSET = 0x748
PREDICTED_BACK_POINTER_OFFSET = 0x758
CURRENT_OBJECT_OFFSET = 0x268
PREDICTED_OBJECT_OFFSET = 0x6C8
VIEW_READ_SIZE = 0x760
GOLD_SCALE = 100_000
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_GUARD = 0x100
READABLE_PRIVATE_PROTECTIONS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
MAX_USER_ADDRESS = 0x7FFFFFFFFFFF
SCAN_CHUNK = 1024 * 1024


class MemoryBasicInformation(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("padding0", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("padding1", wintypes.DWORD),
    ]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def _i64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<q", data, offset)[0]


def _decode_candidate(data: bytes, address: int, base: int, player_id: int):
    if len(data) != VIEW_READ_SIZE:
        return None
    checks = (
        _u64(data, 0) == base + VIEW_VTABLE_RVA,
        _u64(data, 0x10) == base + VIEW_SECONDARY_VTABLE_RVA,
        _u32(data, VIEW_SUBJECT_OFFSET) == player_id,
        _u64(data, CURRENT_SCALE_OFFSET) == GOLD_SCALE,
        _u64(data, PREDICTED_SCALE_OFFSET) == GOLD_SCALE,
        _u64(data, CURRENT_BACK_POINTER_OFFSET) == address + CURRENT_OBJECT_OFFSET,
        _u64(data, PREDICTED_BACK_POINTER_OFFSET)
        == address + PREDICTED_OBJECT_OFFSET,
    )
    current_raw = _i64(data, CURRENT_RAW_OFFSET)
    predicted_raw = _i64(data, PREDICTED_RAW_OFFSET)
    if not all(checks) or current_raw < 0 or predicted_raw < 0:
        return None
    return {
        "view_address": hex(address),
        "subject_character_id": player_id,
        "current_monthly_gold_expense_raw_candidate": current_raw,
        "current_monthly_gold_expense_scale": GOLD_SCALE,
        "predicted_all_raised_monthly_gold_expense_raw_candidate": predicted_raw,
        "predicted_all_raised_monthly_gold_expense_scale": GOLD_SCALE,
        "cache_refresh_epoch_observed": False,
        "visible_gui_value_crosschecked": False,
    }


def _private_readable_regions(process: WindowsReadOnlyProcess):
    """Survey VADs before reading bytes so the cap can be chosen on this PID."""
    kernel = process.k
    kernel.VirtualQueryEx.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p,
        ctypes.POINTER(MemoryBasicInformation), ctypes.c_size_t,
    ]
    kernel.VirtualQueryEx.restype = ctypes.c_size_t
    if ctypes.sizeof(MemoryBasicInformation) != 48:
        raise RuntimeError("64-bit MEMORY_BASIC_INFORMATION layout changed")
    position = 0x10000
    regions: list[tuple[int, int]] = []
    total_bytes = 0
    while position < MAX_USER_ADDRESS:
        info = MemoryBasicInformation()
        ctypes.set_last_error(0)
        queried = kernel.VirtualQueryEx(
            process.handle, ctypes.c_void_p(position),
            ctypes.byref(info), ctypes.sizeof(info))
        if queried == 0:
            error = ctypes.get_last_error()
            if error != 87:  # ERROR_INVALID_PARAMETER above user VA range.
                raise OSError(error, "VirtualQueryEx ended before the address-space limit")
            break
        region_start = int(info.BaseAddress or position)
        region_end = region_start + int(info.RegionSize)
        if region_end <= position:
            raise RuntimeError("VirtualQueryEx failed to advance")
        position = region_end
        if (info.State != MEM_COMMIT or info.Type != MEM_PRIVATE
                or info.Protect & PAGE_GUARD
                or (info.Protect & 0xFF) not in READABLE_PRIVATE_PROTECTIONS):
            continue
        regions.append((region_start, region_end))
        total_bytes += int(info.RegionSize)
    return regions, total_bytes


def _scan(process: WindowsReadOnlyProcess, player_id: int, max_bytes: int,
          regions: list[tuple[int, int]], total_bytes: int):
    if total_bytes > max_bytes:
        return {
            "private_regions_considered": len(regions),
            "private_readable_bytes_surveyed": total_bytes,
            "largest_region_bytes": max(
                (end - start for start, end in regions), default=0),
            "minimum_full_scan_ceiling_mib":
                (total_bytes + 1024 * 1024 - 1) // (1024 * 1024),
            "private_bytes_read": 0,
            "unreadable_bytes": 0,
            "vtable_marker_hits": 0,
            "structurally_matching_views": [],
            "scan_complete": False,
            "scan_budget_insufficient": True,
        }
    marker = struct.pack("<Q", process.base + VIEW_VTABLE_RVA)
    scanned_bytes = 0
    unreadable_bytes = 0
    hits: set[int] = set()
    for region_start, region_end in regions:
        offset = region_start
        tail = b""
        while offset < region_end:
            size = min(SCAN_CHUNK, region_end - offset)
            try:
                chunk = process.read(offset, size)
            except (OSError, ValueError):
                unreadable_bytes += size
                tail = b""
                offset += size
                continue
            scanned_bytes += size
            joined = tail + chunk
            first_address = offset - len(tail)
            cursor = 0
            while True:
                found = joined.find(marker, cursor)
                if found < 0:
                    break
                address = first_address + found
                if address % 8 == 0:
                    hits.add(address)
                cursor = found + 1
            tail = joined[-7:]
            offset += size
    candidates = []
    for address in sorted(hits):
        try:
            first = process.read(address, VIEW_READ_SIZE)
            second = process.read(address, VIEW_READ_SIZE)
        except (OSError, ValueError):
            unreadable_bytes += VIEW_READ_SIZE
            continue
        if first != second:
            unreadable_bytes += VIEW_READ_SIZE
            continue
        candidate = _decode_candidate(first, address, process.base, player_id)
        if candidate is not None:
            candidates.append(candidate)
    return {
        "private_regions_considered": len(regions),
        "private_readable_bytes_surveyed": total_bytes,
        "largest_region_bytes": max(
            (end - start for start, end in regions), default=0),
        "private_bytes_read": scanned_bytes,
        "unreadable_bytes": unreadable_bytes,
        "vtable_marker_hits": len(hits),
        "structurally_matching_views": candidates,
        "scan_complete": unreadable_bytes == 0,
        "scan_budget_insufficient": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--expected-player-id", type=int, required=True)
    parser.add_argument("--session-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-private-mib", type=int, default=8192)
    parser.add_argument("--survey-only", action="store_true",
                        help="enumerate readable private VADs without reading them")
    args = parser.parse_args()
    if (args.pid <= 0 or args.expected_player_id <= 0
            or not 0 < args.max_private_mib <= 32768):
        parser.error("PID/player ID must be positive; scan ceiling must be 1..32768 MiB")
    if args.output.exists() or not args.session_receipt.is_file():
        parser.error("output must be new and managed-session receipt must exist")
    receipt_sha = hashlib.sha256(args.session_receipt.read_bytes()).hexdigest().upper()
    output = {
        "schema": "xar.ck3.war-cash-passive-military-view-sample.v1",
        "status": "RED",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "pid": args.pid,
        "expected_player_id": args.expected_player_id,
        "max_private_mib": args.max_private_mib,
        "session_receipt": str(args.session_receipt.resolve()),
        "session_receipt_sha256": receipt_sha,
        "session_ownership_verified_by_this_tool": False,
        "same_frame_binding_verified_by_this_tool": False,
        "cash_receipt_eligible": False,
        "future_cost_upper_bound_proven": False,
        "game_code_called": False,
        "game_memory_written": False,
    }
    process = None
    try:
        process = WindowsReadOnlyProcess(args.pid)
        output.update(
            process_exe=str(process.exe),
            process_exe_sha256=EXE_SHA.upper(),
            module_base=hex(process.base),
            process_creation_filetime=process.created_filetime,
        )
        global_player_id = _u32(
            process.read(process.base + PLAYED_CHARACTER_ID_GLOBAL_RVA, 4), 0)
        output["global_played_character_id"] = global_player_id
        if global_player_id != args.expected_player_id:
            raise ValueError("global player ID differs from expected paused frame")
        regions, total_bytes = _private_readable_regions(process)
        output["private_readable_survey"] = {
            "region_count": len(regions),
            "total_bytes": total_bytes,
            "largest_region_bytes": max(
                (end - start for start, end in regions), default=0),
            "minimum_full_scan_ceiling_mib":
                (total_bytes + 1024 * 1024 - 1) // (1024 * 1024),
        }
        if args.survey_only:
            output["status"] = "private_readable_survey_only"
        else:
            sample = _scan(process, global_player_id,
                           args.max_private_mib * 1024 * 1024,
                           regions, total_bytes)
            output["scan"] = sample
            count = len(sample["structurally_matching_views"])
            output["status"] = (
                "scan_budget_insufficient"
                if sample["scan_budget_insufficient"]
                else "diagnostic_unique_cache_candidate"
                if sample["scan_complete"] and count == 1
                else "missing_or_ambiguous_cache_candidate")
    except (OSError, RuntimeError, ValueError) as error:
        output["error"] = str(error)
    finally:
        if process is not None:
            process.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(output, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps({"status": output["status"], "output": str(args.output)}))
    return 0 if output["status"] in {
        "diagnostic_unique_cache_candidate", "private_readable_survey_only"
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
