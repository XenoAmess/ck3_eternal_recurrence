"""Private default-OFF wire contract for exact-store war-bound cleanup."""

from __future__ import annotations

import copy

from .raiktor_war_bound_regiment_contract import (
    normalize_raiktor_war_bound_regiment,
)


QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY = (
    "game.command.query-raiktor-war-bound-loss-cleanup-v1-N"
)
QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX = (
    "query-raiktor-war-bound-loss-cleanup-v1-"
)
_WIRE_KEYS = {
    "step",
    "accepted",
    "query_sequence",
    "snapshot_revision",
    "raiktor_war_bound_loss_cleanup",
    "backend_id",
}


def parse_query_raiktor_war_bound_loss_cleanup_v1_step(
    step: object,
) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX
    ):
        return None
    suffix = step[len(QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX) :]
    if (
        not suffix
        or not suffix.isascii()
        or not suffix.isdecimal()
        or suffix.startswith("0")
    ):
        return None
    value = int(suffix)
    return value if 0 < value <= 2**31 - 1 else None


def normalize_raiktor_war_bound_loss_cleanup_v1(
    value: object,
    *,
    expected_step: str,
    expected_war_id: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
    expected_active_public_revision: int,
    expected_active_native_revision: int,
    expected_active_date_raw: int,
    expected_post_public_revision: int,
    expected_post_native_revision: int,
    expected_post_date_raw: int,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _WIRE_KEYS:
        raise ValueError("war-bound cleanup wire envelope is malformed")
    if (
        value.get("step") != expected_step
        or value.get("accepted") is not True
        or value.get("backend_id") != "native-headless"
    ):
        raise ValueError("war-bound cleanup wire identity disagrees")
    sequence = value.get("query_sequence")
    snapshot_revision = value.get("snapshot_revision")
    if (
        isinstance(sequence, bool)
        or not isinstance(sequence, int)
        or sequence <= 0
        or isinstance(snapshot_revision, bool)
        or not isinstance(snapshot_revision, int)
        or snapshot_revision != expected_post_native_revision
    ):
        raise ValueError("war-bound cleanup wire revision is malformed")
    normalized = normalize_raiktor_war_bound_regiment(
        value.get("raiktor_war_bound_loss_cleanup"),
        expected_war_id=expected_war_id,
        expected_attacker_character_id=expected_attacker_character_id,
        expected_defender_character_id=expected_defender_character_id,
        # The DLL knows only its native revision. The Python bridge binds the
        # two snapshot_revision fields to the public frame only after this
        # exact native payload has passed validation.
        expected_snapshot_revision=expected_active_native_revision,
        expected_native_revision=expected_active_native_revision,
        expected_date_raw=expected_active_date_raw,
    )
    post = normalized.get("postwar_frame")
    if not isinstance(post, dict) or post != {
        "snapshot_revision": expected_post_native_revision,
        "native_revision": expected_post_native_revision,
        "date_raw": expected_post_date_raw,
        "paused": True,
        "frozen_war_id": expected_war_id,
        "frozen_war_absent_from_active_wars": True,
    }:
        raise ValueError("war-bound cleanup postwar frame disagrees")
    rebound = copy.deepcopy(normalized)
    rebound["active_frame"]["snapshot_revision"] = (
        expected_active_public_revision
    )
    rebound["postwar_frame"]["snapshot_revision"] = (
        expected_post_public_revision
    )
    normalized = normalize_raiktor_war_bound_regiment(
        rebound,
        expected_war_id=expected_war_id,
        expected_attacker_character_id=expected_attacker_character_id,
        expected_defender_character_id=expected_defender_character_id,
        expected_snapshot_revision=expected_active_public_revision,
        expected_native_revision=expected_active_native_revision,
        expected_date_raw=expected_active_date_raw,
    )
    return {
        "query_sequence": sequence,
        "snapshot_revision": snapshot_revision,
        "observation": copy.deepcopy(normalized),
    }
