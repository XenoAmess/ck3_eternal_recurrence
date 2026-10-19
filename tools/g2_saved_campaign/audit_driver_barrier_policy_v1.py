"""Audit existing Driver/WAL policy from source and sealed small metrics only."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
EXPERIMENT = ROOT / "ck3_autonomous_player/experimental/driver_state_wal_v1"


def require(condition, message=None):
    """Keep source-only audit rejection active under Python -O."""
    if not condition:
        if message is None:
            raise AssertionError
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True, cwd=ROOT).strip()
    source = NATIVE.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "NativeHeadlessGameplayDriver")
    methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}
    deferred = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_is_deferred_read_only_history_step")
    barrier_calls = []
    for name, node in methods.items():
        for call in ast.walk(node):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name) and call.func.value.id == "self"
                    and call.func.attr == "_persist_driver_state"):
                barrier_calls.append({"method": name, "line": call.lineno,
                                      "call": ast.get_source_segment(source, call)})
    patch_source = (EXPERIMENT / "bridge-native_driver.py.patch").read_text(encoding="utf-8-sig")
    helper_source = (EXPERIMENT / "driver_state_wal_v1.py").read_text(encoding="utf-8-sig")
    helper_ast = ast.parse(helper_source)
    helper_functions = {node.name: node for node in helper_ast.body if isinstance(node, ast.FunctionDef)}
    p49_path = ROOT / "docs/ck3-native-ai/evidence/p49-settled-performance.json"
    stages_path = ROOT / "docs/ck3-native-ai/evidence/p49-stage-slice.json"
    p49 = json.loads(p49_path.read_bytes())
    stages = json.loads(stages_path.read_bytes())
    settled = p49["5104-5165"]
    require('step.startswith("query-")' in ast.get_source_segment(source, deferred))
    require('step in {"life-advance", "life-advance-one-day"}' in patch_source)
    require('self._command_history[start:]' in patch_source)
    require('document.get("consolidated_sha256") is not None' in patch_source)
    require('MAX_DELTA_BYTES = 256 * 1024' in helper_source)
    require('MAX_JOURNAL_BYTES = 8 * 1024 * 1024' in helper_source)
    require(len(barrier_calls) == 12)
    roles = {
        "retain_succession_expectation_v1": "same-frame succession expectation scalar capture; persists even without a newly appended row",
        "_with_one_life_episode": "observed episode identity changed; identity/lineage barrier",
        "_migrate_legacy_rollback_war_failures": "one-time rollback schema/material migration",
        "set_player_character_v1": "explicit operator identity rebind after independently observed native result",
        "_record_command": "all failures and successful commands outside deferred readonly predicate; includes SAVE capture binding",
        "_observe_arrange_marriage_outcome": "supported in-place edit of an older history row, invalidates JSON cache; cannot be represented by append-only suffix",
        "_bind_new_episode_from_seed_snapshot": "new episode replaces history and episode identity",
        "_adopt_bridge_session": "physical bridge adoption/recovery identity and possible history replacement",
        "_bind_episode_from_playable_snapshot": "accept/reject cold checkpoint branch, history and identity replacement",
        "_restore_phase2_registered_checkpoint_v1": "register source checkpoint plus history anchor before restore",
        "_execute_restore_checkpoint": "managed restore marker must be published before native-session replaces CK3",
        "close": "flush pending history before endpoint closes; experimental WAL additionally consolidates committed entries",
    }
    for row in barrier_calls:
        row["role"] = roles.get(row["method"], "source-visible barrier; see pinned method and call line")
    pins = []
    for path in (NATIVE, EXPERIMENT / "bridge-native_driver.py.patch", EXPERIMENT / "driver_state_wal_v1.py",
                 ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_transport_v1.py",
                 ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_v1.py",
                 ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py",
                 p49_path, stages_path, Path(__file__)):
        raw = path.read_bytes()
        pins.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()})
    result = {
        "schema": "xar.driver-barrier-policy-source-audit.v1", "machine_id": machine,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip(),
        "scope": "source and existing sealed small JSON only; no benchmark, test matrix, runtime tuple, Driver, SAVE or live RPC",
        "conclusion": "Keep existing deferred successful query rows; do not add a per-query flush. Reuse the existing generic WAL append primitive, and qualify/narrow the timeline policy and failed-full-barrier boundary before any future adoption.",
        "historical_basis": {"P49_machine_id": p49.get("machine_id", "unknown"),
            "stage_machine_id": stages.get("machine_id", "unknown"),
            "machine_note": "small source projections omit machine identity; no path-based local qualification is inferred",
            "settled_window": "5104-5165", "turns": settled["turns"], "zero_date_turns": settled["zero_date_turns"],
            "zero_date_groups": {key: value for key, value in settled["auto_by_group"].items() if value["game_days"] == 0},
            "full_persistence": next(row for row in stages["stages"] if row["stage"] == "driver.full_state_persistence"),
            "stream_write": next(row for row in stages["stages"] if row["stage"] == "driver.full_state_temp_stream_write"),
            "exact_write_trigger_join_available": False,
            "limit": "43 zero-day turns and 21 full-state writes are different aggregate counts. Current source classification cannot establish which deployed historical turn caused a write."},
        "current_query_policy": {
            "predicate_line": deferred.lineno, "predicate_source": ast.get_source_segment(source, deferred),
            "successful_query_effect": "append full index/command/ok/result-or-sidecar-reference/error history row, mark dirty; no immediate full-state write",
            "historical_named_query_groups_current_source": "army_query, war_results_query, war_termination_query are ordinary query-* families; the successful current source path defers them",
            "private_queries": "no blanket private-query exemption: several pure private readers do not record a Driver row; private-query-player-lifestyle-receipt-v1 explicitly records an applied once-action receipt and remains a full barrier",
            "why_not_flush_each_query": "would add I/O to the existing deferred path, without evidence that it removes any of the observed 21 writes"},
        "current_direct_barriers": barrier_calls,
        "preserved_state": {
            "history": "all ordered contiguous rows, complete values and original success/error evidence; valid Army sidecar reference and its independently preserved body remain required",
            "scalars": ["format_version", "pipe_name", "bridge_pid", "episode_character_id", "episode_run_id", "last_checkpoint", "rollback_war_failure", "managed_restore_transaction", "succession_expectation", "succession_lifecycle", "campaign_goal", "rollback_war_failures when present"],
            "excluded_from_deferred_optimization": ["SAVE and checkpoint anchors", "restore and cross-process identity", "actions/once intent, pending and applied receipt transitions", "failed or unknown commands", "old-prefix history edits", "normal close"]},
        "existing_WAL_generalization": {
            "append_delta_source": ast.get_source_segment(helper_source, helper_functions["append_delta"]),
            "already_generic": True,
            "backlog": "the integration copies history[committed_rows:] plus every scalar field, so successful deferred queries already travel with the next eligible timeline append",
            "capacity": {"max_delta_bytes": 262144, "max_journal_bytes": 8388608,
                         "over_limit": "JournalCapacity requests the unchanged full-state barrier; no field truncation or silent omission"},
            "large_payload_limit": "a pending full combat result can exceed the delta cap and force full consolidation; no qualified lossless-reference contract is added here"},
        "multi_day_policy_gap": {
            "old_source_is_not_exact_day_only": True,
            "old_source_gate": 'ok and (step in {"life-advance", "life-advance-one-day"} or parsed committed-route or strict route-horizon eligibility)',
            "new_generic_step": "life-advance", "new_clock_leaf": "campaign_deadline_native_clock_v1",
            "observation": "new multi-day generic results reach the old unconditional membership branch if WAL is enabled; old one-day tests do not qualify them",
            "minimum_reviewable_change": "replace the unconditional generic membership by an explicit timeline-result predicate; reuse append_delta and its current base/journal/restore protocol",
            "required_complete_campaign_deadline_case": [
                "exact known step/result step and successful ordinary composite",
                "clock schema xar.ck3.campaign-native-date-clock/v1 and campaign_date_deadline scope",
                "whole-day start < end == target, 1..45 days, elapsed_days == requested_horizon_days == delta/24",
                "campaign ID/calendar/start/target/boundary/endpoint metadata agrees with the configured campaign cap",
                "armed/stopped generation, mode, speed and dates agree; watch army count 0 and combat count 0",
                "stopped triggered solely by date_deadline, flags 1, signed delta 0, overshoot 0, ticks == elapsed days",
                "pause observed, wrapper ownership valid, no terminal/abnormal/early-boundary cancellation",
                "final paused map, no active/pending/ordinary events, event_resolution none, no top-modal hint or identity materialization",
                "no effect-bearing action in the recorded actions list; every row and scalar is retained"
            ],
            "fallback": "any missing/unknown/interrupted/modal/effect-bearing path retains the full barrier; no action is resent",
            "still_needed": ["29-day, 5-day and month-clipped software eligibility cases using the current result contract", "early-modal/zero-day/cancel/overshoot/wrong-generation negative cases", "actual future source tuple adoption and natural timing; no present-game credit"]},
        "failed_full_barrier_boundary": {
            "existing_guard": "after successful consolidation-marker publication, document.consolidated_sha256 already prevents a later append",
            "remaining_pre_marker_case": "if an older history row was edited and full persistence fails before that marker is installed, or while only the v2 in-memory header exists, a later suffix-only append cannot encode the edited old prefix",
            "minimum_reviewable_change": "an experimental requires_full_barrier flag is set before any requested full barrier; only a successful full base replacement clears it; _try refuses append while it is set",
            "effect": "retrying storage on a later permitted barrier preserves current state without resubmitting the original native action",
            "qualification": "source-risk audit only, not reproduced in this no-test work package"},
        "proposal_scope": {"production_or_frozen_source_modified": False, "WAL_enabled": False,
                           "new_generic_storage_layer": False, "query_flush_added": False,
                           "implementation_target": "future review of the existing experimental bridge-native_driver.py.patch policy and barrier guard only"},
        "validation": {"explicit_source_checks": 7, "direct_persist_calls_classified": len(barrier_calls),
                       "benchmarks": 0, "new_fault_tests": 0, "game_or_native_or_RPC_calls": 0},
        "source_pins": pins,
        "storage": {"policy_version": "1.0.0", "shared_research_remaining_pool_bytes": 134217728,
                    "output_limit_bytes": 65536, "record_review_at_utc": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 4320 * 3600, timezone.utc).isoformat(),
                    "large_or_runtime_inputs_read": False, "deletions": 0}
    }
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(encoded) <= 65536)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes(encoded)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(encoded),
                      "persist_calls": len(barrier_calls), "per_query_flush_recommended": False,
                      "WAL_primitive_already_generic": True, "benchmarks": 0}))


if __name__ == "__main__":
    main()
