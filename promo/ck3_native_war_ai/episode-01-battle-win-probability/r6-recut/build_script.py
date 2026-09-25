"""Build the reviewable R6 script from the frozen R4/R5 source scripts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ROOT / "full-film-unit-script-v3.json",
    ROOT / "math-ledger-unit/script.json",
    ROOT / "casualty-addendum/script.json",
    ROOT / "pursuit-detail/script.json",
]
ORDER = """E1-F01 E1-F02 E1-F03 E1-F04 M02 M03 M04 M05 M06 M07 M08
E1-F05 E1-F06 E1-F09 C01 C02 C03 C04 C05 C06 C07 C08 C09 E1-F19
C10 P01 P02 C11 E1-F20 E1-F23 E1-F24 E1-F25""".split()

REVISIONS = {
    "E1-F01": {
        "zh": "地图上，两支军队已经在墨西拿接战。人数和面板提示只能提供起点，战斗还要沿着阶段和每日结算继续。我们会先认参战者，计算整侧出伤，再看伤害怎样落到各兵团，软伤与永久兵员损失怎样写回，骑士事件何时改变下一日输入。本片逐步核对原版数字，也会分清实机、另一份战斗回执和静态公式向量。整场获胜概率还没有校准，所以今天讲计算链，不给一个假精确的百分比。",
        "en": "The Messina replay opens our route through native combat: identify the sides, calculate aggregate damage, allocate casualties, and update the next day. Separate live footage, other combat receipts, and static formula vectors. No whole-battle win probability is asserted.",
    },
    "M03": {
        "visual_title": "战宽缩放整侧出伤",
        "zh": "这一天的战宽是一千二百六十九，它是宽度参数，不是要除十万的人数原始值。零号侧当前二百一十五人，一号侧二千三百二十四人；这两个回执数已经按人展示。原版把一千二百六十九乘十万，除以二千三百二十四并截断，得到一号侧宽度比例原始值五万四千六百零四，也就是百分之五十四点六零四。零号侧未达到战宽，比例封顶十万，即百分之百。这个比例缩放整侧当天的出伤，不是在这里抽签决定哪一支兵团能打。",
        "en": "Combat width is 1,269 and the displayed strengths are 215 and 2,324 people. The side-one factor is floor(1,269 times 100,000 divided by 2,324), or 54,604 raw. This scales aggregate outgoing damage; it does not randomly select regiments.",
        "visual_lines": ["战宽 1,269；side1 现役 2,324 人：直接读", "floor(1,269 × 100,000 ÷ 2,324) = 54,604", "54,604 ÷ 100,000 = 54.604%：缩放整侧出伤"],
    },
    "E1-F09": {
        "zh": "原生战斗按阶段和游戏日结算。墨西拿原始战局的第一到第三日仍在机动，第四日进入主战，第五日继续主战，所以第五日不能沿用第一日开战画面的兵力。接下来的墨西拿数字，是第五到第六日守方兵团伤亡的实机回执。后面另有一份静态追击公式向量，专门说明软伤怎样转为永久兵员损失；它不是墨西拿追击的逐日录像。每前进一日，都要重新读取阶段、人数和有效属性。",
        "en": "Messina remains in maneuver on days one to three, enters the main phase on day four, and continues on day five. The casualty receipt covers days five to six. A later static vector explains pursuit arithmetic, but is not Messina pursuit footage.",
    },
    "C02": {
        "visual_lines": ["份额 floor(D × Q ÷ S) = 66,393", "比例 floor(66,393 × Q ÷ 1,000,000) = 6,639", "损失 floor(6,282,657 × 6,639 ÷ Q) = 417,105 raw"],
    },
    "C03": {
        "zh": "五十一号职业兵士当前兵力原始值一千九百七十万五千零四十四，除十万是约一百九十七点零五人；有效坚韧四百二十二万四千。先把人数原始值乘入伤八千一百一十四万九千九百七十二，再除十万，截断为一百五十九亿九千零六十三万七千六百八十八。第二步把这个中间值乘十万，除守方总兵力一亿二千二百二十二万五千零七十四，截断为一千三百零八万二千九百四十三。最后必须再乘十万，除坚韧四百二十二万四千，截断得到伤亡原始值三十万九千七百二十八。除十万才是实际约三点一零人的兵员损失。每一步的乘十万和截断都不能省。",
        "en": "For regiment 51, floor(19,705,044 times 81,149,972 divided by Q) is 15,990,637,688. Then floor(that times Q divided by 122,225,074) is 13,082,943. Finally floor(that times Q divided by 4,224,000) is 309,728 raw, or 3.09728 people.",
        "visual_lines": ["floor(19,705,044 × 81,149,972 ÷ Q) = 15,990,637,688", "floor(15,990,637,688 × Q ÷ 122,225,074) = 13,082,943", "floor(13,082,943 × Q ÷ 4,224,000) = 309,728 raw"],
    },
    "C04": {
        "zh": "六十五号是一人规模的职业兵士兵团：人数原始值九万九千一百一十一，除十万约零点九九人；坚韧原始值七百万。沿用职业兵士路径，先用人数乘入伤除十万，得八千零四十二万八千五百四十八。再把这个中间值乘十万，除守方总兵力，得六万五千八百零三。第三步还要乘十万，除七百万坚韧，才截断为九百四十原始伤亡，也就是零点零零九四人。这是兵团人数账。后来它关联的人物是否受伤或死亡，还要单独看骑士事件，不能把九百四十直接叫作一名骑士阵亡。",
        "en": "Regiment 65 has 99,111 raw soldiers and 7,000,000 raw toughness. Its intermediate values are 80,428,548 and 65,803. The final operation is floor(65,803 times Q divided by 7,000,000), yielding 940 raw casualties, or 0.0094 people. Character fate is separate.",
        "visual_lines": ["#65 99,111 raw = 0.99111 人；坚韧 7,000,000", "中间值 80,428,548 → 65,803；每次除法前乘 Q", "floor(65,803 × Q ÷ 7,000,000) = 940 raw"],
    },
    "C05": {
        "zh": "再把总伤亡分成软伤与硬伤。这一日核对到的有效软转硬系数原始值三万六千，除十万是百分之三十六。五十号征召兵损失四十一万七千一百零五原始值，乘三万六千再除十万，截断得硬伤十五万零一百五十七；剩余软伤二十六万六千九百四十八。五十一号职业兵士损失三十万九千七百二十八，按同样的最终有效系数，硬伤十一万一千五百零二，软伤十九万八千二百二十六。都要除十万才是人数：五十号硬伤约一点五零人、软伤约二点六七人；五十一号硬伤约一点一二人、软伤约一点九八人。当前作战人数减去总损失。硬伤在这里指永久兵员损失，不代表骑士人物死亡。",
        "en": "The effective hard-conversion factor is 36,000 raw, or 36%. Regiment 50 splits 417,105 raw into 150,157 hard and 266,948 soft. Regiment 51 splits 309,728 into 111,502 hard and 198,226 soft. Divide each soldier count by Q; hard loss is not proof of a character death.",
        "visual_lines": ["硬伤系数 36,000 ÷ Q = 36%", "#50：417,105 = 硬 150,157 + 软 266,948 raw", "#51：309,728 = 硬 111,502 + 软 198,226 raw"],
    },
    "C09": {
        "zh": "骑士事件要分触发、抽签和效果三层。普通受伤事件这一行的触发条件排除了已经三级伤势的人；所以不能说这行会抽中三级伤者再让他死亡。如果其他路径真的调用加深伤势效果，三级伤势可走到死亡；致残事件中的部分效果也会附加伤势。直接死亡行则直接执行人物死亡。墨西拿冻结第二十六日，六十五号兵团关联角色三万三千四百三十七选中载入表索引十一的死亡行，战报击杀者三万四千一百二十，后续边界读到角色死亡和退场。这只是一次已观察结果，不能反推通用死亡概率，也不存在已证实的先杀低坚韧兵团规则。",
        "en": "The ordinary knight-wounded event row excludes rank-three wounds at its trigger. A separate path that calls the increase-wounds effect at rank three may kill; some maiming effects add wounds; the direct death row kills. The Messina replay selected death row 11 for character 33,437. This observation is not a universal death rate.",
        "visual_lines": ["普通受伤行：触发条件排除 3 级伤势", "其他加伤效果遇 3 级可致死；直接死亡行直接杀", "第 26 日：#65 关联角色 33,437 选中死亡行"],
    },
    "E1-F19": {
        "visual_kind": "card",
        "zh": "另一份原版伤情反馈不是刚才第二十六日死亡事件。角色五万四千一百四十四的英勇先观察为四，随后为二。四个连续观察边界分别在第九日事件执行前、第十日排程前、第十日事件执行前和第十一日排程前；英勇依次是四、四、二、二。有效坚韧原始值依次是七百四十万、七百四十万、七百四十万、三百七十万；有效伤害依次是三千七百万、三千七百万、三千七百万、一千八百五十万。可见人物状态变化与兵团有效属性回读不是同一瞬间。若在后一个计算边界误用旧坚韧，复算会多出二百一十四个原始伤亡单位，折合零点零零二一四人当量；刷新有效值后残差归零。这是状态更新时序的证据，不能单凭这四个观测断言唯一因果。",
        "en": "In another observed wound case, prowess is 4, 4, 2, 2 across four boundaries. Effective toughness is 7.4, 7.4, 7.4, then 3.7 million raw; damage is 37, 37, 37, then 18.5 million raw. Reusing stale toughness creates a 214-raw casualty residual, or 0.00214 person-equivalent. These observations show timing, not unique causation.",
        "visual_points": ["四边界英勇：4 / 4 / 2 / 2", "坚韧 raw：7.4M / 7.4M / 7.4M / 3.7M", "旧值残差：214 raw = 0.00214 人当量"],
        "visual_lines": ["四边界英勇：4 / 4 / 2 / 2", "坚韧 raw：7.4M / 7.4M / 7.4M / 3.7M", "旧值残差：214 raw = 0.00214 人当量"],
        "source_label": "另一份原版伤情回执 · 非第 26 日死亡事件",
    },
    "C11": {
        "zh": "把静态追击向量的第一天结果读成人数：两支征召兵与一支职业兵士各自新增硬伤原始值七十九万一千五百八十四、五十六万五千四百一十六、九十万四千六百六十六。除十万后，分别是七点九一五八四、五点六五四一六、九点零四六六人当量，合计二十二点六一六六六。这里是追击导致的永久兵员损失，不能把每个小数当作一个确定死亡的具体角色。第二、第三日的预算仍根据阶段开始冻结的软伤池计算，却要受当天剩余软伤限制，因此不能把第一天直接乘三。坚韧既进入基础项又进入分母，局部作用可能抵消，也不能简单说坚韧翻倍就让追击损失减半。",
        "en": "This static vector yields hard losses of 791,584, 565,416 and 904,666 raw, equal to 7.91584, 5.65416 and 9.04666 person-equivalents. These are permanent soldier losses, not identified character deaths. Later days use the frozen pool budget but cap against remaining soft losses.",
        "visual_lines": ["静态向量，非墨西拿实机追击", "首日硬伤 raw：791,584 / 565,416 / 904,666", "÷ Q：7.91584 + 5.65416 + 9.04666 = 22.61666"],
    },
    "E1-F23": {
        "zh": "这套计算已经能给游玩智能体提供可用的局部战斗估计。R 零二一七与 R 零二二零的单日兵团记录逐项对拍，墨西拿第五日的五十号和五十一号还能把入伤、软硬分账及次日人数追到原版整数。静态追击向量则核对了公式与取整，但尚未提供墨西拿整场逐日追击回放。因此智能体可以把已闭合的日结算用于解释和局部比较，并保留对应存档、日期、阶段及输入来源。要把它升级为整场获胜概率，仍需校准增援、撤退和终局；自动进攻门禁继续按现有证据范围关闭。",
        "en": "The agent can use validated single-day calculations for local explanation and comparison, with exact source identity. A static pursuit vector verifies arithmetic but is not a full Messina pursuit replay. Reinforcement, retreat and terminal calibration remain before a whole-battle win probability is usable.",
        "visual_points": ["单日局部计算：可供智能体使用", "静态追击向量：公式验证", "整场概率：待增援、撤退、终局校准"],
        "visual_lines": ["单日局部计算：已对拍，可供智能体使用", "静态追击向量：核对公式和取整", "整场概率：待增援、撤退、终局校准"],
        "source_label": "能力边界 · 视频结论与游玩智能体共用",
    },
    "E1-F25": {
        "zh": "回到墨西拿地图，这一集走完了已验证的原版计算链：锁住参与者和战场条件，用优势、战宽与有效攻击算整侧出伤；把入伤分别送进兵团的坚韧公式，再按有效系数拆成软伤和永久兵员损失；人物事件在真正执行和属性回读后才改变后续输入。另用静态向量展示了追击第一天怎样继续消耗溃兵。你能用这些账解释一次局部交锋，也能看清为什么一张战前比例牌还不是整场胜率。以后我们再把增援、撤退与终局接上，逐步扩展智能体的整场判断。",
        "en": "We have followed validated daily damage, regiment casualties, character feedback, and a separate static pursuit example. This supports local combat reasoning, while a forecast for the whole battle still needs reinforcement, retreat and terminal calibration.",
    },
}


def pursuit_rows() -> list[dict]:
    source = json.loads(SOURCES[3].read_text(encoding="utf-8"))["cues"][0]
    first = dict(source, id="P01", shot_id="P01", chapter_id="pursuit", visual_title="追击算术：基础量与净追击")
    first["zh"] = "这里换成原版静态公式向量，不是墨西拿实机追击。两支征召兵的软伤分别是三百五十和二百五十人，职业兵士四百人。逐团有效坚韧乘各自软伤，再相加，得到软伤坚韧量原始值十四亿。胜方追击乘现役人数再乘零点五，得到两亿二千五百万；败方掩护乘软伤，得到两亿。基础百分之五乘十四亿，是七千万；最低百分之一是一千四百万；追击减掩护的正差是两千五百万。基础兜底项取七千万。这里的十四亿、两亿都是属性计算量，不是人口；软伤的一千人才是人数。"
    first["en"] = "Static native pursuit vector, not live Messina pursuit. Soft casualties are 350, 250 and 400 people. Toughness-weighted soft is 1.4 billion raw, pursuit 225 million and screen 200 million. The base is 70 million, minimum 14 million and positive extra 25 million raw."
    first["visual_lines"] = ["静态向量：软伤 350 + 250 + 400 = 1,000 人", "坚韧软伤 1,400,000,000；追击/掩护 225M/200M raw", "基础 70M；最低 14M；净追击 25M raw"]
    second = dict(source, id="P02", shot_id="P02", chapter_id="pursuit", visual_title="追击算术：每日预算与逐团分配")
    second["zh"] = "接着按征召兵六百人、职业兵士四百人的阶段初始软伤池，套用本例百分之百修正，再除三天并逐步截断。征召兵每天两项预算分别是：净追击项三十五万七千，基础项一百万原始值；职业兵士分别是二十三万八千与六十六万六千六百六十六。这里把前一项标为 A，也就是净追击；后一项标为 B，也就是基础兜底。征召兵第一团按三百五十除六百的份额，分到 A 二十万八千二百五十、B 五十八万三千三百三十三；第二团分到 A 十四万八千七百五十、B 四十一万六千六百六十六。第一次合计比预算少一个原始单位，按存储顺序补给第一团，首日两团硬伤就成为七十九万一千五百八十四和五十六万五千四百一十六；职业单团九十万四千六百六十六。每个硬伤原始值除十万才是人当量。"
    second["en"] = "A means net pursuit, B means base floor. Daily levy budgets A/B are 357,000/1,000,000 raw; men-at-arms 238,000/666,666. Allocate by the frozen soft-loss shares, then return the one-raw remainder to the first levy regiment. Day-one hard losses are 791,584, 565,416 and 904,666 raw."
    second["visual_lines"] = ["A=净追击；B=基础兜底；职业 A/B=238,000/666,666", "征召每日 A/B=357,000/1,000,000 raw", "逐团首日硬伤 raw：791,584 / 565,416 / 904,666"]
    return [first, second]


def main() -> None:
    source_rows = {}
    for source in SOURCES:
        for row in json.loads(source.read_text(encoding="utf-8"))["cues"]:
            source_rows[row["id"]] = row
    source_rows.update({row["id"]: row for row in pursuit_rows()})
    cues = []
    shots = []
    for cue_id in ORDER:
        row = dict(source_rows[cue_id])
        row.update(REVISIONS.get(cue_id, {}))
        row["shot_id"] = cue_id
        row["chapter_id"] = "episode-01-r6"
        cues.append(row)
        shots.append({"id": cue_id, "title": row["visual_title"]})
    assert len(cues) == 32 and len({row["id"] for row in cues}) == len(cues)
    here = Path(__file__).resolve().parent
    (here / "script.json").write_text(json.dumps({"format_version": 1, "purpose": "R6 full EdgeTTS recut", "game_version": "1.19.0.6", "cues": cues}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (here / "timeline.json").write_text(json.dumps({"format_version": 1, "shots": shots}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
