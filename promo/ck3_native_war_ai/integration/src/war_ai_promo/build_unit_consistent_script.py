"""Derive the unit-labelled Episode 1 cut without altering the R3 record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


# Only regiment strength and casualty registers in this cut are scaled headcounts.
# Width, IDs, dates, row counts, and random counters are not people to divide by Q.
# Damage/attribute registers are calculation quantities, never casualty counts.
OBSERVATION_REVISIONS = {
    "E1-F03": {
        "visual_points": ["画面：同存档独立重放", "人数：原始整数 ÷ 100,000", "精确数值：绑定研究回执"],
        "zh": "你现在看到的是原版十字军之王三的实机，镜头自动追着墨西拿战场走。这是同一接触点存档的独立重放，和研究数值所用的原始战局在第六天以后分叉。因此，画面上的几百或几千人，是这一次重放当时的界面人数；后面逐项计算的精确数字，来自另外标明日期和战斗身份的原始回执。还有一个更重要的单位问题：引擎保存兵团人数和伤亡时，常用放大十万倍的原始整数。凡是这类数字，我会先说原始值，再除以十万，报出实际约多少人。伤害、战宽、角色编号则各有自己的单位，不能统统当成人数。",
        "en": "Footage is a separate replay. For regiment strength and casualty registers, divide raw fixed-point integers by 100,000 to get people-equivalent values. Damage and IDs are not headcounts.",
    },
    "E1-F05": {
        "visual_kind": "card",
        "visual_title": "兵力原始值怎样变成人数",
        "visual_points": [
            "守方 122,225,074 ÷ 100,000 ≈ 1,222.25 人",
            "#50 6,282,657 ÷ 100,000 ≈ 62.83 人",
            "#51 19,705,044 ÷ 100,000 ≈ 197.05 人",
        ],
        "zh": "换到墨西拿原始回执的第五日，先读懂屏幕和计算器的两种写法。守方参战人数的引擎原始整数是，一亿二千二百二十二万五千零七十四；除去十万倍的计算缩放，实际约一千二百二十二点二五人，并不是一亿多人。五十号征召兵团，原始整数六百二十八万二千六百五十七，除以十万，实际约六十二点八三人。五十一号职业兵团，原始整数一千九百七十万五千零四十四，除以十万，实际约一百九十七点零五人。界面通常显示取整后的人数，旁边的实机又是独立重放，所以它不会逐帧等于这份第五日回执。后续伤亡要分别落到兵团，不能只从守方总数扣一次。",
        "en": "Original Messina day 5 defender raw 122,225,074 / Q is about 1,222.25 people. Regiment #50 raw 6,282,657 is about 62.83; #51 raw 19,705,044 is about 197.05. Footage is a separate replay.",
    },
    "E1-F07": {
        "visual_points": ["战宽 1,269：未放大的宽度", "本例人数 2,324 / 215：直接按人读", "比例 54,604 ÷ 100,000 = 54.604%"],
        "zh": "这里先分清三种数字。在另一份标为 R 零二一七的原版主战日，战宽一千二百六十九是宽度参数，直接读，不再除十万。该回执里的二千三百二十四人和二百一十五人，也已经是按人读的现役人数。只有下面算出的比例保留了十万倍定点缩放：一千二百六十九乘十万，除以二千三百二十四，向下截断得到原始比例五万四千六百零四；去掉缩放就是零点五四六零四，也就是百分之五十四点六零四。二百一十五人没有碰到战宽上限，比例封顶十万，即百分之百。这样，宽度参数、界面人数和定点比例不会混成一类。",
        "en": "R0217 width 1,269 and displayed fighting counts 2,324 / 215 are direct units. Only the resulting fraction 54,604 is scaled: divide by 100,000 to obtain 54.604%.",
    },
    "E1-F08": {
        "visual_points": ["有效伤害原始属性：37,000,000 → 18,500,000", "有效坚韧原始属性：7,400,000 → 3,700,000", "这些是属性计算量，不是士兵人数"],
        "zh": "兵种卡片的基础值不能直接代替战场有效值。原版对象会给出当前伤害、坚韧、追击和掩护四维属性。这里出现的大整数是有效属性的计算原始值，不是几千万士兵。一个可核对的事件反馈里，骑士受伤后英勇由四降到二；下一日边界，有效伤害原始值从三千七百万降到一千八百五十万，恰好减半，有效坚韧原始值从七百四十万降到三百七十万，也恰好减半。这里的除二只说明这一条已观察到的状态变化。它们会影响下一次伤害计算，但绝不能拿这些属性数直接和界面人数比较。",
        "en": "Effective damage and toughness figures are raw attribute quantities, not soldiers. A witnessed wound halves the knight's prowess and these two effective attributes.",
    },
    "E1-F13": {
        "visual_points": ["入伤 81,149,972：伤害值，不是人数", "#50 6,282,657 ÷ Q ≈ 62.83 人", "损失 417,105 ÷ Q ≈ 4.17105 人"],
        "zh": "现在用墨西拿原始回执第五日到第六日，实算守方收到的伤害。攻击方当日出伤的原始计算值八千一百一十四万九千九百七十二，是伤害，不是八千多万人；守方参战人数原始值一亿二千二百二十二万五千零七十四，除以十万是约一千二百二十二点二五人。五十号征召兵的当前人数原始值六百二十八万二千六百五十七，换算后约六十二点八三人；有效坚韧原始值一百万，也是属性，不是人数。先用入伤乘十万再除守方总人数原始值，截断得到份额原始值六万六千三百九十三。再用这份额乘十万除坚韧，得到损失比例原始值六千六百三十九，相当于百分之六点六三九。最后用兵团人数原始值六百二十八万二千六百五十七乘六千六百三十九除十万，截断得到伤亡原始值四十一万七千一百零五；去掉十万倍人数缩放，实际约损失四点一七人。下一日的兵团原始人数确实少了这个数。",
        "en": "Incoming raw damage 81,149,972 is not people. Defender raw strength 122,225,074 is about 1,222.25 people; levy #50 raw 6,282,657 is about 62.83. Raw loss 417,105 / Q is 4.17105 people-equivalent.",
    },
    "E1-F14": {
        "visual_kind": "card",
        "visual_points": ["#51 19,705,044 ÷ Q ≈ 197.05 人", "中间值 15,990,637,688 → 13,082,943：伤害计算量", "损失 309,728 ÷ Q ≈ 3.09728 人"],
        "zh": "同一笔入伤进入五十一号职业兵时，原版换了乘除顺序。五十一号当前人数的原始整数是一千九百七十万五千零四十四，除十万以后实际约一百九十七点零五人。入伤原始计算值仍是八千一百一十四万九千九百七十二；有效坚韧原始值四百二十二万四千。这两个是伤害和属性，不是人口。先把兵团人数原始值乘入伤原始值，除十万并截断，得中间计算值一百五十九亿九千零六十三万七千六百八十八；它仍然不是人数。再乘十万，除守方参战人数原始值一亿二千二百二十二万五千零七十四，得到另一中间值一千三百零八万二千九百四十三。最后乘十万，除有效坚韧原始值四百二十二万四千，得到兵团伤亡原始值三十万九千七百二十八；除十万，实际约损失三点一零人。下一日五十一号兵团的原始人数，正好减少三十万九千七百二十八。",
        "en": "Regiment #51 raw strength 19,705,044 / Q is 197.05 people. Intermediate arithmetic values are not people. Final raw casualty 309,728 / Q is about 3.09728 people.",
    },
    "E1-F15": {
        "visual_points": ["#50 损失 417,105 ÷ Q = 4.17105 人", "#51 损失 309,728 ÷ Q = 3.09728 人", "#50 剩余 5,865,552 ÷ Q ≈ 58.66 人"],
        "zh": "最后把伤亡写回。第五日这侧的有效软转硬系数原始值三万六千，除十万是百分之三十六；这里只断言核对过的最终有效系数。五十号总伤亡原始值四十一万七千一百零五，换算实际四点一七一零五人。乘系数再截断，硬伤亡原始值十五万零一百五十七，实际一点五零一五七人；总数减去它，软伤亡原始值二十六万六千九百四十八，实际二点六六九四八人。五十一号总伤亡原始值三十万九千七百二十八，实际三点零九七二八人。其中硬伤亡原始值十一万一千五百零二，即一点一一五零二人；软伤亡原始值十九万八千二百二十六，即一点九八二二六人。五十号人数原始值六百二十八万二千六百五十七，减去当日损失原始值四十一万七千一百零五，剩五百八十六万五千五百五十二；除十万，实际从约六十二点八三降到约五十八点六六人。界面会取整显示，原版下一日原始回执的计算整数则逐项吻合。",
        "en": "Raw losses divide by Q: #50 total 417,105 = 4.17105 people, hard 150,157 = 1.50157, soft 266,948 = 2.66948. #51 total 309,728 = 3.09728, hard 111,502 = 1.11502, soft 198,226 = 1.98226. #50 remaining raw 5,865,552 = 58.65552 people.",
    },
    "E1-F19": {
        "visual_points": ["另一例：英勇 4 → 2", "有效属性原始值：伤害 37,000,000 → 18,500,000", "有效属性原始值：坚韧 7,400,000 → 3,700,000"],
        "zh": "死亡之外，再看另一份原版伤情反馈，注意它不是刚才第二十六日死亡事件的同一条结果。角色五万四千一百四十四受伤，所属兵团二百二十；英勇从四变成二。下一日边界重新读取有效属性：伤害计算原始值三千七百万变成一千八百五十万，坚韧计算原始值七百四十万变成三百七十万。这些不是士兵人数；人数变化要另读兵团当前人数和伤亡字段。若仍沿用受伤前缓存，复算和原版之间出现二百一十四个原始计算单位的残差；刷新输入后残差归零。",
        "en": "A separate knight wound halves prowess and raw effective attributes; these large attribute registers are not soldier counts. Refreshing them removes a 214-unit residual.",
    },
    "E1-F20": {
        "visual_points": ["R0220 出伤原始值：135,136,791 / 39,435,780", "这是伤害计算量，不是兵力", "54 条兵团伤亡记录逐项零差"],
        "zh": "这套复算的证据范围还有另一份样本。标为 R 零二二零的原版主战日，双侧当日出伤原始计算值分别是一亿三千五百一十三万六千七百九十一和三千九百四十三万五千七百八十。请把它们读成伤害值，绝不是一亿多人或三千多万人。随后按兵团编号对齐两侧记录，共五十四行，比较各行的总伤亡、软伤亡和硬伤亡，这个单日边界里五十四行差值都是零。五十四是兵团记录行数，不是五十四场战斗。它证明绑定条件下这一日的账能对上，下一日仍须重读人数原始值，并除十万才能和界面人数比较。",
        "en": "R0220 values 135,136,791 / 39,435,780 are raw outgoing damage, not people. Fifty-four regiment casualty rows have zero residual in this bound tick.",
    },
}

MATH_REVISIONS = {
    "M02": {
        "visual_lines": ["兵团人数/伤亡：实际人 = raw ÷ 100,000", "战宽/已显示人数：直接读；无需再除", "伤害原始值：计算量，不是阵亡人数"],
        "zh": "先统一数字语言。本片有三类容易混淆的数。兵团当前人数和伤亡的引擎原始整数用十万倍缩放：原始值十万，才相当于一人；例如原始值四十一万七千一百零五，除十万，实际约四点一七人。战宽和回执已经显示成整数的人数则直接读，不要重复除十万。伤害与属性上的大整数是计算量，不能直接念成多少人。定点运算每乘一次，先把原始整数乘起来，再除十万并截断，把留下的整数交给下一步。",
        "en": "For regiment strength and casualties, raw / 100,000 gives people-equivalent values. Width and already displayed counts are direct. Damage registers are calculation quantities, not casualty counts.",
    },
    "M03": {
        "visual_lines": ["战宽 1,269；side1 现役 2,324 人：直接读", "floor(1,269 × 100,000 ÷ 2,324) = 54,604", "宽度比例 54,604 ÷ 100,000 = 54.604%"],
        "zh": "这一天的战宽是一千二百六十九，这是宽度参数，不是要除十万的人数原始值。side 零当前二百一十五人，side 一当前二千三百二十四人；这两个回执数已经按人展示，也不用再除十万。side 一超过战宽，把一千二百六十九乘十万，除以二千三百二十四并截断，得到宽度比例的原始值五万四千六百零四。只有这个比例要去掉十万倍缩放，实际是百分之五十四点六零四。side 零只有二百一十五人，未达到宽度上限，比例封顶十万，即百分之百。",
        "en": "Width 1,269 and fighting counts 2,324 / 215 are direct values. Only fraction raw 54,604 is scaled, giving 54.604%.",
    },
    "M04": {
        "visual_lines": ["优势原始系数 145,000 ÷ Q = 1.45", "宽度比例 54,604 ÷ Q = 54.604%", "反制后攻击 4,911,382,134：属性计算量"],
        "zh": "现在摆出 side 一的输入。优势系数原始值十四万五千，除十万等于一点四五。固定伤害缩放原始值三千，除十万是零点零三。宽度比例原始值五万四千六百零四，实际百分之五十四点六零四。最后，反制与修正后的有效攻击 R 十四，原始计算值四十九亿一千一百三十八万二千一百三十四。这个大数是伤害链里的攻击属性，不是四十九亿名士兵，也不是已经出现的伤亡。接下来按原版次序使用这些原始整数运算。",
        "en": "Advantage raw 145,000 means 1.45; width fraction raw 54,604 means 54.604%. R14 4,911,382,134 is raw effective attack, not people.",
    },
    "M07": {
        "visual_lines": ["2,375 × 4,911,382,134 = 11,664,532,568,250", "÷ 100,000 → side1 出伤 raw 116,645,325", "side0 出伤 raw 12,414,304；两者都非人数"],
        "zh": "第三步，把两千三百七十五乘反制后有效攻击原始值四十九亿一千一百三十八万二千一百三十四。屏幕写出完整整数乘积，再除十万截断，得到 side 一当日出伤原始值一亿一千六百六十四万五千三百二十五。请把它读成伤害计算值，绝不是一亿多名士兵；能损失多少人，还要进入各兵团的坚韧和伤亡公式。另一边 side 零前两步留下三千，乘自己的有效攻击原始值四亿一千三百八十一万零一百四十四，除十万得到出伤原始值一千二百四十一万四千三百零四，同样不是人数。双侧都和原版回读一致。",
        "en": "The final raw outgoing damage is 116,645,325 for side one and 12,414,304 for side zero. These are damage quantities, never troop counts; losses require regiment formulas.",
    },
    "M08": {
        "visual_lines": ["side0 / side1 出伤 raw：12,414,304 / 116,645,325", "伤害计算值 ≠ 人数；经坚韧公式才得伤亡", "兵团伤亡 raw ÷ 100,000 = 实际人"],
        "zh": "把两个出伤数放回原版战斗：side 零原始伤害值一千二百四十一万四千三百零四，side 一原始伤害值一亿一千六百六十四万五千三百二十五。这里没有哪一边损失一亿多人。游戏接着把伤害分配给具体兵团，结合它们当天的坚韧算出伤亡，再更新软伤、硬伤与当前人数。这些兵团伤亡和人数如果以十万倍原始整数呈现，就要逐项除十万才是实际人数。同一 R 零二一七日的四十四条兵团伤亡记录，按编号对拍零差。下一日读到的是更新后的战斗状态。",
        "en": "Outgoing damage values are calculation quantities. Each regiment then gets scaled casualty and strength registers; divide those by 100,000 to compare with people shown in the interface.",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation-source", type=Path, required=True)
    parser.add_argument("--observation-output", type=Path, required=True)
    parser.add_argument("--math-source", type=Path, required=True)
    parser.add_argument("--math-output", type=Path, required=True)
    args = parser.parse_args()
    for source, output, revisions in (
        (args.observation_source, args.observation_output, OBSERVATION_REVISIONS),
        (args.math_source, args.math_output, MATH_REVISIONS),
    ):
        if output.exists():
            raise FileExistsError(output)
        data = json.loads(source.read_text(encoding="utf-8"))
        seen = set()
        for row in data["cues"]:
            if row["id"] in revisions:
                row.update(revisions[row["id"]])
                seen.add(row["id"])
        if seen != set(revisions):
            raise ValueError(f"Unexpected cue set in {source}: {seen}")
        data["purpose"] += "; R4 raw-to-people units stated beside every scaled headcount"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{output}: revised {len(seen)} of {len(data['cues'])} cues")


if __name__ == "__main__":
    main()
