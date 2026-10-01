"""Actual full-Doctrine caller packet through production ingest/wait/query."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_draft_doctrine_choices_private_transport import (
    DOMAIN_KEY, STEP, query_player_religion_draft_doctrine_choices_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_draft_doctrine_choices"


def actual_packet(case: str = "visible-four-slots") -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """Replay the actual complete packet; correlate only its request nonce."""

    allow_private_player_religion_draft_doctrine_choices_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.frame = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_draft_doctrine_choices"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:religion-draft-doctrine-choices")
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionDraftDoctrineChoicesWireTests(unittest.TestCase):
    def test_actual_all_slot_final_choices_keep_short_circuit_nulls(self) -> None:
        packet = actual_packet()
        result = packet["result"]
        native = result["player_religion_draft_doctrine_choices"]
        driver = MailboxPacketDriver(packet)
        actual = query_player_religion_draft_doctrine_choices_private_v1(
            driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
        )
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual["domain_key"], DOMAIN_KEY)
        self.assertEqual(actual["backend_id"], result["backend_id"])
        self.assertEqual(actual["snapshot_revision"], 701)
        self.assertEqual(actual["queried_revision"], 702)
        self.assertEqual(actual["queried_native_revision"], 701)
        self.assertEqual(actual["query_date_raw"], 53175816)
        self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertIs(actual["read_only"], True)
        self.assertIs(actual["advertised"], False)
        self.assertIs(actual["draft_observed"], True)
        self.assertIs(actual["doctrine_gates_complete"], True)
        self.assertEqual([len(slot["sources"]) for slot in actual["slots"]], [6, 6, 3, 0])
        rows = [row for slot in actual["slots"] for row in slot["sources"]]
        self.assertEqual(sum(row["final_selectable"] for row in rows), 5)
        first = actual["slots"][0]["sources"]
        self.assertIs(first[0]["currently_selected"], True)
        self.assertIs(first[0]["final_selectable"], True)
        self.assertIs(first[1]["duplicate_excluded"], True)
        self.assertIsNone(first[1]["passed_shown"])
        self.assertIsNone(first[1]["native_can_pick"])
        self.assertIsNone(first[1]["native_knows_doctrine"])
        self.assertIsNone(first[1]["native_has_prophet"])
        self.assertIs(first[1]["final_selectable"], False)
        self.assertIs(first[2]["passed_shown"], False)
        self.assertIs(first[2]["native_can_pick"], False)
        self.assertIsNone(first[2]["native_knows_doctrine"])
        self.assertIs(first[3]["native_can_pick"], False)
        self.assertIs(first[4]["native_knows_doctrine"], False)
        self.assertIs(first[4]["native_has_prophet"], False)
        self.assertIs(first[4]["final_selectable"], False)
        self.assertIs(first[5]["native_knows_doctrine"], True)
        self.assertIsNone(first[5]["native_has_prophet"])
        self.assertIs(first[5]["final_selectable"], True)
        self.assertEqual(actual["slots"][3]["sources"], [])
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        request = driver.sent[0]
        self.assertEqual(request["step"], STEP)
        self.assertEqual(request["expected_revision"], 701)
        self.assertEqual(request["expected_snapshot_revision"], 701)
        self.assertNotIn("character_id", request)
        self.assertNotIn("slot", request)
        self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))


if __name__ == "__main__":
    unittest.main()
