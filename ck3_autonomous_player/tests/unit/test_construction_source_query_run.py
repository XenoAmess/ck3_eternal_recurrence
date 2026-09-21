from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest import mock

from xar_autoplayer import cli
from xar_autoplayer.runtime import NativeBridgeLaunchConfig
import xar_autoplayer.construction_source_query_run as subject


class ConstructionSourceQueryRunTest(unittest.TestCase):
    def test_cli_is_explicitly_private_and_cold(self) -> None:
        args = cli.parser().parse_args([
            "native-query-private-construction-source-v1",
            "--ownership-round-id", "R900",
            "--cold-start-checkpoint",
        ])
        self.assertEqual(args.command, "native-query-private-construction-source-v1")
        self.assertEqual(args.ownership_round_id, "R900")
        self.assertTrue(args.cold_start_checkpoint)

    def test_cli_wires_only_the_private_source_runner(self) -> None:
        config = NativeBridgeLaunchConfig(
            mode="native-headless", pipe_name=r"\\.\pipe\construction-source-test",
            dll_path=Path("Z:/bridge.dll"), injector_path=Path("Z:/injector.exe"),
        )
        with (
            mock.patch.object(cli, "make_spec", return_value=object()),
            mock.patch.object(cli, "configure_native_bridge_launch_environment"),
            mock.patch.object(subject, "query_private_construction_source_once",
                              return_value={"ok": True, "status": "GREEN_READ_ONLY_SOURCE"}) as run,
            mock.patch("builtins.print"),
        ):
            code = cli.main([
                "--bridge-mode", "native-headless", "--bridge-pipe", config.pipe_name,
                "--bridge-dll", str(config.dll_path),
                "--bridge-injector", str(config.injector_path),
                "native-query-private-construction-source-v1",
                "--ownership-round-id", "R900", "--cold-start-checkpoint",
                "--timeout", "30", "--readiness-timeout", "20",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs["ownership_round_id"], "R900")
        self.assertTrue(run.call_args.kwargs["cold_start_checkpoint"])

    def test_r0066_source_red_is_persisted_without_planning_or_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            save = state / "profile" / "save games" / "xar_checkpoint.ck3"
            driver_path = state / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver_path.parent.mkdir(parents=True)
            save.write_bytes(b"R753 paired pre-action checkpoint")
            sha = subject._sha256(save)
            anchor = {"index": 1, "command": "save-checkpoint", "ok": True}
            restore = {
                "index": 2, "command": "restore-checkpoint", "ok": True,
                "result": {
                    "step": "restore-checkpoint", "accepted": True,
                    "status": "restored", "backend_id": "native-headless",
                    "source": "native-session-cold-start",
                    "checkpoint": {"sha256": sha, "date_raw": 53178312,
                                   "history_index": 1},
                    "restored_date_raw": 53178312, "map_ready": True,
                    "lifecycle": {"previous_pid": 100, "pid": 200},
                },
            }
            before_driver = {
                "bridge_pid": 100, "episode_character_id": 29829,
                "command_history": [anchor],
                "last_checkpoint": {"sha256": sha, "date_raw": 53178312},
            }
            after_driver = {**before_driver, "bridge_pid": 200,
                            "command_history": [anchor, restore]}
            driver_path.write_text(json.dumps(before_driver), encoding="utf-8")
            frame = {
                "snapshot_id": "native:3", "revision": 4,
                "native_revision": 3, "date_raw": 53178312,
                "paused": True, "map_ready": True,
                "native_command_history": [anchor, restore],
            }
            native_result = {
                "step": subject.query_construction_private.__globals__["QUERY_NATIVE"],
                "accepted": True,
                "private_probe": {
                    "snapshot_revision": 3, "date_raw": 53178312,
                    "player_world_building_sources": {
                        "status": "source_unavailable",
                        "unavailable_reason": "synthetic R0066-shaped diagnostic",
                    },
                },
            }
            query_result = {
                "status": "source_red", "native_result": native_result,
                "native_query_request_id": "construction-read-test",
                "source_frame": {"snapshot_id": "native:3", "revision": 4},
                "ending_frame": {"snapshot_id": "native:3", "revision": 4},
            }
            spec = SimpleNamespace(state_dir=state, profile_dir=state / "profile")
            config = NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=r"\\.\pipe\construction-source-test",
                dll_path=state / "bridge.dll", injector_path=state / "injector.exe",
            )
            session_ready = threading.Event()

            class Driver:
                closed = False

                def take_snapshot(self):
                    return copy.deepcopy(frame)

                def close(self):
                    self.closed = True

            driver = Driver()

            def session(*args, stop_event: threading.Event, **kwargs):
                driver_path.write_text(json.dumps(after_driver), encoding="utf-8")
                session_ready.set()
                self.assertTrue(stop_event.wait(2))
                return {"ok": True, "exit_reason": "stop",
                        "shutdown": {"ok": True, "tree_gone": True,
                                     "cleanup_proven": True}}

            def readiness(*args, **kwargs):
                self.assertTrue(session_ready.wait(2))
                return copy.deepcopy(frame)

            with (
                mock.patch.object(subject, "ensure_state_path_safe"),
                mock.patch.object(subject, "validate_native_bridge_launch_config",
                                  return_value=config),
                mock.patch.object(subject, "validate_cold_start_checkpoint_for_pipe",
                                  return_value={"sha256": sha,
                                                "saved_date_raw": 53178312,
                                                "history_index": 1}),
                mock.patch.object(subject, "NativeHeadlessGameplayDriver",
                                  return_value=driver),
                mock.patch.object(subject, "native_session", side_effect=session),
                mock.patch.object(subject, "_wait_for_readiness", side_effect=readiness),
                mock.patch.object(subject, "query_construction_private",
                                  return_value=query_result) as native_query,
            ):
                report = subject.query_private_construction_source_once(
                    spec, timeout_seconds=10, readiness_timeout_seconds=5,
                    ownership_round_id="R900", cold_start_checkpoint=True,
                    native_bridge=config,
                )
            self.assertFalse(report["ok"])
            self.assertEqual(report["status"], "RED")
            self.assertEqual(report["query"]["native_result"], native_result)
            self.assertTrue(all(report["checks"].values()))
            self.assertTrue(driver.closed)
            native_query.assert_called_once_with(driver, expected_revision=4)
            persisted = json.loads(Path(report["report_path"]).read_text(encoding="utf-8"))
            self.assertEqual(persisted["query"]["native_result"], native_result)
            self.assertEqual(subject._sha256(save), sha)


if __name__ == "__main__":
    unittest.main()
