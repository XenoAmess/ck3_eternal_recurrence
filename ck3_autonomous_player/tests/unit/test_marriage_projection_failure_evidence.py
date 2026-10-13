"""New production transport failure evidence tests only; no RPC or native compiler."""
from pathlib import Path
import copy
import json
import tempfile
import unittest

from test_marriage_candidate_alliance_private_transport import _frame, _legality, _reply, IDS
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004

from xar_autoplayer.bridge import marriage_candidate_alliance_private_transport as candidate


class Driver:
    def __init__(self, state_dir, reply, *, before=None, after=None):
        self.state_dir, self.reply = state_dir, reply
        self.endpoint = self.state = self
        self.before = before or _frame()
        self.before["diagnostics"] = {"hello": {"game_version": CK3_12004.game_version,
                                               "executable_sha256": CK3_12004.executable_sha256}}
        self.before.update(snapshot_id="native:3", revision=4, episode_run_id="native-29829-failure-fixture")
        self.frames = [self.before, after or copy.deepcopy(self.before)]
        self.requests, self.wait_ids = [], []

    def take_snapshot(self):
        return self.frames.pop(0)

    def send(self, request):
        self.requests.append(request)

    def wait_for_command_result(self, request_id, timeout_seconds):
        self.wait_ids.append(request_id)
        return self.reply


def legality():
    result = _legality()
    result.update(exact_ck3_build=CK3_12004.game_version, exe_sha256=CK3_12004.executable_sha256,
                  root_query_sequence=33)
    return result


class NewTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, driver, *, legal=None, ids=None):
        return candidate.query_first_heir_candidate_alliance_projection_private_v1(
            driver, legality=legal or legality(), candidate_character_ids=ids or IDS)

    def test_exact12004_five_current_rows_production_transport_positive(self):
        driver = Driver(self.directory, _reply())
        result = self.call(driver)
        self.assertEqual(result["exact_ck3_build"], CK3_12004.game_version)
        self.assertEqual(result["exe_sha256"], CK3_12004.executable_sha256)
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(len(driver.requests), 1)

    def test_unknown_hash_is_rejected_before_send(self):
        driver = Driver(self.directory, _reply())
        driver.before["diagnostics"]["hello"]["executable_sha256"] = "0" * 64
        with self.assertRaises(BridgeUnavailableError):
            self.call(driver)
        self.assertEqual(driver.requests, [])

    def test_four_or_duplicate_ids_still_rejected_before_send(self):
        for ids in (IDS[:4], IDS[:4] + [IDS[0]]):
            driver = Driver(self.directory, _reply())
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.call(driver, ids=ids)
            self.assertEqual(driver.requests, [])

    def test_stale_frame_and_nonunique_legal_candidate_still_rejected_before_send(self):
        for change in ("frame", "duplicate"):
            driver = Driver(self.directory, _reply())
            legal = legality()
            if change == "frame":
                driver.before["native_revision"] += 1
            else:
                legal["native_legal_candidates"].append(copy.deepcopy(legal["native_legal_candidates"][0]))
            with self.subTest(change=change), self.assertRaises(BridgeUnavailableError):
                self.call(driver, legal=legal)
            self.assertEqual(driver.requests, [])

    def test_original_native_red_persists_bounded_id_fiveids_and_raw_error_without_replay(self):
        raw_error = "five distinct current final-legal candidates and same paused revision required"
        driver = Driver(self.directory, {"type": "command_result", "protocol_version": 1,
                                        "ok": False, "error": raw_error})
        with self.assertRaisesRegex(BridgeUnavailableError, raw_error) as caught:
            self.call(driver)
        self.assertEqual(len(driver.requests), 1)
        original_id = driver.requests[0]["request_id"]
        self.assertEqual(driver.wait_ids, [original_id])
        path = self.directory / "marriage-projection-query-failures" / (original_id + ".json")
        self.assertLessEqual(path.stat().st_size, 16384)
        evidence = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["native_request_id"], original_id)
        self.assertEqual(evidence["candidate_character_ids"], IDS)
        self.assertEqual(evidence["legality"]["query_sequence"], 7)
        self.assertEqual(evidence["before_frame"]["native_revision"], 3)
        self.assertEqual(evidence["raw_error"], raw_error)
        self.assertNotIn("command_history", path.read_text(encoding="utf-8"))
        self.assertTrue(any(str(path) in note for note in caught.exception.__notes__))

    def test_diagnostic_write_failure_keeps_original_native_error(self):
        blocked = self.directory / "blocked-state-dir"
        blocked.write_text("file blocks directory creation", encoding="utf-8")
        driver = Driver(blocked, {"ok": False, "error": "native ORIGINAL error"})
        with self.assertRaisesRegex(BridgeUnavailableError, "native ORIGINAL error") as caught:
            self.call(driver)
        self.assertEqual(len(driver.requests), 1)
        self.assertTrue(any("evidence write failed" in note for note in caught.exception.__notes__))

    def test_timeout_retains_same_original_id_single_send(self):
        driver = Driver(self.directory, None)
        with self.assertRaisesRegex(BridgeUnavailableError, "command_result timed out"):
            self.call(driver)
        self.assertEqual(len(driver.requests), 1)
        original_id = driver.requests[0]["request_id"]
        self.assertEqual(driver.wait_ids, [original_id])
        evidence = json.loads((self.directory / "marriage-projection-query-failures" / (original_id + ".json")).read_text(encoding="utf-8"))
        self.assertFalse(evidence["command_result_received"])
        self.assertFalse(evidence["native_query_resubmitted"])


