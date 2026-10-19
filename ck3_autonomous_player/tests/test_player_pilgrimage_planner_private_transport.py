"""Strict frozen pilgrimage wire through transport, Driver and registered MCP."""
from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge import player_pilgrimage_planner_private_transport as T
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server


def snapshot(revision=5, native_revision=4):
    return {"snapshot_id": "synthetic-native:" + str(native_revision),
            "revision": revision, "native_revision": native_revision, "date_raw": 53144328,
            "played_character": {"character_id": 31254, "alive": True},
            "played_character_gold": {"raw": 24300000, "scale": 100000},
            "paused": True, "map_ready": True, "episode_run_id": "synthetic-episode",
            "diagnostics": {"connection_generation": 8, "hello": {
                "expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
                "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "pid": 1234}}}


def quote():
    return {
        "schema": "activity-pilgrimage-configured-full10-cost-v1",
        "activity_key": "activity_pilgrimage", "special_option_key": "pilgrimage_type_pious",
        "observed": True, "read_only": True, "raw_pointer_fields_persisted": False,
        "snapshot_revision": 4, "date_raw": 53144328, "actor_character_id": 31254,
        "application_main_thread": True, "paused": True, "map_ready": True, "actor_alive": True,
        "planning_stage": 5, "scale": 100000, "normal_refresh_sequence": 44,
        "configuration_fingerprint": 123456789, "selected_option": {"native_option_id": 93, "key": "pilgrimage_type_pious"},
        "known_cost_names": ["gold", "treasury", "piety", "barter_goods"],
        "known_name_resource_indices": [0, 7, 4, 9],
        "configured_cost_raw": [10000000, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "diagnostic_aggregate_raw": [10000000, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "named_cost_verified": [True, False, False, False, True, False, False, True, False, True],
        "unknown_positive_configured_cost": False, "final_can_start_observed": True, "final_can_start": True,
        "failure_display_known": False, "failure_display": None,
        "failure_display_unknown_reason": "final_canstart_tooltip_getter_unbound",
    }


def body(operation="read", submit=False):
    return {"schema": T.SCHEMA, "read_only": not submit, "snapshot_revision": 4,
            "date_raw": 53144328, "played_character_id": 31254,
            "activity_type_key": "activity_pilgrimage", "special_option_key": "pilgrimage_type_pious",
            "operation": operation, "operation_status": "observed", "invoked": False,
            "needs_recovery": False, "ledger_state": "idle", "failure": "",
            "planner": {"stage": 5, "selected_pious": True, "destination_province_id": 0x80001234,
                        "can_select": None, "can_progress": True},
            "quote": None, "new_identity": None,
            "absence_is_completion": False, "raw_pointer_fields_persisted": False}


class Driver:
    query_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.query_player_pilgrimage_planner_private_v1
    submit_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.submit_player_pilgrimage_planner_private_v1
    def __init__(self, value=None, *, enabled=True):
        self.allow_private_player_pilgrimage_execution = enabled
        self.source = snapshot()
        self.after = deepcopy(self.source)
        self.value = body() if value is None else value
        self.sent = []
        self.endpoint = self
        self.state = self
        self.corrupt = None
    def take_snapshot(self):
        return deepcopy(self.after if self.sent else self.source)
    def capabilities(self):
        return {}
    def send(self, payload):
        self.sent.append(deepcopy(payload))
    def wait_for_command_result(self, request_id, timeout):
        value = {"type": "command_result", "protocol_version": 1, "request_id": request_id, "ok": True,
                 "result": {"step": self.sent[-1]["step"], "accepted": True, "status": "available",
                            "private_build": True, "read_only": self.value["read_only"], "advertised": False,
                            "player_pilgrimage_planner": deepcopy(self.value), "backend_id": "native-headless"}}
        if self.corrupt:
            self.corrupt(value)
        return value


class TransportTests(unittest.TestCase):
    def test_identity_read_permission_and_case_declaration_never_enable_execution(self):
        d = Driver(enabled=False)
        d.allow_private_player_pilgrimage_activities_query = True
        d.case_declared_read_only_mcp_tools = {
            "ck3_query_player_pilgrimage_activities_v1", "ck3_query_player_pilgrimage_planner_v1"}
        with self.assertRaises(UnsupportedStepError):
            d.query_player_pilgrimage_planner_private_v1(expected_revision=5)
        with self.assertRaises(UnsupportedStepError):
            d.submit_player_pilgrimage_planner_private_v1(expected_revision=5, operation="open", policy_positive=True)
        self.assertEqual(d.sent, [])

    def test_real_driver_constructor_declares_explicit_default_false(self):
        parameter = inspect.signature(NativeHeadlessGameplayDriver).parameters["allow_private_player_pilgrimage_execution"]
        self.assertIs(parameter.default, False)

    def test_read_transmits_actual_actor_native_revision_and_fixed_pious_identity(self):
        d = Driver()
        result = d.query_player_pilgrimage_planner_private_v1(expected_revision=5)
        self.assertEqual(len(d.sent), 1)
        sent = d.sent[0]
        self.assertEqual(sent["expected_revision"], 4)
        self.assertEqual(sent["expected_actor_character_id"], 31254)
        self.assertEqual(sent["expected_activity_key"], "activity_pilgrimage")
        self.assertEqual(sent["expected_option_key"], "pilgrimage_type_pious")
        self.assertEqual(sent["step"], T.QUERY_STEP)
        self.assertFalse(result["business_outcome_observed"])
        self.assertFalse(result["automatic_retry"])

    def test_all_query_operations_accept_only_their_frozen_arguments(self):
        for op in T.QUERY_OPERATIONS:
            value = body(op)
            if op == "quote":
                value["quote"] = quote()
            d = Driver(value)
            d.query_player_pilgrimage_planner_private_v1(
                expected_revision=5, operation=op, province_id=0x80001234 if op == "can_select" else 0)
            self.assertEqual(len(d.sent), 1)
        invalid = [
            {"operation": "can_select", "province_id": 0},
            {"operation": "read", "province_id": 12}, {"operation": "quote", "read_stage": 5},
            {"operation": "post", "read_stage": 1}, {"read_stage": True}, {"read_stage": 6},
            {"province_id": True}, {"timeout_seconds": True}, {"timeout_seconds": float("nan")},
            {"timeout_seconds": float("inf")}, {"expected_revision": True}, {"expected_revision": 6},
        ]
        for options in invalid:
            d = Driver()
            kwargs = {"expected_revision": 5, **options}
            with self.subTest(options=options):
                with self.assertRaises((ValueError, BridgeUnavailableError)):
                    d.query_player_pilgrimage_planner_private_v1(**kwargs)
                self.assertEqual(d.sent, [])

    def test_all_serialized_operations_carry_native_required_read_stage(self):
        for op in sorted(T.QUERY_OPERATIONS | T.SUBMIT_OPERATIONS):
            submit = op in T.SUBMIT_OPERATIONS
            d = Driver(body(op, submit))
            kwargs = {"expected_revision": 5, "operation": op,
                      "province_id": 3 if op in {"can_select", "select", "start"} else 0}
            with self.subTest(operation=op):
                if submit:
                    d.submit_player_pilgrimage_planner_private_v1(policy_positive=True, **kwargs)
                else:
                    d.query_player_pilgrimage_planner_private_v1(**kwargs)
                self.assertEqual(len(d.sent), 1)
                self.assertIs(type(d.sent[0]["read_stage"]), int)
                self.assertEqual(d.sent[0]["read_stage"], 0)

    def test_submit_requires_explicit_policy_and_rejects_unused_arguments(self):
        for op in T.SUBMIT_OPERATIONS:
            d = Driver(body(op, True))
            with self.assertRaises(ValueError):
                d.submit_player_pilgrimage_planner_private_v1(
                    expected_revision=5, operation=op, province_id=12 if op in {"select", "start"} else 0)
            self.assertEqual(d.sent, [])
        cases = [
            {"operation": "start", "province_id": 0}, {"operation": "select", "province_id": 0},
            {"operation": "open", "province_id": 1}, {"operation": "confirm", "reserve_gold_raw": 1},
            {"operation": "start", "province_id": 5, "reserve_piety_raw": -1},
            {"operation": "start", "province_id": 5, "reserve_gold_raw": 2**63},
            {"operation": "start", "province_id": 5, "reserve_gold_raw": True},
        ]
        for options in cases:
            d = Driver(body(options["operation"], True))
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    d.submit_player_pilgrimage_planner_private_v1(
                        expected_revision=5, policy_positive=True, **options)
                self.assertEqual(d.sent, [])

    def test_each_submit_sends_once_and_preserves_rejection_without_success_credit(self):
        for op in T.SUBMIT_OPERATIONS:
            value = body(op, True)
            value.update(operation_status="rejected", failure="native_precondition_failed")
            d = Driver(value)
            result = d.submit_player_pilgrimage_planner_private_v1(
                expected_revision=5, operation=op, policy_positive=True,
                province_id=3 if op in {"select", "start"} else 0)
            self.assertEqual(len(d.sent), 1)
            self.assertEqual(result["operation_status"], "rejected")
            self.assertFalse(result["business_outcome_observed"])

    def test_start_invoked_allows_wallet_revision_postchange_without_claiming_payment(self):
        value = body("start", True)
        value.update(invoked=True, operation_status="submitted_pending", ledger_state="submitted_pending")
        d = Driver(value)
        d.after = snapshot(6, 5)
        d.after["played_character_gold"]["raw"] -= 10000000
        result = d.submit_player_pilgrimage_planner_private_v1(
            expected_revision=5, operation="start", province_id=3, policy_positive=True,
            reserve_gold_raw=4000000)
        self.assertEqual(result["operation_status"], "submitted_pending")
        self.assertFalse(result["business_outcome_observed"])
        self.assertFalse(result["action_ready"])
        self.assertEqual(d.sent[0]["reserve_gold_raw"], 4000000)
        self.assertEqual(len(d.sent), 1)

    def test_queries_nonstart_and_noninvoked_start_reject_changed_frame(self):
        for op, submit in (("read", False), ("open", True), ("start", True)):
            d = Driver(body(op, submit))
            d.after = snapshot(6, 5)
            with self.subTest(op=op):
                with self.assertRaises(BridgeUnavailableError):
                    if submit:
                        d.submit_player_pilgrimage_planner_private_v1(
                            expected_revision=5, operation=op, province_id=3 if op == "start" else 0,
                            policy_positive=True)
                    else:
                        d.query_player_pilgrimage_planner_private_v1(expected_revision=5)
                self.assertEqual(len(d.sent), 1)

    def test_start_never_allows_actor_day_pid_generation_or_build_drift(self):
        changes = [
            lambda s: s["played_character"].update(character_id=55),
            lambda s: s.update(date_raw=53144352),
            lambda s: s["diagnostics"]["hello"].update(pid=4321),
            lambda s: s["diagnostics"].update(connection_generation=9),
            lambda s: s["diagnostics"]["hello"].update(expected_ck3_version="1.20.0.3"),
        ]
        for change in changes:
            value = body("start", True)
            value.update(invoked=True, operation_status="submitted_pending", ledger_state="submitted_pending")
            d = Driver(value)
            change(d.after)
            with self.assertRaises(BridgeUnavailableError):
                d.submit_player_pilgrimage_planner_private_v1(
                    expected_revision=5, operation="start", province_id=3, policy_positive=True)
            self.assertEqual(len(d.sent), 1)

    def test_bad_correlation_envelope_failure_and_null_failure_remain_errors_without_retry(self):
        changes = [
            lambda f: f.update(request_id="foreign"), lambda f: f.update(ok=False),
            lambda f: f["result"].update(accepted=False), lambda f: f["result"].update(status="success"),
            lambda f: f["result"]["player_pilgrimage_planner"].update(played_character_id=8),
            lambda f: f["result"]["player_pilgrimage_planner"].update(failure=None),
            lambda f: f["result"]["player_pilgrimage_planner"].update(raw_pointer_fields_persisted=True),
            lambda f: f["result"]["player_pilgrimage_planner"].update(invoked=True),
        ]
        for change in changes:
            d = Driver()
            d.corrupt = change
            with self.assertRaises(BridgeUnavailableError):
                d.query_player_pilgrimage_planner_private_v1(expected_revision=5)
            self.assertEqual(len(d.sent), 1)

    def test_quote_rejects_wrong_shapes_frame_mask_and_unknown_positive_contradictions(self):
        good = quote()
        self.assertEqual(T.normalize_pilgrimage_quote_v1(good, source=snapshot()), good)
        changes = [
            lambda q: q["configured_cost_raw"].pop(),
            lambda q: q["diagnostic_aggregate_raw"].__setitem__(0, True),
            lambda q: q["known_name_resource_indices"].__setitem__(1, 0),
            lambda q: q["named_cost_verified"].__setitem__(1, True),
            lambda q: q.update(unknown_positive_configured_cost=True),
            lambda q: q.update(date_raw=53144329), lambda q: q.update(snapshot_revision=True),
            lambda q: q["selected_option"].update(key="feast_type_generic"),
            lambda q: q.update(failure_display_known=True), lambda q: q.update(application_main_thread=False),
        ]
        for change in changes:
            q = quote()
            change(q)
            with self.assertRaises(BridgeUnavailableError):
                T.normalize_pilgrimage_quote_v1(q, source=snapshot())
        unknown = quote()
        unknown["configured_cost_raw"][1] = 10
        unknown["unknown_positive_configured_cost"] = True
        self.assertTrue(T.normalize_pilgrimage_quote_v1(unknown, source=snapshot())["unknown_positive_configured_cost"])

    def test_post_full_generation_identity_preserves_unknown_terminal_fields(self):
        value = body("post")
        value.update(operation_status="identity_observed", ledger_state="identity_observed")
        value["new_identity"] = {
            "activity_id": 0xFE000123, "host_character_id": 31254, "type_key": "activity_pilgrimage",
            "terminal_flags_observed": False, "native_completed": None, "native_invalidated": None,
            "native_completion_stamp_observed": False, "native_completion_stamp_raw": None,
        }
        result = Driver(value).query_player_pilgrimage_planner_private_v1(expected_revision=5, operation="post")
        self.assertEqual(result["new_identity"]["activity_id"], 0xFE000123)
        self.assertIsNone(result["new_identity"]["native_completed"])
        self.assertFalse(result["absence_is_completion"])
        bad = deepcopy(value)
        bad["new_identity"]["host_character_id"] = 1
        with self.assertRaises(BridgeUnavailableError):
            Driver(bad).query_player_pilgrimage_planner_private_v1(expected_revision=5, operation="post")

    def test_unknown_and_recovery_states_are_retained_not_resubmitted(self):
        for status, ledger in (("submission_outcome_unknown", "submission_outcome_unknown"),
                               ("needs_recovery", "submitted_pending"), ("ambiguous", "submitted_pending")):
            value = body("post")
            value.update(operation_status=status, ledger_state=ledger, needs_recovery=True,
                         failure="inspect_native_process_ledger")
            d = Driver(value)
            result = d.query_player_pilgrimage_planner_private_v1(expected_revision=5, operation="post")
            self.assertEqual(result["operation_status"], status)
            self.assertEqual(len(d.sent), 1)
            self.assertFalse(result["automatic_retry"])


class RegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_identity_declared_does_not_register_execution_and_explicit_flag_adds_exactly_two(self):
        from mcp import Client
        disabled = Driver(enabled=False)
        disabled.allow_private_player_pilgrimage_activities_query = True
        disabled.case_declared_read_only_mcp_tools = {"ck3_query_player_pilgrimage_activities_v1",
                                                    "ck3_query_player_pilgrimage_planner_v1"}
        async with Client(create_server(disabled)) as client:
            before = {t.name for t in (await client.list_tools()).tools}
        self.assertNotIn("ck3_query_player_pilgrimage_planner_v1", before)
        self.assertNotIn("ck3_submit_player_pilgrimage_planner_v1", before)
        enabled = Driver()
        enabled.allow_private_player_pilgrimage_activities_query = True
        async with Client(create_server(enabled)) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            self.assertEqual(set(tools) - before, {"ck3_query_player_pilgrimage_planner_v1",
                                                  "ck3_submit_player_pilgrimage_planner_v1"})
            self.assertTrue(tools["ck3_query_player_pilgrimage_planner_v1"].annotations.read_only_hint)
            self.assertFalse(tools["ck3_submit_player_pilgrimage_planner_v1"].annotations.read_only_hint)
            result = await client.call_tool("ck3_query_player_pilgrimage_planner_v1", {"expected_revision": 5})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["activity_type_key"], "activity_pilgrimage")
            bad = await client.call_tool("ck3_query_player_pilgrimage_planner_v1",
                                        {"expected_revision": 5, "activity_type_key": "activity_feast"})
            self.assertTrue(bad.is_error)
        self.assertEqual(len(enabled.sent), 1)

    async def test_registered_submit_rejects_false_policy_and_forwards_one_pending_start(self):
        from mcp import Client
        value = body("start", True)
        value.update(invoked=True, operation_status="submitted_pending", ledger_state="submitted_pending")
        d = Driver(value)
        async with Client(create_server(d)) as client:
            bad = await client.call_tool("ck3_submit_player_pilgrimage_planner_v1",
                                        {"expected_revision": 5, "operation": "start", "province_id": 3})
            self.assertTrue(bad.is_error)
            self.assertEqual(d.sent, [])
            result = await client.call_tool("ck3_submit_player_pilgrimage_planner_v1",
                                           {"expected_revision": 5, "operation": "start",
                                            "province_id": 3, "policy_positive": True})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["operation_status"], "submitted_pending")
            self.assertFalse(result.structured_content["business_outcome_observed"])
        self.assertEqual(len(d.sent), 1)



class RealServerCliTests(unittest.TestCase):
    @staticmethod
    def module():
        import importlib
        return importlib.import_module("xar_autoplayer.bridge.mcp_server")

    def run_main(self, extra=(), *, identity=True):
        from unittest.mock import Mock, patch
        module = self.module()
        d = Driver(enabled=False)
        d.allow_private_player_pilgrimage_activities_query = identity
        d.case_declared_read_only_mcp_tools = {
            "ck3_query_player_pilgrimage_activities_v1",
            "ck3_query_player_pilgrimage_planner_v1",
        }
        d.close = Mock()
        server = Mock()
        with patch.object(module, "load_driver", return_value=d) as load, \
             patch.object(module, "create_server", return_value=server) as create:
            result = module.main(["--driver", "native-headless", "--transport", "stdio",
                                  "--state-dir", "synthetic-unused-state", *extra])
        self.assertEqual(result, 0)
        load.assert_called_once()
        self.assertIs(create.call_args.args[0], d)
        server.run.assert_called_once_with(transport="stdio")
        d.close.assert_called_once_with()
        self.assertEqual(d.sent, [])
        return d

    def test_parser_default_off_and_only_explicit_new_switch_on(self):
        module = self.module()
        self.assertIs(module.parser().parse_args([]).allow_private_player_pilgrimage_execution, False)
        self.assertIs(module.parser().parse_args([
            "--allow-private-player-pilgrimage-execution"
        ]).allow_private_player_pilgrimage_execution, True)
        self.assertIs(module.parser().parse_args([
            "--private-activity-feast-queries", "--allow-private-activity-feast-normal"
        ]).allow_private_player_pilgrimage_execution, False)

    def test_main_default_does_not_promote_identity_or_case_permission(self):
        d = self.run_main()
        self.assertIs(d.allow_private_player_pilgrimage_execution, False)
        self.assertIs(d.allow_private_player_pilgrimage_activities_query, True)

    def test_main_old_feast_permissions_do_not_enable_pilgrimage_execution(self):
        d = self.run_main(["--private-activity-feast-queries",
                           "--allow-private-activity-feast-normal"])
        self.assertIs(d.allow_private_player_pilgrimage_execution, False)
        self.assertIs(d.allow_private_activity_feast_stage5_start_action, True)

    def test_main_only_explicit_new_switch_enables_execution(self):
        d = self.run_main(["--allow-private-player-pilgrimage-execution"], identity=False)
        self.assertIs(d.allow_private_player_pilgrimage_execution, True)
        self.assertIs(d.allow_private_player_pilgrimage_activities_query, False)
        self.assertFalse(getattr(d, "allow_private_activity_feast_stage5_start_action", False))

    def test_main_rejects_other_driver_or_transport_before_loading(self):
        from unittest.mock import patch
        module = self.module()
        for args in (["--driver", "mock", "--transport", "stdio"],
                     ["--driver", "native-headless", "--transport", "streamable-http"]):
            with self.subTest(args=args), patch.object(module, "load_driver") as load:
                with self.assertRaisesRegex(ValueError, "native-headless stdio"):
                    module.main([*args, "--allow-private-player-pilgrimage-execution"])
                load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
