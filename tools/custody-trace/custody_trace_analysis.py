"""Bounded explicit-DATA explanations of the pinned custody_trace producer.

This source was authored without execution. It is not a native custody oracle.
Input: exactly {"kind":"DATA","caps":[entries,bytes,handles],"trace":[...]};
rows are [id,payload_bytes,pair_bytes], with immutable charges per id.
No request details are emitted unless --detail-limit 1..128 is explicit.

The literal expectations below were hand-authored BEFORE this tool's analysis
implementation, after reading the existing producer and its prior literal oracle.
They are not model-blind. They are static review material, not executed checks.
The policy arithmetic will use that producer directly, not a copied simulator.
"""

# Zero-based reuse distance counts distinct OTHER ids strictly between requests.
# This independent literal arithmetic is deliberately small and fully explicit.
LITERAL_ORACLE = {
    "status": "STATIC_NOT_EXECUTED",
    "capacity_plus_one": {
        "kind": "DATA", "caps": [2, 1000, 8],
        "trace": [["A", 10, 20], ["B", 10, 20], ["C", 10, 20],
                  ["A", 10, 20], ["B", 10, 20], ["C", 10, 20]],
        "effective_entry_handle_slots": 2,
        "reuse_distances": [None, None, None, 2, 2, 2],
        "window_size_3_distinct_min_max": [3, 3],
        "window_size_3_pair_charge_min_max": [60, 60],
        "firstN_reasons": ["acquired_retained", "acquired_retained",
                           "fallback_entry_bound", "held_path", "held_path",
                           "fallback_entry_bound"],
        "FIFO_reasons": ["acquired_retained", "acquired_retained",
                         "acquired_retained", "acquired_retained",
                         "acquired_retained", "acquired_retained"],
        "FIFO_successful_retirement_by_row": [0, 0, 1, 1, 1, 1],
        "firstN_reacquisition_by_row": [0, 0, 0, 0, 0, 0],
        "FIFO_reacquisition_by_row": [0, 0, 0, 1, 1, 1],
        "FIFO_minus_firstN_acquisition_attempts": 4,
        "FIFO_minus_firstN_reacquisition_attempts": 3,
        "firstN_current_cumulative_peak_retained": [2, 2, 2],
        "FIFO_current_cumulative_peak_retained": [2, 6, 2],
        "FIFO_current_bytes_cumulative_charge_peak_bytes": [40, 120, 40],
        "qualification": "3 distinct ids in each 3-request window exceeds 2 slots; DATA FIFO reacquires every repeat here. Reuse distance alone is not a FIFO miss rule.",
    },
    "retire_then_unretained": {
        "kind": "DATA", "caps": [1, 100, 8],
        "trace": [["A", 10, 20], ["B", 40, 120]],
        "firstN_reasons": ["acquired_retained", "fallback_entry_bound"],
        "FIFO_reasons": ["acquired_retained", "acquired_unretained"],
        "FIFO_successful_retirement_by_row": [0, 1],
        "FIFO_fallback_attempts": 0,
        "FIFO_current_cumulative_peak_retained": [0, 1, 1],
        "FIFO_current_bytes_cumulative_charge_peak_bytes": [0, 20, 20],
    },
    "first_fallback_then_first_acquisition_is_not_reacquisition": {
        "kind": "DATA", "caps": [2, 100, 8],
        "trace": [["A", 10, 60], ["B", 30, 60], ["C", 0, 0],
                  ["D", 0, 0], ["B", 30, 60]],
        "firstN_reasons": ["acquired_retained", "fallback_byte_bound",
                           "acquired_retained", "fallback_entry_bound",
                           "fallback_entry_bound"],
        "FIFO_reasons": ["acquired_retained", "fallback_byte_bound",
                         "acquired_retained", "acquired_retained",
                         "acquired_retained"],
        "FIFO_successful_retirement_by_row": [0, 0, 0, 1, 1],
        "firstN_reacquisition_attempts": 0,
        "FIFO_reacquisition_attempts": 0,
        "FIFO_minus_firstN_acquisition_attempts": 2,
        "FIFO_minus_firstN_reacquisition_attempts": 0,
        "qualification": "B's first acquisition occurs after its prior fallback. A previous request/fallback is not a previous acquisition_attempt.",
    },
}

import argparse
import hashlib
import json
from pathlib import Path
import sys


