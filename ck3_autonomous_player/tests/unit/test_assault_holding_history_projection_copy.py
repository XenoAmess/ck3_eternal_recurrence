"""Exercise the real assault branch with small in-memory query/ACK seams."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
import unittest
from unittest.mock import Mock, patch

from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.driver import BridgeUnavailableError


def _snapshot():
    return {"revision": 3, "native_revision": 100, "snapshot_id": "native:100",
        "date_raw": 10000, "episode_run_id": "episode", "paused": True,
        "war_objective_assault_supported": True,
        "played_character": {"character_id": 7, "alive": True},
        "diagnostics": {"connection_generation": 1},
        "active_wars": [{"war_id": 8, "player_side": "attacker"}]}


def _query(active=False):
    return {"command": "query-war-occupation-targets-v1-8", "ok": True, "result": {
        "queried_snapshot_id": "native:100", "queried_revision": 3,
        "queried_native_revision": 100, "queried_connection_generation": 1,
        "queried_episode_run_id": "episode", "war_occupation_targets_v1": {
            "available": True, "collection_complete": True, "war_id": 8,
            "actor_character_id": 7, "player_side": "attacker",
            "snapshot_revision": 100, "date_raw": 10000, "rows": [{
                "province_id": 12, "siege_observable": True, "active_siege": {
                    "siege_id": 11, "assault_observable": True,
                    "assault_in_progress": active, "can_start_assault": not active,
                    "can_stop_assault": active, "player_army_besieging": True}}]}}}


class _Lock:
    def __init__(self):
        self.value = RLock()
        self.depth = 0

    def __enter__(self):
        self.value.acquire()
        self.depth += 1

    def __exit__(self, *args):
        self.depth -= 1
        self.value.release()


class _History(list):
    def __init__(self, lock, rows):
        super().__init__(rows)
        self.lock = lock
        self.slices = 0

    def __getitem__(self, key):
        if isinstance(key, slice):
            if not self.lock.depth or key != slice(-128, None):
                raise AssertionError("changed the locked 128-row history boundary")
            self.slices += 1
        return super().__getitem__(key)


class _Payload:
    def __init__(self):
        self.copies = 0

    def __deepcopy__(self, memo):
        self.copies += 1
        return self


def _driver(rows, *, active=False):
    driver = native.NativeHeadlessGameplayDriver.__new__(native.NativeHeadlessGameplayDriver)
    driver._history_lock = _Lock()
    driver._command_history = _History(driver._history_lock, rows)
    driver.command_timeout_seconds = 0.1
    driver.take_snapshot = Mock(return_value=_snapshot())
    driver._history_tail_snapshot = Mock(side_effect=AssertionError("unrelated tail copied"))

    def primitive(step, **kwargs):
        if driver._history_lock.depth:
            raise AssertionError("primitive under history lock")
        return {"step": step, "accepted": True,
            "status": "stop_submitted" if active else "start_submitted"}

    def query(step, **kwargs):
        if driver._history_lock.depth or step != "query-war-occupation-targets-v1-8":
            raise AssertionError("post-read scope or lock changed")
        return _query(not active)["result"]

    def wait(snapshot, predicate, **kwargs):
        if driver._history_lock.depth or not predicate(snapshot):
            raise AssertionError("independent post-read not satisfied")
        return snapshot

    driver._execute_primitive_step = Mock(side_effect=primitive)
    driver.execute_step = Mock(side_effect=query)
    driver._wait_for_snapshot = Mock(side_effect=wait)
    return driver


def _attempt(driver, active=False):
    return driver._execute_native_war_step(
        "stop-assault-11" if active else "start-assault-11", expected_revision=3)


class AssaultHoldingHistoryProjectionCopyTests(unittest.TestCase):
    def test_start_and_stop_keep_independent_query_and_original_history(self):
        for active in (False, True):
            with self.subTest(active=active):
                rows = [_query(active)]
                before = deepcopy(rows)
                driver = _driver(rows, active=active)
                result = _attempt(driver, active)
                self.assertEqual(result["assault_action"]["status"],
                    "assault_stopped" if active else "assault_started")
                self.assertIs(result["active_siege"]["assault_in_progress"], not active)
                self.assertEqual(list(driver._command_history), before)
                self.assertEqual(driver._command_history.slices, 1)
                driver._history_tail_snapshot.assert_not_called()
                driver.execute_step.assert_called_once_with(
                    "query-war-occupation-targets-v1-8", expected_revision=3)
                self.assertEqual(driver._history_lock.depth, 0)

    def test_unrelated_body_copy_is_eliminated_but_selected_state_is_isolated(self):
        payload = _Payload()
        row = _query()
        siege = row["result"]["war_occupation_targets_v1"]["rows"][0]["active_siege"]
        driver = _driver([{"command": "query-unrelated", "result": payload}, row])
        native.NativeHeadlessGameplayDriver._history_tail_snapshot(driver, 128)
        self.assertEqual(payload.copies, 1)
        payload.copies = 0
        inspect = native._assault_siege_observation

        def observe(snapshot, **kwargs):
            result = inspect(snapshot, **kwargs)
            if isinstance(result, dict):
                self.assertIsNot(result["active_siege"], siege)
                result["active_siege"]["fixture_local_annotation"] = True
            return result

        with patch.object(native, "_assault_siege_observation", side_effect=observe):
            _attempt(driver)
        self.assertEqual(payload.copies, 0)
        self.assertNotIn("fixture_local_annotation", siege)
        driver._history_tail_snapshot.assert_not_called()

    def test_oldest_allowed_row_and_successful_restore_cut_are_unchanged(self):
        flat = {"command": "unrelated", "ok": True}
        restore = {"command": native._RESTORE_CHECKPOINT_STEP, "ok": True}
        cases = [([_query()] + [flat] * 127, True),
            ([_query()] + [flat] * 128, False), ([_query(), restore], False),
            ([_query(), {**restore, "ok": False}], True),
            ([restore, _query()], True)]
        for rows, accepted in cases:
            with self.subTest(rows=len(rows), accepted=accepted):
                driver = _driver(rows)
                if accepted:
                    _attempt(driver)
                else:
                    with self.assertRaisesRegex(BridgeUnavailableError, "observable SiegeID"):
                        _attempt(driver)
                    driver._execute_primitive_step.assert_not_called()

    def test_newest_failed_or_stale_query_still_blocks_older_valid_query(self):
        for key, value in (("ok", False), ("queried_revision", 4),
                ("queried_native_revision", 101), ("queried_connection_generation", 2),
                ("queried_episode_run_id", "other")):
            with self.subTest(key=key):
                bad = _query()
                if key == "ok":
                    bad[key] = value
                else:
                    bad["result"][key] = value
                driver = _driver([_query(), bad])
                with self.assertRaisesRegex(BridgeUnavailableError, "observable SiegeID"):
                    _attempt(driver)
                driver._execute_primitive_step.assert_not_called()
                driver.execute_step.assert_not_called()

    def test_snapshot_permission_and_assault_eligibility_rejections_remain(self):
        for key, value in (("paused", False), ("war_objective_assault_supported", False)):
            with self.subTest(key=key):
                driver = _driver([_query()])
                driver.take_snapshot.return_value[key] = value
                with self.assertRaises(BridgeUnavailableError):
                    _attempt(driver)
                driver._execute_primitive_step.assert_not_called()
        driver = _driver([_query(True)])
        with self.assertRaisesRegex(BridgeUnavailableError, "not eligible"):
            _attempt(driver)
        driver._execute_primitive_step.assert_not_called()

    def test_bad_ack_and_missing_postcondition_are_not_success(self):
        driver = _driver([_query()])
        driver._execute_primitive_step = Mock(return_value={"status": "submitted"})
        with self.assertRaisesRegex(BridgeUnavailableError, "malformed submission status"):
            _attempt(driver)
        driver.execute_step.assert_not_called()
        driver = _driver([_query()])
        driver._wait_for_snapshot = Mock(side_effect=lambda snapshot, predicate, **kwargs: snapshot)
        with self.assertRaisesRegex(BridgeUnavailableError, "same-SiegeID paused postcondition"):
            _attempt(driver)


if __name__ == "__main__":
    unittest.main()
