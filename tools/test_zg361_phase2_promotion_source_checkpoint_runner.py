#!/usr/bin/env python3
"""CK3-free runner contract tests for the Promotion source capture mode."""

from __future__ import annotations

import copy
from contextlib import ExitStack
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def _install_optional_desktop_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
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
sys.path.insert(0, str(ROOT / "tools"))

import run_zhongguo_acceptance as runner  # noqa: E402
import resume_zg361_phase2_promotion_source_session as retained_client  # noqa: E402
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
from test_zhongguo_phase2_promo_runner_plumbing import (  # noqa: E402
    _enter_common_run_cell_patches,
)


def _player_manager_seed_contract(seed_sha: str = "A" * 64) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": runner.PHASE2_PLAYER_MANAGER_SEED_KIND,
        "seed_purpose": runner.PHASE2_PLAYER_MANAGER_SEED_PURPOSE,
        "status": "ready",
        "ready": True,
        "blocker": "",
        "source": {"sha256": seed_sha},
        "saved_state": {
            "played_character_id": 55001,
            "player_history_id": None,
        },
        "manager_entry": {
            "schema_version": 1,
            "manager_character_id": 55001,
            "reviewable_subject_character_id": 44001,
            "manager_scope": "zga_phase2_manager_owner",
            "subject_scope": "zga_phase2_manager_subject",
            "human": True,
            "alive": True,
            "landed": True,
            "celestial_liege": True,
            "game_rule_enabled": True,
            "existing_direct_reviewable_vassal_count_minimum": 1,
            "b1_active": False,
            "central_active": False,
            "pp_active": False,
            "review_now_eligible": True,
        },
    }


