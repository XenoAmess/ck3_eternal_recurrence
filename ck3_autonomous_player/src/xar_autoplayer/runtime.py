"""Tracked non-debug CK3 launch and visible main-menu attestation."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import gzip
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import uuid
from pathlib import Path

from .environment import (
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    VISIBLE_UI_BASELINE_GAME_VERSION,
    _contract_digest,
    _is_access_denied,
    _toolhelp_process_identity,
    EnvironmentSpec,
    ck3_process_inventory,
    ck3_processes,
    doctor,
    ensure_state_path_safe,
    is_relative_to,
    mod_source_fingerprint,
    same_process_creation_time,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
    verify_profile,
    write_json_atomic,
    write_text_atomic,
)
from .errors import AgentError, UnsafeCleanupError
from .integrity import protected_snapshot, verify_protected_unchanged
from .locking import exclusive_launch_lock, exclusive_state_lock
from .rules import MOD_RULES


MAIN_MENU_REGION = (0.18, 0.28, 0.30, 0.50)
EXPECTED_RESOLUTION = (2560, 1440)
PROCESS_WATCHDOG = Path(__file__).with_name("process_watchdog.py")
NORMAL_REPORT_BINDING_EXCLUSIONS = frozenset(
    {
        "finalized",
        "ok",
        "final_event_sha256",
        "event_chain",
        "report_body_sha256",
    }
)
NORMAL_GREEN_EVENT_ORDER = (
    "smoke_started",
    "ck3_launched",
    "visible_main_menu_attested",
    "single_mod_runtime_attested",
    "tracked_process_stopped",
    "smoke_finished",
)
NORMAL_REPLAY_TRUST_MODEL = {
    "integrity": "unkeyed_sha256",
    "claim": "archive_schema_and_internal_consistency_only",
    "historical_execution_authenticity_proven": False,
}

NATIVE_BRIDGE_DISABLED = "disabled"
NATIVE_BRIDGE_LAUNCH_MODES = frozenset({"native-headless", "hybrid-fallback"})
DEFAULT_NATIVE_BRIDGE_PIPE = r"\\.\pipe\xar_ck3_bridge_mcp"
NATIVE_BRIDGE_MODE_ENV = "XAR_CK3_BRIDGE_MODE"
NATIVE_BRIDGE_PIPE_ENV = "XAR_CK3_BRIDGE_PIPE"
NATIVE_BRIDGE_DLL_ENV = "XAR_CK3_BRIDGE_DLL"
NATIVE_BRIDGE_INJECTOR_ENV = "XAR_CK3_BRIDGE_INJECTOR"
NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS = 30.0
_FALLBACK_WATCHDOG_COMMAND_LINES: dict[int, str] = {}
_FALLBACK_WATCHDOG_PROCESSES: dict[int, subprocess.Popen[bytes]] = {}


@dataclass(frozen=True)
class NativeBridgeLaunchConfig:
    """Explicit opt-in configuration for pre-resume native DLL injection."""

    mode: str
    pipe_name: str
    dll_path: Path
    injector_path: Path


@dataclass
class SessionHandle:
    process: object
    pid_file: Path
    watchdog_pid: int
    command: list[str]
    log_epoch_ns: int
    cleared_logs: list[str]
    nonce: str
    record_file: Path
    ready_file: Path
    unsafe_marker: Path
    ck3_creation_date: str
    watchdog_creation_date: str
    job_handle: object | None
    pre_resume_inventory: dict[str, object] | None = None


class _SuspendedWindowsProcess:
    """Minimal Popen-like wrapper retaining the exact Windows process handle."""

    def __init__(
        self,
        process_handle: object,
        thread_handle: object,
        pid: int,
        command: list[str],
    ) -> None:
        self._process_handle = process_handle
        self._thread_handle = thread_handle
        self.pid = pid
        self.args = command
        self.returncode: int | None = None
        self.resumed = False

    def resume(self) -> None:
        import win32api
        import win32process

        previous_count = int(win32process.ResumeThread(self._thread_handle))
        if previous_count != 1:
            raise AgentError(
                f"new CK3 primary thread had unexpected suspend count {previous_count}"
            )
        self.resumed = True
        win32api.CloseHandle(self._thread_handle)
        self._thread_handle = None

    def poll(self) -> int | None:
        import win32con
        import win32process

        if self.returncode is not None:
            return self.returncode
        result = int(win32process.GetExitCodeProcess(self._process_handle))
        if result == win32con.STILL_ACTIVE:
            return None
        self.returncode = result
        return result

    def wait(self, timeout: float | None = None) -> int:
        import win32event
        import win32process

        milliseconds = (
            win32event.INFINITE
            if timeout is None
            else max(0, min(0xFFFFFFFE, int(timeout * 1000)))
        )
        result = win32event.WaitForSingleObject(self._process_handle, milliseconds)
        if result == win32event.WAIT_TIMEOUT:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if result != win32event.WAIT_OBJECT_0:
            raise AgentError(f"waiting for CK3 returned unexpected status {result}")
        self.returncode = int(win32process.GetExitCodeProcess(self._process_handle))
        return self.returncode

    def terminate_exact(self) -> None:
        import win32api

        if self.poll() is None:
            win32api.TerminateProcess(self._process_handle, 1)

    def image_path(self) -> Path:
        import win32process

        return Path(win32process.GetModuleFileNameEx(self._process_handle, 0)).resolve()

    def close(self) -> None:
        import win32api

        if self._thread_handle is not None:
            win32api.CloseHandle(self._thread_handle)
            self._thread_handle = None
        if self._process_handle is not None:
            win32api.CloseHandle(self._process_handle)
            self._process_handle = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[xar-autoplayer {time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def validate_native_bridge_launch_config(
    config: NativeBridgeLaunchConfig,
) -> NativeBridgeLaunchConfig:
    """Validate and canonicalize an explicitly enabled native launch."""
    if config.mode not in NATIVE_BRIDGE_LAUNCH_MODES:
        raise AgentError(
            "native bridge mode must be native-headless or hybrid-fallback"
        )
    pipe_name = validate_native_bridge_pipe_name(config.pipe_name)
    dll_path = Path(config.dll_path).resolve()
    injector_path = Path(config.injector_path).resolve()
    if not dll_path.is_file():
        raise AgentError(f"native bridge DLL is missing: {dll_path}")
    if not injector_path.is_file():
        raise AgentError(f"native bridge injector is missing: {injector_path}")
    return NativeBridgeLaunchConfig(
        mode=config.mode,
        pipe_name=pipe_name,
        dll_path=dll_path,
        injector_path=injector_path,
    )


def validate_native_bridge_pipe_name(pipe_name: str) -> str:
    """Validate the shared named-pipe identity without requiring binaries."""
    pipe_prefix = "\\\\.\\pipe\\"
    if (
        not isinstance(pipe_name, str)
        or not pipe_name.startswith(pipe_prefix)
        or len(pipe_name) <= len(pipe_prefix)
        or len(pipe_name) >= 256
        or "\x00" in pipe_name
        or "\r" in pipe_name
        or "\n" in pipe_name
    ):
        raise AgentError(
            "native bridge pipe must be a non-empty \\\\.\\pipe\\ name "
            "shorter than 256 characters"
        )
    return pipe_name


def native_bridge_launch_config_from_environment(
    environment: Mapping[str, str] | None = None,
) -> NativeBridgeLaunchConfig | None:
    """Read explicit launch opt-in; disabled mode ignores all path settings."""
    selected = os.environ if environment is None else environment
    mode = selected.get(NATIVE_BRIDGE_MODE_ENV, NATIVE_BRIDGE_DISABLED)
    if mode == NATIVE_BRIDGE_DISABLED:
        return None
    dll_path = selected.get(NATIVE_BRIDGE_DLL_ENV)
    injector_path = selected.get(NATIVE_BRIDGE_INJECTOR_ENV)
    missing: list[str] = []
    if not dll_path:
        missing.append(NATIVE_BRIDGE_DLL_ENV)
    if not injector_path:
        missing.append(NATIVE_BRIDGE_INJECTOR_ENV)
    if missing:
        raise AgentError(
            f"native bridge mode {mode!r} requires " + ", ".join(missing)
        )
    return validate_native_bridge_launch_config(
        NativeBridgeLaunchConfig(
            mode=mode,
            pipe_name=selected.get(
                NATIVE_BRIDGE_PIPE_ENV, DEFAULT_NATIVE_BRIDGE_PIPE
            ),
            dll_path=Path(dll_path),
            injector_path=Path(injector_path),
        )
    )


def configure_native_bridge_launch_environment(
    mode: str,
    *,
    pipe_name: str | None = None,
    dll_path: Path | None = None,
    injector_path: Path | None = None,
    environment: MutableMapping[str, str] | None = None,
) -> NativeBridgeLaunchConfig | None:
    """Apply CLI launch selection to this process and future CK3 children."""
    target = os.environ if environment is None else environment
    if mode == NATIVE_BRIDGE_DISABLED:
        target[NATIVE_BRIDGE_MODE_ENV] = NATIVE_BRIDGE_DISABLED
        return None
    candidate = {
        NATIVE_BRIDGE_MODE_ENV: mode,
        NATIVE_BRIDGE_PIPE_ENV: pipe_name or DEFAULT_NATIVE_BRIDGE_PIPE,
        NATIVE_BRIDGE_DLL_ENV: str(dll_path) if dll_path is not None else "",
        NATIVE_BRIDGE_INJECTOR_ENV: (
            str(injector_path) if injector_path is not None else ""
        ),
    }
    config = native_bridge_launch_config_from_environment(candidate)
    assert config is not None
    target.update(
        {
            NATIVE_BRIDGE_MODE_ENV: config.mode,
            NATIVE_BRIDGE_PIPE_ENV: config.pipe_name,
            NATIVE_BRIDGE_DLL_ENV: str(config.dll_path),
            NATIVE_BRIDGE_INJECTOR_ENV: str(config.injector_path),
        }
    )
    return config


def append_event(path: Path, event: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: str | None = None
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            prior = json.loads(lines[-1])
            previous = prior.get("event_sha256")
            if not isinstance(previous, str):
                raise AgentError("event log tail lacks its hash-chain digest")
    payload = {"at": utc_now(), "previous_event_sha256": previous, **event}
    payload["event_sha256"] = snapshot_digest(payload)
    with path.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    return str(payload["event_sha256"])


def validate_event_chain(path: Path) -> dict[str, object]:
    previous: str | None = None
    count = 0
    tail: dict[str, object] | None = None
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise AgentError(
                f"event chain line {line_number} is invalid JSON"
            ) from error
        if not isinstance(event, dict):
            raise AgentError(f"event chain line {line_number} is not an object")
        recorded = event.get("event_sha256")
        unsigned = dict(event)
        unsigned.pop("event_sha256", None)
        if recorded != snapshot_digest(unsigned):
            raise AgentError(f"event chain line {line_number} digest differs")
        if event.get("previous_event_sha256") != previous:
            raise AgentError(f"event chain line {line_number} previous link differs")
        previous = str(recorded)
        tail = event
        count += 1
    if tail is None:
        raise AgentError("event chain is empty")
    return {"event_count": count, "tail_sha256": previous, "tail": tail}


def validate_final_report_payload(
    report: dict[str, object], chain: dict[str, object]
) -> None:
    tail = chain.get("tail")
    if not isinstance(tail, dict) or tail.get("kind") != "smoke_finished":
        raise AgentError("event chain does not end with smoke_finished")
    if report.get("finalized") is not True:
        raise AgentError("final report payload is not finalized")
    if report.get("final_event_sha256") != chain.get("tail_sha256"):
        raise AgentError("final report does not bind the event-chain tail")
    if report.get("ok") is not tail.get("ok"):
        raise AgentError("final report result differs from its final event")


def _normal_report_body_sha256(report: dict[str, object]) -> str:
    """Hash every normal-report field that precedes the final WAL commit."""
    return snapshot_digest(
        {
            key: value
            for key, value in report.items()
            if key not in NORMAL_REPORT_BINDING_EXCLUSIONS
        }
    )


def _fsync_existing_file(path: Path) -> None:
    with path.open("r+b") as output:
        output.flush()
        os.fsync(output.fileno())


def _append_normal_final_event_transactionally(
    events: Path, *, ok: bool, report_body_sha256: str
) -> str:
    """Commit one final event, recovering only an exact after-fsync success."""
    before = validate_event_chain(events)
    payload = {
        "kind": "smoke_finished",
        "ok": ok,
        "report_body_sha256": report_body_sha256,
    }
    try:
        return append_event(events, payload)
    except Exception as append_error:
        try:
            after = validate_event_chain(events)
        except BaseException:
            raise
        tail = after.get("tail")
        if (
            after.get("event_count") == int(before["event_count"]) + 1
            and isinstance(tail, dict)
            and set(tail)
            == {
                "at",
                "previous_event_sha256",
                "kind",
                "ok",
                "report_body_sha256",
                "event_sha256",
            }
            and tail.get("previous_event_sha256") == before.get("tail_sha256")
            and tail.get("kind") == "smoke_finished"
            and tail.get("ok") is ok
            and tail.get("report_body_sha256") == report_body_sha256
            and tail.get("event_sha256") == after.get("tail_sha256")
        ):
            try:
                _fsync_existing_file(events)
                durable = validate_event_chain(events)
            except Exception as barrier_error:
                raise append_error from barrier_error
            if (
                durable.get("event_count") == after.get("event_count")
                and durable.get("tail_sha256") == after.get("tail_sha256")
                and durable.get("tail") == tail
            ):
                return str(tail["event_sha256"])
        raise


def _write_normal_final_report_transactionally(
    path: Path, report: dict[str, object]
) -> None:
    """Pre-barrier exact bytes, then atomically publish the final report.

    A post-replace fsync can report failure after a GREEN is already visible.
    Instead, durability of the complete candidate is established on a private
    same-directory file.  Only then may replacement make those bytes public.
    """
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".final.tmp")
    if temporary.exists():
        raise AgentError("normal smoke final report temporary already exists")
    try:
        with temporary.open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    except Exception as barrier_error:
        temporary.unlink(missing_ok=True)
        raise AgentError(
            f"normal smoke final report pre-publication barrier failed: {barrier_error}"
        ) from barrier_error
    try:
        os.replace(temporary, path)
    except Exception as replace_error:
        # An injected wrapper can raise after the operating system committed
        # the replacement.  The source bytes were already fsynced, so exact
        # destination equality is sufficient to reconcile that one case.
        try:
            persisted = path.read_bytes()
        except OSError:
            persisted = b""
        if persisted == raw and not temporary.exists():
            return
        raise AgentError(
            f"normal smoke final report replacement failed: {replace_error}"
        ) from replace_error
    if path.read_bytes() != raw:
        raise AgentError("normal smoke final report bytes differ after replacement")


def _normal_run_reference(path: Path, run_dir: Path) -> str:
    resolved = path.resolve()
    root = run_dir.resolve()
    if not is_relative_to(resolved, root):
        raise AgentError(f"normal smoke artifact escaped its run: {resolved}")
    return resolved.relative_to(root).as_posix()


def _normal_artifact_manifest(run_dir: Path) -> list[dict[str, object]]:
    """Return the complete immutable file inventory except its two seals."""
    root = run_dir.resolve()
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in {"events.jsonl", "report.json"}:
            continue
        if path.is_symlink() or not is_relative_to(path.resolve(), root):
            raise AgentError(f"normal smoke artifact escaped its run: {relative}")
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if len({str(item["path"]) for item in entries}) != len(entries):
        raise AgentError("normal smoke artifact manifest contains duplicate paths")
    return entries


def _verified_normal_artifact_manifest(
    report: dict[str, object], run_dir: Path
) -> dict[str, Path]:
    raw_manifest = report.get("artifacts")
    if not isinstance(raw_manifest, list) or not raw_manifest:
        raise AgentError("normal smoke artifact manifest is missing")
    root = run_dir.resolve()
    verified: dict[str, Path] = {}
    previous = ""
    for index, entry in enumerate(raw_manifest):
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise AgentError(f"normal smoke artifact entry {index} differs")
        relative = entry.get("path")
        size = entry.get("size")
        digest = entry.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or relative.startswith("/")
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative <= previous
            or type(size) is not int
            or size < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
        ):
            raise AgentError(f"normal smoke artifact entry {index} differs")
        candidate = root / Path(relative)
        path = candidate.resolve()
        if (
            not is_relative_to(path, root)
            or candidate.is_symlink()
            or not path.is_file()
            or path.stat().st_size != size
            or sha256_file(path) != digest
        ):
            raise AgentError(f"normal smoke artifact {relative} differs")
        verified[relative] = path
        previous = relative
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.relative_to(root).as_posix() not in {"events.jsonl", "report.json"}
    }
    if actual != set(verified):
        raise AgentError("normal smoke artifact manifest is not the complete run inventory")
    return verified


def _normal_artifact_path(
    verified: dict[str, Path], reference: object, label: str
) -> Path:
    if not isinstance(reference, str) or reference not in verified:
        raise AgentError(f"normal smoke {label} reference differs")
    return verified[reference]


def _archive_normal_debug_prefix(
    spec: EnvironmentSpec,
    debug_evidence: object,
    artifacts: Path,
    archive_name: str,
) -> dict[str, object]:
    """Freeze the exact debug.log prefix used by one live attestation."""
    if not isinstance(debug_evidence, dict):
        raise AgentError("runtime load attestation lacks debug prefix metadata")
    source = Path(str(debug_evidence.get("path", ""))).resolve()
    expected_source = (spec.profile_dir / "logs" / "debug.log").resolve()
    prefix_size = debug_evidence.get("captured_prefix_size")
    expected_hash = str(debug_evidence.get("captured_prefix_sha256", ""))
    if (
        source != expected_source
        or type(prefix_size) is not int
        or prefix_size <= 0
        or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
    ):
        raise AgentError("runtime load attestation debug prefix metadata differs")
    raw = source.read_bytes()
    if len(raw) < prefix_size:
        raise AgentError("runtime debug prefix is shorter than its attestation")
    prefix = raw[:prefix_size]
    if hashlib.sha256(prefix).hexdigest() != expected_hash:
        raise AgentError("runtime debug prefix changed before archival")
    destination = artifacts / archive_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(prefix)
    os.replace(temporary, destination)
    archived = json.loads(json.dumps(debug_evidence, ensure_ascii=False))
    archived.pop("path", None)
    archived["archive_path"] = f"artifacts/{archive_name}"
    archived["archive_sha256"] = sha256_file(destination)
    return archived


def _normalize_visual_references(
    evidence: dict[str, object], run_dir: Path
) -> dict[str, object]:
    archived = json.loads(json.dumps(evidence, ensure_ascii=False))
    frames = archived.get("stable_frame_evidence")
    if not isinstance(frames, list):
        raise AgentError("visible main-menu evidence lacks stable frames")
    for frame in frames:
        if not isinstance(frame, dict):
            raise AgentError("visible main-menu frame evidence differs")
        for field in ("screenshot", "ocr"):
            frame[field] = _normal_run_reference(Path(str(frame.get(field, ""))), run_dir)
    for field in ("screenshot", "ocr"):
        archived[field] = _normal_run_reference(
            Path(str(archived.get(field, ""))), run_dir
        )
    return archived


def _normalize_diagnostic_references(
    evidence: dict[str, object], run_dir: Path
) -> dict[str, object]:
    archived = json.loads(json.dumps(evidence, ensure_ascii=False))
    logs = archived.get("logs")
    if not isinstance(logs, dict):
        raise AgentError("engine diagnostics log inventory differs")
    for record in logs.values():
        if isinstance(record, dict) and record.get("present") is True:
            record["path"] = _normal_run_reference(
                Path(str(record.get("path", ""))), run_dir
            )
    return archived


def validate_smoke_report(run_dir: Path) -> dict[str, object]:
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise AgentError("smoke report root is not an object")
    chain = validate_event_chain(run_dir / "events.jsonl")
    validate_final_report_payload(report, chain)
    # Version 1 is the historical shallow contract used by immutable normal and
    # menu reports.  Never reinterpret those archives under the stronger v2
    # schema; new ordinary smoke reports are self-contained and replayed below.
    if report.get("format_version") == 1:
        return report
    if report.get("format_version") != 2:
        raise AgentError("unsupported smoke report format version")
    _validate_normal_v2_report(report, run_dir, chain)
    return report


def _validate_normal_release_manifest(
    manifest: object, environment: dict[str, object]
) -> None:
    if not isinstance(manifest, dict) or set(manifest) != {
        "files",
        "format_version",
        "git_sha",
        "git_tag",
        "mod_version",
        "workshop_item_id",
    }:
        raise AgentError("normal smoke archived production manifest schema differs")
    mod = environment.get("mod")
    identity = mod.get("release_identity") if isinstance(mod, dict) else None
    if (
        not isinstance(mod, dict)
        or not isinstance(identity, dict)
        or manifest.get("format_version") != identity.get("format_version")
        or manifest.get("git_sha") != mod.get("git_revision")
        or manifest.get("git_tag") != identity.get("git_tag")
        or manifest.get("mod_version") != identity.get("mod_version")
        or manifest.get("workshop_item_id") != identity.get("workshop_item_id")
    ):
        raise AgentError("normal smoke archived production manifest identity differs")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) < 4:
        raise AgentError("normal smoke archived production file inventory differs")
    paths: list[str] = []
    projected: dict[str, dict[str, object]] = {}
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            raise AgentError("normal smoke archived production file entry differs")
        relative = entry.get("path")
        size = entry.get("size")
        digest = entry.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or type(size) is not int
            or size < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
        ):
            raise AgentError("normal smoke archived production file entry differs")
        paths.append(relative)
        projected[relative] = {"size": size, "sha256": digest}
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise AgentError("normal smoke archived production paths differ")
    if not {
        "descriptor.mod",
        "common/game_rules/xar_game_rules.txt",
        "common/on_action/eternal_recurrence_on_actions.txt",
        "events/xar_events.txt",
    } <= set(paths):
        raise AgentError("normal smoke archived production manifest lacks runtime files")
    if (
        len(files) != mod.get("production_file_count")
        or snapshot_digest(projected) != mod.get("production_tree_sha256")
    ):
        raise AgentError("normal smoke archived production tree differs")


def _validate_normal_environment(
    report: dict[str, object], verified: dict[str, Path]
) -> dict[str, object]:
    environment_path = _normal_artifact_path(
        verified, "environment.json", "environment archive"
    )
    production_path = _normal_artifact_path(
        verified, "production.manifest.json", "production manifest archive"
    )
    try:
        environment = json.loads(environment_path.read_text(encoding="utf-8"))
        production = json.loads(production_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal smoke environment archive cannot be parsed: {error}") from error
    if (
        not isinstance(environment, dict)
        or environment.get("environment_sha256") != _contract_digest(environment)
        or environment.get("environment_sha256") != report.get("environment_sha256")
    ):
        raise AgentError("normal smoke archived environment digest differs")
    state_dir = Path(str(environment.get("state_dir", "")))
    profile_dir = Path(str(environment.get("profile_dir", "")))
    game = environment.get("game")
    mod = environment.get("mod")
    load_profile = environment.get("load_profile")
    display = environment.get("display")
    legality = environment.get("legality")
    runtime = environment.get("agent_runtime")
    runtime_git = runtime.get("git") if isinstance(runtime, dict) else None
    provenance = mod.get("source_provenance") if isinstance(mod, dict) else None
    dlc = environment.get("dlc")
    allowed_mounts = dlc.get("allowed_mount_roots") if isinstance(dlc, dict) else None
    rules = environment.get("rules")
    profile = rules.get("profile") if isinstance(rules, dict) else None
    expected_mod_profile = [
        {"rule": rule, "setting": setting} for rule, setting in MOD_RULES
    ]
    if (
        not state_dir.is_absolute()
        or not profile_dir.is_absolute()
        or profile_dir.resolve() != (state_dir / "profile").resolve()
        or not isinstance(game, dict)
        or game.get("raw_version") != VISIBLE_UI_BASELINE_GAME_VERSION
        or game.get("debug_mode") is not False
        or not isinstance(mod, dict)
        or mod.get("name") != EXPECTED_MOD_NAME
        or Path(str(mod.get("production_path", ""))).resolve()
        != (profile_dir / "mod-content" / "xar-production").resolve()
        or mod.get("production_manifest_sha256") != sha256_file(production_path)
        or not isinstance(load_profile, dict)
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
        or legality.get("runtime_logs")
        != "environment attestation only; never policy input"
        or not isinstance(rules, dict)
        or rules.get("declared_vanilla_rule_count") != 81
        or rules.get("ironman") is not False
        or not isinstance(profile, list)
        or len(profile) != 84
        or profile[81:] != expected_mod_profile
        or any(
            not isinstance(entry, dict)
            or set(entry) != {"rule", "setting"}
            or not isinstance(entry.get("rule"), str)
            or not entry["rule"]
            or not isinstance(entry.get("setting"), str)
            or not entry["setting"]
            for entry in profile
        )
        or len({entry["rule"] for entry in profile}) != 84
        or len({entry["setting"] for entry in profile}) != 84
        or any(entry["rule"].startswith("xar_") for entry in profile[:81])
        or rules.get("profile_sha256")
        != hashlib.sha256(
            json.dumps(
                profile, ensure_ascii=True, separators=(",", ":")
            ).encode("ascii")
        ).hexdigest()
        or not isinstance(runtime, dict)
        or not isinstance(runtime_git, dict)
        or runtime_git.get("all_files_tracked") is not True
        or runtime_git.get("dirty") is not False
        or runtime_git.get("untracked_runtime_files") != []
        or runtime_git.get("status") != []
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(runtime_git.get("selected_runtime_revision", ""))
        )
        or not isinstance(provenance, dict)
        or provenance.get("git_dirty") is not False
        or provenance.get("all_release_files_tracked") is not True
        or provenance.get("untracked_release_files") != []
        or provenance.get("git_status") != []
        or provenance.get("git_revision") != mod.get("git_revision")
        or not isinstance(allowed_mounts, list)
        or allowed_mounts != sorted(set(allowed_mounts))
        or any(not isinstance(item, str) or not Path(item).is_absolute() for item in allowed_mounts)
        or snapshot_digest(allowed_mounts) != dlc.get("allowed_mount_roots_sha256")
        or len(allowed_mounts) != dlc.get("installed_descriptor_count")
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(dlc.get("installed_descriptors_sha256", ""))
        )
    ):
        raise AgentError("normal smoke archived environment semantics differ")
    runtime_copy = dict(runtime)
    runtime_hash = runtime_copy.pop("sha256", None)
    files = runtime.get("files")
    if (
        runtime_hash != snapshot_digest(runtime_copy)
        or not isinstance(files, list)
        or runtime.get("file_count") != len(files)
        or any(
            not isinstance(item, dict)
            or set(item) != {"path", "size", "sha256"}
            or not isinstance(item.get("path"), str)
            or type(item.get("size")) is not int
            or item["size"] < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
            for item in files
        )
        or [item["path"] for item in files] != sorted({item["path"] for item in files})
    ):
        raise AgentError("normal smoke archived runtime fingerprint differs")
    _validate_normal_release_manifest(production, environment)
    return environment


def _validate_normal_debug_prefix(
    debug: object,
    verified: dict[str, Path],
    label: str,
    expected_reference: str,
) -> tuple[bytes, Path]:
    if not isinstance(debug, dict) or "path" in debug:
        raise AgentError(f"normal smoke {label} debug metadata differs")
    expected_keys = {
        "captured_prefix_size",
        "captured_prefix_sha256",
        "file_size_after_read",
        "mtime_ns",
        "prelaunch_epoch_ns",
        "cleared_before_launch",
        "archive_path",
        "archive_sha256",
    }
    if set(debug) != expected_keys:
        raise AgentError(f"normal smoke {label} debug metadata differs")
    if debug.get("archive_path") != expected_reference:
        raise AgentError(f"normal smoke {label} debug archive reference differs")
    path = _normal_artifact_path(
        verified, debug.get("archive_path"), f"{label} debug archive"
    )
    raw = path.read_bytes()
    size = debug.get("captured_prefix_size")
    digest = hashlib.sha256(raw).hexdigest()
    if (
        type(size) is not int
        or size <= 0
        or len(raw) != size
        or debug.get("captured_prefix_sha256") != digest
        or debug.get("archive_sha256") != digest
        or type(debug.get("file_size_after_read")) is not int
        or debug["file_size_after_read"] < size
        or type(debug.get("mtime_ns")) is not int
        or type(debug.get("prelaunch_epoch_ns")) is not int
        or debug["mtime_ns"] < debug["prelaunch_epoch_ns"]
        or not isinstance(debug.get("cleared_before_launch"), list)
    ):
        raise AgentError(f"normal smoke {label} debug prefix differs")
    return raw, path


def _validate_normal_load(
    report: dict[str, object],
    environment: dict[str, object],
    verified: dict[str, Path],
) -> None:
    load = report.get("load_attestation")
    process = report.get("process")
    expected_load_keys = {
        "enabled_mods",
        "isolated_mod_mounts",
        "runtime_dlc_mounts",
        "unclassified_mounts",
        "evidence_lines",
        "session_marker_count",
        "source",
        "policy_boundary",
        "debug_log",
        "post_exit_revalidated",
        "post_exit_debug_log",
    }
    if (
        not isinstance(load, dict)
        or set(load) != expected_load_keys
        or not isinstance(process, dict)
    ):
        raise AgentError("normal smoke load attestation differs")
    archive = _normal_artifact_path(
        verified,
        "artifacts/supervisor-load-attestation.json",
        "load attestation archive",
    )
    try:
        archived = json.loads(archive.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal smoke load archive cannot be parsed: {error}") from error
    if archived != load:
        raise AgentError("normal smoke report and archived load attestation differ")
    initial_raw, _ = _validate_normal_debug_prefix(
        load.get("debug_log"),
        verified,
        "initial",
        "artifacts/runtime-debug-prefix.log",
    )
    final_raw, _ = _validate_normal_debug_prefix(
        load.get("post_exit_debug_log"),
        verified,
        "final",
        "artifacts/runtime-debug-post-exit.log",
    )
    if not final_raw.startswith(initial_raw):
        raise AgentError("normal smoke final debug prefix does not extend the initial prefix")
    mod = environment["mod"]
    dlc = environment["dlc"]
    profile_dir = Path(str(environment["profile_dir"]))
    production_dir = Path(str(mod["production_path"]))
    allowed_mounts = dlc["allowed_mount_roots"]
    replayed_initial = parse_runtime_attestation(
        initial_raw.decode("utf-8", errors="ignore"),
        profile_dir,
        production_dir,
        allowed_dlc_mounts=allowed_mounts,
    )
    replayed_final = parse_runtime_attestation(
        final_raw.decode("utf-8", errors="ignore"),
        profile_dir,
        production_dir,
        allowed_dlc_mounts=allowed_mounts,
    )
    semantic_keys = (
        "enabled_mods",
        "isolated_mod_mounts",
        "runtime_dlc_mounts",
        "unclassified_mounts",
        "evidence_lines",
        "session_marker_count",
        "source",
        "policy_boundary",
    )
    if (
        load.get("post_exit_revalidated") is not True
        or any(load.get(key) != replayed_initial.get(key) for key in semantic_keys)
        or any(load.get(key) != replayed_final.get(key) for key in semantic_keys)
        or load.get("enabled_mods")
        != [{"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}]
        or load.get("isolated_mod_mounts") != [str(production_dir.resolve())]
        or load.get("unclassified_mounts") != []
        or load.get("session_marker_count") != 1
        or load.get("debug_log", {}).get("prelaunch_epoch_ns")
        != process.get("fresh_log_epoch_ns")
        or load.get("post_exit_debug_log", {}).get("prelaunch_epoch_ns")
        != process.get("fresh_log_epoch_ns")
        or load.get("debug_log", {}).get("cleared_before_launch")
        != process.get("prelaunch_logs_removed")
        or load.get("post_exit_debug_log", {}).get("cleared_before_launch")
        != process.get("prelaunch_logs_removed")
        or len(set(process.get("prelaunch_logs_removed", [])))
        != len(process.get("prelaunch_logs_removed", []))
        or not set(process.get("prelaunch_logs_removed", []))
        <= {"debug.log", "error.log", "gui_warnings.log"}
    ):
        raise AgentError("normal smoke replayed load attestation differs")


def _validate_normal_visual(
    report: dict[str, object], verified: dict[str, Path]
) -> None:
    visual = report.get("visual_attestation")
    if not isinstance(visual, dict) or set(visual) != {
        "target",
        "target_normalized",
        "stable_frames",
        "stable_frame_evidence",
        "window_rect",
        "screenshot",
        "screenshot_sha256",
        "ocr",
        "ocr_sha256",
    }:
        raise AgentError("normal smoke visible main-menu attestation differs")
    frames = visual.get("stable_frame_evidence")
    target = visual.get("target")
    if (
        not isinstance(target, str)
        or target != "\u65b0\u6e38\u620f"
        or visual.get("target_normalized") != normalize_ocr_text(target)
        or visual.get("stable_frames") != 2
        or not isinstance(frames, list)
        or len(frames) != 2
    ):
        raise AgentError("normal smoke stable main-menu frame contract differs")
    previous_sequence = 0
    previous_monotonic: float | None = None
    canonical_references = (
        (
            "artifacts/main-menu-frame-1.png",
            "artifacts/main-menu-frame-1-ocr.json",
        ),
        ("artifacts/main-menu.png", "artifacts/main-menu-ocr.json"),
    )
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, dict):
            raise AgentError("normal smoke visible frame schema differs")
        screenshot = _normal_artifact_path(
            verified, frame.get("screenshot"), f"visible frame {index} PNG"
        )
        ocr_path = _normal_artifact_path(
            verified, frame.get("ocr"), f"visible frame {index} OCR"
        )
        try:
            recorded_ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
            from PIL import Image

            with Image.open(screenshot) as image:
                image.load()
                if (
                    image.format != "PNG"
                    or image.size != EXPECTED_RESOLUTION
                    or image.mode not in {"RGB", "RGBA"}
                ):
                    raise AgentError("normal smoke visible frame PNG geometry differs")
                replayed_ocr = _ocr_items(image, MAIN_MENU_REGION)
        except AgentError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentError(f"normal smoke visible frame cannot be replayed: {error}") from error
        sequence = frame.get("capture_sequence")
        monotonic = frame.get("captured_monotonic")
        rect = frame.get("window_rect")
        if (
            set(frame)
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
            or frame.get("screenshot") != canonical_references[index - 1][0]
            or frame.get("ocr") != canonical_references[index - 1][1]
            or type(sequence) is not int
            or sequence != (previous_sequence + 1 if index > 1 else sequence)
            or sequence <= 0
            or type(monotonic) not in {int, float}
            or not math.isfinite(float(monotonic))
            or (previous_monotonic is not None and float(monotonic) <= previous_monotonic)
            or rect != [0, 0, 2560, 1440]
            or frame.get("screenshot_sha256") != sha256_file(screenshot)
            or frame.get("ocr_sha256") != sha256_file(ocr_path)
            or frame.get("exact_match_count") != 1
            or not isinstance(recorded_ocr, list)
            or replayed_ocr != recorded_ocr
            or unique_exact_ocr_match(recorded_ocr, target) is None
        ):
            raise AgentError("normal smoke replayed visible frame differs")
        try:
            captured = datetime.fromisoformat(str(frame.get("captured_at", "")))
        except ValueError as error:
            raise AgentError("normal smoke visible frame timestamp differs") from error
        if captured.tzinfo != timezone.utc:
            raise AgentError("normal smoke visible frame timestamp differs")
        previous_sequence = sequence
        previous_monotonic = float(monotonic)
    final = frames[1]
    if (
        visual.get("window_rect") != final.get("window_rect")
        or visual.get("screenshot") != final.get("screenshot")
        or visual.get("screenshot_sha256") != final.get("screenshot_sha256")
        or visual.get("ocr") != final.get("ocr")
        or visual.get("ocr_sha256") != final.get("ocr_sha256")
    ):
        raise AgentError("normal smoke top-level visible evidence differs")
    crop = _normal_artifact_path(
        verified, "artifacts/main-menu-crop.png", "visible main-menu crop"
    )
    try:
        from PIL import Image

        second_path = _normal_artifact_path(
            verified, final.get("screenshot"), "final visible frame PNG"
        )
        with Image.open(second_path) as image, Image.open(crop) as archived_crop:
            image.load()
            archived_crop.load()
            expected_crop = image.crop(_region_bbox(image.size, MAIN_MENU_REGION))
            if (
                archived_crop.format != "PNG"
                or archived_crop.size != expected_crop.size
                or archived_crop.mode != expected_crop.mode
                or archived_crop.tobytes() != expected_crop.tobytes()
            ):
                raise AgentError("normal smoke main-menu crop differs from its frame")
    except AgentError:
        raise
    except OSError as error:
        raise AgentError(f"normal smoke main-menu crop cannot be replayed: {error}") from error


def _validate_normal_diagnostics(
    report: dict[str, object],
    environment: dict[str, object],
    verified: dict[str, Path],
) -> None:
    diagnostics = report.get("engine_diagnostics")
    if not isinstance(diagnostics, dict) or set(diagnostics) != {
        "policy_boundary",
        "zero_diagnostics",
        "current_mod_diagnostics",
        "current_mod_diagnostic_hits",
        "logs",
    }:
        raise AgentError("normal smoke engine diagnostics schema differs")
    logs = diagnostics.get("logs")
    if not isinstance(logs, dict) or set(logs) != {"error.log", "gui_warnings.log"}:
        raise AgentError("normal smoke diagnostic log inventory differs")
    all_hits: list[dict[str, object]] = []
    zero = True
    for name in ("error.log", "gui_warnings.log"):
        record = logs[name]
        if not isinstance(record, dict):
            raise AgentError("normal smoke diagnostic log record differs")
        if record.get("present") is False:
            if record != {"present": False, "diagnostic_records": 0}:
                raise AgentError("normal smoke absent diagnostic record differs")
            continue
        if set(record) != {
            "present",
            "path",
            "sha256",
            "size",
            "mtime_ns",
            "diagnostic_records",
            "nonempty_lines",
        } or record.get("present") is not True:
            raise AgentError("normal smoke present diagnostic record differs")
        expected_reference = f"artifacts/supervisor-{name}"
        if record.get("path") != expected_reference:
            raise AgentError("normal smoke diagnostic archive reference differs")
        path = _normal_artifact_path(
            verified, record.get("path"), f"{name} diagnostic archive"
        )
        raw = path.read_bytes()
        replayed = analyze_engine_log_bytes(
            name,
            raw,
            expected_mod_name=EXPECTED_MOD_NAME,
            production_path=Path(str(environment["mod"]["production_path"])),
        )
        if (
            record.get("sha256") != hashlib.sha256(raw).hexdigest()
            or record.get("size") != len(raw)
            or record.get("diagnostic_records") != replayed["diagnostic_records"]
            or record.get("nonempty_lines") != replayed["nonempty_lines"]
            or type(record.get("mtime_ns")) is not int
            or record["mtime_ns"] < report["process"]["fresh_log_epoch_ns"]
        ):
            raise AgentError("normal smoke replayed diagnostic record differs")
        if replayed["diagnostic_records"] or replayed["nonempty_lines"]:
            zero = False
        all_hits.extend(replayed["current_mod_diagnostic_hits"])
    expected_current = bool(all_hits)
    if (
        diagnostics.get("policy_boundary")
        != "supervisor evidence only; unavailable to gameplay policy"
        or diagnostics.get("zero_diagnostics") is not zero
        or diagnostics.get("current_mod_diagnostics") is not expected_current
        or diagnostics.get("current_mod_diagnostic_hits") != all_hits
        or expected_current
    ):
        raise AgentError("normal smoke replayed engine diagnostics differ")


def _validate_empty_ck3_inventory(inventory: object, label: str) -> None:
    if (
        not isinstance(inventory, dict)
        or set(inventory)
        != {"tasklist_returncode", "tasklist_pids", "wmi_pids", "processes"}
        or inventory.get("tasklist_returncode") != 0
        or inventory.get("tasklist_pids") != []
        or inventory.get("wmi_pids") != []
        or inventory.get("processes") != []
    ):
        raise AgentError(f"normal smoke {label} CK3 inventory differs")


def _validate_normal_process_and_shutdown(
    report: dict[str, object], environment: dict[str, object]
) -> None:
    process = report.get("process")
    shutdown = report.get("shutdown_attestation")
    post_inventory = report.get("post_shutdown_ck3_inventory")
    if not isinstance(process, dict) or set(process) != {
        "pid",
        "watchdog_pid",
        "arguments",
        "debug_mode",
        "fresh_log_epoch_ns",
        "prelaunch_logs_removed",
        "pre_resume_ck3_inventory",
        "identity",
        "handle_trust",
    }:
        raise AgentError("normal smoke process contract differs")
    pid = process.get("pid")
    identity = process.get("identity")
    trust = process.get("handle_trust")
    inventory = process.get("pre_resume_ck3_inventory")
    if (
        type(pid) is not int
        or pid <= 0
        or type(process.get("watchdog_pid")) is not int
        or process["watchdog_pid"] <= 0
        or process["watchdog_pid"] == pid
        or not isinstance(process.get("arguments"), list)
        or not process["arguments"]
        or process.get("debug_mode") is not False
        or type(process.get("fresh_log_epoch_ns")) is not int
        or process["fresh_log_epoch_ns"] <= 0
        or not isinstance(process.get("prelaunch_logs_removed"), list)
        or not isinstance(identity, dict)
        or set(identity)
        != {"pid", "parent_pid", "name", "executable", "creation_date"}
        or identity.get("pid") != pid
        or type(identity.get("parent_pid")) is not int
        or identity["parent_pid"] <= 0
        or str(identity.get("name", "")).casefold() != "ck3.exe"
        or not isinstance(identity.get("executable"), str)
        or not Path(identity["executable"]).is_absolute()
        or not isinstance(identity.get("creation_date"), str)
        or not identity["creation_date"]
        or not isinstance(trust, dict)
        or trust
        != {
            "pinned_process_handle": True,
            "owned_kill_on_close_job": True,
            "created_suspended_before_job_assignment": True,
            "pre_resume_identity_cross_validated": True,
        }
    ):
        raise AgentError("normal smoke pinned process identity differs")
    expected_executable = str(Path(identity["executable"]).resolve())
    environment_executable = str(Path(str(environment["game"]["executable"])).resolve())
    expected_arguments = [
        environment_executable,
        "-gdpr-compliant",
        f"-userdir={environment['profile_dir']}",
    ]
    if (
        not _same_executable(expected_executable, environment_executable)
        or process["arguments"] != expected_arguments
        or any(str(item).casefold() == "-debug_mode" for item in process["arguments"])
    ):
        raise AgentError("normal smoke process command executable differs")
    if (
        not isinstance(inventory, dict)
        or set(inventory)
        != {"tasklist_returncode", "tasklist_pids", "wmi_pids", "processes"}
        or inventory.get("tasklist_returncode") != 0
        or inventory.get("tasklist_pids") != [pid]
        or inventory.get("wmi_pids") != [pid]
        or not isinstance(inventory.get("processes"), list)
        or len(inventory["processes"]) != 1
    ):
        raise AgentError("normal smoke pre-resume CK3 singleton differs")
    row = inventory["processes"][0]
    if (
        not isinstance(row, dict)
        or set(row) != {"pid", "parent_pid", "name", "executable", "creation_date"}
        or row.get("pid") != pid
        or row.get("parent_pid") != identity.get("parent_pid")
        or str(row.get("name", "")).casefold() != "ck3.exe"
        or (
            row.get("executable")
            and not _same_executable(row.get("executable"), expected_executable)
        )
        or not same_process_creation_time(
            row.get("creation_date"), identity.get("creation_date")
        )
    ):
        raise AgentError("normal smoke pre-resume process identity differs")
    if not isinstance(shutdown, dict) or set(shutdown) != {
        "nonce",
        "ck3_pid",
        "ck3_creation_date",
        "ck3_exit_code",
        "job_active_processes_before_termination",
        "job_active_processes_final",
        "tree_gone",
        "cleanup_proven",
        "final_ck3_inventory",
        "watchdog_pid",
        "watchdog_creation_date",
        "watchdog_state_before",
        "watchdog_state_after",
        "control_files_absent",
        "contract_errors",
        "ok",
    }:
        raise AgentError("normal smoke shutdown attestation differs")
    if (
        shutdown.get("ck3_pid") != pid
        or shutdown.get("ck3_creation_date") != identity.get("creation_date")
        or shutdown.get("watchdog_pid") != process.get("watchdog_pid")
        or not isinstance(shutdown.get("watchdog_creation_date"), str)
        or not shutdown["watchdog_creation_date"]
        or not same_process_creation_time(
            shutdown["watchdog_creation_date"], shutdown["watchdog_creation_date"]
        )
        or type(shutdown.get("ck3_exit_code")) is not int
        or shutdown["ck3_exit_code"] != 1
        or type(shutdown.get("job_active_processes_before_termination")) is not int
        or shutdown["job_active_processes_before_termination"] < 1
        or type(shutdown.get("job_active_processes_final")) is not int
        or shutdown.get("tree_gone") is not True
        or shutdown.get("cleanup_proven") is not True
        or shutdown.get("job_active_processes_final") != 0
        or shutdown.get("watchdog_state_before") != "running"
        or shutdown.get("watchdog_state_after") != "absent"
        or shutdown.get("contract_errors") != []
        or shutdown.get("ok") is not True
    ):
        raise AgentError("normal smoke shutdown process binding differs")
    _validate_empty_ck3_inventory(
        shutdown.get("final_ck3_inventory"), "shutdown-final"
    )
    controls = shutdown.get("control_files_absent")
    nonce = shutdown.get("nonce")
    control_root = Path(str(environment["state_dir"])) / "control"
    expected_controls = {
        str(control_root / "ck3.json"),
        str(control_root / "ck3.watchdog_error"),
        str(control_root / f"watchdog-{nonce}.ready.json"),
        str(control_root / "unsafe-cleanup.json"),
    }
    if (
        not re.fullmatch(r"[0-9a-f]{32}", str(nonce))
        or
        not isinstance(controls, dict)
        or set(controls) != expected_controls
        or any(value is not True for value in controls.values())
    ):
        raise AgentError("normal smoke shutdown control cleanup differs")
    _validate_empty_ck3_inventory(post_inventory, "post-shutdown")


def _load_normal_protected_snapshot(path: Path, label: str) -> dict[str, object]:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as source:
            payload = json.load(source)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal smoke {label} protected snapshot cannot parse: {error}") from error
    if (
        not isinstance(payload, dict)
        or set(payload) != {"digest", "stores", "allowed_volatile"}
        or not isinstance(payload.get("stores"), dict)
        or set(payload["stores"])
        != {"real_profile", "steam_userdata", "workshop"}
        or any(not isinstance(value, dict) for value in payload["stores"].values())
        or payload.get("digest") != snapshot_digest(payload["stores"])
        or not isinstance(payload.get("allowed_volatile"), dict)
        or set(payload["allowed_volatile"]) != {"steam_remotecache", "policy"}
        or not isinstance(payload["allowed_volatile"].get("steam_remotecache"), dict)
        or payload["allowed_volatile"].get("policy")
        != "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected."
    ):
        raise AgentError(f"normal smoke {label} protected snapshot differs")
    return payload


def _validate_normal_protected(
    report: dict[str, object], verified: dict[str, Path]
) -> tuple[dict[str, object], dict[str, object]]:
    protected = report.get("protected_storage")
    if not isinstance(protected, dict) or set(protected) != {
        "post_exit_matches_baseline",
        "continuous_quiet_seconds",
        "runtime_write_absence_proven",
        "sha256",
        "before_snapshot",
        "before_snapshot_sha256",
        "after_snapshot",
        "after_snapshot_sha256",
        "allowed_volatile_before",
        "allowed_volatile_after",
    }:
        raise AgentError("normal smoke protected-storage attestation differs")
    before_path = _normal_artifact_path(
        verified, protected.get("before_snapshot"), "protected-before"
    )
    after_path = _normal_artifact_path(
        verified, protected.get("after_snapshot"), "protected-after"
    )
    if (
        protected.get("before_snapshot") != "protected-before.json.gz"
        or protected.get("after_snapshot") != "protected-after.json.gz"
    ):
        raise AgentError("normal smoke protected snapshot references differ")
    before = _load_normal_protected_snapshot(before_path, "before")
    after = _load_normal_protected_snapshot(after_path, "after")
    if (
        protected.get("post_exit_matches_baseline") is not True
        or protected.get("continuous_quiet_seconds") != 5
        or protected.get("runtime_write_absence_proven") is not False
        or protected.get("before_snapshot_sha256") != sha256_file(before_path)
        or protected.get("after_snapshot_sha256") != sha256_file(after_path)
        or before.get("stores") != after.get("stores")
        or before.get("digest") != after.get("digest")
        or protected.get("sha256") != before.get("digest")
        or protected.get("allowed_volatile_before") != before.get("allowed_volatile")
        or protected.get("allowed_volatile_after") != after.get("allowed_volatile")
    ):
        raise AgentError("normal smoke protected-storage replay differs")
    return before, after


def _validate_normal_v2_green_payload(
    report: dict[str, object], run_dir: Path, verified: dict[str, Path]
) -> tuple[dict[str, object], dict[str, object]]:
    """Replay every GREEN claim that does not depend on the final WAL row."""
    environment = _validate_normal_environment(report, verified)
    _validate_normal_process_and_shutdown(report, environment)
    _validate_normal_visual(report, verified)
    _validate_normal_load(report, environment, verified)
    _validate_normal_diagnostics(report, environment, verified)
    before, _after = _validate_normal_protected(report, verified)
    if report.get("production_tree_unchanged") is not True:
        raise AgentError("normal smoke production postflight differs")
    return environment, before


def _normal_utc_timestamp(value: object, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as error:
        raise AgentError(f"normal smoke {label} timestamp differs") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise AgentError(f"normal smoke {label} timestamp is not UTC")
    return parsed


def _validate_normal_event_prefix(
    report: dict[str, object], run_dir: Path, events: Path
) -> None:
    try:
        rows = [
            json.loads(line)
            for line in events.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal smoke event prefix cannot parse: {error}") from error
    expected_kinds = list(NORMAL_GREEN_EVENT_ORDER[:-1])
    expected_keys = (
        {
            "at",
            "previous_event_sha256",
            "kind",
            "environment_sha256",
            "protected_storage_sha256",
            "protected_snapshot_sha256",
            "event_sha256",
        },
        {"at", "previous_event_sha256", "kind", "pid", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "pid", "event_sha256"},
    )
    protected = report["protected_storage"]
    process = report["process"]
    if (
        [row.get("kind") for row in rows] != expected_kinds
        or any(set(row) != keys for row, keys in zip(rows, expected_keys))
        or rows[0].get("environment_sha256") != report.get("environment_sha256")
        or rows[0].get("protected_storage_sha256") != protected.get("sha256")
        or rows[0].get("protected_snapshot_sha256")
        != protected.get("before_snapshot_sha256")
        or rows[1].get("pid") != process.get("pid")
        or rows[4].get("pid") != process.get("pid")
    ):
        raise AgentError("normal smoke candidate lifecycle prefix differs")
    timestamps = [
        _normal_utc_timestamp(row.get("at"), f"event {index}")
        for index, row in enumerate(rows, start=1)
    ]
    if any(right < left for left, right in zip(timestamps, timestamps[1:])):
        raise AgentError("normal smoke candidate event timestamps regress")
    chain = validate_event_chain(events)
    if chain.get("event_count") != 5 or chain.get("tail", {}).get("kind") != "tracked_process_stopped":
        raise AgentError("normal smoke candidate event-chain prefix differs")


def _validate_normal_v2_green_candidate(
    report: dict[str, object], run_dir: Path, events: Path
) -> None:
    candidate_keys = {
        "format_version",
        "run_id",
        "kind",
        "acceptance_claim",
        "clean_engine_boot_required",
        "started_at",
        "finished_at",
        "valid_score_episode",
        "environment_sha256",
        "run_dir",
        "replay_trust_model",
        "process",
        "visual_attestation",
        "load_attestation",
        "shutdown_attestation",
        "post_shutdown_ck3_inventory",
        "engine_diagnostics",
        "protected_storage",
        "production_tree_unchanged",
        "artifacts",
        "finalized",
        "ok",
    }
    started = _normal_utc_timestamp(report.get("started_at"), "report start")
    finished = _normal_utc_timestamp(report.get("finished_at"), "report finish")
    if (
        set(report) != candidate_keys
        or report.get("format_version") != 2
        or report.get("run_id") != run_dir.resolve().name
        or report.get("run_dir") != "."
        or report.get("kind") != "infrastructure_smoke"
        or report.get("acceptance_claim")
        != "isolated_single_mod_visible_main_menu_only"
        or report.get("clean_engine_boot_required") is not False
        or report.get("valid_score_episode") is not False
        or report.get("replay_trust_model") != NORMAL_REPLAY_TRUST_MODEL
        or report.get("finalized") is not False
        or report.get("ok") is not False
        or finished < started
    ):
        raise AgentError("normal smoke candidate GREEN report schema differs")
    verified = _verified_normal_artifact_manifest(report, run_dir)
    _validate_normal_v2_green_payload(report, run_dir, verified)
    _validate_normal_event_prefix(report, run_dir, events)


def _publish_normal_provisional_failure(
    report: dict[str, object], path: Path, error: Exception
) -> None:
    """Persist a plainly non-final report when no replayable seal is possible."""
    report["finalized"] = False
    report["ok"] = False
    report["error"] = str(error)
    for field in (
        "report_body_sha256",
        "final_event_sha256",
        "event_chain",
    ):
        report.pop(field, None)
    write_json_atomic(path, report)


def _finalize_normal_smoke_report(
    report: dict[str, object],
    run_dir: Path,
    events: Path,
    primary_error: Exception | None,
) -> Exception | None:
    """Seal one replayable v2 report or leave a non-final provisional report.

    Artifact enumeration is performed before candidate replay and again after
    it.  The second inventory closes a fault window in which bytes can change
    while the candidate verifier is reading them.  If either inventory cannot
    be established, no final WAL row is authorized.
    """
    report_path = run_dir / "report.json"
    try:
        initial_manifest = _normal_artifact_manifest(run_dir)
        report["artifacts"] = initial_manifest
    except Exception as manifest_error:
        failure = AgentError(
            f"normal smoke artifact manifest could not be established: {manifest_error}"
        )
        _publish_normal_provisional_failure(report, report_path, failure)
        raise failure from manifest_error
    if primary_error is None:
        try:
            _validate_normal_v2_green_candidate(report, run_dir, events)
        except Exception as replay_error:
            primary_error = AgentError(
                f"candidate GREEN self-contained replay failed: {replay_error}"
            )
    try:
        # Always refresh after candidate replay, not only on failure.  A
        # validator or filesystem fault must not leave a stale manifest in a
        # finalized RED or GREEN report.
        final_manifest = _normal_artifact_manifest(run_dir)
        report["artifacts"] = final_manifest
        _verified_normal_artifact_manifest(report, run_dir)
    except Exception as manifest_error:
        failure = AgentError(
            f"normal smoke final artifact manifest could not be established: {manifest_error}"
        )
        _publish_normal_provisional_failure(report, report_path, failure)
        raise failure from manifest_error
    if final_manifest != initial_manifest and primary_error is None:
        primary_error = AgentError(
            "normal smoke artifact bytes changed during candidate replay"
        )
    candidate_ok = primary_error is None
    if primary_error is not None:
        report["error"] = str(primary_error)
    report_body_sha256 = _normal_report_body_sha256(report)
    report["report_body_sha256"] = report_body_sha256
    final_event_sha256 = _append_normal_final_event_transactionally(
        events,
        ok=candidate_ok,
        report_body_sha256=report_body_sha256,
    )
    report["final_event_sha256"] = final_event_sha256
    report["finalized"] = True
    report["ok"] = candidate_ok
    event_chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": event_chain["event_count"],
        "tail_sha256": event_chain["tail_sha256"],
    }
    validate_final_report_payload(report, event_chain)
    _write_normal_final_report_transactionally(report_path, report)
    return primary_error


def _validate_normal_v2_report(
    report: dict[str, object], run_dir: Path, chain: dict[str, object]
) -> None:
    tail = chain.get("tail")
    expected_body = _normal_report_body_sha256(report)
    expected_green_keys = {
        "format_version",
        "run_id",
        "kind",
        "acceptance_claim",
        "clean_engine_boot_required",
        "started_at",
        "finished_at",
        "valid_score_episode",
        "environment_sha256",
        "run_dir",
        "replay_trust_model",
        "process",
        "visual_attestation",
        "load_attestation",
        "shutdown_attestation",
        "post_shutdown_ck3_inventory",
        "engine_diagnostics",
        "protected_storage",
        "production_tree_unchanged",
        "artifacts",
        "report_body_sha256",
        "final_event_sha256",
        "event_chain",
        "finalized",
        "ok",
    }
    if (
        report.get("kind") != "infrastructure_smoke"
        or report.get("acceptance_claim")
        != "isolated_single_mod_visible_main_menu_only"
        or report.get("valid_score_episode") is not False
        or report.get("run_id") != run_dir.resolve().name
        or report.get("run_dir") != "."
        or report.get("replay_trust_model") != NORMAL_REPLAY_TRUST_MODEL
        or not isinstance(tail, dict)
        or report.get("report_body_sha256") != expected_body
        or tail.get("report_body_sha256") != expected_body
    ):
        raise AgentError("normal smoke final report-body binding differs")
    verified = _verified_normal_artifact_manifest(report, run_dir)
    # Failed v2 runs remain structurally replayable without inventing evidence
    # for phases that were never reached.  A qualification GREEN must satisfy
    # every semantic replay below.
    if report.get("ok") is not True:
        return
    started = _normal_utc_timestamp(report.get("started_at"), "report start")
    finished = _normal_utc_timestamp(report.get("finished_at"), "report finish")
    if (
        set(report) != expected_green_keys
        or report.get("clean_engine_boot_required") is not False
        or finished < started
    ):
        raise AgentError("normal smoke GREEN report schema differs")
    _environment, before = _validate_normal_v2_green_payload(
        report, run_dir, verified
    )
    events_path = run_dir / "events.jsonl"
    try:
        rows = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal smoke event archive cannot parse: {error}") from error
    process = report["process"]
    protected = report["protected_storage"]
    expected_event_keys = (
        {
            "at",
            "previous_event_sha256",
            "kind",
            "environment_sha256",
            "protected_storage_sha256",
            "protected_snapshot_sha256",
            "event_sha256",
        },
        {"at", "previous_event_sha256", "kind", "pid", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "event_sha256"},
        {"at", "previous_event_sha256", "kind", "pid", "event_sha256"},
        {
            "at",
            "previous_event_sha256",
            "kind",
            "ok",
            "report_body_sha256",
            "event_sha256",
        },
    )
    if (
        [row.get("kind") for row in rows] != list(NORMAL_GREEN_EVENT_ORDER)
        or any(set(row) != keys for row, keys in zip(rows, expected_event_keys))
        or report.get("event_chain")
        != {
            "event_count": chain.get("event_count"),
            "tail_sha256": chain.get("tail_sha256"),
        }
        or rows[0].get("environment_sha256") != report.get("environment_sha256")
        or rows[0].get("protected_storage_sha256") != before.get("digest")
        or rows[0].get("protected_snapshot_sha256")
        != protected.get("before_snapshot_sha256")
        or rows[1].get("pid") != process.get("pid")
        or rows[4].get("pid") != process.get("pid")
        or rows[5].get("ok") is not True
        or rows[5].get("report_body_sha256") != expected_body
    ):
        raise AgentError("normal smoke lifecycle event binding differs")
    event_times = [
        _normal_utc_timestamp(row.get("at"), f"event {index}")
        for index, row in enumerate(rows, start=1)
    ]
    if any(right < left for left, right in zip(event_times, event_times[1:])):
        raise AgentError("normal smoke lifecycle event timestamps regress")


def write_gzip_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as output:
        json.dump(payload, output, ensure_ascii=False, separators=(",", ":"))
        output.write("\n")
    os.replace(temporary, path)


def _pid_running(pid: int) -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        timeout=15,
    )
    return any(f'"{pid}"' in line for line in result.stdout.splitlines())


def _is_wmi_moniker_syntax_error(error: BaseException) -> bool:
    """Recognize pywin32's uninitialized worker-thread WMI moniker failure."""
    hresult = getattr(error, "hresult", None)
    if hresult == -2147221020:  # MK_E_SYNTAX
        return True
    return bool(error.args and error.args[0] == -2147221020)


def _process_identity(pid: int) -> dict[str, object] | None:
    if os.name != "nt":
        return None
    try:
        import win32com.client

        service = win32com.client.GetObject("winmgmts:")
        rows = service.ExecQuery(
            "SELECT ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate,CommandLine "
            f"FROM Win32_Process WHERE ProcessId={pid}"
        )
    except Exception as error:
        if not (
            _is_access_denied(error)
            or _is_wmi_moniker_syntax_error(error)
        ):
            raise
        identity = _toolhelp_process_identity(pid)
        if identity is None:
            return None
        return {
            **identity,
            "command_line": _FALLBACK_WATCHDOG_COMMAND_LINES.get(pid, ""),
        }
    row = next(iter(rows), None)
    if row is None:
        return None
    return {
        "pid": int(row.ProcessId),
        "parent_pid": int(row.ParentProcessId),
        "name": str(row.Name),
        "executable": str(row.ExecutablePath or ""),
        "creation_date": str(row.CreationDate),
        "command_line": str(row.CommandLine or ""),
    }


def _same_executable(first: object, second: object) -> bool:
    return os.path.normcase(os.path.abspath(str(first))) == os.path.normcase(
        os.path.abspath(str(second))
    )


def _authenticated_pid_running(
    pid: int, executable: Path, creation_date: str
) -> bool:
    try:
        identity = _process_identity(pid)
    except Exception:
        return False
    return bool(
        identity
        and _same_executable(identity["executable"], executable)
        and identity["creation_date"] == creation_date
    )


