from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_wheel_configuration_includes_uia_bridge(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as stream:
            configuration = tomllib.load(stream)
        package_data = configuration["tool"]["setuptools"]["package-data"]
        self.assertIn("uia_bridge.ps1", package_data["ck3_workshop_mcp"])
        self.assertTrue(
            (ROOT / "src" / "ck3_workshop_mcp" / "uia_bridge.ps1").is_file()
        )


if __name__ == "__main__":
    unittest.main()
