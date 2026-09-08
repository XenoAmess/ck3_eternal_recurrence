#!/usr/bin/env python3
"""Focused tests for the R322 vanilla intrigue-temptation interrupt."""

from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import re
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("Z:/ck3_mod_rewrite/_runtime/p2r322incidentsource/report.json")
DRIVER_STATE = Path(
    "Z:/ck3_mod_rewrite/_runtime/p2r322incidentsource_state/"
    "native-session/driver-state.json"
)
REPORT_SHA256 = (
    "040D7FA002CF027DB53671C59D122464E6267AAC4442FF5980D9D458A702D087"
)
DRIVER_STATE_SHA256 = (
    "BB6168CA6DA502859A8215E43A7C9B576B53F335512BDEBA484E05D2430EC056"
)
EVENT_SOURCE_SHA256 = (
    "C8413C1DE5EB1B29BC37A6F5A8A730290499A8FAE75578DBC6C085639B5C6248"
)
ON_ACTION_SOURCE_SHA256 = (
    "E90B02C7E82F9D6B45BD4494DB5A4AD47E48C10232C3C1CF26BBFE9375EBA9CA"
)


def _install_optional_desktop_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE", "press", "hotkey", "moveTo", "click",
            "mouseDown", "mouseUp", "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


_install_optional_desktop_stubs()
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
import zg361_phase2_promotion_vanilla_intrigue_temptation_interrupt_contracts as temptation  # noqa: E402


def _scope(name: str, type_key: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        },
    }


def _character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "type_key": "character",
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


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


