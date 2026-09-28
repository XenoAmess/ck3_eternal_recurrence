"""Focused private Sway submit, pending recovery and next-turn tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.active_scheme_sway_formal_private_transport import (
    query_active_scheme_sway_receipt_private_v1,
    submit_active_scheme_sway_private_v1,
)
from xar_autoplayer.sway_formal_consumer import (
    LEDGER_FILE, consume_sway_following_turn, consume_sway_private_once,
    read_sway_ledger, should_submit_sway,
)


SNAPSHOT = {
    "paused": True, "map_ready": True, "revision": 4,
    "native_revision": 3, "date_raw": 53219928,
    "played_character": {"character_id": 29829, "alive": True},
    "active_context": {"active_event": None,
                       "pending_character_interaction": None},
}
READ = {
    "schema": "active-scheme-sway-private-read-v1",
    "snapshot_revision": 3, "capture_epoch": 4493,
    "container_generation": 13183742510539082018,
    "date_raw": 53219928, "actor_character_id": 29829,
    "target_character_id": 32716, "target_opinion_of_actor": -5,
    "active_scheme_count": 0, "matching_sway_active": False,
    "native_complete_can_send": True, "native_legal_now": True,
    "native_failure_classification": "", "queried_revision": 4,
    "queried_native_revision": 3,
}


class Driver:
    allow_private_active_scheme_sway_action = True

    def __init__(self, state_dir: Path, *, fail_submit: bool = False):
        self.state_dir = state_dir
        self.fail_submit = fail_submit
        self.submits = 0
        self.receipts = 0
        self.reads = 0

    def take_snapshot(self):
        return dict(SNAPSHOT)

    def submit_active_scheme_sway_private_v1(self, *, readback, action_id):
        self.submits += 1
        if self.fail_submit:
            raise BridgeUnavailableError("native submit result unavailable")
        assert readback["capture_epoch"] == 4493
        return {"stage": "submitted_verification_pending",
                "action_id": action_id, "pre_capture_epoch": 4494}

    def query_active_scheme_sway_receipt_private_v1(self, **kwargs):
        self.receipts += 1
        assert kwargs["target_character_id"] == 32716
        return {"stage": "applied", "postcondition_verified": True,
                "post_capture_epoch": 4495, "scheme_instance_id": 123}

    def query_active_scheme_sway_target_private_v1(self, **kwargs):
        self.reads += 1
        assert kwargs == {"expected_revision": 4, "target_character_id": 32716}
        return {**READ, "capture_epoch": 4496,
                "active_scheme_count": 1, "matching_sway_active": True,
                "native_complete_can_send": False,
                "native_legal_now": False}


def test_formal_sway_applied_with_independent_read_and_later_turn(tmp_path: Path):
    driver = Driver(tmp_path)
    assert should_submit_sway(SNAPSHOT, READ, 32716)
    result = consume_sway_private_once(
        driver, target_character_id=32716, snapshot=SNAPSHOT,
        readback=READ)
    assert result["status"] == "applied"
    assert result["postcondition_verified"] is True
    assert driver.submits == driver.receipts == driver.reads == 1
    assert read_sway_ledger(tmp_path)["pending"] is None
    assert consume_sway_following_turn(tmp_path, SNAPSHOT) is None
    following = {**SNAPSHOT, "native_revision": 4, "date_raw": 53219929}
    consumed = consume_sway_following_turn(tmp_path, following)
    assert consumed is not None and consumed["next_turn_consumed"] is True
    assert consume_sway_following_turn(tmp_path, following) is None
    duplicate = consume_sway_private_once(
        driver, target_character_id=32716, snapshot=SNAPSHOT,
        readback=READ)
    assert duplicate["status"] == "already_applied"
    assert driver.submits == 1


def test_lost_submit_result_stays_pending_and_cold_read_recovers(tmp_path: Path):
    first = Driver(tmp_path, fail_submit=True)
    unresolved = consume_sway_private_once(
        first, target_character_id=32716, snapshot=SNAPSHOT,
        readback=READ)
    assert unresolved["status"] == "submission_unresolved"
    pending = read_sway_ledger(tmp_path)["pending"]
    assert pending["stage"] == "submission_unresolved"
    assert first.submits == 1
    restored = Driver(tmp_path)
    unchanged = consume_sway_private_once(
        restored, target_character_id=32716, snapshot=SNAPSHOT,
        readback=READ)
    assert unchanged["status"] == "pending_recovery"
    assert restored.submits == 0
    # A new PID can restart its capture epoch.  The independent native active
    # scheme result is enough to resolve the durable pending action.
    cold_read = {**READ, "capture_epoch": 7, "active_scheme_count": 1,
                 "matching_sway_active": True, "native_complete_can_send": False,
                 "native_legal_now": False}
    resolved = consume_sway_private_once(
        restored, target_character_id=32716, snapshot=SNAPSHOT,
        readback=cold_read)
    assert resolved["status"] == "applied"
    assert resolved["native_receipt"] is None
    assert restored.submits == 0
    assert read_sway_ledger(tmp_path)["pending"] is None


def test_only_negative_opinion_empty_slot_is_valuable(tmp_path: Path):
    driver = Driver(tmp_path)
    for changed in (
        {"target_opinion_of_actor": 0},
        {"active_scheme_count": 1, "matching_sway_active": True},
        {"native_legal_now": False, "native_complete_can_send": False},
    ):
        read = {**READ, **changed}
        assert not should_submit_sway(SNAPSHOT, read, 32716)
    assert driver.submits == 0
    assert not (tmp_path / LEDGER_FILE).exists()
    malformed = tmp_path / LEDGER_FILE
    malformed.write_text(json.dumps({"schema": "wrong", "pending": None,
                                     "resolved": None}), encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        read_sway_ledger(tmp_path)


def test_native_transport_accepts_new_epoch_and_zero_generation():
    class Endpoint:
        request = None

        def send(self, request):
            self.request = request

    class State:
        def __init__(self, endpoint):
            self.endpoint = endpoint

        def wait_for_command_result(self, request_id, timeout):
            request = self.endpoint.request
            assert timeout == 30.0 and request_id == request["request_id"]
            submit = request["step"].startswith("submit-")
            stage = "submitted_verification_pending" if submit else "applied"
            payload = ({
                "schema": "active-scheme-sway-formal-private-v1",
                "stage": stage, "action_id": request["action_id"],
                "actor_character_id": 29829, "target_character_id": 32716,
                "pre_capture_epoch": 4494,
                "pre_container_generation": READ["container_generation"],
                "pre_date_raw": 53219928, "submit_call_count": 1,
                "receipt_pending": True,
            } if submit else {
                "schema": "active-scheme-sway-formal-private-v1",
                "stage": stage, "action_id": request["action_id"],
                "post_capture_epoch": 4495,
                "post_container_generation": READ["container_generation"],
                "post_date_raw": 53219928, "scheme_instance_id": 123,
                "scheme_instance_generation": 0,
                "postcondition_verified": True,
            })
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True, "result": {
                        "step": request["step"], "accepted": True,
                        "status": stage, "private_build": True,
                        "advertised": False, "active_scheme_sway_formal": payload,
                        "backend_id": "native-headless",
                    }}

    class TransportDriver:
        allow_private_active_scheme_sway_action = True

        def __init__(self):
            self.endpoint = Endpoint()
            self.state = State(self.endpoint)

        def take_snapshot(self):
            return dict(SNAPSHOT)

    driver = TransportDriver()
    ack = submit_active_scheme_sway_private_v1(
        driver, readback=READ, action_id="sway-test-123")
    assert ack["pre_capture_epoch"] > READ["capture_epoch"]
    assert driver.endpoint.request["expected_target_opinion_of_actor"] == "-5"
    receipt = query_active_scheme_sway_receipt_private_v1(
        driver, target_character_id=32716, action_id="sway-test-123",
        expected_revision=3, pre_capture_epoch=READ["capture_epoch"])
    assert receipt["scheme_instance_generation"] == 0
