"""Real submission guards with in-memory history; no native endpoint or files."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.driver import BridgeUnavailableError


class _Lock:
    def __init__(self):
        self.lock = RLock()
        self.depth = 0

    def __enter__(self):
        self.lock.acquire()
        self.depth += 1

    def __exit__(self, *args):
        self.depth -= 1
        self.lock.release()


class _History(list):
    def __init__(self, lock, rows):
        super().__init__(rows)
        self.lock = lock
        self.scans = 0

    def __reversed__(self):
        if not self.lock.depth:
            raise AssertionError("history was inspected without its lock")
        self.scans += 1
        return super().__reversed__()


class _Payload:
    def __init__(self):
        self.copies = 0

    def __deepcopy__(self, memo):
        self.copies += 1
        return self


class _ReachedPrimitive(Exception):
    pass


def _row(outcome, *, war_id=8, episode="episode", status="applied", **extra):
    step = "offer-white-peace-8" if outcome == "white_peace" else "surrender-war-8"
    return {"index": 2, "command": step, "ok": True, "result": {
        "war_termination_result": {"war_id": war_id, "episode_run_id": episode,
            "outcome": outcome, "status": status, **extra}}}


def _driver(rows):
    driver = native.NativeHeadlessGameplayDriver.__new__(native.NativeHeadlessGameplayDriver)
    driver.state_dir = None
    driver._war31_one_shot_surrender_gate = None
    driver._history_lock = _Lock()
    driver._command_history = _History(driver._history_lock, rows)
    driver.state = SimpleNamespace(capabilities=lambda: {"bridge_capabilities": [
        native.QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
        native.SURRENDER_WAR_CAPABILITY, native.OFFER_WHITE_PEACE_CAPABILITY]})
    driver._history_snapshot = Mock(side_effect=AssertionError("full history export"))

    def reached(*args, **kwargs):
        if driver._history_lock.depth:
            raise AssertionError("primitive called while holding history lock")
        raise _ReachedPrimitive()

    driver._execute_primitive_step = Mock(side_effect=reached)
    return driver


def _attempt(driver, *, surrender=False, variant="ordinary", date=10000):
    starting = {"paused": True, "active_wars": [{"war_id": 8}],
        "episode_run_id": "episode", "date_raw": date}
    readiness = "_emergency_surrender_readiness" if surrender else "_white_peace_readiness"
    with patch.object(native, readiness, return_value=(True, "ready", {"variant": variant})):
        return driver._execute_war_termination_step(
            "surrender-war-8" if surrender else "offer-white-peace-8",
            starting=starting, selected_revision=3, query_war_id=None,
            surrender_war_id=8 if surrender else None,
            white_peace_war_id=None if surrender else 8)


class WarTerminationHistoryReadGuardTests(unittest.TestCase):
    def assert_no_export(self, driver):
        driver._history_snapshot.assert_not_called()
        self.assertEqual(driver._history_lock.depth, 0)

    def test_same_episode_surrender_is_still_rejected_before_primitive(self):
        for outcome in ("attacker_defeat", "attacker_victory"):
            for status in ("submitted_pending", "applied"):
                with self.subTest(outcome=outcome, status=status):
                    row = _row(outcome, status=status)
                    before = deepcopy(row)
                    driver = _driver([row])
                    with self.assertRaisesRegex(BridgeUnavailableError, "already submitted"):
                        _attempt(driver, surrender=True)
                    self.assertEqual(row, before)
                    driver._execute_primitive_step.assert_not_called()
                    self.assert_no_export(driver)

    def test_unrelated_failed_and_other_episode_surrenders_do_not_fence(self):
        rows = [_row("attacker_victory", war_id=9),
            _row("attacker_victory", episode="earlier"),
            _row("attacker_victory", status="rejected")]
        failed = _row("attacker_victory"); failed["ok"] = False
        rows.append(failed)
        driver = _driver(rows)
        with self.assertRaises(_ReachedPrimitive):
            _attempt(driver, surrender=True)
        driver._execute_primitive_step.assert_called_once()
        self.assert_no_export(driver)

    def test_de_jure_fence_survives_cooldown_expiry(self):
        row = _row("white_peace", submitted_date_raw=0, casus_belli={
            "canonical_key": native._DE_JURE_NO_SAFE_ROUTE_SURRENDER_CB,
            "database_index": native._DE_JURE_NO_SAFE_ROUTE_CB_DATABASE_INDEX})
        driver = _driver([row])
        with self.assertRaisesRegex(BridgeUnavailableError, "one-shot WarID fence"):
            _attempt(driver, variant="de_jure_no_safe_route")
        self.assertEqual(driver._command_history.scans, 1)
        driver._execute_primitive_step.assert_not_called()
        self.assert_no_export(driver)

    def test_cooldown_and_malformed_dates_still_reject_without_send(self):
        for submitted, date in ((9999, 10000), (10001, 10000), (None, 10000),
                (True, 10000), (0, True)):
            with self.subTest(submitted=submitted, date=date):
                driver = _driver([_row("white_peace", submitted_date_raw=submitted)])
                with self.assertRaisesRegex(BridgeUnavailableError, "30-day"):
                    _attempt(driver, date=date)
                driver._execute_primitive_step.assert_not_called()
                self.assert_no_export(driver)

    def test_exact_cooldown_boundary_and_newest_matching_row_are_preserved(self):
        boundary = 10000 - native._WHITE_PEACE_PROPOSAL_COOLDOWN_RAW
        rows = [_row("white_peace", submitted_date_raw=9999),
            _row("white_peace", submitted_date_raw=boundary),
            _row("white_peace", episode="other", submitted_date_raw=9999)]
        before = deepcopy(rows)
        driver = _driver(rows)
        with self.assertRaises(_ReachedPrimitive):
            _attempt(driver)
        self.assertEqual(list(driver._command_history), before)
        driver._execute_primitive_step.assert_called_once()
        self.assert_no_export(driver)

    def test_de_jure_and_cooldown_miss_only_scan_locked_metadata(self):
        payload = _Payload()
        row = {"command": "query-combat-simulation-inputs-v2-example", "ok": True,
            "result": {"canonical_full_inputs": payload}}
        driver = _driver([row])
        # The former two snapshot calls copied this body twice, regardless of size.
        tracked = driver._command_history
        driver._command_history = list(tracked)
        native.NativeHeadlessGameplayDriver._history_snapshot(driver)
        native.NativeHeadlessGameplayDriver._history_snapshot(driver)
        driver._command_history = tracked
        self.assertEqual(payload.copies, 2)
        payload.copies = 0
        for surrender in (False, True):
            with self.subTest(surrender=surrender), self.assertRaises(_ReachedPrimitive):
                _attempt(driver, surrender=surrender, variant="de_jure_no_safe_route")
        self.assertEqual(payload.copies, 0)
        self.assertEqual(driver._command_history.scans, 3)
        self.assertIs(driver._command_history[0], row)
        self.assertIs(row["result"]["canonical_full_inputs"], payload)
        self.assert_no_export(driver)

    def test_original_readiness_rejection_still_precedes_history_inspection(self):
        driver = _driver([])
        with patch.object(native, "_white_peace_readiness", return_value=(False, "stale", {})):
            with self.assertRaisesRegex(BridgeUnavailableError, "fresh validation failed: stale"):
                driver._execute_war_termination_step("offer-white-peace-8",
                    starting={"paused": True, "active_wars": [{"war_id": 8}]},
                    selected_revision=3, query_war_id=None, surrender_war_id=None,
                    white_peace_war_id=8)
        self.assertEqual(driver._command_history.scans, 0)
        driver._execute_primitive_step.assert_not_called()
        self.assert_no_export(driver)


if __name__ == "__main__":
    unittest.main()
