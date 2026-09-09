#!/usr/bin/env python3
"""Focused tests for administrative-eunuch story interrupt contracts."""

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
import zg361_phase2_promotion_vanilla_admin_eunuch_interrupt_contracts as admin_eunuch  # noqa: E402


def _scope(
    name: str,
    type_key: str,
    character_id: int | None = None,
) -> dict[str, object]:
    scope: dict[str, object] = {
        "status": "available",
        "type_key": type_key,
    }
    if type_key == "character":
        scope["typed_identity"] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {"name": name, "scope": scope}


def _frame() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    options = [
        {
            "rendered_index": index,
            "native_option_index": index,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        }
        for index in range(3)
    ]
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "ep3_story_cycle_admin_eunuch.8010",
        "current_event_instance_id": 422,
        "date_raw": 53316816,
        "root_scope": _scope("root", "character", 32904)["scope"],
        "saved_scopes": [
            _scope("story", "story"),
            _scope("eunuch", "character", 31801),
            _scope("emperor", "character", 32904),
            _scope("admin_title", "landed_title"),
            _scope("student", "character", 33596937),
            _scope("rival", "character", 16834604),
        ],
        "options": options,
    }
    return (
        {"date_raw": 53316816, "active_event": {"option_count": 3}},
        {"event_instance_id": 422},
        context,
    )


class VanillaAdminEunuchInterruptContractTests(unittest.TestCase):
    def test_r369_eunuch_death_ends_story_through_native_option_two(self) -> None:
        contract = admin_eunuch.VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS[
            "ep3_story_cycle_admin_eunuch.8010"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep3_story_cycle_admin_eunuch.8010"
            ],
            contract,
        )
        snapshot, event, context = _frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep3_story_cycle_admin_eunuch.8010",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertNotIn("max_occurrences", contract)

    def test_r369_eunuch_death_rejects_scope_and_option_drift(self) -> None:
        contract = admin_eunuch.VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS[
            "ep3_story_cycle_admin_eunuch.8010"
        ]
        snapshot, event, context = _frame()

        variants = []
        wrong_emperor = copy.deepcopy(context)
        wrong_emperor["saved_scopes"][2] = _scope(
            "emperor", "character", 31801
        )
        variants.append((wrong_emperor, "scope:emperor"))

        reused_rival = copy.deepcopy(context)
        reused_rival["saved_scopes"][5] = _scope(
            "rival", "character", 33596937
        )
        variants.append((reused_rival, "scope:rival:differs_from"))

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(
            _scope("protege", "character", 33596938)
        )
        variants.append((extra_scope, "saved_scope_names_exact"))

        wrong_options = copy.deepcopy(context)
        wrong_options["options"] = wrong_options["options"][:2]
        variants.append((wrong_options, "authored_options_exact"))

        for changed, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed,
                    event_key="ep3_story_cycle_admin_eunuch.8010",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check], checks)


if __name__ == "__main__":
    unittest.main()
