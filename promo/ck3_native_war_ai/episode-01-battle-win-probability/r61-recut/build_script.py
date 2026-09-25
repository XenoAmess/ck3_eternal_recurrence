"""Build R6.1 with complete pursuit arithmetic and paragraph captions."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
R6 = HERE.parent / "r6-recut" / "script.json"


def main() -> None:
    source = json.loads(R6.read_text(encoding="utf-8"))
    cues = []
    for old in source["cues"]:
        row = dict(old)
        row["subtitle_mode"] = "paragraph"
        if row["id"] == "C04":
            row["visual_lines"] = [
                "floor(99,111 × 81,149,972 ÷ Q) = 80,428,548",
                "floor(80,428,548 × Q ÷ 122,225,074) = 65,803",
                "floor(65,803 × Q ÷ 7,000,000) = 940 raw",
            ]
        if row["id"] == "P02":
            row["visual_title"] = "追击算术：两项每日预算"
            row["zh"] = (
                "先把净追击项 A 和基础兜底项 B 算成定点比例。A 用两千五百万乘十万，除十四亿并截断，"
                "得到一千七百八十五；B 用七千万乘十万除十四亿，得到五千。两个比例都不是人数。"
                "征召兵的阶段初始软伤池是六千万原始人数，也就是六百人。A 先算六千万乘一千七百八十五除十万，"
                "得到一百零七万一千；本例修正为百分之百，所以不变；再按三日定点除法，等于三十五万七千原始单位。"
                "B 用六千万乘五千除十万，先得三百万，再除三日，得到一百万。职业兵士初始软伤池四千万，"
                "即四百人；对应 A 先得七十一万四千，除三日是二十三万八千；B 先得两百万，除三日截成"
                "六十六万六千六百六十六。A 是净追击，B 是基础兜底，两项预算还不是逐团最终损失。"
            )
            row["en"] = (
                "For A, floor(25 million times Q divided by 1.4 billion) is 1,785 raw; "
                "for B, floor(70 million times Q divided by 1.4 billion) is 5,000. "
                "The initial levy soft pool is 60 million raw: A gives 1,071,000 before division by three, "
                "then 357,000; B gives 3,000,000 then 1,000,000. "
                "The 40-million men-at-arms pool yields A 238,000 and B 666,666 raw per day."
            )
            row["visual_lines"] = [
                "A=floor(25M × Q ÷ 1.4B)=1,785；B=5,000",
                "征召 A：60M × 1,785 ÷ Q = 1,071,000；÷3=357,000",
                "征召 B=1,000,000；职业 A/B=238,000/666,666 raw",
            ]
        cues.append(row)
        if row["id"] == "P02":
            part = dict(row)
            part.update({
                "id": "P03", "shot_id": "P03", "visual_title": "追击算术：逐团分配与尾数",
                "zh": (
                    "现在把征召兵每日预算分给两支兵团。第一团软伤三百五十人，第二团二百五十人，"
                    "当前征召兵软伤池六百人。对每一项预算，原版先乘该团软伤，再除六百人的池，且每步都用十万倍定点整数截断。"
                    "第一团从 A 三十五万七千分到二十万八千二百五十，从 B 一百万分到五十八万三千三百三十三，"
                    "初次合计七十九万一千五百八十三。第二团分别分到十四万八千七百五十和四十一万六千六百六十六，"
                    "合计五十六万五千四百一十六。两团第一遍合计比征召兵日预算少一个原始单位；原版第二遍按兵团存储顺序，"
                    "把这一单位补给仍有软伤的第一团。所以最终征召兵硬伤是七十九万一千五百八十四和五十六万五千四百一十六。"
                    "职业兵士只有一支，最终硬伤九十万四千六百六十六。三项各除十万，才是实际人数当量。"
                ),
                "en": (
                    "Allocate levy A and B by each regiment's share of the 600-person soft pool. "
                    "The first regiment receives 208,250 and 583,333 raw; the second receives 148,750 "
                    "and 416,666. The first pass is one raw unit short, which goes to the earliest eligible "
                    "regiment. Final levy hard losses are 791,584 and 565,416 raw; the sole men-at-arms "
                    "regiment loses 904,666 raw. Divide each by Q for person-equivalents."
                ),
                "visual_lines": [
                    "征召 #1 A/B=208,250/583,333；#2=148,750/416,666",
                    "首遍合计 1,356,999；余 1 raw → 第一个兵团",
                    "最终硬伤 791,584 / 565,416 / 904,666 raw",
                ],
            })
            cues.append(part)
    assert len(cues) == 33 and len({row["id"] for row in cues}) == 33
    (HERE / "script.json").write_text(json.dumps({"format_version": 1, "purpose": "R6.1 full recut with paragraph captions", "game_version": "1.19.0.6", "cues": cues}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "timeline.json").write_text(json.dumps({"format_version": 1, "shots": [
        {"id": row["id"], "title": row["visual_title"]} for row in cues]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
