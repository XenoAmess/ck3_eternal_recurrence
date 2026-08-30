"""Artifact-owning acceptance runner for one native episode transition."""

from __future__ import annotations

from datetime import datetime, timezone
import copy
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
    validate_episode_seed_for_state,
)
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)
from .strategy import ONE_LIFE_STRATEGY_RELATIVE_PATH


NEXT_EPISODE_CHECKPOINT_CADENCE = 1


def native_next_episode_run(
    spec: EnvironmentSpec,
    *,
    max_turns: int,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    checkpoint_every_eligible_advances: int = (
        NEXT_EPISODE_CHECKPOINT_CADENCE
    ),
    native_bridge: NativeBridgeLaunchConfig | None = None,
    route_contact_timeline_speed: int = (
        DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
    ),
    allow_route_contact_high_speed_ab: bool = False,
    allow_stationary_objective_hold_sentinel_canary: bool = False,
) -> dict[str, object]:
    """Settle the current life, reload its seed, act, and checkpoint."""
    if (
        isinstance(max_turns, bool)
        or not isinstance(max_turns, int)
        or max_turns < 1
    ):
        raise AgentError("max_turns must be a positive integer")
    if (
        isinstance(checkpoint_every_eligible_advances, bool)
        or not isinstance(checkpoint_every_eligible_advances, int)
        or checkpoint_every_eligible_advances < 1
    ):
        raise AgentError(
            "checkpoint_every_eligible_advances must be a positive integer"
        )
    ensure_state_path_safe(spec.state_dir)
    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != PURE_NATIVE_MODE:
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "native-next-episode requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-next-episode-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "g2-runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report_path = run_dir / "report.json"
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_native_next_episode_run",
        "run_id": run_id,
        "acceptance_claim": "next_episode_seed_reload_ooda_checkpoint",
        "started_at": utc_now(),
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "run_dir": str(run_dir.resolve()),
        "report_path": str(report_path.resolve()),
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
            "allow_stationary_objective_hold_sentinel_canary": (
                allow_stationary_objective_hold_sentinel_canary is True
            ),
        },
        "status": "preflight_pending",
        "outcome": "in_progress",
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(report_path, report)

    artifacts: dict[str, object] = {}
    core_report: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    episode_seed: dict[str, object] | None = None
    try:
        checkpoint = validate_cold_start_checkpoint_for_pipe(
            spec, config.pipe_name
        )
        episode_seed = validate_episode_seed_for_state(spec)
        report["preflight"] = {
            "status": "ready",
            "checkpoint": checkpoint,
            "episode_seed": episode_seed,
        }
        artifacts["inputs"] = _archive_input_bundle(
            spec,
            run_dir,
            checkpoint=checkpoint,
            episode_seed=episode_seed,
        )
        report["artifacts"] = copy.deepcopy(artifacts)
        report["status"] = "preflight_ready"
        write_json_atomic(report_path, report)

        core_report = native_auto_run(
            spec,
            turn_count=max_turns,
            timeout_seconds=timeout_seconds,
            readiness_timeout_seconds=readiness_timeout_seconds,
            cold_start_checkpoint=True,
            native_bridge=config,
            checkpoint_every_eligible_advances=(
                checkpoint_every_eligible_advances
            ),
            completion_contract="next_episode",
            route_contact_timeline_speed=route_contact_timeline_speed,
            allow_route_contact_high_speed_ab=(
                allow_route_contact_high_speed_ab
            ),
            allow_stationary_objective_hold_sentinel_canary=(
                allow_stationary_objective_hold_sentinel_canary
            ),
        )
        if core_report.get("fixed_seed") != checkpoint:
            raise AgentError(
                "next-episode core started from a different checkpoint anchor"
            )
        report = {
            **core_report,
            "kind": "ck3_native_next_episode_run",
            "run_id": run_id,
            "acceptance_claim": "next_episode_seed_reload_ooda_checkpoint",
            "run_dir": str(run_dir.resolve()),
            "report_path": str(report_path.resolve()),
            "preflight": {
                "status": "ready",
                "checkpoint": checkpoint,
                "episode_seed": episode_seed,
            },
            "finalized": True,
        }
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        base = core_report if core_report is not None else report
        blocker = (
            base.get("first_blocker")
            if isinstance(base.get("first_blocker"), dict)
            else {
                "observed_at": utc_now(),
                "turn_index": 0,
                "stage": "preflight" if checkpoint is None else "runner",
                "kind": "next_episode_runner_failed",
                "status": "runner_error",
                "completion_contract": "next_episode",
                "message": message,
                "error_type": type(error).__name__,
                "error": message,
                "last_durable_checkpoint": checkpoint,
                "recoverable_from_checkpoint": checkpoint is not None,
            }
        )
        report = {
            **base,
            "kind": "ck3_native_next_episode_run",
            "run_id": run_id,
            "acceptance_claim": "next_episode_seed_reload_ooda_checkpoint",
            "run_dir": str(run_dir.resolve()),
            "report_path": str(report_path.resolve()),
            "finished_at": utc_now(),
            "status": "runner_error",
            "outcome": "failed",
            "first_blocker": blocker,
            "error": message,
            "finalized": True,
            "ok": False,
        }

    artifacts["outputs"] = _archive_output_bundle(spec, run_dir)
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
    next_episode = report.get("next_episode")
    if isinstance(next_episode, dict):
        next_episode_path = run_dir / "next-episode.json"
        write_json_atomic(next_episode_path, next_episode)
        artifacts["next_episode"] = _artifact_entry(
            next_episode_path, run_dir
        )
    report["artifacts"] = artifacts
    write_json_atomic(report_path, report)
    return report


