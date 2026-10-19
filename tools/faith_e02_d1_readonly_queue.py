"""Finite D1 queries/UI selection; never a decision confirmation or activity launch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

DECISION = "create_hof_decision"
QUERIES = frozenset({
    "ck3_query_campaign_root_context_v1", "ck3_query_current_event_window_context_v1",
    "ck3_query_player_religion_context_v1", "ck3_query_player_rite_governance_v1",
    "ck3_query_player_pilgrimage_activities_v1",
})
STEP_KEYS = frozenset({"id", "kind", "tool", "args", "fresh_revision", "continue_on_error", "timeout"})


def require(value, message):
    if not value:
        raise ValueError(message)


def fields(args, required=(), optional=(), fresh=False):
    require(set(args) <= set(required) | set(optional), "D1 tool has unlisted fields")
    needed = set(required)
    if fresh:
        needed.discard("expected_revision")
    require(needed <= set(args), "D1 tool lacks required explicit fields")
    if "expected_revision" in args:
        require(type(args["expected_revision"]) is int and args["expected_revision"] > 0,
                "D1 revision must be an observed positive integer")


def following(steps, i, tool, args):
    require(i + 1 < len(steps), "D1 UI selection needs an independent later query")
    row = steps[i + 1]
    require(row.get("tool") == tool and row.get("fresh_revision") is True
            and all(row.get("args", {}).get(k) == v for k, v in args.items()),
            "D1 UI selection must immediately precede its matching fresh query")


def validate(plan, report=None):
    require(type(plan) is dict and set(plan) == {"steps"}
            and type(plan["steps"]) is list and 1 <= len(plan["steps"]) <= 16,
            "D1 requires 1..16 explicit finite tool steps")
    rows = plan["steps"]
    ids = []
    for i, row in enumerate(rows):
        require(type(row) is dict and set(row) <= STEP_KEYS
                and row.get("kind", "tool") == "tool", "D1 rejects lifecycle/day/raw operations")
        require(isinstance(row.get("id"), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", row["id"]),
                "D1 step needs a portable explicit identity")
        ids.append(row["id"])
        args = row.get("args", {})
        require(type(args) is dict and row.get("continue_on_error") is True,
                "D1 must retain real unavailable results without closing the host")
        require("fresh_revision" not in row or type(row["fresh_revision"]) is bool,
                "D1 fresh_revision must be a boolean")
        if "timeout" in row:
            require(type(row["timeout"]) in (int, float) and 0 < row["timeout"] <= 300,
                    "D1 query timeout exceeds bounded allocation")
        tool, fresh = row.get("tool"), row.get("fresh_revision") is True
        if tool == "ck3_take_snapshot":
            fields(args, optional={"include_native_command_history"})
            require(args.get("include_native_command_history", False) is False,
                    "D1 does not export unused command history")
        elif tool == "ck3_get_capabilities":
            fields(args)
        elif tool in QUERIES:
            fields(args, {"expected_revision"}, fresh=fresh)
        elif tool == "ck3_inspect_gui_window_tree_v1":
            fields(args, {"window_kind"})
            require(args["window_kind"] in {"decisions", "decision_detail"}, "D1 finite window scope differs")
        elif tool == "ck3_open_ingame_decisions_v1":
            fields(args, {"expected_revision"}, fresh=fresh)
            following(rows, i, "ck3_inspect_gui_window_tree_v1", {"window_kind": "decisions"})
        elif tool in {"ck3_query_ingame_decision_item_v1", "ck3_select_ingame_decision_item_v1"}:
            fields(args, {"decision_key", "expected_revision"}, fresh=fresh)
            require(args["decision_key"] == DECISION, "D1 only observes the actual HoF decision")
            if tool == "ck3_select_ingame_decision_item_v1":
                require(i > 0 and rows[i-1].get("tool") == "ck3_query_ingame_decision_item_v1"
                        and rows[i-1].get("args", {}).get("decision_key") == DECISION,
                        "D1 Select needs the same plan's preceding keyed model query")
                following(rows, i, "ck3_query_ingame_decision_item_v1", {"decision_key": DECISION})
        else:
            raise ValueError("D1 rejects world confirmation, activity start, save, days or unlisted tool: " + str(tool))
    require(len(ids) == len(set(ids)), "D1 duplicate step identity; never replay")
    return {"schema": "faith-e02-D1-readonly-capture-policy-v1", "capture_policy_validated": True,
            "steps": len(rows), "submitted": False, "native_legality_or_success_inferred": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--live", type=Path)
    p.add_argument("--queue-name")
    args = p.parse_args(argv)
    value = validate(json.loads(args.plan.read_bytes()))
    if args.queue_name:
        require(args.live is not None, "D1 dispatch needs its actual public allocated live directory")
        entry = Path(__file__).resolve().with_name("ck3_mod_acceptance_queue_control.py")
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(entry),
                               "--live", str(args.live), "--plan", str(args.plan),
                               "--name", args.queue_name], check=False).returncode
    print(json.dumps(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
