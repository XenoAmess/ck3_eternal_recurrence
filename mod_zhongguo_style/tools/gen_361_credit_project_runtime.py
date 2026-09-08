#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the E/I/J/R credit and project CK3 static-ready runtime.

The generated package owns only new effects, events and localization files.
It consumes the committed shared case-kernel ABI, but never edits the kernel,
B1/B2, scoreboard, on_actions, interactions or any other central dispatcher.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from zg361_localization_style import normalize_localization_rows


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_credit_project_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
DEFER_ROUTE_EN = "Close this item and record policy debt."
DEFER_ROUTE_CN = "关闭本项，登记制度债。"
DEFER_TOOLTIP_EN = "No business action is taken. One next-cycle policy debt is recorded, and this item will not be proposed again automatically."
DEFER_TOOLTIP_CN = "不执行业务动作；登记一笔下周期制度债。本项不会自动重提。"
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
EFFECTS_DIR = Path("common") / "scripted_effects"
LEGACY_EFFECT_FILENAME = "zg361_credit_project_runtime_effects.txt"
EVENTS_DIR = Path("events")
LEGACY_EVENT_FILENAME = "zg361_credit_project_runtime_events.txt"
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# Any future hard-limit exception must carry both an engineering reason and a
# concrete CK3 live artifact. The current B8 layout has no exception.
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}


@dataclass(frozen=True)
class Mechanism:
    mid: int
    domain: str
    state: int
    field: str
    title_en: str
    title_cn: str
    desc_en: str
    desc_cn: str
    routes_en: tuple[str, str, str]
    routes_cn: tuple[str, str, str]


def m(
    mid: int,
    domain: str,
    state: int,
    field: str,
    title_en: str,
    title_cn: str,
    desc_en: str,
    desc_cn: str,
    a_en: str,
    b_en: str,
    c_en: str,
    a_cn: str,
    b_cn: str,
    c_cn: str,
) -> Mechanism:
    return Mechanism(
        mid,
        domain,
        state,
        field,
        title_en,
        title_cn,
        desc_en,
        desc_cn,
        # The acceptance/runtime program is authoritative: route C is the
        # mechanism-specific policy.defer control route, never a third
        # business payload.  The legacy per-item C copy remains accepted by
        # this helper only so the data table stays reviewable while generated
        # player copy and runtime semantics use the canonical defer wording.
        (a_en, b_en, DEFER_ROUTE_EN),
        (a_cn, b_cn, DEFER_ROUTE_CN),
    )


MECHANISMS = (
    m(26, "e", 1, "effort_ledger", "Work and Visibility Are Different Ledgers", "实绩与可见度分账",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. The capacity ledger shows delivery, reporting and relationship work drawing from one balance. Only delivery has produced hard output so far.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。容量账显示交付、汇报与关系事务正在争用同一份余额；目前只有交付工时产出了实际成果。",
      "Protect delivery and keep reporting lean.", "Balance delivery with a fuller account.", "Spend heavily on visibility and record the displaced output.",
      "分配二十小时交付、两小时汇报及一小时关系事务；共占二十三小时容量。", "分配十五小时交付、四小时汇报及三小时关系事务；共占二十二小时容量。", "重押可见度，并如实记录被挤掉的产出。"),
    m(27, "e", 2, "signed_contribution", "Allocate One Hundred Percent of the Credit", "把百分之百贡献分配清楚",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. The subject, direct manager and cross-department contributor all claim the same result. The file has no complete ten-thousand-basis-point allocation, and the frozen facts do not uniquely determine one ratio.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。受评者、直属上司与跨部门贡献者都对同一成果提出了主张；案卷尚无合计一万基点的完整归属表，冻结事实也不足以唯一推出一种比例。",
      "Provisionally record seventy percent for the subject, twenty for the manager and ten cross-department.", "Provisionally record fifty percent for the subject, thirty for the manager and twenty cross-department.", "Defer the allocation pending more facts.",
      "暂按受评者七成、直属上司两成、跨部门一成登记功劳。", "暂按受评者五成、直属上司三成、跨部门两成登记功劳。", "待补事实后再分配。"),
    m(28, "e", 3, "credit_claim", "Credit Claim and Audit Reversal", "抢功申诉与审计回拨",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. The direct manager has requested five hundred basis points from the frozen allocation, but this card contains no finding that proves or disproves the request. Any accepted transfer must leave the total unchanged.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。直属上司要求从冻结归属表取得五百基点，但本案没有足以支持或驳回该要求的审证结论；任何获准转移都不能改变总量。",
      "Approve the requested five-hundred-basis-point transfer from the subject to the manager.", "Reject and reverse the proposed five-hundred-point transfer, keeping the original shares.", "Defer the claim pending evidence.",
      "批准所请转移：从受评者向直属上司转移五百基点。", "驳回并撤销拟议的五百基点转移，维持原份额。", "待补证据后再处理主张。"),
    m(29, "e", 4, "metric_audit", "Metric Packaging and Audit", "指标包装与审计",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. The headline metric has jumped, but the review has not established its source or later cost. This choice records a provisional accounting convention, not a proven factual finding.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。账面指标突然上升，复核尚未查清收益来源与后续成本；本次选择只登记暂定核算口径，不冒充已经查明的事实。",
      "Provisionally book ten short-term gain and no delayed cost as improvement.", "Provisionally book twenty short-term gain and eight delayed cost as metric gaming.", "Defer classification pending source and cost evidence.",
      "暂按真实改善口径登记：短期收益十，延迟成本为零。", "暂按指标博弈口径登记：短期收益二十、延迟成本八。", "待补来源与成本证据后再定性。"),
    m(30, "e", 1, "resource_race", "One Project Wins the Capacity Race", "资源赛马只产生一个赢家",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. A forty-hour subject-led proposal and a sixty-hour cross-functional proposal are competing for one project slot; no hours are reserved yet.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。一份由当事人主导的四十小时提案与一份六十小时跨部门提案正在争夺唯一项目席位；容量账尚未预留工时。",
      "Fund the forty-hour subject-led project.", "Fund the sixty-hour cross-functional project.", "Defer both proposals without reserving capacity.",
      "批准当事人主导的四十小时项目。", "批准六十小时跨部门项目。", "两案暂缓，不预留容量。"),
    m(31, "e", 2, "sponsor_credit", "Sponsor Credit Has a Cap and Expiry", "恩主信用有上限也会到期",
      "Subject: [zg361_cp_e_subject.GetShortUIName]. Decision owner: [zg361_cp_e_owner.GetShortUIName]. A sponsor has offered an introduction, but the available sponsor balance is finite and expires. The offer contains no new delivery evidence.",
      "当事人：[zg361_cp_e_subject.GetShortUIName]；裁决者：[zg361_cp_e_owner.GetShortUIName]。恩主愿意出面引荐，但可用信用有限且会到期；这份人情没有附带任何新的交付证据。",
      "Grant twenty sponsor credit and five visibility without spending the balance.", "Spend ten sponsor credit to gain ten visibility.", "Decline sponsor credit and rely on evidence.",
      "接受二十点恩主信用但暂不动用；增加五点可见度，不增加交付产出。", "接受三十点恩主信用并动用十点；增加十点可见度，不增加交付产出。", "不用恩主信用，只靠证据。"),
    m(54, "i", 1, "report_build", "Reporting Consumes Delivery Capacity", "汇报会挤占交付容量",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. The report packet has not been built, and every hour spent on it will come out of the remaining project capacity without adding delivery output.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。汇报材料尚未制作；投入其中的每个小时都会从项目剩余容量中扣除，却不会增加交付产出。",
      "Build the frozen short fact sheet and spend one hour.", "Build the long narrative and spend four hours.", "Build an exception-only packet.",
      "制作冻结的短事实表，支付一小时。", "制作长叙事，支付四小时。", "只制作异常事项材料。"),
    m(55, "i", 4, "attention_read", "Routing Is Not Reading", "送达不等于阅读",
      "[zg361_cp_i_subject.GetShortUIName]'s report has reached direct manager [zg361_cp_i_owner.GetShortUIName], but neither of the two deep-read slots has been spent. Delivery alone therefore proves no one has read it.",
      "直属上司[zg361_cp_i_owner.GetShortUIName]已经收到[zg361_cp_i_subject.GetShortUIName]的材料，两个深读席位却都尚未使用；仅有送达记录，不能证明任何人真正读过。",
      "Spend one slot on the direct manager.", "Spend both slots on direct and skip-level readers.", "Route it without claiming that anyone read it.",
      "消耗一个阅读席位，让直属上司深读；增加五点可见度。", "消耗两个阅读席位，让直属与越级上司各深读一次；增加十点可见度。", "只完成路由，不声称有人阅读。"),
    m(56, "i", 2, "forwarded_credit", "Forward Without Quietly Taking Credit", "逐级上报不能悄悄截功",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. The frozen contribution book is ready to be forwarded, and a manager has requested five hundred basis points. No supporting finding is frozen here; either route must preserve the total.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。冻结贡献底稿即将上送，一名上司要求取得五百基点；本案没有冻结支持该要求的审证结论，无论如何登记都必须保持总量不变。",
      "Forward the frozen shares unchanged.", "Record the requested five-hundred-point transfer to the manager without claiming an evidence finding.", "Defer the requested change pending evidence.",
      "原样转发冻结份额。", "登记上司所请的五百基点转移，但不声称已经审证。", "待补证据后再处理改份额请求。"),
    m(57, "i", 2, "version_signature", "Freeze the Report Version", "冻结汇报版本",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. The attribution already totals ten thousand basis points. This card contains no visible content difference between archive numbers one and two; the choice only freezes the current table under one of those version numbers.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。当前归属表已经合计一万基点；本案没有显示版本一与版本二之间的内容差异，本次选择只决定用哪个版本号冻结同一张表。",
      "Freeze the current unchanged attribution table as version one.", "Freeze the current unchanged attribution table as version two.", "Defer version numbering pending a distinct revision.",
      "将当前未改动的归属表冻结为版本一。", "将当前未改动的归属表冻结为版本二。", "等出现独立修订后再编号。"),
    m(58, "i", 3, "report_route", "Freeze Material Before Routing", "先冻结版本，再路由",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. The material is frozen and awaiting dispatch. A recipient record will show where it went, but no attention slot is consumed until someone reads it.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。材料已经冻结并等待送出；收件记录只能证明去向，真正阅读之前不会消耗注意力席位。",
      "Route to the direct manager only.", "Route to direct and skip-level managers.", "Route with a cross-department evidence copy.",
      "只送直属上司；暂不计入已阅读。", "同时送直属与越级上司；暂不计入已阅读。", "附跨部门证据副本后路由。"),
    m(59, "i", 3, "risk_timing", "Bad News Has a Timestamp", "坏消息必须有时间戳",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. The risk has entered its reporting window. Every delay now leaves more loss unresolved and weakens the integrity receipt attached to the file.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。风险已经进入报告时限。此后每拖延一步，未化解的损失都会增加，案卷上的诚信回执也会变差。",
      "Report early and halve the remaining loss.", "Report late and retain the full loss.", "Hide it and double the loss.",
      "立即报告：剩余损失降至五，诚信记录增加一点。", "延迟报告：保留九点损失，诚信记录不增加。", "继续隐瞒，让损失翻倍。"),
    m(60, "i", 4, "idea_arbitration", "The Frozen Version Owns the Idea", "创意归属服从冻结版本",
      "[zg361_cp_i_subject.GetShortUIName] and cross-department contributor [zg361_cp_i_cross_reviewer.GetShortUIName] claim the same idea. The frozen author record and cross-department provenance disagree on how much each contributed.",
      "争议双方[zg361_cp_i_subject.GetShortUIName]与跨部门贡献者[zg361_cp_i_cross_reviewer.GetShortUIName]同时认领同一项创意，冻结作者记录与跨部门来源对两人的贡献给出了冲突线索。",
      "Uphold the original author and sustain the theft allegation against the cross-department claimant.", "Assign sole authorship to the cross-department contributor and reject the theft allegation against them.", "Reject the theft allegation for lack of matching provenance.",
      "支持原作者，并认定跨部门主张者构成窃取。", "将唯一作者认定为跨部门贡献者，并驳回对其窃取指控。", "来源不匹配，驳回窃取指控。"),
    m(61, "i", 1, "report_policy", "Choose the Reporting Regime First", "先定汇报制度",
      "Subject: [zg361_cp_i_subject.GetShortUIName]. Decision owner: [zg361_cp_i_owner.GetShortUIName]. No common reporting rule exists. Teams now submit packets of very different length, making their drain on project capacity unpredictable.",
      "当事人：[zg361_cp_i_subject.GetShortUIName]；裁决者：[zg361_cp_i_owner.GetShortUIName]。眼下没有统一汇报规则，各团队送来的材料长短悬殊，对项目容量的消耗也因此无法预估。",
      "Use short factual reports.", "Require long narrative reports.", "Report exceptions only.",
      "采用短事实汇报制度；每份材料占用一小时容量。", "采用长叙事汇报制度；每份材料占用四小时容量。", "只汇报异常。"),
    m(62, "j", 2, "matrix_conflict", "Two Lines, One Recorded Choice", "两条汇报线，只能留下一个选择",
      "[zg361_cp_j_owner.GetShortUIName] and [zg361_cp_j_cross_reviewer.GetShortUIName] have issued incompatible priorities to [zg361_cp_j_subject.GetShortUIName]. Following both would leave two contradictory commitments and no single accountable instruction.",
      "对[zg361_cp_j_subject.GetShortUIName]发令的两名上司[zg361_cp_j_owner.GetShortUIName]与[zg361_cp_j_cross_reviewer.GetShortUIName]下达了互不相容的目标；若同时照办，案卷只会留下两项矛盾承诺，没有唯一责任指令。",
      "Follow the heavier solid-line weight.", "Use joint arbitration.", "Promise both and record integrity debt.",
      "服从权重更高的实线。", "提交联合仲裁。", "两边都答应，并记录诚信债。"),
    m(63, "j", 1, "matrix_weights", "Lock Solid and Dotted Weights", "锁定实线与虚线权重",
      "[zg361_cp_j_owner.GetShortUIName] and [zg361_cp_j_cross_reviewer.GetShortUIName] are competing for assessment authority over [zg361_cp_j_subject.GetShortUIName] this cycle, while the solid- and dotted-line weights do not yet close to one hundred.",
      "两名上司[zg361_cp_j_owner.GetShortUIName]与[zg361_cp_j_cross_reviewer.GetShortUIName]在本周期争用对[zg361_cp_j_subject.GetShortUIName]的考核权，而案卷中的实线与虚线权重还没有合计到一百。",
      "Use seventy-thirty toward the solid line.", "Give solid and dotted lines equal weight.", "Use forty-sixty toward the dotted line.",
      "按实线七成、虚线三成分配考核权。", "按实线与虚线各五成分配考核权。", "按实线四成、虚线六成分配考核权。"),
    m(64, "j", 3, "manager_handoff", "A Manager Handoff Needs Both Owners Named", "换上司必须列明新旧责任人",
      "[zg361_cp_j_subject.GetShortUIName]'s role handoff is pending. Future responsibility may move from [zg361_cp_j_owner.GetShortUIName] to [zg361_cp_j_successor_manager.GetShortUIName], while historical cases remain with [zg361_cp_j_owner.GetShortUIName]; the file has not yet named both managers.",
      "官员[zg361_cp_j_subject.GetShortUIName]的职司交接已经提上日程；未来责任可以从[zg361_cp_j_owner.GetShortUIName]转给继任者[zg361_cp_j_successor_manager.GetShortUIName]，历史案卷仍归[zg361_cp_j_owner.GetShortUIName]，案卷尚未同时列明新旧上司。",
      "Name both managers and finalize the ordered handoff.", "Record only the old manager and leave the handoff pending.", "Decline the handoff and keep the current manager.",
      "列明新旧上司并完成交接；未来责任转给继任者，旧案仍归原上司。", "只记录旧上司，交接保持待定；未来责任暂不转移。", "拒绝交接，保留现任上司。"),
    m(65, "j", 2, "parachute_staffing", "An Airborne Manager Brings a Staff Pack", "空降主管与旧部包",
      "Incoming manager [zg361_cp_j_owner.GetShortUIName] wants to fill [zg361_cp_j_subject.GetShortUIName]'s ten-person team with former staff. Every imported seat displaces retained institutional memory, and the favoritism threshold is close.",
      "新任主管[zg361_cp_j_owner.GetShortUIName]准备把旧部带进[zg361_cp_j_subject.GetShortUIName]所在的十人团队；每占一个席位都会挤掉组织记忆，任人唯亲的审计阈值也已逼近。",
      "Import two of ten staff.", "Import three and trigger the audit threshold.", "Import six and expose severe memory loss.",
      "十人中带入两名旧部，保留八名原团队成员。", "带入三名旧部，保留七名原团队成员并触发任人唯亲审计。", "带入六人，暴露严重记忆流失。"),
    m(66, "j", 4, "strategic_cancel", "Business Cancellation Is Not Personal Failure", "业务取消不等于个人失败",
      "[zg361_cp_j_owner.GetShortUIName]'s strategic review supports cancelling [zg361_cp_j_subject.GetShortUIName]'s project, but the file still mixes unspent capacity with independently verified personal contribution.",
      "上司[zg361_cp_j_owner.GetShortUIName]主持的战略复核已经支持取消[zg361_cp_j_subject.GetShortUIName]负责的项目，案卷却仍把未花容量与已独立验证的个人贡献混在一起。",
      "Cancel now and preserve verified credit.", "Approve a later cancellation without rewriting credit.", "Keep the project active and record the strategic review.",
      "立即取消，释放全部剩余容量并保留已验证功劳。", "登记稍后取消；暂不释放容量，也不改写个人功劳。", "项目继续，但留下战略复核记录。"),
    m(67, "j", 4, "duplicate_role", "Two Incumbents Need One Terminal Owner", "一岗两人最终只能有一个 owner",
      "[zg361_cp_j_subject.GetShortUIName] and [zg361_cp_j_cross_reviewer.GetShortUIName] are both recorded against the same office. [zg361_cp_j_owner.GetShortUIName] cannot close the file until exactly one of them remains accountable for it.",
      "同一职司名下同时挂着[zg361_cp_j_subject.GetShortUIName]与[zg361_cp_j_cross_reviewer.GetShortUIName]两名现任者。[zg361_cp_j_owner.GetShortUIName]只有在其中一人成为唯一责任人后才能结清案卷。",
      "Retain the assessed official.", "Retain the cross-department incumbent.", "Run a bounded transition and name one terminal owner.",
      "保留受评官员。", "保留跨部门现任者。", "完成有界过渡，并指定唯一终态 owner。"),
    m(68, "j", 4, "portable_history", "History Travels; Authorship Does Not", "履历可携带，历史作者不改写",
      "Transferred official [zg361_cp_j_subject.GetShortUIName] arrives under receiving manager [zg361_cp_j_active_manager.GetShortUIName] with prior ratings, while old cases remain with [zg361_cp_j_historical_owner.GetShortUIName]. The receiving team must choose a protected period and whether to carry a PIP if one is still open; none of that history may consume current quota or re-own old cases.",
      "调入者[zg361_cp_j_subject.GetShortUIName]带着旧评级来到[zg361_cp_j_active_manager.GetShortUIName]麾下，旧案仍由[zg361_cp_j_historical_owner.GetShortUIName]负责。接收团队须决定保护期，以及确有未结绩效改进计划时是否一并携带；这些历史都不能占用本期名额或改写旧案责任人。",
      "Keep one protected cycle; carry the PIP only if one remains open, and use no current quota.", "Carry ratings without the PIP and use no current quota.", "Keep history separate for local re-proof.",
      "保留一个保护周期；仅在确有未结绩效改进计划时一并携带，不占本期名额。", "携带一个保护周期及旧评级，不携带绩效改进计划；不占本期名额。", "历史独立保存，等待本地重新证明。"),
    m(129, "r", 2, "promotion_queue", "Promotion Is a Queue With Real Slots", "晋升是有真实槽位的队列",
      "[zg361_cp_r_owner.GetShortUIName]'s promotion queue already has an eligibility order, but this cycle has only one award slot. [zg361_cp_r_subject.GetShortUIName] has not yet been placed against that opening.",
      "晋升案卷由[zg361_cp_r_owner.GetShortUIName]掌管，队列已经排定资格先后，本周期却只有一个授予槽；[zg361_cp_r_subject.GetShortUIName]尚未与这个空缺完成匹配。",
      "Queue the subject for the next opening.", "Queue and allocate the one available slot.", "Defer with a signed eligibility expiry.",
      "把受评者排入下一空缺；保留两周期资格，但本期不授予。", "把受评者入队并占用唯一槽位；本期立即授予，资格保留两周期。", "签署资格到期日后延期。"),
    m(130, "r", 3, "talent_transfer", "Do Not Dump a Hidden PIP", "不能把隐藏 PIP 倾倒给别组",
      "[zg361_cp_r_subject.GetShortUIName] seeks a transfer from [zg361_cp_r_owner.GetShortUIName] to [zg361_cp_r_cross_reviewer.GetShortUIName] while carrying an open PIP and a claim of role mismatch. The file lacks a complete chain from disclosure and role evidence to trial outcome and source-manager accountability.",
      "调动申请人[zg361_cp_r_subject.GetShortUIName]拟从[zg361_cp_r_owner.GetShortUIName]麾下转往[zg361_cp_r_cross_reviewer.GetShortUIName]处，同时带着未结绩效改进计划与错岗主张；披露、岗位证据、试用结果和原上司责任尚未连成完整链条。",
      "Disclose the PIP and run a supported trial.", "Rescue a proven wrong-role placement.", "Hide the PIP; failed trial returns liability to the source manager.",
      "披露 PIP，并进行有支持的试用。", "以错岗证据完成岗位救援。", "隐瞒 PIP；试用失败后责任回到原上司。"),
    m(131, "r", 1, "project_track", "Exploration and Commitment Are Different Tracks", "探索项目与承诺项目分轨",
      "[zg361_cp_r_subject.GetShortUIName]'s project results are still unknown, and [zg361_cp_r_owner.GetShortUIName]'s file has no registered track or matching success rule. Exploration and firm commitment would be judged differently.",
      "官员[zg361_cp_r_subject.GetShortUIName]所涉项目尚无结果，[zg361_cp_r_owner.GetShortUIName]手中的案卷也没有登记类型和对应成功口径；探索任务与承诺任务本来就不该用同一把尺。",
      "Register an exploration track.", "Register a commitment track.", "Register a bounded hybrid under commitment rules.",
      "登记为探索型项目。", "登记为承诺型项目。", "按承诺规则登记有界混合项目。"),
    m(132, "r", 4, "stop_loss", "A Timely Stop Can Earn Credit", "及时止损也可以算功",
      "[zg361_cp_r_subject.GetShortUIName]'s project is still consuming capacity while evidence for stopping accumulates. [zg361_cp_r_owner.GetShortUIName]'s file does not yet separate the business outcome from the timeliness of the individual judgment.",
      "官员[zg361_cp_r_subject.GetShortUIName]负责的项目仍在消耗容量，支持止损的证据却不断累积；[zg361_cp_r_owner.GetShortUIName]手中的案卷尚未把业务结果与个人判断是否及时分开。",
      "Stop on strong evidence and grant timely-stop credit.", "Stop late and record named accountability.", "Stop without credit when the evidence is insufficient.",
      "证据充分时止损，并给予及时止损功劳。", "迟到止损，并记录具名责任。", "证据不足也先止损，但不授予止损功劳。"),
    m(133, "r", 5, "postmortem", "Learning and Liability Need Separate Tracks", "复盘学习与具名责任分轨",
      "[zg361_cp_r_owner.GetShortUIName]'s postmortem of [zg361_cp_r_subject.GetShortUIName]'s project contains both a system defect and a possible named violation. Treating them as one finding would either punish everyone or erase proven accountability.",
      "上司[zg361_cp_r_owner.GetShortUIName]对[zg361_cp_r_subject.GetShortUIName]所涉项目的复盘同时发现系统缺陷与一项可能成立的具名违规；混成一个结论，要么造成连坐，要么抹掉已有责任证据。",
      "Record learning with no proven violation.", "Record system learning and one named violation.", "Record a control repair and manager liability.",
      "记录学习，不认定个人违规。", "记录系统学习及一项具名违规。", "记录控制修复与上司责任。"),
    m(134, "r", 2, "shared_metric_owner", "A Shared Metric Still Has One Owner", "共享指标仍然只有一个 owner",
      "The file names [zg361_cp_r_subject.GetShortUIName], direct manager [zg361_cp_r_owner.GetShortUIName], and cross-department lead [zg361_cp_r_cross_reviewer.GetShortUIName] as contributors, but final settlement authority can be assigned only once. Both the subject and direct manager have a documented claim.",
      "案卷把[zg361_cp_r_subject.GetShortUIName]、直属上司[zg361_cp_r_owner.GetShortUIName]与跨部门负责人[zg361_cp_r_cross_reviewer.GetShortUIName]列为贡献者，但最终结算责任只能分配一次；受评者与直属上司都留有可核的责任主张。",
      "Assign the subject as sole owner.", "Assign the direct manager as sole owner.", "Assign the cross-department lead as sole owner.",
      "指定受评者为唯一 owner。", "指定直属上司为唯一 owner。", "指定跨部门负责人为唯一 owner。"),
)


DOMAIN_ORDER = {
    "e": (30, 26, 27, 31, 28, 29),
    "i": (61, 54, 56, 57, 58, 59, 55, 60),
    "j": (63, 62, 65, 64, 66, 67, 68),
    "r": (131, 129, 134, 130, 132, 133),
}
STAGE_LAST = {
    "e": {26: 1, 31: 2, 28: 3, 29: 4},
    "i": {54: 1, 57: 2, 59: 3, 60: 4},
    "j": {63: 1, 65: 2, 64: 3, 68: 4},
    "r": {131: 1, 134: 2, 130: 3, 132: 4, 133: 5},
}
NEXT_DOMAIN = {"e": "i", "i": "j", "j": "r", "r": None}
QUEUE_EVENTS = {"e": 9001, "i": 9002, "j": 9003}
BATCH_MODE_EVENT = 9050
BATCH_DISPATCH_EVENT_BASE = 9200
# These cards contain no payment, response, delay, personnel-disposition or
# settlement decision. They may execute the player's frozen portfolio mode
# without opening another window. Every other card keeps its original event.
BATCHABLE_IDS = frozenset({31, 56, 57, 58, 61, 62, 63, 65, 68, 131, 134})
RETAINED_POPUP_IDS = frozenset({26, 27, 28, 29, 30, 54, 55, 59, 60, 64, 66, 67, 129, 130, 132, 133})
EXPECTED_IDS = (
    set(range(26, 32))
    | set(range(54, 62))
    | set(range(62, 69))
    | set(range(129, 135))
)


def effect_filename_for(spec: Mechanism) -> str:
    """Return the stable, purpose-named shard owned by one mechanism."""

    return f"zg361_credit_project_m{spec.mid:03d}_{spec.field}_effects.txt"


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.rstrip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.rstrip() + "\n").encode("utf-8")


def indent(text: str, tabs: int = 1) -> str:
    prefix = "\t" * tabs
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def by_id() -> dict[int, Mechanism]:
    return {spec.mid: spec for spec in MECHANISMS}


def validate_specs() -> None:
    specs = by_id()
    if set(specs) != EXPECTED_IDS or len(specs) != 27:
        raise ValueError("credit/project runtime must cover exactly 27 requested IDs")
    if {mid for order in DOMAIN_ORDER.values() for mid in order} != EXPECTED_IDS:
        raise ValueError("domain order must contain every requested ID exactly once")
    if len({spec.field for spec in MECHANISMS}) != 27:
        raise ValueError("every mechanism needs a unique semantic field")
    if BATCHABLE_IDS & RETAINED_POPUP_IDS:
        raise ValueError("batchable and retained-popup credit/project IDs overlap")
    if BATCHABLE_IDS | RETAINED_POPUP_IDS != EXPECTED_IDS:
        raise ValueError("batchable and retained-popup IDs must partition the package")
    for domain, order in DOMAIN_ORDER.items():
        states = [specs[mid].state for mid in order]
        if states != sorted(states):
            raise ValueError(f"domain {domain} execution order is not monotonic")
        # Order, not numeric magnitude, determines the final operation in a stage.
        expected_barriers = {
            [mid for mid in order if specs[mid].state == state][-1]: state
            for state in set(states)
        }
        if STAGE_LAST[domain] != expected_barriers:
            raise ValueError(f"domain {domain} stage barriers drifted")


def tuple_guard(spec: Mechanism) -> str:
    d = spec.domain
    return f"""zg361_case_kernel_full_guard_trigger = {{
\tOWNER_VAR = zg361_case_{d}_owner
\tSUBJECT_VAR = zg361_case_{d}_subject
\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\tCASE_VAR = zg361_case_{d}_case_serial
\tSTATE_VAR = zg361_case_{d}_state
\tACTIVE_VAR = zg361_case_{d}_active
\tEXPECTED_OWNER = $TICKET_OWNER$
\tEXPECTED_SUBJECT = $TICKET_SUBJECT$
\tEXPECTED_CYCLE = $TICKET_CYCLE$
\tEXPECTED_CASE = $TICKET_CASE$
\tEXPECTED_STATE = {spec.state}
}}"""


def receipt_guard(spec: Mechanism, choice: int) -> str:
    mid = spec.mid
    return f"""zg361_case_kernel_receipt_is_current_trigger = {{
\tRECEIPT_OWNER_VAR = zg361_cp_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = zg361_cp_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = zg361_cp_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = zg361_cp_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = zg361_cp_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = zg361_cp_m{mid}_receipt_choice
\tEXPECTED_OWNER = $TICKET_OWNER$
\tEXPECTED_SUBJECT = $TICKET_SUBJECT$
\tEXPECTED_CYCLE = $TICKET_CYCLE$
\tEXPECTED_CASE = $TICKET_CASE$
\tEXPECTED_STATE = {spec.state}
\tEXPECTED_CHOICE = {choice}
}}"""


def any_receipt(spec: Mechanism) -> str:
    return "OR = {\n" + "\n".join(indent(receipt_guard(spec, choice)) for choice in (1, 2, 3)) + "\n}"


def stage_barrier(spec: Mechanism) -> str:
    return "\n".join(
        any_receipt(item)
        for item in MECHANISMS
        if item.domain == spec.domain and item.state == spec.state
    )


def resource_checks(spec: Mechanism, choice: int) -> list[str]:
    d, mid = spec.domain, spec.mid
    checks = [
        f"has_variable = zg361_cp_{d}_operation_total",
        f"has_variable = zg361_cp_{d}_operation_used",
        f"var:zg361_cp_{d}_operation_used < var:zg361_cp_{d}_operation_total",
    ]
    # C is a pure control-plane defer.  It must remain available when an A/B
    # business prerequisite or finite resource is absent, and it may not read
    # a business object merely to manufacture a debt receipt.
    if choice == 3:
        return checks
    if mid != 30:
        checks += [
            "has_variable = zg361_cp_project_object_manager",
            "has_variable = zg361_cp_project_object_subject",
            "has_variable = zg361_cp_project_object_cycle",
            "has_variable = zg361_cp_project_object_origin_case",
            "has_variable = zg361_cp_project_object_version",
            "has_variable = zg361_cp_project_object_deadline_cycle",
            "has_variable = zg361_cp_project_object_status",
            "var:zg361_cp_project_object_manager = $TICKET_OWNER$",
            "var:zg361_cp_project_object_subject = $TICKET_SUBJECT$",
            "var:zg361_cp_project_object_cycle = $TICKET_CYCLE$",
        ]
    if mid in (56, 57, 58, 59, 55, 60):
        checks += [
            "has_variable = zg361_cp_report_object_owner",
            "has_variable = zg361_cp_report_object_subject",
            "has_variable = zg361_cp_report_object_cycle",
            "has_variable = zg361_cp_report_object_case",
            "has_variable = zg361_cp_report_object_version",
            "has_variable = zg361_cp_report_project_origin_case",
            "var:zg361_cp_report_object_owner = $TICKET_OWNER$",
            "var:zg361_cp_report_object_subject = $TICKET_SUBJECT$",
            "var:zg361_cp_report_object_cycle = $TICKET_CYCLE$",
            "var:zg361_cp_report_object_case = $TICKET_CASE$",
            "var:zg361_cp_report_project_origin_case = var:zg361_cp_project_object_origin_case",
        ]
    if mid == 30:
        amount = (40, 60, 80)[choice - 1]
        checks += [
            "has_variable = zg361_cp_project_slot_used",
            "var:zg361_cp_project_slot_used = 0",
            "has_variable = zg361_cp_capacity_available",
            f"var:zg361_cp_capacity_available >= {amount}",
        ]
    if mid == 26:
        amount = (23, 22, 21)[choice - 1]
        checks += ["has_variable = zg361_cp_capacity_remaining", f"var:zg361_cp_capacity_remaining >= {amount}"]
    if mid == 27:
        checks += ["has_variable = zg361_cp_cross_reviewer_valid", "var:zg361_cp_cross_reviewer_valid = 1"]
    if mid == 28:
        checks += ["has_variable = zg361_cp_baseline_share_total", "var:zg361_cp_baseline_share_total = 10000"]
    if mid == 54:
        hours = (1, 4, 1)[choice - 1]
        checks += [
            "has_variable = zg361_cp_report_policy",
            f"var:zg361_cp_report_policy = {choice}",
            "has_variable = zg361_cp_report_policy_hours",
            f"var:zg361_cp_report_policy_hours = {hours}",
            "has_variable = zg361_cp_capacity_remaining",
            f"var:zg361_cp_capacity_remaining >= {hours}",
        ]
    if mid == 56:
        checks += ["has_variable = zg361_cp_claimed_share_total", "var:zg361_cp_claimed_share_total = 10000"]
    if mid in (57, 58, 60):
        if mid == 57:
            checks += ["has_variable = zg361_cp_report_share_total", "var:zg361_cp_report_share_total = 10000"]
        else:
            checks += ["has_variable = zg361_cp_report_version_frozen", "var:zg361_cp_report_version_frozen = 1"]
    if mid == 55 and choice in (1, 2):
        needed = choice
        checks += [
            "has_variable = zg361_cp_report_routed",
            "var:zg361_cp_report_routed = 1",
            "has_variable = zg361_cp_attention_free",
            f"var:zg361_cp_attention_free >= {needed}",
        ]
    if mid == 55 and choice == 3:
        checks += ["has_variable = zg361_cp_report_routed", "var:zg361_cp_report_routed = 1"]
    if mid == 64 and choice == 1:
        checks += ["has_variable = zg361_cp_successor_valid", "var:zg361_cp_successor_valid = 1"]
    if mid == 66 and choice == 1:
        checks += ["has_variable = zg361_cp_project_active", "var:zg361_cp_project_active = 1"]
    if mid == 129 and choice == 2:
        checks += ["has_variable = zg361_cp_promotion_slot_free", "var:zg361_cp_promotion_slot_free >= 1"]
    if mid == 131:
        checks += ["has_variable = zg361_cp_project_winner"]
    if mid == 132:
        checks += ["has_variable = zg361_cp_capacity_remaining", "has_variable = zg361_cp_project_active"]
    if mid == 133:
        checks += ["has_variable = zg361_cp_stop_judgement"]
    return checks


def atomic_precheck(spec: Mechanism, choice: int) -> str:
    checks = resource_checks(spec, choice)
    existence = [row for row in checks if row.startswith("has_variable = ")]
    reads = [row for row in checks if not row.startswith("has_variable = ")]
    return (
        "trigger_if = {\n\tlimit = {\n"
        + indent("\n".join(existence), 2)
        + "\n\t}\n"
        + indent("\n".join(reads))
        + "\n}\ntrigger_else = { always = no }"
    )


def business_effects(spec: Mechanism, choice: int) -> list[str]:
    if choice not in (1, 2):
        raise ValueError("route C is policy.defer and has no business payload")
    mid, d = spec.mid, spec.domain
    lines = [
        f"set_variable = {{ name = zg361_cp_{spec.field} value = {choice} }}",
        f"change_variable = {{ name = zg361_cp_{d}_operation_used add = 1 }}",
    ]
    if mid == 30:
        amount = (40, 60, 80)[choice - 1]
        winner = ("$TICKET_SUBJECT$", "var:zg361_cp_cross_reviewer", "$TICKET_OWNER$")[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_project_object_manager value = $TICKET_OWNER$ }",
            f"set_variable = {{ name = zg361_cp_project_object_owner value = {winner} }}",
            "set_variable = { name = zg361_cp_project_object_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_project_object_cycle value = $TICKET_CYCLE$ }",
            "set_variable = { name = zg361_cp_project_object_origin_case value = $TICKET_CASE$ }",
            "set_variable = { name = zg361_cp_project_object_version value = 1 }",
            "set_variable = { name = zg361_cp_project_object_deadline_cycle value = $TICKET_CYCLE$ }",
            "change_variable = { name = zg361_cp_project_object_deadline_cycle add = 2 }",
            "set_variable = { name = zg361_cp_project_object_status value = 1 }",
            "set_variable = { name = zg361_cp_project_slot_used value = 1 }",
            f"set_variable = {{ name = zg361_cp_project_winner value = {winner} }}",
            f"set_variable = {{ name = zg361_cp_capacity_reserved value = {amount} }}",
            f"set_variable = {{ name = zg361_cp_capacity_remaining value = {amount} }}",
            f"change_variable = {{ name = zg361_cp_capacity_available subtract = {amount} }}",
            "set_variable = { name = zg361_cp_project_active value = 1 }",
            "set_variable = { name = zg361_cp_resource_winner_n value = 1 }",
        ]
    elif mid == 26:
        delivery, report, relationship = ((20, 2, 1), (15, 4, 3), (10, 6, 5))[choice - 1]
        booked = delivery + report + relationship
        visibility = report * 2 + relationship * 3
        lines += [
            f"change_variable = {{ name = zg361_cp_delivery_hours add = {delivery} }}",
            f"change_variable = {{ name = zg361_cp_report_hours add = {report} }}",
            f"change_variable = {{ name = zg361_cp_relationship_hours add = {relationship} }}",
            f"change_variable = {{ name = zg361_cp_capacity_spent add = {booked} }}",
            f"change_variable = {{ name = zg361_cp_capacity_remaining subtract = {booked} }}",
            f"change_variable = {{ name = zg361_cp_hard_output add = {delivery} }}",
            f"change_variable = {{ name = zg361_cp_visibility_points add = {visibility} }}",
            f"set_variable = {{ name = zg361_cp_m26_booked_hours value = {booked} }}",
            # A contribution receipt is a durable business identity, not the
            # six-field case-kernel operation receipt.  Keep the cursor across
            # portfolio reinitialization and bind the published revision to
            # the case revision produced by the successful operation above.
            "if = { limit = { NOT = { has_variable = zg361_cp_contribution_receipt_cursor } } set_variable = { name = zg361_cp_contribution_receipt_cursor value = 0 } }",
            "change_variable = { name = zg361_cp_contribution_receipt_cursor add = 1 }",
            "set_variable = { name = zg361_cp_m26_contribution_receipt_id value = var:zg361_cp_contribution_receipt_cursor }",
            "set_variable = { name = zg361_cp_m26_contribution_receipt_revision value = var:zg361_case_e_revision }",
        ]
    elif mid == 27:
        shares = ((7000, 2000, 1000), (5000, 3000, 2000), (4000, 4000, 2000))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_baseline_subject_bps value = {shares[0]} }}",
            f"set_variable = {{ name = zg361_cp_baseline_manager_bps value = {shares[1]} }}",
            f"set_variable = {{ name = zg361_cp_baseline_cross_bps value = {shares[2]} }}",
            "set_variable = { name = zg361_cp_baseline_share_total value = 10000 }",
            f"set_variable = {{ name = zg361_cp_claimed_subject_bps value = {shares[0]} }}",
            f"set_variable = {{ name = zg361_cp_claimed_manager_bps value = {shares[1]} }}",
            f"set_variable = {{ name = zg361_cp_claimed_cross_bps value = {shares[2]} }}",
            "set_variable = { name = zg361_cp_claimed_share_total value = 10000 }",
            "set_variable = { name = zg361_cp_contribution_party_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_contribution_party_manager value = $TICKET_OWNER$ }",
            "set_variable = { name = zg361_cp_contribution_party_cross value = var:zg361_cp_cross_reviewer }",
        ]
    elif mid == 31:
        grant, spend, visibility = ((20, 0, 5), (30, 10, 10), (0, 0, 0))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_sponsor_granted value = {grant} }}",
            f"set_variable = {{ name = zg361_cp_sponsor_spent value = {spend} }}",
            f"set_variable = {{ name = zg361_cp_sponsor_balance value = {grant - spend} }}",
            f"set_variable = {{ name = zg361_cp_sponsor_visibility value = {visibility} }}",
            "set_variable = { name = zg361_cp_sponsor_expires_cycle value = $TICKET_CYCLE$ }",
            "change_variable = { name = zg361_cp_sponsor_expires_cycle add = 1 }",
            "set_variable = { name = zg361_cp_sponsor_hard_output value = 0 }",
        ]
    elif mid == 28:
        lines += [
            "set_variable = { name = zg361_cp_claim_transfer_source_delta value = 0 }",
            "set_variable = { name = zg361_cp_claim_transfer_claimant_delta value = 0 }",
            "set_variable = { name = zg361_cp_claim_transfer_total value = 0 }",
            "set_variable = { name = zg361_cp_claim_audit_source_delta value = 0 }",
            "set_variable = { name = zg361_cp_claim_audit_claimant_delta value = 0 }",
            "set_variable = { name = zg361_cp_claim_audit_total value = 0 }",
        ]
        if choice in (1, 2):
            lines += [
                "change_variable = { name = zg361_cp_claimed_subject_bps subtract = 500 }",
                "change_variable = { name = zg361_cp_claimed_manager_bps add = 500 }",
                "set_variable = { name = zg361_cp_claim_transfer_source_delta value = -500 }",
                "set_variable = { name = zg361_cp_claim_transfer_claimant_delta value = 500 }",
            ]
        if choice == 2:
            lines += [
                "change_variable = { name = zg361_cp_claimed_subject_bps add = 500 }",
                "change_variable = { name = zg361_cp_claimed_manager_bps subtract = 500 }",
                "set_variable = { name = zg361_cp_claim_audit_source_delta value = 500 }",
                "set_variable = { name = zg361_cp_claim_audit_claimant_delta value = -500 }",
                "set_variable = { name = zg361_cp_claim_status value = 2 }",
            ]
        elif choice == 1:
            lines += ["set_variable = { name = zg361_cp_claim_status value = 1 }"]
        else:
            lines += ["set_variable = { name = zg361_cp_claim_status value = 3 }"]
        lines += ["set_variable = { name = zg361_cp_claimed_share_total value = 10000 }"]
    elif mid == 29:
        short, delayed, clawback = ((10, 0, 0), (20, 8, 0), (20, 10, 20))[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_metric_baseline value = 100 }",
            f"set_variable = {{ name = zg361_cp_metric_short_gain value = {short} }}",
            f"set_variable = {{ name = zg361_cp_metric_delayed_cost value = {delayed} }}",
            f"set_variable = {{ name = zg361_cp_metric_clawback value = {clawback} }}",
            f"set_variable = {{ name = zg361_cp_metric_net value = {short - delayed - clawback} }}",
            "set_variable = { name = zg361_cp_metric_audited value = 1 }",
        ]
    elif mid == 61:
        hours = (1, 4, 1)[choice - 1]
        lines += [f"set_variable = {{ name = zg361_cp_report_policy_hours value = {hours} }}"]
    elif mid == 54:
        hours = (1, 4, 1)[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_report_object_owner value = $TICKET_OWNER$ }",
            "set_variable = { name = zg361_cp_report_object_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_report_object_cycle value = $TICKET_CYCLE$ }",
            "set_variable = { name = zg361_cp_report_object_case value = $TICKET_CASE$ }",
            "set_variable = { name = zg361_cp_report_object_version value = 1 }",
            "set_variable = { name = zg361_cp_report_object_deadline_cycle value = $TICKET_CYCLE$ }",
            "change_variable = { name = zg361_cp_report_object_deadline_cycle add = 1 }",
            "set_variable = { name = zg361_cp_report_project_origin_case value = var:zg361_cp_project_object_origin_case }",
            f"change_variable = {{ name = zg361_cp_report_hours add = {hours} }}",
            f"change_variable = {{ name = zg361_cp_capacity_spent add = {hours} }}",
            f"change_variable = {{ name = zg361_cp_capacity_remaining subtract = {hours} }}",
            f"set_variable = {{ name = zg361_cp_report_packet_hours value = {hours} }}",
            "set_variable = { name = zg361_cp_report_packet_hard_output value = 0 }",
            "set_variable = { name = zg361_cp_report_subject_bps value = var:zg361_cp_claimed_subject_bps }",
            "set_variable = { name = zg361_cp_report_manager_bps value = var:zg361_cp_claimed_manager_bps }",
            "set_variable = { name = zg361_cp_report_cross_bps value = var:zg361_cp_claimed_cross_bps }",
            "set_variable = { name = zg361_cp_report_share_total value = 10000 }",
        ]
    elif mid == 56:
        if choice == 2:
            lines += [
                "change_variable = { name = zg361_cp_report_subject_bps subtract = 500 }",
                "change_variable = { name = zg361_cp_report_manager_bps add = 500 }",
                "set_variable = { name = zg361_cp_forward_source_delta value = -500 }",
                "set_variable = { name = zg361_cp_forward_manager_delta value = 500 }",
            ]
        else:
            lines += [
                "set_variable = { name = zg361_cp_forward_source_delta value = 0 }",
                "set_variable = { name = zg361_cp_forward_manager_delta value = 0 }",
            ]
        lines += [
            "set_variable = { name = zg361_cp_forward_delta_total value = 0 }",
            "set_variable = { name = zg361_cp_report_share_total value = 10000 }",
            f"set_variable = {{ name = zg361_cp_cross_evidence_attached value = {1 if choice == 3 else 0} }}",
        ]
    elif mid == 57:
        lines += [
            f"set_variable = {{ name = zg361_cp_report_version value = {choice} }}",
            "set_variable = { name = zg361_cp_report_version_author value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_report_version_case value = $TICKET_CASE$ }",
            "set_variable = { name = zg361_cp_report_version_frozen value = 1 }",
        ]
    elif mid == 58:
        routes = (1, 2, 3)[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_report_route_count value = {routes} }}",
            "set_variable = { name = zg361_cp_report_direct_recipient value = $TICKET_OWNER$ }",
            f"set_variable = {{ name = zg361_cp_report_skip_recipient value = {'var:zg361_cp_successor_manager' if choice >= 2 else '$TICKET_OWNER$'} }}",
            f"set_variable = {{ name = zg361_cp_report_cross_recipient value = {'var:zg361_cp_cross_reviewer' if choice == 3 else '$TICKET_OWNER$'} }}",
            "set_variable = { name = zg361_cp_report_routed value = 1 }",
            "set_variable = { name = zg361_cp_report_seen_count value = 0 }",
        ]
    elif mid == 59:
        loss, integrity = ((5, 1), (9, 0), (18, -2))[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_risk_severity value = 9 }",
            f"set_variable = {{ name = zg361_cp_risk_remaining_loss value = {loss} }}",
            f"set_variable = {{ name = zg361_cp_risk_integrity_delta value = {integrity} }}",
            "set_variable = { name = zg361_cp_risk_version_case value = var:zg361_cp_report_version_case }",
        ]
    elif mid == 55:
        reads = (1, 2, 0)[choice - 1]
        lines += [
            f"change_variable = {{ name = zg361_cp_attention_free subtract = {reads} }}",
            f"change_variable = {{ name = zg361_cp_attention_used add = {reads} }}",
            f"set_variable = {{ name = zg361_cp_report_seen_count value = {reads} }}",
            f"change_variable = {{ name = zg361_cp_visibility_points add = {reads * 5} }}",
        ]
    elif mid == 60:
        owner = ("$TICKET_SUBJECT$", "var:zg361_cp_cross_reviewer", "$TICKET_SUBJECT$")[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_idea_owner value = {owner} }}",
            f"set_variable = {{ name = zg361_cp_theft_upheld value = {1 if choice == 1 else 0} }}",
            "set_variable = { name = zg361_cp_idea_version_used value = var:zg361_cp_report_version_case }",
        ]
    elif mid == 63:
        solid, dotted = ((70, 30), (50, 50), (40, 60))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_matrix_solid_weight value = {solid} }}",
            f"set_variable = {{ name = zg361_cp_matrix_dotted_weight value = {dotted} }}",
            "set_variable = { name = zg361_cp_matrix_weight_total value = 100 }",
            "set_variable = { name = zg361_cp_matrix_subject value = $TICKET_SUBJECT$ }",
        ]
    elif mid == 62:
        chosen, integrity = ((1, 0), (3, 1), (4, -2))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_matrix_chosen_route value = {chosen} }}",
            f"set_variable = {{ name = zg361_cp_matrix_integrity_delta value = {integrity} }}",
            "set_variable = { name = zg361_cp_matrix_weights_used value = var:zg361_cp_matrix_weight_total }",
        ]
    elif mid == 65:
        imported = (2, 3, 6)[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_team_size value = 10 }",
            f"set_variable = {{ name = zg361_cp_imported_staff value = {imported} }}",
            f"set_variable = {{ name = zg361_cp_retained_memory value = {10 - imported} }}",
            f"set_variable = {{ name = zg361_cp_favoritism_audit value = {1 if imported * 4 > 10 else 0} }}",
        ]
    elif mid == 64:
        lines += [
            "set_variable = { name = zg361_cp_handoff_old_manager value = $TICKET_OWNER$ }",
            "set_variable = { name = zg361_cp_handoff_new_manager value = var:zg361_cp_successor_manager }",
            f"set_variable = {{ name = zg361_cp_handoff_old_manager_recorded value = {1 if choice in (1, 2) else 0} }}",
            f"set_variable = {{ name = zg361_cp_handoff_new_manager_recorded value = {1 if choice == 1 else 0} }}",
            f"set_variable = {{ name = zg361_cp_handoff_finalized value = {1 if choice == 1 else 0} }}",
        ]
        if choice == 1:
            lines += ["set_variable = { name = zg361_cp_active_manager value = var:zg361_cp_successor_manager }"]
    elif mid == 66:
        lines += [
            "set_variable = { name = zg361_cp_cancel_verified_credit_preserved value = 1 }",
            "set_variable = { name = zg361_cp_cancel_historical_owner value = var:zg361_cp_historical_owner }",
        ]
        if choice == 1:
            lines += [
                "set_variable = { name = zg361_cp_cancel_released_capacity value = var:zg361_cp_capacity_remaining }",
                "change_variable = { name = zg361_cp_capacity_available add = var:zg361_cp_capacity_remaining }",
                "set_variable = { name = zg361_cp_capacity_remaining value = 0 }",
                "set_variable = { name = zg361_cp_capacity_reserved value = var:zg361_cp_capacity_spent }",
                "set_variable = { name = zg361_cp_project_active value = 0 }",
                "set_variable = { name = zg361_cp_project_slot_used value = 0 }",
                "set_variable = { name = zg361_cp_project_object_status value = 2 }",
                "set_variable = { name = zg361_cp_business_outcome value = 2 }",
                "set_variable = { name = zg361_cp_individual_outcome value = 1 }",
            ]
        elif choice == 2:
            lines += ["set_variable = { name = zg361_cp_cancel_pending value = 1 }", "set_variable = { name = zg361_cp_business_outcome value = 3 }"]
        else:
            lines += ["set_variable = { name = zg361_cp_business_outcome value = 1 }"]
    elif mid == 67:
        final_owner = ("$TICKET_SUBJECT$", "var:zg361_cp_cross_reviewer", "$TICKET_SUBJECT$")[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_duplicate_role_owner value = {final_owner} }}",
            "set_variable = { name = zg361_cp_duplicate_role_owner_count value = 1 }",
            f"set_variable = {{ name = zg361_cp_duplicate_transition_used value = {1 if choice == 3 else 0} }}",
            "set_variable = { name = zg361_cp_duplicate_transition_terminal value = 1 }",
        ]
    elif mid == 68:
        protection, carry = ((1, 1), (1, 0), (0, 0))[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_history_original_owner value = var:zg361_cp_historical_owner }",
            "set_variable = { name = zg361_cp_history_mapped_manager value = var:zg361_cp_active_manager }",
            f"set_variable = {{ name = zg361_cp_history_protection_cycles value = {protection} }}",
            f"set_variable = {{ name = zg361_cp_history_carry_pip_requested value = {carry} }}",
            "set_variable = { name = zg361_cp_history_pip_carried value = 0 }",
            "set_variable = { name = zg361_cp_history_consumes_current_quota value = 0 }",
            "set_variable = { name = zg361_cp_history_rating_provenance_case value = $TICKET_CASE$ }",
        ]
        if carry:
            lines += [
                "if = {",
                "\tlimit = {",
                "\t\ttrigger_if = {",
                "\t\t\tlimit = { has_variable = zg361_b2_pip_state }",
                "\t\t\tvar:zg361_b2_pip_state < 5",
                "\t\t}",
                "\t\ttrigger_else = { always = no }",
                "\t}",
                "\tset_variable = { name = zg361_cp_history_pip_carried value = 1 }",
                "}",
            ]
    elif mid == 131:
        track = (1, 2, 2)[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_project_track_code value = {track} }}",
            "set_variable = { name = zg361_cp_project_track_locked value = 1 }",
            "set_variable = { name = zg361_cp_project_registry_owner value = var:zg361_cp_project_winner }",
            "set_variable = { name = zg361_cp_project_metric_owner value = $TICKET_SUBJECT$ }",
        ]
    elif mid == 129:
        lines += [
            "set_variable = { name = zg361_cp_promotion_queued_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_promotion_queue_sequence value = 1 }",
            "set_variable = { name = zg361_cp_promotion_eligible_until value = $TICKET_CYCLE$ }",
            f"change_variable = {{ name = zg361_cp_promotion_eligible_until add = {(2, 2, 1)[choice - 1]} }}",
            "set_variable = { name = zg361_cp_promotion_awarded value = 0 }",
        ]
        if choice == 2:
            lines += [
                "change_variable = { name = zg361_cp_promotion_slot_free subtract = 1 }",
                "change_variable = { name = zg361_cp_promotion_slot_used add = 1 }",
                "set_variable = { name = zg361_cp_promotion_awarded value = 1 }",
                "set_variable = { name = zg361_cp_promotion_winner value = $TICKET_SUBJECT$ }",
            ]
    elif mid == 134:
        owner = ("$TICKET_SUBJECT$", "$TICKET_OWNER$", "var:zg361_cp_cross_reviewer")[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_shared_metric_owner value = {owner} }}",
            "set_variable = { name = zg361_cp_shared_metric_owner_count value = 1 }",
            "set_variable = { name = zg361_cp_shared_metric_contributor_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_shared_metric_dependency_cross value = var:zg361_cp_cross_reviewer }",
            "set_variable = { name = zg361_cp_shared_metric_assignment_locked value = 1 }",
        ]
    elif mid == 130:
        disclosed, wrong_role, trial = ((1, 0, 1), (1, 1, 1), (0, 0, 0))[choice - 1]
        outcome = (3, 1, 2)[choice - 1]
        lines += [
            "set_variable = { name = zg361_cp_transfer_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_transfer_source_manager value = $TICKET_OWNER$ }",
            "set_variable = { name = zg361_cp_transfer_destination_manager value = var:zg361_cp_cross_reviewer }",
            f"set_variable = {{ name = zg361_cp_transfer_pip_disclosed value = {disclosed} }}",
            f"set_variable = {{ name = zg361_cp_transfer_wrong_role_evidence value = {wrong_role} }}",
            f"set_variable = {{ name = zg361_cp_transfer_trial_success value = {trial} }}",
            f"set_variable = {{ name = zg361_cp_transfer_outcome value = {outcome} }}",
            f"set_variable = {{ name = zg361_cp_transfer_source_accountability value = {1 if choice == 3 else 0} }}",
        ]
    elif mid == 132:
        lines += [
            "set_variable = { name = zg361_cp_stop_released_capacity value = 0 }",
            "if = {",
            "\tlimit = { var:zg361_cp_project_active = 1 }",
            "\tset_variable = { name = zg361_cp_stop_released_capacity value = var:zg361_cp_capacity_remaining }",
            "\tchange_variable = { name = zg361_cp_capacity_available add = var:zg361_cp_capacity_remaining }",
            "\tset_variable = { name = zg361_cp_capacity_remaining value = 0 }",
            "\tset_variable = { name = zg361_cp_capacity_reserved value = var:zg361_cp_capacity_spent }",
            "\tset_variable = { name = zg361_cp_project_active value = 0 }",
            "\tset_variable = { name = zg361_cp_project_slot_used value = 0 }",
            "\tset_variable = { name = zg361_cp_project_object_status value = 3 }",
            "}",
        ]
        if choice in (1, 2):
            lines += [
                f"set_variable = {{ name = zg361_cp_stop_evidence_strength value = {(80, 50)[choice - 1]} }}",
                f"set_variable = {{ name = zg361_cp_stop_avoidable_delay value = {choice - 1} }}",
                f"set_variable = {{ name = zg361_cp_stop_judgement value = {(1, 2)[choice - 1]} }}",
                "set_variable = { name = zg361_cp_stop_individual_separate value = 1 }",
            ]
        else:
            lines += [
                "set_variable = { name = zg361_cp_stop_evidence_strength value = 30 }",
                "set_variable = { name = zg361_cp_stop_avoidable_delay value = 0 }",
                "set_variable = { name = zg361_cp_stop_judgement value = 3 }",
                "set_variable = { name = zg361_cp_stop_individual_separate value = 1 }",
            ]
    elif mid == 133:
        lines += [
            "set_variable = { name = zg361_cp_postmortem_stop_judgement_used value = var:zg361_cp_stop_judgement }",
            "set_variable = { name = zg361_cp_postmortem_system_causes value = 1 }",
            "set_variable = { name = zg361_cp_postmortem_learning_actions value = 1 }",
            f"set_variable = {{ name = zg361_cp_postmortem_named_liability value = {1 if choice in (2, 3) else 0} }}",
            f"set_variable = {{ name = zg361_cp_postmortem_liability_actor value = {'$TICKET_OWNER$' if choice == 3 else '$TICKET_SUBJECT$'} }}",
            "set_variable = { name = zg361_cp_postmortem_blanket_penalty value = 0 }",
            "set_variable = { name = zg361_cp_postmortem_learning_consumed value = 0 }",
        ]
    if mid != 30:
        lines += ["change_variable = { name = zg361_cp_project_object_version add = 1 }"]
    if mid in (56, 57, 58, 59, 55, 60):
        lines += ["change_variable = { name = zg361_cp_report_object_version add = 1 }"]
    return lines


def consumer_effects(spec: Mechanism) -> list[str]:
    mid = spec.mid
    specific: dict[int, list[str]] = {
        26: ["set_variable = { name = zg361_cp_visible_hard_output value = var:zg361_cp_hard_output }", "set_variable = { name = zg361_cp_visible_visibility value = var:zg361_cp_visibility_points }"],
        27: ["set_variable = { name = zg361_cp_visible_baseline_share_total value = var:zg361_cp_baseline_share_total }"],
        28: ["set_variable = { name = zg361_cp_visible_claimed_share_total value = var:zg361_cp_claimed_share_total }", "set_variable = { name = zg361_cp_visible_claim_delta_total value = var:zg361_cp_claim_transfer_total }", "set_variable = { name = zg361_cp_visible_audit_delta_total value = var:zg361_cp_claim_audit_total }"],
        29: ["set_variable = { name = zg361_cp_visible_metric_net value = var:zg361_cp_metric_net }", "if = { limit = { has_variable = zg361_kpi_value } change_variable = { name = zg361_kpi_value add = var:zg361_cp_metric_net } }"],
        30: ["set_variable = { name = zg361_cp_visible_capacity_reserved value = var:zg361_cp_capacity_reserved }", "set_variable = { name = zg361_cp_visible_resource_winners value = var:zg361_cp_resource_winner_n }"],
        31: ["set_variable = { name = zg361_cp_visible_sponsor_balance value = var:zg361_cp_sponsor_balance }", "set_variable = { name = zg361_cp_visible_sponsor_output value = var:zg361_cp_sponsor_hard_output }"],
        54: ["set_variable = { name = zg361_cp_visible_delivery_capacity value = var:zg361_cp_capacity_remaining }", "set_variable = { name = zg361_cp_visible_report_output value = var:zg361_cp_report_packet_hard_output }"],
        55: ["set_variable = { name = zg361_cp_visible_attention_used value = var:zg361_cp_attention_used }", "set_variable = { name = zg361_cp_visible_seen_count value = var:zg361_cp_report_seen_count }"],
        56: ["set_variable = { name = zg361_cp_visible_forward_total value = var:zg361_cp_report_share_total }"],
        57: ["set_variable = { name = zg361_cp_visible_version_case value = var:zg361_cp_report_version_case }"],
        58: ["set_variable = { name = zg361_cp_visible_route_count value = var:zg361_cp_report_route_count }", "set_variable = { name = zg361_cp_visible_route_seen_count value = var:zg361_cp_report_seen_count }"],
        59: ["set_variable = { name = zg361_cp_visible_risk_loss value = var:zg361_cp_risk_remaining_loss }"],
        60: ["set_variable = { name = zg361_cp_visible_idea_owner value = var:zg361_cp_idea_owner }"],
        61: ["set_variable = { name = zg361_cp_visible_policy_hours value = var:zg361_cp_report_policy_hours }"],
        62: ["set_variable = { name = zg361_cp_visible_matrix_choice value = var:zg361_cp_matrix_chosen_route }"],
        63: ["set_variable = { name = zg361_cp_visible_matrix_total value = var:zg361_cp_matrix_weight_total }"],
        64: ["set_variable = { name = zg361_cp_visible_active_manager value = var:zg361_cp_active_manager }", "set_variable = { name = zg361_cp_visible_historical_owner value = var:zg361_cp_historical_owner }"],
        65: ["set_variable = { name = zg361_cp_visible_retained_memory value = var:zg361_cp_retained_memory }", "set_variable = { name = zg361_cp_visible_favoritism_audit value = var:zg361_cp_favoritism_audit }"],
        66: ["set_variable = { name = zg361_cp_visible_business_outcome value = var:zg361_cp_business_outcome }", "set_variable = { name = zg361_cp_visible_verified_credit_preserved value = var:zg361_cp_cancel_verified_credit_preserved }"],
        67: ["set_variable = { name = zg361_cp_visible_duplicate_owner value = var:zg361_cp_duplicate_role_owner }", "set_variable = { name = zg361_cp_visible_duplicate_owner_count value = var:zg361_cp_duplicate_role_owner_count }"],
        68: ["set_variable = { name = zg361_cp_visible_history_owner value = var:zg361_cp_history_original_owner }", "set_variable = { name = zg361_cp_visible_history_quota_use value = var:zg361_cp_history_consumes_current_quota }"],
        129: ["set_variable = { name = zg361_cp_visible_promotion_awarded value = var:zg361_cp_promotion_awarded }", "set_variable = { name = zg361_cp_visible_promotion_slots value = var:zg361_cp_promotion_slot_used }"],
        130: ["set_variable = { name = zg361_cp_visible_transfer_outcome value = var:zg361_cp_transfer_outcome }", "set_variable = { name = zg361_cp_visible_source_accountability value = var:zg361_cp_transfer_source_accountability }"],
        131: ["set_variable = { name = zg361_cp_visible_project_track value = var:zg361_cp_project_track_code }", "set_variable = { name = zg361_cp_visible_track_locked value = var:zg361_cp_project_track_locked }"],
        132: ["set_variable = { name = zg361_cp_visible_stop_judgement value = var:zg361_cp_stop_judgement }", "set_variable = { name = zg361_cp_visible_stop_release value = var:zg361_cp_stop_released_capacity }"],
        133: ["set_variable = { name = zg361_cp_visible_learning_actions value = var:zg361_cp_postmortem_learning_actions }", "set_variable = { name = zg361_cp_visible_named_liability value = var:zg361_cp_postmortem_named_liability }", "set_variable = { name = zg361_cp_postmortem_learning_consumed value = 1 }"],
        134: ["set_variable = { name = zg361_cp_visible_shared_metric_owner value = var:zg361_cp_shared_metric_owner }", "set_variable = { name = zg361_cp_visible_shared_metric_owner_count value = var:zg361_cp_shared_metric_owner_count }"],
    }
    rows = list(specific[mid])
    rows += [
        "set_variable = { name = zg361_cp_visible_project_manager value = var:zg361_cp_project_object_manager }",
        "set_variable = { name = zg361_cp_visible_project_owner value = var:zg361_cp_project_object_owner }",
        "set_variable = { name = zg361_cp_visible_project_subject value = var:zg361_cp_project_object_subject }",
        "set_variable = { name = zg361_cp_visible_project_cycle value = var:zg361_cp_project_object_cycle }",
        "set_variable = { name = zg361_cp_visible_project_origin_case value = var:zg361_cp_project_object_origin_case }",
        "set_variable = { name = zg361_cp_visible_project_version value = var:zg361_cp_project_object_version }",
        "set_variable = { name = zg361_cp_visible_project_deadline_cycle value = var:zg361_cp_project_object_deadline_cycle }",
        "set_variable = { name = zg361_cp_visible_project_status value = var:zg361_cp_project_object_status }",
    ]
    if mid in (54, 56, 57, 58, 59, 55, 60):
        rows += [
            "set_variable = { name = zg361_cp_visible_report_case value = var:zg361_cp_report_object_case }",
            "set_variable = { name = zg361_cp_visible_report_version value = var:zg361_cp_report_object_version }",
            "set_variable = { name = zg361_cp_visible_report_deadline_cycle value = var:zg361_cp_report_object_deadline_cycle }",
            "set_variable = { name = zg361_cp_visible_report_project_origin_case value = var:zg361_cp_report_project_origin_case }",
        ]
    return rows


def operation_call(spec: Mechanism, choice: int) -> str:
    d, mid = spec.domain, spec.mid
    return f"""zg361_case_kernel_record_operation_effect = {{
\tOWNER_VAR = zg361_case_{d}_owner
\tSUBJECT_VAR = zg361_case_{d}_subject
\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\tCASE_VAR = zg361_case_{d}_case_serial
\tSTATE_VAR = zg361_case_{d}_state
\tREVISION_VAR = zg361_case_{d}_revision
\tACTIVE_VAR = zg361_case_{d}_active
\tTIMELINE_VAR = zg361_case_{d}_timeline_serial
\tFEEDBACK_VAR = zg361_case_{d}_feedback_revision
\tLAST_OPERATION_VAR = zg361_case_{d}_last_operation
\tLAST_CHOICE_VAR = zg361_case_{d}_last_choice
\tRECEIPT_OWNER_VAR = zg361_cp_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = zg361_cp_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = zg361_cp_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = zg361_cp_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = zg361_cp_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = zg361_cp_m{mid}_receipt_choice
\tTICKET_OWNER = $TICKET_OWNER$
\tTICKET_SUBJECT = $TICKET_SUBJECT$
\tTICKET_CYCLE = $TICKET_CYCLE$
\tTICKET_CASE = $TICKET_CASE$
\tTICKET_STATE = {spec.state}
\tOPERATION_ID = {mid}
\tCHOICE = {choice}
}}"""


def render_consumer(spec: Mechanism) -> str:
    d, mid = spec.domain, spec.mid
    identity = ("owner", "subject", "cycle", "case", "state")
    required = [f"zg361_cp_m{mid}_write_{name}" for name in identity] + [
        f"zg361_cp_{spec.field}",
        "zg361_cp_project_object_manager",
        "zg361_cp_project_object_owner",
        "zg361_cp_project_object_subject",
        "zg361_cp_project_object_cycle",
        "zg361_cp_project_object_origin_case",
        "zg361_cp_project_object_version",
        "zg361_cp_project_object_deadline_cycle",
        "zg361_cp_project_object_status",
    ]
    if mid in (54, 56, 57, 58, 59, 55, 60):
        required += [
            "zg361_cp_report_object_case",
            "zg361_cp_report_object_version",
            "zg361_cp_report_object_deadline_cycle",
            "zg361_cp_report_project_origin_case",
        ]
    existence = "\n".join(f"has_variable = {name}" for name in required)
    comparisons = "\n".join(
        f"var:zg361_cp_m{mid}_write_{name} = var:zg361_case_{d}_{'cycle_serial' if name == 'cycle' else 'case_serial' if name == 'case' else name}"
        for name in identity
    )
    consumed = "\n".join(
        f"set_variable = {{ name = zg361_cp_m{mid}_consumed_{name} value = var:zg361_cp_m{mid}_write_{name} }}"
        for name in identity
    )
    special = "\n".join(consumer_effects(spec))
    return f"""# #{mid:03d} meaningful downstream consumer; never reads an unfrozen write.
zg361_cp_m{mid}_consume_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
{indent(existence, 5)}
\t\t\t\t}}
{indent(comparisons, 4)}
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
{indent(consumed, 2)}
\t\tset_variable = {{ name = zg361_cp_m{mid}_visible_value value = var:zg361_cp_{spec.field} }}
\t\tset_variable = {{ name = zg361_cp_m{mid}_visible_provenance_case value = var:zg361_cp_m{mid}_write_case }}
{indent(special, 2)}
\t\tchange_variable = {{ name = zg361_cp_{d}_visible_revision add = 1 }}
\t}}
}}"""


def debt_effects(spec: Mechanism) -> list[str]:
    """Freeze exactly one route-C debt identity; never write business state."""

    mid, d = spec.mid, spec.domain
    stem = f"zg361_cp_m{mid}_debt"
    return [
        f"set_variable = {{ name = zg361_cp_{spec.field} value = 3 }}",
        f"change_variable = {{ name = zg361_cp_{d}_operation_used add = 1 }}",
        f"set_variable = {{ name = {stem}_owner value = $TICKET_OWNER$ }}",
        f"set_variable = {{ name = {stem}_subject value = $TICKET_SUBJECT$ }}",
        f"set_variable = {{ name = {stem}_cycle value = $TICKET_CYCLE$ }}",
        f"set_variable = {{ name = {stem}_case value = $TICKET_CASE$ }}",
        f"set_variable = {{ name = {stem}_state value = {spec.state} }}",
        f"set_variable = {{ name = {stem}_mechanism value = {mid} }}",
        f"set_variable = {{ name = {stem}_due_cycle value = $TICKET_CYCLE$ }}",
        f"change_variable = {{ name = {stem}_due_cycle add = 1 }}",
        f"set_variable = {{ name = {stem}_status value = 1 }}",
        f"set_variable = {{ name = {stem}_audit_state value = 1 }}",
        f"set_variable = {{ name = {stem}_business_object_created value = 0 }}",
        "set_variable = { name = zg361_cp_portfolio_deferred value = 1 }",
        "set_variable = { name = zg361_cp_deferred_cleanup_status value = 1 }",
        "change_variable = { name = zg361_cp_policy_debt_open_n add = 1 }",
    ]


def render_due_debt_consumer(spec: Mechanism) -> str:
    """Settle one exact debt once through the current central-adapter root."""

    mid = spec.mid
    stem = f"zg361_cp_m{mid}_debt"
    receipt = f"zg361_cp_m{mid}_receipt"
    red_code = 60000 + mid
    return f"""# #{mid:03d} next-cycle policy-debt consumer.  The frozen source owner
# remains immutable; settled_by records the exact manager who discharged it.
zg361_cp_m{mid}_consume_due_policy_debt_effect = {{
	if = {{
		limit = {{
			has_variable = {stem}_owner
			has_variable = {stem}_subject
			has_variable = {stem}_cycle
			has_variable = {stem}_case
			has_variable = {stem}_state
			has_variable = {stem}_mechanism
			has_variable = {stem}_due_cycle
			has_variable = {stem}_status
			has_variable = {stem}_audit_state
			has_variable = {stem}_business_object_created
			has_variable = {receipt}_owner
			has_variable = {receipt}_subject
			has_variable = {receipt}_cycle
			has_variable = {receipt}_case
			has_variable = {receipt}_state
			has_variable = {receipt}_choice
			root = {{
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
			}}
			zg361_is_reviewable_vassal_trigger = yes
			liege = root
			var:{stem}_status = 1
			var:{stem}_audit_state = 1
			var:{stem}_business_object_created = 0
			var:{stem}_mechanism = {mid}
			var:{stem}_owner = root
			var:{stem}_subject = this
			var:{receipt}_owner = var:{stem}_owner
			var:{receipt}_subject = var:{stem}_subject
			var:{receipt}_cycle = var:{stem}_cycle
			var:{receipt}_case = var:{stem}_case
			var:{receipt}_state = var:{stem}_state
			var:{receipt}_choice = 3
			root.var:zg361_review_serial = var:{stem}_due_cycle
		}}
		root = {{ change_variable = {{ name = zg361_b2_management_debt add = 1 }} }}
		set_variable = {{ name = {stem}_status value = 2 }}
		set_variable = {{ name = {stem}_audit_state value = 3 }}
		set_variable = {{ name = {stem}_settled_by value = root }}
		set_variable = {{ name = {stem}_settled_cycle value = root.var:zg361_review_serial }}
		set_variable = {{ name = {stem}_performance_sink value = 1 }}
		set_variable = {{ name = {stem}_consumer_status value = 1 }}
		change_variable = {{ name = zg361_cp_policy_debt_open_n add = -1 }}
		change_variable = {{ name = zg361_cp_policy_debt_settled_n add = 1 }}
	}}
	else_if = {{
		# Exact settled replay is audit-only and never reaches the KPI sink again.
		limit = {{
			has_variable = {stem}_status
			has_variable = {stem}_settled_by
			has_variable = {stem}_settled_cycle
			var:{stem}_status = 2
			var:{stem}_settled_by = root
			root = {{ has_variable = zg361_review_serial }}
			root.var:zg361_review_serial >= var:{stem}_settled_cycle
		}}
		set_variable = {{ name = {stem}_consumer_status value = 2 }}
	}}
	else_if = {{
		# A complete exact debt that is not due is future input, never current work.
		limit = {{
			has_variable = {stem}_owner
			has_variable = {stem}_subject
			has_variable = {stem}_due_cycle
			has_variable = {stem}_status
			var:{stem}_status = 1
			var:{stem}_owner = root
			var:{stem}_subject = this
			zg361_is_reviewable_vassal_trigger = yes
			liege = root
			root = {{ has_variable = zg361_review_serial }}
			root.var:zg361_review_serial < var:{stem}_due_cycle
		}}
		set_variable = {{ name = {stem}_consumer_status value = 5 }}
		set_variable = {{ name = zg361_cp_policy_debt_consumer_blocked value = 1 }}
	}}
	else_if = {{
		# Pending but non-exact means stale/cross-owner/corrupt identity: fail closed.
		limit = {{ has_variable = {stem}_status var:{stem}_status = 1 }}
		set_variable = {{ name = {stem}_consumer_status value = 3 }}
		set_variable = {{ name = zg361_cp_policy_debt_consumer_blocked value = 1 }}
		set_variable = {{ name = zg361_cp_last_red_code value = {red_code} }}
	}}
}}"""


def render_due_debt_aggregate() -> str:
    calls = "\n".join(
        f"\tzg361_cp_m{spec.mid}_consume_due_policy_debt_effect = yes"
        for spec in MECHANISMS
    )
    return f"""# The public portfolio adapter is the sole package-owned due pass.
zg361_cp_consume_due_policy_debts_effect = {{
	remove_variable = zg361_cp_deferred_cleanup_due_cycle
	if = {{
		limit = {{ has_variable = zg361_cp_portfolio_cycle }}
		set_variable = {{ name = zg361_cp_deferred_cleanup_due_cycle value = var:zg361_cp_portfolio_cycle }}
		change_variable = {{ name = zg361_cp_deferred_cleanup_due_cycle add = 1 }}
	}}
	remove_variable = zg361_cp_policy_debt_consumer_blocked
{calls}
	if = {{
		limit = {{ NOT = {{ has_variable = zg361_cp_policy_debt_consumer_blocked }} }}
		zg361_cp_settle_deferred_portfolio_effect = yes
	}}
}}"""


def final_domain_action(domain: str) -> str:
    next_domain = NEXT_DOMAIN[domain]
    if next_domain:
        return f"""set_variable = {{ name = zg361_cp_pending_player_event value = {QUEUE_EVENTS[domain]} }}
var:zg361_case_{domain}_owner = {{
\ttrigger_event = {{ id = zg361cp.{QUEUE_EVENTS[domain]} days = 1 }}
}}"""
    return "zg361_cp_finalize_portfolio_effect = yes"


def player_event_id(mid: int) -> int:
    """Return the hidden batch dispatcher or the original visible event."""

    return BATCH_DISPATCH_EVENT_BASE + mid if mid in BATCHABLE_IDS else mid


def pending_player_event_ids(domain: str) -> tuple[int, ...]:
    """Return every durable player edge owned by one domain."""

    first = BATCH_MODE_EVENT if domain == "e" else player_event_id(DOMAIN_ORDER[domain][0])
    ids = [first, *(player_event_id(mid) for mid in DOMAIN_ORDER[domain])]
    if NEXT_DOMAIN[domain] is not None:
        ids.append(QUEUE_EVENTS[domain])
    return tuple(dict.fromkeys(ids))


def current_case_receipts(spec: Mechanism) -> str:
    """Render exact current-case receipt checks without relying on saved scopes."""

    domain = spec.domain
    return (
        any_receipt(spec)
        .replace("$TICKET_OWNER$", "root")
        .replace("$TICKET_SUBJECT$", "this")
        .replace("$TICKET_CYCLE$", f"var:zg361_case_{domain}_cycle_serial")
        .replace("$TICKET_CASE$", f"var:zg361_case_{domain}_case_serial")
    )


def render_resume_domain(domain: str) -> str:
    event_ids = pending_player_event_ids(domain)
    event_filter = "\n".join(
        f"\tvar:zg361_cp_pending_player_event = {event_id}" for event_id in event_ids
    )
    dispatch = "\n".join(
        f"""{"if" if index == 0 else "else_if"} = {{
\tlimit = {{ var:zg361_cp_pending_player_event = {event_id} }}
\tscope:zg361_cp_{domain}_owner = {{ trigger_event = {{ id = zg361cp.{event_id} }} }}
}}"""
        for index, event_id in enumerate(event_ids)
    )
    return f"""if = {{
\tlimit = {{
\t\tOR = {{
{event_filter}
\t\t}}
\t\thas_variable = zg361_case_{domain}_owner
\t\thas_variable = zg361_case_{domain}_subject
\t\thas_variable = zg361_case_{domain}_cycle_serial
\t\thas_variable = zg361_case_{domain}_case_serial
\t\tvar:zg361_case_{domain}_owner = root
\t\tvar:zg361_case_{domain}_subject = this
\t}}
\tvar:zg361_case_{domain}_owner = {{ save_scope_as = zg361_cp_{domain}_owner }}
\tsave_scope_as = zg361_cp_{domain}_subject
\tvar:zg361_cp_cross_reviewer = {{ save_scope_as = zg361_cp_{domain}_cross_reviewer }}
\tvar:zg361_cp_successor_manager = {{ save_scope_as = zg361_cp_{domain}_successor_manager }}
\tvar:zg361_cp_active_manager = {{ save_scope_as = zg361_cp_{domain}_active_manager }}
\tvar:zg361_cp_historical_owner = {{ save_scope_as = zg361_cp_{domain}_historical_owner }}
\tsave_scope_value_as = {{ name = zg361_cp_{domain}_cycle value = var:zg361_case_{domain}_cycle_serial }}
\tsave_scope_value_as = {{ name = zg361_cp_{domain}_case value = var:zg361_case_{domain}_case_serial }}
{indent(dispatch)}
}}"""


def render_pending_player_event_effects() -> str:
    m26 = by_id()[26]
    m27 = by_id()[27]
    domains = "\nelse_".join(render_resume_domain(domain) for domain in ("e", "i", "j", "r"))
    return f"""# Clear only the exact edge that actually entered; a newer cursor is never consumed.
zg361_cp_clear_pending_player_event_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = zg361_cp_pending_player_event
\t\t\tvar:zg361_cp_pending_player_event = $EVENT$
\t\t}}
\t\tremove_variable = zg361_cp_pending_player_event
\t}}
}}

# Recover a player D+1 edge from the persistent case tuple.  The first branch
# is a narrow migration for the frozen post-.26 R296 checkpoint, which predates
# the cursor but has an exact current .26 receipt and no current .27 receipt.
zg361_cp_resume_pending_player_event_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tNOT = {{ has_variable = zg361_cp_pending_player_event }}
\t\t\thas_variable = zg361_cp_portfolio_closed
\t\t\tvar:zg361_cp_portfolio_closed = 0
\t\t\thas_variable = zg361_case_e_owner
\t\t\thas_variable = zg361_case_e_subject
\t\t\thas_variable = zg361_case_e_cycle_serial
\t\t\thas_variable = zg361_case_e_case_serial
\t\t\thas_variable = zg361_case_e_state
\t\t\thas_variable = zg361_case_e_active
\t\t\tvar:zg361_case_e_owner = root
\t\t\tvar:zg361_case_e_subject = this
\t\t\tvar:zg361_case_e_state = 2
\t\t\tvar:zg361_case_e_active = 1
{indent(current_case_receipts(m26), 3)}
\t\t\tNOT = {{
{indent(current_case_receipts(m27), 4)}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_cp_pending_player_event value = 27 }}
\t\tdebug_log = "ZG361CP: inferred missing post-m26 player edge"
\t}}
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = zg361_cp_pending_player_event
\t\t\thas_variable = zg361_cp_portfolio_subject
\t\t\thas_variable = zg361_cp_portfolio_cycle
\t\t\thas_variable = zg361_cp_portfolio_closed
\t\t\thas_variable = zg361_cp_cross_reviewer
\t\t\thas_variable = zg361_cp_successor_manager
\t\t\thas_variable = zg361_cp_active_manager
\t\t\thas_variable = zg361_cp_historical_owner
\t\t\tvar:zg361_cp_portfolio_subject = this
\t\t\tvar:zg361_cp_portfolio_cycle = root.var:zg361_review_serial
\t\t\tvar:zg361_cp_portfolio_closed = 0
\t\t\troot = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }}
\t\t}}
{indent(domains, 2)}
\t}}
}}"""


def render_route(spec: Mechanism, choice: int) -> str:
    d, mid = spec.domain, spec.mid
    letter = "abc"[choice - 1]
    guard = tuple_guard(spec)
    receipts = any_receipt(spec)
    precheck = atomic_precheck(spec, choice)
    if choice == 3:
        # Control-plane route: the shared kernel still freezes the exact
        # receipt and advances the case, but no business payload, resource,
        # write ticket or business consumer is reachable.
        payload = "\n".join(debt_effects(spec))
    else:
        business = "\n".join(business_effects(spec, choice))
        payload = business + f"""
set_variable = {{ name = zg361_cp_m{mid}_write_owner value = $TICKET_OWNER$ }}
set_variable = {{ name = zg361_cp_m{mid}_write_subject value = $TICKET_SUBJECT$ }}
set_variable = {{ name = zg361_cp_m{mid}_write_cycle value = $TICKET_CYCLE$ }}
set_variable = {{ name = zg361_cp_m{mid}_write_case value = $TICKET_CASE$ }}
set_variable = {{ name = zg361_cp_m{mid}_write_state value = {spec.state} }}
set_variable = {{ name = zg361_cp_m{mid}_provenance_choice value = {choice} }}
zg361_cp_m{mid}_consume_effect = yes"""
    advance = ""
    if mid in STAGE_LAST[d]:
        edge = STAGE_LAST[d][mid]
        last_state = max(STAGE_LAST[d].values())
        after = ""
        if edge == last_state:
            after = f"\n\t\t\t{final_domain_action(d)}"
        advance = f"""
\t\tif = {{
\t\t\tlimit = {{
{indent(stage_barrier(spec), 4)}
\t\t\t}}
\t\t\tzg361_case_{d}_advance_{edge:02d}_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\t}}{after}
\t\t}}
"""
    red_code = mid * 10 + choice
    return f"""# #{mid:03d} route {letter.upper()}: full five-field guard, one receipt and atomic preflight.
zg361_cp_m{mid}_route_{letter}_effect = {{
\tremove_variable = zg361_cp_runtime_applied
\tremove_variable = zg361_cp_last_red_code
\tif = {{
\t\tlimit = {{
{indent(guard, 3)}
\t\t\tNOT = {{
{indent(receipts, 4)}
\t\t\t}}
{indent(precheck, 3)}
\t\t}}
{indent(operation_call(spec, choice), 2)}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\t\t\t\tvar:zg361_case_kernel_applied = 1
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t}}
{indent(payload, 3)}
\t\t\tset_variable = {{ name = zg361_cp_runtime_applied value = 1 }}
\t\t\tset_variable = {{ name = zg361_cp_runtime_status value = 1 }}
{advance.rstrip()}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
\t\t\tNOT = {{
{indent(receipts, 4)}
\t\t\t}}
\t\t\tNOT = {{
{indent(precheck, 4)}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_cp_last_red_code value = {red_code} }}
\t\tset_variable = {{ name = zg361_cp_runtime_status value = 4 }} # typed RED; no receipt, business or resource write
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
{indent(receipts, 3)}
\t\t}}
\t\tset_variable = {{ name = zg361_cp_runtime_status value = 2 }} # idempotent no-op
\t}}
\telse = {{ set_variable = {{ name = zg361_cp_runtime_status value = 3 }} }} # stale no-op
}}"""


def render_domain_init(domain: str) -> str:
    cleanup = []
    for mid in DOMAIN_ORDER[domain]:
        cleanup += [
            f"remove_variable = zg361_cp_{by_id()[mid].field}",
            f"remove_variable = zg361_cp_m{mid}_visible_value",
        ]
    lines = [
        f"set_variable = {{ name = zg361_cp_{domain}_operation_total value = {len(DOMAIN_ORDER[domain])} }}",
        f"set_variable = {{ name = zg361_cp_{domain}_operation_used value = 0 }}",
        f"set_variable = {{ name = zg361_cp_{domain}_visible_revision value = 0 }}",
        *cleanup,
    ]
    return f"""zg361_cp_{domain}_initialize_effect = {{
{indent(chr(10).join(lines))}
}}"""


def render_subject_read(domain: str) -> str:
    return f"""# Assessed-only adapter. A count or baron may read their own case revision,
# but receives no authority to open cases, reserve capacity or assess anyone.
zg361_cp_{domain}_subject_read_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tzg361_case_kernel_subject_self_guard_trigger = {{
\t\t\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\t\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = zg361_cp_{domain}_subject_seen_revision value = var:zg361_cp_{domain}_visible_revision }}
\t}}
}}"""


def ai_choice(mid: int) -> str:
    d = by_id()[mid].domain
    defer = f"""zg361_cp_m{mid}_route_c_effect = {{
\tTICKET_OWNER = scope:zg361_cp_{d}_owner
\tTICKET_SUBJECT = scope:zg361_cp_{d}_subject
\tTICKET_CYCLE = scope:zg361_cp_{d}_cycle
\tTICKET_CASE = scope:zg361_cp_{d}_case
}}"""
    if mid == 64:
        ordinary = """if = {
\tlimit = {
\t\ttrigger_if = {
\t\t\tlimit = { has_variable = zg361_cp_successor_valid }
\t\t\tvar:zg361_cp_successor_valid = 1
\t\t}
\t\ttrigger_else = { always = no }
\t}
\tzg361_cp_m64_route_a_effect = {
\t\tTICKET_OWNER = scope:zg361_cp_j_owner
\t\tTICKET_SUBJECT = scope:zg361_cp_j_subject
\t\tTICKET_CYCLE = scope:zg361_cp_j_cycle
\t\tTICKET_CASE = scope:zg361_cp_j_case
\t}
}
else = {
\tzg361_cp_m64_route_c_effect = {
\t\tTICKET_OWNER = scope:zg361_cp_j_owner
\t\tTICKET_SUBJECT = scope:zg361_cp_j_subject
\t\tTICKET_CYCLE = scope:zg361_cp_j_cycle
\t\tTICKET_CASE = scope:zg361_cp_j_case
\t}
}"""
    else:
        ordinary = f"""zg361_cp_m{mid}_route_a_effect = {{
\tTICKET_OWNER = scope:zg361_cp_{d}_owner
\tTICKET_SUBJECT = scope:zg361_cp_{d}_subject
\tTICKET_CYCLE = scope:zg361_cp_{d}_cycle
\tTICKET_CASE = scope:zg361_cp_{d}_case
}}"""
    return f"""if = {{
\tlimit = {{
\t\ttrigger_if = {{
\t\t\tlimit = {{ has_variable = zg361_cp_portfolio_deferred }}
\t\t\tvar:zg361_cp_portfolio_deferred = 1
\t\t}}
\t\ttrigger_else = {{ always = no }}
\t}}
{indent(defer)}
}}
else = {{
{indent(ordinary)}
}}"""


def render_ai(domain: str) -> str:
    calls = "\n".join(ai_choice(mid) for mid in DOMAIN_ORDER[domain])
    return f"""zg361_cp_{domain}_run_authorized_ai_effect = {{
\t# Authorized exception: landed, living celestial duke+ managers only.
\t# AI execution is background-only; it never opens a character event.
\tif = {{
\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
{indent(calls, 2)}
\t}}
}}"""


def render_launch(domain: str) -> str:
    first = DOMAIN_ORDER[domain][0]
    first_event = BATCH_MODE_EVENT if domain == "e" else player_event_id(first)
    portfolio_init = "\n\t\tzg361_cp_initialize_portfolio_effect = yes" if domain == "e" else ""
    return f"""# Subject-scope entry; ROOT remains the eligible direct manager.
zg361_cp_{domain}_launch_effect = {{
\tzg361_case_{domain}_open_effect = yes
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\t\t\tvar:zg361_case_kernel_applied = 1
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
{portfolio_init}
\t\tzg361_cp_{domain}_initialize_effect = yes
\t\tvar:zg361_case_{domain}_owner = {{ save_scope_as = zg361_cp_{domain}_owner }}
\t\tsave_scope_as = zg361_cp_{domain}_subject
\t\tvar:zg361_cp_cross_reviewer = {{ save_scope_as = zg361_cp_{domain}_cross_reviewer }}
\t\tvar:zg361_cp_successor_manager = {{ save_scope_as = zg361_cp_{domain}_successor_manager }}
\t\tvar:zg361_cp_active_manager = {{ save_scope_as = zg361_cp_{domain}_active_manager }}
\t\tvar:zg361_cp_historical_owner = {{ save_scope_as = zg361_cp_{domain}_historical_owner }}
\t\tsave_scope_value_as = {{ name = zg361_cp_{domain}_cycle value = var:zg361_case_{domain}_cycle_serial }}
\t\tsave_scope_value_as = {{ name = zg361_cp_{domain}_case value = var:zg361_case_{domain}_case_serial }}
\t\tif = {{
\t\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tzg361_cp_{domain}_run_authorized_ai_effect = yes
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ root = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tset_variable = {{ name = zg361_cp_pending_player_event value = {first_event} }}
\t\t\tscope:zg361_cp_{domain}_owner = {{ trigger_event = {{ id = zg361cp.{first_event} }} }}
\t\t}}
\t}}
}}"""


def render_portfolio_entries() -> str:
    return r'''# Freeze portfolio actors and finite books exactly once, then execute E -> I -> J -> R.
zg361_cp_initialize_portfolio_effect = {
	save_temporary_scope_as = zg361_cp_portfolio_subject_scope
	remove_variable = zg361_cp_pending_player_event
	set_variable = { name = zg361_cp_portfolio_subject value = this }
	set_variable = { name = zg361_cp_portfolio_cycle value = root.var:zg361_review_serial }
	root = { set_variable = { name = zg361_cp_manager_portfolio_cycle value = var:zg361_review_serial } }
	set_variable = { name = zg361_cp_historical_owner value = root }
	set_variable = { name = zg361_cp_active_manager value = root }
	set_variable = { name = zg361_cp_cross_reviewer value = root }
	set_variable = { name = zg361_cp_cross_reviewer_valid value = 0 }
	set_variable = { name = zg361_cp_successor_manager value = root }
	set_variable = { name = zg361_cp_successor_valid value = 0 }
	root = {
		if = {
			limit = { exists = liege liege = { zg361_is_celestial_liege_trigger = yes } }
			liege = { save_temporary_scope_as = zg361_cp_successor_candidate }
			scope:zg361_cp_portfolio_subject_scope = {
				set_variable = { name = zg361_cp_successor_manager value = scope:zg361_cp_successor_candidate }
				set_variable = { name = zg361_cp_successor_valid value = 1 }
				set_variable = { name = zg361_cp_cross_reviewer value = scope:zg361_cp_successor_candidate }
				set_variable = { name = zg361_cp_cross_reviewer_valid value = 1 }
			}
		}
		ordered_vassal = {
			limit = {
				zg361_is_reviewable_vassal_trigger = yes
				NOT = { this = scope:zg361_cp_portfolio_subject_scope }
			}
			order_by = stewardship
			position = 0
			save_temporary_scope_as = zg361_cp_cross_candidate
			scope:zg361_cp_portfolio_subject_scope = {
				set_variable = { name = zg361_cp_cross_reviewer value = scope:zg361_cp_cross_candidate }
				set_variable = { name = zg361_cp_cross_reviewer_valid value = 1 }
			}
		}
	}
	set_variable = { name = zg361_cp_capacity_total value = 100 }
	set_variable = { name = zg361_cp_capacity_available value = 100 }
	set_variable = { name = zg361_cp_capacity_reserved value = 0 }
	set_variable = { name = zg361_cp_capacity_remaining value = 0 }
	set_variable = { name = zg361_cp_capacity_spent value = 0 }
	set_variable = { name = zg361_cp_project_slot_total value = 1 }
	set_variable = { name = zg361_cp_project_slot_used value = 0 }
	set_variable = { name = zg361_cp_project_active value = 0 }
	set_variable = { name = zg361_cp_delivery_hours value = 0 }
	set_variable = { name = zg361_cp_report_hours value = 0 }
	set_variable = { name = zg361_cp_relationship_hours value = 0 }
	set_variable = { name = zg361_cp_hard_output value = 0 }
	set_variable = { name = zg361_cp_visibility_points value = 0 }
	set_variable = { name = zg361_cp_attention_total value = 2 }
	set_variable = { name = zg361_cp_attention_free value = 2 }
	set_variable = { name = zg361_cp_attention_used value = 0 }
	set_variable = { name = zg361_cp_promotion_slot_total value = 1 }
	set_variable = { name = zg361_cp_promotion_slot_free value = 1 }
	set_variable = { name = zg361_cp_promotion_slot_used value = 0 }
	set_variable = { name = zg361_cp_claimed_share_total value = 0 }
	set_variable = { name = zg361_cp_portfolio_deferred value = 0 }
	if = {
		limit = { NOT = { has_variable = zg361_cp_policy_debt_open_n } }
		set_variable = { name = zg361_cp_policy_debt_open_n value = 0 }
	}
	if = {
		limit = { NOT = { has_variable = zg361_cp_policy_debt_settled_n } }
		set_variable = { name = zg361_cp_policy_debt_settled_n value = 0 }
	}
	set_variable = { name = zg361_cp_portfolio_closed value = 0 }
}

# Due-cycle lifecycle settlement is deliberately separate from route C.
# It may close an A/B project left open in the prior deferred portfolio only
# after every exact mechanism debt has settled and the frozen cycle is due.
zg361_cp_settle_deferred_portfolio_effect = {
	if = {
		limit = {
			has_variable = zg361_cp_portfolio_deferred
			has_variable = zg361_cp_deferred_cleanup_status
			has_variable = zg361_cp_policy_debt_open_n
			has_variable = zg361_cp_portfolio_closed
			has_variable = zg361_cp_historical_owner
			has_variable = zg361_cp_portfolio_subject
			has_variable = zg361_cp_portfolio_cycle
			has_variable = zg361_cp_deferred_cleanup_due_cycle
			has_variable = zg361_cp_project_active
			has_variable = zg361_cp_capacity_available
			has_variable = zg361_cp_capacity_remaining
			has_variable = zg361_cp_capacity_reserved
			has_variable = zg361_cp_capacity_spent
			has_variable = zg361_cp_project_slot_used
			has_variable = zg361_cp_final_deferred
			has_variable = zg361_cp_final_conservation_ok
			has_variable = zg361_cp_final_deferred_capacity_check
			root = {
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
			}
			zg361_is_reviewable_vassal_trigger = yes
			liege = root
			var:zg361_cp_portfolio_deferred = 1
			var:zg361_cp_deferred_cleanup_status = 1
			var:zg361_cp_policy_debt_open_n = 0
			var:zg361_cp_portfolio_closed = 1
			var:zg361_cp_historical_owner = root
			var:zg361_cp_portfolio_subject = this
			var:zg361_cp_final_deferred = 1
			var:zg361_cp_final_conservation_ok = 1
			var:zg361_cp_final_deferred_capacity_check = 100
			root.var:zg361_review_serial = var:zg361_cp_deferred_cleanup_due_cycle
			trigger_if = {
				limit = { var:zg361_cp_project_active = 1 }
				has_variable = zg361_cp_project_object_status
				var:zg361_cp_project_object_status = 1
				var:zg361_cp_project_slot_used = 1
			}
			trigger_else = {
				var:zg361_cp_project_active = 0
				var:zg361_cp_project_slot_used = 0
			}
		}
		if = {
			limit = { var:zg361_cp_project_active = 1 }
			change_variable = { name = zg361_cp_capacity_available add = var:zg361_cp_capacity_remaining }
			set_variable = { name = zg361_cp_capacity_remaining value = 0 }
			set_variable = { name = zg361_cp_capacity_reserved value = var:zg361_cp_capacity_spent }
			set_variable = { name = zg361_cp_project_active value = 0 }
			set_variable = { name = zg361_cp_project_slot_used value = 0 }
			set_variable = { name = zg361_cp_project_object_status value = 3 }
		}
		set_variable = { name = zg361_cp_deferred_cleanup_status value = 2 }
		set_variable = { name = zg361_cp_deferred_cleanup_settled_by value = root }
		set_variable = { name = zg361_cp_deferred_cleanup_settled_cycle value = root.var:zg361_review_serial }
		remove_variable = zg361_cp_pending_player_event
	}
	else_if = {
		limit = {
			has_variable = zg361_cp_deferred_cleanup_status
			var:zg361_cp_deferred_cleanup_status = 1
		}
		set_variable = { name = zg361_cp_policy_debt_consumer_blocked value = 1 }
		set_variable = { name = zg361_cp_last_red_code value = 60999 }
	}
}

# Public manager-scope ABI. Counts and barons may be $SUBJECT$, never ROOT.
zg361_cp_open_portfolio_effect = {
	# The existing central stage-8 adapter doubles as the package-owned due
	# scheduler.  Consume the frozen prior-cycle debts before opening or
	# overwriting any new portfolio state.
	$SUBJECT$ = { zg361_cp_consume_due_policy_debts_effect = yes }
	if = {
		limit = {
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			has_variable = zg361_review_serial
			$SUBJECT$ = { NOT = { has_variable = zg361_cp_policy_debt_consumer_blocked } }
			$SUBJECT$ = { zg361_is_reviewable_vassal_trigger = yes liege = root }
			# Cross-department evidence needs a distinct reviewer: another direct
			# official, or this manager's own eligible manager.
			OR = {
				any_vassal = {
					zg361_is_reviewable_vassal_trigger = yes
					NOT = { this = $SUBJECT$ }
				}
				liege = { zg361_is_celestial_liege_trigger = yes }
			}
			trigger_if = {
				limit = { has_variable = zg361_cp_manager_portfolio_cycle }
				NOT = { var:zg361_cp_manager_portfolio_cycle = var:zg361_review_serial }
			}
			trigger_else = { always = yes }
			$SUBJECT$ = {
				trigger_if = {
					limit = { has_variable = zg361_cp_portfolio_cycle }
					NOT = { var:zg361_cp_portfolio_cycle = root.var:zg361_review_serial }
				}
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_e_active } var:zg361_case_e_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_i_active } var:zg361_case_i_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_j_active } var:zg361_case_j_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_case_r_active } var:zg361_case_r_active = 0 }
				trigger_else = { always = yes }
			}
		}
		$SUBJECT$ = {
			zg361_cp_e_launch_effect = yes
		}
	}
}

zg361_cp_finalize_portfolio_effect = {
	remove_variable = zg361_cp_pending_player_event
	set_variable = { name = zg361_cp_portfolio_closed value = 1 }
	set_variable = { name = zg361_cp_final_owner value = var:zg361_case_r_owner }
	set_variable = { name = zg361_cp_final_subject value = var:zg361_case_r_subject }
	set_variable = { name = zg361_cp_final_cycle value = var:zg361_case_r_cycle_serial }
	set_variable = { name = zg361_cp_final_case value = var:zg361_case_r_case_serial }
	set_variable = { name = zg361_cp_final_state value = var:zg361_case_r_state }
	set_variable = { name = zg361_cp_final_capacity_available value = var:zg361_cp_capacity_available }
	set_variable = { name = zg361_cp_final_capacity_spent value = var:zg361_cp_capacity_spent }
	set_variable = { name = zg361_cp_final_share_total value = var:zg361_cp_claimed_share_total }
	set_variable = { name = zg361_cp_final_capacity_check value = { value = var:zg361_cp_capacity_available add = var:zg361_cp_capacity_spent } }
	set_variable = { name = zg361_cp_final_deferred_capacity_check value = { value = var:zg361_cp_capacity_available add = var:zg361_cp_capacity_spent add = var:zg361_cp_capacity_remaining } }
	set_variable = { name = zg361_cp_final_attention_check value = { value = var:zg361_cp_attention_free add = var:zg361_cp_attention_used } }
	set_variable = { name = zg361_cp_final_promotion_check value = { value = var:zg361_cp_promotion_slot_free add = var:zg361_cp_promotion_slot_used } }
	set_variable = { name = zg361_cp_final_conservation_ok value = 0 }
	set_variable = { name = zg361_cp_final_deferred value = 0 }
	if = {
		limit = {
			var:zg361_cp_portfolio_deferred = 1
			var:zg361_cp_final_deferred_capacity_check = 100
			var:zg361_cp_final_attention_check = 2
			var:zg361_cp_final_promotion_check = 1
			OR = {
				var:zg361_cp_project_slot_used = 0
				var:zg361_cp_project_slot_used = 1
			}
		}
		set_variable = { name = zg361_cp_final_deferred value = 1 }
		set_variable = { name = zg361_cp_final_conservation_ok value = 1 }
	}
	else_if = {
		limit = {
			var:zg361_cp_portfolio_deferred = 0
			var:zg361_cp_final_capacity_check = 100
			var:zg361_cp_final_attention_check = 2
			var:zg361_cp_final_promotion_check = 1
			var:zg361_cp_final_share_total = 10000
			var:zg361_cp_project_slot_used = 0
			var:zg361_cp_project_object_version = 27
			OR = {
				var:zg361_cp_project_object_status = 2
				var:zg361_cp_project_object_status = 3
			}
			var:zg361_cp_report_object_version = 7
		}
		set_variable = { name = zg361_cp_final_conservation_ok value = 1 }
	}
	debug_log = "ZG361CP: credit/project portfolio closed static runtime"
}'''


def render_effects() -> bytes:
    """Render the pre-sharding logical stream for byte-for-byte regression tests.

    This payload is deliberately not emitted. Keeping the canonical stream in
    memory lets tests prove sharding changes only file boundaries, not any
    top-level effect body or its order.
    """

    validate_specs()
    sections = [
        "# ZhongGuo 361 E/I/J/R credit and project runtime.\n"
        f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n"
        "# Public entry: zg361_cp_open_portfolio_effect = { SUBJECT = <direct vassal> }.\n"
        "# Stable status: 1=applied, 2=idempotent no-op, 3=stale no-op, 4=typed RED.",
        render_portfolio_entries(),
        render_pending_player_event_effects(),
    ]
    sections.extend(render_due_debt_consumer(spec) for spec in MECHANISMS)
    sections.append(render_due_debt_aggregate())
    for domain in ("e", "i", "j", "r"):
        sections += [render_domain_init(domain), render_subject_read(domain), render_ai(domain), render_launch(domain)]
    for spec in MECHANISMS:
        sections.append(render_consumer(spec))
        for choice in (1, 2, 3):
            sections.append(render_route(spec, choice))
    return generated("\n\n".join(sections))


def effect_shard_sections() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Partition the logical effect stream into small purpose-owned files."""

    validate_specs()
    shards: list[tuple[str, str, tuple[str, ...]]] = [
        (
            "zg361_credit_project_portfolio_lifecycle_effects.txt",
            "portfolio lifecycle and public entry",
            (render_portfolio_entries(), render_pending_player_event_effects()),
        ),
    ]
    for domain in ("e", "i", "j", "r"):
        debt_sections = tuple(
            render_due_debt_consumer(spec)
            for spec in MECHANISMS
            if spec.domain == domain
        )
        if domain == "r":
            debt_sections += (render_due_debt_aggregate(),)
        shards.append(
            (
                f"zg361_credit_project_{domain}_policy_debt_effects.txt",
                f"domain {domain.upper()} deferred-policy debt settlement",
                debt_sections,
            )
        )
    for domain in ("e", "i", "j", "r"):
        shards.append(
            (
                f"zg361_credit_project_{domain}_orchestration_effects.txt",
                f"domain {domain.upper()} initialization, read, AI and launch adapters",
                (
                    render_domain_init(domain),
                    render_subject_read(domain),
                    render_ai(domain),
                    render_launch(domain),
                ),
            )
        )
    for spec in MECHANISMS:
        shards.append(
            (
                effect_filename_for(spec),
                f"mechanism {spec.mid:03d} {spec.field} consumer and routes",
                (
                    render_consumer(spec),
                    *(render_route(spec, choice) for choice in (1, 2, 3)),
                ),
            )
        )
    return tuple(shards)


def render_effect_shards() -> dict[Path, bytes]:
    rendered: dict[Path, bytes] = {}
    for filename, purpose, sections in effect_shard_sections():
        preamble = (
            "# ZhongGuo 361 E/I/J/R credit and project runtime.\n"
            f"# PURPOSE: {purpose}.\n"
            f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed."
        )
        rendered[MOD_ROOT / EFFECTS_DIR / filename] = generated(
            "\n\n".join((preamble, *sections))
        )
    return rendered


def effect_output_paths() -> tuple[Path, ...]:
    return tuple(render_effect_shards())


def legacy_effect_path() -> Path:
    return MOD_ROOT / EFFECTS_DIR / LEGACY_EFFECT_FILENAME


def event_guard(spec: Mechanism) -> str:
    d = spec.domain
    return f"""is_ai = no
exists = scope:zg361_cp_{d}_owner
exists = scope:zg361_cp_{d}_subject
exists = scope:zg361_cp_{d}_cycle
exists = scope:zg361_cp_{d}_case
this = scope:zg361_cp_{d}_owner
zg361_is_celestial_liege_trigger = yes
scope:zg361_cp_{d}_subject = {{
\tzg361_case_kernel_full_guard_trigger = {{
\t\tOWNER_VAR = zg361_case_{d}_owner
\t\tSUBJECT_VAR = zg361_case_{d}_subject
\t\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\t\tCASE_VAR = zg361_case_{d}_case_serial
\t\tSTATE_VAR = zg361_case_{d}_state
\t\tACTIVE_VAR = zg361_case_{d}_active
\t\tEXPECTED_OWNER = scope:zg361_cp_{d}_owner
\t\tEXPECTED_SUBJECT = scope:zg361_cp_{d}_subject
\t\tEXPECTED_CYCLE = scope:zg361_cp_{d}_cycle
\t\tEXPECTED_CASE = scope:zg361_cp_{d}_case
\t\tEXPECTED_STATE = {spec.state}
\t}}
}}"""


def render_option(spec: Mechanism, choice: int, next_mid: int | None) -> str:
    d, mid = spec.domain, spec.mid
    letter = "abc"[choice - 1]
    next_event = ""
    if next_mid is not None:
        next_event_id = player_event_id(next_mid)
        next_event = f"""
\tif = {{
\t\tlimit = {{
\t\t\tscope:zg361_cp_{d}_subject = {{
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{ has_variable = zg361_cp_runtime_applied }}
\t\t\t\t\tvar:zg361_cp_runtime_applied = 1
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t}}
\t\t}}
\t\tscope:zg361_cp_{d}_subject = {{ set_variable = {{ name = zg361_cp_pending_player_event value = {next_event_id} }} }}
\t\ttrigger_event = {{ id = zg361cp.{next_event_id} days = 1 }}
\t}}"""
    option_trigger = ""
    business_checks: list[str] = []
    if choice in (1, 2):
        # Once any control-plane defer is chosen, later A/B business routes
        # normally remain unavailable because prerequisite objects may not
        # exist. Mode C is narrower: it closes only the eleven frozen low-risk
        # items, so each retained high-value card still exposes its original
        # A/B decisions and lets their unchanged preflight accept or reject it.
        if spec.mid in RETAINED_POPUP_IDS:
            business_checks += [
                "trigger_if = {",
                "\tlimit = { has_variable = zg361_cp_portfolio_deferred }",
                "\tOR = {",
                "\t\tvar:zg361_cp_portfolio_deferred = 0",
                "\t\tAND = {",
                "\t\t\thas_variable = zg361_cp_player_batch_mode",
                "\t\t\tvar:zg361_cp_player_batch_mode = 3",
                "\t\t}",
                "\t}",
                "}",
                "trigger_else = { always = no }",
            ]
        else:
            business_checks += [
                "trigger_if = {",
                "\tlimit = { has_variable = zg361_cp_portfolio_deferred }",
                "\tvar:zg361_cp_portfolio_deferred = 0",
                "}",
                "trigger_else = { always = no }",
            ]
    if spec.mid == 54 and choice in (1, 2):
        policy_hours = (1, 4, 1)[choice - 1]
        business_checks += [
            "trigger_if = {",
            "\tlimit = { has_variable = zg361_cp_report_policy has_variable = zg361_cp_report_policy_hours }",
            f"\tvar:zg361_cp_report_policy = {choice}",
            f"\tvar:zg361_cp_report_policy_hours = {policy_hours}",
            "}",
            "trigger_else = { always = no }",
        ]
    elif spec.mid == 64 and choice == 1:
        business_checks += [
            "trigger_if = {",
            "\tlimit = { has_variable = zg361_cp_successor_valid }",
            "\tvar:zg361_cp_successor_valid = 1",
            "}",
            "trigger_else = { always = no }",
        ]
    if business_checks:
        option_trigger = f"""
\ttrigger = {{
\t\tscope:zg361_cp_{d}_subject = {{
{indent(chr(10).join(business_checks), 3)}
\t\t}}
\t}}"""
    tooltip = f"\n\tcustom_tooltip = zg361cp.{mid}.c.tt" if choice == 3 else ""
    return f"""option = {{
\tname = zg361cp.{mid}.{letter}{tooltip}
{option_trigger}
\tscope:zg361_cp_{d}_subject = {{
\t\tzg361_cp_m{mid}_route_{letter}_effect = {{
\t\t\tTICKET_OWNER = scope:zg361_cp_{d}_owner
\t\t\tTICKET_SUBJECT = scope:zg361_cp_{d}_subject
\t\t\tTICKET_CYCLE = scope:zg361_cp_{d}_cycle
\t\t\tTICKET_CASE = scope:zg361_cp_{d}_case
\t\t}}
\t}}{next_event}
}}"""


def render_batch_mode_option(letter: str, mode: int) -> str:
    tooltip = "\n\tcustom_tooltip = zg361cp.batch.c.tt" if mode == 3 else ""
    return f"""option = {{
\tname = zg361cp.batch.{letter}{tooltip}
\tscope:zg361_cp_e_subject = {{
\t\tset_variable = {{ name = zg361_cp_player_batch_mode value = {mode} }}
\t\tset_variable = {{ name = zg361_cp_pending_player_event value = {DOMAIN_ORDER['e'][0]} }}
\t}}
\ttrigger_event = {{ id = zg361cp.{DOMAIN_ORDER['e'][0]} days = 1 }}
}}"""


def render_batch_mode_event() -> str:
    spec = by_id()[DOMAIN_ORDER["e"][0]]
    options = "\n".join(
        render_batch_mode_option(letter, mode)
        for letter, mode in zip("abcd", (1, 2, 3, 4))
    )
    return f"""# One player choice freezes how the eleven low-risk cards are handled.
zg361cp.{BATCH_MODE_EVENT} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = zg361cp.batch.t
\tdesc = zg361cp.batch.desc
\ttrigger = {{
{indent(event_guard(spec), 2)}
\t}}
\timmediate = {{
\t\tscope:zg361_cp_e_subject = {{
\t\t\tzg361_cp_clear_pending_player_event_effect = {{ EVENT = {BATCH_MODE_EVENT} }}
\t\t}}
\t}}
{indent(options)}
}}"""


def render_batch_route_call(spec: Mechanism, choice: int) -> str:
    letter = "abc"[choice - 1]
    d, mid = spec.domain, spec.mid
    return f"""scope:zg361_cp_{d}_subject = {{
\tzg361_cp_m{mid}_route_{letter}_effect = {{
\t\tTICKET_OWNER = scope:zg361_cp_{d}_owner
\t\tTICKET_SUBJECT = scope:zg361_cp_{d}_subject
\t\tTICKET_CYCLE = scope:zg361_cp_{d}_cycle
\t\tTICKET_CASE = scope:zg361_cp_{d}_case
\t}}
}}"""


def render_batch_dispatch_event(spec: Mechanism, next_mid: int | None) -> str:
    """Render one fail-open dispatcher around the unchanged route cores.

    The dispatcher never guesses around a failed tuple/resource preflight.  It
    calls the exact original event whenever the chosen core does not produce
    ``runtime_applied = 1``; mode D and a missing/invalid mode do the same.
    """

    d, mid = spec.domain, spec.mid
    route_branches = "\n".join(
        (
            ("if" if choice == 1 else "else_if")
            + f" = {{\n\tlimit = {{ scope:zg361_cp_{d}_subject = {{ var:zg361_cp_player_batch_mode = {choice} }} }}\n"
            + indent(render_batch_route_call(spec, choice))
            + "\n}"
        )
        for choice in (1, 2, 3)
    )
    applied_guard = f"""scope:zg361_cp_{d}_subject = {{
\ttrigger_if = {{
\t\tlimit = {{ has_variable = zg361_cp_runtime_applied }}
\t\tvar:zg361_cp_runtime_applied = 1
\t}}
\ttrigger_else = {{ always = no }}
}}"""
    if next_mid is not None:
        outcome = f"""if = {{
\tlimit = {{
{indent(applied_guard, 2)}
\t}}
\tscope:zg361_cp_{d}_subject = {{ set_variable = {{ name = zg361_cp_pending_player_event value = {player_event_id(next_mid)} }} }}
\ttrigger_event = {{ id = zg361cp.{player_event_id(next_mid)} days = 1 }}
}}
else = {{ trigger_event = {{ id = zg361cp.{mid} }} }}"""
    else:
        outcome = f"""if = {{
\tlimit = {{
\t\tNOT = {{
{indent(applied_guard, 3)}
\t\t}}
\t}}
\ttrigger_event = {{ id = zg361cp.{mid} }}
}}"""
    return f"""# #{mid:03d} hidden portfolio-mode dispatcher; every failure restores the original card.
zg361cp.{player_event_id(mid)} = {{
\ttype = character_event
\thidden = yes
\ttrigger = {{ is_ai = no }}
\timmediate = {{
\t\tif = {{
\t\t\tlimit = {{
{indent(event_guard(spec), 4)}
\t\t\t\tscope:zg361_cp_{d}_subject = {{
\t\t\t\t\thas_variable = zg361_cp_player_batch_mode
\t\t\t\t\tvar:zg361_cp_player_batch_mode >= 1
\t\t\t\t\tvar:zg361_cp_player_batch_mode <= 3
\t\t\t\t}}
\t\t\t}}
\t\t\tscope:zg361_cp_{d}_subject = {{
\t\t\t\tzg361_cp_clear_pending_player_event_effect = {{ EVENT = {player_event_id(mid)} }}
\t\t\t}}
{indent(route_branches, 3)}
{indent(outcome, 3)}
\t\t}}
\t\telse = {{ trigger_event = {{ id = zg361cp.{mid} }} }}
\t}}
}}"""


def render_queue_event(domain: str) -> str:
    next_domain = NEXT_DOMAIN[domain]
    if next_domain is None:
        raise ValueError("the final R domain has no queue event")
    event_id = QUEUE_EVENTS[domain]
    final_state = max(STAGE_LAST[domain].values()) + 1
    return f"""# D+1 hidden queue edge: {domain.upper()} closed -> {next_domain.upper()} opens.
zg361cp.{event_id} = {{
\ttype = character_event
\thidden = yes
\ttrigger = {{
\t\texists = scope:zg361_cp_{domain}_owner
\t\texists = scope:zg361_cp_{domain}_subject
\t\texists = scope:zg361_cp_{domain}_cycle
\t\texists = scope:zg361_cp_{domain}_case
\t\tthis = scope:zg361_cp_{domain}_owner
\t\tzg361_is_celestial_liege_trigger = yes
\t\tscope:zg361_cp_{domain}_subject = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
\t\t\t\t\thas_variable = zg361_case_{domain}_owner
\t\t\t\t\thas_variable = zg361_case_{domain}_subject
\t\t\t\t\thas_variable = zg361_case_{domain}_cycle_serial
\t\t\t\t\thas_variable = zg361_case_{domain}_case_serial
\t\t\t\t\thas_variable = zg361_case_{domain}_state
\t\t\t\t\thas_variable = zg361_case_{domain}_active
\t\t\t\t}}
\t\t\t\tvar:zg361_case_{domain}_owner = scope:zg361_cp_{domain}_owner
\t\t\t\tvar:zg361_case_{domain}_subject = scope:zg361_cp_{domain}_subject
\t\t\t\tvar:zg361_case_{domain}_cycle_serial = scope:zg361_cp_{domain}_cycle
\t\t\t\tvar:zg361_case_{domain}_case_serial = scope:zg361_cp_{domain}_case
\t\t\t\tvar:zg361_case_{domain}_state = {final_state}
\t\t\t\tvar:zg361_case_{domain}_active = 0
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
\t}}
\timmediate = {{
\t\tscope:zg361_cp_{domain}_subject = {{
\t\t\tzg361_cp_clear_pending_player_event_effect = {{ EVENT = {event_id} }}
\t\t\tzg361_cp_{next_domain}_launch_effect = yes
\t\t}}
\t}}
}}"""


def render_case_event(spec: Mechanism, next_mid: int | None) -> str:
    mid = spec.mid
    options = "\n".join(render_option(spec, choice, next_mid) for choice in (1, 2, 3))
    return f"""# #{mid:03d} — {spec.title_en}
zg361cp.{mid} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = zg361cp.{mid}.t
\tdesc = zg361cp.{mid}.desc
\ttrigger = {{
{indent(event_guard(spec), 2)}
\t}}
\timmediate = {{
\t\tscope:zg361_cp_{spec.domain}_subject = {{
\t\t\tzg361_cp_clear_pending_player_event_effect = {{ EVENT = {mid} }}
\t\t}}
\t}}
{indent(options)}
}}"""


def event_shard_sections() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Keep each event file purpose-specific and below ten event blocks."""

    specs = by_id()
    shards: list[tuple[str, str, tuple[str, ...]]] = [
        (
            "zg361_credit_project_portfolio_events.txt",
            "portfolio mode entry and cross-domain D+1 queue edges",
            (
                render_batch_mode_event(),
                *(render_queue_event(domain) for domain in ("e", "i", "j")),
            ),
        )
    ]
    for domain, order in DOMAIN_ORDER.items():
        cases: list[str] = []
        dispatchers: list[str] = []
        for index, mid in enumerate(order):
            next_mid = order[index + 1] if index + 1 < len(order) else None
            spec = specs[mid]
            cases.append(render_case_event(spec, next_mid))
            if mid in BATCHABLE_IDS:
                dispatchers.append(render_batch_dispatch_event(spec, next_mid))
        shards.append(
            (
                f"zg361_credit_project_{domain}_case_events.txt",
                f"domain {domain.upper()} player case cards",
                tuple(cases),
            )
        )
        if dispatchers:
            shards.append(
                (
                    f"zg361_credit_project_{domain}_batch_events.txt",
                    f"domain {domain.upper()} hidden portfolio-mode dispatchers",
                    tuple(dispatchers),
                )
            )
    return tuple(shards)


def render_event_shards() -> dict[Path, bytes]:
    validate_specs()
    return {
        MOD_ROOT / EVENTS_DIR / filename: generated(
            f"# PURPOSE: {purpose}\nnamespace = zg361cp\n\n" + "\n\n".join(sections)
        )
        for filename, purpose, sections in event_shard_sections()
    }


def event_output_paths() -> tuple[Path, ...]:
    return tuple(render_event_shards())


def legacy_event_path() -> Path:
    return MOD_ROOT / EVENTS_DIR / LEGACY_EVENT_FILENAME


def render_events() -> bytes:
    """Render a test-only aggregate; release output always uses event shards."""

    sections = [section for _filename, _purpose, shard in event_shard_sections() for section in shard]
    return generated("namespace = zg361cp\n\n" + "\n\n".join(sections))


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


BATCH_COPY_CN = {
    "t": "本轮办案方式",
    "desc": "本轮项目案卷已经归集：[zg361_cp_e_subject.GetShortUIName]是当事人，[zg361_cp_e_owner.GetShortUIName]将作裁决。其中十一项属于常规登记，其余十六项涉及付款、回应、期限、去留或结算，仍须逐案审理。当前未清制度债为[zg361_cp_e_subject.MakeScope.Var('zg361_cp_policy_debt_open_n').GetValue|0]笔。",
    "a": "证据优先统一办理十一案；条件不足则逐案呈报。",
    "b": "速度优先统一办理十一案；条件不足则逐案呈报。",
    "c": "关闭十一项常规案，各记一笔制度债。",
    "d": "保留全部二十七项案卷，逐项裁决。",
    "c.tt": "实际新增数严格等于本次真正关闭的常规案数，每案至多记一笔；已经办结的案卷不会重复记账。涉及付款、回应、期限、去留或结算的其余十六项仍会逐案呈报，另行裁决。",
}
BATCH_COPY_EN = {
    "t": "Method for This Portfolio",
    "desc": "This project portfolio is assembled: [zg361_cp_e_subject.GetShortUIName] is the subject, and [zg361_cp_e_owner.GetShortUIName] will decide it. Eleven entries are routine records; the other sixteen involve payment, response, deadlines, personnel disposition, or settlement and still require individual judgment. Existing unresolved policy debt: [zg361_cp_e_subject.MakeScope.Var('zg361_cp_policy_debt_open_n').GetValue|0].",
    "a": "Resolve eleven routine cases by evidence; present any failed preflight separately.",
    "b": "Resolve eleven routine cases for speed; present any failed preflight separately.",
    "c": "Close eleven routine cases and record one policy debt for each.",
    "d": "Keep all twenty-seven case records and decide each one.",
    "c.tt": "The number added equals the routine cases actually closed, at no more than one debt per case; an already resolved case is never recorded twice. The other sixteen cases involving payment, response, deadlines, personnel disposition, or settlement still arrive for individual judgment.",
}


def render_localization(language: str) -> bytes:
    validate_specs()
    chinese = language == "simp_chinese"
    batch_copy = BATCH_COPY_CN if chinese else BATCH_COPY_EN
    rows: list[str] = [
        f' zg361cp.batch.{key}:0 "{esc(value)}"'
        for key, value in batch_copy.items()
    ]
    for spec in MECHANISMS:
        title = spec.title_cn if chinese else spec.title_en
        desc = spec.desc_cn if chinese else spec.desc_en
        routes = spec.routes_cn if chinese else spec.routes_en
        rows += [
            f' zg361cp.{spec.mid}.t:0 "{esc(title)}"',
            f' zg361cp.{spec.mid}.desc:0 "{esc(desc)}"',
            *(f' zg361cp.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", routes)),
            f' zg361cp.{spec.mid}.c.tt:0 "{esc(DEFER_TOOLTIP_CN if chinese else DEFER_TOOLTIP_EN)}"',
        ]
    if chinese:
        rows = normalize_localization_rows(rows)
    return localized(f"l_{language}:\n" + "\n".join(rows))


def outputs() -> dict[Path, bytes]:
    rendered = {
        **render_effect_shards(),
        **render_event_shards(),
    }
    for language in LANGUAGES:
        rendered[MOD_ROOT / "localization" / language / f"zg361_credit_project_l_{language}.yml"] = render_localization(language)
    return rendered


def sync_outputs(*, check: bool) -> list[Path]:
    """Check or materialize outputs while refusing the retired monolith."""

    rendered = outputs()
    drift: list[Path] = []
    for path, payload in rendered.items():
        if check:
            if not path.exists() or path.read_bytes() != payload:
                drift.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    for legacy in (legacy_effect_path(), legacy_event_path()):
        if legacy.exists():
            if check:
                drift.append(legacy)
            else:
                legacy.unlink()
    return drift


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    drift = sync_outputs(check=args.check)
    if args.check:
        if drift:
            for path in drift:
                print(f"DRIFT: {path.relative_to(MOD_ROOT)}")
            return 1
        print("GREEN: credit/project generated outputs are current")
    else:
        print(f"WROTE: {len(outputs())} credit/project runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
