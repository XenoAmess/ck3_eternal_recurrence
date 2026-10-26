"""Synthetic transport-only cases through real NativeDriver primitive.

These are not compiled native packets, actual draft eligibility, or live CK3
evidence. They verify revision mapping, diagnostics, retained ACK and no resend.
"""
from __future__ import annotations

from copy import deepcopy
import ast
import hashlib
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
from xar_autoplayer.bridge import rite_creation_action_private_v1 as contract
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


def synthetic_catalogue(*, scope: action.CatalogueScope, rite_id: int | None,
        observed: bool = True) -> action.VirtueSinCatalogue:
    return {"schema": "ck3_12004_rite_virtue_sin_catalogue_v1", "scope": scope,
        "observed": observed, "unavailable_reason": None if observed else "synthetic_cache_unavailable",
        "rite_id": rite_id,
        "virtues": [{"trait_id": 101, "trait_key": "brave", "classification": 1,
            "weight_raw": "9007199254740993"}] if observed else None,
        "sins": [{"trait_id": 102, "trait_key": "gluttonous", "classification": 2,
            "weight_raw": "-9223372036854775808"}] if observed else None}


def unavailable(operation, native_revision=9):
    return {"step": action.STEP, "accepted": True, "status": "unavailable", "private_build": True,
        "advertised": False, "read_only": operation in action.READ_OPERATIONS, "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "backend_id": "ck3-1.20.0.4-native-rite-creation-action-v1",
        "domain_key": action.DOMAIN_KEY, "snapshot_revision": native_revision, "date_raw": DATE,
        action.BODY_KEY: {"schema": action.SCHEMA, "operation": operation, "available": False,
            "unavailable_reason": "synthetic_complete_payload_not_observed",
            "frame": {"connection_generation": 1, "native_revision": native_revision,
                "capture_epoch": 3, "date_raw": DATE, "played_character_id": ACTOR},
            "draft": {"observed": False, "names_observed": False,
                "selected_core_tenets_observed": False, "selected_doctrines_observed": False,
                "selected_core_slot_count": None, "selected_core_slot_capacity": None,
                "source_rite_id": None, "source_faith_id": None,
                "actor_faith_id": None, "actual_outcome_kind": None, "names": None,
                "selected_core_tenets": None, "selected_doctrines": None,
                "virtue_sin_catalogue": synthetic_catalogue(scope="draft", rite_id=None, observed=False)},
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
            "action_id": None, "current_rite_poststate": None}}


def synthetic_preview(native_revision=9, *, stage="confirmation", token="a" * 64):
    raw = unavailable("preview", native_revision)
    raw["status"] = "observed"
    leaf = raw[action.BODY_KEY]
    leaf.update(available=True, unavailable_reason=None, complete_command_payload_observed=True,
        original_writer_inputs_observed=True, native_command_text_bytes=1234, native_command_text_sha256="d" * 64,
        preview_identity_available=True, preview_identity=token)
    leaf["draft"].update(observed=True, source_rite_id=RITE, source_faith_id=27, actor_faith_id=27,
        names_observed=True, selected_core_tenets_observed=True, selected_doctrines_observed=True,
        selected_core_slot_count=1, selected_core_slot_capacity=1,
        actual_outcome_kind="create_faith", names={key: "fixture" for key in action.NAME_FIELDS},
        selected_core_tenets=[{"slot_index": 0, "tenet_key": "tenet_christian_syncretism"}],
        selected_doctrines=[{"group_key": "doctrine_pluralism", "doctrine_key": "doctrine_pluralism_pluralistic"}],
        virtue_sin_catalogue=synthetic_catalogue(scope="draft", rite_id=RITE))
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


def synthetic_poststate(preview, *, rite=92, faith=91):
    payload = contract.submitted_payload_from_draft(preview[action.BODY_KEY]["draft"])
    return {"schema": "ck3_12004_rite_creation_poststate_v1", "observed": True,
        "unavailable_reason": None, "source_rite_id_anchor": payload["source_rite_id"],
        "rite_id": rite, "faith_id": faith, "religion_id": 28,
        "founder_character_id": ACTOR, "names": payload["names"],
        "core_tenets": [{"slot_index": index, "tenet_key": row["tenet_key"]}
            for index, row in enumerate(payload["core_tenets"])], "doctrines": payload["doctrines"],
        "virtue_sin_catalogue": synthetic_catalogue(scope="current_rite", rite_id=rite),
        "confirmation_modal_open": False, "creation_window_visible": False}


