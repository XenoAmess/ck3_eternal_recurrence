from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from uuid import uuid4
from datetime import datetime, timezone


PROFILES = {
    "legacy": {
        "repo_revision": "480f287489eb91efd65f94ec07bc39f681960bd0",
        "bridge_dll_sha256": "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF",
        "bridge_injector_sha256": "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF",
        "bridge_dll_relative_path": r"ck3_autonomous_player\native_bridge\.build-event-scopes-a860702-msvc\xar_ck3_bridge.dll",
        "bridge_injector_relative_path": r"ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe",
    },
    "claim-cb-white-peace": {
        "repo_revision": "51fe8cf6cb55de5ca01db4ed215e0abff52213a6",
        "bridge_dll_sha256": "F52203F2395819CCB7A37153DBD36AB9CC6F6E168F4B44D179D3979ABF939D7B",
        "bridge_injector_sha256": "8A46DE3BFBF567E34BA99E61AEFA7F59DA248C4AE89791BB74E12820B4380B99",
        "bridge_dll_relative_path": r"ck3_autonomous_player\native_bridge\build-claim-white-peace-51fe8cf-msvc\xar_ck3_bridge.dll",
        "bridge_injector_relative_path": r"ck3_autonomous_player\native_bridge\build-claim-white-peace-51fe8cf-msvc\xar_ck3_bridge_injector.exe",
    },
}
CANONICAL_CHECKPOINT_SIZE = 67_118_175
CANONICAL_CHECKPOINT_SHA256 = "12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D"
CANONICAL_DRIVER_STATE_SHA256 = "3C3BBFECDC6941B17B1CC946CEDA1011ABF3DD673AD511B1BFB764FC20E955A9"
EXPECTED_PIPE = r"\\.\pipe\xar_ck3_restore_exact2_7aff1d0"
EXPECTED_CHARACTER_ID = 29_829
EXPECTED_EPISODE_RUN_ID = "native-29829-ee172aa720db"
EXPECTED_DATE_RAW = 53_177_976
EXPECTED_HISTORY_INDEX = 402
EXPECTED_INTERACTIVE_USER = "xenoa"
EXPECTED_DESKTOP = r"WinSta0\Default"
REQUIRED_QUALIFICATION_GATES = (
    "start_alive",
    "fixed_seed_verified",
    "started_at_seed_date",
    "same_episode_binding",
    "visible_gameplay",
    "date_advanced",
    "death_terminal_executed",
    "settlement_matches_episode",
    "no_heir_gameplay",
    "cleanup_proven",
)


