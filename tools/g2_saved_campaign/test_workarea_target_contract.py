"""Additional pure DATA witnesses for the existing WorkArea target helper.

Prepared as source only. First import/run belongs to the Native validation lane.
The validator must place the selected production root on its import path.
"""

import unittest

from tools.g2_saved_campaign.fit_owned_game_window import workarea_geometry


class WorkAreaTargetContractTest(unittest.TestCase):
    def test_one_pixel_work_does_not_expand_to_a_game_minimum(self):
        info = {
            "Monitor": (-16384, -8640, 16384, 8640),
            "Work": (-4, 9, -3, 10),
        }

        result = workarea_geometry(info)

        self.assertEqual(result["work"], (-4, 9, -3, 10))
        self.assertEqual(result["target"], (-4, 9, 1, 1))

    def test_insetting_work_changes_the_same_input_to_a_smaller_target(self):
        info = {
            "Monitor": (-700, -400, 1300, 800),
            "Work": (-650, -350, 1250, 750),
        }
        larger_target = workarea_geometry(info)["target"]
        self.assertEqual(larger_target, (-650, -350, 1900, 1100))

        info["Work"] = (-649, -348, 1246, 745)
        smaller_target = workarea_geometry(info)["target"]

        self.assertEqual(smaller_target, (-649, -348, 1895, 1093))
        self.assertLess(smaller_target[2], larger_target[2])
        self.assertLess(smaller_target[3], larger_target[3])

    def test_fixed_work_keeps_target_when_its_container_changes(self):
        info = {
            "Monitor": (-100, -100, 1500, 1000),
            "Work": (17, -23, 1297, 697),
        }
        first_target = workarea_geometry(info)["target"]
        self.assertEqual(first_target, (17, -23, 1280, 720))

        info["Monitor"] = (-500, -300, 2000, 1300)
        second_target = workarea_geometry(info)["target"]

        self.assertEqual(second_target, (17, -23, 1280, 720))
        self.assertEqual(second_target, first_target)


if __name__ == "__main__":
    unittest.main()
