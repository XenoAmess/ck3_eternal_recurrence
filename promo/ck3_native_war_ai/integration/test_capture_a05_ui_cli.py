"""No-screen source admission checks for the explicitly opted-in a05 CLI path."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from capture_session import (
    A04_UI_SOURCE_ROOT,
    A04_UI_GUI_BLOCK_SHA256,
    A04_UI_SETTINGS_SHA256,
    gui_scale_disk_readback,
    prepare_a05_ui_settings,
    validate_a04_ui_gui_source_binding,
)


EVIDENCE = Path(
    r"D:\workspace\ck3_native_war_ai_promo_work"
    r"\episode02-e2-04-d05-screen-lease-20260928-a04"
)
SOURCE = EVIDENCE / "native-ui-saved-settings-a01.pdx.txt"
RECEIPT = EVIDENCE / "native-ui-saved-settings-a01.json"
CHECKPOINT_ROOT = A04_UI_SOURCE_ROOT / "episode01-paired-counter-trace-attempt-010"
CHECKPOINT_SAVE = CHECKPOINT_ROOT / "d05-immutable.ck3"
CHECKPOINT_RECEIPT = (CHECKPOINT_ROOT / "ck3-output" / "interactive-requests-responses" /
                      "d05-save.json")
DEFAULT_RUN = A04_UI_SOURCE_ROOT / "episode02-e2-04-d05-static-a05-cli"


def args(**changes):
    values = dict(import_a04_ui_gui_100=True, a04_ui_settings_snapshot=SOURCE,
                  a04_ui_preservation_receipt=RECEIPT, gui_scale="1.0",
                  checkpoint_save=CHECKPOINT_SAVE,
                  checkpoint_receipt=CHECKPOINT_RECEIPT,
                  state_dir=DEFAULT_RUN / "ck3-state",
                  output_dir=DEFAULT_RUN / "ck3-output",
                  record_debug_desktop=False)
    values.update(changes)
    return argparse.Namespace(**values)


class A05CliUiSourceTest(unittest.TestCase):
    def test_opt_in_requires_complete_arguments_before_any_import(self):
        cases = (
            (args(import_a04_ui_gui_100=False), "require --import"),
            (args(a04_ui_settings_snapshot=None), "both frozen source"),
            (args(a04_ui_preservation_receipt=None), "both frozen source"),
            (args(gui_scale=None), "explicit --gui-scale"),
            (args(checkpoint_save=None), "checkpoint pair"),
            (args(checkpoint_receipt=None), "checkpoint pair"),
            (args(record_debug_desktop=True), "cannot start a debug recorder"),
        )
        for case, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(Exception, message):
                validate_a04_ui_gui_source_binding(case)
        self.assertIsNone(validate_a04_ui_gui_source_binding(args(
            import_a04_ui_gui_100=False, a04_ui_settings_snapshot=None,
            a04_ui_preservation_receipt=None)))

    @unittest.skipUnless(SOURCE.is_file() and RECEIPT.is_file() and
                         CHECKPOINT_SAVE.is_file() and CHECKPOINT_RECEIPT.is_file(),
                         "Frozen external a04 UI evidence is unavailable")
    def test_exact_frozen_source_imports_only_gui_into_fresh_profile(self):
        binding = validate_a04_ui_gui_source_binding(args())
        self.assertEqual(binding["expected_source_sha256"], A04_UI_SETTINGS_SHA256)
        self.assertEqual(binding["expected_gui_block_sha256"], A04_UI_GUI_BLOCK_SHA256)
        self.assertEqual(binding["preservation_receipt"]["sha256"],
                         "69F4535E4FDA428E910CBE6F3B44C70E352853535A2D546CB71AA09CEA941779")
        self.assertEqual(len(binding["original_ui_images"]), 5)
        self.assertEqual(binding["a04_capture_status"], "RED")
        self.assertFalse(binding["recording_authorized_by_this_binding"])
        template = '"Graphics"={}\n"Audio"={}\n\n'
        with tempfile.TemporaryDirectory(dir=A04_UI_SOURCE_ROOT,
                                         prefix="episode02-e2-04-d05-test-") as directory:
            root = Path(directory)
            output = root / "ck3-output"
            profile = root / "ck3-state" / "profile"
            output.mkdir()
            profile.mkdir(parents=True)
            settings = profile / "pdx_settings.txt"
            local_binding = validate_a04_ui_gui_source_binding(args(
                state_dir=root / "ck3-state", output_dir=output))
            prelaunch = prepare_a05_ui_settings(settings, template, output, local_binding)
            expected = template.encode() + SOURCE.read_bytes()[6642:6696]
            self.assertEqual(settings.read_bytes(), expected)
            self.assertEqual(prelaunch["settings"]["sha256"],
                             hashlib.sha256(expected).hexdigest().upper())
            self.assertEqual(prelaunch["ui_source_preservation_receipt"],
                             local_binding["preservation_receipt"])
            self.assertFalse(prelaunch["runtime_scale_proven"])
            self.assertFalse(prelaunch["visual_geometry_reviewed"])
            self.assertFalse(prelaunch["recording_authorized_by_prelaunch"])
            self.assertEqual(json.loads((output / "gui-settings-ui-block-import.json").read_text())
                             ["status"], "GREEN_DISK_ONLY")
            self.assertFalse(gui_scale_disk_readback(settings, "1.0", "default")
                             ["disk_gate_passed"])
            self.assertTrue(gui_scale_disk_readback(
                settings, "1.0", "a05-explicit", allow_native_ui_one=True)
                ["disk_gate_passed"])

    @unittest.skipUnless(SOURCE.is_file() and RECEIPT.is_file() and
                         CHECKPOINT_SAVE.is_file() and CHECKPOINT_RECEIPT.is_file(),
                         "Frozen external a04 UI evidence is unavailable")
    def test_fake_source_self_reported_sha_cannot_override_project_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "self-reported.pdx.txt"
            fake.write_bytes(SOURCE.read_bytes().replace(b'"1"', b'"1.00"', 1))
            unchanged = fake.read_bytes()
            case = args(a04_ui_settings_snapshot=fake)
            case.expected_source_sha256 = hashlib.sha256(fake.read_bytes()).hexdigest().upper()
            case.expected_gui_block_sha256 = case.expected_source_sha256
            with self.assertRaisesRegex(Exception, "frozen full snapshot"):
                validate_a04_ui_gui_source_binding(case)
            self.assertEqual(fake.read_bytes(), unchanged)

    @unittest.skipUnless(SOURCE.is_file() and RECEIPT.is_file() and
                         CHECKPOINT_SAVE.is_file() and CHECKPOINT_RECEIPT.is_file(),
                         "Frozen external a04 UI evidence is unavailable")
    def test_receipt_and_original_image_must_match_reviewed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "self-reported-receipt.json"
            data = json.loads(RECEIPT.read_text(encoding="utf-8"))
            data["claimed_sha256"] = "self-reported"
            fake.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(Exception, "preservation receipt differs"):
                validate_a04_ui_gui_source_binding(args(a04_ui_preservation_receipt=fake))
        original_identity = __import__("capture_session").identity

        def altered_image(path):
            row = original_identity(path)
            if path.name == "scale-100-select-a01.png":
                row = dict(row, sha256="0" * 64)
            return row

        with mock.patch("capture_session.identity", side_effect=altered_image):
            with self.assertRaisesRegex(Exception, "original screenshot bytes differ"):
                validate_a04_ui_gui_source_binding(args())

    @unittest.skipUnless(SOURCE.is_file() and RECEIPT.is_file() and
                         CHECKPOINT_SAVE.is_file() and CHECKPOINT_RECEIPT.is_file(),
                         "Frozen external a04 UI evidence is unavailable")
    def test_caller_supplied_binding_cannot_swap_pinned_evidence(self):
        binding = validate_a04_ui_gui_source_binding(args())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "new-output"
            output.mkdir()
            target = root / "pdx_settings.txt"
            fake = deepcopy(binding)
            fake["hot_readback"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(Exception, "reviewed a04 UI source"):
                prepare_a05_ui_settings(target, '"Graphics"={}\n', output, fake)
            self.assertFalse(target.exists())
            self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
