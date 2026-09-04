#!/usr/bin/env python3
"""Focused static contracts for the Phase 2 B2 and B3 runner routes."""

from __future__ import annotations

import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import threading
import types
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent


def install_optional_desktop_import_stubs() -> None:
    """Keep this static suite independent from live desktop packages."""

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
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


install_optional_desktop_import_stubs()
sys.path.insert(0, str(ROOT / "tools"))
import run_zhongguo_acceptance as capture  # noqa: E402


def paused_snapshot(
    *,
    snapshot_id: str,
    revision: int,
    date_raw: int,
    player_character_id: int = 101,
    bridge_pid: int = 5004,
    connection_generation: int = 7,
) -> dict[str, object]:
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": revision,
        "date_raw": date_raw,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": player_character_id},
        "diagnostics": {
            "bridge_pid": bridge_pid,
            "connection_generation": connection_generation,
        },
    }


def seed_contract() -> dict[str, object]:
    return {
        "domain_query_matrix": {
            "schema_version": 1,
            "b2_pip_owner_character_id": 333,
            "incident_owner_character_id": 222,
            "workforce_owner_character_id": 444,
            "ai_owned_case_owner_character_id": 555,
            "ai_owned_case_subject_character_id": 556,
        }
    }


def focused_green_cell_report() -> dict[str, object]:
    matrix = {
        "result": "GREEN",
        "checks": {
            "four_exact_restores": True,
            "all_managed_pids_dead": True,
        },
    }
    return {
        "result": "GREEN",
        "error_reason": None,
        "phase2_b2_same_checkpoint": True,
        "phase2_b2_same_checkpoint_complete": True,
        "gameplay_acceptance_executed": True,
        "gameplay_green_claimed": True,
        "scenario_evidence": {
            "result": "GREEN",
            "phase2_b2_same_checkpoint_complete": True,
            "phase2_acceptance_complete": False,
            "full_phase2_acceptance_claimed": False,
            "mcp_only": True,
            "ocr_used": False,
            "image_used": False,
            "coordinates_used": False,
            "test_decision_used": False,
            "legacy_run_scenario_used": False,
            "b2_same_checkpoint_matrix": matrix,
        },
    }


def focused_b3_green_cell_report(pid: int = 5004) -> dict[str, object]:
    scenario_checks = {
        "initial_pid_matches_tracked": True,
        "post_action_pid_matches_tracked": True,
        "same_connection_generation": True,
        "same_played_character": True,
        "paused_before_and_after": True,
        "map_ready_before_and_after": True,
        "typed_selector_provider_observed": True,
        "manager_action_green": True,
        "gameplay_action_executed": True,
        "gameplay_action_complete": True,
        "ack_not_business_postcondition": True,
        "provider_postcondition_required": True,
        "provider_postcondition_available": True,
        "runner_checks_green": True,
    }
    action = {
        "result": "GREEN",
        "gameplay_action_executed": True,
        "gameplay_action_complete": True,
        "action_ack_is_business_postcondition": False,
    }
    return {
        "result": "GREEN",
        "error_reason": None,
        "tracked_full_acceptance_pid": pid,
        "phase2_b3_manager_governance_live": True,
        "phase2_b3_manager_governance_complete": True,
        "gameplay_acceptance_executed": True,
        "gameplay_green_claimed": True,
        "native_cleanup": {
            "result": "GREEN",
            "restore_expected": False,
            "pid_lineage": [pid],
        },
        "scenario_evidence": {
            "result": "GREEN",
            "phase2_b3_manager_governance_complete": True,
            "phase2_acceptance_complete": False,
            "full_phase2_acceptance_claimed": False,
            "source_checkpoint_registry_used": False,
            "incident_gameplay_action_cell_executed": False,
            "b2_pip_gameplay_action_cell_executed": False,
            "workforce_gameplay_action_cell_executed": False,
            "scoreboard_gameplay_action_cell_executed": False,
            "manager_governance_gameplay_action_cell": action,
            "checks": scenario_checks,
        },
    }
class CountingEvent(threading.Event):
    def __init__(self) -> None:
        super().__init__()
        self.set_count = 0

    def set(self) -> None:
        self.set_count += 1
        super().set()


def supervisor_handle(pid: int) -> tuple[dict[str, object], CountingEvent]:
    stop_event = CountingEvent()
    session_done = threading.Event()
    session_state: dict[str, object] = {}
    report = {"pid": pid, "shutdown": {"ck3_pid": pid}}

    def worker() -> None:
        stop_event.wait()
        session_state["report"] = report
        session_done.set()

    session_thread = threading.Thread(target=worker, daemon=True)
    session_thread.start()
    return (
        {
            "stop_event": stop_event,
            "session_done": session_done,
            "session_state": session_state,
            "session_thread": session_thread,
        },
        stop_event,
    )


