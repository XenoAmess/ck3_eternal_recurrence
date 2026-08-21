"""Destructive-supervisor crash probe with an independent verifier.

The outer verifier never owns the CK3 Job handle.  A sacrificial supervisor
creates CK3 and a synthetic parent/child tree inside one named kill-on-close
Job, arms the detached watchdog, and is then terminated through a pinned
process handle.  Only the surviving outer process can finalize the report.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

from .environment import (
    EXPECTED_GAME_VERSION,
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    REPO_ROOT,
    _contract_digest,
    EnvironmentSpec,
    ck3_process_inventory,
    doctor,
    ensure_state_path_safe,
    is_relative_to,
    mod_source_fingerprint,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
    verify_profile,
    write_bytes_atomic,
    write_json_atomic,
)
from .errors import AgentError
from .integrity import protected_snapshot, verify_protected_unchanged
from .locking import (
    _launch_lock_name,
    _lock_name,
    exclusive_launch_lock,
    exclusive_state_lock,
)
from .runtime import (
    MAIN_MENU_REGION,
    _ocr_items,
    _assign_process_to_job,
    _authenticated_watchdog_state,
    _create_kill_on_close_job,
    _create_suspended_process,
    _job_active_processes,
    _process_identity,
    _same_executable,
    _wait_process_identity,
    append_event,
    launch,
    parse_runtime_attestation,
    normalize_ocr_text,
    stop_tracked,
    utc_now,
    validate_event_chain,
    validate_final_report_payload,
    unique_exact_ocr_match,
    wait_for_main_menu,
    wait_for_runtime_attestation,
    write_gzip_json_atomic,
)
from .rules import MOD_RULES


CRASH_EXIT_CODE = 77
OUTER_LOST_EXIT_CODE = 86
CONTROL_FILE_LABELS = {
    "record",
    "ready",
    "unsafe_marker",
    "watchdog_error",
}
REPORT_BINDING_EXCLUSIONS = {
    "finalized",
    "ok",
    "final_event_sha256",
    "event_chain",
    "report_body_sha256",
}
REPLAY_TRUST_MODEL = {
    "integrity": "unkeyed_sha256",
    "claim": "archive_schema_and_internal_consistency_only",
    "historical_execution_authenticity_proven": False,
}
_REPLAY_OCR_CACHE: dict[str, list[dict[str, object]]] = {}


def _canonical_job_name(probe_nonce: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{32}", probe_nonce):
        raise AgentError("crash probe nonce must be 32 lowercase hexadecimal characters")
    return f"XarAutoplayer-Crash-{probe_nonce}"


def _report_body_sha256(report: dict[str, object]) -> str:
    body = {
        key: value
        for key, value in report.items()
        if key not in REPORT_BINDING_EXCLUSIONS
    }
    return snapshot_digest(body)


def _artifact_entry(path: Path, run_dir: Path) -> dict[str, str]:
    resolved = path.resolve()
    run_dir = run_dir.resolve()
    if not is_relative_to(resolved, run_dir):
        raise AgentError(f"artifact escaped its crash run: {resolved}")
    return {
        "path": resolved.relative_to(run_dir).as_posix(),
        "sha256": sha256_file(resolved),
    }


def _verify_artifact_entry(
    entry: object, run_dir: Path, label: str
) -> Path:
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
        raise AgentError(f"{label} artifact reference differs")
    relative = Path(str(entry["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise AgentError(f"{label} artifact path is not run-relative")
    path = (run_dir.resolve() / relative).resolve()
    if not is_relative_to(path, run_dir.resolve()):
        raise AgentError(f"{label} artifact escaped its crash run")
    if not path.is_file() or sha256_file(path) != entry["sha256"]:
        raise AgentError(f"{label} artifact hash differs")
    return path


def _replay_main_menu_ocr(
    screenshot: Path, screenshot_sha256: str
) -> list[dict[str, object]]:
    """Re-run the live OCR adapter so archived text is bound to PNG pixels."""
    cached = _REPLAY_OCR_CACHE.get(screenshot_sha256)
    if cached is not None:
        return cached
    from PIL import Image

    with Image.open(screenshot) as image:
        image.load()
        replayed = _ocr_items(image, MAIN_MENU_REGION)
    _REPLAY_OCR_CACHE[screenshot_sha256] = replayed
    return replayed


def _recorded_run_dir(report: dict[str, object]) -> Path:
    """Return the run root recorded at execution time.

    Artifact bytes are resolved below the directory supplied to the replay
    command.  Absolute paths embedded in the live handoff are instead compared
    with this recorded origin, so a complete run directory remains verifiable
    after it is copied to another parent directory.
    """
    recorded = Path(str(report.get("run_dir", "")))
    if not recorded.is_absolute() or recorded.name != report.get("run_id"):
        raise AgentError("crash report recorded run directory differs")
    return recorded.resolve()


def _recorded_reference_matches(
    value: object, recorded_run: Path, relative: str
) -> bool:
    candidate = Path(str(value))
    return candidate.is_absolute() and candidate.resolve() == (
        recorded_run / Path(relative)
    ).resolve()


def _validate_release_manifest_archive(
    manifest: object, environment: dict[str, object]
) -> None:
    """Validate the archived production projection manifest semantically."""
    if not isinstance(manifest, dict) or set(manifest) != {
        "files",
        "format_version",
        "git_sha",
        "git_tag",
        "mod_version",
        "workshop_item_id",
    }:
        raise AgentError("archived production manifest schema differs")
    mod = environment.get("mod")
    if not isinstance(mod, dict):
        raise AgentError("archived environment mod contract differs")
    identity = mod.get("release_identity")
    if (
        not isinstance(identity, dict)
        or manifest.get("format_version") != identity.get("format_version")
        or manifest.get("mod_version") != identity.get("mod_version")
        or manifest.get("git_tag") != identity.get("git_tag")
        or manifest.get("workshop_item_id") != identity.get("workshop_item_id")
        or manifest.get("git_sha") != mod.get("git_revision")
    ):
        raise AgentError("archived production manifest identity differs")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) < 4:
        raise AgentError("archived production manifest file list differs")
    paths: list[str] = []
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            raise AgentError("archived production manifest file entry differs")
        relative = Path(str(entry.get("path", "")))
        digest = str(entry.get("sha256", ""))
        size = entry.get("size")
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or relative.as_posix() != str(entry.get("path"))
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or type(size) is not int
            or size < 0
        ):
            raise AgentError("archived production manifest file entry differs")
        paths.append(relative.as_posix())
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise AgentError("archived production manifest paths differ")
    if not {
        "descriptor.mod",
        "common/game_rules/xar_game_rules.txt",
        "common/on_action/eternal_recurrence_on_actions.txt",
        "events/xar_events.txt",
    } <= set(paths):
        raise AgentError("archived production manifest lacks required runtime files")
    projected_tree = {
        str(entry["path"]): {
            "size": entry["size"],
            "sha256": entry["sha256"],
        }
        for entry in files
    }
    if (
        len(files) != mod.get("production_file_count")
        or snapshot_digest(projected_tree) != mod.get("production_tree_sha256")
    ):
        raise AgentError("archived production manifest tree digest differs")


def _validate_process_identity_payload(identity: object, label: str) -> None:
    if (
        not isinstance(identity, dict)
        or set(identity)
        != {
            "pid",
            "parent_pid",
            "name",
            "executable",
            "creation_date",
            "command_line",
        }
        or type(identity.get("pid")) is not int
        or identity["pid"] <= 0
        or type(identity.get("parent_pid")) is not int
        or identity["parent_pid"] < 0
        or not isinstance(identity.get("name"), str)
        or not identity["name"]
        or not isinstance(identity.get("executable"), str)
        or not Path(identity["executable"]).is_absolute()
        or not isinstance(identity.get("creation_date"), str)
        or not identity["creation_date"]
        or not isinstance(identity.get("command_line"), str)
        or not identity["command_line"]
    ):
        raise AgentError(f"{label} process identity payload differs")


def _validate_environment_archive_semantics(environment: dict[str, object]) -> None:
    required_top = {
        "format_version",
        "agent_version",
        "agent_runtime",
        "prepared_at",
        "state_dir",
        "profile_dir",
        "game",
        "mod",
        "load_profile",
        "rules",
        "display",
        "dlc",
        "persistent_tutorial_state",
        "legality",
        "environment_sha256",
    }
    if set(environment) != required_top or environment.get("format_version") != 1:
        raise AgentError("archived environment schema differs")
    runtime = environment.get("agent_runtime")
    if not isinstance(runtime, dict):
        raise AgentError("archived agent runtime fingerprint differs")
    runtime_without_hash = dict(runtime)
    runtime_hash = runtime_without_hash.pop("sha256", None)
    files = runtime.get("files")
    git = runtime.get("git")
    if (
        runtime_hash != snapshot_digest(runtime_without_hash)
        or not isinstance(files, list)
        or len(files) < 5
        or runtime.get("file_count") != len(files)
        or not isinstance(git, dict)
        or git.get("all_files_tracked") is not True
        or git.get("dirty") is not False
        or git.get("untracked_runtime_files") != []
        or git.get("status") != []
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(git.get("selected_runtime_revision", ""))
        )
    ):
        raise AgentError("archived agent runtime fingerprint differs")
    runtime_paths: set[str] = set()
    for entry in files:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "size", "sha256"}
            or not isinstance(entry.get("path"), str)
            or type(entry.get("size")) is not int
            or entry["size"] < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", "")))
        ):
            raise AgentError("archived agent runtime file entry differs")
        runtime_paths.add(entry["path"])
    if not {
        "agent/src/xar_autoplayer/crash_probe.py",
        "agent/src/xar_autoplayer/environment.py",
        "agent/src/xar_autoplayer/process_watchdog.py",
        "agent/src/xar_autoplayer/runtime.py",
        "repo/tools/build_release.py",
    } <= runtime_paths:
        raise AgentError("archived agent runtime lacks safety-critical files")

    mod = environment.get("mod")
    provenance = mod.get("source_provenance") if isinstance(mod, dict) else None
    if (
        not isinstance(mod, dict)
        or not isinstance(provenance, dict)
        or not re.fullmatch(r"[0-9a-f]{40}", str(mod.get("git_revision", "")))
        or provenance.get("git_revision") != mod.get("git_revision")
        or provenance.get("git_dirty") is not False
        or provenance.get("git_status") != []
        or provenance.get("all_release_files_tracked") is not True
        or provenance.get("untracked_release_files") != []
        or provenance.get("release_source_file_count")
        != mod.get("production_file_count")
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(provenance.get("release_source_sha256", ""))
        )
    ):
        raise AgentError("archived production source provenance differs")

    game = environment.get("game")
    expected_game_fields = {
        "raw_version",
        "display_version",
        "distribution",
        "launcher_settings_sha256",
        "executable",
        "executable_sha256",
        "vanilla_rules",
        "vanilla_rules_sha256",
        "debug_mode",
    }
    if (
        not isinstance(game, dict)
        or set(game) != expected_game_fields
        or game.get("raw_version") != EXPECTED_GAME_VERSION
        or not isinstance(game.get("display_version"), str)
        or not game["display_version"]
        or not isinstance(game.get("distribution"), str)
        or not game["distribution"]
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(game.get("launcher_settings_sha256", ""))
        )
        or not Path(str(game.get("executable", ""))).is_absolute()
        or Path(str(game.get("executable", ""))).name.casefold() != "ck3.exe"
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(game.get("executable_sha256", ""))
        )
        or not Path(str(game.get("vanilla_rules", ""))).is_absolute()
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(game.get("vanilla_rules_sha256", ""))
        )
        or game.get("debug_mode") is not False
    ):
        raise AgentError("archived game identity contract differs")

    load_profile = environment.get("load_profile")
    display = environment.get("display")
    legality = environment.get("legality")
    rules = environment.get("rules")
    profile = rules.get("profile") if isinstance(rules, dict) else None
    if (
        not isinstance(load_profile, dict)
        or load_profile.get("enabled_mods") != [OUTER_DESCRIPTOR_REF]
        or load_profile.get("disabled_dlcs") != []
        or not isinstance(display, dict)
        or display.get("language") != "l_simp_chinese"
        or display.get("resolution") != [2560, 1440]
        or display.get("mode") != "fullscreen"
        or not isinstance(legality, dict)
        or legality.get("production_only") is not True
        or legality.get("single_mod") is not True
        or legality.get("visible_ui_only_for_decisions") is not True
        or legality.get("save_rollback") is not False
        or not isinstance(rules, dict)
        or set(rules)
        != {
            "source",
            "source_sha256",
            "declared_vanilla_rule_count",
            "profile",
            "profile_sha256",
            "ironman",
        }
        or rules.get("source") != game.get("vanilla_rules")
        or rules.get("source_sha256") != game.get("vanilla_rules_sha256")
        or rules.get("declared_vanilla_rule_count") != 81
        or rules.get("ironman") is not False
        or not isinstance(profile, list)
        or len(profile) != 84
    ):
        raise AgentError("archived legal profile contract differs")
    if any(
        not isinstance(entry, dict)
        or set(entry) != {"rule", "setting"}
        or not isinstance(entry.get("rule"), str)
        or not entry["rule"]
        or not isinstance(entry.get("setting"), str)
        or not entry["setting"]
        for entry in profile
    ):
        raise AgentError("archived game-rule profile entry differs")
    serialized_profile = json.dumps(
        profile, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    expected_mod_profile = [
        {"rule": rule, "setting": setting} for rule, setting in MOD_RULES
    ]
    vanilla_profile = profile[:81]
    settings = {
        (entry.get("rule"), entry.get("setting"))
        for entry in profile
    }
    if (
        len(settings) != 84
        or len({entry["rule"] for entry in profile}) != 84
        or len({entry["setting"] for entry in profile}) != 84
        or profile[81:] != expected_mod_profile
        or any(entry["rule"].startswith("xar_") for entry in vanilla_profile)
        or rules.get("profile_sha256")
        != hashlib.sha256(serialized_profile).hexdigest()
    ):
        raise AgentError("archived Growth + 100% rule contract differs")


def _require_committed_environment(manifest: dict[str, object]) -> None:
    agent_git = manifest.get("agent_runtime", {}).get("git", {})
    if (
        not agent_git.get("all_files_tracked")
        or agent_git.get("dirty")
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(agent_git.get("selected_runtime_revision", ""))
        )
    ):
        raise AgentError("crash probe requires a committed, clean agent runtime")
    current_mod = mod_source_fingerprint()
    recorded_mod = manifest.get("mod", {}).get("source_provenance", {})
    if (
        current_mod.get("git_dirty")
        or not current_mod.get("all_release_files_tracked")
        or current_mod.get("release_source_sha256")
        != recorded_mod.get("release_source_sha256")
    ):
        raise AgentError("crash probe requires committed, clean release sources")


def _wait_json(
    path: Path,
    process: subprocess.Popen[object],
    timeout: float,
    *,
    require_process_running: bool = True,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except (OSError, json.JSONDecodeError) as error:
                last_error = error
        if require_process_running and process.poll() is not None:
            raise AgentError(
                f"crash subject exited before {path.name}: rc={process.returncode}"
            )
        time.sleep(0.1)
    detail = f": {last_error}" if last_error else ""
    raise AgentError(f"timeout waiting for {path.name}{detail}")


def _wait_file(path: Path, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return
        time.sleep(0.1)
    raise AgentError(f"timeout waiting for {path.name}")


def _pin_process(
    identity: dict[str, object], *, allow_terminate: bool = False
) -> object:
    import win32api
    import win32con
    import win32process

    rights = (
        win32con.SYNCHRONIZE
        | win32con.PROCESS_QUERY_INFORMATION
        | win32con.PROCESS_QUERY_LIMITED_INFORMATION
        | win32con.PROCESS_VM_READ
    )
    if allow_terminate:
        rights |= win32con.PROCESS_TERMINATE
    pid = int(identity["pid"])
    handle = win32api.OpenProcess(rights, False, pid)
    try:
        current = _process_identity(pid)
        if (
            current is None
            or current["creation_date"] != identity["creation_date"]
            or not _same_executable(current["executable"], identity["executable"])
        ):
            raise AgentError(f"process identity changed before pin: {identity!r}")
        pinned_image = Path(win32process.GetModuleFileNameEx(handle, 0)).resolve()
        if not _same_executable(pinned_image, identity["executable"]):
            raise AgentError(f"pinned process image differs: {pinned_image}")
        return handle
    except Exception:
        win32api.CloseHandle(handle)
        raise


def _wait_pinned_exit(handle: object, label: str, timeout: float = 20) -> int:
    import win32event
    import win32process

    result = win32event.WaitForSingleObject(handle, int(timeout * 1000))
    if result != win32event.WAIT_OBJECT_0:
        raise AgentError(f"pinned {label} did not exit: wait status {result}")
    return int(win32process.GetExitCodeProcess(handle))


def _require_mutex_owned_elsewhere(name: str, label: str) -> None:
    import win32api
    import win32event

    handle = win32event.CreateMutex(None, False, name)
    try:
        result = win32event.WaitForSingleObject(handle, 0)
        if result == win32event.WAIT_TIMEOUT:
            return
        if result == win32event.WAIT_OBJECT_0:
            win32event.ReleaseMutex(handle)
        raise AgentError(f"{label} is not held by the outer verifier")
    finally:
        win32api.CloseHandle(handle)


def _command_arguments(command_line: str) -> list[str]:
    if os.name != "nt":
        import shlex

        return shlex.split(command_line)
    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    argc = ctypes.c_int()
    parse = shell32.CommandLineToArgvW
    parse.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parse.restype = ctypes.POINTER(wintypes.LPWSTR)
    argv = parse(command_line, ctypes.byref(argc))
    if not argv:
        raise AgentError("outer command line could not be parsed")
    try:
        return [str(argv[index]) for index in range(argc.value)]
    finally:
        kernel32.LocalFree(argv)


def _validate_subject_invocation(
    spec: EnvironmentSpec,
    *,
    probe_nonce: str,
    handoff_path: Path,
    handoff_sha256: str,
    armed_path: Path,
    watchdog_final: Path,
    artifacts: Path,
    outer_identity: dict[str, object],
) -> dict[str, object]:
    """Authenticate the hidden subject entry before it can write or launch."""
    _canonical_job_name(probe_nonce)
    state_dir = spec.state_dir.resolve()
    artifacts = artifacts.resolve()
    runs_dir = (state_dir / "runs").resolve()
    if (
        artifacts.name != "artifacts"
        or artifacts.parent.parent.resolve() != runs_dir
        or not re.fullmatch(
            r"[0-9]{8}T[0-9]{6}Z-crash-[0-9a-f]{8}", artifacts.parent.name
        )
        or not artifacts.is_dir()
    ):
        raise AgentError("crash subject artifacts path is outside its exact run")
    expected_paths = {
        "handoff": artifacts / f"handoff-{probe_nonce}.json",
        "armed": artifacts / f"armed-{probe_nonce}.json",
        "watchdog_final": artifacts / f"watchdog-final-{probe_nonce}.json",
    }
    supplied_paths = {
        "handoff": handoff_path.resolve(),
        "armed": armed_path.resolve(),
        "watchdog_final": watchdog_final.resolve(),
    }
    for label, expected in expected_paths.items():
        if supplied_paths[label] != expected.resolve():
            raise AgentError(f"crash subject {label} path differs from its nonce")
    if not handoff_path.is_file() or sha256_file(handoff_path) != handoff_sha256:
        raise AgentError("crash subject handoff hash differs")
    if armed_path.exists() or armed_path.with_name(armed_path.name + ".tmp").exists():
        raise AgentError("crash subject armed evidence already exists")
    if watchdog_final.exists() or watchdog_final.with_name(
        watchdog_final.name + ".tmp"
    ).exists():
        raise AgentError("crash subject watchdog evidence already exists")

    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    if not isinstance(handoff, dict):
        raise AgentError("crash subject handoff root is not an object")
    expected_outer = handoff.get("outer")
    if not isinstance(expected_outer, dict):
        raise AgentError("crash subject handoff lacks outer identity")
    current = _process_identity(os.getpid())
    actual_outer = _process_identity(int(outer_identity["pid"]))
    if (
        current is None
        or int(current["parent_pid"]) != int(outer_identity["pid"])
        or actual_outer is None
        or actual_outer["creation_date"] != outer_identity["creation_date"]
        or not _same_executable(
            actual_outer["executable"], outer_identity["executable"]
        )
        or int(expected_outer.get("pid", -1)) != int(actual_outer["pid"])
        or expected_outer.get("creation_date") != actual_outer["creation_date"]
        or not _same_executable(
            expected_outer.get("executable", ""), actual_outer["executable"]
        )
    ):
        raise AgentError("crash subject is not a direct child of its authenticated outer")
    outer_arguments = _command_arguments(
        str(actual_outer.get("command_line", ""))
    )
    if (
        outer_arguments.count("crash-smoke") != 1
        or "_crash-subject" in outer_arguments
    ):
        raise AgentError("crash subject outer command is not the public crash-smoke entry")

    owner_path = state_dir / "control" / "owner.json"
    if not owner_path.is_file() or sha256_file(owner_path) != handoff.get(
        "owner_sha256"
    ):
        raise AgentError("crash subject state-lock owner evidence differs")
    owner = json.loads(owner_path.read_text(encoding="utf-8"))
    if (
        int(owner.get("pid", -1)) != int(actual_outer["pid"])
        or owner.get("purpose") != "crash-smoke"
        or Path(str(owner.get("state_dir", ""))).resolve() != state_dir
    ):
        raise AgentError("crash subject state-lock owner differs")
    expected_handoff = {
        "format_version": 1,
        "probe_nonce": probe_nonce,
        "run_id": artifacts.parent.name,
        "state_dir": str(state_dir),
        "artifacts": str(artifacts),
        "armed": str(armed_path.resolve()),
        "watchdog_final": str(watchdog_final.resolve()),
        "outer": expected_outer,
        "environment_sha256": handoff.get("environment_sha256"),
        "owner_sha256": handoff.get("owner_sha256"),
    }
    if handoff != expected_handoff:
        raise AgentError("crash subject handoff fields differ")
    _require_mutex_owned_elsewhere(_lock_name(state_dir), "state mutex")
    _require_mutex_owned_elsewhere(
        _launch_lock_name(spec.game_exe), "global launch mutex"
    )
    return handoff


def _start_outer_guard(outer_identity: dict[str, object]) -> None:
    """Exit the sacrificial subject immediately when its exact outer dies."""
    import win32event

    outer_handle = _pin_process(outer_identity)
    started = threading.Event()

    def guard() -> None:
        started.set()
        try:
            result = win32event.WaitForSingleObject(
                outer_handle, win32event.INFINITE
            )
        except Exception:
            os._exit(OUTER_LOST_EXIT_CODE + 1)
        if result == win32event.WAIT_OBJECT_0:
            os._exit(OUTER_LOST_EXIT_CODE)
        os._exit(OUTER_LOST_EXIT_CODE + 1)

    threading.Thread(
        target=guard, name="xar-crash-outer-guard", daemon=True
    ).start()
    if not started.wait(timeout=2):
        raise AgentError("crash subject outer guard did not start")


def _named_job_absent(name: str) -> bool:
    """Prove the named Job object was destroyed when its last owner died."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_job = kernel32.OpenJobObjectW
    open_job.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    open_job.restype = wintypes.HANDLE
    handle = open_job(0x0004, False, name)  # JOB_OBJECT_QUERY
    if handle:
        kernel32.CloseHandle(handle)
        return False
    return ctypes.get_last_error() == 2  # ERROR_FILE_NOT_FOUND


