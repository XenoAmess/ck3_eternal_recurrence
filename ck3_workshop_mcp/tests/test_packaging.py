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
        forbidden_suffixes = {"." + value for value in ("ps" + "1", "psm" + "1", "psd" + "1")}
        package_files = (ROOT / "src" / "ck3_workshop_mcp").iterdir()
        self.assertFalse([path for path in package_files if path.suffix.casefold() in forbidden_suffixes])


if __name__ == "__main__":
    unittest.main()
