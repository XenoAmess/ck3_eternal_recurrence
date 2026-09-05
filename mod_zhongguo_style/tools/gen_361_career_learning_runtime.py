#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the AH312-322 / AI323-333 career-learning CK3 runtime.

The package is intentionally isolated.  It exposes callable manager effects,
reuses the shared case kernel, queues bounded hidden deadlines, and emits one
batched player digest per completed domain.  It does not edit central wiring,
the scoreboard, GUI, B1/B2, or the already-owned manager/governance package.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, plan_effect_shards


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_career_learning_runtime.py\n"
EFFECTS_DIR = MOD_ROOT / "common/scripted_effects"
LEGACY_EFFECTS_PATH = EFFECTS_DIR / "zg361_career_learning_runtime_effects.txt"
EFFECT_SHARD_GLOB = "zg361_career_learning_*_effects.txt"
READINESS = "static-ready"


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: int
    domain: str
    state: int
    operation: str
    consumer: str
    title_en: str
    title_zh: str
    route_a_en: str
    route_a_zh: str
    route_b_en: str
    route_b_zh: str


def m(
    mechanism_id: int,
    domain: str,
    state: int,
    operation: str,
    title_en: str,
    title_zh: str,
    route_a_en: str,
    route_a_zh: str,
    route_b_en: str,
    route_b_zh: str,
) -> Mechanism:
    return Mechanism(
        mechanism_id,
        domain,
        state,
        operation,
        f"zg361_cl_m{mechanism_id:03d}_consumer_value",
        title_en,
        title_zh,
        route_a_en,
        route_a_zh,
        route_b_en,
        route_b_zh,
    )


MECHANISMS: tuple[Mechanism, ...] = (
    m(312, "ah", 1, "market.publish_real_vacancy", "A Vacancy That Exists", "这岗位真的存在", "Publish real HC and terms", "公开真实编制与条款", "Post a phantom vacancy", "挂一个空气岗位"),
    m(313, "ah", 1, "market.freeze_structured_reference", "The Reference Has Columns", "推荐信终于有列", "Freeze the complete record", "冻结完整履历", "Omit risk and whisper revenge", "隐去风险并顺手报复"),
    m(314, "ah", 2, "market.offer_relocation_package", "Relocation Is Not Exposure", "异地调任不能只发愿景", "Accept the funded package", "接受有钱的调任包", "Decline without a rating penalty", "拒绝且不背绩效锅"),
    m(315, "ah", 2, "market.run_bilateral_trial", "Ninety Days, Three Exit Doors", "九十天试岗，三方可退", "Complete a balanced trial", "完成权责对等试岗", "Return after a role mismatch", "岗位不合就原路返回"),
    m(316, "ah", 3, "market.freeze_pay_mapping", "Map Pay Before the Move", "转岗前先把钱说清", "Protect and phase the mapping", "保薪并分期映射", "Force an immediate cut", "立刻降档省预算"),
    m(317, "ah", 3, "market.project_stage_acl", "Your Application Is Not Team News", "你的申请不是团队早报", "Respect stage ACL", "遵守分阶段权限", "Leak it and retaliate", "提前泄露并秋后算账"),
    m(318, "ah", 2, "market.consume_application_slot", "Two Applications, Not Two Silences", "两次申请，不是两次石沉大海", "Use one formal slot", "使用一次正式申请", "Return a slot after manager timeout", "经理超时则返还名额"),
    m(319, "ah", 4, "market.counteroffer_then_release", "One Counteroffer, Then Let Go", "只许反 Offer 一次，然后放人", "Reject and release on time", "拒绝后按时放人", "Promise everything and deliver nothing", "全都答应，然后全不兑现"),
    m(320, "ah", 5, "market.aggregate_exit_voice", "Exit Voice Needs a Sample", "离职心声也要样本量", "Aggregate named and anonymous evidence", "聚合实名与匿名证据", "Reclassify the complaint away", "把投诉重新分类没"),
    m(321, "ah", 5, "market.maintain_alumni_relationship", "Alumni, With Consent", "前同事关系也要同意", "Maintain one consented contact", "维护一次经同意的联系", "Delete the contact card, keep the shame", "删掉联系人，黑历史还在"),
    m(322, "ah", 6, "market.open_returnee_case", "A Returnee Brings Old Receipts", "回流员工自带旧账", "Link old cases and new evidence", "回链旧案与新证据", "Attempt a clean-slate rewrite", "试图一键洗白历史"),
    m(323, "ai", 1, "learning.allocate_dual_budget", "Learning Has Two Budgets", "学习有两本预算", "Fund gold and protected hours", "同时拨金币与保护工时", "Buy certificates, reserve no time", "只买证书，不给时间"),
    m(324, "ai", 1, "learning.advance_three_stages", "Completed Is Not Applied", "结课不等于会用", "Prove completion, application, outcome", "证明结课、应用与结果", "Stop at the completion badge", "停在结课徽章"),
    m(325, "ai", 1, "learning.assess_practical_competence", "A Certificate Cannot Hold the Fort", "证书不能替你守城", "Use a valid practical test", "使用有效实操抽测", "Blame staff for a broken test", "题目失真还怪员工"),
    m(326, "ai", 2, "learning.settle_conference_adoption", "Conference Photos Are Not Adoption", "会议合影不算组织贡献", "Bring back an adopted playbook", "带回并落地一份打法", "Return with exposure only", "只带回行业曝光"),
    m(327, "ai", 2, "learning.attribute_teaching_impact", "Teaching Has a Capacity Bill", "内部授课也占产能", "Split impact after application", "应用后再分影响", "Count attendance as impact", "把到场人数当业务影响"),
    m(328, "ai", 3, "learning.settle_community_adoption", "A Community Needs Maintainers", "专业社区需要维护者", "Fund maintained shared artifacts", "维护并采用公共产物", "Publish and abandon", "发布即弃坑"),
    m(329, "ai", 3, "learning.match_cross_team_mentor", "One Mentee, One Active Mentor", "一名学员同时一个导师", "Match with paid capacity", "用明确产能完成匹配", "Rematch once without moving the deadline", "只换一次且不重置期限"),
    m(330, "ai", 4, "learning.settle_reskill_route", "Reskill or Hire, Pay Either Way", "转型培养或外招，都得付钱", "Reskill the existing official", "培养现有官员", "Hire outside and record fairness debt", "外招并记录公平债"),
    m(331, "ai", 4, "learning.borrow_protected_time", "Protected Time Is Not Decorative", "保护工时不是装饰品", "Borrow for a real crisis and repay", "真危机借用并按期补回", "Repay late and charge the manager", "逾期补回并扣经理分"),
    m(332, "ai", 5, "learning.run_safe_succession_drill", "The Drill Is Not the Disaster", "演练不是事故现场", "Run a successful safe simulation", "完成安全继任演练", "Expose a development gap", "暴露培养缺口"),
    m(333, "ai", 5, "learning.settle_training_commitment", "Training Debt Shrinks Monthly", "培训服务债按月递减", "Apply the skill and serve", "应用所学并履约", "Leave early and repay the remainder", "提前离开并返还余额"),
)

EXPECTED_IDS = tuple(range(312, 334))
SUBJECT_RESPONSE_IDS = frozenset({314, 315, 318, 319, 321, 333})
DUAL_COSTS: dict[int, tuple[int, int, frozenset[int]]] = {
    314: (15, 5, frozenset({1})),
    321: (4, 2, frozenset({1})),
    323: (8, 2, frozenset({1, 2})),
    326: (9, 3, frozenset({1, 2})),
    330: (15, 5, frozenset({1, 2})),
    # All three high-cost-training choices fund the same course.  Route C is
    # the deliberately unbound contract, not a free certificate loophole.
    333: (18, 6, frozenset({1, 2, 3})),
}

# Business deadlines created *after* a case-stage receipt.  These are not the
# stage scheduler above: they belong to the vacancy/offer/learning object and
# survive the case advancing.  One hidden event consumes each active object;
# the pending latch prevents a newer case from overwriting an unresolved one.
OBLIGATION_DAYS: dict[int, dict[int, int]] = {
    312: {1: 30, 2: 30, 3: 30},
    313: {1: 30, 2: 30, 3: 30},
    314: {1: 190, 3: 30},
    315: {1: 90, 2: 90, 3: 30},
    316: {1: 90, 3: 365},
    317: {2: 7, 3: 7},
    318: {2: 14, 3: 14},
    319: {1: 30, 2: 90, 3: 45},
    320: {1: 180, 2: 180, 3: 180},
    321: {1: 365, 3: 30},
    322: {1: 30, 2: 30, 3: 30},
    323: {1: 365, 2: 365, 3: 365},
    324: {1: 90, 2: 90, 3: 90},
    325: {1: 30, 2: 30, 3: 30},
    326: {1: 30, 2: 30, 3: 30},
    327: {1: 30, 2: 30, 3: 30},
    328: {1: 90, 2: 90, 3: 90},
    329: {1: 190, 2: 190, 3: 190},
    330: {1: 90, 2: 30, 3: 180},
    331: {1: 365, 2: 365, 3: 365},
    332: {1: 90, 2: 90, 3: 30},
    333: {1: 360, 2: 90},
}

# Stable numeric kind IDs keep the CK3 projection queryable without relying on
# localized strings.  The Python semantic authority owns the matching typed
# ObjectKind registry and asserts that every ID has one distinct consumer.
OBJECT_KINDS: dict[int, str] = {
    312: "vacancy",
    313: "reference",
    314: "transfer_offer",
    315: "trial_assignment",
    316: "pay_mapping",
    317: "application_acl",
    318: "application_quota",
    319: "release_obligation",
    320: "exit_signal",
    321: "alumni_relation",
    322: "returnee_case",
    323: "learning_budget",
    324: "learning_progress",
    325: "competence_assessment",
    326: "conference_adoption",
    327: "teaching_attribution",
    328: "community_artifact",
    329: "mentor_match",
    330: "reskill_case",
    331: "protected_time_loan",
    332: "succession_drill",
    333: "training_commitment",
}

RELATIONSHIP_IDS = frozenset({313, 314, 315, 317, 319, 321, 322, 327, 329, 330, 332, 333})
STAGES: dict[str, tuple[tuple[int, ...], ...]] = {
    "ah": ((312, 313), (314, 315, 318), (316, 317), (319,), (320, 321), (322,)),
    "ai": ((323, 324, 325), (326, 327), (328, 329), (330, 331), (332, 333)),
}
DELAYS: dict[str, tuple[int, ...]] = {
    "ah": (1, 90, 1, 30, 30, 90),
    "ai": (1, 30, 60, 90, 90),
}
LANGUAGES = (
    ("english", "l_english"),
    ("french", "l_french"),
    ("german", "l_german"),
    ("japanese", "l_japanese"),
    ("korean", "l_korean"),
    ("polish", "l_polish"),
    ("russian", "l_russian"),
    ("simp_chinese", "l_simp_chinese"),
    ("spanish", "l_spanish"),
)


def validate_data() -> None:
    if tuple(row.mechanism_id for row in MECHANISMS) != EXPECTED_IDS:
        raise ValueError("career/learning mechanism coverage drift")
    if len({row.operation for row in MECHANISMS}) != len(MECHANISMS):
        raise ValueError("operation names must be unique")
    flattened = tuple(item for domain in ("ah", "ai") for stage in STAGES[domain] for item in stage)
    if len(flattened) != len(EXPECTED_IDS) or set(flattened) != set(EXPECTED_IDS):
        raise ValueError(f"stage coverage drift: {flattened!r}")
    by_id = {row.mechanism_id: row for row in MECHANISMS}
    for domain, stages in STAGES.items():
        for state, ids in enumerate(stages, 1):
            for mechanism_id in ids:
                row = by_id[mechanism_id]
                if row.domain != domain or row.state != state:
                    raise ValueError(f"stage metadata drift for {mechanism_id}")
    if set(DUAL_COSTS) != {314, 321, 323, 326, 330, 333}:
        raise ValueError("dual-payer set drift")
    if set(OBLIGATION_DAYS) != set(EXPECTED_IDS):
        raise ValueError("every career/learning mechanism needs an obligation policy")
    for mechanism_id, routes in OBLIGATION_DAYS.items():
        if not routes or not set(routes) <= {1, 2, 3}:
            raise ValueError(f"invalid obligation routes for {mechanism_id}")
        if any(isinstance(days, bool) or days < 1 for days in routes.values()):
            raise ValueError(f"invalid obligation duration for {mechanism_id}")
    if set(OBJECT_KINDS) != set(EXPECTED_IDS):
        raise ValueError("object kind coverage drift")
    if len(set(OBJECT_KINDS.values())) != len(EXPECTED_IDS):
        raise ValueError("object kinds must be unique")
    if not RELATIONSHIP_IDS <= set(EXPECTED_IDS):
        raise ValueError("relationship mechanism coverage drift")
    if READINESS != "static-ready":
        raise ValueError("generator cannot claim live readiness")


