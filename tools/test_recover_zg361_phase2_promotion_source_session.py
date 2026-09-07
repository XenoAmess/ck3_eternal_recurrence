#!/usr/bin/env python3
"""CK3-free focused tests for late promotion-source recovery."""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest


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
    def capabilities(self) -> dict[str, object]:
        return {
            "mode": runner.NATIVE_BRIDGE_MODE,
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
            "date_raw": 53204688,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 32904},
        }


class RecoveryHarness:
    def __init__(
        self,
        *,
        unknown_interrupt: bool = False,
        end_on_driver_close: bool = False,
    ) -> None:
        self.unknown_interrupt = unknown_interrupt
        self.service = _Service()
        self.started = False
        self.stopped = False
        self.process_checks: list[str] = []
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
        for relative in ("logs", "save games", "mod", "mod-content/zhongguo_361"):
            (profile / relative).mkdir(parents=True, exist_ok=True)
        (profile / "logs" / "error.log").write_text("loader clean\n", encoding="utf-8")
        (profile / "logs" / "debug.log").write_text("loader clean\n", encoding="utf-8")
        return {
            "enabled_mods": [f"mod/{runner.PRODUCT_OUTER}"],
            "targets": {"product": profile / "mod-content" / "zhongguo_361"},
            "tree_sha256": {"product": "b" * 64},
            "manifest": {"projection": {"name": "current-full-tree"}},
        }

    def start(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.started = True
        if kwargs.get("frontend_first_load_save_name") != "autosave":
            raise AssertionError("recovery did not use frontend-first autosave")
        return self.supervisor

    def wait_binding(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {"bridge_pid": 361247, "connection_generation": 1}

    def loader(self, *args: object, **kwargs: object) -> dict[str, object]:
        if kwargs.get("phase2_promotion_source_capture_live") is not True:
            raise AssertionError("focused promotion loader gate was not selected")
        return {"result": "GREEN", "same_pid_gameplay_continuation_authorized": True}

    def entry(
        self, service: object, *args: object, **kwargs: object
    ) -> dict[str, object]:
        evidence = kwargs["evidence_out"]
        evidence.update(
            {
                "result": "RED" if self.unknown_interrupt else "GREEN",
                "timeline_origin_date_raw": recovery.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "player_character_id": 32904,
            }
        )
        if self.unknown_interrupt:
            evidence["unexpected_event"] = {
                "event_definition_key": "natural_disaster.9999"
            }
            raise recovery.PromotionProductionEntryError("unknown interrupt")
        return dict(evidence)

    def stop(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.stopped = True
        self.supervisor["session_done"].set()
        return {"result": "GREEN"}

    def bindings(self) -> recovery.RuntimeBindings:
        bridge = types.SimpleNamespace(
            mode=runner.NATIVE_BRIDGE_MODE,
            pipe_name=r"\\.\pipe\xar_ck3_bridge_zg361_" + "1" * 32,
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
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
            resolve_bridge=lambda dll, injector, pipe: bridge,
            bridge_identity=lambda value: {
                "mode": value.mode,
                "pipe_name": value.pipe_name,
                "dll_path": str(value.dll_path),
                "injector_path": str(value.injector_path),
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

    def test_green_recovery_retains_resume_compatible_managed_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness()
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "GREEN")
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertTrue(harness.started)
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

    def test_fail_closed_unknown_interrupt_is_retained_without_gameplay_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, _source_save = self._arrange(Path(temporary))
            harness = RecoveryHarness(unknown_interrupt=True)
            report = recovery.run(config, runtime=harness.bindings())

            self.assertEqual(report["result"], "RED")
            self.assertTrue(report["unknown_interrupt_retention"])
            self.assertTrue(report["session_retained_for_resume_client"])
            self.assertFalse(harness.stopped)
            self.assertTrue(harness.driver.closed)
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
            self.assertEqual(
                retention["reason"],
                "fail_closed_unknown_interrupt_recovery_boundary",
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
