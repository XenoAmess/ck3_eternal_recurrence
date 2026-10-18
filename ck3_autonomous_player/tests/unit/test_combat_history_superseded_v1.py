"""Production query/record/persist paths with in-memory native endpoints."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer.bridge import combat_history_superseded_v1 as history_projection
from xar_autoplayer.bridge import native_driver, service


def _fixture_module(version, filename):
    spec = importlib.util.spec_from_file_location(
        f"combat_history_existing_fixture_{version}", Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIXTURES = {
    2: _fixture_module(2, "test_combat_simulation_inputs_bridge.py"),
    3: _fixture_module(3, "test_combat_phase_inputs_v3_bridge.py"),
}


class CombatHistoryProductionTests(unittest.TestCase):
    def setUp(self):
        self.drivers = []
        self.temps = []

    def tearDown(self):
        for driver in self.drivers:
            driver.close()
        for temp in self.temps:
            temp.cleanup()

    def driver(self, version=2, *, persist=False):
        fixture = FIXTURES[version]
        driver, endpoint = fixture._native_driver()
        self.drivers.append(driver)
        driver._test_version = version
        driver._test_endpoint = endpoint
        driver._test_sequence = 0
        driver._test_revision = 5
        driver._test_transform = None
        driver._test_cross_frame = False
        if persist:
            temp = tempfile.TemporaryDirectory(prefix="combat-history-unit-")
            self.temps.append(temp)
            driver.state_dir = Path(temp.name)

        def answer(request):
            if request.get("type") != "execute_step":
                return
            driver._test_sequence += 1
            result = deepcopy(fixture._fixture_result())
            result.update(step=request["step"], query_sequence=driver._test_sequence)
            if driver._test_transform is not None:
                driver._test_transform(result)
            if driver._test_cross_frame:
                self.advance(driver)
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": True,
                              "result": result})

        endpoint.send_hook = answer
        return driver

    def advance(self, driver):
        driver._test_revision += 1
        fixture = FIXTURES[driver._test_version]
        frame = (fixture._snapshot(driver._test_revision) if driver._test_version == 2
                 else fixture._semantic_snapshot(driver._test_revision))
        frame["state"]["date_raw"] += (driver._test_revision - 5) * 24
        driver._test_endpoint.publish(frame)

    def query(self, driver, *, service_api=False):
        raw = FIXTURES[driver._test_version]._fixture_result()
        revision = driver.take_snapshot_without_native_command_history()["revision"]
        if service_api:
            app = service.GameplayBridgeService(driver)
            call = (app.query_combat_simulation_inputs if driver._test_version == 2
                    else app.query_combat_simulation_inputs_v3)
            return call(*history_projection._parsed(raw["step"])[1], expected_revision=revision)
        return driver.execute_step(raw["step"], expected_revision=revision)

    def body(self, row):
        return row["result"]["combat_simulation_inputs"]

    def test_new_available_query_preserves_api_cache_latest_and_all_row_metadata(self):
        for version in (2, 3):
            with self.subTest(version=version):
                driver = self.driver(version)
                first = self.query(driver)
                old = driver._history_snapshot()[0]
                self.advance(driver)
                second = self.query(driver, service_api=True)
                history = driver._history_snapshot()
                self.assertEqual([row["index"] for row in history], [1, 2])
                summary = self.body(history[0])
                self.assertEqual(summary["schema"], history_projection.SUMMARY_SCHEMA)
                encoded = json.dumps(first["combat_simulation_inputs"], ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                self.assertEqual(summary["canonical_sha256"], hashlib.sha256(encoded).hexdigest())
                self.assertEqual(summary["canonical_json_bytes"], len(encoded))
                self.assertFalse(summary["full_body_reconstructible_from_summary"])
                self.assertFalse(summary["original_raw_MCP_receipt"]["exact_path_known"])
                old["result"]["combat_simulation_inputs"] = summary
                self.assertEqual(history[0], old)
                self.assertEqual(self.body(history[-1]), second["combat_simulation_inputs"])
                cache = getattr(driver, "_combat_simulation_inputs_query" if version == 2
                                else "_combat_simulation_inputs_v3_query")
                self.assertEqual(cache["combat_simulation_inputs"], second["combat_simulation_inputs"])
                self.assertNotEqual(second["queried_revision"], second["queried_native_revision"])
                # The API's earlier result is independent of its recorded copy.
                self.assertNotEqual(first["combat_simulation_inputs"].get("schema"),
                                    history_projection.SUMMARY_SCHEMA)

    def test_partial_unavailable_malformed_or_crossed_frame_keeps_old_full(self):
        for version, kind in ((2, "partial"), (3, "unavailable"),
                              (2, "malformed"), (3, "crossframe")):
            with self.subTest(version=version, kind=kind):
                driver = self.driver(version)
                first = self.query(driver)
                self.advance(driver)
                if kind == "partial":
                    driver._test_transform = lambda result: result.update(
                        FIXTURES[2]._partial_fixture_result(), query_sequence=driver._test_sequence)
                elif kind == "unavailable":
                    driver._test_transform = lambda result: result.update(
                        FIXTURES[3]._fixture_result(available=False), query_sequence=driver._test_sequence)
                elif kind == "malformed":
                    driver._test_transform = lambda result: result["combat_simulation_inputs"].update(
                        target_province_id=999)
                else:
                    driver._test_cross_frame = True
                if kind in ("malformed", "crossframe"):
                    with self.assertRaises(native_driver.BridgeUnavailableError):
                        self.query(driver)
                else:
                    self.query(driver)
                self.assertEqual(self.body(driver._history_snapshot()[0]),
                                 first["combat_simulation_inputs"])

    def test_same_frame_other_version_battle_control_and_error_rows_stay_complete(self):
        driver = self.driver()
        first = self.query(driver)
        self.query(driver)
        self.assertEqual(self.body(driver._history_snapshot()[0]), first["combat_simulation_inputs"])
        v3 = FIXTURES[3]._fixture_result()
        v3.update(backend_id="native-headless", queried_snapshot_id="old-v3:1",
                  queried_revision=1, queried_native_revision=1)
        driver._record_command(v3["step"], ok=True, result=v3)
        battle = {"battle_control_snapshot_v1": {"combat_id": 99, "events": [{"full": "kept"}]},
                  "query_sequence": 77}
        driver._record_command("query-battle-control-snapshot-v1-99", ok=True, result=battle)
        driver._record_command(first["step"], ok=False, result={"full_error": "kept"},
                               error="fixture rejection")
        before = driver._history_snapshot()
        self.advance(driver)
        self.query(driver)
        self.assertEqual(driver._history_snapshot()[2:5], before[2:5])

    def test_query_does_not_clone_history_and_digest_failure_keeps_accepted_result(self):
        driver = self.driver()
        self.query(driver)
        self.advance(driver)
        with mock.patch.object(driver, "_history_snapshot", side_effect=AssertionError("history cloned")):
            second = self.query(driver)
        self.assertIn("armies", second["combat_simulation_inputs"])
        self.assertEqual(len(driver.take_snapshot()["native_command_history"]), 2)
        summary = deepcopy(self.body(driver._history_snapshot()[0]))
        self.advance(driver)
        with mock.patch.object(history_projection, "_digest", side_effect=ValueError("fixture cap")):
            third = self.query(driver)
        self.assertIn("armies", third["combat_simulation_inputs"])
        history = driver._history_snapshot()
        self.assertEqual(self.body(history[0]), summary)
        self.assertEqual(self.body(history[1]), second["combat_simulation_inputs"])
        self.assertEqual(driver._combat_history_superseded_v1_last["status"], "full_history_retained")

    def test_real_cached_encoder_persist_and_restore_preserve_positions(self):
        driver = self.driver(persist=True)
        self.query(driver)
        with driver._driver_state_lock:
            initial = json.loads(driver._encode_driver_state_locked())
        self.assertIn("armies", self.body(initial["command_history"][0]))
        self.advance(driver)
        self.query(driver)
        expected = driver._history_snapshot()
        with driver._driver_state_lock:
            encoded = json.loads(driver._encode_driver_state_locked())
        self.assertEqual(encoded["command_history"], expected)
        self.assertEqual(self.body(encoded["command_history"][0])["schema"],
                         history_projection.SUMMARY_SCHEMA)
        self.assertIsNone(driver._persist_driver_state())
        restored = native_driver.load_native_driver_state_for_resume(
            driver._native_driver_state_path(), driver.pipe_name)
        self.assertEqual(restored["command_history"], expected)

    def test_already_summarized_rows_are_noop(self):
        driver = self.driver()
        self.query(driver)
        self.advance(driver)
        self.query(driver)
        summary = deepcopy(driver._history_snapshot()[0])
        self.advance(driver)
        self.query(driver)
        self.assertEqual(driver._history_snapshot()[0], summary)
        self.assertEqual([row["index"] for row in driver._history_snapshot()], [1, 2, 3])

    def test_missing_published_cache_cannot_compact_by_history_result_alone(self):
        driver = self.driver()
        first = self.query(driver)
        self.advance(driver)
        original = driver._record_command

        def record_then_invalidate(*args, **kwargs):
            result = original(*args, **kwargs)
            driver._combat_simulation_inputs_query = None
            return result

        with mock.patch.object(driver, "_record_command", side_effect=record_then_invalidate):
            second = self.query(driver)
        self.assertIn("armies", second["combat_simulation_inputs"])
        self.assertEqual(self.body(driver._history_snapshot()[0]), first["combat_simulation_inputs"])


if __name__ == "__main__":
    unittest.main()
