#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the AB/AC/AD/AL workforce/endgame CK3 static runtime slice.

The generator owns only its effects, events and nine localization projections.
It composes over the public case-kernel ABI and deliberately does not wire an
on_action, decision, interaction, GUI, scoreboard, B1/B2 or shared-kernel file.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from zg361_phase3_workforce_endgame_model import (
    EXPECTED_MECHANISM_IDS,
    MECHANISM_BINDINGS,
)


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_workforce_endgame_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
PREFIX = "zg361_we"
NAMESPACE = "zg361we"
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


DOMAIN_ORDER = {
    "ab": tuple(range(242, 254)),
    "ac": tuple(range(254, 266)),
    "ad": tuple(range(266, 278)),
    "al": (355, 356, 360, 361),
}
DOMAIN_EXPECTED = {
    "ab": {242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253},
    "ac": {254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265},
    "ad": {266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277},
    "al": {355, 356, 360, 361},
}
STATE_BY_HOOK = {
    "capacity_planned": 1,
    "capacity_request_open": 2,
    "capacity_decided": 3,
    "capacity_executed": 4,
    "compensation_due": 5,
    "capacity_normalized": 6,
    "external_need_open": 1,
    "contract_type_locked": 2,
    "supplier_selected": 3,
    "contract_active": 4,
    "delivery_due": 5,
    "contract_resolved": 6,
    "requisition_open": 1,
    "interview_votes_due": 2,
    "interview_calibration_due": 3,
    "offer_due": 4,
    "offer_decided": 5,
    "probation_due": 6,
    "multi_cycle_facts_frozen": 1,
    "manager_collective_action": 4,
    "constitution_chartered": 5,
}
STAGE_LAST = {
    "ab": {243: 1, 245: 2, 247: 3, 249: 4, 251: 5, 253: 6},
    "ac": {255: 1, 257: 2, 259: 3, 261: 4, 263: 5, 265: 6},
    "ad": {267: 1, 269: 2, 271: 3, 273: 4, 275: 5, 277: 6},
    # AL 2/3 belong to mechanisms 357-359.  This slice never forges them.
    "al": {356: 1, 360: 4, 361: 5},
}
NEXT_DOMAIN = {"ab": "ac", "ac": "ad", "ad": "al", "al": None}
DEADLINE_DAYS = {"ab": 90, "ac": 180, "ad": 90, "al": 180}
DOMAIN_EVENT_BASE = {"ab": 4200, "ac": 4400, "ad": 4600, "al": 4800}
FUTURE_EVENT = {
    257: 5257,
    262: 5262,
    263: 5263,
    269: 5269,
    275: 5275,
    355: 5355,
    356: 5356,
    361: 5361,
}
FUTURE_PENDING = {
    257: "m257_conversion_pending",
    262: "m262_review_pending",
    263: "m263_extension_pending",
    269: "m269_outcome_pending",
    275: "m275_hold_pending",
    355: "m355_target_install_pending",
    356: "m356_audit_pending",
    361: "m361_future_install_pending",
}
FUTURE_CHOICES = {
    257: (1, 2),
    262: (1, 2),
    263: (2,),
    269: (1, 2),
    275: (1, 2),
    355: (1,),
    356: (2,),
    361: (1, 2),
}
MAX_COLLECTIVE_OUTCOMES = 6
NONMANAGER_NA_IDS = frozenset({360, 361})
NONMANAGER_OPERATION_COUNT = len(EXPECTED_MECHANISM_IDS - NONMANAGER_NA_IDS)


def _load_mechanisms() -> tuple[Mechanism, ...]:
    choices_path = MOD_ROOT / "tools" / "mechanism_choices" / "choices_241_361.json"
    choices = json.loads(choices_path.read_text(encoding="utf-8"))
    rows: list[Mechanism] = []
    for domain in ("ab", "ac", "ad", "al"):
        for mid in DOMAIN_ORDER[domain]:
            binding = MECHANISM_BINDINGS[mid]
            choice = choices[str(mid)]
            state = STATE_BY_HOOK[binding.trigger_hook]
            title_en = choice["title_en"]
            title_cn = binding.title_cn
            conservation = binding.conservation_rule.rstrip(".")
            desc_en = (
                f"The portfolio has reached {title_en}. Freeze one route, its "
                f"evidence and its resource direction; {conservation}."
            )
            desc_cn = (
                f"案卷来到“{title_cn}”。请选择一条制度路线；证据、资源流向与未来后果都会冻结在本案。"
            )
            rows.append(
                Mechanism(
                    mid,
                    domain,
                    state,
                    binding.behaviors[0],
                    title_en,
                    title_cn,
                    desc_en,
                    desc_cn,
                    (
                        choice["option_a_en"],
                        choice["option_b_en"],
                        "Defer this mechanism, bind one due-cycle debt, and create no business object.",
                    ),
                    (
                        choice["option_a_cn"],
                        choice["option_b_cn"],
                        "暂缓本机制，只绑定一笔到期制度债，不创建业务对象。",
                    ),
                )
            )
    return tuple(rows)


MECHANISMS = _load_mechanisms()


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.rstrip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.rstrip() + "\n").encode("utf-8")


def by_id() -> dict[int, Mechanism]:
    return {spec.mid: spec for spec in MECHANISMS}


def validate_specs() -> None:
    expected = set(EXPECTED_MECHANISM_IDS)
    specs = by_id()
    if set(specs) != expected or len(specs) != 40:
        raise ValueError("workforce/endgame runtime must map the exact 40 authoritative IDs")
    if {mid for ids in DOMAIN_EXPECTED.values() for mid in ids} != expected:
        raise ValueError("domain ID partitions are incomplete")
    if {mid for order in DOMAIN_ORDER.values() for mid in order} != expected:
        raise ValueError("portfolio order must touch every ID once")
    if len({spec.field for spec in MECHANISMS}) != len(MECHANISMS):
        raise ValueError("every numbered mechanism needs a unique semantic write")
    for domain, order in DOMAIN_ORDER.items():
        for mid in order:
            if specs[mid].domain != domain:
                raise ValueError(f"mechanism {mid} is bound to the wrong domain")
        for mid, state in STAGE_LAST[domain].items():
            if specs[mid].state != state:
                raise ValueError(f"stage barrier {mid} has the wrong state")
    if {spec.mid for spec in MECHANISMS if spec.domain == "al" and spec.state in (2, 3)}:
        raise ValueError("AL 357-359 must remain an external dependency")


def indent(text: str, tabs: int = 1) -> str:
    prefix = "\t" * tabs
    return "\n".join(prefix + line if line else line for line in text.splitlines())


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
\tRECEIPT_OWNER_VAR = {PREFIX}_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = {PREFIX}_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = {PREFIX}_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = {PREFIX}_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = {PREFIX}_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = {PREFIX}_m{mid}_receipt_choice
\tEXPECTED_OWNER = $TICKET_OWNER$
\tEXPECTED_SUBJECT = $TICKET_SUBJECT$
\tEXPECTED_CYCLE = $TICKET_CYCLE$
\tEXPECTED_CASE = $TICKET_CASE$
\tEXPECTED_STATE = {spec.state}
\tEXPECTED_CHOICE = {choice}
}}"""


def any_receipt(spec: Mechanism) -> str:
    return "OR = {\n" + "\n".join(indent(receipt_guard(spec, choice)) for choice in (1, 2, 3)) + "\n}"


def _gold_check(amount: int) -> list[str]:
    return [
        f"has_variable = {PREFIX}_gold_available",
        f"var:{PREFIX}_gold_available >= {amount}",
    ]


def _zero_or_missing(name: str) -> str:
    """CK3 trigger for a persistent single-flight flag."""
    return (
        f"trigger_if = {{ limit = {{ has_variable = {name} }} "
        f"var:{name} = 0 }} trigger_else = {{ always = yes }}"
    )


def _collective_external_checks(choice: int) -> list[str]:
    """Fixed three-cohort projection of the model's #360 mapping ABI."""
    checks = [
        f"has_variable = {PREFIX}_al_external_collective_case",
        f"has_variable = {PREFIX}_al_external_collective_submitted_cycle",
        f"has_variable = {PREFIX}_al_external_collective_cohort_count",
        f"has_variable = {PREFIX}_al_external_collective_total_members",
        f"has_variable = {PREFIX}_al_external_collective_total_quota",
        f"has_variable = {PREFIX}_al_external_collective_settlement_id",
        f"has_variable = {PREFIX}_al_external_collective_settled",
        f"has_variable = {PREFIX}_al_external_collective_forced_count",
        f"has_variable = {PREFIX}_al_external_collective_exception_count",
        f"has_variable = {PREFIX}_al_external_collective_manager_cost_total",
        f"var:{PREFIX}_al_external_collective_submitted_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_collective_cohort_count = 3",
        f"var:{PREFIX}_al_external_collective_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_collective_settled = 0",
        f"var:{PREFIX}_al_external_receipt_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_al_external_receipt_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_al_external_receipt_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_receipt_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_receipt_state = 4",
    ]
    for slot in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{slot}"
        for name in (
            "cohort_id", "manager", "member_count", "member_hash",
            "agenda_count", "agenda_hash", "quota", "all_meet_evidence_id",
            "forced_count", "exception_count", "approver",
            "manager_cost", "partition_verified",
            "approval_verified",
        ):
            checks.append(f"has_variable = {base}_{name}")
        checks += [
            f"var:{base}_member_count = var:{base}_agenda_count",
            f"var:{base}_member_hash = var:{base}_agenda_hash",
            f"var:{base}_member_count >= 1",
            f"var:{base}_quota >= 0",
            f"var:{base}_quota <= var:{base}_member_count",
            f"var:{base}_forced_count >= 0",
            f"var:{base}_exception_count >= 0",
            f"var:{base}_manager_cost >= 0",
            f"var:{base}_quota = {{ value = var:{base}_forced_count add = var:{base}_exception_count }}",
            f"var:{base}_manager_cost = var:{base}_exception_count",
            f"var:{base}_partition_verified = 1",
            f"var:{base}_manager = {{ zg361_is_celestial_liege_trigger = yes has_variable = {PREFIX}_manager_score var:{PREFIX}_manager_score >= scope:{PREFIX}_al_subject.var:{base}_manager_cost }}",
            (
                f"trigger_if = {{ limit = {{ var:{base}_exception_count > 0 }} "
                f"NOT = {{ var:{base}_approver = var:{base}_manager }} "
                f"var:{base}_approver = {{ zg361_is_celestial_liege_trigger = yes }} "
                f"var:{base}_manager = {{ liege = scope:{PREFIX}_al_subject.var:{base}_approver }} "
                f"var:{base}_approval_verified = 1 }} "
                f"trigger_else = {{ var:{base}_approver = 0 var:{base}_approval_verified = 0 }}"
            ),
        ]
        if choice == 2:
            checks += [
                f"var:{base}_exception_count = 0",
                f"var:{base}_forced_count = var:{base}_quota",
            ]
    checks += [
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_cohort_id = var:{PREFIX}_al_external_collective_2_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_cohort_id = var:{PREFIX}_al_external_collective_3_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_2_cohort_id = var:{PREFIX}_al_external_collective_3_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_manager = var:{PREFIX}_al_external_collective_2_manager }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_manager = var:{PREFIX}_al_external_collective_3_manager }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_2_manager = var:{PREFIX}_al_external_collective_3_manager }}",
        f"var:{PREFIX}_al_external_collective_total_members = {{ value = var:{PREFIX}_al_external_collective_1_member_count add = var:{PREFIX}_al_external_collective_2_member_count add = var:{PREFIX}_al_external_collective_3_member_count }}",
        f"var:{PREFIX}_al_external_collective_total_quota = {{ value = var:{PREFIX}_al_external_collective_1_quota add = var:{PREFIX}_al_external_collective_2_quota add = var:{PREFIX}_al_external_collective_3_quota }}",
        f"var:{PREFIX}_al_external_collective_forced_count = {{ value = var:{PREFIX}_al_external_collective_1_forced_count add = var:{PREFIX}_al_external_collective_2_forced_count add = var:{PREFIX}_al_external_collective_3_forced_count }}",
        f"var:{PREFIX}_al_external_collective_exception_count = {{ value = var:{PREFIX}_al_external_collective_1_exception_count add = var:{PREFIX}_al_external_collective_2_exception_count add = var:{PREFIX}_al_external_collective_3_exception_count }}",
        f"var:{PREFIX}_al_external_collective_manager_cost_total = {{ value = var:{PREFIX}_al_external_collective_1_manager_cost add = var:{PREFIX}_al_external_collective_2_manager_cost add = var:{PREFIX}_al_external_collective_3_manager_cost }}",
        f"var:{PREFIX}_al_external_collective_total_members >= 3",
        f"var:{PREFIX}_al_external_collective_total_quota >= 0",
        f"var:{PREFIX}_al_external_collective_total_quota <= {MAX_COLLECTIVE_OUTCOMES}",
        f"var:zg361_case_al_owner = {{ var:{PREFIX}_realm_trust >= scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_collective_manager_cost_total }}",
    ]
    if choice == 2:
        checks.append(f"var:{PREFIX}_al_external_collective_exception_count = 0")
    else:
        checks.append(
            f"trigger_if = {{ limit = {{ var:{PREFIX}_al_external_collective_exception_count = 0 }} "
            f"has_variable = {PREFIX}_al_external_collective_reform_proposal_id "
            f"has_variable = {PREFIX}_al_external_collective_reform_effective_cycle "
            f"var:{PREFIX}_al_external_collective_reform_effective_cycle = {{ value = $TICKET_CYCLE$ add = 1 }} }} "
            f"trigger_else = {{ always = yes }}"
        )
    # Outcome identities are partitioned by cohort rather than accepted from a
    # global bag.  Each active local slot is tied to its cohort id, therefore
    # the declared per-cohort forced/exception count is the exact number of
    # identities that can be consumed for that cohort.
    identity_slots: dict[str, list[tuple[int, int, str, str]]] = {
        "forced": [],
        "exception": [],
    }
    for cohort in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{cohort}"
        for kind in ("forced", "exception"):
            count = f"{base}_{kind}_count"
            for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
                identity = f"{base}_{kind}_{slot}"
                identity_slots[kind].append((cohort, slot, count, identity))
                checks.append(
                    f"trigger_if = {{ limit = {{ var:{count} >= {slot} }} "
                    f"has_variable = {identity}_character "
                    f"has_variable = {identity}_cohort_id "
                    f"has_variable = {identity}_member_evidence_receipt "
                    f"var:{identity}_cohort_id = var:{base}_cohort_id "
                    f"var:{identity}_member_evidence_receipt = 1 }} "
                    f"trigger_else = {{ always = yes }}"
                )
    # One character can occupy at most one active outcome slot globally.
    for kind, slots in identity_slots.items():
        for left_index, (_, left_slot, left_count, left) in enumerate(slots):
            for _, right_slot, right_count, right in slots[left_index + 1:]:
                checks.append(
                    f"trigger_if = {{ limit = {{ var:{left_count} >= {left_slot} var:{right_count} >= {right_slot} }} "
                    f"NOT = {{ var:{left}_character = var:{right}_character }} }} "
                    f"trigger_else = {{ always = yes }}"
                )
    for _, forced_slot, forced_count, forced in identity_slots["forced"]:
        for _, exception_slot, exception_count, exception in identity_slots["exception"]:
            checks.append(
                f"trigger_if = {{ limit = {{ var:{forced_count} >= {forced_slot} var:{exception_count} >= {exception_slot} }} "
                f"NOT = {{ var:{forced}_character = var:{exception}_character }} }} "
                f"trigger_else = {{ always = yes }}"
            )
    return checks


def _collective_business_writes(choice: int) -> list[str]:
    lines = [
        _set("m360_collective_case", f"var:{PREFIX}_al_external_collective_case"),
        _set("m360_submitted_cycle", f"var:{PREFIX}_al_external_collective_submitted_cycle"),
        _set("m360_settlement_id", f"var:{PREFIX}_al_external_collective_settlement_id"),
        _set("m360_cohort_count", 3),
        _set("m360_cohort_size", f"var:{PREFIX}_al_external_collective_total_members"),
        _set("m360_agenda_size", f"var:{PREFIX}_al_external_collective_total_members"),
        _set("m360_quota", f"var:{PREFIX}_al_external_collective_total_quota"),
        _set("m360_participating_manager_count", 3),
        _set("m360_approved_exception_count", f"var:{PREFIX}_al_external_collective_exception_count"),
        _set("m360_forced_c_count", f"var:{PREFIX}_al_external_collective_forced_count"),
        _set("m360_manager_cost_total", f"var:{PREFIX}_al_external_collective_manager_cost_total"),
        _set("m360_member_snapshot_frozen", 1),
        _set("m360_agenda_equals_authoritative_cohort", 1),
        _set("m360_all_meet_evidence", 1),
        _set("m360_quota_partition", f"var:{PREFIX}_al_external_collective_total_quota"),
    ]
    for slot in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{slot}"
        for name in (
            "cohort_id", "manager", "member_count", "member_hash",
            "agenda_count", "agenda_hash", "quota", "all_meet_evidence_id",
            "forced_count", "exception_count", "approver",
            "manager_cost", "partition_verified",
            "approval_verified",
        ):
            lines.append(_set(f"m360_cohort_{slot}_{name}", f"var:{base}_{name}"))
        lines.append(_set(f"m360_cohort_{slot}_response", choice))
        lines.append(
            f"var:{base}_manager = {{ change_variable = {{ name = {PREFIX}_manager_score add = {{ value = 0 subtract = scope:{PREFIX}_al_subject.var:{base}_manager_cost }} }} }}"
        )
    for cohort in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{cohort}"
        for kind in ("forced", "exception"):
            for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
                source = f"{base}_{kind}_{slot}"
                lines.append(
                    f"if = {{ limit = {{ var:{base}_{kind}_count >= {slot} }} "
                    f"set_variable = {{ name = {PREFIX}_m360_cohort_{cohort}_{kind}_{slot}_character value = var:{source}_character }} "
                    f"set_variable = {{ name = {PREFIX}_m360_cohort_{cohort}_{kind}_{slot}_cohort_id value = var:{source}_cohort_id }} "
                    f"set_variable = {{ name = {PREFIX}_m360_cohort_{cohort}_{kind}_{slot}_member_evidence_receipt value = var:{source}_member_evidence_receipt }} }}"
                )
    lines += [
        f"var:zg361_case_al_owner = {{ change_variable = {{ name = {PREFIX}_realm_trust add = {{ value = 0 subtract = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_collective_manager_cost_total }} }} }}",
        _set("m360_realm_trust_delta", f"{{ value = 0 subtract = var:{PREFIX}_al_external_collective_manager_cost_total }}"),
        _set("m360_manager_cost_direction", f"{{ value = 0 subtract = var:{PREFIX}_al_external_collective_manager_cost_total }}"),
        _set("m360_settled", 1),
    ]
    if choice == 1:
        lines.append(
            f"if = {{ limit = {{ has_variable = {PREFIX}_al_external_collective_reform_proposal_id has_variable = {PREFIX}_al_external_collective_reform_effective_cycle }} "
            f"set_variable = {{ name = {PREFIX}_m360_reform_proposal_id value = var:{PREFIX}_al_external_collective_reform_proposal_id }} "
            f"set_variable = {{ name = {PREFIX}_m360_reform_effective_cycle value = var:{PREFIX}_al_external_collective_reform_effective_cycle }} }}"
        )
    else:
        lines += [_set("m360_reform_proposal_id", 0), _set("m360_reform_effective_cycle", 0)]
    return lines


