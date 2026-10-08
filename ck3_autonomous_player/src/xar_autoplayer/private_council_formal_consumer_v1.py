"""Consume default Steward or explicitly configured Chancellor adjustments.

The existing skill policy chooses among candidates passing the exact native
final gates. A helper ACK remains pending until the existing receipt reader
and an independent campaign-root position observation confirm the holder.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Mapping
import uuid

from .environment import write_json_atomic
from .bridge.council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_CAPABILITY,
    build_assign_councillor_request_v1,
    normalize_assign_councillor_ack_v1,
    normalize_assign_councillor_receipt_v1,
)
from .bridge.council_composition_candidates_contract import (
    CHANCELLOR_POSITION_KEY,
    STEWARD_POSITION_KEY,
    normalize_council_composition_candidates_v1,
)
from .bridge.council_private_transport_v1 import PRIVATE_ASSIGN_STEP, PRIVATE_RECEIPT_STEP
from .strategy import _plan_council_composition_v1

SUBMIT_STEP = PRIVATE_ASSIGN_STEP
RECEIPT_STEP = PRIVATE_RECEIPT_STEP
ROOT_QUERY_STEP = "query-campaign-root-context-v1"
LEDGER_FILENAME = "private-council-formal-v1.json"
_SCHEMA = "xar.ck3.private-council-formal/v1"


def read_council_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / LEDGER_FILENAME
    if not path.exists():
        return {"schema": _SCHEMA, "pending": None, "applied": None}
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or value.get("schema") != _SCHEMA
            or any(value.get(key) is not None and not isinstance(value[key], dict)
                   for key in ("pending", "applied"))):
        raise ValueError("private council formal ledger is malformed")
    return value


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / LEDGER_FILENAME, dict(ledger))


def _state(driver: object, state_dir: Path | None = None) -> Path:
    selected = state_dir if state_dir is not None else getattr(driver, "state_dir", None)
    if not isinstance(selected, Path):
        raise ValueError("private council formal consumer requires state_dir")
    return selected


def _snapshot(driver: object) -> dict[str, object]:
    read = getattr(driver, "take_internal_semantic_snapshot", None) or getattr(driver, "take_snapshot")
    value = read()
    if not isinstance(value, dict):
        raise ValueError("private council snapshot missing")
    return value


def _actor(snapshot: Mapping[str, object]) -> object:
    played = snapshot.get("played_character")
    return played.get("character_id") if isinstance(played, Mapping) else None


def _root(
    driver: object, campaign_root_result: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    from .bridge.current_first_heir_relationship_private_transport import (
        _same_frame_campaign_root_result,
    )

    before = _snapshot(driver)
    result = _same_frame_campaign_root_result(campaign_root_result, before)
    if result is None:
        result = driver.execute_step(ROOT_QUERY_STEP, expected_revision=before["revision"])
    root = result.get("campaign_root_context") if isinstance(result, dict) else None
    after = _snapshot(driver)
    if not (isinstance(root, dict) and root.get("status") == "available"
            and root.get("snapshot_revision") == before.get("native_revision")
            and root.get("date_raw") == before.get("date_raw")
            and root.get("player_character_id") == _actor(before)
            and _actor(before) == _actor(after)
            and before.get("date_raw") == after.get("date_raw")
            and before.get("native_revision") == after.get("native_revision")):
        raise ValueError("private council independent root observation unavailable")
    return root, after


def _position(root: Mapping[str, object], position_key: str) -> dict[str, object] | None:
    council = root.get("council")
    rows = council.get("positions") if isinstance(council, Mapping) else None
    if not isinstance(rows, list):
        return None
    return next((dict(row) for row in rows if isinstance(row, Mapping)
                  and row.get("position_key") == position_key), None)


def _job_progress_observation(
    root: Mapping[str, object], snapshot: Mapping[str, object], position_key: str,
    *, previous: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Consume the existing native task fields without assigning utility or ETA."""
    row = _position(root, position_key)
    observation = {"position_key": position_key,
                   "source_native_revision": root.get("snapshot_revision"),
                   "source_date_raw": root.get("date_raw"),
                   "episode_run_id": snapshot.get("episode_run_id")}
    if row is None:
        return {**observation, "status": "unavailable"}
    observation.update(status="vacant" if row.get("incumbent_character_id") is None else "available",
        **{key: copy.deepcopy(row.get(key)) for key in (
            "incumbent_character_id", "task_key", "task_type", "target", "frozen", "progress")},
        effect_attribution="not_observed")
    progress = row.get("progress")
    if isinstance(progress, Mapping) and progress.get("kind") != "infinite":
        current, maximum = progress["current"], progress["maximum"]
        observation["remaining_progress"] = {
            "raw": maximum["raw"] - current["raw"], "scale": current["scale"]}
    if previous is not None:
        prior = previous.get("independent_position")
        comparison = {"status": "job_changed"}
        if isinstance(prior, Mapping) and all(row.get(key) == prior.get(key) for key in (
                "incumbent_character_id", "task_key", "task_type", "target")):
            comparison["status"] = "same_job"
            old_progress = prior.get("progress")
            if (isinstance(progress, Mapping) and isinstance(old_progress, Mapping)
                    and progress.get("kind") == old_progress.get("kind")
                    and progress.get("kind") != "infinite"
                    and progress.get("maximum") == old_progress.get("maximum")):
                comparison["progress_change"] = {
                    "raw": progress["current"]["raw"] - old_progress["current"]["raw"],
                    "scale": progress["current"]["scale"]}
        previous_date = previous.get("post_date_raw")
        if type(previous_date) is int and type(root.get("date_raw")) is int:
            comparison.update(previous_date_raw=previous_date,
                              elapsed_game_hours=root["date_raw"] - previous_date)
        observation["following_comparison"] = comparison
    return observation


