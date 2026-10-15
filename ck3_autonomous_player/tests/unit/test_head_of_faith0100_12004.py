"""One exact-build public knowledge case; no local product or live inputs."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.vanilla_events import materialize_vanilla_timeline_contract, query_vanilla_event_knowledge_v1, query_vanilla_event_source_provenance_v1
from xar_autoplayer.vanilla_events.policy import _scope_projection_checks, _option_projection_checks, recommend_registered_vanilla_event_option_v1

KEY = "head_of_faith.0100"


def scope(kind, identity=None):
    return {"status": "available", "type_key": kind, "typed_identity":
            ({"status": "available", "kind": "character", "character_id": identity} if identity else
             {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"})}


class HeadOfFaithKnowledgeTests(unittest.TestCase):
    def test_public_exact_record_guards_sources_and_old_builds(self):
        row = query_vanilla_event_knowledge_v1(KEY, "1.20.0.4")
        self.assertEqual(row["status"], "available")
        contract = materialize_vanilla_timeline_contract(row["contract"], 701)
        context = {"schema": "current-event-window-context-v1", "schema_version": 1,
                   "status": "available", "window_match_count": 1, "date_raw": 10000,
                   "current_event_instance_id": 11, "event_definition_key": KEY,
                   "root_scope": scope("character", 701),
                   "saved_scopes": [{"name": "old_faith", "scope": scope("faith")},
                                    {"name": "old_rite", "scope": scope("rite")},
                                    {"name": "hof", "scope": scope("character", 702)}],
                   "options": [{"rendered_index": i, "native_option_index": i,
                                "shown": True, "enabled": True, "fallback": False, "cancel": False} for i in (0, 1)],
                   "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1"}}
        self.assertTrue(all(_scope_projection_checks(context, contract, 701).values()))
        checks, selected = _option_projection_checks(context, contract, 2)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(selected["native_option_index"], 0)
        self_hof = copy.deepcopy(context)
        self_hof["saved_scopes"][2]["scope"] = scope("character", 701)
        self.assertFalse(all(_scope_projection_checks(self_hof, contract, 701).values()))
        missing = copy.deepcopy(context)
        missing["saved_scopes"].pop()
        self.assertFalse(all(_scope_projection_checks(missing, contract, 701).values()))
        disabled = copy.deepcopy(context)
        disabled["options"][0]["enabled"] = False
        self.assertFalse(all(_option_projection_checks(disabled, contract, 2)[0].values()))
        swapped = copy.deepcopy(context)
        swapped["options"].reverse()
        self.assertFalse(all(_option_projection_checks(swapped, contract, 2)[0].values()))
        analysis = row["analysis"]
        effect = analysis["selected_choice_effect_profile"]["selected_option_effects"][0]
        self.assertEqual((effect["observer_scope"], effect["target_scope"], effect["authored_opinion"]), ("hof", "root", 25))
        self.assertEqual(analysis["selected_choice_effect_profile"]["common_after_effects"], [])
        self.assertIsNone(analysis["follow_up_event"])
        self.assertFalse(analysis["automatic_selection"])
        self.assertIn("flag", analysis["option_semantics"]["1"])
        decision = recommend_registered_vanilla_event_option_v1(context, played_character_id=701, snapshot_option_count=2)
        self.assertEqual(decision["status"], "blocked")
        self.assertEqual(decision["unavailable_reason"], "registered_contract_requires_extended_consumer")
        self.assertIsNone(decision["selected_option_number"])
        source = query_vanilla_event_source_provenance_v1(KEY, build="1.20.0.4")
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 896)
        self.assertEqual(source["definition"]["file_sha256"], analysis["source_sha256"][source["definition"]["relative_path"]])
        self.assertEqual(source["caller_candidates"][0]["line"], 593)
        self.assertTrue(source["caller_candidates_are_lexical_only"])
        for build in ("1.19.0.6", "1.20.0.2", "1.20.0.3"):
            self.assertEqual(query_vanilla_event_knowledge_v1(KEY, build)["unavailable_reason"], "event_definition_key_not_registered")
            self.assertEqual(query_vanilla_event_source_provenance_v1(KEY, build=build)["unavailable_reason"], "event_definition_key_not_indexed")
        json.dumps(row, allow_nan=False)
        row["contract"]["unique_character_scope_excludes"]["hof"] = [-1]
        self.assertEqual(query_vanilla_event_knowledge_v1(KEY, "1.20.0.4")["contract"]["unique_character_scope_excludes"]["hof"], ["$player"])


if __name__ == "__main__":
    unittest.main()