PRODUCER_SHA256 = "2d2d54a77a3527c7aa37c04e6c1670fc0eff1536aa38fe89be793020aa432544"
DEFAULT_PRODUCER_NAME = "custody_trace.py"
MAX_INPUT_BYTES = 1_048_576
MAX_PRODUCER_BYTES = 65_536
MAX_TRACE_ROWS = 100_000
MAX_DETAIL_ROWS = 128
MAX_WINDOWS = 8
MAX_WINDOW_SIZE = 8192
MAX_OUTPUT_BYTES = 1_048_576
POLICIES = ("firstN", "FIFO")
OUTCOMES = ("held_path_attempts", "acquired_retained",
            "acquired_unretained", "fallback_attempts")
FALLBACKS = ("entry_bound", "handle_bound", "byte_bound")


def bounded_read(path, limit):
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("file exceeds its explicit byte limit")
    return raw


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def bounded_json_integer(token):
    # All valid input charges fit a nonnegative signed-long magnitude.
    if len(token) > 19:
        raise ValueError("JSON integer token exceeds finite charge range")
    return int(token)


def reject_number(token):
    raise ValueError("floating-point and nonfinite JSON numbers are forbidden")


def load_request(path):
    raw = bounded_read(path, MAX_INPUT_BYTES)
    request = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object,
                         parse_int=bounded_json_integer,
                         parse_float=reject_number, parse_constant=reject_number)
    if type(request) is not dict or set(request) != {"kind", "caps", "trace"}:
        raise ValueError("input must contain exactly kind, caps, and trace")
    if request["kind"] != "DATA":
        raise ValueError("explicit kind DATA is required")
    if type(request["trace"]) is not list or len(request["trace"]) > MAX_TRACE_ROWS:
        raise ValueError("trace must be a list with at most 100000 rows")
    return request


def load_producer(path):
    # No search, fallback producer, pycache write, or policy reimplementation.
    raw = bounded_read(path, MAX_PRODUCER_BYTES)
    if hashlib.sha256(raw).hexdigest() != PRODUCER_SHA256:
        raise ValueError("producer hash differs; explicit source review is required")
    namespace = {"__name__": "_pinned_custody_trace",
                 "__file__": str(path)}
    exec(compile(raw, str(path), "exec"), namespace)
    return namespace


def parse_cli_integer(text, low, high, name):
    if not text.isascii() or not text.isdecimal() or len(text) > 6:
        raise argparse.ArgumentTypeError(name + " must be a bounded decimal integer")
    value = int(text)
    if not low <= value <= high:
        raise argparse.ArgumentTypeError(name + " is outside its finite range")
    return value


def request_reason(delta):
    if delta["publication_attempts"] != 1:
        raise ValueError("prefix difference must describe exactly one request")
    if any(delta[name] not in (0, 1) for name in OUTCOMES + FALLBACKS):
        raise ValueError("producer outcome increment no longer matches this adapter")
    if sum(delta[name] for name in OUTCOMES) != 1:
        raise ValueError("producer must report one modeled outcome per request")
    if delta["held_path_attempts"]:
        reason = "held_path"
    elif delta["acquired_retained"]:
        reason = "acquired_retained"
    elif delta["acquired_unretained"]:
        reason = "acquired_unretained"
    else:
        failed = [name for name in FALLBACKS if delta[name]]
        if len(failed) != 1:
            raise ValueError("fallback needs exactly one first-failed predicate")
        reason = "fallback_" + failed[0]
    if sum(delta[name] for name in FALLBACKS) != delta["fallback_attempts"]:
        raise ValueError("successful acquisition/retirement must not be fallback")
    if delta["acquisition_attempts"] != (delta["acquired_retained"]
                                           + delta["acquired_unretained"]):
        raise ValueError("producer acquisition and retention counters disagree")
    if delta["retired_pairs"] not in (0, 1):
        raise ValueError("producer no longer has single-pair retirement semantics")
    return reason