def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def case_vars(domain: str) -> dict[str, str]:
    return {
        "owner": f"zg361_case_{domain}_owner",
        "subject": f"zg361_case_{domain}_subject",
        "cycle": f"zg361_case_{domain}_cycle_serial",
        "case": f"zg361_case_{domain}_case_serial",
        "state": f"zg361_case_{domain}_state",
        "revision": f"zg361_case_{domain}_revision",
        "active": f"zg361_case_{domain}_active",
        "timeline": f"zg361_case_{domain}_timeline_serial",
        "feedback": f"zg361_case_{domain}_feedback_revision",
        "last_operation": f"zg361_case_{domain}_last_operation",
        "last_choice": f"zg361_case_{domain}_last_choice",
    }


def kernel_guard(domain: str, state: int, *, ticket: bool = False) -> str:
    v = case_vars(domain)
    owner = "$TICKET_OWNER$" if ticket else f'var:{v["owner"]}'
    subject = "$TICKET_SUBJECT$" if ticket else "this"
    cycle = "$TICKET_CYCLE$" if ticket else f'var:{v["cycle"]}'
    case = "$TICKET_CASE$" if ticket else f'var:{v["case"]}'
    expected_state = "$TICKET_STATE$" if ticket else str(state)
    return f'''zg361_case_kernel_full_guard_trigger = {{
                OWNER_VAR = {v["owner"]}
                SUBJECT_VAR = {v["subject"]}
                CYCLE_VAR = {v["cycle"]}
                CASE_VAR = {v["case"]}
                STATE_VAR = {v["state"]}
                ACTIVE_VAR = {v["active"]}
                EXPECTED_OWNER = {owner}
                EXPECTED_SUBJECT = {subject}
                EXPECTED_CYCLE = {cycle}
                EXPECTED_CASE = {case}
                EXPECTED_STATE = {expected_state}
            }}'''


def receipt_current(row: Mechanism, *, indent: int = 0, ticket: bool = False) -> str:
    v = case_vars(row.domain)
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    owner = "$TICKET_OWNER$" if ticket else f'var:{v["owner"]}'
    subject = "$TICKET_SUBJECT$" if ticket else "this"
    cycle = "$TICKET_CYCLE$" if ticket else f'var:{v["cycle"]}'
    case = "$TICKET_CASE$" if ticket else f'var:{v["case"]}'
    state = "$TICKET_STATE$" if ticket else str(row.state)
    body = f'''zg361_case_kernel_receipt_is_current_trigger = {{
    RECEIPT_OWNER_VAR = {p}_receipt_owner
    RECEIPT_SUBJECT_VAR = {p}_receipt_subject
    RECEIPT_CYCLE_VAR = {p}_receipt_cycle
    RECEIPT_CASE_VAR = {p}_receipt_case
    RECEIPT_STATE_VAR = {p}_receipt_state
    RECEIPT_CHOICE_VAR = {p}_receipt_choice
    EXPECTED_OWNER = {owner}
    EXPECTED_SUBJECT = {subject}
    EXPECTED_CYCLE = {cycle}
    EXPECTED_CASE = {case}
    EXPECTED_STATE = {state}
    EXPECTED_CHOICE = var:{p}_receipt_choice
}}'''
    pad = "\t" * indent
    return "\n".join(pad + line if line else line for line in body.splitlines())


def object_receipt_current(row: Mechanism) -> str:
    """Validate an immutable receipt after the shared case has advanced."""

    p = f"zg361_cl_m{row.mechanism_id:03d}"
    return f'''zg361_case_kernel_receipt_is_current_trigger = {{
    RECEIPT_OWNER_VAR = {p}_receipt_owner
    RECEIPT_SUBJECT_VAR = {p}_receipt_subject
    RECEIPT_CYCLE_VAR = {p}_receipt_cycle
    RECEIPT_CASE_VAR = {p}_receipt_case
    RECEIPT_STATE_VAR = {p}_receipt_state
    RECEIPT_CHOICE_VAR = {p}_receipt_choice
    EXPECTED_OWNER = var:{p}_object_owner
    EXPECTED_SUBJECT = var:{p}_object_subject
    EXPECTED_CYCLE = var:{p}_object_cycle
    EXPECTED_CASE = var:{p}_object_case
    EXPECTED_STATE = {row.state}
    EXPECTED_CHOICE = var:{p}_object_route
}}'''


def record_operation(row: Mechanism) -> str:
    v = case_vars(row.domain)
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    return f'''zg361_case_kernel_record_operation_effect = {{
                OWNER_VAR = {v["owner"]}
                SUBJECT_VAR = {v["subject"]}
                CYCLE_VAR = {v["cycle"]}
                CASE_VAR = {v["case"]}
                STATE_VAR = {v["state"]}
                REVISION_VAR = {v["revision"]}
                ACTIVE_VAR = {v["active"]}
                TIMELINE_VAR = {v["timeline"]}
                FEEDBACK_VAR = {v["feedback"]}
                LAST_OPERATION_VAR = {v["last_operation"]}
                LAST_CHOICE_VAR = {v["last_choice"]}
                RECEIPT_OWNER_VAR = {p}_receipt_owner
                RECEIPT_SUBJECT_VAR = {p}_receipt_subject
                RECEIPT_CYCLE_VAR = {p}_receipt_cycle
                RECEIPT_CASE_VAR = {p}_receipt_case
                RECEIPT_STATE_VAR = {p}_receipt_state
                RECEIPT_CHOICE_VAR = {p}_receipt_choice
                TICKET_OWNER = $TICKET_OWNER$
                TICKET_SUBJECT = $TICKET_SUBJECT$
                TICKET_CYCLE = $TICKET_CYCLE$
                TICKET_CASE = $TICKET_CASE$
                TICKET_STATE = $TICKET_STATE$
                CHOICE = scope:zg361_cl_route
                OPERATION_ID = {row.mechanism_id}
            }}'''


def transaction_journal(row: Mechanism, kind: str, amount: int) -> str:
    v = case_vars(row.domain)
    p = f"zg361_cl_m{row.mechanism_id:03d}_{kind}"
    common = f'''OWNER_VAR = {v["owner"]}
                    SUBJECT_VAR = {v["subject"]}
                    CYCLE_VAR = {v["cycle"]}
                    CASE_VAR = {v["case"]}
                    STATE_VAR = {v["state"]}
                    REVISION_VAR = {v["revision"]}
                    ACTIVE_VAR = {v["active"]}
                    TICKET_OWNER = $TICKET_OWNER$
                    TICKET_SUBJECT = $TICKET_SUBJECT$
                    TICKET_CYCLE = $TICKET_CYCLE$
                    TICKET_CASE = $TICKET_CASE$
                    TICKET_STATE = $TICKET_STATE$'''
    return f'''set_variable = {{ name = {p}_available value = {amount} }}
            set_variable = {{ name = {p}_reserved value = 0 }}
            set_variable = {{ name = {p}_settled value = 0 }}
            set_variable = {{ name = {p}_status value = 0 }}
            zg361_case_kernel_reserve_transaction_effect = {{
                    {common}
                    AVAILABLE_VAR = {p}_available
                    RESERVED_VAR = {p}_reserved
                    RECEIPT_AMOUNT_VAR = {p}_amount
                    RECEIPT_STATUS_VAR = {p}_status
                    RECEIPT_OWNER_VAR = {p}_owner
                    RECEIPT_CYCLE_VAR = {p}_cycle
                    RECEIPT_CASE_VAR = {p}_case
                    AMOUNT = {amount}
            }}
            if = {{
                limit = {{ var:zg361_case_kernel_applied = 1 }}
                zg361_case_kernel_settle_transaction_effect = {{
                    {common}
                    RESERVED_VAR = {p}_reserved
                    SETTLED_VAR = {p}_settled
                    RECEIPT_AMOUNT_VAR = {p}_amount
                    RECEIPT_STATUS_VAR = {p}_status
                }}
            }}'''


def transaction_refund(row: Mechanism, kind: str) -> str:
    v = case_vars(row.domain)
    p = f"zg361_cl_m{row.mechanism_id:03d}_{kind}"
    return f'''if = {{
                limit = {{
                    OR = {{
                        var:{p}_status = 1
                        var:{p}_status = 2
                    }}
                }}
                zg361_case_kernel_refund_transaction_effect = {{
                    OWNER_VAR = {v["owner"]}
                    SUBJECT_VAR = {v["subject"]}
                    CYCLE_VAR = {v["cycle"]}
                    CASE_VAR = {v["case"]}
                    STATE_VAR = {v["state"]}
                    REVISION_VAR = {v["revision"]}
                    ACTIVE_VAR = {v["active"]}
                    TICKET_OWNER = $TICKET_OWNER$
                    TICKET_SUBJECT = $TICKET_SUBJECT$
                    TICKET_CYCLE = $TICKET_CYCLE$
                    TICKET_CASE = $TICKET_CASE$
                    TICKET_STATE = $TICKET_STATE$
                    AVAILABLE_VAR = {p}_available
                    RESERVED_VAR = {p}_reserved
                    SETTLED_VAR = {p}_settled
                    RECEIPT_AMOUNT_VAR = {p}_amount
                    RECEIPT_STATUS_VAR = {p}_status
                }}
            }}'''


def charged_route_trigger(routes: frozenset[int]) -> str:
    rows = "\n".join(f"                    scope:zg361_cl_route = {route}" for route in sorted(routes))
    return f"OR = {{\n{rows}\n                }}"


def render_dual_prepare(row: Mechanism) -> str:
    treasury, manager, routes = DUAL_COSTS[row.mechanism_id]
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    trigger = charged_route_trigger(routes)
    return f'''set_variable = {{ name = {p}_dual_payment_ready value = 0 }}
    if = {{
        limit = {{ {trigger} }}
        {transaction_journal(row, "treasury", treasury)}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {transaction_journal(row, "manager", manager)}
        }}
        if = {{
            limit = {{
                var:{p}_treasury_status = 2
                var:{p}_manager_status = 2
            }}
            set_variable = {{ name = {p}_dual_payment_ready value = 1 }}
        }}
        else = {{
            # No business receipt exists yet.  Undo either shadow journal so
            # a later retry sees a clean dual-payer transaction.
            {transaction_refund(row, "treasury")}
            {transaction_refund(row, "manager")}
        }}
    }}
    else = {{
        set_variable = {{ name = {p}_dual_payment_ready value = 1 }}
    }}'''


def render_dual_apply(row: Mechanism) -> str:
    treasury, manager, routes = DUAL_COSTS[row.mechanism_id]
    v = case_vars(row.domain)
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    trigger = charged_route_trigger(routes)
    return f'''if = {{
                limit = {{ {trigger} }}
                var:{v["owner"]} = {{
                    remove_treasury = {treasury}
                    remove_short_term_gold = {manager}
                }}
                set_variable = {{ name = {p}_dual_payment_settled value = 1 }}
                set_variable = {{ name = {p}_total_cost value = {treasury + manager} }}
                set_variable = {{ name = {p}_treasury_share value = {treasury} }}
                set_variable = {{ name = {p}_manager_share value = {manager} }}
            }}
            else = {{
                set_variable = {{ name = {p}_dual_payment_settled value = 0 }}
                set_variable = {{ name = {p}_total_cost value = 0 }}
            }}'''


def resource_precheck(row: Mechanism) -> str:
    if row.mechanism_id not in DUAL_COSTS:
        return "always = yes"
    treasury, manager, routes = DUAL_COSTS[row.mechanism_id]
    trigger = charged_route_trigger(routes)
    owner = case_vars(row.domain)["owner"]
    return f'''trigger_if = {{
                limit = {{ {trigger} }}
                var:{owner} = {{
                    government_has_flag = government_has_treasury
                    treasury >= {treasury}
                    gold >= {manager}
                }}
            }}
            trigger_else = {{ always = yes }}'''


def live_permission_trigger(row: Mechanism) -> str:
    owner = case_vars(row.domain)["owner"]
    return f'''var:{owner} = {{ zg361_is_celestial_liege_trigger = yes }}
            zg361_is_reviewable_vassal_trigger = yes
            OR = {{
                liege = var:{owner}
                AND = {{
                    # AH and AI cases open in parallel.  Once #319 really
                    # moves the subject, both frozen cases may finish only
                    # under this exact settled vacancy/title postcondition.
                    var:zg361_transfer_consumer_kind = 2
                    var:zg361_transfer_vacancy_status = 3
                    var:zg361_transfer_cl_phase = 6
                    var:zg361_transfer_cl_owner = var:{owner}
                    var:zg361_transfer_cl_subject = this
                    liege = var:zg361_transfer_cl_receiver
                    primary_title = var:zg361_transfer_cl_title
                    var:zg361_transfer_cl_title = {{ holder = this }}
                }}
            }}'''


