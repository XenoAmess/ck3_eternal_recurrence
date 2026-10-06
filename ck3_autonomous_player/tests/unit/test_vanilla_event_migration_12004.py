"""One source-only .4 registration and production-consumer migration case."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.vanilla_events import query_vanilla_event_knowledge_v1
from xar_autoplayer.vanilla_events.builds import (
    CURRENT_CK3_BUILD,
    CURRENT_CK3_EXE_SHA256,
    MIGRATED_CK3_BUILDS,
    SUPPORTED_CK3_EXE_SHA256,
    event_context_build,
)
from xar_autoplayer.vanilla_events.faction_demand1001_context import (
    build_faction_demand1001_decision_context_v1,
)
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.source_index import (
    compute_source_index_dataset_sha256,
    load_vanilla_event_source_index,
)


BUILD = "1.20.0.4"
EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
PREVIOUS_EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
EXACT_BUILD = {
    "game_version": BUILD,
    "ck3_executable_sha256": EXE_SHA256,
    "steam_build_id": 25734779,
}
DATA_DEPOT = {
    "depot_id": "1158311", "manifest": "5078208590259867811",
    "size_bytes": 19091661807, "previous_manifest": "5078208590259867811",
    "same_manifest": True,
}
PREVIOUS_DATASET_SHA256 = "698F66B83C6D45FAD4D5292E3AF2E6DB3721C92F736ADB9396E177BF8878D880"
PLAYER = 29829


def _scope(raw_type: int, kind: str, field: str | None = None,
           value: int | None = None) -> dict[str, object]:
    identity = ({"status": "available", "kind": kind, field: value}
                if field is not None else {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                })
    return {"status": "available", "raw_type_index": raw_type,
            "type_key": kind, "subtype": 0, "typed_identity": identity}


def _option(rendered: int, native: int) -> dict[str, object]:
    return {"rendered_index": rendered, "native_option_index": native,
            "shown": True, "enabled": True, "fallback": False, "cancel": False,
            "resolved_name": "Migration fixture", "unavailable_reason": "",
            "effect_indicators": {"status": "available",
                "coverage": f"played-character-event-icon-indicators-{BUILD}-v1",
                "complete_effect_set": False, "rows": []},
            "effect_preview": {"status": "unavailable",
                "reason": "indicator_subset_has_no_completeness_signal"},
            "resource_deltas": {"status": "unavailable"},
            "relationship_deltas": {"status": "unavailable"}}


def _event(key: str, scopes: list[dict[str, object]],
           native_options: tuple[int, ...]) -> dict[str, object]:
    return {"schema": "current-event-window-context-v1", "schema_version": 1,
            "status": "available", "snapshot_revision": 64,
            "date_raw": 53236608, "current_event_instance_id": 23,
            "window_match_count": 1, "unavailable_reason": None,
            "event_definition_key": key, "calculated_event_id": 4061001,
            "runtime_stats_ordinal": 5943,
            "root_scope": _scope(4, "character", "character_id", PLAYER),
            "saved_scopes": scopes,
            "options": [_option(rendered, native)
                        for rendered, native in enumerate(native_options)],
            "readiness": {"event_definition_identity_ready": True,
                "root_scope_ready": True, "saved_scopes_ready": True,
                "option_presentation_ready": True, "effect_indicators_ready": True,
                "effect_preview_ready": False, "semantic_decision_ready": False},
            "provenance": {"root": "module+0x5C6A520->+0x10",
                "idler_vtable_rva": "0x44BC408", "manager_offset": "+0x28",
                "backend_id": f"ck3-{BUILD}-native-event-window-v1"}}


def _selection_context(key: str) -> dict[str, object]:
    # Scope roles and visible options come from the existing production-shaped
    # .3 completion fixture and epidemic physician variant, not .4 live input.
    if key == "feast.7101":
        rows = (("activity", 2, 6, "activity", None),
                ("host", 62, 4, "character", PLAYER),
                ("province", 37, 8, "province", None),
                ("activity_location", 14682, 8, "province", None),
                ("root_scope", 9563, 4, "character", PLAYER))
        options = (0,)
    else:
        rows = (("epidemic", 10, 50, "epidemic", None),
                ("province", 11, 8, "province", None),
                ("infected_county", 12, 5, "landed_title", None))
        options = (0, 1)
    scopes = [{"name": name, "name_identifier": identifier,
               "scope": _scope(raw_type, kind,
                   "character_id" if character_id is not None else None, character_id)}
              for name, identifier, raw_type, kind, character_id in rows]
    context = _event(key, scopes, options)
    if key == "feast.7101":
        context.update(calculated_event_id=5947101, runtime_stats_ordinal=10168,
                       snapshot_revision=21, date_raw=53222952,
                       current_event_instance_id=20)
    return context


def _title(title_id: int, tier: int = 2, holder: int = PLAYER) -> dict[str, object]:
    return {"title_id": title_id, "tier_raw": tier,
            "de_jure_parent_title_id": 201 if tier == 2 else 301 if tier == 3 else None,
            "duchy_title_id": 201 if tier <= 3 else None, "kingdom_title_id": 301,
            "holder_character_id": holder, "top_liege_character_id": PLAYER}


def _faction_frames() -> tuple[dict[str, object], dict[str, object]]:
    # Reuse the explicit fixture-owned identities/title sets from
    # test_faction_demand1001_context.py; no current Robert observation is claimed.
    roles = {"faction": _scope(25, "faction", "faction_id", 33554465),
             "peasant_county": _scope(5, "landed_title", "title_id", 101),
             "faction_target": _scope(4, "character", "character_id", PLAYER),
             "target_title": _scope(5, "landed_title", "title_id", 301),
             "peasant_leader": _scope(4, "character", "character_id", 70766),
             "new_title": _scope(5, "landed_title", "title_id", 401),
             "faction_leader": _scope(4, "character", "character_id", 70766)}
    event = _event("faction_demand.1001", [
        {"name": name, "name_identifier": index + 1, "scope": scope}
        for index, (name, scope) in enumerate(roles.items())], (2, 3))
    impact = {"status": "available", "unavailable_reason": None,
              "government_allows_state_faith": False, "leader_at_war_with_target": False,
              "ordinary_branch_title_sets_ready": True, "county_loss_complete": True,
              "kingdom_outcome_complete": False,
              "player_subrealm_county_title_ids": [101, 102, 103],
              "member_counties": [_title(101, holder=32716)],
              "seized_counties": [_title(101, holder=32716), _title(102)],
              "seized_duchies": [_title(201, tier=3)],
              "player_direct_title_loss_ids": [102, 201],
              "player_remaining_direct_county_title_ids": [103],
              "kingdoms": [{"title": _title(301, tier=4),
                  "de_jure_county_title_ids": [101, 102, 103],
                  "seized_county_title_ids": [101, 102],
                  "strict_majority_from_seized_counties": True}],
              "unresolved_branches": ["kingdom_receiver_capital_and_existing_direct_counties"]}
    fixed = lambda value: {"raw": value, "scale": 100000}
    faction = {"faction_id": 33554465, "faction_type_key": "populist_faction",
               "target_character_id": PLAYER, "leader_character_id": 70766,
               "leader_is_human": False, "special_character_id": None,
               "special_title_id": None, "faction_at_war": False, "faction_war_id": None,
               "power": fixed(9000000), "power_threshold": fixed(8000000),
               "discontent": fixed(2500000), "discontent_per_month": fixed(500000),
               "months_until_max_discontent": 10, "character_member_ids": [70766],
               "county_member_title_ids": [101], "dangerous_by_stock_rule": True,
               "danger_reason": "non_peasant_discontent_increasing", "surrender_impact": impact}
    alerts = {"schema_version": 1, "status": "available", "snapshot_revision": 65,
              "date_raw": 53236608, "player_character_id": PLAYER,
              "targeting_faction_count": 1, "targeting_factions": [faction],
              "county_exposures": [],
              "planner_projection": {"status": "available", "present": True,
                  "dangerous": True, "dangerous_faction_ids": [33554465],
                  "watch_faction_ids": [], "war_handoff_faction_ids": [],
                  "exposed_county_title_ids": [], "exact_ultimatum_timing_ready": False},
              "readiness": {"identity_ready": True, "targeting_count_ready": True,
                  "targeting_rows_ready": True, "county_exposure_ready": True,
                  "stock_dangerous_predicate_ready": True, "same_frame_ready": True,
                  "alert_ready": True, "exact_ultimatum_timing_ready": False},
              "component_unavailable_reasons": {"targeting_rows": None, "county_exposure": None},
              "unavailable_reason": None,
              "provenance": {"game_version": BUILD, "executable_sha256": EXE_SHA256,
                  "backend_id": f"ck3-{BUILD}-native-player-faction-alerts-v1"}}
    return event, alerts


class VanillaEventMigration12004Tests(unittest.TestCase):
    def test_source_migration_registers_new_tuple_and_drives_current_consumers(self):
        self.assertEqual((CURRENT_CK3_BUILD, CURRENT_CK3_EXE_SHA256), (BUILD, EXE_SHA256))
        self.assertEqual(SUPPORTED_CK3_EXE_SHA256["1.20.0.3"], PREVIOUS_EXE_SHA256)
        self.assertIn(BUILD, MIGRATED_CK3_BUILDS)
        self.assertEqual(event_context_build({"provenance": {
            "backend_id": f"ck3-{BUILD}-native-event-window-v1"}}), BUILD)

        keys = ("feast.7101", "epidemic_events.1100", "faction_demand.1001")
        historical = {key: query_vanilla_event_knowledge_v1(key, "1.20.0.3")
                      for key in keys}
        frozen_history = copy.deepcopy(historical)
        source3 = load_vanilla_event_source_index(build="1.20.0.3")
        source4 = load_vanilla_event_source_index(build=BUILD)
        self.assertEqual((source4["ck3_build"], source4["ck3_exe_sha256"]), (BUILD, EXE_SHA256))
        self.assertEqual(len(source4["events"]), 193)
        self.assertEqual(source4["events"], source3["events"])
        self.assertEqual(source4["audit"], source3["audit"])
        self.assertEqual(source3["dataset_sha256"], PREVIOUS_DATASET_SHA256)
        reuse = source4["source_reuse_1_20_0_4"]
        self.assertEqual(reuse["previous_build"], "1.20.0.3")
        self.assertEqual(reuse["previous_dataset_sha256"], source3["dataset_sha256"])
        self.assertEqual(reuse["data_depot"], DATA_DEPOT)
        self.assertFalse(reuse["fresh_source_scan"])
        self.assertFalse(reuse["runtime_call_chain_revalidated"])
        self.assertFalse(reuse["new_live_evidence"])
        self.assertNotEqual(source4["dataset_sha256"], source3["dataset_sha256"])
        self.assertEqual(source4["dataset_sha256"], compute_source_index_dataset_sha256(source4))

        for key, snapshot_count in (("feast.7101", 1), ("epidemic_events.1100", 3)):
            with self.subTest(event=key):
                current = query_vanilla_event_knowledge_v1(key, BUILD)
                self.assertEqual(current["status"], "available")
                self.assertEqual(current["analysis"]["exact_build"], EXACT_BUILD)
                self.assertEqual(current["contract"], historical[key]["contract"])
                self.assertEqual(current["analysis"]["source_sha256"], historical[key]["analysis"]["source_sha256"])
                migration = current["analysis"]["migration_1_20_0_4"]
                self.assertEqual(migration["previous_build"], "1.20.0.3")
                self.assertEqual(migration["previous_exact_build"], historical[key]["analysis"]["exact_build"])
                self.assertEqual(migration["previous_source_sha256"], historical[key]["analysis"]["source_sha256"])
                self.assertEqual(migration["readiness"], "static-ready")
                self.assertEqual(migration["data_depot"], DATA_DEPOT)
                self.assertFalse(migration["new_live_evidence"])
                self.assertFalse(migration["runtime_call_chain_revalidated"])
                self.assertEqual(current["observations"], {
                    "legacy_build": "1.20.0.3", "new_live_evidence": False,
                    "legacy_observations": historical[key]["observations"],
                })
                decision = recommend_registered_vanilla_event_option_v1(
                    _selection_context(key), played_character_id=PLAYER,
                    snapshot_option_count=snapshot_count)
                self.assertEqual((decision["status"], decision["ck3_build"]), ("recommended", BUILD))
                self.assertEqual((decision["selected_option_number"], decision["selected_native_option_index"]), (1, 0))
                self.assertEqual(decision["failed_checks"], [])

        event, alerts = _faction_frames()
        decision = recommend_registered_vanilla_event_option_v1(
            event, played_character_id=PLAYER, snapshot_option_count=4)
        self.assertEqual((decision["status"], decision["ck3_build"]), ("blocked", BUILD))
        self.assertEqual(decision["unavailable_reason"], "populist_ultimatum_readonly_review_required")
        self.assertEqual(decision["readonly_projection"]["status"], "recognized")
        self.assertIsNone(decision["selected_option_number"])
        comparison = build_faction_demand1001_decision_context_v1(
            event, alerts, played_character_id=PLAYER, expected_event_instance_id=23,
            expected_date_raw=53236608, expected_event_snapshot_revision=64,
            expected_faction_snapshot_revision=65)
        # The strict native event ingress has no new .4 validation in this work
        # package. Registry recognition must not promote this fixture to a frame.
        self.assertEqual((comparison["status"], comparison["ck3_build"], comparison["ck3_exe_sha256"]),
                         ("blocked", BUILD, EXE_SHA256))
        self.assertEqual(comparison["unavailable_reason"], "input_frame_contract_invalid")
        self.assertFalse(comparison["binding_ready"])
        self.assertFalse(comparison["readonly_review_ready"])
        self.assertTrue(comparison["war_execution_authorized"])
        self.assertFalse(comparison["complete_acceptance_outcome_ready"])
        self.assertFalse(comparison["action_execution_ready"])
        self.assertFalse(comparison["automatic_selection"])
        self.assertIsNone(comparison["selected_option_number"])

        war = query_vanilla_event_knowledge_v1("great_holy_war.0011", BUILD)
        self.assertNotEqual(war["unavailable_reason"], "event_domain_outside_nonwar_work_package")
        self.assertEqual(war["unavailable_reason"], "event_source_migration_pending")
        self.assertEqual(query_vanilla_event_knowledge_v1("fervor.1002", BUILD)["unavailable_reason"],
                         "event_definition_not_present_in_current_build")
        self.assertEqual(historical, frozen_history)
        for key in keys:
            self.assertEqual(query_vanilla_event_knowledge_v1(key, "1.20.0.3"), frozen_history[key])
        self.assertEqual(load_vanilla_event_source_index(build="1.20.0.3"), source3)


if __name__ == "__main__":
    unittest.main()
