"""Check that the R6.2 spoken and visible labels match the frozen TTS input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(script_path: Path, inputs_path: Path) -> dict:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    written = script["cues"]
    spoken = inputs["cues"]
    assert len(written) == len(spoken) == 33
    assert [row["id"] for row in written] == [row["id"] for row in spoken]
    for row, frozen in zip(written, spoken, strict=True):
        for key in ("zh", "en", "visual_title", "source_label", "ui_bridge", "visual_lines"):
            if row.get(key) != frozen.get(key):
                raise AssertionError(f"{row['id']}: TTS/visual input differs at {key}")
        if row["visual_kind"] == "card" and not row.get("ui_bridge"):
            raise AssertionError(f"{row['id']}: missing player-facing UI bridge")
        if row["visual_kind"] == "card" and not row.get("source_label"):
            raise AssertionError(f"{row['id']}: missing explicit source/case label")
    cards = {row["id"]: row for row in written if row["visual_kind"] == "card"}
    assert len(cards) == 31
    by_id = {row["id"]: row for row in written}
    source_scope = {
        "E1-F02": "战前预测", "E1-F04": "R0217",
        **{cue_id: "R0217" for cue_id in ("M03", "M04", "M05", "M06", "M07", "M08")},
        **{cue_id: "墨西拿" for cue_id in ("E1-F05", "E1-F06", "E1-F09", "C01", "C02", "C03", "C04", "C05")},
        "C06": "静态", "C07": "公式敏感度", "C08": "阶段事件",
        "C09": "第 26 日", "E1-F19": "另一份",
        **{cue_id: "静态" for cue_id in ("C10", "P01", "P02", "P03", "C11")},
        "E1-F20": "R0220", "E1-F23": "能力边界",
        "E1-F24": "观战方法", "E1-F25": "本集总结",
    }
    for cue_id, term in source_scope.items():
        if term not in cards[cue_id]["source_label"]:
            raise AssertionError(f"{cue_id}: source label missing {term}")
    required = {
        "E1-F02": ("你可能会获胜",),
        "E1-F04": ("尼基弗鲁斯", "罗贝尔", "side"),
        "M02": ("士兵", "军团", "十万"),
        "M03": ("战线宽度", "罗贝尔", "尼基弗鲁斯"),
        "M04": ("优势", "伤害", "内部聚合量"),
        "E1-F05": ("征召兵", "长枪兵", "图尔吉塞"),
        "E1-F09": ("调动", "主要阶段", "追击"),
        "C01": ("士兵", "入伤"),
        "C02": ("罗贝尔", "征召兵"),
        "C03": ("罗贝尔", "长枪兵"),
        "C04": ("骑士图尔吉塞", "兵士条目容器", "不是长枪兵"),
        "C05": ("溃逃士兵", "战死士兵"),
        "C06": ("界面看不到", "存储顺序"),
        "C07": ("长枪兵", "坚韧"),
        "C08": ("骑士", "界面", "权重"),
        "C09": ("图尔吉塞", "阿姆鲁", "塔米姆", "死亡", "六十五号"),
        "E1-F19": ("拉马丹", "阿什拉夫", "勇武"),
        "C10": ("追击", "溃逃士兵", "战死士兵"),
        "P01": ("静态示例", "没有墨西拿", "追击", "掩护"),
        "P02": ("教学代号", "游戏界面没有"),
        "P03": ("静态公式示例", "不是罗贝尔军"),
        "E1-F20": ("R 零二二零", "没有可靠证据", "人物名"),
    }
    for cue_id, terms in required.items():
        value = by_id[cue_id]["zh"]
        for term in terms:
            if term not in value:
                raise AssertionError(f"{cue_id}: missing {term}")
    full = json.dumps(script, ensure_ascii=False)
    for invalid in ("英勇", "六十五号职业兵士", "65号职业兵士"):
        if invalid in full:
            raise AssertionError(f"Legacy or incorrect player-facing term: {invalid}")
    if "骑士图尔吉塞 #65" not in cards["C04"]["source_label"]:
        raise AssertionError("C04 card must identify the knight")
    if "罗贝尔长枪兵 #51" not in cards["C03"]["source_label"]:
        raise AssertionError("C03 card must identify the unit type")
    return {
        "schema": "ck3-war-ai-r62-context-audit.v1",
        "state": "GREEN",
        "cue_count": len(written),
        "ui_bridged_cards": len(cards),
        "source_scope_checks": len(source_scope),
        "spoken_visual_identity_checks": len(required),
        "input_matches_script": True,
        "case_boundaries": ["R0217", "Messina", "static-pursuit-vector", "R0220"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.script, args.inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
