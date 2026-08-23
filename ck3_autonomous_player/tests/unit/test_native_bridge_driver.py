from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import threading
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    CallbackGameplayDriver,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import write_json_atomic


class FakeEndpoint:
    def __init__(self, pipe_name: str = r"\\.\pipe\xar_fixture") -> None:
        self.pipe_name = pipe_name
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None
        self.closed = False
        self.error: str | None = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        self.closed = True

    def transport_error(self) -> str | None:
        return self.error


def _hello(*capabilities: str) -> dict[str, object]:
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 4242,
        "session_generation": 0,
        "capabilities": list(capabilities),
    }


def _snapshot(
    revision: int = 1,
    *,
    active_event: dict[str, object] | None = None,
    date_raw: int = 53_171_400,
    speed: int = 1,
    paused: bool = True,
    map_ready: bool = True,
    pending_character_interaction: dict[str, object] | None = None,
    played_character: dict[str, object] | None = None,
    active_wars: list[dict[str, object]] | None = None,
    player_armies: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": date_raw,
            "speed": speed,
            "paused": paused,
            "map_ready": map_ready,
            "history": [],
            "active_event": active_event,
            "pending_character_interaction": pending_character_interaction,
            "played_character": played_character,
            "active_wars": active_wars,
            "player_armies": player_armies,
        },
    }


def _write_driver_state_checkpoint_fixture(
    state_dir: Path,
    pipe_name: str,
    *,
    bridge_pid: int = 1111,
    character_id: int = 707,
    run_id: str = "native-707-existing",
    date_raw: int = 53_168_784,
    format_version: int = 2,
    include_v2_anchor: bool = True,
) -> tuple[Path, dict[str, object]]:
    save_dir = state_dir / "profile" / "save games"
    save_dir.mkdir(parents=True)
    checkpoint_path = save_dir / "xar_checkpoint.ck3"
    payload = b"cold-checkpoint-fixture"
    checkpoint_path.write_bytes(payload)
    checkpoint: dict[str, object] = {
        "status": "saved",
        "path": str(checkpoint_path.resolve()),
        "name": checkpoint_path.name,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "date_raw": date_raw,
        "strategy": "native-autosave-command-v1",
    }
    if include_v2_anchor:
        checkpoint.update(
            {
                "history_index": 8,
                "episode_character_id": character_id,
                "episode_run_id": run_id,
            }
        )
    history: list[dict[str, object]] = [
        {
            "index": index,
            "command": "life-advance",
            "ok": True,
            "result": {"step": "life-advance", "ending_date_raw": date_raw},
        }
        for index in range(1, 8)
    ]
    history.append(
        {
            "index": 8,
            "command": "save-checkpoint",
            "ok": True,
            "result": {
                "step": "save-checkpoint",
                "checkpoint": dict(checkpoint),
            },
        }
    )
    history.extend(
        [
            {
                "index": 9,
                "command": "life-advance",
                "ok": True,
                "result": {"step": "life-advance"},
            },
            {
                "index": 10,
                "command": "life-advance",
                "ok": True,
                "result": {"step": "life-advance"},
            },
            {
                "index": 11,
                "command": "move-army-1-to-2",
                "ok": True,
                "result": {"step": "move-army-1-to-2"},
            },
        ]
    )
    write_json_atomic(
        state_dir / "native-session" / "driver-state.json",
        {
            "format_version": format_version,
            "pipe_name": pipe_name,
            "bridge_pid": bridge_pid,
            "episode_character_id": character_id,
            "episode_run_id": run_id,
            "last_checkpoint": checkpoint,
            "command_history": history,
        },
    )
    return checkpoint_path, checkpoint


def _army(
    army_id: int,
    *,
    soldiers: int | None = 1_000,
    province_id: int | None = 10,
    move_target_province_id: int | None = None,
    observe_move_target: bool = True,
    controllable: bool = True,
) -> dict[str, object]:
    result = {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": soldiers,
        "current_province_id": province_id,
        "move_target_province_id": move_target_province_id,
        "controllable": controllable,
    }
    if not observe_move_target:
        result.pop("move_target_province_id")
    return result


def _war(
    war_id: int = 61,
    *,
    allied_armies: list[dict[str, object]] | None = None,
    enemy_armies: list[dict[str, object]] | None = None,
    score: int = 12,
    player_is_primary_war_leader: bool = True,
    enemy_primary_default_raise_province_id: int | None = None,
) -> dict[str, object]:
    return {
        "war_id": war_id,
        "player_side": "attacker",
        "primary_opponent_character_id": 808,
        "player_is_primary_war_leader": player_is_primary_war_leader,
        "enemy_primary_default_raise_province_id": (
            enemy_primary_default_raise_province_id
        ),
        "player_relative_war_score": score,
        "allied_armies": allied_armies or [],
        "enemy_armies": enemy_armies or [],
    }