def _charter_external_checks() -> list[str]:
    checks = [
        f"has_variable = {PREFIX}_al_external_charter_id",
        f"has_variable = {PREFIX}_al_external_charter_previous_id",
        f"has_variable = {PREFIX}_al_external_charter_adopted_day",
        f"has_variable = {PREFIX}_al_external_completed_cycles_hash",
        f"has_variable = {PREFIX}_al_external_report_completed_cycles_hash",
        f"has_variable = {PREFIX}_al_external_charter_previous_history_hash",
        f"has_variable = {PREFIX}_al_external_charter_new_history_hash",
        f"var:{PREFIX}_al_external_report_completed_cycles_hash = var:{PREFIX}_al_external_completed_cycles_hash",
        f"NOT = {{ var:{PREFIX}_al_external_charter_new_history_hash = var:{PREFIX}_al_external_charter_previous_history_hash }}",
    ]
    for slot in (1, 2, 3):
        for name in ("cycle", "receipt_id", "receipt_hash"):
            checks.append(f"has_variable = {PREFIX}_al_external_completed_{name}_{slot}")
        checks += [
            f"var:{PREFIX}_al_external_completed_cycle_{slot} >= 1",
            f"var:{PREFIX}_al_external_completed_cycle_{slot} <= $TICKET_CYCLE$",
            f"var:{PREFIX}_al_external_completed_receipt_id_{slot} > 0",
            f"var:{PREFIX}_al_external_completed_receipt_hash_{slot} > 0",
        ]
    checks += [
        f"var:{PREFIX}_al_external_completed_cycle_1 < var:{PREFIX}_al_external_completed_cycle_2",
        f"var:{PREFIX}_al_external_completed_cycle_2 < var:{PREFIX}_al_external_completed_cycle_3",
        f"var:{PREFIX}_al_external_completed_cycle_max = var:{PREFIX}_al_external_completed_cycle_3",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_id_1 = var:{PREFIX}_al_external_completed_receipt_id_2 }}",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_id_1 = var:{PREFIX}_al_external_completed_receipt_id_3 }}",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_id_2 = var:{PREFIX}_al_external_completed_receipt_id_3 }}",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_hash_1 = var:{PREFIX}_al_external_completed_receipt_hash_2 }}",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_hash_1 = var:{PREFIX}_al_external_completed_receipt_hash_3 }}",
        f"NOT = {{ var:{PREFIX}_al_external_completed_receipt_hash_2 = var:{PREFIX}_al_external_completed_receipt_hash_3 }}",
        f"var:zg361_case_al_owner = {{",
        f"\thas_variable = {PREFIX}_realm_charter_current_id",
        f"\thas_variable = {PREFIX}_realm_charter_current_cycle_hash",
        f"\thas_variable = {PREFIX}_realm_charter_current_report_id",
        f"\thas_variable = {PREFIX}_realm_charter_current_adopted_day",
        f"\thas_variable = {PREFIX}_realm_charter_current_effective_cycle",
        f"\thas_variable = {PREFIX}_realm_charter_history_tail_hash",
        f"\thas_variable = {PREFIX}_realm_charter_history_count",
        f"\tvar:{PREFIX}_realm_charter_history_count = var:{PREFIX}_realm_charter_current_version",
        "}",
        f"trigger_if = {{ limit = {{ var:zg361_case_al_owner = {{ var:{PREFIX}_realm_charter_current_version = 0 }} }}",
        f"\tvar:zg361_case_al_owner = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_cycle_1 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_cycle_2 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_cycle_3 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_id_1 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_id_2 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_id_3 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_1 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_2 }} NOT = {{ has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_3 }} NOT = {{ has_variable = {PREFIX}_realm_charter_long_report_anchor }} }}",
        f"}} trigger_else = {{",
        f"\tvar:zg361_case_al_owner = {{ has_variable = {PREFIX}_realm_charter_anchor_cycle_1 has_variable = {PREFIX}_realm_charter_anchor_cycle_2 has_variable = {PREFIX}_realm_charter_anchor_cycle_3 has_variable = {PREFIX}_realm_charter_anchor_receipt_id_1 has_variable = {PREFIX}_realm_charter_anchor_receipt_id_2 has_variable = {PREFIX}_realm_charter_anchor_receipt_id_3 has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_1 has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_2 has_variable = {PREFIX}_realm_charter_anchor_receipt_hash_3 has_variable = {PREFIX}_realm_charter_long_report_anchor }}",
        f"\tvar:{PREFIX}_al_external_completed_cycle_1 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_cycle_1",
        f"\tvar:{PREFIX}_al_external_completed_cycle_2 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_cycle_2",
        f"\tvar:{PREFIX}_al_external_completed_cycle_3 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_cycle_3",
        f"\tvar:{PREFIX}_al_external_completed_receipt_id_1 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_id_1",
        f"\tvar:{PREFIX}_al_external_completed_receipt_id_2 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_id_2",
        f"\tvar:{PREFIX}_al_external_completed_receipt_id_3 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_id_3",
        f"\tvar:{PREFIX}_al_external_completed_receipt_hash_1 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_hash_1",
        f"\tvar:{PREFIX}_al_external_completed_receipt_hash_2 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_hash_2",
        f"\tvar:{PREFIX}_al_external_completed_receipt_hash_3 = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_anchor_receipt_hash_3",
        f"\tvar:{PREFIX}_al_external_long_report_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_long_report_anchor",
        f"}}",
        f"trigger_if = {{ limit = {{ var:zg361_case_al_owner = {{ var:{PREFIX}_realm_charter_current_version > 0 }} }}",
        f"\tvar:{PREFIX}_al_external_charter_previous_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_id",
        f"\tvar:{PREFIX}_al_external_completed_cycles_hash = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_cycle_hash",
        f"\tvar:{PREFIX}_al_external_long_report_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_report_id",
        f"\tvar:{PREFIX}_al_external_charter_previous_history_hash = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_history_tail_hash",
        f"\tvar:{PREFIX}_al_external_charter_adopted_day > var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_adopted_day",
        f"\tvar:zg361_case_al_owner = {{ var:{PREFIX}_realm_charter_current_effective_cycle < {{ value = $TICKET_CYCLE$ add = 1 }} }}",
        f"}} trigger_else = {{ var:{PREFIX}_al_external_charter_previous_id = 0 var:{PREFIX}_al_external_charter_previous_history_hash = 0 }}",
        f"NOT = {{ var:{PREFIX}_al_external_charter_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_id }}",
    ]
    return checks


def _charter_business_writes(choice: int) -> list[str]:
    cost = 5 if choice == 1 else 10
    lines = [
        _change("hours_available", -10),
        _change("hours_governance", 10),
        _change("gold_available", -cost),
        _change("gold_paid", cost),
        _set("m361_previous_version", f"var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_version"),
        _set("m361_previous_charter_id", f"var:{PREFIX}_al_external_charter_previous_id"),
        _set("m361_charter_id", f"var:{PREFIX}_al_external_charter_id"),
        _set("m361_adopted_day", f"var:{PREFIX}_al_external_charter_adopted_day"),
        _set("m361_effective_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"),
        _set("m361_amendment_due_cycle", "{ value = $TICKET_CYCLE$ add = 3 }"),
        _set("m361_completed_evidence_count", 3),
        _set("m361_completed_cycles_hash", f"var:{PREFIX}_al_external_completed_cycles_hash"),
        _set("m361_long_report_id", f"var:{PREFIX}_al_external_long_report_id"),
        _set("m361_report_completed_cycles_hash", f"var:{PREFIX}_al_external_report_completed_cycles_hash"),
        _set("m361_previous_history_hash", f"var:{PREFIX}_al_external_charter_previous_history_hash"),
        _set("m361_new_history_hash", f"var:{PREFIX}_al_external_charter_new_history_hash"),
        _set("m361_long_report_frozen", 1),
        _set("m361_visible_cost_gold", cost),
        _set("m361_history_reset", 0),
        _set("m361_future_install_pending", 1),
    ]
    for slot in (1, 2, 3):
        for name in ("cycle", "receipt_id", "receipt_hash"):
            lines.append(_set(f"m361_completed_{name}_{slot}", f"var:{PREFIX}_al_external_completed_{name}_{slot}"))
    lines += [
        f"var:zg361_case_al_owner = {{ if = {{ limit = {{ var:{PREFIX}_realm_charter_current_version = 0 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_1 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_cycle_1 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_2 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_cycle_2 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_3 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_cycle_3 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_id_1 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_id_1 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_id_2 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_id_2 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_id_3 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_id_3 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_hash_1 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_hash_1 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_hash_2 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_hash_2 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_receipt_hash_3 value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_receipt_hash_3 }} set_variable = {{ name = {PREFIX}_realm_charter_long_report_anchor value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_long_report_id }} }} }}",
        f"var:zg361_case_al_owner = {{ set_variable = {{ name = {PREFIX}_realm_charter_previous_version value = var:{PREFIX}_realm_charter_current_version }} set_variable = {{ name = {PREFIX}_realm_charter_previous_id value = var:{PREFIX}_realm_charter_current_id }} set_variable = {{ name = {PREFIX}_realm_charter_previous_cycle_hash value = var:{PREFIX}_realm_charter_current_cycle_hash }} set_variable = {{ name = {PREFIX}_realm_charter_previous_report_id value = var:{PREFIX}_realm_charter_current_report_id }} change_variable = {{ name = {PREFIX}_realm_charter_current_version add = 1 }} change_variable = {{ name = {PREFIX}_realm_charter_history_count add = 1 }} set_variable = {{ name = {PREFIX}_realm_charter_current_id value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_charter_id }} set_variable = {{ name = {PREFIX}_realm_charter_current_cycle_hash value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_completed_cycles_hash }} set_variable = {{ name = {PREFIX}_realm_charter_current_report_id value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_long_report_id }} set_variable = {{ name = {PREFIX}_realm_charter_current_adopted_day value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_charter_adopted_day }} set_variable = {{ name = {PREFIX}_realm_charter_current_effective_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }} set_variable = {{ name = {PREFIX}_realm_charter_history_tail_hash value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_charter_new_history_hash }} set_variable = {{ name = {PREFIX}_realm_charter_last_case value = $TICKET_CASE$ }} set_variable = {{ name = {PREFIX}_realm_charter_last_report value = scope:{PREFIX}_al_subject.var:{PREFIX}_al_external_long_report_id }} }}",
        _set("m361_adopted_version", f"var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_version"),
        _set("m361_previous_charter_version", f"var:zg361_case_al_owner.var:{PREFIX}_realm_charter_previous_version"),
        f"var:zg361_case_al_owner = {{ remove_gold = {cost} }}",
        f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[361]} days = 365 }}",
    ]
    return lines


