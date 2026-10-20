"""Pure graph regressions plus optional read-only saved-runtime interface replay."""
from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import sys
import types
import unittest
from unittest.mock import patch

import prepare_rich_decision_graph_v1 as g

ROOT = "D:/rich-cold-fixture"
MACHINE = "fixture-machine-001"
SOURCE = Path(__file__).parent


def encoded(value: object) -> bytes:
    return json.dumps(value).encode()


def qualified() -> dict[str, bytes]:
    return {name: (SOURCE / name).read_bytes() for name in g.QUALIFIED}


def fixture() -> tuple[dict[str, bytes], dict[str, bytes], dict[str, object]]:
    roots = {name: b"# unchanged\n" for name in g.CANONICAL}
    roots[g.FEED] = b'''def publish_before_submit(observation):
    actual = observation.get("plan")
    plan = {"selected_step": actual["selected_step"]}
    plan["event_choice_utility"] = {}
    stamp = "clock"
    row = {"request": {}}
    return plan
'''
    roots[g.QUEUE] = b'''def compact_plan(plan):
    return {"prewar_force_admission": None}
def display_projection(row, body):
    # raw response retained
    return {"army_strengths": []}
'''
    while len(roots) < 44:
        roots["fixture_%02d.py" % len(roots)] = b"# unchanged\n"
    external = {g.FEED[:-3]: (len(roots[g.FEED]), hashlib.sha256(roots[g.FEED]).hexdigest())}
    roots[g.OUTER] = ("_C23_EXTERNAL_IMPORT_PINS=" + repr(external) + "\ndef guard():\n    return 'preserved'\n").encode()
    root = PureWindowsPath(ROOT)
    display = {g.FEED: roots[g.FEED], g.MANIFEST: b"pending", g.PROVIDER: b"pending"}
    for name in ("decision_text_view", "decision_text_publisher", "decision_text_admission", "automatic_continuity"):
        display[g.PRESENTATION + name + ".py"] = b"# prior display\n"
    display["presentation-c23/ck3_obs_capture_png_retry_c23.py"] = b"# capture stays exact\n"
    while len(display) < 18:
        display["presentation-c23/fixture_%02d.txt" % len(display)] = b"stable"
    display[g.PROVIDER] = encoded({"schema": "xar.p51.decision-provider-source/v1", "machine_id": MACHINE,
        "sources": {name: g._ref(root, g.PRESENTATION + name + ".py", display[g.PRESENTATION + name + ".py"])
                    for name in ("decision_text_view", "decision_text_publisher", "decision_text_admission", "automatic_continuity")}})
    rows = [{**g._ref(root, name, raw), "relative_path": name} for name, raw in display.items() if name != g.MANIFEST]
    rows.append({"path": "D:/frozen/tools/ck3_capture_closed_receipt.py", "bytes": 8175,
        "sha256": "bf5552199a53bea1909fb8271873740b47b06e04f6856998005296b83b495151",
        "relative_path": "@frozen-host/tools/ck3_capture_closed_receipt.py"})
    display[g.MANIFEST] = encoded({"schema": "xar.display-source-pins-with-frozen-dependency/v1", "machine_id": MACHINE, "files": rows})
    policy: dict[str, object] = {"machine_id": MACHINE, "runtime_import_source_pins": [{"unchanged": True}],
        "entry_source_pins": [[str(root / name), hashlib.sha256(raw).hexdigest()] for name, raw in roots.items()],
        "canonical_entry_source_pins": [[str(root / name), hashlib.sha256(roots[name]).hexdigest()] for name in g.CANONICAL],
        "external_import_source_pins": {name: g._ref(root, name + ".py", roots[name + ".py"]) for name in external}}
    return roots, display, policy


