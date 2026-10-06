"""One source-shaped production-query compound; no game or native callback."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import normalize_battle_terminal_transition_v1
from xar_autoplayer.bridge.battle_person_rule43_diac_contract import (
    emit_following_diac_2920d60_requests_from_current_source_inputs_12003,
)
from xar_autoplayer.simulation.battle_person_rule43_diac_12003 import first_rule43_unknown_node_12003

ACTOR, DATE = 29829, 53288232
OBSERVATIONS = {}


def node(path="rule43", **changes):
    raw = {"path": path, "identity": "same-node", "slot58_rva": 0x855AB0,
        "slot60_rva": 0x9CFEC0, "slotc8_rva": 0x372F780,
        "children_count_raw": 0, "children_array_present": False,
        "reference_arguments_count_raw": None, "reference_compare_raw": None,
        "nested_present": None, "children": [], "result": True, "reason": None}
    raw.update(changes)
    return raw


def rule(**changes):
    raw = {"input_character_full_id": ACTOR, "source_constructed_root_kind": 4,
        "expected_validator_rva": 0x22565B0, "mode_raw": 0,
        "provider_identity": "provider", "rule_identity": "rule",
        "registry_count_raw": 5, "descriptor_selection": "registry_kind4",
        "loaded_validator_rva": 0x22565B0, "root_lookup_selection": "registry_full_generation",
        "root_object_identity": "root-character", "root_tag_raw": 0x43686172,
        "root_full_id_raw": ACTOR, "root_valid": True, "nodes": [node()],
        "result": True, "reason": None}
    raw.update(changes)
    return raw


def selection(**changes):
    raw = {"source_character_identity": "current-character", "requested_diac_id_raw": 1,
        "lookup_selection": "registry_full_generation", "diac_identity": "diac",
        "diac_tag_raw": 0x44696163, "diac_full_id_raw": 1, "diac_owner_full_id_raw": ACTOR,
        "early_character_lookup_selection": "registry_full_generation",
        "rule_character_full_id_raw": ACTOR, "diac_valid": True, "owner_matches": None,
        "rule": rule(), "reason": None}
    raw.update(changes)
    return raw


def numeric(empty=False, scope=ACTOR):
    declarations = []
    if not empty:
        for index in range(2):
            declarations.append({"status": "available", "ready": True, "reason": None,
                "native_index": index, "declaration_identity": "same-declaration",
                "scale_gate_280_raw": 0, "metadata_provider_loaded": True,
                "properties": {"keys_count": 3, "values_count": 3,
                    "keys_u16": [5, 4, 65535], "values_q64": [-199999, 0, 123456]},
                "metadata_rows": [
                    {"native_index": 0, "key_u16": 5, "selection": "provider_50_c8",
                     "metadata_identity": "key5", "byte_ba_raw": 0, "byte_b8_raw": 0},
                    {"native_index": 1, "key_u16": 4, "selection": "provider_50_c8",
                     "metadata_identity": "key4", "byte_ba_raw": 1, "byte_b8_raw": None},
                    {"native_index": 2, "key_u16": 65535, "selection": "static_5451f40",
                     "metadata_identity": "sentinel", "byte_ba_raw": 0, "byte_b8_raw": 1}]})
    return {"status": "available", "ready": True, "reason": None,
        "scope_character_full_id": scope, "scope_id_address_identity": "source-DWORD-address",
        "definition_block_identity": "primary620", "declaration_count_raw": len(declarations),
        "declaration_array_present": bool(declarations), "declarations": declarations}


def leaf():
    return {"status": "available", "ready": True, "reason": None, "character_id": ACTOR,
        "current_character_full_id_raw": None, "primary": selection(), "secondary": None,
        "selected_family": "primary_620", "numeric_inputs": numeric()}


def frame(leaf_value):
    person = {"scope": "current_character",
        "effective_prowess": {"status": "available", "points": 13, "unavailable_reason": None},
        "injury_traits": {"status": "available", "flags": {key: False for key in (
            "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged", "one_eyed",
            "disfigured", "incapable")}, "wounded_rank": 0,
            "wounded_rank_unavailable_reason": None, "unavailable_reason": None},
        "current_context_source_inputs": {"status": "partial", "ready": False,
            "character_id": ACTOR, "branch_291e210": None,
            "following_diac_2920d60": leaf_value, "reason": "unrelated_prior_stage_unavailable"}}
    return {"schema_version": 1, "contract_stage": "production_exact_battle_terminal_transition",
        "status": "available", "unavailable_reason": None, "battle_terminal_transition_ready": False,
        "snapshot_revision": 9, "observed_date_raw": DATE, "prior_combat_id": -1, "subject_public_cunit_id": -1,
        "terminal_journal": {"requested_after_sequence": None, "oldest_available_sequence": 0,
            "latest_sequence": 0, "event_sequence": None, "event_status": "not_observed"},
        "prior": None, "removal": None, "subject": None, "successor": None,
        "character_observations": [{"character_id": ACTOR, "status": "none",
            "actual_jailer_character_id": -1, "alive": True, "current_person_state": person}]}


def normalize(leaf_value):
    query = normalize_battle_terminal_transition_v1(frame(leaf_value), expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None, expected_after_terminal_sequence=None,
        expected_observed_date_raw=DATE, expected_snapshot_revision=9, expected_character_ids=[ACTOR])
    current = query["character_observations"][0]["current_person_state"]
    assert current["effective_prowess"]["points"] == 13
    assert query["battle_terminal_transition_ready"] is False
    return current["current_context_source_inputs"]


class Rule43IntegratedCurrentPerson12003Tests(unittest.TestCase):
    def test_current_query_closed_branches_and_first_unknown(self):
        original = leaf()
        section = normalize(original)
        requests = emit_following_diac_2920d60_requests_from_current_source_inputs_12003(section)
        self.assertEqual(len(requests), 2)
        self.assertEqual([r.first_row_index for r in requests], [0, 1])
        self.assertEqual(requests[0].definition_identity, requests[1].definition_identity)
        self.assertEqual(requests[0].base_property_block["keys_u16"], [5, 4, 65535])
        self.assertEqual(requests[0].base_property_block["values_q64"], [-100000, 0, 123456])
        self.assertEqual(original["numeric_inputs"]["declarations"][0]["properties"]["values_q64"][0], -199999)

        empty = leaf()
        empty["numeric_inputs"] = numeric(empty=True)
        self.assertEqual(emit_following_diac_2920d60_requests_from_current_source_inputs_12003(normalize(empty)), ())
        self.assertIsNone(normalize(empty)["following_diac_2920d60"]["secondary"])

        # Reference zero arguments keeps original root and exact rawBYTE80.
        reference = node(slotc8_rva=0x3730940, slot60_rva=0x9CFEE0,
            children_count_raw=None, children_array_present=None,
            reference_arguments_count_raw=0, reference_compare_raw=0, nested_present=False)
        known_reference = leaf()
        known_reference["primary"]["rule"]["nodes"] = [reference]
        self.assertTrue(normalize(known_reference)["following_diac_2920d60"]["primary"]["rule"]["result"])

        false_reference = leaf()
        false_reference["primary"]["rule"] = rule(result=False,
            nodes=[node(**{**reference, "reference_compare_raw": 2, "result": False})])
        false_reference.update(current_character_full_id_raw=ACTOR, selected_family="none", numeric_inputs=None)
        false_reference["secondary"] = selection(early_character_lookup_selection=None,
            rule_character_full_id_raw=None, diac_tag_raw=0, diac_full_id_raw=None,
            diac_owner_full_id_raw=None, diac_valid=False, rule=None)
        self.assertEqual(emit_following_diac_2920d60_requests_from_current_source_inputs_12003(normalize(false_reference)), ())

        # Repeated child identity remains two physical occurrences in order.
        duplicate = leaf()
        duplicate["primary"]["rule"]["nodes"] = [node(children_count_raw=2,
            children_array_present=True, children=[node("rule43/child0"), node("rule43/child1")])]
        copied_children = normalize(duplicate)["following_diac_2920d60"]["primary"]["rule"]["nodes"][0]["children"]
        self.assertEqual([child["identity"] for child in copied_children], ["same-node", "same-node"])

        unknown = leaf()
        gap = node("rule43/child0/reference", slotc8_rva=0x1234567,
            children_count_raw=None, children_array_present=None, result=None, reason="evaluator_slotc8_source")
        ref = node("rule43/child0", slotc8_rva=0x3730940, slot60_rva=0x9CFEE0,
            children_count_raw=None, children_array_present=None,
            reference_arguments_count_raw=0, nested_present=True, reference_compare_raw=None,
            children=[gap], result=None, reason="evaluator_slotc8_source")
        unknown["primary"]["rule"] = rule(nodes=[node(children_count_raw=2, children_array_present=True,
            children=[ref], result=None, reason="evaluator_slotc8_source")], result=None, reason="evaluator_slotc8_source")
        unknown.update(status="partial", ready=False, selected_family=None, numeric_inputs=None, reason="evaluator_slotc8_source")
        normalized_unknown = normalize(unknown)
        seam = first_rule43_unknown_node_12003(normalized_unknown["following_diac_2920d60"]["primary"]["rule"])
        self.assertEqual(seam["path"], "rule43/child0/reference")
        self.assertEqual(seam["slotc8_rva"], 0x1234567)
        self.assertIsNone(normalized_unknown["following_diac_2920d60"]["secondary"])
        with self.assertRaisesRegex(ValueError, "evaluator_slotc8_source"):
            emit_following_diac_2920d60_requests_from_current_source_inputs_12003(normalized_unknown)

        root_false = deepcopy(false_reference)
        root_false["primary"]["rule"] = rule(root_tag_raw=0, root_full_id_raw=None,
            root_valid=False, result=False, nodes=[])
        self.assertFalse(normalize(root_false)["following_diac_2920d60"]["primary"]["rule"]["result"])
        selected_distinct = leaf()
        selected_distinct["primary"].update(diac_owner_full_id_raw=-1,
            early_character_lookup_selection="native_fallback")
        selected_distinct["numeric_inputs"] = numeric(scope=-1)
        distinct = normalize(selected_distinct)["following_diac_2920d60"]
        self.assertEqual(distinct["primary"]["rule"]["input_character_full_id"], ACTOR)
        self.assertEqual(distinct["numeric_inputs"]["scope_character_full_id"], -1)

        # The ordinary loaded evaluator's known empty mode1 header is separate
        # from its undemanded mode0 header; mode2 is still an exact source gap.
        mode1 = leaf()
        mode1["primary"]["rule"]["mode_raw"] = 1
        self.assertTrue(normalize(mode1)["following_diac_2920d60"]["ready"])
        mode2 = leaf()
        mode2["primary"]["rule"] = rule(mode_raw=2, nodes=[node(children_count_raw=None,
            children_array_present=None, result=None, reason="mode2_372f880_source")],
            result=None, reason="mode2_372f880_source")
        mode2.update(status="partial", ready=False, reason="mode2_372f880_source",
            selected_family=None, numeric_inputs=None)
        self.assertFalse(normalize(mode2)["following_diac_2920d60"]["ready"])
        wrong_actor = leaf()
        wrong_actor["character_id"] += 1
        with self.assertRaisesRegex(ValueError, "character disagrees"):
            normalize(wrong_actor)

        OBSERVATIONS.update(production_path="terminal_transition_v1.character_observations.current_person_state.current_context_source_inputs",
            duplicate_requests=2, literal_values=[-100000, 0, 123456],
            known_empty_primary_suppresses_secondary=True, raw_reference_compare_2_result=False,
            unknown=seam, distinct_rule_scope=[ACTOR, -1], source_read_stage="frozen_current_inputs",
            full_rule43_actual_retained_path_ready=False, full_person_ready=False, Entry_ready=False,
            native_callbacks=0, game_days=0)
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