class CanaryError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def file_identity(
    path: Path, expected_sha256: str, label: str, expected_size: int = -1
) -> dict[str, Any]:
    if not path.is_file():
        raise CanaryError(f"{label} is missing: {path}")
    size = path.stat().st_size
    if expected_size >= 0 and size != expected_size:
        raise CanaryError(f"{label} size differs: {size} != {expected_size} ({path})")
    actual = sha256(path)
    if actual != expected_sha256.upper():
        raise CanaryError(
            f"{label} SHA-256 differs: {actual} != {expected_sha256.upper()} ({path})"
        )
    return {"path": str(path.resolve()), "size": size, "sha256": actual}


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CanaryError(f"{label} is not valid JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise CanaryError(f"{label} JSON root is not an object: {path}")
    return value


def driver_anchor(
    state_root: Path,
    checkpoint_sha256: str,
    checkpoint_size: int,
    driver_state_sha256: str,
) -> dict[str, Any]:
    driver_path = state_root / "native-session" / "driver-state.json"
    driver = load_object(driver_path, "driver state")
    checkpoint = driver.get("last_checkpoint")
    history = driver.get("command_history")
    if not isinstance(checkpoint, dict) or not isinstance(history, list):
        raise CanaryError(f"driver state lacks its checkpoint anchor: {driver_path}")
    expected = (
        driver.get("format_version") == 2
        and driver.get("pipe_name") == EXPECTED_PIPE
        and driver.get("episode_character_id") == EXPECTED_CHARACTER_ID
        and driver.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and checkpoint.get("status") == "saved"
        and checkpoint.get("name") == "xar_checkpoint.ck3"
        and checkpoint.get("size") == checkpoint_size
        and str(checkpoint.get("sha256", "")).upper() == checkpoint_sha256.upper()
        and checkpoint.get("date_raw") == EXPECTED_DATE_RAW
        and checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and checkpoint.get("episode_character_id") == EXPECTED_CHARACTER_ID
        and checkpoint.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and len(history) >= EXPECTED_HISTORY_INDEX
    )
    anchor = history[EXPECTED_HISTORY_INDEX - 1] if expected else None
    saved = anchor.get("result", {}).get("checkpoint") if isinstance(anchor, dict) else None
    expected = expected and isinstance(saved, dict) and (
        anchor.get("index") == EXPECTED_HISTORY_INDEX
        and anchor.get("command") == "save-checkpoint"
        and anchor.get("ok") is True
        and saved.get("size") == checkpoint_size
        and str(saved.get("sha256", "")).upper() == checkpoint_sha256.upper()
        and saved.get("date_raw") == EXPECTED_DATE_RAW
    )
    if not expected:
        raise CanaryError(
            f"driver state does not match the exact production6b checkpoint anchor: {driver_path}"
        )
    identity = file_identity(driver_path, driver_state_sha256, "driver state")
    return {
        **identity,
        "format_version": 2,
        "pipe": EXPECTED_PIPE,
        "episode_character_id": EXPECTED_CHARACTER_ID,
        "episode_run_id": EXPECTED_EPISODE_RUN_ID,
        "date_raw": EXPECTED_DATE_RAW,
        "history_index": EXPECTED_HISTORY_INDEX,
    }


def is_within(candidate: Path, root: Path, *, allow_equal: bool = True) -> bool:
    candidate = candidate.resolve()
    root = root.resolve()
    if not allow_equal and candidate == root:
        return False
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def desktop_identity() -> str:
    if os.name != "nt":
        return "unavailable: Windows only"
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    user32.GetProcessWindowStation.restype = wintypes.HANDLE
    user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user32.GetThreadDesktop.restype = wintypes.HANDLE
    user32.GetUserObjectInformationW.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetUserObjectInformationW.restype = wintypes.BOOL

    def name(handle: int) -> str:
        buffer = ctypes.create_unicode_buffer(512)
        needed = wintypes.DWORD()
        if not user32.GetUserObjectInformationW(
            handle, 2, buffer, ctypes.sizeof(buffer), ctypes.byref(needed)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value

    station = name(user32.GetProcessWindowStation())
    desktop = name(user32.GetThreadDesktop(kernel32.GetCurrentThreadId()))
    return f"{station}\\{desktop}"


def process_ids(executable_name: str) -> list[int]:
    if os.name != "nt":
        return []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    rows: list[int] = []
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while present:
            if entry.szExeFile.casefold() == executable_name.casefold():
                rows.append(int(entry.th32ProcessID))
            present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return rows


def invoke_json(
    executable: Path,
    arguments: list[str],
    allowed_exit_codes: set[int],
    label: str,
    cwd: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        [str(executable), *arguments],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if completed.returncode not in allowed_exit_codes:
        raise CanaryError(f"{label} exited {completed.returncode}: {completed.stdout}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CanaryError(
            f"{label} did not emit one JSON document (exit {completed.returncode}): {completed.stdout}"
        ) from error
    if not isinstance(payload, dict):
        raise CanaryError(f"{label} JSON root is not an object")
    return {"exit_code": completed.returncode, "payload": payload}


def artifact_binding(
    run_dir: Path,
    entry: Any,
    expected_relative_path: str,
    label: str,
) -> dict[str, Any]:
    verification: dict[str, Any] = {
        "ok": False,
        "label": label,
        "expected_relative_path": expected_relative_path,
        "path": None,
        "size": None,
        "sha256": None,
        "error": None,
    }
    try:
        if not isinstance(entry, dict):
            raise CanaryError(f"{label} artifact entry is missing")
        relative = entry.get("path")
        size = entry.get("size")
        digest = entry.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative.strip()
            or Path(relative).is_absolute()
            or relative.replace("\\", "/") != expected_relative_path
        ):
            raise CanaryError(f"{label} artifact path is not the expected relative path")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise CanaryError(f"{label} artifact size is malformed")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", digest):
            raise CanaryError(f"{label} artifact SHA-256 is malformed")
        path = (run_dir / relative).resolve()
        if not is_within(path, run_dir, allow_equal=False):
            raise CanaryError(f"{label} artifact escapes the run directory")
        identity = file_identity(path, digest, f"{label} artifact", size)
        verification.update({"ok": True, **identity})
    except (CanaryError, OSError) as error:
        verification["error"] = str(error)
    return verification


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the exact 20-turn CK3 canary")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="legacy")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--source-state", type=Path)
    parser.add_argument("--target-state", type=Path)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--python-path", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-repository-check", action="store_true")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=float, default=21_600)
    parser.add_argument("--readiness-timeout-seconds", type=float, default=300)
    parser.add_argument("--checkpoint-every-advances", type=int, default=3)
    parser.add_argument("--expected-repo-revision")
    parser.add_argument("--expected-checkpoint-size", type=int)
    parser.add_argument("--expected-checkpoint-sha256")
    parser.add_argument("--expected-driver-state-sha256")
    parser.add_argument("--expected-bridge-dll-sha256")
    parser.add_argument("--expected-bridge-injector-sha256")
    return parser


