"""Offline candidate routing/identity tests; no CK3 or mechanism qualification."""
from __future__ import annotations

import ast
import asyncio
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

CANDIDATE = Path(__file__).resolve().parents[1]
# Normal repository execution needs no external candidate/base directory.
# An external overlay test explicitly binds the unchanged dependency checkout.
REPO = Path(os.environ.get("XAR_TEST_SOURCE_ROOT", str(CANDIDATE))).resolve()
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


A = module(CANDIDATE / "tools/ck3_mod_acceptance_cases/faith_e02_d1_readonly_adapter.py", "candidate_d1_adapter")
Q = module(CANDIDATE / "tools/faith_e02_d1_readonly_queue.py", "candidate_d1_queue")
M = module(CANDIDATE / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py",
           "xar_autoplayer.bridge.mcp_server_next_scene_candidate")


def context():
    saved = {"save": "original-D1.ck3", "bytes": A.SAVE_BYTES, "sha256": A.SAVE_SHA256,
             "player_id": 31254, "date_raw": 53144328}
    c = {"schema": "faith-engine-e02-d1-readonly-case-v1", "product": A.PRODUCT,
         "case": A.CASE, "machine_id": "4-8e1c2f1861", "saved_input": saved,
         "historical_identity_expectation": {
             "kind": "historical_expectation_not_fresh_observation",
             "source": {"path": "source.py", "bytes": 42, "sha256": "a" * 64},
             "player_id": saved["player_id"], "date_raw": saved["date_raw"]},
         "profile": {"enabled_mods": [], "product_files": []}, "scope": dict(A.SCOPE)}
    spec = {"required_mcp_tools": sorted(A.REQUIRED_TOOLS),
            "opt_in_read_only_mcp_tools": sorted(A.READONLY_TOOLS),
            **{key: False for key in A.ACTION_OPT_INS}}
    return {"product": A.PRODUCT, "case": A.CASE, "case_contract": c, "case_spec": spec,
            "run_id": "offline-synthetic-d1-scene", "shared_source_root": str(REPO)}


