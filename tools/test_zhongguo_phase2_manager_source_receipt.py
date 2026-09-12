#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_manager_source_receipt import (
    Phase2ManagerSourceReceiptError,
    SOURCE_RECEIPT_KIND,
    validate_phase2_manager_source_receipt,
)


TREE = "A" * 64
MANAGER = 27181
OWNER = 36354
DATE_RAW = 53155680


def _record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def _source(root: Path) -> Path:
    checkpoint = root / "manager.ck3"
    checkpoint.write_bytes(b"real-checkpoint")
    live = root / "live.json"
    live.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "zg361_stage10_player_source_capture_v1",
                "result": "GREEN",
                "production_live": True,
                "mcp_native_save": True,
                "fixture_used": False,
                "console_used": False,
                "game_time_advanced": False,
                "target_binding": {
                    "player_character_id": MANAGER,
                    "date_raw": DATE_RAW,
                    "paused": True,
                    "map_ready": True,
                    "active_event": None,
                },
                "target_campaign_root": {
                    "player_character_id": MANAGER,
                    "immediate_liege_character_id": OWNER,
                    "independent": False,
                    "campaign_root_context_ready": True,
                },
                "target_checkpoint": _record(checkpoint),
            }
        ),
        encoding="utf-8",
    )
    receipt = root / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": SOURCE_RECEIPT_KIND,
                "result": "GREEN",
                "fixture_used": False,
                "console_used": False,
                "selection_attempted": False,
                "game_version": "1.19.0.6",
                "source_container_header": "SAV0101",
                "offline_player_state": {
                    "meta_number_of_players": 1,
                    "played_character_records": [
                        {"character_id": MANAGER, "player_id": 1}
                    ],
                    "currently_played_character_ids": [MANAGER],
                },
                "offline_topology": {
                    "player_manager_character_id": MANAGER,
                    "immediate_liege_character_id": OWNER,
                    "player_primary_title_tier": 4,
                    "player_government": "celestial_government",
                    "direct_landed_vassal_character_ids": [123],
                },
                "product_tree_sha256": TREE,
                "checkpoint": _record(checkpoint),
                "live_source_provenance": _record(live),
                "fixed_tail_contract": {
                    "source_b1_state": 7,
                    "first_pending_event": "zg361b1.122",
                    "first_pending_event_days": 30,
                    "maximum_action_days": 120,
                },
                "product_fix_contract": {
                    "repaired_product_tree_sha256": TREE,
                },
            }
        ),
        encoding="utf-8",
    )
    return receipt


class Phase2ManagerSourceReceiptTests(unittest.TestCase):
    def test_real_source_contract_is_normalized_for_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = validate_phase2_manager_source_receipt(
                _source(Path(temporary)),
                expected_product_tree_sha256=TREE,
            )
        self.assertEqual(source["result"], "GREEN")
        self.assertEqual(source["player_manager_character_id"], MANAGER)
        self.assertEqual(source["owner_character_id"], OWNER)
        self.assertEqual(source["date_raw"], DATE_RAW)
        self.assertTrue(source["checkpoint"]["save_lineage_id"].startswith(
            "zg361-stage10-player-manager-"
        ))

    def test_product_tree_mismatch_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(Phase2ManagerSourceReceiptError):
                validate_phase2_manager_source_receipt(
                    _source(Path(temporary)),
                    expected_product_tree_sha256="B" * 64,
                )


if __name__ == "__main__":
    unittest.main()
