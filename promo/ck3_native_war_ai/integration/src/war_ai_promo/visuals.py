"""The film's illustrated map, candidate cards, thresholds and peace ledgers."""
from pathlib import Path
import math

from PIL import Image, ImageDraw
from xar_promo.process import CommandSpec, run_command

from .common import font, lines

BG = "#101C29"
PANEL = "#1B2B3A"
INK = "#EBE8DA"
MUTED = "#A1B2BB"
GOLD = "#D7B574"
RED = "#D18176"
BLUE = "#77ACD4"
GREEN = "#8EC9AA"


def text(draw, xy, value, size=44, fill=INK, bold=False, width=None):
    wrapped = lines(value, size, width, bold) if width else [value]
    for i, line in enumerate(wrapped):
        draw.text((xy[0], xy[1] + i * size * 1.35), line, font=font(size, bold), fill=fill)


def box(draw, bounds, color=PANEL, outline=None):
    draw.rounded_rectangle(bounds, radius=22, fill=color, outline=outline, width=3)


def arrow(draw, a, b, color=GOLD, width=7):
    draw.line([a, b], fill=color, width=width)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    tip = [b] + [(b[0] - 25 * math.cos(angle + d), b[1] - 25 * math.sin(angle + d)) for d in (-.5, .5)]
    draw.polygon(tip, fill=color)


def castle(draw, x, y, color):
    draw.rectangle((x - 32, y - 24, x + 32, y + 36), fill=color)
    for dx in (-38, 22):
        draw.rectangle((x + dx, y - 44, x + dx + 16, y + 36), fill=color)
    draw.rectangle((x - 10, y + 5, x + 10, y + 36), fill=BG)


def map_panel(draw, focus=0):
    box(draw, (112, 315, 1420, 1070), color="#152635", outline="#314452")
    text(draw, (155, 345), "赤河与蓝岭", 34, GOLD, True)
    text(draw, (990, 350), "虚构教学地图", 28, MUTED)
    for offset in range(7):
        y = 470 + offset * 73
        draw.line([(155, y), (410, y - 24), (630, y + 16), (1000, y - 34), (1360, y + 10)], fill="#213744", width=2)
    river = [(790, 398), (755, 500), (850, 605), (800, 735), (895, 850), (860, 1005)]
    draw.line(river, fill="#36647B", width=34, joint="curve")
    draw.line(river, fill="#5A8A9D", width=5, joint="curve")
    for x, y in [(640, 437), (1030, 442), (1110, 460), (590, 470)]:
        draw.polygon([(x - 30, y + 35), (x, y - 28), (x + 30, y + 35)], fill="#3D4B50")
    castle(draw, 375, 700, RED)
    castle(draw, 1165, 710, BLUE)
    text(draw, (270, 770), "赤河城堡", 36, RED)
    text(draw, (1060, 780), "蓝岭城堡", 36, BLUE)
    box(draw, (1090, 385, 1360, 462), color="#32404B")
    text(draw, (1125, 400), "第三国", 32, MUTED)
    x, y = ((565, 638), (692, 573), (845, 590))[focus % 3]
    draw.ellipse((x - 34, y - 34, x + 34, y + 34), fill=RED, outline=INK, width=3)
    text(draw, (x - 18, y - 26), "甲", 32, BG, True)
    draw.polygon([(1010, 620), (1047, 665), (1010, 705), (973, 665)], fill=BLUE)
    arrow(draw, (x + 45, y + 10), (958, 667), color=GOLD)
    text(draw, (165, 975), "位置与数字用于解释规则，不是实机复盘", 29, MUTED)


def panel_header(draw, label, subtitle):
    text(draw, (1500, 340), label, 48, GOLD, True, width=910)
    text(draw, (1500, 417), subtitle, 29, MUTED, width=910)


