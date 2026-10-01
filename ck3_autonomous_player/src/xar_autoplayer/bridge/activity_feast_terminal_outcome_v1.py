"""Interpret explicit native Feast terminal flags for one persisted identity.

The 1.20 native completed flag is set after the completion effects return.
Missing hosted identities and legacy rows without these flags stay unknown.
This observation does not assign utility or attribute resource/opinion gains.
"""

from __future__ import annotations

from collections.abc import Mapping

from .activity_feast_stage5_start_private_transport import POST_SCHEMA, _hosted
from .driver import BridgeUnavailableError


SCHEMA = "xar.ck3.activity-feast-terminal-outcome.v1"


def normalize_activity_feast_terminal_outcome_v1(
    post: Mapping[str, object], *, activity_id: int, actor_character_id: int,
) -> dict[str, object]:
    """Return native completion/invalidation, including a possible overlap."""
    if (type(activity_id) is not int or not 0 < activity_id <= 0xFFFFFFFF
            or type(actor_character_id) is not int
            or not 0 < actor_character_id <= 0xFFFFFFFF):
        raise ValueError("Feast terminal observation needs full positive identities")
    if (post.get("schema") != POST_SCHEMA
            or type(post.get("snapshot_revision")) is not int
            or post["snapshot_revision"] <= 0
            or type(post.get("date_raw")) is not int
            or post["date_raw"] < 0
            or post.get("read_only") is not True):
        raise BridgeUnavailableError("private feast terminal post read malformed")
    rows = _hosted(post.get("hosted_activities"))
    outcome: dict[str, object] = {
        "schema": SCHEMA,
        "activity_id": activity_id,
        "actor_character_id": actor_character_id,
        "snapshot_revision": post["snapshot_revision"],
        "date_raw": post["date_raw"],
        "status": "unknown",
        "terminal_flags_observed": False,
        "native_completed": None,
        "native_invalidated": None,
        "unknown_reason": "activity_not_observed",
        "read_only": True,
    }
    for key in ("exact_ck3_build", "exe_sha256", "queried_snapshot_id"):
        if key in post:
            outcome[key] = post[key]
    if post.get("actor_character_id") != actor_character_id:
        outcome["unknown_reason"] = "host_frame_mismatch"
        return outcome
    row = next((row for row in rows if row["activity_id"] == activity_id), None)
    if row is None:
        return outcome
    if (row["host_character_id"] != actor_character_id
            or row["activity_type_key"] != "activity_feast"):
        outcome["unknown_reason"] = "activity_identity_mismatch"
        return outcome
    if row.get("terminal_flags_observed") is not True:
        outcome["unknown_reason"] = "terminal_flags_unobserved"
        return outcome
    completed = row["native_completed"]
    invalidated = row["native_invalidated"]
    if completed and invalidated:
        status = "completed_and_invalidated"
    elif completed:
        status = "completed"
    elif invalidated:
        status = "invalidated"
    else:
        status = "ongoing"
    outcome.update({
        "status": status,
        "terminal_flags_observed": True,
        "native_completed": completed,
        "native_invalidated": invalidated,
        "unknown_reason": None,
    })
    return outcome
