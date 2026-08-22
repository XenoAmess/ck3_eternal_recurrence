"""Sealed visible-UI smoke from the main menu to the bookmark lobby.

This runner deliberately permits one game action only: the visible
``main_menu.new_game`` control.  It shares the normal supervisor's tracked
Job/watchdog shutdown contract, but has its own report and replay validator.
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
import time
import uuid

from jsonschema import Draft202012Validator, FormatChecker

from .environment import (
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
    same_process_creation_time,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
    verify_profile,
    write_bytes_atomic,
    write_json_atomic,
)
from .errors import AgentError
from .integrity import protected_snapshot, verify_protected_unchanged
from .locking import exclusive_launch_lock, exclusive_state_lock
from .rules import MOD_RULES
from .runtime import (
    SessionHandle,
    analyze_engine_log_bytes,
    append_event,
    collect_engine_log_evidence,
    launch,
    log,
    parse_runtime_attestation,
    stop_tracked,
    utc_now,
    validate_event_chain,
    validate_final_report_payload,
    wait_for_runtime_attestation,
    write_gzip_json_atomic,
)


UI_CONTRACT_REPOSITORY_RELATIVE = Path(
    "ck3_autonomous_player/configs/ui/ck3-1.19.0.6.zh-hans.2560x1440.json"
)
UI_CONTRACT_AGENT_RUNTIME_PATH = (
    "agent/configs/ui/ck3-1.19.0.6.zh-hans.2560x1440.json"
)
UI_CONTRACT_ARCHIVE = "ui-contract.json"
OBSERVATION_SCHEMA = (
    REPO_ROOT / "ck3_autonomous_player" / "schemas" / "observation-v2.schema.json"
)
ACTION_RECEIPT_SCHEMA = (
    REPO_ROOT
    / "ck3_autonomous_player"
    / "schemas"
    / "visible-control-action-receipt-v2.schema.json"
)
OBSERVATION_SCHEMA_AGENT_RUNTIME_PATH = "agent/schemas/observation-v2.schema.json"
ACTION_RECEIPT_SCHEMA_AGENT_RUNTIME_PATH = (
    "agent/schemas/visible-control-action-receipt-v2.schema.json"
)
MENU_KIND = "visible_menu_transition_smoke"
MENU_ACCEPTANCE_CLAIM = "visible_main_menu_to_bookmark_lobby_only"
REPORT_BINDING_EXCLUSIONS = frozenset(
    {
        "finalized",
        "ok",
        "final_event_sha256",
        "event_chain",
        "report_body_sha256",
    }
)
REPLAY_TRUST_MODEL = {
    "integrity": "unkeyed_sha256",
    "claim": "archive_schema_and_internal_consistency_only",
    "historical_execution_authenticity_proven": False,
}
NORMAL_V2_QUALIFICATION_VALIDATOR = "validate_smoke_report:v2 self-contained"
LEGACY_NORMAL_QUALIFICATION_VALIDATOR = (
    "validate_smoke_report + menu semantic conjunction"
)
FOREGROUND_OPERATION = "exact_hwnd_foreground_without_synthetic_input"
FOREGROUND_PROTOCOL_VERSION = 2
# Immutable compatibility identities for the four pre-v2, finalized, zero-input
# field runs.  Absence of the generation marker is never accepted generically.
LEGACY_FOREGROUND_PROTOCOL_FINAL_EVENTS = {
    "20260822T010001Z-menu-193c8062": (
        "e8ce9969c916eb5332ceac920a08edf31c1927d4959599b853ba3818dc00c142"
    ),
    "20260822T021436Z-menu-c9b3d667": (
        "4cfad9d5e27f4db994676560664ef0eb5611c3421d0a6880b6a874407055a44d"
    ),
    "20260822T034104Z-menu-49f9b8bd": (
        "489bc93111bac28b93232e28eab4b0ae8ec82bb39e1649cbde1616bddf178e26"
    ),
    "20260822T050447Z-menu-0eae4606": (
        "83908f88c8a77dbbeea717fbd411b013e691cdb86235b2eb56bef3dd52d4cdd8"
    ),
}
GREEN_EVENT_ORDER = (
    "smoke_started",
    "ck3_launched",
    "single_mod_runtime_attested",
    "foreground_activation_planned",
    "foreground_activation_armed",
    "foreground_activation_finished",
    "visible_main_menu_attested",
    "ui_action_planned",
    "ui_input_armed",
    "ui_action_finished",
    "bookmark_lobby_attested",
    "tracked_process_stopped",
    "postflight_attested",
    "smoke_finished",
)
RED_EVENT_ORDER = (
    *GREEN_EVENT_ORDER[:10],
    "foreground_lost",
    *GREEN_EVENT_ORDER[10:],
)


def _validate_json_schema(instance: object, schema_path: Path, label: str) -> None:
    """Execute the frozen Draft 2020-12 schema, not merely document it."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"menu smoke {label} schema cannot be loaded: {error}") from error
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "$"
        raise AgentError(
            f"menu smoke {label} violates its Draft 2020-12 schema at "
            f"{location}: {first.message}"
        )


def _report_body_sha256(report: dict[str, object]) -> str:
    body = {
        key: value
        for key, value in report.items()
        if key not in REPORT_BINDING_EXCLUSIONS
    }
    return snapshot_digest(body)


def _append_final_event_transactionally(
    events: Path,
    *,
    ok: bool,
    report_body_sha256: str,
    expected_prefix: dict[str, object] | None = None,
    expected_final_row: dict[str, object] | None = None,
) -> str:
    """Append the unique final WAL row and recover an after-fsync exception.

    ``append_event`` can durably append and fsync its row before a wrapper or
    filesystem layer reports an exception.  Retrying blindly would create two
    final rows.  Recover only when the validated chain grew by exactly one and
    its new tail is the exact candidate; otherwise preserve the original
    failure.
    """
    before = validate_event_chain(events)
    if expected_prefix is not None and (
        before.get("event_count") != expected_prefix.get("event_count")
        or before.get("tail_sha256") != expected_prefix.get("tail_sha256")
        or before.get("tail") != expected_prefix.get("tail")
    ):
        raise AgentError("menu smoke event prefix changed after candidate replay")
    payload: dict[str, object] = {
        "kind": "smoke_finished",
        "ok": ok,
        "report_body_sha256": report_body_sha256,
    }
    if expected_final_row is not None:
        if (
            set(expected_final_row)
            != {
                "at",
                "previous_event_sha256",
                "kind",
                "ok",
                "report_body_sha256",
                "event_sha256",
            }
            or expected_final_row.get("previous_event_sha256")
            != before.get("tail_sha256")
            or expected_final_row.get("kind") != "smoke_finished"
            or expected_final_row.get("ok") is not ok
            or expected_final_row.get("report_body_sha256")
            != report_body_sha256
        ):
            raise AgentError("menu smoke planned final WAL row differs")
        # append_event deliberately lets explicit event keys override its
        # defaults.  Commit the exact timestamp that passed hypothetical
        # replay instead of sampling a second, unvalidated final row.
        payload["at"] = expected_final_row["at"]
    try:
        digest = append_event(events, payload)
        if (
            expected_final_row is not None
            and digest != expected_final_row.get("event_sha256")
        ):
            raise AgentError("menu smoke committed final WAL digest differs")
        return digest
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
            and tail.get("kind") == payload["kind"]
            and tail.get("ok") is ok
            and tail.get("report_body_sha256") == report_body_sha256
            and tail.get("event_sha256") == after.get("tail_sha256")
            and (
                expected_final_row is None or tail == expected_final_row
            )
        ):
            try:
                # Reading the just-written row can succeed from the page
                # cache even when append_event's first fsync reported an
                # error.  Establish a fresh durability barrier before this
                # tail is allowed to authorize a final (possibly GREEN)
                # report, then revalidate that the file did not change.
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


def _fsync_existing_file(path: Path) -> None:
    """Issue an explicit durability barrier for an already written file."""
    with path.open("r+b") as output:
        output.flush()
        os.fsync(output.fileno())


def _final_report_temporary_is_proven_absent(path: Path) -> bool:
    """Return true only when an exact filesystem lookup reports no entry."""
    try:
        path.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return False


def _discard_final_report_temporary(path: Path) -> None:
    """Remove an unpublished report inode or fail before another attempt."""
    unlink_error: OSError | None = None
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        unlink_error = error
    if _final_report_temporary_is_proven_absent(path):
        return
    error = AgentError(
        f"unpublished final menu report temporary remains: {path.name}"
    )
    if unlink_error is not None:
        raise error from unlink_error
    raise error


def _publish_menu_provisional_report(
    path: Path, report: dict[str, object]
) -> None:
    """Persist a plainly non-final report when no replayable seal is safe."""
    report["finalized"] = False
    report["ok"] = False
    for field in (
        "report_body_sha256",
        "final_event_sha256",
        "event_chain",
    ):
        report.pop(field, None)
    _write_final_report_transactionally(path, report)


def _append_foreground_loss_event_transactionally(
    events: Path, payload: dict[str, object]
) -> tuple[str, dict[str, object]]:
    """Publish one non-input loss row, reconciling committed-then-raise."""
    before = validate_event_chain(events)
    append_error: Exception | None = None
    try:
        digest = append_event(events, payload)
    except Exception as error:
        append_error = error
        digest = ""
    after = validate_event_chain(events)
    tail = after.get("tail")
    unsigned_tail = dict(tail) if isinstance(tail, dict) else {}
    unsigned_tail.pop("at", None)
    unsigned_tail.pop("previous_event_sha256", None)
    unsigned_tail.pop("event_sha256", None)
    if (
        after.get("event_count") != int(before["event_count"]) + 1
        or not isinstance(tail, dict)
        or tail.get("previous_event_sha256") != before.get("tail_sha256")
        or unsigned_tail != payload
        or tail.get("event_sha256") != after.get("tail_sha256")
        or (digest and digest != tail.get("event_sha256"))
    ):
        if append_error is not None:
            raise append_error
        raise AgentError("foreground-loss WAL row differs after append")
    if append_error is not None:
        try:
            _fsync_existing_file(events)
            durable = validate_event_chain(events)
        except Exception as barrier_error:
            raise append_error from barrier_error
        if durable != after:
            raise append_error
    return str(tail["event_sha256"]), tail


def _archive_foreground_loss(
    error: object, artifacts: Path, events: Path
) -> dict[str, object]:
    """Bind immutable detection bytes to one artifact and the primary WAL."""
    from .vision import ForegroundLossError

    if not isinstance(error, ForegroundLossError):
        raise AgentError("foreground-loss archive received a different error")
    snapshot = error.snapshot
    snapshot_id = str(snapshot.get("snapshot_id", ""))
    if re.fullmatch(r"[0-9a-f]{32}", snapshot_id) is None:
        raise AgentError("foreground-loss snapshot ID differs")
    artifact = artifacts / f"foreground-loss-{snapshot_id}.json"
    raw = error.snapshot_bytes + b"\n"
    write_bytes_atomic(artifact, raw)
    _fsync_existing_file(artifact)
    relative = f"artifacts/{artifact.name}"
    artifact_sha256 = sha256_file(artifact)
    snapshot_sha256 = snapshot_digest(snapshot)
    target = snapshot.get("target")
    foreground = snapshot.get("foreground")
    if not isinstance(target, dict) or not isinstance(foreground, dict):
        raise AgentError("foreground-loss snapshot identity is missing")
    payload = {
        "kind": "foreground_lost",
        "snapshot_id": snapshot_id,
        "artifact_path": relative,
        "artifact_sha256": artifact_sha256,
        "artifact_size": len(raw),
        "snapshot_sha256": snapshot_sha256,
        "target_pid": target.get("pid"),
        "target_hwnd": target.get("hwnd"),
        "foreground_status": foreground.get("status"),
        "foreground_root_hwnd": foreground.get("root_hwnd"),
        "foreground_pid": foreground.get("pid"),
        "checkpoint": snapshot.get("checkpoint"),
        "synthetic_input": False,
        "reusable_authorization": False,
    }
    event_sha256, _row = _append_foreground_loss_event_transactionally(
        events, payload
    )
    return {
        "format_version": 1,
        "snapshot_id": snapshot_id,
        "artifact_path": relative,
        "artifact_sha256": artifact_sha256,
        "artifact_size": len(raw),
        "snapshot_sha256": snapshot_sha256,
        "event_sha256": event_sha256,
    }


def _write_final_report_transactionally(
    path: Path, report: dict[str, object]
) -> None:
    """Fsync an exact sibling temporary before atomically publishing it."""
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    first_error: Exception | None = None
    for _attempt in range(2):
        temporary = path.with_name(
            f".{path.name}.final-{uuid.uuid4().hex}.tmp"
        )
        try:
            # A failure here must leave the previously published provisional
            # report untouched.  Only a fully flushed and fsynced inode may be
            # offered to os.replace.
            with temporary.open("xb") as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
        except Exception as error:
            if first_error is None:
                first_error = error
            # A leftover from one attempt is not harmless: a later successful
            # publication would leave an unmanifested final-report candidate
            # beside a GREEN report.  Prove removal before any retry.
            _discard_final_report_temporary(temporary)
            continue
        try:
            os.replace(temporary, path)
            return
        except Exception as error:
            if first_error is None:
                first_error = error
            # Some Windows/filesystem wrappers can report an exception after
            # ReplaceFile has committed.  Accept only that exact state: the
            # fsynced source name is gone and the destination bytes are exact.
            try:
                committed = (
                    _final_report_temporary_is_proven_absent(temporary)
                    and path.read_bytes() == raw
                )
            except OSError:
                committed = False
            if committed:
                return
            _discard_final_report_temporary(temporary)
    if first_error is not None:
        raise first_error
    raise AgentError("final menu smoke report differs after atomic publication")


def _remaining(deadline: float, stage: str) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise AgentError(f"menu smoke timeout before {stage}")
    return remaining


def _canonicalize_ui_artifact_references(
    value: object,
    run_dir: Path,
    *,
    reference_keys: frozenset[str] = frozenset(
        {"screenshot", "observation", "receipt_artifact"}
    ),
) -> object:
    """Replace UI artifact absolute paths with canonical run-relative refs."""
    root = run_dir.resolve()
    def visit(item: object, key: str | None = None) -> object:
        if isinstance(item, dict):
            return {str(child_key): visit(child, str(child_key)) for child_key, child in item.items()}
        if isinstance(item, list):
            return [visit(child, key) for child in item]
        if key in reference_keys and isinstance(item, str) and item:
            candidate = Path(item)
            if candidate.is_absolute():
                resolved = candidate.resolve()
                if not is_relative_to(resolved, root):
                    raise AgentError(f"visible UI artifact reference escapes run: {item}")
                relative = resolved.relative_to(root).as_posix()
            else:
                if "\\" in item or candidate.as_posix() != item or ".." in candidate.parts:
                    raise AgentError(f"visible UI artifact reference is noncanonical: {item}")
                relative = item
            if not relative.startswith("artifacts/"):
                raise AgentError(
                    f"visible UI artifact is outside the artifacts directory: {relative}"
                )
            return relative
        return item

    return visit(value)


def _require_committed_environment(manifest: dict[str, object]) -> None:
    runtime = manifest.get("agent_runtime")
    agent_git = runtime.get("git", {}) if isinstance(runtime, dict) else {}
    if (
        not isinstance(agent_git, dict)
        or not agent_git.get("all_files_tracked")
        or agent_git.get("dirty")
        or not re.fullmatch(
            r"[0-9a-f]{40}",
            str(agent_git.get("selected_runtime_revision", "")),
        )
    ):
        raise AgentError(
            "menu smoke requires a committed, clean selected agent runtime"
        )
    current_mod = mod_source_fingerprint()
    mod = manifest.get("mod")
    recorded_mod = mod.get("source_provenance", {}) if isinstance(mod, dict) else {}
    if (
        not isinstance(recorded_mod, dict)
        or current_mod.get("git_dirty")
        or not current_mod.get("all_release_files_tracked")
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(current_mod.get("git_revision", ""))
        )
        or current_mod.get("release_source_sha256")
        != recorded_mod.get("release_source_sha256")
    ):
        raise AgentError(
            "menu smoke requires a committed, clean production mod source"
        )


def _archive_ui_contract(
    manifest: dict[str, object], run_dir: Path
) -> dict[str, object]:
    """Read the canonical source once and bind those exact bytes to the run."""
    runtime = manifest.get("agent_runtime")
    files = runtime.get("files") if isinstance(runtime, dict) else None
    if not isinstance(files, list):
        raise AgentError("environment agent runtime file inventory is missing")
    matches = [
        item
        for item in files
        if isinstance(item, dict)
        and item.get("path") == UI_CONTRACT_AGENT_RUNTIME_PATH
    ]
    if len(matches) != 1:
        raise AgentError(
            "environment must bind exactly one canonical visible UI contract"
        )
    recorded = matches[0]
    expected_hash = str(recorded.get("sha256", ""))
    expected_size = recorded.get("size")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        or type(expected_size) is not int
        or expected_size <= 0
    ):
        raise AgentError("environment visible UI contract fingerprint is invalid")

    source = (REPO_ROOT / UI_CONTRACT_REPOSITORY_RELATIVE).resolve()
    expected_source = (
        REPO_ROOT
        / "ck3_autonomous_player"
        / "configs"
        / "ui"
        / "ck3-1.19.0.6.zh-hans.2560x1440.json"
    ).resolve()
    if source != expected_source or not source.is_file():
        raise AgentError("canonical visible UI contract source is unavailable")
    raw = source.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_size or actual_hash != expected_hash:
        raise AgentError(
            "canonical visible UI contract bytes differ from the prepared environment"
        )
    archive = run_dir / UI_CONTRACT_ARCHIVE
    if archive.exists():
        raise AgentError("menu smoke UI contract archive already exists")
    write_bytes_atomic(archive, raw)
    if archive.stat().st_size != expected_size or sha256_file(archive) != expected_hash:
        raise AgentError("archived visible UI contract bytes differ")
    return {
        "agent_runtime_path": UI_CONTRACT_AGENT_RUNTIME_PATH,
        "source_repository_relative": UI_CONTRACT_REPOSITORY_RELATIVE.as_posix(),
        "archive_path": UI_CONTRACT_ARCHIVE,
        "size": expected_size,
        "sha256": expected_hash,
    }


def _archive_runtime_debug_prefix(
    spec: EnvironmentSpec,
    debug_evidence: object,
    artifacts: Path,
    archive_name: str,
) -> dict[str, object]:
    """Freeze and bind one exact fresh-session debug.log prefix."""
    if not isinstance(debug_evidence, dict):
        raise AgentError("runtime load attestation lacks debug prefix metadata")
    debug = debug_evidence
    source = Path(str(debug.get("path", ""))).resolve()
    expected_source = (spec.profile_dir / "logs" / "debug.log").resolve()
    prefix_size = debug.get("captured_prefix_size")
    expected_hash = str(debug.get("captured_prefix_sha256", ""))
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
    prefix_path = artifacts / archive_name
    write_bytes_atomic(prefix_path, prefix)
    archived_debug = json.loads(json.dumps(debug, ensure_ascii=False))
    archived_debug["archive_path"] = f"artifacts/{archive_name}"
    archived_debug["archive_sha256"] = sha256_file(prefix_path)
    return archived_debug


def _archive_runtime_attestation(
    spec: EnvironmentSpec,
    load_evidence: dict[str, object],
    artifacts: Path,
) -> dict[str, object]:
    """Freeze the exact debug.log prefix that established the load contract."""
    archived = json.loads(json.dumps(load_evidence, ensure_ascii=False))
    archived_debug = _archive_runtime_debug_prefix(
        spec,
        archived.get("debug_log"),
        artifacts,
        "runtime-debug-prefix.log",
    )
    archived["debug_log"] = archived_debug
    write_json_atomic(artifacts / "supervisor-load-attestation.json", archived)
    return archived


def _artifact_manifest(run_dir: Path) -> list[dict[str, object]]:
    root = run_dir.resolve()
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in {"report.json", "events.jsonl"}:
            continue
        if path.is_symlink() or not is_relative_to(path.resolve(), root):
            raise AgentError(f"menu smoke artifact escapes its run: {relative}")
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if len({str(item["path"]) for item in entries}) != len(entries):
        raise AgentError("menu smoke artifact manifest contains duplicate paths")
    return entries


def _verified_artifact_manifest(
    report: dict[str, object], run_dir: Path
) -> dict[str, Path]:
    manifest = report.get("artifacts")
    if not isinstance(manifest, list) or not manifest:
        raise AgentError("menu smoke artifact manifest is missing")
    root = run_dir.resolve()
    verified: dict[str, Path] = {}
    for index, raw in enumerate(manifest):
        if not isinstance(raw, dict) or set(raw) != {"path", "size", "sha256"}:
            raise AgentError(f"menu smoke artifact entry {index} differs")
        relative = raw.get("path")
        size = raw.get("size")
        digest = raw.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or relative.startswith("/")
            or type(size) is not int
            or size < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
        ):
            raise AgentError(f"menu smoke artifact entry {index} is malformed")
        path = (root / Path(relative)).resolve()
        if (
            not is_relative_to(path, root)
            or path in {root / "report.json", root / "events.jsonl"}
            or not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != size
            or sha256_file(path) != digest
        ):
            raise AgentError(f"menu smoke artifact differs: {relative}")
        if relative in verified:
            raise AgentError("menu smoke artifact manifest has duplicate paths")
        verified[relative] = path
    actual = {
        str(item["path"]): item
        for item in _artifact_manifest(root)
    }
    recorded = {str(item["path"]): item for item in manifest}
    if recorded != actual:
        raise AgentError("menu smoke artifact manifest is not the complete run set")
    return verified


