"""Interpret explicit native Feast terminal flags for one persisted identity.

Native flags come from a guarded hosted row or an exact retained cut record.
Missing records and unread fields stay unknown; downstream effects are separate.
This observation does not assign utility or attribute resource/opinion gains.
"""

from __future__ import annotations

from collections.abc import Mapping

from .activity_feast_stage5_start_private_transport import (
    POST_SCHEMA, _hosted, _native_terminal_observations,
)
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
    journal = _native_terminal_observations(
        post.get("native_terminal_observations"), actor_id=actor_character_id,
    )
    if "native_terminal_observations" in post:
        outcome["native_terminal_observations_coverage"] = (
            {key: value for key, value in journal.items() if key != "records"}
            if journal is not None else None)
    row = next((row for row in rows if row["activity_id"] == activity_id), None)
    if row is None:
        # A retained cut is a historical source observation, not a live object.
        for source in reversed(journal["records"] if journal is not None else []):
            if (source["activity_full_id_u32"] != activity_id
                    or source["activity_instance_generation_u8"] != activity_id >> 24
                    or (source["host_character_id_i32"] & 0xFFFFFFFF) != actor_character_id
                    or source["type_key"] != "activity_feast"):
                continue
            completed = source["completed_raw_u8"] != 0 if source["completed_observed"] else None
            invalidated = source["invalidated_raw_u8"] != 0 if source["invalidated_observed"] else None
            if completed is not True and invalidated is not True:
                continue
            outcome.update({
                "status": "completed_and_invalidated" if completed is True and invalidated is True
                    else "completed" if completed is True else "invalidated",
                "terminal_flags_observed": source["completed_observed"] and source["invalidated_observed"],
                "native_completed": completed, "native_invalidated": invalidated,
                "native_completion_stamp_observed": source["native_completion_stamp_observed"],
                "native_completion_stamp_raw": source["native_completion_stamp_raw_u64"],
                "native_terminal_observation": source, "unknown_reason": None,
            })
            break
        return outcome
    if (row["host_character_id"] != actor_character_id
            or row["activity_type_key"] != "activity_feast"):
        outcome["unknown_reason"] = "activity_identity_mismatch"
        return outcome
    # This raw native QWORD is independent of terminal flags and query date.
    # Its successful zero has no inferred sentinel, units or completion meaning.
    if "native_completion_stamp_observed" in row:
        outcome.update({
            "native_completion_stamp_observed": row["native_completion_stamp_observed"],
            "native_completion_stamp_raw": row["native_completion_stamp_raw"],
        })
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
