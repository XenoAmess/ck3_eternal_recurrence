from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge" / "research"
SCRIPT = RESEARCH / "extract_g2_truce_callsite_activation.py"
FIXTURE = RESEARCH / "g2_truce_callsite_activation_v1.json"
EXE = Path(
    os.environ.get(
        "XAR_CK3_EXE",
        r"Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe",
    )
)


def load_extractor():
    spec = importlib.util.spec_from_file_location("g2_truce_callsite_activation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class G2TruceCallsiteActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if not EXE.is_file():
            raise unittest.SkipTest("pinned CK3 executable is not available")
        cls.payload = load_extractor().extract(EXE)

    def test_exact_specializations_and_virtual_slots(self) -> None:
        self.assertEqual(self.payload["result"], "STATIC_ACTIVATION_BOUNDARY_IDENTIFIED")
        expected = self.fixture["specializations"]
        actual = self.payload["specializations"]
        self.assertEqual(len(actual), 2)
        for row, frozen in zip(actual, expected, strict=True):
            for key in (
                "template_parameter",
                "vtable_rva",
                "rtti_type_name",
                "execute_slot",
                "execute_rva",
                "execute_pdata",
                "execute_sha256",
                "preview_slot",
                "preview_rva",
                "evaluator_call_rva",
            ):
                self.assertEqual(row[key], frozen[key])
            self.assertEqual(row["activation_predicate"]["span"], frozen["predicate_span"])
            self.assertEqual(row["activation_predicate"]["sha256"], frozen["predicate_sha256"])
            self.assertEqual(
                row["activation_predicate"]["taken_target_rva"],
                frozen["predicate_taken_target"],
            )

    def test_loaded_path_can_only_reach_specialization_zero(self) -> None:
        current = self.payload["current_loaded_path"]
        frozen = self.fixture["current_loaded_path"]
        self.assertEqual(current["observed_vtable_rva"], frozen["observed_vtable_rva"])
        self.assertEqual(current["observed_specialization"], 0)
        self.assertEqual(current["applicable_evaluator_call_rva"], frozen["only_applicable_callsite"])
        self.assertFalse(current["second_callsite_structurally_applicable"])

    def test_cfg_predicate_and_no_hit_diagnosis(self) -> None:
        for row in self.payload["specializations"]:
            instructions = row["activation_predicate"]["instructions"]
            self.assertEqual([item["mnemonic"] for item in instructions], ["mov", "mov", "cmp", "jne"])
            self.assertEqual(
                row["activation_predicate"]["semantic"],
                "resolved source CharacterID != resolved target CharacterID",
            )
        activation = self.payload["activation_conclusion"]
        self.assertTrue(activation["frozen_state_character_ids_differ"])
        self.assertFalse(activation["termination_or_context_effect_submitted"])
        self.assertIn("never dispatched", activation["why_no_hit"])

    def test_preview_is_distinct_but_not_duration_evidence(self) -> None:
        preview = self.payload["preview"]
        next_seam = self.payload["next_distinct_read_only_seam"]
        self.assertEqual(preview["shared_rva"], "0x2E87140")
        self.assertFalse(preview["calls_duration_evaluator"])
        self.assertEqual(next_seam["preferred_rva"], preview["shared_rva"])
        self.assertIn("cannot produce evaluated_days", next_seam["limitation"])

    def test_extractor_is_static_and_readiness_stays_false(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("OpenProcess(", "WriteProcessMemory(", "CreateRemoteThread(", "Start-Process"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(self.payload["boundaries"], self.fixture["boundaries"])


if __name__ == "__main__":
    unittest.main()
