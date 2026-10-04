"""Synthetic opening proof and durable one-claim regressions; never use a game endpoint."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.ingame_decisions_open_contract import CAPABILITY, EXE_SHA256, STEP
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def snapshot():
    return {"revision": 1, "native_revision": 7, "snapshot_id": "synthetic-paused-7",
            "episode_run_id": "synthetic-opener-episode", "paused": True, "map_ready": True,
            "date_raw": 1234, "played_character": {"character_id": 7001, "alive": True},
            "diagnostics": {"connection_generation": 1, "pid": 99999,
                            "hello": {"pid": 12700, "ck3_build_match": True,
                                      "game_adapter_id": "ck3-1.20.0.3-msvc-x64",
                                      "expected_ck3_version": "1.20.0.3",
                                      "expected_ck3_sha256": EXE_SHA256}}}


def pending_native_ack():
    return {"schema": "ck3-ingame-decisions-open-v1", "step": STEP, "game_version": "1.20.0.3",
            "executable_sha256": EXE_SHA256, "native_revision": 7,
            "connection_generation": 1, "game_pid": 12700, "played_character_id": 7001,
            "date_raw": 1234, "owner_thread_verified": True, "frame_verified": True,
            "source_abi_pins_verified": True, "gui_owner_binding_verified": True,
            "native_after_read": True, "before_visible": False, "dispatch_invoked": True,
            "topbar_tree_complete": True, "receiver_qualified": True,
            "native_after_visible": False, "native_after_tree_complete": False,
            "postcondition_verified": False, "verification_pending": True}


class SyntheticDriver:
    open_ingame_decisions_v1 = NativeHeadlessGameplayDriver.open_ingame_decisions_v1

    def __init__(self, state_directory, *, frame=None, ack=None, action_error=None):
        self.frame = deepcopy(snapshot() if frame is None else frame)
        self.ack = deepcopy(pending_native_ack() if ack is None else ack)
        self.state_directory = Path(state_directory)
        self.action_error = action_error
        self.submissions = []
        self.queries = []
        self.records = []

    def take_snapshot(self): return deepcopy(self.frame)
    def capabilities(self): return {"bridge_capabilities": [CAPABILITY]}
    def _native_driver_state_path(self): return self.state_directory / "synthetic-state.json"
    def _record_command(self, *args, **kwargs): self.records.append((args, kwargs))

    def _execute_primitive_step(self, step, **kwargs):
        self.submissions.append((step, kwargs))
        if self.action_error is not None:
            raise self.action_error
        return deepcopy(self.ack)

    def inspect_gui_window_tree_v1(self, kind):
        self.queries.append(kind)
        return {"scope_root_name": "decisions_view", "root_available": True,
                "truncated": False, "widgets": [{"child_path": "", "runtime_name": "decisions_view",
                                                  "effective_visible": True}]}


class DecisionsOpeningProofTests(unittest.TestCase):
    def state_directory(self):
        parent = os.environ.get("XAR_WHITE_DECISIONS_TEST_ARTIFACTS")
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        # Preserve synthetic claims for inspection; no old runtime/state path is used.
        return Path(tempfile.mkdtemp(prefix="synthetic-claim-", dir=parent))

    def test_invalid_actual_binding_rejects_before_claim_or_submission(self):
        for invalid in ("hash", "dead", "revision", "missing_game_pid"):
            with self.subTest(invalid=invalid):
                frame = snapshot()
                if invalid == "hash": frame["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
                if invalid == "dead": frame["played_character"]["alive"] = False
                if invalid == "revision": frame["native_revision"] = True
                if invalid == "missing_game_pid": del frame["diagnostics"]["hello"]["pid"]
                driver = SyntheticDriver(self.state_directory(), frame=frame)
                with self.assertRaises(BridgeUnavailableError): driver.open_ingame_decisions_v1()
                self.assertEqual(driver.submissions, [])
                self.assertEqual(driver.queries, [])
                self.assertFalse((driver.state_directory / "ingame-decisions-opener-actions").exists())

    def test_invalid_native_proof_consumes_one_claim_and_cannot_be_retried(self):
        for invalid in ("game_pid", "gui_owner_binding_verified", "native_after_read"):
            with self.subTest(invalid=invalid):
                ack = pending_native_ack()
                ack[invalid] = 99999 if invalid == "game_pid" else False
                driver = SyntheticDriver(self.state_directory(), ack=ack)
                with self.assertRaises(ValueError): driver.open_ingame_decisions_v1()
                self.assertEqual(len(driver.submissions), 1)
                self.assertEqual(driver.queries, [])
                with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
                    driver.open_ingame_decisions_v1()
                self.assertEqual(len(driver.submissions), 1)

    def test_lost_ack_is_not_queried_or_resubmitted_even_after_reconnect(self):
        directory = self.state_directory()
        driver = SyntheticDriver(directory, action_error=TimeoutError("synthetic lost ACK"))
        with self.assertRaises(TimeoutError): driver.open_ingame_decisions_v1()
        self.assertEqual(len(driver.submissions), 1)
        self.assertEqual(driver.queries, [])
        claim_files = list((directory / "ingame-decisions-opener-actions").glob("*.claim.json"))
        self.assertEqual(len(claim_files), 1)
        claim = json.loads(claim_files[0].read_text(encoding="utf-8"))
        self.assertEqual(claim["status"], "claimed_result_unknown_no_retry")
        self.assertEqual(claim["request_id"], driver.submissions[0][1]["protocol_request_id"])
        self.assertEqual(list(claim_files[0].parent.glob("*.result.json")), [])
        reconnect_frame = snapshot()
        reconnect_frame["diagnostics"]["connection_generation"] = 2
        reconnected = SyntheticDriver(directory, frame=reconnect_frame)
        with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
            reconnected.open_ingame_decisions_v1()
        self.assertEqual(reconnected.submissions, [])

    def test_pending_ack_needs_independent_current_visible_root(self):
        driver = SyntheticDriver(self.state_directory())
        result = driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(len(driver.submissions), 1)
        self.assertEqual(driver.queries, ["decisions"])
        self.assertFalse(result["native_ack"]["postcondition_verified"])
        self.assertTrue(result["postcondition_verified"])
        self.assertFalse(result["verification_pending"])
        self.assertEqual(result["later_decisions_tree"]["scope_root_name"], "decisions_view")
        self.assertEqual(driver.submissions[0][1]["request_fields"]["expected_game_pid"], 12700)
        with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
            driver.open_ingame_decisions_v1()
        self.assertEqual(len(driver.submissions), 1)