class NativeHeadlessGameplayDriverTests(unittest.TestCase):
    def test_current_dll_only_exposes_connection_diagnostics(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )

        disconnected = driver.capabilities()
        self.assertEqual(disconnected["mode"], "native-headless")
        self.assertTrue(disconnected["headless"])
        self.assertTrue(disconnected["minimized_operation"])
        self.assertFalse(disconnected["visual_fallback"])
        self.assertFalse(disconnected["fallback_enabled"])
        self.assertFalse(disconnected["snapshot"])
        self.assertEqual(disconnected["action_steps"], [])

        endpoint.publish(
            _hello("bridge.identity", "bridge.heartbeat", "bridge.ping")
        )
        ping = endpoint.frames[-1]
        self.assertEqual(ping["type"], "ping")
        endpoint.publish(
            {
                "type": "heartbeat",
                "protocol_version": 1,
                "sequence": 7,
                "pid": 4242,
                "monotonic_ms": 500,
            }
        )
        endpoint.publish(
            {
                "type": "pong",
                "protocol_version": 1,
                "request_id": ping["request_id"],
                "pid": 4242,
            }
        )

        connected = driver.capabilities()
        diagnostics = connected["diagnostics"]
        self.assertTrue(diagnostics["connected"])
        self.assertEqual(diagnostics["bridge_pid"], 4242)
        self.assertEqual(diagnostics["last_heartbeat"]["sequence"], 7)
        self.assertEqual(
            diagnostics["last_pong"]["request_id"], ping["request_id"]
        )
        self.assertFalse(connected["snapshot"])
        self.assertEqual(connected["action_steps"], [])
        with self.assertRaisesRegex(UnsupportedStepError, "did not advertise"):
            driver.take_snapshot()
        with self.assertRaisesRegex(UnsupportedStepError, "does not implement"):
            driver.execute_step("life-advance")

    def test_protocol_extension_routes_snapshot_and_command_result(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.life-advance")
        )
        endpoint.publish(_snapshot(19))

        capabilities = driver.capabilities()
        self.assertTrue(capabilities["snapshot"])
        self.assertEqual(capabilities["action_steps"], ["life-advance"])
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["native_revision"], 19)
        self.assertEqual(snapshot["phase"], "map_hud")

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "accepted": True},
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "life-advance", expected_revision=int(snapshot["revision"])
        )
        command = next(
            frame for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["expected_revision"], 19)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["backend_id"], "native-headless")
        self.assertEqual(
            driver.take_snapshot()["native_command_history"],
            [
                {
                    "index": 1,
                    "command": "life-advance",
                    "ok": True,
                    "result": result,
                }
            ],
        )

    def test_daemon_restart_restores_episode_and_command_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    "game.command.life-advance",
                )
            )
            endpoint.publish(
                _snapshot(
                    19,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            first = driver.take_snapshot()

            def answer(frame: dict[str, object]) -> None:
                if frame.get("type") == "execute_step":
                    endpoint.publish(
                        {
                            "type": "command_result",
                            "protocol_version": 1,
                            "request_id": frame["request_id"],
                            "ok": True,
                            "result": {
                                "step": frame["step"],
                                "accepted": True,
                            },
                        }
                    )

            endpoint.send_hook = answer
            driver.execute_step(
                "life-advance", expected_revision=int(first["revision"])
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["bridge_pid"], 4242)
            self.assertEqual(persisted["episode_run_id"], first["episode_run_id"])
            self.assertEqual(len(persisted["command_history"]), 1)

            replacement_endpoint = FakeEndpoint(endpoint.pipe_name)
            replacement = NativeHeadlessGameplayDriver(
                replacement_endpoint.pipe_name,
                endpoint=replacement_endpoint,
                state_dir=state_dir,
            )
            replacement_endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    "game.command.life-advance",
                )
            )
            replacement_endpoint.publish(
                _snapshot(
                    20,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            restored = replacement.take_snapshot()
            self.assertEqual(restored["episode_run_id"], first["episode_run_id"])
            self.assertEqual(len(restored["native_command_history"]), 1)
            self.assertTrue(
                replacement.capabilities()["native_session_control"][
                    "driver_state_restored"
                ]
            )

            # A process-level restore inside the same driver keeps this
            # one-life episode, and updates the PID used by the next daemon.
            replacement_endpoint.publish({**_hello("game.state.snapshot"), "pid": 5000})
            replacement_endpoint.publish(
                _snapshot(
                    21,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            after_process_restore = replacement.take_snapshot()
            self.assertEqual(
                after_process_restore["episode_run_id"], first["episode_run_id"]
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["bridge_pid"],
                5000,
            )

            new_endpoint = FakeEndpoint(endpoint.pipe_name)
            new_driver = NativeHeadlessGameplayDriver(
                new_endpoint.pipe_name,
                endpoint=new_endpoint,
                state_dir=state_dir,
            )
            new_endpoint.publish({**_hello("game.state.snapshot"), "pid": 6000})
            new_endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 909, "alive": True},
                )
            )
            new_episode = new_driver.take_snapshot()
            self.assertEqual(new_episode["episode_character_id"], 909)
            self.assertNotEqual(
                new_episode["episode_run_id"], first["episode_run_id"]
            )
            self.assertEqual(new_episode["native_command_history"], [])
            self.assertFalse(
                new_driver.capabilities()["native_session_control"][
                    "driver_state_restored"
                ]
            )

    def test_v1_hot_migration_then_cold_checkpoint_resume_rolls_back_tail(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_cold_migration"
            checkpoint_path, _checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=140760,
                character_id=29829,
                run_id="native-29829-live-run",
                format_version=1,
                include_v2_anchor=False,
            )
            hot_endpoint = FakeEndpoint(pipe_name)
            hot_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=hot_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            hot_endpoint.publish({**_hello("game.state.snapshot"), "pid": 140760})

            hot_control = hot_driver.capabilities()["native_session_control"]
            self.assertTrue(hot_control["driver_state_restored"])
            self.assertEqual(hot_control["driver_state_restore_kind"], "same_pid_hot")
            migrated = json.loads(
                (
                    state_dir / "native-session" / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(migrated["format_version"], 2)
            self.assertEqual(migrated["last_checkpoint"]["history_index"], 8)
            self.assertEqual(
                migrated["last_checkpoint"]["episode_character_id"], 29829
            )
            self.assertEqual(
                migrated["last_checkpoint"]["episode_run_id"],
                "native-29829-live-run",
            )

            cold_endpoint = FakeEndpoint(pipe_name)
            cold_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=cold_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            cold_endpoint.publish({**_hello("game.state.snapshot"), "pid": 150000})
            pending = cold_driver.capabilities()["native_session_control"]
            self.assertEqual(
                pending["episode_binding_state"], "pending_cold_candidate"
            )
            self.assertFalse(pending["driver_state_restored"])

            cold_endpoint.publish(
                _snapshot(
                    1,
                    map_ready=False,
                    date_raw=53_168_784,
                    played_character={"character_id": 29829, "alive": True},
                )
            )
            not_ready = cold_driver.take_snapshot()
            self.assertTrue(not_ready["episode_identity_pending"])
            self.assertFalse(not_ready["one_life_terminal"])
            self.assertIsNone(not_ready["episode_character_id"])

            cold_endpoint.publish(
                _snapshot(
                    2,
                    date_raw=53_168_784,
                    played_character={"character_id": 29829, "alive": True},
                )
            )
            resumed = cold_driver.take_snapshot()
            self.assertEqual(resumed["episode_character_id"], 29829)
            self.assertEqual(resumed["episode_run_id"], "native-29829-live-run")
            self.assertFalse(resumed["one_life_terminal"])
            history = resumed["native_command_history"]
            self.assertEqual(len(history), 9)
            self.assertEqual(history[7]["command"], "save-checkpoint")
            self.assertEqual(history[8]["command"], "restore-checkpoint")
            self.assertEqual(
                history[8]["result"]["source"], "native-session-cold-start"
            )
            self.assertNotIn("move-army-1-to-2", [row["command"] for row in history])
            resumed_control = cold_driver.capabilities()["native_session_control"]
            self.assertTrue(resumed_control["driver_state_restored"])
            self.assertEqual(
                resumed_control["driver_state_restore_kind"], "cold_checkpoint"
            )
            persisted = json.loads(
                (
                    state_dir / "native-session" / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["bridge_pid"], 150000)
            self.assertEqual(len(persisted["command_history"]), 9)

    def test_cold_checkpoint_mismatch_starts_nonterminal_new_episode(self) -> None:
        cases = (
            ("played_character", 909, 53_168_784, False),
            ("date", 707, 53_168_785, False),
            ("sha256", 707, 53_168_784, True),
        )
        for name, character_id, date_raw, mutate_bytes in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                pipe_name = rf"\\.\pipe\xar_cold_mismatch_{name}"
                checkpoint_path, _checkpoint = (
                    _write_driver_state_checkpoint_fixture(state_dir, pipe_name)
                )
                if mutate_bytes:
                    checkpoint_path.write_bytes(b"cold-checkpoint-fixturf")
                endpoint = FakeEndpoint(pipe_name)
                driver = NativeHeadlessGameplayDriver(
                    pipe_name,
                    endpoint=endpoint,
                    state_dir=state_dir,
                    save_dir=checkpoint_path.parent,
                )
                endpoint.publish({**_hello("game.state.snapshot"), "pid": 2222})
                endpoint.publish(
                    _snapshot(
                        1,
                        date_raw=date_raw,
                        played_character={
                            "character_id": character_id,
                            "alive": True,
                        },
                    )
                )

                current = driver.take_snapshot()
                self.assertEqual(current["episode_character_id"], character_id)
                self.assertNotEqual(
                    current["episode_run_id"], "native-707-existing"
                )
                self.assertEqual(current["native_command_history"], [])
                self.assertFalse(current["one_life_terminal"])
                control = driver.capabilities()["native_session_control"]
                self.assertFalse(control["driver_state_restored"])
                self.assertEqual(control["driver_state_restore_kind"], "new_episode")
                self.assertEqual(control["episode_binding_state"], "active_new")

    def test_event_wildcard_expands_from_current_option_count(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(
            _snapshot(23, active_event={"instance_id": 419, "option_count": 3})
        )

        capabilities = driver.capabilities()
        self.assertEqual(
            capabilities["action_steps"],
            [
                "select-event-option-1",
                "select-event-option-2",
                "select-event-option-3",
            ],
        )
        self.assertNotIn("select-event-option-N", capabilities["action_steps"])
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["active_event"]["instance_id"], 419)
        self.assertEqual(snapshot["active_event"]["options"][2]["index"], 2)

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"accepted": True},
                    }
                )

        endpoint.send_hook = answer
        driver.execute_step(
            "select-event-option-3",
            expected_revision=int(snapshot["revision"]),
        )
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["step"], "select-event-option-3")
        self.assertEqual(command["expected_revision"], 23)

    def test_pending_character_interaction_routes_native_reply(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.pending-character-interaction",
                "game.command.accept-pending-character-interaction",
                "game.command.reject-pending-character-interaction",
            )
        )
        endpoint.publish(
            _snapshot(
                27,
                pending_character_interaction={
                    "instance_id": 91,
                    "sender_character_id": 4_294_967,
                    "auto_accept_notification": False,
                },
            )
        )
        snapshot = driver.take_snapshot()
        self.assertEqual(
            snapshot["pending_character_interaction"]["instance_id"], 91
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ],
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "status": "submitted"},
                    }
                )
                endpoint.publish(_snapshot(28))

        endpoint.send_hook = answer
        result = driver.execute_step(
            "accept-pending-character-interaction",
            expected_revision=int(snapshot["revision"]),
        )
        self.assertEqual(result["status"], "submitted")
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(
            command["step"], "accept-pending-character-interaction"
        )
        self.assertEqual(command["expected_revision"], 27)
        endpoint.publish(
            _snapshot(
                29,
                pending_character_interaction={
                    "instance_id": 92,
                    "sender_character_id": 4_294_968,
                    "auto_accept_notification": True,
                },
            )
        )
        self.assertEqual(driver.capabilities()["action_steps"], [])

    def test_episode_identity_locks_on_first_ready_character_and_keeps_heir_info(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                28,
                map_ready=False,
                played_character={"character_id": 707, "alive": True},
            )
        )
        self.assertIsNone(driver.take_snapshot()["episode_character_id"])

        endpoint.publish(
            _snapshot(
                29,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": 808,
                    "has_heir": True,
                },
            )
        )
        first_ready = driver.take_snapshot()
        self.assertEqual(first_ready["episode_character_id"], 707)
        self.assertFalse(first_ready["one_life_terminal"])
        self.assertIsNone(first_ready["one_life_terminal_reason"])
        self.assertEqual(first_ready["played_character"]["primary_heir_id"], 808)
        self.assertTrue(first_ready["played_character"]["has_heir"])

        endpoint.publish(
            _snapshot(
                30,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": None,
                    "has_heir": False,
                },
            )
        )
        same_character = driver.take_snapshot()
        capabilities = driver.capabilities()
        self.assertEqual(same_character["episode_character_id"], 707)
        self.assertFalse(same_character["one_life_terminal"])
        self.assertEqual(capabilities["episode_character_id"], 707)
        self.assertFalse(capabilities["one_life_terminal"])
        self.assertNotIn("death-terminal", capabilities["action_steps"])

    def test_played_character_relationship_state_is_preserved(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "betrothed_id": None,
                    "primary_spouse_id": 808,
                    "spouse_ids": [808, 809],
                },
            )
        )

        played = driver.take_snapshot()["played_character"]
        self.assertIsNone(played["betrothed_id"])
        self.assertEqual(played["primary_spouse_id"], 808)
        self.assertEqual(played["spouse_ids"], [808, 809])

    def test_map_ready_without_played_character_does_not_invent_terminal(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(_snapshot(29, played_character=None))

        snapshot = driver.take_snapshot()
        capabilities = driver.capabilities()

        self.assertIsNone(snapshot["episode_character_id"])
        self.assertFalse(snapshot["one_life_terminal"])
        self.assertIsNone(snapshot["one_life_terminal_reason"])
        self.assertIsNone(capabilities["episode_character_id"])
        self.assertNotIn("death-terminal", capabilities["action_steps"])

    def test_dead_played_character_exposes_one_life_terminal(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                30,
                played_character={"character_id": 17_031, "alive": False},
            )
        )
        snapshot = driver.take_snapshot()

        self.assertIn("death-terminal", driver.capabilities()["action_steps"])
        result = driver.execute_step(
            "death-terminal", expected_revision=int(snapshot["revision"])
        )

        self.assertTrue(result["terminal"])
        self.assertEqual(result["terminal_kind"], "native_played_character_dead")
        self.assertEqual(result["terminal_reason"], "played_character_dead")
        self.assertEqual(result["episode_character_id"], 17_031)
        self.assertFalse(result["continue_as_heir_after_death"])
        self.assertEqual(result["played_character"]["character_id"], 17_031)

    def test_native_death_terminal_records_cross_run_strategy(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    30,
                    played_character={"character_id": 17_031, "alive": False},
                )
            )
            snapshot = driver.take_snapshot()

            result = driver.execute_step(
                "death-terminal", expected_revision=int(snapshot["revision"])
            )

            history = result["cross_run_strategy"]
            episode = history["recorded_episode"]
            self.assertEqual(episode["run_id"], snapshot["episode_run_id"])
            self.assertEqual(episode["terminal_reason"], "played_character_dead")
            self.assertFalse(episode["continue_as_heir_after_death"])
            self.assertEqual(episode["heir_gameplay_actions"], 0)
            self.assertIn("death-terminal", episode["successful_steps"])
            persisted = json.loads(
                (state_dir / "strategy" / "one-life-history.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(persisted["episodes"]), 1)
            self.assertEqual(
                persisted["episodes"][0]["run_id"], snapshot["episode_run_id"]
            )

    def test_played_character_switch_ends_episode_before_heir_gameplay(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": 808,
                    "has_heir": True,
                },
            )
        )
        self.assertEqual(driver.take_snapshot()["episode_character_id"], 707)
        endpoint.publish(
            _snapshot(
                32,
                played_character={"character_id": 808, "alive": True},
            )
        )

        switched = driver.take_snapshot()
        capabilities = driver.capabilities()
        service = GameplayBridgeService(driver)
        plan = service.plan_turn()["plan"]
        result = service.auto_turn()

        self.assertEqual(switched["episode_character_id"], 707)
        self.assertTrue(switched["one_life_terminal"])
        self.assertEqual(
            switched["one_life_terminal_reason"], "played_character_changed"
        )
        self.assertIn("death-terminal", capabilities["action_steps"])
        self.assertEqual(plan["phase"], "terminal_native")
        self.assertEqual(plan["selected_step"], "death-terminal")
        self.assertEqual(plan["episode_character_id"], 707)
        self.assertEqual(plan["terminal_reason"], "played_character_changed")
        self.assertEqual(result["status"], "executed")
        self.assertEqual(
            result["result"]["terminal_kind"],
            "native_played_character_changed",
        )
        self.assertEqual(result["result"]["episode_character_id"], 707)
        self.assertFalse(result["result"]["continue_as_heir_after_death"])

    def test_native_war_templates_expand_and_move_waits_for_target(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.war-primary-opponent",
                "game.command.move-army-N-to-N",
                "game.command.disband-army-N",
            )
        )
        player = _army(101, soldiers=1_500, province_id=11)
        enemy = _army(
            202,
            soldiers=2_400,
            province_id=33,
            controllable=False,
        )
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                player_armies=[player],
            )
        )

        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["disband-army-101", "move-army-101-to-33"],
        )
        before = driver.take_snapshot()
        self.assertEqual(before["active_wars"][0]["enemy_armies"][0]["soldiers"], 2_400)
        self.assertEqual(
            before["active_wars"][0]["primary_opponent_character_id"], 808
        )
        self.assertTrue(
            before["active_wars"][0]["player_is_primary_war_leader"]
        )
        self.assertEqual(
            before["active_wars"][0][
                "enemy_primary_default_raise_province_id"
            ],
            77,
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            moving = _army(
                101,
                soldiers=1_500,
                province_id=11,
                move_target_province_id=33,
            )
            endpoint.publish(
                _snapshot(
                    41,
                    active_wars=[
                        _war(allied_armies=[moving], enemy_armies=[enemy])
                    ],
                    player_armies=[moving],
                )
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "move-army-101-to-33",
            expected_revision=int(before["revision"]),
        )

        self.assertEqual(result["war_action"]["status"], "moving")
        self.assertEqual(result["war_action"]["target_province_id"], 33)
        command = next(
            frame for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["step"], "move-army-101-to-33")
        self.assertEqual(command["expected_revision"], 40)
        self.assertNotIn(
            "move-army-101-to-33", driver.capabilities()["action_steps"]
        )

    def test_exact_war_capability_expands_fallback_and_filters_enforce(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-primary-opponent",
                "game.command.move-army-N-to-N",
                "game.command.enforce-demands-N",
            )
        )
        player = _army(101, province_id=11)
        allied_war = _war(
            war_id=404,
            allied_armies=[player],
            score=100,
            player_is_primary_war_leader=False,
            enemy_primary_default_raise_province_id=77,
        )
        endpoint.publish(
            _snapshot(
                42,
                active_wars=[allied_war],
                player_armies=[player],
            )
        )

        action_steps = driver.capabilities()["action_steps"]

        self.assertIn("move-army-101-to-77", action_steps)
        self.assertNotIn("enforce-demands-404", action_steps)

        primary_war = {
            **allied_war,
            "player_is_primary_war_leader": True,
        }
        endpoint.publish(
            _snapshot(
                43,
                active_wars=[primary_war],
                player_armies=[player],
            )
        )
        self.assertIn(
            "enforce-demands-404", driver.capabilities()["action_steps"]
        )

    def test_legacy_war_adapter_keeps_previous_enforce_advertisement(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.enforce-demands-N",
            )
        )
        legacy_war = _war(war_id=405, score=12)
        legacy_war.pop("primary_opponent_character_id")
        legacy_war.pop("player_is_primary_war_leader")
        legacy_war.pop("enemy_primary_default_raise_province_id")
        endpoint.publish(_snapshot(44, active_wars=[legacy_war]))

        snapshot = driver.take_snapshot()

        self.assertIsNone(
            snapshot["active_wars"][0]["player_is_primary_war_leader"]
        )
        self.assertIn(
            "enforce-demands-405", driver.capabilities()["action_steps"]
        )

    def test_native_war_primary_fields_reject_malformed_values(self) -> None:
        endpoint = FakeEndpoint()
        NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        malformed_values = (
            ("primary_opponent_character_id", "808"),
            ("player_is_primary_war_leader", 1),
            ("enemy_primary_default_raise_province_id", -1),
        )
        for revision, (field, value) in enumerate(
            malformed_values, start=45
        ):
            with self.subTest(field=field):
                war = {**_war(), field: value}
                with self.assertRaises(ValueError):
                    endpoint.publish(
                        _snapshot(revision, active_wars=[war])
                    )

    def test_native_declaration_query_expands_and_starts_war(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.declarable-wars",
                "game.command.query-declarable-wars",
                "game.command.declare-war-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
            )
        )
        declaration = {
            "declaration_id": "808-17-0",
            "target_character_id": 808,
            "casus_belli_index": 17,
            "casus_belli_key": "county_conquest_cb",
            "configuration_index": 0,
            "claimant_character_id": -1,
            "target_title_ids": [91],
        }

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            result: dict[str, object] = {
                "step": frame["step"],
                "accepted": True,
                "status": "submitted",
            }
            if frame["step"] == "query-declarable-wars":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 3,
                        "declarable_wars": [declaration],
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )
            if frame["step"].startswith("declare-war-"):
                endpoint.publish(
                    _snapshot(
                        41,
                        played_character={"character_id": 707, "alive": True},
                        active_wars=[_war(73)],
                    )
                )

        endpoint.send_hook = answer
        starting = driver.take_snapshot()
        query = driver.execute_step(
            "query-declarable-wars",
            expected_revision=int(starting["revision"]),
        )
        self.assertEqual(query["declarable_wars"][0]["casus_belli_key"], "county_conquest_cb")
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["declare-war-808-17-0", "query-declarable-wars"],
        )
        queried = driver.take_snapshot()
        self.assertEqual(queried["declaration_query_sequence"], 3)

        declared = driver.execute_step(
            "declare-war-808-17-0",
            expected_revision=int(queried["revision"]),
        )
        self.assertEqual(declared["war_action"]["status"], "war_started")
        self.assertEqual(declared["war_action"]["target_character_id"], 808)
        self.assertEqual(driver.take_snapshot()["declarable_wars"], [])

    def test_native_marriage_query_expands_and_submits_exact_choice(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-arrange-marriage-choices",
                "game.command.arrange-marriage-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
            )
        )
        choice = {
            "choice_id": "707-808",
            "played_character_id": 707,
            "candidate_character_id": 808,
        }

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            result: dict[str, object] = {
                "step": frame["step"],
                "accepted": True,
                "status": "submitted",
            }
            if frame["step"] == "query-arrange-marriage-choices":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 4,
                        "arrange_marriage_choices": [choice],
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )

        endpoint.send_hook = answer
        starting = driver.take_snapshot()
        query = driver.execute_step(
            "query-arrange-marriage-choices",
            expected_revision=int(starting["revision"]),
        )
        self.assertEqual(query["arrange_marriage_choices"], [{**choice, "source": "native"}])
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["arrange-marriage-707-808", "query-arrange-marriage-choices"],
        )

        queried = driver.take_snapshot()
        submitted = driver.execute_step(
            "arrange-marriage-707-808",
            expected_revision=int(queried["revision"]),
        )
        self.assertEqual(
            submitted["marriage_action"]["status"], "proposal_submitted"
        )
        self.assertEqual(
            submitted["marriage_action"]["candidate_character_id"], 808
        )
        self.assertEqual(driver.take_snapshot()["arrange_marriage_choices"], [])

    def test_native_raise_and_postwar_disband_wait_for_army_state(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.command.raise-troops-default",
                "game.command.disband-army-N",
            )
        )
        enemy = _army(
            302,
            soldiers=None,
            province_id=44,
            controllable=False,
        )
        endpoint.publish(
            _snapshot(50, active_wars=[_war(enemy_armies=[enemy])])
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["raise-troops-default"],
        )

        def answer_raise(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            raised = _army(303, province_id=12)
            endpoint.publish(
                _snapshot(
                    51,
                    active_wars=[
                        _war(allied_armies=[raised], enemy_armies=[enemy])
                    ],
                    player_armies=[raised],
                )
            )

        endpoint.send_hook = answer_raise
        raised = driver.execute_step("raise-troops-default")
        self.assertEqual(raised["war_action"]["raised_army_ids"], [303])

        remaining = _army(303, province_id=12)
        endpoint.publish(_snapshot(52, active_wars=[], player_armies=[remaining]))
        self.assertEqual(
            driver.capabilities()["action_steps"], ["disband-army-303"]
        )

        def answer_disband(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            endpoint.publish(_snapshot(53, active_wars=[], player_armies=[]))

        endpoint.send_hook = answer_disband
        disbanded = driver.execute_step("disband-army-303")
        self.assertEqual(disbanded["war_action"]["status"], "disbanded")
        self.assertEqual(disbanded["player_armies"], [])

    def test_native_enforce_demands_ends_war_before_more_army_orders(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.war-primary-opponent",
                "game.command.enforce-demands-N",
            )
        )
        won_war = _war(war_id=404)
        won_war["player_relative_war_score"] = 100
        endpoint.publish(_snapshot(60, active_wars=[won_war]))

        snapshot = driver.take_snapshot()
        self.assertIn(
            "enforce-demands-404", driver.capabilities()["action_steps"]
        )
        plan = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-404")

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            endpoint.publish(_snapshot(61, active_wars=[]))

        endpoint.send_hook = answer
        result = driver.execute_step(
            "enforce-demands-404",
            expected_revision=int(snapshot["revision"]),
        )

        self.assertEqual(result["war_action"]["status"], "victory_enforced")
        self.assertEqual(result["war_victory"]["war_id"], 404)
        self.assertEqual(result["active_wars"], [])

    def test_native_move_without_target_observation_uses_submission_ack(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.move-army-N-to-N",
            )
        )
        player = _army(401, province_id=None, observe_move_target=False)
        enemy = _army(402, province_id=90, controllable=False)
        endpoint.publish(
            _snapshot(
                60,
                active_wars=[_war(allied_armies=[player], enemy_armies=[enemy])],
                player_armies=[player],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"status": "submitted"},
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step("move-army-401-to-90")

        self.assertEqual(result["war_action"]["status"], "move_submitted")
        self.assertFalse(result["war_action"]["move_target_observable"])
        self.assertEqual(
            result["war_action"]["submitted_date_raw"], 53_171_400
        )

    def test_native_move_not_ready_is_a_deferred_war_action(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.move-army-N-to-N",
            )
        )
        player = _army(401, province_id=20, observe_move_target=False)
        enemy = _army(402, province_id=90, controllable=False)
        endpoint.publish(
            _snapshot(
                60,
                active_wars=[_war(allied_armies=[player], enemy_armies=[enemy])],
                player_armies=[player],
            )
        )

        native_error = "CK3 army state rejects movement"

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": False,
                        "error": native_error,
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step("move-army-401-to-90")

        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "deferred")
        self.assertEqual(result["war_action"]["status"], "move_deferred")
        self.assertEqual(
            result["war_action"]["reason"], "army_not_move_ready"
        )

    def test_save_checkpoint_waits_for_isolated_file_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            save_dir = Path(temporary) / "profile" / "save games"
            save_dir.mkdir(parents=True)
            checkpoint_path = save_dir / "xar_checkpoint.ck3"
            checkpoint_path.write_bytes(b"old checkpoint")
            old_mtime = checkpoint_path.stat().st_mtime_ns
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=Path(temporary) / "state",
                save_dir=save_dir,
                checkpoint_timeout_seconds=1.0,
                checkpoint_poll_interval_seconds=0.005,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.command.save-checkpoint")
            )
            endpoint.publish(
                _snapshot(
                    31,
                    date_raw=53_171_424,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            payload = b"materialized native checkpoint"
            timer: threading.Timer | None = None

            def answer(frame: dict[str, object]) -> None:
                nonlocal timer
                if frame.get("type") != "execute_step":
                    return
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": "save-checkpoint",
                            "accepted": True,
                            "status": "submitted",
                            "submission": {
                                "sequence": 2,
                                "requested_save_name": "xar_checkpoint",
                                "date_raw": 53_171_424,
                            },
                        },
                    }
                )

                def materialize() -> None:
                    checkpoint_path.write_bytes(payload)
                    changed_mtime = old_mtime + 1_000_000_000
                    os.utime(
                        checkpoint_path,
                        ns=(changed_mtime, changed_mtime),
                    )

                timer = threading.Timer(0.02, materialize)
                timer.start()

            endpoint.send_hook = answer
            snapshot = driver.take_snapshot()
            result = driver.execute_step(
                "save-checkpoint",
                expected_revision=int(snapshot["revision"]),
            )
            if timer is not None:
                timer.join(timeout=1.0)

            checkpoint = result["checkpoint"]
            self.assertEqual(checkpoint["status"], "saved")
            self.assertEqual(checkpoint["name"], "xar_checkpoint.ck3")
            self.assertEqual(checkpoint["path"], str(checkpoint_path.resolve()))
            self.assertEqual(checkpoint["size"], len(payload))
            self.assertEqual(
                checkpoint["sha256"], hashlib.sha256(payload).hexdigest()
            )
            self.assertEqual(checkpoint["date_raw"], 53_171_424)
            self.assertEqual(checkpoint["history_index"], 1)
            self.assertEqual(checkpoint["episode_character_id"], 707)
            self.assertEqual(
                checkpoint["episode_run_id"], snapshot["episode_run_id"]
            )
            self.assertTrue(checkpoint["overwrite_confirmed"])
            self.assertTrue(result["materialization"]["available"])
            plan = GameplayBridgeService(driver).plan_turn()["plan"]
            self.assertNotEqual(plan.get("selected_step"), "save-checkpoint")
            self.assertEqual(plan.get("required_step"), "dynasty-review")

    def test_save_checkpoint_without_directory_keeps_submission_explicit(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.save-checkpoint")
        )
        endpoint.publish(_snapshot(8, date_raw=53_171_448))

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": "save-checkpoint",
                            "accepted": True,
                            "status": "submitted",
                            "submission": {
                                "sequence": 1,
                                "requested_save_name": "xar_checkpoint",
                                "date_raw": 53_171_448,
                            },
                        },
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step("save-checkpoint")

        self.assertTrue(result["accepted"])
        self.assertEqual(
            result["checkpoint"]["status"], "materialization_unavailable"
        )
        self.assertIsNone(result["checkpoint"]["path"])
        self.assertFalse(result["materialization"]["available"])
        self.assertEqual(
            result["materialization"]["reason"], "save_dir_not_configured"
        )

    def test_restore_checkpoint_relaunches_and_waits_for_new_map_generation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            save_dir = state_dir / "profile" / "save games"
            save_dir.mkdir(parents=True)
            checkpoint_path = save_dir / "xar_checkpoint.ck3"
            checkpoint_payload = b"native restore checkpoint fixture"
            checkpoint_path.write_bytes(checkpoint_payload)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=save_dir,
                restore_timeout_seconds=1.0,
                restore_poll_interval_seconds=0.005,
            )
            endpoint.publish(_hello("game.state.snapshot"))
            endpoint.publish(
                _snapshot(
                    40,
                    date_raw=53_171_520,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            lifecycle_errors: list[BaseException] = []
            observed_request: dict[str, object] = {}

            def lifecycle() -> None:
                try:
                    inbox = (
                        state_dir
                        / "native-session"
                        / "bridge"
                        / "inbox"
                    )
                    deadline = time.monotonic() + 1.0
                    request_paths: list[Path] = []
                    while time.monotonic() < deadline:
                        request_paths = list(inbox.glob("restore-*.json"))
                        if request_paths:
                            break
                        time.sleep(0.005)
                    self.assertEqual(len(request_paths), 1)
                    request_path = request_paths[0]
                    observed_request.update(
                        json.loads(request_path.read_text(encoding="utf-8"))
                    )
                    assert endpoint.on_disconnect is not None
                    endpoint.on_disconnect()
                    outbox = request_path.parents[1] / "outbox"
                    write_json_atomic(
                        outbox / request_path.name,
                        {
                            "protocol_version": 1,
                            "request_id": request_path.stem,
                            "ok": True,
                            "result": {
                                "status": "relaunched",
                                "previous_pid": 4242,
                                "pid": 5252,
                                "pipe": endpoint.pipe_name,
                                "continue_last_save": False,
                                "load_save_name": "xar_checkpoint",
                                "checkpoint": {
                                    "name": "xar_checkpoint.ck3",
                                    "size": len(checkpoint_payload),
                                    "sha256": hashlib.sha256(
                                        checkpoint_payload
                                    ).hexdigest(),
                                    "saved_date_raw": None,
                                },
                            },
                            "error": None,
                        },
                    )
                    endpoint.publish(
                        {
                            **_hello("game.state.snapshot"),
                            "pid": 5252,
                            "session_generation": 1,
                        }
                    )
                    endpoint.publish(
                        _snapshot(
                            1,
                            date_raw=53_171_400,
                            map_ready=True,
                            played_character={
                                "character_id": 707,
                                "alive": True,
                            },
                        )
                    )
                    # Loading can publish one map-ready projection and then
                    # immediately replace it.  Restore must return the settled
                    # semantic revision, not the first transient map frame.
                    time.sleep(0.05)
                    endpoint.publish(
                        _snapshot(
                            2,
                            date_raw=53_171_424,
                            map_ready=True,
                            played_character={
                                "character_id": 707,
                                "alive": True,
                            },
                        )
                    )
                except BaseException as error:
                    lifecycle_errors.append(error)

            worker = threading.Thread(target=lifecycle)
            worker.start()
            snapshot = driver.take_snapshot()
            self.assertIn(
                "restore-checkpoint", driver.capabilities()["action_steps"]
            )
            result = driver.execute_step(
                "restore-checkpoint",
                expected_revision=int(snapshot["revision"]),
            )
            worker.join(timeout=1.0)

            self.assertFalse(worker.is_alive())
            self.assertEqual(lifecycle_errors, [])
            self.assertEqual(
                observed_request["command"], "restore-checkpoint"
            )
            self.assertEqual(observed_request["pipe"], endpoint.pipe_name)
            self.assertEqual(
                observed_request["checkpoint_name"], "xar_checkpoint.ck3"
            )
            self.assertEqual(
                observed_request["checkpoint_size"], len(checkpoint_payload)
            )
            self.assertEqual(
                observed_request["checkpoint_sha256"],
                hashlib.sha256(checkpoint_payload).hexdigest(),
            )
            self.assertEqual(result["status"], "restored")
            self.assertEqual(result["restored_date_raw"], 53_171_424)
            self.assertEqual(result["checkpoint"]["status"], "restored")
            self.assertEqual(
                result["checkpoint"]["sha256"],
                hashlib.sha256(checkpoint_payload).hexdigest(),
            )
            self.assertEqual(
                result["lifecycle"]["previous_connection_generation"], 1
            )
            self.assertEqual(result["lifecycle"]["connection_generation"], 2)
            self.assertEqual(result["lifecycle"]["previous_pid"], 4242)
            self.assertEqual(result["lifecycle"]["pid"], 5252)
            self.assertTrue(result["map_ready"])
            restored_snapshot = driver.take_snapshot()
            self.assertEqual(restored_snapshot["episode_character_id"], 707)
            self.assertFalse(restored_snapshot["one_life_terminal"])
            self.assertIsNone(restored_snapshot["one_life_terminal_reason"])

    def test_composite_life_advance_resolves_native_event_and_stays_paused(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=1.0,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(_snapshot(1, map_ready=False))
        timers: list[threading.Timer] = []

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(_snapshot(3, speed=5))
            elif step == "resume-map":
                endpoint.publish(_snapshot(4, speed=5, paused=False))
                timer = threading.Timer(
                    0.01,
                    lambda: endpoint.publish(
                        _snapshot(
                            5,
                            date_raw=53_171_424,
                            speed=5,
                            paused=False,
                            active_event={"instance_id": 77, "option_count": 2},
                        )
                    ),
                )
                timers.append(timer)
                timer.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        6,
                        date_raw=53_171_424,
                        speed=5,
                        active_event={"instance_id": 77, "option_count": 2},
                    )
                )
            elif step == "select-event-option-1":
                endpoint.publish(
                    _snapshot(7, date_raw=53_171_424, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        capabilities = driver.capabilities()
        self.assertIn("life-advance", capabilities["action_steps"])
        self.assertEqual(capabilities["composite_action_steps"], ["life-advance"])
        starting_revision = int(driver.take_snapshot()["revision"])
        ready_timer = threading.Timer(
            0.02, lambda: endpoint.publish(_snapshot(2, map_ready=True))
        )
        timers.append(ready_timer)
        ready_timer.start()

        result = driver.execute_step(
            "life-advance", expected_revision=starting_revision
        )
        for timer in timers:
            timer.join(timeout=1.0)

        commands = [
            frame["step"]
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(
            commands,
            [
                "set-speed-5",
                "resume-map",
                "pause-map",
                "select-event-option-1",
            ],
        )
        self.assertEqual(result["starting_date_raw"], 53_171_400)
        self.assertEqual(result["ending_date_raw"], 53_171_424)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])
        self.assertEqual(result["event_resolution"], "selected")
        self.assertEqual(
            result["ordinary_events"][0]["selected_option_number"], 1
        )
        self.assertIsNone(result["active_event"])

    def test_composite_life_advance_can_stop_after_date_without_event(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
            )
        )
        endpoint.publish(_snapshot(1))
        stale_revision = int(driver.take_snapshot()["revision"])
        endpoint.publish(_snapshot(2, date_raw=53_171_424))

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(3, date_raw=53_171_424, speed=5)
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        4,
                        date_raw=53_171_448,
                        speed=5,
                        paused=False,
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(5, date_raw=53_171_448, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "life-advance", expected_revision=stale_revision
        )

        self.assertEqual(result["ordinary_events"], [])
        self.assertEqual(result["event_resolution"], "none")
        self.assertEqual(result["starting_date_raw"], 53_171_424)
        self.assertEqual(result["ending_date_raw"], 53_171_448)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])

    def test_active_war_life_advance_ignores_day_tick_and_enemy_motion(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        enemy = _army(502, province_id=90, controllable=False)
        starting_war = _war(
            allied_armies=[player], enemy_armies=[enemy]
        )
        endpoint.publish(
            _snapshot(
                70,
                date_raw=start_date,
                active_wars=[starting_war],
                player_armies=[player],
            )
        )
        timers: list[threading.Timer] = []

        def publish_running(
            revision: int,
            *,
            date_raw: int,
            score: int,
            enemy_province_id: int,
        ) -> None:
            moved_enemy = _army(
                502,
                province_id=enemy_province_id,
                controllable=False,
            )
            endpoint.publish(
                _snapshot(
                    revision,
                    date_raw=date_raw,
                    speed=5,
                    paused=False,
                    active_wars=[
                        _war(
                            allied_armies=[player],
                            enemy_armies=[moved_enemy],
                            score=score,
                        )
                    ],
                    player_armies=[player],
                )
            )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        71,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[starting_war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                publish_running(
                    72,
                    date_raw=start_date,
                    score=12,
                    enemy_province_id=90,
                )
                day_tick = threading.Timer(
                    0.01,
                    lambda: publish_running(
                        73,
                        date_raw=start_date + 24,
                        score=12,
                        enemy_province_id=91,
                    ),
                )
                score_tick = threading.Timer(
                    0.03,
                    lambda: publish_running(
                        74,
                        date_raw=start_date + 48,
                        score=13,
                        enemy_province_id=92,
                    ),
                )
                timers.extend((day_tick, score_tick))
                day_tick.start()
                score_tick.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        75,
                        date_raw=start_date + 48,
                        speed=5,
                        paused=True,
                        active_wars=[
                            _war(
                                allied_armies=[player],
                                enemy_armies=[enemy],
                                score=13,
                            )
                        ],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        for timer in timers:
            timer.join(timeout=1.0)

        self.assertEqual(result["elapsed_days"], 2)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertTrue(result["paused"])

    def test_active_war_life_advance_wall_timeout_keeps_date_progress(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.05,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        war = _war(allied_armies=[player])
        endpoint.publish(
            _snapshot(
                80,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[player],
            )
        )
        timer: threading.Timer | None = None

        def answer(frame: dict[str, object]) -> None:
            nonlocal timer
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        81,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        82,
                        date_raw=start_date,
                        speed=5,
                        paused=False,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
                timer = threading.Timer(
                    0.01,
                    lambda: endpoint.publish(
                        _snapshot(
                            83,
                            date_raw=start_date + 24,
                            speed=5,
                            paused=False,
                            active_wars=[war],
                            player_armies=[player],
                        )
                    ),
                )
                timer.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        84,
                        date_raw=start_date + 24,
                        speed=5,
                        paused=True,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        if timer is not None:
            timer.join(timeout=1.0)

        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(
            result["progress_status"], "wall_timeout_with_date_progress"
        )
        self.assertTrue(result["paused"])

    def test_active_war_life_advance_stops_at_thirty_day_horizon(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        war = _war(allied_armies=[player])
        endpoint.publish(
            _snapshot(
                90,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[player],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        91,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        92,
                        date_raw=start_date + 30 * 24,
                        speed=5,
                        paused=False,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        93,
                        date_raw=start_date + 30 * 24,
                        speed=5,
                        paused=True,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")

        self.assertEqual(result["elapsed_days"], 30)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertTrue(result["paused"])

    def test_composite_life_advance_retries_one_natural_revision_race(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-5",
            )
        )
        endpoint.publish(_snapshot(1))
        original_take_snapshot = driver.take_snapshot
        calls = 0

        def racing_snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                endpoint.publish(_snapshot(2, date_raw=53_171_424))
            return original_take_snapshot()

        driver.take_snapshot = racing_snapshot  # type: ignore[method-assign]

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(3, date_raw=53_171_424, speed=5)
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        4,
                        date_raw=53_171_448,
                        speed=5,
                        paused=False,
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(5, date_raw=53_171_448, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")

        wire_steps = [
            frame["step"]
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(wire_steps, ["set-speed-5", "resume-map", "pause-map"])
        self.assertEqual(result["starting_date_raw"], 53_171_400)
        self.assertEqual(result["ending_date_raw"], 53_171_448)
        self.assertTrue(result["paused"])

    def test_command_result_does_not_forge_a_semantic_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.life-advance")
        )
        endpoint.publish(_snapshot(19))
        before = driver.take_snapshot()

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "accepted": True},
                    }
                )

        endpoint.send_hook = answer
        driver.execute_step(
            "life-advance", expected_revision=int(before["revision"])
        )
        after = driver.wait_for_change(
            int(before["revision"]), timeout_seconds=0.001
        )

        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(after["native_revision"], before["native_revision"])
        self.assertEqual(after["snapshot_id"], before["snapshot_id"])

    def test_error_frame_is_diagnostic_not_a_semantic_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        endpoint.publish(_snapshot(4))
        before = driver.take_snapshot()

        endpoint.publish(
            {
                "type": "error",
                "protocol_version": 1,
                "error": "fixture diagnostic",
            }
        )
        after = driver.wait_for_change(
            int(before["revision"]), timeout_seconds=0.001
        )

        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(
            driver.diagnostics()["last_error"]["error"],
            "fixture diagnostic",
        )

    def test_disconnect_removes_semantic_state(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        endpoint.publish(_snapshot())
        endpoint.on_disconnect()

        self.assertFalse(driver.capabilities()["snapshot"])
        with self.assertRaises(BridgeUnavailableError):
            driver.take_snapshot()

    def test_repeated_native_snapshot_does_not_forge_a_public_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        frame = _snapshot(7)
        endpoint.publish(frame)
        first = driver.take_snapshot()

        endpoint.publish(dict(frame))
        second = driver.take_snapshot()

        self.assertEqual(second["revision"], first["revision"])
        self.assertEqual(second["native_revision"], 7)

    def test_fatal_transport_error_is_visible_and_blocks_snapshot(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.error = "fixture CreateNamedPipeW failure"

        capabilities = driver.capabilities()
        self.assertFalse(capabilities["transport_ready"])
        self.assertEqual(
            capabilities["diagnostics"]["transport_fatal_error"],
            endpoint.error,
        )
        with self.assertRaisesRegex(BridgeUnavailableError, "CreateNamedPipeW"):
            driver.take_snapshot()


class NativeFallbackModeTests(unittest.TestCase):
    def test_minimized_visual_fallback_is_refused_without_execution(self) -> None:
        calls: list[str] = []
        visual = CallbackGameplayDriver(
            backend_id="vision-session",
            snapshot=lambda: {
                "snapshot_id": "vision:1",
                "revision": 1,
                "history": [],
            },
            execute=lambda step, _revision: calls.append(step) or {},
            action_steps=("marriage-review",),
        )
        guarded = MinimizedRejectingVisualDriver(
            visual,
            window_minimized=lambda: True,
        )

        with self.assertRaisesRegex(BridgeUnavailableError, "minimized"):
            guarded.execute_step("marriage-review")
        self.assertEqual(calls, [])
        self.assertFalse(guarded.capabilities()["visual_fallback_when_minimized"])

    def test_unknown_window_state_also_refuses_visual_fallback(self) -> None:
        calls: list[str] = []
        guarded = MinimizedRejectingVisualDriver(
            CallbackGameplayDriver(
                backend_id="vision-session",
                snapshot=lambda: {"snapshot_id": "vision:1", "revision": 1},
                execute=lambda step, _revision: calls.append(step) or {},
                action_steps=("life-advance",),
            ),
            window_minimized=lambda: None,
        )

        with self.assertRaisesRegex(BridgeUnavailableError, "visibility is unknown"):
            guarded.execute_step("life-advance")
        self.assertEqual(calls, [])

    def test_hybrid_fallback_order_is_explicit_and_guarded(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("bridge.identity", "bridge.heartbeat", "bridge.ping")
        )
        data_mod = CallbackGameplayDriver(
            backend_id="data-mod",
            snapshot=lambda: {
                "snapshot_id": "mod:1",
                "revision": 1,
                "history": [],
                "date": "1066.9.15",
            },
            execute=lambda _step, _revision: {},
            action_steps=(),
        )
        calls: list[str] = []
        visual = MinimizedRejectingVisualDriver(
            CallbackGameplayDriver(
                backend_id="vision-session",
                snapshot=lambda: {
                    "snapshot_id": "vision:2",
                    "revision": 2,
                    "history": [],
                },
                execute=lambda step, _revision: calls.append(step) or {},
                action_steps=("marriage-review",),
            ),
            window_minimized=lambda: True,
        )
        driver = ConfiguredHybridFallbackDriver(native, data_mod, visual)

        capabilities = driver.capabilities()
        self.assertEqual(
            capabilities["fallback_order"],
            ["native-headless", "data-mod", "vision-session-guarded"],
        )
        self.assertTrue(capabilities["fallback_enabled"])
        self.assertFalse(capabilities["visual_fallback_when_minimized"])
        self.assertEqual(driver.take_snapshot()["date"], "1066.9.15")
        with self.assertRaisesRegex(BridgeUnavailableError, "minimized"):
            driver.execute_step("marriage-review")
        self.assertEqual(calls, [])

    def test_restore_checkpoint_never_uses_hybrid_visual_fallback(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        visual_calls: list[str] = []
        driver = ConfiguredHybridFallbackDriver(
            native,
            CallbackGameplayDriver(
                backend_id="data-mod",
                snapshot=lambda: {
                    "snapshot_id": "mod:1",
                    "revision": 1,
                },
                execute=lambda _step, _revision: {},
                action_steps=(),
            ),
            MinimizedRejectingVisualDriver(
                CallbackGameplayDriver(
                    backend_id="vision-session",
                    snapshot=lambda: {
                        "snapshot_id": "vision:1",
                        "revision": 1,
                    },
                    execute=lambda step, _revision: visual_calls.append(step) or {},
                    action_steps=("restore-checkpoint",),
                ),
                window_minimized=lambda: False,
            ),
        )

        self.assertNotIn(
            "restore-checkpoint", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("restore-checkpoint")
        self.assertEqual(visual_calls, [])

    def test_native_war_command_never_uses_hybrid_visual_fallback(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        visual_calls: list[str] = []
        driver = ConfiguredHybridFallbackDriver(
            native,
            CallbackGameplayDriver(
                backend_id="data-mod",
                snapshot=lambda: {"snapshot_id": "mod:1", "revision": 1},
                execute=lambda _step, _revision: {},
                action_steps=(),
            ),
            MinimizedRejectingVisualDriver(
                CallbackGameplayDriver(
                    backend_id="vision-session",
                    snapshot=lambda: {
                        "snapshot_id": "vision:1",
                        "revision": 1,
                    },
                    execute=lambda step, _revision: visual_calls.append(step) or {},
                    action_steps=(
                        "move-army-7-to-9",
                        "query-declarable-wars",
                        "declare-war-808-17-0",
                        "query-arrange-marriage-choices",
                        "arrange-marriage-707-809",
                    ),
                ),
                window_minimized=lambda: False,
            ),
        )

        self.assertNotIn(
            "move-army-7-to-9", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("move-army-7-to-9")
        self.assertNotIn(
            "declare-war-808-17-0", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("declare-war-808-17-0")
        self.assertNotIn(
            "arrange-marriage-707-809", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("arrange-marriage-707-809")
        self.assertEqual(visual_calls, [])


@unittest.skipUnless(os.name == "nt", "Windows named-pipe integration")
class NativeNamedPipeIntegrationTests(unittest.TestCase):
    def test_real_pipe_receives_dll_frames_and_returns_ping(self) -> None:
        try:
            import pywintypes
            import win32file
            import win32pipe
        except ImportError:
            self.skipTest("pywin32 unavailable")
        pipe_name = rf"\\.\pipe\xar_python_test_{uuid.uuid4().hex}"
        driver = NativeHeadlessGameplayDriver(pipe_name)
        client = None
        try:
            deadline = time.monotonic() + 3.0
            while client is None:
                try:
                    client = win32file.CreateFile(
                        pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None,
                    )
                except pywintypes.error as error:
                    if time.monotonic() >= deadline:
                        raise
                    if error.winerror not in (2, 231):
                        raise
                    time.sleep(0.01)
            win32pipe.SetNamedPipeHandleState(
                client, win32pipe.PIPE_READMODE_BYTE, None, None
            )
            _client_write_frame(win32file, client, _hello("bridge.ping"))
            ping = _client_read_frame(win32file, client)
            self.assertEqual(ping["type"], "ping")
            _client_write_frame(
                win32file,
                client,
                {
                    "type": "heartbeat",
                    "protocol_version": 1,
                    "sequence": 11,
                    "pid": 4242,
                    "monotonic_ms": 750,
                },
            )
            _client_write_frame(
                win32file,
                client,
                {
                    "type": "pong",
                    "protocol_version": 1,
                    "request_id": ping["request_id"],
                    "pid": 4242,
                },
            )
            deadline = time.monotonic() + 2.0
            while driver.diagnostics()["last_pong"] is None:
                if time.monotonic() >= deadline:
                    self.fail("native pipe server did not ingest pong")
                time.sleep(0.01)
            self.assertEqual(
                driver.diagnostics()["last_heartbeat"]["sequence"], 11
            )
        finally:
            if client is not None:
                win32file.CloseHandle(client)
            driver.close()


def _client_write_frame(win32file, client, frame: dict[str, object]) -> None:
    payload = json.dumps(frame, separators=(",", ":")).encode("utf-8")
    win32file.WriteFile(client, struct.pack("<I", len(payload)) + payload)


def _client_read_frame(win32file, client) -> dict[str, object]:
    _status, header = win32file.ReadFile(client, 4)
    size = struct.unpack("<I", header)[0]
    _status, payload = win32file.ReadFile(client, size)
    result = json.loads(payload.decode("utf-8"))
    assert isinstance(result, dict)
    return result


if __name__ == "__main__":
    unittest.main()
