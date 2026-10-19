"""Compare the bounded battle-history scan with one fixed Git source version.

Offline only: imports existing small battle fixtures and creates scaling history
in memory. No game, endpoint, native command, save or running SDK is opened.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("ck3_autonomous_player/src/xar_autoplayer/strategy.py")
FUNCTION = "_battle_control_turn_state"
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/tests/unit"))
from xar_autoplayer import strategy


def fixed_baseline(commit: str):
    resolved = subprocess.check_output(
        ["git", "rev-parse", "--verify", commit + "^{commit}"], cwd=ROOT,
        text=True, encoding="utf-8").strip()
    source = subprocess.check_output(
        ["git", "show", resolved + ":" + SOURCE.as_posix()], cwd=ROOT,
        text=True, encoding="utf-8")
    tree = ast.parse(source)
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == FUNCTION)
    module = ast.Module(body=[node], type_ignores=[])
    namespace = dict(vars(strategy))
    exec(compile(module, "fixed-git-baseline/" + SOURCE.as_posix(), "exec"), namespace)
    return namespace[FUNCTION], resolved, hashlib.sha256(
        ast.get_source_segment(source, node).encode("utf-8")).hexdigest()


def scenes():
    from test_battle_reader_unavailable_watch import actual
    actual_projection = actual()
    raw = actual_projection["semantic"]
    failure = actual_projection["unavailable"]
    empty = {"snapshot_id": "synthetic:7", "revision": 7, "native_revision": 7,
             "date_raw": 53144328, "paused": True, "map_ready": True,
             "played_character": {"character_id": 31254, "alive": True,
                 "betrothed_id": None, "primary_spouse_id": 123, "spouse_ids": [123]},
             "active_wars": [], "player_armies": [], "active_event": None,
             "pending_character_interaction": None}
    rows = [{"command": "save-checkpoint", "ok": True, "result": {}}]
    rows += [{"command": "query-unrelated-synthetic", "ok": True, "result": {"small": n}}
             for n in range(8852)]
    advance = {"command": "life-advance-one-day", "ok": True, "result": {}}
    other = {"command": "query-unrelated-synthetic", "ok": True, "result": {}}
    yield "empty", [], empty, []
    yield "no_advances_8853", rows, empty, []
    yield "one_advance", rows + [advance, other], empty, []
    yield "recent_two_advances_8857", rows + [advance, other, advance, other], empty, []
    yield "failed_newer_advance", rows + [advance, other, advance,
        {**advance, "ok": False}, other], empty, []
    yield "auto_turn_advance", rows + [advance, other,
        {"command": "auto-turn", "ok": True,
         "result": {"auto_turn": {"selected_step": "life-advance-one-day", "result": {}}}}], empty, []
    yield "restore_discards_old_window", rows + [advance, advance,
        {"command": "restore-checkpoint", "ok": True, "result": {}}, other], empty, []
    yield "malformed_latest_sentinel", rows + [advance,
        {"command": "battle-decision-epoch-advance-to-53144352", "ok": True,
         "result": {"step": "battle-decision-epoch-advance-to-53144352"}}], empty, []
    yield "closed_P18_actual_unavailable", [{"command": failure["step"],
        "ok": False, "result": failure}], raw, raw["player_armies"]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def run(baseline_commit: str, machine_id: str) -> dict:
    baseline, resolved, baseline_sha = fixed_baseline(baseline_commit)
    candidate = strategy._battle_control_turn_state
    observed = datetime.now(timezone.utc)
    checks = []
    generated = list(scenes())
    for name, rows, snapshot, armies in generated:
        before = _digest((rows, snapshot, armies))
        first = baseline(rows, snapshot, armies)
        second = candidate(rows, snapshot, armies)
        assert first == second, name
        assert _digest((rows, snapshot, armies)) == before, name + " mutated input"
        # Exercise the complete ordinary chooser, not only this scan's result.
        settings = dict(snapshot=snapshot,
            action_steps={"life-advance", "life-advance-one-day", "save-checkpoint",
                          "set-speed-1", "resume-map", "pause-map"},
            bridge_capabilities={"game.command.set-speed-1", "game.command.resume-map",
                                 "game.command.pause-map"})
        with patch.object(strategy, FUNCTION, baseline):
            old_plan = strategy.choose_one_life_turn(rows, **settings)
        with patch.object(strategy, FUNCTION, candidate):
            new_plan = strategy.choose_one_life_turn(rows, **settings)
        assert old_plan == new_plan, name + " ordinary plan differs"
        checks.append({"case": name, "history_rows": len(rows),
            "same_battle_state": True, "same_complete_ordinary_plan": True,
            "input_unchanged": True, "state_sha256": _digest(first),
            "plan_sha256": _digest(old_plan), "selected_step": new_plan.get("selected_step")})
    timings = []
    for name, rows, snapshot, armies in generated:
        if name not in {"no_advances_8853", "recent_two_advances_8857"}:
            continue
        values = {"baseline": [], "candidate": []}
        calls = {}
        for label, implementation in (("baseline", baseline), ("candidate", candidate)):
            original = strategy._is_battle_timeline_advance_step
            def counted(step):
                calls[label] = calls.get(label, 0) + 1
                return original(step)
            with patch.object(strategy, "_is_battle_timeline_advance_step", counted):
                # fixed baseline retains its own namespace.
                previous = baseline.__globals__["_is_battle_timeline_advance_step"]
                baseline.__globals__["_is_battle_timeline_advance_step"] = counted
                try:
                    implementation(rows, snapshot, armies)
                finally:
                    baseline.__globals__["_is_battle_timeline_advance_step"] = previous
        for repeat in range(7):
            order = (("baseline", baseline), ("candidate", candidate))
            if repeat % 2:
                order = tuple(reversed(order))
            for label, implementation in order:
                started = time.perf_counter()
                for _ in range(10):
                    implementation(rows, snapshot, armies)
                values[label].append((time.perf_counter() - started) / 10)
        timings.append({"case": name, "predicate_calls": calls,
            "median_seconds_per_battle_state": {key: statistics.median(value)
                for key, value in values.items()}, "repetitions": 7,
            "calls_per_repetition": 10})
    data = (ROOT / SOURCE).read_bytes()
    return {"schema": "xar.planner-battle-tail-lookup-qualification.v1",
        "machine_id": machine_id, "observed_utc": observed.isoformat(),
        "evidence_kind": "offline closed P18 failure projection and explicitly synthetic scaling histories",
        "baseline_commit": resolved, "baseline_function_sha256": baseline_sha,
        "candidate_source": {"path": SOURCE.as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()},
        "checks": checks, "measurements": timings,
        "native_evaluation_count_before": 0, "native_evaluation_count_after": 0,
        "new_game_or_rpc_calls": 0, "running_sdk_modified": False,
        "live_seconds_per_game_day": None,
        "limits": ["Python function/ordinary-plan equivalence only; no full campaign speed claim.",
            "No-advance miss retains a complete scan; source frame and all existing battle finalizers remain unchanged.",
            "Original full-list expansion returns independently mutable outer rows; no row cache or history pruning added."],
        "storage": {"policy_version": "1.0.0", "body_reads": "fixed Git source plus existing small fixtures only",
            "output_limit_bytes": 1048576, "deletions": 0,
            "review_at_utc": (observed + timedelta(hours=4320)).isoformat()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--machine-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.baseline_commit, args.machine_id)
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(encoded) > 1048576:
        raise ValueError("qualification output exceeds small evidence budget")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"status": "PASS", "checks": len(result["checks"]),
        "measurements": result["measurements"], "output": str(args.output),
        "bytes": len(encoded)}, ensure_ascii=False))
