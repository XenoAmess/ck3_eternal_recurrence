#!/usr/bin/env python3
"""Verify a frozen preview's formal pending-reply action and later turn.

This reads evidence only. The expected definition/step are assertion inputs in
the operator manifest; they are never sent as gameplay action parameters.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _report(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            value = json.loads(raw.decode(encoding))
            if isinstance(value, dict):
                return value
        except (UnicodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"cannot read report JSON: {path}")


def _pending(snapshot: object) -> dict[str, Any] | None:
    if not isinstance(snapshot, dict):
        return None
    context = snapshot.get("active_context")
    pending = context.get("pending_character_interaction") if isinstance(context, dict) else None
    return pending if isinstance(pending, dict) else None


def _decision(row: object) -> dict[str, Any] | None:
    plan = row.get("plan") if isinstance(row, dict) else None
    decision = plan.get("decision") if isinstance(plan, dict) else None
    return decision if isinstance(decision, dict) else None


def _sha_matches(actual: object, expected: object) -> bool:
    return isinstance(actual, str) and isinstance(expected, str) and actual.lower() == expected.lower()


def _checks(
    manifest: dict[str, Any], eligibility: dict[str, Any], formal: dict[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    expected = manifest.get("preview_action")
    if not isinstance(expected, dict) or expected.get("kind") != "pending_reply":
        raise ValueError("manifest.preview_action must describe a pending_reply")
    for field in ("definition_key", "step", "result_status", "rule_id"):
        if not isinstance(expected.get(field), str) or not expected[field]:
            raise ValueError(f"manifest.preview_action.{field} is required")
    auto_run = formal.get("auto_run")
    turns = auto_run.get("turns") if isinstance(auto_run, dict) else None
    turns = turns if isinstance(turns, list) else []
    action = next(
        (
            row for row in turns
            if isinstance(row, dict)
            and row.get("selected_step") == expected["step"]
            and isinstance(_decision(row), dict)
            and _decision(row).get("interaction_key") == expected["definition_key"]
        ), None,
    )
    decision = _decision(action)
    old_id = decision.get("pending_interaction_id") if isinstance(decision, dict) else None
    before = action.get("before") if isinstance(action, dict) else None
    after = action.get("after") if isinstance(action, dict) else None
    before_pending = _pending(before)
    after_pending = _pending(after)
    result = action.get("result") if isinstance(action, dict) else None
    interaction = result.get("interaction_result") if isinstance(result, dict) else None
    action_index = action.get("index") if isinstance(action, dict) else None
    query_before = any(
        isinstance(row, dict)
        and row.get("selected_step") == "query-pending-character-interaction-context-v1"
        and isinstance(row.get("index"), int)
        and isinstance(action_index, int)
        and row["index"] < action_index
        and isinstance(_pending(row.get("before")), dict)
        and _pending(row["before"]).get("instance_id") == old_id
        for row in turns
    )
    following = [
        row for row in turns
        if isinstance(row, dict) and row.get("ok") is True
        and isinstance(row.get("index"), int)
        and isinstance(action_index, int)
        and row["index"] > action_index
    ]
    next_consumed = bool(following) and all(
        not (isinstance(_pending(row.get("before")), dict)
             and _pending(row["before"]).get("instance_id") == old_id)
        and row.get("selected_step") != expected["step"]
        for row in following
    )
    checkpoints = formal.get("checkpoints")
    checkpoints = checkpoints if isinstance(checkpoints, list) else []
    action_date = after.get("date_raw") if isinstance(after, dict) else None
    action_checkpoint = any(
        isinstance(row, dict) and row.get("status") == "saved"
        and isinstance(row.get("turn_index"), int)
        and isinstance(action_index, int)
        and row["turn_index"] >= action_index
        and isinstance(row.get("date_raw"), int)
        and isinstance(action_date, int) and row["date_raw"] >= action_date
        and isinstance(row.get("sha256"), str)
        for row in checkpoints
    )
    identity = formal.get("identity")
    identity = identity if isinstance(identity, dict) else {}
    dll = identity.get("bridge_dll")
    injector = identity.get("bridge_injector")
    readiness = formal.get("readiness")
    active_initial = readiness.get("active_context") if isinstance(readiness, dict) else None
    qualification = eligibility.get("checks")
    qualification = qualification if isinstance(qualification, dict) else {}
    preflight = eligibility.get("preflight")
    preflight = preflight if isinstance(preflight, dict) else {}
    cleanup = formal.get("cleanup")
    cleanup = cleanup if isinstance(cleanup, dict) else {}
    checks = {
        "same_seed_feudal_paused_eligibility": eligibility.get("status") == "GREEN_READ_ONLY"
        and qualification.get("government_exact_feudal") is True
        and qualification.get("no_war_event_pending_army") is True
        and preflight.get("source_commit") == manifest.get("source_commit")
        and _sha_matches(preflight.get("environment_sha256"), manifest.get("environment_sha256")),
        "frozen_binary_and_projection": _sha_matches(
            dll.get("sha256") if isinstance(dll, dict) else None, manifest.get("dll_sha256")
        ) and _sha_matches(
            injector.get("sha256") if isinstance(injector, dict) else None,
            manifest.get("injector_sha256")
        ) and _sha_matches(identity.get("production_tree_sha256"),
                           manifest.get("production_tree_sha256")),
        "formal_production_entry": formal.get("kind") == "ck3_native_auto_run"
        and formal.get("mode") == "native-headless"
        and formal.get("cold_start_checkpoint") is True,
        "same_episode_start": isinstance(readiness, dict)
        and readiness.get("played_character_id") == manifest.get("episode_character_id")
        and readiness.get("episode_run_id") == manifest.get("episode_run_id")
        and readiness.get("date_raw") == manifest.get("date_raw")
        and isinstance(active_initial, dict)
        and active_initial.get("war_ids") == [] and active_initial.get("army_ids") == []
        and active_initial.get("active_event") is None
        and active_initial.get("pending_character_interaction") is None,
        "bounded_qualified_and_process_recycled": formal.get("ok") is True
        and formal.get("status") == "turn_limit"
        and cleanup.get("ok") is True,
        "natural_exact_definition_policy": isinstance(decision, dict)
        and decision.get("interaction_key") == expected["definition_key"]
        and decision.get("rule_id") == expected["rule_id"]
        and isinstance(old_id, int) and not isinstance(old_id, bool),
        "typed_query_before_action": query_before,
        "same_live_pending_before": isinstance(before_pending, dict)
        and before_pending.get("instance_id") == old_id,
        "typed_independent_postcondition": isinstance(interaction, dict)
        and interaction.get("status") == expected["result_status"]
        and interaction.get("instance_id") == old_id
        and isinstance(after, dict) and after.get("paused") is True
        and isinstance(before, dict) and after.get("snapshot_id") != before.get("snapshot_id")
        and after_pending is None
        and isinstance(result, dict)
        and result.get("remaining_pending_character_interaction") is None,
        "next_turn_consumed_without_duplicate": next_consumed,
        "checkpoint_after_semantic_action": action_checkpoint,
    }
    context = {"action_turn": action_index, "live_pending_id": old_id,
               "following_successful_turns": len(following)}
    return checks, context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--eligibility-report", required=True, type=Path)
    parser.add_argument("--formal-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    manifest = _report(args.manifest)
    eligibility = _report(args.eligibility_report)
    formal = _report(args.formal_report)
    checks, context = _checks(manifest, eligibility, formal)
    output = {
        "schema": "xar.ck3.g2_preview_formal_action_verification_v1",
        "status": "GREEN_ACTION_LOOP" if all(checks.values()) else "RED_OR_INCOMPLETE",
        "checks": checks, "context": context,
        "manifest": str(args.manifest.resolve()),
        "eligibility_report": str(args.eligibility_report.resolve()),
        "formal_report": str(args.formal_report.resolve()),
        "formal_status": formal.get("status"), "formal_outcome": formal.get("outcome"),
        "formal_error": formal.get("error"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "checks": checks,
                      "report": str(args.output)}))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
