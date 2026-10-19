"""Exercise the ordinary query hook without a Driver or a current Game."""
from copy import deepcopy
import unittest

from test_realm_membership_feedback_v1 import inputs, COMPONENT
from xar_autoplayer.bridge.realm_membership_after_query_v1 import (
    begin_realm_membership_plan_v1 as begin,
    bind_realm_membership_plan_v1 as bind,
    finalize_realm_membership_plan_v1 as finalize,
    cancel_realm_membership_plan_v1 as cancel,
    enter_realm_membership_planning_v1 as enter,
    leave_realm_membership_planning_v1 as leave,
    bind_current_realm_membership_plan_v1 as bind_current,
    observe_realm_membership_after_query_v1 as consume,
    realm_membership_summary_for_plan_v1 as summary,
)


class Owner:
    def snapshot(self, **kwargs):
        raise AssertionError("realm feedback must not read another snapshot")


def turn(args, owner):
    snap, frame, packet = deepcopy(args)
    del packet["binding"]
    packet.update(step="query-player-faction-alerts-v1", accepted=True, status="available",
        snapshot_revision=frame["native_revision"], player_faction_alerts_ready=True,
        queried_snapshot_id=frame["snapshot_id"], queried_revision=frame["revision"],
        queried_native_revision=frame["native_revision"])
    planned = {"planning_source_frame": frame, "plan": {"selected_step": "query-player-faction-alerts-v1"}}
    epoch = begin(owner)
    assert bind(owner, epoch, planned, snap)
    planned = deepcopy(planned)  # Service.plan_turn's real public-copy boundary
    assert finalize(owner, epoch, planned)
    assert "_realm_membership_query_snapshot_v1" not in planned
    return planned, {"status": "executed", "selected_step": "query-player-faction-alerts-v1", "result": packet}


class RealmMembershipAfterQueryTests(unittest.TestCase):
    def test_ordinary_query_retains_and_next_query_reports_vassal_loss(self):
        owner = Owner()
        planned, outcome = turn(inputs(), owner)
        consume(owner, planned, outcome)
        self.assertEqual(summary(owner, planned["planning_source_frame"])["current_realm_county_count"], 3)
        planned, outcome = turn(inputs((2231, 2262), native=42, public=10, date=53144352, query=2), owner)
        result = consume(owner, planned, outcome)
        self.assertEqual(result["realm_membership_feedback_v1"]["difference"]["lost_county_title_ids"], [2488])
        current = summary(owner, planned["planning_source_frame"])
        self.assertEqual(current["current_realm_county_count"], 2)
        self.assertTrue(current["loss_observed"])
        later_frame = {**planned["planning_source_frame"], "native_revision": 43}
        historical = summary(owner, later_frame)
        self.assertEqual(historical["status"], "historical")
        self.assertIsNone(historical["current_realm_county_count"])
        self.assertEqual(historical["last_observed_realm_county_count"], 2)

    def test_missing_optional_or_original_snapshot_does_not_erase_or_block(self):
        owner = Owner(); planned, outcome = turn(inputs(), owner)
        consume(owner, planned, outcome)
        previous = deepcopy(owner._realm_membership_observation_v1)
        planned, outcome = turn(inputs(native=42, public=10, query=2), owner)
        del outcome["result"]["player_faction_alerts"][COMPONENT]
        result = consume(owner, planned, outcome)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertEqual(owner._realm_membership_observation_v1, previous)
        self.assertIsNone(owner._realm_membership_query_slot_v1)
        cancel(owner, planned)
        self.assertEqual(consume(owner, planned, outcome)["status"], "executed")

    def test_new_plan_late_binding_failure_and_mutated_frame_cannot_adopt_old_slot(self):
        owner = Owner(); old_plan, old_outcome = turn(inputs(), owner)
        old_epoch = owner._realm_membership_plan_epoch_v1
        epoch = begin(owner)
        self.assertIsNone(owner._realm_membership_query_slot_v1)
        self.assertFalse(bind(owner, old_epoch, old_plan, inputs()[0]))
        new_plan, new_outcome = turn(inputs(native=42, public=10, query=2), owner)
        self.assertEqual(consume(owner, old_plan, old_outcome)["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertIs(owner._realm_membership_query_slot_v1["plan"], new_plan)
        new_plan["planning_source_frame"]["actor_character_id"] = 7
        self.assertEqual(consume(owner, new_plan, new_outcome)["realm_membership_feedback_v1"]["status"], "unavailable")
        self.assertIsNone(owner._realm_membership_query_slot_v1)
        self.assertFalse(hasattr(owner, "_realm_membership_observation_v1"))

    def test_cancel_and_concurrent_completion_are_one_shot_without_extra_reads(self):
        from concurrent.futures import ThreadPoolExecutor
        owner = Owner(); planned, outcome = turn(inputs(), owner)
        cancel(owner, planned)
        self.assertEqual(consume(owner, planned, outcome)["realm_membership_feedback_v1"]["status"], "unavailable")
        planned, outcome = turn(inputs(), owner)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: consume(owner, planned, outcome), range(2)))
        self.assertEqual(sorted(r["realm_membership_feedback_v1"]["status"] for r in results), ["available", "unavailable"])
        self.assertIsNone(owner._realm_membership_query_slot_v1)
        epoch = owner._realm_membership_plan_epoch_v1
        self.assertFalse(bind(owner, epoch, planned, inputs()[0]))

    def test_detached_plan_priority_override_and_failed_planning_release_snapshot(self):
        owner = Owner(); snap, frame, _ = inputs()
        candidate = {"plan": {"selected_step": "query-player-faction-alerts-v1"}, "planning_source_frame": frame}
        epoch = begin(owner); self.assertTrue(bind(owner, epoch, candidate, snap))
        override = deepcopy(candidate); override["plan"]["selected_step"] = "life-advance"
        self.assertFalse(finalize(owner, epoch, override))
        self.assertIsNone(owner._realm_membership_query_slot_v1)

    def test_private_planning_scope_survives_public_copy_without_snapshot_or_address(self):
        owner = Owner(); snap, frame, _ = inputs()
        candidate = {"plan": {"selected_step": "query-player-faction-alerts-v1"}, "planning_source_frame": frame}
        self.assertFalse(bind_current(owner, candidate, snap))
        epoch, token = enter(owner)
        try:
            self.assertTrue(bind_current(owner, candidate, snap))
            public = deepcopy(candidate)
            self.assertTrue(finalize(owner, epoch, public))
        finally:
            leave(token)
        self.assertEqual(set(public), {"plan", "planning_source_frame"})
        self.assertIs(owner._realm_membership_query_slot_v1["snapshot"], snap)
        self.assertIs(owner._realm_membership_query_slot_v1["plan"], public)
        self.assertFalse(bind_current(owner, candidate, snap))
        cancel(owner, public)
        self.assertIsNone(owner._realm_membership_query_slot_v1)
        epoch = begin(owner); self.assertTrue(bind(owner, epoch, candidate, snap))
        cancel(owner, epoch=epoch)
        self.assertIsNone(owner._realm_membership_query_slot_v1)

    def test_other_turns_do_zero_work_and_never_synthesize_input(self):
        owner = Owner(); outcome = {"status": "executed", "selected_step": "life-advance"}
        self.assertIs(consume(owner, {}, outcome), outcome)
        self.assertEqual(summary(owner, {})["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
