from __future__ import annotations

import copy
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_event_window_context_v1_bridge import (
    EVENT_ID,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    _Driver as EventServiceDriver,
    _query_result as event_query_result,
    _snapshot as event_snapshot,
)
from test_player_faction_alerts_v1_bridge import (
    PUBLIC_REVISION,
    _ServiceDriver as FactionServiceDriver,
)


class NoFullFactionDriver(FactionServiceDriver):
    def take_snapshot(self):
        raise AssertionError("full faction service snapshot")

    def take_snapshot_without_native_command_history(self):
        return FactionServiceDriver.take_snapshot(self)


class FullOnlyFactionDriver(FactionServiceDriver):
    take_snapshot_without_native_command_history = None

    def take_snapshot(self):
        frame = super().take_snapshot()
        frame["native_command_history"] = [{"command": "historic-sentinel", "ok": True}]
        return frame


class NoFullEventDriver(EventServiceDriver):
    def take_snapshot(self):
        raise AssertionError("full event service snapshot")

    def take_snapshot_without_native_command_history(self):
        return EventServiceDriver.take_snapshot(self)


class FullOnlyEventDriver(EventServiceDriver):
    take_snapshot_without_native_command_history = None

    def take_snapshot(self):
        frame = super().take_snapshot()
        frame["native_command_history"] = [{"command": "historic-sentinel", "ok": True}]
        return frame


class DriftEventDriver(NoFullEventDriver):
    def __init__(self) -> None:
        super().__init__()
        self.reads = 0

    def take_snapshot_without_native_command_history(self):
        self.reads += 1
        frame = super().take_snapshot_without_native_command_history()
        if self.reads > 1:
            frame["revision"] += 1
        return frame


class EventNativeDriver(NativeHeadlessGameplayDriver):
    def __init__(self, *, drift: bool = False) -> None:
        self._driver_state_lock = threading.RLock()
        self.drift = drift
        self.snapshots = 0
        self.primitive_calls = 0

    def capabilities(self):
        return {
            "bridge_capabilities": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY],
            "action_steps": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP],
        }

    def take_snapshot(self):
        raise AssertionError("full event native snapshot")

    def take_snapshot_without_native_command_history(self):
        self.snapshots += 1
        frame = copy.deepcopy(event_snapshot())
        frame["episode_run_id"] = "event-history-free-fixture"
        frame["diagnostics"] = {"connection_generation": 7}
        if self.drift and self.snapshots > 1:
            frame["revision"] += 1
        return frame

    def _execute_primitive_step(
        self, step, *, expected_revision, required_capability,
        request_fields, include_native_command_history=True,
    ):
        assert step == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        assert expected_revision == 9
        assert required_capability == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
        assert request_fields == {"event_instance_id": EVENT_ID}
        assert include_native_command_history is False
        self.primitive_calls += 1
        complete = event_query_result()
        return {key: copy.deepcopy(complete[key]) for key in (
            "step", "accepted", "status", "query_sequence", "snapshot_revision",
            "current_event_window_context", "backend_id",
        )}


class HistoryFreePureQueryTests(unittest.TestCase):
    def test_faction_service_uses_finite_frame_and_preserves_scope(self):
        actual = GameplayBridgeService(NoFullFactionDriver()).query_player_faction_alerts_v1(
            expected_revision=PUBLIC_REVISION,
        )
        expected = GameplayBridgeService(FullOnlyFactionDriver()).query_player_faction_alerts_v1(
            expected_revision=PUBLIC_REVISION,
        )
        self.assertEqual(actual, expected)

    def test_event_service_uses_finite_frame_and_preserves_scope(self):
        actual = GameplayBridgeService(NoFullEventDriver()).query_current_event_window_context_v1(
            EVENT_ID, expected_revision=9,
        )
        expected = GameplayBridgeService(FullOnlyEventDriver()).query_current_event_window_context_v1(
            EVENT_ID, expected_revision=9,
        )
        self.assertEqual(actual, expected)

    def test_event_service_frame_drift_still_refused(self):
        with self.assertRaisesRegex(Exception, "crossed a snapshot revision"):
            GameplayBridgeService(DriftEventDriver()).query_current_event_window_context_v1(
                EVENT_ID, expected_revision=9,
            )

    def test_event_native_uses_two_finite_snapshots_and_finite_primitive(self):
        driver = EventNativeDriver()
        result = driver.query_current_event_window_context_v1(EVENT_ID, expected_revision=9)
        self.assertEqual(result["current_event_window_context"], event_query_result()["current_event_window_context"])
        self.assertEqual(result["queried_revision"], 9)
        self.assertEqual(driver.snapshots, 2)
        self.assertEqual(driver.primitive_calls, 1)

    def test_event_native_frame_drift_still_refused(self):
        driver = EventNativeDriver(drift=True)
        with self.assertRaisesRegex(Exception, "crossed a snapshot revision"):
            driver.query_current_event_window_context_v1(EVENT_ID, expected_revision=9)
        self.assertEqual(driver.snapshots, 2)
        self.assertEqual(driver.primitive_calls, 1)

    def test_event_dispatch_identity_read_is_also_finite(self):
        driver = EventNativeDriver()
        result = driver._execute_step_unrecorded(
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, expected_revision=9,
        )
        self.assertEqual(result["queried_revision"], 9)
        self.assertEqual(driver.snapshots, 3)
        self.assertEqual(driver.primitive_calls, 1)


if __name__ == "__main__":
    unittest.main()
