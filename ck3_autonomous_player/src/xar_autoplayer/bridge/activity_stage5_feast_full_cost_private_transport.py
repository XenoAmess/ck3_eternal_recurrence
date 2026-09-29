"""Default-off typed read of one paused feast's four named stage-5 costs.

This transport preserves the native final CanStart result and actor Gold. It
does not infer affordability for treasury, piety, or barter goods, and it does
not submit Start.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import TypedDict, cast

from .driver import BridgeUnavailableError, UnsupportedStepError


STEP = "query-activity-stage5-feast-full-cost-v1-private"
SCHEMA = "activity-stage5-feast-full-cost-private-read-v1"
RESOURCE_KEYS = ("gold", "treasury", "piety", "barter_goods")
_MAX_I64 = 2**63 - 1
_MIN_I64 = -(2**63)
_MAX_U64 = 2**64 - 1


class NamedCostV1(TypedDict):
    resource_index: int
    configured_cost_raw: int


class FeastCostsV1(TypedDict):
    gold: NamedCostV1
    treasury: NamedCostV1
    piety: NamedCostV1
    barter_goods: NamedCostV1


class ActivityStage5FeastFullCostPayloadV1(TypedDict):
    schema: str
    snapshot_revision: int
    date_raw: int
    actor_character_id: int
    activity_key: str
    planning_stage: int
    normal_refresh_sequence: int
    scale: int
    actor_gold_raw: int
    resources: FeastCostsV1
    final_can_start: bool
    read_only: bool
    raw_pointer_fields_persisted: bool


class ActivityStage5FeastFullCostReadV1(ActivityStage5FeastFullCostPayloadV1):
    queried_snapshot_id: str
    queried_revision: int
    queried_native_revision: int
    post_snapshot_id: str


def _positive_int(value: object, *, maximum: int = _MAX_U64) -> bool:
    return type(value) is int and 0 < value <= maximum


def _signed_i64(value: object) -> bool:
    return type(value) is int and _MIN_I64 <= value <= _MAX_I64


def serialize_activity_stage5_feast_full_cost_request_v1(
    request_id: str, *, expected_native_revision: int,
    expected_date_raw: int, expected_actor_character_id: int,
) -> dict[str, object]:
    """Bind the private query to one paused actor/date/revision and stage."""
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("request_id must be nonempty")
    if not _positive_int(expected_native_revision):
        raise ValueError("expected_native_revision must be positive")
    if type(expected_date_raw) is not int or not 0 <= expected_date_raw <= _MAX_U64:
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


def parse_activity_stage5_feast_full_cost_payload_v1(
    value: object, *, expected_native_revision: int,
    expected_date_raw: int, expected_actor_character_id: int,
) -> ActivityStage5FeastFullCostPayloadV1:
    """Validate and copy native observations without assigning utility."""
    fields = {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "activity_key", "planning_stage", "normal_refresh_sequence",
        "scale", "actor_gold_raw", "resources", "final_can_start",
        "read_only", "raw_pointer_fields_persisted",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise BridgeUnavailableError("private feast full-cost payload malformed")
    resources = value["resources"]
    if not isinstance(resources, dict) or set(resources) != set(RESOURCE_KEYS):
        raise BridgeUnavailableError("private feast full-cost resources malformed")
    copied_resources: dict[str, NamedCostV1] = {}
    for key in RESOURCE_KEYS:
        item = resources[key]
        if (
            not isinstance(item, dict)
            or set(item) != {"resource_index", "configured_cost_raw"}
            or type(item["resource_index"]) is not int
            or not 0 <= item["resource_index"] < 10
            or not _signed_i64(item["configured_cost_raw"])
        ):
            raise BridgeUnavailableError("private feast full-cost resource malformed")
        copied_resources[key] = cast(NamedCostV1, dict(item))
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
        or type(value["scale"]) is not int
        or value["scale"] != 100000
        or not _signed_i64(value["actor_gold_raw"])
        or type(value["final_can_start"]) is not bool
        or value["read_only"] is not True
        or value["raw_pointer_fields_persisted"] is not False
    ):
        raise BridgeUnavailableError("private feast full-cost payload malformed")
    return cast(ActivityStage5FeastFullCostPayloadV1, {
        **value, "resources": copied_resources,
    })


def query_activity_stage5_feast_full_cost_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> ActivityStage5FeastFullCostReadV1:
    """Read one stage-5 native frame; a changed frame remains RED."""
    if getattr(driver, "allow_private_activity_stage5_feast_full_cost_query", False) is not True:
        raise UnsupportedStepError("private feast full-cost query is disabled")
    if not _positive_int(expected_revision):
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
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
        or type(date_raw) is not int or not 0 <= date_raw <= _MAX_U64
        or not isinstance(snapshot_id, str) or not snapshot_id
    ):
        raise BridgeUnavailableError("private feast full-cost read requires a living paused actor")
    actor_id = cast(int, actor["character_id"])
    native_revision = cast(int, native_revision)
    date_raw = cast(int, date_raw)
    request_id = "activity-stage5-feast-full-cost-read-" + uuid.uuid4().hex
    driver.endpoint.send(serialize_activity_stage5_feast_full_cost_request_v1(
        request_id, expected_native_revision=native_revision,
        expected_date_raw=date_raw, expected_actor_character_id=actor_id,
    ))
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (
        not isinstance(frame, dict)
        or frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
    ):
        raise BridgeUnavailableError("private feast full-cost command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private feast full-cost native RED: " + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage5_feast_full_cost", "backend_id",
        }
        or envelope["step"] != STEP
        or envelope["accepted"] is not True
        or envelope["status"] != "available"
        or envelope["private_build"] is not True
        or envelope["read_only"] is not True
        or envelope["advertised"] is not False
        or envelope["backend_id"] != "native-headless"
    ):
        raise BridgeUnavailableError("private feast full-cost envelope malformed")
    payload = parse_activity_stage5_feast_full_cost_payload_v1(
        envelope["activity_stage5_feast_full_cost"],
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
        raise BridgeUnavailableError("private feast full-cost read crossed the paused actor/date frame")
    return cast(ActivityStage5FeastFullCostReadV1, {
        **payload,
        "queried_snapshot_id": snapshot_id,
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after["snapshot_id"],
    })
