"""Exact .3 current rules-window selection observations, before Apply."""

from __future__ import annotations

import re
from typing import Final

QUERY_FRONTEND_GAME_RULE_SELECTIONS_V1_CAPABILITY: Final = (
    "game.command.query-frontend-game-rule-selections-v1"
)
QUERY_FRONTEND_GAME_RULE_SELECTIONS_V1_STEP: Final = (
    "query-frontend-game-rule-selections-v1"
)
ACTIVATE_FRONTEND_GAME_RULES_V1_CAPABILITY: Final = (
    "game.command.activate-frontend-game-rules-v1"
)
ACTIVATE_FRONTEND_GAME_RULES_V1_STEP: Final = "activate-frontend-game-rules-v1"

_SHA: Final = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
_KEY = re.compile(r"[A-Za-z0-9_]{1,96}\Z", re.ASCII)


def normalize_frontend_game_rule_selections_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("game rule observation must be an object")
    expected = {
        "schema": "frontend_game_rule_selections_v1",
        "schema_version": 1,
        "game_version": "1.20.0.3",
        "executable_sha256": _SHA,
        "source": "CJominiGameRulesGui.current_selections",
        "read_only": True,
        "uses_ocr": False,
        "uses_mouse": False,
        "uses_keyboard": False,
        "applied_settings_proven": False,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted or type(value.get(key)) is not type(wanted):
            raise ValueError(f"unverified native game rules field: {key}")
    ready = value.get("ready")
    reason = value.get("unavailable_reason")
    count = value.get("selection_count")
    rows = value.get("selections")
    if (
        type(ready) is not bool
        or not isinstance(reason, str)
        or type(count) is not int
        or not isinstance(rows, list)
        or len(rows) != count
        or not 0 <= count <= 4096
        or (ready and (not count or reason))
        or (not ready and (count or not reason))
    ):
        raise ValueError("inconsistent native game rules readiness/count")
    pairs: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"rule_key", "selected_setting_key"}:
            raise ValueError("game rule row is malformed")
        if any(not isinstance(row[key], str) or not _KEY.fullmatch(row[key])
               for key in ("rule_key", "selected_setting_key")):
            raise ValueError("game rule script key is malformed")
        pairs.append({"rule_key": row["rule_key"],
                      "selected_setting_key": row["selected_setting_key"]})
    keys = [row["rule_key"] for row in pairs]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise ValueError("native game rule IDs are duplicated or unsorted")
    return {**value, "selections": pairs}