def _wait_named_job_absent(name: str, timeout: float = 5) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _named_job_absent(name):
            return
        time.sleep(0.05)
    raise AgentError("named crash Job still exists after owner death")


def _wait_global_ck3_quiet(seconds: float = 5, timeout: float = 30) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    quiet_since: float | None = None
    last: dict[str, object] | None = None
    polls = 0
    while time.monotonic() < deadline:
        last = ck3_process_inventory()
        polls += 1
        if last["processes"]:
            quiet_since = None
        elif quiet_since is None:
            quiet_since = time.monotonic()
        elif time.monotonic() - quiet_since >= seconds:
            return {
                **last,
                "continuous_empty_seconds": seconds,
                "poll_count": polls,
            }
        time.sleep(0.2)
    raise AgentError(f"global CK3 inventory did not remain empty: {last!r}")


def _read_subject_failure(run_dir: Path) -> str:
    path = run_dir / "artifacts" / "subject-error.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return "subject produced no structured failure detail"


def _start_synthetic_job_tree(
    job_handle: object, artifacts: Path, token: str
) -> tuple[object, dict[str, object], dict[str, object]]:
    supervisor = _process_identity(os.getpid())
    if supervisor is None:
        raise AgentError("synthetic Job owner identity disappeared")
    actual_python = Path(str(supervisor["executable"])).resolve()
    child_pid_file = artifacts / f"sentinel-child-{token}.txt"
    sentinel_code = (
        "import pathlib,subprocess,sys,time;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(3600)']);"
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid),encoding='ascii');"
        "time.sleep(3600)"
    )
    parent = _create_suspended_process(
        [str(actual_python), "-c", sentinel_code, str(child_pid_file)],
        actual_python.parent,
    )
    try:
        _assign_process_to_job(job_handle, parent)
        parent.resume()
        _wait_file(child_pid_file, 10)
        child_pid = int(child_pid_file.read_text(encoding="ascii").strip())
        parent_identity = _wait_process_identity(parent.pid)
        child_identity = _wait_process_identity(child_pid)
        if parent_identity is None or child_identity is None:
            raise AgentError("synthetic Job process tree identity is incomplete")
        parent_identity["executable"] = str(parent.image_path())
        return parent, parent_identity, child_identity
    except Exception:
        parent.terminate_exact()
        parent.close()
        raise


