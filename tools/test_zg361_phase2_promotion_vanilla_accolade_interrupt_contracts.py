#!/usr/bin/env python3
"""Focused tests for exact vanilla accolade interrupt contracts."""

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

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
import zg361_phase2_promotion_vanilla_accolade_interrupt_contracts as accolade  # noqa: E402


def _scope(name: str, character_id: int) -> dict[str, object]:
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


def _frame() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "ep2_accolade_events.0300",
        "current_event_instance_id": 638,
        "date_raw": 53380128,
        "root_scope": _scope("root", 32904)["scope"],
        "saved_scopes": [
            _scope("master_of_revels", 16805323),
            _scope("new_reveler", 32904),
        ],
        "options": [{
            "rendered_index": 0,
            "native_option_index": 0,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        }],
    }
    return (
        {"date_raw": 53380128, "active_event": {"option_count": 1}},
        {"event_instance_id": 638},
        context,
    )


def _bound_contract() -> dict[str, object]:
    event_key = "ep2_accolade_events.0300"
    rebound = production._manager_recovery_contract(
        accolade.VANILLA_ACCOLADE_TIMELINE_CONTRACTS[event_key],
        player=32904,
        event_key=event_key,
    )
    return production._timeline_contract_for_window(
        rebound, starting_date=53380128,
    )


class VanillaAccoladeInterruptContractTests(unittest.TestCase):
    def test_r368_root_reveler_training_selects_only_option(self) -> None:
        reusable = accolade.VANILLA_ACCOLADE_TIMELINE_CONTRACTS[
            "ep2_accolade_events.0300"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep2_accolade_events.0300"
            ],
            reusable,
        )
        contract = _bound_contract()
        snapshot, event, context = _frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep2_accolade_events.0300",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertNotIn("max_occurrences", contract)

    def test_r368_root_reveler_training_rejects_identity_drift(self) -> None:
        contract = _bound_contract()
        snapshot, event, context = _frame()

        variants = []
        wrong_root = copy.deepcopy(context)
        wrong_root["saved_scopes"][1] = _scope("new_reveler", 16805323)
        variants.append((wrong_root, "scope:new_reveler"))

        wrong_knight = copy.deepcopy(context)
        wrong_knight["saved_scopes"][0] = _scope("master_of_revels", 32904)
        variants.append((
            wrong_knight,
            "scope:master_of_revels:unique_third_party",
        ))

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(_scope("new_reveler_2", 33249))
        variants.append((extra_scope, "saved_scope_names_exact"))

        for changed, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed,
                    event_key="ep2_accolade_events.0300",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check], checks)


if __name__ == "__main__":
    unittest.main()
