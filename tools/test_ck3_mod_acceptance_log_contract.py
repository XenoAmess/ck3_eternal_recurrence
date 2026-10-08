"""Portable case producer -> actual public declaration -> actual log provider.

Only temporary synthetic log files are read. No CK3, server, native query or
runtime host is started. Function projections preserve the real source bodies.
"""
from pathlib import Path
import ast
import __future__
import copy
import hashlib
import inspect
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOG_TOOL = "ck3_query_engine_log_literals_v1"
MCP = "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
DIAGNOSTICS = "ck3_autonomous_player/src/xar_autoplayer/ck3_runtime_diagnostics.py"


def source_tree(relative):
    path = ROOT / relative
    return path, ast.parse(path.read_text(encoding="utf-8-sig"))


def actual_function(relative, name, namespace):
    path, tree = source_tree(relative)
    nodes = [node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError("Exactly one actual declaration required: " + name)
    node = copy.deepcopy(nodes[0])
    node.decorator_list = []  # No server registration is performed by this test.
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(path), "exec", flags=__future__.annotations.compiler_flag, dont_inherit=True), namespace)
    return namespace[name]


def actual_provider(profile):
    path, tree = source_tree(DIAGNOSTICS)
    namespace = {"Path": Path, "hashlib": hashlib}
    nodes = []
    constants = {"LOG_NAMES", "MAX_LOG_BYTES", "MAX_LOG_LITERALS",
                 "MAX_LITERAL_CHARS", "MAX_LITERAL_SAMPLES", "MAX_LINE_CHARS"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in constants
                for target in node.targets):
            nodes.append(copy.deepcopy(node))
        elif isinstance(node, ast.FunctionDef) and node.name == "_bounded_line":
            nodes.append(copy.deepcopy(node))
        elif isinstance(node, ast.ClassDef) and node.name == "Ck3DiagnosticsError":
            nodes.append(copy.deepcopy(node))
        elif isinstance(node, ast.ClassDef) and node.name == "Ck3RuntimeDiagnosticsInspector":
            selected = copy.deepcopy(node)
            selected.body = [method for method in selected.body
                             if isinstance(method, ast.FunctionDef) and method.name in {
                                 "__init__", "_assert_below_profile", "query_engine_log_literals_v1"}]
            nodes.append(selected)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(path), "exec", flags=__future__.annotations.compiler_flag, dont_inherit=True), namespace)
    return namespace["Ck3RuntimeDiagnosticsInspector"](profile)


class LogPipeline:
    def __init__(self, profile):
        provider = actual_provider(profile)
        self.public = actual_function(MCP, LOG_TOOL, {"runtime_diagnostics": provider})
        self.steps = []
        self.rows = []

    def execute_plan(self, steps, name):
        self.steps.extend(copy.deepcopy(steps))
        rows = []
        for step in steps:
            if step["tool"] != LOG_TOOL:
                raise AssertionError("Unexpected dispatched tool in offline log pipeline")
            # Required names/defaults come from the real public declaration.
            inspect.signature(self.public).bind(**step["args"])
            rows.append({"id": step["id"], "result": self.public(**step["args"])})
        self.rows.extend(rows)
        return rows


class WitnessCaptured(Exception):
    pass


class LawWitnessPipeline(LogPipeline):
    """Capture actual adapter arguments; no physical/native query is executed."""
    def execute_plan(self, steps, name):
        for step in steps:
            declaration = actual_function(MCP, step["tool"], {})
            args = copy.deepcopy(step["args"])
            if "expected_revision" in inspect.signature(declaration).parameters:
                if step.get("fresh_revision") is not True:
                    raise AssertionError("Required current revision was not requested")
                args["expected_revision"] = 17  # Synthetic public revision, never a live value.
            inspect.signature(declaration).bind(**args)
        if len(steps) == 1 and steps[0]["tool"] == "ck3_query_campaign_root_context_v1":
            return [{"id": steps[0]["id"], "result": {
                "campaign_root_context": {"primary_title": {"title_id": 101}}}}]
        log_steps = [step for step in steps if step["tool"] == LOG_TOOL]
        if len(log_steps) != 1:
            raise AssertionError("Exactly one actual law script witness expected")
        super().execute_plan(log_steps, name)
        raise WitnessCaptured()


class LogContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.profile = Path(self.temporary.name)
        (self.profile / "logs").mkdir()
        self.config = json.loads((ROOT / "tools/ck3_mod_acceptance_cases/ted_production_ui.json")
                                 .read_text(encoding="utf-8-sig"))
        self.required = self.config["required_markers"]
        self.forbidden = self.config["forbidden_markers"]
        require = actual_function("tools/ck3_mod_acceptance_cases/_business.py", "require", {})
        self.literals = actual_function("tools/ck3_mod_acceptance_cases/_business.py", "literals", {"require": require})

    def write_log(self, lines):
        (self.profile / "logs/debug.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def check_business(self, lines):
        self.write_log(lines)
        client = LogPipeline(self.profile)
        return self.literals(client, "synthetic-TED-original-markers", self.required, self.forbidden), client

    def test_actual_business_producer_binds_declaration_and_preserves_original_markers(self):
        self.assertEqual((len(self.required), len(self.forbidden)), (6, 3))
        row, client = self.check_business(self.required)
        self.assertIs(row, client.rows[0])
        self.assertEqual(client.steps[0]["args"], {
            "log_name": "debug.log", "literals": self.required + self.forbidden})
        self.assertEqual([item["literal"] for item in row["result"]["matches"]],
                         self.required + self.forbidden)
        self.assertEqual([item["line_count"] for item in row["result"]["matches"]], [1] * 6 + [0] * 3)

    def test_original_required_marker_missing_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check_business(self.required[1:])

    def test_original_required_marker_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check_business(self.required + [self.required[0]])

    def test_original_forbidden_marker_actual_count_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check_business(self.required + [self.forbidden[0]])

    def test_actual_provider_counts_are_case_sensitive(self):
        with self.assertRaises(ValueError):
            self.check_business([self.required[0].swapcase(), *self.required[1:]])

    def test_missing_log_name_and_short_debug_alias_are_rejected(self):
        self.write_log(self.required)
        client = LogPipeline(self.profile)
        with self.assertRaises(TypeError):
            inspect.signature(client.public).bind(literals=self.required)
        with self.assertRaises(ValueError):
            client.public(log_name="debug", literals=self.required)
        with self.assertRaises(ValueError):
            client.public(log_name="debug.log", literals=["duplicate", "duplicate"])
        with self.assertRaises(ValueError):
            client.public(log_name="debug.log", literals=["marker" + str(i) for i in range(17)])

    def test_three_actual_law_adapter_witnesses_bind_public_contract(self):
        # Exercise the real adapter merge, not a changed marker-data producer.
        sys.path.insert(0, str(ROOT))
        self.addCleanup(sys.path.remove, str(ROOT))
        from tools import reclaim_the_motherland_effective_law_contract as law
        require = actual_function("tools/ck3_mod_acceptance_cases/_business.py", "require", {})
        phase = actual_function("tools/ck3_mod_acceptance_cases/rmtm_adapter.py", "_law_phase", {"require": require})
        for name in ("d3", "predeath", "postdeath"):
            with self.subTest(phase=name):
                marker_data = law.phase_literals(name)
                self.assertEqual(set(marker_data), {"literals"})
                self.write_log(marker_data["literals"])
                client = LawWitnessPipeline(self.profile)
                with self.assertRaises(WitnessCaptured):
                    phase(client, name)
                self.assertEqual(client.steps[0]["args"], {"log_name": "debug.log", **marker_data})
                self.assertEqual([item["literal"] for item in client.rows[0]["result"]["matches"]],
                                 marker_data["literals"])

    def test_original_QOL_log_batches_bind_actual_public_signature_and_provider_limit(self):
        self.write_log([])
        plans = json.loads((ROOT / "tools/ck3_mod_acceptance_cases/xqol_original_plans.json")
                           .read_text(encoding="utf-8-sig"))
        batches = [step for section in ("d0", "final6") for step in plans[section]["steps"]
                   if step.get("tool") == LOG_TOOL]
        self.assertEqual([len(step["args"]["literals"]) for step in batches], [16, 9, 16, 7, 3, 4, 2])
        client = LogPipeline(self.profile)
        for step in batches:
            row = client.execute_plan([step], "synthetic-original-QOL-data")[0]
            self.assertTrue(row["result"]["read_only"])
            self.assertEqual([item["literal"] for item in row["result"]["matches"]], step["args"]["literals"])


if __name__ == "__main__":
    unittest.main()
