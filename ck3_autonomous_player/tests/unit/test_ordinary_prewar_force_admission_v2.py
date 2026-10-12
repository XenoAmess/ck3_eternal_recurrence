"""Ordinary policy consumes real v2 validators; these DTOs are unit inputs."""

from __future__ import annotations

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.declaration_contract import declare_war_step
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.ordinary_prewar_force_admission_v2 import (
    assess_ordinary_prewar_force_admission_v2,
)
from xar_autoplayer.strategy import choose_one_life_turn
from test_prewar_surrogate_authority_regression import _snapshot


DOMAIN = "prewar_force_coalition_coverage_v2"
QUERY = "prewar_force_coalition_coverage_v2_query"
SELECTED_FIELDS = (
    "target_character_id", "casus_belli_index", "casus_belli_key",
    "configuration_index", "claimant_character_id", "target_title_ids",
)


def _evidence(*, lower=1500, upper=1000, path="general"):
    # Reuse the actual existing planner-input fixture, not a mocked planner.
    snapshot = _snapshot()
    snapshot["map_ready"] = True
    snapshot["episode_run_id"] = "unit-current-episode"
    snapshot["diagnostics"] = {
        "connection_generation": 2,
        "hello": {
            "bridge_version": "0.1.0.4",
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        },
    }
    declaration = snapshot["declarable_wars"][0]
    actor = snapshot["played_character"]["character_id"]
    target = declaration["target_character_id"]
    if path == "de_jure":
        declaration.update(
            casus_belli_key="individual_county_de_jure_cb",
            configuration_index=-1,
            declaration_id=f"{target}-17--1",
        )
    elif path == "player_claim":
        declaration.update(casus_belli_key="claim_cb", claimant_character_id=actor)
        root = snapshot["campaign_root_context"]
        root["readiness"].update(
            adjacent_external_province_holders_ready=True,
            related_character_contexts_ready=True,
        )
        root["adjacent_external_province_holder_character_ids"] = [target]
        root["related_character_contexts"] = [{
            "character_id": target,
            "relationship_role": "adjacent_external_province_holder",
            "independent": True,
            "primary_title": {"tier_raw": 2, "tier_key": "county", "title_id": 91},
        }]
    selected = {key: deepcopy(declaration[key]) for key in SELECTED_FIELDS}
    value = {
        "schema_version": 2, "status": "available", "read_only": True,
        "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "capture_epoch": 17, "native_revision": snapshot["native_revision"],
        "public_revision": snapshot["revision"], "date_raw": snapshot["date_raw"],
        "actor_character_id": actor, "declaration_id": declaration["declaration_id"],
        "selected_declaration": selected, "effective_target_character_id": None,
        "ticket": 13, "query_sequence": 13,
        "two_round_observation": {
            "round_count": 2, "complete_dto_equal": True,
            "frame_binding_equal": True, "unavailable_reason": None,
        },
        "final_cb_roles": {
            "available": True, "unavailable_reason": None,
            "primary_attacker_character_id": actor,
            "primary_defender_character_id": target,
            "source": "finalized_selected_cb_context", "native_fallback": False,
            "final_can_send": True,
        },
        "potential_enemy_participants": {
            "available": True, "unavailable_reason": None,
            "collection_complete": True,
            "participants": [{"character_id": target, "sources": ["primary_defender"]}],
            "current_allies_complete": True, "holy_joiners_complete": True,
            "additional_supporters_complete": True, "selected_cb_initial_complete": True,
        },
        "owner_forces": [{
            "owner_character_id": actor, "actor_lower_soldiers": lower,
            "actor_lower_ready": True, "inventory_upper_soldiers": lower,
            "inventory_upper_ready": True,
            "inventory_scope": "same_frame_owned_current_inventory_v1",
            "unavailable_reasons": [],
        }, {
            "owner_character_id": target, "actor_lower_soldiers": None,
            "actor_lower_ready": False, "inventory_upper_soldiers": upper,
            "inventory_upper_ready": True,
            "inventory_scope": "same_frame_owned_current_inventory_v1",
            "unavailable_reasons": [],
        }],
        "native_mobilization_qualification": {
            "available": True, "unavailable_reason": None,
            "source": "actual4_raise_command_final_validator_and_owned_current_rosters",
            "native_raise_legal": True, "default_raise_province_id": 1,
            "unraised_lower_soldiers": lower, "unraised_lower_ready": True,
            "raised_commandable_lower_soldiers": None, "raised_lower_ready": False,
            "executable_lower_soldiers": lower, "executable_lower_ready": True,
            "physical_inventory_lower_soldiers": lower,
            "native_unraised_stock_soldiers": lower, "native_unraised_stock_ready": True,
            "component_combination": "maximum_proven_component",
        },
        "actor_lower_soldiers": lower, "enemy_upper_soldiers": upper,
        "enemy_force_coverage_complete": True,
        "complete_initial_participants_ready": True, "missing_required_domains": [],
    }
    envelope = {
        "accepted": True, "status": "available", DOMAIN: value,
        "execution_receipt": {"ticket": 13, "query_sequence": 13, "capture_epoch": 17},
        "native_request_id": "unit-fresh-request",
        "selected_declaration_source": deepcopy(declaration),
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"],
        "queried_date_raw": snapshot["date_raw"],
        "queried_actor_character_id": actor,
        "queried_connection_generation": 2,
        "queried_episode_run_id": snapshot["episode_run_id"],
    }
    snapshot[QUERY] = envelope
    return snapshot, declaration, value, envelope


