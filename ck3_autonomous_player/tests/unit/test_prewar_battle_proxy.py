from xar_autoplayer.simulation.prewar_battle_proxy import (
    forecast_prewar_power_battle,
    prewar_declaration_admission,
)


def test_prewar_aggregate_trials_are_reproducible_and_expose_assumptions():
    assessment = {
        "actor_power_base_raw": 4_000_000,
        "target_power_total_raw": 1_000_000,
        "actor_network_contribution_raw": 0,
        "target_network_contribution_raw": 0,
    }
    first = forecast_prewar_power_battle(assessment, declaration_id="candidate-1")
    assert first == forecast_prewar_power_battle(assessment, declaration_id="candidate-1")
    assert first["wins"] + first["losses"] + first["no_resolution"] == 256
    assert first["calibrated_probability"] is False
    assert prewar_declaration_admission(first)["admitted"] is True


def test_marginal_power_and_invalid_input_do_not_authorize_declaration():
    marginal = forecast_prewar_power_battle(
        {"actor_power_base_raw": 1_600_000, "target_power_total_raw": 1_000_000},
        declaration_id="candidate-2",
    )
    assert prewar_declaration_admission(marginal)["admitted"] is False
    assert forecast_prewar_power_battle(
        {"actor_power_base_raw": 0, "target_power_total_raw": 1},
        declaration_id="candidate-2",
    )["status"] == "native_power_input_unavailable"