def resource_checks(spec: Mechanism, choice: int) -> list[str]:
    """Every read is paired with an existence gate before record_operation."""
    d, mid = spec.domain, spec.mid
    checks = [
        f"has_variable = {PREFIX}_operation_total",
        f"has_variable = {PREFIX}_operation_used",
        f"var:{PREFIX}_operation_used < var:{PREFIX}_operation_total",
    ]
    # Delayed events do not carry arbitrary values in CK3.  Keep each
    # mechanism single-flight so its frozen receipt/write tuple cannot be
    # overwritten by a later cycle before the queued consumer settles.
    if mid in FUTURE_PENDING:
        checks.append(_zero_or_missing(f"{PREFIX}_{FUTURE_PENDING[mid]}"))
    if mid == 263:
        checks += [
            f"trigger_if = {{ limit = {{ has_variable = {PREFIX}_m262_business_object_created var:{PREFIX}_m262_business_object_created = 1 }} has_variable = {PREFIX}_m262_due_cycle var:zg361_case_{d}_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= scope:{PREFIX}_{d}_subject.var:{PREFIX}_m262_due_cycle }} }} trigger_else = {{ always = yes }}",
        ]
    if choice == 3:
        return checks
    if mid == 263:
        checks += [
            f"has_variable = {PREFIX}_m262_business_object_created",
            f"var:{PREFIX}_m262_business_object_created = 1",
        ]
    hour_cost = {
        242: 20,
        243: 2 if choice == 1 else 4,
        244: 5,
        249: 6 if choice == 1 else 12,
        252: 8,
        361: 10,
    }.get(mid)
    if hour_cost:
        checks += [
            f"has_variable = {PREFIX}_hours_available",
            f"var:{PREFIX}_hours_available >= {hour_cost}",
        ]
    if mid in (244,):
        checks += _gold_check(10) + [f"var:zg361_case_{d}_owner = {{ gold >= 10 }}"]
    if mid == 246 and choice == 1:
        checks += _gold_check(15) + [
            f"has_variable = {PREFIX}_overtime_pending",
            f"var:{PREFIX}_overtime_pending >= 5",
            f"var:zg361_case_{d}_owner = {{ gold >= 15 }}",
        ]
    if mid == 246 and choice == 2:
        checks += [
            f"has_variable = {PREFIX}_overtime_pending",
            f"var:{PREFIX}_overtime_pending >= 5",
        ]
    if mid == 254:
        checks += [
            f"has_variable = {PREFIX}_shadow_hc_available",
            f"var:{PREFIX}_shadow_hc_available >= 1",
            *_gold_check(20),
            f"var:zg361_case_{d}_owner = {{ gold >= 20 }}",
        ]
    if mid == 257:
        checks += [
            "has_variable = zg361_ch_hc_available",
            "var:zg361_ch_hc_available >= 1",
            f"has_variable = {PREFIX}_shadow_hc_active",
            f"var:{PREFIX}_shadow_hc_active >= 1",
            _zero_or_missing(f"{PREFIX}_candidate_active"),
            _zero_or_missing(f"{PREFIX}_formal_hc_pending"),
            _zero_or_missing(f"{PREFIX}_formal_hc_active"),
        ]
    if mid == 251:
        checks += [
            f"has_variable = {PREFIX}_m250_attendee_count",
            f"var:{PREFIX}_m250_attendee_count >= 1",
            f"has_variable = {PREFIX}_m249_agenda_frozen",
            f"var:{PREFIX}_m249_agenda_frozen = 1",
        ]
    if mid in (262, 263):
        checks += [f"var:zg361_case_{d}_subject = {{ zg361_is_celestial_liege_trigger = yes }}"]
    if mid == 264:
        checks += [
            f"has_variable = {PREFIX}_contract_gold_reserved",
            f"var:{PREFIX}_contract_gold_reserved >= 20",
            _zero_or_missing(f"{PREFIX}_m257_conversion_pending"),
            (
                f"trigger_if = {{ limit = {{ has_variable = {PREFIX}_m257_conversion_settled "
                f"var:{PREFIX}_m257_conversion_settled = 1 }} always = yes }} "
                f"trigger_else = {{ has_variable = {PREFIX}_shadow_hc_active "
                f"var:{PREFIX}_shadow_hc_active >= 1 }}"
            ),
        ]
        if choice == 1:
            checks.append(f"var:zg361_case_{d}_owner = {{ gold >= 20 }}")
    if mid == 265 and choice == 1:
        checks += [
            f"has_variable = {PREFIX}_contract_gold_paid",
            f"var:{PREFIX}_contract_gold_paid >= 5",
            "gold >= 5",
            f"has_variable = {PREFIX}_m259_responsibility_total_bps",
            f"var:{PREFIX}_m259_responsibility_total_bps = 10000",
            f"has_variable = {PREFIX}_m261_actual_executor_frozen",
            f"var:{PREFIX}_m261_actual_executor_frozen = 1",
            f"has_variable = {PREFIX}_m264_payment_settled",
            f"var:{PREFIX}_m264_payment_settled = 1",
            f"has_variable = {PREFIX}_m264_payee",
            f"var:{PREFIX}_m264_payee = $TICKET_SUBJECT$",
            f"has_variable = {PREFIX}_m264_accepted_by",
            f"var:{PREFIX}_m264_accepted_by = $TICKET_OWNER$",
        ]
    if mid == 266:
        checks += [
            "has_variable = zg361_ch_hc_available",
            "var:zg361_ch_hc_available >= 1",
            _zero_or_missing(f"{PREFIX}_m266_hc_reservation_active"),
            _zero_or_missing(f"{PREFIX}_m269_outcome_pending"),
            _zero_or_missing(f"{PREFIX}_m275_hold_pending"),
            _zero_or_missing(f"{PREFIX}_m275_runner_reopen_pending"),
            f"var:zg361_case_{d}_owner = {{ {_zero_or_missing(f'{PREFIX}_ad_hc_flight_pending')} }}",
        ]
    if mid == 267:
        checks += [
            f"has_variable = {PREFIX}_ad_external_candidate",
            f"has_variable = {PREFIX}_ad_external_referral_present",
            f"has_variable = {PREFIX}_ad_external_referrer_voted",
            f"var:{PREFIX}_ad_external_candidate = $TICKET_SUBJECT$",
            f"var:{PREFIX}_ad_external_referral_present >= 0",
            f"var:{PREFIX}_ad_external_referral_present <= 1",
            f"var:{PREFIX}_ad_external_referrer_voted >= 0",
            f"var:{PREFIX}_ad_external_referrer_voted <= 1",
            f"trigger_if = {{ limit = {{ var:{PREFIX}_ad_external_referral_present = 1 }} has_variable = {PREFIX}_ad_external_referral_id has_variable = {PREFIX}_ad_external_referrer has_variable = {PREFIX}_ad_external_referral_relationship has_variable = {PREFIX}_ad_external_referral_evidence_receipt has_variable = {PREFIX}_ad_external_referral_reward var:{PREFIX}_ad_external_referral_reward = 5 NOT = {{ var:{PREFIX}_ad_external_referrer = var:{PREFIX}_ad_external_candidate }} }} trigger_else = {{ always = yes }}",
        ]
        for slot in (1, 2, 3):
            checks += [
                f"has_variable = {PREFIX}_ad_external_interviewer_{slot}",
                f"has_variable = {PREFIX}_ad_external_vote_{slot}",
                f"has_variable = {PREFIX}_ad_external_vote_evidence_{slot}",
                f"var:{PREFIX}_ad_external_vote_{slot} >= 1",
                f"var:{PREFIX}_ad_external_vote_{slot} <= 3",
                f"var:{PREFIX}_ad_external_interviewer_{slot} = {{ zg361_is_celestial_liege_trigger = yes }}",
            ]
        checks += [
            f"NOT = {{ var:{PREFIX}_ad_external_interviewer_1 = var:{PREFIX}_ad_external_interviewer_2 }}",
            f"NOT = {{ var:{PREFIX}_ad_external_interviewer_1 = var:{PREFIX}_ad_external_interviewer_3 }}",
            f"NOT = {{ var:{PREFIX}_ad_external_interviewer_2 = var:{PREFIX}_ad_external_interviewer_3 }}",
            (
                f"trigger_if = {{ limit = {{ var:{PREFIX}_ad_external_referral_present = 1 }} "
                + (
                    f"var:{PREFIX}_ad_external_referrer_voted = 0 NOT = {{ OR = {{ var:{PREFIX}_ad_external_interviewer_1 = var:{PREFIX}_ad_external_referrer var:{PREFIX}_ad_external_interviewer_2 = var:{PREFIX}_ad_external_referrer var:{PREFIX}_ad_external_interviewer_3 = var:{PREFIX}_ad_external_referrer }} }}"
                    if choice == 1 else
                    f"var:{PREFIX}_ad_external_referrer_voted = 1 OR = {{ var:{PREFIX}_ad_external_interviewer_1 = var:{PREFIX}_ad_external_referrer var:{PREFIX}_ad_external_interviewer_2 = var:{PREFIX}_ad_external_referrer var:{PREFIX}_ad_external_interviewer_3 = var:{PREFIX}_ad_external_referrer }}"
                )
                + f" }} trigger_else = {{ var:{PREFIX}_ad_external_referrer_voted = 0 }}"
            ),
        ]
    if mid == 271:
        checks += _gold_check(5) + [
            f"var:zg361_case_{d}_owner = {{ gold >= 5 }}",
            f"has_variable = {PREFIX}_m267_candidate_frozen",
            f"has_variable = {PREFIX}_m267_referral_present",
            f"has_variable = {PREFIX}_m267_referrer_frozen",
            f"has_variable = {PREFIX}_m267_referral_id",
            f"has_variable = {PREFIX}_m267_referral_relationship",
            f"has_variable = {PREFIX}_m267_referral_evidence_receipt",
            f"has_variable = {PREFIX}_m267_referral_reward",
            f"var:{PREFIX}_m267_candidate_frozen = $TICKET_SUBJECT$",
            f"var:{PREFIX}_m267_referral_present = 1",
            f"var:{PREFIX}_m267_write_case = $TICKET_CASE$",
            f"var:{PREFIX}_m267_business_object_created = 1",
            f"var:{PREFIX}_m267_referrer_voted = {0 if choice == 1 else 1}",
        ]
    if mid == 272:
        checks += _gold_check(10) + [f"var:zg361_case_{d}_owner = {{ gold >= 10 }}"]
    if mid == 274:
        checks += _gold_check(5) + [
            f"has_variable = {PREFIX}_offer_gold_reserved",
            f"var:{PREFIX}_offer_gold_reserved >= 10",
            f"has_variable = {PREFIX}_gold_reserved",
            f"var:{PREFIX}_gold_reserved >= 10",
            f"has_variable = {PREFIX}_m266_hc_reservation_active",
            f"var:{PREFIX}_m266_hc_reservation_active = 1",
            f"has_variable = {PREFIX}_m266_hc_receipt",
            f"var:{PREFIX}_m266_hc_receipt = $TICKET_CASE$",
            f"has_variable = {PREFIX}_candidate_active",
            f"var:{PREFIX}_candidate_active = 1",
            f"var:{PREFIX}_candidate_active_owner = $TICKET_OWNER$",
            f"var:{PREFIX}_candidate_active_case = $TICKET_CASE$",
            _zero_or_missing(f"{PREFIX}_formal_hc_active"),
            f"var:zg361_case_{d}_owner = {{ gold >= 15 }}",
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_ad_hc_flight_pending var:{PREFIX}_ad_hc_flight_pending = 1 var:{PREFIX}_ad_hc_flight_subject = $TICKET_SUBJECT$ var:{PREFIX}_ad_hc_flight_cycle = $TICKET_CYCLE$ var:{PREFIX}_ad_hc_flight_case = $TICKET_CASE$ }}",
        ]
    if mid == 273:
        checks += [
            _zero_or_missing(f"{PREFIX}_candidate_active"),
            _zero_or_missing(f"{PREFIX}_formal_hc_pending"),
            _zero_or_missing(f"{PREFIX}_formal_hc_active"),
        ]
    if mid == 275:
        checks += [
            "has_variable = zg361_ch_hc_reserved",
            "var:zg361_ch_hc_reserved >= 1",
            f"has_variable = {PREFIX}_m266_hc_reservation_active",
            f"var:{PREFIX}_m266_hc_reservation_active = 1",
            f"has_variable = {PREFIX}_m266_hc_receipt",
            f"var:{PREFIX}_m266_hc_receipt = $TICKET_CASE$",
            f"has_variable = {PREFIX}_offer_gold_reserved",
            f"var:{PREFIX}_offer_gold_reserved >= 15",
            f"has_variable = {PREFIX}_gold_reserved",
            f"var:{PREFIX}_gold_reserved >= 15",
            _zero_or_missing(f"{PREFIX}_m274_hired"),
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_ad_hc_flight_pending var:{PREFIX}_ad_hc_flight_pending = 1 var:{PREFIX}_ad_hc_flight_subject = $TICKET_SUBJECT$ var:{PREFIX}_ad_hc_flight_cycle = $TICKET_CYCLE$ var:{PREFIX}_ad_hc_flight_case = $TICKET_CASE$ }}",
            f"has_variable = {PREFIX}_ad_external_refusal_reason_id",
        ]
        if choice == 1:
            checks += [
                f"has_variable = {PREFIX}_ad_external_runner_up",
                f"has_variable = {PREFIX}_ad_external_runner_up_evidence",
                f"NOT = {{ var:{PREFIX}_ad_external_runner_up = $TICKET_SUBJECT$ }}",
            ]
    if mid == 277:
        checks += [
            f"has_variable = {PREFIX}_formal_hc_active",
            f"var:{PREFIX}_formal_hc_active = 1",
            "has_variable = zg361_ch_hc_occupied",
            "var:zg361_ch_hc_occupied >= 1",
        ]
    if mid == 355 and choice == 1:
        checks += _gold_check(10) + [f"var:zg361_case_{d}_owner = {{ gold >= 10 }}"]
    if mid == 360:
        checks += [
            f"has_variable = {PREFIX}_manager_score",
            f"has_variable = {PREFIX}_al_external_stage_receipts_verified",
            f"var:{PREFIX}_al_external_stage_receipts_verified = 1",
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_realm_trust }}",
            *_collective_external_checks(choice),
        ]
    if mid == 361:
        checks += _gold_check(5 if choice == 1 else 10) + [
            f"has_variable = {PREFIX}_al_external_stage_receipts_verified",
            f"var:{PREFIX}_al_external_stage_receipts_verified = 1",
            f"has_variable = {PREFIX}_al_external_completed_cycle_receipt_count",
            f"var:{PREFIX}_al_external_completed_cycle_receipt_count = 3",
            f"has_variable = {PREFIX}_al_external_completed_cycle_max",
            f"var:{PREFIX}_al_external_completed_cycle_max <= $TICKET_CYCLE$",
            f"has_variable = {PREFIX}_al_external_long_report_id",
            f"var:zg361_case_{d}_owner = {{ zg361_is_celestial_liege_trigger = yes }}",
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_realm_charter_current_version has_variable = zg361_review_serial var:zg361_review_serial >= 3 }}",
            f"var:zg361_case_{d}_owner = {{ trigger_if = {{ limit = {{ exists = liege }} NOT = {{ liege = {{ zg361_is_celestial_liege_trigger = yes }} }} }} trigger_else = {{ always = yes }} }}",
            *_charter_external_checks(),
        ]
    return checks


def atomic_precheck(spec: Mechanism, choice: int) -> str:
    checks = resource_checks(spec, choice)
    existence = [line for line in checks if line.startswith("has_variable = ")]
    reads = [line for line in checks if not line.startswith("has_variable = ")]
    return (
        "trigger_if = {\n\tlimit = {\n"
        + indent("\n".join(existence), 2)
        + "\n\t}\n"
        + indent("\n".join(reads))
        + "\n}\ntrigger_else = { always = no }"
    )


def stage_barrier(spec: Mechanism) -> str:
    same_stage = [
        item for item in MECHANISMS
        if item.domain == spec.domain and item.state == spec.state
    ]
    return "\n".join(any_receipt(item) for item in same_stage)


def _set(name: str, value: str | int) -> str:
    return f"set_variable = {{ name = {PREFIX}_{name} value = {value} }}"


def _change(name: str, amount: str | int) -> str:
    return f"change_variable = {{ name = {PREFIX}_{name} add = {amount} }}"


