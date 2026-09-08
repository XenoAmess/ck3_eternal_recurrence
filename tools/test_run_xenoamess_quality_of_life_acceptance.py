#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import run_acceptance as acceptance
import run_xenoamess_quality_of_life_acceptance as xqol


class ProductOuterDescriptorTests(unittest.TestCase):
    def test_workshop_identity_is_recorded_but_not_loaded_in_isolated_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inner = root / "descriptor.mod"
            outer = root / "xqol_acceptance.mod"
            target = root / "product"
            original = 'name="XenoAmess的体验优化"\nremote_file_id="3798133925"\n'
            inner.write_bytes(original.encode("utf-8-sig"))

            item_id = xqol.write_product_outer_descriptor(inner, outer, target)

            self.assertEqual(item_id, "3798133925")
            self.assertEqual(inner.read_text(encoding="utf-8-sig"), 'name="XenoAmess的体验优化"\n')
            rendered = outer.read_text(encoding="utf-8-sig")
            self.assertNotIn("remote_file_id", rendered)
            self.assertIn(f'path="{target.as_posix()}"', rendered)

    def test_malformed_workshop_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inner = root / "descriptor.mod"
            inner.write_text('name="x"\nremote_file_id="not-numeric"\n', encoding="utf-8-sig")

            with self.assertRaises(acceptance.RunnerError):
                xqol.write_product_outer_descriptor(inner, root / "outer.mod", root / "product")


if __name__ == "__main__":
    unittest.main()
