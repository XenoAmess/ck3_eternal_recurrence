#!/usr/bin/env python3
"""Compose a GEN-034 recommendation from one immutable checkpoint replay.

This tool never starts or attaches to CK3.  It joins a bound direct strategic-
power report with the successful exit reads retained by a later failed live
attempt, while preserving the distinct source and target runtime frames.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from prepare_g2_campaign_dominance_certificate import (  # noqa: E402
    render_receipt as render_direct_dominance_receipt,
)
from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (  # noqa: E402
    provide_raiktor_checkpoint_replay_dominance,
)
from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (  # noqa: E402
    provide_raiktor_exit_utility_model,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (  # noqa: E402
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (  # noqa: E402
    provide_raiktor_three_way_exit_recommendation,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)


OUTPUT_SCHEMA = "xar.ck3.gen034_checkpoint_replay_recommendation.v1"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def compose_recommendation(
    *,
    power_report_path: Path,
    power_report_sha256: str,
    power_reclassification_path: Path,
    power_reclassification_sha256: str,
    exit_report_path: Path,
    exit_report_sha256: str,
    exit_driver_state_path: Path,
    exit_driver_state_sha256: str,
    checkpoint_path: Path,
    checkpoint_sha256: str,
    source_driver_state_path: Path,
    source_driver_state_sha256: str,
    war_id: int,
    opponent_character_id: int,
) -> dict[str, object]:
    """Return a hash-bound recommendation without contacting a live bridge."""

    direct_receipt = render_direct_dominance_receipt(
        power_report_path,
        power_report_sha256,
        reclassification_path=power_reclassification_path,
        reclassification_sha256=power_reclassification_sha256,
        war_id=war_id,
        opponent_character_id=opponent_character_id,
    )
    exit_report = _json(
        _read_bound(exit_report_path, exit_report_sha256, "exit report"),
        "exit report",
    )
    exit_driver = _json(
        _read_bound(
            exit_driver_state_path,
            exit_driver_state_sha256,
            "exit final driver state",
        ),
        "exit final driver state",
    )
    _read_bound(checkpoint_path, checkpoint_sha256, "checkpoint")
    _read_bound(
        source_driver_state_path,
        source_driver_state_sha256,
        "source driver state",
    )
    _validate_failed_exit_attempt(exit_report)
    options, terms = _retained_exit_reads(exit_driver, war_id=war_id)
    snapshot = _snapshot_from_readiness(exit_report)

    projection = provide_raiktor_white_peace_narrow_projection(
        snapshot,
        options,
        terms,
        production_live=True,
    )
    if projection.get("observation_ready") is not True:
        raise ValueError("retained exit reads did not produce an observation")
    observation = _object(
        projection.get("white_peace_observation"),
        "white-peace observation",
    )
    target_frame = _dominance_frame(
        _object(observation.get("frame"), "white-peace frame")
    )
    source_certificate = _object(
        _object(
            direct_receipt.get("provider_result"),
            "direct dominance provider",
        ).get("campaign_dominance_certificate"),
        "direct dominance certificate",
    )
    replay = provide_raiktor_checkpoint_replay_dominance(
        source_certificate,
        target_frame,
        source_checkpoint_sha256=checkpoint_sha256,
        target_checkpoint_sha256=checkpoint_sha256,
        source_driver_state_sha256=source_driver_state_sha256,
        target_driver_state_sha256=source_driver_state_sha256,
    )
    recommendation = provide_raiktor_three_way_exit_recommendation(
        projection,
        terms.get("raiktor_surrender_aggregate_session"),
        replay["campaign_dominance_certificate"],
        provide_raiktor_owner_budget_profile(None),
        provide_raiktor_exit_utility_model(),
    )
    if (
        recommendation.get("recommendation_ready") is not True
        or recommendation.get("production_recommendation_ready") is not True
    ):
        raise ValueError("checkpoint replay did not produce a recommendation")
    certificate = _object(
        recommendation.get("recommendation_certificate"),
        "recommendation certificate",
    )

    return {
        "schema": OUTPUT_SCHEMA,
        "status": "GREEN",
        "ok": True,
        "source_live_attempt_status": "RED_preserved",
        "inputs": {
            "power_report": _binding(
                power_report_path, power_report_sha256
            ),
            "power_reclassification": _binding(
                power_reclassification_path,
                power_reclassification_sha256,
            ),
            "exit_report": _binding(exit_report_path, exit_report_sha256),
            "exit_final_driver_state": _binding(
                exit_driver_state_path, exit_driver_state_sha256
            ),
            "checkpoint": _binding(checkpoint_path, checkpoint_sha256),
            "source_driver_state": _binding(
                source_driver_state_path, source_driver_state_sha256
            ),
        },
        "retained_exit_read_commands": [
            f"query-war-termination-options-{war_id}",
            f"query-war-termination-terms-v1-{war_id}",
        ],
        "direct_dominance_receipt": direct_receipt,
        "exit_projection": projection,
        "checkpoint_replay_dominance": replay,
        "recommendation": recommendation,
        "decision": {
            "recommended_outcome": certificate["recommended_outcome"],
            "action_plan": certificate["action_plan"],
            "action_authorization_ready": False,
            "action_submitted": False,
            "postcondition_verified": False,
            "gen034_closed": False,
        },
        "boundaries": {
            "ck3_started_or_attached": False,
            "same_runtime_frame_claimed": False,
            "immutable_checkpoint_state_replay": True,
            "source_red_reclassified": False,
            "current_live_session_available": False,
            "action_authorization_ready": False,
            "action_submitted": False,
        },
    }


def _validate_failed_exit_attempt(report: dict[str, object]) -> None:
    if (
        report.get("kind")
        != "ck3_gen034_three_way_recommendation_live_acceptance"
        or report.get("status") != "red"
        or report.get("ok") is not False
        or report.get("mcp_sequence") is not None
    ):
        raise ValueError("exit report is not the retained failed attempt")
    cleanup = _object(report.get("cleanup"), "exit report cleanup")
    if cleanup.get("cleanup_proven") is not True:
        raise ValueError("exit report did not prove process cleanup")


def _retained_exit_reads(
    driver: dict[str, object], *, war_id: int
) -> tuple[dict[str, object], dict[str, object]]:
    history = driver.get("command_history")
    if not isinstance(history, list) or len(history) < 3:
        raise ValueError("exit driver history is incomplete")
    expected = [
        (f"query-war-termination-options-{war_id}", True),
        (f"query-war-termination-terms-v1-{war_id}", True),
        None,
    ]
    tail = history[-3:]
    observed = [
        (row.get("command"), row.get("ok"))
        if isinstance(row, dict)
        else None
        for row in tail
    ]
    if observed[:2] != expected[:2]:
        raise ValueError("exit reads are not the final two successful reads")
    failed = _object(tail[2], "failed power history row")
    if (
        failed.get("ok") is not False
        or not str(failed.get("command", "")).startswith(
            "query-war-entry-assessments-v1-"
        )
        or "application-main war-entry query failed"
        not in str(failed.get("error", ""))
    ):
        raise ValueError("exit attempt did not retain the expected power RED")
    return (
        _object(_object(tail[0], "options row").get("result"), "options"),
        _object(_object(tail[1], "terms row").get("result"), "terms"),
    )


def _snapshot_from_readiness(report: dict[str, object]) -> dict[str, object]:
    readiness = _object(report.get("readiness"), "readiness")
    snapshot = dict(_object(readiness.get("_semantic"), "semantic snapshot"))
    for key in (
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
        "paused",
        "map_ready",
        "episode_run_id",
        "episode_character_id",
    ):
        snapshot[key] = readiness.get(key)
    snapshot["diagnostics"] = {
        "bridge_pid": readiness.get("bridge_pid"),
        "connection_generation": readiness.get("connection_generation"),
    }
    return snapshot


def _dominance_frame(frame: dict[str, object]) -> dict[str, object]:
    connection = frame.get("connection_id")
    prefix = "connection-generation:"
    if not isinstance(connection, str) or not connection.startswith(prefix):
        raise ValueError("projection connection identity is malformed")
    try:
        generation = int(connection.removeprefix(prefix))
    except ValueError as exc:
        raise ValueError("projection connection identity is malformed") from exc
    return {
        "snapshot_id": frame.get("snapshot_id"),
        "snapshot_revision": frame.get("snapshot_revision"),
        "native_revision": frame.get("native_revision"),
        "date_raw": frame.get("date_raw"),
        "connection_generation": generation,
        "ck3_pid": frame.get("ck3_pid"),
        "episode_run_id": frame.get("episode_id"),
        "paused": frame.get("paused"),
        "war_id": frame.get("war_id"),
        "actor_character_id": frame.get("primary_attacker_character_id"),
        "opponent_character_id": frame.get("primary_defender_character_id"),
    }


def _read_bound(path: Path, expected_sha: str, name: str) -> bytes:
    expected = _sha256(expected_sha, f"{name} SHA-256")
    payload = path.resolve().read_bytes()
    actual = hashlib.sha256(payload).hexdigest().upper()
    if actual != expected:
        raise ValueError(f"{name} hash differs from expected SHA-256")
    return payload


def _json(payload: bytes, name: str) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} must be valid UTF-8 JSON") from exc
    return _object(value, name)


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be an uppercase SHA-256")
    return value


def _binding(path: Path, sha256: str) -> dict[str, str]:
    return {"path": str(path.resolve()), "sha256": sha256}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--power-report", type=Path, required=True)
    parser.add_argument("--power-report-sha256", required=True)
    parser.add_argument("--power-reclassification", type=Path, required=True)
    parser.add_argument("--power-reclassification-sha256", required=True)
    parser.add_argument("--exit-report", type=Path, required=True)
    parser.add_argument("--exit-report-sha256", required=True)
    parser.add_argument("--exit-driver-state", type=Path, required=True)
    parser.add_argument("--exit-driver-state-sha256", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--source-driver-state-sha256", required=True)
    parser.add_argument("--war-id", type=int, required=True)
    parser.add_argument("--opponent-character-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        print(f"ERROR: output already exists: {output}", file=sys.stderr)
        return 2
    try:
        result = compose_recommendation(
            power_report_path=args.power_report,
            power_report_sha256=args.power_report_sha256,
            power_reclassification_path=args.power_reclassification,
            power_reclassification_sha256=(
                args.power_reclassification_sha256
            ),
            exit_report_path=args.exit_report,
            exit_report_sha256=args.exit_report_sha256,
            exit_driver_state_path=args.exit_driver_state,
            exit_driver_state_sha256=args.exit_driver_state_sha256,
            checkpoint_path=args.checkpoint,
            checkpoint_sha256=args.checkpoint_sha256,
            source_driver_state_path=args.source_driver_state,
            source_driver_state_sha256=args.source_driver_state_sha256,
            war_id=args.war_id,
            opponent_character_id=args.opponent_character_id,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
