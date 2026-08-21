from __future__ import annotations

import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RepositoryContractTests(unittest.TestCase):
    def test_all_json_contracts_parse(self) -> None:
        paths = sorted((ROOT / "schemas").glob("*.json"))
        paths.append(ROOT / "strategies" / "growth_100_v1.json")
        self.assertEqual(len(paths), 9)
        for path in paths:
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if path.parent.name == "schemas":
                    expected_version = 2 if "-v2." in path.name else 1
                    self.assertEqual(
                        payload["properties"]["format_version"]["const"],
                        expected_version,
                    )
                else:
                    self.assertEqual(payload["format_version"], 1)

    def test_default_config_is_exact_growth_100_single_mod(self) -> None:
        payload = tomllib.loads(
            (ROOT / "configs" / "default.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["mod"]["enabled_mod_count"], 1)
        self.assertEqual(payload["rules"]["xar_enabled"], "xar_on")
        self.assertEqual(payload["rules"]["xar_inheritance"], "xar_inherit_100")
        self.assertEqual(payload["rules"]["xar_score_basis"], "xar_score_growth")
        self.assertFalse(payload["safety"]["debug_mode"])

    def test_ui_contract_filename_freezes_language_and_runtime_dimensions(self) -> None:
        paths = sorted((ROOT / "configs" / "ui").glob("*.json"))
        self.assertEqual(
            [path.name for path in paths],
            ["ck3-1.19.0.6.zh-hans.2560x1440.json"],
        )
        payload = json.loads(paths[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["game_version"], "1.19.0.6")
        self.assertEqual(payload["language"], "l_simp_chinese")
        self.assertEqual(payload["resolution"], [2560, 1440])


if __name__ == "__main__":
    unittest.main()
