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
                "applied": None, "applied_prior": []}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict)
            or record.get("schema") != "xar.ck3.construction_formal_pending_v1"
            or not all(key in record for key in ("pending", "applied"))
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "applied"))
            or not isinstance(record.get("applied_prior", []), list)
            or any(not isinstance(row, dict)
                   for row in record.get("applied_prior", []))):
        raise ValueError("construction pending ledger shape is unknown")
    record.setdefault("applied_prior", [])
    receipts = [*record["applied_prior"]]
    if record["applied"] is not None:
        receipts.append(record["applied"])
    request_ids = [row.get("action_request_id") for row in receipts]
    if (len(receipts) > 1
            and (any(not isinstance(request_id, str) or not request_id
                     for request_id in request_ids)
                 or len(request_ids) != len(set(request_ids)))):
        raise ValueError("construction applied receipt identity is unknown")
    return record


def write_construction_ledger(state_dir: Path, record: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(record))


def applied_construction_receipts(
    ledger: Mapping[str, object], episode_run_id: object,
) -> list[dict[str, object]]:
    """Oldest first, including the newest legacy-compatible applied receipt."""
    prior = ledger.get("applied_prior", [])
    receipts = [*prior] if isinstance(prior, list) else []
    applied = ledger.get("applied")
    if isinstance(applied, dict):
        receipts.append(applied)
    return [row for row in receipts if isinstance(row, dict)
            and row.get("episode_run_id") == episode_run_id]


