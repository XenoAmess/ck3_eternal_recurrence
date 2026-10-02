#!/usr/bin/env python3
"""Read one exact CHudTopBar owner path and expense cache without a VAD scan.

The caller must own a managed paused CK3 session and separately verify the
native frame before and after this script. No output is a formal cash receipt.
Only an exact EXE, ReadProcessMemory transport, and at most 128 KiB of target
memory across two samples are permitted here. No native GUI getter is called.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

from war_cash_topbar_owner_path import (
    GLOBAL_OWNER_SLOT_RVA, HANDLER_PRIMARY_VTABLE_RVA,
    HANDLER_SECONDARY_VTABLE_RVA, IDLER_PRIMARY_VTABLE_RVA,
    TOPBAR_READ_SIZE, _address,
    inspect_supplied_topbar_owner_path,
)
from war_cash_topbar_passive_layout import (
    MAX_DIAGNOSTIC_ROWS, ROW_STRIDE,
    inspect_supplied_topbar_expense_bytes,
)
from war_cash_topbar_render_epoch import (
    EXPENSE_REFRESH_INTERVAL_RVA, RENDER_CONTEXT_READ_SIZE,
    RENDER_CONTEXT_SLOT_RVA, inspect_supplied_topbar_render_epoch,
)
from war_film_retreat_paused_sample import EXE_SHA, WindowsReadOnlyProcess


MAX_SAMPLE_READ_BYTES = 64 * 1024
# Exact EXE getter refresh reads this DWORD; also pinned by the static verifier.
PLAYED_CHARACTER_ID_GLOBAL_RVA = 0x4FE7EE0


class BoundedReader:
    def __init__(self, process: object) -> None:
        self.process = process
        self.total = 0
        self.reads = 0

    def read(self, address: int, size: int) -> bytes:
        _address(address, "read target")
        if (type(size) is not int or size <= 0
                or address + size > 0x0000800000000000
                or self.total + size > MAX_SAMPLE_READ_BYTES):
            raise ValueError("bounded topbar sample read limit exceeded")
        data = self.process.read(address, size)
        if type(data) is not bytes or len(data) != size:
            raise ValueError("bounded topbar sample read returned short bytes")
        self.total += size
        self.reads += 1
        return data


def sample_bounded_topbar_once(process: object) -> dict[str, object]:
    """Read only five exact owner blocks, then bounded expense rows/names."""
    base = _address(process.base, "module image base")
    reader = BoundedReader(process)
    slot = base + GLOBAL_OWNER_SLOT_RVA
    slot_bytes = reader.read(slot, 8)
    owner = _address(struct.unpack_from("<Q", slot_bytes)[0], "global owner")
    owner_bytes = reader.read(owner, 0x18)
    idler = _address(struct.unpack_from("<Q", owner_bytes, 0x10)[0], "ingame idler")
    idler_bytes = reader.read(idler, 0x90)
    if struct.unpack_from("<Q", idler_bytes)[0] != base + IDLER_PRIMARY_VTABLE_RVA:
        raise ValueError("idler vtable changed before following handler pointer")
    handler = _address(struct.unpack_from("<Q", idler_bytes, 0x88)[0], "ingame handler")
    handler_bytes = reader.read(handler, 0x478)
    if (struct.unpack_from("<Q", handler_bytes)[0]
            != base + HANDLER_PRIMARY_VTABLE_RVA
            or struct.unpack_from("<Q", handler_bytes, 0x58)[0]
            != base + HANDLER_SECONDARY_VTABLE_RVA):
        raise ValueError("handler vtables changed before following topbar pointer")
    topbar = _address(struct.unpack_from("<Q", handler_bytes, 0x470)[0], "topbar")
    topbar_bytes = reader.read(topbar, TOPBAR_READ_SIZE)
    owner_path = inspect_supplied_topbar_owner_path(
        image_base=base, global_slot_address=slot,
        global_slot_bytes=slot_bytes,
        global_owner_address=owner, global_owner_bytes=owner_bytes,
        idler_address=idler, idler_bytes=idler_bytes,
        handler_address=handler, handler_bytes=handler_bytes,
        topbar_address=topbar, topbar_bytes=topbar_bytes,
    )
    player_slot = base + PLAYED_CHARACTER_ID_GLOBAL_RVA
    player_before = struct.unpack("<I", reader.read(player_slot, 4))[0]
    if not 0 < player_before <= 0x7FFFFFFF:
        raise ValueError("global played CharacterID is unavailable")
    result: dict[str, object] = {
        "schema": "xar.ck3.war-cash-topbar-bounded-sample.v1",
        "status": "owner_path_structurally_matching_expense_unavailable",
        "owner_path": owner_path,
        "expense_layout": None,
        "expense_missing_reason": "expense_row_vector_not_checked",
        "render_epoch": None,
        "render_epoch_missing_reason": "render_clock_not_checked",
        "unique_live_topbar_instance_proven": False,
        "same_frame_cache_freshness_proven": False,
        "formal_cash_eligible": False,
    }
    # Preserve only the already-read vector header. A rejected pointer or an
    # empty vector cannot be recovered from the generic _address error later.
    row_array_candidate = struct.unpack_from("<Q", topbar_bytes, 0xAD8)[0]
    row_capacity_candidate, row_count_candidate = struct.unpack_from(
        "<II", topbar_bytes, 0xAE0)
    expense_object_address = topbar + 0xAD8
    expense_back_pointer_candidate = struct.unpack_from(
        "<Q", topbar_bytes, 0xB68)[0]
    expense_total_signed_raw_candidate = struct.unpack_from(
        "<q", topbar_bytes, 0xB50)[0]
    expense_total_scale_candidate = struct.unpack_from(
        "<Q", topbar_bytes, 0xB58)[0]
    result["expense_header_diagnostic"] = {
        "row_array_address_candidate": hex(row_array_candidate),
        "row_array_pointer_class": (
            "zero" if row_array_candidate == 0 else
            "outside_user_range" if not 0x10000 <= row_array_candidate
            < 0x0000800000000000 else
            "unaligned" if row_array_candidate % 8 else
            "aligned_user_address_candidate"
        ),
        "row_capacity_candidate": row_capacity_candidate,
        "row_count_candidate": row_count_candidate,
        "expense_object_address_candidate": hex(expense_object_address),
        "value_breakdown_back_pointer_candidate": hex(
            expense_back_pointer_candidate),
        "back_pointer_matches_expense_object_candidate": (
            expense_back_pointer_candidate == expense_object_address),
        "expense_total_signed_raw_candidate": expense_total_signed_raw_candidate,
        "expense_total_scale_candidate": expense_total_scale_candidate,
        "total_scale_matches_q100000_candidate": (
            expense_total_scale_candidate == 100_000),
        "formal_cash_eligible": False,
    }
    try:
        row_array = _address(row_array_candidate, "expense row array")
        capacity, count = row_capacity_candidate, row_count_candidate
        if not 0 < count <= capacity <= MAX_DIAGNOSTIC_ROWS:
            raise ValueError("expense row vector count/capacity is invalid")
        rows = reader.read(row_array, count * ROW_STRIDE)
        names: dict[int, bytes] = {}
        for index in range(count):
            row = rows[index * ROW_STRIDE:(index + 1) * ROW_STRIDE]
            length, capacity = struct.unpack_from("<QQ", row, 0x28)
            if not 0 < length <= 127 or capacity < length:
                raise ValueError("expense row name length/capacity is invalid")
            if capacity > 15:
                address = _address(struct.unpack_from("<Q", row, 0x18)[0],
                                   "expense row name")
                names[address] = reader.read(address, length + 1)
        result["expense_layout"] = inspect_supplied_topbar_expense_bytes(
            image_base=base, topbar_address=topbar,
            topbar_bytes=topbar_bytes, row_array_address=row_array,
            row_bytes=rows, name_payloads=names,
        )
        result["expense_missing_reason"] = None
        result["status"] = "supplied_owner_and_expense_bytes_structurally_matching"
    except (OSError, ValueError, struct.error) as error:
        result["expense_missing_reason"] = str(error)
    result["render_header_diagnostic"] = {
        "topbar_last_update_tick_candidate": struct.unpack_from(
            "<Q", topbar_bytes, 0xF88)[0],
        "formal_cash_eligible": False,
    }
    try:
        render_slot = base + RENDER_CONTEXT_SLOT_RVA
        slot_bytes = reader.read(render_slot, 8)
        render_context_candidate = struct.unpack("<Q", slot_bytes)[0]
        result["render_header_diagnostic"][
            "render_context_address_candidate"] = hex(render_context_candidate)
        render_context = _address(render_context_candidate, "render context")
        context_bytes = reader.read(render_context, RENDER_CONTEXT_READ_SIZE)
        result["render_header_diagnostic"][
            "current_render_tick_candidate"] = struct.unpack_from(
                "<Q", context_bytes, 0x180)[0]
        interval_address = base + EXPENSE_REFRESH_INTERVAL_RVA
        interval_bytes = reader.read(interval_address, 4)
        result["render_header_diagnostic"][
            "stock_refresh_interval_render_ticks_candidate"] = struct.unpack(
                "<i", interval_bytes)[0]
        result["render_epoch"] = inspect_supplied_topbar_render_epoch(
            image_base=base, topbar_bytes=topbar_bytes,
            render_context_slot_address=render_slot,
            render_context_slot_bytes=slot_bytes,
            render_context_address=render_context,
            render_context_bytes=context_bytes,
            refresh_interval_address=interval_address,
            refresh_interval_bytes=interval_bytes,
        )
        result["render_epoch_missing_reason"] = None
    except (KeyError, OSError, ValueError, struct.error) as error:
        result["render_epoch_missing_reason"] = str(error)
    player_after = struct.unpack("<I", reader.read(player_slot, 4))[0]
    if player_after != player_before:
        raise ValueError("global played CharacterID changed during topbar sample")
    result["global_played_character_id_candidate"] = player_before
    result["global_played_character_id_stable_within_sample"] = True
    result["target_memory_bytes_read"] = reader.total
    result["target_memory_read_calls"] = reader.reads
    return result


def sample_bounded_topbar_twice(process: object) -> dict[str, object]:
    first = sample_bounded_topbar_once(process)
    second = sample_bounded_topbar_once(process)
    owner_addresses = (
        "global_owner_address", "idler_address", "handler_address",
        "topbar_address", "topbar_context_address",
    )
    same_owner_path = all(
        first["owner_path"][key] == second["owner_path"][key]
        for key in owner_addresses
    )
    same_owner_path_bytes = (
        first["owner_path"]["supplied_bytes_sha256"]
        == second["owner_path"]["supplied_bytes_sha256"]
    )
    same_player_id = (
        first["global_played_character_id_candidate"]
        == second["global_played_character_id_candidate"]
    )
    first_expense = first.get("expense_layout")
    second_expense = second.get("expense_layout")
    same_expense_rows = (
        isinstance(first_expense, dict)
        and isinstance(second_expense, dict)
        and first_expense.get("row_array_address")
        == second_expense.get("row_array_address")
        and first_expense.get("row_array_sha256")
        == second_expense.get("row_array_sha256")
        and first_expense.get("expense_total_signed_raw_candidate")
        == second_expense.get("expense_total_signed_raw_candidate")
        and first_expense.get("rows") == second_expense.get("rows")
    )
    first_epoch = first.get("render_epoch")
    second_epoch = second.get("render_epoch")
    render_clock_monotonic = (
        isinstance(first_epoch, dict)
        and isinstance(second_epoch, dict)
        and first_epoch.get("render_context_address")
        == second_epoch.get("render_context_address")
        and type(first_epoch.get("current_render_tick_candidate")) is int
        and type(second_epoch.get("current_render_tick_candidate")) is int
        and first_epoch["current_render_tick_candidate"]
        <= second_epoch["current_render_tick_candidate"]
    )
    return {
        "schema": "xar.ck3.war-cash-topbar-bounded-double-read.v1",
        "status": ("stable_supplied_bytes_diagnostic_only"
                   if same_owner_path and same_owner_path_bytes
                   and same_player_id
                   and same_expense_rows
                   else "RED_owner_or_expense_bytes_changed_or_unavailable"),
        "first": first,
        "second": second,
        "same_owner_path_addresses": same_owner_path,
        "same_owner_path_bytes": same_owner_path_bytes,
        "same_global_played_character_id": same_player_id,
        "same_expense_rows": same_expense_rows,
        "render_clock_monotonic_candidate": render_clock_monotonic,
        "total_target_memory_bytes_read": (
            first["target_memory_bytes_read"]
            + second["target_memory_bytes_read"]),
        "unique_live_topbar_instance_proven": False,
        "same_frame_cache_freshness_proven": False,
        "monthly_war_cash_rate_proven": False,
        "formal_cash_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--session-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pid <= 0 or not args.session_receipt.is_file() or args.output.exists():
        parser.error("positive PID, existing session receipt and new output required")
    if args.session_receipt.stat().st_size > 1024 * 1024:
        parser.error("managed-session receipt exceeds 1 MiB")
    output: dict[str, object] = {
        "schema": "xar.ck3.war-cash-topbar-bounded-process-diagnostic.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "pid": args.pid,
        "session_receipt": str(args.session_receipt.resolve()),
        "session_receipt_sha256": hashlib.sha256(
            args.session_receipt.read_bytes()).hexdigest().upper(),
        "status": "RED",
        "same_native_frame_before_after_proven_by_this_tool": False,
        "session_screen_ownership_proven_by_this_tool": False,
        "native_dll_injector_pair_proven_by_this_tool": False,
        "player_war_binding_proven_by_this_tool": False,
        "game_code_called": False,
        "game_memory_written": False,
        "formal_cash_eligible": False,
    }
    process = None
    try:
        process = WindowsReadOnlyProcess(args.pid)
        output.update(
            process_exe=str(process.exe),
            process_exe_sha256=EXE_SHA.upper(),
            process_created_filetime=process.created_filetime,
            module_image_base=hex(process.base),
            diagnostic=sample_bounded_topbar_twice(process),
        )
        output["status"] = output["diagnostic"]["status"]
    except (OSError, ValueError, RuntimeError, struct.error) as error:
        output["error"] = f"{type(error).__name__}: {error}"
    finally:
        if process is not None:
            process.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(args.output)
    return 0 if output["status"] == "stable_supplied_bytes_diagnostic_only" else 2


if __name__ == "__main__":
    raise SystemExit(main())
