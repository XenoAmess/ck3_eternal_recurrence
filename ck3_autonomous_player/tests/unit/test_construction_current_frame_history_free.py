"""Cash and wartime observation read only current frames, never the transcript."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer.bridge import war_cash_private_transport_v1 as cash
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as construction
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError

FIXTURE = json.loads((ROOT / "tests/fixtures/construction_cash_current_12004.json").read_text(encoding="utf-8"))
PACKET, SOURCE = FIXTURE["packet"], FIXTURE["planning_source_frame"]


class CurrentFrameDriver:
    allow_private_war_cash_query = True

    def __init__(self):
        self.frame = {key: SOURCE[key] for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
        self.frame.update(
            paused=True, map_ready=True, played_character={"character_id": 31254, "alive": True},
            active_event=None, pending_character_interaction=None, active_wars=[], player_armies=[],
            diagnostics={"hello": {"expected_ck3_version": PACKET["game_version"],
                                   "expected_ck3_sha256": PACKET["executable_sha256"]}})
        self.endpoint = self.state = self
        self.requests, self.finite_reads, self.waits = [], 0, 0
        self.after_change = {}

    def take_snapshot(self):
        raise AssertionError("This current-state query does not consume full history")

    def take_snapshot_without_native_command_history(self):
        self.finite_reads += 1
        result = deepcopy(self.frame)
        if self.waits:
            result.update(self.after_change)
        return result

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        self.waits += 1
        return {"type": "command_result", "protocol_version": 1, "request_id": request_id,
                "ok": True, "result": {"step": cash.CURRENT_STEP, "accepted": True,
                "private_build": True, "read_only": True, "advertised": False,
                "war_cash_current_resources": deepcopy(PACKET)}}


class ConstructionCurrentFrameTests(unittest.TestCase):
    def query(self, driver):
        return cash.query_war_cash_current_resources_private_v1(
            driver, expected_revision=SOURCE["revision"])

    def test_actual_cash_packet_round_trip_detached_with_one_query_two_current_reads(self):
        driver = CurrentFrameDriver()
        result = self.query(driver)
        self.assertEqual(result, PACKET)
        self.assertEqual((driver.finite_reads, driver.waits, len(driver.requests)), (2, 1, 1))
        self.assertEqual(driver.requests[0]["expected_revision"], SOURCE["native_revision"])
        self.assertEqual(driver.requests[0]["expected_snapshot_revision"], SOURCE["native_revision"])
        result["current_treasury"]["raw"] += 1
        self.assertNotEqual(result["current_treasury"], PACKET["current_treasury"])

    def test_every_existing_after_frame_guard_still_rejects(self):
        for key, value in (
            ("snapshot_id", "native:737"), ("revision", 635), ("native_revision", 737),
            ("date_raw", SOURCE["date_raw"] + 24), ("paused", False), ("map_ready", False),
            ("played_character", {"character_id": 31255, "alive": True}),
            ("played_character", {"character_id": 31254, "alive": False}),
            ("active_event", {"instance_id": 1}), ("pending_character_interaction", {"id": 1})):
            with self.subTest(key=key, value=value):
                driver = CurrentFrameDriver()
                driver.after_change = {key: value}
                with self.assertRaises(BridgeUnavailableError):
                    self.query(driver)
                self.assertEqual(len(driver.requests), 1)

    def test_disabled_permission_and_stale_before_frame_send_nothing(self):
        driver = CurrentFrameDriver()
        driver.allow_private_war_cash_query = False
        with self.assertRaises(UnsupportedStepError):
            self.query(driver)
        self.assertEqual((driver.finite_reads, len(driver.requests)), (0, 0))
        driver = CurrentFrameDriver()
        driver.frame["revision"] += 1
        with self.assertRaises(BridgeUnavailableError):
            self.query(driver)
        self.assertFalse(driver.requests)

    def test_legacy_driver_missing_finite_method_keeps_fallback(self):
        class Legacy(CurrentFrameDriver):
            take_snapshot_without_native_command_history = None

            def take_snapshot(self):
                return CurrentFrameDriver.take_snapshot_without_native_command_history(self)

        driver = Legacy()
        self.assertEqual(self.query(driver), PACKET)
        self.assertEqual(driver.finite_reads, 2)

    def wartime(self, change=None):
        driver = CurrentFrameDriver()
        driver.frame.update(active_wars=[{"war_id": 71}], player_armies=[{"army_id": 1}],
                            played_character_gold=deepcopy(PACKET["current_treasury"]))
        source = {"status": "no_legal_budgeted_building",
                  "world": {"player_gold_raw": PACKET["current_treasury"]["raw"],
                            "positive_income_coverage_complete": True},
                  "source_frame": deepcopy(SOURCE), "native_query_request_id": "offline-only",
                  "proof_epoch": 99}
        if change:
            source["source_frame"].update(change)
        with patch.object(construction, "query_construction_private", return_value=source) as reader:
            result = construction.query_construction_wartime_observation_private(
                driver, expected_revision=SOURCE["revision"], include_world=True)
        self.assertEqual(reader.call_count, 1)
        self.assertEqual(driver.finite_reads, 1)
        self.assertFalse(driver.requests)
        return result

    def test_wartime_current_frame_projection_preserves_unassessed_spend(self):
        result = self.wartime()
        self.assertEqual(result["status"], "observed")
        self.assertEqual((result["observed_active_war_count"], result["observed_player_army_count"]), (1, 1))
        self.assertFalse(result["formal_action_ready"])
        self.assertIsNone(result["war_future_gold_cost_raw"])
        self.assertEqual(result["joint_budget_affordability"], "unassessed")

    def test_wartime_stale_source_still_red(self):
        result = self.wartime({"native_revision": SOURCE["native_revision"] + 1})
        self.assertEqual(result["status"], "source_red")
        self.assertEqual(result["reason"], "same_frame_binding_mismatch")
        self.assertFalse(result["formal_action_ready"])


if __name__ == "__main__":
    unittest.main()
