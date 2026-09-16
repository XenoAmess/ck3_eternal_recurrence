from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest import mock

from xar_autoplayer import cli
from xar_autoplayer.runtime import NativeBridgeLaunchConfig
import xar_autoplayer.timeline_blocker_action_run as subject


CHARACTER_ID = 35465
EPISODE_RUN_ID = "native-35465-cbdf997e3d80"
DATE_RAW = 53411568


def _prior_history() -> list[dict[str, object]]:
    return [
        {"index": 1, "command": "continue-as-reconciled-successor", "ok": True},
        {"index": 2, "command": "query-campaign-root-context-v1", "ok": True},
        {"index": 3, "command": "save-checkpoint", "ok": True},
    ]


def _restore_entry(checkpoint_sha: str) -> dict[str, object]:
    return {
        "index": 4,
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
                "date_raw": DATE_RAW,
                "history_index": 3,
            },
            "restored_date_raw": DATE_RAW,
            "map_ready": True,
            "lifecycle": {"previous_pid": 100, "pid": 200},
        },
    }


def _field(value: bool) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _context(identity: str) -> dict[str, object]:
    modal = identity == "death_succession_modal"
    return {
        "status": "available",
        "identity": identity,
        "can_continue": _field(True) if modal else {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "no_supported_timeline_surface_visible",
        },
        "blocks_simulation": _field(modal),
        "has_open_succession": _field(modal),
        "evidence_source": {
            "root_name": "succession_event_window" if modal else "none"
        },
    }


class _Driver:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.closed = False

    def close(self):
        self.closed = True


def test_r778_checkpoint_binding_is_the_authoritative_sha256() -> None:
    assert subject.EXPECTED_SOURCE_CHECKPOINT_SHA256 == (
        "2c0f4333ae186ee91f560ad7d14abb2f2e29aaa1b4d2eacfefe0c9a8e1e505e3"
    )
    assert len(subject.EXPECTED_SOURCE_CHECKPOINT_SHA256) == 64


class _Service:
    def __init__(self, driver: _Driver, *, save: Path, history: list[object]):
        self.driver = driver
        self.save = save
        self.action_calls = 0
        self.save_calls = 0
        self.frame: dict[str, object] = {
            "snapshot_id": "native-frame-18",
            "revision": 13,
            "native_revision": 18,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": CHARACTER_ID, "alive": True},
            "episode_character_id": CHARACTER_ID,
            "episode_run_id": EPISODE_RUN_ID,
            "native_command_history": copy.deepcopy(history),
        }

    def snapshot(self):
        return copy.deepcopy(self.frame)

    def continue_death_succession_modal_private_v1(
        self,
        *,
        expected_revision: int,
        expected_played_character_id: int,
        expected_episode_run_id: str,
    ):
        self.action_calls += 1
        assert expected_revision == 13
        assert expected_played_character_id == CHARACTER_ID
        assert expected_episode_run_id == EPISODE_RUN_ID
        ack = {
            "step": subject.ACTION_STEP,
            "accepted": True,
            "status": "submitted",
            "action_observation_revision": 4574,
            "close_invocations": 1,
            "material_result_verified": False,
            "private_build": True,
            "advertised": False,
        }
        initial = {
            "observation_revision": 4573,
            "source": {"paused": True},
            "current_timeline_blocker_context": _context(
                "death_succession_modal"
            ),
        }
        post = {
            "observation_revision": 4575,
            "source": {"paused": True},
            "current_timeline_blocker_context": _context("none"),
        }
        history = self.frame["native_command_history"]
        assert isinstance(history, list)
        history.append(
            {
                "index": 5,
                "command": "life-advance",
                "ok": True,
                "result": {"step": "life-advance", "accepted": True},
            }
        )
        self.frame.update(
            {
                "snapshot_id": "native-frame-19",
                "revision": 14,
                "native_revision": 19,
                "date_raw": DATE_RAW + 4,
            }
        )
        return {
            **ack,
            "status": "materially_verified",
            "material_result_verified": True,
            "submission_ack": ack,
            "initial_query": initial,
            "postcondition_query": post,
            "post_observation_revision": 4575,
            "life_advance_result": {"step": "life-advance", "accepted": True},
            "starting_date_raw": DATE_RAW,
            "ending_date_raw": DATE_RAW + 4,
            "ending_revision": 14,
            "ending_native_revision": 19,
        }

    def save_checkpoint(self, *, expected_revision: int):
        self.save_calls += 1
        assert expected_revision == 14
        self.save.write_bytes(b"material-checkpoint-after-life-advance")
        digest = hashlib.sha256(self.save.read_bytes()).hexdigest()
        checkpoint = {
            "status": "saved",
            "name": "xar_checkpoint.ck3",
            "path": str(self.save.resolve()),
            "strategy": "native-autosave-command-v1",
            "size": self.save.stat().st_size,
            "sha256": digest,
            "date_raw": DATE_RAW + 4,
            "history_index": 6,
            "episode_character_id": CHARACTER_ID,
            "episode_run_id": EPISODE_RUN_ID,
        }
        result = {
            "step": "save-checkpoint",
            "accepted": True,
            "checkpoint": copy.deepcopy(checkpoint),
            "materialization": {
                "available": True,
                "save_dir": str(self.save.parent.resolve()),
                "mtime_ns": self.save.stat().st_mtime_ns,
            },
        }
        history = self.frame["native_command_history"]
        assert isinstance(history, list)
        history.append(
            {
                "index": 6,
                "command": "save-checkpoint",
                "ok": True,
                "result": {"checkpoint": copy.deepcopy(checkpoint)},
            }
        )
        return result


