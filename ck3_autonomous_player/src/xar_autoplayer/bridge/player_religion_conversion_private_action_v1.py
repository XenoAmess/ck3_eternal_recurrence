"""Typed ordinary paid conversion and independent retained-request material.

Use the existing religion conversion terms authorization and native mailbox.
The native owner recaptures paid terms/reasons and actual before state in one
pump. A later result reads actual after state; ACK never means conversion.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_religion_conversion_outcome_private_transport import (
    normalize_player_religion_conversion_outcome_v1,
)
from .player_religion_conversion_terms_private_transport import (
    normalize_player_religion_conversion_terms_v1,
)
from .version_identity import CK3_12003


SUBMIT_STEP = "submit-player-religion-conversion-private-v1"
RESULT_STEP = "query-player-religion-conversion-result-private-v1"
PERMISSION = "allow_private_player_religion_conversion_terms_query"
ACTION_SCHEMA = "xar.ck3.player-religion-conversion-private-action.v1"
RESULT_SCHEMA = "xar.ck3.player-religion-conversion-independent-result.v1"
RESOURCES = ("piety_raw", "gold_raw", "prestige_raw")
SUBMIT_STATUSES = {"not_submitted", "already_target_noop", "queued_verification_pending"}


def _integer(value: object, lower: int, upper: int) -> bool:
    return type(value) is int and lower <= value <= upper


def _action_id(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value.encode("utf-8")) <= 63


def _frame(driver: object, expected_revision: int) -> dict[str, object]:
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private religion conversion is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must identify the current public snapshot")
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (snapshot.get("revision") != expected_revision
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not _integer(actor.get("character_id"), 1, 0xFFFFFFFF - 1)
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] <= 0
            or type(snapshot.get("date_raw")) is not int
            or private_native_build_identity(snapshot) != CK3_12003):
        raise BridgeUnavailableError("conversion requires its current paused Crozier player")
    return snapshot


def _send(driver: object, before: Mapping[str, object], *, step: str,
          fields: Mapping[str, object], timeout_seconds: float) -> tuple[str, dict[str, object]]:
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "religion-convert-" + uuid.uuid4().hex
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
        raise BridgeUnavailableError("conversion command_result unresolved; do not automatically resubmit")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("conversion native RED: " + str(frame.get("error", "unknown")))
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
            or not _integer(result.get("capture_epoch"), 1, 0xFFFFFFFFFFFFFFFF)):
        raise BridgeUnavailableError("conversion native envelope differs from its queried build/frame")
    after = driver.take_snapshot()
    after_actor = after.get("played_character")
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or not isinstance(after_actor, Mapping) or after_actor.get("alive") is not True
            or after_actor.get("character_id") != before["played_character"]["character_id"]
            or private_native_build_identity(after) != build):
        raise BridgeUnavailableError("conversion transport crossed its current actor/date frame")
    return request_id, result


def _context(outcome: Mapping[str, object]) -> Mapping[str, object] | None:
    actor = outcome.get("actor")
    context = actor.get("current_religion") if isinstance(actor, Mapping) else None
    # Actual actor identity/resources suffice; ancillary state/flags may fail.
    if (not isinstance(actor, Mapping) or actor.get("available") is not True
            or not isinstance(context, Mapping) or context.get("available") is not True):
        return None
    return context


def _retained_frame(owner: Mapping[str, object], current: Mapping[str, object]) -> dict[str, object]:
    # Before belongs to the retained owning pump, which may precede the current
    # date/native/public revision. Current build/player still bind this record.
    frame = deepcopy(dict(current))
    frame["date_raw"] = owner["date_raw"]
    frame["native_revision"] = owner["native_revision"]
    frame["revision"] = owner["request"]["expected_revision"]
    return frame


def _owner_identity(owner: object, current: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(owner, dict):
        raise BridgeUnavailableError("conversion native result lacks its owning Submission")
    request = owner.get("request")
    if (not isinstance(request, dict) or not _action_id(request.get("action_id"))
            or not _action_id(owner.get("request_id"))
            or not _integer(request.get("target_rite_id"), 0, 0xFFFFFFFF - 1)
            or not _integer(request.get("max_piety_cost_raw"), 0, (1 << 63) - 1)
            or type(request.get("expected_revision")) is not int or request["expected_revision"] <= 0
            or type(owner.get("native_revision")) is not int or owner["native_revision"] <= 0
            or type(owner.get("date_raw")) is not int
            or not _integer(owner.get("capture_epoch"), 1, 0xFFFFFFFFFFFFFFFF)
            or owner.get("played_character_id") != current["played_character"]["character_id"]
            or owner.get("command_target_rite_id") != request["target_rite_id"]
            or owner.get("command_pay_piety") is not True or owner.get("command_channel") != 0x0E
            or type(owner.get("native_submit_copy_called")) is not bool
            or owner.get("status") not in SUBMIT_STATUSES):
        raise BridgeUnavailableError("conversion retained Submission identity is malformed")
    return owner


def _normalize_baseline(owner: Mapping[str, object], current: Mapping[str, object]) -> dict[str, object]:
    before = normalize_player_religion_conversion_outcome_v1(
        owner.get("before"), snapshot=_retained_frame(owner, current),
        target_rite_id=owner["request"]["target_rite_id"])
    if before["capture_epoch"] != owner["capture_epoch"] or _context(before) is None:
        raise ValueError("conversion Submission lacks its independent before actor")
    return before


def _normalize_paid(owner: Mapping[str, object], current: Mapping[str, object]) -> dict[str, object]:
    paid = normalize_player_religion_conversion_terms_v1(
        owner.get("paid_terms"), snapshot=_retained_frame(owner, current),
        target_rite_id=owner["request"]["target_rite_id"])
    if (owner["native_submit_copy_called"] is not True
            or paid["capture_epoch"] != owner["capture_epoch"] or paid["can_convert"] is not True):
        raise ValueError("conversion queued record lacks its actual paid final source")
    return paid


def submit_player_religion_conversion_private_v1(
    driver: object, *, expected_revision: int, target_rite_id: int,
    max_piety_cost_raw: int, action_id: str, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Submit one caller-selected ordinary paid target through the native owner."""
    if not _integer(target_rite_id, 0, 0xFFFFFFFF - 1):
        raise ValueError("target_rite_id must be a complete Rite reference below the absent sentinel")
    if not _integer(max_piety_cost_raw, 0, (1 << 63) - 1):
        raise ValueError("max_piety_cost_raw must be a nonnegative Q100000 base-fee budget")
    if not _action_id(action_id):
        raise ValueError("action_id must be a new caller identity of at most 63 UTF-8 bytes")
    before = _frame(driver, expected_revision)
    transport_id, envelope = _send(driver, before, step=SUBMIT_STEP, fields={
        "target_rite_id": target_rite_id, "max_piety_cost_raw": max_piety_cost_raw,
        "action_id": action_id,
    }, timeout_seconds=timeout_seconds)
    owner = _owner_identity(envelope.get("submission"), before)
    intent = {"expected_revision": expected_revision, "target_rite_id": target_rite_id,
              "max_piety_cost_raw": max_piety_cost_raw, "action_id": action_id}
    if (owner["request"] != intent or owner["request_id"] != transport_id
            or owner["native_revision"] != before["native_revision"]
            or owner["date_raw"] != before["date_raw"]
            or owner["capture_epoch"] != envelope["capture_epoch"]):
        raise BridgeUnavailableError("conversion Submission differs from its actual submitted frame")
    result = {
        "schema": ACTION_SCHEMA, **private_native_provenance(before),
        "request_id": owner["request_id"], "action_id": action_id,
        "player_character_id": owner["played_character_id"], "target_rite_id": target_rite_id,
        "pay_piety": True, "max_piety_cost_raw": max_piety_cost_raw,
        "material_result": False, "submitted": False, "verification_pending": False,
        "owner_submission": deepcopy(owner), "before_outcome": None,
        "paid_terms": None, "native_reasons": deepcopy(owner.get("native_reasons")),
        "quoted_base_piety_cost_raw": None, "raw_scale": 100000,
        "automatic_retry": False, "advertised": False,
    }
    if owner["status"] == "not_submitted":
        result.update(status="rejected_before_submit", failure=owner.get("failure"))
        return result
    try:
        baseline = _normalize_baseline(owner, before)
        result["before_outcome"] = baseline
        if owner["status"] == "already_target_noop":
            if _context(baseline).get("rite_id") != target_rite_id:
                raise ValueError("conversion native noop lacks a preexisting target match")
            result["status"] = "noop_preexisting_target_match"
            return result
        paid = _normalize_paid(owner, before)
        if _context(baseline).get("rite_id") == target_rite_id:
            raise ValueError("conversion submitted record has a preexisting target match")
        quote = paid["cost"]["piety_cost_raw"]
        if not _integer(quote, -(1 << 63), (1 << 63) - 1) or max(quote, 0) > max_piety_cost_raw:
            raise ValueError("conversion queued quote exceeds caller base-fee authorization")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    result.update(status="submitted_verification_pending", submitted=True,
                  verification_pending=True, paid_terms=paid,
                  quoted_base_piety_cost_raw=quote)
    return result