def _run_named_job_owner_fixture(ready_path: Path, job_name: str) -> None:
    """Windows integration fixture: die without closing a named Job normally."""
    artifacts = ready_path.parent
    job = _create_kill_on_close_job(job_name)
    parent = None
    try:
        parent, parent_identity, child_identity = _start_synthetic_job_tree(
            job, artifacts, "fixture"
        )
        write_json_atomic(
            ready_path,
            {
                "owner": _process_identity(os.getpid()),
                "sentinel_parent": parent_identity,
                "sentinel_child": child_identity,
                "job_active_processes": _job_active_processes(job),
            },
        )
        while True:
            time.sleep(1)
    finally:
        # The integration test terminates this owner, so this normally does not
        # execute.  It makes manual interruption safe.
        if parent is not None:
            parent.terminate_exact()
            parent.close()


def _run_outer_guard_subject_fixture(
    ready_path: Path, job_name: str, outer_identity_path: Path
) -> None:
    """Integration fixture proving pre-arm outer loss closes the subject Job."""
    outer_identity = json.loads(outer_identity_path.read_text(encoding="utf-8"))
    _start_outer_guard(outer_identity)
    job = _create_kill_on_close_job(job_name)
    parent = None
    try:
        parent, parent_identity, child_identity = _start_synthetic_job_tree(
            job, ready_path.parent, "outer-guard"
        )
        write_json_atomic(
            ready_path,
            {
                "outer": outer_identity,
                "subject": _process_identity(os.getpid()),
                "sentinel_parent": parent_identity,
                "sentinel_child": child_identity,
                "job_active_processes": _job_active_processes(job),
            },
        )
        while True:
            time.sleep(1)
    finally:
        if parent is not None:
            parent.terminate_exact()
            parent.close()


def _run_outer_guard_outer_fixture(
    ready_path: Path, job_name: str, package_root: Path
) -> None:
    """Parent fixture whose hard death must trigger the subject's guard."""
    outer_identity = _process_identity(os.getpid())
    if outer_identity is None:
        raise RuntimeError("outer guard fixture identity is unavailable")
    identity_path = ready_path.with_name("outer-identity.json")
    write_json_atomic(identity_path, outer_identity)
    code = (
        "import pathlib,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from xar_autoplayer.crash_probe import _run_outer_guard_subject_fixture;"
        "_run_outer_guard_subject_fixture(pathlib.Path(sys.argv[2]),"
        "sys.argv[3],pathlib.Path(sys.argv[4]))"
    )
    subject = subprocess.Popen(
        [
            sys.executable,
            "-c",
            code,
            str(package_root),
            str(ready_path),
            job_name,
            str(identity_path),
        ]
    )
    try:
        while True:
            if subject.poll() is not None:
                raise RuntimeError(
                    f"outer guard subject exited early: {subject.returncode}"
                )
            time.sleep(1)
    finally:
        if subject.poll() is None:
            subject.terminate()
            subject.wait(timeout=5)


