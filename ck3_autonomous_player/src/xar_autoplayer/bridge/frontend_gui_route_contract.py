"""Closed MCP contract for semantic CK3 frontend navigation."""

from __future__ import annotations

import re
from typing import Final


QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY: Final = (
    "game.command.query-frontend-gui-route-v1"
)
QUERY_FRONTEND_GUI_ROUTE_V1_STEP: Final = "query-frontend-gui-route-v1"
INSPECT_FRONTEND_GUI_TREE_V1_CAPABILITY: Final = (
    "game.command.inspect-frontend-gui-tree-v1"
)
INSPECT_FRONTEND_GUI_TREE_V1_STEP: Final = "inspect-frontend-gui-tree-v1"
INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_CAPABILITY: Final = (
    "game.command.inspect-frontend-coat-of-arms-tree-v1"
)
INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP: Final = (
    "inspect-frontend-coat-of-arms-tree-v1"
)
INSPECT_FRONTEND_GUI_TREE_V1_MAXIMUM_WIDGETS: Final = 512
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
ACTIVATE_FRONTEND_SELECT_RANDOM_PLAYABLE_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-select-random-playable-v1"
)
ACTIVATE_FRONTEND_SELECT_RANDOM_PLAYABLE_V1_STEP: Final = (
    "activate-frontend-select-random-playable-v1"
)
ACTIVATE_FRONTEND_RULER_DESIGNER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-ruler-designer-v1"
)
ACTIVATE_FRONTEND_RULER_DESIGNER_V1_STEP: Final = (
    "activate-frontend-ruler-designer-v1"
)
ACTIVATE_FRONTEND_COAT_OF_ARMS_DESIGNER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-coat-of-arms-designer-v1"
)
ACTIVATE_FRONTEND_COAT_OF_ARMS_DESIGNER_V1_STEP: Final = (
    "activate-frontend-coat-of-arms-designer-v1"
)
COMMIT_FRONTEND_DYNASTY_COAT_OF_ARMS_V1_CAPABILITY: Final = (
    "game.command.commit-frontend-dynasty-coat-of-arms-v1"
)
COMMIT_FRONTEND_DYNASTY_COAT_OF_ARMS_V1_STEP: Final = (
    "commit-frontend-dynasty-coat-of-arms-v1"
)
ACTIVATE_FRONTEND_COAT_OF_ARMS_CUSTOM_MODE_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-coat-of-arms-custom-mode-v1"
)
ACTIVATE_FRONTEND_COAT_OF_ARMS_CUSTOM_MODE_V1_STEP: Final = (
    "activate-frontend-coat-of-arms-custom-mode-v1"
)
PREPARE_FRONTEND_CUSTOM_RULER_V1_STEP: Final = (
    "prepare-frontend-custom-ruler-v1"
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


def normalize_frontend_gui_tree_inspection_v1(
    result: object,
) -> dict[str, object]:
    if not isinstance(result, dict):
        raise ValueError("frontend GUI tree inspection must be an object")
    widgets = result.get("widgets")
    widget_count = result.get("widget_count")
    scope_root_name = result.get("scope_root_name")
    if (
        result.get("step") != INSPECT_FRONTEND_GUI_TREE_V1_STEP
        or result.get("accepted") is not True
        or result.get("status") not in {"available", "unavailable"}
        or not isinstance(scope_root_name, str)
        or scope_root_name
        not in {
            "",
            "_root_",
            "mainmenu_panel_bottom",
            "frontend_bookmarks",
            "lobbyview",
            "ruler_designer",
            "coat_of_arms_page",
        }
        or not isinstance(result.get("root_available"), bool)
        or not isinstance(result.get("truncated"), bool)
        or not isinstance(widget_count, int)
        or isinstance(widget_count, bool)
        or not 0 <= widget_count <= INSPECT_FRONTEND_GUI_TREE_V1_MAXIMUM_WIDGETS
        or not isinstance(widgets, list)
        or len(widgets) != widget_count
        or (result["status"] == "available") is not result["root_available"]
    ):
        raise ValueError("frontend GUI tree inspection is malformed")
    normalized_widgets: list[dict[str, object]] = []
    for row in widgets:
        if not isinstance(row, dict):
            raise ValueError("frontend GUI widget inspection is malformed")
        runtime_name = row.get("runtime_name")
        child_path = row.get("child_path")
        depth = row.get("depth")
        child_count = row.get("child_count")
        vtable_rva = row.get("vtable_rva")
        if (
            not isinstance(runtime_name, str)
            or len(runtime_name.encode("utf-8")) > 127
            or not isinstance(child_path, str)
            or len(child_path) > 383
            or (
                child_path != ""
                and re.fullmatch(r"\d+(?:/\d+)*", child_path) is None
            )
            or not isinstance(depth, int)
            or isinstance(depth, bool)
            or not 0 <= depth <= 64
            or (0 if child_path == "" else child_path.count("/") + 1)
            != depth
            or not isinstance(child_count, int)
            or isinstance(child_count, bool)
            or not 0 <= child_count <= 4096
            or not isinstance(vtable_rva, int)
            or isinstance(vtable_rva, bool)
            or not 0 <= vtable_rva <= 2**64 - 1
            or not isinstance(row.get("effective_visible"), bool)
            or not isinstance(row.get("enabled"), bool)
        ):
            raise ValueError("frontend GUI widget inspection is malformed")
        normalized_widgets.append(
            {
                "runtime_name": runtime_name,
                "child_path": child_path,
                "depth": depth,
                "child_count": child_count,
                "vtable_rva": vtable_rva,
                "effective_visible": row["effective_visible"],
                "enabled": row["enabled"],
            }
        )
    return {
        "schema": "ck3-frontend-gui-tree-inspection-v1",
        "schema_version": 1,
        "step": INSPECT_FRONTEND_GUI_TREE_V1_STEP,
        "accepted": True,
        "status": result["status"],
        "scope_root_name": scope_root_name,
        "root_available": result["root_available"],
        "truncated": result["truncated"],
        "widget_count": widget_count,
        "widgets": normalized_widgets,
        "backend_id": result.get("backend_id"),
        "read_only": True,
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
    }


def normalize_frontend_coat_of_arms_tree_inspection_v1(
    result: object,
) -> dict[str, object]:
    """Normalize only a census rooted at the active native CoA page."""

    if (
        not isinstance(result, dict)
        or result.get("step")
        != INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP
        or result.get("scope_root_name") != "coat_of_arms_page"
    ):
        raise ValueError("frontend coat-of-arms tree inspection is malformed")
    normalized = normalize_frontend_gui_tree_inspection_v1(
        {**result, "step": INSPECT_FRONTEND_GUI_TREE_V1_STEP}
    )
    normalized["step"] = INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP
    return normalized


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


def frontend_lobby_default_ruler_designer_ready_v1(
    inspection: object,
) -> bool:
    if not isinstance(inspection, dict):
        return False
    widgets = inspection.get("widgets")
    return (
        inspection.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and inspection.get("scope_root_name") == "lobbyview"
        and inspection.get("root_available") is True
        and isinstance(widgets, list)
        and any(
            isinstance(row, dict)
            and row.get("child_path") == "3/0/2/3"
            and row.get("runtime_name") == ""
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def frontend_lobby_random_playable_actionable_v1(
    inspection: object,
) -> bool:
    """Prove the fixed vanilla random-playable lobby action is available."""

    if not isinstance(inspection, dict):
        return False
    widgets = inspection.get("widgets")
    return (
        inspection.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and inspection.get("scope_root_name") == "lobbyview"
        and inspection.get("root_available") is True
        and isinstance(widgets, list)
        and any(
            isinstance(row, dict)
            and row.get("child_path") == "4/0/1/0/1"
            and row.get("runtime_name") == ""
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def normalize_frontend_prepare_custom_ruler_v1(
    pick_any_acknowledgement: object,
    select_acknowledgement: object,
    *,
    before: dict[str, object],
    selection_target_inspection: dict[str, object],
    after: dict[str, object],
    lobby_inspection: dict[str, object],
) -> dict[str, object]:
    if not isinstance(select_acknowledgement, dict) or not isinstance(
        pick_any_acknowledgement, dict
    ):
        raise ValueError("frontend custom-ruler acknowledgements must be objects")
    if (
        pick_any_acknowledgement.get("step")
        != ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP
        or pick_any_acknowledgement.get("accepted") is not True
        or pick_any_acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "bookmarks"
        or after.get("route") != "lobby"
        or not frontend_lobby_random_playable_actionable_v1(
            selection_target_inspection
        )
        or select_acknowledgement.get("step")
        != ACTIVATE_FRONTEND_SELECT_RANDOM_PLAYABLE_V1_STEP
        or select_acknowledgement.get("accepted") is not True
        or select_acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or not frontend_lobby_default_ruler_designer_ready_v1(lobby_inspection)
    ):
        raise ValueError("frontend custom-ruler lobby postcondition is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": PREPARE_FRONTEND_CUSTOM_RULER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "prepare_custom_ruler",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "pick_any_acknowledgement": dict(pick_any_acknowledgement),
        "after": after,
        "selection_target_inspection": selection_target_inspection,
        "selection_acknowledgement": dict(select_acknowledgement),
        "lobby_inspection": lobby_inspection,
        "postcondition_verified": True,
        "backend_id": select_acknowledgement.get("backend_id"),
    }


def normalize_frontend_open_ruler_designer_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend ruler-designer acknowledgement must be an object")
    if (
        acknowledgement.get("step") != ACTIVATE_FRONTEND_RULER_DESIGNER_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "lobby"
        or not frontend_lobby_default_ruler_designer_ready_v1(before_inspection)
        or after.get("route") != "ruler_designer"
    ):
        raise ValueError("frontend ruler-designer postcondition is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_RULER_DESIGNER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "open_ruler_designer",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }


def frontend_ruler_designer_dynasty_coa_target_ready_v1(
    value: object,
) -> bool:
    """Recognize the live parent row that owns the fixed dynasty CoA button."""

    if not isinstance(value, dict):
        return False
    widgets = value.get("widgets")
    return bool(
        value.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and value.get("schema_version") == 1
        and value.get("status") == "available"
        and value.get("scope_root_name") == "ruler_designer"
        and value.get("root_available") is True
        and isinstance(widgets, list)
        and any(
            isinstance(row, dict)
            and row.get("child_path") == "0/0/0/0/0/0/0/3/1/0"
            and row.get("runtime_name") == ""
            and row.get("child_count") == 2
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def normalize_frontend_open_coat_of_arms_designer_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend coat-of-arms acknowledgement must be an object")
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_COAT_OF_ARMS_DESIGNER_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "ruler_designer"
        or not frontend_ruler_designer_dynasty_coa_target_ready_v1(
            before_inspection
        )
        or after.get("route") != "coat_of_arms_designer"
    ):
        raise ValueError("frontend coat-of-arms postcondition is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_COAT_OF_ARMS_DESIGNER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "open_coat_of_arms_designer",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }


def frontend_coat_of_arms_dynasty_finish_ready_v1(value: object) -> bool:
    """Recognize only the live dynasty Finish button on the CoA page."""

    if not isinstance(value, dict):
        return False
    widgets = value.get("widgets")
    return bool(
        value.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and value.get("schema_version") == 1
        and value.get("status") == "available"
        and value.get("scope_root_name") == "ruler_designer"
        and value.get("root_available") is True
        and isinstance(widgets, list)
        and any(
            isinstance(row, dict)
            and row.get("child_path") == "0/2/1/1"
            and row.get("runtime_name") == "dynasty_finish_button"
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def normalize_frontend_commit_dynasty_coat_of_arms_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend dynasty coat-of-arms acknowledgement must be an object")
    if (
        acknowledgement.get("step")
        != COMMIT_FRONTEND_DYNASTY_COAT_OF_ARMS_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "coat_of_arms_designer"
        or not frontend_coat_of_arms_dynasty_finish_ready_v1(
            before_inspection
        )
        or after.get("route") != "ruler_designer"
    ):
        raise ValueError("frontend dynasty coat-of-arms commit is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": COMMIT_FRONTEND_DYNASTY_COAT_OF_ARMS_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "commit_dynasty_coat_of_arms",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }


def frontend_coat_of_arms_custom_mode_target_ready_v1(
    value: object,
) -> bool:
    """Recognize exactly one visible source-owned custom-mode button."""

    if not isinstance(value, dict):
        return False
    widgets = value.get("widgets")
    if not (
        value.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and value.get("schema_version") == 1
        and value.get("step")
        == INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP
        and value.get("status") == "available"
        and value.get("scope_root_name") == "coat_of_arms_page"
        and value.get("root_available") is True
        and isinstance(widgets, list)
    ):
        return False
    exact_paths = {
        "0/3/0/2/1/0/0/1/1/0",
        "0/3/0/2/1/0/0/2/1/0",
    }
    visible_targets = [
        row
        for row in widgets
        if isinstance(row, dict)
        and row.get("child_path") in exact_paths
        and row.get("runtime_name") == "button_custom_mode"
        and row.get("effective_visible") is True
        and row.get("enabled") is True
    ]
    return len(visible_targets) == 1


def frontend_coat_of_arms_background_patterns_ready_v1(
    value: object,
) -> bool:
    """Prove the active CoA page has materialized its background pattern UI."""

    if not isinstance(value, dict):
        return False
    widgets = value.get("widgets")
    expected = {
        "0/3/0/2/0": "coa_designer_tabs",
        "0/3/0/2/1/1": "background_panel",
        "0/3/0/2/1/1/2": "patterns",
        "0/3/0/2/1/1/2/0/0": "patterns_scrollbox",
    }
    if not (
        value.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and value.get("schema_version") == 1
        and value.get("step")
        == INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP
        and value.get("status") == "available"
        and value.get("scope_root_name") == "coat_of_arms_page"
        and value.get("root_available") is True
        and isinstance(widgets, list)
    ):
        return False
    visible_by_path = {
        row.get("child_path"): row.get("runtime_name")
        for row in widgets
        if isinstance(row, dict)
        and row.get("effective_visible") is True
        and row.get("enabled") is True
    }
    return all(visible_by_path.get(path) == name for path, name in expected.items())


def normalize_frontend_enter_coat_of_arms_custom_mode_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
    after_inspection: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend coat-of-arms custom-mode acknowledgement must be an object")
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_COAT_OF_ARMS_CUSTOM_MODE_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "coat_of_arms_designer"
        or not frontend_coat_of_arms_custom_mode_target_ready_v1(
            before_inspection
        )
        or after.get("route") != "coat_of_arms_designer"
        or not frontend_coat_of_arms_background_patterns_ready_v1(
            after_inspection
        )
    ):
        raise ValueError("frontend coat-of-arms custom mode is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_COAT_OF_ARMS_CUSTOM_MODE_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "enter_coat_of_arms_custom_mode",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "after": after,
        "after_inspection": after_inspection,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }
