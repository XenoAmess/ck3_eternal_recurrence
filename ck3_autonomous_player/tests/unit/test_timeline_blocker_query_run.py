from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest import mock

from xar_autoplayer import cli
from xar_autoplayer.runtime import NativeBridgeLaunchConfig
import xar_autoplayer.timeline_blocker_query_run as subject


class _Driver:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.closed = False

    def close(self):
        self.closed = True


class _Service:
    def __init__(self, driver):
        self.driver = driver
        self.snapshot_calls = 0
        self.query_calls = 0
        self.frame = {
            "snapshot_id": "native-frame-18",
            "revision": 13,
            "native_revision": 18,
            "date_raw": 53411568,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 35465},
        }

    def snapshot(self):
        self.snapshot_calls += 1
        return copy.deepcopy(self.frame)

    def query_current_timeline_blocker_context_v1(self, *, expected_revision):
        self.query_calls += 1
        assert expected_revision == 13
        return {
            "step": subject.QUERY_STEP,
            "accepted": True,
            "status": "observed",
            "private_build": True,
            "read_only": True,
            "advertised": False,
            "source": {
                "snapshot_id": "native-frame-18",
                "revision": 13,
                "native_revision": 18,
                "date_raw": 53411568,
                "paused": True,
                "backend_id": "native-headless",
            },
            "current_timeline_blocker_context": {"identity": "none"},
        }


class TimelineBlockerQueryRunTest(unittest.TestCase):
    def test_cli_requires_explicit_private_round_and_cold_start_is_opt_in(self) -> None:
        args = cli.parser().parse_args([
            "native-query-current-timeline-blocker-context-v1",
            "--private-timeline-query-round-id",
            "R776",
            "--cold-start-checkpoint",
        ])
        self.assertEqual(
            args.command, "native-query-current-timeline-blocker-context-v1"
        )
        self.assertEqual(args.private_timeline_query_round_id, "R776")
        self.assertTrue(args.cold_start_checkpoint)

    def test_one_query_keeps_files_and_frame_unchanged_then_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile"
            save = profile / "save games" / "xar_checkpoint.ck3"
            driver_state = root / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver_state.parent.mkdir(parents=True)
            save.write_bytes(b"checkpoint")
            driver_state.write_bytes(b"driver-state")
            spec = SimpleNamespace(state_dir=root, profile_dir=profile)
            config = NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=r"\\.\pipe\timeline-test",
                dll_path=root / "bridge.dll",
                injector_path=root / "injector.exe",
            )
            services: list[_Service] = []

            def service_factory(driver):
                service = _Service(driver)
                services.append(service)
                return service

            def session(*args, stop_event: threading.Event, **kwargs):
                self.assertTrue(stop_event.wait(2.0))
                return {
                    "ok": True,
                    "exit_reason": "stop",
                    "shutdown": {
                        "ok": True,
                        "tree_gone": True,
                        "cleanup_proven": True,
                    },
                }

            readiness = {
                "snapshot_id": "native-frame-18",
                "revision": 13,
                "native_revision": 18,
                "date_raw": 53411568,
                "paused": True,
                "map_ready": True,
            }
            with (
                mock.patch.object(subject, "ensure_state_path_safe"),
                mock.patch.object(
                    subject,
                    "validate_native_bridge_launch_config",
                    return_value=config,
                ),
                mock.patch.object(
                    subject,
                    "validate_cold_start_checkpoint_for_pipe",
                    return_value={
                        "sha256": subject._sha256(save),
                        "saved_date_raw": 53411568,
                    },
                ),
                mock.patch.object(subject, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(subject, "GameplayBridgeService", side_effect=service_factory),
                mock.patch.object(subject, "_wait_for_readiness", return_value=readiness),
                mock.patch.object(subject, "native_session", side_effect=session),
            ):
                report = subject.query_current_timeline_blocker_once(
                    spec,
                    timeout_seconds=390,
                    readiness_timeout_seconds=300,
                    private_timeline_query_round_id="R776",
                    cold_start_checkpoint=True,
                    native_bridge=config,
                )

            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "GREEN_READ_ONLY")
            self.assertEqual(report["round"], "R776")
            self.assertEqual(services[0].query_calls, 1)
            self.assertEqual(report["forbidden_action_counts"]["gameplay"], 0)
            self.assertTrue(all(report["checks"].values()))
            self.assertTrue(report["cleanup"]["ok"])
            self.assertEqual(
                report["before"]["files"]["checkpoint"]["sha256"],
                report["after"]["files"]["checkpoint"]["sha256"],
            )

    def test_round_and_cold_checkpoint_are_mandatory(self) -> None:
        spec = SimpleNamespace(state_dir=Path("state"), profile_dir=Path("profile"))
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\timeline-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        with self.assertRaisesRegex(Exception, "R<number>"):
            subject.query_current_timeline_blocker_once(
                spec,
                timeout_seconds=1,
                readiness_timeout_seconds=1,
                private_timeline_query_round_id="R776A",
                cold_start_checkpoint=True,
                native_bridge=config,
            )
        with self.assertRaisesRegex(Exception, "cold-start checkpoint"):
            subject.query_current_timeline_blocker_once(
                spec,
                timeout_seconds=1,
                readiness_timeout_seconds=1,
                private_timeline_query_round_id="R776",
                cold_start_checkpoint=False,
                native_bridge=config,
            )


if __name__ == "__main__":
    unittest.main()
