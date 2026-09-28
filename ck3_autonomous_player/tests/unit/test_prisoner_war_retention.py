"""The war release adapter must never turn a partial scan into a negative."""

from __future__ import annotations

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.prisoner_war_retention import (
    normalize_war_prisoner_release_pairs_v1,
    project_prisoner_war_retention,
)
from xar_autoplayer.bridge.war_contract import (
    is_native_war_step,
    parse_query_war_prisoner_release_pairs_v1_step,
    query_war_prisoner_release_pairs_v1_step,
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


def test_fp3_uses_house_branch_and_skips_generic_pow_effect() -> None:
    war = _war()
    war.update({
        "cb_key": "fp3_free_house_member_cb",
        "primary_attacker_house_id": 2370,
        "attacker_participant_ids": [30097],
        "defender_participant_ids": [29829],
        "attacker_release_candidate_ids": [30097, 34486],
        "defender_release_candidate_ids": [29829],
        "full_participant_scan": True,
        "primary_and_first_three_successors_scanned": True,
    })
    result = project_prisoner_war_retention(
        war=war, prisoners=[_prisoner(34486, 2370)],
    )["prisoners"][0]
    assert result["generic_pow_pair_status"] == "not_applicable_cb"
    assert result["fp3_house_member_status"] == "matched_house"
    assert result["fp3_prestige_effect"]["actual_amount"] is None
    assert result["pending_war_retention_commitment"] == "present"


def test_native_pow_producer_requires_complete_same_frame_scan() -> None:
    raw = {
        "step": "query-war-prisoner-release-pairs-v1-16777231",
        "accepted": True, "status": "available", "read_only": True,
        "backend_id": "native-headless", "snapshot_revision": 3,
        "query_sequence": 1,
        "war_prisoner_release_pairs_v1": {
            "war_id": 16777231, "date_raw": FRAME["date_raw"],
            "active_casus_belli_database_index": 17,
            "active_casus_belli_key": "individual_county_de_jure_cb",
            "primary_attacker_character_id": 30097,
            "primary_defender_character_id": 29829,
            "attacker_participant_ids": [30097],
            "defender_participant_ids": [29829],
            "attacker_release_candidate_ids": [30097, 34486],
            "defender_release_candidate_ids": [29829],
            "release_pairs": [{"jailer_character_id": 29829,
                               "prisoner_character_id": 34486,
                               "reason": "primary_or_successor"}],
            "full_participant_scan": True,
            "primary_and_first_three_successors_scanned": True,
            "same_frame_stable": True,
        },
    }
    args = {"expected_step": raw["step"], "expected_war_id": 16777231,
            "expected_snapshot_revision": 3,
            "expected_date_raw": FRAME["date_raw"]}
    assert normalize_war_prisoner_release_pairs_v1(raw, **args)["release_pairs"]
    incomplete = deepcopy(raw)
    incomplete["war_prisoner_release_pairs_v1"]["full_participant_scan"] = False
    with pytest.raises(ValueError, match="incomplete"):
        normalize_war_prisoner_release_pairs_v1(incomplete, **args)
    drifted = deepcopy(raw)
    drifted["snapshot_revision"] = 4
    with pytest.raises(ValueError, match="revision"):
        normalize_war_prisoner_release_pairs_v1(drifted, **args)
    bogus = deepcopy(raw)
    bogus["war_prisoner_release_pairs_v1"]["release_pairs"][0][
        "prisoner_character_id"] = 47028
    with pytest.raises(ValueError, match="contradicts"):
        normalize_war_prisoner_release_pairs_v1(bogus, **args)


def test_prisoner_query_literal_is_exact_native_war_step() -> None:
    literal = query_war_prisoner_release_pairs_v1_step(16777231)
    assert literal == "query-war-prisoner-release-pairs-v1-16777231"
    assert parse_query_war_prisoner_release_pairs_v1_step(literal) == 16777231
    assert is_native_war_step(literal)
    assert parse_query_war_prisoner_release_pairs_v1_step(literal + "x") is None