class RichGraphTests(unittest.TestCase):
    def test_counts_closure_identity_and_preserved_capture(self) -> None:
        roots, display, policy = fixture()
        result = g.compose_rich_graph(roots, display, encoded(policy), qualified(), runtime_root=ROOT, machine_id=MACHINE)
        self.assertEqual((len(result.root_sources), len(result.display_sources), len(result.display_refs)), (45, 19, 19))
        self.assertEqual(set(result.changed_root), {g.QUEUE, g.FEED, g.OUTER, g.CONTRACT})
        self.assertEqual(len(result.changed_display), 6)
        self.assertEqual(result.root_sources[g.FEED], result.display_sources[g.FEED])
        self.assertEqual(result.root_sources[g.CONTRACT], result.display_sources[g.PRESENTATION + g.CONTRACT])
        for name, raw in display.items():
            if name not in result.changed_display:
                self.assertEqual(result.display_sources[name], raw)
        after = json.loads(result.policy)
        self.assertEqual(after["runtime_import_source_pins"], policy["runtime_import_source_pins"])
        self.assertEqual(len(after["canonical_entry_source_pins"]), 6)
        self.assertEqual(len(after["external_import_source_pins"]), 2)
        self.assertEqual(len(json.loads(result.display_sources[g.PROVIDER])["sources"]), 5)
        manifest = json.loads(result.display_sources[g.MANIFEST])
        self.assertNotIn(g.MANIFEST, {row["relative_path"] for row in manifest["files"]})
        for row in manifest["files"]:
            if not row["relative_path"].startswith("@"):
                raw = result.display_sources[row["relative_path"]]
                self.assertEqual((row["bytes"], row["sha256"]), (len(raw), hashlib.sha256(raw).hexdigest()))
        before_ast = ast.parse(roots[g.OUTER]).body[1:]
        after_ast = ast.parse(result.root_sources[g.OUTER]).body[1:]
        self.assertEqual([ast.dump(x) for x in before_ast], [ast.dump(x) for x in after_ast])
        review = json.loads(json.dumps(result.review()))
        self.assertEqual(review["display_leaf_count"], 19)
        self.assertEqual({row["relative_path"] for row in review["files"]}, set(result.display_sources))
        self.assertEqual(len(review["manifest_files"]), 19)
        with self.assertRaises(TypeError):
            result.root_sources["bad.py"] = b"bad"

    def test_malformed_input_and_identity_fail_closed(self) -> None:
        for variant in range(9):
            with self.subTest(variant=variant), self.assertRaises((ValueError, SyntaxError)):
                roots, display, policy = fixture()
                q = qualified()
                if variant == 0:
                    policy["machine_id"] = "other-machine"
                elif variant == 1:
                    policy["entry_source_pins"] = []
                elif variant == 2:
                    roots[g.FEED] += b"# mismatch\n"
                elif variant == 3:
                    q[g.CONTRACT] += b"# changed\n"
                elif variant == 4:
                    manifest = json.loads(display[g.MANIFEST])
                    manifest["files"][0]["bytes"] = True
                    display[g.MANIFEST] = encoded(manifest)
                elif variant == 5:
                    manifest = json.loads(display[g.MANIFEST])
                    manifest["files"][-1]["relative_path"] = "@frozen-host/arbitrary.py"
                    display[g.MANIFEST] = encoded(manifest)
                elif variant == 6:
                    provider = json.loads(display[g.PROVIDER])
                    provider["sources"]["decision_text_view"]["path"] = "D:/foreign.py"
                    display[g.PROVIDER] = encoded(provider)
                elif variant == 7:
                    manifest = json.loads(display[g.MANIFEST])
                    manifest["files"][-1]["renamedSha"] = "bad"
                    display[g.MANIFEST] = encoded(manifest)
                else:
                    roots["fixture_07.py"] = roots.pop(next(name for name in roots if name.startswith("fixture_")))
                    roots["../escaped.py"] = b"bad"
                g.compose_rich_graph(roots, display, encoded(policy), q, runtime_root=ROOT, machine_id=MACHINE)

    @unittest.skipUnless(os.environ.get("XAR_RICH_GRAPH_BASELINE"), "read-only real runtime path not supplied")
    def test_complete_saved_queue_feed_and_publisher_interface(self) -> None:
        import decision_text_publisher as pub
        from decision_display_contract_v1 import outcome
        from decision_text_view import AudienceState
        runtime = Path(os.environ["XAR_RICH_GRAPH_BASELINE"]).resolve(strict=True)
        policy = json.loads((runtime / "ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json").read_bytes())
        roots = {Path(path).relative_to(runtime).as_posix(): Path(path).read_bytes() for path, _ in policy["entry_source_pins"]}
        manifest = json.loads((runtime / g.MANIFEST).read_bytes())
        display = {row["relative_path"]: Path(row["path"]).read_bytes() for row in manifest["files"] if not row["relative_path"].startswith("@")}
        display[g.MANIFEST] = (runtime / g.MANIFEST).read_bytes()
        result = g.compose_rich_graph(roots, display, encoded(policy), qualified(),
            runtime_root=str(runtime), machine_id=policy["machine_id"])
        # Execute the actual new outer's external guard with immutable RAM files.
        outer_tree = ast.parse(result.root_sources[g.OUTER])
        guard_nodes = [node for node in outer_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_check_c23_external_imports"
            or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
                and t.id == "_C23_EXTERNAL_IMPORT_PINS" for t in node.targets)]
        guard_ns = {"Path": Path, "hashlib": hashlib, "sys": sys, "require": g._require}
        exec(compile(ast.Module(guard_nodes, type_ignores=[]), "actual-outer-guard", "exec"), guard_ns)
        memory_sources = {runtime / name: raw for name, raw in result.root_sources.items()}
        with patch.dict(sys.modules), patch.object(Path, "resolve", lambda path, strict=False: path), \
                patch.object(Path, "open", lambda path, *a, **k: io.BytesIO(memory_sources[path])):
            for name in result.external_refs:
                sys.modules.pop(name, None)
            guard_ns["_check_c23_external_imports"](runtime, json.loads(result.policy))
            foreign = types.ModuleType(g.CONTRACT[:-3])
            foreign.__file__ = str(SOURCE / g.CONTRACT)
            sys.modules[foreign.__name__] = foreign
            with self.assertRaises(ValueError):
                guard_ns["_check_c23_external_imports"](runtime, json.loads(result.policy))
        fake_canonical = types.ModuleType("root_c23_canonical_outer")
        fake_canonical.receive_entry = lambda *a, **k: {}  # software fixture, no process admission
        fake_cold = types.ModuleType("root_p37c23_cold_resume")
        fake_cold.make_normal_checkpoint_cold_queue_v1 = lambda base, *a, **k: base
        queue_module = types.ModuleType("rich_queue_replay")
        queue_module.__file__ = str(runtime / g.QUEUE)
        queue_ns = queue_module.__dict__
        feed_ns = {"__file__": str(runtime / g.FEED), "__name__": "rich_feed_replay"}
        api = types.ModuleType("root_decision_text_api_c23")
        api.load_api = lambda *a: pub
        api.started_reference = lambda *a: {}
        outputs: dict[str, object] = {}
        context = {"sequence": 143, "tool": "ck3_auto_turn"}
        game = {"pid": 123, "creation_date": "fixture-game"}
        config = {"current_request_path": "held-context", "game": game}
        started = {"configuration": {}, "session": str(runtime)}
        def read_memory(path: object) -> object:
            return context if str(path) == "held-context" else outputs[str(path)]
        def atomic_memory(path: object, value: object, **kwargs: object) -> None:
            outputs[str(path)] = copy.deepcopy(value)
        def pin_memory(path: object) -> dict[str, object]:
            raw = encoded(outputs[str(path)])
            return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        old_path = list(sys.path)
        sys.path.insert(0, str(runtime))
        try:
            with patch.dict(sys.modules, {"root_c23_canonical_outer": fake_canonical, "root_p37c23_cold_resume": fake_cold, "rich_queue_replay": queue_module}):
                exec(compile(result.root_sources[g.QUEUE], str(runtime / g.QUEUE), "exec"), queue_ns)
            exec(compile(result.root_sources[g.FEED], str(runtime / g.FEED), "exec"), feed_ns)
            step = "advance-route-contact-window-v1-234881394-to-2627-days-3-h-2-117440697-285212941"
            variants = ({}, {"war_decision_presentation_v1": []},
                        {"construction_private_query": {"candidate": {"stock_gold_cost_raw": 10**400}}})
            with patch.dict(sys.modules, {"root_decision_text_api_c23": api}), \
                patch.object(Path, "read_text", lambda path, **kw: json.dumps(context if path.name == "CURRENT-REQUEST-P37.json" else game)), \
                patch.object(Path, "open", lambda *a, **k: io.StringIO()), \
                patch.object(Path, "exists", lambda path: str(path) in outputs), \
                patch.object(Path, "unlink", lambda *a, **k: None), \
                patch.object(pub, "validate_started", return_value=started), patch.object(pub, "checked", return_value=config), \
                patch.object(pub, "read", side_effect=read_memory), patch.object(pub, "atomic", side_effect=atomic_memory), \
                patch.object(pub, "pin", side_effect=pin_memory), patch.object(pub, "wait_text_published", return_value={"software_text_ack": True}):
                for index, optional in enumerate(variants):
                    chosen = "private-submit-player-construction-v1" if index == 2 else step
                    actual = {"selected_step": chosen, "phase": "native_war_moving_contact_before_strength_progress",
                              "reason": "original planner reason", **optional}
                    observation = {"selected_step": chosen, "plan": actual, "snapshot_id": "fixture", "revision": index}
                    feed_ns["publish_before_submit"](observation)
                    compact = queue_ns["compact_plan"](actual)
                    projected = queue_ns["display_projection"]({"request": {"tool": "ck3_auto_turn", "sequence": 143}},
                        {"selected_step": chosen, "plan": actual, "result": {"status": "executed"}})
                    self.assertEqual(compact["selected_step"], chosen)
                    self.assertIsInstance(projected, dict)
                    self.assertNotEqual(outcome(projected["result"]["structured_content"]).stage, "verified")
                rows = [row for path, row in outputs.items() if path.endswith(".json")]
                self.assertEqual(len(rows), 3)
                self.assertEqual([row["request"]["callback_index"] for row in rows], [1, 2, 3])
                bad_game = copy.deepcopy(rows[0])
                bad_game["game_pid"] = 999
                with self.assertRaises(ValueError):
                    pub.validate_observation(bad_game, Path(next(iter(outputs))), config)
                view = AudienceState()
                view.consume(rows[0])
                self.assertIn(chr(26368) + chr(22810), view.render())
                with self.assertRaises(ValueError):
                    feed_ns["publish_before_submit"]({"selected_step": "wrong", "plan": {"selected_step": step}})
        finally:
            sys.path[:] = old_path


if __name__ == "__main__":
    unittest.main()
