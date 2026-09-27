"""Distinguish spendable prestige from accumulated fame in CK3 saves."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "project_war31_fame_delta.py"
SPEC = importlib.util.spec_from_file_location("project_war31_fame_delta", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class War31FameDeltaTests(unittest.TestCase):
    def test_currency_and_accumulated_are_separate_scoped_fields(self) -> None:
        lines = [
            "SAV010101\n", "living={\n", "\t29829={\n",
            "\t\tfirst_name=\"Robert\"\n", "\t\t\tprestige={\n",
            "\t\t\t\tcurrency=2496.5545\n",
            "\t\t\t\taccumulated=5815.61947\n",
            "\t\t\t}\n", "\t}\n", "}\n",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.ck3"
            path.write_text("".join(lines), encoding="ascii", newline="")
            actual = MODULE.read_prestige_ledger(
                path, character_id=29829, line_start=3, line_end=9,
            )
        self.assertEqual(actual, {
            "currency": 249_655_450,
            "accumulated": 581_561_947,
        })

    def test_wrong_character_locator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.ck3"
            path.write_bytes(
                b"SAV010101\n\t29829={\n\t\t\tprestige={\n"
                b"\t\t\t\tcurrency=1\n\t\t\t\taccumulated=2\n"
                b"\t\t\t}\n\t}\n"
            )
            with self.assertRaisesRegex(ValueError, "start drifted"):
                MODULE.read_prestige_ledger(
                    path, character_id=30097, line_start=2, line_end=7,
                )

    def test_missing_accumulated_is_not_silently_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.ck3"
            path.write_bytes(
                b"SAV010101\n\t29829={\n\t\t\tprestige={\n"
                b"\t\t\t\tcurrency=1\n\t\t\t}\n\t}\n"
            )
            with self.assertRaisesRegex(ValueError, "complete prestige ledger"):
                MODULE.read_prestige_ledger(
                    path, character_id=29829, line_start=2, line_end=6,
                )


if __name__ == "__main__":
    unittest.main()
