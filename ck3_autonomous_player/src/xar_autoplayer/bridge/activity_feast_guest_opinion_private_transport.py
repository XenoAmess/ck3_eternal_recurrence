"""Default-off same-frame native opinion read for an ordinary feast guest.

The default result is a relationship value input. An optional full activity ID
adds current native attending-list and character-record observations. Neither
planning membership nor this read alone establishes historical feast rewards.
"""

from __future__ import annotations

import uuid
from typing import cast

from .activity_feast_stage5_start_private_transport import (
    _same_frame, _source_snapshot,
)
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-activity-feast-guest-opinion-v1"
SCHEMA = "activity-feast-guest-opinion-private-read-v1"
REWARD_OPINION_MODIFIER_KEYS = (
    "hosted_feast_opinion", "hosted_mediocre_feast_opinion", "impressed_opinion",
)
_BASE_PAYLOAD_KEYS = {
    "schema", "snapshot_revision", "date_raw", "actor_character_id",
    "guest_character_id", "status", "guest_opinion_of_actor", "read_only",
    "raw_pointer_fields_persisted",
}
_UNAVAILABLE = frozenset({
    "invalid_request", "frame_changed", "opinion_unavailable",
})
_ACTIVITY_TARGET_KEYS = {
    "status", "activity_id", "guest_character_id", "host_character_id",
    "activity_type_key", "native_completed", "native_invalidated",
    "attending_list_observed", "attending_count", "target_in_attending_list",
    "character_record_observed", "character_activity_id",
    "character_activity_state_raw", "character_record_matches_activity",
    "native_active_attendee",
}
_ACTIVITY_TARGET_UNAVAILABLE = frozenset({
    "exact_build_rejected", "frame_rejected", "manager_unavailable",
    "actor_identity_unavailable", "activity_identity_unavailable",
    "target_identity_unavailable", "attending_list_unavailable",
    "character_record_unavailable", "snapshot_changed",
})


def _parse_activity_target(
    target: object, *, activity_id: int, actor_id: int, guest_id: int,
) -> bool:
    if (not isinstance(target, dict) or set(target) != _ACTIVITY_TARGET_KEYS
            or type(target["activity_id"]) is not int
            or target["activity_id"] != activity_id
            or type(target["guest_character_id"]) is not int
            or target["guest_character_id"] != guest_id
            or not isinstance(target["status"], str)):
        raise BridgeUnavailableError("private feast activity target malformed")
    if target["status"] in _ACTIVITY_TARGET_UNAVAILABLE:
        observed_keys = _ACTIVITY_TARGET_KEYS - {
            "status", "activity_id", "guest_character_id",
        }
        if any(target[key] is not None for key in observed_keys):
            raise BridgeUnavailableError("private feast activity target unavailable malformed")
        return False
    if target["status"] != "observed":
        raise BridgeUnavailableError("private feast activity target status unknown")
    if (type(target["host_character_id"]) is not int
            or target["host_character_id"] != actor_id
            or target["activity_type_key"] != "activity_feast"
            or type(target["native_completed"]) is not bool
            or type(target["native_invalidated"]) is not bool
            or target["attending_list_observed"] is not True
            or type(target["attending_count"]) is not int
            or target["attending_count"] < 0
            or type(target["target_in_attending_list"]) is not bool
            or (target["target_in_attending_list"]
                and target["attending_count"] == 0)
            or type(target["character_record_observed"]) is not bool):
        raise BridgeUnavailableError("private feast activity target observation malformed")
    record_keys = {
        "character_activity_id", "character_activity_state_raw",
        "character_record_matches_activity", "native_active_attendee",
    }
    if target["character_record_observed"] is False:
        if any(target[key] is not None for key in record_keys):
            raise BridgeUnavailableError("private feast activity target empty record malformed")
        return True
    if (type(target["character_activity_id"]) is not int
            or not 0 <= target["character_activity_id"] < 2**32
            or type(target["character_activity_state_raw"]) is not int
            or not 0 <= target["character_activity_state_raw"] < 2**32
            or type(target["character_record_matches_activity"]) is not bool
            or type(target["native_active_attendee"]) is not bool):
        raise BridgeUnavailableError("private feast activity target record malformed")
    same_activity = target["character_activity_id"] == activity_id
    active_attendee = (target["target_in_attending_list"] and same_activity
                       and target["character_activity_state_raw"] == 2)
    if (target["character_record_matches_activity"] is not same_activity
            or target["native_active_attendee"] is not active_attendee):
        raise BridgeUnavailableError("private feast activity target predicate malformed")
    return True


