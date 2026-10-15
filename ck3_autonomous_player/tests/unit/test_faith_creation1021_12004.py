"""One bounded source/registry contract case; no game or local product files."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
    query_vanilla_event_source_provenance_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    _option_projection_checks,
    _scope_projection_checks,
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    compute_source_index_dataset_sha256,
    load_vanilla_event_source_index,
)


KEY = "faith_creation.1021"
PLAYER = 789  # Fixture-owned; no product/save/observed actor identity.


def _scope(kind, character_id=None):
    identity = ({"status": "available", "kind": "character", "character_id": character_id}
                if character_id is not None else {"status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed"})
    return {"status": "available", "type_key": kind, "typed_identity": identity}


def _context():
    kinds = {"old_faith": "faith", "old_rite": "rite", "new_faith": "faith",
             "new_rite": "rite", "founder": "character", "source_rite": "rite",
             "differing_tenet": "tenet"}
    return {
        "schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "window_match_count": 1, "snapshot_revision": 5,
        "date_raw": 10000, "current_event_instance_id": 11, "event_definition_key": KEY,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [{"name": name, "scope": _scope(kind, PLAYER if name == "founder" else None)}
                         for name, kind in kinds.items()],
        "options": [{"rendered_index": i, "native_option_index": i,
                     "shown": True, "enabled": True, "fallback": False, "cancel": False}
                    for i in (0, 1)],
        "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1"},
    }


class FaithCreation1021KnowledgeTests(unittest.TestCase):
    def test_exact_founder_contract_source_projection_and_old_build_isolation(self):
        row = query_vanilla_event_knowledge_v1(KEY, "1.20.0.4")
        self.assertEqual(row["status"], "available")
        self.assertEqual(row["analysis"]["exact_build"]["ck3_executable_sha256"], row["ck3_exe_sha256"])
        contract = materialize_vanilla_timeline_contract(row["contract"], PLAYER)
        context = _context()
        checks = _scope_projection_checks(context, contract, PLAYER)
        self.assertTrue(all(checks.values()), checks)
        checks, selected = _option_projection_checks(context, contract, 4)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(selected["native_option_index"], 0)
        self.assertFalse(all(_option_projection_checks(context, contract, 2)[0].values()))

        observer = copy.deepcopy(context)
        observer["saved_scopes"][4]["scope"] = _scope("character", PLAYER + 1)
        for index, option in enumerate(observer["options"]):
            option["native_option_index"] = index + 2
        self.assertFalse(all(_scope_projection_checks(observer, contract, PLAYER).values()))
        self.assertFalse(all(_option_projection_checks(observer, contract, 4)[0].values()))
        missing = copy.deepcopy(context)
        missing["saved_scopes"].pop()
        self.assertFalse(all(_scope_projection_checks(missing, contract, PLAYER).values()))
        disabled = copy.deepcopy(context)
        disabled["options"][0]["enabled"] = False
        self.assertFalse(all(_option_projection_checks(disabled, contract, 4)[0].values()))

        # Knowledge registration does not widen the generic relational-scope
        # policy allowmap or establish a blanket first-shown recommendation.
        decision = recommend_registered_vanilla_event_option_v1(
            context, played_character_id=PLAYER, snapshot_option_count=4)
        self.assertEqual(decision["status"], "blocked")
        self.assertIsNone(decision["selected_option_number"])
        analysis = row["analysis"]
        self.assertFalse(analysis["automatic_selection"])
        self.assertEqual(set(analysis["option_semantics"]), {"0", "1", "2", "3"})
        profile = analysis["selected_choice_effect_profile"]
        self.assertEqual([effect["authored_base_value"] for effect in profile["selected_option_effects"]], [5, 50])
        self.assertEqual(profile["common_after_effects"], [])
        self.assertIsNone(profile["observable_postcondition"])
        self.assertIsNone(analysis["follow_up_event"])

        source = query_vanilla_event_source_provenance_v1(KEY, build="1.20.0.4")
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 1273)
        self.assertEqual(source["definition"]["file_sha256"], analysis["source_sha256"][source["definition"]["relative_path"]])
        self.assertEqual(source["caller_candidates"][0]["line"], 1265)
        self.assertTrue(source["caller_candidates_are_lexical_only"])
        previous = load_vanilla_event_source_index(build="1.20.0.3")
        current = load_vanilla_event_source_index(build="1.20.0.4")
        self.assertEqual({key: value for key, value in current["events"].items() if key != KEY}, previous["events"])
        self.assertEqual(len(current["events"]), len(previous["events"]) + 1)
        self.assertEqual(current["dataset_sha256"], compute_source_index_dataset_sha256(current))
        self.assertEqual(previous["dataset_sha256"], "698F66B83C6D45FAD4D5292E3AF2E6DB3721C92F736ADB9396E177BF8878D880")
        for build in ("1.19.0.6", "1.20.0.2", "1.20.0.3"):
            self.assertEqual(query_vanilla_event_knowledge_v1(KEY, build)["unavailable_reason"], "event_definition_key_not_registered")
            self.assertEqual(query_vanilla_event_source_provenance_v1(KEY, build=build)["unavailable_reason"], "event_definition_key_not_indexed")

        json.dumps(row, allow_nan=False)
        row["contract"]["character_scopes"]["founder"] = -1
        source["definition"]["line"] = -1
        self.assertEqual(query_vanilla_event_knowledge_v1(KEY, "1.20.0.4")["contract"]["character_scopes"]["founder"], "$player")
        self.assertEqual(query_vanilla_event_source_provenance_v1(KEY, build="1.20.0.4")["definition"]["line"], 1273)


if __name__ == "__main__":
    unittest.main()
