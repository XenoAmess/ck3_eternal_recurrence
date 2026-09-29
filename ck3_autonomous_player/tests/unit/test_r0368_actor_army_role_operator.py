"""No-launch and same-frame guard tests for the dormant R0368 operator."""

from __future__ import annotations

import copy

import pytest

from xar_autoplayer.errors import AgentError
from xar_autoplayer import r0368_actor_army_role_operator as operator


def _check(condition: bool) -> None:
    if not condition:
        raise AssertionError("R0368 operator boundary failed")


def _frame() -> dict[str, object]:
    return {
        "snapshot_id": "native:1", "revision": 4, "native_revision": 3,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "episode_character_id": 29829,
        "diagnostics": {"connected": True, "connection_generation": 1,
                        "bridge_pid": 901, "hello": {"capabilities": []}},
        "active_event": None, "pending_character_interaction": None,
        "hello_capabilities": [], "date_raw": 53219928,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [{"army_id": 83886367,
                            "owner_character_id": 29829,
                            "current_province_id": 2610}],
        "active_wars": [{"war_id": 16777231,
                         "allied_armies": [{"army_id": 83886367,
                                             "owner_character_id": 29829}]}],
    }


class _Driver:
    allow_private_actor_army_role_query = True

    def __init__(self) -> None:
        self.frames = [_frame(), _frame()]
        self.query_calls = 0
        self.snapshot_calls = 0

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        return copy.deepcopy(self.frames.pop(0))

    def query_actor_army_role_private_v1(self, **kwargs: object) -> dict[str, object]:
        self.query_calls += 1
        _check(kwargs == {
            "actor_character_id": 29829,
            "public_army_id": 83886367,
            "expected_war_id": 16777231,
            "expected_episode_run_id": "native-29829-2bc2d599f7f9",
            "expected_revision": 4,
        })
        return {
            "status": "available", "private_build": True,
            "read_only": True, "advertised": False,
            "queried_snapshot_id": "native:1", "queried_revision": 4,
            "queried_native_revision": 3,
            "queried_episode_run_id": "native-29829-2bc2d599f7f9",
            "queried_war_id": 16777231,
            "queried_connection_generation": 1, "queried_bridge_pid": 901,
            "date_raw": 53219928, "global_role_ready": False,
            "safe_role_release_ready": False, "date_advance_ready": False,
            "actor_army_role": {"is_commander_of_requested_army": True},
        }


def _collect(driver: _Driver) -> dict[str, object]:
    return operator.collect_role_only_in_managed_session(
        driver, actor_character_id=29829,
        episode_run_id="native-29829-2bc2d599f7f9",
        war_id=16777231, public_army_id=83886367,
    )


def test_default_off_does_not_touch_driver() -> None:
    driver = _Driver()
    with pytest.raises(AgentError, match="live gate is closed"):
        _collect(driver)
    _check(driver.query_calls == driver.snapshot_calls == 0)


@pytest.mark.parametrize("change", [
    lambda frame: frame["active_wars"][0]["allied_armies"].clear(),
    lambda frame: frame["player_armies"][0].update(owner_character_id=42),
    lambda frame: frame["diagnostics"].update(connection_generation=0),
    lambda frame: frame.update(native_revision=None),
])
def test_missing_fresh_binding_refuses_query(monkeypatch: pytest.MonkeyPatch,
                                              change: object) -> None:
    monkeypatch.setattr(operator, "ROLE_ONLY_LIVE_AUTHORIZED", True)
    driver = _Driver()
    change(driver.frames[0])
    with pytest.raises(AgentError, match="fresh paused"):
        _collect(driver)
    _check(driver.query_calls == 0)


def test_same_frame_result_stays_inner_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator, "ROLE_ONLY_LIVE_AUTHORIZED", True)
    driver = _Driver()
    report = _collect(driver)
    _check(driver.query_calls == 1)
    _check(report["status"] == "READ_ONLY_INNER_AVAILABLE")
    _check(report["outer_session_cleanup_verified"] is False)
    _check(report["action_authorized"] is False)
    _check(report["date_advance_authorized"] is False)
    _check(report["gameplay_actions"] == report["date_advance_actions"] == 0)


@pytest.mark.parametrize("field,value", [
    ("date_raw", 53219929),
    ("episode_run_id", "another-episode"),
    ("native_revision", 4),
])
def test_after_frame_drift_rejects_result(monkeypatch: pytest.MonkeyPatch,
                                          field: str, value: object) -> None:
    monkeypatch.setattr(operator, "ROLE_ONLY_LIVE_AUTHORIZED", True)
    driver = _Driver()
    driver.frames[1][field] = value
    with pytest.raises(AgentError, match="crossed or changed"):
        _collect(driver)
    _check(driver.query_calls == 1)
