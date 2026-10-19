"""Actual sealed wall/date ledger; no live RPC or CPU attribution."""
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


def stamp(value):
    result = datetime.fromisoformat(value)
    require(result.tzinfo is not None, "timestamp has no timezone")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", type=Path, action="append", required=True)
    parser.add_argument("--sha256", action="append", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require(0 < len(args.compact) == len(args.sha256) <= 16, "explicit source pins must pair")
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True, cwd=ROOT).strip()
    sources, inputs = [], []
    for path, expected in zip(args.compact, args.sha256, strict=True):
        require(path.stat().st_size <= 256 * 1024, "source exceeds compact bound")
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, "source SHA mismatch")
        data = json.loads(raw)
        require(data["schema"] == "root.closed-ordinary-batch-compact/v1", "unknown compact schema")
        require(data["machine_id"] == machine, "compact belongs to a different or unknown machine")
        require(data["new_RPC_calls"] == 0 and data["active_Driver_reads"] == 0, "compact producer exceeded source contract")
        inputs.append(data)
        sources.append({"path": str(path), "bytes": len(raw), "sha256": expected})
    require(len({item["campaign_id"] for item in inputs}) == 1, "campaigns cannot share a ledger")
    inputs.sort(key=lambda item: stamp(item["first_rpc_started_at_utc"]))
    groups = defaultdict(lambda: {"count": 0, "elapsed_seconds": 0.0})
    batches, advances, unseen, intervals = [], [], [], []
    seen_sequences = set()
    previous_end = None
    for item in inputs:
        start, end = stamp(item["first_rpc_started_at_utc"]), stamp(item["last_rpc_ended_at_utc"])
        require(end >= start and (previous_end is None or start >= previous_end), "closed batches overlap or reverse")
        local_seconds = 0.0
        local_unknown = 0
        for row in item["responses"]:
            sequence = row["sequence"]
            require(sequence not in seen_sequences, "duplicated response sequence")
            seen_sequences.add(sequence)
            if "elapsed_seconds" not in row:
                local_unknown += 1
                unseen.append(row)
                continue
            begin, finish = stamp(row["started_at_utc"]), stamp(row["ended_at_utc"])
            elapsed = row["elapsed_seconds"]
            require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0, "invalid RPC duration")
            require(start <= begin <= finish <= end, "RPC escapes its closed batch")
            require(abs((finish - begin).total_seconds() - elapsed) < 0.001, "RPC clocks disagree by >=1ms")
            require(not intervals or begin >= intervals[-1][1], "RPC intervals overlap or reverse")
            intervals.append((begin, finish))
            local_seconds += elapsed
            step = row.get("selected_step") or row["request"]["tool"]
            group = "query-war-entry-assessments-*" if step.startswith("query-war-entry-assessments-") else step
            groups[group]["count"] += 1
            groups[group]["elapsed_seconds"] += elapsed
            if step == "life-advance":
                facts = row.get("observed_timing_and_dates", {})
                clock = facts.get("/result/campaign_deadline_native_clock_v1", {})
                first = facts.get("/result/starting_date/date_raw")
                last = facts.get("/result/ending_date/date_raw")
                advances.append({"sequence": sequence, "elapsed_seconds": elapsed,
                    "starting_date_raw": first, "ending_date_raw": last,
                    "actual_days": (last - first) / 24 if type(first) is type(last) is int else None,
                    "clock_stopped": clock.get("stopped"), "early_boundary_cancel": clock.get("early_boundary_cancel"),
                    "active_event_source": facts.get("/result/active_event/source")})
        wall = (end - start).total_seconds()
        batches.append({"batch": item["control_summary"]["batch"], "first_rpc_started_at_utc": start.isoformat(),
            "last_rpc_ended_at_utc": end.isoformat(), "wall_seconds": wall,
            "known_RPC_sum_seconds": local_seconds, "unobserved_RPC_count": local_unknown,
            "unobserved_RPC_and_inter_RPC_gaps_seconds": wall - local_seconds,
            "preceding_inter_batch_gap_seconds": 0.0 if previous_end is None else (start - previous_end).total_seconds(),
            "actual_calendar_days_as_reported": item["control_summary"]["actual_calendar_days"]})
        previous_end = end
    initial = inputs[0]["control_summary"]
    origin = initial["actual_end_date_raw"] - initial["actual_calendar_days"] * 24
    last_date = inputs[-1]["control_summary"]["actual_end_date_raw"]
    days = (last_date - origin) / 24
    wall = (stamp(inputs[-1]["last_rpc_ended_at_utc"]) - stamp(inputs[0]["first_rpc_started_at_utc"])).total_seconds()
    known = sum(row["elapsed_seconds"] for row in groups.values())
    require(days >= 0, "calendar moves backwards")
    result = {"schema": "xar.closed-runtime-end-to-end-wall.v1", "machine_id": machine,
        "observed_utc": datetime.now(timezone.utc).isoformat(), "campaign_id": inputs[0]["campaign_id"],
        "evidence_layer": "sealed actual timestamps/date observations; no CPU/native attribution",
        "sources": sources, "calendar_profile": "ck3-1.20.0.4-cdate-fixed365-raw24/v1",
        "initial_date_raw": origin, "last_date_raw": last_date, "actual_game_days": days,
        "first_AUTO_to_last_closed_RPC_wall_seconds": wall,
        "seconds_per_actual_game_day": wall / days if days else None,
        "phase_goal_seconds_per_day": 1.0, "phase_goal_reached_in_window": bool(days and wall / days <= 1.0),
        "known_RPC_sum_seconds": known, "unobserved_RPC_and_all_gaps_seconds": wall - known,
        "RPC_groups": dict(groups), "batches": batches, "advance_RPC_observations": advances,
        "unobserved_source_rows": unseen,
        "limits": ["includes every gap and zero-day batch after first AUTO, including repairs",
                   "setup/recording before first AUTO excluded and separately disclosed by runtime owner",
                   "unknown response intervals remain mixed with gaps; never relabelled as idle CPU",
                   "latest open batch and repairs after the last closed timestamp not yet measured",
                   "whole AUTO durations include planning and persistence; clock observations do not attribute their full duration"],
        "new_RPC_calls": 0, "active_Driver_or_SAVE_reads": 0, "external_writes_bytes": 0,
        "producer": {"path": Path(__file__).relative_to(ROOT).as_posix(),
                     "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "storage": {"shared_research_annotation": "shared128MiB; ledger16KiB/tool8KiB/peak32KiB limits",
                    "producer_closed": True, "unconsumed_planned_writes_bytes": 0}}
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(raw) <= 16 * 1024 and Path(__file__).stat().st_size <= 8 * 1024, "small ledger budget exceeded")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as output:
        output.write(raw)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(raw), "actual_game_days": days,
                      "wall_seconds": wall, "seconds_per_actual_game_day": result["seconds_per_actual_game_day"]}))


if __name__ == "__main__":
    main()
