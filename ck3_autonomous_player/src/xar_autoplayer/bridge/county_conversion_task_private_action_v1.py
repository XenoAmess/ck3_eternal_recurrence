"""Typed player county-task queue submission and independent task readback.

The native owner evaluates final dispatch eligibility and submits the fixed
task_conversion command. Only a later actual task state verifies assignment;
neither a queued ACK nor that assignment means the county has converted.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, CK3_12004


SUBMIT_STEP = "county-conversion-task-submit-private-v1"
RESULT_STEP = "county-conversion-task-result-private-v1"
PERMISSION = "allow_private_player_clergy_appointment_query"
ACTION_SCHEMA = "xar.ck3.county-conversion-task-private-action.v1"
RESULT_SCHEMA = "xar.ck3.county-conversion-task-independent-result.v1"
SUBMIT_STATUSES = {"not_submitted", "already_active_noop", "queued_verification_pending"}


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _full_id(value: object) -> bool:
    return _integer(value, -(1 << 31), (1 << 31) - 1) and value != -1


def _identity(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value.encode("utf-8")) <= 63


def _frame(driver: object, expected_revision: int) -> dict[str, object]:
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private county conversion task action is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must identify the current public snapshot")
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (snapshot.get("revision") != expected_revision
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not _full_id(actor.get("character_id"))
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] <= 0
            or type(snapshot.get("date_raw")) is not int
            or private_native_build_identity(snapshot) not in (CK3_12003, CK3_12004)):
        raise BridgeUnavailableError("county task requires its current paused Crozier player")
    return snapshot


def _send(driver: object, before: Mapping[str, object], *, step: str,
          fields: Mapping[str, object], timeout_seconds: float) -> tuple[str, dict[str, object]]:
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "county-task-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": before["native_revision"],
        "expected_snapshot_revision": before["native_revision"],
        "expected_public_revision": before["revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": before["played_character"]["character_id"],
        **fields,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("county task command_result unresolved; do not automatically resubmit")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("county task native RED: " + str(frame.get("error", "unknown")))
    result = frame.get("result")
    build = private_native_build_identity(before)
    if (not isinstance(result, dict) or result.get("step") != step
            or result.get("accepted") is not True or result.get("private_build") is not True
            or result.get("advertised") is not False or result.get("backend_id") != "native-headless"
            or result.get("game_version") != build.game_version
            or result.get("executable_sha256") != build.executable_sha256
            or result.get("read_only") is not (step == RESULT_STEP)
            or result.get("snapshot_revision") != before["native_revision"]
            or result.get("public_revision") != before["revision"]
            or result.get("date_raw") != before["date_raw"]
            or not _integer(result.get("capture_epoch"), 1, (1 << 64) - 1)):
        raise BridgeUnavailableError("county task native envelope differs from its queried build/frame")
    after = driver.take_snapshot()
    after_actor = after.get("played_character")
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or not isinstance(after_actor, Mapping) or after_actor.get("alive") is not True
            or after_actor.get("character_id") != before["played_character"]["character_id"]
            or private_native_build_identity(after) != build):
        raise BridgeUnavailableError("county task transport crossed its current actor/date frame")
    return request_id, result


def _task(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or type(value.get("available")) is not bool
            or not isinstance(value.get("failure"), str)
            or not _integer(value.get("capture_epoch"), 0, (1 << 64) - 1)
            or not _integer(value.get("date_raw"), -(1 << 31), (1 << 31) - 1)
            or not _integer(value.get("owner_character_id"), -(1 << 31), (1 << 31) - 1)
            or not isinstance(value.get("task_key"), str)):
        raise BridgeUnavailableError("county task actual state is malformed")
    for key in ("incumbent_character_id", "active_task_id", "target_province_id",
                "target_county_title_id", "progress_kind"):
        if value.get(key) is not None and not _integer(value[key], -(1 << 31), (1 << 31) - 1):
            raise BridgeUnavailableError("county task actual integer is malformed: " + key)
    if (value.get("target_scope_tag") is not None
            and not _integer(value["target_scope_tag"], 0, 0xFFFF)):
        raise BridgeUnavailableError("county task actual scope tag is malformed")
    if (value.get("percentage_progress_raw") is not None
            and not _integer(value["percentage_progress_raw"], -(1 << 63), (1 << 63) - 1)):
        raise BridgeUnavailableError("county task actual progress is malformed")
    if (value["available"] is True
            and (value["capture_epoch"] <= 0 or not _full_id(value["owner_character_id"])
                 or not _full_id(value.get("incumbent_character_id"))
                 or not _full_id(value.get("active_task_id")) or not value["task_key"])):
        raise BridgeUnavailableError("county task available state lacks actual task identity")
    return deepcopy(value)


def _owner(value: object, current: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise BridgeUnavailableError("county task result lacks its retained Submission")
    request = value.get("request")
    if (not isinstance(request, dict) or not _identity(request.get("action_id"))
            or not _identity(value.get("request_id"))
            or not _integer(request.get("expected_active_task_id"), 1, (1 << 31) - 1)
            or not _integer(request.get("expected_incumbent_character_id"), 1, (1 << 31) - 1)
            or not _integer(request.get("province_id"), 1, (1 << 31) - 1)
            or type(request.get("replace_existing_task")) is not bool
            or type(request.get("expected_revision")) is not int or request["expected_revision"] <= 0
            or type(value.get("native_revision")) is not int or value["native_revision"] <= 0
            or type(value.get("date_raw")) is not int
            or not _integer(value.get("capture_epoch"), 1, (1 << 64) - 1)
            or value.get("played_character_id") != current["played_character"]["character_id"]
            or value.get("command_channel") != 0x0E
            or type(value.get("native_submit_copy_called")) is not bool
            or value.get("status") not in SUBMIT_STATUSES
            or not isinstance(value.get("failure"), str)
            or (value.get("native_final_can_dispatch") is not None
                and type(value["native_final_can_dispatch"]) is not bool)):
        raise BridgeUnavailableError("county task retained Submission identity is malformed")
    before = _task(value.get("before"))
    if before["available"] is True:
        if (before["capture_epoch"] != value["capture_epoch"]
                or before["date_raw"] != value["date_raw"]
                or before["owner_character_id"] != value["played_character_id"]):
            raise BridgeUnavailableError("county task before state differs from the submitting player frame")
    if value["status"] == "queued_verification_pending":
        if (not before["available"] or value["native_submit_copy_called"] is not True
                or value["native_final_can_dispatch"] is not True
                or before["active_task_id"] != request["expected_active_task_id"]
                or before["incumbent_character_id"] != request["expected_incumbent_character_id"]
                or not _full_id(value.get("target_county_title_id"))):
            raise BridgeUnavailableError("county task queued record lacks its actual final dispatch source")
    return deepcopy(value)


def _matches(task: Mapping[str, object], owner: Mapping[str, object]) -> bool | None:
    if task["available"] is not True:
        return None
    request = owner["request"]
    return (task["owner_character_id"] == owner["played_character_id"]
            and task["incumbent_character_id"] == request["expected_incumbent_character_id"]
            and _full_id(task["active_task_id"])
            and task["task_key"] == "task_conversion"
            and task["target_scope_tag"] == 8
            and task["target_province_id"] == request["province_id"]
            and task["target_county_title_id"] == owner["target_county_title_id"])


def submit_county_conversion_task_private_v1(
    driver: object, *, expected_revision: int, expected_active_task_id: int,
    expected_incumbent_character_id: int, province_id: int,
    replace_existing_task: bool, action_id: str, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Submit once; preserve final rejection, no-op, and queued ACK separately."""
    if (not _integer(expected_active_task_id, 1, (1 << 31) - 1)
            or not _integer(expected_incumbent_character_id, 1, (1 << 31) - 1)):
        raise ValueError("expected task and incumbent must retain their full native identities")
    if not _integer(province_id, 1, (1 << 31) - 1):
        raise ValueError("province_id must be an observed native Province reference")
    if type(replace_existing_task) is not bool or not _identity(action_id):
        raise ValueError("county task requires explicit replacement acceptance and caller action identity")
    current = _frame(driver, expected_revision)
    fields = {"expected_active_task_id": expected_active_task_id,
              "expected_incumbent_character_id": expected_incumbent_character_id,
              "province_id": province_id, "replace_existing_task": replace_existing_task,
              "action_id": action_id}
    transport_id, envelope = _send(driver, current, step=SUBMIT_STEP, fields=fields,
                                   timeout_seconds=timeout_seconds)
    owner = _owner(envelope.get("submission"), current)
    if (owner["request"] != {"expected_revision": expected_revision, **fields}
            or owner["request_id"] != transport_id
            or owner["native_revision"] != current["native_revision"]
            or owner["date_raw"] != current["date_raw"]
            or owner["capture_epoch"] != envelope["capture_epoch"]):
        raise BridgeUnavailableError("county task Submission differs from its actual submitted frame")
    queued = owner["status"] == "queued_verification_pending"
    if owner["status"] == "already_active_noop" and _matches(owner["before"], owner) is not True:
        raise BridgeUnavailableError("county task no-op lacks a preexisting matching assignment")
    return {
        "schema": ACTION_SCHEMA, **private_native_provenance(current),
        "status": owner["status"], "failure": owner["failure"],
        "request_id": transport_id, "action_id": action_id,
        "player_character_id": owner["played_character_id"],
        "province_id": province_id, "target_county_title_id": owner["target_county_title_id"],
        "submitted": queued, "verification_pending": queued, "material_result": False,
        "task_assignment_material_observed": False, "county_conversion_completed": False,
        "before_task": _task(owner["before"]), "owner_submission": owner,
        "automatic_retry": False, "advertised": False,
    }


