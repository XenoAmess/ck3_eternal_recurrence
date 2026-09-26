"""Bind one native Messina replay to its terminal hard-loss inputs.

Reads only preserved response files.  The report distinguishes the combat
side's terminal numerator from the participant hard-casualty ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest().upper() == expected_sha, f"source SHA: {path}")
    response = json.loads(raw)
    require(response["result"] == "CALL_COMPLETED" and response["body"]["accepted"] is True,
            f"accepted native response: {path}")
    return response["body"]


def project(attempt: Path) -> dict:
    summary_path = attempt / "terminal-loss-live-summary.json"
    summary_raw = summary_path.read_bytes()
    summary = json.loads(summary_raw)
    days = summary["days"]
    require([day["day_index"] for day in days] == [27, 28, 29, 30, 31, 32],
            "continuous replay days")
    controls = []
    for row in days[:-1]:
        day = row["day_index"]
        body = source(attempt / "ck3-output" / "interactive-requests-responses" /
                      f"d{day}-control.json", row["control_receipt_sha256"])
        control = body["battle_control_snapshot"]
        require(control["combat_id"] == 16777218 and
                control["observed_date_raw"] == row["date_raw"],
                f"day {day} combat identity")
        side = control["defender"]
        require(side["stored_terminal_loss_baseline_raw"] ==
                row["sides"]["defender"]["stored_terminal_loss_baseline_raw"],
                f"day {day} baseline")
        controls.append((row, control, side))
    final = days[-1]
    body = source(attempt / "ck3-output" / "interactive-requests-responses" /
                  "d32-terminal.json", final["terminal_receipt_sha256"])
    terminal = body["battle_terminal_transition"]
    prior = terminal["prior"]
    require(terminal["prior_combat_id"] == 16777218 and
            terminal["observed_date_raw"] == final["date_raw"] and
            prior["terminal_kind"] == "normal_result" and prior["winner_raw"] == 0,
            "same normal terminal combat")
    inputs = prior["hard_loss_inputs"]
    require(inputs == final["hard_loss_inputs"] and inputs["losing_side_index"] == 1,
            "terminal input integrity")
    last_side = controls[-1][2]
    levy_soft = sum(row["soft_casualties_raw"] for row in last_side["levy_entries"])
    maa_soft = sum(row["soft_casualties_raw"] for row in last_side["men_at_arms_entries"])
    require(inputs["baseline_raw"] == last_side["stored_terminal_loss_baseline_raw"] and
            inputs["stored_current_raw"] == last_side["stored_current_fighting_raw"] and
            inputs["levy_soft_raw"] == levy_soft and
            inputs["men_at_arms_soft_raw"] == maa_soft,
            "day 31 and terminal same native numerator inputs")
    calculated = max(0, inputs["baseline_raw"] - inputs["stored_current_raw"] -
                     levy_soft - maa_soft)
    require(calculated == inputs["hard_loss_raw"], "native terminal numerator")
    ledger = last_side["participant_hard_total_raw"]
    gap = calculated - ledger
    require(gap == 1_000_000, "observed ten-person accounting gap")
    score = prior["battle_warscore"]
    require(score == final["battle_warscore"] and score["status"] == "recorded" and
            score["war_id"] == 4 and score["value_raw_q100000"] == 5_000_000 and
            score["attacker_relative_delta_raw_q100000"] == -5_000_000,
            "native war row and attacker-relative sign")
    return {
        "schema": "ck3.native_terminal_loss_parity.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_attempt": attempt.name,
        "summary_sha256": hashlib.sha256(summary_raw).hexdigest().upper(),
        "source_control_sha256_by_day": {
            str(row["day_index"]): row["control_receipt_sha256"] for row in days[:-1]
        },
        "source_terminal_sha256": final["terminal_receipt_sha256"],
        "terminal_date_raw": final["date_raw"],
        "losing_combat_side_index": 1,
        "hard_loss_formula": "max(0, baseline - stored_current - levy_soft - men_at_arms_soft)",
        "hard_loss_inputs_raw": inputs,
        "computed_hard_loss_raw": calculated,
        "participant_hard_ledger_day31_raw": ledger,
        "terminal_numerator_minus_participant_ledger_raw": gap,
        "battle_warscore": score,
        "scope": "one replay; denominator, CB scale and uncapped score not observed",
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
    print(f"TERMINAL hard loss {report['computed_hard_loss_raw']} raw")


if __name__ == "__main__":
    main()
