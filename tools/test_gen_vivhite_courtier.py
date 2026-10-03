#!/usr/bin/env python3
"""Protect the independent CK3 1.20.0.3 Vivhite metadata and text contracts."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import gen_vivhite_courtier as generator
import validate_vivhite_static as validator


class VivhiteNativeContractTests(unittest.TestCase):
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
        self.assertEqual(len(union), 226)
        self.assertTrue({"cleric", "debug_enable_raiding_without_restrictions",
                         "debug_enable_raiding_per_standard_restrictions"}.isdisjoint(
                             {trait["key"] for trait in union}))

    def test_independent_old_snapshot_cannot_regenerate_new_product(self):
        self.assertEqual(generator.SNAPSHOT.name, "vivhite_courtier_traits_1_20_0_3.json")
        with self.assertRaisesRegex(ValueError, "source game version"):
            generator.load_snapshot(generator.SNAPSHOT.with_name("vivhite_courtier_traits_1_19_0_6.json"))

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
            shutil.copytree(validator.MOD, source)
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
            shutil.copytree(validator.MOD, source)
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
            shutil.copytree(validator.MOD, source)
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
                shutil.copytree(validator.MOD, source)
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
