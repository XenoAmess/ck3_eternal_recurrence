"""Frozen real-CK3 pursuit observations remain a whole-three-day golden."""

import json
from pathlib import Path

from xar_autoplayer.simulation.combat_core import (
    CombatRegimentState,
    PursuitInitialPools,
    RegimentKind,
    apply_three_day_pursuit,
)


FIXTURE = (
    Path(__file__).parents[2]
    / "src/xar_autoplayer/simulation/data"
    / "ck3_1_19_0_6_episode01_messina_pursuit_parity_v4.json"
)


def _states(rows):
    return tuple(
        CombatRegimentState(
            regiment_id=row["regiment_id"],
            kind=RegimentKind(row["kind"]),
            current_raw=row["current_raw"],
            soft_casualties_raw=row["soft_casualties_raw"],
            toughness_raw=row["toughness_raw"],
            pursuit_raw=row["pursuit_raw"],
            screen_raw=row["screen_raw"],
        )
        for row in rows
    )


def test_one_native_pursuit_start_predicts_all_three_days_and_hard_ledgers():
    evidence = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert evidence["source_index_sha256"] == (
        "B4F8C8D4E2827650E4401E9FBAB34DE62558641A424382A4C460FEDBD261E160"
    )
    inputs = evidence["initial_state"]
    loser = _states(inputs["retreater_entries"])
    pursuer = _states(inputs["pursuer_entries"])
    result = apply_three_day_pursuit(
        loser, pursuer,
        initial_pools=PursuitInitialPools.from_entries(loser),
        pursuer_efficiency_modifier_raw=inputs["pursuer_efficiency_modifier_raw"],
        retreater_loss_modifier_raw=inputs["retreater_loss_modifier_raw"],
    )
    assert len(result.days) == 3
    matched_rows = 0
    for model_day, native_day in zip(result.days, evidence["days"], strict=True):
        assert model_day.total_hard_raw == native_day["native_total_soft_to_hard_raw"]
        assert model_day.total_hard_raw == native_day["native_owner_hard_ledger_delta_raw"]
        for model_entry, native_row in zip(model_day.entries, native_day["rows"], strict=True):
            assert model_entry.regiment_id == native_row["regiment_id"]
            assert model_entry.soft_casualties_raw == native_row["native_after_soft_raw"]
            matched_rows += 1
    assert matched_rows == 72
    assert result.total_hard_raw == 6_294_269
    assert evidence["terminal"] == {
        "kind": "normal_result",
        "winner_raw": 0,
        "player_subject_state": "subject_retreating",
        "battle_warscore_attacker_relative_raw": -5_000_000,
    }
