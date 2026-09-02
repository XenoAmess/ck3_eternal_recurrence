from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
RESEARCH = NATIVE / "research"
GENERATOR_PATH = RESEARCH / "make_phase2_producer_identity_observer_manifest.py"
SPEC = importlib.util.spec_from_file_location("producer_manifest", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class Phase2ProducerIdentityObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = json.loads((RESEARCH / "phase2_producer_identity_observer_v1_abi.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((RESEARCH / "fixtures/phase2_producer_identity_observer_v1_source_contract.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((RESEARCH / "phase2_producer_identity_observer_v1_report.schema.json").read_text(encoding="utf-8"))
        cls.header = (NATIVE / "include/xar_bridge/phase2_producer_identity_observer_v1.hpp").read_text(encoding="utf-8")
        cls.source = (NATIVE / "src/phase2_producer_identity_observer_v1.cpp").read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_default_private_boundary_and_exact_anchor(self) -> None:
        self.assertFalse(self.abi["scope"]["installed_by_default"])
        self.assertFalse(self.abi["scope"]["public_abi_changed"])
        self.assertFalse(self.abi["scope"]["readiness_changed"])
        seam = self.abi["exact_seam"]
        self.assertEqual(seam["physical_patch_bytes"], 16)
        self.assertEqual(seam["physical_anchor_sha256"], "9A7AE24D86BC3453A89A92E6B948EE54A6DA043029CCF76E2B3D1443BD1BBE1E")
        self.assertEqual([row["rva"] for row in seam["logical_hooks"]], ["0x3B9CFD2", "0x3B9CFD7"])

    def test_source_contract_tokens_and_report_schema(self) -> None:
        for token in self.fixture["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.fixture["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.fixture["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.fixture["required_cmake_tokens"]:
            self.assertIn(token, self.cmake)
        self.assertEqual(set(self.fixture["required_report_fields"]), set(self.schema["required"]) - {"private_build"})

    def test_manifest_is_accepted_by_wiring_shape(self) -> None:
        manifest = GENERATOR.create_manifest(ROOT.parent, "a" * 40, "b" * 64, "c" * 64)
        self.assertEqual(manifest["kind"], "zg361_phase2_native_observer_seam")
        self.assertFalse(manifest["launch"]["performed"])
        self.assertEqual(manifest["build"]["private_option"], "XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1")
        self.assertEqual(set(manifest["report_contract"]["required_fields"]), set(self.fixture["required_report_fields"]))


if __name__ == "__main__":
    unittest.main()