def _admission(snapshot, declaration):
    return assess_ordinary_prewar_force_admission_v2(snapshot, declaration)


def _plan(snapshot, declaration):
    return choose_one_life_turn(
        [{"index": 1, "command": "save-checkpoint", "ok": True}],
        snapshot=snapshot,
        action_steps={declare_war_step(declaration["declaration_id"]), "life-advance"},
    )


@pytest.mark.parametrize("lower,upper,admitted", [(1500, 1000, True), (1499, 1000, False), (0, 0, False), (1, 0, True)])
def test_exact_current_force_boundary_uses_real_assessor(lower, upper, admitted):
    snapshot, declaration, _, _ = _evidence(lower=lower, upper=upper)
    before = deepcopy(snapshot)
    result = _admission(snapshot, declaration)
    assert result["declare_admitted"] is admitted
    assert result["force_risk_qualified"] is admitted
    assert result["force_risk"]["policy"]["minimum_actor_to_enemy_ratio_numerator"] == 3
    assert result["force_risk"]["policy"]["minimum_actor_to_enemy_ratio_denominator"] == 2
    assert result["force_risk"]["policy"]["assumption"] == "policy_margin_not_calibrated_probability"
    assert snapshot == before


@pytest.mark.parametrize("path", ["general", "de_jure", "player_claim"])
def test_all_three_real_planner_paths_can_declare_full_qualified_inputs(path):
    snapshot, declaration, _, _ = _evidence(path=path)
    before = deepcopy(snapshot)
    plan = _plan(snapshot, declaration)
    assert plan["decision"]["outcome"] == "DECLARE"
    assert plan["selected_step"] == declare_war_step(declaration["declaration_id"])
    assert plan["prewar_force_admission"]["force_risk_qualified"] is True
    assert snapshot == before
    expected_rule = {
        "general": "general-native-war-entry-battle-prior-v1",
        "de_jure": "feudal-single-county-de-jure-forecast-candidate-v1",
        "player_claim": "feudal-adjacent-independent-county-player-claim-forecast-candidate-v1",
    }
    assert plan["decision"]["policy"] == expected_rule[path]


def test_network_proxy_exclusion_does_not_override_full_current_force():
    snapshot, declaration, _, _ = _evidence()
    assessment = snapshot["war_entry_assessments"]["assessments"][0]
    assessment["actor_network_contribution_raw"] = 500_000
    assessment["actor_power_total_raw"] = 4_500_000
    plan = _plan(snapshot, declaration)
    assert plan["decision"]["outcome"] == "DECLARE"
    assert plan["prewar_force_admission"]["declare_admitted"] is True


