from __future__ import annotations

import copy
from pathlib import Path

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_current_timeline_blocker_context_v1,
)
from xar_autoplayer.bridge.native_driver import _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.timeline_blocker_context_contract import (
    QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
    normalize_current_timeline_blocker_context_v1,
)
from xar_autoplayer.bridge.timeline_blocker_private_transport import (
    query_current_timeline_blocker_context_private_v1,
)


PUBLIC_REVISION = 9
NATIVE_REVISION = 77
DATE_RAW = 53_411_568


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "snapshot-9",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 35_465, "alive": True},
        "active_event": None,
        "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


def _frame(identity: str = "death_succession_modal") -> dict[str, object]:
    if identity == "none":
        can_continue = {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "no_supported_timeline_surface_visible",
        }
        root = "none"
        decisive = "none"
    else:
        can_continue = {
            "status": "available",
            "value": identity != "game_over_modal",
            "unavailable_reason": None,
        }
        root = (
            "succession_select_destiny_window"
            if identity == "succession_select_destiny_modal"
            else "succession_event_window"
        )
        decisive = (
            "menu_button"
            if identity == "game_over_modal"
            else "close_button"
        )
    return {
        "schema": "current-timeline-blocker-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "identity": identity,
        "blocks_simulation": {
            "status": "available",
            "value": identity != "none",
            "unavailable_reason": None,
        },
        "has_open_succession": {
            "status": "available",
            "value": identity != "none",
            "unavailable_reason": None,
        },
        "can_continue": can_continue,
        "evidence_source": {
            "kind": "exact-build-stock-gui-plus-native-widget-state",
            "path": "game/gui/window_succession_event.gui",
            "root_name": root,
            "decisive_widget_name": decisive,
        },
        "unavailable_reason": None,
    }


def _native_result() -> dict[str, object]:
    frame = _frame()
    return {
        "step": QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": 3,
        "observation_revision": 120,
        "snapshot_revision": NATIVE_REVISION,
        "current_timeline_blocker_context": frame,
        "private_build": True,
        "read_only": True,
        "advertised": False,
        "backend_id": "native-headless",
    }


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = copy.deepcopy(request)


class _State:
    def __init__(self, endpoint: _Endpoint) -> None:
        self.endpoint = endpoint

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        assert timeout_seconds == 30.0
        assert self.endpoint.request is not None
        assert self.endpoint.request["request_id"] == request_id
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": _native_result(),
        }


class _TransportDriver:
    allow_private_current_timeline_blocker_query = True

    def __init__(self) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint)
        self.snapshot = _snapshot()

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)


class _ServiceDriver:
    def __init__(self) -> None:
        self.snapshot = _snapshot()

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def query_current_timeline_blocker_context_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        assert expected_revision == PUBLIC_REVISION
        return {
            **_native_result(),
            "queried_snapshot_id": "snapshot-9",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
        }


def test_contract_preserves_exact_native_predicates() -> None:
    normalized = normalize_current_timeline_blocker_context_v1(
        _frame(),
        expected_date_raw=DATE_RAW,
        expected_snapshot_revision=NATIVE_REVISION,
    )
    assert normalized["identity"] == "death_succession_modal"
    assert normalized["can_continue"]["value"] is True
    assert normalized["blocks_simulation"]["value"] is True
    assert normalized["has_open_succession"]["value"] is True
    invalid = _frame()
    invalid["blocks_simulation"]["status"] = "unavailable"
    invalid["blocks_simulation"]["value"] = None
    invalid["blocks_simulation"]["unavailable_reason"] = "missing"
    with pytest.raises(ValueError, match="succession predicates must be available"):
        normalize_current_timeline_blocker_context_v1(
            invalid,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )


def test_private_transport_binds_one_paused_native_frame() -> None:
    driver = _TransportDriver()
    result = query_current_timeline_blocker_context_private_v1(
        driver,
        expected_revision=PUBLIC_REVISION,
    )
    assert result["advertised"] is False
    assert result["read_only"] is True
    assert result["queried_native_revision"] == NATIVE_REVISION
    assert driver.endpoint.request == {
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": driver.endpoint.request["request_id"],
        "step": QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
        "expected_revision": NATIVE_REVISION,
    }


def test_private_transport_is_explicit_opt_in() -> None:
    driver = _TransportDriver()
    driver.allow_private_current_timeline_blocker_query = False
    with pytest.raises(UnsupportedStepError, match="disabled"):
        query_current_timeline_blocker_context_private_v1(
            driver,
            expected_revision=PUBLIC_REVISION,
        )


def test_service_and_private_mcp_helper_preserve_binding() -> None:
    service = GameplayBridgeService(_ServiceDriver())
    result = _ck3_query_current_timeline_blocker_context_v1(
        service,
        PUBLIC_REVISION,
    )
    assert result["scope"] == "exact-current-timeline-blocker"
    assert result["binding"] == {
        "snapshot_id": "snapshot-9",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "expected_revision": PUBLIC_REVISION,
    }
    assert result["current_timeline_blocker_context"]["blocks_simulation"]["value"] is True


def test_capability_and_public_mcp_registry_remain_closed() -> None:
    plan = _action_steps([], paused=True)
    assert QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP not in plan
    adapter_source = (
        Path(__file__).parents[2]
        / "native_bridge/src/ck3_11906_adapter.cpp"
    ).read_text(encoding="utf-8")
    assert QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_CAPABILITY not in adapter_source
    server_source = (
        Path(__file__).parents[2]
        / "src/xar_autoplayer/bridge/mcp_server.py"
    ).read_text(encoding="utf-8")
    assert "def ck3_query_current_timeline_blocker_context_v1(" not in server_source
