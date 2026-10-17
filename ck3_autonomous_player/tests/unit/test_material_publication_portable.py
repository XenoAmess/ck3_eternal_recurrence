"""Focused source-bound material-publication and faction two-stage tests."""

import json
import tempfile
import unittest
from pathlib import Path

from xar_autoplayer.bridge import pending_material_publication_v1 as material
from xar_autoplayer.bridge import faction_gift_formal_route_v1 as faction
from xar_autoplayer.bridge import service as service_module


def frame(*, revision=62, native_revision=61, prestige=199035710,
          actor=31254, pid=230672, generation=1, wars=None):
    return {"snapshot_id": f"native:{native_revision}", "revision": revision,
            "native_revision": native_revision, "date_raw": 53145120,
            "paused": True, "map_ready": True, "active_event": None,
            "pending_character_interaction": None, "active_wars": [] if wars is None else wars,
            "player_armies": [], "one_life_terminal": False,
            "played_character": {"character_id": actor, "alive": True,
                                 "prestige": prestige},
            "episode_run_id": "native-31254-8d3a8440eb30",
            "diagnostics": {"bridge_pid": pid, "connection_generation": generation}}


def crown_pending():
    return {"stage": "receipt_pending", "action_id": "crown-formal-3a4b911a",
            "actor_character_id": 31254,
            "episode_run_id": "native-31254-8d3a8440eb30",
            "pre_native_revision": 61, "pre_date_raw": 53145120,
            "source_context": {"bridge_pid": 230672,
                               "episode_run_id": "native-31254-8d3a8440eb30"}}


class PublicationFenceTests(unittest.TestCase):
    def test_actual_crown_action_receipt_precedes_any_new_opportunity_query(self):
        before = frame()
        intermediate = frame(revision=63, prestige=93035710)
        final = frame(revision=64, native_revision=62, prestige=93035710)
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            (state_dir / "crown-authority-formal-v1.json").write_text(
                json.dumps({"pending": crown_pending(), "resolved": None, "retry": None}),
                encoding="utf-8")

            class Driver:
                _session_bridge_pid = 230672
                allow_private_realm_law_action = True
                allow_private_activity_feast_lifecycle_observation = False

                def take_internal_semantic_snapshot(self):
                    return before

                def _with_internal_planning_view(self, snapshot, callback):
                    return callback(snapshot, [])

                def wait_for_change(self, after_revision, *, timeout_seconds):
                    self.waited.append(after_revision)
                    return {62: intermediate, 63: final}[after_revision]

            driver = Driver()
            driver.state_dir = state_dir
            driver.waited = []
            service = object.__new__(service_module.GameplayBridgeService)
            service.driver = driver
            service.capabilities = lambda: {}
            service._strategy_state_dir = lambda: state_dir
            service._prepare_succession_transition_v1 = (
                lambda snapshot, available_steps, **kwargs: snapshot)
            old_steps = service_module.action_step_set
            old_priority = service_module.plan_one_life_window_priority_v1
            old_one_life = service_module.read_one_life_strategy
            old_choose = service_module.choose_one_life_turn
            service_module.action_step_set = lambda capabilities: {"life-advance-one-day"}
            service_module.plan_one_life_window_priority_v1 = lambda *args, **kwargs: None
            service_module.read_one_life_strategy = lambda state_dir: {"episodes": []}
            service_module.choose_one_life_turn = lambda *args, **kwargs: self.fail(
                "new opportunity strategy was reached before the pending receipt")
            try:
                plan = service._plan_turn_internal_without_readonly_retry_v1()
            finally:
                service_module.action_step_set = old_steps
                service_module.plan_one_life_window_priority_v1 = old_priority
                service_module.read_one_life_strategy = old_one_life
                service_module.choose_one_life_turn = old_choose
            self.assertEqual(driver.waited, [62, 63])
            self.assertEqual(plan["plan"]["selected_step"],
                             service_module.PRIVATE_CROWN_RECEIPT_STEP)
            self.assertEqual(plan["plan"]["crown_pending_action"]["action_id"],
                             crown_pending()["action_id"])

    def test_actual_crown_two_stage_publication_waits_for_native_frame(self):
        before = frame()
        intermediate = frame(revision=63, prestige=93035710)
        final = frame(revision=64, native_revision=62, prestige=93035710)
        pending = crown_pending()
        first = material.classify_pending_material_v1(before, crown=pending,
                                                       bridge_pid=230672)
        self.assertEqual(first["status"], "await_publication")
        self.assertTrue(material.same_publication_scope_v1(before, intermediate))
        self.assertFalse(material.same_publication_owner_v1(before, intermediate))
        self.assertEqual(material.classify_pending_material_v1(
            intermediate, crown=pending, bridge_pid=230672)["status"], "await_publication")
        self.assertTrue(material.same_publication_owner_v1(intermediate, final))
        ready = material.classify_pending_material_v1(final, crown=pending,
                                                      bridge_pid=230672)
        self.assertEqual((ready["status"], ready["domain"], ready["business_credit"]),
                         ("ready", "crown", False))

    def test_changed_owner_or_war_never_qualifies_quiet_advance(self):
        before = frame()
        self.assertFalse(material.same_publication_scope_v1(
            before, frame(revision=63, native_revision=62, pid=230673)))
        self.assertFalse(material.same_publication_scope_v1(
            before, frame(revision=63, native_revision=62, generation=2)))
        self.assertFalse(material.same_publication_scope_v1(
            before, frame(revision=63, native_revision=62, actor=40526)))
        self.assertFalse(material.can_advance_for_publication_v1(
            frame(wars=[{"war_id": 1}])))
        self.assertTrue(material.can_advance_for_publication_v1(before))

    def test_two_pending_intents_and_foreign_source_fail_closed(self):
        pending = crown_pending()
        construction = {"action_request_id": "construction-submit-1",
                        "episode_run_id": pending["episode_run_id"],
                        "actor_character_id": 31254, "pre_native_revision": 60,
                        "source_bridge_pid": 230672,
                        "source_bridge_creation_date": "birth-1"}
        ambiguous = material.classify_pending_material_v1(
            frame(), crown=pending, construction=construction,
            bridge_pid=230672, bridge_creation_date="birth-1")
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertFalse(ambiguous["business_credit"])
        foreign = material.classify_pending_material_v1(
            frame(), crown=pending, bridge_pid=230673)
        self.assertEqual(foreign["status"], "cold_receipt")

    def test_faction_wait_ignores_intermediate_gold_and_waits_for_native_revision(self):
        before = frame(revision=506, native_revision=506, prestige=1)
        before["played_character"]["gold"] = 25810153
        intermediate = frame(revision=507, native_revision=506, prestige=1)
        intermediate["played_character"]["gold"] = 15810153
        final = frame(revision=508, native_revision=507, prestige=1)
        final["played_character"]["gold"] = 15810153
        for item in (before, intermediate, final):
            item["date_raw"] = 53153304
        pending = {"pre_snapshot_revision": 506, "pre_date_raw": 53153304,
                   "episode_run_id": before["episode_run_id"]}
        observed = []

        class Driver:
            def _wait_for_snapshot(self, starting, predicate, *, timeout_seconds):
                self.timeout = timeout_seconds
                for candidate in (intermediate, final):
                    observed.append(predicate(candidate))
                    if observed[-1]:
                        return candidate
                return candidate

        with self.assertRaises(faction.PreSubmissionRevisionMismatchError):
            faction._wait_for_pending_paused_revision_v1(Driver(), before, pending)
        self.assertEqual(observed, [False, True])


if __name__ == "__main__":
    unittest.main()
