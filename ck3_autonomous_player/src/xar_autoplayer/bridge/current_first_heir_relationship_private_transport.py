"""Unadvertised current first-heir relationship read for CK3 1.19.0.6.

This query binds the heir through the public campaign-root observation. It
does not enumerate final-legal candidates, accept an arbitrary CharacterID,
or use a proposal pending record.
"""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .marriage_matchmaking_private_transport import _require_same_paused_frame


STEP = "query-current-first-heir-relationship-v1-private"
SCHEMA = "xar.ck3.current-first-heir-relationship.v1"


def query_current_first_heir_relationship_private_v1(
    driver: object, *, expected_native_revision: int,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_current_first_heir_relationship_query", False) is not True:
        raise UnsupportedStepError("private current first-heir relationship query is disabled")
    before = driver.take_snapshot()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        type(expected_native_revision) is not int
        or expected_native_revision <= 0
        or before.get("native_revision") != expected_native_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or type(played_id) is not int or played_id <= 0
        or type(before.get("revision")) is not int
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError(
            "current heir relationship needs a paused living-player map frame"
        )
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    root = driver._execute_campaign_root_context_v1_query(
        expected_revision=before["revision"]
    )
    partition = root.get("held_title_partition")
    primary = [row for row in partition if isinstance(row, dict)
               and row.get("primary") is True] if isinstance(partition, list) else []
    if (root.get("status") != "available" or len(primary) != 1
            or type(root.get("query_sequence")) is not int
            or root["query_sequence"] <= 0):
        raise BridgeUnavailableError("public primary first-heir binding unavailable")
    heir_id = primary[0].get("first_heir_character_id")
    if heir_id is not None and (type(heir_id) is not int or heir_id <= 0):
        raise BridgeUnavailableError("public primary first-heir ID malformed")
    _require_same_paused_frame(
        driver.take_snapshot(), before, expected_native_revision, played_id
    )
    request_id = "family-relation-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": expected_native_revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(timeout_seconds)
    )
    if frame is None:
        raise BridgeUnavailableError("current heir relationship query timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "current heir relationship query RED: " +
            str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if (
        not isinstance(result, dict)
        or result.get("step") != STEP
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("native_revision") != expected_native_revision
        or result.get("subject_source") !=
           "public_campaign_root_primary_first_heir"
        or result.get("heir_character_id") !=
           (heir_id if heir_id is not None else -1)
    ):
        raise BridgeUnavailableError("current heir relationship identity changed")
    _require_same_paused_frame(
        driver.take_snapshot(), before, expected_native_revision, played_id
    )
    base = {
        "schema": SCHEMA, "schema_version": 1,
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "native_revision": expected_native_revision,
        "root_query_sequence": root["query_sequence"],
        "heir_character_id": heir_id,
    }
    if result.get("status") == "unavailable":
        reason = result.get("unavailable_reason")
        if (not isinstance(reason, str) or not reason
                or result.get("bilateral_verified") is not False
                or result.get("betrothed_character_id") is not None
                or result.get("primary_spouse_character_id") is not None
                or result.get("spouse_character_ids") is not None):
            raise BridgeUnavailableError("unavailable heir relationship is malformed")
        return {**base, "status": "unavailable", "unavailable_reason": reason}
    if result.get("status") != "available" or heir_id is None:
        raise BridgeUnavailableError("current heir relationship status is invalid")
    betrothed = result.get("betrothed_character_id")
    primary_spouse = result.get("primary_spouse_character_id")
    spouses = result.get("spouse_character_ids")
    if (
        result.get("unavailable_reason") is not None
        or result.get("bilateral_verified") is not True
        or any(value is not None and
               (type(value) is not int or value <= 0 or value == heir_id)
               for value in (betrothed, primary_spouse))
        or not isinstance(spouses, list)
        or any(type(value) is not int or value <= 0 or value == heir_id
               for value in spouses)
        or len(set(spouses)) != len(spouses)
        or (betrothed is not None and
            (betrothed == primary_spouse or betrothed in spouses))
    ):
        raise BridgeUnavailableError("available heir relationship is malformed")
    return {**base, "status": "available", "unavailable_reason": None,
            "bilateral_verified": True,
            "betrothed_character_id": betrothed,
            "primary_spouse_character_id": primary_spouse,
            "spouse_character_ids": spouses}
