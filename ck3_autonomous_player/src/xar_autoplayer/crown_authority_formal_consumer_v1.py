"""Ordinary Crown fallback using existing query, enact and material receipt.

This product state follows the existing dedicated institution consumer pattern.
The native transport owns its full-quote admission and material verification.
No ACK, restored state file or cold current-law observation becomes a native
command receipt. Urgent steps and earlier institution choices are unchanged.
"""
from dataclasses import asdict
import json
from pathlib import Path
from typing import Mapping
import uuid

from .bridge.realm_law_formal_private_transport import SUBMIT_STEP, RECEIPT_STEP
from .crown_authority_policy_v1 import choose_crown_authority_upgrade_v1
from .environment import write_json_atomic

_STATE = "crown-authority-formal-v1.json"


def read_crown_authority_state_v1(state_dir: Path) -> dict[str, object]:
    path = state_dir / _STATE
    if not path.exists():
        return {"pending": None, "resolved": None}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write(state_dir: Path, state: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _STATE, dict(state))


def _snapshot(driver: object) -> dict[str, object]:
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    return reader() if callable(reader) else driver.take_snapshot()


def _context(driver: object, snapshot: Mapping[str, object]) -> dict[str, object]:
    return {"bridge_pid": getattr(driver, "_session_bridge_pid", None),
            "episode_run_id": snapshot.get("episode_run_id")}


def _checked_frame(driver: object, snapshot: Mapping[str, object]) -> dict[str, object]:
    return {**_context(driver, snapshot), "native_revision": snapshot.get("native_revision"),
            "date_raw": snapshot.get("date_raw")}


def _record(driver: object, step: str, result: Mapping[str, object]) -> None:
    record = getattr(driver, "_record_command", None)
    if callable(record):
        record(step, ok=True, result=dict(result))


def _new_action_id() -> str:
    return "crown-formal-" + uuid.uuid4().hex


def plan_crown_authority_private_v1(
    driver: object, planned: dict[str, object],
) -> dict[str, object]:
    """Inspect Crown only after ordinary precedence still selects advance."""
    plan = planned.get("plan")
    if (getattr(driver, "allow_private_realm_law_action", False) is not True
            or not isinstance(plan, dict) or plan.get("selected_step") != "life-advance"):
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        return {**planned, "plan": {**plan, "crown_status": "durable_state_unavailable"}}
    snapshot = _snapshot(driver)
    state = read_crown_authority_state_v1(state_dir)
    pending = state.get("pending")
    if isinstance(pending, dict):
        cold = pending.get("source_context") != _context(driver, snapshot)
        fields = {**plan, "crown_pending_action": pending,
                  "crown_cold_recovery": cold}
        # After a negative independent read, retain the pending command and
        # ordinary clock route until the actual source frame changes. This
        # consumes the already observed result; it is not a future-date gate.
        if (not cold and pending.get("last_checked_frame") == _checked_frame(driver, snapshot)):
            return {**planned, "plan": {**fields,
                "crown_status": "pending_result_observed",
                "reason": plan.get("reason", "continue the ordinary route while Crown remains unresolved")}}
        return {**planned, "revision": snapshot["revision"],
            "snapshot_id": snapshot.get("snapshot_id"), "plan": {**fields,
                "selected_step": RECEIPT_STEP,
                "phase": "crown_cold_current_state_read" if cold else "crown_independent_receipt",
                "reason": "independently resolve the existing Crown action; never repeat its submission"}}

    readback = driver.query_realm_law_crown_action_private_v1(expected_revision=snapshot["revision"])
    current = _snapshot(driver)
    choice = choose_crown_authority_upgrade_v1(readback)
    fields = {**plan, "crown_readback": readback, "crown_decision": asdict(choice),
              "crown_observation_consumed": readback.get("available") is True}
    resolved = state.get("resolved")
    if isinstance(resolved, dict) and resolved.get("episode_run_id") == current.get("episode_run_id"):
        consumption = {**resolved,
            "next_turn_consumed": readback.get("active_law_key") == resolved.get("law_key"),
            "next_turn_snapshot_id": current.get("snapshot_id"),
            "next_turn_native_revision": current.get("native_revision"),
            "next_turn_date_raw": current.get("date_raw"),
            "next_turn_effective_law_key": readback.get("active_law_key"),
            "next_turn_context": _context(driver, current)}
        fields["crown_result_consumed"] = consumption
        _write(state_dir, {**state, "resolved": consumption})
    if choice.status == "ready":
        fields.update(selected_step=SUBMIT_STEP, phase="crown_ordinary_typed_enact",
                      reason="enact the source-backed positive-score Crown upgrade using its final native quote")
    return {**planned, "revision": current["revision"],
            "snapshot_id": current.get("snapshot_id"), "plan": fields}


