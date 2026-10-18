"""Synthetic transport-only cases through real NativeDriver primitive.

These are not compiled native packets, actual draft eligibility, or live CK3
evidence. They verify revision mapping, diagnostics, retained ACK and no resend.
"""
from __future__ import annotations

from copy import deepcopy
import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import rite_creation_action_private_v1 as action
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.mcp_server import create_server, parser
from mcp import Client, ClientSession

MACHINE = "synthetic-test-machine"
DATE = 12345
ACTOR = 34014
RITE = 26
SOURCE_TEXT_OVERRIDE = None


def unavailable(operation, native_revision=9):
    return {"step": action.STEP, "accepted": True, "status": "unavailable", "private_build": True,
        "advertised": False, "read_only": operation == "preview", "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "backend_id": "ck3-1.20.0.4-native-rite-creation-action-v1",
        "domain_key": action.DOMAIN_KEY, "snapshot_revision": native_revision, "date_raw": DATE,
        action.BODY_KEY: {"schema": action.SCHEMA, "operation": operation, "available": False,
            "unavailable_reason": "synthetic_complete_payload_not_observed",
            "frame": {"connection_generation": 1, "native_revision": native_revision,
                "capture_epoch": 3, "date_raw": DATE, "played_character_id": ACTOR},
            "draft": {"observed": False, "source_rite_id": None, "source_faith_id": None,
                "actor_faith_id": None, "actual_outcome_kind": None, "names": None,
                "selected_core_tenets": None, "selected_doctrines": None},
            "modal": {"observed": False, "stage": "unknown", "kind": None,
                "active": None, "same_draft_window_bound": None, "native_can_accept": None},
            "full_can": {"observed": False, "can_create": None, "can_edit": None,
                "create_reason": None, "edit_reason": None},
            "quote": {"observed": False, "piety_cost_raw": None, "piety_missing_signed_raw": None,
                "has_enough_piety": None, "raw_scale": 100000},
            "preview_identity_available": False, "preview_identity": None,
            "complete_command_payload_observed": False, "native_dispatch_attempted": False,
            "original_writer_inputs_observed": False, "native_command_text_bytes": None,
            "native_command_text_sha256": None,
            "dispatch_invoked": False, "verification_pending": False,
            "original_writer_may_have_been_queued": False, "business_outcome_observed": False,
            "action_id": None}}


def synthetic_preview(native_revision=9, *, stage="confirmation", token="a" * 64):
    raw = unavailable("preview", native_revision)
    raw["status"] = "observed"
    leaf = raw[action.BODY_KEY]
    leaf.update(available=True, unavailable_reason=None, complete_command_payload_observed=True,
        original_writer_inputs_observed=True, native_command_text_bytes=1234, native_command_text_sha256="d" * 64,
        preview_identity_available=True, preview_identity=token)
    leaf["draft"].update(observed=True, source_rite_id=RITE, source_faith_id=27, actor_faith_id=27,
        actual_outcome_kind="create_faith", names={key: "fixture" for key in action.NAME_FIELDS},
        selected_core_tenets=[{"slot_index": 0, "tenet_key": "tenet_christian_syncretism"}],
        selected_doctrines=[{"group_key": "doctrine_pluralism", "doctrine_key": "doctrine_pluralism_pluralistic"}])
    leaf["modal"].update(observed=True, stage=stage, kind="create" if stage == "confirmation" else None,
        active=stage == "confirmation", same_draft_window_bound=stage == "confirmation",
        native_can_accept=stage == "confirmation")
    leaf["full_can"].update(observed=True, can_create=True, can_edit=False)
    leaf["quote"].update(observed=True, piety_cost_raw=100000, piety_missing_signed_raw=0, has_enough_piety=True)
    return raw


def synthetic_context(snapshot, *, rite=RITE, faith=27, main=RITE):
    return {"schema": "ck3_12004_religion_context_v1", "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256, "available": True, "unavailable_reason": None,
        "capture_epoch": snapshot["native_revision"], "date_raw": DATE, "played_character_id": ACTOR,
        "rite_id": rite, "faith_id": faith, "religion_id": 28, "faith_main_rite_id": main,
        "faith_key": "fixture", "religion_key": "fixture", "faith_fervor_raw": None,
        "spiritual_fulfillment_raw": 0, "raw_scale": 100000, "read_only": True,
        "domain_key": "player_religion_context_v1", "backend_id": CK3_12004.backend_id("player-religion-context-v1"),
        "queried_revision": snapshot["revision"], "snapshot_revision": snapshot["native_revision"]}


