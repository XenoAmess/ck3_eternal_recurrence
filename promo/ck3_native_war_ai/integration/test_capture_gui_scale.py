"""Pure profile-rendering checks; never launches CK3."""

import unittest

from capture_session import render_profile_settings


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


if __name__ == "__main__":
    unittest.main()
