"""Project exact closed C7 wartime evidence; no Game, RPC or raw responses."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

PACK = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
OUTPUT = Path("docs/ck3-native-ai/evidence/c7-first-war-native-timing-2026-10-19.json")
INPUTS = (
    (PACK / "C7-BATCH1213-75-COMPACT.json", 229835, "fc3e3eeccd51de35650c4adb9a53a1551b01d7d3db3ca79e6d507467c9c958bb"),
    (PACK / "C7-BATCH1213-75-STAGE-TRACE.jsonl", 236790, "e3777c3db721e47dd25bf491eef74178d49acc34c61e458aec9107241b18ca88"),
)


def exact(path, size, digest, bound=256 * 1024):
    before = path.stat()
    if before.st_size != size or size > bound:
        raise ValueError("closed input size changed/exceeds bound")
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("input changed during read")
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("closed input SHA changed")
    return raw, {"path": str(path), "bytes": size, "sha256": digest,
                 "stat_before_after_equal": True, "mtime_ns": after.st_mtime_ns}


def timestamp(value):
    return datetime.fromisoformat(value).timestamp()


compact_raw, compact_pin = exact(*INPUTS[0])
trace_raw, trace_pin = exact(*INPUTS[1])
compact = json.loads(compact_raw)
trace = [json.loads(line) for line in trace_raw.splitlines() if line]
responses = compact["responses"]
by_sequence = {row["sequence"]: row for row in responses}
families = defaultdict(list)
for row in responses:
    step = row.get("selected_step") or row.get("request", {}).get("tool", "control")
    family = ("advance-route-contact" if step.startswith("advance-route-contact") else
              "query-route-contact" if step.startswith("query-route-contact") else step)
    families[family].append(row)
stages = defaultdict(list)
for row in trace:
    stages[row["stage"]].append(row)


def stage_totals(rows):
    return {"count": len(rows), "sum_ns": sum(row["elapsed_ns"] for row in rows),
            "max_ns": max(row["elapsed_ns"] for row in rows)}


def matched_stages(rpc):
    start, stop = timestamp(rpc["started_at_utc"]), timestamp(rpc["ended_at_utc"])
    matches = defaultdict(list)
    for row in trace:
        end = timestamp(row["finished_at_utc"])
        begin = end - row["elapsed_ns"] / 1e9
        if begin >= start - 0.002 and end <= stop + 0.002:
            matches[row["stage"]].append(row)
    return {name: stage_totals(rows) for name, rows in matches.items() if name in (
        "service.normal_plan_turn", "driver.native_pipe_send_wait",
        "driver.route_preview_native_pipe_send_wait", "driver.army_normalize",
        "driver.record_command", "driver.exact_clock_resume_to_paused")}


bridge = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p26-all-lifestyle-frontier01/jobs/47f64e761c49/bridge.cpp")
_, bridge_pin = exact(bridge, 1600530, "55cc0bd664478f64496b219445a0b5ceeb902b386bb9e1ef076f1592f0b875e9", 2 * 1024 * 1024)
army = by_sequence[1214]
army_timing = army["observed_timing_and_dates"]["/result/army_native_timing_v1"]
first_frame, last_frame = by_sequence[1215]["after_frame"], by_sequence[1273]["after_frame"]
window_start, window_end = army["started_at_utc"], by_sequence[1273]["ended_at_utc"]
wall = (datetime.fromisoformat(window_end) - datetime.fromisoformat(window_start)).total_seconds()
actual_days = (last_frame["date_raw"] - first_frame["date_raw"]) / 24
selected_stages = (
    "service.normal_plan_turn", "service.planner_capabilities", "service.planner_history_rows",
    "service.planner_choose", "service.planner_public_plan_copy", "driver.native_pipe_send_wait",
    "driver.army_normalize", "driver.record_command", "driver.route_preview_native_pipe_send_wait",
    "driver.full_state_persistence", "driver.life_advance_public_change_wait",
    "driver.exact_clock_resume_to_paused")
result = {
    "schema": "xar.ck3.closed-c7-first-war-native-timing/v1",
    "machine_id": compact["machine_id"],
    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "closed_compact_observed_at_utc": compact.get("observed_at_utc"),
    "business_source_commit": compact["business_source_commit"],
    "native": "Native26; actor four-family gate OFF per runtime handoff; unchanged",
    "inputs": [compact_pin, trace_pin],
    "window": {"started_at_utc": window_start, "ended_at_utc": window_end,
               "wall_seconds": wall, "rpc_count_including_control_and_metrics": len(responses),
               "rpc_elapsed_sum_seconds": sum(row.get("elapsed_seconds") or 0 for row in responses),
               "first_metric_sequence": 1215, "last_metric_sequence": 1273,
               "first_frame": first_frame, "last_frame": last_frame,
               "calendar_raw_units_per_day": 24, "actual_game_days": actual_days,
               "wall_seconds_per_actual_game_day": wall / actual_days,
               "limit": "Closed first-RPC through last-MET extent only; outside preparation, tail and recording costs unknown."},
    "rpc_families": {name: {"count": len(rows),
                    "sum_seconds": sum(row.get("elapsed_seconds") or 0 for row in rows),
                    "max_seconds": max(row.get("elapsed_seconds") or 0 for row in rows)} for name, rows in families.items()},
    "army_1214": {"source_pinned_by_compact_not_reread": army["source"],
                  "rpc_seconds": army["elapsed_seconds"], "native_timing_ns": army_timing,
                  "read_plus_serialization_ns": army_timing["read_total_ns"] + army_timing["serialize_ns"],
                  "query_sequence": None, "profile": None, "world_armies_scanned": None,
                  "owner_armies_scanned": None, "result_armies": None,
                  "missing_count_status": "not_observed in closed compact; no raw-body read or additional query",
                  "temporally_contained_stages": matched_stages(army)},
    "move_1220": {"source_pinned_by_compact_not_reread": by_sequence[1220]["source"],
                  "rpc_seconds": by_sequence[1220]["elapsed_seconds"],
                  "temporally_contained_stages": matched_stages(by_sequence[1220])},
    "stage_totals_non_additive": {name: stage_totals(stages[name]) for name in selected_stages},
    "stage_matching": "UTC interval containment with2ms tolerance; native_request_id is null, so this is temporal matching, not request-ID correlation",
    "new_internal_and_sway_timer_stages_observed": any(
        name in stages for name in ("service.planner_internal", "service.planner_ordinary_sway")),
    "native_source_contract": {"source": bridge_pin,
        "spans_1based": {"26626-26646": "read_total encloses adapter call, then ArmyStrengthsResultFrame; diagnostic owner/baseline/rich are nested, not additive",
                         "9484-9544": "serialize_ns is elapsed since serializer start through payload construction, sampled before diagnostic fields and final suffix"}},
    "interpretation": [
        "Army read+serialize are sequential; owner/baseline/rich are nested, not additive. Timers measure elapsed, not proven CPU cost.",
        "Route advances contain exact_clock resume_to_paused; observation phases and public_change_wait overlap. Never add their totals.",
        "13route queries after12advances do not prove duplicate frames or arrival failure.14preview-pipe stages total0.3235843s, not seconds of Native world enumeration.",
        "Current declarable/combat profile absent; historical unknown-machine2.529M evaluations cannot be assigned here."],
    "next_scope": "performance_python correlates existing route date/revision/position/contact pairs; clock owner retains speed3/horizon contract. No Native algorithm change justified by this sample alone.",
    "actions": {"game": 0, "rpc": 0, "compile": 0, "environment_changes": 0,
                "raw_response_reads": 0, "live_driver_or_save_reads": 0, "business_source_changes": 0},
}
raw = (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
producer_bytes = Path(__file__).stat().st_size
if len(raw) + producer_bytes > 16 * 1024:
    raise ValueError("combined small producer/evidence bound exceeded")
OUTPUT.write_bytes(raw)
print(json.dumps({"path": str(OUTPUT), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                  "producer_bytes": producer_bytes, "combined_bytes": len(raw) + producer_bytes,
                  "wall_seconds": wall, "actual_days": actual_days,
                  "army_rpc_seconds": army["elapsed_seconds"], "move_rpc_seconds": by_sequence[1220]["elapsed_seconds"],
                  "move_contained_stages": matched_stages(by_sequence[1220])}, ensure_ascii=True))
