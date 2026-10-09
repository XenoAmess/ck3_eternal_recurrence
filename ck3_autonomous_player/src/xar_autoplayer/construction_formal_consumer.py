"""One controlled feudal construction action and its durable confirmation.

This is not a public capability.  A lost native reply is an unresolved action,
not permission to build again after a cold start.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import same_process_creation_time, write_json_atomic
from .bridge.declaration_contract import is_native_declaration_step
from .bridge.nonwar_private_build import private_native_build_identity
from .bridge.war_contract import parse_advance_route_contact_horizon_step
from .construction_economic_outcome_v1 import (
    completed_construction_cash_fields_v1, construction_economic_outcome_v1,
    prepare_construction_cash_fields_v1,
)
from .lifestyle_formal_consumer import ROOT_QUERY_STEP, _same_frame_feudal_scope


SUBMIT_STEP = "private-submit-player-construction-v1"
RECEIPT_STEP = "private-query-player-construction-receipt-v1"
_LEDGER = "construction-formal-pending-v1.json"
COMPLETION_WATCH_INTERVAL_RAW = 30 * 24  # 30 game days; date_raw is hourly.


def same_construction_process_identity(
    first: tuple[object, object], second: tuple[object, object],
) -> bool:
    """Compare the actual PID and creation instant while retaining raw evidence."""
    return first[0] == second[0] and (
        first[1] == second[1] or same_process_creation_time(first[1], second[1]))


def observe_construction_cash_before_quote(
    driver: object, *, expected_revision: int,
) -> dict[str, object] | None:
    """Read the existing authorized finance input before a native quote."""
    reader = getattr(driver, "query_construction_cash_outcome_private_v1", None)
    if not callable(reader):
        return None
    if getattr(driver, "allow_private_construction_formal_trial", False) is True:
        driver.allow_private_war_cash_query = True
    if getattr(driver, "allow_private_war_cash_query", False) is not True:
        return None
    from .bridge.domain_construction_private_transport_v1 import RESERVE_RAW
    from .bridge.driver import BridgeUnavailableError

    try:
        return reader(
            expected_revision=expected_revision, reserve_gold_raw=RESERVE_RAW,
            existing_commitment_gold_raw=0, horizon_months=1,
        )
    except BridgeUnavailableError as error:
        return {"status": "unavailable", "reason": str(error)}


def project_construction_quote_current_cash(
    query: Mapping[str, object], observation: Mapping[str, object] | None,
    *, wartime: bool = False,
) -> tuple[dict[str, object], str | None]:
    """Project only this new quote using the one pre-quote cash packet."""
    quoted = dict(query)
    if observation is None:
        return quoted, ("current native cash is unavailable for this wartime spend"
                        if wartime else None)
    budget = observation.get("current_cash_scenarios")
    packet = budget.get("source_cash_resources") if isinstance(budget, Mapping) else None
    candidate = quoted["candidate"]
    treasury = packet.get("current_treasury") if isinstance(packet, Mapping) else None
    if (not isinstance(treasury, Mapping)
            or treasury.get("raw") != candidate.get("gold_before_raw")):
        return quoted, "current cash and native construction quote are not jointly observed"
    source = quoted.get("source_frame")
    if wartime and not (isinstance(source, Mapping)
            and packet.get("played_character_id") == source.get("actor_character_id")
            and packet.get("snapshot_revision") == source.get("native_revision")
            and packet.get("date_raw") == source.get("date_raw")):
        return quoted, "wartime cash and construction quote belong to different actor frames"
    fields = prepare_construction_cash_fields_v1(
        candidate, packet, reserve_gold_raw=budget["reserve_gold_raw"],
        existing_commitment_gold_raw=0, horizon_months=1,
    )
    quoted.update(fields)
    if fields["construction_monthly_budget"]["scenarios"]["current"]["scenario_floor_ready"] is not True:
        return quoted, "defer this quote because current one-month cash does not retain the reserve"
    if (wartime and fields["construction_monthly_budget"]["scenarios"]
            ["all_raised"]["scenario_floor_ready"] is not True):
        return quoted, "defer this quote because all-raised one-month cash does not retain the reserve"
    return quoted, None


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
        if (not same_construction_process_identity(process, (
                row.get("post_bridge_pid"), row.get("post_bridge_creation_date")))
                or (type(revision) is int and type(row.get("post_native_revision")) is int
                    and revision < row["post_native_revision"])
                or (type(date) is int and type(row.get("post_date_raw")) is int
                    and date < row["post_date_raw"])):
            return row
    for row in receipts:
        if (row.get("completion_status") == "completed"
                and (row.get("observed_player_monthly_gold_income_raw") is None
                     or not isinstance(row.get("post_cash_v2"), Mapping))):
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
    quiet_route_advance = (
        plan.get("phase") == "native_war_route_contact_horizon_progress"
        and parse_advance_route_contact_horizon_step(original_step) is not None
    )
    new_action_admitted = original_step == "life-advance" or prewar or quiet_route_advance
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
    cash_observation = None
    cash_loaded = False

    def current_cash():
        nonlocal cash_observation, cash_loaded
        if cash_loaded:
            return cash_observation
        cash_loaded = True
        cash_observation = observe_construction_cash_before_quote(
            driver, expected_revision=int(planned["revision"]),
        )
        return cash_observation

    pending = ledger["pending"]
    if isinstance(pending, dict):
        if pending.get("episode_run_id") != episode:
            return {**planned, "plan": {**plan, "selected_step": None,
                                        "reason": "unresolved construction belongs to another episode"}}
        from .bridge.domain_construction_private_transport_v1 import _identity

        pid, creation = _identity(driver)
        cold_process = not same_construction_process_identity((pid, creation), (
            pending.get("source_bridge_pid"),
            pending.get("source_bridge_creation_date"),
        ))
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
        if (not same_construction_process_identity(process_identity, (
                applied.get("post_bridge_pid"), applied.get("post_bridge_creation_date")))
                or older_frame):
            return {**planned, "plan": {**plan,
                "phase": "construction_cold_applied_requery",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(applied),
                "reason": "cold restore may load an earlier checkpoint; verify construction before using ledger"}}
        plan = {**plan, "construction_receipt_consumed": dict(applied),
                "construction_economic_outcome": construction_economic_outcome_v1(
                    applied, exact_ck3_build=private_native_build_identity(
                        snapshot).game_version)}
        if (applied.get("completion_status") == "completed"
                and (applied.get("observed_player_monthly_gold_income_raw") is None
                     or not isinstance(applied.get("post_cash_v2"), Mapping))):
            observed = current_cash()
            budget = observed.get("current_cash_scenarios") if isinstance(observed, Mapping) else None
            packet = budget.get("source_cash_resources") if isinstance(budget, Mapping) else None
            gross = packet.get("player_monthly_gross_income") if isinstance(packet, Mapping) else None
            if (isinstance(gross, Mapping) and type(gross.get("raw")) is int
                    and packet["readiness"].get("monthly_gross_income_ready") is True):
                completed_receipt = dict(applied)
                if completed_receipt.get("observed_player_monthly_gold_income_raw") is None:
                    completed_receipt.update(
                        observed_player_monthly_gold_income_raw=gross["raw"],
                        income_observed_date_raw=packet["date_raw"],
                    )
                fields = completed_construction_cash_fields_v1(
                    completed_receipt, packet,
                    exact_ck3_build=budget["game_version"],
                )
                applied = fields["receipt"]
                if ledger["applied"] is not None and (
                        ledger["applied"].get("action_request_id") == applied.get("action_request_id")):
                    ledger = {**ledger, "applied": applied}
                else:
                    ledger = {**ledger, "applied_prior": [
                        applied if row.get("action_request_id") == applied.get("action_request_id")
                        else row for row in ledger["applied_prior"]]}
                write_construction_ledger(state_dir, ledger)
                priority_applied = priority_construction_receipt(
                    driver, ledger, snapshot, process_identity=process_identity)
                plan = {**plan, "construction_receipt_consumed": applied,
                        "construction_economic_outcome": fields["construction_economic_outcome"],
                        "construction_cash_outcome": observed}
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
    # Keep selected war work ahead of a new spend. Otherwise the ordinary
    # advance opportunity can use observed current/all-raised cash during war.
    wars = snapshot.get("active_wars")
    if (isinstance(wars, list) and wars
            and not new_action_admitted
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
    # A qualified quiet route clock is also an otherwise selected advance.
    # Only an otherwise selected advance or existing prewar opportunity
    # admits a new expenditure; an active war itself is not a spending ban.
    if not new_action_admitted:
        return {**planned, "plan": plan}
    scope = _same_frame_feudal_scope(snapshot, history, require_peace=False)
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

    observed = current_cash()
    if observed is not None:
        plan = {**plan, "construction_cash_outcome": observed}
    query = query_construction_private(driver, expected_revision=int(planned["revision"]))
    if query.get("status") == "no_legal_budgeted_building":
        if prewar:
            return prewar_unchanged("no_positive_budgeted_building", query=query)
        return {**planned, "plan": {**plan, "construction_private_query": query}}
    if query.get("status") == "evidence_insufficient":
        # Missing coverage defers this optional new spend, not the selected
        # ordinary action. Keep the native query RED without starving its clock.
        if prewar:
            return prewar_unchanged("positive_income_coverage_incomplete",
                                   query=query)
        return {**planned, "plan": {**plan, "construction_private_query": query}}
    if query.get("status") != "selected":
        if prewar:
            return prewar_unchanged("construction_source_red", query=query)
        return {**planned, "plan": {**plan, "selected_step": None,
            "construction_private_query": query,
            "reason": "private construction source unavailable; preserve RED"}}
    wartime = isinstance(wars, list) and bool(wars)
    if observed is not None or wartime:
        query, cash_reason = project_construction_quote_current_cash(
            query, observed, wartime=wartime,
        )
        if "construction_monthly_budget" in query:
            plan = {**plan, "construction_monthly_budget": query["construction_monthly_budget"]}
        if cash_reason is not None:
            return {**planned, "plan": {**plan, "construction_private_query": query,
                "phase": "construction_cash_budget_deferred",
                "reason": cash_reason}}
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
        "phase": ("construction_wartime_typed_submit" if wartime
                  else "construction_typed_submit"), "selected_step": SUBMIT_STEP,
        "construction_private_query": query,
        "reason": "submit one native-legal budgeted construction"}}