def render_mobility_preaction(row: Mechanism) -> str:
    if row.mechanism_id not in {312, 314, 315, 319}:
        return ""
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    ticket = '''
                    TICKET_OWNER = $TICKET_OWNER$
                    TICKET_SUBJECT = $TICKET_SUBJECT$
                    TICKET_CYCLE = $TICKET_CYCLE$
                    TICKET_CASE = $TICKET_CASE$'''
    if row.mechanism_id == 312:
        action = f'''if = {{
                limit = {{ scope:zg361_cl_route = 1 }}
                zg361_career_hc_claim_cl_transfer_vacancy_effect = {{{ticket}
                }}
            }}
            else = {{ set_variable = {{ name = zg361_transfer_cl_applied value = 1 }} }}'''
    elif row.mechanism_id == 314:
        action = f'''if = {{
                limit = {{ scope:zg361_cl_route = 1 }}
                zg361_career_hc_accept_cl_transfer_effect = {{{ticket}
                }}
            }}
            else_if = {{
                limit = {{ scope:zg361_cl_route = 2 }}
                zg361_career_hc_decline_cl_transfer_effect = {{{ticket}
                }}
            }}
            else = {{ set_variable = {{ name = zg361_transfer_cl_applied value = 1 }} }}'''
    elif row.mechanism_id == 315:
        action = f'''if = {{
                limit = {{ scope:zg361_cl_route = 1 }}
                zg361_career_hc_start_cl_transfer_trial_effect = {{{ticket}
                }}
            }}
            else_if = {{
                limit = {{ scope:zg361_cl_route = 2 }}
                zg361_career_hc_decline_cl_transfer_effect = {{{ticket}
                }}
            }}
            else = {{ set_variable = {{ name = zg361_transfer_cl_applied value = 1 }} }}'''
    else:
        action = f'''if = {{
                limit = {{ scope:zg361_cl_route = 1 }}
                zg361_career_hc_authorize_cl_transfer_release_effect = {{{ticket}
                }}
            }}
            else_if = {{
                limit = {{ scope:zg361_cl_route = 2 }}
                zg361_career_hc_decline_cl_transfer_effect = {{{ticket}
                }}
            }}
            else = {{ set_variable = {{ name = zg361_transfer_cl_applied value = 1 }} }}'''
    return f'''set_variable = {{ name = {p}_mobility_policy_debt value = 0 }}
            remove_variable = zg361_transfer_cl_applied
            {action}
            if = {{
                limit = {{
                    trigger_if = {{
                        limit = {{ has_variable = zg361_transfer_cl_applied }}
                        NOT = {{ var:zg361_transfer_cl_applied = 1 }}
                    }}
                    trigger_else = {{ always = yes }}
                }}
                # A missing/stale vacancy, invalid receiver, war, or broken HC
                # reserve becomes an explicit policy debt.  No liege/title
                # mutation has occurred on these adapter RED paths.
                save_temporary_scope_value_as = {{ name = zg361_cl_route value = 3 }}
                set_variable = {{ name = {p}_mobility_policy_debt value = 1 }}
                set_variable = {{ name = {p}_mobility_red_code value = var:zg361_transfer_cl_red_code }}
            }}'''