def _validate_crash_success_payload(
    report: dict[str, object], run_dir: Path, *, require_postflight: bool = True
) -> None:
    recorded_run = _recorded_run_dir(report)
    if report.get("kind") != "crash_recovery_smoke":
        raise AgentError("crash report kind differs")
    if report.get("acceptance_claim") != "post_resume_supervisor_crash_recovery_only":
        raise AgentError("crash report acceptance claim differs")
    if report.get("valid_score_episode") is not False:
        raise AgentError("crash probe must never be a score episode")
    if report.get("replay_trust_model") != REPLAY_TRUST_MODEL:
        raise AgentError("crash replay trust model differs")
    crash = report.get("crash_attestation")
    if not isinstance(crash, dict) or crash.get("cleanup_proven") is not True:
        raise AgentError("crash cleanup proof is absent")
    probe_nonce = str(crash.get("probe_nonce", ""))
    if (
        int(crash.get("subject_exit_code", -1)) != CRASH_EXIT_CODE
        or crash.get("job_name") != _canonical_job_name(probe_nonce)
        or int(crash.get("job_active_processes_before", 0)) < 3
        or crash.get("named_job_destroyed") is not True
    ):
        raise AgentError("crash report does not prove named Job destruction")
    pins = crash.get("pinned_processes_signaled")
    if not isinstance(pins, dict) or set(pins) != {
        "supervisor",
        "ck3",
        "sentinel_parent",
        "sentinel_child",
    } or not all(value is True for value in pins.values()):
        raise AgentError("crash report pinned-process proof differs")
    exit_codes = crash.get("pinned_process_exit_codes")
    if (
        not isinstance(exit_codes, dict)
        or set(exit_codes) != set(pins)
        or int(exit_codes.get("supervisor", -1)) != CRASH_EXIT_CODE
        or any(int(value) == 259 for value in exit_codes.values())
    ):
        raise AgentError("crash report pinned-process exit codes differ")
    if (
        crash.get("watchdog_state_before") != "running"
        or crash.get("watchdog_state_after") != "absent"
        or int(crash.get("watchdog_exit_code", -1)) != 0
    ):
        raise AgentError("crash report watchdog did not become absent")
    controls = crash.get("control_files_absent")
    if (
        not isinstance(controls, dict)
        or set(controls) != CONTROL_FILE_LABELS
        or not all(value is True for value in controls.values())
    ):
        raise AgentError("crash report control-file proof differs")
    inventory = crash.get("final_ck3_inventory")
    if (
        not isinstance(inventory, dict)
        or inventory.get("tasklist_returncode") != 0
        or inventory.get("tasklist_pids") != []
        or inventory.get("wmi_pids") != []
        or inventory.get("processes") != []
        or not math.isfinite(float(inventory.get("continuous_empty_seconds", 0)))
        or float(inventory.get("continuous_empty_seconds", 0)) < 5
        or int(inventory.get("poll_count", 0)) < 2
    ):
        raise AgentError("crash report final CK3 inventory is not empty")

    artifacts = report.get("artifacts")
    required_artifacts = {
        "protected_before",
        "environment",
        "production_manifest",
        "owner",
        "handoff",
        "armed",
        "runtime_debug_prefix",
        "load_attestation",
        "visual_frame_1_screenshot",
        "visual_frame_1_ocr",
        "visual_frame_2_screenshot",
        "visual_frame_2_ocr",
        "control_before_record",
        "control_before_ready",
        "control_before_unsafe_marker",
        "watchdog_final",
    }
    artifacts_payload = report.get("artifacts")
    protected_postflight_present = require_postflight or (
        isinstance(artifacts_payload, dict)
        and "protected_after" in artifacts_payload
    ) or "protected_storage" in report
    if protected_postflight_present:
        required_artifacts.add("protected_after")
    if not isinstance(artifacts, dict) or set(artifacts) != required_artifacts:
        raise AgentError("crash report artifact manifest differs")
    verified = {
        label: _verify_artifact_entry(entry, run_dir, label)
        for label, entry in artifacts.items()
    }
    canonical_relative = {
        "protected_before": "protected-before.json.gz",
        "environment": "environment.json",
        "production_manifest": "production.manifest.json",
        "owner": f"artifacts/owner-{probe_nonce}.json",
        "handoff": f"artifacts/handoff-{probe_nonce}.json",
        "armed": f"artifacts/armed-{probe_nonce}.json",
        "runtime_debug_prefix": f"artifacts/runtime-debug-prefix-{probe_nonce}.log",
        "load_attestation": f"artifacts/load-attestation-{probe_nonce}.json",
        "visual_frame_1_screenshot": "artifacts/main-menu-frame-1.png",
        "visual_frame_1_ocr": "artifacts/main-menu-frame-1-ocr.json",
        "visual_frame_2_screenshot": "artifacts/main-menu.png",
        "visual_frame_2_ocr": "artifacts/main-menu-ocr.json",
        "control_before_record": f"artifacts/control-before-record-{probe_nonce}.json",
        "control_before_ready": f"artifacts/control-before-ready-{probe_nonce}.json",
        "control_before_unsafe_marker": (
            f"artifacts/control-before-unsafe_marker-{probe_nonce}.json"
        ),
        "watchdog_final": f"artifacts/watchdog-final-{probe_nonce}.json",
    }
    if protected_postflight_present:
        canonical_relative["protected_after"] = "protected-after.json.gz"
    if (
        any(artifacts[label]["path"] != relative for label, relative in canonical_relative.items())
        or len(set(verified.values())) != len(verified)
    ):
        raise AgentError("crash report artifact paths are noncanonical or aliased")
    if crash.get("handoff_sha256") != artifacts["handoff"]["sha256"]:
        raise AgentError("crash report handoff binding differs")
    if crash.get("armed_sha256") != artifacts["armed"]["sha256"]:
        raise AgentError("crash report armed binding differs")
    handoff = json.loads(verified["handoff"].read_text(encoding="utf-8"))
    armed = json.loads(verified["armed"].read_text(encoding="utf-8"))
    owner_payload = json.loads(verified["owner"].read_text(encoding="utf-8"))
    if not isinstance(handoff, dict) or not isinstance(armed, dict):
        raise AgentError("crash handoff or armed root differs")
    expected_armed_fields = {
        "format_version",
        "probe_nonce",
        "watchdog_nonce",
        "job_name",
        "job_active_processes",
        "process_resumed",
        "supervisor",
        "ck3",
        "sentinel_parent",
        "sentinel_child",
        "watchdog",
        "control",
        "visual_attestation",
        "load_attestation",
        "artifacts",
        "environment_sha256",
        "armed_at",
    }
    if set(armed) != expected_armed_fields or armed.get("format_version") != 1:
        raise AgentError("crash armed schema differs")
    for identity_label in (
        "supervisor",
        "ck3",
        "sentinel_parent",
        "sentinel_child",
        "watchdog",
    ):
        _validate_process_identity_payload(
            armed.get(identity_label), f"armed {identity_label}"
        )
    expected_handoff_fields = {
        "format_version",
        "probe_nonce",
        "run_id",
        "state_dir",
        "artifacts",
        "armed",
        "watchdog_final",
        "outer",
        "environment_sha256",
        "owner_sha256",
    }
    outer = handoff.get("outer")
    _validate_process_identity_payload(outer, "crash outer")
    identities = {
        "outer": outer,
        **{
            label: armed[label]
            for label in (
                "supervisor",
                "ck3",
                "sentinel_parent",
                "sentinel_child",
                "watchdog",
            )
        },
    }
    if (
        len({int(identity["pid"]) for identity in identities.values()})
        != len(identities)
        or any(
            str(identity["name"]).casefold()
            != Path(str(identity["executable"])).name.casefold()
            for identity in identities.values()
        )
        or str(armed["ck3"]["name"]).casefold() != "ck3.exe"
        or int(armed["ck3"]["parent_pid"])
        != int(armed["supervisor"]["pid"])
    ):
        raise AgentError("crash process identity chain differs")
    if (
        not isinstance(handoff, dict)
        or set(handoff) != expected_handoff_fields
        or handoff.get("format_version") != 1
        or handoff.get("probe_nonce") != probe_nonce
        or handoff.get("run_id") != report.get("run_id")
        or handoff.get("environment_sha256") != report.get("environment_sha256")
        or handoff.get("owner_sha256") != artifacts["owner"]["sha256"]
        or not isinstance(owner_payload, dict)
        or set(owner_payload) != {"pid", "thread_id", "purpose", "state_dir"}
        or owner_payload.get("purpose") != "crash-smoke"
        or int(owner_payload.get("pid", -1)) != int(outer.get("pid", -2))
        or type(owner_payload.get("thread_id")) is not int
        or owner_payload["thread_id"] <= 0
        or Path(str(owner_payload.get("state_dir", ""))).resolve()
        != Path(str(handoff.get("state_dir", ""))).resolve()
        or not isinstance(outer, dict)
        or int(outer.get("pid", -1))
        != int(armed.get("supervisor", {}).get("parent_pid", -2))
        or not outer.get("creation_date")
        or not outer.get("executable")
        or not _recorded_reference_matches(
            handoff.get("artifacts"), recorded_run, "artifacts"
        )
        or armed.get("probe_nonce") != probe_nonce
        or armed.get("job_name") != crash.get("job_name")
        or armed.get("environment_sha256") != report.get("environment_sha256")
        or armed.get("process_resumed") is not True
        or int(armed.get("supervisor", {}).get("pid", -1))
        != int(crash.get("subject_pid", -2))
        or not isinstance(armed.get("ck3"), dict)
        or int(armed.get("ck3", {}).get("pid", -1)) <= 0
        or not armed.get("ck3", {}).get("creation_date")
        or int(armed.get("job_active_processes", 0))
        != int(crash.get("job_active_processes_before", -1))
        or not _recorded_reference_matches(
            handoff.get("armed"), recorded_run, canonical_relative["armed"]
        )
        or not _recorded_reference_matches(
            handoff.get("watchdog_final"),
            recorded_run,
            canonical_relative["watchdog_final"],
        )
    ):
        raise AgentError("crash handoff or armed payload differs")
    expected_recorded_run = (
        Path(str(handoff["state_dir"])) / "runs" / str(handoff["run_id"])
    ).resolve()
    if expected_recorded_run != recorded_run:
        raise AgentError("crash handoff recorded run topology differs")
    if armed.get("artifacts") != {
        "runtime_debug_prefix": artifacts["runtime_debug_prefix"],
        "load_attestation": artifacts["load_attestation"],
        "visual_frame_1_screenshot": artifacts["visual_frame_1_screenshot"],
        "visual_frame_1_ocr": artifacts["visual_frame_1_ocr"],
        "visual_frame_2_screenshot": artifacts["visual_frame_2_screenshot"],
        "visual_frame_2_ocr": artifacts["visual_frame_2_ocr"],
    }:
        raise AgentError("crash armed artifact bindings differ")
    watchdog_identity = crash.get("watchdog_identity_before")
    if watchdog_identity != armed.get("watchdog"):
        raise AgentError("crash watchdog identity binding differs")
    pinned_identities = crash.get("pinned_process_identities")
    expected_identities = {
        label: armed.get(label)
        for label in ("supervisor", "ck3", "sentinel_parent", "sentinel_child")
    }
    if pinned_identities != expected_identities:
        raise AgentError("crash pinned-process identities differ")
    if (
        crash.get("watchdog_nonce") != armed.get("watchdog_nonce")
        or int(armed.get("sentinel_parent", {}).get("parent_pid", -1))
        != int(armed.get("supervisor", {}).get("pid", -2))
        or int(armed.get("sentinel_child", {}).get("parent_pid", -1))
        != int(armed.get("sentinel_parent", {}).get("pid", -2))
        or not _same_executable(
            armed.get("sentinel_parent", {}).get("executable", ""),
            armed.get("supervisor", {}).get("executable", ""),
        )
        or not _same_executable(
            armed.get("sentinel_child", {}).get("executable", ""),
            armed.get("supervisor", {}).get("executable", ""),
        )
    ):
        raise AgentError("crash armed sentinel relationship differs")
    watchdog_nonce = str(armed.get("watchdog_nonce", ""))
    state_dir = Path(str(handoff.get("state_dir", "")))
    control_root = state_dir / "control"
    expected_control_paths = {
        "record": control_root / "ck3.json",
        "ready": control_root / f"watchdog-{watchdog_nonce}.ready.json",
        "unsafe_marker": control_root / "unsafe-cleanup.json",
        "watchdog_error": control_root / "ck3.watchdog_error",
    }
    armed_control = armed.get("control")
    if (
        not state_dir.is_absolute()
        or not re.fullmatch(r"[0-9a-f]{32}", watchdog_nonce)
        or not isinstance(armed_control, dict)
        or set(armed_control)
        != {
            *CONTROL_FILE_LABELS,
            "record_sha256",
            "ready_sha256",
            "unsafe_marker_sha256",
        }
        or any(
            Path(str(armed_control.get(label, ""))).resolve()
            != expected.resolve()
            for label, expected in expected_control_paths.items()
        )
    ):
        raise AgentError("crash armed control-file contract differs")

    evidence_path = verified["watchdog_final"]
    if (
        not _recorded_reference_matches(
            crash.get("watchdog_final"),
            recorded_run,
            canonical_relative["watchdog_final"],
        )
        or artifacts["watchdog_final"]["sha256"]
        != crash.get("watchdog_final_sha256")
    ):
        raise AgentError("watchdog final evidence hash differs")
    final = json.loads(evidence_path.read_text(encoding="ascii"))
    measured_quiet = float(final.get("measured_stable_empty_seconds", 0))
    if (
        final.get("format_version") != 1
        or final.get("ok") is not True
        or final.get("nonce") != crash.get("watchdog_nonce")
        or final.get("stage") != "complete"
        or int(final.get("parent_pid", -1)) != int(crash.get("subject_pid", -2))
        or final.get("parent_creation_date")
        != armed.get("supervisor", {}).get("creation_date")
        or not _same_executable(
            final.get("parent_executable", ""),
            armed.get("supervisor", {}).get("executable", ""),
        )
        or int(final.get("watchdog_pid", -1))
        != int(armed.get("watchdog", {}).get("pid", -2))
        or final.get("watchdog_creation_date")
        != armed.get("watchdog", {}).get("creation_date")
        or final.get("control_files_removed") is not True
        or final.get("parent_termination_observed") is not True
        or not math.isfinite(measured_quiet)
        or measured_quiet < 5
        or int(final.get("empty_poll_count", 0)) < 2
        or not isinstance(final.get("authenticated_candidates"), list)
        or any(type(pid) is not int or pid <= 0 for pid in final["authenticated_candidates"])
        or final["authenticated_candidates"]
        not in ([], [int(armed.get("ck3", {}).get("pid", -1))])
    ):
        raise AgentError("watchdog final evidence payload differs")
    before_controls = crash.get("control_files_before")
    if not isinstance(before_controls, dict) or set(before_controls) != {
        "record",
        "ready",
        "unsafe_marker",
    }:
        raise AgentError("crash control-before artifact set differs")
    for label, entry in before_controls.items():
        if entry != artifacts[f"control_before_{label}"]:
            raise AgentError(f"crash control-before {label} binding differs")
        expected_hash = armed["control"][f"{label}_sha256"]
        if entry.get("sha256") != expected_hash:
            raise AgentError(f"crash control-before {label} hash differs")
    control_payloads = {
        label: json.loads(
            verified[f"control_before_{label}"].read_text(encoding="utf-8")
        )
        for label in ("record", "ready", "unsafe_marker")
    }
    record = control_payloads["record"]
    ready = control_payloads["ready"]
    marker = control_payloads["unsafe_marker"]
    if (
        not isinstance(record, dict)
        or set(record)
        != {
            "format_version",
            "nonce",
            "ck3_pid",
            "parent_pid",
            "executable",
            "creation_date",
        }
        or record.get("format_version") != 1
        or record.get("nonce") != watchdog_nonce
        or int(record.get("ck3_pid", -1)) != int(armed["ck3"].get("pid", -2))
        or int(record.get("parent_pid", -1))
        != int(armed["supervisor"].get("pid", -2))
        or not _same_executable(
            record.get("executable", ""), armed["ck3"].get("executable", "")
        )
        or record.get("creation_date") != armed["ck3"].get("creation_date")
        or not isinstance(ready, dict)
        or set(ready)
        != {
            "nonce",
            "parent_pid",
            "parent_executable",
            "parent_creation_date",
            "watchdog_pid",
        }
        or ready.get("nonce") != watchdog_nonce
        or int(ready.get("parent_pid", -1))
        != int(armed["supervisor"].get("pid", -2))
        or not _same_executable(
            ready.get("parent_executable", ""),
            armed["supervisor"].get("executable", ""),
        )
        or ready.get("parent_creation_date")
        != armed["supervisor"].get("creation_date")
        or int(ready.get("watchdog_pid", -1))
        != int(armed["watchdog"].get("pid", -2))
        or not isinstance(marker, dict)
        or set(marker) != {"nonce", "ck3_pid", "reason"}
        or marker.get("nonce") != watchdog_nonce
        or int(marker.get("ck3_pid", -1)) != int(armed["ck3"].get("pid", -2))
        or marker.get("reason")
        != "suspended launch active; removed only after authenticated tree shutdown"
    ):
        raise AgentError("crash archived control payload differs")

    archived_load = json.loads(
        verified["load_attestation"].read_text(encoding="utf-8")
    )
    expected_production_mount = str(
        (
            Path(str(handoff.get("state_dir", "")))
            / "profile"
            / "mod-content"
            / "xar-production"
        ).resolve()
    )
    if (
        archived_load != armed.get("load_attestation")
        or archived_load != report.get("load_attestation")
        or armed.get("visual_attestation") != report.get("visual_attestation")
        or archived_load.get("enabled_mods")
        != [{"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}]
        or archived_load.get("isolated_mod_mounts") != [expected_production_mount]
        or archived_load.get("unclassified_mounts") != []
        or archived_load.get("session_marker_count") != 1
        or archived_load.get("policy_boundary")
        != "not available to gameplay perception or strategy"
    ):
        raise AgentError("archived load attestation differs from armed payload")
    visual = report.get("visual_attestation")
    if (
        not isinstance(visual, dict)
        or visual.get("target") != "新游戏"
        or visual.get("target_normalized") != normalize_ocr_text("新游戏")
        or visual.get("stable_frames") != 2
    ):
        raise AgentError("visible main-menu artifact binding differs")
    stable_frames = visual.get("stable_frame_evidence")
    if not isinstance(stable_frames, list) or len(stable_frames) != 2:
        raise AgentError("visible main-menu stable-frame evidence differs")
    frame_times: list[datetime] = []
    frame_monotonic: list[float] = []
    capture_sequences: list[int] = []
    for index, frame in enumerate(stable_frames, start=1):
        screenshot_label = f"visual_frame_{index}_screenshot"
        ocr_label = f"visual_frame_{index}_ocr"
        if (
            not isinstance(frame, dict)
            or set(frame)
            != {
                "frame",
                "capture_sequence",
                "captured_at",
                "captured_monotonic",
                "window_rect",
                "screenshot",
                "screenshot_sha256",
                "ocr",
                "ocr_sha256",
                "exact_match_count",
            }
            or frame.get("frame") != index
            or type(frame.get("capture_sequence")) is not int
            or frame["capture_sequence"] <= 0
            or not isinstance(frame.get("captured_monotonic"), (int, float))
            or isinstance(frame.get("captured_monotonic"), bool)
            or not math.isfinite(float(frame["captured_monotonic"]))
            or float(frame["captured_monotonic"]) < 0
            or frame.get("exact_match_count") != 1
            or not isinstance(frame.get("window_rect"), list)
            or len(frame["window_rect"]) != 4
            or any(type(value) is not int for value in frame["window_rect"])
            or frame["window_rect"][2] - frame["window_rect"][0] != 2560
            or frame["window_rect"][3] - frame["window_rect"][1] != 1440
            or not _recorded_reference_matches(
                frame.get("screenshot"),
                recorded_run,
                canonical_relative[screenshot_label],
            )
            or frame.get("screenshot_sha256")
            != artifacts[screenshot_label]["sha256"]
            or not _recorded_reference_matches(
                frame.get("ocr"), recorded_run, canonical_relative[ocr_label]
            )
            or frame.get("ocr_sha256") != artifacts[ocr_label]["sha256"]
        ):
            raise AgentError("visible main-menu stable-frame binding differs")
        try:
            captured_at = datetime.fromisoformat(str(frame.get("captured_at", "")))
        except ValueError as error:
            raise AgentError("visible main-menu frame timestamp differs") from error
        if captured_at.tzinfo is None:
            raise AgentError("visible main-menu frame timestamp lacks timezone")
        frame_times.append(captured_at)
        frame_monotonic.append(float(frame["captured_monotonic"]))
        capture_sequences.append(int(frame["capture_sequence"]))
        from PIL import Image

        try:
            with Image.open(verified[screenshot_label]) as screenshot_image:
                if (
                    screenshot_image.format != "PNG"
                    or screenshot_image.size != (2560, 1440)
                    or screenshot_image.mode not in {"RGB", "RGBA"}
                ):
                    raise AgentError("visible main-menu screenshot format differs")
                screenshot_image.verify()
        except (OSError, ValueError) as error:
            raise AgentError("visible main-menu screenshot cannot be decoded") from error
        visual_ocr = json.loads(verified[ocr_label].read_text(encoding="utf-8"))
        if not isinstance(visual_ocr, list) or not visual_ocr:
            raise AgentError("visible main-menu OCR evidence differs")
        for item in visual_ocr:
            score = item.get("score") if isinstance(item, dict) else None
            center = item.get("center") if isinstance(item, dict) else None
            bbox = item.get("bbox") if isinstance(item, dict) else None
            if (
                not isinstance(item, dict)
                or set(item) != {"text", "score", "center", "bbox"}
                or not isinstance(item.get("text"), str)
                or not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not math.isfinite(float(score))
                or not 0 <= float(score) <= 1
                or not isinstance(center, list)
                or len(center) != 2
                or any(type(value) is not int for value in center)
                or not isinstance(bbox, list)
                or len(bbox) != 4
                or any(type(value) is not int for value in bbox)
                or not (0 <= bbox[0] < bbox[2] <= 2560)
                or not (0 <= bbox[1] < bbox[3] <= 1440)
                or not (bbox[0] <= center[0] <= bbox[2])
                or not (bbox[1] <= center[1] <= bbox[3])
            ):
                raise AgentError("visible main-menu OCR item schema differs")
        archived_match = unique_exact_ocr_match(visual_ocr, "新游戏")
        replayed_items = _replay_main_menu_ocr(
            verified[screenshot_label], artifacts[screenshot_label]["sha256"]
        )
        replayed_match = unique_exact_ocr_match(replayed_items, "新游戏")
        archived_center = archived_match.get("center") if archived_match else None
        replayed_center = replayed_match.get("center") if replayed_match else None
        archived_bbox = archived_match.get("bbox") if archived_match else None
        replayed_bbox = replayed_match.get("bbox") if replayed_match else None
        if (
            archived_match is None
            or replayed_match is None
            or not isinstance(archived_center, list)
            or not isinstance(replayed_center, list)
            or len(archived_center) != len(replayed_center)
            or any(
                abs(int(first) - int(second)) > 2
                for first, second in zip(archived_center, replayed_center)
            )
            or not isinstance(archived_bbox, list)
            or not isinstance(replayed_bbox, list)
            or len(archived_bbox) != len(replayed_bbox)
            or any(
                abs(int(first) - int(second)) > 2
                for first, second in zip(archived_bbox, replayed_bbox)
            )
        ):
            raise AgentError("visible main-menu OCR evidence differs")
    monotonic_delta = frame_monotonic[1] - frame_monotonic[0]
    if (
        capture_sequences[1] != capture_sequences[0] + 1
        or not 0 <= monotonic_delta <= 10
    ):
        raise AgentError("visible main-menu frames are not consecutive")
    second_frame = stable_frames[1]
    if (
        visual.get("screenshot") != second_frame.get("screenshot")
        or visual.get("screenshot_sha256")
        != second_frame.get("screenshot_sha256")
        or visual.get("ocr") != second_frame.get("ocr")
        or visual.get("ocr_sha256") != second_frame.get("ocr_sha256")
        or visual.get("window_rect") != second_frame.get("window_rect")
    ):
        raise AgentError("visible main-menu compatibility binding differs")
    debug = archived_load.get("debug_log", {})
    if (
        not _recorded_reference_matches(
            debug.get("archive_path"),
            recorded_run,
            canonical_relative["runtime_debug_prefix"],
        )
        or debug.get("archive_sha256")
        != artifacts["runtime_debug_prefix"]["sha256"]
    ):
        raise AgentError("archived runtime debug prefix binding differs")
    environment_payload = json.loads(
        verified["environment"].read_text(encoding="utf-8")
    )
    if (
        environment_payload.get("environment_sha256")
        != report.get("environment_sha256")
        or _contract_digest(environment_payload)
        != report.get("environment_sha256")
        or environment_payload.get("state_dir")
        != str(Path(str(handoff.get("state_dir", ""))).resolve())
        or environment_payload.get("profile_dir")
        != str(
            (Path(str(handoff.get("state_dir", ""))) / "profile").resolve()
        )
        or environment_payload.get("mod", {}).get("production_manifest_sha256")
        != artifacts["production_manifest"]["sha256"]
    ):
        raise AgentError("archived environment or production manifest differs")
    _validate_environment_archive_semantics(environment_payload)
    production_manifest = json.loads(
        verified["production_manifest"].read_text(encoding="utf-8")
    )
    _validate_release_manifest_archive(production_manifest, environment_payload)
    dlc = environment_payload.get("dlc")
    allowed_dlc_mounts = dlc.get("allowed_mount_roots") if isinstance(dlc, dict) else None
    if (
        not isinstance(dlc, dict)
        or not isinstance(allowed_dlc_mounts, list)
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(dlc.get("installed_descriptors_sha256", ""))
        )
        or any(
            not isinstance(path, str) or not Path(path).is_absolute()
            for path in allowed_dlc_mounts
        )
        or allowed_dlc_mounts != sorted(set(allowed_dlc_mounts))
        or snapshot_digest(allowed_dlc_mounts)
        != dlc.get("allowed_mount_roots_sha256")
        or len(allowed_dlc_mounts) != dlc.get("installed_descriptor_count")
    ):
        raise AgentError("archived DLC mount allowlist differs")
    archived_game_exe = Path(str(environment_payload["game"]["executable"]))
    if not _same_executable(
        armed.get("ck3", {}).get("executable", ""), archived_game_exe
    ):
        raise AgentError("armed CK3 executable differs from the environment")
    if not _same_executable(
        final.get("expected_ck3_executable", ""), archived_game_exe
    ):
        raise AgentError("watchdog final CK3 executable binding differs")
    reparsed = parse_runtime_attestation(
        verified["runtime_debug_prefix"].read_text(
            encoding="utf-8", errors="ignore"
        ),
        Path(str(handoff["state_dir"])) / "profile",
        Path(str(handoff["state_dir"]))
        / "profile"
        / "mod-content"
        / "xar-production",
        allowed_dlc_mounts=allowed_dlc_mounts,
    )
    if any(
        reparsed.get(key) != archived_load.get(key)
        for key in (
            "enabled_mods",
            "isolated_mod_mounts",
            "runtime_dlc_mounts",
            "unclassified_mounts",
            "session_marker_count",
        )
    ):
        raise AgentError("archived runtime single-mod attestation differs")

    if protected_postflight_present:
        protected = report.get("protected_storage")
        if (
            not isinstance(protected, dict)
            or protected.get("post_exit_matches_baseline") is not True
            or not math.isfinite(float(protected.get("continuous_quiet_seconds", 0)))
            or float(protected.get("continuous_quiet_seconds", 0)) < 5
            or protected.get("runtime_write_absence_proven") is not False
            or protected.get("before_snapshot_sha256")
            != artifacts["protected_before"]["sha256"]
            or protected.get("after_snapshot_sha256")
            != artifacts["protected_after"]["sha256"]
        ):
            raise AgentError("crash report protected-storage boundary differs")
        with gzip.open(
            verified["protected_before"], "rt", encoding="utf-8"
        ) as source:
            protected_before = json.load(source)
        with gzip.open(
            verified["protected_after"], "rt", encoding="utf-8"
        ) as source:
            protected_after = json.load(source)
        before_stores = protected_before.get("stores")
        after_stores = protected_after.get("stores")
        before_volatile = protected_before.get("allowed_volatile")
        after_volatile = protected_after.get("allowed_volatile")
        if (
            not isinstance(protected_before, dict)
            or set(protected_before) != {"digest", "stores", "allowed_volatile"}
            or not isinstance(protected_after, dict)
            or set(protected_after) != {"digest", "stores", "allowed_volatile"}
            or not isinstance(before_stores, dict)
            or set(before_stores) != {"real_profile", "steam_userdata", "workshop"}
            or any(not isinstance(value, dict) for value in before_stores.values())
            or after_stores != before_stores
            or not isinstance(before_volatile, dict)
            or not isinstance(after_volatile, dict)
            or before_volatile.get("policy")
            != "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected."
            or after_volatile.get("policy") != before_volatile.get("policy")
            or not isinstance(before_volatile.get("steam_remotecache"), dict)
            or not isinstance(after_volatile.get("steam_remotecache"), dict)
            or protected_before.get("digest") != protected.get("sha256")
            or protected_after.get("digest") != protected.get("sha256")
            or snapshot_digest(before_stores)
            != protected_before.get("digest")
            or snapshot_digest(after_stores)
            != protected_after.get("digest")
        ):
            raise AgentError("crash protected snapshot semantic digest differs")
        if require_postflight and report.get("production_tree_unchanged") is not True:
            raise AgentError("crash report production tree proof is absent")
    elif (
        "protected_storage" in report
        or "protected_after" in artifacts
        or report.get("production_tree_unchanged") is True
    ):
        raise AgentError("crash report has partial protected postflight evidence")


def _validate_red_cleanup_claim(
    report: dict[str, object], run_dir: Path
) -> None:
    """A RED report may claim cleanup, but never without the full crash proof."""
    _validate_crash_success_payload(report, run_dir, require_postflight=False)


def validate_crash_report(run_dir: Path) -> dict[str, object]:
    run_dir = run_dir.resolve()
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise AgentError("crash report root is not an object")
    if (
        report.get("format_version") != 1
        or report.get("kind") != "crash_recovery_smoke"
        or report.get("run_id") != run_dir.name
        or report.get("valid_score_episode") is not False
        or report.get("runtime_write_absence_proven") is not False
        or report.get("replay_trust_model") != REPLAY_TRUST_MODEL
        or type(report.get("ok")) is not bool
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(report.get("environment_sha256", ""))
        )
    ):
        raise AgentError("crash report base contract differs")
    _recorded_run_dir(report)
    chain = validate_event_chain(run_dir / "events.jsonl")
    validate_final_report_payload(report, chain)
    event_binding = report.get("event_chain")
    if event_binding != {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }:
        raise AgentError("crash report event-chain summary differs")
    event_rows = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    kinds = [row.get("kind") for row in event_rows]
    expected_order = [
        "smoke_started",
        "crash_subject_armed",
        "supervisor_crash_injected",
        "watchdog_cleanup_attested",
        "smoke_finished",
    ]
    crash_payload = report.get("crash_attestation")
    cleanup_claimed = (
        isinstance(crash_payload, dict)
        and crash_payload.get("cleanup_proven") is True
    )
    if report.get("ok") is True or cleanup_claimed:
        if kinds != expected_order:
            raise AgentError("attested crash event sequence differs")
    elif (
        not kinds
        or kinds[0] != "smoke_started"
        or kinds[-1] != "smoke_finished"
        or len(kinds) != len(set(kinds))
        or any(kind not in expected_order for kind in kinds)
        or [expected_order.index(kind) for kind in kinds]
        != sorted(expected_order.index(kind) for kind in kinds)
    ):
        raise AgentError("RED crash event sequence differs")
    expected_body = _report_body_sha256(report)
    if (
        report.get("report_body_sha256") != expected_body
        or chain.get("tail", {}).get("report_body_sha256") != expected_body
    ):
        raise AgentError("crash report body is not bound by its final event")
    if report.get("ok") is True:
        _validate_crash_success_payload(report, run_dir)
    else:
        artifacts = report.get("artifacts")
        if not isinstance(artifacts, dict):
            raise AgentError("RED crash report lacks its artifact manifest")
        verified_red: dict[str, Path] = {}
        for label in ("protected_before", "environment", "production_manifest"):
            verified_red[label] = _verify_artifact_entry(
                artifacts.get(label), run_dir, label
            )
        for label, entry in artifacts.items():
            verified_red[label] = _verify_artifact_entry(entry, run_dir, label)
        if (
            artifacts["protected_before"]["path"] != "protected-before.json.gz"
            or artifacts["environment"]["path"] != "environment.json"
            or artifacts["production_manifest"]["path"]
            != "production.manifest.json"
            or len(set(verified_red.values())) != len(verified_red)
        ):
            raise AgentError("RED crash artifact paths are noncanonical or aliased")
        crash = report.get("crash_attestation", {})
        cleanup = isinstance(crash, dict) and crash.get("cleanup_proven") is True
        if cleanup:
            _validate_red_cleanup_claim(report, run_dir)
        if not cleanup and (
            report.get("unsafe_cleanup") is not True
            or "protected_storage" in report
            or report.get("production_tree_unchanged") is True
        ):
            raise AgentError("RED crash report performed postflight without cleanup proof")
    return report


