"""One controlled feudal construction action and its durable confirmation.

This is not a public capability.  A lost native reply is an unresolved action,
not permission to build again after a cold start.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import write_json_atomic
from .bridge.declaration_contract import is_native_declaration_step
from .lifestyle_formal_consumer import ROOT_QUERY_STEP, same_frame_feudal_peace_scope


SUBMIT_STEP = "private-submit-player-construction-v1"
RECEIPT_STEP = "private-query-player-construction-receipt-v1"
_LEDGER = "construction-formal-pending-v1.json"
COMPLETION_WATCH_INTERVAL_RAW = 30 * 24  # 30 game days; date_raw is hourly.


def same_frame_construction_income(
    snapshot: Mapping[str, object], history: list[dict[str, object]],
) -> tuple[bool, int | None]:
    """Return an observed public root row and its actual player income raw."""
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    for row in reversed(history):
        if row.get("command") != ROOT_QUERY_STEP or row.get("ok") is not True:
            continue
        result = row.get("result")
        root = result.get("campaign_root_context") if isinstance(result, Mapping) else None
        if not (isinstance(root, Mapping) and root.get("status") == "available"
                and root.get("snapshot_revision") == snapshot.get("native_revision")
                and root.get("date_raw") == snapshot.get("date_raw")
                and root.get("player_character_id") == actor):
            continue
        income = root.get("player_monthly_gold_income")
        raw = income.get("raw") if isinstance(income, Mapping) else None
        return True, raw if type(raw) is int and income.get("scale") == 100_000 else None
    return False, None


def read_construction_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.exists():
        return {"schema": "xar.ck3.construction_formal_pending_v1", "pending": None,
                "applied": None}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict)
            or record.get("schema") != "xar.ck3.construction_formal_pending_v1"
            or not all(key in record for key in ("pending", "applied"))
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "applied"))):
        raise ValueError("construction pending ledger shape is unknown")
    return record


def write_construction_ledger(state_dir: Path, record: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(record))


def plan_construction_private(
    driver: object, planned: dict[str, object], snapshot: Mapping[str, object],
    history: list[dict[str, object]], available_steps: set[str],
    *, prewar_arbitration: bool = False,
) -> dict[str, object]:
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    original_step = plan.get("selected_step")
    prewar = prewar_arbitration is True and is_native_declaration_step(original_step)
    if original_step != "life-advance" and not prewar:
        return planned

    def prewar_unchanged(status: str, *, query: object = None) -> dict[str, object]:
        observation = {"status": status, "original_selected_step": original_step,
                       "war_future_gold_cost_raw": None,
                       "additional_shared_gold_commitment_raw": None}
        next_plan = {**plan, "construction_prewar_arbitration": observation}
        if query is not None:
            next_plan["construction_private_query"] = query
        return {**planned, "plan": next_plan}

    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        if prewar:
            return prewar_unchanged("durable_state_unavailable")
        return {**planned, "plan": {**plan, "selected_step": None,
                                    "reason": "construction trial lacks durable state_dir"}}
    ledger = read_construction_ledger(state_dir)
    episode = snapshot.get("episode_run_id")
    pending = ledger["pending"]
    if isinstance(pending, dict):
        if pending.get("episode_run_id") != episode:
            return {**planned, "plan": {**plan, "selected_step": None,
                                        "reason": "unresolved construction belongs to another episode"}}
        from .bridge.domain_construction_private_transport_v1 import _identity

        pid, creation = _identity(driver)
        cold_process = (pid, creation) != (
            pending.get("source_bridge_pid"),
            pending.get("source_bridge_creation_date"),
        )
        if (cold_process or (type(snapshot.get("native_revision")) is int
                             and snapshot["native_revision"] > pending.get("pre_native_revision", 0))):
            return {**planned, "plan": {**plan,
                "phase": "construction_pending_receipt",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(pending),
                "reason": "query independent paused construction state before another action"}}
        if prewar:
            return {**planned, "plan": {**plan,
                "selected_step": None,
                "construction_pending_action": dict(pending),
                "construction_prewar_arbitration": {
                    "status": "pending_action_needs_later_receipt",
                    "original_selected_step": original_step,
                    "war_future_gold_cost_raw": None,
                    "additional_shared_gold_commitment_raw": None},
                "reason": "construction action state unknown; do not spend competing resources"}}
        return {**planned, "plan": {**plan,
            "construction_pending_action": dict(pending),
            "reason": "advance to independent native frame; never resubmit pending construction"}}
    applied = ledger["applied"]
    if isinstance(applied, dict) and applied.get("episode_run_id") == episode:
        from .bridge.domain_construction_private_transport_v1 import _identity

        if _identity(driver) != (applied.get("post_bridge_pid"),
                                 applied.get("post_bridge_creation_date")):
            return {**planned, "plan": {**plan,
                "phase": "construction_cold_applied_requery",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(applied),
                "reason": "cold restore may load an earlier checkpoint; verify construction before using ledger"}}
        plan = {**plan, "construction_receipt_consumed": dict(applied)}
        if (applied.get("completion_status") == "completed"
                and applied.get("observed_player_monthly_gold_income_raw") is None):
            income_observed, actual_income = same_frame_construction_income(
                snapshot, history)
            if actual_income is None:
                if not income_observed and ROOT_QUERY_STEP in available_steps:
                    return {**planned, "plan": {**plan,
                        "phase": "construction_completed_income_query",
                        "selected_step": ROOT_QUERY_STEP,
                        "reason": "read actual player income after independently verified completion"}}
            else:
                return {**planned, "plan": {**plan,
                    "phase": "construction_completed_income_receipt",
                    "selected_step": RECEIPT_STEP,
                    "construction_pending_action": dict(applied),
                    "reason": "bind same-frame actual income to completed native building"}}
        last_completion_check = applied.get(
            "completion_last_check_date_raw", applied.get("post_date_raw"))
        if (applied.get("completion_status") != "completed"
                and type(snapshot.get("date_raw")) is int
                and type(last_completion_check) is int
                and snapshot["date_raw"] >= (
                    last_completion_check + COMPLETION_WATCH_INTERVAL_RAW)):
            income_observed, _ = same_frame_construction_income(snapshot, history)
            if not income_observed and ROOT_QUERY_STEP in available_steps:
                return {**planned, "plan": {**plan,
                    "phase": "construction_completion_income_query",
                    "selected_step": ROOT_QUERY_STEP,
                    "reason": "read same-frame actual player income before completed slot"}}
            return {**planned, "plan": {**plan,
                "phase": "construction_completion_watch",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(applied),
                "reason": "read completed native building slot on a later monthly frame"}}
        # The receipt is consumed on the following formal turn.  A later
        # game day can present another legal province after that turn.
        if not (type(snapshot.get("native_revision")) is int
                and type(snapshot.get("date_raw")) is int
                and type(applied.get("post_native_revision")) is int
                and type(applied.get("post_date_raw")) is int
                and snapshot["native_revision"] > applied["post_native_revision"]
                and snapshot["date_raw"] > applied["post_date_raw"]):
            return {**planned, "plan": plan}
    scope = same_frame_feudal_peace_scope(snapshot, history)
    if scope["status"] == "root_query_needed":
        if ROOT_QUERY_STEP not in available_steps:
            if prewar:
                return prewar_unchanged("feudal_root_query_unavailable")
            return {**planned, "plan": {**plan, "selected_step": None,
                "reason": "construction trial needs same-frame public feudal root query"}}
        return {**planned, "plan": {**plan, "selected_step": ROOT_QUERY_STEP,
            "phase": "construction_feudal_scope_query",
            **({"construction_prewar_arbitration": {
                "status": "root_query_needed",
                "original_selected_step": original_step,
                "war_future_gold_cost_raw": None,
                "additional_shared_gold_commitment_raw": None}}
               if prewar else {})}}
    if scope["status"] != "admitted":
        if prewar:
            return prewar_unchanged(f"scope_{scope['status']}")
        return planned
    from .bridge.domain_construction_private_transport_v1 import query_construction_private

    query = query_construction_private(driver, expected_revision=int(planned["revision"]))
    if query.get("status") == "no_legal_budgeted_building":
        if prewar:
            return prewar_unchanged("no_positive_budgeted_building", query=query)
        return {**planned, "plan": {**plan, "construction_private_query": query}}
    if query.get("status") == "evidence_insufficient":
        if prewar:
            observed = prewar_unchanged("positive_income_coverage_incomplete",
                                        query=query)
            return {**observed, "plan": {**observed["plan"],
                "selected_step": None,
                "reason": "construction positive-income coverage incomplete; preserve RED"}}
        return {**planned, "plan": {**plan, "selected_step": None,
            "construction_private_query": query,
            "reason": "construction positive-income coverage incomplete; preserve RED"}}
    if query.get("status") != "selected":
        if prewar:
            return prewar_unchanged("construction_source_red", query=query)
        return {**planned, "plan": {**plan, "selected_step": None,
            "construction_private_query": query,
            "reason": "private construction source unavailable; preserve RED"}}
    if prewar:
        candidate = query.get("candidate")
        gold = snapshot.get("played_character_gold")
        observed_gold = gold.get("raw") if isinstance(gold, Mapping) else None
        if not (isinstance(candidate, Mapping)
                and type(candidate.get("authored_monthly_income_hundredths")) is int
                and candidate["authored_monthly_income_hundredths"] > 0
                and type(observed_gold) is int and observed_gold >= 0
                and gold.get("scale") == 100_000
                and candidate.get("gold_before_raw") == observed_gold):
            return prewar_unchanged("same_frame_cash_or_positive_value_unavailable",
                                    query=query)
        from .bridge.domain_construction_private_transport_v1 import RESERVE_RAW

        cost = candidate["stock_gold_cost_raw"]
        if (type(cost) is not int or cost <= 0
                or observed_gold - cost < RESERVE_RAW):
            return prewar_unchanged("native_budget_not_available", query=query)
        return {**planned, "plan": {**plan,
            "phase": "construction_prewar_typed_submit",
            "selected_step": SUBMIT_STEP,
            "construction_private_query": query,
            "construction_prewar_arbitration": {
                "status": "selected_positive_budgeted_building",
                "original_selected_step": original_step,
                "observed_player_gold_raw": observed_gold,
                "construction_gold_cost_raw": cost,
                "construction_minimum_gold_reserve_raw": RESERVE_RAW,
                "gold_after_construction_raw": observed_gold - cost,
                "authored_monthly_income_hundredths":
                    candidate["authored_monthly_income_hundredths"],
                "war_future_gold_cost_raw": None,
                "additional_shared_gold_commitment_raw": None},
            "reason": "construct one same-frame native-legal positive-income building before war entry"}}
    return {**planned, "plan": {**plan,
        "phase": "construction_typed_submit", "selected_step": SUBMIT_STEP,
        "construction_private_query": query,
        "reason": "submit one native-legal budgeted construction"}}
