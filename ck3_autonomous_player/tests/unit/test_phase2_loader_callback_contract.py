from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
ABI_PATH = ROOT / "native_bridge/research/phase2_loader_callback_v1_abi.json"
FIXTURE_PATH = (
    ROOT
    / "native_bridge/research/fixtures/phase2_loader_callback_v1_source_contract.json"
)
ANCHORS_PATH = ROOT / "native_bridge/research/ck3_1_19_0_6_anchors.json"
sys.path.insert(0, str(REPO / "tools"))
import zg361_phase2_loader_stage as loader  # noqa: E402


def read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


class Phase2LoaderCallbackContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = read_object(ABI_PATH)
        cls.fixture = read_object(FIXTURE_PATH)
        cls.anchors = read_object(ANCHORS_PATH)

    def test_contract_is_bound_to_the_pinned_exact_build(self) -> None:
        self.assertEqual(self.abi["contract"], "phase2-loader-callback-v1")
        self.assertEqual(self.abi["status"], "static-ready")
        self.assertTrue(self.abi["read_only"])
        self.assertFalse(self.abi["production_installed"])
        self.assertEqual(
            self.abi["build"],
            {
                "product_version": self.anchors["build"]["product_version"],
                "executable_sha256": self.anchors["build"]["sha256"],
                "architecture": "msvc-x64",
            },
        )

    def test_loop_and_node_layout_are_machine_readable(self) -> None:
        loop = self.abi["loader_node_init_loop"]
        self.assertEqual(loop["function_rva"], "0x3B9AB00")
        self.assertEqual(loop["function_end_rva_exclusive"], "0x3B9ACED")
        self.assertEqual(loop["current_node_rva"], "0x3B9AB50")
        self.assertEqual(loop["node_gate_rva"], "0x3B9AB53")
        self.assertEqual(loop["callback_call_rva"], "0x3B9AB90")
        callback = loop["callback"]
        self.assertEqual(callback["kind"], "indirect_virtual_call")
        self.assertEqual(callback["receiver_register"], "rax")
        self.assertEqual(callback["vtable_slot_offset"], "0x10")
        self.assertEqual(callback["return_semantics"], "unknown")
        self.assertEqual(
            loop["node_layout"],
            {
                "initialized_gate_offset": "0x88",
                "init_time_offset": "0x98",
                "dependency_chain_offset": "0xB8",
            },
        )
        self.assertEqual(
            loop["format_strings"],
            {
                "database_node_init_time_rva": "0x4558670",
                "post_init_rva": "0x4558648",
            },
        )

    def test_contract_refuses_source_filename_and_authorization_claims(self) -> None:
        source = self.abi["source_attribution"]
        self.assertEqual(source["status"], "unknown")
        self.assertIsNone(source["script_filename"])
        self.assertFalse(source["allow_filename_inference"])
        boundary = self.abi["telemetry_boundary"]
        self.assertEqual(boundary["authorization_effect"], "none")
        self.assertFalse(boundary["state_write"])
        self.assertFalse(boundary["detour"])
        self.assertIn("database loader readiness", self.abi["unsupported_claims"])
        self.assertIn("vtable owner/type identity", self.abi["unsupported_claims"])

    def test_synthetic_records_join_existing_read_only_loader_parser(self) -> None:
        records = self.fixture["records"]
        self.assertEqual(len(records), 2)
        self.assertEqual(
            [record["sequence"] for record in records],
            [1, 2],
        )
        self.assertTrue(
            all(record["native_log_source_line"] == "database_dependencies.cpp:433"
                for record in records)
        )
        debug_log = "".join(
            "[{timestamp}][D][{source}]: Database Node Init Time: {node} - "
            "{init_ms} ms - {inclusive_ms} ms including dependencies\n".format(
                timestamp=record["timestamp"],
                source=record["native_log_source_line"],
                node=record["node"],
                init_ms=record["init_ms"],
                inclusive_ms=record["inclusive_ms"],
            )
            for record in records
        ).encode("utf-8")
        observed = loader.inspect_loader_logs(debug_log, b"")
        self.assertEqual(
            observed["database_node_count"],
            self.fixture["expected_observation"]["database_node_count"],
        )
        self.assertEqual(
            observed["last_database_node"],
            self.fixture["expected_observation"]["last_database_node"],
        )
        self.assertEqual(
            observed["stage"], self.fixture["expected_observation"]["stage"]
        )
        self.assertFalse(observed["event_wait_authorized"])
        self.assertEqual(
            observed["database_nodes"],
            [
                {
                    "timestamp": record["timestamp"],
                    "source_line": record["native_log_source_line"],
                    "node": record["node"],
                    "init_ms": record["init_ms"],
                    "inclusive_ms": record["inclusive_ms"],
                }
                for record in records
            ],
        )


if __name__ == "__main__":
    unittest.main()