def explain_prefix(producer, caps, trace, policy, limit):
    """Use existing simulate prefixes; these differences are NOT another oracle."""
    simulate = producer["simulate"]
    previous = dict.fromkeys(producer["ORDER"], 0)
    acquired_ids = set()
    reacquisitions = 0
    retained_charge_sum = 0
    rows = []
    for index in range(min(limit, len(trace))):
        after = simulate(caps, trace[:index + 1], policy)
        delta = {key: after[key] - previous[key] for key in producer["ORDER"]}
        reason = request_reason(delta)
        key, payload, pair = trace[index]
        acquired = delta["acquisition_attempts"] == 1
        reacquired = acquired and key in acquired_ids
        if acquired:
            acquired_ids.add(key)
        reacquisitions += int(reacquired)
        if delta["acquired_retained"]:
            retained_charge_sum += pair
        rows.append({
            "reason": reason,
            "acquisition_attempt": acquired,
            "same_trace_reacquisition_attempt": reacquired,
            "successful_retirement_assumed": delta["retired_pairs"],
            "fallback_attempt": delta["fallback_attempts"],
            "before": {"current_entries": previous["current_entries_before_finish"],
                       "current_bytes": previous["current_bytes_before_finish"]},
            "after": {"current_entries": after["current_entries_before_finish"],
                      "current_bytes": after["current_bytes_before_finish"],
                      "cumulative_retained_publications": after["acquired_retained"],
                      "cumulative_retained_pair_charge": retained_charge_sum,
                      "peak_entries": after["peak_entries"],
                      "peak_retained_bytes": after["peak_retained_bytes"]},
        })
        previous = after
    return {"rows": rows, "same_trace_reacquisition_attempts": reacquisitions,
            "distinct_acquired_ids": len(acquired_ids),
            "cumulative_retained_pair_charge": retained_charge_sum}


def reuse_analysis(trace, slots):
    """Exact distinct-id distance within this finite input; no earlier history."""
    size = len(trace)
    tree = [0] * (size + 1)
    last = {}
    distances = []
    cycle_flags = []
    histogram = {"0": 0, "1": 0, "2-3": 0, "4-7": 0,
                 "8-15": 0, "16-31": 0, "32-63": 0, "64-127": 0,
                 "128-255": 0, "256-511": 0, "512-1023": 0,
                 "1024-2047": 0, "2048-4095": 0, "4096+": 0}

    def add(index, amount):
        while index <= size:
            tree[index] += amount
            index += index & -index

    def prefix(index):
        result = 0
        while index:
            result += tree[index]
            index -= index & -index
        return result

    repeats = 0
    distance_sum = 0
    maximum = None
    at_slots = 0
    above_slots = 0
    for index, row in enumerate(trace, 1):
        key = row[0]
        previous = last.get(key)
        distance = None
        cycle = False
        if previous is not None:
            distance = prefix(index - 1) - prefix(previous)
            repeats += 1
            distance_sum += distance
            maximum = distance if maximum is None else max(maximum, distance)
            at_slots += int(distance == slots)
            above_slots += int(distance > slots)
            cycle = distance == slots and index - previous == slots + 1
            if distance >= 4096:
                bucket = "4096+"
            elif distance <= 1:
                bucket = str(distance)
            else:
                low = 1 << (distance.bit_length() - 1)
                bucket = str(low) + "-" + str(low * 2 - 1)
            histogram[bucket] += 1
            add(previous, -1)
        distances.append(distance)
        cycle_flags.append(cycle)
        add(index, 1)
        last[key] = index
    summary = {
        "scope": "exact within supplied trace only; earlier history UNKNOWN",
        "definition": "number of distinct OTHER ids strictly between adjacent occurrences of an id",
        "first_in_trace_prior_history_unknown": len(last),
        "repeat_requests": repeats,
        "maximum_distinct_distance": maximum,
        "mean_distance_numerator": distance_sum,
        "mean_distance_denominator": repeats,
        "distance_histogram": histogram,
        "distance_equal_entry_handle_slots": at_slots,
        "distance_greater_than_entry_handle_slots": above_slots,
        "exact_slots_plus_one_gap_and_distinct_distance_count": sum(cycle_flags),
        "qualification": "Trace reuse distance is not a FIFO hit/miss rule or a measured cold-start distance.",
    }
    return summary, distances, cycle_flags


