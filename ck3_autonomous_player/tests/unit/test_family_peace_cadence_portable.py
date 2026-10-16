"""P19 completed peace frames projected into a small committed fixture."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xar_autoplayer.bridge import service as SERVICE
from xar_autoplayer.bridge import family_wartime_opportunity_cadence_v1 as cadence

FIXTURE=Path(__file__).resolve().parents[1]/"fixtures"/"family_p19_completed_projection.json"
ACTUAL=json.loads(FIXTURE.read_text(encoding="utf-8"))

def actual(seq):
    return ACTUAL["peace"][str(seq)]["projected"]

def snapshot(inner, *, spouse=None):
    frame = inner["planning_source_frame"]
    receipt = inner["family_wartime_opportunity_cooldown_v1"]
    spouse = receipt["player_spouse_signature"] if spouse is None else spouse
    return {
        "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "episode_run_id": frame["episode_run_id"],
        "episode_character_id": frame["actor_character_id"],
        "played_character": {"character_id": frame["actor_character_id"],
                             "alive": True, "betrothed_id": spouse[0],
                             "primary_spouse_id": spouse[1], "spouse_ids": spouse[2]},
        "succession_expectation": {"status": "available",
            "expected_successor_character_id": receipt["expected_successor_character_id"]},
        "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession"},
        "paused": True, "map_ready": True, "active_wars": [], "player_armies": [],
        "active_event": None, "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


class FakeDriver:
    allow_private_current_first_heir_betrothal_fulfillment = False
    allow_private_current_first_heir_relationship_query = True

    def __init__(self, source):
        self.source = source

    def _with_internal_planning_view(self, snapshot, callback):
        return {"pending": None}

    def take_internal_semantic_snapshot(self):
        return self.source


class PeaceFamilyTests(unittest.TestCase):
    def setUp(self):
        self.state_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.state_temp.cleanup)
        self.state_dir = Path(self.state_temp.name)
        self.obj = object.__new__(SERVICE.GameplayBridgeService)
        self.obj._strategy_state_dir = lambda: self.state_dir
        self.obj._observed_planning_source_frame = lambda source: {
            "status": "complete", "snapshot_id": source["snapshot_id"],
            "revision": source["revision"], "native_revision": source["native_revision"],
            "date_raw": source["date_raw"],
            "actor_character_id": source["played_character"]["character_id"],
            "episode_run_id": source["episode_run_id"],
        }
        self.obj._skip_private_family_opportunity_during_cooldown_v1 = lambda *a, **k: None
        self.obj._plan_private_family_education_v1 = lambda result, source, **kw: result
        self.obj._unresolved_family_child_focus_v1 = lambda *a: {"pending": None}

    def _review(self, seq, *, plan=None):
        inner = actual(seq)
        source = snapshot(inner)
        frame = inner["planning_source_frame"]
        self.obj.driver = FakeDriver(source)
        planned = {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
                   "plan": {"selected_step": "life-advance"}}
        real_plan = inner["plan"] if plan is None else plan
        with patch.object(SERVICE, "plan_family_marriage_private",
                          lambda driver, current, snap, **kw: {
                              **current, "plan": real_plan}):
            reviewed = self.obj._plan_private_family_opportunity_v1(planned, source)
        return inner, source, reviewed

    def test_two_real_peace_noops_activate_and_skip_third(self):
        first, source1, reviewed1 = self._review(570)
        self.assertEqual(cadence.complete_noop(first["planning_source_frame"],
            reviewed1["plan"], reviewed1["plan"]["_family_wartime_review_v1"]),
            (39979, [515, 149, 22]))
        observed1 = cadence.observe_after_turn(self.state_dir,
            first["planning_source_frame"], reviewed1["plan"], first)
        self.assertEqual(observed1["consecutive_noop_dates"], 1)
        # A second observation of the same query must not count twice.
        cadence.observe_after_turn(self.state_dir, first["planning_source_frame"],
                                   reviewed1["plan"], first)
        second, source2, reviewed2 = self._review(576)
        observed2 = cadence.observe_after_turn(self.state_dir,
            second["planning_source_frame"], reviewed2["plan"], second)
        self.assertEqual(observed2["status"], "active")
        self.assertEqual(observed2["cooldown_until_date_raw"],
                         second["result"]["ending_date_raw"] + 720)
        third = actual(580)
        source3 = snapshot(third)
        self.obj.driver = FakeDriver(source3)
        planned = {"plan": {"selected_step": "life-advance"}}
        relation = third["plan"]["family_marriage_current_relationship"]
        from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport
        with (patch.object(SERVICE, "read_family_marriage_ledger",
                           lambda state_dir: {"pending": None, "resolved": None}),
              patch.object(transport, "query_current_first_heir_relationship_private_v1",
                           lambda *a, **k: relation),
              patch.object(SERVICE, "plan_family_marriage_private",
                           side_effect=AssertionError("heavy family read was not skipped"))):
            skipped = self.obj._plan_private_family_opportunity_v1(planned, source3)
        self.assertEqual(skipped["plan"]["family_wartime_opportunity_cooldown_v1"]["status"],
                         "active")
        self.assertEqual(skipped["plan"]["selected_step"], "life-advance")

    def test_unknown_or_pending_cannot_count_or_skip(self):
        first = actual(570)
        altered = {**first["plan"], "family_marriage_private_diagnostic":
                   {**first["plan"]["family_marriage_private_diagnostic"], "rows": []}}
        _, _, reviewed = self._review(570, plan=altered)
        self.assertIsNone(cadence.complete_noop(first["planning_source_frame"],
            reviewed["plan"], reviewed["plan"]["_family_wartime_review_v1"]))
        status = cadence.observe_after_turn(self.state_dir,
            first["planning_source_frame"], reviewed["plan"], first)
        self.assertEqual(status["status"], "inactive")
        self.assertEqual(status["consecutive_noop_dates"], 0)
        pending = {"plan": {"selected_step": "life-advance",
                            "family_marriage_pending": {"status": "pending"}}}
        self.assertIsNone(self.obj._skip_private_family_wartime_during_cooldown_v1(
            pending, snapshot(first)))

    def test_actual_material_marriage_resets(self):
        first, _, reviewed1 = self._review(570)
        cadence.observe_after_turn(self.state_dir,
            first["planning_source_frame"], reviewed1["plan"], first)
        second, _, reviewed2 = self._review(576)
        cadence.observe_after_turn(self.state_dir,
            second["planning_source_frame"], reviewed2["plan"], second)
        material = {"status": "executed",
                    "selected_step": "query-observed-first-heir-marriage-result-v1-private",
                    "result": {"status": "marriage", "material_result": True}}
        state = cadence.observe_after_turn(self.state_dir,
            second["planning_source_frame"], reviewed2["plan"], material)
        self.assertEqual(state["status"], "inactive")
        self.assertEqual(state["consecutive_noop_dates"], 0)

    def test_spouse_or_heir_change_cancels_stale_skip(self):
        first, _, reviewed1 = self._review(570)
        cadence.observe_after_turn(self.state_dir,
            first["planning_source_frame"], reviewed1["plan"], first)
        second, _, reviewed2 = self._review(576)
        cadence.observe_after_turn(self.state_dir,
            second["planning_source_frame"], reviewed2["plan"], second)
        third = actual(580)
        base = snapshot(third)
        planned = {"plan": {"selected_step": "life-advance"}}
        with patch.object(SERVICE, "read_family_marriage_ledger",
                          lambda state_dir: {"pending": None, "resolved": None}):
            spouse_changed = snapshot(third, spouse=[None, 30888, [30888]])
            self.obj.driver = FakeDriver(spouse_changed)
            self.assertIsNone(self.obj._skip_private_family_wartime_during_cooldown_v1(
                planned, spouse_changed))
            self.assertEqual(cadence.view(self.state_dir,
                third["planning_source_frame"])["status"], "inactive")
            # Recreate a valid cooldown to test heir drift independently.
            cadence.observe_after_turn(self.state_dir,
                first["planning_source_frame"], reviewed1["plan"], first)
            cadence.observe_after_turn(self.state_dir,
                second["planning_source_frame"], reviewed2["plan"], second)
            heir_changed = dict(base)
            heir_changed["succession_expectation"] = {
                "status": "available", "expected_successor_character_id": 39980}
            self.obj.driver = FakeDriver(heir_changed)
            self.assertIsNone(self.obj._skip_private_family_wartime_during_cooldown_v1(
                planned, heir_changed))

    def test_education_unknown_does_not_mark_full_noop(self):
        first = actual(570)
        altered = {**first["plan"], "family_education_needs":
                   {**first["plan"]["family_education_needs"],
                    "known_empty": False}}
        _, _, reviewed = self._review(570, plan=altered)
        self.assertNotIn("_family_wartime_review_v1", reviewed["plan"])


if __name__ == "__main__":
    unittest.main()
