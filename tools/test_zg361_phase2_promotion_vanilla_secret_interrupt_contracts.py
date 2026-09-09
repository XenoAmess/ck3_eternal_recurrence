#!/usr/bin/env python3
"""Focused tests for exact vanilla secret interrupt contracts."""

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
import zg361_phase2_promotion_vanilla_secret_interrupt_contracts as secret  # noqa: E402


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


class VanillaSecretInterruptContractTests(unittest.TestCase):
    def _frame(self, *, secret_owner_id: int = 28093) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = secret.VANILLA_SECRET_TIMELINE_CONTRACTS["secrets.0122"]
        character_scopes = contract["character_scopes"]
        scope_types = contract["scope_types"]
        dynamic_character_scopes = {
            "secret_owner": secret_owner_id,
            "secret_exposer": secret_owner_id,
            "embezzler": secret_owner_id,
            "local_secret_owner": secret_owner_id,
        }
        scopes = [
            _scope(name, "character", character_scopes[name])
            if name in character_scopes
            else _scope(name, "character", dynamic_character_scopes[name])
            if name in dynamic_character_scopes
            else _scope(name, scope_types[name])
            for name in contract["saved_scope_name_sets"][0]
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "secrets.0122",
            "current_event_instance_id": 155,
            "date_raw": 53187480,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((1, 2))
            ],
        }
        snapshot = {
            "date_raw": 53187480,
            "active_event": {"option_count": 7},
        }
        event = {"event_instance_id": 155}
        return snapshot, event, context

    def test_r231_exact_frame_selects_authored_forgive(self) -> None:
        self.assertEqual(
            set(secret.VANILLA_SECRET_TIMELINE_CONTRACTS),
            {"secrets.0122"},
        )
        contract = secret.VANILLA_SECRET_TIMELINE_CONTRACTS["secrets.0122"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["secrets.0122"],
            contract,
        )
        snapshot, event, context = self._frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="secrets.0122",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(context["saved_scopes"]), 13)
        self.assertEqual(contract["native_option_indices"], (1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_r290_dynamic_secret_owner_aliases_select_authored_forgive(self) -> None:
        contract = secret.VANILLA_SECRET_TIMELINE_CONTRACTS["secrets.0122"]
        snapshot, event, context = self._frame(secret_owner_id=27275)
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="secrets.0122",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(checks["scope:secret_owner:unique_third_party"])
        self.assertTrue(checks["scope:embezzler:matches_any"])
        self.assertTrue(checks["scope:local_secret_owner:matches_any"])

    def test_r231_frame_rejects_date_scope_alias_and_option_drift(self) -> None:
        contract = secret.VANILLA_SECRET_TIMELINE_CONTRACTS["secrets.0122"]
        snapshot, event, context = self._frame()

        variants = []
        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187456
        variants.append((wrong_date, "context_date_raw"))
        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"] = missing_scope["saved_scopes"][:-1]
        variants.append((missing_scope, "saved_scope_names_exact"))
        wrong_flag_type = copy.deepcopy(context)
        next(
            row
            for row in wrong_flag_type["saved_scopes"]
            if row["name"] == "secret_owner_is_vassal"
        )["scope"]["type_key"] = "value"
        variants.append((wrong_flag_type, "scope:secret_owner_is_vassal:type"))
        alias_drift = copy.deepcopy(context)
        next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "secret_owner"
        )["scope"]["typed_identity"]["character_id"] = 32904
        variants.append((alias_drift, "scope:secret_owner:unique_third_party"))
        derived_alias_drift = copy.deepcopy(context)
        next(
            row
            for row in derived_alias_drift["saved_scopes"]
            if row["name"] == "embezzler"
        )["scope"]["typed_identity"]["character_id"] = 30123
        variants.append((derived_alias_drift, "scope:embezzler:matches_any"))
        option_drift = copy.deepcopy(context)
        option_drift["options"][1]["native_option_index"] = 3
        variants.append((option_drift, "authored_options_exact"))

        for changed_context, failed_check in variants:
            with self.subTest(check=failed_check):
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=changed_context,
                    event_key="secrets.0122",
                    contract=contract,
                )
                self.assertFalse(checks[failed_check])

    def test_secret_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "secrets.0122": {', production_source)
        self.assertIn(
            "KNOWN_TIMELINE_INTERRUPTS.update(VANILLA_SECRET_TIMELINE_CONTRACTS)",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
