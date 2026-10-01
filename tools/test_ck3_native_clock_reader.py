from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

import ck3_native_clock_reader as clock
import ck3_native_profile_mcp as profile_mcp
from test_ck3_native_profile_mcp import Backend, fixture


class MemoryFixture:
    def __init__(self):
        self.contract = clock.source_contract()
        self.image_base = 0x140000000
        self.memory = {}
        self.game, self.jomini = 0x200000000, 0x300000000
        self.players, self.data, self.entries, self.entry = 0x400000000, 0x500000000, 0x600000000, 0x700000000
        self.put(self.image_base + self.contract["game_slot"], "<Q", self.game)
        self.put(self.image_base + self.contract["jomini_slot"], "<Q", self.jomini)
        game, jomini = bytearray(0xB0), bytearray(0x21)
        struct.pack_into("<i", game, self.contract["date_offset"], 53169336)
        struct.pack_into("<i", game, self.contract["speed_offset"], 4)
        struct.pack_into("<Q", game, 0xA0, self.data)
        struct.pack_into("<Q", jomini, 0x18, self.players)
        jomini[self.contract["paused_offset"]] = 1
        self.bytes(self.game, game)
        self.bytes(self.jomini, jomini)
        self.put(self.players + 0x1F0, "<i", 0)
        manager = self.data + self.contract["player_manager"]
        self.put(manager + 0x58, "<Q", self.entries)
        self.put(manager + 0x64, "<i", 1)
        self.put(self.entries, "<Q", self.entry)
        self.put(self.entry + 0xD8, "<i", 0)
        self.put(self.entry + 0xB0, "<i", 29829)

    def bytes(self, address, value):
        self.memory.update({address + index: byte for index, byte in enumerate(value)})

    def put(self, address, format, value):
        self.bytes(address, struct.pack(format, value))

    def read(self, address, size):
        return bytes(self.memory[address + offset] for offset in range(size))


class ClockReaderTests(unittest.TestCase):
    def test_source_bound_clock_preserves_native_raw_fields_and_read_only_rights(self):
        reader = MemoryFixture()
        result = clock.read_bound_clock(reader, reader.contract)
        self.assertEqual((result["date_raw"], result["speed"], result["paused"]), (53169336, 5, True))
        self.assertEqual(result["played_character_id"], 29829)
        self.assertEqual(result["process_access"], 0x0410)
        self.assertEqual(result["raw_units_per_day"], 24)
        self.assertEqual(result["calendar_projection"], "unbound_requires_independent_save_date")
        self.assertEqual(len(result["source_contract"]["source_sha256"]), 64)
        self.assertEqual(result["source_contract"]["game_slot"], 0x5C68C50)

    def test_boot_null_player_collection_and_invalid_speed_are_rejected(self):
        for mode in ("game", "jomini", "players", "player", "data", "count", "character", "date", "speed"):
            with self.subTest(mode=mode):
                reader = MemoryFixture()
                if mode in {"game", "jomini"}:
                    reader.put(reader.image_base + reader.contract[f"{mode}_slot"], "<Q", 0)
                elif mode == "players":
                    reader.put(reader.jomini + 0x18, "<Q", 0)
                elif mode == "player":
                    reader.put(reader.players + 0x1F0, "<i", -1)
                elif mode == "data":
                    reader.put(reader.game + 0xA0, "<Q", 0)
                elif mode == "count":
                    reader.put(reader.data + reader.contract["player_manager"] + 0x64, "<i", 0)
                elif mode == "character":
                    reader.put(reader.entry + 0xB0, "<i", -1)
                elif mode == "date":
                    reader.put(reader.game + reader.contract["date_offset"], "<i", 0)
                else:
                    reader.put(reader.game + reader.contract["speed_offset"], "<i", 5)
                with self.assertRaises(RuntimeError):
                    clock.read_bound_clock(reader, reader.contract)

    def test_incomplete_prefix_and_timeline_changes_are_rejected(self):
        reader = MemoryFixture()
        with self.assertRaises(RuntimeError):
            clock.decode_clock(b"", b"", reader.contract)
        original = reader.read
        count = 0
        def read_changing(address, size):
            nonlocal count
            if address == reader.game:
                count += 1
                reader.put(reader.game + reader.contract["date_offset"], "<i", 53169336 + count * 24)
            return original(address, size)
        reader.read = read_changing
        with self.assertRaisesRegex(RuntimeError, "stabilize"):
            clock.read_bound_clock(reader, reader.contract)

    def test_wrong_build_cannot_open_process(self):
        with patch.object(clock, "WindowsReadOnlyMemory") as reader:
            with self.assertRaisesRegex(RuntimeError, "exact"):
                clock.read_live_clock(11, "ck3.exe", "0" * 64, "1.20.0.2")
            reader.assert_not_called()

    def test_windows_process_handle_requests_no_write_or_create_thread_access(self):
        import win32process
        kernel = Mock()
        kernel.OpenProcess.return_value = 123
        with patch.object(clock.ctypes, "WinDLL", return_value=kernel), \
                patch.object(win32process, "EnumProcessModules", return_value=[0x140000000]), \
                patch.object(win32process, "GetModuleFileNameEx", return_value=str(Path("ck3.exe").resolve())):
            reader = clock.WindowsReadOnlyMemory(11, str(Path("ck3.exe").resolve()))
            kernel.OpenProcess.assert_called_once_with(0x0410, False, 11)
            reader.close()
            kernel.CloseHandle.assert_called_once_with(123)


class ClockMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_mcp_clock_is_closed_no_argument_and_does_not_attach(self):
        from mcp import Client
        with tempfile.TemporaryDirectory() as temporary:
            profile, path = fixture(Path(temporary))
            payload = json.loads(path.read_text())
            for key in ("state_directory", "dll", "injector"):
                del payload[key]
            path.write_text(json.dumps(payload), encoding="utf-8")
            profile = profile_mcp.load_clock_profile(path)
            backend = Backend(profile)
            reader = MemoryFixture()
            backend.read_clock = lambda _: clock.read_bound_clock(reader, reader.contract)
            service = profile_mcp.NativeClockProfileService(profile, backend=backend)
            async with Client(profile_mcp.create_clock_server(service)) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual([tool.name for tool in tools], ["ck3_read_profile_native_clock_v1"])
                self.assertEqual(tools[0].input_schema["properties"], {})
                self.assertFalse(tools[0].input_schema["additionalProperties"])
                rejected = await client.call_tool("ck3_read_profile_native_clock_v1", {"pid": 99, "address": 1})
                self.assertTrue(rejected.is_error)
                result = await client.call_tool("ck3_read_profile_native_clock_v1", {})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["clock"]["date_raw"], 53169336)
                self.assertFalse(result.structured_content["uses_injection"])
                self.assertFalse(result.structured_content["writes_process_memory"])
                self.assertEqual(backend.injections, [])
                self.assertIsNone(service.driver)


if __name__ == "__main__":
    unittest.main()