def _archive_load_attestation(
    spec: EnvironmentSpec,
    load_evidence: dict[str, object],
    artifacts: Path,
    probe_nonce: str,
) -> tuple[dict[str, object], dict[str, object]]:
    debug = load_evidence.get("debug_log")
    if not isinstance(debug, dict):
        raise AgentError("runtime load attestation lacks debug prefix metadata")
    source = Path(str(debug.get("path", ""))).resolve()
    expected_source = (spec.profile_dir / "logs" / "debug.log").resolve()
    if source != expected_source:
        raise AgentError("runtime load attestation debug source differs")
    prefix_size = int(debug.get("captured_prefix_size", -1))
    raw = source.read_bytes()
    if prefix_size < 1 or len(raw) < prefix_size:
        raise AgentError("runtime debug prefix size is unavailable")
    prefix = raw[:prefix_size]
    expected_hash = str(debug.get("captured_prefix_sha256", ""))
    if hashlib.sha256(prefix).hexdigest() != expected_hash:
        raise AgentError("runtime debug prefix changed before archival")
    reparsed = parse_runtime_attestation(
        prefix.decode("utf-8", errors="ignore"),
        spec.profile_dir,
        spec.production_dir,
        spec.game_dir,
    )
    for key in (
        "enabled_mods",
        "isolated_mod_mounts",
        "runtime_dlc_mounts",
        "unclassified_mounts",
        "session_marker_count",
    ):
        if reparsed.get(key) != load_evidence.get(key):
            raise AgentError(f"archived runtime attestation differs for {key}")
    prefix_path = artifacts / f"runtime-debug-prefix-{probe_nonce}.log"
    write_bytes_atomic(prefix_path, prefix)
    archived = json.loads(json.dumps(load_evidence, ensure_ascii=False))
    archived_debug = dict(archived["debug_log"])
    archived_debug["archive_path"] = str(prefix_path.resolve())
    archived_debug["archive_sha256"] = sha256_file(prefix_path)
    archived["debug_log"] = archived_debug
    load_path = artifacts / f"load-attestation-{probe_nonce}.json"
    write_json_atomic(load_path, archived)
    return archived, {
        "runtime_debug_prefix": _artifact_entry(prefix_path, artifacts.parent),
        "load_attestation": _artifact_entry(load_path, artifacts.parent),
    }


