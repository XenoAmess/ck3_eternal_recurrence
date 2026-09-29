"""Boundary tests for the disabled-by-default actor army role transport."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from xar_autoplayer.bridge.actor_army_role_private_transport import (
    query_actor_army_role_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:1", "revision": 4, "native_revision": 3,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [{"army_id": 83886367,
                            "owner_character_id": 29829,
                            "current_province_id": 2610}],
        "active_wars": [{"war_id": 16777231}],
    }


def _payload(status: str = "available") -> dict[str, object]:
    return {
        "schema": "xar.war.actor-army-role-private.v1",
        "private_build": True, "read_only": True, "status": status,
        "unavailable_stage": None if status == "available" else "regiment_array_shape",
        "native_revision": 3, "date_raw": 53219928,
        "actor_character_id": 29829, "public_army_id": 83886367,
        "native_carmy_id": 50331794, "owner_character_id": 29829,
        "current_province_id": 2610, "army_state": "stationary",
        "in_combat": False, "retreating": False,
        "commander_status": "available", "commander_character_id": 29829,
        "is_commander_of_requested_army": True,
        "knight_status": "absent" if status == "available" else "unknown",
        "knight_regiment_id": None,
        "is_knight_in_requested_army": False if status == "available" else None,
        "global_commander_or_knight_status": "unknown",
        "safe_role_release": None, "date_credit": False,
    }


class _Endpoint:
    request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, endpoint: _Endpoint, payload: dict[str, object]) -> None:
        self.endpoint = endpoint
        self.payload = payload

    def wait_for_command_result(self, request_id: str, _timeout: float) -> dict[str, object]:
        request = self.endpoint.request
        assert request is not None
        assert request["request_id"] == request_id
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": request["step"], "accepted": True,
                "status": self.payload["status"], "private_build": True,
                "read_only": True, "actor_army_role": self.payload,
                "backend_id": "native-headless",
            },
        }


class _Driver:
    def __init__(self, payload: dict[str, object], *, enabled: bool = True) -> None:
        self.allow_private_actor_army_role_query = enabled
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint, payload)
        self.snapshots = [_snapshot(), _snapshot()]

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshots.pop(0))


def _query(driver: Any) -> dict[str, object]:
    return query_actor_army_role_private_v1(
        driver, actor_character_id=29829, public_army_id=83886367,
        expected_revision=4,
    )


def test_default_off_never_submits() -> None:
    driver = _Driver(_payload(), enabled=False)
    with pytest.raises(UnsupportedStepError):
        _query(driver)
    assert driver.endpoint.request is None


def test_complete_own_army_role_is_still_not_global_release_credit() -> None:
    driver = _Driver(_payload())
    result = _query(driver)
    assert driver.endpoint.request["step"] == (
        "query-war-actor-army-role-v1-29829-83886367"
    )
    assert result["actor_army_role"]["is_commander_of_requested_army"] is True
    assert result["actor_army_role"]["is_knight_in_requested_army"] is False
    assert result["global_role_ready"] is False
    assert result["safe_role_release_ready"] is False
    assert result["date_advance_ready"] is False


def test_partial_knight_stays_unknown() -> None:
    result = _query(_Driver(_payload("partial")))
    assert result["status"] == "partial"
    assert result["actor_army_role"]["is_knight_in_requested_army"] is None


def test_wrong_actor_is_rejected_before_send() -> None:
    driver = _Driver(_payload())
    driver.snapshots[0]["played_character"] = {
        "character_id": 999, "alive": True,
    }
    with pytest.raises(BridgeUnavailableError):
        _query(driver)
    assert driver.endpoint.request is None


def test_postquery_army_drift_invalidates_result() -> None:
    driver = _Driver(_payload())
    driver.snapshots[1]["player_armies"][0]["current_province_id"] = 2611
    with pytest.raises(BridgeUnavailableError):
        _query(driver)


def test_payload_cannot_claim_global_role_or_release() -> None:
    payload = _payload()
    payload["safe_role_release"] = True
    with pytest.raises(BridgeUnavailableError):
        _query(_Driver(payload))
