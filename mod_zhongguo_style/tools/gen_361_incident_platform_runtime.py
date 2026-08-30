#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the CK3 static-ready runtime for mechanisms 192--228.

This projection owns only the X/Y/Z numbered behavior.  It deliberately
leaves the central review hooks, interactions and scoreboard untouched so the
integration coordinator can wire one public entry after the whole batch is
ready.  Every case uses the shared five-field case kernel and every numbered
operation keeps an idempotent receipt, an A/B/C route and a real result that is
consumed by the domain settlement.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from zg361_mechanism_data import load_mechanisms
from zg361_phase3_incident_platform_model import (
    BEHAVIORS,
    DOMAIN_EXECUTION_ORDER,
    EXPECTED_IDS,
)


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_incident_platform_runtime.py\n"

EFFECTS_PATH = MOD_ROOT / "common/scripted_effects/zg361_incident_platform_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events/zg361_incident_platform_runtime_events.txt"
LOC_BASENAME = "zg361_incident_platform_l_{language}.yml"

LANGUAGES: Final[tuple[str, ...]] = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)

# Numeric catalogue order is not always executable dependency order. Credit
# allocation (#197) consumes the immutable timeline (#201), so X must freeze
# that timeline before it allocates or nets incident credit.
EXECUTION_ORDER: Final[dict[str, tuple[int, ...]]] = DOMAIN_EXECUTION_ORDER
EXECUTION_STAGE: Final[dict[int, int]] = {
    192: 1, 195: 1, 196: 2, 200: 2, 201: 3, 197: 3,
    198: 4, 199: 4, 193: 5, 194: 5, 202: 6, 203: 6, 204: 7,
    205: 1, 206: 1, 207: 1, 208: 2, 209: 2, 210: 3,
    211: 3, 212: 3, 213: 4, 214: 4, 215: 5, 216: 5,
    217: 1, 218: 1, 219: 1, 220: 2, 221: 2, 222: 3,
    223: 3, 224: 3, 225: 4, 226: 4, 227: 5, 228: 5,
}


@dataclass(frozen=True)
class Domain:
    code: str
    slug: str
    first_id: int
    last_id: int
    transitions: int
    final_state: int
    event_base: int
    delays: tuple[int, ...]
    result_event: int
    name_cn: str
    name_en: str

    def stage_for(self, mechanism_id: int) -> int:
        return EXECUTION_STAGE[mechanism_id]

    def ids_for_stage(self, stage: int) -> tuple[int, ...]:
        return tuple(
            mechanism_id
            for mechanism_id in EXECUTION_ORDER[self.code]
            if self.stage_for(mechanism_id) == stage
        )


DOMAINS: Final[tuple[Domain, ...]] = (
    Domain("X", "x", 192, 204, 7, 8, 100, (7, 14, 14, 30, 60, 90), 190, "事故、值守与复盘", "Incident, on-call and postmortem"),
    Domain("Y", "y", 205, 216, 5, 6, 200, (30, 60, 90, 90), 290, "积弊、维护与交接", "Maintenance debt and handover"),
    Domain("Z", "z", 217, 228, 5, 6, 300, (30, 60, 60, 90), 390, "共享平台与内部开源", "Shared platform and inner source"),
)
DOMAIN_BY_ID: Final[dict[int, Domain]] = {
    mechanism_id: domain
    for domain in DOMAINS
    for mechanism_id in range(domain.first_id, domain.last_id + 1)
}


# Route values are frozen, deterministic CK3 facts.  The first field of every
# mechanism is its result score, which the domain settlement averages and then
# writes into the subject's next-cycle KPI.  The remaining fields are concrete
# dossier/resource facts and are also consumed by later operations or closure.
ASSIGNMENTS: Final[dict[int, dict[str, tuple[int, int, int]]]] = {
    192: {"rotation_depth": (3, 1, 0), "single_hero_load": (0, 80, 100)},
    193: {"pay_gold": (10, 0, 0), "timeoff_hours": (6, 0, 0), "compensation_debt": (0, 0, 14), "uncompensated_hours": (0, 10, 14)},
    194: {"target_relief_hours": (10, 0, 2), "unrelieved_hours": (0, 10, 8)},
    195: {"alert_total": (10, 10, 10), "false_alerts": (1, 4, 8), "miss_risk": (1, 6, 9)},
    196: {"reported_severity": (3, 2, 1), "corrected_severity": (4, 4, 4)},
    197: {"command_credit": (40, 20, 50), "responder_credit": (60, 80, 50)},
    198: {"root_cause_penalty": (20, 0, 5), "normal_failure": (1, 0, 0)},
    199: {"prevention_credit": (15, 0, 5), "observation_days": (90, 0, 180)},
    200: {"authority_scope": (2, 3, 0), "authority_days": (30, 90, 0), "command_log": (1, 0, 0)},
    201: {"timeline_nodes": (5, 2, 0), "timeline_locked": (1, 0, 0)},
    202: {"action_items": (2, 1, 0), "action_owner_bound": (1, 0, 0), "action_due_days": (30, 0, 0)},
    203: {"liability_level": (2, 1, 0), "resource_refusal_fact": (1, 0, 0)},
    204: {"reliability_spend": (40, 30, 10), "release_gate": (1, 0, 0)},
    205: {"toil_hours": (30, 50, 70), "delivery_hours": (70, 50, 30), "toil_cap": (40, 60, 80)},
    206: {"debt_principal": (20, 30, 40), "debt_interest": (2, 8, 15), "original_owner_visible": (1, 0, 1)},
    207: {"debt_budget_hours": (30, 0, 10), "business_hours": (70, 100, 90), "diversion_receipt": (0, 1, 1)},
    208: {"repair_route": (1, 2, 3), "repair_hours": (20, 30, 8), "debt_repayment": (20, 0, 8)},
    209: {"hazard_pay_gold": (10, 0, 0), "hazard_days": (365, 0, 180), "hazard_debt": (0, 0, 7)},
    210: {"owner_rotated": (1, 0, 1), "trained_backup": (1, 0, 0)},
    211: {"runbook_quality": (2, 0, 1), "non_author_validated": (1, 0, 0)},
    212: {"automation_saved_hours": (20, 0, 8), "automation_credit": (20, 0, 5)},
    213: {"validated_findings": (4, 0, 1), "review_hours": (5, 0, 2), "blocking_hours": (1, 0, 2)},
    214: {"coverage_percent": (80, 98, 60), "critical_misses": (0, 2, 1), "quality_score": (80, 35, 45)},
    215: {"legacy_retired": (1, 1, 0), "hc_released": (1, 1, 0), "necessity_appeal": (1, 0, 0)},
    216: {"handover_categories": (4, 0, 2), "handover_waiver": (0, 0, 1), "handover_percent": (100, 0, 50)},
    217: {"adoption_state": (1, 2, 3), "approved_exception": (1, 0, 1), "adopted_teams": (3, 5, 1)},
    218: {"customer_score": (70, 90, 50), "foundation_score": (75, 30, 80), "dual_floor": (60, 60, 60)},
    219: {"adoption_count": (3, 8, 1), "usage_depth": (80, 25, 60), "confirmed_saving": (30, 20, 10), "migration_burden": (10, 35, 5)},
    220: {"total_cost": (20, 20, 0), "treasury_cost": (12, 18, 0), "personal_cost": (8, 2, 0), "showback_cost": (20, 20, 20)},
    221: {"platform_share": (50, 0, 34), "user_share": (30, 100, 33), "reform_share": (20, 0, 33), "migration_hours": (30, 20, 0)},
    222: {"dual_run_hours": (20, 0, 40), "old_route_closed": (1, 1, 0), "exit_days": (90, 1, 0)},
    223: {"scan_complete": (1, 0, 1), "matched_assets": (1, 0, 1), "scan_decision": (1, 2, 3)},
    224: {"winner_code": (1, 1, 0), "loser_credit": (40, 0, 20), "rubric_frozen": (1, 0, 1)},
    225: {"fork_approved": (1, 0, 1), "fork_budget": (10, 0, 5), "upstream_first": (1, 0, 1)},
    226: {"accepted_submissions": (2, 5, 1), "contributor_credit": (60, 90, 40), "maintainer_credit": (40, 10, 60)},
    227: {"founder_credit": (20, 80, 33), "extension_credit": (40, 10, 33), "maintenance_credit": (40, 10, 34), "halo_decay": (10, 0, 5)},
    228: {"platform_liability": (60, 20, 33), "user_liability": (20, 70, 33), "policy_liability": (20, 10, 34), "total_loss": (100, 100, 100), "local_degrade": (1, 0, 1)},
}

