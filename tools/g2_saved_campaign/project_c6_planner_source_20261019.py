"""Project only the closed C6 timing input and exact frozen source identities."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
base = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
pack = base / "p51-fresh1066-v20261019-prepare01"
source = base / "sdk-v20261019-candidate/src05/xar_autoplayer"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


compact = pack / "CLOSED-FRAGMENT-0287-0353-COMPACT72.json"
assert pin(compact)["sha256"] == "51f553dd034d5f29646996a3168a9d29591691a2a13bdf25e4b62d2b8eeffe9e"
closed = json.loads(compact.read_text(encoding="utf-8-sig"))
trace = pack / "C6-CLOSED-STAGE-TRACE72.jsonl"
assert pin(trace)["sha256"] == "0b5f670097d91fa531ec371cf584ff37fba49d8c1a5b5a0d0fee5b9e759b96a2"
rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line]
service = pin(source / "bridge/service.py")
driver = pin(source / "bridge/native_driver.py")
assert service["sha256"] == "9a22d369ffc245c7a26439a55819461a5c296a4fce015d1cf0ba85f86055e81e"
assert driver["sha256"] == "f64d8c6478b37fe39a3baca6f7794b89a1e20072b443895b9e9e29de6158226f"
freeze = pin(Path(closed["source_adoption"]["path"]))
assert freeze["sha256"] == closed["source_adoption"]["sha256"]
metrics = {}
for stage in ("service.normal_plan_turn", "service.planner_capabilities", "service.planner_history_rows", "service.planner_public_plan_copy"):
    values = [row["elapsed_ns"] for row in rows if row["stage"] == stage]
    metrics[stage] = {"samples": len(values), "sum_ns": sum(values), "max_ns": max(values)}
windows = []
for row in sorted((row for row in rows if row["stage"] == "service.normal_plan_turn"), key=lambda row: row["elapsed_ns"], reverse=True)[:2]:
    end = datetime.fromisoformat(row["finished_at_utc"])
    start = end - timedelta(microseconds=row["elapsed_ns"] / 1000)
    subset = [item for item in rows if start <= datetime.fromisoformat(item["finished_at_utc"]) <= end]
    choose = next(item for item in reversed(subset) if item["stage"] == "service.planner_choose")
    copy = next(item for item in reversed(subset) if item["stage"] == "service.planner_public_plan_copy")
    windows.append({"normal_plan": row, "choose": choose, "public_copy": copy,
        "choose_to_copy_finish_seconds": (datetime.fromisoformat(copy["finished_at_utc"]) - datetime.fromisoformat(choose["finished_at_utc"])).total_seconds()})
result = {
    "schema": "xar.ck3.c6-planner-post-choice-source-boundary/v1",
    "machine_id": subprocess.check_output([sys.executable, str(root / "tools/ck3_live_run_id.py"), "machine"], text=True).strip(),
    "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "NARROW_TIMING_CANDIDATE_SOURCE_ONLY",
    "business_source_commit": closed["business_source_commit"], "source_manifest": freeze,
    "producer": pin(Path(__file__)), "actual_sources": [service, driver, pin(source / "bridge/current_first_heir_relationship_private_transport.py")],
    "closed_compact": pin(compact), "closed_trace": pin(trace), "metrics": metrics, "hot_plan_windows": windows,
    "unread_RPC_rows": [row for row in closed["responses"] if row["sequence"] in (296, 328)],
    "limits": ["296/328 bodies remain oversized_not_observed; exact RPC timing and Native phases unknown",
        "Trace request IDs null; sequence association only closed compact adjacency; nested/concurrent spans not additive",
        "Four actor gates remain OFF; no profiling environment change"],
    "source_findings": [
        "Service1955-1976 prepares succession before choose2274. Trace large gap is after choose, not evidence that1974 prep is the seconds-scale cost.",
        "Prepare1553-1580 already reuses complete same-frame successful root from owned history. Different public/native/date binding still requires current expectation evidence.",
        "Service8046-8321 requires complete envelope/keyset/mirrors/provenance and before/after frame checks. Driver-cache helper103-166 returns only a small projection; substituting it would fail those guards.",
        "NativeDriver3000-3013 reads semantic state;3044-3074 optionally exports history;4865-4917 freezes current expectation and persists. These are not redundant Nativequeries proven by this trace.",
        "Internal collector2509-2520 already removes private history before helper deepcopy. Do not re-propose that fixed history-copy issue.",
        "Prewar1830-1889 already deduplicates an exact same-frame tuple and replans after a newly published observation. No safe query removal identified.",
        "plan_turn1796 runs internal planning;1798 then stage_ordinary_sway_v1;1825 public copy. Current total covers both unseparated trees."],
    "only_next_patch": {"helper": "existing Service._timed_planning_call_v1:641-650, try/finally with existing scalar sink",
        "call_sites": [{"line": 1796, "stage": "service.planner_internal", "operation": "self._plan_turn_internal"},
            {"line": 1798, "stage": "service.planner_ordinary_sway", "operation": "stage_ordinary_sway_v1(self,planned)"}],
        "purpose": "Separate the measured post-choice gap into internal collectors versus post-plan Sway observation before selecting a narrower provider. No cache/query/policy change.",
        "optional_nested": "Only if needed: wrap1974 succession prep using the same helper; no new provider platform.",
        "ownership": "Proposal only. Root schedules future Service owner/adoption; do not touch frozen src05, M6 observer, faction515/M5/harness."},
    "performance_claim": "No speedup measured; no direct duplicate-query optimization proven. Do not attribute observed seconds to CB, force, Native-only, history, capabilities or final public copy.",
    "actions": {"Game": 0, "RPC": 0, "compile": 0, "source_mutations": 0, "Driver_state_reads": 0, "SAVE_reads": 0, "closed_Native26_writes": 0}}
output = root / "docs/ck3-native-ai/evidence/c6-planner-post-choice-source-boundary-2026-10-19.json"
assert not output.exists()
encoded = (json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode()
assert len(encoded) <= 16 * 1024
output.write_bytes(encoded)
print(json.dumps(pin(output)))
