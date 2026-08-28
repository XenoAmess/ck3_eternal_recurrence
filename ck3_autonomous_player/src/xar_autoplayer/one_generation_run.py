"""Artifact-owning runner for one complete native CK3 ruler lifetime."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import uuid

from .bridge.native_driver import DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
from .environment import (
    EnvironmentSpec,
    ensure_state_path_safe,
    sha256_file,
    write_json_atomic,
)
from .errors import AgentError
from .native_auto_run import PURE_NATIVE_MODE, native_auto_run
from .native_session import (
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)


ONE_GENERATION_CHECKPOINT_CADENCE = 3


def native_one_generation_run(
    spec: EnvironmentSpec,
    *,
    max_turns: int,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    checkpoint_every_eligible_advances: int = (
        ONE_GENERATION_CHECKPOINT_CADENCE
    ),
    native_bridge: NativeBridgeLaunchConfig | None = None,
    route_contact_timeline_speed: int = (
        DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
    ),
    allow_route_contact_high_speed_ab: bool = False,
    allow_committed_route_sentinel_canary: bool = False,
) -> dict[str, object]:
    """Run until this episode's scored death settlement or the first blocker."""
    if isinstance(max_turns, bool) or not isinstance(max_turns, int) or max_turns < 1:
        raise AgentError("max_turns must be a positive integer")
    ensure_state_path_safe(spec.state_dir)
    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != PURE_NATIVE_MODE:
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "native-one-generation requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-one-generation-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report_path = run_dir / "report.json"
    seed: dict[str, object] | None = None
    seed_bundle: dict[str, object] = {
        "status": "validation_pending",
        "episode_character_id": None,
        "episode_run_id": None,
        "source_checkpoint": None,
    }
    initial_report: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_native_one_generation_run",
        "run_id": run_id,
        "acceptance_claim": "one_generation_unattended_native_ooda",
        "started_at": utc_now(),
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "run_dir": str(run_dir.resolve()),
        "report_path": str(report_path.resolve()),
        "seed_bundle": seed_bundle,
        "bounds": {
            "max_turns": max_turns,
            "max_wall_seconds": timeout_seconds,
            "readiness_timeout_seconds": readiness_timeout_seconds,
            "checkpoint_every_eligible_advances": (
                checkpoint_every_eligible_advances
            ),
            "route_contact_timeline_speed": route_contact_timeline_speed,
            "allow_route_contact_high_speed_ab": (
                allow_route_contact_high_speed_ab is True
            ),
            "allow_committed_route_sentinel_canary": (
                allow_committed_route_sentinel_canary is True
            ),
        },
        "status": "starting",
        "outcome": "in_progress",
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(report_path, initial_report)

    core_report: dict[str, object] | None = None
    try:
        seed = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
        seed_bundle = {
            "status": "archive_pending",
            "episode_character_id": None,
            "episode_run_id": None,
            "source_checkpoint": seed,
        }
        initial_report["seed_bundle"] = seed_bundle
        initial_report["status"] = "seed_validated"
        write_json_atomic(report_path, initial_report)
        seed_bundle = _archive_seed_bundle(spec, run_dir, seed)
        initial_report["seed_bundle"] = seed_bundle
        initial_report["status"] = "seed_archived"
        write_json_atomic(report_path, initial_report)
        core = native_auto_run(
            spec,
            turn_count=max_turns,
            timeout_seconds=timeout_seconds,
            readiness_timeout_seconds=readiness_timeout_seconds,
            cold_start_checkpoint=True,
            native_bridge=config,
            checkpoint_every_eligible_advances=(
                checkpoint_every_eligible_advances
            ),
            completion_contract="one_generation",
            route_contact_timeline_speed=route_contact_timeline_speed,
            allow_route_contact_high_speed_ab=(
                allow_route_contact_high_speed_ab
            ),
            allow_committed_route_sentinel_canary=(
                allow_committed_route_sentinel_canary
            ),
        )
        core_report = core
        _rebind_invalidated_checkpoint_to_seed_archive(
            core, seed_bundle=seed_bundle, run_dir=run_dir
        )
        if core.get("fixed_seed") != seed:
            raise AgentError(
                "one-generation core started from a different checkpoint anchor"
            )
        report = {
            **core,
            "kind": "ck3_native_one_generation_run",
            "run_id": run_id,
            "acceptance_claim": "one_generation_unattended_native_ooda",
            "run_dir": str(run_dir.resolve()),
            "report_path": str(report_path.resolve()),
            "seed_bundle": seed_bundle,
            "finalized": True,
        }
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        blocker = (
            core_report.get("first_blocker")
            if isinstance(core_report, dict)
            and isinstance(core_report.get("first_blocker"), dict)
            else None
        )
        if blocker is None:
            archived_recovery = _archived_seed_recovery_anchor(
                seed_bundle, run_dir
            )
            fallback_checkpoint = (
                archived_recovery
                if seed_bundle.get("status") == "verified_immutable_copy"
                else seed
            )
            blocker = {
                "observed_at": utc_now(),
                "turn_index": 0,
                "stage": (
                    "identity" if core_report is not None else "startup"
                ),
                "kind": (
                    "seed_identity_mismatch"
                    if core_report is not None
                    else "runner_failed_before_core_report"
                ),
                "status": "runner_error",
                "completion_contract": "one_generation",
                "message": message,
                "error_type": type(error).__name__,
                "error": message,
                "initial_episode": {
                    "episode_character_id": seed_bundle.get(
                        "episode_character_id"
                    ),
                    "episode_run_id": seed_bundle.get("episode_run_id"),
                    "date_raw": (
                        seed.get("saved_date_raw")
                        if isinstance(seed, dict)
                        else None
                    ),
                },
                "before": None,
                "plan": None,
                "selected_step": None,
                "after": None,
                "active_context": None,
                "last_durable_checkpoint": fallback_checkpoint,
                "recoverable_from_checkpoint": (
                    fallback_checkpoint is not None
                ),
                "cleanup": None,
            }
        base_report = core_report if core_report is not None else initial_report
        report = {
            **base_report,
            "kind": "ck3_native_one_generation_run",
            "run_id": run_id,
            "acceptance_claim": "one_generation_unattended_native_ooda",
            "run_dir": str(run_dir.resolve()),
            "report_path": str(report_path.resolve()),
            "seed_bundle": seed_bundle,
            "finished_at": utc_now(),
            "status": "runner_error",
            "outcome": "failed",
            "first_blocker": blocker,
            "error": message,
            "finalized": True,
            "ok": False,
        }

    artifacts: dict[str, object] = {}
    for artifact_key, bundle_key in (
        ("seed_checkpoint", "checkpoint"),
        ("seed_driver_state", "driver_state"),
        ("seed_manifest", "manifest"),
    ):
        entry = seed_bundle.get(bundle_key)
        if isinstance(entry, dict):
            artifacts[artifact_key] = entry
    blocker = report.get("first_blocker")
    if isinstance(blocker, dict):
        blocker_path = run_dir / "first-blocker.json"
        write_json_atomic(blocker_path, blocker)
        artifacts["first_blocker"] = _artifact_entry(blocker_path, run_dir)
    terminal = report.get("terminal")
    if isinstance(terminal, dict):
        terminal_path = run_dir / "terminal-settlement.json"
        write_json_atomic(terminal_path, terminal)
        artifacts["terminal_settlement"] = _artifact_entry(
            terminal_path, run_dir
        )
    report["artifacts"] = artifacts
    write_json_atomic(report_path, report)
    return report


