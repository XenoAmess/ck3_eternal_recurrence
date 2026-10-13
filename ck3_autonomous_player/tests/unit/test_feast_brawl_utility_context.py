"""Focused current-opinion choice deltas; existing M2 qualifications stay closed."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.vanilla_events.feast_brawl_utility_context import (
    compare_feast_brawl_choices_v1,
)
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


def _character(character_id):
    return {"status": "available", "type_key": "character",
        "typed_identity": {"status": "available", "kind": "character",
                           "character_id": character_id}}


def _inputs(values, *, fighter_ids=(38293, 31073)):
    knowledge = query_vanilla_event_knowledge_v1("feast_default.6003", "1.20.0.4")
    event = {"event_definition_key": "feast_default.6003",
        "current_event_instance_id": 17, "snapshot_revision": 24,
        "date_raw": 53222640, "root_scope": _character(29829),
        "saved_scopes": [{"name": f"fighter_{index}", "scope": _character(identity)}
                         for index, identity in enumerate(fighter_ids, start=1)],
        "options": [{"native_option_index": index, "rendered_index": index,
                     "shown": True, "enabled": True} for index in (0, 1)]}
    reads = [{"schema": "activity-feast-guest-opinion-private-read-v1",
        "snapshot_revision": 26 + index, "date_raw": 53222640,
        "actor_character_id": 29829, "guest_character_id": identity,
        "status": "observed", "guest_opinion_of_actor": opinion,
        "read_only": True, "raw_pointer_fields_persisted": False,
        "exact_ck3_build": knowledge["ck3_build"],
        "exe_sha256": knowledge["ck3_exe_sha256"],
        "queried_native_revision": 26 + index,
        "queried_snapshot_id": f"native:{26 + index}",
        "post_snapshot_id": f"native:{26 + index}"}
        for index, (identity, opinion) in enumerate(zip(fighter_ids, values))]
    return event, knowledge, reads


class FeastBrawlCurrentOpinionTests(unittest.TestCase):
    def test_current_balance_selects_either_side_and_matching_source_effects(self):
        for values, selected, fighter_ids in (
            ((100, 12), 1, (38293, 31073)),
            ((12, 100), 0, (77701, 77702)),
        ):
            with self.subTest(values=values):
                event, knowledge, reads = _inputs(values, fighter_ids=fighter_ids)
                original = deepcopy((event, knowledge, reads))
                result = compare_feast_brawl_choices_v1(
                    event, knowledge, opinion_observations=reads)
                self.assertEqual(result["selected_native_option_index"], selected)
                self.assertEqual(result["selected_option_number"], selected + 1)
                self.assertEqual(result["selected_rendered_index"], selected)
                effect = result["choice_effect_profile"]
                self.assertEqual(effect["selected_native_option_index"], selected)
                self.assertEqual(effect["selected_option_effects"][0]["character_scope"],
                                 f"fighter_{selected + 1}")
                self.assertEqual(result["campaign_utility_profile"]["selected_native_option_index"],
                                 selected)
                self.assertEqual(result["campaign_utility_profile"]["alternatives"][0]
                                 ["native_option_index"], 1 - selected)
                context = result["decision_context"]
                self.assertEqual(context["comparison_status"], "current_inputs_compared")
                self.assertTrue(context["current_opinion_inputs_used"])
                self.assertEqual(context["opinion_query_native_revisions"],
                                 {str(fighter_ids[0]): 26, str(fighter_ids[1]): 27})
                self.assertEqual(context["fighters"]["fighter_1"]["character_id"], fighter_ids[0])
                self.assertIsNone(context["predicted_relationship_outcomes"])
                self.assertEqual((event, knowledge, reads), original)

    def test_equal_opinions_keep_existing_bounded_route(self):
        event, knowledge, reads = _inputs((40, 40))
        result = compare_feast_brawl_choices_v1(event, knowledge, opinion_observations=reads)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["decision_context"]["selected_reason"],
                         "equal_current_opinions_retain_source_reviewed_bounded_route")
        self.assertTrue(result["decision_context"]["current_opinion_inputs_used"])

    def test_missing_or_unavailable_pair_retains_explicit_bounded_fallback(self):
        event, knowledge, reads = _inputs((12, 100))
        reads[1].update(status="opinion_unavailable", guest_opinion_of_actor=None)
        for observations in (None, reads):
            with self.subTest(observations_present=observations is not None):
                result = compare_feast_brawl_choices_v1(
                    event, knowledge, opinion_observations=observations)
                self.assertEqual(result["selected_native_option_index"], 1)
                context = result["decision_context"]
                self.assertEqual(context["comparison_status"], "bounded_fallback")
                self.assertFalse(context["current_opinion_inputs_used"])
                self.assertIsNotNone(context["fallback_reason"])
                self.assertIsNone(context["fighters"]["fighter_1"]["opinion_of_player"])
                self.assertIsNone(context["fighters"]["fighter_2"]["opinion_of_player"])

    def test_opinion_read_requires_its_own_revision_binding(self):
        event, knowledge, reads = _inputs((12, 100))
        reads[0]["snapshot_revision"] = 23
        result = compare_feast_brawl_choices_v1(event, knowledge, opinion_observations=reads)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["decision_context"]["fallback_reason"],
                         "current_guest_opinion_pair_does_not_match_event")
        self.assertFalse(result["decision_context"]["current_opinion_inputs_used"])


if __name__ == "__main__":
    unittest.main()
