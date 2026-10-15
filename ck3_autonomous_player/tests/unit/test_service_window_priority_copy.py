"""Window arbitration must not clone unused domain views or mutate history.

All frames, histories and decisions below are synthetic. The actual Service and
NativeDriver protected planning-view implementations run without a Native pipe.
"""
from copy import deepcopy
from threading import RLock

import pytest

import xar_autoplayer.bridge.service as service_module
import xar_autoplayer.holy_order_siege_reinforcement_v1 as reinforcement
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class CopyProbe(dict):
    counts = {}

    def __deepcopy__(self, memo):
        label = self["label"]
        self.counts[label] = self.counts.get(label, 0) + 1
        result = {key: deepcopy(value, memo) for key, value in self.items()}
        memo[id(self)] = result
        return result


class PlanningDriver:
    backend_id = "native-headless"
    state_dir = None
    allow_private_lifestyle_formal_trial = True
    allow_private_faction_gift_formal_trial = True
    allow_private_construction_formal_trial = True
    allow_private_family_marriage_formal_trial = True
    allow_private_council_action = True
    allow_private_m5_joint_collector = True
    allow_private_activity_feast_lifecycle_observation = False
    require_initial_lifestyle_focus_before_date_advance = False

    def __init__(self):
        self._history_lock = RLock()
        self._rollback_war_failures = []
        self._command_history = [{"command": "query-war-results-window-v1", "ok": True,
            "result": {"step": "query-war-results-window-v1",
                       "payload": CopyProbe(label="history")}}]
        self.frame = {
            "snapshot_id": "synthetic:3", "revision": 2, "native_revision": 3,
            "date_raw": 53233368, "episode_run_id": "synthetic-robert",
            "played_character": {"character_id": 31254, "alive": True},
            "paused": True, "map_ready": True, "active_wars": [],
            "active_event": None, "pending_character_interaction": None,
            "diagnostics": {"connection_generation": 2, "bridge_pid": 101},
            "unused_domain_payload": CopyProbe(label="snapshot"),
        }
        self.requests = []

    def take_internal_semantic_snapshot(self):
        return self.frame

    def take_snapshot(self, **kwargs):
        return {**self.frame, "native_command_history": self._command_history}

    def capabilities(self):
        steps = ["query-war-results-window-v1", "close-war-results-window-v1", "life-advance"]
        return {"backend_id": self.backend_id, "action_steps": steps,
                "bridge_capabilities": ["game.command." + step for step in steps]}

    def _with_internal_planning_view(self, snapshot, planner):
        return NativeHeadlessGameplayDriver._with_internal_planning_view(self, snapshot, planner)


def service_for(driver):
    service = service_module.GameplayBridgeService(driver)
    # Isolate the already observed arbitration/copy boundary. These tests do
    # not execute succession reads, private actions, or UI commands.
    service._prepare_succession_transition_v1 = lambda snapshot, *args, **kwargs: snapshot
    service._strategy_state_dir = lambda: None
    return service


@pytest.mark.parametrize("internal_view", [True, False])
@pytest.mark.parametrize("step", ["query-war-results-window-v1", "close-war-results-window-v1", None])
def test_window_priority_detaches_only_consumed_public_data(monkeypatch, internal_view, step):
    driver = PlanningDriver()
    if not internal_view:
        driver._with_internal_planning_view = None
    service = service_for(driver)
    chosen = {"policy": "ordinary-war-results-window-v1", "phase": "war_results_window",
              "status": "ready" if step else "pending", "selected_step": step,
              "reason": "synthetic independently observed window decision",
              "war_results_window": {"close_pending": step is None}}
    monkeypatch.setattr(service_module, "plan_one_life_window_priority_v1", lambda *args, **kwargs: chosen)
    row, result = driver._command_history[0], driver._command_history[0]["result"]
    CopyProbe.counts = {}
    planned = service.plan_turn()
    assert planned["plan"]["selected_step"] == step
    assert planned["plan"]["war_results_window"] == chosen["war_results_window"]
    assert planned["planning_source_frame"] == {
        "schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
        "snapshot_id": "synthetic:3", "revision": 2, "native_revision": 3,
        "date_raw": 53233368, "actor_character_id": 31254,
        "episode_run_id": "synthetic-robert", "connection_generation": 2, "bridge_pid": 101,
    }
    assert "_auto_camera_hotspot_input" in planned
    assert not any(key.startswith("_private_") for key in planned)
    assert CopyProbe.counts == {}
    assert driver._command_history[0] is row and row["result"] is result
    assert result["payload"] == {"label": "history"}
    assert driver.requests == []


def test_nonwindow_consumers_keep_the_original_protected_history_views(monkeypatch):
    driver = PlanningDriver()
    service = service_for(driver)
    monkeypatch.setattr(service_module, "plan_one_life_window_priority_v1", lambda *args, **kwargs: None)
    monkeypatch.setattr(service_module, "choose_one_life_turn", lambda *args, **kwargs: {
        "policy": "synthetic-normal-planner", "selected_step": "life-advance"})
    observed = []

    class ReachedNormalConsumers(Exception):
        pass

    def inspect(_driver, *, planned, **kwargs):
        for domain in ("faction", "construction", "council", "m5"):
            history = planned["_private_" + domain + "_history_v1"]
            assert history[0]["result"]["payload"] is driver._command_history[0]["result"]["payload"]
            observed.append(domain)
        raise ReachedNormalConsumers

    monkeypatch.setattr(reinforcement, "plan_holy_order_siege_reinforcement_v1", inspect)
    with pytest.raises(ReachedNormalConsumers):
        service._plan_turn_internal()
    assert observed == ["faction", "construction", "council", "m5"]
    assert driver.requests == []
