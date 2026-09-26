"""Original RED trace still proves the reinforcement reached pre-fire state."""

import json
from pathlib import Path


REPORT = (
    Path(__file__).parents[2]
    / "src/xar_autoplayer/simulation/data"
    / "ck3_1_19_0_6_episode01_messina_join_phase_order_partial_v2.json"
)


def test_two_natural_joins_expand_side_before_first_fire_without_greenwashing_trace():
    result = json.loads(REPORT.read_text(encoding="utf-8"))
    assert result["schema"] == "ck3.native_join_phase_order_partial.v2"
    assert result["combat_id"] == 16777218
    assert result["all_cases_join_before_side0_fire"] is True
    assert result["all_cases_full_trace_ready"] is False
    assert [(row["source_day"], row["joining_army_id"]) for row in result["cases"]] == [
        (11, 22), (21, 28)
    ]
    for row in result["cases"]:
        assert row["arrival_date_raw"] - row["source_date_raw"] == 24
        assert row["joining_army_id"] in row["arrival_snapshot_side0_army_ids"]
        assert row["joining_army_id"] not in row["scheduled_side0_army_ids"]
        assert row["partial_prefire_side0_army_ids"] == [
            *row["scheduled_side0_army_ids"], 0
        ]
        assert row["arrival_control_side0_army_ids_in_stored_order"] == [
            *row["scheduled_side0_army_ids"], row["joining_army_id"]
        ]
        assert row["prefire_side0_fighting_raw"] > row["schedule_side0_fighting_raw"]
        assert row["prefire_capture_failure_flags"] == 16
        assert row["whole_trace_status"] == "trace_unavailable"
        assert row["whole_trace_failure_flags"] == 1040
        assert row["complete_seven_boundary_state_proven"] is False
        assert row["general_same_day_manager_order_proven"] is False
