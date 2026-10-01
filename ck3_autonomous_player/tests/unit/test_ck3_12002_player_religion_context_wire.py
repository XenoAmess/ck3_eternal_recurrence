"""Consume actual new native religion-context output without querying a game."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.player_religion_context_private_transport import (
    normalize_player_religion_context_v1, query_player_religion_context_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_context"


def load_fixture(relative: str) -> dict[str, object]:
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def snapshot(*, revision: int, date_raw: int, actor: int) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}", "revision": revision + 1,
        "native_revision": revision, "date_raw": date_raw,
        "played_character": {"character_id": actor, "alive": True},
        "paused": True, "map_ready": True,
        "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        }},
    }


class MailboxPacketDriver:
    """Only correlate the generated request ID in an actual full native packet."""

    allow_private_player_religion_context_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_religion_context"]
        self.snapshot = snapshot(revision=result["snapshot_revision"],
                                 date_raw=result["date_raw"], actor=native["played_character_id"])
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        reply = deepcopy(self.frame)
        reply["request_id"] = request_id
        return reply


class PlayerReligion12002LibraryWireTest(unittest.TestCase):
    def test_five_actual_library_cases_preserve_full_ids_nulls_and_signed_resources(self) -> None:
        current = load_fixture("library/current-zero.json")
        before = snapshot(revision=40, date_raw=current["date_raw"], actor=current["played_character_id"])
        for case in ("current-zero", "signed-values", "legal-absent", "native-default", "faith-unavailable"):
            with self.subTest(case=case):
                native = load_fixture(f"library/{case}.json")
                actual = normalize_player_religion_context_v1(native, snapshot=deepcopy(before))
                self.assertEqual(actual, native)
                self.assertNotEqual(actual["capture_epoch"], before["native_revision"])
        zero = normalize_player_religion_context_v1(current, snapshot=before)
        self.assertEqual(zero["rite_id"], 0)
        self.assertGreater(zero["faith_id"], 0x7FFFFFFF)
        self.assertGreater(zero["religion_id"], 0x7FFFFFFF)
        self.assertNotEqual(zero["rite_id"], zero["faith_main_rite_id"])
        self.assertEqual(zero["faith_fervor_raw"], 0)
        self.assertEqual(zero["spiritual_fulfillment_raw"], 0)
        signed = load_fixture("library/signed-values.json")
        self.assertEqual(signed["faith_fervor_raw"], -123456)
        absent = load_fixture("library/legal-absent.json")
        self.assertTrue(absent["available"])
        self.assertIsNone(absent["rite_id"])
        self.assertIsNotNone(absent["spiritual_fulfillment_raw"])
        failed = load_fixture("library/faith-unavailable.json")
        self.assertFalse(failed["available"])
        self.assertEqual(failed["unavailable_reason"], "faith_unavailable")
        self.assertIsNone(failed["spiritual_fulfillment_raw"])


class PlayerReligion12002MailboxWireTest(unittest.TestCase):
    def test_six_actual_mailbox_packets_reach_the_existing_g2_query_transport(self) -> None:
        outputs = {}
        for case in ("current-zero", "signed-values", "native-default", "legal-absent",
                     "faith-unavailable", "fervor-unavailable"):
            with self.subTest(case=case):
                packet = load_fixture(f"mailbox/{case}.json")
                result = packet["result"]
                native = result["player_religion_context"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_context_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], result["status"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-player-religion-context-v1")
                self.assertEqual(request["protocol_version"], 1)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                outputs[case] = actual
        zero = outputs["current-zero"]
        self.assertEqual(zero["rite_id"], 0)
        self.assertGreater(zero["faith_id"], 0x7FFFFFFF)
        self.assertGreater(zero["religion_id"], 0x7FFFFFFF)
        self.assertEqual(zero["faith_key"], 'faith"信')
        self.assertEqual(zero["faith_fervor_raw"], 0)
        self.assertEqual(zero["spiritual_fulfillment_raw"], 0)
        self.assertEqual(outputs["signed-values"]["faith_fervor_raw"], -123456)
        self.assertTrue(outputs["legal-absent"]["available"])
        self.assertIsNone(outputs["legal-absent"]["faith_id"])
        for case, reason in (("faith-unavailable", "faith_unavailable"),
                             ("fervor-unavailable", "fervor_unavailable")):
            self.assertFalse(outputs[case]["available"])
            self.assertEqual(outputs[case]["status"], "unavailable")
            self.assertEqual(outputs[case]["unavailable_reason"], reason)
            self.assertIsNone(outputs[case]["faith_fervor_raw"])

    def test_private_query_is_disabled_before_sending_a_packet(self) -> None:
        driver = MailboxPacketDriver(load_fixture("mailbox/current-zero.json"))
        driver.allow_private_player_religion_context_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_context_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
