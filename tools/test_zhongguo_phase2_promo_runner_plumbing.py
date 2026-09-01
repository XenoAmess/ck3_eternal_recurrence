"""CK3-free regression tests for phase-two promo runner plumbing."""

from __future__ import annotations

import copy
from contextlib import ExitStack, nullcontext
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
from types import SimpleNamespace
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _install_optional_desktop_import_stubs() -> None:
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


_install_optional_desktop_import_stubs()

import run_zhongguo_acceptance as capture  # noqa: E402
from zhongguo_phase2_promo_producer import (  # noqa: E402
    make_phase2_promo_capture_scaffold,
)


class _FakeDriver:
    instances: list["_FakeDriver"] = []

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.closed = False
        self.instances.append(self)

    def close(self) -> None:
        self.closed = True


class _FakeService:
    def __init__(self, driver: _FakeDriver) -> None:
        self.driver = driver

    def capabilities(self) -> dict[str, object]:
        return {
            "diagnostics": {
                "connected": True,
                "bridge_pid": 4321,
                "connection_generation": 1,
            }
        }


class _FakeRecorder:
    instances: list["_FakeRecorder"] = []

    def __init__(self, artifact_dir: Path, *, contract: object) -> None:
        self.artifact_dir = artifact_dir
        self.contract = contract
        self.process: object | None = object()
        self.stop_calls = 0
        self.instances.append(self)

    def stop(self) -> dict[str, object]:
        self.stop_calls += 1
        self.process = None
        evidence: dict[str, object] = {
            "clean_capture_complete": True,
            "missing_clean_spans": [],
        }
        if self.contract == capture.PHASE2_PROMO_CAPTURE_CONTRACT:
            evidence.update(
                {
                    "capture_mode": capture.PHASE2_PROMO_CAPTURE_MODE,
                    "capture_contract_version": (
                        capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
                    ),
                    "capture_contract": self.contract.to_mapping(),
                }
            )
        return evidence


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid

    def poll(self) -> None:
        return None


def _enter_common_run_cell_patches(
    stack: ExitStack, temporary_root: Path
) -> dict[str, object]:
    runtime_targets: dict[str, Path] = {}

    def bootstrap_userdir(
        userdir: Path,
        _runtime_source: Path,
        *,
        workshop_manifest: Path | None = None,
    ) -> dict[str, object]:
        del workshop_manifest
        logs = userdir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "debug.log").write_text("", encoding="utf-8")
        product = userdir / "mod-content" / "product"
        fixture = userdir / "mod-content" / "fixture"
        product.mkdir(parents=True, exist_ok=True)
        fixture.mkdir(parents=True, exist_ok=True)
        runtime_targets.update(product=product, fixture=fixture)
        return {
            "targets": dict(runtime_targets),
            "tree_snapshots": {"product": {}, "fixture": {}},
            "tree_sha256": {"product": "p", "fixture": "f"},
            "enabled_mods": ["mod/product.mod", "mod/fixture.mod"],
            "manifest": {"fixture": "unit"},
        }

    def make_spec(state_dir: Path, game_dir: Path) -> SimpleNamespace:
        resolved = Path(state_dir).resolve()
        return SimpleNamespace(
            state_dir=resolved,
            profile_dir=resolved / "profile",
            game_exe=Path(game_dir) / "binaries" / "ck3.exe",
        )

    stack.enter_context(
        mock.patch.object(capture.acceptance, "configure_runtime_userdir")
    )
    stack.enter_context(
        mock.patch.object(
            capture, "bootstrap_userdir", side_effect=bootstrap_userdir
        )
    )
    stack.enter_context(mock.patch.object(capture, "make_spec", side_effect=make_spec))
    stack.enter_context(
        mock.patch.object(capture.isolated, "tree_snapshot", return_value={})
    )
    stack.enter_context(
        mock.patch.object(
            capture.isolated,
            "installed_game_version",
            return_value=capture.EXPECTED_GAME_VERSION,
        )
    )
    stack.enter_context(
        mock.patch.object(
            capture.isolated,
            "sha256_file",
            return_value=capture.EXPECTED_EXE_SHA256,
        )
    )
    stack.enter_context(
        mock.patch.object(capture, "NativeHeadlessGameplayDriver", _FakeDriver)
    )
    stack.enter_context(
        mock.patch.object(capture, "GameplayBridgeService", _FakeService)
    )
    stack.enter_context(mock.patch.object(capture, "PromoRecorder", _FakeRecorder))
    stack.enter_context(
        mock.patch.object(capture, "project_diagnostics", return_value=([], []))
    )
    stack.enter_context(mock.patch.object(capture, "copy_logs"))
    stack.enter_context(
        mock.patch.object(
            capture,
            "verify_runtime_load_order",
            return_value=["product", "fixture"],
        )
    )
    return {"runtime_targets": runtime_targets, "temporary_root": temporary_root}


