"""Check one Messina native battle-score row from preserved day-31/32 receipts.

The denominator buckets and CB scale are captured passively during the
original war-score writer.  The tool reads immutable response bytes only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.simulation.native_battle_score import (
    calculate_native_battle_score,
    denominator_from_native_buckets,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest().upper() == expected_sha,
            f"source SHA: {path}")
    response = json.loads(raw)
    require(response["result"] == "CALL_COMPLETED" and
            response["body"]["accepted"] is True,
            f"native response: {path}")
    return response["body"]


def project(attempt: Path) -> dict:
    summary_raw = (attempt / "denominator-live-summary.json").read_bytes()
    summary = json.loads(summary_raw)
    days = summary["days"]
    require([row["day_index"] for row in days] == [27, 28, 29, 30, 31, 32],
            "replay day sequence")
    root = attempt / "ck3-output" / "interactive-requests-responses"
    control = load(root / "d31-control.json",
                   days[4]["control_receipt_sha256"])["battle_control_snapshot"]
    terminal = load(root / "d32-terminal.json",
                    days[5]["terminal_receipt_sha256"])["battle_terminal_transition"]
    prior = terminal["prior"]
    require(control["combat_id"] == terminal["prior_combat_id"] ==
            prior["combat_id"] == 16777218 and
            control["observed_date_raw"] == days[4]["date_raw"] and
            terminal["observed_date_raw"] == days[5]["date_raw"] and
            prior["terminal_kind"] == "normal_result" and prior["winner_raw"] == 0,
            "same normal combat and terminal date")
    loss = prior["hard_loss_inputs"]
    losing = control["defender"]
    levy_soft = sum(row["soft_casualties_raw"] for row in losing["levy_entries"])
    maa_soft = sum(row["soft_casualties_raw"] for row in losing["men_at_arms_entries"])
    require(loss["losing_side_index"] == 1 and
            loss["baseline_raw"] == losing["stored_terminal_loss_baseline_raw"] and
            loss["stored_current_raw"] == losing["stored_current_fighting_raw"] and
            loss["levy_soft_raw"] == levy_soft and
            loss["men_at_arms_soft_raw"] == maa_soft,
            "day-31 and terminal hard-loss inputs")
    hard_loss = max(0, loss["baseline_raw"] - loss["stored_current_raw"] -
                    levy_soft - maa_soft)
    require(hard_loss == loss["hard_loss_raw"], "hard-loss numerator")

    score = prior["battle_warscore"]
    denominator = score["denominator_inputs"]
    participants = denominator["participants"]
    require(participants and all(len(row["buckets_native_add_order_int32"]) == 8
                                 for row in participants), "native eight-bucket rows")
    sum_int32, divisor = denominator_from_native_buckets(
        [row["buckets_native_add_order_int32"] for row in participants]
    )
    require(sum_int32 == denominator["sum_int32"] and
            denominator["after_minimum_int32"] == divisor,
            "native 32-bit denominator arithmetic")
    require(len(participants) == 1 and
            participants[0]["character_id"] ==
            prior["defender_primary_participant_character_id"],
            "this replay's losing-war participant identity")
    scale = score["selected_cb_battle_scale_raw_q100000"]
    require(type(scale) is int and scale >= 0, "selected CB scale observed")
    static_single_battle_cap_raw = 5_000_000
    projected = calculate_native_battle_score(
        hard_loss_raw_q100000=hard_loss,
        denominator_count=divisor,
        selected_cb_scale_raw_q100000=scale,
        single_battle_cap_raw_q100000=static_single_battle_cap_raw,
        winner_is_war_attacker=score["winner_is_war_attacker"],
    )
    ratio_raw = projected.ratio_raw_q100000
    uncapped_raw = projected.uncapped_raw_q100000
    expected_row = projected.row_raw_q100000
    require(score["status"] == "recorded" and score["war_id"] == 4 and
            score["war_battle_row_index"] == 0 and
            score["value_raw_q100000"] == expected_row and
            score["winner_is_war_attacker"] is False and
            score["attacker_relative_delta_raw_q100000"] ==
            projected.attacker_relative_raw_q100000,
            "native score row, cap and polarity")
    return {
        "schema": "ck3.native_battle_score_parity.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_attempt": attempt.name,
        "source_summary_sha256": hashlib.sha256(summary_raw).hexdigest().upper(),
        "source_day31_control_sha256": days[4]["control_receipt_sha256"],
        "source_day32_terminal_sha256": days[5]["terminal_receipt_sha256"],
        "terminal_date_raw": days[5]["date_raw"],
        "losing_combat_side_index": 1,
        "hard_loss_inputs_raw_q100000": loss,
        "computed_hard_loss_raw_q100000": hard_loss,
        "day31_participant_hard_ledger_raw_q100000":
            losing["participant_hard_total_raw"],
        "denominator_bucket_order": [
            "eligible_title_regiments", "levies", "men_at_arms",
            "mercenaries", "holy_orders", "special_troops", "knights",
            "nomadic_riders",
        ],
        "denominator_inputs": denominator,
        "ratio_raw_q100000": ratio_raw,
        "selected_cb_battle_scale_raw_q100000": scale,
        "uncapped_score_raw_q100000": uncapped_raw,
        "single_battle_cap_raw_q100000": static_single_battle_cap_raw,
        "expected_row_score_raw_q100000": expected_row,
        "native_battle_warscore": score,
        "scope": "one normal-result replay and loaded CB; not whole-war score or calibrated win probability",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = project(args.attempt)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(rendered, encoding="utf-8")
    print(f"BATTLE SCORE {report['expected_row_score_raw_q100000']} raw")


if __name__ == "__main__":
    main()
