import json
import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
RESEARCH = NATIVE / "research"


class Phase2WrapperConsumerEdgeObserverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.abi = json.loads(
            (RESEARCH / "phase2_wrapper_consumer_edge_observer_v1_abi.json")
            .read_text(encoding="utf-8")
        )
        cls.schema = json.loads(
            (RESEARCH / "phase2_wrapper_consumer_edge_observer_v1_report.schema.json")
            .read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (RESEARCH / "fixtures/phase2_wrapper_consumer_edge_observer_v1_source_contract.json")
            .read_text(encoding="utf-8")
        )
        cls.header = (NATIVE / "include/xar_bridge/phase2_wrapper_consumer_edge_observer_v1.hpp").read_text(encoding="utf-8")
        cls.source = (NATIVE / "src/phase2_wrapper_consumer_edge_observer_v1.cpp").read_text(encoding="utf-8")
        cls.fixture = (NATIVE / "src/phase2_wrapper_consumer_edge_observer_v1_test.cpp").read_text(encoding="utf-8")
        cls.bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
        cls.cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")

    def test_exact_seams_are_frozen(self):
        consumer = self.abi["exact_seams"]["consumer_entry"]
        self.assertEqual(consumer["function_rva"], "0x3B9DD50")
        self.assertEqual(consumer["patch_bytes"], 16)
        self.assertEqual(
            consumer["anchor_hex"], "4055565741544155415641574883EC60"
        )
        self.assertEqual(consumer["continue_rva"], "0x3B9DD60")
        self.assertEqual(
            [edge["call_rva"] for edge in self.abi["exact_seams"]["wrapper_call_edges"]],
            ["0x3B9E10B", "0x3B9E175"],
        )
        self.assertEqual(
            self.abi["exact_seams"]["consumer_identity"]["patch_rva"],
            "0x3B9DEA7",
        )

    def test_source_contract_tokens(self):
        for token in self.contract["required_header_tokens"]:
            self.assertIn(token, self.header)
        for token in self.contract["required_implementation_tokens"]:
            self.assertIn(token, self.source)
        for token in self.contract["required_bridge_tokens"]:
            self.assertIn(token, self.bridge)
        for token in self.contract["required_cmake_tokens"]:
            self.assertIn(token, self.cmake)

    def test_source_hashes_bind_the_native_observer(self):
        paths = {
            "consumer_edge_header_sha256": NATIVE / "include/xar_bridge/phase2_wrapper_consumer_edge_observer_v1.hpp",
            "consumer_edge_implementation_sha256": NATIVE / "src/phase2_wrapper_consumer_edge_observer_v1.cpp",
            "consumer_edge_fixture_sha256": NATIVE / "src/phase2_wrapper_consumer_edge_observer_v1_test.cpp",
            "wrapper_entry_header_sha256": NATIVE / "include/xar_bridge/phase2_wrapper_entry_observer_v1.hpp",
            "wrapper_entry_implementation_sha256": NATIVE / "src/phase2_wrapper_entry_observer_v1.cpp",
            "wrapper_entry_fixture_sha256": NATIVE / "src/phase2_wrapper_entry_observer_v1_test.cpp",
        }
        for key, path in paths.items():
            actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            self.assertEqual(actual, self.abi["source_hashes"][key])

    def test_private_option_is_default_off_and_composes_existing_context(self):
        self.assertEqual(
            self.abi["scope"]["private_build_option"],
            "XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1",
        )
        option = "option(\n  XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1"
        start = self.cmake.index(option)
        self.assertIn("\n  OFF\n)", self.cmake[start : start + 240])
        for implied in (
            "XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1=1",
            "XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1=1",
            "XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1",
            "XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1",
        ):
            self.assertIn(implied, self.cmake)

    def test_heartbeat_schema_matches_abi(self):
        required = self.abi["heartbeat"]["required_fields"]
        self.assertEqual(self.schema["required"], required)
        self.assertEqual(set(self.schema["properties"]), set(required))
        for field in required:
            if field == "private_build":
                continue
            self.assertIn(field, self.bridge)

    def test_decision_matrix_distinguishes_all_four_post_publish_outcomes(self):
        matrix = self.abi["decision_matrix"]
        self.assertEqual(
            set(matrix),
            {
                "selected_zero",
                "selected_nonzero_wrapper_post_publish_zero",
                "wrapper_post_publish_nonzero_consumer_edges_zero",
                "consumer_edge_nonzero_identity_match_zero",
                "consumer_identity_match_nonzero",
            },
        )
        self.assertIn("selected_after_publish_edge_0x3B9E10B_count", self.fixture)
        self.assertIn("selected_after_publish_edge_0x3B9E175_count", self.fixture)
        self.assertIn("selected_after_publish_other_caller_count", self.fixture)

    def test_public_readiness_is_unchanged(self):
        self.assertFalse(self.abi["scope"]["public_abi_changed"])
        self.assertFalse(self.abi["scope"]["readiness_changed"])
        self.assertIn("RED", self.abi["readiness"])


if __name__ == "__main__":
    unittest.main()
