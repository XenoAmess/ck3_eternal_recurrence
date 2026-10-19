"""One bounded, offline comparison of the exact old/new faction lookup.

Reads the tracked 673/674 small projection and a fixed Git source, never a
Driver file, SAVE, native endpoint, or game. Timings describe this local lookup.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ck3_autonomous_player"
sys.path[:0] = [str(PROJECT / "src"), str(PROJECT / "tests/unit")]

from xar_autoplayer import strategy
from test_faction_alert_history_lookup_v1 import fixture_inputs, query_row
from test_war_entry_faction_watch_scope_12003 import _synthetic_candidate_on_actual_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    machine = subprocess.check_output(
        [sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"],
        cwd=ROOT, text=True).strip()
    disk_before = shutil.disk_usage(ROOT)
    path = "ck3_autonomous_player/src/xar_autoplayer/strategy.py"
    baseline = subprocess.check_output(["git", "show", f"{args.baseline}:{path}"], cwd=ROOT).decode("utf-8-sig")
    old_node = next(node for node in ast.parse(baseline).body
                    if isinstance(node, ast.FunctionDef) and node.name == "_same_frame_player_faction_alerts")
    namespace = dict(strategy.__dict__)
    exec(compile(ast.Module(body=[old_node], type_ignores=[]), "fixed-git-baseline", "exec"), namespace)
    old = namespace[old_node.name]
    new = strategy._same_frame_player_faction_alerts
    snapshot, result = fixture_inputs()
    row = query_row(result)
    auto = query_row(result, auto=True)
    noisy = [{"command": "life-advance", "ok": True}] * 8849
    cases = [
        ("latest-direct", [row], snapshot),
        ("latest-auto", [auto], snapshot),
        ("recent-four-of-8853", noisy + [row] + noisy[:3], snapshot),
        ("no-current-history-or-snapshot", noisy, snapshot),
        ("snapshot-only", noisy, {**snapshot, "player_faction_alerts": result["player_faction_alerts"]}),
        ("not-paused", [row], {**snapshot, "paused": False}),
        ("bool-actor", [row], {**snapshot, "played_character": {"character_id": True}}),
        ("none-snapshot", [row], None),
        ("malformed-latest", [row, query_row({"player_faction_alerts": {}})], snapshot),
        ("failed-latest", [row, {**auto, "ok": False}], snapshot),
    ]
    for key in ("queried_snapshot_id", "queried_revision", "queried_native_revision"):
        changed = copy.deepcopy(result)
        changed[key] = "wrong" if key == "queried_snapshot_id" else 7
        cases.append(("wrong-" + key, [row, query_row(changed, auto=True)], snapshot))
    for key in ("date_raw", "snapshot_revision", "player_character_id"):
        changed = copy.deepcopy(result)
        changed["player_faction_alerts"][key] += 1
        cases.append(("wrong-leaf-" + key, [row, query_row(changed)], snapshot))
    equality = []
    for name, rows, snap in cases:
        before = copy.deepcopy((rows, snap))
        expected, actual = old(rows, snap), new(rows, snap)
        assert actual == expected, name
        assert (rows, snap) == before, name
        equality.append({"case": name, "equal": True, "input_unchanged": True,
                         "result_bytes": len(json.dumps(actual, ensure_ascii=False).encode("utf-8"))})
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for module in ("test_faction_alert_history_lookup_v1",):
        suite.addTests(loader.loadTestsFromName(module))
    checked = unittest.TextTestRunner(verbosity=2).run(suite)
    assert checked.wasSuccessful(), "focused checks failed"
    fixture = PROJECT / "tests/fixtures/faction_watch_current_673_674.json"
    plan_snapshot = _synthetic_candidate_on_actual_frame(json.loads(fixture.read_text()))
    plan_rows = [{"index": 1, "command": "save-checkpoint", "ok": True}, auto]
    steps = {"declare-war-808-17-0", "life-advance", strategy.QUERY_PLAYER_FACTION_ALERTS_V1_STEP}
    with mock.patch.object(strategy, "_same_frame_player_faction_alerts", old):
        old_plan = strategy.choose_one_life_turn(plan_rows, snapshot=plan_snapshot, action_steps=steps)
    new_plan = strategy.choose_one_life_turn(plan_rows, snapshot=plan_snapshot, action_steps=steps)
    assert old_plan == new_plan, "complete existing faction watch plan changed"
    timings = []
    for name, rows, snap in (cases[2], cases[3], cases[4]):
        samples = {"old": [], "new": []}
        for group in range(9):
            for label, fn in (("old", old), ("new", new)) if group % 2 == 0 else (("new", new), ("old", old)):
                tick = time.perf_counter_ns()
                for _ in range(100):
                    fn(rows, snap)
                samples[label].append((time.perf_counter_ns() - tick) / 100 / 1e6)
        visits = {}
        for label, fn in (("old", old), ("new", new)):
            target = namespace if label == "old" else strategy.__dict__
            with mock.patch.dict(target, {"_effective_command": mock.Mock(wraps=strategy._effective_command)}):
                fn(rows, snap)
                visits[label] = target["_effective_command"].call_count
        timings.append({"case": name, "history_rows": len(rows),
                        "old_median_ms": statistics.median(samples["old"]),
                        "new_median_ms": statistics.median(samples["new"]),
                        "unpack_calls": visits, "per_group_iterations": 100, "alternating_groups": 9})
    receipt = {
        "schema": "xar.faction-alert-history-lookup-performance.v1",
        "machine_id": machine, "observed_started_utc": started,
        "observed_ended_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_commit": args.baseline, "baseline_function_sha256": hashlib.sha256(ast.get_source_segment(baseline, old_node).encode()).hexdigest(),
        "source_path": path, "source_sha256_at_verification": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
        "input": {"path": fixture.relative_to(ROOT).as_posix(), "bytes": fixture.stat().st_size,
                  "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  "scope": "actual small 1.20.0.3 projection; repeated history filler is synthetic"},
        "equal_cases": equality,
        "focused_tests": {"run": checked.testsRun, "failures": len(checked.failures), "errors": len(checked.errors)},
        "existing_war_watch_plan": {"baseline_equals_new": old_plan == new_plan,
                                    "baseline_selected_step": old_plan["selected_step"],
                                    "new_selected_step": new_plan["selected_step"],
                                    "prior_test_expected_step": "declare-war-808-17-0",
                                    "prior_test_result": "existing test first failed on new helper; replayed complete first plan is equal with baseline, so that first assertion also fails there; remaining test assertions not replayed"},
        "timings": timings,
        "native_calls": 0, "game_calls": 0, "deployed": False,
        "limits": ["local lookup timings only; no games/day throughput claim", "no shared plan cache or query/strategy change", "missing/snapshot paths still scan all history"],
        "storage": {"policy_version": "1.0.0", "peak_budget_bytes": 1048576,
                    "free_at_start_bytes": disk_before.free, "free_at_close_bytes": shutil.disk_usage(ROOT).free,
                    "large_inputs_read": False, "deletions": 0,
                    "record_review_at_utc": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 4320 * 3600, timezone.utc).isoformat()},
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    assert len(encoded.encode()) <= 1048576
    args.receipt.write_text(encoded, encoding="utf-8")
    print(json.dumps({"receipt": str(args.receipt), "tests": checked.testsRun, "equal_cases": len(equality), "timings": timings}, ensure_ascii=False))


if __name__ == "__main__":
    main()
