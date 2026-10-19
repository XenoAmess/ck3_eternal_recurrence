"""Build two tiny mock DLLs and run source-only fixtures through ctypes.

No adapter/CMake changes, game discovery, injector, native RPC or real getter
invocation. A pinned storage card for the one explicit output root is required.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

REPO = Path(__file__).resolve().parents[3]
NATIVE = REPO / "ck3_autonomous_player/native_bridge"
MACHINE_TOOL = REPO / "tools/ck3_live_run_id.py"
HARD_BYTES = 16 * 1024 * 1024
SOURCES = [
    "src/ck3_12004_player_heir_candidate_v1.cpp",
    "tests/ck3_12004_player_heir_candidate_v1_fixture.cpp",
    "src/ck3_12004_abi_profile.cpp",
    "src/ck3_12004_family.cpp",
    "src/ck3_12002_family_value.cpp",
    "src/ck3_12002.cpp",
]
HEADERS = [
    "include/xar_bridge/ck3_12004_player_heir_candidate_v1.hpp",
    "include/xar_bridge/ck3_12004.hpp",
    "include/xar_bridge/ck3_12002.hpp",
    "include/xar_bridge/ck3_12004_family.hpp",
    "include/xar_bridge/ck3_12004_family_abi.hpp",
    "include/xar_bridge/ck3_12002_family_value.hpp",
    "include/xar_bridge/ck3_12004_family_break_penalty.hpp",
]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def machine() -> str:
    return subprocess.check_output(
        [os.sys.executable, str(MACHINE_TOOL), "machine"], text=True).strip()


def write_new(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")


def plan(root: Path, budget_root: Path | None = None) -> dict:
    return {
        "schema": "xar.player-heir-candidate-mock-dll-plan.v1",
        "machine_id": machine(), "observed_at_utc": utc(),
        "output_root": str(root.resolve()), "hard_limit_bytes": HARD_BYTES,
        "budget_root": str((budget_root or root).resolve()),
        "attempt": "one explicit root, create-only; no automatic retry",
        "producer": pin(Path(__file__).resolve()),
        "source_pins": [pin(NATIVE / p) for p in SOURCES + HEADERS],
        "source_knowledge": pin(REPO / (
            "docs/ck3-native-ai/evidence/"
            "player-heir-h12004-source-closure-2026-10-19.json")),
        "outputs": {
            "fixed": ["default-off/provider.dll", "explicit-optin/provider.dll",
                      "default-off/compile.log", "explicit-optin/compile.log",
                      "RESULT.json"],
            "bounded_compiler_sidecars":
                ["default-off/*.obj,*.lib,*.exp", "explicit-optin/*.obj,*.lib,*.exp"],
            "temporary": "tmp/; environment capture script and compiler temporaries only",
        },
        "software_cases": "same suite in default-off/opt-in; actual4 core/FamilyValues/Lineage linked; unrelated fixture-only Break binder stub must have0 calls",
        "boundary": "No production native DLL build/deploy, real CK3 image read, process access, RPC, EXE output or actual H credit; fixture getter substitutes original function.",
        "status": "PLAN_ONLY_NOT_EXECUTED",
    }


def tree_usage(root: Path) -> dict[str, int]:
    # FileStandardInfo supplies both EOF and AllocationSize for the same handle.
    # Zero allocation is valid for an empty file; query failure is never zero.
    from ctypes import wintypes

    class StandardInfo(ctypes.Structure):
        _fields_ = [("AllocationSize", ctypes.c_longlong),
                    ("EndOfFile", ctypes.c_longlong),
                    ("NumberOfLinks", wintypes.DWORD),
                    ("DeletePending", ctypes.c_ubyte),
                    ("Directory", ctypes.c_ubyte)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
        wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
        wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE,
        ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    logical = allocated = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("fixture child unexpectedly contains a link")
        if not path.is_file():
            continue
        handle = kernel.CreateFileW(str(path), 0, 7, None, 3,
                                    0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            error = ctypes.get_last_error()
            if error in (2, 3) and not path.exists():
                continue  # Temporary file vanished; not an unknown read.
            raise OSError(error, "file allocation query open failed", str(path))
        try:
            info = StandardInfo()
            if not kernel.GetFileInformationByHandleEx(handle, 1,
                    ctypes.byref(info), ctypes.sizeof(info)):
                raise OSError(ctypes.get_last_error(),
                              "FileStandardInfo query failed", str(path))
            if info.Directory or info.AllocationSize < 0 or info.EndOfFile < 0:
                raise RuntimeError("unknown allocation metadata in fixture child")
            logical += info.EndOfFile
            allocated += info.AllocationSize
        finally:
            kernel.CloseHandle(handle)
    return {"logical_bytes": logical, "allocated_bytes": allocated,
            "guard_bytes": max(logical, allocated)}


def compile_dll(command: list[str], directory: Path, root: Path,
                environment: dict[str, str]) -> tuple[int, dict[str, int]]:
    peak = tree_usage(root)
    with (directory / "compile.log").open("wb") as log:
        process = subprocess.Popen(command, cwd=directory, env=environment,
            stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        try:
            while True:
                usage = tree_usage(root)
                peak = {k: max(peak[k], usage[k]) for k in peak}
                if peak["guard_bytes"] > HARD_BYTES:
                    raise RuntimeError("fixture hard16MiB exceeded; retained, no retry")
                if process.poll() is not None:
                    break
                time.sleep(0.05)
        except BaseException:
            if process.poll() is None:
                # Only our current Popen child/tree; never a game/other build.
                subprocess.run(["taskkill.exe", "/PID", str(process.pid),
                                "/T", "/F"], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               check=False)
                if process.poll() is None:
                    process.kill()
            process.wait()
            raise
    return process.returncode, peak


def run(plan_path: Path, card_path: Path, card_sha: str) -> dict:
    record = json.loads(plan_path.read_bytes())
    current_machine = machine()
    if record["machine_id"] != current_machine:
        raise RuntimeError("plan machine mismatch")
    if pin(card_path)["sha256"] != card_sha:
        raise RuntimeError("storage card pin mismatch")
    card = json.loads(card_path.read_bytes())
    # The storage owner issues this tiny explicit child-admission projection.
    admission = card["player_heir_fixture_admission"]
    root = Path(record["output_root"]).resolve()
    budget_root = Path(record.get("budget_root", record["output_root"])).resolve()
    if (card["machine_id"] != current_machine or
        Path(admission["output_root"]).resolve() != root or
        admission["plan_sha256"] != pin(plan_path)["sha256"] or
        admission["hard_limit_bytes"] != HARD_BYTES or
        Path(admission.get("budget_root", admission["output_root"])).resolve() != budget_root or
        not root.is_relative_to(budget_root) or
        admission["approved"] is not True):
        raise RuntimeError("exact fixture storage admission mismatch")
    expiry = datetime.fromisoformat(admission["expires_at_utc"].replace("Z", "+00:00"))
    if expiry <= datetime.now(timezone.utc):
        raise RuntimeError("fixture admission expired")
    if pin(Path(__file__).resolve()) != record["producer"]:
        raise RuntimeError("producer changed after fixture plan")
    for row in record["source_pins"] + [record["source_knowledge"]]:
        if pin(Path(row["path"])) != row:
            raise RuntimeError(f"source changed: {row['path']}")
    if root.exists():
        raise RuntimeError("attempt root already exists; preserve and review before new attempt")
    root.mkdir()
    temporary = root / "tmp"
    temporary.mkdir()
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import (
        _visual_studio_environment,
    )
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if not compiler:
        raise RuntimeError("MSVC compiler unavailable")
    start = utc()
    suites = []
    peak = {"logical_bytes": 0, "allocated_bytes": 0, "guard_bytes": 0}
    for mode, flags in (("default-off", []), ("explicit-optin", [
            "/DXAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1"])):
        directory = root / mode
        directory.mkdir()
        dll = directory / "provider.dll"
        command = [compiler, "/nologo", "/LD", "/std:c++20", "/W4", "/WX",
                   "/permissive-", "/EHsc", "/DNOMINMAX", "/Od", "/MD", "/Gy",
                   *flags, f"/I{NATIVE / 'include'}", f"/I{NATIVE / 'research'}",
                   f"/I{NATIVE / 'src'}",
                   *(str(NATIVE / p) for p in SOURCES), f"/Fe:{dll}",
                   "/link", "/OPT:REF", "/INCREMENTAL:NO"]
        code, this_peak = compile_dll(command, directory, budget_root, environment)
        peak = {k: max(peak[k], this_peak[k]) for k in peak}
        if code:
            raise RuntimeError(f"{mode} compile failed, original log retained: {directory / 'compile.log'}")
        library = ctypes.CDLL(str(dll))
        entry = library.RunPlayerHeirCandidateFixtures
        entry.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
        entry.restype = ctypes.c_int
        output = ctypes.create_string_buffer(4096)
        result = entry(output, len(output))
        text = output.value.decode("utf-8")
        if result:
            raise RuntimeError(f"{mode} fixture failed: {text}")
        suites.append({"mode": mode, "dll": pin(dll),
                       "compile_log": pin(directory / "compile.log"),
                       "fixture": json.loads(text)})
    for row in record["source_pins"]:
        if pin(Path(row["path"])) != row:
            raise RuntimeError(f"source changed during test: {row['path']}")
    result = {
        "schema": "xar.player-heir-candidate-mock-dll-result.v1",
        "machine_id": current_machine, "started_at_utc": start,
        "ended_at_utc": utc(), "plan": pin(plan_path), "storage_card": pin(card_path),
        "status": "SOFTWARE_FIXTURES_PASS", "suites": suites,
        "peak_observed_usage": peak, "hard_limit_bytes": HARD_BYTES,
        "compile_priority": "BELOW_NORMAL_PRIORITY_CLASS, no /MP, sequential",
        "budget_root": str(budget_root),
        "native_game_build_deploy_or_actual_H_credit": False,
        "Game_RPC_process_access": 0,
    }
    write_new(root / "RESULT.json", result)
    if tree_usage(budget_root)["guard_bytes"] > HARD_BYTES:
        raise RuntimeError("final fixture child exceeded bound; retain true result")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--build-root", type=Path)
    parser.add_argument("--budget-root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--storage-card", type=Path)
    parser.add_argument("--storage-card-sha256")
    args = parser.parse_args()
    if args.plan_output and args.build_root and not args.plan:
        write_new(args.plan_output, plan(args.build_root, args.budget_root))
        print(json.dumps(pin(args.plan_output)))
    elif args.plan and args.storage_card and args.storage_card_sha256:
        print(json.dumps(run(args.plan, args.storage_card, args.storage_card_sha256)))
    else:
        parser.error("use plan-output/build-root or pinned plan/storage-card inputs")
