"""Illustrated help-request frames with explicit allegiance and state history.

This renderer consumes authored teaching cues, never a live game observation.
Three phases per cue reveal inputs, comparisons and scoped results. Unit positions
stay fixed throughout; friendly assignment arrows preserve the r2 correction.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from .common import font, lines
from .visuals import BG, BLUE, GOLD, GREEN, INK, MUTED, PANEL, RED
from .visuals import arrow, box, castle, text


SIZE = (2560, 1440)
SUBTITLE_TOP = 1120
MAP_BOUNDS = (112, 314, 1400, 1064)
CARD_LEFT = 1456
CARD_RIGHT = 2448
REQUESTER = (640, 665)
ASSISTANT = (315, 566)
PROVINCE = (505, 562, 780, 821)
ON_FILL = "#244B42"
OFF_FILL = "#26343F"
FAINT = "#3A4C59"
TITLES = {
    24: "什么时候开始求援？",
    25: "情况好转了，为什么还在求援？",
    26: "同样的 0.70，为什么结果不同？",
    27: "什么时候停止求援？",
    28: "发出请求，就会有人来吗？",
    29: "这能解释我的盟友为什么不来吗？",
}
BEATS = {
    24: ("普通 AI 求援：先看此前状态", "此前没有请求；假设 ratio = 0.65", "这只是输入，还不是援军到达", "开始门：ratio < 0.66", "0.65 通过开始门，请求亮起", "发出请求，不保证助手立即到达"),
    25: ("此前已经求援，先保留这段历史", "假设情况改善：ratio = 0.70", "现在还应该继续亮灯吗？", "已有请求，使用继续门 0.75", "0.70 < 0.75，所以继续", "开始门与继续门不同"),
    26: ("同样的 0.70，同时摆出两种历史", "此前未求援：不开始", "此前已求援：继续", "暂时只看先前请求状态", "相同输入，因为历史不同而走不同门", "这是两组对照，不是同一军队移动两次"),
    27: ("此前已求援；假设 ratio = 0.76", "0.76 不低于继续门 0.75", "停止继续求援", "0.65 开始 → 0.70 继续", "0.76 停止", "三状态是逻辑演示，不是按日采样"),
    28: ("先有请求，再看能否匹配", "按已有顺序找符合条件的请求者", "这个 helper 不做最短 ETA 排榜", "乙若匹配到甲，先取得甲当前所在省", "箭头连接同属赤河的候选助手与请求者", "目标指派不等于已经行军或最终到达"),
    29: ("这一段讲的是普通 AI 军队之间", "玩家专用支援要另看路径", "不能直接复制普通求援结论", "玩家支援的部分消费路径仍未闭合", "未知不能解释成故意不来", "到这里收束规则，保留玩家支援边界"),
}


def _center(draw, center_x, y, value, size=34, fill=INK, bold=False):
    face = font(size, bold)
    draw.text((center_x - face.getlength(value) / 2, y), value,
              font=face, fill=fill)


def _paragraph(draw, xy, value, width, size=33, fill=INK, bold=False):
    """Use the shared wrapping policy while keeping card copy compact."""
    for i, line in enumerate(lines(value, size, width, bold)):
        text(draw, (xy[0], xy[1] + i * size * 1.35), line,
             size, fill, bold)


def _lamp(draw, xy, active, label, radius=18, label_size=31):
    x, y = xy
    color = GREEN if active else MUTED
    draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                 fill=GREEN if active else OFF_FILL, outline=color, width=3)
    if active:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=INK)
    else:
        draw.line((x - 8, y, x + 8, y), fill=MUTED, width=3)
    text(draw, (x + radius + 15, y - label_size * .65), label,
         label_size, color, True)


def _unit(draw, xy, label, role, solid):
    x, y = xy
    draw.ellipse((x - 33, y - 33, x + 33, y + 33),
                 fill=RED if solid else PANEL, outline=RED, width=5)
    _center(draw, x, y - 27, label, 38, BG if solid else RED, True)
    _center(draw, x, y + 51, role, 33, RED, True)


def _map(draw, shot, phase, cue):
    box(draw, MAP_BOUNDS, "#152635", FAINT)
    text(draw, (153, 337), "虚构教学地图", 29, MUTED)
    text(draw, (153, 396), "赤河 · 我方", 37, RED, True)
    text(draw, (1035, 396), "蓝岭 · 对手", 37, BLUE, True)

    for i in range(6):
        y = 496 + i * 82
        draw.line([(153, y), (445, y - 24), (755, y + 14),
                   (1010, y - 17), (1355, y + 12)], fill="#213744", width=2)
    river = [(849, 382), (811, 480), (867, 590), (835, 718),
             (888, 837), (854, 966)]
    draw.line(river, fill="#365E72", width=29, joint="curve")
    draw.line(river, fill="#5A8A9D", width=4, joint="curve")
    for x in (705, 748):
        draw.polygon([(x - 25, 455), (x, 404), (x + 25, 455)],
                     fill="#3D4B50")
    text(draw, (697, 464), "山口", 26, MUTED)
    box(draw, (1125, 465, 1360, 522), "#32404B")
    text(draw, (1172, 474), "第三国", 28, MUTED)

    castle(draw, 335, 861, RED)
    _center(draw, 335, 919, "赤渡堡", 31, RED)
    castle(draw, 1170, 761, BLUE)
    _center(draw, 1170, 819, "蓝岭堡", 31, BLUE)
    draw.polygon([(1095, 588), (1126, 623), (1095, 658), (1064, 623)],
                 fill=BLUE)
    _center(draw, 1095, 673, "蓝岭军队", 31, BLUE, True)

    province_focused = shot == 28 and (phase == 1 or cue.endswith("056"))
    box(draw, PROVINCE, "#263540" if province_focused else "#1B2E3D",
        GOLD if province_focused else FAINT)
    _unit(draw, REQUESTER, "甲", "请求者甲", True)
    _unit(draw, ASSISTANT, "乙", "候选助手乙", False)
    _center(draw, 640, 778, "甲当前所在省", 27,
            GOLD if province_focused else MUTED)

    # Only an assignment illustration may connect the two friendly units.
    # Its endpoint is the requester's province, not the hostile blue army.
    if shot == 28 and (phase == 1 or cue.endswith("056")):
        arrow(draw, (357, 593), (521, 639), GOLD, 7)
        text(draw, (161, 735), "假设乙匹配到甲", 29, GOLD, True)
        text(draw, (161, 780), "只标帮助目标，不表示已经行军", 24, MUTED)

    box(draw, (152, 980, 1360, 1042), "#1C303C")
    text(draw, (174, 994), "甲、乙同属赤河；蓝岭是对手。位置始终不变。", 29, INK)


def _state_card(draw, y, prior, expression, result, active, focus,
                caption=None, emphasize="result"):
    bounds = (CARD_LEFT, y, CARD_RIGHT, y + 213)
    outline = GOLD if focus else FAINT
    box(draw, bounds, ON_FILL if active and focus else PANEL, outline)
    text(draw, (CARD_LEFT + 29, y + 18), prior, 35,
         GOLD if focus and emphasize == "prior" else MUTED, True)
    text(draw, (CARD_LEFT + 29, y + 81), expression, 61,
         GOLD if focus and emphasize == "ratio" else INK, True)
    _lamp(draw, (CARD_LEFT + 661, y + 111), active, result,
          radius=19, label_size=34)
    if caption:
        text(draw, (CARD_LEFT + 29, y + 166), caption, 26, MUTED)


def _note(draw, title, body, top=893, color=GOLD):
    box(draw, (CARD_LEFT, top, CARD_RIGHT, 1064), "#1B303C", color)
    text(draw, (CARD_LEFT + 29, top + 18), title, 33, color, True)
    _paragraph(draw, (CARD_LEFT + 29, top + 74), body, 925, 28, MUTED)


def _input_result(draw, shot, phase, cue):
    is_start = shot == 24
    establish = cue.endswith("047") or cue.endswith("049")
    prior = "此前没有求援" if is_start else "此前已经求援"
    value = "0.65" if is_start else "0.70"
    threshold = "0.66" if is_start else "0.75"
    text(draw, (CARD_LEFT + 16, 333), "普通军队之间的求援", 35, GOLD, True)
    if establish:
        box(draw, (CARD_LEFT, 409, CARD_RIGHT, 596), PANEL,
            GOLD if phase == 0 else FAINT)
        text(draw, (CARD_LEFT + 29, 432), "先看此前状态", 30, MUTED)
        text(draw, (CARD_LEFT + 29, 491), prior, 51,
             GOLD if phase == 0 else INK, True)
        _lamp(draw, (CARD_LEFT + 665, 526), not is_start,
              "灯灭" if is_start else "灯亮", label_size=34)
        box(draw, (CARD_LEFT, 632, CARD_RIGHT, 848), PANEL,
            GOLD if phase == 1 else FAINT)
        text(draw, (CARD_LEFT + 29, 652), "本次假设输入", 32, MUTED)
        shown_value = "待给出" if is_start and phase == 0 else value
        text(draw, (CARD_LEFT + 29, 713), shown_value, 58 if shown_value == "待给出" else 80,
             GOLD if phase == 1 else INK, True)
        text(draw, (CARD_LEFT + 320, 751), "接下来会怎样？", 37, INK)
        _note(draw, "先确定此前是否已经求援" if phase == 0 else
              "把本次比值与此前状态一起看",
              "数字是教学输入；求援灯只表示请求状态。")
    else:
        _state_card(draw, 415, prior, f"{value} < {threshold}",
                    "开始求援" if is_start else "继续求援", True,
                    phase == 1, "符合当前分支的严格小于条件",
                    "ratio" if phase == 0 else "result")
        box(draw, (CARD_LEFT, 665, CARD_RIGHT, 849), PANEL,
            GOLD if phase == 0 else GREEN)
        text(draw, (CARD_LEFT + 29, 687),
             "本次检查" if phase == 0 else "本次请求状态", 30, MUTED)
        text(draw, (CARD_LEFT + 29, 744),
             "开始用 0.66 这道门" if is_start and phase == 0 else
             "继续用 0.75 这道门" if phase == 0 else
             "请求灯亮，不代表助手已经行动", 39,
             GOLD if phase == 0 else GREEN, True)
        _note(draw, "强度比不能读成胜率",
              "只展示普通求援分支；没有承诺援军一定到达。")


def _comparison(draw, phase, cue):
    explaining_history = cue.endswith("052")
    emphasis = "ratio" if explaining_history and phase == 0 else "prior"
    headline = ("当前比值相同" if phase == 0 else "改变的，是此前状态") if explaining_history else (
        "先看：此前没有求援" if phase == 0 else "再看：此前已经求援")
    text(draw, (CARD_LEFT + 16, 333), headline, 40, GOLD, True)
    _state_card(draw, 417, "此前未求援", "0.70 不低于 0.66", "不开始",
                False, phase == 0, "没有达到开始求援的条件", emphasis)
    _state_card(draw, 653, "此前已求援", "0.70 < 0.75", "继续求援",
                True, phase == 1, "仍符合继续求援的条件", emphasis)
    _note(draw,
          "同一个数字，两种明确结果" if phase == 0 else "求援状态也要带上历史",
          "这两张卡是条件对照，不是军队连续移动的记录。")


def _stop(draw, phase, cue):
    recap = cue.endswith("054")
    text(draw, (CARD_LEFT + 16, 333),
         ("开始、维持、停止" if phase == 0 else "这是状态顺序，不是日期")
         if recap else "此前已求援，本次变为 0.76",
         37, GOLD, True)
    if not recap:
        _state_card(draw, 415, "此前已经求援", "0.76 不低于 0.75",
                    "停止求援", False, phase == 1,
                    "本次不再满足继续条件", "ratio")
        box(draw, (CARD_LEFT, 665, CARD_RIGHT, 849), PANEL,
            GOLD if phase == 0 else MUTED)
        text(draw, (CARD_LEFT + 29, 689),
             "先检查继续条件" if phase == 0 else "停止的是请求状态", 41, INK, True)
        text(draw, (CARD_LEFT + 29, 764),
             "严格小于 0.75 才继续" if phase == 0 else "没有演出军队移动或撤退", 35, MUTED)
        _note(draw, "前态明确，才知道本次走哪道门",
              "灯灭说明这一求援状态结束；不代表战斗结果。")
    else:
        for i, (number, label, lit) in enumerate([
            ("0.65", "开始求援", True),
            ("0.70", "继续求援", True),
            ("0.76", "停止求援", False),
        ]):
            top = 418 + i * 143
            box(draw, (CARD_LEFT, top, CARD_RIGHT, top + 120), PANEL,
                GOLD if phase == 0 else FAINT)
            text(draw, (CARD_LEFT + 30, top + 22), number, 60, INK, True)
            _lamp(draw, (CARD_LEFT + 353, top + 64), lit, label, label_size=37)
        _note(draw, "三次假设求值，不是连续三天",
              "状态箭头不附带固定刷新日程；此处没有连续实机采样。",
              color=GOLD if phase else FAINT)


def _matching(draw, phase, cue):
    province_cue = cue.endswith("056")
    focused = 2 if province_cue else phase
    text(draw, (CARD_LEFT + 16, 333), "请求与匹配，是不同步骤", 38, GOLD, True)
    entries = [
        ("甲提出请求", "求援灯亮，不代表乙已经出发"),
        ("按已有顺序寻找合格请求者", "不是把对象按最短到达时间重排"),
        ("帮助目标是甲当时所在的省", "箭头只解释目标绑定，棋子没有移动"),
    ]
    for i, (title, body) in enumerate(entries):
        y = 418 + i * 151
        box(draw, (CARD_LEFT, y, CARD_RIGHT, y + 131), PANEL,
            GOLD if i == focused else FAINT)
        text(draw, (CARD_LEFT + 28, y + 18), title, 37,
             GOLD if i == focused else INK, True)
        text(draw, (CARD_LEFT + 28, y + 77), body, 28, MUTED)
    _note(draw,
          "更早的步骤，仍可能考察距离" if province_cue and phase == 1 else
          "箭头始终连接同属赤河的两支军队",
          "蓝岭是对手；本图没有向敌人求援，也不保证未来到达。",
          color=GREEN if province_cue and phase == 1 else GOLD)


def _player_boundary(draw, phase):
    text(draw, (CARD_LEFT + 16, 333),
         "先看已经讲清楚的普通求援" if phase == 0 else "再看仍有未知的玩家支援",
         38, GOLD, True)
    for i, (y, title, body, color) in enumerate([
        (430, "普通军队之间", "本段已讲的求援条件", GREEN),
        (667, "电脑支援玩家", "专用路径仍有未明部分", GOLD),
    ]):
        box(draw, (CARD_LEFT, y, CARD_RIGHT, y + 193), PANEL,
            color if phase == i else FAINT)
        text(draw, (CARD_LEFT + 29, y + 25), title, 49,
             color if phase == i else INK, True)
        text(draw, (CARD_LEFT + 29, y + 106), body, 34, MUTED)
    _note(draw, "未知不能替换成“故意不来”",
          "普通求援链还不能回答玩家盟友行为的全部问题。")


def make_help_frame(row, destination, phase):
    """Write one new PNG for a help cue using the existing frame signature."""
    if row.get("chapter_id") != "help":
        raise ValueError("make_help_frame only accepts help chapter rows")
    shot = int(row["shot_id"].split("-")[-1])
    if shot not in TITLES or phase not in (0, 1, 2):
        raise ValueError("Expected help shot S30-24..29 and phase 0, 1, or 2")
    from .teaching_visuals import beat_index, fit
    beat = beat_index(row, phase)
    focus = min(phase, 1)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)

    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, SIZE[0], 10), fill=GOLD)
    text(draw, (112, 65), "CK3 / 原生战争 AI", 30, GOLD, True)
    text(draw, (1660, 65), "HELP REQUESTS / 假设教学输入", 29, MUTED)
    text(draw, (112, 144), TITLES[shot], 67, INK, True, width=2300)
    fit(draw, (115, 244, 2420, 290), BEATS[shot][beat], 30, GOLD, True)
    for i in range(6):
        draw.rounded_rectangle((112 + i * 390, 298, 465 + i * 390, 306), radius=4,
                               fill=GOLD if i <= beat else FAINT)
    cue = str(row.get("id", ""))
    _map(draw, shot, focus, cue)
    if shot in (24, 25):
        _input_result(draw, shot, focus, cue)
    elif shot == 26:
        _comparison(draw, focus, cue)
    elif shot == 27:
        _stop(draw, focus, cue)
    elif shot == 28:
        _matching(draw, focus, cue)
    else:
        _player_boundary(draw, focus)
    if phase == 2:
        # Final emphasis is a local annotation, never a fictitious movement.
        draw.ellipse((592, 617, 688, 713), outline=GOLD, width=4)
        box(draw, (152, 980, 1360, 1042), "#263B46", GOLD)
        fit(draw, (174, 990, 1340, 1037),
            "甲、乙同属赤河；请求、匹配、到达分别判断。", 28, INK)

    text(draw, (112, 1081), "CK3 1.19.0.6 · 虚构教学图", 24, MUTED)
    text(draw, (1710, 1081), "PRIOR STATE / CONDITION / RESULT", 22, MUTED)
    draw.line((112, SUBTITLE_TOP - 4, 2448, SUBTITLE_TOP - 4), fill=FAINT, width=2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        image.save(stream, format="PNG")
