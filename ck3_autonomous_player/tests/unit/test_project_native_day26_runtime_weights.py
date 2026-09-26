from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "tools/project_native_day26_runtime_weights.py"
ARTIFACT = (PROJECT_ROOT / "src/xar_autoplayer/simulation/data"
            / "ck3_1_19_0_6_episode01_day26_runtime_weights_v1.json")
sys.path.insert(0, str(PROJECT_ROOT / "src"))
spec = importlib.util.spec_from_file_location("day26_runtime_weights_projector", SCRIPT)
assert spec is not None and spec.loader is not None
projector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projector)

from xar_autoplayer.simulation.phase_event_evaluator import execute_phase_event_effect


def captured_fixture(choice: dict) -> tuple[dict, list[dict]]:
    entries = choice["entry_node_identity_tokens"]
    selected = choice["selected_entry_identity_token"]
    row = {
        "effect_node_identity_token": choice["effect_node_identity_token"],
        "side_index": 1,
        "native_event_load_index": 11,
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
        {"node_identity_token": choice["effect_node_identity_token"],
         "parent_node_identity_token": "process-local-parent",
         "node_vtable_rva": 0x44782B0, "call_index": 14,
         "side_index": 1, "native_event_load_index": 11},
        {"node_identity_token": selected,
         "parent_node_identity_token": choice["effect_node_identity_token"],
         "node_vtable_rva": 0x4478388, "call_index": 15,
         "counter_before": choice["child_counter_before"] + 1,
         "counter_after": choice["child_counter_after"]},
    ]
    return row, nodes


class NativeDay26RuntimeWeightsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_original_picker_and_same_frame_model_match(self) -> None:
        artifact = self.artifact
        self.assertEqual(artifact["raw_response_sha256"]["finish"], projector.FINISH_SHA256)
        choice = artifact["native_choice"]
        self.assertEqual(choice["weights_native_int32"], [40, 30, 15])
        self.assertEqual(choice["weights_bytes_hex"], "280000001E0000000F000000")
        self.assertEqual(choice["selection_draw31"], 51510340)
        self.assertEqual(choice["selected_source_order_index"], 0)
        row, nodes = captured_fixture(choice)
        self.assertEqual(projector.validate_weight_record(row, nodes), choice)
        replay = execute_phase_event_effect(
            artifact["same_frame_v3_context"], event_key="knight_killed",
            draws=[artifact["native_selector_draw31"], choice["selection_draw31"]],
        )
        self.assertEqual(replay["draw_tape"]["records"][1]["weights_source_order"],
                         [4_000_000, 3_000_000, 1_500_000])
        self.assertEqual(replay["draw_tape"]["records"][1]["selected_index"], 0)
        growth = [row for row in replay["transition_log"]
                  if row["transition"] == "knight_increase_prowess_chance"]
        self.assertEqual(len(growth), 1)
        self.assertEqual(growth[0]["target_character_id"], 34120)
        self.assertEqual(growth[0]["selected_branch"], "no_op")

    def test_corrupted_weight_bytes_or_child_identity_are_rejected(self) -> None:
        row, nodes = captured_fixture(self.artifact["native_choice"])
        row["weights_bytes_hex"] = "29000000" + row["weights_bytes_hex"][8:]
        with self.assertRaises(AssertionError):
            projector.validate_weight_record(row, nodes)
        row, nodes = captured_fixture(self.artifact["native_choice"])
        nodes[1]["node_identity_token"] = row["entry_node_identity_tokens"][1]
        with self.assertRaises(AssertionError):
            projector.validate_weight_record(row, nodes)


if __name__ == "__main__":
    unittest.main()
