"""Offline production-schema fixture equality/copy/refusal/CPU qualification.

Synthetic software evidence only; no native RPC, live input, or game-day claim.
The enriched-input branch still fully recomputes and compares derived values.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ck3_autonomous_player"
sys.path[:0] = [str(PROJECT / "src"), str(PROJECT / "tests/unit")]
from xar_autoplayer.bridge import combat_phase_contract as phase
import test_combat_phase_inputs_v3_production_contract as production_fixture
import test_knight_stat_consumption_stage_lineage_12004 as knight_fixture

SOURCE = "ck3_autonomous_player/src/xar_autoplayer/bridge/combat_phase_contract.py"
NAME = "normalize_combat_simulation_inputs_v3"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def mutable_ids(value):
    found, stack = set(), [value]
    while stack:
        item = stack.pop()
        if type(item) in (dict, list) and id(item) not in found:
            found.add(id(item))
            stack.extend(item.values() if type(item) is dict else item)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--negative-guard", action="store_true")
    args = parser.parse_args()
    require(not args.negative_guard, "intentional optimized verifier rejection")
    started = datetime.now(timezone.utc).isoformat()
    source = subprocess.check_output(["git", "show", f"{args.baseline}:{SOURCE}"], cwd=ROOT).decode("utf-8-sig")
    node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == NAME)
    scope = dict(phase.__dict__)
    exec(compile(ast.Module(body=[node], type_ignores=[]), f"{args.baseline}:{SOURCE}", "exec"), scope)
    old = scope[NAME]
    # Its recursive canonical-to-wire validation must also use the old function.
    scope[NAME] = old
    new = phase.normalize_combat_simulation_inputs_v3
    wire, encounter = production_fixture._production_payload()
    leaf = knight_fixture._wire()
    event = leaf["events"][0]
    leaf["events"] = [dict(copy.deepcopy(event), sequence=str(i)) for i in range(1, 9)]
    leaf["latest_sequence"] = "8"
    wire["base_inputs"]["knight_stat_consumption_v1"] = leaf
    kwargs = {"expected_target_province_id": wire["base_inputs"]["target_province_id"],
              "expected_attacker_entry_province_id": wire["base_inputs"]["scenario"]["attacker_entry_province_id"],
              "expected_encounter_scope": encounter}
    before_wire = encoded(wire)
    require(len(before_wire) <= 4 * 1024 * 1024, "synthetic wire exceeds finite bound")
    canonical = old(wire, **kwargs)
    require(encoded(wire) == before_wire, "baseline wire normalization mutated its input")
    expected = encoded(canonical)
    print(json.dumps({"wire_bytes": len(before_wire), "canonical_bytes": len(expected)}))
    require(encoded(new(wire, **kwargs)) == expected and encoded(wire) == before_wire,
            "new wire path changed bytes or mutated its input")
    require(len(expected) <= 4 * 1024 * 1024, "canonical fixture exceeds finite bound")
    input_ids = mutable_ids(canonical)
    samples = {"old": [], "new": []}
    for group in range(3):
        functions = (("old", old), ("new", new)) if group % 2 == 0 else (("new", new), ("old", old))
        for label, fn in functions:
            tick = time.perf_counter_ns()
            output = fn(canonical, **kwargs)
            samples[label].append((time.perf_counter_ns() - tick) / 1e9)
            require(encoded(output) == expected and encoded(canonical) == expected,
                    label + " changed canonical bytes or its input")
            require(not mutable_ids(output) & input_ids, label + " output aliases mutable input")
    rejected = []
    for case in ("phase_schema", "missing_derived", "derived_drift", "raw_numeric", "phase_derived_drift"):
        value = copy.deepcopy(canonical)
        if case == "phase_schema":
            value["phase_event_inputs"] = None
        elif case == "missing_derived":
            value["phase_event_inputs"].pop("row_evaluations")
        elif case == "derived_drift":
            value["completeness"]["planner_usable"] = True
        elif case == "raw_numeric":
            value["base_inputs"]["knight_stat_consumption_v1"]["events"][0]["contexts"][0]["operand_raw"] = "malformed"
        else:
            value["phase_event_inputs"]["row_evaluations"]["status"] = "tampered"
        before = encoded(value)
        errors = []
        for label, fn in (("old", old), ("new", new)):
            try:
                fn(value, **kwargs)
            except ValueError as error:
                errors.append((type(error).__name__, str(error)))
            else:
                raise ValueError(case + " was not rejected by " + label)
            require(encoded(value) == before, case + " rejection mutated input")
        require(errors[0] == errors[1], case + " refusal changed")
        rejected.append({"case": case, "same_exception_and_message": True,
                         "exception": errors[0][0], "message": errors[0][1], "input_unchanged": True})
    unavailable = copy.deepcopy(wire)
    unavailable_phase = unavailable["phase_event_inputs"]
    unavailable_phase.update(status="unavailable", raw=None, advantage_model=None, unavailable_reason="synthetic unavailable")
    unavailable = old(unavailable, **kwargs)
    unavailable_before = encoded(unavailable)
    for label, fn in (("old", old), ("new", new)):
        output = fn(unavailable, **kwargs)
        require(encoded(output) == unavailable_before and encoded(unavailable) == unavailable_before,
                label + " unavailable branch changed bytes/input")
        require(not mutable_ids(output) & mutable_ids(unavailable), label + " unavailable output aliases input")
    memory = []
    for label, fn in (("old", old), ("new", new)):
        tracemalloc.start()
        output = fn(canonical, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        require(encoded(output) == expected, label + " memory probe changed bytes")
        memory.append({"source": label, "peak_traced_additional_bytes": peak})
    pins = []
    for path in (ROOT / SOURCE, Path(production_fixture.__file__), Path(knight_fixture.__file__),
                 PROJECT / "tests/unit/test_combat_phase_inputs_v3_contract.py", Path(__file__)):
        raw = path.read_bytes()
        pins.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)})
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    result = {"schema": "xar.combat-v3-revalidation-copy-software.v1", "machine_id": machine,
        "observed_started_utc": started, "observed_ended_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_layer": "offline valid synthetic production-schema old/new bytes, refusal, isolation, CPU and traced allocation",
        "baseline": {"commit": args.baseline, "path": SOURCE, "function": NAME,
                     "function_sha256": digest(ast.get_source_segment(source, node).encode())},
        "source_pins": pins,
        "input": {"source": "existing production + knight stage-lineage fixture builders; ring expanded to 8 distinct ordered sequences",
                  "all_synthetic": True, "wire_bytes": len(before_wire), "canonical_bytes": len(expected),
                  "wire_sha256": digest(before_wire), "canonical_sha256": digest(expected), "knight_events": 8},
        "equivalence": {"successful_wire_and_enriched_bytes_equal": True, "unavailable_bytes_equal": True,
                        "input_unchanged": True, "output_mutable_graph_disjoint_from_input": True,
                        "full_recompute_and_derived_comparison_retained": True, "rejected": rejected},
        "cpu": {"alternating_groups": 3, "samples_seconds": samples,
                "median_seconds": {label: statistics.median(values) for label, values in samples.items()}},
        "memory": {"scope": "traced complete revalidation call; prebuilt fixture excluded; not RSS", "sources": memory},
        "read_only_source_basis": ["combat_contract normalizers build canonical values and deepcopy at return:669",
            "phase _normalize_raw constructs new raw values; _normalize_phase_event_inputs copies advantage before adapting origin:715-725",
            "only root/phase shells lose derived keys; recursive normalization/recomputed!=value/final deepcopy:510-607 unchanged"],
        "limits": ["valid fixture and five malformed mutations do not qualify every possible external object subclass",
                   "not an actual 25MB query or game-throughput result; no size-linear extrapolation",
                   "input graphs are expected stable for the duration of their existing synchronous validation call"],
        "game_native_or_RPC_calls": 0, "live_Driver_or_SAVE_reads": 0, "frozen_source_modified": False, "deployed": False,
        "storage": {"external_writes_bytes": 0, "synthetic_body_written": False, "max_repo_leaf_bytes": 49152,
                    "producer_closed": True, "unconsumed_planned_writes_bytes": 0}}
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(raw) <= 16384 and Path(__file__).stat().st_size <= 12288, "finite verifier/receipt budget exceeded")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(raw), "canonical_bytes": len(expected),
                      "median_seconds": result["cpu"]["median_seconds"], "memory": memory, "refusals": len(rejected)}))


if __name__ == "__main__":
    main()
