"""Pure DATA boundaries; never calls main, loads pywin32 or queries a display."""
import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).with_name("fit_owned_game_window.py")
SPEC = importlib.util.spec_from_file_location("owned_window_fit_data_target", SOURCE)
FIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIT)


class WorkareaGeometryTest(unittest.TestCase):
    def test_bottom_taskbar_uses_work_not_full_monitor(self):
        actual = FIT.workarea_geometry({"Monitor": (0, 0, 2560, 1440), "Work": (0, 0, 2560, 1392)})
        self.assertEqual((0, 0, 2560, 1392), actual["work"])
        self.assertEqual((0, 0, 2560, 1392), actual["target"])
        self.assertEqual((0, 0, 2560, 1440), actual["monitor"])

    def test_each_reserved_edge_keeps_work_origin(self):
        cases = [((40, 0, 1920, 1080), (40, 0, 1880, 1080)),
                 ((0, 30, 1920, 1080), (0, 30, 1920, 1050)),
                 ((0, 0, 1880, 1080), (0, 0, 1880, 1080)),
                 ((0, 0, 1920, 1040), (0, 0, 1920, 1040))]
        for work, expected in cases:
            with self.subTest(work=work):
                self.assertEqual(expected, FIT.workarea_geometry({"Monitor": (0, 0, 1920, 1080), "Work": work})["target"])

    def test_negative_secondary_monitor_origin_is_preserved(self):
        actual = FIT.workarea_geometry({"Monitor": (-1920, -1080, 0, 0), "Work": (-1880, -1050, 0, 0)})
        self.assertEqual((-1880, -1050, 1880, 1050), actual["target"])

    def test_no_reserved_space_accepts_equal_rectangles(self):
        actual = FIT.workarea_geometry({"Monitor": [100, 200, 900, 800], "Work": [100, 200, 900, 800]})
        self.assertEqual((100, 200, 800, 600), actual["target"])

    def test_missing_work_never_falls_back_to_monitor(self):
        for info in (None, {}, {"Monitor": (0, 0, 1920, 1080)}, {"Work": (0, 0, 1920, 1080)}):
            with self.subTest(info=info), self.assertRaises(ValueError):
                FIT.workarea_geometry(info)

    def test_work_outside_any_monitor_edge_is_rejected(self):
        for work in ((-1, 0, 1920, 1080), (0, -1, 1920, 1080), (0, 0, 1921, 1080), (0, 0, 1920, 1081)):
            with self.subTest(work=work), self.assertRaises(ValueError):
                FIT.workarea_geometry({"Monitor": (0, 0, 1920, 1080), "Work": work})

    def test_exact_integer_positive_rectangles_required(self):
        for work in ((0, 0, 1920, True), (0, 0, 1920, 1040.0), (0, 0, 1920, "1040"),
                     (0, 0, 1920), (0, 0, 0, 1080), (100, 0, 50, 1080), (0, 10, 1920, 10)):
            with self.subTest(work=work), self.assertRaises(ValueError):
                FIT.workarea_geometry({"Monitor": (0, 0, 1920, 1080), "Work": work})

    def test_win32_coordinate_and_size_overflow_rejected(self):
        for monitor in ((0, 0, 1 << 31, 1080), (-(1 << 31), 0, 1, 1080)):
            with self.subTest(monitor=monitor), self.assertRaises(ValueError):
                FIT.workarea_geometry({"Monitor": monitor, "Work": monitor})


if __name__ == "__main__":
    unittest.main()
