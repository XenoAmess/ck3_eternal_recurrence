"""Build the Messina-only narration and exact source-frame bindings for R7."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "r62-contextual" / "script.json"

# The original 900-second recording covers the actual, non-replayed battle.
# Times below were checked against the visible battle-panel counts in the film.
SOURCE_TIMES = {
    "E1-F01": (250, 260), "E1-F02": (250, 275), "E1-F03": (260, 275),
    "E1-F04": (275, 280), "M02": (275, 280), "M03": (275, 280),
    "M04": (275, 280), "M05": (275, 280), "M06": (275, 280),
    "M07": (275, 280), "M08": (275, 280), "E1-F05": (275, 280),
    "E1-F06": (275, 280), "E1-F09": (260, 275), "C01": (275, 280),
    "C02": (275, 280), "C03": (275, 280), "C04": (275, 280),
    "C05": (275, 280), "C10": (400, 420), "E1-F23": (400, 420),
    "E1-F24": (300, 390), "E1-F25": (420, 423),
}

DROP = {"C06", "C07", "C08", "C09", "E1-F19", "P01", "P02", "P03", "C11", "E1-F20"}

# A source-bound rewrite, not a cosmetic relabel of the unrelated R0217 math.
REWRITE = {
    "E1-F01": {
        "visual_title": "只看墨西拿这一场原版战斗",
        "visual_lines": ["原始实机录像 · CombatID 16777218", "罗贝尔守方 vs 三支进攻军队", "今天只复算这一场仗的同日账"],
        "zh": "屏幕上这场仗发生在墨西拿，守方是玩家罗贝尔的军队，进攻方有多支敌军。你看到的是当时原始战局的实机录像。我们沿着同一个战斗编号、同一个省份和相邻的游戏日，先看战线宽度怎样限制出伤，再把两边的伤害原始值算出来。随后将守方收到的伤害分到征召兵、长枪兵和骑士的一人战斗记录，观察战斗窗人数从一千二百二十二变成一千一百五十六。最后再看这场仗实际进入追击、结束时发生了什么。每一步都把当时的游戏战况放在算式旁边：画面上的整数是玩家看到的士兵数，原生回执中的大整数则经过十万倍缩放。沿这条线走完，你会知道一场看似由兵力决定的战斗，怎样在每天的计算里逐渐改变。",
        "en": "This is the original Messina battle, CombatID 16777218. The footage and calculations refer to the same battle, with Robert defending against enemy armies. We will follow its width, outgoing damage, regiment losses and observed pursuit."
    },
    "E1-F03": {
        "visual_title": "原始录像与原生回执逐日配对",
        "visual_lines": ["原片 275 秒：守方约 1,222、攻方约 1,921", "原片 280 秒：守方约 1,156、攻方约 1,860", "界面取整；底层人数 raw ÷ 100,000"],
        "zh": "先停在原始录像的这两帧。源片二百七十五秒附近，战斗窗显示守方约一千二百二十二人、攻方约一千九百二十一人；到二百八十秒附近，显示约一千一百五十六人与一千八百六十人。底层第五日边界记录的守方是一亿二千二百二十二万五千零七十四原始整数，除以十万是一千二百二十二点二五零七四；下一边界是一亿一千五百六十二万九千八百七十四，折合一千一百五十六点二九八七四。界面显示取整人数，底层回执保留定点精度。后面每张算式都保留这一场战斗的原始画面和对应的前后兵力，让你看到这一天的结算确实落在眼前这支军队身上。",
        "en": "At original video seconds 275 and 280, the combat window visibly changes from roughly 1,222/1,921 to 1,156/1,860. The native fixed-point defender totals are 122,225,074 and 115,629,874 raw. UI counts are rounded."
    },
    "E1-F04": {
        "visual_title": "锁定原始战斗身份与双方",
        "visual_lines": ["CombatID 16777218 · 墨西拿省份 2633", "side 0：进攻方；side 1：罗贝尔守方", "第 5→6 日：同一战斗、连续边界"],
        "zh": "先给这笔账上锁。原始战局的战斗编号是一次性内部键一六七七七二一八，战场省份是二六三三，对应墨西拿。研究回执把进攻方标为side零，守方标为side一；在游戏画面里，守方是罗贝尔军，进攻方则是陆续加入的敌军。side数字负责把回执、公式与画面接在一起。我们选择原始战局第五到第六日这一次主战结算：源日两侧当前参战人数原始值已经冻结，出伤回执也在同一战斗、同一源日读到，目标日能回读兵团损失。游戏界面的整数让我们识别结果，内部计算量则写在右侧。这样，同一场战斗的地形、兵力和伤亡就能连成一笔可以复算的账。",
        "en": "We lock CombatID 16777218 in province 2633. Side zero attacks; side one is Robert's defending army. This calculation connects the original fifth-day native state to the sixth-day readback."
    },
    "M03": {
        "visual_title": "同场战宽：先把原始人数还原",
        "visual_lines": ["攻方 192,121,816 raw → 1,921.21816 人；守方 122,225,074 raw → 1,222.25074 人", "攻方宽度份额 floor(1,480 × Q² ÷ 192,121,816) = 77,034", "守方小于战宽：份额封顶 100,000"],
        "zh": "把同场第五日的人数放进战宽公式。战斗窗背后的最终战线宽度是一千四百八十，这不是兵员定点数，不用除十万。进攻方当前兵力原始整数一亿九千二百一十二万一千八百一十六，折合一千九百二十一点二一八一六人；守方一亿二千二百二十二万五千零七十四，折合一千二百二十二点二五零七四人。原版用战宽除该侧当前参战人数，结果最多封顶百分之百。进攻方一千九百二十一人多于战宽，把一千四百八十乘两个十万，再除其原始兵力并截断，得到宽度份额原始值七万七千零三十四，即百分之七十七点零三四。守方参战人数少于战宽，份额封顶十万，也就是百分之百。两侧在这里不同，不是因为随机挑中了哪支兵团，而是整侧输出被宽度比例缩放。",
        "en": "Messina's width is 1,480. The attacking side has 192,121,816 raw soldiers, or 1,921.21816 people, giving a width fraction of 77,034 raw. Robert's 1,222.25074 defenders are below width, so their fraction is capped at 100,000."
    },
    "M04": {
        "visual_title": "同场出伤的四组输入",
        "visual_lines": ["优势系数：攻方 100,000；罗贝尔守方 130,000", "固定伤害缩放：3,000 / Q = 0.03", "反制后有效攻击 R14：3,511,465,714 / 2,036,632,465 raw"],
        "zh": "现在只拿这场墨西拿战斗的原生出伤输入。第五日的优势作用转成两侧伤害系数：攻方十万，也就是一点零；罗贝尔守方十三万，也就是一点三。这个十三万是原生当天用于出伤的条件化系数，不等于把你在另一帧界面看到的优势数字直接念成百分之三十。固定伤害缩放原始值三千，除十万等于零点零三。刚才算出的宽度份额是攻方七万七千零三十四、守方十万。反制与兵种修正后的有效攻击内部聚合值，攻方三十五亿一千一百四十六万五千七百一十四，守方二十亿三千六百六十三万二千四百六十五。它们叫有效攻击计算量，不是人口，更不是已发生的伤亡。我们不把这些大数冒充游戏里可直接点开的单一面板；观众能在原片中核对的是同一场战斗和稍后人数的变化。",
        "en": "The original fifth-day trace uses advantage factors 100,000 and 130,000, fixed damage scaling 3,000, width factors 77,034 and 100,000, and native post-counter aggregate attack 3,511,465,714 and 2,036,632,465 raw. The large attack terms are internal quantities."
    },
    "M05": {
        "visual_title": "第一步：优势乘固定伤害缩放",
        "visual_lines": ["攻方 floor(100,000 × 3,000 ÷ Q) = 3,000", "罗贝尔守方 floor(130,000 × 3,000 ÷ Q) = 3,900", "中间值不是阵亡人数"],
        "zh": "原版第一步先把优势系数与固定伤害缩放相乘，接着除以十万并截断。进攻方十万乘三千，得到三亿；除十万，留下三千。罗贝尔守方十三万乘三千，得到三亿九千万；除十万，留下三千九百。这两个整数只是第一层内部因子，不是任何一方死了三千人。下一层会继续乘战线宽度份额；如果把这个乘法和后面的乘法合成一条实数公式，再在末尾才取整，就已经不是原版逐步运算了。画面左边的两支军队仍是刚才同一场墨西拿战斗，公式右边的顺序也与原生出伤链一致。",
        "en": "First multiply advantage by the fixed 3,000 damage scale, dividing by 100,000 at this boundary. The attacker keeps 3,000 raw; Robert's defenders keep 3,900 raw. These are intermediate factors, not deaths."
    },
    "M06": {
        "visual_title": "第二步：乘各自的战宽份额",
        "visual_lines": ["攻方 floor(3,000 × 77,034 ÷ Q) = 2,311", "罗贝尔守方 floor(3,900 × 100,000 ÷ Q) = 3,900", "每步截断后再用该整数继续"],
        "zh": "第二步把两边刚得到的整数分别乘战宽份额。进攻方三千乘七万七千零三十四，乘积是两亿三千一百一十万二千；除十万得两千三百一十一点零二，立即截断，留下两千三百一十一。罗贝尔守方三千九百乘封顶的十万，再除十万，仍是三千九百。注意这正是两军人数不对称的影响：攻方虽然有约一千九百二十一名还在战斗的人，但只有一千四百八十的战宽，输出被缩到百分之七十七点零三四；守方约一千二百二十二人，全部进入战宽。接下来不再使用两千三百一十一点零二的小数，而只能用两千三百一十一这个截断后的原始整数。",
        "en": "Second, apply width. The attacker keeps floor(3,000 × 77,034 / 100,000) = 2,311. Robert keeps 3,900. Every following calculation uses these truncated integers."
    },
    "M07": {
        "visual_title": "第三步：算出这一天双侧伤害",
        "visual_lines": ["攻方 floor(2,311 × 3,511,465,714 ÷ Q) = 81,149,972", "守方 floor(3,900 × 2,036,632,465 ÷ Q) = 79,428,666", "两项皆为内部出伤值，不能除 Q 当作死人"],
        "zh": "第三步再乘各自反制后的有效攻击。进攻方两千三百一十一乘三十五亿一千一百四十六万五千七百一十四，除十万向零截断，得到八千一百一十四万九千九百七十二。罗贝尔守方三千九百乘二十亿三千六百六十三万二千四百六十五，同样除十万截断，得到七千九百四十二万八千六百六十六。两组结果逐项和原版这一战、这一天的出伤回读一致。它们仍是内部伤害值；绝不能把八千多万说成八千多万人，也不能直接把两边出伤相减宣布胜负。攻方这笔八千一百一十四万九千九百七十二，下一步会作为罗贝尔守方的入伤，逐支兵团经过自己的坚韧。守方的七千九百四十二万八千六百六十六，则由敌军兵团承受。",
        "en": "Final fixed-point multiplication yields attacker outgoing damage 81,149,972 raw and Robert's outgoing damage 79,428,666 raw. Both match the native fifth-day trace. Damage is not a headcount; each receiving regiment still needs its own casualty calculation."
    },
    "M08": {
        "visual_title": "出伤接入伤：核对下一边界",
        "visual_lines": ["守方入伤 = 攻方出伤 81,149,972", "原片守方显示约 1,222 → 1,156 人", "底层守方 122,225,074 → 115,629,874 raw"],
        "zh": "现在把出伤放回正在发生的墨西拿战斗。攻方的八千一百一十四万九千九百七十二，等于罗贝尔守军收到的入伤；罗贝尔军打出去的七千九百四十二万八千六百六十六，则交给进攻方各兵团。回到原始录像：结算前那一帧，战斗窗守方约一千二百二十二人、攻方约一千九百二十一人；之后分别约一千一百五十六与一千八百六十。底层守方总人数从一亿二千二百二十二万五千零七十四，变成一亿一千五百六十二万九千八百七十四，差值六百五十九万五千二百原始单位，折合约六十五点九五二人。但不能用两侧出伤直接推出这个差值，因为每一支兵团的坚韧、人数和软硬伤分账都还要各自计算。下面就沿着同一笔守方入伤，把账追到具体兵团。",
        "en": "Attacker outgoing 81,149,972 is defender incoming damage. The original combat footage shows about 1,222 defenders before and 1,156 after; the native total changes from 122,225,074 to 115,629,874 raw. Regiment toughness and allocation explain the difference."
    },
    "C10": {
        "visual_title": "这场仗真实的追击与永久损失",
        "visual_lines": ["原始第 28 日：守方现役 0；累计硬伤 46,367,776 raw", "第 29/30/31 日累计硬伤：48,432,891 / 50,524,590 / 52,645,351 raw", "三日新增硬伤合计 6,277,575 raw = 62.77575 人当量"],
        "zh": "现在看这场墨西拿战斗后半段。原始第二十八日，阶段进入游戏所谓追击，罗贝尔守方仍在作战的人数已经是零；原片战斗窗也能看到败退和追击状态。原生回执里，守方累计硬伤是四千六百三十六万七千七百七十六原始单位，折合四百六十三点六七七七六人当量。第二十九日升到四千八百四十三万二千八百九十一，新增二百零六万五千一百一十五，约二十点六五人。第三十日升到五千零五十二万四千五百九十，新增二百零九万一千六百九十九，约二十点九二人。第三十一日升到五千二百六十四万五千三百五十一，再新增二百一十二万零七百六十一，约二十一点二一人。三天合计新增硬伤六百二十七万七千五百七十五，折合六十二点七七五七五人当量。镜头里的败退，与账本里继续增长的永久兵员损失，就是追击阶段可见的两个结果。",
        "en": "In the actual Messina pursuit, Robert has zero active fighters on day 28, but hard losses continue. Cumulative hard loss rises from 46,367,776 raw to 48,432,891, 50,524,590 and 52,645,351 on days 29–31. The three-day increase is 6,277,575 raw, or 62.77575 person-equivalents."
    },
    "E1-F23": {
        "visual_title": "这份同场计算怎样交给智能体",
        "visual_lines": ["墨西拿第 5→6 日：出伤与兵团损失逐项绑定", "同场追击三日：累计硬伤继续增加", "智能体：单日局部计算可以解释兵损"],
        "zh": "把镜头和数字接上，对游玩智能体也有实际意义。它拿到这场墨西拿战斗的省份、双方、战宽、人数和有效攻击，就能复算第五日两侧出伤。攻方的八千一百一十四万九千九百七十二作为罗贝尔守方入伤，继续落到征召兵、长枪兵和骑士的一人战斗记录；算出的兵员损失再与第六日原始回读逐项对照。进入追击后，它还能读取这场战斗的累计硬伤变化：守方现役兵力已经归零，永久损失仍逐日增加。这样的同场计算可以让智能体解释局部兵损，比较战场条件变化对当日出伤的影响。对玩家而言也一样：看到人数优势时，先看宽度和有效攻击，再看伤害落到哪些兵团，才知道战斗数字为什么会变。",
        "en": "The agent can use the original Messina fifth-day outgoing damage and regiment casualty calculations for local reasoning, and read this battle's observed hard-loss changes during pursuit."
    },
    "E1-F24": {
        "visual_title": "下次看战斗，按这条顺序找数字",
        "visual_lines": ["先认双方、地形与战线宽度", "再看两侧有效攻击与逐团坚韧", "最后比前后兵力与软硬伤变化"],
        "zh": "下次你在自己的存档里旁观一场战斗，可以按同样的顺序读界面。先认清双方实际进入的是哪些军队，战场是什么省份，谁在进攻；再看游戏面板上的军团兵种、士兵人数、地形、战线宽度与优势。等游戏日推进，就对照前后两帧的兵力变化，观察征召兵、职业兵士和骑士条目的损失，区分溃逃的软伤与永久的硬伤。墨西拿的这一日给了我们一个具体例子：约一千九百二十一名进攻军受到一千四百八十的战宽限制；罗贝尔守方约一千二百二十二人，随后落到约一千一百五十六人。把这两帧与逐步截断的公式接起来，战斗就从一串跳动的数字，变成一条能追问原因的计算链。",
        "en": "Watch each battle in order: identify the armies and terrain, read width and strength, then compare regiment losses and soft versus hard casualties across adjacent states. Messina gives a concrete example of that chain."
    },
    "E1-F25": {
        "visual_title": "回到墨西拿：一场战斗、一条计算链",
        "visual_lines": ["同场输入：地形、战宽、人数、优势、有效攻击", "同场结算：双侧出伤 → 逐团伤亡 → 次日人数", "同场结果：追击继续写硬伤，终局守方落败"],
        "zh": "最后再看原始墨西拿战场。从同一场、同一天的参战人数出发，森林和战宽先把攻方宽度份额压到七万七千零三十四；优势、固定伤害缩放和反制后有效攻击依次进入公式，双侧出伤算到八千一百一十四万九千九百七十二和七千九百四十二万八千六百六十六。前者落到罗贝尔守方，再沿征召兵、长枪兵与骑士一人记录的各自路径，经过坚韧、截断和软硬伤拆分，接到下一日实机看到的人数变化。战斗后段，守方现役归零，追击的三天仍让硬伤累计增加约六十二点七八人当量，最后守方落败。开头看到的一千二百二十二名守军，就这样被战宽、出伤、逐团坚韧和追击，分段写进了战斗账本。下次你在游戏里遇到人数占优却输掉的战斗，就能从这些数字开始，寻找真正决定结果的条件。",
        "en": "One Messina battle anchors width, daily outgoing damage, regiment casualties and observed pursuit. The defender ultimately loses, and the visible battle states match the calculations shown beside them."
    },
}


def substitute(row: dict, before: str, after: str) -> None:
    value = row["zh"]
    if value.count(before) != 1:
        raise ValueError(f"{row['id']}: expected exactly one {before!r}")
    row["zh"] = value.replace(before, after)


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for old in source["cues"]:
        if old["id"] in DROP:
            continue
        row = dict(old)
        cue_id = row["id"]
        for key, value in REWRITE.get(cue_id, {}).items():
            row[key] = value
        if cue_id == "E1-F05":
            substitute(row, "现在换到另一场墨西拿之战的原始第五日回执。", "继续看这同一场墨西拿之战的原始第五日回执。")
            substitute(row, "界面通常显示取整后的人数，旁边的实机又是独立重放，所以它不会逐帧等于这份第五日回执。", "界面通常显示取整后的人数；这次左边就是原始战局录像的对应状态，可以对照约一千二百二十二名守军。")
            row["en"] = "In the original Messina footage, Robert's defender total of 122,225,074 raw corresponds to about 1,222.25 people. His levy regiment #50 has 6,282,657 raw, about 62.83, and pikemen #51 have 19,705,044 raw, about 197.05."
        if cue_id == "E1-F09":
            substitute(row, "后面另有一份静态追击公式向量，专门说明软伤怎样转为永久兵员损失；它不是墨西拿追击的逐日录像。", "后面我们直接看墨西拿自己第 28 到第 31 日的追击回执，核对永久损失怎样继续增加。")
            row["en"] = "The original Messina battle remains in maneuver on days one to three, enters the main phase on day four, and continues on day five. We later inspect this same battle's actual pursuit readbacks on days 28 to 31."
        if cue_id == "C01":
            substitute(row, "玩家在战斗窗能看到罗贝尔守军剩余的‘士兵’，却看不到整侧入伤 D 的内部大整数。刚才把两侧出伤算出来，但出伤不是死人。", "左边是罗贝尔守军同一场战斗的原片；战斗窗能看到剩余‘士兵’，却看不到整侧入伤 D 的内部大整数。刚才我们确实从这场仗算出了两侧出伤，但出伤不是死人。")
        row["visual_kind"] = "card"
        row["chapter_id"] = "episode-01-r7"
        row["subtitle_mode"] = "paragraph"
        row["visual_lines"] = list(row.get("visual_lines", row.get("visual_points", [])))
        row["visual_points"] = list(row["visual_lines"])
        row["source_label"] = "墨西拿原始战局 · CombatID 16777218 · 同场回执"
        row["evidence"] = "原始录像 gameplay-precontact-r2.mkv；原始逐日回执；Messina outgoing board v2"
        if cue_id == "E1-F02":
            row["source_label"] = "原版通用预测机制 · 墨西拿原始实机作说明"
            row["evidence"] = "docs/ck3-native-ai/combat-prediction.md；原始墨西拿实机"
        row["ui_bridge"] = "左：原始实机画面，面板人数取整；右：同场原生回执与内部算式"
        row["redraw_card"] = True
        row.pop("gameplay_start_seconds", None)
        row.pop("gameplay_seconds", None)
        row["source_time_seconds"], row["target_time_seconds"] = SOURCE_TIMES[cue_id]
        if len(row["visual_lines"]) != 3:
            raise ValueError(f"{cue_id}: three visible lines required")
        rows.append(row)
    if len(rows) != 23 or set(SOURCE_TIMES) != {row["id"] for row in rows}:
        raise ValueError("R7 source coverage mismatch")
    text = json.dumps({"format_version": 1, "purpose": "One original Messina battle with exact game footage", "game_version": "1.19.0.6", "cues": rows}, ensure_ascii=False, indent=2) + "\n"
    (HERE / "script.json").write_text(text, encoding="utf-8")
    (HERE / "timeline.json").write_text(json.dumps({"format_version": 1, "shots": [
        {"id": row["id"], "title": row["visual_title"]} for row in rows
    ]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R7 cues={len(rows)} Chinese characters={sum(len(row['zh']) for row in rows)}")


if __name__ == "__main__":
    main()
