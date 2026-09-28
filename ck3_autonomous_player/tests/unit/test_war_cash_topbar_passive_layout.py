from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))

from war_cash_topbar_passive_layout import (
    inspect_supplied_topbar_expense_bytes,
)


TOPBAR_ADDRESS = 0x100000
ROW_ADDRESS = 0x200000
NAME_ADDRESS = 0x300000
MILITARY_KEY = b"BREAKDOWN_ARMY_MAINTENANCE"


def fixture() -> dict[str, object]:
    topbar = bytearray(0xF90)
    struct.pack_into("<QII", topbar, 0xAD8, ROW_ADDRESS, 2, 2)
    struct.pack_into("<q", topbar, 0xB50, -5_000_000)
    struct.pack_into("<Q", topbar, 0xB58, 100_000)
    struct.pack_into("<Q", topbar, 0xB68, TOPBAR_ADDRESS + 0xAD8)
    struct.pack_into("<Q", topbar, 0xF88, 42)
    rows = bytearray(2 * 0x90)
    struct.pack_into("<Q", rows, 0x18, NAME_ADDRESS)
    struct.pack_into("<QQ", rows, 0x28, len(MILITARY_KEY), 31)
    struct.pack_into("<qQ", rows, 0x78, -2_500_000, 100_000)
    other = b"COURT_EXPENSE"
    rows[0x90 + 0x18:0x90 + 0x18 + len(other)] = other
    struct.pack_into("<QQ", rows, 0x90 + 0x28, len(other), 15)
    struct.pack_into("<qQ", rows, 0x90 + 0x78, -2_500_000, 100_000)
    return {
        "topbar_address": TOPBAR_ADDRESS,
        "topbar_bytes": bytes(topbar),
        "row_array_address": ROW_ADDRESS,
        "row_bytes": bytes(rows),
        "name_payloads": {NAME_ADDRESS: MILITARY_KEY + b"\0"},
    }


class PassiveTopbarLayoutTests(unittest.TestCase):
    def test_named_military_row_remains_diagnostic_only(self) -> None:
        result = inspect_supplied_topbar_expense_bytes(**fixture())
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["military_row_candidate_count"], 1)
        self.assertEqual(result["rows"][0]["name_key"],
                         "BREAKDOWN_ARMY_MAINTENANCE")
        self.assertEqual(result["expense_total_signed_raw_candidate"], -5_000_000)
        self.assertFalse(result["unique_live_topbar_instance_proven"])
        self.assertFalse(result["formal_cash_eligible"])

    def test_backpointer_and_scale_corruption_are_rejected(self) -> None:
        for offset, value, reason in (
            (0xB68, TOPBAR_ADDRESS + 0xAD9, "back-pointer"),
            (0xB58, 1, "Q100000"),
        ):
            candidate = fixture()
            topbar = bytearray(candidate["topbar_bytes"])
            struct.pack_into("<Q", topbar, offset, value)
            candidate["topbar_bytes"] = bytes(topbar)
            with self.subTest(offset=offset), self.assertRaisesRegex(
                ValueError, reason,
            ):
                inspect_supplied_topbar_expense_bytes(**candidate)

    def test_missing_name_bytes_and_truncated_rows_are_rejected(self) -> None:
        candidate = fixture()
        candidate["name_payloads"] = {}
        with self.assertRaisesRegex(ValueError, "not supplied"):
            inspect_supplied_topbar_expense_bytes(**candidate)
        candidate = fixture()
        candidate["row_bytes"] = candidate["row_bytes"][:-1]
        with self.assertRaisesRegex(ValueError, "row vector"):
            inspect_supplied_topbar_expense_bytes(**candidate)

    def test_count_cap_and_row_scale_cannot_claim_empty_or_measured(self) -> None:
        candidate = fixture()
        topbar = bytearray(candidate["topbar_bytes"])
        struct.pack_into("<I", topbar, 0xAE4, 0)
        candidate["topbar_bytes"] = bytes(topbar)
        with self.assertRaisesRegex(ValueError, "row vector"):
            inspect_supplied_topbar_expense_bytes(**candidate)
        candidate = fixture()
        rows = bytearray(candidate["row_bytes"])
        struct.pack_into("<Q", rows, 0x80, 1)
        candidate["row_bytes"] = bytes(rows)
        with self.assertRaisesRegex(ValueError, "row is not Q100000"):
            inspect_supplied_topbar_expense_bytes(**candidate)


if __name__ == "__main__":
    unittest.main()
