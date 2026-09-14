from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_wheel_has_no_script_bridge_package_data(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as stream:
            configuration = tomllib.load(stream)
        package_data = configuration["tool"]["setuptools"].get("package-data", {})
        self.assertEqual(package_data.get("ck3_workshop_mcp", []), [])
        self.assertFalse(list((ROOT / "src" / "ck3_workshop_mcp").glob("*.ps1")))


if __name__ == "__main__":
    unittest.main()