def query_county_conversion_task_result_private_v1(
    driver: object, *, expected_revision: int, submitted_request_id: str, action_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Verify a later real assignment, allowing the existing task FullID to survive."""
    if not _identity(submitted_request_id) or not _identity(action_id):
        raise ValueError("county task result requires its submitted request/action identities")
    current = _frame(driver, expected_revision)
    _, envelope = _send(driver, current, step=RESULT_STEP, fields={
        "submitted_request_id": submitted_request_id, "action_id": action_id,
    }, timeout_seconds=timeout_seconds)
    owner = _owner(envelope.get("submission"), current)
    native = envelope.get("independent_result")
    if (owner["request_id"] != submitted_request_id or owner["request"]["action_id"] != action_id
            or not isinstance(native, dict) or native.get("request_id") != submitted_request_id
            or native.get("action_id") != action_id or native.get("submit_status") != owner["status"]
            or native.get("county_conversion_completed") is not False):
        raise BridgeUnavailableError("county task independent result lost its retained request")
    after = _task(native.get("after"))
    if after["available"] is True:
        if (after["capture_epoch"] != envelope["capture_epoch"]
                or after["date_raw"] != current["date_raw"]):
            raise BridgeUnavailableError("county task after state differs from the current owner pump")
    queued = owner["status"] == "queued_verification_pending"
    same_owner = after["available"] and after["owner_character_id"] == owner["played_character_id"]
    matches = _matches(after, owner) if same_owner else None
    unchanged = (after["active_task_id"] == owner["before"]["active_task_id"]
                 if same_owner and after["active_task_id"] is not None
                 and owner["before"]["active_task_id"] is not None else None)
    material = queued and after["capture_epoch"] > owner["capture_epoch"] and matches is True
    pending = queued and not material
    if (native.get("actual_task_assignment_matches") is not matches
            or native.get("actual_task_id_unchanged") is not unchanged
            or native.get("task_assignment_material_observed") is not material
            or native.get("verification_pending") is not pending):
        raise BridgeUnavailableError("county task result differs from its independent assignment facts")
    return {
        "schema": RESULT_SCHEMA, **private_native_provenance(current),
        "status": "task_assignment_material_observed" if material else owner["status"],
        "request_id": submitted_request_id, "action_id": action_id,
        "player_character_id": owner["played_character_id"],
        "province_id": owner["request"]["province_id"],
        "target_county_title_id": owner["target_county_title_id"],
        "material_result": material, "verification_pending": pending,
        "actual_task_id_unchanged": unchanged, "actual_task_assignment_matches": matches,
        "task_assignment_material_observed": material, "county_conversion_completed": False,
        "before_task": _task(owner["before"]), "after_task": after,
        "owner_submission": owner, "owner_result": deepcopy(native),
        "automatic_retry": False, "advertised": False,
    }