SCORES: Final[dict[int, tuple[int, int, int]]] = {
    mechanism_id: (4, 1, -2) for mechanism_id in range(192, 229)
}

# A/B may consume only a current-case predecessor object. If an upstream item
# was deferred to C, the dependent item also becomes C instead of reading an
# A/B value left behind by an older review cycle.
CURRENT_OBJECT_DEPENDENCIES: Final[dict[int, tuple[int, ...]]] = {
    194: (193,),
    197: (201,),
    198: (197,),
    202: (201,),
    203: (202,),
    204: (196,),
    207: (206,),
    208: (206, 207),
    211: (210,),
    214: (213,),
    215: (214,),
    216: (215,),
    218: (217,),
    219: (218,),
    220: (219,),
    221: (220,),
    222: (221,),
    223: (222,),
    224: (223,),
    225: (224,),
    226: (225,),
    227: (226,),
    228: (227,),
}


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def _prefix(mechanism_id: int) -> str:
    return f"zg361_ip_m{mechanism_id:03d}"


def _domain_prefix(domain: Domain) -> str:
    return f"zg361_ip_{domain.slug}"


def _case_prefix(domain: Domain) -> str:
    return f"zg361_case_{domain.slug}"


def _ticket_args(domain: Domain, state: int, *, source: str = "core") -> str:
    prefix = _case_prefix(domain)
    if source == "deadline":
        owner = f"var:{_domain_prefix(domain)}_deadline_owner"
        subject = f"var:{_domain_prefix(domain)}_deadline_subject"
        cycle = f"var:{_domain_prefix(domain)}_deadline_cycle"
        case = f"var:{_domain_prefix(domain)}_deadline_case"
    else:
        owner = f"var:{prefix}_owner"
        subject = f"var:{prefix}_subject"
        cycle = f"var:{prefix}_cycle_serial"
        case = f"var:{prefix}_case_serial"
    return (
        f"TICKET_OWNER = {owner}\n"
        f"\t\tTICKET_SUBJECT = {subject}\n"
        f"\t\tTICKET_CYCLE = {cycle}\n"
        f"\t\tTICKET_CASE = {case}\n"
        f"\t\tTICKET_STATE = {state}"
    )


def _route_assignment(mechanism_id: int) -> str:
    prefix = _prefix(mechanism_id)
    behavior = BEHAVIORS[mechanism_id]
    lines: list[str] = []
    score = SCORES[mechanism_id]
    lines.append(f"\t\tset_variable = {{ name = {prefix}_result_score value = {score[0]} }}")
    lines.append("\t\tif = {")
    lines.append(f"\t\t\tlimit = {{ var:{prefix}_choice = 2 }}")
    lines.append(f"\t\t\tset_variable = {{ name = {prefix}_result_score value = {score[1]} }}")
    lines.append("\t\t}")
    lines.append("\t\telse_if = {")
    lines.append(f"\t\t\tlimit = {{ var:{prefix}_choice = 3 }}")
    lines.append(f"\t\t\tset_variable = {{ name = {prefix}_result_score value = {score[2]} }}")
    lines.append("\t\t}")
    lines.append("\t\tif = {")
    lines.append(f"\t\t\tlimit = {{ var:{prefix}_choice < 3 }}")
    for suffix, values in ASSIGNMENTS[mechanism_id].items():
        lines.append(f"\t\t\tset_variable = {{ name = {prefix}_{suffix} value = {values[0]} }}")
    lines.append("\t\t\tif = {")
    lines.append(f"\t\t\t\tlimit = {{ var:{prefix}_choice = 2 }}")
    for suffix, values in ASSIGNMENTS[mechanism_id].items():
        lines.append(f"\t\t\t\tset_variable = {{ name = {prefix}_{suffix} value = {values[1]} }}")
    lines.append("\t\t\t}")
    lines.extend(
        (
            f"\t\t\tset_variable = {{ name = {prefix}_business_object_created value = 1 }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_type_code value = {mechanism_id} }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_{behavior.object_type} value = 1 }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_owner value = $TICKET_OWNER$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_subject value = $TICKET_SUBJECT$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_cycle value = $TICKET_CYCLE$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_case value = $TICKET_CASE$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_state value = $TICKET_STATE$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_id value = {{ value = $TICKET_CYCLE$ multiply = 1000000 add = {{ value = $TICKET_CASE$ multiply = 1000 }} add = {mechanism_id} }} }}",
            f"\t\t\tset_variable = {{ name = {prefix}_consumer_contract value = {mechanism_id} }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_consumed value = 0 }}",
        )
    )
    for resource_book in behavior.resource_books:
        lines.append(f"\t\t\tset_variable = {{ name = {prefix}_resource_{resource_book} value = 1 }}")
    if behavior.deadline_cycles:
        lines.append(
            f"\t\t\tset_variable = {{ name = {prefix}_object_due_cycle value = "
            f"{{ value = $TICKET_CYCLE$ add = {behavior.deadline_cycles} }} }}"
        )
    lines.append("\t\t}")
    lines.append("\t\telse = {")
    lines.extend(
        (
            f"\t\t\tset_variable = {{ name = {prefix}_business_object_created value = 0 }}",
            f"\t\t\tset_variable = {{ name = {prefix}_object_consumed value = 0 }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_owner value = $TICKET_OWNER$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_subject value = $TICKET_SUBJECT$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_cycle value = $TICKET_CYCLE$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_case value = $TICKET_CASE$ }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }}",
            f"\t\t\tset_variable = {{ name = {prefix}_debt_open value = 1 }}",
            f"\t\t\tchange_variable = {{ name = zg361_ip_{DOMAIN_BY_ID[mechanism_id].slug}_policy_debt add = 1 }}",
        )
    )
    lines.append("\t\t}")
    return "\n".join(lines)