def frame(actor=31254, date=53144352, revision=5):
    return {
        "snapshot_id": "offline-native:" + str(revision), "revision": revision,
        "native_revision": revision - 1, "date_raw": date,
        "played_character": {"character_id": actor, "alive": True},
        "paused": True, "map_ready": True, "active_event": None, "episode_run_id": None,
        "diagnostics": {"connection_generation": 4, "hello": {
            "pid": 1234, "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
            "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}},
    }


def step(i, tool, args=None, fresh=True):
    return {"id": "d1-" + str(i), "tool": tool, "args": args or {},
            "fresh_revision": fresh, "continue_on_error": True}


def plan():
    return {"steps": [
        step(1, "ck3_take_snapshot"),
        step(2, "ck3_query_player_religion_context_v1"),
        step(3, "ck3_query_player_rite_governance_v1"),
        step(4, "ck3_query_player_pilgrimage_activities_v1"),
        step(5, "ck3_open_ingame_decisions_v1"),
        step(6, "ck3_inspect_gui_window_tree_v1", {"window_kind": "decisions"}),
        step(7, "ck3_query_ingame_decision_item_v1", {"decision_key": Q.DECISION}),
        step(8, "ck3_select_ingame_decision_item_v1", {"decision_key": Q.DECISION}),
        step(9, "ck3_query_ingame_decision_item_v1", {"decision_key": Q.DECISION}),
    ]}


class IdentityAndCaseTests(unittest.TestCase):
    def test_valid_contract_and_fresh_date_replaces_only_historical_expectation(self):
        c = A.validate_contract(context())
        actual = A.initial_scene_binding(frame(), c)
        self.assertEqual(actual["date_raw"], 53144352)
        self.assertNotEqual(actual["date_raw"], c["saved_input"]["date_raw"])
        A.validate_capture_frame(frame(revision=100), actual)

    def test_changed_actor_stops_before_queries(self):
        with self.assertRaisesRegex(ValueError, "actual native player"):
            A.initial_scene_binding(frame(actor=31255), context()["case_contract"])

    def test_actual_actor_and_date_drift_stay_errors(self):
        binding = A.initial_scene_binding(frame(), context()["case_contract"])
        for actual in (frame(actor=31255), frame(date=53144353)):
            with self.subTest(actual=actual):
                with self.assertRaises(ValueError):
                    A.validate_capture_frame(actual, binding)

    def test_context_must_be_live_paused_map_without_event(self):
        for field, value in (("paused", False), ("map_ready", False), ("active_event", {"id": 1})):
            bad = frame()
            bad[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    A.initial_scene_binding(bad, context()["case_contract"])

    def test_source_save_pin_cannot_be_swapped(self):
        bad = context()
        bad["case_contract"]["saved_input"]["sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            A.validate_contract(bad)

    def test_all_world_action_lanes_and_tool_companions_remain_closed(self):
        for key in A.ACTION_OPT_INS:
            bad = context()
            bad["case_spec"][key] = True
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    A.validate_contract(bad)
        bad = context()
        bad["case_spec"]["required_mcp_tools"].append("ck3_confirm_ingame_decision_outcome_v1")
        with self.assertRaises(ValueError):
            A.validate_contract(bad)

    def test_run_writes_independent_first_identity_and_binds_actual_date(self):
        class Client:
            operator_reviewer = "synthetic-reviewer"
            calls = 0
            snapshots = 0
            def snapshot(self):
                self.snapshots += 1
                return frame(revision=5 if self.snapshots == 1 else 6)
            def checkpoint(self, key, value):
                pass
            def root_checkpoint(self, key, value, reserve):
                self.calls += 1
                self.parent_binding = value["scene_binding"]
                return {"run_id": "offline-synthetic-d1-scene", "reviewer": self.operator_reviewer,
                        "status": "complete"}
        with tempfile.TemporaryDirectory() as directory:
            c = context()
            c["output"] = directory
            client = Client()
            result = A.run_case(c, client)
            observed = json.loads((Path(directory) / "faith-e02-d1-first-native-identity.json").read_text())
            self.assertTrue(observed["fresh_identity_validated"])
            self.assertEqual(observed["scene_binding"]["date_raw"], 53144352)
            self.assertEqual(client.parent_binding, observed["scene_binding"])
            self.assertEqual(client.calls, 1)
            self.assertFalse(result["business_pass"])
            self.assertFalse(A.verify_case(c)["business_pass"])

    def test_run_actor_mismatch_still_records_actual_identity_and_never_holds(self):
        class Client:
            calls = 0
            def snapshot(self):
                return frame(actor=98765)
            def root_checkpoint(self, *args, **kwargs):
                self.calls += 1
                raise RuntimeError("must never reach Root query lane")
        with tempfile.TemporaryDirectory() as directory:
            c, client = context(), Client()
            c["output"] = directory
            with self.assertRaises(ValueError):
                A.run_case(c, client)
            actual = json.loads((Path(directory) / "faith-e02-d1-first-native-identity.json").read_text())
            self.assertEqual(actual["actual_snapshot"]["played_character"]["character_id"], 98765)
            self.assertFalse(actual["fresh_identity_validated"])
            self.assertEqual(client.calls, 0)
            self.assertFalse((Path(directory) / "faith-e02-d1-readonly-holder-result.json").exists())

    def test_b1_original_fixed_contract_keeps_its_C2_identity(self):
        from ck3_mod_acceptance_cases import faith_e02_readonly_adapter as B1
        self.assertNotEqual(B1.CASE, A.CASE)
        self.assertEqual(B1.SAVED_IDENTITY["player_id"], 15893)
        self.assertEqual(B1.SAVED_IDENTITY["bytes"], 50210503)
        self.assertEqual(B1.READONLY_TOOLS, frozenset({
            "ck3_query_player_holy_site_creation_context_v1", "ck3_query_player_religion_context_v1",
            "ck3_query_player_holy_site_v1", "ck3_query_faith_power_ui_v1"}))


class FiniteQueueTests(unittest.TestCase):
    def test_valid_query_only_and_selected_readback_plans(self):
        self.assertTrue(Q.validate(plan())["capture_policy_validated"])
        pure = {"steps": plan()["steps"][:4]}
        self.assertEqual(Q.validate(pure)["steps"], 4)

    def test_every_world_confirmation_day_save_and_activity_start_is_rejected(self):
        for tool in ("ck3_confirm_ingame_decision_item_v1", "ck3_confirm_ingame_decision_outcome_v1",
                     "ck3_execute_player_rite_creation_action_v1", "ck3_migration_raw_step",
                     "ck3_start_activity_v1", "ck3_set_speed", "ck3_save_checkpoint"):
            with self.subTest(tool=tool):
                with self.assertRaises(ValueError):
                    Q.validate({"steps": [step(1, tool)]})
        for kind in ("advance_day", "raw_step", "finish_hold", "write-inbox"):
            bad = {"steps": [step(1, "ck3_take_snapshot")]}
            bad["steps"][0]["kind"] = kind
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    Q.validate(bad)

    def test_select_needs_actual_key_query_before_and_fresh_query_after(self):
        for indexes in ([7, 8], [6, 7], [6, 7, 0]):
            bad = {"steps": [deepcopy(plan()["steps"][i]) for i in indexes]}
            with self.subTest(indexes=indexes):
                with self.assertRaises(ValueError):
                    Q.validate(bad)
        bad = plan()
        bad["steps"][-1]["fresh_revision"] = False
        bad["steps"][-1]["args"]["expected_revision"] = 1
        with self.assertRaises(ValueError):
            Q.validate(bad)

    def test_no_other_decision_or_extra_actor_can_be_selected(self):
        bad = plan()
        bad["steps"][-1]["args"]["decision_key"] = "other_decision"
        with self.assertRaises(ValueError):
            Q.validate(bad)
        bad = plan()
        bad["steps"][2]["args"]["character_id"] = 31254
        with self.assertRaises(ValueError):
            Q.validate(bad)

    def test_missing_readbacks_duplicate_ids_and_fatal_query_policy_rejected(self):
        mutations = [
            lambda p: p["steps"].pop(5),
            lambda p: p["steps"][1].update(id=p["steps"][0]["id"]),
            lambda p: p["steps"][1].update(continue_on_error=False),
            lambda p: p["steps"][1].update(fresh_revision=False),
        ]
        for mutate in mutations:
            bad = plan()
            mutate(bad)
            with self.assertRaises(ValueError):
                Q.validate(bad)


def constant_set(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = [n for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    return set(ast.literal_eval(nodes[0].value.args[0]))


def host_choices(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument"
                and any(isinstance(a, ast.Constant) and a.value == "--case-read-only-mcp-tool" for a in n.args)):
            return set(ast.literal_eval(next(k.value for k in n.keywords if k.arg == "choices")))
    raise ValueError("actual host read-only choices missing")


def bind_host_permissions(driver, declared):
    p = CANDIDATE / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
    tree = ast.parse(p.read_text(encoding="utf-8-sig"))
    names = {"allow_private_player_rite_governance_query", "allow_private_player_pilgrimage_activities_query"}
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "native_server")
    nodes = [n for n in function.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Attribute) and t.attr in names for t in n.targets)]
    if len(nodes) != 2:
        raise ValueError("two actual native_server permission assignments required")
    driver.case_declared_read_only_mcp_tools = frozenset(declared)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(p), "exec"), {"driver": driver})


class PublicWiringTests(unittest.TestCase):
    def test_two_readonly_queries_are_public_choices_of_entry_and_actual_host(self):
        required = {"ck3_query_player_rite_governance_v1", "ck3_query_player_pilgrimage_activities_v1"}
        entry = constant_set(CANDIDATE / "tools/ck3_mod_acceptance.py", "CASE_READ_ONLY_MCP_TOOLS")
        host = host_choices(CANDIDATE / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
        self.assertTrue(required <= entry)
        self.assertTrue(required <= host)
        self.assertEqual(entry, host)
        self.assertTrue(all(name.startswith("ck3_query_") for name in entry))
        for action in ("ck3_confirm_ingame_decision_item_v1", "ck3_confirm_ingame_decision_outcome_v1",
                       "ck3_execute_player_rite_creation_action_v1", "ck3_start_activity_v1"):
            self.assertNotIn(action, entry)
            self.assertNotIn(action, host)

    def test_actual_host_boolean_assignments_are_exact_and_do_not_enable_companions(self):
        class Driver:
            allow_private_holy_site_creation_create_once = False
            allow_private_holy_site_relic_actions = False
            allow_private_player_rite_creation_actions = False
        for declared in (set(), {QRY_GOV}, {QRY_PIL}, {QRY_GOV, QRY_PIL}):
            d = Driver()
            bind_host_permissions(d, declared)
            self.assertIs(d.allow_private_player_rite_governance_query, QRY_GOV in declared)
            self.assertIs(d.allow_private_player_pilgrimage_activities_query, QRY_PIL in declared)
            self.assertFalse(d.allow_private_holy_site_creation_create_once)
            self.assertFalse(d.allow_private_holy_site_relic_actions)
            self.assertFalse(d.allow_private_player_rite_creation_actions)


QRY_GOV = "ck3_query_player_rite_governance_v1"
QRY_PIL = "ck3_query_player_pilgrimage_activities_v1"


class DeclaredQueryMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_registered_mcp_adds_only_two_tools_and_forwards_fresh_revision(self):
        from mcp import Client
        class Driver:
            def __init__(self, declared):
                self.calls = []
                bind_host_permissions(self, declared)
            def take_snapshot(self):
                return frame()
            def capabilities(self):
                return {}
            def query_player_rite_governance_private_v1(self, *, expected_revision):
                self.calls.append((QRY_GOV, expected_revision))
                return {"scope": "synthetic-forwarding-only", "expected_revision": expected_revision}
            def query_player_pilgrimage_activities_private_v1(self, *, expected_revision):
                self.calls.append((QRY_PIL, expected_revision))
                return {"scope": "synthetic-forwarding-only", "expected_revision": expected_revision}
        base = Driver(set())
        async with Client(M.create_server(base)) as client:
            names_before = {t.name for t in (await client.list_tools()).tools}
        changed = Driver({QRY_GOV, QRY_PIL})
        async with Client(M.create_server(changed)) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            self.assertEqual(set(tools) - names_before, {QRY_GOV, QRY_PIL})
            for name in (QRY_GOV, QRY_PIL):
                self.assertTrue(tools[name].annotations.read_only_hint)
                self.assertEqual(set(tools[name].input_schema["properties"]), {"expected_revision"})
                result = await client.call_tool(name, {"expected_revision": 5})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["expected_revision"], 5)
            bad = await client.call_tool(QRY_PIL, {"expected_revision": 5, "character_id": 31254})
            self.assertTrue(bad.is_error)
        self.assertEqual(changed.calls, [(QRY_GOV, 5), (QRY_PIL, 5)])
        self.assertEqual(base.calls, [])


if __name__ == "__main__":
    unittest.main()
