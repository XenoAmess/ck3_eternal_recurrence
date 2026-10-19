"""Explicit default-OFF pilgrimage planner transport; ACK never proves payment/completion."""
from __future__ import annotations

from copy import deepcopy
import math
from collections.abc import Mapping
import uuid

from .activity_feast_stage5_start_private_transport import _source_snapshot, _same_frame
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_pilgrimage_activities_private_transport import normalize_player_pilgrimage_activities_v1
from .version_identity import CK3_12004

PERMISSION = "allow_private_player_pilgrimage_execution"
QUERY_STEP = "query-player-pilgrimage-planner-v1-private"
SUBMIT_STEP = "submit-player-pilgrimage-planner-v1-private"
SCHEMA = "ck3_12004_player_pilgrimage_planner_v1"
QUERY_OPERATIONS = frozenset({"read", "can_select", "quote", "post"})
SUBMIT_OPERATIONS = frozenset({"open", "confirm", "select", "start"})
STATUSES = frozenset({
    "observed", "rejected", "submitted_pending", "submission_outcome_unknown",
    "needs_recovery", "unavailable", "identity_observed", "post_pending", "ambiguous",
})
LEDGER_STATES = frozenset({"idle", "submitted_pending", "submission_outcome_unknown", "identity_observed"})
RESOURCES = ("gold", "treasury", "piety", "barter_goods")


def _require(value, message):
    if not value:
        raise BridgeUnavailableError("pilgrimage planner " + message)


def _integer(value, low=0, high=2**64-1):
    return type(value) is int and low <= value <= high


def _scope(source):
    diagnostic = source.get("diagnostics")
    hello = diagnostic.get("hello") if isinstance(diagnostic, Mapping) else None
    _require(_integer(source["played_character"]["character_id"], 1, 2**32-2)
             and isinstance(hello, Mapping) and hello.get("ck3_build_match") is True
             and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"
             and _integer(hello.get("pid"), 1)
             and _integer(diagnostic.get("connection_generation"), 1),
             "requires a qualified actual native process/generation")
    return (hello["pid"], diagnostic["connection_generation"], source.get("episode_run_id"))


