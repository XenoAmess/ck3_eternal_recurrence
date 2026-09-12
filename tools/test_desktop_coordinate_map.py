import unittest

from desktop_coordinate_map import map_point


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


if __name__ == "__main__":
    unittest.main()
