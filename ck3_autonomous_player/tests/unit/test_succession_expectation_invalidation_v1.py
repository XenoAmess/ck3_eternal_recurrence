"""One same-publication estate-change regression using production root material."""
import copy
from pathlib import Path
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_r76_initial_succession_root_reuse import _InitialExpectationDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.succession_expectation_invalidation_v1 import invalidate_succession_state_from_root_v1 as invalidate


def test_new_complete_root_invalidates_same_revision_estate_without_new_query(tmp_path, monkeypatch):
    monkeypatch.setattr("xar_autoplayer.bridge.service.choose_one_life_turn", lambda *_a, **_k: {
        "policy": "one-life-turn-v1", "phase": "synthetic", "selected_step": "life-advance"})
    driver = _InitialExpectationDriver(tmp_path)
    driver.frame.pop("succession_expectation", None)
    service = GameplayBridgeService(driver)
    service.plan_turn()
    snapshot = copy.deepcopy(driver.frame)
    root = service.query_campaign_root_context_v1(expected_revision=snapshot["revision"])
    retained = {"expectation": copy.deepcopy(snapshot["succession_expectation"]),
                "reconciliation": {"opaque_previous_projection": True}}
    original, calls = copy.deepcopy(retained), driver.root_calls
    assert invalidate(retained, snapshot=snapshot, campaign_root_result=root)["status"] == "unchanged"
    rows = root["campaign_root_context"]["held_title_partition"]
    assert len(rows) >= 2
    for kind in ("other_heir", "removed_title", "primary_id", "primary_heir"):
        changed = copy.deepcopy(root)
        changed["query_sequence"] += 1
        actual = changed["campaign_root_context"]["held_title_partition"]
        if kind == "other_heir":
            next(row for row in actual if not row["primary"])["first_heir_character_id"] = 99991
        elif kind == "removed_title":
            actual.remove(next(row for row in actual if not row["primary"]))
        elif kind == "primary_id":
            primary = next(row for row in actual if row["primary"])
            primary["title"]["title_id"] = 99990
            changed["campaign_root_context"]["primary_title"]["title_id"] = 99990
            actual.sort(key=lambda row: row["title"]["title_id"])
        else:
            next(row for row in actual if row["primary"])["first_heir_character_id"] = 99992
            changed["campaign_root_context"]["primary_title_succession_character_ids"][0] = 99992
        for key in ("held_title_partition", "primary_title", "primary_title_succession_character_ids"):
            changed[key] = copy.deepcopy(changed["campaign_root_context"][key])
        output = invalidate(retained, snapshot=snapshot, campaign_root_result=changed)
        assert output["invalidated"] and output["refresh_required"]
        assert output["state"] == {"expectation": None, "reconciliation": None}
        assert output["source_binding"] == retained["expectation"]["binding"]
        assert output["source_query_sequence"] == root["query_sequence"] + 1
        assert not output["submission_authorized"] and output["queries_performed"] == 0
    mixed = copy.deepcopy(root)
    mixed["binding"]["native_revision"] += 1
    with pytest.raises(ValueError, match="one frame"):
        invalidate(retained, snapshot=snapshot, campaign_root_result=mixed)
    with pytest.raises(ValueError, match="living paused"):
        invalidate(retained, snapshot={**snapshot, "one_life_terminal": True}, campaign_root_result=root)
    assert retained == original and driver.root_calls == calls


def test_actual_driver_service_fresh_only_hook_retain_and_frame_race(tmp_path, monkeypatch):
    class Driver(_InitialExpectationDriver):
        retain_succession_expectation_v1 = NativeHeadlessGameplayDriver.retain_succession_expectation_v1

        def __init__(self, root):
            super().__init__(root)
            self._driver_state_lock = threading.RLock()
            self._episode_character_id = self.frame["episode_character_id"]
            self._episode_run_id = self.frame["episode_run_id"]
            self._succession_expectation = self._succession_reconciliation = None
            self._driver_state_dirty = False
            self.persist_calls = self.invalidate_calls = 0
            self.race_before_invalidate = False
            self.state.semantic_snapshot = lambda: copy.deepcopy(self.frame)

        def take_internal_semantic_snapshot(self):
            assert not self._driver_state_lock._is_owned(), "full observer must not invert persistence lock order"
            return {**copy.deepcopy(self.frame),
                    "succession_expectation": copy.deepcopy(self._succession_expectation),
                    "succession_reconciliation": copy.deepcopy(self._succession_reconciliation)}

        def _persist_driver_state(self, *, persistence_reason="unspecified"):
            self.persist_calls += 1

        def invalidate_succession_expectation_from_root_v1(self, result, *, expected_snapshot):
            self.invalidate_calls += 1
            if self.race_before_invalidate:
                self.frame.update(native_revision=self.frame["native_revision"] + 1,
                                  revision=self.frame["revision"] + 1)
                self.frame["snapshot_id"] = f"native:{self.frame['native_revision']}"
                self.race_before_invalidate = False
            return NativeHeadlessGameplayDriver.invalidate_succession_expectation_from_root_v1(
                self, result, expected_snapshot=expected_snapshot)

    monkeypatch.setattr("xar_autoplayer.bridge.service.choose_one_life_turn", lambda *_a, **_k: {
        "policy": "one-life-turn-v1", "phase": "synthetic", "selected_step": "life-advance"})
    driver = Driver(tmp_path)
    service = GameplayBridgeService(driver)
    service.plan_turn()
    original = copy.deepcopy(driver._succession_expectation)
    driver._succession_reconciliation = {"original_projection": True}
    writes, roots = driver.persist_calls, driver.root_calls
    result = service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"])
    assert driver._succession_expectation == original and driver.persist_calls == writes
    assert driver.root_calls == roots + 1
    hooks = driver.invalidate_calls
    cached = service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"],
        _planning_root_result=driver.last_root_result)
    assert cached == result and driver.invalidate_calls == hooks
    assert driver.root_calls == roots + 1 and driver.persist_calls == writes

    native_material = driver.data["current_root"]
    row = next(row for row in native_material["campaign_root_context"]["held_title_partition"] if not row["primary"])
    row["first_heir_character_id"] = 99991
    if "held_title_partition" in native_material:
        native_material["held_title_partition"] = copy.deepcopy(native_material["campaign_root_context"]["held_title_partition"])
    service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"])
    assert driver._succession_expectation is None and driver._succession_reconciliation is None
    assert driver._driver_state_dirty and driver.persist_calls == writes + 1
    roots = driver.root_calls
    service.plan_turn()
    assert driver.root_calls == roots  # Existing original root reuse, no extra RPC.
    assert any(row["first_heir_character_id"] == 99991 for row in driver._succession_expectation["title_expectations"])
    assert driver.persist_calls == writes + 2

    retained, writes = copy.deepcopy(driver._succession_expectation), driver.persist_calls
    row["first_heir_character_id"] = 99992
    if "held_title_partition" in native_material:
        native_material["held_title_partition"] = copy.deepcopy(native_material["campaign_root_context"]["held_title_partition"])
    driver.race_before_invalidate = True
    with pytest.raises(PreSubmissionRevisionMismatchError, match="completed campaign-root frame"):
        service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"])
    assert driver._succession_expectation == retained and driver.persist_calls == writes
    terminal = driver.take_internal_semantic_snapshot()
    terminal.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
    driver.frame.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
    observed = NativeHeadlessGameplayDriver.invalidate_succession_expectation_from_root_v1(
        driver, result, expected_snapshot=terminal)
    assert observed["status"] == "not_applicable" and driver.persist_calls == writes
    assert driver._succession_expectation == retained
