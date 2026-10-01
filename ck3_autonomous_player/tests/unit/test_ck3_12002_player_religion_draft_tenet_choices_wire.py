"""Actual full Tenet candidate packet through production ingest/wait/query."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_draft_tenet_choices_private_transport import (
    DOMAIN_KEY, STEP, query_player_religion_draft_tenet_choices_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_draft_tenet_choices"


class MailboxPacketDriver:
    """Replay the complete actual C++ packet; correlate only the request nonce."""

    allow_private_player_religion_draft_tenet_choices_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.frame = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_draft_tenet_choices"]
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
        self.state = NativeProtocolState("offline-fixture:religion-draft-tenet-choices")
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionDraftTenetChoicesWireTests(unittest.TestCase):
    def test_actual_multisource_packet_keeps_final_gates_and_native_raw_status(self) -> None:
        packet = json.loads((FIXTURES / "native-current-draft.json").read_text(encoding="utf-8"))
        result = packet["result"]
        native = result["player_religion_draft_tenet_choices"]
        driver = MailboxPacketDriver(packet)
        actual = query_player_religion_draft_tenet_choices_private_v1(
            driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
        )
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual["domain_key"], DOMAIN_KEY)
        self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
        self.assertEqual(actual["status"], result["status"])
        self.assertEqual(actual["query_date_raw"], result["date_raw"])
        self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
        self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
        self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertIs(actual["read_only"], True)
        self.assertIs(actual["advertised"], False)
        self.assertIs(actual["draft_observed"], True)
        self.assertIs(actual["tenet_gates_complete"], True)
        self.assertIs(actual["slots_share_source_predicate"], True)
        self.assertGreater(len(actual["sources"]), 1)
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        request = driver.sent[0]
        self.assertEqual(request["step"], STEP)
        self.assertEqual(request["expected_revision"], result["snapshot_revision"])
        self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
        self.assertNotIn("character_id", request)
        self.assertNotIn("slot", request)
        self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))


if __name__ == "__main__":
    unittest.main()
