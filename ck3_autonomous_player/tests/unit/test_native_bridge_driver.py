from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import sys
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


def _snapshot(revision: int = 1) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "history": [],
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
