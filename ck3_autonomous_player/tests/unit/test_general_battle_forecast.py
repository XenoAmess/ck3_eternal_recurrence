import json
from pathlib import Path

from xar_autoplayer.simulation.general_battle_forecast import (
    contact_admission,
    forecast_fixed_contact,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "combat" / "live_rev4_player_attacks_357.json"


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
    assert "loaded_phase_event_effect_transition" in result["missing_required_domains"]
    assert forecast_fixed_contact(payload, **kwargs) == result
    assert forecast_fixed_contact(payload, **{**kwargs, "target_province_id": 1}) == {
        "status": "input_or_encounter_mismatch"
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
    assert unmodeled["unquantified_risks"] == ["commander_or_knight_death"]
