#!/usr/bin/env python3
"""Purpose-split contracts for tribute manager-recovery interrupts."""

from __future__ import annotations

import copy
import importlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production
import xar_autoplayer.vanilla_events as shared_vanilla_events
from xar_autoplayer.vanilla_events import (
    records_analysis_manager_b as manager_b_analysis_records,
)
from xar_autoplayer.vanilla_events import records_manager_b as manager_b_records
from test_zg361_phase2_manager_recovery_interrupts import (
    _context,
    _manager_contract,
    _scope,
)


def _nonhuman_reward_scopes() -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 34077),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", 54393),
        _scope("intermediary", "character", unavailable_character=True),
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 34077),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
        _scope("decided_on_treasury_reward", "flag"),
    ]


def _resource_reward_scopes(resource_type: str) -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 30502),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", unavailable_character=True),
        _scope("intermediary", "character", unavailable_character=True),
        *[
            _scope(f"{size}_{resource_type}_tribute", "boolean")
            for size in ("small", "adequate", "excessive")
        ],
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 30502),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
        _scope("decided_on_treasury_reward", "flag"),
    ]


def _rejected_eunuch_reward_scopes() -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 16808089),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", 45515),
        _scope("intermediary", "character", unavailable_character=True),
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 16808089),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("eunuch_character", "character", 45515),
        _scope("human_tribute", "character", 45515),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
        _scope("rejected_eunuch", "flag"),
        _scope("decided_on_treasury_reward", "flag"),
    ]