class FocusedB2ScenarioTests(unittest.TestCase):
    def test_scenario_orders_prelude_readiness_and_matrix_with_frozen_owner(self) -> None:
        calls: list[str] = []
        initial = paused_snapshot(snapshot_id="initial", revision=10, date_raw=1000)
        post_prelude = paused_snapshot(
            snapshot_id="post-prelude", revision=20, date_raw=1001
        )
        b2_prompt = paused_snapshot(
            snapshot_id="b2-prompt", revision=30, date_raw=1002
        )

        class Service:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                self.assert_revision = expected_revision
                calls.append("manifest")
                return {"loaded_feature_manifest_ready": True}

            def snapshot(self) -> dict[str, object]:
                calls.append("post_prelude_snapshot")
                return post_prelude

        service = Service()
        lifecycle = object()
        matrix = {
            "result": "GREEN",
            "checks": {
                "four_exact_restores": True,
                "all_managed_pids_dead": True,
            },
        }

        def wait_paused(*_args: object, **_kwargs: object) -> dict[str, object]:
            calls.append("paused_seed")
            return initial

        def prove_seed(*_args: object, **_kwargs: object) -> dict[str, object]:
            calls.append("seed_proof")
            return {"result": "GREEN"}

        def run_prelude(*_args: object, **kwargs: object) -> dict[str, object]:
            self.assertEqual(kwargs["baseline_binding"]["snapshot_id"], "initial")
            calls.append("result_continuation_prelude")
            return {"result": "GREEN"}

        def wait_b2(*_args: object, **kwargs: object) -> dict[str, object]:
            self.assertEqual(
                kwargs["baseline_binding"]["snapshot_id"], "post-prelude"
            )
            calls.append("b2_prompt")
            return b2_prompt

        def inspect_prechoice(*_args: object, **kwargs: object) -> dict[str, object]:
            self.assertEqual(kwargs["owner_character_id"], 333)
            calls.append("prechoice")
            return {"result": "GREEN", "provider_ready": True}

        def run_matrix(*args: object, **kwargs: object) -> dict[str, object]:
            self.assertIs(args[0], service)
            self.assertIs(args[1], lifecycle)
            self.assertEqual(kwargs["owner_character_id"], 333)
            self.assertEqual(
                kwargs["artifacts_directory"].name,
                "07_phase2_b2_same_checkpoint_matrix",
            )
            calls.append("matrix")
            return matrix

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with (
                mock.patch.object(
                    capture,
                    "wait_for_phase2_paused_snapshot",
                    side_effect=wait_paused,
                ),
                mock.patch.object(
                    capture, "prove_phase2_loaded_seed", side_effect=prove_seed
                ),
                mock.patch.object(
                    capture,
                    "run_phase2_b2_result_continuation_prelude",
                    side_effect=run_prelude,
                ),
                mock.patch.object(
                    capture,
                    "wait_for_phase2_b2_pip_prompt",
                    side_effect=wait_b2,
                ),
                mock.patch.object(
                    capture, "inspect_b2_pip_prechoice", side_effect=inspect_prechoice
                ),
                mock.patch.object(
                    capture, "run_b2_same_checkpoint_matrix", side_effect=run_matrix
                ),
                mock.patch.object(capture, "run_phase2_live_scenario") as full_batch,
            ):
                evidence = capture.run_phase2_b2_same_checkpoint_scenario(
                    service,
                    lifecycle,
                    artifacts,
                    tracked_ck3_pid=5004,
                    seed_contract=seed_contract(),
                )

        self.assertEqual(
            calls,
            [
                "paused_seed",
                "manifest",
                "seed_proof",
                "result_continuation_prelude",
                "post_prelude_snapshot",
                "b2_prompt",
                "prechoice",
                "matrix",
            ],
        )
        self.assertEqual(service.assert_revision, 10)
        full_batch.assert_not_called()
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["phase2_b2_same_checkpoint_complete"])
        self.assertFalse(evidence["phase2_acceptance_complete"])
        self.assertFalse(evidence["full_phase2_acceptance_claimed"])
        self.assertEqual(evidence["forbidden_full_batch_cells_executed"], [])


