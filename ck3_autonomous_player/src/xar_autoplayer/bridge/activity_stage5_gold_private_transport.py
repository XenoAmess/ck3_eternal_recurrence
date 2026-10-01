"""Default-off typed read of a paused stage-5 feast's named Gold values."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Literal, NotRequired, TypedDict, cast

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-activity-stage5-gold-cost-v1-private"
SCHEMA = "activity-stage5-gold-cost-private-read-v1"
_MAX_I64 = 2**63 - 1
_MIN_I64 = -(2**63)
_MAX_U64 = 2**64 - 1


class GoldQ100000V1(TypedDict):
    resource: str
    raw: int
    scale: int
    source: str


class ActivityStage5GoldPayloadV1(TypedDict):
    schema: str
    snapshot_revision: int
    date_raw: int
    actor_character_id: int
    activity_key: str
    planning_stage: int
    normal_refresh_sequence: int
    configured_cost: GoldQ100000V1
    resource_value: GoldQ100000V1
    final_can_start: None
    raw_slot12_resource_mapping: None
    read_only: bool
    raw_pointer_fields_persisted: bool


class ActivityStage5GoldReadV1(ActivityStage5GoldPayloadV1):
    exact_ck3_build: str
    exe_sha256: NotRequired[str]
    total_cost_state: Literal["unknown"]
    queried_snapshot_id: str
    queried_revision: int
    queried_native_revision: int
    post_snapshot_id: str


def _positive_int(value: object, *, maximum: int = _MAX_U64) -> bool:
    return type(value) is int and 0 < value <= maximum


def _signed_i64(value: object) -> bool:
    return type(value) is int and _MIN_I64 <= value <= _MAX_I64


def serialize_activity_stage5_gold_request_v1(
    request_id: str, *, expected_native_revision: int,
    expected_date_raw: int, expected_actor_character_id: int,
) -> dict[str, object]:
    """Build the exact private native request; stage and type are fixed."""
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("request_id must be nonempty")
    if not _positive_int(expected_native_revision):
        raise ValueError("expected_native_revision must be positive")
    if (type(expected_date_raw) is not int or
            not 0 <= expected_date_raw <= _MAX_U64):
        raise ValueError("expected_date_raw must be nonnegative")
    if not _positive_int(expected_actor_character_id, maximum=2**32 - 1):
        raise ValueError("expected_actor_character_id must be positive")
    return {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": expected_native_revision,
        "expected_date_raw": expected_date_raw,
        "expected_actor_character_id": expected_actor_character_id,
        "expected_activity_key": "activity_feast",
        "expected_planning_stage": 5,
    }


def _gold_value(value: object, *, source: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"resource", "raw", "scale", "source"}
        and value["resource"] == "gold"
        and _signed_i64(value["raw"])
        and type(value["scale"]) is int and value["scale"] == 100000
        and value["source"] == source
    )


def parse_activity_stage5_gold_payload_v1(
    value: object, *, expected_native_revision: int,
    expected_date_raw: int, expected_actor_character_id: int,
) -> ActivityStage5GoldPayloadV1:
    """Copy the exact #606 native payload without pricing or policy inference."""
    if not isinstance(value, dict) or set(value) != {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "activity_key", "planning_stage", "normal_refresh_sequence",
        "configured_cost", "resource_value", "final_can_start",
        "raw_slot12_resource_mapping", "read_only",
        "raw_pointer_fields_persisted",
    }:
        raise BridgeUnavailableError("private stage-5 Gold payload malformed")
    if (
        value["schema"] != SCHEMA
        or type(value["snapshot_revision"]) is not int
        or value["snapshot_revision"] != expected_native_revision
        or type(value["date_raw"]) is not int
        or value["date_raw"] != expected_date_raw
        or type(value["actor_character_id"]) is not int
        or value["actor_character_id"] != expected_actor_character_id
        or value["activity_key"] != "activity_feast"
        or type(value["planning_stage"]) is not int
        or value["planning_stage"] != 5
        or not _positive_int(value["normal_refresh_sequence"])
        or not _gold_value(value["configured_cost"],
                           source="CostBreakdown.GetCost")
        or not _gold_value(value["resource_value"],
                           source="CCharacter.GetGold")
        or value["final_can_start"] is not None
        or value["raw_slot12_resource_mapping"] is not None
        or value["read_only"] is not True
        or value["raw_pointer_fields_persisted"] is not False
    ):
        raise BridgeUnavailableError("private stage-5 Gold payload malformed")
    copied = dict(value)
    copied["configured_cost"] = dict(value["configured_cost"])
    copied["resource_value"] = dict(value["resource_value"])
    return cast(ActivityStage5GoldPayloadV1, copied)


def query_activity_stage5_gold_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> ActivityStage5GoldReadV1:
    """Query one native Gold sample and retain its paused source binding."""
    if getattr(driver, "allow_private_activity_stage5_gold_query", False) is not True:
        raise UnsupportedStepError("private activity stage-5 Gold query is disabled")
    if not _positive_int(expected_revision):
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    provenance = private_native_provenance(before)
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    snapshot_id = before.get("snapshot_id")
    if (
        type(before.get("revision")) is not int
        or before["revision"] != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(actor, Mapping)
        or actor.get("alive") is not True
        or not _positive_int(actor.get("character_id"), maximum=2**32 - 1)
        or not _positive_int(native_revision)
        or type(date_raw) is not int or date_raw < 0
        or not isinstance(snapshot_id, str) or not snapshot_id
    ):
        raise BridgeUnavailableError(
            "private stage-5 Gold read requires a living paused actor")
    actor_id = cast(int, actor["character_id"])
    native_revision = cast(int, native_revision)
    date_raw = cast(int, date_raw)
    request_id = "activity-stage5-gold-read-" + uuid.uuid4().hex
    driver.endpoint.send(serialize_activity_stage5_gold_request_v1(
        request_id, expected_native_revision=native_revision,
        expected_date_raw=date_raw, expected_actor_character_id=actor_id,
    ))
    frame = driver.state.wait_for_command_result(request_id,
                                                 float(timeout_seconds))
    if (
        not isinstance(frame, dict)
        or frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
    ):
        raise BridgeUnavailableError("private stage-5 Gold command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private stage-5 Gold native RED: " + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage5_gold_cost", "backend_id",
        }
        or envelope["step"] != STEP
        or envelope["accepted"] is not True
        or envelope["status"] != "available"
        or envelope["private_build"] is not True
        or envelope["read_only"] is not True
        or envelope["advertised"] is not False
        or envelope["backend_id"] != "native-headless"
    ):
        raise BridgeUnavailableError("private stage-5 Gold envelope malformed")
    payload = parse_activity_stage5_gold_payload_v1(
        envelope["activity_stage5_gold_cost"],
        expected_native_revision=native_revision,
        expected_date_raw=date_raw,
        expected_actor_character_id=actor_id,
    )
    after = driver.take_snapshot()
    if (
        after.get("snapshot_id") != snapshot_id
        or after.get("revision") != expected_revision
        or after.get("native_revision") != native_revision
        or after.get("paused") is not True
        or after.get("map_ready") is not True
        or after.get("date_raw") != date_raw
        or after.get("played_character") != actor
    ):
        raise BridgeUnavailableError(
            "private stage-5 Gold read crossed the paused actor/date frame")
    return cast(ActivityStage5GoldReadV1, {
        **payload,
        **provenance,
        "total_cost_state": "unknown",
        "queried_snapshot_id": snapshot_id,
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after["snapshot_id"],
    })
