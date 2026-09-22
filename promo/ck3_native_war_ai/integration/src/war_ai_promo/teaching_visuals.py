"""Authored teaching diagrams for the 45-shot film; no simulated live evidence.

Six beats per shot correspond to its two narration cues. Values marked as examples
are editorial inputs; they are never used to fabricate observed game state.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from .common import font, lines
from .visuals import BG, PANEL, INK, MUTED, GOLD, RED, BLUE, GREEN, box, arrow, castle

SIZE = (2560, 1440)
SAFE_BOTTOM = 1120
FAINT = "#3A4C59"
CHAPTERS = {
    "hook": ("读懂战争的三个问题", "THREE QUESTIONS"),
    "declaration": ("案例一 · 选哪一场战争", "DECLARATION / CANDIDATE POOL"),
    "targets": ("案例二 · 军队去哪里", "ARMY OBJECTIVES"),
    "movement": ("案例二 · 行军与接战", "MOVEMENT / ENGAGEMENT"),
    "battle-end": ("案例二 · 战斗之后", "BATTLE / WAR LEDGER"),
    "peace": ("案例三 · 和平的两张账", "PROPOSAL / ACCEPTANCE"),
    "epilogue": ("把规则带回自己的战局", "RECAP / EVIDENCE"),
}

# Each entry is (public title, diagram, six synchronized teaching beats).
SHOTS = {
 1: ("三个看似反常的决定", "questions", ("最高分，为什么没有被选中？", "军队，为什么改变方向？", "还有兵，为什么也谈和平？", "先分清决定发生在哪一层", "再看这一层使用什么输入", "最后检查条件与先前状态")),
 2: ("先认识赤河与蓝岭", "geography", ("赤河在西，蓝岭在东", "河流居中，北部有山口", "东北还有一个第三国", "第一案：选哪一场战争", "第二案：一支军队的选择", "第三案：提出与接受和平")),
 3: ("这部片怎样读", "legend", ("研究范围：CK3 1.19.0.6", "实线框：已有原生规则", "假设标签：仅供计算示范", "教学地图不冒充实机复盘", "虚线边：仍未闭合的解释", "从宣战前的三道门开始")),
 4: ("想宣战，先过三道门", "gates", ("先有一次尝试的时机", "再检查宣战资格", "再进入估算军力比较", "三道门不是同一个分数", "通过前置门，不等于必定宣战", "后面还有候选池中的选择")),
 5: ("对方正在打仗，会改变什么", "thirdwar", ("蓝岭与第三国已经交战", "目标的当前条件发生变化", "军力门使用原生估算量", "这里不能直接代入界面人数", "条件改变，需要重看对应分支", "不能由此推出必然开战")),
 6: ("六张牌，先猜哪张会赢", "pool", ("假设六项都取得正分", "分数为 100、97、94", "另外三项是 91、90、89", "100 是最佳分", "最佳分先决定保留边界", "最后选择还要经过抽取")),
 7: ("90 分留下，89 分出局", "pool", ("假设最佳分为 100", "最佳分的 90% 是 90", "严格低于 90 才淘汰", "89 离开候选池", "90 正好在边界，保留", "池里还剩五张牌")),
 8: ("超过五项，才截到前五", "topfive", ("先数经过边界筛选的候选", "本例恰好剩下五项", "不再执行多余的截断", "另一分支：如果多于五项", "按分数降序保留前五", "两条分支要分开读")),
 9: ("最高分，也只是池中的一项", "weighted", ("保留分数：100、97、94、91、90", "五项权重合计 472", "条带长度表示权重份额", "假设这次抽到了 94", "94 ÷ 472 ≈ 19.9%", "这是给定候选池内的抽取概率")),
 10: ("抽牌概率，不是总宣战概率", "declaration_recap", ("先检查尝试与前置门", "再形成合格的候选池", "最后在保留池内加权抽取", "19.9% 只属于本例这张牌", "国家总体宣战概率没有在此算出", "进入下一案：军队选择目标")),
 11: ("围城，还是追击", "objective_intro", ("眼前可以画出多个目标", "但它们未必进入同一次比较", "先看当前适用的 stance", "再看其目标块的顺序", "最后才是块内候选", "不要先替所有目标编一个总分")),
 12: ("先打开适用的那本目标册", "book", ("当前姿态决定适用的目标册", "只展开这一本册子", "其他姿态的册子暂时合上", "册内有按顺序排列的目标块", "接下来问当前块有没有候选", "完整姿态选择公式仍有边界")),
 13: ("当前块有候选，就不再向后找", "blocks", ("从顺序靠前的目标块开始", "有候选：在当前块继续", "后续目标块停止展开", "没有候选：回退到下一块", "在下一块重新检查候选", "不同块不汇入同一个总分池")),
 14: ("目标，最终落到省份候选", "provinces", ("围城目标对应一处省份", "目标区域对应可选省份", "可见军队也关联所在省份", "这些入口属于当前适用目标块", "图标帮助定位，不证明知晓迷雾", "候选还要经过后续评价")),
 15: ("初步前十，再进入含寻路的评价", "topten", ("先对当前候选做初步评价", "初步最高十项进入下一层", "卡片编号只用于展示顺序", "下一层还包含寻路评价", "初筛次序不等于最终行动", "完整成本、去重与平分细节不在此补造")),
 16: ("看到掉头，还不能解释掉头", "target_evidence", ("围城与追击可以有不同规则入口", "教学图先标出这些入口", "不替这次选择编造最终分数", "个案需要同一时刻的候选", "还需要选中目标与后续动作", "缺少对应证据，就保留原因边界")),
 17: ("人数，不是评估力量", "power", ("界面显示的是人数", "原生决策使用评估力量", "两种量不能直接画等号", "力量条仅表达这个区别", "完整输入权重不在这里补齐", "评估力量也不等于获胜概率")),
 18: ("这个强度比，分母里有什么", "ratio", ("分子：自身评估力量", "分母：自身加对方评估力量", "对方是本分支聚合出的敌方量", "正常路径使用这个比值", "没有敌方聚合对象：直接返回 1.0", "例外返回值不是稳赢证明")),
 19: ("三种数字，回答三个问题", "quantities", ("宣战军力门：能否进入后续", "候选抽取：池内选中哪一项", "接战强度比：当前力量比较", "19.9% 只属于假设抽牌案例", "接战 ratio 不是战斗胜率", "跨阶段套用一个数字会读错")),
 20: ("严格大于，等号不过门", "thresholds", ("一般分支：ratio > 0.5", "正好 0.5，不通过此门", "比 0.5 大，才满足这一条件", "desperate 分支：ratio > 0.4", "正好 0.4，同样不通过", "何时进入 desperate，不能凭空推断")),
 21: ("先看相邻的这一步", "path", ("局部检查发现相邻风险点", "ratio < 0.625 进入替代尝试", "搜索有成本边界", "虚线只表示尝试的替代路线", "图上的线不是已经行军", "一次局部检查不覆盖未来整条路")),
 22: ("替代路径，不一定找得到", "path_branches", ("开始一次受限的替代搜索", "找到替代：使用对应结果", "这不保证后面的路线都安全", "搜索失败：回到后续判断", "再看一般或 desperate 接战门", "不要把搜索失败画成强制撤退")),
 23: ("接战之前，与交战之中", "contact", ("尚未接战：可以重新布置目标", "寻路与改目标属于这一层", "画面上的转向不自动等于撤退", "已经交战：进入另一种状态", "主动撤退策略仍有未知", "下一步看军队之间怎样求援")),
 30: ("战斗结束，先确认记在哪场战争", "battle_record", ("一场正常战斗完成结算", "确认它归属的有效战争", "再形成这场战斗的记录", "战斗分进入对应战争账本", "不能把任意战斗都记到这里", "图中没有假设输赢分值")),
 31: ("一场战斗，只是战争账的一部分", "nested_ledger", ("最里面：单场战斗记录", "中间：全部战斗贡献", "最外面：这场战争的总战分", "占领也有自己的贡献", "战争目标等项目分别进入总账", "不能用一场战斗替代整场战争")),
 32: ("能撤退，不等于知道何时会撤退", "retreat", ("撤退资格：规则是否允许", "撤退执行：动作怎样完成", "这些是已知的一部分", "主动策略：AI 何时决定撤", "这一层仍需要更多解释", "玩家能下命令，不能证明 AI 的决策")),
 33: ("还有军队，也可以进入和平判断", "army_peace", ("地图上的军队仍然存在", "战争账本还有其他输入", "兵没有归零，不会自动排除和平", "先区分是谁提出条件", "再区分是谁评估接受", "把镜头转到和平的两张账")),
 34: ("先摆身份，再打开和平账本", "roles", ("标明哪一方是 AI", "标明进攻方与防守方", "标明谁发出提议", "再标明谁收到提议", "角色改变，会进入不同条件", "下面先看主动提出白和")),
 35: ("主动白和：从基础 0 开始", "proposal", ("这是主动提出的一侧", "基础项为 0", "合法性与候选门先于后续倾向", "蓝岭为 AI 防守方：战争至少 182 日", "守方战分不高于 15：这一项增加 10", "单项 +10，不是总分，也不保证次日发信")),
 36: ("收到白和：从基础 −30 开始", "acceptance", ("现在换到收到提议的一侧", "接受度基础项为 −30", "这不是最终拒绝结论", "赤河是接收方，也是进攻方", "战分这一项读取对面蓝岭的防守方战分", "后续修正、最终比较与结果时点仍有边界")),
 37: ("换成玩家身份，先重查分支", "player_roles", ("先看 AI 对 AI 的身份组合", "再明确把其中一方换成玩家", "身份变化不是沿用原账本", "玩家相关路径存在前置筛选", "也有需要单独检查的否决条件", "不能把普通分支直接推广给玩家")),
 38: ("同样的压力，不一定进同一本账", "two_ledgers", ("灰国只与蓝岭交战", "赤河的另一场防御战争：未设定", "不能把同一压力复制成两边的加分", "条件需要按各自分支归位", "两张账不能交换基数", "没有完整输入，不填写最终合计")),
 39: ("一封白和提议，能证明什么", "peace_evidence", ("看到提议，只能先确认发生了什么", "还要核对当时双方的身份", "主动提出与收到接受分别记录", "静态规则可以提供解释入口", "不能补出未记录的最终总分", "也不能编造唯一原因或精确发送日")),
 40: ("愿意先提，与愿意接受，是两条路", "peace_recap", ("主动方沿主动提议路径", "收到方沿接受度路径", "两边各自检查条件", "基础 0 与 −30 分别属于两边", "地图只是这套判断的情境", "有兵、愿提、愿收，是不同问题")),
 41: ("回到开场的三个疑问", "recap", ("最高分未中：还有加权抽取", "改变方向：先看目标层与局部判断", "还有兵谈和：先分主动与接受", "先确定决定发生的阶段", "再确认输入与当前角色", "最后找状态历史和证据边界")),
 42: ("从参数，读到使用参数的地方", "source_chain", ("定义给出求援门槛", "原生消费者读取并使用门槛", "再检查它比较了什么状态", "0.66 对应开始求援", "0.75 对应维持请求", "只看参数名，不足以闭合规则")),
 43: ("知道规则，还要知道当时的状态", "history_evidence", ("同样输入 0.70", "此前没有请求：不开始", "此前已经请求：继续", "规则解释了两种可能", "具体个案仍需先前状态记录", "空白证据不能由推测填满")),
 44: ("判断顺序，比一句 AI 很笨更有用", "takeaways", ("第一步：这是哪一层决定", "第二步：用了哪些输入", "第三步：条件与历史是什么", "电脑支援玩家仍有解释缺口", "交战中的主动撤退策略仍有未知", "把未知留下，判断才有边界")),
 45: ("规则有版本，解释有边界", "closing", ("研究范围：CK3 1.19.0.6", "依据已有原生规则研究", "地图与示例数字均为教学构造", "图解不替代具体战局的状态证据", "完整来源随影片资料保留", "再看一次战局，从它正在做哪一步开始")),
}


def fit(draw, bounds, value, size=42, color=INK, bold=False):
    """Wrap and shrink to the exact assigned box; never draw into another cell."""
    x, y, right, bottom = bounds
    for candidate in range(size, 17, -1):
        wrapped = []
        for paragraph in value.split("\n"):
            wrapped.extend(lines(paragraph, candidate, right - x, bold) if paragraph.strip() else [""])
        if len(wrapped) * candidate * 1.35 <= bottom - y:
            break
    else:
        raise ValueError(f"Text does not fit its teaching panel: {value!r}")
    for index, line in enumerate(wrapped):
        draw.text((x, y + index * candidate * 1.35), line,
                  font=font(candidate, bold), fill=color)


def cell(draw, bounds, title, body="", *, active=False, color=GOLD, size=44):
    box(draw, bounds, PANEL, color if active else FAINT)
    x, y, right, bottom = bounds
    title_bottom = min(y + 115, y + (bottom - y) * .53) if body else bottom - 18
    fit(draw, (x + 30, y + 25, right - 30, title_bottom), title, size, color if active else INK, True)
    if body:
        body_top = y + min(131, (bottom - y) * .57)
        fit(draw, (x + 30, body_top, right - 30, bottom - 24), body, 34, MUTED)


def dashed(draw, bounds, color=MUTED):
    x, y, r, b = bounds
    for start in range(int(x), int(r), 28):
        draw.line((start, y, min(start + 13, r), y), fill=color, width=3)
        draw.line((start, b, min(start + 13, r), b), fill=color, width=3)
    for start in range(int(y), int(b), 28):
        draw.line((x, start, x, min(start + 13, b)), fill=color, width=3)
        draw.line((r, start, r, min(start + 13, b)), fill=color, width=3)


def columns(draw, entries, beat, *, top=355, bottom=925):
    gap = 42
    width = (2336 - gap * (len(entries) - 1)) / len(entries)
    focus = min(beat % 3, len(entries) - 1)
    for i, (title, body) in enumerate(entries):
        x = 112 + i * (width + gap)
        cell(draw, (x, top, x + width, bottom), title, body,
             active=i == focus, color=(GOLD, BLUE, GREEN)[i % 3], size=48)
        # These are parallel comparisons, not a causal or temporal chain.
        # Only flow() may connect successive stages with arrows.


def flow(draw, entries, beat, *, subtitle="", stop=False):
    for i, (title, body) in enumerate(entries):
        x = 112 + i * 798
        visible = i <= beat % 3 or beat >= 3
        cell(draw, (x, 400, x + 738, 850), title,
             body if visible else "接下来检查", active=i == beat % 3)
        if i < 2 and (visible or beat >= 3):
            arrow(draw, (x + 744, 610), (x + 790, 610), RED if stop and i == 1 else GOLD)
    if subtitle:
        fit(draw, (150, 885, 2390, 956), subtitle, 36, MUTED)


def geography(draw, beat, thirdwar=False, objectives=False, army_peace=False):
    box(draw, (112, 332, 1690, 964), "#152635", FAINT)
    # Stable geography across all teaching maps: west Red River, east Blue Ridge.
    draw.polygon([(145, 370), (915, 370), (850, 915), (145, 915)], fill="#302D32")
    draw.polygon([(980, 370), (1652, 370), (1652, 915), (914, 915)], fill="#1C3446")
    river = [(930, 364), (905, 450), (950, 550), (920, 650), (975, 760), (928, 918)]
    draw.line(river, fill="#497E97", width=25, joint="curve")
    for x in (770, 835, 1020):
        draw.polygon([(x - 25, 470), (x, 420), (x + 25, 470)], fill=FAINT)
    fit(draw, (770, 350, 1070, 415), "北部山口", 27, MUTED)
    castle(draw, 420, 775, RED)
    castle(draw, 1320, 535, BLUE)
    fit(draw, (305, 835, 700, 915), "赤河城堡", 34, RED)
    fit(draw, (1220, 585, 1580, 655), "蓝岭城堡", 34, BLUE)
    cell(draw, (1350, 345, 1640, 448), "第三国", active=thirdwar, size=31)
    draw.ellipse((625, 610, 700, 685), fill=RED)
    fit(draw, (644, 618, 694, 671), "甲", 29, BG, True)
    draw.polygon([(1170, 680), (1205, 724), (1170, 768), (1135, 724)], fill=BLUE)
    if thirdwar and beat > 0:
        arrow(draw, (1430, 461), (1350, 500), RED)
        fit(draw, (1050, 845, 1640, 920), "蓝岭与第三国交战", 31, GOLD)
    if objectives:
        for i, (x, y) in enumerate(((1320, 535), (1170, 724), (1040, 810))):
            color = GOLD if i == beat % 3 else FAINT
            draw.ellipse((x - 68, y - 68, x + 68, y + 68), outline=color, width=6)
    side = [("赤河在西", "教学阵营"), ("蓝岭在东", "对手阵营"), ("第三国在东北", "地图方向保持固定")]
    if objectives:
        side = [("城堡 → 省份", "围城目标入口"), ("可见军队 → 省份", "只标可见目标"), ("目标区 → 候选省份", "不表示全图无迷雾")]
    elif thirdwar:
        side = [("已有一场战争", "先记录目标条件"), ("重新看军力门", "使用原生估算量"), ("后续仍有条件", "不是必然宣战")]
    elif army_peace:
        side = [("军队仍在地图上", "存在，不等于拒绝和平"), ("打开战争账本", "还有其他输入"), ("和平分成两条路", "主动提出 / 收到接受")]
    for i, (title, body) in enumerate(side):
        cell(draw, (1740, 335 + i * 211, 2448, 529 + i * 211), title, body,
             active=i == beat % 3, size=36)


def pool(draw, shot, beat):
    values = [100, 97, 94, 91, 90, 89]
    for i, value in enumerate(values):
        x = 112 + i * 398
        removed = shot >= 7 and value == 89 and beat >= 2
        color = RED if removed else GOLD if value == 100 else GREEN if value == 90 and shot == 7 else BLUE
        box(draw, (x, 385, x + 346, 765), PANEL, color)
        fit(draw, (x + 26, 419, x + 320, 490), f"候选 {chr(65+i)}", 36, MUTED)
        fit(draw, (x + 34, 527, x + 320, 674), str(value) if i <= beat or shot >= 7 else "待揭示", 95, color, True)
        if removed:
            draw.line((x + 24, 683, x + 317, 522), fill=RED, width=9)
        fit(draw, (x + 25, 695, x + 322, 752), "淘汰" if removed else "边界保留" if value == 90 and shot == 7 and beat >= 2 else "假设正分", 28, color)
    if shot == 7:
        fit(draw, (180, 821, 1390, 913), "90% × 100 = 90", 62, GOLD, True)
        fit(draw, (1470, 817, 2380, 920), "淘汰条件：分数 < 90\n等于 90，仍然保留", 36, GREEN)
    else:
        fit(draw, (160, 840, 2370, 920), "这些分数是教学输入；最高分先决定边界，再参与后续选择。", 37, MUTED)


def weighted(draw, beat):
    vals = [100, 97, 94, 91, 90]
    palette = [GOLD, BLUE, GREEN, RED, "#ADA0D4"]
    x = 150
    for i, (value, color) in enumerate(zip(vals, palette)):
        w = value / 472 * 2260
        box(draw, (x, 475, x + w - 5, 690), color)
        fit(draw, (x + 35, 532, x + w - 30, 662), str(value), 68, BG, True)
        if i == 2 and beat >= 3:
            arrow(draw, (x + w / 2, 390), (x + w / 2, 463), GREEN, 9)
            fit(draw, (x - 25, 321, x + w + 35, 385), "假设抽到这一项", 34, GREEN, True)
        x += w
    fit(draw, (160, 738, 1130, 826), "权重合计 472", 52, GOLD, True)
    if beat >= 2:
        fit(draw, (1200, 738, 2390, 833), "94 / 472 ≈ 19.9%", 61, GREEN, True)
    fit(draw, (160, 870, 2390, 942), "条带展示池内份额，不是国家总体宣战概率。", 35, MUTED)


def book(draw, beat, blocks=False):
    box(draw, (112, 349, 665, 945), "#27323B", GOLD)
    fit(draw, (150, 392, 610, 500), "当前适用 stance", 46, GOLD, True)
    fit(draw, (150, 545, 610, 745), "按顺序\n打开目标块", 52, INK, True)
    fit(draw, (150, 842, 620, 920), "其他册子保持关闭", 30, MUTED)
    for i in range(3):
        y = 350 + 205 * i
        focused = i == (0 if beat < 3 else min(beat - 2, 2)) if blocks else i == beat % 3
        title = f"目标块 {i+1}"
        body = "检查当前块的候选"
        if blocks:
            body = ("有候选 → 在本块继续" if beat < 3 else "无候选 → 看下一块") if i == 0 else "不再展开" if beat < 3 else "到这里重新检查"
        cell(draw, (810, y, 2420, y + 179), title, body, active=focused, size=39)
        if i < 2 and beat >= 3:
            arrow(draw, (735, y + 105), (735, y + 245), GOLD)
    if blocks and beat < 3:
        arrow(draw, (674, 447), (796, 447), GREEN)


def ratio(draw, beat, thresholds=False):
    if thresholds:
        for i, (title, threshold, color) in enumerate((("一般分支", .5, BLUE), ("desperate 分支", .4, GOLD))):
            y = 367 + i * 270
            fit(draw, (150, y, 840, y + 90), title, 45, color, True)
            fit(draw, (835, y, 2360, y + 90), f"ratio > {threshold}", 66, color, True)
            x, right = 835, 2345
            ty = y + 153
            cut = x + (right - x) * threshold
            draw.line((x, ty, right, ty), fill=FAINT, width=14)
            if beat >= (0 if i == 0 else 3):
                draw.line((cut + 15, ty, right, ty), fill=color, width=14)
            draw.ellipse((cut - 14, ty - 14, cut + 14, ty + 14), fill=BG, outline=RED, width=4)
            fit(draw, (155, y + 117, 735, y + 218), "等于门槛：不通过", 36, RED)
        dashed(draw, (151, 924, 2410, 973))
        fit(draw, (175, 925, 2380, 970), "未知：上游何时选择 desperate 分支，不能由图中门槛单独推出。", 29, MUTED)
        return
    fit(draw, (400, 355, 2200, 478), "自身评估力量", 78, RED, True)
    draw.line((240, 512, 2330, 512), fill=GOLD, width=5)
    fit(draw, (290, 551, 2280, 712), "自身评估力量 + 对方评估力量", 68, INK, True)
    cell(draw, (160, 754, 1260, 955), "正常计算路径", "对方：本分支聚合出的敌方力量", active=beat < 4, size=39)
    cell(draw, (1315, 754, 2400, 955), "无敌方聚合对象", "单独分支直接返回 1.0", active=beat >= 4, color=BLUE, size=39)


def path_diagram(draw, beat, branches=False):
    origin, risk, target = (380, 650), (1140, 650), (2090, 650)
    draw.line((origin, risk, target), fill=FAINT, width=8)
    for point, label, color in ((origin, "当前省份", RED), (risk, "相邻风险点", GOLD), (target, "局部检查之后", MUTED)):
        x, y = point
        draw.ellipse((x - 57, y - 57, x + 57, y + 57), fill=PANEL, outline=color, width=5)
        fit(draw, (x - 200, y + 96, x + 260, y + 170), label, 37, color, True)
    fit(draw, (830, 425, 1450, 522), "ratio < 0.625", 56, GOLD, True)
    if beat >= 1:
        points = [(430, 605), (760, 370), (1540, 370), (2030, 601)]
        for a, b in zip(points, points[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            for j in range(0, 20, 2):
                draw.line((a[0] + dx*j/20, a[1] + dy*j/20, a[0] + dx*(j+1)/20, a[1] + dy*(j+1)/20), fill=BLUE, width=6)
        fit(draw, (830, 285, 1810, 355), "受限替代搜索 · 并非实际行军", 34, BLUE)
    if branches:
        cell(draw, (160, 860, 1250, 971), "找到替代 → 使用对应结果", active=beat < 3, color=GREEN, size=34)
        cell(draw, (1320, 860, 2410, 971), "搜索失败 → 返回接战门判断", active=beat >= 3, color=GOLD, size=34)
    else:
        fit(draw, (220, 868, 2380, 945), "搜索有成本边界；此处不证明未来整条路线安全。", 38, MUTED)


def ledgers(draw, beat, kind):
    left_active = kind == "proposal" or kind not in ("acceptance",) and beat < 3
    right_active = kind == "acceptance" or kind not in ("proposal",) and beat >= 3
    for i, (title, base, english, active) in enumerate((("主动提出白和", "0", "PROPOSE", left_active), ("收到后评估接受", "−30", "ACCEPT", right_active))):
        x = 135 + i * 1190
        box(draw, (x, 340, x + 1100, 958), "#26313A", GOLD if active else FAINT)
        fit(draw, (x + 44, 370, x + 1030, 451), title, 52, GOLD if active else MUTED, True)
        identity = "蓝岭 · AI 防守方 / PROPOSE" if i == 0 else "赤河 · AI 进攻方 / RECEIVE"
        fit(draw, (x + 44, 462, x + 1030, 510), identity, 27, BLUE if i == 0 else RED)
        fit(draw, (x + 48, 543, x + 526, 670), "基础项", 44, INK)
        fit(draw, (x + 620, 517, x + 1010, 676), base, 94, GOLD if active else MUTED, True)
        for n, label in enumerate(("身份与角色", "适用条件", "最终合计：不补造")):
            y = 707 + n * 73
            draw.line((x + 43, y - 7, x + 1055, y - 7), fill=FAINT, width=2)
            fit(draw, (x + 48, y, x + 1020, y + 67), label, 33, INK if active and n <= beat % 3 else MUTED)
        if not active:
            fit(draw, (x + 635, 465, x + 1050, 519), "先分清这一侧", 27, MUTED)


def peace_detail(draw, shot, beat):
    """Frozen narration N70/N72/N75: preserve role and war ownership."""
    if shot == 35:
        for i, (title, body) in enumerate((("蓝岭 · AI 防守方", "当前检查：主动提出白和"), ("战争持续 ≥ 182 日", "原生条件，不是假设发信日期"), ("防守方战分 ≤ 15", "与时长条件同时检查"))):
            cell(draw, (135, 345 + i * 210, 1280, 538 + i * 210), title, body,
                 active=i == beat - 3, color=BLUE, size=43)
        arrow(draw, (1310, 649), (1430, 649), GOLD, 9)
        cell(draw, (1480, 345, 2410, 954), "蓝岭 · 主动账本", "基础 0\n\n满足左侧条件：单项 +10\n\n其他修正：继续检查\n最终总分 / 发送日：未定", active=True, color=GOLD, size=46)
    elif shot == 36:
        cell(draw, (135, 360, 1115, 930), "蓝岭 · AI 防守方", "取这一方的防守方战分\n\n它是赤河的对面一方\n\n不偷换成赤河自己的战分", active=beat < 5, color=BLUE, size=46)
        arrow(draw, (1150, 646), (1310, 646), BLUE, 9)
        cell(draw, (1370, 360, 2410, 930), "赤河 · AI 进攻方 / 接收方", "接受基础 −30\n\n战分项 ← 蓝岭守方战分\n\n之后还有时长等修正\n最终比较与时点仍有未明部分", active=beat >= 4, color=RED, size=42)
    else:
        # No edge from the third country to Redriver: that war was never set up.
        cell(draw, (135, 345, 775, 813), "灰国", "只设定了\n与蓝岭交战", active=beat == 0, color=MUTED, size=51)
        cell(draw, (940, 345, 1600, 813), "蓝岭", "受到灰国战争的影响\n\n还须核对具体修正条件", active=beat == 1, color=BLUE, size=51)
        arrow(draw, (792, 579), (920, 579), BLUE, 8)
        cell(draw, (1760, 345, 2410, 813), "赤河", "另一场防御战争\n\n未设定", active=beat == 2, color=RED, size=51)
        dashed(draw, (1749, 334, 2421, 824), MUTED)
        fit(draw, (170, 868, 2370, 950), "先逐项核对角色和战争归属；不要把压力复制成两本账的加分。", 39, GOLD, True)


def top_ten(draw, beat):
    fit(draw, (142, 323, 1360, 403), "初步候选：展示排序，不编造分数", 42, GOLD, True)
    for i in range(10):
        x, y = 145 + i % 5 * 222, 453 + i // 5 * 190
        cell(draw, (x, y, x + 185, y + 150), str(i + 1), active=i // 4 == beat % 3, size=61)
    arrow(draw, (1290, 635), (1450, 635), GOLD, 9)
    cell(draw, (1505, 423, 2395, 820), "含寻路的下一层评价", "初筛次序 ≠ 最终目标\n完整成本细节不在此补造", active=beat >= 3, color=BLUE, size=47)
    fit(draw, (150, 881, 2395, 955), "原生上限：初步最高十项进入进一步评价。", 36, MUTED)


def nested_ledger(draw, beat):
    for bounds, label, color in (((140, 336, 2420, 965), "总战争分", GOLD), ((240, 440, 1670, 900), "战斗贡献", BLUE), ((355, 552, 1440, 805), "单场战斗记录", GREEN)):
        box(draw, bounds, PANEL, color)
        x, y, r, b = bounds
        fit(draw, (x + 32, y + 18, r - 30, y + 95), label, 42, color, True)
    if beat >= 3:
        cell(draw, (1770, 484, 2350, 673), "占领贡献", "独立项目", active=beat == 3, size=38)
    if beat >= 4:
        cell(draw, (1770, 710, 2350, 899), "战争目标等", "独立项目", active=beat >= 4, size=38)


PANELS = {
 "questions": [("最高分没有中选", "候选分数\n↓\n保留池\n↓\n加权抽取"), ("军队改变方向", "目标层次\n↓\n局部路径\n↓\n状态判断"), ("有兵也谈和平", "角色与方向\n↓\n主动 / 接受\n↓\n各自条件")],
 "legend": [("已有原生规则", "标明版本与适用分支\n实线表示规则关系"), ("假设教学输入", "地图、分数与状态用来算例\n不冒充实机复盘"), ("仍然未知", "保留缺失条件\n不替具体战局补原因")],
 "gates": [("尝试时机", "先进入一次尝试"), ("宣战资格", "检查候选是否合法"), ("估算军力门", "使用原生评估量")],
 "topfive": [("本例：恰好五项", "100 / 97 / 94 / 91 / 90\n保留这五项"), ("如果：多于五项", "按分数降序\n只保留前五"), ("两条数量分支", "先筛 90% 边界\n再检查是否超过五项")],
 "declaration_recap": [("前置门", "尝试时机\n宣战资格\n估算军力"), ("候选池", "90% 边界\n超过五项才截断"), ("池内加权抽取", "假设 94 / 472\n≈ 19.9%\n不是总宣战概率")],
 "objective_intro": [("适用姿态", "当前 stance"), ("目标块", "按既定顺序查找"), ("省份候选", "在当前块内评价")],
 "target_evidence": [("教学规则入口", "围城 / 追击\n分别找适用目标块"), ("具体个案需要", "同一时刻的候选\n选中目标\n衔接动作"), ("不能补出来的", "最终分数\n唯一原因\n未记录的状态")],
 "power": [("界面人数", "可见的兵员数字\nHEADCOUNT"), ("评估力量", "决策中的评估量\nEVALUATED POWER"), ("获胜概率", "不是前两项的同义词\nWIN PROBABILITY")],
 "quantities": [("宣战军力门", "阶段：宣战前\n作用：检查前置条件"), ("池内抽取概率", "阶段：候选选择\n本例：94 / 472 ≈ 19.9%"), ("接战强度比", "阶段：行军与接战\n力量比较，不是胜率")],
 "contact": [("尚未接战", "重新布置目标\n寻找路径\nPRE-CONTACT"), ("状态边界", "转向 ≠ 主动撤退\n不能混用两层解释"), ("已经交战", "主动撤退策略仍有未知\nIN BATTLE")],
 "battle_record": [("正常战斗结算", "先取得本场记录"), ("归属有效战争", "核对对应关系"), ("写入战斗分栏", "只记到对应战争")],
 "retreat": [("撤退资格", "能不能执行\nELIGIBILITY"), ("撤退执行", "怎样完成动作\nEXECUTION"), ("主动撤退策略", "AI 何时决定撤\n仍有未知")],
 "roles": [("主案例：AI 对 AI", "赤河：AI 进攻方\n蓝岭：AI 防守方"), ("提议方向", "蓝岭提出\n↓\n赤河收到"), ("适用条件", "允许白和的战争类型\n身份、人质与相关能力\n分别核对")],
 "player_roles": [("主案例：AI 对 AI", "赤河：AI 进攻方\n蓝岭：AI 防守方"), ("对照：只换赤河", "赤河：玩家进攻方\n蓝岭：仍为 AI 防守方"), ("重查蓝岭主动路径", "候选预筛 ai_potential\n倾向否决 ai_will_do\n不复制普通分支")],
 "peace_evidence": [("实际可见事实", "谁提出\n谁收到\n当时身份"), ("规则解释入口", "主动账本\n接受账本\n分别核对条件"), ("没有记录的部分", "最终总分\n唯一因果\n精确发送日期")],
 "recap": [("最高分未中", "保留池里的加权抽取"), ("军队改方向", "目标层与局部状态判断"), ("还有兵谈和", "主动提出与收到接受")],
 "source_chain": [("参数定义", "开始门槛 0.66\n继续门槛 0.75"), ("原生消费者", "读取门槛\n比较 ratio 与先前状态"), ("闭合规则", "未请求：检查开始门\n已有请求：检查继续门")],
 "history_evidence": [("此前未求援", "同样的 0.70\n不低于 0.66\n→ 不开始"), ("此前已求援", "同样的 0.70\n低于 0.75\n→ 继续"), ("具体个案", "需要当时输入\n与先前请求状态\n不能猜填")],
 "takeaways": [("先确定阶段", "宣战 / 目标 / 移动\n求援 / 战斗 / 和平"), ("再核对输入", "数量、角色与方向\n是否属于当前分支"), ("最后看状态", "先前历史\n可见证据\n未知边界")],
 "closing": [("版本范围", "CK3 1.19.0.6\n原生战争 AI 研究"), ("来源资料", "docs/ck3-native-ai\n随片来源表与版本锁定\n地图及算例为教学构造"), ("继续观察战局", "决定发生在哪一步\n当时用了什么条件")],
}


def beat_index(row, phase):
    if phase not in (0, 1, 2):
        raise ValueError("Visual phase must be 0, 1, or 2")
    cue_number = int(str(row["id"]).rsplit("-", 1)[-1])
    return (0 if cue_number % 2 else 3) + phase


def make_teaching_frame(row, destination, phase):
    shot = int(row["shot_id"].rsplit("-", 1)[-1])
    title, kind, beats = SHOTS[shot]
    beat = beat_index(row, phase)
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 2560, 10), fill=GOLD)
    chapter, english = CHAPTERS[row["chapter_id"]]
    fit(draw, (112, 54, 1580, 111), "CK3 / " + chapter, 30, GOLD, True)
    fit(draw, (1600, 59, 2448, 116), english, 26, MUTED)
    fit(draw, (112, 135, 2448, 238), title, 66, INK, True)
    # Six steady progress marks make the two-cue teaching sequence legible.
    for i in range(6):
        draw.rounded_rectangle((112 + i * 390, 262, 465 + i * 390, 272), radius=5,
                               fill=GOLD if i <= beat else FAINT)
    if kind in ("geography", "thirdwar", "provinces", "army_peace"):
        geography(draw, beat, kind == "thirdwar", kind == "provinces", kind == "army_peace")
    elif kind == "pool":
        pool(draw, shot, beat)
    elif kind == "weighted":
        weighted(draw, beat)
    elif kind in ("book", "blocks"):
        book(draw, beat, kind == "blocks")
    elif kind in ("ratio", "thresholds"):
        ratio(draw, beat, kind == "thresholds")
    elif kind in ("path", "path_branches"):
        path_diagram(draw, beat, kind == "path_branches")
    elif kind in ("proposal", "acceptance", "two_ledgers", "peace_recap"):
        if shot in (35, 36) and beat >= 3 or shot == 38 and beat < 3:
            peace_detail(draw, shot, beat)
        else:
            ledgers(draw, beat, kind)
    elif kind == "topten":
        top_ten(draw, beat)
    elif kind == "nested_ledger":
        nested_ledger(draw, beat)
    elif kind in ("gates", "declaration_recap", "objective_intro", "battle_record", "source_chain"):
        flow(draw, PANELS[kind], beat)
    else:
        columns(draw, PANELS[kind], beat)
        if kind in ("legend", "target_evidence", "peace_evidence", "history_evidence", "retreat"):
            dashed(draw, (1710, 340, 2462, 939), MUTED)
        if kind == "power":
            # Independent abstract bars: no fabricated ratio or transformation formula.
            for i, color in enumerate((RED, BLUE, MUTED)):
                x = 154 + i * 792
                draw.line((x, 807, x + 610, 807), fill=FAINT, width=22)
                if i == beat % 3:
                    draw.line((x, 807, x + 370, 807), fill=color, width=22)
    box(draw, (112, 994, 2448, 1076), "#223341", GOLD)
    fit(draw, (139, 1005, 2417, 1068), beats[beat], 38, GOLD, True)
    fit(draw, (115, 1085, 1690, 1118), "CK3 1.19.0.6 · 教学图解 · 假设示例不等于实机状态", 22, MUTED)
    fit(draw, (1750, 1085, 2448, 1118), "RULES / EXAMPLES / OPEN QUESTIONS", 21, MUTED)
    draw.line((112, SAFE_BOTTOM, 2448, SAFE_BOTTOM), fill=FAINT, width=2)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        image.save(stream, format="PNG")