class VanillaIntrigueTemptationInterruptContractTests(unittest.TestCase):
    def _r322_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "intrigue_temptation.3020",
            "current_event_instance_id": 41,
            "date_raw": 53170824,
            "root_scope": _character_scope(29037),
            "saved_scopes": [_scope("quarter", "value")],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {
            "date_raw": 53170824,
            "active_event": {"option_count": 2},
        }
        return snapshot, {"event_instance_id": 41}, context

    def test_r322_authoritative_artifact_digests_and_live_window(self) -> None:
        if not REPORT.is_file() or not DRIVER_STATE.is_file():
            self.skipTest("R322 live report/state is not present on this machine")
        self.assertEqual(_sha256(REPORT), REPORT_SHA256)
        self.assertEqual(_sha256(DRIVER_STATE), DRIVER_STATE_SHA256)

        report = json.loads(REPORT.read_text(encoding="utf-8"))
        progression = report["target_progression"]
        unexpected = progression["unexpected_event"]
        context = unexpected["query"]["current_event_window_context"]
        self.assertEqual(progression["timeline_origin_date_raw"], 53147016)
        self.assertEqual(progression["starting_date_raw"], 53164440)
        self.assertEqual(
            progression["observations"][-2:],
            [
                {
                    "active_event": False,
                    "date_raw": 53170776,
                    "paused": True,
                    "revision": 258,
                },
                {
                    "active_event": True,
                    "date_raw": 53170824,
                    "paused": True,
                    "revision": 261,
                },
            ],
        )
        self.assertEqual(53170824 - 53170776, 48)
        self.assertEqual(53170824 - 53169864, 40 * 24)
        self.assertEqual(53170824 - 53164440, 266 * 24)
        self.assertEqual(53170824 - 53147016, 992 * 24)
        self.assertEqual(unexpected["event_definition_key"], "intrigue_temptation.3020")
        self.assertEqual(unexpected["event"]["event_instance_id"], 41)
        self.assertEqual(context["saved_scopes"][0]["name"], "quarter")
        self.assertEqual(context["saved_scopes"][0]["scope"]["type_key"], "value")
        self.assertEqual(
            [option["native_option_index"] for option in context["options"]],
            [0, 1],
        )
        contract = production._resolve_timeline_interrupt_contract(
            "intrigue_temptation.3020",
            player=29037,
            starting_date=progression["starting_date_raw"],
            stop_at_clean_review_boundary=False,
        )
        self.assertIsInstance(contract, dict)
        if not isinstance(contract, dict):
            self.fail("R322 contract did not resolve")
        checks = production._known_interrupt_checks(
            snapshot=unexpected["snapshot"],
            event=unexpected["event"],
            context=context,
            event_key="intrigue_temptation.3020",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        driver_state = json.loads(DRIVER_STATE.read_text(encoding="utf-8"))
        history = driver_state["command_history"]
        self.assertEqual(history[-1]["index"], 220)
        self.assertEqual(
            history[-1]["command"],
            "query-current-event-window-context-v1",
        )
        self.assertEqual(
            history[-1]["result"]["current_event_window_context"]
            ["event_definition_key"],
            "intrigue_temptation.3020",
        )

    def test_r322_exact_frame_selects_terminal_authored_option_b(self) -> None:
        self.assertEqual(
            set(temptation.VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS),
            {"intrigue_temptation.3020"},
        )
        raw_contract = (
            temptation.VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS
            ["intrigue_temptation.3020"]
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["intrigue_temptation.3020"],
            raw_contract,
        )
        contract = production._resolve_timeline_interrupt_contract(
            "intrigue_temptation.3020",
            player=29037,
            starting_date=53164440,
            stop_at_clean_review_boundary=False,
        )
        self.assertIsNotNone(contract)
        if contract is None:
            self.fail("intrigue-temptation contract did not resolve")
        snapshot, event, context = self._r322_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="intrigue_temptation.3020",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["date_raw_range"], (53164440, 53284440))
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["max_occurrences"], 1)

    def test_r322_frame_rejects_root_scope_and_option_drift(self) -> None:
        contract = (
            temptation.VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS
            ["intrigue_temptation.3020"]
        )
        snapshot, event, context = self._r322_frame()

        variants = []
        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53170800
        variants.append((wrong_date, "context_date_raw"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = []
        variants.append((missing_scope, "saved_scope_names_exact"))
        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][0]["scope"]["type_key"] = "boolean"
        variants.append((wrong_scope_type, "scope:quarter:type"))
        wrong_root = copy.deepcopy(context)
        wrong_root["root_scope"] = _character_scope(32904)
        variants.append((wrong_root, "root_character_id"))
        option_drift = copy.deepcopy(context)
        option_drift["options"][1]["native_option_index"] = 2
        variants.append((option_drift, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="intrigue_temptation.3020",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_ck3_11906_source_proves_b_is_the_terminal_branch(self) -> None:
        event_source = _ck3_source(
            "events/lifestyles/intrigue_lifestyle/"
            "intrigue_temptation_events.txt"
        )
        on_action_source = _ck3_source(
            "common/on_action/lifestyles/intrigue_lifestyle_on_actions.txt"
        )
        if event_source is None or on_action_source is None:
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        self.assertEqual(_sha256(on_action_source), ON_ACTION_SOURCE_SHA256)
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "intrigue_temptation.3020 =",
        )
        self.assertEqual(len(re.findall(r"(?m)^\toption\s*=\s*\{", event_block)), 2)
        option_a = _extract_block(event_block, "\t\tname = intrigue_temptation.3020.a")
        option_b = _extract_block(event_block, "\t\tname = intrigue_temptation.3020.b")
        self.assertIn("every_ruler = {", option_a)
        self.assertIn("intrigue_temptation_302x_next_portrait_effect = yes", option_a)
        self.assertEqual(
            " ".join(option_b.split()),
            "name = intrigue_temptation.3020.b add_character_modifier = { "
            "modifier = intrigue_picky_about_partners years = 5 }",
        )
        common_pool = _extract_block(
            on_action_source.read_text(encoding="utf-8-sig"),
            "intrigue_lifestyle_common_events =",
        )
        self.assertRegex(
            common_pool,
            r"(?m)^\s*100\s*=\s*intrigue_temptation\.3020\b",
        )

    def test_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "intrigue_temptation.3020": {', production_source)
        self.assertRegex(
            production_source,
            r"KNOWN_TIMELINE_INTERRUPTS\.update\(\s*"
            r"VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS\s*\)",
        )


if __name__ == "__main__":
    unittest.main()