def help_panel(draw, shot, phase):
    if shot == 24:
        panel_header(draw, "开始求援", "普通 AI-to-AI · 此前没有请求")
        text(draw, (1560, 530), "0.65 < 0.66", 80, INK, True)
        box(draw, (1520, 680, 2380, 818), color="#244B42", outline=GREEN)
        text(draw, (1580, 715), "发起请求", 62, GREEN, True)
        text(draw, (1520, 925), "ratio 是估算战力占比，不能读作胜率", 32, MUTED, width=880)
    elif shot == 25:
        panel_header(draw, "情况好转，请求仍然继续", "此前已经求援 · 使用继续门槛")
        text(draw, (1560, 530), "0.70 < 0.75", 80, INK, True)
        box(draw, (1520, 680, 2380, 818), color="#244B42", outline=GREEN)
        text(draw, (1580, 715), "维持请求", 62, GREEN, True)
        text(draw, (1520, 925), "开始门与继续门不同", 39, MUTED)
    elif shot == 26:
        panel_header(draw, "同样 0.70，不同历史", "一次对照 · 两个不同的先前状态")
        for y, label, result, color in [(520, "此前未求援", "不开始", MUTED), (760, "此前已求援", "继续求援", GREEN)]:
            box(draw, (1510, y, 2390, y + 180), outline=color if phase else None)
            text(draw, (1550, y + 22), label, 38, MUTED)
            text(draw, (1550, y + 85), f"0.70  →  {result}", 51, color, True)
    elif shot == 27:
        panel_header(draw, "从开始，到停止", "示意连续状态 · 并非实机采样")
        for i, (value, label, color) in enumerate([("0.65", "开始", GREEN), ("0.70", "继续", GREEN), ("0.76", "停止", RED)]):
            y = 515 + i * 150
            text(draw, (1520, y), value, 66, color, True)
            arrow(draw, (1730, y + 45), (1810, y + 45), color=color)
            text(draw, (1870, y + 8), label, 54, color)
        text(draw, (1510, 1010), "继续条件：已有请求且 ratio < 0.75", 30, MUTED)
    elif shot == 28:
        panel_header(draw, "请求 → 匹配 → 到达", "这三个步骤分别发生")
        for i, value in enumerate(["已有顺序中的合格请求者", "助手指向请求者当时所在省", "之后才有实际移动与接触"]):
            box(draw, (1510, 520 + i * 150, 2390, 630 + i * 150), outline=GOLD if phase == i % 2 else None)
            text(draw, (1540, 553 + i * 150), value, 35, INK)
        text(draw, (1510, 1000), "该 helper 内没有最短 ETA 排序", 31, MUTED)
    else:
        panel_header(draw, "规则到这里为止", "玩家专用支援的消费路径仍有缺口")
        text(draw, (1530, 550), "普通 AI ↔ AI", 64, GREEN, True)
        text(draw, (1530, 710), "玩家专用支援  ？", 59, GOLD, True)
        text(draw, (1530, 900), "不能把前一种规则直接推广成\n“盟友为什么不救玩家”的完整答案", 33, MUTED, width=820)


def cards(draw, entries, phase=0, color=GOLD, top=515):
    for i, value in enumerate(entries):
        y = top + i * 142
        box(draw, (1500, y, 2400, y + 112), outline=color if i == phase % len(entries) else None)
        text(draw, (1530, y + 28), value, 37, INK, width=850)


