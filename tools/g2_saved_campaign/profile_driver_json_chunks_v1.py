"""One bounded offline JSON equivalence/write/CPU/memory qualification.

Evidence is synthetic software measurement, not a game-throughput result. The
existing small P49 timing projection supplies a separate historical wall budget.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import tracemalloc
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ck3_autonomous_player"
sys.path[:0] = [str(PROJECT / "src"), str(PROJECT / "tests/unit")]
from xar_autoplayer.bridge import army_query_history_store as store
from xar_autoplayer.bridge import combat_history_superseded_v1 as combat
from xar_autoplayer.bridge.bounded_json_chunks_v1 import MAX_FAST_CHUNK_BYTES, iter_bounded_json_chunks_v1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original_function(commit, path, name, namespace):
    source = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT).decode("utf-8-sig")
    node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name)
    scope = dict(namespace)
    exec(compile(ast.Module(body=[node], type_ignores=[]), f"{commit}:{path}", "exec"), scope)
    return scope[name], {"commit": commit, "path": path,
                         "function_sha256": sha(ast.get_source_segment(source, node).encode())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    admitted = args.admission.read_bytes()
    admission_text = admitted.decode("utf-8-sig").replace("\\\\", "/").replace("\\", "/").lower()
    require(machine.lower() in admission_text and args.work_root.as_posix().lower() in admission_text,
            "admission must bind this machine and exact controlled work root")
    args.work_root.mkdir(parents=True, exist_ok=False)
    disk_before = shutil.disk_usage(args.work_root)
    old_writer, writer_pin = original_function(args.baseline,
        "ck3_autonomous_player/src/xar_autoplayer/bridge/army_query_history_store.py", "write_json_exclusive", store.__dict__)
    old_digest, digest_pin = original_function(args.baseline,
        "ck3_autonomous_player/src/xar_autoplayer/bridge/combat_history_superseded_v1.py", "_digest", combat.__dict__)
    tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_bounded_json_chunks_v1"))
    require(tests.wasSuccessful(), "JSON chunk contract regression failed")
    payload = {"schema": "synthetic-stream-serialization-workload/v1", "unicode": "琉焰🦁\n",
               "rows": [{"index": index, "stats": list(range(2048)),
                         "contexts": [{"identity": index * 100 + prop, "signed_raw": -100000 + prop,
                                       "ready": prop % 3 != 0, "source": "complete retained source",
                                       "damage": 1.25, "toughness": -0.0, "nullable": None}
                                      for prop in range(24)]}
                        for index in range(256)]}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(len(encoded) <= 4 * 1024 * 1024, "synthetic body exceeds its admitted limit")
    expected_digest = sha(encoded)
    write_results = []
    for label, writer in (("old", old_writer), ("new", store.write_json_exclusive)):
        path = args.work_root / f"{label}-sidecar.json"
        budget = store.ByteBudget(4 * 1024 * 1024)
        tick = time.perf_counter_ns()
        reference = writer(path, payload, budget=budget)
        elapsed = (time.perf_counter_ns() - tick) / 1e9
        require(path.read_bytes() == encoded, label + " writer changed complete bytes")
        require(reference["sha256"] == expected_digest and reference["bytes"] == len(encoded), label + " writer receipt differs")
        require(budget.used == len(encoded), label + " budget accounting changed")
        write_results.append({"source": label, "elapsed_seconds": elapsed,
                              "bytes": reference["bytes"], "sha256": reference["sha256"], "budget_used": budget.used})
    budget_failures = []
    for label, writer in (("old", old_writer), ("new", store.write_json_exclusive)):
        path = args.work_root / f"{label}-budget-partial.json"
        budget = store.ByteBudget(1536 * 1024)
        try:
            writer(path, payload, budget=budget)
        except store.SidecarBudgetExhaustedError as error:
            body = path.read_bytes()
            budget_failures.append({"source": label, "error": type(error).__name__, "bytes": len(body),
                                    "sha256": sha(body), "budget_used": budget.used})
        else:
            raise ValueError(label + " writer ignored the admitted byte limit")
    require({key: value for key, value in budget_failures[0].items() if key != "source"}
            == {key: value for key, value in budget_failures[1].items() if key != "source"},
            "budget refusal or preserved partial bytes changed")
    digest_samples = {"old": [], "new": []}
    for group in range(3):
        for label, fn in (("old", old_digest), ("new", combat._digest)) if group % 2 == 0 else (("new", combat._digest), ("old", old_digest)):
            tick = time.perf_counter_ns()
            digest, size = fn(payload, 4 * 1024 * 1024)
            digest_samples[label].append((time.perf_counter_ns() - tick) / 1e9)
            require(digest == sha(canonical) and size == len(canonical), label + " canonical digest changed")
    memory = []
    for label in ("old", "new"):
        encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))
        chunks = encoder.iterencode(payload) if label == "old" else iter_bounded_json_chunks_v1(payload, encoder)
        max_piece, count, size = 0, 0, 0
        digest = hashlib.sha256()
        tracemalloc.start()
        for text in chunks:
            raw = text.encode("utf-8")
            max_piece = max(max_piece, len(raw))
            count += 1
            size += len(raw)
            digest.update(raw)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        require(digest.hexdigest() == sha(encoded[:-1]) and size == len(encoded) - 1,
                label + " memory probe changed bytes")
        memory.append({"source": label, "peak_traced_additional_bytes": peak,
                       "max_text_piece_utf8_bytes": max_piece, "text_pieces": count})
    require(memory[1]["max_text_piece_utf8_bytes"] <= MAX_FAST_CHUNK_BYTES, "grouped fast piece exceeds its declared bound")
    require(memory[1]["peak_traced_additional_bytes"] <= 2 * 1024 * 1024,
            "synthetic encoder added more than its controlled memory allowance")
    p49_path = ROOT / "docs/ck3-native-ai/evidence/p49-settled-performance.json"
    stage_path = ROOT / "docs/ck3-native-ai/evidence/p49-stage-slice.json"
    p49 = json.loads(p49_path.read_bytes())
    stages = json.loads(stage_path.read_bytes())
    settled = p49["5104-5165"]
    day_count = settled["game_days"]
    stage = {row["stage"]: row for row in stages["stages"]}
    selected_sources = [PROJECT / "src/xar_autoplayer/bridge/bounded_json_chunks_v1.py",
                        PROJECT / "src/xar_autoplayer/bridge/army_query_history_store.py",
                        PROJECT / "src/xar_autoplayer/bridge/combat_history_superseded_v1.py",
                        PROJECT / "tests/unit/test_bounded_json_chunks_v1.py", Path(__file__)]
    source_pins = []
    for path in selected_sources:
        raw = path.read_bytes()
        source_pins.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    manifest = [{"relative_path": path.name, "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
                for path in sorted(args.work_root.iterdir()) if path.is_file()]
    retained = sum(item["bytes"] for item in manifest)
    result = {"schema": "xar.bounded-json-chunks-software-performance.v1", "machine_id": machine,
              "observed_started_utc": started, "observed_ended_utc": datetime.now(timezone.utc).isoformat(),
              "evidence_layer": "exact-source old/new offline synthetic JSON write/digest and traced additional encoder allocation; not game throughput",
              "baseline_sources": [writer_pin, digest_pin], "source_pins": source_pins,
              "input": {"schema": payload["schema"], "bytes_including_newline": len(encoded), "sha256": expected_digest,
                        "rows": 256, "integer_values_per_row": 2048, "flat_contexts_per_row": 24, "all_data_synthetic": True},
              "unit_tests": {"run": tests.testsRun, "failures": len(tests.failures), "errors": len(tests.errors)},
              "actual_create_only_writes": write_results, "budget_refusals": budget_failures,
              "canonical_digest": {"bytes": len(canonical), "sha256": sha(canonical), "alternating_groups": 3,
                                   "samples_seconds": digest_samples,
                                   "median_seconds": {key: statistics.median(value) for key, value in digest_samples.items()}},
              "memory_probe": {"scope": "encoder chunks plus UTF-8/hash consumption; input graph and expected bytes allocated before tracing",
                               "sources": memory, "maximum_grouped_fast_text_bytes": MAX_FAST_CHUNK_BYTES,
                               "oversized_scalar_limit": "a single oversized string retains the original encoder fallback/allocation behavior"},
              "historical_wall_budget": {"source_machine_id": p49.get("machine_id", "unknown"),
                  "stage_source_machine_id": stages.get("machine_id", "unknown"), "game_days": day_count,
                  "wall_seconds": settled["wall_seconds"], "seconds_per_actual_day": settled["wall_seconds"] / day_count,
                  "phase_goal_seconds_per_actual_day": 1.0, "phase_goal_budget_seconds": day_count,
                  "gap_to_phase_goal_seconds": settled["wall_seconds"] - day_count,
                  "later_goal_seconds_per_actual_day": 0.5, "later_goal_gap_seconds": settled["wall_seconds"] - day_count * 0.5,
                  "full_persistence_sum_seconds": stage["driver.full_state_persistence"]["nested_elapsed_sum_seconds"],
                  "stream_write_sum_seconds": stage["driver.full_state_temp_stream_write"]["nested_elapsed_sum_seconds"],
                  "plan_unique_wall_seconds": stages["plan_intervals"]["unique_wall_seconds"],
                  "date_changed_wait_seconds": stages["public_change_wait_by_calendar_delta"]["date_changed"]["elapsed_seconds"],
                  "limits": ["stages overlap, so they are not added into wall", "zero-day counts do not establish persistence causality", "no synthetic encoding gain is extrapolated to historical or current game days"]},
              "current_runtime": {"new_AUTO_sample_received": False, "game_or_native_or_RPC_calls": 0,
                                  "live_Driver_or_SAVE_reads": 0, "frozen_source_modified": False, "deployed": False},
              "storage": {"policy_version": "1.0.0", "admission_path": str(args.admission), "admission_sha256": sha(admitted),
                          "work_root": str(args.work_root), "package_max_bytes": 16777216,
                          "retained_logical_bytes_before_receipt": retained, "allocated_bytes": None,
                          "free_at_start_bytes": disk_before.free, "free_at_close_bytes": shutil.disk_usage(args.work_root).free,
                          "producer_closed": True, "unconsumed_planned_writes_bytes": 0,
                          "derived_review_at_utc": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 48 * 3600, timezone.utc).isoformat(),
                          "deletions": 0, "manifest": manifest}}
    receipt = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(retained + len(receipt) <= 16777216 and len(receipt) <= 65536, "finite research package budget exceeded")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes(receipt)
    (args.work_root / "QUALIFICATION.json").write_bytes(receipt)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(receipt), "input_bytes": len(encoded),
                      "writes": write_results, "digest_median_seconds": result["canonical_digest"]["median_seconds"],
                      "memory": memory, "retained_logical_bytes": retained + len(receipt)}))


if __name__ == "__main__":
    main()
