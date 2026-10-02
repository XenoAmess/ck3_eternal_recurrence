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
    PLAYED_CHARACTER_ID_GLOBAL_RVA,
    sample_bounded_topbar_once, sample_bounded_topbar_twice,
)


ROW_ADDRESS = 0x600000


class FakeReadOnlyProcess:
    base = 0x140000000

    def __init__(self, *, changing_rows: bool = False,
                 changing_total: bool = False,
                 changing_render_frame: bool = False,
                 changing_player_after_read: int | None = None,
                 render_clock: bool = False) -> None:
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
        self.player_reads = 0
        self.changing_player_after_read = changing_player_after_read
        self.reads: list[tuple[int, int]] = []
        self.blocks = {
            supplied["global_slot_address"]: supplied["global_slot_bytes"],
            supplied["global_owner_address"]: supplied["global_owner_bytes"],
            supplied["idler_address"]: supplied["idler_bytes"],
            supplied["handler_address"]: supplied["handler_bytes"],
            supplied["topbar_address"]: bytes(topbar),
            self.base + PLAYED_CHARACTER_ID_GLOBAL_RVA:
                struct.pack("<I", 29829),
            0x700000: self.name,
        }
        if render_clock:
            context = bytearray(0x188)
            struct.pack_into("<Q", context, 0x180, 45)
            self.blocks[self.base + 0x576CC68] = struct.pack("<Q", 0x800000)
            self.blocks[0x800000] = bytes(context)
            self.blocks[self.base + 0x570D8D0] = struct.pack("<i", 8)

    def read(self, address: int, size: int) -> bytes:
        self.reads.append((address, size))
        if address == self.base + PLAYED_CHARACTER_ID_GLOBAL_RVA:
            self.player_reads += 1
            if (self.changing_player_after_read is not None
                    and self.player_reads > self.changing_player_after_read):
                return struct.pack("<I", 29830)
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
        self.assertTrue(sample["same_global_played_character_id"])
        self.assertEqual(sample["first"]["global_played_character_id_candidate"],
                         29829)
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

    def test_bounded_render_epoch_is_only_a_diagnostic(self) -> None:
        sample = sample_bounded_topbar_twice(
            FakeReadOnlyProcess(render_clock=True))
        self.assertEqual(sample["status"], "stable_supplied_bytes_diagnostic_only")
        self.assertTrue(sample["render_clock_monotonic_candidate"])
        epoch = sample["first"]["render_epoch"]
        self.assertEqual(epoch["current_render_tick_candidate"], 45)
        self.assertEqual(epoch["topbar_last_update_tick_candidate"], 42)
        self.assertEqual(epoch["stock_refresh_interval_render_ticks_candidate"], 8)
        self.assertFalse(epoch["getter_refresh_due_if_called_candidate"])
        self.assertFalse(epoch["cache_refresh_completed_proven"])
        self.assertFalse(sample["same_frame_cache_freshness_proven"])

    def test_missing_render_context_does_not_claim_freshness(self) -> None:
        sample = sample_bounded_topbar_twice(FakeReadOnlyProcess())
        self.assertIsNone(sample["first"]["render_epoch"])
        self.assertIsNotNone(sample["first"]["render_epoch_missing_reason"])
        self.assertFalse(sample["render_clock_monotonic_candidate"])
        self.assertFalse(sample["same_frame_cache_freshness_proven"])

    def test_rejected_cache_headers_preserve_bounded_scalar_diagnostics(self) -> None:
        process = FakeReadOnlyProcess(render_clock=True)
        topbar = bytearray(process.blocks[0x400000])
        struct.pack_into("<QII", topbar, 0xAD8, 0, 0, 0)
        struct.pack_into("<Q", topbar, 0xF88, 0)
        process.blocks[0x400000] = bytes(topbar)
        process.blocks[process.base + 0x570D8D0] = struct.pack("<i", 0)
        sample = sample_bounded_topbar_twice(process)
        first = sample["first"]
        self.assertEqual(sample["status"],
                         "RED_owner_or_expense_bytes_changed_or_unavailable")
        self.assertIsNone(first["expense_layout"])
        self.assertEqual(first["expense_header_diagnostic"], {
            "row_array_address_candidate": "0x0",
            "row_array_pointer_class": "zero",
            "row_capacity_candidate": 0,
            "row_count_candidate": 0,
            "expense_object_address_candidate": "0x400ad8",
            "value_breakdown_back_pointer_candidate": "0x400ad8",
            "back_pointer_matches_expense_object_candidate": True,
            "expense_total_signed_raw_candidate": -2_500_000,
            "expense_total_scale_candidate": 100_000,
            "total_scale_matches_q100000_candidate": True,
            "formal_cash_eligible": False,
        })
        self.assertIsNone(first["render_epoch"])
        self.assertEqual(first["render_header_diagnostic"], {
            "topbar_last_update_tick_candidate": 0,
            "render_context_address_candidate": "0x800000",
            "current_render_tick_candidate": 45,
            "stock_refresh_interval_render_ticks_candidate": 0,
            "formal_cash_eligible": False,
        })
        self.assertEqual(process.row_reads, 0)
        self.assertLess(sample["total_target_memory_bytes_read"], 128 * 1024)
        self.assertFalse(sample["formal_cash_eligible"])

    def test_unaligned_vector_pointer_is_retained_without_following_it(self) -> None:
        process = FakeReadOnlyProcess()
        topbar = bytearray(process.blocks[0x400000])
        struct.pack_into("<Q", topbar, 0xAD8, ROW_ADDRESS + 1)
        process.blocks[0x400000] = bytes(topbar)
        sample = sample_bounded_topbar_once(process)
        self.assertEqual(sample["expense_header_diagnostic"]
                         ["row_array_pointer_class"], "unaligned")
        self.assertIsNone(sample["expense_layout"])
        self.assertEqual(process.row_reads, 0)
        self.assertFalse(sample["formal_cash_eligible"])

    def test_wrong_object_back_pointer_stays_diagnostic_and_red(self) -> None:
        process = FakeReadOnlyProcess()
        topbar = bytearray(process.blocks[0x400000])
        struct.pack_into("<Q", topbar, 0xB68, 0x500AD8)
        process.blocks[0x400000] = bytes(topbar)
        sample = sample_bounded_topbar_twice(process)
        header = sample["first"]["expense_header_diagnostic"]
        self.assertEqual(header["row_array_pointer_class"],
                         "aligned_user_address_candidate")
        self.assertEqual(header["value_breakdown_back_pointer_candidate"],
                         "0x500ad8")
        self.assertFalse(header["back_pointer_matches_expense_object_candidate"])
        self.assertEqual(process.row_reads, 2)
        self.assertIsNone(sample["first"]["expense_layout"])
        self.assertEqual(sample["status"],
                         "RED_owner_or_expense_bytes_changed_or_unavailable")
        self.assertFalse(sample["formal_cash_eligible"])

    def test_wrong_total_scale_cannot_become_expense_evidence(self) -> None:
        process = FakeReadOnlyProcess()
        topbar = bytearray(process.blocks[0x400000])
        struct.pack_into("<Q", topbar, 0xB58, 1)
        process.blocks[0x400000] = bytes(topbar)
        sample = sample_bounded_topbar_twice(process)
        header = sample["first"]["expense_header_diagnostic"]
        self.assertEqual(header["expense_total_scale_candidate"], 1)
        self.assertFalse(header["total_scale_matches_q100000_candidate"])
        self.assertIsNone(sample["first"]["expense_layout"])
        self.assertFalse(sample["same_expense_rows"])
        self.assertFalse(sample["formal_cash_eligible"])

    def test_player_switch_during_or_between_passes_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "CharacterID changed"):
            sample_bounded_topbar_once(FakeReadOnlyProcess(
                changing_player_after_read=1))
        sample = sample_bounded_topbar_twice(FakeReadOnlyProcess(
            changing_player_after_read=2))
        self.assertFalse(sample["same_global_played_character_id"])
        self.assertEqual(sample["status"],
                         "RED_owner_or_expense_bytes_changed_or_unavailable")
        self.assertFalse(sample["formal_cash_eligible"])

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
