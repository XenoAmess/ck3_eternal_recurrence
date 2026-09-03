from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
BRIDGE = ROOT / "native_bridge"
CONTRACT = BRIDGE / "research" / "fixtures" / "cold_map_vfs_observer_v1_source_contract.json"
EXE = REPO.parent / "Crusader Kings III" / "binaries" / "ck3.exe"


class ColdMapVfsObserverContractTest(unittest.TestCase):
    def test_exact_build_anchors_and_pdata(self) -> None:
        import pefile

        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(EXE.read_bytes()).hexdigest().upper(),
                         contract["exact_build"]["executable_sha256"])
        pe = pefile.PE(str(EXE), fast_load=False)
        entries = list(pe.DIRECTORY_ENTRY_EXCEPTION)
        for hook in contract["hooks"]:
            rva = int(hook["patch_rva"], 16)
            expected = bytes.fromhex(hook["anchor_hex"])
            with EXE.open("rb") as stream:
                stream.seek(pe.get_offset_from_rva(rva))
                self.assertEqual(stream.read(len(expected)), expected)
            owner = next(e for e in entries
                         if e.struct.BeginAddress <= rva < e.struct.EndAddress)
            self.assertEqual(owner.struct.BeginAddress,
                             int(hook["pdata"]["begin_rva"], 16))
            self.assertEqual(owner.struct.EndAddress,
                             int(hook["pdata"]["end_rva"], 16))
            self.assertEqual(owner.struct.UnwindData,
                             int(hook["pdata"]["unwind_rva"], 16))

    def test_default_off_and_read_only_wiring(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cmake = (BRIDGE / "CMakeLists.txt").read_text(encoding="utf-8")
        bridge = (BRIDGE / "src" / "bridge.cpp").read_text(encoding="utf-8")
        source = (BRIDGE / "src" / "cold_map_vfs_observer_v1.cpp").read_text(
            encoding="utf-8")
        option = contract["observer_contract"]["cmake_option"]
        self.assertIn(option, cmake)
        self.assertRegex(cmake, rf"(?s)option\(\s*{option}.*?\sOFF\s*\)")
        self.assertIn("InstallColdMapVfsObserverV1", bridge)
        self.assertIn('read_only\\":true', bridge)
        self.assertNotIn("SetThreadContext", source)
        self.assertNotIn("TerminateProcess", source)
        self.assertNotIn("Sleep(", source)
        self.assertFalse(contract["observer_contract"]["seventh_guard"])
        self.assertFalse(contract["observer_contract"]["global_callee_patch"])


if __name__ == "__main__":
    unittest.main()
