"""Synthetic Service/owner UI seams; no Native, Game, MCP or business credit."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_succession_ui_observation_v1 import material
import test_native_auto_run as old
from xar_autoplayer import native_auto_run as owner
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.errors import AgentError
from xar_autoplayer.successor_ui_owner_continuation_v1 import continue_verified_successor_ui_v1 as finish
from xar_autoplayer.strategy import continue_ordinary_campaign_goal_v1


def goal(actor):
    return {"format_version": 1, "goal_key": "dynasty_continuity", "campaign_id": "synthetic-campaign",
            "origin_character_id": 19, "current_character_id": actor,
            "progress": {"reconciled_successions": 1, "last_succession": {}}}


def verified_material():
    snapshot, timeline, event = material()
    snapshot.update(one_life_terminal=False, pending_character_interaction=None, campaign_goal=goal(23))
    frame = {key: snapshot[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw")}
    frame.update({key: snapshot["diagnostics"][key] for key in ("bridge_pid", "connection_generation")})
    before = {**frame, "episode_character_id": 19, "episode_run_id": "synthetic-predecessor",
              "played_character_id": 23, "played_character_alive": True,
              "one_life_terminal": True, "one_life_terminal_reason": "played_character_changed"}
    reconciliation = {"status": "available", "verdict": "matched", "successor_match": True,
        "title_distribution_match": True, "predecessor_character_id": 19,
        "actual_successor_character_id": 23, "successor_binding": {key: frame[key] for key in
        ("snapshot_id", "revision", "native_revision", "date_raw")}}
    lifecycle = {"lifecycle": "ordinary_campaign_succession"}
    result = {"step": "continue-as-reconciled-successor", "accepted": True, "status": "continued",
        "source": "native-played-character-transition", "lifecycle_intent": "natural_succession",
        "succession_lifecycle": lifecycle, "predecessor_character_id": 19, "successor_character_id": 23,
        "source_episode_run_id": "synthetic-predecessor", "episode_run_id": snapshot["episode_run_id"],
        "continue_as_heir_after_death": True, "heir_gameplay_actions": 0,
        "ck3_command_submitted": False, "process_restarted": False, "reconciliation": reconciliation}
    binding = {**frame, "episode_binding_state": "active_natural_successor",
               "driver_state_restore_kind": "natural_succession"}
    proof = owner._verify_natural_succession_transition(result, snapshot=snapshot, binding=binding,
                                                       before=before, succession_lifecycle=lifecycle)
    return snapshot, timeline, event, proof


def timeline_packet(snapshot, context, sequence):
    return {"step": "query-current-timeline-blocker-context-v1", "accepted": True,
        "status": context["status"], "query_sequence": sequence, "observation_revision": snapshot["native_revision"],
        "snapshot_revision": snapshot["native_revision"], "current_timeline_blocker_context": deepcopy(context),
        "private_build": True, "read_only": True, "advertised": False, "backend_id": "synthetic-private",
        "queried_snapshot_id": snapshot["snapshot_id"], "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"]}


class SourceDriver:
    def __init__(self):
        self.frame, self.context, self.event, self.proof = verified_material()
        self.reads = self.closes = 0
        self.ack_only = False

    def take_snapshot(self):
        return deepcopy(self.frame)

    take_snapshot_without_native_command_history = take_snapshot

    def query_current_timeline_blocker_context_v1(self, *, expected_revision):
        if expected_revision != self.frame["revision"]:
            raise ValueError("synthetic source revision mismatch")
        self.reads += 1
        return timeline_packet(self.frame, self.context, self.reads)

    def continue_death_succession_modal_private_v1(self, **arguments):
        self.closes += 1
        if self.ack_only:
            return {"status": "submitted", "material_result_verified": False}
        initial = self.query_current_timeline_blocker_context_v1(expected_revision=self.frame["revision"])
        starting = self.frame["date_raw"]
        self.frame["date_raw"] += 24
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        self.frame["snapshot_id"] = "synthetic:after-close"
        self.context.update(identity="none", date_raw=self.frame["date_raw"], snapshot_revision=self.frame["native_revision"])
        for key in ("blocks_simulation", "has_open_succession"):
            self.context[key]["value"] = False
        self.context["can_continue"] = {"status": "unavailable", "value": None,
                                        "unavailable_reason": "no_supported_timeline_surface_visible"}
        post = self.query_current_timeline_blocker_context_v1(expected_revision=self.frame["revision"])
        return {"status": "materially_verified", "material_result_verified": True,
            "starting_date_raw": starting, "ending_date_raw": self.frame["date_raw"],
            "ending_revision": self.frame["revision"], "ending_native_revision": self.frame["native_revision"],
            "submission_ack": {"accepted": True, "status": "submitted", "played_character_id": 23,
                               "close_invocations": 1, "material_result_verified": False},
            "initial_query": initial, "postcondition_query": post}

    def event_finished(self):
        self.frame["active_event"] = None
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        self.frame["snapshot_id"] = "synthetic:after-event"
        self.context.update(identity="death_succession_modal", snapshot_revision=self.frame["native_revision"])
        self.context["can_continue"] = {"status": "available", "value": True, "unavailable_reason": None}


def service(driver):
    value = object.__new__(GameplayBridgeService)
    value.driver = driver
    return value


def run_ui(s, d, previous=None):
    return finish(s, transition=d.proof, snapshot=s.snapshot(), attempt={},
        classify_timeline=owner._ordinary_succession_timeline_state,
        close_issue=owner._ordinary_succession_close_issue, capture_failure=lambda **_: None,
        previous_observation=previous)


class VerifiedSuccessorServiceTests(unittest.TestCase):
    def test_real_service_keeps_old_root_event_unresolved_then_uses_original_close_checks(self):
        d = SourceDriver(); s = service(d)
        query = s.query_current_timeline_blocker_context_v1(expected_revision=d.frame["revision"])
        projected = s.observe_verified_successor_ui_v1(transition=d.proof, snapshot=s.snapshot(),
                                                     timeline_query=query, event_context=d.event)
        self.assertEqual(projected["event_root_scope"]["typed_identity"]["character_id"], 19)
        _, pending, advanced, ui_pending = run_ui(s, d)
        self.assertEqual((pending, advanced, ui_pending, d.closes), (True, False, True, 0))
        observation = d.proof["successor_ui_observation"]
        self.assertEqual(observation["ui_clearance"], "unresolved")
        self.assertFalse(observation["authorizes_close_or_save"])
        d.event_finished()
        current, pending, advanced, ui_pending = run_ui(s, d, observation)
        self.assertEqual((pending, advanced, ui_pending, d.closes), (False, True, False, 1))
        self.assertEqual(current["date_raw"], observation["frame"]["date_raw"] + 24)
        self.assertEqual(d.proof["timeline_blocker_continuation"]["status"], "materially_cleared")

    def test_bad_full_proof_and_foreign_service_frame_cannot_become_clear(self):
        for changed in ("title", "six_frame", "query_revision", "goal", "connection"):
            with self.subTest(changed=changed):
                d = SourceDriver(); s = service(d)
                q = s.query_current_timeline_blocker_context_v1(expected_revision=d.frame["revision"])
                if changed == "title": d.proof["reconciliation"]["title_distribution_match"] = False
                if changed == "six_frame": d.proof["successor_episode_binding"]["native_revision"] -= 1
                if changed == "query_revision": q["queried_revision"] -= 1
                if changed == "goal": d.frame["campaign_goal"]["current_character_id"] = 19
                if changed == "connection": d.frame["diagnostics"]["connection_generation"] += 1
                with self.assertRaises(ValueError):
                    s.observe_verified_successor_ui_v1(transition=d.proof, snapshot=s.snapshot(), timeline_query=q)
                self.assertEqual(d.closes, 0)

    def test_unknown_close_retains_once_marker_and_does_not_query_or_submit_again(self):
        d = SourceDriver(); s = service(d)
        run_ui(s, d); observation = d.proof["successor_ui_observation"]
        d.event_finished(); d.ack_only = True
        with self.assertRaisesRegex(AgentError, "material postcondition"):
            run_ui(s, d, observation)
        reads = d.reads
        with self.assertRaisesRegex(AgentError, "do not resend"):
            run_ui(s, d, observation)
        self.assertEqual((d.closes, d.reads), (1, reads))


class EventHarness(old._NativeAutoRunHarness):
    """Original owner harness with explicit .4/event/goal synthetic sources."""
    fail_persist = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_goal = goal(self.episode_character_id)

    def _diagnostics(self):
        result = super()._diagnostics()
        result["hello"].update(expected_ck3_version=CK3_12004.game_version,
            expected_ck3_sha256=CK3_12004.executable_sha256,
            executable_sha256=CK3_12004.executable_sha256)
        return result

    def snapshot(self):
        return {**super().snapshot(), "campaign_goal": deepcopy(self.ui_goal)}

    def execute_auto_turn(self):
        result = super().execute_auto_turn()
        if result.get("selected_step") == "continue-as-reconciled-successor":
            self.ui_goal = continue_ordinary_campaign_goal_v1(self.ui_goal, result["result"]["reconciliation"])
            self.active_event_id = 47
            if self.fail_persist:
                result["result"]["driver_state_persistence_diagnostic"] = {"status": "failed"}
        return result

    def make_service(self, driver):
        result = super().make_service(driver)
        real = service(types.SimpleNamespace(take_snapshot=self.snapshot))
        result.observe_verified_successor_ui_v1 = real.observe_verified_successor_ui_v1
        sequence = [0]
        def raw(*, expected_revision):
            frame = self.snapshot()
            if expected_revision != frame["revision"]: raise ValueError("synthetic source changed")
            _, context, _ = material()
            context.update(snapshot_revision=self.native_revision, date_raw=self.date_raw)
            modal = self.succession_modal_open and self.active_event_id is None
            blocked = self.succession_modal_open
            context["identity"] = "death_succession_modal" if modal else "none"
            for key in ("blocks_simulation", "has_open_succession"): context[key]["value"] = blocked
            if modal: context["can_continue"] = {"status": "available", "value": True, "unavailable_reason": None}
            sequence[0] += 1
            self.events.append("query_successor_timeline")
            return timeline_packet(frame, context, sequence[0])
        real.driver.query_current_timeline_blocker_context_v1 = raw
        result.query_current_timeline_blocker_context_v1 = real.query_current_timeline_blocker_context_v1
        return result


class OrdinaryOwnerTests(unittest.TestCase):
    def test_bound_after_event_reply_retains_unresolved_ui_without_final_save(self):
        base = old.NativeAutoRunTests(); base.setUp()
        try:
            with patch.object(old, "_NativeAutoRunHarness", EventHarness):
                report, h = base._run(["natural_terminal_advance", "continue_natural_successor", "event"],
                    checkpoint_every_eligible_advances=1,
                    succession_lifecycle="ordinary_campaign_succession", ordinary_campaign_no_pact=True)
            self.assertEqual(report["status"], "turn_limit_player_decision_pending")
            self.assertIsNotNone(report["pending_successor_ui"])
            self.assertNotIn("save_checkpoint", h.events)
            self.assertNotIn("close_successor_timeline", h.events)
        finally:
            base.tearDown()

    def test_original_full_owner_handles_event_before_close_and_preserves_persistence_failure(self):
        for failed in (False, True):
            with self.subTest(failed=failed):
                class Scenario(EventHarness):
                    fail_persist = failed
                base = old.NativeAutoRunTests()
                base.setUp()
                try:
                    with patch.object(old, "_NativeAutoRunHarness", Scenario):
                        report, harness = base._run(["natural_terminal_advance", "continue_natural_successor", "event", "advance"],
                            checkpoint_every_eligible_advances=1,
                            succession_lifecycle="ordinary_campaign_succession", ordinary_campaign_no_pact=True)
                    self.assertEqual(harness.events.count("auto_turn:continue_natural_successor"), 1)
                    if failed:
                        self.assertFalse(report["ok"])
                        self.assertNotIn("query_successor_timeline", harness.events)
                        self.assertNotIn("close_successor_timeline", harness.events)
                    else:
                        self.assertTrue(report["ok"], report.get("error"))
                        self.assertEqual(harness.events.count("close_successor_timeline"), 1)
                        self.assertLess(harness.events.index("auto_turn:event"), harness.events.index("close_successor_timeline"))
                        self.assertIsNone(report["pending_successor_ui"])
                finally:
                    base.tearDown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