def parse_activity_feast_guest_opinion_private_v1(
    payload: object, *, native_revision: int, date_raw: int,
    actor_id: int, guest_id: int, envelope_status: str,
    activity_id: int | None = None,
) -> dict[str, object]:
    expected_keys = _BASE_PAYLOAD_KEYS | ({"activity_target"} if activity_id is not None else set())
    if (not isinstance(payload, dict)
            or set(payload) not in (
                expected_keys,
                expected_keys | {"reward_opinion_modifiers"},
            )
            or payload["schema"] != SCHEMA
            or type(payload["snapshot_revision"]) is not int
            or payload["snapshot_revision"] != native_revision
            or type(payload["date_raw"]) is not int
            or payload["date_raw"] != date_raw
            or type(payload["actor_character_id"]) is not int
            or payload["actor_character_id"] != actor_id
            or type(payload["guest_character_id"]) is not int
            or payload["guest_character_id"] != guest_id
            or payload["read_only"] is not True
            or payload["raw_pointer_fields_persisted"] is not False
            or not isinstance(payload["status"], str)):
        raise BridgeUnavailableError("private feast guest opinion payload malformed")
    status = payload["status"]
    value = payload["guest_opinion_of_actor"]
    if status == "observed":
        if (envelope_status != "available"
                or type(value) is not int or not -100 <= value <= 100):
            raise BridgeUnavailableError("private feast guest opinion value malformed")
    elif status in _UNAVAILABLE:
        if envelope_status != "unavailable" or value is not None:
            raise BridgeUnavailableError("private feast guest opinion unavailable malformed")
    else:
        raise BridgeUnavailableError("private feast guest opinion status unknown")
    if "reward_opinion_modifiers" in payload:
        modifiers = payload["reward_opinion_modifiers"]
        if not isinstance(modifiers, dict) or set(modifiers) != set(REWARD_OPINION_MODIFIER_KEYS):
            raise BridgeUnavailableError("private feast reward modifier keys malformed")
        for row in modifiers.values():
            if not isinstance(row, dict) or set(row) != {"status", "present", "value"}:
                raise BridgeUnavailableError("private feast reward modifier row malformed")
            if row["status"] == "observed":
                if (status != "observed" or type(row["present"]) is not bool
                        or (row["present"] and (type(row["value"]) is not int
                                                or not -(2**31) <= row["value"] < 2**31))
                        or (not row["present"] and row["value"] is not None)):
                    raise BridgeUnavailableError("private feast reward modifier value malformed")
            elif row["status"] == "read_failed":
                if row["present"] is not None or row["value"] is not None:
                    raise BridgeUnavailableError("private feast reward modifier failure malformed")
            else:
                raise BridgeUnavailableError("private feast reward modifier status unknown")
    parsed = dict(payload)
    if activity_id is not None:
        parsed["activity_target_ready"] = _parse_activity_target(
            payload["activity_target"], activity_id=activity_id,
            actor_id=actor_id, guest_id=guest_id,
        )
    return parsed


def query_activity_feast_guest_opinion_private_v1(
    driver: object, *, expected_revision: int, guest_character_id: int,
    activity_id: int | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_opinion_query", False) is not True:
        raise UnsupportedStepError("private feast guest opinion query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if (type(guest_character_id) is not int
            or not 0 < guest_character_id < 2**31):
        raise ValueError("guest_character_id must be a positive full CharacterID")
    if activity_id is not None and (type(activity_id) is not int
                                   or not 0 < activity_id < 2**32 - 1):
        raise ValueError("activity_id must be a positive nonempty full ActivityID")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast guest opinion revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    if guest_character_id == actor_id:
        raise ValueError("guest_character_id must differ from the host")
    request_id = "activity-feast-guest-opinion-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "guest_character_id": guest_character_id,
    }
    if activity_id is not None:
        request["activity_id"] = activity_id
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast guest opinion result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast guest opinion native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_opinion", "backend_id",
            }
            or envelope["step"] != STEP
            or envelope["accepted"] is not True
            or envelope["status"] not in {"available", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast guest opinion envelope malformed")
    payload = parse_activity_feast_guest_opinion_private_v1(
        envelope["activity_feast_guest_opinion"],
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
        guest_id=guest_character_id, envelope_status=envelope["status"],
        activity_id=activity_id,
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast guest opinion crossed paused frame")
    return {**payload, **provenance, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
