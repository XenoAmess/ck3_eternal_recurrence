"""Real journey/registry consumers with finite synthetic public CaseClient I/O.

Run from a checkout normally. XAR_CK3_TEST_REPO_ROOT selects a checkout when
reviewing this new-file candidate externally. No game, driver, screen or day
advance is used, and no historical external fixture package is required.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(os.environ.get("XAR_CK3_TEST_REPO_ROOT", str(Path(__file__).resolve().parents[1]))).resolve()
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from ck3_mod_acceptance_client import CaseClient  # noqa: E402

HELPER_PATH = TOOLS / "ck3_mod_acceptance_cases/faith_e02_pilgrimage_journey.py"
spec = importlib.util.spec_from_file_location("_pilgrimage_event_policy_under_test", HELPER_PATH)
JOURNEY = importlib.util.module_from_spec(spec)
spec.loader.exec_module(JOURNEY)
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


def scope(kind, actor=None):
    return {"status": "available", "raw_type_index": 4 if actor is not None else 1,
        "type_key": kind, "subtype": 0,
        "typed_identity": {"status": "available", "kind": "character", "character_id": actor}
            if actor is not None else {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}}


def saved(name, kind, actor=None):
    return {"name": name, "name_identifier": len(name) + 100, "scope": scope(kind, actor)}


def option(rendered, native, text, enabled=True):
    return {"rendered_index": rendered, "native_option_index": native,
        "shown": True, "enabled": enabled, "fallback": False, "cancel": False,
        "resolved_name": text, "unavailable_reason": "",
        "effect_indicators": {"status": "available", "coverage": "played-character-event-icon-indicators-1.20.0.4-v1",
                              "complete_effect_set": False, "rows": []},
        "effect_preview": {"status": "unavailable", "reason": "indicator_subset_has_no_completeness_signal"},
        "resource_deltas": {"status": "unavailable"}, "relationship_deltas": {"status": "unavailable"}}


class ModalClient(CaseClient):
    """Keep the real public frame validator; replace only external I/O.

    Successful selections change the fixture window independently of the ACK.
    The submission-unknown variant applies that change before raising. Revision
    checks reject stale requests; tests cannot pass by merely returning an ACK.
    """
    operator_reviewer = "synthetic-root-reviewer"

    def __init__(self, path):
        self.output = Path(path)
        self.manifest = {"game": {"version": "1.20.0.4", "exe_sha256": EXE_SHA256}}
        self._binding = None
        self.current = {"revision": 1, "native_revision": 10, "date_raw": 1000,
            "source": "injected-dll-named-pipe", "backend_id": "native-headless",
            "episode_projection": "native_campaign", "snapshot_id": "synthetic:1",
            "episode_run_id": None, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": 101, "alive": True, "source": "native"},
            "diagnostics": {"bridge_pid": 77, "connection_generation": 2, "hello": {
                "pid": 77, "connection_generation": 2, "ck3_build_match": True,
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": EXE_SHA256}}}
        self.calls = []
        self.public_requests_used = 0
        self.public_requests_cap = 480
        self.select_unknown = False
        self.event_key = "health.1015"
        self.displayed = [option(0, 6, "我们必须坚持下去。"), option(1, 0, "叫医生来！马上！")]
        self.physician = False
        self.snapshot_count = 8
        self.root_calls = []
        self.capture_revisions = []
        self.select_revisions = []
        self.capture_change = None
        self.install()

    def install(self):
        self.current["active_event"] = {"instance_id": 9, "option_count": self.snapshot_count,
            "options": [{"index": row["native_option_index"], "option_number": row["native_option_index"] + 1,
                         "enabled": row["enabled"]} for row in self.displayed]}

    def remaining(self):
        return 5000

    def guard(self, reserve=90):
        return {"fixture_only": True}

    def debit(self):
        if self.public_requests_used >= self.public_requests_cap:
            raise ValueError("Synthetic public request cap reached")
        self.public_requests_used += 1

    def fresh(self):
        self.current["revision"] += 1
        self.current["snapshot_id"] = "synthetic:" + str(self.current["revision"])
        return deepcopy(self.current)

    def snapshot(self, **kwargs):
        self.debit()
        return self.validate_frame(self.fresh(), **kwargs)

    def checkpoint(self, name, value):
        path = self.output / (name + ".json")
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream)
        return path

    def typed_context(self, frame):
        scopes = [saved("epidemic", "epidemic"), saved("disease_type", "flag"),
                  saved("sick_character", "character", 101), saved("new_memory", "character_memory")]
        if self.physician:
            scopes.insert(2, saved("physician", "character", 202))
        return {"schema": "current-event-window-context-v1", "schema_version": 1,
            "status": "available", "current_event_instance_id": frame["active_event"]["instance_id"],
            "window_match_count": 1, "unavailable_reason": None, "event_definition_key": self.event_key,
            "date_raw": frame["date_raw"], "snapshot_revision": frame["native_revision"],
            "root_scope": scope("character", 101), "saved_scopes": scopes,
            "options": deepcopy(self.displayed), "provenance": {},
            "readiness": {"option_presentation_ready": True, "event_definition_identity_ready": True,
                          "root_scope_ready": True, "saved_scopes_ready": True}}

    def execute_plan(self, steps, name):
        if len(steps) != 1:
            raise AssertionError("This fixture supports one current public submission")
        self.debit()
        step = steps[0]
        tool, args = step["tool"], step["args"]
        self.calls.append((tool, deepcopy(args)))
        if args["expected_revision"] != self.current["revision"]:
            raise AssertionError("Stale public revision submitted")
        current_id = (self.current.get("active_event") or {}).get("instance_id")
        if args["event_instance_id"] != current_id:
            raise AssertionError("Foreign event instance submitted")
        if tool == JOURNEY.EVENT_CONTEXT:
            value = {"accepted": True, "current_event_window_context_ready": True,
                     "current_event_window_context": self.typed_context(self.current)}
        elif tool == JOURNEY.EVENT_SELECT:
            index = args["option_number"] - 1
            if not any(row["native_option_index"] == index and row["shown"] is True and row["enabled"] is True
                       for row in self.displayed):
                raise AssertionError("Hidden/disabled native option submitted")
            self.select_revisions.append(args["expected_revision"])
            self.current["active_event"] = None
            self.current["native_revision"] += 1
            if self.select_unknown:
                raise RuntimeError("Synthetic original action applied but ACK lost")
            value = {"accepted": True, "event_instance_id": current_id,
                     "option_number": args["option_number"], "option_index": index}
        else:
            raise AssertionError("Unexpected external action: " + tool)
        row = {"id": name, "ok": True, "result": value, "after_snapshot": self.fresh()}
        self.checkpoint(name + ".actual-results", {"rows": [row]})
        return [row]

    def root_checkpoint(self, name, request, reserve=90):
        if reserve != 120:
            raise AssertionError("Root capture changed the original Quit reserve")
        self.root_calls.append((name, deepcopy(request)))
        self.capture_revisions.append(request["frame"]["revision"])
        for _ in range(3):
            self.fresh()  # Original image preparation can publish new public revisions.
        if self.capture_change == "instance":
            self.current["active_event"]["instance_id"] += 999
        elif self.capture_change == "option":
            self.displayed[0]["native_option_index"] = 1
            self.install()
        return {"run_id": request["run_id"], "reviewer": self.operator_reviewer, "status": "complete"}

    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> dict[str, object]:
        raise AssertionError("Finite modal regression must not advance game time")


class PilgrimageEventPolicyTests(unittest.TestCase):
    def make(self, temp):
        context = {"case": JOURNEY.CASE, "product": "faith-engine", "run_id": "synthetic-event-policy",
            "case_contract": {"machine_id": "synthetic-machine"}, "shared_source_root": str(ROOT)}
        binding = {"run_id": context["run_id"], "machine_id": "synthetic-machine",
            "actor_character_id": 101, "bridge_pid": 77, "connection_generation": 2, "episode_run_id": None}
        identity = {"activity_id": 512, "host_character_id": 101, "type_key": "activity_pilgrimage"}
        return context, ModalClient(temp), binding, identity

    def drain(self, context, client, binding):
        return JOURNEY.drain_interruptions(context, client, binding, {})

    @staticmethod
    def selections(client):
        return [args for tool, args in client.calls if tool == JOURNEY.EVENT_SELECT]

    def test_explicit_doctor_uses_actual_named_second_rendered_row_without_hard_index(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "INTERRUPTIONS_DRAINED")
            self.assertEqual(self.selections(client)[0]["option_number"], 1)
            policy = result["event_receipts"][0]["event_policy"]
            self.assertEqual(policy["policy"], "user_health1015_current_named_doctor_v1")
            self.assertEqual(policy["registry_knowledge_status"], "available")
            self.assertTrue(policy["registry_analysis_available"])
            self.assertEqual(policy["registry_decision"]["status"], "blocked")
            self.assertFalse(policy["health1015_user_preference"]["full_registry_occurrence_contract_claimed"])
            self.assertEqual(policy["source_sha256"]["events/health_events.txt"],
                "74073E049A416C744B36A2A996FA467610705E38D53C836B050F1AC6F66E1212")
            self.assertTrue(result["event_receipts"][0]["old_instance_gone_in_independent_snapshot"])

    def test_disabled_doctor_retains_gap_and_uses_actual_first_legal_display(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            client.displayed[1]["enabled"] = False
            client.install()
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "INTERRUPTIONS_DRAINED")
            self.assertEqual(self.selections(client)[0]["option_number"], 7)
            policy = result["event_receipts"][0]["event_policy"]
            self.assertEqual(policy["policy"], "native_first_displayed_v1")
            self.assertTrue(policy["gap"])

    def test_real_shared_registry_recommendation_precedes_generic_first(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            client.event_key = "health.1010"
            client.physician = True
            client.snapshot_count = 7
            client.displayed = [option(0, 3, "safe"), option(1, 4, "risky"), option(2, 6, "reviewed conservative route")]
            client.install()
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "INTERRUPTIONS_DRAINED")
            self.assertEqual(self.selections(client)[0]["option_number"], 7)
            policy = result["event_receipts"][0]["event_policy"]
            self.assertEqual(policy["registry_decision"]["status"], "recommended")
            self.assertEqual(policy["policy"], "existing_registered_vanilla_event_v1")

    def test_unknown_captures_then_selects_actual_first_once_with_independent_window_postcondition(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            client.event_key = "synthetic.unregistered"
            client.displayed = [option(0, 2, "first"), option(1, 6, "later")]
            client.install()
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "INTERRUPTIONS_DRAINED")
            self.assertEqual(self.selections(client)[0]["option_number"], 3)
            receipt = result["event_receipts"][0]
            capture = json.loads(Path(receipt["offline_analysis_input"]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(capture["typed_context"]["current_event_instance_id"], 9)
            self.assertEqual(capture["typed_context"]["options"][0]["native_option_index"], 2)
            self.assertTrue(receipt["ack_accepted"])
            self.assertTrue(receipt["old_instance_gone_in_independent_snapshot"])
            self.assertIsNone(receipt["independent_after_snapshot"]["active_event"])
            self.assertEqual(len(self.selections(client)), 1)

    def test_disabled_first_unknown_never_silently_skips_to_second(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            client.event_key = "synthetic.unregistered"
            client.displayed[0]["enabled"] = False
            client.install()
            result = self.drain(context, client, binding)
            self.assertTrue(result["status"].startswith("PARTIAL_"))
            self.assertEqual(self.selections(client), [])

    def test_unknown_submission_is_never_replayed_even_when_window_is_gone(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            client.select_unknown = True
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "PARTIAL_EVENT_SUBMISSION_UNKNOWN")
            self.assertEqual(len(self.selections(client)), 1)
            self.assertFalse(result["event_receipts"][0]["ack_accepted"])
            self.assertTrue(result["event_receipts"][0]["old_instance_gone_in_independent_snapshot"])

    def test_refresh_recomputes_real_policy_for_nonfirst_chosen_row(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, identity = self.make(temp)
            client.event_key = "health.1010"
            client.physician = True
            client.snapshot_count = 7
            client.displayed = [option(0, 3, "safe"), option(1, 4, "risky"), option(2, 6, "reviewed route")]
            client.install()
            controller = JOURNEY._Journey(context, client, binding, identity, {})
            frame = controller.snapshot()
            row, before, _ = controller.call("initial-event", JOURNEY.EVENT_CONTEXT, {"event_instance_id": 9}, frame)
            typed = row["result"]["current_event_window_context"]
            chosen, _ = controller.choose_event_option(typed, typed["options"], frame, before)
            self.assertEqual(chosen["native_option_index"], 6)
            for _ in range(3):
                client.fresh()
            refreshed = controller.refresh_key_window(typed, chosen, before)
            self.assertEqual(refreshed["event_policy"]["policy"], "existing_registered_vanilla_event_v1")
            controller.call("select-after-refresh", JOURNEY.EVENT_SELECT,
                {"event_instance_id": 9, "option_number": 7}, refreshed["query_after_frame"])
            self.assertEqual(len(self.selections(client)), 1)
            self.assertGreater(self.selections(client)[0]["expected_revision"], before["revision"])
            self.assertIsNone(controller.snapshot()["active_event"])

    def key_window(self, client, key="pilgrimage.7000"):
        client.event_key = key
        client.displayed = [option(0, 0, "current key-window option")]
        client.snapshot_count = 1
        client.install()

    def test_key_capture_revision_jump_selects_once_with_latest_revision_and_postcondition(self):
        for key in ("pilgrimage.7000", "pilgrimage.9001"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp:
                context, client, binding, _ = self.make(temp)
                self.key_window(client, key)
                result = self.drain(context, client, binding)
                self.assertEqual(result["status"], "INTERRUPTIONS_DRAINED")
                self.assertEqual(len(client.root_calls), 1)
                self.assertEqual(len(self.selections(client)), 1)
                self.assertGreater(client.select_revisions[0], client.capture_revisions[0])
                receipt = result["event_receipts"][0]
                self.assertTrue(receipt["key_window_refresh_source"]["sha256"])
                self.assertTrue(receipt["old_instance_gone_in_independent_snapshot"])

    def test_changed_key_event_instance_after_capture_is_not_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            self.key_window(client)
            client.capture_change = "instance"
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "PARTIAL_KEY_EVENT_CHANGED")
            self.assertEqual(self.selections(client), [])
            self.assertEqual(len(client.root_calls), 1)
            self.assertEqual(result["last_frame"]["active_event"]["instance_id"], 1008)

    def test_changed_first_native_option_after_capture_is_not_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            context, client, binding, _ = self.make(temp)
            self.key_window(client)
            client.capture_change = "option"
            result = self.drain(context, client, binding)
            self.assertEqual(result["status"], "PARTIAL_KEY_EVENT_CHANGED")
            self.assertEqual(self.selections(client), [])
            self.assertEqual(len(client.root_calls), 1)

    def test_identity_refresh_event_is_drained_before_next_real_day_consumer(self) -> None:
        from test_ck3_mod_acceptance_native_day import Port
        from ck3_mod_acceptance_native_day import integer, obj

        class IdentityRefreshClient(ModalClient):
            def __init__(self, path: Path) -> None:
                super().__init__(path)
                self.event_key = "synthetic.identity_refresh_race"
                self.displayed = [option(0, 2, "first displayed"), option(1, 6, "later")]
                self.snapshot_count = 2
                self.install()
                self.race_event = deepcopy(self.current["active_event"])
                self.current["active_event"] = None
                self.initial_date = integer(self.current["date_raw"], "fixture initial date")
                self.injected = False
                self.world_dates: list[tuple[int, int]] = []
                self.order: list[str] = []

            def snapshot(self, **kwargs: bool) -> dict[str, object]:
                # Reproduce R0034: an ordinary event is first published by the
                # seven-day identity observer, after the loop's earlier drain.
                if not self.injected and self.current["date_raw"] == self.initial_date + 7 * 24:
                    self.current["active_event"] = deepcopy(self.race_event)
                    self.current["native_revision"] = integer(self.current["native_revision"], "fixture native revision") + 1
                    self.injected = True
                return obj(super().snapshot(**kwargs), "identity-refresh fixture snapshot")

            def execute_plan(self, steps: list[dict[str, object]], name: str) -> list[dict[str, object]]:
                step = steps[0]
                if step["tool"] != JOURNEY.IDENTITIES:
                    rows = super().execute_plan(steps, name)
                    if step["tool"] == JOURNEY.EVENT_SELECT:
                        self.order.append("event-selected")
                    return [obj(row, "fixture modal row") for row in rows]
                self.debit()
                args = obj(step["args"], "fixture identity args")
                if args["expected_revision"] != self.current["revision"]:
                    raise AssertionError("Stale identity observation submitted")
                value = {"schema": "ck3_12004_player_pilgrimage_activities_v1",
                    "scope": "currently-hosted-by-current-player", "activity_type_key": "activity_pilgrimage",
                    "absence_is_completion": False, "read_only": True,
                    "queried_revision": self.current["revision"], "snapshot_revision": self.current["native_revision"],
                    "date_raw": self.current["date_raw"], "played_character_id": 101,
                    "activity_count": 1, "activities": [{"activity_id": 512, "host_character_id": 101,
                        "type_key": "activity_pilgrimage", "terminal_flags_observed": False}]}
                row = {"id": name, "ok": True, "result": value, "after_snapshot": self.fresh()}
                self.checkpoint(name + ".actual-results", {"rows": [row]})
                return [row]

            def advance_day(self, days: int = 1, timeout: float = 300,
                            allow_event_boundary: bool = False,
                            allow_actor_change: bool = False) -> dict[str, object]:
                before = deepcopy(self.current)
                after = deepcopy(before)
                after["date_raw"] = integer(after["date_raw"], "fixture day date") + 24
                after["revision"] = integer(after["revision"], "fixture day revision") + 1
                after["native_revision"] = integer(after["native_revision"], "fixture day native revision") + 1
                raw = {"id": "owned-native-day", "ok": True, "error": None, "after_snapshot": after,
                    "result": {"step": "life-advance-one-day", "source": "native-composite",
                        "backend_id": "native-headless", "starting_date_raw": before["date_raw"],
                        "ending_date_raw": after["date_raw"], "paused": True, "requested_horizon_days": 1,
                        "active_event": None, "pending_character_interaction": None,
                        "ordinary_events": [], "actions": [], "progress_status": "postcondition",
                        "event_resolution": "none"}}
                port = Port(self.output, raw, before)
                port._seq = 100 + len(self.world_dates) * 2
                # This executes the real CaseClient.advance_day and its native
                # event-free guard. No test implementation selects an event.
                row = port.advance_day(days, timeout, allow_event_boundary, allow_actor_change)
                self.assert_single_world_call(port.world_calls())
                self.current = deepcopy(obj(row["after_snapshot"], "actual fixture day after"))
                self.world_dates.append((integer(before["date_raw"], "before date"),
                                         integer(self.current["date_raw"], "after date")))
                self.order.append("day-completed")
                return row

            @staticmethod
            def assert_single_world_call(calls: list[dict[str, object]]) -> None:
                if len(calls) != 1:
                    raise AssertionError("Exactly one native world dispatch required")

        with tempfile.TemporaryDirectory() as temp:
            context, _, binding, identity = self.make(temp)
            client = IdentityRefreshClient(Path(temp))
            result = JOURNEY.run_journey(context, client, binding, identity,
                {"max_days": 9, "max_day_requests": 16})
            self.assertEqual(result["status"], "PARTIAL_DAY_CAP", result.get("reason"))
            self.assertEqual(result["observed_days"], 8)
            self.assertEqual(result["day_requests"], 8)
            self.assertEqual(client.order, ["day-completed"] * 7 + ["event-selected", "day-completed"])
            self.assertEqual(client.world_dates, [(1000 + day * 24, 1024 + day * 24) for day in range(8)])
            self.assertEqual(len(self.selections(client)), 1)
            self.assertEqual(self.selections(client)[0]["option_number"], 3)
            self.assertTrue(result["event_receipts"][0]["old_instance_gone_in_independent_snapshot"])
            self.assertFalse(result["business_pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
