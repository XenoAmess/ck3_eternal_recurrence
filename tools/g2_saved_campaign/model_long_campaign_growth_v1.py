"""Conditional long-campaign byte/row growth; source arithmetic, not benchmark.

Reads only pinned small sealed receipts and source metadata. No Driver/SAVE
body, RPC, synthetic history expansion, or future wall-time claim is involved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PACK = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
PINS = (
    ("CLOSED-BATCH-0011-COMPACT30.json", "fb2415b1cbc179a78e8d013c7417c2fefaf65e65d3670e5aa435cbae1cfea06f"),
    ("CLOSED-FRAGMENT-0131-0143-COMPACT42.json", "0746e3d106efcb7ec351b6ad1b3f5c5ba1f20108afcc3c14d63da0f39ab7bb77"),
    ("CLOSED-FRAGMENT-0161-0194-COMPACT48.json", "1b522bd23573b3bf3ac52875e731788da8567408c94831cdfc2ef4b2c3464601"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--negative-guard", action="store_true")
    args = parser.parse_args()
    require(not args.negative_guard, "intentional optimized arithmetic guard rejection")
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    sources, rows = [], {}

    def read(path, expected=None):
        require(path.stat().st_size <= 256 * 1024, "not a bounded source")
        raw = path.read_bytes()
        require(expected is None or sha(raw) == expected, "source SHA mismatch")
        sources.append({"path": str(path), "bytes": len(raw), "sha256": sha(raw)})
        return json.loads(raw)

    for name, expected in PINS:
        data = read(PACK / name, expected)
        require(data["machine_id"] == machine, "source machine mismatch")
        for row in data["responses"]:
            rows[row["sequence"]] = row

    def rpc_body(sequence):
        ref = rows[sequence]["source"]
        value = read(Path(ref["path"]), ref["sha256"])["result"]
        return value.get("structured_content") or value.get("structuredContent") or next(
            json.loads(row["text"]) for row in value["content"] if row["type"] == "text")

    met30, met61 = rpc_body(140), rpc_body(193)
    save0, save30a, save30b = rpc_body(45), rpc_body(136), rpc_body(142)
    origin = save0["checkpoint"]["date_raw"]
    require((met30["date_raw"] - origin) / 24 == 30 and (met61["date_raw"] - origin) / 24 == 61,
            "actual date anchors changed")
    f0 = rows[49]["after_frame"]["driver_state_bytes"]
    f30, f61 = met30["driver_state_bytes"], met61["driver_state_bytes"]
    require(f0 < f30 < f61, "recorded file growth is not positive")
    n0 = save0["driver_state_replace_receipt"]["encoded_history_rows"]
    n30 = [item["driver_state_replace_receipt"]["encoded_history_rows"] for item in (save30a, save30b)]
    require(all(item["checkpoint"]["date_raw"] == origin + 30 * 24 for item in (save30a, save30b)), "row anchors changed")
    p63 = read(ROOT / "docs/ck3-native-ai/evidence/p63-r6-performance-and-normal-sdk-close-2026-10-18.json")
    require(p63["machine_id"] == machine, "P63 belongs to another machine")
    historical = p63["performance"]
    rates = {
        "current_poststartup_day30_to61": (f61 - f30) / 31,
        "historical_R6_projected_war_window": historical["R6_window"]["driver_growth_bytes"] / historical["R6_window"]["actual_days"],
        "historical_R5_legacy_heavy_window": historical["R5_distinct_window"]["driver_growth_bytes"] / historical["R5_distinct_window"]["actual_days"],
    }
    model = []
    for label, growth in rates.items():
        for day in (1000, 5000, 10000):
            future = day - 61
            full_size = f61 + growth * future
            barriers = future // 8
            # Scenario only: full barriers at 61+8,61+16,...; no claim that
            # actual succession/once/SAVE barriers follow this sparse cadence.
            written = barriers * f61 + growth * 8 * barriers * (barriers + 1) / 2
            require(full_size > f61 and written >= barriers * f61, "growth arithmetic failed")
            model.append({"growth_regime": label, "target_actual_day": day,
                "assumed_growth_bytes_per_day": growth, "modelled_full_Driver_bytes": round(full_size),
                "modelled_full_Driver_MiB": full_size / 2**20,
                "hypothetical_full_barriers_every_8_days_after_day61": barriers,
                "modelled_future_full_file_write_GiB": written / 2**30,
                "whole_file_above_256MiB_warning_only": full_size > 256 * 2**20,
                "history_cache_threshold_actual_crossing_inferred": False})
    root_profile = read(ROOT / "docs/ck3-native-ai/evidence/p50-root-history-lookup-performance-2026-10-18.json")
    battle_profile = read(ROOT / "docs/ck3-native-ai/evidence/planner-battle-tail-lookup-2026-10-19.json")
    p67 = read(ROOT / "docs/ck3-native-ai/evidence/p67-p68-combat-query-archive-performance-2026-10-18.json")
    barrier_audit = read(ROOT / "docs/ck3-native-ai/evidence/driver-barrier-policy-audit-2026-10-19.json")
    row_rates = [(item - n0) / 30 for item in n30]
    row_model = [{"target_actual_day": day, "modelled_row_range": [math.ceil(n0 + rate * day) for rate in row_rates]}
                 for day in (1000, 5000, 10000)]
    source_pins = []
    for name in ("bridge/driver_state_history_json.py", "bridge/combat_history_superseded_v1.py", "bridge/army_query_history_store.py"):
        path = ROOT / "ck3_autonomous_player/src/xar_autoplayer" / name
        raw = path.read_bytes()
        source_pins.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    for name in ("driver_state_wal_v1.py", "bridge-native_driver.py.patch"):
        path = ROOT / "ck3_autonomous_player/experimental/driver_state_wal_v1" / name
        raw = path.read_bytes()
        source_pins.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    result = {"schema": "xar.long-campaign-conditional-growth.v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_layer": "source inspection plus sealed metadata arithmetic; no new benchmark or game-throughput forecast",
        "sources": sources, "source_pins": source_pins,
        "current_actual_anchors": {"day0_poststartup_Driver_file_bytes": f0, "day30_Driver_file_bytes": f30,
            "day61_Driver_file_bytes": f61, "day0_encoded_rows": n0, "day30_two_encoded_row_observations": n30,
            "first30_poststartup_growth_bytes_per_day": (f30 - f0) / 30,
            "next31_growth_bytes_per_day": rates["current_poststartup_day30_to61"],
            "whole_file_stat_is_not_heap_or_history_bytes": True,
            "successful_query_backlog_can_remain_dirty_and_not_in_file_stat": True},
        "model": {"formula": "F(D)=F61+g*(D-61); W8=k*F61+8*g*k*(k+1)/2, k=floor((D-61)/8)",
            "scope": "conditional continuation of each separately observed growth rate; not a forecast, upper bound or current-policy A/B",
            "rows": model, "row_count_formula": "N(D)=N0+(N30-N0)*D/30; metadata range only, not a workload bound",
            "row_count_rows": row_model,
            "missing_inputs": ["actual history-byte fraction of whole Driver", "future war/action/query/restore rates",
                "future full-barrier reasons/counts", "actual storage throughput and concurrent load"],
            "future_seconds_per_day_estimated": False},
        "structural_costs": {"full_persistence": "O(F) write every barrier; accumulated writes quadratic when F grows linearly and barrier density stays positive",
            "history_cache": "256MiB applies to command_history JSON, not whole Driver; above it every encode rebuilds complete JSON and leaves cache unretained",
            "prefix_edits": "marriage outcome and combat history compaction invalidate the history JSON cache even below its size cap",
            "planning": "internal planning view avoids public history deep copy; expansion creates outer rows and missing-result/restore scans remain O(N)",
            "scan_observations_only": {"root_profile_8853": root_profile["measurements"], "battle_profile_8853_8857": battle_profile["measurements"]}},
        "combat_and_raw_evidence": {"superseded_summary_lossless": False,
            "no_additional_history_or_business_fields_removed": True,
            "P67_single_complete_combat_body_bytes": p67["AUTO77"]["structural_raw_encoded_bytes"]["$.result.structured_content.result.combat_simulation_inputs"]["max_bytes"],
            "P67_single_MCP_response_bytes": p67["AUTO77"]["source"]["bytes"],
            "raw_MCP_storage_rate_historical_R6_bytes_per_day": historical["R6_window"]["response_bytes_per_day"],
            "R6_rate_times_10000_days_bytes_scenario_only": historical["R6_window"]["response_bytes_per_day"] * 10000,
            "excludes": ["video", "CK3 SAVE", "sidecars", "SDK generations", "filesystem metadata"],
            "P67_archive_count_gate_exhausted": not p67["archive_usage"]["count_admits_new_archive"]},
        "existing_WAL_review": {"enabled_or_deployed_by_this_work": False, "existing_generic_append_reused": True,
            "delta_cap_bytes": 262144, "journal_cap_bytes": 8388608,
            "journal_write_is_bounded_whole_journal_atomic_replace": True,
            "actual_mixed_barrier_benefit_gap": "full barrier resets v2; next append reads/hashes/re-writes complete sealed base. One append between full barriers saves no base write",
            "succession_barrier": "Service prepares a changed frame expectation; Driver retain remains a full barrier, so count actual consecutive eligible append runs before adoption",
            "minimum_existing_policy_gaps": barrier_audit["multi_day_policy_gap"]["still_needed"],
            "pre_marker_failed_full_barrier_gap": barrier_audit["failed_full_barrier_boundary"]["minimum_reviewable_change"],
            "unchanged_full_barriers": ["SAVE", "restore/identity", "once/pending/action receipts", "unknown or failed actions", "old-prefix edits", "close"],
            "qualification_recovery_matrix_repeated": False,
            "adoption_priority": "stabilize execution chain now; qualify actual mixed-barrier benefit and existing multiday predicate before any later enablement"},
        "new_game_native_RPC_calls": 0, "Driver_SAVE_body_reads": 0, "external_writes_bytes": 0,
        "historical_ledgers02_03_modified": False,
        "producer": {"path": Path(__file__).relative_to(ROOT).as_posix(), "sha256": sha(Path(__file__).read_bytes())},
        "storage": {"pool": "REPO-ONLY-MICROPOOL01", "producer_closed": True, "future_writes_bytes": 0}}
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(raw) <= 32768, "finite model receipt budget exceeded")
    with args.receipt.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(raw), "rates": rates, "model": model}))


if __name__ == "__main__":
    main()
