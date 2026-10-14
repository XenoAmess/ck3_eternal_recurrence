"""Synthetic portable tests: no Windows APIs, overlay, Game, OBS or screen calls."""

import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parent / "g2_saved_campaign" / "live_decision_overlay.py"
if not SOURCE.is_file():
    # The offline candidate bundle also runs without an installed project.
    SOURCE = Path(__file__).with_name("live_decision_overlay.py")
spec = importlib.util.spec_from_file_location("overlay_resilience_under_test", SOURCE)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


def _receipt(directory, suffix):
    paths = list(directory.glob(f"ROOT-DECISION-OVERLAY-*-{suffix}.json"))
    assert len(paths) == 1
    return paths[0], json.loads(paths[0].read_text(encoding="utf-8"))


class FakeWindow:
    def __init__(self):
        self.visible = True
        self.destroyed = False
        self.closed = False
        self.updates = []

    def set_content_visible(self, visible):
        self.visible = visible

    def update(self, *text):
        self.updates.append(text)

    def destroy(self):
        self.destroyed = True

    def close(self):
        self.closed = True


def test_transient_share_lock_retries_atomically_and_retains_first_exception(tmp_path, monkeypatch):
    target = tmp_path / "decision.txt"
    target.write_bytes(b"old verified text")
    evidence = overlay.OverlayEvidence(tmp_path, 99)
    replace = overlay.os.replace
    attempts, sleeps = [], []

    def locked_twice(source, destination):
        attempts.append((source, destination))
        assert target.read_bytes() == b"old verified text"
        if len(attempts) <= 2:
            raise PermissionError(13, "Synthetic Windows destination sharing lock")
        replace(source, destination)

    monkeypatch.setattr(overlay.os, "replace", locked_twice)
    monkeypatch.setattr(overlay.time, "sleep", sleeps.append)

    assert overlay.publish_decision_payload(target, "新的真实回执".encode(), evidence) is True
    assert len(attempts) == 3
    assert sleeps == [.02, .05]
    assert target.read_text(encoding="utf-8") == "新的真实回执"
    assert not list(tmp_path.glob("*.pending"))
    first_path, first = _receipt(tmp_path, "FIRST-EXCEPTION")
    original = first_path.read_bytes()
    assert first["first_exception"]["type"] == "PermissionError"
    assert first["first_exception"]["stage"] == "decision_text_atomic_replace"
    assert "locked_twice" in first["first_exception"]["traceback"]
    evidence.note_exception(ValueError("Synthetic later error"), "tick")
    assert first_path.read_bytes() == original


def test_persistent_lock_defers_without_losing_old_text_and_later_publish_succeeds(tmp_path, monkeypatch):
    target = tmp_path / "decision.txt"
    target.write_bytes(b"last known receipt")
    evidence = overlay.OverlayEvidence(tmp_path, 99)
    replace = overlay.os.replace
    attempts, sleeps = [], []

    def always_locked(*args):
        attempts.append(args)
        raise PermissionError(13, "Synthetic long sharing lock")

    monkeypatch.setattr(overlay.os, "replace", always_locked)
    monkeypatch.setattr(overlay.time, "sleep", sleeps.append)

    assert overlay.publish_decision_payload(target, b"new actual receipt", evidence) is False
    assert len(attempts) == 4
    assert sleeps == [.02, .05, .1]
    assert target.read_bytes() == b"last known receipt"
    assert not list(tmp_path.glob("*.pending"))
    assert evidence.exit_reason is None

    monkeypatch.setattr(overlay.os, "replace", replace)
    assert overlay.publish_decision_payload(target, b"new actual receipt", evidence) is True
    assert target.read_bytes() == b"new actual receipt"


def test_secondary_error_publish_failure_keeps_window_alive_and_preserves_primary(tmp_path):
    window = FakeWindow()
    evidence = overlay.OverlayEvidence(tmp_path, 99)
    primary = json.JSONDecodeError("Synthetic incomplete response", "{", 1)
    publishes = []

    def fail_publish(content):
        publishes.append(content)
        raise PermissionError(13, "Synthetic warning publish sharing lock")

    overlay.show_read_error(window, fail_publish, evidence, primary)

    assert len(publishes) == 1
    assert window.updates and window.visible is False
    assert window.destroyed is False and window.closed is False
    assert evidence.exit_reason is None
    assert evidence.exception_count == 2
    _, first = _receipt(tmp_path, "FIRST-EXCEPTION")
    assert first["first_exception"]["type"] == "JSONDecodeError"
    assert first["first_exception"]["stage"] == "tick"
    assert first["first_exception"]["message"] == str(primary)


def test_locked_warning_text_defers_without_destroying_window_and_recovers(tmp_path, monkeypatch):
    target = tmp_path / "decision.txt"
    target.write_bytes(b"last known actual receipt")
    evidence = overlay.OverlayEvidence(tmp_path, 99)
    window = FakeWindow()
    replace = overlay.os.replace

    def locked(*args):
        raise PermissionError(13, "Synthetic Windows warning text sharing lock")

    monkeypatch.setattr(overlay.os, "replace", locked)
    monkeypatch.setattr(overlay.time, "sleep", lambda delay: None)
    publish = lambda content: overlay.publish_decision_payload(target, content.encode("utf-8"), evidence)
    overlay.show_read_error(window, publish, evidence, ValueError("Synthetic incomplete live response"))

    assert window.destroyed is False and window.closed is False
    assert window.updates and evidence.exit_reason is None
    assert target.read_bytes() == b"last known actual receipt"
    assert not list(tmp_path.glob("*.pending"))
    _, first = _receipt(tmp_path, "FIRST-EXCEPTION")
    assert first["first_exception"]["stage"] == "tick"
    assert first["first_exception"]["type"] == "ValueError"

    monkeypatch.setattr(overlay.os, "replace", replace)
    assert publish("Synthetic next real receipt") is True
    assert target.read_text(encoding="utf-8") == "Synthetic next real receipt"
    assert window.destroyed is False and window.closed is False


@pytest.mark.parametrize("code", ["owner_stop_requested", "game_process_exited"])
def test_explicit_close_keeps_reason_and_closed_receipt_even_when_text_publish_fails(tmp_path, code):
    window = FakeWindow()
    evidence = overlay.OverlayEvidence(tmp_path, 99)
    released = []

    def fail_publish(content):
        raise OSError("Synthetic publisher unavailable during close")

    overlay.close_panel(window, fail_publish, evidence, code, "Synthetic explicit stop")
    assert window.destroyed is True
    overlay.finish_overlay(window, fail_publish, lambda: released.append(True), evidence)

    assert window.closed is True and released == [True]
    _, closed = _receipt(tmp_path, "CLOSED")
    assert closed["exit_reason"]["code"] == code
    assert closed["first_exception"]["stage"] == "stop_publish"
    assert closed["exception_count"] == 2


def test_unattributed_message_loop_return_does_not_invent_a_share_lock_cause(tmp_path):
    window = FakeWindow()
    evidence = overlay.OverlayEvidence(tmp_path, 99)

    overlay.finish_overlay(window, lambda text: True, lambda: None, evidence)

    _, closed = _receipt(tmp_path, "CLOSED")
    assert closed["exit_reason"]["code"] == "native_message_loop_returned_without_requested_stop"
    assert closed["first_exception"] is None
    assert closed["exception_count"] == 0
    assert not list(tmp_path.glob("*FIRST-EXCEPTION.json"))
