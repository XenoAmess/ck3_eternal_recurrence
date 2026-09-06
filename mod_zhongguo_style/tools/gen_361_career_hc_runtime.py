#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the D/M/N/O/P/Q career and headcount CK3 runtime.

The product surface is deliberately isolated from the legacy review cycle.
Callers open one domain case on an assessed direct vassal and then invoke the
numbered manager entry effects.  Every business write is guarded by the shared
five-field case kernel, has a single-use receipt, and is consumed by a bounded
stage barrier.  Exact delayed tickets complete unfinished stages through the
defer route; they never impersonate a manager decision.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from zg361_phase2_career_model import MECHANISM_BEHAVIORS
from zg361_career_hc_semantic_model import (
    EXPECTED_IDS as SEMANTIC_EXPECTED_IDS,
    SEMANTIC_SPECS,
)
from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, plan_effect_shards
from zg361_localization_style import normalize_localization_rows


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_career_hc_runtime.py\n"
EFFECTS_DIR = MOD_ROOT / "common" / "scripted_effects"
LEGACY_EFFECTS_PATH = EFFECTS_DIR / "zg361_career_hc_runtime_effects.txt"
EFFECT_SHARD_GLOB = "zg361_career_hc_*_effects.txt"


@dataclass(frozen=True)
class DomainSpec:
    key: str
    stages: tuple[tuple[int, ...], ...]
    deadlines: tuple[int, ...]
    title_en: str
    title_cn: str


DOMAINS = (
    DomainSpec("d", ((19, 20), (21, 22), (23, 24), (25,)), (90, 90, 180, 90), "Career allocation", "职业分配"),
    DomainSpec("m", ((92, 93), (94,), (95, 96), (97,)), (90, 180, 90, 90), "Career tracks", "职级与双通道"),
    DomainSpec("n", ((98, 99), (100, 101), (102, 103), (104, 105)), (90, 90, 180, 90), "Headcount lifecycle", "编制生命周期"),
    DomainSpec("o", ((106, 107), (108, 109), (110, 111), (112,), (113,)), (90, 180, 90, 90, 180), "Succession planning", "人才盘点与继任"),
    DomainSpec("p", ((114, 115), (116,), (117, 118), (119,), (120,)), (90, 90, 180, 90, 180), "Mobility and onboarding", "内部流动与新人落地"),
    DomainSpec("q", ((121, 122), (123, 124), (125, 126), (127, 128)), (180, 90, 90, 180), "Manager certification", "管理者绩效文化"),
)

DOMAIN_ORDER = tuple(domain.key for domain in DOMAINS)
DOMAIN_BY_KEY = {domain.key: domain for domain in DOMAINS}
NEXT_DOMAIN = {
    domain: DOMAIN_ORDER[index + 1] if index + 1 < len(DOMAIN_ORDER) else None
    for index, domain in enumerate(DOMAIN_ORDER)
}
# Hidden D+1 edges separate domain closure receipts from the next player card.
# They deliberately do not overlap the numbered player events or 901-906
# completion receipts.
QUEUE_EVENTS = {"d": 951, "m": 952, "n": 953, "o": 954, "p": 955}
BATCH_CHOICE_EVENT = 950

EXPECTED_IDS = tuple(
    (*range(19, 26), *range(92, 129))
)
DOMAIN_BY_ID = {
    mechanism_id: domain
    for domain in DOMAINS
    for stage in domain.stages
    for mechanism_id in stage
}
STAGE_BY_ID = {
    mechanism_id: stage_index
    for domain in DOMAINS
    for stage_index, stage in enumerate(domain.stages, start=1)
    for mechanism_id in stage
}

# These actions represent a funded transfer rather than a free label.  Both
# the manager's government treasury and personal gold pay five; the assessed
# official receives the matching two credits.  Route C never spends money.
DUAL_COST_IDS = frozenset({21, 25, 101, 104, 112, 114, 119})

# The player chooses one default treatment for low-risk portfolio paperwork.
# These entries still execute their original guarded core/consumer and retain
# their original visible card as a fail-closed fallback.  Funded transfers,
# people moves, delayed releases and other consequential rulings stay visible.
BATCHABLE_IDS = frozenset(
    {
        19,
        20,
        22,
        23,
        92,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        102,
        106,
        109,
        110,
        117,
        118,
        122,
        126,
        127,
        128,
    }
)
VISIBLE_RULING_IDS = frozenset(EXPECTED_IDS) - BATCHABLE_IDS

# Player-facing route names are deliberately separate from the frozen English
# state identifiers in the semantic model.  The latter are audit vocabulary;
# these strings tell the player what will actually be recorded.
ROUTE_LABELS_CN = {
    19: ("按资格门槛列为可晋升", "绕过提名担保直接列入候选"),
    20: ("提交跨部门评审材料", "提交由提名担保人主导的材料"),
    21: ("按奖金与调薪矩阵兑现薪酬", "把同一预算集中为一次现金激励"),
    22: ("为该岗位预留编制预算", "因例外安排冻结该编制"),
    23: ("完成编制答辩且不借用名额", "以紧急名义借用下一周期名额"),
    24: ("安排下一周期转岗", "阻止本次内部流动"),
    25: ("发出书面留任邀约", "支付反邀约款，但只给口头留任承诺"),
    92: ("保持专业与管理双通道分离", "把明星专家直接转为管理者"),
    93: ("让失败经理回到专家岗", "强留管理岗或降级"),
    94: ("授予有边界的微职级", "只给半级头衔而不补权责"),
    95: ("复审通过，维持本期管理权限", "复审不通过，撤销本期管理权限"),
    96: ("预留一个破格晋升名额", "按提名担保关系破格"),
    97: ("按跨团队校准结果分配名额", "按本地工作量分配名额"),
    98: ("把名额绑定到明确岗位类型", "把名额作为通用空编使用"),
    99: ("只结转一次未用名额", "年底收回未用名额"),
    100: ("仅为关键岗位批准冻结期例外", "因关系安排冻结名额"),
    101: ("按一名资深、两名普通与学徒梯队占用编制", "把全部编制投向资深人选"),
    102: ("按零基重审重新预留编制", "年度结算时收回编制"),
    103: ("收回长期空置的占坑编制", "以虚拟候选继续冻结编制"),
    104: ("同时补入新人和成熟人才", "只补入成熟人才"),
    105: ("把补岗责任绑定到离任岗位", "阻止释放补岗名额"),
    106: ("分别登记关键岗位与关键人才", "把受宠者直接等同于关键岗位"),
    107: ("按证据登记继任准备度", "直接登记为已具备继任资格"),
    108: ("同时授予代理权限、资源与目标", "只加责任而不给资源权限"),
    109: ("只向必要知情人披露高潜标签", "向全体人员公开高潜标签"),
    110: ("先冻结绩效，再单独校准潜力", "用潜力覆盖已冻结绩效"),
    111: ("如实区分遗憾流失与正常流失", "把流失统一包装为健康流动"),
    112: ("兑现一项留任条件", "临时追加反邀约"),
    113: ("按里程碑复制关键知识", "继续依赖单一关键人"),
    114: ("登记人才输出信用", "支付安抚款，同时阻止本次人才转出"),
    115: ("在终选前隐藏内部应聘身份", "在批准前提前暴露身份"),
    116: ("在 90 日内放人", "使用唯一一次延期，在 150 日内放人"),
    117: ("只使用一次转岗爬坡保护", "到岗后立即参加完整排名"),
    118: ("把试用期判定与末位配额分开", "把新人直接放入末位池"),
    119: ("追记三方招聘责任", "只奖招聘速度"),
    120: ("按 3、6、12 个月里程碑结算导师责任", "登记无资源保障的导师关系"),
    121: ("先用三人小团队试任经理", "不经试任，直接交付大团队"),
    122: ("采用结果 40%、育人 30%、价值观 30%", "把结果权重提高到 80%"),
    123: ("采用六因素可信下属反馈", "只采纳一张匿名票"),
    124: ("先确认接班人，再批准经理晋升", "先晋升经理，再补接班人"),
    125: ("把危机处置授权给团队", "由经理亲自包揽救火"),
    126: ("按绩效与价值观四象限处置", "仅按绩效高低决定处置"),
    127: ("增设一层管理岗，把直属人数限制为八人", "保持十一人直属的扁平结构，并承受评分失真"),
    128: ("依据本次气候结果调整下一周期配额政策", "忽略本次气候结果，下一周期继续沿用刚性配额"),
}

# What has happened before the player chooses.  These are deliberately not
# mini-catalogues of A/B/C: the buttons own the executable decisions, while
# the body names the person, the live conflict and why a ruling is due now.
CASE_CONTEXT_CN = {
    19: "晋升材料已过初核，但资格证据与提名关系并不一致；现在必须决定是否把当事人列入候选册。",
    20: "候选材料已经送齐，跨部门证据与提名担保人的陈述互有出入；评审包必须在本阶段定稿。",
    21: "本轮绩效已经冻结，奖金与调薪只能从同一笔预算兑现；任何支付都会同时记入双方钱账。",
    22: "拟任岗位尚未取得稳定编制，现有名额又已被其他承诺占用；本阶段必须确定这处空缺是否继续保留。",
    23: "团队已经提交增员理由，但下一周期名额也有人预先占用；这次答辩必须留下可追责的编制结论。",
    24: "当事人提出内部调动，原任岗位的交接与补岗尚无定案；流动窗口将在本阶段结束。",
    25: "外部邀约已经送到当事人手中，留任预算与口头承诺不能混为一谈；挽留条件须在离任前落定。",
    92: "当事人的专业贡献已经达到进阶门槛，但管理职责尚未接受检验；专业进阶与转任管理的依据彼此冲突。",
    93: "现任管理者未能完成管理职责，专业能力却仍有价值；本阶段要为其确定可继续承担的岗位。",
    94: "完整晋升条件尚未满足，但职责已经扩大；若授予过渡职级，权责与薪酬边界必须同时留下记录。",
    95: "年度管理复审已经到期，在任者的团队结果与履责记录均已冻结；本期权限需要重新确认。",
    96: "候选人请求跳过通常年限，破格名额只有一个；战功、绩效与担保关系必须在本次裁决中分开。",
    97: "多个团队争用同一批晋升名额，各自的本地排名不能直接互比；跨团队校准已经进入分配阶段。",
    98: "一处新名额正在增长、补缺与临时项目之间争用；用途一旦登记，就会约束后续空缺。",
    99: "本周期留下一个未用名额，招聘进度不足以自动保留它；到期前必须决定是否允许一次结转。",
    100: "冻结期内出现关键岗位申请，普通增员已经停办；这项例外必须留下岗位风险和批准责任。",
    101: "同一笔编制预算只能组成一支人才梯队，资深交付与后备培养正在争用名额。",
    102: "旧编制已经进入零基重审，部分岗位仍无近期工作量；保留与回收都必须在本阶段落账。",
    103: "一处编制长期空置，候选管线仍未形成；继续占用将挤压其他团队的真实补员需求。",
    104: "新人培养与成熟人才采购争用同一笔补员预算；两类渠道的候选与薪酬记录目前都未落定。",
    105: "有人离任后留下岗位空缺，原团队与中央编制池都主张名额归己；补岗责任必须先确定。",
    106: "当前岗位的重要性与现任者的受宠程度被混在一起；两者若继续混写，继任依据就会失真。",
    107: "继任候选已经进入盘点，但准备程度尚无统一证据；本次登记会决定其后续培养位置。",
    108: "候选人即将开始代理任职，责任、权限与资源仍未完全对齐；试任条件必须在开始前写清。",
    109: "高潜名单已经形成，公开范围却尚未确定；披露过多会伤害未入选者，过少则妨碍培养。",
    110: "本期绩效已经冻结，潜力判断随后才到；两张表若混写，会改坏已经完成的考核。",
    111: "一名关键成员即将离任，真实原因会影响补岗与管理问责；流失类型必须在案卷关闭前登记。",
    112: "当事人已有离开意向，官署只能兑现一项有预算的留任条件；未经拨款的许诺不得冒充保障。",
    113: "关键知识仍集中在一人手里，继任者尚不能独立接手；移交期限已经进入最后阶段。",
    114: "当事人的转岗申请已获接收方关注，原上司却要承担空缺；人才输出信用与补岗责任需要同时落账。",
    115: "一份内部应聘材料已经进入终选，过早暴露身份可能引来阻拦；申请人的知情范围必须确定。",
    116: "内部录用已经成立，原团队仍有交接任务未完；正常放人期与唯一一次延期都从现在起算。",
    117: "转岗者刚到新岗位，旧履历与新职责不能直接等量比较；首轮爬坡期需要明确边界。",
    118: "新人仍在试用期，岗位门槛与团队末位配额发生冲突；胜任判断和团队排名给出了不同结论。",
    119: "一名新人的爬坡结果已经可见，选人、批准与带教三方的责任都要据此追记。",
    120: "新人尚未独立交付，导师投入也没有完成结算；三段带教里程碑必须确定责任与资源。",
    121: "一名专家第一次承担管理职责，尚无带领大团队的证据；试任规模会决定这次失败的代价。",
    122: "管理者本期结果不错，但育人与价值观记录并不同步；三类权重必须在记分前冻结。",
    123: "下属反馈已经收齐，样本可信度和匿名情绪并不相同；管理评价需要确定采用哪些证据。",
    124: "现任经理进入晋升窗口，但原团队还没有可接班的人；晋升与继任的先后必须现在落定。",
    125: "团队遭遇一次急务，经理与下属都能出手；这次处置会留下授权或包揽的管理证据。",
    126: "当事人的绩效与价值观落在不同象限，只看其中一张表会得到相反结论。",
    127: "现有十一名直属人员已经超过八人的可靠评分上限；增设层级与维持扁平结构各有代价。",
    128: "本周期的压力、协作和流失记录已经汇齐；这些记录与沿用刚性配额的旧例相互冲突。",
}

COMPLETION_COPY_CN = {
    "d": ("职业安排办理完毕", "晋升、调任、留任与相关钱账已经分别归档；尚在期限内的安排会按到期日继续结算。"),
    "m": ("职级路径办理完毕", "专业与管理路径、过渡职级和破格名额已经落定；本轮不会再改写这些选择。"),
    "n": ("编制处置办理完毕", "保留、占用、回收与补岗责任已经写入各自名额；下一轮将沿用本次结论。"),
    "o": ("继任盘点办理完毕", "关键岗位、候选准备度与知识移交已经归档；未到期的试任和留任条件仍会继续履行。"),
    "p": ("内部流动办理完毕", "应聘、放人、爬坡、补岗与带教责任已经分开登记；后续只按各自期限结算。"),
    "q": ("管理复审办理完毕", "试任、权重、下属反馈、继任与授权记录已经写入本轮管理评价。"),
}

TITLE_OVERRIDE_CN = {119: "招聘质量追责"}
TITLE_OVERRIDE_EN = {119: "Recruitment quality accountability"}
CASE_CONTEXT_OVERRIDE_EN = {
    92: (
        "The official's professional contribution has reached the advancement threshold, "
        "but their management duties remain untested; the evidence for professional "
        "advancement conflicts with the case for a management appointment. This ruling "
        "settles within 90 days."
    ),
    104: (
        "Developing newcomers and hiring experienced staff compete for the same staffing "
        "budget; neither channel's candidate and compensation records are settled. This "
        "ruling settles within 90 days."
    ),
    106: (
        "The importance of the post has been conflated with the incumbent's favor; leaving "
        "them combined would distort the succession record. This ruling settles within "
        "90 days."
    ),
    118: (
        "The recruit remains on probation, while the role threshold and the team's bottom "
        "quota point to different outcomes. This ruling settles within 180 days."
    ),
    119: (
        "One recruit's ramp-up result is now available. Accountability for "
        "selection, approval and mentoring must be recorded against that outcome; "
        "this ruling settles within 90 days."
    ),
    127: (
        "Eleven direct reports now exceed the reliable evaluation span of eight; adding a "
        "management layer and preserving the flat structure each carries a cost. This "
        "ruling settles within 180 days."
    ),
    128: (
        "This cycle's pressure, collaboration and attrition records are complete, and they "
        "conflict with the precedent of retaining the rigid quota. This ruling settles "
        "within 180 days."
    ),
}
ROUTE_LABELS_OVERRIDE_EN = {
    21: (
        "Pay compensation under the bonus and salary-adjustment matrix.",
        "Concentrate the same budget in a single cash award.",
    ),
    25: (
        "Issue a written retention offer.",
        "Pay for a counteroffer but give only an oral retention promise.",
    ),
    95: (
        "Pass the review and retain this cycle's management authority.",
        "Fail the review and revoke this cycle's management authority.",
    ),
    101: (
        "Use staffing for one senior, two regular and one apprentice tier.",
        "Commit all staffing capacity to senior candidates.",
    ),
    104: (
        "Hire both newcomers and experienced candidates.",
        "Hire experienced candidates only.",
    ),
    109: (
        "Disclose the high-potential label only to those who need to know.",
        "Disclose the high-potential label to everyone.",
    ),
    114: (
        "Record talent-export credit.",
        "Pay a retention award and block this talent transfer.",
    ),
    119: (
        "Record accountability across selection, approval and mentoring.",
        "Reward hiring speed alone.",
    ),
    121: (
        "Trial the manager with a three-person team first.",
        "Skip the trial and assign a large team immediately.",
    ),
    126: (
        "Act on the four-quadrant performance and values assessment.",
        "Decide the action from performance alone.",
    ),
    127: (
        "Add one management layer and limit direct reports to eight.",
        "Keep eleven direct reports in a flat structure and accept distorted ratings.",
    ),
    128: (
        "Use this climate result to adjust next cycle's quota policy.",
        "Ignore this climate result and retain the rigid quota next cycle.",
    ),
}

