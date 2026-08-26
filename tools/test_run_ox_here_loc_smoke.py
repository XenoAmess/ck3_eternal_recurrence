#!/usr/bin/env python3
"""Offline contract tests for the Ox Here localization smoke runner."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from PIL import Image

import run_acceptance as acceptance
import run_ox_here_loc_smoke as smoke


class LocalizationContractTests(unittest.TestCase):
    def test_language_matrix_is_exact_and_complete(self) -> None:
        self.assertEqual(
            [spec.key for spec in smoke.LANGUAGES],
            [
                "l_english",
                "l_french",
                "l_german",
                "l_polish",
                "l_japanese",
                "l_spanish",
                "l_simp_chinese",
                "l_russian",
                "l_korean",
            ],
        )
        matrix = smoke.localization_matrix(smoke.CANONICAL_SOURCE)
        self.assertEqual(set(matrix), set(smoke.LANGUAGE_BY_KEY))
        self.assertEqual(len(smoke.EXPECTED_LOC_KEYS), 20)
        for values in matrix.values():
            self.assertEqual(frozenset(values), smoke.EXPECTED_LOC_KEYS)
            self.assertEqual(
                values["ox_here_recruit_tooltip"],
                values["ox_here_decision_option_recruit_desc"],
            )
            self.assertEqual(
                values["ox_here_decline_tooltip"],
                values["ox_here_decision_option_decline_desc"],
            )
        self.assertEqual(smoke.localization_errors(smoke.CANONICAL_SOURCE), [])

    def test_fixture_anchors_are_unique_ascii_and_exact_per_locale(self) -> None:
        expected = {
            "l_english": "LOC SMOKE ENGLISH",
            "l_french": "LOC SMOKE FRENCH",
            "l_german": "LOC SMOKE GERMAN",
            "l_polish": "LOC SMOKE POLISH",
            "l_japanese": "LOC SMOKE JAPANESE",
            "l_spanish": "LOC SMOKE SPANISH",
            "l_simp_chinese": "LOC SMOKE CHINESE",
            "l_russian": "LOC SMOKE RUSSIAN",
            "l_korean": "LOC SMOKE KOREAN",
        }
        anchors = [spec.anchor for spec in smoke.LANGUAGES]
        self.assertEqual(len(anchors), len(set(anchors)))
        for spec in smoke.LANGUAGES:
            self.assertEqual(spec.anchor, expected[spec.key])
            self.assertTrue(spec.anchor.isascii())
            values = smoke.parse_localization(
                smoke.FIXTURE_SOURCE / spec.fixture_localization_path,
                spec.key,
            )
            self.assertEqual(
                frozenset(values), smoke.EXPECTED_FIXTURE_LOC_KEYS
            )
            self.assertEqual(values["oxls_anchor_decision"], spec.anchor)
            self.assertEqual(
                values["oxls_anchor_decision_confirm"], "DO NOT CLICK"
            )

    def test_product_and_fixture_sources_are_clean(self) -> None:
        self.assertEqual(
            smoke.product_source_errors(smoke.CANONICAL_SOURCE, None), []
        )
        self.assertEqual(smoke.fixture_source_errors(), [])

    def test_fixture_registers_the_gui_file_and_window_name(self) -> None:
        registry = (
            smoke.FIXTURE_SOURCE
            / "gui"
            / "scripted_widgets"
            / "oxls_scripted_widgets.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertEqual(
            registry.strip(), "gui/oxls_bridge.gui = oxls_bridge_window"
        )

    def test_delivery_observer_is_idempotent_at_effect_execution(self) -> None:
        observer = (
            smoke.FIXTURE_SOURCE
            / "common"
            / "scripted_guis"
            / "oxls_guis.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertIn(
            "NOT = { has_character_flag = oxls_delivery_reported }", observer
        )
        self.assertIn("add_character_flag = oxls_delivery_reported", observer)
        self.assertEqual(observer.count(smoke.DELIVERY_MARKER), 1)

    def test_render_settings_selects_one_language_and_disables_prompts(self) -> None:
        for spec in smoke.LANGUAGES:
            text = smoke.render_settings(spec.key)
            self.assertEqual(text.count('"language"='), 1)
            self.assertEqual(text.count(f'value="{spec.key}"'), 1)
            self.assertIn('"promt_for_tutorial"={ version=0 enabled=no }', text)
            self.assertIn(
                '"prompt_for_china_tutorial"={ version=0 enabled=no }', text
            )
            self.assertEqual(smoke.configured_language_from_text(text), spec.key)
        with self.assertRaises(ValueError):
            smoke.render_settings("l_not_a_ck3_language")


class DescriptorNormalizationTests(unittest.TestCase):
    def test_canonical_descriptor_is_byte_preserved(self) -> None:
        data = b'version="1.0.2"\nsupported_version="1.19.0.6"\n'
        self.assertEqual(smoke.normalized_descriptor_bytes(data, None), data)

    def test_workshop_identity_is_removed_only_from_final_canonical_line(self) -> None:
        body = b'version="1.0.2"\nsupported_version="1.19.0.6"\n'
        injected = body + b'remote_file_id="3799999999"\n'
        self.assertEqual(
            smoke.normalized_descriptor_bytes(injected, "3799999999"), body
        )

    def test_descriptor_rejects_wrong_duplicate_or_nonfinal_identity(self) -> None:
        wrong = b'version="1.0.2"\nremote_file_id="3799999998"\n'
        duplicate = (
            b'version="1.0.2"\nremote_file_id="3799999999"\n'
            b'remote_file_id="3799999999"\n'
        )
        nonfinal = b'remote_file_id="3799999999"\nversion="1.0.2"\n'
        for data in (wrong, duplicate, nonfinal):
            with self.subTest(data=data):
                with self.assertRaises(acceptance.RunnerError):
                    smoke.normalized_descriptor_bytes(data, "3799999999")

    def test_canonical_mode_rejects_any_workshop_identity(self) -> None:
        with self.assertRaises(acceptance.RunnerError):
            smoke.normalized_descriptor_bytes(
                b'version="1.0.2"\nremote_file_id="3799999999"\n', None
            )


class SurfaceEvidenceTests(unittest.TestCase):
    def test_raw_key_rejection_does_not_reject_the_english_title(self) -> None:
        self.assertEqual(smoke.unresolved_product_keys(["Ox Here!"]), [])
        hits = smoke.unresolved_product_keys(
            ["ox_here_", "arrival_event_title"]
        )
        self.assertIn("ox_here_arrival_event_title", hits)

    def test_known_localization_keys_are_rejected(self) -> None:
        hits = smoke.unresolved_product_keys(
            [
                "The label is ox_here_decision_option_recruit",
                "ox_here_recruit_tooltip",
                "ox_here_decline_tooltip",
            ]
        )
        self.assertIn("ox_here_decision_option_recruit", hits)
        self.assertIn("ox_here_recruit_tooltip", hits)
        self.assertIn("ox_here_decline_tooltip", hits)

    def test_ocr_row_match_is_unicode_and_punctuation_tolerant(self) -> None:
        rows = [
            {"text": "¡Buey, ven!", "center": [123, 456]},
            {"text": "LOC SMOKE ENGLISH", "center": [800, 900]},
        ]
        self.assertEqual(smoke.find_ocr_row(rows, "Buey ven"), (123, 456))
        self.assertIsNone(smoke.find_ocr_row(rows, "Вол, приди!"))

    def test_exact_product_title_beats_containing_group_header(self) -> None:
        rows = [
            {"text": "Ox Here (2)", "center": [1874, 695]},
            {"text": "LOC SMOKE ENGLISH", "center": [1895, 756]},
            {"text": "Ox Here!", "center": [1839, 835]},
        ]
        self.assertEqual(smoke.find_ocr_row(rows, "Ox Here!"), (1839, 835))

    def test_changed_pixel_fraction_detects_large_surface_transition(self) -> None:
        first = Image.new("RGB", (256, 144), "black")
        same = Image.new("RGB", (256, 144), "black")
        changed = Image.new("RGB", (256, 144), "white")
        self.assertEqual(smoke.changed_pixel_fraction(first, same), 0.0)
        self.assertGreater(smoke.changed_pixel_fraction(first, changed), 0.9)

    def test_changed_pixel_fraction_can_gate_the_option_response_roi(self) -> None:
        first = Image.new("RGB", (100, 100), "black")
        outside = first.copy()
        for x in range(0, 20):
            for y in range(0, 20):
                outside.putpixel((x, y), (255, 255, 255))
        inside = first.copy()
        for x in range(35, 45):
            for y in range(35, 45):
                inside.putpixel((x, y), (255, 255, 255))
        region = (0.30, 0.30, 0.60, 0.60)
        self.assertEqual(
            smoke.changed_pixel_fraction(first, outside, region), 0.0
        )
        self.assertGreater(
            smoke.changed_pixel_fraction(first, inside, region), 0.10
        )

    def test_changed_pixel_fraction_rejects_an_empty_region(self) -> None:
        image = Image.new("RGB", (100, 100), "black")
        with self.assertRaisesRegex(ValueError, "invalid changed-pixel region"):
            smoke.changed_pixel_fraction(image, image, (0.5, 0.5, 0.5, 0.8))

    def test_wrong_language_anchor_cannot_prove_active_language(self) -> None:
        english = smoke.LANGUAGE_BY_KEY["l_english"]
        french = smoke.LANGUAGE_BY_KEY["l_french"]
        wrong_rows = [{"text": french.anchor, "center": [800, 900]}]
        with self.assertRaisesRegex(
            acceptance.RunnerError, "active-language anchor proof failed"
        ):
            smoke.prove_active_language_anchor(wrong_rows, english)
        proof = smoke.prove_active_language_anchor(
            [{"text": english.anchor, "center": [801, 901]}], english
        )
        self.assertEqual(proof["expected_anchor"], english.anchor)
        self.assertEqual(proof["center"], [801, 901])


class ModeContractTests(unittest.TestCase):
    def test_workshop_mode_requires_manifest_before_environment_access(self) -> None:
        with mock.patch.object(
            smoke.terminal,
            "steam_userdata_root",
            side_effect=AssertionError("environment must not be touched"),
        ):
            with self.assertRaisesRegex(
                acceptance.RunnerError, "--workshop-cache requires --manifest"
            ):
                smoke.main(
                    workshop_cache=r"Z:\fake\1158310\3799999999",
                    manifest_path=None,
                    preflight_only=True,
                )

    def test_manifest_without_workshop_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            acceptance.RunnerError, "--manifest requires --workshop-cache"
        ):
            smoke.validate_mode_arguments(None, r"Z:\fake\manifest.json")


class BootstrapTests(unittest.TestCase):
    def test_copy_product_runtime_uses_exact_release_inventory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oxls-copy-test-") as name:
            target = Path(name) / "product"
            files = smoke.copy_product_runtime(
                smoke.CANONICAL_SOURCE, target, workshop_item_id=None
            )
            self.assertEqual(files, sorted(smoke.build_ox_here_release.RUNTIME_FILES))
            actual = {
                path.relative_to(target).as_posix()
                for path in target.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, set(smoke.build_ox_here_release.RUNTIME_FILES))
            self.assertNotIn(
                b"remote_file_id", (target / "descriptor.mod").read_bytes()
            )

    def test_bootstrap_writes_language_and_exact_load_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oxls-bootstrap-test-") as name:
            userdir = Path(name) / "userdir"
            details = smoke.bootstrap_userdir(
                userdir,
                smoke.CANONICAL_SOURCE,
                workshop_item_id=None,
                language="l_korean",
            )
            self.assertEqual(
                json.loads((userdir / "dlc_load.json").read_text(encoding="utf-8"))[
                    "enabled_mods"
                ],
                [f"mod/{smoke.PRODUCT_OUTER}", f"mod/{smoke.FIXTURE_OUTER}"],
            )
            self.assertEqual(
                smoke.configured_language(userdir / "pdx_settings.txt"),
                "l_korean",
            )
            self.assertEqual(
                set(details["targets"]), {"product", "fixture"}
            )
            product_descriptor = (
                Path(details["targets"]["product"]) / "descriptor.mod"
            )
            self.assertNotIn(b"remote_file_id", product_descriptor.read_bytes())

    def test_launcher_injected_cache_is_accepted_then_normalized(self) -> None:
        item_id = "3799999999"
        with tempfile.TemporaryDirectory(prefix="oxls-cache-test-") as name:
            cache = Path(name) / item_id
            cache.mkdir()
            for relative in smoke.build_ox_here_release.RUNTIME_FILES:
                source = smoke.CANONICAL_SOURCE / relative
                target = cache / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            descriptor = cache / "descriptor.mod"
            descriptor.write_bytes(
                descriptor.read_bytes().rstrip(b"\r\n")
                + f'\nremote_file_id="{item_id}"\n'.encode("ascii")
            )
            self.assertEqual(smoke.product_source_errors(cache, item_id), [])
            normalized = Path(name) / "normalized"
            smoke.copy_product_runtime(cache, normalized, item_id)
            self.assertEqual(
                (normalized / "descriptor.mod").read_bytes(),
                (smoke.CANONICAL_SOURCE / "descriptor.mod").read_bytes(),
            )
            self.assertEqual(
                smoke.product_source_errors(normalized, None), []
            )


if __name__ == "__main__":
    unittest.main()
