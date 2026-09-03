from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
BRIDGE = ROOT / "native_bridge"
CONTRACT = (
    BRIDGE
    / "research"
    / "fixtures"
    / "g2_truce_preview_entry_observer_v1_source_contract.json"
)
SEAM = BRIDGE / "research" / "g2_truce_preview_entry_observer_seam_v1.json"
SOURCE = BRIDGE / "src" / "g2_truce_preview_entry_observer_v1.cpp"
HEADER = (
    BRIDGE
    / "include"
    / "xar_bridge"
    / "g2_truce_preview_entry_observer_v1.hpp"
)
WIRING = (
    BRIDGE
    / "research"
    / "g2_truce_preview_entry_observer_v1_wiring.diff"
)
EXE = REPO.parent / "Crusader Kings III" / "binaries" / "ck3.exe"


class G2TrucePreviewEntryObserverV1ContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_build_anchor_pdata_and_function_hash(self) -> None:
        import pefile

        self.assertEqual(
            hashlib.sha256(EXE.read_bytes()).hexdigest().upper(),
            self.contract["exact_build"]["executable_sha256"],
        )
        pe = pefile.PE(str(EXE), fast_load=False)
        hook = self.contract["hook"]
        patch_rva = int(hook["patch_rva"], 16)
        anchor = bytes.fromhex(hook["anchor_hex"])
        with EXE.open("rb") as stream:
            stream.seek(pe.get_offset_from_rva(patch_rva))
            self.assertEqual(stream.read(len(anchor)), anchor)
            function = self.contract["preview_function"]
            begin = int(function["rva"], 16)
            end = int(function["end_rva"], 16)
            stream.seek(pe.get_offset_from_rva(begin))
            function_bytes = stream.read(end - begin)
        self.assertEqual(
            hashlib.sha256(anchor).hexdigest().upper(),
            hook["anchor_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(function_bytes).hexdigest().upper(),
            self.contract["preview_function"]["function_sha256"],
        )
        owner = next(
            entry
            for entry in pe.DIRECTORY_ENTRY_EXCEPTION
            if entry.struct.BeginAddress <= patch_rva < entry.struct.EndAddress
        )
        function = self.contract["preview_function"]
        self.assertEqual(owner.struct.BeginAddress, int(function["rva"], 16))
        self.assertEqual(owner.struct.EndAddress, int(function["end_rva"], 16))
        self.assertEqual(owner.struct.UnwindData, int(function["unwind_rva"], 16))
        self.assertEqual(
            patch_rva - owner.struct.BeginAddress,
            function["unwind_prolog_size"],
        )

    def test_exact_vtable_only_read_only_source(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        combined = source + header
        seam = json.loads(SEAM.read_text(encoding="utf-8"))
        vtables = [int(row["vtable_rva"], 16)
                   for row in self.contract["exact_type_filter"]]
        self.assertEqual(vtables, [0x4461CA8, 0x4461D70])
        self.assertIn("SafeLoadPointer(effect_this)", source)
        self.assertIn("vtable != normal && vtable != forced", source)
        self.assertIn("accepted_count.fetch_add", source)
        self.assertNotIn("0x3373000", combined.lower())
        self.assertNotIn("0x108", combined.lower())
        self.assertNotIn("SetThreadContext", source)
        self.assertNotIn("QueryPerformanceCounter", source)
        self.assertNotIn("GetCurrentThreadId", source)
        self.assertFalse(seam["preview_function"]["calls_duration_evaluator"])
        self.assertFalse(
            seam["preview_function"]["consumes_duration_at_this_plus_0x108"]
        )
        observer = self.contract["observer_contract"]
        self.assertFalse(observer["default_enabled"])
        self.assertTrue(observer["shared_wiring_applied"])
        self.assertFalse(observer["calls_duration_evaluator"])
        self.assertFalse(observer["reads_duration_member"])
        self.assertFalse(observer["action_or_mutation"])
        self.assertFalse(self.contract["readiness"]["evaluated_days_observable"])
        self.assertFalse(self.contract["readiness"]["promotes_evaluated_days"])

    def test_shared_wiring_is_an_unapplied_default_off_snippet(self) -> None:
        wiring = WIRING.read_text(encoding="utf-8")
        option = self.contract["observer_contract"]["proposed_cmake_option"]
        self.assertIn(option, wiring)
        self.assertIn("OFF", wiring)
        self.assertIn("g2_truce_preview_entry_observer_v1.cpp", wiring)
        self.assertIn("InstallG2TrucePreviewEntryObserverV1", wiring)
        self.assertIn('\\"read_only\\":true', wiring)
        self.assertNotIn("0x3373000", wiring.lower())
        self.assertNotIn("0x108", wiring.lower())


if __name__ == "__main__":
    unittest.main()
