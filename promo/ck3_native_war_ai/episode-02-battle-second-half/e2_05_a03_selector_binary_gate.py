#!/usr/bin/env python3
"""Read-only byte admission for a fresh E2-05 a03 selector DLL candidate.

This never starts CK3, installs a hook, advances time or approves a live run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

from e2_05_a03_no_screen_gate import (
    CK3_SHA,
    GateRed,
    _pin,
    _require,
    source_gate,
)


SELECTOR_RVA = 0x33E8D40
SELECTOR_PROLOGUE = bytes.fromhex("4C89442418488954241048894C2408")
REQUIRED_TESTS = frozenset({
    "xar_ck3_native_bridge_combat_v3_source_contract",
    "xar_ck3_native_bridge_combat_phase_event_trace_v1_source_contract",
    "xar_ck3_native_bridge_combat_phase_event_trace_ring_v1",
    "xar_ck3_native_bridge_combat_phase_event_trace_detour_v1",
    "xar_ck3_native_bridge_combat_phase_event_trace_wire_v1",
    "xar_ck3_native_bridge_combat_phase_event_trace_managed_v1",
})


def pe_machine_and_rva(raw: bytes, rva: int | None = None,
                       count: int = 0) -> tuple[int, bytes | None]:
    _require(len(raw) >= 0x40 and raw[:2] == b"MZ", "missing PE DOS header")
    header = struct.unpack_from("<I", raw, 0x3C)[0]
    _require(header + 24 <= len(raw) and raw[header:header + 4] == b"PE\0\0",
             "missing PE signature")
    machine, sections = struct.unpack_from("<HH", raw, header + 4)
    optional_size = struct.unpack_from("<H", raw, header + 20)[0]
    optional = header + 24
    _require(machine == 0x8664 and sections > 0 and
             optional + optional_size + sections * 40 <= len(raw) and
             struct.unpack_from("<H", raw, optional)[0] == 0x20B,
             "candidate is not a complete x64 PE32+ image")
    if rva is None:
        return machine, None
    _require(count > 0, "RVA read requires positive byte count")
    section_start = optional + optional_size
    for index in range(sections):
        entry = section_start + index * 40
        _, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", raw, entry + 8)
        if virtual_address <= rva and rva + count <= virtual_address + raw_size:
            offset = raw_offset + rva - virtual_address
            _require(offset + count <= len(raw), "PE RVA exceeds file bytes")
            return machine, raw[offset:offset + count]
    raise GateRed("selector RVA is not backed by exact executable file bytes")


def source_fingerprint(root: Path) -> str:
    """Match native_bridge/tools/build_fresh.py's source-tree fingerprint."""
    root = root.resolve()
    paths = [root / "CMakeLists.txt"]
    for tree_name in ("include", "src"):
        paths.extend(path for path in (root / tree_name).rglob("*")
                     if path.is_file() and path.suffix.lower() in
                     {".cpp", ".hpp", ".h", ".c"})
    _require(all(path.is_file() and not path.is_symlink() for path in paths),
             "native source tree is incomplete or linked")
    lines = []
    for path in sorted(paths, key=lambda value: str(value.resolve()).lower()):
        relative = str(path.resolve())[len(str(root)):].lstrip("\\/")
        lines.append(f"{relative}\0{hashlib.sha256(path.read_bytes()).hexdigest().upper()}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest().upper()


def checked_cache(cache: Path, exe: Path, source_root: Path,
                  expected_sha: str) -> dict[str, object]:
    cache_pin = _pin(cache, expected_sha)
    raw = cache.read_bytes()
    _require(hashlib.sha256(raw).hexdigest().upper() == expected_sha,
             "CMakeCache bytes changed after pin")
    values: dict[str, str] = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if line.startswith("//") or line.startswith("#") or "=" not in line:
            continue
        key_type, value = line.split("=", 1)
        key = key_type.split(":", 1)[0]
        values[key] = value
    _require(values.get("CMAKE_BUILD_TYPE") == "Release" and
             values.get("BUILD_TESTING") == "ON" and
             values.get("XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1") == "ON",
             "fresh build lacks Release/testing/managed selector flags")
    configured_exe = values.get("XAR_CK3_EXECUTABLE_PATH", "")
    _require(bool(configured_exe) and
             Path(configured_exe).resolve() == exe.resolve(),
             "fresh build exact CK3 executable binding differs")
    _require(Path(values.get("CMAKE_HOME_DIRECTORY", "")).resolve() ==
             source_root.resolve(), "fresh build source directory differs")
    return {"cache": cache_pin, **{key: values[key] for key in (
        "CMAKE_BUILD_TYPE", "BUILD_TESTING",
        "XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1",
        "XAR_CK3_EXECUTABLE_PATH")}}


def checked_junit(path: Path, expected_sha: str,
                  build: Path) -> dict[str, object]:
    _require(path.resolve().parent == build.resolve(),
             "focused CTest JUnit is outside exact candidate build directory")
    junit_pin = _pin(path, expected_sha)
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest().upper() == expected_sha,
             "focused CTest JUnit bytes changed after pin")
    root = ET.fromstring(raw)
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    _require(bool(suites), "JUnit has no test suite")
    cases = [case for suite in suites for case in suite.findall("testcase")]
    names = [case.attrib.get("name", "") for case in cases]
    _require(len(names) == len(REQUIRED_TESTS) and set(names) == REQUIRED_TESTS and
             all(case.attrib.get("status") == "run" and
                 not any(child.tag in {"failure", "error", "skipped"}
                         for child in case) for case in cases) and
             all(suite.attrib.get("failures", "0") == "0" and
                 suite.attrib.get("errors", "0") == "0" and
                 suite.attrib.get("skipped", "0") == "0" and
                 suite.attrib.get("disabled", "0") == "0" for suite in suites),
             "focused native CTest names/results are incomplete or RED")
    return {"tests": sorted(names), "junit": junit_pin}


