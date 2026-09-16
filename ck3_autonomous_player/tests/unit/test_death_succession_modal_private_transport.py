from __future__ import annotations

import copy
from pathlib import Path

import pytest

from xar_autoplayer.bridge.death_succession_modal_private_transport import (
    CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP,
    continue_death_succession_modal_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.timeline_blocker_context_contract import (
    QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
)


PUBLIC_REVISION = 9
NATIVE_REVISION = 77
DATE_RAW = 53_411_568
CHARACTER_ID = 35_465
EPISODE_RUN_ID = "native-35465-cbdf997e3d80"


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "snapshot-9",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": CHARACTER_ID, "alive": True},
        "episode_character_id": CHARACTER_ID,
        "episode_run_id": EPISODE_RUN_ID,
        "active_event": None,
        "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


def _timeline(identity: str) -> dict[str, object]:
    false_after = identity == "none"
    return {
        "schema": "current-timeline-blocker-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "identity": identity,
        "blocks_simulation": {
            "status": "available",
            "value": not false_after,
            "unavailable_reason": None,
        },
        "has_open_succession": {
            "status": "available",
            "value": not false_after,
            "unavailable_reason": None,
        },
        "can_continue": (
            {
                "status": "unavailable",
                "value": None,
                "unavailable_reason": "no_supported_timeline_surface_visible",
            }
            if false_after
            else {"status": "available", "value": True, "unavailable_reason": None}
        ),
        "evidence_source": {
            "kind": "exact-build-stock-gui-plus-native-widget-state",
            "path": "game/gui/window_succession_event.gui",
            "root_name": "none" if false_after else "succession_event_window",
            "decisive_widget_name": "none" if false_after else "close_button",
        },
        "unavailable_reason": None,
    }


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None
        self.requests: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        self.request = copy.deepcopy(request)
        self.requests.append(copy.deepcopy(request))


class _State:
    def __init__(self, endpoint: _Endpoint) -> None:
        self.endpoint = endpoint
        self.query_count = 0

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        assert timeout_seconds == 30.0
        request = self.endpoint.request
        assert request is not None and request["request_id"] == request_id
        step = request["step"]
        if step == QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP:
            self.query_count += 1
            identity = "death_succession_modal" if self.query_count == 1 else "none"
            result = {
                "step": step,
                "accepted": True,
                "status": "available",
                "query_sequence": self.query_count,
                "observation_revision": 100 if self.query_count == 1 else 102,
                "snapshot_revision": NATIVE_REVISION,
                "current_timeline_blocker_context": _timeline(identity),
                "private_build": True,
                "read_only": True,
                "advertised": False,
                "backend_id": "native-headless",
            }
        else:
            assert step == CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP
            result = {
                "step": step,
                "accepted": True,
                "status": "submitted",
                "snapshot_revision": NATIVE_REVISION,
                "date_raw": DATE_RAW,
                "played_character_id": CHARACTER_ID,
                "action_observation_revision": 101,
                "identity_verified": True,
                "can_continue_verified": True,
                "paused_by_succession_verified": True,
                "has_open_succession_verified": True,
                "controller_vtable_verified": True,
                "controller_open_verified": True,
                "close_invocations": 1,
                "material_result_verified": False,
                "private_build": True,
                "advertised": False,
                "backend_id": "native-headless",
            }
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": result,
        }


class _Driver:
    allow_private_current_timeline_blocker_query = True
    allow_private_death_succession_modal_continue = True

    def __init__(self) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint)
        self.snapshot = _snapshot()

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        assert step == "life-advance" and expected_revision == PUBLIC_REVISION
        self.snapshot["snapshot_id"] = "snapshot-10"
        self.snapshot["revision"] = PUBLIC_REVISION + 1
        self.snapshot["native_revision"] = NATIVE_REVISION + 1
        self.snapshot["date_raw"] = DATE_RAW + 4
        return {"step": step, "accepted": True}


def test_private_typed_close_requires_independent_postcondition_and_date() -> None:
    driver = _Driver()
    result = continue_death_succession_modal_private_v1(
        driver,
        expected_revision=PUBLIC_REVISION,
        expected_played_character_id=CHARACTER_ID,
        expected_episode_run_id=EPISODE_RUN_ID,
    )
    assert result["status"] == "materially_verified"
    assert result["material_result_verified"] is True
    assert result["post_observation_revision"] == 102
    assert result["ending_date_raw"] == DATE_RAW + 4
    assert [row["step"] for row in driver.endpoint.requests] == [
        QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
        CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP,
        QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
    ]


def test_postcondition_must_be_later_than_action() -> None:
    driver = _Driver()
    original = driver.state.wait_for_command_result

    def stale(request_id: str, timeout_seconds: float) -> dict[str, object]:
        frame = original(request_id, timeout_seconds)
        result = frame["result"]
        if (
            result.get("step") == QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP
            and driver.state.query_count == 2
        ):
            result["observation_revision"] = 101
        return frame

    driver.state.wait_for_command_result = stale  # type: ignore[method-assign]
    with pytest.raises(BridgeUnavailableError, match="independent post-Close"):
        continue_death_succession_modal_private_v1(
            driver,
            expected_revision=PUBLIC_REVISION,
            expected_played_character_id=CHARACTER_ID,
            expected_episode_run_id=EPISODE_RUN_ID,
        )


def test_route_remains_private() -> None:
    server = (
        Path(__file__).parents[2]
        / "src/xar_autoplayer/bridge/mcp_server.py"
    ).read_text(encoding="utf-8")
    assert "def ck3_continue_death_succession_modal_v1(" not in server
    adapter = (
        Path(__file__).parents[2]
        / "native_bridge/src/ck3_11906_adapter.cpp"
    ).read_text(encoding="utf-8")
    assert "game.command.continue-death-succession-modal-v1" not in adapter
    assert "game.command.query-current-timeline-blocker-context-v1" not in adapter
    bridge = (
        Path(__file__).parents[2] / "native_bridge/src/bridge.cpp"
    ).read_text(encoding="utf-8")
    assert (
        "IsDeathSuccessionModalPrivateStepV1(step)" in bridge
        and "ParseCurrentTimelineBlockerContextV1Step(step)" in bridge
        and "ParseDeathSuccessionModalContinueV1Step(step)" in bridge
    )
    assert bridge.count(
        "XAR_CK3_ENABLE_G2_DEATH_SUCCESSION_MODAL_PRIVATE_V1"
    ) == 3
