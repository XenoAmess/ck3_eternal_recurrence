"""Actual owned native doctrine providers and complete mailbox packets."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.player_religion_doctrines_private_transport import (
    STEP, normalize_player_religion_doctrines_v1,
    query_player_religion_doctrines_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_doctrines"


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
    """Only echo the request ID in the otherwise unchanged full native frame."""

    allow_private_player_religion_doctrines_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        actor = load_fixture("mailbox/current-scopes.json")["result"]["player_religion_doctrines"]["played_character_id"]
        self.snapshot = snapshot(revision=result["snapshot_revision"],
                                 date_raw=result["date_raw"], actor=actor)
        self.sent: list[dict[str, object]] = []
        self.endpoint = self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        reply = deepcopy(self.frame)
        reply["request_id"] = request_id
        return reply


class PlayerReligionDoctrines12002WireTest(unittest.TestCase):
    def test_actual_cross_provider_dto_keeps_scope_keys_complete_empty_bags_and_typed_failure(self) -> None:
        current = load_fixture("library/current-scopes.json")
        before = snapshot(revision=40, date_raw=current["date_raw"], actor=current["played_character_id"])
        for case in ("current-scopes", "known-empty", "parameter-unavailable"):
            with self.subTest(case=case):
                native = load_fixture(f"library/{case}.json")
                self.assertEqual(normalize_player_religion_doctrines_v1(native, snapshot=before), native)
        self.assertGreater(current["current_rite"]["rite_id"], 0x7FFFFFFF)
        self.assertGreater(current["current_rite"]["faith_id"], 0x7FFFFFFF)
        self.assertNotEqual(current["current_rite"]["rite_id"], current["faith_main_rite"]["main_rite_id"])
        self.assertEqual(current["current_rite"]["rows"][0]["doctrine_key"], 'doctrine_actor"礼')
        self.assertEqual(current["current_rite"]["rows"][0]["source"], "rite_effective")
        self.assertEqual(current["faith_main_rite"]["rows"][0]["source"], "faith_main_rite")
        self.assertEqual(current["boolean_parameters"]["current_rite"]["parameters"],
                         [{"key": "actor_rule", "value": True}])
        self.assertEqual(current["boolean_parameters"]["faith_main_rite"]["parameters"],
                         [{"key": "main_rule", "value": True}])
        empty = load_fixture("library/known-empty.json")
        self.assertTrue(empty["available"])
        self.assertEqual(empty["current_rite"]["rows"], [])
        self.assertEqual(empty["faith_main_rite"]["rows"], [])
        for scope in ("current_rite", "faith_main_rite"):
            self.assertTrue(empty["boolean_parameters"][scope]["boolean_parameters_complete"])
            self.assertEqual(empty["boolean_parameters"][scope]["parameters"], [])
        failed = load_fixture("library/parameter-unavailable.json")
        self.assertFalse(failed["available"])
        self.assertEqual(failed["unavailable_reason"], "boolean_parameters:parameter_key_unavailable")
        self.assertIsNone(failed["boolean_parameters"]["current_rite"])

    def test_actual_full_mailbox_packets_pass_existing_readonly_query_transport(self) -> None:
        outputs = {}
        for case in ("current-scopes", "legal-zero-rite", "known-empty", "parameter-unavailable"):
            with self.subTest(case=case):
                packet = load_fixture(f"mailbox/{case}.json")
                native = packet["result"]["player_religion_doctrines"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_doctrines_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["snapshot_revision"], packet["result"]["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(len(driver.sent), 1)
                self.assertEqual(driver.sent[0]["step"], STEP)
                self.assertEqual(driver.sent[0]["expected_revision"], actual["snapshot_revision"])
                self.assertEqual(driver.sent[0]["expected_snapshot_revision"], actual["snapshot_revision"])
                self.assertNotIn("character_id", driver.sent[0])
                outputs[case] = actual
        self.assertEqual(outputs["legal-zero-rite"]["current_rite"]["rite_id"], 0)
        self.assertEqual(outputs["legal-zero-rite"]["boolean_parameters"]["current_rite"]["rite_id"], 0)
        self.assertTrue(outputs["known-empty"]["available"])
        self.assertEqual(outputs["known-empty"]["boolean_parameters"]["current_rite"]["parameters"], [])
        self.assertFalse(outputs["parameter-unavailable"]["available"])
        self.assertEqual(outputs["parameter-unavailable"]["unavailable_reason"],
                         "boolean_parameters:parameter_key_unavailable")

    def test_disabled_query_sends_nothing(self) -> None:
        driver = MailboxPacketDriver(load_fixture("mailbox/current-scopes.json"))
        driver.allow_private_player_religion_doctrines_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_doctrines_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
