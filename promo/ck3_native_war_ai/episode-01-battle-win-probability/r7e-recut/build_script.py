"""Derive the R7E editorial recut from the immutable R7 same-battle source."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "r7-same-battle" / "script.json"
TARGET = HERE / "script.json"


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {row["id"]: dict(row) for row in source["cues"]}
    assert len(rows) == 23

    def edit(ident: str, *, zh: str | None = None, en: str | None = None,
             title: str | None = None, cards: list[str] | None = None,
             source_time: int | None = None, target_time: int | None = None) -> None:
        row = rows[ident]
        if zh is not None:
            row["zh"] = zh
        if en is not None:
            row["en"] = en
        if title is not None:
            row["visual_title"] = title
        if cards is not None:
            assert len(cards) == 3
            row["visual_lines"] = cards
            row["visual_points"] = cards
        if source_time is not None:
            row["source_time_seconds"] = source_time
        if target_time is not None:
            row["target_time_seconds"] = target_time

    edit("E1-F01",
         title="墨西拿：数字跳得很快，账却一笔笔记",
         zh="墨西拿。罗贝尔的守军，前一日还有一千二百二十二人。日历翻过一页，战斗窗里只剩一千一百五十六。数字跳得很快，账却是一笔一笔记下的。这六十六名现役士兵，究竟从哪一步开始退出战线？我们把这一天倒回去：森林给出战宽，双方算出伤害，入伤再经过每支兵团各自的坚韧。今天，就让原版把墨西拿的这一笔账，算给你看。",
         en="At Messina, Robert's active defenders change from 1,222 to 1,156 across adjacent battle days. That is 66 fewer on the displayed combat window. We follow this same battle's width, damage, and regiment toughness to explain key steps behind the change.",
         cards=["墨西拿 · 罗贝尔守方", "1,222 → 1,156", "相邻游戏日 · 少 66 名现役"],
         source_time=275, target_time=280)
    edit("E1-F03",
         title="把战斗窗两帧接到底层人数",
         zh="现在把刚才的两帧和原生回执接上。原片二百七十五秒，墨西拿守方罗贝尔约一千二百二十二人，进攻方约一千九百二十一人；到二百八十秒，守方约一千一百五十六，进攻方约一千八百六十。底层第五日边界的守方人数是原始整数一亿二千二百二十二万五千零七十四，除十万等于一千二百二十二点二五零七四人；下一边界一亿一千五百六十二万九千八百七十四，折合一千一百五十六点二九八七四人。精确少了六十五点九五二人当量，所以画面上的六十六是取整后的差。我们会始终把游戏窗和内部计算分开标注。",
         en="The original 275-second frame shows roughly 1,222 defenders and 1,921 attackers; the 280-second frame shows 1,156 and 1,860. Defender strength changes from 122,225,074 to 115,629,874 raw, a 65.952 person-equivalent reduction. The displayed difference of 66 is rounded.",
         cards=["原片 275 秒：守方 1,222 / 攻方 1,921", "原片 280 秒：守方 1,156 / 攻方 1,860", "底层守方差 6,595,200 raw = 65.952 人当量"],
         source_time=275, target_time=280)
    edit("E1-F04",
         zh="先锁定身份，避免把别的战斗或别的日期算进来。原生回执里的战斗编号一六七七七二一八，省份二六三三，就是画面上的墨西拿。研究编号 side 零是进攻方，side 一是玩家罗贝尔的守军；编号只负责把画面与回执接起来，不是游戏给军队的名字。我们选第五到第六日相邻边界：同一场、同一省份，源日两侧人数与出伤都已冻结，下一日能回读兵团损失。往后的数字只沿这笔账走。",
         en="CombatID 16777218 in province 2633 is this Messina battle. Research side 0 is the attacker; side 1 is Robert's defenders. We pair the fifth-day native inputs with the sixth-day readback from the same battle.")
    edit("E1-F09",
         zh="原生战斗是一台按阶段、按日推进的机器。这场墨西拿战斗第 1 到第 3 日处于调动，第 4 日进入主要阶段，第 5 日仍在主要阶段。我们现在算的是第 5 到第 6 日这一次主战结算，不能拿开战第一日的人数代入。每前进一日，都要重新读取当日阶段、人数和有效属性。片尾再回到本场第 28 到第 31 日，观察真实追击。",
         en="Messina has maneuver on days 1–3 and its main phase from day 4. Our arithmetic uses the day 5 to day 6 main-phase boundary, with that day's strength and effective attributes. Later we revisit this battle's pursuit on days 28–31.")
    edit("E1-F06",
         zh="这一日的战宽也能按原版整数步骤算出来。墨西拿的基础战宽一千六百四十五；森林地形倍率是九万，除十万为零点九。一千六百四十五乘九万，再除十万，是一千四百八十点五；截断后实际战宽一千四百八十。游戏把它叫战线宽度，可从战斗窗的相对军力提示查看。这个一千四百八十马上要与两侧当日参战人数比较。渡口则必须按实际入省边和攻守身份判定，不能只看地图猜。",
         en="For this Messina day, base battle width 1,645 times forest factor 90,000 / 100,000 is 1,480.5; integer truncation leaves 1,480. Crossing is a separate question determined by the actual entry edge.")
    edit("E1-F02",
         title="战前提示不是整场胜率",
         zh="现在回头看战前预测，别把它误当成刚才这套逐日账的最终概率。原版预测比较眼前双方的相对力量，并给玩家‘可能获胜’等等级提示；真正的战斗按阶段和游戏日继续走。即使研究路径里看到零点六的内部比较值，也不能把它念成百分之六十的整场获胜概率。这场墨西拿战斗，我们展示的是同日出伤、逐团损失和之后观察到的追击；判断战前提示时，要把它与实际结算分开。",
         en="Native pre-battle prediction is a current relative-power comparison with qualitative UI labels. A research ratio of 0.6 is not a calibrated 60% probability of winning the whole battle. The Messina calculations shown here belong to the daily resolver.",
         cards=["战前提示：当前力量比较", "实战：按阶段、按游戏日结算", "内部比例 ≠ 整场获胜概率"],
         source_time=250, target_time=260)
    edit("C05",
         zh=rows["C05"]["zh"].replace("有效软转硬系数", "有效硬伤拆分比例"),
         en=rows["C05"]["en"].replace("effective hard-conversion factor", "effective hard-loss split"),
         cards=["主战硬伤拆分比例 36,000 ÷ Q = 36%",
                "罗贝尔征召兵 #50：417,105 = 硬 150,157 + 软 266,948 raw",
                "罗贝尔长枪兵 #51：309,728 = 硬 111,502 + 软 198,226 raw"])
    edit("C10",
         zh="现在看这场墨西拿战斗后半段。第 28 日进入追击，顶部战斗提示里，罗贝尔守方仍在作战的现役人数已经是零；但原片四百二十秒下方战斗窗的红字仍显示七百六十一名败退兵力。零说的是现役，七百六十一说的是败退，不能混为一谈。原生回执里，守方第 28 日累计硬伤四千六百三十六万七千七百七十六原始单位，除十万约四百六十三点六八人当量。第 29 日升到四千八百四十三万二千八百九十一，比前一天增加二百零六万五千一百一十五，约二十点六五人。第 30 日升到五千零五十二万四千五百九十，再增二百零九万一千六百九十九，约二十点九二人。第 31 日升到五千二百六十四万五千三百五十一，再增二百一十二万零七百六十一，约二十一点二一人。三日新增合计六百二十七万七千五百七十五，折合六十二点七七五七五人当量。这是同一场战斗真实追击中继续增长的永久兵员损失。",
         en="In the actual Messina pursuit, the top tooltip shows zero active Robert fighters; the lower red combat-window number is 761 retreating soldiers at source second 420. Those are different counts. Defender cumulative hard loss rises from 46,367,776 raw on day 28 by 2,065,115, 2,091,699 and 2,120,761 raw on days 29–31, a three-day increase of 6,277,575 raw or 62.77575 person-equivalents.",
         cards=["顶部现役 0；原片 420 秒下方红字 761 为败退兵力",
                "累计硬伤 46,367,776 → 48,432,891 → 50,524,590 → 52,645,351 raw",
                "三日分别 +2,065,115 / +2,091,699 / +2,120,761 raw；合计 62.77575 人当量"])
    edit("E1-F23",
         zh="这笔账也可以交给游玩智能体的研究内核。复算墨西拿第五日两侧出伤，输入除了同日战宽、两侧人数和反制后的有效攻击，还必须带上当日优势系数和固定伤害缩放。代入后，攻方出伤八千一百一十四万九千九百七十二，守方出伤七千九百四十二万八千六百六十六。前者成为罗贝尔守军入伤，再按每支兵团自己的人数与坚韧，得到征召兵、长枪兵及骑士一人条目的局部兵员损失，与下一日回执比对。追击段则能读出同场累计硬伤仍在增加。这样，研究内核已经能解释这一天部分损失，比较战场条件变化对局部出伤的影响；它使用的就是片中这套同日整数步骤。",
         en="The agent research kernel can reproduce this battle day's local calculation when given same-day width, strength, advantage factors, fixed damage scaling, and post-counter effective attack. The resulting 81,149,972 and 79,428,666 outgoing values feed regiment-level loss explanations and conditional comparisons; the pursuit trace supplies observed hard-loss changes.",
         cards=["复算输入：当日战宽、人数、优势、固定缩放、有效攻击",
                "同场出伤：攻方 81,149,972 / 罗贝尔守方 79,428,666",
                "逐团坚韧解释局部兵损；追击回读硬伤变化"])
    edit("E1-F24",
         zh="下次旁观自己的存档，可以先读玩家真正看得到的东西：谁在进攻、战场位置、兵种、人数、地形、战线宽度和优势。游戏日推进后，对照战斗窗前后兵力，以及溃逃士兵、战死士兵的显示。若要像本片这样追到逐团原始整数、有效坚韧和每次截断，就得另用同场原生回执；这些大数不是界面上的隐藏按钮。墨西拿这一日，进攻方约一千九百二十一人，对应战宽一千四百八十；守方从约一千二百二十二变成约一千一百五十六。先把界面里可见的变化认准，再让回执解释其关键计算。",
         en="In the game UI, identify the attacking armies, terrain, width, advantage, troop counts, and visible routed or killed losses. Exact per-regiment raw strength, effective toughness, and truncation steps come from the same-battle research trace, not from a hidden UI button. Messina's displayed defenders change from 1,222 to 1,156.",
         cards=["玩家界面：双方、地形、战宽、优势、人数",
                "相邻日：读战斗窗与溃逃/战死显示",
                "研究回执：逐团 raw、有效坚韧、截断步骤"])
    edit("E1-F25",
         zh="回到墨西拿。森林把基础战宽一千六百四十五变成一千四百八十；约一千九百二十一名进攻者受限，宽度份额原始值七万七千零三十四。优势、固定缩放和反制后攻击依次进入整数公式，得到攻方出伤八千一百一十四万九千九百七十二，罗贝尔守方出伤七千九百四十二万八千六百六十六。前者落到守方兵团，我们沿征召兵、长枪兵和骑士图尔吉塞的一人战斗记录，核对了局部兵员损失与软硬伤拆分；原片也显示守方从一千二百二十二变为一千一百五十六。战斗后段，守方现役归零，追击三日让累计硬伤再增加约六十二点七八人当量，最终守方落败。下次战斗窗数字跳动时，就从这一条线追问：战宽限制了谁，伤害落到哪里，坚韧又让谁留在战线上。",
         en="Messina's forest width is 1,480; attack width fraction is 77,034 raw. Same-day outgoing damage is 81,149,972 for the attacker and 79,428,666 for Robert. The film follows three representative defender entries through local losses, then observes 62.77575 further person-equivalents of hard loss across three pursuit days before Robert's defeat.",
         cards=["森林战宽 1,480；攻方宽度份额 77,034 raw",
                "同日出伤：81,149,972 / 79,428,666 内部值",
                "追击三日新增硬伤约 62.78 人当量；罗贝尔守方落败"])

    order = [
        "E1-F01", "E1-F03", "E1-F04", "M02", "E1-F09", "E1-F06",
        "M03", "M04", "M05", "M06", "M07", "M08", "E1-F05",
        "C01", "C02", "C03", "C04", "C05", "C10", "E1-F02",
        "E1-F23", "E1-F24", "E1-F25",
    ]
    assert len(order) == len(set(order)) == len(rows)
    source["cues"] = [rows[ident] for ident in order]
    source["purpose"] = "R7E editorial recut of one original Messina battle with exact gameplay footage"
    TARGET.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
