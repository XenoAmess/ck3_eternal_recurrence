from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge" / "research"
SCRIPT = RESEARCH / "extract_g2_truce_context_lifetime_v2.py"
FIXTURE = RESEARCH / "g2_truce_context_lifetime_v2.json"
LIVE_RED = (
    ROOT.parent
    / "artifacts"
    / "g2"
    / "2026-09-04"
    / "evaluated-days-current-pin-live-r1-red.json"
)
EXE = Path(
    os.environ.get(
        "XAR_CK3_EXE",
        r"Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe",
    )
)


def load_extractor():
    spec = importlib.util.spec_from_file_location(
        "g2_truce_context_lifetime_v2", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class G2TruceContextLifetimeV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if not EXE.is_file():
            raise unittest.SkipTest("pinned CK3 executable is not available")
        cls.payload = load_extractor().extract(EXE, LIVE_RED)

    def test_generated_contract_matches_frozen_fixture(self) -> None:
        self.assertEqual(self.payload, self.fixture)

    def test_root_and_leaf_contexts_are_not_interchangeable(self) -> None:
        diagnosis = self.payload["diagnosis"]
        self.assertFalse(diagnosis["raw_war_effect_context_is_valid_leaf_context"])
        self.assertFalse(diagnosis["root_preview_wrapper_is_valid_caddtruce_leaf_context"])
        self.assertFalse(diagnosis["root_slot58_proxy_can_supply_leaf_context"])
        self.assertTrue(diagnosis["rdx_and_r8_must_share_one_leaf_wrapper"])
        self.assertEqual(
            diagnosis["root_cause"],
            "direct bridge call bypassed native leaf-context construction",
        )

    def test_execute_and_preview_leaf_lifetimes_are_exact(self) -> None:
        execute = self.payload["execute_context_chain"]
        preview = self.payload["preview_context_chain"]
        self.assertEqual(execute["virtual_call"], "0x3380CFB call [vtable+0xB0]")
        self.assertEqual(preview["virtual_call"], "0x3380947 call [vtable+0xB8]")
        self.assertIn("R15", execute["normal_receiver"])
        self.assertIn("R12", execute["forced_receiver"])
        self.assertIn("synchronous", execute["lifetime"])
        self.assertIn("synchronous", preview["lifetime"])

    def test_candidate_is_private_default_off_and_never_clones_wrapper(self) -> None:
        candidate = self.payload["candidate_boundary"]
        self.assertEqual(
            candidate["supported_seam"],
            "synchronous CAddTruce preview entry 0x2E87155",
        )
        self.assertFalse(candidate["wrapper_clone_allowed"])
        self.assertFalse(candidate["root_wrapper_substitution_allowed"])
        self.assertFalse(candidate["default_enabled"])
        self.assertTrue(candidate["private_only"])
        self.assertFalse(candidate["live_validated"])

    def test_extractor_is_static_only(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "OpenProcess(",
            "WriteProcessMemory(",
            "CreateRemoteThread(",
            "Start-Process",
            "subprocess",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(self.payload["boundaries"]["ck3_started"])
        self.assertFalse(self.payload["boundaries"]["process_attached"])
        self.assertFalse(self.payload["boundaries"]["gen034_closed"])


if __name__ == "__main__":
    unittest.main()
