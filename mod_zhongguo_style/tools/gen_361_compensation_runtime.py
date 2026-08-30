#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the L/AE/AF compensation and LTI CK3 runtime.

The generator owns only new compensation files.  It binds the already-frozen
shared case kernel without editing that kernel, B1/B2, the scoreboard, or any
central on_action.  Public entry effects are intentionally callable from a
later integration hook or from a controlled fixture.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_compensation_runtime.py\n"


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: int
    domain: str
    title_en: str
    title_cn: str
    behavior: str


@dataclass(frozen=True)
class DomainSpec:
    key: str
    stages: tuple[tuple[int, ...], ...]
    states: tuple[str, ...]
    title_en: str
    title_cn: str


MECHANISMS = (
    Mechanism(82, "l", "Total Reward Formula", "总回报公式", "total_reward_quote"),
    Mechanism(83, "l", "Realm, Team, and Individual Bonus Multipliers", "天朝、团队与个人奖金系数", "three_factor_bonus"),
    Mechanism(84, "l", "Deferred Bonus and Vesting", "递延奖金与兑现", "grant_bonus"),
    Mechanism(85, "l", "Retention Incentive Cliff", "留任激励断崖", "retention_cliff_gap"),
    Mechanism(86, "l", "Bonus Holdback and Clawback", "奖金暂扣与追回", "hold_and_clawback_bonus"),
    Mechanism(87, "l", "Pay Bands and Position Within Band", "薪带与带内位置", "pay_band_position"),
    Mechanism(88, "l", "Market Raises Versus Performance Raises", "市场调薪与绩效调薪", "allocate_raise_pool"),
    Mechanism(89, "l", "Decoupling Rank, Appointment, Authority, and Cash", "品级、任命、权力与现金解耦", "career_package"),
    Mechanism(90, "l", "Spot Awards", "专项即时奖", "pay_spot_award"),
    Mechanism(91, "l", "Separate Tenure and Performance Awards", "年功奖与绩效奖分账", "separate_award_accounts"),
    Mechanism(278, "ae", "Annual Total-Compensation Reconciliation", "年度总薪酬对账", "pay_statement"),
    Mechanism(279, "ae", "Contract Status of an Extra Month's Salary", "额外月俸合同属性", "extra_month_contract"),
    Mechanism(280, "ae", "Midyear Entry, Transfer, and Exit Proration", "年中入转离折算", "prorate_award"),
    Mechanism(281, "ae", "Bonus Payment Date and Deferral Credibility", "奖金支付日与延期信用", "defer_statement"),
    Mechanism(282, "ae", "Raise Effective Date and Retroactive True-Up", "调薪生效日与追溯补发", "apply_backpay"),
    Mechanism(283, "ae", "Deadline for a Dry Promotion", "干升职兑现期限", "dry_promotion_commitment"),
    Mechanism(284, "ae", "Pay-Buffer Slope After Demotion", "降职后薪酬缓冲坡", "demotion_pay_schedule"),
    Mechanism(285, "ae", "Second Calibration of Raises Within a Rating", "同档调薪二次校准", "allocate_raise_pool"),
    Mechanism(286, "ae", "Above-Band Freeze and Below-Band Catch-Up", "带上冻结与带下追赶", "band_correction"),
    Mechanism(287, "ae", "Pay Secrecy, Public Bands, or Anonymous Distribution", "密薪、公开带宽与匿名分布", "pay_visibility"),
    Mechanism(288, "ae", "Repairing New-Hire Pay Inversion", "修复新老薪酬倒挂", "repair_pay_inversion"),
    Mechanism(289, "ae", "Separate Pay Appeals from Rating Appeals", "薪酬申诉与绩效申诉分轨", "compensation_appeal"),
    Mechanism(290, "af", "Long-Term Award Nomination Pool", "长期激励提名池", "select_lti_nominations"),
    Mechanism(291, "af", "Fixed Shares Versus Fixed Grant Value", "固定份额与固定授予价值", "grant_units"),
    Mechanism(292, "af", "High-Risk Options Versus Restricted Units", "高风险期权与限制份额", "risk_award_choice"),
    Mechanism(293, "af", "Voluntary Bonus Conversion into Long-Term Units", "自愿奖金转长期份额", "convert_bonus_to_units"),
    Mechanism(294, "af", "Grant Price, Current Valuation, and Liquid Value", "授予价、现值与可变现值", "valuation_columns"),
    Mechanism(295, "af", "Length of the Initial Vesting Cliff", "首次归属断崖长度", "lti_cliff"),
    Mechanism(296, "af", "Monthly, Quarterly, or Annual Vesting", "月度、季度或年度归属", "lti_cadence"),
    Mechanism(297, "af", "Separate Service and Performance Vesting", "服务与绩效归属分轨", "lti_tracks"),
    Mechanism(298, "af", "Organization and Individual Vesting Gates", "组织与个人双归属门槛", "lti_double_gate"),
    Mechanism(299, "af", "Good-Leaver and Bad-Leaver Classification", "善意与恶意离任分类", "classify_lti_leaver"),
    Mechanism(300, "af", "Buyback Window and Liquidity Queue", "回购窗口与流动性队列", "settle_repurchase"),
)

DOMAINS = (
    DomainSpec(
        "l",
        ((82, 83, 84), (85, 86), (87, 88, 89), (90, 91)),
        ("formula_locked", "funds_reserved", "granted", "held", "settled"),
        "Compensation award",
        "薪酬与奖金",
    ),
    DomainSpec(
        "ae",
        ((278, 279, 280), (281, 282), (283, 284, 285), (286, 287), (288, 289)),
        ("payable", "due", "decided", "corrected", "appealed", "closed"),
        "Pay statement",
        "薪酬单",
    ),
    DomainSpec(
        "af",
        ((290, 291, 292), (293, 294), (295, 296), (297, 298), (299, 300)),
        ("nominated", "granted", "cliff_reached", "vesting", "exit_classified", "settled"),
        "Long-term incentive",
        "长期激励",
    ),
)

EXPECTED_IDS = tuple((*range(82, 92), *range(278, 301)))
MECHANISM_BY_ID = {row.mechanism_id: row for row in MECHANISMS}
DOMAIN_BY_ID = {
    mechanism_id: domain
    for domain in DOMAINS
    for stage in domain.stages
    for mechanism_id in stage
}
STAGE_BY_ID = {
    mechanism_id: state
    for domain in DOMAINS
    for state, stage in enumerate(domain.stages, start=1)
    for mechanism_id in stage
}
FINANCIAL_IDS = frozenset({84, 86, 90, 281, 282, 289, 292, 300})
RESULT_GRADE_RATINGS = {1: 325, 2: 350, 3: 375}


def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def validate_specs() -> None:
    if tuple(sorted(MECHANISM_BY_ID)) != EXPECTED_IDS:
        raise ValueError("compensation runtime must cover exact 082-091/278-300")
    if len(MECHANISMS) != 33 or len(MECHANISM_BY_ID) != 33:
        raise ValueError("compensation runtime ID count drifted")
    if tuple(sorted(DOMAIN_BY_ID)) != EXPECTED_IDS:
        raise ValueError("domain stage partition drifted")
    if {row.key for row in DOMAINS} != {"l", "ae", "af"}:
        raise ValueError("runtime may own only L/AE/AF")
    if any(len(row.states) != len(row.stages) + 1 for row in DOMAINS):
        raise ValueError("each domain needs one explicit state on both sides of every stage")
    if RESULT_GRADE_RATINGS != {1: 325, 2: 350, 3: 375}:
        raise ValueError("result grade/rating projection drifted")


def vars_for(domain: str) -> dict[str, str]:
    p = f"zg361_case_{domain}"
    return {
        "owner": f"{p}_owner",
        "subject": f"{p}_subject",
        "cycle": f"{p}_cycle_serial",
        "case": f"{p}_case_serial",
        "state": f"{p}_state",
        "active": f"{p}_active",
        "revision": f"{p}_revision",
        "timeline": f"{p}_timeline_serial",
        "feedback": f"{p}_feedback_revision",
    }


