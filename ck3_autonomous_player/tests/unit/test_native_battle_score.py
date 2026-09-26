"""Live-receipt parity and native integer boundary checks for battle score."""

import json
from pathlib import Path

import pytest

from xar_autoplayer.simulation.native_battle_score import (
    calculate_native_battle_score,
    denominator_from_native_buckets,
)


REPORT = (
    Path(__file__).parents[2] / "src" / "xar_autoplayer" / "simulation" /
    "data" / "ck3_1_19_0_6_episode01_messina_battle_score_parity.json"
)


def test_messina_native_writer_inputs_reproduce_recorded_row():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    score = report["native_battle_warscore"]
    rows = [row["buckets_native_add_order_int32"]
            for row in report["denominator_inputs"]["participants"]]
    summed, divisor = denominator_from_native_buckets(rows)
    projected = calculate_native_battle_score(
        hard_loss_raw_q100000=report["computed_hard_loss_raw_q100000"],
        denominator_count=divisor,
        selected_cb_scale_raw_q100000=report["selected_cb_battle_scale_raw_q100000"],
        single_battle_cap_raw_q100000=report["single_battle_cap_raw_q100000"],
        winner_is_war_attacker=score["winner_is_war_attacker"],
    )
    assert (summed, divisor) == (996, 996)
    assert projected.ratio_raw_q100000 == report["ratio_raw_q100000"]
    assert projected.uncapped_raw_q100000 == report["uncapped_score_raw_q100000"]
    assert projected.row_raw_q100000 == score["value_raw_q100000"]
    assert projected.attacker_relative_raw_q100000 == score["attacker_relative_delta_raw_q100000"]


def test_uncapped_integer_order_and_missing_denominator_are_explicit():
    projected = calculate_native_battle_score(
        hard_loss_raw_q100000=1_000_099,
        denominator_count=30,
        selected_cb_scale_raw_q100000=5_000_000,
        single_battle_cap_raw_q100000=5_000_000,
        winner_is_war_attacker=True,
    )
    assert projected.ratio_raw_q100000 == 33_336
    assert projected.uncapped_raw_q100000 == 1_666_800
    assert projected.attacker_relative_raw_q100000 == 1_666_800
    with pytest.raises(ValueError):
        denominator_from_native_buckets([])
