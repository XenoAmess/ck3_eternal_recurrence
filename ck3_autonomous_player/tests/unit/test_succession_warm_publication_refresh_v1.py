"""Focused SDK public-domain regression over production Driver/Service seams.

All Native material is synthetic retained test data. The 61 -> 2 public and
60 -> 61 Native values reproduce C5's observed domains; no current estate,
process, transport, RPC, runtime file or business action is used here.
"""
import copy
from pathlib import Path
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_r76_initial_succession_root_reuse import _InitialExpectationDriver
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_expectation_invalidation_v1 import (
    invalidate_succession_state_from_root_v1,
)
from xar_autoplayer.bridge.succession_warm_publication_refresh_v1 import (
    same_pid_hot_publication_refresh_v1,
)


class _WarmDriver(_InitialExpectationDriver):
    retain_succession_expectation_v1 = NativeHeadlessGameplayDriver.retain_succession_expectation_v1
    invalidate_succession_expectation_from_root_v1 = (
        NativeHeadlessGameplayDriver.invalidate_succession_expectation_from_root_v1
    )

    def __init__(self, state_dir):
        super().__init__(state_dir)
        self._driver_state_lock = threading.RLock()
        self._episode_character_id = self.frame["episode_character_id"]
        self._episode_run_id = self.frame["episode_run_id"]
        self._succession_expectation = self._succession_reconciliation = None
        self._driver_state_restore_kind = "same_pid_hot"
        self._driver_state_dirty = False
        self.persist_calls = 0
        self.state.semantic_snapshot = lambda: copy.deepcopy(self.frame)
        self.frame.update(snapshot_id="native:60", revision=61, native_revision=60)

    def take_internal_semantic_snapshot(self):
        assert not self._driver_state_lock._is_owned()
        return {**copy.deepcopy(self.frame),
                "succession_expectation": copy.deepcopy(self._succession_expectation),
                "succession_reconciliation": copy.deepcopy(self._succession_reconciliation)}

    def _persist_driver_state(self, *, persistence_reason="unspecified"):
        self.persist_calls += 1


def _warm_material(tmp_path, monkeypatch):
    monkeypatch.setattr("xar_autoplayer.bridge.service.choose_one_life_turn", lambda *_a, **_k: {
        "policy": "one-life-turn-v1", "phase": "synthetic", "selected_step": "life-advance"})
    driver = _WarmDriver(tmp_path)
    service = GameplayBridgeService(driver)
    service.plan_turn()
    previous = {"expectation": copy.deepcopy(driver._succession_expectation),
                "reconciliation": {"opaque_previous_projection": True}}
    driver._succession_reconciliation = copy.deepcopy(previous["reconciliation"])
    driver.frame.update(snapshot_id="native:61", revision=2, native_revision=61)
    snapshot = driver.take_internal_semantic_snapshot()
    return driver, service, previous, snapshot


def test_actual_driver_service_warm_publication_refresh_uses_real_root_and_strict_retain(tmp_path, monkeypatch):
    driver, service, previous, snapshot = _warm_material(tmp_path, monkeypatch)
    roots, writes = driver.root_calls, driver.persist_calls
    root = service.query_campaign_root_context_v1(expected_revision=2)
    assert driver.root_calls == roots + 1
    assert driver._succession_expectation is driver._succession_reconciliation is None
    assert driver.persist_calls == writes + 1 and driver._driver_state_dirty
    # A separate epoch never becomes permission for the old compare guard.
    with pytest.raises(ValueError, match="actor/episode sequence"):
        invalidate_succession_state_from_root_v1(previous, snapshot=snapshot, campaign_root_result=root)
    assert previous["expectation"]["binding"]["revision"] == 61
    assert previous["expectation"]["binding"]["native_revision"] == 60
    root_history = copy.deepcopy(driver._command_history)
    planned = service.plan_turn()
    assert planned["plan"]["selected_step"] == "life-advance"
    assert driver.root_calls == roots + 1  # Original same-frame history reuse.
    assert driver._command_history == root_history and driver.persist_calls == writes + 2
    for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
        assert driver._succession_expectation["binding"][key] == driver.frame[key]
    assert driver._succession_expectation["binding"]["episode_run_id"] == driver._episode_run_id
    # Restore-kind may remain hot, but this current publication is not reset twice.
    service.query_campaign_root_context_v1(expected_revision=2)
    assert driver._succession_expectation is not None and driver.persist_calls == writes + 2
    assert driver.requests == [] and driver.submit_calls == 0


def test_warm_refresh_keeps_identity_native_date_terminal_and_full_root_guards(tmp_path, monkeypatch):
    driver, service, previous, snapshot = _warm_material(tmp_path, monkeypatch)
    root = service.query_campaign_root_context_v1(expected_revision=2)
    original = copy.deepcopy(previous)
    for restore_kind in (None, "cold_checkpoint", "natural_succession"):
        assert same_pid_hot_publication_refresh_v1(previous, snapshot=snapshot,
            campaign_root_result=root, restore_kind=restore_kind) is None
    for revision in (61, 62):
        assert same_pid_hot_publication_refresh_v1(previous, snapshot={**snapshot, "revision": revision},
            campaign_root_result=root, restore_kind="same_pid_hot") is None
    for kind in ("actor", "episode", "native_backwards", "date_backwards", "terminal", "partial", "mixed_root"):
        current, material = copy.deepcopy(snapshot), copy.deepcopy(root)
        if kind == "actor":
            current["played_character"]["character_id"] += 1
            current["episode_character_id"] = current["played_character"]["character_id"]
        elif kind == "episode":
            current["episode_run_id"] += "-other"
        elif kind == "native_backwards":
            current["native_revision"] = 59
        elif kind == "date_backwards":
            current["date_raw"] -= 24
        elif kind == "terminal":
            current.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
        elif kind == "partial":
            material["campaign_root_context"]["readiness"]["held_title_partition_ready"] = False
        else:
            material["binding"]["native_revision"] += 1
        with pytest.raises(ValueError):
            same_pid_hot_publication_refresh_v1(previous, snapshot=current,
                campaign_root_result=material, restore_kind="same_pid_hot")
    assert previous == original
    # The actual Driver preserves the predecessor pair on an unknown terminal.
    driver._succession_expectation = copy.deepcopy(previous["expectation"])
    driver._succession_reconciliation = copy.deepcopy(previous["reconciliation"])
    driver.frame.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
    writes = driver.persist_calls
    result = driver.invalidate_succession_expectation_from_root_v1(
        root, expected_snapshot=driver.take_internal_semantic_snapshot())
    assert result["status"] == "not_applicable" and driver.persist_calls == writes
    assert driver._succession_expectation == previous["expectation"]
    assert driver._succession_reconciliation == previous["reconciliation"]
