"""Consume the actual R9 provider DTO containing a native default blank slot."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.player_religion_draft_tenet_choices_private_transport import (
    normalize_player_religion_draft_tenet_choices_v1,
)

FIXTURE = (ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_draft_tenet_choices/"
           "native-default-third-slot.json")


class PlayerReligionDraftTenetBlankSlotWireTests(unittest.TestCase):
    def test_actual_provider_blank_slot_keeps_identity_null_and_complete_source_gates(self) -> None:
        native = json.loads(FIXTURE.read_text(encoding="utf-8"))
        snapshot = {
            "date_raw": native["date_raw"],
            "played_character": {"character_id": native["played_character_id"]},
            "diagnostics": {"hello": {
                "expected_ck3_version": native["game_version"],
                "expected_ck3_sha256": native["executable_sha256"],
            }},
        }
        actual = normalize_player_religion_draft_tenet_choices_v1(native, snapshot=snapshot)
        self.assertEqual(actual, native)
        self.assertIsNot(actual, native)
        self.assertEqual(actual["slots"], [
            {"slot_index": 0, "selected_tenet_key": "tenet_0"},
            {"slot_index": 1, "selected_tenet_key": "tenet_1"},
            {"slot_index": 2, "selected_tenet_key": None},
        ])
        self.assertIs(actual["available"], True)
        self.assertIs(actual["draft_observed"], True)
        self.assertIs(actual["tenet_gates_complete"], True)
        self.assertEqual(len(actual["sources"]), 8)
        self.assertIs(actual["sources"][3]["final_selectable"], True)
        self.assertIs(actual["sources"][4]["final_selectable"], False)
        self.assertEqual(actual["sources"][4]["native_status_raw"], 0)
        self.assertEqual(actual["sources"][4]["actor_faith_status_raw"], 2)


if __name__ == "__main__":
    unittest.main()