def _current_object_guard(mechanism_id: int) -> str:
    sources = CURRENT_OBJECT_DEPENDENCIES.get(mechanism_id, ())
    if not sources:
        return "always = yes"
    existence: list[str] = []
    reads: list[str] = []
    for source_id in sources:
        source = _prefix(source_id)
        behavior = BEHAVIORS[source_id]
        source_state = DOMAIN_BY_ID[source_id].stage_for(source_id)
        existence.extend(
            (
                f"has_variable = {source}_business_object_created",
                f"has_variable = {source}_object_type_code",
                f"has_variable = {source}_object_{behavior.object_type}",
                f"has_variable = {source}_object_owner",
                f"has_variable = {source}_object_subject",
                f"has_variable = {source}_object_cycle",
                f"has_variable = {source}_object_case",
                f"has_variable = {source}_object_state",
                f"has_variable = {source}_consumer_contract",
                f"has_variable = {source}_object_consumed",
                f"has_variable = {source}_consumer_{behavior.consumer_method}",
            )
        )
        reads.extend(
            (
                f"var:{source}_business_object_created = 1",
                f"var:{source}_object_type_code = {source_id}",
                f"var:{source}_object_{behavior.object_type} = 1",
                f"var:{source}_object_owner = $TICKET_OWNER$",
                f"var:{source}_object_subject = $TICKET_SUBJECT$",
                f"var:{source}_object_cycle = $TICKET_CYCLE$",
                f"var:{source}_object_case = $TICKET_CASE$",
                f"var:{source}_object_state = {source_state}",
                f"var:{source}_consumer_contract = {source_id}",
                f"var:{source}_object_consumed = 1",
                f"var:{source}_consumer_{behavior.consumer_method} = 1",
            )
        )
    return (
        "trigger_if = {\n"
        "\t\t\tlimit = {\n\t\t\t\t"
        + "\n\t\t\t\t".join(existence)
        + "\n\t\t\t}\n\t\t\t"
        + "\n\t\t\t".join(reads)
        + "\n\t\t}\n\t\ttrigger_else = { always = no }"
    )


