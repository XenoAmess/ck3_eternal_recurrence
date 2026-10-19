"""All-war facts stay separate from primary-war policy and absent evidence."""

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.war_contract import enemy_armies_from_wars
from xar_autoplayer.participating_war_threat_observation_v1 import observe_participating_war_threats_v1
from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1


def snapshot():
    return {
        "snapshot_id": "native:7", "revision": 9, "native_revision": 7,
        "date_raw": 53144328, "episode_run_id": "synthetic-participating-scope",
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 31254, "alive": True},
        "player_armies": [],
        "active_wars": [
            {"war_id": 10, "source": "native", "player_side": "defender",
             "player_is_primary_war_leader": True, "player_relative_war_score": -30,
             "targeted_title_ids": [2230], "enemy_armies": [{"army_id": 11, "soldiers": 300}]},
            {"war_id": 20, "source": "native", "player_side": "defender",
             "player_is_primary_war_leader": False, "player_relative_war_score": -80,
             "enemy_armies": [{"army_id": 11, "soldiers": 300}, {"army_id": 12, "soldiers": 700}]},
        ],
    }


def test_all_participating_members_match_existing_tactical_union_without_policy_change():
    value = snapshot()
    before = deepcopy(value)
    policy_before = observe_war_spending_priority_v1(value)
    result = observe_participating_war_threats_v1(value)
    assert result["unique_enemy_army_ids"] == [row["army_id"] for row in enemy_armies_from_wars(value["active_wars"])]
    assert result["enemy_army_memberships"] == [{"army_id": 11, "war_ids": [10, 20]}, {"army_id": 12, "war_ids": [20]}]
    assert result["observed_enemy_raised_soldiers"] == 1000
    assert result["primary_war_ids"] == [10] and result["non_primary_war_ids"] == [20]
    assert policy_before["primary_war_hostile_union_v1"]["observed_current_soldiers"] == 300
    assert observe_war_spending_priority_v1(value) == policy_before and value == before
    assert result["action_authorized"] is False and result["battle_win_probability"] is None


def test_current_strength_cache_and_stale_or_missing_counts_are_distinct():
    value = snapshot()
    for war in value["active_wars"]:
        for army in war["enemy_armies"]:
            army["soldiers"] = None
    value.update(army_strengths_status="available", army_strengths_queried_snapshot_id="native:7",
                 army_strengths_queried_revision=9, army_strengths=[
                     {"army_id": 11, "scope_role": "active_war_enemy", "war_ids": [10, 20], "status": "available", "current_soldiers": 300},
                     {"army_id": 12, "scope_role": "active_war_enemy", "war_ids": [20], "status": "available", "current_soldiers": 700},
                 ])
    assert observe_participating_war_threats_v1(value)["observed_enemy_raised_soldiers"] == 1000
    value["army_strengths_queried_revision"] = 8
    stale = observe_participating_war_threats_v1(value)
    assert stale["status"] == "observed" and stale["observed_enemy_raised_soldiers"] is None
    assert stale["unique_enemy_army_ids"] == [11, 12]


@pytest.mark.parametrize("missing", ["active_wars", "enemy_armies", "war_identity", "frame", "army_identity"])
def test_missing_source_is_unavailable_instead_of_an_empty_or_safe_scope(missing):
    value = snapshot()
    if missing == "active_wars":
        value.pop("active_wars")
    elif missing == "enemy_armies":
        value["active_wars"][1].pop("enemy_armies")
    elif missing == "war_identity":
        value["active_wars"][1]["war_id"] = 10
    elif missing == "frame":
        value["episode_run_id"] = None
    else:
        value["active_wars"][1]["enemy_armies"][1]["army_id"] = True
    result = observe_participating_war_threats_v1(value)
    assert result["status"] == "unavailable" and result["unique_enemy_army_ids"] is None
    assert result["observed_enemy_raised_soldiers"] is None and result["action_authorized"] is False


def test_conflicting_duplicates_keep_membership_and_unknown_strength():
    value = snapshot()
    value["active_wars"][1]["enemy_armies"][0]["soldiers"] = 301
    result = observe_participating_war_threats_v1(value)
    assert result["unique_enemy_army_ids"] == [11, 12]
    assert result["strength_status"] == "unavailable_or_conflicting"
    assert result["observed_enemy_raised_soldiers"] is None


def test_empty_observed_scope_and_unknown_leadership_do_not_claim_complete_war_safety():
    value = snapshot()
    value["active_wars"][1]["player_is_primary_war_leader"] = None
    result = observe_participating_war_threats_v1(value)
    assert result["leadership_unknown_war_ids"] == [20] and result["leadership_scope_complete"] is False
    value["active_wars"] = []
    empty = observe_participating_war_threats_v1(value)
    assert empty["status"] == "observed" and empty["observed_enemy_raised_soldiers"] == 0
    assert empty["unpublished_liege_wars_covered"] is False
    assert empty["unraised_or_future_enemy_reserves_bounded"] is False
