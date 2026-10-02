"""Default-off paused native read for one sway target; no action is sent."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance
from .version_identity import CK3_12002, CK3_12003


STEP_PREFIX = "query-active-scheme-sway-target-v1-private-"
SCHEMA = "active-scheme-sway-private-read-v1"
_ENVELOPE_KEYS = {
    "step", "accepted", "status", "private_build", "read_only",
    "advertised", "active_scheme_sway", "backend_id",
}
_VALUE_KEYS = {
    "schema", "snapshot_revision", "capture_epoch", "container_generation",
    "date_raw", "actor_character_id", "target_character_id",
    "target_opinion_of_actor",
    "active_scheme_count", "matching_sway_active", "native_complete_can_send",
    "native_legal_now", "native_failure_classification",
}
_ACTIVE_SWAY_KEYS = {
    "scheme_instance_id", "scheme_instance_generation", "target_character_id",
    "progress", "progress_goal", "is_exposed", "is_frozen",
}


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _valid_active_sway_instances(value: Mapping[str, object]) -> bool:
    rows = value.get("active_sway_instances")
    if (not isinstance(rows, list)
            or len(rows) > value["active_scheme_count"]):
        return False
    for row in rows:
        if not isinstance(row, dict) or set(row) != _ACTIVE_SWAY_KEYS:
            return False
        if (not _positive_int(row["scheme_instance_id"])
                or row["scheme_instance_id"] > 0xFFFFFFFF
                or type(row["scheme_instance_generation"]) is not int
                or not 0 <= row["scheme_instance_generation"] <= 255
                or not _positive_int(row["target_character_id"])
                or row["target_character_id"] > 0xFFFFFFFF
                or type(row["progress"]) is not int
                or type(row["progress_goal"]) is not int
                or not 0 <= row["progress"] <= row["progress_goal"] <= 0x7FFFFFFF
                or row["progress_goal"] == 0
                or type(row["is_exposed"]) is not bool
                or type(row["is_frozen"]) is not bool):
            return False
    return value["matching_sway_active"] == any(
        row["target_character_id"] == value["target_character_id"] for row in rows
    )


def query_active_scheme_sway_target_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_active_scheme_sway_query", False) is not True:
        raise UnsupportedStepError("private active-scheme sway query is disabled")
    if not _positive_int(expected_revision):
        raise ValueError("expected_revision must be positive")
    if not _positive_int(target_character_id) or target_character_id > 0xFFFFFFFF:
        raise ValueError("target_character_id must be a full 32-bit character ID")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    internal_reader = getattr(driver, "take_internal_semantic_snapshot", None)
    read_frame = internal_reader if callable(internal_reader) else driver.take_snapshot
    before = read_frame()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(actor, Mapping)
        or actor.get("alive") is not True
        or not _positive_int(actor.get("character_id"))
        or actor["character_id"] == target_character_id
        or not _positive_int(native_revision)
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError("private sway requires a living player on a paused map frame")
    provenance = private_native_provenance(before)
    current_build = provenance["exact_ck3_build"] in (CK3_12002.game_version, CK3_12003.game_version)
    expected_keys = _VALUE_KEYS | {"active_sway_instances"} if current_build else _VALUE_KEYS
    step = f"{STEP_PREFIX}{target_character_id}"
    request_id = "sway-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("private sway command_result timed out")
    if (
        not isinstance(frame, dict)
        or frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
    ):
        raise BridgeUnavailableError("private sway command_result malformed")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private sway native RED: " + str(frame.get("error", "unknown"))
        )
    envelope = frame.get("result")
    if (
        not isinstance(envelope, dict)
        or set(envelope) != _ENVELOPE_KEYS
        or envelope.get("step") != step
        or envelope.get("accepted") is not True
        or envelope.get("status") != "available"
        or envelope.get("private_build") is not True
        or envelope.get("read_only") is not True
        or envelope.get("advertised") is not False
        or envelope.get("backend_id") != "native-headless"
    ):
        raise BridgeUnavailableError("private sway envelope malformed")
    value = envelope.get("active_scheme_sway")
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schema") != SCHEMA
        or value.get("snapshot_revision") != native_revision
        or not _positive_int(value.get("capture_epoch"))
        or not _positive_int(value.get("container_generation"))
        or value.get("date_raw") != before["date_raw"]
        or value.get("actor_character_id") != actor["character_id"]
        or value.get("target_character_id") != target_character_id
        or type(value.get("target_opinion_of_actor")) is not int
        or type(value.get("active_scheme_count")) is not int
        or not 0 <= value["active_scheme_count"] <= 32
        or type(value.get("matching_sway_active")) is not bool
        or type(value.get("native_complete_can_send")) is not bool
        or type(value.get("native_legal_now")) is not bool
        or not isinstance(value.get("native_failure_classification"), str)
        or value["native_failure_classification"] not in {
            "", "native_complete_validator_rejected",
        }
        or (
            value["native_legal_now"]
            and (value["matching_sway_active"]
                 or not value["native_complete_can_send"])
        )
        or (current_build and not _valid_active_sway_instances(value))
    ):
        raise BridgeUnavailableError("private sway native payload malformed")
    after = read_frame()
    if (
        after.get("paused") is not True
        or after.get("date_raw") != before["date_raw"]
        or after.get("played_character") != actor
    ):
        raise BridgeUnavailableError("private sway read crossed the paused actor/date frame")
    return {
        **value,
        **provenance,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after.get("snapshot_id"),
    }