class FocusedB2ResultContinuationTests(unittest.TestCase):
    class Service:
        def __init__(
            self,
            event_key: str = "zg361.4",
            *,
            event_date_raw: int = 1001,
        ) -> None:
            self.event_key = event_key
            self.event_date_raw = event_date_raw
            self.revision = 10
            self.paused = True
            self.speed = 5
            self.event_visible = False
            self.selected: list[tuple[int, int, int]] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "snapshot_id": f"native:{self.revision}",
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": self.event_date_raw if self.event_visible else 1000,
                "paused": self.paused,
                "speed": self.speed,
                "map_ready": True,
                "played_character": {"character_id": 101},
                "diagnostics": {
                    "bridge_pid": 5004,
                    "connection_generation": 7,
                },
                "active_event": (
                    {
                        "instance_id": 77,
                        "option_count": (
                            3
                            if self.event_key == capture.B2_PIP_EVENT_DEFINITION_KEY
                            else 4
                        ),
                    }
                    if self.event_visible
                    else None
                ),
            }

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            assert expected_revision == self.revision
            if step == "set-speed-1":
                self.speed = 1
            elif step == "resume-map":
                self.paused = False
                self.event_visible = True
            elif step == "pause-map":
                self.paused = True
            else:
                raise AssertionError(step)
            self.revision += 1
            return {"step": step, "accepted": True, "status": "submitted"}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            assert event_instance_id == 77
            assert expected_revision == self.revision
            return {
                "status": "available",
                "current_event_window_context": {
                    "status": "available",
                    "event_definition_key": self.event_key,
                    "readiness": {"event_definition_identity_ready": True},
                    "options": [
                        {
                            "native_option_index": index,
                            "shown": True,
                            "enabled": True,
                        }
                        for index in range(
                            3
                            if self.event_key == capture.B2_PIP_EVENT_DEFINITION_KEY
                            else 4
                        )
                    ],
                },
            }

        def select_event_option(
            self,
            option_number: int,
            *,
            event_instance_id: int,
            expected_revision: int,
        ) -> dict[str, object]:
            assert expected_revision == self.revision
            self.selected.append(
                (option_number, event_instance_id, expected_revision)
            )
            self.event_visible = False
            self.revision += 1
            return {
                "step": "select-event-option-1",
                "accepted": True,
                "status": "submitted",
            }

    def test_real_zg361_4_option_one_materializes(self) -> None:
        service = self.Service()
        with tempfile.TemporaryDirectory() as temporary:
            evidence = capture.run_phase2_b2_result_continuation_prelude(
                service,
                Path(temporary),
                baseline_binding=capture._phase2_paused_binding(
                    service.snapshot(), label="test baseline"
                ),
                poll_interval_s=0,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(
            evidence["event_identity"]["event_definition_key"], "zg361.4"
        )
        self.assertEqual(service.selected[0][:2], (1, 77))
        self.assertIsNone(evidence["selection_materialization"]["new_event_instance_id"])

    def test_delayed_resume_accepts_idempotent_already_running_ack(self) -> None:
        class DelayedResumeService(self.Service):
            def __init__(self) -> None:
                super().__init__()
                self.resume_count = 0

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                if step != "resume-map":
                    return super().execute_step(
                        step, expected_revision=expected_revision
                    )
                assert expected_revision == self.revision
                self.resume_count += 1
                if self.resume_count == 1:
                    return {
                        "step": step,
                        "accepted": True,
                        "status": "submitted",
                    }
                self.paused = False
                self.event_visible = True
                self.revision += 1
                return {
                    "step": step,
                    "accepted": True,
                    "status": "already_running",
                }

        service = DelayedResumeService()
        service.speed = 1
        with tempfile.TemporaryDirectory() as temporary:
            evidence = capture.run_phase2_b2_result_continuation_prelude(
                service,
                Path(temporary),
                baseline_binding=capture._phase2_paused_binding(
                    service.snapshot(), label="test delayed resume baseline"
                ),
                poll_interval_s=0,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(service.resume_count, 2)
        self.assertEqual(
            [row["status"] for row in evidence["submissions"][:2]],
            ["submitted", "already_running"],
        )

    def test_exact_b2_prompt_one_day_later_is_preserved_without_selection(self) -> None:
        service = self.Service(
            event_key=capture.B2_PIP_EVENT_DEFINITION_KEY,
            event_date_raw=1000 + capture.CK3_DATE_RAW_HOURS_PER_DAY,
        )
        service.speed = 1
        with tempfile.TemporaryDirectory() as temporary:
            evidence = capture.run_phase2_b2_result_continuation_prelude(
                service,
                Path(temporary),
                baseline_binding=capture._phase2_paused_binding(
                    service.snapshot(), label="test B2 prompt baseline"
                ),
                poll_interval_s=0,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["continuation_mode"], "b2_prompt_already_visible")
        self.assertEqual(
            evidence["event_identity"]["event_definition_key"],
            capture.B2_PIP_EVENT_DEFINITION_KEY,
        )
        self.assertEqual(evidence["post_binding"]["date_raw"], 1024)
        self.assertEqual(service.selected, [])
        self.assertTrue(service.paused)

    def test_delayed_pause_accepts_idempotent_already_paused_ack(self) -> None:
        class DelayedPauseService(self.Service):
            def __init__(self) -> None:
                super().__init__(event_key=capture.B2_PIP_EVENT_DEFINITION_KEY)
                self.pause_count = 0

            def execute_step(
                self, step: str, *, expected_revision: int
            ) -> dict[str, object]:
                if step != "pause-map":
                    return super().execute_step(
                        step, expected_revision=expected_revision
                    )
                assert expected_revision == self.revision
                self.pause_count += 1
                if self.pause_count == 1:
                    return {
                        "step": step,
                        "accepted": True,
                        "status": "submitted",
                    }
                self.paused = True
                self.revision += 1
                return {
                    "step": step,
                    "accepted": True,
                    "status": "already_paused",
                }

        service = DelayedPauseService()
        service.speed = 1
        with tempfile.TemporaryDirectory() as temporary:
            evidence = capture.run_phase2_b2_result_continuation_prelude(
                service,
                Path(temporary),
                baseline_binding=capture._phase2_paused_binding(
                    service.snapshot(), label="test delayed pause baseline"
                ),
                poll_interval_s=0,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(service.pause_count, 2)
        self.assertEqual(
            [row["status"] for row in evidence["submissions"][-2:]],
            ["submitted", "already_paused"],
        )
        self.assertTrue(service.paused)

    def test_unexpected_visible_event_fails_without_selection(self) -> None:
        service = self.Service(event_key="vanilla.999")
        service.event_visible = True
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(capture.acceptance.RunnerError) as caught:
                capture.run_phase2_b2_result_continuation_prelude(
                    service,
                    Path(temporary),
                    baseline_binding=capture._phase2_paused_binding(
                        service.snapshot(), label="test baseline"
                    ),
                    poll_interval_s=0,
                )
        self.assertIn("unexpected visible event", str(caught.exception))
        self.assertEqual(service.selected, [])


class FocusedB2MainTests(unittest.TestCase):
    def test_product_only_mount_inventory_does_not_require_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            userdir = Path(temporary)
            product = userdir / "mod-content" / "zhongguo_361"
            logs = userdir / "logs"
            product.mkdir(parents=True)
            logs.mkdir()
            (logs / "debug.log").write_text(
                "runtime|mod/zg361_acceptance.mod|Enabled\n"
                f"Mounted Data: {product.as_posix()}\n",
                encoding="utf-8",
            )
            mounted = capture.verify_runtime_load_order(
                userdir,
                {
                    "enabled_mods": ["mod/zg361_acceptance.mod"],
                    "targets": {"product": product},
                },
            )

        self.assertEqual(mounted, [product.resolve().as_posix()])

    def test_focused_capability_gate_requires_only_used_b2_surface(self) -> None:
        pid = 8123
        self.assertNotIn(
            "manager_governance_snapshot",
            capture.PHASE2_B2_REQUIRED_BRIDGE_CAPABILITY_LABELS,
        )
        self.assertNotIn(
            "manager_governance_snapshot",
            capture.PHASE2_B2_REQUIRED_QUERY_FLAG_LABELS,
        )
        required_bridge = {
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
            for label in capture.PHASE2_B2_REQUIRED_BRIDGE_CAPABILITY_LABELS
        }
        required_steps = {
            capture.PHASE2_REQUIRED_ACTION_STEPS[label]
            for label in capture.PHASE2_B2_REQUIRED_ACTION_STEP_LABELS
        }
        capabilities: dict[str, object] = {
            "mode": capture.NATIVE_BRIDGE_MODE,
            "backend_id": capture.NATIVE_BRIDGE_MODE,
            "visual_fallback": False,
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": sorted(required_bridge),
            "action_steps": sorted(required_steps),
            "diagnostics": {
                "connected": True,
                "bridge_pid": pid,
                "connection_generation": 1,
            },
            "checkpoint_materialization": {"configured": True},
            "native_session_control": {"configured": True},
        }
        for label in capture.PHASE2_B2_REQUIRED_QUERY_FLAG_LABELS:
            capabilities[capture.PHASE2_REQUIRED_QUERY_FLAGS[label]] = True
        service = SimpleNamespace(capabilities=lambda: capabilities)

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            focused = capture.phase2_runtime_capability_preflight(
                service,
                artifacts,
                tracked_ck3_pid=pid,
                managed_restore_supervisor=True,
                focused_b2_same_checkpoint=True,
            )
            with self.assertRaisesRegex(
                capture.acceptance.RunnerError, "MCP capability RED"
            ):
                capture.phase2_runtime_capability_preflight(
                    service,
                    artifacts,
                    tracked_ck3_pid=pid,
                    managed_restore_supervisor=True,
                )

        self.assertEqual(focused["result"], "GREEN")
        self.assertEqual(
            focused["scope"],
            "focused_b2_same_checkpoint_mcp_capability_profile",
        )
        self.assertNotIn(
            "result_case_snapshot", focused["required_bridge_capabilities"]
        )
        self.assertNotIn(
            "workforce_collective_snapshot",
            focused["required_bridge_capabilities"],
        )

    def test_all_existing_runtime_modes_are_mutually_exclusive_with_focused_b2(
        self,
    ) -> None:
        modes = (
            "promo_capture",
            "phase2_promo_capture",
            "promo_camera_probe",
            "loader_smoke",
            "phase2_live_batch",
        )
        for mode in modes:
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(
                    capture.acceptance.RunnerError, "mutually exclusive"
                ):
                    capture.main(
                        preflight_only=True,
                        phase2_b2_same_checkpoint=True,
                        **{mode: True},
                    )

    def test_preflight_forwards_focused_ready_seed_as_product_only(self) -> None:
        native_config = object()
        with (
            mock.patch.object(
                capture, "resolve_native_bridge_config", return_value=native_config
            ),
            mock.patch.object(capture, "preflight", return_value={}),
            mock.patch.object(
                capture, "preflight_phase2_seed_contract", return_value={}
            ) as seed_preflight,
        ):
            result = capture.main(
                preflight_only=True,
                phase2_b2_same_checkpoint=True,
            )

        self.assertEqual(result, 0)
        self.assertTrue(seed_preflight.call_args.kwargs["product_only_runtime"])

    def test_main_forwards_flag_accepts_scoped_green_and_rejects_full_claim(
        self,
    ) -> None:
        green_report = focused_green_cell_report()
        invalid_full_claim = copy.deepcopy(green_report)
        invalid_full_claim["scenario_evidence"]["phase2_acceptance_complete"] = True
        invalid_full_claim["scenario_evidence"]["full_phase2_acceptance_claimed"] = True

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            steam_root = root / "steam"
            steam_root.mkdir()
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            dll.write_bytes(b"focused-b2-test-dll")
            injector.write_bytes(b"focused-b2-test-injector")
            pipe = capture.NATIVE_TITLE_PIPE_PREFIX + "b" * 32
            scoped_artifacts = root / "scoped-green"
            invalid_artifacts = root / "invalid-full-claim"

            with (
                mock.patch.object(
                    capture,
                    "preflight",
                    return_value={"native_bridge_runtime": {"ready": True}},
                ),
                mock.patch.object(
                    capture.terminal,
                    "steam_userdata_root",
                    return_value=steam_root,
                ),
                mock.patch.object(
                    capture.isolated,
                    "steam_workshop_app_roots",
                    return_value=[],
                ),
                mock.patch.object(capture.isolated, "registered_workshop_targets"),
                mock.patch.object(capture.isolated, "ensure_test_paths_safe"),
                mock.patch.object(
                    capture.isolated, "protected_snapshot", return_value={}
                ),
                mock.patch.object(capture.isolated, "verify_protected_storage"),
                mock.patch.object(capture, "write_evidence_index"),
                mock.patch.object(
                    capture,
                    "run_cell",
                    side_effect=[green_report, invalid_full_claim],
                ) as run_cell,
            ):
                scoped_result = capture.main(
                    artifacts_dir=str(scoped_artifacts),
                    keep_userdir=True,
                    phase2_b2_same_checkpoint=True,
                    bridge_dll=str(dll),
                    bridge_injector=str(injector),
                    bridge_pipe=pipe,
                )
                invalid_result = capture.main(
                    artifacts_dir=str(invalid_artifacts),
                    keep_userdir=True,
                    phase2_b2_same_checkpoint=True,
                    bridge_dll=str(dll),
                    bridge_injector=str(injector),
                    bridge_pipe=pipe,
                )

            self.assertEqual(scoped_result, 0)
            self.assertEqual(invalid_result, 1)
            self.assertTrue(
                run_cell.call_args_list[0].kwargs["phase2_b2_same_checkpoint"]
            )
            self.assertFalse(run_cell.call_args_list[0].kwargs["phase2_live_batch"])

            scoped = json.loads(
                (scoped_artifacts / "report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(scoped["result"], "GREEN")
            self.assertTrue(scoped["phase2_b2_same_checkpoint_complete"])
            self.assertFalse(scoped["phase2_live_batch"])
            self.assertFalse(
                scoped["cell"]["scenario_evidence"]["phase2_acceptance_complete"]
            )
            self.assertFalse(
                scoped["cell"]["scenario_evidence"][
                    "full_phase2_acceptance_claimed"
                ]
            )

            rejected = json.loads(
                (invalid_artifacts / "report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(rejected["result"], "RED")
            self.assertFalse(rejected["phase2_b2_same_checkpoint_complete"])
            self.assertFalse(rejected["gameplay_green_claimed"])
            self.assertIn("focused B2 report lacks", rejected["error_reason"])


class FocusedB3ManagerGovernanceTests(unittest.TestCase):
    def test_capability_gate_requires_only_the_b3_runtime_surface(self) -> None:
        pid = 8124
        required_bridge = {
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
            for label in capture.PHASE2_B3_MANAGER_REQUIRED_BRIDGE_CAPABILITY_LABELS
        }
        required_steps = {
            capture.PHASE2_REQUIRED_ACTION_STEPS[label]
            for label in capture.PHASE2_B3_MANAGER_REQUIRED_ACTION_STEP_LABELS
        }
        capabilities: dict[str, object] = {
            "mode": capture.NATIVE_BRIDGE_MODE,
            "backend_id": capture.NATIVE_BRIDGE_MODE,
            "visual_fallback": False,
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": sorted(required_bridge),
            "action_steps": sorted(required_steps),
            "diagnostics": {
                "connected": True,
                "bridge_pid": pid,
                "connection_generation": 1,
            },
            "checkpoint_materialization": {"configured": True},
            "native_session_control": {"configured": True},
        }
        for label in capture.PHASE2_B3_MANAGER_REQUIRED_QUERY_FLAG_LABELS:
            capabilities[capture.PHASE2_REQUIRED_QUERY_FLAGS[label]] = True
        service = SimpleNamespace(capabilities=lambda: capabilities)

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            focused = capture.phase2_runtime_capability_preflight(
                service,
                artifacts,
                tracked_ck3_pid=pid,
                managed_restore_supervisor=True,
                focused_b3_manager_governance=True,
            )
            missing_selector = copy.deepcopy(capabilities)
            missing_selector[
                capture.PHASE2_REQUIRED_QUERY_FLAGS[
                    "manager_subordinate_selector"
                ]
            ] = False
            with self.assertRaisesRegex(
                capture.acceptance.RunnerError, "MCP capability RED"
            ):
                capture.phase2_runtime_capability_preflight(
                    SimpleNamespace(
                        capabilities=lambda: missing_selector
                    ),
                    artifacts,
                    tracked_ck3_pid=pid,
                    managed_restore_supervisor=True,
                    focused_b3_manager_governance=True,
                )

        self.assertEqual(focused["result"], "GREEN")
        self.assertEqual(
            focused["scope"],
            "focused_b3_manager_governance_mcp_capability_profile",
        )
        self.assertEqual(
            set(focused["required_bridge_capabilities"]),
            set(capture.PHASE2_B3_MANAGER_REQUIRED_BRIDGE_CAPABILITY_LABELS),
        )
        for unrelated in (
            "b2_pip_snapshot",
            "incident_snapshot",
            "workforce_collective_snapshot",
            "scoreboard_state_acl",
            "scoreboard_action_transport",
            "result_case_snapshot",
            "promotion_compensation_postcondition",
            "promotion_source_progress_transport",
            "review_now_action_transport",
        ):
            self.assertNotIn(
                unrelated, focused["required_bridge_capabilities"]
            )

    def test_scenario_uses_native_selector_and_only_b3_cell(self) -> None:
        pid = 5004
        generation = 7
        initial = paused_snapshot(
            snapshot_id="b3-initial",
            revision=10,
            date_raw=1000,
            bridge_pid=pid,
            connection_generation=generation,
        )
        selector_snapshot = paused_snapshot(
            snapshot_id="b3-selector",
            revision=11,
            date_raw=1000,
            bridge_pid=pid,
            connection_generation=generation,
        )
        final = paused_snapshot(
            snapshot_id="b3-final",
            revision=12,
            date_raw=1001,
            bridge_pid=pid,
            connection_generation=generation,
        )
        snapshots = iter((selector_snapshot, final))
        selector_calls: list[tuple[str, int]] = []

        class Service:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                self.manifest_revision = expected_revision
                return {"loaded_feature_manifest_ready": True}

            def snapshot(self) -> dict[str, object]:
                return next(snapshots)

            def query_zhongguo_manager_subordinate_selector_v1(
                self,
                request_nonce: str,
                *,
                expected_revision: int,
            ) -> dict[str, object]:
                selector_calls.append((request_nonce, expected_revision))
                return {
                    "status": "available",
                    "selector_kind": capture.PHASE2_B3_MANAGER_SELECTOR_KIND,
                    "provider_observed": True,
                    "manager_character_id": 201,
                    "subordinate_character_id": 202,
                }

        service = Service()
        transition = {
            "gameplay_action_executed": True,
            "gameplay_action_complete": True,
            "background_business_complete": True,
            "action_ack_is_business_postcondition": False,
        }
        action = {
            "result": "GREEN",
            "gameplay_action_executed": True,
            "gameplay_action_complete": True,
            "action_ack_is_business_postcondition": False,
            "transition": transition,
            "postcondition": {"status": "available"},
            "checks": {"provider_business_postcondition": True},
        }
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(
                capture,
                "wait_for_phase2_paused_snapshot",
                return_value=initial,
            ),
            mock.patch.object(
                capture,
                "prove_phase2_loaded_seed",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "run_b3_manager_governance_gameplay_action_cell",
                return_value=action,
            ) as action_cell,
        ):
            evidence = capture.run_phase2_b3_manager_governance_live_scenario(
                service,
                Path(temporary),
                tracked_ck3_pid=pid,
                seed_contract=seed_contract(),
            )

        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["phase2_b3_manager_governance_complete"])
        self.assertFalse(evidence["phase2_acceptance_complete"])
        self.assertFalse(evidence["source_checkpoint_registry_used"])
        self.assertEqual(selector_calls, [("zg361.b3.manager.selector", 11)])
        self.assertEqual(
            action_cell.call_args.kwargs,
            {"manager_character_id": 201, "subordinate_character_id": 202},
        )
        self.assertTrue(all(evidence["checks"].values()))
        for key in (
            "incident_gameplay_action_cell_executed",
            "b2_pip_gameplay_action_cell_executed",
            "workforce_gameplay_action_cell_executed",
            "scoreboard_gameplay_action_cell_executed",
        ):
            self.assertFalse(evidence[key])

    def test_scenario_fails_closed_on_connection_generation_drift(self) -> None:
        pid = 5004
        initial = paused_snapshot(
            snapshot_id="b3-initial",
            revision=10,
            date_raw=1000,
            bridge_pid=pid,
            connection_generation=7,
        )
        final = paused_snapshot(
            snapshot_id="b3-final",
            revision=12,
            date_raw=1001,
            bridge_pid=pid,
            connection_generation=8,
        )
        service = SimpleNamespace(
            query_loaded_feature_manifest_v1=lambda **_kwargs: {
                "loaded_feature_manifest_ready": True
            },
            snapshot=lambda: final,
        )
        manager_action = {
            "result": "GREEN",
            "gameplay_action_executed": True,
            "gameplay_action_complete": True,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition_required": True,
            "provider_observed_postcondition": {"status": "available"},
            "typed_selector": {
                "status": "available",
                "selector_kind": capture.PHASE2_B3_MANAGER_SELECTOR_KIND,
                "provider_observed": True,
            },
            "runner_checks": {"provider_business_postcondition": True},
        }
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(
                capture,
                "wait_for_phase2_paused_snapshot",
                return_value=initial,
            ),
            mock.patch.object(
                capture,
                "prove_phase2_loaded_seed",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "run_phase2_manager_governance_gameplay_action_cell",
                return_value=manager_action,
            ),
        ):
            artifacts = Path(temporary)
            with self.assertRaisesRegex(
                capture.acceptance.RunnerError,
                "same_connection_generation",
            ):
                capture.run_phase2_b3_manager_governance_live_scenario(
                    service,
                    artifacts,
                    tracked_ck3_pid=pid,
                    seed_contract=seed_contract(),
                )
            persisted = json.loads(
                (
                    artifacts
                    / "05_phase2_b3_manager_governance_live_scenario.json"
                ).read_text(encoding="utf-8")
            )
        self.assertEqual(persisted["result"], "RED")
        self.assertIn(
            "same_connection_generation", persisted["failed_checks"]
        )

    def test_loader_gate_forwards_the_dedicated_b3_profile(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(
                capture,
                "wait_for_phase2_seed_loader_stage",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "native_loader_smoke_readiness",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture,
                "phase2_runtime_capability_preflight",
                return_value={"result": "GREEN"},
            ) as capability_preflight,
            mock.patch.object(
                capture,
                "scan_loader_error_log",
                return_value={"result": "GREEN"},
            ),
            mock.patch.object(
                capture, "verify_runtime_load_order", return_value=[]
            ),
        ):
            root = Path(temporary)
            artifacts = root / "artifacts"
            userdir = root / "profile"
            artifacts.mkdir()
            userdir.mkdir()
            evidence = capture.run_loader_gate(
                SimpleNamespace(),
                artifacts,
                userdir,
                {},
                tracked_ck3_pid=5004,
                phase2_live_batch=False,
                managed_restore_supervisor=True,
                phase2_b3_manager_governance_live=True,
            )

        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["mode"], "phase2_b3_manager_governance_live")
        kwargs = capability_preflight.call_args.kwargs
        self.assertTrue(kwargs["focused_b3_manager_governance"])
        self.assertFalse(kwargs["focused_b2_same_checkpoint"])
        self.assertTrue(kwargs["managed_restore_supervisor"])

    def test_cli_and_main_forward_the_scoped_mode_without_registries(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(
                sys,
                "argv",
                [str(Path(capture.__file__)), "--help"],
            ),
            redirect_stdout(output),
            self.assertRaises(SystemExit) as help_exit,
        ):
            runpy.run_path(str(Path(capture.__file__)), run_name="__main__")
        self.assertEqual(help_exit.exception.code, 0)
        self.assertIn("--phase2-b3-manager-governance-live", output.getvalue())

        green_report = focused_b3_green_cell_report()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            steam_root = root / "steam"
            steam_root.mkdir()
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            dll.write_bytes(b"focused-b3-test-dll")
            injector.write_bytes(b"focused-b3-test-injector")
            artifacts = root / "focused-b3-green"
            with (
                mock.patch.object(
                    capture,
                    "preflight",
                    return_value={"native_bridge_runtime": {"ready": True}},
                ),
                mock.patch.object(
                    capture.terminal,
                    "steam_userdata_root",
                    return_value=steam_root,
                ),
                mock.patch.object(
                    capture.isolated,
                    "steam_workshop_app_roots",
                    return_value=[],
                ),
                mock.patch.object(capture.isolated, "registered_workshop_targets"),
                mock.patch.object(capture.isolated, "ensure_test_paths_safe"),
                mock.patch.object(
                    capture.isolated, "protected_snapshot", return_value={}
                ),
                mock.patch.object(capture.isolated, "verify_protected_storage"),
                mock.patch.object(capture, "write_evidence_index"),
                mock.patch.object(
                    capture, "run_cell", return_value=green_report
                ) as run_cell,
            ):
                result = capture.main(
                    artifacts_dir=str(artifacts),
                    keep_userdir=True,
                    phase2_b3_manager_governance_live=True,
                    phase2_frontend_first_load_save_name="autosave",
                    phase2_frontend_first_timeout_seconds=180,
                    bridge_dll=str(dll),
                    bridge_injector=str(injector),
                    bridge_pipe=(capture.NATIVE_TITLE_PIPE_PREFIX + "c" * 32),
                )
                outer = json.loads(
                    (artifacts / "report.json").read_text(encoding="utf-8")
                )

        self.assertEqual(result, 0)
        forwarded = run_cell.call_args.kwargs
        self.assertTrue(forwarded["phase2_b3_manager_governance_live"])
        self.assertEqual(
            forwarded["phase2_frontend_first_load_save_name"], "autosave"
        )
        self.assertEqual(
            forwarded["phase2_frontend_first_timeout_seconds"], 180
        )
        self.assertIsNone(forwarded["phase2_source_checkpoint_registry"])
        self.assertIsNone(
            forwarded["phase2_scoreboard_surface_checkpoint_registry"]
        )
        self.assertEqual(outer["result"], "GREEN")
        self.assertTrue(outer["phase2_b3_manager_governance_complete"])
        self.assertFalse(outer["phase2_live_batch"])

    def test_b3_mode_is_mutually_exclusive_with_full_and_b2(self) -> None:
        for conflict in ("phase2_live_batch", "phase2_b2_same_checkpoint"):
            with self.subTest(conflict=conflict):
                with self.assertRaisesRegex(
                    capture.acceptance.RunnerError, "mutually exclusive"
                ):
                    capture.main(
                        preflight_only=True,
                        phase2_b3_manager_governance_live=True,
                        **{conflict: True},
                    )

    def test_b3_mode_requires_managed_frontend_first_load(self) -> None:
        with self.assertRaisesRegex(
            capture.acceptance.RunnerError,
            "requires the managed frontend-first load-save option",
        ):
            capture.main(
                preflight_only=True,
                phase2_b3_manager_governance_live=True,
            )


class Phase2FullCapabilityPreflightTests(unittest.TestCase):
    @staticmethod
    def complete_capabilities(pid: int) -> dict[str, object]:
        return {
            "mode": capture.NATIVE_BRIDGE_MODE,
            "backend_id": capture.NATIVE_BRIDGE_MODE,
            "visual_fallback": False,
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": sorted(
                set(capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES.values())
            ),
            "action_steps": sorted(
                set(capture.PHASE2_REQUIRED_ACTION_STEPS.values())
            ),
            **{
                flag: True
                for flag in capture.PHASE2_REQUIRED_QUERY_FLAGS.values()
            },
            "diagnostics": {
                "connected": True,
                "bridge_pid": pid,
                "connection_generation": 1,
            },
            "checkpoint_materialization": {"configured": True},
            "native_session_control": {"configured": True},
        }

    def test_result_case_typed_query_is_not_a_zero_argument_action_step(
        self,
    ) -> None:
        pid = 9137
        capability = "game.command.query-zhongguo-result-case-snapshot-v1"
        flag = "zhongguo_result_case_snapshot_v1_query_supported"
        step = "query-zhongguo-result-case-snapshot-v1"

        self.assertEqual(
            capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[
                "result_case_snapshot"
            ],
            capability,
        )
        self.assertEqual(
            capture.PHASE2_REQUIRED_QUERY_FLAGS["result_case_snapshot"],
            flag,
        )
        self.assertNotIn(
            "result_case_snapshot", capture.PHASE2_REQUIRED_ACTION_STEPS
        )

        capabilities = self.complete_capabilities(pid)
        self.assertNotIn(step, capabilities["action_steps"])
        service = SimpleNamespace(capabilities=lambda: capabilities)
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            green = capture.phase2_runtime_capability_preflight(
                service,
                artifacts,
                tracked_ck3_pid=pid,
                managed_restore_supervisor=True,
            )
        self.assertEqual(green["result"], "GREEN")
        self.assertEqual(green["missing_requirements"], [])

        for kind in ("bridge_capability", "query_support_flag"):
            missing = copy.deepcopy(capabilities)
            if kind == "bridge_capability":
                missing["bridge_capabilities"].remove(capability)
            else:
                missing[flag] = False
            service = SimpleNamespace(capabilities=lambda value=missing: value)
            with (
                self.subTest(kind=kind),
                tempfile.TemporaryDirectory() as temporary,
            ):
                artifacts = Path(temporary)
                with self.assertRaisesRegex(
                    capture.acceptance.RunnerError, "MCP capability RED"
                ):
                    capture.phase2_runtime_capability_preflight(
                        service,
                        artifacts,
                        tracked_ck3_pid=pid,
                        managed_restore_supervisor=True,
                    )
                persisted = json.loads(
                    (
                        artifacts / "02_phase2_mcp_capabilities.json"
                    ).read_text(encoding="utf-8")
                )
            self.assertTrue(
                any(
                    row["kind"] == kind
                    and row["label"] == "result_case_snapshot"
                    and row["value"]
                    == (capability if kind == "bridge_capability" else flag)
                    for row in persisted["missing_requirements"]
                )
            )


class FocusedB2LifecycleTests(unittest.TestCase):
    def test_successful_matrix_stop_is_not_repeated_by_outer_cleanup(self) -> None:
        pid = 5004
        supervisor, stop_event = supervisor_handle(pid)
        capabilities = mock.Mock(
            return_value={
                "diagnostics": {"connected": True, "bridge_pid": pid}
            }
        )
        lifecycle = capture.Phase2B2MatrixLifecycle(
            SimpleNamespace(capabilities=capabilities), supervisor
        )

        first_shutdown = lifecycle.stop_session(pid, reason="matrix final stop")
        outer_report = lifecycle.ensure_stopped(reason="outer cleanup")
        repeated_shutdown = lifecycle.stop_session(pid, reason="idempotent replay")

        self.assertEqual(first_shutdown, {"ck3_pid": pid})
        self.assertIs(outer_report, lifecycle.session_report)
        self.assertEqual(repeated_shutdown, first_shutdown)
        self.assertEqual(stop_event.set_count, 1)
        self.assertEqual(capabilities.call_count, 1)
        self.assertTrue(lifecycle.session_stopped)

    def test_early_red_falls_back_to_exactly_one_supervisor_stop(self) -> None:
        pid = 5005
        supervisor, stop_event = supervisor_handle(pid)
        capabilities = mock.Mock(side_effect=RuntimeError("bridge already gone"))
        lifecycle = capture.Phase2B2MatrixLifecycle(
            SimpleNamespace(capabilities=capabilities), supervisor
        )

        report = lifecycle.ensure_stopped(reason="early scenario RED")
        repeated_report = lifecycle.ensure_stopped(reason="outer cleanup replay")

        self.assertEqual(report["pid"], pid)
        self.assertIs(repeated_report, report)
        self.assertEqual(stop_event.set_count, 1)
        self.assertEqual(capabilities.call_count, 1)
        self.assertTrue(lifecycle.session_stopped)
        self.assertTrue(supervisor["session_done"].is_set())
        self.assertFalse(supervisor["session_thread"].is_alive())


class Phase2DiagnosticClassificationTests(unittest.TestCase):
    def test_phase2_static_liveness_lines_are_retained_as_warnings(self) -> None:
        lines = [
            "[E][jomini_effect.cpp:1145]: Variable 'zg361_example' is set "
            "but is never used. Note that use in localization doesn't count",
            "[E][jomini_effect.cpp:1161]: List target 'zg361_list' is used "
            "but is never set. Setting it in an unused scripted trigger or "
            "effect does not count",
            "[E][jomini_eventmanager.cpp:372]: Event zg361we.361 is orphaned",
            "[E][jomini_effect.cpp:999]: unknown effect zg361_real_failure",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / "profile" / "logs"
            artifacts = root / "artifacts"
            logs.mkdir(parents=True)
            artifacts.mkdir()
            (logs / "error.log").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )

            blocking, warnings = capture.project_diagnostics(
                root / "profile",
                artifacts,
                "phase2",
                allow_phase2_static_liveness_warnings=True,
            )

        self.assertEqual(len(warnings), 3)
        self.assertEqual(len(blocking), 1)
        self.assertIn("unknown effect zg361_real_failure", blocking[0])

    def test_legacy_diagnostic_policy_stays_strict(self) -> None:
        line = (
            "[E][jomini_effect.cpp:1161]: Variable 'zg361_example' is used "
            "but is never set. Setting it in an unused scripted trigger or "
            "effect does not count"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / "profile" / "logs"
            artifacts = root / "artifacts"
            logs.mkdir(parents=True)
            artifacts.mkdir()
            (logs / "error.log").write_text(line + "\n", encoding="utf-8")

            blocking, warnings = capture.project_diagnostics(
                root / "profile", artifacts, "legacy"
            )

        self.assertEqual(warnings, [])
        self.assertEqual(len(blocking), 1)


if __name__ == "__main__":
    unittest.main()
