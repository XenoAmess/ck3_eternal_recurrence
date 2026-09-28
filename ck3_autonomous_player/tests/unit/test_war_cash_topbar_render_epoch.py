from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))

from war_cash_topbar_render_epoch import inspect_supplied_topbar_render_epoch


BASE = 0x140000000
CONTEXT = 0x800000


def fixture(*, tick: int = 45, last: int = 42,
            interval: int = 8) -> dict[str, object]:
    topbar = bytearray(0xF90)
    context = bytearray(0x188)
    struct.pack_into("<Q", topbar, 0xF88, last)
    struct.pack_into("<Q", context, 0x180, tick)
    return {
        "image_base": BASE,
        "topbar_bytes": bytes(topbar),
        "render_context_slot_address": BASE + 0x576CC68,
        "render_context_slot_bytes": struct.pack("<Q", CONTEXT),
        "render_context_address": CONTEXT,
        "render_context_bytes": bytes(context),
        "refresh_interval_address": BASE + 0x570D8D0,
        "refresh_interval_bytes": struct.pack("<i", interval),
    }


class TopbarRenderEpochTests(unittest.TestCase):
    def test_stock_interval_is_diagnostic_only(self) -> None:
        observed = inspect_supplied_topbar_render_epoch(**fixture())
        self.assertEqual(observed["render_tick_lag"], 3)
        self.assertFalse(observed["getter_refresh_due_if_called_candidate"])
        self.assertFalse(observed["cache_refresh_completed_proven"])
        self.assertFalse(observed["same_native_revision_proven"])
        self.assertFalse(observed["formal_cash_eligible"])
        due = inspect_supplied_topbar_render_epoch(
            **fixture(tick=50, last=42))
        self.assertTrue(due["getter_refresh_due_if_called_candidate"])
        self.assertFalse(due["getter_called_in_this_sample"])

    def test_mismatched_or_invalid_supplied_bytes_are_rejected(self) -> None:
        for changed in (
            {"render_context_slot_bytes": struct.pack("<Q", CONTEXT + 8)},
            {"refresh_interval_address": BASE + 0x570D8D4},
            {"refresh_interval_bytes": struct.pack("<i", 0)},
            {"render_context_bytes": b""},
            {"topbar_bytes": b""},
        ):
            with self.subTest(changed=changed):
                supplied = fixture()
                supplied.update(changed)
                with self.assertRaises(ValueError):
                    inspect_supplied_topbar_render_epoch(**supplied)
        with self.assertRaisesRegex(ValueError, "render tick"):
            inspect_supplied_topbar_render_epoch(
                **fixture(tick=41, last=42))


if __name__ == "__main__":
    unittest.main()