def _special_consumer(mechanism_id: int) -> str:
    p = _prefix(mechanism_id)
    snippets: dict[int, str] = {
        192: f'''\t\tset_variable = {{ name = {p}_active_roster_size value = var:{p}_rotation_depth }}
\t\tset_variable = {{ name = {p}_single_point_risk value = 0 }}
\t\tif = {{ limit = {{ var:{p}_single_hero_load >= 80 }} set_variable = {{ name = {p}_single_point_risk value = 1 }} }}
\t\tset_variable = {{ name = {p}_roster_projection_frozen value = 1 }}''',
        193: f'''\t\t# Dual-payer on-call compensation: no partial debit is possible.
\t\tset_variable = {{ name = {p}_funded value = 0 }}
\t\tset_variable = {{ name = {p}_ledger_status value = 0 }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tvar:{p}_choice = 1
\t\t\t\tvar:zg361_case_x_owner = {{ government_has_flag = government_has_treasury treasury >= 6 gold >= 4 }}
\t\t\t}}
\t\t\tvar:zg361_case_x_owner = {{ remove_treasury = 6 remove_gold = 4 }}
\t\t\tadd_gold = 10
\t\t\tset_variable = {{ name = {p}_treasury_paid value = 6 }}
\t\t\tset_variable = {{ name = {p}_personal_paid value = 4 }}
\t\t\tset_variable = {{ name = {p}_recipient_credit value = 10 }}
\t\t\tset_variable = {{ name = {p}_funded value = 1 }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 2 }}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ var:{p}_choice = 1 }}
\t\t\tset_variable = {{ name = {p}_compensation_debt value = 10 }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 3 }}
\t\t\tchange_variable = {{ name = zg361_ip_x_score_delta add = -4 }}
\t\t}}
\t\telse_if = {{ limit = {{ var:{p}_choice = 3 }} set_variable = {{ name = {p}_ledger_status value = 3 }} }}''',
        194: f'''\t\tset_variable = {{ name = {p}_verified_compensation value = var:zg361_ip_m193_pay_gold }}''',
        195: f'''\t\tset_variable = {{ name = {p}_true_alerts value = {{ value = var:{p}_alert_total subtract = var:{p}_false_alerts max = 0 }} }}
\t\tset_variable = {{ name = {p}_alert_capacity_consumed value = var:{p}_alert_total }}
\t\tset_variable = {{ name = {p}_miss_risk_frozen value = var:{p}_miss_risk }}''',
        196: f'''\t\tset_variable = {{ name = {p}_integrity_gap value = {{ value = var:{p}_corrected_severity subtract = var:{p}_reported_severity }} }}''',
        197: f'''\t\tset_variable = {{ name = {p}_timeline_revision_used value = var:zg361_ip_m201_timeline_revision }}
\t\tset_variable = {{ name = {p}_credit_check value = {{ value = var:{p}_command_credit add = var:{p}_responder_credit }} }}
\t\tset_variable = {{ name = {p}_credit_conserved value = 0 }}
\t\tif = {{ limit = {{ var:{p}_credit_check = 100 }} set_variable = {{ name = {p}_credit_conserved value = 1 }} }}''',
        198: f'''\t\tset_variable = {{ name = {p}_net_firefighting_credit value = {{ value = var:zg361_ip_m197_responder_credit subtract = var:{p}_root_cause_penalty max = 0 }} }}''',
        199: f'''\t\tset_variable = {{ name = {p}_observation_window_frozen value = 1 }}
\t\tset_variable = {{ name = {p}_prevention_credit_pending value = 0 }}
\t\tif = {{ limit = {{ var:{p}_observation_days > 0 }} set_variable = {{ name = {p}_prevention_credit_pending value = 1 }} }}
\t\tset_variable = {{ name = {p}_credit_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }}''',
        200: f'''\t\tset_variable = {{ name = {p}_authority_bounded value = 0 }}
\t\tif = {{ limit = {{ var:{p}_authority_scope > 0 var:{p}_authority_days > 0 var:{p}_authority_days <= 90 }} set_variable = {{ name = {p}_authority_bounded value = 1 }} }}
\t\tset_variable = {{ name = {p}_authority_audit_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }}''',
        201: f'''\t\tset_variable = {{ name = {p}_timeline_revision value = 1 }}
\t\tset_variable = {{ name = {p}_timeline_deletions value = 0 }}
\t\tset_variable = {{ name = {p}_append_only_enforced value = var:{p}_timeline_locked }}''',
        202: f'''\t\tset_variable = {{ name = {p}_timeline_revision_used value = var:zg361_ip_m201_timeline_nodes }}''',
        203: f'''\t\tvar:zg361_case_x_owner = {{
\t\t\tif = {{ limit = {{ NOT = {{ has_variable = zg361_ip_incident_repeat_n }} }} set_variable = {{ name = zg361_ip_incident_repeat_n value = 0 }} }}
\t\t\tchange_variable = {{ name = zg361_ip_incident_repeat_n add = 1 }}
\t\t}}
\t\tset_variable = {{ name = {p}_action_items_used value = var:zg361_ip_m202_action_items }}''',
        204: f'''\t\tset_variable = {{ name = {p}_severity_fact_used value = var:zg361_ip_m196_corrected_severity }}
\t\tset_variable = {{ name = {p}_budget_remaining value = {{ value = 100 subtract = var:{p}_reliability_spend max = 0 }} }}
\t\tset_variable = {{ name = {p}_release_frozen value = 0 }}
\t\tif = {{ limit = {{ var:{p}_budget_remaining <= 60 }} set_variable = {{ name = {p}_release_frozen value = 1 }} }}''',
        205: f'''\t\tset_variable = {{ name = {p}_capacity_check value = {{ value = var:{p}_toil_hours add = var:{p}_delivery_hours }} }}''',
        206: f'''\t\tset_variable = {{ name = {p}_outstanding_debt value = {{ value = var:{p}_debt_principal add = var:{p}_debt_interest }} }}''',
        207: f'''\t\tset_variable = {{ name = {p}_capacity_check value = {{ value = var:{p}_debt_budget_hours add = var:{p}_business_hours }} }}
\t\tset_variable = {{ name = {p}_opening_debt_used value = var:zg361_ip_m206_outstanding_debt }}''',
        208: f'''\t\tset_variable = {{ name = {p}_debt_after_repayment value = {{ value = var:zg361_ip_m206_outstanding_debt subtract = var:{p}_debt_repayment max = 0 }} }}
\t\tset_variable = {{ name = {p}_budget_used value = var:zg361_ip_m207_debt_budget_hours }}''',
        209: f'''\t\t# Hazard pay uses the same six-plus-four dual-payer atomic precheck.
\t\tset_variable = {{ name = {p}_funded value = 0 }}
\t\tset_variable = {{ name = {p}_ledger_status value = 0 }}
\t\tif = {{
\t\t\tlimit = {{ var:{p}_choice = 1 var:zg361_case_y_owner = {{ government_has_flag = government_has_treasury treasury >= 6 gold >= 4 }} }}
\t\t\tvar:zg361_case_y_owner = {{ remove_treasury = 6 remove_gold = 4 }}
\t\t\tadd_gold = 10
\t\t\tset_variable = {{ name = {p}_treasury_paid value = 6 }}
\t\t\tset_variable = {{ name = {p}_personal_paid value = 4 }}
\t\t\tset_variable = {{ name = {p}_recipient_credit value = 10 }}
\t\t\tset_variable = {{ name = {p}_funded value = 1 }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 2 }}
\t\t}}
\t\telse_if = {{ limit = {{ var:{p}_choice = 1 }} set_variable = {{ name = {p}_hazard_debt value = 10 }} set_variable = {{ name = {p}_ledger_status value = 3 }} change_variable = {{ name = zg361_ip_y_score_delta add = -4 }} }}
\t\telse_if = {{ limit = {{ var:{p}_choice = 3 }} set_variable = {{ name = {p}_ledger_status value = 3 }} }}''',
        210: f'''\t\tset_variable = {{ name = {p}_handover_required value = var:{p}_owner_rotated }}''',
        211: f'''\t\tset_variable = {{ name = {p}_rotation_used value = var:zg361_ip_m210_owner_rotated }}''',
        212: f'''\t\tset_variable = {{ name = {p}_future_capacity_credit value = var:{p}_automation_saved_hours }}''',
        213: f'''\t\tset_variable = {{ name = {p}_review_credit value = var:{p}_validated_findings }}
\t\tset_variable = {{ name = {p}_comment_count_used value = 0 }}
\t\tset_variable = {{ name = {p}_review_capacity_used value = {{ value = var:{p}_review_hours add = var:{p}_blocking_hours }} }}''',
        214: f'''\t\tset_variable = {{ name = {p}_review_findings_used value = var:zg361_ip_m213_validated_findings }}''',
        215: f'''\t\tset_variable = {{ name = {p}_quality_gate_used value = var:zg361_ip_m214_quality_score }}''',
        216: f'''\t\tset_variable = {{ name = {p}_retirement_gate_used value = var:zg361_ip_m215_legacy_retired }}''',
        217: f'''\t\tset_variable = {{ name = {p}_adoption_policy_frozen value = 1 }}
\t\tset_variable = {{ name = {p}_exception_receipt_required value = var:{p}_approved_exception }}
\t\tset_variable = {{ name = {p}_adoption_count_consumed value = var:{p}_adopted_teams }}''',
        218: f'''\t\tset_variable = {{ name = {p}_full_high_eligible value = 0 }}
\t\tif = {{ limit = {{ var:{p}_customer_score >= var:{p}_dual_floor var:{p}_foundation_score >= var:{p}_dual_floor }} set_variable = {{ name = {p}_full_high_eligible value = 1 }} }}
\t\tset_variable = {{ name = {p}_adoption_policy_used value = var:zg361_ip_m217_adoption_state }}''',
        219: f'''\t\tset_variable = {{ name = {p}_net_value value = {{ value = var:{p}_confirmed_saving subtract = var:{p}_migration_burden }} }}
\t\tset_variable = {{ name = {p}_dual_score_gate value = var:zg361_ip_m218_full_high_eligible }}''',
        220: f'''\t\t# Platform settlement also debits organization and manager atomically.
\t\tset_variable = {{ name = {p}_funded value = 0 }}
\t\tset_variable = {{ name = {p}_ledger_status value = 0 }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tvar:{p}_total_cost > 0
\t\t\t\tvar:zg361_case_z_owner = {{
\t\t\t\t\tgovernment_has_flag = government_has_treasury
\t\t\t\t\ttreasury >= var:{p}_treasury_cost
\t\t\t\t\tgold >= var:{p}_personal_cost
\t\t\t\t}}
\t\t\t}}
\t\t\tvar:zg361_case_z_owner = {{ remove_treasury = var:{p}_treasury_cost remove_gold = var:{p}_personal_cost }}
\t\t\tset_variable = {{ name = {p}_treasury_paid value = var:{p}_treasury_cost }}
\t\t\tset_variable = {{ name = {p}_personal_paid value = var:{p}_personal_cost }}
\t\t\tset_variable = {{ name = {p}_paid_total value = var:{p}_total_cost }}
\t\t\tset_variable = {{ name = {p}_funded value = 1 }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 2 }}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ var:{p}_total_cost > 0 }}
\t\t\tset_variable = {{ name = {p}_cost_debt value = var:{p}_total_cost }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 3 }}
\t\t\tchange_variable = {{ name = zg361_ip_z_score_delta add = -4 }}
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ var:{p}_choice = 3 }}
\t\t\tset_variable = {{ name = {p}_cost_debt value = var:{p}_showback_cost }}
\t\t\tset_variable = {{ name = {p}_ledger_status value = 3 }}
\t\t}}
\t\tset_variable = {{ name = {p}_value_metric_used value = var:zg361_ip_m219_net_value }}''',
        221: f'''\t\tset_variable = {{ name = {p}_share_check value = {{ value = var:{p}_platform_share add = var:{p}_user_share add = var:{p}_reform_share }} }}
\t\tset_variable = {{ name = {p}_cost_receipt_used value = var:zg361_ip_m220_funded }}''',
        222: f'''\t\tset_variable = {{ name = {p}_migration_plan_used value = var:zg361_ip_m221_migration_hours }}''',
        223: f'''\t\tset_variable = {{ name = {p}_dual_run_exit_used value = var:zg361_ip_m222_old_route_closed }}''',
        224: f'''\t\tset_variable = {{ name = {p}_scan_receipt_used value = var:zg361_ip_m223_scan_complete }}''',
        225: f'''\t\tset_variable = {{ name = {p}_merger_rubric_used value = var:zg361_ip_m224_rubric_frozen }}''',
        226: f'''\t\tset_variable = {{ name = {p}_credit_check value = {{ value = var:{p}_contributor_credit add = var:{p}_maintainer_credit }} }}
\t\tset_variable = {{ name = {p}_fork_policy_used value = var:zg361_ip_m225_upstream_first }}''',
        227: f'''\t\tset_variable = {{ name = {p}_credit_check value = {{ value = var:{p}_founder_credit add = var:{p}_extension_credit add = var:{p}_maintenance_credit }} }}
\t\tset_variable = {{ name = {p}_inner_source_used value = var:zg361_ip_m226_accepted_submissions }}''',
        228: f'''\t\tset_variable = {{ name = {p}_liability_check value = {{ value = var:{p}_platform_liability add = var:{p}_user_liability add = var:{p}_policy_liability }} }}
\t\tset_variable = {{ name = {p}_role_ledger_used value = var:zg361_ip_m227_credit_check }}''',
    }
    return snippets.get(mechanism_id, "")