OBJECT_KIND_CN = {
    "candidate": "候选人",
    "vacancy": "岗位空缺",
    "compensation": "薪酬回执",
    "hc-slot": "编制名额",
    "incumbent": "在任者",
    "succession": "继任案卷",
    "backfill": "补岗责任",
    "manager": "管理者责任",
}

HC_DEST_A = {
    98: "reserved",
    99: "reserved",
    100: "reserved",
    101: "occupied",
    102: "reserved",
    103: "reclaimed",
    104: "occupied",
    105: "reserved",
}
HC_DEST_B = {
    98: "frozen",
    99: "reclaimed",
    100: "frozen",
    101: "occupied",
    102: "reclaimed",
    103: "frozen",
    104: "occupied",
    105: "frozen",
}

Q_AUTHORITY_IDS = tuple(range(121, 129))
Q_REQUIRED_OBJECT_KINDS = frozenset(
    {"vacancy", "hc-slot", "candidate", "incumbent", "succession", "backfill"}
)


def clean_generated_text(text: str) -> str:
    """Normalize generator-only indentation without changing CK3 semantics."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean_generated_text(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean_generated_text(text).encode("utf-8")


def validate_specs() -> None:
    if tuple(sorted(DOMAIN_BY_ID)) != EXPECTED_IDS:
        raise ValueError("career/HC runtime must cover exactly 44 frozen IDs")
    if len(DOMAIN_BY_ID) != 44:
        raise ValueError("career/HC runtime ID count drifted")
    if set(DOMAIN_BY_ID) - set(MECHANISM_BEHAVIORS):
        raise ValueError("runtime references an unknown career model behavior")
    if {domain.key for domain in DOMAINS} != {"d", "m", "n", "o", "p", "q"}:
        raise ValueError("domain set drifted")
    if DOMAIN_ORDER != ("d", "m", "n", "o", "p", "q"):
        raise ValueError("career/HC portfolio order drifted")
    if set(QUEUE_EVENTS) != set(DOMAIN_ORDER[:-1]):
        raise ValueError("career/HC queue event set drifted")
    for domain in DOMAINS:
        if len(domain.stages) != len(domain.deadlines):
            raise ValueError(f"{domain.key}: stage/deadline count mismatch")
        flattened = [item for stage in domain.stages for item in stage]
        if len(flattened) != len(set(flattened)):
            raise ValueError(f"{domain.key}: repeated mechanism")
    if not DUAL_COST_IDS <= set(EXPECTED_IDS):
        raise ValueError("dual-cost mechanism outside slice")
    if len(BATCHABLE_IDS) != 22:
        raise ValueError("career/HC background batch must cover exactly 22 low-risk rulings")
    if BATCHABLE_IDS | VISIBLE_RULING_IDS != set(EXPECTED_IDS):
        raise ValueError("career/HC batch/visible partition lost a frozen mechanism")
    if BATCHABLE_IDS & VISIBLE_RULING_IDS:
        raise ValueError("career/HC batch/visible partition overlaps")
    if DUAL_COST_IDS & BATCHABLE_IDS:
        raise ValueError("funded career/HC rulings must remain visible")
    if EXPECTED_IDS != SEMANTIC_EXPECTED_IDS:
        raise ValueError("career/HC semantic registry ID drifted")
    if set(SEMANTIC_SPECS) != set(EXPECTED_IDS):
        raise ValueError("career/HC semantic registry coverage drifted")
    if set(ROUTE_LABELS_CN) != set(EXPECTED_IDS):
        raise ValueError("career/HC player-facing route label coverage drifted")
    if set(CASE_CONTEXT_CN) != set(EXPECTED_IDS):
        raise ValueError("career/HC player-facing case context coverage drifted")
    if set(COMPLETION_COPY_CN) != set(DOMAIN_ORDER):
        raise ValueError("career/HC completion copy coverage drifted")
    for overrides in (
        TITLE_OVERRIDE_CN,
        TITLE_OVERRIDE_EN,
        CASE_CONTEXT_OVERRIDE_EN,
        ROUTE_LABELS_OVERRIDE_EN,
    ):
        if not set(overrides) <= set(EXPECTED_IDS):
            raise ValueError("career/HC localization override references an unknown mechanism")
    q_kinds = {
        kind.value
        for mechanism_id in Q_AUTHORITY_IDS
        for kind in SEMANTIC_SPECS[mechanism_id].object_kinds
    }
    if not Q_REQUIRED_OBJECT_KINDS <= q_kinds:
        raise ValueError("Q manager certification lost a typed career/HC object family")
    if {kind.value for kind in SEMANTIC_SPECS[124].object_kinds} != (
        Q_REQUIRED_OBJECT_KINDS | {"manager"}
    ):
        raise ValueError("Q124 must remain the authoritative succession/backfill join")


def domain_vars(domain: str) -> dict[str, str]:
    prefix = f"zg361_case_{domain}"
    return {
        "owner": f"{prefix}_owner",
        "subject": f"{prefix}_subject",
        "cycle": f"{prefix}_cycle_serial",
        "case": f"{prefix}_case_serial",
        "state": f"{prefix}_state",
        "active": f"{prefix}_active",
        "revision": f"{prefix}_revision",
        "timeline": f"{prefix}_timeline_serial",
        "feedback": f"{prefix}_feedback_revision",
    }


def kernel_guard(domain: str, state: int, *, owner: str) -> str:
    row = domain_vars(domain)
    return f'''zg361_case_kernel_full_guard_trigger = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                EXPECTED_OWNER = {owner}
                EXPECTED_SUBJECT = this
                EXPECTED_CYCLE = var:{row["cycle"]}
                EXPECTED_CASE = var:{row["case"]}
                EXPECTED_STATE = {state}
            }}'''


def record_operation(mechanism_id: int, domain: str, state: int) -> str:
    row = domain_vars(domain)
    p = f"zg361_ch_m{mechanism_id:03d}"
    return f'''zg361_case_kernel_record_operation_effect = {{
            OWNER_VAR = {row["owner"]}
            SUBJECT_VAR = {row["subject"]}
            CYCLE_VAR = {row["cycle"]}
            CASE_VAR = {row["case"]}
            STATE_VAR = {row["state"]}
            ACTIVE_VAR = {row["active"]}
            REVISION_VAR = {row["revision"]}
            TIMELINE_VAR = {row["timeline"]}
            FEEDBACK_VAR = {row["feedback"]}
            LAST_OPERATION_VAR = zg361_case_{domain}_last_operation
            LAST_CHOICE_VAR = zg361_case_{domain}_last_choice
            RECEIPT_OWNER_VAR = {p}_receipt_owner
            RECEIPT_SUBJECT_VAR = {p}_receipt_subject
            RECEIPT_CYCLE_VAR = {p}_receipt_cycle
            RECEIPT_CASE_VAR = {p}_receipt_case
            RECEIPT_STATE_VAR = {p}_receipt_state
            RECEIPT_CHOICE_VAR = {p}_receipt_route
            TICKET_OWNER = var:{row["owner"]}
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{row["cycle"]}
            TICKET_CASE = var:{row["case"]}
            TICKET_STATE = {state}
            CHOICE = $ROUTE$
            OPERATION_ID = {mechanism_id}
        }}'''


def transaction_journal(mechanism_id: int, domain: str, state: int, resource: str) -> str:
    row = domain_vars(domain)
    p = f"zg361_ch_m{mechanism_id:03d}_{resource}"
    return f'''zg361_case_kernel_reserve_transaction_effect = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                REVISION_VAR = {row["revision"]}
                AVAILABLE_VAR = {p}_available
                RESERVED_VAR = {p}_reserved
                RECEIPT_AMOUNT_VAR = {p}_amount
                RECEIPT_STATUS_VAR = {p}_status
                RECEIPT_OWNER_VAR = {p}_owner
                RECEIPT_CYCLE_VAR = {p}_cycle
                RECEIPT_CASE_VAR = {p}_case
                TICKET_OWNER = var:{row["owner"]}
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:{row["cycle"]}
                TICKET_CASE = var:{row["case"]}
                TICKET_STATE = {state}
                AMOUNT = 5
            }}
            if = {{
                limit = {{
                    trigger_if = {{
                        limit = {{ has_variable = zg361_case_kernel_applied }}
                        var:zg361_case_kernel_applied = 1
                    }}
                    trigger_else = {{ always = no }}
                }}
                zg361_case_kernel_settle_transaction_effect = {{
                    OWNER_VAR = {row["owner"]}
                    SUBJECT_VAR = {row["subject"]}
                    CYCLE_VAR = {row["cycle"]}
                    CASE_VAR = {row["case"]}
                    STATE_VAR = {row["state"]}
                    ACTIVE_VAR = {row["active"]}
                    REVISION_VAR = {row["revision"]}
                    RESERVED_VAR = {p}_reserved
                    SETTLED_VAR = {p}_settled
                    RECEIPT_AMOUNT_VAR = {p}_amount
                    RECEIPT_STATUS_VAR = {p}_status
                    TICKET_OWNER = var:{row["owner"]}
                    TICKET_SUBJECT = this
                    TICKET_CYCLE = var:{row["cycle"]}
                    TICKET_CASE = var:{row["case"]}
                    TICKET_STATE = {state}
                }}
            }}'''


def special_payload(mechanism_id: int) -> str:
    """Return the behavior-specific projection consumed by later stages."""

    snippets = {
        19: "set_variable = { name = zg361_ch_promotion_eligible value = var:zg361_ch_m019_value }",
        20: "set_variable = { name = zg361_ch_promotion_packet_state value = var:zg361_ch_m020_route }",
        21: "set_variable = { name = zg361_ch_bonus_salary_matrix value = var:zg361_ch_m021_value }",
        22: "set_variable = { name = zg361_ch_soft_hc_budget value = var:zg361_ch_m022_route }",
        23: "set_variable = { name = zg361_ch_jingcha_treasury_delta value = 0 }\n            set_variable = { name = zg361_ch_jingcha_personal_delta value = 0 }\n            set_variable = { name = zg361_ch_hc_defense_year value = current_year }",
        24: "set_variable = { name = zg361_ch_transfer_effective_cycle value = { value = var:zg361_case_d_cycle_serial add = 1 } }",
        25: "set_variable = { name = zg361_ch_counteroffer_terminal value = var:zg361_ch_m025_route }",
        92: "set_variable = { name = zg361_ch_career_track value = var:zg361_ch_m092_route }\n            set_variable = { name = zg361_ch_management_authority value = 0 }\n            if = { limit = { var:zg361_ch_m092_route = 2 zg361_is_celestial_liege_trigger = yes } set_variable = { name = zg361_ch_management_authority value = 1 } }",
        93: "set_variable = { name = zg361_ch_returned_to_expert value = 1 }\n            set_variable = { name = zg361_ch_manager_retry_cycle value = { value = var:zg361_case_m_cycle_serial add = 1 } }",
        94: "change_variable = { name = zg361_ch_micro_level add = 1 }\n            set_variable = { name = zg361_ch_title_unchanged value = 1 }",
        95: "set_variable = { name = zg361_ch_management_review_year value = current_year }\n            set_variable = { name = zg361_ch_management_review_outcome value = var:zg361_ch_m095_route }",
        96: "set_variable = { name = zg361_ch_exceptional_slot_used value = 1 }\n            if = { limit = { var:zg361_ch_m096_route = 2 } change_variable = { name = zg361_ch_future_promotion_debt add = 1 } }",
        97: "set_variable = { name = zg361_ch_cross_team_calibration_winner value = var:zg361_case_m_subject }",
        106: "set_variable = { name = zg361_ch_critical_role_label value = 1 }\n            set_variable = { name = zg361_ch_key_talent_label value = var:zg361_ch_m106_route }",
        107: "set_variable = { name = zg361_ch_readiness_band value = var:zg361_ch_m107_route }\n            set_variable = { name = zg361_ch_readiness_due_cycle value = { value = var:zg361_case_o_cycle_serial add = 2 } }",
        108: "set_variable = { name = zg361_ch_acting_authority_bound value = 1 }\n            set_variable = { name = zg361_ch_acting_capacity_units value = 1 }",
        109: "set_variable = { name = zg361_ch_high_potential_visibility value = var:zg361_ch_m109_route }\n            set_variable = { name = zg361_ch_high_potential_subject_can_read value = 1 }",
        110: "set_variable = { name = zg361_ch_performance_frozen_before_potential value = 1 }\n            set_variable = { name = zg361_ch_potential_score value = { value = var:zg361_ch_m110_value multiply = 10 add = 60 min = 0 max = 100 } }",
        111: "set_variable = { name = zg361_ch_attrition_class value = var:zg361_ch_m111_route }\n            set_variable = { name = zg361_ch_attrition_hc_released value = 1 }",
        112: "set_variable = { name = zg361_ch_stay_promise_state value = var:zg361_ch_m112_route }\n            set_variable = { name = zg361_ch_stay_promise_due_cycle value = { value = var:zg361_case_o_cycle_serial add = 1 } }",
        113: "change_variable = { name = zg361_ch_knowledge_coverage_percent add = 25 }\n            set_variable = { name = zg361_ch_knowledge_milestone_receipt value = var:zg361_case_o_case_serial }",
        114: "set_variable = { name = zg361_ch_talent_export_credit value = 1 }\n            set_variable = { name = zg361_ch_backfill_settled value = 1 }",
        115: "set_variable = { name = zg361_ch_application_identity_visible value = 0 }\n            if = { limit = { var:zg361_ch_m115_route = 2 } set_variable = { name = zg361_ch_application_identity_visible value = 1 } }",
        116: "set_variable = { name = zg361_ch_release_days value = 90 }\n            set_variable = { name = zg361_ch_release_extension_used value = 0 }\n            if = { limit = { var:zg361_ch_m116_route = 2 } set_variable = { name = zg361_ch_release_days value = 150 } set_variable = { name = zg361_ch_release_extension_used value = 1 } }",
        117: "set_variable = { name = zg361_ch_ramp_protection_used_lifetime value = 1 }\n            set_variable = { name = zg361_ch_ramp_participation_percent value = 40 }",
        118: "set_variable = { name = zg361_ch_regular_quota_denominator value = 10 }\n            set_variable = { name = zg361_ch_probation_failures_separate value = 1 }",
        119: "set_variable = { name = zg361_ch_hiring_quality_outcome value = var:zg361_ch_m119_route }\n            set_variable = { name = zg361_ch_hiring_quality_receivers value = 3 }",
        120: "set_variable = { name = zg361_ch_mentor_month_3 value = 1 }\n            set_variable = { name = zg361_ch_mentor_month_6 value = 1 }\n            set_variable = { name = zg361_ch_mentor_month_12 value = 1 }\n            set_variable = { name = zg361_ch_mentor_credit_settled value = 1 }",
        121: "set_variable = { name = zg361_ch_manager_trial_team_size value = 3 }\n            set_variable = { name = zg361_ch_manager_trial_due_cycle value = { value = var:zg361_case_q_cycle_serial add = 1 } }",
        122: "set_variable = { name = zg361_ch_manager_weight_hard value = 40 }\n            set_variable = { name = zg361_ch_manager_weight_people value = 30 }\n            set_variable = { name = zg361_ch_manager_weight_values value = 30 }",
        123: "set_variable = { name = zg361_ch_subordinate_survey_factors value = 6 }\n            set_variable = { name = zg361_ch_subordinate_survey_credibility value = 100 }",
        124: "set_variable = { name = zg361_ch_successor_accepted value = 1 }\n            set_variable = { name = zg361_ch_manager_promotion_released value = 1 }",
        125: "set_variable = { name = zg361_ch_crisis_hours_budget value = 100 }\n            set_variable = { name = zg361_ch_crisis_hours_used value = 100 }\n            set_variable = { name = zg361_ch_successor_evidence value = 1 }",
        126: "set_variable = { name = zg361_ch_values_quadrant value = var:zg361_ch_m126_route }",
        127: "set_variable = { name = zg361_ch_span_frozen value = 8 }\n            set_variable = { name = zg361_ch_span_excess value = 3 }",
        128: "set_variable = { name = zg361_ch_climate_snapshot_cycle value = var:zg361_case_q_cycle_serial }\n            set_variable = { name = zg361_ch_next_cycle_quota_policy value = var:zg361_ch_m128_route }",
    }
    if 98 <= mechanism_id <= 105:
        snippets[mechanism_id] = (
            f"set_variable = {{ name = zg361_ch_hc_mechanism_{mechanism_id:03d}_source value = "
            f"var:zg361_ch_m{mechanism_id:03d}_route }}"
        )
    return snippets[mechanism_id]


def render_cost_initialization(mechanism_id: int) -> str:
    if mechanism_id not in DUAL_COST_IDS:
        return ""
    lines = []
    for resource in ("treasury", "gold"):
        p = f"zg361_ch_m{mechanism_id:03d}_{resource}"
        lines.extend(
            (
                f"set_variable = {{ name = {p}_available value = 5 }}",
                f"set_variable = {{ name = {p}_reserved value = 0 }}",
                f"set_variable = {{ name = {p}_settled value = 0 }}",
                f"set_variable = {{ name = {p}_status value = 0 }}",
            )
        )
    return "\n        ".join(lines)


def render_q_authority_initialization() -> str:
    """Initialize the authoritative Q capacity books and typed-object locks."""

    lines = [
        "set_variable = { name = zg361_ch_q_manager_hc_authorized value = 4 }",
        "set_variable = { name = zg361_ch_q_manager_hc_available value = 4 }",
        "set_variable = { name = zg361_ch_q_manager_hc_reserved value = 0 }",
        "set_variable = { name = zg361_ch_q_manager_hc_occupied value = 0 }",
        "set_variable = { name = zg361_ch_q_manager_hc_frozen value = 0 }",
        "set_variable = { name = zg361_ch_q_manager_hc_reclaimed value = 0 }",
        "set_variable = { name = zg361_ch_q_manager_hc_conserved value = 1 }",
        "set_variable = { name = zg361_ch_q_crisis_hours_authorized value = 100 }",
        "set_variable = { name = zg361_ch_q_crisis_hours_available value = 100 }",
        "set_variable = { name = zg361_ch_q_crisis_hours_delegated value = 0 }",
        "set_variable = { name = zg361_ch_q_crisis_hours_manager value = 0 }",
        "set_variable = { name = zg361_ch_q_crisis_hours_conserved value = 1 }",
        "remove_variable = zg361_ch_q_named_successor_candidate",
        "remove_variable = zg361_ch_q_named_survey_respondent",
    ]
    for mechanism_id in Q_AUTHORITY_IDS:
        p = f"zg361_ch_m{mechanism_id:03d}_business"
        lines.extend(
            (
                f"set_variable = {{ name = {p}_consumed value = 0 }}",
                f"set_variable = {{ name = {p}_deferred value = 0 }}",
                f"set_variable = {{ name = {p}_debt value = 0 }}",
                f"set_variable = {{ name = {p}_object_count value = 0 }}",
            )
        )
    return "\n        ".join(lines)


def render_q_named_people_capture() -> str:
    """Freeze real subordinate characters used by Q survey/succession objects."""

    return '''ordered_vassal = {
                limit = { zg361_is_reviewable_vassal_trigger = yes }
                order_by = stewardship
                position = 0
                save_temporary_scope_as = zg361_ch_q_named_successor_candidate_scope
            }
            if = {
                limit = { exists = scope:zg361_ch_q_named_successor_candidate_scope }
                set_variable = {
                    name = zg361_ch_q_named_successor_candidate
                    value = scope:zg361_ch_q_named_successor_candidate_scope
                }
                set_variable = {
                    name = zg361_ch_q_named_survey_respondent
                    value = scope:zg361_ch_q_named_successor_candidate_scope
                }
            }'''


def domain_mechanisms(domain: DomainSpec) -> tuple[int, ...]:
    return tuple(mechanism_id for stage in domain.stages for mechanism_id in stage)


def event_scope_names(domain: str) -> dict[str, str]:
    prefix = f"zg361_ch_{domain}_event"
    return {
        "owner": f"{prefix}_owner",
        "subject": f"{prefix}_subject",
        "cycle": f"{prefix}_cycle",
        "case": f"{prefix}_case",
    }


def next_domain_mechanism(domain: DomainSpec, mechanism_id: int) -> int | None:
    mechanisms = domain_mechanisms(domain)
    index = mechanisms.index(mechanism_id)
    return mechanisms[index + 1] if index + 1 < len(mechanisms) else None


def render_batch_route_guard() -> str:
    return '''has_variable = zg361_ch_player_batch_route
            OR = {
                var:zg361_ch_player_batch_route = 1
                var:zg361_ch_player_batch_route = 2
                var:zg361_ch_player_batch_route = 3
            }'''


def render_subject_entry(domain: DomainSpec, mechanism_id: int) -> str:
    """Enter one numbered ruling from assessed-official scope.

    Batchable rulings attempt the exact same manager/core/consumer chain.  An
    absent batch preference, stale case guard, or other failed application
    opens the original card instead of silently skipping the ruling.
    """

    if mechanism_id not in BATCHABLE_IDS:
        return f"root = {{ trigger_event = {{ id = zg361ch.{mechanism_id} days = 1 }} }}"
    return f'''if = {{
        limit = {{
            {render_batch_route_guard()}
        }}
        zg361_career_hc_m{mechanism_id:03d}_background_apply_effect = yes
    }}
    else = {{ root = {{ trigger_event = {{ id = zg361ch.{mechanism_id} days = 1 }} }} }}'''


def render_subject_successor(domain: DomainSpec, mechanism_id: int) -> str:
    """Continue a player portfolio from assessed-official scope."""

    successor = next_domain_mechanism(domain, mechanism_id)
    if successor is not None:
        return render_subject_entry(domain, successor)
    if NEXT_DOMAIN[domain.key] is not None:
        return f"root = {{ trigger_event = {{ id = zg361ch.{QUEUE_EVENTS[domain.key]} days = 1 }} }}"
    return f"zg361_career_hc_finalize_{domain.key}_portfolio_effect = yes"


def render_background_resource_guard(mechanism_id: int) -> str:
    """Return the precondition that forces scarce-resource cases visible."""

    if mechanism_id in {98, 99, 100, 102}:
        return '''trigger_if = {
                limit = {
                    OR = {
                        var:zg361_ch_player_batch_route = 1
                        var:zg361_ch_player_batch_route = 2
                    }
                }
                var:zg361_ch_hc_available >= 1
            }
            trigger_else = { always = yes }'''
    if mechanism_id == 127:
        return '''trigger_if = {
                limit = { var:zg361_ch_player_batch_route = 1 }
                var:zg361_ch_q_manager_hc_available >= 1
            }
            trigger_else = { always = yes }'''
    return "always = yes"


def render_background_apply(mechanism_id: int, domain: DomainSpec) -> str:
    """Apply one low-risk ruling silently, with its original card as fallback."""

    return f'''# Low-risk portfolio default for #{mechanism_id:03d}; original card is the fallback.
zg361_career_hc_m{mechanism_id:03d}_background_apply_effect = {{
    if = {{
        limit = {{
            {render_batch_route_guard()}
            {render_background_resource_guard(mechanism_id)}
        }}
        zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{
            ROUTE = var:zg361_ch_player_batch_route
        }}
        if = {{
            limit = {{
                has_variable = zg361_ch_runtime_applied
                var:zg361_ch_runtime_applied = 1
            }}
            {render_subject_successor(domain, mechanism_id)}
        }}
        else = {{
            root = {{ trigger_event = {{ id = zg361ch.{mechanism_id} days = 1 }} }}
        }}
    }}
    else = {{
        root = {{ trigger_event = {{ id = zg361ch.{mechanism_id} days = 1 }} }}
    }}
}}'''


def render_domain_open(domain: DomainSpec) -> str:
    extra_q = (
        "\n            zg361_is_celestial_liege_trigger = yes"
        "\n            any_vassal = { zg361_is_reviewable_vassal_trigger = yes }"
        if domain.key == "q"
        else ""
    )
    receipt_resets = []
    cost_resets = []
    ids = list(domain_mechanisms(domain))
    for mechanism_id in ids:
        p = f"zg361_ch_m{mechanism_id:03d}"
        receipt_resets.extend(
            (
                f"set_variable = {{ name = {p}_receipt_active value = 0 }}",
                f"set_variable = {{ name = {p}_consumed value = 0 }}",
                f"set_variable = {{ name = {p}_deferred value = 0 }}",
            )
        )
        rendered_cost = render_cost_initialization(mechanism_id)
        if rendered_cost:
            cost_resets.append(rendered_cost)
    extra_init = {
        "d": "set_variable = { name = zg361_ch_promotion_slots value = 1 }\n        set_variable = { name = zg361_ch_future_promotion_debt value = 0 }",
        "m": "set_variable = { name = zg361_ch_micro_level value = 1 }\n        set_variable = { name = zg361_ch_management_authority value = 0 }",
        "n": "set_variable = { name = zg361_ch_hc_authorized value = 8 }\n        set_variable = { name = zg361_ch_hc_available value = 8 }\n        set_variable = { name = zg361_ch_hc_reserved value = 0 }\n        set_variable = { name = zg361_ch_hc_occupied value = 0 }\n        set_variable = { name = zg361_ch_hc_frozen value = 0 }\n        set_variable = { name = zg361_ch_hc_reclaimed value = 0 }\n        set_variable = { name = zg361_ch_hc_conserved value = 1 }",
        "o": "set_variable = { name = zg361_ch_knowledge_coverage_percent value = 0 }\n        set_variable = { name = zg361_ch_acting_authority_bound value = 0 }",
        "p": "set_variable = { name = zg361_ch_application_identity_visible value = 0 }\n        set_variable = { name = zg361_ch_release_extension_used value = 0 }",
        "q": "set_variable = { name = zg361_ch_manager_weight_hard value = 40 }\n        set_variable = { name = zg361_ch_manager_weight_people value = 30 }\n        set_variable = { name = zg361_ch_manager_weight_values value = 30 }\n        " + render_q_authority_initialization(),
    }[domain.key]
    q_people_capture = render_q_named_people_capture() if domain.key == "q" else ""
    deadline_resets = []
    for state in range(1, len(domain.stages) + 1):
        suffixes = ("a", "b") if domain.key == "p" and state == 3 else ("x",)
        for suffix in suffixes:
            deadline_resets.extend(
                (
                    f"set_variable = {{ name = zg361_ch_{domain.key}_s{state}_{suffix}_deadline_pending value = 0 }}",
                    f"set_variable = {{ name = zg361_ch_{domain.key}_s{state}_{suffix}_deadline_expired value = 0 }}",
                )
            )
    all_resets = "\n        ".join((*receipt_resets, *cost_resets, *deadline_resets))
    count = len(ids)
    player_start = (
        f"root = {{ trigger_event = {{ id = zg361ch.{BATCH_CHOICE_EVENT} days = 1 }} }}"
        if domain.key == "d"
        else render_subject_entry(domain, ids[0])
    )
    return f'''# Open domain {domain.key.upper()} on one assessed direct vassal.
zg361_career_hc_open_{domain.key}_case_effect = {{
    remove_variable = zg361_ch_runtime_applied
    if = {{
        limit = {{
            root = {{
                zg361_is_celestial_liege_trigger = yes
                has_variable = zg361_review_serial
            }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root{extra_q}
        }}
        zg361_case_{domain.key}_open_effect = yes
        if = {{
            limit = {{
                trigger_if = {{
                    limit = {{ has_variable = zg361_case_kernel_applied }}
                    var:zg361_case_kernel_applied = 1
                }}
                trigger_else = {{ always = no }}
            }}
            set_variable = {{ name = zg361_ch_{domain.key}_authorized value = {count} }}
            set_variable = {{ name = zg361_ch_{domain.key}_available value = {count} }}
            set_variable = {{ name = zg361_ch_{domain.key}_used value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_debt value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_completed value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_favorable value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_extractive value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_outcome value = 0 }}
            set_variable = {{ name = zg361_ch_{domain.key}_conserved value = 1 }}
            {extra_init}
            {all_resets}
            {q_people_capture}
            var:zg361_case_{domain.key}_owner = {{ save_scope_as = zg361_ch_{domain.key}_event_owner }}
            save_scope_as = zg361_ch_{domain.key}_event_subject
            save_scope_value_as = {{ name = zg361_ch_{domain.key}_event_cycle value = var:zg361_case_{domain.key}_cycle_serial }}
            save_scope_value_as = {{ name = zg361_ch_{domain.key}_event_case value = var:zg361_case_{domain.key}_case_serial }}
            zg361_career_hc_schedule_{domain.key}_stage_01_effect = yes
            set_variable = {{ name = zg361_ch_runtime_applied value = 1 }}
            if = {{
                limit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
                zg361_career_hc_{domain.key}_run_authorized_ai_effect = yes
            }}
            else_if = {{
                limit = {{ root = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
                {player_start}
            }}
            debug_log = "ZG361CH: opened {domain.key.upper()} career/HC case"
        }}
    }}
}}'''


def render_authorized_ai_runner(domain: DomainSpec) -> str:
    calls: list[str] = []
    for mechanism_id in domain_mechanisms(domain):
        if mechanism_id in DUAL_COST_IDS:
            calls.append(
                f'''if = {{
        limit = {{
            government_has_flag = government_has_treasury
            root = {{
                government_has_flag = government_has_treasury
                treasury >= 5
                gold >= 5
            }}
        }}
        zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = 1 }}
    }}
    else = {{
        zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = 3 }}
    }}'''
            )
        else:
            calls.append(
                f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = 1 }}"
            )
    if NEXT_DOMAIN[domain.key] is None:
        tail = f'''if = {{
        limit = {{ has_variable = zg361_ch_runtime_applied var:zg361_ch_runtime_applied = 1 }}
        zg361_career_hc_finalize_{domain.key}_portfolio_effect = yes
    }}'''
    else:
        tail = f'''if = {{
        limit = {{ has_variable = zg361_ch_runtime_applied var:zg361_ch_runtime_applied = 1 }}
        root = {{ trigger_event = {{ id = zg361ch.{QUEUE_EVENTS[domain.key]} days = 1 }} }}
    }}'''
    calls_text = "\n".join(
        f"    {line}" for call in calls for line in call.splitlines()
    )
    tail_text = "\n".join(f"    {line}" for line in tail.splitlines())
    return f'''# Authorized second-AI-exception path: consume the same numbered
# receipts and consumers without opening any player business event.
zg361_career_hc_{domain.key}_run_authorized_ai_effect = {{
{calls_text}
{tail_text}
}}'''


def render_portfolio_finalizer(domain: DomainSpec) -> str:
    row = domain_vars(domain.key)
    scopes = event_scope_names(domain.key)
    final_state = len(domain.stages) + 1
    return f'''# Close the manager portfolio only against the last domain's frozen identity.
zg361_career_hc_finalize_{domain.key}_portfolio_effect = {{
    if = {{
        limit = {{
            exists = scope:{scopes["owner"]}
            exists = scope:{scopes["subject"]}
            exists = scope:{scopes["cycle"]}
            exists = scope:{scopes["case"]}
            var:{row["owner"]} = scope:{scopes["owner"]}
            var:{row["subject"]} = scope:{scopes["subject"]}
            var:{row["cycle"]} = scope:{scopes["cycle"]}
            var:{row["case"]} = scope:{scopes["case"]}
            var:{row["state"]} = {final_state}
            var:{row["active"]} = 0
        }}
        set_variable = {{ name = zg361_ch_portfolio_closed value = 1 }}
        set_variable = {{ name = zg361_ch_portfolio_final_owner value = var:{row["owner"]} }}
        set_variable = {{ name = zg361_ch_portfolio_final_subject value = var:{row["subject"]} }}
        set_variable = {{ name = zg361_ch_portfolio_final_cycle value = var:{row["cycle"]} }}
        set_variable = {{ name = zg361_ch_portfolio_final_case value = var:{row["case"]} }}
        set_variable = {{ name = zg361_ch_portfolio_final_state value = var:{row["state"]} }}
        var:{row["owner"]} = {{
            set_variable = {{ name = zg361_ch_manager_portfolio_active value = 0 }}
            set_variable = {{ name = zg361_ch_manager_portfolio_completed_cycle value = var:zg361_review_serial }}
        }}
        debug_log = "ZG361CH: manager career/HC portfolio closed after {domain.key.upper()}"
    }}
}}'''


def render_inactive_case_trigger(domain: str) -> str:
    return f'''trigger_if = {{
                    limit = {{ has_variable = zg361_case_{domain}_active }}
                    var:zg361_case_{domain}_active = 0
                }}
                trigger_else = {{ always = yes }}'''


def render_portfolio_adapter() -> str:
    inactive = "\n                ".join(
        render_inactive_case_trigger(domain) for domain in DOMAIN_ORDER
    )
    subject_limit = f'''zg361_is_reviewable_vassal_trigger = yes
                liege = root
                trigger_if = {{
                    limit = {{ has_variable = zg361_ch_portfolio_cycle }}
                    NOT = {{ var:zg361_ch_portfolio_cycle = root.var:zg361_review_serial }}
                }}
                trigger_else = {{ always = yes }}
                {inactive}'''
    return f'''# The only manager-scope Career/HC ABI for central wiring.  It selects one
# eligible direct official and opens D only; later domains are hidden D+1 edges.
zg361_career_hc_open_portfolio_effect = {{
    remove_variable = zg361_ch_portfolio_applied
    if = {{
        limit = {{
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            trigger_if = {{
                limit = {{ has_variable = zg361_ch_manager_portfolio_cycle }}
                NOT = {{ var:zg361_ch_manager_portfolio_cycle = var:zg361_review_serial }}
            }}
            trigger_else = {{ always = yes }}
            any_vassal = {{
                {subject_limit}
            }}
        }}
        ordered_vassal = {{
            limit = {{
                {subject_limit}
            }}
            order_by = stewardship
            position = 0
            zg361_career_hc_open_d_case_effect = yes
            if = {{
                limit = {{ has_variable = zg361_ch_runtime_applied var:zg361_ch_runtime_applied = 1 }}
                set_variable = {{ name = zg361_ch_portfolio_cycle value = root.var:zg361_review_serial }}
                set_variable = {{ name = zg361_ch_portfolio_closed value = 0 }}
                set_variable = {{ name = zg361_ch_portfolio_owner value = root }}
                set_variable = {{ name = zg361_ch_portfolio_subject value = this }}
                set_variable = {{ name = zg361_ch_portfolio_open_case value = var:zg361_case_d_case_serial }}
                root = {{
                    set_variable = {{ name = zg361_ch_manager_portfolio_cycle value = var:zg361_review_serial }}
                    set_variable = {{ name = zg361_ch_manager_portfolio_active value = 1 }}
                    set_variable = {{ name = zg361_ch_portfolio_applied value = 1 }}
                }}
            }}
        }}
    }}
}}'''


def render_transfer_vacancy_adapter() -> str:
    """Render the Career/HC-owned external vacancy and settlement ABI.

    A reviewed official is a landed direct vassal. CK3's court-position API
    rejects appointing that character in a different manager's court, so the
    adapter freezes the existing title/character and uses the vanilla landed
    office transfer primitive. Variables never substitute for its postcondition.
    """

    return '''# Career/HC owns the external transfer-vacancy ABI consumed by PP #190.
# Status: 1 prepared, 2 PP request accepted, 3 title/vassal transfer settled,
# 4 rejected/reclaimed. RED: 1 no vacancy, 2 duplicate, 3 stale identity,
# 4 native postcondition failed, 6 central lane still active (retry pending).
zg361_career_hc_prepare_transfer_vacancy_effect = {
    remove_variable = zg361_transfer_adapter_applied
    set_variable = { name = zg361_transfer_adapter_red_code value = 0 }
    if = {
        limit = {
            trigger_if = {
                limit = { has_variable = zg361_transfer_vacancy_active }
                var:zg361_transfer_vacancy_active = 1
            }
            trigger_else = { always = no }
        }
        if = {
            limit = {
                var:zg361_transfer_vacancy_owner = var:zg361_case_p_owner
                var:zg361_transfer_vacancy_subject = this
                var:zg361_transfer_vacancy_source_cycle = var:zg361_case_p_cycle_serial
                var:zg361_transfer_vacancy_source_case = var:zg361_case_p_case_serial
            }
            set_variable = { name = zg361_transfer_adapter_red_code value = 2 }
        }
        else = { set_variable = { name = zg361_transfer_adapter_red_code value = 3 } }
    }
    else = {
        set_variable = { name = zg361_transfer_hc_authorized value = 0 }
        set_variable = { name = zg361_transfer_hc_available value = 0 }
        set_variable = { name = zg361_transfer_hc_reserved value = 0 }
        set_variable = { name = zg361_transfer_hc_settled value = 0 }
        set_variable = { name = zg361_transfer_hc_reclaimed value = 0 }
        set_variable = { name = zg361_transfer_hc_partition value = 0 }
        set_variable = { name = zg361_transfer_hc_conserved value = 1 }
        set_variable = { name = zg361_transfer_vacancy_active value = 0 }
        set_variable = { name = zg361_transfer_vacancy_status value = 4 }
        remove_variable = zg361_transfer_vacancy_id
        remove_variable = zg361_transfer_vacancy_owner
        remove_variable = zg361_transfer_vacancy_subject
        remove_variable = zg361_transfer_vacancy_source_cycle
        remove_variable = zg361_transfer_vacancy_source_case
        remove_variable = zg361_transfer_vacancy_receiver
        remove_variable = zg361_transfer_vacancy_title
        remove_variable = zg361_transfer_vacancy_maturity_cycle
        remove_variable = zg361_transfer_vacancy_position_kind
        save_temporary_scope_as = zg361_transfer_prepare_subject
        var:zg361_case_p_owner = { save_temporary_scope_as = zg361_transfer_prepare_owner }
        primary_title = { save_temporary_scope_as = zg361_transfer_prepare_title }
        scope:zg361_transfer_prepare_owner = {
            ordered_vassal = {
                limit = {
                    zg361_is_celestial_liege_trigger = yes
                    NOT = { this = scope:zg361_transfer_prepare_subject }
                    primary_title.tier > scope:zg361_transfer_prepare_subject.primary_title.tier
                    vassal_count < vassal_limit
                    NOT = { is_at_war_with = scope:zg361_transfer_prepare_owner }
                    NOT = { is_at_war_with = scope:zg361_transfer_prepare_subject }
                    scope:zg361_transfer_prepare_subject = { NOT = { is_at_war_with = this } }
                }
                order_by = stewardship
                position = 0
                save_temporary_scope_as = zg361_transfer_prepare_receiver
            }
        }
        if = {
            limit = {
                exists = scope:zg361_transfer_prepare_owner
                exists = scope:zg361_transfer_prepare_subject
                exists = scope:zg361_transfer_prepare_receiver
                exists = scope:zg361_transfer_prepare_title
                var:zg361_case_p_owner = scope:zg361_transfer_prepare_owner
                var:zg361_case_p_subject = this
                var:zg361_case_p_state = 6
                var:zg361_case_p_active = 0
                var:zg361_ch_m114_consumed = 1
                var:zg361_ch_m114_route = 1
                liege = scope:zg361_transfer_prepare_owner
                primary_title = scope:zg361_transfer_prepare_title
                scope:zg361_transfer_prepare_title.holder = this
                scope:zg361_transfer_prepare_receiver = {
                    zg361_is_celestial_liege_trigger = yes
                    liege = scope:zg361_transfer_prepare_owner
                    primary_title.tier > scope:zg361_transfer_prepare_subject.primary_title.tier
                    vassal_count < vassal_limit
                    NOT = { is_at_war_with = scope:zg361_transfer_prepare_owner }
                    NOT = { is_at_war_with = scope:zg361_transfer_prepare_subject }
                }
            }
            set_variable = { name = zg361_transfer_vacancy_id value = { value = var:zg361_case_p_case_serial multiply = 1000 add = 114 } }
            set_variable = { name = zg361_transfer_vacancy_owner value = scope:zg361_transfer_prepare_owner }
            set_variable = { name = zg361_transfer_vacancy_subject value = this }
            set_variable = { name = zg361_transfer_vacancy_source_cycle value = var:zg361_case_p_cycle_serial }
            set_variable = { name = zg361_transfer_vacancy_source_case value = var:zg361_case_p_case_serial }
            set_variable = { name = zg361_transfer_vacancy_receiver value = scope:zg361_transfer_prepare_receiver }
            set_variable = { name = zg361_transfer_vacancy_title value = scope:zg361_transfer_prepare_title }
            set_variable = { name = zg361_transfer_vacancy_maturity_cycle value = { value = var:zg361_case_p_cycle_serial add = 1 } }
            set_variable = { name = zg361_transfer_vacancy_position_kind value = 1 }
            set_variable = { name = zg361_transfer_vacancy_active value = 1 }
            set_variable = { name = zg361_transfer_vacancy_status value = 1 }
            set_variable = { name = zg361_transfer_settlement_attempts value = 0 }
            set_variable = { name = zg361_transfer_hc_authorized value = 1 }
            set_variable = { name = zg361_transfer_hc_reserved value = 1 }
            set_variable = { name = zg361_transfer_hc_partition value = 1 }
            set_variable = { name = zg361_transfer_adapter_applied value = 1 }
        }
        else = { set_variable = { name = zg361_transfer_adapter_red_code value = 1 } }
    }
}

# PP #190 may request only the exact matured vacancy frozen by W prework.
zg361_career_hc_accept_pp_transfer_request_effect = {
    remove_variable = zg361_transfer_adapter_applied
    set_variable = { name = zg361_transfer_adapter_red_code value = 0 }
    if = {
        limit = {
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_request_pp_owner = var:zg361_case_w_owner
            var:zg361_transfer_request_pp_subject = this
            var:zg361_transfer_request_pp_cycle = var:zg361_case_w_cycle_serial
            var:zg361_transfer_request_pp_case = var:zg361_case_w_case_serial
            var:zg361_transfer_request_vacancy = var:zg361_pp_m190_vacancy_id_snapshot
        }
        set_variable = { name = zg361_transfer_adapter_red_code value = 2 }
    }
    else_if = {
        limit = {
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 1
            var:zg361_transfer_vacancy_owner = root
            var:zg361_transfer_vacancy_subject = this
            var:zg361_transfer_vacancy_id = var:zg361_pp_m190_vacancy_id_snapshot
            var:zg361_transfer_vacancy_receiver = var:zg361_pp_m190_receiving_manager
            var:zg361_transfer_vacancy_source_cycle = var:zg361_pp_w_transfer_source_cycle
            var:zg361_transfer_vacancy_source_case = var:zg361_pp_w_transfer_source_case
            var:zg361_transfer_vacancy_title = var:zg361_pp_w_transfer_vacancy_title
            var:zg361_transfer_vacancy_maturity_cycle = var:zg361_pp_w_transfer_maturity_cycle
            var:zg361_transfer_vacancy_position_kind = var:zg361_pp_w_transfer_position_kind
            var:zg361_transfer_vacancy_position_kind = 1
            primary_title = var:zg361_transfer_vacancy_title
            var:zg361_transfer_vacancy_title = { holder = prev }
            var:zg361_transfer_vacancy_maturity_cycle <= root.var:zg361_review_serial
            var:zg361_transfer_hc_authorized = 1
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_request_pp_owner value = var:zg361_case_w_owner }
        set_variable = { name = zg361_transfer_request_pp_subject value = this }
        set_variable = { name = zg361_transfer_request_pp_cycle value = var:zg361_case_w_cycle_serial }
        set_variable = { name = zg361_transfer_request_pp_case value = var:zg361_case_w_case_serial }
        set_variable = { name = zg361_transfer_request_vacancy value = var:zg361_pp_m190_vacancy_id_snapshot }
        set_variable = { name = zg361_transfer_request_receiver value = var:zg361_pp_m190_receiving_manager }
        set_variable = { name = zg361_transfer_request_receipt_owner value = var:zg361_case_w_owner }
        set_variable = { name = zg361_transfer_request_receipt_subject value = this }
        set_variable = { name = zg361_transfer_request_receipt_cycle value = var:zg361_case_w_cycle_serial }
        set_variable = { name = zg361_transfer_request_receipt_case value = var:zg361_case_w_case_serial }
        set_variable = { name = zg361_transfer_request_receipt_vacancy value = var:zg361_pp_m190_vacancy_id_snapshot }
        set_variable = { name = zg361_transfer_request_receipt_receiver value = var:zg361_pp_m190_receiving_manager }
        set_variable = { name = zg361_transfer_request_receipt_source_cycle value = var:zg361_transfer_vacancy_source_cycle }
        set_variable = { name = zg361_transfer_request_receipt_source_case value = var:zg361_transfer_vacancy_source_case }
        set_variable = { name = zg361_transfer_request_receipt_title value = var:zg361_transfer_vacancy_title }
        set_variable = { name = zg361_transfer_request_receipt_maturity_cycle value = var:zg361_transfer_vacancy_maturity_cycle }
        set_variable = { name = zg361_transfer_vacancy_status value = 2 }
        set_variable = { name = zg361_transfer_adapter_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_adapter_red_code value = 3 } }
}

# The D+30 PP audit calls this consumer. A live central lane is a strict
# external block, not a success: retry later without touching the HC book.
zg361_career_hc_settle_pp_transfer_effect = {
    remove_variable = zg361_transfer_adapter_applied
    set_variable = { name = zg361_transfer_adapter_red_code value = 0 }
    if = {
        limit = { var:zg361_transfer_vacancy_status = 3 }
        set_variable = { name = zg361_transfer_adapter_red_code value = 2 }
    }
    else_if = {
        limit = {
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_vacancy_owner = var:zg361_transfer_request_pp_owner
            var:zg361_transfer_vacancy_subject = this
            var:zg361_transfer_vacancy_id = var:zg361_transfer_request_vacancy
            var:zg361_transfer_vacancy_receiver = var:zg361_transfer_request_receiver
            var:zg361_transfer_request_pp_owner = var:zg361_transfer_request_receipt_owner
            var:zg361_transfer_request_pp_subject = var:zg361_transfer_request_receipt_subject
            var:zg361_transfer_request_pp_cycle = var:zg361_transfer_request_receipt_cycle
            var:zg361_transfer_request_pp_case = var:zg361_transfer_request_receipt_case
            var:zg361_transfer_request_vacancy = var:zg361_transfer_request_receipt_vacancy
            var:zg361_transfer_request_receiver = var:zg361_transfer_request_receipt_receiver
            var:zg361_transfer_vacancy_source_cycle = var:zg361_transfer_request_receipt_source_cycle
            var:zg361_transfer_vacancy_source_case = var:zg361_transfer_request_receipt_source_case
            var:zg361_transfer_vacancy_title = var:zg361_transfer_request_receipt_title
            var:zg361_transfer_vacancy_maturity_cycle = var:zg361_transfer_request_receipt_maturity_cycle
            var:zg361_transfer_vacancy_position_kind = 1
            var:zg361_transfer_hc_authorized = 1
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized
            var:zg361_transfer_hc_conserved = 1
        }
        if = {
            limit = {
                var:zg361_transfer_vacancy_owner = {
                    trigger_if = {
                        limit = { has_variable = zg361_p2c_active }
                        var:zg361_p2c_active = 0
                    }
                    trigger_else = { always = yes }
                }
            }
            if = {
                limit = {
                    liege = var:zg361_transfer_vacancy_owner
                    primary_title = var:zg361_transfer_vacancy_title
                    var:zg361_transfer_vacancy_title = { holder = prev }
                    var:zg361_transfer_vacancy_receiver = {
                        zg361_is_celestial_liege_trigger = yes
                        liege = root.var:zg361_transfer_vacancy_owner
                        primary_title.tier > root.primary_title.tier
                        vassal_count < vassal_limit
                        NOT = { is_at_war_with = root.var:zg361_transfer_vacancy_owner }
                        NOT = { is_at_war_with = root }
                    }
                    NOT = { is_at_war_with = var:zg361_transfer_vacancy_receiver }
                }
                save_temporary_scope_as = zg361_transfer_settle_subject
                var:zg361_transfer_vacancy_owner = { save_temporary_scope_as = zg361_transfer_settle_owner }
                var:zg361_transfer_vacancy_receiver = { save_temporary_scope_as = zg361_transfer_settle_receiver }
                var:zg361_transfer_vacancy_title = { save_temporary_scope_as = zg361_transfer_settle_title }
                scope:zg361_transfer_settle_owner = {
                    create_title_and_vassal_change = {
                        type = granted
                        save_scope_as = zg361_transfer_title_change
                        add_claim_on_loss = no
                    }
                    scope:zg361_transfer_settle_subject = {
                        change_liege = {
                            liege = scope:zg361_transfer_settle_receiver
                            change = scope:zg361_transfer_title_change
                        }
                    }
                    resolve_title_and_vassal_change = scope:zg361_transfer_title_change
                }
                if = {
                    limit = {
                        liege = scope:zg361_transfer_settle_receiver
                        primary_title = scope:zg361_transfer_settle_title
                        scope:zg361_transfer_settle_title.holder = this
                    }
                    set_variable = { name = zg361_transfer_vacancy_active value = 0 }
                    set_variable = { name = zg361_transfer_vacancy_status value = 3 }
                    change_variable = { name = zg361_transfer_hc_reserved add = -1 }
                    change_variable = { name = zg361_transfer_hc_settled add = 1 }
                    set_variable = { name = zg361_transfer_hc_partition value = var:zg361_transfer_hc_available }
                    change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reserved }
                    change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_settled }
                    change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reclaimed }
                    set_variable = { name = zg361_transfer_hc_conserved value = 0 }
                    if = { limit = { var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized } set_variable = { name = zg361_transfer_hc_conserved value = 1 } }
                    scope:zg361_transfer_settle_receiver = {
                        set_variable = { name = zg361_received_transfer_vacancy value = root.var:zg361_transfer_vacancy_id }
                        set_variable = { name = zg361_received_transfer_subject value = root }
                        set_variable = { name = zg361_received_transfer_title value = scope:zg361_transfer_settle_title }
                    }
                    scope:zg361_transfer_settle_owner = {
                        set_variable = { name = zg361_last_settled_transfer_vacancy value = root.var:zg361_transfer_vacancy_id }
                        set_variable = { name = zg361_last_settled_transfer_subject value = root }
                    }
                    set_variable = { name = zg361_transfer_adapter_applied value = 1 }
                }
                else = {
                    set_variable = { name = zg361_transfer_adapter_red_code value = 4 }
                    zg361_career_hc_reclaim_transfer_hc_effect = yes
                }
            }
            else = {
                set_variable = { name = zg361_transfer_adapter_red_code value = 1 }
                zg361_career_hc_reclaim_transfer_hc_effect = yes
            }
        }
        else = {
            set_variable = { name = zg361_transfer_adapter_red_code value = 6 }
            change_variable = { name = zg361_transfer_settlement_attempts add = 1 }
            trigger_event = { id = zg361ch.990 days = 30 }
        }
    }
    else = {
        set_variable = { name = zg361_transfer_adapter_red_code value = 3 }
    }
}

zg361_career_hc_reclaim_transfer_hc_effect = {
    if = {
        limit = {
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_vacancy_active value = 0 }
        set_variable = { name = zg361_transfer_vacancy_status value = 4 }
        change_variable = { name = zg361_transfer_hc_reserved add = -1 }
        change_variable = { name = zg361_transfer_hc_reclaimed add = 1 }
        set_variable = { name = zg361_transfer_hc_partition value = var:zg361_transfer_hc_available }
        change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reserved }
        change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_settled }
        change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reclaimed }
        set_variable = { name = zg361_transfer_hc_conserved value = 0 }
        if = { limit = { var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized } set_variable = { name = zg361_transfer_hc_conserved value = 1 } }
    }
}'''


def render_cl_transfer_adapter() -> str:
    """Render the strict Career/Learning consumer of a real transfer vacancy.

    The vacancy and its one-unit HC reserve remain owned by Career/HC.  CL may
    claim one matured P#114 vacancy, record acceptance/trial/release phases, and
    finally invoke the same vanilla title/vassal primitive without fabricating
    any PP#190 request fields.
    """

    return '''# CL #312/#314/#315/#319 consumer of the Career/HC vacancy ledger.
# consumer_kind: 1 PP, 2 CL.  cl_phase: 1 claimed, 2 accepted, 3 trial,
# 4 release authorized, 5 declined/withheld, 6 native settlement complete.
# RED: 1 live vacancy/receiver invalid, 2 exact duplicate, 3 stale identity,
# 4 native postcondition failed, 5 HC reserve invalid.
zg361_career_hc_claim_cl_transfer_vacancy_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            has_variable = zg361_transfer_vacancy_active
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 1
            var:zg361_transfer_vacancy_owner = $TICKET_OWNER$
            var:zg361_transfer_vacancy_subject = this
            var:zg361_transfer_vacancy_maturity_cycle <= $TICKET_CYCLE$
            liege = $TICKET_OWNER$
            primary_title = var:zg361_transfer_vacancy_title
            var:zg361_transfer_vacancy_title = { holder = prev }
            var:zg361_transfer_vacancy_receiver = {
                is_landed = yes
                NOT = { has_trait = gallivanter }
                zg361_is_celestial_liege_trigger = yes
                liege = root.var:zg361_transfer_vacancy_owner
                primary_title.tier > root.primary_title.tier
                vassal_count < vassal_limit
                NOT = { is_at_war_with = root.var:zg361_transfer_vacancy_owner }
                NOT = { is_at_war_with = root }
            }
            NOT = { is_at_war_with = var:zg361_transfer_vacancy_receiver }
            var:zg361_transfer_hc_authorized = 1
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_partition = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_consumer_kind value = 2 }
        set_variable = { name = zg361_transfer_vacancy_status value = 2 }
        set_variable = { name = zg361_transfer_cl_phase value = 1 }
        set_variable = { name = zg361_transfer_cl_owner value = $TICKET_OWNER$ }
        set_variable = { name = zg361_transfer_cl_subject value = this }
        set_variable = { name = zg361_transfer_cl_cycle value = $TICKET_CYCLE$ }
        set_variable = { name = zg361_transfer_cl_case value = $TICKET_CASE$ }
        set_variable = { name = zg361_transfer_cl_vacancy value = var:zg361_transfer_vacancy_id }
        set_variable = { name = zg361_transfer_cl_receiver value = var:zg361_transfer_vacancy_receiver }
        set_variable = { name = zg361_transfer_cl_title value = var:zg361_transfer_vacancy_title }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_phase = 1
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            has_variable = zg361_transfer_vacancy_active
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_hc_reserved = 1
            NOT = { var:zg361_transfer_hc_conserved = 1 }
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 5 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 1 } }
}

zg361_career_hc_accept_cl_transfer_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_phase = 1
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
            var:zg361_transfer_cl_vacancy = var:zg361_transfer_vacancy_id
            var:zg361_transfer_cl_receiver = var:zg361_transfer_vacancy_receiver
            var:zg361_transfer_cl_title = var:zg361_transfer_vacancy_title
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_cl_phase value = 2 }
        set_variable = { name = zg361_transfer_cl_accept_cycle value = $TICKET_CYCLE$ }
        set_variable = { name = zg361_transfer_cl_accept_case value = $TICKET_CASE$ }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_cl_phase = 2
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 3 } }
}

zg361_career_hc_decline_cl_transfer_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_cl_phase value = 5 }
        zg361_career_hc_reclaim_transfer_hc_effect = yes
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_status = 4
            var:zg361_transfer_cl_phase = 5
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 3 } }
}

zg361_career_hc_start_cl_transfer_trial_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_phase = 2
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_cl_phase value = 3 }
        set_variable = { name = zg361_transfer_cl_trial_cycle value = $TICKET_CYCLE$ }
        set_variable = { name = zg361_transfer_cl_trial_case value = $TICKET_CASE$ }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_cl_phase = 3
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 3 } }
}

zg361_career_hc_authorize_cl_transfer_release_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_phase = 3
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_conserved = 1
        }
        set_variable = { name = zg361_transfer_cl_phase value = 4 }
        set_variable = { name = zg361_transfer_cl_release_cycle value = $TICKET_CYCLE$ }
        set_variable = { name = zg361_transfer_cl_release_case value = $TICKET_CASE$ }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_cl_phase = 4
            var:zg361_transfer_cl_owner = $TICKET_OWNER$
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = $TICKET_CYCLE$
            var:zg361_transfer_cl_case = $TICKET_CASE$
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 3 } }
}

zg361_career_hc_settle_cl_transfer_effect = {
    remove_variable = zg361_transfer_cl_applied
    set_variable = { name = zg361_transfer_cl_red_code value = 0 }
    if = {
        limit = {
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_active = 1
            var:zg361_transfer_vacancy_status = 2
            var:zg361_transfer_cl_phase = 4
            var:zg361_transfer_cl_owner = var:zg361_cl_m319_object_owner
            var:zg361_transfer_cl_subject = this
            var:zg361_transfer_cl_cycle = var:zg361_cl_m319_object_cycle
            var:zg361_transfer_cl_case = var:zg361_cl_m319_object_case
            var:zg361_transfer_cl_vacancy = var:zg361_transfer_vacancy_id
            var:zg361_transfer_cl_receiver = var:zg361_transfer_vacancy_receiver
            var:zg361_transfer_cl_title = var:zg361_transfer_vacancy_title
            var:zg361_transfer_cl_accept_cycle = var:zg361_transfer_cl_cycle
            var:zg361_transfer_cl_accept_case = var:zg361_transfer_cl_case
            var:zg361_transfer_cl_trial_cycle = var:zg361_transfer_cl_cycle
            var:zg361_transfer_cl_trial_case = var:zg361_transfer_cl_case
            var:zg361_transfer_cl_release_cycle = var:zg361_transfer_cl_cycle
            var:zg361_transfer_cl_release_case = var:zg361_transfer_cl_case
            var:zg361_cl_m312_vacancy_id = var:zg361_transfer_cl_vacancy
            var:zg361_cl_m312_target_manager = var:zg361_transfer_cl_receiver
            var:zg361_cl_m312_vacancy_title = var:zg361_transfer_cl_title
            var:zg361_cl_m312_hc_reserved = 1
            var:zg361_cl_m314_vacancy_id = var:zg361_transfer_cl_vacancy
            var:zg361_cl_m314_target_manager = var:zg361_transfer_cl_receiver
            var:zg361_cl_m315_vacancy_id = var:zg361_transfer_cl_vacancy
            var:zg361_cl_m315_source_manager = var:zg361_transfer_cl_owner
            var:zg361_cl_m315_target_manager = var:zg361_transfer_cl_receiver
            var:zg361_cl_m319_vacancy_id = var:zg361_transfer_cl_vacancy
            var:zg361_cl_m319_target_manager = var:zg361_transfer_cl_receiver
            var:zg361_cl_m312_receipt_owner = var:zg361_transfer_cl_owner
            var:zg361_cl_m312_receipt_subject = this
            var:zg361_cl_m312_receipt_cycle = var:zg361_transfer_cl_cycle
            var:zg361_cl_m312_receipt_case = var:zg361_transfer_cl_case
            var:zg361_cl_m312_receipt_choice = 1
            var:zg361_cl_m314_receipt_owner = var:zg361_transfer_cl_owner
            var:zg361_cl_m314_receipt_subject = this
            var:zg361_cl_m314_receipt_cycle = var:zg361_transfer_cl_cycle
            var:zg361_cl_m314_receipt_case = var:zg361_transfer_cl_case
            var:zg361_cl_m314_receipt_choice = 1
            var:zg361_cl_m315_receipt_owner = var:zg361_transfer_cl_owner
            var:zg361_cl_m315_receipt_subject = this
            var:zg361_cl_m315_receipt_cycle = var:zg361_transfer_cl_cycle
            var:zg361_cl_m315_receipt_case = var:zg361_transfer_cl_case
            var:zg361_cl_m315_receipt_choice = 1
            var:zg361_cl_m319_receipt_owner = var:zg361_transfer_cl_owner
            var:zg361_cl_m319_receipt_subject = this
            var:zg361_cl_m319_receipt_cycle = var:zg361_transfer_cl_cycle
            var:zg361_cl_m319_receipt_case = var:zg361_transfer_cl_case
            var:zg361_cl_m319_receipt_choice = 1
            var:zg361_transfer_hc_authorized = 1
            var:zg361_transfer_hc_reserved = 1
            var:zg361_transfer_hc_partition = 1
            var:zg361_transfer_hc_conserved = 1
        }
        if = {
            limit = {
                liege = var:zg361_transfer_vacancy_owner
                primary_title = var:zg361_transfer_vacancy_title
                var:zg361_transfer_vacancy_title = { holder = prev }
                var:zg361_transfer_vacancy_receiver = {
                    is_landed = yes
                    NOT = { has_trait = gallivanter }
                    zg361_is_celestial_liege_trigger = yes
                    liege = root.var:zg361_transfer_vacancy_owner
                    primary_title.tier > root.primary_title.tier
                    vassal_count < vassal_limit
                    NOT = { is_at_war_with = root.var:zg361_transfer_vacancy_owner }
                    NOT = { is_at_war_with = root }
                }
                NOT = { is_at_war_with = var:zg361_transfer_vacancy_receiver }
            }
            save_temporary_scope_as = zg361_transfer_cl_settle_subject
            var:zg361_transfer_vacancy_owner = { save_temporary_scope_as = zg361_transfer_cl_settle_owner }
            var:zg361_transfer_vacancy_receiver = { save_temporary_scope_as = zg361_transfer_cl_settle_receiver }
            var:zg361_transfer_vacancy_title = { save_temporary_scope_as = zg361_transfer_cl_settle_title }
            scope:zg361_transfer_cl_settle_owner = {
                create_title_and_vassal_change = {
                    type = granted
                    save_scope_as = zg361_transfer_cl_title_change
                    add_claim_on_loss = no
                }
                scope:zg361_transfer_cl_settle_subject = {
                    change_liege = {
                        liege = scope:zg361_transfer_cl_settle_receiver
                        change = scope:zg361_transfer_cl_title_change
                    }
                }
                resolve_title_and_vassal_change = scope:zg361_transfer_cl_title_change
            }
            if = {
                limit = {
                    liege = scope:zg361_transfer_cl_settle_receiver
                    primary_title = scope:zg361_transfer_cl_settle_title
                    scope:zg361_transfer_cl_settle_title.holder = this
                }
                set_variable = { name = zg361_transfer_vacancy_active value = 0 }
                set_variable = { name = zg361_transfer_vacancy_status value = 3 }
                set_variable = { name = zg361_transfer_cl_phase value = 6 }
                change_variable = { name = zg361_transfer_hc_reserved add = -1 }
                change_variable = { name = zg361_transfer_hc_settled add = 1 }
                set_variable = { name = zg361_transfer_hc_partition value = var:zg361_transfer_hc_available }
                change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reserved }
                change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_settled }
                change_variable = { name = zg361_transfer_hc_partition add = var:zg361_transfer_hc_reclaimed }
                set_variable = { name = zg361_transfer_hc_conserved value = 0 }
                if = { limit = { var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized } set_variable = { name = zg361_transfer_hc_conserved value = 1 } }
                scope:zg361_transfer_cl_settle_receiver = {
                    set_variable = { name = zg361_received_transfer_vacancy value = root.var:zg361_transfer_vacancy_id }
                    set_variable = { name = zg361_received_transfer_subject value = root }
                    set_variable = { name = zg361_received_transfer_title value = scope:zg361_transfer_cl_settle_title }
                }
                scope:zg361_transfer_cl_settle_owner = {
                    set_variable = { name = zg361_last_settled_transfer_vacancy value = root.var:zg361_transfer_vacancy_id }
                    set_variable = { name = zg361_last_settled_transfer_subject value = root }
                }
                set_variable = { name = zg361_transfer_cl_applied value = 1 }
            }
            else = {
                set_variable = { name = zg361_transfer_cl_red_code value = 4 }
                zg361_career_hc_reclaim_transfer_hc_effect = yes
            }
        }
        else = {
            set_variable = { name = zg361_transfer_cl_red_code value = 1 }
            zg361_career_hc_reclaim_transfer_hc_effect = yes
        }
    }
    else_if = {
        limit = {
            trigger_if = {
                limit = { has_variable = zg361_transfer_consumer_kind }
                var:zg361_transfer_consumer_kind = 2
            }
            trigger_else = { always = no }
            var:zg361_transfer_vacancy_status = 3
            var:zg361_transfer_cl_phase = 6
            var:zg361_transfer_cl_subject = this
        }
        set_variable = { name = zg361_transfer_cl_red_code value = 2 }
        set_variable = { name = zg361_transfer_cl_applied value = 1 }
    }
    else = { set_variable = { name = zg361_transfer_cl_red_code value = 3 } }
}'''


def render_manager_entry(mechanism_id: int, domain: str, state: int) -> str:
    row = domain_vars(domain)
    q_subject = "\n            zg361_is_celestial_liege_trigger = yes" if domain == "q" else ""
    return f'''zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{
    remove_variable = zg361_ch_runtime_applied
    if = {{
        limit = {{
            root = {{ zg361_is_celestial_liege_trigger = yes }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root{q_subject}
            {kernel_guard(domain, state, owner="root")}
        }}
        zg361_career_hc_m{mechanism_id:03d}_core_effect = {{ ROUTE = $ROUTE$ }}
    }}
}}'''


def render_core(mechanism_id: int, domain: str, state: int) -> str:
    p = f"zg361_ch_m{mechanism_id:03d}"
    row = domain_vars(domain)
    cost_guard = ""
    cost_apply = ""
    if mechanism_id in DUAL_COST_IDS:
        cost_guard = f'''trigger_if = {{
                limit = {{
                    OR = {{
                        scope:zg361_ch_route = 1
                        scope:zg361_ch_route = 2
                    }}
                }}
                government_has_flag = government_has_treasury
                var:{row["owner"]} = {{
                    government_has_flag = government_has_treasury
                    treasury >= 5
                    gold >= 5
                }}
            }}
            trigger_else = {{ always = yes }}'''
        cost_apply = f'''if = {{
                limit = {{
                    OR = {{
                        scope:zg361_ch_route = 1
                        scope:zg361_ch_route = 2
                    }}
                }}
                {transaction_journal(mechanism_id, domain, state, "treasury")}
                if = {{
                    limit = {{
                        trigger_if = {{
                            limit = {{ has_variable = zg361_case_kernel_applied }}
                            var:zg361_case_kernel_applied = 1
                        }}
                        trigger_else = {{ always = no }}
                    }}
                    {transaction_journal(mechanism_id, domain, state, "gold")}
                }}
                if = {{
                    limit = {{
                        trigger_if = {{
                            limit = {{ has_variable = zg361_case_kernel_applied }}
                            var:zg361_case_kernel_applied = 1
                        }}
                        trigger_else = {{ always = no }}
                        var:{p}_treasury_status = 2
                        var:{p}_gold_status = 2
                    }}
                    var:{row["owner"]} = {{
                        remove_treasury = 5
                        remove_short_term_gold = 5
                    }}
                    add_treasury = 5
                    add_gold = 5
                    set_variable = {{ name = {p}_dual_payment_settled value = 1 }}
                }}
            }}'''
    return f'''# {mechanism_id:03d} {TITLE_OVERRIDE_CN.get(mechanism_id, MECHANISM_BEHAVIORS[mechanism_id].title_cn)}
zg361_career_hc_m{mechanism_id:03d}_core_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_ch_route value = $ROUTE$ }}
    remove_variable = zg361_ch_runtime_applied
    if = {{
        limit = {{
            OR = {{
                scope:zg361_ch_route = 1
                scope:zg361_ch_route = 2
                scope:zg361_ch_route = 3
            }}
            {kernel_guard(domain, state, owner=f"var:{row['owner']}")}
            has_variable = {p}_receipt_active
            var:{p}_receipt_active = 0
            {cost_guard}
        }}
        {record_operation(mechanism_id, domain, state)}
        if = {{
            limit = {{
                trigger_if = {{
                    limit = {{ has_variable = zg361_case_kernel_applied }}
                    var:zg361_case_kernel_applied = 1
                }}
                trigger_else = {{ always = no }}
            }}
            {cost_apply}
            set_variable = {{ name = {p}_receipt_active value = 1 }}
            set_variable = {{ name = {p}_route value = scope:zg361_ch_route }}
            set_variable = {{ name = {p}_value value = 0 }}
            if = {{
                limit = {{ scope:zg361_ch_route = 1 }}
                set_variable = {{ name = {p}_value value = 1 }}
            }}
            else_if = {{
                limit = {{ scope:zg361_ch_route = 2 }}
                set_variable = {{ name = {p}_value value = -1 }}
            }}
            else = {{
                set_variable = {{ name = {p}_deferred value = 1 }}
                set_variable = {{ name = {p}_due_cycle value = {{ value = var:{row["cycle"]} add = 1 }} }}
            }}
            zg361_career_hc_m{mechanism_id:03d}_consume_effect = yes
            set_variable = {{ name = zg361_ch_runtime_applied value = 1 }}
        }}
    }}
}}'''


def render_hc_move(mechanism_id: int) -> str:
    a = HC_DEST_A[mechanism_id]
    b = HC_DEST_B[mechanism_id]
    return f'''if = {{
                limit = {{ var:zg361_ch_m{mechanism_id:03d}_route = 1 }}
                change_variable = {{ name = zg361_ch_hc_available add = -1 }}
                change_variable = {{ name = zg361_ch_hc_{a} add = 1 }}
            }}
            else_if = {{
                limit = {{ var:zg361_ch_m{mechanism_id:03d}_route = 2 }}
                change_variable = {{ name = zg361_ch_hc_available add = -1 }}
                change_variable = {{ name = zg361_ch_hc_{b} add = 1 }}
            }}
            set_variable = {{ name = zg361_ch_hc_partition value = var:zg361_ch_hc_available }}
            change_variable = {{ name = zg361_ch_hc_partition add = var:zg361_ch_hc_reserved }}
            change_variable = {{ name = zg361_ch_hc_partition add = var:zg361_ch_hc_occupied }}
            change_variable = {{ name = zg361_ch_hc_partition add = var:zg361_ch_hc_frozen }}
            change_variable = {{ name = zg361_ch_hc_partition add = var:zg361_ch_hc_reclaimed }}
            set_variable = {{ name = zg361_ch_hc_conserved value = 0 }}
            if = {{
                limit = {{ var:zg361_ch_hc_partition = var:zg361_ch_hc_authorized }}
                set_variable = {{ name = zg361_ch_hc_conserved value = 1 }}
            }}'''


def q_object_prefix(mechanism_id: int, kind: str) -> str:
    return f"zg361_ch_m{mechanism_id:03d}_{kind.replace('-', '_')}_object"


def render_q_five_tuple_object(
    mechanism_id: int,
    kind: str,
    state: int,
    ordinal: int,
) -> str:
    """Render one save-stable typed Q object bound to the frozen case."""

    prefix = q_object_prefix(mechanism_id, kind)
    if kind == "candidate" and mechanism_id != 121:
        person = "var:zg361_ch_q_named_successor_candidate"
    else:
        person = "this"
    role_links = ""
    if kind == "succession":
        role_links = f'''
            set_variable = {{ name = {prefix}_incumbent value = this }}
            set_variable = {{ name = {prefix}_candidate value = var:zg361_ch_q_named_successor_candidate }}'''
    elif kind == "backfill":
        role_links = f'''
            set_variable = {{ name = {prefix}_vacancy_id value = var:{q_object_prefix(124, "vacancy")}_id }}
            set_variable = {{ name = {prefix}_hc_slot_id value = var:{q_object_prefix(124, "hc-slot")}_id }}'''
    return f'''set_variable = {{
                name = {prefix}_id
                value = {{
                    value = var:zg361_case_q_case_serial
                    multiply = 1000
                    add = {mechanism_id * 10 + ordinal}
                }}
            }}
            set_variable = {{ name = {prefix}_owner value = var:zg361_case_q_owner }}
            set_variable = {{ name = {prefix}_subject value = {person} }}
            set_variable = {{ name = {prefix}_cycle value = var:zg361_case_q_cycle_serial }}
            set_variable = {{ name = {prefix}_case value = var:zg361_case_q_case_serial }}
            set_variable = {{ name = {prefix}_state value = {state} }}
            set_variable = {{ name = {prefix}_revision value = var:zg361_case_q_revision }}
            set_variable = {{ name = {prefix}_route value = var:zg361_ch_m{mechanism_id:03d}_route }}
            set_variable = {{ name = {prefix}_active value = 1 }}{role_links}
            change_variable = {{ name = zg361_ch_m{mechanism_id:03d}_business_object_count add = 1 }}'''


def render_q_object_bundle(mechanism_id: int, state: int) -> str:
    return "\n            ".join(
        render_q_five_tuple_object(mechanism_id, kind.value, state, ordinal)
        for ordinal, kind in enumerate(SEMANTIC_SPECS[mechanism_id].object_kinds, start=1)
    )


def render_q_hc_conservation() -> str:
    return '''set_variable = { name = zg361_ch_q_manager_hc_partition value = var:zg361_ch_q_manager_hc_available }
            change_variable = { name = zg361_ch_q_manager_hc_partition add = var:zg361_ch_q_manager_hc_reserved }
            change_variable = { name = zg361_ch_q_manager_hc_partition add = var:zg361_ch_q_manager_hc_occupied }
            change_variable = { name = zg361_ch_q_manager_hc_partition add = var:zg361_ch_q_manager_hc_frozen }
            change_variable = { name = zg361_ch_q_manager_hc_partition add = var:zg361_ch_q_manager_hc_reclaimed }
            set_variable = { name = zg361_ch_q_manager_hc_conserved value = 0 }
            if = {
                limit = { var:zg361_ch_q_manager_hc_partition = var:zg361_ch_q_manager_hc_authorized }
                set_variable = { name = zg361_ch_q_manager_hc_conserved value = 1 }
            }'''


def render_q_hc_move(mechanism_id: int, destination: str, units: int) -> str:
    p = f"zg361_ch_m{mechanism_id:03d}_business"
    return f'''if = {{
                limit = {{ var:zg361_ch_q_manager_hc_available >= {units} }}
                change_variable = {{ name = zg361_ch_q_manager_hc_available add = -{units} }}
                change_variable = {{ name = zg361_ch_q_manager_hc_{destination} add = {units} }}
                set_variable = {{ name = {p}_capacity_applied value = 1 }}
            }}
            else = {{
                set_variable = {{ name = {p}_capacity_applied value = 0 }}
                set_variable = {{ name = {p}_debt value = 1 }}
            }}
            {render_q_hc_conservation()}'''


def render_q_crisis_conservation() -> str:
    return '''set_variable = { name = zg361_ch_q_crisis_hours_partition value = var:zg361_ch_q_crisis_hours_available }
            change_variable = { name = zg361_ch_q_crisis_hours_partition add = var:zg361_ch_q_crisis_hours_delegated }
            change_variable = { name = zg361_ch_q_crisis_hours_partition add = var:zg361_ch_q_crisis_hours_manager }
            set_variable = { name = zg361_ch_q_crisis_hours_conserved value = 0 }
            if = {
                limit = { var:zg361_ch_q_crisis_hours_partition = var:zg361_ch_q_crisis_hours_authorized }
                set_variable = { name = zg361_ch_q_crisis_hours_conserved value = 1 }
            }'''


def render_q_route_payload(mechanism_id: int, state: int, route: int) -> str:
    """Concrete A/B transition for one authoritative manager mechanism."""

    objects = render_q_object_bundle(mechanism_id, state)
    p = f"zg361_ch_m{mechanism_id:03d}_business"
    capacity_precondition = ""
    capacity_failure_conservation = ""
    if mechanism_id == 121:
        destination, units, team_size = (
            ("reserved", 1, 3) if route == 1 else ("occupied", 3, 8)
        )
        capacity_precondition = f"var:zg361_ch_q_manager_hc_available >= {units}"
        capacity_failure_conservation = render_q_hc_conservation()
        business = f'''{render_q_hc_move(mechanism_id, destination, units)}
            set_variable = {{ name = zg361_ch_manager_trial_team_size value = {team_size} }}
            set_variable = {{ name = zg361_ch_manager_trial_authority_state value = {route} }}'''
    elif mechanism_id == 122:
        hard, people, values, total = (
            (70, 70, 70, 70) if route == 1 else (90, 35, 20, 53)
        )
        business = f'''set_variable = {{ name = zg361_ch_manager_score_hard value = {hard} }}
            set_variable = {{ name = zg361_ch_manager_score_people value = {people} }}
            set_variable = {{ name = zg361_ch_manager_score_values value = {values} }}
            set_variable = {{ name = zg361_ch_manager_score_total value = {total} }}
            set_variable = {{ name = zg361_ch_manager_score_weight_total value = 100 }}'''
    elif mechanism_id == 123:
        factors, sample, credibility = (6, 3, 100) if route == 1 else (1, 1, 25)
        business = f'''set_variable = {{ name = zg361_ch_subordinate_survey_factors value = {factors} }}
            set_variable = {{ name = zg361_ch_subordinate_survey_sample value = {sample} }}
            set_variable = {{ name = zg361_ch_subordinate_survey_credibility value = {credibility} }}
            set_variable = {{ name = zg361_ch_subordinate_survey_respondent value = var:zg361_ch_q_named_survey_respondent }}'''
    elif mechanism_id == 124:
        destination = "reserved" if route == 1 else "frozen"
        accepted = 1 if route == 1 else 0
        risk = 0 if route == 1 else 1
        capacity_precondition = "var:zg361_ch_q_manager_hc_available >= 1"
        capacity_failure_conservation = render_q_hc_conservation()
        business = f'''{render_q_hc_move(mechanism_id, destination, 1)}
            set_variable = {{ name = zg361_ch_successor_candidate value = var:zg361_ch_q_named_successor_candidate }}
            set_variable = {{ name = zg361_ch_successor_incumbent value = this }}
            set_variable = {{ name = zg361_ch_successor_accepted value = {accepted} }}
            set_variable = {{ name = zg361_ch_manager_promotion_released value = 1 }}
            set_variable = {{ name = zg361_ch_manager_promotion_continuity_risk value = {risk} }}
            set_variable = {{ name = zg361_ch_backfill_owner value = var:zg361_case_q_owner }}'''
    elif mechanism_id == 125:
        manager_hours, delegated_hours = (40, 60) if route == 1 else (100, 0)
        capacity_precondition = "var:zg361_ch_q_crisis_hours_available >= 100"
        capacity_failure_conservation = render_q_crisis_conservation()
        business = f'''if = {{
                limit = {{ var:zg361_ch_q_crisis_hours_available >= 100 }}
                change_variable = {{ name = zg361_ch_q_crisis_hours_available add = -100 }}
                change_variable = {{ name = zg361_ch_q_crisis_hours_manager add = {manager_hours} }}
                change_variable = {{ name = zg361_ch_q_crisis_hours_delegated add = {delegated_hours} }}
                set_variable = {{ name = {p}_capacity_applied value = 1 }}
            }}
            else = {{
                set_variable = {{ name = {p}_capacity_applied value = 0 }}
                set_variable = {{ name = {p}_debt value = 1 }}
            }}
            set_variable = {{ name = zg361_ch_crisis_hours_budget value = 100 }}
            set_variable = {{ name = zg361_ch_crisis_manager_hours value = {manager_hours} }}
            set_variable = {{ name = zg361_ch_crisis_delegated_hours value = {delegated_hours} }}
            set_variable = {{ name = zg361_ch_successor_evidence value = {1 if route == 1 else 0} }}
            {render_q_crisis_conservation()}'''
    elif mechanism_id == 126:
        quadrant, action = (1, 1) if route == 1 else (2, 2)
        business = f'''set_variable = {{ name = zg361_ch_values_quadrant value = {quadrant} }}
            set_variable = {{ name = zg361_ch_values_quadrant_action value = {action} }}
            set_variable = {{ name = zg361_ch_values_quadrant_evidence_frozen value = 1 }}'''
    elif mechanism_id == 127:
        if route == 1:
            capacity_precondition = "var:zg361_ch_q_manager_hc_available >= 1"
            capacity_failure_conservation = render_q_hc_conservation()
            capacity = render_q_hc_move(mechanism_id, "occupied", 1)
            layered = 1
        else:
            capacity = f'''set_variable = {{ name = {p}_capacity_applied value = 0 }}
            {render_q_hc_conservation()}'''
            layered = 0
        business = f'''{capacity}
            set_variable = {{ name = zg361_ch_span_direct_reports value = 11 }}
            set_variable = {{ name = zg361_ch_span_frozen value = 8 }}
            set_variable = {{ name = zg361_ch_span_excess value = 3 }}
            set_variable = {{ name = zg361_ch_span_layer_inserted value = {layered} }}'''
    elif mechanism_id == 128:
        policy = 1 if route == 1 else 2
        business = f'''set_variable = {{ name = zg361_ch_climate_pressure value = 70 }}
            set_variable = {{ name = zg361_ch_climate_collaboration value = 55 }}
            set_variable = {{ name = zg361_ch_climate_risk_reporting value = 45 }}
            set_variable = {{ name = zg361_ch_climate_peer_credibility value = 60 }}
            set_variable = {{ name = zg361_ch_climate_regrettable_attrition value = 20 }}
            set_variable = {{ name = zg361_ch_next_cycle_quota_policy value = {policy} }}
            set_variable = {{ name = zg361_ch_next_cycle_quota_policy_effective_cycle value = {{ value = var:zg361_case_q_cycle_serial add = 1 }} }}
            set_variable = {{ name = zg361_ch_current_cycle_quota_policy_unchanged value = 1 }}'''
    else:
        raise ValueError(f"Q authority does not own mechanism {mechanism_id}")
    debt = (
        f"\n            set_variable = {{ name = {p}_debt value = 1 }}"
        if route == 2
        else ""
    )
    payload = f'''{objects}
            {business}'''
    if capacity_precondition:
        payload = f'''if = {{
                limit = {{ {capacity_precondition} }}
                {payload}
            }}
            else = {{
                set_variable = {{ name = {p}_capacity_applied value = 0 }}
                set_variable = {{ name = {p}_debt value = 1 }}
                set_variable = {{ name = {p}_object_count value = 0 }}
                {capacity_failure_conservation}
            }}'''
    return f'''{payload}{debt}'''


def render_q_business_consumer(mechanism_id: int, state: int) -> str:
    """Render the authoritative post-receipt Q object transition."""

    p = f"zg361_ch_m{mechanism_id:03d}"
    return f'''# Q{mechanism_id:03d} authoritative typed-object consumer; manager-governance is adapter-only.
{SEMANTIC_SPECS[mechanism_id].consumer_key} = {{
    remove_variable = zg361_ch_q_business_applied
    if = {{
        limit = {{
            {kernel_guard("q", state, owner="var:zg361_case_q_owner")}
            var:{p}_receipt_active = 1
            var:{p}_consumed = 1
            var:{p}_business_consumed = 0
            var:{p}_receipt_owner = var:zg361_case_q_owner
            var:{p}_receipt_subject = this
            var:{p}_receipt_cycle = var:zg361_case_q_cycle_serial
            var:{p}_receipt_case = var:zg361_case_q_case_serial
            var:{p}_receipt_state = {state}
        }}
        set_variable = {{ name = {p}_business_consumed value = 1 }}
        set_variable = {{ name = {p}_business_owner value = var:zg361_case_q_owner }}
        set_variable = {{ name = {p}_business_subject value = this }}
        set_variable = {{ name = {p}_business_cycle value = var:zg361_case_q_cycle_serial }}
        set_variable = {{ name = {p}_business_case value = var:zg361_case_q_case_serial }}
        set_variable = {{ name = {p}_business_state value = {state} }}
        set_variable = {{ name = {p}_business_revision value = var:zg361_case_q_revision }}
        if = {{
            limit = {{ var:{p}_route = 1 }}
            {render_q_route_payload(mechanism_id, state, 1)}
        }}
        else_if = {{
            limit = {{ var:{p}_route = 2 }}
            {render_q_route_payload(mechanism_id, state, 2)}
        }}
        else = {{
            set_variable = {{ name = {p}_business_deferred value = 1 }}
            set_variable = {{ name = {p}_business_debt value = 1 }}
            set_variable = {{ name = {p}_business_object_count value = 0 }}
        }}
        set_variable = {{ name = zg361_ch_q_business_applied value = 1 }}
        debug_log = "ZG361CH: authoritative Q business consumer {mechanism_id:03d} committed"
    }}
}}'''


def render_consumer(mechanism_id: int, domain: str, state: int) -> str:
    p = f"zg361_ch_m{mechanism_id:03d}"
    hc = render_hc_move(mechanism_id) if domain == "n" else ""
    semantic = special_payload(mechanism_id)
    if mechanism_id == 23:
        semantic_projection = semantic
    elif mechanism_id == 116:
        semantic_projection = f'''if = {{
            limit = {{ NOT = {{ var:{p}_route = 3 }} }}
            {semantic}
        }}
        else = {{
            # A timed defer still needs a bounded release clock; it does not
            # consume the single evidence-backed sixty-day extension.
            set_variable = {{ name = zg361_ch_release_days value = 90 }}
            set_variable = {{ name = zg361_ch_release_extension_used value = 0 }}
        }}'''
    else:
        semantic_projection = f'''if = {{
            limit = {{ NOT = {{ var:{p}_route = 3 }} }}
            {semantic}
        }}'''
    business_hook = (
        f"{SEMANTIC_SPECS[mechanism_id].consumer_key} = yes"
        if mechanism_id in Q_AUTHORITY_IDS
        else ""
    )
    return f'''zg361_career_hc_m{mechanism_id:03d}_consume_effect = {{
    if = {{
        limit = {{
            {kernel_guard(domain, state, owner=f"var:zg361_case_{domain}_owner")}
            var:{p}_receipt_active = 1
            var:{p}_consumed = 0
            has_variable = {p}_value
        }}
        set_variable = {{ name = {p}_consumed value = 1 }}
        change_variable = {{ name = zg361_ch_{domain}_completed add = 1 }}
        if = {{
            limit = {{ var:{p}_value > 0 }}
            change_variable = {{ name = zg361_ch_{domain}_favorable add = 1 }}
            change_variable = {{ name = zg361_ch_{domain}_available add = -1 }}
            change_variable = {{ name = zg361_ch_{domain}_used add = 1 }}
        }}
        else_if = {{
            limit = {{ var:{p}_value < 0 }}
            change_variable = {{ name = zg361_ch_{domain}_extractive add = 1 }}
            change_variable = {{ name = zg361_ch_{domain}_available add = -1 }}
            change_variable = {{ name = zg361_ch_{domain}_used add = 1 }}
        }}
        else = {{ change_variable = {{ name = zg361_ch_{domain}_debt add = 1 }} }}
        {semantic_projection}
        {hc}
        {business_hook}
        set_variable = {{ name = zg361_ch_{domain}_capacity_partition value = var:zg361_ch_{domain}_available }}
        change_variable = {{ name = zg361_ch_{domain}_capacity_partition add = var:zg361_ch_{domain}_used }}
        set_variable = {{ name = zg361_ch_{domain}_conserved value = 0 }}
        if = {{
            limit = {{ var:zg361_ch_{domain}_capacity_partition = var:zg361_ch_{domain}_authorized }}
            set_variable = {{ name = zg361_ch_{domain}_conserved value = 1 }}
        }}
        zg361_career_hc_{domain}_try_advance_{state:02d}_effect = yes
    }}
}}'''


def render_schedule(domain: DomainSpec, state: int, days: int, event_id: int) -> str:
    row = domain_vars(domain.key)
    # P stage 3 is the release clock: route A is 90 days, the single evidenced
    # extension is 150.  Both branches get separate exact event tickets.
    dynamic_p = domain.key == "p" and state == 3
    calls = []
    variants = ((90, "a"), (150, "b")) if dynamic_p else ((days, "x"),)
    for actual_days, suffix in variants:
        condition = ""
        if dynamic_p:
            expected = 90 if actual_days == 90 else 150
            condition = f"var:zg361_ch_release_days = {expected}"
        dl = f"zg361_ch_{domain.key}_s{state}_{suffix}_deadline"
        call = f'''zg361_case_kernel_schedule_deadline_effect = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                DEADLINE_OWNER_VAR = {dl}_owner
                DEADLINE_SUBJECT_VAR = {dl}_subject
                DEADLINE_CYCLE_VAR = {dl}_cycle
                DEADLINE_CASE_VAR = {dl}_case
                DEADLINE_STATE_VAR = {dl}_state
                DEADLINE_DAYS_VAR = {dl}_days
                DEADLINE_PENDING_VAR = {dl}_pending
                DEADLINE_EXPIRED_VAR = {dl}_expired
                TICKET_OWNER = var:{row["owner"]}
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:{row["cycle"]}
                TICKET_CASE = var:{row["case"]}
                TICKET_STATE = {state}
                DAYS = {actual_days}
                EVENT = zg361ch.{event_id + (1 if dynamic_p and suffix == "b" else 0)}
            }}'''
        if condition:
            call = f"if = {{\n            limit = {{ {condition} }}\n            {call}\n        }}"
        calls.append(call)
    return f'''zg361_career_hc_schedule_{domain.key}_stage_{state:02d}_effect = {{
    {chr(10).join(calls)}
}}'''


def render_barrier(domain: DomainSpec, state: int, stage_ids: tuple[int, ...]) -> str:
    row = domain_vars(domain.key)
    required = "\n            ".join(
        f"var:zg361_ch_m{mechanism_id:03d}_consumed = 1" for mechanism_id in stage_ids
    )
    final = state == len(domain.stages)
    after = (
        f"zg361_career_hc_resolve_{domain.key}_outcome_effect = yes"
        if final
        else f"zg361_career_hc_schedule_{domain.key}_stage_{state + 1:02d}_effect = yes"
    )
    return f'''zg361_career_hc_{domain.key}_try_advance_{state:02d}_effect = {{
    if = {{
        limit = {{
            {kernel_guard(domain.key, state, owner=f"var:{row['owner']}")}
            {required}
        }}
        zg361_case_{domain.key}_advance_{state:02d}_effect = {{
            TICKET_OWNER = var:{row["owner"]}
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{row["cycle"]}
            TICKET_CASE = var:{row["case"]}
        }}
        if = {{
            limit = {{
                trigger_if = {{
                    limit = {{ has_variable = zg361_case_kernel_applied }}
                    var:zg361_case_kernel_applied = 1
                }}
                trigger_else = {{ always = no }}
            }}
            {after}
        }}
    }}
}}'''


def render_timeout(domain: DomainSpec, state: int, stage_ids: tuple[int, ...]) -> str:
    calls = "\n    ".join(
        f"zg361_career_hc_m{mechanism_id:03d}_core_effect = {{ ROUTE = 3 }}"
        for mechanism_id in stage_ids
    )
    return f'''zg361_career_hc_{domain.key}_timeout_stage_{state:02d}_effect = {{
    {calls}
    debug_log = "ZG361CH: exact {domain.key.upper()} stage {state} deadline consumed"
}}'''


def render_outcome(domain: DomainSpec, completion_event: int) -> str:
    row = domain_vars(domain.key)
    return f'''zg361_career_hc_resolve_{domain.key}_outcome_effect = {{
    if = {{
        limit = {{
            var:zg361_ch_{domain.key}_completed = var:zg361_ch_{domain.key}_authorized
            var:zg361_ch_{domain.key}_conserved = 1
        }}
        if = {{
            limit = {{ var:zg361_ch_{domain.key}_favorable > var:zg361_ch_{domain.key}_extractive }}
            set_variable = {{ name = zg361_ch_{domain.key}_outcome value = 1 }}
            add_prestige = 50
            var:{row["owner"]} = {{ add_prestige = 25 }}
        }}
        else_if = {{
            limit = {{ var:zg361_ch_{domain.key}_extractive > var:zg361_ch_{domain.key}_favorable }}
            set_variable = {{ name = zg361_ch_{domain.key}_outcome value = -1 }}
            add_stress = minor_stress_gain
            var:{row["owner"]} = {{ add_prestige = {{ value = 0 subtract = 25 }} }}
        }}
        else = {{
            set_variable = {{ name = zg361_ch_{domain.key}_outcome value = 0 }}
            add_prestige = 10
        }}
        set_variable = {{ name = zg361_ch_{domain.key}_visible_receipt_revision value = var:{row["revision"]} }}
        if = {{
            limit = {{ var:{row["owner"]} = {{ is_ai = no }} }}
            var:{row["owner"]} = {{ trigger_event = {{ id = zg361ch.{completion_event} days = 1 }} }}
        }}
        if = {{
            limit = {{ is_ai = no }}
            trigger_event = {{ id = zg361ch.{completion_event} days = 1 }}
        }}
        debug_log = "ZG361CH: completed {domain.key.upper()} career/HC case"
    }}
}}'''


def render_deadline_event(domain: DomainSpec, state: int, event_id: int, *, suffix: str = "x") -> str:
    row = domain_vars(domain.key)
    dl = f"zg361_ch_{domain.key}_s{state}_{suffix}_deadline"
    return f'''zg361ch.{event_id} = {{
    type = character_event
    hidden = yes
    immediate = {{
        zg361_case_kernel_expire_deadline_effect = {{
            OWNER_VAR = {row["owner"]}
            SUBJECT_VAR = {row["subject"]}
            CYCLE_VAR = {row["cycle"]}
            CASE_VAR = {row["case"]}
            STATE_VAR = {row["state"]}
            ACTIVE_VAR = {row["active"]}
            REVISION_VAR = {row["revision"]}
            TIMELINE_VAR = {row["timeline"]}
            FEEDBACK_VAR = {row["feedback"]}
            DEADLINE_OWNER_VAR = {dl}_owner
            DEADLINE_SUBJECT_VAR = {dl}_subject
            DEADLINE_CYCLE_VAR = {dl}_cycle
            DEADLINE_CASE_VAR = {dl}_case
            DEADLINE_STATE_VAR = {dl}_state
            DEADLINE_PENDING_VAR = {dl}_pending
            DEADLINE_EXPIRED_VAR = {dl}_expired
        }}
        if = {{
            limit = {{
                trigger_if = {{
                    limit = {{ has_variable = zg361_case_kernel_applied }}
                    var:zg361_case_kernel_applied = 1
                }}
                trigger_else = {{ always = no }}
            }}
            zg361_career_hc_{domain.key}_timeout_stage_{state:02d}_effect = yes
        }}
    }}
}}'''


def render_completion_event(domain: DomainSpec, event_id: int) -> str:
    return f'''zg361ch.{event_id} = {{
    type = character_event
    theme = vassal
    title = zg361ch.{event_id}.t
    desc = zg361ch.{event_id}.desc
    trigger = {{ is_ai = no }}
    option = {{ name = zg361ch.{event_id}.a }}
}}'''


def render_business_event_guard(mechanism_id: int, domain: str, state: int) -> str:
    row = domain_vars(domain)
    scopes = event_scope_names(domain)
    return f'''is_ai = no
        exists = scope:{scopes["owner"]}
        exists = scope:{scopes["subject"]}
        exists = scope:{scopes["cycle"]}
        exists = scope:{scopes["case"]}
        this = scope:{scopes["owner"]}
        zg361_is_celestial_liege_trigger = yes
        scope:{scopes["subject"]} = {{
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            zg361_case_kernel_full_guard_trigger = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                EXPECTED_OWNER = scope:{scopes["owner"]}
                EXPECTED_SUBJECT = scope:{scopes["subject"]}
                EXPECTED_CYCLE = scope:{scopes["cycle"]}
                EXPECTED_CASE = scope:{scopes["case"]}
                EXPECTED_STATE = {state}
            }}
        }}'''


def render_business_option(
    mechanism_id: int,
    domain: DomainSpec,
    route: int,
    next_mechanism: int | None,
) -> str:
    scopes = event_scope_names(domain.key)
    letter = "abc"[route - 1]
    option_trigger = ""
    if mechanism_id in DUAL_COST_IDS and route in (1, 2):
        option_trigger = f'''    trigger = {{
        government_has_flag = government_has_treasury
        treasury >= 5
        gold >= 5
        scope:{scopes["subject"]} = {{ government_has_flag = government_has_treasury }}
    }}
'''
    expected_successor = next_domain_mechanism(domain, mechanism_id)
    if next_mechanism != expected_successor:
        raise ValueError(f"{mechanism_id}: player successor drifted")
    continuation = render_subject_successor(domain, mechanism_id)
    return f'''option = {{
    name = zg361ch.m{mechanism_id:03d}.{letter}
{option_trigger}    scope:{scopes["subject"]} = {{
        zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = {route} }}
    }}
    if = {{
        limit = {{
            scope:{scopes["subject"]} = {{
                has_variable = zg361_ch_runtime_applied
                var:zg361_ch_runtime_applied = 1
            }}
        }}
        scope:{scopes["subject"]} = {{
            {continuation}
        }}
    }}
}}'''


def render_batch_choice_option(route: int) -> str:
    scopes = event_scope_names("d")
    letter = "abc"[route - 1]
    return f'''option = {{
    name = zg361ch.{BATCH_CHOICE_EVENT}.{letter}
    scope:{scopes["subject"]} = {{
        set_variable = {{ name = zg361_ch_player_batch_route value = {route} }}
        zg361_career_hc_m019_background_apply_effect = yes
    }}
}}'''


def render_batch_choice_event() -> str:
    scopes = event_scope_names("d")
    options = "\n".join(render_batch_choice_option(route) for route in (1, 2, 3))
    return f'''# One player portfolio choice replaces 22 low-risk D+1 cards.
zg361ch.{BATCH_CHOICE_EVENT} = {{
    type = character_event
    theme = stewardship
    title = zg361ch.{BATCH_CHOICE_EVENT}.t
    desc = zg361ch.{BATCH_CHOICE_EVENT}.desc
    trigger = {{
        {render_business_event_guard(19, "d", STAGE_BY_ID[19])}
    }}
    {options}
    option = {{
        name = zg361ch.{BATCH_CHOICE_EVENT}.d
        scope:{scopes["subject"]} = {{ remove_variable = zg361_ch_player_batch_route }}
        trigger_event = {{ id = zg361ch.19 days = 1 }}
    }}
}}'''


def render_business_event(
    mechanism_id: int,
    domain: DomainSpec,
    next_mechanism: int | None,
) -> str:
    state = STAGE_BY_ID[mechanism_id]
    options = "\n".join(
        render_business_option(mechanism_id, domain, route, next_mechanism)
        for route in (1, 2, 3)
    )
    return f'''# Player manager business window #{mechanism_id:03d}; its only successor is D+1.
zg361ch.{mechanism_id} = {{
    type = character_event
    theme = stewardship
    title = zg361ch.m{mechanism_id:03d}.name
    desc = zg361ch.m{mechanism_id:03d}.desc
    trigger = {{
        {render_business_event_guard(mechanism_id, domain.key, state)}
    }}
    {options}
}}'''


def render_queue_event(domain: DomainSpec) -> str:
    next_domain = NEXT_DOMAIN[domain.key]
    if next_domain is None:
        raise ValueError("final Career/HC domain has no queue edge")
    row = domain_vars(domain.key)
    scopes = event_scope_names(domain.key)
    final_state = len(domain.stages) + 1
    if next_domain == "q":
        immediate = f'''scope:{scopes["subject"]} = {{
            zg361_career_hc_prepare_transfer_vacancy_effect = yes
            if = {{
                limit = {{
                    zg361_is_celestial_liege_trigger = yes
                    any_vassal = {{ zg361_is_reviewable_vassal_trigger = yes }}
                }}
                zg361_career_hc_open_q_case_effect = yes
            }}
            else = {{ zg361_career_hc_finalize_{domain.key}_portfolio_effect = yes }}
        }}'''
    else:
        immediate = (
            f'scope:{scopes["subject"]} = {{ '
            f'zg361_career_hc_open_{next_domain}_case_effect = yes }}'
        )
    return f'''# D+1 hidden queue edge: {domain.key.upper()} closed -> {next_domain.upper()} opens.
zg361ch.{QUEUE_EVENTS[domain.key]} = {{
    type = character_event
    hidden = yes
    trigger = {{
        exists = scope:{scopes["owner"]}
        exists = scope:{scopes["subject"]}
        exists = scope:{scopes["cycle"]}
        exists = scope:{scopes["case"]}
        this = scope:{scopes["owner"]}
        zg361_is_celestial_liege_trigger = yes
        scope:{scopes["subject"]} = {{
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            var:{row["owner"]} = scope:{scopes["owner"]}
            var:{row["subject"]} = scope:{scopes["subject"]}
            var:{row["cycle"]} = scope:{scopes["cycle"]}
            var:{row["case"]} = scope:{scopes["case"]}
            var:{row["state"]} = {final_state}
            var:{row["active"]} = 0
        }}
    }}
    immediate = {{
        {immediate}
    }}
}}'''


def render_effects() -> bytes:
    sections = [
        "# ZhongGuo 361 career/HC runtime: D/M/N/O/P/Q, 44 numbered mechanisms.",
        "# Routes: 1 = evidence-led; 2 = political/extractive; 3 = bounded defer.",
        "# Public surfaces: central open plus strict PP and CL transfer adapters.",
        render_transfer_vacancy_adapter(),
        render_cl_transfer_adapter(),
        render_portfolio_adapter(),
    ]
    for domain in DOMAINS:
        sections.append(render_domain_open(domain))
        sections.append(render_authorized_ai_runner(domain))
        base_event = (ord(domain.key) - ord("a") + 1) * 100
        for state, (stage_ids, days) in enumerate(zip(domain.stages, domain.deadlines), start=1):
            sections.append(render_schedule(domain, state, days, base_event + state * 2))
            sections.append(render_barrier(domain, state, stage_ids))
            sections.append(render_timeout(domain, state, stage_ids))
        sections.append(render_outcome(domain, 900 + "dmnopq".index(domain.key) + 1))
        for state, stage_ids in enumerate(domain.stages, start=1):
            for mechanism_id in stage_ids:
                sections.append(render_manager_entry(mechanism_id, domain.key, state))
                sections.append(render_core(mechanism_id, domain.key, state))
                sections.append(render_consumer(mechanism_id, domain.key, state))
                if mechanism_id in BATCHABLE_IDS:
                    sections.append(render_background_apply(mechanism_id, domain))
                if mechanism_id in Q_AUTHORITY_IDS:
                    sections.append(render_q_business_consumer(mechanism_id, state))
    sections.append(render_portfolio_finalizer(DOMAIN_BY_KEY["p"]))
    sections.append(render_portfolio_finalizer(DOMAIN_BY_KEY["q"]))
    return generated("\n\n".join(sections))


def effect_purpose(name: str) -> str:
    """Map every generated definition to one contiguous business purpose."""

    if "transfer" in name and not name.endswith("portfolio_effect"):
        return "transfer_adapters"
    if name == "zg361_career_hc_open_portfolio_effect":
        return "portfolio_dispatch"
    if name.startswith("zg361_career_hc_finalize_"):
        return "portfolio_finalizers"
    mechanism_prefix = "zg361_career_hc_m"
    mechanism_token = name[len(mechanism_prefix) : len(mechanism_prefix) + 3]
    if name.startswith(mechanism_prefix) and mechanism_token.isdigit():
        mechanism_id = int(mechanism_token)
        domain = DOMAIN_BY_ID[mechanism_id].key
        state = STAGE_BY_ID[mechanism_id]
        return f"{domain}_stage_{state:02d}_mechanisms"
    # P has five lifecycle stages and previously accumulated eleven top-level
    # definitions in one coarse file.  Freeze its business sub-boundaries so a
    # future lifecycle addition cannot recreate that oversized unit.
    if name == "zg361_career_hc_open_p_case_effect":
        return "p_case_entry"
    if name == "zg361_career_hc_p_run_authorized_ai_effect":
        return "p_ai_runner"
    for state in range(1, len(DOMAIN_BY_KEY["p"].stages) + 1):
        if name in {
            f"zg361_career_hc_schedule_p_stage_{state:02d}_effect",
            f"zg361_career_hc_p_try_advance_{state:02d}_effect",
            f"zg361_career_hc_p_timeout_stage_{state:02d}_effect",
        }:
            return f"p_stage_{state:02d}_lifecycle"
    if name == "zg361_career_hc_resolve_p_outcome_effect":
        return "p_outcome"
    for domain in DOMAIN_ORDER:
        if any(
            marker in name
            for marker in (
                f"_open_{domain}_case_",
                f"_{domain}_run_authorized_ai_",
                f"_schedule_{domain}_stage_",
                f"_{domain}_try_advance_",
                f"_{domain}_timeout_stage_",
                f"_resolve_{domain}_outcome_",
            )
        ):
            return f"{domain}_lifecycle"
    raise ValueError(f"unclassified career/HC scripted effect: {name}")


def effect_shard_outputs() -> dict[Path, bytes]:
    shards = plan_effect_shards(
        render_effects(),
        generated_header=HEADER,
        classify=effect_purpose,
    )
    rendered: dict[Path, bytes] = {}
    for index, shard in enumerate(shards, start=1):
        if not 1 <= len(shard.names) <= MAX_EFFECTS_PER_SHARD:
            raise ValueError(f"career/HC shard {index} violates the 1-10 effect boundary")
        part = f"_part_{shard.part:02d}" if shard.part > 1 else ""
        path = EFFECTS_DIR / (
            f"zg361_career_hc_{index:03d}_{shard.purpose}{part}_effects.txt"
        )
        rendered[path] = generated(
            f'''# Purpose shard: {shard.purpose.replace("_", " ")}.
# Boundary contract: 1-10 top-level effects; this file has {len(shard.names)}.

{shard.body}'''
        )
    return rendered


def generated_effect_residue(expected: set[Path]) -> tuple[Path, ...]:
    return tuple(sorted(path for path in EFFECTS_DIR.glob(EFFECT_SHARD_GLOB) if path not in expected))


def render_events() -> bytes:
    sections = ["namespace = zg361ch", render_batch_choice_event()]
    for domain in DOMAINS:
        mechanisms = domain_mechanisms(domain)
        for index, mechanism_id in enumerate(mechanisms):
            next_mechanism = mechanisms[index + 1] if index + 1 < len(mechanisms) else None
            sections.append(render_business_event(mechanism_id, domain, next_mechanism))
        base_event = (ord(domain.key) - ord("a") + 1) * 100
        for state in range(1, len(domain.stages) + 1):
            event_id = base_event + state * 2
            if domain.key == "p" and state == 3:
                sections.append(render_deadline_event(domain, state, event_id, suffix="a"))
                sections.append(render_deadline_event(domain, state, event_id + 1, suffix="b"))
            else:
                sections.append(render_deadline_event(domain, state, event_id))
        completion = 900 + "dmnopq".index(domain.key) + 1
        sections.append(render_completion_event(domain, completion))
        if NEXT_DOMAIN[domain.key] is not None:
            sections.append(render_queue_event(domain))
    sections.append('''# Retry only while the exact PP-requested vacancy remains externally blocked.
zg361ch.990 = {
    type = character_event
    hidden = yes
    immediate = { zg361_career_hc_settle_pp_transfer_effect = yes }
}''')
    return generated("\n\n".join(sections))


def localization_rows(language: str) -> list[str]:
    english = language != "simp_chinese"
    rows = [f"l_{language}:"]
    if english:
        rows.extend(
            (
                f' zg361ch.{BATCH_CHOICE_EVENT}.t:0 "Set this portfolio\'s routine"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.desc:0 "This portfolio contains forty-four career and headcount rulings. Twenty-two consequential rulings involving payment, movement, release timing, or named people will still be presented individually. Choose one standard treatment for the other twenty-two. Each will retain its own formal record; any case lacking the required conditions will be presented separately."',
                f' zg361ch.{BATCH_CHOICE_EVENT}.a:0 "Use traceable evidence to settle twenty-two routine cases; present any case lacking the required conditions separately."',
                f' zg361ch.{BATCH_CHOICE_EVENT}.b:0 "Put execution speed first in twenty-two routine cases; present any case lacking the required conditions separately."',
                f' zg361ch.{BATCH_CHOICE_EVENT}.c:0 "Defer twenty-two routine cases, recording one next-cycle policy debt for each case."',
                f' zg361ch.{BATCH_CHOICE_EVENT}.d:0 "Present all forty-four cases individually for my separate rulings."',
            )
        )
    else:
        rows.extend(
            (
                f' zg361ch.{BATCH_CHOICE_EVENT}.t:0 "确定本轮办案方式"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.desc:0 "本轮共有四十四项职业与编制裁决。涉及付款、调动、放人期限或具名人员的二十二项仍会逐项呈报；其余二十二项可按统一口径办理。统一办理仍会逐案留下正式记录；任一案件条件不足时，便改为单独呈报。"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.a:0 "以可追溯证据为准，统一办理二十二项常规案；条件不足者单独呈报。"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.b:0 "以执行速度为先，统一办理二十二项常规案；条件不足者单独呈报。"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.c:0 "搁置二十二项常规案，每案记下一笔下周期制度债。"',
                f' zg361ch.{BATCH_CHOICE_EVENT}.d:0 "全部四十四项逐案呈报，由我分别裁决。"',
            )
        )
    for domain_index, domain in enumerate(DOMAINS, start=1):
        event_id = 900 + domain_index
        title = f"{domain.title_en} decisions recorded" if english else COMPLETION_COPY_CN[domain.key][0]
        desc = "The decisions in this career domain are recorded; open dated obligations will continue to settle on their own deadlines." if english else COMPLETION_COPY_CN[domain.key][1]
        option = "File the receipt." if english else "归档。下轮再见。"
        rows.extend(
            (
                f' zg361ch.{event_id}.t:0 "{title}"',
                f' zg361ch.{event_id}.desc:0 "{desc}"',
                f' zg361ch.{event_id}.a:0 "{option}"',
            )
        )
    for mechanism_id in EXPECTED_IDS:
        behavior = MECHANISM_BEHAVIORS[mechanism_id]
        title = (
            TITLE_OVERRIDE_EN.get(
                mechanism_id,
                behavior.behavior_key.replace("_", " ").title(),
            )
            if english
            else TITLE_OVERRIDE_CN.get(mechanism_id, behavior.title_cn)
        )
        domain = DOMAIN_BY_ID[mechanism_id]
        scopes = event_scope_names(domain.key)
        deadline = domain.deadlines[STAGE_BY_ID[mechanism_id] - 1]
        object_names_cn = "、".join(
            OBJECT_KIND_CN[kind.value] for kind in SEMANTIC_SPECS[mechanism_id].object_kinds
        )
        object_names_en = ", ".join(
            kind.value.replace("-", " ") for kind in SEMANTIC_SPECS[mechanism_id].object_kinds
        )
        if english and mechanism_id in CASE_CONTEXT_OVERRIDE_EN:
            desc = (
                f"Official [{scopes['subject']}.GetShortUIName] now requires a ruling from "
                f"[{scopes['owner']}.GetShortUIName]. "
                f"{CASE_CONTEXT_OVERRIDE_EN[mechanism_id]}"
            )
        elif english:
            desc = (
                f"Official [{scopes['subject']}.GetShortUIName] now requires a ruling from "
                f"[{scopes['owner']}.GetShortUIName]. The prior career step is complete; this ruling records "
                f"{object_names_en} and any open stage settles within {deadline} days."
            )
        else:
            desc = (
                f"当事人 [{scopes['subject']}.GetShortUIName]；裁决者 "
                f"[{scopes['owner']}.GetShortUIName]。"
                f"{CASE_CONTEXT_CN[mechanism_id]}本项最迟在 {deadline} 日内结算。"
            )
        route_a_cn, route_b_cn = ROUTE_LABELS_CN[mechanism_id]
        route_a_en, route_b_en = ROUTE_LABELS_OVERRIDE_EN.get(
            mechanism_id,
            (
                SEMANTIC_SPECS[mechanism_id].a_state.replace("-", " ").capitalize() + ".",
                SEMANTIC_SPECS[mechanism_id].b_state.replace("-", " ").capitalize() + ".",
            ),
        )
        if mechanism_id in DUAL_COST_IDS:
            route_a_cn += "；上司公私各付5，当事人公私各收5"
            route_b_cn += "；上司公私各付5，当事人公私各收5"
            route_a_en += " The direct manager pays 5 treasury and 5 personal gold; the official receives both amounts."
            route_b_en += " The direct manager pays 5 treasury and 5 personal gold; the official receives both amounts."
        rows.extend(
            (
                f' zg361ch.m{mechanism_id:03d}.name:0 "{title}"',
                f' zg361ch.m{mechanism_id:03d}.desc:0 "{desc}"',
                f' zg361ch.m{mechanism_id:03d}.a:0 "{route_a_en}"' if english else f' zg361ch.m{mechanism_id:03d}.a:0 "{route_a_cn}"',
                f' zg361ch.m{mechanism_id:03d}.b:0 "{route_b_en}"' if english else f' zg361ch.m{mechanism_id:03d}.b:0 "{route_b_cn}"',
                f' zg361ch.m{mechanism_id:03d}.c:0 "Shelve this ruling, record next-cycle policy debt, and do not propose it again this campaign."' if english else f' zg361ch.m{mechanism_id:03d}.c:0 "搁置本项，记下周期制度债；本局不再提案。"',
            )
        )
    return normalize_localization_rows(rows) if not english else rows


def render_localization(language: str) -> bytes:
    source_language = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source_language)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    rendered = effect_shard_outputs()
    rendered[MOD_ROOT / "events" / "zg361_career_hc_runtime_events.txt"] = render_events()
    for language in (
        "english",
        "simp_chinese",
        "french",
        "german",
        "japanese",
        "korean",
        "polish",
        "russian",
        "spanish",
    ):
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_career_hc_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    expected_effects = {path for path in rendered if path.parent == EFFECTS_DIR}
    residue = generated_effect_residue(expected_effects)
    if args.check:
        if stale or residue:
            print("RED: stale career/HC generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            for path in residue:
                print(f"LEGACY_OR_UNEXPECTED {path.relative_to(MOD_ROOT)}")
            return 1
        print(
            "GREEN: career/HC generated files are current "
            f"({len(expected_effects)} purpose shards, max {MAX_EFFECTS_PER_SHARD} effects each)"
        )
        return 0
    for path in residue:
        payload = path.read_bytes()
        if path != LEGACY_EFFECTS_PATH and not payload.startswith(BOM + HEADER.encode("utf-8")):
            raise RuntimeError(f"refusing to remove unowned effect file: {path}")
        path.unlink()
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} career/HC runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
