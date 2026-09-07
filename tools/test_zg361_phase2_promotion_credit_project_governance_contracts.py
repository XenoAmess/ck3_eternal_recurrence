#!/usr/bin/env python3
"""Focused tests for credit/project R-domain governance contracts."""

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

import zg361_phase2_promotion_credit_project_governance_contracts as governance  # noqa: E402
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


def _option(index: int) -> dict[str, object]:
    return {
        "rendered_index": index,
        "native_option_index": index,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
    }


class CreditProjectGovernanceContractTests(unittest.TestCase):
    def _r234_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = governance.CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS[
            "zg361cp.131"
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
            "event_definition_key": "zg361cp.131",
            "current_event_instance_id": 157,
            "date_raw": 53187528,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187528,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 157}
        return snapshot, event, context

    def test_r234_exact_frame_selects_project_track_one(self) -> None:
        contracts = governance.CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS
        self.assertEqual(set(contracts), {"zg361cp.131"})
        contract = contracts["zg361cp.131"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.131"],
            contract,
        )
        snapshot, event, context = self._r234_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.131",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 74)
        self.assertEqual(len(contract["character_scopes"]), 39)
        self.assertEqual(len(contract["scope_types"]), 35)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r234_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = governance.CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS[
            "zg361cp.131"
        ]
        snapshot, event, context = self._r234_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187504
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.131",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_r_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.131",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_r_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_r_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.131",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_r_subject"])

    def test_governance_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.131": {', production_source)
        self.assertIn(
            "KNOWN_TIMELINE_INTERRUPTS.update("
            "CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS)",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
