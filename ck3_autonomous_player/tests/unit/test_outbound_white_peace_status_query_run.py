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
import xar_autoplayer.outbound_white_peace_status_query_run as subject


WAR_ID = 5
QUERY_STEP = "query-outbound-war-white-peace-status-v1-5"


class _Driver:
    def __init__(self, *args, **kwargs):
        self.closed = False

    def close(self):
        self.closed = True


class _Service:
    def __init__(self, driver, *, history, persisted):
        self.query_calls = 0
        self.persisted = persisted
        self.frame = {
            "snapshot_id": "native:3",
            "revision": 4,
            "native_revision": 3,
            "date_raw": 53149872,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 31853, "alive": True},
            "active_wars": [
                {
                    "war_id": WAR_ID,
                    "primary_opponent_character_id": 31506,
                    "player_side": "attacker",
                    "player_is_primary_war_leader": True,
                }
            ],
            "native_command_history": copy.deepcopy(history),
        }

    def snapshot(self):
        return copy.deepcopy(self.frame)

    def query_outbound_war_white_peace_status(self, war_id, *, expected_revision):
        self.query_calls += 1
        assert war_id == WAR_ID
        assert expected_revision == 4
        row = {
            "index": len(self.frame["native_command_history"]) + 1,
            "command": QUERY_STEP,
            "ok": True,
            "result": {"step": QUERY_STEP, "status": "available"},
        }
        self.frame["native_command_history"].append(row)
        self.persisted[:] = copy.deepcopy(self.frame["native_command_history"])
        return {
            "step": QUERY_STEP,
            "accepted": True,
            "status": "available",
            "backend_id": "native-headless",
            "outbound_war_white_peace_status": {
                "schema_version": 1,
                "war_id": WAR_ID,
                "actor_character_id": 31853,
                "recipient_character_id": 31506,
                "state": "exact_absent",
                "present": False,
                "pending_interaction_id": None,
            },
        }


def _restore_entry(checkpoint_sha: str) -> dict[str, object]:
    return {
        "index": 2,
        "command": "restore-checkpoint",
        "ok": True,
        "result": {
            "step": "restore-checkpoint",
            "accepted": True,
            "status": "restored",
            "backend_id": "native-headless",
            "source": "native-session-cold-start",
            "checkpoint": {
                "sha256": checkpoint_sha,
                "date_raw": 53149872,
                "history_index": 1,
            },
            "restored_date_raw": 53149872,
            "map_ready": True,
            "lifecycle": {"previous_pid": 100, "pid": 200},
        },
    }


class OutboundWhitePeaceStatusQueryRunTest(unittest.TestCase):
    def test_cli_binds_war_and_ownership_round(self) -> None:
        args = cli.parser().parse_args(
            [
                "native-query-outbound-war-white-peace-status-v1",
                "--war-id",
                "5",
                "--ownership-round-id",
                "R798",
                "--cold-start-checkpoint",
            ]
        )
        self.assertEqual(args.war_id, 5)
        self.assertEqual(args.ownership_round_id, "R798")
        self.assertTrue(args.cold_start_checkpoint)

    def test_exact_absent_query_is_read_only_and_cleanup_is_proven(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile"
            save = profile / "save games" / "xar_checkpoint.ck3"
            driver_state = root / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver_state.parent.mkdir(parents=True)
            save.write_bytes(b"checkpoint")
            checkpoint_sha = subject._sha256(save)
            prior = [{"index": 1, "command": "save-checkpoint", "ok": True}]
            restore = _restore_entry(checkpoint_sha)
            driver_state.write_text(
                json.dumps({"bridge_pid": 100, "command_history": prior}),
                encoding="utf-8",
            )
            persisted = [*prior, restore]
            spec = SimpleNamespace(state_dir=root, profile_dir=profile)
            config = NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=r"\\.\pipe\outbound-wp-test",
                dll_path=root / "bridge.dll",
                injector_path=root / "injector.exe",
            )
            services: list[_Service] = []

            def service_factory(driver):
                service = _Service(driver, history=[*prior, restore], persisted=persisted)
                services.append(service)
                return service

            def session(*args, stop_event: threading.Event, **kwargs):
                self.assertTrue(stop_event.wait(2.0))
                driver_state.write_text(
                    json.dumps({"bridge_pid": 200, "command_history": persisted}),
                    encoding="utf-8",
                )
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
                "snapshot_id": "native:3",
                "revision": 4,
                "native_revision": 3,
                "date_raw": 53149872,
                "paused": True,
                "map_ready": True,
            }
            with (
                mock.patch.object(subject, "ensure_state_path_safe"),
                mock.patch.object(
                    subject, "validate_native_bridge_launch_config", return_value=config
                ),
                mock.patch.object(
                    subject,
                    "validate_cold_start_checkpoint_for_pipe",
                    return_value={
                        "sha256": checkpoint_sha,
                        "saved_date_raw": 53149872,
                        "history_index": 1,
                    },
                ),
                mock.patch.object(subject, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    subject, "GameplayBridgeService", side_effect=service_factory
                ),
                mock.patch.object(subject, "_wait_for_readiness", return_value=readiness),
                mock.patch.object(subject, "native_session", side_effect=session),
            ):
                report = subject.query_outbound_white_peace_status_once(
                    spec,
                    war_id=WAR_ID,
                    timeout_seconds=30,
                    readiness_timeout_seconds=20,
                    ownership_round_id="R798",
                    cold_start_checkpoint=True,
                    native_bridge=config,
                )

            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "GREEN_READ_ONLY")
            self.assertEqual(report["round"], "R798")
            self.assertEqual(report["outbound_white_peace_status"]["state"], "exact_absent")
            self.assertEqual(services[0].query_calls, 1)
            self.assertTrue(all(report["checks"].values()))
            self.assertEqual(report["forbidden_action_counts"]["gameplay"], 0)
            self.assertEqual(
                report["before"]["files"]["checkpoint"]["sha256"],
                report["after"]["files"]["checkpoint"]["sha256"],
            )

    def test_round_and_cold_checkpoint_are_mandatory(self) -> None:
        spec = SimpleNamespace(state_dir=Path("state"), profile_dir=Path("profile"))
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\outbound-wp-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        with self.assertRaisesRegex(Exception, "R<number>"):
            subject.query_outbound_white_peace_status_once(
                spec,
                war_id=WAR_ID,
                timeout_seconds=1,
                readiness_timeout_seconds=1,
                ownership_round_id="R798A",
                cold_start_checkpoint=True,
                native_bridge=config,
            )
        with self.assertRaisesRegex(Exception, "cold-start checkpoint"):
            subject.query_outbound_white_peace_status_once(
                spec,
                war_id=WAR_ID,
                timeout_seconds=1,
                readiness_timeout_seconds=1,
                ownership_round_id="R798",
                cold_start_checkpoint=False,
                native_bridge=config,
            )


if __name__ == "__main__":
    unittest.main()
