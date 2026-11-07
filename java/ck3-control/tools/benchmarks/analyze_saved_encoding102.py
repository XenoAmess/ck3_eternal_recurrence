"""Analyze every raw sample from the one authorized immutable-DATA benchmark."""
import hashlib
import json
from pathlib import Path
import statistics
import sys

def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def inside(path):
    # Pure local analysis: only explicitly named paths, no process or network access.
    return Path(path).expanduser().resolve()


def main():
    if len(sys.argv) != 4:
        raise ValueError("stdout.bin ACTUAL.json new-summary.json required")
    source, actual_path, target = map(inside, sys.argv[1:])
    if target.exists():
        raise ValueError("preserve prior analysis; new output required")
    raw = source.read_bytes()
    if not 0 < len(raw) <= 16 * 1024:
        raise ValueError("bounded complete original stdout required")
    rows = [json.loads(line, object_pairs_hook=unique) for line in raw.decode("utf-8").splitlines()]
    if len(rows) != 21:
        raise ValueError("all21 planned records required; do not omit a failed or slow operation")
    by_event = {}
    for row in rows:
        by_event.setdefault(row["event"], []).append(row)
    if set(by_event) != {"benchmark_begin", "setup", "warmup", "sample", "round_end", "benchmark_end"}:
        raise ValueError("unexpected or failed operation remains in raw output")
    setup, end, begin = by_event["setup"][0], by_event["benchmark_end"][0], by_event["benchmark_begin"][0]
    if setup["driver_sha256"] != "092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4":
        raise ValueError("wrong immutable Driver")
    if setup["pair_sha256"] != "be81b46ed5bd7c5d6bc4a5d7125a5c3f649bacaf8d3686f63f40b20ddd6764a6":
        raise ValueError("wrong immutable Pair")
    for phase in ("warmup", "sample"):
        operations = by_event[phase]
        if len(operations) != 8:
            raise ValueError("all8 operations required")
        for round_number, order in ((0, "ABAB"), (1, "BABA")):
            group = [r for r in operations if r["round"] == round_number]
            if "".join(r["mode"] for r in group) != order or [r["ordinal"] for r in group] != list(range(4)):
                raise ValueError("fixed counterbalanced raw order required")
        for row in operations:
            if row["marker"] != setup["expected_marker"] or type(row["component_ns"]) is not int or row["component_ns"] <= 0:
                raise ValueError("actual equal encoded markers and positive nanoseconds required")
    if not end["all_markers_equal"] or end["speed_assertion"] is not False:
        raise ValueError("marker contract only, never speed assertions")
    actual_raw = actual_path.read_bytes()
    if not 0 < len(actual_raw) <= 1024 * 1024:
        raise ValueError("bounded managed ACTUAL required")
    actual = json.loads(actual_raw, object_pairs_hook=unique)
    if actual["exit_code"] != 0 or actual["timeout"] or not actual["contract_accepted"]:
        raise ValueError("preserve incomplete/failed process without producing a success summary")
    summary = {}
    for mode in "AB":
        samples = [r["component_ns"] for r in by_event["sample"] if r["mode"] == mode]
        if len(samples) != 4 or sum(samples) != end[mode.lower() + "_component_sum_ns"]:
            raise ValueError("all four raw samples must match original totals")
        summary[mode] = {"raw_ns_in_original_order": samples, "count": 4, "sum_ns": sum(samples),
                         "mean_ns": statistics.mean(samples), "median_ns": statistics.median(samples),
                         "minimum_ns": min(samples), "maximum_ns": max(samples)}
    result = {"schema": "xar.p102.one-jvm-component-all-samples/v1", "raw_stdout": pin(source),
              "managed_actual": pin(actual_path), "begin": begin, "setup": setup,
              "all_raw_records": rows, "samples": summary, "process_seconds": actual["seconds"],
              "descriptive_A_mean_over_B_mean": summary["A"]["mean_ns"] / summary["B"]["mean_ns"],
              "limits": "One JVM/fixed input/shared first-buffer harness; all warmups and slow samples retained. Component timers exclude output/checksum, main/process totals include them. No whole pipeline, old production binary, causal Runtime or saved-day gain claim.",
              "runtime_operations": 0}
    with target.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": pin(target), "samples": summary, "process_seconds": actual["seconds"]}))


if __name__ == "__main__":
    main()