def _rebind_invalidated_checkpoint_to_seed_archive(
    report: dict[str, object],
    *,
    seed_bundle: dict[str, object],
    run_dir: Path,
) -> None:
    blocker = report.get("first_blocker")
    if not isinstance(blocker, dict) or blocker.get(
        "checkpoint_recovery_invalidated"
    ) is not True:
        return
    archived_recovery = _archived_seed_recovery_anchor(seed_bundle, run_dir)
    blocker["last_durable_checkpoint"] = archived_recovery
    blocker["recoverable_from_checkpoint"] = archived_recovery is not None
    blocker["recovery_fallback"] = (
        "immutable_seed_archive"
        if archived_recovery is not None
        else "unavailable"
    )


def _archived_seed_recovery_anchor(
    seed_bundle: dict[str, object], run_dir: Path
) -> dict[str, object] | None:
    checkpoint = seed_bundle.get("checkpoint")
    driver_state = seed_bundle.get("driver_state")
    source = seed_bundle.get("source_checkpoint")
    if (
        seed_bundle.get("status") != "verified_immutable_copy"
        or not isinstance(checkpoint, dict)
        or not isinstance(driver_state, dict)
        or not isinstance(source, dict)
    ):
        return None

    def absolute_entry(entry: dict[str, object]) -> dict[str, object]:
        return {
            **entry,
            "path": str((run_dir / str(entry.get("path", ""))).resolve()),
        }

    archived_checkpoint = absolute_entry(checkpoint)
    return {
        "status": "verified_immutable_seed_fallback",
        "phase": "archived_seed",
        "turn_index": 0,
        "path": archived_checkpoint["path"],
        "name": source.get("name"),
        "load_save_name": source.get("load_save_name"),
        "size": archived_checkpoint.get("size"),
        "sha256": archived_checkpoint.get("sha256"),
        "saved_date_raw": source.get("saved_date_raw"),
        "history_index": source.get("history_index"),
        "episode_character_id": seed_bundle.get("episode_character_id"),
        "episode_run_id": seed_bundle.get("episode_run_id"),
        "driver_state": absolute_entry(driver_state),
    }


