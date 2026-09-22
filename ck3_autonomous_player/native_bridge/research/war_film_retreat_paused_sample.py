"""Research-only paused RPM preparation; not a bridge/MCP capability.

Reads an already-owned process. Never launches, injects, calls native functions,
pauses, advances, or writes CK3 memory. A stable sample proves neither a producer
invocation nor an AI decision. The Windows transport has not been live accepted.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from datetime import datetime, timezone

EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class Sampler:
    def __init__(self, read, base):
        self.read_memory = read
        self.base = base
        self.raw = []

    def read(self, address, size):
        require(0 < address < 0x0000800000000000 and 0 < size <= 32768,
                "invalid read range")
        data = self.read_memory(address, size)
        require(len(data) == size, "short memory read")
        self.raw.append({"address": hex(address), "size": size, "hex": data.hex()})
        return data

    def number(self, address, fmt):
        return struct.unpack("<" + fmt, self.read(address, struct.calcsize(fmt)))[0]

    def pointer(self, address):
        value = self.number(address, "Q")
        require(0 < value < 0x0000800000000000, "null/invalid pointer")
        return value

    def resolve(self, slot, full_id, identity_offset):
        require(0 < full_id <= 0x7fffffff, "invalid full ID")
        storage = self.pointer(self.base + slot)
        count = self.number(storage + 0x2C, "I")
        require((full_id & 0xffffff) < count <= 0x1000000, "store index out of range")
        entries = self.pointer(storage + 0x20)
        obj = self.pointer(entries + (full_id & 0xffffff) * 16 + 8)
        require(self.number(obj + identity_offset, "i") == full_id, "generation mismatch")
        return obj

    def array(self, owner, offset, fmt, limit=4096):
        data = self.number(owner + offset, "Q")
        capacity = self.number(owner + offset + 8, "i")
        count = self.number(owner + offset + 12, "i")
        require(0 <= count <= capacity <= limit, "invalid bounded array")
        size = struct.calcsize(fmt)
        if count == 0:
            return []
        return list(struct.unpack("<" + fmt * count, self.read(data, size * count)))

    def frame(self):
        game = self.pointer(self.base + 0x570E068)
        jomini = self.pointer(self.base + 0x570F7B8)
        paused = self.number(jomini + 0x20, "B")
        require(paused != 0, "requires paused")
        return {"game_state": hex(game), "jomini_state": hex(jomini),
                "date_raw": self.number(game + 8, "i"), "paused_raw": paused}

    def sample(self, subject_id):
        self.raw = []
        before = self.frame()
        unit = self.resolve(0x570CC80, subject_id, 0x10)
        coordinator_id = self.number(unit + 0x1C4, "i")
        coordinator = self.resolve(0x57C07A8, coordinator_id, 0x10)
        require(coordinator != self.number(self.base + 0x57C0798, "Q"), "fallback coordinator")
        require(self.pointer(coordinator) == self.base + 0x41923B0, "coordinator vtable mismatch")
        subunit = self.pointer(unit + 0x1D0)
        require(self.pointer(subunit) == self.base + 0x4192778, "subunit vtable mismatch")
        parent = self.pointer(subunit + 0x40)
        require(self.pointer(parent) == self.base + 0x4191870, "parent vtable mismatch")
        require(self.pointer(parent + 0x58) == coordinator, "parent coordinator mismatch")
        require(self.array(coordinator, 0x50, "Q").count(parent) == 1, "parent membership mismatch")
        require(self.array(parent, 0x40, "Q").count(subunit) == 1, "subunit membership mismatch")
        require(self.array(subunit, 0x10, "i").count(subject_id) == 1, "subject membership mismatch")
        require(self.pointer(coordinator + 0x1B50) == coordinator, "cache backlink mismatch")
        war_id = self.number(coordinator + 0x1C, "i")
        war = self.resolve(0x570C740, war_id, 8)
        flags = self.number(coordinator + 0x68, "H")
        primary_ids = [self.number(war + offset, "i") for offset in (0x288, 0x28C)]
        selected_id = primary_ids[0 if flags & 4 else 1]
        selected = self.resolve(0x570C130, selected_id, 0x18)
        land = self.number(selected + 0x1B8, "Q")
        army_id = self.number(unit + 0x178, "i")
        army = self.resolve(0x570C730, army_id, 0x10)
        cb = self.pointer(war + 0x100)
        values = {
            "frame": before, "subject_full_id": subject_id, "owner_full_id": self.number(unit + 0x174, "i"),
            "army_full_id": army_id, "combat_full_id": self.number(army + 0x128, "i"),
            "raid_raw": self.number(army + 0x1D4, "B"), "barter_raw": self.number(army + 0x1EC, "B"),
            "coordinator_full_id": coordinator_id, "war_full_id": war_id,
            "addresses": {"unit": hex(unit), "subunit": hex(subunit), "parent": hex(parent),
                          "coordinator": hex(coordinator), "war": hex(war)},
            "coordinator_character_ids": self.array(coordinator, 0x20, "i"),
            "flags_68": flags, "side_bit2": bool(flags & 4), "desperate_bit4": bool(flags & 16),
            "stack_count_5c": self.number(coordinator + 0x5C, "i"),
            "threshold_88_q100000": self.number(coordinator + 0x88, "q"),
            "mode_timer_94": self.number(coordinator + 0x94, "i"),
            "score_1b38_raw": self.number(coordinator + 0x1B38, "i"),
            "power_a_1b58": self.number(coordinator + 0x1B58, "q"),
            "power_b_1b60": self.number(coordinator + 0x1B60, "q"),
            "war_primary_288_id": primary_ids[0], "war_primary_28c_id": primary_ids[1],
            "selected_leader_full_id": selected_id,
            "selected_leader_realm_1d0": self.number(land + 0x1D0, "i") if land else None,
            "ghw_bit17": bool(self.number(cb + 0x1718, "I") & (1 << 17)),
            "runtime_thresholds": {name: self.number(self.base + offset, "q") for name, offset in (
                ("normal", 0x570DF68), ("desperate", 0x570DF18),
                ("ghw_attacker", 0x570DF88), ("ghw_defender", 0x570DF80))},
            "runtime_realm_thresholds": self.array(self.base, 0x4F56778, "i", 256),
            "runtime_score_thresholds": self.array(self.base, 0x4F56760, "i", 256),
        }
        require(before == self.frame(), "frame changed during read")
        return {"values": values, "raw_reads": list(self.raw)}


def stable_sample(reader, base, subject_id):
    sampler = Sampler(reader, base)
    completed = []
    try:
        first = sampler.sample(subject_id)
        completed.append(first)
        second = sampler.sample(subject_id)
        completed.append(second)
        require(first == second, "sample changed between reads")
    except (ValueError, OSError) as error:
        error.partial_raw_reads = list(sampler.raw)
        error.completed_samples = completed
        raise
    return {"schema": "xar.war-film-retreat-paused-research.v1",
            "proof_layer": "stable-paused-raw-memory-only", "producer_observed": False,
            "native_choice_proven": False, "semantic_role_mapping_proven": False,
            "samples_equal": True, "samples": [first, second]}


class WindowsReadOnlyProcess:
    """Single-process transport; only query/read access, no native invocation."""
    def __init__(self, pid):
        require(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8, "requires 64-bit Windows")
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k = k
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                               ctypes.POINTER(wintypes.DWORD)]
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.handle = k.OpenProcess(0x1000 | 0x10, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            buf = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(buf))
            require(k.QueryFullProcessImageNameW(self.handle, 0, buf, ctypes.byref(length)), "image path unavailable")
            self.exe = Path(buf.value)
            require(self.exe.name.lower() == "ck3.exe", "target is not ck3.exe")
            require(hashlib.sha256(self.exe.read_bytes()).hexdigest() == EXE_SHA, "exact EXE mismatch")
            times = [wintypes.FILETIME() for _ in range(4)]
            require(k.GetProcessTimes(self.handle, *(ctypes.byref(item) for item in times)), "process times unavailable")
            self.created_filetime = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            self.base = self.module_base(pid)
        except BaseException:
            self.close()
            raise

    def module_base(self, pid):
        class Module(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
                        ("ProccntUsage", wintypes.DWORD), ("modBaseAddr", ctypes.c_void_p),
                        ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
                        ("szModule", wintypes.WCHAR * 256), ("szExePath", wintypes.WCHAR * 260)]
        k = self.k
        k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        k.Module32FirstW.argtypes = k.Module32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Module)]
        snapshot = k.CreateToolhelp32Snapshot(0x8 | 0x10, pid)
        require(snapshot != ctypes.c_void_p(-1).value, "module snapshot failed")
        try:
            module = Module()
            module.dwSize = ctypes.sizeof(module)
            found = k.Module32FirstW(snapshot, ctypes.byref(module))
            while found:
                if Path(module.szExePath).resolve() == self.exe.resolve():
                    return module.modBaseAddr
                found = k.Module32NextW(snapshot, ctypes.byref(module))
            raise ValueError("exact process image module absent")
        finally:
            k.CloseHandle(snapshot)

    def read(self, address, size):
        data = ctypes.create_string_buffer(size)
        count = ctypes.c_size_t()
        require(self.k.ReadProcessMemory(self.handle, address, data, size, ctypes.byref(count)), "RPM failed")
        require(count.value == size, "short RPM")
        return data.raw

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--subject-full-id", type=lambda text: int(text, 0), required=True)
    parser.add_argument("--session-receipt", type=Path, required=True,
                        help="Existing unique-owner managed-session evidence; attached as provenance only.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output already exists")
    receipt = args.session_receipt.read_bytes()
    result = {"schema": "xar.war-film-retreat-paused-attempt.v1", "argv": sys.argv,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(), "pid": args.pid,
              "session_receipt": str(args.session_receipt.resolve()),
              "session_receipt_sha256": hashlib.sha256(receipt).hexdigest(),
              "session_ownership_verified_by_this_tool": False, "production_capability": False,
              "exe_sha256": EXE_SHA, "status": "RED"}
    process = None
    exit_code = 1
    try:
        process = WindowsReadOnlyProcess(args.pid)
        result.update(exe=str(process.exe), module_base=hex(process.base),
                      process_creation_filetime=process.created_filetime)
        result["sample"] = stable_sample(process.read, process.base, args.subject_full_id)
        result["status"] = "STABLE_RAW_SAMPLE"
        exit_code = 0
    except (ValueError, OSError) as error:
        result["error"] = str(error)
        result["partial_raw_reads"] = getattr(error, "partial_raw_reads", [])
        result["completed_samples"] = getattr(error, "completed_samples", [])
    finally:
        if process is not None:
            process.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps({"status": result["status"], "output": str(args.output)}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
