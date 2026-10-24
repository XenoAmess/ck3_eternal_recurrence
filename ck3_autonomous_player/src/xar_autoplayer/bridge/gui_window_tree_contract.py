"""Native named-window census; business model and hover reads remain separate."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
from typing import NotRequired, TypedDict
from .frontend_gui_route_contract import normalize_frontend_gui_tree_inspection_v1
from .version_identity import CK3_12004, require_exact_native_build

GUI_WINDOW_TREE_STEP = "inspect-gui-window-tree-v1"
GUI_WINDOW_TREE_CAPABILITY = "game.command.inspect-gui-window-tree-v1"
GUI_WINDOW_TREE_ROOTS = {
    "ingame_topbar": "ingame_topbar",
    "decisions": "decisions_view",
    "military": "military_view",
    "holy_site": "holy_site_window",
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
    if window_kind in {"military", "holy_site"}:
        from .gui_callback_binding_12004_contract import normalize_callback_binding_rows_12004
        projected = normalize_callback_binding_rows_12004(raw, projected)
    elif "callback_binding_source_12004" in raw or any(
        "standard_click_binding_12004" in row for row in raw.get("widgets", []) if isinstance(row, dict)
    ):
        raise ValueError("callback binding is only admitted for the exact .4 military/HolySite census")
    return {
        **projected, "schema": "ck3-native-gui-window-tree-inspection-v1",
        "step": GUI_WINDOW_TREE_STEP, "window_kind": window_kind,
        "scope_root_name": root_name,
        "rendered_text_available": False, "selected_state_available": False,
        "tooltip_state_available": False, "business_model_available": False,
    }


SCRIPTED_WIDGET_QUERY_STEP = "query-scripted-widget-controls-v1"
SCRIPTED_WIDGET_ACTION_STEP = "activate-scripted-widget-control-v1"
SCRIPTED_WIDGET_QUERY_CAPABILITY = "game.command." + SCRIPTED_WIDGET_QUERY_STEP
SCRIPTED_WIDGET_ACTION_CAPABILITY = "game.command." + SCRIPTED_WIDGET_ACTION_STEP
SCRIPTED_WIDGET_REVISION_TOOLS = frozenset({
    "ck3_query_scripted_widget_controls_v1", "ck3_activate_scripted_widget_control_v1",
})


class ScriptedWidgetBindingV1(TypedDict):
    native_revision: int
    connection_generation: int
    game_pid: int
    played_character_id: int
    date_raw: int
    episode_run_id: str


class ScriptedWidgetControlV1(TypedDict):
    widget_id: str
    runtime_name: str
    child_path: str
    vtable_rva: int
    effective_visible: bool
    enabled: bool
    clickable: bool


class ScriptedWidgetFrameV1(TypedDict):
    native_revision: int
    connection_generation: int
    game_pid: int
    played_character_id: int
    date_raw: int
    game_version: str
    executable_sha256: str
    owner_thread_verified: bool
    source_abi_pins_verified: bool
    frame_verified: bool
    public_revision: NotRequired[str]


class ScriptedWidgetQueryV1(ScriptedWidgetFrameV1):
    schema: str
    step: str
    available: bool
    unavailable_reason: str
    root_name: str
    query_generation: str
    complete: bool
    truncated: bool
    widgets: list[ScriptedWidgetControlV1]
    read_only: bool


class ScriptedWidgetActionV1(ScriptedWidgetFrameV1):
    schema: str
    step: str
    available: bool
    unavailable_reason: str
    root_name: str
    query_generation: str
    widget_id: str
    dispatch_attempted: bool
    dispatch_invoked: bool
    native_handled: bool
    verification_pending: bool
    postcondition_verified: bool


def scripted_widget_decimal_v1(value: object, *, allow_zero: bool = False) -> str:
    """Canonical uint64 text; never pass provider identities through a float."""
    if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is None:
        raise ValueError("scripted widget identity must be canonical decimal text")
    if int(value) >= 2**64 or (value == "0" and not allow_zero):
        raise ValueError("scripted widget identity is outside its uint64 range")
    return value


def scripted_widget_root_v1(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,127}", value) is None:
        raise ValueError("scripted widget root must be a bounded actual native name")
    return value


def scripted_widget_revision_from_snapshot_v1(value: object) -> str:
    return str(_widget_integer(value, "snapshot public revision"))


def _widget_integer(value: object, key: str, *, minimum: int = 1, maximum: int = 2**64 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"invalid scripted widget {key}")
    return value


def _widget_boolean(value: object, key: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"missing scripted widget boolean {key}")
    return value


def _widget_text(value: object, key: str, maximum: int = 1024) -> str:
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise ValueError(f"invalid scripted widget text {key}")
    return value


def scripted_widget_object_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("scripted widget receipt must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("scripted widget receipt keys must be text")
        result[key] = item
    return result


def scripted_widget_binding_v1(snapshot: object) -> ScriptedWidgetBindingV1:
    frame = scripted_widget_object_v1(snapshot)
    diagnostics = scripted_widget_object_v1(frame.get("diagnostics"))
    hello = scripted_widget_object_v1(diagnostics.get("hello"))
    actor = scripted_widget_object_v1(frame.get("played_character"))
    if (require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256")) != CK3_12004
            or hello.get("game_adapter_id") != "ck3-1.20.0.4-msvc-x64"
            or hello.get("ck3_build_match") is not True or frame.get("paused") is not True
            or frame.get("map_ready") is not True or actor.get("alive") is not True):
        raise ValueError("scripted widget controls require the exact .4 alive paused map")
    episode = _widget_text(frame.get("episode_run_id"), "episode_run_id")
    if not episode:
        raise ValueError("scripted widget episode is missing")
    return {
        "native_revision": _widget_integer(frame.get("native_revision"), "native_revision"),
        "connection_generation": _widget_integer(diagnostics.get("connection_generation"), "connection_generation"),
        "game_pid": _widget_integer(hello.get("pid"), "game_pid", maximum=2**32 - 1),
        "played_character_id": _widget_integer(actor.get("character_id"), "played_character_id", maximum=2**32 - 2),
        "date_raw": _widget_integer(frame.get("date_raw"), "date_raw", minimum=-(2**31), maximum=2**31 - 1),
        "episode_run_id": episode,
    }


def _scripted_widget_frame(raw: dict[str, object], binding: ScriptedWidgetBindingV1 | None) -> ScriptedWidgetFrameV1:
    if require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256")) != CK3_12004:
        raise ValueError("scripted widget receipt is not the exact .4 build")
    frame: ScriptedWidgetFrameV1 = {
        "native_revision": _widget_integer(raw.get("native_revision"), "native_revision"),
        "connection_generation": _widget_integer(raw.get("connection_generation"), "connection_generation"),
        "game_pid": _widget_integer(raw.get("game_pid"), "game_pid", maximum=2**32 - 1),
        "played_character_id": _widget_integer(raw.get("played_character_id"), "played_character_id", maximum=2**32 - 2),
        "date_raw": _widget_integer(raw.get("date_raw"), "date_raw", minimum=-(2**31), maximum=2**31 - 1),
        "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256.lower(),
        "owner_thread_verified": _widget_boolean(raw.get("owner_thread_verified"), "owner_thread_verified"),
        "source_abi_pins_verified": _widget_boolean(raw.get("source_abi_pins_verified"), "source_abi_pins_verified"),
        "frame_verified": _widget_boolean(raw.get("frame_verified"), "frame_verified"),
    }
    if binding is not None:
        for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
            if raw.get(key) != binding.get(key):
                raise ValueError(f"scripted widget {key} changed")
    if "public_revision" in raw:
        frame["public_revision"] = scripted_widget_decimal_v1(raw["public_revision"])
    return frame


def normalize_scripted_widget_query_v1(
    value: object, root_name: str, binding: ScriptedWidgetBindingV1 | None = None,
) -> ScriptedWidgetQueryV1:
    root_name = scripted_widget_root_v1(root_name)
    raw = scripted_widget_object_v1(value)
    if raw.get("schema") != "ck3-native-scripted-widget-controls-v1" or raw.get("step") != SCRIPTED_WIDGET_QUERY_STEP:
        raise ValueError("wrong scripted widget query schema/step")
    if raw.get("root_name") != root_name:
        raise ValueError("scripted widget root differs from its request")
    frame = _scripted_widget_frame(raw, binding)
    available = _widget_boolean(raw.get("available"), "available")
    complete = _widget_boolean(raw.get("complete"), "complete")
    truncated = _widget_boolean(raw.get("truncated"), "truncated")
    generation = scripted_widget_decimal_v1(raw.get("query_generation"), allow_zero=not available)
    reason = _widget_text(raw.get("unavailable_reason"), "unavailable_reason")
    rows = raw.get("widgets")
    if not isinstance(rows, list) or len(rows) > 8192:
        raise ValueError("scripted widget rows missing or unbounded")
    widgets: list[ScriptedWidgetControlV1] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for value_row in rows:
        row = scripted_widget_object_v1(value_row)
        widget_id = scripted_widget_decimal_v1(row.get("widget_id"))
        path = _widget_text(row.get("child_path"), "child_path", 383)
        if path and (re.fullmatch(r"[0-9]+(?:/[0-9]+)*", path) is None or len(path.split("/")) > 64):
            raise ValueError("scripted widget child path is malformed")
        if widget_id in ids or path in paths:
            raise ValueError("scripted widget identity/path is duplicated")
        ids.add(widget_id); paths.add(path)
        widgets.append({
            "widget_id": widget_id,
            "runtime_name": _widget_text(row.get("runtime_name"), "runtime_name", 1024),
            "child_path": path,
            "vtable_rva": _widget_integer(row.get("vtable_rva"), "vtable_rva", maximum=2**32 - 1),
            "effective_visible": _widget_boolean(row.get("effective_visible"), "effective_visible"),
            "enabled": _widget_boolean(row.get("enabled"), "enabled"),
            "clickable": _widget_boolean(row.get("clickable"), "clickable"),
        })
    if available:
        if (not complete or truncated or reason or not all((frame["owner_thread_verified"], frame["source_abi_pins_verified"], frame["frame_verified"]))
                or len([row for row in widgets if row["child_path"] == "" and row["runtime_name"] == root_name]) != 1):
            raise ValueError("available scripted widget query lacks complete actual root/frame proof")
    elif generation != "0" or widgets or not reason:
        raise ValueError("unavailable scripted widget query must have zero token, no rows, and a reason")
    return {**frame, "schema": "ck3-native-scripted-widget-controls-v1", "step": SCRIPTED_WIDGET_QUERY_STEP,
            "available": available, "unavailable_reason": reason, "root_name": root_name,
            "query_generation": generation, "complete": complete, "truncated": truncated,
            "widgets": widgets, "read_only": True}


def normalize_scripted_widget_action_v1(
    value: object, query_generation: str, widget_id: str,
    binding: ScriptedWidgetBindingV1 | None = None,
) -> ScriptedWidgetActionV1:
    query_generation = scripted_widget_decimal_v1(query_generation)
    widget_id = scripted_widget_decimal_v1(widget_id)
    raw = scripted_widget_object_v1(value)
    if raw.get("schema") != "ck3-native-scripted-widget-control-action-v1" or raw.get("step") != SCRIPTED_WIDGET_ACTION_STEP:
        raise ValueError("wrong scripted widget action schema/step")
    if raw.get("query_generation") != query_generation or raw.get("widget_id") != widget_id:
        raise ValueError("scripted widget action changed provider-issued identity")
    frame = _scripted_widget_frame(raw, binding)
    result: ScriptedWidgetActionV1 = {
        **frame, "schema": "ck3-native-scripted-widget-control-action-v1", "step": SCRIPTED_WIDGET_ACTION_STEP,
        "available": _widget_boolean(raw.get("available"), "available"),
        "unavailable_reason": _widget_text(raw.get("unavailable_reason"), "unavailable_reason"),
        "root_name": scripted_widget_root_v1(raw.get("root_name")),
        "query_generation": query_generation, "widget_id": widget_id,
        "dispatch_attempted": _widget_boolean(raw.get("dispatch_attempted"), "dispatch_attempted"),
        "dispatch_invoked": _widget_boolean(raw.get("dispatch_invoked"), "dispatch_invoked"),
        "native_handled": _widget_boolean(raw.get("native_handled"), "native_handled"),
        "verification_pending": _widget_boolean(raw.get("verification_pending"), "verification_pending"),
        "postcondition_verified": _widget_boolean(raw.get("postcondition_verified"), "postcondition_verified"),
    }
    if result["postcondition_verified"]:
        raise ValueError("generic widget dispatch cannot certify a business postcondition")
    if result["available"] and (not all((frame["owner_thread_verified"], frame["source_abi_pins_verified"], frame["frame_verified"]))
            or result["unavailable_reason"] or not result["dispatch_attempted"] or not result["dispatch_invoked"]
            or not result["verification_pending"]):
        raise ValueError("available scripted widget action lacks native dispatch proof")
    if result["native_handled"] and not result["dispatch_invoked"]:
        raise ValueError("scripted widget handled flag lacks a native invocation")
    if not result["available"] and (not result["unavailable_reason"] or result["dispatch_invoked"]):
        raise ValueError("unavailable scripted widget action contradicts its dispatch state")
    return result


def scripted_widget_public_result_v1(value: ScriptedWidgetQueryV1 | ScriptedWidgetActionV1) -> dict[str, object]:
    """Only uint64 frame fields change representation at the public JSON boundary."""
    result: dict[str, object] = {key: item for key, item in value.items()}
    result["native_revision"] = str(value["native_revision"])
    result["connection_generation"] = str(value["connection_generation"])
    return result


def write_scripted_widget_evidence_v1(path: Path, value: object) -> None:
    """Create-only evidence; partial/unknown files must never become a retry path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())


def read_scripted_widget_evidence_v1(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    return scripted_widget_object_v1(value)
