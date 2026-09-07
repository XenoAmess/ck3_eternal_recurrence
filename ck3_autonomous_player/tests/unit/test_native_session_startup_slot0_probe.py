from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import threading
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_session import (  # noqa: E402
    _native_session_locked,
    native_session,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402


def _config(root: Path) -> NativeBridgeLaunchConfig:
    dll = root / "bridge.dll"
    injector = root / "injector.exe"
    dll.touch()
    injector.touch()
    return NativeBridgeLaunchConfig(
        mode="native-headless",
        pipe_name=r"\\.\pipe\slot0-integration",
        dll_path=dll,
        injector_path=injector,
    )


class NativeSessionStartupSlot0ProbeTests(unittest.TestCase):
    def test_probe_is_strictly_opt_in_by_default(self) -> None:
        self.assertIsNone(
            inspect.signature(native_session).parameters[
                "startup_slot0_probe_output"
            ].default
        )
        self.assertIsNone(
            inspect.signature(_native_session_locked).parameters[
                "startup_slot0_probe_plan"
            ].default
        )

    def test_public_entry_prepares_probe_before_locked_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-native-") as temporary:
            root = Path(temporary)
            spec = SimpleNamespace(state_dir=root / "state", game_exe=root / "ck3.exe")
            config = _config(root)
            output = root / "probe.json"
            plan = mock.Mock()
            with mock.patch(
                "xar_autoplayer.native_session.prepare_startup_slot0_probe",
                return_value=plan,
            ) as prepare, mock.patch(
                "xar_autoplayer.native_session.exclusive_launch_lock",
                return_value=mock.MagicMock(),
            ), mock.patch(
                "xar_autoplayer.native_session.exclusive_state_lock",
                return_value=mock.MagicMock(),
            ), mock.patch(
                "xar_autoplayer.native_session._native_session_locked",
                return_value={"ok": True},
            ) as locked:
                report = native_session(
                    spec,
                    timeout_seconds=1,
                    native_bridge=config,
                    startup_slot0_probe_output=output,
                )

        self.assertEqual(report, {"ok": True})
        prepare.assert_called_once_with(spec.game_exe, output)
        self.assertIs(
            locked.call_args.kwargs["startup_slot0_probe_plan"], plan
        )

    def test_initial_process_only_is_probed_and_red_capture_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-locked-") as temporary:
            root = Path(temporary)
            spec = SimpleNamespace(
                state_dir=root / "state",
                profile_dir=root / "profile",
                game_exe=root / "ck3.exe",
            )
            process = mock.Mock()
            process.pid = 5252
            process.poll.return_value = None
            handle = SimpleNamespace(process=process)
            config = _config(root)
            controller = mock.Mock()
            controller.finish.return_value = {
                "capture_ok": False,
                "status": "probe_error",
            }
            plan = mock.Mock()
            plan.start.return_value = controller
            stop_event = threading.Event()
            stop_event.set()
            with mock.patch(
                "xar_autoplayer.native_session.launch", return_value=handle
            ), mock.patch(
                "xar_autoplayer.native_session.stop_tracked",
                return_value={"ok": True, "contract_errors": []},
            ), self.assertRaisesRegex(
                AgentError, "startup slot0 probe did not produce"
            ):
                _native_session_locked(
                    spec,
                    config,
                    1.0,
                    input_stream=None,
                    output_stream=None,
                    poll_interval_seconds=0.001,
                    stop_event=stop_event,
                    startup_slot0_probe_plan=plan,
                )

        plan.start.assert_called_once()
        self.assertEqual(plan.start.call_args.args, (5252,))
        self.assertEqual(plan.start.call_args.kwargs["launch_role"], "initial")
        controller.finish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
