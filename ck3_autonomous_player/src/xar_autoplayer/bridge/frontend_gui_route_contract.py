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
INSPECT_FRONTEND_COAT_OF_ARMS_PATTERN_GRID_V1_CAPABILITY: Final = (
    "game.command.inspect-frontend-coat-of-arms-pattern-grid-v1"
)
INSPECT_FRONTEND_COAT_OF_ARMS_PATTERN_GRID_V1_STEP: Final = (
    "inspect-frontend-coat-of-arms-pattern-grid-v1"
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
ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-start-selected-bookmark-v1"
)
ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP: Final = (
    "activate-frontend-start-selected-bookmark-v1"
)
PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY: Final = (
    "game.command.probe-frontend-bookmark-model-v1"
)
PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP: Final = (
    "probe-frontend-bookmark-model-v1"
)
ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-select-supported-1066-character-v1"
)
ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_STEP: Final = (
    "select-frontend-supported-1066-character-v1"
)
QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_CAPABILITY: Final = (
    "game.command.query-frontend-selected-1066-feudal-candidate-v1"
)
QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP: Final = (
    "query-frontend-selected-1066-feudal-candidate-v1"
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
ACTIVATE_FRONTEND_RANDOMIZE_RULER_FIRST_NAME_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-randomize-ruler-first-name-v1"
)
ACTIVATE_FRONTEND_RANDOMIZE_RULER_FIRST_NAME_V1_STEP: Final = (
    "activate-frontend-randomize-ruler-first-name-v1"
)
ACTIVATE_FRONTEND_FINALIZE_CUSTOM_RULER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-finalize-custom-ruler-v1"
)
ACTIVATE_FRONTEND_FINALIZE_CUSTOM_RULER_V1_STEP: Final = (
    "activate-frontend-finalize-custom-ruler-v1"
)
ACTIVATE_FRONTEND_CONFIRM_CUSTOM_RULER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-confirm-custom-ruler-v1"
)
ACTIVATE_FRONTEND_CONFIRM_CUSTOM_RULER_V1_STEP: Final = (
    "activate-frontend-confirm-custom-ruler-v1"
)
ACTIVATE_FRONTEND_START_LOBBY_SELECTED_CHARACTER_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-start-lobby-selected-character-v1"
)
ACTIVATE_FRONTEND_START_LOBBY_SELECTED_CHARACTER_V1_STEP: Final = (
    "activate-frontend-start-lobby-selected-character-v1"
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
            "coat_of_arms_pattern_grid",
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


def normalize_frontend_coat_of_arms_pattern_grid_inspection_v1(
    result: object,
) -> dict[str, object]:
    """Normalize a fixed-root census with every direct pattern child present."""

    if (
        not isinstance(result, dict)
        or result.get("step")
        != INSPECT_FRONTEND_COAT_OF_ARMS_PATTERN_GRID_V1_STEP
        or result.get("scope_root_name") != "coat_of_arms_pattern_grid"
    ):
        raise ValueError(
            "frontend coat-of-arms pattern-grid inspection is malformed"
        )
    normalized = normalize_frontend_gui_tree_inspection_v1(
        {**result, "step": INSPECT_FRONTEND_GUI_TREE_V1_STEP}
    )
    widgets = normalized["widgets"]
    if not isinstance(widgets, list) or not widgets:
        raise ValueError(
            "frontend coat-of-arms pattern-grid inspection is malformed"
        )
    root = widgets[0]
    if not isinstance(root, dict):
        raise ValueError(
            "frontend coat-of-arms pattern-grid inspection is malformed"
        )
    direct_child_count = root.get("child_count")
    direct_paths = {
        row.get("child_path")
        for row in widgets
        if isinstance(row, dict) and row.get("depth") == 1
    }
    expected_paths = (
        {str(index) for index in range(direct_child_count)}
        if isinstance(direct_child_count, int)
        and not isinstance(direct_child_count, bool)
        and 0 < direct_child_count
        < INSPECT_FRONTEND_GUI_TREE_V1_MAXIMUM_WIDGETS
        else set()
    )
    if (
        normalized.get("status") != "available"
        or normalized.get("root_available") is not True
        or root.get("runtime_name") != ""
        or root.get("child_path") != ""
        or root.get("depth") != 0
        or root.get("effective_visible") is not True
        or root.get("enabled") is not True
        or not expected_paths
        or direct_paths != expected_paths
    ):
        raise ValueError(
            "frontend coat-of-arms pattern-grid direct children are incomplete"
        )
    normalized["step"] = INSPECT_FRONTEND_COAT_OF_ARMS_PATTERN_GRID_V1_STEP
    normalized["direct_child_count"] = direct_child_count
    normalized["direct_children_complete"] = True
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


def normalize_frontend_selected_1066_feudal_candidate_v1(
    result: object,
    *,
    expected_character_name_key: str = (
        "bookmark_rags_to_riches_petty_king_murchad"
    ),
) -> dict[str, object]:
    """Accept only native model identity, never a repeated GUI widget name."""
    if not isinstance(expected_character_name_key, str) or not (
        expected_character_name_key.startswith("bookmark_rags_to_riches_")
        and len(expected_character_name_key) <= 128
    ):
        raise ValueError("expected bookmark character key is invalid")
    if not isinstance(result, dict):
        raise ValueError("frontend selected-candidate query must be an object")
    if (
        result.get("step")
        != QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP
        or result.get("accepted") is not True
        or result.get("status") != "ready"
        or result.get("route") != "bookmarks"
        # CK3 clears the group projection to a native sentinel after a
        # featured character is selected.  The exact bookmark key, start
        # date, character key and government remain the authoritative tuple.
        or result.get("selected_bookmark_group_key")
        not in {None, "bm_group_1066"}
        or result.get("selected_bookmark_key") != "bm_1066_rags_to_riches"
        or result.get("selected_character_name_key")
        != expected_character_name_key
        or result.get("selected_character_government_key")
        != "feudal_government"
        or not isinstance(result.get("selected_bookmark_start_date_raw"), int)
        or isinstance(result.get("selected_bookmark_start_date_raw"), bool)
        or result["selected_bookmark_start_date_raw"] < 1
        or not isinstance(result.get("query_sequence"), int)
        or isinstance(result.get("query_sequence"), bool)
        or result["query_sequence"] < 1
    ):
        raise ValueError(
            "native frontend candidate does not prove the requested 1066 "
            "feudal bookmark character"
        )
    return {
        "schema": "ck3-frontend-selected-1066-feudal-candidate-v1",
        "schema_version": 1,
        "step": QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP,
        "accepted": True,
        "status": "ready",
        "route": "bookmarks",
        "selected_bookmark_group_key": result["selected_bookmark_group_key"],
        "selected_bookmark_key": result["selected_bookmark_key"],
        "selected_character_name_key": result["selected_character_name_key"],
        "selected_character_government_key": result[
            "selected_character_government_key"
        ],
        "selected_bookmark_start_date_raw": result[
            "selected_bookmark_start_date_raw"
        ],
        "query_sequence": result["query_sequence"],
        "backend_id": result.get("backend_id"),
        "read_only": True,
    }


def normalize_frontend_start_selected_bookmark_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    selected_candidate: dict[str, object],
    after_snapshot: dict[str, object],
    campaign_root: dict[str, object],
    expected_character_name_key: str = (
        "bookmark_rags_to_riches_petty_king_murchad"
    ),
) -> dict[str, object]:
    """Require a new paused map and independent feudal campaign-root result."""
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend StartGame acknowledgement must be an object")
    government = campaign_root.get("government")
    played = after_snapshot.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "bookmarks"
        or selected_candidate.get("schema")
        != "ck3-frontend-selected-1066-feudal-candidate-v1"
        or selected_candidate.get("status") != "ready"
        or selected_candidate.get("read_only") is not True
        or selected_candidate.get("selected_bookmark_group_key")
        not in {None, "bm_group_1066"}
        or selected_candidate.get("selected_bookmark_key")
        != "bm_1066_rags_to_riches"
        or selected_candidate.get("selected_character_name_key")
        != expected_character_name_key
        or selected_candidate.get("selected_character_government_key")
        != "feudal_government"
        or selected_candidate.get("selected_bookmark_start_date_raw")
        != after_snapshot.get("date_raw")
        or after_snapshot.get("paused") is not True
        or not isinstance(after_snapshot.get("native_revision"), int)
        or isinstance(after_snapshot.get("native_revision"), bool)
        or after_snapshot["native_revision"] < 1
        or campaign_root.get("campaign_root_context_ready") is not True
        or campaign_root.get("queried_native_revision")
        != after_snapshot.get("native_revision")
        or not isinstance(government, dict)
        or government.get("key") != "feudal_government"
        or not isinstance(campaign_root.get("player_character_id"), int)
        or isinstance(campaign_root.get("player_character_id"), bool)
        or campaign_root["player_character_id"] < 1
        or campaign_root["player_character_id"] != played_id
        or campaign_root.get("date_raw") != after_snapshot.get("date_raw")
    ):
        raise ValueError(
            "frontend StartGame lacks an independent paused feudal map result"
        )
    return {
        "schema": "ck3-frontend-selected-bookmark-start-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
        "accepted": True,
        "status": "verified",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "selected_candidate": selected_candidate,
        "acknowledgement": dict(acknowledgement),
        "after_snapshot": after_snapshot,
        "campaign_root": campaign_root,
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


def frontend_ruler_designer_first_name_target_ready_v1(
    value: object,
) -> bool:
    """Recognize the source-named culture first-name randomizer."""

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
            and row.get("runtime_name") == "random_culture_name"
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def frontend_ruler_designer_finalize_target_ready_v1(
    value: object,
) -> bool:
    """Recognize only the enabled 1.19.0.6 FinalizeOverwrite leaf."""

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
            and row.get("child_path") == "0/0/6/0/2/2"
            and row.get("runtime_name") == ""
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def normalize_frontend_randomize_ruler_first_name_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
    after_inspection: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend first-name acknowledgement must be an object")
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_RANDOMIZE_RULER_FIRST_NAME_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "ruler_designer"
        or before_inspection.get("schema")
        != "ck3-frontend-gui-tree-inspection-v1"
        or before_inspection.get("scope_root_name") != "ruler_designer"
        or before_inspection.get("root_available") is not True
        or after.get("route") != "ruler_designer"
        or not frontend_ruler_designer_finalize_target_ready_v1(
            after_inspection
        )
    ):
        raise ValueError("frontend first-name randomization is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_RANDOMIZE_RULER_FIRST_NAME_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "randomize_ruler_first_name",
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


def normalize_frontend_finalize_custom_ruler_v1(
    acknowledgement: object,
    confirmation_acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    if not isinstance(acknowledgement, dict) or not isinstance(
        confirmation_acknowledgement, dict
    ):
        raise ValueError("frontend finalize acknowledgements must be objects")
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_FINALIZE_CUSTOM_RULER_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or confirmation_acknowledgement.get("step")
        != ACTIVATE_FRONTEND_CONFIRM_CUSTOM_RULER_V1_STEP
        or confirmation_acknowledgement.get("accepted") is not True
        or confirmation_acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "ruler_designer"
        or not frontend_ruler_designer_finalize_target_ready_v1(
            before_inspection
        )
        or after.get("route") != "lobby"
    ):
        raise ValueError("frontend custom-ruler finalization is not proven")
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_FINALIZE_CUSTOM_RULER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "finalize_custom_ruler",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "confirmation_acknowledgement": dict(confirmation_acknowledgement),
        "after": after,
        "postcondition_verified": True,
        "backend_id": acknowledgement.get("backend_id"),
    }


def frontend_lobby_selected_character_start_ready_v1(value: object) -> bool:
    """Recognize the exact ordinary single-player lobby Start button."""

    if not isinstance(value, dict):
        return False
    widgets = value.get("widgets")
    return bool(
        value.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and value.get("schema_version") == 1
        and value.get("status") == "available"
        and value.get("scope_root_name") == "lobbyview"
        and value.get("root_available") is True
        and isinstance(widgets, list)
        and any(
            isinstance(row, dict)
            and row.get("child_path") == "3/0/2/6"
            and row.get("runtime_name") == ""
            and row.get("effective_visible") is True
            and row.get("enabled") is True
            for row in widgets
        )
    )


def normalize_frontend_start_lobby_selected_character_v1(
    acknowledgement: object,
    *,
    before: dict[str, object],
    before_inspection: dict[str, object],
    after_snapshot: dict[str, object],
    campaign_root: dict[str, object],
) -> dict[str, object]:
    """Require the custom ruler to materialize as one paused campaign root."""

    if not isinstance(acknowledgement, dict):
        raise ValueError("frontend lobby Start acknowledgement must be an object")
    played = after_snapshot.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        acknowledgement.get("step")
        != ACTIVATE_FRONTEND_START_LOBBY_SELECTED_CHARACTER_V1_STEP
        or acknowledgement.get("accepted") is not True
        or acknowledgement.get("status")
        != "acknowledged_verification_pending"
        or before.get("route") != "lobby"
        or not frontend_lobby_selected_character_start_ready_v1(
            before_inspection
        )
        or after_snapshot.get("paused") is not True
        or after_snapshot.get("map_ready") is not True
        or not isinstance(after_snapshot.get("native_revision"), int)
        or isinstance(after_snapshot.get("native_revision"), bool)
        or after_snapshot["native_revision"] < 1
        or not isinstance(played_id, int)
        or isinstance(played_id, bool)
        or played_id < 1
        or campaign_root.get("campaign_root_context_ready") is not True
        or campaign_root.get("queried_native_revision")
        != after_snapshot.get("native_revision")
        or campaign_root.get("player_character_id") != played_id
        or campaign_root.get("date_raw") != after_snapshot.get("date_raw")
    ):
        raise ValueError(
            "frontend lobby Start lacks an independent paused campaign root"
        )
    return {
        "schema": "ck3-frontend-custom-ruler-start-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_START_LOBBY_SELECTED_CHARACTER_V1_STEP,
        "accepted": True,
        "status": "verified",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": before,
        "before_inspection": before_inspection,
        "acknowledgement": dict(acknowledgement),
        "after_snapshot": after_snapshot,
        "campaign_root": campaign_root,
        "stable_target_identity": {
            "character_id": played_id,
            "date_raw": after_snapshot.get("date_raw"),
        },
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
