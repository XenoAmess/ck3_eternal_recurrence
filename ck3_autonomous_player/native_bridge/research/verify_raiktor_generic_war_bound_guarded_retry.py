#!/usr/bin/env python3
"""Verify a guarded generic war-bound retry candidate without launching CK3."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Iterable


OPTION = "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1"
STAGE_RECORDER_OPTION = "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1"
GUARD_ORDER = (
    "InstallStartupParticle2NullGuardV1",
    "InstallStartupParticle2ConsumerGuardV1",
    "InstallStartupDx11RenderContextDrawGuardV1",
    "InstallStartupLocalizeCurrentRootGuardV1",
)
STRICT_LAYERS = ["child", "aggregate", "session", "cache"]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _cmake_cache(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "//")) or "=" not in line:
            continue
        typed_name, value = line.split("=", 1)
        name = typed_name.split(":", 1)[0]
        values[name] = value.strip()
    return values


def _default_inventory() -> list[dict[str, object]]:
    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.c_void_p),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel32.Process32FirstW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessEntry32W),
    ]
    kernel32.Process32FirstW.restype = ctypes.c_int
    kernel32.Process32NextW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessEntry32W),
    ]
    kernel32.Process32NextW.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if snapshot == invalid_handle:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    rows: list[dict[str, object]] = []
    entry = ProcessEntry32W()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        present = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while present:
            name = entry.szExeFile.strip().lower()
            if name in {"ck3.exe", "xar_ck3_bridge_injector.exe"}:
                rows.append({"name": name, "pid": int(entry.th32ProcessID)})
            present = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    return rows


def _in_order(text: str, tokens: Iterable[str]) -> bool:
    cursor = -1
    for token in tokens:
        cursor = text.find(token, cursor + 1)
        if cursor < 0:
            return False
    return True


def _source_checks(cmake_text: str, bridge_text: str) -> dict[str, bool]:
    compact_cmake = re.sub(r"\s+", " ", cmake_text)
    option_default_off = re.search(
        rf"option\s*\(\s*{OPTION}\s+\"[^\"]+\"\s+OFF\s*\)",
        compact_cmake,
    ) is not None
    compile_definition = re.search(
        rf"if\s*\(\s*{OPTION}\s*\).*?target_compile_definitions\s*\(\s*xar_ck3_bridge\s+PRIVATE\s+{OPTION}=1\s*\).*?endif\s*\(\s*\)",
        compact_cmake,
    ) is not None
    macro_binding = re.search(
        rf"#if\s+defined\s*\(\s*{OPTION}\s*\).*?kStartupFailureContainmentEnabledV1\s*=\s*true\s*;.*?#else.*?kStartupFailureContainmentEnabledV1\s*=\s*false\s*;.*?#endif",
        bridge_text,
        re.DOTALL,
    ) is not None
    static_exclusion = re.search(
        r"static_assert\s*\(\s*!\s*\(\s*kStartupFailureContainmentEnabledV1\s*&&\s*kStartupParticle2StageRecorderEnabledV1\s*\)\s*\)\s*;",
        bridge_text,
        re.DOTALL,
    ) is not None
    return {
        "containment_option_default_off": option_default_off,
        "containment_compile_definition_wired": compile_definition,
        "containment_constant_macro_bound": macro_binding,
        "stage_recorder_mutually_exclusive": static_exclusion,
        "existing_guard_chain_order": _in_order(bridge_text, GUARD_ORDER),
    }


def _runner_checks(runner_text: str) -> dict[str, bool]:
    bridge_arg_count = len(
        re.findall(r"add_argument\s*\(\s*[\"']--bridge-dll[\"']", runner_text)
    )
    delegates_one_terms_runner = (
        "parser = terms_live._parser()" in runner_text
        and "terms_live._run(" in runner_text
    )
    return {
        "one_bridge_dll_argument": bridge_arg_count == 1
        or (bridge_arg_count == 0 and delegates_one_terms_runner),
        "no_separate_startup_guard_dll_argument": "--startup-guard-dll"
        not in runner_text,
        "prepare_startup_export_used_by_injector_path": "NativeBridgeLaunchConfig"
        in runner_text
        or delegates_one_terms_runner,
    }


def verify(
    *,
    contract_path: Path,
    source_root: Path,
    build_dir: Path,
    base_manifest_path: Path,
    bridge_dll: Path,
    bridge_injector: Path,
    runner_path: Path,
    attempt_dir: Path,
    inventory_provider: Callable[[], list[dict[str, object]]] = _default_inventory,
) -> dict[str, object]:
    contract = _read_json(contract_path)
    base = _read_json(base_manifest_path)
    cmake_path = source_root / "ck3_autonomous_player/native_bridge/CMakeLists.txt"
    bridge_path = source_root / "ck3_autonomous_player/native_bridge/src/bridge.cpp"
    cache_path = build_dir / "CMakeCache.txt"
    required_files = {
        "cmake": cmake_path,
        "bridge_source": bridge_path,
        "cmake_cache": cache_path,
        "base_manifest": base_manifest_path,
        "bridge_dll": bridge_dll,
        "bridge_injector": bridge_injector,
        "runner": runner_path,
    }
    files_present = {name: path.is_file() for name, path in required_files.items()}
    checks: dict[str, bool] = {f"{name}_present": ok for name, ok in files_present.items()}
    errors: list[str] = []

    source_checks: dict[str, bool] = {}
    runner_checks: dict[str, bool] = {}
    cache: dict[str, str] = {}
    bridge_sha: str | None = None
    injector_sha: str | None = None
    inventory: list[dict[str, object]] = []
    if all(files_present.values()):
        cmake_text = cmake_path.read_text(encoding="utf-8-sig")
        bridge_text = bridge_path.read_text(encoding="utf-8-sig")
        runner_text = runner_path.read_text(encoding="utf-8-sig")
        source_checks = _source_checks(cmake_text, bridge_text)
        runner_checks = _runner_checks(runner_text)
        cache = _cmake_cache(cache_path)
        bridge_sha = _sha256_file(bridge_dll)
        injector_sha = _sha256_file(bridge_injector)
        checks.update(source_checks)
        checks.update(runner_checks)
        checks["containment_cache_on"] = cache.get(OPTION, "").upper() == "ON"
        checks["stage_recorder_cache_off"] = (
            cache.get(STAGE_RECORDER_OPTION, "OFF").upper() == "OFF"
        )
        frozen = str(contract.get("frozen_unguarded_bridge_dll_sha256", "")).upper()
        checks["guarded_dll_differs_from_frozen_unguarded"] = bridge_sha != frozen

    base_query = base.get("query_contract")
    contract_query = contract.get("query_contract")
    expected_command = "query-war-termination-terms-v1-50331699"
    checks["query_contract_unchanged"] = base_query == contract_query
    checks["query_count_exactly_two"] = (
        isinstance(base_query, dict)
        and base_query.get("terms_query_count") == 2
        and base_query.get("allowed_gameplay_commands")
        == [expected_command, expected_command]
    )
    checks["mutation_commands_empty"] = (
        isinstance(base_query, dict) and base_query.get("mutation_commands") == []
    )
    checks["paused"] = isinstance(base_query, dict) and base_query.get("paused") is True
    checks["strict_identity_layers"] = (
        isinstance(base_query, dict)
        and base_query.get("strict_equal_layers") == STRICT_LAYERS
    )
    checks["readiness_boundary_unchanged"] = (
        base.get("readiness_boundary") == contract.get("readiness_boundary")
    )
    checks["attempt_dir_absent"] = not attempt_dir.exists()

    try:
        inventory = inventory_provider()
    except Exception as error:  # pragma: no cover - defensive reporting path
        errors.append(f"process inventory failed: {error}")
    checks["exclusive_ck3_inventory_empty"] = not inventory and not errors
    ok = all(checks.values()) and not errors
    return {
        "format_version": 1,
        "kind": "ck3_raiktor_generic_war_bound_guarded_retry_verify_only",
        "status": "READY_TO_FREEZE" if ok else "BLOCKED",
        "ok": ok,
        "no_launch_boundary": {
            "ck3_started": False,
            "profile_prepared": False,
            "query_count": 0,
            "mutation_executed": False,
            "readiness_promoted": False,
        },
        "paths": {name: str(path.resolve()) for name, path in required_files.items()},
        "attempt_dir": str(attempt_dir.resolve()),
        "identities": {
            "contract_sha256": _sha256_file(contract_path),
            "base_manifest_sha256": _sha256_file(base_manifest_path),
            "cmake_sha256": _sha256_file(cmake_path)
            if files_present["cmake"]
            else None,
            "bridge_source_sha256": _sha256_file(bridge_path)
            if files_present["bridge_source"]
            else None,
            "cmake_cache_sha256": _sha256_file(cache_path)
            if files_present["cmake_cache"]
            else None,
            "runner_sha256": _sha256_file(runner_path)
            if files_present["runner"]
            else None,
            "bridge_dll_sha256": bridge_sha,
            "bridge_injector_sha256": injector_sha,
        },
        "configuration": {
            "containment_cache": cache.get(OPTION),
            "stage_recorder_cache": cache.get(STAGE_RECORDER_OPTION),
            "one_runner_bridge_dll_slot": runner_checks.get(
                "one_bridge_dll_argument", False
            ),
            "separate_guard_dll_slot": False,
            "guard_install_order": list(GUARD_ORDER),
        },
        "query_contract": base_query,
        "readiness_boundary": base.get("readiness_boundary"),
        "process_inventory": inventory,
        "checks": checks,
        "errors": errors,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = verify(
        contract_path=args.contract.resolve(),
        source_root=args.source_root.resolve(),
        build_dir=args.build_dir.resolve(),
        base_manifest_path=args.base_manifest.resolve(),
        bridge_dll=args.bridge_dll.resolve(),
        bridge_injector=args.bridge_injector.resolve(),
        runner_path=args.runner.resolve(),
        attempt_dir=args.attempt_dir.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