def resolve_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    args = build_parser().parse_args(argv)
    profile = PROFILES[args.profile]
    args.repo_root = (args.repo_root or REPOSITORY_ROOT).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    args.source_state = (
        args.source_state or temp_root / "xar-war-entry-production6b-state"
    ).resolve()
    if args.target_state is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        args.target_state = temp_root / f"xar-one-generation-canary-{stamp}-{uuid4().hex[:8]}-state"
    args.target_state = args.target_state.resolve()
    args.game_dir = (
        args.game_dir
        or (Path(os.environ["XAR_CK3_GAME_DIR"]) if os.environ.get("XAR_CK3_GAME_DIR") else args.repo_root / "Crusader Kings III")
    ).resolve()
    args.python_path = (
        args.python_path
        or (Path(os.environ["XAR_AUTOPLAYER_PYTHON"]) if os.environ.get("XAR_AUTOPLAYER_PYTHON") else args.repo_root / "tools" / ".venv" / "Scripts" / "python.exe")
    ).resolve()
    args.bridge_dll = (
        args.bridge_dll
        or (Path(os.environ["XAR_CK3_BRIDGE_DLL"]) if os.environ.get("XAR_CK3_BRIDGE_DLL") else args.repo_root / str(profile["bridge_dll_relative_path"]))
    ).resolve()
    args.bridge_injector = (
        args.bridge_injector
        or (Path(os.environ["XAR_CK3_BRIDGE_INJECTOR"]) if os.environ.get("XAR_CK3_BRIDGE_INJECTOR") else args.repo_root / str(profile["bridge_injector_relative_path"]))
    ).resolve()
    args.expected_repo_revision = args.expected_repo_revision or str(profile["repo_revision"])
    args.expected_checkpoint_size = args.expected_checkpoint_size if args.expected_checkpoint_size is not None else CANONICAL_CHECKPOINT_SIZE
    args.expected_checkpoint_sha256 = args.expected_checkpoint_sha256 or CANONICAL_CHECKPOINT_SHA256
    args.expected_driver_state_sha256 = args.expected_driver_state_sha256 or CANONICAL_DRIVER_STATE_SHA256
    args.expected_bridge_dll_sha256 = args.expected_bridge_dll_sha256 or str(profile["bridge_dll_sha256"])
    args.expected_bridge_injector_sha256 = args.expected_bridge_injector_sha256 or str(profile["bridge_injector_sha256"])
    return args