def semantic_precheck(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    checks = [f'''trigger_if = {{
                    limit = {{ has_variable = {p}_obligation_pending }}
                    var:{p}_obligation_pending = 0
                }}
                trigger_else = {{ always = yes }}''']
    if row.mechanism_id == 331:
        owner = case_vars(row.domain)["owner"]
        checks.append(f'''trigger_if = {{
                    limit = {{
                        OR = {{
                            scope:zg361_cl_route = 1
                            scope:zg361_cl_route = 2
                        }}
                    }}
                    OR = {{
                        is_at_war = yes
                        var:{owner} = {{ is_at_war = yes }}
                    }}
                }}
                trigger_else = {{ always = yes }}''')
    body = "\n".join("                " + line if line else line for check in checks for line in check.splitlines())
    return f'''AND = {{
{body}
            }}'''


def payload(mechanism_id: int) -> str:
    p = f"zg361_cl_m{mechanism_id:03d}"
    payloads = {
        312: f'''set_variable = {{ name = {p}_legal_hc value = 1 }}
            set_variable = {{ name = {p}_vacancy_id value = var:zg361_transfer_cl_vacancy }}
            set_variable = {{ name = {p}_target_manager value = var:zg361_transfer_cl_receiver }}
            set_variable = {{ name = {p}_vacancy_title value = var:zg361_transfer_cl_title }}
            set_variable = {{ name = {p}_hc_reserved value = var:zg361_transfer_hc_reserved }}
            set_variable = {{ name = {p}_reporting_line_frozen value = 1 }}
            set_variable = {{ name = {p}_pay_band_frozen value = 4 }}
            set_variable = {{ name = {p}_goal_frozen value = 1 }}
            set_variable = {{ name = {p}_eligible_scope value = 2 }}
            set_variable = {{ name = {p}_vacancy_hire_limit value = 1 }}
            set_variable = {{ name = {p}_vacancy_filled_n value = 0 }}
            set_variable = {{ name = {p}_market_trust_delta value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_legal_hc value = 0 }} set_variable = {{ name = {p}_eligible_scope value = 1 }} set_variable = {{ name = {p}_market_trust_delta value = -2 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_market_trust_delta }}''',
        313: f'''set_variable = {{ name = {p}_achievements_frozen value = 1 }}
            set_variable = {{ name = {p}_risks_frozen value = 1 }}
            set_variable = {{ name = {p}_pip_link_frozen value = 1 }}
            set_variable = {{ name = {p}_handover_frozen value = 1 }}
            set_variable = {{ name = {p}_omitted_material value = 0 }}
            set_variable = {{ name = {p}_retaliatory_whisper value = 0 }}
            set_variable = {{ name = {p}_whitewash_audit value = 0 }}
            set_variable = {{ name = {p}_anti_retaliation_audit value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_omitted_material value = 1 }} set_variable = {{ name = {p}_retaliatory_whisper value = 1 }} set_variable = {{ name = {p}_whitewash_audit value = 1 }} set_variable = {{ name = {p}_anti_retaliation_audit value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_whitewash_audit }}''',
        314: f'''set_variable = {{ name = {p}_accepted value = 0 }}
            set_variable = {{ name = {p}_vacancy_id value = var:zg361_transfer_cl_vacancy }}
            set_variable = {{ name = {p}_target_manager value = var:zg361_transfer_cl_receiver }}
            set_variable = {{ name = {p}_declined value = 0 }}
            set_variable = {{ name = {p}_response_once value = 1 }}
            set_variable = {{ name = {p}_lump_sum value = 10 }}
            set_variable = {{ name = {p}_temporary_allowance value = 6 }}
            set_variable = {{ name = {p}_family_support value = 4 }}
            set_variable = {{ name = {p}_allowance_end_day value = 190 }}
            set_variable = {{ name = {p}_allowance_active value = 0 }}
            set_variable = {{ name = {p}_performance_delta value = 0 }}
            if = {{ limit = {{ var:{p}_route = 1 }} set_variable = {{ name = {p}_accepted value = 1 }} set_variable = {{ name = {p}_allowance_active value = 1 }} }}
            else = {{ set_variable = {{ name = {p}_declined value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_accepted }}''',
        315: f'''set_variable = {{ name = {p}_trial_days value = 90 }}
            set_variable = {{ name = {p}_vacancy_id value = var:zg361_transfer_cl_vacancy }}
            set_variable = {{ name = {p}_source_manager value = var:zg361_transfer_cl_owner }}
            set_variable = {{ name = {p}_target_manager value = var:zg361_transfer_cl_receiver }}
            set_variable = {{ name = {p}_source_credit_share value = 40 }}
            set_variable = {{ name = {p}_target_credit_share value = 60 }}
            set_variable = {{ name = {p}_credit_sum value = 100 }}
            set_variable = {{ name = {p}_employee_exit_right value = 1 }}
            set_variable = {{ name = {p}_source_exit_right value = 1 }}
            set_variable = {{ name = {p}_target_exit_right value = 1 }}
            set_variable = {{ name = {p}_returned_to_source value = 0 }}
            set_variable = {{ name = {p}_failed_is_low_grade value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_returned_to_source value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_returned_to_source }}''',
        316: f'''set_variable = {{ name = {p}_mapping_frozen_before_accept value = 1 }}
            set_variable = {{ name = {p}_professional_base value = 30 }}
            set_variable = {{ name = {p}_source_allowance value = 10 }}
            set_variable = {{ name = {p}_target_allowance value = 5 }}
            set_variable = {{ name = {p}_method value = 2 }}
            set_variable = {{ name = {p}_step_1 value = 38 }}
            set_variable = {{ name = {p}_step_2 value = 36 }}
            set_variable = {{ name = {p}_step_3 value = 35 }}
            set_variable = {{ name = {p}_historical_payments_immutable value = 1 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_method value = 3 }} set_variable = {{ name = {p}_step_1 value = 35 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_method }}''',
        317: f'''set_variable = {{ name = {p}_acl_stage value = 1 }}
            set_variable = {{ name = {p}_authorized_viewers value = 1 }}
            set_variable = {{ name = {p}_access_log_rows value = 1 }}
            set_variable = {{ name = {p}_leaked_to_source value = 0 }}
            set_variable = {{ name = {p}_rating_changed_without_evidence value = 0 }}
            set_variable = {{ name = {p}_anti_retaliation_audit value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_authorized_viewers value = 2 }} set_variable = {{ name = {p}_leaked_to_source value = 1 }} set_variable = {{ name = {p}_rating_changed_without_evidence value = 1 }} set_variable = {{ name = {p}_anti_retaliation_audit value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_anti_retaliation_audit }}''',
        318: f'''set_variable = {{ name = {p}_formal_limit value = 2 }}
            set_variable = {{ name = {p}_formal_used value = 1 }}
            set_variable = {{ name = {p}_withdrawal_still_consumes value = 1 }}
            set_variable = {{ name = {p}_exploratory_consumes value = 0 }}
            set_variable = {{ name = {p}_manager_timeout_refunds value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_formal_used value = 0 }} set_variable = {{ name = {p}_manager_timeout_refunds value = 1 }} }}
            set_variable = {{ name = {p}_formal_remaining value = {{ value = 2 subtract = var:{p}_formal_used }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_formal_remaining }}''',
        319: f'''set_variable = {{ name = {p}_counteroffer_count value = 1 }}
            set_variable = {{ name = {p}_vacancy_id value = var:zg361_transfer_cl_vacancy }}
            set_variable = {{ name = {p}_target_manager value = var:zg361_transfer_cl_receiver }}
            set_variable = {{ name = {p}_counteroffer_limit value = 1 }}
            set_variable = {{ name = {p}_release_deadline_days value = 30 }}
            set_variable = {{ name = {p}_promise_deadline_days value = 90 }}
            set_variable = {{ name = {p}_released_on_time value = 1 }}
            set_variable = {{ name = {p}_promise_fulfilled value = 1 }}
            set_variable = {{ name = {p}_manager_talent_delta value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_released_on_time value = 0 }} set_variable = {{ name = {p}_promise_fulfilled value = 0 }} set_variable = {{ name = {p}_promise_pending value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_manager_talent_delta }}''',
        320: f'''set_variable = {{ name = {p}_named_n value = 1 }}
            set_variable = {{ name = {p}_anonymous_n value = 1 }}
            set_variable = {{ name = {p}_declined_n value = 1 }}
            set_variable = {{ name = {p}_minimum_same_issue_sample value = 2 }}
            set_variable = {{ name = {p}_same_issue_n value = 2 }}
            set_variable = {{ name = {p}_audit_triggered value = 1 }}
            set_variable = {{ name = {p}_anonymous_identity_hidden value = 1 }}
            set_variable = {{ name = {p}_original_reason_preserved value = 1 }}
            set_variable = {{ name = {p}_reclassification_rows value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_reclassification_rows value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_audit_triggered }}''',
        321: f'''set_variable = {{ name = {p}_consent value = 1 }}
            set_variable = {{ name = {p}_maintenance_once_per_cycle value = 1 }}
            set_variable = {{ name = {p}_lead_idempotent value = 1 }}
            set_variable = {{ name = {p}_contact_projection_deleted value = 0 }}
            set_variable = {{ name = {p}_humiliation_history_immutable value = 1 }}
            set_variable = {{ name = {p}_talent_reputation_delta value = 2 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_consent value = 0 }} set_variable = {{ name = {p}_contact_projection_deleted value = 1 }} set_variable = {{ name = {p}_talent_reputation_delta value = -10 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_talent_reputation_delta }}''',
        322: f'''set_variable = {{ name = {p}_old_case_links value = 2 }}
            set_variable = {{ name = {p}_exit_reason_frozen value = 1 }}
            set_variable = {{ name = {p}_old_misconduct_links value = 1 }}
            set_variable = {{ name = {p}_external_evidence_links value = 1 }}
            set_variable = {{ name = {p}_active_flow_limit value = 1 }}
            set_variable = {{ name = {p}_new_cohort_count value = 1 }}
            set_variable = {{ name = {p}_history_wipe_blocked value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_history_wipe_blocked value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_old_case_links }}''',
        323: f'''set_variable = {{ name = {p}_gold_pool value = 40 }}
            set_variable = {{ name = {p}_protected_hours_pool value = 20 }}
            set_variable = {{ name = {p}_allocated_gold value = 10 }}
            set_variable = {{ name = {p}_allocated_hours value = 5 }}
            set_variable = {{ name = {p}_gold_conserved value = 1 }}
            set_variable = {{ name = {p}_hours_conserved value = 1 }}
            set_variable = {{ name = {p}_completion_performance_credit value = 0 }}
            set_variable = {{ name = {p}_certificate_only value = 0 }}
            set_variable = {{ name = {p}_manager_learning_delta value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_allocated_hours value = 0 }} set_variable = {{ name = {p}_certificate_only value = 1 }} set_variable = {{ name = {p}_manager_learning_delta value = -10 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_allocated_hours }}''',
        324: f'''set_variable = {{ name = {p}_completion_evidence value = 1 }}
            set_variable = {{ name = {p}_application_evidence value = 1 }}
            set_variable = {{ name = {p}_outcome_evidence value = 1 }}
            set_variable = {{ name = {p}_observed_delta value = 12 }}
            set_variable = {{ name = {p}_performance_credit value = 12 }}
            set_variable = {{ name = {p}_outcome_requires_application value = 1 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_application_evidence value = 0 }} set_variable = {{ name = {p}_outcome_evidence value = 0 }} set_variable = {{ name = {p}_observed_delta value = 0 }} set_variable = {{ name = {p}_performance_credit value = 0 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_performance_credit }}''',
        325: f'''set_variable = {{ name = {p}_certificate_passed value = 1 }}
            set_variable = {{ name = {p}_practical_score value = 30 }}
            set_variable = {{ name = {p}_practical_threshold value = 60 }}
            set_variable = {{ name = {p}_test_valid value = 1 }}
            set_variable = {{ name = {p}_competent value = 0 }}
            set_variable = {{ name = {p}_training_owner_audit value = 0 }}
            set_variable = {{ name = {p}_automatic_low_grade value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_test_valid value = 0 }} set_variable = {{ name = {p}_training_owner_audit value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_competent }}''',
        326: f'''set_variable = {{ name = {p}_days_away value = 4 }}
            set_variable = {{ name = {p}_artifact_adopted value = 1 }}
            set_variable = {{ name = {p}_adopted_value value = 6 }}
            set_variable = {{ name = {p}_reputation_gain value = 2 }}
            set_variable = {{ name = {p}_delivery_opportunity_cost value = 4 }}
            set_variable = {{ name = {p}_attrition_risk value = 1 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_artifact_adopted value = 0 }} set_variable = {{ name = {p}_adopted_value value = 0 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_adopted_value }}''',
        327: f'''set_variable = {{ name = {p}_teaching_hours value = 8 }}
            set_variable = {{ name = {p}_available_hours value = 40 }}
            set_variable = {{ name = {p}_remaining_hours value = 32 }}
            set_variable = {{ name = {p}_attendees value = 2 }}
            set_variable = {{ name = {p}_applying_attendees value = 1 }}
            set_variable = {{ name = {p}_teacher_share value = 60 }}
            set_variable = {{ name = {p}_applicator_share value = 40 }}
            set_variable = {{ name = {p}_share_sum value = 100 }}
            set_variable = {{ name = {p}_performance_credit value = 6 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_applying_attendees value = 0 }} set_variable = {{ name = {p}_performance_credit value = 0 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_performance_credit }}''',
        328: f'''set_variable = {{ name = {p}_artifacts value = 2 }}
            set_variable = {{ name = {p}_maintainers value = 1 }}
            set_variable = {{ name = {p}_available_hours value = 10 }}
            set_variable = {{ name = {p}_contribution_hours value = 6 }}
            set_variable = {{ name = {p}_capacity_conserved value = 1 }}
            set_variable = {{ name = {p}_adopting_teams value = 2 }}
            set_variable = {{ name = {p}_cross_team_impact value = 2 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_adopting_teams value = 0 }} set_variable = {{ name = {p}_cross_team_impact value = 0 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_cross_team_impact }}''',
        329: f'''set_variable = {{ name = {p}_active_mentor_count value = 1 }}
            set_variable = {{ name = {p}_goal_count value = 1 }}
            set_variable = {{ name = {p}_committed_hours value = 6 }}
            set_variable = {{ name = {p}_capacity_payment value = 2 }}
            set_variable = {{ name = {p}_deadline_before value = 190 }}
            set_variable = {{ name = {p}_deadline_after value = 190 }}
            set_variable = {{ name = {p}_rematch_limit value = 1 }}
            set_variable = {{ name = {p}_rematch_used value = 0 }}
            set_variable = {{ name = {p}_application_evidence value = 0 }}
            set_variable = {{ name = {p}_mentor_credit value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_rematch_used value = 1 }} }}
            if = {{ limit = {{ var:{p}_mentor_distinct = 0 }} set_variable = {{ name = {p}_active_mentor_count value = 0 }} set_variable = {{ name = {p}_application_evidence value = 0 }} set_variable = {{ name = {p}_mentor_credit value = 0 }} set_variable = {{ name = {p}_match_failed value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_mentor_credit }}''',
        330: f'''set_variable = {{ name = {p}_route_code value = 1 }}
            set_variable = {{ name = {p}_affected_character_count value = 1 }}
            set_variable = {{ name = {p}_target_role_count value = 1 }}
            set_variable = {{ name = {p}_training_days value = 90 }}
            set_variable = {{ name = {p}_assessment_score value = 50 }}
            set_variable = {{ name = {p}_threshold value = 70 }}
            set_variable = {{ name = {p}_placed value = 0 }}
            set_variable = {{ name = {p}_failed_is_low_grade value = 0 }}
            set_variable = {{ name = {p}_fairness_debt value = 0 }}
            set_variable = {{ name = {p}_role_identity_conserved value = 1 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_route_code value = 2 }} set_variable = {{ name = {p}_fairness_debt value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_placed }}''',
        331: f'''set_variable = {{ name = {p}_total_capacity value = 100 }}
            set_variable = {{ name = {p}_protected_hours value = 10 }}
            set_variable = {{ name = {p}_borrowed_hours value = 4 }}
            set_variable = {{ name = {p}_delivery_hours value = 94 }}
            set_variable = {{ name = {p}_real_crisis_required value = 1 }}
            set_variable = {{ name = {p}_repayment_due_cycle value = {{ value = var:zg361_case_ai_cycle_serial add = 1 }} }}
            set_variable = {{ name = {p}_repaid_hours value = 0 }}
            set_variable = {{ name = {p}_manager_score_delta value = 0 }}
            set_variable = {{ name = {p}_capacity_conserved value = 1 }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_manager_score_delta }}''',
        332: f'''set_variable = {{ name = {p}_safe_simulation value = 1 }}
            set_variable = {{ name = {p}_readiness_before value = 40 }}
            set_variable = {{ name = {p}_readiness_after value = 50 }}
            set_variable = {{ name = {p}_success value = 1 }}
            set_variable = {{ name = {p}_emergency_veto_limit value = 1 }}
            set_variable = {{ name = {p}_emergency_veto_used value = 0 }}
            set_variable = {{ name = {p}_development_gap value = 0 }}
            set_variable = {{ name = {p}_real_incident value = 0 }}
            set_variable = {{ name = {p}_automatic_low_grade value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_readiness_after value = 42 }} set_variable = {{ name = {p}_success value = 0 }} set_variable = {{ name = {p}_emergency_veto_used value = 1 }} set_variable = {{ name = {p}_development_gap value = 1 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_readiness_after }}''',
        333: f'''set_variable = {{ name = {p}_training_cost value = 24 }}
            set_variable = {{ name = {p}_completion_day value = 100 }}
            set_variable = {{ name = {p}_service_end_day value = 460 }}
            set_variable = {{ name = {p}_monthly_reduction value = 2 }}
            set_variable = {{ name = {p}_months_served value = 3 }}
            set_variable = {{ name = {p}_recovery_cap value = 24 }}
            set_variable = {{ name = {p}_outstanding value = 0 }}
            set_variable = {{ name = {p}_application_evidence value = 1 }}
            set_variable = {{ name = {p}_performance_credit value = 1 }}
            set_variable = {{ name = {p}_organization_layoff_exempt value = 1 }}
            set_variable = {{ name = {p}_recovery_settled value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_outstanding value = 18 }} set_variable = {{ name = {p}_application_evidence value = 0 }} set_variable = {{ name = {p}_performance_credit value = 0 }} set_variable = {{ name = {p}_organization_layoff_exempt value = 0 }} }}
            set_variable = {{ name = {p}_consumer_value value = var:{p}_performance_credit }}''',
    }
    return payloads[mechanism_id]


def obligation_event_id(mechanism_id: int) -> int:
    return 500 + mechanism_id


def render_typed_relations(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    owner = f"var:{p}_object_owner"
    subject = f"var:{p}_object_subject"
    relations = {
        312: (("reporting_manager", owner), ("vacancy_candidate", subject)),
        313: (("source_manager", owner), ("reference_candidate", subject)),
        314: (("target_manager", "var:zg361_transfer_cl_receiver"), ("offered_official", subject)),
        315: (("trial_target_manager", "var:zg361_transfer_cl_receiver"), ("trial_official", subject)),
        316: (("pay_owner", owner), ("mapped_official", subject)),
        317: (("acl_owner", owner), ("applicant", subject)),
        318: (("quota_owner", owner), ("applicant", subject)),
        319: (("releasing_manager", owner), ("target_manager", "var:zg361_transfer_cl_receiver"), ("released_official", subject)),
        320: (("aggregate_owner", owner), ("exit_official", subject)),
        321: (("relationship_owner", owner), ("alumnus", subject)),
        322: (("returnee_owner", owner), ("returnee", subject)),
        323: (("budget_owner", owner), ("learner", subject)),
        324: (("learning_owner", owner), ("learner", subject)),
        325: (("training_owner", owner), ("assessed_official", subject)),
        326: (("conference_owner", owner), ("delegate", subject)),
        327: (("application_owner", owner), ("teacher", subject)),
        328: (("community_owner", owner), ("maintainer", subject)),
        330: (("target_role_owner", owner), ("affected_official", subject)),
        331: (("capacity_owner", owner), ("learner", subject)),
        332: (("incumbent", owner), ("successor_candidate", subject)),
        333: (("contract_owner", owner), ("bound_official", subject)),
    }
    if row.mechanism_id == 329:
        return f'''save_temporary_scope_as = zg361_cl_mentor_subject
                var:{p}_object_owner = {{
                    random_vassal = {{
                        limit = {{
                            zg361_is_reviewable_vassal_trigger = yes
                            NOT = {{ this = scope:zg361_cl_mentor_subject }}
                        }}
                        save_temporary_scope_as = zg361_cl_external_mentor
                    }}
                }}
                if = {{
                    limit = {{ exists = scope:zg361_cl_external_mentor }}
                    set_variable = {{ name = {p}_mentor value = scope:zg361_cl_external_mentor }}
                    set_variable = {{ name = {p}_mentor_distinct value = 1 }}
                }}
                else = {{
                    # A missing distinct mentor is an observable negative object,
                    # never a fabricated successful cross-team match.
                    set_variable = {{ name = {p}_mentor_missing value = 1 }}
                    set_variable = {{ name = {p}_mentor_distinct value = 0 }}
                }}
                set_variable = {{ name = {p}_mentee value = {subject} }}'''
    return "\n                ".join(
        f"set_variable = {{ name = {p}_{name} value = {value} }}"
        for name, value in relations[row.mechanism_id]
    )


def render_object_open(row: Mechanism) -> str:
    """Freeze a queryable business/debt object after the kernel receipt."""

    p = f"zg361_cl_m{row.mechanism_id:03d}"
    kind_id = row.mechanism_id - EXPECTED_IDS[0] + 1
    return f'''set_variable = {{ name = {p}_object_kind_id value = {kind_id} }}
                set_variable = {{ name = {p}_object_serial value = $TICKET_CASE$ }}
                set_variable = {{ name = {p}_object_owner value = $TICKET_OWNER$ }}
                set_variable = {{ name = {p}_object_subject value = $TICKET_SUBJECT$ }}
                set_variable = {{ name = {p}_object_cycle value = $TICKET_CYCLE$ }}
                set_variable = {{ name = {p}_object_case value = $TICKET_CASE$ }}
                set_variable = {{ name = {p}_object_route value = scope:zg361_cl_route }}
                set_variable = {{ name = {p}_object_revision value = 1 }}
                set_variable = {{ name = {p}_object_consumer_revision value = 0 }}
                set_variable = {{ name = {p}_object_resolved value = 0 }}
                set_variable = {{ name = {p}_obligation_pending value = 0 }}
                set_variable = {{ name = {p}_obligation_resolved value = 0 }}
                set_variable = {{ name = {p}_relation_manager value = $TICKET_OWNER$ }}
                set_variable = {{ name = {p}_relation_official value = $TICKET_SUBJECT$ }}
                {render_typed_relations(row)}
                if = {{
                    limit = {{ scope:zg361_cl_route = 3 }}
                    set_variable = {{ name = {p}_object_active value = 0 }}
                    set_variable = {{ name = {p}_debt_active value = 1 }}
                    set_variable = {{ name = {p}_acl_class value = 0 }}
                }}
                else = {{
                    set_variable = {{ name = {p}_object_active value = 1 }}
                    set_variable = {{ name = {p}_debt_active value = 0 }}
                    if = {{
                        limit = {{ scope:zg361_cl_route = 1 }}
                        set_variable = {{ name = {p}_acl_class value = 1 }}
                    }}
                    else = {{ set_variable = {{ name = {p}_acl_class value = 2 }} }}
                }}'''


def render_obligation_schedule(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    routes = OBLIGATION_DAYS[row.mechanism_id]
    branches: list[str] = []
    for index, (route, days) in enumerate(sorted(routes.items())):
        keyword = "if" if index == 0 else "else_if"
        branches.append(f'''{keyword} = {{
                    limit = {{ scope:zg361_cl_route = {route} }}
                    set_variable = {{ name = {p}_obligation_pending value = 1 }}
                    set_variable = {{ name = {p}_obligation_days value = {days} }}
                    set_variable = {{ name = {p}_obligation_owner value = $TICKET_OWNER$ }}
                    set_variable = {{ name = {p}_obligation_subject value = $TICKET_SUBJECT$ }}
                    set_variable = {{ name = {p}_obligation_cycle value = $TICKET_CYCLE$ }}
                    set_variable = {{ name = {p}_obligation_case value = $TICKET_CASE$ }}
                    set_variable = {{ name = {p}_obligation_route value = scope:zg361_cl_route }}
                    trigger_event = {{ id = zg361cl.{obligation_event_id(row.mechanism_id)} days = {days} }}
                }}''')
    branches.append(f'''else = {{
                    set_variable = {{ name = {p}_obligation_pending value = 0 }}
                    set_variable = {{ name = {p}_obligation_days value = 0 }}
                }}''')
    return "\n                ".join(branches)


def render_relationship_mutation(row: Mechanism) -> str:
    if row.mechanism_id not in RELATIONSHIP_IDS:
        return ""
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    return f'''if = {{
            limit = {{ var:{p}_route = 1 }}
            add_opinion = {{ modifier = friendliness_opinion target = var:{p}_object_owner opinion = 5 }}
            set_variable = {{ name = {p}_relationship_revision value = 1 }}
        }}
        else_if = {{
            limit = {{ var:{p}_route = 2 }}
            add_opinion = {{ modifier = angry_opinion target = var:{p}_object_owner opinion = -5 }}
            set_variable = {{ name = {p}_relationship_revision value = 1 }}
        }}'''


def render_consumer(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    return f'''# {row.mechanism_id:03d} consumer: frozen receipt -> domain projection.
zg361_cl_m{row.mechanism_id:03d}_consume_effect = {{
    if = {{
        limit = {{
            {receipt_current(row)}
            NOT = {{ var:{p}_route = 3 }}
        }}
        {payload(row.mechanism_id)}
        {render_relationship_mutation(row)}
        change_variable = {{ name = {p}_object_consumer_revision add = 1 }}
        set_variable = {{ name = {p}_object_state value = 2 }}
        set_variable = {{ name = {p}_consumed value = 1 }}
        debug_log = "ZG361CL: consumed {row.mechanism_id:03d} {row.operation}"
    }}
}}'''


def render_standard_core(row: Mechanism) -> str:
    """Keep the unchanged 18 mechanisms byte-stable."""

    p = f"zg361_cl_m{row.mechanism_id:03d}"
    v = case_vars(row.domain)
    prepare = (
        render_dual_prepare(row)
        if row.mechanism_id in DUAL_COSTS
        else f"set_variable = {{ name = {p}_dual_payment_ready value = 1 }}"
    )
    apply_cost = render_dual_apply(row) if row.mechanism_id in DUAL_COSTS else ""
    rollback = (
        f'''# The shadow journals settled before the business receipt.  If the
                # receipt unexpectedly loses its frozen guard, undo both journals;
                # no CK3 gold has been deducted yet and the same ticket may retry.
                {transaction_refund(row, "treasury")}
                {transaction_refund(row, "manager")}'''
        if row.mechanism_id in DUAL_COSTS
        else ""
    )
    return f'''# {row.mechanism_id:03d} {row.operation}
zg361_cl_m{row.mechanism_id:03d}_core_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_cl_route value = $ROUTE$ }}
    zg361_cl_clear_red_effect = yes
    if = {{
        limit = {{ {receipt_current(row, ticket=True)} }}
        zg361_cl_set_red_effect = {{ CODE = 3 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {kernel_guard(row.domain, row.state, ticket=True)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {live_permission_trigger(row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{
            NOT = {{
                OR = {{
                    scope:zg361_cl_route = 1
                    scope:zg361_cl_route = 2
                    scope:zg361_cl_route = 3
                }}
            }}
        }}
        zg361_cl_set_red_effect = {{ CODE = 4 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {semantic_precheck(row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 4 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {resource_precheck(row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 5 MECHANISM = {row.mechanism_id} }}
    }}
    else = {{
        {prepare}
        if = {{
            limit = {{ var:{p}_dual_payment_ready = 1 }}
            {record_operation(row)}
            if = {{
                limit = {{ var:zg361_case_kernel_applied = 1 }}
                set_variable = {{ name = {p}_route value = scope:zg361_cl_route }}
                set_variable = {{ name = {p}_consumed value = 0 }}
                set_variable = {{ name = {p}_deferred value = 0 }}
                {apply_cost}
                # A receipt now owns one typed object identity.  A/B activate
                # the business object; C activates only a due governance debt.
                {render_object_open(row)}
                {render_obligation_schedule(row)}
                if = {{
                    limit = {{ scope:zg361_cl_route = 3 }}
                    set_variable = {{ name = {p}_deferred value = 1 }}
                    set_variable = {{ name = {p}_debt_due_cycle value = {{ value = var:{v["cycle"]} add = 1 }} }}
                    set_variable = {{ name = {p}_consumer_value value = 0 }}
                }}
                else = {{ zg361_cl_m{row.mechanism_id:03d}_consume_effect = yes }}
            }}
            else = {{
                {rollback}
                zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
            }}
        }}
        else = {{ zg361_cl_set_red_effect = {{ CODE = 5 MECHANISM = {row.mechanism_id} }} }}
    }}
}}'''


def render_core(row: Mechanism) -> str:
    if row.mechanism_id not in {312, 314, 315, 319}:
        return render_standard_core(row)
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    v = case_vars(row.domain)
    prepare = (
        render_dual_prepare(row)
        if row.mechanism_id in DUAL_COSTS
        else f"set_variable = {{ name = {p}_dual_payment_ready value = 1 }}"
    )
    apply_cost = render_dual_apply(row) if row.mechanism_id in DUAL_COSTS else ""
    rollback = (
        f'''# The shadow journals settled before the business receipt.  If the
                # receipt unexpectedly loses its frozen guard, undo both journals;
                # no CK3 gold has been deducted yet and the same ticket may retry.
                {transaction_refund(row, "treasury")}
                {transaction_refund(row, "manager")}'''
        if row.mechanism_id in DUAL_COSTS
        else ""
    )
    mobility = render_mobility_preaction(row)
    mobility_red = (
        f'''if = {{
            limit = {{
                var:{p}_mobility_policy_debt = 1
                var:{p}_mobility_red_code > 0
            }}
            zg361_cl_set_red_effect = {{ CODE = 6 MECHANISM = {row.mechanism_id} }}
        }}'''
        if row.mechanism_id in {312, 314, 315, 319}
        else ""
    )
    return f'''# {row.mechanism_id:03d} {row.operation}
zg361_cl_m{row.mechanism_id:03d}_core_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_cl_route value = $ROUTE$ }}
    zg361_cl_clear_red_effect = yes
    if = {{
        limit = {{ {receipt_current(row, ticket=True)} }}
        zg361_cl_set_red_effect = {{ CODE = 3 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {kernel_guard(row.domain, row.state, ticket=True)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {live_permission_trigger(row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{
            NOT = {{
                OR = {{
                    scope:zg361_cl_route = 1
                    scope:zg361_cl_route = 2
                    scope:zg361_cl_route = 3
                }}
            }}
        }}
        zg361_cl_set_red_effect = {{ CODE = 4 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {semantic_precheck(row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 4 MECHANISM = {row.mechanism_id} }}
    }}
    else = {{
        {mobility}
        if = {{
            limit = {{ NOT = {{ {resource_precheck(row)} }} }}
            zg361_cl_set_red_effect = {{ CODE = 5 MECHANISM = {row.mechanism_id} }}
        }}
        else = {{
            {prepare}
            if = {{
                limit = {{ var:{p}_dual_payment_ready = 1 }}
                {record_operation(row)}
                if = {{
                    limit = {{ var:zg361_case_kernel_applied = 1 }}
                    set_variable = {{ name = {p}_route value = scope:zg361_cl_route }}
                    set_variable = {{ name = {p}_consumed value = 0 }}
                    set_variable = {{ name = {p}_deferred value = 0 }}
                    {apply_cost}
                    # A receipt now owns one typed object identity.  A/B activate
                    # the business object; C activates only a due governance debt.
                    {render_object_open(row)}
                    {render_obligation_schedule(row)}
                    if = {{
                        limit = {{ scope:zg361_cl_route = 3 }}
                        set_variable = {{ name = {p}_deferred value = 1 }}
                        set_variable = {{ name = {p}_debt_due_cycle value = {{ value = var:{v["cycle"]} add = 1 }} }}
                        set_variable = {{ name = {p}_consumer_value value = 0 }}
                    }}
                    else = {{ zg361_cl_m{row.mechanism_id:03d}_consume_effect = yes }}
                }}
                else = {{
                    {rollback}
                    zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
                }}
            }}
            else = {{ zg361_cl_set_red_effect = {{ CODE = 5 MECHANISM = {row.mechanism_id} }} }}
        }}
        {mobility_red}
    }}
}}'''


def render_manager_entry(row: Mechanism) -> str:
    return f'''zg361_cl_m{row.mechanism_id:03d}_manager_apply_effect = {{
    zg361_cl_m{row.mechanism_id:03d}_core_effect = {{
        ROUTE = $ROUTE$
        TICKET_OWNER = $TICKET_OWNER$
        TICKET_SUBJECT = $TICKET_SUBJECT$
        TICKET_CYCLE = $TICKET_CYCLE$
        TICKET_CASE = $TICKET_CASE$
        TICKET_STATE = $TICKET_STATE$
    }}
}}'''


def render_subject_response(row: Mechanism) -> str:
    if row.mechanism_id not in SUBJECT_RESPONSE_IDS:
        return ""
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    return f'''# Assessed count/baron self-response.  It grants no manager or case authority.
zg361_cl_m{row.mechanism_id:03d}_subject_response_effect = {{
    remove_variable = zg361_cl_subject_response_applied
    save_temporary_scope_value_as = {{ name = zg361_cl_subject_route value = $ROUTE$ }}
    if = {{
        limit = {{
            is_ai = no
            {kernel_guard(row.domain, row.state, ticket=True)}
            zg361_case_kernel_subject_self_guard_trigger = {{
                SUBJECT_VAR = zg361_case_{row.domain}_subject
                ACTIVE_VAR = zg361_case_{row.domain}_active
            }}
            NOT = {{ has_variable = {p}_subject_response }}
            OR = {{
                scope:zg361_cl_subject_route = 1
                scope:zg361_cl_subject_route = 2
            }}
        }}
        set_variable = {{ name = {p}_subject_response value = scope:zg361_cl_subject_route }}
        set_variable = {{ name = zg361_cl_subject_response_applied value = 1 }}
        change_variable = {{ name = zg361_case_{row.domain}_feedback_revision add = 1 }}
        debug_log = "ZG361CL: assessed subject answered {row.mechanism_id:03d} once"
    }}
}}'''


def obligation_resolution_payload(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    payloads = {
        312: f"set_variable = {{ name = {p}_vacancy_closed value = 1 }}",
        313: f"set_variable = {{ name = {p}_reference_review_closed value = 1 }}",
        314: f"set_variable = {{ name = {p}_allowance_active value = 0 }}",
        315: f"set_variable = {{ name = {p}_trial_resolved value = 1 }}",
        316: f"set_variable = {{ name = {p}_pay_mapping_settled value = 1 }}",
        317: f"set_variable = {{ name = {p}_acl_review_closed value = 1 }}",
        318: f"set_variable = {{ name = {p}_slot_timeout_settled value = 1 }}",
        319: f'''set_variable = {{ name = {p}_release_or_promise_checked value = 1 }}
            if = {{
                limit = {{ var:{p}_route = 2 }}
                set_variable = {{ name = {p}_promise_pending value = 0 }}
                set_variable = {{ name = {p}_manager_talent_delta value = -20 }}
            }}''',
        320: f"set_variable = {{ name = {p}_aggregate_audit_closed value = 1 }}",
        321: f"set_variable = {{ name = {p}_alumni_contact_cycle_closed value = 1 }}",
        322: f"set_variable = {{ name = {p}_returnee_review_closed value = 1 }}",
        323: f"set_variable = {{ name = {p}_learning_budget_window_closed value = 1 }}",
        324: f"set_variable = {{ name = {p}_outcome_window_closed value = 1 }}",
        325: f"set_variable = {{ name = {p}_practical_assessment_closed value = 1 }}",
        326: f"set_variable = {{ name = {p}_adoption_window_closed value = 1 }}",
        327: f"set_variable = {{ name = {p}_teaching_application_window_closed value = 1 }}",
        328: f"set_variable = {{ name = {p}_community_maintenance_window_closed value = 1 }}",
        329: f'''set_variable = {{ name = {p}_mentor_match_window_closed value = 1 }}
            if = {{
                limit = {{ var:{p}_route = 1 var:{p}_mentor_distinct = 1 }}
                set_variable = {{ name = {p}_application_evidence value = 1 }}
                set_variable = {{ name = {p}_mentor_credit value = 1 }}
            }}''',
        330: f"set_variable = {{ name = {p}_reskill_assessment_closed value = 1 }}",
        331: f'''set_variable = {{ name = {p}_protected_time_repayment_checked value = 1 }}
            set_variable = {{ name = {p}_repaid_hours value = 4 }}
            if = {{
                limit = {{ var:{p}_route = 2 }}
                set_variable = {{ name = {p}_manager_score_delta value = -10 }}
            }}''',
        332: f"set_variable = {{ name = {p}_succession_drill_closed value = 1 }}",
        333: f"set_variable = {{ name = {p}_training_service_window_closed value = 1 }}",
    }
    return payloads[row.mechanism_id]


def render_obligation_finalize(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    relationship_failure = (
        f"add_opinion = {{ modifier = angry_opinion target = var:{p}_object_owner opinion = -5 }}"
        if row.mechanism_id in RELATIONSHIP_IDS
        else ""
    )
    relationship_success = (
        f"add_opinion = {{ modifier = friendliness_opinion target = var:{p}_object_owner opinion = 5 }}"
        if row.mechanism_id in RELATIONSHIP_IDS
        else ""
    )
    return f'''set_variable = {{ name = {p}_obligation_pending value = 0 }}
            set_variable = {{ name = {p}_obligation_resolved value = 1 }}
            set_variable = {{ name = {p}_object_resolved value = 1 }}
            set_variable = {{ name = {p}_object_state value = 3 }}
            {obligation_resolution_payload(row)}
            if = {{
                limit = {{ var:{p}_object_route = 3 }}
                set_variable = {{ name = {p}_debt_overdue value = 1 }}
                {relationship_failure}
            }}
            else_if = {{
                limit = {{ var:{p}_object_route = 2 }}
                set_variable = {{ name = {p}_obligation_negative_outcome value = 1 }}
                {relationship_failure}
            }}
            else = {{
                set_variable = {{ name = {p}_obligation_positive_outcome value = 1 }}
                {relationship_success}
            }}'''


def render_obligation_resolver(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    finalizer = render_obligation_finalize(row)
    if row.mechanism_id == 319:
        resolve_body = f'''if = {{
            limit = {{ var:{p}_object_route = 1 }}
            zg361_career_hc_settle_cl_transfer_effect = yes
            if = {{
                limit = {{ var:zg361_transfer_cl_applied = 1 }}
                zg361_cl_m312_hire_once_effect = yes
                {finalizer}
            }}
            else = {{
                # Invalid receiver/war/HC joins reclaim the reserved seat and
                # close as policy debt without any scripted liege mutation.
                zg361_cl_set_red_effect = {{ CODE = 6 MECHANISM = 319 }}
                set_variable = {{ name = {p}_obligation_pending value = 0 }}
                set_variable = {{ name = {p}_obligation_resolved value = 1 }}
                set_variable = {{ name = {p}_object_resolved value = 1 }}
                set_variable = {{ name = {p}_object_state value = 4 }}
                set_variable = {{ name = {p}_debt_active value = 1 }}
                set_variable = {{ name = {p}_debt_overdue value = 1 }}
                set_variable = {{ name = {p}_mobility_settlement_failed value = 1 }}
                add_opinion = {{ modifier = angry_opinion target = var:{p}_object_owner opinion = -5 }}
            }}
        }}
        else = {{ {finalizer} }}'''
    elif row.mechanism_id == 333:
        resolve_body = f'''if = {{
            limit = {{ var:{p}_object_route = 2 }}
            zg361_cl_m333_layoff_exemption_effect = yes
            if = {{
                limit = {{ var:{p}_recovery_settled = 0 }}
                zg361_cl_m333_recover_outstanding_effect = yes
            }}
            if = {{
                limit = {{ var:{p}_recovery_settled = 1 }}
                {finalizer}
            }}
            else = {{
                # Insufficient personal funds leave the obligation pending and
                # retryable; no recovery or resolved receipt is fabricated.
                trigger_event = {{ id = zg361cl.{obligation_event_id(row.mechanism_id)} days = 30 }}
            }}
        }}
        else = {{ {finalizer} }}'''
    else:
        resolve_body = finalizer
    return f'''# {row.mechanism_id:03d} post-receipt business/debt deadline consumer.
zg361_cl_m{row.mechanism_id:03d}_resolve_obligation_effect = {{
    zg361_cl_clear_red_effect = yes
    if = {{
        limit = {{ NOT = {{ var:{p}_obligation_pending = 1 }} }}
        zg361_cl_set_red_effect = {{ CODE = 3 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{
            NOT = {{
                AND = {{
                    has_variable = {p}_object_owner
                    has_variable = {p}_object_subject
                    has_variable = {p}_object_cycle
                    has_variable = {p}_object_case
                    has_variable = {p}_receipt_owner
                    has_variable = {p}_receipt_subject
                    has_variable = {p}_receipt_cycle
                    has_variable = {p}_receipt_case
                    var:{p}_object_subject = this
                    var:{p}_object_owner = var:{p}_receipt_owner
                    var:{p}_object_subject = var:{p}_receipt_subject
                    var:{p}_object_cycle = var:{p}_receipt_cycle
                    var:{p}_object_case = var:{p}_receipt_case
                    var:{p}_object_revision = 1
                }}
            }}
        }}
        zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ var:{p}_object_owner = {{ zg361_is_celestial_liege_trigger = yes }} }} }}
        zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = {row.mechanism_id} }}
        # A former owner cannot execute the obligation, but the orphan is
        # terminally audited so it cannot deadlock every later review cycle.
        set_variable = {{ name = {p}_obligation_pending value = 0 }}
        set_variable = {{ name = {p}_obligation_orphaned value = 1 }}
        set_variable = {{ name = {p}_object_resolved value = 1 }}
        set_variable = {{ name = {p}_object_state value = 4 }}
    }}
    else = {{
        {resolve_body}
        debug_log = "ZG361CL: resolved {row.mechanism_id:03d} {OBJECT_KINDS[row.mechanism_id]} obligation"
    }}
}}'''


def schedule_deadline(domain: str, state: int, delay: int) -> str:
    v = case_vars(domain)
    event = 100 + state - 1 if domain == "ah" else 200 + state - 1
    p = f"zg361_cl_{domain}_s{state:02d}"
    return f'''zg361_cl_schedule_{domain}_stage_{state:02d}_effect = {{
    zg361_case_kernel_schedule_deadline_effect = {{
        OWNER_VAR = {v["owner"]}
        SUBJECT_VAR = {v["subject"]}
        CYCLE_VAR = {v["cycle"]}
        CASE_VAR = {v["case"]}
        STATE_VAR = {v["state"]}
        ACTIVE_VAR = {v["active"]}
        DEADLINE_OWNER_VAR = {p}_deadline_owner
        DEADLINE_SUBJECT_VAR = {p}_deadline_subject
        DEADLINE_CYCLE_VAR = {p}_deadline_cycle
        DEADLINE_CASE_VAR = {p}_deadline_case
        DEADLINE_STATE_VAR = {p}_deadline_state
        DEADLINE_DAYS_VAR = {p}_deadline_days
        DEADLINE_PENDING_VAR = {p}_deadline_pending
        DEADLINE_EXPIRED_VAR = {p}_deadline_expired
        TICKET_OWNER = var:{v["owner"]}
        TICKET_SUBJECT = this
        TICKET_CYCLE = var:{v["cycle"]}
        TICKET_CASE = var:{v["case"]}
        TICKET_STATE = {state}
        EVENT = zg361cl.{event}
        DAYS = {delay}
    }}
}}'''


def expire_deadline(domain: str, state: int) -> str:
    v = case_vars(domain)
    p = f"zg361_cl_{domain}_s{state:02d}"
    return f'''zg361_case_kernel_expire_deadline_effect = {{
            OWNER_VAR = {v["owner"]}
            SUBJECT_VAR = {v["subject"]}
            CYCLE_VAR = {v["cycle"]}
            CASE_VAR = {v["case"]}
            STATE_VAR = {v["state"]}
            REVISION_VAR = {v["revision"]}
            ACTIVE_VAR = {v["active"]}
            TIMELINE_VAR = {v["timeline"]}
            FEEDBACK_VAR = {v["feedback"]}
            DEADLINE_OWNER_VAR = {p}_deadline_owner
            DEADLINE_SUBJECT_VAR = {p}_deadline_subject
            DEADLINE_CYCLE_VAR = {p}_deadline_cycle
            DEADLINE_CASE_VAR = {p}_deadline_case
            DEADLINE_STATE_VAR = {p}_deadline_state
            DEADLINE_PENDING_VAR = {p}_deadline_pending
            DEADLINE_EXPIRED_VAR = {p}_deadline_expired
        }}'''


def transition(domain: str, state: int) -> str:
    return f'''zg361_case_{domain}_advance_{state:02d}_effect = {{
            TICKET_OWNER = $TICKET_OWNER$
            TICKET_SUBJECT = $TICKET_SUBJECT$
            TICKET_CYCLE = $TICKET_CYCLE$
            TICKET_CASE = $TICKET_CASE$
        }}'''


def render_stage_runner(domain: str, state: int, ids: tuple[int, ...]) -> str:
    by_id = {row.mechanism_id: row for row in MECHANISMS}
    stage_row = by_id[ids[0]]
    calls: list[str] = []
    receipts: list[str] = []
    for mechanism_id in ids:
        row = by_id[mechanism_id]
        p = f"zg361_cl_m{mechanism_id:03d}"
        ticket_args = '''
                TICKET_OWNER = $TICKET_OWNER$
                TICKET_SUBJECT = $TICKET_SUBJECT$
                TICKET_CYCLE = $TICKET_CYCLE$
                TICKET_CASE = $TICKET_CASE$
                TICKET_STATE = $TICKET_STATE$'''
        if mechanism_id == 331:
            default_call = f'''if = {{
                limit = {{
                    OR = {{
                        is_at_war = yes
                        var:zg361_case_ai_owner = {{ is_at_war = yes }}
                    }}
                }}
                zg361_cl_m331_core_effect = {{
                    ROUTE = 1{ticket_args}
                }}
            }}
            else = {{
                # No CK3 war fact means there is no real crisis to borrow for.
                # Freeze route C as制度债 instead of fabricating a crisis receipt.
                zg361_cl_m331_core_effect = {{
                    ROUTE = 3{ticket_args}
                }}
            }}'''
        else:
            default_call = f'''zg361_cl_m{mechanism_id:03d}_core_effect = {{
                ROUTE = 1{ticket_args}
            }}'''
        if mechanism_id in SUBJECT_RESPONSE_IDS:
            calls.append(f'''if = {{
        limit = {{ NOT = {{ {receipt_current(row, ticket=True)} }} }}
        if = {{
            limit = {{ has_variable = {p}_subject_response }}
            zg361_cl_m{mechanism_id:03d}_core_effect = {{
                ROUTE = var:{p}_subject_response{ticket_args}
            }}
        }}
        else_if = {{
            limit = {{ is_ai = yes }}
            {default_call}
        }}
        else_if = {{
            limit = {{ var:{p}_prompt_pending = 1 }}
            save_temporary_scope_value_as = {{ name = zg361_cl_prompt_gate value = 1 }}
        }}
        else_if = {{
            limit = {{ scope:zg361_cl_prompt_gate = 0 }}
            set_variable = {{ name = {p}_prompt_owner value = $TICKET_OWNER$ }}
            set_variable = {{ name = {p}_prompt_subject value = $TICKET_SUBJECT$ }}
            set_variable = {{ name = {p}_prompt_cycle value = $TICKET_CYCLE$ }}
            set_variable = {{ name = {p}_prompt_case value = $TICKET_CASE$ }}
            set_variable = {{ name = {p}_prompt_state value = $TICKET_STATE$ }}
            set_variable = {{ name = {p}_prompt_pending value = 1 }}
            save_temporary_scope_value_as = {{ name = zg361_cl_prompt_gate value = 1 }}
            trigger_event = {{ id = zg361cl.{mechanism_id} days = 1 }}
        }}
    }}''')
        else:
            calls.append(f'''if = {{
        limit = {{ NOT = {{ {receipt_current(row, ticket=True)} }} }}
        {default_call}
    }}''')
        receipts.append(receipt_current(row, indent=3, ticket=True))
    all_receipts = "\n".join(receipts)
    joined_calls = "\n".join(
        "\n".join("    " + line if line else line for line in call.splitlines())
        for call in calls
    )
    next_action = (
        "zg361_cl_queue_owner_digest_effect = { OWNER_VAR = zg361_case_"
        + domain
        + "_owner COUNTER = zg361_cl_portfolio_"
        + domain
        + "_completed CASE_CYCLE = $TICKET_CYCLE$ }"
        if state == len(STAGES[domain])
        else f"zg361_cl_schedule_{domain}_stage_{state + 1:02d}_effect = yes"
    )
    before_transition = ""
    completion_guard = ""
    return f'''zg361_cl_run_{domain}_stage_{state:02d}_effect = {{
    # Revalidate the frozen case and live authority even when every mechanism
    # receipt was written early and the core calls below will all be skipped.
    if = {{
        limit = {{ NOT = {{ {kernel_guard(domain, state, ticket=True)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {ids[0]} }}
    }}
    else_if = {{
        limit = {{ NOT = {{ {live_permission_trigger(stage_row)} }} }}
        zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = {ids[0]} }}
        zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes
    }}
    else = {{
    save_temporary_scope_value_as = {{ name = zg361_cl_prompt_gate value = 0 }}
{joined_calls}
    {before_transition}
    if = {{
        limit = {{
{all_receipts}
            {completion_guard}
        }}
        {transition(domain, state)}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {next_action}
        }}
        else = {{
            # A failed transition leaves the frozen stage retryable.
            zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes
        }}
    }}
    else = {{
        # A resource RED leaves the bounded case open and retries the same
        # frozen stage; it never skips the unpaid mechanism or mints a receipt.
        zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes
    }}
    }}
}}'''


def reset_deadlines(domain: str) -> str:
    lines = []
    for state in range(1, len(STAGES[domain]) + 1):
        p = f"zg361_cl_{domain}_s{state:02d}"
        lines.extend(
            (
                f"set_variable = {{ name = {p}_deadline_pending value = 0 }}",
                f"set_variable = {{ name = {p}_deadline_expired value = 0 }}",
            )
        )
    return "\n            ".join(lines)


def reset_subject_responses(domain: str) -> str:
    lines: list[str] = []
    for mechanism_id in sorted(SUBJECT_RESPONSE_IDS):
        if next(row for row in MECHANISMS if row.mechanism_id == mechanism_id).domain != domain:
            continue
        p = f"zg361_cl_m{mechanism_id:03d}"
        lines.extend(
            (
                f"remove_variable = {p}_subject_response",
                f"remove_variable = {p}_prompt_pending",
                f"remove_variable = {p}_prompt_owner",
                f"remove_variable = {p}_prompt_subject",
                f"remove_variable = {p}_prompt_cycle",
                f"remove_variable = {p}_prompt_case",
                f"remove_variable = {p}_prompt_state",
            )
        )
    return "\n            ".join(lines)


def render_open_domain(domain: str) -> str:
    upper = domain.upper()
    return f'''zg361_cl_open_{domain}_case_effect = {{
    set_variable = {{ name = zg361_cl_open_{domain}_applied value = 0 }}
    if = {{
        limit = {{
            root = {{
                zg361_is_celestial_liege_trigger = yes
                has_variable = zg361_review_serial
            }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
        }}
        zg361_case_{domain}_open_effect = yes
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {reset_deadlines(domain)}
            {reset_subject_responses(domain)}
            zg361_cl_schedule_{domain}_stage_01_effect = yes
            if = {{
                limit = {{ var:zg361_case_kernel_applied = 1 }}
                set_variable = {{ name = zg361_cl_open_{domain}_applied value = 1 }}
                debug_log = "ZG361CL: opened {upper} bounded case"
            }}
        }}
    }}
    else = {{ zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = {312 if domain == "ah" else 323} }} }}
}}'''


def render_effects() -> bytes:
    binding_lines = "\n".join(
        f"# {row.mechanism_id:03d} {row.operation} state={row.state} -> {row.consumer}"
        for row in MECHANISMS
    )
    mechanics = "\n\n".join(
        item
        for row in MECHANISMS
        for item in (
            render_core(row),
            render_consumer(row),
            render_obligation_resolver(row),
            render_manager_entry(row),
            render_subject_response(row),
        )
        if item
    )
    schedules = "\n\n".join(
        schedule_deadline(domain, state, DELAYS[domain][state - 1])
        for domain in ("ah", "ai")
        for state in range(1, len(STAGES[domain]) + 1)
    )
    runners = "\n\n".join(
        render_stage_runner(domain, state, ids)
        for domain in ("ah", "ai")
        for state, ids in enumerate(STAGES[domain], 1)
    )
    body = f'''
# Zhongguo 361 career/learning runtime: AH312-322 + AI323-333 only.
# Static-ready callable seam: zg361_cl_dispatch_direct_reports_effect.
# No scoreboard, GUI, central hook, B1/B2 or manager-governance file is owned.
{binding_lines}

# Typed RED: 1 permission, 2 stale five-field identity/state, 3 duplicate
# receipt, 4 invariant/route, 5 atomic resource precheck.
zg361_cl_set_red_effect = {{
    set_variable = {{ name = zg361_cl_last_red_code value = $CODE$ }}
    set_variable = {{ name = zg361_cl_last_red_mechanism value = $MECHANISM$ }}
    debug_log = "ZG361CL: typed RED $CODE$ on $MECHANISM$"
}}

zg361_cl_clear_red_effect = {{
    remove_variable = zg361_cl_last_red_code
    remove_variable = zg361_cl_last_red_mechanism
}}

# Owner-facing callable.  It intentionally has no is_ai=no gate: authorized
# celestial AI dukes+ are the project owner's second AI exception and use the
# same bounded cases through background events.  Only the digest is player-only.
zg361_cl_dispatch_direct_reports_effect = {{
    if = {{
        limit = {{
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
        }}
        if = {{
            limit = {{
                trigger_if = {{
                    limit = {{ has_variable = zg361_cl_portfolio_cycle }}
                    NOT = {{ var:zg361_cl_portfolio_cycle = var:zg361_review_serial }}
                }}
                trigger_else = {{ always = yes }}
            }}
            set_variable = {{ name = zg361_cl_portfolio_cycle value = var:zg361_review_serial }}
            set_variable = {{ name = zg361_cl_portfolio_ah_expected value = 0 }}
            set_variable = {{ name = zg361_cl_portfolio_ai_expected value = 0 }}
            set_variable = {{ name = zg361_cl_portfolio_ah_completed value = 0 }}
            set_variable = {{ name = zg361_cl_portfolio_ai_completed value = 0 }}
            set_variable = {{ name = zg361_cl_portfolio_digest_shown value = 0 }}
            remove_variable = zg361_cl_digest_pending
            every_vassal = {{
                limit = {{
                    zg361_is_reviewable_vassal_trigger = yes
                    liege = root
                }}
                zg361_cl_open_ah_case_effect = yes
                if = {{
                    limit = {{ var:zg361_cl_open_ah_applied = 1 }}
                    root = {{ change_variable = {{ name = zg361_cl_portfolio_ah_expected add = 1 }} }}
                }}
                zg361_cl_open_ai_case_effect = yes
                if = {{
                    limit = {{ var:zg361_cl_open_ai_applied = 1 }}
                    root = {{ change_variable = {{ name = zg361_cl_portfolio_ai_expected add = 1 }} }}
                }}
            }}
        }}
    }}
    else = {{ zg361_cl_set_red_effect = {{ CODE = 1 MECHANISM = 312 }} }}
}}

{render_open_domain("ah")}

{render_open_domain("ai")}

{schedules}

{mechanics}

{runners}

# Exactly one portfolio digest can be queued per review serial.  It waits for
# both domains across all frozen direct reports, so late deadlines cannot turn
# one portfolio into a second popup.
zg361_cl_queue_owner_digest_effect = {{
    # Freeze the source case cycle before changing into the owner scope; effect
    # parameters are textual and must not be re-read against the owner character.
    save_temporary_scope_value_as = {{
        name = zg361_cl_completion_cycle
        value = $CASE_CYCLE$
    }}
    var:$OWNER_VAR$ = {{
        if = {{
            limit = {{
                has_variable = zg361_cl_portfolio_cycle
                var:zg361_cl_portfolio_cycle = scope:zg361_cl_completion_cycle
            }}
            change_variable = {{ name = $COUNTER$ add = 1 }}
            if = {{
                limit = {{
                    is_ai = no
                    OR = {{
                        var:zg361_cl_portfolio_ah_expected > 0
                        var:zg361_cl_portfolio_ai_expected > 0
                    }}
                    var:zg361_cl_portfolio_ah_completed >= var:zg361_cl_portfolio_ah_expected
                    var:zg361_cl_portfolio_ai_completed >= var:zg361_cl_portfolio_ai_expected
                    var:zg361_cl_portfolio_digest_shown = 0
                    NOT = {{ has_variable = zg361_cl_digest_pending }}
                }}
                set_variable = {{ name = zg361_cl_digest_pending value = 1 }}
                set_variable = {{ name = zg361_cl_portfolio_digest_shown value = 1 }}
                trigger_event = {{ id = zg361cl.390 days = 1 }}
            }}
            else_if = {{
                limit = {{ is_ai = yes }}
                debug_log = "ZG361CL: eligible AI career/learning portfolio advanced silently"
            }}
        }}
        else = {{ debug_log = "ZG361CL: stale portfolio completion ignored" }}
    }}
}}

# A single legal hire consumes the vacancy.  A second call is a typed duplicate.
zg361_cl_m312_hire_once_effect = {{
    if = {{
        limit = {{
            {object_receipt_current(next(row for row in MECHANISMS if row.mechanism_id == 312))}
            var:zg361_cl_m312_legal_hc = 1
            var:zg361_cl_m312_vacancy_filled_n = 0
            var:zg361_transfer_consumer_kind = 2
            var:zg361_transfer_vacancy_status = 3
            var:zg361_transfer_cl_phase = 6
        }}
        set_variable = {{ name = zg361_cl_m312_vacancy_filled_n value = 1 }}
        set_variable = {{ name = zg361_cl_m312_hired_subject value = this }}
    }}
    else = {{ zg361_cl_set_red_effect = {{ CODE = 3 MECHANISM = 312 }} }}
}}

# Organization layoff cancels only the outstanding recovery; it cannot erase
# the original training receipt or manufacture performance credit.
zg361_cl_m333_layoff_exemption_effect = {{
    if = {{
        limit = {{
            {object_receipt_current(next(row for row in MECHANISMS if row.mechanism_id == 333))}
            var:zg361_cl_m333_recovery_settled = 0
            has_variable = zg361_b2_m074_actual_exit
            has_variable = zg361_b2_m074_reason
            has_variable = zg361_b2_m074_subject
            has_variable = zg361_b2_m074_treasury_paid
            has_variable = zg361_b2_m074_personal_received
            has_variable = zg361_b2_m074_hc_released
            has_variable = zg361_b2_m074_state
            var:zg361_b2_m074_actual_exit = 1
            var:zg361_b2_m074_reason = 1
            var:zg361_b2_m074_subject = this
            var:zg361_b2_m074_treasury_paid = 50
            var:zg361_b2_m074_personal_received = 50
            var:zg361_b2_m074_hc_released = 1
            OR = {{
                var:zg361_b2_m074_state = 3
                var:zg361_b2_m074_state = 4
            }}
        }}
        set_variable = {{ name = zg361_cl_m333_organization_layoff_exempt value = 1 }}
        set_variable = {{ name = zg361_cl_m333_outstanding value = 0 }}
        set_variable = {{ name = zg361_cl_m333_recovery_settled value = 1 }}
    }}
}}

# Voluntary early exit returns the D+90 outstanding amount to the original
# treasury/personal split.  18 <= original 24; the latch makes recovery once-only.
zg361_cl_m333_recover_outstanding_effect = {{
    if = {{
        limit = {{
            {object_receipt_current(next(row for row in MECHANISMS if row.mechanism_id == 333))}
            var:zg361_cl_m333_organization_layoff_exempt = 0
            var:zg361_cl_m333_recovery_settled = 0
            var:zg361_cl_m333_outstanding = 18
            gold >= 18
        }}
        remove_short_term_gold = 18
        var:zg361_cl_m333_object_owner = {{
            add_treasury = 13
            add_gold = 5
        }}
        set_variable = {{ name = zg361_cl_m333_recovered value = 18 }}
        set_variable = {{ name = zg361_cl_m333_recovery_settled value = 1 }}
    }}
    else = {{ zg361_cl_set_red_effect = {{ CODE = 5 MECHANISM = 333 }} }}
}}
'''
    return generated(body)


def effect_purpose(name: str) -> str:
    """Map every generated definition to its contiguous runtime purpose."""

    if name in {
        "zg361_cl_m312_hire_once_effect",
        "zg361_cl_m333_layoff_exemption_effect",
        "zg361_cl_m333_recover_outstanding_effect",
    }:
        return "cross_domain_settlement"
    if name in {
        "zg361_cl_set_red_effect",
        "zg361_cl_clear_red_effect",
        "zg361_cl_dispatch_direct_reports_effect",
        "zg361_cl_open_ah_case_effect",
        "zg361_cl_open_ai_case_effect",
    }:
        return "portfolio_control"
    for domain in ("ah", "ai"):
        if name.startswith(f"zg361_cl_schedule_{domain}_stage_"):
            return f"{domain}_deadlines"
        if name.startswith(f"zg361_cl_run_{domain}_stage_"):
            return f"{domain}_stage_runners"
    mechanism_prefix = "zg361_cl_m"
    if name.startswith(mechanism_prefix):
        mechanism_id = int(name[len(mechanism_prefix) : len(mechanism_prefix) + 3])
        row = next(item for item in MECHANISMS if item.mechanism_id == mechanism_id)
        return f"{row.domain}_stage_{row.state:02d}_mechanisms"
    if name == "zg361_cl_queue_owner_digest_effect":
        return "portfolio_digest"
    raise ValueError(f"unclassified career/learning scripted effect: {name}")


def effect_shard_outputs() -> dict[Path, bytes]:
    shards = plan_effect_shards(
        render_effects(),
        generated_header=HEADER,
        classify=effect_purpose,
    )
    rendered: dict[Path, bytes] = {}
    for index, shard in enumerate(shards, start=1):
        if not 1 <= len(shard.names) <= MAX_EFFECTS_PER_SHARD:
            raise ValueError(f"career/learning shard {index} violates the 1-10 effect boundary")
        part = f"_part_{shard.part:02d}" if shard.part > 1 else ""
        path = EFFECTS_DIR / (
            f"zg361_career_learning_{index:03d}_{shard.purpose}{part}_effects.txt"
        )
        rendered[path] = generated(
            f'''# Purpose shard: {shard.purpose.replace("_", " ")}.
# Boundary contract: 1-10 top-level effects; this file has {len(shard.names)}.

{shard.body}'''
        )
    return rendered


def generated_effect_residue(expected: set[Path]) -> tuple[Path, ...]:
    return tuple(sorted(path for path in EFFECTS_DIR.glob(EFFECT_SHARD_GLOB) if path not in expected))


def render_hidden_event(domain: str, state: int) -> str:
    event = 100 + state - 1 if domain == "ah" else 200 + state - 1
    p = f"zg361_cl_{domain}_s{state:02d}"
    return f'''zg361cl.{event} = {{
    type = character_event
    hidden = yes
    immediate = {{
        {expire_deadline(domain, state)}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            zg361_cl_run_{domain}_stage_{state:02d}_effect = {{
                TICKET_OWNER = var:{p}_deadline_owner
                TICKET_SUBJECT = var:{p}_deadline_subject
                TICKET_CYCLE = var:{p}_deadline_cycle
                TICKET_CASE = var:{p}_deadline_case
                TICKET_STATE = var:{p}_deadline_state
            }}
        }}
        else = {{ debug_log = "ZG361CL: stale {domain.upper()} stage {state} deadline ignored" }}
    }}
}}'''


def render_obligation_event(row: Mechanism) -> str:
    return f'''zg361cl.{obligation_event_id(row.mechanism_id)} = {{
    type = character_event
    hidden = yes
    immediate = {{
        zg361_cl_m{row.mechanism_id:03d}_resolve_obligation_effect = yes
    }}
}}'''


def render_subject_response_event(row: Mechanism) -> str:
    p = f"zg361_cl_m{row.mechanism_id:03d}"
    v = case_vars(row.domain)
    prompt_guard = f'''zg361_case_kernel_full_guard_trigger = {{
            OWNER_VAR = {v["owner"]}
            SUBJECT_VAR = {v["subject"]}
            CYCLE_VAR = {v["cycle"]}
            CASE_VAR = {v["case"]}
            STATE_VAR = {v["state"]}
            ACTIVE_VAR = {v["active"]}
            EXPECTED_OWNER = var:{p}_prompt_owner
            EXPECTED_SUBJECT = var:{p}_prompt_subject
            EXPECTED_CYCLE = var:{p}_prompt_cycle
            EXPECTED_CASE = var:{p}_prompt_case
            EXPECTED_STATE = var:{p}_prompt_state
        }}'''

    def option(route: int) -> str:
        return f'''option = {{
        name = {p}_route_{"a" if route == 1 else "b"}
        zg361_cl_m{row.mechanism_id:03d}_subject_response_effect = {{
            ROUTE = {route}
            TICKET_OWNER = var:{p}_prompt_owner
            TICKET_SUBJECT = var:{p}_prompt_subject
            TICKET_CYCLE = var:{p}_prompt_cycle
            TICKET_CASE = var:{p}_prompt_case
            TICKET_STATE = var:{p}_prompt_state
        }}
        if = {{
            limit = {{
                var:zg361_cl_subject_response_applied = 1
                var:{p}_subject_response = {route}
            }}
            remove_variable = {p}_prompt_pending
            zg361_cl_run_{row.domain}_stage_{row.state:02d}_effect = {{
                TICKET_OWNER = var:{p}_prompt_owner
                TICKET_SUBJECT = var:{p}_prompt_subject
                TICKET_CYCLE = var:{p}_prompt_cycle
                TICKET_CASE = var:{p}_prompt_case
                TICKET_STATE = var:{p}_prompt_state
            }}
        }}
        else = {{
            remove_variable = {p}_prompt_pending
            zg361_cl_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}
        }}
    }}'''

    return f'''# Player assessed-subject response; count/baron need no manager gate.
zg361cl.{row.mechanism_id} = {{
    type = character_event
    title = {p}_title
    desc = zg361_cl_subject_prompt_desc
    theme = stewardship
    trigger = {{
        is_ai = no
        var:{p}_prompt_pending = 1
        {prompt_guard}
    }}
    {option(1)}
    {option(2)}
}}'''


def render_events() -> bytes:
    stage_hidden = "\n\n".join(
        render_hidden_event(domain, state)
        for domain in ("ah", "ai")
        for state in range(1, len(STAGES[domain]) + 1)
    )
    obligation_hidden = "\n\n".join(render_obligation_event(row) for row in MECHANISMS)
    subject_visible = "\n\n".join(
        render_subject_response_event(row)
        for row in MECHANISMS
        if row.mechanism_id in SUBJECT_RESPONSE_IDS
    )
    body = f'''
namespace = zg361cl

{stage_hidden}

{obligation_hidden}

{subject_visible}

# One manager digest remains batched; assessed-player responses above are the
# six intentional exceptions.  Authorized AI owners never enter this card.
zg361cl.390 = {{
    type = character_event
    title = zg361_cl_digest_title
    desc = zg361_cl_digest_desc
    theme = stewardship
    trigger = {{ is_ai = no }}
    option = {{
        name = zg361_cl_digest_ack
        remove_variable = zg361_cl_digest_pending
    }}
}}
'''
    return generated(body)


def localization_entries(chinese: bool) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if chinese:
        entries.extend(
            (
                ("zg361_cl_digest_title", "人才流动与学习账本已合批"),
                ("zg361_cl_digest_desc", "这次没有二十二封弹窗排队敲门。内部流动案 [ROOT.Var('zg361_cl_portfolio_ah_completed')|0] 件，学习案 [ROOT.Var('zg361_cl_portfolio_ai_completed')|0] 件，已按收据、期限与资源账本收口。"),
                ("zg361_cl_digest_ack", "很好，至少日报只写一封。"),
                ("zg361_cl_route_defer", "先记制度债，下轮再议"),
                ("zg361_cl_subject_prompt_desc", "这是关于你本人的内部流动或学习安排。你可以接受，也可以明确拒绝；回应不会让你获得考核他人的权限。"),
            )
        )
    else:
        entries.extend(
            (
                ("zg361_cl_digest_title", "Career and Learning Ledger Batched"),
                ("zg361_cl_digest_desc", "Twenty-two popups did not line up at the door. [ROOT.Var('zg361_cl_portfolio_ah_completed')|0] mobility cases and [ROOT.Var('zg361_cl_portfolio_ai_completed')|0] learning cases closed through receipts, deadlines, and conserved resources."),
                ("zg361_cl_digest_ack", "Good. One status mail is enough."),
                ("zg361_cl_route_defer", "Record policy debt and revisit next cycle"),
                ("zg361_cl_subject_prompt_desc", "This internal-mobility or learning choice concerns you. Accept or decline explicitly; answering grants no authority to review anyone else."),
            )
        )
    for row in MECHANISMS:
        if chinese:
            title, route_a, route_b = row.title_zh, row.route_a_zh, row.route_b_zh
        else:
            title, route_a, route_b = row.title_en, row.route_a_en, row.route_b_en
        entries.extend(
            (
                (f"zg361_cl_m{row.mechanism_id:03d}_title", title),
                (f"zg361_cl_m{row.mechanism_id:03d}_route_a", route_a),
                (f"zg361_cl_m{row.mechanism_id:03d}_route_b", route_b),
                (f"zg361_cl_m{row.mechanism_id:03d}_route_c", "先记制度债，下轮再议" if chinese else "Record policy debt and revisit next cycle"),
            )
        )
    return entries


def render_localization(header: str, *, chinese: bool) -> bytes:
    lines = [f"{header}:"]
    for key, value in localization_entries(chinese):
        escaped = value.replace('"', '\\"')
        lines.append(f' {key}:0 "{escaped}"')
    return localized("\n".join(lines))


def outputs() -> dict[Path, bytes]:
    rendered = effect_shard_outputs()
    rendered[MOD_ROOT / "events/zg361_career_learning_runtime_events.txt"] = render_events()
    for folder, header in LANGUAGES:
        rendered[MOD_ROOT / f"localization/{folder}/zg361_career_learning_l_{folder}.yml"] = render_localization(
            header,
            chinese=folder == "simp_chinese",
        )
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    validate_data()
    rendered = outputs()
    expected_effects = {path for path in rendered if path.parent == EFFECTS_DIR}
    residue = generated_effect_residue(expected_effects)
    if args.check:
        stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
        if stale or residue:
            for path in stale:
                print(f"STALE {path.relative_to(MOD_ROOT)}")
            for path in residue:
                print(f"LEGACY_OR_UNEXPECTED {path.relative_to(MOD_ROOT)}")
            return 1
        print(
            f"career-learning runtime current: {len(MECHANISMS)} mechanisms, "
            f"{len(expected_effects)} purpose shards, max {MAX_EFFECTS_PER_SHARD} effects each"
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
        print(path.relative_to(MOD_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