def render_mechanism_effect(mechanism_id: int) -> str:
    domain = DOMAIN_BY_ID[mechanism_id]
    stage = domain.stage_for(mechanism_id)
    prefix = _prefix(mechanism_id)
    case = _case_prefix(domain)
    dp = _domain_prefix(domain)
    special = _special_consumer(mechanism_id)
    behavior = BEHAVIORS[mechanism_id]
    return f'''# {mechanism_id:03d}: one receipted A/B/C operation in {domain.code} stage {stage}.
{prefix}_apply_effect = {{
\tset_variable = {{ name = {prefix}_choice value = 1 }}
\tif = {{
\t\tlimit = {{ var:{case}_owner = {{ has_variable = zg361_mechanism_{mechanism_id:03d}_choice }} }}
\t\tif = {{ limit = {{ var:{case}_owner.var:zg361_mechanism_{mechanism_id:03d}_choice = 2 }} set_variable = {{ name = {prefix}_choice value = 2 }} }}
\t\telse_if = {{ limit = {{ var:{case}_owner.var:zg361_mechanism_{mechanism_id:03d}_choice = 3 }} set_variable = {{ name = {prefix}_choice value = 3 }} }}
\t}}
\telse_if = {{
\t\tlimit = {{ var:{case}_owner = {{ is_ai = yes is_at_war = yes }} }}
\t\tset_variable = {{ name = {prefix}_choice value = 3 }}
\t}}
\telse_if = {{
\t\tlimit = {{ var:{case}_owner = {{ is_ai = yes stewardship < 10 }} }}
\t\tset_variable = {{ name = {prefix}_choice value = 2 }}
\t}}
\tif = {{
\t\tlimit = {{
\t\t\tvar:{prefix}_choice < 3
\t\t\tNOT = {{
{_current_object_guard(mechanism_id)}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {prefix}_choice value = 3 }}
\t\tset_variable = {{ name = {prefix}_prerequisite_deferred value = 1 }}
\t}}
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {prefix}_done_owner has_variable = {prefix}_done_subject has_variable = {prefix}_done_cycle has_variable = {prefix}_done_case has_variable = {prefix}_done_state }}
\t\t\t\tOR = {{
\t\t\t\t\tNOT = {{ var:{prefix}_done_owner = $TICKET_OWNER$ }}
\t\t\t\t\tNOT = {{ var:{prefix}_done_subject = $TICKET_SUBJECT$ }}
\t\t\t\t\tNOT = {{ var:{prefix}_done_cycle = $TICKET_CYCLE$ }}
\t\t\t\t\tNOT = {{ var:{prefix}_done_case = $TICKET_CASE$ }}
\t\t\t\t\tNOT = {{ var:{prefix}_done_state = $TICKET_STATE$ }}
\t\t\t\t}}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tzg361_case_kernel_record_operation_effect = {{
\t\t\tOWNER_VAR = {case}_owner
\t\t\tSUBJECT_VAR = {case}_subject
\t\t\tCYCLE_VAR = {case}_cycle_serial
\t\t\tCASE_VAR = {case}_case_serial
\t\t\tSTATE_VAR = {case}_state
\t\t\tREVISION_VAR = {case}_revision
\t\t\tACTIVE_VAR = {case}_active
\t\t\tTIMELINE_VAR = {case}_timeline_serial
\t\t\tFEEDBACK_VAR = {case}_feedback_revision
\t\t\tLAST_OPERATION_VAR = {case}_last_operation
\t\t\tLAST_CHOICE_VAR = {case}_last_choice
\t\t\tRECEIPT_OWNER_VAR = {prefix}_receipt_owner
\t\t\tRECEIPT_SUBJECT_VAR = {prefix}_receipt_subject
\t\t\tRECEIPT_CYCLE_VAR = {prefix}_receipt_cycle
\t\t\tRECEIPT_CASE_VAR = {prefix}_receipt_case
\t\t\tRECEIPT_STATE_VAR = {prefix}_receipt_state
\t\t\tRECEIPT_CHOICE_VAR = {prefix}_receipt_choice
\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\tTICKET_STATE = $TICKET_STATE$
\t\t\tCHOICE = var:{prefix}_choice
\t\t\tOPERATION_ID = {mechanism_id}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
{_route_assignment(mechanism_id)}
\t\t\t\tchange_variable = {{ name = {dp}_score_delta add = var:{prefix}_result_score }}
\t\t\t\tchange_variable = {{ name = {dp}_evidence_n add = 1 }}
\t\t\t\tset_variable = {{ name = {dp}_last_consumer value = {mechanism_id} }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ var:{prefix}_business_object_created = 1 }}
{special}
\t\t\t\t\tset_variable = {{ name = {prefix}_consumer_{behavior.consumer_method} value = 1 }}
\t\t\t\t\tset_variable = {{ name = {prefix}_object_consumed value = 1 }}
\t\t\t\t}}
\t\t\t\telse = {{ set_variable = {{ name = {prefix}_debt_visible_to_settlement value = 1 }} }}
\t\t\t\tset_variable = {{ name = {prefix}_done_owner value = $TICKET_OWNER$ }}
\t\t\t\tset_variable = {{ name = {prefix}_done_subject value = $TICKET_SUBJECT$ }}
\t\t\t\tset_variable = {{ name = {prefix}_done_cycle value = $TICKET_CYCLE$ }}
\t\t\t\tset_variable = {{ name = {prefix}_done_case value = $TICKET_CASE$ }}
\t\t\t\tset_variable = {{ name = {prefix}_done_state value = $TICKET_STATE$ }}
\t\t\t}}
\t\t}}
\t}}
}}'''