def _stable_frames(payload: object, label: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        raise AgentError(f"menu smoke {label} observation is missing")
    stability = payload.get("stability")
    if (
        not isinstance(stability, dict)
        or stability.get("stable_frames") != 2
        or stability.get("expected_screen") != payload.get("screen")
    ):
        raise AgentError(f"menu smoke {label} stability contract differs")
    frames = stability.get("frames")
    if not isinstance(frames, list) or len(frames) != 2:
        raise AgentError(f"menu smoke {label} lacks two stable frames")
    if any(not isinstance(frame, dict) for frame in frames):
        raise AgentError(f"menu smoke {label} stable frames are malformed")
    identifiers: list[str] = []
    monotonic_values: list[float] = []
    sequences: list[int] = []
    for frame in frames:
        observation_id = frame.get("observation_id")
        captured_monotonic = frame.get("captured_monotonic")
        sequence = frame.get("capture_sequence")
        if not re.fullmatch(r"[0-9a-f]{32}", str(observation_id)):
            raise AgentError(f"menu smoke {label} stable observation ID differs")
        if (
            not isinstance(captured_monotonic, (int, float))
            or isinstance(captured_monotonic, bool)
            or not math.isfinite(float(captured_monotonic))
        ):
            raise AgentError(f"menu smoke {label} stable monotonic evidence differs")
        if type(sequence) is not int or sequence <= 0:
            raise AgentError(f"menu smoke {label} capture sequence differs")
        identifiers.append(str(observation_id))
        monotonic_values.append(float(captured_monotonic))
        sequences.append(sequence)
    if (
        len(set(identifiers)) != 2
        or sequences[1] != sequences[0] + 1
        or not monotonic_values[0] < monotonic_values[1]
        or not math.isclose(
            float(stability.get("monotonic_delta", -1)),
            monotonic_values[1] - monotonic_values[0],
            rel_tol=0,
            abs_tol=1e-9,
        )
    ):
        raise AgentError(f"menu smoke {label} stable frame order differs")
    return frames


def _replay_visible_frame(
    screenshot: Path, contract: object
) -> dict[str, object]:
    """Re-run the pinned PNG through this repository's OCR/classifier stack."""
    from PIL import Image

    try:
        with Image.open(screenshot) as probe:
            if (
                probe.format != "PNG"
                or tuple(probe.size) != tuple(getattr(contract, "resolution", ()))
                or probe.mode != "RGB"
            ):
                raise AgentError("menu smoke archived screenshot raster contract differs")
            probe.verify()
        with Image.open(screenshot) as source:
            source.load()
            image = source.copy()
    except AgentError:
        raise
    except (OSError, ValueError) as error:
        raise AgentError(
            f"menu smoke archived screenshot is not a valid PNG: {error}"
        ) from error

    from .vision.ocr import matching_spans, ocr_spans

    spans = ocr_spans(image)
    screen, confidence, reasons, anchors = contract.classify(spans, image)
    controls: list[dict[str, object]] = []
    for spec in contract.controls_for(screen):
        matches = matching_spans(
            spans,
            spec.text,
            contract.resolution,
            spec.region,
            contains=spec.contains,
        )
        if len(matches) != 1:
            reasons = (*reasons, f"{spec.control_id} matches={len(matches)}")
            screen = "unknown"
            confidence = 0.0
            controls = []
            break
        span = matches[0]
        controls.append(
            {
                "control_id": spec.control_id,
                "label": spec.label,
                "bbox": list(span.bbox),
                "center": list(span.center),
            }
        )
    return {
        "screen": screen,
        "ocr": [span.to_json() for span in spans],
        "visible_anchors": [anchor.to_json() for anchor in anchors],
        "visible_controls": controls,
        "visible_facts": {
            "screen": screen,
            "anchors": [anchor.anchor_id for anchor in anchors],
        },
        "confidence": confidence,
        "unknown_reasons": list(reasons),
    }


def _validate_stable_audit(
    policy: dict[str, object],
    audit: object,
    *,
    screen: str,
    verified: dict[str, Path],
    window_binding: dict[str, object],
    contract: object,
) -> None:
    _validate_json_schema(policy, OBSERVATION_SCHEMA, f"{screen} stable policy")
    policy_frames = _stable_frames(policy, screen)
    if (
        not isinstance(audit, dict)
        or set(audit) != {"stable_frames", "expected_screen", "frames", "monotonic_delta"}
        or audit.get("stable_frames") != 2
        or audit.get("expected_screen") != screen
        or not isinstance(audit.get("frames"), list)
        or len(audit["frames"]) != 2
    ):
        raise AgentError(f"menu smoke {screen} stable audit contract differs")
    process_binding = window_binding.get("process")
    window = window_binding.get("window")
    if not isinstance(process_binding, dict) or not isinstance(window, dict):
        raise AgentError("menu smoke window binding is malformed")
    expected_anchors = {
        anchor.anchor_id
        for screen_spec in getattr(contract, "screens", ())
        if screen_spec.screen_id == screen
        for anchor in screen_spec.anchors
    }
    if not expected_anchors:
        raise AgentError(f"menu smoke contract lacks {screen} anchors")
    anchor_centers: list[dict[str, tuple[int, int]]] = []
    archived_observations: list[dict[str, object]] = []
    for policy_frame, audit_frame in zip(policy_frames, audit["frames"]):
        if not isinstance(audit_frame, dict):
            raise AgentError(f"menu smoke {screen} stable audit frame differs")
        if set(audit_frame) != {
            "observation_id",
            "frame_id",
            "captured_at",
            "capture_sequence",
            "captured_monotonic",
            "screenshot_sha256",
            "screenshot",
            "observation",
            "pid",
            "hwnd",
            "client_rect",
        } or set(policy_frame) != {
            "observation_id",
            "frame_id",
            "captured_at",
            "capture_sequence",
            "captured_monotonic",
            "screenshot_sha256",
        }:
            raise AgentError(f"menu smoke {screen} stable frame schema differs")
        for key in (
            "observation_id",
            "frame_id",
            "captured_at",
            "capture_sequence",
            "captured_monotonic",
            "screenshot_sha256",
        ):
            if audit_frame.get(key) != policy_frame.get(key):
                raise AgentError(f"menu smoke {screen} policy/audit frame binding differs")
        screenshot_ref = audit_frame.get("screenshot")
        observation_ref = audit_frame.get("observation")
        if (
            not isinstance(screenshot_ref, str)
            or not isinstance(observation_ref, str)
            or screenshot_ref not in verified
            or observation_ref not in verified
            or not screenshot_ref.startswith("artifacts/")
            or not observation_ref.startswith("artifacts/")
            or sha256_file(verified[screenshot_ref])
            != audit_frame.get("screenshot_sha256")
        ):
            raise AgentError(f"menu smoke {screen} stable frame artifact differs")
        try:
            archived = json.loads(
                verified[observation_ref].read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentError(
                f"menu smoke {screen} observation artifact cannot be parsed: {error}"
            ) from error
        observation = archived.get("policy_observation") if isinstance(archived, dict) else None
        private = archived.get("private_audit") if isinstance(archived, dict) else None
        _validate_json_schema(
            observation, OBSERVATION_SCHEMA, f"{screen} archived observation"
        )
        if (
            not isinstance(archived, dict)
            or set(archived) != {"format_version", "policy_observation", "private_audit"}
            or archived.get("format_version") != 2
            or not isinstance(observation, dict)
            or not isinstance(private, dict)
            or set(private)
            != {
                "process",
                "client_rect",
                "screenshot_path",
                "observation_path",
                "capture_sequence",
                "captured_monotonic",
                "capture_started_at",
            }
            or observation.get("observation_id") != audit_frame.get("observation_id")
            or observation.get("frame_id") != audit_frame.get("frame_id")
            or observation.get("screen") != screen
            or observation.get("image", {}).get("sha256")
            != audit_frame.get("screenshot_sha256")
            or private.get("process")
            != {"pid": audit_frame.get("pid"), "hwnd": audit_frame.get("hwnd")}
            or private.get("client_rect") != audit_frame.get("client_rect")
            or private.get("capture_sequence") != audit_frame.get("capture_sequence")
            or private.get("captured_monotonic")
            != audit_frame.get("captured_monotonic")
            or private.get("screenshot_path") != screenshot_ref
            or private.get("observation_path") != observation_ref
            or audit_frame.get("pid") != process_binding.get("pid")
            or audit_frame.get("hwnd") != window.get("hwnd")
            or audit_frame.get("client_rect") != window.get("client_rect")
        ):
            raise AgentError(f"menu smoke {screen} observation audit binding differs")
        if (
            observation.get("format_version") != 2
            or observation.get("policy_boundary")
            != "player-visible pixels and OCR only"
            or observation.get("image")
            != {
                "ref": f"frame:{audit_frame.get('frame_id')}",
                "sha256": audit_frame.get("screenshot_sha256"),
                "width": getattr(contract, "resolution", (None, None))[0],
                "height": getattr(contract, "resolution", (None, None))[1],
            }
        ):
            raise AgentError(f"menu smoke {screen} policy image contract differs")
        replayed = _replay_visible_frame(verified[screenshot_ref], contract)
        archived_controls = observation.get("visible_controls")
        replayed_controls = replayed.pop("visible_controls")
        if not isinstance(archived_controls, list):
            raise AgentError(f"menu smoke {screen} visible controls differ")
        normalized_controls: list[dict[str, object]] = []
        for control in archived_controls:
            if (
                not isinstance(control, dict)
                or not re.fullmatch(
                    r"[0-9a-f]{64}", str(control.get("control_token", ""))
                )
            ):
                raise AgentError(f"menu smoke {screen} control token differs")
            normalized_controls.append(
                {
                    key: control.get(key)
                    for key in ("control_id", "label", "bbox", "center")
                }
            )
        replayed_payload = {
            key: observation.get(key)
            for key in (
                "screen",
                "ocr",
                "visible_anchors",
                "visible_facts",
                "confidence",
                "unknown_reasons",
            )
        }
        if replayed_payload != replayed or normalized_controls != replayed_controls:
            raise AgentError(f"menu smoke {screen} PNG/OCR replay differs")
        anchors = observation.get("visible_anchors")
        if (
            not isinstance(anchors, list)
            or {item.get("anchor_id") for item in anchors if isinstance(item, dict)}
            != expected_anchors
        ):
            raise AgentError(f"menu smoke {screen} visible anchors differ")
        centers = {
            str(item["anchor_id"]): tuple(item["center"])
            for item in anchors
            if isinstance(item, dict)
            and isinstance(item.get("center"), list)
            and len(item["center"]) == 2
        }
        if set(centers) != expected_anchors:
            raise AgentError(f"menu smoke {screen} anchor centers differ")
        anchor_centers.append(centers)
        controls = observation.get("visible_controls")
        expected_controls = ["main_menu.new_game"] if screen == "main_menu" else []
        if (
            not isinstance(controls, list)
            or [item.get("control_id") for item in controls if isinstance(item, dict)]
            != expected_controls
        ):
            raise AgentError(f"menu smoke {screen} visible controls differ")
        archived_observations.append(observation)
    for anchor_id in expected_anchors:
        first = anchor_centers[0][anchor_id]
        second = anchor_centers[1][anchor_id]
        if abs(first[0] - second[0]) > 15 or abs(first[1] - second[1]) > 15:
            raise AgentError(f"menu smoke {screen} anchor moved beyond tolerance")
    latest_policy = dict(policy)
    latest_policy.pop("stability", None)
    if latest_policy != archived_observations[-1]:
        raise AgentError(f"menu smoke {screen} latest stable policy binding differs")


def _validate_action_observation(
    evidence: object,
    *,
    expected_screen: str,
    verified: dict[str, Path],
    window_binding: dict[str, object],
    contract: object,
    label: str,
) -> dict[str, object]:
    if not isinstance(evidence, dict):
        raise AgentError(f"menu smoke {label} observation evidence is missing")
    screenshot_ref = evidence.get("screenshot")
    observation_ref = evidence.get("observation")
    if (
        set(evidence)
        != {
            "observation_id",
            "frame_id",
            "captured_at",
            "capture_sequence",
            "captured_monotonic",
            "screenshot",
            "screenshot_sha256",
            "observation",
            "screen",
            "pid",
            "hwnd",
            "client_rect",
        }
        or not isinstance(screenshot_ref, str)
        or not isinstance(observation_ref, str)
        or screenshot_ref not in verified
        or observation_ref not in verified
        or sha256_file(verified[screenshot_ref]) != evidence.get("screenshot_sha256")
        or evidence.get("screen") != expected_screen
    ):
        raise AgentError(f"menu smoke {label} observation artifact differs")
    try:
        archived = json.loads(verified[observation_ref].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"menu smoke {label} observation cannot be parsed: {error}") from error
    observation = archived.get("policy_observation") if isinstance(archived, dict) else None
    private = archived.get("private_audit") if isinstance(archived, dict) else None
    if isinstance(observation, dict):
        _validate_json_schema(observation, OBSERVATION_SCHEMA, f"{label} observation")
    process_binding = window_binding.get("process")
    window = window_binding.get("window")
    if (
        not isinstance(archived, dict)
        or set(archived) != {"format_version", "policy_observation", "private_audit"}
        or archived.get("format_version") != 2
        or not isinstance(observation, dict)
        or not isinstance(private, dict)
        or set(private)
        != {
            "process",
            "client_rect",
            "screenshot_path",
            "observation_path",
            "capture_sequence",
            "captured_monotonic",
            "capture_started_at",
        }
        or observation.get("format_version") != 2
        or observation.get("policy_boundary")
        != "player-visible pixels and OCR only"
        or not isinstance(process_binding, dict)
        or not isinstance(window, dict)
        or observation.get("observation_id") != evidence.get("observation_id")
        or observation.get("frame_id") != evidence.get("frame_id")
        or observation.get("captured_at") != evidence.get("captured_at")
        or observation.get("screen") != expected_screen
        or observation.get("image")
        != {
            "ref": f"frame:{evidence.get('frame_id')}",
            "sha256": evidence.get("screenshot_sha256"),
            "width": getattr(contract, "resolution", (None, None))[0],
            "height": getattr(contract, "resolution", (None, None))[1],
        }
        or private.get("process")
        != {"pid": evidence.get("pid"), "hwnd": evidence.get("hwnd")}
        or private.get("client_rect") != evidence.get("client_rect")
        or private.get("capture_sequence") != evidence.get("capture_sequence")
        or private.get("captured_monotonic") != evidence.get("captured_monotonic")
        or private.get("screenshot_path") != screenshot_ref
        or private.get("observation_path") != observation_ref
        or evidence.get("pid") != process_binding.get("pid")
        or evidence.get("hwnd") != window.get("hwnd")
        or evidence.get("client_rect") != window.get("client_rect")
    ):
        raise AgentError(f"menu smoke {label} observation binding differs")
    replayed = _replay_visible_frame(verified[screenshot_ref], contract)
    archived_controls = observation.get("visible_controls")
    replayed_controls = replayed.pop("visible_controls")
    if not isinstance(archived_controls, list):
        raise AgentError(f"menu smoke {label} visible controls differ")
    normalized_controls: list[dict[str, object]] = []
    for control in archived_controls:
        if (
            not isinstance(control, dict)
            or not re.fullmatch(r"[0-9a-f]{64}", str(control.get("control_token", "")))
        ):
            raise AgentError(f"menu smoke {label} control token differs")
        normalized_controls.append(
            {key: control.get(key) for key in ("control_id", "label", "bbox", "center")}
        )
    archived_replay = {
        key: observation.get(key)
        for key in (
            "screen",
            "ocr",
            "visible_anchors",
            "visible_facts",
            "confidence",
            "unknown_reasons",
        )
    }
    if archived_replay != replayed or normalized_controls != replayed_controls:
        raise AgentError(f"menu smoke {label} PNG/OCR replay differs")
    return observation


def _memory_image_sha256(image: object) -> str:
    mode = str(getattr(image, "mode", ""))
    size = tuple(getattr(image, "size", ()))
    tobytes = getattr(image, "tobytes", None)
    if not mode or len(size) != 2 or not callable(tobytes):
        raise AgentError("menu smoke target patch is not a concrete raster image")
    digest = hashlib.sha256()
    digest.update(f"{mode}:{size[0]}x{size[1]}\0".encode("ascii"))
    digest.update(tobytes())
    return digest.hexdigest()


def _validate_navigation_success(
    navigation: object,
    *,
    verified: dict[str, Path],
    contract: object,
    process: object,
    environment: dict[str, object],
    require_complete_durable_events: bool = True,
    require_responsive_gate: bool = True,
) -> None:
    if not isinstance(navigation, dict):
        raise AgentError("menu smoke navigation attestation is missing")
    if navigation.get("claim") != "visible_main_menu_to_bookmark_lobby_only":
        raise AgentError("menu smoke navigation claim differs")
    start = navigation.get("start_observation")
    if not isinstance(start, dict) or start.get("screen") != "main_menu":
        raise AgentError("menu smoke did not start from the visible main menu")
    window_binding = navigation.get("window_binding")
    start_audit = navigation.get("start_observation_audit")
    if not isinstance(window_binding, dict):
        raise AgentError("menu smoke window binding is missing")
    _validate_window_binding(window_binding, process, environment)
    binding_process = window_binding.get("process")
    binding_window = window_binding.get("window")
    pre_resume_inventory = (
        process.get("pre_resume_ck3_inventory")
        if isinstance(process, dict)
        else None
    )
    pre_resume_processes = (
        pre_resume_inventory.get("processes")
        if isinstance(pre_resume_inventory, dict)
        else None
    )
    pre_resume_parent = (
        pre_resume_processes[0].get("parent_pid")
        if isinstance(pre_resume_processes, list)
        and len(pre_resume_processes) == 1
        and isinstance(pre_resume_processes[0], dict)
        else None
    )
    _validate_foreground_activation(
        navigation.get("foreground_activation"),
        process=process,
        expected_hwnd=(
            binding_window.get("hwnd") if isinstance(binding_window, dict) else None
        ),
        require_responsive_gate=require_responsive_gate,
    )
    bound_executable = Path(str(binding_process.get("executable", ""))) if isinstance(binding_process, dict) else Path()
    handle_executable = Path(str(binding_process.get("handle_executable", ""))) if isinstance(binding_process, dict) else Path()
    wmi_executable = str(binding_process.get("wmi_executable", "")) if isinstance(binding_process, dict) else ""
    game = environment.get("game")
    archived_executable = Path(str(game.get("executable", ""))) if isinstance(game, dict) else Path()
    expected_arguments = [
        str(archived_executable),
        "-gdpr-compliant",
        f"-userdir={environment.get('profile_dir')}",
    ]
    if (
        not isinstance(process, dict)
        or type(process.get("pid")) is not int
        or process["pid"] <= 0
        or not isinstance(process.get("creation_date"), str)
        or not process["creation_date"]
        or process.get("debug_mode") is not False
        or process.get("arguments") != expected_arguments
        or not Path(str(process.get("executable", ""))).is_absolute()
        or Path(str(process.get("executable", ""))).name.casefold() != "ck3.exe"
        or Path(str(process.get("executable"))).resolve()
        != archived_executable.resolve()
        or not isinstance(binding_process, dict)
        or not isinstance(binding_window, dict)
        or binding_process.get("pid") != process.get("pid")
        or binding_process.get("creation_date") != process.get("creation_date")
        or binding_process.get("executable") != process.get("executable")
        or binding_process.get("name") != "ck3.exe"
        or type(binding_process.get("parent_pid")) is not int
        or binding_process["parent_pid"] <= 0
        or pre_resume_parent != binding_process.get("parent_pid")
        or handle_executable.resolve() != bound_executable.resolve()
        or (
            wmi_executable
            and Path(wmi_executable).resolve() != bound_executable.resolve()
        )
        or type(binding_window.get("hwnd")) is not int
        or binding_window["hwnd"] <= 0
        or binding_window.get("client_size") != [2560, 1440]
        or not isinstance(binding_window.get("client_rect"), list)
        or len(binding_window["client_rect"]) != 4
        or binding_window["client_rect"][2] - binding_window["client_rect"][0]
        != 2560
        or binding_window["client_rect"][3] - binding_window["client_rect"][1]
        != 1440
    ):
        raise AgentError("menu smoke process/window binding differs")
    _validate_stable_audit(
        start,
        start_audit,
        screen="main_menu",
        verified=verified,
        window_binding=window_binding,
        contract=contract,
    )
    controls = start.get("visible_controls")
    if (
        not isinstance(controls, list)
        or len(controls) != 1
        or not isinstance(controls[0], dict)
        or controls[0].get("control_id") != "main_menu.new_game"
    ):
        raise AgentError("menu smoke main-menu capability is not the exact singleton")

    transition = navigation.get("transition")
    if not isinstance(transition, dict):
        raise AgentError("menu smoke transition attestation is missing")
    action = transition.get("action")
    after = transition.get("observation")
    if isinstance(action, dict):
        _validate_json_schema(action, ACTION_RECEIPT_SCHEMA, "action receipt")
    if (
        not isinstance(action, dict)
        or action.get("format_version") != 2
        or action.get("kind") != "click_visible_control"
        or action.get("control_id") != "main_menu.new_game"
        or action.get("expected_post_screen") != "bookmark_lobby"
        or action.get("status") != "confirmed"
        or action.get("input_may_have_occurred") is not True
        or not re.fullmatch(r"[0-9a-f]{32}", str(action.get("action_id", "")))
    ):
        raise AgentError("menu smoke visible action receipt differs")
    if not isinstance(after, dict) or after.get("screen") != "bookmark_lobby":
        raise AgentError("menu smoke did not reach the visible bookmark lobby")
    before_action_audit = action.get("before_stable_observation")
    after_action_audit = action.get("after_stable_observation")
    if before_action_audit != start_audit:
        raise AgentError("menu smoke action/start stable audit binding differs")
    _validate_stable_audit(
        after,
        after_action_audit,
        screen="bookmark_lobby",
        verified=verified,
        window_binding=window_binding,
        contract=contract,
    )
    if action.get("result_observation_id") != after.get("observation_id"):
        raise AgentError("menu smoke action result observation binding differs")

    registered = navigation.get("registered_capabilities")
    forbidden = navigation.get("forbidden_capabilities")
    if registered != ["main_menu.new_game"]:
        raise AgentError("menu smoke registered capability set differs")
    if forbidden != ["bookmark_lobby.start_game"]:
        raise AgentError("menu smoke forbidden capability set differs")
    if navigation.get("start_game_capability_registered") is not False:
        raise AgentError("menu smoke registered a forbidden start-game capability")
    target = action.get("target")
    send_input = action.get("send_input")
    durable = action.get("durable_events")
    action_binding = action.get("binding")
    binding_after = action.get("binding_after")
    if not isinstance(action_binding, dict) or not isinstance(binding_after, dict):
        raise AgentError("menu smoke action window binding is missing")
    _validate_window_binding(action_binding, process, environment)
    _validate_window_binding(binding_after, process, environment)
    if not (
        _window_binding_core(action_binding)
        == _window_binding_core(binding_after)
        == _window_binding_core(window_binding)
    ):
        raise AgentError("menu smoke action window binding core changed")
    control = controls[0]
    token = str(control.get("control_token", ""))
    contract_control = contract.control("main_menu.new_game")
    issued = target.get("issued") if isinstance(target, dict) else None
    fresh = target.get("fresh") if isinstance(target, dict) else None
    hover = target.get("hover") if isinstance(target, dict) else None
    if (
        action.get("contract_sha256") != getattr(contract, "source_sha256", None)
        or action.get("input_budget") != {"limit": 1, "consumed": 1}
        or action.get("pointer_input_may_have_occurred") is not True
        or action.get("button_click_may_have_occurred") is not True
        or not isinstance(target, dict)
        or set(target)
        != {
            "issued",
            "fresh",
            "hover",
            "final_patch_sha256",
            "hover_patch_artifact",
            "final_patch_artifact",
        }
        or not isinstance(issued, dict)
        or not isinstance(fresh, dict)
        or not isinstance(hover, dict)
        or set(issued) != {"text", "normalized", "bbox", "center"}
        or set(fresh)
        != {"text", "normalized", "bbox", "center", "screen_point"}
        or set(hover)
        != {
            "text",
            "normalized",
            "bbox",
            "center",
            "patch_bbox",
            "patch_sha256",
        }
        or hover.get("patch_sha256") != target.get("final_patch_sha256")
        or not isinstance(send_input, dict)
        or send_input != {"requested": 2, "accepted": 2, "last_error": 0}
        or not isinstance(durable, dict)
        or (
            require_complete_durable_events
            and set(durable) != {"planned", "armed", "finished"}
        )
        or (
            not require_complete_durable_events
            and (
                not {"planned", "armed"} <= set(durable)
                or not set(durable) <= {"planned", "armed", "finished"}
            )
        )
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", str(value))
            for value in durable.values()
        )
    ):
        raise AgentError("menu smoke hardened action evidence differs")
    if (
        action.get("risk") != contract_control.risk
        or action.get("policy_boundary")
        != "no caller-supplied coordinates or postconditions"
        or action.get("before_observation_id") != start.get("observation_id")
        or action.get("control_token_sha256")
        != hashlib.sha256(token.encode("ascii")).hexdigest()
        or action.get("receipt_artifact") not in verified
    ):
        raise AgentError("menu smoke action issuance binding differs")

    fresh_observation = _validate_action_observation(
        action.get("fresh_observation"),
        expected_screen="main_menu",
        verified=verified,
        window_binding=window_binding,
        contract=contract,
        label="fresh",
    )
    hover_observation = _validate_action_observation(
        action.get("hover_observation"),
        expected_screen="main_menu",
        verified=verified,
        window_binding=window_binding,
        contract=contract,
        label="hover",
    )
    if (
        action.get("fresh_observation_id")
        != fresh_observation.get("observation_id")
        or action.get("hover_observation_id")
        != hover_observation.get("observation_id")
    ):
        raise AgentError("menu smoke action observation ID binding differs")

    def target_span(
        observation: dict[str, object], value: dict[str, object], label: str
    ) -> dict[str, object]:
        spans = observation.get("ocr")
        if not isinstance(spans, list):
            raise AgentError(f"menu smoke {label} target OCR differs")
        matches = [
            span
            for span in spans
            if isinstance(span, dict)
            and span.get("bbox") == value.get("bbox")
            and span.get("center") == value.get("center")
            and span.get("text") == value.get("text")
            and span.get("normalized") == value.get("normalized")
        ]
        if len(matches) != 1:
            raise AgentError(f"menu smoke {label} target/OCR binding differs")
        return matches[0]

    latest_span = target_span(start, issued, "issued")
    target_span(fresh_observation, fresh, "fresh")
    target_span(hover_observation, hover, "hover")
    client_rect = window_binding["window"]["client_rect"]
    if (
        control.get("bbox") != issued.get("bbox")
        or control.get("center") != issued.get("center")
        or latest_span.get("bbox") != control.get("bbox")
        or abs(int(fresh["center"][0]) - int(issued["center"][0])) > 15
        or abs(int(fresh["center"][1]) - int(issued["center"][1])) > 15
        or abs(int(hover["center"][0]) - int(fresh["center"][0])) > 3
        or abs(int(hover["center"][1]) - int(fresh["center"][1])) > 3
        or fresh.get("screen_point")
        != [
            int(client_rect[0]) + int(fresh["center"][0]),
            int(client_rect[1]) + int(fresh["center"][1]),
        ]
    ):
        raise AgentError("menu smoke target geometry binding differs")
    bbox = hover.get("bbox")
    patch_bbox = hover.get("patch_bbox")
    width, height = contract.resolution
    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
        or patch_bbox
        != [
            max(0, int(bbox[0]) - 12),
            max(0, int(bbox[1]) - 12),
            min(width, int(bbox[2]) + 12),
            min(height, int(bbox[3]) + 12),
        ]
    ):
        raise AgentError("menu smoke hover patch geometry differs")
    hover_evidence = action["hover_observation"]
    from PIL import Image

    try:
        with Image.open(verified[str(hover_evidence["screenshot"])]) as source:
            source.load()
            patch_digest = _memory_image_sha256(source.crop(tuple(patch_bbox)))
    except (OSError, ValueError) as error:
        raise AgentError(f"menu smoke hover patch cannot be replayed: {error}") from error
    if patch_digest != hover.get("patch_sha256"):
        raise AgentError("menu smoke hover patch digest differs")
    patch_pixel_hashes: list[str] = []
    for artifact_label in ("hover_patch_artifact", "final_patch_artifact"):
        artifact = target.get(artifact_label)
        if not isinstance(artifact, dict) or set(artifact) != {
            "path",
            "sha256",
            "pixel_sha256",
        }:
            raise AgentError(f"menu smoke {artifact_label} contract differs")
        relative = artifact.get("path")
        if (
            not isinstance(relative, str)
            or relative not in verified
            or not relative.startswith("artifacts/")
            or artifact.get("sha256") != sha256_file(verified[relative])
        ):
            raise AgentError(f"menu smoke {artifact_label} file binding differs")
        try:
            with Image.open(verified[relative]) as source:
                if (
                    source.format != "PNG"
                    or tuple(source.size)
                    != (
                        int(patch_bbox[2]) - int(patch_bbox[0]),
                        int(patch_bbox[3]) - int(patch_bbox[1]),
                    )
                ):
                    raise AgentError(
                        f"menu smoke {artifact_label} raster contract differs"
                    )
                source.load()
                pixel_hash = _memory_image_sha256(source)
        except AgentError:
            raise
        except (OSError, ValueError) as error:
            raise AgentError(
                f"menu smoke {artifact_label} cannot be replayed: {error}"
            ) from error
        if pixel_hash != artifact.get("pixel_sha256"):
            raise AgentError(f"menu smoke {artifact_label} pixel digest differs")
        patch_pixel_hashes.append(pixel_hash)
    if (
        patch_pixel_hashes
        != [hover.get("patch_sha256"), target.get("final_patch_sha256")]
        or len(set(patch_pixel_hashes)) != 1
    ):
        raise AgentError("menu smoke hover/final patch equivalence differs")

    sequence_evidence = [
        *[frame["capture_sequence"] for frame in start_audit["frames"]],
        action["fresh_observation"]["capture_sequence"],
        action["hover_observation"]["capture_sequence"],
        *[frame["capture_sequence"] for frame in after_action_audit["frames"]],
    ]
    monotonic_evidence = [
        *[float(frame["captured_monotonic"]) for frame in start_audit["frames"]],
        float(action["fresh_observation"]["captured_monotonic"]),
        float(action["hover_observation"]["captured_monotonic"]),
        *[float(frame["captured_monotonic"]) for frame in after_action_audit["frames"]],
    ]
    if (
        any(right != left + 1 for left, right in zip(sequence_evidence, sequence_evidence[1:]))
        or any(right <= left for left, right in zip(monotonic_evidence, monotonic_evidence[1:]))
    ):
        raise AgentError("menu smoke full capture sequence differs")


