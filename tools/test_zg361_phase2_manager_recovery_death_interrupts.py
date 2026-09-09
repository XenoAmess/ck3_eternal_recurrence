#!/usr/bin/env python3
"""Purpose-split tests for manager-cycle death notification drains."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production
import zg361_phase2_promotion_manager_death_contracts as death
from test_zg361_phase2_manager_recovery_interrupts import (
    _context,
    _manager_contract,
    _scope,
)


REPORT = Path("Z:/p2r248restore/report.json")
REPORT_SHA256 = (
    "DAFADC56F489226BD5C4FBC57C9C236DB119FD54ED663B083ABCCBDBE3FF968D"
)
R352_REPORT = Path("Z:/ck3_mod_rewrite/_runtime/p2r352endgamesource/report.json")
R352_REPORT_SHA256 = (
    "152A102810E1F71CDB0DBB7B17E82BEC33B25BF6D168548CACAEFC6B1B1D0BB0"
)
EVENT_SOURCE_SHA256 = (
    "31591A2F2D3A61E65853CC43B9BEF4B001FEB75EA1502861D2FB9AC054AB1FB7"
)
ENGLISH_LOCALIZATION_SHA256 = (
    "D958B353FA4E77834553ED5DF023CB22E0BB416ED79240FBDC5FF27FB2FA7311"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _extract_block(source: str, header: str) -> str:
    match = re.search(rf"(?m)^{re.escape(header)}", source)
    if match is None:
        raise AssertionError(f"source header not found: {header}")
    header_index = match.start()
    open_index = source.index("{", header_index + len(header))
    depth = 0
    for index in range(open_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[header_index:index + 1]
    raise AssertionError(f"unterminated source block: {header}")


def _ck3_source(relative_path: str) -> Path | None:
    for game_root in (ROOT, ROOT.parent):
        candidate = game_root / "Crusader Kings III" / "game" / relative_path
        if candidate.is_file():
            return candidate
    return None


class ManagerRecoveryDeathInterruptTests(unittest.TestCase):
    def test_neutral_spouse_death_uses_only_visible_authored_option(self) -> None:
        event_key = "death_management.1000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=25,
            date_raw=53159208,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("surviving_consort", "character", 32904),
                _scope("dead_character", "character", 32797),
                _scope("deceased_character_stress", "value"),
                _scope("realm", "landed_title"),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53159208,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 25},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "dead_character", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53159208,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 25},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:dead_character:unique_third_party"])

        loved_context = _context(
            event_key=event_key,
            instance_id=469,
            date_raw=53344176,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("surviving_consort", "character", 32904),
                _scope("dead_character", "character", 32797),
                _scope("deceased_character_stress", "value"),
                _scope("realm", "landed_title"),
                _scope("like", "boolean"),
            ],
            native_option_indices=(0,),
        )
        loved_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53344176,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 469},
            context=loved_context,
            event_key=event_key,
            contract=contract,
        )
        loved_effective = production._option_contract_for_context(
            loved_context["options"], contract,
        )
        self.assertTrue(all(loved_checks.values()), loved_checks)
        self.assertEqual(loved_effective["selected_option_number"], 1)
        self.assertEqual(loved_effective["selected_native_option_index"], 0)

    def test_r248_minor_child_death_matches_exact_live_frame(self) -> None:
        if not REPORT.is_file():
            self.skipTest("R248 restore report is not present on this machine")
        self.assertEqual(_sha256(REPORT), REPORT_SHA256)
        payload = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        unexpected = payload["entry"]["unexpected_event"]
        contract = death.MANAGER_DEATH_TIMELINE_CONTRACTS[
            "death_management.1001"
        ]

        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["death_management.1001"],
            contract,
        )
        checks = production._known_interrupt_checks(
            snapshot=unexpected["snapshot"],
            event=unexpected["event"],
            context=unexpected["query"],
            event_key="death_management.1001",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertEqual(contract["character_scopes"], {})
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"dead_character": (32904,)},
        )
        self.assertEqual(contract["saved_scope_count"], 4)
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (3,))
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_r248_minor_child_death_rejects_identity_and_option_drift(self) -> None:
        contract = death.MANAGER_DEATH_TIMELINE_CONTRACTS[
            "death_management.1001"
        ]
        context = _context(
            event_key="death_management.1001",
            instance_id=202,
            date_raw=53201424,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("dead_character", "character", 67046),
                _scope("deceased_character_stress", "value"),
                _scope("realm", "landed_title"),
            ],
            native_option_indices=(3,),
        )
        snapshot = {
            "date_raw": 53201424,
            "active_event": {"option_count": 4},
        }
        event = {"event_instance_id": 202}

        variants = []
        root_as_dead_child = copy.deepcopy(context)
        root_as_dead_child["saved_scopes"][1] = _scope(
            "dead_character", "character", 32904
        )
        variants.append(
            (root_as_dead_child, "scope:dead_character:unique_third_party")
        )
        wrong_memory_type = copy.deepcopy(context)
        wrong_memory_type["saved_scopes"][0] = _scope(
            "new_memory", "value"
        )
        variants.append((wrong_memory_type, "scope:new_memory:type"))
        missing_realm = copy.deepcopy(context)
        missing_realm["saved_scopes"] = missing_realm["saved_scopes"][:-1]
        variants.append((missing_realm, "saved_scope_names_exact"))
        wrong_option = copy.deepcopy(context)
        wrong_option["options"][0]["native_option_index"] = 2
        variants.append((wrong_option, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="death_management.1001",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_r352_adult_loved_child_variant_matches_exact_live_frame(self) -> None:
        contract = _manager_contract("death_management.1001", player=32904)
        context = _context(
            event_key="death_management.1001",
            instance_id=215,
            date_raw=53225400,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("dead_character", "character", 37337),
                _scope("deceased_character_stress", "value"),
                _scope("realm", "landed_title"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225400,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 215},
            context=context,
            event_key="death_management.1001",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        effective = production._option_contract_for_context(
            context["options"], contract
        )
        self.assertEqual(effective["native_option_indices"], (0,))
        self.assertEqual(effective["selected_option_number"], 1)
        self.assertEqual(effective["selected_native_option_index"], 0)

        adult_neutral = copy.deepcopy(context)
        adult_neutral["options"][0]["native_option_index"] = 1
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225400,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 215},
            context=adult_neutral,
            event_key="death_management.1001",
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_r352_report_preserves_pre_selection_contract_drift(self) -> None:
        if not R352_REPORT.is_file():
            self.skipTest("R352 report is not present on this machine")
        self.assertEqual(_sha256(R352_REPORT), R352_REPORT_SHA256)
        payload = json.loads(R352_REPORT.read_text(encoding="utf-8-sig"))
        failure = payload["typed_failure"]
        context = failure["query"]["current_event_window_context"]

        self.assertEqual(failure["event_definition_key"], "death_management.1001")
        self.assertEqual(failure["failed_checks"], [
            "authored_options_exact",
            "scope:dead_character",
        ])
        self.assertIs(failure["selection_attempted"], False)
        self.assertEqual(
            context["root_scope"]["typed_identity"]["character_id"], 32904
        )
        dead_scope = next(
            row for row in context["saved_scopes"]
            if row["name"] == "dead_character"
        )
        self.assertEqual(
            dead_scope["scope"]["typed_identity"]["character_id"], 37337
        )
        self.assertEqual(
            [row["native_option_index"] for row in context["options"]],
            [0],
        )

        checks = production._known_interrupt_checks(
            snapshot=failure["snapshot"],
            event=failure["event"],
            context=context,
            event_key="death_management.1001",
            contract=_manager_contract("death_management.1001", player=32904),
        )
        self.assertTrue(all(checks.values()), checks)

    def test_primary_heir_spouse_death_matches_exact_live_frame(self) -> None:
        event_key = "death_management.1008"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=612,
            date_raw=53362704,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("surviving_consort", "character", 36354),
                _scope("dead_character", "character", 35997),
                _scope("spouse_of_dead_character", "character", 36354),
                _scope(
                    "parent_of_spouse_of_dead_character", "character", 32904
                ),
                _scope("deceased_character_stress", "value"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53362704,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 612},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        mismatched_heir = copy.deepcopy(context)
        mismatched_heir["saved_scopes"][1] = _scope(
            "surviving_consort", "character", 36355
        )
        drift = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53362704,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 612},
            context=mismatched_heir,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift["scope:surviving_consort:matches_any"])

    def test_ck3_11906_child_dispatch_and_observed_routes_match_source(self) -> None:
        event_source = _ck3_source(
            "events/death_events/death_management_events.txt"
        )
        localization_source = _ck3_source(
            "localization/english/event_localization/death_events/"
            "death_management_events_l_english.yml"
        )
        if event_source is None or localization_source is None:
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        self.assertEqual(
            _sha256(localization_source), ENGLISH_LOCALIZATION_SHA256
        )
        source = event_source.read_text(encoding="utf-8-sig")
        death_dispatch = _extract_block(source, "death_management.0001 =")
        normalized_dispatch = " ".join(death_dispatch.split())
        for required in (
            "save_scope_as = dead_character",
            "every_parent = {",
        ):
            self.assertIn(required, normalized_dispatch)
        notification_dispatch = _extract_block(
            source, "death_management.0002 ="
        )
        normalized_notification = " ".join(notification_dispatch.split())
        for required in (
            "any_child = { even_if_dead = yes this = scope:dead_character }",
            "trigger_event = death_management.1001",
        ):
            self.assertIn(required, normalized_notification)

        event_block = _extract_block(source, "death_management.1001 =")
        self.assertEqual(
            len(re.findall(r"(?m)^\toption\s*=\s*\{", event_block)),
            4,
        )
        adult_loved_route = _extract_block(
            event_block[event_block.index("#Good child"):],
            "\toption =",
        )
        adult_loved_normalized = " ".join(adult_loved_route.split())
        for required in (
            "is_adult = yes",
            "target = scope:dead_character",
            "value >= 40",
            "name = death_management.1001.a",
            "base = medium_stress_impact_gain",
            "TARGET = scope:dead_character",
            "FLAG = child",
        ):
            self.assertIn(required, adult_loved_normalized)
        minor_route = _extract_block(
            event_block[event_block.index("#Little child..."):],
            "\toption =",
        )
        normalized = " ".join(minor_route.split())
        for required in (
            "is_adult = no",
            "name = death_management.1001.d",
            "any_child = { count >= 10 }",
            "base = minor_stress_impact_gain",
            "base = medium_stress_impact_gain",
            "TARGET = scope:dead_character",
            "FLAG = child",
        ):
            self.assertIn(required, normalized)

        localization = localization_source.read_text(encoding="utf-8-sig")
        self.assertIn(
            'death_management.1001.t:0 "Outliving a Child"',
            localization,
        )
        self.assertIn(
            'death_management.1001.d:0 "Rest in peace, little '
            '[dead_character.GetFirstNameNoTooltip]."',
            localization,
        )

        heir_spouse = _extract_block(source, "death_management.1008 =")
        heir_spouse_normalized = " ".join(heir_spouse.split())
        self.assertEqual(
            len(re.findall(r"(?m)^\toption\s*=\s*\{", heir_spouse)),
            1,
        )
        self.assertIn("name = death_management.1008.a", heir_spouse_normalized)
        self.assertNotIn("trigger_event =", heir_spouse_normalized)


if __name__ == "__main__":
    unittest.main()
