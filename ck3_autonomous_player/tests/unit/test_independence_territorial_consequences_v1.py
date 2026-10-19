"""Reviewed selectors do not turn target overlap or an ally into title loss."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.independence_territorial_consequences_v1 import (
    SOURCE_HASHES, observe_current_independence_war_consequences_v1,
    reviewed_independence_rule_v1,
)


def inputs(cb="independence_war"):
    war = {"war_id": 10, "source": "native", "player_side": "defender",
           "player_is_primary_war_leader": False, "player_relative_war_score": -50,
           "primary_opponent_character_id": 300, "targeted_title_ids": [2230]}
    snapshot = {"snapshot_id": "native:7", "revision": 9, "native_revision": 7,
                "date_raw": 53144328, "episode_run_id": "synthetic-independence",
                "paused": True, "map_ready": True, "diagnostics": {"connection_generation": 3},
                "played_character": {"character_id": 100, "alive": True}, "active_wars": [war]}
    snapshot["war_termination_options"] = [{
        **{k: war[k] for k in ("war_id", "source", "player_side", "player_is_primary_war_leader", "player_relative_war_score")},
        "query_sequence": 1, "queried_snapshot_id": "native:7", "queried_revision": 9,
        "queried_native_revision": 7, "queried_connection_generation": 3,
        "episode_run_id": "synthetic-independence", "active_casus_belli_present": True,
        "active_casus_belli_identity": {"database_index": 4, "canonical_key": cb}}]
    value = {"schema": "xar.ck3.war-occupation-targets.v1", "schema_version": 1,
             "status": "available", "available": True, "collection_complete": True,
             "unavailable_reason": None, "snapshot_revision": 7, "date_raw": 53144328,
             "war_id": 10, "actor_character_id": 100, "player_side": "defender",
             "primary_attacker_character_id": 300, "primary_defender_character_id": 200,
             "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
             "rows": [], "side_counts": [{"territory_side": side, "eligible": 0, "occupied": 0,
                 "native_candidate_count": 0, "collection_complete": True} for side in ("attacker", "defender")]}
    occupation = {"accepted": True, "read_only": True, "status": "available",
                  "step": "query-war-occupation-targets-v1-10", "query_sequence": 2,
                  "queried_snapshot_id": "native:7", "queried_revision": 9,
                  "queried_native_revision": 7, "queried_connection_generation": 3,
                  "queried_episode_run_id": "synthetic-independence", "war_occupation_targets_v1": value}
    root = {"status": "available", "player_character_id": 100, "snapshot_revision": 7,
            "date_raw": 53144328, "held_title_partition": [{"title": {"title_id": 2230}}]}
    return snapshot, occupation, root


@pytest.mark.parametrize("key,selector,effect", [
    ("independence_war", "primary_attacker", "change_liege_or_become_independent"),
    ("independence_faction_war", "current_joined_faction_members_else_flagged_war_attackers", "change_liege_or_become_independent"),
    ("grant_independence_interaction", "recipient", "becomes_independent"),
])
def test_source_closed_independence_types_have_distinct_effect_selectors(key, selector, effect):
    rule = reviewed_independence_rule_v1(key, SOURCE_HASHES)
    assert rule["status"] == "source_reviewed" and rule["affected_principal_selector"] == selector
    assert rule["territorial_effect"] == effect and rule["action_authorized"] is False
    assert rule["loaded_definition_verified"] is False and rule["current_legality_verified"] is False
    if effect == "change_liege_or_become_independent":
        assert "otherwise: change_liege to current_liege.liege" in rule["helper_branch"]


def test_nonprimary_target_overlap_is_not_a_loss_enumeration_or_war_result():
    snapshot, occupation, root = inputs()
    before = deepcopy((snapshot, occupation, root))
    result = observe_current_independence_war_consequences_v1(snapshot, war_id=10,
        source_hashes=SOURCE_HASHES, occupation_result=occupation, campaign_root=root)
    assert result["status"] == "source_bound_current_war_observed"
    assert result["selected_principal_character_ids"] == [300]  # primary attacker, not player/ally/target-holder guess
    assert result["observed_primary_roles"]["primary_defender_character_id"] == 200
    assert result["directly_held_target_identity_overlap"] == [2230]
    assert result["affected_title_ids"] is None and result["title_extent_complete"] is False
    assert result["defender_realm_shrinkage_verified"] is False and result["war_resolution_verified"] is False
    assert result["action_authorized"] is False and (snapshot, occupation, root) == before


def test_faction_principals_remain_unknown_without_actual_membership_or_flags():
    snapshot, occupation, root = inputs("independence_faction_war")
    result = observe_current_independence_war_consequences_v1(snapshot, war_id=10,
        source_hashes=SOURCE_HASHES, occupation_result=occupation, campaign_root=root)
    assert result["observed_primary_roles"] is not None
    assert result["selected_principal_character_ids"] is None and result["principal_selection_complete"] is False
    assert "current_affected_principal_selection" in result["unresolved"]


@pytest.mark.parametrize("changed", ["source", "cb_frame", "occupation_frame", "occupation_role", "root_frame"])
def test_wrong_or_missing_sources_preserve_unknown_instead_of_cross_frame_credit(changed):
    snapshot, occupation, root = inputs()
    hashes = dict(SOURCE_HASHES)
    if changed == "source":
        hashes["common/casus_belli_types/00_civil_war.txt"] = "0" * 64
    elif changed == "cb_frame":
        snapshot["war_termination_options"][0]["queried_native_revision"] = 6
    elif changed == "occupation_frame":
        occupation["queried_connection_generation"] = 2
    elif changed == "occupation_role":
        occupation["war_occupation_targets_v1"]["primary_defender_character_id"] = 100
    else:
        root["date_raw"] -= 24
    result = observe_current_independence_war_consequences_v1(snapshot, war_id=10,
        source_hashes=hashes, occupation_result=occupation, campaign_root=root)
    if changed in {"source", "cb_frame"}:
        assert result["status"] == "unavailable"
    elif changed in {"occupation_frame", "occupation_role"}:
        assert result["status"] == "source_bound_current_war_observed"
        assert result["selected_principal_character_ids"] is None and result["observed_primary_roles"] is None
    else:
        assert result["directly_held_target_identity_overlap"] is None
    assert result["affected_title_ids"] is None and result["action_authorized"] is False


def test_missing_occupation_and_unknown_cb_do_not_manufacture_principals():
    snapshot, _, root = inputs()
    result = observe_current_independence_war_consequences_v1(snapshot, war_id=10,
        source_hashes=SOURCE_HASHES, campaign_root=root)
    assert result["selected_principal_character_ids"] is None
    snapshot["war_termination_options"][0]["active_casus_belli_identity"]["canonical_key"] = "unknown_future_cb"
    assert observe_current_independence_war_consequences_v1(snapshot, war_id=10,
        source_hashes=SOURCE_HASHES)["status"] == "unavailable"
