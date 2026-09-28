from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))

from war_cash_topbar_owner_path import inspect_supplied_topbar_owner_path


BASE = 0x140000000
OWNER = 0x100000
IDLER = 0x200000
HANDLER = 0x300000
TOPBAR = 0x400000
CONTEXT = 0x500000


def fixture() -> dict[str, object]:
    global_slot = struct.pack("<Q", OWNER)
    global_owner = bytearray(0x18)
    struct.pack_into("<Q", global_owner, 0x10, IDLER)
    idler = bytearray(0x90)
    struct.pack_into("<Q", idler, 0, BASE + 0x40B1D30)
    struct.pack_into("<Q", idler, 0x88, HANDLER)
    handler = bytearray(0x478)
    struct.pack_into("<Q", handler, 0, BASE + 0x40AF630)
    struct.pack_into("<Q", handler, 0x40, CONTEXT)
    struct.pack_into("<Q", handler, 0x58, BASE + 0x40AF6A8)
    struct.pack_into("<Q", handler, 0x470, TOPBAR)
    topbar = bytearray(0xF90)
    struct.pack_into("<Q", topbar, 0, BASE + 0x40E6F68)
    struct.pack_into("<Q", topbar, 0x10, BASE + 0x40E7038)
    struct.pack_into("<Q", topbar, 0xC8, CONTEXT)
    struct.pack_into("<Q", topbar, 0xD0, HANDLER)
    return {
        "image_base": BASE,
        "global_slot_address": BASE + 0x570F7B8,
        "global_slot_bytes": global_slot,
        "global_owner_address": OWNER,
        "global_owner_bytes": bytes(global_owner),
        "idler_address": IDLER,
        "idler_bytes": bytes(idler),
        "handler_address": HANDLER,
        "handler_bytes": bytes(handler),
        "topbar_address": TOPBAR,
        "topbar_bytes": bytes(topbar),
    }


class TopbarOwnerPathTests(unittest.TestCase):
    def test_exact_owner_chain_is_diagnostic_only(self) -> None:
        result = inspect_supplied_topbar_owner_path(**fixture())
        self.assertEqual(result["topbar_address"], hex(TOPBAR))
        self.assertFalse(result["unique_live_topbar_instance_proven"])
        self.assertFalse(result["formal_cash_eligible"])

    def test_each_forward_or_reverse_link_must_match(self) -> None:
        for field, offset, wrong, reason in (
            ("global_slot_bytes", 0, IDLER, "global slot"),
            ("global_owner_bytes", 0x10, HANDLER, "global owner"),
            ("idler_bytes", 0x88, TOPBAR, "idler does not"),
            ("handler_bytes", 0x470, IDLER, "handler does not"),
            ("topbar_bytes", 0xC8, OWNER, "topbar context"),
            ("topbar_bytes", 0xD0, IDLER, "reverse handler"),
        ):
            candidate = fixture()
            data = bytearray(candidate[field])
            struct.pack_into("<Q", data, offset, wrong)
            candidate[field] = bytes(data)
            with self.subTest(field=field, offset=offset), self.assertRaisesRegex(
                ValueError, reason,
            ):
                inspect_supplied_topbar_owner_path(**candidate)

    def test_vtable_or_module_base_mismatch_is_rejected(self) -> None:
        for field, offset, reason in (
            ("idler_bytes", 0, "idler primary"),
            ("handler_bytes", 0, "handler double"),
            ("handler_bytes", 0x58, "handler double"),
            ("topbar_bytes", 0, "topbar double"),
            ("topbar_bytes", 0x10, "topbar double"),
        ):
            candidate = fixture()
            data = bytearray(candidate[field])
            struct.pack_into("<Q", data, offset, BASE + 0x4135EE0)
            candidate[field] = bytes(data)
            with self.subTest(field=field, offset=offset), self.assertRaisesRegex(
                ValueError, reason,
            ):
                inspect_supplied_topbar_owner_path(**candidate)
        candidate = fixture()
        candidate["image_base"] = BASE + 0x10000
        candidate["global_slot_address"] = candidate["image_base"] + 0x570F7B8
        with self.assertRaisesRegex(ValueError, "vtable"):
            inspect_supplied_topbar_owner_path(**candidate)

    def test_invalid_address_and_short_bytes_fail_closed(self) -> None:
        candidate = fixture()
        candidate["handler_address"] = 0
        with self.assertRaisesRegex(ValueError, "user-mode address"):
            inspect_supplied_topbar_owner_path(**candidate)
        candidate = fixture()
        candidate["handler_bytes"] = candidate["handler_bytes"][:-1]
        with self.assertRaisesRegex(ValueError, "exactly"):
            inspect_supplied_topbar_owner_path(**candidate)
        candidate = fixture()
        candidate["global_slot_address"] += 8
        with self.assertRaisesRegex(ValueError, "exact-build RVA"):
            inspect_supplied_topbar_owner_path(**candidate)
        candidate = fixture()
        candidate["topbar_address"] = HANDLER + 0x400
        with self.assertRaisesRegex(ValueError, "overlap"):
            inspect_supplied_topbar_owner_path(**candidate)


if __name__ == "__main__":
    unittest.main()