class Endpoint:
    pipe_name = r"\\.\pipe\synthetic-rite-action-transport-only"
    def __init__(self):
        self.requests = []
        self.timeout = False
        self.known_reject = False
        self.on_send_check = None
    def start(self, on_frame, on_disconnect): self.on_frame = on_frame
    def publish(self, frame): self.on_frame(deepcopy(frame))
    def packet(self, request):
        raw = unavailable(request["operation"], request["expected_revision"])
        if request["operation"] == "confirm_once":
            raw[action.BODY_KEY]["action_id"] = request["action_id"]
            if not self.known_reject:
                raw.update(status="ack_pending")
                raw[action.BODY_KEY].update(available=True, unavailable_reason=None,
                    native_dispatch_attempted=True, dispatch_invoked=True, verification_pending=True,
                    original_writer_may_have_been_queued=True)
        return {"type": "command_result", "protocol_version": 1, "request_id": request["request_id"],
            "ok": True, "result": raw}
    def send(self, request):
        if request.get("type") != "execute_step": return
        self.requests.append(deepcopy(request))
        if self.on_send_check: self.on_send_check(request)
        if not self.timeout: self.publish(self.packet(request))
    def transport_error(self): return None
    def close(self): pass


class RiteCreationAdapterTests(unittest.TestCase):
    transport_summaries = []

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xar-rite-transport-test-")
        self.addCleanup(self.temp.cleanup)
        self.machine_patch = patch.object(action, "_machine_id", return_value=MACHINE)
        self.machine_patch.start()
        self.addCleanup(self.machine_patch.stop)

    def driver(self, native_revision=9):
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            state_dir=Path(self.temp.name), command_timeout_seconds=0.05)
        driver.allow_private_player_rite_creation_actions = True
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "connection_generation": 1, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
            "capabilities": ["game.state.snapshot", action.CAPABILITY]})
        endpoint.snapshot = {"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "synthetic:rite-creation-transport-only", "revision": native_revision,
            "state": {"phase": "map_hud", "date": "synthetic-only", "date_raw": DATE, "speed": 1,
                "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": ACTOR, "alive": True}}}
        endpoint.publish(endpoint.snapshot)
        self.addCleanup(driver.close)
        return driver, endpoint

    def call(self, driver, operation="preview", **fields):
        return action.execute_private_v1(driver, operation=operation,
            expected_revision=driver.take_snapshot_without_native_command_history()["revision"],
            expected_source_rite_id=RITE, **fields)

    def confirm(self, driver, native_revision=9, *, stage="confirmation", token="a" * 64):
        return self.call(driver, "confirm_once", expected_preview_identity=token,
            expected_outcome_kind="create_faith",
            observed_preview=synthetic_preview(native_revision, stage=stage, token=token))

    def test_actual_managed_r0016_binding_uses_allocator_and_keeps_durable_once_scope(self):
        import hashlib
        fixture = Path(__file__).resolve().parents[1] / "fixtures/rite_creation_actions12004/r0016-managed-frame.json"
        record = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(record["machine_id"], "4-8e1c2f1861")
        actual = record["snapshot"]
        original = deepcopy(actual)
        bound = action._binding(actual, actual["revision"])
        self.assertIsNone(bound["episode_run_id"])
        self.assertEqual(actual, original)  # no fake episode or snapshot rewrite
        self.assertEqual(bound["managed_campaign_run_binding"], actual["managed_campaign_run_binding"])
        self.assertEqual(bound["intent_scope"]["kind"], "managed_campaign_state_v1")
        source_rite = 0
        identity = action._intent_identity_v1(bound, source_rite)
        self.assertNotIn("episode_run_id", identity)
        # Counterfactual local inputs test retry safety, not another live scene.
        changed = deepcopy(bound)
        changed["managed_campaign_run_binding"].update(run_id="later-allocated-run", frozen_argv_sha256="a" * 64)
        changed.update(connection_generation=2, native_revision=99, date_raw=bound["date_raw"] + 1)
        self.assertEqual(action._intent_identity_v1(changed, source_rite), identity)
        digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        claim = Path(self.temp.name) / (digest(identity) + ".claim.json")
        with patch.object(action.os, "fsync", wraps=action.os.fsync) as fsync:
            action._save_exclusive(claim, {"identity": identity, "status": "unknown_no_retry"})
            self.assertEqual(fsync.call_count, 1)
        with self.assertRaises(FileExistsError):
            action._save_exclusive(Path(self.temp.name) / (digest(action._intent_identity_v1(changed, source_rite)) + ".claim.json"), {})
        self.assertNotEqual(action._intent_identity_v1(bound, 1), identity)
        legacy = {"episode_run_id": "actual-one-life", "played_character_id": 31254}
        self.assertEqual(action._intent_identity_v1(legacy, 0),
            {"episode_run_id": "actual-one-life", "played_character_id": 31254, "source_rite_id": 0})
        for field in ("bridge_pipe", "frozen_argv_sha256"):
            invalid = deepcopy(actual)
            invalid["managed_campaign_run_binding"][field] = "invalid"
            with self.subTest(field=field), self.assertRaises(BridgeUnavailableError):
                action._binding(invalid, invalid["revision"])
        invalid = deepcopy(actual)
        invalid["episode_run_id"] = "invented"
        with self.assertRaises(BridgeUnavailableError): action._binding(invalid, invalid["revision"])
        invalid = deepcopy(actual)
        del invalid["managed_campaign_run_binding"]
        with self.assertRaises(BridgeUnavailableError): action._binding(invalid, invalid["revision"])

    def test_finite_request_fields_reject_pointers_overrides_and_personal_tenet_ambiguity(self):
        for operation, kwargs in (
            ("preview", {"actor_id": ACTOR}), ("preview", {"callback_rva": 0x14F51B0}),
            ("select_core_tenet", {"core_slot_index": True, "tenet_key": "tenet_adaptive"}),
            ("select_core_tenet", {"core_slot_index": 64, "tenet_key": "tenet_adaptive"}),
            ("select_doctrine", {"group_key": "../path", "doctrine_key": "x"}),
            ("set_name_field", {"name_field": "arbitrary", "text": "x"}),
            ("set_name_field", {"name_field": "name", "text": "x\x00y"}),
            ("confirm_once", {"expected_preview_identity": "A" * 64, "expected_outcome_kind": "create_faith"}),
            ("confirm_once", {"expected_preview_identity": "a" * 64, "expected_outcome_kind": "force_create_faith"}),
        ):
            with self.subTest(operation=operation, kwargs=kwargs), self.assertRaises(ValueError):
                action.request_fields(operation, RITE, **kwargs)
        fields = action.request_fields("select_core_tenet", RITE, core_slot_index=0, tenet_key="tenet_christian_syncretism")
        self.assertEqual(fields["operation"], "select_core_tenet")
        self.assertNotIn("actor_id", fields)

    def test_existing_acceptance_case_requires_explicit_boolean_and_all_three_tools(self):
        path = Path(__file__).resolve().parents[3] / "tools/ck3_mod_acceptance.py"
        text = SOURCE_TEXT_OVERRIDE if SOURCE_TEXT_OVERRIDE is not None else path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        definition = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_RITE_CREATION_ACTION_MCP_TOOLS" for target in node.targets))
        tools = frozenset(ast.literal_eval(definition.value.args[0]))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Selection")
        init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        index = next(index for index, node in enumerate(init.body) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute) and target.attr == "opt_in_player_rite_creation_actions" for target in node.targets))
        code = compile(ast.fix_missing_locations(ast.Module(body=init.body[index:index + 4], type_ignores=[])), str(path), "exec")
        for case, expected in (({}, False), ({"opt_in_player_rite_creation_actions": True, "required_mcp_tools": list(tools)}, True)):
            selected = SimpleNamespace(case=case)
            exec(code, {"self": selected, "CASE_RITE_CREATION_ACTION_MCP_TOOLS": tools})
            self.assertIs(selected.opt_in_player_rite_creation_actions, expected)
        for case in ({"opt_in_player_rite_creation_actions": 1}, {"opt_in_player_rite_creation_actions": "true"},
                {"opt_in_player_rite_creation_actions": True}, {"required_mcp_tools": [next(iter(tools))]}):
            with self.assertRaises(ValueError):
                exec(code, {"self": SimpleNamespace(case=case), "CASE_RITE_CREATION_ACTION_MCP_TOOLS": tools})
        branch = next(node for node in ast.walk(cls) if isinstance(node, ast.If)
            and isinstance(node.test, ast.Attribute) and node.test.attr == "opt_in_player_rite_creation_actions")
        for enabled in (False, True):
            arguments = []
            exec(compile(ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])), str(path), "exec"),
                {"self": SimpleNamespace(opt_in_player_rite_creation_actions=enabled), "argv": arguments})
            self.assertEqual(arguments, ["--private-player-rite-creation-actions"] if enabled else [])

    def test_default_off_and_missing_real_capability_never_send(self):
        driver, endpoint = self.driver()
        driver.allow_private_player_rite_creation_actions = False
        with self.assertRaises(BridgeUnavailableError): self.call(driver)
        driver.allow_private_player_rite_creation_actions = True
        with patch.object(driver, "capabilities", return_value={"bridge_capabilities": []}):
            with self.assertRaises(UnsupportedStepError): self.call(driver)
        self.assertEqual(endpoint.requests, [])

    def test_existing_primitive_maps_public_to_native_and_keeps_original_backend(self):
        driver, endpoint = self.driver()
        public = driver.take_snapshot_without_native_command_history()["revision"]
        self.assertNotEqual(public, 9)
        result = self.call(driver, "select_core_tenet", core_slot_index=0, tenet_key="tenet_christian_syncretism")
        self.assertEqual(endpoint.requests[0]["expected_revision"], 9)
        self.assertEqual(endpoint.requests[0]["step"], action.STEP)
        self.assertEqual(endpoint.requests[0]["expected_connection_generation"], 1)
        self.assertEqual(endpoint.requests[0]["expected_date_raw"], DATE)
        self.assertEqual(endpoint.requests[0]["expected_player_character_id"], ACTOR)
        self.assertEqual(result["backend_id"], "ck3-1.20.0.4-native-rite-creation-action-v1")
        self.assertIsNone(result[action.BODY_KEY]["full_can"]["can_create"])
        self.assertFalse(result["business_outcome_verified"])
        self.assertFalse(result["action_ready"])
        self.transport_summaries.append({"case": "unavailable_actual_primitive", "public_revision": public,
            "native_expected_revision": endpoint.requests[0]["expected_revision"], "wire_send_count": 1,
            "native_source_evidence": False, "current_legality": None})

    def test_no_post_modal_or_complete_payload_proof_never_claims_or_sends(self):
        driver, endpoint = self.driver()
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver, stage="none")
        raw = synthetic_preview()
        raw[action.BODY_KEY]["complete_command_payload_observed"] = False
        with self.assertRaises(ValueError):
            action.normalize_result(raw, binding=action._binding(driver.take_snapshot_without_native_command_history(),
                driver.take_snapshot_without_native_command_history()["revision"]),
                fields={"operation": "preview", "expected_source_rite_id": RITE})
        self.assertEqual(endpoint.requests, [])
        self.assertEqual(list(Path(self.temp.name).rglob("*.claim.json")), [])

    def test_claim_fsync_precedes_send_and_unknown_cannot_escape_via_revision_or_restart(self):
        driver, endpoint = self.driver()
        original_episode = driver.take_snapshot_without_native_command_history()["episode_run_id"]
        with patch.object(action.os, "fsync", wraps=os.fsync) as fsync:
            def check(request):
                claims = list(Path(self.temp.name).rglob("*.claim.json"))
                self.assertEqual(len(claims), 1)
                self.assertGreater(fsync.call_count, 0)
                self.assertEqual(json.loads(claims[0].read_text())["request_id"], request["request_id"])
            endpoint.on_send_check = check
            result = self.confirm(driver)
        self.assertFalse(result["business_outcome_verified"])
        self.assertTrue(result[action.BODY_KEY]["original_writer_may_have_been_queued"])
        endpoint.snapshot["revision"] = 10
        endpoint.publish(endpoint.snapshot)
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver, 10, token="b" * 64)
        self.assertEqual(len(endpoint.requests), 1)
        driver.close()
        restarted, other = self.driver(10)
        self.assertEqual(restarted.take_snapshot_without_native_command_history()["episode_run_id"], original_episode)
        with self.assertRaises(BridgeUnavailableError): self.confirm(restarted, 10, token="c" * 64)
        self.assertEqual(other.requests, [])
        self.transport_summaries.append({"case": "durable_unknown", "claim_fsync_before_send": True,
            "changed_native_revision_rejected": True, "new_preview_token_rejected": True,
            "new_driver_same_episode_rejected": True, "wire_send_count": 1,
            "new_native_action_or_game_evidence": False})

    def test_late_result_collection_waits_original_request_without_resend(self):
        driver, endpoint = self.driver()
        endpoint.timeout = True
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver)
        request = endpoint.requests[0]
        pending = action.collect_private_result_v1(driver, action_request_id=request["request_id"])
        self.assertEqual(pending["status"], "pending_unknown")
        endpoint.publish(endpoint.packet(request))
        late = action.collect_private_result_v1(driver, action_request_id=request["request_id"])
        self.assertFalse(late["business_outcome_verified"])
        self.assertEqual(late["status_scope"], "original_request_result_only_not_current_legality")
        self.assertEqual(len(endpoint.requests), 1)
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver)
        self.assertEqual(len(endpoint.requests), 1)

    def test_known_native_no_dispatch_releases_only_after_retaining_complete_intent(self):
        driver, endpoint = self.driver()
        endpoint.known_reject = True
        first = self.confirm(driver)
        self.assertTrue(first["known_no_dispatch_intent_released"])
        self.assertEqual(len(endpoint.requests), 1)
        self.assertEqual(list(Path(self.temp.name).rglob("*.claim.json")), [])
        safe = list(Path(self.temp.name).rglob("*.safe-no-dispatch.json"))
        self.assertEqual(len(safe), 1)
        self.assertEqual(json.loads(safe[0].read_text())["original_claim"]["request_id"], first["action_request_id"])
        collected = action.collect_private_result_v1(driver, action_request_id=first["action_request_id"])
        self.assertTrue(collected["known_no_dispatch_intent_released"])
        self.assertEqual(len(endpoint.requests), 1)
        self.confirm(driver, token="b" * 64)
        self.assertEqual(len(endpoint.requests), 2)  # two explicit requests, never an automatic resend

    def test_existing_primitive_presubmission_capability_race_is_proven_unsent(self):
        driver, endpoint = self.driver()
        capabilities = driver.capabilities()
        count = 0
        def changed():
            nonlocal count
            count += 1
            return capabilities if count == 1 else {"bridge_capabilities": []}
        with patch.object(driver, "capabilities", side_effect=changed):
            with self.assertRaises(UnsupportedStepError): self.confirm(driver)
        self.assertEqual(endpoint.requests, [])
        self.assertEqual(list(Path(self.temp.name).rglob("*.claim.json")), [])
        self.assertEqual(len(list(Path(self.temp.name).rglob("*.safe-no-dispatch.json"))), 1)

    def test_independent_poststate_distinguishes_new_faith_rite_quote_and_unknown_wallet(self):
        driver, endpoint = self.driver()
        before = driver.take_snapshot_without_native_command_history()
        before["played_character_piety"] = {"raw": 100000, "scale": 100000}
        after = deepcopy(before)
        after["revision"] += 1
        after["native_revision"] += 1
        after["played_character_piety"] = {"raw": 0, "scale": 100000}
        args = {"before_snapshot": before, "after_snapshot": after,
            "before_context": synthetic_context(before),
            "after_context": synthetic_context(after, rite=92, faith=91, main=92),
            "expected_outcome_kind": "create_faith", "quoted_piety_cost_raw": 100000}
        result = action.evaluate_independent_poststate_v1(**args)
        self.assertTrue(result["identity_pattern_matches"])
        self.assertEqual(result["piety_after_raw"], 0)
        self.assertEqual(result["piety_quote_comparison"], "equal")
        self.assertFalse(result["business_outcome_verified"])
        self.assertFalse(result["doctrine_parameters_verified"])
        args["after_context"] = synthetic_context(after, rite=92)
        self.assertFalse(action.evaluate_independent_poststate_v1(**args)["identity_pattern_matches"])
        args["expected_outcome_kind"] = "create_rite"
        self.assertTrue(action.evaluate_independent_poststate_v1(**args)["identity_pattern_matches"])
        after.pop("played_character_piety")
        unknown = action.evaluate_independent_poststate_v1(**args)
        self.assertIsNone(unknown["piety_after_raw"])
        self.assertIsNone(unknown["piety_delta_raw"])
        self.assertEqual(unknown["piety_quote_comparison"], "unknown")
        self.assertEqual(endpoint.requests, [])


