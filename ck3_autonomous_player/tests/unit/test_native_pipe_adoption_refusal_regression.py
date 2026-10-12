"""Terminal lifecycle refusals through the real pipe worker and Driver callback.

Only pipe I/O is synthetic. State-byte assertions concern the small state created
by this fixture; hello ingestion and disconnect still change protocol memory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import threading
from unittest import mock

import pytest

from xar_autoplayer.bridge import native_driver
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    NativeNamedPipeServer,
)
from test_succession_transition_contract import (
    _FakeEndpoint,
    _hello,
    _native_snapshot,
    _ordinary_binding,
)


def _persisted_rogue_state(state_dir: Path, *, legacy: bool) -> tuple[str, Path]:
    fixture_endpoint = _FakeEndpoint()
    producer = NativeHeadlessGameplayDriver(
        fixture_endpoint.pipe_name, endpoint=fixture_endpoint, state_dir=state_dir
    )
    try:
        fixture_endpoint.publish(_hello())
        fixture_endpoint.publish(
            _native_snapshot(20, character_id=100, date_raw=53_180_000)
        )
        producer.take_snapshot()
    finally:
        producer.close()
    state_path = state_dir / "native-session" / "driver-state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert isinstance(payload["succession_lifecycle"], dict)
    if legacy:
        payload.pop("succession_lifecycle")
        state_path.write_text(json.dumps(payload), encoding="utf-8")
    return fixture_endpoint.pipe_name, state_path


def _packet(frame: dict[str, object]) -> bytes:
    body = json.dumps(frame, separators=(",", ":")).encode("utf-8")
    return struct.pack("<I", len(body)) + body


@pytest.mark.skipif(os.name != "nt", reason="production named-pipe worker requires Windows")
@pytest.mark.parametrize(
    ("legacy", "reason"),
    [
        pytest.param(True, "legacy_lifecycle_incompatible", id="legacy"),
        pytest.param(False, "persisted_lifecycle_mismatch", id="mismatch"),
    ],
)
def test_adoption_refusal_stops_real_worker_without_rewriting_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, legacy: bool, reason: str
) -> None:
    pipe_name, state_path = _persisted_rogue_state(tmp_path, legacy=legacy)
    before = state_path.read_bytes()
    first_hello = dict(_hello(), pid=5252)
    second_packet = _packet(dict(_hello(), pid=9898))
    first_packet = _packet(first_hello)
    unread = bytearray(first_packet + second_packet)
    handle = 7001
    allow_connection = threading.Event()
    worker_done = threading.Event()
    escaped: list[threading.ExceptHookArgs] = []
    monkeypatch.setattr(threading, "excepthook", escaped.append)

    def connect(requested_handle: int) -> tuple[bool, int]:
        assert requested_handle == handle
        assert allow_connection.wait(timeout=5.0), "fixture did not release connection"
        return True, 0

    def peek(requested_handle: int) -> int:
        assert requested_handle == handle
        return len(unread)

    def read(requested_handle: int, length: int) -> bytes:
        assert requested_handle == handle
        assert length <= len(unread)
        result = bytes(unread[:length])
        del unread[:length]
        return result

    endpoint = NativeNamedPipeServer(pipe_name)
    with (
        mock.patch.object(native_driver, "_create_named_pipe", return_value=handle) as create,
        mock.patch.object(native_driver, "_connect_named_pipe", side_effect=connect) as connected,
        mock.patch.object(native_driver, "_peek_available", side_effect=peek) as peeks,
        mock.patch.object(native_driver, "_read_exact", side_effect=read) as reads,
        mock.patch.object(native_driver, "_write_all") as writes,
        mock.patch.object(native_driver, "_disconnect_pipe") as disconnect,
        mock.patch.object(native_driver, "_close_handle") as close_handle,
        mock.patch.object(native_driver, "_cancel_io") as cancel,
        mock.patch.object(endpoint, "close", wraps=endpoint.close) as endpoint_close,
    ):
        driver = NativeHeadlessGameplayDriver(
            pipe_name,
            endpoint=endpoint,
            state_dir=tmp_path,
            succession_lifecycle_binding=_ordinary_binding(),
        )
        thread = endpoint._thread
        assert thread is not None
        assert endpoint._on_frame is not None
        assert endpoint._on_frame.__self__ is driver
        assert endpoint._on_frame.__func__ is NativeHeadlessGameplayDriver._ingest
        original_disconnect = endpoint._on_disconnect
        assert original_disconnect is not None
        disconnect_callback = mock.Mock(wraps=original_disconnect)

        def observed_disconnect() -> None:
            try:
                disconnect_callback()
            finally:
                worker_done.set()

        endpoint._on_disconnect = observed_disconnect
        try:
            allow_connection.set()
            assert worker_done.wait(timeout=5.0), "real worker did not disconnect"
            thread.join(timeout=2.0)
            assert not thread.is_alive()
            assert escaped == []

            refusal = endpoint.transport_diagnostic()
            assert refusal == {
                "schema": "native-bridge-adoption-refusal-v1",
                "exception_type": "_NativeBridgeAdoptionRefusedError",
                "stage": "hello_adoption",
                "reason": reason,
                "message": endpoint.transport_error(),
                "attempted_bridge_pid": 5252,
            }
            assert isinstance(refusal["message"], str) and refusal["message"]
            assert driver.diagnostics()["transport_refusal"] == refusal
            assert driver.diagnostics()["transport_fatal_error"] == refusal["message"]
            assert driver.state.diagnostics()["connected"] is False
            assert endpoint._stop.is_set()
            assert endpoint._current_handle() is None
            assert bytes(unread) == second_packet
            assert reads.call_args_list == [
                mock.call(handle, 4), mock.call(handle, len(first_packet) - 4)
            ]
            assert peeks.call_count == 2
            create.assert_called_once_with(pipe_name)
            connected.assert_called_once_with(handle)
            writes.assert_not_called()
            disconnect_callback.assert_called_once_with()
            disconnect.assert_called_once_with(handle)
            close_handle.assert_called_once_with(handle)
            endpoint_close.assert_not_called()
            assert state_path.read_bytes() == before

            # A caller cannot overwrite the first fatal receipt through its copy.
            refusal["message"] = "caller mutation"
            assert endpoint.transport_diagnostic()["message"] != "caller mutation"
        finally:
            allow_connection.set()
            driver.close()
        endpoint_close.assert_called_once_with()
        assert endpoint._thread is None
        assert endpoint._current_handle() is None
        cancel.assert_not_called()
        disconnect.assert_called_once_with(handle)
        close_handle.assert_called_once_with(handle)
        assert state_path.read_bytes() == before
        assert escaped == []
