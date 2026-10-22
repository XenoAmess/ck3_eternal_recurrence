"""Finite ordinary pilgrimage controls through the existing public queue."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

QUERY = "ck3_query_player_pilgrimage_planner_v1"
SUBMIT = "ck3_submit_player_pilgrimage_planner_v1"
READS = {"ck3_query_player_religion_context_v1", "ck3_query_player_pilgrimage_activities_v1"}
RESERVES = {"reserve_gold_raw", "reserve_treasury_raw", "reserve_piety_raw", "reserve_barter_goods_raw"}
STEP_KEYS = {"id", "kind", "tool", "args", "fresh_revision", "continue_on_error", "timeout"}


def require(value, message):
    if not value:
        raise ValueError(message)


def integer(value, low=0, high=2**63-1):
    return type(value) is int and low <= value <= high


def validate(plan, report=None):
    require(type(plan) is dict and set(plan) == {"steps"} and type(plan["steps"]) is list
            and 1 <= len(plan["steps"]) <= 16, "Pilgrimage needs 1..16 finite controls")
    ids, starts = [], 0
    for row in plan["steps"]:
        require(type(row) is dict and set(row) <= STEP_KEYS and row.get("kind", "tool") == "tool",
                "Planner queue only accepts listed tool operations")
        identifier = row.get("id")
        require(isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", identifier),
                "Pilgrimage control identity is invalid")
        ids.append(identifier)
        require(row.get("fresh_revision") is True and row.get("continue_on_error") is True,
                "Retain failures and obtain the revision from this original public queue")
        args, tool = row.get("args", {}), row.get("tool")
        require(type(args) is dict, "Explicit tool arguments required")
        if tool == "ck3_take_snapshot":
            require(set(args) <= {"include_native_command_history"}
                    and args.get("include_native_command_history", False) is False, "Snapshot scope differs")
            continue
        if tool in READS:
            require(set(args) <= {"expected_revision"}, "Read tool has unlisted fields")
            continue
        require(tool in {QUERY, SUBMIT}, "Unlisted planner tool")
        submit = tool == SUBMIT
        allowed = {"operation", "expected_revision", "province_id", "timeout_seconds", "option_key"}
        allowed |= {"policy_positive"} | RESERVES if submit else {"read_stage"}
        require(set(args) <= allowed, "Unlisted planner argument")
        require(type(args.get("option_key", "pilgrimage_type_pious")) is str
                and args.get("option_key", "pilgrimage_type_pious") in {
            "pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"
        }, "Unsupported pilgrimage option identity")
        operation = args.get("operation", "read" if not submit else None)
        require(operation in ({"open", "confirm", "select", "start"} if submit
                              else {"read", "can_select", "quote", "post"}), "Unlisted planner operation")
        province = args.get("province_id", 0)
        require(integer(province, 0, 2**32-2), "Province identity is invalid")
        require((province > 0) if operation in {"can_select", "select", "start"} else province == 0,
                "Province does not match operation")
        if "expected_revision" in args:
            require(integer(args["expected_revision"], 1, 2**64-1), "Revision is invalid")
        timeout = args.get("timeout_seconds", 30)
        require(type(timeout) in {int, float} and math.isfinite(timeout) and 0 < timeout <= 300,
                "Finite command budget required")
        if submit:
            require(args.get("policy_positive") is True, "Submit requires an explicit positive policy")
            require(all(integer(args.get(key, 0)) for key in RESERVES), "Resource reserve is invalid")
            require(operation == "start" or all(args.get(key, 0) == 0 for key in RESERVES),
                    "Reserves only apply to Start")
            starts += operation == "start"
        else:
            stage = args.get("read_stage", 0)
            require(integer(stage, 0, 5) and (operation == "read" or stage == 0), "Read stage is invalid")
    require(len(ids) == len(set(ids)) and starts <= 1, "Duplicate controls or multiple Start requests")
    if report is not None and starts:
        require(not any(row.get("tool") == SUBMIT and row.get("args", {}).get("operation") == "start"
                        for row in report.get("steps", [])), "A prior Start is never repeated")
    return {"schema": "faith-e02-pilgrimage-finite-planner-queue-v1", "validated": True,
            "steps": len(ids), "start_requests": starts, "submitted": False,
            "native_legality_or_success_inferred": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--live", type=Path)
    parser.add_argument("--queue-name")
    args = parser.parse_args(argv)
    value = validate(json.loads(args.plan.read_bytes()))
    if args.queue_name:
        require(args.live is not None, "Actual allocated public live directory required")
        entry = Path(__file__).resolve().with_name("ck3_mod_acceptance_queue_control.py")
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(entry),
            "--live", str(args.live), "--plan", str(args.plan), "--name", args.queue_name], check=False).returncode
    print(json.dumps(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
