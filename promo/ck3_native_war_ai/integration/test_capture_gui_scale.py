"""Pure profile-rendering checks; never launches CK3."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from capture_session import (gui_scale_disk_readback, render_profile_settings,
                             require_gui_scale_disk_gate, write_profile_settings)


class CaptureGuiScaleTest(unittest.TestCase):
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
                                 b'\t\tversion=1\r\n\t\tvalue="1.0"\r\n\t}\r\n}\r\n')
            result = gui_scale_disk_readback(settings, "1.0", "after-native-UI-save")
            self.assertTrue(result["disk_gate_passed"])
            self.assertFalse(result["runtime_scale_proven"])
            self.assertFalse(result["visual_geometry_reviewed"])
            self.assertFalse(result["recording_authorized_by_this_gate"])

    def test_missing_or_duplicate_gui_block_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "pdx_settings.txt"
            for raw in (b'"Graphics"={}\n',
                        b'"GUI"={"scale"={version=1 value="1.0"}}\n'
                        b'"GUI"={"scale"={version=1 value="1.0"}}\n'):
                settings.write_bytes(raw)
                self.assertFalse(gui_scale_disk_readback(settings, "1.0", "test")["disk_gate_passed"])


if __name__ == "__main__":
    unittest.main()