def _action_receipts(verified: dict[str, Path]) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for relative, path in verified.items():
        if not relative.startswith("artifacts/") or path.suffix.casefold() != ".json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("kind") == "click_visible_control":
            receipts.append(payload)
    return receipts


def _validate_release_manifest_archive(
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
        raise AgentError("archived production manifest schema differs")
    mod = environment.get("mod")
    identity = mod.get("release_identity") if isinstance(mod, dict) else None
    if (
        not isinstance(mod, dict)
        or not isinstance(identity, dict)
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
    projected: dict[str, dict[str, object]] = {}
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
            or relative.as_posix() != entry.get("path")
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or type(size) is not int
            or size < 0
        ):
            raise AgentError("archived production manifest file entry differs")
        path = relative.as_posix()
        paths.append(path)
        projected[path] = {"size": size, "sha256": digest}
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise AgentError("archived production manifest paths differ")
    if not {
        "descriptor.mod",
        "common/game_rules/xar_game_rules.txt",
        "common/on_action/eternal_recurrence_on_actions.txt",
        "events/xar_events.txt",
    } <= set(paths):
        raise AgentError("archived production manifest lacks required runtime files")
    if (
        len(files) != mod.get("production_file_count")
        or snapshot_digest(projected) != mod.get("production_tree_sha256")
    ):
        raise AgentError("archived production manifest tree digest differs")


def _validate_archived_environment(
    report: dict[str, object], verified: dict[str, Path]
) -> dict[str, object]:
    try:
        environment = json.loads(
            verified["environment.json"].read_text(encoding="utf-8")
        )
        production = json.loads(
            verified["production.manifest.json"].read_text(encoding="utf-8")
        )
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"menu smoke archived environment cannot be parsed: {error}") from error
    if (
        not isinstance(environment, dict)
        or environment.get("environment_sha256") != _contract_digest(environment)
        or environment.get("environment_sha256") != report.get("environment_sha256")
    ):
        raise AgentError("menu smoke archived environment digest differs")
    state_dir = Path(str(environment.get("state_dir", "")))
    profile_dir = Path(str(environment.get("profile_dir", "")))
    if (
        not state_dir.is_absolute()
        or not profile_dir.is_absolute()
        or profile_dir.resolve() != (state_dir / "profile").resolve()
    ):
        raise AgentError("menu smoke archived environment topology differs")
    mod = environment.get("mod")
    display = environment.get("display")
    game = environment.get("game")
    runtime = environment.get("agent_runtime")
    load_profile = environment.get("load_profile")
    legality = environment.get("legality")
    rules = environment.get("rules")
    dlc = environment.get("dlc")
    agent_git = runtime.get("git") if isinstance(runtime, dict) else None
    source_provenance = mod.get("source_provenance") if isinstance(mod, dict) else None
    files = runtime.get("files") if isinstance(runtime, dict) else None
    runtime_files = {
        str(item.get("path")): item
        for item in files or []
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    matches = [runtime_files.get(UI_CONTRACT_AGENT_RUNTIME_PATH)]
    schema_bindings = (
        (OBSERVATION_SCHEMA_AGENT_RUNTIME_PATH, OBSERVATION_SCHEMA),
        (ACTION_RECEIPT_SCHEMA_AGENT_RUNTIME_PATH, ACTION_RECEIPT_SCHEMA),
    )
    contract = report.get("ui_contract")
    runtime_without_hash = dict(runtime) if isinstance(runtime, dict) else {}
    runtime_hash = runtime_without_hash.pop("sha256", None)
    allowed_mounts = dlc.get("allowed_mount_roots") if isinstance(dlc, dict) else None
    profile = rules.get("profile") if isinstance(rules, dict) else None
    expected_mod_profile = [
        {"rule": rule, "setting": setting} for rule, setting in MOD_RULES
    ]
    if (
        not isinstance(mod, dict)
        or mod.get("name") != EXPECTED_MOD_NAME
        or Path(str(mod.get("production_path", ""))).resolve()
        != (profile_dir / "mod-content" / "xar-production").resolve()
        or not isinstance(display, dict)
        or display.get("language") != "l_simp_chinese"
        or display.get("resolution") != [2560, 1440]
        or display.get("mode") != "fullscreen"
        or not isinstance(game, dict)
        or game.get("raw_version") != "1.19.0.6"
        or game.get("debug_mode") is not False
        or not isinstance(load_profile, dict)
        or load_profile.get("enabled_mods") != [OUTER_DESCRIPTOR_REF]
        or load_profile.get("disabled_dlcs") != []
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
        or not isinstance(dlc, dict)
        or not isinstance(allowed_mounts, list)
        or any(
            not isinstance(path, str) or not Path(path).is_absolute()
            for path in allowed_mounts
        )
        or allowed_mounts != sorted(set(allowed_mounts))
        or snapshot_digest(allowed_mounts)
        != dlc.get("allowed_mount_roots_sha256")
        or len(allowed_mounts) != dlc.get("installed_descriptor_count")
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(dlc.get("installed_descriptors_sha256", ""))
        )
        or not isinstance(runtime, dict)
        or not isinstance(agent_git, dict)
        or set(agent_git)
        != {
            "selected_runtime_revision",
            "all_files_tracked",
            "untracked_runtime_files",
            "dirty",
            "status",
        }
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(agent_git.get("selected_runtime_revision", ""))
        )
        or agent_git.get("all_files_tracked") is not True
        or agent_git.get("untracked_runtime_files") != []
        or agent_git.get("dirty") is not False
        or agent_git.get("status") != []
        or not isinstance(source_provenance, dict)
        or set(source_provenance)
        != {
            "git_revision",
            "git_tags_at_revision",
            "git_dirty",
            "git_status",
            "all_release_files_tracked",
            "untracked_release_files",
            "release_source_file_count",
            "release_source_sha256",
        }
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(source_provenance.get("git_revision", ""))
        )
        or source_provenance.get("git_revision") != mod.get("git_revision")
        or not isinstance(source_provenance.get("git_tags_at_revision"), list)
        or any(
            not isinstance(tag, str) or not tag
            for tag in source_provenance.get("git_tags_at_revision", [])
        )
        or source_provenance.get("git_tags_at_revision")
        != sorted(set(source_provenance.get("git_tags_at_revision", [])))
        or source_provenance.get("git_dirty") is not False
        or source_provenance.get("git_status") != []
        or source_provenance.get("all_release_files_tracked") is not True
        or source_provenance.get("untracked_release_files") != []
        or type(source_provenance.get("release_source_file_count")) is not int
        or source_provenance.get("release_source_file_count", 0) <= 0
        or not re.fullmatch(
            r"[0-9a-f]{64}",
            str(source_provenance.get("release_source_sha256", "")),
        )
        or runtime_hash != snapshot_digest(runtime_without_hash)
        or runtime.get("file_count") != len(files or [])
        or not isinstance(files, list)
        or any(
            not isinstance(entry, dict)
            or set(entry) != {"path", "size", "sha256"}
            or not isinstance(entry.get("path"), str)
            or type(entry.get("size")) is not int
            or entry["size"] < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", "")))
            for entry in files or []
        )
        or [entry["path"] for entry in files or []]
        != sorted({entry["path"] for entry in files or []})
        or len(matches) != 1
        or not isinstance(matches[0], dict)
        or not isinstance(contract, dict)
        or matches[0].get("sha256") != contract.get("sha256")
        or matches[0].get("size") != contract.get("size")
        or any(
            not isinstance(runtime_files.get(label), dict)
            or runtime_files[label].get("sha256") != sha256_file(path)
            or runtime_files[label].get("size") != path.stat().st_size
            for label, path in schema_bindings
        )
        or mod.get("production_manifest_sha256")
        != sha256_file(verified["production.manifest.json"])
    ):
        raise AgentError("menu smoke archived environment semantics differ")
    _validate_release_manifest_archive(production, environment)
    return environment


