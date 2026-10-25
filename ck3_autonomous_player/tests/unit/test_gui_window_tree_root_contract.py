"""Fixed native root identity must survive generic validation projection."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1

import ast
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock, patch
from mcp import Client
from xar_autoplayer.bridge import gui_window_tree_contract as contract, mcp_server
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004


def scripted_frame() -> dict[str, object]:
    return {"revision": 9007199254740993, "native_revision": 9007199254740995,
            "snapshot_id": "synthetic-scripted-widget-frame", "episode_run_id": "synthetic-widget-episode",
            "paused": True, "map_ready": True, "date_raw": 1234,
            "played_character": {"character_id": 7001, "alive": True},
            "diagnostics": {"connection_generation": 9007199254740997, "hello": {
                "pid": 12700, "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version": CK3_12004.game_version, "expected_ck3_sha256": CK3_12004.executable_sha256}}}


def actual_campaign_frame() -> dict[str, object]:
    path = Path(__file__).resolve().parents[1] / "fixtures/scripted_widget_native_campaign_R0003_snapshot.json"
    fixture = contract.scripted_widget_object_v1(json.loads(path.read_text(encoding="utf-8")))
    return contract.scripted_widget_object_v1(fixture["snapshot"])


def actual_R0007_owner_samples() -> tuple[dict[str, object], dict[str, object]]:
    path = Path(__file__).resolve().parents[1] / "fixtures/scripted_widget_owner_sampling_R0007.json"
    fixture = contract.scripted_widget_object_v1(json.loads(path.read_text(encoding="utf-8")))
    samples = fixture["samples"]
    if not isinstance(samples, list) or len(samples) != 2:
        raise ValueError("Two original R0007 owner samples required")
    frames = []
    for row in samples:
        sample = contract.scripted_widget_object_v1(row)
        frame = deepcopy(contract.scripted_widget_object_v1(fixture["snapshot"]))
        diagnostics = contract.scripted_widget_object_v1(frame["diagnostics"])
        diagnostics["last_heartbeat"] = sample["heartbeat"]
        frame["diagnostics"] = diagnostics
        frames.append(frame)
    return frames[0], frames[1]


def scripted_query(binding: contract.ScriptedWidgetBindingV1, generation: str = "9007199254740999") -> dict[str, object]:
    return {"schema": "ck3-native-scripted-widget-controls-v1", "step": contract.SCRIPTED_WIDGET_QUERY_STEP,
            **{key: binding[key] for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw")},
            "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
            "owner_thread_verified": True, "source_abi_pins_verified": True, "frame_verified": True,
            "available": True, "unavailable_reason": "", "root_name": "custom_actual_window",
            "query_generation": generation, "complete": True, "truncated": False,
            "widgets": [
                {"widget_id": "1", "runtime_name": "custom_actual_window", "child_path": "", "vtable_rva": 123,
                 "effective_visible": True, "enabled": True, "clickable": False},
                {"widget_id": "9007199254741001", "runtime_name": "confirm", "child_path": "0/2/1", "vtable_rva": 456,
                 "effective_visible": True, "enabled": True, "clickable": True}]}


def scripted_action(binding: contract.ScriptedWidgetBindingV1, generation: str = "9007199254740999") -> dict[str, object]:
    raw = scripted_query(binding, generation)
    for key in ("widgets", "complete", "truncated"):
        del raw[key]
    raw.update(schema="ck3-native-scripted-widget-control-action-v1", step=contract.SCRIPTED_WIDGET_ACTION_STEP,
               widget_id="9007199254741001", dispatch_attempted=True, dispatch_invoked=True,
               native_handled=True, verification_pending=True, postcondition_verified=False)
    return raw


class ScriptedWidgetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="xar-scripted-widget-tests-")
        self.addCleanup(self.temp.cleanup)
        self.frame = scripted_frame()
        self.binding = contract.scripted_widget_binding_v1(self.frame)
        self.generation = 9007199254740999
        self.native_action = scripted_action(self.binding)
        self.driver = object.__new__(NativeHeadlessGameplayDriver)
        self.driver.take_snapshot = Mock(side_effect=lambda: deepcopy(self.frame))
        self.driver._native_driver_state_path = Mock(return_value=Path(self.temp.name) / "driver-state.json")
        self.driver._record_command = Mock()
        self.driver._execute_primitive_step = Mock(side_effect=self.execute)

    def execute(self, step: str, **arguments: object) -> dict[str, object]:
        if step == contract.SCRIPTED_WIDGET_QUERY_STEP:
            return scripted_query(contract.scripted_widget_binding_v1(self.frame), str(self.generation))
        if step == contract.SCRIPTED_WIDGET_ACTION_STEP:
            return deepcopy(self.native_action)
        raise AssertionError(step)

    def query(self) -> contract.ScriptedWidgetQueryV1:
        return self.driver.query_scripted_widget_controls_v1("custom_actual_window", expected_revision=self.frame["revision"])

    def activate(self) -> contract.ScriptedWidgetActionV1:
        return self.driver.activate_scripted_widget_control_v1(str(self.generation), "9007199254741001", expected_revision=self.frame["revision"])

    def use_actual_campaign(self) -> None:
        self.frame = actual_campaign_frame()
        self.binding = contract.scripted_widget_binding_v1(self.frame)
        self.native_action = scripted_action(self.binding, str(self.generation))

    def test_actual_R0007_owner_samples_stabilize_before_one_action_claim(self) -> None:
        pending, self.frame = actual_R0007_owner_samples()
        self.binding = contract.scripted_widget_binding_v1(self.frame)
        self.native_action = scripted_action(self.binding, str(self.generation))
        with self.assertRaisesRegex(ValueError, "current verified application owner"):
            contract.scripted_widget_binding_v1(pending)
        self.query()
        self.driver._execute_primitive_step.reset_mock()
        self.driver.take_snapshot = Mock(side_effect=[pending, deepcopy(self.frame)])
        with patch("xar_autoplayer.bridge.native_driver.time.sleep") as sleep:
            result = self.activate()
        self.assertTrue(result["dispatch_invoked"])
        self.assertEqual(sleep.call_count, 1)
        self.assertEqual(self.driver.take_snapshot.call_count, 2)
        self.driver._execute_primitive_step.assert_called_once()
        self.assertEqual(len(list(Path(self.temp.name).glob("scripted-widget-controls/*.claim.json"))), 1)

    def test_owner_sampling_is_bounded_and_never_claims_or_dispatches_when_unstable(self) -> None:
        pending, self.frame = actual_R0007_owner_samples()
        self.binding = contract.scripted_widget_binding_v1(self.frame)
        self.native_action = scripted_action(self.binding, str(self.generation))
        self.query()
        self.driver._execute_primitive_step.reset_mock()
        self.driver.take_snapshot = Mock(side_effect=lambda: deepcopy(pending))
        with patch("xar_autoplayer.bridge.native_driver.time.sleep") as sleep:
            with self.assertRaisesRegex(BridgeUnavailableError, "bounded read limit"):
                self.activate()
        self.assertEqual(self.driver.take_snapshot.call_count, 8)
        self.assertEqual(sleep.call_count, 7)
        self.driver._execute_primitive_step.assert_not_called()
        self.assertFalse(list(Path(self.temp.name).glob("scripted-widget-controls/*.claim.json")))

    def test_owner_sampling_rejects_frame_and_owner_drift_before_dispatch(self) -> None:
        pending, stable = actual_R0007_owner_samples()
        for defect in ("revision", "date_raw", "played_character", "bridge_pid", "pipe_name", "owner_tid"):
            with self.subTest(defect=defect):
                later = deepcopy(stable)
                if defect == "revision": later[defect] = 11
                elif defect == "date_raw": later[defect] = 53144376
                elif defect == "played_character": later[defect] = {"character_id": 99, "alive": True, "source": "native"}
                else:
                    diagnostics = contract.scripted_widget_object_v1(later["diagnostics"])
                    if defect == "owner_tid":
                        heartbeat = contract.scripted_widget_object_v1(diagnostics["last_heartbeat"])
                        mailbox = contract.scripted_widget_object_v1(heartbeat["main_thread_query_mailbox_v1"])
                        mailbox["owner_tid"] = 99
                        heartbeat["main_thread_query_mailbox_v1"] = mailbox
                        diagnostics["last_heartbeat"] = heartbeat
                    else: diagnostics[defect] = 99 if defect == "bridge_pid" else "other-pipe"
                    later["diagnostics"] = diagnostics
                self.driver.take_snapshot = Mock(side_effect=[deepcopy(pending), later])
                with patch("xar_autoplayer.bridge.native_driver.time.sleep"):
                    with self.assertRaisesRegex(BridgeUnavailableError, "crossed its original paused frame"):
                        self.driver._scripted_widget_stable_frame_v1()
                self.driver._execute_primitive_step.assert_not_called()

    def test_owner_sampling_does_not_relax_other_owner_failures_or_repeat_query(self) -> None:
        pending, self.frame = actual_R0007_owner_samples()
        self.binding = contract.scripted_widget_binding_v1(self.frame)
        for key, value in (("owner_tid", 99), ("owner_verified_pump_epochs", 1), ("stamp_read_success", False)):
            broken = deepcopy(pending)
            diagnostics = contract.scripted_widget_object_v1(broken["diagnostics"])
            heartbeat = contract.scripted_widget_object_v1(diagnostics["last_heartbeat"])
            mailbox = contract.scripted_widget_object_v1(heartbeat["main_thread_query_mailbox_v1"])
            mailbox[key] = value
            heartbeat["main_thread_query_mailbox_v1"] = mailbox
            diagnostics["last_heartbeat"] = heartbeat
            broken["diagnostics"] = diagnostics
            self.driver.take_snapshot = Mock(return_value=broken)
            with patch("xar_autoplayer.bridge.native_driver.time.sleep") as sleep:
                with self.assertRaises(ValueError): self.query()
            sleep.assert_not_called()
            self.driver._execute_primitive_step.assert_not_called()
        # A transient ending observation permits only new reads, not a second primitive.
        self.driver.take_snapshot = Mock(side_effect=[deepcopy(self.frame), pending, deepcopy(self.frame)])
        with patch("xar_autoplayer.bridge.native_driver.time.sleep"):
            self.query()
        self.driver._execute_primitive_step.assert_called_once()

    def assert_unknown_in_independent_process(self) -> None:
        import subprocess
        check = """import sys,json
