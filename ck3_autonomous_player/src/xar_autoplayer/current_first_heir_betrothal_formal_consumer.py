"""Consume a current, native-final adult betrothal without choosing a new pair."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping

from .bridge.current_first_heir_betrothal_private_action_v1 import (
    SUBMIT_STEP, submit_current_first_heir_betrothal_private_v1,
)
from .bridge.current_first_heir_relationship_private_transport import (
    SCHEMA as RELATION_SCHEMA, _COST_FIELDS, _current_pair_actionability,
)
from .bridge.declaration_contract import is_native_declaration_step
from .bridge.domain_construction_private_transport_v1 import _identity
from .bridge.observed_heir_marriage_private_action_v1 import RESULT_STEP, SCHEMA
from .family_marriage_formal_consumer import (
    _write, query_family_marriage_result_private, read_family_marriage_ledger,
)
from .current_betrothal_fulfillment_proposal import (
    build_current_betrothal_fulfillment_proposal,
)


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _paused_actor(snapshot: Mapping[str, object]) -> int | None:
    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True
            or snapshot.get("map_ready") is not True
            or not isinstance(played, Mapping)
            or played.get("alive") is not True
            or not _positive(played.get("character_id"))
            or not _positive(snapshot.get("native_revision"))
            or type(snapshot.get("date_raw")) is not int
            or not isinstance(snapshot.get("episode_run_id"), str)):
        return None
    return played["character_id"]


def evaluate_current_betrothal_fulfillment(
    relationship: Mapping[str, object], snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Value only completing this actual adult pair at observed zero send costs."""
    actor = _paused_actor(snapshot)
    heir = relationship.get("heir_character_id")
    partner = relationship.get("betrothed_character_id")
    reasons: list[str] = []
    if (actor is None
            or relationship.get("schema") != RELATION_SCHEMA
            or relationship.get("exact_ck3_build") != "1.19.0.6"
            or relationship.get("native_revision") != snapshot.get("native_revision")
            or relationship.get("read_only") is not True
            or relationship.get("advertised") is not False):
        raise ValueError("betrothal fulfillment observation crossed its formal frame")
    if (relationship.get("status") != "available"
            or relationship.get("bilateral_verified") is not True):
        reasons.append("current_pair_unavailable")
    if not _positive(heir) or not _positive(partner):
        reasons.append("no_current_bilateral_betrothal")
    if (relationship.get("primary_spouse_character_id") is not None
            or relationship.get("spouse_character_ids") != []):
        reasons.append("current_heir_already_married")
    value = _current_pair_actionability(
        relationship.get("betrothal_actionability"),
        actor=actor, heir=heir, partner=partner)
    if value.get("status") != "available":
        reasons.append("current_pair_value_unknown")
    if value.get("ready_to_marry_betrothed") is not True:
        reasons.append("actual_pair_not_ready")
    if value.get("complete_can_send") is not True:
        reasons.append("native_final_can_send_not_true")
    if (value.get("recipient_acceptance_ready") is not True
            or value.get("recipient_answer_status_raw") not in (0, 1)
            or not _positive(value.get("recipient_ai_accept_raw"))):
        reasons.append("native_recipient_not_positive")
    if value.get("predicted_outcome_if_accepted") != "marriage":
        reasons.append("native_outcome_not_marriage")
    costs = value.get("generic_costs")
    if not isinstance(costs, Mapping) or any(costs.get(key) != 0 for key in _COST_FIELDS):
        reasons.append("nonzero_or_unknown_send_cost_requires_joint_budget")
    selected = not reasons
    return {
        "status": "selected" if selected else "held",
        "reasons": reasons,
        "selected_step": SUBMIT_STEP if selected else None,
        "heir_character_id": heir, "candidate_character_id": partner,
        "recipient_character_id": value.get("recipient_character_id"),
        "intermediary_character_id": value.get("intermediary_character_id"),
        "generic_costs": deepcopy(costs),
        "effective_matrilineal_if_accepted": value.get("effective_matrilineal_if_accepted"),
        "predicted_outcome_if_accepted": value.get("predicted_outcome_if_accepted"),
        "resource_proposal": build_current_betrothal_fulfillment_proposal(
            dict(relationship), dict(snapshot), selected=selected, reasons=reasons),
    }


def _handled(planned: dict[str, object], **fields: object) -> dict[str, object]:
    return {**planned, "plan": {**planned["plan"],
                                "current_betrothal_fulfillment": True, **fields}}


def plan_current_first_heir_betrothal_fulfillment_private(
    driver: object, planned: dict[str, object], snapshot: Mapping[str, object],
    *, prewar_arbitration: bool = False, wartime_arbitration: bool = False,
) -> dict[str, object]:
    """Keep ordinary actions; query/submit only this opted-in fixed-pair contract."""
    if getattr(driver, "allow_private_current_first_heir_betrothal_fulfillment", False) is not True:
        return planned
    plan = planned.get("plan")
    actor = _paused_actor(snapshot)
    if not isinstance(plan, dict) or actor is None:
        return planned
    selected = plan.get("selected_step")
    if (isinstance(selected, str) and selected != "life-advance"
            and not selected.startswith("query-")
            and not (prewar_arbitration is True and is_native_declaration_step(selected))):
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise ValueError("betrothal fulfillment requires the durable family state_dir")
    ledger = read_family_marriage_ledger(state_dir)
    pending = ledger.get("pending")
    resolved = ledger.get("resolved")
    pid, creation = _identity(driver)
    if isinstance(pending, dict):
        if pending.get("fulfill_existing_betrothal") is not True:
            return planned
        if (pending.get("episode_run_id") != snapshot.get("episode_run_id")
                or pending.get("played_character_id") != actor):
            return _handled(planned, selected_step=None,
                            current_betrothal_status="pending_identity_changed")
        cold = (pid, creation) != (pending.get("source_bridge_pid"),
                                   pending.get("source_bridge_creation_date"))
        checked_here = (pid, creation) == (pending.get("last_checked_bridge_pid"),
                                          pending.get("last_checked_bridge_creation_date"))
        last = pending.get("last_checked_native_revision", pending.get("pre_native_revision", 0))
        consumed = pending.get("last_consumed_checkpoint_native_revision")
        if checked_here and _positive(consumed):
            last = max(last, consumed)
        date = pending.get("last_consumed_checkpoint_date_raw",
                           pending.get("last_checked_date_raw", pending.get("source_date_raw")))
        if ((cold and not checked_here) or snapshot["native_revision"] > last
                or (checked_here and type(date) is int and snapshot["date_raw"] > date)):
            return _handled(planned, selected_step=RESULT_STEP,
                phase="current_first_heir_betrothal_result_read",
                current_betrothal_pending=deepcopy(pending),
                current_betrothal_cold_recovery=cold,
                reason="read fulfillment reply and actual marriage without resubmitting")
        return _handled(planned, current_betrothal_pending=deepcopy(pending),
                        current_betrothal_status="await_later_paused_frame")
    source = resolved.get("source_pending") if isinstance(resolved, dict) else None
    if (isinstance(source, dict) and source.get("fulfill_existing_betrothal") is True
            and source.get("episode_run_id") == snapshot.get("episode_run_id")
            and source.get("played_character_id") == actor):
        if resolved.get("status") == "marriage" and (pid, creation) != (
                resolved.get("post_bridge_pid"), resolved.get("post_bridge_creation_date")):
            return _handled(planned, selected_step=RESULT_STEP,
                phase="current_first_heir_betrothal_cold_material_recheck",
                current_betrothal_pending=deepcopy(source),
                current_betrothal_cold_recovery=True,
                current_betrothal_material_recheck=True,
                reason="independently read the fulfilled marriage in the restored PID")
        return _handled(planned, current_betrothal_status=resolved.get("status"),
                        current_betrothal_result_consumed=deepcopy(resolved))
    war_read = (wartime_arbitration is True and isinstance(selected, str)
                and (selected == "life-advance" or selected.startswith("query-"))
                and isinstance(snapshot.get("active_wars"), list)
                and bool(snapshot["active_wars"]))
    if selected != "life-advance" and not (
            prewar_arbitration is True and is_native_declaration_step(selected)) and not war_read:
        return planned
    if (snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return planned
    relation = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=snapshot["native_revision"])
    if (relation.get("status") == "available"
            and relation.get("betrothed_character_id") is None):
        return planned
    choice = evaluate_current_betrothal_fulfillment(relation, snapshot)
    fields = {"current_betrothal_relationship": deepcopy(relation),
              "current_betrothal_choice": choice,
              "current_betrothal_status": choice["status"]}
    if choice["status"] == "selected":
        fields.update(selected_step=SUBMIT_STEP,
                      phase="current_first_heir_betrothal_typed_submit",
                      reason="fulfill the actual native-final adult betrothal")
    return _handled(planned, **fields)


def submit_current_first_heir_betrothal_fulfillment_private(
    driver: object, *, plan: Mapping[str, object], snapshot: Mapping[str, object],
) -> dict[str, object]:
    relation = plan.get("current_betrothal_relationship")
    choice = plan.get("current_betrothal_choice")
    if (plan.get("current_betrothal_fulfillment") is not True
            or plan.get("selected_step") != SUBMIT_STEP
            or not isinstance(relation, dict) or not isinstance(choice, dict)
            or choice.get("status") != "selected"
            or choice != evaluate_current_betrothal_fulfillment(relation, snapshot)):
        raise ValueError("betrothal fulfillment lacks its selected fixed-pair value")
    ledger = read_family_marriage_ledger(driver.state_dir)
    if ledger.get("pending") is not None:
        raise ValueError("family already has an unresolved proposal")
    resolved = ledger.get("resolved")
    prior_source = resolved.get("source_pending") if isinstance(resolved, dict) else None
    if (isinstance(prior_source, dict)
            and prior_source.get("fulfill_existing_betrothal") is True
            and prior_source.get("episode_run_id") == snapshot.get("episode_run_id")
            and prior_source.get("heir_character_id") == choice["heir_character_id"]
            and prior_source.get("candidate_character_id") == choice["candidate_character_id"]):
        raise ValueError("this fulfillment pair already has a consumed reply")
    pid, creation = _identity(driver)
    pending = {
        "schema": SCHEMA, "schema_version": 1, "exact_ck3_build": "1.19.0.6",
        "step": SUBMIT_STEP, "status": "receipt_pending", "material_result": False,
        "advertised": False, "fulfill_existing_betrothal": True,
        "pre_native_revision": snapshot["native_revision"],
        "source_date_raw": snapshot["date_raw"],
        "played_character_id": snapshot["played_character"]["character_id"],
        "heir_character_id": choice["heir_character_id"],
        "candidate_character_id": choice["candidate_character_id"],
        "recipient_character_id": choice["recipient_character_id"],
        "intermediary_character_id": choice["intermediary_character_id"],
        "matrilineal_option_selected": choice["effective_matrilineal_if_accepted"],
        "episode_run_id": snapshot["episode_run_id"],
        "source_bridge_pid": pid, "source_bridge_creation_date": creation,
        "prior_betrothal_relationship": deepcopy(relation),
        "selected_value_projection": deepcopy(relation["betrothal_actionability"]),
        "resource_proposal": deepcopy(choice["resource_proposal"]),
        "submission_state": "may_have_submitted",
    }
    _write(driver.state_dir, {**ledger, "pending": pending})
    result = submit_current_first_heir_betrothal_private_v1(driver, relationship=relation)
    pending.update(result)
    pending["submission_state"] = "receipt_pending"
    _write(driver.state_dir, {**ledger, "pending": pending})
    return pending


def query_current_first_heir_betrothal_fulfillment_result_private(
    driver: object, *, pending: Mapping[str, object], cold: bool,
) -> dict[str, object]:
    if pending.get("fulfill_existing_betrothal") is not True:
        raise ValueError("fulfillment result lacks its durable mode")
    before = driver.take_snapshot()
    result = query_family_marriage_result_private(driver, pending=pending, cold=cold)
    if (result.get("fulfill_existing_betrothal") is not True
            or result.get("status") not in {
                "pending", "accepted_pending", "refused", "invalidated", "marriage"}):
        raise ValueError("fulfillment result cannot consume the original betrothal")
    ledger = read_family_marriage_ledger(driver.state_dir)
    updated = ledger.get("pending")
    if isinstance(updated, dict):
        updated = {**updated, "last_checked_date_raw": before["date_raw"]}
        updated.pop("last_consumed_checkpoint_native_revision", None)
        updated.pop("last_consumed_checkpoint_date_raw", None)
        _write(driver.state_dir, {**ledger, "pending": updated})
    elif isinstance(ledger.get("resolved"), dict):
        _write(driver.state_dir, {**ledger, "resolved": {
            **ledger["resolved"], "fulfill_existing_betrothal": True}})
    return result


def consume_current_first_heir_betrothal_result_checkpoint(
    driver: object, *, before: Mapping[str, object], snapshot: Mapping[str, object],
) -> None:
    """Consume only the official checkpoint after this actual pending read."""
    ledger = read_family_marriage_ledger(driver.state_dir)
    pending = ledger.get("pending")
    if not isinstance(pending, dict):
        return
    pid, creation = _identity(driver)
    if (pending.get("fulfill_existing_betrothal") is not True
            or (pid, creation) != (pending.get("last_checked_bridge_pid"),
                                  pending.get("last_checked_bridge_creation_date"))
            or pending.get("last_checked_native_revision") != before.get("native_revision")
            or _paused_actor(snapshot) != pending.get("played_character_id")
            or snapshot["native_revision"] < before.get("native_revision", 0)
            or snapshot.get("date_raw") != before.get("date_raw")
            or snapshot.get("episode_run_id") != pending.get("episode_run_id")):
        raise ValueError("fulfillment checkpoint crossed its observed pending frame")
    _write(driver.state_dir, {**ledger, "pending": {
        **pending, "last_consumed_checkpoint_native_revision": snapshot["native_revision"],
        "last_consumed_checkpoint_date_raw": snapshot["date_raw"],
    }})
