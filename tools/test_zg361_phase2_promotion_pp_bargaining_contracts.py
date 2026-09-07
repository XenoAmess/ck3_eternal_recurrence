#!/usr/bin/env python3
"""Focused tests for purpose-split PP feedback-bargaining contracts."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]


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

import zg361_phase2_promotion_pp_bargaining_contracts as bargaining  # noqa: E402
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


def _character_scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            },
        },
    }


def _value_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {"status": "available", "type_key": "value"},
    }


def _option(rendered: int, native: int) -> dict[str, object]:
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
    }


class PpBargainingContractTests(unittest.TestCase):
    def _r205_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = bargaining.PP_BARGAINING_TIMELINE_CONTRACTS[
            "zg361pp.149"
        ]
        character_scopes = contract["character_scopes"]
        saved_names = contract["saved_scope_name_sets"][0]
        scopes = [
            _character_scope(name, character_scopes[name])
            if name in character_scopes
            else _value_scope(name)
            for name in saved_names
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361pp.149",
            "current_event_instance_id": 128,
            "date_raw": 53186856,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53186856,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 128}
        return snapshot, event, context

    def test_r205_exact_frame_selects_non_destructive_continuation(self) -> None:
        contracts = bargaining.PP_BARGAINING_TIMELINE_CONTRACTS
        self.assertEqual(set(contracts), {"zg361pp.149"})
        contract = contracts["zg361pp.149"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361pp.149"],
            contract,
        )
        snapshot, event, context = self._r205_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361pp.149",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 48)
        self.assertEqual(len(contract["character_scopes"]), 17)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

    def test_r205_frame_rejects_scope_type_and_alias_drift(self) -> None:
        contract = bargaining.PP_BARGAINING_TIMELINE_CONTRACTS[
            "zg361pp.149"
        ]
        snapshot, event, context = self._r205_frame()

        missing = copy.deepcopy(context)
        missing["saved_scopes"] = [
            row
            for row in missing["saved_scopes"]
            if row["name"] != "zg361_pp_prompt_mechanism"
        ]
        missing_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing,
            event_key="zg361pp.149",
            contract=contract,
        )
        self.assertFalse(missing_checks["scope:zg361_pp_prompt_mechanism:type"])
        self.assertFalse(missing_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_pp_prompt_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361pp.149",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_pp_prompt_subject"])


if __name__ == "__main__":
    unittest.main()