def business_effects(spec: Mechanism, choice: int) -> list[str]:
    """Render deterministic CK3 writes; route C creates only debt/due metadata."""
    d, mid = spec.domain, spec.mid
    lines = [
        _set(spec.field, choice),
        _change("operation_used", 1),
        _set(f"m{mid}_choice", choice),
    ]
    if choice == 3:
        lines += [
            _set(f"m{mid}_debt_owner", "$TICKET_OWNER$"),
            _set(f"m{mid}_debt_subject", "$TICKET_SUBJECT$"),
            _set(f"m{mid}_debt_cycle", "$TICKET_CYCLE$"),
            _set(f"m{mid}_debt_case", "$TICKET_CASE$"),
            _set(f"m{mid}_debt_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"),
            _set(f"m{mid}_business_object_created", 0),
            _change("policy_debt", 1),
        ]
        return lines

    lines += [_set(f"m{mid}_business_object_created", 1)]
    # AB: authorised hours, overtime liabilities, meetings and leave all reconcile.
    if mid == 242:
        lines += [_change("hours_available", -20), _change("hours_output", 20), _set("m242_presence_hours", 30), _set("m242_output_hours", 20), _set("m242_presence_rewarded", 0 if choice == 1 else 1)]
    elif mid == 243:
        hours = 2 if choice == 1 else 4
        lines += [_change("hours_available", -hours), _change("hours_on_call", hours), _set("m243_urgency_frozen", 1), _set("m243_mandatory_for_all", 0 if choice == 1 else 1)]
    elif mid == 244:
        lines += [_change("hours_available", -5), _change("hours_output", 5), _change("gold_available", -10), _change("gold_paid", 10), _set("m244_refusal_protected", 1 if choice == 1 else 0), f"var:zg361_case_{d}_owner = {{ remove_gold = 10 }}", "add_gold = 10"]
    elif mid == 245:
        lines += [_change("overtime_pending", 5), _set("m245_overtime_hours", 5), _set("m245_approved", 1 if choice == 1 else 0), _set("m245_shadow_provenance", 0 if choice == 1 else 1)]
    elif mid == 246:
        lines += [_change("overtime_pending", -5), _set("m246_compensated_hours", 5)]
        if choice == 1:
            lines += [_change("gold_available", -15), _change("gold_paid", 15), _set("m246_compensation_route", 1), f"var:zg361_case_{d}_owner = {{ remove_gold = 15 }}", "add_gold = 15"]
        else:
            lines += [_change("leave_bank", 5), _set("m246_compensation_route", 2)]
    elif mid == 247:
        lines += [_set("m247_start_day", 10), _set("m247_end_day", 20 if choice == 1 else 375), _set("m247_roster_frozen", 1), _set("m247_renewal_required", 1 if choice == 1 else 0)]
    elif mid == 248:
        lines += [_set("m248_overloaded_cycles", 3), _change("manager_score", -5 if choice == 1 else -10), _set("m248_manager_cost_visible", 1)]
    elif mid == 249:
        hours = 6 if choice == 1 else 12
        lines += [_change("hours_available", -hours), _change("hours_meeting", hours), _set("m249_attendee_hours", hours), _set("m249_agenda_frozen", 1), _set("m249_decision_owner_frozen", 1)]
    elif mid == 250:
        lines += [_set("m250_attendee_count", 3), _set("m250_contributor_count", 1 if choice == 1 else 3), _set("m250_contribution_requires_evidence", 1 if choice == 1 else 0)]
    elif mid == 251:
        lines += [_set("m251_refusal_allowed", 1 if choice == 1 else 0), _set("m251_representative", "$TICKET_SUBJECT$"), _set("m251_representative_in_attendees", 1), _set("m251_decision_owner", "$TICKET_OWNER$"), _change("manager_score", -1 if choice == 1 else -3)]
    elif mid == 252:
        lines += [_change("hours_available", -8), _change("hours_leave", 8), _set("m252_original_target", 100), _set("m252_normalized_target", 92 if choice == 1 else 100), _set("m252_replacement_credit_bps", 2000)]
    elif mid == 253:
        lines += [_set("m253_minimum_duty_distinct", 1), _set("m253_appeal_repair", 1 if choice == 1 else 0), _set("m253_misconduct", 0 if choice == 1 else 1)]
    # AC: external capacity has a separate shadow-HC book; formal HC is shared.
    elif mid == 254:
        lines += [_change("shadow_hc_available", -1), _change("shadow_hc_active", 1), _change("gold_available", -20), _change("gold_reserved", 20), _change("contract_gold_reserved", 20), _set("m254_sunset_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m254_formal_hc_touched", 0)]
    elif mid == 255:
        lines += [_set("m255_formal_tco", 120), _set("m255_external_tco", 110), _set("m255_mixed_tco", 100), _set("m255_selected_tco", 100 if choice == 1 else 110)]
    elif mid == 256:
        lines += [_set("m256_external_pool_separate", 1 if choice == 1 else 0), _set("m256_external_entries_in_formal_cohort", 0 if choice == 1 else 1), _set("m256_displaced_formal_members", 0 if choice == 1 else 1)]
    elif mid == 257:
        lines += ["change_variable = { name = zg361_ch_hc_available add = -1 }", "change_variable = { name = zg361_ch_hc_reserved add = 1 }", _set("m257_conversion_pending", 1), _set("m257_conversion_official", "$TICKET_SUBJECT$"), _set("m257_recruitment_ref", "$TICKET_CASE$"), _set("m257_effective_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("formal_hc_pending", 1), _set("formal_hc_pending_owner", "$TICKET_OWNER$"), _set("formal_hc_pending_case", "$TICKET_CASE$"), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[257]} days = 365 }}"]
    elif mid == 258:
        lines += [_set("m258_missing_access_count", 1), _set("m258_target_adjustment", 20 if choice == 1 else 0), _set("m258_formal_grade_written", 0), _set("m258_governance_risk", 0 if choice == 1 else 1)]
    elif mid == 259:
        client, vendor = ((3000, 7000) if choice == 1 else (0, 10000))
        lines += [_set("m259_client_change_bps", client), _set("m259_vendor_management_bps", vendor), _set("m259_responsibility_total_bps", 10000), _set("m259_formal_grade_written", 0)]
    elif mid == 260:
        lines += [_set("m260_contract_type", 2 if choice == 1 else 1), _set("m260_ownership_frozen", 1), _set("m260_change_rule_frozen", 1)]
    elif mid == 261:
        lines += [_set("m261_chain_depth", 3 if choice == 1 else 5), _set("m261_actual_executor_frozen", 1), _set("m261_chain_acyclic", 1 if choice == 1 else 0)]
    elif mid == 262:
        home, host = ((40, 60) if choice == 1 else (0, 100))
        lines += [_set("m262_seconded_official", "$TICKET_SUBJECT$"), _set("m262_home_manager", "$TICKET_OWNER$"), _set("m262_host_manager", "$TICKET_SUBJECT$"), _set("m262_home_weight", home), _set("m262_host_weight", host), _set("m262_weight_total", 100), _set("m262_cost_booked_once", 1), _set("m262_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m262_review_pending", 1), _set("ac_s05_deadline_pending", 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[262]} days = 365 }}"]
    elif mid == 263:
        if choice == 1:
            lines += [_set("m263_return_choice", 1), _set("m263_prior_identity_preserved", 1), _set("m263_extension_terminal", 0), _set("m263_terminal_choice", 1), _set("m263_resolved_choice", 1), _set("m263_due_cycle", "$TICKET_CYCLE$")]
        else:
            lines += [_set("m263_return_choice", 0), _set("m263_prior_identity_preserved", 1), _set("m263_extension_terminal", 0), _set("m263_terminal_choice", 0), _set("m263_resolved_choice", 0), _set("m263_extension_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m263_extension_pending", 1), _set("m263_extension_count", 1), _set("ac_s05_deadline_pending", 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[263]} days = 365 }}"]
    elif mid == 264:
        lines += [_set("m264_accepted_by", "$TICKET_OWNER$"), _set("m264_payee", "$TICKET_SUBJECT$"), _set("m264_vendor_identity", "$TICKET_SUBJECT$"), _set("m264_accepted_by_frozen", 1)]
        if choice == 1:
            lines += [_change("gold_reserved", -20), _change("gold_paid", 20), _change("contract_gold_reserved", -20), _change("contract_gold_paid", 20), _set("m264_artifact_count", 3), _set("m264_documentation_accepted", 1), _set("m264_shadowing_accepted", 1), _set("m264_practical_acceptance", 1), _set("m264_payment_settled", 1), f"var:zg361_case_{d}_owner = {{ remove_gold = 20 }}", "add_gold = 20"]
        else:
            lines += [_change("gold_reserved", -20), _change("gold_available", 20), _change("contract_gold_reserved", -20), _set("m264_artifact_count", 0), _set("m264_documentation_accepted", 0), _set("m264_shadowing_accepted", 0), _set("m264_practical_acceptance", 0), _set("m264_payment_settled", 0), _set("m264_payment_refunded", 20)]
        lines += [f"if = {{ limit = {{ trigger_if = {{ limit = {{ has_variable = {PREFIX}_m257_conversion_settled }} NOT = {{ var:{PREFIX}_m257_conversion_settled = 1 }} }} trigger_else = {{ always = yes }} }} change_variable = {{ name = {PREFIX}_shadow_hc_active add = -1 }} change_variable = {{ name = {PREFIX}_shadow_hc_available add = 1 }} }}", _set("m264_shadow_hc_released", 1)]
    elif mid == 265:
        if choice == 1:
            lines += [_change("gold_paid", -5), _change("gold_available", 5), _change("contract_gold_paid", -5), _change("contract_gold_recovered", 5), _set("m265_evidence_count", 2), _set("m265_incident_evidence", f"var:{PREFIX}_m259_write_case"), _set("m265_executor_evidence", f"var:{PREFIX}_m261_write_case"), _set("m265_vendor_actor", "$TICKET_SUBJECT$"), _set("m265_liable_manager", "$TICKET_OWNER$"), _set("m265_manager_duty_evidence", f"var:{PREFIX}_m259_write_case"), _set("m265_recovery_payee", "$TICKET_OWNER$"), _set("m265_recovery_source", "$TICKET_SUBJECT$"), _set("m265_liability_total_bps", 10000), _set("m265_actor_identity_verified", 1), _set("m265_suspicion_only", 0), _set("m265_investigation_pending", 0), "remove_gold = 5", f"var:zg361_case_{d}_owner = {{ add_gold = 5 }}"]
        else:
            lines += [_set("m265_evidence_count", 0), _set("m265_actor_identity_verified", 0), _set("m265_suspicion_only", 1), _set("m265_management_chain_frozen", 1), _set("m265_investigation_pending", 1), _set("m265_recovery_gold", 0), _change("manager_score", -5)]
    # AD: one shared HC reservation, immutable votes, delayed outcome and holds.
    elif mid == 266:
        lines += ["change_variable = { name = zg361_ch_hc_available add = -1 }", "change_variable = { name = zg361_ch_hc_reserved add = 1 }", _set("m266_standard_bar", 70), _set("m266_selected_bar", 70 if choice == 1 else 60), _set("m266_urgency_level", 2 if choice == 1 else 4), _set("m266_hc_receipt", "$TICKET_CASE$"), _set("m266_hc_reservation_active", 1), _set("m266_vacancy_serial", "$TICKET_CASE$"), f"var:zg361_case_{d}_owner = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 1 }} set_variable = {{ name = {PREFIX}_ad_hc_flight_subject value = $TICKET_SUBJECT$ }} set_variable = {{ name = {PREFIX}_ad_hc_flight_cycle value = $TICKET_CYCLE$ }} set_variable = {{ name = {PREFIX}_ad_hc_flight_case value = $TICKET_CASE$ }} }}"]
    elif mid == 267:
        lines += [_set("m267_vote_count", 3), _set("m267_evidence_count", 3), _set("m267_anchor_before_votes", 0 if choice == 1 else 1), _set("m267_candidate_frozen", f"var:{PREFIX}_ad_external_candidate"), _set("m267_referral_present", f"var:{PREFIX}_ad_external_referral_present"), _set("m267_referrer_voted", f"var:{PREFIX}_ad_external_referrer_voted"), _set("m267_referral_frozen_case", "$TICKET_CASE$")]
        lines += [f"if = {{ limit = {{ var:{PREFIX}_ad_external_referral_present = 1 }} set_variable = {{ name = {PREFIX}_m267_referral_id value = var:{PREFIX}_ad_external_referral_id }} set_variable = {{ name = {PREFIX}_m267_referrer_frozen value = var:{PREFIX}_ad_external_referrer }} set_variable = {{ name = {PREFIX}_m267_referral_relationship value = var:{PREFIX}_ad_external_referral_relationship }} set_variable = {{ name = {PREFIX}_m267_referral_evidence_receipt value = var:{PREFIX}_ad_external_referral_evidence_receipt }} set_variable = {{ name = {PREFIX}_m267_referral_reward value = var:{PREFIX}_ad_external_referral_reward }} set_variable = {{ name = {PREFIX}_m267_referrer_excluded_before_seal value = 1 }} }}"]
        for slot in (1, 2, 3):
            lines += [_set(f"m267_interviewer_{slot}", f"var:{PREFIX}_ad_external_interviewer_{slot}"), _set(f"m267_vote_{slot}", f"var:{PREFIX}_ad_external_vote_{slot}"), _set(f"m267_vote_evidence_{slot}", f"var:{PREFIX}_ad_external_vote_evidence_{slot}")]
        # The seal is the commit marker for the complete identity/vote/evidence
        # snapshot, so it must be the last #267 business write.
        lines += [_set("m267_raw_votes_frozen", 1)]
    elif mid == 268:
        lines += [_set("m268_calibration_snapshot", "$TICKET_CASE$"), _set("m268_raw_votes_preserved", 1), _set("m268_adjustment_bound", 20 if choice == 1 else 100), _set("m268_training_required", 1 if choice == 1 else 0)]
    elif mid == 269:
        lines += [_set("m269_outcome_pending", 1), _set("m269_raw_vote_snapshot", 1), _set("m269_attribution_pending", 1), _set("m269_observed_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[269]} days = 365 }}"]
    elif mid == 270:
        lines += [_set("m270_role_class", 1 if choice == 1 else 4), _set("m270_threshold", 75 if choice == 1 else 85), _set("m270_policy_version", "$TICKET_CYCLE$"), _set("m270_raw_votes_rewritten", 0)]
    elif mid == 271:
        lines += [_change("gold_available", -5), _change("gold_reserved", 5), _change("referral_gold_reserved", 5), _set("m271_candidate", f"var:{PREFIX}_m267_candidate_frozen"), _set("m271_referrer", f"var:{PREFIX}_m267_referrer_frozen"), _set("m271_referrer_not_candidate", 1), _set("m271_relationship_disclosed", 1 if choice == 1 else 0), _set("m271_referrer_recused_before_vote", 1 if choice == 1 else 0), _set("m271_referrer_voted", f"var:{PREFIX}_m267_referrer_voted"), _set("m271_reward_due_after_probation", 1 if choice == 1 else 0), _set("m271_reward_escrowed", 1), f"var:zg361_case_{d}_owner = {{ remove_gold = 5 }}"]
        if choice == 2:
            lines += [_change("gold_reserved", -5), _change("gold_paid", 5), _change("referral_gold_reserved", -5), _change("referral_gold_paid", 5), _set("m271_internal_owner_credit", 5), _set("m271_reward_paid_before_probation", 1), _set("m271_reward_payee", f"var:{PREFIX}_m271_referrer"), _set("m271_reward_escrowed", 0), f"var:{PREFIX}_m271_referrer = {{ add_gold = 5 }}"]
    elif mid == 272:
        lines += [_change("gold_available", -10), _change("gold_reserved", 10), _change("offer_gold_reserved", 10), _set("m272_offer_candidate", "$TICKET_SUBJECT$"), _set("m272_offer_approver", "$TICKET_OWNER$"), _set("m272_offer_terms_frozen", 1), _set("m272_requested_level", 5 if choice == 1 else 6), _set("m272_cross_team_approver", 1 if choice == 1 else 0), _set("m272_premium_end_cycle", "{ value = $TICKET_CYCLE$ add = 1 }")]
    elif mid == 273:
        lines += [_set("candidate_active", 1), _set("candidate_active_owner", "$TICKET_OWNER$"), _set("candidate_active_case", "$TICKET_CASE$"), _set("m273_candidate_fingerprint", "$TICKET_SUBJECT$"), _set("m273_owner_frozen", "$TICKET_OWNER$"), _set("m273_scout_credit_bps", 3000 if choice == 1 else 10000), _set("m273_hiring_credit_bps", 7000 if choice == 1 else 0), _set("m273_credit_total_bps", 10000), _set("m273_additional_hc_reserved", 0)]
    elif mid == 274:
        lines += [_change("gold_available", -5), _change("gold_reserved", 5), _change("offer_gold_reserved", 5), _set("m274_counter_used", 1), _set("m274_counter_amount", 5 if choice == 1 else 15), _set("m274_fairness_cap", 10), _set("m274_offer_acceptance_candidate", 1 if choice == 1 else 0)]
        if choice == 1:
            lines += [_change("gold_reserved", -15), _change("gold_paid", 15), _change("offer_gold_reserved", -15), _change("offer_gold_paid", 15), "change_variable = { name = zg361_ch_hc_reserved add = -1 }", "change_variable = { name = zg361_ch_hc_occupied add = 1 }", _set("m266_hc_reservation_active", 0), _set("candidate_active", 0), _set("formal_hc_active", 1), _set("formal_hc_active_case", "$TICKET_CASE$"), _set("m274_hired", 1), _set("m274_hire_case", "$TICKET_CASE$"), _set("m274_probation_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), f"var:zg361_case_{d}_owner = {{ remove_gold = 15 set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 0 }} }}", "add_gold = 15"]
    elif mid == 275:
        due_add = 1 if choice == 1 else 3
        lines += [_set("m275_refusal", 1), _set("m275_refusal_reason_id", f"var:{PREFIX}_ad_external_refusal_reason_id"), _set("m275_original_candidate", "$TICKET_SUBJECT$"), _set("m275_hold_start_cycle", "$TICKET_CYCLE$"), _set("m275_hold_due_cycle", f"{{ value = $TICKET_CYCLE$ add = {due_add} }}"), _set("m275_hc_lineage_receipt", "$TICKET_CASE$"), _set("m275_hold_pending", 1), _set("m275_runner_attempt_new_case", 1 if choice == 1 else 0), _set("m275_policy_breach_indefinite_requested", 1 if choice == 2 else 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[275]} days = {90 if choice == 1 else 365} }}"]
        if choice == 1:
            lines += [_set("m275_runner_up", f"var:{PREFIX}_ad_external_runner_up"), _set("m275_runner_up_evidence", f"var:{PREFIX}_ad_external_runner_up_evidence"), _set("m275_runner_reopen_pending", 0)]
        else:
            lines += [_set("m275_reason_remediated", 0)]
        lines += [f"if = {{ limit = {{ has_variable = {PREFIX}_m269_outcome_pending var:{PREFIX}_m269_outcome_pending = 1 var:{PREFIX}_m269_write_case = $TICKET_CASE$ }} set_variable = {{ name = {PREFIX}_m269_outcome_pending value = 0 }} set_variable = {{ name = {PREFIX}_m269_watch_cancelled_by_refusal value = 1 }} }}"]
        lines += [_change("gold_reserved", -15), _change("gold_available", 15), _change("offer_gold_reserved", -15), _change("offer_gold_refunded", 15), _set("candidate_active", 0), f"if = {{ limit = {{ has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 }} change_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_available add = 5 }} set_variable = {{ name = {PREFIX}_m271_reward_refunded value = 1 }} set_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }} var:zg361_case_{d}_owner = {{ add_gold = 5 }} }}"]
    elif mid == 276:
        lines += [_set("m276_old_case_hash", "$TICKET_CASE$"), _set("m276_old_history_retained", 1), _set("m276_growth_evidence_frozen", 1 if choice == 1 else 0), _set("m276_history_wipe_attempt", 0 if choice == 1 else 1), _set("m276_hc_touched", 0)]
    elif mid == 277:
        lines += ["change_variable = { name = zg361_ch_hc_occupied add = -1 }", "change_variable = { name = zg361_ch_hc_frozen add = 1 }", _set("formal_hc_active", 0), _set("m277_pip_case_frozen", "$TICKET_CASE$"), _set("m277_former_hc_lineage", f"var:{PREFIX}_formal_hc_active_case"), _set("m277_displaced_subject", "$TICKET_SUBJECT$"), _set("m277_displaced_hours", 20), _set("m277_displaced_cost_provenance", "$TICKET_CASE$"), _set("m277_work_proof", 1 if choice == 1 else 0), _set("m277_automatic_refill", 0 if choice == 1 else 1), _set("m277_vacant_frozen", 1), _set("m277_hc_minted", 0)]
    # AL: immutable multi-cycle facts, quota conservation and future-only charter.
    elif mid == 355:
        lines += [_set("m355_prior_target", 100), _set("m355_prior_actual", 150), _set("m355_repeatable_excess", 20), _set("m355_windfall_excess", 30), _set("m355_excess_total", 50), _set("m355_new_target", 120 if choice == 1 else 150), _set("m355_underproduction_risk", 0 if choice == 1 else 50), _set("m355_authority_ref", "$TICKET_OWNER$"), _set("m355_funding_approved_by", "$TICKET_OWNER$"), _set("m355_old_fact_hash_retained", 1)]
        if choice == 1:
            lines += [_change("gold_available", -10), _change("gold_reserved", 10), _change("target_gold_reserved", 10), _set("m355_target_install_pending", 1), _set("m355_effective_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[355]} days = 365 }}"]
    elif mid == 356:
        lines += [_set("m356_actual_value", 100), _set("m356_completion_cycle", "$TICKET_CYCLE$"), _set("m356_report_cycle", "$TICKET_CYCLE$" if choice == 1 else "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m356_credited_value", 100), _set("m356_net_credit", 100), _set("m356_timestamp_frozen", 1), _set("m356_audit_pending", 1 if choice == 2 else 0)]
        if choice == 2:
            lines += [f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[356]} days = 90 }}"]
    elif mid == 360:
        lines += _collective_business_writes(choice)
    elif mid == 361:
        lines += _charter_business_writes(choice)
        if choice == 1:
            lines += [_set("m361_priority_fairness", 1), _set("m361_priority_innovation", 2), _set("m361_priority_warmth", 3), _set("m361_priority_competition", 4), _set("m361_noncompetition_ahead", 3), _set("m361_delivery_horizon", 2), _set("m361_future_quota_default", 1), _set("m361_future_appeal_default", 1), _set("m361_future_bonus_default", 1), _set("m361_future_hc_default", 1), _set("m361_future_manager_accountability_default", 1), _set("m361_future_transparency_default", 1)]
        else:
            lines += [_set("m361_priority_competition", 1), _set("m361_priority_fairness", 2), _set("m361_priority_innovation", 3), _set("m361_priority_warmth", 4), _set("m361_noncompetition_ahead", 0), _set("m361_delivery_horizon", 1), _set("m361_future_quota_default", 2), _set("m361_future_appeal_default", 2), _set("m361_future_bonus_default", 2), _set("m361_future_hc_default", 2), _set("m361_future_manager_accountability_default", 2), _set("m361_future_transparency_default", 2)]
    return lines


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
\tRECEIPT_OWNER_VAR = {PREFIX}_m{mid}_receipt_owner
\tRECEIPT_SUBJECT_VAR = {PREFIX}_m{mid}_receipt_subject
\tRECEIPT_CYCLE_VAR = {PREFIX}_m{mid}_receipt_cycle
\tRECEIPT_CASE_VAR = {PREFIX}_m{mid}_receipt_case
\tRECEIPT_STATE_VAR = {PREFIX}_m{mid}_receipt_state
\tRECEIPT_CHOICE_VAR = {PREFIX}_m{mid}_receipt_choice
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
    required = [
        *(f"{PREFIX}_m{mid}_write_{name}" for name in ("owner", "subject", "cycle", "case", "state")),
        f"{PREFIX}_{spec.field}",
        *(f"zg361_case_{d}_{name}" for name in ("owner", "subject", "cycle_serial", "case_serial", "state")),
    ]
    existence = "\n".join(f"\t\t\t\thas_variable = {name}" for name in required)
    comparisons = "\n".join((
        f"\t\t\tvar:{PREFIX}_m{mid}_write_owner = var:zg361_case_{d}_owner",
        f"\t\t\tvar:{PREFIX}_m{mid}_write_subject = var:zg361_case_{d}_subject",
        f"\t\t\tvar:{PREFIX}_m{mid}_write_cycle = var:zg361_case_{d}_cycle_serial",
        f"\t\t\tvar:{PREFIX}_m{mid}_write_case = var:zg361_case_{d}_case_serial",
        f"\t\t\tvar:{PREFIX}_m{mid}_write_state = var:zg361_case_{d}_state",
    ))
    consumed_exists = "\n".join(
        f"\t\t\t\t\t\thas_variable = {PREFIX}_m{mid}_consumed_{name}"
        for name in ("owner", "subject", "cycle", "case", "state")
    )
    consumed_equal = "\n".join(
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_consumed_{name} = var:{PREFIX}_m{mid}_write_{name}"
        for name in ("owner", "subject", "cycle", "case", "state")
    )
    writes = "\n".join(
        f"\t\tset_variable = {{ name = {PREFIX}_m{mid}_consumed_{name} value = var:{PREFIX}_m{mid}_write_{name} }}"
        for name in ("owner", "subject", "cycle", "case", "state")
    )
    return f"""# #{mid:03d} read-side projection; existence gates precede tuple reads.
{PREFIX}_m{mid}_consume_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
{existence}
\t\t\t\t}}
{comparisons}
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{
{consumed_exists}
\t\t\t\t\t}}
\t\t\t\t\tNOT = {{
{consumed_equal}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\ttrigger_else = {{ always = yes }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = no }}
\t\t}}
{writes}
\t\tset_variable = {{ name = {PREFIX}_m{mid}_visible_value value = var:{PREFIX}_{spec.field} }}
\t\tset_variable = {{ name = {PREFIX}_m{mid}_visible_provenance_case value = var:{PREFIX}_m{mid}_write_case }}
\t\tchange_variable = {{ name = {PREFIX}_{d}_visible_revision add = 1 }}
\t}}
}}"""


