"""Classify observed pre-schedule stat changes and verify the knight formula.

This explains the refreshed knight values, not why the prior cached values
were different or which modifiers produced the knight-effectiveness factor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from project_native_daily_stat_refresh import CASES, EXE_SHA256, project


KNIGHT_CALL = (0x239CB44, 0x28FDBC0)
KNIGHT_DAMAGE_STOCK = 50
KNIGHT_TOUGHNESS_STOCK = 10


def _static_knight_source(exe: Path) -> dict:
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != EXE_SHA256:
        raise ValueError("CK3 executable differs from the 1.19.0.6 exact build")
    pe = pefile.PE(data=raw, fast_load=True)
    callsite, expected = KNIGHT_CALL
    code = pe.get_data(callsite, 5)
    if len(code) != 5 or code[0] != 0xE8:
        raise ValueError("knight evaluator call missing")
    actual = callsite + 5 + int.from_bytes(code[1:], "little", signed=True)
    if actual != expected:
        raise ValueError("knight evaluator target drifted")
    # These defines are initialized at runtime; the on-disk PE slots are zero.
    # The values below are the separately researched stock-game values, not a
    # new live read from this finish receipt.
    return {"exe_sha256": EXE_SHA256, "knight_callsite_rva": f"0x{callsite:X}",
            "knight_evaluator_rva": f"0x{expected:X}",
            "knight_damage_stock_define": KNIGHT_DAMAGE_STOCK,
            "knight_toughness_stock_define": KNIGHT_TOUGHNESS_STOCK,
            "stock_defines_read_from_this_live_receipt": False}


def classify(attempt: Path, source_day: int, exe: Path, frozen: Path) -> dict:
    report_bytes = frozen.read_bytes()
    report = json.loads(report_bytes)
    if report != project(attempt, source_day, exe):
        raise ValueError("frozen daily-refresh report differs from raw receipts")
    prefix = CASES[source_day][0]
    finish_path = attempt / "ck3-output/interactive-requests-responses" / f"{prefix}-finish.json"
    finish_bytes = finish_path.read_bytes()
    if hashlib.sha256(finish_bytes).hexdigest().upper() != report["finish_response_sha256"]:
        raise ValueError("finish receipt identity drifted")
    boundary = json.loads(finish_bytes)["body"]["managed_trace"]["trace"]["records"][0]
    source = _static_knight_source(exe)
    characters = {row["character_id"]: row for row in boundary["characters"]}
    counts = {"knight": 0, "levy": 0, "men_at_arms": 0}
    knight_witnesses = []
    for side_index, side in enumerate(boundary["sides"]):
        regiments = {row["regiment_id"]: row for row in side["regiments"]}
        knights = {row["regiment_id"]: row["character_id"] for row in side["knights"]
                   if row["character_id"] != -1}
        for change in (row for row in report["changed_regiments"]
                       if row["side_index"] == side_index):
            regiment_id = change["regiment_id"]
            regiment = regiments[regiment_id]
            if regiment_id not in knights:
                bucket = regiment["bucket"]
                if bucket not in ("levy", "men_at_arms"):
                    raise ValueError("unknown native regiment bucket")
                counts[bucket] += 1
                continue
            counts["knight"] += 1
            character_id = knights[regiment_id]
            prowess = characters[character_id]["prowess"]
            p = max(1, prowess)
            denominator = p * source["knight_damage_stock_define"]
            damage = change["new_damage_raw"]
            if damage % denominator:
                raise ValueError("knight damage cannot yield integral effectiveness")
            implied_effectiveness = damage // denominator
            expected_toughness = p * implied_effectiveness * source["knight_toughness_stock_define"]
            if expected_toughness != change["new_toughness_raw"]:
                raise ValueError("knight refreshed toughness differs from native formula")
            knight_witnesses.append({"side_index": side_index, "regiment_id": regiment_id,
                                     "army_id": regiment["army_id"],
                                     "character_id": character_id, "effective_prowess": prowess,
                                     "implied_knight_effectiveness_raw": implied_effectiveness,
                                     "old_damage_raw": change["old_damage_raw"],
                                     "new_damage_raw": damage,
                                     "old_toughness_raw": change["old_toughness_raw"],
                                     "new_toughness_raw": change["new_toughness_raw"]})
    if sum(counts.values()) != report["changed_regiment_count"]:
        raise ValueError("change classification does not cover all rows")
    knight_witnesses.sort(key=lambda row: (row["side_index"], row["regiment_id"]))
    return {"schema": "ck3.native_pre_schedule_stat_source_classification.v1",
            "game_build": "1.19.0.6", "source_day": source_day,
            "refresh_report_sha256": hashlib.sha256(report_bytes).hexdigest().upper(),
            "finish_response_sha256": report["finish_response_sha256"],
            "static_knight_source": source, "changed_by_native_kind": counts,
            "knight_formula_witnesses": knight_witnesses,
            "all_changed_knight_refreshed_values_match_formula": True,
            "prior_cached_stat_change_cause_proven": False,
            "specific_modifier_source_for_knight_effectiveness_proven": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--source-day", type=int, choices=sorted(CASES), required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--frozen-refresh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = classify(args.attempt, args.source_day, args.exe, args.frozen_refresh)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "changed_by_native_kind": report["changed_by_native_kind"],
                      "knight_witness_count": len(report["knight_formula_witnesses"])}))


if __name__ == "__main__":
    main()