def _done_guard(mechanism_id: int) -> str:
    p = _prefix(mechanism_id)
    return f'''\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {p}_done_owner has_variable = {p}_done_subject has_variable = {p}_done_cycle has_variable = {p}_done_case has_variable = {p}_done_state }}
\t\t\t\tvar:{p}_done_owner = $TICKET_OWNER$
\t\t\t\tvar:{p}_done_subject = $TICKET_SUBJECT$
\t\t\t\tvar:{p}_done_cycle = $TICKET_CYCLE$
\t\t\t\tvar:{p}_done_case = $TICKET_CASE$
\t\t\t\tvar:{p}_done_state = $TICKET_STATE$
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}'''


def _schedule_block(domain: Domain, next_state: int) -> str:
    dp = _domain_prefix(domain)
    case = _case_prefix(domain)
    delay = domain.delays[next_state - 2]
    event_id = domain.event_base + next_state
    return f'''\t\t\tzg361_case_kernel_schedule_deadline_effect = {{
\t\t\t\tOWNER_VAR = {case}_owner
\t\t\t\tSUBJECT_VAR = {case}_subject
\t\t\t\tCYCLE_VAR = {case}_cycle_serial
\t\t\t\tCASE_VAR = {case}_case_serial
\t\t\t\tSTATE_VAR = {case}_state
\t\t\t\tACTIVE_VAR = {case}_active
\t\t\t\tDEADLINE_OWNER_VAR = {dp}_deadline_owner
\t\t\t\tDEADLINE_SUBJECT_VAR = {dp}_deadline_subject
\t\t\t\tDEADLINE_CYCLE_VAR = {dp}_deadline_cycle
\t\t\t\tDEADLINE_CASE_VAR = {dp}_deadline_case
\t\t\t\tDEADLINE_STATE_VAR = {dp}_deadline_state
\t\t\t\tDEADLINE_DAYS_VAR = {dp}_deadline_days
\t\t\t\tDEADLINE_PENDING_VAR = {dp}_deadline_pending
\t\t\t\tDEADLINE_EXPIRED_VAR = {dp}_deadline_expired
\t\t\t\tTICKET_OWNER = var:{case}_owner
\t\t\t\tTICKET_SUBJECT = var:{case}_subject
\t\t\t\tTICKET_CYCLE = var:{case}_cycle_serial
\t\t\t\tTICKET_CASE = var:{case}_case_serial
\t\t\t\tTICKET_STATE = {next_state}
\t\t\t\tDAYS = {delay}
\t\t\t\tEVENT = zg361ip.{event_id}
\t\t\t}}'''


def render_stage_dispatcher(domain: Domain, stage: int) -> str:
    ids = domain.ids_for_stage(stage)
    case = _case_prefix(domain)
    calls = "\n".join(
        f'''\t{_prefix(mechanism_id)}_apply_effect = {{
\t\tTICKET_OWNER = $TICKET_OWNER$
\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\tTICKET_CASE = $TICKET_CASE$
\t\tTICKET_STATE = {stage}
\t}}'''
        for mechanism_id in ids
    )
    guards = "\n".join(_done_guard(mechanism_id) for mechanism_id in ids)
    next_state = stage + 1
    after = (
        f"\n{_schedule_block(domain, next_state)}"
        if next_state < domain.final_state
        else f"\n\t\t\tzg361_ip_finalize_{domain.slug}_effect = yes"
    )
    close = "yes" if next_state == domain.final_state else "no"
    return f'''# {domain.code} stage {stage}: all operations settle before the sole transition.
zg361_ip_{domain.slug}_dispatch_{stage:02d}_effect = {{
{calls}
\tif = {{
\t\tlimit = {{
{guards}
\t\t}}
\t\tzg361_case_{domain.slug}_advance_{stage:02d}_effect = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}{after}
\t\t\t}}
\t\t}}
\t}}
}}'''


