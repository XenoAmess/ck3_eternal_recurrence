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
EVENT_SOURCE_SHA256 = (
    "31591A2F2D3A61E65853CC43B9BEF4B001FEB75EA1502861D2FB9AC054AB1FB7"
)
ENGLISH_LOCALIZATION_SHA256 = (
    "D958B353FA4E77834553ED5DF023CB22E0BB416ED79240FBDC5FF27FB2FA7311"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _extract_block(source: str, header: str) -> str:
    header_index = source.index(header)
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
        self.assertEqual(contract["character_scopes"], {"dead_character": 67046})
        self.assertEqual(contract["saved_scope_count"], 4)
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (3,))
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["max_occurrences"], 1)

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
        wrong_child = copy.deepcopy(context)
        wrong_child["saved_scopes"][1] = _scope(
            "dead_character", "character", 67047
        )
        variants.append((wrong_child, "scope:dead_character"))
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

    def test_ck3_11906_minor_child_option_is_the_only_matching_route(self) -> None:
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
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "death_management.1001 =",
        )
        self.assertEqual(
            len(re.findall(r"(?m)^\toption\s*=\s*\{", event_block)),
            4,
        )
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


if __name__ == "__main__":
    unittest.main()
