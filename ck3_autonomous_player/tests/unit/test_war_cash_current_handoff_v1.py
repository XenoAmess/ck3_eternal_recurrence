"""Memory-only transport -> real Service call -> existing consumer validation.

The endpoint is synthetic. No Driver is instantiated, no files/tmp fixtures are
used, and these cases grant no Native ABI, real quote or funding qualification.
"""
from copy import deepcopy
from threading import RLock

import pytest

from xar_autoplayer.bridge import war_cash_private_transport_v1 as cash
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer import war_mercenary_consumer_v1 as consumer


def source():
    return {"snapshot_id": "synthetic-cash-source", "revision": 9, "native_revision": 12,
        "date_raw": 53300000, "episode_run_id": "synthetic-episode", "paused": True,
        "map_ready": True, "played_character": {"character_id": 41, "alive": True},
        "active_wars": [{"war_id": 7}], "diagnostics": {"bridge_pid": 321,
            "connection_generation": 2, "hello": {"expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256}}}


def native_cash():
    def expense():
        return {"status": "available", "owner_character_id": 41, "resource_id": "41",
            "war_ids": [7], "raw_scale": 100000, "time_basis": "month",
            "source_scope": "actor_owned_military_once_across_all_wars",
            "future_war_cost_upper_ready": False, "resource_raw_native": [2] + [0] * 9,
            "gold_raw": 2, "treasury_raw": 0}
    decisions = {"schema": "ck3_12004_holy_order_loan_decision_costs_v1",
        "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
        "read_only": True, "scope": "decision_gates_and_costs_only", "available": True,
        "unavailable_reason": None, "capture_epoch": 123, "date_raw": 53300000,
        "played_character_id": 41, "raw_scale": 100000, "resource_slot_count": 10,
        "complete_loan_terms": False, "principal_quote_raw": None, "typed_debt": None,
        "funding_credit_raw": 0, "submit_planned": False,
        "borrow_decision": {"decision_id": "borrow_from_holy_order_decision", "is_shown": True,
            "can_take": True, "affordable": True, "costs_raw_by_native_index": list(range(-5, 5))},
        "repay_decision": {"decision_id": "repay_loan_decision", "is_shown": False,
            "can_take": True, "affordable": True, "costs_raw_by_native_index": [0] * 10}}
    stamp = {"pump_epoch": 123, "thread_id": 2, "rng_wrapper": 3, "rng_state": 4,
        "rng_owner_thread_id": 2, "tls_initialized_flag_address": 5, "tls_initialized": 1,
        "tls_context": 6, "tls_main_thread_marker": 1, "jomini_state": 7, "game_state": 8,
        "date_raw": 53300000, "paused": True}
    return {"schema": "xar.ck3.war-cash-current-resources.v1", "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256, "status": "available", "read_only": True,
        "advertised": False, "formal_action_ready": False, "played_character_id": 41,
        "snapshot_revision": 12, "date_raw": 53300000, "active_war_ids": [7], "player_army_ids": [],
        "current_treasury": {"raw": 1000000, "scale": 100000},
        "player_monthly_net_income": {"raw": -100, "scale": 100000},
        "military_expenses": {"current": expense(), "all_raised": expense()},
        "readiness": {"same_frame_ready": True}, cash.HOLY_ORDER_LOAN_KEY: {
            "schema": cash.HOLY_ORDER_LOAN_SCHEMA, "status": "available", "read_only": True,
            "advertised": False, "formal_action_ready": False,
            "source_frame": {"snapshot_revision": 12, "ticket_sequence": 4, "local_player_id": 0,
                "played_character_id": 41, "date_raw": 53300000, "full_snapshot_owner_retained": True,
                "same_frame_ready": True, "execution_stamp": stamp},
            "decision_costs": decisions, "decision_costs_unavailable_reason": None,
            "principal": {"status": "available", "value_key": "holy_order_gold_value",
                "raw_scale": 100000, "prospective_principal_raw": 0,
                "owned_temporaries_released": True, "unavailable_reason": None},
            "complete_loan_terms": False, "existing_debt_principal_raw": None,
            "received_funds_verified": False, "funding_credit_raw": 0, "submit_planned": False}}


class Endpoint:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(deepcopy(request))


class State:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_command_result(self, request_id, timeout):
        if self.driver.query_error:
            raise BridgeUnavailableError("synthetic unknown query result")
        return {"type": "command_result", "protocol_version": 1, "request_id": request_id,
            "ok": True, "result": {"step": cash.CURRENT_STEP, "accepted": True,
                "private_build": True, "read_only": True, "advertised": False,
                "war_cash_current_resources": deepcopy(self.driver.packet)}}


class MemoryDriver:
    allow_private_war_cash_query = True

    def __init__(self):
        self._driver_state_lock = RLock()
        self.endpoint, self.state = Endpoint(), State(self)
        self.before, self.generic_after, self.closing = source(), source(), source()
        self.packet = native_cash()
        self.generic_reads = self.closing_reads = 0
        self.query_error = self.closing_error = False

    def take_snapshot_without_native_command_history(self):
        self.generic_reads += 1
        return deepcopy(self.before if self.generic_reads % 2 else self.generic_after)

    def take_internal_semantic_snapshot(self):
        self.closing_reads += 1
        if self.closing_error:
            raise RuntimeError("synthetic closing cache unavailable")
        return deepcopy(self.closing)


def query(driver):
    return cash.query_war_cash_current_resources_private_v1(driver, expected_revision=9)


def through_service(monkeypatch, driver, snapshot=None, step="life-advance"):
    calls = []

    def probe(actual_driver, plan, **kwargs):
        assert actual_driver is driver
        calls.append(kwargs)
        # Use the existing production consumer's full frame/DTO validation.
        loan = consumer._loan_financing_input(kwargs["snapshot"], kwargs.get("cash_resources"),
            kwargs.get("cash_source_frame"))
        return {**plan, "validated_loan": loan}

    monkeypatch.setattr(consumer, "plan_war_mercenary_turn_v1", probe)
    service = GameplayBridgeService.__new__(GameplayBridgeService)
    service.driver = driver
    result = service._plan_war_mercenary_with_current_cash_v1({"selected_step": step},
        snapshot=deepcopy(snapshot or source()), history=[], bridge_capabilities=set())
    assert len(calls) == 1
    return result, calls[0]


def test_actual_transport_return_service_kwargs_and_existing_consumer_zero_funding(monkeypatch):
    driver = MemoryDriver()
    returned = query(driver)
    before_counts = len(driver.endpoint.requests), driver.generic_reads, driver.closing_reads
    assert before_counts == (1, 2, 1)
    result, call = through_service(monkeypatch, driver)
    assert (len(driver.endpoint.requests), driver.generic_reads, driver.closing_reads) == before_counts
    assert call["cash_resources"] == returned
    assert call["cash_source_frame"] == GameplayBridgeService._observed_planning_source_frame(source())
    loan = result["validated_loan"]
    assert loan["principal_quote_raw"] == 0 and loan["borrow_eligible"] is True
    assert loan["decision_observation"]["borrow_decision"]["declared_costs_raw_by_native_index"] == list(range(-5, 5))
    assert loan["funding_credit_raw"] == 0 and loan["received_funds_verified"] is False
    assert result["selected_step"] == "life-advance"
    call["cash_resources"]["current_treasury"]["raw"] = 999
    assert cash.current_war_cash_observation_v1(driver, source())["cash_resources"]["current_treasury"]["raw"] == 1000000


def test_never_queried_slot_preserves_legacy_service_call_signature(monkeypatch):
    driver = MemoryDriver()
    calls = []

    def legacy(actual_driver, plan, *, snapshot, history, bridge_capabilities):
        calls.append((actual_driver, snapshot))
        return plan

    monkeypatch.setattr(consumer, "plan_war_mercenary_turn_v1", legacy)
    service = GameplayBridgeService.__new__(GameplayBridgeService)
    service.driver = driver
    plan = {"selected_step": "life-advance"}
    assert service._plan_war_mercenary_with_current_cash_v1(plan, snapshot=source(),
        history=[], bridge_capabilities=set()) == plan
    assert len(calls) == 1 and not hasattr(driver, cash._CURRENT_OBSERVATION)
    assert not driver.endpoint.requests and driver.generic_reads == driver.closing_reads == 0


def change(frame, key, value):
    if key in ("bridge_pid", "connection_generation"):
        frame["diagnostics"][key] = value
    else:
        frame[key] = value


@pytest.mark.parametrize("key,value", [("native_revision", 13), ("revision", 10),
    ("episode_run_id", "other"), ("bridge_pid", 999), ("connection_generation", 3),
    ("connection_generation", True)])
def test_query_Q_to_closing_P_change_does_not_relabel_packet(monkeypatch, key, value):
    driver = MemoryDriver()
    change(driver.closing, key, value)
    returned = query(driver)
    assert returned["snapshot_revision"] == returned["queried_native_revision"] == 12
    assert returned["status"] == "available"
    assert getattr(driver, cash._CURRENT_OBSERVATION) is None
    result, call = through_service(monkeypatch, driver)
    assert "cash_resources" not in call and result["validated_loan"] is None
    assert len(driver.endpoint.requests) == 1


@pytest.mark.parametrize("key,value", [("native_revision", 13), ("native_revision", 11),
    ("revision", 10), ("episode_run_id", "other"), ("bridge_pid", 999), ("connection_generation", 3)])
def test_closing_P_to_planning_S_change_clears_and_cannot_revive_old_Q(monkeypatch, key, value):
    driver = MemoryDriver()
    query(driver)
    current = source()
    change(current, key, value)
    result, call = through_service(monkeypatch, driver, current)
    assert result["validated_loan"] is None and "cash_source_frame" not in call
    assert getattr(driver, cash._CURRENT_OBSERVATION) is None
    # In particular a Native rollback followed by the old number is no revival.
    assert through_service(monkeypatch, driver)[0]["validated_loan"] is None
    assert len(driver.endpoint.requests) == 1 and driver.closing_reads == 1


@pytest.mark.parametrize("mode", ["no_reader", "closing_exception", "no_lock", "absent_loan"])
def test_absent_or_failed_local_observer_preserves_original_cash_wire(monkeypatch, mode):
    driver = MemoryDriver()
    if mode == "no_reader":
        driver.take_internal_semantic_snapshot = None
    elif mode == "closing_exception":
        driver.closing_error = True
    elif mode == "no_lock":
        del driver._driver_state_lock
    else:
        driver.packet.pop(cash.HOLY_ORDER_LOAN_KEY)
    returned = query(driver)
    expected = cash.normalize_war_cash_current_resources_v1(driver.packet, snapshot=source())
    expected.update(queried_snapshot_id=source()["snapshot_id"], queried_revision=9, queried_native_revision=12)
    assert returned == expected
    result, call = through_service(monkeypatch, driver)
    assert result["validated_loan"] is None and "cash_resources" not in call
    assert len(driver.endpoint.requests) == 1
    if mode != "closing_exception":
        assert driver.closing_reads == 0


@pytest.mark.parametrize("mode", ["command_unknown", "generic_post_changed", "malformed_cash"])
def test_failed_new_query_clears_previous_observation_without_retry(monkeypatch, mode):
    driver = MemoryDriver()
    query(driver)
    if mode == "command_unknown":
        driver.query_error = True
    elif mode == "generic_post_changed":
        driver.generic_after["native_revision"] = 13
    else:
        driver.packet["military_expenses"] = None
    with pytest.raises(BridgeUnavailableError):
        query(driver)
    assert len(driver.endpoint.requests) == 2
    assert getattr(driver, cash._CURRENT_OBSERVATION) is None
    assert through_service(monkeypatch, driver)[0]["validated_loan"] is None


@pytest.mark.parametrize("mode", ["peace", "concrete_order", "event", "interaction"])
def test_nonopportunity_service_does_not_query_or_read_closing(monkeypatch, mode):
    driver = MemoryDriver()
    query(driver)
    current, step = source(), "life-advance"
    if mode == "peace":
        current["active_wars"] = []
    elif mode == "concrete_order":
        step = "army-concrete-order"
    elif mode == "event":
        current["active_event"] = {"id": "synthetic-event"}
    else:
        current["pending_character_interaction"] = {"id": "synthetic-interaction"}
    result, call = through_service(monkeypatch, driver, current, step)
    assert result["selected_step"] == step and "cash_resources" not in call
    assert len(driver.endpoint.requests) == 1 and driver.generic_reads == 2 and driver.closing_reads == 1