def deadline_prefix(domain: str, state: int) -> str:
    return f"{PREFIX}_{domain}_s{state:02d}_deadline"


def deadline_event_id(domain: str, state: int) -> int:
    return DOMAIN_EVENT_BASE[domain] + state


def deadline_relay_event_id(domain: str, state: int) -> int:
    """Immediate owner-root relay paired with one subject-root deadline."""
    return DOMAIN_EVENT_BASE[domain] + 100 + state


def render_schedule(domain: str, state: int) -> str:
    dl = deadline_prefix(domain, state)
    return f"""{PREFIX}_{domain}_schedule_stage_{state:02d}_deadline_effect = {{
\tzg361_case_kernel_schedule_deadline_effect = {{
\t\tOWNER_VAR = zg361_case_{domain}_owner
\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\tCYCLE_VAR = zg361_case_{domain}_cycle_serial
\t\tCASE_VAR = zg361_case_{domain}_case_serial
\t\tSTATE_VAR = zg361_case_{domain}_state
\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\tDEADLINE_OWNER_VAR = {dl}_owner
\t\tDEADLINE_SUBJECT_VAR = {dl}_subject
\t\tDEADLINE_CYCLE_VAR = {dl}_cycle
\t\tDEADLINE_CASE_VAR = {dl}_case
\t\tDEADLINE_STATE_VAR = {dl}_state
\t\tDEADLINE_DAYS_VAR = {dl}_days
\t\tDEADLINE_PENDING_VAR = {dl}_pending
\t\tDEADLINE_EXPIRED_VAR = {dl}_expired
\t\tTICKET_OWNER = var:zg361_case_{domain}_owner
\t\tTICKET_SUBJECT = this
\t\tTICKET_CYCLE = var:zg361_case_{domain}_cycle_serial
\t\tTICKET_CASE = var:zg361_case_{domain}_case_serial
\t\tTICKET_STATE = {state}
\t\tDAYS = {DEADLINE_DAYS[domain]}
\t\tEVENT = {NAMESPACE}.{deadline_event_id(domain, state)}
\t}}
}}"""


def first_mid_for_state(domain: str, state: int) -> int | None:
    for mid in DOMAIN_ORDER[domain]:
        spec = by_id()[mid]
        if spec.state == state:
            return mid
    return None


def render_timeout(domain: str, state: int) -> str:
    specs = [spec for spec in MECHANISMS if spec.domain == domain and spec.state == state]
    calls = "\n".join(
        f"""{PREFIX}_m{spec.mid}_route_c_effect = {{
\tTICKET_OWNER = var:zg361_case_{domain}_owner
\tTICKET_SUBJECT = this
\tTICKET_CYCLE = var:zg361_case_{domain}_cycle_serial
\tTICKET_CASE = var:zg361_case_{domain}_case_serial
}}"""
        for spec in specs
    )
    next_mid = first_mid_for_state(domain, state + 1)
    visible_next = ""
    if next_mid is not None:
        visible_next = f"""
\tif = {{
\t\tlimit = {{
\t\t\tvar:zg361_case_{domain}_owner = {{ is_ai = no }}
\t\t\tvar:zg361_case_{domain}_state = {state + 1}
\t\t}}
\t\tvar:zg361_case_{domain}_owner = {{ trigger_event = {{ id = {NAMESPACE}.{next_mid} }} }}
\t}}"""
    return f"""{PREFIX}_{domain}_timeout_stage_{state:02d}_effect = {{
{indent(calls)}{visible_next}
\tdebug_log = \"ZG361WE: {domain.upper()} stage {state} exact deadline consumed\"
}}"""


def _after_advance(spec: Mechanism) -> str:
    d, mid, state = spec.domain, spec.mid, spec.state
    if d == "al" and mid == 356:
        return f"""if = {{
	limit = {{ NOT = {{ zg361_is_celestial_liege_trigger = yes }} }}
	{PREFIX}_finalize_nonmanager_na_effect = yes
}}
else = {{
	set_variable = {{ name = {PREFIX}_awaiting_al_357_359 value = 1 }}
	set_variable = {{ name = {PREFIX}_portfolio_status value = 5 }} # external dependency, not success
}}"""
    if d == "al" and mid == 360:
        return f"""{PREFIX}_al_schedule_stage_05_deadline_effect = yes
if = {{
\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t{PREFIX}_m361_route_a_effect = {{
\t\tTICKET_OWNER = var:zg361_case_al_owner
\t\tTICKET_SUBJECT = this
\t\tTICKET_CYCLE = var:zg361_case_al_cycle_serial
\t\tTICKET_CASE = var:zg361_case_al_case_serial
\t}}
}}"""
    if d == "al" and mid == 361:
        return f"{PREFIX}_finalize_portfolio_effect = yes"
    if state < 6:
        return f"{PREFIX}_{d}_schedule_stage_{state + 1:02d}_deadline_effect = yes"
    next_domain = NEXT_DOMAIN[d]
    if next_domain:
        return f"{PREFIX}_{next_domain}_launch_effect = yes"
    return f"{PREFIX}_finalize_portfolio_effect = yes"


def render_route_effect(spec: Mechanism, choice: int) -> str:
    mid, d = spec.mid, spec.domain
    letter = "abc"[choice - 1]
    guard = tuple_guard(spec)
    receipts = any_receipt(spec)
    checks = atomic_precheck(spec, choice)
    business = "\n".join(business_effects(spec, choice))
    advance = ""
    # #263 route B is a bounded extension, not a terminal return choice.  Its
    # delayed consumer advances the case only after the new due cycle.
    if mid in STAGE_LAST[d] and not (mid == 263 and choice == 2):
        barrier = stage_barrier(spec)
        edge = STAGE_LAST[d][mid]
        after = _after_advance(spec)
        deadline = deadline_prefix(d, edge)
        advance = f"""
\t\t\tif = {{
\t\t\t\tlimit = {{
{indent(barrier, 5)}
\t\t\t\t}}
\t\t\t\tset_variable = {{ name = {deadline}_pending value = 0 }}
\t\t\t\tzg361_case_{d}_advance_{edge:02d}_effect = {{
\t\t\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
{indent(after, 5)}
\t\t\t\t}}
\t\t\t}}
"""
    red_code = mid * 10 + choice
    return f"""# #{mid:03d} route {letter.upper()}: guard -> atomic precheck -> receipt -> write -> consumer.
{PREFIX}_m{mid}_route_{letter}_effect = {{
\tremove_variable = {PREFIX}_runtime_applied
\tremove_variable = {PREFIX}_last_red_code
\tif = {{
\t\tlimit = {{
{indent(guard, 3)}
\t\t\tNOT = {{
{indent(receipts, 4)}
\t\t\t}}
{indent(checks, 3)}
\t\t}}
{indent(operation_call(spec, choice), 2)}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_runtime_applied value = 1 }}
{indent(business, 3)}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_write_owner value = $TICKET_OWNER$ }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_write_subject value = $TICKET_SUBJECT$ }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_write_cycle value = $TICKET_CYCLE$ }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_write_case value = $TICKET_CASE$ }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_write_state value = {spec.state} }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_provenance_case value = $TICKET_CASE$ }}
\t\t\tset_variable = {{ name = {PREFIX}_m{mid}_provenance_choice value = {choice} }}
\t\t\t{PREFIX}_m{mid}_consume_effect = yes
\t\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 1 }}
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
{indent(checks, 4)}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_last_red_code value = {red_code} }}
\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 4 }} # typed RED, no receipt or business write
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
{indent(receipt_guard(spec, choice), 3)}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 2 }} # idempotent no-op
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(guard, 3)}
{indent(receipts, 3)}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_last_red_code value = {mid * 10 + 9} }}
\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 4 }} # route collision typed RED
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_runtime_status value = 3 }} }} # stale no-op
}}"""


def render_portfolio_initialize() -> str:
    return f"""# Finite portfolio books. Shared formal HC is read, never reinitialized here.
{PREFIX}_initialize_portfolio_effect = {{
\tsave_scope_as = {PREFIX}_portfolio_subject
\troot = {{ save_scope_as = {PREFIX}_portfolio_owner }}
\tset_variable = {{ name = {PREFIX}_portfolio_cycle value = root.var:zg361_review_serial }}
\troot = {{ set_variable = {{ name = {PREFIX}_manager_portfolio_cycle value = var:zg361_review_serial }} }}
\tset_variable = {{ name = {PREFIX}_operation_total value = 40 }}
\tset_variable = {{ name = {PREFIX}_operation_used value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_total value = 400 }}
\tset_variable = {{ name = {PREFIX}_hours_available value = 400 }}
\tset_variable = {{ name = {PREFIX}_hours_output value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_on_call value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_meeting value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_leave value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_governance value = 0 }}
\tset_variable = {{ name = {PREFIX}_overtime_pending value = 0 }}
\tset_variable = {{ name = {PREFIX}_leave_bank value = 0 }}
\t# Gold and shadow-HC books are fixed-cap persistent books.  A new review
\t# never resets debt and never mints another allocation.
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_gold_total }} }} set_variable = {{ name = {PREFIX}_gold_total value = 200 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_gold_available }} }} set_variable = {{ name = {PREFIX}_gold_available value = 200 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_gold_reserved }} }} set_variable = {{ name = {PREFIX}_gold_reserved value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_gold_paid }} }} set_variable = {{ name = {PREFIX}_gold_paid value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_contract_gold_reserved }} }} set_variable = {{ name = {PREFIX}_contract_gold_reserved value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_contract_gold_paid }} }} set_variable = {{ name = {PREFIX}_contract_gold_paid value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_contract_gold_recovered }} }} set_variable = {{ name = {PREFIX}_contract_gold_recovered value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_referral_gold_reserved }} }} set_variable = {{ name = {PREFIX}_referral_gold_reserved value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_referral_gold_paid }} }} set_variable = {{ name = {PREFIX}_referral_gold_paid value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_offer_gold_reserved }} }} set_variable = {{ name = {PREFIX}_offer_gold_reserved value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_offer_gold_paid }} }} set_variable = {{ name = {PREFIX}_offer_gold_paid value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_offer_gold_refunded }} }} set_variable = {{ name = {PREFIX}_offer_gold_refunded value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_target_gold_reserved }} }} set_variable = {{ name = {PREFIX}_target_gold_reserved value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_shadow_hc_total }} }} set_variable = {{ name = {PREFIX}_shadow_hc_total value = 4 }} set_variable = {{ name = {PREFIX}_shadow_hc_available value = 4 }} set_variable = {{ name = {PREFIX}_shadow_hc_active value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_shadow_hc_available }} }} set_variable = {{ name = {PREFIX}_shadow_hc_available value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_shadow_hc_active }} }} set_variable = {{ name = {PREFIX}_shadow_hc_active value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_manager_score }} }} set_variable = {{ name = {PREFIX}_manager_score value = 100 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_policy_debt }} }} set_variable = {{ name = {PREFIX}_policy_debt value = 0 }} }}
\troot = {{
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_trust }} }} set_variable = {{ name = {PREFIX}_realm_trust value = 100 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_version }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_version value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_previous_version }} }} set_variable = {{ name = {PREFIX}_realm_charter_previous_version value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_history_count }} }} set_variable = {{ name = {PREFIX}_realm_charter_history_count value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_id }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_id value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_previous_id }} }} set_variable = {{ name = {PREFIX}_realm_charter_previous_id value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_cycle_hash }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_cycle_hash value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_report_id }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_report_id value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_adopted_day }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_adopted_day value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_effective_cycle }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_effective_cycle value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_history_tail_hash }} }} set_variable = {{ name = {PREFIX}_realm_charter_history_tail_hash value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_current_default_quota }} }} set_variable = {{ name = {PREFIX}_realm_current_default_quota value = 0 }} set_variable = {{ name = {PREFIX}_realm_current_default_appeal value = 0 }} set_variable = {{ name = {PREFIX}_realm_current_default_bonus value = 0 }} set_variable = {{ name = {PREFIX}_realm_current_default_hc value = 0 }} set_variable = {{ name = {PREFIX}_realm_current_default_manager_accountability value = 0 }} set_variable = {{ name = {PREFIX}_realm_current_default_transparency value = 0 }} }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = {PREFIX}_realm_future_default_effective_cycle
\t\t\t\tvar:zg361_review_serial >= var:{PREFIX}_realm_future_default_effective_cycle
\t\t\t}}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_quota value = var:{PREFIX}_realm_future_default_quota }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_appeal value = var:{PREFIX}_realm_future_default_appeal }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_bonus value = var:{PREFIX}_realm_future_default_bonus }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_hc value = var:{PREFIX}_realm_future_default_hc }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_manager_accountability value = var:{PREFIX}_realm_future_default_manager_accountability }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_current_default_transparency value = var:{PREFIX}_realm_future_default_transparency }}
\t\t}}
\t}}
\tset_variable = {{ name = {PREFIX}_portfolio_default_quota value = root.var:{PREFIX}_realm_current_default_quota }}
\tset_variable = {{ name = {PREFIX}_portfolio_default_appeal value = root.var:{PREFIX}_realm_current_default_appeal }}
\tset_variable = {{ name = {PREFIX}_portfolio_default_bonus value = root.var:{PREFIX}_realm_current_default_bonus }}
\tset_variable = {{ name = {PREFIX}_portfolio_default_hc value = root.var:{PREFIX}_realm_current_default_hc }}
\tset_variable = {{ name = {PREFIX}_portfolio_default_manager_accountability value = root.var:{PREFIX}_realm_current_default_manager_accountability }}
\tset_variable = {{ name = {PREFIX}_portfolio_default_transparency value = root.var:{PREFIX}_realm_current_default_transparency }}
\tset_variable = {{ name = {PREFIX}_portfolio_status value = 1 }}
\tset_variable = {{ name = {PREFIX}_portfolio_closed value = 0 }}
\tremove_variable = {PREFIX}_awaiting_al_357_359
}}"""


def render_domain_init(domain: str) -> str:
    cleanup: list[str] = []
    for spec in MECHANISMS:
        if spec.domain == domain:
            cleanup += [
                f"remove_variable = {PREFIX}_{spec.field}",
                f"remove_variable = {PREFIX}_m{spec.mid}_visible_value",
            ]
    for state in sorted(set(STAGE_LAST[domain].values())):
        dl = deadline_prefix(domain, state)
        cleanup += [
            f"set_variable = {{ name = {dl}_pending value = 0 }}",
            f"set_variable = {{ name = {dl}_expired value = 0 }}",
        ]
    return f"""{PREFIX}_{domain}_initialize_effect = {{
\tset_variable = {{ name = {PREFIX}_{domain}_visible_revision value = 0 }}
{indent(chr(10).join(cleanup))}
}}"""


def render_subject_read(domain: str) -> str:
    return f"""# Counts/barons are assessed-only: no open, stage, HC or manager authority.
{PREFIX}_{domain}_subject_read_effect = {{
\tif = {{
\t\tlimit = {{
\t\t\tzg361_case_kernel_subject_self_guard_trigger = {{
\t\t\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\t\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_{domain}_subject_seen_revision value = var:{PREFIX}_{domain}_visible_revision }}
\t}}
}}"""


def render_ai(domain: str) -> str:
    # AL launch owns only state 1. States 4/5 resume through the one public adapter.
    specs = [
        by_id()[mid] for mid in DOMAIN_ORDER[domain]
        if domain != "al" or by_id()[mid].state == 1
    ]
    calls = "\n".join(
        f"""{PREFIX}_m{spec.mid}_route_a_effect = {{
\tTICKET_OWNER = scope:{PREFIX}_{domain}_owner
\tTICKET_SUBJECT = scope:{PREFIX}_{domain}_subject
\tTICKET_CYCLE = scope:{PREFIX}_{domain}_cycle
\tTICKET_CASE = scope:{PREFIX}_{domain}_case
}}"""
        for spec in specs
    )
    return f"""{PREFIX}_{domain}_run_authorized_ai_effect = {{
\t# The project owner's second AI exception is silent/background-only.
\tif = {{
\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
{indent(calls, 2)}
\t}}
}}"""