def submit_crown_authority_private_v1(
    driver: object, *, plan: Mapping[str, object],
) -> dict[str, object]:
    state_dir = driver.state_dir
    state = read_crown_authority_state_v1(state_dir)
    if state.get("pending") is not None:
        raise ValueError("Crown submission already has a pending product record")
    readback = plan["crown_readback"]
    choice = choose_crown_authority_upgrade_v1(readback)
    if choice.status != "ready":
        raise ValueError("Crown submit lacks the selected native-legal quoted upgrade")
    before = _snapshot(driver)
    action_id = _new_action_id()
    pending = {"stage": "submission_unresolved", "episode_run_id": before.get("episode_run_id"),
        "actor_character_id": readback["player_character_id"], "action_id": action_id,
        "law_key": choice.law_key, "readback": dict(readback), "choice": asdict(choice),
        "budgets": dict(choice.budgets_raw), "source_context": _context(driver, before),
        "pre_native_revision": before.get("native_revision"), "pre_date_raw": before.get("date_raw"),
        "ack": None}
    _write(state_dir, {**state, "pending": pending})
    result = driver.submit_realm_law_crown_private_v1(
        readback=readback, law_key=choice.law_key, budgets=dict(choice.budgets_raw), action_id=action_id)
    if result.get("status") == "rejected_before_submit":
        _write(state_dir, {**state, "pending": None, "resolved": {**pending,
            "status": "rejected_before_submit", "material_result": False, "ack": result}})
    else:
        pending = {**pending, "stage": "receipt_pending", "ack": result}
        _write(state_dir, {**state, "pending": pending})
    _record(driver, SUBMIT_STEP, result)
    return result


def read_crown_authority_receipt_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    state_dir = driver.state_dir
    state = read_crown_authority_state_v1(state_dir)
    before = _snapshot(driver)
    cold = pending.get("source_context") != _context(driver, before)
    if cold:
        # The old DLL's pending record is not a durable native receipt. A
        # fresh strict query classifies the loaded campaign, without inventing
        # old command/resource attribution or sending that command again.
        readback = driver.query_realm_law_crown_action_private_v1(expected_revision=expected_revision)
        result = {"status": "cold_current_law_observed", "material_result": False,
            "action_id": pending["action_id"], "requested_law_key": pending["law_key"],
            "effective_law_key": readback.get("active_law_key"),
            "requested_law_observed": readback.get("active_law_key") == pending["law_key"],
            "readback": readback, "original_native_receipt_available": False}
        resolved = {**dict(pending), **result, "episode_run_id": before.get("episode_run_id"),
            "post_context": _context(driver, before), "native_receipt": None,
            "post_native_revision": before.get("native_revision"), "post_date_raw": before.get("date_raw")}
        _write(state_dir, {**state, "pending": None, "resolved": resolved})
    else:
        result = driver.query_realm_law_crown_receipt_private_v1(
            expected_revision=expected_revision, submitted_request_id=pending["action_id"])
        if (result.get("status") == "enacted" and result.get("material_result") is True
                and result.get("effective_law_key") == pending["law_key"]):
            resolved = {**dict(pending), "status": "enacted", "material_result": True,
                "native_receipt": result, "post_context": _context(driver, before),
                "post_native_revision": result.get("post_public_revision"),
                "post_date_raw": result.get("post_date_raw")}
            _write(state_dir, {**state, "pending": None, "resolved": resolved})
        else:
            observed = {**dict(pending), "last_receipt": result,
                        "last_checked_frame": _checked_frame(driver, before)}
            _write(state_dir, {**state, "pending": observed})
    _record(driver, RECEIPT_STEP, result)
    return result
