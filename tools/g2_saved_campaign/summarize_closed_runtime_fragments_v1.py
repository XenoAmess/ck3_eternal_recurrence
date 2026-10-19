"""Actual wall/date evidence from explicit sealed compacts, including repairs.

Ordinary RPC rows, local classifier operations and outer-loop endpoints are
kept distinct. This is timestamp evidence, not CPU attribution or an A/B test.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stamp(text):
    value = datetime.fromisoformat(text)
    require(value.tzinfo is not None, "missing timezone")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", type=Path, action="append", required=True)
    parser.add_argument("--sha256", action="append", required=True)
    parser.add_argument("--new-sdk-first-auto", type=int, required=True)
    parser.add_argument("--subwindow", action="append", default=[])
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require(0 < len(args.compact) == len(args.sha256) <= 32, "source pins must pair")
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    sources, rows, campaign = [], {}, None
    initial_date = None
    for path, expected in zip(args.compact, args.sha256, strict=True):
        require(path.stat().st_size <= 256 * 1024, "not a bounded compact")
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, "compact SHA mismatch")
        data = json.loads(raw)
        require(data["machine_id"] == machine, "unknown/different source machine")
        if campaign is None:
            campaign = data["campaign_id"]
        require(data["campaign_id"] == campaign, "different campaigns")
        schema = data["schema"]
        if schema == "root.closed-ordinary-batch-compact/v1":
            require(data["new_RPC_calls"] == 0 and data["active_Driver_reads"] == 0, "collection was not read-only")
            summary = data["control_summary"]
            require(summary["status"] == "bounded_loop_finished", "ordinary batch not closed")
            start_date = summary["actual_end_date_raw"] - 24 * summary["actual_calendar_days"]
            initial_date = start_date if initial_date is None else min(initial_date, start_date)
        elif schema == "root.closed-runtime-fragment-compact/v1":
            require(data["range_closed"] is True, "fragment not closed")
            require(data["actual_new_RPC_for_collection"] == 0 and data["active_Driver_SAVE_reads"] == 0, "collection was not read-only")
        else:
            raise ValueError("unrecognized compact schema")
        pin = {"path": str(path), "bytes": len(raw), "sha256": expected,
               "business_source_commit": data.get("business_source_commit")}
        for key in ("owner_generation", "source_adoption", "correction"):
            if key in data:
                pin[key] = data[key]
        sources.append(pin)
        for row in data["responses"]:
            seq = row["sequence"]
            require(seq not in rows, "duplicate source sequence")
            rows[seq] = row
    require(type(initial_date) in (int, float), "no initial calendar anchor")
    ordered = sorted(rows.values(), key=lambda row: row["sequence"])
    rpc, controls, unknown, advances, dates = [], [], [], [], []
    for row in ordered:
        request = row.get("request", {})
        if request.get("tool"):
            seconds = row.get("elapsed_seconds")
            if seconds is None:
                unknown.append(row)
                continue
            require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, "bad duration")
            begin, end = stamp(row["started_at_utc"]), stamp(row["ended_at_utc"])
            require(end >= begin and abs((end - begin).total_seconds() - seconds) < 0.001, "RPC clocks disagree by >=1ms")
            rpc.append(row)
        elif row.get("status") == "oversized_not_observed":
            unknown.append(row)
        else:
            controls.append({"sequence": row["sequence"], "command": request.get("command"),
                "status": row.get("status"), "ended_at_utc": row.get("ended_at_utc"),
                "client_error": row.get("client_error"), "source": row.get("source")})
        facts = row.get("observed_timing_and_dates", {})
        if row.get("after_frame", {}).get("date_raw") is not None:
            dates.append((row["sequence"], row["after_frame"]["date_raw"], "after_frame/date_raw"))
        for key in ("/date_raw", "/planning_source_frame/date_raw", "/actual_end_frame/date_raw", "/result/ending_date/date_raw"):
            if type(facts.get(key)) is int:
                dates.append((row["sequence"], facts[key], key))
        if row.get("selected_step") == "life-advance":
            first, last = facts.get("/result/starting_date/date_raw"), facts.get("/result/ending_date/date_raw")
            require(type(first) is type(last) is int and last >= first and (last - first) % 24 == 0, "bad actual advance dates")
            clock = facts.get("/result/campaign_deadline_native_clock_v1", {})
            advances.append({"sequence": row["sequence"], "elapsed_seconds": row["elapsed_seconds"],
                "starting_date_raw": first, "ending_date_raw": last, "actual_days": (last - first) // 24,
                "clock_stopped": clock.get("stopped"), "early_boundary_cancel": clock.get("early_boundary_cancel"),
                "speed_configuration": clock.get("speed_configuration"), "active_event_source": facts.get("/result/active_event/source")})
    require(bool(rpc) and bool(dates), "missing actual RPC/date evidence")
    for left, right in zip(rpc, rpc[1:]):
        require(stamp(left["ended_at_utc"]) <= stamp(right["started_at_utc"]), "RPC intervals overlap or reverse")
    first_auto = next(row for row in rpc if row["request"]["tool"] == "ck3_auto_turn")
    sdk_auto = rows[args.new_sdk_first_auto]
    require(sdk_auto["request"]["tool"] == "ck3_auto_turn", "new SDK boundary is not an AUTO")
    origin, latest = stamp(first_auto["started_at_utc"]), max(stamp(row["ended_at_utc"]) for row in ordered if row.get("ended_at_utc"))
    sdk_start = stamp(sdk_auto["started_at_utc"])
    prior_dates = [date for seq, date, _ in dates if seq < args.new_sdk_first_auto]
    require(bool(prior_dates), "new SDK lacks prior actual date")
    sdk_date, last_date = prior_dates[-1], dates[-1][1]
    chain_date = initial_date
    for item in advances:
        require(item["starting_date_raw"] == chain_date, "advance date chain has a gap or replay")
        chain_date = item["ending_date_raw"]
    require(chain_date == last_date, "advance chain disagrees with last actual frame")

    def window(start, end, days):
        selected = [row for row in rpc if start <= stamp(row["started_at_utc"]) and stamp(row["ended_at_utc"]) <= end]
        groups = defaultdict(lambda: {"count": 0, "elapsed_seconds": 0.0})
        for row in selected:
            group = row.get("selected_step") or row["request"]["tool"]
            if group.startswith("query-war-entry-assessments-"):
                group = "query-war-entry-assessments-*"
            groups[group]["count"] += 1
            groups[group]["elapsed_seconds"] += row["elapsed_seconds"]
        wall = (end - start).total_seconds()
        known = sum(value["elapsed_seconds"] for value in groups.values())
        return {"started_at_utc": start.isoformat(), "ended_at_utc": end.isoformat(), "wall_seconds": wall,
            "actual_days": days, "seconds_per_actual_day": wall / days if days else None,
            "known_RPC_count": len(selected), "known_RPC_sum_seconds": known,
            "unobserved_RPC_and_all_gaps_seconds": wall - known, "RPC_groups": dict(groups)}

    windows = {"entire_run_including_repairs": window(origin, latest, (last_date - initial_date) / 24),
               "new_SDK_including_repairs": window(sdk_start, latest, (last_date - sdk_date) / 24)}
    for spec in args.subwindow:
        begin_seq, end_seq = map(int, spec.split(":"))
        a, z = rows[begin_seq], rows[end_seq]
        start, end = stamp(a["started_at_utc"]), stamp(z["ended_at_utc"])
        before = [date for seq, date, _ in dates if seq <= begin_seq]
        after = [date for seq, date, _ in dates if begin_seq <= seq and rows[seq].get("ended_at_utc") and stamp(rows[seq]["ended_at_utc"]) <= end]
        require(bool(before) and bool(after), "subwindow lacks actual date endpoints")
        windows[f"continuous_subwindow_{spec}"] = window(start, end, (after[-1] - before[-1]) / 24)
    gaps = []
    for label, left, right in (("old SDK maintenance endpoints", 110, 111),
            ("LIFE classifier repair endpoints", 114, 121), ("Crown classifier repair endpoints", 120, 134)):
        if left in rows and right in rows:
            a, z = rows[left]["ended_at_utc"], rows[right]["started_at_utc"]
            gaps.append({"context_reported_by_runtime": label, "after_sequence": left, "before_sequence": right,
                         "started_at_utc": a, "ended_at_utc": z, "seconds": (stamp(z) - stamp(a)).total_seconds(),
                         "exact_cause_CPU_partition_available": False})
    result = {"schema": "xar.actual-runtime-fragment-wall.v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "campaign_id": campaign,
        "evidence_layer": "actual sealed timestamps and chained native-date observations; not native/CPU attribution",
        "sources": sources, "windows": windows, "actual_date_endpoints": {"initial": initial_date,
            "new_SDK_opening": sdk_date, "last": last_date, "last_source_sequence": dates[-1][0]},
        "advance_RPC_observations": advances, "identified_gap_endpoints": gaps,
        "local_and_outer_control_rows": controls, "unobserved_source_rows": unknown,
        "ordinary_event_fix_actual_qualification": "not exercised by new SDK advances: only date_deadline stop observed",
        "phase_goal_entire_run_reached": windows["entire_run_including_repairs"]["seconds_per_actual_day"] <= 1.0,
        "phase_goal_new_SDK_reached": windows["new_SDK_including_repairs"]["seconds_per_actual_day"] <= 1.0,
        "load_context": {"native26_compilation_start_utc_reported_approx": "2026-10-19T04:08:00+00:00",
            "source": "runtime owner report: up to two BELOW_NORMAL compilers; Game stays Native25",
            "overlaps_current_closed_window": latest >= stamp("2026-10-19T04:08:00+00:00"),
            "future_windows_must_retain_overlapping_load_and_wall": True},
        "limits": ["all repairs and failed outer-control intervals remain in cumulative wall",
            "continuous subwindows are separately labelled and cannot replace cumulative throughput",
            "unknown response18 stays unread; residual combines it with gaps",
            "latest open repair after the final closed endpoint is not yet measured",
            "whole AUTO includes planning and persistence; no clock-only throughput claim",
            "freeze and owner pins are preserved as supplied by compact, not re-read as full manifests"],
        "game_native_or_RPC_calls": 0, "Driver_or_SAVE_reads": 0, "external_writes_bytes": 0,
        "producer": {"path": Path(__file__).relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "storage": {"pool": "REPO-ONLY-MICROPOOL01, original shared research128MiB", "producer_closed": True, "future_writes_bytes": 0}}
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(raw) <= 32768, "finite ledger budget exceeded")
    with args.receipt.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(raw),
        "windows": {key: {k: value[k] for k in ("wall_seconds", "actual_days", "seconds_per_actual_day")} for key, value in windows.items()}}))


if __name__ == "__main__":
    main()
