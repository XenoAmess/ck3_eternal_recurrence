"""Compare the agent's casualty kernel with one native independent replay.

This is a conditional per-regiment current-strength check using the native
outgoing damage observed that day.  It does not reconstruct outgoing damage,
phase effects, joining, pursuit, terminal effects, or a win probability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.combat_core import (
    CombatRegimentState,
    RegimentKind,
    apply_main_phase_casualties,
)
from xar_autoplayer.simulation.native_battle_case import (
    EPISODE01_CASE_SHA256,
    load_episode01_native_battle_case,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def receipt(path: Path) -> dict[str, object]:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native receipt is not completed: {path}")
    return row["body"]


def control_path(root: Path, day: int) -> Path:
    return root / ("day04-control.json" if day == 4 else f"trace-d{day:02d}-before-control.json")


def finish_path(root: Path, day: int) -> Path:
    return root / ("day04-finish.json" if day == 4 else f"trace-d{day:02d}-finish.json")


def _source_entries(side: dict[str, object]) -> tuple[CombatRegimentState, ...]:
    rows = []
    for bucket, kind in (
        ("levy_entries", RegimentKind.LEVY),
        ("men_at_arms_entries", RegimentKind.MEN_AT_ARMS),
    ):
        for row in side[bucket]:
            if row["fights_in_main_phase"]:
                rows.append(CombatRegimentState(
                    regiment_id=row["regiment_id"],
                    kind=kind,
                    current_raw=row["current_fighting_raw"],
                    soft_casualties_raw=row["soft_casualties_raw"],
                    toughness_raw=row["effective_toughness_raw"],
                ))
    return tuple(rows)


def _compare_side(source: dict[str, object], target: dict[str, object], incoming: int) -> dict[str, object]:
    entries = _source_entries(source)
    source_total = sum(row.current_raw for row in entries)
    predicted = apply_main_phase_casualties(
        entries,
        incoming_damage_raw=incoming,
        defending_total_fighting_men_raw=source_total,
    )
    target_entries = {
        row["regiment_id"]: row
        for bucket in ("levy_entries", "men_at_arms_entries")
        for row in target[bucket]
    }
    missing = []
    residuals = []
    for row in predicted.entries:
        observed = target_entries.get(row.regiment_id)
        if observed is None:
            missing.append(row.regiment_id)
        elif row.current_raw != observed["current_fighting_raw"]:
            residuals.append({
                "regiment_id": row.regiment_id,
                "predicted_current_raw": row.current_raw,
                "observed_current_raw": observed["current_fighting_raw"],
                "predicted_minus_observed_raw": row.current_raw - observed["current_fighting_raw"],
            })
    return {
        "source_fighting_regiment_count": len(entries),
        "source_fighting_current_raw": source_total,
        "native_incoming_damage_raw": incoming,
        "missing_source_regiment_ids": missing,
        "residuals": residuals,
        "mismatch_count": len(missing) + len(residuals),
        "max_abs_residual_raw": max((abs(row["predicted_minus_observed_raw"]) for row in residuals), default=0),
    }


def compare(trace_root: Path) -> dict[str, object]:
    case = load_episode01_native_battle_case()
    root = trace_root / "ck3-output" / "interactive-requests-responses"
    rows = []
    for day in range(4, 27):
        source_path = control_path(root, day)
        target_path = control_path(root, day + 1)
        phase_path = finish_path(root, day)
        evidence = case["phase_traces"][day - 4]
        if digest(source_path) != evidence["control_receipt_sha256"]:
            raise ValueError(f"source control receipt SHA drift on day {day}")
        if digest(phase_path) != evidence["finish_receipt_sha256"]:
            raise ValueError(f"phase receipt SHA drift on day {day}")
        if digest(target_path) != case["phase_traces"][day - 3]["control_receipt_sha256"]:
            raise ValueError(f"target control receipt SHA drift on day {day+1}")
        source = receipt(source_path)["battle_control_snapshot"]
        target = receipt(target_path)["battle_control_snapshot"]
        trace = receipt(phase_path)["managed_trace"]["trace"]
        if source["phase"] != "main" or source["combat_id"] != case["combat_id"]:
            raise ValueError(f"source is not the frozen main battle on day {day}")
        outgoing = trace["outgoing_damage"]
        if outgoing["count"] != 2:
            raise ValueError(f"native outgoing pair unavailable on day {day}")
        attacker = _compare_side(source["attacker"], target["attacker"], outgoing["side1_raw"])
        defender = _compare_side(source["defender"], target["defender"], outgoing["side0_raw"])
        source_armies = [row["public_cunit_id"] for row in source["attacker"]["ordered_armies"]]
        target_armies = [row["public_cunit_id"] for row in target["attacker"]["ordered_armies"]]
        same_armies = source_armies == target_armies
        exact = attacker["mismatch_count"] == defender["mismatch_count"] == 0
        rows.append({
            "source_day": day,
            "target_day": day + 1,
            "source_control_receipt_sha256": digest(source_path),
            "target_control_receipt_sha256": digest(target_path),
            "phase_finish_receipt_sha256": digest(phase_path),
            "trace_status": evidence["status"],
            "same_attacker_army_ids": same_armies,
            "source_attacker_army_ids": source_armies,
            "target_attacker_army_ids": target_armies,
            "new_battle_events": evidence["new_battle_events"],
            "attacker": attacker,
            "defender": defender,
            "all_source_fighting_regiments_current_raw_exact": exact,
            "stable_bounded_current_raw_exact": (
                exact and same_armies and evidence["status"] == "bounded_trace_available"
            ),
        })
    return {
        "schema": "ck3-native-main-tick-conditional-parity-v1",
        "case_sha256": EPISODE01_CASE_SHA256,
        "combat_id": case["combat_id"],
        "trajectory": "independent-replay-from-original-contact-checkpoint",
        "conditioned_on_native_outgoing_damage": True,
        "outgoing_damage_reconstructed": False,
        "phase_effects_reconstructed": False,
        "join_and_terminal_reconstructed": False,
        "win_probability_available": False,
        "source_days": rows,
        "stable_bounded_exact_days": sum(row["stable_bounded_current_raw_exact"] for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite comparison: {args.output}")
    result = compare(args.trace_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "sha256": digest(args.output),
        "source_days": len(result["source_days"]),
        "stable_bounded_exact_days": result["stable_bounded_exact_days"],
        "all_source_exact_days": sum(row["all_source_fighting_regiments_current_raw_exact"] for row in result["source_days"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
