"""Bounded exact-source A/B for earlier stale combat cache rejection."""
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

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ck3_autonomous_player"
sys.path[:0] = [str(PROJECT / "src"), str(PROJECT / "tests/unit")]
from xar_autoplayer.bridge import native_driver as native
from test_stale_combat_frame_rejection_v1 import inputs, names, harness
from test_knight_stat_consumption_stage_lineage_12004 import _wire


def expanded_consumption():
    """Synthetic valid 32-event ring; never a claim about observed CK3 values."""
    wire = _wire()
    event = wire["events"][0]
    for context in event["contexts"]:
        context.pop("preparation_stage_lineage")
        context.pop("preparation_capture_at_consumption")
        pc = context["consumed_pc"]
        pc["count_i32"] = 2048
        pc["properties"] = {"keys_u16": list(range(2048)), "values_q64": [0] * 2048}
    wire["events"] = []
    for sequence in range(1, 33):
        item = copy.deepcopy(event)
        item["sequence"] = str(sequence)
        wire["events"].append(item)
    wire["latest_sequence"] = "32"
    return wire


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    disk_before = shutil.disk_usage(ROOT)
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True, cwd=ROOT).strip()
    path = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
    source = subprocess.check_output(["git", "show", f"{args.baseline}:{path}"], cwd=ROOT).decode("utf-8-sig")
    cls = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == "NativeHeadlessGameplayDriver")
    old = {}
    pins = {}
    for version in (2, 3):
        method = names(version)[1]
        node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method)
        namespace = dict(native.__dict__)
        exec(compile(ast.Module(body=[node], type_ignores=[]), "fixed-git-baseline", "exec"), namespace)
        old[version] = namespace[method]
        pins[method] = hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest()
    results = []
    for version in (2, 3):
        snapshot, cache = inputs(version)
        cases = [("current-valid", snapshot, cache), ("unpaused", {**snapshot, "paused": False}, cache)]
        for key in ("native_revision", "snapshot_id", "revision", "connection_generation", "episode_run_id"):
            changed = copy.deepcopy(cache)
            changed["cache_binding"][key] = "foreign"
            cases.append(("stale-" + key, snapshot, changed))
        for label, key, value in (("bad-body", "combat_simulation_inputs", {}),
                                  ("bad-sequence", "query_sequence", True),
                                  ("wrong-status", "status", "wrong")):
            cases.append((label, snapshot, {**cache, key: value}))
        target = copy.deepcopy(cache)
        target["cache_binding"]["target_province_id"] += 1
        cases.append(("wrong-target", snapshot, target))
        for label, snap, cached in cases:
            before = copy.deepcopy((snap, cached))
            old_driver, new_driver = harness(version, cached), harness(version, cached)
            field, method, _ = names(version)
            expected = old[version](old_driver, snap, episode_run_id="offline-episode")
            actual = getattr(new_driver, method)(snap, episode_run_id="offline-episode")
            assert expected == actual, (version, label)
            assert getattr(old_driver, field) == getattr(new_driver, field), (version, label, "cache")
            assert (snap, cached) == before, (version, label, "input mutated")
            results.append({"version": version, "case": label, "equal_result": True,
                            "equal_retained_cache": True, "input_unchanged": True})
    checked = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_stale_combat_frame_rejection_v1"))
    assert checked.wasSuccessful(), "focused regression failed"
    snapshot, cache = inputs(2)
    cache["combat_simulation_inputs"]["knight_stat_consumption_v1"] = expanded_consumption()
    # Validate and detach the full synthetic body once before timing either path.
    scope = native.combat_simulation_encounter_scope(snapshot, [12], [22])
    normalized = native.normalize_combat_simulation_inputs(cache["combat_simulation_inputs"], expected_target_province_id=900,
            expected_attacker_entry_province_id=800, expected_encounter_scope=scope)
    cache["combat_simulation_inputs"] = normalized
    body_bytes = len(json.dumps(normalized, separators=(",", ":")).encode())
    assert body_bytes <= 16 * 1024 * 1024
    cache["cache_binding"]["native_revision"] = -1
    field, method, _ = names(2)
    samples = {"old": [], "new": []}
    for group in range(3):
        for label in ("old", "new") if group % 2 == 0 else ("new", "old"):
            driver = harness(2, cache)
            tick = time.perf_counter_ns()
            actual = old[2](driver, snapshot, episode_run_id="offline-episode") if label == "old" else getattr(driver, method)(snapshot, episode_run_id="offline-episode")
            samples[label].append((time.perf_counter_ns() - tick) / 1e9)
            assert actual is None and getattr(driver, field) is None
    receipt = {"schema": "xar.stale-combat-frame-rejection-performance.v1",
               "machine_id": machine, "observed_started_utc": started,
               "observed_ended_utc": datetime.now(timezone.utc).isoformat(),
               "baseline_commit": args.baseline, "baseline_function_sha256": pins,
               "source": {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()},
               "equal_cases": results, "focused_tests": {"run": checked.testsRun, "failures": len(checked.failures), "errors": len(checked.errors)},
               "bounded_synthetic_AB": {"version": 2, "body_json_bytes": body_bytes,
                                        "events": 32, "contexts_per_event": 9, "pc_properties_per_context": 2048,
                                        "source": "test_knight_stat_consumption_stage_lineage_12004._wire expanded in memory; all values synthetic",
                                        "alternating_groups": 3, "iterations_per_group": 1,
                                        "old_seconds": samples["old"], "new_seconds": samples["new"],
                                        "old_median_seconds": statistics.median(samples["old"]),
                                        "new_median_seconds": statistics.median(samples["new"])},
               "same_frame_normalization_retained": True, "shared_plan_cache_added": False,
               "native_or_game_calls": 0, "live_rpc": 0, "large_runtime_bodies_read": 0,
               "deployed": False, "new_game_freeze": "d90d5e79; this candidate is a later batch and is not hot-patched",
               "limits": ["synthetic bounded stale V2 workload, not replay of P67", "no actual games/day claim or attribution of P67 87.814s", "current-frame paths still perform the full original normalization and copying"],
               "storage": {"policy_version": "1.0.0", "memory_body_limit_bytes": 16777216, "output_limit_bytes": 1048576,
                           "free_at_start_bytes": disk_before.free, "free_at_close_bytes": shutil.disk_usage(ROOT).free,
                           "deletions": 0, "record_review_at_utc": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 4320 * 3600, timezone.utc).isoformat()}}
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    assert len(encoded) <= 1048576
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes(encoded)
    print(json.dumps({"receipt": str(args.receipt), "equal_cases": len(results), "tests": checked.testsRun,
                      "body_bytes": body_bytes, "old_median_seconds": statistics.median(samples["old"]),
                      "new_median_seconds": statistics.median(samples["new"])}))


if __name__ == "__main__":
    main()
