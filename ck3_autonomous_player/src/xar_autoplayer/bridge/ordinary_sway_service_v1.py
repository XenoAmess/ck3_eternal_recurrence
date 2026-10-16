"""Optional ordinary Sway work; plan stages only, execution owns every read/send."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ..environment import write_json_atomic
from ..ordinary_sway_schedule_v1 import (
    plan_ordinary_sway_schedule_v1, complete_ordinary_sway_check_v1,
)
from ..ordinary_sway_lifecycle_observation_v1 import (
    READERS, observe_resolved_sway_lifecycle_v1,
)
from ..sway_formal_consumer import read_sway_ledger, consume_sway_private_once
from .driver import BridgeUnavailableError, UnsupportedStepError

STEP = "ordinary-sway-opportunity-v1"
STATE_FILE = "ordinary-sway-schedule-v1.json"
INPUT = "_ordinary_sway_input_v1"


def project_ordinary_sway_input_v1(snapshot: Mapping[str, object], root_result: object) -> dict:
    """Copy existing planner inputs only; safe inside the planning-view lock."""
    played = snapshot.get("played_character")
    context = snapshot.get("active_context")
    if not isinstance(context, Mapping):
        context = ({key: snapshot[key] for key in ("active_event", "pending_character_interaction")}
                   if all(key in snapshot for key in ("active_event", "pending_character_interaction"))
                   else None)
    frame = {key: snapshot.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "paused", "map_ready",
        "episode_run_id", "episode_character_id", "one_life_terminal_reason",
    )}
    frame["played_character"] = dict(played) if isinstance(played, Mapping) else None
    frame["active_context"] = dict(context) if isinstance(context, Mapping) else None
    root = root_result.get("campaign_root_context") if isinstance(root_result, Mapping) else None
    compact = None
    if isinstance(root, Mapping):
        compact = {key: root.get(key) for key in (
            "status", "player_character_id", "player_character_alive", "snapshot_revision", "date_raw",
        )}
        ids = root.get("direct_landed_vassal_character_ids")
        compact["direct_landed_vassal_character_ids"] = list(ids) if isinstance(ids, list) else None
    return {"snapshot": frame, "root": compact}


def _inputs(service):
    state_dir = service._strategy_state_dir()
    if not isinstance(state_dir, Path):
        return None
    path = state_dir / STATE_FILE
    state = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    if state is not None and not isinstance(state, dict):
        raise ValueError("ordinary Sway scheduler state is not an object")
    return state_dir, state, read_sway_ledger(state_dir)


def stage_ordinary_sway_v1(service, planned: dict) -> dict:
    """No Native call, submit, state write or additional snapshot in readonly plan."""
    plan = planned.get("plan")
    source = planned.get(INPUT)
    if (not isinstance(plan, dict) or plan.get("selected_step") != "life-advance"
            or not isinstance(source, Mapping) or not isinstance(source.get("snapshot"), Mapping)):
        return planned
    frame = source["snapshot"]
    if any(planned.get(k) != frame.get(k) for k in ("snapshot_id", "revision")):
        return planned
    driver = service.driver
    formal = (getattr(driver, "allow_private_active_scheme_sway_query", False) is True
              and getattr(driver, "allow_private_active_scheme_sway_action", False) is True)
    observe = any(getattr(driver, row[1], False) is True for row in READERS)
    if not formal and not observe:
        return planned
    try:
        inputs = _inputs(service)
        if inputs is None:
            return planned
        _, state, ledger = inputs
        job = plan_ordinary_sway_schedule_v1(
            source["snapshot"], selected_step=plan["selected_step"],
            root=source.get("root"), ledger=ledger, state=state,
        )
    except (OSError, ValueError) as error:
        return {**planned, "ordinary_sway_optional": {"status": "unavailable", "reason": str(error)}}
    if job["job"] is None:
        return planned
    if job["job"] in {"query_selected_target", "reconcile_pending", "complete_no_relation"} and not formal:
        return planned
    if job["job"] == "observe_applied" and not observe:
        return planned
    return {
        **planned,
        "plan": {**plan, "selected_step": STEP,
                 "reason": "Improve or observe a current vassal relationship",
                 "ordinary_sway_job_v1": job},
    }


def _finish(state_dir, job, frame, outcome, result) -> dict:
    state = complete_ordinary_sway_check_v1(
        job["state"], date_raw=frame["date_raw"], job_kind=job["job"], outcome=outcome,
        target_character_id=job.get("target_character_id"),
        action_id=job.get("action_id") or result.get("action_id"),
    )
    receipt = {"job": job["job"], "target_character_id": job.get("target_character_id"),
               "outcome": outcome, "result": result, "scheduler_state": state,
               "same_pid_or_runtime_claim": False}
    try:
        write_json_atomic(state_dir / STATE_FILE, state)
    except OSError as error:
        receipt["scheduler_state_write_error"] = str(error)
    return receipt


def _ordinary_fallback(service, receipt, before_submit):
    # Internal planning does not stage optional Sway, so this never recurses into
    # the same job. It takes the current normal frame after the optional read.
    fresh = service._plan_turn_internal()
    outcome = service._execute_planned_turn(fresh, before_submit=before_submit)
    return {**outcome, "ordinary_sway_optional": receipt,
            "_ordinary_sway_following_plan_v1": fresh}


def execute_ordinary_sway_v1(service, planned: dict, *, before_submit=None) -> dict:
    """Called only after the existing before_submit decision hook, outside lock."""
    plan = planned["plan"]
    job = plan["ordinary_sway_job_v1"]
    frame = planned[INPUT]["snapshot"]
    try:
        inputs = _inputs(service)
    except (OSError, ValueError) as error:
        return _ordinary_fallback(service, {"status": "unavailable", "reason": str(error)}, before_submit)
    if inputs is None:
        return _ordinary_fallback(service, {"status": "unavailable", "reason": "state_dir_absent"}, before_submit)
    state_dir, _, ledger = inputs
    kind = job["job"]
    result = {}
    outcome = "unavailable"
    actual_new_start = False
    try:
        if kind == "observe_applied":
            result = observe_resolved_sway_lifecycle_v1(service, snapshot=frame) or {
                "status": "unavailable", "reason": "existing_observer_unready"}
            outcome = "observed" if result.get("status") == "observed" else "unavailable"
        elif kind == "complete_no_relation":
            result, outcome = {"status": "known_empty_relation_frontier"}, "no_operation"
        else:
            pending = ledger.get("pending")
            if kind == "reconcile_pending" and (
                    not isinstance(pending, Mapping) or pending.get("action_id") != job.get("action_id")):
                result = {"status": "pending_identity_changed", "submit_attempted": False}
            elif kind == "query_selected_target" and isinstance(pending, Mapping):
                result, outcome = {"status": "original_pending_preserved", "submit_attempted": False}, "pending"
            else:
                read = service.driver.query_active_scheme_sway_target_private_v1(
                    expected_revision=frame["revision"], target_character_id=job["target_character_id"])
                result = consume_sway_private_once(
                    service.driver, target_character_id=job["target_character_id"],
                    snapshot=frame, readback=read)
                status = result.get("status")
                actual_new_start = (kind == "query_selected_target" and status == "applied"
                                    and result.get("postcondition_verified") is True)
                if actual_new_start:
                    outcome = "applied"
                elif status in {"receipt_pending", "postcondition_pending", "submission_unresolved", "pending_recovery"}:
                    outcome = "pending"
                elif status == "no_positive_opportunity":
                    outcome = "no_operation"
                elif status == "already_applied" and result.get("followup", {}).get("decision") in {
                        "finish_selected_relation", "return_to_opportunity_selection", "native_start_unavailable"}:
                    outcome = "no_operation"
                else:
                    outcome = "observed"
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        # The original consumer retains its durable intent if a submit occurred.
        # Optional failure never hides that ledger or authorizes another send.
        result = {"status": "unavailable", "error": f"{type(error).__name__}: {error}"}
    receipt = _finish(state_dir, job, frame, outcome, result)
    if actual_new_start:
        return {"status": "executed", "selected_step": STEP, "plan": plan,
                "result": result, "ordinary_sway_optional": receipt}
    return _ordinary_fallback(service, receipt, before_submit)
