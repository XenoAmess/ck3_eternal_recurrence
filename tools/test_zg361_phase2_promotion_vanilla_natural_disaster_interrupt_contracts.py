#!/usr/bin/env python3
"""Focused tests for the exact vanilla natural-disaster interrupt contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
from pathlib import Path
import re
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("Z:/p2r247promo_resume/report.json")
REPORT_SHA256 = (
    "517B41DB465D1C8A48F70CE2FADAAE6802C9D2647C5D549DAFF041579F387E5A"
)
EVENT_SOURCE_SHA256 = (
    "9595A5C28C14765142E83229EFC215FE06D457C447DC733537677629AD97DF68"
)
ON_ACTION_SOURCE_SHA256 = (
    "7FA3F8BA729BAA8D4CE716F0DB88A19D8CE4D86C9BE441A6324759780E5F8D95"
)
SCRIPTED_EFFECT_SOURCE_SHA256 = (
    "48483CB13CF885203C43316C4990B684BC9D6ED5B5B3A664CCF228F59EAE44D7"
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
import zg361_phase2_promotion_vanilla_natural_disaster_interrupt_contracts as disaster  # noqa: E402


def _scope(
    name: str,
    type_key: str,
    character_id: int | None = None,
) -> dict[str, object]:
    typed_identity: dict[str, object] = {
        "status": "unavailable",
        "reason": "generic_scope_payload_identity_not_closed",
    }
    if character_id is not None:
        typed_identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": typed_identity,
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


class VanillaNaturalDisasterInterruptContractTests(unittest.TestCase):
    def _r247_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS[
            "natural_disaster.8001"
        ]
        character_scopes = contract["character_scopes"]
        scope_types = contract["scope_types"]
        scopes = [
            _scope(name, "character", character_scopes[name])
            if name in character_scopes
            else _scope(name, scope_types[name])
            for name in contract["saved_scope_name_sets"][0]
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "natural_disaster.8001",
            "current_event_instance_id": 204,
            "date_raw": 53204688,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }],
        }
        snapshot = {
            "date_raw": 53204688,
            "active_event": {"option_count": 1},
        }
        event = {"event_instance_id": 204}
        return snapshot, event, context

    def test_r247_authoritative_report_digest(self) -> None:
        if not REPORT.is_file():
            self.skipTest("R247 live report is not present on this machine")
        self.assertEqual(_sha256(REPORT), REPORT_SHA256)

    def test_r247_exact_frame_selects_the_only_acknowledgement(self) -> None:
        self.assertEqual(
            set(disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS),
            {"natural_disaster.8001", "natural_disaster.7021"},
        )
        contract = disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS[
            "natural_disaster.8001"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["natural_disaster.8001"],
            contract,
        )
        snapshot, event, context = self._r247_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="natural_disaster.8001",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(context["saved_scopes"]), 8)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_r355_flood_frame_binds_exact_river_region_sibling(self) -> None:
        contract = disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS[
            "natural_disaster.8001"
        ]
        contract = production._timeline_contract_for_window(
            contract, starting_date=53199480
        )
        snapshot, event, context = self._r247_frame()
        snapshot["date_raw"] = 53254632
        event["event_instance_id"] = 498
        context["current_event_instance_id"] = 498
        context["date_raw"] = 53254632
        context["saved_scopes"].append(
            _scope("river_region", "geographical_region")
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="natural_disaster.8001",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(context["saved_scopes"]), 9)

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][-1]["scope"]["type_key"] = "province"
        drift_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_type,
            event_key="natural_disaster.8001",
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:river_region:type"])

    def test_r355_river_warning_uses_terminal_native_option_two(self) -> None:
        event_key = "natural_disaster.7021"
        contract = production._timeline_contract_for_window(
            disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS[event_key],
            starting_date=53199480,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 499,
            "date_raw": 53255112,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                _scope("situation", "situation"),
                _scope("situation_sub_region", "situation_sub_region"),
                _scope("epicenter_county", "landed_title"),
                _scope("river_region", "geographical_region"),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((0, 2))
            ],
        }
        snapshot = {
            "date_raw": 53255112,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 499}
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["native_option_indices"], (0, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][1]["native_option_index"] = 1
        drift_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_projection,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_r247_frame_rejects_scope_identity_type_and_option_drift(self) -> None:
        contract = disaster.VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS[
            "natural_disaster.8001"
        ]
        snapshot, event, context = self._r247_frame()

        variants = []
        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53204664
        variants.append((wrong_date, "context_date_raw"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = missing_scope["saved_scopes"][:-1]
        variants.append((missing_scope, "saved_scope_names_exact"))
        wrong_type = copy.deepcopy(context)
        next(
            row
            for row in wrong_type["saved_scopes"]
            if row["name"] == "great_project"
        )["scope"]["type_key"] = "landed_title"
        variants.append((wrong_type, "scope:great_project:type"))
        wrong_character = copy.deepcopy(context)
        next(
            row
            for row in wrong_character["saved_scopes"]
            if row["name"] == "ruler"
        )["scope"]["typed_identity"]["character_id"] = 28093
        variants.append((wrong_character, "scope:ruler"))
        option_drift = copy.deepcopy(context)
        option_drift["options"][0]["native_option_index"] = 1
        variants.append((option_drift, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="natural_disaster.8001",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_ck3_11906_source_has_one_player_acknowledgement(self) -> None:
        event_source = _ck3_source(
            "events/situation_events/tgp_natural_disaster_events.txt"
        )
        on_action_source = _ck3_source(
            "common/on_action/dlc/tgp/tgp_natural_disaster_on_actions.txt"
        )
        scripted_effect_source = _ck3_source(
            "common/scripted_effects/10_dlc_tgp_natural_disaster_scripted_effects.txt"
        )
        if (
            event_source is None
            or on_action_source is None
            or scripted_effect_source is None
        ):
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")

        self.assertEqual(_sha256(event_source), EVENT_SOURCE_SHA256)
        self.assertEqual(_sha256(on_action_source), ON_ACTION_SOURCE_SHA256)
        self.assertEqual(
            _sha256(scripted_effect_source), SCRIPTED_EFFECT_SOURCE_SHA256
        )
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "natural_disaster.8001 =",
        )
        option_headers = re.findall(r"(?m)^\toption\s*=\s*\{", event_block)
        self.assertEqual(len(option_headers), 1)
        option_block = _extract_block(event_block, "\toption =")
        normalized_option = " ".join(option_block.split())
        self.assertEqual(
            normalized_option,
            "option = { name = natural_disaster.8001.a "
            "natural_disaster_warning_tooltip_effect = yes }",
        )
        river_warning_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "natural_disaster.7021 =",
        )
        self.assertEqual(
            len(re.findall(r"(?m)^\toption\s*=\s*\{", river_warning_block)),
            3,
        )
        remaining = river_warning_block
        river_options = []
        for _ in range(3):
            option = _extract_block(remaining, "\toption =")
            river_options.append(option)
            remaining = remaining[remaining.index(option) + len(option):]
        terminal_option = river_options[-1]
        self.assertEqual(
            " ".join(terminal_option.split()),
            "option = { name = natural_disaster.7021.a "
            "natural_disaster_warning_tooltip_effect = yes }",
        )

        join_block = _extract_block(
            on_action_source.read_text(encoding="utf-8-sig"),
            "natural_disaster_join_events =",
        )
        self.assertRegex(
            join_block,
            r"trigger\s*=\s*\{\s*is_ai\s*=\s*no\s*\}",
        )
        self.assertEqual(
            re.findall(r"(?m)^\t\t(natural_disaster\.800[123])\b", join_block),
            [
                "natural_disaster.8001",
                "natural_disaster.8002",
                "natural_disaster.8003",
            ],
        )
        warning_block = _extract_block(
            on_action_source.read_text(encoding="utf-8-sig"),
            "natural_disaster_warning_events =",
        )
        self.assertEqual(
            re.findall(
                r"(?m)^\t\t100\s*=\s*(natural_disaster\.70[0-3]1)\b",
                warning_block,
            ),
            [
                "natural_disaster.7001",
                "natural_disaster.7011",
                "natural_disaster.7021",
                "natural_disaster.7031",
            ],
        )
        base_scopes_block = _extract_block(
            scripted_effect_source.read_text(encoding="utf-8-sig"),
            "natural_disaster_save_base_scopes_effect =",
        )
        self.assertIn(
            "var:river_region ?= { save_scope_as = river_region }",
            " ".join(base_scopes_block.split()),
        )

    def test_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "natural_disaster.8001": {', production_source)
        self.assertNotIn('    "natural_disaster.7021": {', production_source)
        self.assertRegex(
            production_source,
            r"KNOWN_TIMELINE_INTERRUPTS\.update\(\s*"
            r"VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS\s*\)",
        )


if __name__ == "__main__":
    unittest.main()
