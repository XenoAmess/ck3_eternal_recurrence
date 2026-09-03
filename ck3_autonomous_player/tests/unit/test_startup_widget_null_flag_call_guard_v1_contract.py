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
    / "startup_widget_null_flag_call_guard_v1_source_contract.json"
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


class StartupWidgetNullFlagCallGuardV1ContractTests(unittest.TestCase):
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
        self.assertEqual(_at(self.image, int(caller["patch_rva"], 16), 13), patch)
        self.assertEqual(
            _at(self.image, int(caller["patch_rva"], 16), 29), production
        )
        displacement = struct.unpack_from("<i", patch, 9)[0]
        resolved = int(caller["direct_call_rva"], 16) + 5 + displacement
        self.assertEqual(resolved, int(caller["call_target_rva"], 16))
        self.assertEqual(
            int(caller["continue_rva"], 16), int(caller["patch_rva"], 16) + 13
        )

    def test_null_producer_failure_edge_and_crash_instruction_are_bound(self) -> None:
        self.assertEqual(
            _at(self.image, 0xAF4EBE, 21),
            bytes.fromhex(
                "E8 3D 69 BC 02 48 8B F8 48 85 C0 75 08 33 C9 "
                "E8 4E 60 BA 02 90"
            ),
        )
        self.assertEqual(
            _at(self.image, 0x369CB45, 22),
            bytes.fromhex(
                "48 8B F1 45 0F B6 F0 0F B6 CA 0F B6 FA 80 F1 01 "
                "C0 E1 04 0F B6 86"
            ),
        )
        self.assertEqual(_at(self.image, 0x369CB58, 7), bytes.fromhex("0F B6 86 D0 00 00 00"))

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

    def test_source_and_build_wiring_remain_default_off_and_caller_local(self) -> None:
        header = (
            NATIVE / "include/xar_bridge/startup_widget_null_flag_call_guard_v1.hpp"
        ).read_text(encoding="utf-8")
        source = (
            NATIVE / "src/startup_widget_null_flag_call_guard_v1.cpp"
        ).read_text(encoding="utf-8")
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        for token in (
            "0xAF4C90",
            "0xAF4EE0",
            "0xAF4EED",
            "0x369CB30",
            "kStartupWidgetNullFlagCallGuardInstalledByDefaultV1 =\n    false",
        ):
            self.assertIn(token, header)
        self.assertIn("test rdi,rdi; jz null", source)
        self.assertIn("state.call_target", source)
        self.assertNotIn("kStartupWidgetNullFlagCallTargetRvaV1,\n    kStartupWidgetNullFlagCallPatchBytesV1", source)
        self.assertIn("XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1", cmake)
        option_tail = cmake.split(
            "option(\n  XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1", 1
        )[1].split(")", 1)[0]
        self.assertIn("OFF", option_tail)
        self.assertIn("InstallStartupWidgetNullFlagCallGuardV1", bridge)
        self.assertIn("UninstallStartupLocalizeCurrentRootGuardV1", bridge)
        semantics = self.contract["guard_semantics"]
        self.assertFalse(semantics["global_callee_patch"])
        self.assertFalse(semantics["default_enabled"])


if __name__ == "__main__":
    unittest.main()