def _archive_input_bundle(
    spec: EnvironmentSpec,
    run_dir: Path,
    *,
    checkpoint: dict[str, object],
    episode_seed: dict[str, object],
) -> dict[str, object]:
    destination = run_dir / "inputs"
    destination.mkdir()
    sources = {
        "checkpoint": Path(str(checkpoint["path"])),
        "driver_state": (
            spec.state_dir
            / NATIVE_SESSION_QUEUE_DIRNAME
            / NATIVE_DRIVER_STATE_FILENAME
        ),
        "episode_seed": Path(str(episode_seed["path"])),
        "episode_seed_metadata": Path(str(episode_seed["metadata_path"])),
        "one_life_strategy": spec.state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH,
    }
    return {
        key: _copy_artifact(source, destination / source.name, run_dir)
        for key, source in sources.items()
        if source.is_file()
    }


def _archive_output_bundle(
    spec: EnvironmentSpec,
    run_dir: Path,
) -> dict[str, object]:
    destination = run_dir / "outputs"
    destination.mkdir(exist_ok=True)
    sources = {
        "checkpoint": spec.profile_dir / "save games" / "xar_checkpoint.ck3",
        "driver_state": (
            spec.state_dir
            / NATIVE_SESSION_QUEUE_DIRNAME
            / NATIVE_DRIVER_STATE_FILENAME
        ),
        "episode_transition": (
            spec.state_dir
            / NATIVE_SESSION_QUEUE_DIRNAME
            / "episode-transition.json"
        ),
        "one_life_strategy": spec.state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH,
    }
    logs_dir = spec.profile_dir / "logs"
    for name in ("error.log", "debug.log", "game.log", "system.log"):
        sources[f"log_{name.replace('.', '_')}"] = logs_dir / name
    return {
        key: _copy_artifact(source, destination / source.name, run_dir)
        for key, source in sources.items()
        if source.is_file()
    }


def _copy_artifact(
    source: Path,
    destination: Path,
    run_dir: Path,
) -> dict[str, object]:
    source = source.resolve()
    before_size = source.stat().st_size
    before_digest = sha256_file(source)
    shutil.copy2(source, destination)
    if (
        source.stat().st_size != before_size
        or sha256_file(source) != before_digest
        or destination.stat().st_size != before_size
        or sha256_file(destination) != before_digest
    ):
        raise AgentError(f"artifact changed while archived: {source}")
    return _artifact_entry(destination, run_dir)


def _artifact_entry(path: Path, run_dir: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve().relative_to(run_dir.resolve())).replace(
            "\\", "/"
        ),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }
