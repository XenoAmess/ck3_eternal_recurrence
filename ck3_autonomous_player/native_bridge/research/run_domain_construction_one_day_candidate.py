"""Verify or explicitly execute a sealed construction one-day candidate.

The default path is a read-only no-launch preflight.  ``--execute`` is the
only path that can delegate to the candidate's frozen live runner, and that
path first requires an exact R690 -> R691 ownership record.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


SCHEMA = "xar.ck3.g2_m4_dev14_r691_construction_one_day_candidate_v1"
SEALED_SCHEMA = "xar.ck3.g2_m4_dev14_r691_sealed_candidate_v1"
ROUND = "R691"
OLD_ROUND = "R690"
PIPE_PREFIX = "\\\\.\\pipe\\"
PIPE = PIPE_PREFIX + "xar_ck3_bridge_g2_m4_dev14_r691_construction_one_day_e08f4a1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SAVE_SHA256 = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
SOURCE_COMMIT = "e08f4a1b5a807f176b29ce280383d93d9c051879"
SOURCE_CANDIDATE_MANIFEST_SHA256 = (
    "7FE54643ED8E117F9802327C987BC4C6E36B4C767F8A470DE6983464D07B7584"
)
SOURCE_PREP_MANIFEST_SHA256 = (
    "BD2410AA0302E133B1AFDBBAC6132FD7B2556316E50F0E026FED9F999C753A64"
)
_PIPE_SUFFIX = re.compile(r"[A-Za-z0-9._-]+\Z")
_MUTABLE_ROOTS = {"live-r691", "round-authorization.json"}


class CandidateError(RuntimeError):
    """The sealed candidate or its execution authorization drifted."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateError(message)


def validate_named_pipe(value: object) -> str:
    _require(
        isinstance(value, str) and value.startswith(PIPE_PREFIX),
        f"named pipe must start with {PIPE_PREFIX!r}",
    )
    suffix = value[len(PIPE_PREFIX) :]
    _require(_PIPE_SUFFIX.fullmatch(suffix) is not None, "named-pipe suffix is invalid")
    return value


def build_date_only_arm_step(starting_date_raw: int) -> tuple[int, str]:
    if (
        not isinstance(starting_date_raw, int)
        or isinstance(starting_date_raw, bool)
        or starting_date_raw <= 0
    ):
        raise ValueError("starting_date_raw must be a positive integer")
    target = starting_date_raw + 24
    return target, (
        "research-arm-tactical-daily-sentinel-v1-"
        f"{starting_date_raw}-to-{target}-speed-3-mode-terminal-a-0"
    )


def classify_counter_deltas(deltas: dict[str, int]) -> str:
    producer = deltas.get("producer_calls")
    accepted = deltas.get("accepted_captures")
    if not isinstance(producer, int) or isinstance(producer, bool) or producer < 0:
        raise CandidateError("producer_calls delta is malformed")
    if not isinstance(accepted, int) or isinstance(accepted, bool) or accepted < 0:
        raise CandidateError("accepted_captures delta is malformed")
    if producer == 0:
        return "BOUNDED_NO_GO"
    if accepted == 0:
        raise CandidateError("producer ran without an accepted application-main capture")
    return "GREEN"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _safe_candidate_file(root: Path, relative: object) -> Path:
    _require(isinstance(relative, str) and bool(relative), "sealed path is missing")
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise CandidateError(f"sealed path escapes candidate root: {relative}") from error
    return target


def _candidate_files(root: Path) -> set[str]:
    result: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.split("/", 1)[0] in _MUTABLE_ROOTS:
            continue
        result.add(relative)
    return result


