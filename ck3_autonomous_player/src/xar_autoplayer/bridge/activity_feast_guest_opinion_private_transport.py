"""Default-off same-frame native opinion read for an ordinary feast guest.

The result is a relationship value input. It does not establish invite-rule
membership, invitation legality, acceptance, attendance or feast rewards.
"""

from __future__ import annotations

import uuid
from typing import cast

from .activity_feast_stage5_start_private_transport import (
    _same_frame, _source_snapshot,
)
from .driver import BridgeUnavailableError, UnsupportedStepError


STEP = "query-activity-feast-guest-opinion-v1"
SCHEMA = "activity-feast-guest-opinion-private-read-v1"
_UNAVAILABLE = frozenset({
    "invalid_request", "frame_changed", "opinion_unavailable",
})


def parse_activity_feast_guest_opinion_private_v1(
    payload: object, *, native_revision: int, date_raw: int,
    actor_id: int, guest_id: int, envelope_status: str,
) -> dict[str, object]:
    if (not isinstance(payload, dict)
            or set(payload) != {
                "schema", "snapshot_revision", "date_raw",
                "actor_character_id", "guest_character_id", "status",
                "guest_opinion_of_actor", "read_only",
                "raw_pointer_fields_persisted",
            }
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
    return dict(payload)


def query_activity_feast_guest_opinion_private_v1(
    driver: object, *, expected_revision: int, guest_character_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_opinion_query", False) is not True:
        raise UnsupportedStepError("private feast guest opinion query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if (type(guest_character_id) is not int
            or not 0 < guest_character_id < 2**31):
        raise ValueError("guest_character_id must be a positive full CharacterID")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast guest opinion revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    if guest_character_id == actor_id:
        raise ValueError("guest_character_id must differ from the host")
    request_id = "activity-feast-guest-opinion-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "guest_character_id": guest_character_id,
    })
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
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast guest opinion crossed paused frame")
    return {**payload, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