def candidate_gate(*, save: Path, receipt: Path, exe: Path, build_dir: Path,
                   source_root: Path, expected_source_fingerprint: str,
                   expected_cache_sha: str, expected_junit_sha: str,
                   expected_dll_sha: str, expected_injector_sha: str,
                   junit: Path) -> dict[str, object]:
    build = build_dir.resolve()
    dll = build / "xar_ck3_bridge.dll"
    injector = build / "xar_ck3_bridge_injector.exe"
    source = source_gate(save, receipt, dll, injector,
                         expected_dll_sha, expected_injector_sha)
    exe_pin = _pin(exe, CK3_SHA)
    exe_bytes = exe.read_bytes()
    _require(hashlib.sha256(exe_bytes).hexdigest().upper() == CK3_SHA,
             "executable bytes changed after pin")
    _, prologue = pe_machine_and_rva(exe_bytes, SELECTOR_RVA,
                                     len(SELECTOR_PROLOGUE))
    _require(prologue == SELECTOR_PROLOGUE,
             "exact selector prologue bytes differ at RVA 0x33E8D40")
    dll_bytes = dll.read_bytes()
    injector_bytes = injector.read_bytes()
    _require(hashlib.sha256(dll_bytes).hexdigest().upper() == expected_dll_sha and
             hashlib.sha256(injector_bytes).hexdigest().upper() == expected_injector_sha,
             "candidate bytes changed after pin")
    pe_machine_and_rva(dll_bytes)
    pe_machine_and_rva(injector_bytes)
    _require(b"knight_selects" in dll_bytes,
             "candidate DLL lacks the selector wire key")
    cache = checked_cache(build / "CMakeCache.txt", exe, source_root,
                          expected_cache_sha)
    fingerprint = source_fingerprint(source_root)
    _require(fingerprint == expected_source_fingerprint,
             "native source fingerprint differs from frozen build source")
    tests = checked_junit(junit, expected_junit_sha, build)
    return {
        **source,
        "exact_exe": exe_pin,
        "selector_rva": SELECTOR_RVA,
        "selector_prologue_hex": SELECTOR_PROLOGUE.hex().upper(),
        "candidate_pe_machine": "AMD64",
        "selector_wire_key_present": True,
        "cmake": cache,
        "native_source_root": str(source_root.resolve()),
        "native_source_fingerprint_sha256": fingerprint,
        "focused_tests": tests,
        "selector_abi_static_bytes_checked": True,
        "selector_abi_reviewed": False,
        "postframe_character_status": "UNKNOWN",
        "live_admission": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-source-fingerprint", required=True)
    parser.add_argument("--expected-cache-sha256", required=True)
    parser.add_argument("--expected-junit-sha256", required=True)
    parser.add_argument("--expected-dll-sha256", required=True)
    parser.add_argument("--expected-injector-sha256", required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        help="Create-exclusive external JSON receipt")
    args = parser.parse_args()
    try:
        result = candidate_gate(
            save=args.save, receipt=args.receipt, exe=args.exe,
            build_dir=args.build_dir,
            source_root=args.source_root,
            expected_source_fingerprint=args.expected_source_fingerprint,
            expected_cache_sha=args.expected_cache_sha256,
            expected_junit_sha=args.expected_junit_sha256,
            expected_dll_sha=args.expected_dll_sha256,
            expected_injector_sha=args.expected_injector_sha256,
            junit=args.junit)
    except (GateRed, OSError, ValueError, ET.ParseError, struct.error) as error:
        print(json.dumps({"status": "RED", "live_admission": False,
                          "reason": str(error)}))
        return 2
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        try:
            with args.output.open("x", encoding="utf-8") as target:
                target.write(serialized)
        except OSError as error:
            print(json.dumps({"status": "RED", "live_admission": False,
                              "reason": str(error)}))
            return 2
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