def query_player_religion_conversion_result_private_v1(
    driver: object, *, expected_revision: int, request_id: str, action_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Read the retained owning baseline and one fresh actual native after state."""
    if not _action_id(request_id) or not _action_id(action_id):
        raise ValueError("conversion result requires its submitted request/action identities")
    current = _frame(driver, expected_revision)
    _, envelope = _send(driver, current, step=RESULT_STEP, fields={
        "submitted_request_id": request_id, "action_id": action_id,
    }, timeout_seconds=timeout_seconds)
    owner = _owner_identity(envelope.get("submission"), current)
    native = envelope.get("independent_result")
    if (owner["request_id"] != request_id or owner["request"]["action_id"] != action_id
            or not isinstance(native, dict) or native.get("request_id") != request_id
            or native.get("action_id") != action_id or native.get("submit_status") != owner["status"]
            or native.get("base_payment_observed") is not False
            or native.get("native_base_piety_charge_raw") is not None
            or native.get("native_execute_observed") is not False
            or native.get("conversion_causality_inferred") is not False):
        raise BridgeUnavailableError("conversion independent result lost its retained request")
    target = owner["request"]["target_rite_id"]
    if owner["status"] != "queued_verification_pending":
        return {"schema": RESULT_SCHEMA, **private_native_provenance(current),
                "status": "noop_preexisting_target_match" if owner["status"] == "already_target_noop" else "rejected_before_submit",
                "request_id": request_id, "action_id": action_id, "target_rite_id": target,
                "material_result": False, "verification_pending": False,
                "owner_submission": deepcopy(owner), "owner_result": deepcopy(native),
                "automatic_retry": False, "advertised": False}
    try:
        baseline = _normalize_baseline(owner, current)
        paid = _normalize_paid(owner, current)
        after = normalize_player_religion_conversion_outcome_v1(
            native.get("after"), snapshot=current, target_rite_id=target)
        if after["capture_epoch"] != envelope["capture_epoch"]:
            raise ValueError("conversion after state differs from the current owner pump")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    before_context, after_context = _context(baseline), _context(after)
    if native.get("after_actor_available") is not (after_context is not None):
        raise BridgeUnavailableError("conversion result lost its actual actor availability")
    net = {key: None for key in RESOURCES}
    preexisting = changed = target_reached = faith_reached = None
    if before_context is not None and after_context is not None:
        before_rite, after_rite = before_context.get("rite_id"), after_context.get("rite_id")
        if before_rite is not None and after_rite is not None:
            preexisting, changed = before_rite == target, before_rite != after_rite
            target_reached = after_rite == target
        after_faith = after_context.get("faith_id")
        if after_faith is not None:
            faith_reached = after_faith == paid["final_gate"]["target_faith_id"]
        for key in RESOURCES:
            old, new = baseline["actor"].get(key), after["actor"].get(key)
            if _integer(old, -(1 << 63), (1 << 63) - 1) and _integer(new, -(1 << 63), (1 << 63) - 1):
                net[key] = new - old
    quote = paid["cost"]["piety_cost_raw"]
    facts = {"target_already_reached_before": preexisting, "actual_rite_changed": changed,
             "actual_target_reached_after": target_reached, "actual_target_faith_reached_after": faith_reached,
             "piety_net_delta_raw": net["piety_raw"], "gold_net_delta_raw": net["gold_raw"],
             "prestige_net_delta_raw": net["prestige_raw"], "quoted_base_piety_cost_raw": quote}
    if any(native.get(key) != value for key, value in facts.items()):
        raise BridgeUnavailableError("conversion result differs from independent before/after facts")
    material = (after["capture_epoch"] > owner["capture_epoch"]
                and preexisting is False and changed is True and target_reached is True
                and faith_reached is True and all(value is not None for value in net.values()))
    if (native.get("request_associated_conversion_material_observed") is not material
            or native.get("verification_pending") is not (not material)):
        raise BridgeUnavailableError("conversion material lacks its queued request and later actual state")
    return {
        "schema": RESULT_SCHEMA, **private_native_provenance(current),
        "status": "converted_material_verified" if material else "submitted_verification_pending",
        "request_id": request_id, "action_id": action_id,
        "player_character_id": owner["played_character_id"], "target_rite_id": target,
        "material_result": material, "verification_pending": not material,
        "request_associated_conversion_material_observed": material,
        **facts, "actual_net_resources_raw": net, "raw_scale": 100000,
        "base_payment_observed": False, "native_base_piety_charge_raw": None,
        "native_execute_observed": False, "conversion_causality_inferred": False,
        "before_outcome": baseline, "after_outcome": after,
        "owner_submission": deepcopy(owner), "owner_result": deepcopy(native),
        "automatic_retry": False, "advertised": False,
    }
