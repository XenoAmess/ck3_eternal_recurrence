#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("extract_bridge_observer_state_from_minidump.py")
SPEC = importlib.util.spec_from_file_location("extract_bridge_observer_state", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ExtractBridgeObserverStateTests(unittest.TestCase):
    def test_map_parser_finds_private_static_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bridge.map"
            path.write_text(
                " bridge\n"
                " Preferred load address is 0000000180000000\n\n"
                " Static symbols\n"
                " 0003:00000000 ?g_named_path_583_root_observer_v1@anon@@3UA "
                "0000000180019230 bridge.cpp.obj\n",
                encoding="utf-8",
            )
            base, symbols = MODULE.parse_linker_map(path)
        self.assertEqual(base, 0x180000000)
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].rva, 0x19230)

    def test_cold_map_decoder_uses_frozen_x64_layout(self) -> None:
        state = bytearray(0x1A8)
        struct.pack_into("<III", state, 0, 1, 7, 0)
        struct.pack_into("<Q", state, 0x10, 1)
        struct.pack_into("<Q", state, 0x40, 2)
        struct.pack_into("<I", state, 0x50, 1)
        struct.pack_into("<Q", state, 0x78, 3)
        struct.pack_into("<I", state, 0x90, 1)
        struct.pack_into("<Q", state, 0xB8, 0x7FF600000000)
        decoded = MODULE.decode_cold_map(bytes(state))
        self.assertTrue(decoded["installed"])
        self.assertEqual(decoded["installed_mask"], 7)
        self.assertEqual(decoded["ctor"]["count"], 1)
        self.assertEqual(decoded["variant"]["count"], 2)
        self.assertEqual(decoded["poll"]["count"], 3)
        self.assertEqual(decoded["module_base"], "0x00007FF600000000")

    def test_named_path_decoder_reports_only_published_slots(self) -> None:
        state = bytearray(0x1468)
        struct.pack_into("<III", state, 0, 1, 3, 0)
        slot = 0x50 + 5 * 0x138
        struct.pack_into("<Q", state, slot, 9)
        struct.pack_into("<I", state, slot + 8, 42)
        struct.pack_into("<Q", state, slot + 0x20, 0x1234)
        struct.pack_into("<I", state, slot + 0x20 + 0x30, 1)
        decoded = MODULE.decode_named_path(bytes(state))
        self.assertEqual(decoded["installed_mask"], 3)
        self.assertEqual(len(decoded["slots"]), 1)
        self.assertEqual(decoded["slots"][0]["index"], 5)
        self.assertTrue(decoded["slots"][0]["resolver"]["null_result"])

    def test_pdx_paths_decoder_uses_frozen_x64_layout(self) -> None:
        state = bytearray(0x290)
        struct.pack_into("<III", state, 0, 1, 0x1F, 0)
        struct.pack_into("<Q", state, 0x18, 1)
        struct.pack_into("<Q", state, 0x30 + 0x10, 7)
        struct.pack_into("<Q", state, 0x68, 1)
        struct.pack_into("<Q", state, 0x68 + 8, 1)
        struct.pack_into("<I", state, 0x108, 0x583)
        struct.pack_into("<I", state, 0x10C, 0xC0242C1D)
        struct.pack_into("<I", state, 0x188 + 0x20, 1)
        decoded = MODULE.decode_pdx_paths(bytes(state))
        self.assertEqual(decoded["task_enter_count"], 1)
        self.assertEqual(decoded["task_table"]["count"], 7)
        self.assertEqual(decoded["paths_lookup"]["return_count"], 1)
        self.assertEqual(decoded["last_key"], 0x583)
        self.assertEqual(decoded["last_hash"], "0xC0242C1D")
        self.assertTrue(decoded["table_after"]["id_583_present"])

    def test_vfs_mount_lifecycle_decoder_uses_frozen_x64_layout(self) -> None:
        state = bytearray(0x33F8)
        struct.pack_into("<III", state, 0, 1, 0x0F, 0)
        struct.pack_into("<Q", state, 0x10, 17)
        struct.pack_into("<QIIQ", state, 0x18, 1, 1, 42, 9)
        struct.pack_into("<QQII", state, 0x30, 0x1000, 0x2000, 1, 0)
        for offset, value in zip(
            range(0x48, 0x88, 8), (2, 2, 1, 1, 0, 0, 14, 17)
        ):
            struct.pack_into("<Q", state, offset, value)

        slot = 0x88 + 3 * 0xC8
        struct.pack_into("<QQQ", state, slot, 4, 14, 15)
        struct.pack_into("<IIII", state, slot + 0x18, 42, 42, 1, 1)
        struct.pack_into("<QQI", state, slot + 0x28, 0xAAAA, 0xBBBB, 1)
        path = slot + 0x40
        struct.pack_into("<QIIII", state, path, 0x3000, 4, 1, 0, 0)
        state[path + 0x18 : path + 0x1C] = b"game"
        struct.pack_into("<QQII", state, slot + 0x98, 0x1000, 0x2000, 1, 0)
        struct.pack_into("<QQII", state, slot + 0xB0, 0x1000, 0x4000, 1, 0)

        paths = 0x3288
        struct.pack_into(
            "<QQQIIIIQ", state, paths,
            1, 0x5000, 0x5010, 14, 0, 42, 0, 16
        )
        struct.pack_into("<QQII", state, paths + 0x30, 0x1000, 0x4000, 1, 0)
        checksummed = 0x32D0
        struct.pack_into(
            "<QQQIIIIQ", state, checksummed,
            1, 0x6000, 0x6010, 26, 1, 42, 0, 17
        )
        struct.pack_into(
            "<QQII", state, checksummed + 0x30, 0x1000, 0x4000, 1, 0
        )
        struct.pack_into("<Q", state, 0x3318, 3)
        runtime_values = (
            0x140000000,
            0x143B5C410,
            0x143BE18C5,
            0x143BE1A0C,
            0x143BE23A4,
            0x14585FA30,
        )
        for index, value in enumerate(runtime_values):
            struct.pack_into("<Q", state, 0x3320 + index * 8, value)
        for index, patch_size in enumerate((5, 5, 5, 8)):
            hook = 0x3350 + index * 0x20
            struct.pack_into("<QQ", state, hook, 0x140000000 + index, patch_size)
            state[hook + 0x10 : hook + 0x18] = bytes([index + 1]) * 8
            state[hook + 0x18 : hook + 0x20] = bytes([0xE8 + index]) * 8
        struct.pack_into("<QQQQQ", state, 0x33D0, 1, 2, 3, 4, 5)

        decoded = MODULE.decode_vfs_mount_lifecycle(bytes(state))
        self.assertTrue(decoded["installed"])
        self.assertEqual(decoded["installed_mask"], 0x0F)
        self.assertEqual(decoded["next_sequence"], 17)
        self.assertEqual(decoded["core_init"]["raw_al"], 1)
        self.assertEqual(decoded["core_init"]["manager"]["head"],
                         "0x0000000000002000")
        self.assertEqual(decoded["publisher"]["entry_count"], 2)
        self.assertEqual(len(decoded["publisher"]["slots"]), 1)
        self.assertEqual(decoded["publisher"]["slots"][0]["index"], 3)
        self.assertEqual(
            decoded["publisher"]["slots"][0]["path"]["preview_text"], "game"
        )
        self.assertEqual(
            decoded["publisher"]["slots"][0]["manager_after"]["head"],
            "0x0000000000004000",
        )
        self.assertEqual(decoded["paths_lookup"]["path_length"], 14)
        self.assertEqual(decoded["checksummed_lookup"]["path_length"], 26)
        self.assertEqual(decoded["lookup_classification_fault_count"], 3)
        self.assertEqual(decoded["hooks"][3]["patch_size"], 8)
        self.assertEqual(decoded["manager_address"], "0x000000014585FA30")
        self.assertEqual(
            MODULE.OBSERVERS["vfs_mount_lifecycle_observer_v1"][1], 0x33F8
        )


if __name__ == "__main__":
    unittest.main()
