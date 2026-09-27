import json
from copy import deepcopy
from pathlib import Path

from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
from xar_autoplayer.simulation.general_battle_forecast import (
    _native_precontact_advantage,
    contact_admission,
    forecast_fixed_contact,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "combat" / "live_rev4_player_attacks_357.json"
V3_FIXTURE = (
    Path(__file__).parents[2] / "native_bridge" / "research" / "fixtures"
    / "combat_simulation_inputs_v3_production_available.json"
)


def _precontact_case():
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = source["combat_simulation_inputs"]
    scenario = base["scenario"]
    payload = {"completeness": {"input_observation_ready": True}, "base_inputs": base}
    kwargs = dict(
        target_province_id=base["target_province_id"],
        attacker_entry_province_id=scenario["attacker_entry_province_id"],
        attacker_army_ids=tuple(scenario["attacker_army_ids"]),
        defender_army_ids=tuple(scenario["defender_army_ids"]),
        capture=source["capture"],
        sample_count=16,
        horizon_days=4,
    )
    return payload, kwargs


def _synthetic_native_advantage(payload, zero_roll_raw):
    """Unit seam only: synthesize v3 helpers for the frozen v2 live base."""
    base = payload["base_inputs"]
    sides = []
    side_inputs = []
    for role in ("attacker", "defender"):
        armies = [army for army in base["armies"] if army["encounter_role"] == role]
        commander_id = armies[0]["commander"]["character_id"]
        sides.append({
            "side": role,
            "battle_commander_character_id": commander_id,
            "battle_commander_selected": commander_id is not None,
            "battle_commander_selection": "native_0x23C8A60",
            "roll_points": 0, "roll_raw": 0,
            "target_conditionals_residual_raw": 0,
            "commander_dynamic_raw": 0, "side_dynamic_raw": 0,
            "side_total_raw": 0,
        })
        side_inputs.append({
            "side": role, "primary_army_id": armies[0]["army_id"],
            "ordered_army_ids": [army["army_id"] for army in armies],
        })
    payload["schema_version"] = 3
    payload["contract_stage"] = "production_exact_132_refs"
    payload["phase_event_inputs"] = {
        "status": "available",
        "advantage_model": {
            "status": "available", "scale": 100_000,
            "scenario_policy": base["participant_policy"],
            "observation_origin": "native_exact_build_production",
            "side_inputs": side_inputs,
            "base_static_accumulator_raw": zero_roll_raw,
            "resolved_dynamic": {
                "status": "available", "helper_status": "original_helpers_matched",
                "roll_policy": "zero_in_query_sampled_offline",
                "original_total_helper_match": True,
                "sides": sides,
                "side_0_dynamic_raw": 0, "side_1_dynamic_raw": 0,
                "resolved_advantage_at_zero_roll_raw": zero_roll_raw,
                "original_total_helper_raw": zero_roll_raw,
            },
        },
    }


def test_frozen_live_encounter_produces_bounded_whole_battle_distribution():
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = source["combat_simulation_inputs"]
    scenario = base["scenario"]
    payload = {"completeness": {"input_observation_ready": True}, "base_inputs": base}
    kwargs = dict(
        target_province_id=base["target_province_id"],
        attacker_entry_province_id=scenario["attacker_entry_province_id"],
        attacker_army_ids=tuple(scenario["attacker_army_ids"]),
        defender_army_ids=tuple(scenario["defender_army_ids"]),
        capture=source["capture"],
        sample_count=16,
    )
    result = forecast_fixed_contact(payload, **kwargs)
    assert result["status"] == "estimated"
    assert result["sample_count"] == 16
    assert result["player_wins"] + result["player_losses"] + result["no_resolution"] == 16
    assert result["native_parity"] is False
    assert result["commander_or_knight_death_probability"] is None
    assert result["character_death_risk_status"] == "unmodeled_phase_events"
    assert "future_daily_effective_stat_refresh_unmodeled" in result["assumptions"]
    assert "future_daily_combat_width_refresh_unmodeled" in result["assumptions"]
    assert "future_daily_non_roll_advantage_refresh_unmodeled" in result["assumptions"]
    assert "loaded_phase_event_effect_transition" in result["missing_required_domains"]
    assert forecast_fixed_contact(payload, **kwargs) == result
    assert forecast_fixed_contact(payload, **{**kwargs, "target_province_id": 1}) == {
        "status": "input_or_encounter_mismatch"
    }


def test_same_frame_native_zero_roll_value_reaches_real_forecast_kernel():
    payload, kwargs = _precontact_case()
    fallback = forecast_fixed_contact(payload, **kwargs)
    assert fallback["status"] == "estimated"
    assert fallback["advantage_input"]["source"] == "generic_commander_and_stock_static_approximation"
    _synthetic_native_advantage(payload, -20_000_000)
    native = forecast_fixed_contact(payload, **kwargs)
    assert native["status"] == "estimated"
    assert native["advantage_input"]["source"] == "same_frame_v3_native_zero_roll_frozen_future"
    assert native["advantage_input"]["zero_roll_raw"] == -20_000_000
    assert native["advantage_input"]["model_sha256"] is not None
    assert native["advantage_input"]["future_daily_refresh_modeled"] is False
    assert "same_frame_native_advantage_frozen_for_future_days" in native["assumptions"]
    # The same frozen base and RNG seed produce different casualties only if
    # the actual kernel consumes the native helper, not just output metadata.
    assert native["player_p90_hard_loss_raw"] != fallback["player_p90_hard_loss_raw"]
    assert native["input_sha256"] == fallback["input_sha256"]


def test_actual_production_v3_wire_shape_binds_original_helper():
    # The checked-in v3 production fixture includes an ongoing combat, so it
    # is used only to test DTO extraction, never precontact forecast admission.
    wire = json.loads(V3_FIXTURE.read_text(encoding="utf-8"))["result"]["combat_simulation_inputs"]
    frozen = freeze_combat_simulation_input(wire["base_inputs"], capture={})
    selected = _native_precontact_advantage(wire, frozen)
    assert selected is not None
    assert selected[:4] == (16777217, 16777218, -600_000, (16777218, None))


def test_native_phase_unavailable_falls_back_but_malformed_available_rejects():
    payload, kwargs = _precontact_case()
    baseline = forecast_fixed_contact(payload, **kwargs)
    payload["schema_version"] = 3
    payload["contract_stage"] = "production_exact_132_refs"
    payload["completeness"]["input_observation_ready"] = False
    payload["phase_event_inputs"] = {"status": "unavailable"}
    fallback = forecast_fixed_contact(payload, **kwargs)
    assert fallback["status"] == "estimated"
    assert fallback["player_p90_hard_loss_raw"] == baseline["player_p90_hard_loss_raw"]
    assert fallback["advantage_input"]["fallback_reason"] == "phase_event_inputs_unavailable"
    _synthetic_native_advantage(payload, -600_000)
    payload["phase_event_inputs"]["advantage_model"]["resolved_dynamic"]["original_total_helper_raw"] += 1
    assert forecast_fixed_contact(payload, **kwargs) == {
        "status": "model_unavailable", "error_type": "CombatInputError"
    }
    _synthetic_native_advantage(payload, -600_000)
    payload["phase_event_inputs"]["advantage_model"]["resolved_dynamic"]["sides"][0]["battle_commander_character_id"] = 42
    assert forecast_fixed_contact(payload, **kwargs) == {
        "status": "model_unavailable", "error_type": "CombatInputError"
    }


def test_bounded_model_can_admit_without_native_parity_and_reject_risk():
    forecast = {
        "status": "estimated",
        "native_parity": False,
        "resolved_win_wilson95": {"lower": 0.8},
        "player_p90_hard_loss_fraction": 0.1,
        "player_stack_wipe_probability": 0.01,
        "commander_or_knight_death_probability": 0.01,
        "no_resolution": 0,
        "sample_count": 100,
    }
    assert contact_admission(forecast)["admitted"] is True
    assert contact_admission(forecast, defensive_relief=True)["admitted"] is True
    assert contact_admission({**forecast, "player_p90_hard_loss_fraction": 0.4})["admitted"] is False
    assert contact_admission({**forecast, "commander_or_knight_death_probability": 0.06})["admitted"] is False
    unmodeled = contact_admission({**forecast, "commander_or_knight_death_probability": None})
    assert unmodeled["admitted"] is True
    assert unmodeled["character_death_risk_modeled"] is False
    assert unmodeled["risk_limits"]["death"] is None
    assert unmodeled["unquantified_risks"] == [
        "commander_or_knight_death", "future_reinforcement_and_participant_exit",
        "voluntary_retreat", "future_daily_effective_stat_refresh",
        "future_daily_combat_width_refresh", "future_daily_non_roll_advantage_refresh",
    ]


def test_active_combat_context_cannot_be_reused_as_precontact_forecast():
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = deepcopy(source["combat_simulation_inputs"])
    base["ongoing_combats"] = [{"combat_id": 16777218}]
    scenario = base["scenario"]
    payload = {"completeness": {"input_observation_ready": True}, "base_inputs": base}
    result = forecast_fixed_contact(
        payload,
        target_province_id=base["target_province_id"],
        attacker_entry_province_id=scenario["attacker_entry_province_id"],
        attacker_army_ids=tuple(scenario["attacker_army_ids"]),
        defender_army_ids=tuple(scenario["defender_army_ids"]),
        capture=source["capture"],
        sample_count=16,
    )
    assert result == {"status": "active_combat_requires_resume_input"}


def test_precontact_forecast_requires_explicit_ongoing_combat_observation():
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = deepcopy(source["combat_simulation_inputs"])
    del base["ongoing_combats"]
    scenario = base["scenario"]
    payload = {"completeness": {"input_observation_ready": True}, "base_inputs": base}
    assert forecast_fixed_contact(
        payload,
        target_province_id=base["target_province_id"],
        attacker_entry_province_id=scenario["attacker_entry_province_id"],
        attacker_army_ids=tuple(scenario["attacker_army_ids"]),
        defender_army_ids=tuple(scenario["defender_army_ids"]),
        capture=source["capture"],
        sample_count=16,
    ) == {"status": "input_or_encounter_mismatch"}