def validate_arguments(args: argparse.Namespace) -> None:
    profile = PROFILES[args.profile]
    identities = (
        (args.expected_checkpoint_sha256, "expected checkpoint SHA-256"),
        (args.expected_driver_state_sha256, "expected driver-state SHA-256"),
        (args.expected_bridge_dll_sha256, "expected bridge DLL SHA-256"),
        (args.expected_bridge_injector_sha256, "expected bridge injector SHA-256"),
    )
    for value, label in identities:
        if not re.fullmatch(r"[0-9A-Fa-f]{64}", value):
            raise CanaryError(f"{label} must be a 64-character SHA-256")
    if not re.fullmatch(r"[0-9A-Fa-f]{40}", args.expected_repo_revision):
        raise CanaryError("expected repo revision must be a full 40-character Git revision")
    if args.max_turns != 20:
        raise CanaryError("this handoff is the exact 20-turn canary; max turns must remain 20")
    if args.timeout_seconds <= 0 or args.readiness_timeout_seconds <= 0 or args.checkpoint_every_advances < 1:
        raise CanaryError("timeouts and checkpoint cadence must be positive")
    if args.execute and (
        args.timeout_seconds != 21_600
        or args.readiness_timeout_seconds != 300
        or args.checkpoint_every_advances != 3
    ):
        raise CanaryError("execute requires the fixed canary bounds: timeout 21600, readiness 300, checkpoint cadence 3")
    if args.execute and args.skip_repository_check:
        raise CanaryError("skip-repository-check is dry-run-only and cannot be combined with execute")
    canonical = (
        args.expected_repo_revision.casefold() == str(profile["repo_revision"]).casefold()
        and args.expected_checkpoint_size == CANONICAL_CHECKPOINT_SIZE
        and args.expected_checkpoint_sha256.upper() == CANONICAL_CHECKPOINT_SHA256
        and args.expected_driver_state_sha256.upper() == CANONICAL_DRIVER_STATE_SHA256
        and args.expected_bridge_dll_sha256.upper() == str(profile["bridge_dll_sha256"])
        and args.expected_bridge_injector_sha256.upper() == str(profile["bridge_injector_sha256"])
    )
    if args.execute and not canonical:
        raise CanaryError(f"execute requires the canonical production6b checkpoint and '{args.profile}' profile identities")
    agent = args.repo_root / "ck3_autonomous_player" / "agent.py"
    for required in (agent, args.python_path):
        if not required.is_file():
            raise CanaryError(f"required file is missing: {required}")
    if not args.game_dir.is_dir() or not (args.game_dir / "binaries" / "ck3.exe").is_file():
        raise CanaryError(f"CK3 game directory is incomplete: {args.game_dir}")
    if not args.source_state.is_dir():
        raise CanaryError(f"production6b source state is missing: {args.source_state}")
    if args.target_state.exists():
        raise CanaryError(f"fresh canary target already exists; refusing overwrite: {args.target_state}")
    if not is_within(args.target_state, Path(tempfile.gettempdir()), allow_equal=False):
        raise CanaryError(f"canary target must be a fresh descendant of the current TEMP directory: {args.target_state}")