class ManagerRecoveryTributeInterruptTests(unittest.TestCase):
    def test_1005_contract_is_portable_without_losing_existing_variants(
        self,
    ) -> None:
        contract = manager_b_records.MANAGER_TRIBUTE_TIMELINE_CONTRACTS[
            "tribute_mission.1005"
        ]

        self.assertEqual(contract["root_character_id"], "$player")
        self.assertNotIn("date_raw", contract)
        self.assertEqual(len(contract["saved_scope_name_sets"]), 3)
        self.assertEqual(len(contract["scope_variants"]), 4)
        self.assertEqual(
            contract["scope_variants"][0]["saved_scope_count"], 13
        )
        self.assertEqual(
            contract["scope_variants"][1]["saved_scope_count"], 16
        )
        self.assertEqual(
            [
                contract["scope_variants"][index]["saved_scope_count"]
                for index in (2, 3)
            ],
            [16, 16],
        )

    def test_r374_rejected_eunuch_reward_uses_native_legitimacy(self) -> None:
        event_key = "tribute_mission.1005"
        contract = production._manager_recovery_contract(
            manager_b_records.MANAGER_TRIBUTE_TIMELINE_CONTRACTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53530000,
        )
        context = _context(
            event_key=event_key,
            instance_id=1007,
            date_raw=53536032,
            player=32904,
            scopes=_rejected_eunuch_reward_scopes(),
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53536032,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 1007},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        effective = production._interrupt_contract_for_context(
            context,
            contract,
        )
        self.assertEqual(effective["saved_scope_count"], 16)
        self.assertEqual(effective["selected_option_number"], 6)
        self.assertEqual(effective["selected_native_option_index"], 5)

        for name, failed_check in (
            ("tributary_scope", "scope:tributary_scope:matches_any"),
            (
                "secondary_recipient",
                "scope:secondary_recipient:matches_any",
            ),
            (
                "eunuch_character",
                "scope:eunuch_character:optional_matches_any",
            ),
            ("human_tribute", "scope:human_tribute:matches_any"),
        ):
            with self.subTest(identity=name):
                drifted = copy.deepcopy(context)
                row = next(
                    row
                    for row in drifted["saved_scopes"]
                    if row["name"] == name
                )
                row["scope"]["typed_identity"]["character_id"] = 45516
                drift_checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53536032,
                        "active_event": {"option_count": 7},
                    },
                    event={"event_instance_id": 1007},
                    context=drifted,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertFalse(drift_checks[failed_check], drift_checks)

        wrong_flag = copy.deepcopy(context)
        next(
            row
            for row in wrong_flag["saved_scopes"]
            if row["name"] == "rejected_eunuch"
        )["scope"]["type_key"] = "boolean"
        drift_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53536032, "active_event": {"option_count": 7}},
            event={"event_instance_id": 1007},
            context=wrong_flag,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:rejected_eunuch:optional_type"]
        )

        missing = copy.deepcopy(context)
        missing["saved_scopes"] = [
            row
            for row in missing["saved_scopes"]
            if row["name"] != "rejected_eunuch"
        ]
        drift_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53536032, "active_event": {"option_count": 7}},
            event={"event_instance_id": 1007},
            context=missing,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])

    def test_r374_rejected_eunuch_observation_is_available_through_mcp(
        self,
    ) -> None:
        event_key = "tribute_mission.1005"
        exemplar = manager_b_analysis_records.MANAGER_VANILLA_OBSERVATIONS_B[
            event_key
        ]["exemplars"][0]

        self.assertEqual(exemplar["event_instance_id"], 1007)
        self.assertEqual(exemplar["date_raw"], 53536032)
        self.assertEqual(exemplar["snapshot_id"], "native:998")
        self.assertEqual(exemplar["revision"], 999)
        self.assertFalse(exemplar["selection_attempted"])
        self.assertEqual(len(exemplar["saved_scope_raw_types"]), 16)
        self.assertEqual(
            exemplar["artifact_sha256"],
            "65D685D64EC4016E952A8F439A40F0406A9AFBFF459340CA71AD8564B90063DD",
        )

        response = shared_vanilla_events.query_vanilla_event_knowledge_v1(
            event_key
        )
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1007,
        )

    def test_1005_same_pid_reload_refreshes_shared_variant_and_observation(
        self,
    ) -> None:
        event_key = "tribute_mission.1005"
        stale = manager_b_records.MANAGER_TRIBUTE_TIMELINE_CONTRACTS[event_key]
        stale["saved_scope_name_sets"] = stale["saved_scope_name_sets"][:2]
        stale["scope_variants"] = (
            stale["scope_variants"][:1] + stale["scope_variants"][2:]
        )
        manager_b_analysis_records.MANAGER_VANILLA_OBSERVATIONS_B.pop(
            event_key
        )
        shared_vanilla_events.DEFAULT_VANILLA_EVENT_OBSERVATIONS.pop(event_key)

        reloaded = importlib.reload(production)
        refreshed = reloaded.KNOWN_TIMELINE_INTERRUPTS[event_key]

        self.assertEqual(refreshed["root_character_id"], "$player")
        self.assertEqual(len(refreshed["saved_scope_name_sets"]), 3)
        self.assertEqual(len(refreshed["scope_variants"]), 4)
        self.assertIn(
            event_key,
            shared_vanilla_events.DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        )

    def test_human_tribute_receipt_is_repeatable_without_a_lifecycle_ceiling(
        self,
    ) -> None:
        contract = _manager_contract("tribute_mission.1002", player=32904)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_tribute_reward_is_repeatable_without_a_lifecycle_ceiling(self) -> None:
        contract = _manager_contract("tribute_mission.1005", player=32904)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_resource_reward_routes_use_exact_typed_scope_variants(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        for resource_type in ("gold", "herd"):
            with self.subTest(resource_type=resource_type):
                context = _context(
                    event_key=event_key,
                    instance_id=65,
                    date_raw=53168208,
                    player=32904,
                    scopes=_resource_reward_scopes(resource_type),
                    native_option_indices=(0, 1, 2, 3, 5, 6),
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53168208,
                        "active_event": {"option_count": 7},
                    },
                    event={"event_instance_id": 65},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)

        drifted = _context(
            event_key=event_key,
            instance_id=65,
            date_raw=53168208,
            player=32904,
            scopes=_resource_reward_scopes("gold"),
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        drifted["saved_scopes"][3] = _scope(
            "secondary_recipient", "character", 30502
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53168208, "active_event": {"option_count": 7}},
            event={"event_instance_id": 65},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:secondary_recipient:unavailable_character"]
        )

    def test_nonhuman_reward_uses_exact_direct_scope_variant(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150352,
            player=32904,
            scopes=_nonhuman_reward_scopes(),
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150352,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 6)
        self.assertEqual(contract["selected_native_option_index"], 5)
        self.assertEqual(
            contract["scope_variants"][0][
                "unique_character_scope_excludes"
            ]["actor"],
            (32904,),
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"].append(
            _scope("unexpected_scope", "character", 54393)
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150352,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])


if __name__ == "__main__":
    unittest.main()