def make_frame(row, destination, phase):
    image = Image.new("RGB", (2560, 1440), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 2560, 10), fill=GOLD)
    text(draw, (112, 69), "CK3  /  原生战争 AI", 30, GOLD, True)
    text(draw, (1815, 69), "机制示意  ·  中文旁白粗剪", 30, MUTED)
    text(draw, (112, 152), row["shot_title"], 67, INK, True, width=2300)
    shot = int(row["shot_id"].split("-")[-1])
    chapter = row["chapter_id"]
    map_panel(draw, 0 if chapter == "help" else phase)
    if chapter == "help":
        help_panel(draw, shot, phase)
    elif chapter == "declaration":
        if shot >= 6:
            panel_header(draw, "候选桌", "假设分数 · 条件抽取概率")
            for i, value in enumerate([100, 97, 94, 91, 90, 89]):
                x, y = 1500 + i % 3 * 310, 520 + i // 3 * 180
                color = GREEN if value == 94 and shot >= 9 else GOLD
                box(draw, (x, y, x + 270, y + 145), outline=color)
                text(draw, (x + 50, y + 25), str(value), 65, color, True)
                if value == 89:
                    draw.line((x + 25, y + 105, x + 240, y + 28), fill=RED, width=8)
            text(draw, (1510, 935), "保留池：94 / 472 ≈ 19.9%", 38, GREEN, True)
            text(draw, (1510, 1010), "低于最佳分的90%淘汰；超过五项才截断", 29, MUTED)
        else:
            panel_header(draw, "先经过哪些门", "机会、资格和军力比较是不同环节")
            cards(draw, ["尝试时机", "宣战资格", "原生估算军力门"], phase)
    elif chapter == "targets":
        panel_header(draw, "目标选择有层次", "先找适用的目标块，再比较其中候选")
        cards(draw, ["适用 stance", "按顺序寻找目标块", "候选初筛 → 含寻路的进一步评价"], phase)
        text(draw, (1510, 990), "不同目标块不汇入一个总分池", 34, GOLD)
    elif chapter == "movement":
        panel_header(draw, "估算战力占比", "不等于胜率，也不是界面人数之比")
        text(draw, (1500, 485), "自身 /（自身 + 对方）", 52, INK, True)
        cards(draw, ["普通分支：严格 > 0.5", "desperate 分支：严格 > 0.4", "邻接检查 < 0.625：可能寻找替路"], phase, top=580)
        text(draw, (1510, 1010), "局部门通过，不保证整条未来路线安全", 31, MUTED)
    elif chapter == "battle-end":
        panel_header(draw, "战斗进入战争账本", "一场战斗是整体战争的一部分")
        cards(draw, ["单场战斗记录 → 战斗战分栏", "占领 / 战争目标等独立贡献", "撤退合法性 ≠ 完整主动撤退策略"], phase)
    elif chapter == "peace":
        panel_header(draw, "和平的两张账", "身份与分支条件必须分别检查")
        for y, title, base in [(525, "主动提出白和", "基础 0"), (760, "收到提议后的接受度", "基础 −30")]:
            box(draw, (1500, y, 2400, y + 200), outline=GOLD)
            text(draw, (1540, y + 25), title, 41, INK, True)
            text(draw, (1540, y + 100), base, 51, GOLD, True)
        text(draw, (1505, 1010), "不是最终分数；不能倒推确切发送日期", 30, MUTED)
    else:
        panel_header(draw, "它到底在算什么？", "沿三个案例走过战争的不同阶段")
        cards(draw, ["选哪一场战争", "军队去哪里、何时求援", "主动提议，还是接受和平"], phase)
        text(draw, (1510, 1000), "CK3 1.19.0.6 · 已有研究，保留未知", 31, MUTED)
    draw.line((112, 1120, 2448, 1120), fill="#3A4D59", width=2)
    text(draw, (112, 1090), row["shot_id"] + "  /  " + ", ".join(row["claim_ids"]), 21, MUTED)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    image.save(destination)


def render_visual(row, destination, ffmpeg, workdir):
    destination = Path(destination)
    folder = Path(workdir) / "drawings" / row["id"]
    folder.mkdir(parents=True, exist_ok=False)
    images = [folder / f"state-{n}.png" for n in range(2)]
    frame_maker = make_frame
    if row["chapter_id"] == "help":
        from .help_visuals import make_help_frame
        frame_maker = make_help_frame
    for n, path in enumerate(images):
        frame_maker(row, path, n)
    duration = row["duration_seconds"]
    half = duration / 2
    graph = (f"[0:v]trim=duration={half:.6f},setpts=PTS-STARTPTS[a];"
             f"[1:v]trim=duration={duration-half:.6f},setpts=PTS-STARTPTS[b];"
             "[a][b]concat=n=2:v=1:a=0,format=yuv420p[v]")
    destination.parent.mkdir(parents=True, exist_ok=True)
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
            "-loop", "1", "-framerate", "30", "-i", str(images[0]),
            "-loop", "1", "-framerate", "30", "-i", str(images[1]),
            "-filter_complex", graph, "-map", "[v]", "-an", "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-threads", "4", str(destination)]
    run_command(CommandSpec.create(argv, label=f"war-map-{row['id']}", partial_artifacts=[destination]),
                audit_directory=Path(workdir) / "audit" / "illustrations" / row["id"])
    return destination