def working_set(trace, window, slots, budget):
    """Sliding distinct ids/immutable pair charge over FULL request windows."""
    frequencies = {}
    charge = 0
    samples = 0
    minimum_ids = maximum_ids = minimum_charge = maximum_charge = None
    above_slots = above_budget = exactly_plus_one = 0
    for index, row in enumerate(trace):
        key, payload, pair = row
        if key not in frequencies:
            charge += pair
        frequencies[key] = frequencies.get(key, 0) + 1
        if index >= window:
            old_key, old_payload, old_pair = trace[index - window]
            frequencies[old_key] -= 1
            if frequencies[old_key] == 0:
                del frequencies[old_key]
                charge -= old_pair
        if index + 1 < window:
            continue
        count = len(frequencies)
        samples += 1
        minimum_ids = count if minimum_ids is None else min(minimum_ids, count)
        maximum_ids = count if maximum_ids is None else max(maximum_ids, count)
        minimum_charge = charge if minimum_charge is None else min(minimum_charge, charge)
        maximum_charge = charge if maximum_charge is None else max(maximum_charge, charge)
        above_slots += int(count > slots)
        exactly_plus_one += int(count == slots + 1)
        above_budget += int(charge > budget)
    return {"window_requests": window, "full_windows": samples,
            "distinct_ids_min": minimum_ids, "distinct_ids_max": maximum_ids,
            "unique_pair_charge_min": minimum_charge,
            "unique_pair_charge_max": maximum_charge,
            "windows_over_entry_handle_slots": above_slots,
            "windows_exactly_slots_plus_one_ids": exactly_plus_one,
            "windows_unique_pair_charge_over_budget": above_budget}


def prefix_cycle_evidence(details, flags):
    count = longest = run = 0
    for index, row in enumerate(details):
        qualifies = flags[index] and row["same_trace_reacquisition_attempt"]
        run = run + 1 if qualifies else 0
        longest = max(longest, run)
        count += int(qualifies)
    return {"same_trace_reacquisitions_on_exact_slots_plus_one_repeats": count,
            "longest_consecutive_qualifying_requests": longest}


