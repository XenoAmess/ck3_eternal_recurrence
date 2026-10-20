"""Read one closed first-FULL HOLD; never submit, continue, or copy a trace.

Use explicit JSONL byte boundaries captured before FULL and at its HOLD. The
extent is hashed in one streaming pass; its caller-supplied alignment remains
explicit. Scalar stage totals overlap and must not be added to RPC/full wall.
Only a small optional create-only report is written; no directories are made.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys

MACHINE = "xenoamess-full-tower-eb9d2c1186"
CONTROL = 10483
START_RAW, BEFORE_RAW, END_RAW = 53144328, 53274624, 53407128
BEFORE_CYCLES = 4753
ORIGINAL_WALL_START = "2026-10-19T03:26:49.420926Z"
DEADLINE = "2026-10-20T06:30:00Z"
CAP = 131072
ROW_CAP = 32768
PHASES = ("relay_total", "consume_guard", "pending_paths", "classifier",
          "display_projection", "atomic_write", "loop_state_persist", "call_total")


def require(ok, why):
    if not ok:
        raise ValueError("A05 timing inspection denied: " + why)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def utc(value):
    require(type(value) is str, "explicit UTC string required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0,
            "UTC timestamp required")
    return stamp


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def small(path, expected=None):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        require(before.st_size <= CAP, "small input exceeds 128 KiB: " + str(path))
        raw = stream.read(CAP + 1)
        after = os.fstat(stream.fileno())
    require(len(raw) <= CAP and signature(before) == signature(after), "small input changed")
    pin = {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}
    if expected is not None:
        require(pin == expected, "exact input reference changed: " + str(path))
    value = json.loads(raw)
    require(type(value) is dict, "JSON object required")
    return value, pin


def signature(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def interval_union(intervals):
    total, start, end = 0, None, None
    for left, right in sorted(intervals):
        require(integer(left) and integer(right) and right >= left, "invalid interval")
        if start is None:
            start, end = left, right
        elif left > end:
            total += end - start
            start, end = left, right
        else:
            end = max(end, right)
    return total + (end - start if start is not None else 0)


def lifecycle(fields, sequence):
    require(fields.get("full_timing_origin") == "new_submission_same_producer"
            and fields.get("full_timing_control_sequence") == sequence
            and fields.get("full_timing_clock") == "monotonic_ns", "same-producer FULL origin required")
    left, right, wall = (fields.get(key) for key in ("full_submit_monotonic_ns",
                        "full_receipt_validated_monotonic_ns", "full_wall_ns"))
    require(integer(left) and integer(right) and integer(wall)
            and right >= left and right - left == wall, "FULL monotonic endpoints differ")
    return wall / 1e9


def validate_hold(status, sequence):
    require(status.get("machine_id") == MACHINE and status.get("status") == "root_review_hold"
            and status.get("control_sequence") == sequence, "actual same-machine first-FULL HOLD required")
    first = status.get("first_batch")
    require(type(first) is dict and first.get("machine_id") == MACHINE
            and first.get("first_control_sequence") == sequence, "first_batch identity differs")
    require(status.get("next_FULL_published") is False, "zero-RPC HOLD not established")
    return first


def rpc_summary(summary, sequence, wall):
    require(type(summary) is dict and summary.get("schema") == "xar.ck3.full-existing-rpc-rows/v1"
            and summary.get("control_sequence") == sequence, "FULL RPC summary missing or mismatched")
    tools = summary.get("tools")
    require(type(tools) is dict and set(tools) == {"AUTO", "MET", "SEM", "SAVE"}, "RPC tools differ")
    for item in tools.values():
        require(type(item) is dict and all(integer(item.get(k)) for k in
                ("count", "error_count", "client_error_count"))
                and number(item.get("elapsed_seconds_sum")), "RPC scalar invalid")
    count = sum(v["count"] for v in tools.values())
    elapsed = sum(v["elapsed_seconds_sum"] for v in tools.values())
    require(count == summary.get("row_count") and number(summary.get("elapsed_seconds_sum"))
            and abs(elapsed - summary["elapsed_seconds_sum"]) <= 1e-6, "RPC row totals differ")
    union = summary.get("interval_union_seconds")
    require(union is None or number(union) and union <= elapsed + 1e-6
            and union <= wall + 1e-6, "RPC union is outside enclosing FULL")
    return {"row_count": count, "tools": tools, "elapsed_seconds_sum": elapsed,
            "interval_union_seconds": union,
            "full_wall_minus_rpc_union_seconds": max(0.0, wall - union) if union is not None else None,
            "residual_attribution": None,
            "invalid_elapsed_rows": summary.get("invalid_elapsed_rows"),
            "duplicate_rows_ignored": summary.get("duplicate_rows_ignored"),
            "source": summary.get("source"), "CPU_attribution": None}


def control_summary(probe, sequence):
    if probe is None:
        return {"status": "unknown_not_written_or_probe_sequence_skipped", "expected_sequence": CONTROL,
                "relay_total": None, "consume_guard": None, "ACK_split": None, "artifact_scan_split": None}
    require(probe.get("schema") == "xar.ck3.queue-control-timing/v1"
            and probe.get("machine_id") == MACHINE and probe.get("control_sequence") == sequence == CONTROL,
            "control probe machine/sequence differs")
    require(probe.get("clock_kind") == "monotonic_ns" and probe.get("cycle_budget") == 30,
            "probe clock/budget differs")
    phases = probe.get("phase_totals")
    require(type(phases) is dict, "phase aggregates missing")
    selected = {}
    for name in PHASES:
        value = phases.get(name)
        if value is not None:
            require(type(value) is dict and all(integer(value.get(k)) for k in
                    ("count", "inclusive_ns", "exclusive_ns", "max_ns", "error_count"))
                    and value["exclusive_ns"] <= value["inclusive_ns"], "phase aggregate invalid")
        selected[name] = value
    intervals, missing = [], 0
    boundaries = probe.get("request_boundaries")
    require(type(boundaries) is dict and len(boundaries) <= 128, "bounded request boundaries required")
    for row in boundaries.values():
        require(type(row) is dict, "request boundary object required")
        left, right = row.get("rpc_start"), row.get("rpc_end")
        if left is None or right is None:
            missing += 1
            continue
        require(type(left) is type(right) is dict, "boundary shape differs")
        intervals.append((left.get("monotonic_ns"), right.get("monotonic_ns")))
    union = interval_union(intervals) / 1e9 if not missing else None
    return {"status": "measured_wall_not_CPU", **selected,
            "observed_settled_cycles": probe.get("observed_settled_cycles"),
            "actual_cycle_delta": probe.get("actual_cycle_delta"),
            "RPC_boundary_count": len(boundaries), "RPC_boundary_union_seconds": union,
            "incomplete_RPC_boundaries": missing, "ACK_split": None, "artifact_scan_split": None,
            "unavailable_reason": "ACK and scan detail are not connected by the frozen A05 adapter",
            "nested_inclusive_totals_additive": False,
            "dropped_open_spans": probe.get("dropped_open_spans"), "open_spans": probe.get("open_spans"),
            "boundary_limit_reached": probe.get("boundary_limit_reached"),
            "instrumentation_diagnostics": probe.get("instrumentation_diagnostics")}


def stream_rows(stream, start, end):
    require(integer(start) and integer(end) and end >= start, "explicit closed byte extent required")
    if start:
        stream.seek(start - 1)
        require(stream.read(1) == b"\n", "extent starts inside a JSONL row")
    stream.seek(start)
    hashed, groups, clocks, schemas = hashlib.sha256(), {}, {}, {}
    remaining, rows = end - start, 0
    first_utc = last_utc = None
    while remaining:
        raw = stream.readline(min(remaining, ROW_CAP) + 1)
        require(raw and len(raw) <= min(remaining, ROW_CAP) and raw.endswith(b"\n"),
                "extent ends inside a row, input truncated, or row exceeds 32 KiB")
        remaining -= len(raw)
        hashed.update(raw)
        row = json.loads(raw)
        require(type(row) is dict, "JSONL object required")
        rows += 1
        schema = row.get("schema")
        require(type(schema) is str and len(schema) <= 128, "bounded trace schema required")
        require(schema in schemas or len(schemas) < 32, "too many trace schemas")
        schemas[schema] = schemas.get(schema, 0) + 1
        stamp = row.get("finished_at_utc")
        if stamp is not None:
            moment = utc(stamp)
            first_utc = moment if first_utc is None else min(first_utc, moment)
            last_utc = moment if last_utc is None else max(last_utc, moment)
        elapsed = row.get("elapsed_ns")
        if schema not in {"xar.ck3.army-query-timing.v1", "xar.ck3.exact-clock-observation.v1"}:
            continue
        require(integer(elapsed), "recognized timing row elapsed invalid")
        if schema == "xar.ck3.army-query-timing.v1":
            key = (row.get("stage"), row.get("step"))
            target = groups
        else:
            key = (row.get("phase"), "cumulative_since_resume")
            target = clocks
        require(all(type(k) is str and len(k) <= 128 for k in key), "bounded stage/step required")
        require(key in target or len(target) < 96, "too many stage groups")
        item = target.setdefault(key, {"count": 0, "sum_ns": 0, "max_ns": 0,
                                     "min_date_raw": None, "max_date_raw": None})
        item["count"] += 1
        item["sum_ns"] += elapsed
        item["max_ns"] = max(item["max_ns"], elapsed)
        date = row.get("date_raw")
        if integer(date):
            item["min_date_raw"] = date if item["min_date_raw"] is None else min(item["min_date_raw"], date)
            item["max_date_raw"] = date if item["max_date_raw"] is None else max(item["max_date_raw"], date)
    def projection(target, cumulative):
        return [{"stage_or_phase": key[0], "step_or_basis": key[1],
                 **({k: v for k, v in value.items() if k != "sum_ns"} if cumulative else value),
                 **({"mean_elapsed_since_resume_ns": value["sum_ns"] / value["count"]} if cumulative else {})}
                for key, value in sorted(target.items())]
    return {"start_byte": start, "end_byte": end, "extent_bytes": end - start,
            "extent_sha256": hashed.hexdigest(), "rows": rows, "schemas": schemas,
            "first_finished_at_utc": first_utc.isoformat() if first_utc else None,
            "last_finished_at_utc": last_utc.isoformat() if last_utc else None,
            "stage_totals": projection(groups, False), "clock_phases": projection(clocks, True),
            "stage_totals_additive": False, "clock_phases_additive": False,
            "scope": "caller-captured fixed closed byte extent; alignment is not inferred from dates",
            "WAL_status": None, "CPU_attribution": None}


def extent(path, start, end):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        require(before.st_size >= end, "extent exceeds actual file")
        result = stream_rows(stream, start, end)
        after = os.fstat(stream.fileno())
    require(signature(before) == signature(after)
            and signature(after) == signature(path.stat()), "trace changed while frozen extent was read")
    return {"path": str(path), "file_identity": {"device": before.st_dev, "inode": before.st_ino},
            "file_size_at_read": before.st_size, "file_mtime_ns": before.st_mtime_ns, **result}


def inspect(runtime, sequence, trace=None, start=None, end=None):
    runtime = Path(runtime).resolve(strict=True)
    status, status_pin = small(runtime / "ROOT-CONTINUOUS-FEEDER-STATUS-P37C23.json")
    first = validate_hold(status, sequence)
    require(Path(first["request"]["path"]).resolve().parent == runtime / "p37-requests"
            and Path(first["response"]["path"]).resolve().parent == runtime / "p37-responses",
            "first-FULL request/response must belong to this runtime")
    if trace is not None:
        require(Path(trace).resolve() == runtime / "ordinary-stage-timings.jsonl", "trace belongs to another runtime")
    wall = lifecycle(first["full_lifecycle"], sequence)
    request, request_pin = small(first["request"]["path"], first["request"])
    response, response_pin = small(first["response"]["path"], first["response"])
    require(request.get("sequence") == sequence and request.get("command") == "full_loop"
            and type(request.get("arguments")) is dict
            and integer(request["arguments"].get("max_turns"), 1)
            and request["arguments"]["max_turns"] <= 30, "bounded original FULL request required")
    wrapper = response.get("result")
    require(response.get("request") == request and type(wrapper) is dict
            and wrapper.get("is_error") is False, "original response mismatch/error")
    result = wrapper.get("structured_content")
    require(type(result) is dict and result.get("status") == "bounded_loop_finished", "successful FULL result required")
    turns, cycles, date = (result.get(k) for k in ("actual_turns", "cumulative_cycles", "actual_end_date_raw"))
    require(integer(turns, 1) and turns <= request["arguments"]["max_turns"]
            and integer(cycles) and cycles - turns == BEFORE_CYCLES
            and integer(date) and BEFORE_RAW <= date <= END_RAW
            and first.get("completed_cycles") == cycles and first.get("date_raw") == date,
            "first A05 date/cycle credit chain differs")
    batch, batch_pin = small(runtime / "p37-offline-batches" / (str(sequence).zfill(4) + ".json"))
    require(batch.get("machine_id") == MACHINE and batch.get("completed_control_sequence") == sequence
            and Path(batch.get("control_response", "")).resolve() == Path(response_pin["path"])
            and batch.get("cumulative_cycles") == cycles, "offline batch binding differs")
    for key, value in first["full_lifecycle"].items():
        require(batch.get(key) == value, "offline batch FULL wall scalar differs: " + key)
    require(batch.get("full_rpc_rows_v1") == result.get("full_rpc_rows_v1"), "batch/result RPC summary differs")
    rpc = rpc_summary(result.get("full_rpc_rows_v1"), sequence, wall)
    probe_path = runtime / "p37-queue" / ("CONTROL-TIMING-" + str(CONTROL).zfill(4) + ".json")
    probe, probe_pin = (small(probe_path) if sequence == CONTROL and probe_path.exists() else (None, None))
    control = control_summary(probe, sequence)
    now = datetime.now(timezone.utc)
    allwall = (now - utc(ORIGINAL_WALL_START)).total_seconds()
    days = (date - BEFORE_RAW) / 24
    campaign_days = (date - START_RAW) / 24
    independent_union = control.get("RPC_boundary_union_seconds")
    paired_union = rpc["interval_union_seconds"]
    return {"schema": "xar.C23-A05-first-FULL-timing-inspection/v1", "machine_id": MACHINE,
            "observed_at_utc": now.isoformat(), "status": "CLOSED_FIRST_FULL_READ_ONLY",
            "control_sequence": sequence, "input_refs": {"HOLD": status_pin, "request": request_pin,
                "response": response_pin, "offline_batch": batch_pin, "control_probe": probe_pin},
            "first_batch_sha256": digest(encoded(first)), "before_date_raw": BEFORE_RAW,
            "after_date_raw": date, "elapsed_game_days": days, "completed_cycles_before": BEFORE_CYCLES,
            "completed_cycles_after": cycles, "actual_settled_cycle_delta": turns,
            "full_wall_seconds": wall, "local_full_seconds_per_day": wall / days if days else None,
            "zero_day_full_wall_retained": True, "RPC": rpc, "control_probe": control,
            "RPC_union_comparison_delta_seconds": (independent_union - paired_union
                if independent_union is not None and paired_union is not None else None),
            "trace": extent(trace, start, end) if trace is not None else None,
            "campaign": {"original_wall_start_utc": ORIGINAL_WALL_START,
                "wall_seconds_through_observation": allwall, "credited_days": campaign_days,
                "seconds_per_credited_day": allwall / campaign_days if campaign_days else None,
                "10950_day_final_mean_lower_bound_seconds_per_day": allwall / 10950,
                "one_second_per_day_still_possible": allwall <= 10950,
                "maintenance_failure_research_time_removed": False, "wall_start_reset": False},
            "game_RPC_calls": 0, "continue_marker_written": False, "trace_copied": False,
            "limits": ["Phase inclusive totals overlap; no CPU attribution or automatic residual cause.",
                "Missing ACK/scan detail is unknown, never measured zero.",
                "A local FULL cannot establish whole-campaign throughput or optimization causality."]}


def self_test():
    global small
    cases = []
    def case(name, operation, rejects=False):
        try:
            operation()
        except ValueError:
            require(rejects, "unexpected self-test rejection: " + name)
        else:
            require(not rejects, "self-test expected rejection: " + name)
        cases.append(name)
    case("overlapping_RPC_intervals_merge", lambda: require(
        interval_union([(0, 10), (2, 5), (8, 12), (20, 23)]) == 15, "union"))
    case("boolean_interval_rejected", lambda: interval_union([(True, 2)]), True)
    row = {"schema": "xar.ck3.army-query-timing.v1", "stage": "service.normal_plan_turn",
           "step": "synthetic", "elapsed_ns": 12, "date_raw": BEFORE_RAW}
    payload = encoded(row) + b"\n"
    case("closed_extent_single_hash", lambda: require(stream_rows(io.BytesIO(payload), 0, len(payload))
        ["extent_sha256"] == digest(payload), "extent hash"))
    case("partial_final_row_rejected", lambda: stream_rows(io.BytesIO(payload), 0, len(payload) - 1), True)
    case("partial_initial_row_rejected", lambda: stream_rows(io.BytesIO(payload), 2, len(payload)), True)
    clock = {**row, "schema": "xar.ck3.exact-clock-observation.v1", "phase": "resume_to_paused_final"}
    clock_bytes = encoded(clock) + b"\n"
    case("clock_phase_not_an_additive_interval", lambda: require("sum_ns" not in
        stream_rows(io.BytesIO(clock_bytes), 0, len(clock_bytes))["clock_phases"][0], "clock cumulative sum"))
    case("unconnected_ACK_and_scan_unknown", lambda: require(control_summary(None, CONTROL)["ACK_split"] is None
        and control_summary(None, CONTROL)["artifact_scan_split"] is None, "unknown phases"))
    first = {"machine_id": MACHINE, "first_control_sequence": CONTROL}
    hold = {"machine_id": MACHINE, "status": "root_review_hold", "control_sequence": CONTROL,
            "first_batch": first, "next_FULL_published": False}
    case("first_HOLD_binds_actual_sequence", lambda: validate_hold(hold, CONTROL))
    case("wrong_sequence_rejected", lambda: validate_hold(hold, CONTROL + 1), True)
    case("other_machine_rejected", lambda: validate_hold({**hold, "machine_id": "other-machine"}, CONTROL), True)
    case("FULL_mono_mismatch_rejected", lambda: lifecycle({"full_timing_origin": "new_submission_same_producer",
        "full_timing_control_sequence": CONTROL, "full_timing_clock": "monotonic_ns",
        "full_submit_monotonic_ns": 1, "full_receipt_validated_monotonic_ns": 9, "full_wall_ns": 9}, CONTROL), True)
    def zero_day_full():
        root = Path(__file__).resolve().parent
        ref = {"path": str(root / "p37-responses/synthetic-response.json"), "bytes": 1, "sha256": "synthetic"}
        wall = {"full_timing_origin": "new_submission_same_producer", "full_timing_control_sequence": CONTROL,
                "full_timing_clock": "monotonic_ns", "full_submit_monotonic_ns": 1,
                "full_receipt_validated_monotonic_ns": 1000000001, "full_wall_ns": 1000000000}
        req = {"sequence": CONTROL, "command": "full_loop", "arguments": {"max_turns": 30}}
        item = {"count": 0, "error_count": 0, "client_error_count": 0, "elapsed_seconds_sum": 0}
        summary = {"schema": "xar.ck3.full-existing-rpc-rows/v1", "control_sequence": CONTROL,
                   "tools": {k: dict(item) for k in ("AUTO", "MET", "SEM", "SAVE")},
                   "row_count": 0, "elapsed_seconds_sum": 0, "interval_union_seconds": 0}
        result = {"status": "bounded_loop_finished", "actual_turns": 1, "cumulative_cycles": 4754,
                  "actual_end_date_raw": BEFORE_RAW, "full_rpc_rows_v1": summary}
        held = {**hold, "first_batch": {**first, "full_lifecycle": wall, "request": {**ref,
                "path": str(root / "p37-requests/synthetic-request.json")}, "response": ref,
                "completed_cycles": 4754, "date_raw": BEFORE_RAW}}
        batch = {"machine_id": MACHINE, "completed_control_sequence": CONTROL, "control_response": ref["path"],
                 "cumulative_cycles": 4754, "full_rpc_rows_v1": summary, **wall}
        values = {"ROOT-CONTINUOUS-FEEDER-STATUS-P37C23.json": held,
                  "synthetic-request.json": req, "synthetic-response.json": {"request": req,
                  "result": {"is_error": False, "structured_content": result}}, "10483.json": batch}
        original = small
        try:
            globals()["small"] = lambda path, expected=None: (values[Path(path).name],
                expected or {"path": str(Path(path).resolve()), "bytes": 1, "sha256": "synthetic"})
            report = inspect(root, CONTROL)
            require(report["elapsed_game_days"] == 0 and report["local_full_seconds_per_day"] is None
                    and report["full_wall_seconds"] == 1, "zero-day FULL wall lost")
        finally:
            globals()["small"] = original
    case("zero_day_FULL_retains_complete_wall", zero_day_full)
    return {"schema": "xar.C23-A05-timing-inspector-software-qualification/v1", "machine_id": MACHINE,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOFTWARE_ONLY_NOT_RUNTIME",
            "cases_passed": cases, "case_count": len(cases), "runtime_credit": 0,
            "game_RPC_calls": 0, "trace_copies": 0, "benchmark_runs": 0,
            "original_wall_start_utc": ORIGINAL_WALL_START, "output_cap_bytes": CAP}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--sequence", type=int, default=CONTROL)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--trace-start-byte", type=int)
    parser.add_argument("--trace-end-byte", type=int)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=Path, help="Create-only, existing approved parent; never a trace copy")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ck3_live_run_id import current_machine_id
    require(current_machine_id() == MACHINE, "current machine identity differs")
    if args.out is not None:
        require(datetime.now(timezone.utc) < utc(DEADLINE), "original write review deadline expired")
        require(not args.out.exists() and args.out.parent.is_dir(), "create-only output with existing parent required")
    if args.self_test:
        require(args.runtime is None and args.trace is None, "software test does not inspect runtime")
        report = self_test()
    else:
        require(args.runtime is not None, "--runtime or --self-test required")
        require((args.trace is None and args.trace_start_byte is args.trace_end_byte is None)
                or args.trace is not None and integer(args.trace_start_byte) and integer(args.trace_end_byte),
                "trace needs both explicit closed offsets")
        report = inspect(args.runtime, args.sequence, args.trace, args.trace_start_byte, args.trace_end_byte)
    own = Path(__file__).resolve()
    report["inspector"] = {"path": str(own), "bytes": own.stat().st_size, "sha256": digest(own.read_bytes())}
    raw = encoded(report)
    require(len(raw) <= CAP, "report exceeds single-item 128 KiB cap")
    if args.out is not None:
        with args.out.open("xb") as stream:
            stream.write(raw)
        print(json.dumps({"machine_id": MACHINE, "path": str(args.out.resolve()),
                          "bytes": len(raw), "sha256": digest(raw)}, separators=(",", ":")))
    else:
        print(raw.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
