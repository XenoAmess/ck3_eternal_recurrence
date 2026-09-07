#!/usr/bin/env python3
"""Focused tests for credit/project I-domain reporting-policy contracts."""

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

import zg361_phase2_promotion_credit_project_reporting_policy_contracts as reporting  # noqa: E402
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


class CreditProjectReportingPolicyContractTests(unittest.TestCase):
    def _r218_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.61"
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
            "event_definition_key": "zg361cp.61",
            "current_event_instance_id": 141,
            "date_raw": 53187168,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187168,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 141}
        return snapshot, event, context

    def _r219_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.54"
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
            "event_definition_key": "zg361cp.54",
            "current_event_instance_id": 142,
            "date_raw": 53187192,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(0, 0), _option(1, 2)],
        }
        snapshot = {
            "date_raw": 53187192,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 142}
        return snapshot, event, context

    def _r220_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.56"
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
            "event_definition_key": "zg361cp.56",
            "current_event_instance_id": 143,
            "date_raw": 53187216,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187216,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 143}
        return snapshot, event, context

    def _r221_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.57"
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
            "event_definition_key": "zg361cp.57",
            "current_event_instance_id": 144,
            "date_raw": 53187240,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187240,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 144}
        return snapshot, event, context

    def _r222_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.58"
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
            "event_definition_key": "zg361cp.58",
            "current_event_instance_id": 145,
            "date_raw": 53187264,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187264,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 145}
        return snapshot, event, context

    def test_r218_exact_frame_selects_short_fact_reporting_policy(self) -> None:
        contracts = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS
        self.assertEqual(
            set(contracts),
            {
                "zg361cp.61",
                "zg361cp.54",
                "zg361cp.56",
                "zg361cp.57",
                "zg361cp.58",
            },
        )
        contract = contracts["zg361cp.61"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.61"],
            contract,
        )
        snapshot, event, context = self._r218_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.61",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 58)
        self.assertEqual(len(contract["character_scopes"]), 27)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r218_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.61"
        ]
        snapshot, event, context = self._r218_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187144
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.61",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_i_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.61",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_i_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_i_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.61",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_i_subject"])

    def test_r219_exact_frame_selects_visible_one_hour_report(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.54"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.54"],
            contract,
        )
        snapshot, event, context = self._r219_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.54",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 58)
        self.assertEqual(len(contract["character_scopes"]), 27)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["option_count"], 2)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r219_frame_rejects_option_snapshot_and_scope_drift(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.54"
        ]
        snapshot, event, context = self._r219_frame()

        wrong_snapshot = copy.deepcopy(snapshot)
        wrong_snapshot["active_event"]["option_count"] = 2
        snapshot_checks = production._known_interrupt_checks(
            snapshot=wrong_snapshot,
            event=event,
            context=context,
            event_key="zg361cp.54",
            contract=contract,
        )
        self.assertFalse(snapshot_checks["snapshot_option_count"])

        wrong_mapping = copy.deepcopy(context)
        wrong_mapping["options"][1]["native_option_index"] = 1
        mapping_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_mapping,
            event_key="zg361cp.54",
            contract=contract,
        )
        self.assertFalse(mapping_checks["authored_options_exact"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_i_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.54",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_i_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

    def test_report_build_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.54": {', production_source)

    def test_r220_exact_frame_selects_share_preserving_forward(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.56"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.56"],
            contract,
        )
        snapshot, event, context = self._r220_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.56",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 58)
        self.assertEqual(len(contract["character_scopes"]), 27)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r220_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.56"
        ]
        snapshot, event, context = self._r220_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187192
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.56",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_i_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.56",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_i_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_i_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.56",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_i_subject"])

    def test_forwarded_credit_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.56": {', production_source)

    def test_r221_exact_frame_selects_minimum_complete_freeze(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.57"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.57"],
            contract,
        )
        snapshot, event, context = self._r221_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.57",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 58)
        self.assertEqual(len(contract["character_scopes"]), 27)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r221_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.57"
        ]
        snapshot, event, context = self._r221_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187216
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.57",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_i_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.57",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_i_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_i_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.57",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_i_subject"])

    def test_version_signature_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.57": {', production_source)

    def test_r222_exact_frame_selects_single_direct_owner_route(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.58"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cp.58"],
            contract,
        )
        snapshot, event, context = self._r222_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361cp.58",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 58)
        self.assertEqual(len(contract["character_scopes"]), 27)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r222_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = reporting.CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS[
            "zg361cp.58"
        ]
        snapshot, event, context = self._r222_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187240
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361cp.58",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_cp_i_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361cp.58",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_cp_i_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_cp_i_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 26347
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361cp.58",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_cp_i_subject"])

    def test_report_route_contract_is_not_inlined_in_production_entry(
        self,
    ) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.58": {', production_source)

    def test_contract_is_not_inlined_in_production_entry(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361cp.61": {', production_source)


if __name__ == "__main__":
    unittest.main()