def test_known_empty_enemy_can_declare_when_the_old_proxy_has_no_estimate():
    snapshot, declaration, _, _ = _evidence(lower=1, upper=0)
    assessment = snapshot["war_entry_assessments"]["assessments"][0]
    assessment.update(
        target_power_base_raw=0, target_pre_adjustment_total_raw=0,
        target_power_total_raw=0, actual_power_ratio_raw=0,
    )
    plan = _plan(snapshot, declaration)
    assert plan["decision"]["outcome"] == "DECLARE"
    assert plan["prewar_force_admission"]["declare_admitted"] is True
    assert plan["prewar_battle_forecast"]["status"] == "native_power_input_unavailable"
    assert plan["prewar_forecast_admission_available"] is False


def test_known_nullable_native_campaign_episode_can_declare():
    snapshot, declaration, _, envelope = _evidence()
    snapshot["episode_run_id"] = None
    envelope["queried_episode_run_id"] = None
    assert _plan(snapshot, declaration)["decision"]["outcome"] == "DECLARE"


def test_negative_proxy_margin_does_not_redirect_a_qualified_current_declaration():
    snapshot, declaration, _, _ = _evidence()
    assessment = snapshot["war_entry_assessments"]["assessments"][0]
    assessment.update(
        target_power_base_raw=5_000_000,
        target_pre_adjustment_total_raw=5_000_000,
        target_power_total_raw=5_000_000,
        actual_power_ratio_raw=125_000,
    )
    alternative = deepcopy(declaration)
    alternative.update(target_character_id=910, declaration_id="910-17-0")
    snapshot["declarable_wars"].append(alternative)
    plan = choose_one_life_turn(
        [{"index": 1, "command": "save-checkpoint", "ok": True}],
        snapshot=snapshot,
        action_steps={
            declare_war_step(declaration["declaration_id"]), "life-advance",
            "query-war-entry-assessments-v1-1-910",
        },
    )
    assert plan["decision"]["outcome"] == "DECLARE"
    assert plan["selected_step"] == declare_war_step(declaration["declaration_id"])


@pytest.mark.parametrize("field", ["queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_date_raw", "queried_actor_character_id", "queried_connection_generation", "queried_episode_run_id"])
def test_each_current_lease_mismatch_blocks_declaration(field):
    snapshot, declaration, _, envelope = _evidence()
    envelope[field] = "stale" if isinstance(envelope[field], str) else envelope[field] + 1
    result = _admission(snapshot, declaration)
    assert result["declare_admitted"] is False
    assert result["reason"] == "force_coalition_query_scope_stale"
    assert result["required_prewar_force_coalition_query"] is None


def test_missing_evidence_requests_one_formal_typed_prefetch():
    snapshot, declaration, _, _ = _evidence()
    del snapshot[QUERY]
    result = _admission(snapshot, declaration)
    assert result["declare_admitted"] is False
    assert result["required_prewar_force_coalition_query"] == {
        "declaration_id": declaration["declaration_id"],
        "expected_revision": snapshot["revision"], "profile": "v2",
    }
    plan = _plan(snapshot, declaration)
    assert plan["required_prewar_force_coalition_query"] == result["required_prewar_force_coalition_query"]


@pytest.mark.parametrize("kind", ["partial", "failed", "unknown", "missing_episode"])
def test_present_unknown_does_not_repeat_a_query_or_declare(kind):
    snapshot, declaration, _, envelope = _evidence()
    if kind == "partial":
        envelope["status"] = "partial"
    elif kind == "failed":
        envelope["accepted"] = False
    elif kind == "unknown":
        envelope[DOMAIN] = None
    else:
        snapshot["episode_run_id"] = None
        del envelope["queried_episode_run_id"]
    result = _admission(snapshot, declaration)
    assert result["declare_admitted"] is False
    assert result["required_prewar_force_coalition_query"] is None


