"""Actual C++ doctrine knowledge packets through the production query transport."""

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
from xar_autoplayer.bridge.player_religion_doctrine_knowledge_private_transport import (
    STEP, normalize_player_religion_doctrine_knowledge_v1,
    query_player_religion_doctrine_knowledge_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURE = ROOT.parent / "research/religion_doctrine12002_choices_mailbox_wire_fixtures.json"


def load_fixture(case: str) -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["packets"][case]


class MailboxPacketDriver:
    """Use actual NativeProtocolState ingestion/wait, with an in-memory endpoint."""

    allow_private_player_religion_doctrine_knowledge_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_religion_doctrine_knowledge"]
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
        self.state = NativeProtocolState("offline-doctrine-knowledge-fixture")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        reply = deepcopy(self.frame)
        # Only request correlation changes; DTO/envelope come from actual C++.
        reply["request_id"] = request["request_id"]
        self.state.ingest(reply)


class PlayerDoctrineKnowledge12002WireTest(unittest.TestCase):
    def test_six_actual_dtos_preserve_native_knowledge_absence_and_failure(self) -> None:
        for case in ("learned-current.json", "lookup-known.json", "lookup-not-known.json",
                     "lookup-absent.json", "lookup-registry-unavailable.json", "learned-empty.json"):
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_doctrine_knowledge"]
                driver = MailboxPacketDriver(packet)
                normalized = normalize_player_religion_doctrine_knowledge_v1(native, snapshot=driver.snapshot)
                self.assertEqual(normalized, native)
                self.assertNotEqual(normalized["capture_epoch"], driver.snapshot["native_revision"])
        learned = load_fixture("learned-current.json")["result"]["player_religion_doctrine_knowledge"]
        self.assertGreater(learned["rite_id"], 0x7FFFFFFF)
        self.assertEqual(learned["knowledge_source"], "character_extension")
        self.assertEqual(learned["learned_rows"][1]["doctrine_key"], 'doc"信')

    def test_six_actual_full_packets_ingest_and_wait_through_production_protocol_state(self) -> None:
        outputs = {}
        for case in ("learned-current.json", "lookup-known.json", "lookup-not-known.json",
                     "lookup-absent.json", "lookup-registry-unavailable.json", "learned-empty.json"):
            with self.subTest(case=case):
                packet = load_fixture(case)
                result = packet["result"]
                native = result["player_religion_doctrine_knowledge"]
                driver = MailboxPacketDriver(packet)
                key = native.get("requested_doctrine_key")
                actual = query_player_religion_doctrine_knowledge_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], doctrine_key=key,
                )
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(actual["query_mode"], result["query_mode"])
                self.assertEqual(actual["status"], result["status"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["protocol_version"], 1)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                if key is None:
                    self.assertNotIn("doctrine_key", request)
                else:
                    self.assertEqual(request["doctrine_key"], key)
                outputs[case] = actual
        self.assertIs(outputs["lookup-known.json"]["native_knows_doctrine"], True)
        self.assertIs(outputs["lookup-not-known.json"]["native_knows_doctrine"], False)
        self.assertTrue(outputs["lookup-not-known.json"]["definition_found"])
        absent = outputs["lookup-absent.json"]
        self.assertTrue(absent["available"])
        self.assertFalse(absent["definition_found"])
        self.assertIsNone(absent["definition"])
        self.assertIsNone(absent["native_knows_doctrine"])
        failed = outputs["lookup-registry-unavailable.json"]
        self.assertFalse(failed["available"])
        self.assertEqual(failed["status"], "unavailable")
        self.assertEqual(failed["unavailable_reason"], "definition_registry_unavailable")
        self.assertIsNone(failed["native_knows_doctrine"])
        self.assertTrue(outputs["learned-empty.json"]["available"])
        self.assertEqual(outputs["learned-empty.json"]["learned_rows"], [])

    def test_disabled_query_and_invalid_key_send_nothing(self) -> None:
        driver = MailboxPacketDriver(load_fixture("learned-current.json"))
        driver.allow_private_player_religion_doctrine_knowledge_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_doctrine_knowledge_private_v1(
                driver, expected_revision=driver.snapshot["revision"],
            )
        driver.allow_private_player_religion_doctrine_knowledge_query = True
        for key in ("", 0, False):
            with self.subTest(key=key), self.assertRaises(ValueError):
                query_player_religion_doctrine_knowledge_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], doctrine_key=key,
                )
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
