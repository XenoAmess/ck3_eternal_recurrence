#!/usr/bin/env python3
"""Focused contracts for purpose-split manager elimination interrupts."""

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

import zg361_phase2_promotion_manager_elimination_contracts as elimination  # noqa: E402
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


class ManagerEliminationContractTests(unittest.TestCase):
    def _zg361_5_frame(self) -> tuple[
        dict[str, object], dict[str, object], dict[str, object]
    ]:
        contract = elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS[
            "zg361.5"
        ]
        character_scopes = contract["character_scopes"]
        scope_types = contract["scope_types"]
        saved_names = contract["saved_scope_name_sets"][0]
        scopes = [
            _character_scope(name, character_scopes[name])
            if name in character_scopes
            else _value_scope(name)
            for name in saved_names
        ]
        self.assertEqual(set(scope_types), set(saved_names) - set(character_scopes))
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361.5",
            "current_event_instance_id": 100,
            "date_raw": 53186136,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": scopes,
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53186136,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 100}
        return snapshot, event, context

    def test_r204_exact_frame_selects_merciful_route(self) -> None:
        contract = elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS[
            "zg361.5"
        ]
        snapshot, event, context = self._zg361_5_frame()
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361.5",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(contract["saved_scope_name_sets"][0]), 43)
        self.assertEqual(contract["scope_types"]["zg361_n_elim"], "value")
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

    def test_r204_frame_rejects_scope_and_alias_drift(self) -> None:
        contract = elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS[
            "zg361.5"
        ]
        snapshot, event, context = self._zg361_5_frame()

        missing_value = copy.deepcopy(context)
        missing_value["saved_scopes"] = [
            row
            for row in missing_value["saved_scopes"]
            if row["name"] != "zg361_n_elim"
        ]
        missing_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_value,
            event_key="zg361.5",
            contract=contract,
        )
        self.assertFalse(missing_checks["scope:zg361_n_elim:type"])
        self.assertFalse(missing_checks["saved_scope_names_exact"])

        alias_drift = copy.deepcopy(context)
        subject = next(
            row
            for row in alias_drift["saved_scopes"]
            if row["name"] == "zg361_ch_d_event_subject"
        )
        subject["scope"]["typed_identity"]["character_id"] = 45031
        alias_checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=alias_drift,
            event_key="zg361.5",
            contract=contract,
        )
        self.assertFalse(alias_checks["scope:zg361_ch_d_event_subject"])

    def test_r293_r351_r353_late_variant_binds_dynamic_subjects(self) -> None:
        contract = production._timeline_contract_for_window(
            elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS["zg361.5"],
            starting_date=53199480,
        )
        variant = contract["scope_variants"][0]
        names = variant["saved_scope_names"]

        def context_for(
            *, reopen_subject: int, mentor: int, pip_subject: int,
            notice_subject: int,
        ) -> dict[str, object]:
            characters = {
                **variant["character_scopes"],
                "zg361_b1_reopen_ticket_subject": reopen_subject,
                "zg361_b2_support_mentor": mentor,
                "zg361_b2_pip_deadline_subject": pip_subject,
                "zg361_notice_deadline_subject": notice_subject,
            }
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": "zg361.5",
                "current_event_instance_id": 216,
                "date_raw": 53230200,
                "root_scope": _character_scope("root", 32904)["scope"],
                "saved_scopes": [
                    _character_scope(name, characters[name])
                    if name in characters
                    else _value_scope(name)
                    for name in names
                ],
                "options": [_option(index, index) for index in range(3)],
            }

        snapshot = {
            "date_raw": 53230200,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 216}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361.5",
                contract=contract,
            )

        for context in (
            context_for(
                reopen_subject=45031,
                mentor=30434,
                pip_subject=29747,
                notice_subject=29747,
            ),
            context_for(
                reopen_subject=45031,
                mentor=30434,
                pip_subject=29747,
                notice_subject=28679,
            ),
            context_for(
                reopen_subject=62223,
                mentor=28303,
                pip_subject=29747,
                notice_subject=29747,
            ),
        ):
            checks = checks_for(context)
            self.assertTrue(all(checks.values()), checks)

        player_reopen_subject = context_for(
            reopen_subject=32904,
            mentor=28303,
            pip_subject=29747,
            notice_subject=29747,
        )
        self.assertFalse(checks_for(player_reopen_subject)[
            "scope:zg361_b1_reopen_ticket_subject:unique_third_party"
        ])

        mentor_reused_pip_subject = context_for(
            reopen_subject=62223,
            mentor=29747,
            pip_subject=29747,
            notice_subject=28679,
        )
        self.assertFalse(checks_for(mentor_reused_pip_subject)[
            "scope:zg361_b2_support_mentor:differs_from"
        ])

        wrong_fixed_subject = context_for(
            reopen_subject=62223,
            mentor=28303,
            pip_subject=29747,
            notice_subject=29747,
        )
        index = names.index("zg361_cp_e_subject")
        wrong_fixed_subject["saved_scopes"][index] = _character_scope(
            "zg361_cp_e_subject", 26506
        )
        self.assertFalse(
            checks_for(wrong_fixed_subject)["scope:zg361_cp_e_subject"]
        )

    def test_r355_prompt_variant_binds_current_cross_domain_subject(self) -> None:
        contract = production._timeline_contract_for_window(
            elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS["zg361.5"],
            starting_date=53199480,
        )
        variant = contract["scope_variants"][1]
        names = variant["saved_scope_names"]
        characters = {
            **variant["character_scopes"],
            "zg361_b1_reopen_ticket_subject": 62551,
            "zg361_b2_support_mentor": 30434,
            "zg361_b2_pip_deadline_subject": 29612,
            "zg361_notice_deadline_subject": 29612,
            "zg361_ch_d_event_subject": 30938,
            "zg361_cp_e_subject": 30938,
            "zg361_cp_e_cross_reviewer": 27928,
            "zg361_p3_aa_subject": 30938,
            "zg361_pp_prompt_subject": 30938,
        }
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361.5",
            "current_event_instance_id": 367,
            "date_raw": 53247816,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": [
                _character_scope(name, characters[name])
                if name in characters
                else _value_scope(name)
                for name in names
            ],
            "options": [_option(index, index) for index in range(3)],
        }
        snapshot = {
            "date_raw": 53247816,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 367}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361.5",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(len(names), 61)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        mismatched_prompt = copy.deepcopy(context)
        index = names.index("zg361_pp_prompt_subject")
        mismatched_prompt["saved_scopes"][index] = _character_scope(
            "zg361_pp_prompt_subject", 30939
        )
        self.assertFalse(checks_for(mismatched_prompt)[
            "scope:zg361_pp_prompt_subject:matches_any"
        ])

        player_reviewer = copy.deepcopy(context)
        index = names.index("zg361_cp_e_cross_reviewer")
        player_reviewer["saved_scopes"][index] = _character_scope(
            "zg361_cp_e_cross_reviewer", 32904
        )
        self.assertFalse(checks_for(player_reviewer)[
            "scope:zg361_cp_e_cross_reviewer:unique_third_party"
        ])

    def test_module_owns_exactly_two_elimination_contracts(self) -> None:
        contracts = elimination.MANAGER_ELIMINATION_TIMELINE_CONTRACTS
        self.assertEqual(set(contracts), {"zg361.5", "zg361.6"})
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.5"],
            contracts["zg361.5"],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.6"],
            contracts["zg361.6"],
        )
        self.assertEqual(len(contracts["zg361.6"]["saved_scope_name_sets"][0]), 48)

        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('    "zg361.5": {', production_source)
        self.assertNotIn('    "zg361.6": {', production_source)


if __name__ == "__main__":
    unittest.main()
