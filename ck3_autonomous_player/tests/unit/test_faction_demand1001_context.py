from __future__ import annotations

import copy
import unittest

from xar_autoplayer.vanilla_events.builds import CURRENT_CK3_EXE_SHA256
from xar_autoplayer.vanilla_events.faction_demand1001_context import build_faction_demand1001_decision_context_v1
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


def _scope(type_index: int, kind: str, field: str, value: int) -> dict[str, object]:
    return {"status": "available", "raw_type_index": type_index, "type_key": kind,
        "subtype": 0, "typed_identity": {"status": "available", "kind": kind, field: value}}


def _title(title_id: int, tier: int = 2, holder: int = 29829) -> dict[str, object]:
    return {"title_id": title_id, "tier_raw": tier,
        "de_jure_parent_title_id": 201 if tier == 2 else 301 if tier == 3 else None,
        "duchy_title_id": 201 if tier <= 3 else None, "kingdom_title_id": 301,
        "holder_character_id": holder, "top_liege_character_id": 29829}


def _frames() -> tuple[dict[str, object], dict[str, object]]:
    # Fixture-owned identities and title sets, never a current Robert observation.
    scopes = {"faction": _scope(25, "faction", "faction_id", 33554465),
        "peasant_county": _scope(5, "landed_title", "title_id", 101),
        "faction_target": _scope(4, "character", "character_id", 29829),
        "target_title": _scope(5, "landed_title", "title_id", 301),
        "peasant_leader": _scope(4, "character", "character_id", 70766),
        "new_title": _scope(5, "landed_title", "title_id", 401),
        "faction_leader": _scope(4, "character", "character_id", 70766)}
    options = [{"rendered_index": index, "native_option_index": native,
        "shown": True, "enabled": True, "fallback": False, "cancel": False,
        "resolved_name": "Accept fixture" if native == 2 else "Refuse fixture",
        "unavailable_reason": "", "effect_indicators": {"status": "available",
            "coverage": "played-character-event-icon-indicators-1.20.0.3-v1",
            "complete_effect_set": False, "rows": []},
        "effect_preview": {"status": "unavailable", "reason": "indicator_subset_has_no_completeness_signal"},
        "resource_deltas": {"status": "unavailable"}, "relationship_deltas": {"status": "unavailable"}}
        for index, native in enumerate((2, 3))]
    event = {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "snapshot_revision": 64, "date_raw": 53236608,
        "current_event_instance_id": 23, "window_match_count": 1,
        "unavailable_reason": None, "event_definition_key": "faction_demand.1001",
        "calculated_event_id": 4061001, "runtime_stats_ordinal": 5943,
        "root_scope": _scope(4, "character", "character_id", 29829),
        "saved_scopes": [{"name": name, "name_identifier": index + 1, "scope": scope}
            for index, (name, scope) in enumerate(scopes.items())], "options": options,
        "readiness": {"event_definition_identity_ready": True, "root_scope_ready": True,
            "saved_scopes_ready": True, "option_presentation_ready": True,
            "effect_indicators_ready": True, "effect_preview_ready": False,
            "semantic_decision_ready": False},
        "provenance": {"root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC408",
            "manager_offset": "+0x28", "backend_id": "ck3-1.20.0.3-native-event-window-v1"}}
    impact = {"status": "available", "unavailable_reason": None,
        "government_allows_state_faith": False, "leader_at_war_with_target": False,
        "ordinary_branch_title_sets_ready": True, "county_loss_complete": True,
        "kingdom_outcome_complete": False, "player_subrealm_county_title_ids": [101, 102, 103],
        "member_counties": [_title(101, holder=32716)],
        "seized_counties": [_title(101, holder=32716), _title(102)],
        "seized_duchies": [_title(201, tier=3)],
        "player_direct_title_loss_ids": [102, 201],
        "player_remaining_direct_county_title_ids": [103],
        "kingdoms": [{"title": _title(301, tier=4),
            "de_jure_county_title_ids": [101, 102, 103], "seized_county_title_ids": [101, 102],
            "strict_majority_from_seized_counties": True}],
        "unresolved_branches": ["kingdom_receiver_capital_and_existing_direct_counties"]}
    fixed = lambda value: {"raw": value, "scale": 100000}
    faction = {"faction_id": 33554465, "faction_type_key": "populist_faction",
        "target_character_id": 29829, "leader_character_id": 70766,
        "leader_is_human": False, "special_character_id": None, "special_title_id": None,
        "faction_at_war": False, "faction_war_id": None, "power": fixed(9000000),
        "power_threshold": fixed(8000000), "discontent": fixed(2500000),
        "discontent_per_month": fixed(500000), "months_until_max_discontent": 10,
        "character_member_ids": [70766], "county_member_title_ids": [101],
        "dangerous_by_stock_rule": True, "danger_reason": "non_peasant_discontent_increasing",
        "surrender_impact": impact}
    alerts = {"schema_version": 1, "status": "available", "snapshot_revision": 65,
        "date_raw": 53236608, "player_character_id": 29829, "targeting_faction_count": 1,
        "targeting_factions": [faction], "county_exposures": [],
        "planner_projection": {"status": "available", "present": True, "dangerous": True,
            "dangerous_faction_ids": [33554465], "watch_faction_ids": [],
            "war_handoff_faction_ids": [], "exposed_county_title_ids": [],
            "exact_ultimatum_timing_ready": False},
        "readiness": {"identity_ready": True, "targeting_count_ready": True,
            "targeting_rows_ready": True, "county_exposure_ready": True,
            "stock_dangerous_predicate_ready": True, "same_frame_ready": True,
            "alert_ready": True, "exact_ultimatum_timing_ready": False},
        "component_unavailable_reasons": {"targeting_rows": None, "county_exposure": None},
        "unavailable_reason": None,
        "provenance": {"game_version": "1.20.0.3", "executable_sha256": CURRENT_CK3_EXE_SHA256,
            "backend_id": "ck3-1.20.0.3-native-player-faction-alerts-v1"}}
    return event, alerts


def _context(event: dict[str, object], alerts: dict[str, object]) -> dict[str, object]:
    return build_faction_demand1001_decision_context_v1(event, alerts,
        played_character_id=29829, expected_event_instance_id=23,
        expected_date_raw=53236608, expected_event_snapshot_revision=64,
        expected_faction_snapshot_revision=65)


class FactionDemand1001ContextTests(unittest.TestCase):
    def test_exact_registry_and_generic_policy_recognize_without_selecting(self):
        knowledge = query_vanilla_event_knowledge_v1("faction_demand.1001", "1.20.0.3")
        self.assertEqual(knowledge["status"], "available")
        self.assertTrue(knowledge["contract"]["selection_deferred"])
        self.assertIsNone(knowledge["contract"]["selected_native_option_index"])
        self.assertTrue(knowledge["analysis"]["option_semantics"]["3"]["war_execution_authorized"])
        self.assertIn("2026-10-03", knowledge["analysis"]["selection_boundary"])
        event, _ = _frames()
        decision = recommend_registered_vanilla_event_option_v1(event,
            played_character_id=29829, snapshot_option_count=4)
        self.assertEqual(decision["readonly_projection"]["status"], "recognized")
        self.assertIsNone(decision["selected_option_number"])
        self.assertEqual(decision["unavailable_reason"], "populist_ultimatum_readonly_review_required")

    def test_exact_faction_binding_and_spillover_comparison(self):
        event, alerts = _frames()
        context = _context(event, alerts)
        self.assertEqual(context["status"], "available")
        self.assertTrue(context["binding_ready"] and context["readonly_review_ready"])
        self.assertEqual(context["acceptance"]["api_option_number"], 3)
        self.assertEqual(context["acceptance"]["rendered_index"], 0)
        self.assertEqual(context["refusal"]["api_option_number"], 4)
        self.assertEqual(context["refusal"]["effect"], "faction_start_war")
        self.assertEqual(context["acceptance"]["realm_county_loss_ids"], [101, 102])
        self.assertEqual(context["acceptance"]["player_direct_county_and_duchy_loss_ids"], [102, 201])
        self.assertEqual(context["acceptance"]["player_remaining_direct_county_title_ids"], [103])
        self.assertFalse(context["complete_acceptance_outcome_ready"])
        self.assertFalse(context["action_execution_ready"])
        self.assertTrue(context["war_execution_authorized"])
        self.assertTrue(context["refusal"]["war_execution_authorized"])
        self.assertFalse(context["refusal"]["execution_ready"])
        self.assertFalse(context["automatic_selection"])
        self.assertIsNone(context["selected_option_number"])
        self.assertEqual(context["binding"]["faction_snapshot_revision"], 65)

    def test_saved_full_generation_is_required_even_with_same_leader(self):
        event, alerts = _frames()
        event["saved_scopes"][0]["scope"]["typed_identity"]["faction_id"] = 16777249
        context = _context(event, alerts)
        self.assertEqual(context["unavailable_reason"], "saved_full_faction_id_not_in_observed_targeting_rows")
        self.assertFalse(context["binding_ready"])

    def test_missing_title_requests_specific_observation_and_preserves_refusal_source(self):
        event, alerts = _frames()
        event["saved_scopes"][3]["scope"]["typed_identity"] = {
            "status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}
        context = _context(event, alerts)
        self.assertEqual(context["status"], "partial")
        self.assertEqual(context["missing_observations"], ["saved_target_title_full_id"])
        self.assertEqual(context["refusal"]["effect"], "faction_start_war")

    def test_native_null_new_title_and_conditional_kingdom_are_reviewable(self):
        event, alerts = _frames()
        event["saved_scopes"][5]["scope"]["typed_identity"] = {
            "status": "unavailable", "reason": "landed_title_scope_is_null"}
        context = _context(event, alerts)
        self.assertTrue(context["readonly_review_ready"])
        self.assertTrue(context["binding"]["new_title_native_null"])
        self.assertTrue(context["acceptance"]["conditional_kingdom_candidates"][0]["strict_majority_from_seized_counties"])
        self.assertFalse(context["complete_acceptance_outcome_ready"])

    def test_state_faith_branch_and_new_date_do_not_use_ordinary_losses(self):
        event, alerts = _frames()
        alerts["targeting_factions"][0]["surrender_impact"]["government_allows_state_faith"] = True
        context = _context(event, alerts)
        self.assertFalse(context["readonly_review_ready"])
        self.assertIsNone(context["acceptance"]["realm_county_loss_ids"])
        self.assertEqual(context["missing_observations"], ["state_faith_transfer_outcome"])
        changed = copy.deepcopy(event)
        changed["date_raw"] += 1
        context = _context(changed, alerts)
        self.assertEqual(context["unavailable_reason"], "input_frame_contract_invalid")


if __name__ == "__main__":
    unittest.main()
