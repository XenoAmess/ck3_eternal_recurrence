"""Bind two native reinforcement arrivals to same-date regiment casualties.

This read-only projector checks immutable pre-contact saves, Rakaly melted
bytes, native snapshot receipts, and the next valid phase record.  It does not
prove the global manager call order or turn an independent replay into the
original battle trajectory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.native_battle_case import load_episode01_native_battle_case  # noqa: E402


MELTED_SAVE_SHA256 = {
    11: "A82FDD3A57B84B8FC5E4A42EBD292013C45FAA5061D89F79D9E7A24E979A01C6",
    21: "48F2EA80D7AF0DA5EA4DA3B34E965A481BD2FF201017E35F0F08711503089B61",
}
RAKALY_EXE_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
JOIN_CASES = ((11, 12, 22), (21, 22, 28))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _source_regiments(text: str, army_id: int) -> dict[int, int]:
    start = text.index("\narmies={")
    end = text.index("\n\tarmies={", start)
    section = text[start:end]
    rows = {}
    for match in re.finditer(r"^\t\t(\d+)=\{\n(.*?)^\t\t\}", section, re.M | re.S):
        body = match.group(2)
        if re.search(rf"^\t\t\tarmy={army_id}$", body, re.M) is None:
            continue
        cached = re.search(r"^\t\t\tcached=\{\n\t\t\t\tcurrent=(\d+)$", body, re.M)
        if cached is None:
            raise ValueError(f"army {army_id} regiment {match.group(1)} has no cached current")
        regiment_id = int(match.group(1))
        if regiment_id in rows:
            raise ValueError(f"army {army_id} duplicate regiment {regiment_id}")
        rows[regiment_id] = int(cached.group(1))
    if not rows:
        raise ValueError(f"army {army_id} has no regiments in save")
    return rows


def _war_army(body: dict, army_id: int) -> dict:
    if len(body.get("active_wars", [])) != 1:
        raise ValueError("snapshot has no unique active war")
    armies = body["active_wars"][0]["enemy_armies"]
    matches = [row for row in armies if row["army_id"] == army_id]
    if len(matches) != 1:
        raise ValueError(f"snapshot has no unique enemy army {army_id}")
    return matches[0]


def project(trace_root: Path, melted_root: Path, rakaly_exe: Path) -> dict:
    if digest(rakaly_exe) != RAKALY_EXE_SHA256:
        raise ValueError("Rakaly executable bytes changed")
    case = load_episode01_native_battle_case()
    by_day = {row["source_day"]: row for row in case["phase_traces"]}
    responses = trace_root / "ck3-output" / "interactive-requests-responses"
    rows = []
    for source_day, arrival_day, army_id in JOIN_CASES:
        prior = by_day[source_day]
        next_trace = by_day[arrival_day]
        if (prior["target_day"] != arrival_day
                or prior["status"] != "trace_unavailable"
                or next_trace["status"] != "bounded_trace_available"
                or next_trace["readiness"]["original_trace_ready"] is not False
                or prior["replay_matches_original_day"] is not False):
            raise ValueError(f"day {source_day}: source/next trace readiness mismatch")
        raw = trace_root / f"trace-d{source_day:02d}-immutable.ck3"
        raw_sha = digest(raw)
        if raw_sha != prior["checkpoint_sha256"]:
            raise ValueError(f"day {source_day}: original save SHA mismatch")
        melted = melted_root / f"trace-d{source_day:02d}-melted.ck3"
        melted_sha = digest(melted)
        if melted_sha != MELTED_SAVE_SHA256[source_day]:
            raise ValueError(f"day {source_day}: melted save SHA mismatch")
        before_strength = _source_regiments(melted.read_text(encoding="utf-8-sig"), army_id)
        snapshot_rows = []
        for phase in ("before", "after"):
            path = responses / f"trace-d{source_day:02d}-{phase}-snapshot.json"
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt["result"] != "CALL_COMPLETED":
                raise ValueError(f"day {source_day}: {phase} snapshot failed")
            body = receipt["body"]
            army = _war_army(body, army_id)
            snapshot_rows.append({
                "phase": phase,
                "receipt_sha256": digest(path),
                "date_raw": body["date_raw"],
                "army_id": army_id,
                "current_province_id": army["current_province_id"],
                "move_target_province_id": army["move_target_province_id"],
                "in_combat": army["in_combat"],
                "army_state": army["army_state"],
            })
        if (snapshot_rows[0]["date_raw"] != prior["source_date_raw"]
                or snapshot_rows[1]["date_raw"] != case["daily"][arrival_day - 1]["date_raw"]
                or snapshot_rows[0]["in_combat"] is not False
                or snapshot_rows[1]["in_combat"] is not True
                or snapshot_rows[0]["move_target_province_id"] != case["province_id"]
                or snapshot_rows[1]["current_province_id"] != case["province_id"]):
            raise ValueError(f"day {source_day}: movement/contact state mismatch")
        next_path = responses / f"trace-d{arrival_day:02d}-finish.json"
        next_sha = digest(next_path)
        if next_sha != next_trace["finish_receipt_sha256"]:
            raise ValueError(f"day {arrival_day}: next phase receipt SHA mismatch")
        next_receipt = json.loads(next_path.read_text(encoding="utf-8"))
        trace = next_receipt["body"]["managed_trace"]["trace"]
        if (next_receipt["body"]["status"] != "bounded_trace_available"
                or trace["record_count"] != 7
                or len(trace["records"]) != 7):
            raise ValueError(f"day {arrival_day}: next phase record unavailable")
        first = trace["records"][0]
        if (first["capture_failure_flags"] != 0
                or first["native_date_raw"] != snapshot_rows[1]["date_raw"]
                or first["boundary"] != "native_capture_before_side0_schedule_call_0x27FB58F"):
            raise ValueError(f"day {arrival_day}: first valid phase boundary mismatch")
        side_rows = [side for side in first["sides"]
                     if any(army["army_id"] == army_id for army in side["armies"])]
        if len(side_rows) != 1:
            raise ValueError(f"day {arrival_day}: joined army not uniquely in battle")
        post_rows = [row for row in side_rows[0]["regiments"] if row["army_id"] == army_id]
        if set(before_strength) != {row["regiment_id"] for row in post_rows}:
            raise ValueError(f"day {arrival_day}: joined regiment roster mismatch")
        regiments = []
        for after in post_rows:
            regiment_id = after["regiment_id"]
            before_raw = before_strength[regiment_id] * 100_000
            fighting = after["fights_in_main_phase"]
            if after["starting_raw"] != before_raw:
                raise ValueError(f"day {arrival_day}: regiment {regiment_id} start mismatch")
            if fighting:
                soft, hard = after["soft_casualties_raw"], after["hard_casualties_raw"]
                if (not isinstance(soft, int) or not isinstance(hard, int)
                        or soft + hard != before_raw - after["current_fighting_raw"]
                        or soft + hard <= 0):
                    raise ValueError(f"day {arrival_day}: regiment {regiment_id} casualty mismatch")
            elif (after["current_fighting_raw"] != 0
                  or after["soft_casualties_raw"] != 0
                  or after["hard_casualties_raw"] is not None):
                raise ValueError(f"day {arrival_day}: non-fighting regiment {regiment_id} mismatch")
            regiments.append({
                "regiment_id": regiment_id,
                "fights_in_main_phase": fighting,
                "prejoin_saved_current_raw": before_raw,
                "arrival_day_starting_raw": after["starting_raw"],
                "arrival_day_current_fighting_raw": after["current_fighting_raw"],
                "arrival_day_soft_casualties_raw": after["soft_casualties_raw"],
                "arrival_day_hard_casualties_raw": after["hard_casualties_raw"],
            })
        if not any(row["fights_in_main_phase"] for row in regiments):
            raise ValueError(f"day {arrival_day}: no fighting joined regiments")
        rows.append({
            "source_day": source_day,
            "arrival_day": arrival_day,
            "army_id": army_id,
            "combat_id": case["combat_id"],
            "original_save_sha256": raw_sha,
            "melted_save_sha256": melted_sha,
            "snapshots": snapshot_rows,
            "arrival_phase_receipt_sha256": next_sha,
            "arrival_phase_boundary": first["boundary"],
            "arrival_phase_date_raw": first["native_date_raw"],
            "regiments": regiments,
            "fighting_regiment_count": sum(row["fights_in_main_phase"] for row in regiments),
            "arrival_day_casualties_observed": True,
            "global_manager_order_proven": False,
            "source_day_whole_trace_available": False,
        })
    return {
        "schema": "ck3-native-join-day-casualty-observation-v1",
        "case_id": case["case_id"],
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "phase_trace_trajectory": case["phase_trace_trajectory"],
        "melted_by_rakaly_version": "0.8.19",
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "join_observations": rows,
        "same_day_reinforcement_damage_observed": True,
        "global_manager_order_proven": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--melted-dir", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite output: {args.output}")
    report = project(args.trace_root.resolve(), args.melted_dir.resolve(), args.rakaly_exe.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "joined_armies": [row["army_id"] for row in report["join_observations"]]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
