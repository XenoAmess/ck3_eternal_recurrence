"""Use current native hire terms for one measured, blocked player siege."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .bridge.player_holy_order_context_private_transport import normalize_player_holy_order_context_v1
from .bridge.war_contract import HIRE_HOLY_ORDER_V1_CAPABILITY, HIRE_HOLY_ORDER_V1_STEP, preview_move_army_step

SCHEMA = "xar.ck3.holy-order-siege-reinforcement-proposal.v1"
_STOCKS = {0: "gold", 1: "prestige", 2: "piety"}


def _frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    actor = snapshot.get("played_character")
    return {"snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"), "date_raw": snapshot.get("date_raw"),
            "played_character_id": actor.get("character_id") if isinstance(actor, Mapping) else None}


def _stocks(snapshot: Mapping[str, object]) -> dict[str, int | None]:
    result = {}
    for name in _STOCKS.values():
        value = snapshot.get("played_character_" + name)
        result[name] = (value["raw"] if isinstance(value, Mapping) and type(value.get("raw")) is int
                        and value.get("scale") == 100000 else None)
    return result


def _siege_need(snapshot: Mapping[str, object], plan: Mapping[str, object]) -> dict[str, int] | None:
    # This is the existing blocked-siege alternative. Other selected actions
    # retain their existing priority, including retreat and move commands.
    if plan.get("phase") != "native_war_siege_exit_blocked" or plan.get("selected_step") is not None:
        return None
    actor = snapshot.get("played_character")
    siege, pursuit = plan.get("siege_state"), plan.get("pursuit")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not isinstance(siege, Mapping) or not isinstance(pursuit, Mapping)
            or siege.get("status") != "insufficient_strength" or siege.get("player_army_besieging") is not True):
        return None
    war, province, garrison, strength = (pursuit.get("war_id"), siege.get("province_id"),
                                        siege.get("garrison_size"), siege.get("besieging_strength"))
    wars = snapshot.get("active_wars")
    if (any(type(value) is not int for value in (war, province, garrison, strength))
            or war <= 0 or province <= 0 or not 0 <= strength < garrison
            or not isinstance(wars, list)
            or not any(isinstance(row, Mapping) and row.get("war_id") == war for row in wars)):
        return None
    return {"war_id": war, "target_province_id": province, "garrison_size": garrison,
            "besieging_strength": strength, "additional_soldiers_required": garrison - strength}


def choose_holy_order_siege_reinforcement_v1(
    *, snapshot: Mapping[str, object], plan: Mapping[str, object], holy_context: object,
) -> dict[str, object]:
    """Return a bounded proposal, preserving final native permission and price."""
    need = _siege_need(snapshot, plan)
    out = {"schema": SCHEMA, "status": "not_applicable", "source_frame": _frame(snapshot),
           "military_need": need, "selected_step": None, "candidate_rows": []}
    if need is None:
        return out
    context = normalize_player_holy_order_context_v1(holy_context, snapshot=snapshot)
    if (context.get("queried_revision") != snapshot.get("revision")
            or context.get("queried_native_revision") != snapshot.get("native_revision")):
        raise ValueError("holy-order proposal differs from its actual queried frame")
    stocks = _stocks(snapshot)
    out.update(status="no_eligible_reinforcement", before_resource_stocks_raw=stocks)
    if context["available"] is not True:
        out.update(status="input_unavailable", unavailable_reason=context["unavailable_reason"])
        return out
    eligible = []
    for source_ordinal, row in enumerate(context["rows"]):
        if row["is_military"] is not True:
            continue
        terms = row["military_terms"]
        strength = terms.get("troop_strength")
        evaluation = {"holy_order_id": row["holy_order_id"], "source_ordinal": source_ordinal,
                      "can_hire": terms.get("can_hire"), "can_afford": terms.get("can_afford"),
                      "can_hire_reason_literal": terms.get("can_hire_reason_literal"),
                      "can_afford_reason_literal": terms.get("can_afford_reason_literal")}
        reason = None
        if row.get("employer_id") == context["played_character_id"]:
            reason = "already_employed_by_player"
        elif terms["available"] is not True:
            reason = terms["unavailable_reason"]
        elif terms["can_hire"] is not True:
            reason = "native_can_hire_false"
        elif terms["can_afford"] is not True:
            reason = "native_can_afford_false"
        elif not isinstance(strength, Mapping) or strength.get("available") is not True:
            reason = "current_soldiers_unavailable"
        elif strength["current_soldiers"] < need["additional_soldiers_required"]:
            reason = "current_troops_do_not_cover_measured_deficit"
        else:
            costs = terms["resource_costs_raw"]
            for slot, name in _STOCKS.items():
                if stocks[name] is None:
                    reason = "current_" + name + "_stock_unavailable"
                    break
                if costs[slot] > 0 and costs[slot] > stocks[name]:
                    reason = "quoted_" + name + "_exceeds_current_stock"
                    break
            if reason is None:
                candidate = {"holy_order_id": row["holy_order_id"], "source_ordinal": source_ordinal,
                             "prior_employer_id": row.get("employer_id"),
                             "native_quote_raw": list(costs), "current_soldiers": strength["current_soldiers"]}
                eligible.append(candidate)
        evaluation.update(status="eligible" if reason is None else "not_selected", reason=reason)
        out["candidate_rows"].append(evaluation)
    if eligible:
        # Native resources are not summed into an invented common currency.
        # This is our narrow deterministic choice, not an original-AI score.
        selected = min(eligible, key=lambda row: (row["native_quote_raw"][2], row["native_quote_raw"][0],
                                                  row["native_quote_raw"][1], row["holy_order_id"], row["source_ordinal"]))
        out.update(selected, status="actionable", selected_step=HIRE_HOLY_ORDER_V1_STEP,
                   ranking_policy="lowest_native_piety_then_gold_prestige_full_id",
                   original_ai_ranking_observed=False)
    return out


def plan_holy_order_siege_reinforcement_v1(
    driver: object, *, planned: dict[str, object], snapshot: Mapping[str, object],
    bridge_capabilities: list[str],
) -> dict[str, object]:
    plan = planned.get("plan")
    if not isinstance(plan, Mapping) or _siege_need(snapshot, plan) is None:
        return planned
    read = getattr(driver, "query_player_holy_order_context_private_v1", None)
    if HIRE_HOLY_ORDER_V1_CAPABILITY not in bridge_capabilities or not callable(read):
        return planned
    try:
        context = read(expected_revision=planned["revision"])
        proposal = choose_holy_order_siege_reinforcement_v1(snapshot=snapshot, plan=plan, holy_context=context)
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        return {**planned, "plan": {**plan, "holy_order_reinforcement_observation": {
            "status": "input_unavailable", "reason": str(error)}}}
    if proposal["status"] != "actionable":
        return {**planned, "plan": {**plan, "holy_order_reinforcement_observation": proposal}}
    return {**planned, "plan": {**plan, "phase": "native_war_holy_order_siege_reinforcement",
        "selected_step": HIRE_HOLY_ORDER_V1_STEP,
        "reason": "current native legal order troops cover the observed blocked-siege deficit",
        "holy_order_hire_proposal": proposal,
        "deferred_siege_plan": deepcopy(dict(plan))}}


def submit_holy_order_siege_reinforcement_v1(
    driver: object, *, plan: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    proposal = plan.get("holy_order_hire_proposal")
    if not isinstance(proposal, Mapping) or proposal.get("status") != "actionable":
        raise UnsupportedStepError("holy-order reinforcement lacks its valued current native proposal")
    ack = driver.hire_holy_order_v1(holy_order_id=proposal["holy_order_id"], expected_revision=expected_revision)
    receipt = {"schema": "xar.ck3.holy-order-siege-reinforcement-postcondition.v1",
               "status": "verification_pending", "holy_order_id": proposal["holy_order_id"],
               "employer_observed": False, "usable_army_observed": False,
               "material_armies": [], "next_formal": None,
               "quote_raw": list(proposal["native_quote_raw"]),
               "before_resource_stocks_raw": dict(proposal["before_resource_stocks_raw"]),
               "after_resource_stocks_raw": None, "observed_stock_delta_raw": None,
               "unchanged_date_quote_delta_match": None, "actor_expenses": None,
               "expense_query_error": None, "source": "independent_current_queries",
               "full_hire_loop_complete": False}
    if ack.get("accepted") is not True:
        receipt["status"] = "not_submitted"
        return {**ack, "holy_order_reinforcement_postcondition": receipt}
    try:
        after = driver.take_snapshot()
        context = driver.query_player_holy_order_context_private_v1(expected_revision=after["revision"])
        context = normalize_player_holy_order_context_v1(context, snapshot=after)
        rows = [row for row in context["rows"] if row["holy_order_id"] == proposal["holy_order_id"]]
        actor = after.get("played_character")
        employer = (rows[0].get("employer_id") if len(rows) == 1 else None)
        receipt.update(after_source_frame=_frame(after), actual_employer_id=employer,
                       employer_observed=isinstance(actor, Mapping) and employer == actor.get("character_id"),
                       after_resource_stocks_raw=_stocks(after))
        before_stocks, after_stocks = receipt["before_resource_stocks_raw"], receipt["after_resource_stocks_raw"]
        deltas = {name: before_stocks[name] - after_stocks[name]
                  if type(before_stocks[name]) is int and type(after_stocks[name]) is int else None
                  for name in _STOCKS.values()}
        receipt["observed_stock_delta_raw"] = deltas
        if after.get("date_raw") == proposal["source_frame"]["date_raw"]:
            supported = all(value == 0 for slot, value in enumerate(proposal["native_quote_raw"]) if slot not in _STOCKS)
            if supported and all(type(value) is int for value in deltas.values()):
                receipt["unchanged_date_quote_delta_match"] = all(
                    deltas[name] == proposal["native_quote_raw"][slot] for slot, name in _STOCKS.items())
        if receipt["employer_observed"]:
            association = rows[0]["military_terms"].get("troop_association")
            receipt["troop_association"] = deepcopy(association)
            refs = {member["native_carmy_id"] for member in association.get("rows", [])
                    if member.get("available") is True and member.get("native_carmy_resolved") is True} if isinstance(association, Mapping) else set()
            public = {row["army_id"]: row for row in after.get("player_armies", []) if isinstance(row, Mapping)}
            if refs and public:
                strengths = driver.query_army_strengths(army_ids=list(public), expected_revision=after["revision"])
                for row in strengths.get("army_strengths", []):
                    army = public.get(row.get("army_id"))
                    if (row.get("status") == "available" and row.get("native_carmy_id") in refs
                            and isinstance(army, Mapping) and army.get("controllable") is True
                            and type(row.get("current_soldiers")) is int and row["current_soldiers"] > 0):
                        receipt["material_armies"].append({"army_id": army["army_id"],
                            "native_carmy_id": row["native_carmy_id"], "current_soldiers": row["current_soldiers"],
                            "owner_character_id": army.get("owner_character_id"),
                            "controllable": True, "current_province_id": army.get("current_province_id")})
                receipt["usable_army_observed"] = bool(receipt["material_armies"])
        cash = getattr(driver, "query_war_cash_current_resources_private_v1", None)
        if callable(cash):
            try:
                receipt["actor_expenses"] = cash(expected_revision=after["revision"])
            except (BridgeUnavailableError, UnsupportedStepError) as error:
                receipt["expense_query_error"] = str(error)
        if receipt["usable_army_observed"]:
            selected = max(receipt["material_armies"], key=lambda row: (row["current_soldiers"], -row["army_id"]))
            target = proposal["military_need"]["target_province_id"]
            receipt.update(status="employer_and_usable_army_observed", next_formal={
                "selected_step": preview_move_army_step(selected["army_id"], target),
                "expected_revision": after["revision"], "army_id": selected["army_id"],
                "target_province_id": target, "source": "observed_order_army_and_original_siege_target"})
        elif receipt["employer_observed"]:
            receipt["status"] = "employer_observed_army_pending"
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        receipt["post_query_error"] = str(error)
    # The native ACK stays intact, including its false after_state_observed.
    return {**ack, "holy_order_reinforcement_postcondition": receipt}
