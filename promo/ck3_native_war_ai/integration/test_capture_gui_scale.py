"""Pure profile-rendering checks; never launches CK3."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from capture_session import (A04_UI_GUI_BLOCK_BYTES, A04_UI_GUI_BLOCK_SHA256,
                             gui_scale_disk_readback, normalize_gui_scale_ratio,
                             render_profile_settings,
                             require_gui_scale_disk_gate,
                             reseed_gui_scale_after_warmup, write_profile_settings)


class CaptureGuiScaleTest(unittest.TestCase):
    def test_native_ui_saved_one_needs_explicit_future_run_opt_in(self) -> None:
        # The complete a04 Save and Close source stays outside the repository:
        # 6891 B, SHA-256 E6AD4D44...FDF7D; only its GUI block is needed here.
        source = b'"GUI"={\r\n\t"scale"={\r\n\t\tversion=1\r\n\t\tvalue="1"\r\n\t}\r\n}\r\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "pdx_settings.txt"
            settings.write_bytes(source)
            default = gui_scale_disk_readback(settings, "1.0", "a04-diagnostic")
            self.assertEqual(default["observed_scale_token"], 'value="1"')
            self.assertEqual(default["observed_scale_ratio"], "1")
            self.assertTrue(default["ratio_equivalent_to_request"])
            self.assertFalse(default["disk_gate_passed"])
            self.assertEqual(default["reason"], "ratio_equal_but_literal_not_admitted")
            admitted = gui_scale_disk_readback(settings, "1.0", "future-candidate",
                                               allow_native_ui_one=True)
            self.assertTrue(admitted["disk_gate_passed"])
            self.assertEqual(admitted["admission"], "explicit_native_ui_one")
            self.assertFalse(admitted["runtime_scale_proven"])
            self.assertFalse(admitted["recording_authorized_by_this_gate"])
            receipt_path = root / "future-candidate-gate.json"
            require_gui_scale_disk_gate(settings, "1.0", "future-candidate",
                                        receipt_path, allow_native_ui_one=True)
            self.assertTrue(json.loads(receipt_path.read_text())["disk_gate_passed"])

    def test_real_a03_warmup_6861_byte_reseed_changes_only_gui_value(self) -> None:
        # Exact, unnormalized bytes from the immutable E2-04 a03 warm-up profile.
        fixture = (Path(__file__).parent / "fixtures" /
                   "e2-04-a03-warmup-pdx-settings.bin")
        source = fixture.read_bytes()
        self.assertEqual(len(source), 6861)
        self.assertEqual(hashlib.sha256(source).hexdigest().upper(),
                         "2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509")
        old_value = b'value="1.3"'
        new_value = b'value="1.0"'
        self.assertEqual(source.count(old_value), 1)
        gui_offset = source.index(b'"GUI"={')
        value_offset = source.index(old_value, gui_offset)
        expected = source[:value_offset] + new_value + source[value_offset + len(old_value):]
        self.assertEqual(len(expected), len(source))
        self.assertEqual(hashlib.sha256(expected).hexdigest().upper(),
                         "A45FF273C54C4D1D0819FC756F6E8B336411AB71E147F24E5BC462057309E541")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            settings = root / "pdx_settings.txt"
            settings.write_bytes(source)
            reseed_gui_scale_after_warmup(settings, "1.0", output)
            actual = settings.read_bytes()
            self.assertEqual(actual, expected)
            self.assertEqual(actual[:value_offset], source[:value_offset])
            self.assertEqual(actual[value_offset + len(new_value):],
                             source[value_offset + len(old_value):])
            self.assertEqual((output / "gui-settings-warmup-before-reseed.pdx.txt").read_bytes(), source)
            before = json.loads((output / "gui-settings-before-final-launch.json").read_text())
            reseed = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
            after = json.loads((output / "gui-settings-after-reseed-before-final-launch.json").read_text())
            self.assertEqual(before["settings"]["sha256"],
                             "2191EA423B3B1A94CB7E905B6096F3D07BBF0B7F1668C3E0ED412297AEF2C509")
            self.assertFalse(before["disk_gate_passed"])
            self.assertEqual(reseed["status"], "GREEN_DISK_ONLY")
            self.assertEqual(reseed["expected_target"]["sha256"],
                             "A45FF273C54C4D1D0819FC756F6E8B336411AB71E147F24E5BC462057309E541")
            self.assertTrue(after["disk_gate_passed"])

    def test_default_keeps_exact_settings_bytes(self) -> None:
        base = '"Graphics"={\n\t"display_mode"={ version=0 value="fullscreen" }\n}\n'
        self.assertEqual(render_profile_settings(base, None), base)

    def test_requested_scale_has_one_exact_gui_block(self) -> None:
        base = '"Graphics"={}\n'
        actual = render_profile_settings(base, "1.0")
        self.assertEqual(actual, base + '"GUI"={\n\t"scale"={ version=1 value="1.0" }\n}\n')
        self.assertEqual(actual.count('"GUI"='), 1)

    def test_unsupported_or_duplicate_settings_fail_closed(self) -> None:
        with self.assertRaises(Exception):
            render_profile_settings('"Graphics"={}\n', "1.3")
        with self.assertRaises(Exception):
            render_profile_settings('"GUI"={}\n', "1.0")

    def test_requested_scale_freezes_exact_disk_bytes_and_sha(self) -> None:
        base = '"Graphics"={}\n'
        expected = render_profile_settings(base, "1.0").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pdx_settings.txt"
            receipt = write_profile_settings(path, base, "1.0")
            self.assertEqual(path.read_bytes(), expected)
            self.assertNotIn(b"\r\n", path.read_bytes())
            self.assertEqual(receipt["settings"]["sha256"], hashlib.sha256(expected).hexdigest().upper())
            self.assertEqual(receipt["expected_utf8_sha256"], hashlib.sha256(expected).hexdigest().upper())
            self.assertTrue(receipt["exact_utf8_disk_match"])
            with self.assertRaises(FileExistsError):
                write_profile_settings(path, base, "1.0")

    def test_default_keeps_existing_disk_write_behavior(self) -> None:
        base = '"Graphics"={}\n'
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pdx_settings.txt"
            old_behavior = Path(directory) / "old.txt"
            old_behavior.write_text(base, encoding="utf-8")
            receipt = write_profile_settings(target, base, None)
            self.assertEqual(target.read_bytes(), old_behavior.read_bytes())
            self.assertIsNone(receipt["exact_utf8_disk_match"])

    def test_default_has_no_scale_gate_or_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "not-created.json"
            require_gui_scale_disk_gate(Path(directory) / "missing.txt", None,
                                        "postmap-before-capture", receipt)
            self.assertFalse(receipt.exists())

    def test_postmap_ck3_rewrite_to_1_3_is_red_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "pdx_settings.txt"
            settings.write_bytes(b'"Graphics"={}\r\n"GUI"={\r\n\t"scale"={\r\n'
                                 b'\t\tversion=1\r\n\t\tvalue="1.3"\r\n\t}\r\n}\r\n')
            receipt = root / "gui-settings-postmap.json"
            with self.assertRaisesRegex(RuntimeError, "postmap-before-capture"):
                require_gui_scale_disk_gate(settings, "1.0", "postmap-before-capture", receipt)
            self.assertTrue(receipt.is_file())
            self.assertEqual(gui_scale_disk_readback(settings, "1.0", "test")["observed_scale"], "1.3")
            self.assertFalse(gui_scale_disk_readback(settings, "1.0", "test")["disk_gate_passed"])

    def test_native_ui_save_to_1_0_needs_separate_visual_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "pdx_settings.txt"
            settings.write_bytes(b'"Graphics"={}\r\n"GUI"={\r\n\t"scale"={\r\n'
                                 b'\t\tversion=1\r\n\t\tvalue="1"\r\n\t}\r\n}\r\n')
            result = gui_scale_disk_readback(settings, "1.0", "after-native-UI-save",
                                             allow_native_ui_one=True)
            self.assertTrue(result["disk_gate_passed"])
            self.assertEqual(result["schema"], "war-film-gui-scale-disk-gate/v2")
            self.assertEqual(result["observed_scale_serialized"], "1")
            self.assertEqual(result["observed_scale_token"], 'value="1"')
            self.assertEqual(result["observed_scale_ratio"], "1")
            self.assertEqual(result["requested_scale_ratio"], "1")
            self.assertFalse(result["runtime_scale_proven"])
            self.assertFalse(result["visual_geometry_reviewed"])
            self.assertFalse(result["recording_authorized_by_this_gate"])

    def test_decimal_normalization_is_diagnostic_until_literal_admitted(self) -> None:
        for value in ("1", "1.0", "1.00", "1.000000"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                settings = Path(directory) / "pdx_settings.txt"
                settings.write_bytes((f'"GUI"={{"scale"={{version=1 value="{value}"}}}}\n').encode("ascii"))
                result = gui_scale_disk_readback(settings, "1.0", "test")
                self.assertEqual(result["observed_scale_serialized"], value)
                self.assertEqual(result["observed_scale_ratio"], "1")
                self.assertTrue(result["ratio_equivalent_to_request"])
                self.assertEqual(result["disk_gate_passed"], value == "1.0")
                opted_in = gui_scale_disk_readback(settings, "1.0", "test",
                                                    allow_native_ui_one=True)
                self.assertEqual(opted_in["disk_gate_passed"], value in ("1", "1.0"))

    def test_noncanonical_numeric_forms_remain_red(self) -> None:
        for value in ("1e0", "+1", "01", "1.", " 1", "1,0", "NaN",
                      "Infinity", "0", "0.0", "1.0.0", "1%", ""):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                settings = Path(directory) / "pdx_settings.txt"
                settings.write_bytes((f'"GUI"={{"scale"={{version=1 value="{value}"}}}}\n').encode("ascii"))
                result = gui_scale_disk_readback(settings, "1.0", "test",
                                                 allow_native_ui_one=True)
                self.assertEqual(result["observed_scale_serialized"], value)
                self.assertIsNone(result["observed_scale_ratio"])
                self.assertFalse(result["disk_gate_passed"])
                self.assertEqual(normalize_gui_scale_ratio(value), None)

    def test_native_ui_opt_in_must_be_boolean(self) -> None:
        for value in (0, 1, "true", None):
            with self.subTest(value=value), self.assertRaisesRegex(RuntimeError, "must be boolean"):
                gui_scale_disk_readback(Path("missing.txt"), "1.0", "test",
                                        allow_native_ui_one=value)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "requires an explicit"):
                require_gui_scale_disk_gate(Path("missing.txt"), None, "test",
                                            Path(directory) / "not-created.json",
                                            allow_native_ui_one=True)

    def test_ambiguous_gui_or_scale_fields_remain_red(self) -> None:
        variants = (
            b'"GUI"={"scale"={version=1 value="1"}}\n"GUI"=bad\n',
            b'"GUI"={"scale"={version=1 value="1"}}\n  "GUI"=bad\n',
            b'  "GUI"={"scale"={version=1 value="1.0"}}\n',
            b'"GUI"={"scale"={version=1 value="1"} "scale"={version=1 value="1"}}\n',
            b'"GUI"={"scale"={version=1 value="1" value="1"}}\n',
            b'"GUI"={"scale"={version=1 version=1 value="1"}}\n',
            b'"GUI"={"scale"={version=1 value=1}}\n',
            b'"GUI"={"scale"={version=2 value="1"}}\n',
        )
        for raw in variants:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                settings = Path(directory) / "pdx_settings.txt"
                settings.write_bytes(raw)
                result = gui_scale_disk_readback(settings, "1.0", "test",
                                                 allow_native_ui_one=True)
                self.assertFalse(result["disk_gate_passed"])
                self.assertIsNone(result["observed_scale_ratio"])

    def test_missing_or_duplicate_gui_block_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "pdx_settings.txt"
            for raw in (b'"Graphics"={}\n',
                        b'"GUI"={"scale"={version=1 value="1.0"}}\n'
                        b'"GUI"={"scale"={version=1 value="1.0"}}\n'):
                settings.write_bytes(raw)
                self.assertFalse(gui_scale_disk_readback(settings, "1.0", "test")["disk_gate_passed"])

    def test_warmup_reseed_preserves_complete_settings_except_scale_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            settings = root / "pdx_settings.txt"
            source = (b'\xef\xbb\xbf"Graphics"={\r\n\t"display_mode"={ value="fullscreen" }\r\n}\r\n'
                      b'"GUI"={\r\n\t"scale"={\r\n\t\tversion=1\r\n'
                      b'\t\tvalue="1.3"\r\n\t}\r\n}\r\n'
                      b'"Audio"={\r\n\t"music"={ value="1.3" }\r\n}\r\n')
            settings.write_bytes(source)
            reseed_gui_scale_after_warmup(settings, "1.0", output)
            target = source.replace(b'value="1.3"\r\n\t}', b'value="1.0"\r\n\t}', 1)
            self.assertEqual(settings.read_bytes(), target)
            self.assertEqual((output / "gui-settings-warmup-before-reseed.pdx.txt").read_bytes(), source)
            before = json.loads((output / "gui-settings-before-final-launch.json").read_text())
            receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
            after = json.loads((output / "gui-settings-after-reseed-before-final-launch.json").read_text())
            self.assertEqual(before["observed_scale"], "1.3")
            self.assertFalse(before["disk_gate_passed"])
            self.assertEqual(before["settings"]["sha256"], hashlib.sha256(source).hexdigest().upper())
            self.assertEqual(receipt["status"], "GREEN_DISK_ONLY")
            self.assertTrue(receipt["replacement_performed"])
            self.assertTrue(receipt["atomic_same_directory_replace"])
            self.assertFalse(receipt["runtime_scale_proven"])
            self.assertFalse(receipt["recording_authorized_by_this_receipt"])
            self.assertTrue(after["disk_gate_passed"])
            self.assertEqual(after["settings"]["sha256"], hashlib.sha256(target).hexdigest().upper())

    def test_already_100_percent_is_preserved_without_replacement(self) -> None:
        cases = (("1.0", False, b'"Graphics"={}\r\n"GUI"={\r\n"scale"={ version=1 value="1.0" }\r\n}\r\n'),
                 ("1", True, b'"Graphics"={}\r\n' + A04_UI_GUI_BLOCK_BYTES))
        for serialized, allow_native_ui_one, source in cases:
            with self.subTest(serialized=serialized), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "evidence"
                output.mkdir()
                settings = root / "pdx_settings.txt"
                settings.write_bytes(source)
                reseed_gui_scale_after_warmup(settings, "1.0", output,
                                              allow_native_ui_one=allow_native_ui_one)
                receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
                self.assertEqual(settings.read_bytes(), source)
                self.assertFalse(receipt["replacement_performed"])
                self.assertEqual(receipt["before_observed_scale"], serialized)
                self.assertEqual(receipt["before_observed_scale_ratio"], "1")
                self.assertEqual(receipt["status"], "GREEN_DISK_ONLY")
                if allow_native_ui_one:
                    self.assertTrue(receipt["final_native_gui_block_exact"])
                    self.assertEqual(receipt["native_a04_gui_block_sha256"], A04_UI_GUI_BLOCK_SHA256)

    def test_reseed_rejects_unreviewed_equivalent_literal(self) -> None:
        for serialized, allow_native_ui_one in (("1", False), ("1.00", False),
                                                ("1.00", True), ("1.0", True)):
            with self.subTest(serialized=serialized, opt_in=allow_native_ui_one), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "evidence"
                output.mkdir()
                settings = root / "pdx_settings.txt"
                source = f'"GUI"={{"scale"={{version=1 value="{serialized}"}}}}\n'.encode("ascii")
                settings.write_bytes(source)
                with self.assertRaises(Exception):
                    reseed_gui_scale_after_warmup(settings, "1.0", output,
                                                  allow_native_ui_one=allow_native_ui_one)
                self.assertEqual(settings.read_bytes(), source)
                receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
                self.assertEqual(receipt["status"], "RED")
                self.assertFalse(receipt["replacement_performed"])

    def test_a05_warmup_130_restores_exact_native_block_and_preserves_other_bytes(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "e2-04-a03-warmup-pdx-settings.bin"
        source = fixture.read_bytes()
        warmup_block = A04_UI_GUI_BLOCK_BYTES.replace(b'value="1"', b'value="1.3"')
        self.assertEqual(source.count(warmup_block), 1)
        expected = source.replace(warmup_block, A04_UI_GUI_BLOCK_BYTES, 1)
        self.assertNotIn(b'value="1.0"', expected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            settings = root / "pdx_settings.txt"
            settings.write_bytes(source)
            reseed_gui_scale_after_warmup(settings, "1.0", output,
                                          allow_native_ui_one=True)
            self.assertEqual(settings.read_bytes(), expected)
            self.assertEqual((output / "gui-settings-warmup-before-reseed.pdx.txt").read_bytes(),
                             source)
            receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
            after = json.loads((output / "gui-settings-after-reseed-before-final-launch.json").read_text())
            self.assertEqual(receipt["source_snapshot"]["sha256"],
                             hashlib.sha256(source).hexdigest().upper())
            self.assertEqual(receipt["expected_target"]["sha256"],
                             hashlib.sha256(expected).hexdigest().upper())
            self.assertTrue(receipt["replacement_performed"])
            self.assertTrue(receipt["non_gui_bytes_unchanged"])
            self.assertTrue(receipt["final_native_gui_block_exact"])
            self.assertEqual(receipt["native_a04_gui_block_sha256"], A04_UI_GUI_BLOCK_SHA256)
            self.assertEqual(receipt["status"], "GREEN_DISK_ONLY")
            self.assertEqual(after["observed_scale_serialized"], "1")
            self.assertTrue(after["native_a04_gui_block_passed"])
            self.assertTrue(after["disk_gate_passed"])

    def test_a05_final_gate_rejects_synthetic_or_reformatted_100_percent(self) -> None:
        variants = (A04_UI_GUI_BLOCK_BYTES.replace(b'value="1"', b'value="1.0"'),
                    b'"GUI"={"scale"={version=1 value="1"}}\n')
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                settings = root / "pdx_settings.txt"
                settings.write_bytes(b'"Graphics"={}\n' + variant)
                receipt_path = root / "final-gate.json"
                with self.assertRaisesRegex(RuntimeError, "final-a05"):
                    require_gui_scale_disk_gate(
                        settings, "1.0", "final-a05", receipt_path,
                        allow_native_ui_one=True, require_native_a04_gui_block=True)
                receipt = json.loads(receipt_path.read_text())
                self.assertFalse(receipt["disk_gate_passed"])
                self.assertFalse(receipt["native_a04_gui_block_passed"])

    def test_ambiguous_or_unreviewed_gui_syntax_stays_red_and_unmodified(self) -> None:
        variants = (
            b'"Graphics"={}\n',
            b'"GUI"={"scale"={version=1 value="1.3"}}\n'
            b'"GUI"={"scale"={version=1 value="1.3"}}\n',
            b'"GUI"={"scale"={version=1 value="0.9"}}\n',
            b'"GUI"={"scale"={version=1 value="1.3"} "extra"=yes}\n',
        )
        for source in variants:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "evidence"
                output.mkdir()
                settings = root / "pdx_settings.txt"
                settings.write_bytes(source)
                with self.assertRaises(Exception):
                    reseed_gui_scale_after_warmup(settings, "1.0", output)
                self.assertEqual(settings.read_bytes(), source)
                receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
                self.assertEqual(receipt["status"], "RED")
                self.assertFalse(receipt["replacement_performed"])

    def test_replace_failure_leaves_source_and_no_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            settings = root / "pdx_settings.txt"
            source = b'"GUI"={"scale"={version=1 value="1.3"}}\n'
            settings.write_bytes(source)
            with mock.patch("capture_session.os.replace", side_effect=OSError("replace denied")):
                with self.assertRaisesRegex(OSError, "replace denied"):
                    reseed_gui_scale_after_warmup(settings, "1.0", output)
            self.assertEqual(settings.read_bytes(), source)
            self.assertEqual(list(root.glob(".pdx_settings.gui_reseed-*.tmp")), [])
            receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
            self.assertEqual(receipt["status"], "RED")

    def test_cleanup_failure_preserves_primary_error_and_writes_red_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            settings = root / "pdx_settings.txt"
            source = b'"GUI"={"scale"={version=1 value="1.3"}}\n'
            settings.write_bytes(source)
            with mock.patch("capture_session.os.replace", side_effect=OSError("replace denied")):
                with mock.patch("capture_session.Path.unlink", side_effect=OSError("cleanup denied")):
                    with self.assertRaisesRegex(OSError, "replace denied"):
                        reseed_gui_scale_after_warmup(settings, "1.0", output)
            receipt = json.loads((output / "gui-settings-warmup-reseed.json").read_text())
            self.assertEqual(receipt["status"], "RED")
            self.assertIn("replace denied", receipt["error"])
            self.assertIn("cleanup denied", receipt["cleanup_error"])
            self.assertEqual(settings.read_bytes(), source)


if __name__ == "__main__":
    unittest.main()