def render_finalize(domain: Domain) -> str:
    dp = _domain_prefix(domain)
    case = _case_prefix(domain)
    return f'''# {domain.code} closure: average all numbered outputs and affect the next review.
zg361_ip_finalize_{domain.slug}_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {case}_state
\t\t\thas_variable = {case}_active
\t\t\tvar:{case}_state = {domain.final_state}
\t\t\tvar:{case}_active = 0
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {dp}_final_case }}
\t\t\t\tNOT = {{ var:{dp}_final_case = var:{case}_case_serial }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = {dp}_final_score value = 0 }}
\t\tif = {{
\t\t\tlimit = {{ var:{dp}_evidence_n > 0 }}
\t\t\tset_variable = {{ name = {dp}_final_score value = {{ value = var:{dp}_score_delta divide = var:{dp}_evidence_n round = yes max = 4 min = -4 }} }}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_kpi_value }}
\t\t\tchange_variable = {{ name = zg361_kpi_value add = var:{dp}_final_score }}
\t\t}}
\t\telse = {{ set_variable = {{ name = zg361_kpi_value value = var:{dp}_final_score }} }}
\t\tset_variable = {{ name = {dp}_final_owner value = var:{case}_owner }}
\t\tset_variable = {{ name = {dp}_final_subject value = var:{case}_subject }}
\t\tset_variable = {{ name = {dp}_final_cycle value = var:{case}_cycle_serial }}
\t\tset_variable = {{ name = {dp}_final_case value = var:{case}_case_serial }}
\t\tset_variable = {{ name = {dp}_final_state value = {domain.final_state} }}
\t\tset_variable = {{ name = {dp}_final_revision value = var:{case}_revision }}
\t\tsave_scope_as = zg361_ip_result_subject
\t\tif = {{
\t\t\tlimit = {{ var:{case}_owner = {{ is_alive = yes is_ai = no }} }}
\t\t\tvar:{case}_owner = {{ trigger_event = {{ id = zg361ip.{domain.result_event} }} }}
\t\t}}
\t\tdebug_log = "ZG361IP: {domain.code} case closed and next-cycle KPI consumed"
\t}}
}}'''


def render_open_on_subject(domain: Domain) -> str:
    dp = _domain_prefix(domain)
    case = _case_prefix(domain)
    return f'''# Subject-scope entry; ROOT must be the eligible direct manager.
zg361_ip_open_{domain.slug}_case_on_subject_effect = {{
\tif = {{ limit = {{ has_variable = {dp}_final_score }} set_variable = {{ name = {dp}_previous_final_score value = var:{dp}_final_score }} }}
\tzg361_case_{domain.slug}_open_effect = yes
\tif = {{
\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
\t\t\tset_variable = {{ name = {dp}_score_delta value = 0 }}
\t\t\tset_variable = {{ name = {dp}_evidence_n value = 0 }}
\t\t\tset_variable = {{ name = {dp}_last_consumer value = 0 }}
\t\t\tif = {{ limit = {{ NOT = {{ has_variable = {dp}_policy_debt }} }} set_variable = {{ name = {dp}_policy_debt value = 0 }} }}
\t\t\tset_variable = {{ name = {dp}_deadline_pending value = 0 }}
\t\t\tset_variable = {{ name = {dp}_deadline_expired value = 0 }}
\t\t\tzg361_ip_{domain.slug}_dispatch_01_effect = {{
\t\t\t\tTICKET_OWNER = var:{case}_owner
\t\t\t\tTICKET_SUBJECT = var:{case}_subject
\t\t\t\tTICKET_CYCLE = var:{case}_cycle_serial
\t\t\t\tTICKET_CASE = var:{case}_case_serial
\t\t\t}}
\t\t}}
\t}}
}}

# Public integration entry. It grants no authority of its own: the shared open
# trigger still requires a landed celestial duke-or-higher direct manager.
zg361_ip_open_{domain.slug}_case_effect = {{
\t$SUBJECT$ = {{ zg361_ip_open_{domain.slug}_case_on_subject_effect = yes }}
}}'''


def render_due_effect(domain: Domain, state: int) -> str:
    dp = _domain_prefix(domain)
    case = _case_prefix(domain)
    return f'''zg361_ip_{domain.slug}_due_{state:02d}_effect = {{
\tzg361_case_kernel_expire_deadline_effect = {{
\t\tOWNER_VAR = {case}_owner
\t\tSUBJECT_VAR = {case}_subject
\t\tCYCLE_VAR = {case}_cycle_serial
\t\tCASE_VAR = {case}_case_serial
\t\tSTATE_VAR = {case}_state
\t\tREVISION_VAR = {case}_revision
\t\tACTIVE_VAR = {case}_active
\t\tTIMELINE_VAR = {case}_timeline_serial
\t\tFEEDBACK_VAR = {case}_feedback_revision
\t\tDEADLINE_OWNER_VAR = {dp}_deadline_owner
\t\tDEADLINE_SUBJECT_VAR = {dp}_deadline_subject
\t\tDEADLINE_CYCLE_VAR = {dp}_deadline_cycle
\t\tDEADLINE_CASE_VAR = {dp}_deadline_case
\t\tDEADLINE_STATE_VAR = {dp}_deadline_state
\t\tDEADLINE_PENDING_VAR = {dp}_deadline_pending
\t\tDEADLINE_EXPIRED_VAR = {dp}_deadline_expired
\t}}
\tif = {{
\t\tlimit = {{ has_variable = zg361_case_kernel_applied }}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_case_kernel_applied = 1 }}
\t\t\tzg361_ip_{domain.slug}_dispatch_{state:02d}_effect = {{
\t\t\t\t{_ticket_args(domain, state, source="deadline")}
\t\t\t}}
\t\t}}
\t}}
}}'''


def render_effects() -> bytes:
    sections: list[str] = [
        "# X/Y/Z phase-three runtime. Readiness: CK3 static-ready; not live.\n"
        "# Public entries are zg361_ip_open_{x,y,z}_case_effect and\n"
        "# zg361_ip_open_portfolio_effect. No GUI/on_action/interactions are added."
    ]
    sections.extend(render_mechanism_effect(mechanism_id) for mechanism_id in range(192, 229))
    for domain in DOMAINS:
        sections.append(render_finalize(domain))
        sections.extend(render_stage_dispatcher(domain, stage) for stage in range(1, domain.transitions + 1))
        sections.extend(render_due_effect(domain, state) for state in range(2, domain.final_state))
        sections.append(render_open_on_subject(domain))
    sections.append(r'''# Single integration hook: open the three independent cases for one bounded
# direct assessed official. Counts/barons are valid subjects but never ROOT here.
zg361_ip_open_portfolio_effect = {
	if = {
		limit = {
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			has_variable = zg361_review_serial
			any_vassal = { zg361_is_reviewable_vassal_trigger = yes }
			trigger_if = {
				limit = { has_variable = zg361_ip_portfolio_cycle }
				NOT = { var:zg361_ip_portfolio_cycle = var:zg361_review_serial }
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = zg361_ip_portfolio_cycle value = var:zg361_review_serial }
		ordered_vassal = {
			limit = { zg361_is_reviewable_vassal_trigger = yes }
			order_by = stewardship
			zg361_ip_open_x_case_on_subject_effect = yes
			zg361_ip_open_y_case_on_subject_effect = yes
			zg361_ip_open_z_case_on_subject_effect = yes
		}
	}
}''')
    return generated("\n\n".join(sections))


