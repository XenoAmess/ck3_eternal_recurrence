"""Native named-window census; business model and hover reads remain separate."""
from __future__ import annotations
from .frontend_gui_route_contract import normalize_frontend_gui_tree_inspection_v1

GUI_WINDOW_TREE_STEP = "inspect-gui-window-tree-v1"
GUI_WINDOW_TREE_CAPABILITY = "game.command.inspect-gui-window-tree-v1"
GUI_WINDOW_TREE_ROOTS = {
    "ingame_topbar": "ingame_topbar",
    "decisions": "decisions_view",
    "decision_detail": "decisiondetail_view",
    "courtier": "xar_courtier_creator_window",
    "vivhite_courtier": "ervc_courtier_creator_window",
    "death_succession": "succession_event_window",
    "death_destiny": "succession_select_destiny_window",
}

def normalize_gui_window_tree_v1(raw: object, window_kind: str) -> dict[str, object]:
    if window_kind not in GUI_WINDOW_TREE_ROOTS:
        raise ValueError("unsupported GUI window census scope")
    root_name = GUI_WINDOW_TREE_ROOTS[window_kind]
    if window_kind in {"ingame_topbar", "death_succession", "death_destiny"} and isinstance(raw, dict) and raw.get("truncated") is not False:
        raise ValueError("native fixed window census is incomplete")
    if not isinstance(raw, dict) or raw.get("step") != GUI_WINDOW_TREE_STEP or raw.get("scope_root_name") != root_name:
        raise ValueError("GUI window census does not match requested native scope")
    if raw.get("root_available") is True:
        rows = raw.get("widgets")
        roots = [row for row in rows if isinstance(row, dict) and row.get("child_path") == ""] if isinstance(rows, list) else []
        if len(roots) != 1 or roots[0].get("runtime_name") != root_name:
            raise ValueError("GUI window census actual root row does not match fixed scope")
    # Reuse the existing row/count/path validator. Project its two routing
    # fields only for validation, then restore the original native identity.
    projected = normalize_frontend_gui_tree_inspection_v1({
        **raw, "step": "inspect-frontend-gui-tree-v1", "scope_root_name": "_root_",
    })
    return {
        **projected, "schema": "ck3-native-gui-window-tree-inspection-v1",
        "step": GUI_WINDOW_TREE_STEP, "window_kind": window_kind,
        "scope_root_name": root_name,
        "rendered_text_available": False, "selected_state_available": False,
        "tooltip_state_available": False, "business_model_available": False,
    }
