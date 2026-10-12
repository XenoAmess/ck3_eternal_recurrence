"""A strong aggregate prior is evidence, not declaration authority."""

from copy import deepcopy

import pytest

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_entry_contract import normalize_war_entry_assessments
from xar_autoplayer.simulation.prewar_battle_proxy import prewar_declaration_admission
from xar_autoplayer.strategy import (
    _forecast_required_war_entry_plan,
    _same_frame_campaign_root_context,
    _same_frame_war_entry_assessments,
    choose_one_life_turn,
)


ACTOR = 29_829
TARGET = 909
DATE = 53_171_400
REVISION = 5
DECLARE = "declare-war-909-17-0"
QUERY = "query-war-entry-assessments-v1-1-909"


def _snapshot():
    assessment = {
        "target_character_id": TARGET,
        "effective_target_character_id": TARGET,
        "distance_raw": 0,
        "actor_power_base_raw": 4_000_000,
        "actor_network_contribution_raw": 0,
        "actor_power_total_raw": 4_000_000,
        "target_power_base_raw": 1_000_000,
        "target_network_contribution_raw": 0,
        "target_pre_adjustment_total_raw": 1_000_000,
        "target_adjustment_delta_raw": 0,
        "target_power_total_raw": 1_000_000,
        "actual_power_ratio_raw": 25_000,
        "target_ai_context_actor_entry_raw": 0,
        "actor_ai_context_target_entry_raw": 1,
        "native_flags_raw": 3,
    }
    return {
        "snapshot_id": "native:5",
        "revision": 6,
        "native_revision": REVISION,
        "date_raw": DATE,
        "paused": True,
        "played_character": {"character_id": ACTOR, "alive": True},
        "active_wars": [],
        "player_armies": [],
        "declarable_wars": [{
            "declaration_id": "909-17-0",
            "target_character_id": TARGET,
            "casus_belli_index": 17,
            "casus_belli_key": "county_conquest_cb",
            "configuration_index": 0,
            "claimant_character_id": -1,
            "target_title_ids": [91],
            "source": "native",
        }],
        "war_entry_assessments": {
            "schema_version": 1,
            "status": "available",
            "snapshot_revision": REVISION,
            "date_raw": DATE,
            "actor_character_id": ACTOR,
            "requested_target_character_ids": [TARGET],
            "assessments": [assessment],
            "readiness": {
                "actor_identity_ready": True,
                "targets_declarable_ready": True,
                "effective_targets_ready": True,
                "ai_context_ready": True,
                "native_output_ready": True,
                "network_decomposition_ready": True,
                "same_frame_ready": True,
                "ready": True,
            },
            "provenance": {
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "assessment_rva": "0x1A23220",
                "network_collector_rva": "0x1A23FF0",
                "power_leaf": "CCharacter+0x1C0->+0x308",
                "fixed_point_scale": 100_000,
            },
        },
        "campaign_root_context": {
            "schema_version": 1,
            "status": "available",
            "snapshot_revision": REVISION,
            "date_raw": DATE,
            "player_character_id": ACTOR,
            "independent": True,
            "player_monthly_gold_income": {"raw": 400_000, "scale": 100_000},
            "player_domain_size": 2,
            "player_domain_limit": 5,
            "player_targeting_faction_count": 0,
            "government": {
                "key": "feudal_government",
                "flags": ["government_is_feudal", "government_is_settled"],
                "native_flag_count": 2,
            },
            "readiness": {"ready": True},
        },
    }


def _plan(snapshot, *, steps=None):
    return choose_one_life_turn(
        [{"index": 1, "command": "save-checkpoint", "ok": True}],
        snapshot=snapshot,
        action_steps=steps or {DECLARE, QUERY, "life-advance"},
    )


@pytest.mark.parametrize("wins,lower", [(252, 0.9605207372908033), (256, 1.0)])
def test_surrogate_risk_pass_cannot_authorize_real_strategy_consumer(monkeypatch, wins, lower):
    # Replay the observed score at the model boundary; admission and planning
    # remain production consumers, including their typed-action eligibility.
    forecast = {
        "status": "estimated",
        "sample_count": 256,
        "wins": wins,
        "losses": 256 - wins,
        "no_resolution": 0,
        "resolved_win_fraction": wins / 256,
        "resolved_win_wilson95_lower": lower,
        "model_fidelity": "aggregate-prewar-surrogate-not-native-parity",
        "calibrated_probability": False,
    }
    admission = prewar_declaration_admission(forecast)
    assert admission["proxy_risk_budget_passed"] is True
    assert admission["admitted"] is False
    monkeypatch.setattr("xar_autoplayer.strategy.forecast_prewar_power_battle", lambda *a, **k: deepcopy(forecast))
    snapshot = _snapshot()
    candidate = {
        "rule_id": "general-native-war-entry-battle-prior-v1",
        "typed_declaration_step": DECLARE,
        "typed_declaration_available": True,
    }
    plan = _forecast_required_war_entry_plan(
        snapshot["declarable_wars"][0],
        snapshot["war_entry_assessments"]["assessments"][0],
        candidate, snapshot["campaign_root_context"], {DECLARE, "life-advance"},
    )
    assert plan["selected_step"] == "life-advance"
    assert plan["decision"]["outcome"] == "NO_DECLARE"
    assert plan["decision"]["automatic_declaration_enabled"] is False


