#!/usr/bin/env python3
"""CK3-free focused tests for late promotion-source recovery."""

from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
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
        if importlib.util.find_spec(name) is not None:
            continue
        module = types.ModuleType(name)
        module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
        for attribute in names:
            setattr(module, attribute, None)
        sys.modules[name] = module


_install_optional_desktop_stubs()
sys.path.insert(0, str(ROOT / "tools"))

import recover_zg361_phase2_promotion_source_session as recovery  # noqa: E402
import resume_zg361_phase2_promotion_source_session as resume  # noqa: E402
import run_zhongguo_acceptance as runner  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _player_manager_seed_contract() -> dict[str, object]:
    return {
        "kind": runner.PHASE2_PLAYER_MANAGER_SEED_KIND,
        "seed_purpose": runner.PHASE2_PLAYER_MANAGER_SEED_PURPOSE,
        "ready": True,
        "status": "ready",
        "source": {"sha256": "a" * 64},
        "saved_state": {
            "played_character_id": 29037,
            "player_history_id": None,
        },
        "manager_entry": {
            "schema_version": 1,
            "manager_character_id": 29037,
            "reviewable_subject_character_id": 32904,
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


class _Driver:
    def __init__(
        self,
        *args: object,
        on_close: object = None,
        **kwargs: object,
    ) -> None:
        self.closed = False
        self.on_close = on_close

    def close(self) -> None:
        self.closed = True
        if callable(self.on_close):
            self.on_close()


class _Service:
    def __init__(self, *, checkpoint_failure: bool = False) -> None:
        self.checkpoint_failure = checkpoint_failure
        self.save_dir: Path | None = None
        self.save_calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "mode": runner.NATIVE_BRIDGE_MODE,
            "backend_id": "native-headless",
            "visual_fallback": False,
            "bridge_capabilities": ["game.command.save-checkpoint"],
            "action_steps": ["save-checkpoint"],
            "checkpoint_materialization": {"configured": True},
            "diagnostics": {
                "connected": True,
                "bridge_pid": 361247,
                "connection_generation": 1,
            },
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "native:247",
            "revision": 248,
            "native_revision": 247,
            "date_raw": 53204688,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 32904},
            "diagnostics": {
                "connected": True,
                "bridge_pid": 361247,
                "connection_generation": 1,
            },
            "active_event": {"instance_id": 204, "option_count": 1},
        }

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.save_calls += 1
        if expected_revision != 248:
            raise AssertionError("unexpected checkpoint revision")
        if self.checkpoint_failure:
            raise RuntimeError("mock checkpoint materialization failed")
        if self.save_dir is None:
            raise AssertionError("mock save directory was not configured")
        path = self.save_dir / "xar_checkpoint.ck3"
        payload = b"durable-recovery-unknown-event"
        path.write_bytes(payload)
        return {
            "accepted": True,
            "status": "submitted",
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "date_raw": 53204688,
                "episode_character_id": 32904,
                "episode_run_id": "native-32904-recovery-unit",
                "history_index": 1,
                "strategy": "native-autosave-command-v1",
            },
            "materialization": {"available": True},
        }


