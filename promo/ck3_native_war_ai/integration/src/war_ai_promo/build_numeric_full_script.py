"""Create the numbered Episode 1 narration without changing historical scripts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


# Raw fixed-point values use Q=100,000. The Messina day-5 defender examples
# are bound to b005-control.json and b006-control.json of the original run.
# The R0217 outgoing example belongs to a separate, explicitly labelled tick.
REVISIONS = {
    "E1-F04": {
        "visual_points": ["R0217 战斗 ID 738197508", "同一日、同一双方顺序", "44 条兵团记录逐项绑定"],
        "zh": "先认准我们到底在算哪一场。一个已核验的原版主战日，战斗编号是七亿三千八百一十九万七千五百零八，双方合计有四十四条兵团记录。四十四条不是一个平均兵种，而是各自带有编号、阵营和当前人数的对象。复算时要同时锁住战斗编号、游戏日期、战场省份和双方顺序。若把另一日的兵力或另一次重放的伤亡塞进来，即使公式完全正确，结果也没有意义。后面我会把这个四十四条的出伤案例，和墨西拿另一份第五日守方伤亡案例，明确分开。",
        "en": "A verified R0217 tick binds CombatID 738197508 and 44 regiment records. Dates, sides, and replay identity stay bound; the later Messina casualty example is a separate receipt.",
        "evidence": "battle-simulation.md R0217；原版 combat identity 与兵团记录",
    },
    "E1-F05": {
        "visual_points": ["墨西拿第 5 日守方总兵 122,225,074 raw", "征召兵 #50：6,282,657 raw", "职业兵 #51：19,705,044 raw"],
        "zh": "换到墨西拿原始回执的第五日，这一侧守方当前参战总量是一亿二千二百二十二万五千零七十四个原版定点单位。里面的五十号征召兵团当前是六百二十八万二千六百五十七，五十一号职业兵团是一千九百七十万五千零四十四。单位的缩放是十万，所以这不是一亿多名士兵，而是约一千二百二十二点二五的参战人数。五十号只有约六十二点八三人，五十一号约一百九十七点零五人。以后入伤要分别落到这两个兵团，不能只对一千二百二十二这个总数扣一次。",
        "en": "On the original Messina day 5, defender fighting strength is raw 122,225,074. Levy #50 is 6,282,657 and men-at-arms #51 is 19,705,044, all scaled by 100,000.",
        "evidence": "墨西拿原始 b005-control.json；b006-control.json；Q100000",
    },
    "E1-F06": {
        "visual_points": ["墨西拿基础战宽 1,645", "森林倍率 90,000 ÷ 100,000 = 0.9", "最终战宽截断为 1,480"],
        "zh": "再看地形如何进入一个真正的数。墨西拿这一战在对应日期读到基础战宽一千六百四十五，森林的定点倍率是九万，也就是零点九。先算一千六百四十五乘九万，除以十万，得到一千四百八十点五；原版按整数截断，最终战宽是一千四百八十。渡口仍必须由实际进入目标省份的最后一段边和攻守身份判定，不能凭地图截图猜一条河。森林这个一千四百八十的结果，随后才会和两侧当天还在战斗的人数相比。",
        "en": "Messina width: 1,645 times forest multiplier 90,000 / 100,000 is 1,480.5, truncated to 1,480. Crossing depends on the native final contact edge.",
        "evidence": "墨西拿原始战场回执；battle-simulation.md 战宽路径",
    },
    "E1-F07": {
        "visual_points": ["R0217 战宽 1,269", "2,324 人：比例 54,604 ÷ 100,000", "215 人：比例封顶 100,000"],
        "zh": "战宽不是把总人数直接砍成一千二百六十九人。在另一份标为 R 零二一七的原版主战日，宽度一千二百六十九，一侧当前二千三百二十四人。把一千二百六十九乘十万，再除以二千三百二十四，向下截断，得到五万四千六百零四；也就是这侧当天只按百分之五十四点六零四的宽度比例出伤。另一侧只有二百一十五人，宽度比已超过一，所以封顶为十万。两个数字接下来分别乘到各自的伤害链里，额外兵力不会使当天输出无限上涨。",
        "en": "In separate R0217, width 1,269 against 2,324 fighting gives floor(1,269×100,000/2,324)=54,604. The 215-person side is capped at 100,000.",
        "evidence": "battle-simulation.md R0217；Q100000",
    },
    "E1-F08": {
        "visual_points": ["有效伤害、坚韧、追击、掩护", "骑士伤害 37,000,000 → 18,500,000", "坚韧 7,400,000 → 3,700,000"],
        "zh": "兵种卡片的基础值不能直接代替战场有效值。原版对象会给出当前的伤害、坚韧、追击和掩护四维属性。一个可核对的事件反馈例子里，骑士受伤后英勇由四降到二；下一日边界，他的有效伤害从三千七百万降到一千八百五十万，恰好减半，有效坚韧也从七百四十万降到三百七十万，恰好减半。这里的除二只是这条已观察到的状态变化，不代表所有属性修正都能概括成一个统一乘数。复算当日必须重新读取四维有效值。",
        "en": "A witnessed knight wound changes prowess 4 to 2 and next-day effective damage 37,000,000 to 18,500,000, toughness 7,400,000 to 3,700,000.",
        "evidence": "combat-phase-feedback-battle-horizon.md 骑士伤情；battle-simulation.md 有效属性",
    },
    "E1-F09": {
        "visual_points": ["墨西拿第 1–3 日：机动", "第 4 日：首个主战日", "第 5 日：下一主战日"],
        "zh": "原生战斗先走阶段，再走当天的结算。墨西拿这份原始战局，第一、第二、第三日仍在机动；第四日才进入主战，第五日是后续主战日。于是第五日的当前兵力，不可能继续用第一日开战画面的数。主战以后还可能进入追击和结束，但这部片逐步算出的数字只覆盖已经闭合的主战出伤与伤亡。每前进一个游戏日，先读新的阶段、双方兵团当前人数和优势状态，再按这一日的公式走。",
        "en": "The original Messina trace spends days 1–3 in maneuver, enters main battle on day 4, then continues main battle on day 5. Daily inputs must be refreshed.",
        "evidence": "墨西拿 original_case.json phase_traces；battle-simulation.md",
    },
    "E1-F10": {
        "visual_points": ["R0217 side0：优势系数 100,000", "R0217 side1：优势系数 145,000", "同一缩放 3,000，后续逐步截断"],
        "zh": "优势不能凭固定统帅值推整场。在 R 零二一七这一个已绑定的日结算里，零号侧的当日优势系数是十万，也就是一；一号侧是十四万五千，也就是一点四五。原版这一路径的伤害缩放是三千，也就是零点零三。于是零号侧第一乘是十万乘三千除十万，仍为三千；一号侧是十四万五千乘三千除十万，得到四千三百五十。这个整数继续交给战宽和有效攻击的下一步，不能把一天的掷骰当作整场常数。",
        "en": "For R0217, side 0's advantage multiplier 100,000 yields 3,000 after the 3,000 scaling; side 1's 145,000 yields 4,350. The next steps use these truncated integers.",
        "evidence": "battle-simulation.md R0217；原版主战出伤路径",
    },
    "E1-F11": {
        "visual_points": ["side1 优势 145,000 × 缩放 3,000", "第一步截断为 4,350", "第二步乘宽度 54,604 → 2,375"],
        "zh": "把 R 零二一七的一号侧主战出伤直接列出来。优势系数十四万五千乘原版伤害缩放三千，除十万并截断，第一步是四千三百五十。再把四千三百五十乘战宽占比五万四千六百零四，除十万，整数第二步是两千三百七十五。到这里还不是最终伤害，只是接下来乘反制后有效攻击的中间系数。原版每一步都把截断后的整数交给下一步，这就是这一日实际执行的计算。",
        "en": "R0217 side 1: floor(145,000×3,000/100,000)=4,350; floor(4,350×54,604/100,000)=2,375 before effective attack.",
        "evidence": "battle-simulation.md R0217 原版主战出伤；Q100000",
    },
    "E1-F12": {
        "visual_points": ["第三步：2,375 × 4,911,382,134", "除 100,000 → 116,645,325 raw", "side0 同理得 12,414,304 raw"],
        "zh": "继续 R 零二一七的一号侧。反制后有效攻击在这一次回执里是四十九亿一千一百三十八万二千一百三十四个原始单位。刚才保留下来的两千三百七十五，乘这个攻击值、除十万并截断，最终一号侧当天出伤是一亿一千六百六十四万五千三百二十五。零号侧则用自己的三千和四亿一千三百八十一万零一百四十四，有效宽度比例封顶十万，算出一千二百四十一万四千三百零四。两侧的原版回读与这两个结果一致。",
        "en": "R0217 side 1 final: floor(2,375×4,911,382,134/100,000)=116,645,325 raw. Side 0 computes 12,414,304 raw.",
        "evidence": "battle-simulation.md R0217 原版出伤回执；Q100000",
    },
    "E1-F13": {
        "visual_title": "实算守方入伤：征召兵",
        "visual_points": ["入伤 81,149,972；守方总量 122,225,074", "份额 66,393；除坚韧得 6,639", "#50 当日总伤亡 417,105"],
        "zh": "现在用墨西拿原始回执第五日到第六日，实算守方收到的伤害。攻击方第五日原版出伤是八千一百一十四万九千九百七十二，这就是守方入伤；守方当前参战总量是一亿二千二百二十二万五千零七十四。先看五十号征召兵，当前人数六百二十八万二千六百五十七，有效坚韧一百万。征召兵分支先算入伤乘十万、除守方总量，截断得六万六千三百九十三；再乘十万、除坚韧一百万，截断得六千六百三十九；最后拿当前人数乘六千六百三十九、除十万，截断为四十一万七千一百零五。原版下一日这条兵团记录确实减少四十一万七千一百零五个定点单位。",
        "en": "Messina day 5→6 defender levy #50: incoming 81,149,972 / side 122,225,074 gives share 66,393; divide by toughness 1,000,000 gives ratio 6,639; current 6,282,657 yields total loss 417,105.",
        "evidence": "墨西拿原始 b005/b006-control.json；combat_core.py levy 分支",
    },
    "E1-F14": {
        "visual_title": "实算守方入伤：职业兵",
        "visual_points": ["#51：19,705,044 × 81,149,972 ÷ Q", "中间值 15,990,637,688 → 13,082,943", "除坚韧 4,224,000 → 309,728"],
        "zh": "同一笔入伤进入五十一号职业兵时，原版换了乘除顺序。五十一号当前人数一千九百七十万五千零四十四，有效坚韧四百二十二万四千。先把当前人数乘入伤八千一百一十四万九千九百七十二，再除十万并截断，得一百五十九亿九千零六十三万七千六百八十八。再把它乘十万、除守方总量一亿二千二百二十二万五千零七十四，截断为一千三百零八万二千九百四十三。最后乘十万、除坚韧四百二十二万四千，得到三十万九千七百二十八。游戏第六日的五十一号记录正好少了三十万九千七百二十八。这里两种兵团不是直接按同一个浮点比例扣人。",
        "en": "Messina day 5→6 defender MAA #51: floor(19,705,044×81,149,972/Q)=15,990,637,688; divided by side 122,225,074 gives 13,082,943; divided by toughness 4,224,000 gives loss 309,728.",
        "evidence": "墨西拿原始 b005/b006-control.json；combat_core.py MAA 分支",
    },
    "E1-F15": {
        "visual_title": "软硬伤亡怎样写回",
        "visual_points": ["#50：417,105 → 硬 150,157＋软 266,948", "#51：309,728 → 硬 111,502＋软 198,226", "#50 当前 6,282,657 → 5,865,552"],
        "zh": "还差最后一个账本。第五日这侧的有效软转硬系数，从原版拆分结果核对为三万六千，也就是百分之三十六；这里只能断言最终有效系数，不把缺失的当日各项修正凭空拆开。五十号总伤亡四十一万七千一百零五，乘三万六千、除十万并截断，硬伤亡十五万零一百五十七；总数减硬伤亡，软伤亡二十六万六千九百四十八。五十一号总伤亡三十万九千七百二十八，同样乘三万六千除十万，硬伤亡十一万一千五百零二，软伤亡十九万八千二百二十六。于是五十号当前人数由六百二十八万二千六百五十七，减四十一万七千一百零五，变成五百八十六万五千五百五十二。游戏第六日的这三项回读都吻合。",
        "en": "The observed effective hard conversion is 36,000. Levy #50: 417,105 total → 150,157 hard and 266,948 soft; current 6,282,657→5,865,552. MAA #51: 309,728 → 111,502 hard and 198,226 soft.",
        "evidence": "墨西拿原始 b005/b006-control.json；battle-simulation.md 硬伤亡换算",
    },
    "E1-F16": {
        "visual_points": ["载入事件表：13 行", "本次选中全局索引 11", "排程、执行、状态回读分三处"],
        "zh": "数字算完，还要看事件怎样改下一日输入。一次冻结的墨西拿原版事件回放中，载入事件表共有十三行，实际选中的全局行索引是十一，对应骑士阵亡事件。索引十一是从零开始数的第十二行，不是百分之十一的概率。原版先排程，再执行效果，再回读战报与角色状态；这些不是同一个时间点。模型只在状态真的改变的边界更新人物与兵团，不能在候选事件刚排进日程时就提前扣除骑士。",
        "en": "A frozen Messina replay has 13 loaded phase-event rows; selected global index 11 is the knight-killed event. Index 11 identifies a row, not an 11% probability.",
        "evidence": "messina_selected_phase_event_row.json；combat-phase-event-trace.md",
    },
    "E1-F17": {
        "visual_points": ["事件阶段全局计数 421,195 → 421,197", "两侧各消耗一个原版随机调用", "内部击杀抽签未直接观测"],
        "zh": "随机数也有账本。在那次冻结事件回放的阶段选择边界，全局随机计数从四十二万一千一百九十五走到四十二万一千一百九十七，一共前进两次，分别对应双方的事件选择路径。但这两个已观测到的调用，不等于骑士被击杀的最终概率。事件效果内部还会使用自己的随机状态，深层击杀抽签没有同级别的直接回读。因此本片只把十三行中的第十一号选择和后续实际状态讲清，不报一个无法证实的死亡百分比。",
        "en": "The observed phase-selection RNG counter moves 421,195→421,197 across the two sides. Deeper effect-local kill selection is not directly observed, so no death probability is claimed.",
        "evidence": "phase_fire_draw_projection.json；effect_root_observation.json",
    },
    "E1-F18": {
        "visual_points": ["冻结第 26 日：索引 11 的骑士阵亡", "目标角色 33,437；战报击杀者 34,120", "边界 4→5 记账，边界 6 退场"],
        "zh": "这次观察有一个能核对的结果。冻结回放第二十六日，载入事件表十三行中的索引十一被选中，目标角色编号三万三千四百三十七；战报记录的击杀者编号三万四千一百二十。事件账本在边界四到五之间出现，到了边界六，目标的死亡和退出战场才从角色与兵团状态中读到。这里的三个数字分别是事件索引、目标身份和击杀者身份，不是三个抽签概率。把战报和状态分开，才能知道骑士从哪一天开始不再提供战力。",
        "en": "On frozen day 26, event row 11 targets character 33,437 and the battle ledger names killer 34,120. The ledger appears at boundary 4→5; death and withdrawal are read at boundary 6.",
        "evidence": "messina_selected_phase_event_row.json；effect_root_observation.json",
    },
    "E1-F19": {
        "visual_points": ["另一例：英勇 4 → 2", "有效伤害 37,000,000 → 18,500,000", "有效坚韧 7,400,000 → 3,700,000"],
        "zh": "死亡之外，再看另一份原版伤情反馈，注意它不是刚才第二十六日死亡事件的同一条结果。角色五万四千一百四十四受伤，所属兵团二百二十；英勇从四变成二。下一日边界重新读取有效属性，伤害三千七百万变成一千八百五十万，坚韧七百四十万变成三百七十万。若仍沿用受伤前缓存，复算和原版之间出现二百一十四个原始单位的残差；刷新输入后残差归零。这说明事件反馈不是结尾花絮，而是下一日计算必须重读的实参。",
        "en": "A separate wound case, character 54,144/regiment 220, changes prowess 4→2, effective damage 37,000,000→18,500,000 and toughness 7,400,000→3,700,000. Refreshing clears a 214-raw residual.",
        "evidence": "ck3_1_19_0_6_episode01_messina_phase_event_regiment_feedback.json",
    },
    "E1-F20": {
        "visual_points": ["R0220 原版出伤：135,136,791 / 39,435,780", "两侧按兵团 ID 共核对 54 行", "该日 54 行差值均为 0"],
        "zh": "这套复算有多大证据范围？另一个标为 R 零二二零的原版主战日，双方当天出伤分别是一亿三千五百一十三万六千七百九十一和三千九百四十三万五千七百八十个原始单位。我们随后按兵团编号对齐两侧记录，共五十四行，比较各行的总伤亡、软伤亡和硬伤亡；这个单日边界里五十四行差值都是零。五十四是兵团行数，不是五十四场战斗，更不是整场胜率的五十四次抽样。它证明绑定条件下这一日的账能对上，下一日或另一场仗仍要重新绑定输入。",
        "en": "In separate R0220, native outgoing raw values are 135,136,791 and 39,435,780. Fifty-four regiment rows have zero residual for this single bound tick, not 54 battles.",
        "evidence": "battle-simulation.md R0220 原版对拍；按 RegimentID 核对",
    },
    "E1-F23": {
        "visual_points": ["R0217：44 行单日闭合", "R0220：54 行单日闭合", "整场胜率仍无合格生产者"],
        "zh": "真正能交给游玩智能体的，是有明确输入和明确适用范围的计算。我们有 R 零二一七四十四条兵团的单日对拍，也有 R 零二二零五十四条兵团的单日对拍；墨西拿第五日的守方五十号与五十一号，又能把入伤、伤亡拆分和下一日人数逐项算到原版结果。这样的能力可以解释当天为什么损失这么分配，也能供智能体比较已闭合的局部交锋。但是整场胜率还需要把增援、撤退、追击和终局串起来校准；自动进攻门禁因此仍保持关闭，不能把当前力量比冒充最终获胜概率。",
        "en": "Bounded agent use includes R0217's 44-row and R0220's 54-row daily parity, plus Messina defender casualty arithmetic. A calibrated whole-battle probability is not yet available.",
        "evidence": "battle-simulation.md R0217/R0220；combat_core.py；strategy.py",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    script = json.loads(args.source.read_text(encoding="utf-8"))
    found = set()
    for row in script["cues"]:
        revision = REVISIONS.get(row["id"])
        if revision:
            row.update(revision)
            found.add(row["id"])
    if found != set(REVISIONS) or args.output.exists():
        raise ValueError("script cue mismatch or output exists")
    script["purpose"] = "Episode 1 numbered native-calculation cut; distinct receipts never combined"
    args.output.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cues": len(script["cues"]), "revised": len(found),
                      "chinese_characters": sum(len(row["zh"]) for row in script["cues"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