def test_real_legal_native_inputs_remain_candidates_without_becoming_authority():
    snapshot = _snapshot()
    before = deepcopy(snapshot)
    plan = _plan(snapshot)
    assert snapshot == before
    assert plan["phase"] == "native_war_entry_forecast_required"
    assert plan["war_entry_candidate"]["typed_declaration_available"] is True
    assert plan["war_entry_assessment"] == before["war_entry_assessments"]["assessments"][0]
    assert plan["campaign_root_context"]["player_character_id"] == ACTOR
    assert plan["campaign_root_context"]["date_raw"] == DATE
    assert plan["prewar_forecast_admission"]["proxy_risk_budget_passed"] is True
    assert plan["decision"]["outcome"] == "NO_DECLARE"
    assert plan["selected_step"] == "life-advance"
    assert plan["decision"]["automatic_declaration_enabled"] is False


@pytest.mark.parametrize("field", ["actor_network_contribution_raw", "target_network_contribution_raw"])
@pytest.mark.parametrize("unknown", [None, False, "missing"])
def test_unknown_coalition_power_is_not_normalized_as_known_zero(field, unknown):
    snapshot = _snapshot()
    payload = snapshot["war_entry_assessments"]
    known = normalize_war_entry_assessments(payload, expected_target_character_ids=[TARGET])
    assert known["assessments"][0][field] == 0
    if unknown == "missing":
        del payload["assessments"][0][field]
    else:
        payload["assessments"][0][field] = unknown
    with pytest.raises(ValueError):
        normalize_war_entry_assessments(payload, expected_target_character_ids=[TARGET])
    assert _same_frame_war_entry_assessments([], snapshot) == {}
    assert _plan(snapshot)["selected_step"] == QUERY


def test_unknown_faction_count_requests_evidence_instead_of_claiming_known_empty():
    snapshot = _snapshot()
    del snapshot["campaign_root_context"]["player_targeting_faction_count"]
    plan = _plan(snapshot, steps={DECLARE, "query-player-faction-alerts-v1", "life-advance"})
    assert plan["selected_step"] == "query-player-faction-alerts-v1"
    assert plan["war_entry_faction_context"]["status"] == "unavailable"
    assert plan["war_entry_faction_context"]["targeting_faction_count"] is None
    assert plan["war_entry_faction_context"]["prior_scope_eligible"] is False


@pytest.mark.parametrize("field", ["actor_character_id", "date_raw", "snapshot_revision"])
@pytest.mark.parametrize("via_history", [False, True])
def test_assessment_must_match_current_actor_date_and_revision(field, via_history):
    snapshot = _snapshot()
    assert TARGET in _same_frame_war_entry_assessments([], snapshot)
    payload = snapshot["war_entry_assessments"]
    payload[field] += 1
    history = []
    if via_history:
        history = [{"command": QUERY, "ok": True, "result": {"war_entry_assessments": payload}}]
        del snapshot["war_entry_assessments"]
    assert _same_frame_war_entry_assessments(history, snapshot) == {}


@pytest.mark.parametrize("field", ["player_character_id", "date_raw", "snapshot_revision"])
@pytest.mark.parametrize("via_history", [False, True])
def test_campaign_scope_must_match_current_actor_date_and_revision(field, via_history):
    snapshot = _snapshot()
    assert _same_frame_campaign_root_context([], snapshot) is snapshot["campaign_root_context"]
    payload = snapshot["campaign_root_context"]
    payload[field] += 1
    history = []
    if via_history:
        history = [{"command": "query-campaign-root-context-v1", "ok": True,
                    "result": {"campaign_root_context": payload}}]
        del snapshot["campaign_root_context"]
    assert _same_frame_campaign_root_context(history, snapshot) is None


def test_assessment_target_request_scope_is_not_interchangeable():
    payload = _snapshot()["war_entry_assessments"]
    with pytest.raises(ValueError, match="requested target order mismatch"):
        normalize_war_entry_assessments(payload, expected_target_character_ids=[TARGET + 1])