def priority_construction_receipt(
    driver: object, ledger: Mapping[str, object], snapshot: Mapping[str, object],
    *, process_identity: tuple[int, str] | None = None,
) -> dict[str, object] | None:
    """Choose one old material follow-up before considering a new expenditure."""
    receipts = applied_construction_receipts(
        ledger, snapshot.get("episode_run_id"))
    if not receipts:
        return None
    from .bridge.domain_construction_private_transport_v1 import _identity

    process = process_identity if process_identity is not None else _identity(driver)
    revision = snapshot.get("native_revision")
    date = snapshot.get("date_raw")
    for row in receipts:
        if (process != (row.get("post_bridge_pid"),
                        row.get("post_bridge_creation_date"))
                or (type(revision) is int and type(row.get("post_native_revision")) is int
                    and revision < row["post_native_revision"])
                or (type(date) is int and type(row.get("post_date_raw")) is int
                    and date < row["post_date_raw"])):
            return row
    for row in receipts:
        if (row.get("completion_status") == "completed"
                and row.get("observed_player_monthly_gold_income_raw") is None):
            return row
    for row in receipts:
        province = row.get("construction_province_income_observation")
        last_check = row.get("completion_last_check_date_raw",
                             row.get("post_date_raw"))
        if (row.get("completion_status") == "completed"
                and (not isinstance(province, Mapping)
                     or province.get("status") != "observed")
                and type(date) is int and type(last_check) is int
                and date >= last_check + COMPLETION_WATCH_INTERVAL_RAW):
            return row
    for row in receipts:
        last_check = row.get("completion_last_check_date_raw",
                             row.get("post_date_raw"))
        if (row.get("completion_status") != "completed"
                and type(date) is int and type(last_check) is int
                and date >= last_check + COMPLETION_WATCH_INTERVAL_RAW):
            return row
    return None


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
    new_action_admitted = original_step == "life-advance" or prewar
    if (not new_action_admitted
            and (snapshot.get("paused") is not True
                 or snapshot.get("map_ready") is not True
                 or snapshot.get("active_event") is not None
                 or snapshot.get("pending_character_interaction") is not None)):
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
        if not new_action_admitted:
            return planned
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
    receipts = applied_construction_receipts(ledger, episode)
    process_identity = None
    if receipts:
        from .bridge.domain_construction_private_transport_v1 import _identity
        process_identity = _identity(driver)
    priority_applied = priority_construction_receipt(
        driver, ledger, snapshot, process_identity=process_identity)
    applied = priority_applied or ledger["applied"]
    if isinstance(applied, dict) and applied.get("episode_run_id") == episode:
        older_frame = (
            (type(snapshot.get("native_revision")) is int
             and type(applied.get("post_native_revision")) is int
             and snapshot["native_revision"] < applied["post_native_revision"])
            or (type(snapshot.get("date_raw")) is int
                and type(applied.get("post_date_raw")) is int
                and snapshot["date_raw"] < applied["post_date_raw"])
        )
        if (process_identity != (applied.get("post_bridge_pid"),
                                 applied.get("post_bridge_creation_date"))
                or older_frame):
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
            if priority_applied is not None:
                return {**planned, "plan": {**plan,
                    "selected_step": None,
                    "reason": "completed construction income remains unavailable"}}
        last_completion_check = applied.get(
            "completion_last_check_date_raw", applied.get("post_date_raw"))
        province = applied.get("construction_province_income_observation")
        if (applied.get("completion_status") == "completed"
                and (not isinstance(province, Mapping)
                     or province.get("status") != "observed")
                and type(snapshot.get("date_raw")) is int
                and type(last_completion_check) is int
                and snapshot["date_raw"] >= (
                    last_completion_check + COMPLETION_WATCH_INTERVAL_RAW)):
            return {**planned, "plan": {**plan,
                "phase": "construction_completed_province_income_watch",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(applied),
                "reason": "retry target province aggregate after completed-slot proof"}}
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
        if priority_applied is not None:
            return {**planned, "plan": plan}
        # The receipt is consumed on the following formal turn.  A later
        # game day can present another legal province after that turn.
        newest = ledger["applied"]
        if isinstance(newest, dict) and not (
                type(snapshot.get("native_revision")) is int
                and type(snapshot.get("date_raw")) is int
                and type(newest.get("post_native_revision")) is int
                and type(newest.get("post_date_raw")) is int
                and snapshot["native_revision"] > newest["post_native_revision"]
                and snapshot["date_raw"] > newest["post_date_raw"]):
            return {**planned, "plan": plan}
    # A pre-existing construction needs its material/income readback even
    # while the ordinary strategy is busy with war. Native building choices
    # can be observed during war, but an unassessed war cash commitment never
    # admits a new spend or replaces the already selected formal action.
    wars = snapshot.get("active_wars")
    if (isinstance(wars, list) and wars
            and (original_step is not None or getattr(
                driver, "allow_private_m5_joint_collector", False) is True)):
        binding = (snapshot.get("episode_run_id"), snapshot.get("snapshot_id"),
                   snapshot.get("revision"), snapshot.get("date_raw"),
                   snapshot.get("played_character", {}).get("character_id")
                   if isinstance(snapshot.get("played_character"), Mapping) else None)
        cached = getattr(driver, "_construction_wartime_observation_cache", None)
        if isinstance(cached, tuple) and len(cached) == 2 and cached[0] == binding:
            observation = cached[1]
        else:
            from .bridge.domain_construction_private_transport_v1 import (
                query_construction_wartime_observation_private,
            )
            from .bridge.driver import BridgeUnavailableError

            try:
                observation = query_construction_wartime_observation_private(
                    driver, expected_revision=int(planned["revision"]))
            except BridgeUnavailableError as error:
                observation = {
                    "status": "source_red", "read_only": True,
                    "advertised": False, "formal_action_ready": False,
                    "candidate": None,
                    "existing_shared_gold_commitment_raw": None,
                    "war_future_gold_cost_raw": None,
                    "joint_budget_affordability": "unassessed",
                    "reason": str(error),
                }
            setattr(driver, "_construction_wartime_observation_cache",
                    (binding, observation))
        return {**planned, "plan": {**plan,
            "construction_wartime_observation": observation}}
    # Only a new expenditure remains limited to the life-advance or
    # peaceful prewar opportunity.
    if not new_action_admitted:
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
