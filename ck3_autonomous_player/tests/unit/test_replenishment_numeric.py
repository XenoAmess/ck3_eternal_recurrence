"""Focused offline checks for native chunk arithmetic and its query consumer."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP
from xar_autoplayer.replenishment_numeric import (
    project_observed_replenishment_v1,
    same_input_chunk_q,
)


def record(*, ordinal: int = 0, current: int = 90, maximum: int = 100,
           prepared: int = 20_000, predicate: bool = True,
           status: str = "available") -> dict[str, object]:
    return {
        "status": status,
        "unavailable_reason": None if status == "available" else "chunk_read_failed",
        "record_index": ordinal, "persistent_regiment_id": 0, "chunk_index": ordinal,
        "current_soldiers": current, "maximum_soldiers": maximum,
        "effective_current_soldiers": current, "state_raw": 0,
        "native_can_replenish": False, "native_chunk_can_replenish": predicate,
        "persistent_monthly_replenishment_fraction_raw": 99_999,
        "persistent_monthly_replenishment_fraction_scale": 100_000,
        "persistent_prepared_replenishment_fraction_raw": prepared,
        "persistent_prepared_replenishment_fraction_scale": 100_000,
    }


def army(army_id: int = 0, records: list[dict[str, object]] | None = None,
         *, data_status: str = "available") -> dict[str, object]:
    records = records if records is not None else [record()]
    return {
        "status": "available", "army_id": army_id, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 1,
        "current_soldiers": 450, "maximum_soldiers": 500,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100_000,
        "unavailable_reason": None,
        "regiment_replenishment_records_v1": [{
            "army_regiment_id": 0, "source": "native_all_data_records",
            "status": data_status, "ready": data_status == "available",
            "native_data_record_count": len(records),
            "unavailable_reason": None if data_status == "available" else "partial_data",
            "records": records,
        }],
    }


class OfflineStrengthService(GameplayBridgeService):
    """In-memory transport boundary; never creates a driver or game connection."""

    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.steps: list[tuple[str, int | None]] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "paused": True, "revision": 5, "player_armies": [
                {"army_id": row["army_id"]} for row in self.rows
            ], "active_wars": [],
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(self, step: str, *, expected_revision: int | None = None,
                     **kwargs: object) -> dict[str, object]:
        self.steps.append((step, expected_revision))
        return {"status": "available", "army_strengths": copy.deepcopy(self.rows)}


class ReplenishmentNumericTests(unittest.TestCase):
    def test_chunk_cap_and_native_zero_keep_core_eligibility(self) -> None:
        self.assertEqual(same_input_chunk_q(100, 90, 20_000, True)["same_input_q"], 10)
        zero = same_input_chunk_q(10, 0, 1, True)
        self.assertEqual(zero["same_input_q"], 0)
        self.assertTrue(zero["native_core_chunk_qualifies"])
        for prepared, predicate in ((0, True), (-1, True), (20_000, False)):
            result = same_input_chunk_q(100, 90, prepared, predicate)
            self.assertEqual(result["same_input_q"], 0)
            self.assertFalse(result["native_core_chunk_qualifies"])
        state3 = same_input_chunk_q(10, 10, 20_000, True)
        self.assertEqual(state3["same_input_q"], 0)
        self.assertFalse(state3["native_core_chunk_qualifies"])

    def test_native_low64_product_trunc_zero_and_low32_store(self) -> None:
        # 3 * 6148914691236483871 = 2**64 - 100003: native low64 is negative.
        wrapped = same_input_chunk_q(3, 0, 6_148_914_691_236_483_871, True)
        self.assertEqual(wrapped["wrapped_product"], -100_003)
        self.assertEqual(wrapped["same_input_q"], -1)
        self.assertTrue(wrapped["native_core_chunk_qualifies"])
        narrowed = same_input_chunk_q(2_147_483_647, -2_147_483_648, 400_000, True)
        self.assertEqual(narrowed["effective_deficit"], 4_294_967_295)
        self.assertEqual(narrowed["same_input_q"], -1)
        for values in ((True, 0, 1, True), (1, 0, None, True),
                       (1, 0, 2**63, True), (1, 0, 1, 1)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                same_input_chunk_q(*values)

    def test_existing_query_exposes_projection_from_actual_field_names(self) -> None:
        rows = [army()]
        before = copy.deepcopy(rows)
        service = OfflineStrengthService(rows)
        result = service.query_army_strengths([0], expected_revision=5)
        projection = result["same_input_replenishment_v1"]
        group = projection["persistent_outputs"][0]
        self.assertEqual(projection["status"], "available")
        self.assertEqual(group["same_input_q_by_chunk"], [10, None, None, None, None, None, None])
        self.assertEqual(group["status_by_chunk"][0], "available")
        self.assertFalse(group["all_seven_observed"])
        self.assertEqual(projection["source_snapshots"][0]["native_data_record_count"], 1)
        self.assertEqual(service.steps, [(QUERY_ARMY_STRENGTHS_STEP, 5)])
        self.assertEqual(rows, before)
        self.assertEqual(result["army_strengths"], before)
        # Whole capacity500, fresh99999, and persistent Can=false are independent.
        self.assertEqual(group["observations_by_chunk"][0][0]["calculation"]["wrapped_product"], 2_000_000)
        self.assertIsNone(result["source"]["game_version"])

    def test_unavailable_and_missing_fraction_never_become_integer_zero(self) -> None:
        rows = [army(records=[record(current=0, maximum=10, prepared=1),
                              record(ordinal=1, status="unavailable")],
                     data_status="partial")]
        projection = project_observed_replenishment_v1(rows)
        group = projection["persistent_outputs"][0]
        self.assertEqual(projection["status"], "partial")
        self.assertEqual(group["same_input_q_by_chunk"][:2], [0, None])
        self.assertEqual(group["status_by_chunk"][:2], ["available", "unavailable"])
        missing = army()
        missing["regiment_replenishment_records_v1"][0]["records"][0][
            "persistent_prepared_replenishment_fraction_raw"
        ] = None
        projected = project_observed_replenishment_v1([missing])
        self.assertIsNone(projected["persistent_outputs"][0]["same_input_q_by_chunk"][0])
        with self.assertRaises(BridgeUnavailableError):
            OfflineStrengthService([missing]).query_army_strengths([0], expected_revision=5)

    def test_aliases_conflicts_empty_and_unpublished_coverage(self) -> None:
        rows = [army(), army(1)]
        projected = project_observed_replenishment_v1(rows)
        self.assertEqual(len(projected["persistent_outputs"]), 1)
        group = projected["persistent_outputs"][0]
        self.assertEqual(group["same_input_q_by_chunk"][0], 10)
        self.assertEqual(len(group["observations_by_chunk"][0]), 2)
        rows[1]["regiment_replenishment_records_v1"][0]["records"][0][
            "persistent_prepared_replenishment_fraction_raw"
        ] = 5_000
        conflict = project_observed_replenishment_v1(rows)
        self.assertEqual(conflict["status"], "partial")
        self.assertEqual(conflict["persistent_outputs"][0]["status_by_chunk"][0],
                         "conflicting_observations")
        self.assertIsNone(conflict["persistent_outputs"][0]["same_input_q_by_chunk"][0])
        empty = project_observed_replenishment_v1([army(records=[])])
        self.assertEqual(empty["status"], "available")
        self.assertEqual(empty["source_snapshots"][0]["native_data_record_count"], 0)
        self.assertEqual(empty["persistent_outputs"], [])
        legacy = army()
        del legacy["regiment_replenishment_records_v1"]
        unpublished = project_observed_replenishment_v1([legacy])
        self.assertEqual(unpublished["status"], "unavailable")
        self.assertEqual(unpublished["persistent_outputs"], [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReplenishmentNumericTests)
    )
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)
        paths = [Path(__file__), ROOT / "src/xar_autoplayer/replenishment_numeric.py",
                 ROOT / "src/xar_autoplayer/bridge/service.py"]
        receipt = {
            "status": "GREEN" if result.wasSuccessful() else "RED",
            "readiness": "static-ready", "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors),
            "game_interactions": 0, "added_game_days": 0,
            "native_build": False,
            "open_kaishek_prevalidation": {
                "status": "not-applicable",
                "reason": "Native int-width arithmetic and Python query projection; no Paradox script semantics.",
            },
            "inputs": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                       for path in paths],
        }
        (args.artifacts / "offline-validation.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