def render_launch(domain: str) -> str:
    first = first_mid_for_state(domain, 1)
    portfolio_init = f"\n\t\t{PREFIX}_initialize_portfolio_effect = yes" if domain == "ab" else ""
    return f"""# Internal subject-scope launch; ROOT is the eligible direct manager.
{PREFIX}_{domain}_launch_effect = {{
\tremove_variable = {PREFIX}_runtime_applied
\tzg361_case_{domain}_open_effect = yes
\tif = {{
\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}{portfolio_init}
\t\t{PREFIX}_{domain}_initialize_effect = yes
\t\tvar:zg361_case_{domain}_owner = {{ save_scope_as = {PREFIX}_{domain}_owner }}
\t\tsave_scope_as = {PREFIX}_{domain}_subject
\t\tsave_scope_value_as = {{ name = {PREFIX}_{domain}_cycle value = var:zg361_case_{domain}_cycle_serial }}
\t\tsave_scope_value_as = {{ name = {PREFIX}_{domain}_case value = var:zg361_case_{domain}_case_serial }}
\t\t{PREFIX}_{domain}_schedule_stage_01_deadline_effect = yes
\t\tif = {{
\t\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t{PREFIX}_{domain}_run_authorized_ai_effect = yes
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ root = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
\t\t\tscope:{PREFIX}_{domain}_owner = {{ trigger_event = {{ id = {NAMESPACE}.{first} }} }}
\t\t}}
\t}}
}}"""


def render_portfolio_entry() -> str:
    active_clear = "\n".join(
        f"""trigger_if = {{ limit = {{ has_variable = zg361_case_{domain}_active }} var:zg361_case_{domain}_active = 0 }}
trigger_else = {{ always = yes }}"""
        for domain in ("ab", "ac", "ad", "al")
    )
    future_clear = "\n".join(
        _zero_or_missing(f"{PREFIX}_{pending}")
        for pending in (*FUTURE_PENDING.values(), "m275_runner_reopen_pending")
    )
    return f"""# The only public manager-scope ABI:
# {PREFIX}_open_portfolio_effect = {{ SUBJECT = <direct assessed vassal> }}.
{PREFIX}_open_portfolio_effect = {{
\tremove_variable = {PREFIX}_runtime_applied
\tremove_variable = {PREFIX}_last_red_code
\tif = {{
\t\t# Resume #360/#361 only after external #357-359 advanced AL to state 4/5.
\t\tlimit = {{
\t\t\thas_game_rule = zg361_on
\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\thas_variable = zg361_review_serial
\t\t\t$SUBJECT$ = {{ zg361_is_reviewable_vassal_trigger = yes liege = root }}
\t\t\t$SUBJECT$ = {{ zg361_is_celestial_liege_trigger = yes }}
\t\t\t$SUBJECT$ = {{
\t\t\t\thas_variable = zg361_case_al_active
\t\t\t\tvar:zg361_case_al_active = 1
\t\t\t\tvar:zg361_case_al_owner = root
\t\t\t\tvar:zg361_case_al_subject = this
\t\t\t\tvar:zg361_case_al_cycle_serial = root.var:zg361_review_serial
\t\t\t\tOR = {{ var:zg361_case_al_state = 4 var:zg361_case_al_state = 5 }}
\t\t\t\thas_variable = {PREFIX}_al_external_stage_receipts_verified
\t\t\t\tvar:{PREFIX}_al_external_stage_receipts_verified = 1
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_owner
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_subject
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_cycle
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_case
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_state
\t\t\t\thas_variable = {PREFIX}_al_external_receipt_count
\t\t\t\thas_variable = {PREFIX}_al_external_last_operation
\t\t\t\tvar:{PREFIX}_al_external_receipt_owner = root
\t\t\t\tvar:{PREFIX}_al_external_receipt_subject = this
\t\t\t\tvar:{PREFIX}_al_external_receipt_cycle = var:zg361_case_al_cycle_serial
\t\t\t\tvar:{PREFIX}_al_external_receipt_case = var:zg361_case_al_case_serial
\t\t\t\tvar:{PREFIX}_al_external_receipt_state = 4
\t\t\t\tvar:{PREFIX}_al_external_receipt_count = 3
\t\t\t\tvar:{PREFIX}_al_external_last_operation = 359
\t\t\t}}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ $SUBJECT$ = {{ var:zg361_case_al_state = 5 }} }}
\t\t\t\troot = {{
\t\t\t\t\ttrigger_if = {{
\t\t\t\t\t\tlimit = {{ exists = liege }}
\t\t\t\t\t\tNOT = {{ liege = {{ zg361_is_celestial_liege_trigger = yes }} }}
\t\t\t\t\t}}
\t\t\t\t\ttrigger_else = {{ always = yes }}
\t\t\t\t}}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\t$SUBJECT$ = {{
\t\t\tremove_variable = {PREFIX}_awaiting_al_357_359
\t\t\tvar:zg361_case_al_owner = {{ save_scope_as = {PREFIX}_al_owner }}
\t\t\tsave_scope_as = {PREFIX}_al_subject
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_al_cycle value = var:zg361_case_al_cycle_serial }}
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_al_case value = var:zg361_case_al_case_serial }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_case_al_state = 4 }}
\t\t\t\t{PREFIX}_al_schedule_stage_04_deadline_effect = yes
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ root = {{ is_ai = yes }} }}
\t\t\t\t\t{PREFIX}_m360_route_a_effect = {{ TICKET_OWNER = var:zg361_case_al_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_al_cycle_serial TICKET_CASE = var:zg361_case_al_case_serial }}
\t\t\t\t}}
\t\t\t\telse = {{ root = {{ trigger_event = {{ id = {NAMESPACE}.360 }} }} }}
\t\t\t}}
\t\t\telse_if = {{
\t\t\t\tlimit = {{ var:zg361_case_al_state = 5 }}
\t\t\t\t{PREFIX}_al_schedule_stage_05_deadline_effect = yes
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ root = {{ is_ai = yes }} }}
\t\t\t\t\t{PREFIX}_m361_route_a_effect = {{ TICKET_OWNER = var:zg361_case_al_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_al_cycle_serial TICKET_CASE = var:zg361_case_al_case_serial }}
\t\t\t\t}}
\t\t\t\telse = {{ root = {{ trigger_event = {{ id = {NAMESPACE}.361 }} }} }}
\t\t\t}}
\t\t}}
\t}}
\telse_if = {{
\t\t# Start one new portfolio. Replay cannot reset an active/same-cycle book.
\t\tlimit = {{
\t\t\thas_game_rule = zg361_on
\t\t\tzg361_is_celestial_liege_trigger = yes
\t\t\thas_variable = zg361_review_serial
\t\t\t{_zero_or_missing(f'{PREFIX}_ad_hc_flight_pending')}
\t\t\t$SUBJECT$ = {{ zg361_is_reviewable_vassal_trigger = yes liege = root }}
\t\t\t# Counts/barons are valid direct assessed subjects for AB/AC/AD. Only
\t\t\t# manager-specific routes and the AL #360/#361 resume require duke+.
\t\t\t$SUBJECT$ = {{
\t\t\t\thas_variable = zg361_ch_hc_authorized
\t\t\t\thas_variable = zg361_ch_hc_available
\t\t\t\thas_variable = zg361_ch_hc_reserved
\t\t\t\thas_variable = zg361_ch_hc_occupied
\t\t\t\thas_variable = zg361_ch_hc_frozen
\t\t\t\thas_variable = zg361_ch_hc_reclaimed
{indent(future_clear, 4)}
\t\t\t\t{_zero_or_missing(f'{PREFIX}_m266_hc_reservation_active')}
\t\t\t}}
\t\t\ttrigger_if = {{ limit = {{ has_variable = {PREFIX}_manager_portfolio_cycle }} NOT = {{ var:{PREFIX}_manager_portfolio_cycle = var:zg361_review_serial }} }}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\t$SUBJECT$ = {{
{indent(active_clear, 4)}
\t\t\t}}
\t\t}}
\t\t$SUBJECT$ = {{ {PREFIX}_ab_launch_effect = yes }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_last_red_code value = 9001 }}
\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
\t}}
}}"""


def _future_tuple_guard(mid: int) -> str:
    state = by_id()[mid].state
    choices = " ".join(f"var:{PREFIX}_m{mid}_receipt_choice = {choice}" for choice in FUTURE_CHOICES[mid])
    return f"""trigger_if = {{
\tlimit = {{
\t\thas_variable = {PREFIX}_m{mid}_write_owner
\t\thas_variable = {PREFIX}_m{mid}_write_subject
\t\thas_variable = {PREFIX}_m{mid}_write_cycle
\t\thas_variable = {PREFIX}_m{mid}_write_case
\t\thas_variable = {PREFIX}_m{mid}_write_state
\t\thas_variable = {PREFIX}_m{mid}_receipt_owner
\t\thas_variable = {PREFIX}_m{mid}_receipt_subject
\t\thas_variable = {PREFIX}_m{mid}_receipt_cycle
\t\thas_variable = {PREFIX}_m{mid}_receipt_case
\t\thas_variable = {PREFIX}_m{mid}_receipt_state
\t\thas_variable = {PREFIX}_m{mid}_receipt_choice
\t}}
\tvar:{PREFIX}_m{mid}_write_subject = this
\tvar:{PREFIX}_m{mid}_write_owner = var:{PREFIX}_m{mid}_receipt_owner
\tvar:{PREFIX}_m{mid}_write_subject = var:{PREFIX}_m{mid}_receipt_subject
\tvar:{PREFIX}_m{mid}_write_cycle = var:{PREFIX}_m{mid}_receipt_cycle
\tvar:{PREFIX}_m{mid}_write_case = var:{PREFIX}_m{mid}_receipt_case
\tvar:{PREFIX}_m{mid}_write_state = var:{PREFIX}_m{mid}_receipt_state
\tvar:{PREFIX}_m{mid}_receipt_state = {state}
\tOR = {{ {choices} }}
}}
trigger_else = {{ always = no }}"""


