#!/usr/bin/env python3
"""Focused tests for exact Phase 3 metrics-delivery AA contracts."""

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
sys.path.insert(0, str(ROOT / "mod_zhongguo_style" / "tools"))

import gen_361_phase3_metrics_delivery_runtime as generator  # noqa: E402
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
import zg361_phase3_metrics_delivery_aa_contracts as metrics_aa  # noqa: E402


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


def _script_block(source: str, header: str) -> str:
    start = source.index(header)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"unterminated script block: {header}")


class Phase3MetricsDeliveryAAContractTests(unittest.TestCase):
    def _r240_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS[
            "zg361p3.9000"
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
            "event_definition_key": "zg361p3.9000",
            "current_event_instance_id": 163,
            "date_raw": 53187720,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index) for index in range(4)],
        }
        snapshot = {
            "date_raw": 53187720,
            "active_event": {"option_count": 4},
        }
        event = {"event_instance_id": 163}
        return snapshot, event, context

    def _r241_live_m229_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS[
            "zg361p3.229"
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
            "event_definition_key": "zg361p3.229",
            "current_event_instance_id": 164,
            "date_raw": 53187744,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53187744,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 164}
        return snapshot, event, context

    def test_r240_exact_frame_selects_itemized_mode(self) -> None:
        contracts = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS
        self.assertEqual(
            set(contracts),
            {"zg361p3.9000"}
            | {
                event_key
                for event_key, _date_raw in (
                    metrics_aa.PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
                )
            },
        )
        contract = contracts["zg361p3.9000"]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361p3.9000"],
            contract,
        )
        snapshot, event, context = self._r240_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361p3.9000",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 54)
        self.assertEqual(len(contract["character_scopes"]), 23)
        self.assertEqual(len(contract["scope_types"]), 31)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

    def test_r240_frame_rejects_date_scope_and_alias_drift(self) -> None:
        contract = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS[
            "zg361p3.9000"
        ]
        snapshot, event, context = self._r240_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187648
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361p3.9000",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_p3_aa_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361p3.9000",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_p3_aa_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_p3_aa_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 27448
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361p3.9000",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_p3_aa_subject"])

    def test_all_itemized_contracts_share_exact_schema_and_route_vector(self) -> None:
        contracts = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS
        expected_route_vector = tuple(
            (event_key, 1, 0)
            for event_key, _date_raw in (
                metrics_aa.PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
            )
        )
        self.assertEqual(
            metrics_aa.PHASE3_METRICS_DELIVERY_AA_ROUTE_VECTOR,
            expected_route_vector,
        )
        for event_key, date_raw in (
            metrics_aa.PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
        ):
            with self.subTest(event_key=event_key):
                contract = contracts[event_key]
                self.assertIs(
                    production.KNOWN_TIMELINE_INTERRUPTS[event_key],
                    contract,
                )
                self.assertEqual(contract["date_raw"], date_raw)
                self.assertIs(
                    contract["character_scopes"],
                    metrics_aa.PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES,
                )
                self.assertEqual(
                    contract["saved_scope_name_sets"],
                    (metrics_aa.PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES,),
                )
                self.assertEqual(len(contract["saved_scope_name_sets"][0]), 54)
                self.assertEqual(len(contract["character_scopes"]), 23)
                self.assertEqual(len(contract["scope_types"]), 31)
                self.assertEqual(contract["option_count"], 3)
                self.assertEqual(contract["snapshot_option_count"], 3)
                self.assertEqual(contract["native_option_indices"], (0, 1, 2))
                self.assertEqual(contract["selected_option_number"], 1)
                self.assertEqual(contract["selected_native_option_index"], 0)

    def test_r241_live_frozen_m229_frame_matches(self) -> None:
        contract = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS[
            "zg361p3.229"
        ]
        snapshot, event, context = self._r241_live_m229_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361p3.229",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(context["current_event_instance_id"], 164)

    def test_r241_live_m229_rejects_date_scope_and_alias_drift(self) -> None:
        contract = metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS[
            "zg361p3.229"
        ]
        snapshot, event, context = self._r241_live_m229_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53187720
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361p3.229",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_p3_aa_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361p3.229",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_p3_aa_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_p3_aa_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 27448
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361p3.229",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_p3_aa_subject"])

    def test_itemized_source_sequence_barriers_and_route_a_are_frozen(self) -> None:
        schedule = metrics_aa.PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
        mids = tuple(int(event_key.rsplit(".", 1)[1]) for event_key, _ in schedule)
        barriers = dict(metrics_aa.PHASE3_METRICS_DELIVERY_AA_STAGE_BARRIERS)
        self.assertEqual(tuple(generator.DOMAIN_ORDER["aa"]), mids)
        self.assertEqual(generator.STAGE_LAST["aa"], barriers)

        event_source = (
            ROOT
            / "mod_zhongguo_style"
            / "events"
            / "zg361_phase3_metrics_delivery_runtime_events.txt"
        ).read_text(encoding="utf-8-sig")
        effect_source = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in sorted(
                (
                    ROOT
                    / "mod_zhongguo_style"
                    / "common"
                    / "scripted_effects"
                ).glob("zg361_phase3_aa_*_effects.txt")
            )
        )
        for index, mid in enumerate(mids):
            with self.subTest(mid=mid):
                event_block = _script_block(event_source, f"zg361p3.{mid} = {{")
                self.assertEqual(event_block.count("\n\toption = {"), 3)
                self.assertEqual(event_block.count("\n\t\ttrigger = {"), 0)
                for letter in "abc":
                    self.assertEqual(
                        event_block.count(f"zg361_p3_m{mid}_route_{letter}_effect"),
                        1,
                    )

                route_a = _script_block(
                    effect_source,
                    f"zg361_p3_m{mid}_route_a_effect = {{",
                )
                self.assertIn(f"OPERATION_ID = {mid}", route_a)
                self.assertIn("CHOICE = 1", route_a)
                self.assertIn(
                    f"name = zg361_p3_m{mid}_provenance_choice value = 1",
                    route_a,
                )
                if mid in barriers:
                    self.assertEqual(
                        route_a.count(
                            f"zg361_case_aa_advance_{barriers[mid]:02d}_effect"
                        ),
                        1,
                    )
                else:
                    self.assertNotIn("zg361_case_aa_advance_", route_a)

                if index + 1 < len(mids):
                    next_mid = mids[index + 1]
                    self.assertEqual(
                        event_block.count(
                            f"trigger_event = {{ id = zg361p3.{next_mid} days = 1 }}"
                        ),
                        3,
                    )

        m240_route_a = _script_block(
            effect_source,
            "zg361_p3_m240_route_a_effect = {",
        )
        self.assertLess(
            m240_route_a.index("var:zg361_p3_aa_sample_used <"),
            m240_route_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn(
            "change_variable = { name = zg361_p3_aa_sample_used add = 1 }",
            m240_route_a,
        )
        m241_route_a = _script_block(
            effect_source,
            "zg361_p3_m241_route_a_effect = {",
        )
        self.assertIn(
            "trigger_event = { id = zg361p3.9001 days = 1 }",
            m241_route_a,
        )

    def test_metrics_aa_contract_is_registered_without_inline_copy(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        for event_key in metrics_aa.PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS:
            self.assertNotIn(f'    "{event_key}": {{', production_source)
        self.assertIn(
            "KNOWN_TIMELINE_INTERRUPTS.update(\n"
            "    PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS\n"
            ")",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