class TimelineBlockerActionRunTest(unittest.TestCase):
    def test_cli_requires_explicit_bound_action_inputs(self) -> None:
        args = cli.parser().parse_args(
            [
                "native-continue-death-succession-modal-v1",
                "--private-timeline-action-round-id",
                "R778",
                "--expected-played-character-id",
                str(CHARACTER_ID),
                "--expected-episode-run-id",
                EPISODE_RUN_ID,
                "--expected-date-raw",
                str(DATE_RAW),
                "--cold-start-checkpoint",
            ]
        )
        self.assertEqual(
            args.command, "native-continue-death-succession-modal-v1"
        )
        self.assertEqual(args.private_timeline_action_round_id, "R778")
        self.assertTrue(args.cold_start_checkpoint)

    def test_close_postcondition_life_advance_and_checkpoint_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile"
            save = profile / "save games" / "xar_checkpoint.ck3"
            driver_state = root / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver_state.parent.mkdir(parents=True)
            save.write_bytes(b"sealed-source-checkpoint")
            prior = _prior_history()
            restore = _restore_entry(subject.EXPECTED_SOURCE_CHECKPOINT_SHA256)
            before_driver = {
                "format_version": 2,
                "bridge_pid": 100,
                "episode_character_id": CHARACTER_ID,
                "episode_run_id": EPISODE_RUN_ID,
                "command_history": prior,
            }
            driver_state.write_text(json.dumps(before_driver), encoding="utf-8")
            spec = SimpleNamespace(state_dir=root, profile_dir=profile)
            config = NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=r"\\.\pipe\timeline-action-test",
                dll_path=root / "bridge.dll",
                injector_path=root / "injector.exe",
            )
            services: list[_Service] = []

            def service_factory(driver):
                service = _Service(driver, save=save, history=[*prior, restore])
                services.append(service)
                return service

            def session(*args, stop_event: threading.Event, **kwargs):
                self.assertTrue(stop_event.wait(2.0))
                after_driver = {
                    **before_driver,
                    "bridge_pid": 200,
                    "command_history": copy.deepcopy(
                        services[0].frame["native_command_history"]
                    ),
                }
                driver_state.write_text(json.dumps(after_driver), encoding="utf-8")
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
                "date_raw": DATE_RAW,
                "paused": True,
                "map_ready": True,
            }

            def sealed_sha(path: Path) -> str:
                if path == save and path.read_bytes() == b"sealed-source-checkpoint":
                    return subject.EXPECTED_SOURCE_CHECKPOINT_SHA256
                if path == driver_state and json.loads(
                    path.read_text(encoding="utf-8")
                ).get("bridge_pid") == 100:
                    return subject.EXPECTED_SOURCE_DRIVER_STATE_SHA256
                return hashlib.sha256(path.read_bytes()).hexdigest()

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
                        "sha256": subject.EXPECTED_SOURCE_CHECKPOINT_SHA256,
                        "saved_date_raw": DATE_RAW,
                        "history_index": 3,
                    },
                ),
                mock.patch.object(subject, "_sha256", side_effect=sealed_sha),
                mock.patch.object(subject, "NativeHeadlessGameplayDriver", _Driver),
                mock.patch.object(
                    subject,
                    "GameplayBridgeService",
                    side_effect=service_factory,
                ),
                mock.patch.object(
                    subject, "_wait_for_readiness", return_value=readiness
                ),
                mock.patch.object(subject, "native_session", side_effect=session),
            ):
                report = subject.continue_death_succession_modal_once(
                    spec,
                    timeout_seconds=390,
                    readiness_timeout_seconds=300,
                    private_timeline_action_round_id="R778",
                    expected_played_character_id=CHARACTER_ID,
                    expected_episode_run_id=EPISODE_RUN_ID,
                    expected_date_raw=DATE_RAW,
                    cold_start_checkpoint=True,
                    native_bridge=config,
                )

            self.assertTrue(report["ok"], report)
            self.assertEqual(report["status"], "GREEN_MATERIAL")
            self.assertEqual(report["action_counts"], {
                "close": 1,
                "life_advance": 1,
                "checkpoint": 1,
            })
            self.assertTrue(all(report["checks"].values()))
            self.assertTrue(all(
                count == 0
                for count in report["forbidden_action_counts"].values()
            ))
            self.assertEqual(report["checkpoint"]["history_index"], 6)
            self.assertGreater(report["after"]["date_raw"], DATE_RAW)
            self.assertEqual(services[0].action_calls, 1)
            self.assertEqual(services[0].save_calls, 1)
            driver_kwargs = services[0].driver.kwargs
            self.assertTrue(driver_kwargs["allow_private_current_timeline_blocker_query"])
            self.assertTrue(driver_kwargs["allow_private_death_succession_modal_continue"])

    def test_exact_history_three_is_required_before_session_start(self) -> None:
        checkpoint = {"history_index": 4}
        driver = {"command_history": [*_prior_history(), {
            "index": 4,
            "command": "restore-checkpoint",
            "ok": True,
        }]}
        self.assertFalse(subject._exact_source_history(driver, checkpoint))


if __name__ == "__main__":
    unittest.main()
