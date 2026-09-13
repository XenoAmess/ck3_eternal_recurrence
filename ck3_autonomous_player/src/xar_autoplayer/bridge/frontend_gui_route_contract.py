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
FRONTEND_GUI_ROUTES_V1: Final = frozenset(
    {
        "unavailable",
        "main_menu",
        "bookmarks",
        "ruler_designer",
        "coat_of_arms_designer",
    }
)


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
