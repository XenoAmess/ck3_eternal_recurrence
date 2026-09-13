"""Closed MCP contract for semantic CK3 frontend navigation."""

from __future__ import annotations

from typing import Final


QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY: Final = (
    "game.command.query-frontend-gui-route-v1"
)
QUERY_FRONTEND_GUI_ROUTE_V1_STEP: Final = "query-frontend-gui-route-v1"
ACTIVATE_FRONTEND_NEW_GAME_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-new-game-v1"
)
ACTIVATE_FRONTEND_NEW_GAME_V1_STEP: Final = (
    "activate-frontend-new-game-v1"
)
ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-pick-any-character-v1"
)
ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP: Final = (
    "activate-frontend-pick-any-character-v1"
)
FRONTEND_GUI_ROUTES_V1: Final = frozenset(
    {
        "unavailable",
        "main_menu",
        "bookmarks",
        "lobby",
        "ruler_designer",
        "coat_of_arms_designer",
    }
)
FRONTEND_GUI_ROUTE_V1_GAME_VERSION: Final = "1.19.0.6"
FRONTEND_GUI_ROUTE_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
FRONTEND_GUI_ROUTE_V1_GAME_ADAPTER_ID: Final = "ck3-1.19.0.6-msvc-x64"


def frontend_gui_route_binding_from_capabilities(
    value: object,
) -> dict[str, int]:
    """Bind a pre-game GUI command even after CK3 starts snapshot publication."""

    candidates: list[tuple[int, int]] = []

    def visit(row: object) -> None:
        if not isinstance(row, dict):
            return
        capabilities = row.get("bridge_capabilities")
        diagnostics = row.get("diagnostics")
        if (
            row.get("backend_id") == "native-headless"
            and row.get("mode") == "native-headless"
            and row.get("source") == "injected-dll-named-pipe"
            and row.get("visual_fallback") is False
            and isinstance(capabilities, list)
            and QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY in capabilities
            and isinstance(diagnostics, dict)
        ):
            hello = diagnostics.get("hello")
            bridge_pid = diagnostics.get("bridge_pid")
            connection_generation = diagnostics.get("connection_generation")
            if not (
                diagnostics.get("connected") is True
                and isinstance(hello, dict)
                and isinstance(bridge_pid, int)
                and not isinstance(bridge_pid, bool)
                and 1 <= bridge_pid <= 2**32 - 1
                and hello.get("pid") == bridge_pid
                and isinstance(connection_generation, int)
                and not isinstance(connection_generation, bool)
                and 1 <= connection_generation <= 2**64 - 1
                and hello.get("connection_generation")
                == connection_generation
                and hello.get("game_adapter_id")
                == FRONTEND_GUI_ROUTE_V1_GAME_ADAPTER_ID
                and hello.get("game_adapter_status") == "ready"
                and hello.get("expected_ck3_version")
                == FRONTEND_GUI_ROUTE_V1_GAME_VERSION
                and hello.get("expected_ck3_sha256")
                == FRONTEND_GUI_ROUTE_V1_EXECUTABLE_SHA256
                and hello.get("ck3_build_match") is True
                and isinstance(hello.get("capabilities"), list)
                and QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY
                in hello["capabilities"]
            ):
                raise ValueError(
                    "frontend GUI route native bridge identity is malformed"
                )
            candidates.append((bridge_pid, connection_generation))
        backends = row.get("backends")
        if isinstance(backends, list):
            for backend in backends:
                visit(backend)

    visit(value)
    unique = set(candidates)
    if len(unique) != 1:
        raise ValueError("frontend GUI route requires one exact native bridge")
    bridge_pid, connection_generation = unique.pop()
    return {
        "bridge_pid": bridge_pid,
        "connection_generation": connection_generation,
    }


def normalize_frontend_gui_route_v1(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise ValueError("frontend GUI route result must be an object")
    if (
        result.get("step") != QUERY_FRONTEND_GUI_ROUTE_V1_STEP
        or result.get("accepted") is not True
        or result.get("status") not in FRONTEND_GUI_ROUTES_V1
    ):
        raise ValueError("frontend GUI route result is malformed")
    return {
        "schema": "ck3-frontend-gui-route-v1",
        "schema_version": 1,
        "step": QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
        "accepted": True,
        "route": result["status"],
        "backend_id": result.get("backend_id"),
    }


def normalize_frontend_new_game_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend new-game acknowledgement must be an object")
    if (
        acknowledgement.get("step") != ACTIVATE_FRONTEND_NEW_GAME_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "main_menu"
        or after.get("route") != "bookmarks"
    ):
        raise ValueError("frontend new-game postcondition is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "open_new_game",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }


def normalize_frontend_pick_any_character_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend pick-any-character acknowledgement must be an object")
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "bookmarks"
        or after.get("route") != "lobby"
    ):
        raise ValueError("frontend pick-any-character postcondition is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "pick_any_character",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }
