#!/usr/bin/env python3
"""Purpose-split contracts for health manager-recovery interrupts."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production
from test_zg361_phase2_manager_recovery_interrupts import (
    _context,
    _manager_contract,
    _scope,
)


class ManagerRecoveryHealthInterruptTests(unittest.TestCase):
    def test_minor_epidemic_request_uses_exact_relief_branch(self) -> None:
        event_key = "epidemic_events.5001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=210,
            date_raw=53225904,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("epidemic_county", "landed_title"),
                _scope("province_owner", "character", 67647),
                _scope("courtier", "character", 37804),
            ],
            native_option_indices=(0, 1),
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53225904,
                    "active_event": {"option_count": 2},
                },
                event={"event_instance_id": 210},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_county_type = copy.deepcopy(context)
        wrong_county_type["saved_scopes"][2]["scope"]["type_key"] = "province"
        self.assertFalse(
            checks_for(wrong_county_type)["scope:epidemic_county:type"]
        )

        player_messenger = copy.deepcopy(context)
        player_messenger["saved_scopes"][4] = _scope(
            "courtier", "character", 32904
        )
        self.assertFalse(checks_for(player_messenger)[
            "scope:courtier:unique_third_party"
        ])

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 1
        self.assertFalse(
            checks_for(wrong_projection)["authored_options_exact"]
        )

    def test_post_epidemic_recovery_uses_exact_no_spend_branch(
        self,
    ) -> None:
        event_key = "epidemic_events.0110"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=206,
            date_raw=53208120,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("new_preferred_capital", "landed_title"),
            ],
            native_option_indices=(1, 2),
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53208120,
                    "active_event": {"option_count": 3},
                },
                event={"event_instance_id": 206},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][1]["scope"]["type_key"] = "county"
        self.assertFalse(
            checks_for(wrong_scope_type)["scope:new_preferred_capital:type"]
        )

        missing_epidemic = copy.deepcopy(context)
        missing_epidemic["saved_scopes"] = missing_epidemic["saved_scopes"][1:]
        missing_checks = checks_for(missing_epidemic)
        self.assertFalse(missing_checks["scope:epidemic:type"])
        self.assertFalse(missing_checks["saved_scope_names_exact"])

        relocation_visible = copy.deepcopy(context)
        relocation_visible["options"].insert(
            0,
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            },
        )
        relocation_visible["options"][1]["rendered_index"] = 1
        relocation_visible["options"][2]["rendered_index"] = 2
        self.assertFalse(
            checks_for(relocation_visible)["authored_options_exact"]
        )

        wrong_snapshot_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53208120,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 206},
            context=context,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(wrong_snapshot_checks["snapshot_option_count"])

    def test_infirm_depression_pulse_binds_only_authored_option(self) -> None:
        event_key = "health.7100"
        contract = _manager_contract(event_key, player=29037)
        context = _context(
            event_key=event_key,
            instance_id=29,
            date_raw=53160264,
            player=29037,
            scopes=[],
            native_option_indices=(0,),
        )
        snapshot = {
            "date_raw": 53160264,
            "active_event": {"option_count": 1},
        }
        event = {"event_instance_id": 29}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(_scope("unreviewed", "value"))
        self.assertFalse(checks_for(extra_scope)["saved_scope_count"])

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

    def test_recovery_ack_accepts_exact_no_physician_scope_variant(self) -> None:
        event_key = "health.1101"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=90,
            date_raw=53178144,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32904),
                _scope("disease_type", "flag"),
            ],
            native_option_indices=(0,),
        )
        snapshot = {
            "date_raw": 53178144,
            "active_event": {"option_count": 1},
        }
        event = {"event_instance_id": 90}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        effective = production._scope_contract_for_context(
            context["saved_scopes"], contract
        )
        self.assertEqual(effective["saved_scope_count"], 2)
        self.assertEqual(effective["unique_character_scope_excludes"], {})
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(_scope("unrelated", "value"))
        extra_checks = checks_for(extra_scope)
        self.assertFalse(extra_checks["saved_scope_names_exact"])

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][1]["scope"]["type_key"] = "value"
        self.assertFalse(checks_for(wrong_type)["scope:disease_type:type"])

        wrong_patient = copy.deepcopy(context)
        wrong_patient["saved_scopes"][0] = _scope(
            "sick_character", "character", 49718
        )
        self.assertFalse(checks_for(wrong_patient)["scope:sick_character"])

        duplicate_alias = copy.deepcopy(context)
        duplicate_alias["saved_scopes"][1]["name"] = "sick_character"
        alias_checks = checks_for(duplicate_alias)
        self.assertFalse(alias_checks["scope:disease_type:type"])
        self.assertFalse(alias_checks["saved_scope_names_exact"])

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

    def test_safe_treatment_success_binds_exact_acknowledgement(self) -> None:
        event_key = "health.3103"
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
        context = _context(
            event_key=event_key,
            instance_id=86,
            date_raw=53177016,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32904),
                _scope("disease_type", "flag"),
                _scope("high_skill_option", "character", 49718),
                _scope("low_skill_option", "character", 36369),
                _scope("physician", "character", 49718),
                _scope("background_terrain_scope", "province"),
                _scope("treatment_picker", "character", 32904),
                _scope("treatment", "flag"),
                _scope("outcome", "flag"),
                _scope("portrait", "character", 49718),
            ],
            native_option_indices=(0,),
        )
        snapshot = {
            "date_raw": 53177016,
            "active_event": {"option_count": 1},
        }
        event = {"event_instance_id": 86}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_portrait = copy.deepcopy(context)
        wrong_portrait["saved_scopes"][-1] = _scope(
            "portrait", "character", 36369
        )
        portrait_checks = checks_for(wrong_portrait)
        self.assertFalse(portrait_checks["scope:portrait"])
        self.assertFalse(portrait_checks["scope:portrait:matches_any"])

        wrong_picker = copy.deepcopy(context)
        wrong_picker["saved_scopes"][6] = _scope(
            "treatment_picker", "character", 49718
        )
        self.assertFalse(checks_for(wrong_picker)["scope:treatment_picker"])

        wrong_outcome_type = copy.deepcopy(context)
        wrong_outcome_type["saved_scopes"][8]["scope"]["type_key"] = "value"
        self.assertFalse(
            checks_for(wrong_outcome_type)["scope:outcome:type"]
        )

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

        missing_alias = copy.deepcopy(context)
        missing_alias["saved_scopes"][-1]["name"] = "result_portrait"
        alias_checks = checks_for(missing_alias)
        self.assertFalse(alias_checks["scope:portrait"])
        self.assertFalse(alias_checks["saved_scope_names_exact"])

    def test_safe_treatment_success_accepts_existing_physician_carry(
        self,
    ) -> None:
        event_key = "health.3103"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=210,
            date_raw=53220576,
            player=32904,
            scopes=[
                _scope("physician", "character", 49718),
                _scope("sick_character", "character", 32904),
                _scope("disease_type", "flag"),
                _scope("treatment_picker", "character", 32904),
                _scope("treatment", "flag"),
                _scope("outcome", "flag"),
                _scope("portrait", "character", 49718),
                _scope("background_terrain_scope", "province"),
            ],
            native_option_indices=(0,),
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53220576,
                    "active_event": {"option_count": 1},
                },
                event={"event_instance_id": 210},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        effective = production._scope_contract_for_context(
            context["saved_scopes"], contract
        )
        self.assertEqual(effective["saved_scope_count"], 8)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_portrait = copy.deepcopy(context)
        wrong_portrait["saved_scopes"][6] = _scope(
            "portrait", "character", 36369
        )
        drift_checks = checks_for(wrong_portrait)
        self.assertFalse(drift_checks["scope:physician:matches_any"])
        self.assertFalse(drift_checks["scope:portrait:matches_any"])

    def test_new_physician_uses_exact_safe_treatment_branch(self) -> None:
        event_key = "health.3101"
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
        context = _context(
            event_key=event_key,
            instance_id=85,
            date_raw=53177016,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32904),
                _scope("disease_type", "flag"),
                _scope("high_skill_option", "character", 49718),
                _scope("low_skill_option", "character", 36369),
                _scope("physician", "character", 49718),
                _scope("background_terrain_scope", "province"),
            ],
            native_option_indices=(0, 1, 3),
        )
        snapshot = {
            "date_raw": 53177016,
            "active_event": {"option_count": 4},
        }
        event = {"event_instance_id": 85}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_physician = copy.deepcopy(context)
        wrong_physician["saved_scopes"][4] = _scope(
            "physician", "character", 36369
        )
        physician_checks = checks_for(wrong_physician)
        self.assertFalse(physician_checks["scope:physician"])
        self.assertFalse(physician_checks["scope:physician:matches_any"])

        mystic_projection = copy.deepcopy(context)
        mystic_projection["options"].insert(
            2,
            {
                "rendered_index": 2,
                "native_option_index": 2,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            },
        )
        mystic_projection["options"][3]["rendered_index"] = 3
        self.assertFalse(
            checks_for(mystic_projection)["authored_options_exact"]
        )

        wrong_background = copy.deepcopy(context)
        wrong_background["saved_scopes"][-1]["scope"]["type_key"] = "value"
        self.assertFalse(
            checks_for(wrong_background)["scope:background_terrain_scope:type"]
        )

        missing_alias = copy.deepcopy(context)
        missing_alias["saved_scopes"][2]["name"] = "excellent_skill_option"
        alias_checks = checks_for(missing_alias)
        self.assertFalse(alias_checks["scope:high_skill_option"])
        self.assertFalse(alias_checks["saved_scope_names_exact"])

    def test_physician_search_hires_exact_high_skill_candidate(self) -> None:
        event_key = "health.3001"
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
        context = _context(
            event_key=event_key,
            instance_id=84,
            date_raw=53176968,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32904),
                _scope("disease_type", "flag"),
                _scope("high_skill_option", "character", 49718),
                _scope("low_skill_option", "character", 36369),
            ],
            native_option_indices=(1, 2, 4),
        )
        snapshot = {
            "date_raw": 53176968,
            "active_event": {"option_count": 5},
        }
        event = {"event_instance_id": 84}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertEqual(contract["date_raw"], 53176968)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        wrong_alias = copy.deepcopy(context)
        wrong_alias["saved_scopes"][2]["name"] = "excellent_skill_option"
        alias_checks = checks_for(wrong_alias)
        self.assertFalse(alias_checks["scope:high_skill_option"])
        self.assertFalse(alias_checks["saved_scope_names_exact"])

        wrong_candidate = copy.deepcopy(context)
        wrong_candidate["saved_scopes"][2] = _scope(
            "high_skill_option", "character", 36369
        )
        candidate_checks = checks_for(wrong_candidate)
        self.assertFalse(candidate_checks["scope:high_skill_option"])
        self.assertFalse(
            candidate_checks["scope:high_skill_option:differs_from"]
        )

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][1]["scope"]["type_key"] = "value"
        self.assertFalse(checks_for(wrong_type)["scope:disease_type:type"])

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 0
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

    def test_third_party_disease_notice_avoids_physician_search(self) -> None:
        event_key = "health.2201"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=20,
            date_raw=53156832,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32797),
                _scope("disease_type", "flag"),
                _scope("health_court_owner", "character", 32904),
                _scope("background_terrain_scope", "province"),
            ],
            native_option_indices=(5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 7)
        self.assertEqual(contract["selected_native_option_index"], 6)
        self.assertEqual(contract["character_scopes"]["health_court_owner"], 32904)

        player_became_patient = copy.deepcopy(context)
        player_became_patient["saved_scopes"][0] = _scope(
            "sick_character", "character", 32904
        )
        patient_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=player_became_patient,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(patient_checks["scope:sick_character:unique_third_party"])

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 4
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
