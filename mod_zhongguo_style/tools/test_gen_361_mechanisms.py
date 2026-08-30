#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 tests for the complete 361 mechanism projection."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from gen_361_mechanisms import MOD_ROOT, effect_name, outputs
from zg361_mechanism_data import (
    ACCEPTANCE_FIELDS,
    AcceptanceContract,
    LEDGERS,
    MECHANISM_COUNT,
    PROFILE_DELTAS,
    load_acceptance_contracts,
    load_mechanisms,
    mechanism_deltas,
)
from zg361_phase2_runtime_data import PHASE2_RUNTIME_SPECS


def valid_acceptance_payload(mechanism_id: int) -> dict[str, object]:
    return {
        "acceptance_cn": f"机制 {mechanism_id:03d} 必须冻结具体案卷并核对结果。",
        "semantic_family": f"family_{mechanism_id:03d}",
        "required_state": [f"case_{mechanism_id:03d}_id 与 review_serial"],
        "visible_feedback": [f"显示机制 {mechanism_id:03d} 的具体案卷结果"],
        "batch_assertions": [f"机制 {mechanism_id:03d} 的案卷只结算一次"],
    }


class MechanismGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.rendered = outputs(cls.mechanisms)

    def test_exact_catalogue(self) -> None:
        self.assertEqual(len(self.mechanisms), MECHANISM_COUNT)
        self.assertEqual([item.id for item in self.mechanisms], list(range(1, 362)))
        self.assertEqual(len({item.title_cn for item in self.mechanisms}), 361)
        self.assertEqual(len({item.title_en for item in self.mechanisms}), 361)

    def test_every_choice_is_reviewed_and_specific(self) -> None:
        generic = {
            "Adopt the evidence-led policy",
            "Prioritize the short-term result",
        }
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertNotIn(mechanism.option_a_en, generic)
                self.assertNotIn(mechanism.option_b_en, generic)
                self.assertNotEqual(mechanism.option_a_cn, mechanism.option_b_cn)
                self.assertNotEqual(mechanism.option_a_en, mechanism.option_b_en)
                self.assertIn(mechanism.profile, PROFILE_DELTAS)
                self.assertIn(mechanism.reference_choice, {"a", "b", "c"})

    def test_acceptance_contracts_are_typed_complete_and_specific(self) -> None:
        for mechanism in self.mechanisms:
            contract = mechanism.acceptance_contract
            with self.subTest(mechanism=mechanism.id):
                self.assertIsInstance(contract, AcceptanceContract)
                self.assertTrue(contract.acceptance_cn)
                self.assertTrue(contract.semantic_family)
                self.assertTrue(contract.required_state)
                self.assertTrue(contract.visible_feedback)
                self.assertTrue(contract.batch_assertions)
                for values in (
                    contract.required_state,
                    contract.visible_feedback,
                    contract.batch_assertions,
                ):
                    self.assertTrue(all(isinstance(value, str) and value for value in values))

    def test_acceptance_loader_rejects_missing_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            payload = {
                f"{mechanism_id:03d}": valid_acceptance_payload(mechanism_id)
                for mechanism_id in range(1, MECHANISM_COUNT)
            }
            (folder / "acceptance_001_360.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "exactly 001..361"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            duplicate = {"001": valid_acceptance_payload(1)}
            for name in ("acceptance_a.json", "acceptance_b.json"):
                (folder / name).write_text(
                    json.dumps(duplicate, ensure_ascii=False), encoding="utf-8"
                )
            with self.assertRaisesRegex(ValueError, "duplicate acceptance contract"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_missing_or_wrong_typed_field(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            missing = valid_acceptance_payload(1)
            del missing["visible_feedback"]
            (folder / "acceptance_missing.json").write_text(
                json.dumps({"001": missing}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "fields mismatch"):
                load_acceptance_contracts(folder)

        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            wrong_type = valid_acceptance_payload(1)
            wrong_type["required_state"] = "not a list"
            (folder / "acceptance_wrong_type.json").write_text(
                json.dumps({"001": wrong_type}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "must be a non-empty list"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_generic_variable_change_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            generic = valid_acceptance_payload(1)
            generic["batch_assertions"] = ["变量变化"]
            (folder / "acceptance_generic.json").write_text(
                json.dumps({"001": generic}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "generic variable-change claim"):
                load_acceptance_contracts(folder)

    def test_shared_ledgers_have_real_tradeoffs(self) -> None:
        for mechanism in self.mechanisms:
            choices = {
                choice: mechanism_deltas(mechanism, choice)
                for choice in ("a", "b", "c")
            }
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(len({tuple(sorted(value.items())) for value in choices.values()}), 3)
                for deltas in choices.values():
                    self.assertTrue(deltas)
                    self.assertTrue(set(deltas).issubset(LEDGERS))
                # At least one route carries an explicit cost/risk, preventing a no-brainer trio.
                self.assertTrue(
                    any(
                        value > 0
                        for choice in choices.values()
                        for key, value in choice.items()
                        if key
                        in {
                            "admin_load",
                            "appeal_risk",
                            "tech_debt",
                            "burnout",
                            "hc_pressure",
                            "pay_debt",
                            "policy_debt",
                            "budget_pressure",
                        }
                    )
                )

    def test_generated_runtime_coverage(self) -> None:
        event_path = MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt"
        effect_path = (
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_mechanism_effects.txt"
        )
        events = self.rendered[event_path].decode("utf-8-sig")
        effects = self.rendered[effect_path].decode("utf-8-sig")
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(events.count(f"zg361m.{mechanism.id} = {{"), 1)
                for choice in ("a", "b", "c"):
                    self.assertEqual(effects.count(f"{effect_name(mechanism.id, choice)} = {{"), 1)
                self.assertEqual(
                    effects.count(f"zg361_mechanism_{mechanism.id:03d}_ai_effect = {{"),
                    1,
                )
                self.assertIn(f"ZG361M: CASE {mechanism.id:03d}", effects)

    def test_org_climate_thresholds_do_not_read_unset_ledgers(self) -> None:
        effect_path = (
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_mechanism_effects.txt"
        )
        effects = self.rendered[effect_path].decode("utf-8-sig")
        climate = effects.split("zg361_refresh_org_climate_effect = {", 1)[1]
        expected = (
            ("trust", 20, "zg361_org_high_trust"),
            ("admin_load", 35, "zg361_org_admin_overload"),
            ("burnout", 20, "zg361_org_burnout_crisis"),
            ("stability", 20, "zg361_org_delivery_stable"),
            ("tech_debt", 20, "zg361_org_tech_debt_crisis"),
            ("talent", 20, "zg361_org_talent_healthy"),
        )
        for ledger, threshold, modifier in expected:
            variable = f"zg361_org_{ledger}"
            guarded = (
                "\tif = {\n"
                "\t\tlimit = {\n"
                "\t\t\ttrigger_if = {\n"
                f"\t\t\t\tlimit = {{ has_variable = {variable} }}\n"
                f"\t\t\t\tvar:{variable} >= {threshold}\n"
                "\t\t\t}\n"
                "\t\t\ttrigger_else = { always = no }\n"
                "\t\t}\n"
                f"\t\tadd_character_modifier = {{ modifier = {modifier} years = 1 }}\n"
                "\t}"
            )
            with self.subTest(ledger=ledger):
                self.assertIn(guarded, climate)
                self.assertNotIn(
                    f"\t\tlimit = {{ var:{variable} >= {threshold} }}", climate
                )

    def test_policy_localization_renders_ids_and_line_breaks_literally(self) -> None:
        chinese_path = (
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / "zg361_mechanisms_l_simp_chinese.yml"
        )
        english_path = (
            MOD_ROOT
            / "localization"
            / "english"
            / "zg361_mechanisms_l_english.yml"
        )
        chinese = self.rendered[chinese_path].decode("utf-8-sig")
        english = self.rendered[english_path].decode("utf-8-sig")
        self.assertIn('zg361m.1.t:0 "第001号 · KPI 分项证据单"', chinese)
        self.assertIn('zg361m.1.t:0 "No.001 · Itemized KPI Evidence Sheet"', english)
        self.assertIn(r"／P0】\n\n决策：", chinese)
        self.assertNotIn(r"\\n", chinese)
        for path, rendered in self.rendered.items():
            if path.name.startswith("zg361_mechanisms_l_"):
                text = rendered.decode("utf-8-sig")
                title_lines = [
                    line
                    for line in text.splitlines()
                    if line.startswith(" zg361m.") and ".t:0 " in line
                ]
                with self.subTest(language=path.parent.name):
                    self.assertEqual(len(title_lines), 361)
                    self.assertFalse(any(':0 "#' in line for line in title_lines))

    def test_machine_manifest_maps_every_id(self) -> None:
        manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
        manifest = json.loads(self.rendered[manifest_path].decode("utf-8"))
        self.assertEqual(manifest["schema"], 3)
        self.assertEqual(manifest["mechanism_count"], 361)
        self.assertEqual([item["id"] for item in manifest["items"]], list(range(1, 362)))
        self.assertEqual({item["live_wave"] for item in manifest["items"]}, {1, 2, 3, 4})
        legacy_status = {
            "catalogue": "complete",
            "policy_configuration": "fixture-live",
            "ledger_projection": "fixture-live",
            "domain_runtime": "not-implemented",
            "player_visible_loop": "partial",
        }
        phase2_status = {
            **legacy_status,
            "domain_runtime": "partial",
            "runtime_evidence": "static-ready",
        }
        phase2_ids = {int(mechanism_id) for mechanism_id in PHASE2_RUNTIME_SPECS}
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        for item in manifest["items"]:
            self.assertEqual(len(item["implementation"]["choice_effects"]), 3)
            expected_status = phase2_status if item["id"] in phase2_ids else legacy_status
            self.assertEqual(item["status"], expected_status)
            self.assertNotIsInstance(item["status"], str)
            if item["id"] in phase2_ids:
                self.assertIsInstance(item["runtime_contract"], dict)
                self.assertEqual(
                    set(item["runtime_contract"]),
                    {
                        "object_type",
                        "owner_binding",
                        "subject_binding",
                        "cycle_binding",
                        "case_binding",
                        "hook",
                        "states",
                        "feedback",
                        "permissions",
                    },
                )
            else:
                self.assertNotIn("runtime_contract", item)
                self.assertNotIn("runtime_evidence", item["status"])
            self.assertEqual(
                tuple(item["acceptance_contract"]), ACCEPTANCE_FIELDS
            )
            self.assertEqual(
                item["acceptance_contract"],
                mechanisms_by_id[item["id"]].acceptance_contract.manifest_payload(),
            )
        self.assertEqual(
            manifest["acceptance"]["run_id"],
            "zga_20260829_061314_ea5f04ad",
        )
        self.assertIn(
            "1083",
            manifest["acceptance"]["claim_boundary"],
        )
        self.assertEqual(manifest["phase2_static"]["mechanism_ids"], [1, 18, 69, 357])
        self.assertEqual(manifest["phase2_static"]["evidence"], "static-ready")
        self.assertIn("do not prove CK3", manifest["phase2_static"]["claim_boundary"])

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in self.rendered.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
