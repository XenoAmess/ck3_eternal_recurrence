#!/usr/bin/env python3
"""Focused tests for credit/project J-domain matrix/handoff contracts."""

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

import zg361_phase2_promotion_credit_project_matrix_handoff_contracts as matrix  # noqa: E402
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


class CreditProjectMatrixHandoffContractTests(unittest.TestCase):
    def _r226_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.63"
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
            "event_definition_key": "zg361cp.63",
            "current_event_instance_id": 149,
            "date_raw": 53187360,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187360,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 149}
        return snapshot, event, context

    def _r227_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.62"
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
            "event_definition_key": "zg361cp.62",
            "current_event_instance_id": 150,
            "date_raw": 53187384,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187384,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 150}
        return snapshot, event, context

    def _r228_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.65"
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
            "event_definition_key": "zg361cp.65",
            "current_event_instance_id": 151,
            "date_raw": 53187408,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187408,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 151}
        return snapshot, event, context

    def _r229_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.64"
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
            "event_definition_key": "zg361cp.64",
            "current_event_instance_id": 152,
            "date_raw": 53187432,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187432,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 152}
        return snapshot, event, context

    def _r230_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.66"
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
            "event_definition_key": "zg361cp.66",
            "current_event_instance_id": 153,
            "date_raw": 53187456,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187456,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 153}
        return snapshot, event, context

    def _r232_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.67"
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
            "event_definition_key": "zg361cp.67",
            "current_event_instance_id": 154,
            "date_raw": 53187480,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187480,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 154}
        return snapshot, event, context

    def test_r226_exact_frame_selects_high_solid_matrix_weights(self) -> None:
        contracts = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS
        self.assertEqual(
            set(contracts),
            {
                "zg361cp.63",
                "zg361cp.62",
                "zg361cp.65",
                "zg361cp.64",
                "zg361cp.66",
                "zg361cp.67",
            },
        )
        contract = contracts["zg361cp.63"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.63"],
            contract,
        )
        snapshot, event, context = self._r226_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.63",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r226_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.63"
        ]
        snapshot, event, context = self._r226_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187336
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.63",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.63",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.63",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_matrix_weight_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.63": {', production_source)

    def test_r227_exact_frame_selects_minimum_recorded_route(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.62"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.62"],
            contract,
        )
        snapshot, event, context = self._r227_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.62",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r227_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.62"
        ]
        snapshot, event, context = self._r227_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187360
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.62",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.62",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.62",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_recorded_route_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.62": {', production_source)

    def test_r228_exact_frame_selects_minimum_parachute_staffing(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.65"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.65"],
            contract,
        )
        snapshot, event, context = self._r228_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.65",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r228_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.65"
        ]
        snapshot, event, context = self._r228_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187384
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.65",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.65",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.65",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_parachute_staffing_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.65": {', production_source)

    def test_r229_exact_frame_keeps_manager_handoff_pending(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.64"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.64"],
            contract,
        )
        snapshot, event, context = self._r229_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.64",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_r229_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.64"
        ]
        snapshot, event, context = self._r229_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187408
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.64",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.64",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.64",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_manager_handoff_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.64": {', production_source)

    def test_r230_exact_frame_keeps_cancellation_capacity_pending(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.66"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.66"],
            contract,
        )
        snapshot, event, context = self._r230_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.66",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_r230_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.66"
        ]
        snapshot, event, context = self._r230_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187432
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.66",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.66",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.66",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_strategic_cancel_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.66": {', production_source)

    def test_r232_exact_frame_keeps_duplicate_role_on_subject(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.67"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.67"],
            contract,
        )
        snapshot, event, context = self._r232_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.67",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 66)
        self.assertEqual(len(contract["character_scopes"]), 33)
        self.assertEqual(len(contract["scope_types"]), 33)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r232_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = matrix.CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS[
            "zg361cp.67"
        ]
        snapshot, event, context = self._r232_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187456
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.67",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_j_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.67",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_j_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_j_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.67",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_j_subject"])

    def test_duplicate_role_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.67": {', production_source)


if __name__ == "__main__":
    unittest.main()