def _record_position_key(record: Mapping[str, object]) -> str:
    action = record.get("action_ack")
    ack = action.get("council_assign_councillor_ack") if isinstance(action, Mapping) else None
    query = record.get("source_query")
    payload = query.get("council_composition_candidates") if isinstance(query, Mapping) else None
    position = payload.get("position") if isinstance(payload, Mapping) else None
    source = ack if isinstance(ack, Mapping) else position
    key = source.get("position_key", STEWARD_POSITION_KEY) if isinstance(source, Mapping) else STEWARD_POSITION_KEY
    if key not in {STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY}:
        raise ValueError("Council ledger position is outside assignment coverage")
    return key


def _query_position(driver: object, position_key: str) -> dict[str, object]:
    fresh = _snapshot(driver)
    if position_key == STEWARD_POSITION_KEY:
        # Preserve the legacy default call signature and its existing fixtures.
        return driver.query_council_final_gates_private_v1(expected_revision=fresh["revision"])
    return driver.query_council_final_gates_private_v1(
        expected_revision=fresh["revision"], position_key=position_key,
    )


def select_council_candidate_v1(
    query: Mapping[str, object], *, position_key: str = STEWARD_POSITION_KEY,
    allow_occupied_chancellor: bool = False,
) -> dict[str, object]:
    """Keep every native row as evidence; rank only rows passing native gates."""
    if position_key not in {STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY}:
        raise ValueError("Council assignment position is outside coverage")
    if query.get("status") != "available":
        policy = ("council-composition-steward-v1" if position_key == STEWARD_POSITION_KEY
                  else "council-composition-chancellor-v1")
        return {"policy": policy, "outcome": "QUERY_UNAVAILABLE",
                "reason_code": query.get("unavailable_reason", "private_query_unavailable")}
    payload = query.get("council_composition_candidates")
    gates = query.get("council_final_gates")
    if not isinstance(payload, dict) or not isinstance(gates, Mapping):
        raise ValueError("private council final gates lack the actual candidate payload")
    frame = payload.get("snapshot")
    if not isinstance(frame, dict):
        raise ValueError("private council candidate frame missing")
    observation = normalize_council_composition_candidates_v1(
        payload, expected_snapshot_id=frame.get("snapshot_id"),
        expected_public_revision=frame.get("public_revision"),
        expected_native_revision=frame.get("native_revision"),
        expected_date_raw=frame.get("date_raw"),
        expected_owner_character_id=payload.get("owner_character_id"),
        expected_position_key=position_key,
    )
    rows = gates.get("rows")
    if not (gates.get("status") == "available" and isinstance(rows, list)
            and len(rows) == len(observation["candidates"])
            and gates.get("candidate_count") == len(rows)):
        raise ValueError("private council final gates are incomplete")
    legal, excluded = [], []
    for candidate, gate in zip(observation["candidates"], rows):
        if not isinstance(gate, dict) or any(candidate[key] != gate.get(key)
                for key in ("character_id", "native_collection_ordinal")):
            raise ValueError("private council final-gate row identity mismatch")
        blockers = []
        if gate.get("final_gate_available") is not True:
            blockers.append("final_legality_unavailable")
        for key in ("candidate_already_councillor", "candidate_is_guest", "pending_character_interaction"):
            if gate.get(key) is not False:
                blockers.append(key)
        if (observation["position"]["vacant"] is False and not (
                gate.get("incumbent_fireability_evaluated") is True
                and gate.get("incumbent_can_be_fired") is True)):
            blockers.append("incumbent_cannot_be_replaced")
        if blockers:
            excluded.append({"character_id": candidate["character_id"], "reasons": blockers,
                             "native_gates": copy.deepcopy(gate)})
        else:
            legal.append(candidate)
    planner_options = ({"allow_occupied_chancellor": True}
                       if allow_occupied_chancellor is True else {})
    decision = _plan_council_composition_v1(
        {**observation, "candidates": legal},
        available_capabilities={ASSIGN_COUNCILLOR_V1_CAPABILITY},
        position_key=position_key,
        **planner_options,
    )
    selected = decision.get("selected_candidate")
    incumbent = observation["position"]["incumbent_main_skill"]
    return {**decision, "native_candidate_count": len(observation["candidates"]),
            "legal_candidate_count": len(legal), "native_gate_exclusions": excluded,
            "skill_gain": selected["main_skill"]["value"] - incumbent["value"]
                          if selected and incumbent else None,
            "value_scope": ("native stewardship points; alternate-candidate tax modifier is not observed"
                            if position_key == STEWARD_POSITION_KEY else
                            "native diplomacy points; alternate-task and political utility are not observed")}


