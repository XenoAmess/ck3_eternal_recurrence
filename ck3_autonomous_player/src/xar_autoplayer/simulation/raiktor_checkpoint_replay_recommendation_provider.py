"""Rebind one immutable-checkpoint GEN-034 continue recommendation."""

from __future__ import annotations

from copy import deepcopy
import re

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (
    CONTRACT as SOURCE_CONTRACT,
    PROVIDER_ID as SOURCE_PROVIDER_ID,
    PROVIDER_SCHEMA as SOURCE_PROVIDER_SCHEMA,
)


CONTRACT = "raiktor-checkpoint-replay-recommendation-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_checkpoint_replay_recommendation.v1"
PROVIDER_ID = "raiktor-checkpoint-replay-recommendation-provider-v1"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
_STATE_FRAME_FIELDS = {
    "snapshot_id": "snapshot_id",
    "snapshot_revision": "revision",
    "native_revision": "native_revision",
    "date_raw": "date_raw",
    "episode_id": "episode_run_id",
}


class CheckpointReplayRecommendationError(ValueError):
    """The source recommendation or target checkpoint identity drifted."""


def provide_raiktor_checkpoint_replay_recommendation(
    source_recommendation_value: object,
    target_snapshot_value: object,
    *,
    source_checkpoint_sha256: str,
    target_checkpoint_sha256: str,
    source_driver_state_sha256: str,
    target_driver_state_sha256: str,
) -> dict[str, object]:
    """Rebind a production continue decision before any gameplay command."""

    source = _object(source_recommendation_value, "source recommendation")
    source_certificate = _object(
        source.get("recommendation_certificate"), "source certificate"
    )
    if (
        source.get("schema") != SOURCE_PROVIDER_SCHEMA
        or source.get("provider") != SOURCE_PROVIDER_ID
        or source.get("status") != "production_recommendation_available"
        or source.get("production_recommendation_ready") is not True
        or source.get("action_ready") is not True
        or source.get("recommended_outcome") != "continue"
        or source.get("action_literal") != "resume-map"
        or source.get("blockers") != []
        or source_certificate.get("contract") != SOURCE_CONTRACT
        or source_certificate.get("recommended_outcome") != "continue"
    ):
        raise CheckpointReplayRecommendationError(
            "source is not a production continue recommendation"
        )
    source_digest = source_certificate.get("certificate_sha256")
    source_unhashed = {
        key: value
        for key, value in source_certificate.items()
        if key != "certificate_sha256"
    }
    if (
        not _is_sha256(source_digest)
        or canonical_policy_input_sha256(source_unhashed) != source_digest
    ):
        raise CheckpointReplayRecommendationError(
            "source recommendation hash drifted"
        )
    source_frame = _object(source_certificate.get("frame"), "source frame")
    target = _target_frame(target_snapshot_value, source_frame=source_frame)
    if source_frame.get("ck3_pid") == target.get("ck3_pid"):
        raise CheckpointReplayRecommendationError(
            "checkpoint replay requires a distinct runtime process"
        )

    checkpoint = _equal_sha256(
        source_checkpoint_sha256,
        target_checkpoint_sha256,
        "checkpoint",
    )
    driver_state = _equal_sha256(
        source_driver_state_sha256,
        target_driver_state_sha256,
        "driver state",
    )
    certificate = deepcopy(source_certificate)
    certificate["contract"] = CONTRACT
    certificate["frame"] = target
    certificate["checkpoint_replay"] = {
        "source_recommendation_certificate_sha256": source_digest,
        "checkpoint_sha256": checkpoint,
        "driver_state_sha256": driver_state,
        "source_runtime_frame": deepcopy(source_frame),
        "target_runtime_frame": deepcopy(target),
        "same_runtime_frame": False,
        "immutable_checkpoint_state_equivalent": True,
    }
    certificate["boundaries"][
        "checkpoint_replay_recommendation_input"
    ] = True
    certificate.pop("certificate_sha256", None)
    certificate["certificate_sha256"] = canonical_policy_input_sha256(
        certificate
    )

    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "production_recommendation_available",
        "recommendation_ready": True,
        "production_recommendation_ready": True,
        "recommended_outcome": "continue",
        "action_ready": True,
        "action_literal": "resume-map",
        "postcondition_verified": False,
        "gen034_closed": False,
        "recommendation_certificate": certificate,
        "immediate_exit_evaluation": deepcopy(
            source.get("immediate_exit_evaluation")
        ),
        "blockers": [],
        "boundaries": [
            "immutable_checkpoint_and_driver_state_only",
            "source_and_target_runtime_frames_remain_distinct",
            "continue_route_only",
            "provider_does_not_authorize_or_submit_an_action",
        ],
    }


def _target_frame(
    snapshot_value: object, *, source_frame: dict[str, object]
) -> dict[str, object]:
    snapshot = _object(snapshot_value, "target snapshot")
    diagnostics = _object(snapshot.get("diagnostics"), "target diagnostics")
    played = _object(snapshot.get("played_character"), "target player")
    if snapshot.get("paused") is not True or snapshot.get("active_event") is not None:
        raise CheckpointReplayRecommendationError(
            "target must be a clear paused frame"
        )
    for frame_key, snapshot_key in _STATE_FRAME_FIELDS.items():
        if source_frame.get(frame_key) != snapshot.get(snapshot_key):
            raise CheckpointReplayRecommendationError(
                f"target gameplay identity drifted: {frame_key}"
            )
    connection = source_frame.get("connection_id")
    expected_connection = f"connection-generation:{diagnostics.get('connection_generation')}"
    if connection != expected_connection:
        raise CheckpointReplayRecommendationError(
            "target gameplay identity drifted: connection_id"
        )
    if played.get("character_id") != source_frame.get(
        "primary_attacker_character_id"
    ):
        raise CheckpointReplayRecommendationError(
            "target gameplay identity drifted: played character"
        )
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        raise CheckpointReplayRecommendationError("target active wars are absent")
    matches = [
        row
        for row in wars
        if isinstance(row, dict)
        and row.get("war_id") == source_frame.get("war_id")
        and row.get("primary_opponent_character_id")
        == source_frame.get("primary_defender_character_id")
        and row.get("player_side") == "attacker"
        and row.get("player_is_primary_war_leader") is True
    ]
    if len(matches) != 1:
        raise CheckpointReplayRecommendationError(
            "target gameplay identity drifted: active war"
        )
    pid = diagnostics.get("bridge_pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise CheckpointReplayRecommendationError("target PID is malformed")
    target = deepcopy(source_frame)
    target["ck3_pid"] = pid
    return target


def _equal_sha256(left: object, right: object, name: str) -> str:
    if not _is_sha256(left) or not _is_sha256(right) or left != right:
        raise CheckpointReplayRecommendationError(
            f"checkpoint replay {name} identity drifted"
        )
    return str(left)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CheckpointReplayRecommendationError(f"{name} is malformed")
    return value


__all__ = [
    "CONTRACT",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "CheckpointReplayRecommendationError",
    "provide_raiktor_checkpoint_replay_recommendation",
]
