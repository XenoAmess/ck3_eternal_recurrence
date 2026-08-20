#!/usr/bin/env python3
"""Contract tests for the reversible native succession GUI projection."""

import unittest

import gen_no_heir_gui


class SuccessionProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection = gen_no_heir_gui.OUTPUT.read_text(encoding="utf-8-sig")

    def test_tracked_projection_round_trips_without_game_files(self):
        source = gen_no_heir_gui.recover_source(self.projection)
        self.assertEqual(gen_no_heir_gui.native_digest(source), gen_no_heir_gui.NATIVE_SHA256)
        self.assertEqual(
            gen_no_heir_gui.HEADER + gen_no_heir_gui.render_source(source),
            self.projection,
        )

    def test_projection_rejects_missing_injection(self):
        projection = self.projection.replace(gen_no_heir_gui.INJECTION, "", 1)
        with self.assertRaisesRegex(RuntimeError, "exactly one XAR injection"):
            gen_no_heir_gui.recover_source(projection)

    def test_projection_rejects_modified_native_body(self):
        projection = self.projection.replace("SUCCESSION EVENT", "ALTERED EVENT", 1)
        with self.assertRaisesRegex(RuntimeError, "digest changed"):
            gen_no_heir_gui.recover_source(projection)

    def test_local_native_source_matches_when_available(self):
        if not gen_no_heir_gui.SOURCE.is_file():
            self.skipTest("CK3 source is intentionally absent in clean checkouts")
        source = gen_no_heir_gui.SOURCE.read_text(encoding="utf-8-sig")
        gen_no_heir_gui.validate_native_source(source)
        self.assertEqual(source, gen_no_heir_gui.recover_source(self.projection))


if __name__ == "__main__":
    unittest.main()
