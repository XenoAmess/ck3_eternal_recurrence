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


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_credit_project_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
DEFER_ROUTE_EN = "Defer this mechanism and open one next-cycle policy debt."
DEFER_ROUTE_CN = "延期本机制，并登记一笔下周期制度债。"
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
      "Delivery, reporting and relationship hours spend the same finite project capacity, but only delivery creates hard output.",
      "交付、汇报与关系工时花的是同一份项目容量，只有交付工时会生成真实产出。",
      "Protect delivery and keep reporting lean.", "Balance delivery with a fuller account.", "Spend heavily on visibility and record the displaced output.",
      "保护交付，只做精简汇报。", "交付与完整汇报并重。", "重押可见度，并如实记录被挤掉的产出。"),
    m(27, "e", 2, "signed_contribution", "Sign One Hundred Percent of the Credit", "把百分之百贡献签清楚",
      "The subject, direct manager and cross-department contributor must sign a complete ten-thousand-basis-point allocation.",
      "受评者、直属上司与跨部门贡献者必须把一万基点完整签清。",
      "Give the subject the clear majority.", "Use a balanced cross-functional split.", "Give management and coordination more weight.",
      "让受评者取得明确多数。", "采用均衡的跨部门分配。", "提高管理与协调贡献的权重。"),
    m(28, "e", 3, "credit_claim", "Credit Claim and Audit Reversal", "抢功申诉与审计回拨",
      "A credit transfer must be net zero, and a rejected grab must be reversed without rewriting the signed baseline.",
      "功劳转移必须净额为零；抢功不成立时必须完整回拨，不能改写签字底稿。",
      "Uphold a bounded manager claim.", "Reverse the grab after evidence review.", "Reject the unsupported claim without transfer.",
      "支持一笔有界的上司主张。", "审证后完整回拨抢功。", "驳回无证据主张，不发生转移。"),
    m(29, "e", 4, "metric_audit", "Metric Packaging and Audit", "指标包装与审计",
      "Short-term KPI gain, delayed cost and fraud clawback settle as separate traceable entries.",
      "短期指标收益、延迟成本与造假回拨必须分账结算并可追溯。",
      "Record a genuine improvement.", "Record gaming and its delayed cost.", "Record fraud and claw the gain back.",
      "记录真实改善。", "记录指标博弈及其延迟成本。", "记录造假并追回全部短期收益。"),
    m(30, "e", 1, "resource_race", "One Project Wins the Capacity Race", "资源赛马只产生一个赢家",
      "One bounded project slot and a finite capacity book must be reserved before anyone spends project hours.",
      "开工前必须从唯一项目席位和有限容量账本中真实预留资源。",
      "Fund a forty-hour subject-led project.", "Fund a sixty-hour cross-functional project.", "Fund an eighty-hour manager-led commitment.",
      "给受评者主导的项目四十小时。", "给跨部门项目六十小时。", "给上司主导的承诺项目八十小时。"),
    m(31, "e", 2, "sponsor_credit", "Sponsor Credit Has a Cap and Expiry", "恩主信用有上限也会到期",
      "Sponsor visibility is temporary, bounded and cannot manufacture hard output.",
      "恩主带来的可见度必须临时、有界，也不能凭空制造真实产出。",
      "Grant a small transparent introduction.", "Spend a bounded sponsor balance.", "Decline sponsor credit and rely on evidence.",
      "给予一次透明的小额引荐。", "动用一笔有界恩主信用。", "不用恩主信用，只靠证据。"),
    m(54, "i", 1, "report_build", "Reporting Consumes Delivery Capacity", "汇报会挤占交付容量",
      "Building the packet spends real hours from the project without creating hard output.",
      "制作材料会真实消耗项目工时，却不会直接生成交付产出。",
      "Build the signed short fact sheet.", "Build the long narrative and pay four hours.", "Build an exception-only packet.",
      "制作签字短事实表。", "制作长叙事，并支付四小时。", "只制作异常事项材料。"),
    m(55, "i", 4, "attention_read", "Routing Is Not Reading", "送达不等于阅读",
      "A routed report becomes visible only when a manager spends one of two finite deep-read slots.",
      "材料送达后，只有上司实际消耗两个有限深读席位之一，才算真正看见。",
      "Spend one slot on the direct manager.", "Spend both slots on direct and skip-level readers.", "Route it without claiming that anyone read it.",
      "让直属上司消耗一个阅读席位。", "直属与越级上司各消耗一个席位。", "只完成路由，不声称有人阅读。"),
    m(56, "i", 2, "forwarded_credit", "Forward Without Quietly Taking Credit", "逐级上报不能悄悄截功",
      "Forwarded attribution starts from the signed contribution book and every transfer remains net zero.",
      "逐级上报必须从签字贡献底稿出发，任何转移都必须净额为零。",
      "Forward the signed shares unchanged.", "Transfer five hundred basis points to the manager.", "Add cross-department evidence and preserve the shares.",
      "原样转发签字份额。", "向上司转移五百基点。", "补充跨部门证据，但不改份额。"),
    m(57, "i", 2, "version_signature", "Freeze the Report Version", "冻结汇报版本签名",
      "Only a complete ten-thousand-basis-point attribution may receive the author's version signature.",
      "只有合计一万基点的完整归属表，才能取得作者的版本签名。",
      "Sign version one.", "Sign version two after evidence review.", "Sign version three with the cross-department appendix.",
      "签署第一版。", "审证后签署第二版。", "带跨部门附件签署第三版。"),
    m(58, "i", 3, "report_route", "Signed Material Before Routing", "先签字，再路由",
      "Direct and skip-level routing records recipients, but does not itself consume an attention slot.",
      "直属与越级路由只记录收件人，本身不会消耗阅读席位。",
      "Route to the direct manager only.", "Route to direct and skip-level managers.", "Route with a cross-department evidence copy.",
      "只送直属上司。", "同时送直属与越级上司。", "附跨部门证据副本后路由。"),
    m(59, "i", 3, "risk_timing", "Bad News Has a Timestamp", "坏消息必须有时间戳",
      "Early, delayed and hidden risk reports produce different remaining loss and integrity receipts.",
      "早报、迟报与隐瞒会产生不同的剩余损失和诚信收执。",
      "Report early and halve the remaining loss.", "Report late and retain the full loss.", "Hide it and double the loss.",
      "提前报告，把剩余损失减半。", "延迟报告，承担全部损失。", "继续隐瞒，让损失翻倍。"),
    m(60, "i", 4, "idea_arbitration", "The Signed Version Owns the Idea", "创意归属服从签字版本",
      "Idea theft is arbitrated against the frozen author signature and cross-department provenance.",
      "创意窃取争议以冻结作者签名和跨部门来源为裁判依据。",
      "Uphold the original author.", "Recognize a proven joint authorship.", "Reject the theft allegation for lack of matching provenance.",
      "支持原作者。", "认可证据充分的共同作者。", "来源不匹配，驳回窃取指控。"),
    m(61, "i", 1, "report_policy", "Choose the Reporting Regime First", "先定汇报制度",
      "Short facts, long narrative and exception-only reporting carry different capacity costs.",
      "短事实、长叙事与仅报异常三种制度，消耗的容量不同。",
      "Use short factual reports.", "Require long narrative reports.", "Report exceptions only.",
      "采用短事实汇报。", "要求长叙事汇报。", "只汇报异常。"),
    m(62, "j", 2, "matrix_conflict", "Two Lines, One Recorded Choice", "两条汇报线，只能留下一个选择",
      "Conflicting priorities must resolve by frozen weights, joint arbitration or an explicit integrity debt.",
      "目标冲突必须按冻结权重、联合仲裁或明确的诚信债处理。",
      "Follow the heavier solid-line weight.", "Use joint arbitration.", "Promise both and record integrity debt.",
      "服从权重更高的实线。", "提交联合仲裁。", "两边都答应，并记录诚信债。"),
    m(63, "j", 1, "matrix_weights", "Lock Solid and Dotted Weights", "锁定实线与虚线权重",
      "Two manager weights are frozen at cycle start and must total exactly one hundred.",
      "周期开始时冻结两名管理者的权重，合计必须正好一百。",
      "Use seventy-thirty toward the solid line.", "Use equal weights.", "Use forty-sixty toward the dotted line.",
      "实线七成、虚线三成。", "双方各半。", "实线四成、虚线六成。"),
    m(64, "j", 3, "manager_handoff", "A Manager Handoff Needs Two Signatures", "换老板必须双签",
      "Only old and new managers together may move future responsibility; historical case ownership never moves.",
      "只有新旧上司共同签字才能转移未来责任；历史案卷 owner 永远不动。",
      "Collect both signatures and finalize.", "Record only the old manager's signature.", "Decline the handoff and keep the current manager.",
      "收齐双方签名并完成交接。", "只记录旧上司签名。", "拒绝交接，保留现任上司。"),
    m(65, "j", 2, "parachute_staffing", "An Airborne Manager Brings a Staff Pack", "空降主管与旧部包",
      "Imported staff reduce retained institutional memory and can trigger a favoritism audit.",
      "随空降主管带入的旧部会挤掉组织记忆，也可能触发任人唯亲审计。",
      "Import two of ten staff.", "Import three and trigger the audit threshold.", "Import six and expose severe memory loss.",
      "十人中带入两名旧部。", "带入三人并触发审计阈值。", "带入六人，暴露严重记忆流失。"),
    m(66, "j", 4, "strategic_cancel", "Business Cancellation Is Not Personal Failure", "业务取消不等于个人失败",
      "A strategic cancellation releases unspent capacity while preserving independently verified contribution.",
      "战略取消会释放未花容量，同时保留已独立验证的个人贡献。",
      "Cancel now and preserve verified credit.", "Approve a later cancellation without rewriting credit.", "Keep the project active and record the strategic review.",
      "立即取消，并保留已验证功劳。", "批准稍后取消，不改写个人功劳。", "项目继续，但留下战略复核记录。"),
    m(67, "j", 4, "duplicate_role", "Two Incumbents Need One Terminal Owner", "一岗两人最终只能有一个 owner",
      "Competition, retention or a bounded transition must end with exactly one accountable role owner.",
      "公开竞争、直接保留或有界过渡，最终都必须留下唯一责任人。",
      "Retain the assessed official.", "Retain the cross-department incumbent.", "Run a bounded transition and name one terminal owner.",
      "保留受评官员。", "保留跨部门现任者。", "完成有界过渡，并指定唯一终态 owner。"),
    m(68, "j", 4, "portable_history", "History Travels; Authorship Does Not", "履历可携带，历史作者不改写",
      "Ratings and an open PIP may travel as priors, but do not consume current quota or re-own old cases.",
      "评级与未结 PIP 可以作为先验携带，但不占本期名额，也不能改写旧案 owner。",
      "Carry one protected cycle and any open PIP.", "Carry ratings without the PIP.", "Keep history separate for local re-proof.",
      "携带一个保护周期及未结 PIP。", "只携带评级，不携带 PIP。", "历史独立保存，等待本地重新证明。"),
    m(129, "r", 2, "promotion_queue", "Promotion Is a Queue With Real Slots", "晋升是有真实槽位的队列",
      "FIFO eligibility and one bounded award slot prevent duplicate or out-of-order promotion.",
      "先进先出资格与一个有界授予槽，防止重复或插队晋升。",
      "Queue the subject for the next opening.", "Queue and allocate the one available slot.", "Defer with a signed eligibility expiry.",
      "把受评者排入下一空缺。", "入队并分配唯一可用槽位。", "签署资格到期日后延期。"),
    m(130, "r", 3, "talent_transfer", "Do Not Dump a Hidden PIP", "不能把隐藏 PIP 倾倒给别组",
      "Transfer provenance records PIP disclosure, role evidence, trial outcome and source-manager accountability.",
      "调动来源必须记录 PIP 披露、岗位证据、试用结果与原上司责任。",
      "Disclose the PIP and run a supported trial.", "Rescue a proven wrong-role placement.", "Hide the PIP; failed trial returns liability to the source manager.",
      "披露 PIP，并进行有支持的试用。", "以错岗证据完成岗位救援。", "隐瞒 PIP；试用失败后责任回到原上司。"),
    m(131, "r", 1, "project_track", "Exploration and Commitment Are Different Tracks", "探索项目与承诺项目分轨",
      "The project track and its success rule are frozen at registration, before results are known.",
      "项目类型和成功口径必须在登记时、结果未知前冻结。",
      "Register an exploration track.", "Register a commitment track.", "Register a bounded hybrid under commitment rules.",
      "登记为探索型项目。", "登记为承诺型项目。", "按承诺规则登记有界混合项目。"),
    m(132, "r", 4, "stop_loss", "A Timely Stop Can Earn Credit", "及时止损也可以算功",
      "A stop decision releases unspent capacity and keeps business outcome separate from individual judgement.",
      "止损会释放未花容量，并把业务结果与个人判断分账。",
      "Stop on strong evidence and grant timely-stop credit.", "Stop late and record named accountability.", "Stop without credit when the evidence is insufficient.",
      "证据充分时止损，并给予及时止损功劳。", "迟到止损，并记录具名责任。", "证据不足也先止损，但不授予止损功劳。"),
    m(133, "r", 5, "postmortem", "Learning and Liability Need Separate Tracks", "复盘学习与具名责任分轨",
      "System causes and learning actions are recorded without blanket punishment; proven violations remain named.",
      "系统原因与学习行动不触发连坐；证据成立的违规仍须具名。",
      "Record learning with no proven violation.", "Record system learning and one named violation.", "Record a control repair and manager liability.",
      "记录学习，不认定个人违规。", "记录系统学习及一项具名违规。", "记录控制修复与上司责任。"),
    m(134, "r", 2, "shared_metric_owner", "A Shared Metric Still Has One Owner", "共享指标仍然只有一个 owner",
      "Contributors and dependencies may be many, but settlement authority is assigned exactly once.",
      "贡献者和依赖方可以很多，但最终结算责任只能分配一次。",
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
EXPECTED_IDS = (
    set(range(26, 32))
    | set(range(54, 62))
    | set(range(62, 69))
    | set(range(129, 135))
)


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
        checks += ["has_variable = zg361_cp_signed_share_total", "var:zg361_cp_signed_share_total = 10000"]
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
            checks += ["has_variable = zg361_cp_report_signed", "var:zg361_cp_report_signed = 1"]
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
        ]
    elif mid == 27:
        shares = ((7000, 2000, 1000), (5000, 3000, 2000), (4000, 4000, 2000))[choice - 1]
        lines += [
            f"set_variable = {{ name = zg361_cp_signed_subject_bps value = {shares[0]} }}",
            f"set_variable = {{ name = zg361_cp_signed_manager_bps value = {shares[1]} }}",
            f"set_variable = {{ name = zg361_cp_signed_cross_bps value = {shares[2]} }}",
            "set_variable = { name = zg361_cp_signed_share_total value = 10000 }",
            f"set_variable = {{ name = zg361_cp_claimed_subject_bps value = {shares[0]} }}",
            f"set_variable = {{ name = zg361_cp_claimed_manager_bps value = {shares[1]} }}",
            f"set_variable = {{ name = zg361_cp_claimed_cross_bps value = {shares[2]} }}",
            "set_variable = { name = zg361_cp_claimed_share_total value = 10000 }",
            "set_variable = { name = zg361_cp_contribution_signer_subject value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_contribution_signer_manager value = $TICKET_OWNER$ }",
            "set_variable = { name = zg361_cp_contribution_signer_cross value = var:zg361_cp_cross_reviewer }",
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
            "set_variable = { name = zg361_cp_report_signer value = $TICKET_SUBJECT$ }",
            "set_variable = { name = zg361_cp_report_signature_case value = $TICKET_CASE$ }",
            "set_variable = { name = zg361_cp_report_signed value = 1 }",
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
            "set_variable = { name = zg361_cp_risk_version_case value = var:zg361_cp_report_signature_case }",
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
            "set_variable = { name = zg361_cp_idea_signature_used value = var:zg361_cp_report_signature_case }",
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
            f"set_variable = {{ name = zg361_cp_handoff_old_signed value = {1 if choice in (1, 2) else 0} }}",
            f"set_variable = {{ name = zg361_cp_handoff_new_signed value = {1 if choice == 1 else 0} }}",
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
        27: ["set_variable = { name = zg361_cp_visible_signed_share_total value = var:zg361_cp_signed_share_total }"],
        28: ["set_variable = { name = zg361_cp_visible_claimed_share_total value = var:zg361_cp_claimed_share_total }", "set_variable = { name = zg361_cp_visible_claim_delta_total value = var:zg361_cp_claim_transfer_total }", "set_variable = { name = zg361_cp_visible_audit_delta_total value = var:zg361_cp_claim_audit_total }"],
        29: ["set_variable = { name = zg361_cp_visible_metric_net value = var:zg361_cp_metric_net }", "if = { limit = { has_variable = zg361_kpi_value } change_variable = { name = zg361_kpi_value add = var:zg361_cp_metric_net } }"],
        30: ["set_variable = { name = zg361_cp_visible_capacity_reserved value = var:zg361_cp_capacity_reserved }", "set_variable = { name = zg361_cp_visible_resource_winners value = var:zg361_cp_resource_winner_n }"],
        31: ["set_variable = { name = zg361_cp_visible_sponsor_balance value = var:zg361_cp_sponsor_balance }", "set_variable = { name = zg361_cp_visible_sponsor_output value = var:zg361_cp_sponsor_hard_output }"],
        54: ["set_variable = { name = zg361_cp_visible_delivery_capacity value = var:zg361_cp_capacity_remaining }", "set_variable = { name = zg361_cp_visible_report_output value = var:zg361_cp_report_packet_hard_output }"],
        55: ["set_variable = { name = zg361_cp_visible_attention_used value = var:zg361_cp_attention_used }", "set_variable = { name = zg361_cp_visible_seen_count value = var:zg361_cp_report_seen_count }"],
        56: ["set_variable = { name = zg361_cp_visible_forward_total value = var:zg361_cp_report_share_total }"],
        57: ["set_variable = { name = zg361_cp_visible_signature_case value = var:zg361_cp_report_signature_case }"],
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
        f"set_variable = {{ name = {stem}_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }}",
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
        return f"""var:zg361_case_{domain}_owner = {{
\ttrigger_event = {{ id = zg361cp.{QUEUE_EVENTS[domain]} days = 1 }}
}}"""
    return "zg361_cp_finalize_portfolio_effect = yes"


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
\t\tsave_scope_value_as = {{ name = zg361_cp_{domain}_cycle value = var:zg361_case_{domain}_cycle_serial }}
\t\tsave_scope_value_as = {{ name = zg361_cp_{domain}_case value = var:zg361_case_{domain}_case_serial }}
\t\tif = {{
\t\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tzg361_cp_{domain}_run_authorized_ai_effect = yes
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ root = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tscope:zg361_cp_{domain}_owner = {{ trigger_event = {{ id = zg361cp.{first} }} }}
\t\t}}
\t}}
}}"""


def render_portfolio_entries() -> str:
    return r'''# Freeze portfolio actors and finite books exactly once, then execute E -> I -> J -> R.
zg361_cp_initialize_portfolio_effect = {
	save_scope_as = zg361_cp_portfolio_subject
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
			scope:zg361_cp_portfolio_subject = {
				set_variable = { name = zg361_cp_successor_manager value = scope:zg361_cp_successor_candidate }
				set_variable = { name = zg361_cp_successor_valid value = 1 }
				set_variable = { name = zg361_cp_cross_reviewer value = scope:zg361_cp_successor_candidate }
				set_variable = { name = zg361_cp_cross_reviewer_valid value = 1 }
			}
		}
		ordered_vassal = {
			limit = {
				zg361_is_reviewable_vassal_trigger = yes
				NOT = { this = scope:zg361_cp_portfolio_subject }
			}
			order_by = stewardship
			position = 0
			save_temporary_scope_as = zg361_cp_cross_candidate
			scope:zg361_cp_portfolio_subject = {
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
			root.var:zg361_review_serial = { value = var:zg361_cp_portfolio_cycle add = 1 }
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
    validate_specs()
    sections = [
        "# ZhongGuo 361 E/I/J/R credit and project runtime.\n"
        f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n"
        "# Public entry: zg361_cp_open_portfolio_effect = { SUBJECT = <direct vassal> }.\n"
        "# Stable status: 1=applied, 2=idempotent no-op, 3=stale no-op, 4=typed RED.",
        render_portfolio_entries(),
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
\t\ttrigger_event = {{ id = zg361cp.{next_mid} days = 1 }}
\t}}"""
    option_trigger = ""
    business_checks: list[str] = []
    if choice in (1, 2):
        # Once any control-plane defer is chosen, later A/B business routes
        # are unavailable because their prerequisite objects may deliberately
        # not exist.  C remains available and carries the case to closure.
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
    return f"""option = {{
\tname = zg361cp.{mid}.{letter}
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
\timmediate = {{ scope:zg361_cp_{domain}_subject = {{ zg361_cp_{next_domain}_launch_effect = yes }} }}
}}"""


