"""Nine fixed actual White TextBox UTF-8 values; no button.down or business projection."""
from __future__ import annotations
from copy import deepcopy
from .white_player_business_variables_contract import business_binding

STEP = "query-white-rendered-text-v1"
CAPABILITY = "game.command.query-white-rendered-text-v1"
SCHEMA = "ck3-native-white-rendered-text-v1"
TEXT_NAMES = tuple("ervc_cc_" + name + "_value_text" for name in
                   ("age", "diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess", "price", "gold"))
PROOFS = ("owner_thread_verified", "source_abi_pins_verified", "frame_verified",
          "gui_owner_binding_verified", "tree_complete", "inner_modal_visible", "stable_two_pass_text")
_KEYS = {"schema", "step", "read_only", "available", "rendered_text_available", "selected_down_available",
         *PROOFS, "game_pid", "native_revision", "connection_generation", "played_character_id",
         "date_raw", "widget_count", "fields", "text_source", "unavailable_reason"}

def normalize_white_rendered_text(raw: object, binding: dict[str, object]) -> dict[str, object]:
    if not isinstance(raw, dict) or set(raw) not in (_KEYS, _KEYS | {"backend_id"}):
        raise ValueError("malformed fixed White text DTO")
    if raw.get("backend_id", "native-headless") != "native-headless" or raw["schema"] != SCHEMA or raw["step"] != STEP:
        raise ValueError("wrong native fixed White text source")
    for key in ("read_only", "available", "rendered_text_available", "selected_down_available", *PROOFS):
        if type(raw[key]) is not bool:
            raise ValueError("White text requires actual bool " + key)
    if raw["read_only"] is not True or raw["selected_down_available"] is not False or raw["rendered_text_available"] != raw["available"]:
        raise ValueError("text query cannot provide selected/down credit")
    limits = {"game_pid": (1, 2**32-1), "native_revision": (1, 2**64-1),
              "connection_generation": (1, 2**64-1), "played_character_id": (-1, 2**31-1),
              "date_raw": (-2**31, 2**31-1), "widget_count": (0, 2048)}
    for key, (lo, hi) in limits.items():
        if type(raw[key]) is not int or not lo <= raw[key] <= hi:
            raise ValueError("invalid native White text " + key)
    for key in ("game_pid", "native_revision", "connection_generation"):
        if raw[key] != binding[key]:
            raise ValueError("White text crossed " + key)
    if raw["text_source"] != "actual_CPdxGuiTextbox_GetText_390":
        raise ValueError("White text must come from actual widget getter storage")
    fields = raw["fields"]
    if not isinstance(fields, dict) or set(fields) != set(TEXT_NAMES):
        raise ValueError("White text requires exactly nine fixed fields")
    if raw["available"]:
        if any(raw[key] is not True for key in PROOFS) or not raw["widget_count"] or raw["unavailable_reason"] != "":
            raise ValueError("White text lacks complete visible owner/two-pass/frame proof")
        for key in ("played_character_id", "date_raw"):
            if raw[key] != binding[key]:
                raise ValueError("White text crossed " + key)
        paths = set()
        for name, value in fields.items():
            if not isinstance(value, dict) or set(value) != {"child_path", "text_utf8", "effective_visible", "enabled"}:
                raise ValueError("malformed fixed White text field " + name)
            path = value["child_path"]
            if not isinstance(path, str) or not path.startswith("0/") or len(path.split("/")) > 64:
                raise ValueError("White text is outside actual inner modal")
            if any(not n.isascii() or not n.isdecimal() or int(n) > 2048 for n in path.split("/")) or path in paths:
                raise ValueError("White text child path invalid/ambiguous")
            paths.add(path)
            text = value["text_utf8"]
            if not isinstance(text, str) or "\0" in text:
                raise ValueError("invalid actual White UTF-8 value")
            try:
                encoded = text.encode("utf-8", "strict")
            except UnicodeError as error:
                raise ValueError("invalid actual White UTF-8 value") from error
            if len(encoded) > 2048 or value["effective_visible"] is not True or type(value["enabled"]) is not bool:
                raise ValueError("White text visibility/size is unqualified")
    elif (any(value is not None for value in fields.values()) or
          not isinstance(raw["unavailable_reason"], str) or not raw["unavailable_reason"] or
          raw["played_character_id"] not in (-1, binding["played_character_id"]) or raw["date_raw"] not in (0, binding["date_raw"])):
        raise ValueError("unavailable White text leaks values or crossed frame")
    return deepcopy(raw)
