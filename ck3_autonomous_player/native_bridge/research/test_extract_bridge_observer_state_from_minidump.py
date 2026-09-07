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


if __name__ == "__main__":
    unittest.main()
