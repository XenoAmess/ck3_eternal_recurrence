from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player" / "native_bridge"
CONTRACT_PATH = (
    NATIVE
    / "research"
    / "fixtures"
    / "startup_rbx_null_call_guard_v1_source_contract.json"
)
GAME_EXE = ROOT.parent / "Crusader Kings III" / "binaries" / "ck3.exe"


def _sections(image: bytes) -> list[tuple[int, int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    assert image[pe : pe + 4] == b"PE\0\0"
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    table = pe + 24 + optional_size
    return [
        (
            struct.unpack_from("<I", image, table + index * 40 + 12)[0],
            struct.unpack_from("<I", image, table + index * 40 + 8)[0],
            struct.unpack_from("<I", image, table + index * 40 + 16)[0],
            struct.unpack_from("<I", image, table + index * 40 + 20)[0],
        )
        for index in range(count)
    ]


def _offset(image: bytes, rva: int) -> int:
    for virtual_address, virtual_size, raw_size, raw_offset in _sections(image):
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            delta = rva - virtual_address
            assert delta < raw_size
            return raw_offset + delta
    raise AssertionError(f"RVA not mapped: {rva:#x}")


def _at(image: bytes, rva: int, size: int) -> bytes:
    offset = _offset(image, rva)
    return image[offset : offset + size]


class StartupRbxNullCallGuardV1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.image = GAME_EXE.read_bytes()

    def test_exact_build_and_single_caller_anchor(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.image).hexdigest().upper(),
            self.contract["exact_build"]["executable_sha256"],
        )
        caller = self.contract["caller"]
        patch = bytes.fromhex(caller["patch_bytes_hex"])
        production = bytes.fromhex(caller["production_anchor_bytes_hex"])
        self.assertEqual(_at(self.image, int(caller["patch_rva"], 16), 16), patch)
        self.assertEqual(
            _at(self.image, int(caller["patch_rva"], 16), 36), production
        )
        displacement = struct.unpack_from("<i", patch, 12)[0]
        resolved = int(caller["direct_call_rva"], 16) + 5 + displacement
        self.assertEqual(resolved, int(caller["call_target_rva"], 16))
        self.assertEqual(
            int(caller["continue_rva"], 16), int(caller["patch_rva"], 16) + 16
        )

    def test_null_argument_call_edge_and_crash_instruction_are_bound(self) -> None:
        self.assertEqual(
            _at(self.image, 0x390A9E2, 36),
            bytes.fromhex(
                "48 89 5D 6F 48 8B 55 77 48 8B CB E8 3E C9 25 00 "
                "90 48 85 DB 74 0E 48 8B 03 BA 01 00 00 00 48 8B "
                "CB FF 10 90"
            ),
        )
        self.assertEqual(
            _at(self.image, 0x3B67330, 25),
            bytes.fromhex(
                "48 89 6C 24 10 48 89 74 24 18 48 89 7C 24 20 41 "
                "56 48 83 EC 20 48 8B 79 08"
            ),
        )
        self.assertEqual(_at(self.image, 0x3B67345, 4), bytes.fromhex("48 8B 79 08"))

    def test_pdata_owner_and_unwind_prologue_are_exact(self) -> None:
        caller = self.contract["caller"]
        begin, end, unwind = struct.unpack(
            "<III", _at(self.image, int(caller["pdata_row_rva"], 16), 12)
        )
        self.assertEqual(begin, int(caller["owner_begin_rva"], 16))
        self.assertEqual(end, int(caller["owner_end_rva"], 16))
        self.assertEqual(unwind, int(caller["unwind_info_rva"], 16))
        unwind_header = _at(self.image, unwind, 4)
        self.assertEqual(unwind_header[1], caller["unwind_size_of_prolog"])
        callee = self.contract["callee"]
        callee_begin, callee_end, callee_unwind = struct.unpack(
            "<III", _at(self.image, int(callee["pdata_row_rva"], 16), 12)
        )
        self.assertEqual(callee_begin, int(callee["begin_rva"], 16))
        self.assertEqual(callee_end, int(callee["end_rva"], 16))
        self.assertEqual(callee_unwind, int(callee["unwind_info_rva"], 16))
        self.assertEqual(
            _at(self.image, callee_unwind, 4)[1],
            callee["unwind_size_of_prolog"],
        )

    def test_source_and_build_wiring_remain_default_off_and_caller_local(self) -> None:
        header = (
            NATIVE / "include/xar_bridge/startup_rbx_null_call_guard_v1.hpp"
        ).read_text(encoding="utf-8")
        source = (
            NATIVE / "src/startup_rbx_null_call_guard_v1.cpp"
        ).read_text(encoding="utf-8")
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        for token in (
            "0x390A700",
            "0x390A9E2",
            "0x390A9F2",
            "0x3B67330",
            "kStartupRbxNullCallGuardInstalledByDefaultV1 =\n    false",
        ):
            self.assertIn(token, header)
        self.assertIn("null-RBX callsite", source)
        self.assertIn("state.call_target", source)
        self.assertNotIn("kStartupRbxNullCallTargetRvaV1,\n    kStartupRbxNullCallPatchBytesV1", source)
        self.assertIn("XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1", cmake)
        option_tail = cmake.split(
            "option(\n  XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1", 1
        )[1].split(")", 1)[0]
        self.assertIn("OFF", option_tail)
        self.assertIn("InstallStartupRbxNullCallGuardV1", bridge)
        self.assertIn("UninstallStartupWidgetNullFlagCallGuardV1", bridge)
        semantics = self.contract["guard_semantics"]
        self.assertFalse(semantics["global_callee_patch"])
        self.assertFalse(semantics["default_enabled"])


if __name__ == "__main__":
    unittest.main()