def _authenticated_watchdog_running(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> bool:
    return (
        _authenticated_watchdog_state(
            pid, creation_date, parent_pid, nonce
        )
        == "running"
    )


def _authenticated_watchdog_state(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> str:
    try:
        identity = _process_identity(pid)
    except Exception:
        return "unknown"
    if identity is None or identity["creation_date"] != creation_date:
        return "absent"
    command = str(identity["command_line"]).casefold()
    matches = (
        str(identity["name"]).casefold() in {"python.exe", "pythonw.exe"}
        and str(PROCESS_WATCHDOG).casefold() in command
        and str(parent_pid) in command
        and nonce.casefold() in command
    )
    return "running" if matches else "unknown"


def _stop_authenticated_watchdog(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> bool:
    """Pin the process object before the final identity check and termination."""
    import win32api
    import win32con
    import win32event

    try:
        process_handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE
            | win32con.SYNCHRONIZE
            | win32con.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
    except Exception as error:
        state = _authenticated_watchdog_state(
            pid, creation_date, parent_pid, nonce
        )
        if state == "absent":
            _forget_fallback_watchdog(pid)
            return False
        raise UnsafeCleanupError(
            f"authenticated watchdog PID {pid} could not be pinned: {error}"
        ) from error
    try:
        state = _authenticated_watchdog_state(pid, creation_date, parent_pid, nonce)
        if state == "unknown":
            raise UnsafeCleanupError(
                f"authenticated watchdog PID {pid} identity is unknown"
            )
        if state == "absent":
            return False
        win32api.TerminateProcess(process_handle, 1)
        result = win32event.WaitForSingleObject(process_handle, 10_000)
        if result != win32event.WAIT_OBJECT_0:
            raise AgentError(f"authenticated watchdog PID {pid} did not exit")
        _forget_fallback_watchdog(pid)
        return True
    finally:
        win32api.CloseHandle(process_handle)


def _forget_fallback_watchdog(pid: int) -> None:
    process = _FALLBACK_WATCHDOG_PROCESSES.pop(pid, None)
    _FALLBACK_WATCHDOG_COMMAND_LINES.pop(pid, None)
    if process is None:
        return
    try:
        process.wait(timeout=1)
    except (subprocess.TimeoutExpired, OSError):
        pass


def _rebind_fallback_watchdog(bootstrap_pid: int, actual_pid: int) -> None:
    if bootstrap_pid == actual_pid:
        return
    command = _FALLBACK_WATCHDOG_COMMAND_LINES.pop(bootstrap_pid, None)
    process = _FALLBACK_WATCHDOG_PROCESSES.pop(bootstrap_pid, None)
    if process is not None:
        try:
            process.wait(timeout=1)
        except (subprocess.TimeoutExpired, OSError):
            pass
    if command is not None:
        _FALLBACK_WATCHDOG_COMMAND_LINES[actual_pid] = command


def _start_process_watchdog(
    parent_pid: int,
    parent_executable: Path,
    parent_creation_date: str,
    nonce: str,
    ready_file: Path,
    record_file: Path,
    unsafe_marker: Path,
    game_exe: Path,
    final_evidence: Path | None = None,
) -> tuple[int, str]:
    watchdog_python = Path(sys.executable).with_name("pythonw.exe")
    if not watchdog_python.is_file():
        watchdog_python = Path(sys.executable)
    arguments = [
        str(watchdog_python),
        # The watchdog is created through Win32_Process.Create when possible;
        # that detached boundary does not reliably inherit the caller's
        # PYTHONDONTWRITEBYTECODE environment.  Keep the clean source export
        # immutable even while the watchdog imports its package helpers.
        "-B",
        str(PROCESS_WATCHDOG),
        str(parent_pid),
        str(parent_executable),
        parent_creation_date,
        nonce,
        str(ready_file),
        str(record_file),
        str(unsafe_marker),
        str(game_exe),
    ]
    if final_evidence is not None:
        arguments.append(str(final_evidence))
    command = subprocess.list2cmdline(arguments)
    literal = "'" + command.replace("'", "''") + "'"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$result = Invoke-CimMethod -ClassName Win32_Process "
            f"-MethodName Create -Arguments @{{CommandLine={literal}}}; "
            "if ($result.ReturnValue -ne 0) { exit $result.ReturnValue }; "
            "$result.ProcessId",
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        timeout=15,
    )
    detached_fallback = result.returncode != 0 and _is_access_denied(
        result.stderr
    )
    if result.returncode != 0 and not detached_fallback:
        raise AgentError(
            f"process watchdog launch failed: rc={result.returncode}, "
            f"stderr={result.stderr.strip()!r}"
        )
    if detached_fallback:
        try:
            bootstrap_process = subprocess.Popen(
                arguments,
                close_fds=True,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                ),
            )
        except OSError as error:
            raise AgentError(
                f"process watchdog fallback launch failed: {error}"
            ) from error
        bootstrap_pid = int(bootstrap_process.pid)
        _FALLBACK_WATCHDOG_COMMAND_LINES[bootstrap_pid] = command
        _FALLBACK_WATCHDOG_PROCESSES[bootstrap_pid] = bootstrap_process
    else:
        if result.stdout.strip():
            try:
                bootstrap_pid = int(result.stdout.strip().splitlines()[-1])
            except ValueError as error:
                raise AgentError(
                    f"process watchdog returned no PID: {result.stdout!r}"
                ) from error
            # Worker-thread WMI access can fail and force _process_identity()
            # onto Toolhelp, which has no command-line field.  We created this
            # exact process and command, so retain that nonce-bound command for
            # the same fallback authentication used by detached launches.
            _FALLBACK_WATCHDOG_COMMAND_LINES[bootstrap_pid] = command
        else:
            # In the managed sandbox Win32_Process.Create succeeds but its
            # ProcessId projection is suppressed.  The child still proves its
            # exact PID by atomically publishing the nonce-bound ready record.
            no_pid_deadline = time.monotonic() + 10
            error_file = record_file.with_suffix(".watchdog_error")
            while time.monotonic() < no_pid_deadline:
                if error_file.is_file():
                    detail = error_file.read_text(
                        encoding="utf-8", errors="replace"
                    ).strip()
                    raise AgentError(
                        f"process watchdog bootstrap failed: {detail}"
                    )
                if ready_file.is_file():
                    try:
                        bootstrap_pid = int(
                            json.loads(
                                ready_file.read_text(encoding="ascii")
                            )["watchdog_pid"]
                        )
                    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                        raise AgentError(
                            "process watchdog ready record cannot recover the "
                            "suppressed PID"
                        ) from error
                    _FALLBACK_WATCHDOG_COMMAND_LINES[bootstrap_pid] = command
                    break
                time.sleep(0.1)
            else:
                try:
                    bootstrap_process = subprocess.Popen(
                        arguments,
                        close_fds=True,
                        creationflags=(
                            subprocess.CREATE_NEW_PROCESS_GROUP
                            | subprocess.DETACHED_PROCESS
                        ),
                    )
                except OSError as error:
                    raise UnsafeCleanupError(
                        "process watchdog launch produced neither PID nor ready "
                        f"proof, and fallback launch failed: {error}"
                    ) from error
                bootstrap_pid = int(bootstrap_process.pid)
                _FALLBACK_WATCHDOG_COMMAND_LINES[bootstrap_pid] = command
                _FALLBACK_WATCHDOG_PROCESSES[bootstrap_pid] = bootstrap_process
    error_file = record_file.with_suffix(".watchdog_error")
    actual_pid: int | None = None
    creation_date = ""
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if error_file.is_file():
                detail = error_file.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                raise AgentError(f"process watchdog bootstrap failed: {detail}")
            if ready_file.is_file():
                ready = json.loads(ready_file.read_text(encoding="ascii"))
                if set(ready) != {
                    "nonce",
                    "parent_pid",
                    "parent_executable",
                    "parent_creation_date",
                    "watchdog_pid",
                }:
                    raise AgentError(
                        f"process watchdog ready fields differ: {ready!r}"
                    )
                if (
                    ready.get("nonce") != nonce
                    or ready.get("parent_pid") != parent_pid
                    or not _same_executable(
                        ready.get("parent_executable"), parent_executable
                    )
                    or ready.get("parent_creation_date") != parent_creation_date
                ):
                    raise AgentError(
                        f"process watchdog ready identity differs: {ready!r}"
                    )
                actual_pid = int(ready["watchdog_pid"])
                _rebind_fallback_watchdog(bootstrap_pid, actual_pid)
                identity = _process_identity(actual_pid)
                if identity is None:
                    raise AgentError(
                        f"process watchdog PID {actual_pid} disappeared after ready"
                    )
                creation_date = str(identity["creation_date"])
                if not _authenticated_watchdog_running(
                    actual_pid, creation_date, parent_pid, nonce
                ):
                    raise AgentError(
                        f"process watchdog identity differs: {identity!r}"
                    )
                return actual_pid, creation_date
            time.sleep(0.1)
        raise AgentError(
            f"process watchdog bootstrap PID {bootstrap_pid} did not become ready"
        )
    except Exception as bootstrap_error:
        candidate = actual_pid if actual_pid is not None else bootstrap_pid
        cleanup_error: Exception | None = None
        try:
            identity = _process_identity(candidate)
            if identity is not None:
                candidate_creation = str(identity["creation_date"])
                _stop_authenticated_watchdog(
                    candidate, candidate_creation, parent_pid, nonce
                )
        except Exception as error:
            cleanup_error = error
        if cleanup_error is None:
            ready_file.unlink(missing_ok=True)
        else:
            try:
                error_file.write_text(
                    f"bootstrap-cleanup:{cleanup_error}\n", encoding="utf-8"
                )
            except OSError:
                pass
        detail = (
            f"; watchdog cleanup unproven: {cleanup_error}"
            if cleanup_error is not None
            else ""
        )
        raise UnsafeCleanupError(
            f"process watchdog bootstrap failed: {bootstrap_error}{detail}"
        ) from bootstrap_error


def _create_kill_on_close_job(name: str | None = None) -> object:
    import win32api
    import win32job
    import winerror

    win32api.SetLastError(0)
    job = win32job.CreateJobObject(None, name or "")
    create_error = win32api.GetLastError()
    if name and create_error == winerror.ERROR_ALREADY_EXISTS:
        win32api.CloseHandle(job)
        raise AgentError(f"named Job already exists: {name}")
    try:
        limits = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation
        )
        limits["BasicLimitInformation"]["LimitFlags"] |= (
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        win32job.SetInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation, limits
        )
    except Exception:
        win32api.CloseHandle(job)
        raise
    return job


