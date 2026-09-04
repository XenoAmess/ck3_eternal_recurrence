#!/usr/bin/env python3
"""Regression tests for the B3 no-launch projection freezer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import freeze_zg361_phase2_b3_no_launch as freeze


BOM = b"\xef\xbb\xbf"


def write_effects(root: Path, name: str, body: str) -> None:
    directory = root / "common" / "scripted_effects"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(BOM + body.encode("utf-8"))


class CentralEffectCallClosureTests(unittest.TestCase):
    def test_recursive_custom_effect_calls_are_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_helper_effect = yes\n"
                "}\n",
            )
            write_effects(
                root,
                "dispatch_effects.txt",
                "zg361_probe_helper_effect = {\n"
                "    zg361_probe_leaf_effect = yes\n"
                "}\n\n"
                "zg361_probe_leaf_effect = {\n"
                "    set_variable = { name = probe value = 1 }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_provider_files=frozenset({"dispatch_effects.txt"}),
            )
            self.assertTrue(result["green"])
            self.assertEqual(3, result["reachable_effect_count"])
            self.assertEqual([], result["missing_effects"])

    def test_recursive_missing_callee_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_helper_effect = yes\n"
                "}\n",
            )
            write_effects(
                root,
                "dispatch_effects.txt",
                "zg361_probe_helper_effect = {\n"
                "    zg361_probe_missing_effect = yes\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_provider_files=frozenset({"dispatch_effects.txt"}),
            )
            self.assertFalse(result["green"])
            self.assertEqual(
                ["zg361_probe_missing_effect"], result["missing_effects"]
            )

    def test_predecessor_material_red_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cell").mkdir()
            (root / "report.json").write_text(
                json.dumps({"result": "RED"}), encoding="utf-8"
            )
            (root / "cell" / "report.json").write_text(
                json.dumps(
                    {
                        "result": "RED",
                        "native_cleanup": {
                            "result": "GREEN",
                            "failed_checks": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            caller = freeze.PREDECESSOR_CALLER_FILE
            (root / "cell" / "final_error.log").write_text(
                "Unknown effect: zg361_p2c_record_stage_effect " + caller + "\n"
                "Unknown effect: zg361_p2c_record_red_effect " + caller + "\n",
                encoding="utf-8",
            )
            (root / "evidence-index.json").write_text("{}\n", encoding="utf-8")
            result = freeze.predecessor_live_red_evidence(root)
            self.assertEqual("material-projection-closure-red", result["classification"])
            self.assertFalse(result["loader_performance_claimed"])
            self.assertEqual(2, result["unknown_effect_line_count"])
            self.assertTrue(result["cleanup_green"])


if __name__ == "__main__":
    unittest.main()