def analyze(producer, request, detail_limit, windows, producer_path):
    # Delegates bool rejection, finite caps/rows/charges and identity drift checks.
    if (type(request) is not dict or set(request) != {"kind", "caps", "trace"}
            or request["kind"] != "DATA"):
        raise ValueError("exact explicit DATA request is required")
    producer["integer"](detail_limit, 0, MAX_DETAIL_ROWS, "detail_limit")
    if windows is not None:
        if type(windows) is not list or not 1 <= len(windows) <= MAX_WINDOWS:
            raise ValueError("windows must be a list with one to eight sizes")
        for window in windows:
            producer["integer"](window, 1, MAX_WINDOW_SIZE, "window_size")
    caps, trace = request["caps"], request["trace"]
    entries, budget, handles = producer["validate"](caps, trace)
    slots = min(entries, (handles - 2) // 2)
    if windows is None:
        windows = sorted({1, slots, slots + 1})
    else:
        windows = sorted(set(windows))
    total = {policy: producer["simulate"](caps, trace, policy) for policy in POLICIES}
    explained = {policy: explain_prefix(producer, caps, trace, policy, detail_limit)
                 for policy in POLICIES}
    reused, distances, flags = reuse_analysis(trace, slots)
    count = min(detail_limit, len(trace))
    complete = count == len(trace)
    policy_results = {}
    for policy in POLICIES:
        prefix_result = explained[policy]
        policy_results[policy] = {
            "full_trace_producer_counts": total[policy],
            "full_trace_same_trace_reacquisition_attempts":
                prefix_result["same_trace_reacquisition_attempts"] if complete else None,
            "full_trace_same_trace_reacquisition_status":
                "KNOWN" if complete else "UNKNOWN_UNEXPLAINED_SUFFIX",
            "explained_prefix": {key: value for key, value in prefix_result.items()
                                 if key != "rows"},
            "capacity_plus_one_prefix_evidence":
                prefix_cycle_evidence(prefix_result["rows"], flags),
        }
    comparable = ("acquisition_attempts", "held_path_attempts", "acquired_retained",
                  "acquired_unretained", "fallback_attempts", "retired_pairs",
                  "current_entries_before_finish", "current_bytes_before_finish",
                  "peak_entries", "peak_retained_bytes")
    reacquisition_delta = (explained["FIFO"]["same_trace_reacquisition_attempts"]
                          - explained["firstN"]["same_trace_reacquisition_attempts"])
    rows = []
    for index in range(count):
        key, payload, pair = trace[index]
        first = explained["firstN"]["rows"][index]
        fifo = explained["FIFO"]["rows"][index]
        rows.append({"request_1based": index + 1, "id": key,
                     "payload_bytes": payload, "pair_bytes": pair,
                     "distinct_reuse_distance_in_trace": distances[index],
                     "exact_slots_plus_one_gap_and_distance": flags[index],
                     "firstN": first, "FIFO": fifo,
                     "FIFO_minus_firstN_reacquisition_attempt":
                         int(fifo["same_trace_reacquisition_attempt"])
                         - int(first["same_trace_reacquisition_attempt"])})
    return {
        "schema": "custody-trace-analysis/DATA-v1", "kind": "DATA",
        "qualification": "Explicit trace arithmetic only; no IO, speed, hit-rate, cold-start, identity, custody, or close-failure inference. All retirements assume successful double-close as in the producer.",
        "producer": {"path": str(producer_path), "sha256": PRODUCER_SHA256,
                     "use": "unchanged simulate totals and bounded prefix differences; not an independent policy oracle"},
        "bounds": {"input_bytes": MAX_INPUT_BYTES, "trace_rows": MAX_TRACE_ROWS,
                   "detail_rows": MAX_DETAIL_ROWS, "windows": MAX_WINDOWS,
                   "window_size": MAX_WINDOW_SIZE, "output_bytes": MAX_OUTPUT_BYTES,
                   "policy_prefix_calls": 2 * count,
                   "policy_prefix_trace_rows_including_repeats": count * (count + 1)},
        "caps": caps, "trace_rows": len(trace),
        "effective_entry_handle_slots_ignoring_bytes": slots,
        "slot_formula": "min(entries,(handles-2)//2); handles=4 admits one pair",
        "metric_meanings": {
            "current": "entries/bytes still retained before finish; may decrease after retirement",
            "cumulative": "acquired_retained counts successful retention events, including reacquisitions; never a current occupancy",
            "peak": "maximum simultaneously retained entries/bytes; never cumulative retention",
            "reacquisition": "an acquisition_attempt for an id with an earlier acquisition_attempt in the same supplied trace; prior fallback alone is insufficient",
            "successful_retirement": "retired_pairs; not fallback or a fallback-bound reason",
            "working_set_charge": "sum of one immutable pair_bytes per distinct id in the request window; not actual retained bytes or an admission oracle",
        },
        "reuse": reused,
        "working_sets": [working_set(trace, window, slots, budget) for window in windows],
        "policies": policy_results,
        "comparison": {
            "direction": "FIFO minus firstN",
            "full_trace_counter_delta": {key: total["FIFO"][key] - total["firstN"][key]
                                         for key in comparable},
            "full_trace_same_trace_reacquisition_attempts_delta":
                reacquisition_delta if complete else None,
            "full_trace_same_trace_reacquisition_status":
                "KNOWN" if complete else "UNKNOWN_UNEXPLAINED_SUFFIX",
            "explained_prefix_same_trace_reacquisition_attempts_delta": reacquisition_delta,
            "qualification": "Extra acquisition_attempts need not all be reacquisitions. Capacity+1 trace patterns plus bounded observed policy outcomes explain candidates; no extrapolation to omitted requests or actual workloads.",
        },
        "details": {"requested_limit": detail_limit, "emitted_rows": count,
                    "omitted_rows": len(trace) - count,
                    "selection": "first N input requests, no hidden sampling",
                    "rows": rows},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--detail-limit", default=0,
                        type=lambda value: parse_cli_integer(value, 0, MAX_DETAIL_ROWS,
                                                            "detail-limit"),
                        help="explicit first-request output cap 0..128; default 0")
    parser.add_argument("--window-size", action="append",
                        type=lambda value: parse_cli_integer(value, 1, MAX_WINDOW_SIZE,
                                                            "window-size"),
                        help="at most eight request-window sizes 1..8192; defaults to 1,slots,slots+1")
    parser.add_argument("--producer", type=Path, help="explicit producer path; default is " + DEFAULT_PRODUCER_NAME + " next to this tool")
    parser.add_argument("--output", type=Path, help="create-only output path; omitted writes to stdout")
    arguments = parser.parse_args()
    if arguments.window_size is not None and len(arguments.window_size) > MAX_WINDOWS:
        raise ValueError("at most eight window-size arguments are allowed")
    request = load_request(arguments.input)
    if arguments.producer is None:
        producer_path = Path(__file__).resolve().parent / DEFAULT_PRODUCER_NAME
    else:
        producer_path = arguments.producer
    producer = load_producer(producer_path)
    result = analyze(producer, request, arguments.detail_limit, arguments.window_size, producer_path)
    encoded = json.dumps(result, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) + 1 > MAX_OUTPUT_BYTES:
        raise ValueError("result exceeds finite output cap; reduce detail-limit")
    if arguments.output is None:
        sys.stdout.buffer.write(encoded + b"\n")
    else:
        with arguments.output.open("xb") as sink:
            sink.write(encoded + b"\n")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError, RecursionError) as problem:
        print(type(problem).__name__ + ": " + str(problem), file=sys.stderr)
        raise SystemExit(2)
