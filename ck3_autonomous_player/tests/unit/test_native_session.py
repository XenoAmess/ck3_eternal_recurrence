from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.environment import write_json_atomic  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_session import (  # noqa: E402
    _native_session_locked,
    native_session,
    validate_episode_seed_for_state,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402


def _config(root: Path, mode: str = "native-headless") -> NativeBridgeLaunchConfig:
    dll = root / "xar_ck3_bridge.dll"
    injector = root / "xar_ck3_bridge_injector.exe"
    dll.touch()
    injector.touch()
    return NativeBridgeLaunchConfig(
        mode=mode,
        pipe_name=r"\\.\pipe\native-session-test",
        dll_path=dll,
        injector_path=injector,
    )


class NativeSessionModeTests(unittest.TestCase):
    def test_parser_exposes_native_session(self) -> None:
        args = cli.parser().parse_args(
            [
                "--bridge-mode",
                "native-headless",
                "native-session",
                "--timeout",
                "7",
                "--cold-start-checkpoint",
            ]
        )
        self.assertEqual(args.command, "native-session")
        self.assertEqual(args.bridge_mode, "native-headless")
        self.assertEqual(args.timeout, 7)
        self.assertTrue(args.cold_start_checkpoint)

    def test_native_session_rejects_hybrid_fallback_before_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-native-session-") as temporary:
            config = _config(Path(temporary), mode="hybrid-fallback")
            spec = SimpleNamespace(
                state_dir=Path(temporary) / "state",
                game_exe=Path(temporary) / "ck3.exe",
            )
            with mock.patch(
                "xar_autoplayer.native_session.launch"
            ) as launch_mock, self.assertRaisesRegex(
                AgentError, "requires --bridge-mode native-headless"
            ):
                native_session(spec, timeout_seconds=1, native_bridge=config)
        launch_mock.assert_not_called()

    def test_import_does_not_load_visual_or_input_modules(self) -> None:
        script = (
            "import sys; "
            f"sys.path.insert(0, {str(PACKAGE_ROOT)!r}); "
            "import xar_autoplayer.native_session; "
            "blocked=('xar_autoplayer.vision','xar_autoplayer.control',"
            "'xar_autoplayer.opening_smoke','xar_autoplayer.menu_smoke'); "
            "loaded=[n for n in sys.modules if n.startswith(blocked)]; "
            "assert not loaded, loaded"
        )
        result = subprocess.run(
            [sys.executable, "-I", "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class NativeSessionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-native-session-lifecycle-"
        )
        root = Path(self.temporary.name)
        self.spec = SimpleNamespace(
            state_dir=root,
            profile_dir=root / "profile",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_episode_seed_preflight_binds_metadata_to_exact_bytes(self) -> None:
        payload = b"immutable next episode seed"
        seed_path = (
            self.spec.profile_dir / "save games" / "xar_episode_seed.ck3"
        )
        seed_path.parent.mkdir(parents=True)
        seed_path.write_bytes(payload)
        metadata_path = (
            self.spec.state_dir / "native-session" / "episode-seed.json"
        )
        write_json_atomic(
            metadata_path,
            {
                "format_version": 1,
                "name": "xar_episode_seed.ck3",
                "path": str(seed_path.resolve()),
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "date_raw": 53_168_784,
                "character_id": 707,
                "source_run_id": "native-707-source",
                "source_checkpoint_name": "xar_checkpoint.ck3",
                "immutable": True,
            },
        )

        seed = validate_episode_seed_for_state(self.spec)

        self.assertEqual(seed["path"], str(seed_path.resolve()))
        self.assertEqual(seed["metadata_path"], str(metadata_path.resolve()))
        self.assertEqual(seed["size"], len(payload))
        self.assertEqual(seed["date_raw"], 53_168_784)

        seed_path.write_bytes(payload + b" changed")
        with self.assertRaisesRegex(AgentError, "immutable metadata"):
            validate_episode_seed_for_state(self.spec)

    def test_status_then_stop_uses_native_launch_and_tracked_cleanup(self) -> None:
        process = mock.Mock()
        process.pid = 4242
        process.poll.return_value = None
        handle = SimpleNamespace(process=process)
        shutdown = {"ok": True, "contract_errors": []}
        output = io.StringIO()
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\native-session-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        with mock.patch(
            "xar_autoplayer.native_session.launch", return_value=handle
        ) as launch_mock, mock.patch(
            "xar_autoplayer.native_session.stop_tracked", return_value=shutdown
        ) as stop_mock:
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=io.StringIO("status\nstop\n"),
                output_stream=output,
                poll_interval_seconds=0.001,
            )

        launch_mock.assert_called_once_with(
            mock.ANY,
            native_bridge=config,
            continue_last_save=True,
        )
        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(report["exit_reason"], "stop")
        self.assertEqual(report["mode"], "native-headless")
        self.assertEqual(report["pipe"], config.pipe_name)
        self.assertTrue(report["ok"])
        lines = output.getvalue().splitlines()
        self.assertTrue(any('"type": "native_session_ready"' in line for line in lines))
        self.assertTrue(any('"type": "native_session_status"' in line for line in lines))

    def test_pre_set_stop_event_uses_tracked_cleanup_once(self) -> None:
        process = mock.Mock()
        process.pid = 4243
        process.poll.return_value = None
        handle = SimpleNamespace(process=process)
        shutdown = {"ok": True, "contract_errors": []}
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\native-session-stop-event-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        stop_event = threading.Event()
        stop_event.set()

        with mock.patch(
            "xar_autoplayer.native_session.launch", return_value=handle
        ), mock.patch(
            "xar_autoplayer.native_session.stop_tracked", return_value=shutdown
        ) as stop_mock:
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.001,
                stop_event=stop_event,
            )

        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(report["exit_reason"], "stop")
        self.assertTrue(report["ok"])

    def test_explicit_cold_start_launches_exact_xar_checkpoint(self) -> None:
        process = mock.Mock()
        process.pid = 4250
        process.poll.return_value = None
        handle = SimpleNamespace(process=process)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\cold-start-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        checkpoint_payload = b"explicit cold checkpoint"
        checkpoint_path = (
            self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        )
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint_path.write_bytes(checkpoint_payload)
        checkpoint_sha256 = hashlib.sha256(checkpoint_payload).hexdigest()
        checkpoint = {
            "name": "xar_checkpoint.ck3",
            "size": len(checkpoint_payload),
            "sha256": checkpoint_sha256,
            "date_raw": 53_168_784,
            "history_index": 1,
            "episode_character_id": 707,
            "episode_run_id": "native-707-existing",
        }
        write_json_atomic(
            self.spec.state_dir / "native-session" / "driver-state.json",
            {
                "format_version": 2,
                "pipe_name": config.pipe_name,
                "bridge_pid": 4242,
                "episode_character_id": 707,
                "episode_run_id": "native-707-existing",
                "last_checkpoint": checkpoint,
                "command_history": [
                    {
                        "index": 1,
                        "command": "save-checkpoint",
                        "ok": True,
                        "result": {
                            "step": "save-checkpoint",
                            "checkpoint": checkpoint,
                        },
                    }
                ],
            },
        )

        with mock.patch(
            "xar_autoplayer.native_session.launch", return_value=handle
        ) as launch_mock, mock.patch(
            "xar_autoplayer.native_session.stop_tracked",
            return_value={"ok": True, "contract_errors": []},
        ):
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=io.StringIO("stop\n"),
                output_stream=None,
                poll_interval_seconds=0.001,
                cold_start_checkpoint=True,
            )

        launch_mock.assert_called_once_with(
            self.spec,
            native_bridge=config,
            load_save_name="xar_checkpoint",
        )
        self.assertEqual(
            report["cold_start_checkpoint"]["sha256"], checkpoint_sha256
        )
        self.assertEqual(
            report["cold_start_checkpoint"]["history_index"], 1
        )

    def test_timeout_stops_tracked_process(self) -> None:
        process = mock.Mock()
        process.pid = 4343
        process.poll.return_value = None
        handle = SimpleNamespace(process=process)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\timeout-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        with mock.patch(
            "xar_autoplayer.native_session.launch", return_value=handle
        ), mock.patch(
            "xar_autoplayer.native_session.stop_tracked",
            return_value={"ok": True, "contract_errors": []},
        ) as stop_mock:
            report = _native_session_locked(
                self.spec,
                config,
                0.005,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.001,
            )

        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(report["exit_reason"], "timeout")
        self.assertTrue(report["ok"])

    def test_process_exit_is_reported_and_cleaned(self) -> None:
        process = mock.Mock()
        process.pid = 4444
        process.poll.return_value = 0
        handle = SimpleNamespace(process=process)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\exit-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        with mock.patch(
            "xar_autoplayer.native_session.launch", return_value=handle
        ), mock.patch(
            "xar_autoplayer.native_session.stop_tracked",
            return_value={"ok": True, "contract_errors": []},
        ):
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.001,
            )

        self.assertEqual(report["exit_reason"], "process_exit")
        self.assertEqual(report["process_exit_code"], 0)
        self.assertTrue(report["ok"])

    def test_restore_request_restarts_managed_process_and_responds(self) -> None:
        first_process = mock.Mock()
        first_process.pid = 4545
        first_process.poll.return_value = None
        second_process = mock.Mock()
        second_process.pid = 4646
        second_process.poll.return_value = None
        first_handle = SimpleNamespace(process=first_process)
        second_handle = SimpleNamespace(process=second_process)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\restore-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        bridge_dir = self.spec.state_dir / "native-session" / "bridge"
        checkpoint_payload = b"native-session exact checkpoint"
        checkpoint_path = (
            self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        )
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint_path.write_bytes(checkpoint_payload)
        checkpoint_sha256 = hashlib.sha256(checkpoint_payload).hexdigest()
        write_json_atomic(
            bridge_dir / "inbox" / "01-restore.json",
            {
                "protocol_version": 1,
                "request_id": "01-restore",
                "command": "restore-checkpoint",
                "pipe": config.pipe_name,
                "checkpoint_name": "xar_checkpoint.ck3",
                "checkpoint_size": len(checkpoint_payload),
                "checkpoint_sha256": checkpoint_sha256,
                "checkpoint_saved_date_raw": 53_168_664,
            },
        )
        write_json_atomic(
            bridge_dir / "inbox" / "02-stop.json",
            {
                "protocol_version": 1,
                "request_id": "02-stop",
                "command": "stop",
            },
        )
        shutdown = {"ok": True, "contract_errors": []}

        with mock.patch(
            "xar_autoplayer.native_session.launch",
            side_effect=(first_handle, second_handle),
        ) as launch_mock, mock.patch(
            "xar_autoplayer.native_session.stop_tracked",
            side_effect=(shutdown, shutdown),
        ) as stop_mock, mock.patch(
            "xar_autoplayer.native_session._process_windows_minimized",
            # The regular loop observes minimized.  At the exact restore
            # boundary the SDL window may temporarily disappear; retain the
            # last concrete state instead of treating that as restored.
            side_effect=(True, None),
        ) as minimized_before_mock, mock.patch(
            "xar_autoplayer.native_session._minimize_process_windows",
            return_value=True,
        ) as minimize_after_mock:
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.001,
            )

        self.assertEqual(launch_mock.call_count, 2)
        self.assertEqual(
            launch_mock.call_args_list,
            [
                mock.call(
                    self.spec,
                    native_bridge=config,
                    continue_last_save=True,
                ),
                mock.call(
                    self.spec,
                    native_bridge=config,
                    load_save_name="xar_checkpoint",
                    verify_prepared_profile=False,
                ),
            ],
        )
        self.assertEqual(
            stop_mock.call_args_list,
            [
                mock.call(first_handle, require_running=False),
                mock.call(second_handle, require_running=False),
            ],
        )
        response = json.loads(
            (bridge_dir / "outbox" / "01-restore.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["previous_pid"], 4545)
        self.assertEqual(response["result"]["pid"], 4646)
        self.assertFalse(response["result"]["continue_last_save"])
        self.assertEqual(
            response["result"]["load_save_name"], "xar_checkpoint"
        )
        self.assertEqual(
            response["result"]["checkpoint"]["sha256"], checkpoint_sha256
        )
        self.assertEqual(
            response["result"]["checkpoint"]["saved_date_raw"], 53_168_664
        )
        self.assertTrue(response["result"]["previous_window_minimized"])
        self.assertTrue(response["result"]["minimized_state_preserved"])
        self.assertEqual(
            minimized_before_mock.call_args_list,
            [mock.call(4545), mock.call(4545)],
        )
        minimize_after_mock.assert_called_once_with(
            4646,
            timeout_seconds=mock.ANY,
            poll_interval_seconds=0.001,
        )
        self.assertEqual(report["restart_count"], 1)
        self.assertEqual(report["pid"], 4646)
        self.assertEqual(report["exit_reason"], "stop")

    def test_start_next_episode_loads_immutable_seed_with_new_lifecycle_marker(
        self,
    ) -> None:
        first_process = mock.Mock(pid=4545)
        first_process.poll.return_value = None
        second_process = mock.Mock(pid=4646)
        second_process.poll.return_value = None
        first_handle = SimpleNamespace(process=first_process)
        second_handle = SimpleNamespace(process=second_process)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\next-episode-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        bridge_dir = self.spec.state_dir / "native-session" / "bridge"
        seed_payload = b"immutable seed"
        seed_path = self.spec.profile_dir / "save games" / "xar_episode_seed.ck3"
        seed_path.parent.mkdir(parents=True)
        seed_path.write_bytes(seed_payload)
        digest = hashlib.sha256(seed_payload).hexdigest()
        write_json_atomic(
            bridge_dir / "inbox" / "01-next.json",
            {
                "protocol_version": 1,
                "request_id": "01-next",
                "command": "start-next-episode",
                "pipe": config.pipe_name,
                "seed_name": seed_path.name,
                "seed_size": len(seed_payload),
                "seed_sha256": digest,
                "seed_date_raw": 53_168_784,
                "seed_character_id": 707,
                "source_run_id": "native-707-finished",
            },
        )
        write_json_atomic(
            bridge_dir / "inbox" / "02-stop.json",
            {"protocol_version": 1, "request_id": "02-stop", "command": "stop"},
        )
        shutdown = {"ok": True, "contract_errors": []}
        with mock.patch(
            "xar_autoplayer.native_session.launch",
            side_effect=(first_handle, second_handle),
        ) as launch_mock, mock.patch(
            "xar_autoplayer.native_session.stop_tracked",
            side_effect=(shutdown, shutdown),
        ):
            report = _native_session_locked(
                self.spec,
                config,
                1.0,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.001,
            )

        self.assertEqual(
            launch_mock.call_args_list[1],
            mock.call(
                self.spec,
                native_bridge=config,
                load_save_name="xar_episode_seed",
                verify_prepared_profile=False,
            ),
        )
        response = json.loads(
            (bridge_dir / "outbox" / "01-next.json").read_text(encoding="utf-8")
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["lifecycle_intent"], "new_episode")
        self.assertEqual(response["result"]["episode_seed"]["sha256"], digest)
        self.assertNotIn("checkpoint", response["result"])
        self.assertEqual(report["restart_count"], 1)


if __name__ == "__main__":
    unittest.main()