def plan_council_private(
    driver: object, planned: dict[str, object], snapshot: Mapping[str, object],
    history: list[dict[str, object]], available_steps: set[str],
    *, state_dir: Path | None = None,
    campaign_root_result: dict[str, object] | None = None,
    position_key: str = STEWARD_POSITION_KEY,
) -> dict[str, object]:
    """Plan one private council turn without public advertisement or war policy."""
    if getattr(driver, "allow_private_council_action", False) is not True:
        return planned
    if position_key not in {STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY}:
        raise ValueError("Council assignment position is outside coverage")
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    state_dir = _state(driver, state_dir)
    ledger = read_council_ledger(state_dir)
    pending = ledger["pending"]
    if isinstance(pending, dict):
        if pending.get("episode_run_id") != snapshot.get("episode_run_id"):
            return {**planned, "plan": {**plan, "selected_step": None,
                "reason": "unresolved council assignment belongs to another episode"}}
        ack = pending.get("action_ack")
        ack_value = ack.get("council_assign_councillor_ack") if isinstance(ack, Mapping) else None
        native = snapshot.get("native_revision")
        later = (isinstance(ack_value, Mapping) and type(native) is int
                 and native > ack_value.get("pre_native_revision", native))
        return {**planned, "plan": {**plan,
            "phase": "council_pending_receipt" if later else "council_pending_later_frame",
            "selected_step": RECEIPT_STEP if later else None,
            "council_pending_action": copy.deepcopy(pending),
            "reason": "observe the existing assignment on a later paused frame; do not submit it again"}}
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return planned
    applied = ledger["applied"]
    applied_role = (_record_position_key(applied)
                    if isinstance(applied, dict) and applied.get("episode_run_id") == snapshot.get("episode_run_id")
                    else None)
    # Keep the configured submission quote in the native mailbox.
    # Persistence for another role uses the independent campaign-root holder.
    query = _query_position(driver, position_key)
    decision = select_council_candidate_v1(
        query, position_key=position_key,
        allow_occupied_chancellor=position_key == CHANCELLOR_POSITION_KEY,
    )
    current = _snapshot(driver)
    next_plan = {**plan, "council_private_query": query, "council_decision": decision,
                 "council_observation_consumed": decision["outcome"] != "QUERY_UNAVAILABLE"}
    from .bridge.current_first_heir_relationship_private_transport import (
        _same_frame_campaign_root_result,
    )
    reused_root = _same_frame_campaign_root_result(campaign_root_result, current)
    root = reused_root.get("campaign_root_context") if reused_root is not None else None
    if isinstance(applied, dict) and applied.get("episode_run_id") == current.get("episode_run_id"):
        root, current = _root(driver, campaign_root_result)
        holder = _position(root, applied_role)
        receipt = applied.get("receipt", {}).get("council_assign_councillor_receipt", {})
        observed = (query.get("council_composition_candidates", {}).get("position", {})
                    if applied_role == position_key else holder)
        persists = bool(holder and holder.get("incumbent_character_id") == applied.get("candidate_character_id")
                        and observed.get("incumbent_character_id") == applied.get("candidate_character_id"))
        consumption = {**applied, "next_turn_consumed": persists,
                       "next_turn_snapshot_id": current.get("snapshot_id"),
                       "next_turn_native_revision": current.get("native_revision"),
                       "next_turn_date_raw": current.get("date_raw"),
                       "next_turn_position": holder,
                       "next_turn_job_progress_observation": _job_progress_observation(
                           root, current, applied_role, previous=applied),
                       "previous_receipt_post_snapshot_id": receipt.get("post_snapshot_id")}
        next_plan["council_receipt_consumed"] = consumption
        if persists:
            _write(state_dir, {**ledger, "applied": consumption})
        else:
            return {**planned, "revision": current["revision"], "snapshot_id": current["snapshot_id"],
                    "plan": {**next_plan, "selected_step": None,
                             "reason": "current council holder differs from the applied assignment"}}
    if decision["outcome"] in {"ASSIGN_REQUIRED", "REPLACE_REQUIRED"}:
        role = "steward" if position_key == STEWARD_POSITION_KEY else "chancellor"
        next_plan.update({"phase": "council_private_typed_submit", "selected_step": SUBMIT_STEP,
                           "reason": f"assign one current native-legal {role} with higher observed skill"})
    elif position_key == STEWARD_POSITION_KEY and decision["outcome"] != "QUERY_UNAVAILABLE":
        if root is None:
            root, current = _root(driver, campaign_root_result)
        chancellor = _position(root, CHANCELLOR_POSITION_KEY)
        if chancellor is not None:
            chancellor_query = _query_position(driver, CHANCELLOR_POSITION_KEY)
            chancellor_decision = select_council_candidate_v1(
                chancellor_query, position_key=CHANCELLOR_POSITION_KEY,
                allow_occupied_chancellor=True,
            )
            current = _snapshot(driver)
            next_plan.update({"council_private_query": chancellor_query,
                              "council_decision": chancellor_decision,
                              "council_observation_consumed": chancellor_decision["outcome"] != "QUERY_UNAVAILABLE"})
            if chancellor_decision["outcome"] in {"ASSIGN_REQUIRED", "REPLACE_REQUIRED"}:
                next_plan.update({"phase": "council_private_typed_submit", "selected_step": SUBMIT_STEP,
                                  "reason": ("fill the observed Chancellor vacancy with one current native-legal candidate"
                                             if chancellor_decision["outcome"] == "ASSIGN_REQUIRED" else
                                             "replace the observed Chancellor with one current native-legal candidate with higher Diplomacy")})
    if root is not None:
        next_plan["council_job_progress_observations"] = [
            _job_progress_observation(root, current, role)
            for role in (STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY)]
        selected_role = next_plan["council_decision"].get("position_key", position_key)
        job = _job_progress_observation(root, current, selected_role)
        next_plan["council_job_progress_observation"] = job
        next_plan["council_decision"] = {**next_plan["council_decision"],
                                        "current_job_progress_observation": copy.deepcopy(job)}
    return {**planned, "revision": current["revision"], "snapshot_id": current["snapshot_id"], "plan": next_plan}