def _create_suspended_process(
    command: list[str],
    working_directory: Path,
    environment: Mapping[str, str] | None = None,
) -> _SuspendedWindowsProcess:
    import win32process

    startup = win32process.STARTUPINFO()
    creation_flags = win32process.CREATE_SUSPENDED
    if environment is not None:
        creation_flags |= getattr(
            win32process, "CREATE_UNICODE_ENVIRONMENT", 0x00000400
        )
    process_handle, thread_handle, pid, _thread_id = win32process.CreateProcess(
        command[0],
        subprocess.list2cmdline(command),
        None,
        None,
        False,
        creation_flags,
        None if environment is None else dict(environment),
        str(working_directory),
        startup,
    )
    return _SuspendedWindowsProcess(
        process_handle, thread_handle, int(pid), command
    )


def _native_bridge_child_environment(
    config: NativeBridgeLaunchConfig,
    parent_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build the inherited environment read by the injected bridge DLL."""
    source = os.environ if parent_environment is None else parent_environment
    result = {
        key: value
        for key, value in source.items()
        if key.casefold()
        not in {
            NATIVE_BRIDGE_MODE_ENV.casefold(),
            NATIVE_BRIDGE_PIPE_ENV.casefold(),
        }
    }
    result[NATIVE_BRIDGE_MODE_ENV] = config.mode
    result[NATIVE_BRIDGE_PIPE_ENV] = config.pipe_name
    return result


def _ck3_launch_command(
    spec: EnvironmentSpec,
    *,
    continue_last_save: bool = False,
    load_save_name: str | None = None,
) -> list[str]:
    if continue_last_save and load_save_name is not None:
        raise AgentError(
            "CK3 launch cannot combine -continuelastsave with -loadsave"
        )
    if load_save_name is not None:
        if (
            not isinstance(load_save_name, str)
            or not load_save_name
            or Path(load_save_name).name != load_save_name
            or Path(load_save_name).suffix
            or any(
                character in load_save_name for character in ("/", "\\", "\0")
            )
        ):
            raise AgentError(
                "CK3 -loadsave requires one save basename without a path or "
                "extension"
            )
    command = [
        str(spec.game_exe),
        "-gdpr-compliant",
        f"-userdir={spec.profile_dir}",
    ]
    if continue_last_save:
        command.append("-continuelastsave")
    elif load_save_name is not None:
        command.append(f"-loadsave={load_save_name}")
    return command


def _inject_native_bridge(
    process: _SuspendedWindowsProcess,
    config: NativeBridgeLaunchConfig,
) -> None:
    """Run the existing injector CLI while CK3's primary thread is suspended."""
    command = [
        str(config.injector_path),
        str(process.pid),
        str(config.dll_path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AgentError(
            f"native bridge injector could not complete: {error}"
        ) from error
    if result.returncode != 0:
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        raise AgentError(
            "native bridge injector failed before CK3 resume: "
            f"rc={result.returncode}, stdout={stdout!r}, stderr={stderr!r}"
        )


def _resume_with_native_bridge(
    process: _SuspendedWindowsProcess,
    config: NativeBridgeLaunchConfig | None,
) -> None:
    if config is not None:
        _inject_native_bridge(process, config)
    process.resume()


def _assign_process_to_job(
    job_handle: object, process: _SuspendedWindowsProcess
) -> None:
    import win32job

    win32job.AssignProcessToJobObject(job_handle, process._process_handle)


def _wait_process_identity(pid: int, timeout: float = 5) -> dict[str, object] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        identity = _process_identity(pid)
        if identity is not None:
            return identity
        time.sleep(0.05)
    return None


def _job_active_processes(job_handle: object | None) -> int | None:
    if job_handle is None:
        return None
    import win32job

    details = win32job.QueryInformationJobObject(
        job_handle, win32job.JobObjectBasicAccountingInformation
    )
    return int(details["ActiveProcesses"])


def _terminate_job(job_handle: object) -> None:
    import win32job

    win32job.TerminateJobObject(job_handle, 1)


def _close_job(job_handle: object | None) -> None:
    if job_handle is None:
        return
    import win32api

    win32api.CloseHandle(job_handle)


def _clear_isolated_runtime_logs(spec: EnvironmentSpec) -> tuple[int, list[str]]:
    log_root = (spec.profile_dir / "logs").resolve()
    if not is_relative_to(log_root, spec.profile_dir.resolve()):
        raise AgentError(f"isolated log directory escaped profile: {log_root}")
    log_root.mkdir(parents=True, exist_ok=True)
    cleared: list[str] = []
    for name in ("debug.log", "error.log", "gui_warnings.log"):
        path = log_root / name
        if path.exists():
            path.unlink()
            cleared.append(name)
    epoch = time.time_ns()
    for name in ("debug.log", "error.log", "gui_warnings.log"):
        if (log_root / name).exists():
            raise AgentError(f"runtime log survived prelaunch clear: {name}")
    return epoch, cleared


def launch(
    spec: EnvironmentSpec,
    *,
    watchdog_final_evidence: Path | None = None,
    job_name: str | None = None,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    continue_last_save: bool = False,
    load_save_name: str | None = None,
    verify_prepared_profile: bool = True,
) -> SessionHandle:
    native_bridge = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if verify_prepared_profile:
        verify_profile(spec)
    if job_name is not None and not re.fullmatch(
        r"XarAutoplayer-Crash-[0-9a-f]{32}", job_name
    ):
        raise AgentError(f"invalid crash Job name: {job_name!r}")
    if ck3_processes():
        raise AgentError("refusing to launch while any ck3.exe is already running")
    command = _ck3_launch_command(
        spec,
        continue_last_save=continue_last_save,
        load_save_name=load_save_name,
    )
    child_environment = (
        _native_bridge_child_environment(native_bridge)
        if native_bridge is not None
        else None
    )
    control = spec.state_dir / "control"
    nonce = uuid.uuid4().hex
    pid_file = control / "ck3.json"
    ready_file = control / f"watchdog-{nonce}.ready.json"
    unsafe_marker = control / "unsafe-cleanup.json"
    if unsafe_marker.is_file():
        raise AgentError(
            f"an unresolved unsafe cleanup marker blocks launch: {unsafe_marker}"
        )
    if watchdog_final_evidence is not None:
        watchdog_final_evidence = watchdog_final_evidence.resolve()
        runs_root = (spec.state_dir / "runs").resolve()
        parents = watchdog_final_evidence.parents
        if (
            len(parents) < 3
            or parents[0].name != "artifacts"
            or parents[2] != runs_root
            or not parents[1].is_dir()
        ):
            raise AgentError(
                "watchdog final evidence must be a new file under "
                "state/runs/<run-id>/artifacts"
            )
        temporary = watchdog_final_evidence.with_name(
            watchdog_final_evidence.name + ".tmp"
        )
        if watchdog_final_evidence.exists() or temporary.exists():
            raise AgentError("watchdog final evidence target already exists")
    for path in (
        pid_file,
        pid_file.with_suffix(".watchdog_error"),
        ready_file,
    ):
        path.unlink(missing_ok=True)
    log_epoch_ns, cleared_logs = _clear_isolated_runtime_logs(spec)
    parent_identity = _process_identity(os.getpid())
    if (
        parent_identity is None
        or str(parent_identity["name"]).casefold()
        not in {"python.exe", "pythonw.exe"}
        or not Path(str(parent_identity["executable"])).is_file()
    ):
        raise AgentError(
            f"supervisor process identity could not be authenticated: {parent_identity!r}"
        )
    try:
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": None,
                "reason": "watchdog bootstrap requested; CK3 launch not yet started",
            },
        )
    except Exception as error:
        raise AgentError(f"could not establish unsafe cleanup marker: {error}") from error
    try:
        watchdog_pid, watchdog_creation_date = _start_process_watchdog(
            os.getpid(),
            Path(str(parent_identity["executable"])),
            str(parent_identity["creation_date"]),
            nonce,
            ready_file,
            pid_file,
            unsafe_marker,
            spec.game_exe,
            watchdog_final_evidence,
        )
    except Exception as error:
        raise UnsafeCleanupError(
            f"watchdog bootstrap failed; unsafe marker retained: {error}"
        ) from error
    try:
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": None,
                "reason": "watchdog ready; CK3 launch not yet started",
            },
        )
    except Exception as error:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception as cleanup_error:
            raise UnsafeCleanupError(
                "unsafe marker update and watchdog cleanup both failed: "
                f"{error}; cleanup={cleanup_error}"
            ) from cleanup_error
        ready_file.unlink(missing_ok=True)
        unsafe_marker.unlink(missing_ok=True)
        raise AgentError(f"could not update unsafe cleanup marker: {error}") from error
    # Close the remaining race after the ready handshake. The global launch
    # mutex prevents another agent state from reaching this point concurrently.
    try:
        appeared = ck3_processes()
    except Exception:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception:
            raise UnsafeCleanupError(
                "CK3 inventory and watchdog cleanup both became unverifiable"
            )
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        raise
    if appeared:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception as error:
            raise UnsafeCleanupError(
                f"CK3 appeared before launch and watchdog cleanup failed: {error}"
            ) from error
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        raise AgentError("ck3.exe appeared between preflight and launch")
    process: _SuspendedWindowsProcess | None = None
    job_handle: object | None = None
    try:
        job_handle = _create_kill_on_close_job(job_name)
        process = _create_suspended_process(
            command,
            spec.game_exe.parent,
            child_environment,
        )
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": process.pid,
                "reason": "suspended launch active; removed only after authenticated tree shutdown",
            },
        )
        _assign_process_to_job(job_handle, process)
        pinned_image = process.image_path()
        identity = _wait_process_identity(process.pid)
        if (
            identity is None
            or identity["name"].casefold() != "ck3.exe"
            or int(identity["parent_pid"]) != os.getpid()
            or not _same_executable(pinned_image, spec.game_exe)
            or (
                identity["executable"]
                and not _same_executable(identity["executable"], spec.game_exe)
            )
        ):
            raise AgentError(f"launched CK3 process identity differs: {identity!r}")
        record = {
            "format_version": 1,
            "nonce": nonce,
            "ck3_pid": process.pid,
            "parent_pid": os.getpid(),
            "executable": str(spec.game_exe.resolve()),
            "creation_date": identity["creation_date"],
        }
        write_json_atomic(pid_file, record)
        pre_resume_inventory = ck3_process_inventory()
        visible = pre_resume_inventory["processes"]
        if (
            len(visible) != 1
            or int(visible[0]["pid"]) != process.pid
            or int(visible[0]["parent_pid"]) != os.getpid()
            or str(visible[0]["name"]).casefold() != "ck3.exe"
            or not same_process_creation_time(
                visible[0].get("creation_date"), identity["creation_date"]
            )
            or (
                visible[0].get("executable")
                and not _same_executable(visible[0]["executable"], spec.game_exe)
            )
        ):
            raise AgentError(
                "pre-resume global CK3 inventory is not the exact suspended process: "
                f"{visible!r}"
            )
        _resume_with_native_bridge(process, native_bridge)
    except Exception as error:
        # A process that has not resumed cannot have spawned descendants. Once
        # resumed, assignment to the kill-on-close Job has already succeeded.
        if process is not None:
            try:
                process.terminate_exact()
                process.wait(timeout=20)
            except Exception:
                pass
        try:
            active = _job_active_processes(job_handle)
        except Exception:
            active = -1
        process_alive = process is not None and process.poll() is None
        no_tree_proof = (
            process_alive
            or active == -1
            or (process is not None and process.resumed and active != 0)
            or (process is not None and process.resumed and job_handle is None)
        )
        if no_tree_proof:
            raise UnsafeCleanupError(
                f"CK3 launch contract failed and its job is not empty: {error}"
            ) from error
        _close_job(job_handle)
        if process is not None:
            process.close()
        _stop_authenticated_watchdog(
            watchdog_pid, watchdog_creation_date, os.getpid(), nonce
        )
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        pid_file.unlink(missing_ok=True)
        raise AgentError(f"CK3 launch contract failed safely: {error}") from error
    return SessionHandle(
        process,
        pid_file,
        watchdog_pid,
        command,
        log_epoch_ns,
        cleared_logs,
        nonce,
        pid_file,
        ready_file,
        unsafe_marker,
        str(identity["creation_date"]),
        watchdog_creation_date,
        job_handle,
        pre_resume_inventory,
    )


