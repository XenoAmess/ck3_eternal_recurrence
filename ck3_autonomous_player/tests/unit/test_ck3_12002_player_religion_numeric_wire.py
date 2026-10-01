"""Actual numeric cache/getter DTOs and combined native mailbox packets."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_numeric_special_parameters_private_transport import (
    STEP, normalize_faith_numeric_final_v1,
    normalize_player_religion_numeric_special_parameters_v1,
    query_player_religion_numeric_special_parameters_private_v1,
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((REPOSITORY / "research" / name).read_text(encoding="utf-8"))


def mailbox_cases() -> dict[str, object]:
    return load_fixture("religion_doctrine12002_numeric_mailbox_wire_fixtures.json")["cases"]


class NumericPacketDriver:
    """Correlate requests, ingest real full packets, use production cache wait."""

    allow_private_player_religion_numeric_special_parameters_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        primary = result["player_religion_numeric_special_parameters"]
        native_revision = result["snapshot_revision"]
        self.state = NativeProtocolState("offline-numeric-combined-packet-fixture")
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1, "capabilities": [],
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        })
        self.snapshot = {
            "snapshot_id": f"native:{native_revision}", "revision": native_revision + 1,
            "native_revision": native_revision, "date_raw": result["date_raw"],
            "played_character": {"character_id": primary["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": self.state.diagnostics()["hello"]},
        }
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        self.ingested_frame_types: list[str] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        reply = deepcopy(self.frame)
        reply["request_id"] = request["request_id"]
        self.ingested_frame_types.append(self.state.ingest(reply))


class PlayerReligionNumeric12002WireTest(unittest.TestCase):
    def test_actual_provider_dtos_keep_cache_and_final_states_separate(self) -> None:
        before = NumericPacketDriver(mailbox_cases()["current-versus-main"]["command_result"]).snapshot
        primary = load_fixture("religion_doctrine12002_numeric_wire_fixtures.json")
        for name, case in primary["cases"].items():
            with self.subTest(primary=name):
                native = case["numeric_special_parameters"]
                self.assertEqual(normalize_player_religion_numeric_special_parameters_v1(native, snapshot=before), native)
        final = load_fixture("religion_doctrine12002_numeric_final_wire_fixtures.json")
        for name, case in final["cases"].items():
            with self.subTest(final=name):
                native = case["faith_numeric_final"]
                self.assertEqual(normalize_faith_numeric_final_v1(native, snapshot=before), native)

    def test_six_actual_combined_packets_reach_real_protocol_cache_and_query(self) -> None:
        outputs = {}
        for name, case in mailbox_cases().items():
            with self.subTest(case=name):
                packet = case["command_result"]
                driver = NumericPacketDriver(packet)
                actual = query_player_religion_numeric_special_parameters_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                primary = packet["result"]["player_religion_numeric_special_parameters"]
                self.assertEqual({key: actual[key] for key in primary}, primary)
                self.assertEqual(actual["faith_numeric_final"], packet["result"]["faith_numeric_final"])
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["snapshot_revision"], packet["result"]["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(driver.ingested_frame_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], actual["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], actual["snapshot_revision"])
                self.assertNotIn("actor_character_id", request)
                self.assertNotIn("target_rite_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[name] = actual
        current = outputs["current-versus-main"]
        self.assertEqual(current["current_rite"]["rite_id"], 0)
        self.assertGreater(current["faith_id"], 0x7FFFFFFF)
        self.assertNotEqual(current["current_rite"]["rite_id"], current["faith_main_rite"]["rite_id"])
        self.assertEqual(current["current_rite"]["parameters"][4]["raw"], -500000)
        self.assertEqual(current["faith_main_rite"]["parameters"][4]["raw"], 500000)
        self.assertEqual(current["faith_numeric_final"]["final_heresy_threshold_raw"], 3000000)
        self.assertEqual(current["faith_numeric_final"]["final_heresy_threshold"], 30.0)
        self.assertEqual(current["current_rite"]["parameters"][1]["value"], 0.05)
        self.assertFalse(current["authored_presence_provenance_observed"])
        zero = outputs["known-zero-final"]
        self.assertEqual(zero["faith_numeric_final"]["value_state"], "value")
        self.assertEqual(zero["faith_numeric_final"]["final_heresy_threshold_raw"], 0)
        self.assertIsInstance(zero["faith_numeric_final"]["final_heresy_threshold"], float)
        self.assertEqual(zero["faith_numeric_final"]["final_heresy_threshold"], 0.0)
        unset = outputs["minimum-unset"]["current_rite"]["parameters"][0]
        self.assertEqual((unset["raw"], unset["state"], unset["value"]), (-1, "unset", None))
        for name, state in (("legal-absent-faith", "legal_absent_faith"),
                            ("legal-absent-main-rite", "legal_absent_main_rite")):
            final = outputs[name]["faith_numeric_final"]
            self.assertTrue(final["available"])
            self.assertEqual(final["value_state"], state)
            self.assertIsNone(final["final_heresy_threshold_raw"])
            self.assertIsNone(final["final_heresy_threshold"])
        failed = outputs["native-threshold-unavailable"]
        self.assertTrue(failed["available"])
        self.assertEqual(failed["status"], "observed")
        self.assertFalse(failed["faith_numeric_final"]["available"])
        self.assertEqual(failed["faith_numeric_final"]["unavailable_reason"], "native_threshold_unavailable")
        self.assertIsNone(failed["faith_numeric_final"]["final_heresy_threshold"])

    def test_default_off_query_sends_nothing(self) -> None:
        driver = NumericPacketDriver(mailbox_cases()["current-versus-main"]["command_result"])
        driver.allow_private_player_religion_numeric_special_parameters_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_numeric_special_parameters_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
