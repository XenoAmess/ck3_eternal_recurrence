#!/usr/bin/env python3
"""Focused tests for administrative-eunuch story interrupt contracts."""

from __future__ import annotations

import copy
import importlib
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
import xar_autoplayer.vanilla_events as shared_vanilla_events  # noqa: E402
from xar_autoplayer.vanilla_events import (  # noqa: E402
    records_analysis_embedded_b as embedded_b_analysis_records,
)
from xar_autoplayer.vanilla_events import (  # noqa: E402
    records_embedded as embedded_records,
)


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


def _bound_8010_contract() -> dict[str, object]:
    event_key = "ep3_story_cycle_admin_eunuch.8010"
    rebound = production._manager_recovery_contract(
        admin_eunuch.VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS[event_key],
        player=32904,
        event_key=event_key,
    )
    return production._timeline_contract_for_window(
        rebound, starting_date=53316816,
    )


def _frame_1001(
    saved_scopes: list[dict[str, object]],
    native_indices: tuple[int, ...] = (0, 1),
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    options = [
        {
            "rendered_index": rendered,
            "native_option_index": native,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        }
        for rendered, native in enumerate(native_indices)
    ]
    context = {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "ep3_story_cycle_admin_eunuch.1001",
        "current_event_instance_id": 988,
        "date_raw": 53513184,
        "root_scope": _scope("root", "character", 32904)["scope"],
        "saved_scopes": saved_scopes,
        "options": options,
    }
    return (
        {"date_raw": 53513184, "active_event": {"option_count": 2}},
        {"event_instance_id": 988},
        context,
    )


def _generated_1001_scopes() -> list[dict[str, object]]:
    return [
        _scope("origin_liege", "character", 63082),
        _scope("origin", "landed_title"),
        _scope("eunuch", "character", 16850194),
        _scope("parent_min_age", "value"),
        _scope("parent_max_age", "value"),
        _scope("parent", "character", 67186091),
        _scope("eunuch_father", "character", 67186091),
        _scope("count", "value"),
        _scope("min_age", "value"),
        _scope("max_age", "value"),
        _scope("newly_created_character", "character", 67186058),
        _scope("story", "story"),
        _scope("family_head", "character", 67186091),
        _scope("new_noble_family_holder", "character", 67186091),
        _scope("government_giver", "character", 67186091),
        _scope("new_title", "landed_title"),
        _scope("noble_family_head", "character", 67186091),
        _scope("liege", "character", 32904),
        _scope("candidate", "character", 16850194),
        _scope("modifier_type", "flag"),
    ]


class VanillaAdminEunuchInterruptContractTests(unittest.TestCase):
    def test_1001_portable_contract_accepts_only_two_exact_source_shapes(
        self,
    ) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.1001"
        contract = embedded_records.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[
            event_key
        ]

        self.assertEqual(contract["root_character_id"], "$player")
        self.assertNotIn("date_raw", contract)
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(contract["saved_scope_counts"], (6, 20))
        self.assertEqual(len(contract["saved_scope_name_sets"]), 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        rebound = production._manager_recovery_contract(
            contract,
            player=32904,
            event_key=event_key,
        )
        rebound = production._timeline_contract_for_window(
            rebound,
            starting_date=53510000,
        )
        legacy_scopes = [
            _scope("eunuch", "character", 16850194),
            _scope("origin", "landed_title"),
            _scope("story", "story"),
            _scope("liege", "character", 32904),
            _scope("candidate", "character", 16850194),
            _scope("modifier_type", "flag"),
        ]
        generated_scopes = _generated_1001_scopes()

        for scopes, native_indices in (
            (legacy_scopes, (0, 1)),
            (generated_scopes, (0, 1)),
            (generated_scopes, (1,)),
        ):
            with self.subTest(
                scope_count=len(scopes), native_indices=native_indices
            ):
                snapshot, event, context = _frame_1001(
                    copy.deepcopy(scopes), native_indices
                )
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=context,
                    event_key=event_key,
                    contract=rebound,
                )
                self.assertTrue(all(checks.values()), checks)
                effective = production._interrupt_contract_for_context(
                    context,
                    rebound,
                )
                self.assertEqual(effective["selected_option_number"], 2)
                self.assertEqual(effective["selected_native_option_index"], 1)

        unobserved_sibling = copy.deepcopy(generated_scopes)
        unobserved_sibling.append(
            _scope("eunuch_sibling", "character", 67186092)
        )
        snapshot, event, context = _frame_1001(unobserved_sibling)
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key=event_key,
            contract=rebound,
        )
        self.assertFalse(checks["saved_scope_names_exact"])
        self.assertFalse(checks["saved_scope_count"])

    def test_1001_generated_shape_rejects_identity_type_and_missing_drift(
        self,
    ) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.1001"
        contract = production._manager_recovery_contract(
            embedded_records.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53510000,
        )

        def change_character(
            scopes: list[dict[str, object]], name: str, character_id: int
        ) -> None:
            row = next(row for row in scopes if row["name"] == name)
            row["scope"]["typed_identity"]["character_id"] = character_id

        mutations: list[tuple[str, list[dict[str, object]], str]] = []
        for name, failed_check in (
            ("candidate", "scope:candidate:matches_any"),
            ("eunuch_father", "scope:eunuch_father:optional_matches_any"),
            ("family_head", "scope:family_head:optional_matches_any"),
            (
                "new_noble_family_holder",
                "scope:new_noble_family_holder:optional_matches_any",
            ),
            (
                "government_giver",
                "scope:government_giver:optional_matches_any",
            ),
            (
                "noble_family_head",
                "scope:noble_family_head:optional_matches_any",
            ),
        ):
            scopes = _generated_1001_scopes()
            change_character(scopes, name, 67186092)
            mutations.append((name, scopes, failed_check))

        wrong_liege = _generated_1001_scopes()
        change_character(wrong_liege, "liege", 63082)
        mutations.append(("liege", wrong_liege, "scope:liege"))

        wrong_value = _generated_1001_scopes()
        next(
            row for row in wrong_value if row["name"] == "parent_min_age"
        )["scope"]["type_key"] = "flag"
        mutations.append(
            (
                "parent_min_age_type",
                wrong_value,
                "scope:parent_min_age:optional_type",
            )
        )

        wrong_title = _generated_1001_scopes()
        next(row for row in wrong_title if row["name"] == "new_title")[
            "scope"
        ]["type_key"] = "province"
        mutations.append(
            ("new_title_type", wrong_title, "scope:new_title:optional_type")
        )

        missing_count = [
            row for row in _generated_1001_scopes() if row["name"] != "count"
        ]
        mutations.append(
            ("missing_count", missing_count, "saved_scope_names_exact")
        )

        for label, scopes, failed_check in mutations:
            with self.subTest(label=label):
                snapshot, event, context = _frame_1001(scopes)
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertFalse(checks[failed_check], checks)

    def test_1001_analysis_observation_and_mcp_are_source_backed(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.1001"
        analysis = embedded_b_analysis_records.VANILLA_EMBEDDED_B_ANALYSIS[
            event_key
        ]
        exemplar = (
            embedded_b_analysis_records.VANILLA_EMBEDDED_B_OBSERVATIONS[
                event_key
            ]["exemplars"][0]
        )

        self.assertEqual(analysis["definition_lines"], "556-671")
        self.assertIn("ten-year cooldown", analysis["repeatability"])
        self.assertIn("rather than loose optionals", analysis["saved_scope_boundary"])
        self.assertEqual(exemplar["run"], "R374")
        self.assertEqual(exemplar["event_instance_id"], 988)
        self.assertEqual(exemplar["date_raw"], 53513184)
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertEqual(exemplar["bridge_pid"], 51852)
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(
            exemplar["artifact_sha256"],
            "FAEFEF7A2F09099A697CE4A0215AECF6CCE080013D2822BBFD65BBB8B38B7116",
        )

        response = shared_vanilla_events.query_vanilla_event_knowledge_v1(
            event_key
        )
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["saved_scope_counts"], [6, 20])
        self.assertEqual(response["analysis"]["definition_lines"], "556-671")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            988,
        )

    def test_1001_is_registered_without_inline_duplicate(self) -> None:
        production_source = (
            ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            '    "ep3_story_cycle_admin_eunuch.1001": {',
            production_source,
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep3_story_cycle_admin_eunuch.1001"
            ],
            embedded_records.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[
                "ep3_story_cycle_admin_eunuch.1001"
            ],
        )

    def test_1001_same_pid_hot_reload_refreshes_cached_contract(self) -> None:
        event_key = "ep3_story_cycle_admin_eunuch.1001"
        stale = embedded_records.EMBEDDED_VANILLA_TIMELINE_CONTRACTS[
            event_key
        ]
        stale["saved_scope_name_sets"] = stale["saved_scope_name_sets"][:1]
        stale["saved_scope_count"] = 6
        stale.pop("saved_scope_counts")
        embedded_b_analysis_records.VANILLA_EMBEDDED_B_OBSERVATIONS.pop(
            event_key
        )
        shared_vanilla_events.DEFAULT_VANILLA_EVENT_OBSERVATIONS.pop(event_key)

        reloaded = importlib.reload(production)
        refreshed = reloaded.KNOWN_TIMELINE_INTERRUPTS[event_key]

        self.assertEqual(refreshed["saved_scope_counts"], (6, 20))
        self.assertEqual(len(refreshed["saved_scope_name_sets"]), 2)
        self.assertNotIn("saved_scope_count", refreshed)
        self.assertIn(
            event_key,
            shared_vanilla_events.DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        )

    def test_r369_eunuch_death_ends_story_through_native_option_two(self) -> None:
        reusable = admin_eunuch.VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS[
            "ep3_story_cycle_admin_eunuch.8010"
        ]
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "ep3_story_cycle_admin_eunuch.8010"
            ],
            reusable,
        )
        contract = _bound_8010_contract()
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
        contract = _bound_8010_contract()
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