def git_revision(args: argparse.Namespace) -> str | None:
    if args.skip_repository_check:
        return None
    status = subprocess.run(
        ["git", "-C", str(args.repo_root), "status", "--porcelain=v1", "--untracked-files=all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if status.returncode or status.stdout:
        raise CanaryError(f"final canary source clone is not clean:\n{status.stdout}{status.stderr}")
    revision = subprocess.run(
        ["git", "-C", str(args.repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="ascii",
        check=False,
    )
    observed = revision.stdout.strip().casefold()
    if revision.returncode or not re.fullmatch(r"[0-9a-f]{40}", observed):
        raise CanaryError("could not resolve the clean source revision")
    if observed != args.expected_repo_revision.casefold():
        raise CanaryError(f"clean source revision differs: {observed} != {args.expected_repo_revision.casefold()}")
    return observed


def qualify_result(canary: dict[str, Any], target_state: Path, post_pids: list[int]) -> dict[str, Any]:
    result = canary["payload"]
    runs_root = (target_state / "runs").resolve()
    run_dirs = sorted(path for path in runs_root.glob("*-one-generation-*") if path.is_dir())
    run_dir = run_dirs[-1].resolve() if run_dirs else None
    report_path = run_dir / "report.json" if run_dir else None
    try:
        persisted = load_object(report_path, "persisted report") if report_path and report_path.is_file() else None
    except CanaryError:
        persisted = None
    identity_bound = bool(
        persisted
        and run_dir
        and report_path
        and is_within(run_dir, runs_root, allow_equal=False)
        and run_dir.name == result.get("run_id") == persisted.get("run_id")
        and result.get("run_dir") == persisted.get("run_dir") == str(run_dir)
        and result.get("report_path") == persisted.get("report_path") == str(report_path)
    )
    stdout_matches = identity_bound and stable_json(result) == stable_json(persisted)
    artifacts = persisted.get("artifacts", {}) if persisted else {}
    blocker_entry = artifacts.get("first_blocker") if isinstance(artifacts, dict) else None
    terminal_entry = artifacts.get("terminal_settlement") if isinstance(artifacts, dict) else None
    binding_root = run_dir or runs_root
    blocker_artifact = artifact_binding(binding_root, blocker_entry, "first-blocker.json", "first blocker")
    terminal_artifact = artifact_binding(binding_root, terminal_entry, "terminal-settlement.json", "terminal settlement")

    def read_bound(binding: dict[str, Any]) -> dict[str, Any] | None:
        try:
            return load_object(Path(binding["path"]), binding["label"]) if binding["ok"] else None
        except CanaryError:
            return None

    blocker_sidecar = read_bound(blocker_artifact)
    terminal_sidecar = read_bound(terminal_artifact)
    first_blocker = persisted.get("first_blocker") if persisted else None
    terminal = persisted.get("terminal") if persisted else None
    blocker_matches = blocker_sidecar is not None and stable_json(blocker_sidecar) == stable_json(first_blocker)
    terminal_matches = terminal_sidecar is not None and stable_json(terminal_sidecar) == stable_json(terminal)
    gates = persisted.get("qualification_gates") if persisted else None
    gates_all_true = isinstance(gates, dict) and all(gates.get(key) is True for key in REQUIRED_QUALIFICATION_GATES) and all(isinstance(value, bool) and value for value in gates.values())
    cleanup = persisted.get("cleanup") if persisted else None
    bounds = persisted.get("bounds") if persisted else None
    finalized = persisted.get("finalized") if persisted else None
    completion_contract = persisted.get("completion_contract") if persisted else None
    status = persisted.get("status") if persisted else None
    outcome = persisted.get("outcome") if persisted else None
    ok = persisted.get("ok") if persisted else None
    common = (
        identity_bound
        and stdout_matches
        and finalized is True
        and completion_contract == "one_generation"
        and isinstance(cleanup, dict)
        and cleanup.get("ok") is True
        and isinstance(bounds, dict)
        and bounds.get("requested_turns") == 20
        and bounds.get("max_wall_seconds") == 21_600
        and bounds.get("readiness_timeout_seconds") == 300
        and bounds.get("checkpoint_every_eligible_advances") == 3
        and not post_pids
    )
    classification = "capability_or_harness_failure"
    expected = False
    if (
        canary["exit_code"] == 0
        and common
        and status == "episode_complete"
        and outcome == "qualified"
        and ok is True
        and gates_all_true
        and first_blocker is None
        and blocker_entry is None
        and terminal_artifact["ok"]
        and terminal_matches
    ):
        classification = "qualified_death_within_20_turns"
        expected = True
    elif (
        canary["exit_code"] == 1
        and common
        and status == "turn_limit"
        and outcome == "bounded_incomplete"
        and ok is False
        and isinstance(first_blocker, dict)
        and first_blocker.get("kind") == "run_bound_exhausted"
        and first_blocker.get("status") == "turn_limit"
        and first_blocker.get("turn_index") == 20
        and blocker_artifact["ok"]
        and blocker_matches
        and terminal is None
        and terminal_entry is None
    ):
        classification = "expected_bounded_incomplete"
        expected = True
    return {
        "status": status,
        "outcome": outcome,
        "ok": ok,
        "classification": classification,
        "expected_canary_outcome": expected,
        "report_path": str(report_path) if report_path else None,
        "run_dir": str(run_dir) if run_dir else None,
        "report_identity_bound": identity_bound,
        "stdout_report_matches_persisted": stdout_matches,
        "newest_one_generation_run": str(run_dir) if run_dir else None,
        "finalized": finalized,
        "completion_contract": completion_contract,
        "cleanup": cleanup,
        "qualification_gates_all_true": gates_all_true,
        "first_blocker_artifact": blocker_artifact,
        "first_blocker_sidecar_matches": blocker_matches,
        "terminal_artifact": terminal_artifact,
        "terminal_sidecar_matches": terminal_matches,
        "post_canary_ck3_process_count": len(post_pids),
        "post_canary_ck3_pids": post_pids,
        "first_blocker": first_blocker,
    }


def main(argv: list[str] | None = None) -> int:
    args = resolve_arguments(argv)
    validate_arguments(args)
    revision = git_revision(args)
    source_checkpoint_path = args.source_state / "profile" / "save games" / "xar_checkpoint.ck3"
    source_checkpoint = file_identity(source_checkpoint_path, args.expected_checkpoint_sha256, "production6b checkpoint", args.expected_checkpoint_size)
    source_driver = driver_anchor(args.source_state, args.expected_checkpoint_sha256, args.expected_checkpoint_size, args.expected_driver_state_sha256)
    dll = file_identity(args.bridge_dll, args.expected_bridge_dll_sha256, "exact-build bridge DLL")
    injector = file_identity(args.bridge_injector, args.expected_bridge_injector_sha256, "exact-build bridge injector")
    agent = args.repo_root / "ck3_autonomous_player" / "agent.py"
    prepare = [str(agent), "--state-dir", str(args.target_state), "--game-dir", str(args.game_dir), "--bridge-mode", "disabled", "prepare-profile"]
    verify = [str(agent), "--state-dir", str(args.target_state), "--game-dir", str(args.game_dir), "--bridge-mode", "disabled", "verify-profile"]
    canary_argv = [str(agent), "--state-dir", str(args.target_state), "--game-dir", str(args.game_dir), "--bridge-mode", "native-headless", "--bridge-pipe", EXPECTED_PIPE, "--bridge-dll", str(args.bridge_dll), "--bridge-injector", str(args.bridge_injector), "native-one-generation", "--max-turns", "20", "--timeout", f"{args.timeout_seconds:g}", "--readiness-timeout", f"{args.readiness_timeout_seconds:g}", "--checkpoint-every-advances", str(args.checkpoint_every_advances)]
    try:
        desktop = desktop_identity()
    except OSError as error:
        desktop = f"unavailable: {error}"
    plan = {
        "format_version": 1,
        "kind": "ck3_one_generation_20_turn_canary_handoff",
        "profile": args.profile,
        "mode": "execute" if args.execute else "dry_run",
        "repo_root": str(args.repo_root),
        "git_revision": revision,
        "source_state": str(args.source_state),
        "target_state": str(args.target_state),
        "game_dir": str(args.game_dir),
        "source_checkpoint": source_checkpoint,
        "source_driver_state": source_driver,
        "bridge_dll": dll,
        "bridge_injector": injector,
        "host_observed": {"user": os.environ.get("USERNAME") or os.environ.get("USER"), "desktop": desktop},
        "execute_host_required": {"user": EXPECTED_INTERACTIVE_USER, "desktop": EXPECTED_DESKTOP},
        "copy_contract": "fresh-target, non-overlapping TEMP descendant, Python shutil.copytree without purge or mirror",
        "commands": {"prepare_profile": [str(args.python_path), *prepare], "verify_profile": [str(args.python_path), *verify], "native_one_generation": [str(args.python_path), *canary_argv]},
        "strict_canary_contract": {
            "max_turns": 20,
            "qualified_death_within_bound": "exit 0 / outcome qualified",
            "alive_at_bound": "exit 1 / outcome bounded_incomplete (expected canary result)",
            "blocker_or_harness_failure": "exit 1 / outcome failed (not expected)",
            "helper_exit": "0 only after either native outcome above is structurally verified; native exit remains recorded",
            "note": "native-one-generation never promotes a turn bound to GREEN",
        },
        "known_out_of_scope_debt": {
            "scope": "G2 next-episode startup only; does not block this G1 one-lifetime canary",
            "observation": "production6b episode-seed.json points outside the cloned state and the cloned profile has no xar_episode_seed.ck3",
            "action": "record only; do not mutate the verified production6b source or synthesize an episode seed",
        },
    }
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    user = str(plan["host_observed"]["user"] or "")
    if user.casefold() != EXPECTED_INTERACTIVE_USER.casefold():
        raise CanaryError(f"execute requires the normal xenoa token; observed user is {user}")
    if desktop != EXPECTED_DESKTOP:
        raise CanaryError(f"execute requires {EXPECTED_DESKTOP}; observed desktop is {desktop}")
    before_pids = process_ids("ck3.exe")
    if before_pids:
        raise CanaryError(f"execute requires no existing ck3.exe; observed PID(s): {before_pids}")
    shutil.copytree(args.source_state, args.target_state, copy_function=shutil.copy2, symlinks=True)
    copied_checkpoint = file_identity(args.target_state / "profile" / "save games" / "xar_checkpoint.ck3", args.expected_checkpoint_sha256, "copied checkpoint", args.expected_checkpoint_size)
    copied_driver = driver_anchor(args.target_state, args.expected_checkpoint_sha256, args.expected_checkpoint_size, args.expected_driver_state_sha256)
    if copied_driver["sha256"] != source_driver["sha256"]:
        raise CanaryError("copied driver-state bytes differ from production6b source")
    prepared = invoke_json(
        args.python_path, prepare, {0}, "prepare-profile", args.repo_root
    )
    verified = invoke_json(
        args.python_path, verify, {0}, "verify-profile", args.repo_root
    )
    file_identity(Path(copied_checkpoint["path"]), args.expected_checkpoint_sha256, "prepared checkpoint", args.expected_checkpoint_size)
    prepared_driver = driver_anchor(args.target_state, args.expected_checkpoint_sha256, args.expected_checkpoint_size, args.expected_driver_state_sha256)
    if prepared_driver["sha256"] != source_driver["sha256"]:
        raise CanaryError("prepare/verify changed the copied production6b driver-state bytes")
    canary = invoke_json(
        args.python_path,
        canary_argv,
        {0, 1},
        "native-one-generation",
        args.repo_root,
    )
    post_pids = process_ids("ck3.exe")
    file_identity(source_checkpoint_path, args.expected_checkpoint_sha256, "production6b source checkpoint after canary", args.expected_checkpoint_size)
    source_after = driver_anchor(args.source_state, args.expected_checkpoint_sha256, args.expected_checkpoint_size, args.expected_driver_state_sha256)
    if source_after["sha256"] != source_driver["sha256"]:
        raise CanaryError("production6b source driver state changed during the canary")
    qualification = qualify_result(canary, args.target_state, post_pids)
    summary = {
        "format_version": 1,
        "kind": "ck3_one_generation_20_turn_canary_handoff_result",
        "profile": args.profile,
        "target_state": str(args.target_state),
        "git_revision": revision,
        "copy_exit_code": 0,
        "source_unchanged": True,
        "prepare_profile": prepared["payload"],
        "verify_profile": verified["payload"],
        "canary": {"exit_code": canary["exit_code"], **qualification},
        "strict_exit_note": "exit 1 with bounded_incomplete is expected for a living ruler at the 20-turn bound; it is intentionally not GREEN",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if qualification["expected_canary_outcome"] else 1


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CanaryError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
