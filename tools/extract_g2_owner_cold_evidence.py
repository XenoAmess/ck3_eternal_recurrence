"""Offline closed-receipt projection; missing fields stay unknown.
No game/OS access, runtime admission, discovery or stability credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_g2_goal_continuity import (
    source, structured, frame_projection, goal_projection,
)

MAX_INPUT = 262144
GOAL_KEYS = ("goal_key", "campaign_id", "current_character_id", "progress")
CONTROL_KEYS = (
    "driver_state_restored", "driver_state_restore_kind", "episode_binding_state",
    "cold_candidate_rejection", "driver_state_error",
)


def read_receipt(path):
    path = Path(path)
    if path.suffix.lower() != ".json" or path.name.lower() == "driver-state.json":
        raise ValueError("explicit compact closed JSON receipts only")
    document, pin = source(path)
    if not isinstance(document, dict):
        raise ValueError("receipt must be a JSON object")
    return document, pin


def select(value, keys):
    value = value if isinstance(value, dict) else {}
    return {key: value.get(key) for key in keys}


def body(document):
    value = structured(document)
    if not isinstance(value, dict):
        raise ValueError("structured receipt must be an object")
    return value


def equal(*values):
    if any(value is None for value in values):
        return None
    first = values[0]
    return all(type(value) is type(first) and value == first for value in values)


def together(*values):
    if False in values:
        return False
    return None if None in values else True


def pointer(document, path):
    if not path.startswith("/"):
        raise ValueError("plan goal pointer must start with /")
    value = document
    for part in path[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value.get(key) if isinstance(value, dict) else None
    return value


def control_projection(document):
    if document is None:
        return {"request_tool": None, "native_session_control": None}
    tool = document.get("request", {}).get("tool")
    control = body(document).get("native_session_control")
    if tool not in (None, "ck3_get_capabilities", "ck3_get_capabilities_private_v1"):
        control = None
    return {
        "request_tool": tool,
        "native_session_control": select(control, CONTROL_KEYS)
        if isinstance(control, dict) else None,
    }


def summarize(owner, inputs, migration, semantic, *, initial_capabilities=None, hot_semantic=None, hot_capabilities=None,
              plan=None, plan_pointer="/result/structured_content/plan/campaign_goal_plan_used"):
    current = body(semantic)
    frame = frame_projection(current)
    goal = goal_projection(current.get("campaign_goal"))
    checkpoint = inputs.get("checkpoint", {})
    relocated = migration.get("checkpoint", {})
    previous = inputs.get("source_game_identity", {})
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    relocated = relocated if isinstance(relocated, dict) else {}
    previous = previous if isinstance(previous, dict) else {}
    name = checkpoint.get("name")
    load_name = name[:-4] if isinstance(name, str) and name.endswith(".ck3") else None
    command = owner.get("command")
    command_matches = (("-loadsave=" + load_name) in command
                       if isinstance(command, list) and load_name else None)
    sha = checkpoint.get("sha256")
    valid_sha = (len(sha) == 64 and all(c in "0123456789abcdefABCDEF" for c in sha)
                 if isinstance(sha, str) else None)
    size = checkpoint.get("size")
    valid_size = size > 0 if type(size) is int else None
    checks = {
        "prior_game_exit_observed": equal(inputs.get("old_game_actual_exit_verified"), True),
        "owner_reports_named_load": together(
            equal(owner.get("old_save_loaded"), True),
            equal(owner.get("load_save_name"), relocated.get("load_save_name"), load_name),
            equal(name, relocated.get("name")), command_matches),
        "checkpoint_identity_matches": together(
            valid_sha, valid_size,
            equal(sha, relocated.get("sha256"), inputs.get("canonical_save_sha256")),
            equal(size, relocated.get("size")),
            equal(checkpoint.get("date_raw"), relocated.get("saved_date_raw")),
            equal(checkpoint.get("history_index"), relocated.get("history_index"))),
        "owner_pid_matches_frame": equal(owner.get("pid"), frame.get("bridge_pid")),
        "different_game_pid_observed": (
            previous.get("pid") != owner.get("pid")
            if previous.get("pid") is not None and owner.get("pid") is not None else None),
        "checkpoint_frame_matches": together(
            equal(checkpoint.get("date_raw"), frame.get("date_raw")),
            equal(checkpoint.get("episode_character_id"), frame.get("episode_character_id"),
                  frame.get("played_character_id")),
            equal(checkpoint.get("episode_run_id"), frame.get("episode_run_id"))),
        "paused_playable_frame": together(
            equal(frame.get("paused"), True), equal(frame.get("map_ready"), True),
            equal(frame.get("played_character_alive"), True)),
        "goal_tracks_played_actor": equal(
            goal.get("current_character_id") if goal else None,
            frame.get("played_character_id")),
    }
    optional = {}
    hot = body(hot_semantic) if hot_semantic is not None else {}
    hot_frame = frame_projection(hot)
    hot_goal = goal_projection(hot.get("campaign_goal"))
    optional["later_hot_goal_and_episode_match"] = together(
        equal(goal, hot_goal),
        equal(frame.get("episode_run_id"), hot_frame.get("episode_run_id")),
        equal(frame.get("bridge_pid"), hot_frame.get("bridge_pid")))
    hot_control = control_projection(hot_capabilities)
    hot_values = hot_control["native_session_control"] or {}
    optional["later_control_reports_same_pid_hot"] = together(
        equal(hot_values.get("driver_state_restored"), True),
        equal(hot_values.get("driver_state_restore_kind"), "same_pid_hot"),
        equal(hot_values.get("episode_binding_state"), "active_resumed"))
    plan_goal = pointer(plan, plan_pointer) if plan is not None else None
    plan_values = select(plan_goal, GOAL_KEYS) if isinstance(plan_goal, dict) else None
    optional["later_plan_goal_fields_match"] = together(*(
        equal(goal.get(key) if goal else None,
              plan_values.get(key) if plan_values else None) for key in GOAL_KEYS))
    state = ("observed_mismatch" if False in checks.values() else
             "incomplete_observations" if None in checks.values() else
             "consistent_supplied_fields")
    return {
        "schema": "g2-owner-cold-evidence-projection-v1",
        "evidence_layer": "offline supplied owner/load/checkpoint/frame fields",
        "owner_chain_state": state, "checks": checks, "optional_checks": optional,
        "owner_load": select(owner, ("pid", "creation_date", "load_save_name",
                                     "old_save_loaded", "command")),
        "prior_game": select(previous, ("pid", "creation_filetime")),
        "prior_exit": select(inputs, (
            "old_game_actual_exit_verified", "old_game_normal_close_qualified",
            "old_game_actual_exit_code", "old_game_close_classification")),
        "checkpoint": select(checkpoint, (
            "name", "size", "sha256", "date_raw", "history_index",
            "episode_character_id", "episode_run_id")),
        "restored_frame": frame, "restored_goal": goal,
        "initial_control": control_projection(initial_capabilities),
        "later_hot_control": hot_control,
        "later_plan": {"json_pointer": plan_pointer, "goal_fields": plan_values,
                       "timing": "later observation; not immediate next turn"},
        "limits": "No save revalidation or government inference; PID alone is not cold proof.",
        "runtime_operations": 0, "m7_complete_claimed": False,
        "stability_window_credit": "not calculated; owned by the main continuity ledger",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    required = ("owner-load", "cold-input", "relocation", "semantic")
    optional = ("initial-capabilities", "later-hot-semantic",
                "later-hot-capabilities", "plan")
    for name in required + optional:
        parser.add_argument("--" + name + "-receipt", type=Path, required=name in required)
    parser.add_argument("--plan-goal-pointer",
                        default="/result/structured_content/plan/campaign_goal_plan_used")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    documents, pins = {}, {}
    for name in required + optional:
        path = getattr(args, name.replace("-", "_") + "_receipt")
        documents[name], pins[name] = read_receipt(path) if path else (None, None)
    report = summarize(
        documents["owner-load"], documents["cold-input"], documents["relocation"],
        documents["semantic"],
        initial_capabilities=documents["initial-capabilities"],
        hot_semantic=documents["later-hot-semantic"],
        hot_capabilities=documents["later-hot-capabilities"], plan=documents["plan"],
        plan_pointer=args.plan_goal_pointer)
    report["source_pins"] = pins
    encoded = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if len(encoded) > 65536:
        raise ValueError("compact output budget exceeded")
    with args.output.open("xb") as handle:
        handle.write(encoded)
    print(json.dumps({"output": str(args.output), "bytes": len(encoded),
                      "owner_chain_state": report["owner_chain_state"]}))


if __name__ == "__main__":
    main()
