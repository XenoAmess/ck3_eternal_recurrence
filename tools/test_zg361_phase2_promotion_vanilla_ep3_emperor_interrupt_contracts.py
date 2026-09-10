#!/usr/bin/env python3
"""Focused tests for the exact vanilla EP3 emperor interrupt contract."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("Z:/p2r250promo_resume/report.json")
REPORT_SHA256 = (
    "E7EE5D62BF4998F1C082849CC9602C8DA4D9796E6396F1C640145F4BEE0A1061"
)
R287_REPORT = Path(
    "Z:/ck3_mod_rewrite/_runtime/p2r287restore/report.json"
)
R287_REPORT_SHA256 = (
    "3FF264C2B90A15027258E042566408F03B69115CB38A6B0153FC6A582A0879B3"
)
EVENT_SOURCE_SHA256 = (
    "5B59252EF885BB605529B1AE76964A03BA447255DB77951CDBF2CB2AE267BDCD"
)
POWERFUL_FAMILIES_EVENT_SOURCE_SHA256 = (
    "CA19D38CD1C45783E32CF59E21A212642EA407B2DDD8EDE2467DF50ED9F7BC7A"
)
ENGLISH_LOCALIZATION_SHA256 = (
    "1CE764CFEB02858BF5D978ED10DA7C1E68BE48A2281374F1FFE86C0F6DC4BBBE"
)
SIMP_CHINESE_LOCALIZATION_SHA256 = (
    "920FBE1BC3B5B3A46A009ECDD0C6C48AA2B5B5C676781530BBC289DC70FA928D"
)


sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
import zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts as emperor  # noqa: E402
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


class VanillaEp3EmperorInterruptContractTests(unittest.TestCase):
    def test_r366_powerful_family_offer_uses_non_war_refusal(self) -> None:
        event_key = "ep3_powerful_families.8012"
        source_contract = emperor.VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS[
            event_key
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            source_contract,
        )
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53300000,
            absolute_end_date=53350000,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        context = _context(
            event_key=event_key,
            instance_id=429,
            date_raw=53328600,
            player=32904,
            scopes=[
                _scope("generous_family", "character", 32536),
                _scope("liege", "character", 32904),
                _scope("war", "war"),
            ],
            native_option_indices=(0, 1),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53328600,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 429},
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
        self.assertNotIn("max_occurrences", contract)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][0] = _scope(
            "generous_family", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53328600,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 429},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:generous_family:unique_third_party"]
        )

    def _r287_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        context = _context(
            event_key="ep3_emperor_yearly.2170",
            instance_id=204,
            date_raw=53205336,
            player=32904,
            scopes=[_scope("our_county", "landed_title")],
            native_option_indices=(0, 1),
        )
        snapshot = {
            "date_raw": 53205336,
            "active_event": {"option_count": 2},
        }
        event = {"event_instance_id": 204}
        return snapshot, event, context

    def _r250_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        context = _context(
            event_key="ep3_emperor_yearly.2211",
            instance_id=206,
            date_raw=53206512,
            player=32904,
            scopes=[
                _scope("potential_title", "landed_title"),
                _scope("liege", "character", 32904),
                _scope("vassal", "character", 27275),
            ],
            native_option_indices=(1, 2, 3),
        )
        snapshot = {
            "date_raw": 53206512,
            "active_event": {"option_count": 4},
        }
        event = {"event_instance_id": 206}
        return snapshot, event, context

    def _r355_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        context = _context(
            event_key="ep3_emperor_yearly.2211",
            instance_id=364,
            date_raw=53243544,
            player=32904,
            scopes=[
                _scope("potential_title", "landed_title"),
                _scope("liege", "character", 32904),
                _scope("vassal", "character", 30987),
            ],
            native_option_indices=(1, 3),
        )
        snapshot = {
            "date_raw": 53243544,
            "active_event": {"option_count": 4},
        }
        event = {"event_instance_id": 364}
        return snapshot, event, context

    def test_r250_report_digest_and_exact_frame_select_bounded_route(self) -> None:
        if REPORT.is_file():
            self.assertEqual(_sha256(REPORT), REPORT_SHA256)

        source_contract = emperor.VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS[
            "ep3_emperor_yearly.2211"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep3_emperor_yearly.2211"
            ],
            source_contract,
        )
        contract = production._resolve_timeline_interrupt_contract(
            "ep3_emperor_yearly.2211",
            player=32904,
            starting_date=53199480,
            absolute_end_date=53260000,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        snapshot, event, context = self._r250_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep3_emperor_yearly.2211",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"], {"liege": 32904})
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"vassal": (32904,)},
        )
        self.assertEqual(contract["saved_scope_count"], 3)
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (1, 2, 3))
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_r355_two_option_frame_selects_same_terminal_route(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            "ep3_emperor_yearly.2211",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        snapshot, event, context = self._r355_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep3_emperor_yearly.2211",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        effective = production._option_contract_for_context(
            context["options"], contract
        )
        self.assertEqual(effective["native_option_indices"], (1, 3))
        self.assertEqual(effective["selected_option_number"], 4)
        self.assertEqual(effective["selected_native_option_index"], 3)

    def test_r250_frame_rejects_window_scope_and_option_drift(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            "ep3_emperor_yearly.2211",
            player=32904,
            starting_date=53199480,
            absolute_end_date=53260000,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        snapshot, event, context = self._r250_frame()

        variants = []
        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53199456
        variants.append((wrong_date, "context_date_raw"))
        wrong_vassal = copy.deepcopy(context)
        wrong_vassal["saved_scopes"][2] = _scope(
            "vassal", "character", 32904
        )
        variants.append((wrong_vassal, "scope:vassal:unique_third_party"))
        wrong_title_type = copy.deepcopy(context)
        wrong_title_type["saved_scopes"][0] = _scope(
            "potential_title", "province"
        )
        variants.append((wrong_title_type, "scope:potential_title:type"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = missing_scope["saved_scopes"][:-1]
        variants.append((missing_scope, "saved_scope_names_exact"))
        option_drift = copy.deepcopy(context)
        option_drift["options"][0]["native_option_index"] = 0
        variants.append((option_drift, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="ep3_emperor_yearly.2211",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_r287_report_and_exact_county_frame_select_route_a(self) -> None:
        if R287_REPORT.is_file():
            self.assertEqual(_sha256(R287_REPORT), R287_REPORT_SHA256)

        source_contract = emperor.VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS[
            "ep3_emperor_yearly.2170"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep3_emperor_yearly.2170"
            ],
            source_contract,
        )
        contract = production._resolve_timeline_interrupt_contract(
            "ep3_emperor_yearly.2170",
            player=32904,
            starting_date=53199480,
            absolute_end_date=53260000,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        snapshot, event, context = self._r287_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep3_emperor_yearly.2170",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["scope_types"], {
            "our_county": "landed_title",
        })
        self.assertEqual(contract["saved_scope_count"], 1)
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 1)

    def test_r287_frame_rejects_scope_and_option_drift(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            "ep3_emperor_yearly.2170",
            player=32904,
            starting_date=53199480,
            absolute_end_date=53260000,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        snapshot, event, context = self._r287_frame()

        variants = []
        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][0] = _scope(
            "our_county", "province"
        )
        variants.append((wrong_scope_type, "scope:our_county:type"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = []
        variants.append((missing_scope, "saved_scope_names_exact"))
        option_drift = copy.deepcopy(context)
        option_drift["options"][1]["native_option_index"] = 2
        variants.append((option_drift, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="ep3_emperor_yearly.2170",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_ck3_11906_route_c_is_the_bounded_terminal_option(self) -> None:
        event_source = _ck3_source(
            "events/dlc/ep3/ep3_emperor_yearly_2.txt"
        )
        english_source = _ck3_source(
            "localization/english/dlc/ep3/"
            "ep3_emperor_yearly_2_l_english.yml"
        )
        chinese_source = _ck3_source(
            "localization/simp_chinese/dlc/ep3/"
            "ep3_emperor_yearly_2_l_simp_chinese.yml"
        )
        if any(
            source is None
            for source in (event_source, english_source, chinese_source)
        ):
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")
        assert event_source is not None
        assert english_source is not None
        assert chinese_source is not None

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        self.assertEqual(_sha256(english_source), ENGLISH_LOCALIZATION_SHA256)
        self.assertEqual(
            _sha256(chinese_source), SIMP_CHINESE_LOCALIZATION_SHA256
        )
        source_text = event_source.read_text(encoding="utf-8-sig")
        caller_block = _extract_block(
            source_text,
            "ep3_emperor_yearly.2210 =",
        )
        caller_immediate = _extract_block(caller_block, "\timmediate =")
        self.assertIn("liege = { save_scope_as = liege }", caller_immediate)
        self.assertIn("root = { save_scope_as = vassal }", caller_immediate)
        event_block = _extract_block(
            source_text,
            "ep3_emperor_yearly.2211 =",
        )
        self.assertEqual(
            re.findall(
                r"(?m)^\t\tname = (ep3_emperor_yearly\.2211\.[abcd])$",
                event_block,
            ),
            [
                "ep3_emperor_yearly.2211.a",
                "ep3_emperor_yearly.2211.b",
                "ep3_emperor_yearly.2211.d",
                "ep3_emperor_yearly.2211.c",
            ],
        )
        route_c = _extract_block(
            event_block[event_block.rfind("\toption ="):],
            "\toption =",
        )
        self.assertEqual(
            " ".join(route_c.split()),
            "option = { name = ep3_emperor_yearly.2211.c scope:vassal = { "
            "change_influence = minor_influence_loss } change_influence = "
            "minor_influence_gain ai_chance = { base = 100 } }",
        )
        for mutation in (
            "change_appointment_investment",
            "add_hook",
            "add_character_modifier",
            "trigger_event",
        ):
            self.assertNotIn(mutation, route_c)

        english = english_source.read_text(encoding="utf-8-sig")
        chinese = chinese_source.read_text(encoding="utf-8-sig")
        self.assertIn(
            'ep3_emperor_yearly.2211.c: "Your value should be proved with '
            'deeds, not dreams!"',
            english,
        )
        self.assertIn(
            'ep3_emperor_yearly.2211.c: "你的价值应该用行动来证明，而不是梦！"',
            chinese,
        )

    def test_ck3_11906_route_a_avoids_the_efficiency_flag(self) -> None:
        event_source = _ck3_source(
            "events/dlc/ep3/ep3_emperor_yearly_2.txt"
        )
        if event_source is None:
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "ep3_emperor_yearly.2170 =",
        )
        self.assertEqual(
            re.findall(
                r"(?m)^\t\tname = (ep3_emperor_yearly\.2170\.[ab])$",
                event_block,
            ),
            [
                "ep3_emperor_yearly.2170.a",
                "ep3_emperor_yearly.2170.b",
            ],
        )
        route_a_start = event_block.index("\toption =")
        route_a = _extract_block(event_block[route_a_start:], "\toption =")
        route_b_start = event_block.index(
            "\toption =", route_a_start + len(route_a)
        )
        route_b = _extract_block(event_block[route_b_start:], "\toption =")

        self.assertIn("ep3_tunnels_encouraged_county_modifier", route_a)
        self.assertIn("change_influence = major_influence_gain", route_a)
        self.assertNotIn("add_character_flag", route_a)
        self.assertNotIn("trigger_event", route_a)
        self.assertIn("ep3_population_control_county_modifier", route_b)
        self.assertIn("flag = ep3_2170_success", route_b)

    def test_ck3_11906_powerful_family_refusal_avoids_war_mutation(self) -> None:
        event_source = _ck3_source(
            "events/dlc/ep3/ep3_powerful_families_8.txt"
        )
        if event_source is None:
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")

        self.assertEqual(
            _sha256(event_source), POWERFUL_FAMILIES_EVENT_SOURCE_SHA256
        )
        source_text = event_source.read_text(encoding="utf-8-sig")
        caller_block = _extract_block(
            source_text, "ep3_powerful_families.8010 ="
        )
        self.assertIn("years = 15", caller_block)
        self.assertIn("id = ep3_powerful_families.8012", caller_block)
        event_block = _extract_block(
            source_text, "ep3_powerful_families.8012 ="
        )
        options = re.findall(
            r"(?m)^\t\tname = (ep3_powerful_families\.8012\.[ab])$",
            event_block,
        )
        self.assertEqual(
            options,
            ["ep3_powerful_families.8012.a", "ep3_powerful_families.8012.b"],
        )
        route_b_start = event_block.rfind("\toption =")
        route_b = _extract_block(event_block[route_b_start:], "\toption =")
        self.assertIn("change_influence = minor_influence_gain", route_b)
        self.assertNotIn("ep3_pf_8010_b_accept_effect", route_b)
        self.assertNotIn("add_attacker", route_b)
        self.assertNotIn("add_defender", route_b)
        self.assertNotIn("trigger_event", route_b)

    def test_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            '    "ep3_emperor_yearly.2170": {', production_source
        )
        self.assertNotIn(
            '    "ep3_emperor_yearly.2211": {', production_source
        )
        self.assertNotIn(
            '    "ep3_powerful_families.8012": {', production_source
        )
        self.assertRegex(
            production_source,
            r"KNOWN_TIMELINE_INTERRUPTS\.update\("
            r"VANILLA_EVENT_TIMELINE_CONTRACTS\)",
        )
        self.assertNotIn(
            "VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS", production_source
        )
        self.assertNotIn(
            "zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
