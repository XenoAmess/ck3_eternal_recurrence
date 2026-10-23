"""Portable authored-state tests; no native output, process or game is created."""
from __future__ import annotations

from copy import deepcopy
import base64
import hashlib
import json
import tempfile
import importlib.util
from pathlib import Path
from types import SimpleNamespace, ModuleType
from typing import Callable, Protocol, runtime_checkable
from ck3_mod_acceptance_background_types import FilePin
import unittest


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


TOOLS = Path(__file__).resolve().parent
ADAPTER = module("_ordinary_adapter_under_test", TOOLS / "ck3_mod_acceptance_cases/faith_e02_pilgrimage_adapter.py")
QUEUE = module("_ordinary_queue_under_test", TOOLS / "faith_e02_pilgrimage_queue.py")


def frame():
    return {"revision": 9, "native_revision": 7, "date_raw": 53144328, "paused": True, "map_ready": True,
        "source": "injected-dll-named-pipe", "backend_id": "native-headless", "episode_projection": "native_campaign",
        "played_character": {"character_id": 31254, "alive": True, "source": "native"},
        "played_character_gold": 243, "active_event": None, "pending_character_interaction": None,
        "diagnostics": {"bridge_pid": 123, "connection_generation": 2, "hello": {"pid": 123,
            "connection_generation": 2, "ck3_build_match": True,
            "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "expected_ck3_sha256": ADAPTER.EXE_SHA256}}}


def offers():
    common = {"played_character_id": 31254, "date_raw": 53144328, "capture_epoch": 7}
    candidates, routes = [], []
    for province, arrival, cost in ((100, 53144712, 11000000), (200, 53144520, 7000000)):
        candidates.append({"province_id": province, "can_select": True, "location_predicate": {"value": True},
            "same_province_cap_allows": True, "total_cap_allows": True,
            "default_activity_quote": {"affordable": True, "journey_cost_included": False,
                                       "activity_gold_cost_raw": cost}})
        routes.append({**common, "candidate_province_id": province, "available": True,
            "route_valid": True, "outbound_arrival_date_raw": arrival})
    return {"player_pilgrimage_activity_type_terms": {**common, "available": True, "can_plan": True},
        "player_pilgrimage_headless_activity_terms": {**common, "available": True, "faith_id": 13, "rite_id": 0,
            "single_location": True, "configured_phase_count": 1, "journey_cost_included": False,
            "candidates": candidates}, "player_pilgrimage_candidate_routes": routes}


def context():
    return {"case": ADAPTER.CASE, "product": "faith-engine", "run_id": "authored-fixture-only",
        "case_contract": {"schema": "faith-engine-e02-d1-ordinary-pilgrimage-case-v1",
            "case": ADAPTER.CASE, "product": "faith-engine", "machine_id": "fixture-machine",
            "profile": {"enabled_mods": [], "product_files": []}, "expected_actor_character_id": 31254,
            "prior_scene_date_raw": 53144328, "saved_input": {"player_id": 31254, "date_raw": 53144328},
            "policy": {"reserve_gold_raw": 10000000, "max_journey_days": 240, "max_day_requests": 480,
                "max_public_requests": 480,
                "max_events": 128, "one_day_timeout": 60, "quit_reserve_seconds": 120}},
        "case_spec": {"opt_in_player_pilgrimage_execution": True,
            "required_mcp_tools": [ADAPTER.QUERY, ADAPTER.SUBMIT],
            "opt_in_read_only_mcp_tools": [ADAPTER.RELIGION, ADAPTER.IDENTITIES]}}


class Client:
    def __init__(self):
        self.calls, self.evidence = [], {}
        self.capture_points = []
        self.operator_reviewer = "/root-authored-fixture"
        self.started = False
        self.stage = 0
        self.start_timeout = False
        self.start_timeout_effective = False
        self.unknown_positive = False
        self.can_start = True
        self.can_select = True
        self.existing_identity = False
        self.post_pending = False
        self.hosted_missing_after_start = False
        self.review_overrides = {}
        self.stage1_selected = True
        self.stage1_rejected = False
        self.change_selection_after_review = False
        self.open_invoked = True
        self.option_key = "pilgrimage_type_pious"
        self.faith_id, self.rite_id = 13, 0
        self.bad_save_size = False

    def snapshot(self, **kwargs):
        return frame()

    def guard(self, reserve):
        assert reserve >= 90

    def checkpoint(self, name, value):
        if name in self.evidence:
            raise AssertionError("Duplicate evidence: " + name)
        self.evidence[name] = deepcopy(value)

    def root_checkpoint(self, name, request, reserve):
        assert reserve == 120
        self.capture_points.append((name, deepcopy(request)))
        if "before-planner" in name:
            assert not any(row["tool"] == ADAPTER.SUBMIT for row in self.calls)
        if "before-start" in name:
            assert not any(row["args"].get("operation") == "start" for row in self.calls)
        response = {"run_id": request["run_id"], "reviewer": self.operator_reviewer, "status": "complete"}
        if "native_observation" in request:
            image = Path(self.review_image).read_bytes()
            response.update(original_image_directly_reviewed=True,
                original_image={"path": str(self.review_image), "bytes": len(image),
                    "sha256": hashlib.sha256(image).hexdigest()},
                reviewed_native_observation_sha256=ADAPTER.visual_observation_sha256(request["native_observation"]))
            response[request["approval_key"]] = True
            response.update(self.review_overrides.get(request["approval_key"], {}))
        if "stage1-before-confirm" in name:
            assert self.stage == 1
            assert request["native_observation"]["planner"]["selected_option_key"] == self.option_key
            assert not any(row["args"].get("operation") == "confirm" for row in self.calls)
            if self.change_selection_after_review:
                self.stage1_selected = False
        return response

    def identity(self):
        return {"activity_id": 0x12340001, "host_character_id": 31254, "type_key": "activity_pilgrimage",
            "terminal_flags_observed": True, "native_completed": False, "native_invalidated": False,
            "native_completion_stamp_observed": False, "native_completion_stamp_raw": None}

    def execute_plan(self, steps, name):
        step = steps[0]
        self.calls.append(deepcopy(step))
        tool, args = step["tool"], step["args"]
        if tool == "ck3_save_checkpoint":
            raw = b"owned synthetic continuation save; no game queried"
            Path(self.save_path).write_bytes(raw)
            value = {"accepted": True, "step": "save-checkpoint", "checkpoint": {
                "status": "saved", "date_raw": 53144328, "episode_projection": "native_campaign",
                "path": str(self.save_path), "size": True if self.bad_save_size else len(raw),
                "sha256": hashlib.sha256(raw).hexdigest()}}
        elif tool == ADAPTER.RELIGION:
            value = offers()
            value["player_pilgrimage_headless_activity_terms"].update(
                faith_id=self.faith_id, rite_id=self.rite_id)
        elif tool == ADAPTER.IDENTITIES:
            rows = [self.identity()] if (self.started and not self.hosted_missing_after_start) or self.existing_identity else []
            value = {"activity_count": len(rows), "activities": rows}
        else:
            op = args["operation"]
            if op == "start" and self.start_timeout:
                if self.start_timeout_effective:
                    self.started = True
                raise TimeoutError("authored lost ACK")
            if op == "open":
                self.stage = 1
            elif op == "confirm":
                self.stage = 2
            elif op == "select":
                self.stage = 5
            elif op == "start":
                self.started = True
            value = {"operation_status": "observed", "needs_recovery": False, "ledger_state": "idle",
                "invoked": tool == ADAPTER.SUBMIT, "planner": {"stage": self.stage, "selected_option_key": self.option_key,
                    "destination_province_id": 200 if self.stage == 5 else 0, "can_select": self.can_select,
                    "can_progress": True}}
            if op == "open":
                # Actual Open reports invocation/stage/readiness, not selection.
                value["planner"]["selected_option_key"] = None
                value["invoked"] = self.open_invoked
            if op == "read" and args.get("read_stage") == 1:
                value["planner"]["selected_option_key"] = self.option_key if self.stage1_selected is True else self.stage1_selected
                if self.stage1_rejected:
                    value["operation_status"] = "rejected"
            if op == "quote":
                value["quote"] = {"observed": True, "planning_stage": 5, "final_can_start_observed": True,
                    "final_can_start": self.can_start, "unknown_positive_configured_cost": self.unknown_positive,
                    "selected_option": {"key": self.option_key}}
            elif op == "post":
                pending = self.post_pending or not self.started
                value.update(operation_status="post_pending" if pending else "identity_observed",
                             new_identity=None if pending else self.identity())
        return [{"id": name, "ok": True, "result": value}]


JSONObject = dict[str, object]


def resume_object(value: object) -> JSONObject:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError("authored resume fixture requires a JSON object")
    return value


def resume_write(root: Path, name: str, value: object) -> FilePin:
    path = root / name
    raw = json.dumps(value, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def resume_contract(ctx: JSONObject) -> JSONObject:
    return resume_object(ctx["case_contract"])


def resume_payload(ctx: JSONObject) -> JSONObject:
    return resume_object(resume_contract(ctx)["resume_existing"])


class ResumeClient:
    """Typed actual result envelopes; no planner, process or game is created."""
    def __init__(self, output: Path, identity: JSONObject) -> None:
        self.output = output
        make_frame: Callable[[], object] = frame
        self.current = resume_object(make_frame())
        hello = resume_object(resume_object(self.current["diagnostics"])["hello"])
        hello["expected_ck3_version"] = "1.20.0.4"
        self.rows = [deepcopy(identity)]
        self.faith_id = 50
        self.rite_id: int | None = 13
        self.bad_scope = False
        self.after_override: JSONObject = {}
        self.calls: list[JSONObject] = []
        self.evidence: dict[str, JSONObject] = {}
        self.capture_points: list[str] = []
        self.operator_reviewer = "/root-authored-fixture"
        self.save_path = output / "return.ck3"

    def snapshot(self, **kwargs: bool) -> JSONObject:
        return deepcopy(self.current)

    def guard(self, reserve: int = 90) -> JSONObject:
        if reserve < 90:
            raise AssertionError("original Quit reserve must remain intact")
        return {"fixture_only": True}

    def remaining(self) -> float:
        return 5000

    def checkpoint(self, name: str, value: JSONObject) -> Path:
        self.evidence[name] = deepcopy(value)
        path = self.output / (name + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def execute_plan(self, steps: list[JSONObject], name: str) -> list[JSONObject]:
        if len(steps) != 1:
            raise AssertionError("one actual public control required")
        step = steps[0]
        self.calls.append(deepcopy(step))
        before = deepcopy(self.current)
        tool = step["tool"]
        if tool == "ck3_save_checkpoint":
            raw = b"owned synthetic continuation save; no game queried"
            self.save_path.write_bytes(raw)
            saved: JSONObject = {"accepted": True, "step": "save-checkpoint", "checkpoint": {
                "status": "saved", "date_raw": before["date_raw"], "episode_projection": "native_campaign",
                "path": str(self.save_path), "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}
            return [{"id": name, "ok": True, "result": saved}]
        args = resume_object(step["args"])
        if args["expected_revision"] != before["revision"]:
            raise AssertionError("resume query must use its actual current revision")
        native = before["native_revision"]
        # Keep a genuinely integer native producer result even when testing a
        # malformed outer frame containing bool/float with the same value.
        if not isinstance(native, (int, float)):
            raise AssertionError("fixture native revision must be numeric")
        value: JSONObject = {"read_only": True, "queried_revision": before["revision"],
            "snapshot_revision": int(native), "date_raw": before["date_raw"], "played_character_id": 31254}
        if tool == ADAPTER.RELIGION:
            value.update(available=True, faith_id=self.faith_id, rite_id=self.rite_id)
        elif tool == ADAPTER.IDENTITIES:
            value.update(schema="ck3_12004_player_pilgrimage_activities_v1",
                scope="currently-hosted-by-current-player", activity_type_key="activity_pilgrimage",
                absence_is_completion=False, activity_count=len(self.rows), activities=deepcopy(self.rows))
        else:
            raise AssertionError("resume must not call a planner or mutation")
        if self.bad_scope:
            value["queried_revision"] = True
        after = self.snapshot(require_event_free=False)
        after.update(self.after_override)
        row: JSONObject = {"id": name, "plan": deepcopy(step), "ok": True, "result": value, "after_snapshot": after}
        self.checkpoint(name + ".actual-results", {"rows": [row]})
        return [row]


@runtime_checkable
class ResumeModalPort(Protocol):
    current: JSONObject
    typed_context: Callable[[JSONObject], JSONObject]
    operator_reviewer: str
    event_key: str
    displayed: list[JSONObject]
    snapshot_count: int

    def snapshot(self, **kwargs: bool) -> object: ...
    def validate_frame(self, value: object, **kwargs: bool) -> object: ...
    def execute_plan(self, steps: list[JSONObject], name: str) -> object: ...
    def root_checkpoint(self, name: str, request: JSONObject, reserve: int = 90) -> object: ...


class SharedResumeClient(ResumeClient):
    """Compose the existing public CaseClient modal fixture, without copying its producer."""
    def __init__(self, output: Path, identity: JSONObject) -> None:
        super().__init__(output, identity)
        from tools.test_faith_e02_pilgrimage_event_policy import ModalClient, option
        factory: Callable[[Path], object] = ModalClient
        port = factory(output)
        if not isinstance(port, ResumeModalPort):
            raise ValueError("existing modal fixture lacks its actual public interface")
        self.modal = port
        option_factory: Callable[[int, int, str], object] = option
        self.modal.displayed = [resume_object(option_factory(0, 0, "actual first fixture option"))]
        self.modal.snapshot_count = 1
        self.current.update(snapshot_id="synthetic:9", episode_run_id=None)
        self.modal.current = self.current
        self.operator_reviewer = self.modal.operator_reviewer
        original = self.modal.typed_context
        def typed_context(current: JSONObject) -> JSONObject:
            value = resume_object(original(current))
            value["root_scope"] = {"status": "available", "raw_type_index": 4, "type_key": "character", "subtype": 0,
                "typed_identity": {"status": "available", "kind": "character", "character_id": 31254}}
            return value
        self.modal.typed_context = typed_context
        self.stage_injected = False
        self.next_event_key = "pilgrimage.7000"
        self.active_key: str | None = None

    def snapshot(self, **kwargs: bool) -> JSONObject:
        return resume_object(self.modal.snapshot(**kwargs))

    def validate_frame(self, value: object, **kwargs: bool) -> JSONObject:
        return resume_object(self.modal.validate_frame(value, **kwargs))

    def root_checkpoint(self, name: str, request: JSONObject, reserve: int = 90) -> JSONObject:
        return resume_object(self.modal.root_checkpoint(name, request, reserve))

    def install_phase(self, key: str, instance: int) -> None:
        # Existing fixture's endpoint fields, not production/event policy code.
        self.modal.event_key = key
        self.active_key = key
        self.current["active_event"] = {"instance_id": instance, "option_count": 1,
            "options": [{"index": 0, "option_number": 1, "enabled": True}]}

    def execute_plan(self, steps: list[JSONObject], name: str) -> list[JSONObject]:
        tool = steps[0]["tool"]
        if tool in {ADAPTER.RELIGION, ADAPTER.IDENTITIES}:
            rows = super().execute_plan(steps, name)
            if tool == ADAPTER.IDENTITIES and not name.startswith("pilgrimage-resume-") and not self.stage_injected:
                self.stage_injected = True
                self.install_phase(self.next_event_key, 21)
                rows[0]["after_snapshot"] = self.snapshot(require_event_free=False)
                self.checkpoint(name + ".actual-results", {"rows": rows})
            return rows
        if tool == "ck3_save_checkpoint":
            return super().execute_plan(steps, name)
        self.calls.extend(deepcopy(steps))
        raw = self.modal.execute_plan(steps, name)
        if not isinstance(raw, list):
            raise ValueError("existing public modal fixture returned malformed rows")
        rows = [resume_object(row) for row in raw]
        if tool == "ck3_select_event_option" and self.active_key == "pilgrimage.7000":
            self.install_phase("pilgrimage.9001", 22)
        return rows


class WorkflowTests(unittest.TestCase):
    images: tempfile.TemporaryDirectory[str]
    original_sibling: Callable[[Path, str], ModuleType]

    def test_v2_extended_finite_policy_reaches_journey_consumer_and_preserves_legacy_caps(self) -> None:
        journey = module("_finite_policy_journey", TOOLS / "ck3_mod_acceptance_cases/faith_e02_pilgrimage_journey.py")
        ctx = context()
        ctx["case"] = ADAPTER.MECHANISM_CASE
        contract = ctx["case_contract"]
        contract.update(case=ADAPTER.MECHANISM_CASE, schema="faith-engine-e02-pilgrimage-mechanism-case-v2",
                        expected_faith_id=50, expected_rite_id=13, option_key="pilgrimage_type_hajj")
        contract["policy"].update(max_journey_days=730, max_day_requests=1024, max_public_requests=4096)
        validated = ADAPTER.validate_contract(ctx)
        encoded = json.loads(json.dumps(ADAPTER.journey_limits(validated["policy"])))
        self.assertEqual(journey._limits(encoded, case_id=ADAPTER.MECHANISM_CASE)["max_days"], 730)
        self.assertEqual(journey._limits(encoded, case_id=ADAPTER.MECHANISM_CASE)["quit_reserve_seconds"], 120)
        for key, wrong in (("max_journey_days", 731), ("max_journey_days", True),
                           ("max_journey_days", 730.0), ("max_public_requests", 4097),
                           ("max_day_requests", 1025), ("quit_reserve_seconds", 89)):
            bad = deepcopy(ctx)
            bad["case_contract"]["policy"][key] = wrong
            with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                ADAPTER.validate_contract(bad)
        for key, wrong in (("max_journey_days", 367), ("max_public_requests", 1025)):
            legacy = context()
            legacy["case_contract"]["policy"][key] = wrong
            with self.subTest(legacy=key), self.assertRaises(ValueError):
                ADAPTER.validate_contract(legacy)
        with self.assertRaises(journey.JourneyStop):
            journey._limits({"max_days": 367}, case_id=ADAPTER.CASE)
        with self.assertRaises(journey.JourneyStop):
            journey._limits({"max_days": 731}, case_id=ADAPTER.MECHANISM_CASE)
        controller = object.__new__(journey._Journey)
        controller.limits = {**journey._limits(encoded, case_id=ADAPTER.MECHANISM_CASE),
                             "quit_reserve_seconds": 600}
        controller.client = SimpleNamespace(public_requests_used=4096, public_requests_cap=4096,
                                            remaining=lambda: 10000, guard=lambda: None)
        with self.assertRaises(journey.JourneyStop) as exhausted:
            controller.guard()
        self.assertEqual(exhausted.exception.status, "PARTIAL_PUBLIC_REQUEST_CAP")
        controller.client.public_requests_used = 0
        controller.client.remaining = lambda: 635
        with self.assertRaises(journey.JourneyStop) as reserve:
            controller.guard(35)
        self.assertEqual(reserve.exception.status, "PARTIAL_QUIT_RESERVE")

    @classmethod
    def setUpClass(cls):
        cls.images = tempfile.TemporaryDirectory(prefix="authored-root-review-")
        Client.review_image = Path(cls.images.name) / "authored-synthetic-not-game.png"
        Client.review_image.write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="))
        Client.save_path = Path(cls.images.name) / "owned-continuation.ck3"

    @classmethod
    def tearDownClass(cls):
        cls.images.cleanup()

    def setUp(self):
        self.original_sibling = ADAPTER.sibling
        ADAPTER.sibling = lambda path, name: (QUEUE if path.name.endswith("queue.py") else
            SimpleNamespace(observe_milestone=lambda *args, **kwargs: None,
                run_journey=lambda *args, **kwargs: {"status": "AUTHORED_JOURNEY_RESULT", "terminal_observed": False}))
        self.addCleanup(setattr, ADAPTER, "sibling", self.original_sibling)

    def starts(self, client):
        return [s for s in client.calls if s["tool"] == ADAPTER.SUBMIT and s["args"]["operation"] == "start"]

    def resume_fixture(self) -> tuple[JSONObject, JSONObject]:
        """Pinned synthetic predecessor, not a game save or runtime claim."""
        root = Path(self.images.name)
        source = resume_write(root, "resume-source-index.json", {"source_commit": "a" * 40, "files": {}})
        manifest = resume_write(root, "resume-manifest.json", {"machine_id": "fixture-machine", "source_commit": "a" * 40,
            "source_index": {"path_key": "source_index", "bytes": source["bytes"], "sha256": source["sha256"]}})
        runtime = resume_write(root, "resume-runtime.json", {"schema": "ck3-mod-acceptance-runtime-v1", "machine_id": "fixture-machine",
            "manifest": manifest, "paths": {"source_index": source["path"]}})
        identity: JSONObject = {"activity_id": 0, "host_character_id": 31254, "type_key": "activity_pilgrimage"}
        origin = resume_write(root, "resume-start-observed.json", {"run_id": "previous-authored-fixture", "machine_id": "fixture-machine",
            "binding": {"run_id": "previous-authored-fixture", "machine_id": "fixture-machine", "actor_character_id": 31254,
                "bridge_pid": 122, "connection_generation": 1, "episode_run_id": None},
            "hosted_identity": identity, "native_ledger_state_reconciled": True,
            "start_response": {"invoked": True, "operation": "start", "played_character_id": 31254,
                "date_raw": 53144328 - 240, "planner": {"selected_option_key": "pilgrimage_type_hajj", "destination_province_id": 6223}}})
        contract: JSONObject = {"schema": "faith-engine-e02-pilgrimage-mechanism-case-v2", "case": ADAPTER.MECHANISM_CASE,
            "product": "faith-engine", "machine_id": "fixture-machine", "profile": {"enabled_mods": [], "product_files": []},
            "expected_actor_character_id": 31254, "prior_scene_date_raw": 53144328,
            "saved_input": {"player_id": 31254, "date_raw": 53144328},
            "expected_faith_id": 50, "expected_rite_id": 13, "option_key": "pilgrimage_type_hajj", "preferred_destination_id": 6223,
            "policy": {"reserve_gold_raw": 10000000, "max_journey_days": 240, "max_day_requests": 480, "max_public_requests": 480,
                "max_events": 128, "one_day_timeout": 60, "quit_reserve_seconds": 120},
            "entry_mode": "resume_existing", "resume_existing": {"predecessor_run_id": "previous-authored-fixture",
                "original_start": origin, "predecessor_runtime": runtime, "activity": identity, "consumed_events": []}}
        ctx: JSONObject = {"case": ADAPTER.MECHANISM_CASE, "product": "faith-engine", "run_id": "authored-fixture-only",
            "case_contract": contract, "case_spec": {"opt_in_player_pilgrimage_execution": True,
                "required_mcp_tools": [ADAPTER.QUERY, ADAPTER.SUBMIT],
                "opt_in_read_only_mcp_tools": [ADAPTER.RELIGION, ADAPTER.IDENTITIES]}}
        return ctx, identity

    def test_resume_existing_reuses_journey_without_any_planner_start_path(self) -> None:
        ctx, identity = self.resume_fixture()
        client = ResumeClient(Path(self.images.name), identity)
        value = resume_object(ADAPTER.run_case(ctx, client))
        self.assertEqual(value["status"], "AUTHORED_JOURNEY_RESULT")
        self.assertTrue(value["hosted_identity_observed"])
        self.assertFalse(value["start_invoked"])
        self.assertFalse(any(row["tool"] in {ADAPTER.QUERY, ADAPTER.SUBMIT} for row in client.calls))
        self.assertEqual(client.capture_points, [])
        self.assertEqual(value["hosted_identity"], identity)
        proof = client.evidence["pilgrimage-resume-native-identity"]
        self.assertEqual(proof["prior_elapsed_hours"], 240)
        self.assertEqual(proof["predecessor_source_commit"], "a" * 40)
        self.assertEqual([r["tool"] for r in client.calls], [ADAPTER.RELIGION, ADAPTER.IDENTITIES])

    def test_resume_contract_roundtrip_and_rejects_missing_null_extra_and_noninteger_identities(self) -> None:
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_resume
        ctx, _ = self.resume_fixture()
        original = pilgrimage_resume(ctx["case_contract"])
        self.assertEqual(original, pilgrimage_resume(json.loads(json.dumps(ctx["case_contract"]))))
        for field in ("original_start", "predecessor_runtime", "activity", "consumed_events", "predecessor_run_id"):
            for disposition in ("missing", "null"):
                bad = deepcopy(ctx)
                if disposition == "missing": del resume_payload(bad)[field]
                else: resume_payload(bad)[field] = None
                with self.subTest(field=field, disposition=disposition), self.assertRaises(ValueError): ADAPTER.validate_contract(bad)
        for field, wrong in (("activity_id", True), ("activity_id", 0.0), ("host_character_id", True), ("type_key", "other")):
            bad = deepcopy(ctx); resume_object(resume_payload(bad)["activity"])[field] = wrong
            with self.subTest(field=field, wrong=wrong), self.assertRaises(ValueError): ADAPTER.validate_contract(bad)
        for wrong_mode in (None, True, "other", "new_start"):
            bad = deepcopy(ctx); resume_contract(bad)["entry_mode"] = wrong_mode
            with self.subTest(mode=wrong_mode), self.assertRaises(ValueError): ADAPTER.validate_contract(bad)
        bad = deepcopy(ctx); resume_payload(bad)["extra"] = 1
        with self.assertRaises(ValueError): ADAPTER.validate_contract(bad)
        bad = deepcopy(ctx); resume_contract(bad)["case"] = ADAPTER.CASE
        with self.assertRaises(ValueError): pilgrimage_resume(bad["case_contract"])

    def test_resume_refuses_wrong_cold_owner_faith_rite_scope_modal_or_nonunique_identity_before_journey(self) -> None:
        for wrong in ("pid", "actor", "date", "faith", "rite", "scope", "modal", "missing", "multiple", "activity", "bool_id"):
            ctx, identity = self.resume_fixture()
            client = ResumeClient(Path(self.images.name), identity)
            if wrong == "pid":
                diagnostics = resume_object(client.current["diagnostics"])
                diagnostics["bridge_pid"] = 122; resume_object(diagnostics["hello"])["pid"] = 122
            elif wrong == "actor": resume_object(client.current["played_character"])["character_id"] = 7
            elif wrong == "date": client.current["date_raw"] = 53144329
            elif wrong == "faith": client.faith_id = 51
            elif wrong == "rite": client.rite_id = None
            elif wrong == "scope": client.bad_scope = True
            elif wrong == "modal": client.current["active_event"] = {"instance_id": 14}
            elif wrong == "missing": client.rows = []
            elif wrong == "multiple": client.rows *= 2
            elif wrong == "activity": client.rows[0]["activity_id"] = 1
            elif wrong == "bool_id": client.rows[0]["activity_id"] = False
            with self.subTest(wrong=wrong):
                try: value = resume_object(ADAPTER.run_case(ctx, client))
                except ValueError: value = {"status": "pre-frame-refused"}
                self.assertNotEqual(value["status"], "AUTHORED_JOURNEY_RESULT")
                self.assertFalse(any(r["tool"] in {ADAPTER.QUERY, ADAPTER.SUBMIT, "ck3_select_event_option"} for r in client.calls))

    def test_resume_rejects_noninteger_before_and_after_revisions_and_does_not_copy_native_stamp(self) -> None:
        for position in ("before", "after"):
            for field in ("revision", "native_revision"):
                for wrong in (True, 7.0):
                    ctx, identity = self.resume_fixture()
                    client = ResumeClient(Path(self.images.name), identity)
                    if position == "before": client.current[field] = wrong
                    else: client.after_override[field] = wrong
                    with self.subTest(position=position, field=field, wrong=wrong):
                        result = resume_object(ADAPTER.run_case(ctx, client))
                        self.assertNotEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
                        self.assertNotIn("pilgrimage-resume-native-identity", client.evidence)
        ctx, identity = self.resume_fixture()
        client = ResumeClient(Path(self.images.name), identity)
        client.rows[0].update(native_completion_stamp_raw=244046518620802472, native_completed=False, native_invalidated=False)
        result = resume_object(ADAPTER.run_case(ctx, client))
        self.assertEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
        self.assertEqual(result["hosted_identity"], identity)
        self.assertNotIn("244046518620802472", json.dumps(result))

    def test_resume_rejects_tampered_predecessor_source_before_any_native_control(self) -> None:
        ctx, identity = self.resume_fixture()
        pin = resume_object(resume_payload(ctx)["predecessor_runtime"])
        Path(str(pin["path"])).write_text("{}", encoding="utf-8")
        client = ResumeClient(Path(self.images.name), identity)
        with self.assertRaisesRegex(ValueError, "evidence bytes differ"): ADAPTER.run_case(ctx, client)
        self.assertEqual(client.calls, [])

    def consumed_resume_fixture(self, ctx: JSONObject) -> FilePin:
        root = Path(self.images.name)
        old_frame: JSONObject = {"date_raw": 53144328, "played_character": {"character_id": 31254}, "active_event": None,
            "diagnostics": {"bridge_pid": 122, "connection_generation": 1, "hello": {"pid": 122, "connection_generation": 1}}}
        query = resume_write(root, "prior-3010-query.json", {"rows": [{"ok": True, "after_snapshot": old_frame,
            "result": {"accepted": True, "current_event_window_context": {"status": "available", "event_definition_key": "hajj.3010",
                "current_event_instance_id": 14, "date_raw": 53144328}}}]})
        selected = resume_write(root, "prior-3010-selected.json", {"rows": [{"ok": True,
            "plan": {"tool": "ck3_select_event_option", "args": {"event_instance_id": 14, "option_number": 1}},
            "result": {"accepted": True, "event_selection": {"status": "event_instance_advanced", "postcondition_verified": True,
                "old_event_instance_id": 14, "bridge_pid": 122, "connection_generation": 1, "selected_option_number": 1}},
            "after_snapshot": old_frame}]})
        resume_payload(ctx)["consumed_events"] = [{"event_id": "hajj.3010", "query": query, "selection": selected}]
        return selected

    def test_resume_consumed_postcondition_roundtrip_rejects_wrong_postcondition(self) -> None:
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_resume
        ctx, _ = self.resume_fixture(); pin = self.consumed_resume_fixture(ctx)
        self.assertEqual(pilgrimage_resume(ctx["case_contract"]), pilgrimage_resume(json.loads(json.dumps(ctx["case_contract"]))))
        ADAPTER.validate_contract(ctx)
        original = resume_object(json.loads(Path(pin["path"]).read_bytes()))
        for field, wrong in (("postcondition_verified", False), ("bridge_pid", 999), ("connection_generation", True), ("old_event_instance_id", True)):
            bad = deepcopy(original)
            rows = bad["rows"]
            if not isinstance(rows, list): raise AssertionError("fixture rows changed")
            result = resume_object(resume_object(rows[0])["result"])
            resume_object(result["event_selection"])[field] = wrong
            changed = resume_write(Path(self.images.name), "prior-3010-selected.json", bad)
            pin.update(changed)
            with self.subTest(field=field), self.assertRaises(ValueError): ADAPTER.validate_contract(ctx)
        for kind in ("active_missing", "active_bool", "active_wrong", "diag_missing", "pid_bool", "pid_wrong", "hello_wrong"):
            bad = deepcopy(original)
            rows = bad["rows"]
            if not isinstance(rows, list): raise AssertionError("fixture rows changed")
            after = resume_object(resume_object(rows[0])["after_snapshot"])
            if kind == "active_missing": del after["active_event"]
            elif kind == "active_bool": after["active_event"] = False
            elif kind == "active_wrong": after["active_event"] = {"instance_id": 19, "option_count": True, "options": []}
            elif kind == "diag_missing": del after["diagnostics"]
            elif kind == "pid_bool": resume_object(after["diagnostics"])["bridge_pid"] = True
            elif kind == "pid_wrong": resume_object(after["diagnostics"])["bridge_pid"] = 999
            elif kind == "hello_wrong": resume_object(resume_object(after["diagnostics"])["hello"])["connection_generation"] = 2
            changed = resume_write(Path(self.images.name), "prior-3010-selected.json", bad)
            pin.update(changed)
            with self.subTest(kind=kind), self.assertRaises(ValueError): ADAPTER.validate_contract(ctx)

    def test_resume_real_journey_consumes_return_and_shared_save_tail_once_without_start_or_3010(self) -> None:
        ctx, identity = self.resume_fixture(); self.consumed_resume_fixture(ctx)
        ctx["shared_source_root"] = str(TOOLS.parent)
        resume_contract(ctx)["scope"] = {"new_save_allowed": True}
        resume_object(resume_contract(ctx)["saved_input"])["save"] = str(Path(self.images.name) / "immutable.ck3")
        spec = resume_object(ctx["case_spec"])
        spec["required_mcp_tools"] = [ADAPTER.QUERY, ADAPTER.SUBMIT, "ck3_save_checkpoint"]
        client = SharedResumeClient(Path(self.images.name), identity)
        ADAPTER.sibling = self.original_sibling
        value = resume_object(ADAPTER.run_case(ctx, client))
        self.assertEqual(value["status"], "JOURNEY_CONCLUSION_AND_RETURN_EVENT_OBSERVED", value.get("failure") or value.get("journey"))
        journey = resume_object(value["journey"])
        self.assertEqual(resume_object(journey["limits"])["max_days"], 230)
        self.assertTrue(resume_object(value["continuation_save"])["file_bytes_verified"])
        receipts = journey["event_receipts"]
        if not isinstance(receipts, list): raise AssertionError("actual journey event receipts missing")
        self.assertEqual([resume_object(r)["event_definition_key"] for r in receipts], ["pilgrimage.7000", "pilgrimage.9001"])
        self.assertFalse(value["start_invoked"])
        self.assertEqual(sum(r["tool"] == "ck3_save_checkpoint" for r in client.calls), 1)
        verify_context = {**ctx, "output": str(self.images.name)}
        self.assertEqual(resume_object(ADAPTER.verify_case(verify_context))["status"], value["status"])
        with tempfile.TemporaryDirectory() as directory:
            blocked = SharedResumeClient(Path(directory), identity)
            blocked.next_event_key = "hajj.3010"
            result = resume_object(ADAPTER.run_case(ctx, blocked))
            self.assertEqual(result["status"], "PARTIAL_EVENT_NO_REPLAY", result)
            self.assertFalse(any(r["tool"] == "ck3_select_event_option" for r in blocked.calls))

    def test_v2_hajj_and_worldly_use_same_producer_adapter_and_all_planner_consumers(self):
        for key in ("pilgrimage_type_hajj", "pilgrimage_type_worldly"):
            ctx = context()
            ctx["case"] = ADAPTER.MECHANISM_CASE
            ctx["case_contract"].update(case=ADAPTER.MECHANISM_CASE,
                schema="faith-engine-e02-pilgrimage-mechanism-case-v2",
                expected_faith_id=50, expected_rite_id=13, option_key=key)
            client = Client()
            client.option_key, client.faith_id, client.rite_id = key, 50, 13
            result = ADAPTER.run_case(ctx, client)
            self.assertEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
            self.assertEqual(len(self.starts(client)), 1)
            planner_calls = [row for row in client.calls if row["tool"] in {ADAPTER.QUERY, ADAPTER.SUBMIT}]
            self.assertTrue(planner_calls)
            self.assertTrue(all(row["args"]["option_key"] == key for row in planner_calls))

    def test_v2_wrong_faith_or_selected_option_cannot_reach_start(self):
        ctx = context()
        ctx["case"] = ADAPTER.MECHANISM_CASE
        ctx["case_contract"].update(case=ADAPTER.MECHANISM_CASE,
            schema="faith-engine-e02-pilgrimage-mechanism-case-v2",
            expected_faith_id=50, expected_rite_id=13, option_key="pilgrimage_type_hajj")
        for matching_faith in (False, True):
            client = Client()
            if matching_faith:
                client.faith_id, client.rite_id = 50, 13
            result = ADAPTER.run_case(ctx, client)
            self.assertEqual(result["status"], "capability_or_legality_blocked")
            self.assertEqual(self.starts(client), [])

    def test_v2_return_save_reads_actual_file_and_never_retries_invalid_metadata(self):
        ctx = context()
        ctx["case"] = ADAPTER.MECHANISM_CASE
        ctx["case_contract"].update(case=ADAPTER.MECHANISM_CASE,
            schema="faith-engine-e02-pilgrimage-mechanism-case-v2",
            expected_faith_id=13, expected_rite_id=0, option_key="pilgrimage_type_pious",
            scope={"new_save_allowed": True})
        ctx["case_contract"]["saved_input"]["save"] = str(Path(Client.save_path).with_name("immutable-source.ck3"))
        ctx["case_spec"]["required_mcp_tools"].append("ck3_save_checkpoint")
        ADAPTER.sibling = lambda path, name: (QUEUE if path.name.endswith("queue.py") else
            SimpleNamespace(observe_milestone=lambda *args, **kwargs: None,
                run_journey=lambda *args: {"status": "AUTHORED_RETURN", "return_observed": True,
                                          "return_event_chain_complete": True}))
        for bad_size in (False, True):
            client = Client(); client.bad_save_size = bad_size
            result = ADAPTER.run_case(ctx, client)
            self.assertEqual(sum(row["tool"] == "ck3_save_checkpoint" for row in client.calls), 1)
            if bad_size:
                self.assertNotIn("continuation_save", result)
                self.assertIn("file differs", result["failure"])
            else:
                self.assertTrue(result["continuation_save"]["file_bytes_verified"])
                self.assertFalse(result["continuation_save"]["reload_business_qualified"])

    def test_v2_identity_runtime_types_and_json_roundtrip(self):
        import json
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_identity
        data = context()["case_contract"]
        data.update(case=ADAPTER.MECHANISM_CASE, schema="faith-engine-e02-pilgrimage-mechanism-case-v2",
            expected_faith_id=50, expected_rite_id=None, option_key="pilgrimage_type_hajj")
        self.assertEqual(pilgrimage_identity(data), pilgrimage_identity(json.loads(json.dumps(data))))
        for key, wrong in (("expected_faith_id", True), ("expected_actor_character_id", 31254.0),
                           ("prior_scene_date_raw", True), ("expected_rite_id", False), ("option_key", None)):
            bad = deepcopy(data); bad[key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError):
                pilgrimage_identity(bad)
        for key in ("expected_rite_id", "expected_faith_id", "option_key"):
            bad = deepcopy(data); del bad[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                pilgrimage_identity(bad)

    def test_successful_finite_plan_has_single_start_intent_independent_identity_and_journey(self):
        client = Client()
        value = ADAPTER.run_case(context(), client)
        self.assertEqual(value["status"], "AUTHORED_JOURNEY_RESULT")
        self.assertTrue(value["hosted_identity_observed"])
        self.assertEqual(len(self.starts(client)), 1)
        self.assertEqual(self.starts(client)[0]["args"]["reserve_gold_raw"], 10000000)
        self.assertIn("ordinary-pilgrimage-start-once-intent", client.evidence)
        self.assertFalse(value["payment_total_proven"])
        self.assertFalse(value["business_pass"])
        self.assertEqual([row[0] for row in client.capture_points], [
            "ordinary-pilgrimage-record-before-planner", "ordinary-pilgrimage-review-stage1-before-confirm",
            "ordinary-pilgrimage-record-quote-before-start",
            "ordinary-pilgrimage-start-observed-take"])

    def test_start_timeout_never_resends_or_advances_journey(self):
        client = Client(); client.start_timeout = True
        value = ADAPTER.run_case(context(), client)
        self.assertEqual(len(self.starts(client)), 1)
        self.assertTrue(value["needs_recovery"])
        self.assertEqual(value["status"], "start_outcome_unknown")
        self.assertIsNone(value["journey"])

    def test_lost_start_ack_after_effect_continues_readonly_post_and_journey_without_retry(self):
        client = Client(); client.start_timeout = True; client.start_timeout_effective = True
        value = ADAPTER.run_case(context(), client)
        self.assertEqual(len(self.starts(client)), 1)
        self.assertTrue(value["start_acknowledgement_missing"])
        self.assertTrue(value["hosted_identity_observed"])
        self.assertTrue(value["native_ledger_state_reconciled"])
        self.assertEqual(value["status"], "AUTHORED_JOURNEY_RESULT")
        self.assertFalse(value["needs_recovery"])
        self.assertIn("ordinary-pilgrimage-post-start-wallet-observation", client.evidence)

    def test_root_capture_response_is_bound_to_run_reviewer_and_complete_status(self):
        for field, value in (("run_id", "foreign"), ("reviewer", "foreign"), ("status", "pending")):
            client = Client(); ctx = context()
            response = {"run_id": ctx["run_id"], "reviewer": client.operator_reviewer, "status": "complete"}
            response[field] = value
            client.root_checkpoint = lambda *args, **kwargs: response
            with self.assertRaisesRegex(ValueError, "foreign or incomplete"):
                ADAPTER.capture_checkpoint(ctx, client, "test", {})

    def test_initial_native_interruption_is_drained_before_planner_actions(self):
        client = Client()
        calls = []
        snapshot_count = [0]
        def snapshot(**kwargs):
            snapshot_count[0] += 1
            current = frame()
            if snapshot_count[0] == 1:
                current["active_event"] = {"instance_id": 99}
            return current
        def drain(*args):
            calls.append("drain")
            self.assertEqual(client.calls, [])
            return {"status": "INTERRUPTIONS_DRAINED", "last_frame": frame()}
        client.snapshot = snapshot
        ADAPTER.sibling = lambda path, name: (QUEUE if path.name.endswith("queue.py") else SimpleNamespace(
            drain_interruptions=drain,
            observe_milestone=lambda *args, **kwargs: None,
            run_journey=lambda *args: {"status": "AUTHORED_JOURNEY_RESULT"}))
        result = ADAPTER.run_case(context(), client)
        self.assertEqual(calls, ["drain"])
        self.assertEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
        self.assertEqual(len(self.starts(client)), 1)

    def test_unknown_positive_resource_prevents_start(self):
        client = Client(); client.unknown_positive = True
        value = ADAPTER.run_case(context(), client)
        self.assertEqual(self.starts(client), [])
        self.assertFalse(value["start_intent_written"])

    def test_final_canstart_false_prevents_start(self):
        client = Client(); client.can_start = False
        ADAPTER.run_case(context(), client)
        self.assertEqual(self.starts(client), [])

    def test_current_native_canselect_false_prevents_selection_and_start(self):
        client = Client(); client.can_select = False
        ADAPTER.run_case(context(), client)
        self.assertEqual(self.starts(client), [])
        self.assertFalse(any(s["args"].get("operation") == "select" for s in client.calls))

    def test_existing_hosted_identity_prevents_planner_actions(self):
        client = Client(); client.existing_identity = True
        ADAPTER.run_case(context(), client)
        self.assertEqual(len(client.calls), 1)

    def test_pending_post_is_bounded_and_never_advances_journey(self):
        client = Client(); client.post_pending = True; client.hosted_missing_after_start = True
        value = ADAPTER.run_case(context(), client)
        self.assertEqual(len(self.starts(client)), 1)
        self.assertEqual(sum(s["args"].get("operation") == "post" for s in client.calls), 4)
        self.assertTrue(value["needs_recovery"])
        self.assertIsNone(value["journey"])

    def test_fresh_candidates_are_ranked_without_treating_activity_quote_as_journey_total(self):
        result = ADAPTER.choose_destination(offers(), 31254, 53144328)
        self.assertEqual(result["province_id"], 200)
        self.assertFalse(result["journey_cost_known"])
        self.assertFalse(result["can_start_inferred"])

    def test_stale_or_wrong_rite_offers_are_rejected(self):
        for field, value in (("date_raw", 1), ("rite_id", 5)):
            data = offers(); data["player_pilgrimage_headless_activity_terms"][field] = value
            with self.assertRaises(ValueError):
                ADAPTER.choose_destination(data, 31254, 53144328)

    def test_same_actor_with_changed_process_is_rejected(self):
        c = context(); before = frame(); after = frame()
        binding = ADAPTER.frame_binding(before, c, 31254)
        after["diagnostics"]["hello"]["pid"] = 999
        with self.assertRaises(ValueError):
            ADAPTER.frame_binding(after, c, 31254)
        self.assertEqual(binding["bridge_pid"], 123)

    def test_queue_rejects_raw_actions_duplicate_start_and_unlisted_arguments(self):
        step = {"id": "start", "tool": ADAPTER.SUBMIT, "args": {
            "operation": "start", "province_id": 200, "policy_positive": True},
            "fresh_revision": True, "continue_on_error": True}
        self.assertEqual(QUEUE.validate({"steps": [step]})["start_requests"], 1)
        with self.assertRaises(ValueError):
            QUEUE.validate({"steps": [step, {**step, "id": "start2"}]})
        with self.assertRaises(ValueError):
            QUEUE.validate({"steps": [{**step, "args": {**step["args"], "raw_pointer": 1}}]})
        with self.assertRaises(ValueError):
            QUEUE.validate({"steps": [{**step, "kind": "advance_day"}]})

    def test_public_request_budget_counts_snapshots_and_all_plan_tools(self):
        client = Client()
        budget = ADAPTER.BudgetedClient(client, 3)
        budget.snapshot()
        step = {"id": "one", "tool": ADAPTER.IDENTITIES, "args": {}}
        budget.execute_plan([step, {**step, "id": "two"}], "two-controls")
        self.assertEqual(budget.public_requests_used, 3)
        with self.assertRaisesRegex(ValueError, "public request cap"):
            budget.snapshot()
        self.assertEqual(budget.public_requests_used, 3)

    def test_low_total_public_request_cap_stops_before_start_with_original_evidence(self):
        client = Client(); ctx = context()
        ctx["case_contract"]["policy"]["max_public_requests"] = 5
        value = ADAPTER.run_case(ctx, client)
        self.assertEqual(self.starts(client), [])
        self.assertEqual(value["public_requests_used"], 5)
        self.assertIn("public request cap", value["failure"])



    def test_stage1_has_fresh_native_read_both_before_and_after_root_visual_review(self):
        client = Client()
        result = ADAPTER.run_case(context(), client)
        self.assertEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
        reads = [row for row in client.calls if row["args"].get("operation") == "read"
                 and row["args"].get("read_stage") == 1]
        self.assertEqual(len(reads), 2)
        self.assertEqual(sum(row["args"].get("operation") == "confirm" for row in client.calls), 1)

    def test_stage1_rejected_or_unselected_never_reaches_review_confirm_or_start(self):
        for field, value in (("stage1_rejected", True), ("stage1_selected", False)):
            with self.subTest(field=field):
                client = Client(); setattr(client, field, value)
                ADAPTER.run_case(context(), client)
                self.assertFalse(any("stage1-before-confirm" in name for name, _ in client.capture_points))
                self.assertFalse(any(row["args"].get("operation") in {"confirm", "start"} for row in client.calls))

    def test_complete_alone_wrong_observation_missing_review_or_bad_image_blocks_each_mutation(self):
        failures = [{"original_image_directly_reviewed": False},
            {"reviewed_native_observation_sha256": "0" * 64},
            {"original_image": None}]
        for approval, forbidden in (("confirm_once_authorized", "confirm"), ("start_once_authorized", "start")):
            for override in failures + [{approval: False}]:
                with self.subTest(approval=approval, override=override):
                    client = Client(); client.review_overrides[approval] = override
                    result = ADAPTER.run_case(context(), client)
                    self.assertFalse(any(row["args"].get("operation") == forbidden for row in client.calls))
                    self.assertFalse(result["start_invoked"])

    def test_selection_change_after_root_review_blocks_confirm_and_start(self):
        client = Client(); client.change_selection_after_review = True
        ADAPTER.run_case(context(), client)
        self.assertFalse(any(row["args"].get("operation") in {"confirm", "start"} for row in client.calls))

    def test_original_open_requires_actual_true_invocation_before_fresh_read_or_confirm(self):
        for invoked in (False, None):
            with self.subTest(invoked=invoked):
                client = Client(); client.open_invoked = invoked
                ADAPTER.run_case(context(), client)
                self.assertFalse(any(row["args"].get("read_stage") == 1 for row in client.calls))
                self.assertFalse(any(row["args"].get("operation") in {"confirm", "start"} for row in client.calls))

    def test_null_selected_pious_in_fresh_stage1_read_is_rejected(self):
        client = Client(); client.stage1_selected = None
        ADAPTER.run_case(context(), client)
        self.assertFalse(any("stage1-before-confirm" in name for name, _ in client.capture_points))
        self.assertFalse(any(row["args"].get("operation") in {"confirm", "start"} for row in client.calls))

    def test_original_image_hash_is_actually_verified(self):
        client = Client()
        image = {"path": str(client.review_image), "bytes": client.review_image.stat().st_size,
                 "sha256": "0" * 64}
        client.review_overrides["confirm_once_authorized"] = {"original_image": image}
        result = ADAPTER.run_case(context(), client)
        self.assertIn("PNG evidence changed", result["failure"])
        self.assertFalse(any(row["args"].get("operation") == "confirm" for row in client.calls))


    def test_v2_natural_clock_capability_query_precedes_start_and_failed_capability_blocks_start(self) -> None:
        class CapabilityClient(Client):
            def __init__(self, output: Path, *, supported: bool) -> None:
                super().__init__()
                self.output = output
                self.supported = supported

            def execute_plan(self, steps: list[dict[str, object]], name: str) -> list[dict[str, object]]:
                if steps[0]["tool"] != "ck3_get_capabilities":
                    return super().execute_plan(steps, name)
                self.calls.append(deepcopy(steps[0]))
                if self.started:
                    raise AssertionError("Capability query occurred after the sole Start")
                value = {"action_steps": ["life-advance"] if self.supported else [],
                    "composite_action_steps": ["life-advance"] if self.supported else [],
                    "current_event_window_context_v1_query_supported": True}
                row = {"id": name, "ok": True, "result": value, "after_snapshot": frame()}
                (self.output / (name + ".actual-results.json")).write_text(
                    json.dumps({"rows": [row]}), encoding="utf-8")
                return [row]

        for supported in (False, True):
            with self.subTest(supported=supported), tempfile.TemporaryDirectory() as temp:
                ctx = context()
                ctx["case"] = ADAPTER.MECHANISM_CASE
                ctx["case_contract"].update(case=ADAPTER.MECHANISM_CASE,
                    schema="faith-engine-e02-pilgrimage-mechanism-case-v2", expected_faith_id=13,
                    expected_rite_id=0, option_key="pilgrimage_type_pious")
                ctx["case_contract"]["policy"]["natural_advance_mode"] = "native_horizon"
                ctx["case_spec"]["required_mcp_tools"].extend(["ck3_get_capabilities", "ck3_execute_step"])
                client = CapabilityClient(Path(temp), supported=supported)
                received: list[object] = []

                def continuation(*args: object, natural_capabilities: object = None) -> dict[str, object]:
                    received.append(natural_capabilities)
                    return {"status": "AUTHORED_JOURNEY_RESULT", "terminal_observed": False}

                ADAPTER.sibling = lambda path, name: (QUEUE if path.name.endswith("queue.py") else
                    SimpleNamespace(observe_milestone=lambda *args, **kwargs: None, run_journey=continuation))
                result = ADAPTER.run_case(ctx, client)
                self.assertEqual(client.calls[0]["tool"], "ck3_get_capabilities")
                self.assertEqual(len(self.starts(client)), 1 if supported else 0)
                self.assertEqual(len(received), 1 if supported else 0)
                if supported:
                    self.assertEqual(result["status"], "AUTHORED_JOURNEY_RESULT")
                    actual = json.loads((Path(temp) / "ordinary-pilgrimage-natural-clock-capabilities.actual-results.json").read_text())
                    self.assertEqual(received[0], actual["rows"][0]["result"])
                else:
                    self.assertIn("unavailable", result["failure"])

    def test_natural_clock_mode_and_required_tools_are_validated_before_original_work(self) -> None:
        for mode in (True, 1.0, None, "automatically"):
            ctx = context()
            ctx["case_contract"]["policy"]["natural_advance_mode"] = mode
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                ADAPTER.validate_contract(ctx)
        ctx = context()
        ctx["case"] = ADAPTER.MECHANISM_CASE
        ctx["case_contract"].update(case=ADAPTER.MECHANISM_CASE,
            schema="faith-engine-e02-pilgrimage-mechanism-case-v2", expected_faith_id=13,
            expected_rite_id=0, option_key="pilgrimage_type_pious")
        ctx["case_contract"]["policy"]["natural_advance_mode"] = "native_horizon"
        with self.assertRaisesRegex(ValueError, "actual public capability query"):
            ADAPTER.validate_contract(ctx)


if __name__ == "__main__":
    unittest.main(verbosity=2)
