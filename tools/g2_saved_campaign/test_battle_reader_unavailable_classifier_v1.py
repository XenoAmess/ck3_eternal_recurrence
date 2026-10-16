"""Queue and application may use different SDK namespaces."""
from pathlib import Path
import ast
import builtins
import copy
import json
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("battle_reader_unavailable_classifier_v1.py")
FIXTURE = ROOT / "ck3_autonomous_player/tests/fixtures/battle_reader_p18_actual_projection.json"


class SelfContainedBattleClassifier(unittest.TestCase):
    def test_actual_field_projection_under_production_ast_selection(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        selected = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("classify_"):
                selected.append(node)
            elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
                ast.literal_eval(node.value)
                selected.append(node)
        def no_import(*args, **kwargs):
            raise AssertionError("AST-installed battle branch must not import an SDK")
        namespace = {"__builtins__": dict(vars(builtins), __import__=no_import)}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), namespace)
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        dto = fixture["unavailable"]
        source = {k: v for k, v in dto["source_frame"].items() if k not in {"paused", "map_ready"}}
        source.update(schema="xar.ck3.planning-source-frame/v1", status="complete")
        # Service envelope is minimized; DTO retains the actual native packets.
        body = {"status": "executed", "selected_step": dto["step"],
                "plan": {"selected_step": dto["step"]}, "result": dto,
                "planning_source_frame": source}
        classify = namespace["classify_battle_reader_unavailable_v1"]
        observation = classify(body, initial_frame=source, game_pid=source["bridge_pid"])
        self.assertTrue(observation["typed_nonmaterial_observation"])
        self.assertFalse(observation["action_credit"])
        self.assertFalse(observation["date_advance_observed"])
        self.assertFalse(observation["replay_allowed"])
        self.assertEqual(observation["original_readonly_unavailable"], dto)
        bad = copy.deepcopy(body)
        bad["result"]["same_frame_readback"]["native_revision"] += 1
        with self.assertRaises(ValueError):
            classify(bad, initial_frame=source, game_pid=source["bridge_pid"])
        self.assertIsNone(classify({"status": "other"}))


if __name__ == "__main__":
    unittest.main()
