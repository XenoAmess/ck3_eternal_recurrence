from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "native_bridge/research/phase2_loader_callback_cfg_v1_abi.json"
SLICE_PATH = (
    ROOT / "native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json"
)


def read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def branch_target(rva: int, raw: bytes) -> tuple[int, int]:
    if len(raw) == 2 and 0x70 <= raw[0] <= 0x7F:
        displacement = struct.unpack("<b", raw[1:2])[0]
    elif len(raw) == 6 and raw[0] == 0x0F and 0x80 <= raw[1] <= 0x8F:
        displacement = struct.unpack("<i", raw[2:6])[0]
    else:
        raise AssertionError(f"unsupported conditional branch bytes: {raw.hex()}")
    fallthrough = rva + len(raw)
    return fallthrough + displacement, fallthrough


class Phase2LoaderCallbackCfgContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = read_object(CFG_PATH)
        cls.static_slice = read_object(SLICE_PATH)

    def test_contract_reuses_the_exact_static_slice_without_public_abi(self) -> None:
        self.assertEqual(self.cfg["contract"], "phase2-loader-callback-cfg-v1")
        self.assertEqual(self.cfg["status"], "static-ready")
        self.assertTrue(self.cfg["read_only"])
        self.assertFalse(self.cfg["production_installed"])
        self.assertFalse(self.cfg["production_abi_changed"])
        source = self.cfg["source"]
        self.assertEqual(
            source["executable_sha256"],
            self.static_slice["build"]["executable_sha256"],
        )
        self.assertEqual(
            source["static_slice_contract"], self.static_slice["contract"]
        )
        self.assertEqual(
            source["static_slice_contract_sha256"],
            hashlib.sha256(SLICE_PATH.read_bytes()).hexdigest().upper(),
        )

    def test_every_conditional_edge_decodes_to_its_declared_target(self) -> None:
        function = self.cfg["function"]
        self.assertEqual(function["rva"], "0x3B9AB00")
        self.assertEqual(function["end_rva_exclusive"], "0x3B9ACED")
        edges = function["branch_edges"]
        self.assertEqual(len(edges), 11)
        self.assertEqual(
            [edge["rva"] for edge in edges],
            [
                "0x3B9AB36",
                "0x3B9AB5B",
                "0x3B9AB87",
                "0x3B9ABAE",
                "0x3B9ABC5",
                "0x3B9AC3E",
                "0x3B9AC4D",
                "0x3B9AC88",
                "0x3B9AC9B",
                "0x3B9ACB0",
                "0x3B9ACBE",
            ],
        )
        for edge in edges:
            target, fallthrough = branch_target(
                int(edge["rva"], 0), bytes.fromhex(edge["bytes_hex"])
            )
            self.assertEqual(target, int(edge["target_rva"], 0))
            self.assertEqual(fallthrough, int(edge["fallthrough_rva"], 0))

    def test_double_read_null_edge_is_explicit_and_conservative(self) -> None:
        callback_null = self.cfg["function"]["null_edges"][0]
        self.assertEqual(callback_null["field"], "node+0x88")
        self.assertEqual(callback_null["initial_check_rva"], "0x3B9AB53")
        self.assertEqual(callback_null["initial_branch_rva"], "0x3B9AB5B")
        self.assertEqual(callback_null["initial_null_target_rva"], "0x3B9AB93")
        self.assertEqual(callback_null["reload_rva"], "0x3B9AB7D")
        self.assertEqual(callback_null["reload_test_rva"], "0x3B9AB84")
        self.assertEqual(callback_null["reload_null_target_rva"], "0x3B9ACE1")
        self.assertEqual(
            callback_null["path_condition"],
            "initial check non-null, then reload reads null",
        )
        self.assertEqual(callback_null["race_or_lifetime_cause"], "unknown")
        self.assertIn(
            "The reload-null edge proves a static path, not a scheduler race or a use-after-free.",
            self.cfg["limits"],
        )

    def test_loop_and_terminal_edges_do_not_promote_error_meaning(self) -> None:
        function = self.cfg["function"]
        self.assertEqual(
            function["loop_edges"],
            [
                {
                    "from_rva": "0x3B9ABC5",
                    "target_rva": "0x3B9ABB0",
                    "condition": "dependency_chain_not_sentinel",
                },
                {
                    "from_rva": "0x3B9ACBE",
                    "target_rva": "0x3B9AB50",
                    "condition": "next_node_exists",
                },
            ],
        )
        self.assertEqual(function["normal_return_rva"], "0x3B9ACE0")
        self.assertEqual(
            function["opaque_error_call_edges"],
            [
                {"from_rva": "0x3B9ACE1", "target_rva": "0x3E22A88"},
                {"from_rva": "0x3B9ACE7", "target_rva": "0x3E34DF0"},
            ],
        )
        self.assertIn(
            "Opaque error-call targets are not assigned a failure meaning without runtime evidence.",
            self.cfg["limits"],
        )


if __name__ == "__main__":
    unittest.main()
