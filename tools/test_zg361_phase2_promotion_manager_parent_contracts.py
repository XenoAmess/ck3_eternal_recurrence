#!/usr/bin/env python3
"""Focused tests for the exact vanilla parent-support interrupt."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("Z:/p2r249promo_resume/report.json")
REPORT_SHA256 = (
    "4F2B70AC510157DC8DFD978A3A0418B9A28597D5B88EE50460FD10F4BB6964F1"
)
EVENT_SOURCE_SHA256 = (
    "FAC64C2E65F735A31B3CBA18758F318769131D40C2E20472BF16A0C80559861E"
)
PARENT_EFFECTS_SOURCE_SHA256 = (
    "0BF21F6229BEEEB03C32E6056CCECD89A6F763430608DE768D8458BEFC90F6FA"
)
ENGLISH_LOCALIZATION_SHA256 = (
    "15D143D5E7DB118B41A2809F1C6771712EC6FC1052ECC605C64C9EBC9746721B"
)
SIMP_CHINESE_LOCALIZATION_SHA256 = (
    "D72C09E31639BB51CFD0C61ADA75E3168ED77CDAF1149616D43D093454E59042"
)


sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_manager_parent_contracts as parent  # noqa: E402
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
from test_zg361_phase2_manager_recovery_interrupts import (  # noqa: E402
    _context,
    _scope,
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


class ManagerParentInterruptContractTests(unittest.TestCase):
    def test_r249_report_and_exact_parent_frame_select_terminal_route(self) -> None:
        if not REPORT.is_file():
            self.skipTest("R249 live report is not present on this machine")
        self.assertEqual(_sha256(REPORT), REPORT_SHA256)
        payload = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        unexpected = payload["entry"]["unexpected_event"]
        contract = parent.MANAGER_PARENT_TIMELINE_CONTRACTS["parent.1005"]

        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["parent.1005"],
            contract,
        )
        checks = production._known_interrupt_checks(
            snapshot=unexpected["snapshot"],
            event=unexpected["event"],
            context=unexpected["query"],
            event_key="parent.1005",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertEqual(contract["character_scopes"], {"parent": 29613})
        self.assertEqual(contract["saved_scope_name_sets"], (("parent",),))
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["max_occurrences"], 1)

    def test_r249_parent_frame_rejects_identity_scope_and_option_drift(self) -> None:
        contract = parent.MANAGER_PARENT_TIMELINE_CONTRACTS["parent.1005"]
        context = _context(
            event_key="parent.1005",
            instance_id=205,
            date_raw=53205336,
            player=32904,
            scopes=[_scope("parent", "character", 29613)],
            native_option_indices=(0, 1),
        )
        snapshot = {
            "date_raw": 53205336,
            "active_event": {"option_count": 2},
        }
        event = {"event_instance_id": 205}

        variants = []
        wrong_parent = copy.deepcopy(context)
        wrong_parent["saved_scopes"][0] = _scope(
            "parent", "character", 29614
        )
        variants.append((wrong_parent, "scope:parent"))
        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][0] = _scope("parent", "value")
        variants.append((wrong_type, "scope:parent:type"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = []
        variants.append((missing_scope, "saved_scope_names_exact"))
        wrong_options = copy.deepcopy(context)
        wrong_options["options"][1]["native_option_index"] = 2
        variants.append((wrong_options, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="parent.1005",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_ck3_11906_route_b_is_bounded_and_source_localization_match(self) -> None:
        event_source = _ck3_source("events/relations_events/parent_events.txt")
        effects_source = _ck3_source(
            "common/scripted_effects/00_parent_effects.txt"
        )
        english_source = _ck3_source(
            "localization/english/event_localization/relation_events/"
            "parent_events_l_english.yml"
        )
        chinese_source = _ck3_source(
            "localization/simp_chinese/event_localization/relation_events/"
            "parent_events_l_simp_chinese.yml"
        )
        if any(
            source is None
            for source in (
                event_source,
                effects_source,
                english_source,
                chinese_source,
            )
        ):
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")
        assert event_source is not None
        assert effects_source is not None
        assert english_source is not None
        assert chinese_source is not None

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        self.assertEqual(_sha256(effects_source), PARENT_EFFECTS_SOURCE_SHA256)
        self.assertEqual(_sha256(english_source), ENGLISH_LOCALIZATION_SHA256)
        self.assertEqual(
            _sha256(chinese_source), SIMP_CHINESE_LOCALIZATION_SHA256
        )
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "parent.1005 =",
        )
        self.assertEqual(
            len(re.findall(r"(?m)^\toption\s*=\s*\{", event_block)),
            2,
        )
        route_a = _extract_block(event_block, "\toption =")
        route_b = _extract_block(
            event_block[event_block.index(route_a) + len(route_a):],
            "\toption =",
        )
        normalized_a = " ".join(route_a.split())
        normalized_b = " ".join(route_b.split())
        self.assertIn("modifier = parent_aids_learning_modifier", normalized_a)
        self.assertIn("days = 1825", normalized_a)
        self.assertIn("increase_parent_meddling_value_effect = yes", normalized_a)
        self.assertEqual(
            normalized_b,
            "option = { name = parent.1005.b scope:parent = { "
            "add_opinion = { target = root modifier = disappointed_opinion "
            "opinion = -15 } } }",
        )

        increase_block = _extract_block(
            effects_source.read_text(encoding="utf-8-sig"),
            "increase_parent_meddling_value_effect =",
        )
        normalized_increase = " ".join(increase_block.split())
        self.assertIn("chance = 10", normalized_increase)
        self.assertIn("on_action = parent_meddling_outcome", normalized_increase)
        self.assertIn("days = { 180 365 }", normalized_increase)

        english = english_source.read_text(encoding="utf-8-sig")
        chinese = chinese_source.read_text(encoding="utf-8-sig")
        self.assertIn(
            'parent.1005.b:0 "The words dazzle, but are they all that wise?"',
            english,
        )
        self.assertIn(
            'parent.1005.b: "这些话听上去头头是道，但真的都那么明智吗？"',
            chinese,
        )

    def test_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "parent.1005": {', production_source)
        self.assertRegex(
            production_source,
            r"KNOWN_TIMELINE_INTERRUPTS\.update\(\s*"
            r"VANILLA_EVENT_TIMELINE_CONTRACTS\s*\)",
        )
        self.assertNotIn(
            "MANAGER_PARENT_TIMELINE_CONTRACTS", production_source
        )
        self.assertNotIn(
            "zg361_phase2_promotion_manager_parent_contracts",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
