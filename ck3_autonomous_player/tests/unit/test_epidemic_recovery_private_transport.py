from __future__ import annotations

import copy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.epidemic_recovery_private_transport import (
    STEP, TITLE_STEP_PREFIX, query_player_epidemic_recovery_private_v1,
)


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:237", "revision": 238, "native_revision": 237,
        "date_raw": 53376672, "paused": True, "map_ready": True,
        "played_character": {"character_id": 36403, "alive": True},
        "active_event": {"instance_id": 24},
        "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


def _result(title_id: int = 0, *, available: bool = True) -> dict[str, object]:
    step = STEP if title_id == 0 else TITLE_STEP_PREFIX + str(title_id)
    counties = [
        {"landed_title_id": title_id or 524, "minor_present": False,
         "tiny_present": True},
    ] if available else None
    return {
        "step": step, "accepted": True,
        "status": "available" if available else "unavailable",
        "query_sequence": 1, "observation_revision": 10,
        "snapshot_revision": 237,
        "player_epidemic_recovery": {
            "schema": "player-epidemic-recovery-v1", "schema_version": 1,
            "snapshot_revision": 237, "date_raw": 53376672,
            "played_character_id": 36403,
            "list_key": "formerly_infected_counties",
            "requested_title_id": title_id,
            "status": "available" if available else "unavailable",
            "counties": counties,
            "remaining_days": {"status": "unavailable", "value": None,
                               "unavailable_reason": "duration_abi_not_verified"},
            "unavailable_reason": None if available else "landed_title_unavailable",
        },
        "private_build": True, "read_only": True, "advertised": False,
        "backend_id": "native-headless",
    }


class _Driver:
    allow_private_epidemic_recovery_query = True

    def __init__(self, value: dict[str, object]) -> None:
        self.value = value
        self.snapshot = _snapshot()
        self.request: dict[str, object] | None = None
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.request = request

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        assert timeout == 30.0 and self.request is not None
        assert self.request["step"] == self.value["step"]
        assert self.request["expected_revision"] == 237
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": self.value}


@pytest.mark.parametrize("title_id", [0, 524])
def test_list_and_explicit_post_title_readback(title_id: int) -> None:
    driver = _Driver(_result(title_id))
    if title_id > 0:
        driver.snapshot["active_event"] = None
    envelope = query_player_epidemic_recovery_private_v1(
        driver, expected_revision=238,
        requested_title_id=title_id,
        expected_event_instance_id=24 if title_id == 0 else None,
    )
    assert envelope["player_epidemic_recovery"]["counties"][0]["landed_title_id"] == 524
    assert envelope["queried_native_revision"] == 237


def test_unavailable_is_distinct_from_empty_list() -> None:
    envelope = query_player_epidemic_recovery_private_v1(
        _Driver(_result(available=False)), expected_revision=238,
        expected_event_instance_id=24,
    )
    assert envelope["player_epidemic_recovery"]["counties"] is None
    empty = _result()
    empty["player_epidemic_recovery"]["counties"] = []
    envelope = query_player_epidemic_recovery_private_v1(
        _Driver(empty), expected_revision=238,
        expected_event_instance_id=24,
    )
    assert envelope["player_epidemic_recovery"]["counties"] == []


def test_wrong_title_and_frame_drift_are_rejected() -> None:
    wrong = _result(524)
    wrong["player_epidemic_recovery"]["counties"][0]["landed_title_id"] = 525
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_recovery_private_v1(
            _Driver(wrong), expected_revision=238, requested_title_id=524,
        )

    class _ShiftedDriver(_Driver):
        def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
            frame = super().wait_for_command_result(request_id, timeout)
            self.snapshot["date_raw"] = 53376696
            return frame

    with pytest.raises(BridgeUnavailableError, match="crossed its paused frame"):
        query_player_epidemic_recovery_private_v1(
            _ShiftedDriver(_result()), expected_revision=238,
            expected_event_instance_id=24,
        )


def test_private_opt_in_and_revision_binding() -> None:
    driver = _Driver(_result())
    driver.allow_private_epidemic_recovery_query = False
    with pytest.raises(UnsupportedStepError):
        query_player_epidemic_recovery_private_v1(
            driver, expected_revision=238, expected_event_instance_id=24,
        )
    driver.allow_private_epidemic_recovery_query = True
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_recovery_private_v1(
            driver, expected_revision=239, expected_event_instance_id=24,
        )
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_recovery_private_v1(
            driver, expected_revision=238, expected_event_instance_id=25,
        )
