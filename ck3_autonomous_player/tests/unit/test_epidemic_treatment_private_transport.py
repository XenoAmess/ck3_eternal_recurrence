from __future__ import annotations

import copy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.epidemic_treatment_private_transport import (
    KEY,
    STEP,
    query_player_epidemic_treatment_presence_private_v1,
)


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:171", "revision": 172, "native_revision": 171,
        "date_raw": 53350560, "paused": True, "map_ready": True,
        "played_character": {"character_id": 36403, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


def _result(present: bool | None = True) -> dict[str, object]:
    available = present is not None
    return {
        "step": STEP, "accepted": True,
        "status": "available" if available else "unavailable",
        "query_sequence": 1, "observation_revision": 10,
        "snapshot_revision": 171,
        "player_epidemic_treatment_presence": {
            "schema": "player-epidemic-treatment-presence-v1",
            "schema_version": 1, "modifier_key": KEY,
            "snapshot_revision": 171, "date_raw": 53350560,
            "played_character_id": 36403,
            "status": "available" if available else "unavailable",
            "present": present,
            "remaining_days": {"status": "unavailable", "value": None,
                               "unavailable_reason": "duration_abi_not_verified"},
            "unavailable_reason": None if available else "modifier_rows_unavailable",
        },
        "private_build": True, "read_only": True, "advertised": False,
        "backend_id": "native-headless",
    }


class _Driver:
    allow_private_epidemic_treatment_presence_query = True

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
        if timeout != 30.0 or self.request is None:
            pytest.fail("unexpected private query timeout or missing request")
        if self.request["step"] != STEP or self.request["expected_revision"] != 171:
            pytest.fail("wrong fixed-key native request")
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": self.value}


@pytest.mark.parametrize("present", [True, False, None])
def test_fixed_key_same_frame_readback(present: bool | None) -> None:
    driver = _Driver(_result(present))
    envelope = query_player_epidemic_treatment_presence_private_v1(
        driver, expected_revision=172,
    )
    if envelope["player_epidemic_treatment_presence"]["present"] is not present:
        pytest.fail("presence was not preserved")
    if envelope["queried_native_revision"] != 171:
        pytest.fail("native revision was not preserved")


def test_wrong_key_or_duration_cannot_masquerade_as_result() -> None:
    wrong = _result()
    wrong["player_epidemic_treatment_presence"]["modifier_key"] = "other"
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_treatment_presence_private_v1(
            _Driver(wrong), expected_revision=172,
        )
    wrong = _result()
    wrong["player_epidemic_treatment_presence"]["remaining_days"]["value"] = 100
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_treatment_presence_private_v1(
            _Driver(wrong), expected_revision=172,
        )


def test_private_opt_in_and_same_frame_required() -> None:
    driver = _Driver(_result())
    driver.allow_private_epidemic_treatment_presence_query = False
    with pytest.raises(UnsupportedStepError):
        query_player_epidemic_treatment_presence_private_v1(
            driver, expected_revision=172,
        )
    driver.allow_private_epidemic_treatment_presence_query = True
    with pytest.raises(BridgeUnavailableError):
        query_player_epidemic_treatment_presence_private_v1(
            driver, expected_revision=173,
        )


def test_frame_change_during_readback_is_rejected() -> None:
    class _ShiftedDriver(_Driver):
        def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
            frame = super().wait_for_command_result(request_id, timeout)
            self.snapshot["date_raw"] = 53350561
            return frame

    with pytest.raises(BridgeUnavailableError, match="crossed its paused frame"):
        query_player_epidemic_treatment_presence_private_v1(
            _ShiftedDriver(_result()), expected_revision=172,
        )