def render_events() -> bytes:
    validate_specs()
    specs = by_id()
    events = ["namespace = zg361cp"]
    for domain in ("e", "i", "j", "r"):
        order = DOMAIN_ORDER[domain]
        for index, mid in enumerate(order):
            spec = specs[mid]
            next_mid = order[index + 1] if index + 1 < len(order) else None
            options = "\n".join(render_option(spec, choice, next_mid) for choice in (1, 2, 3))
            events.append(f"""# #{mid:03d} — {spec.title_en}
zg361cp.{mid} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = zg361cp.{mid}.t
\tdesc = zg361cp.{mid}.desc
\ttrigger = {{
{indent(event_guard(spec), 2)}
\t}}
{indent(options)}
}}""")
    events.extend(render_queue_event(domain) for domain in ("e", "i", "j"))
    return generated("\n\n".join(events))


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    validate_specs()
    chinese = language == "simp_chinese"
    rows: list[str] = []
    for spec in MECHANISMS:
        title = spec.title_cn if chinese else spec.title_en
        desc = spec.desc_cn if chinese else spec.desc_en
        routes = spec.routes_cn if chinese else spec.routes_en
        rows += [
            f' zg361cp.{spec.mid}.t:0 "{esc(title)}"',
            f' zg361cp.{spec.mid}.desc:0 "{esc(desc)}"',
            *(f' zg361cp.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", routes)),
        ]
    return localized(f"l_{language}:\n" + "\n".join(rows))


def outputs() -> dict[Path, bytes]:
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_credit_project_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_credit_project_runtime_events.txt": render_events(),
    }
    for language in LANGUAGES:
        rendered[MOD_ROOT / "localization" / language / f"zg361_credit_project_l_{language}.yml"] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    drift: list[Path] = []
    for path, payload in outputs().items():
        if args.check:
            if not path.exists() or path.read_bytes() != payload:
                drift.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
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