def run_crash_subject(
    spec: EnvironmentSpec,
    *,
    probe_nonce: str,
    handoff_path: Path,
    handoff_sha256: str,
    armed_path: Path,
    watchdog_final: Path,
    artifacts: Path,
    timeout_seconds: float,
    outer_identity: dict[str, object],
) -> int:
    """Internal sacrificial entry point.  The outer verifier owns all locks."""
    handoff = _validate_subject_invocation(
        spec,
        probe_nonce=probe_nonce,
        handoff_path=handoff_path,
        handoff_sha256=handoff_sha256,
        armed_path=armed_path,
        watchdog_final=watchdog_final,
        artifacts=artifacts,
        outer_identity=outer_identity,
    )
    _start_outer_guard(outer_identity)
    handle = None
    sentinel_parent = None
    try:
        manifest = verify_profile(spec)
        if manifest["environment_sha256"] != handoff["environment_sha256"]:
            raise AgentError("crash subject prepared environment differs from handoff")
        job_name = _canonical_job_name(probe_nonce)
        handle = launch(
            spec,
            watchdog_final_evidence=watchdog_final,
            job_name=job_name,
        )
        visual = wait_for_main_menu(handle, artifacts, timeout_seconds)
        load_evidence = wait_for_runtime_attestation(spec, handle)
        load_evidence, load_artifacts = _archive_load_attestation(
            spec, load_evidence, artifacts, probe_nonce
        )
        stable_frames = visual.get("stable_frame_evidence")
        if not isinstance(stable_frames, list) or len(stable_frames) != 2:
            raise AgentError("visible main-menu stable evidence differs before arming")
        for index, frame in enumerate(stable_frames, start=1):
            if not isinstance(frame, dict) or frame.get("frame") != index:
                raise AgentError("visible main-menu frame order differs before arming")
            screenshot = Path(str(frame.get("screenshot", ""))).resolve()
            ocr = Path(str(frame.get("ocr", ""))).resolve()
            if (
                not is_relative_to(screenshot, artifacts.resolve())
                or not is_relative_to(ocr, artifacts.resolve())
                or not screenshot.is_file()
                or not ocr.is_file()
                or sha256_file(screenshot) != frame.get("screenshot_sha256")
                or sha256_file(ocr) != frame.get("ocr_sha256")
                or unique_exact_ocr_match(
                    json.loads(ocr.read_text(encoding="utf-8")), "新游戏"
                )
                is None
            ):
                raise AgentError("visible main-menu artifacts differ before arming")
            load_artifacts[f"visual_frame_{index}_screenshot"] = _artifact_entry(
                screenshot, artifacts.parent
            )
            load_artifacts[f"visual_frame_{index}_ocr"] = _artifact_entry(
                ocr, artifacts.parent
            )

        parent_identity = _process_identity(os.getpid())
        if parent_identity is None:
            raise AgentError("crash subject identity disappeared")
        (
            sentinel_parent,
            sentinel_parent_identity,
            sentinel_child_identity,
        ) = _start_synthetic_job_tree(handle.job_handle, artifacts, probe_nonce)
        actual_python = str(parent_identity["executable"])
        if (
            int(sentinel_parent_identity.get("parent_pid", -1)) != os.getpid()
            or int(sentinel_child_identity.get("parent_pid", -1))
            != int(sentinel_parent_identity["pid"])
            or not _same_executable(
                sentinel_parent_identity.get("executable", ""), actual_python
            )
            or not _same_executable(
                sentinel_child_identity.get("executable", ""), actual_python
            )
        ):
            raise AgentError("synthetic Job parent/child identity differs")
        active = _job_active_processes(handle.job_handle)
        if active is None or active < 3:
            raise AgentError(f"crash Job has only {active} active processes")
        watchdog_identity = _process_identity(handle.watchdog_pid)
        watchdog_state = _authenticated_watchdog_state(
            handle.watchdog_pid,
            handle.watchdog_creation_date,
            os.getpid(),
            handle.nonce,
        )
        if (
            watchdog_identity is None
            or watchdog_state != "running"
        ):
            raise AgentError("crash cleanup watchdog is not authenticated and running")
        record_sha = sha256_file(handle.record_file)
        marker_sha = sha256_file(handle.unsafe_marker)
        armed = {
            "format_version": 1,
            "probe_nonce": probe_nonce,
            "watchdog_nonce": handle.nonce,
            "job_name": job_name,
            "job_active_processes": active,
            "process_resumed": handle.process.resumed,
            "supervisor": parent_identity,
            "ck3": {
                **(_process_identity(handle.process.pid) or {}),
                "executable": str(handle.process.image_path()),
            },
            "sentinel_parent": {
                **sentinel_parent_identity,
            },
            "sentinel_child": sentinel_child_identity,
            "watchdog": watchdog_identity,
            "control": {
                "record": str(handle.record_file),
                "ready": str(handle.ready_file),
                "unsafe_marker": str(handle.unsafe_marker),
                "watchdog_error": str(handle.pid_file.with_suffix(".watchdog_error")),
                "record_sha256": record_sha,
                "unsafe_marker_sha256": marker_sha,
                "ready_sha256": sha256_file(handle.ready_file),
            },
            "visual_attestation": visual,
            "load_attestation": load_evidence,
            "artifacts": load_artifacts,
            "environment_sha256": manifest["environment_sha256"],
            "armed_at": utc_now(),
        }
        write_json_atomic(armed_path, armed)

        while True:
            if handle.process.poll() is not None:
                raise AgentError("CK3 exited before crash injection")
            if sentinel_parent.poll() is not None:
                raise AgentError("synthetic Job parent exited before crash injection")
            time.sleep(0.25)
    except Exception as error:
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "subject-error.txt").write_text(
            f"{type(error).__name__}: {error}\n", encoding="utf-8"
        )
        return 1
    finally:
        # A real injected TerminateProcess never executes this block.  It exists
        # only for pre-arm/natural failures, where the subject is still alive.
        if handle is not None:
            try:
                stop_tracked(handle, require_running=False)
            except Exception as cleanup_error:
                artifacts.mkdir(parents=True, exist_ok=True)
                (artifacts / "subject-cleanup-error.txt").write_text(
                    f"{type(cleanup_error).__name__}: {cleanup_error}\n",
                    encoding="utf-8",
                )
        if sentinel_parent is not None:
            sentinel_parent.close()