class PromotionSourceCheckpointRunnerTests(unittest.TestCase):
    def test_review_now_waits_for_heartbeat_before_product_postcondition(
        self,
    ) -> None:
        order: list[object] = []

        class Service:
            @staticmethod
            def activate_zhongguo_review_now_v1(
                nonce: str,
                source_progress: dict[str, object],
                *,
                expected_revision: int,
            ) -> dict[str, object]:
                order.append("action")
                return {
                    "accepted": True,
                    "status": "acknowledged_verification_pending",
                    "production_capability_advertised": False,
                }

            @staticmethod
            def snapshot() -> dict[str, object]:
                order.append("snapshot")
                return {
                    "map_ready": True,
                    "revision": 8,
                    "date_raw": 53154120,
                    "played_character": {"character_id": 32904},
                    "diagnostics": {"connection_generation": 1},
                    "paused": True,
                    "speed": 5,
                }

            @staticmethod
            def query_zhongguo_promotion_source_progress_v1(
                request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                order.append("query")
                widgets = [
                    {
                        "effective_visible": {
                            "status": "available",
                            "value": False,
                        }
                    }
                    for _ in range(5)
                ]
                widgets[2]["effective_visible"]["value"] = True
                return {
                    "status": "available",
                    "query_sequence": 2,
                    "binding": {
                        "connection_generation": 1,
                        "player_character_id": 32904,
                    },
                    "zhongguo_promotion_source_progress": {
                        "widgets": widgets
                    },
                }

        evidence: dict[str, object] = {}

        def settle(seconds: float) -> None:
            order.append(("sleep", seconds))

        production._activate_review_now_from_progress(
            Service(),
            source_progress={"query_sequence": 1},
            source_revision=7,
            player=32904,
            connection_generation=1,
            evidence=evidence,
            nonce="promo.entry.review",
            sleeper=settle,
        )

        self.assertEqual(
            order,
            [
                "action",
                ("sleep", production.PAUSED_PROGRESS_SETTLE_SECONDS),
                "snapshot",
                "query",
            ],
        )
        self.assertEqual(
            evidence["review_action_postcondition"]["status"], "verified"
        )

    def test_binding_accepts_revision_growth_without_rebinding(self) -> None:
        snapshot = {
            "snapshot_id": "native:47",
            "revision": 47,
            "native_revision": 46,
            "date_raw": 53147112,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 32904},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 1234},
            "active_event": None,
        }

        observed, event = production._binding(
            snapshot, player=32904, connection_generation=1
        )

        self.assertEqual(observed["revision"], 47)
        self.assertIsNone(event)

    def test_binding_failure_preserves_terminal_frame(self) -> None:
        snapshot = {
            "snapshot_id": "native:104",
            "revision": 104,
            "native_revision": 103,
            "date_raw": 53149440,
            "paused": False,
            "speed": 5,
            "map_ready": True,
            "played_character": {"character_id": 33001},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 200604},
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "active_event": None,
        }

        with self.assertRaises(production.PromotionBindingError) as caught:
            production._binding(
                snapshot, player=32904, connection_generation=1
            )

        self.assertEqual(
            caught.exception.evidence,
            {
                "snapshot_id": "native:104",
                "revision": 104,
                "native_revision": 103,
                "date_raw": 53149440,
                "paused": False,
                "speed": 5,
                "map_ready": True,
                "actual_player_character_id": 33001,
                "expected_player_character_id": 32904,
                "actual_connection_generation": 1,
                "expected_connection_generation": 1,
                "bridge_pid": 200604,
                "one_life_terminal": True,
                "one_life_terminal_reason": "played_character_changed",
                "active_event": None,
            },
        )

    def test_promotion_source_requires_typed_player_manager_seed(self) -> None:
        contract = _player_manager_seed_contract()
        self.assertEqual(
            runner.validate_phase2_promotion_source_seed_contract(contract),
            contract,
        )
        self.assertIsNone(contract["saved_state"]["player_history_id"])

        full_manager_contract = runner.load_phase2_seed_contract()
        full_manager_contract["kind"] = runner.PHASE2_PLAYER_MANAGER_SEED_KIND
        full_manager_contract["seed_purpose"] = (
            runner.PHASE2_PLAYER_MANAGER_SEED_PURPOSE
        )
        full_manager_contract["manager_entry"] = copy.deepcopy(
            contract["manager_entry"]
        )
        full_manager_contract["saved_state"]["played_character_id"] = 55001
        full_manager_contract["saved_state"]["player_history_id"] = None
        full_manager_contract["domain_query_matrix"] = {
            "schema_version": 1,
            "b2_pip_owner_character_id": 55001,
            "incident_owner_character_id": 55001,
            "workforce_owner_character_id": 55001,
            "ai_owned_case_owner_character_id": 55001,
            "ai_owned_case_subject_character_id": 55002,
        }
        with tempfile.TemporaryDirectory() as temporary:
            manager_path = Path(temporary) / "manager-seed.json"
            manager_path.write_text(
                json.dumps(full_manager_contract), encoding="utf-8"
            )
            self.assertEqual(
                runner.load_phase2_seed_contract(manager_path),
                full_manager_contract,
            )

        old_player_subject = {
            "kind": "zg361_phase2_paused_seed",
            "status": "ready",
            "ready": True,
            "saved_state": {
                "played_character_id": 29037,
                "player_history_id": "han_6875",
            },
        }
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError,
            "ready typed player-manager seed: .*kind",
        ):
            runner.validate_phase2_promotion_source_seed_contract(
                old_player_subject
            )

        same_subject = copy.deepcopy(contract)
        same_subject["manager_entry"]["reviewable_subject_character_id"] = 55001
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError, "subject_differs_from_manager"
        ):
            runner.validate_phase2_promotion_source_seed_contract(same_subject)

        fixture_mutated_product = copy.deepcopy(contract)
        fixture_mutated_product["provenance"] = {
            "fixture_opened_product_b1": True,
            "product_receipts_written_by_fixture": False,
        }
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError,
            "provenance_fixture_opened_product_b1_false",
        ):
            runner.validate_phase2_promotion_source_seed_contract(
                fixture_mutated_product
            )

        source_report = {
            "result": "GREEN",
            "typed_manager_entry": copy.deepcopy(contract["manager_entry"]),
            "fixture_opened_product_b1": False,
            "product_receipts_written_by_fixture": False,
        }
        self.assertEqual(
            runner.validate_phase2_promotion_source_seed_contract(
                contract, source_report=source_report
            ),
            contract,
        )
        source_report["product_receipts_written_by_fixture"] = True
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError,
            "source_report_fixture_wrote_no_product_receipts",
        ):
            runner.validate_phase2_promotion_source_seed_contract(
                contract, source_report=source_report
            )

    def test_career_hc_portfolio_mode_card_is_a_known_interrupt(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            payload: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            payload["typed_identity"] = (
                {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
                if character_id is not None
                else {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                }
            )
            return {"name": name, "scope": payload}

        event_key = "zg361ch.950"
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 19,
            "date_raw": 53157000,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                # Inherited call-stack state is permitted but not required.
                scope("zg361_b1_ticket_owner", "character", 29037),
                scope("zg361_ch_d_event_owner", "character", 29037),
                scope("zg361_ch_d_event_subject", "character", 26936),
                scope("zg361_ch_d_event_cycle", "value"),
                scope("zg361_ch_d_event_case", "value"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(4)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53157000, "active_event": {"option_count": 4}},
            event={"event_instance_id": 19},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_compensation_card_keeps_42_authored_slots_and_terminates_af5(self) -> None:
        event_key = "zg361comp.1"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53157768,
        )

        def context_for(
            *, stage_index: int, native_option_indices: tuple[int, ...],
            instance_id: int,
        ) -> dict[str, object]:
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": event_key,
                "current_event_instance_id": instance_id,
                "date_raw": 53157768 + stage_index * 24,
                "root_scope": {
                    "status": "available",
                    "type_key": "character",
                    "typed_identity": {
                        "status": "available",
                        "kind": "character",
                        "character_id": 29037,
                    },
                },
                "saved_scopes": [],
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": native_option_index,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                    for index, native_option_index in enumerate(
                        native_option_indices
                    )
                ],
            }

        # L1-L4, AE1-AE5 and AF1-AF4 retain route 1.
        for stage_index in range(13):
            native_option_indices = tuple(
                range(stage_index * 3, stage_index * 3 + 3)
            )
            context = context_for(
                stage_index=stage_index,
                native_option_indices=native_option_indices,
                instance_id=49 + stage_index,
            )
            checks = production._known_interrupt_checks(
                snapshot={
                    "date_raw": context["date_raw"],
                    "active_event": {"option_count": 42},
                },
                event={"event_instance_id": context["current_event_instance_id"]},
                context=context,
                event_key=event_key,
                contract=contract,
            )

            self.assertTrue(all(checks.values()), (stage_index, checks))
            effective = production._option_contract_for_context(
                context["options"], contract
            )
            self.assertEqual(effective["snapshot_option_count"], 42)
            self.assertEqual(
                effective["selected_option_number"], stage_index * 3 + 1
            )
            self.assertEqual(
                effective["selected_native_option_index"], stage_index * 3
            )

        # AF5 route 3 is authored option 42/native index 41.  It remains the
        # deterministic terminal route as resource gating projects 3, 2 or 1
        # visible choices from the unchanged 42-slot authored event.
        for variant_index, native_option_indices in enumerate(
            ((39, 40, 41), (40, 41), (41,))
        ):
            with self.subTest(
                af5_visible=len(native_option_indices),
                native_option_indices=native_option_indices,
            ):
                instance_id = 80 + variant_index
                context = context_for(
                    stage_index=13,
                    native_option_indices=native_option_indices,
                    instance_id=instance_id,
                )
                snapshot = {
                    "date_raw": context["date_raw"],
                    "active_event": {"option_count": 42},
                }
                event = {"event_instance_id": instance_id}
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
                effective = production._option_contract_for_context(
                    context["options"], contract
                )
                self.assertEqual(effective["snapshot_option_count"], 42)
                self.assertEqual(
                    effective["option_count"], len(native_option_indices)
                )
                self.assertEqual(effective["selected_option_number"], 42)
                self.assertEqual(effective["selected_native_option_index"], 41)

                class Service:
                    def snapshot(self) -> dict[str, object]:
                        return {
                            "snapshot_id": f"native:{instance_id}",
                            "revision": 900 + instance_id,
                            "native_revision": instance_id,
                            "date_raw": context["date_raw"],
                            "map_ready": True,
                            "paused": True,
                            "played_character": {"character_id": 29037},
                            "diagnostics": {"connection_generation": 9},
                            "active_event": {
                                "instance_id": instance_id,
                                "option_count": 42,
                            },
                        }

                    def select_event_option(
                        self, option_number: int, *, event_instance_id: int,
                        expected_revision: int,
                    ) -> dict[str, object]:
                        self.submission = (
                            option_number, event_instance_id, expected_revision,
                        )
                        return {
                            "accepted": True,
                            "status": "submitted",
                            "option_number": option_number,
                            "option_index": 41,
                            "event_selection": {
                                "postcondition_verified": True,
                                "old_event_instance_id": event_instance_id,
                                "new_event_instance_id": None,
                                "selected_option_number": option_number,
                                "selected_native_option_index": 41,
                            },
                        }

                service = Service()
                drain = production._drain_known_timeline_interrupt(
                    service,
                    snapshot=snapshot,
                    event=event,
                    query={"current_event_window_context": context},
                    event_key=event_key,
                    contract=contract,
                    player=29037,
                    connection_generation=9,
                )
                self.assertEqual(
                    service.submission, (42, instance_id, 900 + instance_id)
                )
                self.assertEqual(drain["result"], "GREEN")
                self.assertTrue(all(drain["selection_checks"].values()))

    def test_pp_portfolio_mode_card_is_a_known_interrupt(self) -> None:
        event_key = "zg361pp.9100"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 88,
            "date_raw": 53169192,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [
                {
                    "name": "zg361_b1_ticket_owner",
                    "scope": {
                        "status": "available",
                        "type_key": "character",
                        "typed_identity": {
                            "status": "available",
                            "kind": "character",
                            "character_id": 29037,
                        },
                    },
                }
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(4)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53169192, "active_event": {"option_count": 4}},
            event={"event_instance_id": 88},
            context=context,
            event_key=event_key,
            contract=production.KNOWN_TIMELINE_INTERRUPTS[event_key],
        )

        self.assertTrue(all(checks.values()), checks)
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

    def test_governor_removal_letter_invalidates_scenario_without_click(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def unavailable_character_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": "character",
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "character_scope_identity_unavailable",
                    },
                },
            }

        def generic_scope(name: str, type_key: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": type_key,
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "generic_scope_payload_identity_not_closed",
                    },
                },
            }

        event_key = "ep3_interactions_events.0630"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53160264,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 23,
            "date_raw": 53164992,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope("actor", 36354),
                character_scope("recipient", 29037),
                unavailable_character_scope("secondary_actor"),
                unavailable_character_scope("secondary_recipient"),
                unavailable_character_scope("intermediary"),
                generic_scope("hook", "boolean"),
                generic_scope("force_retirement_treasury_cost", "value"),
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
        snapshot = {"date_raw": 53164992, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 23}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(checks["scope:actor:unique_third_party"])

        earlier_actor = copy.deepcopy(context)
        earlier_actor["saved_scopes"][0] = character_scope("actor", 32904)
        self.assertTrue(all(checks_for(earlier_actor).values()))

        player_actor = copy.deepcopy(context)
        player_actor["saved_scopes"][0] = character_scope("actor", 29037)
        self.assertFalse(
            checks_for(player_actor)["scope:actor:unique_third_party"]
        )

        class NoMutationService:
            def snapshot(self) -> dict[str, object]:
                raise AssertionError("scenario-invalidating event must stay paused")

            def select_event_option(self, *_args: object, **_kwargs: object) -> None:
                raise AssertionError("scenario-invalidating event must not be clicked")

        with self.assertRaises(
            production.PromotionScenarioInvalidatingInterrupt
        ) as raised:
            production._drain_known_timeline_interrupt(
                NoMutationService(),
                snapshot=snapshot,
                event=event,
                query={"current_event_window_context": context},
                event_key=event_key,
                contract=contract,
                player=29037,
                connection_generation=9,
            )
        invalidation = raised.exception.evidence
        self.assertEqual(
            invalidation,
            {
                "classification": "scenario-invalidating-interrupt",
                "handling": "fail-closed-no-selection",
                "product_result": "NOT_EVALUATED",
                "product_red": False,
                "event_definition_key": event_key,
                "date_raw": 53164992,
                "event_instance_id": 23,
                "reason_code": (
                    "governor_resignation_title_transfer_breaks_manager_roster"
                ),
                "reason": (
                    "the event's only enabled option executes "
                    "governor_resignation_title_transfer_effect and removes the "
                    "played manager's governor position/direct-vassal roster"
                ),
                "invalidated_precondition": (
                    "stable_player_manager_governor_position_and_direct_vassal_roster"
                ),
                "actor_character_id": 36354,
                "recipient_character_id": 29037,
                "identity_checks": checks,
                "selection_attempted": False,
            },
        )

    def test_new_governorship_notice_binds_dynamic_previous_holder_alias(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            else:
                value["typed_identity"] = {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                }
            return {"name": name, "scope": value}

        event_key = "ep3_admin_events.0002"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53164992,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 24,
            "date_raw": 53165496,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("title", "landed_title"),
                scope("previous_holder", "character", 28893),
                scope("new_holder", "character", 29037),
                scope("transfer_type", "flag"),
                scope("county_title", "landed_title"),
                scope("nf_gov_type", "government_type"),
                scope("governor_title", "landed_title"),
                scope("previous_governor", "character", 28893),
                scope("appointment_succession", "landed_title"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        snapshot = {"date_raw": 53165496, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 24}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        earlier_shape = copy.deepcopy(context)
        earlier_shape["saved_scopes"] = [
            scope("title", "landed_title"),
            scope("previous_holder", "character", 28557),
            scope("new_holder", "character", 29037),
            scope("transfer_type", "flag"),
            scope("nf_gov_type", "government_type"),
            scope("governor_title", "landed_title"),
            scope("previous_governor", "character", 28557),
        ]
        earlier_checks = checks_for(earlier_shape)
        self.assertTrue(all(earlier_checks.values()), earlier_checks)

        appointment_without_county = copy.deepcopy(earlier_shape)
        appointment_without_county["saved_scopes"].append(
            scope("appointment_succession", "landed_title")
        )
        appointment_checks = checks_for(appointment_without_county)
        self.assertTrue(all(appointment_checks.values()), appointment_checks)

        wrong_optional_type = copy.deepcopy(context)
        wrong_optional_type["saved_scopes"][8] = scope(
            "appointment_succession", "flag"
        )
        self.assertFalse(
            checks_for(wrong_optional_type)[
                "scope:appointment_succession:optional_type"
            ]
        )

        mismatched_alias = copy.deepcopy(context)
        mismatched_alias["saved_scopes"][7] = scope(
            "previous_governor", "character", 28557
        )
        self.assertFalse(
            checks_for(mismatched_alias)["scope:previous_holder:matches_any"]
        )

    def test_retained_client_waits_for_async_dll_reconnect(self) -> None:
        calls = {"capabilities": 0, "clock": 0.0}

        def capabilities() -> dict[str, object]:
            calls["capabilities"] += 1
            connected = calls["capabilities"] >= 3
            return {
                "diagnostics": {
                    "connected": connected,
                    "bridge_pid": 71148 if connected else None,
                    "connection_generation": 2 if connected else 1,
                }
            }

        def clock() -> float:
            calls["clock"] += 0.01
            return calls["clock"]

        service = types.SimpleNamespace(
            capabilities=capabilities,
            snapshot=lambda: {"map_ready": True, "revision": 9},
        )
        actual_capabilities, snapshot = (
            retained_client.wait_for_retained_session_reconnect(
                service,
                {"bridge_pid": 71148},
                timeout_seconds=1.0,
                sleeper=lambda _seconds: None,
                clock=clock,
            )
        )
        self.assertEqual(calls["capabilities"], 3)
        self.assertTrue(actual_capabilities["diagnostics"]["connected"])
        self.assertTrue(snapshot["map_ready"])

    def test_yearly_jingcha_interrupt_rebinds_to_a_retained_window(self) -> None:
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.40"],
            starting_date=53160240,
        )
        self.assertTrue(production._contract_date_matches(53168400, contract))
        self.assertFalse(production._contract_date_matches(53168424, contract))
        self.assertFalse(production._contract_date_matches(53159640, contract))

    def test_value_track_card_selects_bounded_option_and_closes(self) -> None:
        def scope(name: str, type_key: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": type_key},
            }

        event_key = "zg361.30"
        date_raw = 53156880
        instance_id = 21
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": instance_id,
            "date_raw": date_raw,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [
                # R116 carried live review/PIP call-stack scopes here.  They
                # are inherited context, not inputs consumed by zg361.30.
                scope("zg361_b1_ticket_cycle", "value"),
                scope("zg361_n_dog", "value"),
                scope("zg361_n_rabbit", "value"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {
            "date_raw": date_raw,
            "active_event": {"option_count": 2},
        }
        event = {"event_instance_id": instance_id}
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        class Service:
            def snapshot(self) -> dict[str, object]:
                return {
                    "snapshot_id": "native:374",
                    "revision": 375,
                    "native_revision": 374,
                    "date_raw": date_raw,
                    "map_ready": True,
                    "paused": True,
                    "played_character": {"character_id": 29037},
                    "diagnostics": {"connection_generation": 9},
                    "active_event": {
                        "instance_id": instance_id,
                        "option_count": 2,
                    },
                }

            def select_event_option(
                self, option_number: int, *, event_instance_id: int,
                expected_revision: int,
            ) -> dict[str, object]:
                self.submission = (
                    option_number, event_instance_id, expected_revision,
                )
                return {
                    "accepted": True,
                    "status": "submitted",
                    "option_number": option_number,
                    "option_index": 0,
                    "event_selection": {
                        "postcondition_verified": True,
                        "old_event_instance_id": event_instance_id,
                        "new_event_instance_id": None,
                        "selected_option_number": option_number,
                        "selected_native_option_index": 0,
                    },
                }

        service = Service()
        drain = production._drain_known_timeline_interrupt(
            service,
            snapshot=snapshot,
            event=event,
            query={"current_event_window_context": context},
            event_key=event_key,
            contract=contract,
            player=29037,
            connection_generation=9,
        )
        self.assertEqual(service.submission, (1, instance_id, 375))
        self.assertEqual(drain["result"], "GREEN")
        self.assertTrue(all(drain["selection_checks"].values()))

    def test_find_secrets_interrupt_allows_the_three_live_observed_deliveries(self) -> None:
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["spymaster_task.0381"],
            starting_date=53147016,
        )
        self.assertEqual(contract["max_occurrences"], 3)
        for date_raw in (53148768, 53152896, 53157024):
            with self.subTest(date_raw=date_raw):
                self.assertTrue(production._contract_date_matches(date_raw, contract))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_random_interrupt_dates_rebind_but_authored_anchor_stays_exact(self) -> None:
        random_contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[
                "tgp_dynastic_cycle_events.0040"
            ],
            starting_date=53173752,
        )
        self.assertTrue(
            production._contract_date_matches(53182368, random_contract)
        )
        authored_contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361b2.40"],
            starting_date=53173752,
        )
        self.assertTrue(
            production._contract_date_matches(53147040, authored_contract)
        )
        self.assertFalse(
            production._contract_date_matches(53173752, authored_contract)
        )

    def test_retained_client_binds_exact_state_pipe_seed_and_loader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            (state / "profile").mkdir(parents=True)
            cell = root / "source-cell"
            cell.mkdir()
            pipe = r"\\.\pipe\retained-unit"
            (cell / "09_phase2_native_session_retained.json").write_text(
                json.dumps({
                    "result": "RETAINED",
                    "reconnect_authorized": True,
                    "process_restart_required": False,
                    "state_dir": str(state.resolve()),
                    "profile_dir": str((state / "profile").resolve()),
                    "pipe": pipe,
                }),
                encoding="utf-8",
            )
            (cell / "00_phase2_seed_install.json").write_text(
                json.dumps({
                    "result": "GREEN",
                    "contract": _player_manager_seed_contract(),
                }),
                encoding="utf-8",
            )
            (cell / "03_loader_gate.json").write_text(
                json.dumps({"result": "GREEN"}), encoding="utf-8"
            )

            result = retained_client.validate_retained_session_inputs(
                state_dir=state, pipe_name=pipe, source_run_cell=cell
            )
            self.assertTrue(all(result["checks"].values()))
            with self.assertRaisesRegex(
                retained_client.RetainedSessionError, "pipe_exact"
            ):
                retained_client.validate_retained_session_inputs(
                    state_dir=state,
                    pipe_name=r"\\.\pipe\different",
                    source_run_cell=cell,
                )

    def test_retained_client_accepts_exact_managed_restore_pid_successor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            driver_state = state / "native-session" / "driver-state.json"
            driver_state.parent.mkdir(parents=True)
            pipe = r"\\.\pipe\retained-unit"
            checkpoint_sha = "a" * 64
            driver_state.write_text(
                json.dumps({
                    "bridge_pid": 202,
                    "command_history": [{
                        "index": 7,
                        "command": "restore-checkpoint",
                        "ok": True,
                        "result": {
                            "accepted": True,
                            "status": "restored",
                            "restored_date_raw": 53164440,
                            "checkpoint": {
                                "status": "restored",
                                "size": 75,
                                "sha256": checkpoint_sha,
                            },
                            "lifecycle": {
                                "status": "relaunched",
                                "lifecycle_intent": "restore",
                                "pipe": pipe,
                                "previous_pid": 101,
                                "pid": 202,
                                "checkpoint": {
                                    "size": 75,
                                    "sha256": checkpoint_sha,
                                },
                            },
                        },
                    }],
                }),
                encoding="utf-8",
            )
            evidence = retained_client.retained_pid_lineage_evidence(
                state_dir=state,
                retention={"bridge_pid": 101},
                live_pid=202,
                pipe_name=pipe,
            )
            self.assertEqual(evidence["result"], "GREEN")
            self.assertEqual(evidence["restart_count"], 1)
            self.assertEqual(evidence["restores"][0]["previous_pid"], 101)
            self.assertEqual(evidence["restores"][0]["pid"], 202)

            with self.assertRaisesRegex(
                retained_client.RetainedSessionError,
                "retained_or_managed_restore_successor",
            ):
                retained_client.retained_pid_lineage_evidence(
                    state_dir=state,
                    retention={"bridge_pid": 303},
                    live_pid=202,
                    pipe_name=pipe,
                )

    def _capabilities(self, pid: int) -> dict[str, object]:
        bridge_labels = (
            runner.PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_BRIDGE_CAPABILITY_LABELS
        )
        query_labels = (
            runner.PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_QUERY_FLAG_LABELS
        )
        action_labels = (
            runner.PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_ACTION_STEP_LABELS
        )
        result: dict[str, object] = {
            "mode": runner.NATIVE_BRIDGE_MODE,
            "backend_id": runner.NATIVE_BRIDGE_MODE,
            "visual_fallback": False,
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": sorted(
                runner.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
                for label in bridge_labels
            ),
            "action_steps": sorted(
                runner.PHASE2_REQUIRED_ACTION_STEPS[label]
                for label in action_labels
            ),
            "diagnostics": {
                "connected": True,
                "bridge_pid": pid,
                "connection_generation": 9,
            },
            "checkpoint_materialization": {"configured": True},
            "native_session_control": {"configured": True},
        }
        for label in query_labels:
            result[runner.PHASE2_REQUIRED_QUERY_FLAGS[label]] = True
        return result

    def test_focused_preflight_requires_exact_entry_query_action_and_save(self) -> None:
        pid = 361147
        capabilities = self._capabilities(pid)
        service = types.SimpleNamespace(capabilities=lambda: capabilities)
        with tempfile.TemporaryDirectory() as temporary:
            report = runner.phase2_runtime_capability_preflight(
                service,
                Path(temporary),
                tracked_ck3_pid=pid,
                managed_restore_supervisor=True,
                focused_promotion_source_capture=True,
            )

        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(
            report["scope"],
            "focused_promotion_source_checkpoint_capture_mcp_capability_profile",
        )
        required = set(report["required_bridge_capabilities"].values())
        self.assertNotIn(
            runner.QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
            required,
        )
        self.assertIn("game.command.select-event-option-N", required)
        self.assertIn("game.command.pause-map", required)
        self.assertIn(
            runner.QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
            required,
        )
        self.assertIn(
            runner.ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
            required,
        )
        self.assertEqual(
            set(report["required_action_steps"].values()),
            {
                "save-checkpoint",
                "pause-map",
                "resume-map",
                "set-speed-1",
                "set-speed-5",
            },
        )

    def test_current_event_capability_absence_is_typed_red(self) -> None:
        pid = 361148
        capabilities = self._capabilities(pid)
        capabilities["bridge_capabilities"].remove(
            runner.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
        )
        service = types.SimpleNamespace(capabilities=lambda: capabilities)
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with self.assertRaisesRegex(
                runner.acceptance.RunnerError, "current_event_context"
            ):
                runner.phase2_runtime_capability_preflight(
                    service,
                    artifacts,
                    tracked_ck3_pid=pid,
                    managed_restore_supervisor=True,
                    focused_promotion_source_capture=True,
                )
            persisted = (artifacts / "02_phase2_mcp_capabilities.json").read_text(
                encoding="utf-8"
            )
        self.assertIn('"result": "RED"', persisted)

    def test_resume_rebinds_a_pre_submission_heartbeat_without_restart(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.revision = 118
                self.attempted_revisions: list[int] = []

            def snapshot(self) -> dict[str, object]:
                return {
                    "map_ready": True,
                    "revision": self.revision,
                    "date_raw": 53150352,
                    "played_character": {"character_id": 29037},
                    "diagnostics": {"connection_generation": 9},
                    "paused": True,
                    "speed": 5,
                }

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.assert_step(step)
                self.attempted_revisions.append(expected_revision)
                if len(self.attempted_revisions) == 1:
                    self.revision += 1
                    raise production.PreSubmissionRevisionMismatchError(
                        "native gameplay revision mismatch: expected 118, current 119"
                    )
                return {"accepted": True, "status": "submitted"}

            @staticmethod
            def assert_step(step: str) -> None:
                if step != "resume-map":
                    raise AssertionError(f"unexpected step: {step}")

        service = Service()
        audit: list[dict[str, object]] = []
        result = production._resume_map_from_latest_binding(
            service,
            player=29037,
            connection_generation=9,
            rebind_audit=audit,
        )

        self.assertEqual(result, {"accepted": True, "status": "submitted"})
        self.assertEqual(service.attempted_revisions, [118, 119])
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["stale_revision"], 118)
        self.assertFalse(audit[0]["request_submitted"])

    def test_zg361_6_modal_wait_controls_only_the_same_pid_and_event(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.revision = 20
                self.speed = 1
                self.paused = True
                self.pid = 361006
                self.steps: list[str] = []

            def snapshot(self) -> dict[str, object]:
                return {
                    "map_ready": True,
                    "snapshot_id": f"snapshot-{self.revision}",
                    "revision": self.revision,
                    "native_revision": self.revision,
                    "date_raw": 53159136,
                    "played_character": {"character_id": 29037},
                    "diagnostics": {
                        "connection_generation": 9,
                        "bridge_pid": self.pid,
                    },
                    "paused": self.paused,
                    "speed": self.speed,
                    "active_event": {"instance_id": 70, "option_count": 4},
                }

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.assertEqual(expected_revision, self.revision)
                self.steps.append(step)
                self.revision += 1
                if step == "set-speed-5":
                    self.speed = 5
                elif step == "resume-map":
                    self.paused = False
                return {"accepted": True, "status": "submitted"}

            @staticmethod
            def assertEqual(actual: object, expected: object) -> None:
                if actual != expected:
                    raise AssertionError((actual, expected))

        service = Service()
        audit: list[dict[str, object]] = []
        production._retained_modal_map_control(
            service,
            step="set-speed-5",
            player=29037,
            connection_generation=9,
            bridge_pid=361006,
            event_instance_id=70,
            rebind_audit=audit,
        )
        production._retained_modal_map_control(
            service,
            step="resume-map",
            player=29037,
            connection_generation=9,
            bridge_pid=361006,
            event_instance_id=70,
            rebind_audit=audit,
        )
        self.assertEqual(service.steps, ["set-speed-5", "resume-map"])
        service.pid += 1
        with self.assertRaisesRegex(
            production.PromotionProductionEntryError, "PID/event identity"
        ):
            production._retained_modal_map_control(
                service,
                step="set-speed-5",
                player=29037,
                connection_generation=9,
                bridge_pid=361006,
                event_instance_id=70,
                rebind_audit=audit,
            )

    def test_zg361_6_never_falls_back_when_modal_cannot_advance(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.revision = 20
                self.speed = 1
                self.paused = True
                self.steps: list[str] = []
                self.selections: list[int] = []

            def snapshot(self) -> dict[str, object]:
                return {
                    "map_ready": True,
                    "snapshot_id": f"snapshot-{self.revision}",
                    "revision": self.revision,
                    "native_revision": self.revision,
                    "date_raw": 53159136,
                    "played_character": {"character_id": 29037},
                    "diagnostics": {
                        "connection_generation": 9,
                        "bridge_pid": 361006,
                    },
                    "paused": self.paused,
                    "speed": self.speed,
                    "active_event": {"instance_id": 70, "option_count": 4},
                }

            def query_zhongguo_promotion_source_progress_v1(
                self, request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                widgets = [
                    {"effective_visible": {"status": "available", "value": False}}
                    for _ in range(5)
                ]
                widgets[3]["effective_visible"]["value"] = True
                return {
                    "status": "available",
                    "query_sequence": 1,
                    "zhongguo_promotion_source_progress": {"widgets": widgets},
                }

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.steps.append(step)
                self.revision += 1
                if step == "set-speed-5":
                    self.speed = 5
                elif step == "resume-map":
                    self.paused = False
                return {"accepted": True, "status": "submitted"}

            def select_event_option(
                self, option_number: int, *, event_instance_id: int,
                expected_revision: int,
            ) -> dict[str, object]:
                self.selections.append(option_number)
                raise AssertionError("random appeal option must never be selected")

        query = {
            "current_event_window_context": {
                "options": [
                    {"native_option_index": 0, "shown": True, "enabled": True},
                    {"native_option_index": 2, "shown": True, "enabled": True},
                ]
            }
        }
        service = Service()
        with (
            mock.patch.object(
                production,
                "_event_definition",
                return_value=("zg361.6", query),
            ),
            mock.patch.object(
                production,
                "_known_interrupt_checks",
                return_value={"identity": True},
            ),
            mock.patch.object(
                production,
                "ZG361_6_MODAL_ADVANCE_TIMEOUT_SECONDS",
                0.0,
            ),
        ):
            with self.assertRaisesRegex(
                production.PromotionProductionEntryError,
                "native modal cannot advance at speed 5",
            ):
                production.enter_promotion_source_checkpoint_v1(
                    service,
                    timeout_seconds=1.0,
                    poll_interval_seconds=0.0,
                    clock=lambda: 0.0,
                    sleeper=lambda _seconds: None,
                )
        self.assertEqual(service.steps, ["set-speed-5", "resume-map"])
        self.assertEqual(service.selections, [])

    def test_product_timeline_bound_covers_two_cycles_from_canonical_seed(self) -> None:
        reconnect_date = production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW + 500 * 24
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.6"],
            starting_date=production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
        )
        self.assertEqual(production.PRODUCT_CYCLE_OPPORTUNITIES, 2)
        self.assertEqual(production.POST_PUBLICATION_OBSERVATION_DAYS, 1100)
        self.assertEqual(production.MAX_ADVANCE_DAYS, 1900)
        self.assertEqual(
            contract["date_raw_range"],
            (
                production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
                + production.MAX_ADVANCE_DAYS * production.HOURS_PER_DAY,
            ),
        )
        self.assertNotEqual(contract["date_raw_range"][0], reconnect_date)

        # R116's second player B1 became visible at D+525.  The canonical
        # deadline covers that complete authored cycle without deriving any
        # new budget from reconnect_date.
        r116_second_cycle_active_date = 53159616
        self.assertGreaterEqual(
            contract["date_raw_range"][1],
            r116_second_cycle_active_date
            + production.B1_AUTHORED_ADVANCE_DAYS
            * production.HOURS_PER_DAY,
        )

        # R182 reached L stage 4 at this exact frame.  Its authored D+365
        # settlement fell 34 days beyond the former D+1100 cap.  The new cap
        # covers that deadline and the later AF D+365 + eleven D+30 cadence
        # critical path, with a finite 60-day event/pump margin.
        r182_l_stage4_open_date = 53165472
        fixed_post_stage_tail_days = 365 + 365 + 11 * 30 + 60
        self.assertGreaterEqual(
            contract["date_raw_range"][1],
            r182_l_stage4_open_date
            + fixed_post_stage_tail_days * production.HOURS_PER_DAY,
        )

        service = SimpleNamespace(snapshot=lambda: {
            "map_ready": True,
            "revision": 1,
            "date_raw": contract["date_raw_range"][1] + 1,
            "played_character": {"character_id": 29037},
            "diagnostics": {"connection_generation": 9},
            "paused": True,
            "speed": 5,
        })
        with self.assertRaisesRegex(
            production.PromotionProductionEntryError,
            "before this retained-client reconnect",
        ):
            production.enter_promotion_source_checkpoint_v1(service)

    def test_runtime_product_error_preempts_absolute_timeline_bound(self) -> None:
        service = SimpleNamespace(snapshot=lambda: {
            "map_ready": True,
            "revision": 1,
            "date_raw": (
                production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
                + production.MAX_ADVANCE_DAYS * production.HOURS_PER_DAY
                + 1
            ),
            "played_character": {"character_id": 29037},
            "diagnostics": {"connection_generation": 9},
            "paused": True,
            "speed": 5,
        })

        with self.assertRaisesRegex(
            production.PromotionProductionEntryError,
            "product runtime diagnostic: .*zg361_b1_runtime",
        ):
            production.enter_promotion_source_checkpoint_v1(
                service,
                runtime_diagnostic_probe=lambda: (
                    "error.log: Script system error in zg361_b1_runtime"
                ),
            )

    def test_manager_recovery_rebinds_identity_without_weakening_shape(self) -> None:
        source = {
            "root_character_id": 29037,
            "character_scopes": {"owner": 29037, "subject": 56656},
            "optional_character_scopes": {"optional_subject": 16780004},
            "scope_types": {},
            "optional_scope_types": {},
            "unique_character_scope_excludes": {"subject": (29037, 32904)},
            "option_count": 3,
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        }
        rebound = production._manager_recovery_contract(
            source, player=32904,
        )
        self.assertEqual(rebound["root_character_id"], 32904)
        self.assertEqual(rebound["character_scopes"], {"owner": 32904})
        self.assertEqual(rebound["scope_types"], {"subject": "character"})
        self.assertEqual(
            rebound["optional_scope_types"],
            {"optional_subject": "character"},
        )
        self.assertEqual(
            rebound["unique_character_scope_excludes"]["subject"],
            (32904, 32904),
        )
        self.assertEqual(rebound["option_count"], 3)
        self.assertEqual(rebound["selected_option_number"], 2)

        jingcha = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.40"],
            player=32904,
            event_key="zg361.40",
        )
        self.assertEqual(jingcha["root_character_id"], 32904)
        self.assertEqual(
            jingcha["date_policy"], "manager-recovery-product-window"
        )
        self.assertNotIn("date_raw_anchor", jingcha)
        self.assertNotIn("date_period_hours", jingcha)

        batch = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361pp.9100"],
            player=32904,
            event_key="zg361pp.9100",
        )
        self.assertEqual(batch["selected_option_number"], 1)
        self.assertEqual(batch["selected_native_option_index"], 0)

        completion = production._manager_recovery_pp_contract(
            "zg361pp.9001", player=32904, starting_date=53147016,
        )
        self.assertIsNotNone(completion)
        assert completion is not None
        self.assertEqual(completion["root_character_id"], 32904)
        self.assertEqual(completion["option_count"], 1)
        self.assertEqual(
            completion["scope_types"],
            {"zg361_pp_completion_subject": "character"},
        )
        self.assertIsNone(
            production._manager_recovery_pp_contract(
                "zg361pp.9100", player=32904, starting_date=53147016,
            )
        )

    def test_movement_petition_interrupt_uses_terminal_refusal(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def generic_scope(name: str, type_key: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": type_key,
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "generic_scope_payload_identity_not_closed",
                    },
                },
            }

        event_key = "tgp_decision_events.0101"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract, starting_date=53154120,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 18,
            "date_raw": 53156928,
            "root_scope": character_scope("root", 32904)["scope"],
            "saved_scopes": [
                character_scope("petitioner", 28664),
                generic_scope("actors_movement", "situation_participant_group"),
                character_scope("hegemon", 32904),
                character_scope("petition_recipient", 32904),
                generic_scope("province_metropolitan", "boolean"),
                character_scope("other_movement_member", 27181),
                character_scope("province_change_recipient", 27181),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53156928, "active_event": {"option_count": 3}},
            event={"event_instance_id": 18},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(contract["max_occurrences"], 2)

        for province_scope in (
            "province_metropolitan",
            "province_industrial",
            "province_military",
            "province_protectorate",
        ):
            with self.subTest(province_scope=province_scope):
                province_change = copy.deepcopy(context)
                province_change["saved_scopes"][4] = generic_scope(
                    province_scope, "boolean"
                )
                province_checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53156928,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 18},
                    context=province_change,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(province_checks.values()), province_checks)

        house_and_other = copy.deepcopy(context)
        house_and_other["saved_scopes"].insert(
            -1, character_scope("house_movement_member", 27183)
        )
        house_and_other_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53158008, "active_event": {"option_count": 3}},
            event={"event_instance_id": 20},
            context={
                **house_and_other,
                "current_event_instance_id": 20,
                "date_raw": 53158008,
            },
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(house_and_other_checks.values()), house_and_other_checks)

        unrelated_recipient = copy.deepcopy(house_and_other)
        unrelated_recipient["saved_scopes"][-1] = character_scope(
            "province_change_recipient", 27199
        )
        unrelated_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53158008, "active_event": {"option_count": 3}},
            event={"event_instance_id": 20},
            context={
                **unrelated_recipient,
                "current_event_instance_id": 20,
                "date_raw": 53158008,
            },
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            unrelated_checks["scope:province_change_recipient:matches_any"]
        )

        inherited = copy.deepcopy(context)
        inherited["saved_scopes"].insert(
            -1, character_scope("house_movement_member", 27183)
        )
        inherited["saved_scopes"].insert(
            -1, character_scope("disciple_movement_member", 27184)
        )
        inherited["saved_scopes"][-1] = character_scope(
            "province_change_recipient", 27183
        )
        inherited_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53158008, "active_event": {"option_count": 3}},
            event={"event_instance_id": 20},
            context={
                **inherited,
                "current_event_instance_id": 20,
                "date_raw": 53158008,
            },
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(inherited_checks.values()), inherited_checks)

        drifted_province = copy.deepcopy(context)
        drifted_province["saved_scopes"][4] = generic_scope(
            "province_unknown", "boolean"
        )
        drifted_province_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53156928, "active_event": {"option_count": 3}},
            event={"event_instance_id": 18},
            context=drifted_province,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drifted_province_checks["saved_scope_names_exact"])

        for direction_scope in (
            "increase_law",
            "decrease_law",
            "increase_army_law",
            "decrease_army_law",
        ):
            with self.subTest(direction_scope=direction_scope):
                law_change = {
                    **context,
                    "current_event_instance_id": 21,
                    "date_raw": 53156928,
                    "saved_scopes": [
                        character_scope("petitioner", 28664),
                        generic_scope(
                            "actors_movement", "situation_participant_group"
                        ),
                        character_scope("hegemon", 32904),
                        character_scope("petition_recipient", 32904),
                        generic_scope(direction_scope, "boolean"),
                    ],
                }
                law_change_checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53156928,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 21},
                    context=law_change,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(
                    all(law_change_checks.values()), law_change_checks
                )

    def test_administrative_confirmation_interrupt_uses_terminal_refusal(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        event_key = "ep3_decisions_event.2001"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 19,
            "date_raw": 53157888,
            "root_scope": character_scope("root", 32904)["scope"],
            "saved_scopes": [
                character_scope("confirmation_vassal", 28667),
                character_scope("confirmation_liege", 32904),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53157888, "active_event": {"option_count": 2}},
            event={"event_instance_id": 19},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_treasury_budget_interrupt_keeps_existing_allocation(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        event_key = "tgp_china_ministry.0100"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract, starting_date=53158008,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 21,
            "date_raw": 53163168,
            "root_scope": character_scope("root", 32904)["scope"],
            "saved_scopes": [
                character_scope("treasury_ruler", 32904),
                character_scope("steward", 29346),
                character_scope("salary_budget", 32904),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53163168, "active_event": {"option_count": 3}},
            event={"event_instance_id": 21},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_imperial_debate_interrupt_confirms_calculated_winner(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None,
        ) -> dict[str, object]:
            identity: dict[str, object]
            if character_id is None:
                identity = {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                }
            else:
                identity = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": type_key,
                    "typed_identity": identity,
                },
            }

        event_key = "debate_event.5110"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract, starting_date=53163168,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 23,
            "date_raw": 53163240,
            "root_scope": scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                scope("activity", "activity"),
                scope("host", "character", 29752),
                scope("province", "province"),
                scope("debate_opponent", "character", 29752),
                scope("debate_contender", "character", 29752),
                scope("debate_loser", "character", 29752),
                scope("debate_winner", "character", 29628),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53163240, "active_event": {"option_count": 2}},
            event={"event_instance_id": 23},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        host_wins = copy.deepcopy(context)
        host_wins["current_event_instance_id"] = 66
        host_wins["date_raw"] = 53166768
        host_wins["saved_scopes"] = [
            scope("activity", "activity"),
            scope("host", "character", 29501),
            scope("province", "province"),
            scope("debate_opponent", "character", 29501),
            scope("debate_contender", "character", 29501),
            scope("debate_loser", "character", 28667),
            scope("debate_winner", "character", 29501),
        ]
        host_wins_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53166768,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 66},
            context=host_wins,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(host_wins_checks.values()), host_wins_checks)
        self.assertTrue(host_wins_checks["scope:host:matches_any"])
        self.assertTrue(host_wins_checks["scope:debate_winner:differs_from"])
        self.assertNotIn(
            "scope:debate_loser:matches_any", host_wins_checks,
        )

        unexpected = copy.deepcopy(context)
        unexpected["current_event_instance_id"] = 64
        unexpected["date_raw"] = 53166672
        unexpected["saved_scopes"] = [
            scope("activity", "activity"),
            scope("host", "character", 29501),
            scope("province", "province"),
            scope("debate_opponent", "character", 29501),
            scope("debate_contender", "character", 29501),
            scope("debate_winner", "character", 29501),
            scope("debate_loser", "character", 29628),
            scope("debate_unexpected_win", "character", 29501),
        ]
        unexpected_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53166672, "active_event": {"option_count": 2}},
            event={"event_instance_id": 64},
            context=unexpected,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(unexpected_checks.values()), unexpected_checks)

        drifted_unexpected = copy.deepcopy(unexpected)
        drifted_unexpected["saved_scopes"][-1] = scope(
            "debate_unexpected_win", "character", 29628
        )
        drifted_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53166672, "active_event": {"option_count": 2}},
            event={"event_instance_id": 64},
            context=drifted_unexpected,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drifted_checks["scope:debate_unexpected_win:matches_any"]
        )

    def test_befriend_success_interrupt_uses_gentle_rejection(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None,
        ) -> dict[str, object]:
            identity: dict[str, object]
            if character_id is None:
                identity = {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                }
            else:
                identity = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": type_key,
                    "typed_identity": identity,
                },
            }

        event_key = "befriend_outcome.0002"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract, starting_date=53163240,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 25,
            "date_raw": 53164584,
            "root_scope": scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                scope("scheme", "scheme"),
                scope("owner", "character", 31210),
                scope("artifact", "artifact"),
                scope("target", "character", 32904),
                scope("scheme_successful", "flag"),
            ],
            "options": [
                {
                    "rendered_index": rendered_index,
                    "native_option_index": native_index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered_index, native_index in enumerate((0, 2, 3))
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53164584, "active_event": {"option_count": 4}},
            event={"event_instance_id": 25},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

    def test_adultery_suspicion_interrupt_does_nothing(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        event_key = "adultery.0002"
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            player=32904,
            event_key=event_key,
        )
        contract = production._timeline_contract_for_window(
            contract, starting_date=53164584,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 26,
            "date_raw": 53169888,
            "root_scope": character_scope("root", 32904)["scope"],
            "saved_scopes": [
                character_scope("spouse", 32904),
                character_scope("lover_spouse", 32797),
            ],
            "options": [
                {
                    "rendered_index": rendered_index,
                    "native_option_index": native_index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered_index, native_index in enumerate((0, 2, 3))
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53169888, "active_event": {"option_count": 4}},
            event={"event_instance_id": 26},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

    def test_active_cycle_recovery_stops_at_first_clean_review_boundary(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.date_raw = production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
                self.paused = True
                self.clean = False
                self.steps: list[str] = []

            def snapshot(self) -> dict[str, object]:
                return {
                    "map_ready": True,
                    "revision": 7,
                    "date_raw": self.date_raw,
                    "played_character": {"character_id": 32904},
                    "diagnostics": {"connection_generation": 9},
                    "paused": self.paused,
                    "speed": 5,
                }

            def query_zhongguo_promotion_source_progress_v1(
                self, request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                widgets = [
                    {"effective_visible": {"status": "available", "value": False}}
                    for _ in range(5)
                ]
                if self.clean:
                    widgets[1]["effective_visible"]["value"] = True
                else:
                    widgets[2]["effective_visible"]["value"] = True
                return {
                    "status": "available",
                    "query_sequence": 1,
                    "zhongguo_promotion_source_progress": {"widgets": widgets},
                }

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.steps.append(step)
                if step == "resume-map":
                    self.paused = False
                elif step == "pause-map":
                    self.paused = True
                return {"accepted": True, "status": "submitted"}

        service = Service()
        elapsed = [0.0]

        def sleeper(seconds: float) -> None:
            elapsed[0] += seconds
            if not service.paused:
                service.date_raw += 24
                service.clean = True

        result = production.enter_promotion_source_checkpoint_v1(
            service,
            timeout_seconds=5.0,
            poll_interval_seconds=0.05,
            stop_at_clean_review_boundary=True,
            clock=lambda: elapsed[0],
            sleeper=sleeper,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["readiness"], "paused-clean-review-boundary")
        self.assertEqual(
            result["clean_review_boundary"],
            {
                "revision": 7,
                "date_raw": production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW + 24,
                "review_now_eligible": True,
                "b1_active": False,
                "central_active": False,
                "pp_active": False,
            },
        )
        self.assertEqual(service.steps, ["resume-map", "pause-map"])

    def test_product_entry_uses_speed_five_and_pauses_before_progress_query(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.speed = 1
                # Retained production sessions hand over while speed 5 is
                # normally still running. Exercise the first pause heartbeat,
                # not only the later timeline polling pause.
                self.paused = False
                self.event_pending = False
                self.speed_transition_pending = False
                self.pause_transition_pending = False
                self.date_raw = 53147016
                self.running_sleeps = 0
                self.steps: list[str] = []
                self.progress_queries: list[str] = []
                self.progress_binding_rejected_once = False

            def snapshot(self) -> dict[str, object]:
                snapshot: dict[str, object] = {
                    "map_ready": True,
                    "revision": 7,
                    "date_raw": self.date_raw,
                    "played_character": {"character_id": 29037},
                    "diagnostics": {"connection_generation": 9},
                    "paused": self.paused,
                    "speed": self.speed,
                }
                if self.event_pending:
                    snapshot["active_event"] = {"option_count": 1}
                return snapshot

            def query_zhongguo_promotion_source_progress_v1(
                self, request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.progress_queries.append(request_nonce)
                if not self.paused:
                    raise AssertionError("progress polling must use a paused frame")
                if (
                    request_nonce.startswith("promo.entry.poll.")
                    and self.speed_transition_pending
                ):
                    raise AssertionError(
                        "progress polling must not bisect a paused speed transition"
                    )
                if (
                    self.pause_transition_pending
                ):
                    raise AssertionError(
                        "progress polling must wait for the paused heartbeat"
                    )
                if (
                    request_nonce.startswith("promo.entry.poll.")
                    and not self.progress_binding_rejected_once
                ):
                    self.progress_binding_rejected_once = True
                    raise production.BridgeUnavailableError(
                        "native gameplay step failed: ZhongGuo promotion "
                        "source progress binding changed or is not ready"
                    )
                widgets = [
                    {"effective_visible": {"status": "available", "value": False}}
                    for _ in range(5)
                ]
                widgets[2]["effective_visible"]["value"] = True
                return {
                    "status": "available",
                    "query_sequence": 1,
                    "zhongguo_promotion_source_progress": {"widgets": widgets},
                }

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.steps.append(step)
                if step == "set-speed-5":
                    self.speed = 5
                    self.speed_transition_pending = True
                elif step == "resume-map":
                    self.paused = False
                    self.speed_transition_pending = False
                elif step == "pause-map":
                    self.paused = True
                    self.pause_transition_pending = True
                    self.event_pending = False
                return {"accepted": True, "status": "submitted"}

        ticks = iter((0.0, 0.0, 0.0, 0.0, 0.0, 2.0))
        service = Service()
        evidence: dict[str, object] = {}

        def settle(_seconds: float) -> None:
            if service.paused:
                service.pause_transition_pending = False
            else:
                service.running_sleeps += 1
                # Leave the first running poll on the same native date. The
                # runner must keep running instead of immediately pausing it.
                if service.running_sleeps % 2 == 0:
                    service.date_raw += 24

        with self.assertRaisesRegex(
            production.PromotionProductionEntryError,
            "timed out before paused real zg361pp.147",
        ):
            production.enter_promotion_source_checkpoint_v1(
                service,
                timeout_seconds=1.0,
                poll_interval_seconds=0.05,
                clock=lambda: next(ticks),
                sleeper=settle,
                evidence_out=evidence,
            )
        self.assertEqual(
            service.steps,
            [
                "pause-map",
                "set-speed-5",
                "resume-map",
                "pause-map",
                "resume-map",
            ],
        )
        self.assertEqual(service.progress_queries[0], "promo.entry.before")
        self.assertEqual(len(service.progress_queries), 3)
        self.assertEqual(service.progress_queries[1], "promo.entry.poll.1")
        self.assertEqual(service.progress_queries[2], "promo.entry.poll.1")
        self.assertEqual(len(evidence["progress_query_rebinds"]), 1)
        self.assertFalse(
            evidence["progress_query_rebinds"][0]["state_mutation_submitted"]
        )

    def test_product_progress_observation_rejects_unavailable_widget(self) -> None:
        widgets = [
            {"effective_visible": {"status": "available", "value": False}}
            for _ in range(5)
        ]
        query = {
            "status": "available",
            "zhongguo_promotion_source_progress": {"widgets": widgets},
        }
        observed = production._compact_progress_observation(
            query, date_raw=53147040, revision=8,
        )
        self.assertEqual(
            observed,
            {
                "revision": 8,
                "date_raw": 53147040,
                "review_now_eligible": False,
                "b1_active": False,
                "central_active": False,
                "pp_active": False,
            },
        )

        widgets[3]["effective_visible"] = {
            "status": "unavailable",
            "value": None,
        }
        with self.assertRaisesRegex(
            production.PromotionProductionEntryError,
            "unavailable widget",
        ):
            production._compact_progress_observation(
                query, date_raw=53147040, revision=8,
            )

    def test_post_interrupt_seed_invalid_requires_no_live_or_review_witness(self) -> None:
        inactive = {
            "review_now_eligible": False,
            "b1_active": False,
            "central_active": False,
            "pp_active": False,
        }
        self.assertTrue(production._post_interrupt_seed_is_invalid(inactive))
        self.assertFalse(
            production._post_interrupt_seed_is_invalid(
                inactive, stop_at_clean_review_boundary=True
            )
        )
        for witness in (
            "review_now_eligible", "b1_active", "central_active", "pp_active"
        ):
            viable = dict(inactive)
            viable[witness] = True
            self.assertFalse(
                production._post_interrupt_seed_is_invalid(viable), witness
            )

    def test_capture_mode_is_mutually_exclusive_with_other_runtime_modes(self) -> None:
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError, "mutually exclusive"
        ):
            runner.main(
                preflight_only=True,
                loader_smoke=True,
                phase2_promotion_source_capture_live=True,
            )

    def test_b1_self_review_binds_consumed_ticket_and_only_names_outer_bank_scopes(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def value_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": "value"},
            }

        def inherited_outer_scope(name: str) -> dict[str, object]:
            # R71 observed that the four bank-ticket names can survive into
            # .200 after their payload bindings cease to describe the active
            # self-review. The event source does not consume these fields.
            return {
                "name": name,
                "scope": {"status": "unavailable", "type_key": "unknown"},
            }

        manager = 36354
        names = (
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
            "zg361_b1_self_ticket_owner",
            "zg361_b1_self_ticket_subject",
            "zg361_b1_self_ticket_cycle",
            "zg361_b1_self_ticket_case",
            "zg361_b1_self_ticket_state",
        )
        character_names = {
            "zg361_b1_ticket_owner": manager,
            "zg361_b1_self_ticket_owner": manager,
            "zg361_b1_self_ticket_subject": 29037,
        }
        inherited_outer_names = {
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
        }
        scopes = [
            character_scope(name, character_names[name])
            if name in character_names
            else inherited_outer_scope(name)
            if name in inherited_outer_names
            else value_scope(name)
            for name in names
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361b1.200",
            "current_event_instance_id": 18,
            "date_raw": 53156232,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": scopes,
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        snapshot = {"date_raw": 53156232, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 18}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["zg361b1.200"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361b1.200",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        extra = copy.deepcopy(context)
        extra["saved_scopes"].append(value_scope("unrelated_scope"))
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra,
            event_key="zg361b1.200",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_names_exact"])

        wrong_alias = copy.deepcopy(context)
        wrong_alias["saved_scopes"][4] = character_scope(
            "zg361_b1_ticket_owner", 36355
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_alias,
            event_key="zg361b1.200",
            contract=contract,
        )
        self.assertFalse(checks["scope:zg361_b1_ticket_owner:matches_any"])

        missing_outer_name = copy.deepcopy(context)
        del missing_outer_name["saved_scopes"][0]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=missing_outer_name,
            event_key="zg361b1.200",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_b1_shadow_accept_binds_consumed_ticket_and_exact_inheritance(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def value_scope(name: str, *, type_key: str = "value") -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": type_key},
            }

        manager = 36354
        names = (
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
            "zg361_b1_self_ticket_owner",
            "zg361_b1_self_ticket_subject",
            "zg361_b1_self_ticket_cycle",
            "zg361_b1_self_ticket_case",
            "zg361_b1_self_ticket_state",
            "zg361_b1_shadow_ticket_owner",
            "zg361_b1_shadow_ticket_subject",
            "zg361_b1_shadow_ticket_cycle",
            "zg361_b1_shadow_ticket_case",
            "zg361_b1_shadow_ticket_state",
        )
        character_names = {
            "zg361_b1_bank_ticket_owner": manager,
            "zg361_b1_ticket_owner": manager,
            "zg361_b1_self_ticket_owner": manager,
            "zg361_b1_self_ticket_subject": 29037,
            "zg361_b1_shadow_ticket_owner": manager,
            "zg361_b1_shadow_ticket_subject": 29037,
        }
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361b1.201",
            "current_event_instance_id": 20,
            "date_raw": 53157672,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope(name, character_names[name])
                if name in character_names
                else value_scope(name)
                for name in names
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53157672, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 20}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361b1.201"],
            starting_date=53147016,
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361b1.201",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_owner = copy.deepcopy(context)
        wrong_owner["saved_scopes"][13] = character_scope(
            "zg361_b1_shadow_ticket_owner", 36355
        )
        checks = checks_for(wrong_owner)
        self.assertFalse(checks["scope:zg361_b1_shadow_ticket_owner:matches_any"])

        wrong_subject = copy.deepcopy(context)
        wrong_subject["saved_scopes"][14] = character_scope(
            "zg361_b1_shadow_ticket_subject", 29038
        )
        checks = checks_for(wrong_subject)
        self.assertFalse(checks["scope:zg361_b1_shadow_ticket_subject"])

        wrong_value_type = copy.deepcopy(context)
        wrong_value_type["saved_scopes"][15] = value_scope(
            "zg361_b1_shadow_ticket_cycle", type_key="boolean"
        )
        checks = checks_for(wrong_value_type)
        self.assertFalse(checks["scope:zg361_b1_shadow_ticket_cycle:type"])

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(value_scope("unrelated_scope"))
        checks = checks_for(extra_scope)
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_b1_publication_notice_excludes_completed_event_local_tickets(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def value_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": "value"},
            }

        manager = 36354
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361b1.126"],
            starting_date=53147016,
        )
        first_cycle_names, later_cycle_names = contract["saved_scope_name_sets"]
        character_names = {
            "zg361_b1_bank_ticket_owner": 32904,
            "zg361_b1_ticket_owner": manager,
            "zg361_b1_self_ticket_owner": manager,
            "zg361_b1_self_ticket_subject": 29037,
            "zg361_b1_shadow_ticket_owner": manager,
            "zg361_b1_shadow_ticket_subject": 29037,
            "zg361_b1_oversight_ticket_owner": manager,
            "zg361_b1_pending_watch_owner": manager,
            "zg361_b1_local_publish_notice_owner": manager,
            "zg361_b1_local_publish_notice_subject": 29037,
        }

        def context_for(names: tuple[str, ...]) -> dict[str, object]:
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": "zg361b1.126",
                "current_event_instance_id": 20,
                "date_raw": 53155488,
                "root_scope": character_scope("root", 29037)["scope"],
                "saved_scopes": [
                    character_scope(name, character_names[name])
                    if name in character_names
                    else value_scope(name)
                    for name in names
                ],
                "options": [
                    {
                        "rendered_index": 0,
                        "native_option_index": 0,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                ],
            }

        context = context_for(first_cycle_names)
        snapshot = {"date_raw": 53155488, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 20}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361b1.126",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        later_cycle = context_for(later_cycle_names)
        checks = checks_for(later_cycle)
        self.assertTrue(all(checks.values()), checks)

        partial_later_cycle = copy.deepcopy(later_cycle)
        partial_later_cycle["saved_scopes"] = partial_later_cycle["saved_scopes"][:-1]
        checks = checks_for(partial_later_cycle)
        self.assertFalse(checks["saved_scope_names_exact"])

        wrong_manager = copy.deepcopy(context)
        wrong_manager["saved_scopes"][12] = character_scope(
            "zg361_b1_pending_watch_owner", 36355
        )
        checks = checks_for(wrong_manager)
        self.assertFalse(checks["scope:zg361_b1_pending_watch_owner:matches_any"])

    def test_annual_summary_accepts_all_exact_live_scope_sets(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def value_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": "value"},
            }

        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.1"],
            starting_date=53168304,
        )
        (
            first_cycle_names,
            later_cycle_names,
            extended_cycle_names,
            extended_later_cycle_names,
            retained_seed_pending_names,
            watchdog_recovery_names,
        ) = contract["saved_scope_name_sets"]
        character_names = {
            "zg361_b1_calibration_watchdog_owner": 29037,
            "zg361_b1_bank_ticket_owner": 32904,
            "zg361_b1_ticket_owner": 29037,
            "zg361_b1_oversight_ticket_owner": 29037,
            "zg361_b1_reopen_ticket_subject": 45214,
            "zg361_b1_reopen_ticket_owner": 29037,
            "zga_phase2_seed_player": 29037,
        }

        def context_for(names: tuple[str, ...]) -> dict[str, object]:
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": "zg361.1",
                "current_event_instance_id": 87,
                "date_raw": 53168304,
                "root_scope": character_scope("root", 29037)["scope"],
                "saved_scopes": [
                    character_scope(name, character_names[name])
                    if name in character_names
                    else value_scope(name)
                    for name in names
                ],
                "options": [
                    {
                        "rendered_index": 0,
                        "native_option_index": 0,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                ],
            }

        snapshot = {"date_raw": 53168304, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 87}

        def checks_for(names: tuple[str, ...]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=context_for(names),
                event_key="zg361.1",
                contract=contract,
            )

        first_cycle_checks = checks_for(first_cycle_names)
        self.assertTrue(all(first_cycle_checks.values()), first_cycle_checks)
        later_cycle_checks = checks_for(later_cycle_names)
        self.assertTrue(all(later_cycle_checks.values()), later_cycle_checks)
        extended_cycle_checks = checks_for(extended_cycle_names)
        self.assertTrue(all(extended_cycle_checks.values()), extended_cycle_checks)
        extended_later_cycle_checks = checks_for(extended_later_cycle_names)
        self.assertTrue(
            all(extended_later_cycle_checks.values()), extended_later_cycle_checks
        )
        retained_seed_pending_checks = checks_for(retained_seed_pending_names)
        self.assertTrue(
            all(retained_seed_pending_checks.values()), retained_seed_pending_checks
        )
        watchdog_recovery_checks = checks_for(watchdog_recovery_names)
        self.assertTrue(
            all(watchdog_recovery_checks.values()), watchdog_recovery_checks
        )
        self.assertIn(
            "scope:zg361_b1_calibration_watchdog_owner:optional",
            watchdog_recovery_checks,
        )
        self.assertIn(
            "scope:zg361_b1_calibration_watchdog_cycle:optional_type",
            watchdog_recovery_checks,
        )
        self.assertIn(
            "scope:zg361_b1_calibration_watchdog_case:optional_type",
            watchdog_recovery_checks,
        )
        self.assertNotIn(
            "scope:zg361_b1_bank_ticket_owner:unique_third_party",
            later_cycle_checks,
        )
        self.assertNotIn(
            "scope:zg361_b1_bank_ticket_owner:differs_from",
            later_cycle_checks,
        )
        self.assertNotIn(
            "scope:zg361_b1_bank_ticket_season:type",
            later_cycle_checks,
        )

        extra_names = extended_later_cycle_names + ("unrelated_scope",)
        extra_checks = checks_for(extra_names)
        self.assertFalse(extra_checks["saved_scope_names_exact"])

    def test_bonus_salary_matrix_accepts_funded_and_defer_only_options(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def option(rendered: int, native: int) -> dict[str, object]:
            return {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }

        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361ch.21"],
            starting_date=53156544,
        )
        base_context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361ch.21",
            "current_event_instance_id": 91,
            "date_raw": 53156544,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope("zg361_ch_d_event_owner", 29037),
                character_scope("zg361_ch_d_event_subject", 45214),
                {
                    "name": "zg361_ch_d_event_cycle",
                    "scope": {"status": "available", "type_key": "value"},
                },
                {
                    "name": "zg361_ch_d_event_case",
                    "scope": {"status": "available", "type_key": "value"},
                },
            ],
        }
        snapshot = {"date_raw": 53156544, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 91}

        for indices, selected_number, selected_native in (
            ((0, 1, 2), 1, 0),
            ((2,), 3, 2),
        ):
            with self.subTest(indices=indices):
                context = copy.deepcopy(base_context)
                context["options"] = [
                    option(rendered, native)
                    for rendered, native in enumerate(indices)
                ]
                checks = production._known_interrupt_checks(
                    snapshot=snapshot,
                    event=event,
                    context=context,
                    event_key="zg361ch.21",
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
                resolved = production._option_contract_for_context(
                    context["options"], contract
                )
                self.assertEqual(resolved["selected_option_number"], selected_number)
                self.assertEqual(
                    resolved["selected_native_option_index"], selected_native
                )

        unknown = copy.deepcopy(base_context)
        unknown["options"] = [option(0, 1), option(1, 2)]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=unknown,
            event_key="zg361ch.21",
            contract=contract,
        )
        self.assertFalse(checks["authored_options_exact"])

        for event_key in (
            "zg361ch.25",
            "zg361ch.101",
            "zg361ch.104",
            "zg361ch.112",
            "zg361ch.114",
            "zg361ch.119",
        ):
            candidate = production.KNOWN_TIMELINE_INTERRUPTS[event_key]
            with self.subTest(event_key=event_key, projection="funded"):
                resolved = production._option_contract_for_context(
                    [option(0, 0), option(1, 1), option(2, 2)], candidate
                )
                self.assertEqual(resolved["selected_option_number"], 1)
                self.assertEqual(resolved["selected_native_option_index"], 0)
            with self.subTest(event_key=event_key, projection="defer-only"):
                resolved = production._option_contract_for_context(
                    [option(0, 2)], candidate
                )
                self.assertEqual(resolved["selected_option_number"], 3)
                self.assertEqual(resolved["selected_native_option_index"], 2)

    def test_player_325_notice_binds_prompt_tuple_and_exact_inherited_names(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def value_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": "value"},
            }

        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.50"],
            starting_date=53147016,
        )
        first_cycle_names, later_cycle_names = contract["saved_scope_name_sets"]
        manager = 28598
        character_names = {
            "zg361_b1_bank_ticket_owner": 32904,
            "zg361_b1_ticket_owner": manager,
            "zg361_b1_self_ticket_owner": manager,
            "zg361_b1_self_ticket_subject": 29037,
            "zg361_b1_shadow_ticket_owner": manager,
            "zg361_b1_shadow_ticket_subject": 29037,
            "zg361_b1_oversight_ticket_owner": manager,
            "zg361_b1_pending_continue_owner": manager,
            "zg361_b1_pending_continue_subject": 32536,
            "zg361_b1_reopen_ticket_subject": 45172,
            "zg361_b1_reopen_ticket_owner": manager,
            "zg361_notice_prompt_owner": manager,
            "zg361_notice_prompt_subject": 29037,
            "zg361_reviewing_superior": manager,
        }
        def context_for(names: tuple[str, ...]) -> dict[str, object]:
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": "zg361.50",
                "current_event_instance_id": 42,
                "date_raw": 53156952,
                "root_scope": character_scope("root", 29037)["scope"],
                "saved_scopes": [
                    character_scope(name, character_names[name])
                    if name in character_names
                    else value_scope(name)
                    for name in names
                ],
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                    for index in range(3)
                ],
            }

        context = context_for(first_cycle_names)
        snapshot = {"date_raw": 53156952, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 42}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361.50",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        later_cycle = context_for(later_cycle_names)
        later_checks = checks_for(later_cycle)
        self.assertTrue(all(later_checks.values()), later_checks)
        self.assertNotIn(
            "scope:zg361_b1_bank_ticket_owner:unique_third_party",
            later_checks,
        )

        wrong_subject = copy.deepcopy(context)
        prompt_subject_index = first_cycle_names.index("zg361_notice_prompt_subject")
        wrong_subject["saved_scopes"][prompt_subject_index] = character_scope(
            "zg361_notice_prompt_subject", 29038
        )
        checks = checks_for(wrong_subject)
        self.assertFalse(checks["scope:zg361_notice_prompt_subject"])

        wrong_owner = copy.deepcopy(context)
        reviewer_index = first_cycle_names.index("zg361_reviewing_superior")
        wrong_owner["saved_scopes"][reviewer_index] = character_scope(
            "zg361_reviewing_superior", 28599
        )
        checks = checks_for(wrong_owner)
        self.assertFalse(checks["scope:zg361_reviewing_superior:matches_any"])

        extra_scope = copy.deepcopy(later_cycle)
        extra_scope["saved_scopes"].append(value_scope("unrelated_scope"))
        checks = checks_for(extra_scope)
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_player_325_reaction_uses_safe_option_without_scope_payload_claims(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def inherited_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": "unknown"},
            }

        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.4"],
            starting_date=53147016,
        )
        first_cycle_names, later_cycle_names = contract["saved_scope_name_sets"]

        def context_for(names: tuple[str, ...]) -> dict[str, object]:
            return {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": "zg361.4",
                "current_event_instance_id": 45,
                "date_raw": 53156976,
                "root_scope": character_scope("root", 29037)["scope"],
                "saved_scopes": [inherited_scope(name) for name in names],
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                    for index in range(4)
                ],
            }

        context = context_for(first_cycle_names)
        snapshot = {"date_raw": 53156976, "active_event": {"option_count": 4}}
        event = {"event_instance_id": 45}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361.4",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        later_checks = checks_for(context_for(later_cycle_names))
        self.assertTrue(all(later_checks.values()), later_checks)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(inherited_scope("unrelated_scope"))
        checks = checks_for(extra_scope)
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_player_elimination_appeal_binds_sparse_options_and_exact_names(self) -> None:
        def character_scope(character_id: int) -> dict[str, object]:
            return {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                },
            }

        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361.6"],
            starting_date=53147016,
        )
        names = contract["saved_scope_name_sets"][0]
        self_and_shadow_ticket_names = {
            f"zg361_b1_{ticket}_ticket_{field}"
            for ticket, fields in (
                ("self", ("owner", "subject", "cycle", "case", "state")),
                ("shadow", ("owner", "subject", "cycle", "case", "state")),
            )
            for field in fields
        }
        expired_bank_ticket_names = {
            f"zg361_b1_bank_ticket_{field}"
            for field in ("owner", "season", "case", "state")
        }
        self.assertEqual(len(names), 48)
        self.assertTrue(self_and_shadow_ticket_names.issubset(names))
        self.assertTrue(expired_bank_ticket_names.isdisjoint(names))
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361.6",
            "current_event_instance_id": 70,
            "date_raw": 53159136,
            "root_scope": character_scope(29037),
            "saved_scopes": [
                {
                    "name": name,
                    "scope": {"status": "available", "type_key": "unknown"},
                }
                for name in names
            ],
            "options": [
                {
                    "rendered_index": rendered_index,
                    "native_option_index": native_index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered_index, native_index in enumerate((0, 2))
            ],
        }
        snapshot = {"date_raw": 53159136, "active_event": {"option_count": 4}}
        event = {"event_instance_id": 70}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361.6",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertFalse(production._zg361_6_retain_option_ready({
            "current_event_window_context": context
        }))
        with self.assertRaisesRegex(
            production.PromotionProductionEntryError,
            "requires a deterministic option",
        ):
            production._drain_known_timeline_interrupt(
                SimpleNamespace(),
                snapshot=snapshot,
                event=event,
                query={"current_event_window_context": context},
                event_key="zg361.6",
                contract=contract,
                player=29037,
                connection_generation=9,
            )

        dense_options = copy.deepcopy(context)
        dense_options["options"][1]["native_option_index"] = 1
        dense_options["options"].append({
            "rendered_index": 2,
            "native_option_index": 2,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        })
        checks = checks_for(dense_options)
        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(production._zg361_6_retain_option_ready({
            "current_event_window_context": dense_options
        }))

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(
            {"name": "unrelated_scope", "scope": {"status": "available"}}
        )
        checks = checks_for(extra_scope)
        self.assertFalse(checks["saved_scope_names_exact"])

        stale_bank_shape = copy.deepcopy(context)
        stale_bank_shape["saved_scopes"] = [
            row
            for row in stale_bank_shape["saved_scopes"]
            if row["name"] not in self_and_shadow_ticket_names
        ] + [
            {"name": name, "scope": {"status": "available", "type_key": "unknown"}}
            for name in sorted(expired_bank_ticket_names)
        ]
        checks = checks_for(stale_bank_shape)
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_second_mechanism_card_uses_reference_charter_choice(self) -> None:
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361m.2"],
            starting_date=53159136,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361m.2",
            "current_event_instance_id": 88,
            "date_raw": 53168304,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53168304, "active_event": {"option_count": 3}},
            event={"event_instance_id": 88},
            context=context,
            event_key="zg361m.2",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_spymaster_no_find_accepts_only_source_proven_boolean_branch(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def boolean_scope(
            name: str, *, type_key: str = "boolean"
        ) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": type_key},
            }

        base_scopes = [
            character_scope("councillor", 27963),
            character_scope("councillor_liege", 29037),
            character_scope("target_character", 27051),
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "spymaster_task.0399",
            "current_event_instance_id": 18,
            "date_raw": 53152896,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": base_scopes + [boolean_scope("secrets_to_be_found")],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53152896, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 18}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["spymaster_task.0399"],
            starting_date=53147016,
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="spymaster_task.0399",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        alternative = copy.deepcopy(context)
        alternative["saved_scopes"][-1] = boolean_scope("no_secrets_here")
        checks = checks_for(alternative)
        self.assertTrue(all(checks.values()), checks)

        both = copy.deepcopy(context)
        both["saved_scopes"].append(boolean_scope("no_secrets_here"))
        checks = checks_for(both)
        self.assertFalse(checks["boolean_scope_names_exact"])
        self.assertFalse(checks["saved_scope_names_exact"])

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][-1] = boolean_scope(
            "secrets_to_be_found", type_key="value"
        )
        checks = checks_for(wrong_type)
        self.assertFalse(checks["boolean_scope_names_exact"])

        extra = copy.deepcopy(context)
        extra["saved_scopes"].append(boolean_scope("unrelated_scope"))
        checks = checks_for(extra)
        self.assertFalse(checks["saved_scope_names_exact"])

        out_of_window = copy.deepcopy(context)
        out_of_window["date_raw"] = (
            production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
            + (production.MAX_ADVANCE_DAYS + 1) * production.HOURS_PER_DAY
        )
        checks = checks_for(out_of_window)
        self.assertFalse(checks["context_date_raw"])

    def test_bp1_yearly_9006_binds_random_courtier_and_minimum_external_option(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "bp1_yearly.9006",
            "current_event_instance_id": 14,
            "date_raw": 53147520,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope("bp1_yearly_9006_sinful_courtier", 29068)
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53147520, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 14}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["bp1_yearly.9006"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="bp1_yearly.9006",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        player_as_courtier = copy.deepcopy(context)
        player_as_courtier["saved_scopes"] = [
            character_scope("bp1_yearly_9006_sinful_courtier", 29037)
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=player_as_courtier,
            event_key="bp1_yearly.9006",
            contract=contract,
        )
        self.assertFalse(
            checks["scope:bp1_yearly_9006_sinful_courtier:unique_third_party"]
        )

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(
            character_scope("unrelated_scope", 29069)
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra_scope,
            event_key="bp1_yearly.9006",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_count"])

    def test_ep3_governor_8080_binds_magistrate_and_punishment_option(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "ep3_governor_yearly.8080",
            "current_event_instance_id": 16,
            "date_raw": 53147520,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [character_scope("magistrate", 16780023)],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(4)
            ],
        }
        snapshot = {"date_raw": 53147520, "active_event": {"option_count": 4}}
        event = {"event_instance_id": 16}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[
            "ep3_governor_yearly.8080"
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="ep3_governor_yearly.8080",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        player_as_magistrate = copy.deepcopy(context)
        player_as_magistrate["saved_scopes"] = [
            character_scope("magistrate", 29037)
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=player_as_magistrate,
            event_key="ep3_governor_yearly.8080",
            contract=contract,
        )
        self.assertFalse(checks["scope:magistrate:unique_third_party"])

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(
            character_scope("unrelated_scope", 16780024)
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra_scope,
            event_key="ep3_governor_yearly.8080",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_count"])

    def test_yearly_1040_and_direct_disclosure_bind_r85_live_shape(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        base_scopes = [
            scope("suspicious", "character", 31647),
            scope("suspicious_type", "flag"),
            scope("surprise_type", "flag"),
        ]

        def checks_for(
            event_key: str,
            option_count: int,
            candidate_scopes: list[dict[str, object]],
        ) -> dict[str, bool]:
            contract = production._timeline_contract_for_window(
                production.KNOWN_TIMELINE_INTERRUPTS[event_key],
                starting_date=53147016,
            )
            context = {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "window_match_count": 1,
                "event_definition_key": event_key,
                "current_event_instance_id": 14,
                "date_raw": 53147520,
                "root_scope": scope("root", "character", 29037)["scope"],
                "saved_scopes": candidate_scopes,
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                        "fallback": False,
                        "cancel": False,
                    }
                    for index in range(option_count)
                ],
            }
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53147520,
                    "active_event": {"option_count": option_count},
                },
                event={"event_instance_id": 14},
                context=context,
                event_key=event_key,
                contract=contract,
            )

        opening = checks_for("yearly.1040", 3, copy.deepcopy(base_scopes))
        self.assertTrue(all(opening.values()), opening)
        opening_contract = production.KNOWN_TIMELINE_INTERRUPTS["yearly.1040"]
        self.assertEqual(opening_contract["selected_option_number"], 1)
        self.assertEqual(opening_contract["selected_native_option_index"], 0)

        disclosure = checks_for("yearly.1041", 1, copy.deepcopy(base_scopes))
        self.assertTrue(all(disclosure.values()), disclosure)

        player_target = copy.deepcopy(base_scopes)
        player_target[0] = scope("suspicious", "character", 29037)
        self.assertFalse(
            checks_for("yearly.1040", 3, player_target)[
                "scope:suspicious:unique_third_party"
            ]
        )

        wrong_type = copy.deepcopy(base_scopes)
        wrong_type[-1] = scope("surprise_type", "value")
        self.assertFalse(
            checks_for("yearly.1040", 3, wrong_type)[
                "scope:surprise_type:type"
            ]
        )

        extra = copy.deepcopy(base_scopes)
        extra.append(scope("unrelated", "flag"))
        self.assertFalse(
            checks_for("yearly.1040", 3, extra)["saved_scope_count"]
        )

    def test_tgp_merchant_dispute_binds_dynamic_distinct_characters(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        event_key = "tgp_china_yearly.0015"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 14,
            "date_raw": 53147520,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope("market_vendor", 16780100),
                character_scope("traveling_merchant", 16780101),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((0, 1, 2))
            ],
        }
        snapshot = {"date_raw": 53147520, "active_event": {"option_count": 4}}
        event = {"event_instance_id": 14}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        player_vendor = copy.deepcopy(context)
        player_vendor["saved_scopes"][0] = character_scope(
            "market_vendor", 29037
        )
        self.assertFalse(
            checks_for(player_vendor)["scope:market_vendor:unique_third_party"]
        )

        duplicate = copy.deepcopy(context)
        duplicate["saved_scopes"][1] = character_scope(
            "traveling_merchant", 16780100
        )
        duplicate_checks = checks_for(duplicate)
        self.assertFalse(
            duplicate_checks["scope:market_vendor:differs_from"]
        )
        self.assertFalse(
            duplicate_checks["scope:traveling_merchant:differs_from"]
        )

        extra = copy.deepcopy(context)
        extra["saved_scopes"].append(character_scope("unrelated", 16780102))
        self.assertFalse(checks_for(extra)["saved_scope_count"])

    def test_ep3_governor_3060_binds_late_product_window_and_safe_option(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "ep3_governor_yearly.3060"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53147016,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 19,
            "date_raw": 53156640,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("previous_holder", "character", 32904),
                scope("new_holder", "character", 36354),
                scope("emperor", "character", 36354),
                scope("root_scope", "character", 29037),
                scope("title", "landed_title"),
                scope("transfer_type", "flag"),
                scope("nf_gov_type", "government_type"),
                scope("emp_location", "province"),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((1, 2, 3))
            ],
        }
        snapshot = {"date_raw": 53156640, "active_event": {"option_count": 4}}
        event = {"event_instance_id": 19}
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        outside = copy.deepcopy(context)
        outside["date_raw"] = (
            production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
            + (production.MAX_ADVANCE_DAYS + 1) * production.HOURS_PER_DAY
        )
        outside_snapshot = copy.deepcopy(snapshot)
        outside_snapshot["date_raw"] = outside["date_raw"]
        checks = production._known_interrupt_checks(
            snapshot=outside_snapshot,
            event=event,
            context=outside,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(checks["context_date_raw"])
        self.assertFalse(checks["snapshot_date_raw"])

        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][-1]["scope"]["type_key"] = "value"
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_scope_type,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(checks["scope:emp_location:type"])

    def test_health_7000_accepts_unavoidable_infirmity_frame(self) -> None:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "health.7000",
            "current_event_instance_id": 17,
            "date_raw": 53152296,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53152296, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 17}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["health.7000"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="health.7000",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"] = [
            {
                "name": "unrelated_scope",
                "scope": {"status": "available", "type_key": "value"},
            }
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra_scope,
            event_key="health.7000",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_count"])

    def test_bp1_5725_binds_both_characters_and_selects_terminal_branch(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "bp1_yearly.5725",
            "current_event_instance_id": 14,
            "date_raw": 53147520,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [
                character_scope("matchmaker_courtier", 31003),
                character_scope("khutulun", 16779972),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53147520, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 14}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["bp1_yearly.5725"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="bp1_yearly.5725",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        wrong_khutulun = copy.deepcopy(context)
        wrong_khutulun["saved_scopes"][1]["scope"]["typed_identity"][
            "character_id"
        ] = 16779973
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_khutulun,
            event_key="bp1_yearly.5725",
            contract=contract,
        )
        self.assertFalse(checks["scope:khutulun"])

    def test_health_7500_accepts_only_the_source_proven_single_option_frame(self) -> None:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "health.7500",
            "current_event_instance_id": 16,
            "date_raw": 53152296,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53152296, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 16}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["health.7500"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="health.7500",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"] = [
            {
                "name": "unrelated_scope",
                "scope": {"status": "available", "type_key": "value"},
            }
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra_scope,
            event_key="health.7500",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_count"])

    def test_health_7400_accepts_unavoidable_faltering_heart_frame(self) -> None:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "health.7400",
            "current_event_instance_id": 31,
            "date_raw": 53190360,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53190360, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 31}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["health.7400"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="health.7400",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"] = [
            {
                "name": "unrelated_scope",
                "scope": {"status": "available", "type_key": "value"},
            }
        ]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=extra_scope,
            event_key="health.7400",
            contract=contract,
        )
        self.assertFalse(checks["saved_scope_count"])

    def test_health_1001_binds_generic_illness_and_safe_treatment_branch(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "health.1001"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 22,
            "date_raw": 53175480,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("physician", "character", 56656),
                scope("sick_character", "character", 29037),
                scope("disease_type", "flag"),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((3, 4, 6))
            ],
        }
        snapshot = {"date_raw": 53175480, "active_event": {"option_count": 7}}
        event = {"event_instance_id": 22}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][-1]["native_option_index"] = 5
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

        player_physician = copy.deepcopy(context)
        player_physician["saved_scopes"][0] = scope(
            "physician", "character", 29037
        )
        self.assertFalse(
            checks_for(player_physician)["scope:physician:unique_third_party"]
        )

        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][-1]["scope"]["type_key"] = "value"
        self.assertFalse(checks_for(wrong_scope_type)["scope:disease_type:type"])

    def test_health_3104_binds_safe_treatment_failure_acknowledgement(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "health.3104"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 23,
            "date_raw": 53175480,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("physician", "character", 56656),
                scope("sick_character", "character", 29037),
                scope("disease_type", "flag"),
                scope("treatment_picker", "character", 29037),
                scope("treatment", "flag"),
                scope("outcome", "flag"),
                scope("portrait", "character", 56656),
                scope("background_terrain_scope", "province"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        snapshot = {"date_raw": 53175480, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 23}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_portrait = copy.deepcopy(context)
        wrong_portrait["saved_scopes"][6] = scope(
            "portrait", "character", 56657
        )
        self.assertFalse(
            checks_for(wrong_portrait)["scope:physician:matches_any"]
        )

        non_player_picker = copy.deepcopy(context)
        non_player_picker["saved_scopes"][3] = scope(
            "treatment_picker", "character", 56656
        )
        self.assertFalse(
            checks_for(non_player_picker)["scope:treatment_picker"]
        )

        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][-1]["scope"]["type_key"] = "flag"
        self.assertFalse(
            checks_for(wrong_scope_type)["scope:background_terrain_scope:type"]
        )

    def test_health_1101_binds_generic_illness_recovery_acknowledgement(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "health.1101"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 29,
            "date_raw": 53183712,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("physician", "character", 56656),
                scope("sick_character", "character", 29037),
                scope("disease_type", "flag"),
            ],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53183712, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 29}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        player_physician = copy.deepcopy(context)
        player_physician["saved_scopes"][0] = scope(
            "physician", "character", 29037
        )
        self.assertFalse(
            checks_for(player_physician)["scope:physician:unique_third_party"]
        )

        wrong_disease_type = copy.deepcopy(context)
        wrong_disease_type["saved_scopes"][-1]["scope"]["type_key"] = "value"
        self.assertFalse(
            checks_for(wrong_disease_type)["scope:disease_type:type"]
        )

    def test_health_1006_binds_diagnosis_frame_and_safe_treatment_branch(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "health.1006"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 27,
            "date_raw": 53168904,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("epidemic", "epidemic"),
                scope("disease_type", "flag"),
                scope("physician", "character", 56656),
                scope("sick_character", "character", 29037),
                scope("new_memory", "character_memory"),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((3, 4, 6))
            ],
        }
        snapshot = {"date_raw": 53168904, "active_event": {"option_count": 7}}
        event = {"event_instance_id": 27}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][-1]["native_option_index"] = 5
        self.assertFalse(checks_for(wrong_projection)["authored_options_exact"])

        player_physician = copy.deepcopy(context)
        player_physician["saved_scopes"][2] = scope(
            "physician", "character", 29037
        )
        self.assertFalse(
            checks_for(player_physician)["scope:physician:unique_third_party"]
        )

        wrong_scope_type = copy.deepcopy(context)
        wrong_scope_type["saved_scopes"][0]["scope"]["type_key"] = "flag"
        self.assertFalse(checks_for(wrong_scope_type)["scope:epidemic:type"])

    def test_slander_reaction_accepts_both_source_boolean_shapes(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "scheme_critical_moments.1134"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53177256,
        )
        base_scopes = [
            scope("scheme", "scheme"),
            scope("owner", "character", 28424),
            scope("artifact", "artifact"),
            scope("target", "character", 29037),
            scope("follow_up_event", "flag"),
            scope("discovery_chance", "value"),
        ]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 27,
            "date_raw": 53181000,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": base_scopes + [
                scope("scheme_successful", "boolean")
            ],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53181000, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 27}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        discovered = copy.deepcopy(context)
        discovered["saved_scopes"].insert(
            -1, scope("scheme_discovered", "boolean")
        )
        checks = checks_for(discovered)
        self.assertTrue(all(checks.values()), checks)

        missing_success = copy.deepcopy(context)
        missing_success["saved_scopes"] = base_scopes
        checks = checks_for(missing_success)
        self.assertFalse(checks["boolean_scope_names_exact"])
        self.assertFalse(checks["saved_scope_names_exact"])

        extra_boolean = copy.deepcopy(context)
        extra_boolean["saved_scopes"].insert(
            -1, scope("scheme_discovered", "boolean")
        )
        extra_boolean["saved_scopes"].insert(
            -1, scope("unrelated_boolean", "boolean")
        )
        checks = checks_for(extra_boolean)
        self.assertFalse(checks["saved_scope_names_exact"])

    def test_ep3_governor_8160_binds_fresh_administrator_relationship(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "ep3_governor_yearly.8160"
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 17,
            "date_raw": 53147520,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("councillor", "character", 31003),
                scope("culture", "character", 29037),
                scope("administrator", "character", 16780173),
                scope("minority_county", "landed_title"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        snapshot = {"date_raw": 53147520, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 17}
        contract = production.KNOWN_TIMELINE_INTERRUPTS[event_key]

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        player_administrator = copy.deepcopy(context)
        player_administrator["saved_scopes"][2] = scope(
            "administrator", "character", 29037
        )
        self.assertFalse(
            checks_for(player_administrator)[
                "scope:administrator:unique_third_party"
            ]
        )

        councillor_administrator = copy.deepcopy(context)
        councillor_administrator["saved_scopes"][2] = scope(
            "administrator", "character", 31003
        )
        self.assertFalse(
            checks_for(councillor_administrator)[
                "scope:administrator:differs_from"
            ]
        )

    def test_tgp_military_aid_letter_binds_weak_slots_and_empty_ack(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def unavailable_character_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": "character",
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "character_scope_identity_unavailable",
                    },
                },
            }

        event_key = "tgp_interaction_event.0016"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53147016,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 20,
            "date_raw": 53159976,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                character_scope("actor", 30987),
                character_scope("recipient", 45123),
                unavailable_character_scope("secondary_actor"),
                character_scope("secondary_recipient", 29037),
                unavailable_character_scope("intermediary"),
                character_scope("governor_at_war", 45123),
                character_scope("governor_joining", 29037),
            ],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53159976, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 20}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        invented_weak_identity = copy.deepcopy(context)
        invented_weak_identity["saved_scopes"][2] = character_scope(
            "secondary_actor", 30987
        )
        checks = checks_for(invented_weak_identity)
        self.assertFalse(checks["scope:secondary_actor:unavailable_character"])

        wrong_joining_governor = copy.deepcopy(context)
        wrong_joining_governor["saved_scopes"][-1] = character_scope(
            "governor_joining", 29038
        )
        checks = checks_for(wrong_joining_governor)
        self.assertFalse(checks["scope:governor_joining"])

        mismatched_war_governor = copy.deepcopy(context)
        mismatched_war_governor["saved_scopes"][-2] = character_scope(
            "governor_at_war", 45124
        )
        checks = checks_for(mismatched_war_governor)
        self.assertFalse(checks["scope:recipient:matches_any"])

        player_as_war_governor = copy.deepcopy(context)
        player_as_war_governor["saved_scopes"][1] = character_scope(
            "recipient", 29037
        )
        player_as_war_governor["saved_scopes"][-2] = character_scope(
            "governor_at_war", 29037
        )
        checks = checks_for(player_as_war_governor)
        self.assertFalse(checks["scope:recipient:unique_third_party"])

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(character_scope("extra", 29037))
        checks = checks_for(extra_scope)
        self.assertFalse(checks["saved_scope_count"])

    def test_tgp_elder_break_letter_binds_relationship_payload(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        def unavailable_character_scope(name: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": "character",
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "character_scope_identity_unavailable",
                    },
                },
            }

        event_key = "tgp_interaction_event.0030"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53175480,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 25,
            "date_raw": 53177256,
            "root_scope": scope("root", "character", 29037)["scope"],
            "saved_scopes": [
                scope("actor", "character", 29491),
                scope("recipient", "character", 29037),
                unavailable_character_scope("secondary_actor"),
                unavailable_character_scope("secondary_recipient"),
                unavailable_character_scope("intermediary"),
                scope("prestige", "boolean"),
                scope("gift", "boolean"),
                scope("gift_significant", "boolean"),
                scope("offer_hook", "boolean"),
                scope("offer_hook_strong", "boolean"),
                scope("influence", "boolean"),
                scope("piety", "boolean"),
                scope("hook", "boolean"),
                scope("actors_movement", "situation_participant_group"),
                scope("new_disciple", "character", 29491),
                scope("old_elder", "character", 29037),
                scope("new_elder", "character", 26743),
            ],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {"date_raw": 53177256, "active_event": {"option_count": 1}}
        event = {"event_instance_id": 25}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)

        mismatched_disciple = copy.deepcopy(context)
        mismatched_disciple["saved_scopes"][14] = scope(
            "new_disciple", "character", 29492
        )
        self.assertFalse(
            checks_for(mismatched_disciple)["scope:actor:matches_any"]
        )

        player_new_elder = copy.deepcopy(context)
        player_new_elder["saved_scopes"][-1] = scope(
            "new_elder", "character", 29037
        )
        self.assertFalse(
            checks_for(player_new_elder)["scope:new_elder:unique_third_party"]
        )

        invented_scope = copy.deepcopy(context)
        invented_scope["saved_scopes"].append(
            scope("unrelated_scope", "character", 29491)
        )
        self.assertFalse(checks_for(invented_scope)["saved_scope_names_exact"])

        activity_variant = copy.deepcopy(context)
        activity_variant["saved_scopes"] = [
            scope("activity", "activity"),
            scope("host", "character", 31703),
            scope("province", "province"),
            scope("elder_candidate", "character", 28679),
            scope("rival_candidate", "character", 28907),
            scope("my_movement", "situation_participant_group"),
            scope("new_disciple", "character", 28907),
            scope("old_elder", "character", 29037),
            scope("new_elder", "character", 28679),
            scope("actor", "character", 28907),
            scope("recipient", "character", 29037),
        ]
        activity_checks = checks_for(activity_variant)
        self.assertTrue(all(activity_checks.values()), activity_checks)

    def test_mechanism_001_accepts_the_reference_charter_choice(self) -> None:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361m.1",
            "current_event_instance_id": 19,
            "date_raw": 53156376,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            # R74 carried unrelated B1 ticket scopes into this frame.  The
            # mechanism event source reads none of them, so the contract must
            # remain valid regardless of inherited saved-scope payloads.
            "saved_scopes": [
                {
                    "name": "zg361_b1_pending_continue_subject",
                    "scope": {
                        "status": "available",
                        "type_key": "character",
                        "typed_identity": {
                            "status": "available",
                            "kind": "character",
                            "character_id": 29575,
                        },
                    },
                }
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        snapshot = {"date_raw": 53156376, "active_event": {"option_count": 3}}
        event = {"event_instance_id": 19}
        contract = production.KNOWN_TIMELINE_INTERRUPTS["zg361m.1"]
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="zg361m.1",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        wrong_root = copy.deepcopy(context)
        wrong_root["root_scope"]["typed_identity"]["character_id"] = 29575
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_root,
            event_key="zg361m.1",
            contract=contract,
        )
        self.assertFalse(checks["root_character_id"])

    def test_sway_compliment_accepts_dynamic_three_plus_empty_fallback(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        def typed_scope(name: str, type_key: str) -> dict[str, object]:
            return {
                "name": name,
                "scope": {"status": "available", "type_key": type_key},
            }

        def options(native_indices: tuple[int, ...]) -> list[dict[str, object]]:
            return [
                {
                    "rendered_index": index,
                    "native_option_index": native_index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index, native_index in enumerate(native_indices)
            ]

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "sway_ongoing.1002",
            "current_event_instance_id": 15,
            "date_raw": 53149920,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                typed_scope("scheme", "scheme"),
                character_scope("owner", 29037),
                typed_scope("artifact", "artifact"),
                character_scope("target", 27051),
                character_scope("compliment_receiver", 27051),
            ],
            "options": options((1, 3, 8, 12)),
        }
        snapshot = {"date_raw": 53149920, "active_event": {"option_count": 13}}
        event = {"event_instance_id": 15}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["sway_ongoing.1002"],
            starting_date=53147016,
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="sway_ongoing.1002",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)

        alternate_random_flags = copy.deepcopy(context)
        alternate_random_flags["options"] = options((0, 5, 11, 12))
        checks = checks_for(alternate_random_flags)
        self.assertTrue(all(checks.values()), checks)

        for bad_indices in ((1, 1, 8, 12), (1, 3, 12, 12), (1, 3, 8, 11)):
            with self.subTest(native_indices=bad_indices):
                bad_shape = copy.deepcopy(context)
                bad_shape["options"] = options(bad_indices)
                checks = checks_for(bad_shape)
                self.assertFalse(checks["authored_options_exact"])

        wrong_receiver = copy.deepcopy(context)
        wrong_receiver["saved_scopes"][-1] = character_scope(
            "compliment_receiver", 27052
        )
        checks = checks_for(wrong_receiver)
        self.assertFalse(checks["scope:compliment_receiver"])

    def test_sway_visit_uses_exact_no_followup_stress_loss_branch(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "sway_ongoing.5011",
            "current_event_instance_id": 17,
            "date_raw": 53149200,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                {"name": "scheme", "scope": {"status": "available", "type_key": "scheme"}},
                character_scope("owner", 29037),
                {"name": "artifact", "scope": {"status": "available", "type_key": "artifact"}},
                character_scope("target", 27051),
                {"name": "capital", "scope": {"status": "available", "type_key": "province"}},
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53149200, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 17}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["sway_ongoing.5011"],
            starting_date=53147016,
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="sway_ongoing.5011",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        wrong_target = copy.deepcopy(context)
        wrong_target["saved_scopes"][3] = character_scope("target", 27052)
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_target,
            event_key="sway_ongoing.5011",
            contract=contract,
        )
        self.assertFalse(checks["scope:target"])

    def test_sway_success_uses_exact_deterministic_outcome_branch(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "sway_outcome.1001",
            "current_event_instance_id": 20,
            "date_raw": 53153952,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                {"name": "scheme", "scope": {"status": "available", "type_key": "scheme"}},
                character_scope("owner", 29037),
                {"name": "artifact", "scope": {"status": "available", "type_key": "artifact"}},
                character_scope("target", 27051),
                {
                    "name": "scheme_successful",
                    "scope": {"status": "available", "type_key": "boolean"},
                },
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53153952, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 20}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["sway_outcome.1001"],
            starting_date=53147016,
        )
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=context,
            event_key="sway_outcome.1001",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        wrong_success_type = copy.deepcopy(context)
        wrong_success_type["saved_scopes"][4]["scope"]["type_key"] = "value"
        checks = production._known_interrupt_checks(
            snapshot=snapshot,
            event=event,
            context=wrong_success_type,
            event_key="sway_outcome.1001",
            contract=contract,
        )
        self.assertFalse(checks["scope:scheme_successful"])

    def test_unpaid_tax_binds_dynamic_distinct_liege_and_official(self) -> None:
        def character_scope(name: str, character_id: int) -> dict[str, object]:
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

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "tgp_china_yearly.0020",
            "current_event_instance_id": 29,
            "date_raw": 53166240,
            "root_scope": character_scope("root", 29037)["scope"],
            "saved_scopes": [
                {
                    "name": "taxless_county",
                    "scope": {"status": "available", "type_key": "landed_title"},
                },
                character_scope("tax_official", 29346),
                character_scope("tax_liege", 36354),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        snapshot = {"date_raw": 53166240, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 29}
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["tgp_china_yearly.0020"],
            starting_date=53153952,
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="tgp_china_yearly.0020",
                contract=contract,
            )

        self.assertTrue(all(checks_for(context).values()), checks_for(context))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        player_liege = copy.deepcopy(context)
        player_liege["saved_scopes"][2] = character_scope("tax_liege", 29037)
        self.assertFalse(checks_for(player_liege)["scope:tax_liege:unique_third_party"])

        same_role = copy.deepcopy(context)
        same_role["saved_scopes"][2] = character_scope("tax_liege", 29346)
        self.assertFalse(checks_for(same_role)["scope:tax_liege:differs_from"])

    def test_run_cell_passes_owned_product_lineage_to_capture_callable(self) -> None:
        self._run_cell_case(entry_error=False)

    def test_run_cell_preserves_production_timeline_on_entry_error(self) -> None:
        self._run_cell_case(entry_error=True)

    def test_run_cell_retains_healthy_session_on_harness_red(self) -> None:
        self._run_cell_case(entry_error=True, retain_session=True)

    def test_run_cell_deduplicates_primary_product_runtime_diagnostic(self) -> None:
        self._run_cell_case(entry_error=True, diagnostic_dedupe=True)

    def _run_cell_case(
        self,
        *,
        entry_error: bool,
        retain_session: bool = False,
        diagnostic_dedupe: bool = False,
    ) -> None:
        seed_sha = "A" * 64
        seed_contract = _player_manager_seed_contract(seed_sha)
        seed_install = {"result": "GREEN", "contract": seed_contract}
        binding = {"bridge_pid": 4321, "connection_generation": 1}
        loader_gate = {
            "result": "GREEN",
            "mode": "phase2_promotion_source_checkpoint_live",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
            "loader_error_log_scan": {"result": "GREEN"},
            "runtime_mount_inventory": ["product"],
        }
        captured = {
            "schema_version": 2,
            "kind": runner.PROMOTION_SOURCE_CAPTURE_ARTIFACT_KIND,
            "result": "GREEN",
            "incomplete_for_canonical_4_entry_registry": True,
            "canonical_registry_ready": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            bridge = SimpleNamespace(pipe_name=r"\\.\pipe\promotion-source-unit")
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                duplicate_diagnostic = (
                    "error.log: complete zg361 product runtime diagnostic block"
                )
                if diagnostic_dedupe:
                    stack.enter_context(
                        mock.patch.object(
                            runner,
                            "project_diagnostics",
                            return_value=([duplicate_diagnostic], []),
                        )
                    )
                stack.enter_context(
                    mock.patch.object(
                        runner,
                        "install_phase2_seed",
                        return_value=copy.deepcopy(seed_install),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        runner,
                        "start_phase2_native_session_supervisor",
                        return_value={
                            "kind": "fake-supervisor",
                            "session_done": threading.Event(),
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        runner,
                        "wait_for_phase2_native_session_binding",
                        return_value=copy.deepcopy(binding),
                    )
                )
                gate = stack.enter_context(
                    mock.patch.object(
                        runner,
                        "run_loader_gate",
                        return_value=copy.deepcopy(loader_gate),
                    )
                )
                stop = stack.enter_context(
                    mock.patch.object(
                        runner,
                        "stop_phase2_native_session_supervisor",
                        return_value={
                            "pid_lineage": [4321],
                            "connection_generation_lineage": [1],
                            "session_report": {"restart_count": 0},
                        },
                    )
                )
                capture = stack.enter_context(
                    mock.patch.object(
                        runner,
                        "capture_promotion_source_checkpoint_v2",
                        return_value=copy.deepcopy(captured),
                    )
                )
                def run_entry(*args, **kwargs):
                    retained = kwargs["evidence_out"]
                    retained.update({
                        "schema_version": 1,
                        "kind": "zg361_phase2_promotion_source_production_entry",
                        "result": "RED" if entry_error else "GREEN",
                        "readiness": "static-ready-live-pending" if entry_error else "paused-real-zg361pp.147",
                        "observations": [{"date_raw": 53157024, "active_event": True}],
                    })
                    if entry_error:
                        if diagnostic_dedupe:
                            raise RuntimeError(
                                "product runtime diagnostic: "
                                + duplicate_diagnostic
                            )
                        raise RuntimeError("known interrupt date drift")
                    return retained

                entry = stack.enter_context(
                    mock.patch.object(
                        runner,
                        "enter_promotion_source_checkpoint_v1",
                        side_effect=run_entry,
                    )
                )
                forbidden_launch = stack.enter_context(
                    mock.patch.object(runner, "launch_native_ck3")
                )
                report = runner.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    phase2_promotion_source_capture_live=True,
                    phase2_promotion_source_capture_timeout_seconds=12.5,
                    retain_healthy_phase2_session_on_red=retain_session,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "unit"}
                    },
                )
                retained = json.loads(
                    (root / "artifacts" / "03_promotion_source_production_entry.json").read_text(encoding="utf-8")
                )

        forbidden_launch.assert_not_called()
        gate.assert_called_once()
        self.assertTrue(
            gate.call_args.kwargs["phase2_promotion_source_capture_live"]
        )
        entry.assert_called_once()
        self.assertEqual(entry.call_args.kwargs["timeout_seconds"], 12.5)
        self.assertTrue(
            callable(entry.call_args.kwargs["runtime_diagnostic_probe"])
        )
        self.assertEqual(retained["observations"], [{"date_raw": 53157024, "active_event": True}])
        if entry_error:
            capture.assert_not_called()
            self.assertEqual(retained["result"], "RED")
            if diagnostic_dedupe:
                self.assertIn(duplicate_diagnostic, retained["error_reason"])
            else:
                self.assertIn(
                    "known interrupt date drift", retained["error_reason"]
                )
            self.assertEqual(report["result"], "RED")
            if diagnostic_dedupe:
                self.assertEqual(
                    report["error_reason"].count(duplicate_diagnostic), 1
                )
            if retain_session:
                stop.assert_not_called()
                retention = report["phase2_session_retention"]
                self.assertEqual(retention["result"], "RETAINED")
                self.assertTrue(retention["reconnect_authorized"])
                self.assertFalse(
                    retention["process_restart_required"]
                )
                self.assertEqual(report["native_cleanup"]["result"], "RETAINED")
            else:
                stop.assert_called_once()
            return
        capture.assert_called_once()
        self.assertEqual(retained["result"], "GREEN")
        self.assertEqual(capture.call_args.kwargs["timeout_seconds"], 12.5)
        session = capture.call_args.kwargs["managed_product_session"]
        lineage = capture.call_args.kwargs["capture_lineage"]
        self.assertTrue(session["product_only_runtime"])
        self.assertFalse(session["acceptance_fixture_loaded"])
        self.assertEqual(session["tracked_ck3_pid"], 4321)
        self.assertEqual(session["connection_generation"], 1)
        self.assertEqual(
            session["seed_lineage_id"], f"zg361-phase2-seed-{seed_sha.lower()}"
        )
        self.assertEqual(lineage["game_version"], runner.EXPECTED_GAME_VERSION)
        self.assertFalse(lineage["fixture_used"])
        self.assertFalse(lineage["console_used"])
        stop.assert_called_once()
        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["phase2_promotion_source_capture_complete"])
        self.assertFalse(report["gameplay_acceptance_executed"])
        self.assertFalse(report["gameplay_green_claimed"])


    def test_ep1_flavor_2040_binds_r183_exotic_blade_refusal(self) -> None:
        def scope(
            name: str, type_key: str, character_id: int | None = None
        ) -> dict[str, object]:
            value: dict[str, object] = {
                "status": "available",
                "type_key": type_key,
            }
            if character_id is not None:
                value["typed_identity"] = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {"name": name, "scope": value}

        event_key = "ep1_flavor.2040"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=production.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 65,
            "date_raw": 53174184,
            "root_scope": scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                scope("exotic_blade_holder", "character", 34092),
                scope("exotic_arms_target", "character", 32904),
                scope("owner", "character", 34092),
                scope("weapon_type", "flag"),
                scope("random_quality_bonus", "value"),
                scope("quality", "value"),
                scope("wealth", "value"),
                scope("newly_created_artifact", "artifact"),
                scope("merchant_county", "landed_title"),
                scope("foreign_merchant", "character", 65791),
                scope("exotic_blade", "artifact"),
            ],
            "options": [
                {
                    "rendered_index": rendered_index,
                    "native_option_index": native_option_index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered_index, native_option_index in enumerate((1, 2))
            ],
        }
        snapshot = {
            "date_raw": 53174184,
            "active_event": {"option_count": 3},
        }
        event = {"event_instance_id": 65}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        extra_scope = copy.deepcopy(context)
        extra_scope["saved_scopes"].append(scope("unreviewed", "value"))
        self.assertFalse(checks_for(extra_scope)["saved_scope_count"])

        wrong_holder = copy.deepcopy(context)
        wrong_holder["saved_scopes"][0] = scope(
            "exotic_blade_holder", "character", 34093
        )
        self.assertFalse(checks_for(wrong_holder)["scope:exotic_blade_holder"])

        purchase_only_shape = copy.deepcopy(context)
        purchase_only_shape["options"] = purchase_only_shape["options"][:1]
        self.assertFalse(checks_for(purchase_only_shape)["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
