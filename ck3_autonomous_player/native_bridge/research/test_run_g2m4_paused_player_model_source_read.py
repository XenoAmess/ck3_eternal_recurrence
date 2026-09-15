"""Protocol-shaped no-action tests for the owned slot42 player model receipt."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_g2m4_paused_player_model_source_read import (
    run_owned_paused_player_model_source_read,
)
from test_run_g2m4_paused_player_view_read import (
    ACTOR_ID,
    DATE_RAW,
    PRIVATE_STEP,
    REVISION,
    ROOT_STEP,
    FakeDriver,
    frozen,
    probe_result,
    root_result,
)


def probe_with_model(*, holdings: list[dict[str, int]] | None = None,
                     definitions: int = 5,
                     status: str = "sources_available") -> dict[str, object]:
    probe = probe_result()
    probe["private_probe"]["player_model_sources"] = {
        "schema_version": 1,
        "advertised": False,
        "status": status,
        "failure": "none" if status == "sources_available" else "definition_source",
        "snapshot_revision": REVISION if status == "sources_available" else None,
        "date_raw": DATE_RAW if status == "sources_available" else None,
        "player_character_id": ACTOR_ID if status == "sources_available" else None,
        "view_model_binding_verified": True if status == "sources_available" else False,
        "directly_held_barony_provinces": holdings if holdings is not None else [
            {"barony_title_id": 1001, "province_id": 2619},
            {"barony_title_id": 1002, "province_id": 2620},
        ],
        "definition_source_count": definitions if status == "sources_available" else None,
        "legal_construction_evaluated": False,
    }
    return probe


class PausedPlayerModelSourceReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.artifact = Path(self.temporary.name) / "model-read.json"

    def Run(self, model: dict[str, object]) -> tuple[dict[str, object], FakeDriver]:
        driver = FakeDriver({ROOT_STEP: root_result(), PRIVATE_STEP: model})
        record = run_owned_paused_player_model_source_read(
            driver, frozen(), self.artifact
        )
        self.assertEqual(json.loads(self.artifact.read_text(encoding="utf-8")), record)
        self.assertEqual([frame["step"] for frame in driver.sent],
                         [ROOT_STEP, PRIVATE_STEP])
        return record, driver

    def test_closed_gui_cache_empty_but_direct_model_sources_observed(self) -> None:
        record, _ = self.Run(probe_with_model())
        self.assertEqual(record["status"], "model_sources_observed")
        self.assertEqual(record["player_model_sources"]["definition_source_count"], 5)
        self.assertEqual(record["player_model_sources"]["directly_held_barony_provinces"][0]["province_id"], 2619)
        self.assertFalse(record["construction_legality_ready"])
        self.assertEqual(record["next_read"], "same_frame_player_native_final_legality_and_cost")
        self.assertFalse(record["advertised"])
        self.assertNotIn("borrowed_definition_addresses", self.artifact.read_text(encoding="utf-8"))

    def test_unavailable_model_source_preserves_red(self) -> None:
        record, _ = self.Run(probe_with_model(status="unavailable"))
        self.assertEqual(record["status"], "red")
        self.assertEqual(record["issue"], "player_model_source_unavailable")

    def test_empty_source_is_evidence_insufficient_not_no_legal(self) -> None:
        record, _ = self.Run(probe_with_model(holdings=[], definitions=0))
        self.assertEqual(record["status"], "model_sources_evidence_insufficient")
        self.assertFalse(record["construction_legality_ready"])


if __name__ == "__main__":
    unittest.main()
