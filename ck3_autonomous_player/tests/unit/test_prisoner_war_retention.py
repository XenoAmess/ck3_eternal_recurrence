"""The war release adapter must never turn a partial scan into a negative."""

from __future__ import annotations

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.prisoner_war_retention import (
    project_prisoner_war_retention,
)


FRAME = {
    "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
    "date_raw": 53217624, "played_character_id": 29829,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}


def _war() -> dict[str, object]:
    return {
        "frame": dict(FRAME), "war_id": 16777231,
        "cb_key": "individual_county_de_jure_cb",
        "primary_attacker_character_id": 30097,
        "primary_defender_character_id": 29829,
        "primary_attacker_house_id": None,
        "attacker_participant_ids": None, "defender_participant_ids": None,
        "attacker_release_candidate_ids": None,
        "defender_release_candidate_ids": None,
        "full_participant_scan": False,
        "primary_and_first_three_successors_scanned": False,
    }


def _prisoner(character_id: int, house_id: int | None) -> dict[str, object]:
    return {
        "frame": dict(FRAME), "character_id": character_id,
        "jailer_character_id": 29829, "house_id": house_id,
        "house_observable": True, "custody_status": "held_by_jailer",
    }


def test_h2825_known_cb_excludes_fp3_but_not_generic_pow() -> None:
    result = project_prisoner_war_retention(
        war=_war(), prisoners=[_prisoner(34486, 2370),
                               _prisoner(44484, None), _prisoner(47028, None)],
    )
    assert result["generic_pow_source_scan_complete"] is False
    assert [row["generic_pow_pair_status"] for row in result["prisoners"]] == [
        "unavailable", "unavailable", "unavailable",
    ]
    assert {row["fp3_house_member_status"] for row in result["prisoners"]} == {
        "not_applicable_cb",
    }
    assert {row["pending_war_retention_commitment"] for row in result["prisoners"]} == {
        "unavailable",
    }


def test_complete_native_lists_find_exact_pair_and_reachable_exit() -> None:
    war = _war()
    war.update({
        "attacker_participant_ids": [30097, 30100],
        "defender_participant_ids": [29829],
        "attacker_release_candidate_ids": [30097, 34486],
        "defender_release_candidate_ids": [29829, 44200],
        "full_participant_scan": True,
        "primary_and_first_three_successors_scanned": True,
    })
    options = {
        "frame": dict(FRAME), "war_id": 16777231,
        "cb_key": "individual_county_de_jure_cb",
        "options": {"surrender": True, "white_peace": False, "victory": False},
    }
    result = project_prisoner_war_retention(
        war=war,
        prisoners=[_prisoner(34486, 2370), _prisoner(47028, None)],
        exit_options=options,
    )
    assert result["generic_pow_source_scan_complete"] is True
    assert result["prisoners"][0]["generic_pow_pair_status"] == "matched_pair"
    assert result["prisoners"][0]["generic_pow_pair_side"] == "defender_jailer"
    assert result["prisoners"][0]["generic_pow_exit_attainable_now"] is True
    assert result["prisoners"][0]["pending_war_retention_commitment"] == "present"
    assert result["prisoners"][1]["generic_pow_pair_status"] == "not_in_pairs"


def test_frame_drift_and_incomplete_scan_fail_closed() -> None:
    war = _war()
    row = _prisoner(34486, 2370)
    drifted = deepcopy(row)
    drifted["frame"]["native_revision"] = 4
    with pytest.raises(ValueError, match="paused war frame"):
        project_prisoner_war_retention(war=war, prisoners=[drifted])
    war["attacker_participant_ids"] = []
    war["defender_participant_ids"] = []
    war["attacker_release_candidate_ids"] = []
    war["defender_release_candidate_ids"] = []
    result = project_prisoner_war_retention(war=war, prisoners=[row])
    assert result["prisoners"][0]["generic_pow_pair_status"] == "unavailable"
    war["full_participant_scan"] = True
    war["primary_and_first_three_successors_scanned"] = True
    with pytest.raises(ValueError, match="inconsistent"):
        project_prisoner_war_retention(war=war, prisoners=[row])
