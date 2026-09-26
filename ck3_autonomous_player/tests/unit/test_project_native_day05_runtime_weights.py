from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "tools/project_native_day05_runtime_weights.py"
ARTIFACT = (
    PROJECT_ROOT
    / "src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_day05_runtime_weights_v1.json"
)
sys.path.insert(0, str(PROJECT_ROOT / "src"))
spec = importlib.util.spec_from_file_location("day05_runtime_weights_projector", SCRIPT)
assert spec is not None and spec.loader is not None
projector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projector)


def _captured_row(choice: dict) -> tuple[dict, list[dict]]:
    entries = choice["entry_node_identity_tokens"]
    selected = choice["selected_entry_identity_token"]
    row = {
        "effect_node_identity_token": choice["effect_node_identity_token"],
        "side_index": choice["side_index"],
        "native_event_load_index": choice["native_event_load_index"],
        "weights": choice["weights_native_int32"],
        "weights_bytes_hex": choice["weights_bytes_hex"],
        "entry_count": len(entries),
        "entry_node_identity_tokens": entries,
        "selected_entry_identity_tokens": [selected],
        "pick_count": 1,
        "child_counter_before": choice["child_counter_before"],
        "child_salt_before": 0,
        "child_counter_after": choice["child_counter_after"],
        "child_salt_after": 0,
    }
    nodes = [
        {
            "node_identity_token": choice["effect_node_identity_token"],
            "parent_node_identity_token": "process-local-parent",
            "node_vtable_rva": 0x44782B0,
            "call_index": choice["call_index"],
            "side_index": 1,
            "native_event_load_index": 10,
        },
        {
            "node_identity_token": selected,
            "parent_node_identity_token": choice["effect_node_identity_token"],
            "node_vtable_rva": 0x4478388,
            "counter_before": choice["child_counter_before"] + 1,
            "counter_after": choice["child_counter_after"],
        },
    ]
    return row, nodes


class NativeDay05RuntimeWeightsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_three_native_vectors_bind_draw_and_executed_child(self) -> None:
        choices = self.artifact["choices"]
        self.assertEqual(
            [(c["call_index"], c["weights_native_int32"], c["selected_source_order_index"])
             for c in choices],
            [(8, [54, 30, 10], 0), (15, [4, 2, 4, 4], 0), (49, [40, 50], 1)],
        )
        for choice in choices:
            with self.subTest(call=choice["call_index"]):
                row, nodes = _captured_row(choice)
                result = projector.validate_weight_record(row, nodes)
                self.assertEqual(result["selection_draw31"], choice["selection_draw31"])
                self.assertEqual(result["threshold"], choice["threshold"])
                self.assertEqual(result["selected_source_order_index"],
                                 choice["selected_source_order_index"])

    def test_changed_raw_weight_bytes_are_rejected(self) -> None:
        row, nodes = _captured_row(self.artifact["choices"][0])
        row["weights_bytes_hex"] = "00000000" + row["weights_bytes_hex"][8:]
        with self.assertRaises(AssertionError):
            projector.validate_weight_record(row, nodes)

    def test_child_identity_mismatch_is_rejected(self) -> None:
        row, nodes = _captured_row(self.artifact["choices"][2])
        nodes[1]["node_identity_token"] = row["entry_node_identity_tokens"][0]
        with self.assertRaises(AssertionError):
            projector.validate_weight_record(row, nodes)


if __name__ == "__main__":
    unittest.main()
