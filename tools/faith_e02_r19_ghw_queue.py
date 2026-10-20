"""Finite H2 original-once plus GHW observation; no GHW world action."""
from __future__ import annotations
import faith_e02_hof_queue as hof

DECISION = hof.DECISION
QUERY = hof.QUERY
CONFIRM = hof.CONFIRM
EVENT_CONTEXT = hof.EVENT_CONTEXT
EVENT_SELECT = hof.EVENT_SELECT
LAUNCH_DECISION = "launch_undirected_great_holy_war_decision"
GHW_QUERY = "ck3_query_player_ghw_permissions_v1"
PILGRIMAGE_QUERY = "ck3_query_player_pilgrimage_activities_v1"
require = hof.require
pin = hof.pin
read_pin = hof.read_pin
quote_terms = hof.quote_terms
verify_quote_pair = hof.verify_quote_pair
first_event_option = hof.first_event_option
admit_event_choice = hof.admit_event_choice
admit_confirm = hof.admit_confirm


def validate(plan, *, claim_path=None, event_path=None):
    require(isinstance(plan, dict) and set(plan) == {"steps"}
        and isinstance(plan["steps"], list) and 1 <= len(plan["steps"]) <= 8,
        "R19 combined needs a finite plan")
    ids = []
    for step in plan["steps"]:
        require(isinstance(step, dict) and set(step) <= {
            "id", "kind", "tool", "args", "fresh_revision", "continue_on_error"}
            and step.get("kind", "tool") == "tool" and step.get("fresh_revision") is True
            and step.get("continue_on_error") is True and isinstance(step.get("id"), str),
            "R19 rejects raw, stale, day, save or lifecycle operation")
        ids.append(step["id"])
        tool, args = step.get("tool"), step.get("args", {})
        require(isinstance(args, dict), "R19 combined requires named args")
        if tool in {GHW_QUERY, PILGRIMAGE_QUERY}:
            require(set(args) <= {"expected_revision"}, "R19 readonly query accepts no actor/key/pointer")
            if "expected_revision" in args:
                require(type(args["expected_revision"]) is int and args["expected_revision"] > 0,
                    "R19 requires a positive real public revision")
        elif tool in {QUERY, "ck3_select_ingame_decision_item_v1"} and args.get("decision_key") == LAUNCH_DECISION:
            require(set(args) <= {"decision_key", "expected_revision"}, "R19 launch detail args differ")
            if "expected_revision" in args:
                require(type(args["expected_revision"]) is int and args["expected_revision"] > 0,
                    "R19 requires a positive real public revision")
        else:
            # Existing H2/event once admission is reused unchanged. Its only
            # Confirm key is create_hof_decision; launch Confirm cannot pass.
            hof.validate({"steps": [step]}, claim_path=claim_path, event_path=event_path)
    require(len(ids) == len(set(ids)), "R19 combined step identity reused")
    return {"capture_policy_validated": True, "ghw_action_allowed": False,
        "native_legality_or_success_inferred": False}
