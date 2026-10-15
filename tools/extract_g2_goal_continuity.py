"""Summarize explicitly supplied closed receipts; never connect to a game.

This is an offline evidence projection, not a runtime acceptance gate. A missing
field is reported as not_observed. No process, driver-state, save or directory is
discovered or opened automatically. Callers supply completed receipt paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def structured(document):
    if not isinstance(document, dict):
        raise ValueError("receipt must be a JSON object")
    result = document.get("result", document)
    if not isinstance(result, dict):
        raise ValueError("receipt result must be an object")
    return result.get("structured_content", result)


def goal_projection(goal):
    if not isinstance(goal, dict):
        return None
    return {key: goal.get(key) for key in (
        "format_version", "goal_key", "campaign_id", "origin_character_id",
        "current_character_id", "progress",
    )}


def source(path):
    path = Path(path)
    size = path.stat().st_size
    if size > 262144:
        raise ValueError("supply an existing compact receipt, not a full Driver or trace")
    data = path.read_bytes()
    return json.loads(data), {
        "path": str(path), "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def frame_projection(value):
    if not isinstance(value, dict):
        return {}
    played = value.get("played_character")
    diagnostic = value.get("diagnostics")
    return {
        **{key: value.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "paused",
            "map_ready", "episode_character_id", "episode_run_id",
            "episode_identity_pending", "one_life_terminal_reason",
        ) if key in value},
        "played_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "played_character_alive": played.get("alive") if isinstance(played, dict) else None,
        "bridge_pid": diagnostic.get("bridge_pid") if isinstance(diagnostic, dict) else value.get("bridge_pid"),
    }


def plan_goal_values(document):
    """Find already-recorded plan consumption without traversing native history."""
    found = []
    excluded = {"history", "native_command_history", "native_transcript", "diagnostics"}

    def visit(value, path, depth):
        if depth > 12:
            return
        if isinstance(value, dict):
            plan = value.get("campaign_goal_plan_used")
            if isinstance(plan, dict):
                found.append({"json_path": path + ".campaign_goal_plan_used", "value": plan})
            for key, child in value.items():
                if key not in excluded and isinstance(child, (dict, list)):
                    visit(child, path + "." + key, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + "[" + str(index) + "]", depth + 1)

    visit(document, "$", 0)
    return found


def summarize(save_document, semantic_document, plan_document=None):
    saved = structured(save_document)
    semantic = structured(semantic_document)
    replace = saved.get("driver_state_replace_receipt", {})
    attempt = replace.get("attempt_binding", {})
    checkpoint = saved.get("checkpoint", {})
    old_goal = goal_projection(attempt.get("campaign_goal"))
    new_goal = goal_projection(semantic.get("campaign_goal"))
    plans = plan_goal_values(plan_document) if plan_document is not None else []
    saved_pid = attempt.get("bridge_pid")
    current = frame_projection(semantic)
    current_pid = current.get("bridge_pid")
    observed = old_goal is not None and new_goal is not None
    return {
        "evidence_layer": "offline projection of caller-supplied completed MCP receipts",
        "runtime_operations": 0,
        "save": {
            "step": saved.get("step"), "status": saved.get("status"),
            "checkpoint": {key: checkpoint.get(key) for key in (
                "status", "date_raw", "size", "sha256", "history_index",
                "episode_character_id", "episode_run_id", "succession_lifecycle",
            )},
            "driver_replace_scope": replace.get("scope"),
            "save_binding_verified": replace.get("save_binding_verified"),
            "bridge_pid": saved_pid, "campaign_goal": old_goal,
        },
        "semantic": {"frame": current, "campaign_goal": new_goal,
                     "succession_lifecycle": semantic.get("succession_lifecycle")},
        "comparison": {
            "goal_equal": old_goal == new_goal if observed else None,
            "goal_status": ("observed_equal" if old_goal == new_goal else "observed_different") if observed else "not_observed",
            "different_game_pid_observed": saved_pid != current_pid if saved_pid is not None and current_pid is not None else None,
            "same_saved_date": checkpoint.get("date_raw") == semantic.get("date_raw") if checkpoint.get("date_raw") is not None else None,
            "same_successor_episode": checkpoint.get("episode_run_id") == semantic.get("episode_run_id") if checkpoint.get("episode_run_id") is not None else None,
            "physical_cold_checkpoint_anchor": "not established by these two receipts alone",
        },
        "normal_plan_consumption": {"status": "observed" if plans else "not_observed", "occurrences": plans},
        "m7_complete_claimed": False,
        "stability_window_credit": "not calculated; owned by the main continuity ledger",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save-receipt", required=True, type=Path)
    parser.add_argument("--semantic-receipt", required=True, type=Path)
    parser.add_argument("--plan-receipt", type=Path)
    parser.add_argument("--existing-custody-evidence", action="append", type=Path, default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    save, save_source = source(args.save_receipt)
    semantic, semantic_source = source(args.semantic_receipt)
    plan, plan_source = source(args.plan_receipt) if args.plan_receipt else (None, None)
    report = summarize(save, semantic, plan)
    report["source_pins"] = {"save": save_source, "semantic": semantic_source, "plan": plan_source}
    # Custody receipts are retained as explicit references. A generic tool cannot
    # turn an unrelated receipt or a PID into a physical-restore proof.
    report["additional_custody_receipt_pins"] = [source(path)[1] for path in args.existing_custody_evidence]
    encoded = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if len(encoded) > 65536:
        raise ValueError("projection exceeds its compact report budget")
    args.output.write_bytes(encoded)
    print(json.dumps({"output": str(args.output), "bytes": len(encoded),
                      "goal_status": report["comparison"]["goal_status"]}))


if __name__ == "__main__":
    main()
