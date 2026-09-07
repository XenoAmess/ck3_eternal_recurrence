#!/usr/bin/env python3
"""Focused tests for exact Phase 3 metrics-delivery AJ contracts."""

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
import zg361_phase3_metrics_delivery_aj_contracts as metrics_aj  # noqa: E402


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


class Phase3MetricsDeliveryAJContractTests(unittest.TestCase):
    def _r243_live_m334_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS[
            "zg361p3.334"
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
            "event_definition_key": "zg361p3.334",
            "current_event_instance_id": 188,
            "date_raw": 53188320,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53188320,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 188}
        return snapshot, event, context

    def test_all_aj_contracts_share_exact_schema_and_route_vector(self) -> None:
        contracts = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS
        schedule = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_ITEMIZED_SCHEDULE
        route_vector = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_ROUTE_VECTOR
        self.assertEqual(set(contracts), {event_key for event_key, _ in schedule})
        self.assertEqual(
            route_vector,
            tuple(
                (event_key, 2, 1)
                if event_key == "zg361p3.336"
                else (event_key, 1, 0)
                for event_key, _ in schedule
            ),
        )
        for (event_key, date_raw), (
            route_event_key,
            option_number,
            native_index,
        ) in zip(schedule, route_vector, strict=True):
            with self.subTest(event_key=event_key):
                self.assertEqual(event_key, route_event_key)
                contract = contracts[event_key]
                self.assertIs(
                    production.KNOWN_TIMELINE_INTERRUPTS[event_key],
                    contract,
                )
                self.assertEqual(contract["date_raw"], date_raw)
                self.assertIs(
                    contract["character_scopes"],
                    metrics_aj.PHASE3_METRICS_DELIVERY_AJ_CHARACTER_SCOPES,
                )
                self.assertEqual(
                    contract["saved_scope_name_sets"],
                    (metrics_aj.PHASE3_METRICS_DELIVERY_AJ_SAVED_SCOPE_NAMES,),
                )
                self.assertEqual(len(contract["saved_scope_name_sets"][0]), 62)
                self.assertEqual(len(contract["character_scopes"]), 27)
                self.assertEqual(len(contract["scope_types"]), 35)
                self.assertEqual(contract["option_count"], 3)
                self.assertEqual(contract["snapshot_option_count"], 3)
                self.assertEqual(contract["native_option_indices"], (0, 1, 2))
                self.assertEqual(contract["selected_option_number"], option_number)
                self.assertEqual(
                    contract["selected_native_option_index"],
                    native_index,
                )

    def test_r243_live_frozen_m334_frame_matches(self) -> None:
        contract = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS[
            "zg361p3.334"
        ]
        snapshot, event, context = self._r243_live_m334_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361p3.334",
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(context["current_event_instance_id"], 188)

    def test_r243_live_m334_rejects_date_scope_and_alias_drift(self) -> None:
        contract = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS[
            "zg361p3.334"
        ]
        snapshot, event, context = self._r243_live_m334_frame()

        wrong_date = copy.deepcopy(context)
        wrong_date["date_raw"] = 53188296
        date_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_date,
            event_key="zg361p3.334",
            contract=contract,
        )
        self.assertFalse(date_checks["context_date_raw"])

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_p3_aj_case"
        ]
        scope_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361p3.334",
            contract=contract,
        )
        self.assertFalse(scope_checks["scope:zg361_p3_aj_case:type"])
        self.assertFalse(scope_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_p3_aj_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 27448
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361p3.334",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_p3_aj_subject"])

    def test_aj_source_sequence_barriers_and_selected_routes_are_frozen(self) -> None:
        schedule = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_ITEMIZED_SCHEDULE
        route_vector = metrics_aj.PHASE3_METRICS_DELIVERY_AJ_ROUTE_VECTOR
        mids = tuple(int(event_key.rsplit(".", 1)[1]) for event_key, _ in schedule)
        barriers = dict(metrics_aj.PHASE3_METRICS_DELIVERY_AJ_STAGE_BARRIERS)
        self.assertEqual(tuple(generator.DOMAIN_ORDER["aj"]), mids)
        self.assertEqual(generator.STAGE_LAST["aj"], barriers)

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
                ).glob("zg361_phase3_aj_*_effects.txt")
            )
        )
        for index, (event_key, option_number, native_index) in enumerate(
            route_vector
        ):
            mid = int(event_key.rsplit(".", 1)[1])
            letter = "abc"[native_index]
            with self.subTest(mid=mid):
                event_block = _script_block(event_source, f"{event_key} = {{")
                self.assertEqual(event_block.count("\n\toption = {"), 3)
                self.assertEqual(event_block.count("\n\t\ttrigger = {"), 0)
                for authored_letter in "abc":
                    self.assertEqual(
                        event_block.count(
                            f"zg361_p3_m{mid}_route_{authored_letter}_effect"
                        ),
                        1,
                    )

                selected_route = _script_block(
                    effect_source,
                    f"zg361_p3_m{mid}_route_{letter}_effect = {{",
                )
                self.assertIn(f"OPERATION_ID = {mid}", selected_route)
                self.assertIn(f"CHOICE = {option_number}", selected_route)
                self.assertIn(
                    f"name = zg361_p3_m{mid}_provenance_choice value = {option_number}",
                    selected_route,
                )
                if mid in barriers:
                    self.assertEqual(
                        selected_route.count(
                            f"zg361_case_aj_advance_{barriers[mid]:02d}_effect"
                        ),
                        1,
                    )
                else:
                    self.assertNotIn("zg361_case_aj_advance_", selected_route)

                if index + 1 < len(route_vector):
                    next_event_key = route_vector[index + 1][0]
                    self.assertEqual(
                        event_block.count(
                            f"trigger_event = {{ id = {next_event_key} days = 1 }}"
                        ),
                        3,
                    )

    def test_selected_aj_resource_path_is_reachable_and_finalizes(self) -> None:
        effects_dir = (
            ROOT / "mod_zhongguo_style" / "common" / "scripted_effects"
        )
        effect_source = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in sorted(effects_dir.glob("zg361_phase3_aj_*_effects.txt"))
        )
        lifecycle = (
            effects_dir / "zg361_phase3_portfolio_lifecycle_effects.txt"
        ).read_text(encoding="utf-8-sig")
        initialize = _script_block(
            effect_source,
            "zg361_p3_aj_initialize_effect = {",
        )
        for expected in (
            "zg361_p3_aj_capacity_remaining value = 100",
            "zg361_p3_aj_next_capacity_remaining value = 100",
            "zg361_p3_aj_emergency_total value = 1",
            "zg361_p3_aj_emergency_used value = 0",
            "zg361_p3_aj_wip_limit value = 1",
            "zg361_p3_aj_wip_used value = 0",
            "zg361_p3_aj_value_credit_remaining value = 10000",
        ):
            self.assertIn(expected, initialize)

        m335_a = _script_block(effect_source, "zg361_p3_m335_route_a_effect = {")
        self.assertLess(
            m335_a.index(
                "zg361_p3_aj_emergency_used < var:zg361_p3_aj_emergency_total"
            ),
            m335_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn(
            "change_variable = { name = zg361_p3_aj_emergency_used add = 1 }",
            m335_a,
        )

        m336_b = _script_block(effect_source, "zg361_p3_m336_route_b_effect = {")
        self.assertIn("zg361_p3_demand_estimated_hours value = 10", m336_b)
        self.assertIn("zg361_p3_demand_admitted value = 1", m336_b)

        m340_a = _script_block(effect_source, "zg361_p3_m340_route_a_effect = {")
        self.assertLess(
            m340_a.index("zg361_p3_aj_capacity_remaining >= var:zg361_p3_demand_estimated_hours"),
            m340_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertLess(
            m340_a.index("zg361_p3_aj_wip_used < var:zg361_p3_aj_wip_limit"),
            m340_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn("zg361_p3_aj_wip_used add = 1", m340_a)

        m337_a = _script_block(effect_source, "zg361_p3_m337_route_a_effect = {")
        self.assertLess(
            m337_a.index("zg361_p3_aj_capacity_remaining >= 10"),
            m337_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn("zg361_p3_aj_capacity_remaining subtract = 10", m337_a)
        self.assertIn("zg361_p3_aj_capacity_reserved add = 10", m337_a)

        m341_a = _script_block(effect_source, "zg361_p3_m341_route_a_effect = {")
        self.assertLess(
            m341_a.index("zg361_p3_aj_next_capacity_remaining >= 10"),
            m341_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn("zg361_p3_aj_next_capacity_remaining subtract = 10", m341_a)
        self.assertIn("zg361_p3_demand_active value = 0", m341_a)
        self.assertIn("zg361_p3_demand_reserved_hours value = 0", m341_a)

        m344_a = _script_block(effect_source, "zg361_p3_m344_route_a_effect = {")
        self.assertLess(
            m344_a.index("zg361_p3_aj_value_credit_remaining = 10000"),
            m344_a.index("zg361_case_kernel_record_operation_effect"),
        )
        self.assertIn("zg361_p3_m344_share_total value = 10000", m344_a)
        self.assertIn("zg361_p3_aj_value_credit_remaining value = 0", m344_a)
        self.assertIn("zg361_case_aj_advance_07_effect", m344_a)
        self.assertIn("zg361_p3_finalize_portfolio_effect = yes", m344_a)
        self.assertNotIn("trigger_event = {", m344_a)

        finalize = _script_block(lifecycle, "zg361_p3_finalize_portfolio_effect = {")
        for expected in (
            "zg361_p3_aa_operation_used = 13",
            "zg361_p3_ag_operation_used = 11",
            "zg361_p3_aj_operation_used = 11",
            "zg361_case_aa_active = 0",
            "zg361_case_ag_active = 0",
            "zg361_case_aj_active = 0",
            "zg361_p3_final_conservation_ok value = 1",
        ):
            self.assertIn(expected, finalize)

    def test_aj_contracts_are_registered_without_inline_copies(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        for event_key in metrics_aj.PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS:
            self.assertNotIn(f'    "{event_key}": {{', production_source)
        self.assertIn(
            "KNOWN_TIMELINE_INTERRUPTS.update(\n"
            "    PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS\n"
            ")",
            production_source,
        )


if __name__ == "__main__":
    unittest.main()