@pytest.mark.parametrize("legal", [False, None])
def test_current_final_can_send_is_not_overridden_by_older_legal_catalogue(legal):
    snapshot, declaration, value, _ = _evidence()
    value["final_cb_roles"]["final_can_send"] = legal
    result = _admission(snapshot, declaration)
    assert result["declare_admitted"] is False
    assert _plan(snapshot, declaration)["decision"]["outcome"] == "NO_DECLARE"


@pytest.mark.parametrize("damage", ["duplicate_owner", "duplicate_participant", "missing_enemy_owner", "ally_closure_missing", "missing_mobilization", "wrong_native_receipt", "receipt_request_override", "scope_tuple_changed", "boolean_floor"])
def test_incomplete_or_conflicting_inventory_never_produces_permission(damage):
    snapshot, declaration, value, envelope = _evidence()
    if damage == "duplicate_owner":
        value["owner_forces"].append(deepcopy(value["owner_forces"][1]))
    elif damage == "duplicate_participant":
        value["potential_enemy_participants"]["participants"] *= 2
    elif damage == "missing_enemy_owner":
        value["owner_forces"].pop()
    elif damage == "ally_closure_missing":
        value["potential_enemy_participants"]["current_allies_complete"] = False
    elif damage == "missing_mobilization":
        del value["native_mobilization_qualification"]
    elif damage == "wrong_native_receipt":
        envelope["execution_receipt"]["capture_epoch"] += 1
    elif damage == "receipt_request_override":
        envelope["execution_receipt"]["request_id"] = "not-the-outer-id"
    elif damage == "scope_tuple_changed":
        value["selected_declaration"]["target_title_ids"] = [92]
    else:
        value["actor_lower_soldiers"] = True
    assert _admission(snapshot, declaration)["declare_admitted"] is False


@pytest.mark.parametrize("physical,stock", [(1500, 1), (1, 1500)])
def test_minimum_proven_unraised_component_is_not_a_large_inventory_proxy(physical, stock):
    snapshot, declaration, value, _ = _evidence(lower=1)
    mob = value["native_mobilization_qualification"]
    mob["physical_inventory_lower_soldiers"] = physical
    mob["native_unraised_stock_soldiers"] = stock
    value["owner_forces"][0]["inventory_upper_soldiers"] = physical
    assert _admission(snapshot, declaration)["status"] == "risk_rejected"


def test_false_raise_with_independently_commandable_standing_force_can_qualify():
    snapshot, declaration, value, _ = _evidence()
    mob = value["native_mobilization_qualification"]
    mob.update(native_raise_legal=False, raised_commandable_lower_soldiers=1500, raised_lower_ready=True)
    assert _admission(snapshot, declaration)["declare_admitted"] is True


def test_unproven_sum_of_raised_and_unraised_components_cannot_inflate_lower():
    snapshot, declaration, value, _ = _evidence()
    mob = value["native_mobilization_qualification"]
    mob.update(raised_commandable_lower_soldiers=1500, raised_lower_ready=True, executable_lower_soldiers=3000)
    mob["physical_inventory_lower_soldiers"] = 3000
    value["actor_lower_soldiers"] = 3000
    value["owner_forces"][0]["actor_lower_soldiers"] = 3000
    value["owner_forces"][0]["inventory_upper_soldiers"] = 3000
    assert _admission(snapshot, declaration)["declare_admitted"] is False


@pytest.mark.parametrize("guard", ["budget", "faction", "controller"])
def test_full_force_does_not_bypass_other_real_planner_guards(guard):
    snapshot, declaration, _, _ = _evidence()
    if guard == "budget":
        snapshot["campaign_root_context"]["player_monthly_gold_income"]["raw"] = 0
    elif guard == "faction":
        snapshot["campaign_root_context"]["player_targeting_faction_count"] = None
    else:
        snapshot["played_character"]["alive"] = False
    plan = _plan(snapshot, declaration)
    assert plan.get("decision", {}).get("outcome") != "DECLARE"
    assert plan["selected_step"] != declare_war_step(declaration["declaration_id"])
