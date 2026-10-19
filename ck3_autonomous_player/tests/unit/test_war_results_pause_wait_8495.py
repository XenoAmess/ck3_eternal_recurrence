"""Real8495 first frames; synthetic successors. No Game, pipe or history IO."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xar_autoplayer import war_results_scope_pause_v1 as scope
from xar_autoplayer.bridge import native_driver as nd


def facts():
    return json.loads((Path(__file__).parent / "fixtures" /
        "war8495_pause_wait_source_v1.json").read_bytes())["result"]


def raw_frame(f):
    # Only reconstruct the public containers the helper's original _frame
    # removed. No additional business/identity field is invented.
    return {**{k: f[k] for k in ("snapshot_id", "revision", "native_revision", "date_raw", "paused", "map_ready", "episode_run_id")},
        "played_character": {"character_id": f["actor_character_id"]},
        "diagnostics": {"bridge_pid": f["bridge_pid"], "hello": {"pid": f["hello_pid"]},
                        "connection_generation": f["connection_generation"]}}


class Driver:
    # Execute the actual existing bounded internal wait; its native-change
    # source alone is a deterministic software sequence, never take_snapshot.
    _wait_for_life_advance_snapshot = nd.NativeHeadlessGameplayDriver._wait_for_life_advance_snapshot

    def __init__(self, later=None, *, paused_at_start=False):
        result = facts()["scope_transition_pause"]
        self.before = raw_frame(result["before_pause"])
        self.immediate = raw_frame(result["after_pause"])
        if paused_at_start:
            self.before["paused"] = self.immediate["paused"] = True
        self.reads = [self.before, self.immediate]
        self.later = list(later or [])
        self.actions, self.waits = [], []
        self.clock = 0.0

    def take_internal_semantic_snapshot(self):
        return deepcopy(self.reads.pop(0))

    def execute_step(self, step, *, expected_revision):
        assert step == "pause-map" and expected_revision is None
        self.actions.append(step)
        return {"step": step, "accepted": True, "status": "submitted"}

    def _wait_for_life_advance_change(self, revision, *, timeout_seconds, before_snapshot):
        self.waits.append((revision, timeout_seconds))
        if self.later:
            self.clock += min(0.1, timeout_seconds)
            return deepcopy(self.later.pop(0))
        self.clock += timeout_seconds
        return deepcopy(before_snapshot)

    def observe(self, original=None):
        with patch.object(scope, "monotonic", lambda: self.clock), \
             patch.object(nd.time, "monotonic", lambda: self.clock):
            return scope.pause_after_war_results_scope_transition_v1(self, original or facts())


def successor(**changes):
    current = raw_frame(facts()["scope_transition_pause"]["after_pause"])
    current.update(snapshot_id="native:1127", native_revision=1127, revision=1128, paused=True)
    current.update(changes)
    return current


def assert_uncredited(result):
    assert result["close_replayed"] is result["close_action_credit"] is False
    assert result["fresh_war_results_query_required"] is True


def test_actual8495_immediate_false_then_new_paused_frame_uses_one_pause_only():
    original = facts()
    preserved = deepcopy(original)
    assert original["scope_transition_pause"]["status"] == "pause_unverified"
    driver = Driver([successor()])
    result = driver.observe(original)
    assert driver.actions == ["pause-map"]
    assert driver.waits == [(1127, 1.5)]
    assert result["wait_attempted"] is True and result["observed_frame_count"] == 2
    assert result["immediate_after_pause"]["paused"] is False
    assert result["after_pause"]["paused"] is True
    assert result["status"] == "paused_same_owner_requery_required"
    assert result["observation_stop_reason"] == "paused"
    assert result["wait_elapsed_seconds"] == 0.1
    assert original == preserved  # The actual8495 failure is not rewritten.
    assert_uncredited(result)


def test_timeout_keeps_original_uncertainty_without_another_action():
    driver = Driver()
    result = driver.observe()
    assert driver.actions == ["pause-map"] and driver.waits == [(1127, 1.5)]
    assert result["status"] == "pause_unverified"
    assert result["after_pause"]["paused"] is False
    assert result["observation_stop_reason"] == "timeout"
    assert result["wait_elapsed_seconds"] == 1.5
    assert_uncredited(result)


@pytest.mark.parametrize("change", [
    lambda f: f["played_character"].update(character_id=99),
    lambda f: f.update(episode_run_id="foreign"),
    lambda f: f["diagnostics"].update(connection_generation=2),
    lambda f: f["diagnostics"].update(bridge_pid=99, hello={"pid": 99}),
    lambda f: f.update(revision=1126),
    lambda f: f.update(native_revision=1125),
    lambda f: f.update(date_raw=53217048),
    lambda f: f.update(map_ready=False),
    lambda f: f.update(active_event={"instance_id": 1}),
    lambda f: f.update(pending_character_interaction={"interaction": "unknown"}),
    lambda f: f.update(top_exclusive_modal_choice_hint={"status": "present"}),
    lambda f: f.update(one_life_terminal=True),
    lambda f: f.update(episode_identity_pending=True),
])
def test_foreign_regressed_or_new_decision_ends_wait_unverified(change):
    later = successor()
    change(later)
    driver = Driver([later])
    result = driver.observe()
    assert result["status"] == "pause_unverified"
    assert len(driver.waits) == 1 and driver.actions == ["pause-map"]
    assert result["wait_elapsed_seconds"] == 0.1
    assert result["observation_stop_reason"] not in (None, "paused", "timeout")
    assert_uncredited(result)


def test_already_paused_reads_without_pause_or_wait():
    driver = Driver(paused_at_start=True)
    result = driver.observe()
    assert result["status"] == "paused_same_owner_requery_required"
    assert driver.actions == driver.waits == []
    assert result["wait_attempted"] is False
    assert_uncredited(result)


def test_missing_waiter_or_exception_never_repeats_pause():
    missing = Driver()
    missing._wait_for_life_advance_snapshot = None
    result = missing.observe()
    assert result["status"] == "pause_unverified"
    assert result["observation_stop_reason"] == "internal_pause_observer_unavailable"
    assert missing.actions == ["pause-map"]
    assert_uncredited(result)
    failed = Driver()
    def unavailable(*args, **kwargs):
        raise RuntimeError("observer unavailable")
    failed._wait_for_life_advance_snapshot = unavailable
    result = failed.observe()
    assert result["status"] == "pause_unverified"
    assert "observer unavailable" in result["failure"]
    assert failed.actions == ["pause-map"]
    assert_uncredited(result)


def test_foreign_before_observation_never_submits_pause():
    driver = Driver()
    driver.reads[0]["episode_run_id"] = "foreign"
    result = driver.observe()
    assert result["status"] == "pause_unverified"
    assert driver.actions == driver.waits == []


def test_decision_before_pause_keeps_existing_single_safety_pause():
    driver = Driver()
    driver.reads[0]["active_event"] = {"instance_id": 1}
    driver.reads[1]["active_event"] = {"instance_id": 1}
    driver.reads[1]["paused"] = True
    result = driver.observe()
    assert result["status"] == "paused_same_owner_requery_required"
    assert driver.actions == ["pause-map"] and driver.waits == []
    assert_uncredited(result)
