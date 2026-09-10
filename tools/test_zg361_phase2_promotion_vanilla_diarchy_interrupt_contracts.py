#!/usr/bin/env python3
"""Focused tests for exact vanilla diarchy interrupt contracts."""

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
import zg361_phase2_promotion_vanilla_diarchy_interrupt_contracts as diarchy  # noqa: E402


def _scope(
    name: str,
    type_key: str,
    character_id: int | None = None,
    *,
    unavailable_character: bool = False,
) -> dict[str, object]:
    if character_id is not None:
        identity: dict[str, object] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    else:
        identity = {
            "status": "unavailable",
            "reason": (
                "character_scope_identity_unavailable"
                if unavailable_character
                else "generic_scope_payload_identity_not_closed"
            ),
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": identity,
        },
    }


def _frame() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "diarchy.8042",
        "current_event_instance_id": 497,
        "date_raw": 53366952,
        "root_scope": _scope("root", "character", 32904)["scope"],
        "saved_scopes": [
            _scope("actor", "character", 32603),
            _scope("recipient", "character", 32904),
            _scope("secondary_actor", "character", unavailable_character=True),
            _scope("secondary_recipient", "character", unavailable_character=True),
            _scope("intermediary", "character", unavailable_character=True),
            _scope("diplomacy_small", "boolean"),
            _scope("diplomacy_large", "boolean"),
            _scope("intrigue_small", "boolean"),
            _scope("intrigue_large", "boolean"),
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
        {"date_raw": 53366952, "active_event": {"option_count": 2}},
        {"event_instance_id": 497},
        context,
    )


def _bound_contract() -> dict[str, object]:
    event_key = "diarchy.8042"
    rebound = production._manager_recovery_contract(
        diarchy.VANILLA_DIARCHY_TIMELINE_CONTRACTS[event_key],
        player=32904,
        event_key=event_key,
    )
    return production._timeline_contract_for_window(
        rebound, starting_date=53366952,
    )


class VanillaDiarchyInterruptContractTests(unittest.TestCase):
    def test_r368_recipient_letter_selects_empty_acknowledgement(self) -> None:
        reusable = diarchy.VANILLA_DIARCHY_TIMELINE_CONTRACTS["diarchy.8042"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["diarchy.8042"], reusable,
        )
        contract = _bound_contract()
        snapshot, event, context = _frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="diarchy.8042",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_r368_recipient_letter_rejects_scope_drift(self) -> None:
        contract = _bound_contract()
        snapshot, event, context = _frame()
        variants = []

        actor_is_recipient = copy.deepcopy(context)
        actor_is_recipient["saved_scopes"][0] = _scope(
            "actor", "character", 32904,
        )
        variants.append((actor_is_recipient, "scope:actor:unique_third_party"))

        participant_became_available = copy.deepcopy(context)
        participant_became_available["saved_scopes"][2] = _scope(
            "secondary_actor", "character", 32603,
        )
        variants.append((
            participant_became_available,
            "scope:secondary_actor:unavailable_character",
        ))

        wrong_flag_type = copy.deepcopy(context)
        wrong_flag_type["saved_scopes"][5]["scope"]["type_key"] = "value"
        variants.append((wrong_flag_type, "scope:diplomacy_small"))

        extra_option = copy.deepcopy(context)
        extra_option["options"].append({
            **extra_option["options"][0],
            "rendered_index": 1,
            "native_option_index": 1,
        })
        variants.append((extra_option, "authored_options_exact"))

        for changed, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed,
                    event_key="diarchy.8042",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check], checks)


if __name__ == "__main__":
    unittest.main()
