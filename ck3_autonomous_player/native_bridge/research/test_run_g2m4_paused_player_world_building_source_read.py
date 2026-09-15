"""No-launch protocol fixture for the private paused M4 world eligibility read."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_g2m4_paused_player_world_building_source_read import (
    run_owned_paused_player_world_building_source_read,
)
from test_run_g2m4_paused_player_model_source_read import probe_with_model
from test_run_g2m4_paused_player_view_read import (
    ACTOR_ID, DATE_RAW, PRIVATE_STEP, REVISION, ROOT_STEP,
    FakeDriver, frozen, root_result,
)


HOLDINGS = [{"barony_title_id": 2143, "province_id": 2619}]


def probe_with_world(*, available: bool = True,
                     samples: list[dict[str, int]] | None = None) -> dict[str, object]:
    probe = probe_with_model(holdings=HOLDINGS, definitions=0)
    probe["private_probe"]["player_world_building_sources"] = {
        "schema_version": 1,
        "advertised": False,
        "read_only": True,
        "status": "source_available" if available else "unavailable",
        "failure": "none" if available else "registry_source",
        "snapshot_revision": REVISION if available else None,
        "date_raw": DATE_RAW if available else None,
        "player_character_id": ACTOR_ID if available else None,
        "definition_source_count": 2 if available else None,
        "final_legality_checks": 4 if available else None,
        "native_final_legality_evaluated": available,
        "checks_truncated": False,
        "cost_ready": False,
        "construction_action_ready": False,
        "directly_held_barony_provinces": HOLDINGS if available else [],
        "legal_samples": (samples if samples is not None else [
            {"barony_title_id": 2143, "province_id": 2619,
             "building_type_id": 22, "slot_index": 1},
        ]) if available else [],
    }
    return probe


class PausedWorldBuildingSourceReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.artifact = Path(self.temporary.name) / "world-read.json"

    def Run(self, probe: dict[str, object]) -> tuple[dict[str, object], FakeDriver]:
        driver = FakeDriver({ROOT_STEP: root_result(), PRIVATE_STEP: probe})
        record = run_owned_paused_player_world_building_source_read(
            driver, frozen(), self.artifact
        )
        self.assertEqual(json.loads(self.artifact.read_text(encoding="utf-8")),
                         record)
        self.assertEqual([frame["step"] for frame in driver.sent],
                         [ROOT_STEP, PRIVATE_STEP])
        return record, driver

    def test_closed_gui_zero_but_world_native_legal_sample(self) -> None:
        record, _ = self.Run(probe_with_world())
        self.assertEqual(record["status"], "world_player_legality_observed")
        self.assertEqual(record["player_world_building_sources"]["definition_source_count"], 2)
        self.assertFalse(record["construction_action_ready"])
        self.assertFalse(record["advertised"])
        text = self.artifact.read_text(encoding="utf-8")
        self.assertNotIn("borrowed_definition_address", text)

    def test_no_legal_sample_is_evidence_insufficient(self) -> None:
        record, _ = self.Run(probe_with_world(samples=[]))
        self.assertEqual(record["status"], "world_source_evidence_insufficient")
        self.assertFalse(record["construction_action_ready"])

    def test_world_registry_failure_is_red(self) -> None:
        record, _ = self.Run(probe_with_world(available=False))
        self.assertEqual(record["status"], "red")
        self.assertEqual(record["issue"], "private_world_source_unavailable")

    def test_cost_claim_without_stock_row_is_red(self) -> None:
        probe = probe_with_world()
        probe["private_probe"]["player_world_building_sources"]["cost_ready"] = True
        record, _ = self.Run(probe)
        self.assertEqual(record["status"], "red")
        self.assertEqual(record["issue"], "private_world_claims_unobserved_cost_or_action")


if __name__ == "__main__":
    unittest.main()