from pathlib import Path
from unittest.mock import Mock
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
directory=Path(sys.argv[1]); frame=json.loads(sys.argv[2])
driver=object.__new__(NativeHeadlessGameplayDriver)
driver.take_snapshot=Mock(return_value=frame)
driver._native_driver_state_path=Mock(return_value=directory/'driver-state.json')
driver._execute_primitive_step=Mock(side_effect=AssertionError('must not dispatch'))
try: driver.activate_scripted_widget_control_v1(sys.argv[3],'9007199254741001',expected_revision=frame['revision'])
except BridgeUnavailableError as error:
 assert 'unknown' in str(error),str(error)
else: raise AssertionError('unknown action replayed')
driver._execute_primitive_step.assert_not_called()
"""
        completed = subprocess.run([sys.executable, "-c", check, self.temp.name, json.dumps(self.frame), str(self.generation)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    async def test_actual_R0003_campaign_snapshot_reaches_mcp_without_fabricating_episode(self) -> None:
        """Real failed-run snapshot; primitive response is the named test fixture, not a live query."""
        self.use_actual_campaign()
        self.assertNotIn("episode_run_id", self.frame)
        self.assertIsNone(self.binding["episode_run_id"])
        self.assertEqual(self.binding["played_character_id"], 31254)
        self.assertEqual(self.binding["scope"]["kind"], "managed_native_campaign")
        self.assertEqual(self.binding["scope"]["run_binding"], self.frame["managed_campaign_run_binding"])
        async with Client(mcp_server.create_server(self.driver)) as client:
            observed = await client.session.call_tool("ck3_query_scripted_widget_controls_v1", {
                "root_name": "custom_actual_window", "expected_revision": "7"})
            self.assertFalse(observed.is_error, str(observed))
            result = await client.session.call_tool("ck3_activate_scripted_widget_control_v1", {
                "query_generation": str(self.generation), "widget_id": "9007199254741001", "expected_revision": "7"})
            self.assertFalse(result.is_error, str(result))
            self.assertFalse(result.structured_content["postcondition_verified"])
        self.assertNotIn("episode_run_id", self.frame)
        self.assertEqual(self.driver._execute_primitive_step.call_count, 2)

    def test_campaign_requires_complete_actual_run_and_nullable_episode_only_in_campaign(self) -> None:
        original = actual_campaign_frame()
        for mutation in ("missing_run", "extra_field", "missing_field", "empty_run", "bool_run", "wrong_pipe",
                         "nonnull_episode", "wrong_projection", "wrong_backend", "missing_episode_projection"):
            with self.subTest(mutation=mutation):
                frame = deepcopy(original)
                if mutation == "missing_run": del frame["managed_campaign_run_binding"]
                elif mutation == "extra_field": frame["managed_campaign_run_binding"]["extra"] = "x"
                elif mutation == "missing_field": del frame["managed_campaign_run_binding"]["state_dir"]
                elif mutation == "empty_run": frame["managed_campaign_run_binding"]["run_id"] = ""
                elif mutation == "bool_run": frame["managed_campaign_run_binding"]["run_id"] = True
                elif mutation == "wrong_pipe": frame["managed_campaign_run_binding"]["bridge_pipe"] = "different-pipe"
                elif mutation == "nonnull_episode": frame["episode_run_id"] = "manufactured-episode"
                elif mutation == "wrong_projection": frame["episode_projection"] = "one_life"
                elif mutation == "wrong_backend": frame["backend_id"] = "mock"
                else: del frame["episode_projection"]
                with self.assertRaises(ValueError): contract.scripted_widget_binding_v1(frame)
        for episode in (None, "", True):
            frame = scripted_frame(); frame["episode_run_id"] = episode
            with self.assertRaises(ValueError): contract.scripted_widget_binding_v1(frame)

    def test_campaign_saved_query_requires_same_full_managed_binding(self) -> None:
        for field in ("run_id", "state_dir", "bridge_pipe", "host_path", "frozen_argv_sha256"):
            with self.subTest(field=field):
                self.use_actual_campaign(); self.generation += 1
                self.query()
                run = self.frame["managed_campaign_run_binding"]
                run[field] = "a" * 64 if field == "frozen_argv_sha256" else run[field] + "-changed"
                if field == "bridge_pipe": self.frame["diagnostics"]["pipe_name"] = run[field]
                with self.assertRaisesRegex(BridgeUnavailableError, "saved query"): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 5)

    def test_campaign_query_ending_requires_same_managed_run(self) -> None:
        self.use_actual_campaign()
        ending = deepcopy(self.frame)
        ending["managed_campaign_run_binding"]["run_id"] += "-changed"
        self.driver.take_snapshot = Mock(side_effect=[deepcopy(self.frame), ending])
        with self.assertRaisesRegex(BridgeUnavailableError, "paused frame"): self.query()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 1)

    def test_campaign_unknown_survives_run_transport_changes_and_independent_process(self) -> None:
        self.use_actual_campaign(); self.query()
        self.native_action.update(available=False, unavailable_reason="native_invocation_result_unknown",
                                  dispatch_invoked=False, native_handled=False)
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        run = self.frame["managed_campaign_run_binding"]
        run["run_id"] += "-successor"
        run["host_path"] += "-successor"
        run["frozen_argv_sha256"] = "a" * 64
        # Equivalent Windows spelling must not turn UNKNOWN into a fresh intent.
        run["state_dir"] = run["state_dir"].upper() + "\\."
        self.frame["diagnostics"]["connection_generation"] += 1
        self.frame["diagnostics"]["hello"]["connection_generation"] += 1
        self.generation += 1; self.query()
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 3)
        self.assert_unknown_in_independent_process()

    def test_strict_wire_and_json_roundtrip_preserve_provider_identity(self) -> None:
        result = self.query()
        self.assertEqual(contract.normalize_scripted_widget_query_v1(json.loads(json.dumps(result)), "custom_actual_window"), result)
        public = contract.scripted_widget_public_result_v1(result)
        self.assertEqual(public["native_revision"], "9007199254740995")
        self.assertEqual(public["connection_generation"], "9007199254740997")
        self.assertEqual(public["query_generation"], "9007199254740999")
        for bad in (True, 1, 1.0, "01", "1.0", "0", str(2**64), None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                contract.scripted_widget_decimal_v1(bad)
        for key, bad in (("native_revision", True), ("connection_generation", 1.0), ("frame_verified", 1),
                         ("game_version", "1.20.0.3"), ("widgets", None), ("complete", False)):
            raw = scripted_query(self.binding); raw[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                contract.normalize_scripted_widget_query_v1(raw, "custom_actual_window", self.binding)
        for key in ("query_generation", "widgets", "native_revision", "root_name"):
            raw = scripted_query(self.binding); del raw[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                contract.normalize_scripted_widget_query_v1(raw, "custom_actual_window")
        for bad in ("", "x y", "../root", "x" * 129):
            with self.assertRaises(ValueError): contract.scripted_widget_root_v1(bad)

    def test_actual_cpp_serializer_outputs_reach_shared_contract(self) -> None:
        """CI supplies its just-built reducer test executable, never a stored JSON substitute."""
        import subprocess
        executable = os.environ.get("XAR_SCRIPTED_WIDGET_NATIVE_TEST_EXE")
        if not executable:
            self.skipTest("native producer executable not supplied; this cross-language check was not executed")
        completed = subprocess.run([executable, "--wire-fixtures"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        packets = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(packets), 3)
        query = contract.normalize_scripted_widget_query_v1(packets[0], "custom_mod_window")
        self.assertTrue(query["available"])
        self.assertEqual(query["native_revision"], 17)
        for index in (1, 2):
            packet = contract.scripted_widget_object_v1(packets[index])
            result = contract.normalize_scripted_widget_action_v1(packet,
                contract.scripted_widget_decimal_v1(packet.get("query_generation")),
                contract.scripted_widget_decimal_v1(packet.get("widget_id")))
            self.assertFalse(result["postcondition_verified"])
            self.assertTrue(result["dispatch_attempted"])
            self.assertEqual(result["dispatch_invoked"], index == 1)

    def test_actual_root_paths_and_clickability_are_required(self) -> None:
        for mutation in ("wrong_root", "duplicate_path", "pointer", "invisible", "disabled", "not_clickable"):
            with self.subTest(mutation=mutation):
                raw = scripted_query(self.binding)
                if mutation == "wrong_root": raw["widgets"][0]["runtime_name"] = "other_root"
                elif mutation == "duplicate_path": raw["widgets"][1]["child_path"] = ""
                elif mutation == "pointer": raw["widgets"][1]["widget_id"] = 123
                else: raw["widgets"][1][{"invisible": "effective_visible", "disabled": "enabled", "not_clickable": "clickable"}[mutation]] = False
                if mutation in {"wrong_root", "duplicate_path", "pointer"}:
                    with self.assertRaises(ValueError): contract.normalize_scripted_widget_query_v1(raw, "custom_actual_window")
                else:
                    result = contract.normalize_scripted_widget_query_v1(raw, "custom_actual_window", self.binding)
                    result["public_revision"] = str(self.frame["revision"])
                    path = Path(self.temp.name) / "scripted-widget-controls" / f"query-12700-9007199254740997-{self.generation}.json"
                    contract.write_scripted_widget_evidence_v1(path, {"binding": self.binding, "query": result})
                    with self.assertRaises(BridgeUnavailableError): self.activate()
                    path.unlink()
        self.driver._execute_primitive_step.assert_not_called()

    def test_real_driver_service_routes_once_and_does_not_claim_business_completion(self) -> None:
        service = GameplayBridgeService(self.driver)
        query = service.query_scripted_widget_controls_v1("custom_actual_window", expected_revision=self.frame["revision"])
        result = service.activate_scripted_widget_control_v1(query["query_generation"], "9007199254741001", expected_revision=self.frame["revision"])
        self.assertTrue(result["dispatch_invoked"])
        self.assertFalse(result["postcondition_verified"])
        self.assertTrue(result["verification_pending"])
        sent = self.driver._execute_primitive_step.call_args
        self.assertEqual(sent.kwargs["expected_revision"], 9007199254740993)
        self.assertEqual(sent.kwargs["request_fields"], {"query_generation": "9007199254740999", "widget_id": "9007199254741001",
            "expected_player_character_id": 7001, "expected_game_pid": 12700, "expected_connection_generation": 9007199254740997})
        with self.assertRaisesRegex(BridgeUnavailableError, "consumed"): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 2)

    def test_later_fresh_query_allows_new_intent_after_known_native_dispatch(self) -> None:
        self.query(); self.activate()
        self.generation += 1
        self.query()
        self.native_action = scripted_action(self.binding, str(self.generation))
        result = self.activate()
        self.assertTrue(result["dispatch_invoked"])
        self.assertFalse(result["postcondition_verified"])
        self.assertEqual(self.driver._execute_primitive_step.call_count, 4)

    def test_unknown_blocks_new_query_and_reconnect_and_survives_independent_process(self) -> None:
        self.query()
        self.native_action.update(available=False, unavailable_reason="native_invocation_result_unknown",
                                  dispatch_invoked=False, native_handled=False)
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        self.frame["diagnostics"]["connection_generation"] += 1
        self.generation += 1
        self.query()
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 3)
        self.assert_unknown_in_independent_process()

    def test_lost_ack_or_malformed_ack_never_becomes_repeatable(self) -> None:
        self.query()
        self.driver._execute_primitive_step.side_effect = TimeoutError("lost acknowledgement")
        with self.assertRaises(TimeoutError): self.activate()
        self.driver._execute_primitive_step.side_effect = self.execute
        self.generation += 1; self.query()
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        self.assertEqual(len(list((Path(self.temp.name) / "scripted-widget-controls").glob("*.dispatch.json"))), 0)

    def test_malformed_native_ack_retains_unknown_claim(self) -> None:
        self.query()
        self.native_action["postcondition_verified"] = True
        with self.assertRaisesRegex(ValueError, "business postcondition"): self.activate()
        self.generation += 1; self.query()
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown"): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 3)

    def test_unobserved_or_stale_identity_rejected_before_native_submission(self) -> None:
        with self.assertRaises(BridgeUnavailableError): self.activate()
        self.driver._execute_primitive_step.assert_not_called()
        self.query()
        self.frame["date_raw"] += 1
        with self.assertRaises(BridgeUnavailableError): self.activate()
        self.assertEqual(self.driver._execute_primitive_step.call_count, 1)

    async def test_actual_mcp_factory_rejects_numbers_aliases_and_unknown_arguments(self) -> None:
        server = mcp_server.create_server(self.driver)
        async with Client(server) as client:
            tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
            name = "ck3_query_scripted_widget_controls_v1"
            self.assertEqual(tools[name].input_schema["properties"]["expected_revision"]["type"], "string")
            for extra in ({"expected_revision": 9007199254740993}, {"expected_revision": True},
                          {"expected_revision": "09007199254740993"}, {"expected_revision": str(2**64)},
                          {"expected_revision": "9007199254740993", "pointer": "123"}):
                args = {"root_name": "custom_actual_window", **extra}
                result = await client.session.call_tool(name, args)
                self.assertTrue(result.is_error, str(result))
            self.driver._execute_primitive_step.assert_not_called()
            observed = await client.session.call_tool(name, {"root_name": "custom_actual_window", "expected_revision": "9007199254740993"})
            self.assertFalse(observed.is_error, str(observed))
            self.assertEqual(observed.structured_content["native_revision"], "9007199254740995")
            action_name = "ck3_activate_scripted_widget_control_v1"
            base = {"query_generation": "9007199254740999", "widget_id": "9007199254741001", "expected_revision": "9007199254740993"}
            for field in ("query_generation", "widget_id", "expected_revision"):
                result = await client.session.call_tool(action_name, {**base, field: int(base[field])})
                self.assertTrue(result.is_error)
            self.assertEqual(self.driver._execute_primitive_step.call_count, 1)
            action = await client.session.call_tool(action_name, base)
            self.assertFalse(action.is_error, str(action))
            self.assertFalse(action.structured_content["postcondition_verified"])
            replay = await client.session.call_tool(action_name, base)
            self.assertTrue(replay.is_error)
            self.assertEqual(self.driver._execute_primitive_step.call_count, 2)

    async def test_actual_plan_client_fresh_revision_reaches_registered_tools(self) -> None:
        import argparse
        import importlib.util
        host_path = Path(__file__).resolve().parents[2] / "native_bridge/research/run_ck3_12002_mcp_live.py"
        spec = importlib.util.spec_from_file_location("scripted_widget_actual_host_v1", host_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        async with Client(mcp_server.create_server(self.driver)) as client:
            host = module.PlanClient(client.session, argparse.Namespace(
                output=Path(self.temp.name) / "host-report.json", command_timeout=10,
                frontend_mod_load_observation=False), {"steps": []}, lambda: None)
            host.tools = {tool.name: {"inputSchema": tool.input_schema} for tool in (await client.session.list_tools()).tools}

            async def fresh() -> dict[str, object]:
                host.snapshot = deepcopy(self.frame)
                return host.snapshot

            host.fresh = fresh
            observed = await host.invoke("ck3_query_scripted_widget_controls_v1", {"root_name": "custom_actual_window"})
            self.assertEqual(observed["query_generation"], "9007199254740999")
            result = await host.invoke("ck3_activate_scripted_widget_control_v1", {
                "query_generation": observed["query_generation"], "widget_id": observed["widgets"][1]["widget_id"]})
            self.assertFalse(result["postcondition_verified"])
            self.assertTrue(result["dispatch_invoked"])
            self.assertEqual(self.driver._execute_primitive_step.call_count, 2)
            with self.assertRaises(ValueError):
                await host.invoke("ck3_query_scripted_widget_controls_v1", {
                    "root_name": "custom_actual_window", "expected_revision": 9007199254740993})
            self.assertEqual(self.driver._execute_primitive_step.call_count, 2)

    def test_changed_contract_and_driver_service_mcp_methods_pass_strict_types(self) -> None:
        """Check the whole shared contract and actual changed methods, not legacy bodies."""
        from mypy import api
        base = Path(contract.__file__).parent
        selected = {
            "native_driver.py": {"_scripted_widget_stable_frame_v1", "query_scripted_widget_controls_v1", "activate_scripted_widget_control_v1"},
            "service.py": {"query_scripted_widget_controls_v1", "activate_scripted_widget_control_v1"},
            "mcp_server.py": {"ck3_query_scripted_widget_controls_v1", "ck3_activate_scripted_widget_control_v1"},
        }
        classes = []
        functions = []
        for filename, names in selected.items():
            tree = ast.parse((base / filename).read_text(encoding="utf-8"))
            methods = [deepcopy(node) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names]
            self.assertEqual(len(methods), len(names))
            for method in methods:
                method.decorator_list = []
                for node in ast.walk(method):
                    if isinstance(node, ast.ImportFrom) and node.level:
                        node.module = "xar_autoplayer.bridge." + node.module
                        node.level = 0
            if filename == "mcp_server.py": functions.extend(methods)
            else:
                stubs = ast.parse("""class Checked:
    driver: object
    def take_snapshot(self) -> dict[str, object]: raise RuntimeError
    def _execute_primitive_step(self, step: str, **arguments: object) -> object: raise RuntimeError
    def _native_driver_state_path(self) -> Path: raise RuntimeError
    def _record_command(self, step: str, **arguments: object) -> None: raise RuntimeError
