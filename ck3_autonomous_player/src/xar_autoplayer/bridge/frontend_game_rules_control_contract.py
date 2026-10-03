"""Exact .3 native rule-window observation and stock-method ACK contracts."""
from collections.abc import Mapping
import re

QUERY_FRONTEND_GAME_RULES_WINDOW_V1_STEP = "query-frontend-game-rules-window-v1"
QUERY_FRONTEND_GAME_RULES_WINDOW_V1_CAPABILITY = "game.command." + QUERY_FRONTEND_GAME_RULES_WINDOW_V1_STEP
SELECT_FRONTEND_GAME_RULE_V1_STEP = "select-frontend-game-rule-v1"
SELECT_FRONTEND_GAME_RULE_V1_CAPABILITY = "game.command." + SELECT_FRONTEND_GAME_RULE_V1_STEP
APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP = "apply-and-hide-frontend-game-rules-v1"
APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_CAPABILITY = "game.command." + APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP
HIDE_FRONTEND_GAME_RULES_V1_STEP = "hide-frontend-game-rules-v1"
HIDE_FRONTEND_GAME_RULES_V1_CAPABILITY = "game.command." + HIDE_FRONTEND_GAME_RULES_V1_STEP
EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


def require_game_rule_script_key(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,96}", value):
        raise ValueError("game rule keys must be actual script identifiers")
    return value


def _common(raw: object, schema: str, source: str, read_only: bool) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        raise ValueError("native game rules projection must be an object")
    result = dict(raw)
    for key, expected in {"schema": schema, "schema_version": 1,
            "game_version": "1.20.0.3", "executable_sha256": EXE_SHA256,
            "source": source, "read_only": read_only, "backend_id": "native-headless",
            "uses_ocr": False, "uses_mouse": False, "uses_keyboard": False,
            "applied_settings_proven": False}.items():
        if type(result.get(key)) is not type(expected) or result[key] != expected:
            raise ValueError(f"native game rules {key} is not admitted")
    if type(result.get("ready")) is not bool:
        raise ValueError("native game rules ready must be boolean")
    reason = result.get("unavailable_reason")
    if not isinstance(reason, str) or (reason and not re.fullmatch(r"[a-z0-9_]{1,128}", reason)):
        raise ValueError("native game rules reason is malformed")
    if result["ready"] != (reason == ""):
        raise ValueError("native game rules availability contradicts its reason")
    return result


def normalize_frontend_game_rules_window_v1(raw: object) -> dict[str, object]:
    result = _common(raw, "frontend_game_rules_window_v1",
        "CJominiGameRulesGui.owner_root_and_stock_predicates", True)
    fields = ["window_visible", "window_enabled", "is_host", "game_has_started",
              "may_edit", "window_closed_proven"]
    for key in fields:
        if type(result.get(key)) is not bool:
            raise ValueError(f"native game rules {key} must be boolean")
    if not result["ready"] and any(result[k] for k in fields):
        raise ValueError("unavailable game rules window cannot assert state")
    eligible = bool(result["ready"] and result["window_visible"] and
        result["window_enabled"] and result["is_host"] and not result["game_has_started"])
    closed = bool(result["ready"] and not result["window_visible"])
    if result["may_edit"] != eligible or result["window_closed_proven"] != closed:
        raise ValueError("native game rules edit/closure predicates are inconsistent")
    return result


def normalize_frontend_game_rules_mutation_v1(raw: object, action: str) -> dict[str, object]:
    if action not in {"select", "apply_and_hide", "hide"}:
        raise ValueError("unsupported native game rules action")
    result = _common(raw, "frontend_game_rules_mutation_v1",
        "CJominiGameRulesGui.stock_methods", False)
    if result.get("action") != action:
        raise ValueError("native game rules ACK names a different action")
    for key in ["native_invoked", "selection_verified", "apply_invoked", "hide_invoked",
                "window_closed_proven"]:
        if type(result.get(key)) is not bool:
            raise ValueError(f"native game rules {key} must be boolean")
    count = result.get("native_next_calls")
    if type(count) is not int or not 0 <= count <= 511:
        raise ValueError("native Next calls exceed the actual-option bound")
    if result["window_closed_proven"] is not False:
        raise ValueError("native game rules action ACK cannot prove closure")
    if action == "select":
        if result["apply_invoked"] or result["hide_invoked"] or bool(count) != result["native_invoked"]:
            raise ValueError("selection ACK includes inconsistent native calls")
        if result["ready"] and not result["selection_verified"]:
            raise ValueError("selection ACK lacks actual target readback")
    else:
        if count or result["selection_verified"]:
            raise ValueError("window action ACK contains selection state")
        if action == "hide" and result["apply_invoked"]:
            raise ValueError("Hide ACK includes an Apply call")
        if result["ready"] and (not result["native_invoked"] or not result["hide_invoked"] or
                (action == "apply_and_hide" and not result["apply_invoked"])):
            raise ValueError("window action ACK lacks its stock callback sequence")
    return result
