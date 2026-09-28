from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_war_cash_topbar_owner_path import fixture
from war_cash_topbar_bounded_sample import (
    sample_bounded_topbar_once, sample_bounded_topbar_twice,
)


ROW_ADDRESS = 0x600000


class FakeReadOnlyProcess:
    base = 0x140000000

    def __init__(self, *, changing_rows: bool = False,
                 changing_total: bool = False,
                 changing_render_frame: bool = False) -> None:
        supplied = fixture()
        topbar = bytearray(supplied["topbar_bytes"])
        struct.pack_into("<QII", topbar, 0xAD8, ROW_ADDRESS, 1, 1)
        struct.pack_into("<qQ", topbar, 0xB50, -2_500_000, 100_000)
        struct.pack_into("<Q", topbar, 0xB68, supplied["topbar_address"] + 0xAD8)
        struct.pack_into("<Q", topbar, 0xF88, 42)
        row = bytearray(0x90)
        name = b"BREAKDOWN_ARMY_MAINTENANCE"
        struct.pack_into("<Q", row, 0x18, 0x700000)
        struct.pack_into("<QQ", row, 0x28, len(name), 31)
        struct.pack_into("<qQ", row, 0x78, -2_500_000, 100_000)
        self.name = name + b"\0"
        self.row = bytes(row)
        self.changing_rows = changing_rows
        self.changing_total = changing_total
        self.changing_render_frame = changing_render_frame
        self.row_reads = 0
        self.topbar_reads = 0
        self.reads: list[tuple[int, int]] = []
        self.blocks = {
            supplied["global_slot_address"]: supplied["global_slot_bytes"],
            supplied["global_owner_address"]: supplied["global_owner_bytes"],
            supplied["idler_address"]: supplied["idler_bytes"],
            supplied["handler_address"]: supplied["handler_bytes"],
            supplied["topbar_address"]: bytes(topbar),
            0x700000: self.name,
        }

    def read(self, address: int, size: int) -> bytes:
        self.reads.append((address, size))
        if address == 0x400000:
            self.topbar_reads += 1
            if (self.changing_total or self.changing_render_frame
                    ) and self.topbar_reads == 2:
                changed = bytearray(self.blocks[address])
                if self.changing_total:
                    struct.pack_into("<q", changed, 0xB50, -3_000_000)
                if self.changing_render_frame:
                    struct.pack_into("<Q", changed, 0xF88, 43)
                return bytes(changed)
        if address == ROW_ADDRESS:
            self.row_reads += 1
            if self.changing_rows and self.row_reads == 2:
                changed = bytearray(self.row)
                struct.pack_into("<q", changed, 0x78, -3_000_000)
                return bytes(changed)
            return self.row
        value = self.blocks[address]
        if len(value) != size:
            raise ValueError("fake read length mismatch")
        return value


class BoundedTopbarSampleTests(unittest.TestCase):
    def test_no_scan_owner_and_expense_sample_is_diagnostic(self) -> None:
        process = FakeReadOnlyProcess()
        sample = sample_bounded_topbar_twice(process)
        self.assertEqual(sample["status"], "stable_supplied_bytes_diagnostic_only")
        self.assertEqual(sample["first"]["expense_layout"]["rows"][0]
                         ["signed_raw_candidate"], -2_500_000)
        self.assertLess(sample["total_target_memory_bytes_read"], 128 * 1024)
        self.assertEqual(process.row_reads, 2)
        self.assertFalse(sample["same_frame_cache_freshness_proven"])
        self.assertFalse(sample["formal_cash_eligible"])

    def test_changed_expense_rows_stay_red(self) -> None:
        sample = sample_bounded_topbar_twice(
            FakeReadOnlyProcess(changing_rows=True))
        self.assertEqual(sample["status"],
                         "RED_owner_or_expense_bytes_changed_or_unavailable")
        self.assertFalse(sample["same_expense_rows"])
        self.assertFalse(sample["formal_cash_eligible"])
        sample = sample_bounded_topbar_twice(
            FakeReadOnlyProcess(changing_total=True))
        self.assertFalse(sample["same_owner_path_bytes"])
        self.assertFalse(sample["same_expense_rows"])
        self.assertFalse(sample["formal_cash_eligible"])
        sample = sample_bounded_topbar_twice(
            FakeReadOnlyProcess(changing_render_frame=True))
        self.assertEqual(sample["status"],
                         "RED_owner_or_expense_bytes_changed_or_unavailable")
        self.assertFalse(sample["same_owner_path_bytes"])
        self.assertTrue(sample["same_expense_rows"])

    def test_wrong_global_owner_pointer_fails_before_other_reads(self) -> None:
        process = FakeReadOnlyProcess()
        slot = process.base + 0x570F7B8
        process.blocks[slot] = struct.pack("<Q", 0)
        with self.assertRaisesRegex(ValueError, "global owner"):
            sample_bounded_topbar_once(process)
        self.assertEqual(process.reads, [(slot, 8)])

    def test_bad_parent_vtable_is_rejected_before_child_read(self) -> None:
        process = FakeReadOnlyProcess()
        idler = bytearray(process.blocks[0x200000])
        struct.pack_into("<Q", idler, 0, 0x140000000 + 0x4135EE0)
        process.blocks[0x200000] = bytes(idler)
        with self.assertRaisesRegex(ValueError, "idler vtable"):
            sample_bounded_topbar_once(process)
        self.assertNotIn((0x300000, 0x478), process.reads)
        process = FakeReadOnlyProcess()
        handler = bytearray(process.blocks[0x300000])
        struct.pack_into("<Q", handler, 0x58, 0x140000000 + 0x4135FB0)
        process.blocks[0x300000] = bytes(handler)
        with self.assertRaisesRegex(ValueError, "handler vtables"):
            sample_bounded_topbar_once(process)
        self.assertNotIn((0x400000, 0xF90), process.reads)


if __name__ == "__main__":
    unittest.main()
