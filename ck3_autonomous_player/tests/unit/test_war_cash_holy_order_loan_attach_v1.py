"""Synthetic DTO/consumer input checks; no native ABI or funds qualification."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from xar_autoplayer.bridge import war_cash_private_transport_v1 as cash
from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004
from xar_autoplayer.war_mercenary_consumer_v1 import _loan_financing_input


KEY = "holy_order_loan_observation_v1"
ROOT = Path(__file__).resolve().parents[2]
LEGACY = json.loads((ROOT / "native_bridge/research/fixtures/ck3_12002_war_cash_current-resources-normal.json").read_text(encoding="utf-8"))


def packet():
    value = deepcopy(LEGACY)
    value.update(game_version=CK3_12004.game_version, executable_sha256=CK3_12004.executable_sha256)
    actor, date = value["played_character_id"], value["date_raw"]
    costs = {"schema": "ck3_12004_holy_order_loan_decision_costs_v1",
        "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
        "read_only": True, "scope": "decision_gates_and_costs_only", "available": True,
        "unavailable_reason": None, "capture_epoch": 123, "date_raw": date,
        "played_character_id": actor, "raw_scale": 100000, "resource_slot_count": 10,
        "complete_loan_terms": False, "principal_quote_raw": None, "typed_debt": None,
        "funding_credit_raw": 0, "submit_planned": False,
        "borrow_decision": {"decision_id": "borrow_from_holy_order_decision", "is_shown": True,
            "can_take": False, "affordable": True, "costs_raw_by_native_index": list(range(-5, 5))},
        "repay_decision": {"decision_id": "repay_loan_decision", "is_shown": False,
            "can_take": True, "affordable": True, "costs_raw_by_native_index": [0] * 10}}
    stamp = {"pump_epoch": 123, "thread_id": 2, "rng_wrapper": 3, "rng_state": 4,
        "rng_owner_thread_id": 2, "tls_initialized_flag_address": 5, "tls_initialized": 1,
        "tls_context": 6, "tls_main_thread_marker": 1, "jomini_state": 7, "game_state": 8,
        "date_raw": date, "paused": True}
    value[KEY] = {"schema": "xar.ck3.holy-order-loan-war-cash.v1", "status": "available",
        "read_only": True, "advertised": False, "formal_action_ready": False,
        "source_frame": {"snapshot_revision": value["snapshot_revision"], "ticket_sequence": 12,
            "local_player_id": 0, "played_character_id": actor, "date_raw": date,
            "full_snapshot_owner_retained": True, "same_frame_ready": True, "execution_stamp": stamp},
        "decision_costs": costs, "decision_costs_unavailable_reason": None,
        "principal": {"status": "available", "value_key": "holy_order_gold_value", "raw_scale": 100000,
            "prospective_principal_raw": 0, "owned_temporaries_released": True, "unavailable_reason": None},
        "complete_loan_terms": False, "existing_debt_principal_raw": None,
        "received_funds_verified": False, "funding_credit_raw": 0, "submit_planned": False}
    value["readiness"]["same_frame_ready"] = True
    return value


def snapshot(value):
    return {"paused": True, "map_ready": True, "snapshot_id": "synthetic-snapshot",
        "revision": 9, "native_revision": value["snapshot_revision"], "date_raw": value["date_raw"],
        "episode_run_id": "synthetic-episode", "played_character": {"character_id": value["played_character_id"]},
        "diagnostics": {"bridge_pid": 321, "connection_generation": 7, "hello": {
            "expected_ck3_version": value["game_version"], "expected_ck3_sha256": value["executable_sha256"]}}}


def planning_frame(s):
    return {"schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
        "snapshot_id": s["snapshot_id"], "revision": s["revision"], "native_revision": s["native_revision"],
        "date_raw": s["date_raw"], "actor_character_id": s["played_character"]["character_id"],
        "episode_run_id": s["episode_run_id"], "bridge_pid": s["diagnostics"]["bridge_pid"],
        "connection_generation": s["diagnostics"]["connection_generation"]}


def normalize(value):
    return cash.normalize_war_cash_current_resources_v1(value, snapshot=snapshot(value))


def test_absent_leaf_retains_original_cash_packet():
    value = packet()
    value.pop(KEY)
    before = deepcopy(value)
    assert normalize(value) == before == value


@pytest.mark.parametrize("key", ["paused", "map_ready"])
def test_unpaused_or_unready_current_snapshot_keeps_cash_but_not_loan(key):
    value = packet()
    s = snapshot(value)
    s[key] = False
    result = cash.normalize_war_cash_current_resources_v1(value, snapshot=s)
    assert result["status"] == value["status"]
    assert result[KEY]["principal_quote_raw"] is None and result[KEY]["borrow_eligible"] is None


def test_quote_zero_native_false_gate_and_ten_cost_slots_remain_independent():
    value = packet()
    before = deepcopy(value)
    result = normalize(value)
    loan = result[KEY]
    assert result["status"] == value["status"]
    assert loan["principal_quote_raw"] == 0
    assert loan["decision_observation"]["borrow_decision"]["native_gates_allow_decision"] is False
    assert loan["decision_observation"]["borrow_decision"]["declared_costs_raw_by_native_index"] == list(range(-5, 5))
    assert loan["funding_credit_raw"] == 0 and loan["received_funds_verified"] is False
    assert loan["existing_debt_principal_raw"] is None and loan["complete_loan_terms"] is False
    assert value == before
    assert normalize(result) == result


@pytest.mark.parametrize("bad", [[0] * 9, [True] + [0] * 9, [2**63] + [0] * 9])
def test_bad_costs_keep_valid_zero_quote_and_unknown_eligibility(bad):
    value = packet()
    value[KEY]["decision_costs"]["borrow_decision"]["costs_raw_by_native_index"] = bad
    loan = normalize(value)[KEY]
    assert loan["status"] == "partial" and loan["principal_quote_raw"] == 0
    assert loan["decision_observation"] is None and loan["borrow_eligible"] is None


@pytest.mark.parametrize("changes", [
    {"prospective_principal_raw": True}, {"prospective_principal_raw": 2**63},
    {"owned_temporaries_released": False}, {"unavailable_reason": "cleanup_exception"}])
def test_bad_principal_keeps_native_costs_and_known_false_eligibility(changes):
    value = packet()
    value[KEY]["principal"].update(changes)
    loan = normalize(value)[KEY]
    assert loan["status"] == "partial" and loan["principal_quote_raw"] is None
    assert loan["borrow_eligible"] is False and loan["decision_observation"] is not None


@pytest.mark.parametrize("name,change", [("snapshot_revision", 999), ("played_character_id", 999),
    ("date_raw", 999), ("ticket_sequence", 0), ("same_frame_ready", False),
    ("full_snapshot_owner_retained", False)])
def test_bad_native_frame_only_discards_loan(name, change):
    value = packet()
    value[KEY]["source_frame"][name] = change
    result = normalize(value)
    assert result["current_treasury"] == value["current_treasury"] and result["status"] == value["status"]
    assert result[KEY]["status"] == "unavailable" and result[KEY]["borrow_eligible"] is None


@pytest.mark.parametrize("name,change", [("pump_epoch", 0), ("thread_id", True),
    ("date_raw", 999), ("paused", False), ("tls_context", -1)])
def test_bad_execution_stamp_cannot_be_available(name, change):
    value = packet()
    value[KEY]["source_frame"]["execution_stamp"][name] = change
    assert normalize(value)[KEY]["principal_quote_raw"] is None


@pytest.mark.parametrize("key,change", [("funding_credit_raw", 100), ("received_funds_verified", True),
    ("complete_loan_terms", True), ("existing_debt_principal_raw", 10), ("submit_planned", True)])
def test_asserted_funding_or_full_terms_isolated_from_cash(key, change):
    value = packet()
    value[KEY][key] = change
    result = normalize(value)
    assert result["status"] == value["status"] and result[KEY]["funding_credit_raw"] == 0
    assert result[KEY]["principal_quote_raw"] is None


def test_old_build_is_not_relabelled_as_new_loan():
    value = packet()
    value.update(game_version=CK3_12003.game_version, executable_sha256=CK3_12003.executable_sha256)
    assert normalize(value)[KEY]["status"] == "unavailable"


def test_consumer_optional_input_requires_actual_complete_same_frame_and_query_metadata():
    value = packet()
    s = snapshot(value)
    assert _loan_financing_input(s, None, None) is None
    value.update(queried_snapshot_id=s["snapshot_id"], queried_revision=s["revision"],
        queried_native_revision=s["native_revision"])
    ready = _loan_financing_input(s, normalize(value), planning_frame(s))
    assert ready["principal_quote_raw"] == 0 and ready["planning_source_frame"] == planning_frame(s)
    assert ready["funding_credit_raw"] == 0
    for key, changed in [("bridge_pid", 999), ("episode_run_id", "other"),
                         ("connection_generation", 8), ("revision", 10)]:
        bad = {**planning_frame(s), key: changed}
        result = _loan_financing_input(s, value, bad)
        assert result["principal_quote_raw"] is None and result["borrow_eligible"] is None
    s["diagnostics"]["bridge_pid"] = None
    assert _loan_financing_input(s, value, planning_frame(s))["principal_quote_raw"] is None