def render_events() -> bytes:
    sections = ["namespace = zg361ip"]
    for domain in DOMAINS:
        for state in range(2, domain.final_state):
            event_id = domain.event_base + state
            sections.append(f'''# {domain.code} state {state} bound deadline.
zg361ip.{event_id} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ zg361_ip_{domain.slug}_due_{state:02d}_effect = yes }}
}}''')
        sections.append(f'''# Player manager closure notice; authorized AI managers remain silent.
zg361ip.{domain.result_event} = {{
\ttype = character_event
\ttheme = vassal
\ttitle = zg361ip.{domain.result_event}.t
\tdesc = zg361ip.{domain.result_event}.desc
\ttrigger = {{ is_ai = no has_game_rule = zg361_on exists = scope:zg361_ip_result_subject }}
\toption = {{ name = zg361ip.result.ok }}
}}''')
    return generated("\n\n".join(sections))


def _loc_rows(language: str) -> dict[str, str]:
    mechanisms = {
        row.id: row
        for row in load_mechanisms(MOD_ROOT)
        if 192 <= row.id <= 228
    }
    english: dict[str, str] = {
        "zg361ip.result.ok": "Archive the receipts",
        "zg361ip.190.t": "Incident postmortem closed",
        "zg361ip.190.desc": "The on-call, severity, immutable timeline, action owners and reliability budget have settled. The averaged result now affects the assessed official's next review.",
        "zg361ip.290.t": "Maintenance ledger closed",
        "zg361ip.290.desc": "Toil, debt interest, protected repayment capacity, quality gates, retirement and handover have settled into a receipted maintenance result.",
        "zg361ip.390.t": "Shared platform account closed",
        "zg361ip.390.desc": "Adoption, dual scores, migration, platform costs, inner-source credit and blast-radius liability have settled without merging their ledgers.",
    }
    chinese: dict[str, str] = {
        "zg361ip.result.ok": "把回执归档",
        "zg361ip.190.t": "事故复盘结案",
        "zg361ip.190.desc": "值守、事故定级、不可改写时间线、行动项与可靠性预算均已结算；汇总结果将进入受评官员的下一轮考核。",
        "zg361ip.290.t": "积弊账结案",
        "zg361ip.290.desc": "重复运维、积弊本息、固定偿债工时、质量关、旧务退役与离岗交接，已经合成一份有回执的维护结果。",
        "zg361ip.390.t": "共享平台分账结案",
        "zg361ip.390.desc": "采用、客户与底座双分、迁移、平台成本、内部开源分功和爆炸半径责任已经分别结算，不再用一张大饼糊过去。",
    }
    for mechanism_id, row in mechanisms.items():
        english[f"zg361_ip_m{mechanism_id:03d}_name"] = row.title_en
        english[f"zg361_ip_m{mechanism_id:03d}_result"] = (
            f"Mechanism {mechanism_id:03d} froze an A/B/C route, a five-field receipt and a result consumed by its domain settlement."
        )
        chinese[f"zg361_ip_m{mechanism_id:03d}_name"] = row.title_cn
        chinese[f"zg361_ip_m{mechanism_id:03d}_result"] = (
            f"机制 {mechanism_id:03d} 已冻结 A/B/C 路径、五元回执，并把结果送入本领域结算。"
        )
    return chinese if language == "simp_chinese" else english


def render_localization(language: str) -> bytes:
    rows = _loc_rows(language)
    body = [f"l_{language}:"]
    for key, value in rows.items():
        escaped = value.replace('"', '\\"')
        body.append(f' {key}:0 "{escaped}"')
    return localized("\n".join(body))


def outputs() -> dict[Path, bytes]:
    rendered = {EFFECTS_PATH: render_effects(), EVENTS_PATH: render_events()}
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / LOC_BASENAME.format(language=language)
        ] = render_localization(language)
    return rendered


def write_outputs(*, check: bool) -> None:
    stale: list[str] = []
    for path, payload in outputs().items():
        if check:
            if not path.exists() or path.read_bytes() != payload:
                stale.append(str(path.relative_to(MOD_ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    if stale:
        raise SystemExit("stale generated files:\n" + "\n".join(stale))


def validate_source_data() -> None:
    if set(BEHAVIORS) != set(EXPECTED_IDS) or set(EXPECTED_IDS) != set(range(192, 229)):
        raise ValueError("semantic model bindings must cover exactly 192..228")
    if set(ASSIGNMENTS) != set(range(192, 229)):
        raise ValueError("assignments must cover exactly 192..228")
    if set(SCORES) != set(range(192, 229)):
        raise ValueError("scores must cover exactly 192..228")
    if set(DOMAIN_BY_ID) != set(range(192, 229)):
        raise ValueError("domains must cover exactly 192..228")
    for mechanism_id, dependencies in CURRENT_OBJECT_DEPENDENCIES.items():
        if mechanism_id not in EXPECTED_IDS or not dependencies:
            raise ValueError("current-object dependency map is malformed")
        if any(DOMAIN_BY_ID[source_id] != DOMAIN_BY_ID[mechanism_id] for source_id in dependencies):
            raise ValueError(f"mechanism {mechanism_id} crosses a domain object boundary")
        order = EXECUTION_ORDER[DOMAIN_BY_ID[mechanism_id].code]
        if any(order.index(source_id) >= order.index(mechanism_id) for source_id in dependencies):
            raise ValueError(f"mechanism {mechanism_id} has a non-prior semantic dependency")
    for mechanism_id, facts in ASSIGNMENTS.items():
        if not facts or any(len(values) != 3 for values in facts.values()):
            raise ValueError(f"mechanism {mechanism_id} lacks complete A/B/C facts")
        behavior = BEHAVIORS[mechanism_id]
        if not behavior.object_type or not behavior.consumer_method or not behavior.resource_books:
            raise ValueError(f"mechanism {mechanism_id} lacks an exact semantic binding")
        if not _special_consumer(mechanism_id):
            raise ValueError(f"mechanism {mechanism_id} lacks a per-ID business consumer")
    if any(not domain.ids_for_stage(stage) for domain in DOMAINS for stage in range(1, domain.transitions + 1)):
        raise ValueError("every shared stage must own at least one numbered operation")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    validate_source_data()
    write_outputs(check=args.check)


if __name__ == "__main__":
    main()