def stop_tracked(
    handle: SessionHandle, require_running: bool = False
) -> dict[str, object]:
    """Stop the pinned CK3 Job and return the proof required for postflight."""
    errors: list[str] = []
    try:
        record = json.loads(handle.pid_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        record = None
        errors.append(f"tracked CK3 PID file is unavailable: {error}")
    expected_record = {
        "format_version": 1,
        "nonce": handle.nonce,
        "ck3_pid": handle.process.pid,
        "parent_pid": os.getpid(),
        "executable": handle.command[0],
        "creation_date": handle.ck3_creation_date,
    }
    if record is not None and record != expected_record:
        errors.append(f"tracked CK3 launch record changed: {record!r}")
    watchdog_state_before = _authenticated_watchdog_state(
        handle.watchdog_pid,
        handle.watchdog_creation_date,
        os.getpid(),
        handle.nonce,
    )
    if watchdog_state_before != "running":
        errors.append(
            f"process watchdog PID {handle.watchdog_pid} state before shutdown "
            f"was {watchdog_state_before}"
        )
    running = handle.process.poll() is None
    if require_running and not running:
        errors.append(f"CK3 PID {handle.process.pid} exited before shutdown")
    try:
        active_before_termination = _job_active_processes(handle.job_handle)
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"tracked CK3 job could not be queried before termination: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"tracked CK3 job could not be queried; watchdog retained: {error}"
        ) from error
    if active_before_termination:
        try:
            _terminate_job(handle.job_handle)
        except Exception as error:
            errors.append(
                f"TerminateJobObject failed for tracked CK3 tree: {error}"
            )
    try:
        handle.process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        errors.append(f"tracked CK3 PID {handle.process.pid} did not exit")
    try:
        deadline = time.monotonic() + 20
        active = _job_active_processes(handle.job_handle)
        while active != 0 and time.monotonic() < deadline:
            time.sleep(0.1)
            active = _job_active_processes(handle.job_handle)
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"tracked CK3 job could not be queried: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"tracked CK3 job could not be queried; watchdog retained: {error}"
        ) from error
    root_process_exited = handle.process.poll() is not None
    tree_gone = root_process_exited and active == 0
    if not tree_gone:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": "tracked CK3 job did not become empty",
            },
        )
        raise UnsafeCleanupError(
            "; ".join(
                [
                    *errors,
                    f"tracked CK3 PID {handle.process.pid} or its job remains alive",
                    "detached authenticated watchdog retained",
                ]
            )
        )
    try:
        final_inventory = ck3_process_inventory()
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"final global CK3 inventory is unknown: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"final global CK3 inventory is unknown; watchdog retained: {error}"
        ) from error
    if final_inventory["processes"]:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": "a CK3 process remains after the tracked Job became empty",
            },
        )
        raise UnsafeCleanupError(
            "a CK3 process remains after the tracked Job became empty; "
            "watchdog retained"
        )
    try:
        _close_job(handle.job_handle)
        handle.job_handle = None
        if isinstance(handle.process, _SuspendedWindowsProcess):
            handle.process.close()
        _stop_authenticated_watchdog(
            handle.watchdog_pid,
            handle.watchdog_creation_date,
            os.getpid(),
            handle.nonce,
        )
        deadline = time.monotonic() + 10
        while True:
            watchdog_state_after = _authenticated_watchdog_state(
                handle.watchdog_pid,
                handle.watchdog_creation_date,
                os.getpid(),
                handle.nonce,
            )
            if watchdog_state_after != "running" or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        if watchdog_state_after != "absent":
            raise UnsafeCleanupError(
                f"watchdog exit state is {watchdog_state_after}, not absent"
            )
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"shutdown control cleanup is unproven: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"shutdown control cleanup is unproven: {error}"
        ) from error
    watchdog_error = handle.pid_file.with_suffix(".watchdog_error")
    if watchdog_error.is_file():
        try:
            detail = watchdog_error.read_text(encoding="ascii").strip()
        except OSError as error:
            detail = str(error)
        errors.append(f"process watchdog reported failure: {detail}")
        watchdog_error.unlink(missing_ok=True)
    try:
        handle.pid_file.unlink(missing_ok=True)
        handle.ready_file.unlink(missing_ok=True)
        watchdog_error.unlink(missing_ok=True)
        # The marker is deliberately last: its absence authorizes a new launch.
        handle.unsafe_marker.unlink(missing_ok=True)
    except OSError as error:
        raise UnsafeCleanupError(
            f"shutdown control files could not be removed: {error}"
        ) from error
    control_absent = {
        str(path): not path.exists()
        for path in (
            handle.pid_file,
            handle.ready_file,
            watchdog_error,
            handle.unsafe_marker,
        )
    }
    if not all(control_absent.values()):
        raise UnsafeCleanupError(
            f"shutdown control files remain after cleanup: {control_absent!r}"
        )
    cleanup_proven = (
        root_process_exited
        and active == 0
        and not final_inventory["processes"]
        and watchdog_state_after == "absent"
        and all(control_absent.values())
    )
    if not cleanup_proven:
        raise UnsafeCleanupError("shutdown proof conjunction is false")
    return {
        "nonce": handle.nonce,
        "ck3_pid": handle.process.pid,
        "ck3_creation_date": handle.ck3_creation_date,
        "ck3_exit_code": handle.process.returncode,
        "job_active_processes_before_termination": active_before_termination,
        "job_active_processes_final": active,
        "tree_gone": True,
        "cleanup_proven": cleanup_proven,
        "final_ck3_inventory": final_inventory,
        "watchdog_pid": handle.watchdog_pid,
        "watchdog_creation_date": handle.watchdog_creation_date,
        "watchdog_state_before": watchdog_state_before,
        "watchdog_state_after": watchdog_state_after,
        "control_files_absent": control_absent,
        "contract_errors": errors,
        "ok": not errors,
    }


