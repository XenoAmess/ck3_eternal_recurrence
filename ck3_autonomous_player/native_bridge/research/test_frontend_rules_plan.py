"""Offline protocol checks for the optional pre-Start typed rule plan."""
from __future__ import annotations

import ast
import asyncio
import copy
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_ck3_12002_mcp_live as harness


TOOLS = {
    "ck3_query_frontend_game_rules_window_v1", "ck3_activate_frontend_game_rules_v1",
    "ck3_query_frontend_game_rule_selections_v1", "ck3_select_frontend_game_rule_v1",
    "ck3_apply_and_hide_frontend_game_rules_v1", "ck3_query_frontend_applied_game_rules_v1",
}
INTENT = {"schema": "ck3-frontend-rules-plan-v1", "schema_version": 1, "rules": [
    {"rule_key": "product_enabled", "desired_setting_key": "product_on"},
    {"rule_key": "product_frequency", "desired_setting_key": "product_yearly"},
    {"rule_key": "product_ratio", "desired_setting_key": "product_strict"},
]}


class ActualRulesClient:
    def __init__(self, *, opened=False, lost=None, unrelated_change=False,
                 stale_sequence=False, no_apply=False, unavailable_apply=False):
        self.tools = {name: {} for name in TOOLS}
        self.calls = []
        self.sequence = 0
        self.binding = {"bridge_pid": 42, "connection_generation": 9}
        self.values = {"product_enabled": "product_off", "product_frequency": "product_three_year",
                       "product_ratio": "product_relaxed", "vanilla_rule": "vanilla_default"}
        self.old_values = dict(self.values)
        self.opened, self.lost, self.unrelated_change = opened, lost, unrelated_change
        self.stale_sequence, self.no_apply, self.unavailable_apply = stale_sequence, no_apply, unavailable_apply
        self.applied_queries = 0

    def packet(self, schema, source, ready=True):
        self.sequence += 1
        return {"schema": schema, "schema_version": 1, "source": source,
            "read_only": True, "backend_id": "native-headless", "game_version": "1.20.0.3",
            "executable_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
            "uses_ocr": False, "uses_mouse": False, "uses_keyboard": False,
            "binding": dict(self.binding), "query_sequence": 1 if self.stale_sequence else self.sequence,
            "ready": ready, "unavailable_reason": "" if ready else "actual_instance_pending",
            "applied_settings_proven": schema == "frontend_applied_game_rules_v1" and ready}

    def window(self):
        return {**self.packet("frontend_game_rules_window_v1",
            "CJominiGameRulesGui.owner_root_and_stock_predicates"),
            "window_visible": self.opened, "window_enabled": True, "is_host": True,
            "game_has_started": False, "may_edit": self.opened, "window_closed_proven": not self.opened}

    def selections(self, applied=False, values=None, ready=True):
        values = self.values if values is None else values
        return {**self.packet("frontend_applied_game_rules_v1" if applied else "frontend_game_rule_selections_v1",
            "CGameRuleInstance.selected_settings" if applied else "CJominiGameRulesGui.current_selections", ready),
            "selection_count": len(values) if ready else 0,
            "selections": [{"rule_key": key, "selected_setting_key": value}
                           for key, value in sorted(values.items())] if ready else []}

    async def call(self, name, arguments=None):
        self.calls.append((name, copy.deepcopy(arguments)))
        if name == "ck3_query_frontend_game_rules_window_v1":
            return self.window()
        if name == "ck3_activate_frontend_game_rules_v1":
            self.opened = True
            result = {"status": "observed", "dispatch_invoked": True, "observation": self.selections()}
        elif name == "ck3_query_frontend_game_rule_selections_v1":
            return self.selections()
        elif name == "ck3_select_frontend_game_rule_v1":
            assert arguments["expected_current_setting_key"] == self.values[arguments["rule_key"]]
            self.values[arguments["rule_key"]] = arguments["desired_setting_key"]
            if self.unrelated_change:
                self.values["vanilla_rule"] = "unrequested_choice"
            result = {"status": "observed", "rule_key": arguments["rule_key"],
                "selected_setting_key": arguments["desired_setting_key"], "applied_settings_proven": False,
                "observation": self.selections()}
        elif name == "ck3_apply_and_hide_frontend_game_rules_v1":
            self.opened = False
            result = {"status": "observed", "window_closed_proven": True,
                "applied_settings_proven": False, "window_observation": self.window()}
        elif name == "ck3_query_frontend_applied_game_rules_v1":
            self.applied_queries += 1
            return self.selections(applied=True, values=self.old_values if self.no_apply or self.applied_queries == 1 else self.values,
                ready=not (self.unavailable_apply and self.applied_queries == 1))
        else:
            raise AssertionError("unadmitted tool or map snapshot called")
        if self.lost == name:
            raise TimeoutError("simulated lost ACK after actual submission")
        return result


