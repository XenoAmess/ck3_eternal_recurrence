"""Drive Robert 1066 through the opening pact and first map decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path
import re
import shutil
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
GENERIC_EVENT_PREVIEW_REGION = (0.23, 0.22, 0.48, 0.80)

# CK3 1.19.0.6 at the frozen 2560x1440/100% UI contract.  Alt+1..N only
# addresses existing GUIBuildingItem tracks; the empty ``+`` slots are not in
# that shortcut model.  The rightmost empty slot is therefore the one
# unavoidable layout-derived mouse target in the construction flow.
HOLDING_EMPTY_BUILDING_SLOT_CENTER = (608, 1118)

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
        "kin_count": visible_count("亲族"),
        "courtier_count": visible_count("廷臣"),
        "vassal_count": visible_count("臣属"),
        "source_observation_id": observation.get("observation_id"),
        "policy_boundary": "player-visible OCR only",
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


def _generic_event_preview(window: object, sequence: int) -> dict[str, object] | None:
    """Check the event lane without persisting ordinary map polling frames."""
    from .vision.ocr import ocr_spans

    image = window.capture()
    width, height = image.size
    return _generic_event_in_frame(
        SimpleNamespace(
            observation_id=None,
            capture_sequence=sequence,
            client_rect=(0, 0, width, height),
            spans=ocr_spans(image, GENERIC_EVENT_PREVIEW_REGION),
        )
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


def _building_offer_summaries(frame: object) -> list[dict[str, object]]:
    """Rank visible construction rows by player-visible economic language."""
    buttons = _spans_with_text(frame, "建造")
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
) -> dict[str, object]:
    from .control import VisibleUiDriver
    from .control.executor import (
        _prepare_key_chord_batch,
        _prepare_key_press_batch,
        _prepare_left_click_batch,
    )
    from .vision import load_ui_contract

    display = manifest.get("display")
    if not isinstance(display, dict):
        raise AgentError("prepared display contract is missing")
    language = str(display.get("language", ""))
    contract = load_ui_contract(contract_path, expected_sha256=contract_sha256)
    window = _bind_window(spec, handle, deadline)
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
                "control_id": "holding_view.rightmost_empty_building_slot",
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
        selected_slot = "rightmost_empty"
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
                "control_id": "holding_view.rightmost_empty_building_slot",
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
                "control_id": "holding_view.rightmost_empty_building_slot",
                "result_screen": "building_selection",
                "result_observation_id": building_frame.observation_id,
            },
        )

        offer = _choose_economic_building_offer(building_frame)
        button_center = tuple(offer["button_center"])

        def construction_started(frame: object) -> bool:
            return bool(_spans_with_text(frame, "正在修建", contains=True))

        button_candidates = [
            item
            for item in _spans_with_text(building_frame, "建造")
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
            text="建造",
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
                if _generic_event_preview(window, preview_sequence) is None:
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


def _opening_smoke_locked(
    spec: EnvironmentSpec,
    manifest: dict[str, object],
    timeout_seconds: float,
    ordinary_event_count: int,
) -> dict[str, object]:
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-opening-"
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
        "kind": "ck3_opening_smoke",
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
        log("launching CK3 for Robert 1066 opening")
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
            f"opening smoke failed; report={report_path}: {primary_error}"
        ) from primary_error
    return report
