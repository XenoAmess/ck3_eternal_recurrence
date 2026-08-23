"""Drive Robert 1066 through the opening pact and first map decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import time
from types import SimpleNamespace
import uuid

from .environment import (
    REPO_ROOT,
    EnvironmentSpec,
    ck3_process_inventory,
    doctor,
    ensure_state_path_safe,
    sha256_file,
    verify_profile,
    write_json_atomic,
)
from .errors import AgentError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .runtime import (
    SessionHandle,
    append_event,
    launch,
    log,
    stop_tracked,
    utc_now,
    wait_for_runtime_attestation,
)
from .strategy import (
    read_one_life_strategy,
    record_one_life_episode,
)


OPENING_CONTRACT = (
    REPO_ROOT
    / "ck3_autonomous_player"
    / "configs"
    / "ui"
    / "ck3-1.19.0.6.zh-hans.2560x1440.opening.json"
)
OPENING_ALLOWED_CONTROLS = frozenset(
    {
        "main_menu.new_game",
        "bookmark_lobby.select_robert",
        "bookmark_lobby.start_game",
        "pact_event.accept_contract",
        "first_life_event.begin",
        "blessing_event.option_1",
        "blessing_event.option_2",
        "blessing_event.option_3",
        "curse_event.option_1",
        "curse_event.option_2",
        "map_hud.open_player_character",
        "map_hud.open_lifestyle",
        "lifestyle_selection.open_martial",
        "lifestyle_martial.select_authority_focus",
        "lifestyle_authority_confirmation.confirm",
        "lifestyle_martial_authority.close",
        "map_hud.set_speed_five",
        "map_hud.resume",
        "map_running.pause",
    }
)

INSTANT_UI_TRANSITION_TIMEOUT_SECONDS = 20.0
INITIAL_MAIN_MENU_TIMEOUT_SECONDS = 120.0
ORDINARY_EVENT_WAIT_TIMEOUT_SECONDS = 180.0
DEFAULT_ORDINARY_EVENT_COUNT = 3
MAX_CHAINED_ORDINARY_EVENTS = 8
ACTIVE_EVENT_PREVIEW_REGION = (0.23, 0.08, 0.60, 0.86)
DEVELOPMENT_EVENT_WAIT_SECONDS = 45.0
ONE_LIFE_TURN_WAIT_SECONDS = 10.0
OPENING_DEVELOPMENT_STEPS = (
    "auto-turn",
    "pause-map",
    "life-advance",
    "steward-development",
    "economic-event-cycle",
    "save-checkpoint",
    "restore-checkpoint",
    "dynasty-review",
    "succession-review",
    "marriage-review",
    "marriage-alliance",
    "marriage-confirm-response",
    "death-terminal",
    "strategy-review",
    "war-review",
    "war-target-review",
    "war-interaction-review",
    "war-declaration-review",
    "war-casus-belli-review",
    "war-goal-review",
    "war-declare-palermo",
    "war-raise-all",
    "war-move-palermo",
    "war-map-review",
    "war-find-palermo",
    "war-siege-palermo",
    "war-advance-week",
    "war-advance-month",
    "war-status",
    "war-enforce-demands",
    "war-disband-armies",
    "resolve-current-event",
)

# CK3 1.19.0.6 at the frozen 2560x1440/100% UI contract.  Alt+1..N only
# addresses existing GUIBuildingItem tracks; the empty ``+`` slots are not in
# that shortcut model.  The leftmost standard empty slot is therefore the one
# unavoidable layout-derived mouse target in the construction flow.  The
# rightmost ``+`` at this resolution is the duchy-building slot.
HOLDING_EMPTY_BUILDING_SLOT_CENTER = (461, 1398)

# CK3 1.19.0.6, 2560x1440/100% UI.  Council tasks do not expose native
# shortcuts.  The task identity is therefore confirmed by its visible hover
# tooltip before the single click.  County candidates are hover-probed and the
# click is only submitted when CK3 visibly names the eligible Foggia county.
STEWARD_DEVELOP_COUNTY_TASK_CENTER = (2160, 803)
ROBERT_DEVELOPMENT_COUNTY_CANDIDATE_POINTS = (
    (1220, 560),
    (1320, 520),
    (1360, 560),
    (1190, 640),
)
PALERMO_VISIBLE_LABEL_FALLBACK = (672, 1261)
PALERMO_HOLY_WAR_GOAL_FALLBACK = (1690, 452)
PALERMO_FORT_DESTINATION_FALLBACK = (1200, 650)
CHILD_PORTRAIT_FIRST_CENTER_X = 45
CHILD_PORTRAIT_COLUMN_WIDTH = 85
CHILD_PORTRAIT_CENTER_BELOW_HEADER = 52

# Frozen from Crusader Kings III/game/gui/shortcuts.shortcuts. Scan codes are
# used so the binding does not depend on the active Windows keyboard layout.
CK3_SHORTCUT_SCAN_CODES = {
    "escape": 0x01,
    "1": 0x02,
    "2": 0x03,
    "3": 0x04,
    "4": 0x05,
    "5": 0x06,
    "6": 0x07,
    "7": 0x08,
    "8": 0x09,
    "9": 0x0A,
    "0": 0x0B,
    "minus": 0x0C,
    "equals": 0x0D,
    "backspace": 0x0E,
    "enter": 0x1C,
    "left_ctrl": 0x1D,
    "q": 0x10,
    "v": 0x2F,
    "w": 0x11,
    "j": 0x24,
    "left_shift": 0x2A,
    "left_alt": 0x38,
    "f1": 0x3B,
    "f2": 0x3C,
    "f3": 0x3D,
    "f4": 0x3E,
    "f8": 0x42,
    "space": 0x39,
}
EVENT_OPTION_SHORTCUTS = {
    1: ("shift+1", CK3_SHORTCUT_SCAN_CODES["1"]),
    2: ("shift+2", CK3_SHORTCUT_SCAN_CODES["2"]),
    3: ("shift+3", CK3_SHORTCUT_SCAN_CODES["3"]),
    4: ("shift+4", CK3_SHORTCUT_SCAN_CODES["4"]),
    5: ("shift+5", CK3_SHORTCUT_SCAN_CODES["5"]),
    6: ("shift+6", 0x07),
    7: ("shift+7", 0x08),
    8: ("shift+8", 0x09),
    9: ("shift+9", 0x0A),
    10: ("shift+0", CK3_SHORTCUT_SCAN_CODES["0"]),
    11: ("shift+-", CK3_SHORTCUT_SCAN_CODES["minus"]),
    12: ("shift+=", CK3_SHORTCUT_SCAN_CODES["equals"]),
    13: ("shift+backspace", CK3_SHORTCUT_SCAN_CODES["backspace"]),
}
MAP_PANEL_SHORTCUTS = (
    ("realm", "我的领地", "f2", CK3_SHORTCUT_SCAN_CODES["f2"]),
    ("military", "军事", "f3", CK3_SHORTCUT_SCAN_CODES["f3"]),
    ("council", "内阁", "f4", CK3_SHORTCUT_SCAN_CODES["f4"]),
    ("decisions", "决议", "f8", CK3_SHORTCUT_SCAN_CODES["f8"]),
)

_ECONOMIC_BUILDING_KEYWORDS = {
    "税": 120,
    "收入": 120,
    "发展度": 80,
    "农田": 70,
    "牧场": 60,
    "港": 60,
    "市场": 60,
    "庄园": 55,
    "果园": 50,
    "猎场": 25,
    "征召兵": -20,
    "驻军": -20,
}


def _remaining(deadline: float, stage: str) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise AgentError(f"opening timeout elapsed before {stage}")
    return remaining


def _bind_window(
    spec: EnvironmentSpec, handle: SessionHandle, deadline: float
):
    from .vision import BoundGameWindow

    last_error: AgentError | None = None
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            raise AgentError("CK3 exited before its opening window could be bound")
        try:
            return BoundGameWindow.bind_session(handle, spec.game_exe)
        except AgentError as error:
            last_error = error
            time.sleep(0.25)
    raise last_error or AgentError("CK3 opening window did not appear")


def _action_summary(action: dict[str, object]) -> dict[str, object]:
    return {
        "control_id": action.get("control_id"),
        "status": action.get("status"),
        "receipt_artifact": action.get("receipt_artifact"),
        "send_input": action.get("send_input"),
        "result_observation_id": action.get("result_observation_id"),
        "expected_post_screen": action.get("expected_post_screen"),
    }


_BLESSING_RARITY_SCORE = {"普通": 1000, "稀有": 2000, "传说": 3000}
_BLESSING_CATEGORY_SCORE = {
    "秘契": 900,
    "特质": 800,
    "修正": 700,
    "属性": 650,
    "生活方式": 500,
    "宗族": 450,
    "财富": 400,
    "权谋": 380,
    "信仰": 360,
    "威望": 340,
    "压力": 320,
}
_CURSE_RARITY_LOSS = {"普通": 1000, "稀有": 2000, "传说": 3000}
_CURSE_CATEGORY_LOSS = {
    "秘契": 900,
    "修正": 800,
    "特质": 750,
    "属性": 700,
    "生活方式": 350,
    "财富": 320,
    "权谋": 300,
    "信仰": 280,
    "威望": 260,
    "压力": 240,
    "宗族": 220,
}


def _score_first_blessing(text: str) -> int:
    """Rank a visible first-life blessing without reading hidden game state."""
    rarity = next(
        (score for name, score in _BLESSING_RARITY_SCORE.items() if name in text),
        0,
    )
    category = next(
        (score for name, score in _BLESSING_CATEGORY_SCORE.items() if name in text),
        0,
    )
    magnitudes = [abs(int(value)) for value in re.findall(r"[+-]?\d+", text)]
    magnitude = min(max(magnitudes, default=0), 99)
    return rarity + category + magnitude


def _choose_first_blessing(stable: object) -> tuple[object, str, int]:
    controls = tuple(getattr(stable, "controls", ()))
    latest = getattr(stable, "latest", None)
    spans = tuple(getattr(latest, "spans", ()))
    if len(controls) != 3:
        raise AgentError("first blessing screen does not expose exactly three choices")
    ranked: list[tuple[int, str, object, str]] = []
    for control in controls:
        matches = [
            span
            for span in spans
            if span.bbox == control.bbox and span.center == control.center
        ]
        if len(matches) != 1:
            raise AgentError("first blessing control lacks one exact visible OCR span")
        visible_text = matches[0].text
        ranked.append(
            (
                _score_first_blessing(visible_text),
                str(control.control_id),
                control,
                visible_text,
            )
        )
    score, _control_id, selected, visible_text = max(
        ranked, key=lambda item: (item[0], item[1])
    )
    return selected, visible_text, score


def _score_first_curse(text: str) -> int:
    """Estimate visible curse loss; lower is preferred."""
    rarity = next(
        (loss for name, loss in _CURSE_RARITY_LOSS.items() if name in text),
        0,
    )
    category = next(
        (loss for name, loss in _CURSE_CATEGORY_LOSS.items() if name in text),
        0,
    )
    magnitudes = [abs(int(value)) for value in re.findall(r"[+-]?\d+", text)]
    magnitude = min(max(magnitudes, default=0), 99)
    return rarity + category + magnitude


def _choose_first_curse(stable: object) -> tuple[object, str, int]:
    controls = tuple(getattr(stable, "controls", ()))
    latest = getattr(stable, "latest", None)
    spans = tuple(getattr(latest, "spans", ()))
    if len(controls) != 2:
        raise AgentError("first curse screen does not expose exactly two choices")
    ranked: list[tuple[int, str, object, str]] = []
    for control in controls:
        matches = [
            span
            for span in spans
            if span.bbox == control.bbox and span.center == control.center
        ]
        if len(matches) != 1:
            raise AgentError("first curse control lacks one exact visible OCR span")
        visible_text = matches[0].text
        ranked.append(
            (
                _score_first_curse(visible_text),
                str(control.control_id),
                control,
                visible_text,
            )
        )
    loss, _control_id, selected, visible_text = min(
        ranked, key=lambda item: (item[0], item[1])
    )
    return selected, visible_text, loss


def _extract_player_character_state(observation: dict[str, object]) -> dict[str, object]:
    """Extract the first useful map-state facts from the visible player panel."""
    if observation.get("screen") != "player_character":
        raise AgentError("player character state requires the player character screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("player character observation OCR is missing")
    texts = [
        item.get("text")
        for item in ocr
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    names = [
        text
        for text in texts
        if "阿普利亚公爵" in text and "罗贝尔" in text
    ]
    if len(names) != 1:
        raise AgentError("player character identity is not uniquely visible")

    def visible_count(prefix: str) -> int | None:
        matches: list[int] = []
        for text in texts:
            normalized = re.sub(r"\s+", "", text)
            match = re.fullmatch(re.escape(prefix) + r"[（(]?([0-9]+)[）)]?", normalized)
            if match:
                matches.append(int(match.group(1)))
        return matches[0] if len(matches) == 1 else None

    return {
        "character": names[0],
        "is_player": True,
        "spouse_visible": texts.count("配偶") == 1,
        "player_heir_visible": texts.count("玩家继承人") == 1,
        "child_count": visible_count("子女"),
        "kin_count": visible_count("亲族"),
        "courtier_count": visible_count("廷臣"),
        "vassal_count": visible_count("臣属"),
        "source_observation_id": observation.get("observation_id"),
        "policy_boundary": "player-visible OCR only",
    }


def _choose_one_life_dynasty_action(state: dict[str, object]) -> dict[str, object]:
    """Choose dynasty work for the current life without planning heir continuation."""
    if state.get("spouse_visible") is not True:
        return {
            "action": "seek_player_spouse",
            "priority": 100,
            "reason": "the current ruler has no visible spouse",
            "continue_as_heir_after_death": False,
        }
    if state.get("player_heir_visible") is not True:
        return {
            "action": "prioritize_current_life_heir",
            "priority": 90,
            "reason": "the current ruler has no visible player heir",
            "continue_as_heir_after_death": False,
        }
    child_count = state.get("child_count")
    return {
        "action": "hold_player_marriage_review_child_alliances_later",
        "priority": 20,
        "reason": (
            f"the current ruler already has a spouse, an heir and {child_count} visible children"
            if isinstance(child_count, int)
            else "the current ruler already has a spouse and an heir"
        ),
        "continue_as_heir_after_death": False,
    }


def _succession_panel_visible(frame: object) -> bool:
    """Recognize the native F2/Ctrl+4 succession tab from rendered text."""
    texts = {
        re.sub(r"\s+", "", str(getattr(item, "text", "")))
        for item in tuple(getattr(frame, "spans", ()))
    }
    has_succession = any("继承" in text for text in texts)
    has_current_life_detail = any(
        marker in text
        for text in texts
        for marker in ("玩家继承人", "当前继承人", "继承顺位", "头衔继承")
    )
    return has_succession and has_current_life_detail


def _extract_current_life_succession_state(frame: object) -> dict[str, object]:
    """Summarize succession as a current-ruler risk; death ends this run."""
    if not _succession_panel_visible(frame):
        raise AgentError("current-life succession state requires the native succession tab")
    visible_text = [
        str(getattr(item, "text", "")).strip()
        for item in tuple(getattr(frame, "spans", ()))
        if str(getattr(item, "text", "")).strip()
    ]
    normalized = [re.sub(r"\s+", "", text) for text in visible_text]
    risk_text = [
        text
        for text in visible_text
        if any(marker in re.sub(r"\s+", "", text) for marker in ("失去", "分割", "分封"))
    ]
    law_text = [
        text
        for text in visible_text
        if any(marker in text for marker in ("继承制", "分割继承", "长子继承", "幼子继承"))
    ]
    return {
        "player_heir_visible": any("玩家继承人" in text for text in normalized),
        "partition_risk_visible": bool(risk_text),
        "risk_text": risk_text,
        "succession_law_text": law_text,
        "visible_text": visible_text,
        "source_observation_id": getattr(frame, "observation_id", None),
        "strategy": {
            "scope": "current_ruler_domain_and_alliance_stability",
            "death_is_terminal_settlement": True,
            "continue_as_heir_after_death": False,
        },
    }


def _child_portrait_candidates(frame: object) -> tuple[tuple[int, int], ...]:
    """Derive CK3's seven-slot child row from its rendered section heading."""
    headers = [
        item
        for item in tuple(getattr(frame, "spans", ()))
        if re.fullmatch(
            r"子女[（(]?([0-9]+)[）)]?",
            re.sub(r"\s+", "", str(getattr(item, "text", ""))),
        )
    ]
    if len(headers) != 1:
        raise AgentError("player family panel lacks one visible child heading")
    match = re.fullmatch(
        r"子女[（(]?([0-9]+)[）)]?",
        re.sub(r"\s+", "", str(getattr(headers[0], "text", ""))),
    )
    if match is None:
        raise AgentError("player family child count is malformed")
    count = min(7, int(match.group(1)))
    y = int(getattr(headers[0], "bbox")[3]) + CHILD_PORTRAIT_CENTER_BELOW_HEADER
    return tuple(
        (CHILD_PORTRAIT_FIRST_CENTER_X + CHILD_PORTRAIT_COLUMN_WIDTH * index, y)
        for index in range(count)
    )


def _marriage_interaction_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "寻找配偶")
        or _spans_with_text(frame, "安排婚姻")
    )


def _marriage_window_visible(frame: object) -> bool:
    has_title = bool(
        _spans_with_text(frame, "寻找配偶")
        or _spans_with_text(frame, "安排婚姻")
    )
    return bool(
        has_title
        and _spans_with_text(frame, "排序规则", contains=True)
        and _spans_with_text(frame, "选择结婚对象", contains=True)
    )


def _marriage_offer_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "安排婚姻")
        and _spans_with_text(frame, "求婚")
        and _spans_with_text(frame, "配偶")
    )


def _extract_marriage_review(frame: object) -> dict[str, object]:
    if not _marriage_window_visible(frame):
        raise AgentError("marriage review requires the native matchmaker window")
    visible_text = [
        str(getattr(item, "text", "")).strip()
        for item in tuple(getattr(frame, "spans", ()))
        if str(getattr(item, "text", "")).strip()
    ]
    return {
        "status": "candidate_list_visible",
        "visible_text": visible_text,
        "source_observation_id": getattr(frame, "observation_id", None),
        "selection_policy": "current-life alliance first; never heir continuation",
        "continue_as_heir_after_death": False,
    }


def _marriage_acceptance_in_frame(frame: object) -> dict[str, object] | None:
    texts = [
        str(getattr(item, "text", "")).strip()
        for item in tuple(getattr(frame, "spans", ()))
        if str(getattr(item, "text", "")).strip()
    ]
    acceptance = [text for text in texts if "接受你的订婚提议" in text]
    pairing = [text for text in texts if "埃玛" in text and "贝内迪克特" in text]
    options = [text for text in texts if "太好了" in text]
    if len(acceptance) != 1 or len(pairing) != 1 or len(options) != 1:
        return None
    return {
        "status": "accepted_betrothal",
        "acceptance_text": acceptance[0],
        "pairing_text": pairing[0],
        "option_text": options[0],
        "source_observation_id": getattr(frame, "observation_id", None),
        "current_life_value": "Danish alliance and family relationship",
        "continue_as_heir_after_death": False,
    }


def _call_to_war_in_frame(frame: object) -> dict[str, object] | None:
    """Recognize CK3's alliance call-to-war letter from visible text."""
    titles = _spans_with_text(frame, "召集加入战争", contains=True)
    reject = _spans_with_text(frame, "拒绝")
    accept = _spans_with_text(frame, "同意")
    if len(titles) != 1 or len(reject) != 1 or len(accept) != 1:
        return None
    visible_text = _frame_visible_text(frame)
    war_text = next(
        (
            text
            for text in visible_text
            if "加入" in text and "战争" in text and text != "召集加入战争"
        ),
        None,
    )
    return {
        "status": "alliance_call_visible",
        "title": titles[0].text,
        "war_text": war_text,
        "accept_text": accept[0].text,
        "reject_text": reject[0].text,
        "source_observation_id": getattr(frame, "observation_id", None),
    }


def _frame_visible_text(frame: object) -> list[str]:
    return [
        str(getattr(item, "text", "")).strip()
        for item in tuple(getattr(frame, "spans", ()))
        if str(getattr(item, "text", "")).strip()
    ]


def _death_terminal_state(frame: object) -> str | None:
    """Classify only the three visible states used by one-life termination."""
    texts = _frame_visible_text(frame)
    compact = [re.sub(r"\s+", "", text) for text in texts]
    has_title = any("轮回终结" in text for text in compact)
    if has_title and any("退出到菜单" in text for text in compact):
        return "native_no_heir_settlement"
    if has_title and (
        any("辛苦了,旅人" in text.replace("，", ",") for text in compact)
        or any("这笔账" in text or "下次再来" in text for text in compact)
    ):
        return "recurrence_settlement_event"
    if (
        any(
            marker in text
            for text in compact
            for marker in ("你已过世", "你已经去世", "你已死亡")
        )
        and any("继续扮演" in text for text in compact)
    ):
        return "native_succession_handoff"
    return None


def _observer_mode_visible(frame: object) -> bool:
    return any("正在观察" in text for text in _frame_visible_text(frame))


def _exit_to_main_menu_confirmation_visible(frame: object) -> bool:
    texts = _frame_visible_text(frame)
    return bool(
        any("退出游戏" in text for text in texts)
        and any("退出到主菜单" in text for text in texts)
        and any("退出到桌面" in text for text in texts)
    )


def _visible_labeled_number(
    frame: object, labels: tuple[str, ...]
) -> int | float | None:
    spans = tuple(getattr(frame, "spans", ()))
    number_pattern = re.compile(r"[+-]?\d+(?:[.,]\d+)?")

    def convert(raw: str) -> int | float:
        value = float(raw.replace(",", "."))
        return int(value) if value.is_integer() else value

    for item in spans:
        text = re.sub(r"\s+", "", str(getattr(item, "text", "")))
        for label in labels:
            position = text.find(label)
            if position < 0:
                continue
            suffix = text[position + len(label) :].lstrip(":：")
            match = number_pattern.search(suffix)
            if match:
                return convert(match.group(0))

    label_spans = [
        item
        for item in spans
        if any(label in re.sub(r"\s+", "", str(getattr(item, "text", ""))) for label in labels)
    ]
    for label_span in label_spans:
        label_center = tuple(getattr(label_span, "center", ()))
        if len(label_center) != 2:
            continue
        candidates: list[tuple[int, str]] = []
        for item in spans:
            raw = re.sub(r"\s+", "", str(getattr(item, "text", "")))
            if number_pattern.fullmatch(raw) is None:
                continue
            center = tuple(getattr(item, "center", ()))
            if (
                len(center) == 2
                and center[0] > label_center[0]
                and abs(center[1] - label_center[1]) <= 28
            ):
                candidates.append((center[0] - label_center[0], raw))
        if candidates:
            return convert(min(candidates)[1])
    return None


def _extract_death_terminal(frame: object) -> dict[str, object]:
    terminal_kind = _death_terminal_state(frame)
    if terminal_kind is None:
        raise AgentError("visible frame is not a one-life terminal")
    score = {
        "final": _visible_labeled_number(frame, ("最终分数", "最终分量")),
        "previous_record": _visible_labeled_number(
            frame, ("此前纪录", "此前余烬位阶")
        ),
        "candidate_record": _visible_labeled_number(frame, ("本世候选位阶",)),
        "delta": _visible_labeled_number(frame, ("记录差值", "差值")),
        "completed_bargains": _visible_labeled_number(frame, ("完成交易",)),
        "refused_bargains": _visible_labeled_number(frame, ("拒绝垂青",)),
        "contract_progress": _visible_labeled_number(frame, ("契约进度",)),
    }
    return {
        "terminal": True,
        "terminal_kind": terminal_kind,
        "score": score,
        "visible_text": _frame_visible_text(frame),
        "source_observation_id": getattr(frame, "observation_id", None),
        "continue_as_heir_after_death": False,
    }


