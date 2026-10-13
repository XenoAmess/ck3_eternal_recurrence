"""StartGame map and post-ready pump share one bounded observation window."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.frontend_gui_route_contract import (
    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
    QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP,
    normalize_frontend_selected_1066_feudal_candidate_v1,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


ROBERT_KEY = "bookmark_rags_to_riches_duke_robert"


class NoIOEndpoint:
    """Constructor callbacks are accepted; any attempted transport send fails."""

    pipe_name = r"\\.\pipe\frontend-shared-deadline-offline-fixture"

    def __init__(self):
        self.sent = []
        self.closed = False

    def start(self, on_frame, on_disconnect):
        self.on_frame, self.on_disconnect = on_frame, on_disconnect

    def send(self, frame):
        self.sent.append(frame)
        raise AssertionError("no native pipe or protocol send is allowed")

    def close(self):
        self.closed = True


class FakeClock:
    def __init__(self):
        self.seconds = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.seconds

    def sleep(self, seconds):
        if seconds <= 0:
            raise AssertionError("observation sleep must have a positive remaining budget")
        self.sleeps.append(seconds)
        self.seconds += seconds


def paused_map(*, epoch=100, revision=3):
    return {
        "snapshot_id": f"native:{revision}", "native_revision": revision,
        "revision": revision, "paused": True, "map_ready": True,
        "date_raw": 53178312, "played_character": {"character_id": 29829},
        "diagnostics": {"bridge_pid": 16168, "connection_generation": 1,
                        "last_heartbeat": {"main_thread_query_mailbox_v1": {"pump_epochs": epoch}}},
    }


def campaign_root(*, revision):
    return {
        "campaign_root_context_ready": True, "queried_native_revision": revision,
        "date_raw": 53178312, "player_character_id": 29829,
        "government": {"key": "feudal_government"},
    }


def candidate():
    return normalize_frontend_selected_1066_feudal_candidate_v1({
        "step": QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP,
        "accepted": True, "status": "ready", "route": "bookmarks",
        "selected_bookmark_group_key": "bm_group_1066",
        "selected_bookmark_key": "bm_1066_rags_to_riches",
        "selected_character_name_key": ROBERT_KEY,
        "selected_character_government_key": "feudal_government",
        "selected_bookmark_start_date_raw": 53178312, "query_sequence": 1,
    }, expected_character_name_key=ROBERT_KEY)


class FrontendSharedDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.endpoint = NoIOEndpoint()
        native_pipe = self.enterContext(patch(
            "xar_autoplayer.bridge.native_driver.NativeNamedPipeServer",
            side_effect=AssertionError("a real native pipe cannot be constructed"),
        ))
        self.driver = NativeHeadlessGameplayDriver(
            self.endpoint.pipe_name, endpoint=self.endpoint,
            frontend_transition_timeout_seconds=600.0,
        )
        self.addCleanup(self.driver.close)
        native_pipe.assert_not_called()
        self.enterContext(patch(
            "xar_autoplayer.bridge.native_driver.time.monotonic",
            side_effect=self.clock.monotonic,
        ))
        self.enterContext(patch(
            "xar_autoplayer.bridge.native_driver.time.sleep", side_effect=self.clock.sleep,
        ))
        self.driver.query_frontend_gui_route_v1 = Mock(return_value={"route": "bookmarks"})
        self.driver._execute_primitive_step = Mock(return_value={
            "step": ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
            "accepted": True, "status": "acknowledged_verification_pending",
            "backend_id": "native-headless",
        })
        self.driver._execute_campaign_root_context_v1_query = Mock()

    def start(self):
        return self.driver.activate_frontend_start_selected_bookmark_v1(
            expected_character_name_key=ROBERT_KEY, selected_candidate=candidate(),
        )

    def assert_single_start(self):
        self.driver._execute_primitive_step.assert_called_once_with(
            ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
            expected_revision=0,
            required_capability=ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
            allow_frontend_revision_zero=True,
        )
        self.assertEqual(self.endpoint.sent, [])

    def test_near_deadline_map_cannot_grant_a_second_600_second_pump_window(self):
        reads = []

        def observed():
            reads.append(self.clock.seconds)
            if len(reads) == 1:
                # The original Start budget ends at700, leaving one quarter second.
                self.clock.seconds = 699.75
            # A new semantic publication is not ApplicationMain pump progress.
            return paused_map(epoch=100, revision=2 + len(reads))

        self.driver.take_snapshot = Mock(side_effect=observed)
        with self.assertRaisesRegex(BridgeUnavailableError, "pump did not advance"):
            self.start()
        self.assertEqual(self.clock.seconds, 700.0)
        self.assertEqual(self.clock.sleeps, [0.25])
        self.assertEqual(len(reads), 2)
        self.driver._execute_campaign_root_context_v1_query.assert_not_called()
        self.assert_single_start()

    def test_advanced_pump_within_original_remainder_verifies_the_single_start(self):
        reads = []

        def observed():
            reads.append(self.clock.seconds)
            if len(reads) == 1:
                self.clock.seconds = 699.5
            return paused_map(epoch=101 if len(reads) == 3 else 100,
                              revision=2 + len(reads))

        self.driver.take_snapshot = Mock(side_effect=observed)
        self.driver._execute_campaign_root_context_v1_query.return_value = campaign_root(revision=5)
        result = self.start()
        self.assertEqual(self.clock.seconds, 699.75)
        self.assertEqual(self.clock.sleeps, [0.25])
        self.assertEqual(len(reads), 3)
        self.assertIs(result["postcondition_verified"], True)
        self.assertEqual(result["status"], "verified")
        self.driver._execute_campaign_root_context_v1_query.assert_called_once_with(expected_revision=None)
        self.assert_single_start()

    def test_expired_explicit_pump_deadline_reads_no_new_frame(self):
        self.driver.take_snapshot = Mock(side_effect=AssertionError("expired budget cannot observe again"))
        with self.assertRaisesRegex(BridgeUnavailableError, "observations=0"):
            self.driver._wait_for_frontend_start_post_ready_pump_v1(
                paused_map(), deadline=self.clock.seconds,
            )
        self.driver.take_snapshot.assert_not_called()
        self.driver._execute_primitive_step.assert_not_called()
        self.assertEqual(self.clock.seconds, 100.0)
        self.assertEqual(self.clock.sleeps, [])

    def test_standalone_pump_helper_keeps_its_default_configured_window(self):
        self.driver.frontend_transition_timeout_seconds = 1.0

        def observed():
            return paused_map(epoch=101 if self.clock.seconds >= 100.75 else 100,
                              revision=4)

        self.driver.take_snapshot = Mock(side_effect=observed)
        result = self.driver._wait_for_frontend_start_post_ready_pump_v1(paused_map())
        self.assertEqual(self.clock.seconds, 100.75)
        self.assertEqual(self.driver.take_snapshot.call_count, 4)
        self.assertEqual(result["diagnostics"]["last_heartbeat"]
                         ["main_thread_query_mailbox_v1"]["pump_epochs"], 101)
        self.driver._execute_primitive_step.assert_not_called()
        self.assertEqual(self.endpoint.sent, [])


if __name__ == "__main__":
    unittest.main()