def full_guard(domain: str, state: int, *, owner: str) -> str:
    row = vars_for(domain)
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
    row = vars_for(domain)
    p = f"zg361_comp_m{mechanism_id:03d}"
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
            LAST_OPERATION_VAR = zg361_comp_{domain}_last_operation
            LAST_CHOICE_VAR = zg361_comp_{domain}_last_route
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
            CHOICE = scope:zg361_comp_route
            OPERATION_ID = {mechanism_id}
        }}'''


def journal_reserve(domain: str, state: int, prefix: str, resource: str, amount: str) -> str:
    row = vars_for(domain)
    return f'''zg361_case_kernel_reserve_transaction_effect = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                REVISION_VAR = {row["revision"]}
                AVAILABLE_VAR = zg361_comp_{domain}_{resource}_available
                RESERVED_VAR = zg361_comp_{domain}_{resource}_reserved
                RECEIPT_AMOUNT_VAR = {prefix}_{resource}_amount
                RECEIPT_STATUS_VAR = {prefix}_{resource}_status
                RECEIPT_OWNER_VAR = {prefix}_{resource}_owner
                RECEIPT_CYCLE_VAR = {prefix}_{resource}_cycle
                RECEIPT_CASE_VAR = {prefix}_{resource}_case
                TICKET_OWNER = var:{row["owner"]}
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:{row["cycle"]}
                TICKET_CASE = var:{row["case"]}
                TICKET_STATE = {state}
                AMOUNT = {amount}
            }}'''


def journal_settle(domain: str, state: int, prefix: str, resource: str) -> str:
    row = vars_for(domain)
    return f'''zg361_case_kernel_settle_transaction_effect = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                REVISION_VAR = {row["revision"]}
                RESERVED_VAR = zg361_comp_{domain}_{resource}_reserved
                SETTLED_VAR = zg361_comp_{domain}_{resource}_settled
                RECEIPT_AMOUNT_VAR = {prefix}_{resource}_amount
                RECEIPT_STATUS_VAR = {prefix}_{resource}_status
                TICKET_OWNER = var:{row["owner"]}
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:{row["cycle"]}
                TICKET_CASE = var:{row["case"]}
                TICKET_STATE = {state}
            }}'''


def journal_refund(domain: str, state: int, prefix: str, resource: str) -> str:
    row = vars_for(domain)
    return f'''zg361_case_kernel_refund_transaction_effect = {{
                OWNER_VAR = {row["owner"]}
                SUBJECT_VAR = {row["subject"]}
                CYCLE_VAR = {row["cycle"]}
                CASE_VAR = {row["case"]}
                STATE_VAR = {row["state"]}
                ACTIVE_VAR = {row["active"]}
                REVISION_VAR = {row["revision"]}
                AVAILABLE_VAR = zg361_comp_{domain}_{resource}_available
                RESERVED_VAR = zg361_comp_{domain}_{resource}_reserved
                SETTLED_VAR = zg361_comp_{domain}_{resource}_settled
                RECEIPT_AMOUNT_VAR = {prefix}_{resource}_amount
                RECEIPT_STATUS_VAR = {prefix}_{resource}_status
                TICKET_OWNER = var:{row["owner"]}
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:{row["cycle"]}
                TICKET_CASE = var:{row["case"]}
                TICKET_STATE = {state}
            }}'''


def freeze_cash_identities(prefix: str, domain: str, state: int) -> str:
    row = vars_for(domain)
    return f'''set_variable = {{ name = {prefix}_treasury_payer value = var:{row["owner"]} }}
            set_variable = {{ name = {prefix}_personal_payer value = var:{row["owner"]} }}
            set_variable = {{ name = {prefix}_recipient value = this }}
            set_variable = {{ name = {prefix}_approver value = var:{row["owner"]} }}
            set_variable = {{ name = {prefix}_frozen_owner value = var:{row["owner"]} }}
            set_variable = {{ name = {prefix}_frozen_subject value = this }}
            set_variable = {{ name = {prefix}_frozen_cycle value = var:{row["cycle"]} }}
            set_variable = {{ name = {prefix}_frozen_case value = var:{row["case"]} }}
            set_variable = {{ name = {prefix}_frozen_state value = {state} }}'''


def render_fixed_dual_payment(
    name: str,
    domain: str,
    state: int,
    prefix: str,
    treasury_amount: int,
    personal_amount: int,
) -> str:
    total = treasury_amount + personal_amount
    row = vars_for(domain)
    return f'''{name} = {{
    remove_variable = zg361_comp_financial_applied
    {journal_reserve(domain, state, prefix, "treasury", str(treasury_amount))}
    if = {{
        limit = {{ var:zg361_case_kernel_applied = 1 }}
        {journal_reserve(domain, state, prefix, "personal", str(personal_amount))}
    }}
    if = {{
        limit = {{
            var:{prefix}_treasury_status = 1
            var:{prefix}_personal_status = 1
        }}
        {journal_settle(domain, state, prefix, "treasury")}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {journal_settle(domain, state, prefix, "personal")}
        }}
    }}
    if = {{
        limit = {{
            var:{prefix}_treasury_status = 2
            var:{prefix}_personal_status = 2
        }}
        var:{row["owner"]} = {{
            remove_treasury = {treasury_amount}
            add_gold = {{ value = 0 subtract = {personal_amount} }}
        }}
        add_gold = {total}
        {freeze_cash_identities(prefix, domain, state)}
        set_variable = {{ name = {prefix}_gross value = {total} }}
        set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
    }}
}}'''


def render_dynamic_dual_payment(
    name: str,
    domain: str,
    state: int,
    prefix: str,
    treasury_scope: str,
    personal_scope: str,
    gross_scope: str,
) -> str:
    row = vars_for(domain)
    return f'''{name} = {{
    remove_variable = zg361_comp_financial_applied
    {journal_reserve(domain, state, prefix, "treasury", treasury_scope)}
    if = {{
        limit = {{ var:zg361_case_kernel_applied = 1 }}
        {journal_reserve(domain, state, prefix, "personal", personal_scope)}
    }}
    if = {{
        limit = {{
            var:{prefix}_treasury_status = 1
            var:{prefix}_personal_status = 1
        }}
        {journal_settle(domain, state, prefix, "treasury")}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {journal_settle(domain, state, prefix, "personal")}
        }}
    }}
    if = {{
        limit = {{
            var:{prefix}_treasury_status = 2
            var:{prefix}_personal_status = 2
        }}
        var:{row["owner"]} = {{
            remove_treasury = {{ value = {treasury_scope} }}
            add_gold = {{ value = 0 subtract = {personal_scope} }}
        }}
        add_gold = {{ value = {gross_scope} }}
        {freeze_cash_identities(prefix, domain, state)}
        set_variable = {{ name = {prefix}_gross value = {gross_scope} }}
        set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
    }}
}}'''


def special_payload(mechanism_id: int) -> str:
    """Behavior-specific write consumed by the next stage or final resolver."""

    p = f"zg361_comp_m{mechanism_id:03d}"
    payloads = {
        82: f'''set_variable = {{ name = {p}_fixed_pay value = 12 }}
            set_variable = {{ name = {p}_role_allowance value = 3 }}
            set_variable = {{ name = {p}_performance_bonus value = 20 }}
            set_variable = {{ name = {p}_spot_award value = 10 }}
            set_variable = {{ name = {p}_deferred_award value = 6 }}
            set_variable = {{ name = {p}_total_reward value = 51 }}''',
        83: f'''set_variable = {{ name = {p}_realm_bps value = 10000 }}
            set_variable = {{ name = {p}_team_bps value = 10000 }}
            set_variable = {{ name = {p}_individual_bps value = 10000 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_individual_bps value = 8000 }} }}
            set_variable = {{ name = {p}_formula_version value = 1 }}''',
        84: f'''set_variable = {{ name = {p}_formula_locked value = 1 }}
            set_variable = {{ name = {p}_reserve_receipt value = var:zg361_case_l_case_serial }}
            set_variable = {{ name = {p}_deferred_due_year value = {{ value = current_year add = 1 }} }}''',
        85: f'''set_variable = {{ name = {p}_last_vest_year value = current_year }}
            set_variable = {{ name = {p}_next_grant_year value = 0 }}
            if = {{ limit = {{ var:{p}_route = 1 }} set_variable = {{ name = {p}_next_grant_year value = {{ value = current_year add = 2 }} }} }}
            set_variable = {{ name = {p}_cliff_gap_years value = 0 }}
            if = {{ limit = {{ var:{p}_next_grant_year > 0 }} set_variable = {{ name = {p}_cliff_gap_years value = {{ value = var:{p}_next_grant_year subtract = var:{p}_last_vest_year }} }} }}''',
        86: f'''set_variable = {{ name = {p}_hold_policy value = var:{p}_route }}
            set_variable = {{ name = {p}_clawback_source_receipt value = var:zg361_comp_bonus_immediate_receipt_serial }}
            set_variable = {{ name = {p}_clawback_limit value = 2 }}''',
        87: f'''set_variable = {{ name = {p}_band_min value = 10 }}
            set_variable = {{ name = {p}_band_max value = 20 }}
            set_variable = {{ name = {p}_salary value = 15 }}
            set_variable = {{ name = {p}_position_bps value = 5000 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_position_bps value = 11000 }} }}''',
        88: f'''set_variable = {{ name = {p}_raise_pool value = 10 }}
            set_variable = {{ name = {p}_market_allocation value = 4 }}
            set_variable = {{ name = {p}_merit_allocation value = 3 }}
            set_variable = {{ name = {p}_fairness_allocation value = 3 }}
            set_variable = {{ name = {p}_allocation_total value = 10 }}''',
        89: f'''set_variable = {{ name = {p}_grade_level value = 4 }}
            set_variable = {{ name = {p}_appointment_code value = var:{p}_route }}
            set_variable = {{ name = {p}_authority value = 1 }}
            set_variable = {{ name = {p}_cash_raise value = 0 }}''',
        90: f'''set_variable = {{ name = {p}_spot_gross value = 0 }}
            if = {{ limit = {{ OR = {{ var:{p}_route = 1 var:{p}_route = 2 }} }} set_variable = {{ name = {p}_spot_gross value = 10 }} }}
            set_variable = {{ name = {p}_performance_slot_delta value = 0 }}''',
        91: f'''set_variable = {{ name = {p}_tenure_award value = 3 }}
            set_variable = {{ name = {p}_performance_award value = 7 }}
            set_variable = {{ name = {p}_award_total value = 10 }}''',
        278: f'''set_variable = {{ name = {p}_promised value = var:zg361_comp_ae_statement_payable }}
            set_variable = {{ name = {p}_paid value = var:zg361_comp_ae_statement_paid }}
            set_variable = {{ name = {p}_owed value = var:zg361_comp_ae_statement_owed }}
            set_variable = {{ name = {p}_returned value = var:zg361_comp_ae_statement_returned }}''',
        279: f'''set_variable = {{ name = {p}_contract_kind value = var:{p}_route }}
            set_variable = {{ name = {p}_locked_cycle value = var:zg361_case_ae_cycle_serial }}
            set_variable = {{ name = {p}_amount value = 6 }}''',
        280: f'''set_variable = {{ name = {p}_rule value = var:{p}_route }}
            set_variable = {{ name = {p}_service_months value = 12 }}
            set_variable = {{ name = {p}_proration_bps value = 10000 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_proration_bps value = 5000 }} }}
            else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_proration_bps value = 0 }} }}''',
        281: f'''set_variable = {{ name = {p}_decision value = var:{p}_route }}
            if = {{ limit = {{ var:{p}_route = 1 }}
                set_variable = {{ name = {p}_paid_amount value = scope:zg361_comp_due_gross }}
                change_variable = {{ name = zg361_comp_ae_statement_paid add = scope:zg361_comp_due_gross }}
                set_variable = {{ name = zg361_comp_ae_statement_owed value = 0 }}
                set_variable = {{ name = zg361_comp_ae_due_resolved value = 1 }}
            }}
            else = {{
                change_variable = {{ name = zg361_comp_ae_delay_count add = 1 }}
                change_variable = {{ name = zg361_comp_ae_credibility add = {{ value = 0 subtract = 15 }} }}
                set_variable = {{ name = {p}_new_due_days value = 90 }}
                if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_new_due_days value = 180 }} }}
                set_variable = {{ name = zg361_comp_ae_due_resolved value = 0 }}
            }}''',
        282: f'''set_variable = {{ name = {p}_reason_code value = var:{p}_route }}
            set_variable = {{ name = {p}_backpay value = 0 }}
            if = {{ limit = {{ var:{p}_route = 1 }}
                set_variable = {{ name = {p}_backpay value = 4 }}
                change_variable = {{ name = zg361_comp_ae_statement_payable add = 4 }}
                change_variable = {{ name = zg361_comp_ae_statement_paid add = 4 }}
            }}
            else_if = {{ limit = {{ var:{p}_route = 2 }}
                set_variable = {{ name = {p}_backpay value = 4 }}
                change_variable = {{ name = zg361_comp_ae_statement_payable add = 4 }}
                change_variable = {{ name = zg361_comp_ae_statement_owed add = 4 }}
            }}''',
        283: f'''set_variable = {{ name = {p}_responsibility_cycle value = var:zg361_case_ae_cycle_serial }}
            set_variable = {{ name = {p}_cash_due_cycle value = {{ value = var:zg361_case_ae_cycle_serial add = 1 }} }}
            set_variable = {{ name = {p}_cash_raise value = 4 }}''',
        284: f'''set_variable = {{ name = {p}_current_pay value = 20 }}
            set_variable = {{ name = {p}_target_pay value = 16 }}
            set_variable = {{ name = {p}_steps value = 2 }}
            set_variable = {{ name = {p}_professional_pay_preserved value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_professional_pay_preserved value = 1 }} }}''',
        285: f'''set_variable = {{ name = {p}_frozen_grade value = var:zg361_comp_result_rating }}
            set_variable = {{ name = {p}_raise_pool value = 10 }}
            set_variable = {{ name = {p}_band_debt_allocation value = 6 }}
            set_variable = {{ name = {p}_scarcity_allocation value = 4 }}
            set_variable = {{ name = {p}_allocation_total value = 10 }}''',
        286: f'''set_variable = {{ name = {p}_fixed_raise value = 0 }}
            set_variable = {{ name = {p}_one_time_bonus value = 0 }}
            set_variable = {{ name = {p}_exception_expiry_cycle value = 0 }}
            if = {{ limit = {{ var:{p}_route = 1 }} set_variable = {{ name = {p}_fixed_raise value = 4 }} }}
            else_if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_one_time_bonus value = 4 }} set_variable = {{ name = {p}_exception_expiry_cycle value = {{ value = var:zg361_case_ae_cycle_serial add = 1 }} }} }}''',
        287: f'''set_variable = {{ name = {p}_visibility_mode value = var:{p}_route }}
            set_variable = {{ name = {p}_named_peer_salary_visible value = 0 }}
            set_variable = {{ name = {p}_own_salary_visible value = 1 }}''',
        288: f'''set_variable = {{ name = {p}_incumbent_salary value = 15 }}
            set_variable = {{ name = {p}_new_hire_salary value = 18 }}
            set_variable = {{ name = {p}_scarcity_allowance value = 1 }}
            set_variable = {{ name = {p}_repair_due value = 2 }}''',
        289: f'''set_variable = {{ name = {p}_appeal_track value = 1 }}
            set_variable = {{ name = {p}_frozen_performance_grade value = var:zg361_comp_ae_frozen_performance_grade }}
            set_variable = {{ name = {p}_outcome value = var:{p}_route }}
            if = {{ limit = {{ var:{p}_route = 1 }}
                change_variable = {{ name = zg361_comp_ae_statement_payable add = 4 }}
                change_variable = {{ name = zg361_comp_ae_statement_paid add = 4 }}
            }}''',
        290: f'''set_variable = {{ name = {p}_result_owner value = var:zg361_comp_result_owner }}
            set_variable = {{ name = {p}_result_subject value = var:zg361_comp_result_subject }}
            set_variable = {{ name = {p}_result_cycle value = var:zg361_comp_result_cycle }}
            set_variable = {{ name = {p}_result_case value = var:zg361_comp_result_case }}
            set_variable = {{ name = {p}_result_state value = var:zg361_comp_result_state }}
            set_variable = {{ name = {p}_result_grade value = var:zg361_comp_result_grade }}
            set_variable = {{ name = {p}_rating value = var:zg361_comp_result_rating }}
            set_variable = {{ name = {p}_eligible value = 0 }}
            if = {{ limit = {{ var:{p}_result_grade = 3 var:{p}_rating = 375 }} set_variable = {{ name = {p}_eligible value = 1 }} }}
            set_variable = {{ name = {p}_nomination_score value = 10 }}''',
        291: f'''set_variable = {{ name = {p}_grant_measure value = var:{p}_route }}
            set_variable = {{ name = zg361_comp_af_grant_base_units value = 0 }}
            if = {{
                limit = {{ var:zg361_comp_m290_eligible = 1 }}
                set_variable = {{ name = zg361_comp_af_grant_base_units value = 100 }}
                if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = zg361_comp_af_grant_base_units value = 80 }} }}
                else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = zg361_comp_af_grant_base_units value = 60 }} }}
            }}''',
        292: f'''set_variable = {{ name = {p}_risk_kind value = var:{p}_route }}
            set_variable = {{ name = {p}_cash_alternative value = 0 }}
            set_variable = {{ name = {p}_can_expire_worthless value = 0 }}
            if = {{ limit = {{ var:{p}_route = 1 }} set_variable = {{ name = {p}_can_expire_worthless value = 1 }} }}
            else_if = {{
                limit = {{ var:{p}_route = 3 }}
                set_variable = {{ name = zg361_comp_af_grant_base_units value = 0 }}
                if = {{ limit = {{ var:zg361_comp_m290_eligible = 1 }} set_variable = {{ name = {p}_cash_alternative value = 10 }} }}
            }}''',
        293: f'''set_variable = {{ name = {p}_voluntary value = 0 }}
            set_variable = {{ name = {p}_converted_cash value = 0 }}
            set_variable = {{ name = zg361_comp_af_conversion_units value = 0 }}
            set_variable = {{ name = {p}_cash_remaining value = 10 }}
            if = {{ limit = {{ var:{p}_route = 1 var:zg361_comp_m290_eligible = 1 }}
                set_variable = {{ name = {p}_voluntary value = 1 }}
                set_variable = {{ name = {p}_converted_cash value = 4 }}
                set_variable = {{ name = zg361_comp_af_conversion_units value = 4 }}
                set_variable = {{ name = {p}_cash_remaining value = 6 }}
            }}''',
        294: f'''set_variable = {{ name = {p}_grant_price value = 1 }}
            set_variable = {{ name = {p}_current_price value = 2 }}
            set_variable = {{ name = {p}_liquidity_bps value = 5000 }}
            set_variable = {{ name = {p}_grant_value value = var:zg361_comp_af_total_units }}
            set_variable = {{ name = {p}_current_value value = {{ value = var:zg361_comp_af_total_units multiply = 2 }} }}
            set_variable = {{ name = {p}_liquid_value value = var:zg361_comp_af_total_units }}''',
        295: f'''set_variable = {{ name = {p}_cliff_days value = 365 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_cliff_days value = 180 }} }}
            else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_cliff_days value = 730 }} }}
            set_variable = {{ name = zg361_comp_af_cliff_days value = var:{p}_cliff_days }}''',
        296: f'''set_variable = {{ name = {p}_cadence_days value = 30 }}
            set_variable = {{ name = {p}_vesting_periods value = 12 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_cadence_days value = 90 }} set_variable = {{ name = {p}_vesting_periods value = 4 }} }}
            else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_cadence_days value = 365 }} set_variable = {{ name = {p}_vesting_periods value = 1 }} }}
            set_variable = {{ name = zg361_comp_af_cadence_days value = var:{p}_cadence_days }}
            set_variable = {{ name = zg361_comp_af_vesting_periods value = var:{p}_vesting_periods }}''',
        297: f'''set_variable = {{ name = {p}_service_bps value = 5000 }}
            set_variable = {{ name = {p}_performance_bps value = 5000 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_service_bps value = 7000 }} set_variable = {{ name = {p}_performance_bps value = 3000 }} }}
            else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_service_bps value = 10000 }} set_variable = {{ name = {p}_performance_bps value = 0 }} }}''',
        298: f'''set_variable = {{ name = {p}_organization_gate value = 1 }}
            set_variable = {{ name = {p}_individual_gate value = 1 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_individual_gate value = 0 }} }}
            else_if = {{ limit = {{ var:{p}_route = 3 }} set_variable = {{ name = {p}_organization_gate value = 0 }} set_variable = {{ name = {p}_individual_gate value = 0 }} }}''',
        299: f'''set_variable = {{ name = {p}_leaver_class value = var:{p}_route }}
            set_variable = {{ name = {p}_good_leaver_acceleration value = 0 }}
            set_variable = {{ name = {p}_vested_preserved value = var:zg361_comp_af_vested_units }}
            if = {{ limit = {{ OR = {{ var:{p}_route = 1 var:{p}_route = 2 }} }}
                change_variable = {{ name = zg361_comp_af_forfeited_units add = var:zg361_comp_af_unvested_service }}
                change_variable = {{ name = zg361_comp_af_forfeited_units add = var:zg361_comp_af_unvested_performance }}
                set_variable = {{ name = zg361_comp_af_unvested_service value = 0 }}
                set_variable = {{ name = zg361_comp_af_unvested_performance value = 0 }}
            }}
            set_variable = {{ name = {p}_clawback_eligible value = 0 }}
            if = {{ limit = {{ var:{p}_route = 2 }} set_variable = {{ name = {p}_clawback_eligible value = 1 }} }}''',
        300: f'''set_variable = {{ name = {p}_window_open value = 0 }}
            set_variable = {{ name = {p}_requested_units value = 0 }}
            if = {{ limit = {{ OR = {{ var:{p}_route = 1 var:{p}_route = 2 }} }}
                set_variable = {{ name = {p}_window_open value = 1 }}
                set_variable = {{ name = {p}_requested_units value = 10 }}
            }}''',
    }
    return payloads[mechanism_id]


def recalculate_statement_call(mechanism_id: int) -> str:
    return (
        "zg361_comp_ae_recalculate_statement_effect = yes"
        if 278 <= mechanism_id <= 289
        else ""
    )


def recalculate_lti_call(mechanism_id: int) -> str:
    if mechanism_id in {291, 292, 293, 297}:
        return "zg361_comp_af_recalculate_units_effect = yes"
    if mechanism_id in {299, 300}:
        return "zg361_comp_af_check_conservation_effect = yes"
    return ""


def post_consumer(mechanism_id: int) -> str:
    if mechanism_id != 300:
        return ""
    owner = vars_for("af")["owner"]
    return f'''if = {{
            limit = {{ OR = {{ var:zg361_comp_m300_route = 1 var:zg361_comp_m300_route = 2 }} }}
            var:{owner} = {{ change_variable = {{ name = zg361_comp_af_queue_tail add = 1 }} }}
            set_variable = {{ name = zg361_comp_af_request_serial value = var:{owner}.var:zg361_comp_af_queue_tail }}
            set_variable = {{ name = zg361_comp_af_request_state value = 1 }}
            set_variable = {{ name = zg361_comp_af_repurchase_resolved value = 0 }}
            if = {{
                limit = {{ var:zg361_comp_m300_route = 1 }}
                change_variable = {{ name = zg361_comp_af_vested_units add = -10 }}
                change_variable = {{ name = zg361_comp_af_repurchased_units add = 10 }}
                set_variable = {{ name = zg361_comp_af_request_state value = 2 }}
                set_variable = {{ name = zg361_comp_af_repurchase_resolved value = 1 }}
                var:{owner} = {{ change_variable = {{ name = zg361_comp_af_queue_head add = 1 }} }}
            }}
            else = {{ {schedule_deadline("af_buyback_90")} }}
        }}
        else = {{ set_variable = {{ name = zg361_comp_af_repurchase_resolved value = 1 }} }}'''


def finance_prelude(mechanism_id: int) -> str:
    if mechanism_id != 281:
        return ""
    return r'''save_temporary_scope_value_as = {
        name = zg361_comp_due_gross
        value = var:zg361_comp_ae_statement_owed
    }
    save_temporary_scope_value_as = {
        name = zg361_comp_due_treasury
        value = { value = scope:zg361_comp_due_gross multiply = 0.7 add = 0.5 floor = yes }
    }
    save_temporary_scope_value_as = {
        name = zg361_comp_due_personal
        value = { value = scope:zg361_comp_due_gross subtract = scope:zg361_comp_due_treasury }
    }'''


def finance_guard(mechanism_id: int, domain: str) -> str:
    p = f"zg361_comp_m{mechanism_id:03d}"
    row = vars_for(domain)
    fixed: dict[int, tuple[str, int, int, str]] = {
        84: (f"NOT = {{ scope:zg361_comp_route = 3 }}", 14, 6, "zg361_comp_bonus_immediate_treasury_status"),
        90: (f"NOT = {{ scope:zg361_comp_route = 3 }}", 7, 3, "zg361_comp_m090_pay_treasury_status"),
        282: ("scope:zg361_comp_route = 1", 3, 1, "zg361_comp_m282_pay_treasury_status"),
        289: ("scope:zg361_comp_route = 1", 3, 1, "zg361_comp_m289_pay_treasury_status"),
        292: ("scope:zg361_comp_route = 3 var:zg361_comp_m290_eligible = 1", 7, 3, "zg361_comp_m292_cash_treasury_status"),
        300: ("scope:zg361_comp_route = 1", 7, 3, "zg361_comp_m300_buyback_treasury_status"),
    }
    if mechanism_id in fixed:
        condition, treasury_amount, personal_amount, status = fixed[mechanism_id]
        extra = ""
        if mechanism_id == 300:
            extra = f'''
                    var:zg361_comp_af_vested_units >= 10
                    var:{row["owner"]} = {{
                        var:zg361_comp_af_queue_tail = var:zg361_comp_af_queue_head
                    }}'''
        return f'''trigger_if = {{
                limit = {{ {condition} }}
                var:{row["owner"]} = {{
                    has_treasury = yes
                    treasury >= {treasury_amount}
                    gold >= {personal_amount}
                }}
                var:zg361_comp_{domain}_treasury_available >= {treasury_amount}
                var:zg361_comp_{domain}_personal_available >= {personal_amount}
                trigger_if = {{
                    limit = {{ has_variable = {status} }}
                    var:{status} = 0
                }}
                trigger_else = {{ always = yes }}{extra}
            }}
            trigger_else = {{ always = yes }}'''
    if mechanism_id == 86:
        return f'''trigger_if = {{
                limit = {{ scope:zg361_comp_route = 2 }}
                var:zg361_comp_bonus_funded = 1
                var:zg361_comp_bonus_immediate_paid >= 2
                var:zg361_comp_bonus_clawback_status = 0
                gold >= 2
                var:{row["owner"]} = {{ has_treasury = yes }}
                var:zg361_comp_bonus_immediate_receipt_owner = var:{row["owner"]}
                var:zg361_comp_bonus_immediate_receipt_subject = this
                var:zg361_comp_bonus_immediate_receipt_cycle = var:{row["cycle"]}
                var:zg361_comp_bonus_immediate_receipt_case = var:{row["case"]}
            }}
            trigger_else = {{ always = yes }}'''
    if mechanism_id == 281:
        return f'''trigger_if = {{
                limit = {{ scope:zg361_comp_route = 1 }}
                scope:zg361_comp_due_gross >= 2
                scope:zg361_comp_due_treasury >= 1
                scope:zg361_comp_due_personal >= 1
                var:{row["owner"]} = {{
                    has_treasury = yes
                    treasury >= scope:zg361_comp_due_treasury
                    gold >= scope:zg361_comp_due_personal
                }}
                var:zg361_comp_ae_treasury_available >= scope:zg361_comp_due_treasury
                var:zg361_comp_ae_personal_available >= scope:zg361_comp_due_personal
            }}
            trigger_else = {{ always = yes }}'''
    if mechanism_id == 300:
        return f'''trigger_if = {{
                limit = {{ NOT = {{ scope:zg361_comp_route = 3 }} }}
                var:zg361_comp_af_vested_units >= 10
            }}
            trigger_else = {{ always = yes }}'''
    return ""


def behavior_guard(mechanism_id: int) -> str:
    if mechanism_id == 289:
        return '''var:zg361_comp_ae_appeal_response_recorded = 1
            trigger_if = {
                limit = { scope:zg361_comp_route = 1 }
                var:zg361_comp_ae_appeal_requested = 1
            }
            trigger_else = { always = yes }'''
    if mechanism_id == 300:
        return '''trigger_if = {
                limit = { NOT = { scope:zg361_comp_route = 3 } }
                var:zg361_comp_af_vested_units >= 10
            }
            trigger_else = { always = yes }'''
    return ""


def finance_apply(mechanism_id: int) -> str:
    calls = {
        84: '''if = {
                limit = { NOT = { scope:zg361_comp_route = 3 } }
                zg361_comp_l_reserve_bonus_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        86: '''if = {
                limit = { scope:zg361_comp_route = 2 }
                zg361_comp_l_clawback_bonus_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        90: '''if = {
                limit = { NOT = { scope:zg361_comp_route = 3 } }
                zg361_comp_l_pay_spot_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        281: '''if = {
                limit = { scope:zg361_comp_route = 1 }
                zg361_comp_ae_pay_due_now_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        282: '''if = {
                limit = { scope:zg361_comp_route = 1 }
                zg361_comp_ae_pay_backpay_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        289: '''if = {
                limit = { scope:zg361_comp_route = 1 }
                zg361_comp_ae_pay_appeal_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        292: '''if = {
                limit = { scope:zg361_comp_route = 3 var:zg361_comp_m290_eligible = 1 }
                zg361_comp_af_pay_cash_alternative_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
        300: '''if = {
                limit = { scope:zg361_comp_route = 1 }
                zg361_comp_af_pay_buyback_now_effect = yes
            }
            else = { set_variable = { name = zg361_comp_financial_applied value = 1 } }''',
    }
    return calls.get(
        mechanism_id,
        "set_variable = { name = zg361_comp_financial_applied value = 1 }",
    )


def render_manager_entry(mechanism_id: int, domain: str, state: int) -> str:
    return f'''zg361_comp_m{mechanism_id:03d}_manager_apply_effect = {{
    remove_variable = zg361_comp_runtime_applied
    if = {{
        limit = {{
            root = {{
                zg361_is_celestial_liege_trigger = yes
                # No is_ai=no gate: the project-authorized AI manager uses this
                # same duke+ background resolver without opening player UI.
            }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            {full_guard(domain, state, owner="root")}
        }}
        zg361_comp_m{mechanism_id:03d}_core_effect = {{ ROUTE = $ROUTE$ }}
    }}
}}'''


def render_core(mechanism_id: int, domain: str, state: int) -> str:
    p = f"zg361_comp_m{mechanism_id:03d}"
    prelude = finance_prelude(mechanism_id)
    guard = finance_guard(mechanism_id, domain)
    business_guard = behavior_guard(mechanism_id)
    finance = finance_apply(mechanism_id)
    return f'''# {mechanism_id:03d} {MECHANISM_BY_ID[mechanism_id].title_cn}
zg361_comp_m{mechanism_id:03d}_core_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_comp_route value = $ROUTE$ }}
    remove_variable = zg361_comp_runtime_applied
    remove_variable = zg361_comp_financial_applied
    {prelude}
    if = {{
        limit = {{
            OR = {{
                scope:zg361_comp_route = 1
                scope:zg361_comp_route = 2
                scope:zg361_comp_route = 3
            }}
            {full_guard(domain, state, owner=f"var:{vars_for(domain)['owner']}")}
            has_variable = {p}_receipt_active
            var:{p}_receipt_active = 0
            {business_guard}
            {guard}
        }}
        {record_operation(mechanism_id, domain, state)}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {finance}
            if = {{
                limit = {{ var:zg361_comp_financial_applied = 1 }}
                set_variable = {{ name = {p}_receipt_active value = 1 }}
                set_variable = {{ name = {p}_route value = scope:zg361_comp_route }}
                set_variable = {{ name = {p}_value value = 0 }}
                if = {{ limit = {{ scope:zg361_comp_route = 1 }} set_variable = {{ name = {p}_value value = 1 }} }}
                else_if = {{ limit = {{ scope:zg361_comp_route = 2 }} set_variable = {{ name = {p}_value value = -1 }} }}
                zg361_comp_m{mechanism_id:03d}_consume_effect = yes
                set_variable = {{ name = zg361_comp_last_disposition value = 1 }}
                set_variable = {{ name = zg361_comp_runtime_applied value = 1 }}
            }}
        }}
    }}
    else = {{
        if = {{
            limit = {{
                var:{p}_receipt_active = 1
                var:{p}_receipt_owner = var:{vars_for(domain)["owner"]}
                var:{p}_receipt_subject = this
                var:{p}_receipt_cycle = var:{vars_for(domain)["cycle"]}
                var:{p}_receipt_case = var:{vars_for(domain)["case"]}
                var:{p}_receipt_state = {state}
            }}
            if = {{
                limit = {{ var:{p}_receipt_route = scope:zg361_comp_route }}
                set_variable = {{ name = zg361_comp_last_disposition value = 2 }}
            }}
            else = {{
                set_variable = {{ name = zg361_comp_typed_red value = 3 }}
                set_variable = {{ name = zg361_comp_last_disposition value = -1 }}
            }}
        }}
        else = {{ set_variable = {{ name = zg361_comp_last_disposition value = 3 }} }}
    }}
}}'''


def render_consumer(mechanism_id: int, domain: str, state: int) -> str:
    p = f"zg361_comp_m{mechanism_id:03d}"
    reconcile_statement = recalculate_statement_call(mechanism_id)
    reconcile_lti = recalculate_lti_call(mechanism_id)
    post = post_consumer(mechanism_id)
    barrier = (
        "zg361_comp_af_try_start_vesting_effect = yes"
        if domain == "af" and state == 4
        else f"zg361_comp_{domain}_try_advance_{state:02d}_effect = yes"
    )
    return f'''zg361_comp_m{mechanism_id:03d}_consume_effect = {{
    if = {{
        limit = {{
            {full_guard(domain, state, owner=f"var:{vars_for(domain)['owner']}")}
            var:{p}_receipt_active = 1
            var:{p}_consumed = 0
        }}
        {special_payload(mechanism_id)}
        {post}
        {reconcile_statement}
        {reconcile_lti}
        set_variable = {{ name = {p}_consumed value = 1 }}
        {barrier}
        debug_log = "ZG361COMP: consumed mechanism {mechanism_id:03d}"
    }}
}}'''


DEADLINES = {
    "l_deferred": ("l", 4, 365, "zg361comp.100"),
    "ae_due_90": ("ae", 3, 90, "zg361comp.210"),
    "ae_due_180": ("ae", 3, 180, "zg361comp.211"),
    "af_vest_30": ("af", 4, 30, "zg361comp.300"),
    "af_vest_90": ("af", 4, 90, "zg361comp.301"),
    "af_vest_180": ("af", 4, 180, "zg361comp.302"),
    "af_vest_365": ("af", 4, 365, "zg361comp.303"),
    "af_vest_730": ("af", 4, 730, "zg361comp.304"),
    "af_buyback_90": ("af", 5, 90, "zg361comp.310"),
}


def deadline_names(prefix: str) -> dict[str, str]:
    p = f"zg361_comp_{prefix}_deadline"
    return {
        "owner": f"{p}_owner",
        "subject": f"{p}_subject",
        "cycle": f"{p}_cycle",
        "case": f"{p}_case",
        "state": f"{p}_state",
        "days": f"{p}_days",
        "pending": f"{p}_pending",
        "expired": f"{p}_expired",
    }


def schedule_deadline(prefix: str) -> str:
    domain, state, days, event_id = DEADLINES[prefix]
    row = vars_for(domain)
    dl = deadline_names(prefix)
    return f'''zg361_case_kernel_schedule_deadline_effect = {{
            OWNER_VAR = {row["owner"]}
            SUBJECT_VAR = {row["subject"]}
            CYCLE_VAR = {row["cycle"]}
            CASE_VAR = {row["case"]}
            STATE_VAR = {row["state"]}
            ACTIVE_VAR = {row["active"]}
            DEADLINE_OWNER_VAR = {dl["owner"]}
            DEADLINE_SUBJECT_VAR = {dl["subject"]}
            DEADLINE_CYCLE_VAR = {dl["cycle"]}
            DEADLINE_CASE_VAR = {dl["case"]}
            DEADLINE_STATE_VAR = {dl["state"]}
            DEADLINE_DAYS_VAR = {dl["days"]}
            DEADLINE_PENDING_VAR = {dl["pending"]}
            DEADLINE_EXPIRED_VAR = {dl["expired"]}
            TICKET_OWNER = var:{row["owner"]}
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{row["cycle"]}
            TICKET_CASE = var:{row["case"]}
            TICKET_STATE = {state}
            DAYS = {days}
            EVENT = {event_id}
        }}'''


def expire_deadline(prefix: str) -> str:
    domain, _, _, _ = DEADLINES[prefix]
    row = vars_for(domain)
    dl = deadline_names(prefix)
    return f'''zg361_case_kernel_expire_deadline_effect = {{
            OWNER_VAR = {row["owner"]}
            SUBJECT_VAR = {row["subject"]}
            CYCLE_VAR = {row["cycle"]}
            CASE_VAR = {row["case"]}
            STATE_VAR = {row["state"]}
            ACTIVE_VAR = {row["active"]}
            REVISION_VAR = {row["revision"]}
            TIMELINE_VAR = {row["timeline"]}
            FEEDBACK_VAR = {row["feedback"]}
            DEADLINE_OWNER_VAR = {dl["owner"]}
            DEADLINE_SUBJECT_VAR = {dl["subject"]}
            DEADLINE_CYCLE_VAR = {dl["cycle"]}
            DEADLINE_CASE_VAR = {dl["case"]}
            DEADLINE_STATE_VAR = {dl["state"]}
            DEADLINE_PENDING_VAR = {dl["pending"]}
            DEADLINE_EXPIRED_VAR = {dl["expired"]}
        }}'''


def domain_initialization(domain: DomainSpec) -> str:
    if domain.key == "l":
        return r'''set_variable = { name = zg361_comp_l_treasury_available value = 100 }
            set_variable = { name = zg361_comp_l_personal_available value = 50 }
            set_variable = { name = zg361_comp_l_treasury_reserved value = 0 }
            set_variable = { name = zg361_comp_l_personal_reserved value = 0 }
            set_variable = { name = zg361_comp_l_treasury_settled value = 0 }
            set_variable = { name = zg361_comp_l_personal_settled value = 0 }
            set_variable = { name = zg361_comp_bonus_total value = 0 }
            set_variable = { name = zg361_comp_bonus_immediate_owed value = 0 }
            set_variable = { name = zg361_comp_bonus_deferred_owed value = 0 }
            set_variable = { name = zg361_comp_bonus_held value = 0 }
            set_variable = { name = zg361_comp_bonus_paid_gross value = 0 }
            set_variable = { name = zg361_comp_bonus_returned value = 0 }
            set_variable = { name = zg361_comp_bonus_forfeited value = 0 }
            set_variable = { name = zg361_comp_bonus_funded value = 0 }
            set_variable = { name = zg361_comp_bonus_immediate_paid value = 0 }
            set_variable = { name = zg361_comp_bonus_clawback_status value = 0 }
            set_variable = { name = zg361_comp_l_deferred_resolved value = 0 }
            set_variable = { name = zg361_comp_l_bonus_conserved value = 1 }
            set_variable = { name = zg361_comp_bonus_immediate_receipt_serial value = 0 }
            set_variable = { name = zg361_comp_bonus_immediate_treasury_status value = 0 }
            set_variable = { name = zg361_comp_bonus_immediate_personal_status value = 0 }
            set_variable = { name = zg361_comp_bonus_deferred_treasury_status value = 0 }
            set_variable = { name = zg361_comp_bonus_deferred_personal_status value = 0 }
            set_variable = { name = zg361_comp_bonus_held_treasury_status value = 0 }
            set_variable = { name = zg361_comp_bonus_held_personal_status value = 0 }
            set_variable = { name = zg361_comp_m090_pay_treasury_status value = 0 }
            set_variable = { name = zg361_comp_m090_pay_personal_status value = 0 }'''
    if domain.key == "ae":
        return r'''set_variable = { name = zg361_comp_ae_treasury_available value = 200 }
            set_variable = { name = zg361_comp_ae_personal_available value = 100 }
            set_variable = { name = zg361_comp_ae_treasury_reserved value = 0 }
            set_variable = { name = zg361_comp_ae_personal_reserved value = 0 }
            set_variable = { name = zg361_comp_ae_treasury_settled value = 0 }
            set_variable = { name = zg361_comp_ae_personal_settled value = 0 }
            set_variable = { name = zg361_comp_ae_statement_base value = 15 }
            set_variable = { name = zg361_comp_ae_statement_payable value = 0 }
            set_variable = { name = zg361_comp_ae_statement_paid value = 0 }
            set_variable = { name = zg361_comp_ae_statement_owed value = 0 }
            set_variable = { name = zg361_comp_ae_statement_returned value = 0 }
            set_variable = { name = zg361_comp_ae_statement_initialized value = 0 }
            set_variable = { name = zg361_comp_ae_statement_conserved value = 1 }
            set_variable = { name = zg361_comp_ae_due_resolved value = 1 }
            set_variable = { name = zg361_comp_ae_delay_count value = 0 }
            set_variable = { name = zg361_comp_ae_credibility value = 100 }
            set_variable = { name = zg361_comp_ae_payment_red value = 0 }
            set_variable = { name = zg361_comp_ae_frozen_performance_grade value = var:zg361_comp_result_rating }
            set_variable = { name = zg361_comp_ae_appeal_response_recorded value = 0 }
            set_variable = { name = zg361_comp_ae_appeal_requested value = 0 }
            set_variable = { name = zg361_comp_ae_due_now_treasury_status value = 0 }
            set_variable = { name = zg361_comp_ae_due_now_personal_status value = 0 }
            set_variable = { name = zg361_comp_ae_due_later_treasury_status value = 0 }
            set_variable = { name = zg361_comp_ae_due_later_personal_status value = 0 }
            set_variable = { name = zg361_comp_m282_pay_treasury_status value = 0 }
            set_variable = { name = zg361_comp_m282_pay_personal_status value = 0 }
            set_variable = { name = zg361_comp_m289_pay_treasury_status value = 0 }
            set_variable = { name = zg361_comp_m289_pay_personal_status value = 0 }'''
    return r'''set_variable = { name = zg361_comp_af_treasury_available value = 100 }
            set_variable = { name = zg361_comp_af_personal_available value = 50 }
            set_variable = { name = zg361_comp_af_treasury_reserved value = 0 }
            set_variable = { name = zg361_comp_af_personal_reserved value = 0 }
            set_variable = { name = zg361_comp_af_treasury_settled value = 0 }
            set_variable = { name = zg361_comp_af_personal_settled value = 0 }
            set_variable = { name = zg361_comp_af_grant_base_units value = 0 }
            set_variable = { name = zg361_comp_af_conversion_units value = 0 }
            set_variable = { name = zg361_comp_af_total_units value = 0 }
            set_variable = { name = zg361_comp_af_unvested_service value = 0 }
            set_variable = { name = zg361_comp_af_unvested_performance value = 0 }
            set_variable = { name = zg361_comp_af_service_original value = 0 }
            set_variable = { name = zg361_comp_af_performance_original value = 0 }
            set_variable = { name = zg361_comp_af_vested_units value = 0 }
            set_variable = { name = zg361_comp_af_forfeited_units value = 0 }
            set_variable = { name = zg361_comp_af_repurchased_units value = 0 }
            set_variable = { name = zg361_comp_af_periods_processed value = 0 }
            set_variable = { name = zg361_comp_af_vesting_periods value = 12 }
            set_variable = { name = zg361_comp_af_cadence_days value = 30 }
            set_variable = { name = zg361_comp_af_cliff_days value = 365 }
            set_variable = { name = zg361_comp_af_cliff_consumed value = 0 }
            set_variable = { name = zg361_comp_af_vesting_ready value = 0 }
            set_variable = { name = zg361_comp_af_vesting_complete value = 0 }
            set_variable = { name = zg361_comp_af_exit_requested value = 0 }
            set_variable = { name = zg361_comp_af_last_exit_offer_period value = 0 }
            set_variable = { name = zg361_comp_af_repurchase_resolved value = 1 }
            set_variable = { name = zg361_comp_af_unit_conserved value = 1 }
            set_variable = { name = zg361_comp_af_request_serial value = 0 }
            set_variable = { name = zg361_comp_af_request_state value = 0 }
            set_variable = { name = zg361_comp_af_vesting_red value = 0 }
            set_variable = { name = zg361_comp_af_buyback_red value = 0 }
            set_variable = { name = zg361_comp_m292_cash_treasury_status value = 0 }
            set_variable = { name = zg361_comp_m292_cash_personal_status value = 0 }
            set_variable = { name = zg361_comp_m300_buyback_treasury_status value = 0 }
            set_variable = { name = zg361_comp_m300_buyback_personal_status value = 0 }
            set_variable = { name = zg361_comp_af_buyback_later_treasury_status value = 0 }
            set_variable = { name = zg361_comp_af_buyback_later_personal_status value = 0 }
            root = {
                if = { limit = { NOT = { has_variable = zg361_comp_af_queue_head } } set_variable = { name = zg361_comp_af_queue_head value = 0 } }
                if = { limit = { NOT = { has_variable = zg361_comp_af_queue_tail } } set_variable = { name = zg361_comp_af_queue_tail value = 0 } }
            }'''


def render_result_snapshot_helpers() -> str:
    return r'''# Subject-scoped freeze of one delivered result.  The manager portfolio owns
# this immutable source identity for the complete L -> AE -> AF sequence.
zg361_comp_freeze_current_result_effect = {
    root = { remove_variable = zg361_comp_portfolio_result_snapshot_applied }
    if = {
        limit = {
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            trigger_if = {
                limit = {
                    has_variable = zg361_result_case_owner
                    has_variable = zg361_result_cycle_serial
                    has_variable = zg361_result_case_serial
                    has_variable = zg361_result_case_state
                    has_variable = zg361_result_grade
                    root = { has_variable = zg361_review_serial }
                }
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
                var:zg361_result_case_state >= 3
                OR = {
                    var:zg361_result_grade = 1
                    var:zg361_result_grade = 2
                    var:zg361_result_grade = 3
                }
            }
            trigger_else = { always = no }
        }
        save_scope_as = zg361_comp_result_subject_scope
        root = {
            set_variable = { name = zg361_comp_portfolio_cycle value = var:zg361_review_serial }
            set_variable = { name = zg361_comp_portfolio_subject value = scope:zg361_comp_result_subject_scope }
            set_variable = { name = zg361_comp_portfolio_result_owner value = scope:zg361_comp_result_subject_scope.var:zg361_result_case_owner }
            set_variable = { name = zg361_comp_portfolio_result_subject value = scope:zg361_comp_result_subject_scope }
            set_variable = { name = zg361_comp_portfolio_result_cycle value = scope:zg361_comp_result_subject_scope.var:zg361_result_cycle_serial }
            set_variable = { name = zg361_comp_portfolio_result_case value = scope:zg361_comp_result_subject_scope.var:zg361_result_case_serial }
            set_variable = { name = zg361_comp_portfolio_result_state value = scope:zg361_comp_result_subject_scope.var:zg361_result_case_state }
            set_variable = { name = zg361_comp_portfolio_result_grade value = scope:zg361_comp_result_subject_scope.var:zg361_result_grade }
            set_variable = { name = zg361_comp_portfolio_result_rating value = 325 }
            if = {
                limit = { scope:zg361_comp_result_subject_scope.var:zg361_result_grade = 2 }
                set_variable = { name = zg361_comp_portfolio_result_rating value = 350 }
            }
            else_if = {
                limit = { scope:zg361_comp_result_subject_scope.var:zg361_result_grade = 3 }
                set_variable = { name = zg361_comp_portfolio_result_rating value = 375 }
            }
            set_variable = { name = zg361_comp_portfolio_result_snapshot_applied value = 1 }
        }
    }
}'''


def render_open(domain: DomainSpec) -> str:
    resets = []
    for mechanism_id in (item for stage in domain.stages for item in stage):
        p = f"zg361_comp_m{mechanism_id:03d}"
        resets.extend(
            (
                f"set_variable = {{ name = {p}_receipt_active value = 0 }}",
                f"set_variable = {{ name = {p}_consumed value = 0 }}",
                f"set_variable = {{ name = {p}_route value = 0 }}",
                f"set_variable = {{ name = {p}_value value = 0 }}",
            )
        )
    for prefix, (key, _, _, _) in DEADLINES.items():
        if key == domain.key:
            dl = deadline_names(prefix)
            resets.append(f"set_variable = {{ name = {dl['pending']} value = 0 }}")
            resets.append(f"set_variable = {{ name = {dl['expired']} value = 0 }}")
    reset_text = "\n            ".join(resets)
    return f'''zg361_comp_open_{domain.key}_case_effect = {{
    save_scope_as = zg361_comp_open_subject
    remove_variable = zg361_comp_runtime_applied
    if = {{
        limit = {{
            root = {{
                zg361_is_celestial_liege_trigger = yes
                has_variable = zg361_review_serial
                trigger_if = {{
                    limit = {{
                        has_variable = zg361_comp_portfolio_cycle
                        has_variable = zg361_comp_portfolio_subject
                        has_variable = zg361_comp_portfolio_result_owner
                        has_variable = zg361_comp_portfolio_result_subject
                        has_variable = zg361_comp_portfolio_result_cycle
                        has_variable = zg361_comp_portfolio_result_case
                        has_variable = zg361_comp_portfolio_result_state
                        has_variable = zg361_comp_portfolio_result_grade
                        has_variable = zg361_comp_portfolio_result_rating
                        has_variable = zg361_comp_portfolio_result_snapshot_applied
                    }}
                    var:zg361_comp_portfolio_cycle = var:zg361_review_serial
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_open_subject
                    var:zg361_comp_portfolio_result_owner = root
                    var:zg361_comp_portfolio_result_subject = scope:zg361_comp_open_subject
                    var:zg361_comp_portfolio_result_cycle = var:zg361_review_serial
                    var:zg361_comp_portfolio_result_state >= 3
                    var:zg361_comp_portfolio_result_snapshot_applied = 1
                    OR = {{
                        AND = {{ var:zg361_comp_portfolio_result_grade = 1 var:zg361_comp_portfolio_result_rating = 325 }}
                        AND = {{ var:zg361_comp_portfolio_result_grade = 2 var:zg361_comp_portfolio_result_rating = 350 }}
                        AND = {{ var:zg361_comp_portfolio_result_grade = 3 var:zg361_comp_portfolio_result_rating = 375 }}
                    }}
                }}
                trigger_else = {{ always = no }}
            }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
        }}
        zg361_case_{domain.key}_open_effect = yes
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            set_variable = {{ name = zg361_comp_result_owner value = root.var:zg361_comp_portfolio_result_owner }}
            set_variable = {{ name = zg361_comp_result_subject value = root.var:zg361_comp_portfolio_result_subject }}
            set_variable = {{ name = zg361_comp_result_cycle value = root.var:zg361_comp_portfolio_result_cycle }}
            set_variable = {{ name = zg361_comp_result_case value = root.var:zg361_comp_portfolio_result_case }}
            set_variable = {{ name = zg361_comp_result_state value = root.var:zg361_comp_portfolio_result_state }}
            set_variable = {{ name = zg361_comp_result_grade value = root.var:zg361_comp_portfolio_result_grade }}
            set_variable = {{ name = zg361_comp_result_rating value = root.var:zg361_comp_portfolio_result_rating }}
            set_variable = {{ name = zg361_comp_{domain.key}_last_operation value = 0 }}
            set_variable = {{ name = zg361_comp_{domain.key}_last_route value = 0 }}
            set_variable = {{ name = zg361_comp_last_disposition value = 0 }}
            set_variable = {{ name = zg361_comp_typed_red value = 0 }}
            {domain_initialization(domain)}
            {reset_text}
            set_variable = {{ name = zg361_comp_runtime_applied value = 1 }}
            debug_log = "ZG361COMP: opened {domain.key.upper()} {domain.title_en} case"
        }}
    }}
}}'''


def render_bonus_financial_helpers() -> str:
    owner = vars_for("l")["owner"]
    reserves = "\n    ".join(
        (
            journal_reserve("l", 1, "zg361_comp_bonus_immediate", "treasury", "10"),
            journal_reserve("l", 1, "zg361_comp_bonus_immediate", "personal", "4"),
            journal_reserve("l", 1, "zg361_comp_bonus_deferred", "treasury", "3"),
            journal_reserve("l", 1, "zg361_comp_bonus_deferred", "personal", "1"),
            journal_reserve("l", 1, "zg361_comp_bonus_held", "treasury", "1"),
            journal_reserve("l", 1, "zg361_comp_bonus_held", "personal", "1"),
        )
    )
    settles = "\n        ".join(
        (
            journal_settle("l", 1, "zg361_comp_bonus_immediate", "treasury"),
            journal_settle("l", 1, "zg361_comp_bonus_immediate", "personal"),
        )
    )
    settle_deferred = "\n        ".join(
        (
            journal_settle("l", 4, "zg361_comp_bonus_deferred", "treasury"),
            journal_settle("l", 4, "zg361_comp_bonus_deferred", "personal"),
            journal_settle("l", 4, "zg361_comp_bonus_held", "treasury"),
            journal_settle("l", 4, "zg361_comp_bonus_held", "personal"),
        )
    )
    refund_deferred = "\n        ".join(
        (
            journal_refund("l", 4, "zg361_comp_bonus_deferred", "treasury"),
            journal_refund("l", 4, "zg361_comp_bonus_deferred", "personal"),
            journal_refund("l", 4, "zg361_comp_bonus_held", "treasury"),
            journal_refund("l", 4, "zg361_comp_bonus_held", "personal"),
        )
    )
    return f'''zg361_comp_l_reserve_bonus_effect = {{
    remove_variable = zg361_comp_financial_applied
    {reserves}
    if = {{
        limit = {{
            var:zg361_comp_bonus_immediate_treasury_status = 1
            var:zg361_comp_bonus_immediate_personal_status = 1
            var:zg361_comp_bonus_deferred_treasury_status = 1
            var:zg361_comp_bonus_deferred_personal_status = 1
            var:zg361_comp_bonus_held_treasury_status = 1
            var:zg361_comp_bonus_held_personal_status = 1
        }}
        {settles}
    }}
    if = {{
        limit = {{
            var:zg361_comp_bonus_immediate_treasury_status = 2
            var:zg361_comp_bonus_immediate_personal_status = 2
            var:zg361_comp_bonus_deferred_treasury_status = 1
            var:zg361_comp_bonus_deferred_personal_status = 1
            var:zg361_comp_bonus_held_treasury_status = 1
            var:zg361_comp_bonus_held_personal_status = 1
        }}
        var:{owner} = {{
            remove_treasury = 14
            add_gold = {{ value = 0 subtract = 6 }}
        }}
        add_gold = 14
        {freeze_cash_identities("zg361_comp_bonus_immediate_receipt", "l", 1)}
        set_variable = {{ name = zg361_comp_bonus_immediate_receipt_serial value = var:zg361_case_l_case_serial }}
        set_variable = {{ name = zg361_comp_bonus_total value = 20 }}
        set_variable = {{ name = zg361_comp_bonus_immediate_owed value = 0 }}
        set_variable = {{ name = zg361_comp_bonus_deferred_owed value = 4 }}
        set_variable = {{ name = zg361_comp_bonus_held value = 2 }}
        set_variable = {{ name = zg361_comp_bonus_paid_gross value = 14 }}
        set_variable = {{ name = zg361_comp_bonus_immediate_paid value = 14 }}
        set_variable = {{ name = zg361_comp_bonus_funded value = 1 }}
        set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
        zg361_comp_l_check_conservation_effect = yes
    }}
}}

zg361_comp_l_clawback_bonus_effect = {{
    remove_variable = zg361_comp_financial_applied
    if = {{
        limit = {{
            var:zg361_comp_bonus_clawback_status = 0
            var:zg361_comp_bonus_returned = 0
            gold >= 2
            var:{owner} = {{ has_treasury = yes }}
        }}
        add_gold = {{ value = 0 subtract = 2 }}
        var:{owner} = {{
            add_treasury = 1
            add_gold = 1
        }}
        set_variable = {{ name = zg361_comp_bonus_clawback_status value = 2 }}
        set_variable = {{ name = zg361_comp_bonus_clawback_source_receipt value = var:zg361_comp_bonus_immediate_receipt_serial }}
        {freeze_cash_identities("zg361_comp_bonus_clawback_receipt", "l", 2)}
        change_variable = {{ name = zg361_comp_bonus_returned add = 2 }}
        change_variable = {{ name = zg361_comp_bonus_forfeited add = 2 }}
        set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
        zg361_comp_l_check_conservation_effect = yes
    }}
}}

zg361_comp_l_consume_deferred_effect = {{
    remove_variable = zg361_comp_financial_applied
    if = {{
        limit = {{
            var:zg361_comp_bonus_funded = 1
            zg361_is_reviewable_vassal_trigger = yes
            liege = var:{owner}
            var:zg361_comp_m086_route = 1
        }}
        {settle_deferred}
        if = {{
            limit = {{
                var:zg361_comp_bonus_deferred_treasury_status = 2
                var:zg361_comp_bonus_deferred_personal_status = 2
                var:zg361_comp_bonus_held_treasury_status = 2
                var:zg361_comp_bonus_held_personal_status = 2
            }}
            add_gold = 6
            change_variable = {{ name = zg361_comp_bonus_paid_gross add = 6 }}
            set_variable = {{ name = zg361_comp_bonus_deferred_owed value = 0 }}
            set_variable = {{ name = zg361_comp_bonus_held value = 0 }}
            {freeze_cash_identities("zg361_comp_bonus_deferred_settlement_receipt", "l", 4)}
            set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
        }}
    }}
    else_if = {{
        limit = {{ var:zg361_comp_bonus_funded = 1 }}
        {refund_deferred}
        if = {{
            limit = {{
                var:zg361_comp_bonus_deferred_treasury_status = 3
                var:zg361_comp_bonus_deferred_personal_status = 3
                var:zg361_comp_bonus_held_treasury_status = 3
                var:zg361_comp_bonus_held_personal_status = 3
            }}
            var:{owner} = {{ add_treasury = 4 add_gold = 2 }}
            change_variable = {{ name = zg361_comp_bonus_forfeited add = 6 }}
            set_variable = {{ name = zg361_comp_bonus_deferred_owed value = 0 }}
            set_variable = {{ name = zg361_comp_bonus_held value = 0 }}
            set_variable = {{ name = zg361_comp_bonus_refund_source_receipt value = var:zg361_comp_bonus_immediate_receipt_serial }}
            {freeze_cash_identities("zg361_comp_bonus_refund_receipt", "l", 4)}
            set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
        }}
    }}
    else = {{ set_variable = {{ name = zg361_comp_financial_applied value = 1 }} }}
    if = {{
        limit = {{ var:zg361_comp_financial_applied = 1 }}
        set_variable = {{ name = zg361_comp_l_deferred_resolved value = 1 }}
        zg361_comp_l_check_conservation_effect = yes
        zg361_comp_l_try_advance_04_effect = yes
        if = {{
            limit = {{ is_ai = no var:{owner} = {{ is_ai = no }} }}
            trigger_event = {{ id = zg361comp.901 days = 1 }}
        }}
    }}
}}

zg361_comp_l_check_conservation_effect = {{
    set_variable = {{ name = zg361_comp_l_bonus_accounted value = var:zg361_comp_bonus_immediate_owed }}
    change_variable = {{ name = zg361_comp_l_bonus_accounted add = var:zg361_comp_bonus_deferred_owed }}
    change_variable = {{ name = zg361_comp_l_bonus_accounted add = var:zg361_comp_bonus_held }}
    change_variable = {{ name = zg361_comp_l_bonus_accounted add = var:zg361_comp_bonus_paid_gross }}
    change_variable = {{ name = zg361_comp_l_bonus_accounted add = {{ value = 0 subtract = var:zg361_comp_bonus_returned }} }}
    change_variable = {{ name = zg361_comp_l_bonus_accounted add = var:zg361_comp_bonus_forfeited }}
    set_variable = {{ name = zg361_comp_l_bonus_conserved value = 0 }}
    if = {{
        limit = {{ var:zg361_comp_l_bonus_accounted = var:zg361_comp_bonus_total }}
        set_variable = {{ name = zg361_comp_l_bonus_conserved value = 1 }}
    }}
}}'''


def render_financial_helpers() -> str:
    parts = [render_bonus_financial_helpers()]
    parts.extend(
        (
            render_fixed_dual_payment("zg361_comp_l_pay_spot_effect", "l", 4, "zg361_comp_m090_pay", 7, 3),
            render_dynamic_dual_payment(
                "zg361_comp_ae_pay_due_now_effect",
                "ae",
                2,
                "zg361_comp_ae_due_now",
                "scope:zg361_comp_due_treasury",
                "scope:zg361_comp_due_personal",
                "scope:zg361_comp_due_gross",
            ),
            render_dynamic_dual_payment(
                "zg361_comp_ae_pay_due_later_effect",
                "ae",
                3,
                "zg361_comp_ae_due_later",
                "scope:zg361_comp_due_treasury",
                "scope:zg361_comp_due_personal",
                "scope:zg361_comp_due_gross",
            ),
            render_fixed_dual_payment("zg361_comp_ae_pay_backpay_effect", "ae", 2, "zg361_comp_m282_pay", 3, 1),
            render_fixed_dual_payment("zg361_comp_ae_pay_appeal_effect", "ae", 5, "zg361_comp_m289_pay", 3, 1),
            render_fixed_dual_payment("zg361_comp_af_pay_cash_alternative_effect", "af", 1, "zg361_comp_m292_cash", 7, 3),
            render_fixed_dual_payment("zg361_comp_af_pay_buyback_now_effect", "af", 5, "zg361_comp_m300_buyback", 7, 3),
            render_fixed_dual_payment("zg361_comp_af_pay_buyback_later_effect", "af", 5, "zg361_comp_af_buyback_later", 7, 3),
        )
    )
    return "\n\n".join(parts)


def render_account_helpers() -> str:
    return r'''zg361_comp_ae_recalculate_statement_effect = {
    if = {
        limit = {
            var:zg361_comp_ae_statement_initialized = 0
            var:zg361_comp_m278_consumed = 1
            var:zg361_comp_m279_consumed = 1
            var:zg361_comp_m280_consumed = 1
        }
        set_variable = {
            name = zg361_comp_ae_extra_month_prorated
            value = {
                value = var:zg361_comp_m279_amount
                multiply = var:zg361_comp_m280_proration_bps
                divide = 10000
                floor = yes
            }
        }
        if = {
            limit = {
                var:zg361_comp_m279_contract_kind = 2
                var:zg361_comp_ae_frozen_performance_grade < 375
            }
            set_variable = { name = zg361_comp_ae_extra_month_prorated value = 0 }
        }
        else_if = {
            limit = { var:zg361_comp_m279_contract_kind = 3 }
            set_variable = { name = zg361_comp_ae_extra_month_prorated value = 0 }
        }
        set_variable = { name = zg361_comp_ae_statement_payable value = var:zg361_comp_ae_statement_base }
        change_variable = { name = zg361_comp_ae_statement_payable add = var:zg361_comp_ae_extra_month_prorated }
        set_variable = { name = zg361_comp_ae_statement_paid value = 0 }
        set_variable = { name = zg361_comp_ae_statement_owed value = var:zg361_comp_ae_statement_payable }
        set_variable = { name = zg361_comp_ae_statement_returned value = 0 }
        set_variable = { name = zg361_comp_ae_statement_initialized value = 1 }
    }
    # Mechanism 278 is necessarily consumed before 279/280 finish the
    # formula. Refresh its consumer-facing account snapshot after every
    # recalculation instead of freezing the pre-initialization zeroes.
    set_variable = { name = zg361_comp_m278_promised value = var:zg361_comp_ae_statement_payable }
    set_variable = { name = zg361_comp_m278_paid value = var:zg361_comp_ae_statement_paid }
    set_variable = { name = zg361_comp_m278_owed value = var:zg361_comp_ae_statement_owed }
    set_variable = { name = zg361_comp_m278_returned value = var:zg361_comp_ae_statement_returned }
    set_variable = { name = zg361_comp_ae_statement_rhs value = var:zg361_comp_ae_statement_paid }
    change_variable = { name = zg361_comp_ae_statement_rhs add = var:zg361_comp_ae_statement_owed }
    change_variable = { name = zg361_comp_ae_statement_rhs add = { value = 0 subtract = var:zg361_comp_ae_statement_returned } }
    set_variable = { name = zg361_comp_ae_statement_conserved value = 0 }
    if = {
        limit = { var:zg361_comp_ae_statement_rhs = var:zg361_comp_ae_statement_payable }
        set_variable = { name = zg361_comp_ae_statement_conserved value = 1 }
    }
}

zg361_comp_af_recalculate_units_effect = {
    if = {
        limit = { var:zg361_comp_af_periods_processed = 0 }
        set_variable = { name = zg361_comp_af_total_units value = var:zg361_comp_af_grant_base_units }
        change_variable = { name = zg361_comp_af_total_units add = var:zg361_comp_af_conversion_units }
        if = {
            limit = { var:zg361_comp_m292_consumed = 1 var:zg361_comp_m292_risk_kind = 3 }
            set_variable = { name = zg361_comp_af_total_units value = var:zg361_comp_af_conversion_units }
        }
        set_variable = { name = zg361_comp_af_service_bps value = 5000 }
        if = {
            limit = { var:zg361_comp_m297_consumed = 1 }
            set_variable = { name = zg361_comp_af_service_bps value = var:zg361_comp_m297_service_bps }
        }
        set_variable = {
            name = zg361_comp_af_service_original
            value = {
                value = var:zg361_comp_af_total_units
                multiply = var:zg361_comp_af_service_bps
                divide = 10000
                floor = yes
            }
        }
        set_variable = {
            name = zg361_comp_af_performance_original
            value = {
                value = var:zg361_comp_af_total_units
                subtract = var:zg361_comp_af_service_original
            }
        }
        set_variable = { name = zg361_comp_af_unvested_service value = var:zg361_comp_af_service_original }
        set_variable = { name = zg361_comp_af_unvested_performance value = var:zg361_comp_af_performance_original }
    }
    zg361_comp_af_check_conservation_effect = yes
}

zg361_comp_af_check_conservation_effect = {
    set_variable = { name = zg361_comp_af_unit_accounted value = var:zg361_comp_af_unvested_service }
    change_variable = { name = zg361_comp_af_unit_accounted add = var:zg361_comp_af_unvested_performance }
    change_variable = { name = zg361_comp_af_unit_accounted add = var:zg361_comp_af_vested_units }
    change_variable = { name = zg361_comp_af_unit_accounted add = var:zg361_comp_af_forfeited_units }
    change_variable = { name = zg361_comp_af_unit_accounted add = var:zg361_comp_af_repurchased_units }
    set_variable = { name = zg361_comp_af_unit_conserved value = 0 }
    if = {
        limit = { var:zg361_comp_af_unit_accounted = var:zg361_comp_af_total_units }
        set_variable = { name = zg361_comp_af_unit_conserved value = 1 }
    }
}'''


def after_transition(domain: str, state: int) -> str:
    if domain == "l" and state == 3:
        return schedule_deadline("l_deferred")
    if domain == "l" and state == 4:
        return '''zg361_comp_portfolio_case_closed_effect = { DOMAIN = 1 }
        if = { limit = { is_ai = no var:zg361_case_l_owner = { is_ai = no } } trigger_event = { id = zg361comp.900 days = 1 } }'''
    if domain == "ae" and state == 2:
        return f'''if = {{
            limit = {{ var:zg361_comp_ae_due_resolved = 0 var:zg361_comp_m281_route = 2 }}
            {schedule_deadline("ae_due_90")}
        }}
        else_if = {{
            limit = {{ var:zg361_comp_ae_due_resolved = 0 var:zg361_comp_m281_route = 3 }}
            {schedule_deadline("ae_due_180")}
        }}'''
    if domain == "ae" and state == 4:
        return '''if = {
            limit = { OR = { is_ai = yes var:zg361_case_ae_owner = { is_ai = yes } } }
            set_variable = { name = zg361_comp_ae_appeal_response_recorded value = 1 }
            set_variable = { name = zg361_comp_ae_appeal_requested value = 0 }
        }
        else = { trigger_event = { id = zg361comp.289 days = 1 } }'''
    if domain == "ae" and state == 5:
        return '''zg361_comp_portfolio_case_closed_effect = { DOMAIN = 2 }
        if = { limit = { is_ai = no var:zg361_case_ae_owner = { is_ai = no } } trigger_event = { id = zg361comp.902 days = 1 } }'''
    if domain == "af" and state == 3:
        return '''zg361_comp_af_schedule_first_vest_effect = yes'''
    if domain == "af" and state == 5:
        return '''zg361_comp_portfolio_case_closed_effect = { DOMAIN = 3 }
        if = { limit = { is_ai = no var:zg361_case_af_owner = { is_ai = no } } trigger_event = { id = zg361comp.904 days = 1 } }'''
    return ""


def barrier_extra(domain: str, state: int) -> str:
    if domain == "l" and state == 4:
        return "var:zg361_comp_l_deferred_resolved = 1\n            var:zg361_comp_l_bonus_conserved = 1"
    if domain == "ae" and state == 3:
        return "var:zg361_comp_ae_due_resolved = 1\n            var:zg361_comp_ae_statement_conserved = 1"
    if domain == "ae" and state == 5:
        return "var:zg361_comp_ae_appeal_response_recorded = 1\n            var:zg361_comp_ae_statement_conserved = 1"
    if domain == "af" and state == 5:
        return "var:zg361_comp_af_repurchase_resolved = 1\n            var:zg361_comp_af_unit_conserved = 1"
    return ""


def render_barrier(domain: DomainSpec, state: int, stage_ids: tuple[int, ...]) -> str:
    required = "\n            ".join(
        f"var:zg361_comp_m{mechanism_id:03d}_consumed = 1"
        for mechanism_id in stage_ids
    )
    extra = barrier_extra(domain.key, state)
    callback = after_transition(domain.key, state)
    notify = f"zg361_comp_portfolio_notify_owner_effect = {{ DOMAIN = {DOMAINS.index(domain) + 1} }}"
    return f'''zg361_comp_{domain.key}_try_advance_{state:02d}_effect = {{
    if = {{
        limit = {{
            {full_guard(domain.key, state, owner=f"var:{vars_for(domain.key)['owner']}")}
            {required}
            {extra}
        }}
        zg361_case_{domain.key}_advance_{state:02d}_effect = {{
            TICKET_OWNER = var:{vars_for(domain.key)["owner"]}
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{vars_for(domain.key)["cycle"]}
            TICKET_CASE = var:{vars_for(domain.key)["case"]}
        }}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {callback}
            {notify}
        }}
    }}
}}'''


def render_ae_runtime_helpers() -> str:
    owner = vars_for("ae")["owner"]
    return f'''zg361_comp_ae_consume_due_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_comp_due_gross value = var:zg361_comp_ae_statement_owed }}
    save_temporary_scope_value_as = {{
        name = zg361_comp_due_treasury
        value = {{ value = scope:zg361_comp_due_gross multiply = 0.7 add = 0.5 floor = yes }}
    }}
    save_temporary_scope_value_as = {{
        name = zg361_comp_due_personal
        value = {{ value = scope:zg361_comp_due_gross subtract = scope:zg361_comp_due_treasury }}
    }}
    remove_variable = zg361_comp_financial_applied
    if = {{
        limit = {{
            scope:zg361_comp_due_gross >= 2
            scope:zg361_comp_due_treasury >= 1
            scope:zg361_comp_due_personal >= 1
            var:{owner} = {{
                has_treasury = yes
                treasury >= scope:zg361_comp_due_treasury
                gold >= scope:zg361_comp_due_personal
            }}
            var:zg361_comp_ae_treasury_available >= scope:zg361_comp_due_treasury
            var:zg361_comp_ae_personal_available >= scope:zg361_comp_due_personal
        }}
        zg361_comp_ae_pay_due_later_effect = yes
    }}
    else_if = {{
        limit = {{ scope:zg361_comp_due_gross = 0 }}
        set_variable = {{ name = zg361_comp_financial_applied value = 1 }}
    }}
    if = {{
        limit = {{ var:zg361_comp_financial_applied = 1 }}
        change_variable = {{ name = zg361_comp_ae_statement_paid add = scope:zg361_comp_due_gross }}
        set_variable = {{ name = zg361_comp_ae_statement_owed value = 0 }}
    }}
    else = {{
        # Typed insufficient-funds RED: both real payer balances and the
        # statement remain unchanged; the owed amount stays visible.
        set_variable = {{ name = zg361_comp_ae_payment_red value = 1 }}
        set_variable = {{ name = zg361_comp_typed_red value = 4 }}
    }}
    set_variable = {{ name = zg361_comp_ae_due_resolved value = 1 }}
    zg361_comp_ae_recalculate_statement_effect = yes
    zg361_comp_ae_try_advance_03_effect = yes
}}

# Subject-only response.  Counts/barons may answer their own case but this
# effect cannot open/advance a case, approve money, or call a manager core.
zg361_comp_ae_subject_appeal_response_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_comp_subject_route value = $ROUTE$ }}
    if = {{
        limit = {{
            is_ai = no
            zg361_case_kernel_subject_self_guard_trigger = {{
                SUBJECT_VAR = zg361_case_ae_subject
                ACTIVE_VAR = zg361_case_ae_active
            }}
            var:zg361_case_ae_state = 5
            var:zg361_comp_ae_appeal_response_recorded = 0
            OR = {{ scope:zg361_comp_subject_route = 1 scope:zg361_comp_subject_route = 2 }}
        }}
        set_variable = {{ name = zg361_comp_ae_appeal_response_recorded value = 1 }}
        set_variable = {{ name = zg361_comp_ae_appeal_requested value = 0 }}
        if = {{ limit = {{ scope:zg361_comp_subject_route = 1 }} set_variable = {{ name = zg361_comp_ae_appeal_requested value = 1 }} }}
            change_variable = {{ name = zg361_case_ae_feedback_revision add = 1 }}
            zg361_comp_portfolio_notify_owner_effect = {{ DOMAIN = 2 }}
    }}
}}'''


def render_af_runtime_helpers() -> str:
    owner = vars_for("af")["owner"]
    first_schedule = f'''if = {{ limit = {{ var:zg361_comp_af_cliff_days = 180 }} {schedule_deadline("af_vest_180")} }}
    else_if = {{ limit = {{ var:zg361_comp_af_cliff_days = 730 }} {schedule_deadline("af_vest_730")} }}
    else = {{ {schedule_deadline("af_vest_365")} }}'''
    next_schedule = f'''if = {{ limit = {{ var:zg361_comp_af_cadence_days = 90 }} {schedule_deadline("af_vest_90")} }}
    else_if = {{ limit = {{ var:zg361_comp_af_cadence_days = 365 }} {schedule_deadline("af_vest_365")} }}
    else = {{ {schedule_deadline("af_vest_30")} }}'''
    return f'''zg361_comp_af_schedule_first_vest_effect = {{
    {first_schedule}
}}

zg361_comp_af_schedule_next_vest_effect = {{
    {next_schedule}
}}

zg361_comp_af_try_start_vesting_effect = {{
    if = {{
        limit = {{
            {full_guard("af", 4, owner=f"var:{owner}")}
            var:zg361_comp_m297_consumed = 1
            var:zg361_comp_m298_consumed = 1
        }}
        set_variable = {{ name = zg361_comp_af_vesting_ready value = 1 }}
    }}
}}

zg361_comp_af_consume_vest_effect = {{
    if = {{
        limit = {{
            {full_guard("af", 4, owner=f"var:{owner}")}
            var:zg361_comp_af_vesting_ready = 1
            var:zg361_comp_af_periods_processed < var:zg361_comp_af_vesting_periods
        }}
        set_variable = {{ name = zg361_comp_af_cliff_consumed value = 1 }}
        set_variable = {{
            name = zg361_comp_af_service_tranche
            value = {{ value = var:zg361_comp_af_service_original divide = var:zg361_comp_af_vesting_periods floor = yes }}
        }}
        set_variable = {{
            name = zg361_comp_af_performance_tranche
            value = {{ value = var:zg361_comp_af_performance_original divide = var:zg361_comp_af_vesting_periods floor = yes }}
        }}
        set_variable = {{ name = zg361_comp_af_next_period value = {{ value = var:zg361_comp_af_periods_processed add = 1 }} }}
        if = {{
            limit = {{ var:zg361_comp_af_next_period = var:zg361_comp_af_vesting_periods }}
            set_variable = {{ name = zg361_comp_af_service_tranche value = var:zg361_comp_af_unvested_service }}
            set_variable = {{ name = zg361_comp_af_performance_tranche value = var:zg361_comp_af_unvested_performance }}
        }}
        if = {{
            limit = {{ zg361_is_reviewable_vassal_trigger = yes liege = var:{owner} }}
            change_variable = {{ name = zg361_comp_af_unvested_service add = {{ value = 0 subtract = var:zg361_comp_af_service_tranche }} }}
            change_variable = {{ name = zg361_comp_af_vested_units add = var:zg361_comp_af_service_tranche }}
            if = {{
                limit = {{
                    var:zg361_comp_m298_organization_gate = 1
                    var:zg361_comp_m298_individual_gate = 1
                }}
                change_variable = {{ name = zg361_comp_af_unvested_performance add = {{ value = 0 subtract = var:zg361_comp_af_performance_tranche }} }}
                change_variable = {{ name = zg361_comp_af_vested_units add = var:zg361_comp_af_performance_tranche }}
            }}
        }}
        change_variable = {{ name = zg361_comp_af_periods_processed add = 1 }}
        zg361_comp_af_check_conservation_effect = yes
        if = {{
            limit = {{ is_ai = no var:{owner} = {{ is_ai = no }} }}
            trigger_event = {{ id = zg361comp.903 days = 1 }}
        }}
        if = {{
            limit = {{
                var:zg361_comp_af_periods_processed < var:zg361_comp_af_vesting_periods
                var:zg361_comp_af_exit_requested = 0
            }}
            zg361_comp_af_schedule_next_vest_effect = yes
        }}
        else = {{ set_variable = {{ name = zg361_comp_af_vesting_complete value = 1 }} }}
        zg361_comp_portfolio_notify_owner_effect = {{ DOMAIN = 3 }}
    }}
    else = {{
        set_variable = {{ name = zg361_comp_af_vesting_red value = 1 }}
        set_variable = {{ name = zg361_comp_typed_red value = 5 }}
    }}
}}

# Manager-controlled exit barrier.  Repeated cadence events keep state 4 until
# this explicit request; vesting is therefore not collapsed into one transit.
zg361_comp_af_request_exit_effect = {{
    if = {{
        limit = {{
            root = {{ zg361_is_celestial_liege_trigger = yes }}
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            {full_guard("af", 4, owner="root")}
            var:zg361_comp_af_vesting_ready = 1
            var:zg361_comp_af_cliff_consumed = 1
        }}
        set_variable = {{ name = zg361_comp_af_exit_requested value = 1 }}
        zg361_case_af_advance_04_effect = {{
            TICKET_OWNER = root
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:zg361_case_af_cycle_serial
            TICKET_CASE = var:zg361_case_af_case_serial
        }}
        zg361_comp_portfolio_notify_owner_effect = {{ DOMAIN = 3 }}
    }}
}}

zg361_comp_af_consume_buyback_effect = {{
    remove_variable = zg361_comp_financial_applied
    if = {{
        limit = {{
            {full_guard("af", 5, owner=f"var:{owner}")}
            var:zg361_comp_af_request_state = 1
            var:zg361_comp_af_vested_units >= 10
            var:zg361_comp_af_request_serial = {{ value = var:{owner}.var:zg361_comp_af_queue_head add = 1 }}
            var:{owner} = {{ has_treasury = yes treasury >= 7 gold >= 3 }}
            var:zg361_comp_af_treasury_available >= 7
            var:zg361_comp_af_personal_available >= 3
        }}
        zg361_comp_af_pay_buyback_later_effect = yes
    }}
    if = {{
        limit = {{ var:zg361_comp_financial_applied = 1 }}
        change_variable = {{ name = zg361_comp_af_vested_units add = -10 }}
        change_variable = {{ name = zg361_comp_af_repurchased_units add = 10 }}
        set_variable = {{ name = zg361_comp_af_request_state value = 2 }}
        set_variable = {{ name = zg361_comp_af_repurchase_resolved value = 1 }}
        var:{owner} = {{ change_variable = {{ name = zg361_comp_af_queue_head add = 1 }} }}
        zg361_comp_af_check_conservation_effect = yes
        zg361_comp_af_try_advance_05_effect = yes
    }}
    else_if = {{
        limit = {{
            {full_guard("af", 5, owner=f"var:{owner}")}
            var:zg361_comp_af_request_state = 1
            var:zg361_comp_af_vested_units >= 10
            var:zg361_comp_af_request_serial = {{ value = var:{owner}.var:zg361_comp_af_queue_head add = 1 }}
        }}
        # The delayed request reaches a terminal insufficient-funds outcome.
        # No balance or unit moved; advancing the FIFO releases later cases.
        set_variable = {{ name = zg361_comp_af_buyback_red value = 1 }}
        set_variable = {{ name = zg361_comp_typed_red value = 4 }}
        set_variable = {{ name = zg361_comp_af_request_state value = 4 }}
        set_variable = {{ name = zg361_comp_af_repurchase_resolved value = 1 }}
        var:{owner} = {{ change_variable = {{ name = zg361_comp_af_queue_head add = 1 }} }}
        zg361_comp_af_check_conservation_effect = yes
        zg361_comp_af_try_advance_05_effect = yes
    }}
    else = {{ set_variable = {{ name = zg361_comp_typed_red value = 5 }} }}
}}'''


def portfolio_domain_dispatch(domain: DomainSpec) -> str:
    state_branches = []
    for state, ids in enumerate(domain.stages, start=1):
        calls = "\n                    ".join(
            f"zg361_comp_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = scope:zg361_comp_portfolio_route }}"
            for mechanism_id in ids
        )
        special = ""
        if domain.key == "af" and state == 4:
            special = '''if = {
                    limit = {
                        var:zg361_comp_m297_consumed = 1
                        var:zg361_comp_m298_consumed = 1
                        var:zg361_comp_af_cliff_consumed = 1
                    }
                    if = {
                        limit = { NOT = { scope:zg361_comp_portfolio_route = 3 } }
                        zg361_comp_af_request_exit_effect = yes
                    }
                    else = {
                        # Snoozing records this vesting period. The next
                        # cadence tick may offer the one portfolio card again.
                        set_variable = {
                            name = zg361_comp_af_last_exit_offer_period
                            value = var:zg361_comp_af_periods_processed
                        }
                    }
                }
                else = {'''
            calls = special + "\n                    " + calls + "\n                }"
        keyword = "if" if state == 1 else "else_if"
        state_branches.append(
            f'''{keyword} = {{
                limit = {{ var:zg361_case_{domain.key}_state = {state} }}
                {calls}
            }}'''
        )
    return f'''if = {{
        limit = {{ var:zg361_comp_portfolio_domain = {DOMAINS.index(domain) + 1} }}
        var:zg361_comp_portfolio_subject = {{
            {chr(10).join(state_branches)}
        }}
    }}'''


def portfolio_pending_trigger(domain: DomainSpec) -> str:
    branches = []
    for state, ids in enumerate(domain.stages, start=1):
        missing = "\n                        ".join(
            f"var:zg361_comp_m{mechanism_id:03d}_consumed = 0" for mechanism_id in ids
        )
        # OR is required when a stage contains multiple writes.  A one-item
        # stage can use the same OR form without changing semantics.
        condition = f"OR = {{\n                        {missing}\n                    }}"
        if domain.key == "af" and state == 4:
            condition = f'''OR = {{
                        {missing}
                        AND = {{
                            var:zg361_comp_m297_consumed = 1
                            var:zg361_comp_m298_consumed = 1
                            var:zg361_comp_af_cliff_consumed = 1
                            var:zg361_comp_af_exit_requested = 0
                            var:zg361_comp_af_last_exit_offer_period < var:zg361_comp_af_periods_processed
                        }}
                    }}'''
        if domain.key == "ae" and state == 5:
            condition = f'''AND = {{
                        var:zg361_comp_ae_appeal_response_recorded = 1
                        {condition}
                    }}'''
        branches.append(f'''AND = {{
                    var:zg361_case_{domain.key}_state = {state}
                    {condition}
                }}''')
    return f'''AND = {{
            var:zg361_comp_portfolio_domain = {DOMAINS.index(domain) + 1}
            var:zg361_comp_portfolio_subject = {{
                var:zg361_case_{domain.key}_active = 1
                OR = {{
                    {chr(10).join(branches)}
                }}
            }}
        }}'''


def render_portfolio_helpers() -> str:
    opens = []
    for index, domain in enumerate(DOMAINS, start=1):
        opens.append(
            f'''if = {{
            limit = {{ var:zg361_comp_portfolio_domain = {index} }}
            var:zg361_comp_portfolio_subject = {{ zg361_comp_open_{domain.key}_case_effect = yes }}
        }}'''
        )
    dispatch = "\n    ".join(portfolio_domain_dispatch(domain) for domain in DOMAINS)
    pending = "\n        ".join(portfolio_pending_trigger(domain) for domain in DOMAINS)
    return f'''# Manager-scope portfolio adapter.  It owns one selected subject and one
# L/AE/AF case at a time; no numbered mechanism opens its own visible window.
zg361_comp_portfolio_open_next_effect = {{
    if = {{
        limit = {{
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            NOT = {{ has_character_flag = zg361_comp_portfolio_active }}
            trigger_if = {{
                limit = {{ has_variable = zg361_comp_portfolio_completed_cycle }}
                NOT = {{ var:zg361_comp_portfolio_completed_cycle = var:zg361_review_serial }}
            }}
            trigger_else = {{ always = yes }}
        }}
        if = {{
            limit = {{ NOT = {{ has_variable = zg361_comp_portfolio_domain }} }}
            set_variable = {{ name = zg361_comp_portfolio_domain value = 1 }}
        }}
        if = {{
            limit = {{
                var:zg361_comp_portfolio_domain = 1
                NOT = {{ has_variable = zg361_comp_portfolio_subject }}
            }}
            remove_variable = zg361_comp_portfolio_cycle
            remove_variable = zg361_comp_portfolio_subject
            remove_variable = zg361_comp_portfolio_result_owner
            remove_variable = zg361_comp_portfolio_result_subject
            remove_variable = zg361_comp_portfolio_result_cycle
            remove_variable = zg361_comp_portfolio_result_case
            remove_variable = zg361_comp_portfolio_result_state
            remove_variable = zg361_comp_portfolio_result_grade
            remove_variable = zg361_comp_portfolio_result_rating
            remove_variable = zg361_comp_portfolio_result_snapshot_applied
            ordered_vassal = {{
                limit = {{
                    zg361_is_reviewable_vassal_trigger = yes
                    liege = root
                    trigger_if = {{
                        limit = {{
                            has_variable = zg361_result_case_owner
                            has_variable = zg361_result_cycle_serial
                            has_variable = zg361_result_case_serial
                            has_variable = zg361_result_case_state
                            has_variable = zg361_result_grade
                            root = {{ has_variable = zg361_review_serial }}
                        }}
                        var:zg361_result_case_owner = root
                        var:zg361_result_cycle_serial = root.var:zg361_review_serial
                        var:zg361_result_case_state >= 3
                        OR = {{
                            var:zg361_result_grade = 1
                            var:zg361_result_grade = 2
                            var:zg361_result_grade = 3
                        }}
                    }}
                    trigger_else = {{ always = no }}
                }}
                order_by = stewardship
                position = 0
                save_temporary_scope_as = zg361_comp_portfolio_selected
                zg361_comp_freeze_current_result_effect = yes
            }}
        }}
        if = {{
            limit = {{
                var:zg361_comp_portfolio_domain <= 3
                has_variable = zg361_comp_portfolio_subject
                trigger_if = {{
                    limit = {{
                        has_variable = zg361_comp_portfolio_cycle
                        has_variable = zg361_comp_portfolio_result_owner
                        has_variable = zg361_comp_portfolio_result_subject
                        has_variable = zg361_comp_portfolio_result_cycle
                        has_variable = zg361_comp_portfolio_result_case
                        has_variable = zg361_comp_portfolio_result_state
                        has_variable = zg361_comp_portfolio_result_grade
                        has_variable = zg361_comp_portfolio_result_rating
                        has_variable = zg361_comp_portfolio_result_snapshot_applied
                    }}
                    var:zg361_comp_portfolio_cycle = var:zg361_review_serial
                    var:zg361_comp_portfolio_result_owner = root
                    var:zg361_comp_portfolio_result_subject = var:zg361_comp_portfolio_subject
                    var:zg361_comp_portfolio_result_cycle = var:zg361_review_serial
                    var:zg361_comp_portfolio_result_state >= 3
                    var:zg361_comp_portfolio_result_snapshot_applied = 1
                    OR = {{
                        AND = {{ var:zg361_comp_portfolio_result_grade = 1 var:zg361_comp_portfolio_result_rating = 325 }}
                        AND = {{ var:zg361_comp_portfolio_result_grade = 2 var:zg361_comp_portfolio_result_rating = 350 }}
                        AND = {{ var:zg361_comp_portfolio_result_grade = 3 var:zg361_comp_portfolio_result_rating = 375 }}
                    }}
                }}
                trigger_else = {{ always = no }}
            }}
            {chr(10).join(opens)}
            if = {{
                limit = {{
                    var:zg361_comp_portfolio_subject = {{
                        has_variable = zg361_comp_runtime_applied
                        var:zg361_comp_runtime_applied = 1
                    }}
                }}
                add_character_flag = zg361_comp_portfolio_active
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                zg361_comp_portfolio_refresh_effect = yes
            }}
            else = {{
                if = {{
                    limit = {{ var:zg361_comp_portfolio_domain = 1 }}
                    remove_variable = zg361_comp_portfolio_subject
                }}
            }}
        }}
        else_if = {{
            limit = {{ var:zg361_comp_portfolio_domain > 3 }}
            remove_variable = zg361_comp_portfolio_subject
            remove_variable = zg361_comp_portfolio_domain
            set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
            set_variable = {{ name = zg361_comp_portfolio_completed_cycle value = var:zg361_review_serial }}
        }}
    }}
}}

zg361_comp_portfolio_apply_stage_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_comp_portfolio_route value = $ROUTE$ }}
    if = {{
        limit = {{
            zg361_is_celestial_liege_trigger = yes
            has_character_flag = zg361_comp_portfolio_active
            has_variable = zg361_comp_portfolio_subject
            OR = {{
                scope:zg361_comp_portfolio_route = 1
                scope:zg361_comp_portfolio_route = 2
                scope:zg361_comp_portfolio_route = 3
            }}
        }}
        set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
        {dispatch}
        zg361_comp_portfolio_refresh_effect = yes
    }}
}}

zg361_comp_portfolio_refresh_effect = {{
    if = {{
        limit = {{
            has_character_flag = zg361_comp_portfolio_active
            has_variable = zg361_comp_portfolio_subject
            OR = {{
                {pending}
            }}
            var:zg361_comp_portfolio_visible_pending = 0
        }}
        set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 1 }}
        if = {{
            limit = {{ is_ai = yes }}
            trigger_event = {{ id = zg361comp.2 days = 1 }}
        }}
        else = {{ trigger_event = {{ id = zg361comp.1 days = 1 }} }}
    }}
}}

# Called from a subject-scoped write, deadline, or barrier. Only the frozen
# case owner may clear/re-arm its currently selected portfolio card.
zg361_comp_portfolio_notify_owner_effect = {{
    save_scope_as = zg361_comp_notify_subject
    save_temporary_scope_value_as = {{ name = zg361_comp_notify_domain value = $DOMAIN$ }}
    if = {{
        limit = {{ scope:zg361_comp_notify_domain = 1 has_variable = zg361_case_l_owner }}
        var:zg361_case_l_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    has_variable = zg361_comp_portfolio_subject
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_notify_subject
                }}
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                zg361_comp_portfolio_refresh_effect = yes
            }}
        }}
    }}
    else_if = {{
        limit = {{ scope:zg361_comp_notify_domain = 2 has_variable = zg361_case_ae_owner }}
        var:zg361_case_ae_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    has_variable = zg361_comp_portfolio_subject
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_notify_subject
                }}
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                zg361_comp_portfolio_refresh_effect = yes
            }}
        }}
    }}
    else_if = {{
        limit = {{ scope:zg361_comp_notify_domain = 3 has_variable = zg361_case_af_owner }}
        var:zg361_case_af_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    has_variable = zg361_comp_portfolio_subject
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_notify_subject
                }}
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                zg361_comp_portfolio_refresh_effect = yes
            }}
        }}
    }}
}}

zg361_comp_portfolio_case_closed_effect = {{
    save_scope_as = zg361_comp_closed_subject
    save_temporary_scope_value_as = {{ name = zg361_comp_closed_domain value = $DOMAIN$ }}
    if = {{
        limit = {{ scope:zg361_comp_closed_domain = 1 has_variable = zg361_case_l_owner }}
        var:zg361_case_l_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    has_variable = zg361_comp_portfolio_subject
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_closed_subject
                }}
                remove_character_flag = zg361_comp_portfolio_active
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                change_variable = {{ name = zg361_comp_portfolio_domain add = 1 }}
                trigger_event = {{ id = zg361comp.3 days = 1 }}
            }}
        }}
    }}
    else_if = {{
        limit = {{ scope:zg361_comp_closed_domain = 2 has_variable = zg361_case_ae_owner }}
        var:zg361_case_ae_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_closed_subject
                }}
                remove_character_flag = zg361_comp_portfolio_active
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                change_variable = {{ name = zg361_comp_portfolio_domain add = 1 }}
                trigger_event = {{ id = zg361comp.3 days = 1 }}
            }}
        }}
    }}
    else_if = {{
        limit = {{ scope:zg361_comp_closed_domain = 3 has_variable = zg361_case_af_owner }}
        var:zg361_case_af_owner = {{
            if = {{
                limit = {{
                    has_character_flag = zg361_comp_portfolio_active
                    var:zg361_comp_portfolio_subject = scope:zg361_comp_closed_subject
                }}
                remove_character_flag = zg361_comp_portfolio_active
                set_variable = {{ name = zg361_comp_portfolio_visible_pending value = 0 }}
                change_variable = {{ name = zg361_comp_portfolio_domain add = 1 }}
                trigger_event = {{ id = zg361comp.3 days = 1 }}
            }}
        }}
    }}
}}'''


def render_deadline_event(prefix: str, consumer: str) -> str:
    _, _, _, event_id = DEADLINES[prefix]
    return f'''{event_id} = {{
    type = character_event
    hidden = yes
    immediate = {{
        {expire_deadline(prefix)}
        if = {{
            limit = {{ var:zg361_case_kernel_applied = 1 }}
            {consumer} = yes
        }}
        else = {{ debug_log = "ZG361COMP: stale {prefix} five-field ticket ignored" }}
    }}
}}'''


def render_events() -> bytes:
    hidden = [
        render_deadline_event("l_deferred", "zg361_comp_l_consume_deferred_effect"),
        render_deadline_event("ae_due_90", "zg361_comp_ae_consume_due_effect"),
        render_deadline_event("ae_due_180", "zg361_comp_ae_consume_due_effect"),
        render_deadline_event("af_vest_30", "zg361_comp_af_consume_vest_effect"),
        render_deadline_event("af_vest_90", "zg361_comp_af_consume_vest_effect"),
        render_deadline_event("af_vest_180", "zg361_comp_af_consume_vest_effect"),
        render_deadline_event("af_vest_365", "zg361_comp_af_consume_vest_effect"),
        render_deadline_event("af_vest_730", "zg361_comp_af_consume_vest_effect"),
        render_deadline_event("af_buyback_90", "zg361_comp_af_consume_buyback_effect"),
    ]
    visible = r'''zg361comp.1 = {
    type = character_event
    theme = vassal
    title = zg361comp.1.t
    desc = zg361comp.1.desc
    trigger = {
        is_ai = no
        zg361_is_celestial_liege_trigger = yes
        has_character_flag = zg361_comp_portfolio_active
        var:zg361_comp_portfolio_visible_pending = 1
    }
    immediate = { set_variable = { name = zg361_comp_portfolio_visible_pending value = 0 } }
    option = { name = zg361comp.1.a zg361_comp_portfolio_apply_stage_effect = { ROUTE = 1 } }
    option = { name = zg361comp.1.b zg361_comp_portfolio_apply_stage_effect = { ROUTE = 2 } }
    option = { name = zg361comp.1.c zg361_comp_portfolio_apply_stage_effect = { ROUTE = 3 } }
}

# Authorized AI managers never open the visible portfolio card.
zg361comp.2 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                is_ai = yes
                zg361_is_celestial_liege_trigger = yes
                has_character_flag = zg361_comp_portfolio_active
            }
            set_variable = { name = zg361_comp_portfolio_visible_pending value = 0 }
            zg361_comp_portfolio_apply_stage_effect = { ROUTE = 1 }
        }
    }
}

zg361comp.3 = {
    type = character_event
    hidden = yes
    immediate = { zg361_comp_portfolio_open_next_effect = yes }
}

zg361comp.289 = {
    type = character_event
    theme = vassal
    title = zg361comp.289.t
    desc = zg361comp.289.desc
    trigger = { is_ai = no var:zg361_case_ae_state = 5 }
    option = { name = zg361comp.289.a zg361_comp_ae_subject_appeal_response_effect = { ROUTE = 1 } }
    option = { name = zg361comp.289.b zg361_comp_ae_subject_appeal_response_effect = { ROUTE = 2 } }
}

zg361comp.900 = {
    type = character_event
    theme = vassal
    title = zg361comp.900.t
    desc = zg361comp.900.desc
    trigger = { is_ai = no }
    option = { name = zg361comp.ok }
}

zg361comp.901 = {
    type = character_event
    theme = vassal
    title = zg361comp.901.t
    desc = zg361comp.901.desc
    trigger = { is_ai = no }
    option = { name = zg361comp.ok }
}

zg361comp.902 = {
    type = character_event
    theme = vassal
    title = zg361comp.902.t
    desc = zg361comp.902.desc
    trigger = { is_ai = no }
    option = { name = zg361comp.ok }
}

zg361comp.903 = {
    type = character_event
    theme = vassal
    title = zg361comp.903.t
    desc = zg361comp.903.desc
    trigger = { is_ai = no }
    option = { name = zg361comp.ok }
}

zg361comp.904 = {
    type = character_event
    theme = vassal
    title = zg361comp.904.t
    desc = zg361comp.904.desc
    trigger = { is_ai = no }
    option = { name = zg361comp.ok }
}'''
    return generated("namespace = zg361comp\n\n" + "\n\n".join(hidden) + "\n\n" + visible)


def render_effects() -> bytes:
    sections = [
        "# ZhongGuo 361 compensation/LTI runtime: L 082-091, AE 278-289, AF 290-300.",
        "# Routes: 1 = evidence/contract led; 2 = bounded alternative; 3 = defer/decline.",
        "# Honest boundary: generated CK3 source is static-ready until MCP-first live evidence exists.",
    ]
    for domain in DOMAINS:
        sections.append(
            f"# {domain.key.upper()} explicit state machine: "
            + " -> ".join(domain.states)
        )
        for stage, mechanism_ids in enumerate(domain.stages, start=1):
            sections.append(
                f"# {domain.key.upper()} stage {stage}: {domain.states[stage - 1]} -> "
                f"{domain.states[stage]}; writes "
                + ", ".join(f"{mechanism_id:03d}" for mechanism_id in mechanism_ids)
            )
    sections.append(render_result_snapshot_helpers())
    sections.extend(render_open(domain) for domain in DOMAINS)
    sections.append(render_financial_helpers())
    sections.append(render_account_helpers())
    sections.append(render_ae_runtime_helpers())
    sections.append(render_af_runtime_helpers())
    sections.append(render_portfolio_helpers())
    for mechanism in MECHANISMS:
        mechanism_id = mechanism.mechanism_id
        domain = mechanism.domain
        state = STAGE_BY_ID[mechanism_id]
        sections.append(render_manager_entry(mechanism_id, domain, state))
        sections.append(render_core(mechanism_id, domain, state))
        sections.append(render_consumer(mechanism_id, domain, state))
    for domain in DOMAINS:
        for state, ids in enumerate(domain.stages, start=1):
            if domain.key == "af" and state == 4:
                continue
            sections.append(render_barrier(domain, state, ids))
    return generated("\n\n".join(sections))


def render_english_localization() -> bytes:
    return localized(r'''l_english:
 zg361comp.1.t:0 "Compensation Portfolio"
 zg361comp.1.desc:0 "One sealed compensation case is before you. Choose the route for this stage; its numbered writes will be consumed together, never as thirty-three competing windows."
 zg361comp.1.a:0 "Follow the frozen contract and evidence."
 zg361comp.1.b:0 "Use the bounded alternative."
 zg361comp.1.c:0 "Defer or decline this stage."
 zg361comp.289.t:0 "Compensation Statement Appeal"
 zg361comp.289.desc:0 "The statement is itemized and the performance grade remains frozen. You may appeal the money account without reopening the rating track."
 zg361comp.289.a:0 "File a compensation-only appeal."
 zg361comp.289.b:0 "Accept the statement as served."
 zg361comp.900.t:0 "Compensation Case Settled"
 zg361comp.900.desc:0 "The award, its reserve, payments, refunds, and any bounded return now reconcile to the frozen contract."
 zg361comp.901.t:0 "Deferred Award Resolved"
 zg361comp.901.desc:0 "The delayed award has either vested into personal gold or returned to its original treasury and personal payers."
 zg361comp.902.t:0 "Pay Statement Closed"
 zg361comp.902.desc:0 "Promised, paid, owed, and returned amounts now share one closed statement. The frozen performance grade was not rewritten."
 zg361comp.903.t:0 "Long-Term Units Vested"
 zg361comp.903.desc:0 "A scheduled service tranche, and any performance tranche whose two gates opened, has moved into vested units."
 zg361comp.904.t:0 "Long-Term Incentive Settled"
 zg361comp.904.desc:0 "Exit classification and the FIFO liquidity request are closed without minting units or bypassing either payer."
 zg361comp.ok:0 "Record the receipt."
''')


def render_simp_chinese_localization() -> bytes:
    return localized(r'''l_simp_chinese:
 zg361comp.1.t:0 "薪酬案卷"
 zg361comp.1.desc:0 "一份封存的薪酬案卷正在候审。请选择本阶段路线；各编号写入会成组消费，绝不会化作三十三扇争相弹出的窗口。"
 zg361comp.1.a:0 "依冻结合同与证据执行。"
 zg361comp.1.b:0 "采用有界替代方案。"
 zg361comp.1.c:0 "延期或放弃本阶段。"
 zg361comp.289.t:0 "薪酬单申诉"
 zg361comp.289.desc:0 "薪酬单已经逐项列明，绩效档仍保持冻结。你可以申诉钱账，但不能借此重开绩效案轨。"
 zg361comp.289.a:0 "仅就薪酬账发起申诉。"
 zg361comp.289.b:0 "接受送达的薪酬单。"
 zg361comp.900.t:0 "薪酬案结清"
 zg361comp.900.desc:0 "授予、预留、支付、退款与有界追回已经按冻结合同完成对账。"
 zg361comp.901.t:0 "递延奖励已处理"
 zg361comp.901.desc:0 "延期奖励已经归属为个人金币，或按原比例退回最初的国库与个人付款人。"
 zg361comp.902.t:0 "薪酬单已关闭"
 zg361comp.902.desc:0 "应付、实付、欠付与退回归于同一份结清账单；冻结的绩效档没有被改写。"
 zg361comp.903.t:0 "长期份额归属"
 zg361comp.903.desc:0 "一批定时服务份额，以及同时通过组织与个人门槛的绩效份额，已经转为已归属。"
 zg361comp.904.t:0 "长期激励结清"
 zg361comp.904.desc:0 "离任分类与先进先出的流动性申请已经关闭；份额没有凭空增加，付款也没有绕过任何一方。"
 zg361comp.ok:0 "收存这份凭据。"
''')


def render_placeholder_localization(language: str) -> bytes:
    english = render_english_localization().decode("utf-8-sig")
    return localized(english.replace("l_english:", f"l_{language}:", 1))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_generated_compensation_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_generated_compensation_runtime_events.txt": render_events(),
        MOD_ROOT / "localization" / "english" / "zg361_compensation_runtime_l_english.yml": render_english_localization(),
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_compensation_runtime_l_simp_chinese.yml": render_simp_chinese_localization(),
    }
    for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_compensation_runtime_l_{language}.yml"
        ] = render_placeholder_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    if args.check:
        if stale:
            print("RED: stale compensation/LTI generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: compensation/LTI generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} compensation/LTI runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
