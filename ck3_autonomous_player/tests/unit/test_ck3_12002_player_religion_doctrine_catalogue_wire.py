"""Consume the actual loaded Catalogue full C++ packets without querying CK3."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_doctrine_catalogue_private_transport import (
    STEP, normalize_player_religion_doctrine_catalogue_v1,
    query_player_religion_doctrine_catalogue_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT.parent / "research/religion_doctrine12002_catalogue_packets"


def load_fixture(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """Feed actual full packets into production protocol ingestion and wait."""

    allow_private_player_religion_doctrine_catalogue_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_religion_doctrine_catalogue"]
        revision = result["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": f"native:{revision}", "revision": revision + 1,
            "native_revision": revision, "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = NativeProtocolState("offline-doctrine-catalogue-fixture")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        reply = deepcopy(self.frame)
        # Request correlation is the only changed field in actual C++ output.
        reply["request_id"] = request["request_id"]
        self.state.ingest(reply)


class PlayerDoctrineCatalogue12002WireTest(unittest.TestCase):
    def test_three_actual_dtos_keep_loaded_keys_empty_catalogue_and_failure(self) -> None:
        for case in ("loaded-catalogue", "known-empty", "database-unavailable"):
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_doctrine_catalogue"]
                driver = MailboxPacketDriver(packet)
                normalized = normalize_player_religion_doctrine_catalogue_v1(native, snapshot=driver.snapshot)
                self.assertEqual(normalized, native)
                self.assertNotEqual(normalized["capture_epoch"], driver.snapshot["native_revision"])
        loaded = load_fixture("loaded-catalogue")["result"]["player_religion_doctrine_catalogue"]
        self.assertTrue(loaded["catalogue_complete"])
        self.assertEqual(loaded["rows"][2]["doctrine_key"], 'mod_custom_doctrine"信')
        self.assertEqual(loaded["rows"][2]["group_key"], "group_a")
        self.assertEqual(loaded["rows"][2]["source"], "loaded_doctrine_registry")

    def test_three_actual_full_packets_ingest_then_wait_through_the_existing_transport(self) -> None:
        outputs = {}
        for case in ("loaded-catalogue", "known-empty", "database-unavailable"):
            with self.subTest(case=case):
                packet = load_fixture(case)
                result = packet["result"]
                native = result["player_religion_doctrine_catalogue"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_doctrine_catalogue_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(actual["status"], result["status"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["protocol_version"], 1)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                self.assertNotIn("target_id", request)
                self.assertNotIn("doctrine_key", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[case] = actual
        empty = outputs["known-empty"]
        self.assertTrue(empty["available"])
        self.assertTrue(empty["catalogue_complete"])
        self.assertEqual(empty["status"], "observed")
        self.assertEqual(empty["rows"], [])
        failed = outputs["database-unavailable"]
        self.assertFalse(failed["available"])
        self.assertFalse(failed["catalogue_complete"])
        self.assertEqual(failed["status"], "unavailable")
        self.assertEqual(failed["unavailable_reason"], "doctrine_database_unavailable")
        self.assertEqual(failed["rows"], [])

    def test_disabled_query_sends_nothing(self) -> None:
        driver = MailboxPacketDriver(load_fixture("loaded-catalogue"))
        driver.allow_private_player_religion_doctrine_catalogue_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_doctrine_catalogue_private_v1(
                driver, expected_revision=driver.snapshot["revision"],
            )
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
