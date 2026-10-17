"""Source-bound completed P43 guardian negatives, with no Game dependency."""
import copy
import unittest
import json
import os
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('XAR_TEST_SDK_ROOT',str(HERE.parents[1]/'src')))
import xar_autoplayer.bridge as bridge
if os.environ.get('XAR_TEST_BRIDGE_OVERLAY'):
    bridge.__path__.insert(0,os.environ['XAR_TEST_BRIDGE_OVERLAY'])
FIXTURE={int(row['source_ref'].split('AUTO')[1]):row for row in
    json.loads((HERE.parent/'fixtures/family_guardian_p43_completed_projection_v1.json').read_text(encoding='utf-8'))['rows']}
from xar_autoplayer.bridge import family_guardian_negative_cadence_v1 as mod
from xar_autoplayer.family_education_needs_12004 import derive_family_education_needs_12004

def sample(seq):
    body=FIXTURE[seq]
    relationship=body['family_marriage_current_relationship']
    needs=derive_family_education_needs_12004(
        relationship['family_generation_education_decision_inputs_v1'],
        child_relation_materials=relationship.get('current_child_relation_materials_v1'),
        child_education_provider_inputs=relationship.get('current_child_education_provider_inputs_v1'),
        child_education_provider_source=relationship.get('current_child_education_provider_inputs_source_v1'))
    return (body['planning_source_frame'],needs['rows'][0],
            relationship['heir_character_id'],body['family_education_observations'][0])

class GuardianCadence(unittest.TestCase):
    def test_actual_two_dates_then_thirty_day_defer_and_same_frame_dedup(self):
        records = {}
        frame1, row1, heir1, obs1 = sample(555)
        scope1 = mod.source_scope(frame1, row1, heir1)
        self.assertIsNotNone(scope1)
        first = mod.observe(records, scope1, frame1, obs1["default_query"], obs1["request_attempts"], selected_step="life-advance")
        self.assertEqual(first["consecutive_observed_dates"], 1)
        self.assertEqual(mod.deferred(records, scope1, frame1)["status"], "same_frame_negative_reuse")
        self.assertIsNone(mod.observe(records, scope1, frame1, obs1["default_query"], obs1["request_attempts"], selected_step="life-advance"))
        self.assertEqual(records[row1["raw_character_id"]]["count"], 1)
        frame2, row2, heir2, obs2 = sample(559)
        scope2 = mod.source_scope(frame2, row2, heir2)
        self.assertEqual(scope2, scope1)
        self.assertIsNone(mod.deferred(records, scope2, frame2))
        second = mod.observe(records, scope2, frame2, obs2["default_query"], obs2["request_attempts"], selected_step="life-advance")
        self.assertEqual(second["consecutive_observed_dates"], 2)
        frame3, row3, heir3, _ = sample(578)
        scope3 = mod.source_scope(frame3, row3, heir3)
        self.assertEqual(scope3, scope1)
        self.assertEqual(mod.deferred(records, scope3, frame3)["status"], "policy_deferred")
        self.assertEqual(mod.deferred(records, scope3, frame3)["current_native_legal_status"], "unknown_without_fresh_query")
        expiry = dict(frame3, date_raw=second["cooldown_until_date_raw"])
        self.assertIsNone(mod.deferred(records, scope3, expiry))

    def test_scope_changes_or_unknown_never_defer(self):
        frame, row, heir, obs = sample(555)
        scope = mod.source_scope(frame, row, heir)
        records = {}
        mod.observe(records, scope, frame, obs["default_query"], obs["request_attempts"], selected_step="life-advance")
        records[row["raw_character_id"]]["count"] = 2
        records[row["raw_character_id"]]["cooldown_until_date_raw"] = frame["date_raw"] + 720
        future = dict(frame, date_raw=frame["date_raw"] + 24, native_revision=frame["native_revision"] + 1)
        for key, value in (("bridge_pid", frame["bridge_pid"] + 1),
                           ("connection_generation", frame["connection_generation"] + 1),
                           ("actor_character_id", frame["actor_character_id"] + 1),
                           ("episode_run_id", frame["episode_run_id"] + "x")):
            changed = dict(future, **{key: value})
            self.assertIsNone(mod.deferred(records, mod.source_scope(changed, row, heir), changed), key)
        for edit in (lambda r: r["values"].update(age_measure_raw=1),
                     lambda r: r["focus_management"].update(state="education_focus_present", current_key="education_martial"),
                     lambda r: r["current_court_owner"].update(owner_character_id_raw=999),
                     lambda r: r["education_provider_inputs"]["observation"].update(guardian_full_id=888)):
            changed_row = copy.deepcopy(row)
            edit(changed_row)
            self.assertIsNone(mod.deferred(records, mod.source_scope(future, changed_row, heir), future))
        self.assertIsNone(mod.deferred(records, mod.source_scope(future, row, heir + 1), future))
        bad = copy.deepcopy(obs["request_attempts"])
        bad[0]["query"]["character_interaction_ordinary_context"]["can_send"] = True
        self.assertIsNone(mod.observe({}, scope, frame, obs["default_query"], bad, selected_step="life-advance"))
        self.assertIsNone(mod.observe({}, scope, frame, obs["default_query"], obs["request_attempts"], selected_step="private-submit"))


if __name__ == "__main__":
    unittest.main()