def render_future_consumers() -> str:
    return f"""# Cross-period consumers are single-flight.  The route cannot
# overwrite its receipt/write tuple until the queued consumer clears pending.
{PREFIX}_m257_future_consume_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(257), 3)}
\t\t\thas_variable = {PREFIX}_m257_conversion_pending
\t\t\tvar:{PREFIX}_m257_conversion_pending = 1
\t\t\thas_variable = {PREFIX}_formal_hc_pending
\t\t\tvar:{PREFIX}_formal_hc_pending = 1
\t\t\tvar:{PREFIX}_formal_hc_pending_owner = var:{PREFIX}_m257_write_owner
\t\t\tvar:{PREFIX}_formal_hc_pending_case = var:{PREFIX}_m257_write_case
\t\t\tvar:{PREFIX}_m257_conversion_official = this
\t\t\thas_variable = zg361_ch_hc_reserved
\t\t\tvar:zg361_ch_hc_reserved >= 1
\t\t\thas_variable = {PREFIX}_shadow_hc_active
\t\t\tvar:{PREFIX}_shadow_hc_active >= 1
\t\t\tvar:{PREFIX}_m257_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m257_effective_cycle }}
\t\t}}
\t\tchange_variable = {{ name = zg361_ch_hc_reserved add = -1 }}
\t\tchange_variable = {{ name = zg361_ch_hc_occupied add = 1 }}
\t\tchange_variable = {{ name = {PREFIX}_shadow_hc_active add = -1 }}
\t\tchange_variable = {{ name = {PREFIX}_shadow_hc_available add = 1 }}
\t\tset_variable = {{ name = {PREFIX}_formal_hc_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_formal_hc_active value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_formal_hc_active_case value = var:{PREFIX}_m257_write_case }}
\t\tset_variable = {{ name = {PREFIX}_m257_conversion_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m257_conversion_settled value = 1 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(257), 3)}
\t\t\tvar:{PREFIX}_m257_conversion_pending = 1
\t\t\tvar:{PREFIX}_m257_write_owner = {{ var:zg361_review_serial < root.var:{PREFIX}_m257_effective_cycle }}
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[257]} days = 90 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2571 }} }}
}}

{PREFIX}_m262_secondment_due_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(262), 3)}
\t\t\tvar:{PREFIX}_m262_review_pending = 1
\t\t\tvar:{PREFIX}_m262_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m262_due_cycle }}
\t\t\tvar:zg361_case_ac_active = 1
\t\t\tvar:zg361_case_ac_state = 5
\t\t\tvar:zg361_case_ac_owner = var:{PREFIX}_m262_write_owner
\t\t\tvar:zg361_case_ac_subject = this
\t\t\tvar:zg361_case_ac_cycle_serial = var:{PREFIX}_m262_write_cycle
\t\t\tvar:zg361_case_ac_case_serial = var:{PREFIX}_m262_write_case
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m262_review_pending value = 0 }}
\t\tvar:{PREFIX}_m262_write_owner = {{ save_scope_as = {PREFIX}_ac_owner }}
\t\tsave_scope_as = {PREFIX}_ac_subject
\t\tsave_scope_value_as = {{ name = {PREFIX}_ac_cycle value = var:{PREFIX}_m262_write_cycle }}
\t\tsave_scope_value_as = {{ name = {PREFIX}_ac_case value = var:{PREFIX}_m262_write_case }}
\t\t{PREFIX}_ac_schedule_stage_05_deadline_effect = yes
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m262_write_owner = {{ is_ai = yes }} }}
\t\t\t{PREFIX}_m263_route_a_effect = {{ TICKET_OWNER = var:{PREFIX}_m262_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m262_write_cycle TICKET_CASE = var:{PREFIX}_m262_write_case }}
\t\t}}
\t\telse = {{ var:{PREFIX}_m262_write_owner = {{ trigger_event = {{ id = {NAMESPACE}.263 }} }} }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(262), 3)}
\t\t\tvar:{PREFIX}_m262_review_pending = 1
\t\t\tvar:{PREFIX}_m262_write_owner = {{ var:zg361_review_serial < root.var:{PREFIX}_m262_due_cycle }}
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[262]} days = 90 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2621 }} }}
}}

{PREFIX}_m263_extension_due_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(263), 3)}
\t\t\tvar:{PREFIX}_m263_extension_pending = 1
\t\t\tvar:{PREFIX}_m263_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m263_extension_due_cycle }}
\t\t\tvar:zg361_case_ac_active = 1
\t\t\tvar:zg361_case_ac_state = 5
\t\t\tvar:zg361_case_ac_case_serial = var:{PREFIX}_m263_write_case
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m263_extension_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m263_return_choice value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m263_terminal_choice value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m263_resolved_choice value = 1 }}
\t\tzg361_case_ac_advance_05_effect = {{ TICKET_OWNER = var:{PREFIX}_m263_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m263_write_cycle TICKET_CASE = var:{PREFIX}_m263_write_case }}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
\t\t\t{PREFIX}_ac_schedule_stage_06_deadline_effect = yes
\t\t\tvar:{PREFIX}_m263_write_owner = {{ save_scope_as = {PREFIX}_ac_owner }}
\t\t\tsave_scope_as = {PREFIX}_ac_subject
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ac_cycle value = var:{PREFIX}_m263_write_cycle }}
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ac_case value = var:{PREFIX}_m263_write_case }}
\t\t\tif = {{ limit = {{ var:{PREFIX}_m263_write_owner = {{ is_ai = no }} }} var:{PREFIX}_m263_write_owner = {{ trigger_event = {{ id = {NAMESPACE}.264 }} }} }}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(263), 3)}
\t\t\tvar:{PREFIX}_m263_extension_pending = 1
\t\t\tvar:{PREFIX}_m263_write_owner = {{ var:zg361_review_serial < root.var:{PREFIX}_m263_extension_due_cycle }}
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[263]} days = 90 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2631 }} }}
}}

{PREFIX}_m269_future_consume_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t\thas_variable = {PREFIX}_ad_external_outcome_ready
\t\t\thas_variable = {PREFIX}_ad_external_outcome_id
\t\t\thas_variable = {PREFIX}_ad_external_outcome_hire_case
\t\t\thas_variable = {PREFIX}_ad_external_outcome_candidate
\t\t\thas_variable = {PREFIX}_ad_external_outcome_quality
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_id
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_hash
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_count
\t\t\thas_variable = {PREFIX}_ad_external_outcome_observed_cycle
\t\t\tvar:{PREFIX}_ad_external_outcome_ready = 1
\t\t\tvar:{PREFIX}_ad_external_outcome_hire_case = var:{PREFIX}_m269_write_case
\t\t\tvar:{PREFIX}_ad_external_outcome_candidate = var:{PREFIX}_m267_candidate_frozen
\t\t\tvar:{PREFIX}_ad_external_outcome_quality >= 1
\t\t\tvar:{PREFIX}_ad_external_outcome_quality <= 4
\t\t\tvar:{PREFIX}_ad_external_outcome_evidence_count >= 1
\t\t\tvar:{PREFIX}_ad_external_outcome_observed_cycle > var:{PREFIX}_m269_write_cycle
\t\t\thas_variable = {PREFIX}_m274_hired
\t\t\tvar:{PREFIX}_m274_hired = 1
\t\t\tvar:{PREFIX}_m274_hire_case = var:{PREFIX}_m269_write_case
\t\t\thas_variable = {PREFIX}_formal_hc_active
\t\t\tvar:{PREFIX}_formal_hc_active = 1
\t\t\tvar:{PREFIX}_formal_hc_active_case = var:{PREFIX}_m269_write_case
\t\t\tvar:{PREFIX}_m269_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m274_probation_due_cycle var:zg361_review_serial >= root.var:{PREFIX}_ad_external_outcome_observed_cycle }}
\t\t\ttrigger_if = {{ limit = {{ has_variable = {PREFIX}_m269_last_outcome_id }} NOT = {{ var:{PREFIX}_m269_last_outcome_id = var:{PREFIX}_ad_external_outcome_id }} }}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ var:{PREFIX}_m269_receipt_choice = 1 }}
\t\t\t\thas_variable = {PREFIX}_ad_external_outcome_dimension_1
\t\t\t\thas_variable = {PREFIX}_ad_external_outcome_dimension_2
\t\t\t\thas_variable = {PREFIX}_ad_external_outcome_dimension_3
\t\t\t\thas_variable = {PREFIX}_ad_external_responsible_interviewer_1
\t\t\t\thas_variable = {PREFIX}_ad_external_responsible_interviewer_2
\t\t\t\thas_variable = {PREFIX}_ad_external_responsible_interviewer_3
\t\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_1
\t\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_2
\t\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_3
\t\t\t\tvar:{PREFIX}_ad_external_responsible_interviewer_1 = var:{PREFIX}_m267_interviewer_1
\t\t\t\tvar:{PREFIX}_ad_external_responsible_interviewer_2 = var:{PREFIX}_m267_interviewer_2
\t\t\t\tvar:{PREFIX}_ad_external_responsible_interviewer_3 = var:{PREFIX}_m267_interviewer_3
\t\t\t\tvar:{PREFIX}_ad_external_attribution_bps_1 >= 0
\t\t\t\tvar:{PREFIX}_ad_external_attribution_bps_2 >= 0
\t\t\t\tvar:{PREFIX}_ad_external_attribution_bps_3 >= 0
\t\t\t\ttrigger_if = {{ limit = {{ var:{PREFIX}_ad_external_outcome_quality = 4 }} var:{PREFIX}_ad_external_attribution_bps_1 = 0 var:{PREFIX}_ad_external_attribution_bps_2 = 0 var:{PREFIX}_ad_external_attribution_bps_3 = 0 has_variable = {PREFIX}_ad_external_outcome_exclusion_reason }}
\t\t\t\ttrigger_else = {{ var:{PREFIX}_ad_external_attribution_bps_1 = {{ value = 10000 subtract = var:{PREFIX}_ad_external_attribution_bps_2 subtract = var:{PREFIX}_ad_external_attribution_bps_3 }} }}
\t\t\t}}
\t\t\ttrigger_else = {{
\t\t\t\tvar:{PREFIX}_m269_receipt_choice = 2
\t\t\t\thas_variable = {PREFIX}_ad_external_final_approver
\t\t\t\thas_variable = {PREFIX}_m272_offer_approver
\t\t\t\tvar:{PREFIX}_ad_external_final_approver = var:{PREFIX}_m272_offer_approver
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_original_votes_preserved value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_last_outcome_id value = var:{PREFIX}_ad_external_outcome_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_hire_case value = var:{PREFIX}_ad_external_outcome_hire_case }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_candidate value = var:{PREFIX}_ad_external_outcome_candidate }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_id value = var:{PREFIX}_ad_external_outcome_evidence_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_hash value = var:{PREFIX}_ad_external_outcome_evidence_hash }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_count value = var:{PREFIX}_ad_external_outcome_evidence_count }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_observed_cycle value = var:{PREFIX}_ad_external_outcome_observed_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_final_quality value = var:{PREFIX}_ad_external_outcome_quality }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_provenance_locked value = 1 }}
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m269_receipt_choice = 1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_1 value = var:{PREFIX}_ad_external_outcome_dimension_1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_2 value = var:{PREFIX}_ad_external_outcome_dimension_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_3 value = var:{PREFIX}_ad_external_outcome_dimension_3 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_1 value = var:{PREFIX}_ad_external_responsible_interviewer_1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_2 value = var:{PREFIX}_ad_external_responsible_interviewer_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_3 value = var:{PREFIX}_ad_external_responsible_interviewer_3 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_1 value = var:{PREFIX}_ad_external_attribution_bps_1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_2 value = var:{PREFIX}_ad_external_attribution_bps_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_3 value = var:{PREFIX}_ad_external_attribution_bps_3 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = {{ value = var:{PREFIX}_ad_external_attribution_bps_1 add = var:{PREFIX}_ad_external_attribution_bps_2 add = var:{PREFIX}_ad_external_attribution_bps_3 }} }}
\t\t\t\tif = {{ limit = {{ var:{PREFIX}_ad_external_outcome_quality = 4 }} set_variable = {{ name = {PREFIX}_m269_exclusion_reason value = var:{PREFIX}_ad_external_outcome_exclusion_reason }} }}
\t\t\t}}
\t\t\telse = {{
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_blamed_final_approver value = var:{PREFIX}_ad_external_final_approver }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_approver_blame_bps value = 10000 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_premature_approver_blame value = 1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 10000 }}
\t\t\t}}
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_ad_external_outcome_quality = 1 has_variable = {PREFIX}_m271_reward_due_after_probation var:{PREFIX}_m271_reward_due_after_probation = 1 has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 has_variable = {PREFIX}_m271_referrer }}
\t\t\t\tchange_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }}
\t\t\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = -5 }}
\t\t\t\tchange_variable = {{ name = {PREFIX}_referral_gold_paid add = 5 }}
\t\t\t\tchange_variable = {{ name = {PREFIX}_gold_paid add = 5 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_payee value = var:{PREFIX}_m271_referrer }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_settled value = 1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }}
\t\t\t\tvar:{PREFIX}_m271_referrer = {{ add_gold = 5 }}
\t\t}}
\t\telse = {{
\t\t\tif = {{ limit = {{ has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 }} change_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_available add = 5 }} set_variable = {{ name = {PREFIX}_m271_reward_refunded value = 1 }} set_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }} var:{PREFIX}_m269_write_owner = {{ add_gold = 5 }} }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_requisition_released value = 0 }} # #269 never owns HC release
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_settled value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_pending value = 0 }} # clear last
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\thas_variable = {PREFIX}_m269_watch_cancelled_by_refusal
\t\t\tvar:{PREFIX}_m269_watch_cancelled_by_refusal = 1
\t\t\tvar:{PREFIX}_m269_outcome_pending = 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_cancel_receipt_consumed value = 1 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = {PREFIX}_ad_external_outcome_ready var:{PREFIX}_ad_external_outcome_ready = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_future_red_code value = 2692 }} # typed invalid outcome; pending remains inspectable
\t\t}}
\t\telse = {{
\t\t\tset_variable = {{ name = {PREFIX}_m269_waiting_for_outcome_evidence value = 1 }}
\t\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[269]} days = 90 }}
\t\t}}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2691 }} }}
}}

{PREFIX}_m275_hold_due_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(275), 3)}
\t\t\tvar:{PREFIX}_m275_hold_pending = 1
\t\t\tOR = {{
\t\t\t\tvar:{PREFIX}_m275_receipt_choice = 1
\t\t\t\tAND = {{
\t\t\t\t\tvar:{PREFIX}_m275_receipt_choice = 2
\t\t\t\t\thas_variable = {PREFIX}_ad_external_m275_remediation_receipt
\t\t\t\t\tvar:{PREFIX}_ad_external_m275_remediation_receipt = 1
\t\t\t\t\thas_variable = {PREFIX}_ad_external_m275_remediated_reason_id
\t\t\t\t\tvar:{PREFIX}_ad_external_m275_remediated_reason_id = var:{PREFIX}_m275_refusal_reason_id
\t\t\t\t}}
\t\t\t}}
\t\t\thas_variable = {PREFIX}_m266_hc_reservation_active
\t\t\tvar:{PREFIX}_m266_hc_reservation_active = 1
\t\t\tvar:{PREFIX}_m266_hc_receipt = var:{PREFIX}_m275_hc_lineage_receipt
\t\t\tvar:{PREFIX}_m275_hc_lineage_receipt = var:{PREFIX}_m275_write_case
\t\t\thas_variable = zg361_ch_hc_reserved
\t\t\tvar:zg361_ch_hc_reserved >= 1
\t\t\tvar:{PREFIX}_m275_write_owner = {{ has_variable = {PREFIX}_ad_hc_flight_pending var:{PREFIX}_ad_hc_flight_pending = 1 var:{PREFIX}_ad_hc_flight_subject = root.var:{PREFIX}_m275_write_subject var:{PREFIX}_ad_hc_flight_cycle = root.var:{PREFIX}_m275_write_cycle var:{PREFIX}_ad_hc_flight_case = root.var:{PREFIX}_m275_write_case }}
\t\t\tvar:{PREFIX}_m275_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m275_hold_due_cycle }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m275_hold_pending value = 0 }}
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m275_receipt_choice = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_candidate_active value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_candidate_active_owner value = var:{PREFIX}_m275_write_owner }}
\t\t\tset_variable = {{ name = {PREFIX}_candidate_active_case value = var:{PREFIX}_m275_write_case }}
\t\t\tset_variable = {{ name = {PREFIX}_candidate_active_character value = var:{PREFIX}_m275_runner_up }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_runner_reopen_pending value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_runner_attempt_opened value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_old_attempt_reopened value = 0 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_hold_released value = 0 }}
\t\t}}
\t\telse = {{
\t\t\tchange_variable = {{ name = zg361_ch_hc_reserved add = -1 }}
\t\t\tchange_variable = {{ name = zg361_ch_hc_available add = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m266_hc_reservation_active value = 0 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_reason_remediated value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_hold_released value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_old_attempt_reopened value = 0 }}
\t\t\tvar:{PREFIX}_m275_write_owner = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 0 }} }}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(275), 3)}
\t\t\tvar:{PREFIX}_m275_hold_pending = 1
\t\t}}
\t\tif = {{ limit = {{ var:{PREFIX}_m275_receipt_choice = 2 var:{PREFIX}_m275_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m275_hold_due_cycle }} }} set_variable = {{ name = {PREFIX}_m275_unremediated_reason_blocks_release value = 1 }} }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[275]} days = 90 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2751 }} }}
}}

{PREFIX}_m355_target_install_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(355), 3)}
\t\t\tvar:{PREFIX}_m355_target_install_pending = 1
\t\t\thas_variable = {PREFIX}_target_gold_reserved
\t\t\tvar:{PREFIX}_target_gold_reserved >= 10
\t\t\tvar:{PREFIX}_m355_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m355_effective_cycle gold >= 10 }}
\t\t}}
\t\tchange_variable = {{ name = {PREFIX}_target_gold_reserved add = -10 }}
\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = -10 }}
\t\tchange_variable = {{ name = {PREFIX}_gold_paid add = 10 }}
\t\tvar:{PREFIX}_m355_write_owner = {{ remove_gold = 10 }}
\t\tadd_gold = 10
\t\tset_variable = {{ name = {PREFIX}_m355_target_install_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m355_target_installed_future_cycle value = var:{PREFIX}_m355_effective_cycle }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(355), 3)}
\t\t\tvar:{PREFIX}_m355_target_install_pending = 1
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_future_red_code value = 3551 }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[355]} days = 90 }}
\t}}
}}

{PREFIX}_m356_cutoff_audit_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(356), 3)}
\t\t\tvar:{PREFIX}_m356_audit_pending = 1
\t\t\tvar:{PREFIX}_m356_write_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= root.var:{PREFIX}_m356_report_cycle }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m356_audit_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m356_audit_settled value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m356_credited_cycle value = var:{PREFIX}_m356_completion_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m356_duplicate_credit_reversed value = 1 }}
\t\tchange_variable = {{ name = {PREFIX}_manager_score add = -5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(356), 3)}
\t\t\tvar:{PREFIX}_m356_audit_pending = 1
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[356]} days = 90 }}
\t}}
}}

{PREFIX}_m361_future_default_install_effect = {{
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(361), 3)}
\t\t\tvar:{PREFIX}_m361_future_install_pending = 1
\t\t\tvar:{PREFIX}_m361_write_owner = {{
\t\t\t\thas_variable = zg361_review_serial
\t\t\t\tvar:zg361_review_serial >= root.var:{PREFIX}_m361_effective_cycle
\t\t\t\thas_variable = {PREFIX}_realm_charter_current_version
\t\t\t\tvar:{PREFIX}_realm_charter_current_version = root.var:{PREFIX}_m361_adopted_version
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m361_future_install_pending value = 0 }}
\t\tvar:{PREFIX}_m361_write_owner = {{
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_effective_cycle value = root.var:{PREFIX}_m361_effective_cycle }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_quota value = root.var:{PREFIX}_m361_future_quota_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_appeal value = root.var:{PREFIX}_m361_future_appeal_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_bonus value = root.var:{PREFIX}_m361_future_bonus_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_hc value = root.var:{PREFIX}_m361_future_hc_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_manager_accountability value = root.var:{PREFIX}_m361_future_manager_accountability_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_future_default_transparency value = root.var:{PREFIX}_m361_future_transparency_default }}
\t\t\tset_variable = {{ name = {PREFIX}_realm_charter_history_append_only value = 1 }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_charter_history_append_only value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_charter_current_case_rewritten value = 0 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(361), 3)}
\t\t\tvar:{PREFIX}_m361_future_install_pending = 1
\t\t\tvar:{PREFIX}_m361_write_owner = {{ var:zg361_review_serial < root.var:{PREFIX}_m361_effective_cycle }}
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[361]} days = 90 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 3611 }} }}
}}"""


def render_nonmanager_na_finalize() -> str:
    """Close a count/baron portfolio without forging manager-only #360/#361."""

    return f"""{PREFIX}_finalize_nonmanager_na_effect = {{
	remove_variable = {PREFIX}_runtime_applied
	if = {{
		limit = {{
			NOT = {{ zg361_is_celestial_liege_trigger = yes }}
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner
				SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial
				CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state
				ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = var:zg361_case_al_owner
				EXPECTED_SUBJECT = this
				EXPECTED_CYCLE = var:zg361_case_al_cycle_serial
				EXPECTED_CASE = var:zg361_case_al_case_serial
				EXPECTED_STATE = 2
			}}
			var:zg361_case_al_owner = {{ zg361_is_celestial_liege_trigger = yes }}
			has_variable = {PREFIX}_operation_total
			has_variable = {PREFIX}_operation_used
			has_variable = {PREFIX}_gold_total
			has_variable = {PREFIX}_gold_available
			has_variable = {PREFIX}_gold_reserved
			has_variable = {PREFIX}_gold_paid
			has_variable = {PREFIX}_hours_total
			has_variable = {PREFIX}_hours_available
			has_variable = {PREFIX}_hours_output
			has_variable = {PREFIX}_hours_on_call
			has_variable = {PREFIX}_hours_meeting
			has_variable = {PREFIX}_hours_leave
			has_variable = {PREFIX}_hours_governance
			has_variable = {PREFIX}_shadow_hc_total
			has_variable = {PREFIX}_shadow_hc_available
			has_variable = {PREFIX}_shadow_hc_active
			has_variable = zg361_ch_hc_authorized
			has_variable = zg361_ch_hc_available
			has_variable = zg361_ch_hc_reserved
			has_variable = zg361_ch_hc_occupied
			has_variable = zg361_ch_hc_frozen
			has_variable = zg361_ch_hc_reclaimed
			var:{PREFIX}_operation_total = 40
			var:{PREFIX}_operation_used = {NONMANAGER_OPERATION_COUNT}
		}}
		set_variable = {{ name = {PREFIX}_portfolio_closed value = 0 }}
		set_variable = {{ name = {PREFIX}_portfolio_status value = 4 }}
		set_variable = {{ name = {PREFIX}_final_operation_check value = var:{PREFIX}_operation_used }}
		set_variable = {{ name = {PREFIX}_final_gold_check value = var:{PREFIX}_gold_available }}
		change_variable = {{ name = {PREFIX}_final_gold_check add = var:{PREFIX}_gold_reserved }}
		change_variable = {{ name = {PREFIX}_final_gold_check add = var:{PREFIX}_gold_paid }}
		set_variable = {{ name = {PREFIX}_final_hours_check value = var:{PREFIX}_hours_available }}
		change_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_output }}
		change_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_on_call }}
		change_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_meeting }}
		change_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_leave }}
		change_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_governance }}
		set_variable = {{ name = {PREFIX}_final_shadow_hc_check value = var:{PREFIX}_shadow_hc_available }}
		change_variable = {{ name = {PREFIX}_final_shadow_hc_check add = var:{PREFIX}_shadow_hc_active }}
		set_variable = {{ name = {PREFIX}_final_formal_hc_check value = var:zg361_ch_hc_available }}
		change_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_reserved }}
		change_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_occupied }}
		change_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_frozen }}
		change_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_reclaimed }}
		set_variable = {{ name = {PREFIX}_final_conservation_ok value = 0 }}
		if = {{
			limit = {{
				var:{PREFIX}_final_operation_check = {NONMANAGER_OPERATION_COUNT}
				var:{PREFIX}_gold_available >= 0
				var:{PREFIX}_gold_reserved >= 0
				var:{PREFIX}_gold_paid >= 0
				var:{PREFIX}_final_gold_check = var:{PREFIX}_gold_total
				var:{PREFIX}_hours_available >= 0
				var:{PREFIX}_hours_output >= 0
				var:{PREFIX}_hours_on_call >= 0
				var:{PREFIX}_hours_meeting >= 0
				var:{PREFIX}_hours_leave >= 0
				var:{PREFIX}_hours_governance >= 0
				var:{PREFIX}_final_hours_check = var:{PREFIX}_hours_total
				var:{PREFIX}_shadow_hc_available >= 0
				var:{PREFIX}_shadow_hc_active >= 0
				var:{PREFIX}_final_shadow_hc_check = var:{PREFIX}_shadow_hc_total
				var:zg361_ch_hc_available >= 0
				var:zg361_ch_hc_reserved >= 0
				var:zg361_ch_hc_occupied >= 0
				var:zg361_ch_hc_frozen >= 0
				var:zg361_ch_hc_reclaimed >= 0
				var:{PREFIX}_final_formal_hc_check = var:zg361_ch_hc_authorized
			}}
			zg361_case_kernel_transition_effect = {{
				OWNER_VAR = zg361_case_al_owner
				SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial
				CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state
				REVISION_VAR = zg361_case_al_revision
				ACTIVE_VAR = zg361_case_al_active
				TIMELINE_VAR = zg361_case_al_timeline_serial
				FEEDBACK_VAR = zg361_case_al_feedback_revision
				LAST_HOOK_VAR = zg361_case_al_last_hook
				TICKET_OWNER = var:zg361_case_al_owner
				TICKET_SUBJECT = this
				TICKET_CYCLE = var:zg361_case_al_cycle_serial
				TICKET_CASE = var:zg361_case_al_case_serial
				TICKET_STATE = 2
				NEXT_STATE = 7
				HOOK_ID = 9361
				CLOSE_CASE = yes
			}}
			if = {{
				limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 var:zg361_case_al_active = 0 var:zg361_case_al_state = 7 }}
				set_variable = {{ name = {PREFIX}_final_conservation_ok value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_na value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_reason value = 360361 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_owned_operations value = {NONMANAGER_OPERATION_COUNT} }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_skipped_manager_only value = 2 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_success value = 0 }}
				set_variable = {{ name = {PREFIX}_awaiting_al_357_359 value = 0 }}
				set_variable = {{ name = {PREFIX}_portfolio_closed value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_status value = 7 }}
				set_variable = {{ name = {PREFIX}_runtime_applied value = 1 }}
				set_variable = {{ name = {PREFIX}_runtime_status value = 1 }}
				debug_log = "ZG361WE: count/baron portfolio closed N/A before manager-only #360/#361"
			}}
			else = {{
				set_variable = {{ name = {PREFIX}_last_red_code value = 9098 }}
				set_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
			}}
		}}
		else = {{
			set_variable = {{ name = {PREFIX}_last_red_code value = 9098 }}
			set_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
			debug_log = "ZG361WE RED: non-manager N/A conservation failed; AL remains active"
		}}
	}}
	else_if = {{
		limit = {{ has_variable = {PREFIX}_portfolio_terminal_na var:{PREFIX}_portfolio_terminal_na = 1 var:{PREFIX}_portfolio_closed = 1 var:{PREFIX}_portfolio_status = 7 var:zg361_case_al_active = 0 }}
		set_variable = {{ name = {PREFIX}_runtime_status value = 2 }} # idempotent N/A no-op
	}}
	else = {{
		set_variable = {{ name = {PREFIX}_last_red_code value = 9098 }}
		set_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
	}}
}}"""


