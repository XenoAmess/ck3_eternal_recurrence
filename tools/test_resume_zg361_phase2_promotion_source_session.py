#!/usr/bin/env python3
"""CK3-free retained promotion-source diagnostic regression tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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

import resume_zg361_phase2_promotion_source_session as client  # noqa: E402
import zg361_phase2_promotion_source_production_entry as entry  # noqa: E402


PREFIX = b"[11:00:00][I][unit.cpp:1]: source client boundary\n"
PROJECT_ERROR = (
    b"[11:01:00][E][pdx_data_factory.cpp:1364]: Failed to find type "
    b"'scope:zg361_ch_a_event_subject'\n"
    b"[11:01:00][E][pdx_data_localize.cpp:146]: Data error in loc string "
    b"'zg361ch.m001.desc'\n"
)


class _Driver:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class RetainedRuntimeDiagnosticTests(unittest.TestCase):
    def _arrange_source(self, root: Path) -> tuple[Path, Path, str]:
        state = root / "state"
        profile = state / "profile"
        logs = profile / "logs"
        logs.mkdir(parents=True)
        cell = root / "source-cell"
        cell.mkdir()
        pipe = r"\\.\pipe\retained-diagnostic-unit"
        (cell / "09_phase2_native_session_retained.json").write_text(
            json.dumps(
                {
                    "result": "RETAINED",
                    "reconnect_authorized": True,
                    "process_restart_required": False,
                    "state_dir": str(state.resolve()),
                    "profile_dir": str(profile.resolve()),
                    "pipe": pipe,
                    "bridge_pid": 361116,
                }
            ),
            encoding="utf-8",
        )
        (cell / "00_phase2_seed_install.json").write_text(
            json.dumps(
                {
                    "result": "GREEN",
                    "contract": {
                        "ready": True,
                        "status": "ready",
                        "source": {"sha256": "a" * 64},
                    },
                }
            ),
            encoding="utf-8",
        )
        (cell / "03_loader_gate.json").write_text(
            json.dumps({"result": "GREEN"}), encoding="utf-8"
        )
        for name in ("error.log", "debug.log"):
            (cell / f"final_{name}").write_bytes(PREFIX)
            (logs / name).write_bytes(PREFIX + PROJECT_ERROR)
        return state, cell, pipe

    def test_source_cold_offsets_do_not_rebaseline_at_reconnect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, _pipe = self._arrange_source(root)
            offsets, evidence = client.source_cold_runtime_diagnostic_offsets(
                source_run_cell=cell,
                profile_dir=state / "profile",
            )

        self.assertEqual(offsets["error.log"], len(PREFIX))
        self.assertEqual(offsets["debug.log"], len(PREFIX))
        self.assertEqual(
            evidence["reconnect_observed_offsets"]["error.log"],
            len(PREFIX + PROJECT_ERROR),
        )
        self.assertEqual(
            evidence["reconnect_observed_offsets"]["debug.log"],
            len(PREFIX + PROJECT_ERROR),
        )

    def test_error_and_debug_mirror_is_one_product_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, _pipe = self._arrange_source(root)
            offsets, _evidence = client.source_cold_runtime_diagnostic_offsets(
                source_run_cell=cell,
                profile_dir=state / "profile",
            )
            blocking, warnings = client.retained_runtime_project_diagnostics(
                state / "profile", offsets
            )

        self.assertEqual(len(blocking), 1)
        self.assertIn("zg361ch.m001.desc", blocking[0])
        self.assertEqual(warnings, [])

    def test_entry_probe_preempts_absolute_550_day_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": (
                    entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW
                    + entry.MAX_ADVANCE_DAYS * entry.HOURS_PER_DAY
                    + 1
                ),
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )
            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )

        self.assertEqual(report["result"], "RED")
        self.assertIn("1 product runtime diagnostic(s)", report["error_reason"])
        self.assertIn("zg361ch.m001.desc", report["error_reason"])
        self.assertNotIn("550-day", report["error_reason"])
        diagnostics = report["runtime_diagnostics"]
        self.assertEqual(diagnostics["blocking_diagnostic_count"], 1)
        self.assertGreaterEqual(diagnostics["scan_count"], 2)

    def test_terminal_scan_overrides_entry_timeout_that_skipped_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, cell, pipe = self._arrange_source(root)
            logs = state / "profile" / "logs"
            for name in ("error.log", "debug.log"):
                (logs / name).write_bytes(PREFIX)
            artifacts = root / "artifacts"
            snapshot = {
                "snapshot_id": "native:116",
                "native_revision": 116,
                "revision": 1,
                "date_raw": entry.PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
                "map_ready": True,
                "paused": True,
                "speed": 5,
                "played_character": {"character_id": 29037},
                "diagnostics": {"connection_generation": 1},
            }
            capabilities = {
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 361116,
                    "connection_generation": 1,
                }
            }
            service = types.SimpleNamespace(
                snapshot=lambda: dict(snapshot),
                capabilities=lambda: dict(capabilities),
            )

            def timeout_after_writing_error(*args: object, **kwargs: object) -> None:
                for name in ("error.log", "debug.log"):
                    with (logs / name).open("ab") as handle:
                        handle.write(PROJECT_ERROR)
                raise entry.PromotionProductionEntryError(
                    "promotion path exceeded its 550-day product observation bound"
                )

            with (
                mock.patch.object(client, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    client, "GameplayBridgeService", return_value=service
                ),
                mock.patch.object(
                    client,
                    "wait_for_retained_session_reconnect",
                    return_value=(capabilities, snapshot),
                ),
                mock.patch.object(
                    client,
                    "retained_pid_lineage_evidence",
                    return_value={"result": "GREEN", "restart_count": 0},
                ),
                mock.patch.object(
                    client,
                    "enter_promotion_source_checkpoint_v1",
                    side_effect=timeout_after_writing_error,
                ),
            ):
                report = client.run(
                    state_dir=state,
                    pipe_name=pipe,
                    source_run_cell=cell,
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                )
            persisted = json.loads(
                (artifacts / "02_retained_runtime_diagnostics.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(report["result"], "RED")
        self.assertIn("1 product runtime diagnostic(s)", report["error_reason"])
        self.assertNotIn("550-day", report["error_reason"])
        self.assertEqual(persisted["blocking_diagnostic_count"], 1)


if __name__ == "__main__":
    unittest.main()