class Phase2PromoRunnerPlumbingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_producer = capture._PHASE2_PROMO_CAPTURE_PRODUCER
        _FakeDriver.instances.clear()
        _FakeRecorder.instances.clear()

    def tearDown(self) -> None:
        capture._PHASE2_PROMO_CAPTURE_PRODUCER = self.prior_producer

    def test_phase2_promo_preflight_keeps_missing_seed_typed_red(self) -> None:
        capture.register_phase2_promo_capture_producer(
            lambda *_args, **_kwargs: {}  # pragma: no cover - never invoked
        )
        bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-promo-unit")
        with (
            mock.patch.object(
                capture, "resolve_native_bridge_config", return_value=bridge
            ),
            mock.patch.object(
                capture,
                "preflight",
                return_value={"native_bridge_runtime": {"unit": True}},
            ) as preflight,
            mock.patch.object(
                capture,
                "load_phase2_seed_contract",
                return_value={
                    "ready": False,
                    "blocker": "no ready canonical paused seed",
                },
            ),
            mock.patch.object(capture, "run_cell") as forbidden_run_cell,
            mock.patch.object(capture, "install_phase2_seed") as forbidden_install,
            mock.patch.object(
                capture, "start_phase2_native_session_supervisor"
            ) as forbidden_supervisor,
        ):
            with self.assertRaises(capture.acceptance.RunnerError) as raised:
                capture.main(
                    preflight_only=True,
                    phase2_promo_capture=True,
                )
        self.assertIn("phase-two seed preflight RED", str(raised.exception))
        self.assertIn("no ready canonical paused seed", str(raised.exception))
        self.assertFalse(preflight.call_args.kwargs["require_visual_tools"])
        forbidden_run_cell.assert_not_called()
        forbidden_install.assert_not_called()
        forbidden_supervisor.assert_not_called()

    def test_phase2_promo_reuses_seed_supervisor_loader_and_context(self) -> None:
        seen: dict[str, object] = {}

        def runtime_probe(context: object) -> dict[str, object]:
            seen["context"] = context
            return {"ready": True, "source": "managed-phase2-unit"}

        def choreography(
            context: object, runtime: dict[str, object]
        ) -> dict[str, object]:
            self.assertIs(context, seen["context"])
            self.assertEqual(runtime["source"], "managed-phase2-unit")
            return {
                "result": "GREEN",
                "capture_mode": capture.PHASE2_PROMO_CAPTURE_MODE,
                "capture_contract_version": (
                    capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
                ),
                "capture_contract": (
                    capture.PHASE2_PROMO_CAPTURE_CONTRACT.to_mapping()
                ),
            }

        capture.register_phase2_promo_capture_producer(
            make_phase2_promo_capture_scaffold(
                runtime_probe=runtime_probe,
                choreography=choreography,
            )
        )
        ready_contract = {
            "status": "ready",
            "ready": True,
            "seed_identity": "canonical-unit-seed",
        }
        seed_install = {
            "result": "GREEN",
            "contract": ready_contract,
            "targets": {"continue": "autosave.ck3"},
        }
        binding = {
            "bridge_pid": 4321,
            "connection_generation": 1,
        }
        loader_gate = {
            "result": "GREEN",
            "mode": "phase2_promo_capture",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
            "loader_error_log_scan": {"result": "GREEN"},
            "runtime_mount_inventory": ["product", "fixture"],
        }
        lifecycle: list[str] = []

        def install_seed(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("seed")
            return copy.deepcopy(seed_install)

        def start_supervisor(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("supervisor")
            return {"kind": "fake-supervisor"}

        def wait_binding(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("binding")
            return copy.deepcopy(binding)

        def run_gate(*_args: object, **kwargs: object) -> dict[str, object]:
            lifecycle.append("loader")
            self.assertTrue(kwargs["phase2_live_batch"])
            self.assertTrue(kwargs["phase2_promo_capture"])
            self.assertTrue(kwargs["managed_restore_supervisor"])
            return copy.deepcopy(loader_gate)

        def stop_supervisor(
            *_args: object, **kwargs: object
        ) -> dict[str, object]:
            lifecycle.append("cleanup")
            self.assertEqual(kwargs["initial_pid"], 4321)
            self.assertEqual(kwargs["initial_generation"], 1)
            return {
                "pid_lineage": [4321],
                "connection_generation_lineage": [1],
                "session_report": {"restart_count": 0},
            }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-promo-unit")
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                install = stack.enter_context(
                    mock.patch.object(
                        capture, "install_phase2_seed", side_effect=install_seed
                    )
                )
                start = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "start_phase2_native_session_supervisor",
                        side_effect=start_supervisor,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "wait_for_phase2_native_session_binding",
                        side_effect=wait_binding,
                    )
                )
                gate = stack.enter_context(
                    mock.patch.object(
                        capture, "run_loader_gate", side_effect=run_gate
                    )
                )
                stop = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_phase2_native_session_supervisor",
                        side_effect=stop_supervisor,
                    )
                )
                forbidden_launch = stack.enter_context(
                    mock.patch.object(capture, "launch_native_ck3")
                )
                forbidden_liveness = stack.enter_context(
                    mock.patch.object(
                        capture, "phase2_native_session_liveness_gate"
                    )
                )
                forbidden_legacy = stack.enter_context(
                    mock.patch.object(capture, "run_scenario")
                )
                report = capture.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    phase2_promo_capture=True,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "preflight-unit"}
                    },
                )

        self.assertEqual(lifecycle, ["seed", "supervisor", "binding", "loader", "cleanup"])
        install.assert_called_once()
        start.assert_called_once()
        gate.assert_called_once()
        stop.assert_called_once()
        forbidden_launch.assert_not_called()
        forbidden_liveness.assert_not_called()
        forbidden_legacy.assert_not_called()
        context = seen["context"]
        self.assertEqual(context.seed_contract, ready_contract)  # type: ignore[union-attr]
        self.assertEqual(context.seed_install, seed_install)  # type: ignore[union-attr]
        self.assertEqual(context.native_session_binding, binding)  # type: ignore[union-attr]
        self.assertEqual(context.loader_gate, loader_gate)  # type: ignore[union-attr]
        self.assertEqual(context.tracked_ck3_pid, 4321)  # type: ignore[union-attr]
        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["loader_gate_executed"])
        self.assertTrue(report["gameplay_green_claimed"])
        self.assertEqual(report["phase2_seed_install"], seed_install)
        self.assertIsNone(report["native_session_liveness"])
        self.assertEqual(
            report["native_session_liveness_scope"],
            "not_applicable_phase2_promo_capture",
        )
        self.assertEqual(
            report["loader_gate_evidence"]["mode"], "phase2_promo_capture"
        )

    def test_legacy_promo_keeps_suspended_launch_without_phase2_plumbing(self) -> None:
        process = _FakeProcess(2468)
        session = SimpleNamespace(process=process, watchdog_pid=2469)
        bridge = SimpleNamespace(pipe_name=r"\\.\pipe\legacy-promo-unit")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "exclusive_launch_lock",
                        side_effect=lambda *_args, **_kwargs: nullcontext(),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "exclusive_state_lock",
                        side_effect=lambda *_args, **_kwargs: nullcontext(),
                    )
                )
                launch = stack.enter_context(
                    mock.patch.object(
                        capture, "launch_native_ck3", return_value=session
                    )
                )
                stop = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_tracked",
                        return_value={
                            "cleanup_proven": True,
                            "contract_errors": [],
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "wait_for_ocr_text")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.isolated, "dismiss_external_main_menu_popup"
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "navigate_lobby")
                )
                stack.enter_context(
                    mock.patch.object(capture.isolated, "wait_for_gameplay_hud")
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "ensure_game_paused")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "force_ck3_english_keyboard_layout",
                        return_value={"result": "GREEN"},
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.MarkerStream, "validate")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.acceptance.pyautogui,
                        "size",
                        return_value=SimpleNamespace(width=2560, height=1440),
                    )
                )
                legacy_scenario = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "run_scenario",
                        return_value={"result": "GREEN", "legacy": True},
                    )
                )
                phase2_calls = [
                    stack.enter_context(mock.patch.object(capture, name))
                    for name in (
                        "install_phase2_seed",
                        "start_phase2_native_session_supervisor",
                        "wait_for_phase2_native_session_binding",
                        "run_loader_gate",
                        "run_phase2_promo_capture_scenario",
                        "phase2_native_session_liveness_gate",
                    )
                ]
                report = capture.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    promo_capture=True,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "legacy-unit"}
                    },
                )

        launch.assert_called_once()
        stop.assert_called_once()
        legacy_scenario.assert_called_once()
        for phase2_call in phase2_calls:
            phase2_call.assert_not_called()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["native_launch_sequence"], "suspended_inject_resume")
        self.assertFalse(report["loader_gate_executed"])
        self.assertIsNone(report["phase2_seed_install"])
        self.assertIsNone(report["native_session_liveness"])
        self.assertIsNone(report["native_session_liveness_scope"])

    def test_loader_gate_labels_promo_and_runs_managed_phase2_checks(self) -> None:
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            userdir = root / "profile"
            artifacts.mkdir()
            userdir.mkdir()

            def record(name: str, result: object):
                def invoke(*_args: object, **_kwargs: object) -> object:
                    calls.append(name)
                    return copy.deepcopy(result)

                return invoke

            with (
                mock.patch.object(
                    capture,
                    "wait_for_phase2_seed_loader_stage",
                    side_effect=record("loader", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "native_loader_smoke_readiness",
                    side_effect=record("readiness", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "phase2_runtime_capability_preflight",
                    side_effect=record("capabilities", {"result": "GREEN"}),
                ) as capability,
                mock.patch.object(
                    capture,
                    "scan_loader_error_log",
                    side_effect=record("errors", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "verify_runtime_load_order",
                    side_effect=record("mounts", ["product", "fixture"]),
                ),
            ):
                evidence = capture.run_loader_gate(
                    SimpleNamespace(),
                    artifacts,
                    userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=False,
                    managed_restore_supervisor=True,
                    phase2_promo_capture=True,
                )
        self.assertEqual(
            calls,
            ["loader", "readiness", "capabilities", "errors", "mounts"],
        )
        self.assertEqual(evidence["mode"], "phase2_promo_capture")
        self.assertTrue(evidence["same_pid_gameplay_continuation_authorized"])
        self.assertTrue(
            capability.call_args.kwargs["managed_restore_supervisor"]
        )


if __name__ == "__main__":
    unittest.main()