def _validate_archived_load(
    report: dict[str, object],
    environment: dict[str, object],
    verified: dict[str, Path],
    *,
    require_post_exit: bool = True,
) -> None:
    load = report.get("load_attestation")
    process = report.get("process")
    mod = environment["mod"]
    dlc = environment.get("dlc")
    allowed_mounts = dlc.get("allowed_mount_roots") if isinstance(dlc, dict) else None
    runtime_dlc_mounts = load.get("runtime_dlc_mounts") if isinstance(load, dict) else None
    if (
        not isinstance(load, dict)
        or not isinstance(process, dict)
        or type(process.get("fresh_log_epoch_ns")) is not int
        or not isinstance(process.get("prelaunch_logs_removed"), list)
        or load.get("enabled_mods")
        != [{"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}]
        or load.get("isolated_mod_mounts") != [str(Path(str(mod["production_path"])).resolve())]
        or load.get("unclassified_mounts") != []
        or load.get("session_marker_count") != 1
        or load.get("source")
        != "fresh non-debug boot log, reduced to load attestation only"
        or load.get("policy_boundary")
        != "not available to gameplay perception or strategy"
        or (require_post_exit and load.get("post_exit_revalidated") is not True)
        or not isinstance(allowed_mounts, list)
        or not isinstance(runtime_dlc_mounts, list)
        or any(
            not isinstance(path, str)
            or not Path(path).is_absolute()
            or path not in allowed_mounts
            for path in runtime_dlc_mounts
        )
        or len(runtime_dlc_mounts) != len(set(runtime_dlc_mounts))
    ):
        raise AgentError("menu smoke exact single-mod load proof differs")
    def validate_debug_archive(value: object, relative: str) -> bytes:
        if not isinstance(value, dict) or relative not in verified:
            raise AgentError("menu smoke runtime debug archive is missing")
        source = Path(str(value.get("path", "")))
        captured = value.get("captured_prefix_size")
        file_size = value.get("file_size_after_read")
        if (
            not source.is_absolute()
            or source.resolve()
            != (Path(str(environment["profile_dir"])) / "logs" / "debug.log").resolve()
            or type(captured) is not int
            or captured <= 0
            or type(file_size) is not int
            or file_size < captured
            or type(value.get("mtime_ns")) is not int
            or type(value.get("prelaunch_epoch_ns")) is not int
            or value.get("prelaunch_epoch_ns")
            != process.get("fresh_log_epoch_ns")
            or value["mtime_ns"] < value["prelaunch_epoch_ns"]
            or not isinstance(value.get("cleared_before_launch"), list)
            or value.get("cleared_before_launch")
            != process.get("prelaunch_logs_removed")
            or value.get("archive_path") != relative
            or value.get("archive_sha256") != sha256_file(verified[relative])
        ):
            raise AgentError("menu smoke runtime debug archive binding differs")
        raw = verified[relative].read_bytes()
        if (
            len(raw) != captured
            or hashlib.sha256(raw).hexdigest()
            != value.get("captured_prefix_sha256")
        ):
            raise AgentError("menu smoke runtime debug prefix metadata differs")
        return raw

    debug = load.get("debug_log")
    prefix = validate_debug_archive(debug, "artifacts/runtime-debug-prefix.log")
    archived_load = json.loads(
        verified["artifacts/supervisor-load-attestation.json"].read_text(
            encoding="utf-8"
        )
    )
    if archived_load != load:
        raise AgentError("menu smoke archived load-attestation JSON differs")
    replayed = parse_runtime_attestation(
        prefix.decode("utf-8", errors="ignore"),
        Path(str(environment["profile_dir"])),
        Path(str(mod["production_path"])),
        allowed_dlc_mounts=allowed_mounts,
    )
    for key in (
        "enabled_mods",
        "isolated_mod_mounts",
        "runtime_dlc_mounts",
        "unclassified_mounts",
        "session_marker_count",
        "source",
        "policy_boundary",
    ):
        if replayed.get(key) != load.get(key):
            raise AgentError(f"menu smoke replayed load proof differs for {key}")
    post_exit_debug = load.get("post_exit_debug_log")
    if require_post_exit or post_exit_debug is not None:
        if load.get("post_exit_revalidated") is not True:
            raise AgentError("menu smoke post-exit load proof is not attested")
        final_prefix = validate_debug_archive(
            post_exit_debug, "artifacts/runtime-debug-post-exit.log"
        )
        if len(final_prefix) < len(prefix) or final_prefix[: len(prefix)] != prefix:
            raise AgentError("menu smoke post-exit debug log does not extend its initial prefix")
        final_replayed = parse_runtime_attestation(
            final_prefix.decode("utf-8", errors="ignore"),
            Path(str(environment["profile_dir"])),
            Path(str(mod["production_path"])),
            allowed_dlc_mounts=allowed_mounts,
        )
        for key in (
            "enabled_mods",
            "isolated_mod_mounts",
            "runtime_dlc_mounts",
            "unclassified_mounts",
            "session_marker_count",
            "source",
            "policy_boundary",
        ):
            if final_replayed.get(key) != load.get(key):
                raise AgentError(
                    f"menu smoke post-exit replayed load proof differs for {key}"
                )


def _load_archived_ui_contract(
    report: dict[str, object], verified: dict[str, Path]
) -> object:
    if UI_CONTRACT_ARCHIVE not in verified:
        raise AgentError("menu smoke UI contract archive is missing")
    evidence = report.get("ui_contract")
    if (
        not isinstance(evidence, dict)
        or evidence.get("agent_runtime_path") != UI_CONTRACT_AGENT_RUNTIME_PATH
        or evidence.get("source_repository_relative")
        != UI_CONTRACT_REPOSITORY_RELATIVE.as_posix()
        or evidence.get("archive_path") != UI_CONTRACT_ARCHIVE
        or evidence.get("sha256") != sha256_file(verified[UI_CONTRACT_ARCHIVE])
        or evidence.get("size") != verified[UI_CONTRACT_ARCHIVE].stat().st_size
    ):
        raise AgentError("menu smoke UI contract report binding differs")
    from .vision.classifier import (
        load_ui_contract,
        require_canonical_phase_b_contract,
    )

    contract = load_ui_contract(
        verified[UI_CONTRACT_ARCHIVE],
        expected_sha256=str(evidence["sha256"]),
    )
    require_canonical_phase_b_contract(contract, str(evidence["sha256"]))
    return contract


def _qualification_utc(value: object, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as error:
        raise AgentError(f"menu smoke {label} timestamp differs") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise AgentError(f"menu smoke {label} timestamp is not UTC")
    return parsed


def _legacy_normal_replay_is_non_authorizing_red(
    report: dict[str, object], verified: dict[str, Path]
) -> bool:
    """Narrow v1 compatibility to historical menu runs with zero UI input."""
    if (
        report.get("format_version") != 1
        or report.get("ok") is not False
        or "navigation_attestation" in report
        or "environment.json" not in verified
    ):
        return False
    run_dir = verified["environment.json"].parent
    try:
        rows = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    # Seeing and persisting frames is non-authorizing.  Compatibility stops at
    # the first durable input protocol row or successful lobby transition.
    forbidden_events = {"bookmark_lobby_attested"}
    if any(
        row.get("kind") in forbidden_events
        or str(row.get("kind", "")).startswith("ui_")
        for row in rows
    ):
        return False
    own_authorizing_artifacts = []
    for relative in verified:
        name = Path(relative).name.casefold()
        if relative.startswith("artifacts/") and (
            "action" in name
            or "receipt" in name
            or "navigation" in name
        ):
            own_authorizing_artifacts.append(relative)
    return not own_authorizing_artifacts


def _validate_archived_menu_qualification(
    report: dict[str, object], verified: dict[str, Path]
) -> None:
    qualification = report.get("qualification")
    try:
        normal_finished = _qualification_utc(
            qualification.get("normal_finished_at")
            if isinstance(qualification, dict)
            else None,
            "normal qualification finish",
        )
        crash_started = _qualification_utc(
            qualification.get("crash_started_at")
            if isinstance(qualification, dict)
            else None,
            "crash qualification start",
        )
    except AgentError:
        raise
    if (
        not isinstance(qualification, dict)
        or set(qualification)
        != {
            "environment_sha256",
            "normal",
            "crash",
            "normal_finished_at",
            "crash_started_at",
        }
        or qualification.get("environment_sha256")
        != report.get("environment_sha256")
        or not isinstance(qualification.get("normal_finished_at"), str)
        or not isinstance(qualification.get("crash_started_at"), str)
        or normal_finished >= crash_started
    ):
        raise AgentError("menu smoke qualification envelope differs")
    expected = str(report.get("environment_sha256"))
    reports: dict[str, dict[str, object]] = {}
    from .crash_probe import validate_crash_report

    legacy_normal_allowed = _legacy_normal_replay_is_non_authorizing_red(
        report, verified
    )
    for label, kind in (
        ("normal", "infrastructure_smoke"),
        ("crash", "crash_recovery_smoke"),
    ):
        entry = qualification.get(label)
        if not isinstance(entry, dict) or set(entry) != {
            "run_id",
            "archive_path",
            "report_sha256",
            "events_sha256",
            "validator",
            "prelaunch_validation_passed",
        }:
            raise AgentError(f"menu smoke {label} qualification entry differs")
        run_id = entry.get("run_id")
        archive_path = entry.get("archive_path")
        validator_name = entry.get("validator")
        legacy_normal = (
            label == "normal"
            and validator_name == LEGACY_NORMAL_QUALIFICATION_VALIDATOR
            and legacy_normal_allowed
        )
        expected_validator = (
            NORMAL_V2_QUALIFICATION_VALIDATOR
            if label == "normal" and not legacy_normal
            else (
                LEGACY_NORMAL_QUALIFICATION_VALIDATOR
                if label == "normal"
                else "validate_crash_report"
            )
        )
        expected_path = f"qualification/{label}/runs/{run_id}"
        report_ref = f"{expected_path}/report.json"
        events_ref = f"{expected_path}/events.jsonl"
        if (
            not isinstance(run_id, str)
            or not run_id
            or archive_path != expected_path
            or validator_name != expected_validator
            or entry.get("prelaunch_validation_passed") is not True
            or report_ref not in verified
            or events_ref not in verified
            or entry.get("report_sha256") != sha256_file(verified[report_ref])
            or entry.get("events_sha256") != sha256_file(verified[events_ref])
        ):
            raise AgentError(f"menu smoke {label} qualification archive differs")
        nested_run = verified[report_ref].parent
        try:
            nested = json.loads(verified[report_ref].read_text(encoding="utf-8"))
            if label == "normal":
                replayed = (
                    _validate_normal_qualification(
                        nested_run,
                        expected,
                        allow_legacy_v1_red_replay=True,
                    )
                    if legacy_normal
                    else _validate_normal_qualification(nested_run, expected)
                )
            else:
                replayed = validate_crash_report(nested_run)
        except (AgentError, OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentError(
                f"menu smoke {label} qualification replay failed: {error}"
            ) from error
        if replayed != nested:
            raise AgentError(
                f"menu smoke {label} qualification replay payload differs"
            )
        chain = validate_event_chain(verified[events_ref])
        validate_final_report_payload(nested, chain)
        if (
            not isinstance(nested, dict)
            or nested.get("run_id") != run_id
            or nested.get("kind") != kind
            or (
                label == "normal"
                and nested.get("format_version") != (1 if legacy_normal else 2)
            )
            or nested.get("environment_sha256") != expected
            or nested.get("finalized") is not True
            or nested.get("ok") is not True
            or nested.get("valid_score_episode") is not False
            or nested.get("event_chain")
            != {
                "event_count": chain["event_count"],
                "tail_sha256": chain["tail_sha256"],
            }
        ):
            raise AgentError(f"menu smoke {label} qualification semantics differ")
        reports[label] = nested
    normal = reports["normal"]
    crash = reports["crash"]
    normal_load = normal.get("load_attestation")
    normal_shutdown = normal.get("shutdown_attestation")
    normal_inventory = normal.get("post_shutdown_ck3_inventory")
    crash_attestation = crash.get("crash_attestation")
    if (
        normal.get("finished_at") != qualification.get("normal_finished_at")
        or crash.get("started_at") != qualification.get("crash_started_at")
        or not isinstance(normal_load, dict)
        or normal_load.get("enabled_mods")
        != [{"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}]
        or normal_load.get("unclassified_mounts") != []
        or normal_load.get("post_exit_revalidated") is not True
        or not isinstance(normal_shutdown, dict)
        or normal_shutdown.get("cleanup_proven") is not True
        or normal_shutdown.get("tree_gone") is not True
        or normal_shutdown.get("job_active_processes_final") != 0
        or normal_shutdown.get("watchdog_state_after") != "absent"
        or not isinstance(normal_inventory, dict)
        or normal_inventory.get("processes") != []
        or normal.get("production_tree_unchanged") is not True
        or not isinstance(crash_attestation, dict)
        or crash_attestation.get("cleanup_proven") is not True
        or crash.get("production_tree_unchanged") is not True
    ):
        raise AgentError("menu smoke qualification cleanup/load conjunction differs")


def _validate_process_contract(
    process: object, environment: dict[str, object]
) -> None:
    game = environment.get("game")
    executable = Path(str(game.get("executable", ""))) if isinstance(game, dict) else Path()
    profile_dir = environment.get("profile_dir")
    pre_resume = (
        process.get("pre_resume_ck3_inventory") if isinstance(process, dict) else None
    )
    pre_processes = pre_resume.get("processes") if isinstance(pre_resume, dict) else None
    pre_process = pre_processes[0] if isinstance(pre_processes, list) and len(pre_processes) == 1 else None
    if (
        not isinstance(process, dict)
        or type(process.get("pid")) is not int
        or process["pid"] <= 0
        or not isinstance(process.get("creation_date"), str)
        or not process["creation_date"]
        or not executable.is_absolute()
        or executable.name.casefold() != "ck3.exe"
        or not Path(str(process.get("executable", ""))).is_absolute()
        or Path(str(process.get("executable"))).resolve() != executable.resolve()
        or process.get("arguments")
        != [str(executable), "-gdpr-compliant", f"-userdir={profile_dir}"]
        or process.get("debug_mode") is not False
        or type(process.get("watchdog_pid")) is not int
        or process["watchdog_pid"] <= 0
        or type(process.get("fresh_log_epoch_ns")) is not int
        or process["fresh_log_epoch_ns"] <= 0
        or not isinstance(process.get("prelaunch_logs_removed"), list)
        or not isinstance(pre_resume, dict)
        or set(pre_resume)
        != {"tasklist_returncode", "tasklist_pids", "wmi_pids", "processes"}
        or pre_resume.get("tasklist_returncode") != 0
        or pre_resume.get("tasklist_pids") != [process.get("pid")]
        or pre_resume.get("wmi_pids") != [process.get("pid")]
        or not isinstance(pre_process, dict)
        or set(pre_process)
        != {"pid", "parent_pid", "name", "executable", "creation_date"}
        or pre_process.get("pid") != process.get("pid")
        or type(pre_process.get("parent_pid")) is not int
        or pre_process["parent_pid"] <= 0
        or str(pre_process.get("name", "")).casefold() != "ck3.exe"
        or not same_process_creation_time(
            pre_process.get("creation_date"), process.get("creation_date")
        )
        or (
            pre_process.get("executable")
            and Path(str(pre_process["executable"])).resolve()
            != executable.resolve()
        )
    ):
        raise AgentError("menu smoke launched process contract differs")


def _validate_window_binding(
    binding: object,
    process: object,
    environment: dict[str, object],
) -> None:
    bound_process = binding.get("process") if isinstance(binding, dict) else None
    window = binding.get("window") if isinstance(binding, dict) else None
    expected_executable = Path(str(environment["game"]["executable"]))
    wmi_executable = (
        str(bound_process.get("wmi_executable", ""))
        if isinstance(bound_process, dict)
        else ""
    )
    rect = window.get("client_rect") if isinstance(window, dict) else None
    if (
        not isinstance(process, dict)
        or not isinstance(bound_process, dict)
        or not isinstance(window, dict)
        or bound_process.get("pid") != process.get("pid")
        or bound_process.get("creation_date") != process.get("creation_date")
        or bound_process.get("name") != "ck3.exe"
        or type(bound_process.get("parent_pid")) is not int
        or bound_process["parent_pid"] <= 0
        or Path(str(bound_process.get("executable", ""))).resolve()
        != expected_executable.resolve()
        or Path(str(bound_process.get("handle_executable", ""))).resolve()
        != expected_executable.resolve()
        or (
            wmi_executable
            and Path(wmi_executable).resolve() != expected_executable.resolve()
        )
        or type(window.get("hwnd")) is not int
        or window["hwnd"] <= 0
        or window.get("client_size") != [2560, 1440]
        or not isinstance(rect, list)
        or len(rect) != 4
        or rect[2] - rect[0] != 2560
        or rect[3] - rect[1] != 1440
    ):
        raise AgentError("menu smoke process/window binding differs")


def _window_binding_core(binding: dict[str, object]) -> dict[str, object]:
    """Return fields that must stay stable while WMI path visibility may vary."""
    process = binding.get("process")
    window = binding.get("window")
    if not isinstance(process, dict) or not isinstance(window, dict):
        raise AgentError("menu smoke process/window binding core is missing")
    return {
        "process": {
            key: process.get(key)
            for key in (
                "pid",
                "parent_pid",
                "name",
                "creation_date",
                "executable",
                "handle_executable",
            )
        },
        "window": {
            key: window.get(key)
            for key in ("hwnd", "client_rect", "client_size")
        },
    }


def _validate_pre_mutation_responsive_stability(
    gate: object,
    *,
    process: dict[str, object],
    expected_hwnd: int,
    target_thread: int,
    activation_input_tick: int,
    activation_mode: str,
) -> None:
    """Replay the exact read-only gate that precedes foreground mutation."""
    expected_keys = {
        "format_version",
        "kind",
        "status",
        "started_at",
        "finished_at",
        "started_monotonic_ns",
        "finished_monotonic_ns",
        "timeout_seconds",
        "poll_interval_seconds",
        "wm_null_message",
        "wm_null_timeout_milliseconds",
        "wm_null_flags",
        "required_consecutive_samples",
        "required_span_ns",
        "maximum_sample_gap_ns",
        "last_sample_to_finish_gap_ns",
        "sample_count",
        "confirmation_streak_start_index",
        "confirmation_streak_end_index",
        "confirmation_streak_sample_count",
        "initial_last_input_tick",
        "final_last_input_tick",
        "observed_last_input_tick_unchanged",
        "target",
        "samples",
        "read_only_contract",
        "full_verify_before",
        "full_verify_after",
        "local_identity_revalidated_after",
        "maximum_post_confirmation_gap_ns",
        "first_window_mutation_monotonic_ns",
        "last_window_mutation_monotonic_ns",
        "confirmation_to_last_mutation_gap_ns",
        "confirmation_consumed_monotonic_ns",
        "confirmation_consumption_gap_ns",
        "activation_completed_monotonic_ns",
        "confirmation_completion_gap_ns",
    }
    target_keys = {
        "pid",
        "hwnd",
        "thread_id",
        "client_rect",
        "executable",
        "creation_date",
    }
    sample_keys = {
        "index",
        "observed_at",
        "monotonic_ns",
        "target_pid",
        "target_hwnd",
        "target_thread_id",
        "root_hwnd",
        "client_rect",
        "process_active",
        "handle_pid",
        "handle_executable",
        "bound_creation_date",
        "window_exists",
        "window_visible",
        "window_iconic",
        "last_input_tick_before",
        "last_input_tick_after",
        "wm_null_timeout_milliseconds",
        "wm_null_responded",
        "wm_null_last_error",
        "is_hung_app_window",
        "responsive",
    }
    if not isinstance(gate, dict) or set(gate) != expected_keys:
        raise AgentError("menu smoke responsive gate schema differs")
    target = gate.get("target")
    samples = gate.get("samples")
    timeout_seconds = gate.get("timeout_seconds")
    if (
        gate.get("format_version") != 1
        or gate.get("kind") != "pre_mutation_responsive_stability"
        or gate.get("status") != "confirmed"
        or type(timeout_seconds) is not float
        or not math.isfinite(timeout_seconds)
        or not 0 < timeout_seconds <= 30.0
        or gate.get("poll_interval_seconds") != 0.25
        or gate.get("wm_null_message") != 0
        or gate.get("wm_null_timeout_milliseconds") != 100
        or gate.get("wm_null_flags") != 35
        or gate.get("required_consecutive_samples") != 21
        or gate.get("required_span_ns") != 5_000_000_000
        or gate.get("maximum_sample_gap_ns") != 500_000_000
        or type(gate.get("last_sample_to_finish_gap_ns")) is not int
        or type(gate.get("sample_count")) is not int
        or gate["sample_count"] < 3
        or gate["sample_count"] > math.ceil(timeout_seconds / 0.25) + 1
        or not isinstance(samples, list)
        or len(samples) != gate["sample_count"]
        or type(gate.get("confirmation_streak_start_index")) is not int
        or gate["confirmation_streak_start_index"] < 1
        or gate.get("confirmation_streak_end_index") != gate["sample_count"]
        or type(gate.get("confirmation_streak_sample_count")) is not int
        or gate["confirmation_streak_sample_count"]
        != gate["confirmation_streak_end_index"]
        - gate["confirmation_streak_start_index"]
        + 1
        or gate["confirmation_streak_sample_count"] < 21
        or gate.get("initial_last_input_tick") != activation_input_tick
        or gate.get("final_last_input_tick") != activation_input_tick
        or gate.get("observed_last_input_tick_unchanged") is not True
        or gate.get("full_verify_before") is not True
        or gate.get("full_verify_after") is not False
        or gate.get("local_identity_revalidated_after") is not True
        or gate.get("maximum_post_confirmation_gap_ns") != 500_000_000
        or not isinstance(target, dict)
        or set(target) != target_keys
        or target.get("pid") != process.get("pid")
        or target.get("hwnd") != expected_hwnd
        or target.get("thread_id") != target_thread
        or target.get("client_rect") != [0, 0, 2560, 1440]
        or target.get("creation_date") != process.get("creation_date")
        or Path(str(target.get("executable", ""))).resolve()
        != Path(str(process.get("executable", ""))).resolve()
        or gate.get("read_only_contract")
        != {
            "set_foreground_window_calls": 0,
            "attach_thread_input_calls": 0,
            "synthetic_input_calls": 0,
            "window_close_calls": 0,
            "desktop_enumeration_calls": 0,
            "wmi_queries": 0,
        }
    ):
        raise AgentError("menu smoke responsive gate contract differs")
    timestamp_pattern = (
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00"
    )
    parsed_times: dict[str, datetime] = {}
    for label in ("started_at", "finished_at"):
        value = gate.get(label)
        if not isinstance(value, str) or re.fullmatch(timestamp_pattern, value) is None:
            raise AgentError("menu smoke responsive gate timestamp differs")
        try:
            parsed_times[label] = datetime.fromisoformat(value)
        except ValueError as error:
            raise AgentError("menu smoke responsive gate timestamp differs") from error
    started_ns = gate.get("started_monotonic_ns")
    finished_ns = gate.get("finished_monotonic_ns")
    mutation_ns = gate.get("first_window_mutation_monotonic_ns")
    last_mutation_ns = gate.get("last_window_mutation_monotonic_ns")
    last_mutation_gap_ns = gate.get("confirmation_to_last_mutation_gap_ns")
    consumed_ns = gate.get("confirmation_consumed_monotonic_ns")
    consumption_gap_ns = gate.get("confirmation_consumption_gap_ns")
    completed_ns = gate.get("activation_completed_monotonic_ns")
    completion_gap_ns = gate.get("confirmation_completion_gap_ns")
    if (
        parsed_times["finished_at"] < parsed_times["started_at"]
        or type(started_ns) is not int
        or started_ns <= 0
        or type(finished_ns) is not int
        or finished_ns < started_ns
        or finished_ns > started_ns + int(timeout_seconds * 1_000_000_000)
        or gate["last_sample_to_finish_gap_ns"]
        != finished_ns - samples[-1]["monotonic_ns"]
        or not 0 <= gate["last_sample_to_finish_gap_ns"] <= 500_000_000
        or type(consumed_ns) is not int
        or type(consumption_gap_ns) is not int
        or consumed_ns - finished_ns != consumption_gap_ns
        or not 0 <= consumption_gap_ns <= 500_000_000
        or type(completed_ns) is not int
        or type(completion_gap_ns) is not int
        or completed_ns - finished_ns != completion_gap_ns
        or not 0 <= completion_gap_ns <= 500_000_000
        or consumed_ns > completed_ns
        or (
            activation_mode == "already_foreground"
            and (
                mutation_ns is not None
                or last_mutation_ns is not None
                or last_mutation_gap_ns is not None
                or consumed_ns != completed_ns
            )
        )
        or (
            activation_mode in {"direct", "attached_fallback"}
            and (
                type(mutation_ns) is not int
                or mutation_ns != consumed_ns
                or type(last_mutation_ns) is not int
                or type(last_mutation_gap_ns) is not int
                or last_mutation_ns - finished_ns != last_mutation_gap_ns
                or not 0 <= last_mutation_gap_ns <= 500_000_000
                or last_mutation_ns < mutation_ns
                or last_mutation_ns > completed_ns
            )
        )
    ):
        raise AgentError("menu smoke responsive gate chronology differs")
    prior_ns = started_ns - 1
    for index, sample in enumerate(samples, start=1):
        if not isinstance(sample, dict) or set(sample) != sample_keys:
            raise AgentError("menu smoke responsive gate sample schema differs")
        observed_at = sample.get("observed_at")
        try:
            parsed_observed_at = datetime.fromisoformat(str(observed_at))
        except ValueError as error:
            raise AgentError("menu smoke responsive gate sample time differs") from error
        sample_ns = sample.get("monotonic_ns")
        responded = sample.get("wm_null_responded")
        hung = sample.get("is_hung_app_window")
        if (
            not isinstance(observed_at, str)
            or re.fullmatch(timestamp_pattern, observed_at) is None
            or not parsed_times["started_at"]
            <= parsed_observed_at
            <= parsed_times["finished_at"]
            or sample.get("index") != index
            or type(sample_ns) is not int
            or sample_ns <= prior_ns
            or (
                index > 1
                and sample_ns - prior_ns < 250_000_000
            )
            or sample_ns > finished_ns
            or sample.get("target_pid") != process.get("pid")
            or sample.get("target_hwnd") != expected_hwnd
            or sample.get("target_thread_id") != target_thread
            or sample.get("root_hwnd") != expected_hwnd
            or sample.get("client_rect") != [0, 0, 2560, 1440]
            or sample.get("process_active") is not True
            or sample.get("handle_pid") != process.get("pid")
            or Path(str(sample.get("handle_executable", ""))).resolve()
            != Path(str(process.get("executable", ""))).resolve()
            or sample.get("bound_creation_date") != process.get("creation_date")
            or sample.get("window_exists") is not True
            or sample.get("window_visible") is not True
            or sample.get("window_iconic") is not False
            or sample.get("last_input_tick_before") != activation_input_tick
            or sample.get("last_input_tick_after") != activation_input_tick
            or type(sample.get("wm_null_timeout_milliseconds")) is not int
            or not 1 <= sample["wm_null_timeout_milliseconds"] <= 100
            or type(responded) is not bool
            or type(hung) is not bool
            or type(sample.get("wm_null_last_error")) is not int
            or sample["wm_null_last_error"] < 0
            or (responded and sample["wm_null_last_error"] != 0)
            or sample.get("responsive") is not (responded and not hung)
        ):
            raise AgentError("menu smoke responsive gate sample differs")
        prior_ns = sample_ns
    confirmed = samples[gate["confirmation_streak_start_index"] - 1 :]
    if (
        any(item.get("responsive") is not True for item in confirmed)
        or any(
            confirmed[index]["monotonic_ns"]
            - confirmed[index - 1]["monotonic_ns"]
            > 500_000_000
            for index in range(1, len(confirmed))
        )
        or confirmed[-1]["monotonic_ns"] - confirmed[0]["monotonic_ns"]
        < 5_000_000_000
        or (
            gate["confirmation_streak_start_index"] > 1
            and samples[gate["confirmation_streak_start_index"] - 2].get(
                "responsive"
            )
            is True
            and confirmed[0]["monotonic_ns"]
            - samples[gate["confirmation_streak_start_index"] - 2][
                "monotonic_ns"
            ]
            <= 500_000_000
        )
        or confirmed[0]["monotonic_ns"] < started_ns
        or confirmed[-1]["monotonic_ns"]
        > started_ns + int(timeout_seconds * 1_000_000_000)
    ):
        raise AgentError("menu smoke responsive gate confirmation differs")


def _validate_foreground_activation(
    attestation: object,
    *,
    process: object,
    expected_hwnd: object,
    require_responsive_gate: bool,
) -> None:
    """Validate the exact no-synthetic-input foreground transaction."""
    expected_keys = {
        "format_version",
        "target_pid",
        "target_hwnd",
        "target_thread_id",
        "caller_thread_id",
        "foreground_hwnd_before",
        "foreground_thread_id_before",
        "foreground_pid_before",
        "last_input_tick_before",
        "synthetic_input",
        "mode",
        "attached_fallback",
        "detach_succeeded",
        "foreground_hwnd_after",
        "foreground_thread_id_after",
        "foreground_pid_after",
        "last_input_tick_after",
        "observed_last_input_tick_unchanged",
    }
    if isinstance(attestation, dict) and "pre_mutation_responsive_stability" in attestation:
        expected_keys.add("pre_mutation_responsive_stability")
    if (
        not isinstance(attestation, dict)
        or set(attestation) != expected_keys
        or not isinstance(process, dict)
        or type(expected_hwnd) is not int
        or expected_hwnd <= 0
        or attestation.get("format_version") != 1
        or attestation.get("target_pid") != process.get("pid")
        or attestation.get("target_hwnd") != expected_hwnd
        or type(attestation.get("target_thread_id")) is not int
        or attestation["target_thread_id"] <= 0
        or type(attestation.get("caller_thread_id")) is not int
        or attestation["caller_thread_id"] <= 0
        or type(attestation.get("foreground_hwnd_before")) is not int
        or attestation["foreground_hwnd_before"] < 0
        or type(attestation.get("foreground_thread_id_before")) is not int
        or attestation["foreground_thread_id_before"] < 0
        or type(attestation.get("foreground_pid_before")) is not int
        or attestation["foreground_pid_before"] < 0
        or type(attestation.get("last_input_tick_before")) is not int
        or attestation["last_input_tick_before"] < 0
        or attestation.get("synthetic_input") is not False
        or attestation.get("foreground_hwnd_after") != expected_hwnd
        or attestation.get("foreground_thread_id_after")
        != attestation.get("target_thread_id")
        or attestation.get("foreground_pid_after") != process.get("pid")
        or attestation.get("last_input_tick_after")
        != attestation.get("last_input_tick_before")
        or attestation.get("observed_last_input_tick_unchanged") is not True
    ):
        raise AgentError("menu smoke foreground activation attestation differs")
    mode = attestation.get("mode")
    before_is_target = (
        attestation.get("foreground_hwnd_before") == expected_hwnd
        and attestation.get("foreground_thread_id_before")
        == attestation.get("target_thread_id")
        and attestation.get("foreground_pid_before") == process.get("pid")
    )
    before_all_zero = (
        attestation.get("foreground_hwnd_before") == 0
        and attestation.get("foreground_thread_id_before") == 0
        and attestation.get("foreground_pid_before") == 0
    )
    before_all_positive = (
        attestation.get("foreground_hwnd_before") > 0
        and attestation.get("foreground_thread_id_before") > 0
        and attestation.get("foreground_pid_before") > 0
    )
    if mode == "already_foreground":
        valid_mode = (
            before_is_target
            and attestation.get("attached_fallback") is False
            and attestation.get("detach_succeeded") is None
        )
    elif mode == "direct":
        valid_mode = (
            not before_is_target
            and (before_all_zero or before_all_positive)
            and attestation.get("attached_fallback") is False
            and attestation.get("detach_succeeded") is None
        )
    elif mode == "attached_fallback":
        valid_mode = (
            not before_is_target
            and before_all_positive
            and attestation.get("foreground_thread_id_before")
            != attestation.get("caller_thread_id")
            and attestation.get("attached_fallback") is True
            and attestation.get("detach_succeeded") is True
        )
    else:
        valid_mode = False
    if not valid_mode:
        raise AgentError("menu smoke foreground activation mode differs")
    responsive_gate = attestation.get("pre_mutation_responsive_stability")
    if responsive_gate is None:
        if require_responsive_gate:
            raise AgentError("menu smoke responsive gate attestation is missing")
    else:
        _validate_pre_mutation_responsive_stability(
            responsive_gate,
            process=process,
            expected_hwnd=expected_hwnd,
            target_thread=attestation["target_thread_id"],
            activation_input_tick=attestation["last_input_tick_before"],
            activation_mode=str(attestation["mode"]),
        )


def _validate_foreground_events(
    report: dict[str, object], rows: list[dict[str, object]]
) -> None:
    by_kind = {
        str(row.get("kind")): row
        for row in rows
        if str(row.get("kind", "")).startswith("foreground_activation_")
    }
    process = report.get("process")
    planned = by_kind.get("foreground_activation_planned")
    armed = by_kind.get("foreground_activation_armed")
    finished = by_kind.get("foreground_activation_finished")
    if not by_kind:
        return
    if not isinstance(process, dict) or planned is None:
        raise AgentError("menu smoke foreground event lacks its process/planned proof")
    envelope_keys = {"at", "previous_event_sha256", "event_sha256", "kind"}
    if set(planned) != envelope_keys | {
        "pid",
        "hwnd",
        "operation",
        "synthetic_input",
    }:
        raise AgentError("menu smoke foreground planned event schema differs")
    if (
        planned.get("pid") != process.get("pid")
        or type(planned.get("hwnd")) is not int
        or planned["hwnd"] <= 0
        or planned.get("operation") != FOREGROUND_OPERATION
        or planned.get("synthetic_input") is not False
    ):
        raise AgentError("menu smoke foreground planned event differs")
    if armed is not None:
        if set(armed) != envelope_keys | {
            "pid",
            "hwnd",
            "operation",
            "foreground_may_have_changed",
            "synthetic_input_may_have_occurred",
        }:
            raise AgentError("menu smoke foreground armed event schema differs")
        if (
            armed.get("pid") != process.get("pid")
            or armed.get("hwnd") != planned.get("hwnd")
            or armed.get("operation") != FOREGROUND_OPERATION
            or armed.get("foreground_may_have_changed") is not True
            or armed.get("synthetic_input_may_have_occurred") is not False
        ):
            raise AgentError("menu smoke foreground armed event differs")
    if finished is not None:
        if set(finished) != envelope_keys | {
            "pid",
            "hwnd",
            "status",
            "attestation",
        }:
            raise AgentError("menu smoke foreground finished event schema differs")
        if armed is None or (
            finished.get("pid") != process.get("pid")
            or finished.get("hwnd") != planned.get("hwnd")
            or finished.get("status") != "confirmed"
        ):
            raise AgentError("menu smoke foreground finished event differs")
        _validate_foreground_activation(
            finished.get("attestation"),
            process=process,
            expected_hwnd=planned.get("hwnd"),
            require_responsive_gate=(
                report.get("foreground_protocol_version")
                == FOREGROUND_PROTOCOL_VERSION
            ),
        )
    navigation = report.get("navigation_attestation")
    if navigation is not None:
        if not isinstance(navigation, dict) or finished is None:
            raise AgentError("menu smoke navigation lacks foreground completion")
        if navigation.get("foreground_activation") != finished.get("attestation"):
            raise AgentError("menu smoke navigation/foreground event binding differs")


def _validate_foreground_loss_evidence(
    report: dict[str, object],
    rows: list[dict[str, object]],
    verified: dict[str, Path],
) -> None:
    """Replay a detection-time foreground snapshot without live backfilling."""
    loss_rows = [row for row in rows if row.get("kind") == "foreground_lost"]
    loss_artifacts = [
        relative
        for relative in verified
        if re.fullmatch(
            r"artifacts/foreground-loss-[0-9a-f]{32}\.json", relative
        )
    ]
    descriptor = report.get("foreground_loss")
    if not loss_rows and not loss_artifacts and descriptor is None:
        # Historical v1 RED reports predate typed loss evidence.
        if report.get("error_type") == "ForegroundLossError":
            raise AgentError(
                "menu smoke typed foreground loss lacks its evidence set"
            )
        return
    if (
        len(loss_rows) != 1
        or len(loss_artifacts) != 1
        or not isinstance(descriptor, dict)
        or set(descriptor)
        != {
            "format_version",
            "snapshot_id",
            "artifact_path",
            "artifact_sha256",
            "artifact_size",
            "snapshot_sha256",
            "event_sha256",
        }
        or descriptor.get("format_version") != 1
        or report.get("error_type") != "ForegroundLossError"
        or report.get("error")
        != (
            "runtime: ForegroundLossError: bound CK3 client lost "
            "foreground; refusing input"
        )
    ):
        raise AgentError("menu smoke foreground-loss evidence set differs")
    row = loss_rows[0]
    envelope = {"at", "previous_event_sha256", "event_sha256", "kind"}
    if set(row) != envelope | {
        "snapshot_id",
        "artifact_path",
        "artifact_sha256",
        "artifact_size",
        "snapshot_sha256",
        "target_pid",
        "target_hwnd",
        "foreground_status",
        "foreground_root_hwnd",
        "foreground_pid",
        "checkpoint",
        "synthetic_input",
        "reusable_authorization",
    }:
        raise AgentError("menu smoke foreground-loss event schema differs")
    relative = descriptor.get("artifact_path")
    if (
        not isinstance(relative, str)
        or relative != loss_artifacts[0]
        or relative
        != f"artifacts/foreground-loss-{descriptor.get('snapshot_id')}.json"
        or relative not in verified
        or row.get("artifact_path") != relative
        or descriptor.get("event_sha256") != row.get("event_sha256")
        or descriptor.get("snapshot_id") != row.get("snapshot_id")
        or descriptor.get("artifact_sha256") != row.get("artifact_sha256")
        or descriptor.get("artifact_size") != row.get("artifact_size")
        or descriptor.get("snapshot_sha256") != row.get("snapshot_sha256")
        or row.get("synthetic_input") is not False
        or row.get("reusable_authorization") is not False
    ):
        raise AgentError("menu smoke foreground-loss report/event binding differs")
    raw = verified[relative].read_bytes()
    try:
        snapshot = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"menu smoke foreground-loss artifact cannot be parsed: {error}"
        ) from error
    canonical = (
        json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    if (
        not isinstance(snapshot, dict)
        or raw != canonical
        or descriptor.get("artifact_sha256") != hashlib.sha256(raw).hexdigest()
        or descriptor.get("artifact_size") != len(raw)
        or descriptor.get("snapshot_sha256") != snapshot_digest(snapshot)
    ):
        raise AgentError("menu smoke foreground-loss artifact binding differs")
    snapshot_keys = {
        "format_version",
        "kind",
        "snapshot_id",
        "observed_at",
        "observed_monotonic_ns",
        "checkpoint",
        "capture_sequence",
        "expected_screen",
        "last_input_tick",
        "instantaneous_observation_only",
        "reusable_authorization",
        "synthetic_input",
        "target",
        "foreground",
    }
    target = snapshot.get("target")
    foreground = snapshot.get("foreground")
    process = report.get("process")
    if (
        set(snapshot) != snapshot_keys
        or snapshot.get("format_version") != 1
        or snapshot.get("kind") != "foreground_loss_snapshot"
        or not re.fullmatch(
            r"[0-9a-f]{32}", str(snapshot.get("snapshot_id", ""))
        )
        or snapshot.get("snapshot_id") != descriptor.get("snapshot_id")
        or snapshot.get("instantaneous_observation_only") is not True
        or snapshot.get("reusable_authorization") is not False
        or snapshot.get("synthetic_input") is not False
        or type(snapshot.get("observed_monotonic_ns")) is not int
        or snapshot["observed_monotonic_ns"] <= 0
        or snapshot.get("checkpoint")
        not in {
            "foreground_guard",
            "capture.pre_grab",
            "capture.post_grab",
            "capture_patch.pre_grab",
            "capture_patch.post_grab",
        }
        or snapshot.get("expected_screen") not in {None, "main_menu", "bookmark_lobby"}
        or (
            snapshot.get("last_input_tick") is not None
            and (
                type(snapshot.get("last_input_tick")) is not int
                or snapshot["last_input_tick"] < 0
            )
        )
        or (
            snapshot.get("capture_sequence") is not None
            and (
                type(snapshot.get("capture_sequence")) is not int
                or snapshot["capture_sequence"] <= 0
            )
        )
        or not isinstance(target, dict)
        or not isinstance(foreground, dict)
        or not isinstance(process, dict)
    ):
        raise AgentError("menu smoke foreground-loss snapshot contract differs")
    try:
        if re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00",
            str(snapshot["observed_at"]),
        ) is None:
            raise ValueError("noncanonical UTC timestamp")
        observed_at = datetime.fromisoformat(str(snapshot["observed_at"]))
    except ValueError as error:
        raise AgentError("menu smoke foreground-loss timestamp differs") from error
    if observed_at.utcoffset() is None or observed_at.utcoffset().total_seconds() != 0:
        raise AgentError("menu smoke foreground-loss timestamp differs")
    try:
        event_at = datetime.fromisoformat(str(row["at"]))
    except ValueError as error:
        raise AgentError("menu smoke foreground-loss event timestamp differs") from error
    if event_at < observed_at:
        raise AgentError("menu smoke foreground-loss event predates its snapshot")
    target_keys = {
        "pid",
        "hwnd",
        "thread_id",
        "client_rect",
        "executable",
        "creation_date",
        "identity_verified_before_sample",
        "error",
    }
    finished = next(
        (
            event
            for event in rows
            if event.get("kind") == "foreground_activation_finished"
        ),
        None,
    )
    activation = finished.get("attestation") if isinstance(finished, dict) else None
    target_thread = target.get("thread_id")
    if (
        set(target) != target_keys
        or target.get("pid") != process.get("pid")
        or target.get("hwnd") != row.get("target_hwnd")
        or target.get("pid") != row.get("target_pid")
        or target.get("creation_date") != process.get("creation_date")
        or Path(str(target.get("executable", ""))).resolve()
        != Path(str(process.get("executable", ""))).resolve()
        or target.get("identity_verified_before_sample") is not True
        or not isinstance(target.get("client_rect"), list)
        or len(target["client_rect"]) != 4
        or any(type(value) is not int for value in target["client_rect"])
        or target["client_rect"][2] - target["client_rect"][0] != 2560
        or target["client_rect"][3] - target["client_rect"][1] != 1440
        or not isinstance(activation, dict)
        or activation.get("target_pid") != target.get("pid")
        or activation.get("target_hwnd") != target.get("hwnd")
        or (
            target_thread is not None
            and (
                type(target_thread) is not int
                or target_thread <= 0
                or target_thread != activation.get("target_thread_id")
                or target.get("error") is not None
            )
        )
        or (
            target_thread is None
            and not (
                isinstance(target.get("error"), str) and target.get("error")
            )
        )
    ):
        raise AgentError("menu smoke foreground-loss target binding differs")
    foreground_keys = {
        "status",
        "raw_hwnd",
        "root_hwnd",
        "thread_id",
        "pid",
        "class_name",
        "rect",
        "exstyle",
        "topmost",
        "visible",
        "iconic",
        "identity_revalidated",
        "process_identity",
        "error",
    }
    identity = foreground.get("process_identity")
    if (
        set(foreground) != foreground_keys
        or type(foreground.get("raw_hwnd")) is not int
        or foreground["raw_hwnd"] < 0
        or type(foreground.get("root_hwnd")) is not int
        or foreground["root_hwnd"] < 0
        or foreground.get("root_hwnd") == target.get("hwnd")
        or foreground.get("status") != row.get("foreground_status")
        or foreground.get("root_hwnd") != row.get("foreground_root_hwnd")
        or foreground.get("pid") != row.get("foreground_pid")
        or snapshot.get("checkpoint") != row.get("checkpoint")
        or not isinstance(identity, dict)
        or set(identity)
        != {
            "status",
            "pid",
            "executable",
            "creation_time_100ns",
            "pin_method",
            "error",
        }
    ):
        raise AgentError("menu smoke foreground-loss observed binding differs")
    if foreground.get("status") == "observed":
        exstyle = foreground.get("exstyle")
        if (
            foreground.get("root_hwnd", 0) <= 0
            or type(foreground.get("thread_id")) is not int
            or foreground["thread_id"] <= 0
            or type(foreground.get("pid")) is not int
            or foreground["pid"] <= 0
            or not isinstance(foreground.get("class_name"), str)
            or not foreground["class_name"]
            or not isinstance(foreground.get("rect"), list)
            or len(foreground["rect"]) != 4
            or any(type(value) is not int for value in foreground["rect"])
            or type(exstyle) is not int
            or foreground.get("topmost") is not bool(exstyle & 0x8)
            or type(foreground.get("visible")) is not bool
            or type(foreground.get("iconic")) is not bool
            or foreground.get("error") is not None
            or identity.get("pid") != foreground.get("pid")
        ):
            raise AgentError("menu smoke observed foreground identity differs")
        if identity.get("status") == "proven":
            if (
                not isinstance(identity.get("executable"), str)
                or not identity.get("executable")
                or type(identity.get("creation_time_100ns")) is not int
                or identity["creation_time_100ns"] <= 0
                or identity.get("pin_method")
                != "OpenProcess+GetProcessId+QueryFullProcessImageNameW+GetProcessTimes"
                or identity.get("error") is not None
                or foreground.get("identity_revalidated") is not True
            ):
                raise AgentError("menu smoke pinned foreground process differs")
        elif identity.get("status") == "unknown":
            if (
                identity.get("executable") is not None
                or identity.get("creation_time_100ns") is not None
                or identity.get("pin_method") is not None
                or not isinstance(identity.get("error"), str)
                or not identity.get("error")
                or foreground.get("identity_revalidated") is not False
            ):
                raise AgentError("menu smoke unknown foreground process differs")
        else:
            raise AgentError("menu smoke foreground process status differs")
    elif foreground.get("status") == "unknown":
        if (
            any(
                foreground.get(key) is not None
                for key in (
                    "thread_id",
                    "pid",
                    "class_name",
                    "rect",
                    "exstyle",
                    "topmost",
                    "visible",
                    "iconic",
                )
            )
            or foreground.get("identity_revalidated") is not False
            or not isinstance(foreground.get("error"), str)
            or not foreground.get("error")
            or identity.get("status") != "unknown"
            or identity.get("pid") is not None
            or identity.get("executable") is not None
            or identity.get("creation_time_100ns") is not None
            or identity.get("pin_method") is not None
            or not isinstance(identity.get("error"), str)
            or not identity.get("error")
        ):
            raise AgentError("menu smoke unknown foreground identity differs")
    else:
        raise AgentError("menu smoke foreground-loss status differs")
    observation_sequences: list[int] = []
    for relative, path in verified.items():
        if not relative.startswith("artifacts/") or not relative.endswith(
            ".observation.json"
        ):
            continue
        try:
            observation = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentError(
                f"menu smoke foreground-loss observation cannot be parsed: {error}"
            ) from error
        private = (
            observation.get("private_audit")
            if isinstance(observation, dict)
            else None
        )
        if not isinstance(private, dict):
            continue
        sequence = private.get("capture_sequence")
        if (
            type(sequence) is not int
            or sequence <= 0
            or sequence in observation_sequences
        ):
            raise AgentError(
                "menu smoke foreground-loss observation sequence differs"
            )
        observation_sequences.append(sequence)
        private_process = private.get("process")
        if (
            not isinstance(private_process, dict)
            or private_process.get("pid") != target.get("pid")
            or private_process.get("hwnd") != target.get("hwnd")
            or private.get("client_rect") != target.get("client_rect")
        ):
            raise AgentError(
                "menu smoke foreground-loss target/observation binding differs"
            )
    checkpoint = snapshot.get("checkpoint")
    capture_sequence = snapshot.get("capture_sequence")
    expected_screen = snapshot.get("expected_screen")
    receipts = _action_receipts(verified)
    if len(receipts) > 1:
        raise AgentError(
            "menu smoke foreground-loss capture stage has multiple receipts"
        )
    send_input = receipts[0].get("send_input") if receipts else None
    if checkpoint in {"capture.pre_grab", "capture.post_grab"}:
        derived_expected_screen = (
            "bookmark_lobby"
            if isinstance(send_input, dict) and send_input.get("accepted") == 2
            else "main_menu"
        )
        if (
            type(capture_sequence) is not int
            or capture_sequence != max(observation_sequences, default=0) + 1
            or expected_screen != derived_expected_screen
        ):
            raise AgentError("menu smoke foreground-loss capture context differs")
    else:
        if (
            len(receipts) != 1
            or not isinstance(send_input, dict)
            or send_input.get("accepted") is not None
        ):
            raise AgentError(
                "menu smoke foreground-loss action checkpoint differs"
            )
        if capture_sequence is not None or expected_screen is not None:
            raise AgentError(
                "menu smoke foreground-loss non-capture context differs"
            )


def _validate_shutdown_contract(
    report: dict[str, object], environment: dict[str, object]
) -> bool:
    shutdown = report.get("shutdown_attestation")
    process = report.get("process")
    inventory = report.get("post_shutdown_ck3_inventory")
    if not isinstance(shutdown, dict) or not isinstance(process, dict):
        raise AgentError("menu smoke tracked shutdown evidence is missing")
    nonce = shutdown.get("nonce")
    if not isinstance(nonce, str) or not re.fullmatch(r"[0-9a-f]{32}", nonce):
        raise AgentError("menu smoke tracked shutdown nonce differs")
    control = Path(str(environment["state_dir"])) / "control"
    expected_absent = {
        str(control / "ck3.json"): True,
        str(control / f"watchdog-{nonce}.ready.json"): True,
        str(control / "ck3.watchdog_error"): True,
        str(control / "unsafe-cleanup.json"): True,
    }
    if (
        type(shutdown.get("ok")) is not bool
        or not isinstance(shutdown.get("contract_errors"), list)
        or any(
            not isinstance(item, str) or not item
            for item in shutdown["contract_errors"]
        )
        or shutdown["ok"] is not (shutdown["contract_errors"] == [])
    ):
        raise AgentError("menu smoke shutdown contract result differs")
    # cleanup_proven is deliberately narrower than shutdown.ok.  The runtime
    # can prove that the Job/process/control tree is physically gone while
    # still reporting a non-safety contract error (for example, CK3 exited
    # before a require-running stop).  Such a run is a replayable RED and may
    # proceed to protected postflight; GREEN separately requires ok=true and
    # an empty contract_errors list.
    cleanup_conjunction = (
        shutdown.get("tree_gone") is True
        and shutdown.get("job_active_processes_final") == 0
        and isinstance(shutdown.get("final_ck3_inventory"), dict)
        and shutdown["final_ck3_inventory"].get("processes") == []
        and shutdown.get("watchdog_state_after") == "absent"
        and shutdown.get("control_files_absent") == expected_absent
        and shutdown.get("ck3_pid") == process.get("pid")
        and shutdown.get("ck3_creation_date") == process.get("creation_date")
        and shutdown.get("watchdog_pid") == process.get("watchdog_pid")
    )
    if cleanup_conjunction is not True or shutdown.get("cleanup_proven") is not True:
        raise AgentError("menu smoke cleanup claim does not equal its conjunction")
    return bool(
        cleanup_conjunction
        and isinstance(inventory, dict)
        and inventory.get("processes") == []
    )


def _validate_engine_diagnostics_archive(
    report: dict[str, object],
    environment: dict[str, object],
    verified: dict[str, Path],
) -> None:
    diagnostics = report.get("engine_diagnostics")
    process = report.get("process")
    logs = diagnostics.get("logs") if isinstance(diagnostics, dict) else None
    if (
        not isinstance(diagnostics, dict)
        or not isinstance(process, dict)
        or type(process.get("fresh_log_epoch_ns")) is not int
        or diagnostics.get("policy_boundary")
        != "supervisor evidence only; unavailable to gameplay policy"
        or not isinstance(logs, dict)
        or set(logs) != {"error.log", "gui_warnings.log"}
    ):
        raise AgentError("menu smoke engine diagnostic contract differs")
    production = Path(str(environment["mod"]["production_path"]))
    expected_hits: list[dict[str, object]] = []
    expected_zero = True
    for name in ("error.log", "gui_warnings.log"):
        record = logs[name]
        if not isinstance(record, dict) or type(record.get("present")) is not bool:
            raise AgentError(f"menu smoke {name} diagnostic record differs")
        if not record["present"]:
            if record != {"present": False, "diagnostic_records": 0}:
                raise AgentError(f"menu smoke absent {name} diagnostic record differs")
            continue
        relative = f"artifacts/supervisor-{name}"
        if (
            set(record)
            != {
                "present",
                "path",
                "sha256",
                "size",
                "mtime_ns",
                "diagnostic_records",
                "nonempty_lines",
            }
            or record.get("path") != relative
            or relative not in verified
            or record.get("sha256") != sha256_file(verified[relative])
            or record.get("size") != verified[relative].stat().st_size
            or type(record.get("mtime_ns")) is not int
            or record.get("mtime_ns") < process.get("fresh_log_epoch_ns")
        ):
            raise AgentError(f"menu smoke {name} diagnostic artifact differs")
        analysis = analyze_engine_log_bytes(
            name,
            verified[relative].read_bytes(),
            expected_mod_name=EXPECTED_MOD_NAME,
            production_path=production,
        )
        if (
            record.get("diagnostic_records")
            != analysis["diagnostic_records"]
            or record.get("nonempty_lines") != analysis["nonempty_lines"]
        ):
            raise AgentError(f"menu smoke {name} diagnostic analysis differs")
        if analysis["diagnostic_records"] or analysis["nonempty_lines"]:
            expected_zero = False
        expected_hits.extend(analysis["current_mod_diagnostic_hits"])
    if (
        diagnostics.get("zero_diagnostics") is not expected_zero
        or diagnostics.get("current_mod_diagnostics") is not bool(expected_hits)
        or diagnostics.get("current_mod_diagnostic_hits") != expected_hits
    ):
        raise AgentError("menu smoke engine diagnostic summary differs")


def _validate_success_payload(
    report: dict[str, object],
    run_dir: Path,
    verified: dict[str, Path],
    *,
    event_rows: list[dict[str, object]] | None = None,
) -> None:
    forbidden_failure_fields = {
        "error",
        "error_type",
        "foreground_loss",
        "interrupted",
        "secondary_errors",
        "unsafe_cleanup",
    }
    present_failure_fields = forbidden_failure_fields & set(report)
    if present_failure_fields:
        raise AgentError(
            "menu smoke GREEN contains failure fields: "
            + ", ".join(sorted(present_failure_fields))
        )
    environment = _validate_archived_environment(report, verified)
    _validate_archived_menu_qualification(report, verified)
    if event_rows is None:
        event_rows = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
    _validate_foreground_loss_evidence(report, event_rows, verified)
    postflight_rows = [
        row for row in event_rows if row.get("kind") == "postflight_attested"
    ]
    environment_mod = environment.get("mod")
    if (
        len(postflight_rows) != 1
        or not isinstance(environment_mod, dict)
        or postflight_rows[0].get("production_tree_sha256")
        != environment_mod.get("production_tree_sha256")
    ):
        raise AgentError("menu smoke production postflight event binding differs")
    _validate_process_contract(report.get("process"), environment)
    _validate_archived_load(report, environment, verified)
    if "ui-contract.json" not in verified:
        raise AgentError("menu smoke UI contract archive is missing")
    contract = report.get("ui_contract")
    if (
        not isinstance(contract, dict)
        or contract.get("agent_runtime_path") != UI_CONTRACT_AGENT_RUNTIME_PATH
        or contract.get("source_repository_relative")
        != UI_CONTRACT_REPOSITORY_RELATIVE.as_posix()
        or contract.get("archive_path") != UI_CONTRACT_ARCHIVE
        or contract.get("sha256") != sha256_file(verified[UI_CONTRACT_ARCHIVE])
        or contract.get("size") != verified[UI_CONTRACT_ARCHIVE].stat().st_size
    ):
        raise AgentError("menu smoke UI contract report binding differs")
    from .vision.classifier import (
        load_ui_contract,
        require_canonical_phase_b_contract,
    )

    ui_contract = load_ui_contract(
        verified[UI_CONTRACT_ARCHIVE],
        expected_sha256=str(contract["sha256"]),
    )
    require_canonical_phase_b_contract(ui_contract, str(contract["sha256"]))
    _validate_navigation_success(
        report.get("navigation_attestation"),
        verified=verified,
        contract=ui_contract,
        process=report.get("process"),
        environment=environment,
    )
    navigation = report["navigation_attestation"]
    transition = navigation["transition"]
    action = transition["action"]
    receipts = _action_receipts(verified)
    receipt_ref = action.get("receipt_artifact") if isinstance(action, dict) else None
    if (
        receipts != [action]
        or not isinstance(receipt_ref, str)
        or receipt_ref not in verified
        or json.loads(verified[receipt_ref].read_text(encoding="utf-8")) != action
    ):
        raise AgentError("menu smoke does not bind exactly one confirmed action receipt")
    if _validate_shutdown_contract(report, environment) is not True:
        raise AgentError("menu smoke GREEN cleanup conjunction is false")
    shutdown = report.get("shutdown_attestation")
    inventory = report.get("post_shutdown_ck3_inventory")
    process = report.get("process")
    final_inventory = (
        shutdown.get("final_ck3_inventory") if isinstance(shutdown, dict) else None
    )
    controls_absent = (
        shutdown.get("control_files_absent") if isinstance(shutdown, dict) else None
    )
    shutdown_nonce = shutdown.get("nonce") if isinstance(shutdown, dict) else None
    control_root = Path(str(environment["state_dir"])) / "control"
    if not isinstance(shutdown_nonce, str) or not re.fullmatch(
        r"[0-9a-f]{32}", shutdown_nonce
    ):
        raise AgentError("menu smoke shutdown nonce differs")
    expected_controls_absent = {
        str(control_root / "ck3.json"): True,
        str(control_root / f"watchdog-{shutdown_nonce}.ready.json"): True,
        str(control_root / "ck3.watchdog_error"): True,
        str(control_root / "unsafe-cleanup.json"): True,
    }
    if (
        not isinstance(shutdown, dict)
        or shutdown.get("cleanup_proven") is not True
        or shutdown.get("ok") is not True
        or shutdown.get("tree_gone") is not True
        or shutdown.get("job_active_processes_final") != 0
        or shutdown.get("watchdog_state_after") != "absent"
        or shutdown.get("contract_errors") != []
        or not isinstance(process, dict)
        or shutdown.get("ck3_pid") != process.get("pid")
        or shutdown.get("ck3_creation_date") != process.get("creation_date")
        or shutdown.get("watchdog_pid") != process.get("watchdog_pid")
        or not isinstance(final_inventory, dict)
        or final_inventory.get("processes") != []
        or controls_absent != expected_controls_absent
        or not isinstance(inventory, dict)
        or inventory.get("processes") != []
    ):
        raise AgentError("menu smoke tracked cleanup proof differs")
    protected = report.get("protected_storage")
    if (
        not isinstance(protected, dict)
        or protected.get("post_exit_matches_baseline") is not True
        or protected.get("continuous_quiet_seconds") != 5
        or protected.get("runtime_write_absence_proven") is not False
        or protected.get("before_snapshot") != "protected-before.json.gz"
        or protected.get("after_snapshot") != "protected-after.json.gz"
        or protected.get("before_snapshot_sha256")
        != sha256_file(verified["protected-before.json.gz"])
        or protected.get("after_snapshot_sha256")
        != sha256_file(verified["protected-after.json.gz"])
        or report.get("production_tree_unchanged") is not True
    ):
        raise AgentError("menu smoke protected postflight proof differs")
    try:
        with gzip.open(
            verified["protected-before.json.gz"], "rt", encoding="utf-8"
        ) as source:
            protected_before = json.load(source)
        with gzip.open(
            verified["protected-after.json.gz"], "rt", encoding="utf-8"
        ) as source:
            protected_after = json.load(source)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"menu smoke protected snapshots cannot be parsed: {error}"
        ) from error
    before_stores = (
        protected_before.get("stores") if isinstance(protected_before, dict) else None
    )
    after_stores = (
        protected_after.get("stores") if isinstance(protected_after, dict) else None
    )
    before_volatile = (
        protected_before.get("allowed_volatile")
        if isinstance(protected_before, dict)
        else None
    )
    after_volatile = (
        protected_after.get("allowed_volatile")
        if isinstance(protected_after, dict)
        else None
    )
    volatile_policy = (
        "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected."
    )
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
        or before_volatile.get("policy") != volatile_policy
        or after_volatile.get("policy") != volatile_policy
        or not isinstance(before_volatile.get("steam_remotecache"), dict)
        or not isinstance(after_volatile.get("steam_remotecache"), dict)
        or protected_before.get("digest") != protected.get("sha256")
        or protected_after.get("digest") != protected.get("sha256")
        or snapshot_digest(before_stores) != protected_before.get("digest")
        or snapshot_digest(after_stores) != protected_after.get("digest")
        or protected.get("allowed_volatile_before") != before_volatile
        or protected.get("allowed_volatile_after") != after_volatile
    ):
        raise AgentError("menu smoke protected snapshot semantics differ")
    _validate_engine_diagnostics_archive(report, environment, verified)
    if report["engine_diagnostics"].get("current_mod_diagnostics") is not False:
        raise AgentError("menu smoke GREEN contains current-mod engine diagnostics")
    required = {
        "environment.json",
        "production.manifest.json",
        "protected-before.json.gz",
        "protected-after.json.gz",
        UI_CONTRACT_ARCHIVE,
        "artifacts/supervisor-load-attestation.json",
    }
    if not required <= set(verified):
        raise AgentError("menu smoke success artifact set is incomplete")


def _validate_event_semantics(
    report: dict[str, object],
    chain: dict[str, object],
    run_dir: Path,
    *,
    event_rows: list[dict[str, object]] | None = None,
) -> None:
    rows = event_rows
    if rows is None:
        rows = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
    for row in rows:
        at = row.get("at")
        if not isinstance(at, str) or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00",
            at,
        ) is None:
            raise AgentError("menu smoke event timestamp differs")
        try:
            parsed_at = datetime.fromisoformat(at)
        except ValueError as error:
            raise AgentError("menu smoke event timestamp differs") from error
        if parsed_at.utcoffset() is None or parsed_at.utcoffset().total_seconds() != 0:
            raise AgentError("menu smoke event timestamp differs")
    kinds = [row.get("kind") for row in rows]
    if report.get("ok") is True:
        if tuple(kinds) != GREEN_EVENT_ORDER:
            raise AgentError(f"menu smoke GREEN event order differs: {kinds!r}")
    else:
        if (
            not kinds
            or kinds[0] != "smoke_started"
            or kinds[-1] != "smoke_finished"
            or any(kind not in RED_EVENT_ORDER for kind in kinds)
            or len(kinds) != len(set(kinds))
            or [RED_EVENT_ORDER.index(str(kind)) for kind in kinds]
            != sorted(RED_EVENT_ORDER.index(str(kind)) for kind in kinds)
        ):
            raise AgentError(f"menu smoke RED event order differs: {kinds!r}")
        kind_set = set(kinds)
        foreground_kinds = {
            "foreground_activation_planned",
            "foreground_activation_armed",
            "foreground_activation_finished",
        }
        if (
            (
                kind_set
                & {
                    "visible_main_menu_attested",
                    "ui_action_planned",
                    "ui_input_armed",
                    "ui_action_finished",
                    "bookmark_lobby_attested",
                }
                and "single_mod_runtime_attested" not in kind_set
            )
            or (
                kind_set & foreground_kinds
                and "single_mod_runtime_attested" not in kind_set
            )
            or (
                "foreground_activation_armed" in kind_set
                and "foreground_activation_planned" not in kind_set
            )
            or (
                "foreground_activation_finished" in kind_set
                and "foreground_activation_armed" not in kind_set
            )
            or (
                "foreground_lost" in kind_set
                and "foreground_activation_finished" not in kind_set
            )
            or (
                kind_set
                & {
                    "visible_main_menu_attested",
                    "ui_action_planned",
                    "ui_input_armed",
                    "ui_action_finished",
                    "bookmark_lobby_attested",
                }
                and "foreground_activation_finished" not in kind_set
            )
            or (
                kind_set & {"ui_action_planned", "ui_input_armed", "ui_action_finished"}
                and "visible_main_menu_attested" not in kind_set
            )
            or (
                kind_set & {"ui_input_armed", "ui_action_finished"}
                and "ui_action_planned" not in kind_set
            )
        ):
            raise AgentError("menu smoke RED event prerequisites differ")
    _validate_foreground_events(report, rows)
    action_rows = [row for row in rows if str(row.get("kind", "")).startswith("ui_")]
    if report.get("ok") is True:
        if [row.get("kind") for row in action_rows] != [
            "ui_action_planned",
            "ui_input_armed",
            "ui_action_finished",
        ]:
            raise AgentError("menu smoke UI action event sequence differs")
        action_ids = {row.get("action_id") for row in action_rows}
        navigation = report.get("navigation_attestation", {})
        transition = navigation.get("transition", {}) if isinstance(navigation, dict) else {}
        action = transition.get("action", {}) if isinstance(transition, dict) else {}
        before_audit = action.get("before_stable_observation", {}) if isinstance(action, dict) else {}
        after_audit = action.get("after_stable_observation", {}) if isinstance(action, dict) else {}
        before_frames = before_audit.get("frames", []) if isinstance(before_audit, dict) else []
        after_frames = after_audit.get("frames", []) if isinstance(after_audit, dict) else []
        durable = action.get("durable_events", {}) if isinstance(action, dict) else {}
        target = action.get("target", {}) if isinstance(action, dict) else {}
        armed_target = (
            {key: target[key] for key in ("issued", "fresh")}
            if isinstance(target, dict) and {"issued", "fresh"} <= set(target)
            else None
        )
        if (
            len(action_ids) != 1
            or next(iter(action_ids)) != action.get("action_id")
            or action_rows[0].get("control_id") != "main_menu.new_game"
            or action_rows[-1].get("status") != "confirmed"
            or not isinstance(durable, dict)
            or durable
            != {
                "planned": action_rows[0].get("event_sha256"),
                "armed": action_rows[1].get("event_sha256"),
                "finished": action_rows[2].get("event_sha256"),
            }
            or action_rows[0].get("contract_sha256")
            != action.get("contract_sha256")
            or action_rows[0].get("receipt_artifact")
            != action.get("receipt_artifact")
            or action_rows[0].get("token_sha256")
            != action.get("control_token_sha256")
            or action_rows[0].get("before_frame_ids")
            != [frame.get("frame_id") for frame in before_frames]
            or action_rows[1].get("control_id") != "main_menu.new_game"
            or action_rows[1].get("contract_sha256")
            != action.get("contract_sha256")
            or action_rows[1].get("receipt_artifact")
            != action.get("receipt_artifact")
            or action_rows[1].get("binding") != action.get("binding")
            or action_rows[1].get("target") != armed_target
            or action_rows[1].get("pointer_input_may_have_occurred") is not True
            or action_rows[1].get("button_click_may_have_occurred") is not True
            or action_rows[2].get("receipt_artifact")
            != action.get("receipt_artifact")
            or action_rows[2].get("result_frame_ids")
            != [frame.get("frame_id") for frame in after_frames]
            or action_rows[2].get("send_input") != action.get("send_input")
        ):
            raise AgentError("menu smoke UI event/action receipt binding differs")
        main_row = rows[GREEN_EVENT_ORDER.index("visible_main_menu_attested")]
        lobby_row = rows[GREEN_EVENT_ORDER.index("bookmark_lobby_attested")]
        contract_sha = action.get("contract_sha256")
        if (
            main_row.get("contract_sha256") != contract_sha
            or main_row.get("observation_id")
            != navigation.get("start_observation", {}).get("observation_id")
            or main_row.get("frame_ids")
            != [frame.get("frame_id") for frame in before_frames]
            or lobby_row.get("contract_sha256") != contract_sha
            or lobby_row.get("observation_id")
            != transition.get("observation", {}).get("observation_id")
            or lobby_row.get("frame_ids")
            != [frame.get("frame_id") for frame in after_frames]
        ):
            raise AgentError("menu smoke stable-state event binding differs")
        started_row = rows[0]
        launched_row = rows[1]
        stopped_row = rows[GREEN_EVENT_ORDER.index("tracked_process_stopped")]
        postflight_row = rows[GREEN_EVENT_ORDER.index("postflight_attested")]
        process = report.get("process")
        protected = report.get("protected_storage")
        environment = report.get("environment_sha256")
        qualification = report.get("qualification")
        normal_qualification = (
            qualification.get("normal") if isinstance(qualification, dict) else None
        )
        crash_qualification = (
            qualification.get("crash") if isinstance(qualification, dict) else None
        )
        if (
            not isinstance(process, dict)
            or not isinstance(protected, dict)
            or started_row.get("probe") != "main_menu_to_bookmark_lobby"
            or started_row.get("environment_sha256") != environment
            or started_row.get("protected_storage_sha256")
            != protected.get("sha256")
            or started_row.get("ui_contract_sha256") != contract_sha
            or not isinstance(normal_qualification, dict)
            or not isinstance(crash_qualification, dict)
            or started_row.get("normal_qualification_run_id")
            != normal_qualification.get("run_id")
            or started_row.get("crash_qualification_run_id")
            != crash_qualification.get("run_id")
            or launched_row.get("pid") != process.get("pid")
            or stopped_row.get("pid") != process.get("pid")
            or stopped_row.get("cleanup_proven") is not True
            or postflight_row.get("protected_storage_sha256")
            != protected.get("sha256")
        ):
            raise AgentError("menu smoke lifecycle event binding differs")
    expected_body = _report_body_sha256(report)
    tail = chain.get("tail")
    if (
        report.get("report_body_sha256") != expected_body
        or not isinstance(tail, dict)
        or tail.get("report_body_sha256") != expected_body
    ):
        raise AgentError("menu smoke report body is not bound by its final event")


def _validate_red_ui_evidence(
    report: dict[str, object],
    rows: list[dict[str, object]],
    verified: dict[str, Path],
    contract: object,
    environment: dict[str, object],
) -> None:
    process = report.get("process")
    stable_policy: dict[str, object] | None = None
    stable_audit: dict[str, object] | None = None
    observation_paths = sorted(
        relative
        for relative in verified
        if relative.startswith("artifacts/")
        and relative.endswith(".observation.json")
    )
    policies_by_frame: dict[str, dict[str, object]] = {}
    evidence_by_frame: dict[str, dict[str, object]] = {}
    for relative in observation_paths:
        try:
            archived = json.loads(verified[relative].read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentError(f"menu smoke RED observation cannot be parsed: {error}") from error
        policy = archived.get("policy_observation") if isinstance(archived, dict) else None
        private = archived.get("private_audit") if isinstance(archived, dict) else None
        if not isinstance(policy, dict) or not isinstance(private, dict):
            raise AgentError("menu smoke RED observation archive differs")
        screenshot_ref = private.get("screenshot_path")
        if (
            not isinstance(screenshot_ref, str)
            or screenshot_ref not in verified
            or private.get("observation_path") != relative
            or not isinstance(process, dict)
            or private.get("process", {}).get("pid") != process.get("pid")
        ):
            raise AgentError("menu smoke RED observation reference differs")
        evidence = {
            "observation_id": policy.get("observation_id"),
            "frame_id": policy.get("frame_id"),
            "captured_at": policy.get("captured_at"),
            "capture_sequence": private.get("capture_sequence"),
            "captured_monotonic": private.get("captured_monotonic"),
            "screenshot": screenshot_ref,
            "screenshot_sha256": policy.get("image", {}).get("sha256"),
            "observation": relative,
            "screen": policy.get("screen"),
            "pid": private.get("process", {}).get("pid"),
            "hwnd": private.get("process", {}).get("hwnd"),
            "client_rect": private.get("client_rect"),
        }
        _validate_action_observation(
            evidence,
            expected_screen=str(policy.get("screen", "")),
            verified=verified,
            window_binding={
                "process": {"pid": process.get("pid")},
                "window": {
                    "hwnd": private.get("process", {}).get("hwnd"),
                    "client_rect": private.get("client_rect"),
                },
            },
            contract=contract,
            label="RED archived",
        )
        policies_by_frame[str(policy.get("frame_id"))] = policy
        evidence_by_frame[str(policy.get("frame_id"))] = evidence

    action_rows = [row for row in rows if str(row.get("kind", "")).startswith("ui_")]
    main_rows = [row for row in rows if row.get("kind") == "visible_main_menu_attested"]
    if main_rows:
        if len(main_rows) != 1:
            raise AgentError("menu smoke RED main-menu event count differs")
        main = main_rows[0]
        frame_ids = main.get("frame_ids")
        if (
            main.get("contract_sha256") != getattr(contract, "source_sha256", None)
            or not isinstance(frame_ids, list)
            or len(frame_ids) != 2
            or any(frame_id not in policies_by_frame for frame_id in frame_ids)
        ):
            raise AgentError("menu smoke RED main-menu event references differ")
        frames = [
            {
                key: evidence_by_frame[str(frame_id)][key]
                for key in (
                    "observation_id",
                    "frame_id",
                    "captured_at",
                    "capture_sequence",
                    "captured_monotonic",
                    "screenshot_sha256",
                    "screenshot",
                    "observation",
                    "pid",
                    "hwnd",
                    "client_rect",
                )
            }
            for frame_id in frame_ids
        ]
        latest = policies_by_frame[str(frame_ids[-1])]
        audit = {
            "stable_frames": 2,
            "expected_screen": "main_menu",
            "frames": frames,
            "monotonic_delta": (
                float(frames[1]["captured_monotonic"])
                - float(frames[0]["captured_monotonic"])
            ),
        }
        stable = dict(latest)
        stable["stability"] = {
            "stable_frames": 2,
            "expected_screen": "main_menu",
            "frames": [
                {
                    key: frame[key]
                    for key in (
                        "observation_id",
                        "frame_id",
                        "captured_at",
                        "capture_sequence",
                        "captured_monotonic",
                        "screenshot_sha256",
                    )
                }
                for frame in frames
            ],
            "monotonic_delta": audit["monotonic_delta"],
        }
        _validate_stable_audit(
            stable,
            audit,
            screen="main_menu",
            verified=verified,
            window_binding={
                "process": {"pid": frames[-1]["pid"]},
                "window": {
                    "hwnd": frames[-1]["hwnd"],
                    "client_rect": frames[-1]["client_rect"],
                },
            },
            contract=contract,
        )
        if main.get("observation_id") != stable.get("observation_id"):
            raise AgentError("menu smoke RED main-menu observation binding differs")
        stable_policy = stable
        stable_audit = audit
    receipts = _action_receipts(verified)
    if len(receipts) > 1:
        raise AgentError("menu smoke RED has more than one action receipt")
    if not receipts:
        if action_rows:
            raise AgentError("menu smoke RED WAL lacks its action receipt")
        if report.get("navigation_attestation") is not None:
            raise AgentError("menu smoke RED has navigation without an action receipt")
        return
    if stable_policy is None or stable_audit is None or len(main_rows) != 1:
        raise AgentError("menu smoke RED receipt lacks its stable main-menu proof")
    action = receipts[0]
    _validate_json_schema(action, ACTION_RECEIPT_SCHEMA, "RED action receipt")
    receipt_ref = action.get("receipt_artifact")
    if (
        action.get("format_version") != 2
        or not re.fullmatch(r"[0-9a-f]{32}", str(action.get("action_id", "")))
        or action.get("kind") != "click_visible_control"
        or action.get("control_id") != "main_menu.new_game"
        or action.get("expected_post_screen") != "bookmark_lobby"
        or action.get("risk") != contract.control("main_menu.new_game").risk
        or action.get("policy_boundary")
        != "no caller-supplied coordinates or postconditions"
        or action.get("input_budget") != {"limit": 1, "consumed": 1}
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(action.get("control_token_sha256", ""))
        )
        or not re.fullmatch(
            r"[0-9a-f]{32}", str(action.get("before_observation_id", ""))
        )
        or action.get("contract_sha256") != getattr(contract, "source_sha256", None)
        or not isinstance(receipt_ref, str)
        or receipt_ref not in verified
        or json.loads(verified[receipt_ref].read_text(encoding="utf-8")) != action
        or (
            action_rows
            and {row.get("action_id") for row in action_rows}
            != {action.get("action_id")}
        )
    ):
        raise AgentError("menu smoke RED action identity differs")
    expected_kinds = ["ui_action_planned", "ui_input_armed", "ui_action_finished"]
    actual_kinds = [row.get("kind") for row in action_rows]
    if action_rows and (
        any(kind not in expected_kinds for kind in actual_kinds)
        or [expected_kinds.index(str(kind)) for kind in actual_kinds]
        != sorted(expected_kinds.index(str(kind)) for kind in actual_kinds)
        or actual_kinds[0] != "ui_action_planned"
    ):
        raise AgentError("menu smoke RED UI WAL order differs")
    durable = action.get("durable_events")
    labels = {
        "ui_action_planned": "planned",
        "ui_input_armed": "armed",
        "ui_action_finished": "finished",
    }
    row_labels = [labels[str(row["kind"])] for row in action_rows]
    recorded_labels = list(durable) if isinstance(durable, dict) else []
    if (
        not isinstance(durable, dict)
        or recorded_labels != row_labels[: len(recorded_labels)]
        or any(
            durable[label] != action_rows[index].get("event_sha256")
            for index, label in enumerate(recorded_labels)
        )
    ):
        raise AgentError("menu smoke RED receipt/WAL digest binding differs")
    if not action_rows and recorded_labels:
        raise AgentError("menu smoke RED orphan receipt claims a WAL digest")
    planned = action_rows[0] if action_rows else None
    before = action.get("before_stable_observation")
    before_frames = before.get("frames") if isinstance(before, dict) else None
    if not isinstance(before_frames, list) or len(before_frames) != 2:
        raise AgentError("menu smoke RED receipt stable-frame proof differs")
    if planned is not None and (
        planned.get("control_id") != "main_menu.new_game"
        or planned.get("contract_sha256") != action.get("contract_sha256")
        or planned.get("receipt_artifact") != action.get("receipt_artifact")
        or planned.get("token_sha256") != action.get("control_token_sha256")
        or len(before_frames) != 2
        or planned.get("before_frame_ids")
        != [frame.get("frame_id") for frame in before_frames]
    ):
        raise AgentError("menu smoke RED planned event differs")
    binding = action.get("binding")
    if not isinstance(binding, dict):
        raise AgentError("menu smoke RED action binding is missing")
    _validate_window_binding(binding, process, environment)
    if "binding_after" in action:
        binding_after = action.get("binding_after")
        if not isinstance(binding_after, dict):
            raise AgentError("menu smoke RED post-action window binding is missing")
        _validate_window_binding(binding_after, process, environment)
        if _window_binding_core(binding_after) != _window_binding_core(binding):
            raise AgentError("menu smoke RED post-action window binding core differs")
    latest_ref = before_frames[-1].get("observation")
    if not isinstance(latest_ref, str) or latest_ref not in verified:
        raise AgentError("menu smoke RED stable receipt reference differs")
    latest_archive = json.loads(verified[latest_ref].read_text(encoding="utf-8"))
    latest_policy = latest_archive.get("policy_observation")
    if not isinstance(latest_policy, dict):
        raise AgentError("menu smoke RED stable receipt policy differs")
    stable_policy = dict(latest_policy)
    stable_policy["stability"] = {
        "stable_frames": before.get("stable_frames"),
        "expected_screen": before.get("expected_screen"),
        "frames": [
            {
                key: frame.get(key)
                for key in (
                    "observation_id",
                    "frame_id",
                    "captured_at",
                    "capture_sequence",
                    "captured_monotonic",
                    "screenshot_sha256",
                )
            }
            for frame in before_frames
        ],
        "monotonic_delta": before.get("monotonic_delta"),
    }
    _validate_stable_audit(
        stable_policy,
        before,
        screen="main_menu",
        verified=verified,
        window_binding=binding,
        contract=contract,
    )
    if (
        main_rows[0].get("contract_sha256") != action.get("contract_sha256")
        or main_rows[0].get("observation_id") != stable_policy.get("observation_id")
        or main_rows[0].get("frame_ids")
        != [frame.get("frame_id") for frame in before_frames]
        or action.get("before_observation_id")
        != stable_policy.get("observation_id")
    ):
        raise AgentError("menu smoke RED main-menu event binding differs")

    controls = stable_policy.get("visible_controls")
    target = action.get("target")
    issued = target.get("issued") if isinstance(target, dict) else None
    if (
        not isinstance(controls, list)
        or len(controls) != 1
        or not isinstance(controls[0], dict)
        or controls[0].get("control_id") != "main_menu.new_game"
        or not isinstance(target, dict)
        or not isinstance(issued, dict)
        or set(issued) != {"text", "normalized", "bbox", "center"}
        or not set(target)
        <= {
            "issued",
            "fresh",
            "hover",
            "final_patch_sha256",
            "hover_patch_artifact",
            "final_patch_artifact",
        }
    ):
        raise AgentError("menu smoke RED issued target contract differs")
    control = controls[0]
    control_token = str(control.get("control_token", ""))
    if (
        not re.fullmatch(r"[0-9a-f]{64}", control_token)
        or action.get("control_token_sha256")
        != hashlib.sha256(control_token.encode("ascii")).hexdigest()
        or issued.get("bbox") != control.get("bbox")
        or issued.get("center") != control.get("center")
    ):
        raise AgentError("menu smoke RED issued control/token binding differs")

    def require_target_span(
        observation: dict[str, object], value: object, label: str
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            raise AgentError(f"menu smoke RED {label} target is missing")
        spans = observation.get("ocr")
        matches = [
            span
            for span in spans
            if isinstance(spans, list)
            and isinstance(span, dict)
            and all(
                span.get(key) == value.get(key)
                for key in ("text", "normalized", "bbox", "center")
            )
        ] if isinstance(spans, list) else []
        if len(matches) != 1:
            raise AgentError(f"menu smoke RED {label} target/OCR binding differs")
        return matches[0]

    require_target_span(stable_policy, issued, "issued")
    observed_by_label: dict[str, dict[str, object]] = {}
    for label in ("fresh", "hover"):
        evidence = action.get(f"{label}_observation")
        identifier = action.get(f"{label}_observation_id")
        if evidence is None and identifier is None:
            continue
        if evidence is None or identifier is None:
            raise AgentError(f"menu smoke RED {label} observation pair differs")
        if not isinstance(evidence, dict) or not isinstance(evidence.get("screen"), str):
            raise AgentError(f"menu smoke RED {label} screen evidence differs")
        observed = _validate_action_observation(
            evidence,
            expected_screen=str(evidence["screen"]),
            verified=verified,
            window_binding=binding,
            contract=contract,
            label=f"RED {label}",
        )
        if observed.get("observation_id") != identifier:
            raise AgentError(f"menu smoke RED {label} observation ID differs")
        observed_by_label[label] = observed

    fresh_target = target.get("fresh")
    hover_target = target.get("hover")
    fresh_observed = observed_by_label.get("fresh")
    hover_observed = observed_by_label.get("hover")
    if fresh_observed is not None and fresh_observed.get("screen") != "main_menu":
        changed_screen = fresh_observed.get("screen")
        if (
            action.get("status") != "rejected_before_input"
            or action.get("error")
            != f"AgentError: screen changed before input: main_menu -> {changed_screen}"
            or action.get("input_may_have_occurred") is not False
            or action.get("pointer_input_may_have_occurred") is not False
            or action.get("button_click_may_have_occurred") is not False
            or fresh_target is not None
            or hover_observed is not None
            or hover_target is not None
            or "ui_input_armed" in actual_kinds
        ):
            raise AgentError("menu smoke RED fresh screen-change evidence differs")
    if hover_observed is not None and hover_observed.get("screen") != "main_menu":
        changed_screen = hover_observed.get("screen")
        if (
            fresh_observed is None
            or fresh_observed.get("screen") != "main_menu"
            or not isinstance(fresh_target, dict)
            or action.get("status") != "failed_after_possible_input"
            or action.get("error")
            != f"AgentError: screen changed during hover: main_menu -> {changed_screen}"
            or action.get("input_may_have_occurred") is not True
            or action.get("pointer_input_may_have_occurred") is not True
            or action.get("button_click_may_have_occurred") is not False
            or hover_target is not None
            or "ui_input_armed" not in actual_kinds
        ):
            raise AgentError("menu smoke RED hover screen-change evidence differs")
    if fresh_target is not None:
        if fresh_observed is None or not isinstance(fresh_target, dict):
            raise AgentError("menu smoke RED fresh target lacks its observation")
        require_target_span(fresh_observed, fresh_target, "fresh")
        client_rect = binding["window"]["client_rect"]
        if (
            abs(int(fresh_target["center"][0]) - int(issued["center"][0])) > 15
            or abs(int(fresh_target["center"][1]) - int(issued["center"][1])) > 15
            or fresh_target.get("screen_point")
            != [
                int(client_rect[0]) + int(fresh_target["center"][0]),
                int(client_rect[1]) + int(fresh_target["center"][1]),
            ]
        ):
            raise AgentError("menu smoke RED fresh target geometry differs")
    if hover_target is not None:
        if (
            hover_observed is None
            or not isinstance(hover_target, dict)
            or not isinstance(fresh_target, dict)
        ):
            raise AgentError("menu smoke RED hover target lacks its observation")
        require_target_span(hover_observed, hover_target, "hover")
        bbox = hover_target.get("bbox")
        patch_bbox = hover_target.get("patch_bbox")
        width, height = contract.resolution
        if (
            abs(int(hover_target["center"][0]) - int(fresh_target["center"][0])) > 3
            or abs(int(hover_target["center"][1]) - int(fresh_target["center"][1])) > 3
            or not isinstance(bbox, list)
            or len(bbox) != 4
            or patch_bbox
            != [
                max(0, int(bbox[0]) - 12),
                max(0, int(bbox[1]) - 12),
                min(width, int(bbox[2]) + 12),
                min(height, int(bbox[3]) + 12),
            ]
        ):
            raise AgentError("menu smoke RED hover target geometry differs")
        from PIL import Image

        hover_evidence = action["hover_observation"]
        try:
            with Image.open(verified[str(hover_evidence["screenshot"])]) as source:
                source.load()
                patch_digest = _memory_image_sha256(source.crop(tuple(patch_bbox)))
        except (OSError, ValueError) as error:
            raise AgentError(f"menu smoke RED hover patch cannot replay: {error}") from error
        if patch_digest != hover_target.get("patch_sha256"):
            raise AgentError("menu smoke RED hover patch digest differs")
        final_patch_digest = target.get("final_patch_sha256")
        pixel_change_rejection = (
            action.get("status") == "failed_after_possible_input"
            and action.get("error")
            == "AgentError: visible target pixels changed immediately before input"
            and action.get("button_click_may_have_occurred") is False
            and isinstance(action.get("send_input"), dict)
            and action["send_input"].get("accepted") is None
            and isinstance(final_patch_digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", final_patch_digest) is not None
            and final_patch_digest != patch_digest
            and "hover_patch_artifact" not in target
            and "final_patch_artifact" not in target
        )
        if final_patch_digest is not None and final_patch_digest != patch_digest:
            if not pixel_change_rejection:
                raise AgentError("menu smoke RED final in-memory patch differs")
        elif action.get("error") == (
            "AgentError: visible target pixels changed immediately before input"
        ):
            raise AgentError("menu smoke RED pixel-change rejection lacks changed pixels")

    patch_hashes: list[str] = []
    for artifact_label in ("hover_patch_artifact", "final_patch_artifact"):
        artifact = target.get(artifact_label)
        if artifact is None:
            continue
        if (
            not isinstance(artifact, dict)
            or set(artifact) != {"path", "sha256", "pixel_sha256"}
            or not isinstance(artifact.get("path"), str)
            or artifact["path"] not in verified
            or artifact.get("sha256") != sha256_file(verified[str(artifact["path"])])
        ):
            raise AgentError(f"menu smoke RED {artifact_label} file binding differs")
        from PIL import Image

        try:
            with Image.open(verified[str(artifact["path"])]) as source:
                source.load()
                pixel_hash = _memory_image_sha256(source)
        except (OSError, ValueError) as error:
            raise AgentError(f"menu smoke RED {artifact_label} cannot replay: {error}") from error
        if pixel_hash != artifact.get("pixel_sha256"):
            raise AgentError(f"menu smoke RED {artifact_label} pixels differ")
        patch_hashes.append(pixel_hash)
    if patch_hashes and (
        not isinstance(hover_target, dict)
        or any(value != hover_target.get("patch_sha256") for value in patch_hashes)
    ):
        raise AgentError("menu smoke RED persisted patch equivalence differs")

    send_input = action.get("send_input")
    if not isinstance(send_input, dict) or set(send_input) != {
        "requested",
        "accepted",
        "last_error",
    } or send_input.get("requested") != 2:
        raise AgentError("menu smoke RED SendInput receipt differs")
    accepted = send_input.get("accepted")
    if accepted is not None and (
        type(accepted) is not int
        or not 0 <= accepted <= 2
        or action.get("button_click_may_have_occurred") is not True
        or "ui_input_armed" not in actual_kinds
        or not {"hover_patch_artifact", "final_patch_artifact"} <= set(target)
    ):
        raise AgentError("menu smoke RED submitted-input evidence differs")
    if action.get("button_click_may_have_occurred") is False and accepted is not None:
        raise AgentError("menu smoke RED denies a recorded button submission")

    if "ui_input_armed" in actual_kinds:
        armed = next(row for row in action_rows if row.get("kind") == "ui_input_armed")
        armed_target = (
            {key: target[key] for key in ("issued", "fresh")}
            if isinstance(target, dict) and {"issued", "fresh"} <= set(target)
            else None
        )
        if (
            armed.get("binding") != binding
            or armed.get("target") != armed_target
            or armed.get("pointer_input_may_have_occurred") is not True
            or armed.get("button_click_may_have_occurred") is not True
            or action.get("input_may_have_occurred") is not True
            or action.get("pointer_input_may_have_occurred") is not True
            or action.get("status")
            not in {"input_attempting", "failed_after_possible_input", "confirmed"}
            or fresh_target is None
        ):
            raise AgentError("menu smoke RED armed evidence differs")
    elif action_rows and action.get("status") in {
        "input_attempting",
        "failed_after_possible_input",
    }:
        expected_button = action.get("status") == "input_attempting"
        if (
            action.get("input_may_have_occurred") is not True
            or action.get("pointer_input_may_have_occurred") is not True
            or action.get("button_click_may_have_occurred") is not expected_button
            or accepted is not None
            or fresh_target is None
        ):
            raise AgentError("menu smoke RED pre-WAL arming receipt differs")
    elif (
        action.get("input_may_have_occurred") is not False
        or action.get("pointer_input_may_have_occurred") is not False
        or action.get("button_click_may_have_occurred") is not False
        or action.get("status") not in {"planned", "rejected_before_input"}
        or accepted is not None
    ):
        raise AgentError("menu smoke RED pre-input receipt differs")
    if not action_rows and action.get("status") not in {
        "planned",
        "rejected_before_input",
    }:
        raise AgentError("menu smoke RED orphan receipt advanced beyond planning")
    if "ui_action_finished" in actual_kinds:
        finished = action_rows[-1]
        if (
            finished.get("status") != action.get("status")
            or finished.get("receipt_artifact") != action.get("receipt_artifact")
        ):
            raise AgentError("menu smoke RED finished event differs")
        if action.get("status") == "confirmed":
            after_audit = action.get("after_stable_observation")
            after_frames = (
                after_audit.get("frames") if isinstance(after_audit, dict) else None
            )
            if (
                not isinstance(after_frames, list)
                or finished.get("result_frame_ids")
                != [frame.get("frame_id") for frame in after_frames]
                or finished.get("send_input") != send_input
            ):
                raise AgentError("menu smoke RED confirmed finish binding differs")
        elif (
            finished.get("input_may_have_occurred")
            != action.get("input_may_have_occurred")
            or finished.get("button_click_may_have_occurred")
            != action.get("button_click_may_have_occurred")
        ):
            raise AgentError("menu smoke RED failed finish flags differ")
    navigation = report.get("navigation_attestation")
    if action.get("status") == "confirmed":
        after_audit = action.get("after_stable_observation")
        after_frames = after_audit.get("frames") if isinstance(after_audit, dict) else None
        if not isinstance(after_frames, list) or len(after_frames) != 2:
            raise AgentError("menu smoke RED confirmed receipt lacks lobby frames")
        after_ref = after_frames[-1].get("observation")
        if not isinstance(after_ref, str) or after_ref not in verified:
            raise AgentError("menu smoke RED lobby receipt reference differs")
        after_archive = json.loads(verified[after_ref].read_text(encoding="utf-8"))
        after_policy = after_archive.get("policy_observation")
        if not isinstance(after_policy, dict):
            raise AgentError("menu smoke RED lobby policy differs")
        foreground_rows = [
            row
            for row in rows
            if row.get("kind") == "foreground_activation_finished"
        ]
        if len(foreground_rows) != 1:
            raise AgentError("menu smoke RED confirmed receipt lacks foreground proof")
        after_stable = dict(after_policy)
        after_stable["stability"] = {
            "stable_frames": after_audit.get("stable_frames"),
            "expected_screen": after_audit.get("expected_screen"),
            "frames": [
                {
                    key: frame.get(key)
                    for key in (
                        "observation_id",
                        "frame_id",
                        "captured_at",
                        "capture_sequence",
                        "captured_monotonic",
                        "screenshot_sha256",
                    )
                }
                for frame in after_frames
            ],
            "monotonic_delta": after_audit.get("monotonic_delta"),
        }
        synthetic_navigation = {
            "claim": MENU_ACCEPTANCE_CLAIM,
            "window_binding": binding,
            "foreground_activation": foreground_rows[0].get("attestation"),
            "start_observation": stable_policy,
            "start_observation_audit": before,
            "transition": {"action": action, "observation": after_stable},
            "registered_capabilities": ["main_menu.new_game"],
            "forbidden_capabilities": ["bookmark_lobby.start_game"],
            "start_game_capability_registered": False,
        }
        _validate_navigation_success(
            synthetic_navigation,
            verified=verified,
            contract=contract,
            process=process,
            environment=environment,
            require_complete_durable_events=False,
            require_responsive_gate=(
                report.get("foreground_protocol_version")
                == FOREGROUND_PROTOCOL_VERSION
            ),
        )
        if navigation is not None:
            if navigation != synthetic_navigation:
                raise AgentError("menu smoke RED navigation aggregate differs")
            _validate_navigation_success(
                navigation,
                verified=verified,
                contract=contract,
                process=process,
                environment=environment,
                require_responsive_gate=(
                    report.get("foreground_protocol_version")
                    == FOREGROUND_PROTOCOL_VERSION
                ),
            )
        lobby_rows = [row for row in rows if row.get("kind") == "bookmark_lobby_attested"]
        if lobby_rows and (
            len(lobby_rows) != 1
            or lobby_rows[0].get("contract_sha256")
            != action.get("contract_sha256")
            or lobby_rows[0].get("observation_id")
            != after_stable.get("observation_id")
            or lobby_rows[0].get("frame_ids")
            != [frame.get("frame_id") for frame in after_frames]
        ):
            raise AgentError("menu smoke RED lobby event binding differs")
    elif navigation is not None or any(
        row.get("kind") == "bookmark_lobby_attested" for row in rows
    ):
        raise AgentError("menu smoke RED claims lobby without a confirmed receipt")


def _validate_red_postflight(
    report: dict[str, object],
    rows: list[dict[str, object]],
    verified: dict[str, Path],
    environment: dict[str, object],
) -> None:
    protected = report.get("protected_storage")
    if (
        not isinstance(protected, dict)
        or protected.get("post_exit_matches_baseline") is not True
        or protected.get("continuous_quiet_seconds") != 5
        or protected.get("runtime_write_absence_proven") is not False
        or protected.get("before_snapshot") != "protected-before.json.gz"
        or protected.get("after_snapshot") != "protected-after.json.gz"
        or protected.get("before_snapshot_sha256")
        != sha256_file(verified["protected-before.json.gz"])
        or protected.get("after_snapshot_sha256")
        != sha256_file(verified["protected-after.json.gz"])
        or report.get("production_tree_unchanged") is not True
    ):
        raise AgentError("menu smoke RED protected postflight differs")
    try:
        with gzip.open(verified["protected-before.json.gz"], "rt", encoding="utf-8") as source:
            before = json.load(source)
        with gzip.open(verified["protected-after.json.gz"], "rt", encoding="utf-8") as source:
            after = json.load(source)
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"menu smoke RED protected archive differs: {error}") from error
    if (
        not isinstance(before, dict)
        or not isinstance(after, dict)
        or set(before) != {"digest", "stores", "allowed_volatile"}
        or set(after) != {"digest", "stores", "allowed_volatile"}
        or after.get("stores") != before.get("stores")
        or before.get("digest") != snapshot_digest(before.get("stores"))
        or after.get("digest") != snapshot_digest(after.get("stores"))
        or before.get("digest") != protected.get("sha256")
        or after.get("digest") != protected.get("sha256")
        or protected.get("allowed_volatile_before") != before.get("allowed_volatile")
        or protected.get("allowed_volatile_after") != after.get("allowed_volatile")
    ):
        raise AgentError("menu smoke RED protected archive semantics differ")
    _validate_engine_diagnostics_archive(report, environment, verified)
    postflight_rows = [row for row in rows if row.get("kind") == "postflight_attested"]
    if postflight_rows and (
        len(postflight_rows) != 1
        or postflight_rows[0].get("protected_storage_sha256")
        != protected.get("sha256")
        or postflight_rows[0].get("production_tree_sha256")
        != environment["mod"]["production_tree_sha256"]
    ):
        raise AgentError("menu smoke RED postflight event binding differs")


def _validate_red_payload(
    report: dict[str, object],
    run_dir: Path,
    verified: dict[str, Path],
    *,
    event_rows: list[dict[str, object]] | None = None,
) -> None:
    rows = event_rows
    if rows is None:
        rows = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
    kinds = [str(row.get("kind", "")) for row in rows]
    environment = _validate_archived_environment(report, verified)
    _validate_archived_menu_qualification(report, verified)
    contract = _load_archived_ui_contract(report, verified)
    try:
        with gzip.open(
            verified["protected-before.json.gz"], "rt", encoding="utf-8"
        ) as source:
            before = json.load(source)
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"menu smoke RED baseline cannot be parsed: {error}") from error
    started = rows[0]
    qualification = report.get("qualification")
    normal_qualification = (
        qualification.get("normal") if isinstance(qualification, dict) else None
    )
    crash_qualification = (
        qualification.get("crash") if isinstance(qualification, dict) else None
    )
    stores = before.get("stores") if isinstance(before, dict) else None
    volatile = before.get("allowed_volatile") if isinstance(before, dict) else None
    if (
        not isinstance(before, dict)
        or set(before) != {"digest", "stores", "allowed_volatile"}
        or not isinstance(stores, dict)
        or set(stores) != {"real_profile", "steam_userdata", "workshop"}
        or any(not isinstance(value, dict) for value in stores.values())
        or before.get("digest") != snapshot_digest(stores)
        or not isinstance(volatile, dict)
        or volatile.get("policy")
        != "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected."
        or not isinstance(volatile.get("steam_remotecache"), dict)
        or started.get("probe") != "main_menu_to_bookmark_lobby"
        or started.get("environment_sha256") != report.get("environment_sha256")
        or started.get("protected_storage_sha256") != before.get("digest")
        or started.get("ui_contract_sha256")
        != getattr(contract, "source_sha256", None)
        or not isinstance(normal_qualification, dict)
        or not isinstance(crash_qualification, dict)
        or started.get("normal_qualification_run_id")
        != normal_qualification.get("run_id")
        or started.get("crash_qualification_run_id")
        != crash_qualification.get("run_id")
    ):
        raise AgentError("menu smoke RED start/baseline binding differs")
    if "process" in report:
        _validate_process_contract(report.get("process"), environment)
        if "ck3_launched" in kinds and (
            rows[kinds.index("ck3_launched")].get("pid")
            != report["process"]["pid"]
        ):
            raise AgentError("menu smoke RED launch event binding differs")
    elif "ck3_launched" in kinds:
        raise AgentError("menu smoke RED launch event lacks its process proof")
    if "load_attestation" in report:
        _validate_archived_load(
            report,
            environment,
            verified,
            require_post_exit="protected_storage" in report,
        )
    elif "single_mod_runtime_attested" in kinds:
        raise AgentError("menu smoke RED load event lacks its archived proof")
    _validate_foreground_loss_evidence(report, rows, verified)
    _validate_red_ui_evidence(report, rows, verified, contract, environment)
    shutdown_present = "shutdown_attestation" in report
    cleanup = _validate_shutdown_contract(report, environment) if shutdown_present else False
    if "tracked_process_stopped" in kinds:
        if not shutdown_present or not isinstance(report.get("process"), dict):
            raise AgentError("menu smoke RED stop event lacks its shutdown proof")
        stopped = rows[kinds.index("tracked_process_stopped")]
        shutdown = report["shutdown_attestation"]
        if (
            stopped.get("pid") != report["process"]["pid"]
            or stopped.get("cleanup_proven") is not shutdown.get("cleanup_proven")
        ):
            raise AgentError("menu smoke RED stop event binding differs")
    has_postflight_event = "postflight_attested" in kinds
    postflight_keys = {
        "protected_storage",
        "engine_diagnostics",
        "production_tree_unchanged",
    }
    present_postflight_keys = postflight_keys & set(report)
    complete_postflight = (
        present_postflight_keys == postflight_keys
        and "protected-after.json.gz" in verified
        and report.get("production_tree_unchanged") is True
    )
    if has_postflight_event and not complete_postflight:
        raise AgentError("menu smoke RED postflight event lacks complete proof")
    if cleanup:
        if report.get("unsafe_cleanup") is True:
            raise AgentError("menu smoke RED proven cleanup is marked unsafe")
        if complete_postflight:
            _validate_red_postflight(report, rows, verified, environment)
        elif present_postflight_keys:
            raise AgentError("menu smoke RED claims an incomplete postflight")
    else:
        inventory = report.get("post_shutdown_ck3_inventory")
        inventory_known = (
            isinstance(inventory, dict) and isinstance(inventory.get("processes"), list)
        )
        inventory_unknown = (
            isinstance(inventory, dict)
            and inventory.get("status") == "unknown"
            and isinstance(inventory.get("error"), str)
            and bool(inventory.get("error"))
        )
        if (
            report.get("unsafe_cleanup") is not True
            or (not inventory_known and not inventory_unknown)
            or has_postflight_event
            or present_postflight_keys
        ):
            raise AgentError("menu smoke RED unproven cleanup boundary differs")


def _validate_menu_report_base_contract(
    report: dict[str, object], run_dir: Path
) -> None:
    protocol_version = report.get("foreground_protocol_version")
    if protocol_version != FOREGROUND_PROTOCOL_VERSION:
        expected_legacy_final = LEGACY_FOREGROUND_PROTOCOL_FINAL_EVENTS.get(
            str(report.get("run_id", ""))
        )
        if (
            "foreground_protocol_version" in report
            or report.get("ok") is not False
            or expected_legacy_final is None
            or report.get("final_event_sha256") != expected_legacy_final
            or not isinstance(report.get("event_chain"), dict)
            or report["event_chain"].get("tail_sha256") != expected_legacy_final
        ):
            raise AgentError("menu smoke foreground protocol generation differs")
    if (
        report.get("format_version") != 1
        or report.get("kind") != MENU_KIND
        or report.get("acceptance_claim") != MENU_ACCEPTANCE_CLAIM
        or report.get("run_id") != run_dir.name
        or report.get("run_dir") != "."
        or report.get("valid_score_episode") is not False
        or report.get("growth100_lobby_adoption_proven") is not False
        or report.get("runtime_write_absence_proven") is not False
        or report.get("clean_engine_boot_required") is not False
        or report.get("replay_trust_model") != REPLAY_TRUST_MODEL
        or type(report.get("ok")) is not bool
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(report.get("environment_sha256", ""))
        )
    ):
        raise AgentError("menu smoke report base contract differs")


def _validated_menu_event_rows(
    path: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Read and validate one immutable-in-memory view of the WAL prefix."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise AgentError(f"menu smoke event chain cannot be read: {error}") from error
    previous: str | None = None
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise AgentError(
                f"menu smoke event chain line {line_number} is invalid JSON"
            ) from error
        if not isinstance(row, dict):
            raise AgentError(
                f"menu smoke event chain line {line_number} is not an object"
            )
        recorded = row.get("event_sha256")
        unsigned = dict(row)
        unsigned.pop("event_sha256", None)
        if recorded != snapshot_digest(unsigned):
            raise AgentError(
                f"menu smoke event chain line {line_number} digest differs"
            )
        if row.get("previous_event_sha256") != previous:
            raise AgentError(
                f"menu smoke event chain line {line_number} previous link differs"
            )
        previous = str(recorded)
        rows.append(row)
    if not rows:
        raise AgentError("menu smoke event chain is empty")
    return rows, {
        "event_count": len(rows),
        "tail_sha256": previous,
        "tail": rows[-1],
    }


def _validate_unsafe_cleanup_boundary(
    report: dict[str, object],
    verified: dict[str, Path],
    rows: list[dict[str, object]],
) -> None:
    if report.get("unsafe_cleanup") is True and (
        "protected_storage" in report
        or "protected-after.json.gz" in verified
        or report.get("production_tree_unchanged") is True
        or "engine_diagnostics" in report
        or "postflight_attested" in {row.get("kind") for row in rows}
    ):
        raise AgentError("unsafe menu smoke performed protected postflight")


def _validate_finalized_menu_candidate(
    report: dict[str, object],
    run_dir: Path,
    verified: dict[str, Path],
    rows: list[dict[str, object]],
    chain: dict[str, object],
) -> None:
    """Shared pure semantic replay for preseal, postappend, and public use."""
    _validate_menu_report_base_contract(report, run_dir)
    validate_final_report_payload(report, chain)
    if report.get("event_chain") != {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }:
        raise AgentError("menu smoke event-chain summary differs")
    _validate_event_semantics(
        report,
        chain,
        run_dir,
        event_rows=rows,
    )
    if report.get("ok") is True:
        _validate_success_payload(
            report,
            run_dir,
            verified,
            event_rows=rows,
        )
    elif (
        "error" not in report
        or not isinstance(report.get("error"), str)
        or not report.get("error")
    ):
        raise AgentError("menu smoke RED report lacks its error")
    else:
        _validate_red_payload(
            report,
            run_dir,
            verified,
            event_rows=rows,
        )
    _validate_unsafe_cleanup_boundary(report, verified, rows)


def _validate_preseal_candidate(
    report: dict[str, object],
    run_dir: Path,
    verified: dict[str, Path],
    prefix_rows: list[dict[str, object]],
    prefix_chain: dict[str, object],
    *,
    ok: bool,
) -> tuple[str, dict[str, object]]:
    """Replay the exact hypothetical final report without writing its WAL row."""
    body_hash = _report_body_sha256(report)
    final_row: dict[str, object] = {
        "at": utc_now(),
        "previous_event_sha256": prefix_chain.get("tail_sha256"),
        "kind": "smoke_finished",
        "ok": ok,
        "report_body_sha256": body_hash,
    }
    final_row["event_sha256"] = snapshot_digest(final_row)
    candidate_rows = [
        json.loads(json.dumps(row, ensure_ascii=False)) for row in prefix_rows
    ] + [final_row]
    candidate_chain = {
        "event_count": len(candidate_rows),
        "tail_sha256": final_row["event_sha256"],
        "tail": final_row,
    }
    candidate = json.loads(json.dumps(report, ensure_ascii=False))
    candidate["report_body_sha256"] = body_hash
    candidate["final_event_sha256"] = final_row["event_sha256"]
    candidate["event_chain"] = {
        "event_count": candidate_chain["event_count"],
        "tail_sha256": candidate_chain["tail_sha256"],
    }
    candidate["finalized"] = True
    candidate["ok"] = ok

    _validate_finalized_menu_candidate(
        candidate,
        run_dir,
        verified,
        candidate_rows,
        candidate_chain,
    )
    return body_hash, final_row


def validate_menu_smoke_report(run_dir: Path) -> dict[str, object]:
    run_dir = run_dir.resolve()
    report_path = run_dir / "report.json"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes.decode("utf-8"))
    if not isinstance(report, dict):
        raise AgentError("menu smoke report root is not an object")
    chain = validate_event_chain(run_dir / "events.jsonl")
    verified = _verified_artifact_manifest(report, run_dir)
    event_rows, local_chain = _validated_menu_event_rows(
        run_dir / "events.jsonl"
    )
    if local_chain != chain:
        raise AgentError("menu smoke event chain changed during public replay")
    _validate_finalized_menu_candidate(
        report, run_dir, verified, event_rows, chain
    )
    # Public replay only claims stability across its own two samples.  The
    # archive is unkeyed, so every later consumer must repeat this replay; no
    # return value grants ongoing authorization after external byte changes.
    if report_path.read_bytes() != report_bytes:
        raise AgentError("menu smoke report changed during public replay")
    final_verified = _verified_artifact_manifest(report, run_dir)
    if final_verified != verified:
        raise AgentError("menu smoke artifact set changed during public replay")
    final_rows, final_chain = _validated_menu_event_rows(
        run_dir / "events.jsonl"
    )
    if final_rows != event_rows or final_chain != chain:
        raise AgentError("menu smoke event chain changed during public replay")
    return report


def _run_menu_scenario(
    spec: EnvironmentSpec,
    handle: SessionHandle,
    manifest: dict[str, object],
    artifacts: Path,
    events: Path,
    contract_archive: Path,
    contract_sha256: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Adapter point for the hardened visible driver supplied by launch-audit."""
    # Local imports avoid runtime -> executor -> runtime import recursion.
    from .control import VisibleUiDriver
    from .vision import BoundGameWindow, ForegroundLossError, load_ui_contract

    display = manifest.get("display")
    if not isinstance(display, dict):
        raise AgentError("prepared display contract is missing")
    language = str(display.get("language", ""))
    contract = load_ui_contract(contract_archive, expected_sha256=contract_sha256)
    deadline = time.monotonic() + timeout_seconds
    last_binding_error: AgentError | None = None
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            raise AgentError("CK3 exited before its visible window could be bound")
        try:
            window = BoundGameWindow.bind_session(handle, spec.game_exe)
            break
        except AgentError as error:
            last_binding_error = error
            time.sleep(0.25)
    else:
        raise last_binding_error or AgentError(
            "visible CK3 window did not become naturally foreground"
        )
    # Binding may wait for the one exact 2560x1440 client to appear.  Once it
    # exists, foreground acquisition is a one-shot transaction: no activation,
    # attach, detach, identity, or sampled-input-tick failure is ever retried.
    append_event(
        events,
        {
            "kind": "foreground_activation_planned",
            "pid": window.pid,
            "hwnd": window.hwnd,
            "operation": FOREGROUND_OPERATION,
            "synthetic_input": False,
        },
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_armed",
            "pid": window.pid,
            "hwnd": window.hwnd,
            "operation": FOREGROUND_OPERATION,
            "foreground_may_have_changed": True,
            "synthetic_input_may_have_occurred": False,
        },
    )
    foreground_activation = window.request_foreground_without_input(
        responsive_gate_timeout_seconds=30.0,
        responsive_gate_deadline=deadline,
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_finished",
            "pid": window.pid,
            "hwnd": window.hwnd,
            "status": "confirmed",
            "attestation": foreground_activation,
        },
    )
    driver = VisibleUiDriver(
        window,
        contract,
        artifacts,
        expected_game_version=spec.expected_game_version,
        expected_language=language,
        expected_contract_sha256=contract_sha256,
        durable_event_callback=lambda event: append_event(events, event),
    )
    try:
        before = driver.observe_stable(
            "main_menu",
            _remaining(deadline, "stable visible main menu"),
            stable_frames=2,
        )
        controls = [
            control
            for control in before.controls
            if control.control_id == "main_menu.new_game"
        ]
        if len(before.controls) != 1 or len(controls) != 1:
            raise AgentError(
                "main menu did not expose the exact singleton New Game capability"
            )
        run_dir = artifacts.parent.resolve()
        before_audit = _canonicalize_ui_artifact_references(
            before.to_audit_evidence(), run_dir
        )
        append_event(
            events,
            {
                "kind": "visible_main_menu_attested",
                "contract_sha256": contract_sha256,
                "observation_id": before.observation_id,
                "frame_ids": [
                    frame["frame_id"] for frame in before_audit["frames"]
                ],
            },
        )
        transition = driver.click_visible_control(
            controls[0].token,
            timeout_seconds=_remaining(deadline, "stable visible bookmark lobby"),
        )
    except ForegroundLossError as error:
        try:
            evidence = _archive_foreground_loss(error, artifacts, events)
        except BaseException as evidence_error:
            try:
                error.add_note(
                    "foreground-loss evidence publication failed: "
                    f"{type(evidence_error).__name__}: {evidence_error}"
                )
            except (AttributeError, TypeError):
                pass
            raise error
        raise error.with_evidence(evidence) from error
    action = transition.get("action")
    after = transition.get("observation")
    if not isinstance(action, dict) or not isinstance(after, dict):
        raise AgentError("visible New Game transition result is malformed")
    action = _canonicalize_ui_artifact_references(action, run_dir)
    if not isinstance(action, dict):
        raise AgentError("canonical visible action receipt is malformed")
    transition["action"] = action
    receipt_ref = action.get("receipt_artifact")
    if not isinstance(receipt_ref, str):
        raise AgentError("visible action receipt artifact reference is missing")
    write_json_atomic(run_dir / receipt_ref, action)
    after_audit = action.get("after_stable_observation")
    if not isinstance(after_audit, dict):
        raise AgentError("visible bookmark lobby lacks stable audit evidence")
    append_event(
        events,
        {
            "kind": "bookmark_lobby_attested",
            "contract_sha256": contract_sha256,
            "observation_id": after.get("observation_id"),
            "frame_ids": [frame["frame_id"] for frame in after_audit["frames"]],
        },
    )
    registered = sorted(driver.registered_capabilities)
    return {
        "claim": "visible_main_menu_to_bookmark_lobby_only",
        "window_binding": window.audit_binding(),
        "foreground_activation": foreground_activation,
        "start_observation": before.to_policy_json(),
        "start_observation_audit": before_audit,
        "transition": transition,
        "registered_capabilities": registered,
        "forbidden_capabilities": sorted(driver.contract.forbidden_capabilities),
        "start_game_capability_registered": (
            "bookmark_lobby.start_game" in driver.registered_capabilities
        ),
    }


def _validate_legacy_normal_qualification(
    run_dir: Path, expected_environment_sha256: str
) -> dict[str, object]:
    """Replay the historical v1 conjunction for non-authorizing RED archives."""
    from .runtime import validate_smoke_report

    report = validate_smoke_report(run_dir)
    load = report.get("load_attestation")
    shutdown = report.get("shutdown_attestation")
    inventory = report.get("post_shutdown_ck3_inventory")
    protected = report.get("protected_storage")
    process = report.get("process")
    environment_path = run_dir / "environment.json"
    try:
        environment = json.loads(environment_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal qualification environment cannot be parsed: {error}") from error
    before_path = run_dir / "protected-before.json.gz"
    after_path = run_dir / "protected-after.json.gz"
    try:
        with gzip.open(before_path, "rt", encoding="utf-8") as source:
            before = json.load(source)
        with gzip.open(after_path, "rt", encoding="utf-8") as source:
            after = json.load(source)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"normal qualification protected proof cannot parse: {error}") from error
    production_path = run_dir / "production.manifest.json"
    events_path = run_dir / "events.jsonl"
    try:
        production = json.loads(production_path.read_text(encoding="utf-8"))
        rows = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"normal qualification archive cannot be parsed: {error}"
        ) from error
    mod = environment.get("mod") if isinstance(environment, dict) else None
    started = rows[0] if rows else None
    launched = rows[1] if len(rows) > 1 else None
    stopped = rows[4] if len(rows) > 4 else None
    finished = rows[5] if len(rows) > 5 else None
    if (
        not isinstance(environment, dict)
        or not isinstance(before, dict)
        or not isinstance(after, dict)
        or not isinstance(process, dict)
    ):
        raise AgentError("normal qualification archive object schema differs")
    if (
        report.get("kind") != "infrastructure_smoke"
        or report.get("acceptance_claim")
        != "isolated_single_mod_visible_main_menu_only"
        or report.get("finalized") is not True
        or report.get("ok") is not True
        or report.get("valid_score_episode") is not False
        or report.get("environment_sha256") != expected_environment_sha256
        or environment.get("environment_sha256") != expected_environment_sha256
        or environment.get("environment_sha256") != _contract_digest(environment)
        or not isinstance(mod, dict)
        or mod.get("production_manifest_sha256") != sha256_file(production_path)
        or not isinstance(production, dict)
        or not isinstance(started, dict)
        or [row.get("kind") for row in rows]
        != [
            "smoke_started",
            "ck3_launched",
            "visible_main_menu_attested",
            "single_mod_runtime_attested",
            "tracked_process_stopped",
            "smoke_finished",
        ]
        or started.get("environment_sha256") != expected_environment_sha256
        or started.get("protected_storage_sha256") != before.get("digest")
        or started.get("protected_snapshot_sha256") != sha256_file(before_path)
        or not isinstance(launched, dict)
        or not isinstance(stopped, dict)
        or not isinstance(finished, dict)
        or launched.get("pid") != process.get("pid")
        or stopped.get("pid") != process.get("pid")
        or finished.get("ok") is not True
        or process.get("debug_mode") is not False
        or not isinstance(load, dict)
        or load.get("enabled_mods")
        != [{"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}]
        or not isinstance(load.get("isolated_mod_mounts"), list)
        or len(load["isolated_mod_mounts"]) != 1
        or load.get("unclassified_mounts") != []
        or load.get("session_marker_count") != 1
        or load.get("post_exit_revalidated") is not True
        or not isinstance(shutdown, dict)
        or shutdown.get("cleanup_proven") is not True
        or shutdown.get("tree_gone") is not True
        or shutdown.get("job_active_processes_final") != 0
        or shutdown.get("watchdog_state_after") != "absent"
        or shutdown.get("contract_errors") != []
        or shutdown.get("ok") is not True
        or not isinstance(inventory, dict)
        or inventory.get("processes") != []
        or not isinstance(protected, dict)
        or protected.get("post_exit_matches_baseline") is not True
        or protected.get("runtime_write_absence_proven") is not False
        or protected.get("continuous_quiet_seconds") != 5
        or protected.get("before_snapshot_sha256") != sha256_file(before_path)
        or protected.get("after_snapshot_sha256") != sha256_file(after_path)
        or before.get("stores") != after.get("stores")
        or before.get("digest") != snapshot_digest(before.get("stores"))
        or after.get("digest") != snapshot_digest(after.get("stores"))
        or before.get("digest") != protected.get("sha256")
        or after.get("digest") != protected.get("sha256")
        or report.get("production_tree_unchanged") is not True
    ):
        raise AgentError("normal qualification semantic conjunction differs")
    _validate_release_manifest_archive(production, environment)
    return report


def _validate_normal_qualification(
    run_dir: Path,
    expected_environment_sha256: str,
    *,
    allow_legacy_v1_red_replay: bool = False,
) -> dict[str, object]:
    """Require a self-contained v2 GREEN unless replaying a historical RED.

    The legacy branch is deliberately opt-in and is never used by the live
    qualification scanner or by the producer that archives a new menu run.
    """
    from .runtime import validate_smoke_report

    report = validate_smoke_report(run_dir)
    version = report.get("format_version")
    if version == 1:
        if not allow_legacy_v1_red_replay:
            raise AgentError(
                "normal qualification requires the self-contained v2 contract"
            )
        return _validate_legacy_normal_qualification(
            run_dir, expected_environment_sha256
        )
    if version != 2:
        raise AgentError("normal qualification format version differs")
    if (
        report.get("run_id") != run_dir.resolve().name
        or report.get("run_dir") != "."
        or report.get("kind") != "infrastructure_smoke"
        or report.get("acceptance_claim")
        != "isolated_single_mod_visible_main_menu_only"
        or report.get("environment_sha256") != expected_environment_sha256
        or report.get("finalized") is not True
        or report.get("ok") is not True
        or report.get("valid_score_episode") is not False
    ):
        raise AgentError("normal v2 qualification semantic conjunction differs")
    return report


def _require_menu_qualification(
    spec: EnvironmentSpec, manifest: dict[str, object]
) -> dict[str, object]:
    expected = str(manifest.get("environment_sha256", ""))
    runs_root = spec.state_dir / "runs"
    normal: tuple[Path, dict[str, object]] | None = None
    crashes: list[tuple[Path, dict[str, object]]] = []
    from .crash_probe import validate_crash_report

    for candidate in sorted(
        (path for path in runs_root.iterdir() if path.is_dir()), reverse=True
    ) if runs_root.is_dir() else []:
        report_path = candidate / "report.json"
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            not isinstance(payload, dict)
            or payload.get("environment_sha256") != expected
            or payload.get("finalized") is not True
            or payload.get("ok") is not True
        ):
            continue
        try:
            if payload.get("kind") == "infrastructure_smoke" and normal is None:
                normal = (candidate, _validate_normal_qualification(candidate, expected))
            elif payload.get("kind") == "crash_recovery_smoke":
                crash = validate_crash_report(candidate)
                attestation = crash.get("crash_attestation")
                if (
                    crash.get("valid_score_episode") is not False
                    or not isinstance(attestation, dict)
                    or attestation.get("cleanup_proven") is not True
                    or crash.get("production_tree_unchanged") is not True
                ):
                    raise AgentError("crash qualification semantic conjunction differs")
                crashes.append((candidate, crash))
        except (AgentError, OSError, UnicodeError, json.JSONDecodeError):
            continue
    if normal is None:
        raise AgentError(
            "menu smoke requires a same-environment ordinary smoke GREEN before input"
        )
    normal_finished = _qualification_utc(
        normal[1].get("finished_at"), "live normal qualification finish"
    )
    crash = None
    for item in crashes:
        try:
            crash_started = _qualification_utc(
                item[1].get("started_at"), "live crash qualification start"
            )
        except AgentError:
            continue
        if crash_started > normal_finished:
            crash = item
            break
    if crash is None:
        raise AgentError(
            "menu smoke requires a later same-environment post-resume crash-smoke GREEN before input"
        )
    return {
        "environment_sha256": expected,
        "normal_source": normal[0],
        "normal_report": normal[1],
        "crash_source": crash[0],
        "crash_report": crash[1],
    }


def _copy_qualification_tree(source: Path, destination: Path) -> None:
    root = source.resolve()
    for path in root.rglob("*"):
        if path.is_symlink() or not is_relative_to(path.resolve(), root):
            raise AgentError(f"qualification run contains an unsafe path: {path}")
    shutil.copytree(root, destination)


def _archive_menu_qualification(
    qualification: dict[str, object], run_dir: Path
) -> dict[str, object]:
    archive_root = run_dir / "qualification"
    normal_source = qualification.get("normal_source")
    crash_source = qualification.get("crash_source")
    if not isinstance(normal_source, Path) or not isinstance(crash_source, Path):
        raise AgentError("menu smoke qualification sources are missing")
    normal_relative = (
        Path("qualification") / "normal" / "runs" / normal_source.name
    )
    crash_relative = (
        Path("qualification") / "crash" / "runs" / crash_source.name
    )
    _copy_qualification_tree(normal_source, run_dir / normal_relative)
    _copy_qualification_tree(crash_source, run_dir / crash_relative)
    normal_copy = run_dir / normal_relative
    crash_copy = run_dir / crash_relative
    normal = _validate_normal_qualification(
        normal_copy, str(qualification["environment_sha256"])
    )
    from .crash_probe import validate_crash_report

    crash = validate_crash_report(crash_copy)
    return {
        "environment_sha256": qualification["environment_sha256"],
        "normal": {
            "run_id": normal_source.name,
            "archive_path": normal_relative.as_posix(),
            "report_sha256": sha256_file(normal_copy / "report.json"),
            "events_sha256": sha256_file(normal_copy / "events.jsonl"),
            "validator": NORMAL_V2_QUALIFICATION_VALIDATOR,
            "prelaunch_validation_passed": True,
        },
        "crash": {
            "run_id": crash_source.name,
            "archive_path": crash_relative.as_posix(),
            "report_sha256": sha256_file(crash_copy / "report.json"),
            "events_sha256": sha256_file(crash_copy / "events.jsonl"),
            "validator": "validate_crash_report",
            "prelaunch_validation_passed": True,
        },
        "normal_finished_at": normal.get("finished_at"),
        "crash_started_at": crash.get("started_at"),
    }


def menu_smoke(
    spec: EnvironmentSpec, timeout_seconds: float = 180
) -> dict[str, object]:
    """Run one sealed visible New Game transition and safely stop CK3."""
    ensure_state_path_safe(spec.state_dir)
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise AgentError("menu smoke timeout must be finite and positive")
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "menu-smoke"):
            return _menu_smoke_locked(spec, timeout_seconds)


def _menu_smoke_locked(
    spec: EnvironmentSpec, timeout_seconds: float
) -> dict[str, object]:
    manifest = verify_profile(spec)
    doctor(spec, require_prepared=True)
    _require_committed_environment(manifest)
    if ck3_process_inventory()["processes"]:
        raise AgentError("refusing menu smoke while CK3 is already running")
    qualification = _require_menu_qualification(spec, manifest)

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-menu-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    run_dir.mkdir(parents=True, exist_ok=False)
    artifacts.mkdir()

    baseline = protected_snapshot()
    before_path = run_dir / "protected-before.json.gz"
    write_gzip_json_atomic(before_path, baseline)
    shutil.copy2(spec.manifest_path, run_dir / "environment.json")
    mod = manifest.get("mod")
    production_manifest = mod.get("production_manifest") if isinstance(mod, dict) else None
    if not isinstance(production_manifest, str):
        raise AgentError("prepared production manifest path is missing")
    shutil.copy2(Path(production_manifest), run_dir / "production.manifest.json")
    contract_evidence = _archive_ui_contract(manifest, run_dir)
    qualification_evidence = _archive_menu_qualification(qualification, run_dir)
    append_event(
        events,
        {
            "kind": "smoke_started",
            "probe": "main_menu_to_bookmark_lobby",
            "environment_sha256": manifest["environment_sha256"],
            "protected_storage_sha256": baseline["digest"],
            "ui_contract_sha256": contract_evidence["sha256"],
            "normal_qualification_run_id": qualification_evidence["normal"]["run_id"],
            "crash_qualification_run_id": qualification_evidence["crash"]["run_id"],
        },
    )
    report: dict[str, object] = {
        "format_version": 1,
        "foreground_protocol_version": FOREGROUND_PROTOCOL_VERSION,
        "run_id": run_id,
        "kind": MENU_KIND,
        "acceptance_claim": MENU_ACCEPTANCE_CLAIM,
        "clean_engine_boot_required": False,
        "valid_score_episode": False,
        "growth100_lobby_adoption_proven": False,
        "runtime_write_absence_proven": False,
        "replay_trust_model": dict(REPLAY_TRUST_MODEL),
        "started_at": utc_now(),
        "environment_sha256": manifest["environment_sha256"],
        "run_dir": ".",
        "ui_contract": contract_evidence,
        "qualification": qualification_evidence,
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(run_dir / "report.json", report)

    deadline = time.monotonic() + timeout_seconds
    handle: SessionHandle | None = None
    primary_error: BaseException | None = None
    fatal_error: BaseException | None = None
    secondary_errors: list[str] = []
    cleanup_proven = False

    def process_envelope(session: SessionHandle, pid: int) -> dict[str, object]:
        return {
            "pid": pid,
            "creation_date": session.ck3_creation_date,
            "executable": str(spec.game_exe.resolve()),
            "watchdog_pid": session.watchdog_pid,
            "arguments": session.command,
            "debug_mode": False,
            "fresh_log_epoch_ns": session.log_epoch_ns,
            "prelaunch_logs_removed": session.cleared_logs,
            "pre_resume_ck3_inventory": session.pre_resume_inventory,
        }

    def record_error(error: BaseException, stage: str) -> None:
        nonlocal primary_error, fatal_error
        detail = f"{stage}: {type(error).__name__}: {error}"
        if primary_error is None:
            primary_error = error
            report["error"] = detail
            report["error_type"] = type(error).__name__
        else:
            secondary_errors.append(detail)
        if not isinstance(error, Exception) and fatal_error is None:
            fatal_error = error
            report["interrupted"] = True

    try:
        log("launching tracked non-debug CK3 for the sealed menu smoke")
        handle = launch(spec)
        launched_pid = int(handle.process.pid)
        report["process"] = process_envelope(handle, launched_pid)
        append_event(events, {"kind": "ck3_launched", "pid": launched_pid})
        live_load = wait_for_runtime_attestation(
            spec,
            handle,
            _remaining(deadline, "single-mod runtime attestation"),
        )
        report["load_attestation"] = _archive_runtime_attestation(
            spec, live_load, artifacts
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
        report["navigation_attestation"] = _run_menu_scenario(
            spec,
            handle,
            manifest,
            artifacts,
            events,
            run_dir / UI_CONTRACT_ARCHIVE,
            str(contract_evidence["sha256"]),
            _remaining(deadline, "visible New Game transition"),
        )
    except BaseException as error:
        from .vision import ForegroundLossError

        if isinstance(error, ForegroundLossError):
            report["foreground_loss"] = error.evidence or {
                "status": "unavailable"
            }
        record_error(error, "runtime")
    finally:
        if handle is not None:
            try:
                shutdown = stop_tracked(
                    handle, require_running=primary_error is None
                )
                if not isinstance(report.get("process"), dict):
                    stopped_pid = shutdown.get("ck3_pid")
                    if type(stopped_pid) is not int:
                        raise AgentError(
                            "tracked shutdown lacks CK3 PID needed for process evidence"
                        )
                    report["process"] = process_envelope(handle, stopped_pid)
                report["shutdown_attestation"] = shutdown
                cleanup_proven = shutdown.get("cleanup_proven") is True
                append_event(
                    events,
                    {
                        "kind": "tracked_process_stopped",
                        "pid": report["process"]["pid"],
                        "cleanup_proven": cleanup_proven,
                    },
                )
                if shutdown.get("ok") is not True:
                    record_error(
                        AgentError(
                            "shutdown contract errors: "
                            + "; ".join(
                                str(item)
                                for item in shutdown.get("contract_errors", [])
                            )
                        ),
                        "shutdown",
                    )
            except BaseException as error:
                record_error(error, "shutdown")

    try:
        inventory = ck3_process_inventory()
        report["post_shutdown_ck3_inventory"] = inventory
        if inventory["processes"]:
            cleanup_proven = False
            record_error(
                AgentError(f"CK3 remains after menu smoke: {inventory['processes']!r}"),
                "inventory",
            )
    except BaseException as error:
        cleanup_proven = False
        report["post_shutdown_ck3_inventory"] = {
            "status": "unknown",
            "error": f"{type(error).__name__}: {error}",
        }
        record_error(error, "inventory")

    if cleanup_proven:
        try:
            if handle is None:
                raise AgentError("cleanup was claimed without a tracked session")
            final_load = wait_for_runtime_attestation(spec, handle, 2)
            load = report.get("load_attestation")
            if not isinstance(load, dict):
                raise AgentError("menu smoke load attestation is missing")
            for key in (
                "enabled_mods",
                "isolated_mod_mounts",
                "runtime_dlc_mounts",
                "unclassified_mounts",
                "session_marker_count",
            ):
                if final_load[key] != load[key]:
                    raise AgentError(
                        f"post-exit runtime attestation changed for {key}"
                    )
            final_load_archive = dict(load)
            final_load_archive["post_exit_debug_log"] = _archive_runtime_debug_prefix(
                spec,
                final_load.get("debug_log"),
                artifacts,
                "runtime-debug-post-exit.log",
            )
            final_load_archive["post_exit_revalidated"] = True
            load_archive_path = artifacts / "supervisor-load-attestation.json"
            try:
                write_json_atomic(load_archive_path, final_load_archive)
            except BaseException:
                # Atomic replacement can fail either before or just after the
                # new bytes become visible. Keep the report aligned with the
                # complete generation that actually won so a RED remains
                # replayable in both cases.
                try:
                    persisted_load = json.loads(
                        load_archive_path.read_text(encoding="utf-8")
                    )
                except (OSError, UnicodeError, json.JSONDecodeError):
                    persisted_load = None
                if persisted_load == final_load_archive:
                    report["load_attestation"] = final_load_archive
                elif persisted_load == load:
                    report["load_attestation"] = load
                raise
            report["load_attestation"] = final_load_archive
            postflight_diagnostics = _canonicalize_ui_artifact_references(
                collect_engine_log_evidence(spec, handle, artifacts),
                run_dir,
                reference_keys=frozenset({"path"}),
            )
            after = verify_protected_unchanged(baseline)
            after_path = run_dir / "protected-after.json.gz"
            write_gzip_json_atomic(after_path, after)
            postflight_protected = {
                "post_exit_matches_baseline": True,
                "continuous_quiet_seconds": 5,
                "runtime_write_absence_proven": False,
                "sha256": after["digest"],
                "before_snapshot": "protected-before.json.gz",
                "before_snapshot_sha256": sha256_file(before_path),
                "after_snapshot": "protected-after.json.gz",
                "after_snapshot_sha256": sha256_file(after_path),
                "allowed_volatile_before": baseline.get("allowed_volatile"),
                "allowed_volatile_after": after.get("allowed_volatile"),
            }
            verify_profile(spec)
            current_tree = snapshot_digest(tree_snapshot(spec.production_dir))
            if current_tree != manifest["mod"]["production_tree_sha256"]:
                raise AgentError("production projection changed during menu smoke")
            if isinstance(postflight_diagnostics, dict) and postflight_diagnostics.get(
                "current_mod_diagnostics"
            ):
                raise AgentError(
                    "fresh engine diagnostics reference the current production mod"
                )
            report["engine_diagnostics"] = postflight_diagnostics
            report["protected_storage"] = postflight_protected
            report["production_tree_unchanged"] = True
            append_event(
                events,
                {
                    "kind": "postflight_attested",
                    "protected_storage_sha256": after["digest"],
                    "production_tree_sha256": current_tree,
                },
            )
        except BaseException as error:
            record_error(error, "postflight")
    else:
        report["unsafe_cleanup"] = True
        if primary_error is None:
            record_error(
                AgentError(
                    "menu smoke cleanup is not proven; protected postflight withheld"
                ),
                "cleanup",
            )

    try:
        finalized_event_kinds = {
            json.loads(line).get("kind")
            for line in events.read_text(encoding="utf-8").splitlines()
        }
        postflight_fields = {
            "protected_storage",
            "engine_diagnostics",
            "production_tree_unchanged",
        }
        present_postflight = postflight_fields & set(report)
        if (
            "postflight_attested" not in finalized_event_kinds
            and present_postflight
            and present_postflight != postflight_fields
        ):
            # A BaseException can land between the three derived report
            # assignments.  Preserve their files, but do not publish a partial
            # semantic claim in the finalized RED envelope.
            for key in postflight_fields:
                report.pop(key, None)
        if secondary_errors:
            report["secondary_errors"] = secondary_errors
        report["finished_at"] = utc_now()
        try:
            initial_manifest = _artifact_manifest(run_dir)
            report["artifacts"] = initial_manifest
        except BaseException as error:
            record_error(error, "initial artifact manifest")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise

        candidate_ok = primary_error is None
        candidate_validation_error: BaseException | None = None
        candidate_body_hash: str | None = None
        planned_final_row: dict[str, object] | None = None
        prefix_rows: list[dict[str, object]] | None = None
        prefix_chain: dict[str, object] | None = None
        try:
            initial_verified = _verified_artifact_manifest(report, run_dir)
            prefix_rows, prefix_chain = _validated_menu_event_rows(events)
            candidate_body_hash, planned_final_row = (
                _validate_preseal_candidate(
                    report,
                    run_dir,
                    initial_verified,
                    prefix_rows,
                    prefix_chain,
                    ok=candidate_ok,
                )
            )
        except BaseException as error:
            candidate_validation_error = error
            record_error(error, "pre-final candidate replay")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors

        try:
            # Candidate replay may itself observe mutable artifact bytes.  A
            # fresh, fully verified inventory is the only generation that may
            # be bound into the final RED/GREEN report.
            final_manifest = _artifact_manifest(run_dir)
            report["artifacts"] = final_manifest
            final_verified = _verified_artifact_manifest(report, run_dir)
        except BaseException as error:
            record_error(error, "final artifact manifest")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise
        if final_manifest != initial_manifest:
            stability_error = AgentError(
                "menu smoke artifact bytes changed during candidate replay"
            )
            record_error(stability_error, "pre-final artifact stability")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise stability_error
        if candidate_validation_error is not None:
            # Neither a GREEN nor an operational RED may be sealed if its
            # exact hypothetical public replay failed.
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise candidate_validation_error

        try:
            final_prefix_rows, final_prefix_chain = _validated_menu_event_rows(
                events
            )
        except BaseException as error:
            record_error(error, "final event-prefix validation")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise
        if (
            prefix_rows is None
            or prefix_chain is None
            or final_prefix_rows != prefix_rows
            or final_prefix_chain != prefix_chain
        ):
            prefix_error = AgentError(
                "menu smoke event prefix changed during candidate replay"
            )
            record_error(prefix_error, "pre-final event stability")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise prefix_error
        if (
            candidate_body_hash is None
            or planned_final_row is None
            or _report_body_sha256(report) != candidate_body_hash
        ):
            body_error = AgentError(
                "menu smoke report body changed after candidate replay"
            )
            record_error(body_error, "pre-final report stability")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise body_error

        body_hash = candidate_body_hash
        report["report_body_sha256"] = body_hash
        final_event = _append_final_event_transactionally(
            events,
            ok=candidate_ok,
            report_body_sha256=body_hash,
            expected_prefix=final_prefix_chain,
            expected_final_row=planned_final_row,
        )
        report["final_event_sha256"] = final_event
        report["finalized"] = True
        report["ok"] = candidate_ok
        chain = validate_event_chain(events)
        report["event_chain"] = {
            "event_count": chain["event_count"],
            "tail_sha256": chain["tail_sha256"],
        }
        try:
            actual_rows, actual_chain = _validated_menu_event_rows(events)
            if (
                actual_chain != chain
                or actual_chain.get("tail") != planned_final_row
            ):
                raise AgentError(
                    "menu smoke actual final WAL row differs from preseal replay"
                )
            # Re-hash the complete artifact inventory and replay the exact
            # committed row/report generation before publishing report.json.
            postappend_verified = _verified_artifact_manifest(report, run_dir)
            if postappend_verified != final_verified:
                raise AgentError(
                    "menu smoke artifact inventory changed after final WAL append"
                )
            _validate_finalized_menu_candidate(
                report,
                run_dir,
                postappend_verified,
                actual_rows,
                actual_chain,
            )
        except BaseException as error:
            record_error(error, "post-append candidate replay")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            _publish_menu_provisional_report(run_dir / "report.json", report)
            raise
        _write_final_report_transactionally(run_dir / "report.json", report)
        try:
            validated = validate_menu_smoke_report(run_dir)
        except BaseException as error:
            # Publication and public replay are necessarily two operations.
            # If bytes drift in that interval, make the already published
            # report plainly non-authorizing before preserving the replay
            # failure.  This is best effort; every later consumer must still
            # perform its own public replay under the unkeyed trust model.
            record_error(error, "published final report replay")
            if secondary_errors:
                report["secondary_errors"] = secondary_errors
            try:
                _publish_menu_provisional_report(
                    run_dir / "report.json", report
                )
            except BaseException as downgrade_error:
                try:
                    error.add_note(
                        "provisional downgrade also failed: "
                        f"{type(downgrade_error).__name__}: {downgrade_error}"
                    )
                except (AttributeError, TypeError):
                    pass
            raise
    except BaseException:
        # Finalization/validation is best effort for fatal asynchronous exits.
        # Never replace the original KeyboardInterrupt/SystemExit-equivalent.
        if fatal_error is not None:
            raise fatal_error
        raise
    if fatal_error is not None:
        raise fatal_error
    if primary_error is not None:
        raise AgentError(
            f"menu smoke failed; evidence retained at {run_dir}: {report['error']}"
        ) from primary_error
    log(f"visible menu transition smoke GREEN; evidence={run_dir}")
    return validated
