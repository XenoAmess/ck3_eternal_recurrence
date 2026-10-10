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

    def test_non_png_receipts_refuse_click_and_move_before_input(self):
        for action in ("--click", "--move"):
            for filename in ("after.json", "after.jpg"):
                with self.subTest(action=action, filename=filename):
                    desktop = FakeDesktop()
                    receipt = self.directory / filename
                    extra = self.reviewed_argv() if action == "--move" else []
                    with patch.dict(sys.modules, {"pyautogui": desktop}), \
                         patch.object(mapper, "foreground_state", side_effect=AssertionError("focus queried before receipt refusal")), \
                         contextlib.redirect_stderr(io.StringIO()) as errors:
                        with self.assertRaises(SystemExit) as error:
                            mapper.main(self.argv(action, "--receipt", str(receipt), *extra))
                    self.assertEqual(error.exception.code, 2)
                    self.assertIn("PNG screenshot path ending in .png", errors.getvalue())
                    self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
                    self.assertFalse(receipt.exists())

    def test_existing_receipts_or_file_parent_refuse_before_input(self):
        existing = self.directory / "existing.png"
        existing.write_bytes(b"existing evidence")
        file_parent = self.directory / "file-parent"
        file_parent.write_bytes(b"file, not directory")
        sidecar_receipt = self.directory / "sidecar-only.png"
        Path(str(sidecar_receipt) + ".json").write_text("existing sidecar", encoding="utf-8")
        cases = [(action, receipt) for action in ("--click", "--move")
                 for receipt in (existing, file_parent / "after.png")]
        cases.append(("--move", sidecar_receipt))
        for action, receipt in cases:
            with self.subTest(action=action, receipt=receipt):
                desktop = FakeDesktop()
                extra = self.reviewed_argv() if action == "--move" else []
                with patch.dict(sys.modules, {"pyautogui": desktop}), \
                     contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        mapper.main(self.argv(action, "--receipt", str(receipt), *extra))
                self.assertEqual(error.exception.code, 2)
                self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        self.assertEqual(existing.read_bytes(), b"existing evidence")
        self.assertEqual(file_parent.read_bytes(), b"file, not directory")
        self.assertEqual(Path(str(sidecar_receipt) + ".json").read_text(encoding="utf-8"), "existing sidecar")

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


class GuardedClickTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "pointer-fixtures" / uuid.uuid4().hex
    FOCUS = PointerMoveTests.FOCUS
    setUp = PointerMoveTests.setUp
    argv = PointerMoveTests.argv
    # Reuse only the existing fake desktop/source setup, not the move test cases.
    def test_click_wrong_foreground_refuses_before_any_input(self):
        desktop = FakeDesktop()
        with patch.dict(sys.modules, {"pyautogui": desktop}), \
             patch.object(mapper, "foreground_state", return_value={**self.FOCUS, "foreground_hwnd": 999}), \
             self.assertRaisesRegex(ValueError, "expected HWND for click"):
            mapper.main(self.argv("--click", "--receipt", str(self.receipt), "--expected-foreground-hwnd", "1001"))
        self.assertEqual(desktop.inputs, [])
        self.assertEqual(desktop.screenshots, [])
        self.assertFalse(self.receipt.exists())
        self.assertFalse(Path(str(self.receipt) + ".json").exists())

    def test_click_checks_both_sides_and_preserves_failed_post_readback(self):
        for index, after in enumerate((self.FOCUS, {**self.FOCUS, "foreground_hwnd": 999},
                                      {**self.FOCUS, "foreground_pid": 99})):
            with self.subTest(after=after):
                receipt = self.directory / f"guarded-{index}.png"
                desktop = FakeDesktop()
                with patch.dict(sys.modules, {"pyautogui": desktop}), \
                     patch.object(mapper, "foreground_state", side_effect=[self.FOCUS, after]) as focus, \
                     contextlib.redirect_stdout(io.StringIO()) as output:
                    rc = mapper.main(self.argv("--click", "--receipt", str(receipt), "--expected-foreground-hwnd", "0x3e9"))
                result = json.loads(output.getvalue())
                self.assertEqual(focus.call_count, 2)
                self.assertEqual(desktop.inputs, [("click", 50, 30)])
                self.assertIs(result["click_completed"], True)
                self.assertEqual(rc, 0 if index == 0 else 3)
                self.assertEqual(result["focus_before"], self.FOCUS)
                self.assertEqual(result["focus_after"], after)
                self.assertEqual(result["expected_foreground_hwnd"], 1001)
                self.assertEqual(result["failures"], [] if index == 0 else ["foreground_changed_after_click"])
                self.assertTrue(receipt.is_file())
                self.assertEqual(json.loads(Path(str(receipt) + ".json").read_text("utf-8")), result)

    def test_explicit_source_age_rejects_expired_images_and_invalid_limits(self):
        import time
        observed = time.time()
        desktop = FakeDesktop()
        with patch.dict(sys.modules, {"pyautogui": desktop}), \
             patch("time.time", return_value=observed + 3600), \
             patch.object(mapper, "foreground_state", side_effect=AssertionError("expired image reached foreground/click")), \
             self.assertRaisesRegex(ValueError, "expired"):
            mapper.main(self.argv("--click", "--receipt", str(self.receipt),
                                  "--expected-foreground-hwnd", "1001", "--max-source-age-seconds", "30"))
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        with patch("time.time", return_value=self.source.stat().st_mtime + 2):
            age = mapper.source_image_age(self.source, 3)
        self.assertEqual(age["age_seconds"], 2)
        for limit in ("0", "-1", "nan", "inf"):
            with self.subTest(limit=limit), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                mapper.parse_args(self.argv("--click", "--receipt", str(self.receipt), "--max-source-age-seconds", limit))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            mapper.parse_args(self.argv("--max-source-age-seconds", "30"))
        self.assertFalse(self.receipt.exists())



