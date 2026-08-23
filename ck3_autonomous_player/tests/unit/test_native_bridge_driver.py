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
        },
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
                save_dir=save_dir,
                checkpoint_timeout_seconds=1.0,
                checkpoint_poll_interval_seconds=0.005,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.command.save-checkpoint")
            )
            endpoint.publish(_snapshot(31, date_raw=53_171_424))
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
            self.assertTrue(checkpoint["overwrite_confirmed"])
            self.assertTrue(result["materialization"]["available"])

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
