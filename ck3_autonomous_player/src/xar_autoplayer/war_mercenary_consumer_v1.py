"""Normal-turn mercenary query, coarse defensive choice and durable follow-up."""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from pathlib import Path

from .bridge.player_mercenary_context import (
    CAPABILITY as QUERY_CAPABILITY, STEP as QUERY_STEP,
    normalize_player_mercenary_context_v1,
)
from .bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY as ROOT_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP as ROOT_STEP,
)
from .bridge.war_contract import (
    HIRE_MERCENARY_V1_CAPABILITY as HIRE_CAPABILITY,
    HIRE_MERCENARY_V1_STEP as HIRE_STEP,
    is_life_advance_step, parse_advance_route_contact_horizon_step,
)
from .environment import write_json_atomic
from .m5_observed_opportunity_selector import observed_frame
from .war_reinforcement_tradeoff_v1 import (
    _count as observed_army_count,
    assess_mercenary_reinforcement_v1, observe_war_spending_priority_v1,
)

_LEDGER = "war-mercenary-pending-v1.json"


def _ledger(directory: Path) -> dict[str, object]:
    path = directory / _LEDGER
    value = (json.loads(path.read_text(encoding="utf-8")) if path.exists() else
             {"schema": "xar.war-mercenary-pending.v1", "pending": None, "observed": []})
    if (not isinstance(value, dict) or value.get("schema") != "xar.war-mercenary-pending.v1"
            or not isinstance(value.get("observed"), list)
            or value.get("pending") is not None and not isinstance(value["pending"], dict)):
        raise ValueError("unknown durable mercenary pending state")
    return value


def _context(history: list[dict[str, object]], snapshot: Mapping[str, object]):
    frame = observed_frame(snapshot)
    for row in reversed(history):
        result = row.get("result")
        if (row.get("command") != QUERY_STEP or row.get("ok") is not True
                or not isinstance(result, Mapping)
                or result.get("mercenary_query_source_frame_v1") != frame
                or result.get("snapshot_revision") != frame["native_revision"]
                or type(result.get("query_sequence")) is not int or result["query_sequence"] <= 0
                or result.get("read_only") is not True or result.get("accepted") is not True
                or result.get("status") != "completed"):
            continue
        try:
            return normalize_player_mercenary_context_v1(
                result.get("player_mercenary_context"), snapshot=snapshot)
        except ValueError:
            continue
    return None


