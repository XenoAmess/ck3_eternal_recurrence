"""New scheduler path only; all engine/source frames below are synthetic."""
from __future__ import annotations
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
from xar_autoplayer.ordinary_sway_schedule_v1 import (
    plan_ordinary_sway_schedule_v1 as plan,
    complete_ordinary_sway_check_v1 as complete,
)

def frame(date=1000, actor=7):
    return {
        "paused": True, "map_ready": True, "revision": 4,
        "native_revision": 3, "date_raw": date,
        "played_character": {"character_id": actor, "alive": True},
        "active_context": {"active_event": None, "pending_character_interaction": None},
    }

def root(date=1000, actor=7, targets=None):
    return {
        "status": "available", "player_character_id": actor,
        "player_character_alive": True, "snapshot_revision": 3, "date_raw": date,
        "direct_landed_vassal_character_ids": [900, 100, 500] if targets is None else targets,
    }

def applied(actor=7, target=900):
    return {
        "pending": None,
        "resolved": {
            "status": "applied", "postcondition_verified": True,
            "actor_character_id": actor, "target_character_id": target,
            "action_id": "synthetic-original",
        },
    }

class ScheduleTests(unittest.TestCase):
    def test_native_order_rotation_and_two_noops_then_saturated_month(self):
        first = plan(frame(), selected_step="life-advance", root=root())
        self.assertEqual(first["target_character_id"], 900)
        self.assertFalse(first["native_ai_rank_claimed"])
        state = complete(first["state"], date_raw=1000, job_kind=first["job"],
                         outcome="no_operation", target_character_id=900)
        self.assertEqual(plan(frame(), selected_step="life-advance", root=root(), state=state)["job"], None)
        second = plan(frame(1024), selected_step="life-advance", root=root(1024), state=state)
        self.assertEqual(second["target_character_id"], 100)
        state = complete(second["state"], date_raw=1024, job_kind=second["job"],
                         outcome="no_operation", target_character_id=100)
        self.assertEqual(state["no_operation_count"], 2)
        self.assertEqual(state["next_check_date_raw"], 1744)
        self.assertIsNone(plan(frame(1720), selected_step="life-advance", root=root(1720), state=state)["job"])
        third = plan(frame(1744), selected_step="life-advance", root=root(1744), state=state)
        self.assertEqual(third["target_character_id"], 500)
        after = complete(third["state"], date_raw=1744, job_kind=third["job"],
                         outcome="no_operation", target_character_id=500)
        self.assertEqual(after["no_operation_count"], 2)
        self.assertEqual(after["next_check_date_raw"], 2464)

    def test_actual_frontier_and_actor_changes_reset_cooldown_without_id_ranking(self):
        original = plan(frame(), selected_step="life-advance", root=root())["state"]
        state = {**original, "no_operation_count": 2, "last_check_date_raw": 1000,
                 "next_check_date_raw": 5000, "last_target_character_id": 900}
        changed = plan(frame(1024), selected_step="life-advance",
                       root=root(1024, targets=[900, 500, 600]), state=state)
        self.assertEqual(changed["target_character_id"], 500)
        self.assertEqual(changed["state"]["no_operation_count"], 0)
        successor = plan(frame(1024, 8), selected_step="life-advance",
                         root=root(1024, 8, [600, 100]), state=state)
        self.assertEqual(successor["target_character_id"], 600)
        self.assertEqual(successor["state"]["actor_character_id"], 8)

    def test_reordered_frontier_alone_does_not_rearm_cooldown(self):
        state = plan(frame(), selected_step="life-advance", root=root())["state"]
        state.update(no_operation_count=2, last_check_date_raw=1000, next_check_date_raw=5000)
        result = plan(frame(1024), selected_step="life-advance",
                      root=root(1024, targets=[500, 900, 100]), state=state)
        self.assertIsNone(result["job"])
        self.assertEqual(result["state"]["no_operation_count"], 2)

    def test_war_priority_and_mandatory_context_preserve_ordinary_turn(self):
        state = {"actor_character_id": 7, "no_operation_count": 2}
        result = plan(frame(), selected_step="native-defend-war", root=root(), state=state)
        self.assertIsNone(result["job"])
        self.assertEqual(result["reason"], "preserve_selected_step")
        modal = frame()
        modal["active_context"]["active_event"] = {"instance_id": 9}
        self.assertIsNone(plan(modal, selected_step="life-advance", root=root())["job"])

    def test_pending_is_readonly_and_monthly_never_resubmitted(self):
        ledger = {"pending": {"actor_character_id": 7, "target_character_id": 900,
                              "action_id": "pending-once"}, "resolved": None}
        job = plan(frame(), selected_step="life-advance", ledger=ledger)
        self.assertEqual(job["job"], "reconcile_pending")
        self.assertFalse(job["submit_allowed"])
        state = complete(job["state"], date_raw=1000, job_kind=job["job"], outcome="pending")
        self.assertIsNone(plan(frame(1024), selected_step="life-advance", ledger=ledger, state=state)["job"])
        self.assertEqual(plan(frame(1720), selected_step="life-advance", ledger=ledger, state=state)["job"], "reconcile_pending")
        foreign = copy.deepcopy(ledger)
        foreign["pending"]["actor_character_id"] = 8
        self.assertEqual(plan(frame(), selected_step="life-advance", ledger=foreign)["reason"], "unresolved_other_actor")

    def test_applied_observation_monthly_success_and_failure_same_day_attach(self):
        state = plan(frame(), selected_step="life-advance", root=root())["state"]
        state = complete(state, date_raw=1000, job_kind="query_selected_target",
                         outcome="applied", target_character_id=900, action_id="synthetic-original")
        ledger = applied()
        job = plan(frame(), selected_step="life-advance", ledger=ledger, state=state)
        self.assertEqual(job["job"], "observe_applied")
        state = complete(job["state"], date_raw=1000, job_kind=job["job"],
                         outcome="unavailable", action_id=job["action_id"])
        self.assertEqual(state["no_operation_count"], 0)
        self.assertIsNone(plan(frame(1024), selected_step="life-advance", ledger=ledger, state=state)["job"])
        self.assertEqual(plan(frame(1720), selected_step="life-advance", ledger=ledger, state=state)["job"], "observe_applied")

    def test_terminal_allows_nomination_without_claiming_cause_or_moving_old_actor(self):
        ledger = applied()
        ledger["resolved"]["terminal_intervention"] = {
            "instance_terminal_outcome_observed": True, "terminal_cause_observed": False}
        state = plan(frame(), selected_step="life-advance", root=root())["state"]
        state["last_target_character_id"] = 900
        result = plan(frame(), selected_step="life-advance", root=root(), ledger=ledger, state=state)
        self.assertEqual(result["target_character_id"], 100)
        foreign = applied(actor=29829, target=34333)
        result = plan(frame(), selected_step="life-advance", root=root(), ledger=foreign)
        self.assertEqual(result["target_character_id"], 900)

    def test_unavailable_does_not_become_empty_or_noop(self):
        bad = root()
        bad["date_raw"] = 999
        result = plan(frame(), selected_step="life-advance", root=bad)
        self.assertIsNone(result["job"])
        self.assertEqual(result["state"]["no_operation_count"], 0)
        empty = plan(frame(), selected_step="life-advance", root=root(targets=[]))
        self.assertEqual(empty["job"], "complete_no_relation")
        failed = complete(result["state"], date_raw=1000, job_kind="query_selected_target", outcome="unavailable")
        self.assertEqual(failed["no_operation_count"], 0)
        self.assertEqual(failed["next_check_date_raw"], 1720)

    def test_observed_terminal_opens_opportunity_without_another_month(self):
        ledger = applied()
        initial = plan(frame(), selected_step="life-advance", root=root())["state"]
        observed = complete(initial, date_raw=1000, job_kind="observe_applied",
                            outcome="observed", action_id="synthetic-original")
        observed["last_target_character_id"] = 900
        ledger["resolved"]["terminal_intervention"] = {
            "instance_terminal_outcome_observed": True, "terminal_cause_observed": False}
        same_day = plan(frame(), selected_step="life-advance", root=root(),
                        ledger=ledger, state=observed)
        self.assertIsNone(same_day["job"])
        self.assertIsNone(same_day["state"]["next_check_date_raw"])
        next_day = plan(frame(1024), selected_step="life-advance", root=root(1024),
                        ledger=ledger, state=same_day["state"])
        self.assertEqual(next_day["target_character_id"], 100)
        self.assertEqual(next_day["state"]["no_operation_count"], 0)

    def test_inputs_unchanged(self):
        f, r, ledger = frame(), root(), {"pending": None, "resolved": None}
        before = copy.deepcopy((f, r, ledger))
        result = plan(f, selected_step="life-advance", root=r, ledger=ledger)
        complete(result["state"], date_raw=1000, job_kind=result["job"],
                 outcome="no_operation", target_character_id=900)
        self.assertEqual((f, r, ledger), before)

    def test_new_nomination_to_existing_formal_consumer_once_and_following(self):
        from xar_autoplayer.sway_formal_consumer import (
            consume_sway_private_once, consume_sway_following_turn, read_sway_ledger,
        )
        nomination = plan(frame(), selected_step="life-advance", root=root())
        target = nomination["target_character_id"]
        before = frame()
        quote = {
            "schema": "active-scheme-sway-private-read-v1",
            "snapshot_revision": 3, "capture_epoch": 10, "container_generation": 20,
            "date_raw": 1000, "actor_character_id": 7, "target_character_id": target,
            "target_opinion_of_actor": 5, "active_scheme_count": 0,
            "matching_sway_active": False, "native_complete_can_send": True,
            "native_legal_now": True, "queried_revision": 4, "queried_native_revision": 3,
        }
        class Driver:
            allow_private_active_scheme_sway_action = True
            def __init__(self, state_dir):
                self.state_dir = state_dir
                self.submits = self.receipts = self.reads = 0
            def take_snapshot(self):
                return copy.deepcopy(before)
            def submit_active_scheme_sway_private_v1(self, *, readback, action_id):
                self.submits += 1
                self.action_id = action_id
                return {"stage": "submitted_verification_pending", "action_id": action_id}
            def query_active_scheme_sway_receipt_private_v1(self, **kwargs):
                self.receipts += 1
                return {"schema": "active-scheme-sway-formal-private-v1", "stage": "applied",
                        "postcondition_verified": True, "action_id": self.action_id,
                        "actor_character_id": 7, "target_character_id": target,
                        "scheme_instance_id": 16777233, "scheme_instance_generation": 1}
            def query_active_scheme_sway_target_private_v1(self, **kwargs):
                self.reads += 1
                return {**quote, "capture_epoch": 12, "active_scheme_count": 1,
                        "matching_sway_active": True, "native_complete_can_send": False,
                        "native_legal_now": False}
        storage = Path(os.environ.get("XAR_M6_SWAY_TEST_ROOT", tempfile.gettempdir())) / "xar-sway-scheduler-tests"
        storage.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=storage) as directory:
            driver = Driver(Path(directory))
            result = consume_sway_private_once(driver, target_character_id=target,
                                               snapshot=before, readback=quote)
            self.assertEqual(result["status"], "applied")
            self.assertEqual((driver.submits, driver.receipts, driver.reads), (1, 1, 1))
            ledger = read_sway_ledger(Path(directory))
            job = plan(frame(), selected_step="life-advance", ledger=ledger,
                       state=nomination["state"])
            self.assertEqual(job["job"], "observe_applied")
            following = frame(1024)
            following["native_revision"] = 4
            consumed = consume_sway_following_turn(Path(directory), following)
            self.assertTrue(consumed["next_turn_consumed"])
            current = driver.query_active_scheme_sway_target_private_v1()
            duplicate = consume_sway_private_once(driver, target_character_id=target,
                                                  snapshot=before, readback=current)
            self.assertEqual(duplicate["status"], "already_applied")
            self.assertEqual(driver.submits, 1)

    def test_full32_high_bit_target_nomination_and_completion_state(self):
        import json
        high = 0x80000001
        job = plan(frame(), selected_step="life-advance", root=root(targets=[high, 100]))
        self.assertEqual(job["target_character_id"], high)
        state = complete(job["state"], date_raw=1000, job_kind=job["job"],
                         outcome="no_operation", target_character_id=high)
        self.assertEqual(state["last_target_character_id"], high)
        restored = json.loads(json.dumps(state))
        next_job = plan(frame(1024), selected_step="life-advance",
                        root=root(1024, targets=[high, 100]), state=restored)
        self.assertEqual(next_job["target_character_id"], 100)
        self.assertEqual(restored["frontier_membership"], [100, high])
        invalid = plan(frame(), selected_step="life-advance", root=root(targets=[True]))
        self.assertEqual(invalid["reason"], "frontier_unavailable")

if __name__ == "__main__":
    unittest.main()