def _arguments(driver, *, operation, expected_revision, province_id, read_stage,
               policy_positive, reserves, timeout_seconds, submit):
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private pilgrimage execution is disabled")
    if not _integer(expected_revision, 1):
        raise ValueError("expected_revision must be a positive actual public revision")
    if operation not in (SUBMIT_OPERATIONS if submit else QUERY_OPERATIONS):
        raise ValueError("unlisted pilgrimage planner operation")
    if not _integer(province_id, 0, 2**32-2):
        raise ValueError("province_id must be a complete uint32 identity or zero")
    if operation in {"can_select", "select", "start"}:
        if province_id == 0:
            raise ValueError("this operation requires a nonzero actual province_id")
    elif province_id != 0:
        raise ValueError("this operation does not accept province_id")
    if not _integer(read_stage, 0, 5) or (operation != "read" and read_stage != 0):
        raise ValueError("read_stage is a read-only 0..5 filter")
    if type(policy_positive) is not bool or (submit and policy_positive is not True):
        raise ValueError("each submit requires explicit policy_positive=true")
    if (type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
        raise ValueError("timeout_seconds must be finite and positive")
    if any(not _integer(v, 0, 2**63-1) for v in reserves.values()):
        raise ValueError("resource reserves must be explicit nonnegative signed64 integers")
    if operation != "start" and any(reserves.values()):
        raise ValueError("reserves only apply to Start")
    before = _source_snapshot(driver)
    _require(before["revision"] == expected_revision, "public revision changed")
    _require(private_native_build_identity(before) == CK3_12004, "requires exact CK3 1.20.0.4")
    _scope(before)
    return before


def normalize_pilgrimage_quote_v1(value, *, source):
    keys = {
        "schema", "activity_key", "special_option_key", "observed", "read_only",
        "raw_pointer_fields_persisted", "snapshot_revision", "date_raw", "actor_character_id",
        "application_main_thread", "paused", "map_ready", "actor_alive", "planning_stage",
        "scale", "normal_refresh_sequence", "configuration_fingerprint", "selected_option",
        "known_cost_names", "known_name_resource_indices", "configured_cost_raw",
        "diagnostic_aggregate_raw", "named_cost_verified", "unknown_positive_configured_cost",
        "final_can_start_observed", "final_can_start", "failure_display_known",
        "failure_display", "failure_display_unknown_reason",
    }
    _require(isinstance(value, dict) and set(value) == keys, "quote shape differs from native serializer")
    _require(value["schema"] == "activity-pilgrimage-configured-full10-cost-v1"
             and value["activity_key"] == "activity_pilgrimage"
             and value["special_option_key"] == "pilgrimage_type_pious", "quote is another activity/option")
    for key in ("observed", "read_only", "application_main_thread", "paused",
                "map_ready", "actor_alive", "final_can_start_observed"):
        _require(value[key] is True, "quote lacks " + key)
    _require(value["raw_pointer_fields_persisted"] is False
             and value["failure_display_known"] is False and value["failure_display"] is None
             and value["failure_display_unknown_reason"] == "final_canstart_tooltip_getter_unbound",
             "quote invents pointer/failure-display evidence")
    for key, expected in (("snapshot_revision", source["native_revision"]), ("date_raw", source["date_raw"]),
                          ("actor_character_id", source["played_character"]["character_id"])):
        _require(type(value[key]) is int and value[key] == expected, "quote changed " + key)
    _require(type(value["planning_stage"]) is int and value["planning_stage"] == 5
             and type(value["scale"]) is int and value["scale"] == 100000
             and _integer(value["normal_refresh_sequence"], 1)
             and _integer(value["configuration_fingerprint"])
             and type(value["final_can_start"]) is bool, "quote stage/refresh/scalars malformed")
    selection = value["selected_option"]
    _require(isinstance(selection, dict) and set(selection) == {"native_option_id", "key"}
             and _integer(selection["native_option_id"], 0, 2**32-2)
             and selection["key"] == "pilgrimage_type_pious", "quote selected option malformed")
    _require(value["known_cost_names"] == list(RESOURCES), "quote cost names changed")
    indices = value["known_name_resource_indices"]
    _require(isinstance(indices, list) and len(indices) == 4
             and all(_integer(i, 0, 9) for i in indices) and len(set(indices)) == 4,
             "quote named resource indices malformed")
    for key in ("configured_cost_raw", "diagnostic_aggregate_raw"):
        vector = value[key]
        _require(isinstance(vector, list) and len(vector) == 10
                 and all(_integer(n, -(2**63), 2**63-1) for n in vector), "quote full10 vector malformed")
    mask = value["named_cost_verified"]
    _require(isinstance(mask, list) and len(mask) == 10 and all(type(v) is bool for v in mask)
             and mask == [i in indices for i in range(10)], "quote named mask disagrees with dynamic indices")
    unknown = any(not mask[i] and value["configured_cost_raw"][i] > 0 for i in range(10))
    _require(type(value["unknown_positive_configured_cost"]) is bool
             and value["unknown_positive_configured_cost"] is unknown, "quote unknown-positive flag disagrees")
    return deepcopy(value)


def normalize_player_pilgrimage_planner_v1(value, *, source, operation, submit):
    keys = {
        "schema", "read_only", "snapshot_revision", "date_raw", "played_character_id",
        "activity_type_key", "special_option_key", "operation", "operation_status",
        "invoked", "needs_recovery", "ledger_state", "failure", "planner", "quote",
        "new_identity", "absence_is_completion", "raw_pointer_fields_persisted",
    }
    _require(isinstance(value, dict) and set(value) == keys and value["schema"] == SCHEMA,
             "typed body malformed")
    _require(value["read_only"] is (not submit) and value["operation"] == operation
             and isinstance(value["operation_status"], str) and value["operation_status"] in STATUSES
             and isinstance(value["ledger_state"], str) and value["ledger_state"] in LEDGER_STATES
             and value["activity_type_key"] == "activity_pilgrimage"
             and value["special_option_key"] == "pilgrimage_type_pious"
             and value["absence_is_completion"] is False and value["raw_pointer_fields_persisted"] is False,
             "body operation/scope/status malformed")
    for key, expected in (("snapshot_revision", source["native_revision"]), ("date_raw", source["date_raw"]),
                          ("played_character_id", source["played_character"]["character_id"])):
        _require(type(value[key]) is int and value[key] == expected, "body changed " + key)
    _require(type(value["invoked"]) is bool and type(value["needs_recovery"]) is bool,
             "body invocation/recovery availability malformed")
    _require(submit or value["invoked"] is False, "read-only operation reports a world invocation")
    _require(isinstance(value["failure"], str) and len(value["failure"]) <= 4096,
             "body failure diagnostic malformed")
    planner = value["planner"]
    if planner is not None:
        _require(isinstance(planner, dict) and set(planner) == {
            "stage", "selected_pious", "destination_province_id", "can_select", "can_progress"},
            "planner semantic shape malformed")
        _require(_integer(planner["stage"], 0, 5), "planner stage malformed")
        for key in ("selected_pious", "can_select", "can_progress"):
            _require(planner[key] is None or type(planner[key]) is bool, "planner nullable boolean malformed")
        _require(planner["destination_province_id"] is None
                 or _integer(planner["destination_province_id"], 0, 2**32-2), "planner destination malformed")
    if value["quote"] is not None:
        normalize_pilgrimage_quote_v1(value["quote"], source=source)
    if value["new_identity"] is not None:
        synthetic_container = {
            "schema": "ck3_12004_player_pilgrimage_activities_v1", "read_only": True,
            "snapshot_revision": source["native_revision"], "date_raw": source["date_raw"],
            "played_character_id": source["played_character"]["character_id"],
            "scope": "currently-hosted-by-current-player", "activity_type_key": "activity_pilgrimage",
            "activity_count": 1, "activities": [value["new_identity"]],
            "absence_is_completion": False, "raw_pointer_fields_persisted": False,
        }
        normalize_player_pilgrimage_activities_v1(synthetic_container, source=source)
    return deepcopy(value)


def _request(driver, *, operation, expected_revision, province_id, read_stage,
             policy_positive, reserves, timeout_seconds, submit):
    before = _arguments(driver, operation=operation, expected_revision=expected_revision,
                        province_id=province_id, read_stage=read_stage, policy_positive=policy_positive,
                        reserves=reserves, timeout_seconds=timeout_seconds, submit=submit)
    step = SUBMIT_STEP if submit else QUERY_STEP
    request_id = "player-pilgrimage-planner-" + uuid.uuid4().hex
    payload = {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id, "step": step,
        "operation": operation, "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": before["played_character"]["character_id"],
        "expected_activity_key": "activity_pilgrimage", "expected_option_key": "pilgrimage_type_pious",
        "province_id": province_id, "read_stage": read_stage,
    }
    if submit:
        payload["policy_positive"] = policy_positive
        payload.update({"reserve_" + name + "_raw": reserves[name] for name in RESOURCES})
    # The native process-persistent ledger owns exactly-once Start. This
    # transport sends once, never retries, and exposes no reset/resend tool.
    driver.endpoint.send(payload)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    _require(isinstance(frame, dict) and frame.get("type") == "command_result"
             and frame.get("protocol_version") == 1 and frame.get("request_id") == request_id,
             "response missing/corrupted; outcome may be unknown, never resend submit")
    _require(frame.get("ok") is True, "native RED; inspect retained request/native ledger before any further action")
    envelope = frame.get("result")
    _require(isinstance(envelope, dict) and set(envelope) == {
        "step", "accepted", "status", "private_build", "read_only", "advertised",
        "player_pilgrimage_planner", "backend_id"}
        and envelope["step"] == step and envelope["accepted"] is True
        and envelope["status"] == "available" and envelope["private_build"] is True
        and envelope["read_only"] is (not submit) and envelope["advertised"] is False
        and envelope["backend_id"] == "native-headless", "typed envelope malformed")
    value = normalize_player_pilgrimage_planner_v1(
        envelope["player_pilgrimage_planner"], source=before, operation=operation, submit=submit)
    after = _source_snapshot(driver)
    _require(private_native_build_identity(after) == CK3_12004 and _scope(after) == _scope(before),
             "native process/build/generation changed")
    if submit and operation == "start" and value["invoked"]:
        _require(after["played_character"]["character_id"] == before["played_character"]["character_id"]
                 and after["date_raw"] == before["date_raw"], "Start post-frame actor/date changed")
    else:
        _require(_same_frame(before, after), "query/UI operation crossed paused frame")
    return {**value, **private_native_provenance(before), "request_id": request_id,
            "queried_snapshot_id": before["snapshot_id"], "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"], "post_snapshot_id": after["snapshot_id"],
            "automatic_retry": False, "business_outcome_observed": False, "action_ready": False}


def query_player_pilgrimage_planner_private_v1(
    driver, *, expected_revision, operation="read", province_id=0, read_stage=0, timeout_seconds=30.0,
):
    return _request(driver, expected_revision=expected_revision, operation=operation,
                    province_id=province_id, read_stage=read_stage, policy_positive=False,
                    reserves=dict.fromkeys(RESOURCES, 0), timeout_seconds=timeout_seconds, submit=False)


def submit_player_pilgrimage_planner_private_v1(
    driver, *, expected_revision, operation, province_id=0, policy_positive=False,
    reserve_gold_raw=0, reserve_treasury_raw=0, reserve_piety_raw=0,
    reserve_barter_goods_raw=0, timeout_seconds=30.0,
):
    return _request(driver, expected_revision=expected_revision, operation=operation,
                    province_id=province_id, read_stage=0, policy_positive=policy_positive,
                    reserves=dict(zip(RESOURCES, (reserve_gold_raw, reserve_treasury_raw,
                                                  reserve_piety_raw, reserve_barter_goods_raw))),
                    timeout_seconds=timeout_seconds, submit=True)