class Endpoint:
    pipe_name = r"\\.\pipe\synthetic-rite-action-transport-only"
    def __init__(self):
        self.requests = []
        self.timeout = False
        self.known_reject = False
        self.on_send_check = None
        self.preview = None
        self.poststate = None
        self.poststate_epoch = 4
    def start(self, on_frame, on_disconnect): self.on_frame = on_frame
    def publish(self, frame): self.on_frame(deepcopy(frame))
    def packet(self, request):
        raw = unavailable(request["operation"], request["expected_revision"])
        if request["operation"] == "preview" and self.preview is not None:
            raw = deepcopy(self.preview)
        if request["operation"] == "observe_current_rite" and self.poststate is not None:
            raw.update(status="observed")
            raw[action.BODY_KEY].update(available=True, unavailable_reason=None,
                current_rite_poststate=deepcopy(self.poststate))
            raw[action.BODY_KEY]["frame"]["capture_epoch"] = self.poststate_epoch
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
            ("select_core_tenet", {"core_slot_index": 100, "tenet_key": "tenet_adaptive"}),
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
        self.assertEqual(action.request_fields("select_core_tenet", RITE,
            core_slot_index=99, tenet_key="tenet_adaptive")["core_slot_index"], 99)

    def test_existing_acceptance_case_requires_explicit_boolean_and_all_three_tools(self):
        path = Path(__file__).resolve().parents[3] / "tools/ck3_mod_acceptance.py"
        text = SOURCE_TEXT_OVERRIDE if SOURCE_TEXT_OVERRIDE is not None else path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        definition = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_RITE_CREATION_ACTION_MCP_TOOLS" for target in node.targets))
        tools = frozenset(ast.literal_eval(definition.value.args[0]))
        required_definition = next((node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_RITE_CREATION_ACTION_REQUIRED_MCP_TOOLS"
                for target in node.targets)), None)
        globals_scope = {"CASE_RITE_CREATION_ACTION_MCP_TOOLS": tools}
        if required_definition is not None:
            exec(compile(ast.fix_missing_locations(ast.Module(body=[required_definition], type_ignores=[])), str(path), "exec"), globals_scope)
        required_tools = globals_scope.get("CASE_RITE_CREATION_ACTION_REQUIRED_MCP_TOOLS", tools)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Selection")
        init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        index = next(index for index, node in enumerate(init.body) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute) and target.attr == "opt_in_player_rite_creation_actions" for target in node.targets))
        code = compile(ast.fix_missing_locations(ast.Module(body=init.body[index:index + 4], type_ignores=[])), str(path), "exec")
        for case, expected in (({}, False), ({"opt_in_player_rite_creation_actions": True, "required_mcp_tools": list(required_tools)}, True)):
            selected = SimpleNamespace(case=case)
            exec(code, {**globals_scope, "self": selected})
            self.assertIs(selected.opt_in_player_rite_creation_actions, expected)
        for case in ({"opt_in_player_rite_creation_actions": 1}, {"opt_in_player_rite_creation_actions": "true"},
                {"opt_in_player_rite_creation_actions": True}, {"required_mcp_tools": [next(iter(tools))]}):
            with self.assertRaises(ValueError):
                exec(code, {**globals_scope, "self": SimpleNamespace(case=case)})
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

    def test_complete_payload_roundtrip_rejects_wrong_missing_fields_and_boolean_ids(self) -> None:
        payload = contract.submitted_payload_from_draft(synthetic_preview()[action.BODY_KEY]["draft"])
        self.assertEqual(contract.parse_submitted_payload(json.loads(json.dumps(payload))), payload)
        for field, value in (("source_rite_id", True), ("source_faith_id", 27.0),
                ("core_tenets", None), ("doctrines", {}), ("names", {"name": "fixture"})):
            invalid = deepcopy(payload)
            invalid[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                contract.parse_submitted_payload(invalid)
        invalid = deepcopy(payload)
        invalid["source_rite"] = invalid.pop("source_rite_id")
        with self.assertRaises(ValueError): contract.parse_submitted_payload(invalid)
        invalid = deepcopy(payload)
        invalid["core_tenets"][0]["slot_index"] = False
        with self.assertRaises(ValueError): contract.parse_submitted_payload(invalid)
        invalid = deepcopy(payload)
        invalid["doctrines"].append(deepcopy(invalid["doctrines"][0]))
        with self.assertRaises(ValueError): contract.parse_submitted_payload(invalid)
        post = synthetic_poststate(synthetic_preview())
        self.assertEqual(contract.parse_current_rite_poststate(json.loads(json.dumps(post))), post)
        for field in post:
            invalid = deepcopy(post)
            del invalid[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                contract.parse_current_rite_poststate(invalid)

    def test_sparse_slots_preserve_payload_and_match_dense_persistent_core_by_keys(self) -> None:
        preview = synthetic_preview()
        draft = preview[action.BODY_KEY]["draft"]
        draft.update(selected_core_slot_count=100, selected_core_slot_capacity=120,
            selected_core_tenets=[{"slot_index": slot, "tenet_key": key} for slot, key in
                ((0, "tenet_adaptive"), (17, "tenet_asceticism"), (99, "tenet_legalism"))])
        payload = contract.submitted_payload_from_draft(draft)
        self.assertEqual([row["slot_index"] for row in payload["core_tenets"]], [0, 17, 99])
        self.assertEqual(contract.parse_submitted_payload(json.loads(json.dumps(payload))), payload)
        post = contract.parse_current_rite_poststate(synthetic_poststate(preview))
        self.assertTrue(contract.poststate_matches_payload(payload, post, ACTOR))
        shifted = deepcopy(payload)
        shifted["core_tenets"][1]["slot_index"] = 18
        self.assertFalse(contract.different_business_intent(payload, shifted))
        wrong = deepcopy(post)
        wrong["core_tenets"][1]["tenet_key"] = "tenet_replaced"
        self.assertFalse(contract.poststate_matches_payload(payload, wrong, ACTOR))
        invalid = synthetic_poststate(preview)
        invalid["core_tenets"] = payload["core_tenets"]
        with self.assertRaises(ValueError): contract.parse_current_rite_poststate(invalid)

    def test_native_slot_counts_and_sparse_indices_reject_missing_wrong_and_duplicate_values(self) -> None:
        good = synthetic_preview()[action.BODY_KEY]["draft"]
        for field, value in (("selected_core_slot_count", True), ("selected_core_slot_count", 1.0),
                ("selected_core_slot_count", 101), ("selected_core_slot_capacity", False),
                ("selected_core_slot_capacity", 0), ("selected_core_slot_capacity", 1 << 31)):
            invalid = deepcopy(good)
            invalid[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                contract.parse_draft_core_tenets(invalid)
        for field in ("selected_core_slot_count", "selected_core_slot_capacity"):
            invalid = deepcopy(good)
            del invalid[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                contract.parse_draft_core_tenets(invalid)
        for rows in ([{"slot_index": 1, "tenet_key": "tenet_a"}],
                [{"slot_index": False, "tenet_key": "tenet_a"}],
                [{"slot_index": 0, "tenet_key": "tenet_a"}, {"slot_index": 0, "tenet_key": "tenet_b"}],
                [{"slot_index": 0, "tenet_key": "tenet_a"}, {"slot_index": 1, "tenet_key": "tenet_a"}]):
            invalid = deepcopy(good)
            invalid["selected_core_tenets"] = rows
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                contract.parse_draft_core_tenets(invalid)
        empty = deepcopy(good)
        empty.update(selected_core_slot_count=0, selected_core_slot_capacity=0, selected_core_tenets=[])
        self.assertEqual(contract.parse_draft_core_tenets(empty), [])  # Observation does not grant native Can.
        unavailable_draft = unavailable("preview")[action.BODY_KEY]["draft"]
        self.assertIsNone(contract.parse_draft_core_tenets(unavailable_draft))
        unavailable_draft["selected_core_slot_count"] = 0
        with self.assertRaises(ValueError): contract.parse_draft_core_tenets(unavailable_draft)

    def test_full_native_catalogue_roundtrip_preserves_order_signed64_and_source(self) -> None:
        catalogue = synthetic_catalogue(scope="draft", rite_id=RITE)
        catalogue["virtues"].append({"trait_id": 99, "trait_key": "generous", "classification": 1,
            "weight_raw": "9223372036854775807"})
        parsed = contract.parse_virtue_sin_catalogue(json.loads(json.dumps(catalogue)), scope="draft", rite_id=RITE)
        self.assertEqual(parsed, catalogue)
        self.assertEqual([row["trait_id"] for row in parsed["virtues"]], [101, 99])
        for field, value in (("trait_id", True), ("trait_id", 101.0), ("trait_id", 0xFFFFFFFF),
                ("classification", True), ("classification", 2), ("trait_key", "../brave"),
                ("weight_raw", 9007199254740993), ("weight_raw", "-0"), ("weight_raw", "01"),
                ("weight_raw", "+1"), ("weight_raw", "9223372036854775808")):
            invalid = deepcopy(catalogue)
            invalid["virtues"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                contract.parse_virtue_sin_catalogue(invalid, scope="draft", rite_id=RITE)
        for field in catalogue:
            invalid = deepcopy(catalogue)
            del invalid[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                contract.parse_virtue_sin_catalogue(invalid, scope="draft", rite_id=RITE)
        for field, value in (("trait_id", 101), ("trait_key", "brave")):
            invalid = deepcopy(catalogue)
            invalid["sins"][0][field] = value
            with self.subTest(duplicate=field), self.assertRaises(ValueError):
                contract.parse_virtue_sin_catalogue(invalid, scope="draft", rite_id=RITE)
        with self.assertRaises(ValueError):
            contract.parse_virtue_sin_catalogue(catalogue, scope="current_rite", rite_id=RITE)
        with self.assertRaises(ValueError):
            contract.parse_virtue_sin_catalogue(catalogue, scope="draft", rite_id=RITE + 1)
        empty = deepcopy(catalogue)
        empty.update(virtues=[], sins=[])
        self.assertEqual(contract.parse_virtue_sin_catalogue(empty, scope="draft", rite_id=RITE), empty)
        invalid = deepcopy(empty)
        invalid["virtues"] = None
        with self.assertRaises(ValueError):
            contract.parse_virtue_sin_catalogue(invalid, scope="draft", rite_id=RITE)

    def test_missing_current_catalogue_window_does_not_hide_independent_basic_poststate(self) -> None:
        preview = synthetic_preview()
        payload = contract.submitted_payload_from_draft(preview[action.BODY_KEY]["draft"])
        post = synthetic_poststate(preview)
        post["virtue_sin_catalogue"] = synthetic_catalogue(scope="current_rite", rite_id=post["rite_id"], observed=False)
        parsed = contract.parse_current_rite_poststate(post)
        self.assertTrue(parsed["observed"])
        self.assertFalse(parsed["virtue_sin_catalogue"]["observed"])
        self.assertTrue(contract.poststate_matches_payload(payload, parsed, ACTOR))

    def test_native_formatted_description_roundtrips_but_authored_controls_remain_rejected(self) -> None:
        preview = synthetic_preview()
        description = "实际中文\x15ONCLICK:religion\x15TOOLTIP:rite\x15"
        preview[action.BODY_KEY]["draft"]["names"]["description"] = description
        payload = contract.submitted_payload_from_draft(preview[action.BODY_KEY]["draft"])
        self.assertEqual(contract.parse_submitted_payload(json.loads(json.dumps(payload)))["names"]["description"], description)
        post = contract.parse_current_rite_poststate(json.loads(json.dumps(synthetic_poststate(preview))))
        self.assertEqual(post["names"]["description"], description)
        self.assertTrue(contract.poststate_matches_payload(payload, post, ACTOR))
        with self.assertRaises(ValueError):
            action.request_fields("set_name_field", RITE, name_field="description", text=description)
        self.assertEqual(action.request_fields("set_name_field", RITE,
            name_field="description", text="纯中文\n\t描述")["text"], "纯中文\n\t描述")

    def test_verified_successor_keeps_original_claim_and_requires_different_business_payload(self) -> None:
        driver, endpoint = self.driver()
        preview = synthetic_preview()
        first = self.confirm(driver)
        claim_path = next(Path(self.temp.name).rglob("*.claim.json"))
        original_bytes = claim_path.read_bytes()
        endpoint.poststate = synthetic_poststate(preview)
        verified = action.verify_completed_private_v1(driver, action_request_id=first["action_request_id"],
            expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
        self.assertTrue(verified["business_outcome_verified"])
        self.assertEqual(claim_path.read_bytes(), original_bytes)
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver, token="b" * 64)
        second_preview = synthetic_preview(token="b" * 64)
        second_preview[action.BODY_KEY]["draft"]["names"]["name"] = "another explicit authored name"
        second = self.call(driver, "confirm_once", expected_preview_identity="b" * 64,
            expected_outcome_kind="create_faith", observed_preview=second_preview)
        claims = list(Path(self.temp.name).rglob("*.claim.json"))
        self.assertEqual(len(claims), 2)
        self.assertEqual(claim_path.read_bytes(), original_bytes)
        successor = next(json.loads(path.read_text()) for path in claims if path != claim_path)
        self.assertEqual(successor["predecessor_request_id"], first["action_request_id"])
        self.assertNotEqual(first["action_request_id"], second["action_request_id"])
        self.assertEqual([request["operation"] for request in endpoint.requests],
            ["confirm_once", "observe_current_rite", "confirm_once"])
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver, token="c" * 64)

    def test_false_or_stale_poststate_and_changed_evidence_never_admit_a_successor(self) -> None:
        driver, endpoint = self.driver()
        first = self.confirm(driver)
        original = synthetic_poststate(synthetic_preview())
        for field, value in (("rite_id", RITE), ("founder_character_id", ACTOR + 1),
                ("confirmation_modal_open", True), ("creation_window_visible", True),
                ("names", {**original["names"], "name": "different"}), ("doctrines", [])):
            endpoint.poststate = {**deepcopy(original), field: value}
            if field == "rite_id":
                endpoint.poststate["virtue_sin_catalogue"]["rite_id"] = value
            with self.subTest(field=field):
                result = action.verify_completed_private_v1(driver, action_request_id=first["action_request_id"],
                    expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
                self.assertFalse(result["business_outcome_verified"])
                self.assertEqual(result["status"], "poststate_mismatch")
        self.assertEqual(list(Path(self.temp.name).rglob("*.completed.json")), [])
        endpoint.poststate = original
        endpoint.poststate_epoch = 3
        with self.assertRaises(BridgeUnavailableError):
            action.verify_completed_private_v1(driver, action_request_id=first["action_request_id"],
                expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
        endpoint.poststate_epoch = 4
        complete = action.verify_completed_private_v1(driver, action_request_id=first["action_request_id"],
            expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
        receipt_path = Path(complete["completion_receipt"])
        receipt = json.loads(receipt_path.read_text())
        evidence = receipt_path.parent / receipt["poststate_native_result_file"]
        evidence.write_text(evidence.read_text() + " ")
        changed = synthetic_preview(token="b" * 64)
        changed[action.BODY_KEY]["draft"]["names"]["name"] = "new intent"
        with self.assertRaises(BridgeUnavailableError):
            self.call(driver, "confirm_once", expected_preview_identity="b" * 64,
                expected_outcome_kind="create_faith", observed_preview=changed)

    def test_unknown_and_legacy_claims_cannot_be_reclassified_by_current_payload(self) -> None:
        driver, endpoint = self.driver()
        endpoint.timeout = True
        first_id = None
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver)
        claim_path = next(Path(self.temp.name).rglob("*.claim.json"))
        record = json.loads(claim_path.read_text())
        first_id = record["request_id"]
        endpoint.poststate = synthetic_poststate(synthetic_preview())
        pending = action.verify_completed_private_v1(driver, action_request_id=first_id,
            expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
        self.assertEqual(pending["status"], "pending_unknown")
        self.assertEqual(len(endpoint.requests), 1)
        record.pop("submitted_payload")
        record.pop("predecessor_request_id")
        record["schema"] = "xar.ck3-rite-confirm-once.v1"
        claim_path.write_text(json.dumps(record))
        with self.assertRaises(BridgeUnavailableError):
            action.verify_completed_private_v1(driver, action_request_id=first_id,
                expected_revision=driver.take_snapshot_without_native_command_history()["revision"])
        with self.assertRaises(BridgeUnavailableError): self.confirm(driver, token="d" * 64)
        self.assertEqual(len(endpoint.requests), 1)

    def test_cancel_or_actual_source_change_does_not_release_an_unknown_confirmation(self) -> None:
        driver, endpoint = self.driver()
        self.confirm(driver)
        claim_path = next(Path(self.temp.name).rglob("*.claim.json"))
        before = claim_path.read_bytes()
        with self.assertRaises(BridgeUnavailableError): self.call(driver, "cancel_draft")
        self.assertEqual(claim_path.read_bytes(), before)
        moved = synthetic_preview(token="e" * 64)
        moved[action.BODY_KEY]["draft"]["source_rite_id"] = 93
        moved[action.BODY_KEY]["draft"]["virtue_sin_catalogue"]["rite_id"] = 93
        moved[action.BODY_KEY]["draft"]["names"]["name"] = "other authored Rite"
        with self.assertRaises(BridgeUnavailableError):
            action.execute_private_v1(driver, operation="confirm_once",
                expected_revision=driver.take_snapshot_without_native_command_history()["revision"],
                expected_source_rite_id=93, expected_preview_identity="e" * 64,
                expected_outcome_kind="create_faith", observed_preview=moved)
        self.assertEqual([request["operation"] for request in endpoint.requests], ["confirm_once"])

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

    async def test_real_mcp_sparse_slot99_retained_claim_and_native_catalogue_readback(self) -> None:
        driver, endpoint = self.driver()
        preview = synthetic_preview()
        draft = preview[action.BODY_KEY]["draft"]
        draft.update(selected_core_slot_count=100, selected_core_slot_capacity=100,
            selected_core_tenets=[{"slot_index": slot, "tenet_key": key} for slot, key in
                ((0, "tenet_adaptive"), (50, "tenet_asceticism"), (99, "tenet_legalism"))])
        endpoint.preview = preview
        endpoint.poststate = synthetic_poststate(preview)
        query = "ck3_query_player_rite_creation_action_context_v1"
        write = "ck3_execute_player_rite_creation_action_v1"
        verify = "ck3_verify_player_rite_creation_action_completed_v1"
        public = driver.take_snapshot_without_native_command_history()["revision"]
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
            slot_schema = tools[write].input_schema["properties"]["core_slot_index"]
            self.assertTrue(any(part.get("exclusiveMaximum") == 100 for part in slot_schema["anyOf"]))
            read = await client.session.call_tool(query, {"expected_revision": public, "expected_source_rite_id": RITE})
            self.assertFalse(read.is_error, str(read))
            self.assertEqual(read.structured_content[action.BODY_KEY]["draft"]["virtue_sin_catalogue"],
                draft["virtue_sin_catalogue"])
            for slot in (True, 99.0, 100):
                invalid = await client.session.call_tool(write, {"operation": "select_core_tenet",
                    "expected_revision": public, "expected_source_rite_id": RITE,
                    "core_slot_index": slot, "tenet_key": "tenet_legalism"})
                self.assertTrue(invalid.is_error, str(invalid))
            selected = await client.session.call_tool(write, {"operation": "select_core_tenet",
                "expected_revision": public, "expected_source_rite_id": RITE,
                "core_slot_index": 99, "tenet_key": "tenet_legalism"})
            self.assertFalse(selected.is_error, str(selected))
            self.assertEqual(endpoint.requests[-1]["core_slot_index"], 99)
            await client.session.call_tool(query, {"expected_revision": public, "expected_source_rite_id": RITE})
            sent = await client.session.call_tool(write, {"operation": "confirm_once", "expected_revision": public,
                "expected_source_rite_id": RITE, "expected_preview_identity": "a" * 64,
                "expected_outcome_kind": "create_faith"})
            self.assertFalse(sent.is_error, str(sent))
            request_id = sent.structured_content["action_request_id"]
            claim_path = next(Path(self.temp.name).rglob("*.claim.json"))
            before = claim_path.read_bytes()
            claim = json.loads(before)
            self.assertEqual([row["slot_index"] for row in claim["submitted_payload"]["core_tenets"]], [0, 50, 99])
            finished = await client.session.call_tool(verify, {"action_request_id": request_id, "expected_revision": public})
            self.assertFalse(finished.is_error, str(finished))
            self.assertTrue(finished.structured_content["business_outcome_verified"])
            self.assertEqual(claim_path.read_bytes(), before)
            self.assertEqual(sum(row["operation"] == "confirm_once" for row in endpoint.requests), 1)

    async def test_real_mcp_native_unavailable_current_preserves_reason_and_unknown_claim(self) -> None:
        driver, endpoint = self.driver()
        public = driver.take_snapshot_without_native_command_history()["revision"]
        query = "ck3_query_player_rite_creation_action_context_v1"
        write = "ck3_execute_player_rite_creation_action_v1"
        verify = "ck3_verify_player_rite_creation_action_completed_v1"
        async with Client(create_server(driver)) as client:
            missing = await client.session.call_tool(query, {"expected_revision": public,
                "expected_source_rite_id": RITE, "observation": "current_rite"})
            self.assertFalse(missing.is_error, str(missing))
            leaf = missing.structured_content[action.BODY_KEY]
            self.assertEqual(leaf["unavailable_reason"], "synthetic_complete_payload_not_observed")
            self.assertIsNone(leaf["current_rite_poststate"])
            endpoint.preview = synthetic_preview()
            await client.session.call_tool(query, {"expected_revision": public, "expected_source_rite_id": RITE})
            sent = await client.session.call_tool(write, {"operation": "confirm_once", "expected_revision": public,
                "expected_source_rite_id": RITE, "expected_preview_identity": "a" * 64,
                "expected_outcome_kind": "create_faith"})
            self.assertFalse(sent.is_error, str(sent))
            claim_path = next(Path(self.temp.name).rglob("*.claim.json"))
            before = claim_path.read_bytes()
            observed = await client.session.call_tool(verify, {
                "action_request_id": sent.structured_content["action_request_id"], "expected_revision": public})
            self.assertFalse(observed.is_error, str(observed))
            self.assertEqual(observed.structured_content["status"], "poststate_unavailable")
            self.assertEqual(observed.structured_content["unavailable_reason"], "synthetic_complete_payload_not_observed")
            self.assertFalse(observed.structured_content["automatic_retry"])
            self.assertFalse(observed.structured_content["business_outcome_verified"])
            self.assertEqual(claim_path.read_bytes(), before)
            self.assertEqual(list(Path(self.temp.name).rglob("*.completed.json")), [])
            self.assertEqual(sum(row["operation"] == "confirm_once" for row in endpoint.requests), 1)

    async def test_real_mcp_cancel_diagnostic_and_independent_current_rite_read(self) -> None:
        driver, endpoint = self.driver()
        endpoint.poststate = synthetic_poststate(synthetic_preview(), rite=RITE, faith=27)
        public = driver.take_snapshot_without_native_command_history()["revision"]
        async with Client(create_server(driver)) as client:
            cancel = await client.session.call_tool("ck3_execute_player_rite_creation_action_v1", {
                "operation": "cancel_draft", "expected_revision": public, "expected_source_rite_id": RITE})
            self.assertFalse(cancel.is_error, str(cancel))
            self.assertFalse(cancel.structured_content[action.BODY_KEY]["available"])
            self.assertEqual(cancel.structured_content[action.BODY_KEY]["unavailable_reason"],
                "synthetic_complete_payload_not_observed")
            current = await client.session.call_tool("ck3_query_player_rite_creation_action_context_v1", {
                "expected_revision": public, "expected_source_rite_id": RITE, "observation": "current_rite"})
            self.assertFalse(current.is_error, str(current))
            self.assertTrue(current.structured_content["read_only"])
            self.assertEqual(current.structured_content[action.BODY_KEY]["current_rite_poststate"], endpoint.poststate)
            self.assertFalse(current.structured_content["business_outcome_verified"])
            rejected = await client.session.call_tool("ck3_query_player_rite_creation_action_context_v1", {
                "expected_revision": public, "expected_source_rite_id": RITE, "observation": "invented"})
            self.assertTrue(rejected.is_error)
        self.assertEqual([request["operation"] for request in endpoint.requests], ["cancel_draft", "observe_current_rite"])
        self.assertEqual(list(Path(self.temp.name).rglob("*.claim.json")), [])

    async def test_real_mcp_verified_edits_then_new_rite_use_distinct_immutable_claims(self) -> None:
        driver, endpoint = self.driver()
        query = "ck3_query_player_rite_creation_action_context_v1"
        write = "ck3_execute_player_rite_creation_action_v1"
        verify = "ck3_verify_player_rite_creation_action_completed_v1"
        driver.allow_private_player_rite_creation_actions = False
        async with Client(create_server(driver)) as client:
            self.assertNotIn(verify, {tool.name for tool in (await client.session.list_tools()).tools})
        driver.allow_private_player_rite_creation_actions = True
        completed_ids = []
        original_claim_bytes = None
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
            self.assertTrue(tools[verify].annotations.read_only_hint)
            self.assertNotIn("current_rite_poststate", tools[verify].input_schema["properties"])
            for index, (kind, doctrine, name) in enumerate((
                    ("edit_rite", "doctrine_fixture_enabled", "fixture"),
                    ("edit_rite", "doctrine_fixture_none", "fixture"),
                    ("edit_rite", "doctrine_fixture_enabled", "fixture"),
                    ("create_rite", "doctrine_fixture_enabled", "a genuinely different authored Rite"))):
                token = format(index + 10, "064x")
                preview = synthetic_preview(token=token)
                draft = preview[action.BODY_KEY]["draft"]
                draft["actual_outcome_kind"] = kind
                draft["names"]["name"] = name
                draft["selected_doctrines"] = [{"group_key": "doctrine_fixture", "doctrine_key": doctrine}]
                preview[action.BODY_KEY]["full_can"].update(can_edit=kind == "edit_rite", can_create=kind != "edit_rite")
                endpoint.preview = preview
                endpoint.poststate = synthetic_poststate(preview, rite=RITE if kind == "edit_rite" else 92, faith=27)
                public = driver.take_snapshot_without_native_command_history()["revision"]
                read = await client.session.call_tool(query, {"expected_revision": public, "expected_source_rite_id": RITE})
                self.assertFalse(read.is_error, str(read))
                submitted = await client.session.call_tool(write, {"operation": "confirm_once", "expected_revision": public,
                    "expected_source_rite_id": RITE, "expected_preview_identity": token, "expected_outcome_kind": kind})
                self.assertFalse(submitted.is_error, str(submitted))
                request_id = submitted.structured_content["action_request_id"]
                self.assertFalse(submitted.structured_content["business_outcome_verified"])
                confirmed = await client.session.call_tool(verify, {"action_request_id": request_id, "expected_revision": public})
                self.assertFalse(confirmed.is_error, str(confirmed))
                self.assertTrue(confirmed.structured_content["business_outcome_verified"])
                self.assertEqual(confirmed.structured_content["status"], "completed")
                completed_ids.append(request_id)
                first_claim = next(path for path in Path(self.temp.name).rglob("*.claim.json")
                    if json.loads(path.read_text())["predecessor_request_id"] is None)
                if original_claim_bytes is None:
                    original_claim_bytes = first_claim.read_bytes()
                self.assertEqual(first_claim.read_bytes(), original_claim_bytes)
        self.assertEqual(len(set(completed_ids)), 4)
        self.assertEqual(len(list(Path(self.temp.name).rglob("*.claim.json"))), 4)
        self.assertEqual(len(list(Path(self.temp.name).rglob("*.completed.json"))), 4)
        self.assertEqual(sum(request["operation"] == "confirm_once" for request in endpoint.requests), 4)
        self.assertEqual(sum(request["operation"] == "observe_current_rite" for request in endpoint.requests), 4)

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


def consume_native_wire_fixture(path: Path) -> None:
    """Consume actual C++ serializer bytes; this is fixture evidence, never live CK3."""
    raw = path.read_bytes()
    packet = contract.object_map(json.loads(raw), "C++ serializer fixture packet")
    if packet.get("type") != "command_result" or packet.get("ok") is not True:
        raise ValueError("actual C++ command-result fixture required")
    result = contract.object_map(packet.get("result"), "C++ fixture result")
    leaf = contract.object_map(result.get(action.BODY_KEY), "C++ fixture Rite action")
    draft = contract.object_map(leaf.get("draft"), "C++ fixture draft")
    rows = contract.parse_draft_core_tenets(draft)
    if draft["selected_core_slot_count"] != 100 or rows is None or [row["slot_index"] for row in rows] != [0, 50, 99]:
        raise ValueError("C++ fixture lost100 physical slots and sparse native positions")
    payload = contract.submitted_payload_from_draft(draft)
    if contract.parse_submitted_payload(json.loads(json.dumps(payload))) != payload:
        raise ValueError("C++ submitted payload did not roundtrip")
    catalogue = contract.parse_virtue_sin_catalogue(draft.get("virtue_sin_catalogue"),
        scope="draft", rite_id=payload["source_rite_id"])
    virtues, sins = catalogue["virtues"], catalogue["sins"]
    if virtues is None or sins is None or not any(abs(int(row["weight_raw"])) > 2**53 for row in virtues + sins):
        raise ValueError("C++ fixture omitted exact wide native weight strings")
    if contract.parse_virtue_sin_catalogue(json.loads(json.dumps(catalogue)),
            scope="draft", rite_id=payload["source_rite_id"]) != catalogue:
        raise ValueError("C++ native Trait catalogue did not roundtrip")
    current = contract.parse_current_rite_poststate(leaf.get("current_rite_poststate"))
    frame = contract.object_map(leaf.get("frame"), "C++ fixture frame")
    actor = contract.exact_integer(frame.get("played_character_id"), "fixture actor", 1, 0x7FFFFFFF)
    if not contract.poststate_matches_payload(payload, current, actor):
        raise ValueError("C++ independent dense poststate differs from sparse effective payload")
    description = payload["names"]["description"]
    if "\x15" not in description or current["names"] != payload["names"]:
        raise ValueError("C++ legal native formatted description was changed")
    try:
        action.request_fields("set_name_field", payload["source_rite_id"],
            name_field="description", text=description)
    except ValueError:
        pass
    else:
        raise ValueError("SDK accidentally accepted native formatting controls as authored input")
    print(json.dumps({"status": "CPP_SERIALIZER_FIXTURE_CONSUMED", "synthetic_fixture_only": True,
        "machine_id": action._machine_id(), "game_started": False, "business_pass": False,
        "input": {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
        "physical_slot_count": draft["selected_core_slot_count"], "valid_tenet_count": len(rows),
        "native_catalogue_observed": catalogue["observed"], "formatted_description_preserved": True}))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--native-wire":
        if len(sys.argv) != 3:
            raise SystemExit("--native-wire requires the exact fixture path")
        consume_native_wire_fixture(Path(sys.argv[2]))
    else:
        unittest.main()