def _extract_lifestyle_state(observation: dict[str, object]) -> dict[str, object]:
    """Record the visible lifestyle decision that the opening selected."""
    if observation.get("screen") != "lifestyle_martial_authority":
        raise AgentError("lifestyle state requires the selected authority screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("lifestyle observation OCR is missing")
    texts = [
        re.sub(r"\s+", "", item.get("text", ""))
        for item in ocr
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    if texts.count("军事生活方式") != 1 or texts.count("当前：权威重心") != 1:
        raise AgentError("selected military authority focus is not uniquely visible")
    return {
        "lifestyle": "军事",
        "focus": "权威",
        "visible_current_focus": "当前：权威重心",
        "source_observation_id": observation.get("observation_id"),
        "strategy": "growth100.stabilize-domain-control-v1",
        "policy_boundary": "player-visible OCR only",
    }


def _extract_map_date(observation: dict[str, object]) -> dict[str, object]:
    """Read the rendered CK3 calendar from a visible map observation."""
    if observation.get("screen") not in {"map_hud", "map_running"}:
        raise AgentError("map date requires a paused or running map screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("map observation OCR is missing")
    matches: list[tuple[str, int, int, int]] = []
    for item in ocr:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        bbox = item.get("bbox")
        if (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or any(type(value) is not int for value in bbox)
        ):
            continue
        center_x = (bbox[0] + bbox[2]) // 2
        center_y = (bbox[1] + bbox[3]) // 2
        if not (1792 <= center_x <= 2381 and 1368 <= center_y < 1440):
            continue
        text = re.sub(r"\s+", "", item["text"])
        match = re.search(
            r"(?:公元)?(\d{3,4})年(\d{1,2})月(\d{1,2})日",
            text,
        )
        if match:
            matches.append((text, *(int(value) for value in match.groups())))
    if len(matches) != 1:
        raise AgentError("map date is not uniquely visible")
    visible_text, year, month, day = matches[0]
    try:
        ordinal = datetime(year, month, day, tzinfo=timezone.utc).toordinal()
    except ValueError as error:
        raise AgentError("map date is invalid") from error
    return {
        "year": year,
        "month": month,
        "day": day,
        "ordinal": ordinal,
        "visible_text": visible_text,
        "source_observation_id": observation.get("observation_id"),
        "policy_boundary": "player-visible OCR only",
    }


def _generic_event_in_frame(observation: object) -> dict[str, object] | None:
    """Recognize the standard CK3 event title and option lanes in one frame."""
    spans = tuple(getattr(observation, "spans", ()))
    client_rect = tuple(getattr(observation, "client_rect", ()))
    if len(client_rect) != 4:
        return None
    width = client_rect[2] - client_rect[0]
    height = client_rect[3] - client_rect[1]
    if width <= 0 or height <= 0:
        return None

    titles = []
    options = []
    for item in spans:
        text = str(getattr(item, "text", "")).strip()
        bbox = tuple(getattr(item, "bbox", ()))
        center = tuple(getattr(item, "center", ()))
        score = float(getattr(item, "score", 0.0))
        if not text or len(bbox) != 4 or len(center) != 2 or score < 0.55:
            continue
        box_width = bbox[2] - bbox[0]
        box_height = bbox[3] - bbox[1]
        x_ratio = center[0] / width
        y_ratio = center[1] / height
        if (
            0.25 <= x_ratio <= 0.43
            and 0.245 <= y_ratio <= 0.32
            and box_width >= width * 0.025
            and height * 0.018 <= box_height <= height * 0.05
        ):
            titles.append(item)
        if (
            0.31 <= x_ratio <= 0.45
            and 0.56 <= y_ratio <= 0.76
            and width * 0.025 <= box_width <= width * 0.30
            and height * 0.010 <= box_height <= height * 0.035
            and not re.fullmatch(r"[\d\s./:+-]+", text)
        ):
            options.append(item)
    if len(titles) != 1 or not options:
        return None

    rows: list[object] = []
    for item in sorted(options, key=lambda candidate: candidate.center[1]):
        if rows and abs(item.center[1] - rows[-1].center[1]) <= 12:
            if item.score > rows[-1].score:
                rows[-1] = item
            continue
        rows.append(item)
    if not 1 <= len(rows) <= len(EVENT_OPTION_SHORTCUTS):
        return None
    return {
        "title": titles[0].text,
        "title_center": list(titles[0].center),
        "options": [
            {
                "option_number": index,
                "visible_text": item.text,
                "center": list(item.center),
                "bbox": list(item.bbox),
            }
            for index, item in enumerate(rows, 1)
        ],
        "observation_id": getattr(observation, "observation_id", None),
        "capture_sequence": getattr(observation, "capture_sequence", None),
    }


def _same_generic_event(
    first: dict[str, object], second: dict[str, object]
) -> bool:
    """Require the same rendered event layout in consecutive captures."""
    if first.get("title") != second.get("title"):
        return False
    first_options = first.get("options")
    second_options = second.get("options")
    if not isinstance(first_options, list) or not isinstance(second_options, list):
        return False
    if len(first_options) != len(second_options):
        return False
    for old, new in zip(first_options, second_options):
        if not isinstance(old, dict) or not isinstance(new, dict):
            return False
        old_center = old.get("center")
        new_center = new.get("center")
        if (
            not isinstance(old_center, list)
            or not isinstance(new_center, list)
            or len(old_center) != 2
            or len(new_center) != 2
            or abs(int(old_center[0]) - int(new_center[0])) > 20
            or abs(int(old_center[1]) - int(new_center[1])) > 20
        ):
            return False
    return True


def _visible_event_preview(
    window: object, sequence: int
) -> tuple[dict[str, object] | None, dict[str, object] | None, str | None]:
    """Recognize actionable event lanes with one capture and one OCR pass."""
    from .vision.ocr import ocr_spans

    image = window.capture()
    width, height = image.size
    frame = SimpleNamespace(
        observation_id=None,
        capture_sequence=sequence,
        client_rect=(0, 0, width, height),
        spans=ocr_spans(image, ACTIVE_EVENT_PREVIEW_REGION),
    )
    return (
        _generic_event_in_frame(frame),
        _call_to_war_in_frame(frame),
        _death_terminal_state(frame),
    )


_GENERIC_EVENT_OPTION_WEIGHTS = (
    ("获得", 80),
    ("增加", 65),
    ("提升", 65),
    ("改善", 50),
    ("发展", 45),
    ("学习", 35),
    ("训练", 35),
    ("健康", 55),
    ("金币", 35),
    ("财富", 35),
    ("威望", 30),
    ("虔诚", 30),
    ("好感", 25),
    ("会是我的", 25),
    ("减轻压力", 55),
    ("降低压力", 55),
    ("失去", -90),
    ("死亡", -150),
    ("受伤", -100),
    ("患病", -100),
    ("花费", -55),
    ("支付", -55),
    ("降低", -45),
    ("减少", -35),
    ("压力", -25),
    ("放弃", -25),
    ("远离", -15),
)


def _score_generic_event_option(text: str) -> tuple[int, list[str]]:
    """Score only the text rendered on one ordinary CK3 event option."""
    normalized = re.sub(r"\s+", "", text)
    score = 0
    reasons: list[str] = []
    for term, weight in _GENERIC_EVENT_OPTION_WEIGHTS:
        if term not in normalized:
            continue
        # Do not penalize the negative word inside the two explicit
        # pressure-reduction phrases above.
        if term in {"降低", "减少", "压力"} and (
            "减轻压力" in normalized or "降低压力" in normalized
        ):
            continue
        score += weight
        reasons.append(f"{term}:{weight:+d}")
    for sign, raw_value in re.findall(r"([+-])\s*(\d+)", text):
        value = min(int(raw_value), 100)
        delta = value if sign == "+" else -value
        score += delta
        reasons.append(f"visible-number:{delta:+d}")
    return score, reasons


def _choose_generic_event_option(
    event: dict[str, object],
) -> tuple[dict[str, object], int, list[str]]:
    """Choose the highest visible-utility option, keeping first as tie-break."""
    options = event.get("options")
    if not isinstance(options, list) or not options:
        raise AgentError("ordinary CK3 event has no visible option")
    ranked: list[tuple[int, int, dict[str, object], list[str]]] = []
    for option in options:
        if not isinstance(option, dict):
            raise AgentError("ordinary CK3 event option is malformed")
        number = option.get("option_number")
        text = option.get("visible_text")
        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or number not in EVENT_OPTION_SHORTCUTS
            or not isinstance(text, str)
            or not text.strip()
        ):
            raise AgentError("ordinary CK3 event option is malformed")
        score, reasons = _score_generic_event_option(text)
        ranked.append((score, -number, option, reasons))
    score, _tie_break, selected, reasons = max(
        ranked, key=lambda item: (item[0], item[1])
    )
    return selected, score, reasons


def _confirm_post_shortcut_event(
    driver: object,
    first: dict[str, object],
    deadline: float,
) -> tuple[dict[str, object] | None, object]:
    """Distinguish a stable chained event from a fading prior event."""
    prior = first
    last_frame = None
    while time.monotonic() < deadline:
        last_frame = driver.capture_once()
        candidate = _generic_event_in_frame(last_frame)
        if candidate is None:
            return None, last_frame
        if (
            int(candidate["capture_sequence"])
            == int(prior["capture_sequence"]) + 1
            and _same_generic_event(prior, candidate)
        ):
            return candidate, last_frame
        prior = candidate
    raise AgentError("ordinary CK3 event transition did not stabilize")


def _panel_summary(
    panel_id: str,
    expected_title: str,
    first: object,
    second: object,
) -> dict[str, object]:
    """Bind one keyboard-opened map panel to two consecutive OCR frames."""
    from .vision.ocr import normalize_visible_text

    first_sequence = getattr(first, "capture_sequence", None)
    second_sequence = getattr(second, "capture_sequence", None)
    if (
        isinstance(first_sequence, bool)
        or not isinstance(first_sequence, int)
        or not isinstance(second_sequence, int)
        or second_sequence != first_sequence + 1
    ):
        raise AgentError(f"{panel_id} panel frames are not consecutive")
    target = normalize_visible_text(expected_title)

    def title_candidates(frame: object) -> list[object]:
        client_rect = tuple(getattr(frame, "client_rect", ()))
        if len(client_rect) != 4:
            return []
        height = client_rect[3] - client_rect[1]
        return [
            item
            for item in getattr(frame, "spans", ())
            if normalize_visible_text(str(getattr(item, "text", ""))) == target
            and getattr(item, "center", (0, height))[1] <= height * 0.25
        ]

    first_titles = title_candidates(first)
    second_titles = title_candidates(second)
    pairs = [
        (old, new)
        for old in first_titles
        for new in second_titles
        if abs(old.center[0] - new.center[0]) <= 30
        and abs(old.center[1] - new.center[1]) <= 30
    ]
    if len(pairs) != 1:
        raise AgentError(
            f"{panel_id} panel title {expected_title!r} is not uniquely stable"
        )
    visible_text: list[str] = []
    for item in getattr(second, "spans", ()):
        text = str(getattr(item, "text", "")).strip()
        if text and text not in visible_text:
            visible_text.append(text)
    return {
        "panel": panel_id,
        "title": expected_title,
        "shortcut": next(
            shortcut
            for candidate_id, _title, shortcut, _scan in MAP_PANEL_SHORTCUTS
            if candidate_id == panel_id
        ),
        "frame_observation_ids": [
            getattr(first, "observation_id", None),
            getattr(second, "observation_id", None),
        ],
        "visible_text": visible_text,
        "policy_boundary": "player-visible OCR only",
    }


def _spans_with_text(
    frame: object,
    text: str,
    *,
    region: tuple[float, float, float, float] | None = None,
    contains: bool = False,
) -> list[object]:
    """Return OCR spans matching visible text inside an optional client region."""
    from .vision.ocr import normalize_visible_text

    target = normalize_visible_text(text)
    client_rect = tuple(getattr(frame, "client_rect", ()))
    if len(client_rect) != 4:
        return []
    width = client_rect[2] - client_rect[0]
    height = client_rect[3] - client_rect[1]
    matches: list[object] = []
    for item in getattr(frame, "spans", ()):
        normalized = normalize_visible_text(str(getattr(item, "text", "")))
        if not (target in normalized if contains else normalized == target):
            continue
        center = tuple(getattr(item, "center", ()))
        if len(center) != 2:
            continue
        if region is not None:
            left, top, right, bottom = region
            if not (
                left * width <= center[0] <= right * width
                and top * height <= center[1] <= bottom * height
            ):
                continue
        matches.append(item)
    return matches


def _council_panel_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "内阁", region=(0.72, 0.0, 0.95, 0.18))
        and _spans_with_text(
            frame, "财政总管", region=(0.72, 0.25, 0.98, 0.72)
        )
    )


def _steward_development_targeting_active(frame: object) -> bool:
    """Recognize CK3's county-targeting overlay for the steward task."""
    return bool(
        _spans_with_text(frame, "提升伯爵领发展度", contains=True)
        and _spans_with_text(frame, "点击地图上的一处地点", contains=True)
    )


def _steward_development_assignment_confirmation(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "派遣你的", contains=True)
        and _spans_with_text(frame, "提升伯爵领发展度", contains=True)
    )


def _steward_development_active(frame: object) -> bool:
    """Recognize the steward's active assignment from the persistent task card."""
    return bool(
        _council_panel_visible(frame)
        and _spans_with_text(frame, "在福贾伯爵领", contains=True)
        and _spans_with_text(frame, "剩余", contains=True)
    )


def _pause_menu_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "保存游戏")
        and _spans_with_text(frame, "载入游戏")
        and _spans_with_text(frame, "继续")
        and _spans_with_text(frame, "退出游戏")
    )


def _save_window_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "保存游戏")
        and _spans_with_text(frame, "存档名", contains=True)
    )


def _load_window_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "载入游戏")
        and _spans_with_text(frame, "显示无效", contains=True)
    )


def _title_finder_visible(frame: object) -> bool:
    return bool(_spans_with_text(frame, "查找头衔", contains=True))


def _overwrite_save_confirmation_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "覆盖存档", contains=True)
        and _spans_with_text(frame, "你确定要覆盖", contains=True)
    )


def _palermo_interactions_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "宣战", contains=True)
        and _spans_with_text(frame, "安排婚姻", contains=True)
    )


def _declare_war_window_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "宣战", contains=True)
        and (
            _spans_with_text(frame, "选择宣战理由", contains=True)
            or _spans_with_text(frame, "选择一个目标", contains=True)
        )
    )


def _war_overview_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "战争开始于", contains=True)
        and _spans_with_text(frame, "战争分数", contains=True)
        and _spans_with_text(frame, "强制执行要求", contains=True)
    )


def _war_results_victory_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "胜利", contains=True)
        and _spans_with_text(frame, "就这样吧")
    )


def _army_disband_confirmation_visible(frame: object) -> bool:
    return bool(
        _spans_with_text(frame, "解散军队", region=(0.30, 0.28, 0.70, 0.48))
        and _spans_with_text(frame, "取消", region=(0.30, 0.45, 0.50, 0.62))
        and _spans_with_text(frame, "解散", region=(0.50, 0.45, 0.70, 0.62))
    )


def _county_label_target_candidates(
    frame: object, county_label: str
) -> tuple[tuple[int, int], ...]:
    """Derive map targets from the currently rendered county label."""
    matches = _spans_with_text(
        frame,
        county_label,
        region=(0.15, 0.12, 0.75, 0.85),
    )
    if len(matches) != 1:
        raise AgentError(
            f"map lacks one visible {county_label!r} county label: {len(matches)}"
        )
    x, y = matches[0].center
    width = frame.client_rect[2] - frame.client_rect[0]
    height = frame.client_rect[3] - frame.client_rect[1]
    candidates = (
        (x, y),
        (x + 80, y),
        (x, y + 60),
        (x - 80, y),
    )
    return tuple(
        point
        for point in candidates
        if 0 <= point[0] < width and 0 <= point[1] < height
    )


def _palermo_map_targets(frame: object) -> tuple[tuple[int, int], ...]:
    """Find the visible Palermo label despite OCR occasionally dropping characters."""
    matches = _spans_with_text(
        frame,
        "莱尔",
        contains=True,
        region=(0.15, 0.68, 0.40, 0.95),
    )
    return tuple(dict.fromkeys(span.center for span in matches))


_OPENING_REPLAY_CHECKS = {
    "council-panel": _council_panel_visible,
    "steward-development-targeting": _steward_development_targeting_active,
    "steward-development-confirmation": (
        _steward_development_assignment_confirmation
    ),
    "steward-development-active": _steward_development_active,
}