def crash_smoke(spec: EnvironmentSpec, timeout_seconds: float = 180) -> dict[str, object]:
    ensure_state_path_safe(spec.state_dir)
    with exclusive_state_lock(spec.state_dir, "crash-smoke"):
        with exclusive_launch_lock(spec.game_exe):
            return _crash_smoke_locked(spec, timeout_seconds)


def _crash_smoke_locked(
    spec: EnvironmentSpec, timeout_seconds: float
) -> dict[str, object]:
    manifest = verify_profile(spec)
    doctor(spec, require_prepared=True)
    _require_committed_environment(manifest)
    if ck3_process_inventory()["processes"]:
        raise AgentError("refusing crash probe while CK3 is already running")

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-crash-"
        + uuid.uuid4().hex[:8]
    )
    probe_nonce = uuid.uuid4().hex
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    run_dir.mkdir(parents=True, exist_ok=False)
    artifacts.mkdir()
    handoff_path = artifacts / f"handoff-{probe_nonce}.json"
    armed_path = artifacts / f"armed-{probe_nonce}.json"
    watchdog_final = artifacts / f"watchdog-final-{probe_nonce}.json"

    baseline = protected_snapshot()
    before_path = run_dir / "protected-before.json.gz"
    write_gzip_json_atomic(before_path, baseline)
    environment_copy = run_dir / "environment.json"
    production_copy = run_dir / "production.manifest.json"
    shutil.copy2(spec.manifest_path, environment_copy)
    shutil.copy2(
        Path(str(manifest["mod"]["production_manifest"])),
        production_copy,
    )
    append_event(
        events,
        {
            "kind": "smoke_started",
            "probe": "post_resume_supervisor_crash",
            "environment_sha256": manifest["environment_sha256"],
            "protected_storage_sha256": baseline["digest"],
        },
    )
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_id,
        "kind": "crash_recovery_smoke",
        "acceptance_claim": "post_resume_supervisor_crash_recovery_only",
        "valid_score_episode": False,
        "runtime_write_absence_proven": False,
        "replay_trust_model": dict(REPLAY_TRUST_MODEL),
        "started_at": utc_now(),
        "environment_sha256": manifest["environment_sha256"],
        "run_dir": str(run_dir),
        "artifacts": {
            "protected_before": _artifact_entry(before_path, run_dir),
            "environment": _artifact_entry(environment_copy, run_dir),
            "production_manifest": _artifact_entry(production_copy, run_dir),
        },
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(run_dir / "report.json", report)

    agent_entry = REPO_ROOT / "ck3_autonomous_player" / "agent.py"
    stdout_path = artifacts / "subject-stdout.log"
    stderr_path = artifacts / "subject-stderr.log"
    subject: subprocess.Popen[object] | None = None
    pins: list[object] = []
    primary_error: Exception | None = None
    cleanup_proven = False
    armed: dict[str, object] | None = None
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            outer_identity = _process_identity(os.getpid())
            if outer_identity is None:
                raise AgentError(
                    "outer crash verifier identity could not be authenticated"
                )
            owner_path = spec.state_dir / "control" / "owner.json"
            if not owner_path.is_file():
                raise AgentError("outer crash verifier state-lock owner is missing")
            owner_copy = artifacts / f"owner-{probe_nonce}.json"
            write_bytes_atomic(owner_copy, owner_path.read_bytes())
            report["artifacts"]["owner"] = _artifact_entry(owner_copy, run_dir)
            handoff = {
                "format_version": 1,
                "probe_nonce": probe_nonce,
                "run_id": run_id,
                "state_dir": str(spec.state_dir.resolve()),
                "artifacts": str(artifacts.resolve()),
                "armed": str(armed_path.resolve()),
                "watchdog_final": str(watchdog_final.resolve()),
                "outer": outer_identity,
                "environment_sha256": manifest["environment_sha256"],
                "owner_sha256": sha256_file(owner_path),
            }
            write_json_atomic(handoff_path, handoff)
            handoff_hash = sha256_file(handoff_path)
            report["artifacts"]["handoff"] = _artifact_entry(handoff_path, run_dir)
            command = [
                sys.executable,
                str(agent_entry),
                "--state-dir",
                str(spec.state_dir),
                "--game-dir",
                str(spec.game_dir),
                "_crash-subject",
                "--probe-nonce",
                probe_nonce,
                "--handoff",
                str(handoff_path),
                "--handoff-sha256",
                handoff_hash,
                "--armed",
                str(armed_path),
                "--watchdog-final",
                str(watchdog_final),
                "--artifacts",
                str(artifacts),
                "--timeout",
                str(timeout_seconds),
                "--outer-pid",
                str(outer_identity["pid"]),
                "--outer-executable",
                str(outer_identity["executable"]),
                "--outer-creation-date",
                str(outer_identity["creation_date"]),
            ]
            subject = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            armed = _wait_json(armed_path, subject, timeout_seconds + 45)
            expected_job_name = _canonical_job_name(probe_nonce)
            if int(armed["supervisor"]["pid"]) != subject.pid:
                raise AgentError("armed supervisor PID differs from spawned subject")
            if int(armed["supervisor"].get("parent_pid", -1)) != os.getpid():
                raise AgentError("armed supervisor is not a direct child of outer")
            if armed.get("probe_nonce") != probe_nonce:
                raise AgentError("armed crash probe nonce differs")
            if armed.get("job_name") != expected_job_name:
                raise AgentError("armed crash Job name differs from its nonce")
            if armed.get("environment_sha256") != manifest["environment_sha256"]:
                raise AgentError("armed environment fingerprint differs")
            if armed.get("process_resumed") is not True:
                raise AgentError("crash subject was not armed after CK3 resume")
            if int(armed.get("job_active_processes", 0)) < 3:
                raise AgentError("crash subject did not prove a three-member Job tree")
            load = armed.get("load_attestation", {})
            if load.get("enabled_mods") != [
                {"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}
            ]:
                raise AgentError("crash subject runtime enabled-mod inventory differs")
            if len(load.get("isolated_mod_mounts", [])) != 1 or load.get(
                "unclassified_mounts"
            ):
                raise AgentError("crash subject runtime mount attestation differs")
            if armed.get("visual_attestation", {}).get("stable_frames") != 2:
                raise AgentError("crash subject lacks stable visible main-menu evidence")
            sentinel_parent = armed.get("sentinel_parent", {})
            sentinel_child = armed.get("sentinel_child", {})
            if (
                int(sentinel_parent.get("parent_pid", -1)) != subject.pid
                or int(sentinel_child.get("parent_pid", -1))
                != int(sentinel_parent.get("pid", -2))
                or not _same_executable(
                    sentinel_parent.get("executable", ""),
                    armed["supervisor"].get("executable", ""),
                )
                or not _same_executable(
                    sentinel_child.get("executable", ""),
                    armed["supervisor"].get("executable", ""),
                )
            ):
                raise AgentError("armed synthetic parent/child identity differs")
            watchdog_nonce = str(armed.get("watchdog_nonce", ""))
            if not re.fullmatch(r"[0-9a-f]{32}", watchdog_nonce):
                raise AgentError("armed watchdog nonce differs")
            control_root = (spec.state_dir / "control").resolve()
            expected_control = {
                "record": control_root / "ck3.json",
                "ready": control_root / f"watchdog-{watchdog_nonce}.ready.json",
                "unsafe_marker": control_root / "unsafe-cleanup.json",
                "watchdog_error": control_root / "ck3.watchdog_error",
            }
            control = armed.get("control")
            if not isinstance(control, dict) or set(control) != {
                *CONTROL_FILE_LABELS,
                "record_sha256",
                "ready_sha256",
                "unsafe_marker_sha256",
            }:
                raise AgentError("armed control-file fields differ")
            for label, expected_path in expected_control.items():
                if Path(str(control[label])).resolve() != expected_path:
                    raise AgentError(f"armed {label} control path differs")
            for label, hash_label in (
                ("record", "record_sha256"),
                ("ready", "ready_sha256"),
                ("unsafe_marker", "unsafe_marker_sha256"),
            ):
                path = Path(str(armed["control"][label]))
                expected_hash = str(armed["control"][hash_label])
                if not path.is_file() or sha256_file(path) != expected_hash:
                    raise AgentError(f"armed {label} control evidence differs")
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload.get("nonce") != armed["watchdog_nonce"]:
                    raise AgentError(f"armed {label} nonce differs")
            watchdog_error = Path(str(armed["control"]["watchdog_error"]))
            if watchdog_error.exists():
                raise AgentError("watchdog error exists before crash injection")

            report["artifacts"]["armed"] = _artifact_entry(armed_path, run_dir)
            subject_artifacts = armed.get("artifacts")
            if not isinstance(subject_artifacts, dict) or set(subject_artifacts) != {
                "runtime_debug_prefix",
                "load_attestation",
                "visual_frame_1_screenshot",
                "visual_frame_1_ocr",
                "visual_frame_2_screenshot",
                "visual_frame_2_ocr",
            }:
                raise AgentError("armed subject artifact set differs")
            for label, entry in subject_artifacts.items():
                _verify_artifact_entry(entry, run_dir, label)
                report["artifacts"][label] = entry
            control_before: dict[str, dict[str, str]] = {}
            for label in ("record", "ready", "unsafe_marker"):
                source = Path(str(control[label]))
                copy = artifacts / f"control-before-{label}-{probe_nonce}.json"
                write_bytes_atomic(copy, source.read_bytes())
                if sha256_file(copy) != control[f"{label}_sha256"]:
                    raise AgentError(f"archived {label} control hash differs")
                entry = _artifact_entry(copy, run_dir)
                control_before[label] = entry
                report["artifacts"][f"control_before_{label}"] = entry

            supervisor_pin = _pin_process(armed["supervisor"], allow_terminate=True)
            ck3_pin = _pin_process(armed["ck3"])
            sentinel_parent_pin = _pin_process(armed["sentinel_parent"])
            sentinel_child_pin = _pin_process(armed["sentinel_child"])
            watchdog_state_before = _authenticated_watchdog_state(
                int(armed["watchdog"]["pid"]),
                str(armed["watchdog"]["creation_date"]),
                subject.pid,
                watchdog_nonce,
            )
            if watchdog_state_before != "running":
                raise AgentError(
                    f"watchdog state before crash is {watchdog_state_before}"
                )
            watchdog_pin = _pin_process(armed["watchdog"])
            pins.extend(
                [
                    supervisor_pin,
                    ck3_pin,
                    sentinel_parent_pin,
                    sentinel_child_pin,
                    watchdog_pin,
                ]
            )
            append_event(
                events,
                {
                    "kind": "crash_subject_armed",
                    "subject_pid": subject.pid,
                    "ck3_pid": armed["ck3"]["pid"],
                    "job_active_processes": armed["job_active_processes"],
                    "job_name": expected_job_name,
                    "handoff_sha256": handoff_hash,
                    "armed_sha256": sha256_file(armed_path),
                },
            )

            import win32api

            win32api.TerminateProcess(supervisor_pin, CRASH_EXIT_CODE)
            append_event(events, {"kind": "supervisor_crash_injected"})
            pinned_exit_codes = {
                "supervisor": _wait_pinned_exit(supervisor_pin, "crash subject"),
                "ck3": _wait_pinned_exit(ck3_pin, "CK3"),
                "sentinel_parent": _wait_pinned_exit(
                    sentinel_parent_pin, "synthetic Job parent"
                ),
                "sentinel_child": _wait_pinned_exit(
                    sentinel_child_pin, "synthetic Job child"
                ),
            }
            subject.wait(timeout=5)
            if subject.returncode != CRASH_EXIT_CODE:
                raise AgentError(
                    "crash subject exit code is "
                    f"{subject.returncode}, expected {CRASH_EXIT_CODE}"
                )
            _wait_named_job_absent(expected_job_name)

            watchdog_exit_code = _wait_pinned_exit(
                watchdog_pin, "crash cleanup watchdog", 40
            )
            if watchdog_exit_code != 0:
                raise AgentError(
                    f"crash cleanup watchdog exited {watchdog_exit_code}, expected 0"
                )

            watchdog_evidence = _wait_json(
                watchdog_final,
                subject,
                30,
                require_process_running=False,
            )
            measured_quiet = float(
                watchdog_evidence.get("measured_stable_empty_seconds", 0)
            )
            if (
                watchdog_evidence.get("ok") is not True
                or watchdog_evidence.get("nonce") != armed["watchdog_nonce"]
                or watchdog_evidence.get("stage") != "complete"
                or int(watchdog_evidence.get("parent_pid", -1)) != subject.pid
                or not _same_executable(
                    watchdog_evidence.get("parent_executable", ""),
                    armed["supervisor"].get("executable", ""),
                )
                or watchdog_evidence.get("parent_creation_date")
                != armed["supervisor"].get("creation_date")
                or int(watchdog_evidence.get("watchdog_pid", -1))
                != int(armed["watchdog"]["pid"])
                or watchdog_evidence.get("watchdog_creation_date")
                != armed["watchdog"].get("creation_date")
                or not _same_executable(
                    watchdog_evidence.get("expected_ck3_executable", ""),
                    spec.game_exe,
                )
                or watchdog_evidence.get("control_files_removed") is not True
                or watchdog_evidence.get("parent_termination_observed") is not True
                or not math.isfinite(measured_quiet)
                or measured_quiet < 5
                or int(watchdog_evidence.get("empty_poll_count", 0)) < 2
            ):
                raise AgentError(
                    f"watchdog final evidence differs: {watchdog_evidence!r}"
                )
            watchdog_state = _authenticated_watchdog_state(
                int(armed["watchdog"]["pid"]),
                str(armed["watchdog"]["creation_date"]),
                subject.pid,
                str(armed["watchdog_nonce"]),
            )
            if watchdog_state != "absent":
                raise AgentError(f"watchdog state after crash is {watchdog_state}")
            controls = {
                label: not Path(str(path)).exists()
                for label, path in armed["control"].items()
                if label in CONTROL_FILE_LABELS
            }
            if set(controls) != CONTROL_FILE_LABELS or not all(
                value is True for value in controls.values()
            ):
                raise AgentError(f"crash control files remain: {controls!r}")
            final_inventory = _wait_global_ck3_quiet()
            report["artifacts"]["watchdog_final"] = _artifact_entry(
                watchdog_final, run_dir
            )
            report["crash_attestation"] = {
                "probe_nonce": probe_nonce,
                "subject_pid": subject.pid,
                "subject_exit_code": subject.returncode,
                "handoff_sha256": handoff_hash,
                "armed_sha256": sha256_file(armed_path),
                "job_name": expected_job_name,
                "job_active_processes_before": armed["job_active_processes"],
                "named_job_destroyed": True,
                "pinned_processes_signaled": {
                    "supervisor": True,
                    "ck3": True,
                    "sentinel_parent": True,
                    "sentinel_child": True,
                },
                "pinned_process_identities": {
                    "supervisor": armed["supervisor"],
                    "ck3": armed["ck3"],
                    "sentinel_parent": armed["sentinel_parent"],
                    "sentinel_child": armed["sentinel_child"],
                },
                "pinned_process_exit_codes": pinned_exit_codes,
                "watchdog_identity_before": armed["watchdog"],
                "watchdog_state_before": watchdog_state_before,
                "watchdog_exit_code": watchdog_exit_code,
                "watchdog_final": str(watchdog_final),
                "watchdog_final_sha256": sha256_file(watchdog_final),
                "watchdog_nonce": armed["watchdog_nonce"],
                "watchdog_state_after": watchdog_state,
                "control_files_before": control_before,
                "control_files_absent": controls,
                "final_ck3_inventory": final_inventory,
                "cleanup_proven": False,
            }
            report["visual_attestation"] = armed["visual_attestation"]
            report["load_attestation"] = armed["load_attestation"]
            append_event(events, {"kind": "watchdog_cleanup_attested"})
            report["crash_attestation"]["cleanup_proven"] = True
            cleanup_proven = True
    except Exception as error:
        primary_error = error
    finally:
        import win32api

        for pinned in reversed(pins):
            try:
                win32api.CloseHandle(pinned)
            except Exception:
                pass
        if subject is not None and subject.poll() is None:
            try:
                subject.terminate()
                subject.wait(timeout=10)
            except Exception as cleanup_error:
                report["subject_cleanup_error"] = str(cleanup_error)
        if primary_error is not None and subject is not None:
            report["subject_failure"] = _read_subject_failure(run_dir)

    if cleanup_proven:
        try:
            after = verify_protected_unchanged(baseline)
            after_path = run_dir / "protected-after.json.gz"
            write_gzip_json_atomic(after_path, after)
            report["artifacts"]["protected_after"] = _artifact_entry(
                after_path, run_dir
            )
            report["protected_storage"] = {
                "post_exit_matches_baseline": True,
                "continuous_quiet_seconds": 5,
                "runtime_write_absence_proven": False,
                "sha256": after["digest"],
                "before_snapshot": str(before_path),
                "after_snapshot": str(after_path),
                "before_snapshot_sha256": sha256_file(before_path),
                "after_snapshot_sha256": sha256_file(after_path),
            }
            verify_profile(spec)
            current_tree = snapshot_digest(tree_snapshot(spec.production_dir))
            if current_tree != manifest["mod"]["production_tree_sha256"]:
                raise AgentError("production projection changed during crash probe")
            report["production_tree_unchanged"] = True
        except Exception as postflight_error:
            if primary_error is None:
                primary_error = postflight_error
            else:
                report["postflight_error"] = str(postflight_error)
    else:
        report["unsafe_cleanup"] = True
        if primary_error is None:
            primary_error = AgentError(
                "crash cleanup is not proven; protected postflight withheld"
            )

    report["finished_at"] = utc_now()
    if primary_error is None:
        try:
            _validate_crash_success_payload(report, run_dir)
        except Exception as validation_error:
            primary_error = validation_error
    candidate_ok = primary_error is None
    if primary_error is not None:
        report["error"] = str(primary_error)
    report_body_sha256 = _report_body_sha256(report)
    report["report_body_sha256"] = report_body_sha256
    final_event = append_event(
        events,
        {
            "kind": "smoke_finished",
            "ok": candidate_ok,
            "report_body_sha256": report_body_sha256,
        },
    )
    report["final_event_sha256"] = final_event
    report["finalized"] = True
    report["ok"] = candidate_ok
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    validate_final_report_payload(report, chain)
    write_json_atomic(run_dir / "report.json", report)
    if primary_error is not None:
        raise AgentError(
            f"crash smoke failed; evidence retained at {run_dir}: {primary_error}"
        ) from primary_error
    return validate_crash_report(run_dir)