def _git(source: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "-C", str(source), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
        env=environment,
    )
    _require(completed.returncode == 0, f"Git check failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _windows_ck3_inventory() -> list[dict[str, object]]:
    """Read CK3 identities directly through Toolhelp and Win32 APIs."""
    if os.name != "nt":
        return []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.wintypes.LONG),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.wintypes.WCHAR * 260),
        ]

    kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32FirstW.restype = ctypes.wintypes.BOOL
    kernel32.Process32NextW.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32NextW.restype = ctypes.wintypes.BOOL
    kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
    kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.LPWSTR,
        ctypes.POINTER(ctypes.wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = ctypes.wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.FILETIME),
        ctypes.POINTER(ctypes.wintypes.FILETIME),
        ctypes.POINTER(ctypes.wintypes.FILETIME),
        ctypes.POINTER(ctypes.wintypes.FILETIME),
    ]
    kernel32.GetProcessTimes.restype = ctypes.wintypes.BOOL
    kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
    kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    _require(
        snapshot != ctypes.wintypes.HANDLE(-1).value,
        f"Toolhelp snapshot failed: winerror={ctypes.get_last_error()}",
    )
    entries: list[dict[str, int | str]] = []
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        _require(
            bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry))),
            f"Toolhelp first process failed: winerror={ctypes.get_last_error()}",
        )
        while True:
            if str(entry.szExeFile).casefold() == "ck3.exe":
                entries.append(
                    {
                        "pid": int(entry.th32ProcessID),
                        "parent_pid": int(entry.th32ParentProcessID),
                        "name": str(entry.szExeFile),
                    }
                )
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                error = ctypes.get_last_error()
                _require(error == 18, f"Toolhelp next process failed: winerror={error}")
                break
    finally:
        kernel32.CloseHandle(snapshot)

    result: list[dict[str, object]] = []
    for entry in entries:
        pid = int(entry["pid"])
        handle = kernel32.OpenProcess(0x00001000, False, pid)
        _require(bool(handle), f"CK3 process {pid} identity is unreadable")
        try:
            path_buffer = ctypes.create_unicode_buffer(32768)
            path_length = ctypes.wintypes.DWORD(len(path_buffer))
            _require(
                bool(
                    kernel32.QueryFullProcessImageNameW(
                        handle, 0, path_buffer, ctypes.byref(path_length)
                    )
                ),
                f"CK3 process {pid} image path is unreadable",
            )
            creation = ctypes.wintypes.FILETIME()
            exit_time = ctypes.wintypes.FILETIME()
            kernel_time = ctypes.wintypes.FILETIME()
            user_time = ctypes.wintypes.FILETIME()
            _require(
                bool(
                    kernel32.GetProcessTimes(
                        handle,
                        ctypes.byref(creation),
                        ctypes.byref(exit_time),
                        ctypes.byref(kernel_time),
                        ctypes.byref(user_time),
                    )
                ),
                f"CK3 process {pid} creation time is unreadable",
            )
        finally:
            kernel32.CloseHandle(handle)
        ticks = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        unix_ticks = ticks - 116_444_736_000_000_000
        seconds, fractional = divmod(unix_ticks, 10_000_000)
        stamp = datetime.fromtimestamp(seconds, timezone.utc)
        result.append(
            {
                **entry,
                "executable": path_buffer.value,
                "creation_date": stamp.strftime("%Y%m%d%H%M%S")
                + f".{fractional // 10:06d}+000",
            }
        )
    return sorted(result, key=lambda item: int(item["pid"]))


