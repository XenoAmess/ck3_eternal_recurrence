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


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_career_hc_runtime.py\n"


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

# Subject-owned acknowledgements are separate from manager decisions.  They
# may be used by counts/barons on their own frozen case and never open/advance
# a case or consume the manager receipt.
SUBJECT_RESPONSE_IDS = frozenset(
    {19, 20, 24, 25, 92, 93, 94, 107, 108, 109, 112, 113, 114, 115, 116, 117, 119, 120}
)

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
    if not SUBJECT_RESPONSE_IDS <= set(EXPECTED_IDS):
        raise ValueError("subject response outside slice")


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
                limit = {{ var:zg361_case_kernel_applied = 1 }}
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


def render_domain_open(domain: DomainSpec) -> str:
    extra_q = "\n            zg361_is_celestial_liege_trigger = yes" if domain.key == "q" else ""
    receipt_resets = []
    cost_resets = []
    ids = list(domain_mechanisms(domain))
    for mechanism_id in ids:
        p = f"zg361_ch_m{mechanism_id:03d}"
        receipt_resets.extend(
            (
                f"set_variable = {{ name = {p}_receipt_active value = 0 }}",
                f"set_variable = {{ name = {p}_consumed value = 0 }}",
                f"set_variable = {{ name = {p}_subject_ack value = 0 }}",
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
        "q": "set_variable = { name = zg361_ch_manager_weight_hard value = 40 }\n        set_variable = { name = zg361_ch_manager_weight_people value = 30 }\n        set_variable = { name = zg361_ch_manager_weight_values value = 30 }",
    }[domain.key]
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
            limit = {{ var:zg361_case_kernel_applied = 1 }}
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
                root = {{ trigger_event = {{ id = zg361ch.{ids[0]} days = 1 }} }}
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


def render_subject_response(mechanism_id: int, domain: str, state: int) -> str:
    if mechanism_id not in SUBJECT_RESPONSE_IDS:
        return ""
    p = f"zg361_ch_m{mechanism_id:03d}"
    return f'''# Assessed-official self response; grants no manager/HC/panel authority.
zg361_career_hc_m{mechanism_id:03d}_subject_response_effect = {{
    save_temporary_scope_value_as = {{ name = zg361_ch_subject_route value = $ROUTE$ }}
    if = {{
        limit = {{
            is_ai = no
            zg361_case_kernel_subject_self_guard_trigger = {{
                SUBJECT_VAR = zg361_case_{domain}_subject
                ACTIVE_VAR = zg361_case_{domain}_active
            }}
            has_variable = zg361_case_{domain}_state
            var:zg361_case_{domain}_state = {state}
            var:{p}_subject_ack = 0
            OR = {{
                scope:zg361_ch_subject_route = 1
                scope:zg361_ch_subject_route = 2
                scope:zg361_ch_subject_route = 3
            }}
        }}
        set_variable = {{ name = {p}_subject_ack value = 1 }}
        set_variable = {{ name = {p}_subject_route value = scope:zg361_ch_subject_route }}
        change_variable = {{ name = zg361_case_{domain}_feedback_revision add = 1 }}
        debug_log = "ZG361CH: subject response {mechanism_id:03d} recorded"
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
                    limit = {{ var:zg361_case_kernel_applied = 1 }}
                    {transaction_journal(mechanism_id, domain, state, "gold")}
                }}
                if = {{
                    limit = {{
                        var:zg361_case_kernel_applied = 1
                        var:{p}_treasury_status = 2
                        var:{p}_gold_status = 2
                    }}
                    var:{row["owner"]} = {{
                        remove_treasury = 5
                        add_gold = {{ value = 0 subtract = 5 }}
                    }}
                    add_treasury = 5
                    add_gold = 5
                    set_variable = {{ name = {p}_dual_payment_settled value = 1 }}
                }}
            }}'''
    return f'''# {mechanism_id:03d} {MECHANISM_BEHAVIORS[mechanism_id].title_cn}
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
            limit = {{ var:zg361_case_kernel_applied = 1 }}
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
            limit = {{ var:zg361_case_kernel_applied = 1 }}
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
            limit = {{ var:zg361_case_kernel_applied = 1 }}
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
    if next_mechanism is not None:
        continuation = f"trigger_event = {{ id = zg361ch.{next_mechanism} days = 1 }}"
    elif NEXT_DOMAIN[domain.key] is not None:
        continuation = f"trigger_event = {{ id = zg361ch.{QUEUE_EVENTS[domain.key]} days = 1 }}"
    else:
        continuation = (
            f"scope:{scopes['subject']} = {{ "
            f"zg361_career_hc_finalize_{domain.key}_portfolio_effect = yes }}"
        )
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
        {continuation}
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
            if = {{
                limit = {{ zg361_is_celestial_liege_trigger = yes }}
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
        "# Public central surface: zg361_career_hc_open_portfolio_effect only.",
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
                response = render_subject_response(mechanism_id, domain.key, state)
                if response:
                    sections.append(response)
                sections.append(render_core(mechanism_id, domain.key, state))
                sections.append(render_consumer(mechanism_id, domain.key, state))
    sections.append(render_portfolio_finalizer(DOMAIN_BY_KEY["p"]))
    sections.append(render_portfolio_finalizer(DOMAIN_BY_KEY["q"]))
    return generated("\n\n".join(sections))


def render_events() -> bytes:
    sections = ["namespace = zg361ch"]
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
    return generated("\n\n".join(sections))


def localization_rows(language: str) -> list[str]:
    english = language != "simp_chinese"
    rows = [f"l_{language}:"]
    for domain_index, domain in enumerate(DOMAINS, start=1):
        event_id = 900 + domain_index
        title = f"361 Case Closed: {domain.title_en}" if english else f"三六一案卷已结：{domain.title_cn}"
        desc = (
            "The frozen career and headcount receipts have been consumed. The result now affects capacity, resources and the next review cycle."
            if english
            else "冻结的职业与编制回执均已消费。结论已经进入容量、资源与下一轮考核，不是一张只会喊口号的制度卡。"
        )
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
        title = behavior.behavior_key.replace("_", " ").title() if english else behavior.title_cn
        domain = DOMAIN_BY_ID[mechanism_id]
        desc = (
            f"Decide how this frozen {domain.title_en.lower()} case will handle {title}. "
            "The route is bound to this manager, official, review cycle, case and stage."
            if english
            else f"这份已冻结的{domain.title_cn}案卷来到“{title}”。"
            "路线会绑定上司、受评官员、考核周期、案卷与阶段，不能靠重开窗口改口。"
        )
        rows.extend(
            (
                f' zg361ch.m{mechanism_id:03d}.name:0 "{title}"',
                f' zg361ch.m{mechanism_id:03d}.desc:0 "{desc}"',
                f' zg361ch.m{mechanism_id:03d}.a:0 "Evidence-led route"' if english else f' zg361ch.m{mechanism_id:03d}.a:0 "按证据办"',
                f' zg361ch.m{mechanism_id:03d}.b:0 "Political route"' if english else f' zg361ch.m{mechanism_id:03d}.b:0 "按政治办"',
                f' zg361ch.m{mechanism_id:03d}.c:0 "Defer with recorded debt"' if english else f' zg361ch.m{mechanism_id:03d}.c:0 "延期，但欠账留痕"',
            )
        )
    return rows


def render_localization(language: str) -> bytes:
    source_language = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source_language)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_career_hc_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_career_hc_runtime_events.txt": render_events(),
    }
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
    if args.check:
        if stale:
            print("RED: stale career/HC generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: career/HC generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} career/HC runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
