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


class PromotionSourceCheckpointRunnerTests(unittest.TestCase):
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
                    "contract": {
                        "ready": True,
                        "status": "ready",
                        "source": {"sha256": "A" * 64},
                    },
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
        out_of_window["date_raw"] = 53160240
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
        outside["date_raw"] = 53160240
        outside_snapshot = copy.deepcopy(snapshot)
        outside_snapshot["date_raw"] = 53160240
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

    def test_run_cell_passes_owned_product_lineage_to_capture_callable(self) -> None:
        self._run_cell_case(entry_error=False)

    def test_run_cell_preserves_production_timeline_on_entry_error(self) -> None:
        self._run_cell_case(entry_error=True)

    def test_run_cell_retains_healthy_session_on_harness_red(self) -> None:
        self._run_cell_case(entry_error=True, retain_session=True)

    def _run_cell_case(
        self, *, entry_error: bool, retain_session: bool = False
    ) -> None:
        seed_sha = "A" * 64
        seed_contract = {
            "status": "ready",
            "ready": True,
            "source": {"sha256": seed_sha},
        }
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
        self.assertEqual(retained["observations"], [{"date_raw": 53157024, "active_event": True}])
        if entry_error:
            capture.assert_not_called()
            self.assertEqual(retained["result"], "RED")
            self.assertIn("known interrupt date drift", retained["error_reason"])
            self.assertEqual(report["result"], "RED")
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


if __name__ == "__main__":
    unittest.main()
