"""One pure estate-feedback compound; no M3 contract or runtime revalidation."""
import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.ordinary_succession_operating_context_v1 import build_ordinary_succession_operating_context_v1 as project


def test_complete_current_estate_changes_risks_and_frame_invalidation():
    binding = {"snapshot_id": "native:40", "revision": 41, "native_revision": 40,
               "date_raw": 53145240, "episode_run_id": "synthetic-robert", "episode_character_id": 31254}
    expectation = {"schema": "xar.ck3.succession-expectation/v1", "status": "available", "binding": binding,
        "expectation_state": "successor_expected", "predecessor_character_id": 31254,
        "expected_successor_character_id": 40526, "risk_state": "split_successors", "unavailable_reason": None,
        "title_expectations": [
            {"title": {"title_id": 2230, "tier_raw": 3}, "first_heir_character_id": 40526, "primary": True},
            {"title": {"title_id": 2231, "tier_raw": 2}, "first_heir_character_id": 40526, "primary": False},
            {"title": {"title_id": 2262, "tier_raw": 2}, "first_heir_character_id": 40695, "primary": False}]}
    snapshot = {**binding, "paused": True, "map_ready": True, "one_life_terminal": False,
        "one_life_terminal_reason": None, "played_character": {"character_id": 31254, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession"},
        "succession_expectation": expectation}
    original = copy.deepcopy(snapshot)
    current = project(snapshot)
    assert current["estate"]["personal_estate_titles_to_other_heirs"] == [2262]
    assert current["estate"]["equal_or_higher_rank_titles_to_other_heirs"] == []
    assert not current["actual_land_loss_or_realm_exit_inferred"]
    assert current["action_candidates"] == []  # A split is not a reason to spend on Crown.
    assert snapshot == original

    changed = copy.deepcopy(snapshot)
    changed.update(snapshot_id="native:41", revision=42, native_revision=41)
    changed["succession_expectation"]["binding"].update(snapshot_id="native:41", revision=42, native_revision=41)
    changed["succession_expectation"]["title_expectations"].append(
        {"title": {"title_id": 3000, "tier_raw": 3}, "first_heir_character_id": 40695, "primary": False})
    changed["succession_expectation"]["title_expectations"][1]["first_heir_character_id"] = 40695
    facts = project(changed, previous_expectation=expectation)
    assert facts["estate"]["equal_or_higher_rank_titles_to_other_heirs"] == [3000]
    assert facts["observed_changes"]["added_held_title_ids"] == [3000]
    assert facts["observed_changes"]["changed_first_heir_title_ids"] == [2231]
    assert not facts["law_change_inferred_from_title_distribution"]
    assert not facts["issues"][-1]["actual_realm_exit_proven"]

    for altered, reason in (({**snapshot, "native_revision": 41}, "same_frame_refresh"),
                            ({**snapshot, "active_event": {"instance_id": 7}}, "player_decision"),
                            ({**snapshot, "episode_run_id": "different"}, "same_frame_refresh")):
        output = project(altered)
        assert output["status"] != "available" and reason in output["unavailable_reason"]
        assert output["issues"] == [] and output["action_candidates"] == []
    no_heir = copy.deepcopy(snapshot)
    no_heir["succession_expectation"].update(expectation_state="no_primary_heir",
        expected_successor_character_id=None, risk_state="no_primary_heir")
    for row in no_heir["succession_expectation"]["title_expectations"]:
        row["first_heir_character_id"] = None
    assert project(no_heir)["issues"][0]["kind"] == "no_observed_primary_title_heir"
