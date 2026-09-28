"""Project E2-09 numbers from one *new* terminal writer receipt, read-only.

The report proves local integer parity and source identity. It cannot certify
that a gameplay video shows the same run, that clean spans exist, or that the
old 024 narration/card numbers still match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_score import (  # noqa: E402
    calculate_native_battle_score,
    denominator_from_native_buckets,
)


SINGLE_BATTLE_CAP_RAW_Q100000 = 5_000_000  # exact CK3 1.19.0.6 static cap


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_bound(path: Path, expected_sha256: str) -> tuple[dict, dict]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    require(digest == expected_sha256, f"source bytes changed: {path}")
    return json.loads(raw), {"path": str(path.resolve()), "bytes": len(raw), "sha256": digest}


def project(static_receipt: Path, driver_result: Path) -> dict:
    frozen = json.loads(static_receipt.read_text(encoding="utf-8"))
    require(frozen["status"] == "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
            "static identity receipt not GREEN")
    driver_raw = driver_result.read_bytes()
    driver = json.loads(driver_raw)
    require(driver.get("status") == "new-run-native-writer-inputs-captured-not-yet-projected",
            "new run did not capture complete writer inputs")
    require(driver.get("static_receipt", {}).get("sha256") ==
            hashlib.sha256(static_receipt.read_bytes()).hexdigest().upper(),
            "driver used another static source/binary identity")
    days = driver.get("days") or []
    require(days and [row["day_index"] for row in days] ==
            list(range(27, days[-1]["day_index"] + 1)), "day sequence has a gap")
    last = days[-1]
    require(last["terminal_kind"] == "normal_result" and
            last["date_raw"] == frozen["checkpoint_date_raw"] + 24 * (last["day_index"] - 27),
            "terminal date/kind mismatch")
    attempt_root = driver_result.parent
    response_root = attempt_root / "ck3-output" / "interactive-requests-responses"
    for row in days:
        prefix = f"e2t-d{row['day_index']:02d}"
        snapshot, _ = read_bound(response_root / f"{prefix}-snapshot.json",
                                 row["snapshot_receipt_sha256"])
        require(snapshot.get("result") == "CALL_COMPLETED" and
                snapshot.get("body", {}).get("paused") is True and
                snapshot["body"].get("date_raw") == row["date_raw"],
                f"day {row['day_index']} paused source frame changed")
        if "control_receipt_sha256" in row:
            control, _ = read_bound(response_root / f"{prefix}-control.json",
                                    row["control_receipt_sha256"])
            require(control.get("result") == "CALL_COMPLETED" and
                    control.get("body", {}).get("battle_control_snapshot", {}).get("combat_id") ==
                    frozen["expected_combat_id"], f"day {row['day_index']} combat control changed")
        if "advance_receipt_sha256" in row:
            advance, _ = read_bound(response_root / f"{prefix}-advance.json",
                                    row["advance_receipt_sha256"])
            require(advance.get("result") == "CALL_COMPLETED" and
                    advance.get("body", {}).get("starting_date_raw") == row["date_raw"] and
                    advance["body"].get("ending_date_raw") == row["date_raw"] + 24,
                    f"day {row['day_index']} advance receipt changed")
    terminal_path = attempt_root / "ck3-output" / "interactive-requests-responses" / f"e2t-d{last['day_index']:02d}-terminal.json"
    response, terminal_source = read_bound(terminal_path, last["terminal_receipt_sha256"])
    require(response.get("result") == "CALL_COMPLETED" and
            response.get("body", {}).get("accepted") is True,
            "terminal MCP response not accepted")
    terminal = response["body"]["battle_terminal_transition"]
    prior = terminal["prior"]
    require(terminal.get("prior_combat_id") == frozen["expected_combat_id"] and
            prior.get("combat_id") == frozen["expected_combat_id"] and
            terminal.get("observed_date_raw") == last["date_raw"] and
            prior.get("terminal_kind") == "normal_result", "terminal source identity changed")
    loss = prior["hard_loss_inputs"]
    hard_loss = max(0, loss["baseline_raw"] - loss["stored_current_raw"] -
                    loss["levy_soft_raw"] - loss["men_at_arms_soft_raw"])
    require(hard_loss == loss["hard_loss_raw"], "native hard-loss numerator differs")
    score = prior["battle_warscore"]
    denominator = score["denominator_inputs"]
    participants = denominator["participants"]
    require(participants and all(isinstance(row, dict) and
                                 len(row["buckets_native_add_order_int32"]) == 8
                                 for row in participants), "native eight-bucket rows missing")
    sum_int32, divisor = denominator_from_native_buckets(
        [row["buckets_native_add_order_int32"] for row in participants])
    require(denominator["sum_int32"] == sum_int32 and
            denominator["after_minimum_int32"] == divisor,
            "native denominator buckets disagree with writer")
    scale = score["selected_cb_battle_scale_raw_q100000"]
    require(type(scale) is int and scale >= 0 and
            type(score["winner_is_war_attacker"]) is bool, "CB scale or war side invalid")
    calculated = calculate_native_battle_score(
        hard_loss_raw_q100000=hard_loss,
        denominator_count=divisor,
        selected_cb_scale_raw_q100000=scale,
        single_battle_cap_raw_q100000=SINGLE_BATTLE_CAP_RAW_Q100000,
        winner_is_war_attacker=score["winner_is_war_attacker"],
    )
    require(score["status"] == "recorded" and score["war_id"] == frozen["expected_war_id"] and
            score["value_raw_q100000"] == calculated.row_raw_q100000 and
            score["attacker_relative_delta_raw_q100000"] == calculated.attacker_relative_raw_q100000,
            "native writer row/cap/polarity differs from common integer model")
    return {
        "schema": "ck3.episode02.terminal-pair-numbers.v1",
        "status": "numeric-parity-green-footage-and-voice-unverified",
        "source_attempt": attempt_root.name,
        "static_receipt_sha256": hashlib.sha256(static_receipt.read_bytes()).hexdigest().upper(),
        "driver_result_sha256": hashlib.sha256(driver_raw).hexdigest().upper(),
        "terminal_source": terminal_source,
        "combat_id": frozen["expected_combat_id"], "war_id": frozen["expected_war_id"],
        "terminal_day": last["day_index"], "terminal_date_raw": last["date_raw"],
        "winner_raw": prior.get("winner_raw"),
        "hard_loss_inputs_raw_q100000": loss,
        "computed_hard_loss_raw_q100000": hard_loss,
        "denominator_inputs": denominator,
        "ratio_raw_q100000": calculated.ratio_raw_q100000,
        "selected_cb_battle_scale_raw_q100000": scale,
        "uncapped_score_raw_q100000": calculated.uncapped_raw_q100000,
        "single_battle_cap_raw_q100000": SINGLE_BATTLE_CAP_RAW_Q100000,
        "row_score_raw_q100000": calculated.row_raw_q100000,
        "war_attacker_relative_raw_q100000": calculated.attacker_relative_raw_q100000,
        "old_024_numbers_assumed": False,
        "requires_same_run_clean_footage_and_1x_review": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-receipt", type=Path, required=True)
    parser.add_argument("--driver-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = project(args.static_receipt, args.driver_result)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "row": result["row_score_raw_q100000"],
                      "war_attacker_relative": result["war_attacker_relative_raw_q100000"]}))


if __name__ == "__main__":
    main()