def replay_opening_observation(
    observation_path: Path, check: str
) -> dict[str, object]:
    """Evaluate a gameplay predicate against archived OCR without launching CK3."""
    try:
        payload = json.loads(observation_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise AgentError(f"opening observation could not be read: {error}") from error
    predicate = _OPENING_REPLAY_CHECKS.get(check)
    if predicate is None:
        raise AgentError(f"unknown opening replay check: {check}")
    policy = payload.get("policy_observation")
    private = payload.get("private_audit")
    if not isinstance(policy, dict) or not isinstance(private, dict):
        raise AgentError("opening observation archive is malformed")
    ocr = policy.get("ocr")
    client_rect = private.get("client_rect")
    if not isinstance(ocr, list) or not isinstance(client_rect, list):
        raise AgentError("opening observation OCR or client rect is missing")
    spans = []
    for item in ocr:
        if not isinstance(item, dict):
            raise AgentError("opening observation OCR row is malformed")
        center = item.get("center")
        bbox = item.get("bbox")
        if not isinstance(center, list) or not isinstance(bbox, list):
            raise AgentError("opening observation OCR geometry is malformed")
        spans.append(
            SimpleNamespace(
                text=str(item.get("text", "")),
                center=tuple(center),
                bbox=tuple(bbox),
            )
        )
    frame = SimpleNamespace(
        client_rect=tuple(client_rect),
        spans=tuple(spans),
        screen=policy.get("screen"),
    )
    matched = bool(predicate(frame))
    return {
        "ok": matched,
        "mode": "offline_observation_replay",
        "check": check,
        "observation_path": str(observation_path.resolve()),
        "observation_id": policy.get("observation_id"),
        "screen": policy.get("screen"),
        "capture_sequence": private.get("capture_sequence"),
    }


def _building_offer_summaries(frame: object) -> list[dict[str, object]]:
    """Rank visible construction rows by player-visible economic language."""
    buttons = _spans_with_text(frame, "修建")
    offers: list[dict[str, object]] = []
    all_spans = tuple(getattr(frame, "spans", ()))
    for index, button in enumerate(buttons, 1):
        button_center = tuple(getattr(button, "center", (0, 0)))
        nearby: list[str] = []
        for item in all_spans:
            center = tuple(getattr(item, "center", (0, 0)))
            if (
                abs(center[1] - button_center[1]) <= 105
                and center[0] <= button_center[0] + 30
            ):
                value = str(getattr(item, "text", "")).strip()
                if value and value not in nearby:
                    nearby.append(value)
        combined = " ".join(nearby)
        score = sum(
            weight
            for keyword, weight in _ECONOMIC_BUILDING_KEYWORDS.items()
            if keyword in combined
        )
        offers.append(
            {
                "offer_index": index,
                "button_text": str(getattr(button, "text", "")),
                "button_center": list(button_center),
                "visible_text": nearby,
                "strategy_score": score,
                "strategy": "visible-economic-building-v1",
            }
        )
    return offers


def _choose_economic_building_offer(frame: object) -> dict[str, object]:
    offers = _building_offer_summaries(frame)
    if not offers:
        raise AgentError("building selection exposes no visible construct action")
    return max(
        offers,
        key=lambda offer: (
            int(offer["strategy_score"]),
            -int(offer["offer_index"]),
        ),
    )


def _building_construction_in_progress(frame: object) -> bool:
    """Recognize CK3's visible holding-row construction progress label."""
    return bool(
        _spans_with_text(frame, "个月内完工", contains=True)
        or _spans_with_text(frame, "正在修建", contains=True)
    )


def _drive_opening(
    spec: EnvironmentSpec,
    handle: SessionHandle,
    manifest: dict[str, object],
    artifacts: Path,
    events: Path,
    contract_path: Path,
    contract_sha256: str,
    deadline: float,
    ordinary_event_count: int = 1,
    inspect_map_panels: bool = False,
    construct_economic_building: bool = False,
    assign_steward_development: bool = False,
    development_step: str | None = None,
    resume_saved_game: bool = False,
) -> dict[str, object]:
    if development_step == "auto-turn":
        # The persistent session may have imported an older strategy module;
        # reload it here as well so adding planner behavior never requires a
        # CK3 restart.
        from . import strategy as strategy_policy

        strategy_policy = importlib.reload(strategy_policy)
        commands: list[dict[str, object]] = []
        session_report_path = artifacts.parent / "report.json"
        if session_report_path.exists():
            try:
                session_report = json.loads(
                    session_report_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as error:
                raise AgentError(
                    f"development session report is unreadable: {error}"
                ) from error
            raw_commands = session_report.get("commands")
            if isinstance(raw_commands, list):
                commands = [row for row in raw_commands if isinstance(row, dict)]
        turn = strategy_policy.choose_one_life_turn(commands)
        selected_step = turn["selected_step"]
        if not isinstance(selected_step, str) or selected_step == "auto-turn":
            raise AgentError("one-life turn planner returned an invalid step")
        result = _drive_opening(
            spec,
            handle,
            manifest,
            artifacts,
            events,
            contract_path,
            contract_sha256,
            deadline,
            ordinary_event_count=ordinary_event_count,
            inspect_map_panels=inspect_map_panels,
            construct_economic_building=construct_economic_building,
            assign_steward_development=assign_steward_development,
            development_step=selected_step,
            resume_saved_game=resume_saved_game,
        )
        result["requested_step"] = "auto-turn"
        result["auto_turn"] = turn
        return result

    # This command only reads the agent's cross-run policy.  Keep it outside
    # the CK3 binding/foreground/OCR path so it stays instant in a persistent
    # development session.
    if development_step == "strategy-review":
        return {
            "development_only": True,
            "release_qualification": False,
            "step": development_step,
            "resume": None,
            "actions": [],
            "strategy": read_one_life_strategy(spec.state_dir),
            "final_screen": "unchanged",
            "final_observation_id": None,
            "window_binding": None,
            "foreground_activation": None,
        }

    from .control import VisibleUiDriver
    from .control.executor import (
        _prepare_key_chord_batch,
        _prepare_key_press_batch,
        _prepare_left_click_batch,
        _prepare_right_click_batch,
    )
    from .vision import load_ui_contract

    display = manifest.get("display")
    if not isinstance(display, dict):
        raise AgentError("prepared display contract is missing")
    language = str(display.get("language", ""))
    contract = load_ui_contract(contract_path, expected_sha256=contract_sha256)
    window = _bind_window(spec, handle, deadline)
    persistent_hot_command = development_step is not None and not resume_saved_game
    if persistent_hot_command:
        # The persistent session already completed the full response/activation
        # gate when it resumed the save.  Re-running its five-second streak for
        # every hot-loaded turn adds no gameplay value.  Subsequent commands do
        # a fresh process/window verification and require CK3 to still be the
        # foreground window; they never steal focus here.
        window.require_foreground()
        foreground = {
            "format_version": 1,
            "status": "confirmed",
            "mode": "persistent_session_already_foreground",
            "target_pid": window.pid,
            "target_hwnd": window.hwnd,
            "synthetic_input": False,
            "full_gate_completed_at_session_start": True,
        }
        append_event(
            events,
            {
                "kind": "foreground_activation_observed",
                "pid": window.pid,
                "hwnd": window.hwnd,
                "status": "confirmed",
                "attestation": foreground,
            },
        )
    else:
        append_event(
            events,
            {
                "kind": "foreground_activation_planned",
                "pid": window.pid,
                "hwnd": window.hwnd,
            },
        )
        foreground = window.request_foreground_without_input(
            responsive_gate_timeout_seconds=min(
                30.0, _remaining(deadline, "foreground activation")
            ),
            responsive_gate_deadline=deadline,
        )
        append_event(
            events,
            {
                "kind": "foreground_activation_finished",
                "pid": window.pid,
                "hwnd": window.hwnd,
                "status": "confirmed",
                "attestation": foreground,
            },
        )

    def new_driver() -> VisibleUiDriver:
        return VisibleUiDriver(
            window,
            contract,
            artifacts,
            expected_game_version=spec.expected_game_version,
            expected_language=language,
            expected_contract_sha256=contract_sha256,
            durable_event_callback=lambda event: append_event(events, event),
            allowed_controls=OPENING_ALLOWED_CONTROLS,
        )

    actions: list[dict[str, object]] = []

    def click(
        screen: str,
        control_id: str,
        next_stage: str,
        *,
        observe_timeout_seconds: float | None = None,
        post_timeout_seconds: float | None = None,
    ) -> dict[str, object]:
        driver = new_driver()
        observation_timeout = _remaining(deadline, f"stable {screen}")
        if observe_timeout_seconds is not None:
            observation_timeout = min(
                observation_timeout, observe_timeout_seconds
            )
        stable = driver.observe_stable(
            screen,
            observation_timeout,
            stable_frames=2,
        )
        matches = [
            control for control in stable.controls if control.control_id == control_id
        ]
        if len(matches) != 1:
            visible = sorted(control.control_id for control in stable.controls)
            raise AgentError(
                f"{screen} lacks one {control_id} control; visible={visible!r}"
            )
        transition_timeout = _remaining(deadline, next_stage)
        if post_timeout_seconds is not None:
            transition_timeout = min(transition_timeout, post_timeout_seconds)
        transition = driver.click_visible_control(
            matches[0].token,
            timeout_seconds=transition_timeout,
        )
        action = transition.get("action")
        observation = transition.get("observation")
        if not isinstance(action, dict) or not isinstance(observation, dict):
            raise AgentError(f"{control_id} transition result is malformed")
        if action.get("status") != "confirmed":
            raise AgentError(f"{control_id} was not confirmed")
        actions.append(_action_summary(action))
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": control_id,
                "result_screen": observation.get("screen"),
                "result_observation_id": observation.get("observation_id"),
            },
        )
        return observation

    def press_shortcut(
        screen: str,
        control_id: str,
        key: str,
        scan_code: int,
        next_screen: str,
        next_stage: str,
        *,
        modifier_scan_code: int | None = None,
        driver: VisibleUiDriver | None = None,
        stable: object | None = None,
        require_visible_control: bool = True,
        post_timeout_seconds: float | None = None,
        summary_fields: dict[str, object] | None = None,
    ) -> dict[str, object]:
        driver = driver or new_driver()
        if stable is None:
            stable = driver.observe_stable(
                screen,
                _remaining(deadline, f"stable {screen} before {key}"),
                stable_frames=2,
            )
        if getattr(stable, "screen", None) != screen:
            raise AgentError(f"{key} source screen is not {screen}")
        if require_visible_control:
            matches = [
                control
                for control in getattr(stable, "controls", ())
                if control.control_id == control_id
            ]
            if len(matches) != 1:
                visible = sorted(
                    control.control_id
                    for control in getattr(stable, "controls", ())
                )
                raise AgentError(
                    f"{screen} lacks one {control_id} shortcut target; "
                    f"visible={visible!r}"
                )
        window.require_foreground()
        requested = 2 if modifier_scan_code is None else 4
        planned: dict[str, object] = {
            "kind": "opening_key_input_planned",
            "control_id": control_id,
            "key": key,
            "scan_code": scan_code,
            "expected_post_screen": next_screen,
        }
        if modifier_scan_code is not None:
            planned["modifier_scan_code"] = modifier_scan_code
        append_event(
            events,
            planned,
        )
        submit = (
            _prepare_key_press_batch(scan_code)
            if modifier_scan_code is None
            else _prepare_key_chord_batch(modifier_scan_code, scan_code)
        )
        accepted, last_error = submit()
        if accepted != requested:
            raise AgentError(
                f"{key} shortcut SendInput was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        transition_timeout = _remaining(deadline, next_stage)
        if post_timeout_seconds is not None:
            transition_timeout = min(transition_timeout, post_timeout_seconds)
        after = driver.observe_stable(
            next_screen,
            transition_timeout,
            stable_frames=2,
        )
        action: dict[str, object] = {
            "control_id": control_id,
            "status": "confirmed",
            "input_kind": "keyboard_shortcut",
            "key": key,
            "scan_code": scan_code,
            "send_input": {
                "requested": requested,
                "accepted": accepted,
                "last_error": last_error,
            },
            "result_observation_id": after.observation_id,
            "expected_post_screen": next_screen,
        }
        if modifier_scan_code is not None:
            action["modifier_scan_code"] = modifier_scan_code
        if summary_fields:
            action.update(summary_fields)
        actions.append(action)
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": control_id,
                "result_screen": after.screen,
                "result_observation_id": after.observation_id,
            },
        )
        return after.to_policy_json()

    def press_event_option(
        screen: str,
        control_id: str,
        next_screen: str,
        next_stage: str,
        *,
        option_number: int | None = None,
        driver: VisibleUiDriver | None = None,
        stable: object | None = None,
        summary_fields: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if option_number is None:
            match = re.fullmatch(r"[a-z_]+\.option_(\d+)", control_id)
            option_number = int(match.group(1)) if match else 0
        shortcut = EVENT_OPTION_SHORTCUTS.get(option_number)
        if shortcut is None:
            raise AgentError(f"{control_id} has no frozen CK3 event shortcut")
        key, scan_code = shortcut
        return press_shortcut(
            screen,
            control_id,
            key,
            scan_code,
            next_screen,
            next_stage,
            modifier_scan_code=CK3_SHORTCUT_SCAN_CODES["left_shift"],
            driver=driver,
            stable=stable,
            post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            summary_fields=summary_fields,
        )

    def inspect_map_panel(
        panel_id: str,
        title: str,
        key: str,
        scan_code: int,
        *,
        leave_open: bool = False,
    ) -> tuple[dict[str, object], object]:
        driver = new_driver()
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": f"map_hud.open_{panel_id}",
                "key": key,
                "scan_code": scan_code,
                "expected_post_screen": f"{panel_id}_panel",
            },
        )
        accepted, last_error = _prepare_key_press_batch(scan_code)()
        if accepted != 2:
            raise AgentError(
                f"{key} panel shortcut SendInput was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        panel_deadline = min(
            deadline,
            time.monotonic() + INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        )
        prior = None
        summary = None
        while time.monotonic() < panel_deadline:
            frame = driver.capture_once()
            if prior is not None:
                try:
                    summary = _panel_summary(panel_id, title, prior, frame)
                    break
                except AgentError:
                    pass
            prior = frame
        if summary is None:
            raise AgentError(f"{key} did not open a stable {panel_id} panel")
        result_observation_id = summary["frame_observation_ids"][-1]
        actions.append(
            {
                "control_id": f"map_hud.open_{panel_id}",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": key,
                "scan_code": scan_code,
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "result_observation_id": result_observation_id,
                "expected_post_screen": f"{panel_id}_panel",
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": f"map_hud.open_{panel_id}",
                "result_screen": f"{panel_id}_panel",
                "result_observation_id": result_observation_id,
            },
        )

        if leave_open:
            return summary, frame

        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": f"{panel_id}_panel.close",
                "key": key,
                "scan_code": scan_code,
                "expected_post_screen": "map_hud",
            },
        )
        close_accepted, close_last_error = _prepare_key_press_batch(scan_code)()
        if close_accepted != 2:
            raise AgentError(
                f"{key} panel-close shortcut SendInput was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        after = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, f"map after {panel_id} inspection"),
            ),
            stable_frames=2,
        )
        actions.append(
            {
                "control_id": f"{panel_id}_panel.close",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": key,
                "scan_code": scan_code,
                "send_input": {
                    "requested": 2,
                    "accepted": close_accepted,
                    "last_error": close_last_error,
                },
                "result_observation_id": after.observation_id,
                "expected_post_screen": "map_hud",
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": f"{panel_id}_panel.close",
                "result_screen": "map_hud",
                "result_observation_id": after.observation_id,
            },
        )
        return summary, after.to_policy_json()

    def wait_for_custom_state(
        driver: VisibleUiDriver,
        predicate: object,
        stage: str,
        timeout_seconds: float = INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    ) -> tuple[object, object]:
        custom_deadline = min(
            deadline,
            time.monotonic() + timeout_seconds,
        )
        prior = None
        while time.monotonic() < custom_deadline:
            frame = driver.capture_once()
            if bool(predicate(frame)):
                if (
                    prior is not None
                    and frame.capture_sequence == prior.capture_sequence + 1
                    and bool(predicate(prior))
                ):
                    return prior, frame
                prior = frame
            else:
                prior = None
        raise AgentError(f"{stage} did not become visibly stable")

    def click_visible_text_once(
        driver: VisibleUiDriver,
        source: object,
        *,
        text: str,
        region: tuple[float, float, float, float],
        control_id: str,
        expected_post_screen: str,
        post_predicate: object,
    ) -> tuple[object, object]:
        issued = _spans_with_text(source, text, region=region)
        if len(issued) != 1:
            raise AgentError(
                f"{control_id} lacks one visible {text!r} target: {len(issued)}"
            )
        fresh = driver.capture_once()
        fresh_matches = [
            item
            for item in _spans_with_text(fresh, text, region=region)
            if abs(item.center[0] - issued[0].center[0]) <= 20
            and abs(item.center[1] - issued[0].center[1]) <= 20
        ]
        if len(fresh_matches) != 1:
            raise AgentError(f"{control_id} visible target changed before click")
        target = fresh_matches[0]
        point = tuple(target.center)
        window.require_foreground()
        window.require_unobscured(point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": control_id,
                "visible_text": target.text,
                "bbox": list(target.bbox),
                "center": list(point),
                "expected_post_screen": expected_post_screen,
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        screen_point = (
            window.client_rect[0] + point[0],
            window.client_rect[1] + point[1],
        )
        pyautogui.moveTo(*screen_point, duration=0.12)
        time.sleep(0.2)
        window.require_cursor_target(point)
        accepted, last_error = _prepare_left_click_batch(0.05)()
        if accepted != 2:
            raise AgentError(
                f"{control_id} mouse click was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first, second = wait_for_custom_state(
            driver,
            post_predicate,
            expected_post_screen,
        )
        action = {
            "control_id": control_id,
            "status": "confirmed",
            "input_kind": "visible_ocr_click",
            "visible_text": target.text,
            "source_observation_id": fresh.observation_id,
            "click_point": list(point),
            "send_input": {
                "requested": 2,
                "accepted": accepted,
                "last_error": last_error,
            },
            "result_observation_id": second.observation_id,
            "expected_post_screen": expected_post_screen,
        }
        actions.append(action)
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": control_id,
                "result_screen": expected_post_screen,
                "result_observation_id": second.observation_id,
            },
        )
        return first, second

    def accept_visible_call_to_war(
        driver: VisibleUiDriver,
        call: dict[str, object],
    ) -> tuple[dict[str, object], dict[str, object]]:
        window.require_foreground()
        speed_accepted, speed_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["1"]
        )()
        if speed_accepted != 2:
            raise AgentError(
                "call-to-war speed-one shortcut was partial: "
                f"accepted={speed_accepted}, last_error={speed_last_error}"
            )
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "diplomacy.call_to_war.accept",
                "key": "shift+2",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["2"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                "expected_post_screen": "map",
            },
        )
        accepted, last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_shift"],
            CK3_SHORTCUT_SCAN_CODES["2"],
        )()
        if accepted != 4:
            raise AgentError(
                "call-to-war acceptance shortcut was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        time.sleep(0.5)
        _map_first, after = wait_for_custom_state(
            driver,
            lambda frame: bool(
                getattr(frame, "screen", None) in {"map_hud", "map_running"}
                and _call_to_war_in_frame(frame) is None
            ),
            "map after accepting alliance call to war",
        )
        if after.screen == "map_running":
            final = press_shortcut(
                "map_running",
                "map_running.pause_after_call_to_war",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused after accepting alliance call to war",
                driver=driver,
                stable=after,
                require_visible_control=False,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
        else:
            final = after.to_policy_json()
        resolved = dict(call)
        resolved.update(
            {
                "status": "accepted_alliance_call",
                "strategy": "honor_current_life_alliance-v1",
                "continue_as_heir_after_death": False,
            }
        )
        actions.append(
            {
                "control_id": "diplomacy.call_to_war.accept",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "shift+2",
                "send_input": {
                    "requested": 4,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "result_observation_id": final["observation_id"],
                "expected_post_screen": "map_hud",
            }
        )
        return resolved, final

    def assign_steward_to_develop_foggia() -> tuple[
        dict[str, object], dict[str, object]
    ]:
        _council_summary, council_frame = inspect_map_panel(
            "council",
            "内阁",
            "f4",
            CK3_SHORTCUT_SCAN_CODES["f4"],
            leave_open=True,
        )
        driver = new_driver()
        width = window.client_rect[2] - window.client_rect[0]
        height = window.client_rect[3] - window.client_rect[1]
        if (width, height) != (2560, 1440):
            raise AgentError("council task layout differs from 2560x1440")
        if not _council_panel_visible(council_frame):
            raise AgentError("council panel changed before steward assignment")

        if _steward_development_active(council_frame):
            actions.append(
                {
                    "control_id": "council.steward.develop_county.verify",
                    "status": "already_active",
                    "input_kind": "visible_state_verification",
                    "visible_identity": "提升伯爵领发展度",
                    "visible_target": "福贾伯爵领",
                    "source_observation_id": council_frame.observation_id,
                    "result_observation_id": council_frame.observation_id,
                    "expected_post_screen": "council_panel",
                }
            )
            window.require_foreground()
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": "council_panel.close_after_steward_verification",
                    "key": "f4",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                    "expected_post_screen": "map_hud",
                },
            )
            close_accepted, close_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["f4"]
            )()
            if close_accepted != 2:
                raise AgentError(
                    "F4 council close after steward verification was partial: "
                    f"accepted={close_accepted}, last_error={close_last_error}"
                )
            final_map = driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "map after steward verification"),
                ),
                stable_frames=2,
            )
            actions.append(
                {
                    "control_id": "council_panel.close_after_steward_verification",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "f4",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                    "send_input": {
                        "requested": 2,
                        "accepted": close_accepted,
                        "last_error": close_last_error,
                    },
                    "result_observation_id": final_map.observation_id,
                    "expected_post_screen": "map_hud",
                }
            )
            return (
                {
                    "status": "already_active",
                    "task": "提升伯爵领发展度",
                    "county": "福贾伯爵领",
                    "active_observation_id": council_frame.observation_id,
                    "strategy": "visible-active-task-card-v1",
                },
                final_map.to_policy_json(),
            )

        task_point = STEWARD_DEVELOP_COUNTY_TASK_CENTER
        window.require_foreground()
        window.require_unobscured(task_point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "council.steward.develop_county",
                "center": list(task_point),
                "visible_identity": "提升伯爵领发展度",
                "expected_post_screen": "steward_development_targeting",
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        screen_point = (
            window.client_rect[0] + task_point[0],
            window.client_rect[1] + task_point[1],
        )
        pyautogui.moveTo(*screen_point, duration=0.12)
        _task_hover_first, task_hover = wait_for_custom_state(
            driver,
            lambda frame: bool(
                _council_panel_visible(frame)
                and _spans_with_text(
                    frame, "提升伯爵领发展度", contains=True
                )
            ),
            "steward development task tooltip",
        )
        window.require_cursor_target(task_point)
        accepted, last_error = _prepare_left_click_batch(0.05)()
        if accepted != 2:
            raise AgentError(
                "steward development task click was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        _targeting_first, targeting = wait_for_custom_state(
            driver,
            _steward_development_targeting_active,
            "steward development county targeting",
        )
        actions.append(
            {
                "control_id": "council.steward.develop_county",
                "status": "confirmed",
                "input_kind": "visible_layout_click",
                "visible_identity": "提升伯爵领发展度",
                "click_point": list(task_point),
                "source_observation_id": task_hover.observation_id,
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "result_observation_id": targeting.observation_id,
                "expected_post_screen": "steward_development_targeting",
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": "council.steward.develop_county",
                "result_screen": "steward_development_targeting",
                "result_observation_id": targeting.observation_id,
            },
        )

        target_point = None
        target_hover = None
        hover_attempts: list[dict[str, object]] = []
        visible_county_candidates = _county_label_target_candidates(
            targeting, "福贾"
        )
        candidate_points = tuple(
            dict.fromkeys(
                visible_county_candidates
                + ROBERT_DEVELOPMENT_COUNTY_CANDIDATE_POINTS
            )
        )
        for candidate in candidate_points:
            window.require_foreground()
            window.require_unobscured(candidate)
            pyautogui.moveTo(
                window.client_rect[0] + candidate[0],
                window.client_rect[1] + candidate[1],
                duration=0.12,
            )
            try:
                _hover_first, hover_second = wait_for_custom_state(
                    driver,
                    lambda frame: bool(
                        _steward_development_targeting_active(frame)
                        and _spans_with_text(
                            frame, "福贾伯爵领", contains=True
                        )
                    ),
                    "Foggia county hover",
                    timeout_seconds=4.0,
                )
            except AgentError:
                hover_attempts.append(
                    {"center": list(candidate), "visible_target": False}
                )
                continue
            window.require_cursor_target(candidate)
            target_point = candidate
            target_hover = hover_second
            hover_attempts.append(
                {
                    "center": list(candidate),
                    "visible_target": True,
                    "observation_id": hover_second.observation_id,
                }
            )
            break
        if target_point is None or target_hover is None:
            raise AgentError(
                "Foggia county was not visibly identified at any frozen map candidate"
            )

        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "steward_development_targeting.foggia_county",
                "center": list(target_point),
                "visible_identity": "福贾伯爵领",
                "expected_post_screen": "steward_development_assigned",
            },
        )
        target_accepted, target_last_error = _prepare_left_click_batch(0.05)()
        if target_accepted != 2:
            raise AgentError(
                "Foggia county task click was partial: "
                f"accepted={target_accepted}, last_error={target_last_error}"
            )

        def assignment_transition(frame: object) -> bool:
            return bool(
                _steward_development_assignment_confirmation(frame)
                or (
                    not _steward_development_targeting_active(frame)
                    and (
                        _council_panel_visible(frame)
                        or _spans_with_text(frame, "政治地图", contains=True)
                    )
                )
            )

        _assigned_first, assigned_frame = wait_for_custom_state(
            driver,
            assignment_transition,
            "steward development assignment transition",
        )
        actions.append(
            {
                "control_id": "steward_development_targeting.foggia_county",
                "status": "confirmed",
                "input_kind": "visible_layout_click",
                "visible_identity": "福贾伯爵领",
                "click_point": list(target_point),
                "source_observation_id": target_hover.observation_id,
                "send_input": {
                    "requested": 2,
                    "accepted": target_accepted,
                    "last_error": target_last_error,
                },
                "result_observation_id": assigned_frame.observation_id,
                "expected_post_screen": "steward_development_assigned",
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": "steward_development_targeting.foggia_county",
                "result_screen": "steward_development_assigned",
                "result_observation_id": assigned_frame.observation_id,
            },
        )

        confirmation_observation_id = None
        if _steward_development_assignment_confirmation(assigned_frame):
            confirmation_observation_id = assigned_frame.observation_id
            window.require_foreground()
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": "steward_development_confirmation.accept",
                    "key": "enter",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                    "expected_post_screen": "steward_development_assigned",
                },
            )
            confirm_accepted, confirm_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["enter"]
            )()
            if confirm_accepted != 2:
                raise AgentError(
                    "steward task confirmation shortcut was partial: "
                    f"accepted={confirm_accepted}, last_error={confirm_last_error}"
                )
            _confirm_first, assigned_frame = wait_for_custom_state(
                driver,
                lambda frame: bool(
                    not _steward_development_targeting_active(frame)
                    and not _steward_development_assignment_confirmation(frame)
                    and (
                        _council_panel_visible(frame)
                        or _spans_with_text(frame, "政治地图", contains=True)
                    )
                ),
                "confirmed steward development assignment",
            )
            actions.append(
                {
                    "control_id": "steward_development_confirmation.accept",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "enter",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                    "send_input": {
                        "requested": 2,
                        "accepted": confirm_accepted,
                        "last_error": confirm_last_error,
                    },
                    "result_observation_id": assigned_frame.observation_id,
                    "expected_post_screen": "steward_development_assigned",
                }
            )

        if _council_panel_visible(assigned_frame):
            active_panel = assigned_frame
        else:
            _active_summary, active_panel = inspect_map_panel(
                "council",
                "内阁",
                "f4",
                CK3_SHORTCUT_SCAN_CODES["f4"],
                leave_open=True,
            )
        _active_first, active_frame = wait_for_custom_state(
            driver,
            _steward_development_active,
            "active steward development task",
        )
        actions.append(
            {
                "control_id": "council.steward.develop_county.verify",
                "status": "confirmed",
                "input_kind": "visible_state_verification",
                "visible_identity": "提升伯爵领发展度",
                "visible_target": "福贾伯爵领",
                "source_observation_id": getattr(
                    active_panel, "observation_id", None
                ),
                "result_observation_id": active_frame.observation_id,
                "expected_post_screen": "council_panel",
            }
        )

        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "council_panel.close_after_steward_assignment",
                "key": "f4",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                "expected_post_screen": "map_hud",
            },
        )
        close_accepted, close_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["f4"]
        )()
        if close_accepted != 2:
            raise AgentError(
                "F4 council close was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        final_map = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "map after steward assignment"),
            ),
            stable_frames=2,
        )
        actions.append(
            {
                "control_id": "council_panel.close_after_steward_assignment",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "f4",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                "send_input": {
                    "requested": 2,
                    "accepted": close_accepted,
                    "last_error": close_last_error,
                },
                "result_observation_id": final_map.observation_id,
                "expected_post_screen": "map_hud",
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": "council_panel.close_after_steward_assignment",
                "result_screen": "map_hud",
                "result_observation_id": final_map.observation_id,
            },
        )
        return (
            {
                "councillor": "财政总管",
                "task": "提升伯爵领发展度",
                "target": "福贾伯爵领",
                "task_button_center": list(task_point),
                "target_point": list(target_point),
                "target_hover_attempts": hover_attempts,
                "targeting_observation_id": targeting.observation_id,
                "confirmation_observation_id": confirmation_observation_id,
                "active_observation_id": active_frame.observation_id,
                "strategy": "visible-eligible-foggia-development-v1",
                "policy_boundary": "player-visible task tooltip and county name",
            },
            final_map.to_policy_json(),
        )

    def construct_first_economic_building() -> tuple[dict[str, object], dict[str, object]]:
        realm_title = "我的领地"
        _realm_summary, realm_frame = inspect_map_panel(
            "realm",
            realm_title,
            "f2",
            CK3_SHORTCUT_SCAN_CODES["f2"],
            leave_open=True,
        )
        driver = new_driver()

        # An ordinary event can be queued while the slower panel inspection
        # pass is running.  Resolve such a visible interruption with CK3's
        # native Shift+number binding before looking for the holding row.
        for _interruption in range(MAX_CHAINED_ORDINARY_EVENTS):
            detected_event = _generic_event_in_frame(realm_frame)
            if detected_event is None:
                break
            selected_event_option, option_score, score_reasons = (
                _choose_generic_event_option(detected_event)
            )
            option_number = int(selected_event_option["option_number"])
            key, scan_code = EVENT_OPTION_SHORTCUTS[option_number]
            interruption_index = len(ordinary_events) + 1
            control_id = f"ordinary_event.option_{option_number}"
            window.require_foreground()
            speed_accepted, speed_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["1"]
            )()
            if speed_accepted != 2:
                raise AgentError(
                    "ordinary-event speed-one latch was partial: "
                    f"accepted={speed_accepted}, last_error={speed_last_error}"
                )
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": control_id,
                    "event_index": interruption_index,
                    "key": key,
                    "scan_code": scan_code,
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    "expected_post_screen": "realm_or_ordinary_event",
                },
            )
            accepted, last_error = _prepare_key_chord_batch(
                CK3_SHORTCUT_SCAN_CODES["left_shift"], scan_code
            )()
            if accepted != 4:
                raise AgentError(
                    f"{key} interrupting-event shortcut SendInput was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )

            transition_deadline = min(deadline, time.monotonic() + 12.0)
            prior_frame = None
            prior_state = None
            while time.monotonic() < transition_deadline:
                candidate = driver.capture_once()
                candidate_event = _generic_event_in_frame(candidate)
                if candidate_event is not None:
                    candidate_state = (
                        "ordinary_event",
                        str(candidate_event["title"]),
                        tuple(
                            str(item["visible_text"])
                            for item in candidate_event["options"]
                        ),
                    )
                elif _spans_with_text(candidate, realm_title, contains=True):
                    candidate_state = ("realm_panel",)
                else:
                    prior_frame = None
                    prior_state = None
                    continue
                if (
                    prior_frame is not None
                    and candidate.capture_sequence
                    == prior_frame.capture_sequence + 1
                    and candidate_state == prior_state
                ):
                    realm_frame = candidate
                    break
                prior_frame = candidate
                prior_state = candidate_state
            else:
                raise AgentError(
                    "interrupting ordinary event did not resolve to a stable state"
                )
            result_event = _generic_event_in_frame(realm_frame)
            result_screen = (
                "ordinary_event" if result_event is not None else "realm_panel"
            )
            actions.append(
                {
                    "control_id": control_id,
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": key,
                    "scan_code": scan_code,
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    "send_input": {
                        "requested": 4,
                        "accepted": accepted,
                        "last_error": last_error,
                    },
                    "event_index": interruption_index,
                    "event_title": detected_event["title"],
                    "visible_option": selected_event_option["visible_text"],
                    "visible_option_count": len(detected_event["options"]),
                    "strategy_score": option_score,
                    "strategy_reasons": score_reasons,
                    "source_observation_id": detected_event["observation_id"],
                    "result_observation_id": realm_frame.observation_id,
                    "expected_post_screen": result_screen,
                }
            )
            append_event(
                events,
                {
                    "kind": "opening_step_completed",
                    "control_id": control_id,
                    "event_index": interruption_index,
                    "result_screen": result_screen,
                    "result_observation_id": realm_frame.observation_id,
                },
            )
            ordinary_events.append(
                {
                    "event_index": interruption_index,
                    "title": detected_event["title"],
                    "visible_options": detected_event["options"],
                    "selected_option_number": option_number,
                    "selected_visible_text": selected_event_option["visible_text"],
                    "strategy_score": option_score,
                    "strategy_reasons": score_reasons,
                    "strategy": "visible-option-utility-v1",
                    "source_observation_id": detected_event["observation_id"],
                    "interrupted_action": "construct_first_economic_building",
                }
            )
        else:
            if _generic_event_in_frame(realm_frame) is not None:
                raise AgentError(
                    "ordinary CK3 interruption chain exceeded its bounded depth"
                )

        def holding_view(frame: object) -> bool:
            return (
                bool(_spans_with_text(frame, "地产类型", contains=True))
                and bool(_spans_with_text(frame, "你的城堡地产", contains=True))
                and bool(_spans_with_text(frame, "持有者", contains=True))
            )

        _holding_first, holding_second = click_visible_text_once(
            driver,
            realm_frame,
            text="可以修建建筑",
            region=(0.68, 0.33, 0.78, 0.42),
            control_id="realm_panel.open_first_buildable_holding",
            expected_post_screen="holding_view",
            post_predicate=holding_view,
        )

        width = window.client_rect[2] - window.client_rect[0]
        height = window.client_rect[3] - window.client_rect[1]
        if (width, height) != (2560, 1440):
            raise AgentError("holding building-slot layout differs from 2560x1440")
        fresh_holding = driver.capture_once()
        if not holding_view(fresh_holding):
            raise AgentError("holding view changed before opening an empty slot")
        slot_point = HOLDING_EMPTY_BUILDING_SLOT_CENTER
        window.require_foreground()
        window.require_unobscured(slot_point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "holding_view.leftmost_standard_empty_building_slot",
                "center": list(slot_point),
                "expected_post_screen": "building_selection",
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        screen_point = (
            window.client_rect[0] + slot_point[0],
            window.client_rect[1] + slot_point[1],
        )
        pyautogui.moveTo(*screen_point, duration=0.12)
        time.sleep(0.2)
        window.require_cursor_target(slot_point)
        accepted, last_error = _prepare_left_click_batch(0.05)()
        if accepted != 2:
            raise AgentError(
                "empty building-slot mouse click was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        _building_first, building_frame = wait_for_custom_state(
            driver,
            lambda frame: bool(_building_offer_summaries(frame)),
            "building selection",
        )
        visible_offer_count = len(_building_offer_summaries(building_frame))
        selected_slot = "leftmost_standard_empty"
        slot_attempts: list[dict[str, object]] = [
            {
                "slot": selected_slot,
                "center": list(slot_point),
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "visible_construct_offers": visible_offer_count,
                "result_observation_id": building_frame.observation_id,
            }
        ]
        actions.append(
            {
                "control_id": "holding_view.leftmost_standard_empty_building_slot",
                "status": "confirmed",
                "input_kind": "visible_layout_click",
                "click_point": list(slot_point),
                "source_observation_id": fresh_holding.observation_id,
                "send_input": slot_attempts[0]["send_input"],
                "result_observation_id": building_frame.observation_id,
                "expected_post_screen": "building_selection",
                "visible_construct_offers": visible_offer_count,
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": "holding_view.leftmost_standard_empty_building_slot",
                "result_screen": "building_selection",
                "result_observation_id": building_frame.observation_id,
            },
        )

        offer = _choose_economic_building_offer(building_frame)
        button_center = tuple(offer["button_center"])

        def construction_started(frame: object) -> bool:
            return _building_construction_in_progress(frame)

        button_candidates = [
            item
            for item in _spans_with_text(building_frame, "修建")
            if abs(item.center[0] - button_center[0]) <= 20
            and abs(item.center[1] - button_center[1]) <= 20
        ]
        if len(button_candidates) != 1:
            raise AgentError("selected economic building button is not unique")
        # Narrow the region around the selected visible button so the final
        # click is derived from OCR rather than from a frozen coordinate.
        width = window.client_rect[2] - window.client_rect[0]
        height = window.client_rect[3] - window.client_rect[1]
        click_region = (
            max(0.0, (button_center[0] - 40) / width),
            max(0.0, (button_center[1] - 30) / height),
            min(1.0, (button_center[0] + 40) / width),
            min(1.0, (button_center[1] + 30) / height),
        )
        _started_first, started_second = click_visible_text_once(
            driver,
            building_frame,
            text="修建",
            region=click_region,
            control_id="building_selection.construct_economic_offer",
            expected_post_screen="building_construction_started",
            post_predicate=construction_started,
        )

        final_observation = None
        for close_index in range(1, 4):
            window.require_foreground()
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": f"building_view.close_{close_index}",
                    "key": "escape",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                    "expected_post_screen": "map_hud",
                },
            )
            accepted, last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if accepted != 2:
                raise AgentError(
                    f"escape after construction was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )
            try:
                stable_map = driver.observe_stable(
                    "map_hud",
                    min(4.0, _remaining(deadline, "map after construction")),
                    stable_frames=2,
                )
            except AgentError:
                continue
            final_observation = stable_map.to_policy_json()
            actions.append(
                {
                    "control_id": f"building_view.close_{close_index}",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "escape",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                    "send_input": {
                        "requested": 2,
                        "accepted": accepted,
                        "last_error": last_error,
                    },
                    "result_observation_id": stable_map.observation_id,
                    "expected_post_screen": "map_hud",
                }
            )
            break
        if final_observation is None:
            raise AgentError("construction view did not close back to the map")

        return (
            {
                "holding": "阿普利亚伯爵领",
                "holding_source_observation_id": holding_second.observation_id,
                "building_slot": selected_slot,
                "slot_attempts": slot_attempts,
                "selected_offer": offer,
                "construction_observation_id": started_second.observation_id,
                "strategy": "first-affordable-visible-economic-building-v1",
                "policy_boundary": "player-visible OCR only",
            },
            final_observation,
        )

    def review_palermo_war_target() -> dict[str, object]:
        driver = new_driver()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "map before Palermo target review"),
            ),
            stable_frames=2,
        )
        candidates = _palermo_map_targets(source.latest)
        issued_point = (
            min(
                candidates,
                key=lambda candidate: (
                    (candidate[0] - PALERMO_VISIBLE_LABEL_FALLBACK[0]) ** 2
                    + (candidate[1] - PALERMO_VISIBLE_LABEL_FALLBACK[1]) ** 2
                ),
            )
            if candidates
            else PALERMO_VISIBLE_LABEL_FALLBACK
        )
        target_source = "visible OCR" if candidates else "same-session observed label"
        point = issued_point
        window.require_foreground()
        window.require_unobscured(point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "map_hud.select_palermo_war_target",
                "visible_identity": "Palermo map label",
                "target_source": target_source,
                "center": list(point),
                "expected_post_screen": "palermo_title_selection",
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.moveTo(
            window.client_rect[0] + point[0],
            window.client_rect[1] + point[1],
            duration=0.12,
        )
        time.sleep(0.2)
        window.require_cursor_target(point)
        accepted, last_error = _prepare_left_click_batch(0.05)()
        if accepted != 2:
            raise AgentError(
                "Palermo target selection was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first = driver.capture_once()
        second = driver.capture_once()
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            text = str(getattr(item, "text", "")).strip()
            if text and text not in visible_text:
                visible_text.append(text)
        actions.append(
            {
                "control_id": "map_hud.select_palermo_war_target",
                "status": "confirmed",
                "input_kind": "visible_ocr_click",
                "visible_identity": "Palermo map label",
                "target_source": target_source,
                "click_point": list(point),
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": second.observation_id,
                "expected_post_screen": "palermo_title_selection",
            }
        )
        return {
            "target": "Palermo",
            "ocr_target_point": list(point),
            "target_source": target_source,
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
            "policy_boundary": "reversible visible map selection only",
        }

    def review_palermo_interactions() -> dict[str, object]:
        driver = new_driver()
        source = driver.capture_once()
        if not _spans_with_text(source, "拜莱尔姆谢赫", contains=True):
            review_palermo_war_target()
            source = driver.capture_once()
        if not _spans_with_text(source, "拜莱尔姆谢赫", contains=True):
            raise AgentError("Palermo ruler is not visibly selected")
        portrait_point = (150, 180)
        window.require_foreground()
        window.require_unobscured(portrait_point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "palermo_ruler.open_interactions",
                "button": "right",
                "center": list(portrait_point),
                "expected_post_screen": "palermo_interactions",
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.moveTo(
            window.client_rect[0] + portrait_point[0],
            window.client_rect[1] + portrait_point[1],
            duration=0.12,
        )
        time.sleep(0.2)
        window.require_cursor_target(portrait_point)
        accepted, last_error = _prepare_right_click_batch()()
        if accepted != 2:
            raise AgentError(
                "Palermo interaction right click was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first, second = wait_for_custom_state(
            driver,
            lambda frame: bool(_spans_with_text(frame, "宣战", contains=True)),
            "Palermo interaction menu",
        )
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            text = str(getattr(item, "text", "")).strip()
            if text and text not in visible_text:
                visible_text.append(text)
        actions.append(
            {
                "control_id": "palermo_ruler.open_interactions",
                "status": "confirmed",
                "input_kind": "visible_right_click",
                "visible_identity": "拜莱尔姆谢赫",
                "click_point": list(portrait_point),
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": second.observation_id,
                "expected_post_screen": "palermo_interactions",
            }
        )
        return {
            "target": "拜莱尔姆谢赫，优素福·伊本·阿卜杜拉",
            "declare_war_visible": bool(
                _spans_with_text(second, "宣战", contains=True)
            ),
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
        }

    def review_palermo_declaration() -> dict[str, object]:
        driver = new_driver()
        source = driver.capture_once()
        if not _spans_with_text(source, "宣战", contains=True):
            review_palermo_interactions()
            source = driver.capture_once()
        first, second = click_visible_text_once(
            driver,
            source,
            text="宣战",
            region=(0.12, 0.08, 0.28, 0.22),
            control_id="palermo_interactions.declare_war",
            expected_post_screen="declare_war_window",
            post_predicate=lambda frame: bool(
                _spans_with_text(frame, "选择宣战理由", contains=True)
            ),
        )
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            text = str(getattr(item, "text", "")).strip()
            if text and text not in visible_text:
                visible_text.append(text)
        return {
            "target": "拜莱尔姆谢赫，优素福·伊本·阿卜杜拉",
            "casus_belli_visible": bool(
                _spans_with_text(second, "选择宣战理由", contains=True)
            ),
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
        }

    def review_palermo_county_holy_war() -> dict[str, object]:
        driver = new_driver()
        source = driver.capture_once()
        if not _spans_with_text(source, "选择宣战理由", contains=True):
            review_palermo_declaration()
            source = driver.capture_once()
        first, second = click_visible_text_once(
            driver,
            source,
            text="伯爵领圣战",
            region=(0.55, 0.27, 0.80, 0.47),
            control_id="declare_war.select_county_holy_war",
            expected_post_screen="declare_war_target_selection",
            post_predicate=lambda frame: bool(
                _spans_with_text(frame, "选择一个目标", contains=True)
            ),
        )
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            text = str(getattr(item, "text", "")).strip()
            if text and text not in visible_text:
                visible_text.append(text)
        return {
            "target_ruler": "拜莱尔姆谢赫，优素福·伊本·阿卜杜拉",
            "casus_belli": "伯爵领圣战",
            "target_selection_visible": bool(
                _spans_with_text(second, "选择一个目标", contains=True)
            ),
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
        }

    def select_palermo_war_goal() -> dict[str, object]:
        driver = new_driver()
        source = driver.capture_once()
        if not _spans_with_text(source, "选择一个目标", contains=True):
            review_palermo_county_holy_war()
            source = driver.capture_once()
        matches = _spans_with_text(
            source,
            "拜莱尔姆谢赫国",
            region=(0.55, 0.27, 0.80, 0.39),
        )
        target = matches[0] if len(matches) == 1 else None
        point = (
            tuple(target.center)
            if target is not None
            else PALERMO_HOLY_WAR_GOAL_FALLBACK
        )
        target_text = target.text if target is not None else "拜莱尔姆谢赫国"
        target_source = "visible OCR" if target is not None else "same-page observed row"
        window.require_foreground()
        window.require_unobscured(point)
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "declare_war.select_palermo_goal",
                "visible_text": target_text,
                "target_source": target_source,
                "center": list(point),
                "expected_post_screen": "declare_war_ready",
            },
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.moveTo(
            window.client_rect[0] + point[0],
            window.client_rect[1] + point[1],
            duration=0.12,
        )
        time.sleep(0.2)
        window.require_cursor_target(point)
        accepted, last_error = _prepare_left_click_batch(0.05)()
        if accepted != 2:
            raise AgentError(
                "Palermo war-goal selection was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first = driver.capture_once()
        second = driver.capture_once()
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            text = str(getattr(item, "text", "")).strip()
            if text and text not in visible_text:
                visible_text.append(text)
        actions.append(
            {
                "control_id": "declare_war.select_palermo_goal",
                "status": "confirmed",
                "input_kind": "visible_ocr_click",
                "visible_text": target_text,
                "target_source": target_source,
                "click_point": list(point),
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": second.observation_id,
                "expected_post_screen": "declare_war_ready",
            }
        )
        return {
            "target_ruler": "拜莱尔姆谢赫，优素福·伊本·阿卜杜拉",
            "casus_belli": "伯爵领圣战",
            "war_goal": target_text,
            "target_source": target_source,
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
        }

    def declare_palermo_county_holy_war() -> dict[str, object]:
        driver = new_driver()
        source = driver.capture_once()
        final_buttons = _spans_with_text(
            source,
            "宣战",
            region=(0.75, 0.82, 0.90, 0.95),
        )
        if len(final_buttons) != 1:
            select_palermo_war_goal()
            source = driver.capture_once()
        if not _spans_with_text(
            source,
            "伯爵领圣战",
            region=(0.55, 0.25, 0.82, 0.72),
        ):
            raise AgentError("Palermo county holy-war reason is not visible")
        if not _spans_with_text(
            source,
            "拜莱尔姆谢赫国",
            region=(0.55, 0.27, 0.82, 0.60),
        ):
            raise AgentError("Palermo county war goal is not visible")

        _map_first, map_second = click_visible_text_once(
            driver,
            source,
            text="宣战",
            region=(0.75, 0.82, 0.90, 0.95),
            control_id="declare_war.confirm_palermo_county_holy_war",
            expected_post_screen="map_after_war_declaration",
            post_predicate=lambda frame: getattr(frame, "screen", None)
            in {"map_hud", "map_running"},
        )

        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "map_hud.open_war_overview",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "expected_post_screen": "war_overview",
            },
        )
        overview_accepted, overview_last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_alt"],
            CK3_SHORTCUT_SCAN_CODES["w"],
        )()
        if overview_accepted != 4:
            raise AgentError(
                "alt+w war overview shortcut was partial: "
                f"accepted={overview_accepted}, last_error={overview_last_error}"
            )
        overview_first, overview_second = wait_for_custom_state(
            driver,
            _war_overview_visible,
            "Palermo war overview",
        )
        visible_text: list[str] = []
        for item in getattr(overview_second, "spans", ()):
            value = str(getattr(item, "text", "")).strip()
            if value and value not in visible_text:
                visible_text.append(value)
        actions.append(
            {
                "control_id": "map_hud.open_war_overview",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "send_input": {
                    "requested": 4,
                    "accepted": overview_accepted,
                    "last_error": overview_last_error,
                },
                "source_observation_id": map_second.observation_id,
                "result_observation_id": overview_second.observation_id,
                "expected_post_screen": "war_overview",
            }
        )

        window.require_foreground()
        close_accepted, close_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["escape"]
        )()
        if close_accepted != 2:
            raise AgentError(
                "escape war overview close was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        _closed_first, closed_second = wait_for_custom_state(
            driver,
            lambda frame: getattr(frame, "screen", None)
            in {"map_hud", "map_running"},
            "map after Palermo war overview",
        )
        actions.append(
            {
                "control_id": "war_overview.close",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "escape",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                "send_input": {
                    "requested": 2,
                    "accepted": close_accepted,
                    "last_error": close_last_error,
                },
                "source_observation_id": overview_second.observation_id,
                "result_observation_id": closed_second.observation_id,
                "expected_post_screen": "map_hud",
            }
        )
        if getattr(closed_second, "screen", None) == "map_running":
            paused = press_shortcut(
                "map_running",
                "map_running.pause_after_war_declaration",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused map after Palermo war declaration",
                driver=driver,
                stable=closed_second,
                require_visible_control=False,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            final_map_observation_id = paused["observation_id"]
        else:
            final_map_observation_id = closed_second.observation_id
        checkpoint, checkpoint_frame = save_development_checkpoint()
        return {
            "target_ruler": "拜莱尔姆谢赫，优素福·伊本·阿卜杜拉",
            "casus_belli": "伯爵领圣战",
            "war_goal": "拜莱尔姆谢赫国",
            "declared": True,
            "war_overview_frame_observation_ids": [
                overview_first.observation_id,
                overview_second.observation_id,
            ],
            "war_overview_visible_text": visible_text,
            "checkpoint": checkpoint,
            "pre_checkpoint_observation_id": final_map_observation_id,
            "final_observation_id": checkpoint_frame["observation_id"],
        }

    def raise_all_war_armies() -> dict[str, object]:
        driver = new_driver()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "map before raising all armies"),
            ),
            stable_frames=2,
        )
        raise_region = (0.40, 0.92, 0.60, 1.00)
        if len(
            _spans_with_text(
                source.latest,
                "集结所有军队",
                region=raise_region,
            )
        ) != 1:
            raise AgentError("map lacks one visible raise-all-armies button")
        first, second = click_visible_text_once(
            driver,
            source.latest,
            text="集结所有军队",
            region=raise_region,
            control_id="war.raise_all_armies",
            expected_post_screen="armies_raised",
            post_predicate=lambda frame: not _spans_with_text(
                frame,
                "集结所有军队",
                region=raise_region,
            ),
        )
        visible_text: list[str] = []
        for item in getattr(second, "spans", ()):
            value = str(getattr(item, "text", "")).strip()
            if value and value not in visible_text:
                visible_text.append(value)
        return {
            "raised_all": True,
            "source_observation_id": source.observation_id,
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
            "final_observation_id": second.observation_id,
        }

    def move_selected_army_to_palermo_fort() -> dict[str, object]:
        driver = new_driver()
        _initial = driver.capture_once()
        latest = driver.capture_once()
        if _spans_with_text(latest, "相邻统治者", contains=True):
            window.require_foreground()
            close_accepted, close_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if close_accepted != 2:
                raise AgentError(
                    "character panel close before siege was partial: "
                    f"accepted={close_accepted}, last_error={close_last_error}"
                )
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "selected army before Palermo siege"),
            ),
            stable_frames=2,
        )
        import pyautogui

        pyautogui.FAILSAFE = True
        if not _spans_with_text(source.latest, "阿普利亚第1军", contains=True):
            window.require_foreground()
            outliner_accepted, outliner_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["q"]
            )()
            if outliner_accepted != 2:
                raise AgentError(
                    "army outliner shortcut was partial: "
                    f"accepted={outliner_accepted}, last_error={outliner_last_error}"
                )
            _outliner_first, outliner = wait_for_custom_state(
                driver,
                lambda frame: _spans_with_text(
                    frame, "阿普利亚第1军", contains=True
                ),
                "raised army in the CK3 outliner",
            )
            window.require_foreground()
            select_accepted, select_last_error = _prepare_key_chord_batch(
                CK3_SHORTCUT_SCAN_CODES["left_alt"],
                CK3_SHORTCUT_SCAN_CODES["1"],
            )()
            if select_accepted != 4:
                raise AgentError(
                    "first outliner army shortcut was partial: "
                    f"accepted={select_accepted}, last_error={select_last_error}"
                )
            _selected_first, selected = wait_for_custom_state(
                driver,
                lambda frame: _spans_with_text(
                    frame, "阿普利亚第1军", contains=True
                ),
                "selected Apulia first army",
            )
            window.require_foreground()
            close_accepted, close_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["q"]
            )()
            if close_accepted != 2:
                raise AgentError(
                    "army outliner close was partial: "
                    f"accepted={close_accepted}, last_error={close_last_error}"
                )
            source = driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "selected army after outliner close"),
                ),
                stable_frames=2,
            )
            if not _spans_with_text(source.latest, "阿普利亚第1军", contains=True):
                raise AgentError("Apulia first army did not become visibly selected")
        find_palermo_title()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "selected army on the Palermo target map"),
            ),
            stable_frames=2,
        )
        if not _spans_with_text(source.latest, "阿普利亚第1军", contains=True):
            raise AgentError("Palermo title pan did not preserve army selection")
        point = PALERMO_FORT_DESTINATION_FALLBACK
        window.require_foreground()
        window.require_unobscured(point)
        pyautogui.moveTo(
            window.client_rect[0] + point[0],
            window.client_rect[1] + point[1],
            duration=0.12,
        )
        time.sleep(0.35)
        window.require_cursor_target(point)
        hover_first = driver.capture_once()
        hover_second = driver.capture_once()
        hover_text = [
            str(getattr(item, "text", "")).strip()
            for item in getattr(hover_second, "spans", ())
            if str(getattr(item, "text", "")).strip()
        ]
        if not _spans_with_text(hover_second, "莱尔", contains=True):
            raise AgentError(
                "Palermo fort hover did not visibly name the war target: "
                + " | ".join(hover_text[-20:])
            )
        append_event(
            events,
            {
                "kind": "opening_pointer_input_planned",
                "control_id": "war.selected_army.siege_palermo_fort",
                "button": "right",
                "center": list(point),
                "visible_identity": "Palermo fortified holding",
                "expected_post_screen": "army_moving_to_palermo_fort",
            },
        )
        accepted, last_error = _prepare_right_click_batch()()
        if accepted != 2:
            raise AgentError(
                "Palermo fort march was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first = driver.capture_once()
        second = driver.capture_once()
        if getattr(second, "screen", None) not in {"map_hud", "map_running"}:
            raise AgentError("Palermo fort march did not remain on the campaign map")
        actions.append(
            {
                "control_id": "war.selected_army.siege_palermo_fort",
                "status": "confirmed",
                "input_kind": "visible_right_click",
                "visible_identity": "Palermo fortified holding",
                "click_point": list(point),
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "source_observation_id": source.observation_id,
                "hover_observation_ids": [
                    hover_first.observation_id,
                    hover_second.observation_id,
                ],
                "result_observation_id": second.observation_id,
                "expected_post_screen": "army_moving_to_palermo_fort",
            }
        )
        return {
            "destination": "Palermo fortified holding",
            "army": "阿普利亚第1军",
            "click_point": list(point),
            "hover_visible_text": hover_text,
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "final_observation_id": second.observation_id,
        }

    def review_current_war_map() -> dict[str, object]:
        """Close a character overlay, if present, and archive the untouched war map."""
        driver = new_driver()
        _initial = driver.capture_once()
        latest = driver.capture_once()
        overlay_closed = False
        if _spans_with_text(latest, "相邻统治者", contains=True):
            window.require_foreground()
            accepted, last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if accepted != 2:
                raise AgentError(
                    "character panel close before map review was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )
            overlay_closed = True
            _first, latest = wait_for_custom_state(
                driver,
                lambda frame: (
                    getattr(frame, "screen", None) == "map_hud"
                    and not _spans_with_text(frame, "相邻统治者", contains=True)
                ),
                "unobstructed current war map",
            )
        elif getattr(latest, "screen", None) != "map_hud":
            raise AgentError(
                "current UI is neither the campaign map nor a closable character panel"
            )
        # Clear any stale province/character tooltip without clicking so the
        # current army banner remains visible in the archived map frame.
        import pyautogui

        pyautogui.FAILSAFE = True
        neutral_point = (2450, 1360)
        window.require_foreground()
        pyautogui.moveTo(
            window.client_rect[0] + neutral_point[0],
            window.client_rect[1] + neutral_point[1],
            duration=0.12,
        )
        time.sleep(0.5)
        window.require_cursor_target(neutral_point)
        _clear_first = driver.capture_once()
        latest = driver.capture_once()
        visible_text: list[str] = []
        for item in getattr(latest, "spans", ()):
            value = str(getattr(item, "text", "")).strip()
            if value and value not in visible_text:
                visible_text.append(value)
        return {
            "overlay_closed": overlay_closed,
            "visible_text": visible_text,
            "final_observation_id": latest.observation_id,
        }

    def find_palermo_title() -> dict[str, object]:
        """Use CK3's native title finder to pan to Palermo without map guesses."""
        driver = new_driver()
        _current_first = driver.capture_once()
        current = driver.capture_once()
        if _title_finder_visible(current):
            finder = current
            source_observation_id = current.observation_id
        else:
            source = driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "map before Palermo title search"),
                ),
                stable_frames=2,
            )
            source_observation_id = source.observation_id
            window.require_foreground()
            finder_accepted, finder_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["v"]
            )()
            if finder_accepted != 2:
                raise AgentError(
                    "title finder shortcut was partial: "
                    f"accepted={finder_accepted}, last_error={finder_last_error}"
                )
            _finder_first, finder = wait_for_custom_state(
                driver,
                _title_finder_visible,
                "CK3 title finder",
            )

        if _spans_with_text(finder, "拜莱尔姆", contains=True):
            result = finder
        else:
            import pyperclip

            prior_clipboard = pyperclip.paste()
            try:
                pyperclip.copy("拜莱尔姆")
                window.require_foreground()
                paste_accepted, paste_last_error = _prepare_key_chord_batch(
                    CK3_SHORTCUT_SCAN_CODES["left_ctrl"],
                    CK3_SHORTCUT_SCAN_CODES["v"],
                )()
                if paste_accepted != 4:
                    raise AgentError(
                        "Palermo title search paste was partial: "
                        f"accepted={paste_accepted}, last_error={paste_last_error}"
                    )
                _result_first, result = wait_for_custom_state(
                    driver,
                    lambda frame: bool(
                        _title_finder_visible(frame)
                        and _spans_with_text(frame, "拜莱尔姆", contains=True)
                    ),
                    "Palermo title search result",
                )
            finally:
                pyperclip.copy(prior_clipboard)
        matches = _spans_with_text(result, "拜莱尔姆", contains=True)
        visible_results = list(dict.fromkeys(item.text for item in matches))
        target_matches = _spans_with_text(
            result,
            "拜莱尔姆谢赫国",
            contains=True,
            region=(0.76, 0.24, 0.88, 0.29),
        )
        title_panel_matches = _spans_with_text(
            result,
            "拜莱尔姆谢赫国",
            contains=True,
            region=(0.0, 0.0, 0.30, 0.08),
        )
        already_panned = len(target_matches) == 0 and len(title_panel_matches) == 1
        if len(target_matches) != 1 and not already_panned:
            raise AgentError(
                "title finder lacks one visible Palermo realm result: "
                f"{len(target_matches)}"
            )
        point = tuple(target_matches[0].center) if target_matches else None
        if point is not None:
            window.require_foreground()
            window.require_unobscured(point)
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.moveTo(
                window.client_rect[0] + point[0],
                window.client_rect[1] + point[1],
                duration=0.12,
            )
            time.sleep(0.2)
            window.require_cursor_target(point)
            pan_accepted, pan_last_error = _prepare_right_click_batch()()
            if pan_accepted != 2:
                raise AgentError(
                    "Palermo title finder pan was partial: "
                    f"accepted={pan_accepted}, last_error={pan_last_error}"
                )
            _panned_first = driver.capture_once()
            panned = driver.capture_once()
        else:
            panned = result
        if _title_finder_visible(panned):
            # Escape first dismisses an active IME composition, if any, and
            # the following press closes the title finder itself.
            for _attempt in range(3):
                window.require_foreground()
                close_finder_accepted, close_finder_last_error = (
                    _prepare_key_press_batch(CK3_SHORTCUT_SCAN_CODES["escape"])()
                )
                if close_finder_accepted != 2:
                    raise AgentError(
                        "title finder close was partial: "
                        f"accepted={close_finder_accepted}, "
                        f"last_error={close_finder_last_error}"
                    )
                _closed_first = driver.capture_once()
                panned = driver.capture_once()
                if not _title_finder_visible(panned):
                    break
            else:
                raise AgentError("title finder did not close after Palermo pan")
        if _spans_with_text(panned, "头衔历史", contains=True):
            window.require_foreground()
            panel_accepted, panel_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if panel_accepted != 2:
                raise AgentError(
                    "Palermo title panel close was partial: "
                    f"accepted={panel_accepted}, last_error={panel_last_error}"
                )
        _map_first, final = wait_for_custom_state(
            driver,
            lambda frame: bool(
                getattr(frame, "screen", None) == "map_hud"
                and not _title_finder_visible(frame)
                and not _spans_with_text(frame, "头衔历史", contains=True)
            ),
            "map centered on Palermo",
        )
        actions.append(
            {
                "control_id": "map_hud.find_palermo_title",
                "status": "confirmed",
                "input_kind": "keyboard_shortcuts",
                "keys": ["v", "ctrl+v"],
                "right_click_point": list(point) if point is not None else None,
                "already_panned": already_panned,
                "visible_identity": "拜莱尔姆",
                "source_observation_id": source_observation_id,
                "finder_observation_id": finder.observation_id,
                "result_observation_id": final.observation_id,
            }
        )
        return {
            "query": "拜莱尔姆",
            "visible_results": visible_results,
            "result_observation_id": result.observation_id,
            "final_observation_id": final.observation_id,
        }

    def advance_war_days(target_days: int, speed: str) -> dict[str, object]:
        if target_days not in {7, 30} or speed not in {"3", "4"}:
            raise AgentError("war time advance request is unsupported")
        driver = new_driver()
        paused = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "paused campaign map before war advance"),
            ),
            stable_frames=2,
        )
        starting_date = _extract_map_date(paused.to_policy_json())
        press_shortcut(
            "map_hud",
            f"map_hud.set_speed_{speed}_for_war",
            speed,
            CK3_SHORTCUT_SCAN_CODES[speed],
            "map_hud",
            f"war speed {speed}",
            driver=driver,
            stable=paused,
            require_visible_control=False,
            post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        )
        running = press_shortcut(
            "map_hud",
            "map_hud.resume_war_advance",
            "space",
            CK3_SHORTCUT_SCAN_CODES["space"],
            "map_running",
            "running war advance",
            require_visible_control=False,
            post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        )
        progress_driver = new_driver()
        progress_deadline = min(deadline, time.monotonic() + 60.0)
        last_frame = None
        ending_date = None
        while time.monotonic() < progress_deadline:
            frame = progress_driver.capture_once()
            event = _generic_event_in_frame(frame)
            if event is not None:
                raise AgentError(
                    "ordinary event interrupted war advance; resolve it before continuing"
                )
            if getattr(frame, "screen", None) not in {"map_hud", "map_running"}:
                last_frame = frame
                continue
            try:
                observed_date = _extract_map_date(frame.to_policy_json())
            except AgentError:
                last_frame = frame
                continue
            last_frame = frame
            if (
                int(observed_date["ordinal"]) - int(starting_date["ordinal"])
                >= target_days
            ):
                ending_date = observed_date
                break
        if last_frame is None or ending_date is None:
            raise AgentError(
                f"war timeline did not visibly advance {target_days} days"
            )
        if getattr(last_frame, "screen", None) == "map_running":
            final = press_shortcut(
                "map_running",
                "map_running.pause_after_war_advance",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused after war advance",
                driver=progress_driver,
                stable=last_frame,
                require_visible_control=False,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
        else:
            final = last_frame.to_policy_json()
        return {
            "starting_date": starting_date,
            "ending_date": ending_date,
            "requested_days": target_days,
            "speed": int(speed),
            "elapsed_days": int(ending_date["ordinal"])
            - int(starting_date["ordinal"]),
            "running_observation_id": running["observation_id"],
            "final_screen": final["screen"],
            "final_observation_id": final["observation_id"],
            "visible_text": [
                item["text"]
                for item in final.get("ocr", [])
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ],
        }

    def advance_war_one_week() -> dict[str, object]:
        return advance_war_days(7, "3")

    def advance_war_one_month() -> dict[str, object]:
        return advance_war_days(30, "4")

    def inspect_active_war_status() -> dict[str, object]:
        driver = new_driver()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "campaign map before war overview"),
            ),
            stable_frames=2,
        )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "map_hud.inspect_active_war",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "expected_post_screen": "war_overview",
            },
        )
        accepted, last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_alt"],
            CK3_SHORTCUT_SCAN_CODES["w"],
        )()
        if accepted != 4:
            raise AgentError(
                "alt+w war status shortcut was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        first, second = wait_for_custom_state(
            driver,
            _war_overview_visible,
            "active war overview",
        )
        visible_text: list[str] = []
        war_score = None
        for item in getattr(second, "spans", ()):
            value = str(getattr(item, "text", "")).strip()
            if value and value not in visible_text:
                visible_text.append(value)
            match = re.search(r"战争分数\s*([+-]?\d+)\s*%", value)
            if match is not None:
                war_score = int(match.group(1))
        window.require_foreground()
        close_accepted, close_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["escape"]
        )()
        if close_accepted != 2:
            raise AgentError(
                "war status close was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        _map_first, map_second = wait_for_custom_state(
            driver,
            lambda frame: getattr(frame, "screen", None) == "map_hud",
            "paused campaign map after war overview",
        )
        actions.append(
            {
                "control_id": "map_hud.inspect_active_war",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "send_input": {
                    "requested": 4,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": second.observation_id,
                "expected_post_screen": "war_overview",
            }
        )
        return {
            "war_score_percent": war_score,
            "frame_observation_ids": [
                first.observation_id,
                second.observation_id,
            ],
            "visible_text": visible_text,
            "final_observation_id": map_second.observation_id,
        }

    def enforce_active_war_demands() -> dict[str, object]:
        driver = new_driver()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "campaign map before enforcing war demands"),
            ),
            stable_frames=2,
        )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "map_hud.open_war_for_victory",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "expected_post_screen": "war_overview",
            },
        )
        open_accepted, open_last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_alt"],
            CK3_SHORTCUT_SCAN_CODES["w"],
        )()
        if open_accepted != 4:
            raise AgentError(
                "alt+w victory shortcut was partial: "
                f"accepted={open_accepted}, last_error={open_last_error}"
            )
        _overview_first, overview = wait_for_custom_state(
            driver,
            _war_overview_visible,
            "100-percent war overview",
        )
        score_matches: list[int] = []
        for item in getattr(overview, "spans", ()):
            match = re.search(
                r"战争分数\s*([+-]?\d+)\s*%",
                str(getattr(item, "text", "")),
            )
            if match is not None:
                score_matches.append(int(match.group(1)))
        if score_matches != [100]:
            raise AgentError(
                f"war demands require one visible +100% score: {score_matches!r}"
            )
        actions.append(
            {
                "control_id": "map_hud.open_war_for_victory",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "alt+w",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["w"],
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_alt"],
                "send_input": {
                    "requested": 4,
                    "accepted": open_accepted,
                    "last_error": open_last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": overview.observation_id,
                "expected_post_screen": "war_overview",
            }
        )

        terms = overview
        send_region = (0.42, 0.88, 0.58, 0.96)
        if len(_spans_with_text(terms, "强制执行要求", region=send_region)) != 1:
            _terms_first, terms = click_visible_text_once(
                driver,
                terms,
                text="强制执行要求",
                region=(0.54, 0.96, 0.68, 1.0),
                control_id="war_overview.open_victory_terms",
                expected_post_screen="war_victory_terms",
                post_predicate=lambda frame: bool(
                    _war_overview_visible(frame)
                    and len(
                        _spans_with_text(
                            frame, "强制执行要求", region=send_region
                        )
                    )
                    == 1
                ),
            )
        else:
            actions.append(
                {
                    "control_id": "war_overview.select_victory_terms",
                    "status": "already_selected",
                    "input_kind": "visible_state_verification",
                    "source_observation_id": overview.observation_id,
                    "result_observation_id": overview.observation_id,
                    "expected_post_screen": "war_victory_terms",
                }
            )
        _result_first, result = click_visible_text_once(
            driver,
            terms,
            text="强制执行要求",
            region=send_region,
            control_id="war_victory_terms.enforce_demands",
            expected_post_screen="war_results_victory",
            post_predicate=_war_results_victory_visible,
        )
        _map_first, final = click_visible_text_once(
            driver,
            result,
            text="就这样吧",
            region=(0.25, 0.62, 0.75, 0.92),
            control_id="war_results.dismiss_victory",
            expected_post_screen="map_hud",
            post_predicate=lambda frame: bool(
                getattr(frame, "screen", None) == "map_hud"
                and not _war_results_victory_visible(frame)
            ),
        )
        final_policy = final.to_policy_json()
        return {
            "status": "victory_enforced",
            "war_score_percent": 100,
            "victory_terms_observation_id": terms.observation_id,
            "war_results_observation_id": result.observation_id,
            "final_observation_id": final.observation_id,
            "ending_date": _extract_map_date(final_policy),
            "strategy": "native-war-tab-plus-visible-send-v1",
        }

    def disband_war_armies() -> dict[str, object]:
        driver = new_driver()

        def armies_absent(frame: object) -> bool:
            return bool(
                getattr(frame, "screen", None) == "map_hud"
                and not _spans_with_text(frame, "全部解散")
                and not _spans_with_text(
                    frame, "阿普利亚第1军", contains=True
                )
                and not _army_disband_confirmation_visible(frame)
            )

        def confirm_disband(frame: object) -> object:
            _confirmed_first, confirmed = click_visible_text_once(
                driver,
                frame,
                text="解散",
                region=(0.50, 0.48, 0.62, 0.61),
                control_id="army_disband_confirmation.confirm",
                expected_post_screen="map_hud_without_raised_armies",
                post_predicate=armies_absent,
            )
            return confirmed

        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "campaign map before army disband"),
            ),
            stable_frames=2,
        )
        if _army_disband_confirmation_visible(source.latest):
            final = confirm_disband(source.latest)
            return {
                "status": "disbanded",
                "army": "阿普利亚第1军",
                "confirmation_resumed": True,
                "final_observation_id": final.observation_id,
                "strategy": "native-outliner-army-shortcut-v1",
            }
        if not _spans_with_text(source.latest, "全部解散"):
            return {
                "status": "already_disbanded",
                "final_observation_id": source.observation_id,
                "strategy": "native-outliner-army-shortcut-v1",
            }
        window.require_foreground()
        outliner_accepted, outliner_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["q"]
        )()
        if outliner_accepted != 2:
            raise AgentError(
                "army outliner shortcut before disband was partial: "
                f"accepted={outliner_accepted}, last_error={outliner_last_error}"
            )
        _outliner_first, outliner = wait_for_custom_state(
            driver,
            lambda frame: bool(
                _spans_with_text(frame, "阿普利亚第1军", contains=True)
            ),
            "raised army in outliner before disband",
        )
        window.require_foreground()
        select_accepted, select_last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_alt"],
            CK3_SHORTCUT_SCAN_CODES["1"],
        )()
        if select_accepted != 4:
            raise AgentError(
                "first outliner army selection before disband was partial: "
                f"accepted={select_accepted}, last_error={select_last_error}"
            )
        _selected_first, selected = wait_for_custom_state(
            driver,
            lambda frame: bool(
                _spans_with_text(frame, "阿普利亚第1军", contains=True)
            ),
            "selected army before disband",
        )
        window.require_foreground()
        close_accepted, close_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["q"]
        )()
        if close_accepted != 2:
            raise AgentError(
                "army outliner close before disband was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        _map_first, selected_map = wait_for_custom_state(
            driver,
            lambda frame: bool(
                getattr(frame, "screen", None) == "map_hud"
                and _spans_with_text(frame, "阿普利亚第1军", contains=True)
            ),
            "selected army on map before disband",
        )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "selected_army.disband",
                "key": "j",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["j"],
                "expected_post_screen": "map_hud_without_raised_armies",
            },
        )
        disband_accepted, disband_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["j"]
        )()
        if disband_accepted != 2:
            raise AgentError(
                "army J disband shortcut was partial: "
                f"accepted={disband_accepted}, last_error={disband_last_error}"
            )
        _transition_first, transition = wait_for_custom_state(
            driver,
            lambda frame: bool(
                armies_absent(frame)
                or _army_disband_confirmation_visible(frame)
            ),
            "army disband result or confirmation",
        )
        final = (
            confirm_disband(transition)
            if _army_disband_confirmation_visible(transition)
            else transition
        )
        actions.append(
            {
                "control_id": "selected_army.disband",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "j",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["j"],
                "send_input": {
                    "requested": 2,
                    "accepted": disband_accepted,
                    "last_error": disband_last_error,
                },
                "source_observation_id": selected_map.observation_id,
                "result_observation_id": final.observation_id,
                "expected_post_screen": "map_hud_without_raised_armies",
            }
        )
        return {
            "status": "disbanded",
            "army": "阿普利亚第1军",
            "outliner_observation_id": outliner.observation_id,
            "selected_observation_id": selected.observation_id,
            "final_observation_id": final.observation_id,
            "strategy": "native-outliner-army-shortcut-v1",
        }

    def save_development_checkpoint() -> tuple[
        dict[str, object], dict[str, object]
    ]:
        save_root = spec.profile_dir / "save games"
        save_root.mkdir(parents=True, exist_ok=True)
        before = {
            path.name: (path.stat().st_size, path.stat().st_mtime_ns)
            for path in save_root.glob("*.ck3")
            if path.is_file()
        }
        driver = new_driver()
        source = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "map before development checkpoint"),
            ),
            stable_frames=2,
        )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "map_hud.open_pause_menu",
                "key": "escape",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                "expected_post_screen": "pause_menu",
            },
        )
        menu_accepted, menu_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["escape"]
        )()
        if menu_accepted != 2:
            raise AgentError(
                "pause-menu shortcut was partial: "
                f"accepted={menu_accepted}, last_error={menu_last_error}"
            )
        _menu_first, pause_menu = wait_for_custom_state(
            driver,
            _pause_menu_visible,
            "pause menu",
        )
        actions.append(
            {
                "control_id": "map_hud.open_pause_menu",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "escape",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                "send_input": {
                    "requested": 2,
                    "accepted": menu_accepted,
                    "last_error": menu_last_error,
                },
                "source_observation_id": source.observation_id,
                "result_observation_id": pause_menu.observation_id,
                "expected_post_screen": "pause_menu",
            }
        )

        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "pause_menu.save_game",
                "key": "1",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["1"],
                "expected_post_screen": "save_window",
            },
        )
        save_menu_accepted, save_menu_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["1"]
        )()
        if save_menu_accepted != 2:
            raise AgentError(
                "pause-menu save shortcut was partial: "
                f"accepted={save_menu_accepted}, last_error={save_menu_last_error}"
            )
        _save_first, save_window = wait_for_custom_state(
            driver,
            _save_window_visible,
            "save window",
        )
        actions.append(
            {
                "control_id": "pause_menu.save_game",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "1",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["1"],
                "send_input": {
                    "requested": 2,
                    "accepted": save_menu_accepted,
                    "last_error": save_menu_last_error,
                },
                "source_observation_id": pause_menu.observation_id,
                "result_observation_id": save_window.observation_id,
                "expected_post_screen": "save_window",
            }
        )

        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "save_window.accept_default_name",
                "key": "enter",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                "expected_post_screen": "pause_menu_or_overwrite_confirmation",
            },
        )
        save_accepted, save_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["enter"]
        )()
        if save_accepted != 2:
            raise AgentError(
                "save confirmation shortcut was partial: "
                f"accepted={save_accepted}, last_error={save_last_error}"
            )
        _transition_first, transition = wait_for_custom_state(
            driver,
            lambda frame: bool(
                _pause_menu_visible(frame)
                or _overwrite_save_confirmation_visible(frame)
            ),
            "save completion or overwrite confirmation",
        )
        overwrite_confirmed = False
        if _overwrite_save_confirmation_visible(transition):
            overwrite_confirmed = True
            window.require_foreground()
            overwrite_accepted, overwrite_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["enter"]
            )()
            if overwrite_accepted != 2:
                raise AgentError(
                    "overwrite confirmation shortcut was partial: "
                    f"accepted={overwrite_accepted}, last_error={overwrite_last_error}"
                )
            _pause_first, transition = wait_for_custom_state(
                driver,
                _pause_menu_visible,
                "pause menu after save overwrite",
            )
        actions.append(
            {
                "control_id": "save_window.accept_default_name",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "key": "enter",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                "send_input": {
                    "requested": 2,
                    "accepted": save_accepted,
                    "last_error": save_last_error,
                },
                "overwrite_confirmed": overwrite_confirmed,
                "source_observation_id": save_window.observation_id,
                "result_observation_id": transition.observation_id,
                "expected_post_screen": "pause_menu",
            }
        )

        changed: list[Path] = []
        save_deadline = min(deadline, time.monotonic() + 30.0)
        prior_signature = None
        while time.monotonic() < save_deadline:
            changed = []
            for path in save_root.glob("*.ck3"):
                if not path.is_file():
                    continue
                current = (path.stat().st_size, path.stat().st_mtime_ns)
                if before.get(path.name) != current:
                    changed.append(path)
            signature = tuple(
                sorted(
                    (path.name, path.stat().st_size, path.stat().st_mtime_ns)
                    for path in changed
                )
            )
            if signature and signature == prior_signature:
                break
            prior_signature = signature
            time.sleep(0.25)
        else:
            raise AgentError("development checkpoint file did not become stable")
        checkpoint = max(changed, key=lambda path: path.stat().st_mtime_ns)

        window.require_foreground()
        close_accepted, close_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["escape"]
        )()
        if close_accepted != 2:
            raise AgentError(
                "pause-menu close after save was partial: "
                f"accepted={close_accepted}, last_error={close_last_error}"
            )
        final_map = driver.observe_stable(
            "map_hud",
            min(
                INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                _remaining(deadline, "map after development checkpoint"),
            ),
            stable_frames=2,
        )
        return (
            {
                "status": "saved",
                "path": str(checkpoint.resolve()),
                "name": checkpoint.name,
                "size": checkpoint.stat().st_size,
                "sha256": sha256_file(checkpoint),
                "overwrite_confirmed": overwrite_confirmed,
                "strategy": "native-pause-menu-default-save-v1",
            },
            final_map.to_policy_json(),
        )

    def restore_latest_development_checkpoint() -> dict[str, object]:
        """Load the newest named checkpoint inside the owned CK3 process."""
        save_root = spec.profile_dir / "save games"
        checkpoints = [
            path
            for path in save_root.glob("*.ck3")
            if path.is_file() and not path.name.casefold().startswith("autosave")
        ]
        if not checkpoints:
            raise AgentError("no named development checkpoint is available")
        checkpoint = max(checkpoints, key=lambda path: path.stat().st_mtime_ns)
        expected_size = checkpoint.stat().st_size
        expected_sha256 = sha256_file(checkpoint)

        driver = new_driver()
        _current_first = driver.capture_once()
        current = driver.capture_once()
        if not _pause_menu_visible(current) and not _load_window_visible(current):
            if (
                _spans_with_text(current, "阿普利亚第1军", contains=True)
                or _spans_with_text(current, "相邻统治者", contains=True)
            ):
                window.require_foreground()
                close_accepted, close_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if close_accepted != 2:
                    raise AgentError(
                        "current map overlay close before restore was partial: "
                        f"accepted={close_accepted}, last_error={close_last_error}"
                    )
                _closed_first, current = wait_for_custom_state(
                    driver,
                    lambda frame: (
                        getattr(frame, "screen", None) == "map_hud"
                        and not _spans_with_text(
                            frame, "阿普利亚第1军", contains=True
                        )
                        and not _spans_with_text(
                            frame, "相邻统治者", contains=True
                        )
                    ),
                    "plain campaign map before checkpoint restore",
                )
            window.require_foreground()
            menu_accepted, menu_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if menu_accepted != 2:
                raise AgentError(
                    "pause menu open before restore was partial: "
                    f"accepted={menu_accepted}, last_error={menu_last_error}"
                )
            _menu_first, current = wait_for_custom_state(
                driver,
                _pause_menu_visible,
                "pause menu before checkpoint restore",
            )
        if _pause_menu_visible(current):
            window.require_foreground()
            load_accepted, load_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["2"]
            )()
            if load_accepted != 2:
                raise AgentError(
                    "pause-menu load shortcut was partial: "
                    f"accepted={load_accepted}, last_error={load_last_error}"
                )
            _load_first, current = wait_for_custom_state(
                driver,
                _load_window_visible,
                "load checkpoint window",
            )
        if not _spans_with_text(current, checkpoint.stem, contains=True):
            raise AgentError(
                f"load window does not visibly contain checkpoint {checkpoint.stem!r}"
            )

        window.require_foreground()
        select_accepted, select_last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_alt"],
            CK3_SHORTCUT_SCAN_CODES["1"],
        )()
        if select_accepted != 4:
            raise AgentError(
                "first save selection shortcut was partial: "
                f"accepted={select_accepted}, last_error={select_last_error}"
            )
        _selected_first, selected = wait_for_custom_state(
            driver,
            lambda frame: bool(
                _load_window_visible(frame)
                and _spans_with_text(frame, checkpoint.stem, contains=True)
            ),
            "selected named checkpoint",
        )
        window.require_foreground()
        confirm_accepted, confirm_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["enter"]
        )()
        if confirm_accepted != 2:
            raise AgentError(
                "checkpoint load confirmation shortcut was partial: "
                f"accepted={confirm_accepted}, last_error={confirm_last_error}"
            )
        _loaded_first, loaded = wait_for_custom_state(
            driver,
            lambda frame: bool(
                getattr(frame, "screen", None) in {"map_hud", "map_running"}
                or _pause_menu_visible(frame)
            ),
            "restored checkpoint state",
            timeout_seconds=min(
                INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
                _remaining(deadline, "checkpoint load"),
            ),
        )
        if _pause_menu_visible(loaded):
            window.require_foreground()
            close_accepted, close_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["escape"]
            )()
            if close_accepted != 2:
                raise AgentError(
                    "pause menu close after checkpoint restore was partial: "
                    f"accepted={close_accepted}, last_error={close_last_error}"
                )
            _map_first, loaded = wait_for_custom_state(
                driver,
                lambda frame: getattr(frame, "screen", None)
                in {"map_hud", "map_running"},
                "map after checkpoint restore",
            )
        if loaded.screen == "map_running":
            final = press_shortcut(
                "map_running",
                "map_running.pause_after_checkpoint_restore",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused restored checkpoint",
                driver=driver,
                stable=SimpleNamespace(
                    screen="map_running", controls=loaded.controls
                ),
                require_visible_control=False,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
        else:
            final = loaded.to_policy_json()
        restored_date = _extract_map_date(final)
        return {
            "status": "restored",
            "process_restarted": False,
            "checkpoint": {
                "name": checkpoint.name,
                "size": expected_size,
                "sha256": expected_sha256,
            },
            "restored_date": restored_date,
            "selection_method": "pause-menu-load-alt-1-enter-v1",
            "source_observation_id": selected.observation_id,
            "final_observation_id": final["observation_id"],
        }

    def run_ordinary_event_loop(
        event_target: int,
        *,
        initial_event: dict[str, object] | None = None,
        wait_timeout_seconds: float = ORDINARY_EVENT_WAIT_TIMEOUT_SECONDS,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        ordinary_events: list[dict[str, object]] = []
        post_driver = None
        post_state = None
        pending_event: dict[str, object] | None = initial_event
        event_index = 0
        while event_index < event_target or pending_event is not None:
            event_index += 1
            if event_index > event_target + MAX_CHAINED_ORDINARY_EVENTS:
                raise AgentError("ordinary CK3 event chain exceeded its bounded depth")
            detected_event = pending_event
            detected_call: dict[str, object] | None = None
            pending_event = None
            if detected_event is None:
                event_deadline = min(
                    deadline,
                    time.monotonic() + wait_timeout_seconds,
                )
                event_driver = new_driver()
                preview_sequence = 0
                while time.monotonic() < event_deadline:
                    preview_sequence += 1
                    generic_preview, call_preview, terminal_preview = (
                        _visible_event_preview(window, preview_sequence)
                    )
                    if terminal_preview is not None:
                        first_frame = event_driver.capture_once()
                        second_frame = event_driver.capture_once()
                        first_terminal = _death_terminal_state(first_frame)
                        second_terminal = _death_terminal_state(second_frame)
                        if (
                            first_terminal is not None
                            and first_terminal == second_terminal
                        ):
                            raise AgentError(
                                "one-life death terminal visible: "
                                f"{second_terminal}"
                            )
                        continue
                    if generic_preview is None and call_preview is None:
                        continue
                    first_frame = event_driver.capture_once()
                    second_frame = event_driver.capture_once()
                    first_call = _call_to_war_in_frame(first_frame)
                    second_call = _call_to_war_in_frame(second_frame)
                    if first_call is not None and second_call is not None:
                        detected_call = second_call
                        break
                    prior_event = _generic_event_in_frame(first_frame)
                    candidate = _generic_event_in_frame(second_frame)
                    if (
                        prior_event is not None
                        and candidate is not None
                        and int(candidate["capture_sequence"])
                        == int(prior_event["capture_sequence"]) + 1
                        and _same_generic_event(prior_event, candidate)
                    ):
                        detected_event = candidate
                        break
                if detected_event is None and detected_call is None:
                    first_frame = event_driver.capture_once()
                    second_frame = event_driver.capture_once()
                    first_terminal = _death_terminal_state(first_frame)
                    second_terminal = _death_terminal_state(second_frame)
                    if (
                        first_terminal is not None
                        and first_terminal == second_terminal
                    ):
                        raise AgentError(
                            "one-life death terminal visible: "
                            f"{second_terminal}"
                        )
                    first_call = _call_to_war_in_frame(first_frame)
                    second_call = _call_to_war_in_frame(second_frame)
                    if first_call is not None and second_call is not None:
                        detected_call = second_call
                    else:
                        prior_event = _generic_event_in_frame(first_frame)
                        candidate = _generic_event_in_frame(second_frame)
                        if (
                            prior_event is not None
                            and candidate is not None
                            and _same_generic_event(prior_event, candidate)
                        ):
                            detected_event = candidate
                    if detected_event is None and detected_call is None:
                        if (
                            first_frame.screen != second_frame.screen
                            or second_frame.screen
                            not in {"map_hud", "map_running"}
                        ):
                            raise AgentError(
                                "bounded event wait ended on an unknown visible state"
                            )
                        if second_frame.screen == "map_running":
                            final = press_shortcut(
                                "map_running",
                                "map_running.pause_after_bounded_wait",
                                "space",
                                CK3_SHORTCUT_SCAN_CODES["space"],
                                "map_hud",
                                "paused after bounded no-event wait",
                                driver=event_driver,
                                stable=second_frame,
                                require_visible_control=False,
                                post_timeout_seconds=(
                                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS
                                ),
                            )
                        else:
                            final = second_frame.to_policy_json()
                        return ordinary_events, final

            if detected_call is not None:
                resolved_call, final = accept_visible_call_to_war(
                    event_driver, detected_call
                )
                ordinary_events.append(
                    {
                        "event_index": event_index,
                        "event_kind": "call_to_war",
                        **resolved_call,
                    }
                )
                if event_index >= event_target:
                    return ordinary_events, final
                post_driver = new_driver()
                post_state = post_driver.observe_stable(
                    "map_hud",
                    min(
                        INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                        _remaining(deadline, "map after alliance call"),
                    ),
                    stable_frames=2,
                )
                press_shortcut(
                    "map_hud",
                    "map_hud.resume_after_alliance_call",
                    "space",
                    CK3_SHORTCUT_SCAN_CODES["space"],
                    "map_running",
                    "running timeline after alliance call",
                    driver=post_driver,
                    stable=post_state,
                    require_visible_control=False,
                    post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )
                continue

            event_options = detected_event["options"]
            selected_event_option, option_score, score_reasons = (
                _choose_generic_event_option(detected_event)
            )
            option_number = int(selected_event_option["option_number"])
            key, scan_code = EVENT_OPTION_SHORTCUTS[option_number]
            control_id = f"ordinary_event.option_{option_number}"
            window.require_foreground()
            speed_accepted, speed_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["1"]
            )()
            if speed_accepted != 2:
                raise AgentError(
                    "ordinary-event speed-one latch was partial: "
                    f"accepted={speed_accepted}, last_error={speed_last_error}"
                )
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": control_id,
                    "event_index": event_index,
                    "key": key,
                    "scan_code": scan_code,
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    "expected_post_screen": "map",
                },
            )
            accepted, last_error = _prepare_key_chord_batch(
                CK3_SHORTCUT_SCAN_CODES["left_shift"], scan_code
            )()
            if accepted != 4:
                raise AgentError(
                    f"{key} ordinary-event shortcut SendInput was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )
            # CK3 applies the option shortcut before it tears down the hard-
            # pause event window.  A Space record submitted in the same input
            # turn is swallowed by that window, so give the UI one bounded
            # non-OCR frame to close while the underlying speed is already 1.
            time.sleep(0.5)
            pause_accepted, pause_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["space"]
            )()
            if pause_accepted != 2:
                raise AgentError(
                    "ordinary-event immediate pause was partial: "
                    f"accepted={pause_accepted}, last_error={pause_last_error}"
                )

            post_driver = new_driver()
            post_state = None
            paused_error: AgentError | None = None
            try:
                post_state = post_driver.observe_stable(
                    "map_hud",
                    min(
                        8.0,
                        _remaining(deadline, "ordinary event paused postcondition"),
                    ),
                    stable_frames=2,
                )
            except AgentError as error:
                paused_error = error
            if post_state is None:
                try:
                    post_state = post_driver.observe_stable(
                        "map_running",
                        min(
                            8.0,
                            _remaining(
                                deadline, "ordinary event running postcondition"
                            ),
                        ),
                        stable_frames=2,
                    )
                except AgentError:
                    if paused_error is not None:
                        raise paused_error
                    raise
            result_observation_id = post_state.observation_id
            result_screen = post_state.screen
            post_candidate = _generic_event_in_frame(post_state.latest)
            if post_candidate is not None:
                pending_event, transition_frame = _confirm_post_shortcut_event(
                    post_driver,
                    post_candidate,
                    min(deadline, time.monotonic() + 8.0),
                )
                result_observation_id = getattr(
                    transition_frame, "observation_id", result_observation_id
                )
                if pending_event is not None:
                    if pending_event.get("title") == detected_event.get("title"):
                        raise AgentError(
                            "ordinary CK3 event remained visible after its shortcut"
                        )
                    result_screen = "ordinary_event"

            actions.append(
                {
                    "control_id": control_id,
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": key,
                    "scan_code": scan_code,
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    "send_input": {
                        "requested": 4,
                        "accepted": accepted,
                        "last_error": last_error,
                    },
                    "speed_one_latch": {
                        "requested": 2,
                        "accepted": speed_accepted,
                        "last_error": speed_last_error,
                    },
                    "immediate_pause": {
                        "requested": 2,
                        "accepted": pause_accepted,
                        "last_error": pause_last_error,
                    },
                    "event_index": event_index,
                    "event_title": detected_event["title"],
                    "visible_option": selected_event_option["visible_text"],
                    "visible_option_count": len(event_options),
                    "strategy_score": option_score,
                    "strategy_reasons": score_reasons,
                    "source_observation_id": detected_event["observation_id"],
                    "result_observation_id": result_observation_id,
                    "expected_post_screen": result_screen,
                }
            )
            append_event(
                events,
                {
                    "kind": "opening_step_completed",
                    "control_id": control_id,
                    "event_index": event_index,
                    "result_screen": result_screen,
                    "result_observation_id": result_observation_id,
                },
            )
            ordinary_events.append(
                {
                    "event_index": event_index,
                    "title": detected_event["title"],
                    "visible_options": event_options,
                    "selected_option_number": option_number,
                    "selected_visible_text": selected_event_option["visible_text"],
                    "strategy_score": option_score,
                    "strategy_reasons": score_reasons,
                    "strategy": "visible-option-utility-v1",
                    "source_observation_id": detected_event["observation_id"],
                }
            )
            if (
                pending_event is None
                and event_index < event_target
                and post_state.screen == "map_hud"
            ):
                press_shortcut(
                    "map_hud",
                    "map_hud.resume",
                    "space",
                    CK3_SHORTCUT_SCAN_CODES["space"],
                    "map_running",
                    f"running timeline after ordinary event {event_index}",
                    driver=post_driver,
                    stable=post_state,
                    post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )

        if post_driver is None or post_state is None:
            raise AgentError("ordinary CK3 event loop produced no final state")
        if post_state.screen == "map_running":
            final_observation = press_shortcut(
                "map_running",
                "map_running.pause",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused after ordinary event loop",
                driver=post_driver,
                stable=post_state,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
        else:
            final_observation = post_state.to_policy_json()
        return ordinary_events, final_observation

    if development_step is not None and development_step not in (
        OPENING_DEVELOPMENT_STEPS
    ):
        raise AgentError(
            f"unsupported opening development step: {development_step}"
        )
    resume_info = None
    if resume_saved_game:
        resume_driver = new_driver()
        main_menu = resume_driver.observe_stable(
            "main_menu",
            min(
                INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
                _remaining(deadline, "main menu before saved-game resume"),
            ),
            stable_frames=2,
        )
        continue_matches = _spans_with_text(
            main_menu.latest,
            "继续游戏",
            region=(0.02, 0.20, 0.42, 0.80),
        )
        if len(continue_matches) != 1:
            raise AgentError(
                "main menu lacks one visible Continue Game shortcut target"
            )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "main_menu.continue_game",
                "key": "enter",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                "expected_post_screen": "saved_map",
            },
        )
        continue_accepted, continue_last_error = _prepare_key_press_batch(
            CK3_SHORTCUT_SCAN_CODES["enter"]
        )()
        if continue_accepted != 2:
            raise AgentError(
                "Continue Game shortcut was partial: "
                f"accepted={continue_accepted}, last_error={continue_last_error}"
            )
        _loaded_first, loaded_map = wait_for_custom_state(
            resume_driver,
            lambda frame: getattr(frame, "screen", None)
            in {"map_hud", "map_running"},
            "saved map",
            timeout_seconds=min(
                INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
                _remaining(deadline, "saved-game load"),
            ),
        )
        actions.append(
            {
                "control_id": "main_menu.continue_game",
                "status": "confirmed",
                "input_kind": "keyboard_shortcut",
                "visible_identity": "继续游戏",
                "key": "enter",
                "scan_code": CK3_SHORTCUT_SCAN_CODES["enter"],
                "send_input": {
                    "requested": 2,
                    "accepted": continue_accepted,
                    "last_error": continue_last_error,
                },
                "result_observation_id": loaded_map.observation_id,
                "expected_post_screen": loaded_map.screen,
            }
        )
        if loaded_map.screen == "map_running":
            paused = press_shortcut(
                "map_running",
                "map_running.pause",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_hud",
                "paused resumed map",
                driver=resume_driver,
                stable=SimpleNamespace(
                    screen="map_running",
                    controls=loaded_map.controls,
                ),
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            resumed_observation_id = paused.get("observation_id")
        else:
            resumed_observation_id = loaded_map.observation_id
        resume_info = {
            "method": "visible-main-menu-continue-shortcut",
            "source_observation_id": main_menu.observation_id,
            "result_observation_id": resumed_observation_id,
        }

    if development_step is not None:
        if development_step == "pause-map":
            pause_driver = new_driver()
            _pause_first, current_map = wait_for_custom_state(
                pause_driver,
                lambda frame: getattr(frame, "screen", None)
                in {"map_hud", "map_running"},
                "current map before idempotent pause",
            )
            if current_map.screen == "map_running":
                final = press_shortcut(
                    "map_running",
                    "map_running.pause_on_request",
                    "space",
                    CK3_SHORTCUT_SCAN_CODES["space"],
                    "map_hud",
                    "paused map on request",
                    driver=pause_driver,
                    stable=current_map,
                    require_visible_control=False,
                    post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )
                status = "paused"
            else:
                final = current_map.to_policy_json()
                status = "already_paused"
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "pause": {"status": status},
                "final_screen": final["screen"],
                "final_observation_id": final["observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "death-terminal":
            death_driver = new_driver()
            _terminal_first, terminal_frame = wait_for_custom_state(
                death_driver,
                lambda frame: _death_terminal_state(frame) is not None,
                "one-life death terminal",
                timeout_seconds=min(
                    30.0, _remaining(deadline, "one-life death terminal")
                ),
            )
            terminal = _extract_death_terminal(terminal_frame)
            technical_handoff = False

            if terminal["terminal_kind"] == "native_succession_handoff":
                technical_handoff = True
                _handoff_first, handoff_after = click_visible_text_once(
                    death_driver,
                    terminal_frame,
                    text="继续扮演",
                    region=(0.45, 0.55, 0.80, 0.92),
                    control_id="death.technical_settlement_handoff",
                    expected_post_screen="settlement_handoff",
                    post_predicate=lambda frame: bool(
                        getattr(frame, "screen", None)
                        in {"map_hud", "map_running"}
                        or _death_terminal_state(frame)
                        == "recurrence_settlement_event"
                    ),
                )
                if (
                    _death_terminal_state(handoff_after)
                    != "recurrence_settlement_event"
                ):
                    window.require_foreground()
                    append_event(
                        events,
                        {
                            "kind": "opening_key_input_planned",
                            "control_id": "death.handoff_speed_one",
                            "key": "1",
                            "scan_code": CK3_SHORTCUT_SCAN_CODES["1"],
                            "expected_post_screen": "settlement_delivery",
                        },
                    )
                    speed_accepted, speed_error = _prepare_key_press_batch(
                        CK3_SHORTCUT_SCAN_CODES["1"]
                    )()
                    if speed_accepted != 2:
                        raise AgentError(
                            "settlement handoff speed shortcut was partial: "
                            f"accepted={speed_accepted}, last_error={speed_error}"
                        )
                    resume_accepted = None
                    resume_error = None
                    if getattr(handoff_after, "screen", None) == "map_hud":
                        resume_accepted, resume_error = _prepare_key_press_batch(
                            CK3_SHORTCUT_SCAN_CODES["space"]
                        )()
                        if resume_accepted != 2:
                            raise AgentError(
                                "settlement handoff resume shortcut was partial: "
                                f"accepted={resume_accepted}, last_error={resume_error}"
                            )
                    actions.append(
                        {
                            "control_id": "death.handoff_speed_one",
                            "status": "confirmed",
                            "input_kind": "keyboard_shortcut",
                            "key": "1_then_space_if_paused",
                            "technical_settlement_handoff": True,
                            "heir_gameplay_actions": 0,
                            "send_input": {
                                "speed_requested": 2,
                                "speed_accepted": speed_accepted,
                                "speed_last_error": speed_error,
                                "resume_requested": (
                                    2 if resume_accepted is not None else 0
                                ),
                                "resume_accepted": resume_accepted,
                                "resume_last_error": resume_error,
                            },
                        }
                    )
                    _settlement_first, terminal_frame = wait_for_custom_state(
                        death_driver,
                        lambda frame: _death_terminal_state(frame)
                        == "recurrence_settlement_event",
                        "recurrence settlement after succession handoff",
                        timeout_seconds=min(
                            30.0,
                            _remaining(
                                deadline,
                                "recurrence settlement after succession handoff",
                            ),
                        ),
                    )
                else:
                    terminal_frame = handoff_after
                terminal = _extract_death_terminal(terminal_frame)

            if terminal["terminal_kind"] == "recurrence_settlement_event":
                if terminal["score"]["final"] is None:
                    import pyautogui

                    pyautogui.FAILSAFE = True
                    scroll_point = (800, 720)
                    window.require_foreground()
                    window.require_unobscured(scroll_point)
                    pyautogui.moveTo(
                        window.client_rect[0] + scroll_point[0],
                        window.client_rect[1] + scroll_point[1],
                        duration=0.12,
                    )
                    window.require_cursor_target(scroll_point)
                    pyautogui.scroll(-12)
                    _score_first, score_frame = wait_for_custom_state(
                        death_driver,
                        lambda frame: _death_terminal_state(frame)
                        == "recurrence_settlement_event",
                        "scrolled recurrence settlement",
                    )
                    scrolled = _extract_death_terminal(score_frame)
                    terminal["score"] = {
                        key: (
                            value
                            if value is not None
                            else terminal["score"].get(key)
                        )
                        for key, value in scrolled["score"].items()
                    }
                    terminal["scrolled_observation_id"] = score_frame.observation_id
                    terminal_frame = score_frame
                window.require_foreground()
                append_event(
                    events,
                    {
                        "kind": "opening_key_input_planned",
                        "control_id": "death.settlement_confirm",
                        "key": "shift+1",
                        "scan_code": CK3_SHORTCUT_SCAN_CODES["1"],
                        "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES[
                            "left_shift"
                        ],
                        "expected_post_screen": "observer_mode",
                    },
                )
                accepted, last_error = _prepare_key_chord_batch(
                    CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    CK3_SHORTCUT_SCAN_CODES["1"],
                )()
                if accepted != 4:
                    raise AgentError(
                        "death settlement shortcut was partial: "
                        f"accepted={accepted}, last_error={last_error}"
                    )
                _observer_first, observer_frame = wait_for_custom_state(
                    death_driver,
                    _observer_mode_visible,
                    "observer mode after one-life settlement",
                )
                actions.append(
                    {
                        "control_id": "death.settlement_confirm",
                        "status": "confirmed",
                        "input_kind": "keyboard_shortcut",
                        "key": "shift+1",
                        "send_input": {
                            "requested": 4,
                            "accepted": accepted,
                            "last_error": last_error,
                        },
                        "result_observation_id": observer_frame.observation_id,
                        "heir_gameplay_actions": 0,
                    }
                )
                window.require_foreground()
                menu_accepted, menu_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if menu_accepted != 2:
                    raise AgentError(
                        "terminal pause-menu shortcut was partial: "
                        f"accepted={menu_accepted}, last_error={menu_error}"
                    )
                _menu_first, pause_menu = wait_for_custom_state(
                    death_driver, _pause_menu_visible, "terminal pause menu"
                )
                window.require_foreground()
                exit_accepted, exit_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["5"]
                )()
                if exit_accepted != 2:
                    raise AgentError(
                        "terminal exit-game shortcut was partial: "
                        f"accepted={exit_accepted}, last_error={exit_error}"
                    )
                _exit_first, exit_confirmation = wait_for_custom_state(
                    death_driver,
                    _exit_to_main_menu_confirmation_visible,
                    "terminal exit confirmation",
                )
                actions.extend(
                    (
                        {
                            "control_id": "death.open_game_menu",
                            "status": "confirmed",
                            "input_kind": "keyboard_shortcut",
                            "key": "escape",
                            "send_input": {
                                "requested": 2,
                                "accepted": menu_accepted,
                                "last_error": menu_error,
                            },
                            "result_observation_id": pause_menu.observation_id,
                        },
                        {
                            "control_id": "death.open_exit_confirmation",
                            "status": "confirmed",
                            "input_kind": "keyboard_shortcut",
                            "key": "5",
                            "send_input": {
                                "requested": 2,
                                "accepted": exit_accepted,
                                "last_error": exit_error,
                            },
                            "result_observation_id": (
                                exit_confirmation.observation_id
                            ),
                        },
                    )
                )
            elif terminal["terminal_kind"] == "native_no_heir_settlement":
                _exit_first, exit_confirmation = click_visible_text_once(
                    death_driver,
                    terminal_frame,
                    text="退出到菜单",
                    region=(0.30, 0.55, 0.70, 0.98),
                    control_id="death.no_heir_exit",
                    expected_post_screen="exit_confirmation",
                    post_predicate=_exit_to_main_menu_confirmation_visible,
                )
            else:
                raise AgentError("one-life death did not reach a settlement screen")

            _main_first, main_menu = click_visible_text_once(
                death_driver,
                exit_confirmation,
                text="退出到主菜单",
                region=(0.30, 0.25, 0.70, 0.70),
                control_id="death.exit_to_main_menu",
                expected_post_screen="main_menu",
                post_predicate=lambda frame: getattr(frame, "screen", None)
                == "main_menu",
            )
            terminal.update(
                {
                    "technical_settlement_handoff": technical_handoff,
                    "heir_gameplay_actions": 0,
                    "returned_to_main_menu": True,
                    "final_observation_id": main_menu.observation_id,
                }
            )
            prior_commands: list[dict[str, object]] = []
            session_report_path = artifacts.parent / "report.json"
            if session_report_path.exists():
                try:
                    session_report = json.loads(
                        session_report_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError) as error:
                    raise AgentError(
                        f"development session report is unreadable: {error}"
                    ) from error
                raw_commands = session_report.get("commands")
                if isinstance(raw_commands, list):
                    prior_commands = [
                        row for row in raw_commands if isinstance(row, dict)
                    ]
            cross_run_strategy = record_one_life_episode(
                spec.state_dir,
                run_id=artifacts.parent.name,
                commands=[
                    *prior_commands,
                    {
                        "command": "death-terminal",
                        "ok": True,
                        "result": {"terminal": terminal},
                    },
                ],
                terminal=terminal,
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "terminal": terminal,
                "cross_run_strategy": cross_run_strategy,
                "final_screen": "main_menu",
                "final_observation_id": main_menu.observation_id,
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if not resume_saved_game:
            live_driver = new_driver()
            _live_first, live_map = wait_for_custom_state(
                live_driver,
                lambda frame: (
                    getattr(frame, "screen", None)
                    in {"map_hud", "map_running"}
                    or _steward_development_targeting_active(frame)
                    or _council_panel_visible(frame)
                    or _pause_menu_visible(frame)
                    or _load_window_visible(frame)
                    or _title_finder_visible(frame)
                    or _palermo_interactions_visible(frame)
                    or _declare_war_window_visible(frame)
                    or _war_overview_visible(frame)
                    or _marriage_window_visible(frame)
                    or _marriage_acceptance_in_frame(frame) is not None
                    or _generic_event_in_frame(frame) is not None
                ),
                "current development map",
            )
            if _marriage_window_visible(live_map):
                window.require_foreground()
                close_matchmaker, close_matchmaker_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if close_matchmaker != 2:
                    raise AgentError(
                        "existing matchmaker close was partial: "
                        f"accepted={close_matchmaker}, last_error={close_matchmaker_error}"
                    )
                _panel_first, _panel_second = wait_for_custom_state(
                    live_driver,
                    lambda frame: getattr(frame, "screen", None) == "player_character",
                    "player panel after existing matchmaker close",
                )
                window.require_foreground()
                close_panel, close_panel_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["f1"]
                )()
                if close_panel != 2:
                    raise AgentError(
                        "existing player panel close was partial: "
                        f"accepted={close_panel}, last_error={close_panel_error}"
                    )
                live_driver.observe_stable(
                    "map_hud",
                    min(
                        INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                        _remaining(deadline, "map after existing matchmaker close"),
                    ),
                    stable_frames=2,
                )
            elif _steward_development_targeting_active(live_map):
                window.require_foreground()
                append_event(
                    events,
                    {
                        "kind": "opening_key_input_planned",
                        "control_id": "development_session.cancel_targeting",
                        "key": "escape",
                        "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                        "expected_post_screen": "map_hud",
                    },
                )
                cancel_accepted, cancel_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if cancel_accepted != 2:
                    raise AgentError(
                        "development targeting cancel was partial: "
                        f"accepted={cancel_accepted}, last_error={cancel_last_error}"
                    )
                wait_for_custom_state(
                    live_driver,
                    _council_panel_visible,
                    "council panel after targeting cancel",
                )
                append_event(
                    events,
                    {
                        "kind": "opening_key_input_planned",
                        "control_id": "development_session.close_council_after_cancel",
                        "key": "f4",
                        "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                        "expected_post_screen": "map_hud",
                    },
                )
                close_accepted, close_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["f4"]
                )()
                if close_accepted != 2:
                    raise AgentError(
                        "F4 after development targeting cancel was partial: "
                        f"accepted={close_accepted}, last_error={close_last_error}"
                    )
                live_driver.observe_stable(
                    "map_hud",
                    min(
                        INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                        _remaining(deadline, "map after targeting cancel"),
                    ),
                    stable_frames=2,
                )
            elif _council_panel_visible(live_map):
                window.require_foreground()
                append_event(
                    events,
                    {
                        "kind": "opening_key_input_planned",
                        "control_id": "development_session.close_existing_council",
                        "key": "f4",
                        "scan_code": CK3_SHORTCUT_SCAN_CODES["f4"],
                        "expected_post_screen": "map_hud",
                    },
                )
                close_accepted, close_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["f4"]
                )()
                if close_accepted != 2:
                    raise AgentError(
                        "existing council close was partial: "
                        f"accepted={close_accepted}, last_error={close_last_error}"
                    )
                live_driver.observe_stable(
                    "map_hud",
                    min(
                        INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                        _remaining(deadline, "map after existing council close"),
                    ),
                    stable_frames=2,
                )
            elif _pause_menu_visible(live_map):
                window.require_foreground()
                close_accepted, close_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if close_accepted != 2:
                    raise AgentError(
                        "existing pause-menu close was partial: "
                        f"accepted={close_accepted}, last_error={close_last_error}"
                    )
                live_driver.observe_stable(
                    "map_hud",
                    min(
                        INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                        _remaining(deadline, "map after existing pause-menu close"),
                    ),
                    stable_frames=2,
                )
            elif _war_overview_visible(live_map):
                window.require_foreground()
                append_event(
                    events,
                    {
                        "kind": "opening_key_input_planned",
                        "control_id": "development_session.close_existing_war_overview",
                        "key": "escape",
                        "scan_code": CK3_SHORTCUT_SCAN_CODES["escape"],
                        "expected_post_screen": "map",
                    },
                )
                close_accepted, close_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if close_accepted != 2:
                    raise AgentError(
                        "existing war overview close was partial: "
                        f"accepted={close_accepted}, last_error={close_last_error}"
                    )
                _map_first, post_overview_map = wait_for_custom_state(
                    live_driver,
                    lambda frame: getattr(frame, "screen", None)
                    in {"map_hud", "map_running"},
                    "map after existing war overview close",
                )
                if getattr(post_overview_map, "screen", None) == "map_running":
                    press_shortcut(
                        "map_running",
                        "map_running.pause_after_existing_war_overview",
                        "space",
                        CK3_SHORTCUT_SCAN_CODES["space"],
                        "map_hud",
                        "paused map after existing war overview",
                        driver=live_driver,
                        stable=post_overview_map,
                        require_visible_control=False,
                        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    )
            elif live_map.screen == "map_running":
                press_shortcut(
                    "map_running",
                    "map_running.pause",
                    "space",
                    CK3_SHORTCUT_SCAN_CODES["space"],
                    "map_hud",
                    "paused current development map",
                    driver=live_driver,
                    stable=SimpleNamespace(
                        screen="map_running",
                        controls=live_map.controls,
                    ),
                    post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )
        if development_step == "resolve-current-event":
            event_driver = new_driver()
            first_frame = event_driver.capture_once()
            second_frame = event_driver.capture_once()
            first_call = _call_to_war_in_frame(first_frame)
            second_call = _call_to_war_in_frame(second_frame)
            if first_call is not None and second_call is not None:
                resolved_call, final = accept_visible_call_to_war(
                    event_driver, second_call
                )
                return {
                    "development_only": True,
                    "release_qualification": False,
                    "step": development_step,
                    "resume": resume_info,
                    "actions": actions,
                    "diplomatic_event": resolved_call,
                    "final_screen": final["screen"],
                    "final_observation_id": final["observation_id"],
                    "window_binding": window.audit_binding(),
                    "foreground_activation": foreground,
                }
            first_event = _generic_event_in_frame(first_frame)
            second_event = _generic_event_in_frame(second_frame)
            if (
                first_event is None
                or second_event is None
                or not _same_generic_event(first_event, second_event)
            ):
                raise AgentError("current ordinary event is not visibly stable")
            resolved_events, final_observation = run_ordinary_event_loop(
                1,
                initial_event=second_event,
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "ordinary_events": resolved_events,
                "final_screen": final_observation["screen"],
                "final_observation_id": final_observation["observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "dynasty-review":
            player_observation = press_shortcut(
                "map_hud",
                "map_hud.open_player_character",
                "f1",
                CK3_SHORTCUT_SCAN_CODES["f1"],
                "player_character",
                "player character dynasty review",
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            dynasty_state = _extract_player_character_state(player_observation)
            dynasty_state["strategy"] = _choose_one_life_dynasty_action(
                dynasty_state
            )
            dynasty_state["visible_text"] = [
                item["text"]
                for item in player_observation.get("ocr", [])
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            final_observation = press_shortcut(
                "player_character",
                "player_character.close",
                "f1",
                CK3_SHORTCUT_SCAN_CODES["f1"],
                "map_hud",
                "map after dynasty review",
                require_visible_control=False,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "dynasty_state": dynasty_state,
                "final_screen": final_observation.get("screen"),
                "final_observation_id": final_observation.get("observation_id"),
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "succession-review":
            _realm_summary, _realm_frame = inspect_map_panel(
                "realm",
                "我的领地",
                "f2",
                CK3_SHORTCUT_SCAN_CODES["f2"],
                leave_open=True,
            )
            realm_driver = new_driver()
            window.require_foreground()
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": "realm_panel.open_succession",
                    "key": "ctrl+4",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["4"],
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_ctrl"],
                    "expected_post_screen": "succession_panel",
                },
            )
            accepted, last_error = _prepare_key_chord_batch(
                CK3_SHORTCUT_SCAN_CODES["left_ctrl"],
                CK3_SHORTCUT_SCAN_CODES["4"],
            )()
            if accepted != 4:
                raise AgentError(
                    "Ctrl+4 succession-tab shortcut was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )
            _succession_first, succession_frame = wait_for_custom_state(
                realm_driver,
                _succession_panel_visible,
                "native succession tab",
            )
            actions.append(
                {
                    "control_id": "realm_panel.open_succession",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "ctrl+4",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["4"],
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_ctrl"],
                    "send_input": {
                        "requested": 4,
                        "accepted": accepted,
                        "last_error": last_error,
                    },
                    "result_observation_id": succession_frame.observation_id,
                    "expected_post_screen": "succession_panel",
                }
            )
            succession_state = _extract_current_life_succession_state(
                succession_frame
            )
            window.require_foreground()
            close_accepted, close_last_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["f2"]
            )()
            if close_accepted != 2:
                raise AgentError(
                    "F2 succession-panel close was partial: "
                    f"accepted={close_accepted}, last_error={close_last_error}"
                )
            final_map = realm_driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "map after succession review"),
                ),
                stable_frames=2,
            )
            actions.append(
                {
                    "control_id": "succession_panel.close",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "f2",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["f2"],
                    "send_input": {
                        "requested": 2,
                        "accepted": close_accepted,
                        "last_error": close_last_error,
                    },
                    "result_observation_id": final_map.observation_id,
                    "expected_post_screen": "map_hud",
                }
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "succession_state": succession_state,
                "final_screen": final_map.screen,
                "final_observation_id": final_map.observation_id,
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step in {"marriage-review", "marriage-alliance"}:
            player_observation = press_shortcut(
                "map_hud",
                "map_hud.open_player_character",
                "f1",
                CK3_SHORTCUT_SCAN_CODES["f1"],
                "player_character",
                "player family before marriage review",
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            marriage_driver = new_driver()
            _family_first, family_frame = wait_for_custom_state(
                marriage_driver,
                lambda frame: getattr(frame, "screen", None) == "player_character",
                "stable player family for marriage review",
            )
            import pyautogui

            pyautogui.FAILSAFE = True
            selected_point = None
            interaction_frame = None
            interaction_text = None
            attempted_points: list[list[int]] = []
            for point in _child_portrait_candidates(family_frame):
                attempted_points.append(list(point))
                window.require_foreground()
                window.require_unobscured(point)
                append_event(
                    events,
                    {
                        "kind": "opening_pointer_input_planned",
                        "control_id": "player_character.child_interactions",
                        "center": list(point),
                        "input_kind": "right_click",
                        "expected_post_screen": "character_interaction_menu",
                    },
                )
                pyautogui.moveTo(
                    window.client_rect[0] + point[0],
                    window.client_rect[1] + point[1],
                    duration=0.12,
                )
                window.require_cursor_target(point)
                right_accepted, right_last_error = _prepare_right_click_batch()()
                if right_accepted != 2:
                    raise AgentError(
                        "child portrait right click was partial: "
                        f"accepted={right_accepted}, last_error={right_last_error}"
                    )
                first_menu = marriage_driver.capture_once()
                second_menu = marriage_driver.capture_once()
                if (
                    _marriage_interaction_visible(first_menu)
                    and _marriage_interaction_visible(second_menu)
                ):
                    selected_point = point
                    interaction_frame = second_menu
                    choices = [
                        text
                        for text in ("寻找配偶", "安排婚姻")
                        if _spans_with_text(second_menu, text)
                    ]
                    interaction_text = choices[0]
                    actions.append(
                        {
                            "control_id": "player_character.child_interactions",
                            "status": "confirmed",
                            "input_kind": "visible_right_click",
                            "click_point": list(point),
                            "visible_marriage_action": interaction_text,
                            "result_observation_id": second_menu.observation_id,
                            "send_input": {
                                "requested": 2,
                                "accepted": right_accepted,
                                "last_error": right_last_error,
                            },
                        }
                    )
                    break
                window.require_foreground()
                escape_accepted, escape_last_error = _prepare_key_press_batch(
                    CK3_SHORTCUT_SCAN_CODES["escape"]
                )()
                if escape_accepted != 2:
                    raise AgentError(
                        "interaction menu close was partial: "
                        f"accepted={escape_accepted}, last_error={escape_last_error}"
                    )
            if selected_point is None or interaction_frame is None or interaction_text is None:
                raise AgentError("no visible child exposes a marriage interaction")
            _marriage_first, marriage_frame = click_visible_text_once(
                marriage_driver,
                interaction_frame,
                text=interaction_text,
                region=(0.0, 0.0, 1.0, 1.0),
                control_id="child_interactions.open_matchmaker",
                expected_post_screen="marriage_matchmaker",
                post_predicate=_marriage_window_visible,
            )
            marriage_review = _extract_marriage_review(marriage_frame)
            marriage_review["child_portrait_point"] = list(selected_point)
            marriage_review["attempted_portrait_points"] = attempted_points
            marriage_review["interaction"] = interaction_text
            if development_step == "marriage-alliance":
                candidate_spans = sorted(
                    _spans_with_text(
                        marriage_frame,
                        "丹麦王子",
                        contains=True,
                        region=(0.35, 0.45, 0.60, 0.90),
                    ),
                    key=lambda item: (item.center[1], item.center[0]),
                )
                if not candidate_spans:
                    raise AgentError("matchmaker exposes no visible Danish alliance candidate")
                selected_candidate = candidate_spans[0]
                _offer_first, offer_frame = click_visible_text_once(
                    marriage_driver,
                    marriage_frame,
                    text=selected_candidate.text,
                    region=(0.35, 0.45, 0.60, 0.90),
                    control_id="marriage_matchmaker.select_alliance_candidate",
                    expected_post_screen="marriage_offer",
                    post_predicate=_marriage_offer_visible,
                )
                proposal_matches = _spans_with_text(offer_frame, "求婚")
                if len(proposal_matches) != 1:
                    raise AgentError("marriage offer lacks one visible proposal button")
                _proposal_first, panel_frame = click_visible_text_once(
                    marriage_driver,
                    offer_frame,
                    text="求婚",
                    region=(0.20, 0.55, 0.80, 0.95),
                    control_id="marriage_offer.send_proposal",
                    expected_post_screen="player_character",
                    post_predicate=lambda frame: bool(
                        getattr(frame, "screen", None) == "player_character"
                        and not _marriage_window_visible(frame)
                    ),
                )
                marriage_review.update(
                    {
                        "status": "proposal_sent",
                        "selected_candidate": selected_candidate.text,
                        "strategy": "top-visible-related-alliance-candidate-v1",
                    }
                )
            else:
                window.require_foreground()
                close_matchmaker_accepted, close_matchmaker_error = (
                    _prepare_key_press_batch(CK3_SHORTCUT_SCAN_CODES["escape"])()
                )
                if close_matchmaker_accepted != 2:
                    raise AgentError(
                        "matchmaker close was partial: "
                        f"accepted={close_matchmaker_accepted}, last_error={close_matchmaker_error}"
                    )
                _panel_first, panel_frame = wait_for_custom_state(
                    marriage_driver,
                    lambda frame: getattr(frame, "screen", None) == "player_character",
                    "player panel after marriage review",
                )
            window.require_foreground()
            close_panel_accepted, close_panel_error = _prepare_key_press_batch(
                CK3_SHORTCUT_SCAN_CODES["f1"]
            )()
            if close_panel_accepted != 2:
                raise AgentError(
                    "F1 close after marriage review was partial: "
                    f"accepted={close_panel_accepted}, last_error={close_panel_error}"
                )
            final_map = marriage_driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "map after marriage review"),
                ),
                stable_frames=2,
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "marriage_review": marriage_review,
                "final_screen": final_map.screen,
                "final_observation_id": final_map.observation_id,
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "marriage-confirm-response":
            response_driver = new_driver()
            first_response = response_driver.capture_once()
            second_response = response_driver.capture_once()
            first_acceptance = _marriage_acceptance_in_frame(first_response)
            second_acceptance = _marriage_acceptance_in_frame(second_response)
            if first_acceptance is None or second_acceptance is None:
                raise AgentError("accepted marriage response is not visibly stable")
            window.require_foreground()
            append_event(
                events,
                {
                    "kind": "opening_key_input_planned",
                    "control_id": "marriage_response.accept",
                    "key": "shift+1",
                    "scan_code": CK3_SHORTCUT_SCAN_CODES["1"],
                    "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                    "expected_post_screen": "map",
                },
            )
            accepted, last_error = _prepare_key_chord_batch(
                CK3_SHORTCUT_SCAN_CODES["left_shift"],
                CK3_SHORTCUT_SCAN_CODES["1"],
            )()
            if accepted != 4:
                raise AgentError(
                    "marriage response shortcut was partial: "
                    f"accepted={accepted}, last_error={last_error}"
                )
            _map_first, after = wait_for_custom_state(
                response_driver,
                lambda frame: getattr(frame, "screen", None)
                in {"map_hud", "map_running"},
                "map after accepted marriage response",
            )
            if after.screen == "map_running":
                final = press_shortcut(
                    "map_running",
                    "map_running.pause_after_marriage_response",
                    "space",
                    CK3_SHORTCUT_SCAN_CODES["space"],
                    "map_hud",
                    "paused after accepted marriage response",
                    driver=response_driver,
                    stable=after,
                    require_visible_control=False,
                    post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                )
            else:
                final = after.to_policy_json()
            actions.append(
                {
                    "control_id": "marriage_response.accept",
                    "status": "confirmed",
                    "input_kind": "keyboard_shortcut",
                    "key": "shift+1",
                    "send_input": {
                        "requested": 4,
                        "accepted": accepted,
                        "last_error": last_error,
                    },
                    "result_observation_id": final["observation_id"],
                    "expected_post_screen": "map_hud",
                }
            )
            second_acceptance["ending_date"] = _extract_map_date(final)
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "marriage_result": second_acceptance,
                "final_screen": final["screen"],
                "final_observation_id": final["observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-review":
            military_state, final_observation = inspect_map_panel(
                *MAP_PANEL_SHORTCUTS[1]
            )
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "military_state": military_state,
                "final_screen": getattr(final_observation, "screen", None),
                "final_observation_id": getattr(
                    final_observation, "observation_id", None
                ),
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-target-review":
            target_state = review_palermo_war_target()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_target": target_state,
                "final_screen": "map_hud",
                "final_observation_id": target_state["frame_observation_ids"][-1],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-interaction-review":
            interaction_state = review_palermo_interactions()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_interactions": interaction_state,
                "final_screen": "palermo_interactions",
                "final_observation_id": interaction_state[
                    "frame_observation_ids"
                ][-1],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-declaration-review":
            declaration_state = review_palermo_declaration()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_declaration": declaration_state,
                "final_screen": "declare_war_window",
                "final_observation_id": declaration_state[
                    "frame_observation_ids"
                ][-1],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-casus-belli-review":
            casus_belli_state = review_palermo_county_holy_war()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_casus_belli": casus_belli_state,
                "final_screen": "declare_war_target_selection",
                "final_observation_id": casus_belli_state[
                    "frame_observation_ids"
                ][-1],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-goal-review":
            war_goal_state = select_palermo_war_goal()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_goal": war_goal_state,
                "final_screen": "declare_war_ready",
                "final_observation_id": war_goal_state[
                    "frame_observation_ids"
                ][-1],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-declare-palermo":
            war_state = declare_palermo_county_holy_war()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war": war_state,
                "final_screen": "map_hud",
                "final_observation_id": war_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-raise-all":
            army_state = raise_all_war_armies()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "army": army_state,
                "final_screen": "armies_raised",
                "final_observation_id": army_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-move-palermo":
            # Backward-compatible command alias.  The former implementation
            # right-clicked an unverified map coordinate and failed in real
            # play.  Route it through the proven title-search + fort-hover
            # workflow instead.
            march_state = move_selected_army_to_palermo_fort()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "march": march_state,
                "final_screen": "army_moving_to_palermo_fort",
                "final_observation_id": march_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-map-review":
            map_state = review_current_war_map()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_map": map_state,
                "final_screen": "map_hud",
                "final_observation_id": map_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-find-palermo":
            target_state = find_palermo_title()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_target_search": target_state,
                "final_screen": "map_hud",
                "final_observation_id": target_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-siege-palermo":
            siege_state = move_selected_army_to_palermo_fort()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "siege": siege_state,
                "final_screen": "army_moving_to_palermo_fort",
                "final_observation_id": siege_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-advance-week":
            progress_state = advance_war_one_week()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_progress": progress_state,
                "final_screen": progress_state["final_screen"],
                "final_observation_id": progress_state[
                    "final_observation_id"
                ],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-advance-month":
            progress_state = advance_war_one_month()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_progress": progress_state,
                "final_screen": progress_state["final_screen"],
                "final_observation_id": progress_state[
                    "final_observation_id"
                ],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-status":
            status_state = inspect_active_war_status()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_status": status_state,
                "final_screen": "map_hud",
                "final_observation_id": status_state[
                    "final_observation_id"
                ],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-enforce-demands":
            victory_state = enforce_active_war_demands()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "war_victory": victory_state,
                "final_screen": "map_hud",
                "final_observation_id": victory_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "war-disband-armies":
            disband_state = disband_war_armies()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "army_disband": disband_state,
                "final_screen": "map_hud",
                "final_observation_id": disband_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "save-checkpoint":
            checkpoint, final_observation = save_development_checkpoint()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "checkpoint": checkpoint,
                "final_screen": final_observation.get("screen"),
                "final_observation_id": final_observation.get("observation_id"),
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step == "restore-checkpoint":
            restore_state = restore_latest_development_checkpoint()
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "restore": restore_state,
                "final_screen": "map_hud",
                "final_observation_id": restore_state["final_observation_id"],
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        if development_step in {"life-advance", "economic-event-cycle"}:
            cycle_driver = new_driver()
            paused_map = cycle_driver.observe_stable(
                "map_hud",
                min(
                    INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
                    _remaining(deadline, "economic cycle starting map"),
                ),
                stable_frames=2,
            )
            starting_date = _extract_map_date(paused_map.to_policy_json())
            press_shortcut(
                "map_hud",
                "map_hud.set_speed_five",
                "5",
                CK3_SHORTCUT_SCAN_CODES["5"],
                "map_hud",
                "economic cycle speed five",
                driver=cycle_driver,
                stable=paused_map,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            press_shortcut(
                "map_hud",
                "map_hud.resume",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_running",
                "economic cycle running timeline",
                driver=cycle_driver,
                stable=paused_map,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )
            cycle_events, final_observation = run_ordinary_event_loop(
                1,
                wait_timeout_seconds=(
                    ONE_LIFE_TURN_WAIT_SECONDS
                    if development_step == "life-advance"
                    else DEVELOPMENT_EVENT_WAIT_SECONDS
                ),
            )
            ending_date = _extract_map_date(final_observation)
            if int(ending_date["ordinal"]) <= int(starting_date["ordinal"]):
                raise AgentError("economic cycle did not advance the CK3 date")
            panel_snapshots: dict[str, dict[str, object]] = {}
            if development_step == "economic-event-cycle":
                for panel_id, title, key, scan_code in (
                    MAP_PANEL_SHORTCUTS[0],
                    MAP_PANEL_SHORTCUTS[2],
                ):
                    summary, final_observation = inspect_map_panel(
                        panel_id,
                        title,
                        key,
                        scan_code,
                    )
                    panel_snapshots[panel_id] = summary
            return {
                "development_only": True,
                "release_qualification": False,
                "step": development_step,
                "resume": resume_info,
                "actions": actions,
                "starting_date": starting_date,
                "ending_date": ending_date,
                "elapsed_days": int(ending_date["ordinal"])
                - int(starting_date["ordinal"]),
                "ordinary_events": cycle_events,
                "map_panels": panel_snapshots,
                "final_screen": final_observation.get("screen"),
                "final_observation_id": final_observation.get("observation_id"),
                "window_binding": window.audit_binding(),
                "foreground_activation": foreground,
            }
        steward_development, final_observation = (
            assign_steward_to_develop_foggia()
        )
        return {
            "development_only": True,
            "release_qualification": False,
            "step": development_step,
            "resume": resume_info,
            "actions": actions,
            "steward_development": steward_development,
            "final_screen": final_observation.get("screen"),
            "final_observation_id": final_observation.get("observation_id"),
            "window_binding": window.audit_binding(),
            "foreground_activation": foreground,
        }

    if resume_saved_game:
        return {
            "development_only": True,
            "release_qualification": False,
            "step": None,
            "resume": resume_info,
            "actions": actions,
            "final_screen": "map_hud",
            "final_observation_id": resume_info["result_observation_id"],
            "window_binding": window.audit_binding(),
            "foreground_activation": foreground,
        }

    click(
        "main_menu",
        "main_menu.new_game",
        "bookmark lobby",
        observe_timeout_seconds=INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
    )
    click(
        "bookmark_lobby",
        "bookmark_lobby.select_robert",
        "Robert selection",
    )
    click(
        "bookmark_lobby_selected",
        "bookmark_lobby.start_game",
        "first pact event",
    )
    press_event_option(
        "pact_event",
        "pact_event.accept_contract",
        "first_life_event",
        "first-life explanation",
        option_number=1,
    )
    press_event_option(
        "first_life_event",
        "first_life_event.begin",
        "blessing_event",
        "first blessing choice",
        option_number=1,
    )
    blessing_driver = new_driver()
    blessing_stable = blessing_driver.observe_stable(
        "blessing_event",
        _remaining(deadline, "stable first blessing choice"),
        stable_frames=2,
    )
    selected, visible_text, strategy_score = _choose_first_blessing(blessing_stable)
    final_observation = press_event_option(
        "blessing_event",
        selected.control_id,
        "curse_event",
        "first curse choice",
        driver=blessing_driver,
        stable=blessing_stable,
        summary_fields={
            "visible_choice": visible_text,
            "strategy_score": strategy_score,
        },
    )
    if final_observation.get("screen") != "curse_event":
        raise AgentError("opening did not reach the first curse choice")
    curse_driver = new_driver()
    curse_stable = curse_driver.observe_stable(
        "curse_event",
        _remaining(deadline, "stable first curse choice"),
        stable_frames=2,
    )
    curse_selected, curse_text, curse_loss = _choose_first_curse(curse_stable)
    final_observation = press_event_option(
        "curse_event",
        curse_selected.control_id,
        "map_hud",
        "playable map",
        driver=curse_driver,
        stable=curse_stable,
        summary_fields={
            "visible_choice": curse_text,
            "strategy_loss": curse_loss,
        },
    )
    if final_observation.get("screen") != "map_hud":
        raise AgentError("opening did not reach the playable map after its first pair")
    final_observation = press_shortcut(
        "map_hud",
        "map_hud.open_player_character",
        "f1",
        CK3_SHORTCUT_SCAN_CODES["f1"],
        "player_character",
        "player character state",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    player_state = _extract_player_character_state(final_observation)
    press_shortcut(
        "player_character",
        "player_character.close",
        "f1",
        CK3_SHORTCUT_SCAN_CODES["f1"],
        "map_hud",
        "playable map after player inspection",
        require_visible_control=False,
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    click(
        "map_hud",
        "map_hud.open_lifestyle",
        "lifestyle selection",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    click(
        "lifestyle_selection",
        "lifestyle_selection.open_martial",
        "martial lifestyle",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    click(
        "lifestyle_martial_unfocused",
        "lifestyle_martial.select_authority_focus",
        "authority focus confirmation",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    final_observation = press_shortcut(
        "lifestyle_authority_confirmation",
        "lifestyle_authority_confirmation.confirm",
        "enter",
        CK3_SHORTCUT_SCAN_CODES["enter"],
        "lifestyle_martial_authority",
        "selected authority focus",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    lifestyle_state = _extract_lifestyle_state(final_observation)
    final_observation = press_shortcut(
        "lifestyle_martial_authority",
        "lifestyle_martial_authority.close",
        "escape",
        CK3_SHORTCUT_SCAN_CODES["escape"],
        "map_hud",
        "paused map after lifestyle selection",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    starting_date = _extract_map_date(final_observation)
    final_observation = press_shortcut(
        "map_hud",
        "map_hud.set_speed_five",
        "5",
        CK3_SHORTCUT_SCAN_CODES["5"],
        "map_hud",
        "speed five selected",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    final_observation = press_shortcut(
        "map_hud",
        "map_hud.resume",
        "space",
        CK3_SHORTCUT_SCAN_CODES["space"],
        "map_running",
        "running timeline",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    running_date = _extract_map_date(final_observation)
    if int(running_date["ordinal"]) <= int(starting_date["ordinal"]):
        raise AgentError("CK3 timeline did not advance after resume")

    ordinary_events: list[dict[str, object]] = []
    final_observation: dict[str, object] | None = None
    post_driver = None
    post_state = None
    pending_event: dict[str, object] | None = None
    event_index = 0
    while event_index < ordinary_event_count or pending_event is not None:
        event_index += 1
        if event_index > ordinary_event_count + MAX_CHAINED_ORDINARY_EVENTS:
            raise AgentError("ordinary CK3 event chain exceeded its bounded depth")
        detected_event = pending_event
        pending_event = None
        if detected_event is None:
            event_deadline = min(
                deadline,
                time.monotonic() + ORDINARY_EVENT_WAIT_TIMEOUT_SECONDS,
            )
            event_driver = new_driver()
            preview_sequence = 0
            while time.monotonic() < event_deadline:
                preview_sequence += 1
                generic_preview, _, terminal_preview = _visible_event_preview(
                    window, preview_sequence
                )
                if terminal_preview is not None:
                    raise AgentError(
                        "one-life death terminal visible: "
                        f"{terminal_preview}"
                    )
                if generic_preview is None:
                    continue
                first_frame = event_driver.capture_once()
                second_frame = event_driver.capture_once()
                prior_event = _generic_event_in_frame(first_frame)
                candidate = _generic_event_in_frame(second_frame)
                if (
                    prior_event is not None
                    and candidate is not None
                    and int(candidate["capture_sequence"])
                    == int(prior_event["capture_sequence"]) + 1
                    and _same_generic_event(prior_event, candidate)
                ):
                    detected_event = candidate
                    break
            if detected_event is None:
                raise AgentError(
                    f"ordinary CK3 event {event_index}/{ordinary_event_count} "
                    "did not appear before the deadline"
                )

        event_options = detected_event["options"]
        selected_event_option, option_score, score_reasons = (
            _choose_generic_event_option(detected_event)
        )
        option_number = int(selected_event_option["option_number"])
        key, scan_code = EVENT_OPTION_SHORTCUTS[option_number]
        control_id = f"ordinary_event.option_{option_number}"
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": control_id,
                "event_index": event_index,
                "key": key,
                "scan_code": scan_code,
                "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
                "expected_post_screen": "map",
            },
        )
        accepted, last_error = _prepare_key_chord_batch(
            CK3_SHORTCUT_SCAN_CODES["left_shift"], scan_code
        )()
        if accepted != 4:
            raise AgentError(
                f"{key} ordinary-event shortcut SendInput was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )

        post_driver = new_driver()
        post_state = None
        running_error: AgentError | None = None
        try:
            post_state = post_driver.observe_stable(
                "map_running",
                min(
                    8.0,
                    _remaining(deadline, "ordinary event running postcondition"),
                ),
                stable_frames=2,
            )
        except AgentError as error:
            running_error = error
        if post_state is None:
            try:
                post_state = post_driver.observe_stable(
                    "map_hud",
                    min(
                        8.0,
                        _remaining(deadline, "ordinary event paused postcondition"),
                    ),
                    stable_frames=2,
                )
            except AgentError:
                if running_error is not None:
                    raise running_error
                raise
        result_observation_id = post_state.observation_id
        result_screen = post_state.screen
        post_candidate = _generic_event_in_frame(post_state.latest)
        if post_candidate is not None:
            pending_event, transition_frame = _confirm_post_shortcut_event(
                post_driver,
                post_candidate,
                min(deadline, time.monotonic() + 8.0),
            )
            result_observation_id = getattr(
                transition_frame, "observation_id", result_observation_id
            )
            if pending_event is not None:
                if pending_event.get("title") == detected_event.get("title"):
                    raise AgentError(
                        "ordinary CK3 event remained visible after its shortcut"
                    )
                result_screen = "ordinary_event"

        ordinary_action = {
            "control_id": control_id,
            "status": "confirmed",
            "input_kind": "keyboard_shortcut",
            "key": key,
            "scan_code": scan_code,
            "modifier_scan_code": CK3_SHORTCUT_SCAN_CODES["left_shift"],
            "send_input": {
                "requested": 4,
                "accepted": accepted,
                "last_error": last_error,
            },
            "event_index": event_index,
            "event_title": detected_event["title"],
            "visible_option": selected_event_option["visible_text"],
            "visible_option_count": len(event_options),
            "strategy_score": option_score,
            "strategy_reasons": score_reasons,
            "source_observation_id": detected_event["observation_id"],
            "result_observation_id": result_observation_id,
            "expected_post_screen": result_screen,
        }
        actions.append(ordinary_action)
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": control_id,
                "event_index": event_index,
                "result_screen": result_screen,
                "result_observation_id": result_observation_id,
            },
        )
        ordinary_events.append(
            {
                "event_index": event_index,
                "title": detected_event["title"],
                "visible_options": event_options,
                "selected_option_number": option_number,
                "selected_visible_text": selected_event_option["visible_text"],
                "strategy_score": option_score,
                "strategy_reasons": score_reasons,
                "strategy": "visible-option-utility-v1",
                "source_observation_id": detected_event["observation_id"],
            }
        )
        if (
            pending_event is None
            and event_index < ordinary_event_count
            and post_state.screen == "map_hud"
        ):
            press_shortcut(
                "map_hud",
                "map_hud.resume",
                "space",
                CK3_SHORTCUT_SCAN_CODES["space"],
                "map_running",
                f"running timeline after ordinary event {event_index}",
                driver=post_driver,
                stable=post_state,
                post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
            )

    if post_driver is None or post_state is None:
        raise AgentError("ordinary CK3 event loop produced no final state")
    if post_state.screen == "map_running":
        final_observation = press_shortcut(
            "map_running",
            "map_running.pause",
            "space",
            CK3_SHORTCUT_SCAN_CODES["space"],
            "map_hud",
            "paused after ordinary event loop",
            driver=post_driver,
            stable=post_state,
            post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        )
    else:
        final_observation = post_state.to_policy_json()
    map_panels: dict[str, dict[str, object]] = {}
    if inspect_map_panels:
        for panel_id, title, key, scan_code in MAP_PANEL_SHORTCUTS:
            summary, final_observation = inspect_map_panel(
                panel_id,
                title,
                key,
                scan_code,
            )
            map_panels[panel_id] = summary
    economic_building = None
    if construct_economic_building:
        economic_building, final_observation = construct_first_economic_building()
    steward_development = None
    if assign_steward_development:
        steward_development, final_observation = (
            assign_steward_to_develop_foggia()
        )
    paused_date = _extract_map_date(final_observation)
    if int(paused_date["ordinal"]) < int(running_date["ordinal"]):
        raise AgentError("paused map date moved backwards")
    return {
        "character": "Robert the Fox, Duke of Apulia",
        "bookmark": "1066",
        "actions": actions,
        "first_blessing_choice": {
            "control_id": selected.control_id,
            "visible_text": visible_text,
            "strategy_score": strategy_score,
            "strategy": "growth100.first-blessing-visible-v1",
        },
        "first_curse_choice": {
            "control_id": curse_selected.control_id,
            "visible_text": curse_text,
            "strategy_loss": curse_loss,
            "strategy": "growth100.first-curse-visible-v1",
        },
        "player_character_state": player_state,
        "lifestyle_state": lifestyle_state,
        "first_ordinary_event": ordinary_events[0],
        "ordinary_events": ordinary_events,
        "map_panels": map_panels,
        "economic_building": economic_building,
        "steward_development": steward_development,
        "time_progression": {
            "strategy": "speed-five-visible-date-v1",
            "starting_date": starting_date,
            "running_date": running_date,
            "paused_date": paused_date,
            "elapsed_days": int(paused_date["ordinal"])
            - int(starting_date["ordinal"]),
            "policy_boundary": "player-visible OCR and rendered timeline controls only",
        },
        "final_screen": final_observation.get("screen"),
        "final_observation_id": final_observation.get("observation_id"),
        "window_binding": window.audit_binding(),
        "foreground_activation": foreground,
    }


def opening_smoke(
    spec: EnvironmentSpec,
    timeout_seconds: float = 900,
    ordinary_event_count: int = DEFAULT_ORDINARY_EVENT_COUNT,
) -> dict[str, object]:
    """Complete Robert's opening and answer several ordinary CK3 events."""
    ensure_state_path_safe(spec.state_dir)
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise AgentError("opening timeout must be finite and positive")
    if (
        isinstance(ordinary_event_count, bool)
        or not isinstance(ordinary_event_count, int)
        or not 1 <= ordinary_event_count <= 10
    ):
        raise AgentError("ordinary event count must be an integer from 1 to 10")
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "opening-smoke"):
            manifest = verify_profile(spec)
            doctor(spec, require_prepared=True)
            if ck3_process_inventory()["processes"]:
                raise AgentError("refusing opening smoke while CK3 is already running")
            return _opening_smoke_locked(
                spec,
                manifest,
                float(timeout_seconds),
                ordinary_event_count,
            )


def opening_step(
    spec: EnvironmentSpec,
    step: str = "steward-development",
    timeout_seconds: float = 240,
) -> dict[str, object]:
    """Resume the isolated autosave and exercise one development-only step."""
    ensure_state_path_safe(spec.state_dir)
    if step not in OPENING_DEVELOPMENT_STEPS:
        raise AgentError(f"unsupported opening development step: {step}")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise AgentError("opening step timeout must be finite and positive")
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "opening-step"):
            manifest = verify_profile(spec)
            doctor(spec, require_prepared=True)
            if ck3_process_inventory()["processes"]:
                raise AgentError("refusing opening step while CK3 is already running")
            save_root = spec.profile_dir / "save games"
            if not any(save_root.glob("autosave*.ck3")):
                raise AgentError("opening step requires an isolated autosave")
            return _opening_smoke_locked(
                spec,
                manifest,
                float(timeout_seconds),
                0,
                resume_step=step,
            )


def _reload_opening_development_policy():
    """Reload perception and gameplay policy while the owned CK3 process stays up."""
    importlib.invalidate_caches()
    for name in (
        "xar_autoplayer.vision.ocr",
        "xar_autoplayer.vision.classifier",
        "xar_autoplayer.vision.window",
        "xar_autoplayer.vision",
        "xar_autoplayer.control.executor",
        "xar_autoplayer.control",
        "xar_autoplayer.strategy",
    ):
        module = sys.modules.get(name)
        if module is not None:
            importlib.reload(module)
    return importlib.reload(sys.modules[__name__])


def opening_dev_session(
    spec: EnvironmentSpec,
    timeout_seconds: float = 21600,
) -> dict[str, object]:
    """Keep one isolated CK3 process alive and hot-reload gameplay steps from stdin."""
    ensure_state_path_safe(spec.state_dir)
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise AgentError("opening dev-session timeout must be finite and positive")
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "opening-dev-session"):
            manifest = verify_profile(spec)
            doctor(spec, require_prepared=True)
            if ck3_process_inventory()["processes"]:
                raise AgentError(
                    "refusing opening dev session while CK3 is already running"
                )
            save_root = spec.profile_dir / "save games"
            if not any(save_root.glob("autosave*.ck3")):
                raise AgentError("opening dev session requires an isolated autosave")
            return _opening_dev_session_locked(
                spec, manifest, float(timeout_seconds)
            )


def _opening_dev_session_locked(
    spec: EnvironmentSpec,
    manifest: dict[str, object],
    timeout_seconds: float,
) -> dict[str, object]:
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-dev-session-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    artifacts.mkdir(parents=True, exist_ok=False)
    report_path = run_dir / "report.json"
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_id,
        "kind": "ck3_opening_development_session",
        "started_at": utc_now(),
        "environment_sha256": manifest.get("environment_sha256"),
        "development_only": True,
        "release_qualification": False,
        "commands": [],
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(report_path, report)
    append_event(
        events,
        {
            "kind": "opening_dev_session_started",
            "environment_sha256": manifest.get("environment_sha256"),
        },
    )
    deadline = time.monotonic() + timeout_seconds
    handle: SessionHandle | None = None
    primary_error: BaseException | None = None
    try:
        log("launching one persistent CK3 development session")
        handle = launch(spec)
        report["process"] = {
            "pid": int(handle.process.pid),
            "creation_date": handle.ck3_creation_date,
        }
        append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
        report["load_attestation"] = wait_for_runtime_attestation(
            spec,
            handle,
            _remaining(deadline, "runtime load attestation"),
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
        initial_contract = run_dir / "opening-ui-contract-initial.json"
        shutil.copy2(OPENING_CONTRACT, initial_contract)
        initial_contract_sha256 = sha256_file(initial_contract)
        report["resume"] = _drive_opening(
            spec,
            handle,
            manifest,
            artifacts,
            events,
            initial_contract,
            initial_contract_sha256,
            deadline,
            ordinary_event_count=0,
            development_step=None,
            resume_saved_game=True,
        )
        write_json_atomic(report_path, report)
        print(
            json.dumps(
                {
                    "type": "opening_dev_session_ready",
                    "run_id": run_id,
                    "pid": handle.process.pid,
                    "commands": [
                        *OPENING_DEVELOPMENT_STEPS,
                        "strategy-review",
                        "status",
                        "stop",
                    ],
                    "hot_reload": True,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        command_index = 0
        while time.monotonic() < deadline:
            line = sys.stdin.readline()
            if line == "":
                break
            command = line.strip()
            if not command:
                continue
            if command == "stop":
                break
            if command == "status":
                print(
                    json.dumps(
                        {
                            "type": "opening_dev_session_status",
                            "run_id": run_id,
                            "pid": handle.process.pid,
                            "running": handle.process.poll() is None,
                            "command_count": len(report["commands"]),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                continue
            command_index += 1
            command_record: dict[str, object] = {
                "index": command_index,
                "command": command,
                "started_at": utc_now(),
                "ok": False,
            }
            try:
                policy = _reload_opening_development_policy()
                if command == "strategy-review":
                    command_record["result"] = policy.read_one_life_strategy(
                        spec.state_dir
                    )
                else:
                    command_contract = (
                        run_dir / f"opening-ui-contract-command-{command_index}.json"
                    )
                    shutil.copy2(policy.OPENING_CONTRACT, command_contract)
                    command_contract_sha256 = policy.sha256_file(command_contract)
                    command_record["contract_sha256"] = command_contract_sha256
                    command_record["result"] = policy._drive_opening(
                        spec,
                        handle,
                        manifest,
                        artifacts,
                        events,
                        command_contract,
                        command_contract_sha256,
                        deadline,
                        ordinary_event_count=0,
                        development_step=command,
                        resume_saved_game=False,
                    )
                command_record["ok"] = True
            except Exception as error:
                command_record["error"] = f"{type(error).__name__}: {error}"
            command_record["finished_at"] = utc_now()
            report["commands"].append(command_record)
            write_json_atomic(report_path, report)
            print(
                json.dumps(
                    {
                        "type": "opening_dev_command_result",
                        "command": command,
                        "index": command_index,
                        "ok": command_record["ok"],
                        "error": command_record.get("error"),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    except BaseException as error:
        primary_error = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if handle is not None:
            try:
                report["shutdown_attestation"] = stop_tracked(
                    handle, require_running=primary_error is None
                )
            except BaseException as error:
                report["shutdown_error"] = f"{type(error).__name__}: {error}"
                if primary_error is None:
                    primary_error = error
        report["finished_at"] = utc_now()
        report["ok"] = primary_error is None
        report["finalized"] = True
        append_event(
            events,
            {"kind": "opening_dev_session_finished", "ok": report["ok"]},
        )
        write_json_atomic(report_path, report)
    if primary_error is not None:
        if not isinstance(primary_error, Exception):
            raise primary_error
        raise AgentError(
            f"opening dev session failed; report={report_path}: {primary_error}"
        ) from primary_error
    return report


def _opening_smoke_locked(
    spec: EnvironmentSpec,
    manifest: dict[str, object],
    timeout_seconds: float,
    ordinary_event_count: int,
    resume_step: str | None = None,
) -> dict[str, object]:
    run_kind = "step" if resume_step is not None else "opening"
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-{run_kind}-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    artifacts.mkdir(parents=True, exist_ok=False)
    contract_archive = run_dir / "opening-ui-contract.json"
    shutil.copy2(OPENING_CONTRACT, contract_archive)
    contract_sha256 = sha256_file(contract_archive)
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_id,
        "kind": (
            "ck3_opening_development_step"
            if resume_step is not None
            else "ck3_opening_smoke"
        ),
        "started_at": utc_now(),
        "environment_sha256": manifest.get("environment_sha256"),
        "contract": {
            "path": contract_archive.name,
            "sha256": contract_sha256,
        },
        "ordinary_event_target": ordinary_event_count,
        "finalized": False,
        "ok": False,
    }
    if resume_step is not None:
        report.update(
            {
                "development_only": True,
                "release_qualification": False,
                "step": resume_step,
            }
        )
    report_path = run_dir / "report.json"
    write_json_atomic(report_path, report)
    append_event(
        events,
        {
            "kind": "opening_started",
            "environment_sha256": manifest.get("environment_sha256"),
            "contract_sha256": contract_sha256,
        },
    )
    deadline = time.monotonic() + timeout_seconds
    handle: SessionHandle | None = None
    primary_error: BaseException | None = None
    try:
        log(
            "launching CK3 for isolated saved-game step"
            if resume_step is not None
            else "launching CK3 for Robert 1066 opening"
        )
        handle = launch(spec)
        report["process"] = {
            "pid": int(handle.process.pid),
            "creation_date": handle.ck3_creation_date,
        }
        append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
        report["load_attestation"] = wait_for_runtime_attestation(
            spec,
            handle,
            _remaining(deadline, "runtime load attestation"),
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
        report["opening"] = _drive_opening(
            spec,
            handle,
            manifest,
            artifacts,
            events,
            contract_archive,
            contract_sha256,
            deadline,
            ordinary_event_count,
            True,
            True,
            True,
            resume_step,
            resume_step is not None,
        )
    except BaseException as error:
        primary_error = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if handle is not None:
            try:
                shutdown = stop_tracked(
                    handle, require_running=primary_error is None
                )
                report["shutdown_attestation"] = shutdown
                if shutdown.get("ok") is not True and primary_error is None:
                    primary_error = AgentError(
                        "opening shutdown contract failed: "
                        + "; ".join(
                            str(item)
                            for item in shutdown.get("contract_errors", [])
                        )
                    )
                    report["error"] = str(primary_error)
            except BaseException as error:
                report["shutdown_error"] = f"{type(error).__name__}: {error}"
                if primary_error is None:
                    primary_error = error
        report["finished_at"] = utc_now()
        report["ok"] = primary_error is None
        report["finalized"] = True
        append_event(
            events,
            {
                "kind": "opening_finished",
                "ok": report["ok"],
                "final_screen": (
                    report.get("opening", {}).get("final_screen")
                    if isinstance(report.get("opening"), dict)
                    else None
                ),
            },
        )
        write_json_atomic(report_path, report)
    if primary_error is not None:
        if not isinstance(primary_error, Exception):
            raise primary_error
        raise AgentError(
            f"opening {run_kind} failed; report={report_path}: {primary_error}"
        ) from primary_error
    return report
