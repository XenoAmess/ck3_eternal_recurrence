"""Portable authored-state tests; no native output, process or game is created."""
from __future__ import annotations

from copy import deepcopy
import base64
import hashlib
import json
import tempfile
import importlib.util
from pathlib import Path
from types import SimpleNamespace
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


class WorkflowTests(unittest.TestCase):
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
                run_journey=lambda *args: {"status": "AUTHORED_JOURNEY_RESULT", "terminal_observed": False}))
        self.addCleanup(setattr, ADAPTER, "sibling", self.original_sibling)

    def starts(self, client):
        return [s for s in client.calls if s["tool"] == ADAPTER.SUBMIT and s["args"]["operation"] == "start"]

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
