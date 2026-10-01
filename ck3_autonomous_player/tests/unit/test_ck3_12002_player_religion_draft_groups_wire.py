"""Actual new draft-group caller packets through production ingest/wait/query."""

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
from xar_autoplayer.bridge.player_religion_draft_groups_private_transport import (
    DOMAIN_KEY, STEP, query_player_religion_draft_groups_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_draft_groups"
CASES = ("visible-multi-slots", "absent-window", "hidden-window", "known-empty")


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """Replay the actual full packet; edit only its in-memory request nonce."""

    allow_private_player_religion_draft_groups_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.frame = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_draft_groups"]
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
        self.state = NativeProtocolState("offline-fixture:religion-draft-groups")
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionDraftGroupsWireTests(unittest.TestCase):
    def test_four_actual_packets_keep_sources_current_final_gates_and_scope_absence(self) -> None:
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                result = packet["result"]
                native = result["player_religion_draft_groups"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_draft_groups_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["domain_key"], DOMAIN_KEY)
                self.assertEqual(actual["status"], result["status"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                self.assertNotIn("slot", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                outputs[case] = actual

        visible = outputs["visible-multi-slots"]
        self.assertIs(visible["draft_observed"], True)
        self.assertIs(visible["category_materialized"], True)
        self.assertEqual(visible["founder_character_id"], visible["played_character_id"])
        self.assertEqual(len(visible["selected_slots"]), 2)
        self.assertEqual([len(row["group_source_definition_keys"]) for row in visible["selected_slots"]],
                         [2, 2])
        self.assertIs(visible["all_group_materialized_choices_complete"], False)
        self.assertIs(visible["current_tenet_gate_complete"], True)
        self.assertIs(visible["current_tenet_choices"][0]["final_can_pick"], True)
        for case in ("absent-window", "hidden-window", "known-empty"):
            actual = outputs[case]
            self.assertIs(actual["available"], True)
            self.assertIs(actual["category_materialized"], False)
            self.assertIs(actual["current_tenet_gate_complete"], False)
            self.assertIs(actual["all_group_materialized_choices_complete"], False)
            self.assertEqual(actual["current_category_slot"], -1)
            self.assertEqual(actual["selected_slots"], [])
            self.assertEqual(actual["current_tenet_choices"], [])
        self.assertIs(outputs["absent-window"]["draft_observed"], False)
        self.assertIs(outputs["hidden-window"]["draft_observed"], False)
        self.assertIsNone(outputs["absent-window"]["source_rite_id"])
        self.assertIs(outputs["known-empty"]["draft_observed"], True)

    def test_disabled_private_permission_sends_no_query(self) -> None:
        driver = MailboxPacketDriver(actual_packet("visible-multi-slots"))
        driver.allow_private_player_religion_draft_groups_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_draft_groups_private_v1(
                driver, expected_revision=driver.snapshot["revision"],
            )
        self.assertEqual(driver.sent, [])
        self.assertEqual(driver.ingested_types, [])


if __name__ == "__main__":
    unittest.main()