def _window_for_pid(pid: int) -> tuple[int, tuple[int, int, int, int]] | None:
    import win32gui
    import win32process

    found: list[tuple[int, tuple[int, int, int, int]]] = []

    def callback(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
        if window_pid != pid:
            return
        rect = win32gui.GetWindowRect(hwnd)
        if rect[2] > rect[0] and rect[3] > rect[1]:
            found.append((hwnd, rect))

    win32gui.EnumWindows(callback, None)
    if not found:
        return None
    return max(found, key=lambda item: (item[1][2] - item[1][0]) * (item[1][3] - item[1][1]))


def _focus_window(hwnd: int) -> None:
    import ctypes
    import pyautogui
    import win32api
    import win32con
    import win32gui
    import win32process

    pyautogui.FAILSAFE = True
    if win32gui.GetForegroundWindow() == hwnd:
        return
    user32 = ctypes.windll.user32
    last_error: Exception | None = None
    for _ in range(3):
        foreground = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        foreground_thread = (
            win32process.GetWindowThreadProcessId(foreground)[0] if foreground else 0
        )
        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        attached: list[int] = []
        try:
            for thread in {foreground_thread, target_thread}:
                if thread and thread != current_thread:
                    if user32.AttachThreadInput(current_thread, thread, True):
                        attached.append(thread)
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(hwnd)
            pyautogui.keyDown("alt")
            try:
                win32gui.SetForegroundWindow(hwnd)
            finally:
                pyautogui.keyUp("alt")
        except Exception as error:
            last_error = error
        finally:
            for thread in reversed(attached):
                user32.AttachThreadInput(current_thread, thread, False)
        if win32gui.GetForegroundWindow() == hwnd:
            return
        time.sleep(0.2)
    active = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(active) if active else ""
    detail = f": {last_error}" if last_error else ""
    raise AgentError(
        f"CK3 window could not obtain foreground; active={title!r}{detail}"
    )


def _region_bbox(size: tuple[int, int], region: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    width, height = size
    left, top, right, bottom = region
    return (
        int(width * left),
        int(height * top),
        int(width * right),
        int(height * bottom),
    )


def _ocr_items(image: object, region: tuple[float, float, float, float]) -> list[dict[str, object]]:
    import numpy as np
    from .vision.ocr import rapidocr_engine

    crop_box = _region_bbox(image.size, region)
    result, _ = rapidocr_engine()(np.asarray(image.crop(crop_box)))
    found: list[dict[str, object]] = []
    for box, text, score in result or []:
        score = float(score)
        if not text or score < 0.45:
            continue
        xs = [int(point[0] + crop_box[0]) for point in box]
        ys = [int(point[1] + crop_box[1]) for point in box]
        found.append(
            {
                "text": text.strip(),
                "score": round(score, 4),
                "center": [int(sum(xs) / len(xs)), int(sum(ys) / len(ys))],
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
            }
        )
    return found


def normalize_ocr_text(value: object) -> str:
    """Return the canonical text used by live and replay OCR contracts."""
    normalized = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", "", normalized)


def unique_exact_ocr_match(
    items: object, target: str
) -> dict[str, object] | None:
    """Return one exact canonical OCR match, rejecting zero or duplicates."""
    if not isinstance(items, list):
        return None
    normalized_target = normalize_ocr_text(target)
    matches = [
        item
        for item in items
        if isinstance(item, dict)
        and "text" in item
        and normalize_ocr_text(item["text"]) == normalized_target
    ]
    return matches[0] if len(matches) == 1 else None


def wait_for_main_menu(
    handle: SessionHandle, artifacts: Path, timeout_seconds: float = 180
) -> dict[str, object]:
    from PIL import ImageGrab

    deadline = time.monotonic() + timeout_seconds
    target = "新游戏"
    stable_evidence: list[
        tuple[object, list[dict[str, object]], list[int], str, float, int]
    ] = []
    capture_sequence = 0
    last_image = None
    last_items: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            raise AgentError(
                f"CK3 PID {handle.process.pid} exited during boot: "
                f"rc={handle.process.returncode}"
            )
        window = _window_for_pid(handle.process.pid)
        if window is None:
            time.sleep(1)
            continue
        hwnd, rect = window
        width, height = rect[2] - rect[0], rect[3] - rect[1]
        if (width, height) != EXPECTED_RESOLUTION:
            raise AgentError(
                f"CK3 window must be 2560x1440, got {width}x{height}: {rect}"
            )
        _focus_window(hwnd)
        last_image = ImageGrab.grab(bbox=rect, all_screens=True)
        capture_sequence += 1
        captured_at = utc_now()
        captured_monotonic = time.monotonic()
        last_items = _ocr_items(last_image, MAIN_MENU_REGION)
        if unique_exact_ocr_match(last_items, target) is not None:
            stable_evidence.append(
                (
                    last_image,
                    last_items,
                    list(rect),
                    captured_at,
                    captured_monotonic,
                    capture_sequence,
                )
            )
            if len(stable_evidence) == 2:
                artifacts.mkdir(parents=True, exist_ok=True)
                (
                    first_image,
                    first_items,
                    first_rect,
                    first_captured_at,
                    first_captured_monotonic,
                    first_sequence,
                ) = stable_evidence[0]
                (
                    second_image,
                    second_items,
                    second_rect,
                    second_captured_at,
                    second_captured_monotonic,
                    second_sequence,
                ) = stable_evidence[1]
                first_screenshot = artifacts / "main-menu-frame-1.png"
                first_ocr = artifacts / "main-menu-frame-1-ocr.json"
                screenshot = artifacts / "main-menu.png"
                crop = artifacts / "main-menu-crop.png"
                ocr_path = artifacts / "main-menu-ocr.json"
                first_image.save(first_screenshot)
                write_json_atomic(first_ocr, first_items)
                second_image.save(screenshot)
                second_image.crop(
                    _region_bbox(second_image.size, MAIN_MENU_REGION)
                ).save(crop)
                write_json_atomic(ocr_path, second_items)
                frame_evidence = [
                    {
                        "frame": 1,
                        "capture_sequence": first_sequence,
                        "captured_at": first_captured_at,
                        "captured_monotonic": first_captured_monotonic,
                        "window_rect": first_rect,
                        "screenshot": str(first_screenshot),
                        "screenshot_sha256": _file_sha256(first_screenshot),
                        "ocr": str(first_ocr),
                        "ocr_sha256": _file_sha256(first_ocr),
                        "exact_match_count": 1,
                    },
                    {
                        "frame": 2,
                        "capture_sequence": second_sequence,
                        "captured_at": second_captured_at,
                        "captured_monotonic": second_captured_monotonic,
                        "window_rect": second_rect,
                        "screenshot": str(screenshot),
                        "screenshot_sha256": _file_sha256(screenshot),
                        "ocr": str(ocr_path),
                        "ocr_sha256": _file_sha256(ocr_path),
                        "exact_match_count": 1,
                    },
                ]
                return {
                    "target": target,
                    "target_normalized": normalize_ocr_text(target),
                    "stable_frames": len(frame_evidence),
                    "stable_frame_evidence": frame_evidence,
                    "window_rect": second_rect,
                    "screenshot": str(screenshot),
                    "screenshot_sha256": _file_sha256(screenshot),
                    "ocr": str(ocr_path),
                    "ocr_sha256": _file_sha256(ocr_path),
                }
        else:
            stable_evidence.clear()
        time.sleep(0.75)
    artifacts.mkdir(parents=True, exist_ok=True)
    if last_image is not None:
        last_image.save(artifacts / "main-menu-timeout.png")
        write_json_atomic(artifacts / "main-menu-timeout-ocr.json", last_items)
    raise AgentError("OCR timeout waiting for the visible 新游戏 main-menu control")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_runtime_attestation(
    text: str,
    profile_dir: Path,
    production_dir: Path,
    game_dir: Path | None = None,
    *,
    allowed_dlc_mounts: object | None = None,
) -> dict[str, object]:
    markers = list(re.finditer(r"Log system initialized", text))
    if len(markers) != 1:
        raise AgentError(
            "fresh debug.log must contain exactly one Log system initialized "
            f"marker, got {len(markers)}"
        )
    session = text[markers[0].start() :]
    enabled_matches = list(
        re.finditer(
            r"(?m)^([^\r\n|]+)\|(mod/[^\r\n|]+)\|Enabled\s*$", session
        )
    )
    enabled = [(match.group(1), match.group(2)) for match in enabled_matches]
    expected = [(EXPECTED_MOD_NAME, OUTER_DESCRIPTOR_REF)]
    if enabled != expected:
        raise AgentError(
            "runtime enabled-mod inventory is not the exact singleton: "
            f"actual={enabled!r}, expected={expected!r}"
        )
    content_root = (profile_dir / "mod-content").resolve()
    if allowed_dlc_mounts is not None:
        if not isinstance(allowed_dlc_mounts, (list, tuple, set, frozenset)):
            raise AgentError("runtime DLC mount allowlist is malformed")
        allowed_dlc_mount_paths = {Path(str(path)).resolve() for path in allowed_dlc_mounts}
    else:
        allowed_dlc_mount_paths = (
            {
                descriptor.parent.resolve()
                for descriptor in (game_dir / "game" / "dlc").glob("*/*.dlc")
            }
            if game_dir
            else set()
        )
    isolated_mounts: list[Path] = []
    dlc_mounts: list[Path] = []
    unknown_mounts: list[Path] = []
    mount_matches = list(
        re.finditer(r"(?m)^.*Mounted Data:\s*([^\r\n]+?)\s*$", session)
    )
    for match in mount_matches:
        path = Path(match.group(1).strip()).resolve()
        if is_relative_to(path, content_root):
            isolated_mounts.append(path)
        elif path in allowed_dlc_mount_paths:
            dlc_mounts.append(path)
        else:
            unknown_mounts.append(path)
    expected_mounts = [production_dir.resolve()]
    if isolated_mounts != expected_mounts:
        raise AgentError(
            "runtime isolated mount inventory differs: "
            f"actual={[str(path) for path in isolated_mounts]!r}, "
            f"expected={[str(path) for path in expected_mounts]!r}"
        )
    if unknown_mounts:
        raise AgentError(
            "runtime contains an unclassified non-DLC mount: "
            + ", ".join(str(path) for path in unknown_mounts)
        )
    return {
        "enabled_mods": [
            {"name": name, "descriptor": descriptor} for name, descriptor in enabled
        ],
        "isolated_mod_mounts": [str(path) for path in isolated_mounts],
        "runtime_dlc_mounts": [str(path) for path in dlc_mounts],
        "unclassified_mounts": [],
        "evidence_lines": [
            *(match.group(0).rstrip("\r\n") for match in enabled_matches),
            *(match.group(0).rstrip("\r\n") for match in mount_matches),
        ],
        "session_marker_count": 1,
        "source": "fresh non-debug boot log, reduced to load attestation only",
        "policy_boundary": "not available to gameplay perception or strategy",
    }


def wait_for_runtime_attestation(
    spec: EnvironmentSpec, handle: SessionHandle, timeout_seconds: float = 30
) -> dict[str, object]:
    path = spec.profile_dir / "logs" / "debug.log"
    deadline = time.monotonic() + timeout_seconds
    last_error: AgentError | None = None
    while time.monotonic() < deadline:
        try:
            raw = path.read_bytes()
            stat = path.stat()
            if stat.st_mtime_ns < handle.log_epoch_ns:
                raise AgentError(
                    "debug.log predates the prelaunch log epoch and is stale"
                )
            text = raw.decode("utf-8", errors="ignore")
            result = parse_runtime_attestation(
                text, spec.profile_dir, spec.production_dir, spec.game_dir
            )
            result["debug_log"] = {
                "path": str(path),
                "captured_prefix_size": len(raw),
                "captured_prefix_sha256": hashlib.sha256(raw).hexdigest(),
                "file_size_after_read": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "prelaunch_epoch_ns": handle.log_epoch_ns,
                "cleared_before_launch": handle.cleared_logs,
            }
            return result
        except OSError as error:
            last_error = AgentError(f"runtime load log unavailable: {error}")
        except AgentError as error:
            last_error = error
        time.sleep(0.5)
    raise last_error or AgentError("runtime load attestation timed out")


def analyze_engine_log_bytes(
    name: str,
    raw: bytes,
    *,
    expected_mod_name: str,
    production_path: Path,
) -> dict[str, object]:
    """Pure analysis shared by the live collector and offline replay."""
    text = raw.decode("utf-8", errors="replace")
    diagnostic_records = len(re.findall(r"(?m)^.*\[[EWI]\]\[", text))
    nonempty_lines = sum(1 for line in text.splitlines() if line.strip())
    needles = (
        "xar_",
        expected_mod_name.casefold(),
        str(production_path).casefold(),
    )
    hits: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        folded = line.casefold()
        if any(needle and needle in folded for needle in needles):
            hits.append(
                {
                    "log": name,
                    "line": line_number,
                    "sha256": hashlib.sha256(
                        line.encode("utf-8", errors="replace")
                    ).hexdigest(),
                }
            )
    return {
        "diagnostic_records": diagnostic_records,
        "nonempty_lines": nonempty_lines,
        "current_mod_diagnostic_hits": hits,
    }


def collect_engine_log_evidence(
    spec: EnvironmentSpec, handle: SessionHandle, artifacts: Path
) -> dict[str, object]:
    """Archive supervisor-only diagnostics without exposing them to policy input."""
    artifacts.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
        "zero_diagnostics": True,
        "current_mod_diagnostics": False,
        "current_mod_diagnostic_hits": [],
        "logs": {},
    }
    for name in ("error.log", "gui_warnings.log"):
        source = spec.profile_dir / "logs" / name
        if not source.is_file():
            result["logs"][name] = {"present": False, "diagnostic_records": 0}
            continue
        stat = source.stat()
        if stat.st_mtime_ns < handle.log_epoch_ns:
            raise AgentError(f"{name} predates this launch's fresh-log epoch")
        raw = source.read_bytes()
        destination = artifacts / f"supervisor-{name}"
        shutil.copy2(source, destination)
        analysis = analyze_engine_log_bytes(
            name,
            raw,
            expected_mod_name=EXPECTED_MOD_NAME,
            production_path=spec.production_dir,
        )
        record = {
            "present": True,
            "path": str(destination),
            "sha256": _file_sha256(destination),
            "size": len(raw),
            "mtime_ns": stat.st_mtime_ns,
            "diagnostic_records": analysis["diagnostic_records"],
            "nonempty_lines": analysis["nonempty_lines"],
        }
        result["logs"][name] = record
        if analysis["diagnostic_records"] or analysis["nonempty_lines"]:
            result["zero_diagnostics"] = False
        hits = analysis["current_mod_diagnostic_hits"]
        if hits:
            result["current_mod_diagnostics"] = True
            result["current_mod_diagnostic_hits"].extend(hits)
    return result


def smoke(spec: EnvironmentSpec, timeout_seconds: float = 180) -> dict[str, object]:
    """Hold exclusive ownership across preflight, boot, shutdown, and postflight."""
    ensure_state_path_safe(spec.state_dir)
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "smoke"):
            return _smoke_locked(spec, timeout_seconds)