def _verify_candidate(
    root: Path,
    game_dir: Path,
    *,
    require_seal: bool,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    game_dir = game_dir.expanduser().resolve()
    _require(root.is_dir(), f"candidate root is missing: {root}")
    manifest_path = root / "candidate-manifest.json"
    sidecar_path = root / "candidate-manifest.sha256"
    manifest = _read_json(manifest_path)
    recorded_manifest = sidecar_path.read_text(encoding="ascii").split()[0].upper()
    _require(sha256(manifest_path) == recorded_manifest, "candidate manifest hash differs")
    _require(manifest.get("schema") == SCHEMA, "candidate schema differs")
    _require(manifest.get("status") == "sealed-no-launch", "candidate status differs")
    _require(manifest.get("source_commit") == SOURCE_COMMIT, "source commit differs")
    _require(
        manifest.get("source_candidate_manifest_sha256")
        == SOURCE_CANDIDATE_MANIFEST_SHA256,
        "source candidate manifest differs",
    )
    _require(
        manifest.get("source_prep_manifest_sha256") == SOURCE_PREP_MANIFEST_SHA256,
        "source prep manifest differs",
    )
    next_live = manifest.get("next_live")
    _require(isinstance(next_live, dict), "next-live contract is missing")
    _require(next_live.get("old_round") == OLD_ROUND, "old round differs")
    _require(next_live.get("new_round") == ROUND, "new round differs")
    _require(next_live.get("round_allocated") is False, "candidate allocated CK3 ownership")
    _require(next_live.get("unique_pipe") == PIPE, "candidate named pipe differs")
    _require(validate_named_pipe(next_live.get("unique_pipe")) == PIPE, "pipe differs")
    _require(next_live.get("state_relative_path") == "state-r691", "state path differs")
    _require(next_live.get("live_relative_path") == "live-r691", "live path differs")
    _require(next_live.get("same_round_retry") is False, "same-round retry is enabled")

    source = root / "source-repo"
    _require(_git(source, "rev-parse", "HEAD") == SOURCE_COMMIT, "source HEAD differs")
    _require(
        not _git(source, "status", "--porcelain=v1", "--untracked-files=no"),
        "source repository tracked files differ",
    )
    game_exe = game_dir / "binaries" / "ck3.exe"
    _require(game_exe.is_file(), f"game executable is missing: {game_exe}")
    _require(sha256(game_exe) == EXE_SHA256, "exact-build game executable differs")
    for relative in (
        "source-save/dev3b_r639.ck3",
        "state-r691/profile/save games/dev3b_r639.ck3",
    ):
        path = root / relative
        _require(path.is_file() and sha256(path) == SAVE_SHA256, f"save differs: {relative}")
    _require(
        (root / "state-r691/profile/xar-autoplayer-environment.json").is_file(),
        "prepared environment manifest is missing",
    )
    descriptor = (root / "state-r691/profile/mod/xar_autoplayer.mod").read_text(
        encoding="utf-8-sig"
    )
    _require(
        (root / "state-r691/profile/mod-content/xar-production").as_posix() in descriptor,
        "profile descriptor is not bound to the R691 candidate path",
    )
    scripts = manifest.get("runner")
    _require(isinstance(scripts, dict), "runner contract is missing")
    forbidden_shell = "power" + "shell"
    forbidden_alias = "pw" + "sh"
    for name in ("entry", "live", "preflight"):
        record = scripts.get(name)
        _require(isinstance(record, dict), f"runner {name} record is missing")
        path = _safe_candidate_file(root, record.get("path"))
        _require(path.is_file() and sha256(path) == record.get("sha256"), f"runner differs: {name}")
        source_text = path.read_text(encoding="utf-8-sig").casefold()
        _require(
            forbidden_shell not in source_text and forbidden_alias not in source_text,
            f"runner invokes a forbidden process shell: {name}",
        )
    live_source = (root / "run_r691.py").read_text(encoding="utf-8-sig")
    _require(live_source.count('"resume-map"') == 1, "live runner resume site differs")
    _require(live_source.count('"set-speed-3"') == 1, "live runner speed site differs")
    _require("live-r690" not in live_source and "state-r690" not in live_source, "old mutable path remains in live runner")
    _require(PIPE in live_source, "live runner pipe differs")

    if require_seal:
        sealed_path = root / "sealed-prep-manifest.json"
        sealed_sidecar = root / "sealed-prep-manifest.sha256"
        sealed = _read_json(sealed_path)
        recorded_seal = sealed_sidecar.read_text(encoding="ascii").split()[0].upper()
        _require(sha256(sealed_path) == recorded_seal, "sealed manifest hash differs")
        _require(sealed.get("schema") == SEALED_SCHEMA, "sealed schema differs")
        _require(sealed.get("status") == "sealed-no-launch", "sealed status differs")
        rows = sealed.get("files")
        _require(isinstance(rows, list), "sealed file inventory is missing")
        expected: set[str] = set()
        for row in rows:
            _require(isinstance(row, dict), "sealed file row is malformed")
            path = _safe_candidate_file(root, row.get("path"))
            relative = path.relative_to(root).as_posix()
            expected.add(relative)
            _require(path.is_file(), f"sealed file is missing: {relative}")
            _require(path.stat().st_size == row.get("size_bytes"), f"sealed size differs: {relative}")
            _require(sha256(path) == row.get("sha256"), f"sealed hash differs: {relative}")
        expected.update({"sealed-prep-manifest.json", "sealed-prep-manifest.sha256"})
        _require(_candidate_files(root) == expected, "candidate has unsealed or missing files")
    else:
        _require(
            not (root / "sealed-prep-manifest.json").exists()
            and not (root / "sealed-prep-manifest.sha256").exists(),
            "pre-seal validation received an already sealed candidate",
        )

    inventory = _windows_ck3_inventory()
    _require(not inventory, "CK3 inventory is nonzero; no-launch preflight remains RED")
    return {
        "schema": "xar.ck3.g2_m4_dev14_r691_no_launch_preflight_v1",
        "status": "GREEN_NO_LAUNCH",
        "mode": "optimized" if not __debug__ else "normal",
        "candidate_root": str(root),
        "candidate_manifest_sha256": recorded_manifest,
        "sealed_manifest_sha256": (
            sha256(root / "sealed-prep-manifest.json") if require_seal else None
        ),
        "old_round": OLD_ROUND,
        "new_round": ROUND,
        "state_relative_path": "state-r691",
        "live_relative_path": "live-r691",
        "unique_pipe": PIPE,
        "ck3_launched": False,
        "ck3_processes": inventory,
        "public_surface_changed": False,
    }


def _verify_authorization(root: Path) -> dict[str, Any]:
    authorization = _read_json(root / "round-authorization.json")
    _require(authorization.get("status") == "AUTHORIZED", "round is not authorized")
    _require(authorization.get("old_round") == OLD_ROUND, "authorization old round differs")
    _require(authorization.get("new_round") == ROUND, "authorization new round differs")
    _require(
        authorization.get("r690_confirmed_terminated") is True,
        "R690 termination is unconfirmed",
    )
    _require(
        isinstance(authorization.get("global_ck3_zero_confirmed_at"), str)
        and bool(authorization["global_ck3_zero_confirmed_at"].strip()),
        "global zero-CK3 confirmation is missing",
    )
    _require(
        isinstance(authorization.get("owner"), str)
        and bool(authorization["owner"].strip()),
        "exclusive CK3 owner is missing",
    )
    return authorization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--pre-seal", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root = args.candidate_root.expanduser().resolve()
    report = _verify_candidate(root, args.game_dir, require_seal=not args.pre_seal)
    if not args.execute:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    _require(not args.pre_seal, "execution cannot use a pre-seal candidate")
    _verify_authorization(root)
    _require(not (root / "live-r691").exists(), "R691 live output already exists")
    environment = dict(os.environ)
    environment["XAR_CK3_GAME_DIR"] = str(args.game_dir.expanduser().resolve())
    environment["XAR_CK3_PIPE_NAME"] = PIPE
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    source = root / "source-repo" / "ck3_autonomous_player" / "src"
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(source) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    completed = subprocess.run(
        [str(args.python.expanduser().resolve()), "-B", str(root / "run_r691.py")],
        cwd=root,
        check=False,
        env=environment,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
