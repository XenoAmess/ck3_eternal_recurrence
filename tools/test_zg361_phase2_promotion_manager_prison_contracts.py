#!/usr/bin/env python3
"""Focused tests for exact prison-notification interrupt contracts."""

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

import zg361_phase2_promotion_manager_prison_contracts as prison  # noqa: E402
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


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


class ManagerPrisonInterruptContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event_key = "prison_notification.2002"
        self.contract = prison.MANAGER_PRISON_TIMELINE_CONTRACTS[self.event_key]
        identities = {
            "imprisoner": 30075,
            "prisoner": 36354,
            "bg_override_char": 30075,
            "this_player": 32904,
        }
        self.context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": self.event_key,
            "current_event_instance_id": 608,
            "date_raw": self.contract["date_raw"],
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                _scope(name, "character", identities[name])
                if name in identities
                else _scope(name, self.contract["scope_types"][name])
                for name in self.contract["saved_scope_name_sets"][0]
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

    def _checks(self, context: dict[str, object]) -> dict[str, bool]:
        return production._known_interrupt_checks(
            snapshot={
                "date_raw": self.contract["date_raw"],
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 608},
            context=context,
            event_key=self.event_key,
            contract=self.contract,
        )

    def test_r370_release_notice_selects_empty_acknowledgement(self) -> None:
        checks = self._checks(self.context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(self.contract["selected_option_number"], 1)
        self.assertEqual(self.contract["selected_native_option_index"], 0)
        self.assertEqual(
            self.contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", self.contract)

    def test_r370_release_notice_rejects_scope_drift(self) -> None:
        wrong_background = copy.deepcopy(self.context)
        next(
            row for row in wrong_background["saved_scopes"]
            if row["name"] == "bg_override_char"
        )["scope"]["typed_identity"]["character_id"] = 30076
        self.assertFalse(
            self._checks(wrong_background)["scope:bg_override_char:matches_any"]
        )

        root_imprisoner = copy.deepcopy(self.context)
        next(
            row for row in root_imprisoner["saved_scopes"]
            if row["name"] == "imprisoner"
        )["scope"]["typed_identity"]["character_id"] = 32904
        self.assertFalse(
            self._checks(root_imprisoner)["scope:imprisoner:unique_third_party"]
        )

        wrong_memory_type = copy.deepcopy(self.context)
        next(
            row for row in wrong_memory_type["saved_scopes"]
            if row["name"] == "new_memory"
        )["scope"]["type_key"] = "value"
        self.assertFalse(
            self._checks(wrong_memory_type)["scope:new_memory:type"]
        )

        extra_scope = copy.deepcopy(self.context)
        extra_scope["saved_scopes"].append(_scope("unexpected", "value"))
        extra_checks = self._checks(extra_scope)
        self.assertFalse(extra_checks["saved_scope_names_exact"])
        self.assertFalse(extra_checks["saved_scope_count"])


if __name__ == "__main__":
    unittest.main()