class RecoveryHarness:
    def __init__(
        self,
        *,
        unknown_interrupt: bool = False,
        known_contract_drift: bool = False,
        checkpoint_failure: bool = False,
        end_on_driver_close: bool = False,
        startup_shader_projection: object = None,
    ) -> None:
        self.unknown_interrupt = unknown_interrupt
        self.known_contract_drift = known_contract_drift
        self.service = _Service(checkpoint_failure=checkpoint_failure)
        self.started = False
        self.start_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.stopped = False
        self.process_checks: list[str] = []
        self.loader_calls: list[
            tuple[tuple[object, ...], dict[str, object]]
        ] = []
        self.bootstrap_calls: list[
            tuple[tuple[object, ...], dict[str, object]]
        ] = []
        self.startup_shader_projection = (
            {
                "result": "GREEN_STATIC",
                "projected": True,
            }
            if startup_shader_projection is None
            else startup_shader_projection
        )
        self.supervisor = {
            "session_done": threading.Event(),
            "session_state": {"report": None, "error": None},
        }
        on_close = (
            self._end_supervisor_on_driver_close
            if end_on_driver_close
            else None
        )
        self.driver = _Driver(on_close=on_close)

    def _end_supervisor_on_driver_close(self) -> None:
        self.supervisor["session_state"] = {
            "report": {"exit_reason": "process_exit"},
            "error": "native session ended during handoff",
        }
        self.supervisor["session_done"].set()

    def process_running(self, image: str) -> bool:
        self.process_checks.append(image)
        return False

    def bootstrap(self, profile: Path, *args: object, **kwargs: object) -> dict[str, object]:
        self.bootstrap_calls.append(((profile, *args), dict(kwargs)))
        for relative in ("logs", "save games", "mod", "mod-content/zhongguo_361"):
            (profile / relative).mkdir(parents=True, exist_ok=True)
        self.service.save_dir = profile / "save games"
        (profile / "logs" / "error.log").write_text("loader clean\n", encoding="utf-8")
        (profile / "logs" / "debug.log").write_text("loader clean\n", encoding="utf-8")
        return {
            "enabled_mods": [f"mod/{runner.PRODUCT_OUTER}"],
            "targets": {"product": profile / "mod-content" / "zhongguo_361"},
            "tree_sha256": {"product": "b" * 64},
            "manifest": {"projection": {"name": "current-full-tree"}},
            "particle2_startup_shader_projection": self.startup_shader_projection,
        }

    def start(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.started = True
        self.start_calls.append((args, dict(kwargs)))
        return self.supervisor

    def wait_binding(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {"bridge_pid": 361247, "connection_generation": 1}

    def loader(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.loader_calls.append((args, dict(kwargs)))
        if kwargs.get("phase2_promotion_source_capture_live") is not True:
            raise AssertionError("focused promotion loader gate was not selected")
        return {"result": "GREEN", "same_pid_gameplay_continuation_authorized": True}

    def entry(
        self, service: object, *args: object, **kwargs: object
    ) -> dict[str, object]:
        evidence = kwargs["evidence_out"]
        evidence.update(
            {
                "result": (
                    "RED"
                    if self.unknown_interrupt or self.known_contract_drift
                    else "GREEN"
                ),
                "timeline_origin_date_raw": recovery.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "player_character_id": 32904,
            }
        )
        if self.unknown_interrupt:
            snapshot = self.service.snapshot()
            evidence["unexpected_event"] = {
                "event_definition_key": "natural_disaster.9999",
                "snapshot": snapshot,
                "event": {
                    "snapshot_id": snapshot["snapshot_id"],
                    "revision": snapshot["revision"],
                    "native_revision": snapshot["native_revision"],
                    "date_raw": snapshot["date_raw"],
                    "player_character_id": 32904,
                    "connection_generation": 1,
                    "event_instance_id": 204,
                    "event_option_count": 1,
                },
                "query": {
                    "status": "available",
                    "current_event_window_context": {
                        "event_definition_key": "natural_disaster.9999"
                    },
                    "binding": {
                        "snapshot_id": snapshot["snapshot_id"],
                        "revision": snapshot["revision"],
                        "native_revision": snapshot["native_revision"],
                        "event_instance_id": 204,
                    },
                },
            }
            raise recovery.PromotionProductionEntryError("unknown interrupt")
        if self.known_contract_drift:
            raise recovery.PromotionKnownInterruptContractError(
                {
                    "classification": "known-interrupt-contract-drift",
                    "event_definition_key": "ep1_flavor.2040",
                    "date_raw": 53206056,
                    "event_instance_id": 205,
                    "failed_checks": ["scope:foreign_merchant"],
                    "selection_attempted": False,
                },
                "known promotion-timeline interrupt drifted",
            )
        return dict(evidence)

    def stop(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.stopped = True
        self.supervisor["session_done"].set()
        return {"result": "GREEN"}

    def bindings(self) -> recovery.RuntimeBindings:
        def resolve_bridge(
            dll: Path, injector: Path, pipe: str
        ) -> types.SimpleNamespace:
            return types.SimpleNamespace(
                mode=runner.NATIVE_BRIDGE_MODE,
                pipe_name=pipe,
                dll_path=dll,
                injector_path=injector,
            )

        return recovery.RuntimeBindings(
            process_running=self.process_running,
            verify_game=lambda path: {
                "game_dir": str(path),
                "version": runner.EXPECTED_GAME_VERSION,
                "executable_sha256": runner.EXPECTED_EXE_SHA256,
            },
            validate_seed_contract=lambda contract: None,
            bootstrap_userdir=self.bootstrap,
            configure_runtime_userdir=lambda profile: None,
            make_spec=lambda state, game: types.SimpleNamespace(
                state_dir=state, profile_dir=state / "profile", game_dir=game
            ),
            resolve_bridge=resolve_bridge,
            bridge_identity=lambda value: {
                "mode": value.mode,
                "pipe_name": value.pipe_name,
                "dll_path": str(value.dll_path),
                "dll_sha256": _sha256(value.dll_path),
                "injector_path": str(value.injector_path),
                "injector_sha256": _sha256(value.injector_path),
            },
            driver_factory=lambda *args, **kwargs: self.driver,
            service_factory=lambda driver: self.service,
            start_supervisor=self.start,
            wait_binding=self.wait_binding,
            loader_gate=self.loader,
            production_entry=self.entry,
            stop_supervisor=self.stop,
        )


class RecoveryTests(unittest.TestCase):
    def test_managed_loader_probe_ignores_missing_logs_until_session_done(
        self,
    ) -> None:
        supervisor = {
            "session_done": threading.Event(),
            "session_state": {"report": None, "error": None},
            "session_thread": threading.Thread(target=lambda: None),
        }

        self.assertIsNone(
            runner.phase2_native_session_terminal_probe(
                supervisor,
                tracked_ck3_pid=361247,
            )
        )

    def test_managed_loader_gate_failfasts_on_typed_process_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            userdir = root / "profile"
            artifacts.mkdir()
            (userdir / "logs").mkdir(parents=True)
            session_done = threading.Event()
            session_done.set()
            session_report = {
                "format_version": 1,
                "kind": "ck3_native_headless_session",
                "pid": 361247,
                "exit_reason": "process_exit",
                "process_exit_code": 1,
                "ok": False,
            }
            supervisor = {
                "session_done": session_done,
                "session_state": {
                    "report": session_report,
                    "error": None,
                },
                "session_thread": threading.Thread(target=lambda: None),
            }

            with self.assertRaisesRegex(
                runner.acceptance.RunnerError,
                "native_session_process_exit",
            ):
                runner.run_loader_gate(
                    _Service(),
                    artifacts,
                    userdir,
                    {},
                    tracked_ck3_pid=361247,
                    phase2_live_batch=False,
                    managed_restore_supervisor=True,
                    native_session_supervisor=supervisor,
                    phase2_promotion_source_capture_live=True,
                )

            gate = json.loads(
                (artifacts / "03_loader_gate.json").read_text(
                    encoding="utf-8"
                )
            )
            terminal = gate["append_only_loader_stage"]
            self.assertEqual(terminal["state"], "native_session_process_exit")
            self.assertEqual(terminal["process_exit_code"], 1)
            self.assertTrue(terminal["process_exit_nonzero"])
            self.assertEqual(
                terminal["native_session"]["session_report"],
                session_report,
            )
            rows = [
                json.loads(line)
                for line in (
                    artifacts / "01_phase2_loader_stage_progress.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(rows[-1]["state"], "native_session_process_exit")

    def test_phase2_supervisor_forwards_independent_warmup_bridge(self) -> None:
        final_bridge = runner.NativeBridgeLaunchConfig(
            mode=runner.NATIVE_BRIDGE_MODE,
            pipe_name=r"\\.\pipe\xar_ck3_bridge_zg361_" + "1" * 32,
            dll_path=Path("final.dll"),
            injector_path=Path("final.exe"),
        )
        warmup_bridge = runner.NativeBridgeLaunchConfig(
            mode=runner.NATIVE_BRIDGE_MODE,
            pipe_name=r"\\.\pipe\xar_ck3_bridge_zg361_" + "2" * 32,
            dll_path=Path("warmup.dll"),
            injector_path=Path("warmup.exe"),
        )
        probe_output = Path("state") / "diagnostics" / "slot0.json"
        with mock.patch.object(
            runner, "native_session", return_value={"result": "stopped"}
        ) as native_session_call:
            supervisor = runner.start_phase2_native_session_supervisor(
                types.SimpleNamespace(state_dir=Path("state")),
                final_bridge,
                runtime_timeout_seconds=43_200.0,
                frontend_first_load_save_name="autosave",
                frontend_first_timeout_seconds=7.0,
                frontend_first_warmup_bridge=warmup_bridge,
                startup_slot0_probe_output=probe_output,
            )
            supervisor["session_thread"].join(timeout=1.0)

        self.assertTrue(supervisor["session_done"].is_set())
        keywords = native_session_call.call_args.kwargs
        self.assertIs(keywords["native_bridge"], final_bridge)
        self.assertIs(
            keywords["frontend_first_warmup_bridge"], warmup_bridge
        )
        self.assertEqual(keywords["frontend_first_load_save_name"], "autosave")
        self.assertEqual(keywords["startup_slot0_probe_output"], probe_output)
        self.assertEqual(
            supervisor["startup_slot0_probe_output"],
            str(probe_output.resolve()),
        )
        self.assertEqual(keywords["timeout_seconds"], 43_200.0)
        self.assertEqual(supervisor["runtime_timeout_seconds"], 43_200.0)
        self.assertFalse(keywords["cold_start_checkpoint"])

    def test_phase2_supervisor_runtime_timeout_default_and_validation(self) -> None:
        bridge = runner.NativeBridgeLaunchConfig(
            mode=runner.NATIVE_BRIDGE_MODE,
            pipe_name=r"\\.\pipe\xar_ck3_bridge_zg361_" + "3" * 32,
            dll_path=Path("final.dll"),
            injector_path=Path("final.exe"),
        )
        with mock.patch.object(
            runner, "native_session", return_value={"result": "stopped"}
        ) as native_session_call:
            supervisor = runner.start_phase2_native_session_supervisor(
                types.SimpleNamespace(state_dir=Path("state")), bridge
            )
            supervisor["session_thread"].join(timeout=1.0)
        self.assertEqual(
            native_session_call.call_args.kwargs["timeout_seconds"],
            runner.PHASE2_SUPERVISOR_RUNTIME_TIMEOUT_S,
        )
        self.assertEqual(
            supervisor["runtime_timeout_seconds"],
            runner.PHASE2_SUPERVISOR_RUNTIME_TIMEOUT_S,
        )

        for invalid in (True, 0, -1, float("nan"), float("inf"), "3600"):
            with self.subTest(invalid=invalid):
                with mock.patch.object(runner, "native_session") as native_session:
                    with self.assertRaisesRegex(
                        runner.acceptance.RunnerError,
                        "runtime timeout must be finite and positive",
                    ):
                        runner.start_phase2_native_session_supervisor(
                            types.SimpleNamespace(state_dir=Path("state")),
                            bridge,
                            runtime_timeout_seconds=invalid,
                        )
                native_session.assert_not_called()

    def test_phase2_timeout_cleanup_is_cleanup_only_and_fail_closed(self) -> None:
        pipe = r"\\.\pipe\xar_ck3_bridge_zg361_" + "4" * 32

        def shutdown(pid: int) -> dict[str, object]:
            return {
                "ck3_pid": pid,
                "ok": True,
                "cleanup_proven": True,
                "tree_gone": True,
                "job_active_processes_final": 0,
                "final_ck3_inventory": {"processes": []},
                "watchdog_state_after": "absent",
                "control_files_absent": {
                    "pid": True,
                    "ready": True,
                    "watchdog_error": True,
                    "unsafe": True,
                },
                "contract_errors": [],
            }

        timeout_report = {
            "kind": "ck3_native_headless_session",
            "mode": runner.NATIVE_BRIDGE_MODE,
            "pipe": pipe,
            "pid": 4321,
            "exit_reason": "timeout",
            "process_exit_code": 1,
            "shutdown": shutdown(4321),
            "restart_count": 0,
            "restart_shutdowns": [],
            "ok": True,
        }
        disconnected = {
            "diagnostics": {
                "connected": False,
                "bridge_pid": None,
                "connection_generation": 0,
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            green_dir = root / "timeout-green"
            green_dir.mkdir()
            cleanup = runner.prove_phase2_native_session_cleanup(
                timeout_report,
                green_dir,
                initial_pid=4321,
                initial_generation=4,
                expected_pipe=pipe,
                scenario_evidence={},
                final_capabilities=disconnected,
                session_error=None,
                supervisor_stopped=True,
            )
            self.assertEqual(cleanup["result"], "GREEN")
            self.assertEqual(cleanup["acceptance_scope"], "cleanup_only")
            self.assertEqual(cleanup["session_result"], "TIMEOUT")
            self.assertEqual(cleanup["product_result"], "INCOMPLETE")
            self.assertTrue(cleanup["resume_required"])
            self.assertFalse(cleanup["timeout_accepted_as_gameplay_success"])
            self.assertTrue(cleanup["checks"]["session_exit_reason_timeout"])
            self.assertTrue(
                cleanup["checks"]["session_process_exit_code_recorded"]
            )
            self.assertTrue(cleanup["checks"]["final_capabilities_disconnected"])

            red_report = copy.deepcopy(timeout_report)
            red_report["shutdown"]["job_active_processes_final"] = 1
            red_dir = root / "timeout-red"
            red_dir.mkdir()
            with self.assertRaisesRegex(
                runner.acceptance.RunnerError,
                "initial_pid_shutdown_job_empty",
            ):
                runner.prove_phase2_native_session_cleanup(
                    red_report,
                    red_dir,
                    initial_pid=4321,
                    initial_generation=4,
                    expected_pipe=pipe,
                    scenario_evidence={},
                    final_capabilities=disconnected,
                    session_error=None,
                    supervisor_stopped=True,
                )
            red_evidence = json.loads(
                (red_dir / "09_phase2_native_session_cleanup.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(red_evidence["result"], "RED")
            self.assertFalse(
                red_evidence["checks"]["initial_pid_shutdown_job_empty"]
            )

            stop_report = copy.deepcopy(timeout_report)
            stop_report["exit_reason"] = "stop"
            stop_report["process_exit_code"] = None
            connected = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 4321,
                    "connection_generation": 4,
                }
            }
            stop_dir = root / "stop-green"
            stop_dir.mkdir()
            stop_cleanup = runner.prove_phase2_native_session_cleanup(
                stop_report,
                stop_dir,
                initial_pid=4321,
                initial_generation=4,
                expected_pipe=pipe,
                scenario_evidence={},
                final_capabilities=connected,
                session_error=None,
                supervisor_stopped=True,
            )
            self.assertEqual(stop_cleanup["result"], "GREEN")
            self.assertTrue(stop_cleanup["checks"]["session_exit_reason_stop"])
            self.assertTrue(stop_cleanup["checks"]["final_capabilities_connected"])
            self.assertNotIn("acceptance_scope", stop_cleanup)
            self.assertNotIn("timeout_accepted_as_gameplay_success", stop_cleanup)

    def test_tasklist_denial_uses_exact_toolhelp_fallback(self) -> None:
        denied = types.SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="ERROR: Access is denied",
        )
        with (
            mock.patch.object(recovery.subprocess, "run", return_value=denied),
            mock.patch.object(
                recovery,
                "_process_image_is_running_toolhelp",
                return_value=True,
            ) as fallback,
        ):
            self.assertTrue(recovery.process_image_is_running("ck3.exe"))
        fallback.assert_called_once_with("ck3.exe")

    def test_tasklist_and_toolhelp_failure_remains_fail_closed(self) -> None:
        denied = types.SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="ERROR: Access is denied",
        )
        with (
            mock.patch.object(recovery.subprocess, "run", return_value=denied),
            mock.patch.object(
                recovery,
                "_process_image_is_running_toolhelp",
                side_effect=OSError(5, "Access is denied"),
            ),
        ):
            with self.assertRaisesRegex(
                recovery.RecoveryError,
                "could not prove empty process slot",
            ):
                recovery.process_image_is_running("ck3.exe")

    def _arrange(self, root: Path) -> tuple[recovery.RecoveryConfig, Path]:
        source_profile = root / "source-profile"
        save_dir = source_profile / "save games"
        save_dir.mkdir(parents=True)
        source_save = save_dir / "autosave.ck3"
        source_save.write_bytes(b"late-R247-save")
        (source_profile / "pdx_settings.txt").write_text(
            "language=l_english\n", encoding="utf-8"
        )
        shadercache = source_profile / "shadercache"
        shadercache.mkdir()
        (shadercache / "warm.cache").write_bytes(b"warm")
        source_cell = root / "source-cell"
        source_cell.mkdir()
        (source_cell / "00_phase2_seed_install.json").write_text(
            json.dumps(
                {"result": "GREEN", "contract": _player_manager_seed_contract()}
            ),
            encoding="utf-8",
        )
        product = root / "current-product"
        product.mkdir()
        projection = root / "current-projection.json"
        projection.write_text("{}", encoding="utf-8")
        game = root / "game"
        game.mkdir()
        dll = root / "bridge.dll"
        injector = root / "xar_ck3_bridge_injector.exe"
        dll.write_bytes(b"dll")
        injector.write_bytes(b"injector")
        pipe = r"\\.\pipe\xar_ck3_bridge_zg361_" + "1" * 32
        return (
            recovery.RecoveryConfig(
                source_profile=source_profile,
                source_save=source_save,
                expected_source_save_sha256=_sha256(source_save),
                source_run_cell=source_cell,
                state_dir=root / "new-state",
                artifacts_dir=root / "new-source-cell",
                product_source=product,
                product_projection="current-full-tree",
                product_projection_manifest=projection,
                game_dir=game,
                bridge_dll=dll,
                bridge_injector=injector,
                bridge_pipe=pipe,
                timeout_seconds=1.0,
                frontend_timeout_seconds=1.0,
            ),
            source_save,
        )

    def _cli_arguments(self, config: recovery.RecoveryConfig) -> list[str]:
        return [
            "--source-profile",
            str(config.source_profile),
            "--source-save",
            str(config.source_save),
            "--expected-source-save-sha256",
            config.expected_source_save_sha256,
            "--source-run-cell",
            str(config.source_run_cell),
            "--state-dir",
            str(config.state_dir),
            "--artifacts-dir",
            str(config.artifacts_dir),
            "--product-source",
            str(config.product_source),
            "--product-projection",
            config.product_projection,
            "--product-projection-manifest",
            str(config.product_projection_manifest),
            "--game-dir",
            str(config.game_dir),
            "--bridge-dll",
            str(config.bridge_dll),
            "--bridge-injector",
            str(config.bridge_injector),
            "--bridge-pipe",
            config.bridge_pipe,
        ]

    def test_startup_mode_cli_defaults_and_fail_closed_choices(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            arguments = self._cli_arguments(config)

            parsed = recovery.parse_args(arguments)
            self.assertEqual(
                parsed.startup_mode,
                recovery.STARTUP_MODE_FRONTEND_FIRST,
            )
            self.assertIsNone(parsed.startup_slot0_probe_output)
            probe_output = config.artifacts_dir / "diagnostics" / "slot0.json"
            parsed = recovery.parse_args(
                arguments
                + ["--startup-slot0-probe-output", str(probe_output)]
            )
            self.assertEqual(parsed.startup_slot0_probe_output, probe_output)
            parsed = recovery.parse_args(
                arguments
                + [
                    "--startup-mode",
                    recovery.STARTUP_MODE_CONTINUE_LAST_SAVE,
                ]
            )
            self.assertEqual(
                parsed.startup_mode,
                recovery.STARTUP_MODE_CONTINUE_LAST_SAVE,
            )
            warmup_dll = Path(temporary) / "warmup.dll"
            warmup_injector = Path(temporary) / "warmup-injector.exe"
            warmup_arguments = [
                "--startup-mode",
                recovery.STARTUP_MODE_BRIDGE_FRONTEND_FIRST,
                "--warmup-bridge-dll",
                str(warmup_dll),
                "--warmup-bridge-injector",
                str(warmup_injector),
                "--warmup-bridge-pipe",
                r"\\.\pipe\xar_ck3_bridge_zg361_" + "2" * 32,
                "--expected-warmup-bridge-dll-sha256",
                "a" * 64,
                "--expected-warmup-bridge-injector-sha256",
                "b" * 64,
            ]
            parsed = recovery.parse_args(arguments + warmup_arguments)
            self.assertEqual(
                parsed.startup_mode,
                recovery.STARTUP_MODE_BRIDGE_FRONTEND_FIRST,
            )
            self.assertEqual(parsed.warmup_bridge_dll, warmup_dll)
            with self.assertRaises(SystemExit) as raised:
                recovery.parse_args(arguments + ["--startup-mode", "automatic"])
            self.assertEqual(raised.exception.code, 2)

    def test_invalid_programmatic_startup_mode_fails_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness()
            with self.assertRaisesRegex(recovery.RecoveryError, "startup mode"):
                recovery.run(
                    replace(config, startup_mode="automatic"),
                    runtime=harness.bindings(),
                )
            self.assertFalse(harness.started)

    def test_startup_slot0_probe_rejects_path_outside_fresh_run_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            harness = RecoveryHarness()
            with self.assertRaisesRegex(
                recovery.RecoveryError,
                "must be inside the fresh state or artifacts directory",
            ):
                recovery.run(
                    replace(
                        config,
                        startup_slot0_probe_output=root / "outside.json",
                    ),
                    runtime=harness.bindings(),
                )
            self.assertFalse(harness.started)

    def test_startup_slot0_probe_rechecks_new_target_immediately_prelaunch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            harness = RecoveryHarness()
            # report.json is absent at the initial fresh-root gate, then the
            # recovery creates it before the exact startup contract is frozen.
            report = recovery.run(
                replace(
                    config,
                    startup_slot0_probe_output=(
                        config.artifacts_dir / "report.json"
                    ),
                ),
                runtime=harness.bindings(),
            )
            self.assertEqual(report["result"], "RED")
            self.assertIn(
                "must not exist before launch", report["failure_reason"]
            )
            self.assertFalse(harness.started)

    def test_startup_slot0_probe_forwards_fresh_artifact_and_freezes_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            output = config.artifacts_dir / "diagnostics" / "slot0.json"
            config = replace(config, startup_slot0_probe_output=output)
            harness = RecoveryHarness()
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "GREEN")
            _args, start_keywords = harness.start_calls[0]
            self.assertEqual(
                start_keywords["startup_slot0_probe_output"], output.resolve()
            )
            probe = report["startup"]["prelaunch_boundary"][
                "startup_slot0_probe"
            ]
            self.assertTrue(probe["enabled"])
            self.assertEqual(probe["contained_by"], "artifacts_dir")
            self.assertEqual(probe["output_path"], str(output.resolve()))
            self.assertTrue(probe["target_absent"])
            self.assertTrue(probe["temporary_target_absent"])
            supervisor_call = report["startup"]["supervisor_call"]
            self.assertTrue(
                supervisor_call["startup_slot0_probe_output_passed"]
            )
            self.assertEqual(
                supervisor_call["startup_slot0_probe_output"],
                str(output.resolve()),
            )

    def test_green_recovery_retains_resume_compatible_managed_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness()
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "GREEN")
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertTrue(harness.started)
            _loader_args, loader_keywords = harness.loader_calls[0]
            self.assertIs(
                loader_keywords["native_session_supervisor"],
                harness.supervisor,
            )
            _bootstrap_args, bootstrap_keywords = harness.bootstrap_calls[0]
            self.assertEqual(bootstrap_keywords["game_dir"], config.game_dir.resolve())
            _args, start_keywords = harness.start_calls[0]
            self.assertEqual(
                start_keywords,
                {
                    "frontend_first_load_save_name": "autosave",
                    "frontend_first_timeout_seconds": 1.0,
                },
            )
            self.assertEqual(
                report["startup"]["mode"],
                recovery.STARTUP_MODE_FRONTEND_FIRST,
            )
            self.assertFalse(
                report["startup"]["supervisor_call"][
                    "cold_start_checkpoint_argument_passed"
                ]
            )
            self.assertTrue(
                report["startup"]["native_session_contract"][
                    "suspended_pre_resume_bridge_injection"
                ]
            )
            self.assertEqual(
                report["startup"]["native_session_contract"][
                    "bridge_injection_target"
                ],
                "final-save-load-process",
            )
            self.assertFalse(harness.stopped)
            self.assertTrue(harness.driver.closed)
            self.assertEqual(
                _sha256(config.state_dir / "profile" / "save games" / "autosave.ck3"),
                _sha256(source_save),
            )
            self.assertTrue(
                (config.state_dir / "profile" / "shadercache" / "warm.cache").is_file()
            )
            inputs = resume.validate_retained_session_inputs(
                state_dir=config.state_dir,
                pipe_name=config.bridge_pipe,
                source_run_cell=config.artifacts_dir,
            )
            self.assertTrue(all(inputs["checks"].values()))
            self.assertTrue((config.artifacts_dir / "final_error.log").is_file())
            self.assertTrue((config.artifacts_dir / "final_debug.log").is_file())
            self.assertEqual(harness.process_checks.count("ck3.exe"), 2)
            self.assertEqual(
                harness.process_checks.count(config.bridge_injector.name), 2
            )

    def test_startup_shader_projection_failure_is_red_without_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(
                startup_shader_projection={
                    "result": "OFFLINE_UNAVAILABLE",
                    "projected": False,
                }
            )
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertIn(
                "projection was not GREEN_STATIC",
                report["failure_reason"],
            )
            self.assertFalse(harness.started)

    def test_continue_last_save_omits_frontend_and_cold_checkpoint_arguments(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            config = replace(
                config,
                startup_mode=recovery.STARTUP_MODE_CONTINUE_LAST_SAVE,
            )
            harness = RecoveryHarness()
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "GREEN")
            self.assertEqual(len(harness.start_calls), 1)
            _args, start_keywords = harness.start_calls[0]
            self.assertEqual(start_keywords, {})
            startup = report["startup"]
            self.assertEqual(
                startup["mode"], recovery.STARTUP_MODE_CONTINUE_LAST_SAVE
            )
            self.assertTrue(
                startup["native_session_contract"]["continue_last_save"]
            )
            self.assertFalse(
                startup["native_session_contract"]["cold_start_checkpoint"]
            )
            self.assertTrue(
                startup["native_session_contract"][
                    "suspended_pre_resume_bridge_injection"
                ]
            )
            self.assertEqual(
                startup["native_session_contract"]["bridge_injection_target"],
                "initial-continue-last-save-process",
            )
            self.assertTrue(
                startup["prelaunch_boundary"]["last_save"][
                    "byte_copy_of_autosave"
                ]
            )

    def test_bridge_frontend_first_hash_preflights_and_forwards_two_bridges(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            warmup_dll = root / "freeze165b" / "xar_ck3_bridge.dll"
            warmup_injector = (
                root / "freeze165b" / "xar_ck3_bridge_injector.exe"
            )
            warmup_dll.parent.mkdir()
            warmup_dll.write_bytes(b"freeze165b-dll")
            warmup_injector.write_bytes(b"freeze165b-injector")
            warmup_pipe = r"\\.\pipe\xar_ck3_bridge_zg361_" + "2" * 32
            config = replace(
                config,
                startup_mode=recovery.STARTUP_MODE_BRIDGE_FRONTEND_FIRST,
                warmup_bridge_dll=warmup_dll,
                warmup_bridge_injector=warmup_injector,
                warmup_bridge_pipe=warmup_pipe,
                expected_warmup_bridge_dll_sha256=_sha256(warmup_dll),
                expected_warmup_bridge_injector_sha256=_sha256(warmup_injector),
            )
            harness = RecoveryHarness()
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "GREEN")
            _args, start_keywords = harness.start_calls[0]
            self.assertEqual(
                set(start_keywords),
                {
                    "frontend_first_load_save_name",
                    "frontend_first_timeout_seconds",
                    "frontend_first_warmup_bridge",
                },
            )
            warmup_bridge = start_keywords["frontend_first_warmup_bridge"]
            self.assertEqual(warmup_bridge.pipe_name, warmup_pipe)
            self.assertEqual(warmup_bridge.dll_path, warmup_dll.resolve())
            startup = report["startup"]
            self.assertTrue(
                startup["native_session_contract"]["warmup_bridge_injection"]
            )
            self.assertEqual(
                startup["native_session_contract"]["warmup_bridge"][
                    "dll_sha256"
                ],
                _sha256(warmup_dll),
            )
            self.assertEqual(
                startup["native_session_contract"]["final_save_load_bridge"][
                    "dll_sha256"
                ],
                _sha256(config.bridge_dll),
            )

    def test_bridge_frontend_first_rejects_hash_drift_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            warmup_dll = root / "warmup.dll"
            warmup_injector = root / "warmup-injector.exe"
            warmup_dll.write_bytes(b"dll")
            warmup_injector.write_bytes(b"injector")
            config = replace(
                config,
                startup_mode=recovery.STARTUP_MODE_BRIDGE_FRONTEND_FIRST,
                warmup_bridge_dll=warmup_dll,
                warmup_bridge_injector=warmup_injector,
                warmup_bridge_pipe=(
                    r"\\.\pipe\xar_ck3_bridge_zg361_" + "2" * 32
                ),
                expected_warmup_bridge_dll_sha256="0" * 64,
                expected_warmup_bridge_injector_sha256=_sha256(warmup_injector),
            )
            harness = RecoveryHarness()
            with self.assertRaisesRegex(recovery.RecoveryError, "SHA-256 mismatch"):
                recovery.run(config, runtime=harness.bindings())
            self.assertFalse(harness.started)

    def test_bridge_frontend_first_rejects_final_pipe_reuse_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _source_save = self._arrange(root)
            warmup_dll = root / "warmup.dll"
            warmup_injector = root / "warmup-injector.exe"
            warmup_dll.write_bytes(b"dll")
            warmup_injector.write_bytes(b"injector")
            config = replace(
                config,
                startup_mode=recovery.STARTUP_MODE_BRIDGE_FRONTEND_FIRST,
                warmup_bridge_dll=warmup_dll,
                warmup_bridge_injector=warmup_injector,
                warmup_bridge_pipe=config.bridge_pipe.upper(),
                expected_warmup_bridge_dll_sha256=_sha256(warmup_dll),
                expected_warmup_bridge_injector_sha256=_sha256(warmup_injector),
            )
            harness = RecoveryHarness()
            with self.assertRaisesRegex(recovery.RecoveryError, "must be distinct"):
                recovery.run(config, runtime=harness.bindings())
            self.assertFalse(harness.started)

    def test_fail_closed_unknown_interrupt_is_retained_without_gameplay_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(unknown_interrupt=True)
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertTrue(report["unknown_interrupt_retention"])
            self.assertTrue(report["unexpected_event_durable_recovery_ready"])
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertFalse(harness.stopped)
            self.assertTrue(harness.driver.closed)
            self.assertEqual(harness.service.save_calls, 1)
            self.assertTrue(
                (
                    config.state_dir
                    / "profile"
                    / "save games"
                    / "xar_checkpoint.ck3"
                ).is_file()
            )
            self.assertTrue(report["mcp_only"])
            self.assertFalse(report["ocr_used"])
            self.assertFalse(report["coordinates_used"])
            self.assertFalse(report["console_used"])
            retention = json.loads(
                (config.artifacts_dir / "09_phase2_native_session_retained.json").read_text(
                    encoding="utf-8-sig"
                )
            )
            self.assertEqual(retention["result"], "RETAINED")
            self.assertTrue(retention["durable_recovery_ready"])
            self.assertEqual(
                retention["reason"],
                "fail_closed_unknown_interrupt_recovery_boundary",
            )

    def test_checkpoint_failure_retains_healthy_unknown_event_without_durable_claim(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(
                unknown_interrupt=True,
                checkpoint_failure=True,
            )
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertTrue(report["unknown_interrupt_retention"])
            self.assertFalse(report["unexpected_event_durable_recovery_ready"])
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertFalse(harness.stopped)
            self.assertTrue(harness.driver.closed)
            self.assertEqual(harness.service.save_calls, 1)
            checkpoint = report["unexpected_event_durable_checkpoint"]
            self.assertEqual(checkpoint["result"], "RED")
            self.assertFalse(checkpoint["durable_recovery_ready"])
            self.assertIn("mock checkpoint", checkpoint["failure_reason"])
            retention = json.loads(
                (
                    config.artifacts_dir
                    / "09_phase2_native_session_retained.json"
                ).read_text(encoding="utf-8-sig")
            )
            self.assertEqual(retention["result"], "RETAINED")
            self.assertFalse(retention["durable_recovery_ready"])

    def test_input_free_known_contract_drift_retains_healthy_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(known_contract_drift=True)
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertTrue(report["known_interrupt_contract_retention"])
            self.assertFalse(report["unknown_interrupt_retention"])
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertFalse(harness.stopped)
            self.assertTrue(harness.driver.closed)
            self.assertEqual(harness.service.save_calls, 0)
            failure = report["entry"]["known_interrupt_contract_failure"]
            self.assertEqual(
                failure["classification"], "known-interrupt-contract-drift"
            )
            self.assertFalse(failure["selection_attempted"])
            retention = json.loads(
                (
                    config.artifacts_dir
                    / "09_phase2_native_session_retained.json"
                ).read_text(encoding="utf-8-sig")
            )
            self.assertEqual(retention["result"], "RETAINED")
            self.assertEqual(
                retention["reason"],
                "fail_closed_known_interrupt_contract_recovery_boundary",
            )

    def test_supervisor_exit_during_driver_close_revokes_retention_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(end_on_driver_close=True)
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertFalse(report["session_retained_for_resume_client"])
            self.assertFalse(harness.stopped)
            self.assertTrue(report["session_state"]["session_done"])
            self.assertIn("ended before final", report["failure_reason"])
            retention = json.loads(
                (config.artifacts_dir / "09_phase2_native_session_retained.json").read_text(
                    encoding="utf-8-sig"
                )
            )
            self.assertEqual(retention["result"], "RED")
            self.assertFalse(retention["reconnect_authorized"])
            self.assertTrue(retention["process_restart_required"])
            self.assertTrue(retention["session_state"]["session_done"])
            session_state = json.loads(
                (config.artifacts_dir / "10_phase2_native_session_state.json").read_text(
                    encoding="utf-8-sig"
                )
            )
            self.assertTrue(session_state["session_done"])


if __name__ == "__main__":
    unittest.main()
