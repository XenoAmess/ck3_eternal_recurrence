"""Actual public case admission, argv, host parser and permission; never launches."""
from __future__ import annotations

import argparse
import ast
import contextlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest

import ck3_mod_acceptance as entry
import test_ck3_mod_acceptance as shared_test_support

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
# Default repository tests read repository source. The external candidate runner
# may supply exact SHA-checked source text in memory without applying the patch.
SOURCE_TEXT_OVERRIDES = {}
TOOLS = {"ck3_query_player_pilgrimage_planner_v1", "ck3_submit_player_pilgrimage_planner_v1"}
FLAG = "--allow-private-player-pilgrimage-execution"
KEY = "opt_in_player_pilgrimage_execution"


def source_text(path):
    return SOURCE_TEXT_OVERRIDES.get(str(path.resolve()), path.read_text(encoding="utf-8-sig"))


def execute_nodes(nodes, namespace, filename):
    tree = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(tree, str(filename), "exec"), namespace)


class PublicCaseTests(unittest.TestCase):
    def setUp(self):
        # Reuse the existing small shared-runtime fixture, with the actual entry
        # module under test. No external baseline or game input is required.
        self.old_support_entry = shared_test_support.entry
        shared_test_support.entry = entry
        self.addCleanup(setattr, shared_test_support, "entry", self.old_support_entry)
        self.support = shared_test_support.SharedEntryTests()
        self.support.setUp()
        self.addCleanup(self.support.doCleanups)
        self.case = self.support.products["products"]["xqol"]["cases"][0]
        # Pin the actual host source as metadata; the host is never imported/run.
        self.support.host.write_text(source_text(HOST), encoding="utf-8")
        self.support.manifest["host"] = {
            "path_key": "host", **{key: value for key, value in entry.pin(self.support.host).items() if key != "path"}}
        for tool in TOOLS:
            self.support.manifest["capabilities"][tool] = {
                "source_build_ready": True, "actual_live_qualified": False}
        self.support.write(self.support.manifest_path, self.support.manifest)
        self.support.runtime["manifest"] = entry.pin(self.support.manifest_path)
        self.support.write(self.support.runtime_path, self.support.runtime)

    def select(self):
        self.support.write(self.support.products_path, self.support.products)
        return self.support.select()

    def test_exact_two_tools_are_execution_only_and_not_readonly(self):
        self.assertEqual(entry.CASE_PLAYER_PILGRIMAGE_EXECUTION_MCP_TOOLS, TOOLS)
        self.assertFalse(TOOLS & entry.CASE_READ_ONLY_MCP_TOOLS)

    def test_full_selection_default_false_and_explicit_false_do_not_forward(self):
        for value in ("missing", False):
            with self.subTest(value=value):
                if value is False:
                    self.case[KEY] = value
                selected = self.select()
                self.assertIs(selected.opt_in_player_pilgrimage_execution, False)
                self.assertNotIn(FLAG, selected.argv)
                self.assertIs(selected.describe()[KEY], False)

    def test_exact_true_requires_both_tools_and_forwards_once(self):
        self.case[KEY] = True
        self.case["required_mcp_tools"] += sorted(TOOLS)
        selected = self.select()
        self.assertEqual(selected.argv.count(FLAG), 1)
        self.assertIs(selected.describe()[KEY], True)
        self.assertEqual(selected.preflight()["blockers"], [])
        self.assertEqual(selected.describe()["runtime_status"], "NOT_RUN")

    def test_missing_tools_are_rejected_before_host_launch(self):
        self.case[KEY] = True
        original = list(self.case["required_mcp_tools"])
        for required in ([], *[[tool] for tool in sorted(TOOLS)]):
            with self.subTest(required=required):
                self.case["required_mcp_tools"] = original + required
                with self.assertRaisesRegex(ValueError, "both planner query and submit"):
                    self.select()

    def test_declaring_any_execution_tool_without_optin_does_not_enable_it(self):
        original = list(self.case["required_mcp_tools"])
        for required in ([tool] for tool in sorted(TOOLS)):
            with self.subTest(required=required):
                self.case["required_mcp_tools"] = original + required
                with self.assertRaisesRegex(ValueError, "explicit execution case opt-in"):
                    self.select()

    def test_non_boolean_optins_are_rejected(self):
        self.case["required_mcp_tools"] += sorted(TOOLS)
        for value in (None, 0, 1, "true", "false", [], {}):
            with self.subTest(value=value):
                self.case[KEY] = value
                with self.assertRaisesRegex(ValueError, "explicit Boolean"):
                    self.select()

    def test_readonly_identity_and_case_declaration_cannot_promote_execution(self):
        identity = "ck3_query_player_pilgrimage_activities_v1"
        self.case["required_mcp_tools"].append(identity)
        self.case["opt_in_read_only_mcp_tools"] = [identity]
        selected = self.select()
        self.assertIs(selected.opt_in_player_pilgrimage_execution, False)
        self.assertNotIn(FLAG, selected.argv)
        self.assertIn(identity, selected.argv)
        for tool in sorted(TOOLS):
            with self.subTest(tool=tool):
                self.case["opt_in_read_only_mcp_tools"] = [identity, tool]
                self.case["required_mcp_tools"].append(tool)
                with self.assertRaisesRegex(ValueError, "read-only opt-in"):
                    self.select()

    def test_adapter_context_reports_actual_execution_bool(self):
        selected = self.select()
        selected.adapter_config = self.support.files["initial"]
        selected.products["product_inventory"] = str(self.support.files["inventory"])
        self.assertIs(selected.adapter_context(inputs={})[KEY], False)
        self.case[KEY] = True
        self.case["required_mcp_tools"] += sorted(TOOLS)
        selected = self.select()
        selected.adapter_config = self.support.files["initial"]
        selected.products["product_inventory"] = str(self.support.files["inventory"])
        self.assertIs(selected.adapter_context(inputs={})[KEY], True)


class ActualHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(source_text(HOST), str(HOST))
        cls.functions = {node.name: node for node in cls.tree.body
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        namespace = {"argparse": argparse, "Path": Path, "__doc__": "test"}
        execute_nodes([cls.functions["parser"], cls.functions["bind_player_pilgrimage_execution_permission"]],
                      namespace, HOST)
        cls.parser = staticmethod(namespace["parser"])
        cls.bind = staticmethod(namespace["bind_player_pilgrimage_execution_permission"])
        run = cls.functions["run"]
        cls.forward = next(node for node in run.body if isinstance(node, ast.If)
            and "allow_private_player_pilgrimage_execution" in ast.unparse(node.test))
        server = cls.functions["native_server"]
        cls.binding_call = next(node for node in server.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "bind_player_pilgrimage_execution_permission")

    def test_actual_parser_default_off_explicit_on_and_identity_remains_independent(self):
        self.assertIs(self.parser().parse_args([]).allow_private_player_pilgrimage_execution, False)
        self.assertIs(self.parser().parse_args([FLAG]).allow_private_player_pilgrimage_execution, True)
        args = self.parser().parse_args(["--case-read-only-mcp-tool", "ck3_query_player_pilgrimage_activities_v1"])
        self.assertIs(args.allow_private_player_pilgrimage_execution, False)
        self.assertEqual(args.case_read_only_mcp_tool, ["ck3_query_player_pilgrimage_activities_v1"])

    def test_actual_readonly_choices_reject_both_execution_tools(self):
        for tool in sorted(TOOLS):
            with self.subTest(tool=tool), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.parser().parse_args(["--case-read-only-mcp-tool", tool])
                self.assertEqual(error.exception.code, 2)

    def test_parent_to_server_child_forwards_once_only_when_explicit_true(self):
        for value in (None, False, True, 1, "true"):
            with self.subTest(value=value):
                args = SimpleNamespace(case_read_only_mcp_tool=["ck3_query_player_pilgrimage_activities_v1"])
                if value is not None:
                    args.allow_private_player_pilgrimage_execution = value
                child_args = ["host.py", "--server"]
                execute_nodes([self.forward], {"args": args, "child_args": child_args}, HOST)
                self.assertEqual(child_args, ["host.py", "--server", FLAG] if value is True else ["host.py", "--server"])
                parsed = self.parser().parse_args(child_args[1:])
                self.assertIs(parsed.allow_private_player_pilgrimage_execution, value is True)

    def test_actual_native_server_call_maps_only_new_arg_and_not_identity_or_rite(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                driver = SimpleNamespace(allow_private_player_pilgrimage_execution=False,
                    allow_private_player_pilgrimage_activities_query=True,
                    allow_private_player_rite_creation_actions=True)
                args = self.parser().parse_args([FLAG] if enabled else [
                    "--case-read-only-mcp-tool", "ck3_query_player_pilgrimage_activities_v1"])
                execute_nodes([self.binding_call], {"args": args, "driver": driver,
                    "bind_player_pilgrimage_execution_permission": self.bind}, HOST)
                self.assertIs(driver.allow_private_player_pilgrimage_execution, enabled)
                self.assertIs(driver.allow_private_player_pilgrimage_activities_query, True)
                self.assertIs(driver.allow_private_player_rite_creation_actions, True)

    def test_permission_binding_rejects_truthy_non_boolean(self):
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(value=value):
                driver = SimpleNamespace(allow_private_player_pilgrimage_execution=False)
                with self.assertRaisesRegex(ValueError, "explicit boolean"):
                    self.bind(driver, value)
                self.assertIs(driver.allow_private_player_pilgrimage_execution, False)

    def test_full_public_argv_to_parent_child_to_permission_chain(self):
        support = PublicCaseTests()
        support.setUp()
        self.addCleanup(support.doCleanups)
        support.case[KEY] = True
        support.case["required_mcp_tools"] += sorted(TOOLS)
        selected = support.select()
        parent = self.parser().parse_args(selected.argv[5:])
        self.assertIs(parent.allow_private_player_pilgrimage_execution, True)
        child_args = ["--server"]
        execute_nodes([self.forward], {"args": parent, "child_args": child_args}, HOST)
        child = self.parser().parse_args(child_args)
        driver = SimpleNamespace(allow_private_player_pilgrimage_execution=False)
        execute_nodes([self.binding_call], {"args": child, "driver": driver,
            "bind_player_pilgrimage_execution_permission": self.bind}, HOST)
        self.assertIs(driver.allow_private_player_pilgrimage_execution, True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