def _archive_seed_bundle(
    spec: EnvironmentSpec,
    run_dir: Path,
    seed: dict[str, object],
) -> dict[str, object]:
    seed_dir = run_dir / "seed"
    seed_dir.mkdir()
    source_checkpoint = Path(str(seed["path"])).resolve()
    source_state = (
        spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_DRIVER_STATE_FILENAME
    ).resolve()
    try:
        state = json.loads(source_state.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"one-generation seed driver state is unavailable: {error}") from error
    archived_checkpoint = seed_dir / source_checkpoint.name
    archived_state = seed_dir / NATIVE_DRIVER_STATE_FILENAME
    source_state_sha256 = sha256_file(source_state)
    shutil.copy2(source_checkpoint, archived_checkpoint)
    shutil.copy2(source_state, archived_state)
    if (
        archived_checkpoint.stat().st_size != seed.get("size")
        or sha256_file(archived_checkpoint) != seed.get("sha256")
        or source_checkpoint.stat().st_size != seed.get("size")
        or sha256_file(source_checkpoint) != seed.get("sha256")
        or sha256_file(source_state) != source_state_sha256
        or sha256_file(archived_state) != source_state_sha256
    ):
        raise AgentError("one-generation seed changed while it was archived")
    manifest_path = seed_dir / "manifest.json"
    manifest_payload: dict[str, object] = {
        "status": "verified_immutable_copy",
        "episode_character_id": (
            state.get("episode_character_id")
            if isinstance(state, dict)
            else None
        ),
        "episode_run_id": (
            state.get("episode_run_id") if isinstance(state, dict) else None
        ),
        "checkpoint": _artifact_entry(archived_checkpoint, run_dir),
        "driver_state": _artifact_entry(archived_state, run_dir),
        "source_checkpoint": seed,
    }
    write_json_atomic(manifest_path, manifest_payload)
    return {
        **manifest_payload,
        "manifest": _artifact_entry(manifest_path, run_dir),
    }


def _artifact_entry(path: Path, run_dir: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve().relative_to(run_dir.resolve())).replace(
            "\\", "/"
        ),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }
