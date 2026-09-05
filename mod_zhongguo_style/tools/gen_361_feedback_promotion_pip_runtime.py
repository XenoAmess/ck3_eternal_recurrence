#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the T/U/V/W feedback, promotion, panel and PIP CK3 runtime.

This is an isolated static-ready adapter for mechanisms 146--191.  It owns no
central hook, interaction, scoreboard widget, B1/B2 source, or shared case
kernel.  The generated callable surface can therefore be integrated and
MCP-first exercised later without overstating live readiness here.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE -- edit tools/gen_361_feedback_promotion_pip_runtime.py\n"
READINESS = "static-ready"
PREFIX = "zg361_pp"
EVENT_NAMESPACE = "zg361pp"
LEGACY_EFFECT_FILENAME = "zg361_feedback_promotion_pip_runtime_effects.txt"
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# Any future hard-limit exception must carry both an engineering reason and a
# concrete CK3 live artifact.  The current B7 layout has no exception.
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}


@dataclass(frozen=True)
class DomainSpec:
    code: str
    key: str
    stages: tuple[tuple[int, ...], ...]
    stage_deadlines: tuple[int, ...]
    title_cn: str
    title_en: str
    resource: str


@dataclass(frozen=True)
class MechanismSpec:
    mechanism_id: int
    domain: str
    field: str
    title_cn: str
    title_en: str
    a_cn: str
    a_en: str
    b_cn: str
    b_en: str
    c_cn: str
    c_en: str
    deadlines: tuple[int, ...]
    consumer: str


@dataclass(frozen=True)
class EffectGroup:
    filename: str
    purpose: str
    effect_names: tuple[str, ...]


DOMAINS: tuple[DomainSpec, ...] = (
    DomainSpec("T", "t", ((146, 147, 148), (149, 150, 151), (152, 153, 154), (155, 156)), (30, 180, 90, 30), "反馈谈判与承诺债", "Feedback bargaining and promise debt", "operation_capacity"),
    # U deliberately overrides the catalogue's even ID partition.  The Python
    # L0 packet model makes withdrawal legal only while NOMINATED, so 166 must
    # run after packet evidence is frozen but before 160 prescreen mutates it.
    DomainSpec("U", "u", ((157, 158, 159), (163, 164, 165), (161, 162, 166), (160, 167, 168)), (30, 90, 30, 90), "晋升提名与预审", "Promotion nomination and prescreen", "operation_capacity"),
    # V follows the authoritative DomainSpec partition exactly: 174--176 are
    # blind_reviewed -> defended; 177--178 are defended -> voted.
    DomainSpec("V", "v", ((169, 170, 171), (172, 173), (174, 175, 176), (177, 178), (179, 180)), (30, 30, 30, 30, 90), "晋升答辩与评委政治", "Promotion panels and review politics", "operation_capacity"),
    # A graduated case waits for #188's exact D+365 observation, which queues
    # #189 on D+367.  Its case deadline is D+368 so neither same-day event
    # ordering nor timeout can choose the terminal fork for the player.  A
    # failed first PIP skips #188 as not applicable and enters #189 directly.
    DomainSpec("W", "w", ((181, 182, 183), (184, 185), (186, 187), (188, 189), (190, 191)), (30, 30, 367, 368, 30), "PIP 启动、毕业与复发", "PIP initiation, graduation and relapse", "operation_capacity"),
)
DOMAIN_BY_KEY = {domain.key: domain for domain in DOMAINS}
DOMAIN_BY_ID = {
    mechanism_id: domain
    for domain in DOMAINS
    for stage in domain.stages
    for mechanism_id in stage
}


def _m(
    mechanism_id: int,
    domain: str,
    field: str,
    title_cn: str,
    title_en: str,
    a_cn: str,
    a_en: str,
    b_cn: str,
    b_en: str,
    deadlines: int | tuple[int, ...],
    consumer: str,
) -> MechanismSpec:
    due = (deadlines,) if isinstance(deadlines, int) else deadlines
    return MechanismSpec(
        mechanism_id,
        domain,
        field,
        title_cn,
        title_en,
        a_cn,
        a_en,
        b_cn,
        b_en,
        "延期，但把负责人、期限和欠账写进案卷。",
        "Defer, but bind an owner, deadline and policy-debt receipt.",
        due,
        consumer,
    )


MECHANISMS: tuple[MechanismSpec, ...] = (
    _m(146, "t", "delivery_style", "直白档位 / 委婉话术制度", "Plain rating or softened wording", "直说冻结档位，并确认对方确实听懂。", "State the frozen rating plainly and record understanding.", "委婉表达，但保留同一档位并记录误解债。", "Use indirect wording, preserve the rating, and record misunderstanding debt.", 30, "反馈会和申诉时钟读取同一冻结档位"),
    _m(147, "t", "polarity_template", "强制“一扬一抑”反馈模板", "Forced praise-and-critique template", "只写有冻结证据支撑的表扬或批评。", "Let frozen evidence determine praise and critique counts.", "硬凑一扬一抑，并标记无证据套话。", "Force both polarities and flag unsupported boilerplate.", 30, "反馈质量表消费证据链接与套话数"),
    _m(148, "t", "meeting_order", "先讲证据还是先报结果", "Evidence first or rating first", "逐项确认事实，再宣布档位。", "Confirm each evidence item before announcing the rating.", "先报档位，但不得删改随后展示的证据。", "Announce the rating first while preserving the same evidence and disputes.", 30, "纪要保存步骤顺序、确认和异议"),
    _m(149, "t", "bargain_terms", "绩效结果谈判包", "Performance-result bargain package", "书面冻结补偿条款、负责人和到期日；本轮低档不变。", "Freeze written terms, owner and due date without changing the current lower rating.", "只留口头保证，不得冒充已经履约。", "Record an oral assurance without pretending the debt is fulfilled.", 180, "个人谈判页核销实际付款回执"),
    _m(150, "t", "sacrifice_promise", "“这次先委屈你”的补偿承诺", "A promise for this cycle's sacrifice", "建立有资金、有期限的非改档补偿义务。", "Open a funded, dated, non-rating compensation obligation.", "继续画饼，并公开它仍是未履约债。", "Make an oral promise and expose it as unfulfilled debt.", 365, "承诺时间线到期后结算履约或背约"),
    _m(151, "t", "receipt_agreement", "签收不等于认同", "Receipt is not agreement", "把送达、认同、异议分别记录，保留申诉。", "Record delivery, agreement and objection separately; keep appeal available.", "把签收强写成认同，并产生程序债。", "Coerce receipt into agreement and post procedural debt.", (7, 90), "收据行、见证送达与申诉案卷分别消费"),
    _m(152, "t", "actionability_score", "反馈可行动性评分", "Feedback actionability score", "按具体、可控、期限、资源四项冻结评分。", "Freeze specificity, controllability, deadline and resource scores.", "只记满意度，模糊建议不得拿满分。", "Record sentiment only; vague advice cannot receive full actionability credit.", 365, "经理反馈质量表按收件人一次性回写"),
    _m(153, "t", "action_item", "反馈后行动项闭环", "Post-feedback action closure", "建立唯一负责人、原始期限和验收证据。", "Open one action with an owner, original due date and acceptance evidence.", "允许改期或取消，但完整保留历史和理由。", "Allow change or cancellation while preserving history and reasons.", 90, "行动时间线只接受一个终态回执"),
    _m(154, "t", "minutes_mode", "录音式完整纪要 / 摘要纪要", "Full minutes or summary minutes", "保存附证据引用的完整追加式纪要。", "Keep complete append-only minutes with evidence references.", "保存摘要，但必须保留结果与证据索引。", "Keep a summary while retaining result and evidence references.", 7, "申诉投影只读纪要版本和更正附录"),
    _m(155, "t", "public_private_boundary", "公开表扬与私下批评边界", "Public praise and private criticism boundary", "只公开获准成绩，敏感反馈留在本人案卷。", "Publish approved achievements and keep sensitive feedback private.", "公开点名末位，并承担羞辱与报复成本。", "Name bottom performers publicly and incur shaming and retaliation costs.", 1, "团队公告与私人反馈使用不同字段投影"),
    _m(156, "t", "team_briefing", "团队结果说明会", "Team result briefing", "出榜后说明分布原则、共性问题和资源计划。", "Brief the distribution rule, common issues and resource plan after publication.", "不解释，让信息真空生成传言债。", "Skip the briefing and post information-vacuum debt.", 30, "政策面板读取说明会收据或流言风险"),

    _m(157, "u", "nomination_access", "自荐权与主管提名权", "Self-nomination and manager nomination", "允许合资格者自荐，但绑定 sponsor 与主管意见。", "Allow eligible self-nomination with a sponsor and recorded manager opinion.", "主管独占入口，并记录反对或支持理由。", "Keep manager-only access and record the support or rejection reason.", 30, "提名队列生成一人一包的冻结案号"),
    _m(158, "u", "nomination_quota", "主管提名额度", "Manager nomination quota", "把稀缺额度集中给有证据的候选并排序。", "Concentrate scarce slots on evidence-backed candidates and rank them.", "分散押边界包，辅导工时同步摊薄。", "Spread slots across boundary packets and dilute coaching hours.", 30, "额度账校验已用、归还与剩余恒等"),
    _m(159, "u", "shelved_star", "雪藏明星不提名", "Shelving an eligible star", "先冻结接班计划，再给明星明确提名期限。", "Freeze a successor plan and a dated nomination path for the star.", "为保当期产出继续雪藏，并生成逾期人才债。", "Shelve the star for current output and post overdue talent debt.", 90, "逾期审计每周期只扣一次经理人才分"),
    _m(160, "u", "prescreen_rubric", "部门预审淘汰赛", "Department prescreen", "按材料、职级证据、战略匹配三维预审。", "Prescreen on packet completeness, level evidence and strategic fit.", "派系先筛人，但保留本轮淘汰理由。", "Use a political cut while preserving the rejection reason.", 30, "预审队列只把真实席位数量的包送进答辩"),
    _m(161, "u", "sham_competition", "“陪跑包”与虚假竞争", "Filler packets and sham competition", "只提交真愿意支持的候选。", "Submit only candidates the manager genuinely supports.", "放入陪跑包，计入准备工时和公平债。", "Insert a filler packet and charge its preparation hours and fairness debt.", 30, "经理公平信用和主推包合法性消费陪跑识别"),
    _m(162, "u", "tenure_exception", "资历门槛例外申请", "Tenure exception application", "先占破格额度并单独表决准入，再评能力。", "Reserve an exception slot and vote on admission before merit review.", "把普通表现包装成破格，并透支未来可信度。", "Package ordinary evidence as exceptional and spend future credibility.", 30, "破格额度账与后续能力评审保持分离"),
    _m(163, "u", "observation_window", "晋升绩效观察窗", "Promotion observation window", "周期初冻结最近两轮，并给重组等事实附语境。", "Freeze the last two cycles up front and attach reorganization context.", "只挑最漂亮一轮，留下选窗审计差异。", "Cherry-pick the best cycle and retain the window audit diff.", 90, "预审只读取冻结窗口内的完整候选历史"),
    _m(164, "u", "cross_team_evidence", "跨团队成果进入晋升包", "Cross-team evidence in the packet", "旧 owner 共签或独立复核后按贡献份额入包。", "Admit cross-team evidence after old-owner cosign or independent review with bounded shares.", "拿团队总成绩冒充个人影响，触发归因债。", "Claim the team total as personal impact and post attribution debt.", 90, "晋升包消费有来源的贡献份额而非团队总分"),
    _m(165, "u", "next_level_trial", "“先干到下一级”试岗证据", "Next-level trial evidence", "同时冻结授权、补偿、期限和退出条件。", "Freeze authority, compensation, deadline and exit condition together.", "只加活不给权，并记录职级债。", "Add next-level work without authority and post level debt.", 90, "预审消费试岗验收回执，不改当期绩效"),
    _m(166, "u", "packet_withdrawal", "候选主动撤包", "Candidate packet withdrawal", "预审前撤回，归还额度并只复用已验证材料。", "Withdraw before prescreen, return the slot and retain only verified artifacts.", "劝候选硬上，失败理由照实归档。", "Push the weak packet forward and preserve the failure reason.", 90, "下轮材料版本读取已验证工件与准备度风险"),
    _m(167, "u", "sponsor_credit", "Sponsor 的晋升信用债", "Sponsor promotion credit", "按事实作有限背书，下一观察期再结算信用。", "Make a bounded factual endorsement and settle credit after observation.", "强力担保，失配时按同等强度折价。", "Guarantee strongly and accept an equal credibility discount on mismatch.", 365, "后续胜任观察只结算一次 sponsor 信用"),
    _m(168, "u", "manager_hit_rate", "经理提名命中率", "Manager nomination hit rate", "按难度加权通过与胜任，并计入无故漏提。", "Weight passage and later competence by difficulty and count omitted qualified staff.", "只报稳赢包，命中率旁列风险规避债。", "Nominate only sure wins and display risk-avoidance debt beside the hit rate.", 365, "上司下一轮辅导或收紧额度时消费成熟样本"),

    _m(169, "v", "expertise_mix", "评委专业匹配", "Panel expertise matching", "冻结专业席与外部席权重，合计一百。", "Freeze expert and external weights that sum to one hundred.", "让熟悉团队的人占多数，并公开关系风险。", "Give familiar reviewers the majority and expose relationship risk.", 30, "答辩计分器按事前权重消费每席评分"),
    _m(170, "v", "panel_selection", "随机评委与熟人评委", "Random and familiar panelists", "从跨部门池按冻结种子抽唯一评委。", "Draw unique panelists from the cross-unit pool with a frozen seed.", "接受团队推荐熟人，但候选不得指定多数。", "Accept some familiar nominees without letting the candidate appoint a majority.", 30, "复跑以同一 seed 得到同一无重复席位"),
    _m(171, "v", "panel_recusal", "答辩评委利益回避", "Panel conflict recusal", "披露冲突并用同专业的清洁备选席替换。", "Disclose conflicts and replace each seat with a clean peer of the same kind.", "隐瞒冲突；发现后整包进入重审债。", "Hide conflicts and post full-packet re-review debt when found.", 30, "投票器只接受回避后的活跃评委集合"),
    _m(172, "v", "decision_rule", "一票否决 / 多数票 / 平均分", "Veto, majority or trimmed mean", "投票前冻结规则；否决必须附可复核理由。", "Freeze the rule before voting and require a reviewable reason for every veto.", "临场改规则帮助目标候选，并留下规则漂移债。", "Change the rule midstream for a favored candidate and post rule-drift debt.", 30, "最终决定只消费冻结规则下的一人一票"),
    _m(173, "v", "blind_live_review", "盲材料审查与现场答辩", "Blind packet and live defense", "先冻结去身份材料分，再实名现场提问。", "Freeze identity-blind packet scores before the named live defense.", "直接现场看关系，仍保留书面工件缺口。", "Review live with relationship anchors and retain the missing-artifact gap.", 30, "评委质量复盘比较不可变盲分与现场分"),
    _m(174, "v", "defense_time", "答辩时间预算", "Defense time budget", "六十分钟中保护二十分钟质询，其余用于陈述。", "Protect twenty of sixty minutes for questions and use the rest for presentation.", "让 PPT 占满大部分时间，但总时长仍守恒。", "Let slides consume most of the session while total time still conserves.", 30, "答辩记录校验陈述加质询等于冻结总时长"),
    _m(175, "v", "coaching_pool", "模拟答辩与辅导资源", "Mock-defense coaching pool", "从公共教练池按透明规则分配有限工时。", "Allocate finite hours from a transparent shared coaching pool.", "只辅导亲信，并把机会不均写进案卷。", "Coach favorites and record unequal opportunity evidence.", 30, "辅导账校验已分配工时不超过开放池"),
    _m(176, "v", "individual_attribution", "团队成绩的个人归因质询", "Individual attribution of team results", "把候选与同伴贡献拆分到一百。", "Split candidate and peer contribution shares to exactly one hundred.", "把团队成绩全据为己有，生成抢功债。", "Claim the team result wholesale and post credit-grab debt.", 30, "评委只按冻结个人份额计算影响证据"),
    _m(177, "v", "scale_leverage", "项目规模与个人杠杆分离", "Project scale versus personal leverage", "分别冻结项目规模与个人杠杆。", "Freeze project scale and personal leverage as separate scores.", "用大项目光环替代个人杠杆，留下分离差值。", "Substitute project halo for personal leverage and retain the gap.", 30, "目标职级判定同时消费两个独立维度"),
    _m(178, "v", "dual_evidence", "可复核工件与故事表达双证据", "Artifacts and narrative as dual evidence", "工件与叙事均过冻结门槛才进入投票。", "Require both artifacts and narrative to clear frozen thresholds before voting.", "只凭故事放行，缺工件则延期补齐。", "Advance on narrative alone and mark the missing-artifact deferral.", 30, "双门槛结果决定投票或补材料"),
    _m(179, "v", "rejection_feedback", "失败答辩的具体反馈 owner", "Named owner for rejection feedback", "每条差距绑定一名实际评委和下一证据。", "Bind each gap and next evidence item to an actual panelist.", "写“再提升影响力”，空话扣评委质量。", "Write a vague improvement slogan and charge reviewer-quality debt.", 90, "下轮材料对照同一 gap，不得无故换口径"),
    _m(180, "v", "retry_cooldown", "晋升冷却与材料刷新", "Promotion retry cooldown and refresh", "冷却一轮；指定差距完成可提前重开。", "Cool down for one cycle, with early retry after every frozen gap is closed.", "立即重复消耗评委，并累积评审拥塞。", "Retry immediately and accumulate panel congestion.", (90, 365), "重试只复用版本化旧材料并追加新影响"),

    _m(181, "w", "triage_category", "能力、意愿、错岗三分诊", "Skill, will or role-mismatch triage", "按证据分诊并把错岗导向真实转岗，不改本轮档位。", "Triage from evidence and route role mismatch to a real transfer without rewriting the rating.", "一律归为不愿做，生成误诊与申诉风险。", "Assume unwillingness and post misdiagnosis and appeal risk.", 30, "PIP 入口按唯一主类别选择训练、纪律或转岗"),
    _m(182, "w", "pip_evidence_gate", "PIP 启动证据门槛", "PIP evidence threshold", "只有冻结证据组合过线才正式开案。", "Open a formal PIP only after the frozen evidence combination meets threshold.", "看到 3.25 就自动开案，并记录误伤风险。", "Auto-start from a 3.25 rating and record false-positive risk.", 30, "启动门把红线违纪分流到独立纪律案"),
    _m(183, "w", "pip_acknowledgement", "PIP 目标双签与拒签理由", "Dual-signature PIP goals", "目标、资源、期限双签后计时。", "Start the clock after dual signature on goals, resources and deadlines.", "保留拒签理由，交独立席判断合理性。", "Preserve refusal reasons for independent reasonableness review.", 30, "任务页区分送达、认同、拒签和一次修订"),
    _m(184, "w", "pip_caseload", "经理的 PIP 承载量", "Manager PIP caseload", "预留经理工时，或增加导师与错峰容量。", "Reserve manager hours or add mentor and staggered capacity.", "超载开案，并把支持失败责任回写经理。", "Overbook cases and assign support-failure liability to the manager.", 1, "容量面板按终态一次释放每案预留"),
    _m(185, "w", "pip_midpoint", "PIP 中期检查", "PIP midpoint review", "只做一次中检，并允许一次有证据修正。", "Run one midpoint and allow one evidence-backed correction.", "跳过中检，随后不得倒造资源或目标更正。", "Skip the midpoint; later resource or goal corrections become invalid.", 180, "PIP 时间线消费进度、资源交付和目标有效性"),
    _m(186, "w", "goal_creep_lock", "PIP 目标膨胀锁", "PIP goal-creep lock", "加任务必须等量替换、延期或获紧急复核。", "Add work only with equal replacement, extension or emergency review.", "直接加码，并生成目标膨胀违规。", "Add workload directly and post a goal-creep violation.", 7, "变更账比较基线、当前工作量和补偿路线"),
    _m(187, "w", "graduation_gate", "PIP 毕业标准", "PIP graduation gate", "读取唯一案卷的毕业或失败回执；经理只能选择复核程序。", "Read the unique case's graduation or failure receipt; the manager chooses only the review procedure.", "要求程序复核，但不能替本人签字或替结算器宣布毕业。", "Request procedural review without signing for the subject or declaring graduation for the settler.", 366, "毕业或失败只读取 B2 唯一结算回执，绝不直接写档位"),
    _m(188, "w", "relapse_window", "毕业后的复发观察期", "Post-graduation relapse window", "只观察一个周期，且仅同类问题升级。", "Observe exactly one cycle and escalate only the same problem category.", "贴长期标签，并记录过度披露风险。", "Apply a long-lived label and record overbreadth risk.", 365, "观察标记到期一次；新问题必须另开案"),
    _m(189, "w", "terminal_fork", "二次 PIP / 调岗 / 退出三岔口", "Second PIP, transfer or exit", "按支持、错岗和真实空缺只选一条合法路线。", "Choose one legal route from support sufficiency, role mismatch and real vacancy.", "强制退出，并结算空缺、交接和补员成本。", "Force exit and settle vacancy, handover and replacement costs.", 30, "终局决定页只接受一个排他终态"),
    _m(190, "w", "transfer_disclosure", "PIP 随转岗披露的最小范围", "Minimum PIP transfer disclosure", "只向真实接收经理披露目标、支持、结果和本人陈述。", "Disclose goals, support, outcome and the subject statement only to the real receiving manager.", "贴粗糙标签，但不得编造细节或改旧档位。", "Apply a coarse label without inventing details or rewriting the old rating.", 30, "转岗包按 ACL 投影最小字段"),
    _m(191, "w", "exit_cost_statement", "PIP 退出后的团队成本单", "Team cost statement after PIP exit", "以实际付款回执列空缺、交接、加班和补员净成本。", "Post vacancy, handover, overtime and replacement net cost from actual receipts.", "只报节省，隐藏成本转为经理债。", "Report gross savings and move hidden costs to manager debt.", 30, "团队成本表和经理记分卡消费同一净额"),
)
MECHANISM_BY_ID = {mechanism.mechanism_id: mechanism for mechanism in MECHANISMS}
EXPECTED_IDS = tuple(range(146, 192))
DUAL_COST_ROUTE_BY_ID = {149: 1, 150: 1, 165: 1, 189: 2, 191: 1}
DUAL_COST_IDS = frozenset(DUAL_COST_ROUTE_BY_ID)
SUBJECT_RESPONSE_IDS = frozenset({151, 166, 190})
P2_DEFER_IDS = frozenset({147, 149, 154, 155, 161, 162, 166, 170, 172, 173})
EXTRA_RESOURCES_BY_ID: dict[int, tuple[str, ...]] = {
    **{mechanism_id: ("capacity_hours",) for mechanism_id in (*range(146, 155), 156)},
    149: ("capacity_hours", "commitment_capacity"),
    150: ("capacity_hours", "commitment_capacity"),
    157: ("nomination_slot",),
    162: ("tenure_exception_slot",),
    165: ("capacity_hours",),
    **{mechanism_id: ("panel_vote",) for mechanism_id in (169, 170, 173, 174, 176, 177, 178, 179, 180)},
    **{mechanism_id: ("capacity_hours",) for mechanism_id in (171, 172, 175)},
    191: ("exit_cost",),
}

# These resources exist only when the corresponding route creates the real
# business object.  A political prescreen rejection must not burn a promotion
# slot; an overloaded PIP must not pretend that capacity was reserved; and a
# supported second-PIP/transfer path must not post an exit-cost receipt.
ROUTE_A_EXTRA_RESOURCES_BY_ID: dict[int, tuple[str, ...]] = {
    160: ("promotion_slot",),
}

# #161 only spends a second real nomination slot and preparation hours on the
# expedient filler-packet route.  The evidence-led route creates no phantom
# candidate and therefore must not burn those resources.
ROUTE_B_EXTRA_RESOURCES_BY_ID: dict[int, tuple[str, ...]] = {
    161: ("nomination_slot", "capacity_hours"),
    189: ("exit_cost",),
}

# Every delayed audit must consume one field from the mechanism's typed
# business object.  Merely copying the A/B/C route into a generic audit row is
# not a downstream consumer: it cannot prove that the promised packet, vote,
# obligation, PIP gate, or terminal fork ever existed.  These fields are all
# initialized on both A and B and are read only after the five-tuple audit
# guard succeeds.  Route C has no typed object and therefore records only the
# bounded policy-debt outcome.
DELAYED_CONSUMER_FIELD_BY_ID: dict[int, str] = {
    146: "frozen_grade",
    147: "quality_credit",
    148: "rating_snapshot",
    149: "obligation_status",
    150: "obligation_status",
    151: "grade_at_delivery",
    152: "total_score",
    153: "current_due_days",
    154: "evidence_index",
    155: "private_sensitive_fields",
    156: "completion_receipt",
    157: "packet_status",
    158: "quota_conserved",
    159: "nomination_due_cycles",
    160: "prescreen_pass",
    161: "filler",
    162: "admission_vote_frozen",
    163: "window_cycles",
    164: "share_check",
    165: "trial_due_days",
    166: "packet_active_after",
    167: "observation_id",
    168: "attempt_id",
    169: "weight_check",
    170: "selection_checksum",
    171: "active_panel_revision",
    172: "decision_rule_code",
    173: "blind_score",
    174: "time_check",
    175: "coaching_conserved",
    176: "share_check",
    177: "dimensions_separate",
    178: "final_decision",
    179: "gap_id",
    180: "retry_count",
    181: "evidence_id",
    182: "gate_status",
    183: "acknowledgement_status",
    184: "active_case",
    185: "midpoint_status",
    186: "current_workload",
    187: "graduation_status",
    188: "relapse_status",
    189: "terminal_code",
    190: "audit_delivery_acl_pass",
    191: "net_cost",
}

# A business decision may be recorded immediately while its promised outcome
# remains time-bound.  These three mechanisms deliberately hold their stage
# barrier until the target-bound audit consumes the promise.  #188 also holds
# the next same-stage card, otherwise the player could choose a terminal fork
# before the one-cycle relapse window had elapsed.
DELAYED_STAGE_GATE_IDS = frozenset({185, 187, 188})

AUDIT_ONLY_FIELDS_BY_ID: dict[int, tuple[str, ...]] = {
    149: ("fulfilled_receipt", "breach_receipt"),
    150: ("fulfilled_receipt", "breach_receipt"),
    151: (
        "delivery_audit_closed",
        "delivery_receipt_valid",
        "appeal_clock_closed",
        "appeal_result_grade",
        "appeal_closed_without_filing",
    ),
    167: ("competent", "sponsor_credit_delta"),
    168: ("competent",),
    180: ("retry_unlock_reason", "retry_settled_receipt"),
    185: (
        "progress_snapshot",
        "progress_truth_status",
        "progress_red_code",
        "resource_delivery_valid",
        "late_correction_invalid",
    ),
    187: (
        "key_milestones_met",
        "stability_days_observed",
        "independent_review_pass",
        "independent_review_red_code",
        "appeal_weight",
    ),
    188: (
        "observed_result_owner",
        "observed_result_subject",
        "observed_result_cycle",
        "observed_result_case",
        "observed_result_state",
        "observed_result_grade",
        "observed_result_reason",
        "observed_category",
        "skipped_first_failure",
    ),
    189: ("skipped_no_relapse",),
    190: (
        "audit_delivery_acl_pass",
        "audit_external_status",
        "audit_external_red_code",
    ),
}

RESPONSE_ONLY_FIELDS_BY_ID: dict[int, tuple[str, ...]] = {
    151: ("appeal_snapshot_grade",),
    190: (
        "subject_statement_author",
        "subject_statement_receiver",
        "subject_statement_version",
        "subject_statement_private_ids",
        "subject_statement_code",
        "subject_disclosure_refused",
    ),
}


MECHANISM_LIFECYCLE_GROUPS: tuple[tuple[int, ...], ...] = (
    # T: feedback bargaining and promise debt.
    (146, 147),
    (148,),
    (149, 150),
    (151,),
    (152, 153),
    (154,),
    (155, 156),
    # U: promotion nomination and prescreen.
    (157, 158),
    (159, 160),
    (161, 162),
    (163, 164),
    (165, 166),
    (167, 168),
    # V: promotion panels and review politics.
    (169, 170),
    (171, 172),
    (173, 174),
    (175, 176),
    (177, 178),
    (179, 180),
    # W: PIP initiation, graduation and relapse.
    (181, 182),
    (183, 184),
    (185, 186),
    (187, 188),
    (189, 190),
    (191,),
)


def _mechanism_lifecycle_effect_names(
    mechanism_ids: tuple[int, ...],
) -> tuple[str, ...]:
    names: list[str] = []
    for mechanism_id in mechanism_ids:
        names.append(f"zg361_pp_m{mechanism_id:03d}_manager_apply_effect")
        if mechanism_id in SUBJECT_RESPONSE_IDS:
            names.extend(
                (
                    f"zg361_pp_m{mechanism_id:03d}_subject_response_effect",
                    f"zg361_pp_m{mechanism_id:03d}_resume_after_subject_effect",
                )
            )
        names.extend(
            (
                f"zg361_pp_m{mechanism_id:03d}_core_effect",
                f"zg361_pp_m{mechanism_id:03d}_consume_effect",
            )
        )
        names.extend(
            f"zg361_pp_m{mechanism_id:03d}_schedule_audit_{index}_effect"
            for index, _days in enumerate(
                MECHANISM_BY_ID[mechanism_id].deadlines, start=1
            )
        )
    return tuple(names)


def _build_effect_groups() -> tuple[EffectGroup, ...]:
    """Build ordered B7 purpose shards from the historical call surface."""

    groups: list[EffectGroup] = []

    def add(slug: str, purpose: str, names: tuple[str, ...]) -> None:
        ordinal = len(groups) + 1
        groups.append(
            EffectGroup(
                filename=(
                    "zg361_feedback_promotion_pip_"
                    f"{ordinal:03d}_{slug}_effects.txt"
                ),
                purpose=purpose,
                effect_names=names,
            )
        )

    add(
        "portfolio_adapter",
        "portfolio integration adapter",
        ("zg361_pp_manager_portfolio_adapter_effect",),
    )
    add(
        "pip_terminal_guards",
        "PIP first-failure and clean-graduation terminal guards",
        (
            "zg361_pp_m188_skip_first_failure_effect",
            "zg361_pp_m189_skip_no_relapse_effect",
        ),
    )

    for domain in DOMAINS:
        stage_spans = (
            ((1,), (2, 3), (4,))
            if len(domain.stages) == 4
            else ((1,), (2, 3), (4, 5))
        )
        for span_index, states in enumerate(stage_spans):
            names: list[str] = []
            if span_index == 0:
                names.append(f"zg361_pp_open_{domain.key}_case_effect")
            for state in states:
                names.extend(
                    (
                        f"zg361_pp_schedule_{domain.key}_stage_{state:02d}_effect",
                        f"zg361_pp_dispatch_{domain.key}_stage_{state:02d}_effect",
                        f"zg361_pp_{domain.key}_try_advance_{state:02d}_effect",
                        f"zg361_pp_{domain.key}_timeout_stage_{state:02d}_effect",
                    )
                )
            if span_index == len(stage_spans) - 1:
                names.append(f"zg361_pp_resolve_{domain.key}_outcome_effect")
            stage_slug = "_".join(f"{state:02d}" for state in states)
            add(
                f"{domain.key}_stages_{stage_slug}",
                f"{domain.code} case stages {', '.join(map(str, states))}",
                tuple(names),
            )

    for mechanism_ids in MECHANISM_LIFECYCLE_GROUPS:
        first = mechanism_ids[0]
        last = mechanism_ids[-1]
        domain = DOMAIN_BY_ID[first]
        if any(DOMAIN_BY_ID[mid] != domain for mid in mechanism_ids):
            raise ValueError("effect purpose shard crosses a T/U/V/W domain")
        mechanism_slug = (
            f"m{first:03d}" if first == last else f"m{first:03d}_m{last:03d}"
        )
        add(
            f"{domain.key}_{mechanism_slug}_lifecycle",
            f"{domain.code} mechanism lifecycle {first}"
            + ("" if first == last else f"-{last}"),
            _mechanism_lifecycle_effect_names(mechanism_ids),
        )
    return tuple(groups)


EFFECT_GROUPS = _build_effect_groups()


def validate_specs() -> None:
    ids = tuple(mechanism.mechanism_id for mechanism in MECHANISMS)
    if ids != EXPECTED_IDS or tuple(sorted(DOMAIN_BY_ID)) != EXPECTED_IDS:
        raise ValueError("feedback/promotion/PIP runtime must cover exactly 146--191")
    if len(set(ids)) != 46 or len({mechanism.field for mechanism in MECHANISMS}) != 46:
        raise ValueError("mechanism IDs and typed operation fields must be unique")
    if {mechanism.domain for mechanism in MECHANISMS} != {"t", "u", "v", "w"}:
        raise ValueError("only T/U/V/W are owned")
    for domain in DOMAINS:
        if len(domain.stages) != len(domain.stage_deadlines):
            raise ValueError(f"{domain.code}: stage/deadline mismatch")
        for stage_index, stage in enumerate(domain.stages, start=1):
            for mechanism_id in stage:
                mechanism = MECHANISM_BY_ID[mechanism_id]
                if mechanism.domain != domain.key or not mechanism.deadlines:
                    raise ValueError(f"{mechanism_id}: domain/deadline drift")
                if stage_index < 1 or any(days < 1 for days in mechanism.deadlines):
                    raise ValueError(f"{mechanism_id}: invalid deadline")
    if not DUAL_COST_IDS <= set(EXPECTED_IDS) or not SUBJECT_RESPONSE_IDS <= set(EXPECTED_IDS):
        raise ValueError("special mechanism outside owned range")
    if not P2_DEFER_IDS <= set(EXPECTED_IDS):
        raise ValueError("P2 defer mechanism outside owned range")
    if not set(EXTRA_RESOURCES_BY_ID) <= set(EXPECTED_IDS):
        raise ValueError("secondary resource outside owned range")
    if not set(ROUTE_B_EXTRA_RESOURCES_BY_ID) <= set(EXPECTED_IDS):
        raise ValueError("route-B resource outside owned range")
    if not set(ROUTE_A_EXTRA_RESOURCES_BY_ID) <= set(EXPECTED_IDS):
        raise ValueError("route-A resource outside owned range")
    if set(ROUTE_A_EXTRA_RESOURCES_BY_ID) & set(ROUTE_B_EXTRA_RESOURCES_BY_ID):
        raise ValueError("route-specific resource ownership must be unambiguous")
    if set(DUAL_COST_ROUTE_BY_ID) != set(DUAL_COST_IDS) or not all(
        route in (1, 2) for route in DUAL_COST_ROUTE_BY_ID.values()
    ):
        raise ValueError("dual-payer routes must be explicit A/B operations")
    if set(DELAYED_CONSUMER_FIELD_BY_ID) != set(EXPECTED_IDS):
        raise ValueError("every owned mechanism needs one typed delayed consumer")
    if not DELAYED_STAGE_GATE_IDS <= set(EXPECTED_IDS):
        raise ValueError("delayed stage gate outside owned range")
    if not set(AUDIT_ONLY_FIELDS_BY_ID) <= set(EXPECTED_IDS):
        raise ValueError("audit-only reset field outside owned range")
    if not set(RESPONSE_ONLY_FIELDS_BY_ID) <= set(SUBJECT_RESPONSE_IDS):
        raise ValueError("response-only reset field without subject response")
    if READINESS != "static-ready":
        raise ValueError("generator must not claim live readiness")


def generated(text: str) -> bytes:
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"
    return BOM + (HEADER + cleaned).encode("utf-8")


def localized(text: str) -> bytes:
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"
    return BOM + cleaned.encode("utf-8")


def case_vars(domain: str) -> dict[str, str]:
    base = f"zg361_case_{domain}"
    return {
        "owner": f"{base}_owner",
        "subject": f"{base}_subject",
        "cycle": f"{base}_cycle_serial",
        "case": f"{base}_case_serial",
        "state": f"{base}_state",
        "active": f"{base}_active",
        "revision": f"{base}_revision",
        "timeline": f"{base}_timeline_serial",
        "feedback": f"{base}_feedback_revision",
    }


def mechanism_stage(mechanism_id: int) -> int:
    domain = DOMAIN_BY_ID[mechanism_id]
    return next(index for index, stage in enumerate(domain.stages, start=1) if mechanism_id in stage)


def defer_days(mechanism_id: int) -> int:
    return 180 if mechanism_id in P2_DEFER_IDS else 90


def indent(text: str, tabs: int = 1) -> str:
    prefix = "\t" * tabs
    return "\n".join(prefix + line if line else "" for line in text.splitlines())


def full_guard(
    domain: str,
    state: int,
    owner: str,
    subject: str = "this",
    cycle: str | None = None,
    case: str | None = None,
    expected_state: str | None = None,
) -> str:
    row = case_vars(domain)
    cycle = cycle or f'var:{row["cycle"]}'
    case = case or f'var:{row["case"]}'
    expected_state = expected_state or str(state)
    return f'''zg361_case_kernel_full_guard_trigger = {{
\tOWNER_VAR = {row["owner"]}
\tSUBJECT_VAR = {row["subject"]}
\tCYCLE_VAR = {row["cycle"]}
\tCASE_VAR = {row["case"]}
\tSTATE_VAR = {row["state"]}
\tACTIVE_VAR = {row["active"]}
\tEXPECTED_OWNER = {owner}
\tEXPECTED_SUBJECT = {subject}
\tEXPECTED_CYCLE = {cycle}
\tEXPECTED_CASE = {case}
\tEXPECTED_STATE = {expected_state}
}}'''


def business_dependency_conditions(mechanism_id: int, route: int) -> str:
    """Return real prerequisite reads for an A/B operation.

    Route C intentionally has no business prerequisites: it records bounded
    policy debt and lets the stage dispatcher close the decision without
    manufacturing the missing object.
    """

    if route == 3:
        return "always = yes"
    common_packet = '''var:zg361_pp_m157_packet_active = 1
var:zg361_pp_m157_packet_status = 1
var:zg361_pp_m157_packet_candidate = this
var:zg361_pp_m157_receipt_owner = var:zg361_case_u_owner
var:zg361_pp_m157_receipt_cycle = var:zg361_case_u_cycle_serial
var:zg361_pp_m157_receipt_case = var:zg361_case_u_case_serial
OR = {
\tvar:zg361_pp_m157_nomination_slot_status = 1
\tvar:zg361_pp_m157_nomination_slot_status = 2
}'''
    rows: dict[int, str] = {
        157: "var:zg361_pp_u_candidate_eligible = 1",
        158: common_packet,
        161: common_packet,
        162: common_packet,
        163: common_packet,
        164: common_packet,
        165: common_packet,
        166: common_packet,
        160: f'''{common_packet}
var:zg361_pp_m158_quota_conserved = 1
var:zg361_pp_m158_quota_used >= 1
has_variable = zg361_pp_m161_filler
var:zg361_pp_m162_exception_admitted = 1
has_variable = zg361_pp_m163_window_cycles
has_variable = zg361_pp_m164_candidate_share
has_variable = zg361_pp_m165_authority_bound
var:zg361_pp_m166_packet_active_after = 1
var:zg361_pp_m166_withdrawn_before_prescreen = 0''',
        167: '''has_variable = zg361_pp_m160_prescreen_pass
var:zg361_pp_m160_packet_candidate_consumed = this''',
        168: '''has_variable = zg361_pp_m160_prescreen_pass
has_variable = zg361_pp_m167_observation_id''',
        169: '''var:zg361_pp_m160_prescreen_pass = 1
var:zg361_pp_m160_packet_candidate_consumed = this
var:zg361_pp_m160_promotion_slot_status = 2
has_variable = zg361_pp_v_source_packet_case''',
        170: '''has_variable = zg361_pp_v_panel_pool_1
has_variable = zg361_pp_v_panel_pool_2
has_variable = zg361_pp_v_panel_pool_3''',
        171: '''var:zg361_pp_m170_selection_replay_ok = 1
var:zg361_pp_m170_panel_unique = 1''',
        172: '''var:zg361_pp_m169_weight_check = 100
var:zg361_pp_m171_active_panel_count = 3
has_variable = zg361_pp_m171_active_panel_revision''',
        173: '''var:zg361_pp_m172_rule_frozen_before_vote = 1
var:zg361_pp_m172_panel_weight_check = 100''',
        174: '''has_variable = zg361_pp_m173_blind_score
var:zg361_pp_m173_identity_fields_hidden = 1''',
        175: '''var:zg361_pp_m174_time_check = 60
var:zg361_pp_m174_question_minutes >= 5''',
        176: '''var:zg361_pp_m174_time_check = 60
has_variable = zg361_pp_m175_coaching_allocated''',
        177: '''var:zg361_pp_m176_share_check = 100
has_variable = zg361_pp_m176_candidate_share''',
        178: '''has_variable = zg361_pp_m173_blind_score
var:zg361_pp_m174_time_check = 60
has_variable = zg361_pp_m175_coaching_allocated
var:zg361_pp_m176_share_check = 100
has_variable = zg361_pp_m177_scale_score
has_variable = zg361_pp_m177_leverage_score''',
        179: '''var:zg361_pp_m178_final_decision = 0
has_variable = zg361_pp_m171_active_panel_1''',
        180: '''var:zg361_pp_m178_final_decision = 0
has_variable = zg361_pp_m179_gap_id
var:zg361_pp_m179_feedback_owner = var:zg361_pp_m171_active_panel_1''',
        182: '''has_variable = zg361_pp_m181_primary_category
has_variable = zg361_pp_m181_evidence_id
var:zg361_pp_m181_result_grade_snapshot = var:zg361_pp_w_frozen_grade''',
        183: '''var:zg361_pp_m182_gate_status = 1
var:zg361_b2_pip_owner = var:zg361_case_w_owner
var:zg361_b2_pip_subject = this
var:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
var:zg361_b2_pip_case = var:zg361_case_w_case_serial''',
        184: '''var:zg361_pp_m182_gate_status = 1
var:zg361_pp_m183_goals_frozen = 1
var:zg361_pp_m183_manager_signed = 1
OR = {
\tvar:zg361_b2_pip_state = 2
\tvar:zg361_b2_pip_state = 3
\tvar:zg361_b2_pip_state = 4
}
var:zg361_pp_m183_subject_signed = 1''',
        185: "var:zg361_pp_m184_active_case = 1",
        186: '''var:zg361_pp_m185_audit_1_consumed = 1
OR = {
\tvar:zg361_pp_m185_midpoint_status = 1
\tvar:zg361_pp_m185_midpoint_status = 2
}''',
        187: '''var:zg361_pp_m185_audit_1_consumed = 1
has_variable = zg361_pp_m186_baseline_workload''',
        188: "var:zg361_pp_m187_graduation_status = 1",
        189: '''OR = {
\tAND = {
\t\tvar:zg361_pp_m187_graduation_status = 2
\t\tvar:zg361_pp_m188_skipped_first_failure = 1
\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\tvar:zg361_b2_pip_subject = this
\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\tvar:zg361_b2_pip_state = 4
\t\tvar:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case
\t}
\tAND = {
\t\tvar:zg361_pp_m188_audit_1_consumed = 1
\t\tvar:zg361_pp_m188_observation_closed = 1
\t\tvar:zg361_pp_m188_relapse_status = 1
\t}
}''',
        190: '''var:zg361_pp_m189_terminal_code = 2
has_variable = zg361_pp_m189_receiving_manager
var:zg361_pp_m189_receiving_manager = var:zg361_pp_w_receiving_manager
has_variable = zg361_pp_w_transfer_vacancy_id
var:zg361_pp_w_transfer_vacancy_active = 1
var:zg361_pp_w_transfer_vacancy_receiver = var:zg361_pp_m189_receiving_manager
var:zg361_pp_w_transfer_vacancy_owner = root
var:zg361_pp_w_transfer_vacancy_subject = this
var:zg361_transfer_vacancy_active = 1
var:zg361_transfer_vacancy_status = 1
var:zg361_transfer_vacancy_id = var:zg361_pp_w_transfer_vacancy_id
var:zg361_transfer_vacancy_owner = root
var:zg361_transfer_vacancy_subject = this
var:zg361_transfer_vacancy_receiver = var:zg361_pp_w_transfer_vacancy_receiver
var:zg361_transfer_vacancy_source_cycle = var:zg361_pp_w_transfer_source_cycle
var:zg361_transfer_vacancy_source_case = var:zg361_pp_w_transfer_source_case
var:zg361_transfer_vacancy_title = var:zg361_pp_w_transfer_vacancy_title
var:zg361_transfer_vacancy_maturity_cycle = var:zg361_pp_w_transfer_maturity_cycle
var:zg361_transfer_vacancy_position_kind = var:zg361_pp_w_transfer_position_kind
var:zg361_pp_w_transfer_position_kind = 1
primary_title = var:zg361_pp_w_transfer_vacancy_title
var:zg361_pp_w_transfer_vacancy_title = { holder = this }
var:zg361_transfer_hc_authorized = 1
var:zg361_transfer_hc_reserved = 1
var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized
var:zg361_transfer_hc_conserved = 1
var:zg361_pp_w_transfer_vacancy_receiver = {
\tliege = root
\tprimary_title.tier > prev.primary_title.tier
\tvassal_count < vassal_limit
\tNOT = { is_at_war_with = root }
\tNOT = { is_at_war_with = prev }
}
NOT = { is_at_war_with = var:zg361_pp_w_transfer_vacancy_receiver }
has_variable = zg361_pp_m183_goal_bundle_id
has_variable = zg361_pp_m184_support_status
has_variable = zg361_pp_m187_graduation_status
has_variable = zg361_pp_m183_subject_statement_code
var:zg361_pp_m189_receiving_manager = {
\tzg361_is_celestial_liege_trigger = yes
\tNOT = { this = root }
}''',
        191: "var:zg361_pp_m189_terminal_code = 3",
    }
    result = rows.get(mechanism_id, "always = yes")
    if mechanism_id == 161 and route == 2:
        result += '''
has_variable = zg361_pp_m161_filler_candidate
NOT = { var:zg361_pp_m161_filler_candidate = this }'''
    if mechanism_id == 166 and route == 1:
        result += '''
var:zg361_pp_m166_withdraw_intent = 1
NOT = { has_variable = zg361_pp_m160_prescreen_pass }
var:zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner
var:zg361_pp_m157_nomination_slot_cycle = var:zg361_case_u_cycle_serial
var:zg361_pp_m157_nomination_slot_case = var:zg361_case_u_case_serial'''
    if mechanism_id == 171 and route == 1:
        result += '''
has_variable = zg361_pp_v_panel_pool_4
NOT = { var:zg361_pp_v_panel_pool_4 = var:zg361_pp_m170_panelist_1 }
NOT = { var:zg361_pp_v_panel_pool_4 = var:zg361_pp_m170_panelist_2 }
NOT = { var:zg361_pp_v_panel_pool_4 = var:zg361_pp_m170_panelist_3 }'''
    if mechanism_id == 182:
        result += "\nvar:zg361_pp_w_pip_gate_candidate = 1"
    if mechanism_id == 183:
        result += "\nvar:zg361_pp_m182_gate_status = 1"
    if mechanism_id == 188 and route == 2:
        # The political route may label a successfully graduated subject too,
        # but it still cannot invent a relapse before the D+365 observation.
        result += "\nvar:zg361_pp_m187_graduation_status = 1"
    if mechanism_id == 189 and route == 1:
        result += '''
OR = {
\tAND = {
\t\tvar:zg361_pp_m187_graduation_status = 2
\t\tvar:zg361_pp_m188_skipped_first_failure = 1
\t}
\tvar:zg361_pp_m188_same_category_relapse = 1
}'''
    if mechanism_id == 189 and route == 2:
        result += "\nvar:zg361_pp_w_frozen_grade = 1"
    return result


def routed_dependency_guard(mechanism_id: int) -> str:
    return f'''trigger_if = {{
\tlimit = {{ scope:zg361_pp_route = 1 }}
\t{indent(business_dependency_conditions(mechanism_id, 1), 1).lstrip()}
}}
trigger_else_if = {{
\tlimit = {{ scope:zg361_pp_route = 2 }}
\t{indent(business_dependency_conditions(mechanism_id, 2), 1).lstrip()}
}}
trigger_else = {{ always = yes }}'''


def record_operation(mechanism: MechanismSpec, state: int) -> str:
    row = case_vars(mechanism.domain)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    return f'''if = {{
\tlimit = {{ NOT = {{ scope:zg361_pp_route = 3 }} }}
\tzg361_case_kernel_record_operation_effect = {{
\tOWNER_VAR = {row["owner"]}
\tSUBJECT_VAR = {row["subject"]}
\tCYCLE_VAR = {row["cycle"]}
\tCASE_VAR = {row["case"]}
\tSTATE_VAR = {row["state"]}
\tACTIVE_VAR = {row["active"]}
\tREVISION_VAR = {row["revision"]}
\tTIMELINE_VAR = {row["timeline"]}
\tFEEDBACK_VAR = {row["feedback"]}
\tLAST_OPERATION_VAR = zg361_case_{mechanism.domain}_last_operation
\tLAST_CHOICE_VAR = zg361_case_{mechanism.domain}_last_choice
\tRECEIPT_OWNER_VAR = {p}_receipt_owner
\tRECEIPT_SUBJECT_VAR = {p}_receipt_subject
\tRECEIPT_CYCLE_VAR = {p}_receipt_cycle
\tRECEIPT_CASE_VAR = {p}_receipt_case
\tRECEIPT_STATE_VAR = {p}_receipt_state
\tRECEIPT_CHOICE_VAR = {p}_receipt_route
\tTICKET_OWNER = $TICKET_OWNER$
\tTICKET_SUBJECT = $TICKET_SUBJECT$
\tTICKET_CYCLE = $TICKET_CYCLE$
\tTICKET_CASE = $TICKET_CASE$
\tTICKET_STATE = $TICKET_STATE$
\tCHOICE = scope:zg361_pp_route
\tOPERATION_ID = {mechanism.mechanism_id}
\t}}
}}
else = {{
\t# Route C is a policy-debt receipt, not a disguised business mutation.  It
\t# deliberately does not call record_operation and therefore cannot change
\t# the case revision, last operation, resource ledger, or typed payload.
\tset_variable = {{ name = zg361_case_kernel_applied value = 1 }}
\tset_variable = {{ name = {p}_receipt_owner value = $TICKET_OWNER$ }}
\tset_variable = {{ name = {p}_receipt_subject value = $TICKET_SUBJECT$ }}
\tset_variable = {{ name = {p}_receipt_cycle value = $TICKET_CYCLE$ }}
\tset_variable = {{ name = {p}_receipt_case value = $TICKET_CASE$ }}
\tset_variable = {{ name = {p}_receipt_state value = $TICKET_STATE$ }}
\tset_variable = {{ name = {p}_receipt_route value = 3 }}
}}'''


def transaction_call(mechanism: MechanismSpec, state: int, resource: str) -> str:
    row = case_vars(mechanism.domain)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}_{resource}"
    available = f"{PREFIX}_{mechanism.domain}_{resource}_available"
    reserved = f"{PREFIX}_{mechanism.domain}_{resource}_reserved"
    settled = f"{PREFIX}_{mechanism.domain}_{resource}_settled"
    return f'''zg361_case_kernel_reserve_transaction_effect = {{
\tOWNER_VAR = {row["owner"]}
\tSUBJECT_VAR = {row["subject"]}
\tCYCLE_VAR = {row["cycle"]}
\tCASE_VAR = {row["case"]}
\tSTATE_VAR = {row["state"]}
\tACTIVE_VAR = {row["active"]}
\tREVISION_VAR = {row["revision"]}
\tAVAILABLE_VAR = {available}
\tRESERVED_VAR = {reserved}
\tRECEIPT_AMOUNT_VAR = {p}_amount
\tRECEIPT_STATUS_VAR = {p}_status
\tRECEIPT_OWNER_VAR = {p}_owner
\tRECEIPT_CYCLE_VAR = {p}_cycle
\tRECEIPT_CASE_VAR = {p}_case
\tTICKET_OWNER = $TICKET_OWNER$
\tTICKET_SUBJECT = $TICKET_SUBJECT$
\tTICKET_CYCLE = $TICKET_CYCLE$
\tTICKET_CASE = $TICKET_CASE$
\tTICKET_STATE = $TICKET_STATE$
\tAMOUNT = 1
}}
if = {{
\t# Authority contract: route A remains an exact reservation (status 1);
\t# route B settles at operation time (status 2).
\tlimit = {{ var:zg361_case_kernel_applied = 1 scope:zg361_pp_route = 2 }}
\tzg361_case_kernel_settle_transaction_effect = {{
\t\tOWNER_VAR = {row["owner"]}
\t\tSUBJECT_VAR = {row["subject"]}
\t\tCYCLE_VAR = {row["cycle"]}
\t\tCASE_VAR = {row["case"]}
\t\tSTATE_VAR = {row["state"]}
\t\tACTIVE_VAR = {row["active"]}
\t\tREVISION_VAR = {row["revision"]}
\t\tRESERVED_VAR = {reserved}
\t\tSETTLED_VAR = {settled}
\t\tRECEIPT_AMOUNT_VAR = {p}_amount
\t\tRECEIPT_STATUS_VAR = {p}_status
\t\tTICKET_OWNER = $TICKET_OWNER$
\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\tTICKET_CASE = $TICKET_CASE$
\t\tTICKET_STATE = $TICKET_STATE$
\t}}
}}'''


def dual_cost_guard(mechanism_id: int) -> str:
    if mechanism_id not in DUAL_COST_IDS:
        return "always = yes"
    route = DUAL_COST_ROUTE_BY_ID[mechanism_id]
    return f'''trigger_if = {{
\tlimit = {{ scope:zg361_pp_route = {route} }}
\tvar:zg361_pp_cost_owner = {{
\t\tgovernment_has_flag = government_has_treasury
\t\ttreasury >= 5
\t\tgold >= 5
\t}}
}}
trigger_else = {{ always = yes }}'''


def dual_cost_write(mechanism: MechanismSpec) -> str:
    if mechanism.mechanism_id not in DUAL_COST_IDS:
        return ""
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    route = DUAL_COST_ROUTE_BY_ID[mechanism.mechanism_id]
    return f'''if = {{
\tlimit = {{ scope:zg361_pp_route = {route} }}
\tvar:zg361_case_{mechanism.domain}_owner = {{
\t\tremove_treasury = 5
\t\tremove_short_term_gold = 5
\t}}
\tadd_gold = 10
\tset_variable = {{ name = {p}_treasury_paid value = 5 }}
\tset_variable = {{ name = {p}_personal_paid value = 5 }}
\tset_variable = {{ name = {p}_subject_received value = 10 }}
\tset_variable = {{ name = {p}_dual_payment_conserved value = 1 }}
}}'''


def business_object_identity_write(mechanism: MechanismSpec, state: int) -> str:
    """Freeze an explicit owner/subject/cycle/case/state business identity.

    The case-kernel operation receipt already carries this tuple, but typed
    downstream objects must not rely on whatever case happens to be current
    when a D+365 event wakes up.  Keeping the tuple beside every payload also
    gives MCP a stable object key without requiring 46 bespoke schemas.
    """

    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    row = case_vars(mechanism.domain)
    return f'''set_variable = {{ name = {p}_object_owner value = var:{row["owner"]} }}
set_variable = {{ name = {p}_object_subject value = this }}
set_variable = {{ name = {p}_object_cycle value = var:{row["cycle"]} }}
set_variable = {{ name = {p}_object_case value = var:{row["case"]} }}
set_variable = {{ name = {p}_object_state value = {state} }}'''


def render_m189_no_relapse_skip() -> str:
    """Close the conditional terminal mechanism when the observation is clean.

    #189 is not a policy breach when no same-category relapse happened; it is
    simply inapplicable.  This explicit receipt lets the stage and completed
    count close without inventing a second PIP, transfer, exit, policy debt or
    delayed audit.
    """

    return '''zg361_pp_m189_skip_no_relapse_effect = {
\tif = {
\t\tlimit = {
\t\t\tzg361_case_kernel_full_guard_trigger = {
\t\t\t\tOWNER_VAR = zg361_case_w_owner
\t\t\t\tSUBJECT_VAR = zg361_case_w_subject
\t\t\t\tCYCLE_VAR = zg361_case_w_cycle_serial
\t\t\t\tCASE_VAR = zg361_case_w_case_serial
\t\t\t\tSTATE_VAR = zg361_case_w_state
\t\t\t\tACTIVE_VAR = zg361_case_w_active
\t\t\t\tEXPECTED_OWNER = var:zg361_case_w_owner
\t\t\t\tEXPECTED_SUBJECT = this
\t\t\t\tEXPECTED_CYCLE = var:zg361_case_w_cycle_serial
\t\t\t\tEXPECTED_CASE = var:zg361_case_w_case_serial
\t\t\t\tEXPECTED_STATE = 4
\t\t\t}
\t\t\tvar:zg361_pp_m188_audit_1_consumed = 1
\t\t\tvar:zg361_pp_m188_relapse_status = 2
\t\t\tvar:zg361_pp_m189_receipt_active = 0
\t\t}
\t\tset_variable = { name = zg361_pp_m189_receipt_owner value = var:zg361_case_w_owner }
\t\tset_variable = { name = zg361_pp_m189_receipt_subject value = this }
\t\tset_variable = { name = zg361_pp_m189_receipt_cycle value = var:zg361_case_w_cycle_serial }
\t\tset_variable = { name = zg361_pp_m189_receipt_case value = var:zg361_case_w_case_serial }
\t\tset_variable = { name = zg361_pp_m189_receipt_state value = 4 }
\t\tset_variable = { name = zg361_pp_m189_receipt_route value = 0 }
\t\tset_variable = { name = zg361_pp_m189_receipt_active value = 1 }
\t\tset_variable = { name = zg361_pp_m189_route value = 0 }
\t\tset_variable = { name = zg361_pp_m189_terminal_fork value = 0 }
\t\tset_variable = { name = zg361_pp_m189_terminal_code value = 0 }
\t\tset_variable = { name = zg361_pp_m189_skipped_no_relapse value = 1 }
\t\tset_variable = { name = zg361_pp_m189_visible_outcome_code value = 4 }
\t\tset_variable = { name = zg361_pp_m189_audit_1_state value = 2 }
\t\tset_variable = { name = zg361_pp_m189_audit_1_consumed value = 1 }
\t\tzg361_pp_m189_consume_effect = yes
\t}
}'''


def render_m188_first_failure_skip() -> str:
    """Close post-graduation observation when the first PIP already failed.

    A first-PIP failure is itself a terminal-fork input.  It must not wait a
    year for, or manufacture, a post-graduation relapse.  This exact route-0
    receipt closes #188 as not applicable while retaining the failed #187
    evidence that authorizes #189 A/B.
    """

    return '''zg361_pp_m188_skip_first_failure_effect = {
\tif = {
\t\tlimit = {
\t\t\tzg361_case_kernel_full_guard_trigger = {
\t\t\t\tOWNER_VAR = zg361_case_w_owner
\t\t\t\tSUBJECT_VAR = zg361_case_w_subject
\t\t\t\tCYCLE_VAR = zg361_case_w_cycle_serial
\t\t\t\tCASE_VAR = zg361_case_w_case_serial
\t\t\t\tSTATE_VAR = zg361_case_w_state
\t\t\t\tACTIVE_VAR = zg361_case_w_active
\t\t\t\tEXPECTED_OWNER = var:zg361_case_w_owner
\t\t\t\tEXPECTED_SUBJECT = this
\t\t\t\tEXPECTED_CYCLE = var:zg361_case_w_cycle_serial
\t\t\t\tEXPECTED_CASE = var:zg361_case_w_case_serial
\t\t\t\tEXPECTED_STATE = 4
\t\t\t}
\t\t\tvar:zg361_pp_m187_graduation_status = 2
\t\t\tvar:zg361_b2_pip_state = 4
\t\t\tvar:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case
\t\t\tvar:zg361_pp_m188_receipt_active = 0
\t\t}
\t\tset_variable = { name = zg361_pp_m188_receipt_owner value = var:zg361_case_w_owner }
\t\tset_variable = { name = zg361_pp_m188_receipt_subject value = this }
\t\tset_variable = { name = zg361_pp_m188_receipt_cycle value = var:zg361_case_w_cycle_serial }
\t\tset_variable = { name = zg361_pp_m188_receipt_case value = var:zg361_case_w_case_serial }
\t\tset_variable = { name = zg361_pp_m188_receipt_state value = 4 }
\t\tset_variable = { name = zg361_pp_m188_receipt_route value = 0 }
\t\tset_variable = { name = zg361_pp_m188_receipt_active value = 1 }
\t\tset_variable = { name = zg361_pp_m188_route value = 0 }
\t\tset_variable = { name = zg361_pp_m188_relapse_window value = 0 }
\t\tset_variable = { name = zg361_pp_m188_relapse_status value = 0 }
\t\tset_variable = { name = zg361_pp_m188_skipped_first_failure value = 1 }
\t\tset_variable = { name = zg361_pp_m188_visible_outcome_code value = 4 }
\t\tset_variable = { name = zg361_pp_m188_audit_1_state value = 2 }
\t\tset_variable = { name = zg361_pp_m188_audit_1_consumed value = 1 }
\t\tzg361_pp_m188_consume_effect = yes
\t}
}'''


def semantic_write(mechanism: MechanismSpec) -> str:
    """Behavior-specific writes consumed by later mechanisms or projections."""

    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    d = mechanism.domain
    snippets: dict[int, str] = {
        146: f'''set_variable = {{ name = {p}_frozen_grade value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_disclosed_grade value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_understood_grade value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_understanding_gap value = 0 }}
set_variable = {{ name = {p}_frozen_evidence_hash value = var:zg361_pp_t_frozen_evidence_hash }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_understood_grade value = 0 }} set_variable = {{ name = {p}_understanding_gap value = 1 }} }}''',
        147: f'''# The delivered result case is the cross-product business identity.  The
# T case receipt below remains the internal case-kernel ticket; this serial
# gives promotion and compensation one stable, positive correlation key.
set_variable = {{ name = {p}_receipt_serial value = var:zg361_pp_t_result_case }}
set_variable = {{ name = {p}_receipt_revision value = var:zg361_case_t_revision }}
set_variable = {{ name = {p}_evidence_hash_consumed value = var:zg361_pp_t_frozen_evidence_hash }}
set_variable = {{ name = {p}_supported_praise_n value = 1 }}
set_variable = {{ name = {p}_supported_critique_n value = 1 }}
set_variable = {{ name = {p}_unsupported_sentence_n value = 0 }}
set_variable = {{ name = {p}_quality_credit value = 2 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_supported_praise_n value = 0 }} set_variable = {{ name = {p}_supported_critique_n value = 0 }} set_variable = {{ name = {p}_unsupported_sentence_n value = 2 }} set_variable = {{ name = {p}_quality_credit value = 0 }} }}''',
        148: f'''set_variable = {{ name = {p}_evidence_snapshot value = var:zg361_pp_t_frozen_evidence_hash }}
set_variable = {{ name = {p}_rating_snapshot value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_step_order value = 1 }}
set_variable = {{ name = {p}_facts_acknowledged value = 1 }}
set_variable = {{ name = {p}_dispute_open value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_step_order value = 2 }} set_variable = {{ name = {p}_dispute_open value = 1 }} }}''',
        149: f'''set_variable = {{ name = {p}_grade_before_terms value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_grade_after_terms value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_obligation_id value = {{ value = var:zg361_case_t_case_serial multiply = 1000 add = 149 }} }}
set_variable = {{ name = {p}_term_owner value = var:zg361_case_t_owner }}
set_variable = {{ name = {p}_term_due_days value = 180 }}
set_variable = {{ name = {p}_obligation_status value = 1 }}
set_variable = {{ name = {p}_funded value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 1 }} set_variable = {{ name = {p}_funded value = 1 }} }}''',
        150: f'''set_variable = {{ name = {p}_obligation_id value = {{ value = var:zg361_case_t_case_serial multiply = 1000 add = 150 }} }}
set_variable = {{ name = {p}_sacrifice_cycle value = var:zg361_case_t_cycle_serial }}
set_variable = {{ name = {p}_promise_owner value = var:zg361_case_t_owner }}
set_variable = {{ name = {p}_promise_due_days value = 365 }}
set_variable = {{ name = {p}_obligation_status value = 1 }}
set_variable = {{ name = {p}_written value = 1 }}
set_variable = {{ name = {p}_funded value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_written value = 0 }} set_variable = {{ name = {p}_funded value = 0 }} }}''',
        151: f'''set_variable = {{ name = {p}_delivered value = 1 }}
set_variable = {{ name = {p}_agreed value = 0 }}
set_variable = {{ name = {p}_disputed value = 0 }}
set_variable = {{ name = {p}_witness_required value = 0 }}
set_variable = {{ name = {p}_appeal_eligible value = 1 }}
set_variable = {{ name = {p}_appeal_due_days value = 90 }}
set_variable = {{ name = {p}_grade_at_delivery value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_non_aggravation_grade value = var:zg361_pp_t_frozen_grade }}
set_variable = {{ name = {p}_non_aggravation_ok value = 1 }}
if = {{ limit = {{ var:{p}_subject_response = 1 }} set_variable = {{ name = {p}_agreed value = 1 }} }}
else_if = {{ limit = {{ var:{p}_subject_response = 2 }} set_variable = {{ name = {p}_disputed value = 1 }} set_variable = {{ name = {p}_appeal_filed value = 1 }} }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_suppressed_objection value = 1 }} set_variable = {{ name = {p}_procedural_debt value = 1 }} }}''',
        152: f'''set_variable = {{ name = {p}_specificity value = 25 }}
set_variable = {{ name = {p}_controllability value = 25 }}
set_variable = {{ name = {p}_deadline_quality value = 25 }}
set_variable = {{ name = {p}_resource_quality value = 25 }}
set_variable = {{ name = {p}_total_score value = 100 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_specificity value = 5 }} set_variable = {{ name = {p}_controllability value = 5 }} set_variable = {{ name = {p}_deadline_quality value = 0 }} set_variable = {{ name = {p}_resource_quality value = 0 }} set_variable = {{ name = {p}_total_score value = 10 }} }}''',
        153: f'''set_variable = {{ name = {p}_action_owner value = var:zg361_case_t_owner }}
set_variable = {{ name = {p}_original_due_days value = 90 }}
set_variable = {{ name = {p}_current_due_days value = 90 }}
set_variable = {{ name = {p}_deadline_revision value = 1 }}
set_variable = {{ name = {p}_terminal_status value = 0 }}
set_variable = {{ name = {p}_acceptance_evidence value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_current_due_days value = 120 }} set_variable = {{ name = {p}_deadline_revision value = 2 }} set_variable = {{ name = {p}_change_reason value = 1 }} }}''',
        154: f'''set_variable = {{ name = {p}_minutes_id value = {{ value = var:zg361_case_t_case_serial multiply = 1000 add = 154 }} }}
set_variable = {{ name = {p}_mode value = 1 }}
set_variable = {{ name = {p}_version value = 1 }}
set_variable = {{ name = {p}_append_only value = 1 }}
set_variable = {{ name = {p}_evidence_index value = var:zg361_pp_t_frozen_evidence_hash }}
set_variable = {{ name = {p}_correction_revision value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_mode value = 2 }} }}''',
        155: f'''set_variable = {{ name = {p}_public_achievement_fields value = 1 }}
set_variable = {{ name = {p}_public_grade_fields value = 0 }}
set_variable = {{ name = {p}_private_sensitive_fields value = 1 }}
set_variable = {{ name = {p}_subject_projection_acl value = 1 }}
set_variable = {{ name = {p}_team_projection_acl value = 2 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} add_stress = minor_stress_gain set_variable = {{ name = {p}_public_grade_fields value = 1 }} set_variable = {{ name = {p}_public_shaming value = 1 }} set_variable = {{ name = {p}_retaliation_risk value = 1 }} }}''',
        156: f'''set_variable = {{ name = {p}_briefing_id value = {{ value = var:zg361_case_t_case_serial multiply = 1000 add = 156 }} }}
set_variable = {{ name = {p}_distribution_rule_explained value = 1 }}
set_variable = {{ name = {p}_common_issue_n value = 1 }}
set_variable = {{ name = {p}_resource_plan_explained value = 1 }}
set_variable = {{ name = {p}_completion_receipt value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_distribution_rule_explained value = 0 }} set_variable = {{ name = {p}_resource_plan_explained value = 0 }} set_variable = {{ name = {p}_completion_receipt value = 0 }} set_variable = {{ name = {p}_rumor_debt value = 1 }} }}''',
        157: f'''save_temporary_scope_as = zg361_pp_nomination_candidate
set_variable = {{ name = {p}_eligibility_grade value = var:zg361_pp_u_frozen_grade }}
set_variable = {{ name = {p}_eligible_at_nomination value = var:zg361_pp_u_candidate_eligible }}
set_variable = {{ name = {p}_packet_candidate value = this }}
set_variable = {{ name = {p}_packet_owner value = var:zg361_case_u_owner }}
set_variable = {{ name = {p}_packet_cycle value = var:zg361_case_u_cycle_serial }}
set_variable = {{ name = {p}_packet_case value = var:zg361_case_u_case_serial }}
set_variable = {{ name = {p}_packet_source value = scope:zg361_pp_route }}
set_variable = {{ name = {p}_packet_active value = 1 }}
set_variable = {{ name = {p}_packet_status value = 1 }}
set_variable = {{ name = {p}_sponsor_bound value = 1 }}
set_variable = {{ name = {p}_manager_opinion_bound value = 1 }}
var:zg361_case_u_owner = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = zg361_pp_u_shelving_candidate
\t\t\tvar:zg361_pp_u_shelving_candidate = scope:zg361_pp_nomination_candidate
\t\t\tvar:zg361_pp_u_shelving_active = 1
\t\t}}
\t\tset_variable = {{ name = zg361_pp_u_shelving_nominated value = 1 }}
\t\tset_variable = {{ name = zg361_pp_u_shelving_active value = 0 }}
\t}}
}}''',
        158: f'''set_variable = {{ name = {p}_packet_candidate_consumed value = var:zg361_pp_m157_packet_candidate }}
set_variable = {{ name = {p}_packet_case_consumed value = var:zg361_pp_m157_receipt_case }}
set_variable = {{ name = {p}_quota_total value = var:zg361_pp_u_nomination_slot_authorized }}
set_variable = {{ name = {p}_quota_used value = var:zg361_pp_u_nomination_slot_reserved }}
change_variable = {{ name = {p}_quota_used add = var:zg361_pp_u_nomination_slot_settled }}
set_variable = {{ name = {p}_quota_remaining value = var:zg361_pp_u_nomination_slot_available }}
set_variable = {{ name = {p}_quota_returned value = 0 }}
set_variable = {{ name = {p}_quota_partition value = var:{p}_quota_used }}
change_variable = {{ name = {p}_quota_partition add = var:{p}_quota_remaining }}
change_variable = {{ name = {p}_quota_partition add = var:{p}_quota_returned }}
set_variable = {{ name = {p}_quota_conserved value = 0 }}
if = {{ limit = {{ var:{p}_quota_partition = var:{p}_quota_total }} set_variable = {{ name = {p}_quota_conserved value = 1 }} }}
set_variable = {{ name = {p}_rank value = 1 }}''',
        159: f'''save_temporary_scope_as = zg361_pp_shelved_candidate
set_variable = {{ name = {p}_successor_plan value = 1 }}
set_variable = {{ name = {p}_nomination_due_cycles value = 1 }}
var:zg361_case_u_owner = {{
\tset_variable = {{ name = zg361_pp_u_shelving_candidate value = scope:zg361_pp_shelved_candidate }}
\tset_variable = {{ name = zg361_pp_u_shelving_owner value = this }}
\tset_variable = {{ name = zg361_pp_u_shelving_due_cycle value = {{ value = var:zg361_review_serial add = 1 }} }}
\tset_variable = {{ name = zg361_pp_u_shelving_last_penalty_cycle value = 0 }}
\tset_variable = {{ name = zg361_pp_u_shelving_resource value = 1 }}
\tif = {{
\t\tlimit = {{ scope:zg361_pp_route = 1 }}
\t\t# #157 already nominated this subject on the evidence-led path.
\t\tset_variable = {{ name = zg361_pp_u_shelving_active value = 0 }}
\t\tset_variable = {{ name = zg361_pp_u_shelving_nominated value = 1 }}
\t}}
\telse = {{
\t\t# Political shelving persists on the manager and is charged once per
\t\t# later overdue cycle until #157 nominates this same character.
\t\tset_variable = {{ name = zg361_pp_u_shelving_active value = 1 }}
\t\tset_variable = {{ name = zg361_pp_u_shelving_nominated value = 0 }}
\t}}
}}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_successor_plan value = 0 }} set_variable = {{ name = {p}_talent_debt value = 1 }} }}''',
        160: f'''set_variable = {{ name = {p}_packet_candidate_consumed value = var:zg361_pp_m157_packet_candidate }}
set_variable = {{ name = {p}_quota_used_consumed value = var:zg361_pp_m158_quota_used }}
set_variable = {{ name = {p}_filler_consumed value = var:zg361_pp_m161_filler }}
set_variable = {{ name = {p}_exception_vote_consumed value = var:zg361_pp_m162_admission_vote_frozen }}
set_variable = {{ name = {p}_window_consumed value = var:zg361_pp_m163_window_cycles }}
set_variable = {{ name = {p}_cross_team_share_consumed value = var:zg361_pp_m164_candidate_share }}
set_variable = {{ name = {p}_trial_authority_consumed value = var:zg361_pp_m165_authority_bound }}
set_variable = {{ name = {p}_withdrawal_status_consumed value = var:zg361_pp_m166_withdrawn_before_prescreen }}
set_variable = {{ name = {p}_rubric_material value = 80 }}
set_variable = {{ name = {p}_rubric_level value = 80 }}
set_variable = {{ name = {p}_rubric_strategy value = 80 }}
set_variable = {{ name = {p}_packet_score value = 240 }}
set_variable = {{ name = {p}_prescreen_pass value = 1 }}
set_variable = {{ name = {p}_promotion_boundary value = 180 }}
set_variable = {{ name = {p}_boundary_pass value = 1 }}
set_variable = {{ name = {p}_rejection_reason value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_packet_score value = 120 }} set_variable = {{ name = {p}_prescreen_pass value = 0 }} set_variable = {{ name = {p}_boundary_pass value = 0 }} set_variable = {{ name = {p}_rejection_reason value = 2 }} set_variable = {{ name = {p}_political_cut value = 1 }} }}''',
        161: f'''set_variable = {{ name = {p}_filler value = 0 }}
set_variable = {{ name = {p}_preparation_hours value = 0 }}
set_variable = {{ name = {p}_main_packet_candidate value = var:zg361_pp_m157_packet_candidate }}
if = {{
\tlimit = {{ scope:zg361_pp_route = 2 }}
\tset_variable = {{ name = {p}_filler value = 1 }}
\tset_variable = {{ name = {p}_filler_packet_candidate value = var:{p}_filler_candidate }}
\tset_variable = {{ name = {p}_preparation_hours value = 12 }}
\tset_variable = {{ name = {p}_fairness_debt value = 1 }}
\tset_variable = {{ name = {p}_filler_disclosed value = 1 }}
}}
set_variable = {{ name = {p}_quota_used_after value = var:zg361_pp_u_nomination_slot_reserved }}
change_variable = {{ name = {p}_quota_used_after add = var:zg361_pp_u_nomination_slot_settled }}
set_variable = {{ name = {p}_quota_remaining_after value = var:zg361_pp_u_nomination_slot_available }}
set_variable = {{ name = zg361_pp_m158_quota_used value = var:{p}_quota_used_after }}
set_variable = {{ name = zg361_pp_m158_quota_remaining value = var:{p}_quota_remaining_after }}
set_variable = {{ name = zg361_pp_m158_quota_partition value = var:zg361_pp_m158_quota_used }}
change_variable = {{ name = zg361_pp_m158_quota_partition add = var:zg361_pp_m158_quota_remaining }}
change_variable = {{ name = zg361_pp_m158_quota_partition add = var:zg361_pp_m158_quota_returned }}
set_variable = {{ name = zg361_pp_m158_quota_conserved value = 0 }}
if = {{ limit = {{ var:zg361_pp_m158_quota_partition = var:zg361_pp_m158_quota_total }} set_variable = {{ name = zg361_pp_m158_quota_conserved value = 1 }} }}''',
        162: f'''set_variable = {{ name = {p}_candidate_consumed value = var:zg361_pp_m157_packet_candidate }}
set_variable = {{ name = {p}_tenure_required_days value = 730 }}
set_variable = {{ name = {p}_tenure_actual_days value = 365 }}
set_variable = {{ name = {p}_tenure_met value = 0 }}
set_variable = {{ name = {p}_exception_slots_total value = 1 }}
set_variable = {{ name = {p}_exception_slots_used value = 1 }}
set_variable = {{ name = {p}_admission_vote_frozen value = 1 }}
set_variable = {{ name = {p}_exception_admitted value = 1 }}
set_variable = {{ name = {p}_capability_review_open value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_credibility_debt value = 1 }} }}''',
        163: f'''set_variable = {{ name = {p}_window_cycles value = 2 }}
set_variable = {{ name = {p}_window_frozen_cycle value = var:zg361_case_u_cycle_serial }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_window_cycles value = 1 }} set_variable = {{ name = {p}_window_audit_diff value = 1 }} }}''',
        164: f'''set_variable = {{ name = {p}_candidate_share value = 40 }}
set_variable = {{ name = {p}_peer_share value = 60 }}
set_variable = {{ name = {p}_share_check value = 100 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_candidate_share value = 100 }} set_variable = {{ name = {p}_peer_share value = 0 }} set_variable = {{ name = {p}_attribution_debt value = 1 }} }}''',
        165: f'''set_variable = {{ name = {p}_authority_bound value = 1 }}
set_variable = {{ name = {p}_trial_due_days value = 90 }}
set_variable = {{ name = {p}_exit_condition_bound value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_authority_bound value = 0 }} set_variable = {{ name = {p}_level_debt value = 1 }} }}''',
        166: f'''if = {{
\tlimit = {{ scope:zg361_pp_route = 1 }}
\tzg361_case_kernel_refund_transaction_effect = {{
\t\tOWNER_VAR = zg361_case_u_owner
\t\tSUBJECT_VAR = zg361_case_u_subject
\t\tCYCLE_VAR = zg361_case_u_cycle_serial
\t\tCASE_VAR = zg361_case_u_case_serial
\t\tSTATE_VAR = zg361_case_u_state
\t\tACTIVE_VAR = zg361_case_u_active
\t\tREVISION_VAR = zg361_case_u_revision
\t\tAVAILABLE_VAR = zg361_pp_u_nomination_slot_available
\t\tRESERVED_VAR = zg361_pp_u_nomination_slot_reserved
\t\tSETTLED_VAR = zg361_pp_u_nomination_slot_settled
\t\tRECEIPT_AMOUNT_VAR = zg361_pp_m157_nomination_slot_amount
\t\tRECEIPT_STATUS_VAR = zg361_pp_m157_nomination_slot_status
\t\tTICKET_OWNER = var:zg361_case_u_owner
\t\tTICKET_SUBJECT = this
\t\tTICKET_CYCLE = var:zg361_case_u_cycle_serial
\t\tTICKET_CASE = var:zg361_case_u_case_serial
\t\tTICKET_STATE = 3
\t}}
\tif = {{
\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
\t\tset_variable = {{ name = {p}_withdrawn_before_prescreen value = 1 }}
\t\tset_variable = {{ name = {p}_quota_returned value = 1 }}
\t\tset_variable = {{ name = {p}_verified_artifacts_reusable value = 1 }}
\t\tset_variable = {{ name = {p}_readiness_risk value = 1 }}
\t\tset_variable = {{ name = {p}_nomination_slot_refunded value = 1 }}
\t\tset_variable = {{ name = {p}_packet_active_after value = 0 }}
\t\tset_variable = {{ name = zg361_pp_m157_packet_active value = 0 }}
\t\tset_variable = {{ name = zg361_pp_m157_packet_status value = 5 }}
\t\tset_variable = {{ name = zg361_pp_m158_quota_used value = var:zg361_pp_u_nomination_slot_reserved }}
\t\tchange_variable = {{ name = zg361_pp_m158_quota_used add = var:zg361_pp_u_nomination_slot_settled }}
\t\tset_variable = {{ name = zg361_pp_m158_quota_remaining value = var:zg361_pp_u_nomination_slot_available }}
\t\tset_variable = {{ name = zg361_pp_m158_quota_partition value = var:zg361_pp_m158_quota_used }}
\t\tchange_variable = {{ name = zg361_pp_m158_quota_partition add = var:zg361_pp_m158_quota_remaining }}
\t\tset_variable = {{ name = zg361_pp_m158_quota_conserved value = 0 }}
\t\tif = {{ limit = {{ var:zg361_pp_m158_quota_partition = var:zg361_pp_m158_quota_total }} set_variable = {{ name = zg361_pp_m158_quota_conserved value = 1 }} }}
\t}}
}}
else = {{
\tset_variable = {{ name = {p}_withdrawn_before_prescreen value = 0 }}
\tset_variable = {{ name = {p}_quota_returned value = 0 }}
\tset_variable = {{ name = {p}_packet_active_after value = 1 }}
\tset_variable = {{ name = {p}_push_forward value = 1 }}
}}''',
        167: f'''set_variable = {{ name = {p}_sponsor_strength value = 1 }}
set_variable = {{ name = {p}_observation_id value = {{ value = var:zg361_case_u_case_serial multiply = 1000 add = 167 }} }}
set_variable = {{ name = {p}_observation_candidate value = var:zg361_pp_m160_packet_candidate_consumed }}
set_variable = {{ name = {p}_observation_due_cycle value = {{ value = var:zg361_case_u_cycle_serial add = 1 }} }}
set_variable = {{ name = {p}_observation_settled value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_sponsor_strength value = 3 }} }}''',
        168: f'''set_variable = {{ name = {p}_attempt_id value = {{ value = var:zg361_case_u_case_serial multiply = 1000 add = 168 }} }}
set_variable = {{ name = {p}_difficulty value = 3 }}
set_variable = {{ name = {p}_prescreen_pass_snapshot value = var:zg361_pp_m160_prescreen_pass }}
set_variable = {{ name = {p}_sponsor_observation_id value = var:zg361_pp_m167_observation_id }}
set_variable = {{ name = {p}_observation_due_cycle value = {{ value = var:zg361_case_u_cycle_serial add = 1 }} }}
set_variable = {{ name = {p}_sample_pending value = 1 }}
set_variable = {{ name = {p}_sample_settled value = 0 }}
set_variable = {{ name = {p}_omitted_qualified value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_difficulty value = 1 }} set_variable = {{ name = {p}_omitted_qualified value = 1 }} set_variable = {{ name = {p}_risk_avoidance_debt value = 1 }} }}''',
        169: f'''set_variable = {{ name = {p}_expert_weight value = 60 }}
set_variable = {{ name = {p}_external_weight value = 40 }}
if = {{ limit = {{ has_variable = zg361_pp_m163_window_cycles }} set_variable = {{ name = {p}_observation_window_consumed value = var:zg361_pp_m163_window_cycles }} }}
if = {{ limit = {{ has_variable = zg361_pp_m164_candidate_share }} set_variable = {{ name = {p}_cross_team_share_consumed value = var:zg361_pp_m164_candidate_share }} }}
if = {{ limit = {{ has_variable = zg361_pp_m165_authority_bound }} set_variable = {{ name = {p}_trial_authority_consumed value = var:zg361_pp_m165_authority_bound }} }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_expert_weight value = 80 }} set_variable = {{ name = {p}_external_weight value = 20 }} set_variable = {{ name = {p}_familiarity_risk value = 1 }} }}
set_variable = {{ name = {p}_weight_check value = var:{p}_expert_weight }}
change_variable = {{ name = {p}_weight_check add = var:{p}_external_weight }}''',
        170: f'''set_variable = {{ name = {p}_panel_seed value = var:zg361_case_v_case_serial }}
set_variable = {{ name = {p}_panelist_1 value = var:zg361_pp_v_panel_pool_1 }}
set_variable = {{ name = {p}_panelist_2 value = var:zg361_pp_v_panel_pool_2 }}
set_variable = {{ name = {p}_panelist_3 value = var:zg361_pp_v_panel_pool_3 }}
set_variable = {{ name = {p}_panel_size value = 3 }}
set_variable = {{ name = {p}_panel_unique value = 0 }}
if = {{
\tlimit = {{
\t\tNOT = {{ var:{p}_panelist_1 = var:{p}_panelist_2 }}
\t\tNOT = {{ var:{p}_panelist_1 = var:{p}_panelist_3 }}
\t\tNOT = {{ var:{p}_panelist_2 = var:{p}_panelist_3 }}
\t}}
\tset_variable = {{ name = {p}_panel_unique value = 1 }}
}}
set_variable = {{ name = {p}_familiar_seats value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_familiar_seats value = 1 }} }}
set_variable = {{ name = {p}_familiarity_margin value = var:{p}_panel_size }}
change_variable = {{ name = {p}_familiarity_margin add = {{ value = var:{p}_familiar_seats multiply = -2 }} }}
set_variable = {{ name = {p}_familiar_minority_ok value = 0 }}
if = {{ limit = {{ var:{p}_familiarity_margin > 0 }} set_variable = {{ name = {p}_familiar_minority_ok value = 1 }} }}
set_variable = {{ name = {p}_selection_checksum value = var:{p}_panel_seed }}
change_variable = {{ name = {p}_selection_checksum add = var:{p}_panel_size }}
set_variable = {{ name = {p}_selection_replay_ok value = 1 }}''',
        171: f'''set_variable = {{ name = {p}_conflicts_disclosed value = 1 }}
set_variable = {{ name = {p}_recused_panelist value = var:zg361_pp_m170_panelist_1 }}
set_variable = {{ name = {p}_replacement_panelist value = var:zg361_pp_v_panel_pool_4 }}
set_variable = {{ name = {p}_active_panel_1 value = var:zg361_pp_v_panel_pool_4 }}
set_variable = {{ name = {p}_active_panel_2 value = var:zg361_pp_m170_panelist_2 }}
set_variable = {{ name = {p}_active_panel_3 value = var:zg361_pp_m170_panelist_3 }}
set_variable = {{ name = {p}_active_panel_count value = 3 }}
set_variable = {{ name = {p}_active_panel_revision value = {{ value = var:zg361_case_v_revision add = 1 }} }}
set_variable = {{ name = {p}_replacement_same_kind value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_conflicts_disclosed value = 0 }} set_variable = {{ name = {p}_active_panel_1 value = var:zg361_pp_m170_panelist_1 }} set_variable = {{ name = {p}_rereview_debt value = 1 }} set_variable = {{ name = {p}_active_panel_revision value = {{ value = var:{p}_active_panel_revision add = 1 }} }} }}''',
        172: f'''set_variable = {{ name = {p}_rule_frozen_before_vote value = 1 }}
set_variable = {{ name = {p}_decision_rule_code value = 2 }}
set_variable = {{ name = {p}_veto_reason_required value = 1 }}
set_variable = {{ name = {p}_expert_weight_consumed value = var:zg361_pp_m169_expert_weight }}
set_variable = {{ name = {p}_external_weight_consumed value = var:zg361_pp_m169_external_weight }}
set_variable = {{ name = {p}_panel_weight_check value = var:{p}_expert_weight_consumed }}
change_variable = {{ name = {p}_panel_weight_check add = var:{p}_external_weight_consumed }}
set_variable = {{ name = {p}_active_panel_revision_consumed value = var:zg361_pp_m171_active_panel_revision }}
set_variable = {{ name = {p}_active_panel_count_consumed value = var:zg361_pp_m171_active_panel_count }}
set_variable = {{ name = {p}_active_panel_1_consumed value = var:zg361_pp_m171_active_panel_1 }}
set_variable = {{ name = {p}_active_panel_2_consumed value = var:zg361_pp_m171_active_panel_2 }}
set_variable = {{ name = {p}_active_panel_3_consumed value = var:zg361_pp_m171_active_panel_3 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_decision_rule_code value = 3 }} set_variable = {{ name = {p}_rule_drift_debt value = 1 }} }}''',
        173: f'''set_variable = {{ name = {p}_blind_score value = 78 }}
set_variable = {{ name = {p}_blind_score_frozen value = 1 }}
set_variable = {{ name = {p}_identity_fields_hidden value = 1 }}
set_variable = {{ name = {p}_live_score value = 72 }}
set_variable = {{ name = {p}_unblind_after_freeze value = 1 }}
set_variable = {{ name = {p}_active_panel_revision_consumed value = var:zg361_pp_m172_active_panel_revision_consumed }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_blind_score value = 55 }} set_variable = {{ name = {p}_live_score value = 90 }} set_variable = {{ name = {p}_identity_fields_hidden value = 0 }} set_variable = {{ name = {p}_relationship_anchor value = 1 }} }}''',
        174: f'''set_variable = {{ name = {p}_total_minutes value = 60 }}
set_variable = {{ name = {p}_presentation_minutes value = 40 }}
set_variable = {{ name = {p}_question_minutes value = 20 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_presentation_minutes value = 55 }} set_variable = {{ name = {p}_question_minutes value = 5 }} }}
set_variable = {{ name = {p}_time_check value = var:{p}_presentation_minutes }}
change_variable = {{ name = {p}_time_check add = var:{p}_question_minutes }}''',
        175: f'''set_variable = {{ name = {p}_coaching_opening value = 10 }}
set_variable = {{ name = {p}_coaching_allocated value = 10 }}
set_variable = {{ name = {p}_coaching_remaining value = var:{p}_coaching_opening }}
change_variable = {{ name = {p}_coaching_remaining add = {{ value = var:{p}_coaching_allocated multiply = -1 }} }}
set_variable = {{ name = {p}_coaching_conserved value = 0 }}
if = {{ limit = {{ var:{p}_coaching_remaining >= 0 }} set_variable = {{ name = {p}_coaching_conserved value = 1 }} }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_opportunity_inequality value = 1 }} }}''',
        176: f'''set_variable = {{ name = {p}_candidate_share value = 40 }}
set_variable = {{ name = {p}_peer_share value = 60 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_candidate_share value = 100 }} set_variable = {{ name = {p}_peer_share value = 0 }} set_variable = {{ name = {p}_credit_grab_debt value = 1 }} }}
set_variable = {{ name = {p}_share_check value = var:{p}_candidate_share }}
change_variable = {{ name = {p}_share_check add = var:{p}_peer_share }}''',
        177: f'''set_variable = {{ name = {p}_scale_score value = 95 }}
set_variable = {{ name = {p}_leverage_score value = 30 }}
set_variable = {{ name = {p}_dimensions_separate value = 1 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_leverage_score value = 95 }} set_variable = {{ name = {p}_dimensions_separate value = 0 }} }}''',
        178: f'''set_variable = {{ name = {p}_artifact_score value = 80 }}
set_variable = {{ name = {p}_narrative_score value = 70 }}
set_variable = {{ name = {p}_dual_gate_pass value = 1 }}
set_variable = {{ name = {p}_blind_score_consumed value = var:zg361_pp_m173_blind_score }}
set_variable = {{ name = {p}_coaching_hours_consumed value = var:zg361_pp_m175_coaching_allocated }}
set_variable = {{ name = {p}_candidate_share_consumed value = var:zg361_pp_m176_candidate_share }}
set_variable = {{ name = {p}_scale_consumed value = var:zg361_pp_m177_scale_score }}
set_variable = {{ name = {p}_leverage_consumed value = var:zg361_pp_m177_leverage_score }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_artifact_score value = 40 }} set_variable = {{ name = {p}_narrative_score value = 95 }} set_variable = {{ name = {p}_dual_gate_pass value = 0 }} }}
set_variable = {{ name = {p}_weighted_score value = {{ value = var:{p}_blind_score_consumed multiply = var:zg361_pp_m172_expert_weight_consumed divide = 100 }} }}
change_variable = {{ name = {p}_weighted_score add = {{ value = var:{p}_narrative_score multiply = var:zg361_pp_m172_external_weight_consumed divide = 100 }} }}
set_variable = {{ name = {p}_vote_eligible value = 0 }}
if = {{
\tlimit = {{
\t\tvar:{p}_dual_gate_pass = 1
\t\tvar:zg361_pp_m172_panel_weight_check = 100
\t\tvar:zg361_pp_m172_active_panel_count_consumed = 3
\t\tvar:zg361_pp_m170_familiar_minority_ok = 1
\t\tvar:zg361_pp_m176_share_check = 100
\t\tvar:zg361_pp_m174_time_check = 60
\t}}
\tset_variable = {{ name = {p}_vote_eligible value = 1 }}
}}
set_variable = {{ name = {p}_votes_cast value = 0 }}
set_variable = {{ name = {p}_final_decision value = 0 }}
if = {{ limit = {{ var:{p}_vote_eligible = 1 var:{p}_weighted_score >= 70 }} set_variable = {{ name = {p}_votes_cast value = 3 }} set_variable = {{ name = {p}_final_decision value = 1 }} }}
else = {{ set_variable = {{ name = {p}_material_deferral value = 1 }} }}''',
        179: f'''set_variable = {{ name = {p}_feedback_owner value = var:zg361_pp_m171_active_panel_1 }}
set_variable = {{ name = {p}_gap_id value = {{ value = var:zg361_case_v_case_serial multiply = 1000 add = 179 }} }}
set_variable = {{ name = {p}_gap_frozen value = 1 }}
set_variable = {{ name = {p}_next_evidence_id value = {{ value = var:{p}_gap_id add = 1 }} }}
set_variable = {{ name = {p}_next_evidence_frozen value = 1 }}
set_variable = {{ name = {p}_decision_consumed value = var:zg361_pp_m178_final_decision }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_reviewer_quality_debt value = 1 }} }}''',
        180: f'''set_variable = {{ name = {p}_candidate value = this }}
set_variable = {{ name = {p}_cooldown_due_cycle value = {{ value = var:zg361_case_v_cycle_serial add = 1 }} }}
set_variable = {{ name = {p}_prior_gap_id value = var:zg361_pp_m179_gap_id }}
set_variable = {{ name = {p}_prior_material_version value = var:zg361_case_v_revision }}
set_variable = {{ name = {p}_new_material_version value = {{ value = var:zg361_case_v_revision add = 1 }} }}
set_variable = {{ name = {p}_gap_completion value = 0 }}
set_variable = {{ name = {p}_retry_count value = 1 }}
set_variable = {{ name = {p}_retry_available value = 0 }}
set_variable = {{ name = {p}_nomination_slot_consumed value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 1 stewardship >= 12 }} set_variable = {{ name = {p}_gap_completion value = 1 }} }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_panel_congestion value = 1 }} }}''',
        181: f'''set_variable = {{ name = {p}_evidence_id value = {{ value = var:zg361_case_w_case_serial multiply = 1000 add = 181 }} }}
set_variable = {{ name = {p}_result_owner_snapshot value = var:zg361_pp_w_result_owner }}
set_variable = {{ name = {p}_result_cycle_snapshot value = var:zg361_pp_w_result_cycle }}
set_variable = {{ name = {p}_result_case_snapshot value = var:zg361_pp_w_result_case }}
set_variable = {{ name = {p}_result_state_snapshot value = var:zg361_pp_w_result_state }}
set_variable = {{ name = {p}_result_grade_snapshot value = var:zg361_pp_w_frozen_grade }}
set_variable = {{ name = {p}_result_reason_snapshot value = var:zg361_pp_w_frozen_reason }}
set_variable = {{ name = {p}_evidence_component_count value = var:zg361_pp_w_evidence_component_count }}
set_variable = {{ name = {p}_primary_category value = 0 }}
set_variable = {{ name = {p}_triage_truth_status value = 0 }}
set_variable = {{ name = {p}_triage_red_code value = 1 }}
set_variable = {{ name = {p}_manager_proposed_category value = scope:zg361_pp_route }}
set_variable = {{ name = {p}_current_rating_unchanged value = 1 }}
set_variable = {{ name = {p}_misdiagnosis_risk value = 1 }}''',
        182: f'''set_variable = {{ name = {p}_evidence_bundle_id value = var:zg361_pp_m181_evidence_id }}
set_variable = {{ name = {p}_evidence_component_count value = var:zg361_b2_pip_gate_component_count }}
set_variable = {{ name = {p}_threshold_required value = var:zg361_b2_pip_gate_threshold }}
set_variable = {{ name = {p}_evidence_threshold_met value = 1 }}
set_variable = {{ name = {p}_grade_only_autostart value = 0 }}
set_variable = {{ name = {p}_gate_status value = var:zg361_b2_pip_gate_status }}
set_variable = {{ name = {p}_gate_owner value = var:zg361_b2_pip_gate_owner }}
set_variable = {{ name = {p}_gate_cycle value = var:zg361_b2_pip_gate_cycle }}
set_variable = {{ name = {p}_gate_case value = var:zg361_b2_pip_gate_case }}
set_variable = {{ name = {p}_misconduct_routed_separately value = 1 }}
set_variable = {{ name = {p}_false_positive_risk value = 0 }}
set_variable = {{ name = {p}_manager_gate_review_route value = scope:zg361_pp_route }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_override_attempted value = 1 }} }}''',
        183: f'''set_variable = {{ name = {p}_goal_bundle_id value = {{ value = var:zg361_case_w_case_serial multiply = 1000 add = 183 }} }}
set_variable = {{ name = {p}_goals_frozen value = 1 }}
set_variable = {{ name = {p}_resources_frozen value = var:zg361_b2_pip_support_reserved }}
set_variable = {{ name = {p}_deadline_days value = 365 }}
set_variable = {{ name = {p}_manager_signed value = 1 }}
set_variable = {{ name = {p}_subject_signed value = 0 }}
set_variable = {{ name = {p}_independent_review_pass value = 0 }}
set_variable = {{ name = {p}_acknowledgement_status value = var:zg361_b2_pip_subject_response }}
set_variable = {{ name = {p}_subject_statement_code value = var:zg361_b2_pip_subject_response }}
set_variable = {{ name = {p}_subject_statement_author value = var:zg361_b2_pip_subject_response_author }}
set_variable = {{ name = {p}_subject_response_case value = var:zg361_b2_pip_subject_response_case }}
set_variable = {{ name = {p}_revision_remaining value = 1 }}
set_variable = {{ name = {p}_revision_used value = var:zg361_b2_pip_goal_revision_used }}
set_variable = {{ name = {p}_refusal_is_failure value = 0 }}
set_variable = {{ name = {p}_non_aggravation_grade value = var:zg361_pp_w_non_aggravation_grade }}
set_variable = {{ name = {p}_manager_process_route value = scope:zg361_pp_route }}
if = {{ limit = {{ OR = {{ var:zg361_b2_pip_subject_response = 1 var:zg361_b2_pip_subject_response = 2 }} }} set_variable = {{ name = {p}_subject_signed value = 1 }} }}
if = {{ limit = {{ var:zg361_b2_pip_subject_response = 3 }} set_variable = {{ name = {p}_refusal_reason value = 1 }} }}''',
        184: f'''set_variable = {{ name = {p}_active_case value = 1 }}
set_variable = {{ name = {p}_capacity_reserved value = var:zg361_b2_pip_support_reserved }}
set_variable = {{ name = {p}_support_status value = 2 }}
set_variable = {{ name = {p}_release_once value = 0 }}
set_variable = {{ name = {p}_overload_liability value = var:zg361_b2_pip_support_absent }}
set_variable = {{ name = {p}_support_hours value = var:zg361_b2_pip_support_hours }}
set_variable = {{ name = {p}_support_budget_spent value = var:zg361_b2_pip_support_budget_spent }}
set_variable = {{ name = {p}_support_case value = var:zg361_b2_m016_receipt_serial }}
set_variable = {{ name = {p}_manager_support_route value = scope:zg361_pp_route }}
if = {{ limit = {{ var:zg361_b2_pip_support_reserved = 1 }} set_variable = {{ name = {p}_support_status value = 1 }} }}''',
        185: f'''set_variable = {{ name = {p}_midpoint_due_days value = 180 }}
set_variable = {{ name = {p}_midpoint_status value = 0 }}
set_variable = {{ name = {p}_midpoint_pending value = 1 }}
set_variable = {{ name = {p}_midpoint_completed value = 0 }}
set_variable = {{ name = {p}_corrections_remaining value = 1 }}
set_variable = {{ name = {p}_skipped_midpoint value = 0 }}
set_variable = {{ name = {p}_manager_midpoint_route value = scope:zg361_pp_route }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_corrections_remaining value = 0 }} set_variable = {{ name = {p}_skipped_midpoint value = 1 }} }}''',
        186: f'''set_variable = {{ name = {p}_baseline_workload value = 0 }}
set_variable = {{ name = {p}_current_workload value = 0 }}
set_variable = {{ name = {p}_replacement_workload value = 0 }}
set_variable = {{ name = {p}_deadline_extension_days value = 0 }}
set_variable = {{ name = {p}_goal_creep_violation value = 0 }}
set_variable = {{ name = {p}_workload_truth_status value = 0 }}
set_variable = {{ name = {p}_workload_red_code value = 1 }}
set_variable = {{ name = {p}_manager_workload_route value = scope:zg361_pp_route }}''',
        187: f'''set_variable = {{ name = {p}_milestone_evidence_submitted value = 0 }}
set_variable = {{ name = {p}_stability_days_required value = 365 }}
set_variable = {{ name = {p}_independent_review_required value = 1 }}
set_variable = {{ name = {p}_evaluation_pending value = 1 }}
set_variable = {{ name = {p}_graduation_status value = 0 }}
set_variable = {{ name = {p}_writes_top_grade value = 0 }}
set_variable = {{ name = {p}_opaque_extension value = 0 }}
set_variable = {{ name = {p}_manager_review_route value = scope:zg361_pp_route }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_procedural_review_requested value = 1 }} }}''',
        188: f'''set_variable = {{ name = {p}_observation_days value = 365 }}
set_variable = {{ name = {p}_observation_start_cycle value = root.var:zg361_review_serial }}
set_variable = {{ name = {p}_observation_due_cycle value = {{ value = root.var:zg361_review_serial add = 1 }} }}
set_variable = {{ name = {p}_same_category_only value = 1 }}
set_variable = {{ name = {p}_category_snapshot value = var:zg361_pp_m181_primary_category }}
set_variable = {{ name = {p}_observation_pending value = 1 }}
set_variable = {{ name = {p}_observation_closed value = 0 }}
set_variable = {{ name = {p}_same_category_relapse value = 0 }}
set_variable = {{ name = {p}_relapse_status value = 0 }}
set_variable = {{ name = {p}_overbreadth_risk value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_same_category_only value = 0 }} set_variable = {{ name = {p}_overbreadth_risk value = 1 }} }}''',
        189: f'''set_variable = {{ name = {p}_second_pip value = 0 }}
set_variable = {{ name = {p}_transfer value = 0 }}
set_variable = {{ name = {p}_exit value = 0 }}
set_variable = {{ name = {p}_terminal_code value = 0 }}
set_variable = {{ name = {p}_real_vacancy_required value = 1 }}
if = {{
\tlimit = {{ scope:zg361_pp_route = 1 var:zg361_pp_m181_primary_category = 3 var:zg361_pp_w_real_vacancy = 1 }}
\tset_variable = {{ name = {p}_transfer value = 1 }}
\tset_variable = {{ name = {p}_terminal_code value = 2 }}
\tset_variable = {{ name = {p}_receiving_manager value = var:zg361_pp_w_receiving_manager }}
\tset_variable = {{ name = {p}_vacancy_id value = var:zg361_pp_w_transfer_vacancy_id }}
}}
else_if = {{
\tlimit = {{ scope:zg361_pp_route = 1 }}
\tset_variable = {{ name = {p}_second_pip value = 1 }}
\tset_variable = {{ name = {p}_terminal_code value = 1 }}
}}
else_if = {{
\tlimit = {{ scope:zg361_pp_route = 2 }}
\tset_variable = {{ name = {p}_exit value = 1 }}
\tset_variable = {{ name = {p}_terminal_code value = 3 }}
\tset_variable = {{ name = {p}_forced_exit value = 1 }}
\tset_variable = {{ name = {p}_replacement_cost value = 10 }}
}}
set_variable = {{ name = {p}_terminal_sum value = var:{p}_second_pip }}
change_variable = {{ name = {p}_terminal_sum add = var:{p}_transfer }}
change_variable = {{ name = {p}_terminal_sum add = var:{p}_exit }}
set_variable = {{ name = {p}_exclusive_terminal value = 0 }}
if = {{ limit = {{ var:{p}_terminal_sum = 1 }} set_variable = {{ name = {p}_exclusive_terminal value = 1 }} }}''',
        190: f'''set_variable = {{ name = {p}_disclosure_bundle_id value = {{ value = var:zg361_case_w_case_serial multiply = 1000 add = 190 }} }}
set_variable = {{ name = {p}_receiving_manager value = var:zg361_pp_m189_receiving_manager }}
set_variable = {{ name = {p}_acl_subject value = this }}
set_variable = {{ name = {p}_acl_receiver value = var:zg361_pp_m189_receiving_manager }}
set_variable = {{ name = {p}_vacancy_id_snapshot value = var:zg361_pp_w_transfer_vacancy_id }}
set_variable = {{ name = {p}_goal_snapshot value = var:zg361_b2_pip_case }}
set_variable = {{ name = {p}_support_snapshot value = var:zg361_b2_pip_support_reserved }}
set_variable = {{ name = {p}_completion_snapshot value = var:zg361_b2_pip_state }}
set_variable = {{ name = {p}_subject_statement_snapshot value = var:{p}_subject_statement_code }}
set_variable = {{ name = {p}_subject_statement_receiver value = var:{p}_acl_receiver }}
set_variable = {{ name = {p}_disclosed_fields value = 4 }}
set_variable = {{ name = {p}_private_ids_excluded value = 1 }}
set_variable = {{ name = {p}_old_rating_snapshot value = var:zg361_pp_w_non_aggravation_grade }}
set_variable = {{ name = {p}_old_rating_unchanged value = 1 }}
set_variable = {{ name = {p}_acl_pass value = 0 }}
set_variable = {{ name = {p}_stigma_risk value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_stigma_risk value = 1 }} }}
zg361_career_hc_accept_pp_transfer_request_effect = yes
set_variable = {{ name = {p}_external_request_status value = var:zg361_transfer_vacancy_status }}
set_variable = {{ name = {p}_external_request_red_code value = var:zg361_transfer_adapter_red_code }}
if = {{
\tlimit = {{
\t\ttrigger_if = {{
\t\t\tlimit = {{ has_variable = zg361_transfer_adapter_applied has_variable = zg361_transfer_vacancy_status }}
\t\t\tvar:zg361_transfer_adapter_applied = 1
\t\t\tvar:zg361_transfer_vacancy_status = 2
\t\t}}
\t\ttrigger_else = {{ always = no }}
\t}}
\tset_variable = {{ name = {p}_acl_pass value = 1 }}
\tsave_temporary_scope_as = zg361_pp_m190_disclosure_subject
\tvar:{p}_acl_receiver = {{
\t\tset_variable = {{ name = zg361_pp_received_transfer_disclosure_bundle value = scope:zg361_pp_m190_disclosure_subject.var:{p}_disclosure_bundle_id }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_disclosure_subject value = scope:zg361_pp_m190_disclosure_subject }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_disclosure_cycle value = scope:zg361_pp_m190_disclosure_subject.var:zg361_case_w_cycle_serial }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_disclosure_case value = scope:zg361_pp_m190_disclosure_subject.var:zg361_case_w_case_serial }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_disclosure_vacancy value = scope:zg361_pp_m190_disclosure_subject.var:{p}_vacancy_id_snapshot }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_goal value = scope:zg361_pp_m190_disclosure_subject.var:{p}_goal_snapshot }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_support value = scope:zg361_pp_m190_disclosure_subject.var:{p}_support_snapshot }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_completion value = scope:zg361_pp_m190_disclosure_subject.var:{p}_completion_snapshot }}
\t\tset_variable = {{ name = zg361_pp_received_transfer_subject_statement value = scope:zg361_pp_m190_disclosure_subject.var:{p}_subject_statement_snapshot }}
\t}}
}}''',
        191: f'''set_variable = {{ name = {p}_terminal_code_consumed value = var:zg361_pp_m189_terminal_code }}
set_variable = {{ name = {p}_vacancy_cost value = 3 }}
set_variable = {{ name = {p}_handover_cost value = 2 }}
set_variable = {{ name = {p}_overtime_cost value = 0 }}
set_variable = {{ name = {p}_replacement_cost value = 5 }}
set_variable = {{ name = {p}_net_cost value = 10 }}
set_variable = {{ name = {p}_cost_conserved value = 1 }}
set_variable = {{ name = {p}_hidden_cost_debt value = 0 }}
if = {{ limit = {{ scope:zg361_pp_route = 2 }} set_variable = {{ name = {p}_net_cost value = 0 }} set_variable = {{ name = {p}_cost_conserved value = 0 }} set_variable = {{ name = {p}_hidden_cost_debt value = 10 }} }}''',
    }
    return snippets[mechanism.mechanism_id]


def queue_manager_decision_call(mechanism_id: int) -> str:
    mechanism = MECHANISM_BY_ID[mechanism_id]
    row = case_vars(mechanism.domain)
    state = mechanism_stage(mechanism_id)
    return f'''save_scope_as = zg361_pp_prompt_subject
var:{row["owner"]} = {{ save_scope_as = zg361_pp_prompt_owner }}
save_scope_value_as = {{ name = zg361_pp_prompt_cycle value = var:{row["cycle"]} }}
save_scope_value_as = {{ name = zg361_pp_prompt_case value = var:{row["case"]} }}
save_scope_value_as = {{ name = zg361_pp_prompt_state value = {state} }}
save_scope_value_as = {{ name = zg361_pp_prompt_mechanism value = {mechanism_id} }}
var:{row["owner"]} = {{ trigger_event = {{ id = {EVENT_NAMESPACE}.{mechanism_id} days = 1 }} }}'''


def queue_subject_response_call(mechanism_id: int) -> str:
    mechanism = MECHANISM_BY_ID[mechanism_id]
    row = case_vars(mechanism.domain)
    state = mechanism_stage(mechanism_id)
    ai_route = 2 if mechanism_id == 166 else 1
    return f'''save_scope_as = zg361_pp_subject_prompt_subject
var:{row["owner"]} = {{ save_scope_as = zg361_pp_subject_prompt_owner }}
save_scope_value_as = {{ name = zg361_pp_subject_prompt_cycle value = var:{row["cycle"]} }}
save_scope_value_as = {{ name = zg361_pp_subject_prompt_case value = var:{row["case"]} }}
save_scope_value_as = {{ name = zg361_pp_subject_prompt_state value = {state} }}
if = {{
\tlimit = {{ is_ai = yes }}
\tzg361_pp_m{mechanism_id:03d}_subject_response_effect = {{ ROUTE = {ai_route} }}
\tzg361_pp_m{mechanism_id:03d}_resume_after_subject_effect = yes
}}
else = {{ trigger_event = {{ id = {EVENT_NAMESPACE}.{5000 + mechanism_id} days = 1 }} }}'''


def queue_decision_call(mechanism_id: int) -> str:
    if mechanism_id in SUBJECT_RESPONSE_IDS:
        return queue_subject_response_call(mechanism_id)
    return queue_manager_decision_call(mechanism_id)


def portfolio_done_trigger(domain: str, expected: bool = True) -> str:
    body = f'''trigger_if = {{
\tlimit = {{ has_variable = zg361_pp_{domain}_portfolio_done_cycle }}
\tvar:zg361_pp_{domain}_portfolio_done_cycle = root.var:zg361_review_serial
}}
trigger_else = {{ always = no }}'''
    return body if expected else f"NOT = {{\n{indent(body, 1)}\n}}"


def no_pending_audit_trigger(domain: DomainSpec) -> str:
    """Block receipt-variable reuse while a delayed audit is outstanding."""

    rows: list[str] = []
    for stage in domain.stages:
        for mechanism_id in stage:
            mechanism = MECHANISM_BY_ID[mechanism_id]
            for index, _ in enumerate(mechanism.deadlines, start=1):
                state = (
                    f"{PREFIX}_m{mechanism_id:03d}_audit_{index}_state"
                )
                rows.append(
                    "NOT = {\n"
                    "\ttrigger_if = {\n"
                    f"\t\tlimit = {{ has_variable = {state} }}\n"
                    f"\t\tvar:{state} = 1\n"
                    "\t}\n"
                    "\ttrigger_else = { always = no }\n"
                    "}"
                )
    return "\n".join(rows)


def render_portfolio_adapter() -> str:
    """One manager-scope integration seam, intentionally not centrally wired."""

    checks = []
    for domain in DOMAINS:
        if domain.key in {"u", "v", "w"}:
            skip_comments = {
                "u": "Only a delivered 3.5/3.75 result may create a promotion packet.",
                "v": "No U prescreen winner means no panel, vote or phantom promotion slot.",
                "w": "Only a delivered 3.25 result may enter PIP; other grades create no PIP object.",
            }
            skip_vars = {
                "u": "zg361_pp_u_skipped_not_eligible_cycle",
                "v": "zg361_pp_v_skipped_no_winner_cycle",
                "w": "zg361_pp_w_skipped_not_applicable_cycle",
            }
            skip_comment = skip_comments[domain.key]
            skip_var = skip_vars[domain.key]
            checks.append(
                f'''else_if = {{
\tlimit = {{
\t\t{portfolio_done_trigger(domain.key, expected=False)}
\t\t{indent(no_pending_audit_trigger(domain), 2).lstrip()}
\t\tNOT = {{
\t\t\t{indent(domain_open_guard(domain), 3).lstrip()}
\t\t}}
\t}}
\t# {skip_comment}
\tset_variable = {{ name = {skip_var} value = root.var:zg361_review_serial }}
\tset_variable = {{ name = zg361_pp_{domain.key}_portfolio_done_cycle value = root.var:zg361_review_serial }}
}}'''
            )
        checks.append(
            f'''else_if = {{
\tlimit = {{
\t\t{portfolio_done_trigger(domain.key, expected=False)}
\t\t{indent(no_pending_audit_trigger(domain), 2).lstrip()}
\t}}
\tzg361_pp_open_{domain.key}_case_effect = yes
}}'''
        )
    # The first branch cannot be an else_if in Paradox script.
    chain = "\n".join(checks)
    chain = chain.replace("else_if = {", "if = {", 1)
    all_done = "\n\t\t\t\t".join(portfolio_done_trigger(domain.key) for domain in DOMAINS)
    return f'''# The only integration-facing seam.  Current scope is the manager.  One
# deterministic assessed direct vassal receives one domain at a time; a later
# central caller may invoke the adapter again only after the visible queue has
# closed.  This file deliberately does not add that central caller.
zg361_pp_manager_portfolio_adapter_effect = {{
\tremove_variable = zg361_pp_runtime_applied
\tif = {{
\t\tlimit = {{
\t\t\thas_game_rule = zg361_on
\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\thas_variable = zg361_review_serial
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = zg361_pp_portfolio_queue_active }}
\t\t\t\tvar:zg361_pp_portfolio_queue_active = 0
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\tany_vassal = {{ zg361_is_reviewable_vassal_trigger = yes }}
\t\t}}
\t\tsave_temporary_scope_as = zg361_pp_portfolio_manager
\t\tordered_vassal = {{
\t\t\tlimit = {{ zg361_is_reviewable_vassal_trigger = yes liege = scope:zg361_pp_portfolio_manager }}
\t\t\torder_by = stewardship
\t\t\tposition = 0
\t\t\tsave_temporary_scope_as = zg361_pp_portfolio_subject
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ exists = scope:zg361_pp_portfolio_subject }}
\t\t\tscope:zg361_pp_portfolio_subject = {{
\t\t\t\t{indent(chain, 4).lstrip()}
\t\t\t\telse_if = {{
\t\t\t\t\tlimit = {{ {all_done} }}
\t\t\t\t\tscope:zg361_pp_portfolio_manager = {{ set_variable = {{ name = zg361_pp_portfolio_complete_cycle value = var:zg361_review_serial }} }}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}}
}}'''


def mechanism_reset_lines(mechanism: MechanismSpec, domain: DomainSpec) -> list[str]:
    """Clear every case-local payload and transaction receipt before reuse."""

    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    controls = {
        f"{p}_receipt_active": 0,
        f"{p}_consumed": 0,
        f"{p}_deferred": 0,
        f"{p}_audit_revision": 0,
    }
    owned = set(
        re.findall(
            r"name = (zg361_pp_m\d{3}_[A-Za-z0-9_]+)",
            "\n".join((semantic_write(mechanism), dual_cost_write(mechanism))),
        )
    )
    owned.update(
        {
            f"{p}_{mechanism.field}",
            f"{p}_route",
            f"{p}_policy_debt_due_days",
            f"{p}_consumer_value",
            f"{p}_consumer_revision",
            f"{p}_receipt_owner",
            f"{p}_receipt_subject",
            f"{p}_receipt_cycle",
            f"{p}_receipt_case",
            f"{p}_receipt_state",
            f"{p}_receipt_route",
            f"{p}_object_owner",
            f"{p}_object_subject",
            f"{p}_object_cycle",
            f"{p}_object_case",
            f"{p}_object_state",
        }
    )
    if mechanism.mechanism_id in SUBJECT_RESPONSE_IDS:
        owned.add(f"{p}_subject_response")
    if mechanism.mechanism_id == 166:
        owned.add(f"{p}_withdraw_intent")
    owned.update(f"{p}_{suffix}" for suffix in AUDIT_ONLY_FIELDS_BY_ID.get(mechanism.mechanism_id, ()))
    owned.update(f"{p}_{suffix}" for suffix in RESPONSE_ONLY_FIELDS_BY_ID.get(mechanism.mechanism_id, ()))
    controls[f"{p}_visible_outcome_code"] = 0
    resources = dict.fromkeys(
        (
            domain.resource,
            *EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
            *ROUTE_A_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
            *ROUTE_B_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
        )
    )
    lines: list[str] = []
    for resource in resources:
        receipt = f"{p}_{resource}"
        controls[f"{receipt}_amount"] = 0
        controls[f"{receipt}_status"] = 0
        owned.update({f"{receipt}_owner", f"{receipt}_cycle", f"{receipt}_case"})
    for index, _ in enumerate(mechanism.deadlines, start=1):
        controls[f"{p}_audit_{index}_state"] = 0
        controls[f"{p}_audit_{index}_consumed"] = 0
        controls[f"{p}_audit_{index}_business_settled"] = 0
        controls[f"{p}_audit_{index}_policy_debt_settled"] = 0
        owned.update(
            {
                f"{p}_audit_{index}_owner",
                f"{p}_audit_{index}_subject",
                f"{p}_audit_{index}_cycle",
                f"{p}_audit_{index}_case",
                f"{p}_audit_{index}_expected_state",
                f"{p}_audit_{index}_outcome",
                f"{p}_audit_{index}_consumer_value",
                f"{p}_audit_{index}_business_input",
            }
        )
    for name in sorted(owned - set(controls)):
        lines.append(f"remove_variable = {name}")
    for name, value in sorted(controls.items()):
        lines.append(f"set_variable = {{ name = {name} value = {value} }}")
    return lines


def render_domain_prework(domain: DomainSpec) -> str:
    if domain.key == "t":
        return '''# Freeze the delivered result's exact five-tuple and payload.  A live
# result case, not last_grade or a Boolean "preserved" marker, is authoritative.
set_variable = { name = zg361_pp_t_result_owner value = var:zg361_result_case_owner }
set_variable = { name = zg361_pp_t_result_subject value = this }
set_variable = { name = zg361_pp_t_result_cycle value = var:zg361_result_cycle_serial }
set_variable = { name = zg361_pp_t_result_case value = var:zg361_result_case_serial }
set_variable = { name = zg361_pp_t_result_state value = var:zg361_result_case_state }
set_variable = { name = zg361_pp_t_frozen_grade value = var:zg361_result_grade }
set_variable = { name = zg361_pp_t_frozen_reason value = var:zg361_result_grade_reason }
set_variable = { name = zg361_pp_t_frozen_kpi value = var:zg361_result_kpi_frozen }
set_variable = { name = zg361_pp_t_frozen_rank value = var:zg361_result_rank_frozen }
set_variable = { name = zg361_pp_t_frozen_evidence_hash value = { value = var:zg361_result_case_serial multiply = 100 add = var:zg361_pp_t_frozen_reason } }
set_variable = { name = zg361_pp_t_non_aggravation_ok value = 1 }
set_variable = { name = zg361_pp_t_visible_feedback_revision value = 0 }'''
    if domain.key == "u":
        return '''# Freeze the delivered result identity and candidate boundary before
# nomination politics can move either one.
set_variable = { name = zg361_pp_u_result_owner value = var:zg361_result_case_owner }
set_variable = { name = zg361_pp_u_result_subject value = this }
set_variable = { name = zg361_pp_u_result_cycle value = var:zg361_result_cycle_serial }
set_variable = { name = zg361_pp_u_result_case value = var:zg361_result_case_serial }
set_variable = { name = zg361_pp_u_result_state value = var:zg361_result_case_state }
set_variable = { name = zg361_pp_u_frozen_grade value = var:zg361_result_grade }
set_variable = { name = zg361_pp_u_frozen_reason value = var:zg361_result_grade_reason }
set_variable = { name = zg361_pp_u_candidate_eligible value = 0 }
if = { limit = { var:zg361_pp_u_frozen_grade >= 2 } set_variable = { name = zg361_pp_u_candidate_eligible value = 1 } }
# Persistent shelving obligations are consumed once per later review cycle.
root = {
\tif = {
\t\tlimit = {
\t\t\ttrigger_if = {
\t\t\t\tlimit = {
\t\t\t\t\thas_variable = zg361_pp_u_shelving_active
\t\t\t\t\thas_variable = zg361_pp_u_shelving_due_cycle
\t\t\t\t\thas_variable = zg361_pp_u_shelving_last_penalty_cycle
\t\t\t\t\thas_variable = zg361_pp_u_shelving_nominated
\t\t\t\t}
\t\t\t\tvar:zg361_pp_u_shelving_active = 1
\t\t\t\tvar:zg361_pp_u_shelving_nominated = 0
\t\t\t\tvar:zg361_review_serial >= var:zg361_pp_u_shelving_due_cycle
\t\t\t\tNOT = { var:zg361_pp_u_shelving_last_penalty_cycle = var:zg361_review_serial }
\t\t\t}
\t\t\ttrigger_else = { always = no }
\t\t}
\t\tset_variable = { name = zg361_pp_u_shelving_last_penalty_cycle value = var:zg361_review_serial }
\t}
}
# Matured #168 observations alter only the next cycle's quota, once and clamped.
if = {
\tlimit = { root = { has_variable = zg361_pp_u_next_quota_pending var:zg361_pp_u_next_quota_pending = 1 } }
\tset_variable = {
\t\tname = zg361_pp_u_nomination_slot_authorized
\t\tvalue = { value = var:zg361_pp_u_nomination_slot_authorized add = root.var:zg361_pp_u_next_quota_delta min = 1 max = 3 }
\t}
\tset_variable = { name = zg361_pp_u_nomination_slot_available value = var:zg361_pp_u_nomination_slot_authorized }
\troot = {
\t\tset_variable = { name = zg361_pp_u_next_quota_pending value = 0 }
\t\tset_variable = { name = zg361_pp_u_next_quota_consumed_cycle value = var:zg361_review_serial }
\t}
}
# Freeze a distinct filler candidate before #161 can spend real quota/hours.
remove_variable = zg361_pp_m161_filler_candidate
save_temporary_scope_as = zg361_pp_u_main_candidate
root = {
\tordered_vassal = {
\t\tlimit = {
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tNOT = { this = scope:zg361_pp_u_main_candidate }
\t\t}
\t\torder_by = stewardship
\t\tposition = 0
\t\tsave_temporary_scope_as = zg361_pp_u_filler_candidate
\t}
}
if = { limit = { exists = scope:zg361_pp_u_filler_candidate } set_variable = { name = zg361_pp_m161_filler_candidate value = scope:zg361_pp_u_filler_candidate } }'''
    if domain.key == "v":
        selectors = []
        assignments = []
        for index in range(1, 5):
            selectors.append(
                f'''ordered_vassal = {{
\tlimit = {{
\t\tzg361_is_reviewable_vassal_trigger = yes
\t\tNOT = {{ this = scope:zg361_pp_v_candidate }}
\t}}
\torder_by = stewardship
\tposition = {index - 1}
\tsave_temporary_scope_as = zg361_pp_v_pool_{index}
}}'''
            )
            assignments.append(
                f'''if = {{ limit = {{ exists = scope:zg361_pp_v_pool_{index} }} set_variable = {{ name = zg361_pp_v_panel_pool_{index} value = scope:zg361_pp_v_pool_{index} }} }}'''
            )
        return f'''# Consume the one real U prescreen winner and freeze three active seats plus
# one clean alternate.  The candidate cannot manufacture a panel without a
# passed packet and the reserved promotion slot is settled exactly once here.
set_variable = {{ name = zg361_pp_v_source_packet_case value = var:zg361_pp_m157_packet_case }}
set_variable = {{ name = zg361_pp_v_source_prescreen_case value = var:zg361_pp_m160_receipt_case }}
if = {{
	limit = {{ var:zg361_pp_m160_promotion_slot_status = 1 }}
	change_variable = {{ name = zg361_pp_u_promotion_slot_reserved add = -1 }}
	change_variable = {{ name = zg361_pp_u_promotion_slot_settled add = 1 }}
	set_variable = {{ name = zg361_pp_m160_promotion_slot_status value = 2 }}
}}
remove_variable = zg361_pp_v_panel_pool_1
remove_variable = zg361_pp_v_panel_pool_2
remove_variable = zg361_pp_v_panel_pool_3
remove_variable = zg361_pp_v_panel_pool_4
save_temporary_scope_as = zg361_pp_v_candidate
root = {{
\t{indent(chr(10).join(selectors), 1).lstrip()}
}}
{chr(10).join(assignments)}'''
    if domain.key == "w":
        return '''# W is a read/supplement projection over B2's unique PIP case.  It
# never starts, signs, settles or releases that case.  Grade 3.25 is not a gate:
# the exact B2 evidence receipt below is authoritative.
set_variable = { name = zg361_pp_w_result_owner value = var:zg361_result_case_owner }
set_variable = { name = zg361_pp_w_result_subject value = this }
set_variable = { name = zg361_pp_w_result_cycle value = var:zg361_result_cycle_serial }
set_variable = { name = zg361_pp_w_result_case value = var:zg361_result_case_serial }
set_variable = { name = zg361_pp_w_result_state value = var:zg361_result_case_state }
set_variable = { name = zg361_pp_w_frozen_grade value = var:zg361_result_grade }
set_variable = { name = zg361_pp_w_frozen_reason value = var:zg361_result_grade_reason }
set_variable = { name = zg361_pp_w_frozen_kpi value = var:zg361_result_kpi_frozen }
set_variable = { name = zg361_pp_w_frozen_rank value = var:zg361_result_rank_frozen }
set_variable = { name = zg361_pp_w_case_open_grade value = var:zg361_pp_w_frozen_grade }
set_variable = { name = zg361_pp_w_non_aggravation_grade value = var:zg361_pp_w_frozen_grade }
set_variable = { name = zg361_pp_w_b2_pip_owner value = var:zg361_b2_pip_owner }
set_variable = { name = zg361_pp_w_b2_pip_subject value = var:zg361_b2_pip_subject }
set_variable = { name = zg361_pp_w_b2_pip_cycle value = var:zg361_b2_pip_cycle }
set_variable = { name = zg361_pp_w_b2_pip_case value = var:zg361_b2_pip_case }
set_variable = { name = zg361_pp_w_b2_pip_state_at_open value = var:zg361_b2_pip_state }
set_variable = { name = zg361_pp_w_evidence_component_count value = var:zg361_b2_pip_gate_component_count }
set_variable = { name = zg361_pp_w_pip_gate_threshold value = var:zg361_b2_pip_gate_threshold }
set_variable = { name = zg361_pp_w_pip_gate_candidate value = var:zg361_b2_pip_gate_status }
# A receiving manager does not prove that a vacancy exists.  The central
# career/HC adapter must bind an exact active vacancy ID and its receiver on
# this subject; this package only freezes and verifies that input.
remove_variable = zg361_pp_w_receiving_manager
remove_variable = zg361_pp_w_transfer_vacancy_id
remove_variable = zg361_pp_w_transfer_vacancy_receiver
remove_variable = zg361_pp_w_transfer_vacancy_owner
remove_variable = zg361_pp_w_transfer_vacancy_subject
remove_variable = zg361_pp_w_transfer_source_cycle
remove_variable = zg361_pp_w_transfer_source_case
remove_variable = zg361_pp_w_transfer_vacancy_title
remove_variable = zg361_pp_w_transfer_maturity_cycle
remove_variable = zg361_pp_w_transfer_position_kind
set_variable = { name = zg361_pp_w_real_vacancy value = 0 }
set_variable = { name = zg361_pp_w_transfer_vacancy_active value = 0 }
if = {
	limit = {
		trigger_if = {
			limit = {
				has_variable = zg361_transfer_vacancy_id
				has_variable = zg361_transfer_vacancy_owner
				has_variable = zg361_transfer_vacancy_subject
				has_variable = zg361_transfer_vacancy_receiver
				has_variable = zg361_transfer_vacancy_source_cycle
				has_variable = zg361_transfer_vacancy_source_case
				has_variable = zg361_transfer_vacancy_title
				has_variable = zg361_transfer_vacancy_maturity_cycle
				has_variable = zg361_transfer_vacancy_position_kind
				has_variable = zg361_transfer_vacancy_active
				has_variable = zg361_transfer_vacancy_status
				has_variable = zg361_transfer_hc_authorized
				has_variable = zg361_transfer_hc_reserved
				has_variable = zg361_transfer_hc_partition
				has_variable = zg361_transfer_hc_conserved
			}
			var:zg361_transfer_vacancy_active = 1
			var:zg361_transfer_vacancy_status = 1
			var:zg361_transfer_vacancy_owner = root
			var:zg361_transfer_vacancy_subject = this
			var:zg361_transfer_vacancy_source_cycle < root.var:zg361_review_serial
			var:zg361_transfer_vacancy_maturity_cycle <= root.var:zg361_review_serial
			var:zg361_transfer_vacancy_position_kind = 1
			NOT = { var:zg361_transfer_vacancy_receiver = this }
			primary_title = var:zg361_transfer_vacancy_title
			var:zg361_transfer_vacancy_title = { holder = this }
			var:zg361_transfer_hc_authorized = 1
			var:zg361_transfer_hc_reserved = 1
			var:zg361_transfer_hc_partition = var:zg361_transfer_hc_authorized
			var:zg361_transfer_hc_conserved = 1
			var:zg361_transfer_vacancy_receiver = {
				zg361_is_celestial_liege_trigger = yes
				NOT = { this = root }
				liege = root
				primary_title.tier > prev.primary_title.tier
				vassal_count < vassal_limit
				NOT = { is_at_war_with = root }
				NOT = { is_at_war_with = prev }
			}
			NOT = { is_at_war_with = var:zg361_transfer_vacancy_receiver }
		}
		trigger_else = { always = no }
	}
	set_variable = { name = zg361_pp_w_receiving_manager value = var:zg361_transfer_vacancy_receiver }
	set_variable = { name = zg361_pp_w_transfer_vacancy_receiver value = var:zg361_transfer_vacancy_receiver }
	set_variable = { name = zg361_pp_w_transfer_vacancy_id value = var:zg361_transfer_vacancy_id }
	set_variable = { name = zg361_pp_w_transfer_vacancy_owner value = var:zg361_transfer_vacancy_owner }
	set_variable = { name = zg361_pp_w_transfer_vacancy_subject value = this }
	set_variable = { name = zg361_pp_w_transfer_source_cycle value = var:zg361_transfer_vacancy_source_cycle }
	set_variable = { name = zg361_pp_w_transfer_source_case value = var:zg361_transfer_vacancy_source_case }
	set_variable = { name = zg361_pp_w_transfer_vacancy_title value = var:zg361_transfer_vacancy_title }
	set_variable = { name = zg361_pp_w_transfer_maturity_cycle value = var:zg361_transfer_vacancy_maturity_cycle }
	set_variable = { name = zg361_pp_w_transfer_position_kind value = var:zg361_transfer_vacancy_position_kind }
	set_variable = { name = zg361_pp_w_transfer_vacancy_active value = 1 }
	set_variable = { name = zg361_pp_w_real_vacancy value = 1 }
}
set_variable = { name = zg361_pp_w_visible_case_revision value = 0 }'''
    return "# no domain-specific prework"


def domain_open_guard(domain: DomainSpec) -> str:
    if domain.key == "t":
        return '''has_variable = zg361_result_case_owner
var:zg361_result_case_owner = root
has_variable = zg361_result_cycle_serial
var:zg361_result_cycle_serial = root.var:zg361_review_serial
has_variable = zg361_result_case_serial
has_variable = zg361_result_case_state
var:zg361_result_case_state >= 3
has_variable = zg361_result_grade
has_variable = zg361_result_grade_reason
has_variable = zg361_result_kpi_frozen
has_variable = zg361_result_rank_frozen'''
    if domain.key == "u":
        return '''has_variable = zg361_result_case_owner
var:zg361_result_case_owner = root
has_variable = zg361_result_cycle_serial
var:zg361_result_cycle_serial = root.var:zg361_review_serial
has_variable = zg361_result_case_serial
has_variable = zg361_result_case_state
var:zg361_result_case_state >= 3
has_variable = zg361_result_grade
var:zg361_result_grade >= 2
has_variable = zg361_result_grade_reason'''
    if domain.key == "v":
        return '''var:zg361_pp_m160_prescreen_pass = 1
var:zg361_pp_m160_packet_candidate_consumed = this
var:zg361_pp_m160_promotion_slot_status = 1'''
    if domain.key == "w":
        return '''has_variable = zg361_result_case_owner
var:zg361_result_case_owner = root
has_variable = zg361_result_cycle_serial
var:zg361_result_cycle_serial = root.var:zg361_review_serial
has_variable = zg361_result_case_serial
has_variable = zg361_result_case_state
var:zg361_result_case_state >= 3
has_variable = zg361_result_grade
var:zg361_result_grade = 1
has_variable = zg361_result_grade_reason
has_variable = zg361_result_kpi_frozen
has_variable = zg361_result_rank_frozen
has_variable = zg361_b2_pip_gate_owner
var:zg361_b2_pip_gate_owner = root
has_variable = zg361_b2_pip_gate_subject
var:zg361_b2_pip_gate_subject = this
has_variable = zg361_b2_pip_gate_cycle
var:zg361_b2_pip_gate_cycle = var:zg361_result_cycle_serial
has_variable = zg361_b2_pip_gate_case
var:zg361_b2_pip_gate_case = var:zg361_result_case_serial
var:zg361_b2_pip_gate_status = 1
has_variable = zg361_b2_pip_owner
var:zg361_b2_pip_owner = root
has_variable = zg361_b2_pip_subject
var:zg361_b2_pip_subject = this
has_variable = zg361_b2_pip_cycle
var:zg361_b2_pip_cycle = var:zg361_result_cycle_serial
has_variable = zg361_b2_pip_case
var:zg361_b2_pip_case = var:zg361_result_case_serial
OR = {
	var:zg361_b2_pip_state = 1
	var:zg361_b2_pip_state = 2
	var:zg361_b2_pip_state = 3
	var:zg361_b2_pip_state = 4
	var:zg361_b2_pip_state = 5
}
var:zg361_b2_m015_receipt_serial = var:zg361_b2_pip_case'''
    raise AssertionError(domain.key)


def render_open(domain: DomainSpec) -> str:
    ids = tuple(mechanism_id for stage in domain.stages for mechanism_id in stage)
    resets: list[str] = []
    for mechanism_id in ids:
        p = f"{PREFIX}_m{mechanism_id:03d}"
        resets.extend(mechanism_reset_lines(MECHANISM_BY_ID[mechanism_id], domain))
    for state in range(1, len(domain.stages) + 1):
        dl = f"{PREFIX}_{domain.key}_stage_{state}_deadline"
        resets.extend(
            (
                f"set_variable = {{ name = {dl}_pending value = 0 }}",
                f"set_variable = {{ name = {dl}_expired value = 0 }}",
                f"remove_variable = {dl}_owner",
                f"remove_variable = {dl}_subject",
                f"remove_variable = {dl}_cycle",
                f"remove_variable = {dl}_case",
                f"remove_variable = {dl}_state",
                f"remove_variable = {dl}_days",
            )
        )
    extra_counts: dict[str, int] = {}
    for mechanism_id in ids:
        for resource in (
            *EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
            *ROUTE_A_EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
            *ROUTE_B_EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
        ):
            extra_counts[resource] = extra_counts.get(resource, 0) + 1
    for resource, amount in extra_counts.items():
        resets.extend(
            (
                f"set_variable = {{ name = zg361_pp_{domain.key}_{resource}_authorized value = {amount} }}",
                f"set_variable = {{ name = zg361_pp_{domain.key}_{resource}_available value = {amount} }}",
                f"set_variable = {{ name = zg361_pp_{domain.key}_{resource}_reserved value = 0 }}",
                f"set_variable = {{ name = zg361_pp_{domain.key}_{resource}_settled value = 0 }}",
                f"set_variable = {{ name = zg361_pp_{domain.key}_{resource}_conserved value = 1 }}",
            )
        )
    reset_text = "\n\t\t".join(resets)
    prework = render_domain_prework(domain)
    authorized = len(ids)
    return f'''# Open one {domain.code} case on an assessed direct vassal.  ROOT is the
# celestial duke-or-higher manager; counts and barons can only be this subject.
zg361_pp_open_{domain.key}_case_effect = {{
\tremove_variable = zg361_pp_runtime_applied
\tif = {{
\t\tlimit = {{
\t\t\troot = {{
\t\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\t\thas_variable = zg361_review_serial
\t\t\t}}
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = root
\t\t\t{indent(domain_open_guard(domain), 3).lstrip()}
\t\t\t# Do not reuse this domain's receipt variables while any delayed
\t\t\t# audit is pending.  The portfolio adapter may skip to another
\t\t\t# domain and retry this one after the old receipt is terminal.
\t\t\t{indent(no_pending_audit_trigger(domain), 3).lstrip()}
\t\t}}
\t\tzg361_case_{domain.key}_open_effect = yes
\t\tif = {{
\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_authorized value = {authorized} }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_completed value = 0 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_evidence_led value = 0 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_political value = 0 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_policy_debt value = 0 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_{domain.resource}_available value = {authorized} }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_{domain.resource}_reserved value = 0 }}
\t\t\tset_variable = {{ name = zg361_pp_{domain.key}_{domain.resource}_settled value = 0 }}
\t\t\t{reset_text}
\t\t\t{indent(prework, 3).lstrip()}
\t\t\troot = {{ set_variable = {{ name = zg361_pp_portfolio_queue_active value = 1 }} }}
\t\t\tzg361_pp_schedule_{domain.key}_stage_01_effect = yes
\t\t\tzg361_pp_dispatch_{domain.key}_stage_01_effect = yes
\t\t\tset_variable = {{ name = zg361_pp_runtime_applied value = 1 }}
\t\t}}
\t}}
}}'''


def render_manager_entry(mechanism: MechanismSpec) -> str:
    state = mechanism_stage(mechanism.mechanism_id)
    return f'''zg361_pp_m{mechanism.mechanism_id:03d}_manager_apply_effect = {{
\tremove_variable = zg361_pp_runtime_applied
\tif = {{
\t\tlimit = {{
\t\t\troot = {{ zg361_is_celestial_liege_trigger = yes }}
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = root
\t\t\t{indent(full_guard(mechanism.domain, state, "$TICKET_OWNER$", "$TICKET_SUBJECT$", "$TICKET_CYCLE$", "$TICKET_CASE$", "$TICKET_STATE$"), 3).lstrip()}
\t\t}}
\t\tzg361_pp_m{mechanism.mechanism_id:03d}_core_effect = {{
\t\t\tROUTE = $ROUTE$
\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\tTICKET_STATE = $TICKET_STATE$
\t\t}}
\t}}
}}'''


def render_subject_response(mechanism: MechanismSpec) -> str:
    if mechanism.mechanism_id not in SUBJECT_RESPONSE_IDS:
        return ""
    state = mechanism_stage(mechanism.mechanism_id)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    response_action = ""
    if mechanism.mechanism_id == 151:
        response_action = f'''if = {{
\t\t\tlimit = {{ scope:zg361_pp_subject_route = 1 }}
\t\t\tset_variable = {{ name = {p}_agreed value = 1 }}
\t\t\tset_variable = {{ name = {p}_disputed value = 0 }}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ scope:zg361_pp_subject_route = 2 }}
\t\t\tset_variable = {{ name = {p}_appeal_filed value = 1 }}
\t\t\tset_variable = {{ name = {p}_appeal_snapshot_grade value = var:zg361_pp_t_frozen_grade }}
\t\t\tset_variable = {{ name = {p}_disputed value = 1 }}
\t\t}}
\t\tchange_variable = {{ name = zg361_case_t_feedback_revision add = 1 }}'''
    elif mechanism.mechanism_id == 166:
        response_action = f'''if = {{
\t\t\tlimit = {{ scope:zg361_pp_subject_route = 1 }}
\t\t\tset_variable = {{ name = {p}_withdraw_intent value = 1 }}
\t\t\tzg361_pp_m166_core_effect = {{
\t\t\t\tROUTE = 1
\t\t\t\tTICKET_OWNER = var:zg361_case_u_owner
\t\t\t\tTICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:zg361_case_u_cycle_serial
\t\t\t\tTICKET_CASE = var:zg361_case_u_case_serial
\t\t\t\tTICKET_STATE = 3
\t\t\t}}
\t\t}}
\t\telse = {{ set_variable = {{ name = {p}_withdraw_intent value = 0 }} }}
\t\tchange_variable = {{ name = zg361_case_u_feedback_revision add = 1 }}'''
    elif mechanism.mechanism_id == 190:
        response_action = f'''set_variable = {{ name = {p}_subject_statement_author value = this }}
\t\tset_variable = {{ name = {p}_subject_statement_version value = 1 }}
\t\tset_variable = {{ name = {p}_subject_statement_private_ids value = 0 }}
\t\tset_variable = {{ name = {p}_subject_statement_code value = scope:zg361_pp_subject_route }}
\t\tif = {{ limit = {{ scope:zg361_pp_subject_route = 2 }} set_variable = {{ name = {p}_subject_disclosure_refused value = 1 }} }}
\t\tchange_variable = {{ name = zg361_case_w_feedback_revision add = 1 }}'''
    resume_guard = (
        f"NOT = {{ var:{p}_subject_response = 1 }}"
        if mechanism.mechanism_id == 166
        else f"has_variable = {p}_subject_response"
    )
    ai_route = (
        f'''set_variable = {{ name = zg361_pp_ai_route value = 2 }}'''
        if mechanism.mechanism_id == 166
        else f'''set_variable = {{ name = zg361_pp_ai_route value = 1 }}
\t\tif = {{ limit = {{ var:zg361_case_{mechanism.domain}_owner = {{ is_at_war = yes }} }} set_variable = {{ name = zg361_pp_ai_route value = 3 }} }}
\t\telse_if = {{ limit = {{ var:zg361_case_{mechanism.domain}_owner = {{ OR = {{ has_trait = arbitrary has_trait = ambitious }} }} }} set_variable = {{ name = zg361_pp_ai_route value = 2 }} }}'''
    )
    if mechanism.mechanism_id == 190:
        ai_route += "\n\t\tif = { limit = { NOT = { var:zg361_pp_m189_terminal_code = 2 } } set_variable = { name = zg361_pp_ai_route value = 3 } }"
    manager_queue = queue_manager_decision_call(mechanism.mechanism_id)
    return f'''# The assessed official may respond only to their own packet.  This grants no
# cohort, nomination, panel, PIP-initiation or assessment authority.
zg361_pp_m{mechanism.mechanism_id:03d}_subject_response_effect = {{
\tsave_temporary_scope_value_as = {{ name = zg361_pp_subject_route value = $ROUTE$ }}
\tif = {{
\t\tlimit = {{
\t\t\tOR = {{ scope:zg361_pp_subject_route = 1 scope:zg361_pp_subject_route = 2 }}
\t\t\tzg361_case_kernel_subject_self_guard_trigger = {{
\t\t\t\tSUBJECT_VAR = zg361_case_{mechanism.domain}_subject
\t\t\t\tACTIVE_VAR = zg361_case_{mechanism.domain}_active
\t\t\t}}
\t\t\tvar:zg361_case_{mechanism.domain}_state = {state}
\t\t\tNOT = {{ has_variable = {p}_subject_response }}
\t\t}}
\t\tset_variable = {{ name = {p}_subject_response value = scope:zg361_pp_subject_route }}
\t\t{response_action or f"change_variable = {{ name = zg361_case_{mechanism.domain}_feedback_revision add = 1 }}"}
\t}}
}}

zg361_pp_m{mechanism.mechanism_id:03d}_resume_after_subject_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\t{resume_guard}
\t\t\tzg361_case_kernel_subject_self_guard_trigger = {{
\t\t\t\tSUBJECT_VAR = zg361_case_{mechanism.domain}_subject
\t\t\t\tACTIVE_VAR = zg361_case_{mechanism.domain}_active
\t\t\t}}
\t\t\tvar:zg361_case_{mechanism.domain}_state = {state}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_case_{mechanism.domain}_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t{ai_route}
\t\t\tzg361_pp_m{mechanism.mechanism_id:03d}_core_effect = {{
\t\t\t\tROUTE = var:zg361_pp_ai_route
\t\t\t\tTICKET_OWNER = var:zg361_case_{mechanism.domain}_owner
\t\t\t\tTICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:zg361_case_{mechanism.domain}_cycle_serial
\t\t\t\tTICKET_CASE = var:zg361_case_{mechanism.domain}_case_serial
\t\t\t\tTICKET_STATE = {state}
\t\t\t}}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ var:zg361_case_{mechanism.domain}_owner = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t{indent(manager_queue, 3).lstrip()}
\t\t}}
\t}}
}}'''


def render_core(mechanism: MechanismSpec) -> str:
    state = mechanism_stage(mechanism.mechanism_id)
    row = case_vars(mechanism.domain)
    domain = DOMAIN_BY_KEY[mechanism.domain]
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    cost_owner = f"set_variable = {{ name = zg361_pp_cost_owner value = var:{row['owner']} }}"
    transaction = transaction_call(mechanism, state, domain.resource)
    extra_resources = EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ())
    route_a_resources = ROUTE_A_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ())
    route_b_resources = ROUTE_B_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ())
    extra_guard = "\n".join(
        f"var:zg361_pp_{mechanism.domain}_{resource}_available >= 1"
        for resource in extra_resources
    ) or "always = yes"
    extra_transaction = "\n".join(
        transaction_call(mechanism, state, resource) for resource in extra_resources
    )
    route_a_guard = "\n".join(
        f"var:zg361_pp_{mechanism.domain}_{resource}_available >= 1"
        for resource in route_a_resources
    ) or "always = yes"
    route_a_transaction = "\n".join(
        transaction_call(mechanism, state, resource) for resource in route_a_resources
    )
    route_b_guard = "\n".join(
        f"var:zg361_pp_{mechanism.domain}_{resource}_available >= 1"
        for resource in route_b_resources
    ) or "always = yes"
    route_b_transaction = "\n".join(
        transaction_call(mechanism, state, resource) for resource in route_b_resources
    )
    all_resources = (domain.resource, *extra_resources)
    status_rows = "\n".join(
        f'''trigger_if = {{
\tlimit = {{ scope:zg361_pp_route = 1 }}
\tvar:{p}_{resource}_status = 1
}}
trigger_else_if = {{
\tlimit = {{ scope:zg361_pp_route = 2 }}
\tvar:{p}_{resource}_status = 2
}}
trigger_else = {{ always = yes }}'''
        for resource in all_resources
    )
    route_b_status = "\n".join(
        f'''trigger_if = {{
\tlimit = {{ scope:zg361_pp_route = 2 }}
\tvar:{p}_{resource}_status = 2
}}
trigger_else = {{ always = yes }}'''
        for resource in route_b_resources
    ) or "always = yes"
    route_a_status = "\n".join(
        f'''trigger_if = {{
\tlimit = {{ scope:zg361_pp_route = 1 }}
\tvar:{p}_{resource}_status = 1
}}
trigger_else = {{ always = yes }}'''
        for resource in route_a_resources
    ) or "always = yes"
    semantic = "\n".join(
        (business_object_identity_write(mechanism, state), semantic_write(mechanism))
    )
    payment = dual_cost_write(mechanism)
    # B2 is the only PIP-capacity owner.  PP records manager procedure and
    # projects the B2 receipt; it never reserves or releases a second slot.
    post_operation = ""
    deadline_calls = "\n\t\t\t".join(
        f"zg361_pp_m{mechanism.mechanism_id:03d}_schedule_audit_{index}_effect = yes"
        for index, _ in enumerate(mechanism.deadlines, start=1)
    )
    return f'''# {mechanism.mechanism_id:03d} {mechanism.title_cn}: typed A/B/C write -> {mechanism.consumer}.
zg361_pp_m{mechanism.mechanism_id:03d}_core_effect = {{
\tsave_temporary_scope_value_as = {{ name = zg361_pp_route value = $ROUTE$ }}
\tremove_variable = zg361_pp_runtime_applied
\t{cost_owner}
\tif = {{
\t\tlimit = {{
\t\t\tOR = {{ scope:zg361_pp_route = 1 scope:zg361_pp_route = 2 scope:zg361_pp_route = 3 }}
\t\t\t{indent(full_guard(mechanism.domain, state, "$TICKET_OWNER$", "$TICKET_SUBJECT$", "$TICKET_CYCLE$", "$TICKET_CASE$", "$TICKET_STATE$"), 3).lstrip()}
\t\t\tvar:{p}_receipt_active = 0
\t\t\t{indent(routed_dependency_guard(mechanism.mechanism_id), 3).lstrip()}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ NOT = {{ scope:zg361_pp_route = 3 }} }}
\t\t\t\tvar:zg361_pp_{mechanism.domain}_{domain.resource}_available >= 1
\t\t\t\t{extra_guard}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ scope:zg361_pp_route = 1 }}
\t\t\t\t{route_a_guard}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ scope:zg361_pp_route = 2 }}
\t\t\t\t{route_b_guard}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\t{indent(dual_cost_guard(mechanism.mechanism_id), 3).lstrip()}
\t\t}}
\t\t{indent(record_operation(mechanism, state), 2).lstrip()}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
\t\t\tif = {{
\t\t\t\tlimit = {{ NOT = {{ scope:zg361_pp_route = 3 }} }}
\t\t\t\t{indent(transaction, 4).lstrip()}
\t\t\t\t{indent(extra_transaction, 4).lstrip()}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ scope:zg361_pp_route = 1 }}
\t\t\t\t\t{indent(route_a_transaction, 5).lstrip()}
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ scope:zg361_pp_route = 2 }}
\t\t\t\t\t{indent(route_b_transaction, 5).lstrip()}
\t\t\t\t}}
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\t{indent(status_rows, 5).lstrip()}
\t\t\t\t\t{indent(route_a_status, 5).lstrip()}
\t\t\t\t\t{indent(route_b_status, 5).lstrip()}
\t\t\t\t}}
\t\t\t\tset_variable = {{ name = {p}_receipt_active value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_route value = scope:zg361_pp_route }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ scope:zg361_pp_route = 1 }}
\t\t\t\t\tset_variable = {{ name = {p}_{mechanism.field} value = 1 }}
\t\t\t\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_evidence_led add = 1 }}
\t\t\t\t}}
\t\t\t\telse_if = {{
\t\t\t\t\tlimit = {{ scope:zg361_pp_route = 2 }}
\t\t\t\t\tset_variable = {{ name = {p}_{mechanism.field} value = 2 }}
\t\t\t\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_political add = 1 }}
\t\t\t\t}}
\t\t\t\telse = {{
\t\t\t\t\tset_variable = {{ name = {p}_deferred value = 1 }}
\t\t\t\t\tset_variable = {{ name = {p}_policy_debt_due_days value = {defer_days(mechanism.mechanism_id)} }}
\t\t\t\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_policy_debt add = 1 }}
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ NOT = {{ scope:zg361_pp_route = 3 }} }}
\t\t\t\t\t{indent(semantic, 5).lstrip()}
\t\t\t\t\t{indent(payment, 5).lstrip()}
\t\t\t\t}}
\t\t\t\t{indent(post_operation, 4).lstrip()}
\t\t\t\tzg361_pp_m{mechanism.mechanism_id:03d}_consume_effect = yes
\t\t\t\t{deadline_calls}
\t\t\t\tset_variable = {{ name = zg361_pp_runtime_applied value = 1 }}
\t\t\t}}
\t\t}}
\t}}
}}'''


def render_consumer(mechanism: MechanismSpec) -> str:
    state = mechanism_stage(mechanism.mechanism_id)
    domain = DOMAIN_BY_KEY[mechanism.domain]
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    consumer_guard = "always = yes"
    if mechanism.mechanism_id == 166:
        consumer_guard = f'''trigger_if = {{
\tlimit = {{ var:{p}_route = 1 }}
\tvar:{p}_nomination_slot_refunded = 1
\tvar:{p}_packet_active_after = 0
}}
trigger_else = {{ always = yes }}'''
    extra_conservation_rows: list[str] = []
    for extra_resource in dict.fromkeys(
        (
            *EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
            *ROUTE_A_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
            *ROUTE_B_EXTRA_RESOURCES_BY_ID.get(mechanism.mechanism_id, ()),
        )
    ):
        extra_conservation_rows.append(f'''set_variable = {{ name = zg361_pp_{mechanism.domain}_{extra_resource}_partition value = var:zg361_pp_{mechanism.domain}_{extra_resource}_available }}
\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_{extra_resource}_partition add = var:zg361_pp_{mechanism.domain}_{extra_resource}_reserved }}
\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_{extra_resource}_partition add = var:zg361_pp_{mechanism.domain}_{extra_resource}_settled }}
\t\tset_variable = {{ name = zg361_pp_{mechanism.domain}_{extra_resource}_conserved value = 0 }}
\t\tif = {{ limit = {{ var:zg361_pp_{mechanism.domain}_{extra_resource}_partition = var:zg361_pp_{mechanism.domain}_{extra_resource}_authorized }} set_variable = {{ name = zg361_pp_{mechanism.domain}_{extra_resource}_conserved value = 1 }} }}'''
        )
    extra_conservation = "\n\t\t".join(extra_conservation_rows)
    receipt_revision = ""
    if mechanism.mechanism_id == 147:
        receipt_revision = f'''set_variable = {{ name = {p}_receipt_revision value = var:zg361_case_t_revision }}'''
    return f'''zg361_pp_m{mechanism.mechanism_id:03d}_consume_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\t{indent(full_guard(mechanism.domain, state, f"var:{p}_receipt_owner", f"var:{p}_receipt_subject", f"var:{p}_receipt_cycle", f"var:{p}_receipt_case", f"var:{p}_receipt_state"), 3).lstrip()}
\t\t\tvar:{p}_receipt_active = 1
\t\t\tvar:{p}_consumed = 0
\t\t\thas_variable = {p}_route
\t\t\t{indent(consumer_guard, 3).lstrip()}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\thas_variable = {p}_{mechanism.field}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = {p}_consumed value = 1 }}
\t\tset_variable = {{ name = {p}_consumer_revision value = var:zg361_case_{mechanism.domain}_revision }}
\t\t{receipt_revision}
\t\tif = {{ limit = {{ NOT = {{ var:{p}_route = 3 }} }} set_variable = {{ name = {p}_consumer_value value = var:{p}_{mechanism.field} }} }}
\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_completed add = 1 }}
\t\tset_variable = {{ name = zg361_pp_{mechanism.domain}_resource_partition value = var:zg361_pp_{mechanism.domain}_{domain.resource}_available }}
\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_resource_partition add = var:zg361_pp_{mechanism.domain}_{domain.resource}_reserved }}
\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_resource_partition add = var:zg361_pp_{mechanism.domain}_{domain.resource}_settled }}
\t\tset_variable = {{ name = zg361_pp_{mechanism.domain}_resource_conserved value = 0 }}
\t\tif = {{ limit = {{ var:zg361_pp_{mechanism.domain}_resource_partition = var:zg361_pp_{mechanism.domain}_authorized }} set_variable = {{ name = zg361_pp_{mechanism.domain}_resource_conserved value = 1 }} }}
\t\t{extra_conservation}
\t\tzg361_pp_{mechanism.domain}_try_advance_{state:02d}_effect = yes
\t}}
}}'''


def render_audit_schedule(mechanism: MechanismSpec, index: int, days: int) -> str:
    row = case_vars(mechanism.domain)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    event_id = 2000 + mechanism.mechanism_id + (1000 if index > 1 else 0)
    route_schedule = f'''if = {{
\t\tlimit = {{ var:{p}_route = 3 }}
\t\ttrigger_event = {{ id = {EVENT_NAMESPACE}.{event_id} days = {defer_days(mechanism.mechanism_id)} }}
\t}}
\telse = {{ trigger_event = {{ id = {EVENT_NAMESPACE}.{event_id} days = {days} }} }}''' if index == 1 else f'''if = {{
\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\ttrigger_event = {{ id = {EVENT_NAMESPACE}.{event_id} days = {days} }}
\t}}
\telse = {{ set_variable = {{ name = {p}_audit_{index}_state value = 2 }} set_variable = {{ name = {p}_audit_{index}_consumed value = 1 }} }}'''
    return f'''zg361_pp_m{mechanism.mechanism_id:03d}_schedule_audit_{index}_effect = {{
\tif = {{
\t\tlimit = {{ var:{p}_audit_{index}_state = 0 var:{p}_receipt_active = 1 }}
\t\tset_variable = {{ name = {p}_audit_{index}_owner value = var:{row["owner"]} }}
\t\tset_variable = {{ name = {p}_audit_{index}_subject value = this }}
\t\tset_variable = {{ name = {p}_audit_{index}_cycle value = var:{row["cycle"]} }}
\t\tset_variable = {{ name = {p}_audit_{index}_case value = var:{row["case"]} }}
\t\tset_variable = {{ name = {p}_audit_{index}_expected_state value = {mechanism_stage(mechanism.mechanism_id)} }}
\t\tset_variable = {{ name = {p}_audit_{index}_state value = 1 }}
\t\t{route_schedule}
\t}}
}}'''


def render_schedule_stage(domain: DomainSpec, state: int, days: int) -> str:
    row = case_vars(domain.key)
    dl = f"{PREFIX}_{domain.key}_stage_{state}_deadline"
    event_id = 4000 + (ord(domain.key) - ord("t")) * 10 + state
    return f'''zg361_pp_schedule_{domain.key}_stage_{state:02d}_effect = {{
\tzg361_case_kernel_schedule_deadline_effect = {{
\t\tOWNER_VAR = {row["owner"]}
\t\tSUBJECT_VAR = {row["subject"]}
\t\tCYCLE_VAR = {row["cycle"]}
\t\tCASE_VAR = {row["case"]}
\t\tSTATE_VAR = {row["state"]}
\t\tACTIVE_VAR = {row["active"]}
\t\tDEADLINE_OWNER_VAR = {dl}_owner
\t\tDEADLINE_SUBJECT_VAR = {dl}_subject
\t\tDEADLINE_CYCLE_VAR = {dl}_cycle
\t\tDEADLINE_CASE_VAR = {dl}_case
\t\tDEADLINE_STATE_VAR = {dl}_state
\t\tDEADLINE_DAYS_VAR = {dl}_days
\t\tDEADLINE_PENDING_VAR = {dl}_pending
\t\tDEADLINE_EXPIRED_VAR = {dl}_expired
\t\tTICKET_OWNER = var:{row["owner"]}
\t\tTICKET_SUBJECT = this
\t\tTICKET_CYCLE = var:{row["cycle"]}
\t\tTICKET_CASE = var:{row["case"]}
\t\tTICKET_STATE = {state}
\t\tDAYS = {days}
\t\tEVENT = {EVENT_NAMESPACE}.{event_id}
\t}}
}}'''


def render_stage_dispatch(domain: DomainSpec, state: int, stage: tuple[int, ...]) -> str:
    first = stage[0]
    ai_calls = []
    for mechanism_id in stage:
        if mechanism_id == 189:
            # #188's D+365 audit owns this dispatch for both player and AI.
            continue
        if mechanism_id in SUBJECT_RESPONSE_IDS:
            # The assessed official owns this response even under an AI
            # manager. Players receive one exact-ticket event; AI subjects take
            # the same self-guarded effect silently and then resume the manager.
            ai_calls.append(queue_subject_response_call(mechanism_id))
            continue
        ai_pre = ""
        if mechanism_id == 190:
            ai_pre += "if = { limit = { NOT = { var:zg361_pp_m189_terminal_code = 2 } } set_variable = { name = zg361_pp_ai_route value = 3 } }\n"
        elif mechanism_id == 191:
            ai_pre += "if = { limit = { NOT = { var:zg361_pp_m189_terminal_code = 3 } } set_variable = { name = zg361_pp_ai_route value = 3 } }\n"
        ai_calls.append(
            f'''set_variable = {{ name = zg361_pp_ai_route value = 1 }}
if = {{ limit = {{ var:zg361_case_{domain.key}_owner = {{ is_at_war = yes }} }} set_variable = {{ name = zg361_pp_ai_route value = 3 }} }}
else_if = {{ limit = {{ var:zg361_case_{domain.key}_owner = {{ OR = {{ has_trait = arbitrary has_trait = ambitious }} }} }} set_variable = {{ name = zg361_pp_ai_route value = 2 }} }}
{ai_pre}zg361_pp_m{mechanism_id:03d}_core_effect = {{
\tROUTE = var:zg361_pp_ai_route
\tTICKET_OWNER = var:zg361_case_{domain.key}_owner
\tTICKET_SUBJECT = this
\tTICKET_CYCLE = var:zg361_case_{domain.key}_cycle_serial
\tTICKET_CASE = var:zg361_case_{domain.key}_case_serial
\tTICKET_STATE = {mechanism_stage(mechanism_id)}
}}'''
        )
    ai_text = "\n\t\t".join(ai_calls)
    queue = queue_decision_call(first)
    if domain.key == "w" and state == 4:
        terminal_queue = queue_decision_call(189)
        first_failure_guard = '''var:zg361_pp_m187_graduation_status = 2
var:zg361_b2_pip_state = 4
var:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case
var:zg361_pp_m188_receipt_active = 0'''
        return f'''zg361_pp_dispatch_w_stage_04_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_case_w_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }}
\t\t\t{indent(first_failure_guard, 3).lstrip()}
\t\t}}
\t\t# A failed first PIP enters the terminal fork immediately; #188 is a
\t\t# post-graduation observation and is explicitly not applicable here.
\t\tzg361_pp_m188_skip_first_failure_effect = yes
\t\tif = {{
\t\t\tlimit = {{ var:zg361_pp_m188_skipped_first_failure = 1 }}
\t\t\tset_variable = {{ name = zg361_pp_ai_route value = 1 }}
\t\t\tif = {{ limit = {{ var:zg361_case_w_owner = {{ OR = {{ has_trait = arbitrary has_trait = ambitious }} }} }} set_variable = {{ name = zg361_pp_ai_route value = 2 }} }}
\t\t\tzg361_pp_m189_core_effect = {{
\t\t\t\tROUTE = var:zg361_pp_ai_route
\t\t\t\tTICKET_OWNER = var:zg361_case_w_owner
\t\t\t\tTICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:zg361_case_w_cycle_serial
\t\t\t\tTICKET_CASE = var:zg361_case_w_case_serial
\t\t\t\tTICKET_STATE = 4
\t\t\t}}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:zg361_case_w_owner = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }}
\t\t\t{indent(first_failure_guard, 3).lstrip()}
\t\t}}
\t\tzg361_pp_m188_skip_first_failure_effect = yes
\t\tif = {{
\t\t\tlimit = {{ var:zg361_pp_m188_skipped_first_failure = 1 }}
\t\t\t{indent(terminal_queue, 3).lstrip()}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{ var:zg361_case_w_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t# Owner-authorized second AI exception: background resolver only, no GUI.
\t\t{ai_text}
\t}}
\telse_if = {{
\t\tlimit = {{ var:zg361_case_w_owner = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t# Graduated cases enter the one-cycle #188 observation first.
\t\t{indent(queue, 2).lstrip()}
\t}}
}}'''
    return f'''zg361_pp_dispatch_{domain.key}_stage_{state:02d}_effect = {{
\tif = {{
\t\tlimit = {{ var:zg361_case_{domain.key}_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t# Owner-authorized second AI exception: background resolver only, no GUI.
\t\t{ai_text}
\t}}
\telse_if = {{
\t\tlimit = {{ var:zg361_case_{domain.key}_owner = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t# Exactly one visible decision is queued.  Each option schedules only the
\t\t# next card, so a 46-card popup storm is structurally impossible.
\t\t{indent(queue, 2).lstrip()}
\t}}
}}'''


def render_barrier(domain: DomainSpec, state: int, stage: tuple[int, ...]) -> str:
    requirements = [
        f"var:{PREFIX}_m{mechanism_id:03d}_consumed = 1"
        for mechanism_id in stage
    ]
    requirements.extend(
        f"var:{PREFIX}_m{mechanism_id:03d}_audit_1_consumed = 1"
        for mechanism_id in stage
        if mechanism_id in DELAYED_STAGE_GATE_IDS
    )
    required = "\n\t\t\t".join(requirements)
    row = case_vars(domain.key)
    final = state == len(domain.stages)
    after = (
        f"zg361_pp_resolve_{domain.key}_outcome_effect = yes"
        if final
        else f"zg361_pp_schedule_{domain.key}_stage_{state + 1:02d}_effect = yes\n\t\t\tzg361_pp_dispatch_{domain.key}_stage_{state + 1:02d}_effect = yes"
    )
    return f'''zg361_pp_{domain.key}_try_advance_{state:02d}_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\t{indent(full_guard(domain.key, state, f"var:{row['owner']}"), 3).lstrip()}
\t\t\t{required}
\t\t}}
\t\tzg361_case_{domain.key}_advance_{state:02d}_effect = {{
\t\t\tTICKET_OWNER = var:{row["owner"]}
\t\t\tTICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:{row["cycle"]}
\t\t\tTICKET_CASE = var:{row["case"]}
\t\t}}
\t\tif = {{ limit = {{ var:zg361_case_kernel_applied = 1 }} {after} }}
\t}}
}}'''


def render_timeout(domain: DomainSpec, state: int, stage: tuple[int, ...]) -> str:
    calls = []
    for mechanism_id in stage:
        p = f"{PREFIX}_m{mechanism_id:03d}"
        calls.append(
            f'''if = {{
\tlimit = {{ var:{p}_consumed = 0 }}
\tzg361_pp_m{mechanism_id:03d}_core_effect = {{
\t\tROUTE = 3
\t\tTICKET_OWNER = var:zg361_pp_{domain.key}_stage_{state}_deadline_owner
\t\tTICKET_SUBJECT = var:zg361_pp_{domain.key}_stage_{state}_deadline_subject
\t\tTICKET_CYCLE = var:zg361_pp_{domain.key}_stage_{state}_deadline_cycle
\t\tTICKET_CASE = var:zg361_pp_{domain.key}_stage_{state}_deadline_case
\t\tTICKET_STATE = var:zg361_pp_{domain.key}_stage_{state}_deadline_state
\t}}
}}'''
        )
    return f'''zg361_pp_{domain.key}_timeout_stage_{state:02d}_effect = {{
\t{indent(chr(10).join(calls), 1).lstrip()}
\tdebug_log = "ZG361PP: exact {domain.code} stage {state} deadline consumed"
}}'''


def render_outcome(domain: DomainSpec, completion_event: int) -> str:
    row = case_vars(domain.key)
    extra_resources = sorted(
        {
            resource
            for mechanism_id in (mid for stage in domain.stages for mid in stage)
            for resource in (
                *EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
                *ROUTE_A_EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
                *ROUTE_B_EXTRA_RESOURCES_BY_ID.get(mechanism_id, ()),
            )
        }
    )
    extra_conserved = "\n\t\t\t".join(
        f"var:zg361_pp_{domain.key}_{resource}_conserved = 1"
        for resource in extra_resources
    )
    return f'''zg361_pp_resolve_{domain.key}_outcome_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_pp_{domain.key}_completed = var:zg361_pp_{domain.key}_authorized
\t\t\tvar:zg361_pp_{domain.key}_resource_conserved = 1
\t\t\t{extra_conserved}
\t\t}}
\t\tset_variable = {{ name = zg361_pp_{domain.key}_outcome value = 0 }}
\t\tif = {{ limit = {{ var:zg361_pp_{domain.key}_evidence_led > var:zg361_pp_{domain.key}_political }} set_variable = {{ name = zg361_pp_{domain.key}_outcome value = 1 }} add_prestige = 25 }}
\t\telse_if = {{ limit = {{ var:zg361_pp_{domain.key}_political > var:zg361_pp_{domain.key}_evidence_led }} set_variable = {{ name = zg361_pp_{domain.key}_outcome value = -1 }} add_stress = minor_stress_gain }}
\t\tset_variable = {{ name = zg361_pp_{domain.key}_visible_receipt_revision value = var:{row["revision"]} }}
\t\tset_variable = {{ name = zg361_pp_{domain.key}_portfolio_done_cycle value = var:{row["cycle"]} }}
\t\tif = {{
\t\t\tlimit = {{ var:{row["owner"]} = {{ is_ai = no }} }}
\t\t\tsave_scope_as = zg361_pp_completion_subject
\t\t\t# Retain the queue lock through the visible completion card, otherwise a
\t\t\t# same-day central adapter call could overlap it with the next domain.
\t\t\tvar:{row["owner"]} = {{ trigger_event = {{ id = {EVENT_NAMESPACE}.{completion_event} days = 1 }} }}
\t\t}}
\t\telse = {{
\t\t\t# The authorized AI route has no visible card and releases immediately.
\t\t\tvar:{row["owner"]} = {{ set_variable = {{ name = zg361_pp_portfolio_queue_active value = 0 }} }}
\t\t}}
\t\tdebug_log = "ZG361PP: completed {domain.code} runtime case"
\t}}
}}'''


def render_effects() -> bytes:
    """Render the frozen historical monolith for parity validation only.

    Product output is emitted by :func:`render_effect_parts`.  Keeping this
    aggregate in memory gives all purpose shards one byte-stable source of
    truth while preserving the original top-level block order.
    """

    sections = [
        "# ZhongGuo 361 T/U/V/W runtime: mechanisms 146--191.",
        "# Routes: 1 evidence-led; 2 political/extractive; 3 bounded policy debt.",
        "# Only integration seam: zg361_pp_manager_portfolio_adapter_effect.",
    ]
    sections.append(render_portfolio_adapter())
    sections.append(render_m188_first_failure_skip())
    sections.append(render_m189_no_relapse_skip())
    for domain_index, domain in enumerate(DOMAINS, start=1):
        sections.append(render_open(domain))
        for state, (stage, days) in enumerate(zip(domain.stages, domain.stage_deadlines), start=1):
            sections.append(render_schedule_stage(domain, state, days))
            sections.append(render_stage_dispatch(domain, state, stage))
            sections.append(render_barrier(domain, state, stage))
            sections.append(render_timeout(domain, state, stage))
        sections.append(render_outcome(domain, 9000 + domain_index))
    for mechanism in MECHANISMS:
        sections.append(render_manager_entry(mechanism))
        subject = render_subject_response(mechanism)
        if subject:
            sections.append(subject)
        sections.append(render_core(mechanism))
        sections.append(render_consumer(mechanism))
        for index, days in enumerate(mechanism.deadlines, start=1):
            sections.append(render_audit_schedule(mechanism, index, days))
    return generated("\n\n".join(sections))


def _skip_comment(text: str, index: int) -> int:
    newline = text.find("\n", index)
    return len(text) if newline < 0 else newline + 1


def _skip_quoted_string(text: str, index: int) -> int:
    index += 1
    escaped = False
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
        index += 1
    raise ValueError("unterminated quoted string in generated PP script")


def _block_end(text: str, index: int) -> int:
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("unbalanced generated PP script block")
        index += 1
    raise ValueError("unterminated generated PP script block")


def top_level_effect_blocks(
    payload: bytes | str,
) -> tuple[tuple[str, str], ...]:
    """Return exact top-level effect blocks, ignoring calls and comments."""

    text = (
        payload.decode("utf-8-sig")
        if isinstance(payload, bytes)
        else payload.lstrip("\ufeff")
    )
    blocks: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if not (char.isalpha() or char == "_"):
            index += 1
            continue
        start = index
        index += 1
        while index < len(text) and (
            text[index].isalnum() or text[index] in "_."
        ):
            index += 1
        name = text[start:index]
        cursor = index
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "=":
            continue
        cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            continue
        end = _block_end(text, cursor)
        if name.startswith("zg361_pp_") and name.endswith("_effect"):
            blocks.append((name, text[start:end]))
        index = end
    return tuple(blocks)


def _validate_effect_groups(
    source_blocks: tuple[tuple[str, str], ...],
) -> None:
    source_names = tuple(name for name, _block in source_blocks)
    configured_names = tuple(
        name for group in EFFECT_GROUPS for name in group.effect_names
    )
    filenames = tuple(group.filename for group in EFFECT_GROUPS)
    if len(source_names) != 275 or len(set(source_names)) != 275:
        raise ValueError(
            "feedback/promotion/PIP historical render must contain "
            "275 unique top-level effects"
        )
    if len(EFFECT_GROUPS) != 39 or len(filenames) != len(set(filenames)):
        raise ValueError(
            "feedback/promotion/PIP runtime must remain split into "
            "39 uniquely named purpose files"
        )
    if configured_names != source_names:
        missing = sorted(set(source_names) - set(configured_names))
        extra = sorted(set(configured_names) - set(source_names))
        raise ValueError(
            "feedback/promotion/PIP purpose map changed effect order or coverage: "
            f"missing={missing}, extra={extra}"
        )
    for group in EFFECT_GROUPS:
        count = len(group.effect_names)
        if count < 1:
            raise ValueError(f"empty PP purpose shard: {group.filename}")
        if count > EFFECT_HARD_MAX:
            exception = EFFECT_HARD_LIMIT_EXCEPTIONS.get(group.filename)
            if (
                exception is None
                or len(exception) != 2
                or not exception[0].strip()
                or not exception[1].strip()
            ):
                raise ValueError(
                    f"{group.filename} exceeds {EFFECT_HARD_MAX} effects "
                    "without a reason and CK3 live-evidence reference"
                )
        elif count > EFFECT_TARGET_MAX:
            raise ValueError(
                f"{group.filename} exceeds the {EFFECT_TARGET_MAX}-effect "
                "B7 target"
            )
    oversized = {
        group.filename
        for group in EFFECT_GROUPS
        if len(group.effect_names) > EFFECT_HARD_MAX
    }
    if set(EFFECT_HARD_LIMIT_EXCEPTIONS) != oversized:
        raise ValueError(
            "feedback/promotion/PIP hard-limit exceptions must exactly match "
            f"oversized shards: exceptions={sorted(EFFECT_HARD_LIMIT_EXCEPTIONS)}, "
            f"oversized={sorted(oversized)}"
        )


def render_effect_parts() -> dict[str, bytes]:
    """Render 39 purpose shards without changing any top-level block bytes."""

    source_blocks = top_level_effect_blocks(render_effects())
    _validate_effect_groups(source_blocks)
    by_name = dict(source_blocks)
    return {
        group.filename: generated(
            f"# PURPOSE: {group.purpose}.\n\n"
            + "\n\n".join(by_name[name] for name in group.effect_names)
        )
        for group in EFFECT_GROUPS
    }


def next_in_stage(mechanism_id: int) -> int | None:
    if mechanism_id in DELAYED_STAGE_GATE_IDS:
        # The next card is dispatched only by the target-bound audit.  This is
        # material for #188, whose terminal fork must not appear on D+1.
        return None
    domain = DOMAIN_BY_ID[mechanism_id]
    for stage in domain.stages:
        if mechanism_id in stage:
            index = stage.index(mechanism_id)
            return stage[index + 1] if index + 1 < len(stage) else None
    raise AssertionError(mechanism_id)


def delayed_consumer_write(mechanism: MechanismSpec, index: int) -> str:
    """Consume one mechanism-specific payload after a valid delayed ticket."""

    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    field = DELAYED_CONSUMER_FIELD_BY_ID[mechanism.mechanism_id]
    return f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_audit_{index}_business_input value = var:{p}_{field} }}
\t\t\t\tset_variable = {{ name = {p}_audit_{index}_business_settled value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_visible_outcome_code value = var:{p}_route }}
\t\t\t}}
\t\t\telse = {{
\t\t\t\t# Route C closes only its policy-debt timer; it cannot manufacture
\t\t\t\t# the typed business field named above.
\t\t\t\tset_variable = {{ name = {p}_audit_{index}_policy_debt_settled value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_visible_outcome_code value = 3 }}
\t\t\t}}
\t\t\tchange_variable = {{ name = zg361_pp_{mechanism.domain}_visible_receipt_revision add = 1 }}'''


def render_player_event(mechanism: MechanismSpec) -> str:
    state = mechanism_stage(mechanism.mechanism_id)
    row = case_vars(mechanism.domain)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    desc = f"zg361pp.{mechanism.mechanism_id}.desc"
    if mechanism.domain in {"t", "w"}:
        frozen = f"zg361_pp_{mechanism.domain}_frozen_grade"
        desc = f'''{{
\t\tdesc = zg361pp.{mechanism.mechanism_id}.desc
\t\tfirst_valid = {{
\t\t\ttriggered_desc = {{ trigger = {{ scope:zg361_pp_prompt_subject = {{ var:{frozen} = 3 }} }} desc = zg361pp.grade.375 }}
\t\t\ttriggered_desc = {{ trigger = {{ scope:zg361_pp_prompt_subject = {{ var:{frozen} = 2 }} }} desc = zg361pp.grade.350 }}
\t\t\ttriggered_desc = {{ trigger = {{ scope:zg361_pp_prompt_subject = {{ var:{frozen} = 1 }} }} desc = zg361pp.grade.325 }}
\t\t}}
\t}}'''
    nxt = next_in_stage(mechanism.mechanism_id)
    chain = ""
    if nxt is not None:
        chain = f'''if = {{
\t\t\tlimit = {{ scope:zg361_pp_prompt_subject = {{ var:{p}_consumed = 1 }} }}
\t\t\tscope:zg361_pp_prompt_subject = {{ {queue_decision_call(nxt)} }}
\t\t}}'''
    options = []
    for route, letter in ((1, "a"), (2, "b"), (3, "c")):
        option_guard = business_dependency_conditions(mechanism.mechanism_id, route)
        options.append(
            f'''option = {{
\t\tname = zg361pp.{mechanism.mechanism_id}.{letter}
\t\ttrigger = {{ scope:zg361_pp_prompt_subject = {{ {option_guard} }} }}
\t\tscope:zg361_pp_prompt_subject = {{
\t\t\tzg361_pp_m{mechanism.mechanism_id:03d}_manager_apply_effect = {{
\t\t\t\tROUTE = {route}
\t\t\t\tTICKET_OWNER = scope:zg361_pp_prompt_owner
\t\t\t\tTICKET_SUBJECT = scope:zg361_pp_prompt_subject
\t\t\t\tTICKET_CYCLE = scope:zg361_pp_prompt_cycle
\t\t\t\tTICKET_CASE = scope:zg361_pp_prompt_case
\t\t\t\tTICKET_STATE = scope:zg361_pp_prompt_state
\t\t\t}}
\t\t}}
\t\t{chain}
\t}}'''
        )
    return f'''# {mechanism.mechanism_id:03d}: one queued manager decision; never shown to AI.
zg361pp.{mechanism.mechanism_id} = {{
\ttype = character_event
\ttheme = vassal
\ttitle = zg361pp.{mechanism.mechanism_id}.t
\tdesc = {desc}
\ttrigger = {{
\t\tis_ai = no
\t\tzg361_is_celestial_liege_trigger = yes
\t\texists = scope:zg361_pp_prompt_owner
\t\texists = scope:zg361_pp_prompt_subject
\t\tthis = scope:zg361_pp_prompt_owner
\t\tscope:zg361_pp_prompt_subject = {{
\t\t\tzg361_is_reviewable_vassal_trigger = yes
\t\t\tliege = scope:zg361_pp_prompt_owner
\t\t\tvar:{row["owner"]} = scope:zg361_pp_prompt_owner
\t\t\tvar:{row["subject"]} = this
\t\t\tvar:{row["cycle"]} = scope:zg361_pp_prompt_cycle
\t\t\tvar:{row["case"]} = scope:zg361_pp_prompt_case
\t\t\tvar:{row["state"]} = scope:zg361_pp_prompt_state
\t\t\tvar:{row["state"]} = {state}
\t\t\tvar:{p}_receipt_active = 0
\t\t}}
\t}}
\t{indent(chr(10).join(options), 1).lstrip()}
}}'''


def render_subject_response_event(mechanism: MechanismSpec) -> str:
    state = mechanism_stage(mechanism.mechanism_id)
    row = case_vars(mechanism.domain)
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    event_id = 5000 + mechanism.mechanism_id
    return f'''# {mechanism.mechanism_id:03d}: the assessed official, never the manager,
# owns this response. AI subjects use the same effect silently at the queue.
zg361pp.{event_id} = {{
\ttype = character_event
\ttheme = vassal
\ttitle = zg361pp.{mechanism.mechanism_id}.t
\tdesc = zg361pp.{mechanism.mechanism_id}.desc
\ttrigger = {{
\t\tis_ai = no
\t\thas_game_rule = zg361_on
\t\texists = scope:zg361_pp_subject_prompt_owner
\t\texists = scope:zg361_pp_subject_prompt_subject
\t\tthis = scope:zg361_pp_subject_prompt_subject
\t\tvar:{row["owner"]} = scope:zg361_pp_subject_prompt_owner
\t\tvar:{row["subject"]} = this
\t\tvar:{row["cycle"]} = scope:zg361_pp_subject_prompt_cycle
\t\tvar:{row["case"]} = scope:zg361_pp_subject_prompt_case
\t\tvar:{row["state"]} = scope:zg361_pp_subject_prompt_state
\t\tvar:{row["state"]} = {state}
\t\tvar:{row["active"]} = 1
\t\tNOT = {{ has_variable = {p}_subject_response }}
\t}}
\toption = {{
\t\tname = zg361pp.{mechanism.mechanism_id}.subject.a
\t\tzg361_pp_m{mechanism.mechanism_id:03d}_subject_response_effect = {{ ROUTE = 1 }}
\t\tzg361_pp_m{mechanism.mechanism_id:03d}_resume_after_subject_effect = yes
\t}}
\toption = {{
\t\tname = zg361pp.{mechanism.mechanism_id}.subject.b
\t\tzg361_pp_m{mechanism.mechanism_id:03d}_subject_response_effect = {{ ROUTE = 2 }}
\t\tzg361_pp_m{mechanism.mechanism_id:03d}_resume_after_subject_effect = yes
\t}}
}}'''


def render_audit_event(mechanism: MechanismSpec, index: int) -> str:
    p = f"{PREFIX}_m{mechanism.mechanism_id:03d}"
    event_id = 2000 + mechanism.mechanism_id + (1000 if index > 1 else 0)
    special_audit = ""
    if mechanism.mechanism_id == 149:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ var:{p}_route = 1 var:{p}_funded = 1 var:{p}_obligation_status = 1 }}
\t\t\t\tset_variable = {{ name = {p}_obligation_status value = 2 }}
\t\t\t\tset_variable = {{ name = {p}_fulfilled_receipt value = var:{p}_obligation_id }}
\t\t\t}}
\t\t\telse_if = {{
\t\t\t\tlimit = {{ var:{p}_route = 2 var:{p}_obligation_status = 1 }}
\t\t\t\tset_variable = {{ name = {p}_obligation_status value = 3 }}
\t\t\t\tset_variable = {{ name = {p}_breach_receipt value = var:{p}_obligation_id }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 150:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ var:{p}_route = 1 var:{p}_funded = 1 var:{p}_written = 1 var:{p}_obligation_status = 1 }}
\t\t\t\tset_variable = {{ name = {p}_obligation_status value = 2 }}
\t\t\t\tset_variable = {{ name = {p}_fulfilled_receipt value = var:{p}_obligation_id }}
\t\t\t}}
\t\t\telse_if = {{
\t\t\t\tlimit = {{ var:{p}_route = 2 var:{p}_obligation_status = 1 }}
\t\t\t\tset_variable = {{ name = {p}_obligation_status value = 3 }}
\t\t\t\tset_variable = {{ name = {p}_breach_receipt value = var:{p}_obligation_id }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 151:
        if index == 1:
            special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_delivery_audit_closed value = 1 }}
\t\t\t\tif = {{ limit = {{ var:{p}_delivered = 1 }} set_variable = {{ name = {p}_delivery_receipt_valid value = 1 }} }}
\t\t\t}}'''
        else:
            special_audit = f'''set_variable = {{ name = {p}_appeal_clock_closed value = 1 }}
\t\t\tif = {{
\t\t\t\tlimit = {{ has_variable = {p}_appeal_filed var:{p}_appeal_filed = 1 }}
\t\t\t\tset_variable = {{ name = {p}_appeal_result_grade value = var:zg361_result_grade }}
\t\t\t\tset_variable = {{ name = {p}_non_aggravation_ok value = 0 }}
\t\t\t\tif = {{ limit = {{ var:zg361_result_grade >= var:{p}_appeal_snapshot_grade }} set_variable = {{ name = {p}_non_aggravation_ok value = 1 }} }}
\t\t\t}}
\t\t\telse = {{ set_variable = {{ name = {p}_appeal_closed_without_filing value = 1 }} }}'''
    elif mechanism.mechanism_id == 159:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tvar:zg361_case_u_owner = {{
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_shelving_last_audit_candidate value = root }}
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_shelving_last_audit_cycle value = var:zg361_review_serial }}
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_shelving_last_audit_active value = var:zg361_pp_u_shelving_active }}
\t\t\t\t}}
\t\t\t}}'''
    elif mechanism.mechanism_id == 167:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ var:{p}_observation_settled = 0 }}
\t\t\t\tset_variable = {{ name = {p}_competent value = 0 }}
\t\t\t\tif = {{ limit = {{ stewardship >= 10 }} set_variable = {{ name = {p}_competent value = 1 }} }}
\t\t\t\tset_variable = {{ name = {p}_sponsor_credit_delta value = {{ value = var:{p}_sponsor_strength multiply = -1 }} }}
\t\t\t\tif = {{ limit = {{ var:{p}_competent = 1 }} set_variable = {{ name = {p}_sponsor_credit_delta value = var:{p}_sponsor_strength }} }}
\t\t\t\tset_variable = {{ name = {p}_observation_settled value = 1 }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 168:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ var:{p}_sample_pending = 1 var:{p}_sample_settled = 0 }}
\t\t\t\tset_variable = {{ name = {p}_competent value = 0 }}
\t\t\t\tif = {{ limit = {{ stewardship >= 10 }} set_variable = {{ name = {p}_competent value = 1 }} }}
\t\t\t\tvar:zg361_case_u_owner = {{
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_next_quota_delta value = -1 }}
\t\t\t\t\tif = {{ limit = {{ root.var:{p}_prescreen_pass_snapshot = 1 root.var:{p}_competent = 1 }} set_variable = {{ name = zg361_pp_u_next_quota_delta value = 1 }} }}
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_next_quota_pending value = 1 }}
\t\t\t\t\tset_variable = {{ name = zg361_pp_u_last_settled_attempt value = root.var:{p}_attempt_id }}
\t\t\t\t}}
\t\t\t\tset_variable = {{ name = {p}_sample_pending value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_sample_settled value = 1 }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 180:
        if index == 1:
            special_audit = f'''if = {{
\t\t\t\tlimit = {{ var:{p}_route = 1 var:{p}_gap_completion = 1 var:{p}_retry_available = 0 }}
\t\t\t\tset_variable = {{ name = {p}_retry_available value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_retry_unlock_reason value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_retry_settled_receipt value = var:{p}_prior_gap_id }}
\t\t\t}}'''
        else:
            special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} var:{p}_retry_available = 0 }}
\t\t\t\tset_variable = {{ name = {p}_retry_available value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_retry_unlock_reason value = 2 }}
\t\t\t\tset_variable = {{ name = {p}_retry_settled_receipt value = var:{p}_prior_gap_id }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 183:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{
\t\t\t\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\t\t\t\tvar:zg361_b2_pip_subject = this
\t\t\t\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\t\t\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\t\t\t\tvar:zg361_b2_pip_subject_response_case = var:zg361_b2_pip_case
\t\t\t\t}}
\t\t\t\tset_variable = {{ name = {p}_acknowledgement_status value = var:zg361_b2_pip_subject_response }}
\t\t\t\tset_variable = {{ name = {p}_subject_statement_code value = var:zg361_b2_pip_subject_response }}
\t\t\t\tset_variable = {{ name = {p}_subject_statement_author value = var:zg361_b2_pip_subject_response_author }}
\t\t\t\tset_variable = {{ name = {p}_subject_signed value = 0 }}
\t\t\t\tif = {{ limit = {{ OR = {{ var:zg361_b2_pip_subject_response = 1 var:zg361_b2_pip_subject_response = 2 }} }} set_variable = {{ name = {p}_subject_signed value = 1 }} }}
\t\t\t}}'''
    elif mechanism.mechanism_id == 185:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_midpoint_pending value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_midpoint_completed value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_progress_snapshot value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_progress_truth_status value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_progress_red_code value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_resource_delivery_valid value = 0 }}
\t\t\t\t# #185 projects only B2's exact D+180 producer. Missing or stale
\t\t\t\t# provenance retains the typed RED initialized above.
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_receipt
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_status
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_red_code
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_owner
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_subject
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_cycle
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_case
\t\t\t\t\t\thas_variable = zg361_b2_pip_midpoint_progress_delta
\t\t\t\t\t}}
\t\t\t\t\tif = {{
\t\t\t\t\t\tlimit = {{
\t\t\t\t\t\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\t\t\t\t\t\tvar:zg361_b2_pip_subject = this
\t\t\t\t\t\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\t\t\t\t\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\t\t\t\t\t\tvar:zg361_b2_pip_midpoint_receipt = var:zg361_b2_pip_case
\t\t\t\t\t\t\tvar:zg361_b2_pip_midpoint_progress_owner = var:zg361_b2_pip_owner
\t\t\t\t\t\t\tvar:zg361_b2_pip_midpoint_progress_subject = this
\t\t\t\t\t\t\tvar:zg361_b2_pip_midpoint_progress_cycle = var:zg361_b2_pip_cycle
\t\t\t\t\t\t\tvar:zg361_b2_pip_midpoint_progress_case = var:zg361_b2_pip_case
\t\t\t\t\t\t}}
\t\t\t\t\t\tset_variable = {{ name = {p}_progress_snapshot value = var:zg361_b2_pip_midpoint_progress_delta }}
\t\t\t\t\t\tset_variable = {{ name = {p}_progress_truth_status value = var:zg361_b2_pip_midpoint_progress_status }}
\t\t\t\t\t\tset_variable = {{ name = {p}_progress_red_code value = var:zg361_b2_pip_midpoint_progress_red_code }}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\t\t\t\t\tvar:zg361_b2_pip_subject = this
\t\t\t\t\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\t\t\t\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\t\t\t\t\tvar:zg361_b2_pip_support_reserved = 1
\t\t\t\t\t\tvar:zg361_b2_pip_support_budget_spent = 25
\t\t\t\t\t\tvar:zg361_b2_pip_support_hours = 12
\t\t\t\t\t}}
\t\t\t\t\tset_variable = {{ name = {p}_resource_delivery_valid value = 1 }}
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ var:{p}_route = 1 }}
\t\t\t\t\tset_variable = {{ name = {p}_midpoint_status value = 1 }}
\t\t\t\t}}
\t\t\t\telse_if = {{
\t\t\t\t\tlimit = {{ var:{p}_route = 2 }}
\t\t\t\t\tset_variable = {{ name = {p}_midpoint_status value = 2 }}
\t\t\t\t\tset_variable = {{ name = {p}_late_correction_invalid value = 1 }}
\t\t\t\t}}
\t\t\t}}
\t\t\tzg361_pp_w_try_advance_02_effect = yes'''
    elif mechanism.mechanism_id == 187:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_evaluation_pending value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_graduation_status value = 0 }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\t\t\t\t\tvar:zg361_b2_pip_subject = this
\t\t\t\t\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\t\t\t\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\t\t\t\t\tvar:zg361_b2_pip_state = 3
\t\t\t\t\t\tvar:zg361_b2_pip_graduation_receipt = var:zg361_b2_pip_case
\t\t\t\t\t\tvar:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_status = 1
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_red_code = 0
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_receipt = var:zg361_b2_pip_case
\t\t\t\t\t}}
\t\t\t\t\tset_variable = {{ name = {p}_key_milestones_met value = 1 }}
\t\t\t\t\tset_variable = {{ name = {p}_stability_days_observed value = var:zg361_b2_pip_stability_days_observed }}
\t\t\t\t\tset_variable = {{ name = {p}_independent_review_pass value = var:zg361_b2_pip_independent_review_status }}
\t\t\t\t\tset_variable = {{ name = {p}_independent_review_red_code value = var:zg361_b2_pip_independent_review_red_code }}
\t\t\t\t\tset_variable = {{ name = {p}_graduation_status value = 1 }}
\t\t\t\t}}
\t\t\t\telse_if = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\tvar:zg361_b2_pip_owner = var:zg361_case_w_owner
\t\t\t\t\t\tvar:zg361_b2_pip_subject = this
\t\t\t\t\t\tvar:zg361_b2_pip_cycle = var:zg361_case_w_cycle_serial
\t\t\t\t\t\tvar:zg361_b2_pip_case = var:zg361_case_w_case_serial
\t\t\t\t\t\tvar:zg361_b2_pip_state = 4
\t\t\t\t\t\tvar:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case
\t\t\t\t\t\tvar:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_status = 2
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_red_code = 0
\t\t\t\t\t\tvar:zg361_b2_pip_independent_review_receipt = var:zg361_b2_pip_case
\t\t\t\t\t}}
\t\t\t\t\tset_variable = {{ name = {p}_key_milestones_met value = 0 }}
\t\t\t\t\tset_variable = {{ name = {p}_stability_days_observed value = var:zg361_b2_pip_stability_days_observed }}
\t\t\t\t\tset_variable = {{ name = {p}_independent_review_pass value = var:zg361_b2_pip_independent_review_status }}
\t\t\t\t\tset_variable = {{ name = {p}_independent_review_red_code value = var:zg361_b2_pip_independent_review_red_code }}
\t\t\t\t\tset_variable = {{ name = {p}_graduation_status value = 2 }}
\t\t\t\t\tif = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_appeal_weight value = 1 }} }}
\t\t\t\t}}
\t\t\t}}
\t\t\tzg361_pp_w_try_advance_03_effect = yes'''
    elif mechanism.mechanism_id == 188:
        followup = queue_decision_call(189)
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_observation_pending value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_observation_closed value = 1 }}
\t\t\t\tset_variable = {{ name = {p}_same_category_relapse value = 0 }}
\t\t\t\tset_variable = {{ name = {p}_relapse_status value = 2 }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\thas_variable = zg361_result_case_owner
\t\t\t\t\t\thas_variable = zg361_result_cycle_serial
\t\t\t\t\t\thas_variable = zg361_result_case_serial
\t\t\t\t\t\thas_variable = zg361_result_case_state
\t\t\t\t\t\thas_variable = zg361_result_grade
\t\t\t\t\t\thas_variable = zg361_result_grade_reason
\t\t\t\t\t\tvar:zg361_result_case_owner = var:zg361_case_w_owner
\t\t\t\t\t\tvar:zg361_result_cycle_serial = var:{p}_observation_due_cycle
\t\t\t\t\t\tvar:zg361_result_case_state >= 3
\t\t\t\t\t\tvar:zg361_result_grade = 1
\t\t\t\t\t}}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_owner value = var:zg361_result_case_owner }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_subject value = this }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_cycle value = var:zg361_result_cycle_serial }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_case value = var:zg361_result_case_serial }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_state value = var:zg361_result_case_state }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_grade value = var:zg361_result_grade }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_result_reason value = var:zg361_result_grade_reason }}
\t\t\t\t\tset_variable = {{ name = {p}_observed_category value = 1 }}
\t\t\t\t\tif = {{ limit = {{ var:zg361_result_grade_reason = 5 }} set_variable = {{ name = {p}_observed_category value = 3 }} }}
\t\t\t\t\tif = {{
\t\t\t\t\t\tlimit = {{
\t\t\t\t\t\t\tOR = {{
\t\t\t\t\t\t\t\tvar:{p}_route = 2
\t\t\t\t\t\t\t\tAND = {{ var:{p}_route = 1 var:{p}_observed_category = var:{p}_category_snapshot }}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\tif = {{ limit = {{ var:{p}_observed_category = var:{p}_category_snapshot }} set_variable = {{ name = {p}_same_category_relapse value = 1 }} }}
\t\t\t\t\t\tset_variable = {{ name = {p}_relapse_status value = 1 }}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:{p}_relapse_status = 2 }}
\t\t\t\tzg361_pp_m189_skip_no_relapse_effect = yes
\t\t\t}}
\t\t\telse_if = {{
\t\t\t\tlimit = {{ var:zg361_case_w_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t\tset_variable = {{ name = zg361_pp_ai_route value = 3 }}
\t\t\t\tif = {{ limit = {{ NOT = {{ var:{p}_route = 3 }} }} set_variable = {{ name = zg361_pp_ai_route value = 1 }} }}
\t\t\t\tif = {{ limit = {{ NOT = {{ var:{p}_route = 3 }} var:zg361_case_w_owner = {{ has_trait = arbitrary }} }} set_variable = {{ name = zg361_pp_ai_route value = 2 }} }}
\t\t\t\tzg361_pp_m189_core_effect = {{
\t\t\t\t\tROUTE = var:zg361_pp_ai_route
\t\t\t\t\tTICKET_OWNER = var:zg361_case_w_owner
\t\t\t\t\tTICKET_SUBJECT = this
\t\t\t\t\tTICKET_CYCLE = var:zg361_case_w_cycle_serial
\t\t\t\t\tTICKET_CASE = var:zg361_case_w_case_serial
\t\t\t\t\tTICKET_STATE = 4
\t\t\t\t}}
\t\t\t}}
\t\t\telse_if = {{
\t\t\t\tlimit = {{ var:zg361_case_w_owner = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t\t{indent(followup, 4).lstrip()}
\t\t\t}}
\t\t\t# The stage timeout may already have consumed #189 as route C while
\t\t\t# this delayed #188 audit was pending.  Recheck the barrier after the
\t\t\t# audit closes so that exact fallback cannot strand W in state four.
\t\t\tzg361_pp_w_try_advance_04_effect = yes'''
    elif mechanism.mechanism_id == 190:
        special_audit = f'''if = {{
\t\t\t\tlimit = {{ NOT = {{ var:{p}_route = 3 }} }}
\t\t\t\tset_variable = {{ name = {p}_audit_delivery_acl_pass value = 0 }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\tvar:{p}_receiving_manager = var:{p}_acl_receiver
\t\t\t\t\t\tvar:{p}_receiving_manager = {{
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_disclosure_bundle = root.var:{p}_disclosure_bundle_id
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_disclosure_subject = root
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_disclosure_cycle = root.var:zg361_case_w_cycle_serial
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_disclosure_case = root.var:zg361_case_w_case_serial
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_disclosure_vacancy = root.var:{p}_vacancy_id_snapshot
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_goal = root.var:{p}_goal_snapshot
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_support = root.var:{p}_support_snapshot
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_completion = root.var:{p}_completion_snapshot
\t\t\t\t\t\t\tvar:zg361_pp_received_transfer_subject_statement = root.var:{p}_subject_statement_snapshot
\t\t\t\t\t\t}}
\t\t\t\t\t\tvar:zg361_transfer_vacancy_status = 2
\t\t\t\t\t\tvar:zg361_transfer_vacancy_active = 1
\t\t\t\t\t\tvar:zg361_transfer_request_pp_owner = root.var:zg361_case_w_owner
\t\t\t\t\t\tvar:zg361_transfer_request_pp_subject = root
\t\t\t\t\t\tvar:zg361_transfer_request_pp_cycle = root.var:zg361_case_w_cycle_serial
\t\t\t\t\t\tvar:zg361_transfer_request_pp_case = root.var:zg361_case_w_case_serial
\t\t\t\t\t\tvar:zg361_transfer_request_vacancy = root.var:{p}_vacancy_id_snapshot
\t\t\t\t\t}}
\t\t\t\t\tset_variable = {{ name = {p}_audit_delivery_acl_pass value = 1 }}
\t\t\t\t}}
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:{p}_audit_delivery_acl_pass = 1 }}
\t\t\t\tzg361_career_hc_settle_pp_transfer_effect = yes
\t\t\t\tset_variable = {{ name = {p}_audit_external_status value = var:zg361_transfer_vacancy_status }}
\t\t\t\tset_variable = {{ name = {p}_audit_external_red_code value = var:zg361_transfer_adapter_red_code }}
\t\t\t}}'''
    typed_audit = delayed_consumer_write(mechanism, index)
    return f'''zg361pp.{event_id} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tvar:{p}_audit_{index}_owner = var:zg361_case_{mechanism.domain}_owner
\t\t\t\tvar:{p}_audit_{index}_subject = this
\t\t\t\tvar:{p}_audit_{index}_cycle = var:zg361_case_{mechanism.domain}_cycle_serial
\t\t\t\tvar:{p}_audit_{index}_case = var:zg361_case_{mechanism.domain}_case_serial
\t\t\t\tvar:{p}_audit_{index}_expected_state = var:{p}_receipt_state
\t\t\t\tvar:{p}_audit_{index}_expected_state = {mechanism_stage(mechanism.mechanism_id)}
\t\t\t\tvar:{p}_audit_{index}_state = 1
\t\t\t\tvar:{p}_audit_{index}_consumed = 0
\t\t\t\tvar:{p}_receipt_active = 1
\t\t\t}}
\t\t\tset_variable = {{ name = {p}_audit_{index}_consumed value = 1 }}
\t\t\tset_variable = {{ name = {p}_audit_{index}_state value = 2 }}
\t\t\tchange_variable = {{ name = {p}_audit_revision add = 1 }}
\t\t\tif = {{ limit = {{ NOT = {{ var:{p}_route = 3 }} }} set_variable = {{ name = {p}_audit_{index}_consumer_value value = var:{p}_{mechanism.field} }} }}
\t\t\tif = {{ limit = {{ var:{p}_route = 1 }} set_variable = {{ name = {p}_audit_{index}_outcome value = 1 }} }}
\t\t\telse_if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_audit_{index}_outcome value = 2 }} }}
\t\t\telse = {{ set_variable = {{ name = {p}_audit_{index}_outcome value = 3 }} }}
\t\t\t{special_audit}
\t\t\t{typed_audit}
\t\t}}
\t\telse = {{ debug_log = "ZG361PP: stale {mechanism.mechanism_id:03d} audit ticket ignored" }}
\t}}
}}'''


def render_stage_deadline_event(domain: DomainSpec, state: int) -> str:
    row = case_vars(domain.key)
    dl = f"{PREFIX}_{domain.key}_stage_{state}_deadline"
    event_id = 4000 + (ord(domain.key) - ord("t")) * 10 + state
    return f'''zg361pp.{event_id} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tzg361_case_kernel_expire_deadline_effect = {{
\t\t\tOWNER_VAR = {row["owner"]}
\t\t\tSUBJECT_VAR = {row["subject"]}
\t\t\tCYCLE_VAR = {row["cycle"]}
\t\t\tCASE_VAR = {row["case"]}
\t\t\tSTATE_VAR = {row["state"]}
\t\t\tACTIVE_VAR = {row["active"]}
\t\t\tREVISION_VAR = {row["revision"]}
\t\t\tTIMELINE_VAR = {row["timeline"]}
\t\t\tFEEDBACK_VAR = {row["feedback"]}
\t\t\tDEADLINE_OWNER_VAR = {dl}_owner
\t\t\tDEADLINE_SUBJECT_VAR = {dl}_subject
\t\t\tDEADLINE_CYCLE_VAR = {dl}_cycle
\t\t\tDEADLINE_CASE_VAR = {dl}_case
\t\t\tDEADLINE_STATE_VAR = {dl}_state
\t\t\tDEADLINE_PENDING_VAR = {dl}_pending
\t\t\tDEADLINE_EXPIRED_VAR = {dl}_expired
\t\t}}
\t\tif = {{ limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }} zg361_pp_{domain.key}_timeout_stage_{state:02d}_effect = yes }}
\t}}
}}'''


def render_completion_event(domain: DomainSpec, event_id: int) -> str:
    terminal = ""
    if domain.key == "w":
        terminal = '''
\t\tfirst_valid = {
\t\t\ttriggered_desc = { trigger = { scope:zg361_pp_completion_subject = { var:zg361_pp_m189_skipped_no_relapse = 1 } } desc = zg361pp.terminal.graduated }
\t\t\ttriggered_desc = { trigger = { scope:zg361_pp_completion_subject = { var:zg361_pp_m189_terminal_code = 1 } } desc = zg361pp.terminal.second_pip }
\t\t\ttriggered_desc = { trigger = { scope:zg361_pp_completion_subject = { var:zg361_pp_m189_terminal_code = 2 } } desc = zg361pp.terminal.transfer }
\t\t\ttriggered_desc = { trigger = { scope:zg361_pp_completion_subject = { var:zg361_pp_m189_terminal_code = 3 } } desc = zg361pp.terminal.exit }
\t\t}'''
    return f'''zg361pp.{event_id} = {{
\ttype = character_event
\ttheme = vassal
\ttitle = zg361pp.{event_id}.t
\tdesc = {{
\t\tdesc = zg361pp.{event_id}.desc
\t\tfirst_valid = {{
\t\t\ttriggered_desc = {{ trigger = {{ scope:zg361_pp_completion_subject = {{ var:zg361_pp_{domain.key}_outcome = 1 }} }} desc = zg361pp.outcome.evidence }}
\t\t\ttriggered_desc = {{ trigger = {{ scope:zg361_pp_completion_subject = {{ var:zg361_pp_{domain.key}_outcome = -1 }} }} desc = zg361pp.outcome.political }}
\t\t\tdesc = zg361pp.outcome.mixed
\t\t}}
\t\t{terminal}
\t}}
\ttrigger = {{
\t\tis_ai = no
\t\tzg361_is_celestial_liege_trigger = yes
\t\tvar:zg361_pp_portfolio_queue_active = 1
\t\texists = scope:zg361_pp_completion_subject
\t}}
\toption = {{
\t\tname = zg361pp.{event_id}.a
\t\tset_variable = {{ name = zg361_pp_portfolio_queue_active value = 0 }}
\t}}
}}'''


def render_events() -> bytes:
    sections = ["namespace = zg361pp"]
    sections.extend(render_player_event(mechanism) for mechanism in MECHANISMS)
    sections.extend(
        render_subject_response_event(MECHANISM_BY_ID[mechanism_id])
        for mechanism_id in sorted(SUBJECT_RESPONSE_IDS)
    )
    for mechanism in MECHANISMS:
        for index, _ in enumerate(mechanism.deadlines, start=1):
            sections.append(render_audit_event(mechanism, index))
    for domain_index, domain in enumerate(DOMAINS, start=1):
        for state in range(1, len(domain.stages) + 1):
            sections.append(render_stage_deadline_event(domain, state))
        sections.append(render_completion_event(domain, 9000 + domain_index))
    return generated("\n\n".join(sections))


def escape_loc(value: str) -> str:
    return value.replace('"', '\\"')


def localization_rows(language: str) -> list[str]:
    chinese = language == "simp_chinese"
    rows = [f"l_{language}:"]
    if chinese:
        rows.extend(
            (
                ' zg361pp.grade.375:0 "本轮冻结绩效：3.75。别急，这一页还没开始夸你。"',
                ' zg361pp.grade.350:0 "本轮冻结绩效：3.5。翻译成人话：干得不少，坑也给你留着。"',
                ' zg361pp.grade.325:0 "本轮冻结绩效：3.25。PPT 叫改进空间，账本叫证据起点。"',
                ' zg361pp.outcome.evidence:0 "证据路线占优：流程没有变善良，只是这次终于留下了能对账的东西。"',
                ' zg361pp.outcome.political:0 "政治路线占优：业务很灵活，责任很稳定——稳定地落在经理名下。"',
                ' zg361pp.outcome.mixed:0 "路线打平：制度和人情各赢一半，只有会议时间全输了。"',
                ' zg361pp.terminal.second_pip:0 "终局：二次 PIP。恭喜，改进计划成功改进成了续费服务。"',
                ' zg361pp.terminal.graduated:0 "终局：观察期内没有同类复发。这回改进计划没有续费成功。"',
                ' zg361pp.terminal.transfer:0 "终局：真实转岗。不是把问题挪个群聊，而是连接收经理和空缺都写进了案卷。"',
                ' zg361pp.terminal.exit:0 "终局：退出。空缺、交接、加班和补员成本一个都没被‘组织优化’优化掉。"',
            )
        )
    else:
        rows.extend(
            (
                ' zg361pp.grade.375:0 "Frozen performance: 3.75. Relax; this page has not started praising you yet."',
                ' zg361pp.grade.350:0 "Frozen performance: 3.5. In plain speech: plenty delivered, with a few traps left for the review."',
                ' zg361pp.grade.325:0 "Frozen performance: 3.25. Slides call it growth space; the ledger calls it an evidence starting point."',
                ' zg361pp.outcome.evidence:0 "Evidence led: the process is not kinder, but it finally left something auditable."',
                ' zg361pp.outcome.political:0 "Politics led: the business stayed flexible and responsibility stayed reliably attached to the manager."',
                ' zg361pp.outcome.mixed:0 "The routes tied: policy and politics each won half; meeting time lost all of it."',
                ' zg361pp.terminal.second_pip:0 "Terminal: second PIP. The improvement plan has improved itself into a subscription."',
                ' zg361pp.terminal.graduated:0 "Terminal: no same-category relapse. The improvement plan did not renew its subscription this time."',
                ' zg361pp.terminal.transfer:0 "Terminal: real transfer. This moves a vacancy and receiving manager, not merely the problem into another chat."',
                ' zg361pp.terminal.exit:0 "Terminal: exit. Vacancy, handover, overtime and replacement costs all survived the optimization."',
            )
        )
    subject_response_rows = {
        151: (
            ("确认收到并同意。", "确认收到，但保留异议并提出申诉。")
            if chinese
            else ("Acknowledge receipt and agree.", "Acknowledge receipt, preserve my objection, and appeal.")
        ),
        166: (
            ("撤回我的晋升包。", "继续参评，由经理处理后续程序。")
            if chinese
            else ("Withdraw my promotion packet.", "Continue; let the manager handle the remaining procedure.")
        ),
        190: (
            ("同意附上我的最小披露陈述。", "拒绝扩散本人陈述，只保留程序回执。")
            if chinese
            else ("Attach my minimum-disclosure statement.", "Withhold my statement and retain only the procedural receipt.")
        ),
    }
    for mechanism_id, options in subject_response_rows.items():
        rows.extend(
            (
                f' zg361pp.{mechanism_id}.subject.a:0 "{escape_loc(options[0])}"',
                f' zg361pp.{mechanism_id}.subject.b:0 "{escape_loc(options[1])}"',
            )
        )
    for mechanism in MECHANISMS:
        title = mechanism.title_cn if chinese else mechanism.title_en
        desc = (
            f"{mechanism.consumer}。这一步写入的是可复核案卷，不会凭一句‘业务需要’穿越状态机。"
            if chinese
            else f"Consumer: {mechanism.consumer}. This writes a reviewable case receipt; 'business needs' cannot skip the state machine."
        )
        routes = (
            (mechanism.a_cn, mechanism.b_cn, mechanism.c_cn)
            if chinese
            else (mechanism.a_en, mechanism.b_en, mechanism.c_en)
        )
        rows.extend(
            (
                f' zg361pp.{mechanism.mechanism_id}.t:0 "{escape_loc(title)}"',
                f' zg361pp.{mechanism.mechanism_id}.desc:0 "{escape_loc(desc)}"',
                f' zg361pp.{mechanism.mechanism_id}.a:0 "{escape_loc(routes[0])}"',
                f' zg361pp.{mechanism.mechanism_id}.b:0 "{escape_loc(routes[1])}"',
                f' zg361pp.{mechanism.mechanism_id}.c:0 "{escape_loc(routes[2])}"',
            )
        )
    for domain_index, domain in enumerate(DOMAINS, start=1):
        event_id = 9000 + domain_index
        title = f"三六一案卷已结：{domain.title_cn}" if chinese else f"361 Case Closed: {domain.title_en}"
        desc = (
            "本域全部回执、资源和期限已经收口。你可以不同意制度，但账本现在至少敢把名字写全。"
            if chinese
            else "All receipts, resources and deadlines in this domain have closed. You may still hate the policy; at least its ledger now signs its name."
        )
        option = "归档。下一轮继续互相成就。" if chinese else "File it. Continue mutually enabling each other next cycle."
        rows.extend(
            (
                f' zg361pp.{event_id}.t:0 "{escape_loc(title)}"',
                f' zg361pp.{event_id}.desc:0 "{escape_loc(desc)}"',
                f' zg361pp.{event_id}.a:0 "{escape_loc(option)}"',
            )
        )
    return rows


def render_localization(language: str) -> bytes:
    source = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


LANGUAGES = (
    "english",
    "simp_chinese",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)


def outputs() -> dict[Path, bytes]:
    validate_specs()
    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    rendered = {
        MOD_ROOT / "events" / "zg361_feedback_promotion_pip_runtime_events.txt": render_events(),
    }
    rendered.update(
        {
            effects_dir / filename: payload
            for filename, payload in render_effect_parts().items()
        }
    )
    for language in LANGUAGES:
        rendered[
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_feedback_promotion_pip_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    legacy_effect_path = (
        MOD_ROOT / "common" / "scripted_effects" / LEGACY_EFFECT_FILENAME
    )
    if args.check:
        if stale or legacy_effect_path.exists():
            print("RED: stale feedback/promotion/PIP generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            if legacy_effect_path.exists():
                print(f"{legacy_effect_path.relative_to(MOD_ROOT)} (legacy monolith)")
            return 1
        print("GREEN: feedback/promotion/PIP generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    if legacy_effect_path.exists():
        legacy_effect_path.unlink()
    print(f"GREEN: generated {len(rendered)} feedback/promotion/PIP runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
