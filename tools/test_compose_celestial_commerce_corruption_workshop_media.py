#!/usr/bin/env python3
"""Tests for Celestial Commerce & Corruption Workshop gameplay media."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import compose_celestial_commerce_corruption_workshop_media as media


class CelestialCommerceWorkshopMediaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="xccc-media-test-")
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "run"
        (self.artifacts / "cell").mkdir(parents=True)
        self.output = self.root / "output"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_report(self, result: str = "GREEN") -> None:
        report = {
            "result": result,
            "cell": {
                "result": result,
                "scenario_evidence": {
                    "installed_build": "1.19.0.6",
                    "celestial_government_allows_barter": True,
                    "production_decision_rendered_and_confirmed": True,
                    "production_event_tier_four_selected": True,
                    "corruption_trait_applied": "xccc_corruption_4",
                    "tier_four_tax_rate": 0.5,
                },
            },
        }
        (self.artifacts / "report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )

    def write_capture(self, size: tuple[int, int] = media.EXPECTED_SIZE) -> None:
        Image.new("RGB", size, (42, 73, 91)).save(
            self.artifacts / "cell" / media.SOURCE_NAME
        )

    def test_green_run_renders_deterministically(self) -> None:
        self.write_report()
        self.write_capture()
        first = media.render(self.artifacts, self.output)
        first_bytes = (self.output / media.OUTPUT_NAME).read_bytes()
        second = media.render(self.artifacts, self.output)
        self.assertEqual((self.output / media.OUTPUT_NAME).read_bytes(), first_bytes)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(first["dimensions"], [1320, 743])
        self.assertLess(first["bytes"], media.MAX_BYTES)

    def test_red_run_is_rejected(self) -> None:
        self.write_report("RED")
        self.write_capture()
        with self.assertRaisesRegex(ValueError, "GREEN acceptance report"):
            media.render(self.artifacts, self.output)

    def test_wrong_capture_dimensions_are_rejected(self) -> None:
        self.write_report()
        self.write_capture((1280, 720))
        with self.assertRaisesRegex(ValueError, "unexpected gameplay capture dimensions"):
            media.render(self.artifacts, self.output)


if __name__ == "__main__":
    unittest.main()