class AgeRejectionReceiptTests(unittest.TestCase):
    """Offline only; every desktop call uses the existing FakeDesktop."""
    ROOT = Path(__file__).resolve().parents[1] / "pointer-fixtures" / uuid.uuid4().hex
    FOCUS = PointerMoveTests.FOCUS
    setUp = PointerMoveTests.setUp

    def guarded(self, desktop, receipt=None):
        return mapper.guarded_click(mapping=self.mapping, source_image=self.source,
            receipt_path=receipt or self.receipt, desktop=desktop, button="left",
            expected_foreground_hwnd=1001, max_source_age_seconds=60)

    def assert_age_rejection(self, checked_at, reason, receipt=None):
        receipt = receipt or self.receipt
        desktop = FakeDesktop()
        with patch("time.time", return_value=checked_at), \
             patch.object(mapper, "foreground_state") as focus, \
             self.assertRaisesRegex(ValueError, "source screenshot is expired or has a future modification time") as failure:
            self.guarded(desktop, receipt)
        focus.assert_not_called()
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        self.assertFalse(receipt.exists())
        sidecar = Path(str(receipt) + ".json")
        # Reject bare non-finite JSON tokens; quoted diagnostic repr is allowed.
        def reject_constant(value):
            raise AssertionError("non-standard JSON constant: " + value)
        result = json.loads(sidecar.read_text("utf-8"), parse_constant=reject_constant)
        self.assertEqual(result["status"], "rejected")
        self.assertIs(result["input_performed"], False)
        self.assertIs(result["click_completed"], False)
        self.assertEqual(result["reason"], reason)
        self.assertEqual(result["maximum"], 60)
        self.assertEqual(result["source_mtime"], self.source.stat().st_mtime)
        self.assertEqual(result["error"], str(failure.exception))
        return result

    def test_expired_age_persists_actual_seconds_before_original_rejection(self):
        modified = self.source.stat().st_mtime
        result = self.assert_age_rejection(modified + 61, "source_image_expired")
        self.assertEqual(result["checked_at"], modified + 61)
        self.assertEqual(result["age_seconds"], 61)

    def test_future_mtime_persists_negative_age_without_input(self):
        modified = self.source.stat().st_mtime
        result = self.assert_age_rejection(modified - 1, "source_mtime_in_future")
        self.assertEqual(result["checked_at"], modified - 1)
        self.assertEqual(result["age_seconds"], -1)

    def test_nonfinite_clock_age_is_null_with_explicit_repr_and_standard_json(self):
        for index, value in enumerate((float("nan"), float("inf"), float("-inf"))):
            with self.subTest(value=repr(value)):
                result = self.assert_age_rejection(value, "source_age_nonfinite",
                    self.directory / f"nonfinite-{index}.png")
                self.assertIsNone(result["checked_at"])
                self.assertIsNone(result["age_seconds"])
                self.assertEqual(result["source_age_before"]["nonfinite_values"]["checked_at_unix"], repr(value))
                self.assertIn("age_seconds", result["source_age_before"]["nonfinite_values"])

    def test_exact_age_limit_allows_original_click_and_success_receipt(self):
        modified = self.source.stat().st_mtime
        desktop = FakeDesktop()
        with patch("time.time", return_value=modified + 60), \
             patch.object(mapper, "foreground_state", side_effect=[self.FOCUS, self.FOCUS]):
            result = self.guarded(desktop)
        self.assertEqual(desktop.inputs, [("click", 50, 30)])
        self.assertEqual(len(desktop.screenshots), 1)
        self.assertEqual(result["status"], "guarded-click-readback-matched")
        self.assertEqual(result["source_age_before"], {"source_mtime_unix": modified,
            "checked_at_unix": modified + 60, "age_seconds": 60, "maximum_seconds": 60})
        self.assertNotIn("input_performed", result)
        self.assertNotIn("reason", result)
        self.assertEqual(json.loads(Path(str(self.receipt) + ".json").read_text("utf-8")),
                         json.loads(json.dumps(result)))

    def test_existing_sidecar_rejects_before_age_and_is_never_overwritten(self):
        sidecar = Path(str(self.receipt) + ".json")
        sidecar.write_text("original evidence", encoding="utf-8")
        desktop = FakeDesktop()
        with patch.object(mapper, "source_image_age") as age, self.assertRaisesRegex(ValueError, "sidecar already exists"):
            self.guarded(desktop)
        age.assert_not_called()
        self.assertEqual(sidecar.read_text("utf-8"), "original evidence")
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))

    def test_sidecar_creation_race_preserves_original_and_never_clicks(self):
        original_age = mapper.source_image_age
        sidecar = Path(str(self.receipt) + ".json")
        def racing_age(source, maximum):
            sidecar.write_text("race winner evidence", encoding="utf-8")
            return original_age(source, maximum)
        desktop = FakeDesktop()
        with patch("time.time", return_value=self.source.stat().st_mtime + 61), \
             patch.object(mapper, "source_image_age", side_effect=racing_age), \
             self.assertRaises(FileExistsError):
            self.guarded(desktop)
        self.assertEqual(sidecar.read_text("utf-8"), "race winner evidence")
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        self.assertFalse(self.receipt.exists())

    def test_rejection_sidecar_write_failure_never_clicks(self):
        desktop = FakeDesktop()
        with patch("time.time", return_value=self.source.stat().st_mtime + 61), \
             patch.object(Path, "open", side_effect=PermissionError("synthetic denied receipt")), \
             self.assertRaises(PermissionError):
            self.guarded(desktop)
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        self.assertFalse(self.receipt.exists())

    def test_original_preclick_size_gate_still_runs_before_age(self):
        desktop = FakeDesktop((101, 60))
        with patch.object(mapper, "source_image_age") as age, \
             self.assertRaisesRegex(ValueError, "screen size changed before guarded click"):
            self.guarded(desktop)
        age.assert_not_called()
        self.assertEqual((desktop.inputs, desktop.screenshots), ([], []))
        self.assertFalse(Path(str(self.receipt) + ".json").exists())


if __name__ == "__main__":
    unittest.main()