""").body[0]
                stubs.name = "Checked" + filename.split(".")[0].title().replace("_", "")
                stubs.body.extend(methods)
                classes.append(stubs)
        imports = """from __future__ import annotations
from pathlib import Path
import uuid
import time
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError, PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.native_driver import _validate_revision, _same_paused_native_frame
from xar_autoplayer.bridge.gui_window_tree_contract import ScriptedWidgetActionV1, ScriptedWidgetBindingV1, ScriptedWidgetQueryV1, normalize_scripted_widget_action_v1, normalize_scripted_widget_query_v1, scripted_widget_public_result_v1
from xar_autoplayer.bridge.mcp_server import ScriptedWidgetDecimalV1, ScriptedWidgetRootV1
from xar_autoplayer.bridge.service import GameplayBridgeService
service: GameplayBridgeService
"""
        source = imports + ast.unparse(ast.fix_missing_locations(ast.Module(body=classes + functions, type_ignores=[])))
        path = Path(self.temp.name) / "changed_scripted_widget_methods.py"
        path.write_text(source, encoding="utf-8")
        stdout, stderr, status = api.run(["--strict", "--follow-imports=silent", "--no-incremental",
            "--cache-dir=nul", "--python-executable=" + sys.executable,
            "--python-version=" + str(sys.version_info.major) + "." + str(sys.version_info.minor),
            str(Path(contract.__file__)), str(path)])
        self.assertEqual(status, 0, stdout + stderr)

class GuiWindowTreeRootTests(unittest.TestCase):
    def test_wrong_actual_root_row_is_rejected(self):
        raw = {"step": "inspect-gui-window-tree-v1", "accepted": True,
               "status": "available", "scope_root_name": "decisions_view",
               "root_available": True, "truncated": False, "widget_count": 1,
               "widgets": [{"runtime_name": "decisions_view", "child_path": "", "depth": 0,
                            "child_count": 0, "vtable_rva": 1,
                            "effective_visible": True, "enabled": True}]}
        self.assertEqual(normalize_gui_window_tree_v1(raw, "decisions")["scope_root_name"], "decisions_view")
        wrong = deepcopy(raw)
        wrong["widgets"][0]["runtime_name"] = "different_native_window"
        with self.assertRaises(ValueError):
            normalize_gui_window_tree_v1(wrong, "decisions")
