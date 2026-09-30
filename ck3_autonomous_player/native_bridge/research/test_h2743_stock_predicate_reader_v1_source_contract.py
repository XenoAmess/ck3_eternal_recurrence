"""Fresh disk/source binding fixture; no compiler, game or native call.

The separate C++ fake-memory fixture tests production reader behavior only after
the integration owner authorizes a build. This fixture does not imply that run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class DiskPe:
    def __init__(self, path: Path):
        self.stream = path.open("rb")
        self.stream.seek(0x3C)
        pe_offset = struct.unpack("<I", self.stream.read(4))[0]
        self.stream.seek(pe_offset)
        if self.stream.read(4) != b"PE\0\0":
            raise ValueError("not a PE executable")
        coff = self.stream.read(20)
        machine, count = struct.unpack_from("<HH", coff)
        optional_size = struct.unpack_from("<H", coff, 16)[0]
        optional = self.stream.read(optional_size)
        if machine != 0x8664 or struct.unpack_from("<H", optional)[0] != 0x20B:
            raise ValueError("not AMD64 PE32+")
        self.image_base = struct.unpack_from("<Q", optional, 24)[0]
        self.sections = []
        for _ in range(count):
            row = self.stream.read(40)
            virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", row, 8)
            self.sections.append((rva, max(virtual_size, raw_size), raw_offset, raw_size))

    def read(self, rva: int, size: int) -> bytes:
        for start, extent, raw_offset, raw_size in self.sections:
            if start <= rva and rva + size <= start + extent:
                offset = rva - start
                if offset + size > raw_size:
                    raise ValueError("disk fixture requested virtual-only bytes")
                self.stream.seek(raw_offset + offset)
                value = self.stream.read(size)
                if len(value) != size:
                    raise ValueError("short disk read")
                return value
        raise ValueError(f"unmapped RVA {rva:#x}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--ck3-executable", type=Path, required=True)
    parser.add_argument("--game-data-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit("report already exists; use a fresh attempt")
    native = args.root / "ck3_autonomous_player/native_bridge"
    abi_path = native / "research/h2743_stock_predicate_reader_v1_abi.json"
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    checks = []

    def check(label: str, condition: bool):
        checks.append({"label": label, "passed": bool(condition)})

    check("exact executable SHA", sha(args.ck3_executable) == abi["executable_sha256"])
    pe = DiskPe(args.ck3_executable)
    for row in abi["disk_proofs"]:
        rva = int(row["rva"], 16)
        if "bytes" in row:
            expected = bytes.fromhex(row["bytes"])
            check(row["name"], pe.read(rva, len(expected)) == expected)
        elif "target_rva" in row:
            value = struct.unpack("<Q", pe.read(rva, 8))[0]
            check(row["name"], value - pe.image_base == int(row["target_rva"], 16))
        else:
            check(row["name"], hashlib.sha256(pe.read(rva, row["size"])).hexdigest().upper()
                  == row["sha256"])
    for row in abi["stock_script_inputs"]:
        check(row["path"] + " exact SHA", sha(args.game_data_root / row["path"]) == row["sha256"])
    texts = {}
    source_hashes = []
    for relative in abi["candidate_source_paths"]:
        path = native / relative
        source_hashes.append({"path": relative, "size": path.stat().st_size, "sha256": sha(path)})
        texts[relative] = path.read_text(encoding="utf-8-sig")
    core = texts["src/h2743_stock_predicate_reader_v1.cpp"]
    adapter = texts["src/h2743_stock_native_source_adapter_v1.cpp"]
    header = texts["include/xar_bridge/h2743_stock_predicate_reader_v1.hpp"]
    fragment = texts["cmake/h2743_stock_predicate_reader_v1.cmake"]
    check("default OFF macro", "#define XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 0" in adapter)
    check("default OFF option", 'sources" OFF)' in fragment)
    check("full identity comparison", "actual != id" in core)
    check("uint64 cache dirty guard", "std::uint64_t dirty = 1" in core and "dirty == 0" in core)
    check("independent parameter bindings", "short_bound" in core and "long_bound" in core)
    check("CB writer/mode before and after", core.count("Read(owner + 0xEB8, lock_state)") == 2
          and core.count("Read(owner + 0xEF8, lock_mode)") == 2)
    check("full CB name and exact vptr", "DefinitionName(definition, kBorderRaidName)" in core
          and "vtable != b.module_base + kCbVtable" in core)
    check("double byte journal and real stamp", "first.journal != second.journal" in core
          and core.count("MatchingStamp(bindings, expected)") == 3)
    check("private material remains incomplete", "material_complete = false" in header
          and "material_complete = true" not in core)
    check("actual process read", "ReadProcessMemory(GetCurrentProcess()" in adapter)
    check("owner thread checked", "application_main_thread_id != GetCurrentThreadId()" in adapter)
    check("borrowed name exact roundtrip", "IdentifierRoundTripV1" in adapter
          and "std::memcmp(&header, &after, sizeof(header)) == 0" in adapter)
    check("no interner/evaluator/lock-mutating getter call", all(
        token not in adapter + core for token in
        ("0x3B58330", "0x334C510", "0x334C600", "0x2D05950;", "0x88E260", "0x2024E40;")))
    passed = sum(row["passed"] for row in checks)
    report = {
        "schema": "xar.ck3.h2743.stock_reader_source_fixture.v1",
        "status": "GREEN_DISK_SOURCE_BINDING" if passed == len(checks) else "RED_DISK_SOURCE_BINDING",
        "python": sys.executable, "python_version": sys.version,
        "source_root": str(args.root), "abi_sha256": sha(abi_path),
        "executable": str(args.ck3_executable), "executable_sha256": sha(args.ck3_executable),
        "checks_passed": passed, "checks_total": len(checks), "checks": checks,
        "source_hashes": source_hashes,
        "native_build": False, "cpp_behavior_fixture_executed": False,
        "ck3_launched": False, "runtime_predicate_observed": False,
        "action": None,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "passed": passed, "total": len(checks),
                      "report": str(args.report), "sha256": sha(args.report)}))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
