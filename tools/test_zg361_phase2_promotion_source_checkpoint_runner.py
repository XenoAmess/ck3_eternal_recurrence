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
from test_zhongguo_phase2_promo_runner_plumbing import (  # noqa: E402
    _enter_common_run_cell_patches,
)


class PromotionSourceCheckpointRunnerTests(unittest.TestCase):
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
            {"save-checkpoint", "pause-map", "resume-map", "set-speed-1"},
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

    def test_capture_mode_is_mutually_exclusive_with_other_runtime_modes(self) -> None:
        with self.assertRaisesRegex(
            runner.acceptance.RunnerError, "mutually exclusive"
        ):
            runner.main(
                preflight_only=True,
                loader_smoke=True,
                phase2_promotion_source_capture_live=True,
            )

    def test_run_cell_passes_owned_product_lineage_to_capture_callable(self) -> None:
        self._run_cell_case(entry_error=False)

    def test_run_cell_preserves_production_timeline_on_entry_error(self) -> None:
        self._run_cell_case(entry_error=True)

    def _run_cell_case(self, *, entry_error: bool) -> None:
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
                        return_value={"kind": "fake-supervisor"},
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
