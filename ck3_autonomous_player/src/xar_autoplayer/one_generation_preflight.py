"""No-launch readiness artifact for resuming one strict ruler lifetime."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

from .bridge.native_driver import load_native_driver_state_for_resume
from .environment import (
    EnvironmentSpec,
    ck3_process_inventory,
    ensure_state_path_safe,
    sha256_file,
    verify_profile,
    write_json_atomic,
)
from .errors import AgentError
from .locking import exclusive_state_lock
from .native_session import (
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import utc_now


def native_one_generation_preflight(
    spec: EnvironmentSpec,
    *,
    pipe_name: str,
    expected_character_id: int | None = None,
    expected_episode_run_id: str | None = None,
    expected_checkpoint_sha256: str | None = None,
    expected_driver_state_sha256: str | None = None,
) -> dict[str, object]:
    """Verify a durable G1 resume anchor without launching or driving CK3."""
    ensure_state_path_safe(spec.state_dir)
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-one-generation-preflight-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "preflights" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report_path = run_dir / "report.json"
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_native_one_generation_preflight",
        "run_id": run_id,
        "started_at": utc_now(),
        "run_dir": str(run_dir.resolve()),
        "report_path": str(report_path.resolve()),
        "pipe": pipe_name,
        "expected": {
            "episode_character_id": expected_character_id,
            "episode_run_id": expected_episode_run_id,
            "checkpoint_sha256": _normalize_digest(
                expected_checkpoint_sha256
            ),
            "driver_state_sha256": _normalize_digest(
                expected_driver_state_sha256
            ),
        },
        "desktop_interaction": False,
        "ck3_launch_attempted": False,
        "status": "checking",
        "ok": False,
    }
    write_json_atomic(report_path, report)

    try:
        _validate_expectations(
            expected_character_id=expected_character_id,
            expected_episode_run_id=expected_episode_run_id,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
            expected_driver_state_sha256=expected_driver_state_sha256,
        )
        with exclusive_state_lock(
            spec.state_dir, "native-one-generation-preflight"
        ):
            inventory = ck3_process_inventory()
            report["process_inventory"] = inventory
            processes = inventory.get("processes")
            if not isinstance(processes, list):
                raise AgentError("CK3 process inventory is malformed")
            if processes:
                raise AgentError(
                    "one-generation preflight requires zero running ck3.exe "
                    f"processes; observed {len(processes)}"
                )

            manifest = verify_profile(spec)
            report["profile"] = _profile_summary(manifest)
            checkpoint = validate_cold_start_checkpoint_for_pipe(
                spec, pipe_name
            )
            driver_path = (
                spec.state_dir
                / NATIVE_SESSION_QUEUE_DIRNAME
                / NATIVE_DRIVER_STATE_FILENAME
            ).resolve()
            try:
                driver_state = load_native_driver_state_for_resume(
                    driver_path, pipe_name
                )
            except (OSError, UnicodeError, ValueError) as error:
                raise AgentError(
                    "one-generation driver state is not consumer-compatible: "
                    f"{error}"
                ) from error
            if driver_state is None:
                raise AgentError(
                    "one-generation driver state is not consumer-compatible "
                    "with this pipe or format"
                )
            driver_artifact = {
                "path": str(driver_path),
                "size": driver_path.stat().st_size,
                "sha256": sha256_file(driver_path),
                "format_version": driver_state.get("format_version"),
                "pipe_name": pipe_name,
                "episode_character_id": driver_state.get(
                    "episode_character_id"
                ),
                "episode_run_id": driver_state.get("episode_run_id"),
            }
            report["resume_anchor"] = {
                "checkpoint": checkpoint,
                "driver_state": driver_artifact,
            }
            _verify_expected_resume_identity(
                checkpoint=checkpoint,
                driver_state=driver_artifact,
                expected_character_id=expected_character_id,
                expected_episode_run_id=expected_episode_run_id,
                expected_checkpoint_sha256=expected_checkpoint_sha256,
                expected_driver_state_sha256=expected_driver_state_sha256,
            )

            report.update(
                {
                    "finished_at": utc_now(),
                    "status": "ready",
                    "ok": True,
                }
            )
    except Exception as error:
        report.update(
            {
                "finished_at": utc_now(),
                "status": "blocked",
                "error": f"{type(error).__name__}: {error}",
                "ok": False,
            }
        )

    write_json_atomic(report_path, report)
    return report


def _profile_summary(manifest: dict[str, object]) -> dict[str, object]:
    agent_runtime = manifest.get("agent_runtime")
    game = manifest.get("game")
    mod = manifest.get("mod")
    rules = manifest.get("rules")
    return {
        "profile_dir": manifest.get("profile_dir"),
        "environment_sha256": manifest.get("environment_sha256"),
        "agent_runtime_sha256": (
            agent_runtime.get("sha256")
            if isinstance(agent_runtime, dict)
            else None
        ),
        "agent_runtime_revision": (
            agent_runtime.get("git", {}).get("selected_runtime_revision")
            if isinstance(agent_runtime, dict)
            and isinstance(agent_runtime.get("git"), dict)
            else None
        ),
        "ck3_executable_sha256": (
            game.get("executable_sha256")
            if isinstance(game, dict)
            else None
        ),
        "production_tree_sha256": (
            mod.get("production_tree_sha256")
            if isinstance(mod, dict)
            else None
        ),
        "rules_sha256": (
            rules.get("profile_sha256")
            if isinstance(rules, dict)
            else None
        ),
    }


def _verify_expected_resume_identity(
    *,
    checkpoint: dict[str, object],
    driver_state: dict[str, object],
    expected_character_id: int | None,
    expected_episode_run_id: str | None,
    expected_checkpoint_sha256: str | None,
    expected_driver_state_sha256: str | None,
) -> None:
    comparisons = (
        (
            "episode CharacterID",
            driver_state.get("episode_character_id"),
            expected_character_id,
        ),
        (
            "episode run ID",
            driver_state.get("episode_run_id"),
            expected_episode_run_id,
        ),
        (
            "checkpoint SHA-256",
            str(checkpoint.get("sha256", "")).lower(),
            _normalize_digest(expected_checkpoint_sha256),
        ),
        (
            "driver-state SHA-256",
            str(driver_state.get("sha256", "")).lower(),
            _normalize_digest(expected_driver_state_sha256),
        ),
    )
    for label, actual, expected in comparisons:
        if expected is not None and actual != expected:
            raise AgentError(
                f"one-generation {label} differs: "
                f"expected {expected!r}, observed {actual!r}"
            )


def _validate_expectations(
    *,
    expected_character_id: int | None,
    expected_episode_run_id: str | None,
    expected_checkpoint_sha256: str | None,
    expected_driver_state_sha256: str | None,
) -> None:
    if (
        expected_character_id is None
        or isinstance(expected_character_id, bool)
        or not isinstance(expected_character_id, int)
        or expected_character_id <= 0
    ):
        raise AgentError("expected_character_id must be a positive integer")
    if (
        expected_episode_run_id is None
        or not isinstance(expected_episode_run_id, str)
        or not expected_episode_run_id
    ):
        raise AgentError("expected_episode_run_id must be a nonempty string")
    for label, digest in (
        ("expected_checkpoint_sha256", expected_checkpoint_sha256),
        ("expected_driver_state_sha256", expected_driver_state_sha256),
    ):
        normalized = _normalize_digest(digest)
        if (
            normalized is None
            or len(normalized) != 64
            or any(
                character not in "0123456789abcdef"
                for character in normalized
            )
        ):
            raise AgentError(f"{label} must be a 64-character SHA-256")


def _normalize_digest(value: str | None) -> str | None:
    return value.lower() if isinstance(value, str) else None