def plan_war_mercenary_turn_v1(
    driver: object, plan: dict[str, object], *, snapshot: Mapping[str, object],
    history: list[dict[str, object]], bridge_capabilities: set[str],
) -> dict[str, object]:
    """Insert one existing query/hire only at an otherwise quiet war opportunity.

    Missing capabilities or a rejected model preserve the original war action.
    Mandatory windows, concrete army orders and war termination keep priority.
    """
    priority = observe_war_spending_priority_v1(snapshot)
    if not priority["wars"]:
        return plan
    plan = {**plan, "war_spending_priority_v1": priority}
    step = plan.get("selected_step")
    quiet = (is_life_advance_step(step)
             or parse_advance_route_contact_horizon_step(step) is not None)
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None or not quiet):
        return plan
    directory = getattr(driver, "state_dir", None)
    if not isinstance(directory, Path):
        return {**plan, "war_mercenary_status": "durable_state_unavailable"}
    from .construction_formal_consumer import read_construction_ledger

    if read_construction_ledger(directory).get("pending") is not None:
        return {**plan, "war_mercenary_status": "existing_construction_pending_receipt_keeps_priority"}
    ledger = _ledger(directory)
    pending = ledger["pending"]
    frame = observed_frame(snapshot)
    if pending is not None and pending.get("source_frame", {}).get("episode_run_id") != snapshot.get("episode_run_id"):
        return {**plan, "war_mercenary_status": "prior_episode_pending_retained"}
    if not priority["defer_new_economic_construction"] and pending is None:
        return plan
    if pending is None:
        active_ids = {row["war_id"] for row in priority["wars"]}
        for prior in reversed(ledger["observed"]):
            if prior.get("status") == "native_rejected" and prior.get("source_frame") == frame:
                return {**plan, "war_mercenary_status": "native_rejection_observed_wait_new_frame_no_retry_loop"}
            if prior.get("status") != "employment_observed":
                continue
            chosen = prior.get("decision", {}).get("selected_candidate", {})
            if not active_ids.intersection(chosen.get("numerical_balance_reversed_war_ids", [])):
                continue
            old_ids = set(prior.get("pre_player_army_ids", []))
            new_force = [row for row in snapshot.get("player_armies", [])
                         if isinstance(row, Mapping) and row.get("army_id") not in old_ids
                         and row.get("current_province_id") == chosen.get("predicted_auto_raise_province_id")
                         and (new_count := observed_army_count([row], snapshot=snapshot, role="player")) is not None
                         and new_count > 0]
            if not new_force:
                return {**plan, "war_mercenary_status": "employment_observed_await_fresh_raised_inventory_no_duplicate_hire",
                        "war_mercenary_receipt": prior}
            break
    if QUERY_CAPABILITY not in bridge_capabilities:
        return {**plan, "war_mercenary_status": "native_query_capability_unavailable"}
    context = _context(history, snapshot)
    if pending is not None and (context is None or context.get("capture_epoch", 0) <= pending["pre_capture_epoch"]):
        context = None
    if context is None:
        if getattr(driver, "_war_mercenary_query_frame_v1", None) == frame:
            return {**plan, "war_mercenary_status": "query_unavailable_continue_war_no_same_frame_loop"}
        return {**plan, "selected_step": QUERY_STEP, "phase": "native_war_mercenary_query",
                "war_mercenary_deferred_step": step,
                "reason": "compare native mercenary reinforcement before spending cash on economic buildings"}
    if pending is not None:
        match = next((row for row in context["rows"] if row["company_id"] == pending["company_id"]), None)
        if match is not None and match.get("employer_id") == frame["played_character_id"]:
            employment = {**pending, "status": "employment_observed",
                          "observed_source_frame": frame, "capture_epoch": context["capture_epoch"],
                          "employer_character_id": match["employer_id"],
                          "army_creation_verified": False, "payment_verified": False}
            ledger["observed"].append(employment)
            ledger["pending"] = None
            write_json_atomic(directory / _LEDGER, ledger)
            return {**plan, "war_mercenary_receipt": employment,
                    "war_mercenary_status": "employment_independently_observed"}
        return {**plan, "war_mercenary_status": "pending_unresolved_never_resubmit",
                "war_mercenary_pending": pending}
    from .strategy import _same_frame_campaign_root_context
    from .activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1

    root = _same_frame_campaign_root_context(history, dict(snapshot))
    if root is None:
        if (ROOT_CAPABILITY in bridge_capabilities
                and getattr(driver, "_war_mercenary_root_query_frame_v1", None) != frame):
            return {**plan, "selected_step": ROOT_STEP, "phase": "native_war_mercenary_finance_query",
                    "reason": "read current income and maximum maintenance before choosing a defensive contract"}
        return {**plan, "war_mercenary_status": "same_frame_finance_unavailable_continue_existing_war"}
    spending = observe_feast_start_budget_v1(snapshot, {
        "actor_character_id": frame["played_character_id"], "snapshot_revision": frame["native_revision"],
        "date_raw": frame["date_raw"], "post_snapshot_id": frame["snapshot_id"],
        "queried_revision": frame["revision"]}, state_dir=directory, campaign_root=root)
    if spending.get("status") != "observed":
        return {**plan, "war_mercenary_status": "existing_spending_intent_or_frame_unavailable",
                "war_mercenary_spending_observation": spending}
    decision = assess_mercenary_reinforcement_v1(snapshot, context, campaign_root=root)
    plan = {**plan, "war_mercenary_decision_v1": decision}
    if decision["selected_company_id"] is None or HIRE_CAPABILITY not in bridge_capabilities:
        return plan
    if not callable(getattr(driver, "hire_mercenary_v1", None)):
        return {**plan, "war_mercenary_status": "typed_hire_executor_unavailable"}
    return {**plan, "selected_step": HIRE_STEP, "phase": "native_war_mercenary_hire",
            "war_mercenary_source_frame": frame, "war_mercenary_pre_capture_epoch": context["capture_epoch"],
            "war_mercenary_deferred_step": step,
            "reason": "hire the cheapest affordable company that reverses the observed local headcount deficit at friendly staging"}


def submit_war_mercenary_v1(driver: object, *, plan: Mapping[str, object], expected_revision: int):
    """Persist an unresolved claim before calling the existing typed native hire."""
    directory = getattr(driver, "state_dir", None)
    if not isinstance(directory, Path):
        raise ValueError("mercenary hire requires durable state")
    current = driver.take_snapshot()
    if (current.get("revision") != expected_revision
            or observed_frame(current) != plan.get("war_mercenary_source_frame")):
        raise ValueError("mercenary decision source frame is stale")
    decision = plan.get("war_mercenary_decision_v1")
    company = decision.get("selected_company_id") if isinstance(decision, Mapping) else None
    if type(company) is not int or decision.get("recommendation") != "hire_local_reinforcement":
        raise ValueError("mercenary hire lacks its selected reinforcement decision")
    ledger = _ledger(directory)
    if ledger["pending"] is not None:
        raise ValueError("unresolved mercenary hire must never be resubmitted")
    pending = {"action_request_id": uuid.uuid4().hex, "company_id": company,
               "source_frame": observed_frame(current), "status": "submission_unresolved",
               "pre_capture_epoch": plan["war_mercenary_pre_capture_epoch"],
               "pre_player_army_ids": [row["army_id"] for row in current.get("player_armies", [])
                                       if isinstance(row, Mapping) and type(row.get("army_id")) is int],
               "decision": dict(decision)}
    ledger["pending"] = pending
    write_json_atomic(directory / _LEDGER, ledger)
    # A pre-hire query must not suppress the independent post-hire query.
    driver._war_mercenary_query_frame_v1 = None
    result = driver.hire_mercenary_v1(company_id=company, expected_revision=expected_revision)
    pending["native_ack"] = result
    # A known rejected command can be reconsidered from new observations. Every
    # unavailable/lost result remains pending, without a duplicate submission.
    if result.get("status") == "rejected":
        pending["status"] = "native_rejected"
        ledger["observed"].append(pending)
        ledger["pending"] = None
    write_json_atomic(directory / _LEDGER, ledger)
    return {**result, "war_mercenary_pending": pending,
            "postcondition_verified": False, "payment_verified": False,
            "army_creation_verified": False}