class FrontendRulesPlanTests(unittest.IsolatedAsyncioTestCase):
    async def run_plan(self, client, report=None, timeout=1):
        report = {} if report is None else report
        writes = []
        await harness.execute_frontend_rules_plan(client, INTENT, report=report,
            write=lambda: writes.append(copy.deepcopy(report)), timeout=timeout, poll_interval=0)
        return report, writes

    async def test_dynamic_three_key_requests_and_later_actual_apply(self):
        client = ActualRulesClient()
        report, writes = await self.run_plan(client)
        requests = [args for name, args in client.calls if name == "ck3_select_frontend_game_rule_v1"]
        self.assertEqual([args["expected_current_setting_key"] for args in requests],
            ["product_off", "product_three_year", "product_relaxed"])
        self.assertTrue(all(set(args) == {"rule_key", "expected_current_setting_key", "desired_setting_key"}
                            for args in requests))
        self.assertEqual(sum(name == "ck3_apply_and_hide_frontend_game_rules_v1" for name, _ in client.calls), 1)
        execution = report["frontend_rules_plan_execution"]
        self.assertEqual(execution["status"], "ACTUAL_RULES_APPLIED_AND_WINDOW_CLOSED")
        self.assertTrue(execution["applied_settings_proven"] and execution["window_closed_proven"])
        self.assertEqual(execution["snapshot_calls"], 0)
        self.assertEqual(client.applied_queries, 2)
        self.assertEqual(execution["requested_selected_pairs"]["vanilla_rule"], "vanilla_default")
        for name in ("ck3_select_frontend_game_rule_v1", "ck3_apply_and_hide_frontend_game_rules_v1"):
            self.assertTrue(any(write["frontend_rules_plan_execution"]["calls"] and write["frontend_rules_plan_execution"]["calls"][-1]["tool"] == name
                and write["frontend_rules_plan_execution"]["calls"][-1]["acknowledged"] is False for write in writes))
        self.assertTrue(set(name for name, _ in client.calls) <= TOOLS)

    async def test_actual_open_window_does_not_reopen(self):
        client = ActualRulesClient(opened=True)
        await self.run_plan(client)
        self.assertNotIn("ck3_activate_frontend_game_rules_v1", [name for name, _ in client.calls])

    async def test_valid_unavailable_instance_is_polled_without_proof_or_reapply(self):
        client = ActualRulesClient(unavailable_apply=True)
        report, writes = await self.run_plan(client)
        self.assertEqual(client.applied_queries, 2)
        self.assertTrue(any(write["frontend_rules_plan_execution"].get("latest_applied_instance", {}).get("ready") is False
                            and write["frontend_rules_plan_execution"]["applied_settings_proven"] is False for write in writes))

    async def test_lost_mutation_ack_stops_once_and_reentry_is_rejected(self):
        for lost in ("ck3_activate_frontend_game_rules_v1", "ck3_select_frontend_game_rule_v1",
                     "ck3_apply_and_hide_frontend_game_rules_v1"):
            with self.subTest(lost=lost):
                client, report = ActualRulesClient(lost=lost), {}
                with self.assertRaises(TimeoutError):
                    await self.run_plan(client, report)
                self.assertEqual(sum(name == lost for name, _ in client.calls), 1)
                self.assertEqual(report["frontend_rules_plan_execution"]["status"], "FAILED_NO_START")
                self.assertFalse(report["frontend_rules_plan_execution"]["applied_settings_proven"])
                count = len(client.calls)
                with self.assertRaisesRegex(RuntimeError, "already attempted"):
                    await self.run_plan(client, report)
                self.assertEqual(len(client.calls), count)

    async def test_missing_target_rejects_before_first_select(self):
        client = ActualRulesClient()
        del client.values["product_ratio"]
        with self.assertRaisesRegex(RuntimeError, "absent"):
            await self.run_plan(client)
        self.assertFalse(any(name in {"ck3_select_frontend_game_rule_v1", "ck3_apply_and_hide_frontend_game_rules_v1"}
                             for name, _ in client.calls))

    async def test_unrequested_rule_change_stops_without_apply(self):
        client = ActualRulesClient(unrelated_change=True)
        with self.assertRaisesRegex(RuntimeError, "changed another"):
            await self.run_plan(client)
        self.assertNotIn("ck3_apply_and_hide_frontend_game_rules_v1", [name for name, _ in client.calls])

    async def test_window_closure_alone_cannot_prove_actual_apply(self):
        client, report = ActualRulesClient(no_apply=True), {}
        with self.assertRaises(TimeoutError):
            await self.run_plan(client, report, timeout=0)
        self.assertTrue(report["frontend_rules_plan_execution"]["window_closed_proven"])
        self.assertFalse(report["frontend_rules_plan_execution"]["applied_settings_proven"])
        self.assertEqual(client.applied_queries, 1)

    async def test_stale_query_sequence_is_not_independent_evidence(self):
        client = ActualRulesClient(stale_sequence=True)
        with self.assertRaisesRegex(RuntimeError, "later independent"):
            await self.run_plan(client)
        self.assertNotIn("ck3_select_frontend_game_rule_v1", [name for name, _ in client.calls])

    async def test_missing_typed_surface_fails_before_any_call(self):
        client = ActualRulesClient()
        del client.tools["ck3_query_frontend_applied_game_rules_v1"]
        with self.assertRaisesRegex(RuntimeError, "complete typed"):
            await self.run_plan(client)
        self.assertEqual(client.calls, [])

    def test_intent_rejects_expected_current_tools_credit_and_duplicate_targets(self):
        cases = []
        for key, value in (("tool", "ck3_take_snapshot"), ("expected_current_setting_key", "product_on"),
                           ("applied_settings_proven", True)):
            item = copy.deepcopy(INTENT)
            item["rules"][0][key] = value
            cases.append(item)
        item = copy.deepcopy(INTENT)
        item["rules"].append(dict(item["rules"][0]))
        cases.append(item)
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                harness.validate_frontend_rules_plan(item)

    def test_input_preserves_exact_bytes_and_rejects_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rules.json"
            raw = b'\xef\xbb\xbf' + json.dumps(INTENT, indent=4).encode() + b'\r\n'
            path.write_bytes(raw)
            parsed, frozen = harness.load_frontend_rules_plan(path)
            self.assertEqual(parsed, INTENT)
            self.assertEqual(frozen, raw)
            path.write_text('{"schema": "a", "schema": "b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON"):
                harness.load_frontend_rules_plan(path)

    def test_exact_build_binding_predicates_and_credit_are_required(self):
        client = ActualRulesClient()
        window = client.window()
        cases = [("executable_sha256", "OLD"), ("binding", {"bridge_pid": True, "connection_generation": 9}),
                 ("window_closed_proven", False), ("applied_settings_proven", True), ("read_only", False)]
        for key, value in cases:
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                harness.require_frontend_rules_window({**window, key: value})

    def test_optional_cli_rejects_incompatible_modes_before_launch(self):
        self.assertIsNone(harness.parser().parse_args([]).frontend_rules_plan)
        modes = [[], ["--frontend-robert-bootstrap", "--frontend-diagnostic-only"],
                 ["--frontend-robert-bootstrap", "--sdk-smoke-test"],
                 ["--frontend-robert-bootstrap", "--cold-start-checkpoint"]]
        for modes in modes:
            with self.subTest(modes=modes), patch("sys.argv", ["harness", "--frontend-rules-plan", "targets.json", *modes]), \
                    self.assertRaisesRegex(SystemExit, "requires ordinary"):
                harness.main()

    def test_prestart_hook_is_guarded_and_old_execute_has_no_rule_mutations(self):
        source = inspect.getsource(harness.run)
        tree = ast.parse(source)
        names = [(node.lineno, node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
                 for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Name, ast.Attribute))]
        rules_line = next(line for line, name in names if name == "execute_frontend_rules_plan")
        picker_lines = [line for line, name in names if name == "require_verified_bookmarks_picker"]
        start_line = next(node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call)
                          and node.args and isinstance(node.args[0], ast.Constant)
                          and node.args[0].value == "ck3_activate_frontend_start_1066_bookmark_character_v1")
        self.assertLess(min(picker_lines), rules_line)
        self.assertLess(rules_line, max(picker_lines))
        self.assertLess(max(picker_lines), start_line)
        guard = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                     and ast.unparse(node.test) == "frontend_rules_plan is not None")
        self.assertTrue(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                            and node.func.id == "execute_frontend_rules_plan" for node in ast.walk(guard)))
        self.assertNotIn("select_frontend_game_rule", inspect.getsource(harness.PlanClient.execute))


if __name__ == "__main__":
    unittest.main()
