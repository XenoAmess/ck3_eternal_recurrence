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
        "target_title_holder_prestate": [
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 29829}
        ],
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


def _truce_inputs() -> dict[str, object]:
    observed = lambda value: {"status": "observed", "value": value,
                              "unavailable_reason": None}
    unavailable = lambda reason: {"status": "unavailable", "value": None,
                                  "unavailable_reason": reason}
    return {
        "schema": "xar.ck3.defender-de-jure-truce-inputs.v1",
        "attacker_flexible_truces_perk": observed(False),
        "attacker_government_is_nomadic": observed(True),
        "defender_government_is_nomadic": observed(False),
        "nomad_both": observed(False),
        "short": unavailable("stock_condition_reader_unavailable"),
        "long": unavailable("stock_condition_reader_unavailable"),
        "border_raid_pair": unavailable("stock_condition_reader_unavailable"),
        "evaluated_days": None,
        "persisted_expiry_date_raw": None,
    }


class DefenderDeJureExitTermsV1Tests(unittest.TestCase):
    def test_storage_scan_is_only_a_structural_candidate(self) -> None:
        candidate = _candidate()
        candidate["truce_inputs_v1"] = _truce_inputs()
        candidate["border_raid_storage_candidate_v1"] = {
            "schema": "xar.ck3.h2743-border-raid-storage-candidate.v1",
            "status": "structural_candidate_only", "candidate": False,
            "storage_capacity": 17, "active_war_count": 2,
            "matching_war_count": 0, "unavailable_reason": None,
            "native_condition_observed": False,
        }
        projected = _project(candidate)
        self.assertIs(projected["border_raid_storage_candidate_v1"]["candidate"], False)
        self.assertEqual(projected["truce_inputs_v1"]["border_raid_pair"]["status"],
                         "unavailable")
        self.assertIsNone(projected["directed_truce"])
        self.assertFalse(projected["material_complete"])
        self.assertIsNone(projected["action_literal"])
        for field, value in (
            ("status", "observed"), ("native_condition_observed", True),
            ("candidate", None), ("matching_war_count", 1),
            ("storage_capacity", 1),
        ):
            with self.subTest(field=field):
                invalid = copy.deepcopy(candidate)
                invalid["border_raid_storage_candidate_v1"][field] = value
                with self.assertRaises(ValueError):
                    _project(invalid)
        invalid = copy.deepcopy(candidate)
        invalid["truce_inputs_v1"]["border_raid_pair"] = {
            "status": "observed", "value": False,
            "unavailable_reason": None,
        }
        with self.assertRaises(ValueError):
            _project(invalid)

    def test_partial_truce_inputs_preserve_material_gate(self) -> None:
        candidate = _candidate()
        candidate["truce_inputs_v1"] = _truce_inputs()
        projected = _project(candidate)
        self.assertIs(projected["truce_inputs_v1"]["nomad_both"]["value"], False)
        self.assertIsNone(projected["truce_inputs_v1"]["evaluated_days"])
        self.assertIsNone(projected["directed_truce"])
        self.assertFalse(projected["material_complete"])
        self.assertIsNone(projected["action_literal"])

    def test_partial_truce_inputs_fail_closed_on_missing_or_laundered_fields(self) -> None:
        for mutate in (
            lambda item: item["attacker_flexible_truces_perk"].update(
                status="unavailable", value=False),
            lambda item: item["attacker_government_is_nomadic"].update(
                status="unavailable", value=None, unavailable_reason=None),
            lambda item: item["nomad_both"].update(value=True),
            lambda item: item["short"].update(status="observed", value=False,
                                              unavailable_reason=None),
            lambda item: item.update(evaluated_days=730),
            lambda item: item.pop("border_raid_pair"),
        ):
            with self.subTest(mutate=mutate):
                candidate = _candidate()
                candidate["truce_inputs_v1"] = _truce_inputs()
                mutate(candidate["truce_inputs_v1"])
                with self.assertRaises(ValueError):
                    _project(candidate)

    def test_partial_truce_inputs_allow_typed_unavailable(self) -> None:
        candidate = _candidate()
        inputs = _truce_inputs()
        inputs["attacker_government_is_nomadic"] = {
            "status": "unavailable", "value": None,
            "unavailable_reason": "landed_government_flags_unavailable"}
        inputs["nomad_both"] = {
            "status": "unavailable", "value": None,
            "unavailable_reason": "party_government_flag_unavailable"}
        candidate["truce_inputs_v1"] = inputs
        self.assertIsNone(_project(candidate)["truce_inputs_v1"]["nomad_both"]["value"])

    def test_current_baseline_projects_without_exit_authority(self) -> None:
        projected = _project(_candidate())
        self.assertEqual(projected["target_title_ids"], [2128])
        self.assertEqual(projected["target_title_holder_prestate"], [
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 29829}
        ])
        self.assertEqual(len(projected["primary_resource_balances"]), 14)
        self.assertIsNone(projected["truce_inputs_v1"])
        self.assertIsNone(projected["title_vassal_delta"])
        self.assertIsNone(projected["signed_resource_delta"])
        self.assertIsNone(projected["directed_truce"])
        for field, reason in UNAVAILABLE_REASONS.items():
            self.assertEqual(projected[f"{field}_unavailable_reason"], reason)
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

    def test_title_holder_prestate_is_typed_and_not_a_transfer(self) -> None:
        for row in (
            {"title_id": 2129, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 29829},
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 33435},
            {"title_id": 2128, "holder_character_id": None,
             "holder_immediate_liege_character_id": 29829},
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": True},
        ):
            with self.subTest(row=row):
                candidate = _candidate()
                candidate["target_title_holder_prestate"] = [row]
                with self.assertRaises(ValueError):
                    _project(candidate)
        candidate = _candidate()
        candidate["target_title_holder_prestate"] = []
        with self.assertRaises(ValueError):
            _project(candidate)
        candidate = _candidate()
        candidate["target_title_holder_prestate"][0][
            "holder_immediate_liege_character_id"] = None
        self.assertIsNone(_project(candidate)["target_title_holder_prestate"][0][
            "holder_immediate_liege_character_id"])
        self.assertIsNone(_project(_candidate())["title_vassal_delta"])

    def test_real_zero_baseline_is_distinct_from_missing_material_effect(self) -> None:
        candidate = _candidate()
        for row in candidate["primary_resource_balances"]:
            row["value"]["raw"] = 0
        for row in candidate["primary_monthly_gold_income"]:
            row["value"]["raw"] = 0
        projected = _project(candidate)
        self.assertTrue(all(row["value"]["raw"] == 0 for row in projected["primary_resource_balances"]))
        self.assertIsNone(projected["signed_resource_delta"])
        self.assertIsNone(projected["title_vassal_delta"])
        self.assertIsNone(projected["directed_truce"])
        for field, reason in UNAVAILABLE_REASONS.items():
            self.assertEqual(projected[f"{field}_unavailable_reason"], reason)
        self.assertFalse(projected["material_complete"])

    def test_missing_native_read_cannot_be_filled_with_zero(self) -> None:
        mutations = (
            lambda item: item["primary_resource_balances"][0]["value"].update(raw=None),
            lambda item: item["primary_resource_balances"][0].pop("value"),
            lambda item: item["primary_monthly_gold_income"][1]["value"].update(raw=None),
            lambda item: item["primary_monthly_gold_income"].pop(),
            lambda item: item.update(signed_resource_delta=[]),
            lambda item: item.update(title_vassal_delta=[]),
            lambda item: item.update(directed_truce={"days": 0}),
            lambda item: item.update(material_complete=True),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                candidate = _candidate()
                mutate(candidate)
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
