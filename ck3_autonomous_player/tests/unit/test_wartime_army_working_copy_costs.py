"""Keep conditional loss results independent without copying manager graphs."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from test_army_strength_contract import _available_row
from test_current_callback_supply_risk_service_12004 import current_packet
from xar_autoplayer.bridge import army_current_callback_soldier_effects_projection as effects
from xar_autoplayer.bridge import army_loss_sequence_replay as replay
from xar_autoplayer.bridge import war_contract
from xar_autoplayer.bridge import service as service_module
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.army_current_callback_supply_risk_projection import (
    project_current_callback_supply_risk_v1,
)


class _UnrelatedManagerGraph:
    def __deepcopy__(self, memo):
        raise AssertionError("conditional regiment writes traversed unrelated manager inputs")


@pytest.mark.parametrize("budget,expected", [(0, 101), (2, 99)])
def test_callback_owns_only_budget_and_regiment_working_state(budget, expected):
    army = current_packet()
    before = deepcopy(army)
    risk = project_current_callback_supply_risk_v1(army)
    risk["conditional_supply_budget_soldiers"] = budget
    baseline = effects.project_current_callback_soldier_effects_v1(army, risk)
    army["current_army_flag31_inputs_v1"] = _UnrelatedManagerGraph()
    observed = effects.project_current_callback_soldier_effects_v1(army, risk)
    assert observed == baseline
    assert observed["conditional_loss_sequence_v1"]["conditional_final_current_soldiers"] == expected
    assert {key: value for key, value in army.items()
            if key != "current_army_flag31_inputs_v1"} == before
    observed["conditional_loss_sequence_v1"]["conditional_final_regiment_strengths"][0][
        "current_soldiers"] = -1
    assert army["regiment_strengths"][0]["current_soldiers"] == 101


def test_partial_loss_keeps_missing_data_result_without_copying_other_families():
    army = current_packet()
    army.pop("regiment_replenishment_records_v1")
    army["loss_application_inputs_v1"]["current_supply_loss_budget"] = 2
    baseline = replay.project_conditional_army_loss_sequence(army)
    army["current_pre_date_pending_update_inputs_v1"] = _UnrelatedManagerGraph()
    observed = replay.project_conditional_army_loss_sequence(army)
    assert observed == baseline
    assert observed["status"] == "partial"
    assert observed["conditional_sequence_ready"] is False


_MANAGER_NORMALIZERS = {
    "current_daily_assault_roster_admission_v1": "normalize_current_daily_assault_roster_admission_v1",
    "current_pre_date_pending_update_inputs_v1": "normalize_current_pre_date_pending_update_inputs_v1",
    "current_post_admission_refresh_inputs_v1": "normalize_current_post_admission_refresh_inputs_v1",
    "current_selected_title_holder_owner_relation_v1": "normalize_current_selected_title_holder_owner_relation_v1",
    "current_army_combat_roles_phase_inputs_v1": "normalize_current_army_combat_roles_phase_inputs_v1",
    "current_army_flag31_inputs_v1": "normalize_current_army_flag31_inputs_v1",
    "current_army_condition30_inputs_v1": "normalize_current_army_condition30_inputs_v1",
    "current_army_flag20_inputs_v1": "normalize_current_army_flag20_inputs_v1",
    "current_army_flag21_inputs_v1": "normalize_current_army_flag21_inputs_v1",
    "current_pre_date_character_prefix_inputs_v1": "normalize_current_pre_date_character_prefix_inputs_v1",
}


def test_all_ten_shared_manager_families_validate_and_serialize_once(monkeypatch):
    def validate(value):
        if type(value["occurrences"][0]["index"]) is not int:
            raise ValueError("strict manager index")
        return deepcopy(value)

    spies = {}
    for field, name in _MANAGER_NORMALIZERS.items():
        spies[field] = Mock(side_effect=validate)
        monkeypatch.setattr(war_contract, name, spies[field])
    fields = {field: {"occurrences": [{"index": 0}]}
              for field in _MANAGER_NORMALIZERS}
    raw = [{**_available_row(army_id, "player", []), **fields}
           for army_id in (11, 12, 13)]
    dumps = Mock(wraps=war_contract.pickle.dumps)
    monkeypatch.setattr(war_contract.pickle, "dumps", dumps)
    rows = war_contract.normalize_army_strengths(raw)
    assert [spy.call_count for spy in spies.values()] == [1] * 10
    assert dumps.call_count == 10
    for field in fields:
        assert rows[0][field] == rows[1][field] == rows[2][field] == fields[field]
        rows[1][field]["occurrences"][0]["index"] = 8
        assert rows[0][field]["occurrences"][0]["index"] == 0
        assert rows[2][field]["occurrences"][0]["index"] == 0
        assert fields[field]["occurrences"][0]["index"] == 0
    for spy in spies.values():
        spy.reset_mock()
    dumps.reset_mock()
    war_contract.normalize_army_strengths([deepcopy(row) for row in raw])
    assert [spy.call_count for spy in spies.values()] == [3] * 10
    assert dumps.call_count == 0
    invalid = deepcopy(raw)
    invalid[1]["current_army_flag20_inputs_v1"]["occurrences"][0]["index"] = True
    with pytest.raises(ValueError, match="strict manager index"):
        war_contract.normalize_army_strengths(invalid)


def test_unpicklable_normalized_manager_retains_independent_copy_fallback():
    raw = {"items": [1]}
    def normalize(value):
        return {"items": list(value["items"]), "function": lambda: None}
    cache = {}
    first = war_contract._normalize_manager_input_once(raw, normalize, cache)
    second = war_contract._normalize_manager_input_once(raw, normalize, cache)
    second["items"].append(2)
    assert first["items"] == raw["items"] == [1]


@pytest.mark.parametrize("native", [True, False])
def test_service_reuses_exact_native_rows_and_keeps_other_backend_validation(monkeypatch, native):
    rows = war_contract.normalize_army_strengths([_available_row(11, "player", [])])
    result = {"step": "query-army-strengths-v1", "accepted": True,
              "status": "available", "army_strengths": rows}
    driver = object.__new__(NativeHeadlessGameplayDriver) if native else SimpleNamespace()
    driver.execute_step = lambda *args, **kwargs: result
    service = object.__new__(GameplayBridgeService)
    service.driver = driver
    service.snapshot = lambda **kwargs: {}
    projected = []
    service._native71_army_projection_rows = lambda result, values, **kwargs: projected.append(values) or {}
    service._current_callback_supply_projection_rows = lambda values: {}
    service._unit_new_date_entry_normalization_rows = lambda result, values: []
    service._unit_next_movement_projection_rows = lambda result, values, **kwargs: {}
    normalizer = Mock(wraps=war_contract.normalize_army_strengths)
    monkeypatch.setattr(service_module, "normalize_army_strengths", normalizer)
    assert service.execute_step("query-army-strengths-v1") == {
        **result, "current_unit_new_date_entry_normalization_v1": []}
    assert normalizer.call_count == (0 if native else 1)
    assert projected[0] == rows
    if native:
        assert projected[0] is rows
    else:
        result["army_strengths"] = [{**rows[0], "ai_base_power_scale": True}]
        with pytest.raises(ValueError):
            service.execute_step("query-army-strengths-v1")
