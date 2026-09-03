from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge" / "research"
SCRIPT = RESEARCH / "extract_g2_truce_preview_entry_observer_seam.py"
FIXTURE = RESEARCH / "g2_truce_preview_entry_observer_seam_v1.json"
EXE = Path(
    os.environ.get(
        "XAR_CK3_EXE",
        r"Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe",
    )
)


def load_extractor():
    spec = importlib.util.spec_from_file_location("g2_truce_preview_entry_seam", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class G2TrucePreviewEntryObserverSeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if not EXE.is_file():
            raise unittest.SkipTest("pinned CK3 executable is not available")
        cls.payload = load_extractor().extract(EXE)

    def test_generated_contract_matches_frozen_fixture(self) -> None:
        self.assertEqual(self.payload, self.fixture)

    def test_exact_post_prolog_seam_and_register_flow(self) -> None:
        function = self.payload["preview_function"]
        seam = self.payload["observer_seam"]
        self.assertEqual(function["pdata"], ["0x2E87140", "0x2E8723B", "0x4DF9914"])
        self.assertEqual(function["unwind_prolog_size"], "0x15")
        self.assertEqual(seam["patch_rva"], "0x2E87155")
        self.assertEqual(seam["continue_rva"], "0x2E87165")
        self.assertEqual(seam["patch_bytes"], 16)
        self.assertTrue(seam["after_unwind_prolog"])
        self.assertEqual(
            [row["mnemonic"] for row in seam["instructions"]],
            ["mov", "mov", "mov", "mov", "cmp"],
        )
        registers = seam["incoming_registers"]
        self.assertIn("effect_this", registers["RCX"])
        self.assertIn("R10", registers["RDX"])
        self.assertIn("R14", registers["R8"])

    def test_shared_function_requires_exact_caddtruce_vtable_filter(self) -> None:
        function = self.payload["preview_function"]
        self.assertEqual(function["shared_pointer_reference_count"], 8)
        self.assertEqual(
            [row["vtable_rva"] for row in self.payload["caddtruce_types"]],
            ["0x4461CA8", "0x4461D70"],
        )
        self.assertIn("accept only exact vtable", self.payload["observer_seam"]["caddtruce_filter"])

    def test_preview_cannot_be_promoted_to_evaluated_days(self) -> None:
        function = self.payload["preview_function"]
        limits = self.payload["evidence_limit"]
        self.assertFalse(function["calls_duration_evaluator"])
        self.assertFalse(function["consumes_duration_at_this_plus_0x108"])
        self.assertFalse(limits["preview_hit_is_evaluated_days"])
        self.assertFalse(limits["can_close_evaluated_days_gap"])
        self.assertFalse(self.payload["boundaries"]["evaluated_days_observable"])

    def test_extractor_and_contract_remain_static_only(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "OpenProcess(",
            "WriteProcessMemory(",
            "CreateRemoteThread(",
            "Start-Process",
            "subprocess",
        ):
            self.assertNotIn(forbidden, source)
        rules = self.payload["observer_rules"]
        self.assertFalse(rules["default_enabled"])
        self.assertTrue(rules["read_only_telemetry"])
        self.assertTrue(rules["no_guard"])
        self.assertTrue(rules["no_branch_or_return_change"])
        self.assertTrue(rules["no_action_or_mutation"])


if __name__ == "__main__":
    unittest.main()