def _smoke_locked(
    spec: EnvironmentSpec, timeout_seconds: float = 180
) -> dict[str, object]:
    """Boot to a visible main menu, attest one mod, and stop only our PID tree."""
    manifest = verify_profile(spec)
    doctor(spec, require_prepared=True)
    agent_git = manifest.get("agent_runtime", {}).get("git", {})
    if (
        not agent_git.get("all_files_tracked")
        or agent_git.get("dirty")
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(agent_git.get("selected_runtime_revision", ""))
        )
    ):
        raise AgentError(
            "infrastructure smoke requires a committed, clean selected agent runtime"
        )
    mod_git = mod_source_fingerprint()
    recorded_mod_git = manifest.get("mod", {}).get("source_provenance", {})
    if (
        mod_git.get("git_dirty")
        or not mod_git.get("all_release_files_tracked")
        or not re.fullmatch(r"[0-9a-f]{40}", str(mod_git.get("git_revision", "")))
        or mod_git.get("release_source_sha256")
        != recorded_mod_git.get("release_source_sha256")
    ):
        raise AgentError(
            "infrastructure smoke requires a committed, clean production mod source"
        )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    run_dir.mkdir(parents=True, exist_ok=False)
    log("snapshotting protected real profile, Steam userdata, and Workshop metadata")
    baseline = protected_snapshot()
    before_path = run_dir / "protected-before.json.gz"
    write_gzip_json_atomic(before_path, baseline)
    shutil.copy2(spec.manifest_path, run_dir / "environment.json")
    shutil.copy2(
        Path(str(manifest["mod"]["production_manifest"])),
        run_dir / "production.manifest.json",
    )
    append_event(
        events,
        {
            "kind": "smoke_started",
            "environment_sha256": manifest["environment_sha256"],
            "protected_storage_sha256": baseline["digest"],
            "protected_snapshot_sha256": _file_sha256(before_path),
        },
    )
    handle: SessionHandle | None = None
    report: dict[str, object] = {
        "format_version": 2,
        "run_id": run_id,
        "kind": "infrastructure_smoke",
        "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
        "clean_engine_boot_required": False,
        "started_at": utc_now(),
        "valid_score_episode": False,
        "environment_sha256": manifest["environment_sha256"],
        "run_dir": ".",
        "replay_trust_model": dict(NORMAL_REPLAY_TRUST_MODEL),
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(run_dir / "report.json", report)
    primary_error: Exception | None = None
    cleanup_proven = False
    try:
        log("launching tracked non-debug CK3 process")
        handle = launch(spec)
        live_identity = _process_identity(handle.process.pid)
        handle_trust = {
            "pinned_process_handle": (
                isinstance(handle.process, _SuspendedWindowsProcess)
                and handle.process._process_handle is not None
            ),
            "owned_kill_on_close_job": handle.job_handle is not None,
            "created_suspended_before_job_assignment": (
                isinstance(handle.process, _SuspendedWindowsProcess)
                and handle.process.resumed is True
            ),
            "pre_resume_identity_cross_validated": (
                handle.pre_resume_inventory is not None
            ),
        }
        if (
            not isinstance(live_identity, dict)
            or int(live_identity.get("pid", 0)) != handle.process.pid
            or int(live_identity.get("parent_pid", 0)) != os.getpid()
            or str(live_identity.get("name", "")).casefold() != "ck3.exe"
            or (
                live_identity.get("executable")
                and not _same_executable(
                    live_identity.get("executable"), spec.game_exe
                )
            )
            or not same_process_creation_time(
                live_identity.get("creation_date"), handle.ck3_creation_date
            )
            or not all(handle_trust.values())
        ):
            raise AgentError(
                "launched CK3 pinned identity/handle trust differs: "
                f"identity={live_identity!r}, trust={handle_trust!r}"
            )
        report["process"] = {
            "pid": handle.process.pid,
            "watchdog_pid": handle.watchdog_pid,
            "arguments": handle.command,
            "debug_mode": False,
            "fresh_log_epoch_ns": handle.log_epoch_ns,
            "prelaunch_logs_removed": handle.cleared_logs,
            "pre_resume_ck3_inventory": handle.pre_resume_inventory,
            "identity": {
                "pid": handle.process.pid,
                "parent_pid": os.getpid(),
                "name": "ck3.exe",
                "executable": str(spec.game_exe.resolve()),
                "creation_date": handle.ck3_creation_date,
            },
            "handle_trust": handle_trust,
        }
        append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
        log("waiting for two stable visible main-menu OCR frames")
        report["visual_attestation"] = _normalize_visual_references(
            wait_for_main_menu(handle, artifacts, timeout_seconds), run_dir
        )
        append_event(events, {"kind": "visible_main_menu_attested"})
        log("checking exact one-mod runtime inventory and isolated mount")
        report["load_attestation"] = wait_for_runtime_attestation(spec, handle)
        report["load_attestation"]["debug_log"] = _archive_normal_debug_prefix(
            spec,
            report["load_attestation"].get("debug_log"),
            artifacts,
            "runtime-debug-prefix.log",
        )
        write_json_atomic(
            artifacts / "supervisor-load-attestation.json",
            report["load_attestation"],
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
    except Exception as error:
        primary_error = error
    finally:
        if handle is not None:
            try:
                log(f"stopping only tracked CK3 PID {handle.process.pid}")
                shutdown = stop_tracked(
                    handle, require_running=primary_error is None
                )
                report["shutdown_attestation"] = shutdown
                cleanup_proven = shutdown.get("cleanup_proven") is True
                append_event(events, {"kind": "tracked_process_stopped", "pid": handle.process.pid})
                if not shutdown.get("ok"):
                    shutdown_error = AgentError(
                        "shutdown contract errors: "
                        + "; ".join(str(item) for item in shutdown["contract_errors"])
                    )
                    if primary_error is None:
                        primary_error = shutdown_error
                    else:
                        report["shutdown_error"] = str(shutdown_error)
            except Exception as stop_error:
                if primary_error is None:
                    primary_error = stop_error
                else:
                    report["shutdown_error"] = str(stop_error)

    try:
        remaining_inventory = ck3_process_inventory()
        report["post_shutdown_ck3_inventory"] = remaining_inventory
        remaining_ck3 = remaining_inventory["processes"]
    except Exception as inventory_error:
        remaining_ck3 = [f"inventory unknown: {inventory_error}"]
        report["post_shutdown_ck3_inventory_error"] = str(inventory_error)
        cleanup_proven = False
    if not cleanup_proven or remaining_ck3:
        alive_error = AgentError(
            "CK3 cleanup is not proven complete; protected postflight withheld"
            + (f"; running={remaining_ck3!r}" if remaining_ck3 else "")
        )
        report["unsafe_cleanup"] = True
        if primary_error is None:
            primary_error = alive_error
        else:
            report["postflight_error"] = str(alive_error)
    else:
        try:
            if handle is not None and "load_attestation" in report:
                final_load = wait_for_runtime_attestation(spec, handle, 2)
                for key in (
                    "enabled_mods",
                    "isolated_mod_mounts",
                    "runtime_dlc_mounts",
                    "unclassified_mounts",
                    "session_marker_count",
                ):
                    if final_load[key] != report["load_attestation"][key]:
                        raise AgentError(
                            f"post-exit runtime attestation changed for {key}"
                        )
                report["load_attestation"]["post_exit_revalidated"] = True
                report["load_attestation"]["post_exit_debug_log"] = (
                    _archive_normal_debug_prefix(
                        spec,
                        final_load["debug_log"],
                        artifacts,
                        "runtime-debug-post-exit.log",
                    )
                )
                write_json_atomic(
                    artifacts / "supervisor-load-attestation.json",
                    report["load_attestation"],
                )
            if handle is not None:
                report["engine_diagnostics"] = _normalize_diagnostic_references(
                    collect_engine_log_evidence(spec, handle, artifacts), run_dir
                )
            log("verifying protected stores return to the semantic baseline")
            after = verify_protected_unchanged(baseline)
            after_path = run_dir / "protected-after.json.gz"
            write_gzip_json_atomic(after_path, after)
            report["protected_storage"] = {
                "post_exit_matches_baseline": True,
                "continuous_quiet_seconds": 5,
                "runtime_write_absence_proven": False,
                "sha256": after["digest"],
                "before_snapshot": _normal_run_reference(before_path, run_dir),
                "before_snapshot_sha256": _file_sha256(before_path),
                "after_snapshot": _normal_run_reference(after_path, run_dir),
                "after_snapshot_sha256": _file_sha256(after_path),
                "allowed_volatile_before": baseline.get("allowed_volatile"),
                "allowed_volatile_after": after.get("allowed_volatile"),
            }
            verify_profile(spec)
            current_tree = snapshot_digest(tree_snapshot(spec.production_dir))
            if current_tree != manifest["mod"]["production_tree_sha256"]:
                raise AgentError("production projection changed during smoke")
            report["production_tree_unchanged"] = True
            if report.get("engine_diagnostics", {}).get(
                "current_mod_diagnostics"
            ):
                raise AgentError(
                    "fresh engine diagnostics reference the current production mod"
                )
        except Exception as postflight_error:
            if primary_error is None:
                primary_error = postflight_error
            else:
                report["postflight_error"] = str(postflight_error)

    report["finished_at"] = utc_now()
    primary_error = _finalize_normal_smoke_report(
        report, run_dir, events, primary_error
    )
    if primary_error is not None:
        raise AgentError(
            f"smoke failed; evidence retained at {run_dir}: {primary_error}"
        ) from primary_error
    # Re-open only the sealed run archive and execute the same public replay
    # used by later qualification.  No prepared-profile or production source
    # path is read by this call.
    validate_smoke_report(run_dir)
    clean = report.get("engine_diagnostics", {}).get("zero_diagnostics")
    log(
        "single-mod isolation smoke GREEN; "
        f"clean_engine_boot={clean}; evidence={run_dir}"
    )
    return report
