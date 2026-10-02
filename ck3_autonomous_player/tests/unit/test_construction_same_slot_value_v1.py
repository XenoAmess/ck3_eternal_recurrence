"""Focused regression for Robert's actual gross-positive downgrade proposal.

Actual material: m4-council/role-coverage/robert-v19-412-actual-01/
construction/query-source.json, SHA-256
4fd9fa8b7fb971b6473fd80f2beb3abccf12edfc63bb38f5f56dcc3360fcb662.
The Farm02/Farm01 tuple, native cost, gold and empty Cereal quote are actual
projections. Equal-value, unknown-key and Pastures incumbents below are
explicit controlled value variants. Completed rows retain only the fields
consumed by the pure selector, plus actual Farm02 ordinal where known; these
focused projections are not full wire rows. No new legality/ABI claim is made.
"""
from __future__ import annotations

import unittest

from xar_autoplayer.bridge.domain_construction_private_transport_v1 import (
    _candidate,
)


ACTUAL_GOLD_RAW = 120_659_426
ACTUAL_FARM_HOLDING = (2103, 2635)
ACTUAL_CEREAL_HOLDING = (2143, 2619)
ACTUAL_CEREAL_COST_RAW = 14_250_000
ACTUAL_FARM_COST_RAW = 18_000_000


def _legal(holding: tuple[int, int], slot: int, *, key: str,
           type_id: int, cost: int) -> dict[str, object]:
    return {
        "barony_title_id": holding[0], "province_id": holding[1],
        "slot_index": slot, "building_type_id": type_id,
        "building_key": key, "native_cost_observed": True,
        "cost_raw_native": [cost, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }


def _completed(holding: tuple[int, int], slot: int, key: str | None,
               *, type_id: int | None = None) -> dict[str, object]:
    row: dict[str, object] = {
        "barony_title_id": holding[0], "province_id": holding[1],
        "slot_index": slot, "building_key": key,
    }
    if type_id is not None:
        row["building_type_id"] = type_id
    return row


def _world(samples: list[dict[str, object]],
           completed: list[dict[str, object]]) -> dict[str, object]:
    holdings = sorted({(row["barony_title_id"], row["province_id"])
                       for row in samples})
    return {
        "player_gold_raw": ACTUAL_GOLD_RAW,
        "active_constructions": [
            {"barony_title_id": barony, "province_id": province,
             "active": False}
            for barony, province in holdings
        ],
        "legal_samples": samples,
        "completed_buildings_observed": True,
        "completed_buildings": completed,
        # These actual source flags do not veto a positive observed candidate.
        "positive_income_coverage_complete": False,
        "checks_truncated": True,
    }


def _cereal(slot: int = 4) -> dict[str, object]:
    return _legal(ACTUAL_CEREAL_HOLDING, slot, key="cereal_fields_01",
                  type_id=604, cost=ACTUAL_CEREAL_COST_RAW)


def _farm_downgrade() -> dict[str, object]:
    return _legal(ACTUAL_FARM_HOLDING, 1, key="farm_estates_01",
                  type_id=596, cost=ACTUAL_FARM_COST_RAW)


def _farm_occupant() -> dict[str, object]:
    return _completed(ACTUAL_FARM_HOLDING, 1, "farm_estates_02", type_id=597)


class ConstructionSameSlotValueTests(unittest.TestCase):
    def test_actual_farm_downgrade_yields_to_positive_empty_cereal(self) -> None:
        world = _world([_farm_downgrade(), _cereal()], [_farm_occupant()])

        selected = _candidate(world, exact_ck3_build="1.20.0.3")

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(
            tuple(selected[key] for key in
                  ("barony_title_id", "province_id", "building_type_id", "slot_index")),
            (2143, 2619, 604, 4),
        )
        self.assertEqual(selected["building_key"], "cereal_fields_01")
        self.assertEqual(selected["stock_gold_cost_raw"], ACTUAL_CEREAL_COST_RAW)
        self.assertEqual(selected["gold_before_raw"], ACTUAL_GOLD_RAW)
        self.assertEqual(selected["authored_monthly_income_hundredths"], 50)
        self.assertEqual(selected["authored_monthly_income_delta_hundredths"], 50)
        self.assertEqual(selected["old_authored_monthly_income_hundredths"], 0)
        self.assertIsNone(selected["old_building_key"])
        self.assertIs(selected["slot_was_empty"], True)

    def test_equal_gain_and_cost_prefer_empty_slot_over_military_replacement(self) -> None:
        world = _world(
            [_cereal(2), _cereal(4)],
            [_completed(ACTUAL_CEREAL_HOLDING, 2, "military_camps_01")],
        )

        selected = _candidate(world, exact_ck3_build="1.20.0.3")

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected["slot_index"], 4)
        self.assertIs(selected["slot_was_empty"], True)
        self.assertEqual(selected["authored_monthly_income_delta_hundredths"], 50)

    def test_negative_and_zero_direct_income_replacements_are_not_selected(self) -> None:
        # The actual Farm02 replacement is negative. A controlled equal-income
        # Paddies occupant makes the otherwise positive Cereal target zero gain.
        world = _world(
            [_farm_downgrade(), _cereal()],
            [_farm_occupant(),
             _completed(ACTUAL_CEREAL_HOLDING, 4, "paddy_fields_01")],
        )

        self.assertIsNone(_candidate(world, exact_ck3_build="1.20.0.3"))

    def test_unknown_occupied_key_is_not_empty_and_known_empty_still_selects(self) -> None:
        world = _world(
            [_cereal(2), _cereal(4)],
            [_completed(ACTUAL_CEREAL_HOLDING, 2, None)],
        )

        selected = _candidate(world, exact_ck3_build="1.20.0.3")

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected["slot_index"], 4)
        self.assertIs(selected["slot_was_empty"], True)

    def test_gross_field_remains_compatible_and_replacement_delta_is_separate(self) -> None:
        # Controlled positive replacement: Cereal gross50 minus Pastures35.
        world = _world(
            [_cereal(2)],
            [_completed(ACTUAL_CEREAL_HOLDING, 2, "pastures_01")],
        )

        selected = _candidate(world, exact_ck3_build="1.20.0.3")

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected["authored_monthly_income_hundredths"], 50)
        self.assertEqual(selected["old_authored_monthly_income_hundredths"], 35)
        self.assertEqual(selected["authored_monthly_income_delta_hundredths"], 15)
        self.assertEqual(selected["old_building_key"], "pastures_01")
        self.assertIs(selected["slot_was_empty"], False)


if __name__ == "__main__":
    unittest.main()
