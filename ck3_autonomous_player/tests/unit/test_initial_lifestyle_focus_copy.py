"""Opening LIFE keeps its real inputs without copying unrelated domain views.

Fixtures are synthetic; actual Service and protected Driver methods run offline.
"""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge import service as service_module
from test_service_window_priority_copy import CopyProbe, PlanningDriver, service_for
from test_m4_lifestyle_service_opening_gate_consumer_12004 import _OpeningDriver


@pytest.mark.parametrize("pending", [None, {
    "kind": "focus", "action_request_id": "synthetic-original-focus-request",
    "target_key": "martial_strategy_focus",
}])
def test_opening_preserves_LIFE_scope_original_pending_and_war_frame_without_other_views(monkeypatch, pending):
    driver = PlanningDriver()
    driver.require_initial_lifestyle_focus_before_date_advance = True
    service = service_for(driver)
    scope = {"status": "admitted", "actor_character_id": 31254,
             "snapshot_id": driver.frame["snapshot_id"], "date_raw": driver.frame["date_raw"]}
    monkeypatch.setattr(service_module, "plan_one_life_window_priority_v1", lambda *args, **kwargs: None)
    monkeypatch.setattr(service_module, "same_frame_feudal_lifestyle_scope", lambda *args, **kwargs: scope)
    monkeypatch.setattr(service_module, "unresolved_lifestyle_perk_action", lambda *args, **kwargs: pending)
    observed = []

    def consume(planned, available_steps):
        observed.append(planned)
        assert planned["_private_lifestyle_scope_v1"] == scope
        assert planned["_private_lifestyle_pending_v1"] == pending
        assert "_private_lifestyle_war_frame_v1" in planned
        assert planned["_private_lifestyle_war_frame_v1"] is None
        required = {"_private_lifestyle_scope_v1", "_private_lifestyle_pending_v1",
                    "_private_lifestyle_war_frame_v1"}
        private_keys = {key for key in planned if key.startswith("_private_")}
        # Current W consumes the arbitration flag before reaching LIFE.
        assert required <= private_keys <= required | {"_private_window_priority_v1"}
        return planned

    monkeypatch.setattr(service, "_plan_initial_lifestyle_focus_first_v1", consume)
    original = deepcopy(driver._command_history)
    row, result = driver._command_history[0], driver._command_history[0]["result"]
    CopyProbe.counts = {}
    planned = service.plan_turn()
    assert len(observed) == 1
    assert planned["plan"]["policy"] == "initial-lifestyle-focus-first-v1"
    assert planned["planning_source_frame"]["date_raw"] == driver.frame["date_raw"]
    assert "_private_construction_history_v1" not in planned
    assert "_private_faction_history_v1" not in planned
    assert CopyProbe.counts == {}
    assert driver._command_history == original
    assert driver._command_history[0] is row and row["result"] is result
    assert driver.requests == []


@pytest.mark.parametrize("current_state_reader", [True, False])
def test_real_opening_LIFE_readback_uses_history_free_frame_checks_without_action(monkeypatch, current_state_reader):
    driver = _OpeningDriver(existing_focus=True)
    if not current_state_reader:
        driver.query_player_lifestyle_current_state_private_v1 = None
    service = service_module.GameplayBridgeService(driver)
    planned = {**driver.frame, "plan": {"selected_step": "life-advance"},
               "_private_lifestyle_scope_v1": {}, "_private_lifestyle_pending_v1": None,
               "_private_lifestyle_war_frame_v1": None}
    original_snapshot = service.snapshot
    calls = []

    def snapshot(**kwargs):
        calls.append(kwargs.get("include_native_command_history"))
        return original_snapshot(**kwargs)

    monkeypatch.setattr(service, "snapshot", snapshot)
    result = service._plan_initial_lifestyle_focus_first_v1(planned, set(driver.capabilities()["action_steps"]))
    assert calls[:3] == [False, False, False]
    assert result["plan"]["phase"] == "initial_lifestyle_focus_already_present"
    proof = result["plan"]["initial_lifestyle_focus_existing"]
    assert proof["status"] == "verified_existing"
    assert proof["source_frame"]["snapshot_id"] == driver.frame["snapshot_id"]
    assert proof["current_focus"]["presence"] == "present"
    assert proof["current_lifestyle_progress"]["xp_per_level"] > 0
    assert driver.executed == []
