"""Synthetic refusals exercise real failure history persistence, without CK3."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _NativeCommandRejectedError,
)


class NoTransport:
    """Initialization boundary only; any attempted native send fails this test."""

    def start(self, on_frame, on_disconnect):
        pass

    def send(self, frame):
        raise AssertionError("native transport must not run in history tests")

    def close(self):
        pass


@pytest.mark.parametrize("kind", ["assignment", "unrelated", "no_frame"])
def test_rejection_history_preserves_failure_and_never_retries(tmp_path, monkeypatch, kind):
    step = "assign-army-commander-v1-army-18-to-character-34232"
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": "synthetic-once", "expected_revision": 3,
        "step": step if kind != "unrelated" else "query-unrelated",
    }
    response = {
        "type": "command_result", "protocol_version": 1,
        "request_id": "synthetic-once", "ok": False, "error": "state_changed",
        "army_commander_predispatch_failure_v1": {
            "first_failed": "observed_read", "dispatch_submitted": False,
        },
        "unknown_native_field": {"must_survive": [7, None, "original"]},
    }
    error = _NativeCommandRejectedError(
        "state_changed", native_request_id="synthetic-once",
        native_request_frame=None if kind == "no_frame" else request,
        native_command_result_frame=response,
    )
    driver = NativeHeadlessGameplayDriver(endpoint=NoTransport(), state_dir=tmp_path)
    # Synthetic identity enables the production disk writer; it is no live PID.
    driver._session_bridge_pid = 12345
    driver._episode_character_id = 31254
    driver._episode_run_id = "synthetic-commander-history"
    driver._native_driver_state_path().parent.mkdir(parents=True, exist_ok=True)
    attempts = []

    def refuse(actual_step, *, expected_revision):
        attempts.append((actual_step, expected_revision))
        raise error

    monkeypatch.setattr(driver, "_execute_step_unrecorded", refuse)
    with pytest.raises(_NativeCommandRejectedError) as caught:
        driver.execute_step(step, expected_revision=4)

    assert caught.value is error
    assert attempts == [(step, 4)]
    assert len(driver._command_history) == 1
    row = driver._command_history[0]
    assert row["command"] == step and row["ok"] is False
    assert "state_changed" in row["error"]
    persisted = json.loads(driver._native_driver_state_path().read_bytes())
    assert persisted["command_history"] == driver._command_history
    if kind == "assignment":
        saved = row["result"]
        assert saved["native_request_id"] == "synthetic-once"
        assert saved["native_request_frame"] == request
        assert saved["native_command_result_frame"] == response
        assert saved["never_replay"] is True
        assert saved["dispatch_status"].startswith("unknown")
    else:
        assert "result" not in row
