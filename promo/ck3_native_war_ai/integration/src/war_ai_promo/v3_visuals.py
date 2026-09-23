"""Evidence-scoped stills for the V3 CK3 war documentary.

This module draws paper diagrams and labels a separately supplied, hash-bound
original CK3 frame as *context*. It never derives a decision from screenshot
pixels. Unknown and unbound cues fail before an image is written.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Mapping

from PIL import Image, ImageDraw

from .common import font


SIZE = (2560, 1440)
SUBTITLE_TOP = 1120
INK = "#F2E6CC"
MUTED = "#C9B899"
GOLD = "#D7AF69"
DARK = "#211912"
PAPER = "#D6BD8F"
PAPER_INK = "#3A2B20"
RED = "#9E5848"
GREEN = "#62744C"

ALLOWED_STATES = {"exact-live-case", "verified-static", "illustrative-rule-scenario"}
CASE_FRAME_CUES = {
    "V3-01": "CASE-R", "V3-03": "CASE-R", "V3-05": "CASE-W",
    "V3-06": "CASE-R", "V3-44": "CASE-R", "V3-45": "CASE-W",
    "V3-02": "CASE-R", "V3-16": "CASE-W", "V3-17": "CASE-W",
    "V3-22": "CASE-W", "V3-23": "CASE-W", "V3-43": "CASE-W",
}
CASE_CONTEXT_LABELS = {
    "CASE-R": "CASE-R · 同一暂停现场的地图；评估值随后单独查询",
    "CASE-W": "CASE-W · 原版行军现场；卡片数值来自独立原生读回",
}


@dataclass(frozen=True)
class Copy:
    title: str
    kicker: str
    hero: str
    points: tuple[str, str, str]
    limit: str


# The words below are editorial annotations of the cited native rules and
# case readbacks. Unbound cues are intentionally absent from this table.
COPY: dict[str, Copy] = {
    "V3-02": Copy("沿着战争读原生 AI", "章节导览 · 实机与规则分开", "宣战 → 行军 → 接战 → 战分 → 和平", ("CASE-R：原生读回，非自然宣战", "CASE-W：敌军行军观察，非因果闭环", "战斗与和平：已核对原生规则图解"), "背景是 CASE-R 地图；五个阶段不是同一场战争的完整实机录像。"),
    "V3-01": Copy("罗贝尔的两张战争比较卡", "实机读回 · CASE-R", "2.83095  /  0.35235", ("目标 31899 → 有效防守方 37169", "目标 31549 → 有效防守方 31549", "相同比较者：战略军力 37860"), "两个比值是目标军力／自身军力，不是胜率；原录像早于查询。"),
    "V3-03": Copy("合法宣战，与 AI 最终选择", "实机读回 + 原生规则", "9 条当前合法宣战行", ("罗贝尔暂停现场：9 行，7 个原始目标", "合法性只回答此刻能否声明", "准备、评分和选择仍在后续阶段"), "这不是 AI 自然宣战，也不是 9 个已评分的 AI 候选。"),
    "V3-04": Copy("准备金和具体宣战成本", "已核对原生规则", "先有资源门，再有候选门", ("战争准备金要按规则保留", "战争理由和交互还各有成本", "地图上的金币数不能代替完整预算读回"), "本片没有采到罗贝尔的完整 AI 战争预算。"),
    "V3-05": Copy("士兵数与战略军力是两把尺", "实机读回 · CASE-W", "U22：2570 人  /  73640 军力", ("同一观测帧的军队 U22", "2570 是人数；73640 是原生力量估值", "不能把力量值写成参战人数"), "这一个对照不推出完整兵种权重，也不表示获胜概率。"),
    "V3-06": Copy("原目标可以指向另一位防守方", "实机读回 · CASE-R", "31899 → 37169", ("A：有效防守方 37169\n战略军力 107180；比值 2.83095", "B：有效防守方 31549\n战略军力 13340；比值 0.35235", "两次查询的自身战略军力均为 37860"), "R0004 的同暂停读回；不混入 R0005 的数值，也不推断重定向原因。"),
    "V3-07": Copy("潜在参战关系要经过门槛", "已核对原生规则", "关系 ≠ 已到场援军", ("先从原生关系来源取候选", "再检查 potential-call 条件", "CASE-R 两个估值的网络增量都为 0"), "增量为零不能证明没有盟友、已拒绝参战或没有后续援军。"),
    "V3-08": Copy("同一军力比，遇到两种门槛", "规则算例 · 非实机数值", "1.2  对照  1.0 / 1.5", ("假设其他修正均为 0", "和平目标门槛 1.0：1.2 可通过这一项", "已交战目标门槛 1.5：1.2 不通过这一项"), "只示范该军力门；不代表 CASE-R 的实际判定或最终宣战。"),
    "V3-09": Copy("评分之后，先决定候选池", "规则算例 · 非实机评分", "100 · 97 · 94 · 91 · 90 · 89", ("最高分 100 的九成是 90", "89 被筛掉；90 恰在边界，留下", "本例保留五项，恰好不用再截前五"), "六张分数卡不是 CASE-R 的九条合法宣战行。"),
    "V3-10": Copy("第一名，也只是抽取池的一项", "规则算例 · 条件概率", "94 / 472  ≈  19.9%", ("保留权重：100、97、94、91、90", "权重合计 472；94 占约 19.9%", "这只是在给定候选池内被抽中的份额"), "这不是总体宣战概率，更不是战争获胜概率。"),
    "V3-11": Copy("军团目标按军队与省份配对", "已核对原生规则", "军队 × 省份", ("先取得当前可用军队与目标省份", "当前目标块形成候选配对", "候选还要经过后续评价与分配"), "CASE-W 行军只说明位置变化，未读到每个候选配对分数。"),
    "V3-12": Copy("同一省份的重复候选怎样处理", "规则算例 · 非实机评分", "80 与 60  →  基础优先级 80", ("两条入口指向同一省份", "基础优先级取替换后的较高值", "不把 80 与 60 相加成 140"), "80/60 为教学数字，后续修正另算。"),
    "V3-13": Copy("较早目标块，不必包办全部军团", "规则算例 · 非实机分配", "未分配军团 → 继续下一块", ("先检查顺序靠前的目标块", "能覆盖的军团进入当前候选", "仍未分配的军团可到后续目标块"), "示意的是遍历结构，不是全局目标优先级表。"),
    "V3-14": Copy("排序后的配对还要逐个分配", "规则算例 · 非实机评分", "A/城堡 90 · B/城堡 85 · B/其他 80", ("先取 A/城堡 90", "该省份已被占用，B/城堡 85 不再取", "B/其他 80 仍可给 B"), "占用标记属于这次分配轮次，不等于省份永久归属。"),
    "V3-15": Copy("分数靠前，仍要过后续条件", "已核对原生规则", "排序 → 限量检查 → 路径门", ("初步分数决定检查次序", "部分候选还要经过路线及其他条件", "先排第一不保证最后落到行动"), "CASE-W 未记录被拒的精确候选，不能由改道反推。"),
    "V3-16": Copy("军团什么时候重算目标", "已核对原生规则 · CASE-W 地图语境", "计数器 · 提前请求 · 暂缓", ("先确认目标重算发生", "再比较候选与实际分配", "最后读回目标写入和行动"), "CASE-W 只观察到路线字段变化，没有读到重算触发或候选分数。"),
    "V3-17": Copy("目的地是分配，行军是动作", "已核对原生规则 · CASE-W 地图语境", "候选 → 分配 → 写回 → 行动", ("省份与军团配对后排序", "占用、已有安排、路径条件继续筛选", "CASE-W 只证明 U22 的路线到位置进展"), "不能将 CASE-W 的位移反推为完整目标分配因果链。"),
    "V3-18": Copy("接战比较用局部力量比", "规则算例 · 非实机输入", "自身 /（自身 + 敌方）", ("100 / (100 + 100) = 0.50", "200 / (200 + 100) ≈ 0.667", "此量属于局部接近判断"), "与 CASE-R 的战略 ratio、战斗预测概率各有不同口径。"),
    "V3-19": Copy("敌方力量也要按关系聚合", "已核对原生规则", "主要敌对组 + 适用折算组", ("原生按关系与情境确定敌对组", "部分组别按规则折算后相加", "结果才送入局部力量比较"), "不能用画面旗帜旁的士兵数直接填这个力量值。"),
    "V3-20": Copy("两个接近门都是严格大于", "规则算例 · 非实机输入", "一般 > 0.5  /  desperate > 0.4", ("0.50 不通过一般分支的严格门", "0.45 可通过 desperate 门", "何时进入 desperate 另由上游规则决定"), "算例不证明实际军团选中了哪种模式或一定会接战。"),
    "V3-21": Copy("desperate 不是输着打的俗称", "已核对原生规则", "先读上游 mode 条件", ("角色类型和战争攻守身份有关", "还要看自身战分等输入", "满足对应分支才进入低门槛模式"), "没有实机 active mode 读回时，不能只看兵力劣势来命名。"),
    "V3-22": Copy("局部不利邻接与替代路线", "已核对原生规则 · CASE-W 地图语境", "预测值 < 0.625 → 尝试替代路", ("门针对目标前的不利邻接", "替代路还要过额外成本约束", "找不到替代路才回看原路接战门"), "地图是 CASE-W 战区背景；U22 改道原因未被证明。"),
    "V3-23": Copy("接近前，先看哪一道门", "已核对原生规则 · CASE-W 地图语境", "目标 · 局部力量 · mode · 路线", ("先核对当前军团目标", "再核对局部力量和接近 mode", "最后对照路线与实际动作"), "CASE-W 未取得同军团完整门槛链；主动撤退是另一决策。"),
    "V3-24": Copy("求援有上一刻的状态", "规则算例 · 普通 AI 援军", "开始 < 0.66  /  继续 < 0.75", ("尚未请求时按开始门判断", "已经请求时按维持门判断", "同一比值可因历史状态得到不同结果"), "CASE-W 的 U22 仅一次读到 asking=false，没有门槛穿越链。"),
    "V3-25": Copy("0.70 需要先问：原来求援了吗", "规则算例 · 非实机时间线", "0.65 → 0.70 → 0.76", ("0.65 时触发开始请求的条件", "已有请求时，0.70 可继续维持", "0.76 越过维持界；从未请求的 0.70 也不会开始"), "三个数值是规则演示，不是 CASE-W 的日期读回。"),
    "V3-26": Copy("能求援，先看真实军团结构", "已核对原生规则", "parent stack 的子单位数 > 1", ("普通生产端检查母军团结构", "单一子单位情形不能直接套入", "CASE-W U22：parent stack 3，subunit 0"), "U22 结构 ready 不等于确实发出了请求。"),
    "V3-27": Copy("援军能否补足，比较的是力量", "规则算例 · 非实机军力", "需求 150：149 / 150 / 151", ("可用力量 149：不足 150", "可用力量 150：到达等号边界", "可用力量 151：超过门槛"), "力量单位不是士兵人数；算例不指认 CASE-W 的援军。"),
    "V3-28": Copy("求援是四步，不是一个镜头", "已核对原生规则", "请求 → 指派 → 路线 → 到场", ("请求状态由生产端更新", "另一组单位匹配后才获得支援任务", "实际到场要绑定同一 CombatID"), "CASE-W 无请求链；CASE-C 无接战样本，图中四步不是实机复盘。"),
    "V3-29": Copy("普通求援与支援玩家分开读", "已核对原生规则", "起请求 · 维持 · 指派 · 到场", ("普通 AI 之间先看带历史的求援门", "支援玩家有另外的路径与限制", "候选、指派和真正到场还要逐环查证"), "CASE-W 没有取得请求→指派→同一战斗到场的连续链。"),
    "V3-30": Copy("一场战斗如何进入战争账本", "已核对原生规则 · 非 CASE-C 战果", "本场硬损失 ÷ 败方参战者数量", ("分子仅取本场败方硬损失", "分母来自败方整场战争的参战者", "再应用战争理由倍率与单场上限"), "CASE-C 没有 CombatID 或终局；此处不展示真实战果。"),
    "V3-31": Copy("战分分母由八类数量组成", "已核对原生规则", "数量口径 ≠ 战略军力估值", ("征召兵、兵士按相应最大数量口径", "特殊部队、骑士、游牧骑手等另有规则", "汇总的是战争参战者的数量项"), "没有逐桶实机读回时，不填某场战斗的真实分母。"),
    "V3-32": Copy("同样硬损失，战争规模不同", "规则算例 · 倍率假定为 50", "1000/10000×50=5  ·  1000/20000×50=2.5", ("两例本场硬损失均假设为 1000", "败方战争参战者数量分别为 10000 / 20000", "结果只是单场贡献算例"), "倍率 50 不是 CASE-C 已测战争理由，也不是面板总战分。"),
    "V3-33": Copy("战争分有三层账", "已核对原生规则 · 非 CASE-C 战果", "单场 → 累计战斗 → 总战争分", ("单场记录先按攻守身份汇总", "累计战斗项受这场战争的上限限制", "总分另受占领、目标控制和囚禁影响"), "没有同 War 的实测变化，不能把总分变化归因于某场战斗。"),
    "V3-34": Copy("解释战分要沿三层账核对", "已核对原生规则", "单场 → 累计战斗 → 总战争分", ("先核对硬损失与败方参战者分母", "再看当前战争理由的倍率和单场上限", "最后区分累计战斗与其他总分来源"), "CASE-C 没有战斗终局；这里不呈现真实战果。"),
    "V3-35": Copy("白和有两张不同的账", "已核对原生规则", "主动提出：基础 0  /  接受：基础 −30", ("提出者判断现在是否值得发送", "收件人判断是否接受已给条件", "两侧还有各自适用的局势修正"), "没有自然 AI 白和提议的实机案例；数值不能替代实际结果。"),
    "V3-36": Copy("接受分：方向与严格边界", "规则算例 · 防守方收件人", "−30+20=−10  ·  −30+30=0  ·  −30+31=1", ("假设其他适用修正全部为 0", "加的是对手进攻方战分 20 / 30 / 31", "普通路径要求原始结果严格大于 0"), "30 不是通用白和阈值；显示取整与其他修正另行核对。"),
    "V3-37": Copy("零分还没有过接受门", "已核对原生规则", "普通合法 AI 收件人：raw > 0", ("战争分只是输入之一", "时长、债务、其他防御战争等会改变结果", "还要按角色检查合法性和特殊条件"), "不能用 UI 显示的 0 直接断言原始值恰好等于 0。"),
    "V3-38": Copy("主动求和有自己的动机", "已核对原生规则", "提出者侧单独计算", ("时长、战分、债务与其他战争参与计算", "进攻方和防守方分支不完全对称", "一些条件增加动机，也有归零分支"), "没有提出者的同期输入时，不能把某一次求和归因于债务。"),
    "V3-39": Copy("有动机后，还要等机会和竞争", "规则算例 · 非实机随机值", "40−60=−20  /  40−10=30", ("当前最佳值从 0 开始", "−20 不替换 0；30 可以成为候选", "最后仍需检查交互是否可发送"), "两次随机数都是演示输入，不是已采样的自然白和结果。"),
    "V3-40": Copy("向玩家提白和还有额外限制", "已核对原生规则", "玩家攻 / AI 守 / 攻方战分 ≥ 10", ("这个身份组合触发主动提议预筛", "相应候选被排除", "接受玩家提议仍须按收件人路径另算"), "只覆盖这个已证角色分支，不能概括所有攻守组合。"),
    "V3-41": Copy("发送之后，怎样确认和平结果", "已核对原生规则与核验顺序", "提出 → 发送 → 答复 → 战争终局", ("先读提出者和提议条件", "再读收件人的接受或拒绝", "最后读战争状态与实际后果"), "CASE-W/C 没有自然和平提案；这张卡是核验方法而非实机结局。"),
    "V3-42": Copy("两张账在交互结果处相遇", "已核对原生规则", "提出者 → 发送  /  收件人 → 应答", ("主动倾向与机会竞争先产生候选", "收件人用接受规则检查条件", "发送、答复与战争结局须分别回读"), "此图不宣称已取得自然谈判终局。"),
    "V3-43": Copy("三个阶段，三套尺度", "规则总结 · 案例分开署名", "资格与军力 · 局部力量 · 战分与和平", ("CASE-R：宣战评估原生读回", "CASE-W：玩家宣战后敌军行军", "战斗与和平：来源核对的规则图解"), "CASE-R/W/C 不是从 AI 自然宣战到自然停战的同一完整实机案例。"),
    "V3-44": Copy("两张卡回答了什么，又没回答什么", "实机读回 · CASE-R", "2.83095  /  0.35235", ("31899 → 37169；目标军力 107180", "31549 → 31549；目标军力 13340", "同一暂停现场的自身军力均为 37860"), "是原生估值的两个结果，不是最终 AI 选择或自然宣战。"),
    "V3-45": Copy("重新看懂一场战争的观察顺序", "版本与来源 · CK3 1.19.0.6", "对象 → 阶段 → 量纲 → 条件", ("先确认哪个人、哪场战争、哪个军团", "再区分战略军力、局部力量、战分与和平分", "完整规则与证据索引见 docs/ck3-native-ai"), "地图为 CASE-W 原始抽帧背景；不表示全部战争树或影片已经签核。"),
}


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _load_cue(ledger_path: Path, cue_id: str, shot_id: str) -> dict:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    if ledger.get("schema") != "ck3-war-ai.v3-evidence-visual-ledger.v1":
        raise ValueError("Expected the reviewed V3 evidence ledger schema")
    cues = ledger.get("cues")
    if not isinstance(cues, list) or len(cues) != 45 or len({r.get("id") for r in cues}) != 45:
        raise ValueError("The V3 ledger must contain 45 unique cues")
    matches = [r for r in cues if r.get("id") == cue_id]
    if len(matches) != 1:
        raise ValueError(f"Unknown V3 cue: {cue_id}")
    cue = matches[0]
    if cue.get("shot_id") != shot_id:
        raise ValueError(f"V3 cue/shot binding differs: {cue_id}")
    if cue.get("state") == "unbound":
        raise ValueError(f"V3 cue still needs a causal shot or revised scope: {cue_id}")
    if cue_id not in COPY:
        raise ValueError(f"V3 cue has no authored scene: {cue_id}")
    if cue.get("state") not in ALLOWED_STATES or not cue.get("spoken_source_links"):
        raise ValueError(f"V3 evidence binding is incomplete: {cue_id}")
    root = Path(__file__).resolve().parents[5]
    for source in cue["spoken_source_links"]:
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"V3 cited source is unavailable: {source['path']}")
    for case_id in cue.get("case_refs", []):
        document = ledger.get("case_documents", {}).get(case_id)
        if not document:
            continue
        path = (root / document["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file() or _sha256(path) != document["sha256"]:
            raise ValueError(f"V3 cited case document changed: {case_id}")
    if cue_id in CASE_FRAME_CUES and CASE_FRAME_CUES[cue_id] not in cue.get("case_refs", []):
        raise ValueError(f"V3 live case does not match its frame case: {cue_id}")
    return cue


def _frame_asset(case_id: str, assets: Mapping[str, dict]) -> tuple[Image.Image, dict]:
    binding = assets.get(case_id)
    if not isinstance(binding, dict):
        raise ValueError(f"A reviewed original frame binding is required for {case_id}")
    if binding.get("case_id") != case_id or binding.get("evidence_role") != "context-only-original-frame":
        raise ValueError(f"Original frame role/case mismatch: {case_id}")
    path = Path(binding["path"])
    if not path.is_file() or path.suffix.lower() != ".png":
        raise ValueError(f"Original frame is missing or not PNG: {path}")
    if _sha256(path) != binding.get("sha256"):
        raise ValueError(f"Original frame changed after review: {case_id}")
    with Image.open(path) as source:
        if source.size != SIZE:
            raise ValueError(f"Original CK3 frame has unexpected dimensions: {case_id}")
        return source.convert("RGB"), dict(binding)


def _fit_text(draw: ImageDraw.ImageDraw, bounds, value: str, *, size: int, color: str,
              bold: bool = False, min_size: int = 20):
    x, y, right, bottom = bounds
    width, height = right - x, bottom - y
    for candidate in range(size, min_size - 1, -1):
        face = font(candidate, bold)
        rows = []
        for paragraph in value.split("\n"):
            if not paragraph:
                rows.append("")
                continue
            current = ""
            for ch in paragraph:
                if current and draw.textlength(current + ch, font=face) > width:
                    rows.append(current)
                    current = ch
                else:
                    current += ch
            rows.append(current)
        step = int(candidate * 1.34)
        if len(rows) * step <= height and all(draw.textlength(line, font=face) <= width for line in rows):
            for index, line in enumerate(rows):
                draw.text((x, y + index * step), line, font=face, fill=color)
            return candidate
    raise ValueError(f"V3 visual text does not fit: {value!r}")


def _folio_canvas() -> Image.Image:
    image = Image.new("RGB", SIZE, DARK)
    draw = ImageDraw.Draw(image)
    rng = random.Random(119006)
    for _ in range(8000):
        x, y = rng.randrange(SIZE[0]), rng.randrange(SUBTITLE_TOP)
        draw.point((x, y), fill=(43 + rng.randrange(8), 32 + rng.randrange(6), 24 + rng.randrange(5)))
    draw.rectangle((50, 42, 2510, 1116), outline=GOLD, width=3)
    draw.line((78, 120, 2482, 120), fill="#695039", width=2)
    draw.line((80, 1116, 2480, 1116), fill="#695039", width=2)
    for x in (100, 2460):
        draw.ellipse((x - 17, 68, x + 17, 102), outline=GOLD, width=3)
        draw.line((x, 60, x, 110), fill=GOLD, width=2)
    return image


def _header(draw, cue_id: str, copy: Copy, state: str):
    _fit_text(draw, (112, 142, 1900, 232), copy.title, size=69, color=INK, bold=True)
    _fit_text(draw, (1940, 156, 2435, 220), cue_id, size=38, color=GOLD, bold=True)
    tag = {"exact-live-case": "原生实机读回", "verified-static": "原生规则图解",
           "illustrative-rule-scenario": "明确标注的规则算例"}[state]
    _fit_text(draw, (120, 241, 1000, 307), f"{tag}  ·  {copy.kicker}", size=34, color=GOLD)


def _steps(draw, copy: Copy, *, phase: int, area=(105, 548, 2455, 940)):
    x0, y0, x1, y1 = area
    gap = 25
    cell_width = (x1 - x0 - 2 * gap) / 3
    for i, item in enumerate(copy.points):
        left = int(x0 + i * (cell_width + gap))
        right = int(left + cell_width)
        active = i == phase
        draw.rounded_rectangle((left, y0, right, y1), radius=5,
                               fill="#D8C091" if active else "#BEA77E",
                               outline=GOLD if active else "#8D7453", width=4 if active else 2)
        draw.text((left + 32, y0 + 23), f"0{i + 1}", font=font(38, True), fill=RED)
        _fit_text(draw, (left + 33, y0 + 95, right - 32, y1 - 30), item,
                  size=45, color=PAPER_INK, bold=active)


def _source_footer(draw, cue: dict, copy: Copy):
    source_names = [Path(s["path"]).name for s in cue["spoken_source_links"]]
    refs = " · ".join(source_names[:3])
    if len(source_names) > 3:
        refs += f" · +{len(source_names) - 3} 项"
    _fit_text(draw, (114, 970, 2435, 1015), f"依据：{refs}", size=25, color=GOLD, min_size=20)
    _fit_text(draw, (114, 1021, 2435, 1065), f"边界：{copy.limit}", size=26, color=MUTED, min_size=20)


def _draw_live(image: Image.Image, cue: dict, copy: Copy, phase: int,
               frame: Image.Image, case_id: str):
    draw = ImageDraw.Draw(image)
    frame = frame.resize((1500, 844), Image.Resampling.LANCZOS)
    image.paste(frame, (95, 197))
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 192, 1600, 1046), outline=GOLD, width=5)
    draw.rectangle((95, 957, 1595, 1041), fill="#211912")
    _fit_text(draw, (119, 973, 1555, 1027), CASE_CONTEXT_LABELS[case_id], size=28, color=INK)
    draw.rounded_rectangle((1633, 196, 2458, 949), radius=5, fill=PAPER, outline=GOLD, width=4)
    _fit_text(draw, (1671, 231, 2415, 298), f"{cue['id']}  ·  {copy.kicker}", size=34, color=RED, bold=True)
    _fit_text(draw, (1671, 325, 2413, 439), copy.title, size=49, color=PAPER_INK, bold=True)
    _fit_text(draw, (1671, 463, 2413, 556), copy.hero, size=44, color=RED, bold=True)
    for i, point in enumerate(copy.points):
        top = 590 + i * 103
        draw.ellipse((1672, top + 5, 1698, top + 31), fill=RED if i == phase else GREEN)
        _fit_text(draw, (1720, top, 2410, top + 87), point,
                  size=34, color=PAPER_INK, bold=i == phase, min_size=23)
    source_names = " · ".join(Path(s["path"]).name for s in cue["spoken_source_links"][:2])
    _fit_text(draw, (113, 1048, 2430, 1080), f"依据：{source_names}", size=23, color=GOLD)
    _fit_text(draw, (113, 1081, 2430, 1113), f"边界：{copy.limit}", size=22, color=MUTED)


def _draw_paper(image: Image.Image, cue: dict, copy: Copy, phase: int):
    draw = ImageDraw.Draw(image)
    _header(draw, cue["id"], copy, cue["state"])
    draw.rounded_rectangle((105, 322, 2455, 520), radius=5, fill=PAPER, outline=GOLD, width=4)
    _fit_text(draw, (153, 366, 2405, 492), copy.hero, size=68, color=PAPER_INK, bold=True)
    _steps(draw, copy, phase=phase)
    _source_footer(draw, cue, copy)


def make_v3_frame(row: dict, destination: str | Path, phase: int, *,
                  ledger_path: str | Path, assets: Mapping[str, dict] | None = None) -> dict:
    """Create one 2560×1440 authored V3 still; return its exact input receipt.

    `assets` maps CASE-R/CASE-W to explicit original PNG bindings with `path`,
    `sha256`, `case_id`, and `evidence_role=context-only-original-frame`.
    Background frames are never substituted for evidence of a live AI decision.
    `phase` selects which of three paper annotations is emphasized.
    """
    if not isinstance(row, dict) or phase not in (0, 1, 2):
        raise ValueError("V3 frame needs a cue row and phase 0, 1, or 2")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    ledger_path = Path(ledger_path)
    cue_id = row.get("id")
    cue = _load_cue(ledger_path, cue_id, row.get("shot_id"))
    if cue_id not in COPY:
        raise ValueError(f"No authored V3 layout for {cue_id}")
    copy = COPY[cue_id]
    case_id = CASE_FRAME_CUES.get(cue_id)
    frame = binding = None
    if case_id:
        frame, binding = _frame_asset(case_id, assets or {})
    image = _folio_canvas()
    if frame is not None:
        _draw_live(image, cue, copy, phase, frame, case_id)
    else:
        _draw_paper(image, cue, copy, phase)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return {
        "schema": "ck3-war-ai.v3-visual-frame.v1",
        "cue_id": cue_id,
        "shot_id": cue["shot_id"],
        "phase": phase,
        "state": cue["state"],
        "source_links": [r["path"] for r in cue["spoken_source_links"]],
        "ledger": {"path": ledger_path.resolve().as_posix(), "sha256": _sha256(ledger_path)},
        "context_frame": binding,
        "context_frame_evidence_role": "context-only; no frame-synchronous decision inference" if binding else None,
        "output": {"path": destination.resolve().as_posix(), "sha256": _sha256(destination),
                   "bytes": destination.stat().st_size},
        "human_full_film_review": False,
    }
