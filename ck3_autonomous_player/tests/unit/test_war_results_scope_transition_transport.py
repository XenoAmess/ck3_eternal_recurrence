"""A returned UI close may release pause; read-only queries keep their lease."""
from pathlib import Path
import copy
import sys
import threading
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_results_window_transport import execute_war_results_window_v1


def fixture(operation):
    before = dict(snapshot_id="native:617", revision=3, native_revision=617,
                  date_raw=53169792, episode_run_id="synthetic-ui-scope-episode", paused=True,
                  map_ready=True, played_character=dict(character_id=31254, alive=True),
                  diagnostics=dict(connection_generation=13, hello=dict(connection_generation=13,
                      expected_ck3_version=CK3_12004.game_version,
                      expected_ck3_sha256=CK3_12004.executable_sha256)))
    after = copy.deepcopy(before)
    after.update(paused=False, date_raw=before["date_raw"]+24)
    frames, calls = iter([before, after]), []
    driver = SimpleNamespace(_driver_state_lock=threading.RLock(),
        _war_results_window_close_pending=None, _war_results_window_attempt=0,
        _war_results_window_observation=None, _war_results_window_query_attempt=None,
        _war_results_window_last_clear=None, command_timeout_seconds=10,
        take_internal_semantic_snapshot=lambda: copy.deepcopy(next(frames)))
    def reply(rid, timeout):
        leaf = dict(schema="ck3-war-results-window-v1", operation=operation, window_name="war_results",
            available=operation=="query", accepted=operation=="query",
            status="visible" if operation=="query" else "verification_pending",
            unavailable_reason="" if operation=="query" else
                "war_results_ui_scope_transition;begin_date_raw=53169792;end_date_raw=53169816;begin_paused=true;end_paused=false;owner_boundary_admitted=true",
            root_observed=True, window_present=True, effective_visible=True,
            button_name="" if operation=="query" else "close_button",
            dispatch_attempted=operation=="close", dispatch_invoked=operation=="close",
            native_handled=operation=="close", post_observed=True,
            post_window_present=True, post_effective_visible=True,
            scope_unchanged=operation=="query", closure_verified=False,
            application_owner_thread_verified=True, played_character_id=31254,
            date_raw=53169792, paused=True, native_revision=617, connection_generation=13,
            pump_epoch=101, thread_id=202, ticket_sequence=303, request_id=rid,
            root_observation_source="guarded_top_level_and_complete_owner_tree",
            post_observation_source="guarded_top_level_and_complete_owner_tree",
            game_version=CK3_12004.game_version, executable_sha256=CK3_12004.executable_sha256,
            dismiss_stage="not_attempted" if operation=="query" else "callback_returned",
            dismiss_exception_code=0)
        owner = dict(request_id=rid, ticket_sequence=303, executor_started_sequence=303,
                     completed_sequence=303, pump_epoch=101, thread_id=202,
                     date_raw=53169792, connection_generation=13)
        return dict(type="command_result", protocol_version=1, request_id=rid,
                    ok=True, result=leaf, war_results_window_owner_receipt=owner)
    driver.endpoint = SimpleNamespace(send=lambda request: calls.append(request))
    driver.state = SimpleNamespace(capabilities=lambda: {"bridge_capabilities": [
        "game.command.query-war-results-window-v1", "game.command.close-war-results-window-v1"]},
        wait_for_command_result=reply)
    return driver, calls


class WarResultsScopeTransitionTransport(unittest.TestCase):
    def test_returned_close_retains_pending_across_pause_release(self):
        driver, calls = fixture("close")
        result = execute_war_results_window_v1(driver, operation="close", expected_revision=3)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["status"], "verification_pending")
        self.assertFalse(result["accepted"])
        self.assertFalse(result["closure_verified"])
        self.assertEqual(driver._war_results_window_close_pending["status"], "verification_pending")

    def test_read_only_query_still_rejects_scope_drift(self):
        driver, calls = fixture("query")
        with self.assertRaises(BridgeUnavailableError):
            execute_war_results_window_v1(driver, operation="query", expected_revision=3)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
