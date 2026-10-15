"""Date-based recovery points survive query inflation and actual-save failures."""

import copy
import unittest

import root_checkpoint_calendar_cadence as cadence


def frame(day, revision=1):
    return {"date_raw": 1000000 + day * 24, "revision": revision,
            "snapshot_id": "native:" + str(revision), "actor_character_id": 12,
            "episode_run_id": "campaign"}


def cycle(state, day, *, wars=(), material=False, readonly=False):
    before = copy.deepcopy(state["before"])
    after = frame(day, before["revision"] + 1)
    pending = {"before": before, "selected_step": "query-army-strengths-v1" if readonly else "life-advance",
               "observation": {"existing_typed_material_verified": material}}
    if not readonly:
        pending["checkpoint_context"] = {
            "schema": "g2.queue.calendar-checkpoint-context/v1",
            "before": {key: before[key] for key in ("date_raw", "actor_character_id", "episode_run_id")},
            "after": dict(after), "war_ids": list(wars), "war_ended": False,
        }
    state["completed_cycles"] += 1
    due = cadence.checkpoint_after_settled_cycle(state, pending, after)
    state["before"] = after
    return due


def saved(state):
    cadence.checkpoint_saved(state, {"status": "saved", "date_raw": state["before"]["date_raw"],
                                   "episode_character_id": 12, "episode_run_id": "campaign"})


class CalendarCadenceTests(unittest.TestCase):
    def state(self):
        return {"completed_cycles": 0, "terminal": None,
                "checkpoint_dirty_since_save": False, "before": frame(0)}

    def test_queries_do_not_inflate_save_rate(self):
        for count in (0, 1, 9, 40):
            state, saves = self.state(), []
            for day in range(7, 127, 7):
                for _ in range(count):
                    self.assertFalse(cycle(state, day - 7, readonly=True))
                if cycle(state, day):
                    saves.append(day)
                    saved(state)
            self.assertEqual(saves, [91])

    def test_war_uses_normal_quarterly_interval_and_war_end_forces_checkpoint(self):
        state = self.state()
        self.assertFalse(cycle(state, 1, wars=[44]))
        self.assertFalse(cycle(state, 6, wars=[44]))
        self.assertFalse(cycle(state, 7, wars=[44]))
        self.assertFalse(cycle(state, 89, wars=[44]))
        self.assertTrue(cycle(state, 90, wars=[44]))
        saved(state)
        self.assertTrue(cycle(state, 91, wars=[]))
        self.assertEqual(state["checkpoint_last_decision"]["reason"], "critical_outcome_checkpoint")

    def test_verified_material_outcome_saves_at_same_date(self):
        state = self.state()
        self.assertFalse(cycle(state, 1))
        self.assertTrue(cycle(state, 1, material=True))
        saved(state)
        self.assertFalse(cycle(state, 1, readonly=True))
        self.assertFalse(state["checkpoint_due_after_readonly_chain"])

    def test_unknown_legacy_dirty_state_keeps_conservative_fallback(self):
        state = self.state()
        state.update(checkpoint_dirty_since_save=True, completed_cycles=4)
        self.assertFalse(cycle(state, 0, readonly=True))
        self.assertTrue(state["checkpoint_due_after_readonly_chain"])
        self.assertTrue(cycle(state, 1))

    def test_unconfirmed_save_does_not_reset_calendar(self):
        state = self.state()
        self.assertTrue(cycle(state, 91))
        old_clock = copy.deepcopy(state[cadence.STATE_KEY])
        with self.assertRaises(ValueError):
            cadence.checkpoint_saved(state, {"status": "submitted", "date_raw": frame(91)["date_raw"]})
        self.assertEqual(old_clock, state[cadence.STATE_KEY])
        self.assertTrue(state["checkpoint_dirty_since_save"])
        self.assertTrue(cycle(state, 92))

    def test_actor_terminal_does_not_bypass_existing_handoff(self):
        state = self.state()
        state["terminal"] = "actual_actor_changed"
        self.assertFalse(cycle(state, 91))

    def test_saved_episode_origin_is_not_confused_with_current_actor(self):
        state = self.state()
        state["before"]["actor_character_id"] = 13
        cadence.checkpoint_saved(state, {"status": "saved", "date_raw": state["before"]["date_raw"],
                                        "episode_character_id": 12, "episode_run_id": "campaign"})
        self.assertEqual(state[cadence.STATE_KEY]["actor_character_id"], 13)

    def test_context_requires_same_returned_frame(self):
        source = {"status": "complete", **frame(0)}
        body = {"status": "executed", "selected_step": "life-advance", "planning_source_frame": source,
                "result": {"step": "life-advance", "source": "native-composite", "backend_id": "native-headless",
                           "paused": True, "final_screen": "map_hud", "starting_date_raw": frame(0)["date_raw"],
                           "ending_date_raw": frame(7)["date_raw"], "elapsed_days": 7,
                           "snapshot_id": "native:2", "revision": 2,
                           "war_progress_before": {"date_raw": frame(0)["date_raw"], "wars": []},
                           "war_progress_after": {"date_raw": frame(7)["date_raw"], "wars": []}}}
        self.assertIsNotNone(cadence.checkpoint_context_from_auto(body))
        body["result"]["war_progress_after"]["date_raw"] += 24
        self.assertIsNone(cadence.checkpoint_context_from_auto(body))


if __name__ == "__main__":
    unittest.main()
