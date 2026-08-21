"""Explicit, fail-closed recovery of crash-probe control evidence.

This module does not upgrade a failed crash probe into a successful probe.  It
only proves that the processes named by one finalized RED crash archive are no
longer present, preserves the stale control files in a separate recovery
archive, and removes the unsafe marker as the final control-file operation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import uuid

from .crash_probe import (
    REPLAY_TRUST_MODEL,
    _canonical_job_name,
    _named_job_absent,
    _recorded_run_dir,
    _report_body_sha256,
    _verify_artifact_entry,
    _wait_global_ck3_quiet,
    validate_crash_report,
)
from .environment import (
    _contract_digest,
    EnvironmentSpec,
    ck3_process_inventory,
    ensure_state_path_safe,
    is_relative_to,
    sha256_file,
    snapshot_digest,
    write_bytes_atomic,
    write_json_atomic,
)
from .errors import AgentError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .runtime import (
    _process_identity,
    _same_executable,
    utc_now,
    validate_event_chain,
    validate_final_report_payload,
)


RUN_ID_PATTERN = re.compile(
    r"[0-9]{8}T[0-9]{6}Z-crash-[0-9a-f]{8}", re.ASCII
)
NONCE_PATTERN = re.compile(r"[0-9a-f]{32}", re.ASCII)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
IDENTITY_FIELDS = {
    "pid",
    "parent_pid",
    "name",
    "executable",
    "creation_date",
    "command_line",
}
LEGACY_WATCHDOG_RED_FIELDS = {
    "format_version",
    "run_id",
    "kind",
    "acceptance_claim",
    "valid_score_episode",
    "runtime_write_absence_proven",
    "replay_trust_model",
    "started_at",
    "environment_sha256",
    "run_dir",
    "artifacts",
    "finalized",
    "ok",
    "failure_path_ck3_inventory",
    "failure_path_watchdog_state",
    "subject_failure",
    "unsafe_cleanup",
    "finished_at",
    "error",
    "report_body_sha256",
    "final_event_sha256",
    "event_chain",
}
LEGACY_WATCHDOG_RED_ARTIFACTS = {
    "protected_before",
    "environment",
    "production_manifest",
    "owner",
    "handoff",
    "supervisor_ready",
    "supervisor_ack",
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
}


def _new_recovery_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-recovery-{uuid.uuid4().hex[:8]}"


def _load_object(path: Path, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise AgentError(f"{label} is missing or is not a regular file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AgentError(f"{label} root is not an object")
    return payload


def _require_exact_keys(
    payload: dict[str, object], expected: set[str], label: str
) -> None:
    if set(payload) != expected:
        raise AgentError(f"{label} fields differ")


def _require_nonce(value: object, label: str) -> str:
    nonce = str(value)
    if not NONCE_PATTERN.fullmatch(nonce):
        raise AgentError(f"{label} is not a lowercase 32-character nonce")
    return nonce


def _require_sha256(value: object, label: str) -> str:
    digest = str(value)
    if not SHA256_PATTERN.fullmatch(digest):
        raise AgentError(f"{label} is not a lowercase SHA-256 digest")
    return digest


def _require_absolute_path(value: object, expected: Path, label: str) -> None:
    raw = Path(str(value))
    if not raw.is_absolute() or raw.resolve() != expected.resolve():
        raise AgentError(f"{label} path differs")


def _source_run_dir(spec: EnvironmentSpec, run_id: str) -> Path:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise AgentError("recovery run ID is not a canonical crash run ID")
    runs_root = (spec.state_dir / "runs").resolve()
    if runs_root != spec.state_dir.resolve() / "runs":
        raise AgentError("crash runs root resolves outside the state directory")
    candidate = runs_root / run_id
    if candidate.is_symlink() or not candidate.is_dir():
        raise AgentError(f"crash run is missing or is not a regular directory: {run_id}")
    resolved = candidate.resolve()
    if resolved.parent != runs_root or resolved.name != run_id:
        raise AgentError("crash run path is noncanonical")
    report = resolved / "report.json"
    if report.is_symlink() or not report.is_file():
        raise AgentError("crash run report is missing or is not a regular file")
    return resolved


def _create_recovery_dir(spec: EnvironmentSpec) -> tuple[str, Path]:
    root = spec.state_dir.resolve() / "recoveries"
    if root.exists() and (root.is_symlink() or root.resolve() != root):
        raise AgentError("recovery archive root is noncanonical")
    root.mkdir(parents=True, exist_ok=True)
    for _ in range(8):
        recovery_id = _new_recovery_id()
        if not re.fullmatch(
            r"[0-9]{8}T[0-9]{6}Z-recovery-[0-9a-f]{8}", recovery_id
        ):
            raise AgentError("generated recovery ID is noncanonical")
        recovery_dir = root / recovery_id
        try:
            recovery_dir.mkdir()
        except FileExistsError:
            continue
        (recovery_dir / "artifacts").mkdir()
        return recovery_id, recovery_dir
    raise AgentError("could not allocate a unique recovery archive")


def _ensure_control_root_canonical(spec: EnvironmentSpec) -> Path:
    control = spec.state_dir.resolve() / "control"
    if control.exists() and (control.is_symlink() or control.resolve() != control):
        raise AgentError("control root is linked or resolves outside the state directory")
    return control


def _artifact_path(
    report: dict[str, object], run_dir: Path, label: str
) -> tuple[Path, str]:
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict):
        raise AgentError("source crash report lacks an artifact manifest")
    entry = artifacts.get(label)
    path = _verify_artifact_entry(entry, run_dir, label)
    assert isinstance(entry, dict)
    return path, _require_sha256(entry.get("sha256"), f"{label} artifact hash")


def _validate_legacy_watchdog_red(run_dir: Path) -> dict[str, object]:
    """Validate the one pre-diagnostic unsafe RED shape this command can recover.

    The later watchdog-final file is deliberately outside this legacy report's
    hash manifest.  This validator authenticates the old report and every
    artifact it did bind, but makes no historical cleanup claim from that file.
    """
    report = _load_object(run_dir / "report.json", "legacy crash report")
    if (
        set(report) != LEGACY_WATCHDOG_RED_FIELDS
        or report.get("format_version") != 1
        or report.get("kind") != "crash_recovery_smoke"
        or report.get("run_id") != run_dir.name
        or report.get("acceptance_claim")
        != "post_resume_supervisor_crash_recovery_only"
        or report.get("valid_score_episode") is not False
        or report.get("runtime_write_absence_proven") is not False
        or report.get("replay_trust_model") != REPLAY_TRUST_MODEL
        or report.get("finalized") is not True
        or report.get("ok") is not False
        or report.get("unsafe_cleanup") is not True
        or report.get("failure_path_watchdog_state") != "absent"
        or report.get("subject_failure")
        != "subject produced no structured failure detail"
        or report.get("error")
        != "crash cleanup watchdog exited 1, expected 0"
        or not SHA256_PATTERN.fullmatch(
            str(report.get("environment_sha256", ""))
        )
    ):
        raise AgentError("legacy watchdog RED report schema differs")
    if _recorded_run_dir(report) != run_dir.resolve():
        raise AgentError("legacy watchdog RED recorded run path differs")

    chain = validate_event_chain(run_dir / "events.jsonl")
    validate_final_report_payload(report, chain)
    if report.get("event_chain") != {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }:
        raise AgentError("legacy watchdog RED event summary differs")
    rows = [
        json.loads(line)
        for line in (run_dir / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    if [row.get("kind") for row in rows] != [
        "smoke_started",
        "crash_subject_armed",
        "supervisor_crash_injected",
        "smoke_finished",
    ]:
        raise AgentError("legacy watchdog RED event sequence differs")
    expected_body = _report_body_sha256(report)
    if (
        report.get("report_body_sha256") != expected_body
        or chain.get("tail", {}).get("report_body_sha256") != expected_body
    ):
        raise AgentError("legacy watchdog RED body is not event-bound")

    inventory = report.get("failure_path_ck3_inventory")
    _validate_empty_inventory(inventory, "legacy failure-path", stable=True)
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != LEGACY_WATCHDOG_RED_ARTIFACTS:
        raise AgentError("legacy watchdog RED artifact manifest differs")
    verified: dict[str, Path] = {
        label: _verify_artifact_entry(entry, run_dir, label)
        for label, entry in artifacts.items()
    }
    if (
        artifacts["protected_before"].get("path")
        != "protected-before.json.gz"
        or artifacts["environment"].get("path") != "environment.json"
        or artifacts["production_manifest"].get("path")
        != "production.manifest.json"
        or len(set(verified.values())) != len(verified)
    ):
        raise AgentError("legacy watchdog RED artifact paths differ")
    return report


def _validate_recovery_source_report(
    run_dir: Path,
) -> tuple[dict[str, object], str]:
    try:
        return validate_crash_report(run_dir), "current"
    except AgentError as current_error:
        try:
            legacy = _validate_legacy_watchdog_red(run_dir)
        except Exception:
            raise current_error
        return legacy, "legacy_watchdog_failure_red"


def _revalidate_source_archive(
    run_dir: Path,
    expected_report_sha256: str,
    expected_report: dict[str, object],
    expected_validation: str,
) -> None:
    report_path = run_dir / "report.json"
    if sha256_file(report_path) != expected_report_sha256:
        raise AgentError("source crash report changed during recovery")
    refreshed, validation = _validate_recovery_source_report(run_dir)
    if (
        validation != expected_validation
        or snapshot_digest(refreshed) != snapshot_digest(expected_report)
    ):
        raise AgentError("source crash archive semantics changed during recovery")


def _validate_environment(
    spec: EnvironmentSpec,
    report: dict[str, object],
    path: Path,
) -> dict[str, object]:
    environment = _load_object(path, "archived environment")
    digest = _require_sha256(
        environment.get("environment_sha256"), "archived environment digest"
    )
    if (
        digest != report.get("environment_sha256")
        or _contract_digest(environment) != digest
    ):
        raise AgentError("archived environment semantic digest differs")
    _require_absolute_path(environment.get("state_dir"), spec.state_dir, "environment state")
    _require_absolute_path(
        environment.get("profile_dir"), spec.profile_dir, "environment profile"
    )
    game = environment.get("game")
    if not isinstance(game, dict):
        raise AgentError("archived environment game identity is missing")
    _require_absolute_path(game.get("executable"), spec.game_exe, "environment CK3")
    expected_executable_hash = _require_sha256(
        game.get("executable_sha256"), "environment CK3 executable hash"
    )
    if not spec.game_exe.is_file() or sha256_file(spec.game_exe) != expected_executable_hash:
        raise AgentError("current CK3 executable differs from the crash environment")
    return environment


def _validate_identity(identity: object, label: str) -> dict[str, object]:
    if not isinstance(identity, dict) or set(identity) != IDENTITY_FIELDS:
        raise AgentError(f"{label} process identity fields differ")
    if (
        type(identity.get("pid")) is not int
        or int(identity["pid"]) <= 0
        or type(identity.get("parent_pid")) is not int
        or int(identity["parent_pid"]) < 0
    ):
        raise AgentError(f"{label} process PID fields differ")
    for field in ("name", "executable", "creation_date", "command_line"):
        if not isinstance(identity.get(field), str):
            raise AgentError(f"{label} process {field} differs")
    executable = str(identity["executable"])
    if not executable or not (Path(executable).is_absolute() or ntpath.isabs(executable)):
        raise AgentError(f"{label} executable is not absolute")
    if str(identity["name"]).casefold() != ntpath.basename(executable).casefold():
        raise AgentError(f"{label} name does not match its executable")
    if not str(identity["creation_date"]):
        raise AgentError(f"{label} creation date is empty")
    return identity


def _prove_identity_absent(
    recorded: dict[str, object], label: str
) -> dict[str, object]:
    try:
        current = _process_identity(int(recorded["pid"]))
    except Exception as error:
        raise AgentError(f"{label} process identity is unknown") from error
    if current is None:
        return {
            "pid": recorded["pid"],
            "creation_date": recorded["creation_date"],
            "status": "absent",
        }
    current = _validate_identity(current, f"current {label}")
    if current["creation_date"] != recorded["creation_date"]:
        return {
            "pid": recorded["pid"],
            "creation_date": recorded["creation_date"],
            "status": "absent_pid_reused",
            "current_creation_date": current["creation_date"],
        }
    fields_match = all(
        current[field] == recorded[field]
        for field in IDENTITY_FIELDS - {"executable"}
    ) and _same_executable(current["executable"], recorded["executable"])
    if not fields_match:
        raise AgentError(
            f"{label} PID and creation date match but its identity is ambiguous"
        )
    raise AgentError(f"{label} process is still running")


def _validate_handoff(
    spec: EnvironmentSpec,
    report: dict[str, object],
    run_dir: Path,
    handoff_path: Path,
) -> tuple[dict[str, object], str]:
    handoff = _load_object(handoff_path, "crash handoff")
    _require_exact_keys(
        handoff,
        {
            "format_version",
            "probe_nonce",
            "run_id",
            "state_dir",
            "game_dir",
            "timeout_seconds",
            "artifacts",
            "supervisor_ready",
            "supervisor_ack",
            "armed",
            "watchdog_final",
            "outer",
            "environment_sha256",
            "owner_sha256",
        },
        "crash handoff",
    )
    if handoff.get("format_version") != 1 or handoff.get("run_id") != run_dir.name:
        raise AgentError("crash handoff base identity differs")
    probe_nonce = _require_nonce(handoff.get("probe_nonce"), "crash probe nonce")
    if handoff.get("environment_sha256") != report.get("environment_sha256"):
        raise AgentError("crash handoff environment digest differs")
    _require_absolute_path(handoff.get("state_dir"), spec.state_dir, "handoff state")
    _require_absolute_path(handoff.get("game_dir"), spec.game_dir, "handoff game")
    artifacts = run_dir / "artifacts"
    expected_paths = {
        "artifacts": artifacts,
        "supervisor_ready": artifacts / f"supervisor-ready-{probe_nonce}.json",
        "supervisor_ack": artifacts / f"supervisor-ack-{probe_nonce}.json",
        "armed": artifacts / f"armed-{probe_nonce}.json",
        "watchdog_final": artifacts / f"watchdog-final-{probe_nonce}.json",
    }
    for field, expected in expected_paths.items():
        _require_absolute_path(handoff.get(field), expected, f"handoff {field}")
    if handoff_path.resolve() != artifacts / f"handoff-{probe_nonce}.json":
        raise AgentError("crash handoff artifact path is noncanonical")
    report_artifacts = report.get("artifacts")
    if not isinstance(report_artifacts, dict):
        raise AgentError("source crash artifact manifest is missing")
    owner = report_artifacts.get("owner")
    if not isinstance(owner, dict) or handoff.get("owner_sha256") != owner.get("sha256"):
        raise AgentError("crash handoff owner digest differs")
    timeout = handoff.get("timeout_seconds")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise AgentError("crash handoff timeout differs")
    _validate_identity(handoff.get("outer"), "outer verifier")
    return handoff, probe_nonce


def _validate_armed(
    spec: EnvironmentSpec,
    report: dict[str, object],
    run_dir: Path,
    armed_path: Path,
    probe_nonce: str,
) -> tuple[dict[str, object], str, dict[str, Path]]:
    armed = _load_object(armed_path, "armed crash evidence")
    _require_exact_keys(
        armed,
        {
            "format_version",
            "probe_nonce",
            "watchdog_nonce",
            "job_name",
            "job_active_processes",
            "process_resumed",
            "supervisor",
            "supervisor_bootstrap",
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
            "armed_monotonic",
        },
        "armed crash evidence",
    )
    if (
        armed.get("format_version") != 1
        or armed.get("probe_nonce") != probe_nonce
        or armed.get("environment_sha256") != report.get("environment_sha256")
        or armed.get("process_resumed") is not True
        or armed.get("job_active_processes") != 3
        or armed.get("job_name") != _canonical_job_name(probe_nonce)
    ):
        raise AgentError("armed crash base contract differs")
    watchdog_nonce = _require_nonce(armed.get("watchdog_nonce"), "watchdog nonce")
    for label in ("supervisor", "ck3", "sentinel_parent", "sentinel_child", "watchdog"):
        _validate_identity(armed.get(label), label)
    if armed.get("supervisor_bootstrap") is not None:
        _validate_identity(armed.get("supervisor_bootstrap"), "supervisor bootstrap")
    control = armed.get("control")
    if not isinstance(control, dict):
        raise AgentError("armed control contract is missing")
    _require_exact_keys(
        control,
        {
            "record",
            "ready",
            "unsafe_marker",
            "watchdog_error",
            "record_sha256",
            "ready_sha256",
            "unsafe_marker_sha256",
        },
        "armed control contract",
    )
    control_root = _ensure_control_root_canonical(spec)
    expected = {
        "record": control_root / "ck3.json",
        "ready": control_root / f"watchdog-{watchdog_nonce}.ready.json",
        "unsafe_marker": control_root / "unsafe-cleanup.json",
        "watchdog_error": control_root / "ck3.watchdog_error",
    }
    for label, path in expected.items():
        _require_absolute_path(control.get(label), path, f"armed {label}")
    report_artifacts = report.get("artifacts")
    assert isinstance(report_artifacts, dict)
    for label, hash_label in (
        ("record", "record_sha256"),
        ("ready", "ready_sha256"),
        ("unsafe_marker", "unsafe_marker_sha256"),
    ):
        digest = _require_sha256(control.get(hash_label), f"armed {label} hash")
        archive_label = f"control_before_{label}"
        archive_entry = report_artifacts.get(archive_label)
        if not isinstance(archive_entry, dict) or archive_entry.get("sha256") != digest:
            raise AgentError(f"armed {label} hash is not bound by the crash report")
        archive_path = _verify_artifact_entry(archive_entry, run_dir, archive_label)
        expected_archive = run_dir / "artifacts" / (
            f"control-before-{label}-{probe_nonce}.json"
        )
        if archive_path != expected_archive:
            raise AgentError(f"archived {label} control path is noncanonical")
    return armed, watchdog_nonce, expected


def _validate_current_controls(
    armed: dict[str, object],
    watchdog_nonce: str,
    paths: dict[str, Path],
    report: dict[str, object],
    run_dir: Path,
    probe_nonce: str,
) -> tuple[dict[str, str], bytes, dict[str, object]]:
    ready_files = sorted(paths["ready"].parent.glob("watchdog-*.ready.json"))
    if ready_files != [paths["ready"]]:
        raise AgentError("active watchdog ready-file inventory differs")
    for path in paths.values():
        temporary = path.with_name(path.name + ".tmp")
        if path.is_symlink() or not path.is_file() or temporary.exists():
            raise AgentError(
                "active control file is missing, linked, or has a temporary peer: "
                f"{path.name}"
            )

    control = armed["control"]
    assert isinstance(control, dict)
    hashes: dict[str, str] = {}
    for label in ("record", "ready", "unsafe_marker"):
        expected_hash = _require_sha256(control[f"{label}_sha256"], f"active {label} hash")
        if sha256_file(paths[label]) != expected_hash:
            raise AgentError(f"active {label} control hash differs")
        hashes[label] = expected_hash
        archive_path, archive_hash = _artifact_path(
            report, run_dir, f"control_before_{label}"
        )
        if archive_hash != expected_hash or archive_path.read_bytes() != paths[label].read_bytes():
            raise AgentError(f"active {label} bytes differ from archived control evidence")

    ck3 = armed["ck3"]
    supervisor = armed["supervisor"]
    watchdog = armed["watchdog"]
    assert isinstance(ck3, dict) and isinstance(supervisor, dict) and isinstance(watchdog, dict)
    record = _load_object(paths["record"], "active CK3 record")
    _require_exact_keys(
        record,
        {"format_version", "nonce", "ck3_pid", "parent_pid", "executable", "creation_date"},
        "active CK3 record",
    )
    if (
        record.get("format_version") != 1
        or record.get("nonce") != watchdog_nonce
        or record.get("ck3_pid") != ck3["pid"]
        or record.get("parent_pid") != supervisor["pid"]
        or record.get("creation_date") != ck3["creation_date"]
        or not _same_executable(record.get("executable"), ck3["executable"])
    ):
        raise AgentError("active CK3 record identity differs")
    ready = _load_object(paths["ready"], "active watchdog ready")
    _require_exact_keys(
        ready,
        {"nonce", "parent_pid", "parent_executable", "parent_creation_date", "watchdog_pid"},
        "active watchdog ready",
    )
    if (
        ready.get("nonce") != watchdog_nonce
        or ready.get("parent_pid") != supervisor["pid"]
        or ready.get("parent_creation_date") != supervisor["creation_date"]
        or ready.get("watchdog_pid") != watchdog["pid"]
        or not _same_executable(ready.get("parent_executable"), supervisor["executable"])
    ):
        raise AgentError("active watchdog ready identity differs")
    marker = _load_object(paths["unsafe_marker"], "active unsafe marker")
    _require_exact_keys(marker, {"nonce", "ck3_pid", "reason"}, "active unsafe marker")
    if (
        marker.get("nonce") != watchdog_nonce
        or marker.get("ck3_pid") != ck3["pid"]
        or not isinstance(marker.get("reason"), str)
        or not str(marker["reason"]).strip()
    ):
        raise AgentError("active unsafe marker identity differs")

    watchdog_final_path = run_dir / "artifacts" / f"watchdog-final-{probe_nonce}.json"
    final = _load_object(watchdog_final_path, "watchdog final evidence")
    _require_exact_keys(
        final,
        {
            "format_version",
            "nonce",
            "parent_pid",
            "ok",
            "stage",
            "authenticated_candidates",
            "errors",
        },
        "watchdog final evidence",
    )
    errors = final.get("errors")
    if (
        final.get("format_version") != 1
        or final.get("nonce") != watchdog_nonce
        or final.get("parent_pid") != supervisor["pid"]
        or final.get("ok") is not False
        or final.get("stage") != "cleanup"
        or final.get("authenticated_candidates") != [ck3["pid"]]
        or not isinstance(errors, list)
        or not errors
        or any(not isinstance(item, str) or not item for item in errors)
    ):
        raise AgentError("watchdog final failure contract differs")
    error_bytes = paths["watchdog_error"].read_bytes()
    expected_error = ";".join(errors)
    try:
        error_text = error_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AgentError("active watchdog error is not UTF-8") from error
    if error_text not in {expected_error + "\n", expected_error + "\r\n"}:
        raise AgentError("active watchdog error differs from final evidence")
    hashes["watchdog_error"] = sha256_file(paths["watchdog_error"])
    hashes["watchdog_final"] = sha256_file(watchdog_final_path)
    return hashes, paths["unsafe_marker"].read_bytes(), final


def _validate_empty_inventory(inventory: object, label: str, stable: bool) -> dict[str, object]:
    if not isinstance(inventory, dict):
        raise AgentError(f"{label} CK3 inventory is not an object")
    if (
        inventory.get("processes") != []
        or inventory.get("tasklist_pids") != []
        or inventory.get("wmi_pids") != []
    ):
        raise AgentError(f"{label} CK3 inventory is not empty")
    if stable and (
        not isinstance(inventory.get("continuous_empty_seconds"), (int, float))
        or isinstance(inventory.get("continuous_empty_seconds"), bool)
        or float(inventory["continuous_empty_seconds"]) < 5
        or type(inventory.get("poll_count")) is not int
        or int(inventory["poll_count"]) < 2
    ):
        raise AgentError("stable CK3 absence proof is too short")
    return inventory


def _cas_archive_control(
    source: Path,
    destination: Path,
    expected_sha256: str,
    expected_nonce: str | None,
) -> None:
    """Compare, move, and post-verify one control file without overwriting evidence."""
    if source.is_symlink() or not source.is_file() or destination.exists():
        raise AgentError(f"control CAS precondition failed: {source.name}")
    before = source.read_bytes()
    if hashlib.sha256(before).hexdigest() != expected_sha256:
        raise AgentError(f"control CAS hash changed: {source.name}")
    if expected_nonce is not None:
        payload = json.loads(before.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("nonce") != expected_nonce:
            raise AgentError(f"control CAS nonce changed: {source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    try:
        if (
            source.exists()
            or not destination.is_file()
            or sha256_file(destination) != expected_sha256
        ):
            raise AgentError(f"control CAS postcondition failed: {source.name}")
    except BaseException:
        if not source.exists() and destination.exists():
            os.replace(destination, source)
        raise


def _restore_controls(
    journal: list[tuple[str, Path, Path, str]],
) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for label, active, archived, expected_hash in reversed(journal):
        if not archived.exists():
            outcomes[label] = "archive_missing"
            continue
        if active.exists():
            outcomes[label] = "active_path_occupied"
            continue
        try:
            os.replace(archived, active)
            outcomes[label] = (
                "restored"
                if active.is_file() and sha256_file(active) == expected_hash
                else "restored_hash_unknown"
            )
        except OSError as error:
            outcomes[label] = f"restore_failed:{type(error).__name__}"
    return outcomes


def _finalize_failure_report(
    report_path: Path,
    report: dict[str, object],
    error: BaseException,
    restoration: dict[str, str],
) -> None:
    report["finished_at"] = utc_now()
    report["stage"] = "failed"
    report["error"] = f"{type(error).__name__}: {error}"
    report["restoration"] = restoration
    report["ok"] = False
    report["finalized"] = True
    report["report_body_sha256"] = snapshot_digest(
        {key: value for key, value in report.items() if key != "report_body_sha256"}
    )
    write_json_atomic(report_path, report)


def validate_recovery_report(recovery_dir: Path) -> dict[str, object]:
    """Read-only validation of a committed conditional recovery report."""
    recovery_dir = recovery_dir.resolve()
    report = _load_object(recovery_dir / "report.json", "recovery report")
    if (
        report.get("format_version") != 1
        or report.get("kind") != "stale_control_recovery"
        or report.get("recovery_id") != recovery_dir.name
        or Path(str(report.get("recovery_dir", ""))).resolve() != recovery_dir
        or report.get("historical_cleanup_proven") is not False
        or report.get("current_absence_proven") is not True
        or report.get("valid_score_episode") is not False
        or report.get("acceptance_claim")
        != "stale_control_current_absence_recovery_only"
        or report.get("stage")
        != "complete_when_marker_commit_condition_holds"
        or report.get("finalized") is not True
        or report.get("ok") is not True
    ):
        raise AgentError("recovery report success contract differs")
    recorded_digest = _require_sha256(
        report.get("report_body_sha256"), "recovery report body digest"
    )
    expected_digest = snapshot_digest(
        {key: value for key, value in report.items() if key != "report_body_sha256"}
    )
    if recorded_digest != expected_digest:
        raise AgentError("recovery report body digest differs")

    commit = report.get("write_ahead_commit")
    if not isinstance(commit, dict):
        raise AgentError("recovery write-ahead commit is missing")
    _require_exact_keys(
        commit,
        {
            "format_version",
            "kind",
            "completion_condition",
            "post_report_guard_order",
            "interpretation",
        },
        "recovery write-ahead commit",
    )
    condition = commit.get("completion_condition")
    if not isinstance(condition, dict):
        raise AgentError("recovery completion condition is missing")
    _require_exact_keys(
        condition,
        {
            "active_marker_absent",
            "archive_marker",
            "archive_marker_sha256",
        },
        "recovery completion condition",
    )
    if (
        commit.get("format_version") != 1
        or commit.get("kind") != "unsafe_marker_cas"
        or commit.get("post_report_guard_order")
        != [
            "dual_source_ck3_inventory_empty",
            "named_job_absent",
            "unsafe_marker_cas",
        ]
    ):
        raise AgentError("recovery write-ahead protocol differs")

    source_run = Path(str(report.get("source_run_dir", "")))
    if not source_run.is_absolute() or source_run.parent.name != "runs":
        raise AgentError("recovery source run path differs")
    expected_active = source_run.parent.parent / "control" / "unsafe-cleanup.json"
    active = Path(str(condition.get("active_marker_absent", "")))
    if (
        not active.is_absolute()
        or active.resolve() != expected_active.resolve()
        or active.exists()
        or active.is_symlink()
    ):
        raise AgentError("recovery active-marker completion condition is false")
    archive_relative = Path(str(condition.get("archive_marker", "")))
    if archive_relative.is_absolute() or ".." in archive_relative.parts:
        raise AgentError("recovery marker archive path is noncanonical")
    marker_archive = (recovery_dir / archive_relative).resolve()
    if (
        not is_relative_to(marker_archive, recovery_dir)
        or marker_archive.is_symlink()
        or not marker_archive.is_file()
        or sha256_file(marker_archive)
        != _require_sha256(
            condition.get("archive_marker_sha256"),
            "recovery marker archive digest",
        )
    ):
        raise AgentError("recovery marker archive completion condition is false")

    archived = report.get("archived_control_files")
    if not isinstance(archived, dict) or set(archived) != {
        "record",
        "ready",
        "watchdog_error",
        "unsafe_marker",
    }:
        raise AgentError("recovery archived-control manifest differs")
    marker_entry = archived["unsafe_marker"]
    if (
        not isinstance(marker_entry, dict)
        or marker_entry.get("path") != archive_relative.as_posix()
        or marker_entry.get("sha256")
        != condition.get("archive_marker_sha256")
    ):
        raise AgentError("recovery marker completion binding differs")
    verified: set[Path] = set()
    for label, entry in archived.items():
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise AgentError(f"recovery {label} archive reference differs")
        relative = Path(str(entry["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise AgentError(f"recovery {label} archive path is noncanonical")
        path = (recovery_dir / relative).resolve()
        if (
            not is_relative_to(path, recovery_dir)
            or path.is_symlink()
            or not path.is_file()
            or sha256_file(path)
            != _require_sha256(entry["sha256"], f"recovery {label} archive hash")
        ):
            raise AgentError(f"recovery {label} archive differs")
        verified.add(path)
    if len(verified) != len(archived) or marker_archive not in verified:
        raise AgentError("recovery archived-control files alias or omit the marker")
    return report


def _committed_marker_report(
    recovery_dir: Path,
    report: dict[str, object],
    canonical_marker: Path,
    marker_archive: Path,
    expected_sha256: str,
    expected_nonce: str,
) -> dict[str, object] | None:
    """Recognize a completed marker CAS using reads only.

    A returned report is the durable commit.  Once this condition holds the
    caller must not restore controls or rewrite the report, even while handling
    an asynchronous BaseException delivered immediately after the CAS call.
    """
    if canonical_marker.exists() or canonical_marker.is_symlink():
        return None
    expected_archive = recovery_dir.resolve() / "artifacts" / canonical_marker.name
    if (
        marker_archive.resolve() != expected_archive
        or marker_archive.is_symlink()
        or not marker_archive.is_file()
        or sha256_file(marker_archive) != expected_sha256
    ):
        return None
    marker = _load_object(marker_archive, "committed unsafe marker archive")
    if marker.get("nonce") != expected_nonce:
        return None
    committed = validate_recovery_report(recovery_dir)
    if committed != report:
        raise AgentError("committed recovery report differs from its prewritten body")
    return committed


def _recover_stale_control_locked(
    spec: EnvironmentSpec, run_id: str
) -> dict[str, object]:
    run_dir = _source_run_dir(spec, run_id)
    source_report_path = run_dir / "report.json"
    source_report_sha256 = sha256_file(source_report_path)
    recovery_id, recovery_dir = _create_recovery_dir(spec)
    report_path = recovery_dir / "report.json"
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "stale_control_recovery",
        "recovery_id": recovery_id,
        "recovery_dir": str(recovery_dir),
        "source_run_id": run_id,
        "source_run_dir": str(run_dir),
        "source_report_sha256": source_report_sha256,
        "started_at": utc_now(),
        "finished_at": None,
        "stage": "validating",
        "historical_cleanup_proven": False,
        "current_absence_proven": False,
        "valid_score_episode": False,
        "acceptance_claim": "stale_control_current_absence_recovery_only",
        "archived_control_files": {},
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(report_path, report)

    control_root = spec.state_dir.resolve() / "control"
    canonical_marker = control_root / "unsafe-cleanup.json"
    marker_archive = recovery_dir / "artifacts" / canonical_marker.name
    marker_bytes: bytes | None = None
    watchdog_nonce: str | None = None
    hashes: dict[str, str] = {}
    journal: list[tuple[str, Path, Path, str]] = []
    try:
        source, source_validation = _validate_recovery_source_report(run_dir)
        if (
            source.get("finalized") is not True
            or source.get("ok") is not False
            or source.get("unsafe_cleanup") is not True
            or source.get("valid_score_episode") is not False
            or source.get("runtime_write_absence_proven") is not False
            or source.get("run_id") != run_id
            or Path(str(source.get("run_dir", ""))).resolve() != run_dir
            or (
                isinstance(source.get("crash_attestation"), dict)
                and source["crash_attestation"].get("cleanup_proven") is True
            )
        ):
            raise AgentError("source crash report is not a finalized unsafe RED run")
        _revalidate_source_archive(
            run_dir, source_report_sha256, source, source_validation
        )

        environment_path, _ = _artifact_path(source, run_dir, "environment")
        _validate_environment(spec, source, environment_path)
        handoff_path, _ = _artifact_path(source, run_dir, "handoff")
        handoff, probe_nonce = _validate_handoff(
            spec, source, run_dir, handoff_path
        )
        armed_path, _ = _artifact_path(source, run_dir, "armed")
        armed, watchdog_nonce, control_paths = _validate_armed(
            spec, source, run_dir, armed_path, probe_nonce
        )
        if Path(str(handoff["armed"])).resolve() != armed_path:
            raise AgentError("handoff armed path differs from the report artifact")
        expected_watchdog_final = run_dir / "artifacts" / f"watchdog-final-{probe_nonce}.json"
        if Path(str(handoff["watchdog_final"])).resolve() != expected_watchdog_final:
            raise AgentError("handoff watchdog-final path differs")
        archived_marker_path, _ = _artifact_path(
            source, run_dir, "control_before_unsafe_marker"
        )
        marker_bytes = archived_marker_path.read_bytes()
        hashes, marker_bytes, watchdog_final = _validate_current_controls(
            armed,
            watchdog_nonce,
            control_paths,
            source,
            run_dir,
            probe_nonce,
        )
        if source_validation == "current":
            bound_final, bound_final_hash = _artifact_path(
                source, run_dir, "watchdog_final"
            )
            bound_error, bound_error_hash = _artifact_path(
                source, run_dir, "watchdog_error"
            )
            if (
                bound_final != expected_watchdog_final
                or bound_error
                != run_dir / "artifacts" / f"watchdog-error-{probe_nonce}.txt"
                or bound_final_hash != hashes["watchdog_final"]
                or bound_error_hash != hashes["watchdog_error"]
            ):
                raise AgentError("current watchdog diagnostic binding differs")
            diagnostic_binding = "source_report_artifact"
            diagnostic_source_bound = True
        else:
            artifacts = source.get("artifacts")
            if not isinstance(artifacts, dict) or {
                "watchdog_final",
                "watchdog_error",
            } & set(artifacts):
                raise AgentError("legacy watchdog diagnostic unexpectedly claims binding")
            diagnostic_binding = "recovery_time_sha256_and_current_control_consistency"
            diagnostic_source_bound = False

        identities: list[tuple[str, dict[str, object]]] = [
            ("outer_verifier", _validate_identity(handoff["outer"], "outer verifier")),
            ("supervisor", _validate_identity(armed["supervisor"], "supervisor")),
            ("ck3", _validate_identity(armed["ck3"], "CK3")),
            ("sentinel_parent", _validate_identity(armed["sentinel_parent"], "sentinel parent")),
            ("sentinel_child", _validate_identity(armed["sentinel_child"], "sentinel child")),
            ("watchdog", _validate_identity(armed["watchdog"], "watchdog")),
        ]
        if armed.get("supervisor_bootstrap") is not None:
            identities.insert(
                2,
                (
                    "supervisor_bootstrap",
                    _validate_identity(armed["supervisor_bootstrap"], "supervisor bootstrap"),
                ),
            )
        pids = [int(identity["pid"]) for _, identity in identities]
        if len(pids) != len(set(pids)):
            raise AgentError("recorded crash process identities reuse a PID")
        identity_absence = {
            label: _prove_identity_absent(identity, label)
            for label, identity in identities
        }
        if not _named_job_absent(str(armed["job_name"])):
            raise AgentError("named crash Job still exists")
        stable_inventory = _validate_empty_inventory(
            _wait_global_ck3_quiet(), "stable", stable=True
        )
        _revalidate_source_archive(
            run_dir, source_report_sha256, source, source_validation
        )

        report.update(
            {
                "stage": "validated",
                "source_validation": source_validation,
                "environment_sha256": source["environment_sha256"],
                "probe_nonce": probe_nonce,
                "watchdog_nonce": watchdog_nonce,
                "job_name": armed["job_name"],
                "watchdog_final": {
                    "path": str(expected_watchdog_final),
                    "sha256": hashes["watchdog_final"],
                    "stage": watchdog_final["stage"],
                    "ok": watchdog_final["ok"],
                    "binding": diagnostic_binding,
                    "source_report_bound": diagnostic_source_bound,
                },
                "identity_absence": identity_absence,
                "named_job_absent": True,
                "stable_ck3_inventory": stable_inventory,
                "current_absence_proven": True,
            }
        )
        write_json_atomic(report_path, report)

        archive_root = recovery_dir / "artifacts"
        order = ("record", "ready", "watchdog_error")
        for label in order:
            active = control_paths[label]
            archived = archive_root / active.name
            expected_nonce = watchdog_nonce if label != "watchdog_error" else None
            journal.append((label, active, archived, hashes[label]))
            _cas_archive_control(active, archived, hashes[label], expected_nonce)
            report["archived_control_files"][label] = {
                "path": archived.relative_to(recovery_dir).as_posix(),
                "sha256": hashes[label],
            }

        _revalidate_source_archive(
            run_dir, source_report_sha256, source, source_validation
        )
        if sha256_file(expected_watchdog_final) != hashes["watchdog_final"]:
            raise AgentError("watchdog final evidence changed before marker removal")
        report["archived_control_files"]["unsafe_marker"] = {
            "path": marker_archive.relative_to(recovery_dir).as_posix(),
            "sha256": hashes["unsafe_marker"],
        }
        report["source_report_unchanged"] = True
        report["write_ahead_commit"] = {
            "format_version": 1,
            "kind": "unsafe_marker_cas",
            "completion_condition": {
                "active_marker_absent": str(canonical_marker),
                "archive_marker": marker_archive.relative_to(
                    recovery_dir
                ).as_posix(),
                "archive_marker_sha256": hashes["unsafe_marker"],
            },
            "post_report_guard_order": [
                "dual_source_ck3_inventory_empty",
                "named_job_absent",
                "unsafe_marker_cas",
            ],
            "interpretation": (
                "ok=true is complete only when the active marker is absent and "
                "the archived marker has the declared SHA-256"
            ),
        }
        report["finished_at"] = utc_now()
        report["stage"] = "complete_when_marker_commit_condition_holds"
        report["finalized"] = True
        report["ok"] = True
        report["report_body_sha256"] = snapshot_digest(
            {key: value for key, value in report.items() if key != "report_body_sha256"}
        )
        write_json_atomic(report_path, report)

        _validate_empty_inventory(
            ck3_process_inventory(), "pre-marker", stable=False
        )
        if not _named_job_absent(str(armed["job_name"])):
            raise AgentError("named crash Job reappeared before marker removal")
        journal.append(
            (
                "unsafe_marker",
                canonical_marker,
                marker_archive,
                hashes["unsafe_marker"],
            )
        )
        _cas_archive_control(
            canonical_marker,
            marker_archive,
            hashes["unsafe_marker"],
            watchdog_nonce,
        )
        return report
    except BaseException as error:
        if watchdog_nonce is not None and "unsafe_marker" in hashes:
            committed = _committed_marker_report(
                recovery_dir,
                report,
                canonical_marker,
                marker_archive,
                hashes["unsafe_marker"],
                watchdog_nonce,
            )
            if committed is not None:
                return committed
        restoration = _restore_controls(journal)
        if marker_bytes is not None and not canonical_marker.exists():
            try:
                write_bytes_atomic(canonical_marker, marker_bytes)
                restoration["unsafe_marker_fallback"] = "restored"
            except OSError as restore_error:
                restoration["unsafe_marker_fallback"] = (
                    f"restore_failed:{type(restore_error).__name__}"
                )
        remaining_archives: dict[str, dict[str, str]] = {}
        for label, _, archived, expected_hash in journal:
            if archived.is_file():
                remaining_archives[label] = {
                    "path": archived.relative_to(recovery_dir).as_posix(),
                    "sha256": expected_hash,
                }
        report["archived_control_files"] = remaining_archives
        report.pop("marker_removed", None)
        report.pop("write_ahead_commit", None)
        report["marker_present_after_failure"] = canonical_marker.is_file()
        report["current_absence_proven"] = False
        try:
            _finalize_failure_report(report_path, report, error, restoration)
        except Exception as report_error:
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise AgentError(
                f"stale-control recovery failed and its RED report could not be finalized: {report_error}"
            ) from error
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        raise AgentError(
            f"stale-control recovery failed; evidence retained at {recovery_dir}: {error}"
        ) from error


def recover_stale_control(
    spec: EnvironmentSpec, run_id: str
) -> dict[str, object]:
    """Recover stale control files only for one explicitly named RED crash run."""
    ensure_state_path_safe(spec.state_dir)
    _ensure_control_root_canonical(spec)
    with exclusive_state_lock(spec.state_dir, "recover-stale-control"):
        with exclusive_launch_lock(spec.game_exe):
            return _recover_stale_control_locked(spec, run_id)