def render_finalize() -> str:
    return f"""{PREFIX}_finalize_portfolio_effect = {{
\tset_variable = {{ name = {PREFIX}_portfolio_closed value = 0 }}
\tset_variable = {{ name = {PREFIX}_portfolio_status value = 4 }}
\tset_variable = {{ name = {PREFIX}_final_operation_check value = var:{PREFIX}_operation_used }}
\tset_variable = {{ name = {PREFIX}_final_gold_check value = var:{PREFIX}_gold_available }}
\tchange_variable = {{ name = {PREFIX}_final_gold_check add = var:{PREFIX}_gold_reserved }}
\tchange_variable = {{ name = {PREFIX}_final_gold_check add = var:{PREFIX}_gold_paid }}
\tset_variable = {{ name = {PREFIX}_final_hours_check value = var:{PREFIX}_hours_available }}
\tchange_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_output }}
\tchange_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_on_call }}
\tchange_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_meeting }}
\tchange_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_leave }}
\tchange_variable = {{ name = {PREFIX}_final_hours_check add = var:{PREFIX}_hours_governance }}
\tset_variable = {{ name = {PREFIX}_final_shadow_hc_check value = var:{PREFIX}_shadow_hc_available }}
\tchange_variable = {{ name = {PREFIX}_final_shadow_hc_check add = var:{PREFIX}_shadow_hc_active }}
\tset_variable = {{ name = {PREFIX}_final_formal_hc_check value = var:zg361_ch_hc_available }}
\tchange_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_reserved }}
\tchange_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_occupied }}
\tchange_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_frozen }}
\tchange_variable = {{ name = {PREFIX}_final_formal_hc_check add = var:zg361_ch_hc_reclaimed }}
\tset_variable = {{ name = {PREFIX}_final_conservation_ok value = 0 }}
\tif = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_operation_used >= 0
\t\t\tvar:{PREFIX}_operation_used <= var:{PREFIX}_operation_total
\t\t\tvar:{PREFIX}_gold_available >= 0
\t\t\tvar:{PREFIX}_gold_reserved >= 0
\t\t\tvar:{PREFIX}_gold_paid >= 0
\t\t\tvar:{PREFIX}_hours_available >= 0
\t\t\tvar:{PREFIX}_hours_output >= 0
\t\t\tvar:{PREFIX}_hours_on_call >= 0
\t\t\tvar:{PREFIX}_hours_meeting >= 0
\t\t\tvar:{PREFIX}_hours_leave >= 0
\t\t\tvar:{PREFIX}_hours_governance >= 0
\t\t\tvar:{PREFIX}_shadow_hc_available >= 0
\t\t\tvar:{PREFIX}_shadow_hc_active >= 0
\t\t\tvar:zg361_ch_hc_available >= 0
\t\t\tvar:zg361_ch_hc_reserved >= 0
\t\t\tvar:zg361_ch_hc_occupied >= 0
\t\t\tvar:zg361_ch_hc_frozen >= 0
\t\t\tvar:zg361_ch_hc_reclaimed >= 0
\t\t\tvar:{PREFIX}_final_operation_check = 40
\t\t\tvar:{PREFIX}_final_gold_check = var:{PREFIX}_gold_total
\t\t\tvar:{PREFIX}_final_hours_check = var:{PREFIX}_hours_total
\t\t\tvar:{PREFIX}_final_shadow_hc_check = var:{PREFIX}_shadow_hc_total
\t\t\tvar:{PREFIX}_final_formal_hc_check = var:zg361_ch_hc_authorized
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_final_conservation_ok value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_portfolio_closed value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_portfolio_status value = 6 }}
\t\tdebug_log = "ZG361WE: workforce/endgame portfolio closed static runtime"
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_last_red_code value = 9099 }}
\t\tset_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
\t\tdebug_log = "ZG361WE RED: final conservation failed; portfolio remains open"
\t}}
}}"""


def render_effects() -> bytes:
    validate_specs()
    sections = [
        "# ZhongGuo 361 workforce/endgame: AB/AC/AD plus AL 355/356/360/361.\n"
        f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n"
        f"# Public manager ABI: {PREFIX}_open_portfolio_effect = {{ SUBJECT = <direct vassal> }}.\n"
        "# Stable status: 1=applied, 2=idempotent, 3=stale, 4=typed RED, 5=external dependency, 6=complete, 7=honest N/A terminal.",
        render_portfolio_initialize(),
        render_portfolio_entry(),
        render_future_consumers(),
        render_nonmanager_na_finalize(),
        render_finalize(),
    ]
    for domain in ("ab", "ac", "ad", "al"):
        sections += [render_domain_init(domain), render_subject_read(domain), render_ai(domain), render_launch(domain)]
        for state in sorted(set(STAGE_LAST[domain].values())):
            sections += [render_schedule(domain, state), render_timeout(domain, state)]
    for spec in MECHANISMS:
        sections.append(render_consumer(spec))
        for choice in (1, 2, 3):
            sections.append(render_route_effect(spec, choice))
    return generated("\n\n".join(sections))


def event_guard(spec: Mechanism) -> str:
    d = spec.domain
    top_gate = ""
    if spec.mid == 361:
        top_gate = """
trigger_if = {
\tlimit = { exists = liege }
\tNOT = { liege = { zg361_is_celestial_liege_trigger = yes } }
}
trigger_else = { always = yes }"""
    dependency = ""
    if spec.mid in (360, 361):
        dependency = f"""
scope:{PREFIX}_{d}_subject = {{
\thas_variable = {PREFIX}_al_external_stage_receipts_verified
\tvar:{PREFIX}_al_external_stage_receipts_verified = 1
}}"""
    completed = ""
    if spec.mid == 361:
        completed = f"""
scope:{PREFIX}_{d}_subject = {{
\thas_variable = {PREFIX}_al_external_completed_cycle_receipt_count
\tvar:{PREFIX}_al_external_completed_cycle_receipt_count >= 3
\thas_variable = {PREFIX}_al_external_completed_cycle_max
\tvar:{PREFIX}_al_external_completed_cycle_max <= scope:{PREFIX}_{d}_cycle
\thas_variable = {PREFIX}_al_external_long_report_id
}}"""
    return f"""is_ai = no
exists = scope:{PREFIX}_{d}_owner
exists = scope:{PREFIX}_{d}_subject
exists = scope:{PREFIX}_{d}_cycle
exists = scope:{PREFIX}_{d}_case
this = scope:{PREFIX}_{d}_owner
zg361_is_celestial_liege_trigger = yes{top_gate}{dependency}{completed}
scope:{PREFIX}_{d}_subject = {{
\tzg361_case_kernel_full_guard_trigger = {{
\t\tOWNER_VAR = zg361_case_{d}_owner
\t\tSUBJECT_VAR = zg361_case_{d}_subject
\t\tCYCLE_VAR = zg361_case_{d}_cycle_serial
\t\tCASE_VAR = zg361_case_{d}_case_serial
\t\tSTATE_VAR = zg361_case_{d}_state
\t\tACTIVE_VAR = zg361_case_{d}_active
\t\tEXPECTED_OWNER = scope:{PREFIX}_{d}_owner
\t\tEXPECTED_SUBJECT = scope:{PREFIX}_{d}_subject
\t\tEXPECTED_CYCLE = scope:{PREFIX}_{d}_cycle
\t\tEXPECTED_CASE = scope:{PREFIX}_{d}_case
\t\tEXPECTED_STATE = {spec.state}
\t}}
}}"""


def event_next_mid(spec: Mechanism) -> int | None:
    order = DOMAIN_ORDER[spec.domain]
    index = order.index(spec.mid)
    if index + 1 >= len(order):
        return None
    candidate = by_id()[order[index + 1]]
    if spec.domain == "al" and candidate.state > spec.state + 1:
        return None
    return candidate.mid


def render_option(spec: Mechanism, choice: int) -> str:
    d, mid = spec.domain, spec.mid
    letter = "abc"[choice - 1]
    next_mid = event_next_mid(spec)
    next_event = ""
    # #262 opens a due-cycle review; it must not immediately ask #263 in the
    # same cycle.  The hidden due consumer queues that player event later.
    if next_mid is not None and not (mid == 262 and choice in (1, 2)):
        next_state = by_id()[next_mid].state
        next_event = f"""
\tif = {{
\t\tlimit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_{d}_state = {next_state} }} }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{next_mid} }}
\t}}"""
    return f"""option = {{
\tname = {NAMESPACE}.{mid}.{letter}
\tscope:{PREFIX}_{d}_subject = {{
\t\t{PREFIX}_m{mid}_route_{letter}_effect = {{
\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case
\t\t}}
\t}}{next_event}
}}"""


def render_deadline_event(domain: str, state: int) -> str:
    dl = deadline_prefix(domain, state)
    relay_owner = f"{PREFIX}_{domain}_s{state:02d}_relay_owner"
    relay_subject = f"{PREFIX}_{domain}_s{state:02d}_relay_subject"
    relay_cycle = f"{PREFIX}_{domain}_s{state:02d}_relay_cycle"
    relay_case = f"{PREFIX}_{domain}_s{state:02d}_relay_case"
    relay_state = f"{PREFIX}_{domain}_s{state:02d}_relay_state"
    return f"""{NAMESPACE}.{deadline_event_id(domain, state)} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tzg361_case_kernel_expire_deadline_effect = {{
\t\t\tOWNER_VAR = zg361_case_{domain}_owner
\t\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\t\tCYCLE_VAR = zg361_case_{domain}_cycle_serial
\t\t\tCASE_VAR = zg361_case_{domain}_case_serial
\t\t\tSTATE_VAR = zg361_case_{domain}_state
\t\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\t\tREVISION_VAR = zg361_case_{domain}_revision
\t\t\tTIMELINE_VAR = zg361_case_{domain}_timeline_serial
\t\t\tFEEDBACK_VAR = zg361_case_{domain}_feedback_revision
\t\t\tDEADLINE_OWNER_VAR = {dl}_owner
\t\t\tDEADLINE_SUBJECT_VAR = {dl}_subject
\t\t\tDEADLINE_CYCLE_VAR = {dl}_cycle
\t\t\tDEADLINE_CASE_VAR = {dl}_case
\t\t\tDEADLINE_STATE_VAR = {dl}_state
\t\t\tDEADLINE_PENDING_VAR = {dl}_pending
\t\t\tDEADLINE_EXPIRED_VAR = {dl}_expired
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
\t\t\tvar:{dl}_owner = {{ save_scope_as = {relay_owner} }}
\t\t\tsave_scope_as = {relay_subject}
\t\t\tsave_scope_value_as = {{ name = {relay_cycle} value = var:{dl}_cycle }}
\t\t\tsave_scope_value_as = {{ name = {relay_case} value = var:{dl}_case }}
\t\t\tsave_scope_value_as = {{ name = {relay_state} value = var:{dl}_state }}
\t\t\tvar:{dl}_owner = {{ trigger_event = {{ id = {NAMESPACE}.{deadline_relay_event_id(domain, state)} }} }}
\t\t}}
\t}}
}}

{NAMESPACE}.{deadline_relay_event_id(domain, state)} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\texists = scope:{relay_owner}
\t\t\t\texists = scope:{relay_subject}
\t\t\t\texists = scope:{relay_cycle}
\t\t\t\texists = scope:{relay_case}
\t\t\t\texists = scope:{relay_state}
\t\t\t\tthis = scope:{relay_owner}
\t\t\t\tscope:{relay_subject} = {{
\t\t\t\t\tzg361_case_kernel_full_guard_trigger = {{
\t\t\t\t\t\tOWNER_VAR = zg361_case_{domain}_owner
\t\t\t\t\t\tSUBJECT_VAR = zg361_case_{domain}_subject
\t\t\t\t\t\tCYCLE_VAR = zg361_case_{domain}_cycle_serial
\t\t\t\t\t\tCASE_VAR = zg361_case_{domain}_case_serial
\t\t\t\t\t\tSTATE_VAR = zg361_case_{domain}_state
\t\t\t\t\t\tACTIVE_VAR = zg361_case_{domain}_active
\t\t\t\t\t\tEXPECTED_OWNER = root
\t\t\t\t\t\tEXPECTED_SUBJECT = this
\t\t\t\t\t\tEXPECTED_CYCLE = scope:{relay_cycle}
\t\t\t\t\t\tEXPECTED_CASE = scope:{relay_case}
\t\t\t\t\t\tEXPECTED_STATE = scope:{relay_state}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}
\t\t\tscope:{relay_subject} = {{ {PREFIX}_{domain}_timeout_stage_{state:02d}_effect = yes }}
\t\t}}
\t\telse = {{ debug_log = "ZG361WE: stale {domain.upper()} stage {state} owner-root relay ignored" }}
\t}}
}}"""


def render_future_event(mid: int) -> str:
    effect = {
        257: f"{PREFIX}_m257_future_consume_effect",
        262: f"{PREFIX}_m262_secondment_due_effect",
        263: f"{PREFIX}_m263_extension_due_effect",
        269: f"{PREFIX}_m269_future_consume_effect",
        275: f"{PREFIX}_m275_hold_due_effect",
        355: f"{PREFIX}_m355_target_install_effect",
        356: f"{PREFIX}_m356_cutoff_audit_effect",
        361: f"{PREFIX}_m361_future_default_install_effect",
    }[mid]
    return f"""{NAMESPACE}.{FUTURE_EVENT[mid]} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {effect} = yes }}
}}"""


def render_events() -> bytes:
    validate_specs()
    sections = [f"namespace = {NAMESPACE}"]
    for spec in MECHANISMS:
        options = "\n".join(render_option(spec, choice) for choice in (1, 2, 3))
        sections.append(f"""# #{spec.mid:03d} — {spec.title_en}
{NAMESPACE}.{spec.mid} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = {NAMESPACE}.{spec.mid}.t
\tdesc = {NAMESPACE}.{spec.mid}.desc
\ttrigger = {{
{indent(event_guard(spec), 2)}
\t}}
{indent(options)}
}}""")
    for domain in ("ab", "ac", "ad", "al"):
        for state in sorted(set(STAGE_LAST[domain].values())):
            sections.append(render_deadline_event(domain, state))
    for mid in FUTURE_EVENT:
        sections.append(render_future_event(mid))
    return generated("\n\n".join(sections))


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    validate_specs()
    chinese = language == "simp_chinese"
    rows: list[str] = []
    for spec in MECHANISMS:
        title = spec.title_cn if chinese else spec.title_en
        desc = spec.desc_cn if chinese else spec.desc_en
        routes = spec.routes_cn if chinese else spec.routes_en
        rows += [
            f' {NAMESPACE}.{spec.mid}.t:0 "{esc(title)}"',
            f' {NAMESPACE}.{spec.mid}.desc:0 "{esc(desc)}"',
            *(f' {NAMESPACE}.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", routes)),
        ]
    return localized(f"l_{language}:\n" + "\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_workforce_endgame_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_workforce_endgame_runtime_events.txt": render_events(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_workforce_endgame_l_{language}.yml"
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
            print("RED: stale workforce/endgame generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print(f"GREEN: {len(rendered)} workforce/endgame generated files are current ({READINESS})")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} workforce/endgame runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
