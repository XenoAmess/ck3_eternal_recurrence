"""Recut Episode 1 so every research quantity has a player-facing identity."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "r61-recut" / "script.json"

UI_BRIDGE = {
    "E1-F02": "游戏中：战前预测是‘你可能会获胜’等提示；内部比值并非胜率",
    "E1-F04": "游戏中：敌军由尼基弗鲁斯率领；玩家是罗贝尔；side 是研究索引",
    "M02": "游戏中：士兵/军团人数；raw÷100,000；伤害大数是内部量",
    "M03": "游戏中：相对军力提示里的战线宽度；敌军 side0 / 罗贝尔 side1",
    "M04": "游戏中：优势伤害加成 +45%；R14 是整侧内部有效攻击",
    "M05": "游戏中：罗贝尔军的优势；4,350 是内部计算中间值",
    "M06": "游戏中：战线宽度影响罗贝尔军出伤；2,375 是内部中间值",
    "M07": "游戏中：罗贝尔军 vs 尼基弗鲁斯敌军；出伤大数无单独面板",
    "M08": "游戏中：士兵、溃逃士兵、战死士兵；出伤仍是内部量",
    "E1-F05": "游戏中：罗贝尔守军；#50 征召兵、#51 长枪兵、#65 骑士图尔吉塞",
    "E1-F06": "游戏中：战线宽度与森林地形；渡口须按接触边判定",
    "E1-F09": "游戏中的阶段：调动 → 主要阶段 → 追击",
    "C01": "游戏中：罗贝尔守军士兵；入伤 D 与逐团份额是内部量",
    "C02": "游戏中：罗贝尔的征召兵军团；#50 只是回执编号",
    "C03": "游戏中：罗贝尔的长枪兵军团；#51 只是回执编号",
    "C04": "游戏中：罗贝尔军骑士图尔吉塞；#65 是一人战斗记录",
    "C05": "游戏中：溃逃士兵=软伤；战死士兵=永久硬伤",
    "C06": "游戏中：能看到军团剩余兵力；底层组件与尾账无单独面板",
    "C07": "游戏中：长枪兵的坚韧；本例的有效值随状态改变",
    "C08": "游戏中：骑士名单和战报；排程与抽签权重为内部量",
    "C09": "游戏中：罗贝尔骑士图尔吉塞 / 敌军骑士阿姆鲁；#65 是回执号",
    "E1-F19": "游戏中：拉马丹敌军骑士阿什拉夫；勇武/伤势会影响有效属性",
    "C10": "游戏中：追击阶段、溃逃士兵和战死士兵",
    "P01": "公式示例：三支虚构兵团；追击/掩护是游戏兵士属性",
    "P02": "公式示例：A/B 是教学代号；游戏不显示两栏预算",
    "P03": "公式示例：逐团分配与尾数是内部账，不是墨西拿实机",
    "C11": "游戏中：追击让溃逃士兵转为战死士兵；三团数为静态向量",
    "E1-F20": "R0220：另一份原版单日回执；双方人物名尚无可靠绑定",
    "E1-F23": "游戏中：局部交锋可解释；整场胜率仍非可用 UI 输出",
    "E1-F24": "游戏中：士兵、军团、战线宽度、优势、坚韧、溃逃/战死",
    "E1-F25": "游戏中：每次看一场战斗的阶段、人数、伤亡与战报",
}

REPLACEMENTS = {
    "E1-F02": [
        ("假如屏幕出现零点六，那只能按对应字段的定义读成比较比例，不能未经证明就翻译成百分之六十获胜。",
         "玩家在战前预测里看到的是‘你可能会获胜’等等级提示，而不是一个已校准的胜率。研究路径里若出现零点六的内部比较值，也不能翻译成百分之六十获胜。"),
    ],
    "E1-F03": [
        ("这是同一接触点存档的独立重放，", "这是玩家罗贝尔同一接触点存档的独立重放，"),
    ],
    "E1-F04": [
        ("先认准我们到底在算哪一场。", "先认准我们到底在算哪一场。这份 R 零二一七回执不是墨西拿：side 零是尼基弗鲁斯率领的敌军，side 一是玩家罗贝尔军。side 只是引擎内部侧索引，不是游戏中某支军队的名称。"),
    ],
    "M02": [
        ("先统一数字语言。", "先统一游戏界面和研究回执两套数字语言。游戏显示‘士兵’和‘军团’，我们底层回执则保存对应原始整数。"),
        ("战宽和回执已经显示成整数的人数", "游戏称‘战线宽度’的战宽，和回执已经显示成整数的人数"),
    ],
    "M03": [
        ("这一天的战宽是一千二百六十九", "游戏界面称之为‘战线宽度’。这一天的战线宽度是一千二百六十九"),
        ("零号侧当前二百一十五人，一号侧二千三百二十四人", "零号侧是尼基弗鲁斯率领的敌军，当前二百一十五人；一号侧是玩家罗贝尔军，当前二千三百二十四人"),
    ],
    "M04": [
        ("现在摆出 side 一的输入。", "现在摆出玩家罗贝尔军，也就是这场样本的 side 一的输入。游戏面板有‘优势’、‘战线宽度’和兵士的‘伤害’属性；下面的整侧有效攻击 R 十四则是内部聚合量，界面不会显示这个大整数。"),
    ],
    "M05": [("按原版指令顺序，先让优势系数", "对玩家罗贝尔军，按原版指令顺序，先让优势系数")],
    "M06": [("第二步，四千三百五十", "罗贝尔军这一侧的第二步，四千三百五十")],
    "M07": [
        ("第三步，把两千三百七十五", "罗贝尔军这一侧的第三步，把两千三百七十五"),
        ("得到 side 一当日出伤", "得到玩家罗贝尔军，也就是 side 一，当日出伤"),
        ("另一边 side 零前两步", "另一边尼基弗鲁斯率领的敌军，也就是 side 零，前两步"),
    ],
    "M08": [
        ("side 零原始伤害值", "尼基弗鲁斯敌军、即 side 零，原始伤害值"),
        ("side 一原始伤害值", "玩家罗贝尔军、即 side 一，原始伤害值"),
    ],
    "E1-F05": [
        ("换到墨西拿原始回执的第五日，先读懂屏幕和计算器的两种写法。",
         "现在换到另一场墨西拿之战的原始第五日回执。防御方是玩家罗贝尔的军队：研究编号五十是征召兵军团，五十一是游戏名为‘长枪兵’的军团，六十五则关联骑士图尔吉塞。编号方便我们对账，不是你在战斗界面认兵种时要念的名字。先读懂屏幕和计算器的两种写法。"),
        ("五十一号职业兵团", "五十一号长枪兵军团"),
    ],
    "E1-F06": [("再看地形如何进入一个真正的数。", "游戏把这一项叫‘战线宽度’，可从战斗窗的相对军力提示查看。再看森林地形如何进入这个数。")],
    "E1-F09": [("第一到第三日仍在机动，第四日进入主战，第五日继续主战", "第一到第三日处于界面所称的‘调动’阶段，第四日进入‘主要阶段’，第五日仍在主要阶段")],
    "C01": [("刚才把两侧出伤算出来，但出伤不是死人。", "玩家在战斗窗能看到罗贝尔守军剩余的‘士兵’，却看不到整侧入伤 D 的内部大整数。刚才把两侧出伤算出来，但出伤不是死人。")],
    "C02": [("看五十号征召兵。", "看玩家罗贝尔军中的征召兵军团。研究回执叫它五十号，界面则让你按兵种和人数认出它。")],
    "C03": [
        ("五十一号职业兵士当前兵力", "玩家罗贝尔军中的长枪兵军团，研究编号五十一，当前兵力"),
    ],
    "C04": [
        ("六十五号是一人规模的职业兵士兵团：", "六十五号对应的是罗贝尔军骑士图尔吉塞的一人战斗记录。存档直接把这条记录连到人物三万三千四百三十七；它在伤亡计算中位于兵士条目容器，却不是长枪兵那样的普通兵士种类。"),
        ("沿用职业兵士路径", "沿用该条目容器的整数路径"),
    ],
    "C05": [
        ("再把总伤亡分成软伤与硬伤。", "游戏战斗窗把软伤一侧称为‘溃逃士兵’，把永久硬伤一侧称为‘战死士兵’；后者也包括重伤到不能再战的人。再把总伤亡分成这两本账。"),
        ("五十一号职业兵士", "五十一号长枪兵"),
    ],
    "C06": [("那有没有谁先死的顺序？", "军团底层组件和它的尾账在普通战斗界面看不到，只能读原始记录。那有没有谁先死的顺序？")],
    "C07": [("五十一号原版实机的伤害份额", "罗贝尔的长枪兵军团，也就是五十一号，在原版实机中的伤害份额")],
    "C08": [("骑士人物层另走阶段事件。", "游戏界面能看到骑士和战报，却不会列出下面的排程和抽签权重。骑士人物层另走阶段事件。")],
    "C09": [("骑士事件要分触发、抽签和效果三层。", "继续跟踪罗贝尔军中的骑士图尔吉塞；他在研究回执里关联六十五号。骑士事件要分触发、抽签和效果三层。"),
            ("战报击杀者三万四千一百二十", "战报中的击杀者三万四千一百二十，是敌方塔米姆军的骑士阿姆鲁")],
    "E1-F19": [("另一份原版伤情反馈不是刚才第二十六日死亡事件。角色五万四千一百四十四", "另一份原版伤情反馈发生在敌方拉马丹军中的骑士阿什拉夫身上，不是刚才图尔吉塞第二十六日的死亡事件。回执角色五万四千一百四十四")],
    "C10": [("胜负确定后，能撤退的一侧才可能进入追击；", "游戏把这一段叫‘追击’，战斗窗能看到溃逃士兵与战死士兵的变化；下述整侧加权量是内部计算。胜负确定后，能撤退的一侧才可能进入追击；")],
    "P01": [("这里换成原版静态公式向量，不是墨西拿实机追击。", "这里的三支军团是原版公式的静态示例，没有墨西拿战场上的玩家、真实兵种或人物对应；它不是墨西拿实机追击。")],
    "P02": [("先把净追击项 A 和基础兜底项 B 算成定点比例。", "A 和 B 是我们给两项内部预算起的教学代号，游戏界面没有这两栏。先把净追击项 A 和基础兜底项 B 算成定点比例。")],
    "P03": [("现在把征召兵每日预算分给两支兵团。", "这仍是静态公式示例，不是罗贝尔军的真实追击镜头。现在把征召兵每日预算分给两支兵团。")],
    "C11": [("把静态追击向量的第一天结果读成人数：", "在游戏界面，这意味着溃逃士兵的一部分转成了战死士兵；A/B 预算及尾数只存在内部账。把静态追击向量的第一天结果读成人数：")],
    "E1-F20": [("这套复算的证据范围还有另一份样本。", "最后还有第三份原版单日样本 R 零二二零。它的战斗与日期已绑定，但本片没有可靠证据给那两侧起人物名，所以只用于核对单日账，绝不让你把它认成罗贝尔的墨西拿战斗。")],
    "E1-F24": [("再看兵种、当前人数、地形、战宽与将领优势；", "再看游戏面板上的军团兵种、士兵人数、地形、战线宽度与优势；")],
    "E1-F25": [("用优势、战宽与有效攻击算整侧出伤", "用面板可辨的优势、战线宽度和内部聚合的有效攻击算整侧出伤")],
}

ENGLISH = {
    "E1-F04": "Separate R0217: side zero is the enemy army commanded by Nikephoros; side one is player Robert's army. The labels are internal side indices, not names shown in the combat window. Its CombatID is 738197508 with 44 regiment records.",
    "C02": "Robert's levy regiment is research ID 50. Its exact fixed-point steps are floor(D times Q divided by side strength)=66,393; floor(66,393 times Q divided by toughness 1,000,000)=6,639; floor(6,282,657 times 6,639 divided by Q)=417,105 raw, or 4.17105 people-equivalents.",
    "C03": "Robert's pikemen regiment is research ID 51. It has 19,705,044 raw soldiers, or about 197.05 people. Its three fixed-point steps produce 15,990,637,688, then 13,082,943, then 309,728 raw casualties, or 3.09728 people.",
    "C04": "Research ID 65 is the one-person combat entry for Robert's knight Turgise, character 33,437. It is stored in the men-at-arms entry path but is not an ordinary men-at-arms type. The arithmetic yields 80,428,548, then 65,803, then 940 raw soldier losses; character injury or death is separate.",
    "E1-F19": "This is enemy Ramadan's knight Ashraf, character 54,144, in a different wound event. His prowess is observed as 4, 4, 2, 2; effective toughness changes from 7.4 to 3.7 million raw only at a later boundary. This is not Turgise's day-26 death event.",
    "P01": "These three regiments are a static native formula vector, not named troops from Messina. Pursuit and screen are visible men-at-arms attributes; the 1.4-billion toughness-weighted sum and 225/200-million totals are internal calculations.",
}

TITLES = {
    "E1-F04": "另一场原版战斗：罗贝尔与敌军",
    "C02": "罗贝尔征召兵 #50：三次截断",
    "C03": "罗贝尔长枪兵 #51：三次截断",
    "C04": "骑士图尔吉塞 #65：两本账",
    "C07": "长枪兵的坚韧怎样影响伤亡",
    "E1-F19": "骑士阿什拉夫：事件改变下一日输入",
}

# Keep the underlying numbers visible while putting the player's names on the
# same card. These replacements affect visuals only; narration inputs stay byte
# for byte identical when this script is regenerated after TTS preparation.
VISUAL_REPLACEMENTS = {
    "M03": [("side1 现役", "罗贝尔军 side1 现役")],
    "M07": [("side1 出伤", "罗贝尔军 side1 出伤"), ("side0 出伤", "尼基弗鲁斯敌军 side0 出伤")],
    "M08": [("side0 / side1 出伤", "尼基弗鲁斯敌军 side0 / 罗贝尔军 side1 出伤")],
    "E1-F05": [("#50 6,282,657", "罗贝尔征召兵 #50 6,282,657"), ("#51 19,705,044", "罗贝尔长枪兵 #51 19,705,044")],
    "E1-F09": [("机动", "调动"), ("首个主战日", "首个主要阶段日"), ("下一主战日", "下一个主要阶段日")],
    "C05": [("#50：", "罗贝尔征召兵 #50："), ("#51：", "罗贝尔长枪兵 #51：")],
    "C07": [("固定 #51 份额", "固定长枪兵 #51 份额")],
    "C09": [("#65 关联角色", "骑士图尔吉塞 #65 关联角色")],
    "E1-F19": [("四边界英勇", "四边界勇武")],
    "C10": [("征召兵/职业兵", "征召兵/兵士")],
    "P02": [("职业 A/B", "兵士 A/B")],
}

SOURCE_LABELS = {
    "E1-F02": "原版战前预测与逐日结算 · 比较值非胜率",
    "E1-F04": "R0217 · CombatID 738197508 · 非墨西拿",
    "M02": "原版计数单位 · 人数/伤亡 raw 与 UI 对照",
    "M03": "R0217 · 战线宽度与双方当日兵力",
    "M04": "R0217 · 罗贝尔军整侧伤害输入",
    "M05": "R0217 · 罗贝尔军定点计算第 1 步",
    "M06": "R0217 · 罗贝尔军定点计算第 2 步",
    "M07": "R0217 · 双侧主战日出伤",
    "M08": "R0217 · 双侧出伤与逐团伤亡",
    "E1-F05": "墨西拿 · 原始第 5 日罗贝尔守军",
    "E1-F06": "墨西拿 · 森林战线宽度",
    "E1-F09": "墨西拿 · 原始第 1–5 日阶段",
    "C02": "墨西拿第 5→6 日 · 罗贝尔征召兵 #50",
    "C03": "墨西拿第 5→6 日 · 罗贝尔长枪兵 #51",
    "C04": "墨西拿第 5→6 日 · 骑士图尔吉塞 #65",
    "E1-F20": "R0220 · 另一场原版单日回执 · 人物未绑定",
    "E1-F24": "观战方法 · 按游戏界面核对不同案例",
    "E1-F25": "本集总结 · 原版算术与不同证据边界",
}


def replace_once(value: str, old: str, new: str, cue_id: str) -> str:
    if value.count(old) != 1:
        raise ValueError(f"{cue_id}: expected one occurrence of {old!r}, got {value.count(old)}")
    return value.replace(old, new, 1)


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for old in source["cues"]:
        row = dict(old)
        cue_id = row["id"]
        for before, after in REPLACEMENTS.get(cue_id, []):
            row["zh"] = replace_once(row["zh"], before, after, cue_id)
        if cue_id == "E1-F19":
            if row["zh"].count("英勇") != 2:
                raise ValueError("E1-F19: expected two legacy prowess terms")
            row["zh"] = row["zh"].replace("英勇", "勇武")
        if cue_id in ENGLISH:
            row["en"] = ENGLISH[cue_id]
        if row["visual_kind"] == "card":
            row["ui_bridge"] = UI_BRIDGE[cue_id]
            row["redraw_card"] = True
            row["visual_lines"] = list(row.get("visual_lines", row.get("visual_points", [])))
            if len(row["visual_lines"]) != 3:
                raise ValueError(cue_id + ": card needs exactly three visible claims")
            for before, after in VISUAL_REPLACEMENTS.get(cue_id, []):
                matches = sum(line.count(before) for line in row["visual_lines"])
                if matches != 1:
                    raise ValueError(f"{cue_id}: visual {before!r} appears {matches} times")
                row["visual_lines"] = [line.replace(before, after, 1) for line in row["visual_lines"]]
            # Legacy rows keep this alias; synchronize it so a source reader
            # cannot see an obsolete unit name while the renderer shows the new one.
            row["visual_points"] = list(row["visual_lines"])
        if cue_id in TITLES:
            row["visual_title"] = TITLES[cue_id]
        if cue_id in SOURCE_LABELS:
            row["source_label"] = SOURCE_LABELS[cue_id]
        if row["visual_kind"] == "card" and not row.get("source_label"):
            raise ValueError(f"{cue_id}: every card needs an explicit source scope")
        row["subtitle_mode"] = "paragraph"
        rows.append(row)
    assert len(rows) == 33 and set(UI_BRIDGE) == {row["id"] for row in rows if row["visual_kind"] == "card"}
    (HERE / "script.json").write_text(json.dumps({
        "format_version": 1,
        "purpose": "R6.2 source-bound player names and UI concepts beside native raw calculations",
        "game_version": "1.19.0.6", "cues": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "timeline.json").write_text(json.dumps({"format_version": 1, "shots": [
        {"id": row["id"], "title": row["visual_title"]} for row in rows
    ]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
