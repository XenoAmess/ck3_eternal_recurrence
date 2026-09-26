"""Compare direct native regiment stats in two independently verified campaign saves.

This measures observed day-11 to day-21 drift. It does not infer the modifier
sources or claim that intervening or future days stayed constant.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from project_native_paused_stat_eval_parity import project as project_parity


def project(
    day11_paused: Path, day11_trace: Path, day11_frozen: Path,
    day21_paused: Path, day21_trace: Path, day21_frozen: Path,
) -> dict:
    sources = {}
    for day, paused, trace, frozen in (
        (11, day11_paused, day11_trace, day11_frozen),
        (21, day21_paused, day21_trace, day21_frozen),
    ):
        raw = frozen.read_bytes()
        report = json.loads(raw)
        if report != project_parity(paused, trace, day):
            raise ValueError(f"day {day} frozen parity differs from raw receipts")
        sources[day] = (report, hashlib.sha256(raw).hexdigest().upper())
    old = {row["regiment_id"]: row for row in sources[11][0]["per_regiment_comparison"]}
    new = {row["regiment_id"]: row for row in sources[21][0]["per_regiment_comparison"]}
    if len(old) != 51 or len(new) != 63:
        raise ValueError("unexpected native roster census")
    changes = []
    by_kind = Counter()
    changed_by_kind = Counter()
    for regiment_id in sorted(old.keys() & new.keys()):
        before, after = old[regiment_id], new[regiment_id]
        if (before["kind"] != after["kind"]
                or before["side_index"] != after["side_index"]
                or before["knight_character_id"] != after["knight_character_id"]):
            raise ValueError(f"regiment {regiment_id} changed kind/side/knight identity")
        kind = before["kind"]
        by_kind[kind] += 1
        before_pair = (before["paused_direct_damage_raw"], before["paused_direct_toughness_raw"])
        after_pair = (after["paused_direct_damage_raw"], after["paused_direct_toughness_raw"])
        if before_pair != after_pair:
            changed_by_kind[kind] += 1
            changes.append({
                "side_index": before["side_index"], "regiment_id": regiment_id,
                "kind": kind, "day11_damage_raw": before_pair[0],
                "day21_damage_raw": after_pair[0],
                "day11_toughness_raw": before_pair[1],
                "day21_toughness_raw": after_pair[1],
                "knight_character_id": before["knight_character_id"],
                "day11_knight_prowess": before["knight_prowess"],
                "day21_knight_prowess": after["knight_prowess"],
                "day11_knight_effectiveness_raw": before["knight_effectiveness_raw"],
                "day21_knight_effectiveness_raw": after["knight_effectiveness_raw"],
            })
    return {
        "schema": "ck3.native_cross_day_effective_stat_stability.v1",
        "game_build": "1.19.0.6", "combat_id": 16777218,
        "source_parity_report_sha256": {str(day): digest for day, (_, digest) in sources.items()},
        "day11_roster_count": len(old), "day21_roster_count": len(new),
        "shared_regiment_count": len(old.keys() & new.keys()),
        "shared_by_kind": dict(sorted(by_kind.items())),
        "changed_by_kind": dict(sorted(changed_by_kind.items())),
        "changed_regiments": changes,
        "intervening_daily_values_observed": False,
        "future_modifier_transition_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for day in (11, 21):
        parser.add_argument(f"--day{day}-paused", type=Path, required=True)
        parser.add_argument(f"--day{day}-trace", type=Path, required=True)
        parser.add_argument(f"--day{day}-frozen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(
        args.day11_paused, args.day11_trace, args.day11_frozen,
        args.day21_paused, args.day21_trace, args.day21_frozen,
    )
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
        "shared": report["shared_by_kind"], "changed": report["changed_by_kind"],
        "output": str(args.output),
    }))


if __name__ == "__main__":
    main()
