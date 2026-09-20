#!/usr/bin/env python3
"""Build the sentence-by-sentence human-viewer copy audit for the r13 film."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    ROOT
    / "artifacts/project-causality/2026-09-20-r13/project-causality-r13.build-plan.json"
)
DEFAULT_OUTPUT = ROOT / "docs/project-causality-r13-line-audit.md"
SENTENCE_RE = re.compile(r"[^。！？；]+[。！？；]?|[^。！？；]+$")


# These are diagnoses, not replacement copy.  Unlisted lines passed a literal
# human-viewer read for conversational flow and documentary immersion.
FINDINGS: dict[int, tuple[str, str]] = {
    22: ("轻微不自然", "价值概述里突然出现 runner，口语层级比前后更像施工说明。"),
    30: ("工程腔偏重", "在第一批直观产品展示之前集中出现精确版本、bridge、MCP，理解门槛提前抬高。"),
    40: ("轻微不自然", "“蓄王”对不了解契约原型的观众缺少即时语义。"),
    58: ("工程腔偏重", "独立命名空间与二十七文件白名单是有效证据，但作为口播略像发布清单。"),
    62: ("轻微不自然", "连续念出“三十、六十、十”和三个小数，听感密集，且百分比关系依赖观众自行补全。"),
    65: ("轻微不自然", "“进入同一本组织账”有意象，但政策卡怎样影响考核仍较抽象。"),
    67: ("轻微不自然", "“借镜头提前出生”修辞较用力，短暂让人意识到这是宣传片自证。"),
    75: ("工程腔偏重", "“精确版本的机器投影”是内部实现表达，新观众不易在一次聆听中消化。"),
    87: ("工程腔偏重", "连续罗列不安装、不启动、无 MCP、无任意脚本，像边界审计清单。"),
    91: ("工程腔偏重", "OCR 与鼠标坐标是必要证据说明，但会短暂打断实机展示的戏剧推进。"),
    95: ("明显脱戏", "主动解释本局没有事件、也不会借片段冒充，诚实但防御性很强，观众注意力会从能力转向缺失项。"),
    100: ("工程腔偏重", "军队编号、路线与目标的有效期属于实现论证，放在实机段中稍显抽象。"),
    102: ("明显脱戏", "“影片没有规定”直接暴露导演约束，叙事从智能体决策跳到制作过程。"),
    120: ("工程腔偏重（位置合理）", "哈希与 ABI 很硬，但已进入咒章后半的工程论证区，结构上成立。"),
    121: ("工程腔偏重（位置合理）", "“前端模型”需要技术背景，所处位置允许保留。"),
    122: ("工程腔偏重（位置合理）", "版本绑定的结论清楚，但语域已完全转为工程审计。"),
    123: ("工程腔偏重（位置合理）", "ACK 是准确术语，也会把普通观众挡在门外。"),
    124: ("工程腔偏重（位置合理）", "War ID 与字段枚举适合作为证据深挖，不适合作为价值概述；当前顺序正确。"),
    125: ("轻微不自然", "中文口播中突然落到 target ledger，术语没有中文落脚点。"),
    126: ("工程腔偏重（位置合理）", "OODA 的解释完整，但整句信息密度高。"),
    127: ("明显不自然", "production-live primitive 作为英文状态名直接朗读，像从进度表复制进旁白。"),
    128: ("明显不自然", "production-live loop 延续同一问题；概念准确，但听感不是自然演讲。"),
    133: ("轻微不自然", "“问我敢不敢动”中的“我”指代不清，可能被理解为旁白本人。"),
    161: ("轻微不自然", "一句承担测试、接口、版本、证据和字节五层信息，正常语速下难以一次听懂。"),
    168: ("工程腔偏重（位置合理）", "语义哈希是必要深挖，但没有技术背景的观众只会留下“又一道门禁”的印象。"),
    176: ("明显不自然", "片中此前使用 open-kashek，此处写成 open_kaishek；命名和读法均不一致，且整句术语过密。"),
    179: ("工程腔偏重（位置合理）", "ABI、线程和暂停条件属于 MCP 构建细节，位置符合本章承诺。"),
    186: ("轻微不自然", "“发布必须绑定目标与持久回执”高度压缩，缺少可感知的主语和场景。"),
    194: ("轻微不自然", "“生产家徽网页”不像自然称呼；三种禁用边界并列也带有内部规章口吻。"),
    200: ("轻微不自然", "“失败则留下姓名”意象不够明确，第一反应可能是给失败者点名。"),
    204: ("工程腔偏重（位置合理）", "白名单、暂存目录、确定性压缩包是发行施工语言，证据价值大于口语亲和力。"),
    208: ("工程腔偏重（位置合理）", "连续八个系统名词形成清单感，但它位于术章总结，尚不脱离主题。"),
    216: ("轻微不自然", "RED 以英文状态词突入中文价值段，声音上比“红灯”更像项目周报。"),
    233: ("轻微不自然", "句子很长，五个结果并列后还追加因果条件，口播呼吸与理解负担都偏高。"),
    234: ("工程腔偏重（位置合理）", "“一个提供方”没有现场可见指代，像内部验收条款。"),
    237: ("工程腔偏重（位置合理）", "五级 readiness 状态连续朗读，准确但报告感明显。"),
    239: ("工程腔偏重（位置合理）", "固定种子与长局是内部证据边界，非技术观众需要依赖上下文。"),
    241: ("轻微不自然", "把版本、哈希、接口和决策树统称为“能力”，概念跨度过大。"),
    248: ("明显脱戏", "“宗教通用域暂缓”是内部路线图状态，突然出现在公开宣传价值段，观众既缺背景也难理解其必要性。"),
    268: ("轻微不自然", "一个句子塞入原版研究、观察动作、四阶段闭环和无人时长，听感接近路线图摘要。"),
    270: ("证据边界待复核", "“完整寿命已经画出实线”是很强的能力声明，需要与最终发布时的 live artifact 严格一致。"),
    279: ("工程腔偏重（位置合理）", "构建字节与签核准确但生硬，处于发行循环说明中可以理解。"),
    292: ("轻微不自然", "四个互不相干的镜头和四个动作压在一句里，画面若切换稍慢就会跟不上。"),
    289: ("结构性回跳", "句子本身自然，但在四环和人的结论之后重新从角色死亡起笔，像影片第二次开场。"),
    290: ("结构性回跳", "与前面永恒轮回产品段的表达重复，作用更像回顾而非新推进。"),
    291: ("结构性回跳", "金句成立，但段落位置使观众误判影片是否重新开始。"),
    293: ("结构性回跳", "承接蒙太奇自然，但随后又展开项目总论，形成明显的第二套开场结构。"),
    294: ("结构性回跳", "再次提出“真正的问题”，与冷开场的问题框架重复。"),
    295: ("结构性回跳", "作为总复盘可用，但此处听感更像重新立题。"),
    296: ("结构性回跳", "价值判断没有问题，问题在于它启动了已讲过的体系定义。"),
    297: ("结构性回跳", "再次宣告结果被因果链连接，和 01:49 的总论功能重叠。"),
    298: ("结构性回跳", "排除式定义自然，但放在 47 分钟处仍像正式开题。"),
    299: ("结构性回跳", "“共享同一套记忆”适合前段立论，作为尾声回顾需更明确的回望语气。"),
    300: ("结构性回跳", "句子自然，功能却仍在解释系统基本构成。"),
    301: ("结构性回跳", "再次列出文档、生成、测试、实机、证据与发行，和术章总结高度重合。"),
    302: ("结构性回跳", "“真正要造的”是开题语式，不像已经完成四章后的收束语式。"),
    303: ("结构性回跳", "价值表达准确，但重复 01:49 与四环总论的核心命题。"),
    304: ("明显脱戏", "“沿着这条因果链向里走，会经过四层”在四层已经全部讲完后才出现，时间方向错误。"),
    305: ("结构性回跳", "重新介绍最外层结果，内容与咒章已完整覆盖。"),
    306: ("结构性回跳", "重新介绍术的范围，内容与术章已完整覆盖。"),
    307: ("结构性回跳", "重新预告道的尺度，但道章此时已经结束。"),
    308: ("轻微不自然", "“最深的图景还没有完成”可作愿景边界，但它紧接一次迟到的四层导览。"),
    309: ("明显脱戏", "“先把桌上的结果一件件摆出来”出现在所有结果已经摆完之后，叙事时态与位置冲突。"),
}


def stamp(seconds: float) -> str:
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def section(index: int) -> str:
    if index <= 4:
        return "抓人开场"
    if index <= 10:
        return "总价值与双入口"
    if index <= 47:
        return "咒"
    if index <= 74:
        return "术"
    if index <= 90:
        return "道"
    return "辉煌愿景"


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    rows: list[dict[str, object]] = []
    number = 0
    for cue in payload["cues"]:
        cue_text = "".join(
            block["text"].replace("\n", "") for block in cue["subtitle_blocks"]
        )
        sentences = [
            match.group(0).strip()
            for match in SENTENCE_RE.finditer(cue_text)
            if match.group(0).strip()
        ]
        for sentence in sentences:
            number += 1
            verdict, note = FINDINGS.get(
                number, ("通过", "口语连贯，未见明显脱戏或不自然。")
            )
            rows.append(
                {
                    "number": number,
                    "cue_index": int(cue["index"]),
                    "cue_id": cue["id"],
                    "time": stamp(float(cue["start_seconds"])),
                    "text": sentence,
                    "verdict": verdict,
                    "note": note,
                }
            )

    if number != 328:
        raise RuntimeError(f"expected 328 spoken units, got {number}")
    unknown = sorted(set(FINDINGS) - {int(row["number"]) for row in rows})
    if unknown:
        raise RuntimeError(f"findings reference missing lines: {unknown}")

    counts = Counter(str(row["verdict"]) for row in rows)
    flagged = number - counts["通过"]
    lines = [
        "# 《Project 因果律：伪天司的辉煌愿景》r13 逐句文案审计",
        "",
        "> 状态：仅审计，不改稿。审计对象为 r13 最终构建计划中的全部中文朗读文案；分号分隔的独立语义单元也单独计数，避免漏审。",
        "",
        "## 结论",
        "",
        f"共审计 **{number} 个朗读语义句**。其中 **{counts['通过']} 句通过**，**{flagged} 句需要人工复审**。",
        "",
        "从普通观众视角看，新增冷开场是有效的：前 100 秒先抛出维护成本、无人验收与自动玩家三组价值，没有再用标题、副标题或制作说明占据第一注意力。主要问题集中在四处：",
        "",
        "- 14–22 分钟的罗贝尔实机与工程深挖之间，个别防御性说明会让观众从“智能体在做什么”跳到“制作方为什么这样剪”。",
        "- 21–39 分钟有若干英文 readiness/工程术语直接进入中文口播；它们按要求被放在价值展示之后，结构正确，但少数句子仍像日报或接口文档。",
        "- 40:20 的“宗教通用域暂缓”属于内部路线图信息，公开宣传语境里最明显地脱戏。",
        "- 46:15–49:39 在四环论证完成后又重新执行一次“结果提问—项目定义—四层导览”，形成第二次开场；尤其“沿着这条因果链向里走”和“先把结果摆出来”与此时的时间位置冲突。",
        "",
        "审计标签不是删改指令。“工程腔偏重（位置合理）”表示内容值得保留，只是需要人工判断声音、画面和节奏能否托住；本报告不提供替换文案，也没有修改成片旁白。",
        "",
        "## 标签统计",
        "",
        "| 标签 | 数量 |",
        "|---|---:|",
    ]
    order = [
        "通过",
        "轻微不自然",
        "工程腔偏重",
        "工程腔偏重（位置合理）",
        "明显不自然",
        "明显脱戏",
        "结构性回跳",
        "证据边界待复核",
    ]
    for label in order:
        lines.append(f"| {label} | {counts[label]} |")

    current = ""
    for row in rows:
        heading = section(int(row["cue_index"]))
        if heading != current:
            current = heading
            lines.extend(
                [
                    "",
                    f"## {heading}",
                    "",
                    "| # | 时间 | Cue | 原文 | 判断 | 观众感受 |",
                    "|---:|:---:|---|---|---|---|",
                ]
            )
        lines.append(
            f"| {row['number']} | {row['time']} | `{row['cue_id']}` | "
            f"{escape(str(row['text']))} | {row['verdict']} | {escape(str(row['note']))} |"
        )

    lines.extend(
        [
            "",
            "## 非朗读画面文案抽检",
            "",
            "- 章节门“咒 / 术 / 道 / 辉煌愿景”只作主题声明，没有把 Why / What / How 等阶段名印到画面上：通过。",
            "- 结尾 Steam 创意工坊卡现列出 9 项已发布 Mod，包含《牛来》及 ID `3790635143`：通过。",
            "- 结尾卡的仓库地址、双入口价值句与最终余烬句层级清楚：通过。",
            "- 工程深挖中的英文术语仍是最明显的语域断层；它们不是画面排版错误，而是朗读文案问题，已逐句标出。",
            "",
            "## 人工复审优先级",
            "",
            "1. 先看 46:15–49:39 是否确实产生“影片重新开场”的体感。",
            "2. 再看 15:24 与 17:25 的防御性制作说明是否打断罗贝尔秀肌肉。",
            "3. 最后判断 production-live、target ledger、readiness 等原词是否必须保留原语言。",
            "4. 核对“完整寿命已经画出实线”的最终证据等级；这是唯一被单列为能力声明风险的句子。",
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"AUDIT: {args.output} | {number} units | {flagged} flagged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
