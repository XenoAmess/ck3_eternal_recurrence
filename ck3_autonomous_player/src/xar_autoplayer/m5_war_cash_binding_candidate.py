"""Structural candidates for a future same-frame wartime cash producer.

These checks do not authenticate a native quote, establish a zero-cost action,
or turn any cash receipt into a formal action.  They make two otherwise easy
to-miss mismatches explicit before a producer is connected: a quote reused for
another action and independent cash floors collapsed with ``max``.
"""

from __future__ import annotations

from collections.abc import Mapping


_MAX_SIGNED_RAW = (1 << 63) - 1


def _gold_raw(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_SIGNED_RAW:
        raise ValueError(f"{name} needs a nonnegative signed Q100000 raw amount")
    return value


def require_structural_action_quote_binding_v1(
    *, plan: Mapping[str, object], quote: Mapping[str, object],
    frame: Mapping[str, object], war_id: int,
) -> dict[str, object]:
    """Check exact plan/quote identity; return diagnostic, never entitlement.

    ``plan.priced_command`` is a producer-supplied typed action identity.  A
    move must contain army, origin, target, full route and preview sequence.
    The future native producer must independently prove that this identity,
    quote and paused frame refer to the same game object and that the quote is
    fresh.  Strings in this object are not such proof.
    """
    if type(war_id) is not int or war_id <= 0:
        raise ValueError("positive WarID required")
    if not isinstance(plan, Mapping) or not isinstance(quote, Mapping):
        raise ValueError("plan and quote objects required")
    selected_step = plan.get("selected_step")
    command = plan.get("priced_command")
    if type(selected_step) is not str or not selected_step:
        raise ValueError("selected war step required")
    if not isinstance(command, Mapping):
        raise ValueError("typed priced command required on plan")
    if (quote.get("source_frame") != dict(frame)
            or quote.get("war_id") != war_id
            or quote.get("selected_step") != selected_step
            or quote.get("priced_command") != command):
        raise ValueError("war quote changed frame, WarID or selected command")
    kind = command.get("kind")
    if kind == "read_only_query":
        # This is the only query step with a reviewed typed projection.  A
        # matching plan/quote pair is still unsafe if both carry a different
        # selected step for the same query.  Extend this table only alongside
        # the corresponding native bridge step and its argument contract.
        query_steps = {
            "war_termination_options": f"query-war-termination-options-{war_id}",
        }
        if (set(command) != {"kind", "war_id", "query_name"}
                or command.get("war_id") != war_id
                or type(command.get("query_name")) is not str
                or selected_step != query_steps.get(command["query_name"])):
            raise ValueError("read-only query identity is incomplete")
    elif kind == "move_army":
        if set(command) != {
            "kind", "army_id", "origin_province_id", "target_province_id",
            "route_province_ids", "route_preview_query_sequence",
        }:
            raise ValueError("move quote lacks complete typed route identity")
        for name in ("army_id", "origin_province_id", "target_province_id",
                     "route_preview_query_sequence"):
            if type(command.get(name)) is not int or command[name] <= 0:
                raise ValueError(f"move quote lacks positive {name}")
        route = command.get("route_province_ids")
        if (not isinstance(route, list) or len(route) < 2
                or any(type(item) is not int or item <= 0 for item in route)
                or route[0] != command["origin_province_id"]
                or route[-1] != command["target_province_id"]):
            raise ValueError("move quote route endpoints are unproved")
        expected_step = (
            f"move-army-{command['army_id']}-to-{command['target_province_id']}"
        )
        if selected_step != expected_step:
            raise ValueError("move quote differs from selected step")
    else:
        raise ValueError("unsupported war command kind for cash quote")
    amount = _gold_raw(quote.get("quoted_cost_raw"), "quoted_cost_raw")
    if quote.get("scale") != 100_000:
        raise ValueError("war quote requires Q100000 scale")
    quote_id = quote.get("native_quote_id")
    if type(quote_id) is not str or not quote_id:
        raise ValueError("native quote identity is unavailable")
    return {
        "status": "structurally_bound_only",
        "selected_step": selected_step,
        "war_id": war_id,
        "quoted_cost_raw": amount,
        "native_quote_id": quote_id,
        "same_frame_native_quote_proven": False,
        "native_quote_pure_read_proven": False,
        "formal_cash_eligible": False,
    }


def add_independent_cash_reserves_v1(
    *, construction_policy_floor_raw: int,
    future_war_cost_upper_raw: int, future_risk_budget_raw: int,
    war_policy_minimum_raw: int,
) -> dict[str, object]:
    """Add disjoint construction and war needs without asserting overlap.

    A policy that proves overlap needs a separate explicit contract.  The
    caller still must source each input in the same paused frame and account
    for pending commitments and the selected action fee separately.
    """
    parts = {
        "construction_policy_floor_raw": _gold_raw(
            construction_policy_floor_raw, "construction_policy_floor_raw"),
        "future_war_cost_upper_raw": _gold_raw(
            future_war_cost_upper_raw, "future_war_cost_upper_raw"),
        "future_risk_budget_raw": _gold_raw(
            future_risk_budget_raw, "future_risk_budget_raw"),
        "war_policy_minimum_raw": _gold_raw(
            war_policy_minimum_raw, "war_policy_minimum_raw"),
    }
    total = sum(parts.values())
    if total > _MAX_SIGNED_RAW:
        raise ValueError("independent cash reserves overflow signed raw gold")
    return {
        "status": "arithmetic_candidate_only",
        "components_raw": parts,
        "required_global_gold_reserve_raw": total,
        "overlap_assumed": False,
        "source_frame_proven": False,
        "formal_action_ready": False,
    }
