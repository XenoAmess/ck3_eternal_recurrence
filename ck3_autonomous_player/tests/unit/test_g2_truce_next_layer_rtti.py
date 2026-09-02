from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
RESEARCH = ROOT / "native_bridge" / "research"
SCRIPT = RESEARCH / "extract_g2_truce_next_layer_rtti.py"
CONTRACT = (
    RESEARCH / "fixtures" / "g2_truce_next_layer_rtti_v1_contract.json"
)
EXE = Path(
    os.environ.get(
        "XAR_CK3_EXE",
        r"Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe",
    )
)


def load_extractor():
    spec = importlib.util.spec_from_file_location(
        "extract_g2_truce_next_layer_rtti", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class G2TruceNextLayerRttiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not EXE.is_file():
            raise unittest.SkipTest("pinned CK3 executable is not available")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.payload = load_extractor().extract(EXE)

    def test_exact_build_and_target_identity(self) -> None:
        self.assertEqual(self.payload["result"], "GREEN")
        self.assertTrue(self.payload["read_only"])
        self.assertFalse(self.payload["ck3_started"])
        self.assertEqual(
            self.payload["exact_build"]["sha256"],
            self.contract["exact_build"]["sha256"],
        )
        expected = self.contract["target_type"]
        actual = self.payload["target_truce_effect"]
        self.assertEqual(actual["vtable_rva"], expected["vtable_rva"])
        self.assertEqual(
            actual["complete_object_locator"]["rva"], expected["col_rva"]
        )
        self.assertEqual(
            actual["type_descriptor_rva"], expected["type_descriptor_rva"]
        )
        self.assertEqual(actual["rtti_type_name"], expected["rtti_type_name"])
        self.assertEqual(actual["object_size"], expected["object_size"])

    def test_all_five_observed_vtables_bind_expected_rtti(self) -> None:
        actual_by_vtable = {
            row["vtable_rva"]: row
            for row in self.payload["observed_next_layer_candidates"]
        }
        self.assertEqual(set(actual_by_vtable), set(self.contract["candidate_types"]))
        for vtable, expected in self.contract["candidate_types"].items():
            actual = actual_by_vtable[vtable]
            self.assertEqual(
                actual["complete_object_locator"]["rva"], expected["col_rva"]
            )
            self.assertEqual(
                actual["type_descriptor_rva"], expected["type_descriptor_rva"]
            )
            self.assertEqual(actual["rtti_type_name"], expected["rtti_type_name"])
            self.assertEqual(actual["object_size"], expected["object_size"])
            self.assertEqual(
                actual["multiple_target_effect_base"],
                expected["multiple_target_effect_base"],
            )
            self.assertTrue(actual["primary_vtable"])
            self.assertEqual(actual["complete_object_locator"]["signature"], 1)

    def test_bounded_container_classification_and_cif_owned_pointer(self) -> None:
        expected = self.contract["bounded_path_classification"]
        actual = self.payload["bounded_path_classification"]
        self.assertEqual(
            actual["remaining_multiple_target_positions"],
            expected["remaining_multiple_target_positions"],
        )
        self.assertEqual(
            actual["excluded_from_common_multiple_target_walk"],
            expected["excluded_from_common_multiple_target_walk"],
        )
        self.assertFalse(actual["unique_path_identified"])

        cif_expected = self.contract["cif_optional_effect_storage"]
        cif_actual = self.payload["cif_optional_effect_storage"]
        for key in ("field_offset", "destructor_span_rva", "destructor_span_hex"):
            self.assertEqual(cif_actual[key], cif_expected[key])

    def test_extractor_has_no_process_or_mutation_surface(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "subprocess",
            "Start-Process",
            "OpenProcess",
            "WriteProcessMemory",
            "CreateRemoteThread",
            "surrender",
            "white_peace",
            "enforce_demands",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            self.payload["boundaries"],
            {
                "public_abi_changed": False,
                "readiness_changed": False,
                "production_shape_contract_changed": False,
                "mutation_sent": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
