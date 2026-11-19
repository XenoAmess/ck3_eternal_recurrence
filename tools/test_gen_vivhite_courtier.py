#!/usr/bin/env python3
"""Protect the independent CK3 1.21.0 Vivhite metadata and text contracts."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest import mock

import gen_vivhite_courtier as generator
import validate_vivhite_static as validator


def copy_localization_fixture(source: Path, target: Path) -> None:
    """Copy the real localization-check input closure without PNG/DDS assets."""
    paths = list((source / "localization").rglob("*.yml"))
    paths.append(source / "gui/ervc_courtier_creator.gui")
    for path in paths:
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())


class VivhiteNativeContractTests(unittest.TestCase):
    def test_snapshot_boundary_rejects_numeric_type_confusion_and_missing_fields(self) -> None:
        original = generator.SNAPSHOT.read_text(encoding="utf-8-sig")
        mutations = (
            ("schema_version", True), ("schema_version", 1.0),
            ("trait_count", 311.0), ("trait_count", True),
            ("ruler_designer_cost", True), ("minimum_age", 16.0),
            ("physical", 1), ("opposites", [1]),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "traits.json"
            for key, value in mutations:
                payload = json.loads(original)
                target = payload if key in {"schema_version", "trait_count"} else payload["traits"][0]
                target[key] = value
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    generator.load_snapshot(path)
            payload = json.loads(original)
            del payload["traits"][0]["maximum_age"]
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing"):
                generator.load_snapshot(path)

    def test_new_scholar_is_distinct_from_renamed_erudite(self):
        _, traits = generator.load_snapshot()
        by_key = {trait["key"]: trait for trait in traits}
        self.assertNotIn("scholar", by_key)
        self.assertEqual(by_key["erudite"]["ruler_designer_cost"], 50)
        self.assertEqual(by_key["lifestyle_scholar"]["ruler_designer_cost"], 15)
        self.assertEqual(by_key["lifestyle_scholar"]["minimum_age"], 16)
        self.assertTrue(by_key["lifestyle_scholar"]["has_track"])
        self.assertEqual(by_key["herald"]["ruler_designer_cost"], 100)
        _, union = generator.build_catalogs(traits)
        self.assertEqual(len(union), 230)
        self.assertTrue({"cleric", "debug_enable_raiding_without_restrictions",
                         "debug_enable_raiding_per_standard_restrictions"}.isdisjoint(
                             {trait["key"] for trait in union}))

    def test_independent_old_snapshot_cannot_regenerate_new_product(self):
        self.assertEqual(generator.SNAPSHOT.name, "vivhite_courtier_traits_1_21_0.json")
        for filename in ("vivhite_courtier_traits_1_19_0_6.json", "vivhite_courtier_traits_1_20_0_3.json"):
            with self.subTest(filename=filename), self.assertRaisesRegex(ValueError, "source game version"):
                generator.load_snapshot(generator.SNAPSHOT.with_name(filename))

    def test_florin_catalog_keeps_hidden_traits_and_education_boundary(self):
        _, traits = generator.load_snapshot()
        catalogs, union = generator.build_catalogs(traits)
        self.assertEqual(len(traits), 311)
        self.assertEqual({name: len(items) for name, items in catalogs.items()},
                         {"education": 25, "commander": 17, "physical": 38,
                          "personality": 36, "other": 114})
        keys = {trait["key"] for trait in union}
        self.assertTrue({"devoted", "merchant_associate", "lifestyle_merchant", "dealbreaker"} <= keys)
        self.assertTrue({"adopted_no_inheritance", "education_republican_knowledge_5"}.isdisjoint(keys))
        self.assertEqual(sum(trait["shown_in_ruler_designer"] for trait in traits), 229)

    def test_florin_prices_age_and_merchant_replacement_reach_generated_consumers(self):
        _, traits = generator.load_snapshot()
        by_key = {trait["key"]: trait for trait in traits}
        catalogs, union = generator.build_catalogs(traits)
        conflicts = generator.build_conflicts(traits, union)
        self.assertEqual(len(generator.conflict_pairs(union, conflicts)), 96)
        self.assertEqual(conflicts["merchant_associate"], ["lifestyle_merchant"])
        self.assertEqual(conflicts["lifestyle_merchant"], ["merchant_associate"])
        for key, cost in (("devoted", 0), ("merchant_associate", 10),
                          ("lifestyle_merchant", 10), ("dealbreaker", 10)):
            self.assertEqual(by_key[key]["ruler_designer_cost"], cost)
        for key in ("lifestyle_merchant", "dealbreaker"):
            self.assertEqual(by_key[key]["minimum_age"], 16)
            self.assertIn("var:ervc_cc_age >= 16", generator.metadata_checks(by_key[key]))
        self.assertTrue(by_key["lifestyle_merchant"]["has_track"])
        self.assertTrue(by_key["devoted"]["has_track"])
        effects = generator.generated_effects(catalogs, union, conflicts)
        self.assertIn("ervc_cc_remove_selected_trait_effect = { ervc_trait = trait:merchant_associate }", effects)
        self.assertIn("ervc_cc_remove_selected_trait_effect = { ervc_trait = trait:lifestyle_merchant }", effects)
        values = generator.generated_values(union)
        triggers = generator.generated_triggers(union, conflicts)
        for key in ("devoted", "merchant_associate", "lifestyle_merchant", "dealbreaker"):
            self.assertIn("trait:" + key, values)
            self.assertIn("trait:" + key, triggers)

    def test_florin_fixture_keeps_both_current_catalogs_and_their_product_prefixes(self):
        import prepare_courtier_1_20_fixture as fixture
        standalone = fixture.extra_ui_effects("ervc")
        original = fixture.extra_ui_effects("xar")
        self.assertIn("name = ervc_cc_catalog_other value = 114", standalone)
        self.assertIn("CCA120: PASS florin_trait_catalog", standalone)
        self.assertIn("name = xar_cc_catalog_other value = 114", original)
        self.assertIn("CCA120: PASS florin_trait_catalog", original)
        for key in ("devoted", "merchant_associate", "lifestyle_merchant", "dealbreaker"):
            self.assertIn("trait:" + key, standalone)
        for marker in ("new_trait_catalog", "legacy_same_faith_rite", "legacy_other_faith_main_rite"):
            self.assertIn("CCA120: PASS " + marker, standalone)
            self.assertIn("CCA120: PASS " + marker, original)

    def test_localization_gate_does_not_read_live_original_product(self):
        with tempfile.TemporaryDirectory() as name, mock.patch.object(
                validator, "ORIGINAL_MOD", Path(name) / "absent-original"):
            errors = []
            validator.localization_checks(errors, {})
        self.assertEqual(errors, [])

    def test_localization_contract_rejects_unreviewed_refresh(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "contract.json"
            path.write_bytes(validator.LOCALIZATION_CONTRACT.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SHA-256 changed"):
                validator.load_localization_contract(path)

    def test_independent_contract_still_rejects_chinese_localization_drift(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "source"
            copy_localization_fixture(validator.MOD, source)
            path = source / "localization/simp_chinese/ervc_l_simp_chinese.yml"
            data = path.read_text(encoding="utf-8-sig")
            lines = data.splitlines()
            for index, line in enumerate(lines):
                if line.lstrip().startswith("ervc.cc.origin.help:"):
                    lines[index] = line[:-1] + "正文变化999\""
            path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
            with mock.patch.object(validator, "MOD", source):
                errors = []
                validator.localization_checks(errors, {})
        self.assertTrue(any("independent frozen contract" in error and "origin.help" in error
                            for error in errors), errors)
        self.assertTrue(any("numeric literal mismatch" in error and "origin.help" in error
                            for error in errors), errors)

    def test_non_chinese_prose_and_numbers_are_format_only(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "source"
            copy_localization_fixture(validator.MOD, source)
            for language in validator.LANGUAGES:
                if language == "simp_chinese":
                    continue
                path = source / f"localization/{language}/ervc_l_{language}.yml"
                lines = path.read_text(encoding="utf-8-sig").splitlines()
                for index, line in enumerate(lines):
                    if line.lstrip().startswith(tuple(validator.EXPECTED_LOC_KEYS)):
                        lines[index] = line[:-1] + " Changed text 777\""
                path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
            with mock.patch.object(validator, "MOD", source):
                errors = []
                validator.localization_checks(errors, {})
            self.assertEqual(errors, [])

    def test_non_chinese_english_copy_is_valid_format(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "source"
            copy_localization_fixture(validator.MOD, source)
            english = (source / "localization/english/ervc_l_english.yml").read_bytes()
            for language in validator.OTHER_LANGUAGES:
                path = source / f"localization/{language}/ervc_l_{language}.yml"
                path.write_bytes(english.replace(b"l_english:", f"l_{language}:".encode(), 1))
            with mock.patch.object(validator, "MOD", source):
                errors = []
                validator.localization_checks(errors, {})
            self.assertEqual(errors, [])

    def test_non_chinese_format_drift_is_rejected(self):
        mutations = {
            "missing_key": lambda data: b"\n".join(
                line for line in data.split(b"\n")
                if not line.lstrip().startswith(b"ervc.cc.origin.help:")
            ),
            "protected_token": lambda data: data.replace(b"$trait_impotent$", b"impotent"),
            "header": lambda data: data.replace(b"l_french:", b"l_german:", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as name:
                source = Path(name) / "source"
                copy_localization_fixture(validator.MOD, source)
                path = source / "localization/french/ervc_l_french.yml"
                path.write_bytes(mutate(path.read_bytes()))
                with mock.patch.object(validator, "MOD", source):
                    errors = []
                    validator.localization_checks(errors, {})
                expected = {
                    "missing_key": "exact 45 standalone keys",
                    "protected_token": "protected localization token mismatch",
                    "header": "must begin exactly with l_french:",
                }[label]
                self.assertTrue(any(expected in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