class RiteCreationMcpTests(unittest.IsolatedAsyncioTestCase):
    setUp = RiteCreationAdapterTests.setUp
    driver = RiteCreationAdapterTests.driver
    actual_mcp_summaries = []

    async def test_real_mcp_default_off_finite_selectors_and_missing_native_proof(self):
        driver, endpoint = self.driver()
        driver.allow_private_player_rite_creation_actions = False
        query = "ck3_query_player_rite_creation_action_context_v1"
        write = "ck3_execute_player_rite_creation_action_v1"
        collect = "ck3_collect_player_rite_creation_action_result_v1"
        async with Client(create_server(driver)) as client:
            self.assertFalse({query, write, collect} & {tool.name for tool in (await client.session.list_tools()).tools})
        driver.allow_private_player_rite_creation_actions = True
        public = driver.take_snapshot_without_native_command_history()["revision"]
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
            self.assertTrue({query, write, collect} <= set(tools))
            self.assertTrue(tools[query].annotations.read_only_hint)
            self.assertFalse(tools[write].annotations.read_only_hint)
            self.assertFalse(tools[write].annotations.idempotent_hint)
            self.assertNotIn("observed_preview", tools[write].input_schema["properties"])
            self.assertNotIn("actor_id", tools[write].input_schema["properties"])
            for tool, arguments in (
                (query, {"expected_revision": public, "expected_source_rite_id": RITE}),
                (write, {"operation": "select_core_tenet", "expected_revision": public,
                    "expected_source_rite_id": RITE, "core_slot_index": 0, "tenet_key": "tenet_christian_syncretism"}),
            ):
                reply = await client.session.call_tool(tool, arguments)
                self.assertFalse(reply.is_error, str(reply))
                self.assertFalse(reply.structured_content["action_ready"])
                self.assertIsNone(reply.structured_content[action.BODY_KEY]["full_can"]["can_create"])
                self.actual_mcp_summaries.append({"tool": tool, "is_error": reply.is_error,
                    "public_revision": public, "native_revision": 9, "synthetic_endpoint_only": True,
                    "action_ready": reply.structured_content["action_ready"]})
            invalid = await client.session.call_tool(write, {"operation": "open_create_draft", "expected_revision": public,
                "expected_source_rite_id": RITE, "actor_id": ACTOR})
            self.assertTrue(invalid.is_error)
            missing = await client.session.call_tool(write, {"operation": "confirm_once", "expected_revision": public,
                "expected_source_rite_id": RITE, "expected_preview_identity": "a" * 64,
                "expected_outcome_kind": "create_faith"})
            self.assertTrue(missing.is_error)
            self.assertIn("actual post-modal preview", " ".join(item.text for item in missing.content if item.type == "text"))
        self.assertEqual(len(endpoint.requests), 2)
        self.assertTrue(all(request["expected_revision"] == 9 for request in endpoint.requests))
        self.assertFalse(parser().parse_args([]).private_player_rite_creation_actions)
        self.assertTrue(parser().parse_args(["--private-player-rite-creation-actions"]).private_player_rite_creation_actions)


if __name__ == "__main__":
    unittest.main()
