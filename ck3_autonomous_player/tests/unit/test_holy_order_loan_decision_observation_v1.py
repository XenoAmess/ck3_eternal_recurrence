from copy import deepcopy

import pytest

from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004
from xar_autoplayer.holy_order_loan_decision_observation_v1 import (
    NATIVE_SCHEMA, project_holy_order_loan_decision_observation_v1 as project,
)


def native():
    return {
        "schema": NATIVE_SCHEMA, "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "read_only": True, "scope": "decision_gates_and_costs_only", "available": True,
        "unavailable_reason": None, "played_character_id": 41, "date_raw": 53300000,
        "capture_epoch": 123, "raw_scale": 100000, "resource_slot_count": 10,
        "complete_loan_terms": False, "principal_quote_raw": None, "typed_debt": None,
        "funding_credit_raw": 0, "submit_planned": False,
        "borrow_decision": {"decision_id": "borrow_from_holy_order_decision",
            "is_shown": False, "can_take": False, "affordable": True,
            "costs_raw_by_native_index": [0, 0, 5000000, 0, 0, 0, 0, 0, 0, 0]},
        "repay_decision": {"decision_id": "repay_loan_decision",
            "is_shown": False, "can_take": True, "affordable": True,
            "costs_raw_by_native_index": [0] * 10},
    }


def observe(value):
    return project(value, expected_played_character_id=41,
                   expected_date_raw=53300000, expected_capture_epoch=123)


def test_hidden_repay_with_true_can_take_is_not_a_free_or_legal_repayment():
    value = native()
    result = observe(value)
    assert result["repay_decision"]["can_take"] is True
    assert result["repay_decision"]["native_gates_allow_decision"] is False
    assert result["repay_decision"]["declared_costs_raw_by_native_index"] == [0] * 10
    assert result["existing_debt_principal_raw"] is None
    assert result["repayment_total_outlay_raw"] is None
    assert result["submission_qualified"] is False


def test_all_native_gates_pass_still_has_unknown_principal_debt_and_zero_funds():
    value = native()
    value["borrow_decision"].update(is_shown=True, can_take=True)
    value["borrow_decision"]["costs_raw_by_native_index"] = [10, 20, 30, 40, 50, -60, 70, 80, 90, 100]
    before = deepcopy(value)
    result = observe(value)
    assert value == before
    assert result["borrow_decision"]["native_gates_allow_decision"] is True
    costs = result["borrow_decision"]["declared_costs_raw_by_native_index"]
    assert costs == value["borrow_decision"]["costs_raw_by_native_index"]
    costs[9] = 999
    assert value == before
    assert result["principal_quote_raw"] is None and result["complete_loan_terms"] is False
    assert result["received_funds_verified"] is False and result["funding_credit_raw"] == 0
    assert result["selected_action"] is None and result["submission_qualified"] is False


def test_unavailable_preserves_unknown_gates_and_costs():
    value = native()
    value.update(available=False, unavailable_reason="loan_decision_capture_exception")
    for name in ("borrow_decision", "repay_decision"):
        value[name].update(is_shown=None, can_take=None, affordable=None, costs_raw_by_native_index=None)
    result = observe(value)
    assert result["available"] is False
    assert result["borrow_decision"]["native_gates_allow_decision"] is None
    assert result["borrow_decision"]["declared_costs_raw_by_native_index"] is None


@pytest.mark.parametrize("costs", [[0] * 4, [0] * 9, [0] * 11, [False] + [0] * 9,
                                  [2**63] + [0] * 9, None])
def test_partial_boolean_or_out_of_range_native_costs_are_rejected(costs):
    value = native()
    value["borrow_decision"]["costs_raw_by_native_index"] = costs
    with pytest.raises(ValueError):
        observe(value)


@pytest.mark.parametrize("key,changed", [("played_character_id", 42), ("date_raw", 53300024),
                                       ("capture_epoch", 124), ("capture_epoch", True)])
def test_wrong_actor_date_or_capture_cannot_be_current_terms(key, changed):
    value = native()
    value[key] = changed
    with pytest.raises(ValueError):
        observe(value)


def test_previous_build_is_not_relabelled_as_current_provider():
    value = native()
    value.update(game_version=CK3_12003.game_version, executable_sha256=CK3_12003.executable_sha256)
    with pytest.raises(ValueError):
        observe(value)


@pytest.mark.parametrize("key,changed", [("principal_quote_raw", 30000000),
    ("typed_debt", {"owed": 30000000}), ("complete_loan_terms", True),
    ("funding_credit_raw", 30000000), ("funding_credit_raw", False), ("submit_planned", True)])
def test_gates_and_costs_never_launder_unobserved_principal_or_funding(key, changed):
    value = native()
    value[key] = changed
    with pytest.raises(ValueError):
        observe(value)
