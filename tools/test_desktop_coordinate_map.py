import unittest
import contextlib
import io
import json
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import desktop_coordinate_map as mapper
from desktop_coordinate_map import Mapping, map_point


class CoordinateMappingTests(unittest.TestCase):
    def test_maps_each_axis_independently(self) -> None:
        self.assertEqual(
            map_point(
                preview_bounds=(0, 0, 1000, 500),
                observed_point=(250, 400),
                target_size=(3000, 1000),
            ),
            (750, 800),
        )

    def test_supports_unrelated_aspect_ratios(self) -> None:
        self.assertEqual(
            map_point(
                preview_bounds=(0, 0, 2048, 1000),
                observed_point=(1024, 500),
                target_size=(2560, 1440),
            ),
            (1280, 720),
        )

    def test_rejects_missing_or_out_of_range_geometry(self) -> None:
        cases = (
            ((0, 0, 0, 100), (1, 1), (100, 100)),
            ((0, 0, 100, 100), (-1, 1), (100, 100)),
            ((0, 0, 100, 100), (100, 1), (100, 100)),
            ((0, 0, 100, 100), (1, 100), (100, 100)),
            ((0, 0, 100, 100), (1, 1), (0, 100)),
        )
        for preview_bounds, observed_point, target_size in cases:
            with self.subTest(
                preview_bounds=preview_bounds,
                observed_point=observed_point,
                target_size=target_size,
            ):
                with self.assertRaises(ValueError):
                    map_point(
                        preview_bounds=preview_bounds,
                        observed_point=observed_point,
                        target_size=target_size,
                    )

    def test_accounts_for_preview_content_origin(self) -> None:
        self.assertEqual(
            map_point(
                preview_bounds=(100, 50, 800, 600),
                observed_point=(500, 350),
                target_size=(3440, 1440),
            ),
            (1720, 720),
        )


class FakeDesktop:
    """No desktop API is imported or invoked by these fixtures."""
    def __init__(self, size=(100, 60), after_size=None, position_matches=True):
        self.screen_size = size
        self.after_size = after_size or size
        self.cursor = (99, 0)
        self.position_matches = position_matches
        self.inputs = []
        self.screenshots = []

    def size(self):
        return self.after_size if self.inputs else self.screen_size

    def position(self):
        return self.cursor

    def moveTo(self, x, y, duration=0):
        self.inputs.append(("move", x, y, duration))
        self.cursor = (x, y) if self.position_matches else (x + 1, y)

    def click(self, x, y):
        self.inputs.append(("click", x, y))

    def screenshot(self, path):
        self.screenshots.append(path)
        image = Image.new("RGB", self.after_size, (12, 34, 56))
        image.save(path)
        return image


class PointerMoveTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "pointer-fixtures" / uuid.uuid4().hex
    FOCUS = {"foreground_hwnd": 1001, "foreground_pid": 10,
             "foreground_thread_id": 11, "focus_hwnd": 1002, "title": "Fixture"}
    BUTTONS = {name: False for name in ("left", "right", "middle", "x1", "x2")}

    def setUp(self):
        self.directory = self.ROOT / self._testMethodName
        self.assertFalse(self.directory.exists())
        self.directory.mkdir(parents=True)
        self.source = self.directory / "source.png"
        Image.new("RGB", (100, 60), (12, 34, 56)).save(self.source)
        self.receipt = self.directory / "after.png"
        self.mapping = Mapping((10, 5, 50, 30), (35, 20), (100, 60), (100, 60), (50, 30))
        self.reviewed = (20, 10, 30, 20)

    def argv(self, *extra):
        return ["--source-image", str(self.source), "--preview-left", "10",
                "--preview-top", "5", "--preview-width", "50", "--preview-height", "30",
                "--observed-x", "35", "--observed-y", "20", *extra]

    def reviewed_argv(self):
        return ["--reviewed-left", "20", "--reviewed-top", "10",
                "--reviewed-width", "30", "--reviewed-height", "20"]

    def call_move(self, desktop, focus=None, mapping=None, reviewed=None, buttons=None):
        with patch.object(mapper, "foreground_state", side_effect=focus or [self.FOCUS, self.FOCUS]), \
             patch.object(mapper, "mouse_button_state", side_effect=buttons or [self.BUTTONS, self.BUTTONS]):
            return mapper.move_pointer(mapping=mapping or self.mapping,
                reviewed_bounds=reviewed or self.reviewed, source_image=self.source,
                receipt_path=self.receipt, desktop=desktop, expected_foreground_hwnd=1001)

    def test_move_records_exact_pointer_focus_and_png_json_receipts(self):
        desktop = FakeDesktop()
        result = self.call_move(desktop)
        self.assertEqual(desktop.inputs, [("move", 50, 30, 0)])
        self.assertEqual(result["pointer_before"], (99, 0))
        self.assertEqual(result["pointer_after"], (50, 30))
        self.assertEqual(result["focus_before"], self.FOCUS)
        self.assertEqual(result["mouse_buttons_before"], self.BUTTONS)
        self.assertEqual(result["mouse_buttons_after"], self.BUTTONS)
        self.assertEqual(result["screen_size_after"], (100, 60))
        self.assertEqual(result["status"], "pointer-move-readback-matched")
        self.assertTrue(self.receipt.exists())
        persisted = json.loads(Path(str(self.receipt) + ".json").read_text("utf-8"))
        self.assertEqual(persisted["receipt_sha256"], result["receipt_sha256"])

    def test_unreviewed_or_invalid_region_refuses_before_input(self):
        cases = ((10, 5, 10, 10), (0, 0, 100, 60), (20, 10, 0, 20),
                 (float("nan"), 10, 30, 20))
        for region in cases:
            with self.subTest(region=region):
                desktop = FakeDesktop()
                with self.assertRaises(ValueError):
                    self.call_move(desktop, reviewed=region)
                self.assertEqual(desktop.inputs, [])
        self.assertFalse(self.receipt.exists())

    def test_held_mouse_button_refuses_move_that_would_drag(self):
        for button in self.BUTTONS:
            with self.subTest(button=button):
                desktop = FakeDesktop()
                with self.assertRaisesRegex(ValueError, "could drag"):
                    self.call_move(desktop, buttons=[{**self.BUTTONS, button: True}])
                self.assertEqual(desktop.inputs, [])
        self.assertFalse(self.receipt.exists())

    def test_rounded_target_cannot_leave_reviewed_region(self):
        mapping = Mapping((0, 0, 100, 100), (0.49, 0.49), (10, 10), (10, 10), (0, 0))
        with self.assertRaises(ValueError):
            mapper.validate_reviewed_region(mapping, (0.4, 0.4, 1, 1))

    def test_pre_move_size_or_expected_focus_mismatch_refuses_input(self):
        for desktop, focus in ((FakeDesktop((101, 60)), self.FOCUS),
                               (FakeDesktop(), {**self.FOCUS, "foreground_hwnd": 999})):
            with self.subTest(size=desktop.screen_size, focus=focus):
                with self.assertRaises(ValueError):
                    self.call_move(desktop, focus=[focus])
                self.assertEqual(desktop.inputs, [])
        self.assertFalse(self.receipt.exists())

    def test_changed_post_dimensions_focus_or_pointer_rejects_with_receipt(self):
        cases = ((FakeDesktop(after_size=(101, 60)), self.FOCUS, "screen_size_changed"),
                 (FakeDesktop(), {**self.FOCUS, "focus_hwnd": 999}, "focus_changed"),
                 (FakeDesktop(position_matches=False), self.FOCUS, "pointer_readback_mismatch"))
        for index, (desktop, focus, reason) in enumerate(cases):
            with self.subTest(reason=reason):
                self.receipt = self.directory / f"after-{index}.png"
                result = self.call_move(desktop, focus=[self.FOCUS, focus])
                self.assertEqual(result["status"], "rejected-readback")
                self.assertIn(reason, result["failures"])
                self.assertTrue(Path(str(self.receipt) + ".json").exists())

    def test_dry_run_sends_no_pointer_input_and_creates_no_receipt(self):
        desktop = FakeDesktop()
        with patch.dict(sys.modules, {"pyautogui": desktop}), \
             patch.object(mapper, "foreground_state", side_effect=AssertionError("dry-run focus accessed")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            rc = mapper.main(self.argv("--move", "--dry-run", *self.reviewed_argv()))
        self.assertEqual(rc, 0)
        self.assertFalse(json.loads(output.getvalue())["pointer_input_sent"])
        self.assertEqual(desktop.inputs, [])
        self.assertEqual(desktop.screenshots, [])
        self.assertFalse(self.receipt.exists())

    def test_original_png_dimension_mismatch_refuses_before_input(self):
        desktop = FakeDesktop((101, 60))
        with patch.dict(sys.modules, {"pyautogui": desktop}), self.assertRaises(SystemExit):
            mapper.main(self.argv("--move", "--receipt", str(self.receipt), *self.reviewed_argv()))
        self.assertEqual(desktop.inputs, [])

    def test_move_parser_requires_region_receipt_and_excludes_click(self):
        cases = (self.argv("--move"),
                 self.argv("--move", *self.reviewed_argv()),
                 self.argv("--move", "--click", "--receipt", str(self.receipt), *self.reviewed_argv()))
        for argv in cases:
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    mapper.parse_args(argv)

    def test_click_keeps_existing_action_and_receipt_behavior(self):
        desktop = FakeDesktop()
        with patch.dict(sys.modules, {"pyautogui": desktop}), \
             patch.object(mapper, "foreground_state", side_effect=AssertionError("click focus path changed")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            rc = mapper.main(self.argv("--click", "--receipt", str(self.receipt)))
        self.assertEqual(rc, 0)
        self.assertEqual(desktop.inputs, [("click", 50, 30)])
        self.assertEqual(json.loads(output.getvalue())["screen_point"], [50, 30])
        self.assertTrue(self.receipt.exists())
        self.assertFalse(Path(str(self.receipt) + ".json").exists())


if __name__ == "__main__":
    unittest.main()
