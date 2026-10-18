"""One offline connected test of default-OFF host wiring and the same-client binder."""
import argparse
import ast
import __future__
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

PATHS = ("tools/ck3_mod_acceptance.py",
         "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
OPTIONS = None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execute(nodes, namespace):
    code = compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                   "<actual-shared-source-seam>", "exec", flags=__future__.annotations.compiler_flag)
    exec(code, namespace)


class Connected(unittest.TestCase):
    def test_explicit_host_registration_and_bound_common_owner(self):
        root = Path(OPTIONS.repo).resolve()
        if OPTIONS.candidate_builder:
            _, sources = load(OPTIONS.candidate_builder, "r08_candidate_builder").build_sources(root)
        else:
            sources = {p: (root / p).read_text(encoding="utf-8-sig") for p in PATHS}
        # Execute the actual contiguous host-features branch, not a copied model.
        tree = ast.parse(sources[PATHS[0]])
        features = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "features" for t in n.targets)]
        self.assertEqual(len(features), 1)
        parent = next(n for n in ast.walk(tree) if isinstance(getattr(n, "body", None), list) and features[0] in n.body)
        start = parent.body.index(features[0]); end = start + 1
        while not (isinstance(parent.body[end], ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "budgets" for t in parent.body[end].targets)):
            end += 1
        feature_nodes = parent.body[start:end]
        live = ast.parse(sources[PATHS[1]])
        add = [n for n in ast.walk(live) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
               and n.value.args and isinstance(n.value.args[0], ast.Constant)
               and n.value.args[0].value == "--private-war-cash-queries"]
        # Parser Expr and child append Expr are deliberately disambiguated.
        parser_node = [n for n in add if isinstance(n.value.func, ast.Attribute)
                       and n.value.func.attr == "add_argument"]
        self.assertEqual(len(parser_node), 1)
        driver_node = [n for n in ast.walk(live) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Attribute) and t.attr == "allow_private_war_cash_query"
                               for t in n.targets)]
        child_node = [n for n in ast.walk(live) if isinstance(n, ast.If)
                      and "private_war_cash_queries" in ast.unparse(n.test)]
        self.assertEqual(len(driver_node), 1); self.assertEqual(len(child_node), 1)
        server_tree = ast.parse((root / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py").read_text(encoding="utf-8-sig"))
        cash_gate = [n for n in ast.walk(server_tree) if isinstance(n, ast.If)
                     and "allow_private_war_cash_query" in ast.unparse(n.test)]
        self.assertEqual(len(cash_gate), 1)
        for manifest, expected in (({}, False), ({"war_cash_queries": False}, False),
                                   ({"war_cash_queries": True}, True)):
            ns = {"self": SimpleNamespace(manifest={"host_features": manifest}),
                  "argv": [], "startup": {"mode": "saved_campaign"}}
            execute(feature_nodes, ns)
            self.assertEqual(ns["argv"], ["--private-war-cash-queries"] if expected else [])
            parser = argparse.ArgumentParser(); execute(parser_node, {"result": parser})
            args = parser.parse_args(ns["argv"])
            driver = SimpleNamespace()
            bound = {"args": args, "driver": driver, "child_args": []}
            execute(driver_node + child_node, bound)
            self.assertIs(driver.allow_private_war_cash_query, expected)
            self.assertEqual(bound["child_args"], ns["argv"])
            tools = {}
            def register(**unused):
                def decorate(fn):
                    tools[fn.__name__] = fn
                    return fn
                return decorate
            driver.query_war_cash_current_resources_private_v1 = lambda **kw: kw
            execute(cash_gate, {"driver": driver, "server": SimpleNamespace(tool=register), "read_only_tool": {}})
            self.assertEqual("ck3_query_war_cash_current_resources_private_v1" in tools, expected)
            if expected:
                self.assertEqual(tools["ck3_query_war_cash_current_resources_private_v1"](
                    expected_revision=7, payment_sampling="query"),
                    {"expected_revision": 7, "payment_sampling": "query", "payment_window_contract": None})
        with self.assertRaisesRegex(ValueError, "explicit booleans"):
            execute(feature_nodes, {"self": SimpleNamespace(manifest={"host_features": {"war_cash_queries": 1}}),
                                    "argv": [], "startup": {"mode": "saved_campaign"}})
        adapter = load(OPTIONS.adapter or root / "tools/ck3_mod_acceptance_cases/r08_writer_common_adapter.py", "r08_common_under_test")
        # The real shared adapter_context has no machine_id. Caller supplies the
        # actual existing machine identity, as the production R05 relay does.
        with tempfile.TemporaryDirectory(dir=OPTIONS.scratch_root, prefix="r08-common-") as scratch:
            output = Path(scratch); calls = []; guards = []
            context = {"output": str(output), "repo_root": str(root), "run_dir": str(output / "run")}
            snapshot = {"revision": 7, "native_revision": 6, "date_raw": 53149056,
                        "episode_run_id": "native-synthetic", "played_character": {"character_id": 33388},
                        "diagnostics": {"bridge_pid": 91, "connection_generation": 3}}
            cash = {"current_raw_context_v1": {"synthetic_marker": [1, 2, 3]},
                    "war_payment_observations_v1": {"current_session": {"controlled_window_id": 2},
                    "sampling": {"epoch": 4, "capture_enabled": False}, "controlled_window_admitted": False}}
            def execute_plan(steps, name, timeout=None):
                self.assertEqual(len(steps), 1); step = steps[0]
                self.assertIs(step["fresh_revision"], False); self.assertIs(step["continue_on_error"], True)
                calls.append(step)
                row = {"id": step["id"], "ok": step["tool"] != "synthetic-error",
                       "error": "original RED" if step["tool"] == "synthetic-error" else None,
                       "result": snapshot if step["tool"] == "ck3_take_snapshot" else cash}
                (output / (name + ".actual-results.json")).write_text(json.dumps({"rows": [row]}), encoding="utf-8")
                return [row]
            client = SimpleNamespace(output=output, execute_plan=execute_plan,
                guard=lambda: guards.append("common"), retain_process=lambda: None,
                _process={"pid": 91, "create_time": 1.25}, _handle=object(), _binding=(91, 3, 33388),
                selection=SimpleNamespace(locations={"python": sys.executable}),
                validate_frame=lambda frame, **kw: self.assertEqual(frame, snapshot))
            result = adapter.collect_current_context(context, client, machine="synthetic-machine",
                prefix="r207-cash-inputs", packet_root=output / "views", _created_reader=lambda _: 123456)
            self.assertEqual([c["tool"] for c in calls], ["ck3_take_snapshot", adapter.CASH_TOOL])
            self.assertEqual(calls[1]["args"], {"expected_revision": 7, "payment_sampling": "query"})
            self.assertEqual(result["expected"]["created"], 123456)
            self.assertIs(result["actual_payment_capture_enabled"], False)
            self.assertEqual(result["sampling_actions"], 0); self.assertFalse(result["observer_started"])
            view = adapter.read_pin(result["cash_response"])
            self.assertEqual(view["body"], cash); self.assertEqual(view["common_original"]["pointer"], "/rows/0/result")
            original = adapter.read_pin({k: v for k, v in view["common_original"].items() if k != "pointer"})
            self.assertEqual(original["rows"][0]["result"], cash)
            legacy = SimpleNamespace()
            adapter.bind_legacy_driver(legacy, context, client, machine="synthetic-machine", _created_reader=lambda _: 123456)
            with self.assertRaisesRegex(ValueError, "independent 45s"):
                legacy.RootRuntime({})
            authorized = []
            adapter.bind_legacy_driver(legacy, context, client, machine="synthetic-machine",
                root_window_guard=lambda c, owner, cfg: authorized.append(owner), _created_reader=lambda _: 123456)
            cfg = {"schema": "xar.e04.common-cd-writer-driver-input.v1", "request_prefix": "r207-observe-one",
                   "control_root": str(output / "control"), "common_packet_root": str(output / "runtime-views"),
                   "watch": {"expected": result["expected"], "repo": str(root), "python": sys.executable}}
            cfgpin = adapter.write_new(output / "config.json", cfg)
            self.assertEqual(legacy.load_config(cfgpin), cfg)
            rt = legacy.RootRuntime(cfg)
            body, _ = rt.request("r207-bound-cash", adapter.CASH_TOOL, {"expected_revision": 7, "payment_sampling": "query"})
            self.assertEqual(body, cash); self.assertTrue(all(owner is client for owner in authorized))
            relay = adapter.CommonPackets(context, client, output / "errors", machine="synthetic-machine")
            with self.assertRaisesRegex(ValueError, "never replay"):
                relay.request("r207-error", "synthetic-error", {})
            failed = json.loads((output / "errors/r207-error.common-view.json").read_bytes())
            self.assertTrue(failed["is_error"])
            count = len(calls)
            with self.assertRaisesRegex(ValueError, "never replay"):
                relay.request("r207-error", "synthetic-error", {})
            self.assertEqual(len(calls), count)
        print("PASS_R08_SHARED_CASH_OPTIN_AND_SAME_OWNER_BINDER_OFFLINE; no SDK/observer/host/native execution")


def main():
    global OPTIONS
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--candidate-builder", type=Path)
    p.add_argument("--adapter", type=Path)
    p.add_argument("--scratch-root", type=Path)
    OPTIONS = p.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Connected)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
