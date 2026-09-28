"""The de-jure exit baseline must never become a material decision."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import (
    RESOURCES,
    SCHEMA,
    UNAVAILABLE_REASONS,
    normalize_defender_dejure_exit_terms_v1,
    parse_query_defender_dejure_exit_terms_v1_step,
    query_defender_dejure_exit_terms_v1_step,
)


def _candidate() -> dict[str, object]:
    rows = [
        {"character_id": character_id, "resource": resource, "value": {"raw": 1, "scale": 100_000}}
        for character_id in (30097, 29829)
        for resource in sorted(RESOURCES)
    ]
    return {
        "schema": SCHEMA,
        "native_revision": 3,
        "war_id": 16777231,
        "date_raw": 53217264,
        "casus_belli_database_index": 17,
        "casus_belli_key": "individual_county_de_jure_cb",
        "primary_attacker_character_id": 30097,
        "primary_defender_character_id": 29829,
        "target_title_ids": [2128],
        "primary_resource_balances": rows,
        "primary_monthly_gold_income": [
            {"character_id": character_id, "value": {"raw": 1, "scale": 100_000}}
            for character_id in (30097, 29829)
        ],
        "title_vassal_delta": None,
        "title_vassal_delta_unavailable_reason": UNAVAILABLE_REASONS["title_vassal_delta"],
        "signed_resource_delta": None,
        "signed_resource_delta_unavailable_reason": UNAVAILABLE_REASONS["signed_resource_delta"],
        "directed_truce": None,
        "directed_truce_unavailable_reason": UNAVAILABLE_REASONS["directed_truce"],
        "same_frame_stable": True,
        "material_complete": False,
    }


def _project(value: dict[str, object]) -> dict[str, object]:
    return normalize_defender_dejure_exit_terms_v1(
        value,
        expected_war_id=16777231,
        expected_native_revision=3,
        expected_date_raw=53217264,
        expected_defender_id=29829,
        expected_attacker_id=30097,
        expected_target_title_ids=[2128],
    )


class DefenderDeJureExitTermsV1Tests(unittest.TestCase):
    def test_current_baseline_projects_without_exit_authority(self) -> None:
        projected = _project(_candidate())
        self.assertEqual(projected["target_title_ids"], [2128])
        self.assertEqual(len(projected["primary_resource_balances"]), 14)
        self.assertIsNone(projected["title_vassal_delta"])
        self.assertIsNone(projected["signed_resource_delta"])
        self.assertIsNone(projected["directed_truce"])
        self.assertIsNone(projected["recommended_outcome"])
        self.assertIsNone(projected["action_literal"])
        self.assertFalse(projected["material_complete"])

    def test_rejects_laundered_material_readiness(self) -> None:
        for field, substitute in (
            ("material_complete", True),
            ("signed_resource_delta", []),
            ("title_vassal_delta_unavailable_reason", "observed"),
            ("directed_truce", {"days": 1}),
        ):
            with self.subTest(field=field):
                candidate = _candidate()
                candidate[field] = substitute
                with self.assertRaises(ValueError):
                    _project(candidate)

    def test_rejects_wrong_war_target_and_missing_balance(self) -> None:
        for field, substitute in (
            ("war_id", 16777232),
            ("native_revision", 4),
            ("target_title_ids", [2129]),
            ("primary_attacker_character_id", 30098),
        ):
            with self.subTest(field=field):
                candidate = _candidate()
                candidate[field] = substitute
                with self.assertRaises(ValueError):
                    _project(candidate)
        candidate = _candidate()
        candidate["primary_resource_balances"] = copy.deepcopy(
            candidate["primary_resource_balances"][:-1]
        )
        with self.assertRaises(ValueError):
            _project(candidate)

    def test_step_requires_canonical_positive_war_id(self) -> None:
        step = query_defender_dejure_exit_terms_v1_step(16777231)
        self.assertEqual(parse_query_defender_dejure_exit_terms_v1_step(step), 16777231)
        self.assertIsNone(parse_query_defender_dejure_exit_terms_v1_step(step + "x"))
        self.assertIsNone(parse_query_defender_dejure_exit_terms_v1_step(step.replace("16777231", "016777231")))
        with self.assertRaises(ValueError):
            query_defender_dejure_exit_terms_v1_step(-1)


if __name__ == "__main__":
    unittest.main()
