from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge" / "research"
SCRIPT = RESEARCH / "extract_g2_truce_residual_rtti.py"
CONTRACT = RESEARCH / "fixtures" / "g2_truce_residual_rtti_v1_contract.json"
EXE = Path(os.environ.get("XAR_CK3_EXE", r"Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe"))
GAME = Path(os.environ.get("XAR_CK3_GAME", r"Z:\ck3_mod_rewrite\Crusader Kings III\game"))


def load_extractor():
    spec = importlib.util.spec_from_file_location("extract_g2_truce_residual_rtti", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class G2TruceResidualRttiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not EXE.is_file() or not GAME.is_dir():
            raise unittest.SkipTest("pinned CK3 build is not available")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.payload = load_extractor().extract(EXE, GAME)

    def test_exact_rtti_and_container_offsets(self) -> None:
        self.assertEqual(self.payload["result"], "GREEN")
        self.assertEqual(self.payload["exact_build"]["sha256"], self.contract["exact_build"]["sha256"])
        actual = {row["vtable_rva"]: row for row in self.payload["residual_types"]}
        for vtable, expected in self.contract["residual_types"].items():
            row = actual[vtable]
            self.assertEqual(row["complete_object_locator"]["rva"], expected["col_rva"])
            self.assertEqual(row["type_descriptor_rva"], expected["type_descriptor_rva"])
            self.assertEqual(row["rtti_type_name"], expected["rtti_type_name"])
            self.assertEqual(row["object_size"], expected["object_size"])
            self.assertEqual(row["common_effect_vector"]["pointer_offset"], expected["common_pointer_offset"])
            self.assertEqual(row["common_effect_vector"]["count_offset"], expected["common_count_offset"])
            self.assertEqual(row["common_effect_vector"]["walk_rva"], expected["common_walk_rva"])
        context = actual["0x44D27B8"]["separate_scope_storage"]
        self.assertEqual(context["pointer_offset"], "0x60")
        self.assertEqual(context["count_offset"], "0x6C")
        self.assertIn("distinct", context["classification"])

    def test_stock_source_order_uniquely_returns_to_index7(self) -> None:
        rows = self.payload["raiktor_on_defeat_top_level"]
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[7]["key"], "add_truce_attacker_defeat_effect")
        self.assertEqual(rows[9]["key"], "on_lost_aggression_war_discontent_loss")
        self.assertEqual(rows[10]["key"], "laamp_as_mercenary_payout_tooltip_effect")
        self.assertEqual(self.payload["correlation"]["unique_truce_scripted_effect_index"], self.contract["unique_truce_scripted_effect_index"])
        self.assertEqual(self.payload["correlation"]["unique_next_read_only_path"], self.contract["unique_next_read_only_path"])
        self.assertFalse(self.payload["correlation"]["residual_index10_branch_is_truce"])

    def test_scripted_shapes_match_live_counts(self) -> None:
        shapes = self.payload["scripted_effect_top_level_shapes"]
        self.assertEqual(len(shapes["add_truce_attacker_defeat_effect"]), 4)
        self.assertEqual(len(shapes["on_lost_aggression_war_discontent_loss"]), 1)
        self.assertEqual(len(shapes["laamp_as_mercenary_payout_tooltip_effect"]), 1)
        self.assertEqual(len(shapes["mandala_war_defeat_effects"]), 2)

    def test_cif_null_scope_and_read_only_boundaries(self) -> None:
        closure = self.payload["cif_0x258_closure"]
        self.assertEqual(closure["captured_parent_objects_null"], 3)
        self.assertFalse(closure["recursive_child_object_sampled"])
        self.assertEqual(self.payload["boundaries"], {
            "public_abi_changed": False,
            "readiness_changed": False,
            "production_shape_contract_changed": False,
            "mutation_sent": False,
            "next_path_requires_live_validation": True,
        })
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "Start-Process", "OpenProcess", "WriteProcessMemory", "CreateRemoteThread"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