def submit_council_private(
    driver: object, *, plan: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    state_dir = _state(driver)
    ledger = read_council_ledger(state_dir)
    if ledger["pending"] is not None:
        raise ValueError("private council already has an unresolved assignment")
    query, decision = plan.get("council_private_query"), plan.get("council_decision")
    if (not isinstance(query, Mapping) or not isinstance(decision, Mapping)
            or decision.get("outcome") not in {"ASSIGN_REQUIRED", "REPLACE_REQUIRED"}):
        raise ValueError("private council submit lacks a selected current native candidate")
    candidate = decision["selected_candidate"]["character_id"]
    request_id = "council-formal-" + uuid.uuid4().hex
    request = build_assign_councillor_request_v1(query.get("council_composition_candidates"),
                candidate_character_id=candidate, request_id=request_id)
    before = _snapshot(driver)
    pending = {"stage": "submission_unresolved", "episode_run_id": before.get("episode_run_id"),
               "action_request_id": request_id, "candidate_character_id": candidate,
               "source_query": copy.deepcopy(dict(query)), "source_decision": copy.deepcopy(dict(decision)),
               "pre_native_revision": before.get("native_revision"), "pre_date_raw": before.get("date_raw"),
               "request": request.as_wire_fields(), "action_ack": None}
    _write(state_dir, {**ledger, "pending": pending})
    result = driver.submit_council_assign_private_v1(query=query, candidate_character_id=candidate,
                expected_revision=expected_revision, action_request_id=request_id)
    ack = normalize_assign_councillor_ack_v1(result.get("council_assign_councillor_ack"), expected_request=request)
    if ack["status"] == "rejected_before_submit":
        _write(state_dir, {**ledger, "pending": None})
        return result
    pending.update({"stage": "receipt_pending", "action_ack": copy.deepcopy(result)})
    _write(state_dir, {**ledger, "pending": pending})
    return pending


def read_council_receipt_private(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    state_dir = _state(driver)
    ledger = read_council_ledger(state_dir)
    if ledger["pending"] != dict(pending):
        raise ValueError("private council receipt pending differs from ledger")
    native_pending = pending.get("action_ack")
    if not isinstance(native_pending, Mapping):
        return {"status": "submission_unresolved", "source_pending": dict(pending)}
    result = driver.query_council_assign_receipt_private_v1(pending=native_pending, expected_revision=expected_revision)
    receipt = normalize_assign_councillor_receipt_v1(result.get("council_assign_councillor_receipt"),
                expected_ack=native_pending["council_assign_councillor_ack"])
    if receipt["status"] != "applied":
        return {**result, "source_pending": dict(pending)}
    root, current = _root(driver)
    holder = _position(root, _record_position_key(pending))
    if not holder or holder.get("incumbent_character_id") != pending["candidate_character_id"]:
        return {"status": "independent_position_not_applied", "native_receipt": result,
                "independent_position": holder, "source_pending": dict(pending)}
    applied = {"status": "applied", "episode_run_id": pending.get("episode_run_id"),
               "action_request_id": pending["action_request_id"],
               "candidate_character_id": pending["candidate_character_id"],
               "action_ack": copy.deepcopy(native_pending), "receipt": copy.deepcopy(result),
               "post_snapshot_id": current.get("snapshot_id"), "post_native_revision": current.get("native_revision"),
               "post_date_raw": current.get("date_raw"), "independent_position": holder,
               "independent_job_progress_observation": _job_progress_observation(
                   root, current, _record_position_key(pending)),
               "source_decision": copy.deepcopy(pending["source_decision"]), "next_turn_consumed": False}
    _write(state_dir, {**ledger, "pending": None, "applied": applied})
    return applied
