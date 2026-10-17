import copy
import json
from pathlib import Path
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from g2_saved_campaign import sentinel_partial_recovery as recovery

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "p41_sentinel_partial_projection.json").read_bytes())


class Tests(unittest.TestCase):
    def qualify(self, fixture):
        return recovery.qualify(fixture["original"], fixture["plan"], fixture["state"], fixture["launch"])

    def observed(self, fixture):
        qualification = self.qualify(fixture)
        return recovery.qualify_stable_observations(fixture["fresh1"], fixture["fresh2"],
            before=fixture["state"]["before"], launch=fixture["launch"],
            lifecycle=fixture["fresh1"]["succession_lifecycle"], normalize_lifecycle=lambda value: value,
            until=qualification["until"], expected_birth=fixture["expected_birth"],
            observed_births=(fixture["expected_birth"], fixture["expected_birth"]))

    def test_actual_completed_error_and_plan(self):
        qualified = self.qualify(FIXTURE)
        self.assertTrue(qualified["original_submission_may_have_applied"])
        self.assertFalse(qualified["read_only_precondition"])
        for name in ("failed_pending_cycle_credit", "failed_pending_date_credit", "failed_pending_business_credit"):
            self.assertEqual(qualified[name], 0)
        self.assertTrue(FIXTURE["original"]["result"]["is_error"])

    def test_actual_two_stable_fresh_frames(self):
        current = self.observed(FIXTURE)
        self.assertEqual(current["date_raw"] - FIXTURE["state"]["before"]["date_raw"], 6 * 24)
        self.assertNotEqual(current["revision"], current["native_revision"])
        self.assertEqual(current["decision_identity"][0], "interaction")

    def test_project_only_failed_branch_preserves_durable_state(self):
        state = copy.deepcopy(FIXTURE["state"])
        state.update(counts={"synthetic_preservation_sentinel": 3},
            governance_result_state={"pending_business": {"status": "must_remain"}},
            checkpoint_calendar_v1={"last_saved_date_raw": state["before"]["date_raw"] - 24})
        projected = recovery.projected_state(state, self.observed(FIXTURE), "actual-fresh-read-receipt.json")
        self.assertIsNone(projected["pending_cycle"])
        for key in ("completed_cycles", "counts", "governance_result_state", "checkpoint_calendar_v1"):
            self.assertEqual(projected[key], state[key])
        self.assertIsNotNone(state["pending_cycle"])
        self.assertTrue(projected["checkpoint_dirty_since_save"])

    def test_error_plan_pending_mutations(self):
        cases = [
            lambda f: f["original"]["result"].update(is_error=False),
            lambda f: f["original"].update(client_error="outcome unknown"),
            lambda f: f["original"]["result"]["content"][0].update(text="native timeout"),
            lambda f: f["original"]["result"]["content"][0].update(text=f["original"]["result"]["content"][0]["text"] + "; cleanup failed"),
            lambda f: f["original"]["request"].update(arguments={"action": "replay"}),
            lambda f: f["plan"].update(game_pid=f["launch"]["pid"] + 1),
            lambda f: f["plan"]["result"]["structured_content"].update(revision=f["state"]["before"]["native_revision"]),
            lambda f: f["plan"]["result"]["structured_content"]["plan"].update(selected_step="life-advance-one-day"),
            lambda f: f["state"]["pending_cycle"].update(stage="auto_verified"),
            lambda f: f["state"].update(pending_checkpoint={}),
            lambda f: f["state"].update(terminal={}),
        ]
        for change in cases:
            with self.subTest(line=change.__code__.co_firstlineno):
                fixture = copy.deepcopy(FIXTURE)
                change(fixture)
                with self.assertRaises(ValueError): self.qualify(fixture)

    def test_fresh_observation_mutations(self):
        cases = [lambda f: f["fresh2"].update(paused=False),
            lambda f: f["fresh2"].update(date_raw=f["fresh2"]["date_raw"] + 24),
            lambda f: f["fresh2"].update(revision=f["fresh2"]["revision"] + 1),
            lambda f: f["fresh2"]["pending_character_interaction"].update(instance_id=1),
            lambda f: f["fresh2"]["pending_character_interaction"].update(source="synthetic"),
            lambda f: f["fresh2"]["played_character"].update(alive=False),
            lambda f: f["fresh2"].update(episode_run_id="another-episode")]
        for change in cases:
            with self.subTest(line=change.__code__.co_firstlineno):
                fixture = copy.deepcopy(FIXTURE)
                change(fixture)
                with self.assertRaises(ValueError): self.observed(fixture)

    def test_full_birth_mismatch(self):
        qualified = self.qualify(FIXTURE)
        with self.assertRaises(ValueError):
            recovery.qualify_stable_observations(FIXTURE["fresh1"], FIXTURE["fresh2"],
                before=FIXTURE["state"]["before"], launch=FIXTURE["launch"],
                lifecycle=FIXTURE["fresh1"]["succession_lifecycle"], normalize_lifecycle=lambda x: x,
                until=qualified["until"], expected_birth=FIXTURE["expected_birth"],
                observed_births=(FIXTURE["expected_birth"], FIXTURE["expected_birth"] + 1))


if __name__ == "__main__": unittest.main()
