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
    WORKFORCE_EXECUTION_ORDER,
    WORKFORCE_EXECUTION_STAGE,
)


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_workforce_endgame_runtime.py\n"
READINESS = "ck3-script-static-ready-not-live"
LEGACY_EFFECT_FILENAME = "zg361_workforce_endgame_runtime_effects.txt"
LEGACY_EFFECT_PATH = MOD_ROOT / "common" / "scripted_effects" / LEGACY_EFFECT_FILENAME
EFFECT_SHARD_GLOB = "zg361_workforce_endgame_*_effects.txt"
HISTORICAL_EFFECT_BYTES = 4_636_271
HISTORICAL_EFFECT_SHA256 = "926453FE4B3621B5381743D61F5D03AC29C1D498181702E05A9532739D334D8A"
HISTORICAL_EFFECT_COUNT = 324
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# A future shard above the hard limit is invalid unless this map contains both
# a concrete purpose-cohesion reason and a reference to CK3 live evidence.
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}
RETIRED_EFFECT_FILENAMES = (
    "zg361_workforce_endgame_024c_manager_terminal_cleanup_effects.txt",
    "zg361_workforce_endgame_015a_m269_attribution_settlement_effects.txt",
    "zg361_workforce_endgame_023b_al_m360_m361_due_debt_effects.txt",
    "zg361_workforce_endgame_025_ab_control_effects.txt",
    "zg361_workforce_endgame_028_ac_control_effects.txt",
    "zg361_workforce_endgame_031_ad_control_effects.txt",
    "zg361_workforce_endgame_035b_al_stage04_05_deadline_effects.txt",
    "zg361_workforce_endgame_048_ac_m264_m265_effects.txt",
    "zg361_workforce_endgame_050_ad_m271_m267_effects.txt",
    "zg361_workforce_endgame_053_ad_m274_m275_effects.txt",
    "zg361_workforce_endgame_046_ac_m257_m262_effects.txt",
    "zg361_workforce_endgame_061_al_m361_effects.txt",
)
RETIRED_EFFECT_PATHS = tuple(
    MOD_ROOT / "common" / "scripted_effects" / filename
    for filename in RETIRED_EFFECT_FILENAMES
)
LEGACY_EVENT_FILENAME = "zg361_workforce_endgame_runtime_events.txt"
LEGACY_EVENT_PATH = MOD_ROOT / "events" / LEGACY_EVENT_FILENAME
EVENT_SHARD_GLOB = "zg361_workforce_endgame_event_*_events.txt"
HISTORICAL_EVENT_BYTES = 168_729
HISTORICAL_EVENT_SHA256 = "637F65CC72C176E6E19BE982F41B203DC326047939B79A80E5E43D3A9D361EF7"
HISTORICAL_EVENT_COUNT = 149
EVENT_TARGET_MAX = 10
EVENT_HARD_MAX = 20
# A future shard above the hard limit is invalid unless this map contains both
# a concrete purpose-cohesion reason and a reference to CK3 live evidence.
EVENT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}
RETIRED_EVENT_FILENAMES = (
    "zg361_workforce_endgame_event_011_al_collective_charter_events.txt",
    "zg361_workforce_endgame_event_021_al_deadline_stage04_05_events.txt",
    "zg361_workforce_endgame_event_027_m269_attribution_events.txt",
    "zg361_workforce_endgame_event_035_al_collective_charter_debt_events.txt",
)
RETIRED_EVENT_PATHS = tuple(
    MOD_ROOT / "events" / filename for filename in RETIRED_EVENT_FILENAMES
)
PREFIX = "zg361_we"
NAMESPACE = "zg361we"
APPOINTMENT_WRAPPER = "zg361_workforce_appointment_fact_m274_appoint_and_consume_effect"
APPOINTMENT_STATUS_VAR = "zg361_workforce_appointment_fact_status"
PROBATION_ARM_EFFECT = "zg361_workforce_probation_fact_arm_hire_effect"
PROBATION_STATUS_VAR = "zg361_workforce_probation_fact_adapter_status"
PROBATION_FINALIZE_EFFECT = "zg361_workforce_probation_fact_finalize_consumption_receipt_effect"
ATTRIBUTION_BEGIN_EFFECT = "zg361_workforce_attribution_fact_begin_signature_effect"
ATTRIBUTION_PUBLISH_EFFECT = "zg361_workforce_attribution_fact_publish_result_effect"
ATTRIBUTION_CANCEL_EFFECT = "zg361_workforce_attribution_fact_cancel_from_m269_debt_effect"
ATTRIBUTION_STATUS_VAR = "zg361_workforce_attribution_fact_status"
CAREER_SLOT_ARM_EFFECT = "zg361_workforce_exit_fact_arm_from_m274_effect"
REHIRE_CAPTURE_GROWTH_EFFECT = "zg361_workforce_rehire_fact_capture_growth_effect"
REHIRE_PREPARE_EFFECT = "zg361_workforce_rehire_fact_prepare_m276_effect"
REHIRE_FINALIZE_EFFECT = "zg361_workforce_rehire_fact_finalize_m276_effect"
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
    object_type: str
    consumer_key: str
    resource_books: tuple[str, ...]
    deadline_cycles: int
    title_en: str
    title_cn: str
    desc_en: str
    desc_cn: str
    routes_en: tuple[str, str, str]
    routes_cn: tuple[str, str, str]


@dataclass(frozen=True)
class EffectGroup:
    filename: str
    purpose: str
    effect_names: tuple[str, ...]


@dataclass(frozen=True)
class EventGroup:
    filename: str
    purpose: str
    event_ids: tuple[int, ...]


DOMAIN_ORDER = {domain.lower(): order for domain, order in WORKFORCE_EXECUTION_ORDER.items()}
DOMAIN_EXPECTED = {
    "ab": {242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253},
    "ac": {254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265},
    "ad": {266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277},
    "al": {355, 356, 360, 361},
}
STATE_BY_ID = dict(WORKFORCE_EXECUTION_STAGE)
STAGE_LAST = {
    "ab": {243: 1, 245: 2, 247: 3, 249: 4, 251: 5, 253: 6},
    "ac": {255: 1, 261: 2, 259: 3, 262: 4, 263: 5, 265: 6},
    "ad": {267: 1, 270: 2, 272: 3, 275: 4, 269: 5, 277: 6},
    # AL 2/3 belong to mechanisms 357-359.  This slice never forges them.
    "al": {356: 1, 360: 4, 361: 5},
}
# A route may consume only business objects frozen by the same five-tuple.
# This is deliberately narrower than "an earlier variable happens to exist":
# old-cycle projections and route-C debt cannot satisfy a current business
# prerequisite.  The order is the executable model's real dependency order.
CURRENT_OBJECT_DEPENDENCIES = {
    246: (245,),
    250: (249,),
    251: (249, 250),
    255: (254,),
    260: (254,),
    261: (254, 260),
    256: (254, 260, 261),
    258: (254,),
    259: (254, 260, 261),
    257: (254, 256),
    263: (262,),
    # #264 is now a product-owned, subject-response handoff flow.  Its three
    # milestones are anchored to real current-case objects: supplier quality
    # (#256), executor-chain documentation (#261), and the completed
    # secondment/return chain (#262/#263).  No caller-supplied artifact hash is
    # accepted.
    264: (254, 256, 261, 262, 263),
    265: (259, 261, 264),
    273: (266,),
    271: (266, 273),
    267: (266, 273, 271),
    268: (267,),
    270: (266, 267),
    272: (266, 267, 268, 270, 273),
    274: (266, 272, 273),
    # #274 hire and #275 refusal are mutually exclusive outcomes of the same
    # offer.  #275 still records a current no-hold decision after a hire.
    275: (266, 272, 273, 274),
    269: (267, 268, 274, 275),
    277: (274, 269),
    361: (360,),
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
REMEDIATION_OPEN_EVENT = 5276
REMEDIATION_CONSUME_EVENT = 5277
# CK3 event namespace suffixes are bounded to 0..9999.  The former 52739..
# 52750 spellings were rejected by the loader (and could surface as misleading
# duplicate-registration noise), so keep this product-owned relay range both
# explicit and below the engine ceiling.
M274_NATIVE_ACK_EVENT = 5370
M274_PROBATION_AUDIT_EVENT = 5371
M274_SIGNATURE_AUDIT_EVENT = 5372
M274_DISPOSITION_AUDIT_EVENT = 5373
M269_DEBT_CANCEL_EVENT = 5374
M269_DEBT_CANCEL_ACK_EVENT = 5375
M269_DEBT_ADVANCE_AUDIT_EVENT = 5376
M269_POSTSETTLEMENT_EVENT = 5377
M269_RESULT_PUBLISH_EVENT = 5378
M276_PREPARE_AUDIT_EVENT = 5379
M276_FINALIZE_EVENT = 5380
M276_FINALIZE_AUDIT_EVENT = 5381
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
DEBT_EVENT = {mid: 6000 + mid for mid in EXPECTED_MECHANISM_IDS}
MAX_COLLECTIVE_OUTCOMES = 6
M360_CENTRAL_GLOBAL_FIELDS = (
    "status", "reason", "owner", "subject", "p2c_cycle", "p2c_case",
    "al_cycle", "al_case", "cohort_count", "total_quota",
)
M360_CENTRAL_COHORT_FIELDS = (
    "manager", "b1_cycle", "b1_case", "b1_source_id", "b1_source_hash",
    "quota", "mg_cycle", "mg_case", "mg_snapshot_source_serial",
    "mg_snapshot_revision",
)
M360_B1_SLOT_FIELDS = (
    "character", "processing_order", "m357_receipt_id", "m357_receipt_hash",
    "b1_owner", "b1_subject", "b1_cycle", "b1_case", "result_owner",
    "result_subject", "result_cycle", "result_case",
)
M360_MG_RECEIPT_FIELDS = (
    "status", "id", "hash", "owner", "al_subject", "al_cycle", "al_case",
    "settlement_id", "settlement_hash", "cohort_id", "ordinal", "manager",
    "mg_cycle", "mg_case", "mg_snapshot_source_serial",
    "mg_snapshot_revision", "b1_cycle", "b1_case", "b1_source_id",
    "b1_source_hash", "route", "quota", "exception_count", "cost",
    "score_before", "score_after", "score_delta",
)
HANDOFF_EVENT = {1: 5264, 2: 5265, 3: 5266}
HANDOFF_RELAY_EVENT = {2: 5267, 3: 5268}
NONMANAGER_NA_IDS = frozenset({360, 361})
NONMANAGER_OPERATION_COUNT = len(EXPECTED_MECHANISM_IDS - NONMANAGER_NA_IDS)
CHARTER_HISTORY_ACCRUAL_OPERATION_COUNT = len(EXPECTED_MECHANISM_IDS) - 1
B2_PIP_SOURCE_FIELDS = (
    "pending", "consumed", "owner", "subject", "cycle", "case", "state",
    "case_id", "case_hash", "closure_receipt_id", "closure_receipt_hash",
)
AD_SOURCE_COMMON_FIELDS = (
    "pending", "consumed", "retired", "owner", "subject", "cycle", "case",
    "state", "id", "hash",
)
AD_REFERRAL_SOURCE_FIELDS = AD_SOURCE_COMMON_FIELDS + (
    "disposition", "referral_id", "referrer", "relationship",
    "evidence_receipt",
)
AD_PANEL_SOURCE_FIELDS = AD_SOURCE_COMMON_FIELDS + (
    "disposition", "referrer", "referrer_vote_policy", "interviewer_1",
    "interviewer_2", "interviewer_3", "vote_1", "vote_2", "vote_3",
    "vote_evidence_1", "vote_evidence_2", "vote_evidence_3",
    "runner_up_present",
)
AD_OFFER_SOURCE_FIELDS = AD_SOURCE_COMMON_FIELDS + (
    "response", "response_receipt",
)
AD_SOURCE_REPLACED_EXTERNAL_ALIASES = frozenset({
    "zg361_we_ad_external_referral_id",
    "zg361_we_ad_external_referrer",
    "zg361_we_ad_external_referral_relationship",
    "zg361_we_ad_external_referral_evidence_receipt",
    "zg361_we_ad_external_interviewer_1",
    "zg361_we_ad_external_interviewer_2",
    "zg361_we_ad_external_interviewer_3",
    "zg361_we_ad_external_vote_1",
    "zg361_we_ad_external_vote_2",
    "zg361_we_ad_external_vote_3",
    "zg361_we_ad_external_vote_evidence_1",
    "zg361_we_ad_external_vote_evidence_2",
    "zg361_we_ad_external_vote_evidence_3",
    "zg361_we_ad_external_runner_up",
    "zg361_we_ad_external_runner_up_evidence",
    "zg361_we_ad_external_refusal_reason_id",
})
# These names came from the frozen AD80 loader artifact, but they are not
# independent external facts.  They are either current-case identity aliases,
# facts already committed by this product, or the redundant projection of the
# B2 one-slot PIP source.  Keep the exact set executable so tests can prove we
# did not retire a genuine provider field by accident.
RETIRED_AD_EXTERNAL_ALIASES = frozenset({
    "zg361_we_ad_external_candidate",
    "zg361_we_ad_external_final_approver",
    "zg361_we_ad_external_outcome_candidate",
    "zg361_we_ad_external_outcome_hire_case",
    "zg361_we_ad_external_referral_present",
    "zg361_we_ad_external_referral_reward",
    "zg361_we_ad_external_referrer_voted",
    "zg361_we_ad_external_responsible_interviewer_1",
    "zg361_we_ad_external_responsible_interviewer_2",
    "zg361_we_ad_external_responsible_interviewer_3",
    "zg361_we_ad_external_appointed_character",
    "zg361_we_ad_external_appointment_case",
    "zg361_we_ad_external_appointment_cycle",
    "zg361_we_ad_external_appointment_owner",
    "zg361_we_ad_external_appointment_state",
    "zg361_we_ad_external_appointment_subject",
    "zg361_we_ad_external_outcome_ready",
    "zg361_we_ad_external_pip_case",
    "zg361_we_ad_external_pip_cycle",
    "zg361_we_ad_external_pip_owner",
    "zg361_we_ad_external_pip_state",
    "zg361_we_ad_external_pip_subject",
    "zg361_we_ad_external_rehire_candidate",
    "zg361_we_ad_external_rehire_case",
    "zg361_we_ad_external_rehire_cycle",
    "zg361_we_ad_external_rehire_owner",
    "zg361_we_ad_external_rehire_state",
    "zg361_we_ad_external_rehire_subject",
    "zg361_we_ad_external_pip_case_hash",
    "zg361_we_ad_external_pip_case_id",
    "zg361_we_ad_external_pip_closure_receipt_hash",
    "zg361_we_ad_external_pip_closure_receipt_id",
    "zg361_we_ad_external_attribution_bps_1",
    "zg361_we_ad_external_attribution_bps_2",
    "zg361_we_ad_external_attribution_bps_3",
    "zg361_we_ad_external_outcome_dimension_1",
    "zg361_we_ad_external_outcome_dimension_2",
    "zg361_we_ad_external_outcome_dimension_3",
    "zg361_we_ad_external_outcome_evidence_count",
    "zg361_we_ad_external_outcome_evidence_hash",
    "zg361_we_ad_external_outcome_evidence_id",
    "zg361_we_ad_external_outcome_exclusion_reason",
    "zg361_we_ad_external_outcome_id",
    "zg361_we_ad_external_outcome_observed_cycle",
    "zg361_we_ad_external_outcome_quality",
    "zg361_we_ad_external_exit_hc_lineage_case",
    "zg361_we_ad_external_exit_position_type_id",
})


def _load_mechanisms() -> tuple[Mechanism, ...]:
    choices_path = MOD_ROOT / "tools" / "mechanism_choices" / "choices_241_361.json"
    choices = json.loads(choices_path.read_text(encoding="utf-8"))
    rows: list[Mechanism] = []
    for domain in ("ab", "ac", "ad", "al"):
        for mid in DOMAIN_ORDER[domain]:
            binding = MECHANISM_BINDINGS[mid]
            choice = choices[str(mid)]
            state = binding.execution_stage
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
                    binding.object_type,
                    binding.consumer_key,
                    binding.resource_books,
                    binding.deadline_cycles,
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
    if len({spec.object_type for spec in MECHANISMS}) != len(MECHANISMS):
        raise ValueError("every numbered mechanism needs an exact, non-generic object type")
    for spec in MECHANISMS:
        binding = MECHANISM_BINDINGS[spec.mid]
        if (
            spec.object_type != binding.object_type
            or spec.consumer_key != binding.consumer_key
            or spec.resource_books != binding.resource_books
            or spec.deadline_cycles != binding.deadline_cycles
            or spec.state != binding.execution_stage
        ):
            raise ValueError(f"mechanism {spec.mid} semantic projection diverges from the model")
        if not spec.resource_books or spec.deadline_cycles not in (0, 1):
            raise ValueError(f"mechanism {spec.mid} has an invalid resource/deadline contract")
    for domain, order in DOMAIN_ORDER.items():
        positions = {mid: index for index, mid in enumerate(order)}
        for mid in order:
            if specs[mid].domain != domain:
                raise ValueError(f"mechanism {mid} is bound to the wrong domain")
            for source_mid in CURRENT_OBJECT_DEPENDENCIES.get(mid, ()):
                if specs[source_mid].domain != domain:
                    raise ValueError(f"mechanism {mid} has a cross-domain business dependency")
                if positions[source_mid] >= positions[mid]:
                    raise ValueError(f"mechanism {mid} reads future object {source_mid}")
        for mid, state in STAGE_LAST[domain].items():
            if specs[mid].state != state:
                raise ValueError(f"stage barrier {mid} has the wrong state")
    if {spec.mid for spec in MECHANISMS if spec.domain == "al" and spec.state in (2, 3)}:
        raise ValueError("AL 357-359 must remain an external dependency")
    if len(AD_SOURCE_REPLACED_EXTERNAL_ALIASES) != 16:
        raise ValueError("the AD fact source bridge must replace exactly sixteen legacy aliases")
    if AD_SOURCE_REPLACED_EXTERNAL_ALIASES & RETIRED_AD_EXTERNAL_ALIASES:
        raise ValueError("AD source replacements and independently retired aliases must stay disjoint")
    event_suffixes = [spec.mid for spec in MECHANISMS]
    for domain in ("ab", "ac", "ad", "al"):
        for state in sorted(set(STAGE_LAST[domain].values())):
            event_suffixes.extend((
                DOMAIN_EVENT_BASE[domain] + state,
                DOMAIN_EVENT_BASE[domain] + 100 + state,
            ))
    event_suffixes.extend(FUTURE_EVENT.values())
    event_suffixes.extend((
        M274_NATIVE_ACK_EVENT,
        M274_PROBATION_AUDIT_EVENT,
        M274_SIGNATURE_AUDIT_EVENT,
        M274_DISPOSITION_AUDIT_EVENT,
        M269_DEBT_CANCEL_EVENT,
        M269_DEBT_CANCEL_ACK_EVENT,
        M269_DEBT_ADVANCE_AUDIT_EVENT,
        M269_POSTSETTLEMENT_EVENT,
        M269_RESULT_PUBLISH_EVENT,
        M276_PREPARE_AUDIT_EVENT,
        M276_FINALIZE_EVENT,
        M276_FINALIZE_AUDIT_EVENT,
        REMEDIATION_OPEN_EVENT,
        REMEDIATION_CONSUME_EVENT,
        *HANDOFF_EVENT.values(),
        *HANDOFF_RELAY_EVENT.values(),
        *DEBT_EVENT.values(),
    ))
    if any(suffix < 0 or suffix >= 10000 for suffix in event_suffixes):
        raise ValueError("CK3 event namespace suffixes must remain in 0..9999")
    if len(set(event_suffixes)) != len(event_suffixes):
        raise ValueError("workforce/endgame event namespace suffixes must remain unique")


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


def _save_temp_value(name: str, value: str) -> str:
    """Render effect-side arithmetic before a trigger compares the result."""
    return (
        "save_temporary_scope_value_as = {\n"
        f"\tname = {name}\n"
        f"\tvalue = {{ value = {value} }}\n"
        "}"
    )


def _ticket_next_cycle_prelude() -> str:
    return _save_temp_value("zg361_we_expected_ticket_next_cycle", "$TICKET_CYCLE$ add = 1")


def _collective_argument_prelude() -> str:
    """Arithmetic for the public #360 adapter's scalar arguments."""
    values = [
        *(
            (f"zg361_we_expected_c{slot}_quota", f"$C{slot}_FORCED_COUNT$ add = $C{slot}_EXCEPTION_COUNT$")
            for slot in (1, 2, 3)
        ),
        (
            "zg361_we_expected_collective_total_quota",
            "$C1_QUOTA$ add = $C2_QUOTA$ add = $C3_QUOTA$",
        ),
    ]
    return "\n".join(_save_temp_value(name, value) for name, value in values) + "\n" + _ticket_next_cycle_prelude()


def _collective_persistent_prelude() -> str:
    """Compute #360 aggregate expectations outside trigger grammar."""
    required: list[str] = []
    values: list[tuple[str, str]] = []
    for slot in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{slot}"
        for field in ("member_count", "quota", "forced_count", "exception_count", "manager_cost"):
            required.append(f"has_variable = {base}_{field}")
        values.append(
            (
                f"zg361_we_expected_collective_{slot}_quota",
                f"var:{base}_forced_count add = var:{base}_exception_count",
            )
        )
    for field, source in (
        ("total_members", "member_count"),
        ("total_quota", "quota"),
        ("forced_count", "forced_count"),
        ("exception_count", "exception_count"),
        ("manager_cost_total", "manager_cost"),
    ):
        values.append(
            (
                f"zg361_we_expected_collective_{field}",
                " add = ".join(
                    f"var:{PREFIX}_al_external_collective_{slot}_{source}"
                    for slot in (1, 2, 3)
                ),
            )
        )
    saves = "\n".join(_save_temp_value(name, value) for name, value in values)
    return (
        "if = {\n"
        "\tlimit = {\n"
        f"{indent(chr(10).join(required), 2)}\n"
        "\t}\n"
        f"{indent(saves)}\n"
        "}\n"
        + _ticket_next_cycle_prelude()
    )


def _debt_id_prelude(mid: int) -> str:
    p = f"{PREFIX}_m{mid}_debt"
    return f"""if = {{
\tlimit = {{ has_variable = {p}_cycle has_variable = {p}_case }}
\tsave_temporary_scope_value_as = {{
\t\tname = {PREFIX}_m{mid}_expected_debt_id
\t\tvalue = {{ value = var:{p}_cycle multiply = 1000000 add = {{ value = var:{p}_case multiply = 1000 }} add = {mid} }}
\t}}
}}"""


def _m360_cost_scope_prelude() -> str:
    """Restore the two scopes consumed by the MG #360 public ABI."""

    return f"""save_scope_as = {PREFIX}_m360_cost_subject
$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_cost_owner }}"""


def _central_m360_quota_prelude() -> str:
    """Compute Central's frozen quota sum outside trigger grammar."""

    save = _save_temp_value(
        f"{PREFIX}_expected_central_m360_total_quota",
        "scope:zg361_we_m360_materialize_owner.var:zg361_p2c_m360_source_c1_quota "
        "add = scope:zg361_we_m360_materialize_owner.var:zg361_p2c_m360_source_c2_quota "
        "add = scope:zg361_we_m360_materialize_owner.var:zg361_p2c_m360_source_c3_quota",
    )
    return f"""if = {{
\tlimit = {{
\t\tscope:{PREFIX}_m360_materialize_owner = {{
\t\t\thas_variable = zg361_p2c_m360_source_c1_quota
\t\t\thas_variable = zg361_p2c_m360_source_c2_quota
\t\t\thas_variable = zg361_p2c_m360_source_c3_quota
\t\t}}
\t}}
{indent(save)}
}}"""


def _central_m360_owner_checks(
    status: int = 1, *, verify_quota_sum: bool = True
) -> list[str]:
    """Validate Central's frozen route-neutral envelope from owner scope."""

    common_fields = tuple(
        field for field in M360_CENTRAL_GLOBAL_FIELDS
        if field not in ("cohort_count", "total_quota")
    )
    checks = [
        *(f"has_variable = zg361_p2c_m360_source_{field}" for field in common_fields),
        "has_variable = zg361_p2c_subject",
        "has_variable = zg361_p2c_cycle",
        "has_variable = zg361_p2c_case_serial",
        f"var:zg361_p2c_m360_source_status = {status}",
        "var:zg361_p2c_m360_source_owner = this",
        "var:zg361_p2c_m360_source_subject = $TICKET_SUBJECT$",
        "var:zg361_p2c_m360_source_subject = var:zg361_p2c_subject",
        "var:zg361_p2c_m360_source_p2c_cycle = $TICKET_CYCLE$",
        "var:zg361_p2c_m360_source_p2c_cycle = var:zg361_p2c_cycle",
        "var:zg361_p2c_m360_source_p2c_case = var:zg361_p2c_case_serial",
        "var:zg361_p2c_m360_source_al_cycle = $TICKET_CYCLE$",
        "var:zg361_p2c_m360_source_al_case = $TICKET_CASE$",
    ]
    if status == 1:
        checks += [
            "has_variable = zg361_p2c_m360_source_cohort_count",
            "has_variable = zg361_p2c_m360_source_total_quota",
            "var:zg361_p2c_m360_source_reason = 0",
            "NOT = { has_variable = zg361_p2c_m360_source_upstream_reason }",
            "var:zg361_p2c_m360_source_cohort_count = 3",
            "var:zg361_p2c_m360_source_total_quota >= 1",
            f"var:zg361_p2c_m360_source_total_quota <= {MAX_COLLECTIVE_OUTCOMES}",
        ]
        for cohort in (1, 2, 3):
            base = f"zg361_p2c_m360_source_c{cohort}"
            checks += [
                *(f"has_variable = {base}_{field}" for field in M360_CENTRAL_COHORT_FIELDS),
                f"var:{base}_manager = {{ zg361_is_celestial_liege_trigger = yes liege = scope:{PREFIX}_m360_materialize_owner }}",
                f"var:{base}_b1_cycle > 0",
                f"var:{base}_b1_case > 0",
                f"var:{base}_b1_source_id > 0",
                f"var:{base}_b1_source_hash > 0",
                f"var:{base}_quota >= 1",
                f"var:{base}_quota <= {MAX_COLLECTIVE_OUTCOMES}",
                f"var:{base}_mg_cycle > 0",
                f"var:{base}_mg_case > 0",
                f"var:{base}_mg_snapshot_source_serial > 0",
                f"var:{base}_mg_snapshot_revision > 0",
            ]
        checks += [
            "var:zg361_p2c_m360_source_c1_manager = $TICKET_SUBJECT$",
            "NOT = { var:zg361_p2c_m360_source_c1_manager = var:zg361_p2c_m360_source_c2_manager }",
            "NOT = { var:zg361_p2c_m360_source_c1_manager = var:zg361_p2c_m360_source_c3_manager }",
            "NOT = { var:zg361_p2c_m360_source_c2_manager = var:zg361_p2c_m360_source_c3_manager }",
        ]
        if verify_quota_sum:
            checks.append(
                f"var:zg361_p2c_m360_source_total_quota = scope:{PREFIX}_expected_central_m360_total_quota"
            )
    else:
        checks += [
            "var:zg361_p2c_m360_source_reason >= 360421",
            "var:zg361_p2c_m360_source_reason <= 360425",
            "NOT = { has_variable = zg361_p2c_m360_source_cohort_count }",
            "NOT = { has_variable = zg361_p2c_m360_source_total_quota }",
            "trigger_if = { limit = { var:zg361_p2c_m360_source_reason = 360424 } has_variable = zg361_p2c_m360_source_upstream_reason var:zg361_p2c_m360_source_upstream_reason > 0 } trigger_else = { NOT = { has_variable = zg361_p2c_m360_source_upstream_reason } }",
        ]
    return checks


def _central_m360_live_manager_checks(cohort: int) -> list[str]:
    """Rejoin one frozen Central cohort to its current immutable B1/MG source."""

    central = f"zg361_p2c_m360_source_c{cohort}"
    checks = [
        "zg361_is_celestial_liege_trigger = yes",
        f"liege = scope:{PREFIX}_m360_materialize_owner",
        "has_variable = zg361_b1_m360_source_available",
        "has_variable = zg361_b1_m360_source_sealed",
        "has_variable = zg361_b1_m360_source_status",
        "has_variable = zg361_b1_m360_source_manager",
        "has_variable = zg361_b1_m360_source_cycle",
        "has_variable = zg361_b1_m360_source_case",
        "has_variable = zg361_b1_m360_source_state",
        "has_variable = zg361_b1_m360_source_id",
        "has_variable = zg361_b1_m360_source_hash",
        "has_variable = zg361_b1_m360_source_member_count",
        "has_variable = zg361_b1_m360_source_member_hash",
        "has_variable = zg361_b1_m360_source_agenda_count",
        "has_variable = zg361_b1_m360_source_agenda_hash",
        "has_variable = zg361_b1_m360_source_quota",
        "has_variable = zg361_b1_m360_source_all_meet_receipt_serial",
        "has_variable = zg361_b1_m360_source_forced_count",
        "var:zg361_b1_m360_source_available = 1",
        "var:zg361_b1_m360_source_sealed = 1",
        "var:zg361_b1_m360_source_status = 1",
        "var:zg361_b1_m360_source_manager = this",
        f"var:zg361_b1_m360_source_cycle = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_cycle",
        f"var:zg361_b1_m360_source_case = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_case",
        "var:zg361_b1_m360_source_state = 8",
        f"var:zg361_b1_m360_source_id = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_id",
        f"var:zg361_b1_m360_source_hash = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_hash",
        "var:zg361_b1_m360_source_member_count >= 1",
        "var:zg361_b1_m360_source_member_hash > 0",
        "var:zg361_b1_m360_source_agenda_count = var:zg361_b1_m360_source_member_count",
        "var:zg361_b1_m360_source_agenda_hash = var:zg361_b1_m360_source_member_hash",
        f"var:zg361_b1_m360_source_quota = scope:{PREFIX}_m360_materialize_owner.var:{central}_quota",
        "var:zg361_b1_m360_source_forced_count = var:zg361_b1_m360_source_quota",
        "var:zg361_b1_m360_source_all_meet_receipt_serial > 0",
        "has_variable = zg361_mg_team_snapshot_status",
        "has_variable = zg361_mg_team_snapshot_owner",
        "has_variable = zg361_mg_team_snapshot_subject",
        "has_variable = zg361_mg_team_snapshot_cycle",
        "has_variable = zg361_mg_team_snapshot_case",
        "has_variable = zg361_mg_team_snapshot_revision",
        "has_variable = zg361_mg_snapshot_source_serial",
        "has_variable = zg361_mg_team_snapshot_b1_available",
        "has_variable = zg361_mg_team_snapshot_b1_manager",
        "has_variable = zg361_mg_team_snapshot_b1_cycle",
        "has_variable = zg361_mg_team_snapshot_b1_case",
        "has_variable = zg361_mg_team_snapshot_b1_id",
        "has_variable = zg361_mg_team_snapshot_b1_hash",
        "var:zg361_mg_team_snapshot_status = 1",
        f"var:zg361_mg_team_snapshot_owner = scope:{PREFIX}_m360_materialize_owner",
        "var:zg361_mg_team_snapshot_subject = this",
        f"var:zg361_mg_team_snapshot_cycle = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_cycle",
        f"var:zg361_mg_team_snapshot_case = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_case",
        f"var:zg361_mg_snapshot_source_serial = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_source_serial",
        f"var:zg361_mg_team_snapshot_revision = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_revision",
        "var:zg361_mg_team_snapshot_b1_available = 1",
        "var:zg361_mg_team_snapshot_b1_manager = this",
        f"var:zg361_mg_team_snapshot_b1_cycle = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_cycle",
        f"var:zg361_mg_team_snapshot_b1_case = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_case",
        f"var:zg361_mg_team_snapshot_b1_id = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_id",
        f"var:zg361_mg_team_snapshot_b1_hash = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_hash",
    ]
    for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
        source = f"zg361_b1_m360_source_forced_{slot}"
        checks.append(
            f"trigger_if = {{ limit = {{ var:zg361_b1_m360_source_quota >= {slot} }} "
            + " ".join(f"has_variable = {source}_{field}" for field in M360_B1_SLOT_FIELDS)
            + f" var:{source}_processing_order >= 1"
            + f" var:{source}_processing_order <= var:zg361_b1_m360_source_member_count"
            + f" var:{source}_m357_receipt_id > 0 var:{source}_m357_receipt_hash > 0"
            + f" var:{source}_b1_owner = this var:{source}_b1_subject = var:{source}_character"
            + f" var:{source}_b1_cycle = var:zg361_b1_m360_source_cycle var:{source}_b1_case = var:zg361_b1_m360_source_case"
            + f" var:{source}_result_owner = this var:{source}_result_subject = var:{source}_character"
            + f" var:{source}_result_cycle = var:zg361_b1_m360_source_cycle var:{source}_result_case > 0 }}"
            + " trigger_else = { always = yes }"
        )
    return checks


def _collective_external_checks(choice: int) -> list[str]:
    """Validate the product-owned three-cohort object before any mutation."""

    if choice not in (1, 2):
        raise ValueError("collective facts exist only for #360 route A/B")
    checks = [
        *(f"has_variable = {PREFIX}_al_external_collective_{field}" for field in (
            "case", "submitted_cycle", "cohort_count", "total_members",
            "total_quota", "settlement_id", "settlement_hash", "settled",
            "forced_count", "exception_count", "manager_cost_total", "route",
            "submission_active", "submission_sealed", "submission_consumed",
            "submission_owner", "submission_subject", "submission_cycle",
            "submission_case", "submission_state",
        )),
        f"var:{PREFIX}_al_external_collective_submitted_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_collective_cohort_count = 3",
        f"var:{PREFIX}_al_external_collective_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_collective_settled = 0",
        f"var:{PREFIX}_al_external_collective_route = {choice}",
        f"var:{PREFIX}_al_external_collective_submission_active = 1",
        f"var:{PREFIX}_al_external_collective_submission_sealed = 1",
        f"var:{PREFIX}_al_external_collective_submission_consumed = 0",
        f"var:{PREFIX}_al_external_collective_submission_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_al_external_collective_submission_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_al_external_collective_submission_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_collective_submission_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_collective_submission_state = 4",
        f"var:{PREFIX}_al_external_receipt_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_al_external_receipt_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_al_external_receipt_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_receipt_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_receipt_state = 4",
    ]
    identity_slots: list[tuple[int, int, str, str]] = []
    active_kind = "exception" if choice == 1 else "forced"
    inactive_kind = "forced" if choice == 1 else "exception"
    for cohort in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{cohort}"
        for name in (
            "cohort_id", "manager", "member_count", "member_hash",
            "agenda_count", "agenda_hash", "quota", "all_meet_evidence_id",
            "forced_count", "exception_count", "approver", "manager_cost",
            "partition_verified", "approval_verified", "mg_cycle", "mg_case",
            "mg_snapshot_source_serial", "mg_snapshot_revision", "b1_cycle",
            "b1_case", "b1_source_id", "b1_source_hash",
        ):
            checks.append(f"has_variable = {base}_{name}")
        checks += [
            f"var:{base}_member_count = var:{base}_agenda_count",
            f"var:{base}_member_hash = var:{base}_agenda_hash",
            f"var:{base}_member_count >= 1",
            f"var:{base}_member_hash > 0",
            f"var:{base}_quota >= 1",
            f"var:{base}_quota <= var:{base}_member_count",
            f"var:{base}_partition_verified = 1",
            f"var:{base}_manager = {{ zg361_is_celestial_liege_trigger = yes liege = scope:{PREFIX}_m360_cost_owner }}",
            f"var:{base}_manager = {{ zg361_mg_m360_collective_cost_c{cohort}_can_apply_trigger = yes }}",
        ]
        if choice == 1:
            checks += [
                f"var:{base}_forced_count = 0",
                f"var:{base}_exception_count = var:{base}_quota",
                f"var:{base}_manager_cost = var:{base}_quota",
                f"var:{base}_approver = $TICKET_OWNER$",
                f"var:{base}_approval_verified = 1",
            ]
        else:
            checks += [
                f"var:{base}_forced_count = var:{base}_quota",
                f"var:{base}_exception_count = 0",
                f"var:{base}_manager_cost = 0",
                f"var:{base}_approver = 0",
                f"var:{base}_approval_verified = 0",
            ]
        for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
            identity = f"{base}_{active_kind}_{slot}"
            identity_slots.append((cohort, slot, f"{base}_{active_kind}_count", identity))
            active_fields = (
                "character", "cohort_id", "member_evidence_receipt",
                "member_evidence_id", "member_evidence_hash", "processing_order",
                "b1_owner", "b1_subject", "b1_cycle", "b1_case",
                "result_owner", "result_subject", "result_cycle", "result_case",
            )
            checks.append(
                f"trigger_if = {{ limit = {{ var:{base}_{active_kind}_count >= {slot} }} "
                + " ".join(f"has_variable = {identity}_{field}" for field in active_fields)
                + f" var:{identity}_cohort_id = var:{base}_cohort_id"
                + f" var:{identity}_member_evidence_receipt = 1"
                + f" var:{identity}_member_evidence_id > 0 var:{identity}_member_evidence_hash > 0"
                + f" var:{identity}_processing_order >= 1 var:{identity}_processing_order <= var:{base}_member_count"
                + f" var:{identity}_b1_owner = var:{base}_manager var:{identity}_b1_subject = var:{identity}_character"
                + f" var:{identity}_b1_cycle = var:{base}_b1_cycle var:{identity}_b1_case = var:{base}_b1_case"
                + f" var:{identity}_result_owner = var:{base}_manager var:{identity}_result_subject = var:{identity}_character"
                + f" var:{identity}_result_cycle = var:{base}_b1_cycle var:{identity}_result_case > 0 }}"
                + " trigger_else = { always = yes }"
            )
            checks.append(
                f"trigger_if = {{ limit = {{ var:{base}_{inactive_kind}_count >= {slot} }} always = no }} "
                f"trigger_else = {{ always = yes }}"
            )
    checks += [
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_cohort_id = var:{PREFIX}_al_external_collective_2_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_cohort_id = var:{PREFIX}_al_external_collective_3_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_2_cohort_id = var:{PREFIX}_al_external_collective_3_cohort_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_manager = var:{PREFIX}_al_external_collective_2_manager }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_1_manager = var:{PREFIX}_al_external_collective_3_manager }}",
        f"NOT = {{ var:{PREFIX}_al_external_collective_2_manager = var:{PREFIX}_al_external_collective_3_manager }}",
        f"var:{PREFIX}_al_external_collective_total_members = scope:zg361_we_expected_collective_total_members",
        f"var:{PREFIX}_al_external_collective_total_quota = scope:zg361_we_expected_collective_total_quota",
        f"var:{PREFIX}_al_external_collective_forced_count = scope:zg361_we_expected_collective_forced_count",
        f"var:{PREFIX}_al_external_collective_exception_count = scope:zg361_we_expected_collective_exception_count",
        f"var:{PREFIX}_al_external_collective_manager_cost_total = scope:zg361_we_expected_collective_manager_cost_total",
        f"var:{PREFIX}_al_external_collective_total_members >= 3",
        f"var:{PREFIX}_al_external_collective_total_quota >= 1",
        f"var:{PREFIX}_al_external_collective_total_quota <= {MAX_COLLECTIVE_OUTCOMES}",
    ]
    if choice == 1:
        checks += [
            f"var:{PREFIX}_al_external_collective_forced_count = 0",
            f"var:{PREFIX}_al_external_collective_exception_count = var:{PREFIX}_al_external_collective_total_quota",
            f"var:{PREFIX}_al_external_collective_manager_cost_total = var:{PREFIX}_al_external_collective_total_quota",
            f"$TICKET_OWNER$ = {{ has_variable = {PREFIX}_realm_trust var:{PREFIX}_realm_trust >= scope:{PREFIX}_m360_cost_subject.var:{PREFIX}_al_external_collective_manager_cost_total }}",
        ]
    else:
        checks += [
            f"var:{PREFIX}_al_external_collective_forced_count = var:{PREFIX}_al_external_collective_total_quota",
            f"var:{PREFIX}_al_external_collective_exception_count = 0",
            f"var:{PREFIX}_al_external_collective_manager_cost_total = 0",
        ]
    # One B1 candidate can occupy exactly one active route-local slot globally.
    for left_index, (_, left_slot, left_count, left) in enumerate(identity_slots):
        for _, right_slot, right_count, right in identity_slots[left_index + 1:]:
            checks.append(
                f"trigger_if = {{ limit = {{ var:{left_count} >= {left_slot} var:{right_count} >= {right_slot} }} "
                f"NOT = {{ var:{left}_character = var:{right}_character }} }} "
                f"trigger_else = {{ always = yes }}"
            )
    return checks


def _collective_business_writes(choice: int) -> list[str]:
    if choice not in (1, 2):
        raise ValueError("collective settlement exists only for #360 route A/B")
    lines = [
        _m360_cost_scope_prelude(),
    ]
    for slot in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{slot}"
        lines.append(
            f"var:{base}_manager = {{ zg361_mg_m360_apply_collective_cost_c{slot}_effect = yes }}"
        )
    lines += [
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
        if choice == 1:
            for field in M360_MG_RECEIPT_FIELDS:
                lines.append(
                    _set(
                        f"m360_cohort_{slot}_manager_cost_receipt_{field}",
                        f"var:{base}_manager.var:zg361_mg_m360_cost_receipt_{field}",
                    )
                )
            lines += [
                _set(f"m360_cohort_{slot}_manager_cost_applicable", 1),
                _set(f"m360_cohort_{slot}_manager_cost_receipt_present", 1),
            ]
        else:
            lines += [
                *(
                    f"remove_variable = {PREFIX}_m360_cohort_{slot}_manager_cost_receipt_{field}"
                    for field in M360_MG_RECEIPT_FIELDS
                ),
                _set(f"m360_cohort_{slot}_manager_cost_applicable", 0),
                _set(f"m360_cohort_{slot}_manager_cost_receipt_present", 0),
            ]
    for cohort in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{cohort}"
        for kind in ("forced", "exception"):
            for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
                source = f"{base}_{kind}_{slot}"
                copy_fields = (
                    "character", "cohort_id", "member_evidence_receipt",
                    "member_evidence_id", "member_evidence_hash", "processing_order",
                    "b1_owner", "b1_subject", "b1_cycle", "b1_case",
                    "result_owner", "result_subject", "result_cycle", "result_case",
                )
                copies = " ".join(
                    f"set_variable = {{ name = {PREFIX}_m360_cohort_{cohort}_{kind}_{slot}_{field} value = var:{source}_{field} }}"
                    for field in copy_fields
                )
                lines.append(
                    f"if = {{ limit = {{ var:{base}_{kind}_count >= {slot} }} {copies} }}"
                )
    if choice == 1:
        lines += [
            f"$TICKET_OWNER$ = {{ change_variable = {{ name = {PREFIX}_realm_trust add = {{ value = 0 subtract = scope:{PREFIX}_m360_cost_subject.var:{PREFIX}_al_external_collective_manager_cost_total }} }} }}",
            _set("m360_realm_trust_delta", f"{{ value = 0 subtract = var:{PREFIX}_al_external_collective_manager_cost_total }}"),
            _set("m360_manager_cost_direction", f"{{ value = 0 subtract = var:{PREFIX}_al_external_collective_manager_cost_total }}"),
        ]
    else:
        lines += [
            _set("m360_realm_trust_delta", 0),
            _set("m360_manager_cost_direction", 0),
        ]
    lines += [
        _set("m360_settled", 1),
        _set("al_external_collective_settled", 1),
        _set("al_external_collective_submission_consumed", 1),
        _set("al_external_collective_submission_active", 0),
        _set("m360_event_queued", 0),
    ]
    return lines


def _charter_evidence_checks() -> list[str]:
    """Validate the product-owned report projected from three real stage receipts."""

    checks = [
        f"has_variable = {PREFIX}_m361_evidence_count",
        f"has_variable = {PREFIX}_m361_evidence_ready",
        f"has_variable = {PREFIX}_m361_evidence_consumed",
        f"has_variable = {PREFIX}_m361_evidence_owner",
        f"has_variable = {PREFIX}_m361_evidence_subject",
        f"has_variable = {PREFIX}_m361_evidence_cycle",
        f"has_variable = {PREFIX}_m361_evidence_case",
        f"has_variable = {PREFIX}_m361_evidence_state",
        f"has_variable = {PREFIX}_m361_prepared_report_id",
        f"has_variable = {PREFIX}_m361_prepared_charter_id",
        f"has_variable = {PREFIX}_m361_prepared_previous_charter_id",
        f"has_variable = {PREFIX}_m361_prepared_previous_version",
        f"has_variable = {PREFIX}_m361_prepared_adopted_cycle",
        f"has_variable = {PREFIX}_m361_prepared_effective_cycle",
        f"var:{PREFIX}_m361_evidence_count = 3",
        f"var:{PREFIX}_m361_evidence_ready = 1",
        f"var:{PREFIX}_m361_evidence_consumed = 0",
        f"var:{PREFIX}_m361_evidence_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m361_evidence_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m361_evidence_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m361_evidence_case = $TICKET_CASE$",
        f"var:{PREFIX}_m361_evidence_state = 5",
        f"var:{PREFIX}_m361_prepared_report_id > 0",
        f"var:{PREFIX}_m361_prepared_charter_id > 0",
        f"var:{PREFIX}_m361_prepared_adopted_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m361_prepared_effective_cycle = scope:{PREFIX}_expected_ticket_next_cycle",
        f"var:zg361_case_al_owner = {{",
        f"\thas_variable = {PREFIX}_realm_charter_current_version",
        f"\thas_variable = {PREFIX}_realm_charter_current_id",
        f"\thas_variable = {PREFIX}_realm_charter_current_report_id",
        f"\thas_variable = {PREFIX}_realm_charter_current_adopted_cycle",
        f"\thas_variable = {PREFIX}_realm_charter_current_effective_cycle",
        f"\thas_variable = {PREFIX}_realm_charter_history_count",
        f"\thas_variable = {PREFIX}_realm_charter_report_serial",
        f"\thas_variable = {PREFIX}_realm_charter_id_serial",
        f"\tvar:{PREFIX}_realm_charter_history_count = var:{PREFIX}_realm_charter_current_version",
        f"\tvar:{PREFIX}_realm_charter_current_version = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_previous_version",
        f"\tvar:{PREFIX}_realm_charter_current_id = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_previous_charter_id",
        f"\tvar:{PREFIX}_realm_charter_report_serial = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_report_id",
        f"\tvar:{PREFIX}_realm_charter_id_serial = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_charter_id",
        "}",
        f"trigger_if = {{ limit = {{ var:zg361_case_al_owner = {{ var:{PREFIX}_realm_charter_current_version > 0 }} }}",
        f"\tvar:{PREFIX}_m361_prepared_adopted_cycle > var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_adopted_cycle",
        f"\tNOT = {{ var:{PREFIX}_m361_prepared_report_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_report_id }}",
        f"\tNOT = {{ var:{PREFIX}_m361_prepared_charter_id = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_id }}",
        f"\tvar:zg361_case_al_owner = {{ var:{PREFIX}_realm_charter_current_effective_cycle < scope:{PREFIX}_expected_ticket_next_cycle }}",
        f"}} trigger_else = {{ var:{PREFIX}_m361_prepared_previous_charter_id = 0 }}",
    ]
    for slot in (1, 2, 3):
        for name in ("owner", "subject", "cycle", "case"):
            checks += [
                f"has_variable = {PREFIX}_m361_evidence_{name}_{slot}",
                f"var:{PREFIX}_m361_evidence_{name}_{slot} = var:zg361_case_al_owner.var:{PREFIX}_completed_cycle_ledger_{name}_{slot}",
            ]
        for mid in (357, 358, 359):
            for kind in ("id", "hash"):
                checks += [
                    f"has_variable = {PREFIX}_m361_evidence_m{mid}_receipt_{kind}_{slot}",
                    f"var:{PREFIX}_m361_evidence_m{mid}_receipt_{kind}_{slot} = var:zg361_case_al_owner.var:{PREFIX}_completed_cycle_ledger_m{mid}_receipt_{kind}_{slot}",
                ]
        checks += [
            f"var:{PREFIX}_m361_evidence_owner_{slot} = $TICKET_OWNER$",
            f"var:{PREFIX}_m361_evidence_cycle_{slot} >= 1",
            f"var:{PREFIX}_m361_evidence_case_{slot} > 0",
        ]
        for mid in (357, 358, 359):
            checks += [
                f"var:{PREFIX}_m361_evidence_m{mid}_receipt_id_{slot} > 0",
                f"var:{PREFIX}_m361_evidence_m{mid}_receipt_hash_{slot} > 0",
            ]
    checks += [
        f"var:{PREFIX}_m361_evidence_cycle_1 < var:{PREFIX}_m361_evidence_cycle_2",
        f"var:{PREFIX}_m361_evidence_cycle_2 < var:{PREFIX}_m361_evidence_cycle_3",
        f"var:{PREFIX}_m361_evidence_cycle_3 = $TICKET_CYCLE$",
        f"var:{PREFIX}_m361_evidence_subject_3 = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m361_evidence_case_3 = $TICKET_CASE$",
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
        _set("m361_previous_charter_id", f"var:{PREFIX}_m361_prepared_previous_charter_id"),
        _set("m361_charter_id", f"var:{PREFIX}_m361_prepared_charter_id"),
        _set("m361_adopted_cycle", f"var:{PREFIX}_m361_prepared_adopted_cycle"),
        _set("m361_effective_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"),
        _set("m361_amendment_due_cycle", "{ value = $TICKET_CYCLE$ add = 3 }"),
        _set("m361_completed_evidence_count", 3),
        _set("m361_report_id", f"var:{PREFIX}_m361_prepared_report_id"),
        _set("m361_report_frozen", 1),
        _set("m361_visible_cost_gold", cost),
        _set("m361_history_reset", 0),
        _set("m361_future_install_pending", 1),
    ]
    for slot in (1, 2, 3):
        for name in ("owner", "subject", "cycle", "case"):
            lines.append(_set(f"m361_completed_{name}_{slot}", f"var:{PREFIX}_m361_evidence_{name}_{slot}"))
        for mid in (357, 358, 359):
            for kind in ("id", "hash"):
                lines.append(
                    _set(
                        f"m361_completed_m{mid}_receipt_{kind}_{slot}",
                        f"var:{PREFIX}_m361_evidence_m{mid}_receipt_{kind}_{slot}",
                    )
                )
    lines += [
        f"var:zg361_case_al_owner = {{ if = {{ limit = {{ var:{PREFIX}_realm_charter_current_version = 0 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_1 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_cycle_1 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_2 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_cycle_2 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_cycle_3 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_cycle_3 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_case_1 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_case_1 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_case_2 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_case_2 }} set_variable = {{ name = {PREFIX}_realm_charter_anchor_case_3 value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_evidence_case_3 }} set_variable = {{ name = {PREFIX}_realm_charter_report_anchor value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_report_id }} }} }}",
        f"var:zg361_case_al_owner = {{ set_variable = {{ name = {PREFIX}_realm_charter_previous_version value = var:{PREFIX}_realm_charter_current_version }} set_variable = {{ name = {PREFIX}_realm_charter_previous_id value = var:{PREFIX}_realm_charter_current_id }} set_variable = {{ name = {PREFIX}_realm_charter_previous_report_id value = var:{PREFIX}_realm_charter_current_report_id }} change_variable = {{ name = {PREFIX}_realm_charter_current_version add = 1 }} change_variable = {{ name = {PREFIX}_realm_charter_history_count add = 1 }} set_variable = {{ name = {PREFIX}_realm_charter_current_id value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_charter_id }} set_variable = {{ name = {PREFIX}_realm_charter_current_report_id value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_report_id }} set_variable = {{ name = {PREFIX}_realm_charter_current_adopted_cycle value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_adopted_cycle }} set_variable = {{ name = {PREFIX}_realm_charter_current_effective_cycle value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_effective_cycle }} set_variable = {{ name = {PREFIX}_realm_charter_last_case value = $TICKET_CASE$ }} set_variable = {{ name = {PREFIX}_realm_charter_last_report value = scope:{PREFIX}_al_subject.var:{PREFIX}_m361_prepared_report_id }} }}",
        _set("m361_adopted_version", f"var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_version"),
        _set("m361_previous_charter_version", f"var:zg361_case_al_owner.var:{PREFIX}_realm_charter_previous_version"),
        _set("m361_evidence_consumed", 1),
        _set("m361_evidence_ready", 0),
        f"var:zg361_case_al_owner = {{ remove_short_term_gold = {cost} }}",
        f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[361]} days = 365 }}",
    ]
    return lines

def _current_object_checks(spec: Mechanism) -> list[str]:
    """Require every semantic input to be a consumed object of this case.

    Per-ID variables persist on characters across review cycles.  Existence by
    itself therefore accepts stale evidence.  These checks bind every source
    object back to the live owner/subject/cycle/case tuple before any resource
    read or receipt is written.
    """

    checks: list[str] = []
    for source_mid in CURRENT_OBJECT_DEPENDENCIES.get(spec.mid, ()):
        source = by_id()[source_mid]
        for name in (
            "business_object_created",
            "object_type_code",
            "object_owner",
            "object_subject",
            "object_cycle",
            "object_case",
            "object_consumed",
            f"consumer_{source.consumer_key}",
        ):
            checks.append(f"has_variable = {PREFIX}_m{source_mid}_{name}")
        checks += [
            f"var:{PREFIX}_m{source_mid}_business_object_created = 1",
            f"var:{PREFIX}_m{source_mid}_object_type_code = {source_mid}",
            f"var:{PREFIX}_m{source_mid}_object_owner = $TICKET_OWNER$",
            f"var:{PREFIX}_m{source_mid}_object_subject = $TICKET_SUBJECT$",
            f"var:{PREFIX}_m{source_mid}_object_cycle = $TICKET_CYCLE$",
            f"var:{PREFIX}_m{source_mid}_object_case = $TICKET_CASE$",
            f"var:{PREFIX}_m{source_mid}_object_consumed = 1",
            f"var:{PREFIX}_m{source_mid}_consumer_{source.consumer_key} = 1",
        ]
    return checks


def _ad_source_hash_prelude(source: str) -> str:
    terminal = "response" if source == "offer" else "disposition"
    p = f"zg361_wad_{source}_source"
    return f"""if = {{
	limit = {{
		has_variable = {p}_id
		has_variable = {p}_cycle
		has_variable = {p}_case
		has_variable = {p}_{terminal}
	}}
	save_temporary_scope_value_as = {{
		name = {PREFIX}_ad_expected_{source}_source_hash
		value = {{ value = var:{p}_id multiply = 1000000 add = {{ value = var:{p}_cycle multiply = 10000 }} add = {{ value = var:{p}_case multiply = 10 }} add = var:{p}_{terminal} }}
	}}
}}"""


def _ad_source_common_checks(
    source: str,
    *,
    state: int,
    terminal: int | tuple[int, ...],
    pending: int = 1,
    consumed: int = 0,
    retired: int = 0,
) -> list[str]:
    terminal_name = "response" if source == "offer" else "disposition"
    p = f"zg361_wad_{source}_source"
    terminal_values = (terminal,) if isinstance(terminal, int) else terminal
    terminal_check = (
        f"var:{p}_{terminal_name} = {terminal_values[0]}"
        if len(terminal_values) == 1
        else "OR = { " + " ".join(
            f"var:{p}_{terminal_name} = {value}" for value in terminal_values
        ) + " }"
    )
    fields = (*AD_SOURCE_COMMON_FIELDS, terminal_name)
    checks = [f"has_variable = {p}_{field}" for field in fields]
    checks += [
        f"var:{p}_pending = {pending}",
        f"var:{p}_consumed = {consumed}",
        f"var:{p}_retired = {retired}",
        f"var:{p}_owner = $TICKET_OWNER$",
        f"var:{p}_subject = $TICKET_SUBJECT$",
        f"var:{p}_cycle = $TICKET_CYCLE$",
        f"var:{p}_case = $TICKET_CASE$",
        f"var:{p}_state = {state}",
        f"var:{p}_id > 0",
        f"var:{p}_hash = scope:{PREFIX}_ad_expected_{source}_source_hash",
        terminal_check,
    ]
    return checks


def _ad_referral_source_checks(*, disposition: int | tuple[int, ...] = 1) -> list[str]:
    checks = _ad_source_common_checks("referral", state=1, terminal=disposition)
    if disposition == 1:
        checks += [
            "has_variable = zg361_wad_referral_source_referral_id",
            "has_variable = zg361_wad_referral_source_referrer",
            "has_variable = zg361_wad_referral_source_relationship",
            "has_variable = zg361_wad_referral_source_evidence_receipt",
            "var:zg361_wad_referral_source_referral_id > 0",
            "var:zg361_wad_referral_source_evidence_receipt > 0",
            "NOT = { var:zg361_wad_referral_source_id = var:zg361_wad_referral_source_referral_id }",
            "NOT = { var:zg361_wad_referral_source_id = var:zg361_wad_referral_source_evidence_receipt }",
            "NOT = { var:zg361_wad_referral_source_referral_id = var:zg361_wad_referral_source_evidence_receipt }",
            "var:zg361_wad_referral_source_referrer = { zg361_is_celestial_liege_trigger = yes }",
            "NOT = { var:zg361_wad_referral_source_referrer = $TICKET_SUBJECT$ }",
            "var:zg361_wad_referral_source_relationship >= 1",
            "var:zg361_wad_referral_source_relationship <= 3",
        ]
    return checks


def _ad_panel_source_checks(*, disposition: int | tuple[int, ...] = 1) -> list[str]:
    checks = _ad_source_common_checks("panel", state=1, terminal=disposition)
    if disposition == 1:
        checks += [
            "has_variable = zg361_wad_panel_source_referrer",
            "has_variable = zg361_wad_panel_source_referrer_vote_policy",
            "has_variable = zg361_wad_panel_runner_up_present",
            "var:zg361_wad_panel_source_referrer_vote_policy >= 0",
            "var:zg361_wad_panel_source_referrer_vote_policy <= 1",
            "var:zg361_wad_panel_runner_up_present >= 0",
            "var:zg361_wad_panel_runner_up_present <= 1",
        ]
        for slot in (1, 2, 3):
            checks += [
                f"has_variable = zg361_wad_panel_source_interviewer_{slot}",
                f"has_variable = zg361_wad_panel_source_vote_{slot}",
                f"has_variable = zg361_wad_panel_source_vote_evidence_{slot}",
                f"has_variable = zg361_wad_panel_vote_receipt_actor_{slot}",
                f"var:zg361_wad_panel_source_interviewer_{slot} = {{ zg361_is_celestial_liege_trigger = yes }}",
                f"NOT = {{ var:zg361_wad_panel_source_interviewer_{slot} = $TICKET_SUBJECT$ }}",
                f"var:zg361_wad_panel_source_vote_{slot} >= 1",
                f"var:zg361_wad_panel_source_vote_{slot} <= 3",
                f"var:zg361_wad_panel_source_vote_evidence_{slot} > 0",
                f"var:zg361_wad_panel_vote_receipt_actor_{slot} = var:zg361_wad_panel_source_interviewer_{slot}",
                f"NOT = {{ var:zg361_wad_panel_source_id = var:zg361_wad_panel_source_vote_evidence_{slot} }}",
            ]
        checks += [
            "NOT = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_interviewer_2 }",
            "NOT = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_interviewer_3 }",
            "NOT = { var:zg361_wad_panel_source_interviewer_2 = var:zg361_wad_panel_source_interviewer_3 }",
            "NOT = { var:zg361_wad_panel_source_vote_evidence_1 = var:zg361_wad_panel_source_vote_evidence_2 }",
            "NOT = { var:zg361_wad_panel_source_vote_evidence_1 = var:zg361_wad_panel_source_vote_evidence_3 }",
            "NOT = { var:zg361_wad_panel_source_vote_evidence_2 = var:zg361_wad_panel_source_vote_evidence_3 }",
            "trigger_if = { limit = { var:zg361_wad_panel_runner_up_present = 1 } has_variable = zg361_wad_panel_source_runner_up has_variable = zg361_wad_panel_source_runner_up_evidence var:zg361_wad_panel_source_runner_up_evidence > 0 NOT = { var:zg361_wad_panel_source_runner_up = $TICKET_SUBJECT$ } } trigger_else = { NOT = { has_variable = zg361_wad_panel_source_runner_up } NOT = { has_variable = zg361_wad_panel_source_runner_up_evidence } }",
        ]
    return checks


def _ad_offer_source_checks(*, response: int) -> list[str]:
    checks = _ad_source_common_checks("offer", state=4, terminal=response)
    checks += [
        "has_variable = zg361_wad_offer_source_response_receipt",
        "var:zg361_wad_offer_source_response_receipt > 0",
        "NOT = { var:zg361_wad_offer_source_id = var:zg361_wad_offer_source_response_receipt }",
    ]
    if response == 1:
        checks.append("NOT = { has_variable = zg361_wad_offer_source_refusal_reason_id }")
    else:
        checks += [
            "has_variable = zg361_wad_offer_source_refusal_reason_id",
            "var:zg361_wad_offer_source_refusal_reason_id >= 1",
            "var:zg361_wad_offer_source_refusal_reason_id <= 3",
        ]
    return checks


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
    checks += _current_object_checks(spec)
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
    if mid == 262:
        checks += [
            f"has_variable = {PREFIX}_ac_external_secondment_host_manager",
            f"var:{PREFIX}_ac_external_secondment_host_manager = {{ zg361_is_celestial_liege_trigger = yes }}",
            f"NOT = {{ var:{PREFIX}_ac_external_secondment_host_manager = $TICKET_SUBJECT$ }}",
            f"NOT = {{ var:{PREFIX}_ac_external_secondment_host_manager = $TICKET_OWNER$ }}",
        ]
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
            f"has_variable = {PREFIX}_m264_handoff_flow_active",
            f"has_variable = {PREFIX}_m264_handoff_flow_consumed",
            f"has_variable = {PREFIX}_m264_handoff_owner",
            f"has_variable = {PREFIX}_m264_handoff_subject",
            f"has_variable = {PREFIX}_m264_handoff_cycle",
            f"has_variable = {PREFIX}_m264_handoff_case",
            f"has_variable = {PREFIX}_m264_handoff_contract_id",
            f"has_variable = {PREFIX}_m264_handoff_response",
            f"var:{PREFIX}_m264_handoff_flow_active = 1",
            f"var:{PREFIX}_m264_handoff_flow_consumed = 0",
            f"var:{PREFIX}_m264_handoff_owner = $TICKET_OWNER$",
            f"var:{PREFIX}_m264_handoff_subject = $TICKET_SUBJECT$",
            f"var:{PREFIX}_m264_handoff_cycle = $TICKET_CYCLE$",
            f"var:{PREFIX}_m264_handoff_case = $TICKET_CASE$",
            f"var:{PREFIX}_m264_handoff_contract_id = var:{PREFIX}_m254_contract_id",
            f"var:zg361_case_{d}_owner = {{ has_variable = zg361_review_serial var:zg361_review_serial >= scope:{PREFIX}_{d}_subject.var:{PREFIX}_m254_sunset_cycle }}",
        ]
        if choice == 1:
            checks += [
                f"var:zg361_case_{d}_owner = {{ gold >= 20 }}",
                f"var:{PREFIX}_m264_handoff_response = 1",
                f"has_variable = {PREFIX}_m264_documentation_receipt_id",
                f"has_variable = {PREFIX}_m264_shadowing_receipt_id",
                f"has_variable = {PREFIX}_m264_practical_receipt_id",
                f"has_variable = {PREFIX}_m264_handoff_documentation_source_object",
                f"has_variable = {PREFIX}_m264_handoff_shadowing_source_object",
                f"has_variable = {PREFIX}_m264_handoff_practical_source_object",
                f"var:{PREFIX}_m264_documentation_receipt_id > 0",
                f"var:{PREFIX}_m264_shadowing_receipt_id > 0",
                f"var:{PREFIX}_m264_practical_receipt_id > 0",
                f"var:{PREFIX}_m264_handoff_documentation_source_object = var:{PREFIX}_m261_object_id",
                f"var:{PREFIX}_m264_handoff_shadowing_source_object = var:{PREFIX}_m263_object_id",
                f"var:{PREFIX}_m264_handoff_practical_source_object = var:{PREFIX}_m256_object_id",
                f"NOT = {{ var:{PREFIX}_m264_documentation_receipt_id = var:{PREFIX}_m264_shadowing_receipt_id }}",
                f"NOT = {{ var:{PREFIX}_m264_documentation_receipt_id = var:{PREFIX}_m264_practical_receipt_id }}",
                f"NOT = {{ var:{PREFIX}_m264_shadowing_receipt_id = var:{PREFIX}_m264_practical_receipt_id }}",
            ]
        else:
            checks += [
                f"var:{PREFIX}_m264_handoff_response = 2",
                f"has_variable = {PREFIX}_m264_handoff_refusal_reason",
                f"var:{PREFIX}_m264_handoff_refusal_reason >= 1",
                f"var:{PREFIX}_m264_handoff_refusal_reason <= 3",
            ]
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
        checks += _ad_panel_source_checks() + [
            f"has_variable = {PREFIX}_m271_candidate",
            f"has_variable = {PREFIX}_m271_referral_id",
            f"has_variable = {PREFIX}_m271_referrer",
            f"has_variable = {PREFIX}_m271_relationship_ref",
            f"has_variable = {PREFIX}_m271_evidence_receipt",
            f"has_variable = {PREFIX}_m271_reward_gold",
            f"has_variable = {PREFIX}_m271_referrer_vote_policy",
            f"var:{PREFIX}_m271_candidate = $TICKET_SUBJECT$",
            f"var:{PREFIX}_m271_referral_id > 0",
            f"var:{PREFIX}_m271_evidence_receipt > 0",
            f"var:{PREFIX}_m271_reward_gold = 5",
            f"var:{PREFIX}_m271_referrer_vote_policy >= 0",
            f"var:{PREFIX}_m271_referrer_vote_policy <= 1",
            f"NOT = {{ var:{PREFIX}_m271_referrer = var:{PREFIX}_m271_candidate }}",
            f"has_variable = {PREFIX}_gold_reserved",
            f"var:{PREFIX}_gold_reserved >= 5",
            f"has_variable = {PREFIX}_referral_gold_reserved",
            f"var:{PREFIX}_referral_gold_reserved >= 5",
            f"has_variable = {PREFIX}_m271_reward_escrowed",
            f"var:{PREFIX}_m271_reward_escrowed = 1",
            f"has_variable = {PREFIX}_m271_reward_paid_before_probation",
            f"var:{PREFIX}_m271_reward_paid_before_probation = 0",
        ]
        checks += [
            (
                f"var:{PREFIX}_m271_referrer_vote_policy = 0 NOT = {{ OR = {{ var:zg361_wad_panel_source_interviewer_1 = var:{PREFIX}_m271_referrer var:zg361_wad_panel_source_interviewer_2 = var:{PREFIX}_m271_referrer var:zg361_wad_panel_source_interviewer_3 = var:{PREFIX}_m271_referrer }} }}"
                if choice == 1 else
                f"var:{PREFIX}_m271_referrer_vote_policy = 1 var:zg361_wad_panel_source_interviewer_1 = var:{PREFIX}_m271_referrer"
            ),
        ]
    if mid == 271:
        checks += _gold_check(5) + _ad_referral_source_checks() + [
            f"var:zg361_case_{d}_owner = {{ gold >= 5 }}",
        ]
    if mid == 272:
        checks += _gold_check(10) + [f"var:zg361_case_{d}_owner = {{ gold >= 10 }}"]
    if mid == 274:
        checks += _gold_check(5) + _ad_offer_source_checks(response=choice) + [
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
        if choice == 1:
            checks += [
                f"has_variable = {PREFIX}_ad_external_appointment_ready",
                f"has_variable = {PREFIX}_ad_external_appointment_consumed",
                f"has_variable = {PREFIX}_ad_external_appointing_owner",
                f"has_variable = {PREFIX}_ad_external_position_type_id",
                f"has_variable = {PREFIX}_ad_external_position_receipt_id",
                f"has_variable = {PREFIX}_ad_external_position_receipt_hash",
                f"has_variable = {PREFIX}_ad_appointment_receipt_owner",
                f"has_variable = {PREFIX}_ad_appointment_receipt_subject",
                f"has_variable = {PREFIX}_ad_appointment_receipt_cycle",
                f"has_variable = {PREFIX}_ad_appointment_receipt_case",
                f"has_variable = {PREFIX}_ad_appointment_receipt_state",
                f"var:{PREFIX}_ad_external_appointment_ready = 1",
                f"var:{PREFIX}_ad_external_appointment_consumed = 0",
                f"var:{PREFIX}_ad_external_appointing_owner = $TICKET_OWNER$",
                f"var:{PREFIX}_ad_external_position_type_id > 0",
                f"var:{PREFIX}_ad_external_position_receipt_id > 0",
                f"var:{PREFIX}_ad_external_position_receipt_hash > 0",
                f"var:{PREFIX}_ad_appointment_receipt_owner = $TICKET_OWNER$",
                f"var:{PREFIX}_ad_appointment_receipt_subject = $TICKET_SUBJECT$",
                f"var:{PREFIX}_ad_appointment_receipt_cycle = $TICKET_CYCLE$",
                f"var:{PREFIX}_ad_appointment_receipt_case = $TICKET_CASE$",
                f"var:{PREFIX}_ad_appointment_receipt_state = 4",
            ]
    if mid == 273:
        checks += [
            _zero_or_missing(f"{PREFIX}_candidate_active"),
            _zero_or_missing(f"{PREFIX}_formal_hc_pending"),
            _zero_or_missing(f"{PREFIX}_formal_hc_active"),
        ]
    if mid == 275:
        refusal_only = (
            f"has_variable = zg361_ch_hc_reserved var:zg361_ch_hc_reserved >= 1 "
            f"has_variable = {PREFIX}_m266_hc_reservation_active var:{PREFIX}_m266_hc_reservation_active = 1 "
            f"has_variable = {PREFIX}_m266_hc_receipt var:{PREFIX}_m266_hc_receipt = $TICKET_CASE$ "
            f"has_variable = {PREFIX}_offer_gold_reserved var:{PREFIX}_offer_gold_reserved >= 15 "
            f"has_variable = {PREFIX}_gold_reserved var:{PREFIX}_gold_reserved >= 15 "
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_ad_hc_flight_pending "
            f"var:{PREFIX}_ad_hc_flight_pending = 1 var:{PREFIX}_ad_hc_flight_subject = $TICKET_SUBJECT$ "
            f"var:{PREFIX}_ad_hc_flight_cycle = $TICKET_CYCLE$ var:{PREFIX}_ad_hc_flight_case = $TICKET_CASE$ }} "
            f"{' '.join(_ad_offer_source_checks(response=2))}"
        )
        if choice == 1:
            refusal_only += (
                f" has_variable = {PREFIX}_m267_runner_up "
                f"has_variable = {PREFIX}_m267_runner_up_evidence "
                f"has_variable = {PREFIX}_m267_runner_up_present "
                f"var:{PREFIX}_m267_runner_up_present = 1 "
                f"NOT = {{ var:{PREFIX}_m267_runner_up = $TICKET_SUBJECT$ }}"
            )
        checks.append(
            f"trigger_if = {{ limit = {{ has_variable = {PREFIX}_m274_hired "
            f"var:{PREFIX}_m274_hired = 1 }} has_variable = {PREFIX}_formal_hc_active "
            f"var:{PREFIX}_formal_hc_active = 1 has_variable = zg361_ch_hc_occupied "
            f"var:zg361_ch_hc_occupied >= 1 }} trigger_else = {{ {refusal_only} }}"
        )
    if mid == 269:
        checks.append(
            f"trigger_if = {{ limit = {{ has_variable = {PREFIX}_m274_hired "
            f"var:{PREFIX}_m274_hired = 1 }} has_variable = {PREFIX}_formal_hc_active "
            f"var:{PREFIX}_formal_hc_active = 1 has_variable = {PREFIX}_m274_probation_due_cycle "
            f"var:{PREFIX}_m274_hire_case = $TICKET_CASE$ }} trigger_else = {{ "
            f"has_variable = {PREFIX}_m275_refusal var:{PREFIX}_m275_refusal = 1 "
            f"has_variable = {PREFIX}_m275_hold_pending var:{PREFIX}_m275_hold_pending = 1 "
            f"has_variable = {PREFIX}_m275_not_applicable_hired "
            f"var:{PREFIX}_m275_not_applicable_hired = 0 }}"
        )
    if mid == 276:
        for name in (
            "ready", "consumed", "id", "historical_case_id", "historical_case_hash",
            "historical_cycle", "growth_evidence_id", "growth_evidence_hash",
            "future_cohort_cycle",
        ):
            checks.append(f"has_variable = {PREFIX}_ad_external_rehire_{name}")
        for name in ("owner", "subject", "cycle", "case", "state"):
            checks.append(f"has_variable = {PREFIX}_ad_rehire_history_{name}")
        checks += [
            f"var:{PREFIX}_ad_external_rehire_ready = 1",
            f"var:{PREFIX}_ad_external_rehire_consumed = 0",
            f"var:{PREFIX}_ad_external_rehire_historical_case_id > 0",
            f"NOT = {{ var:{PREFIX}_ad_external_rehire_historical_case_id = $TICKET_CASE$ }}",
            f"var:{PREFIX}_ad_external_rehire_historical_case_hash > 0",
            f"var:{PREFIX}_ad_external_rehire_historical_cycle < $TICKET_CYCLE$",
            f"var:{PREFIX}_ad_external_rehire_growth_evidence_id > 0",
            f"var:{PREFIX}_ad_external_rehire_growth_evidence_hash > 0",
            f"var:{PREFIX}_ad_external_rehire_future_cohort_cycle > $TICKET_CYCLE$",
            f"var:{PREFIX}_ad_rehire_history_owner = $TICKET_OWNER$",
            f"var:{PREFIX}_ad_rehire_history_subject = $TICKET_SUBJECT$",
            f"var:{PREFIX}_ad_rehire_history_cycle = $TICKET_CYCLE$",
            f"var:{PREFIX}_ad_rehire_history_case = $TICKET_CASE$",
            f"var:{PREFIX}_ad_rehire_history_state = 6",
        ]
    if mid == 277:
        checks += [
            f"has_variable = {PREFIX}_m274_hired",
            f"var:{PREFIX}_m274_hired = 1",
            f"has_variable = {PREFIX}_m274_hire_case",
            f"var:{PREFIX}_m274_hire_case = $TICKET_CASE$",
            f"has_variable = {PREFIX}_m269_outcome_settled",
            f"var:{PREFIX}_m269_outcome_settled = 1",
            f"has_variable = {PREFIX}_m269_not_applicable_no_hire",
            f"var:{PREFIX}_m269_not_applicable_no_hire = 0",
            f"has_variable = {PREFIX}_formal_hc_active",
            f"var:{PREFIX}_formal_hc_active = 1",
            f"has_variable = {PREFIX}_formal_hc_active_case",
            f"var:{PREFIX}_formal_hc_active_case = $TICKET_CASE$",
            "has_variable = zg361_ch_hc_occupied",
            "var:zg361_ch_hc_occupied >= 1",
            f"has_variable = {PREFIX}_m274_position_type_id",
            f"var:{PREFIX}_m274_position_type_id > 0",
        ]
        for name in B2_PIP_SOURCE_FIELDS:
            checks.append(f"has_variable = zg361_b2_workforce_pip_{name}")
        for name in (
            "receipt_id", "receipt_hash", "former_slot_id", "displaced_hours",
            "displaced_cost_receipt",
        ):
            checks.append(f"has_variable = {PREFIX}_ad_external_exit_{name}")
        checks += [
            f"has_variable = {PREFIX}_ad_external_pip_exit_ready",
            f"has_variable = {PREFIX}_ad_external_pip_exit_consumed",
            f"var:{PREFIX}_ad_external_pip_exit_ready = 1",
            f"var:{PREFIX}_ad_external_pip_exit_consumed = 0",
            "var:zg361_b2_workforce_pip_pending = 1",
            "var:zg361_b2_workforce_pip_consumed = 0",
            "var:zg361_b2_workforce_pip_owner = $TICKET_OWNER$",
            "var:zg361_b2_workforce_pip_subject = $TICKET_SUBJECT$",
            "var:zg361_b2_workforce_pip_cycle > 0",
            "var:zg361_b2_workforce_pip_case > 0",
            "OR = { var:zg361_b2_workforce_pip_state = 3 var:zg361_b2_workforce_pip_state = 4 }",
            "var:zg361_b2_workforce_pip_case_id > 0",
            "NOT = { var:zg361_b2_workforce_pip_case_id = $TICKET_CASE$ }",
            "var:zg361_b2_workforce_pip_case_hash > 0",
            "var:zg361_b2_workforce_pip_closure_receipt_id > 0",
            "var:zg361_b2_workforce_pip_closure_receipt_hash > 0",
            "NOT = { var:zg361_b2_workforce_pip_case_id = var:zg361_b2_workforce_pip_closure_receipt_id }",
            "NOT = { var:zg361_b2_workforce_pip_case_hash = var:zg361_b2_workforce_pip_closure_receipt_hash }",
            f"var:{PREFIX}_ad_external_exit_receipt_id > 0",
            f"var:{PREFIX}_ad_external_exit_receipt_hash > 0",
            f"var:{PREFIX}_ad_external_exit_former_slot_id > 0",
            f"var:{PREFIX}_ad_external_exit_displaced_hours >= 0",
            f"var:{PREFIX}_ad_external_exit_displaced_cost_receipt > 0",
            f"NOT = {{ var:{PREFIX}_ad_external_exit_receipt_id = var:zg361_b2_workforce_pip_case_id }}",
            f"NOT = {{ var:{PREFIX}_ad_external_exit_receipt_id = var:zg361_b2_workforce_pip_closure_receipt_id }}",
            f"NOT = {{ var:{PREFIX}_ad_external_exit_receipt_hash = var:zg361_b2_workforce_pip_case_hash }}",
            f"NOT = {{ var:{PREFIX}_ad_external_exit_receipt_hash = var:zg361_b2_workforce_pip_closure_receipt_hash }}",
        ]
    if mid == 355 and choice == 1:
        checks += _gold_check(10) + [f"var:zg361_case_{d}_owner = {{ gold >= 10 }}"]
    if mid == 360:
        checks += [
            f"has_variable = {PREFIX}_al_external_stage_receipts_verified",
            f"var:{PREFIX}_al_external_stage_receipts_verified = 1",
        ]
        if choice in (1, 2):
            checks += _collective_external_checks(choice)
        else:
            checks += [
                f"{_zero_or_missing(f'{PREFIX}_al_external_collective_submission_active')}",
                f"$TICKET_OWNER$ = {{\n{indent(chr(10).join(_central_m360_owner_checks(1)))}\n}}",
            ]
    if mid == 361:
        checks += _gold_check(5 if choice == 1 else 10) + [
            f"has_variable = {PREFIX}_al_external_stage_receipts_verified",
            f"var:{PREFIX}_al_external_stage_receipts_verified = 1",
            f"var:zg361_case_{d}_owner = {{ zg361_is_celestial_liege_trigger = yes }}",
            f"var:zg361_case_{d}_owner = {{ has_variable = {PREFIX}_realm_charter_current_version has_variable = zg361_review_serial var:zg361_review_serial >= 3 }}",
            f"var:zg361_case_{d}_owner = {{ trigger_if = {{ limit = {{ exists = liege }} NOT = {{ liege = {{ zg361_is_celestial_liege_trigger = yes }} }} }} trigger_else = {{ always = yes }} }}",
            *_charter_evidence_checks(),
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
            _set(f"m{mid}_debt_state", "$TICKET_STATE$"),
            _set(f"m{mid}_debt_type_code", mid),
            _set(
                f"m{mid}_debt_id",
                f"{{ value = $TICKET_CYCLE$ multiply = 1000000 add = {{ value = $TICKET_CASE$ multiply = 1000 }} add = {mid} }}",
            ),
            _set(f"m{mid}_debt_consumer_contract", mid),
            _set(f"m{mid}_debt_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"),
            _set(f"m{mid}_debt_open", 1),
            _set(f"m{mid}_debt_consumed", 0),
            _set(f"m{mid}_debt_escalation_count", 0),
            _set(f"m{mid}_business_object_created", 0),
            _change("policy_debt", 1),
            f"trigger_event = {{ id = {NAMESPACE}.{DEBT_EVENT[mid]} days = 365 }}",
        ]
        if mid == 361:
            lines += [
                _set("m361_evidence_ready", 0),
                _set("m361_evidence_consumed", 0),
                _set("m361_evidence_deferred", 1),
            ]
        if mid == 360:
            lines += [
                f"remove_variable = {PREFIX}_al_external_collective_submission_sealed",
                f"remove_variable = {PREFIX}_al_external_collective_submission_consumed",
                f"remove_variable = {PREFIX}_al_external_collective_route",
                _set("m360_event_queued", 0),
            ]
        return lines

    lines += [
        _set(f"m{mid}_business_object_created", 1),
        _set(f"m{mid}_object_type_code", mid),
        _set(f"m{mid}_object_{spec.object_type}", 1),
        _set(f"m{mid}_object_owner", "$TICKET_OWNER$"),
        _set(f"m{mid}_object_subject", "$TICKET_SUBJECT$"),
        _set(f"m{mid}_object_cycle", "$TICKET_CYCLE$"),
        _set(f"m{mid}_object_case", "$TICKET_CASE$"),
        _set(f"m{mid}_object_state", spec.state),
        _set(f"m{mid}_object_id", f"{{ value = $TICKET_CASE$ multiply = 1000 add = {mid} }}"),
        _set(f"m{mid}_consumer_contract", mid),
        _set(f"m{mid}_object_consumed", 0),
    ]
    for resource_book in spec.resource_books:
        lines.append(_set(f"m{mid}_resource_{resource_book}", 1))
    if spec.deadline_cycles:
        lines.append(
            _set(
                f"m{mid}_object_due_cycle",
                f"{{ value = $TICKET_CYCLE$ add = {spec.deadline_cycles} }}",
            )
        )
    # AB: authorised hours, overtime liabilities, meetings and leave all reconcile.
    if mid == 242:
        lines += [_change("hours_available", -20), _change("hours_output", 20), _set("m242_presence_hours", 30), _set("m242_output_hours", 20), _set("m242_presence_rewarded", 0 if choice == 1 else 1)]
    elif mid == 243:
        hours = 2 if choice == 1 else 4
        lines += [_change("hours_available", -hours), _change("hours_on_call", hours), _set("m243_urgency_frozen", 1), _set("m243_mandatory_for_all", 0 if choice == 1 else 1)]
    elif mid == 244:
        lines += [_change("hours_available", -5), _change("hours_output", 5), _change("gold_available", -10), _change("gold_paid", 10), _set("m244_refusal_protected", 1 if choice == 1 else 0), f"var:zg361_case_{d}_owner = {{ remove_short_term_gold = 10 }}", "add_gold = 10"]
    elif mid == 245:
        lines += [_change("overtime_pending", 5), _set("m245_overtime_hours", 5), _set("m245_approved", 1 if choice == 1 else 0), _set("m245_shadow_provenance", 0 if choice == 1 else 1)]
    elif mid == 246:
        lines += [_change("overtime_pending", -5), _set("m246_compensated_hours", 5)]
        if choice == 1:
            lines += [_change("gold_available", -15), _change("gold_paid", 15), _set("m246_compensation_route", 1), f"var:zg361_case_{d}_owner = {{ remove_short_term_gold = 15 }}", "add_gold = 15"]
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
        lines += [_change("shadow_hc_available", -1), _change("shadow_hc_active", 1), _change("gold_available", -20), _change("gold_reserved", 20), _change("contract_gold_reserved", 20), _set("m254_contract_id", "$TICKET_CASE$"), _set("m254_vendor_id", "$TICKET_SUBJECT$"), _set("m254_contract_type", 2), _set("m254_shadow_hc_units", 1), _set("m254_budget_gold", 20), _set("m254_start_cycle", "$TICKET_CYCLE$"), _set("m254_sunset_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m254_formal_hc_touched", 0)]
    elif mid == 255:
        lines += [_set("m255_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m255_formal_tco", 120), _set("m255_external_tco", 110), _set("m255_mixed_tco", 100), _set("m255_selected_tco", 100 if choice == 1 else 110)]
    elif mid == 256:
        lines += [_set("m256_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m256_actual_executor", f"var:{PREFIX}_m261_actual_executor"), _set("m256_delivery_score", 80), _set("m256_quality_score", 80), _set("m256_sla_score", 80), _set("m256_external_pool_separate", 1 if choice == 1 else 0), _set("m256_external_entries_in_formal_cohort", 0 if choice == 1 else 1), _set("m256_displaced_formal_members", 0 if choice == 1 else 1)]
    elif mid == 257:
        lines += ["change_variable = { name = zg361_ch_hc_available add = -1 }", "change_variable = { name = zg361_ch_hc_reserved add = 1 }", _set("m257_conversion_pending", 1), _set("m257_conversion_official", "$TICKET_SUBJECT$"), _set("m257_recruitment_ref", "$TICKET_CASE$"), _set("m257_effective_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("formal_hc_pending", 1), _set("formal_hc_pending_owner", "$TICKET_OWNER$"), _set("formal_hc_pending_case", "$TICKET_CASE$"), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[257]} days = 365 }}"]
    elif mid == 258:
        lines += [_set("m258_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m258_missing_access_count", 1), _set("m258_target_adjustment", 20 if choice == 1 else 0), _set("m258_formal_grade_written", 0), _set("m258_governance_risk", 0 if choice == 1 else 1)]
    elif mid == 259:
        client, vendor = ((3000, 7000) if choice == 1 else (0, 10000))
        lines += [_set("m259_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m259_incident_id", "$TICKET_CASE$"), _set("m259_client_change_bps", client), _set("m259_vendor_management_bps", vendor), _set("m259_responsibility_total_bps", 10000), _set("m259_formal_grade_written", 0)]
    elif mid == 260:
        lines += [_set("m260_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m260_contract_type", f"var:{PREFIX}_m254_contract_type"), _set("m260_ownership_frozen", 1 if choice == 1 else 0), _set("m260_change_rule_frozen", 1 if choice == 1 else 0)]
    elif mid == 261:
        lines += [_set("m261_contract_id", f"var:{PREFIX}_m254_contract_id"), _set("m261_vendor_id", f"var:{PREFIX}_m254_vendor_id"), _set("m261_actual_executor", "$TICKET_SUBJECT$"), _set("m261_chain_depth", 3 if choice == 1 else 5), _set("m261_actual_executor_frozen", 1), _set("m261_chain_acyclic", 1 if choice == 1 else 0)]
    elif mid == 262:
        home, host = ((40, 60) if choice == 1 else (0, 100))
        lines += [_set("m262_seconded_official", "$TICKET_SUBJECT$"), _set("m262_home_manager", "$TICKET_OWNER$"), _set("m262_host_manager", f"var:{PREFIX}_ac_external_secondment_host_manager"), _set("m262_home_weight", home), _set("m262_host_weight", host), _set("m262_weight_total", 100), _set("m262_cost_booked_once", 1), _set("m262_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m262_review_pending", 1), _set("ac_s05_deadline_pending", 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[262]} days = 365 }}"]
    elif mid == 263:
        if choice == 1:
            lines += [_set("m263_return_choice", 1), _set("m263_prior_identity_preserved", 1), _set("m263_extension_terminal", 0), _set("m263_terminal_choice", 1), _set("m263_resolved_choice", 1), _set("m263_due_cycle", "$TICKET_CYCLE$")]
        else:
            lines += [_set("m263_return_choice", 0), _set("m263_prior_identity_preserved", 1), _set("m263_extension_terminal", 0), _set("m263_terminal_choice", 0), _set("m263_resolved_choice", 0), _set("m263_extension_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("m263_extension_pending", 1), _set("m263_extension_count", 1), _set("ac_s05_deadline_pending", 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[263]} days = 365 }}"]
    elif mid == 264:
        lines += [
            _set("m264_accepted_by", "$TICKET_OWNER$"),
            _set("m264_payee", f"var:{PREFIX}_m254_vendor_id"),
            _set("m264_vendor_identity", f"var:{PREFIX}_m254_vendor_id"),
            _set("m264_contract_id", f"var:{PREFIX}_m254_contract_id"),
            _set("m264_sunset_cycle", f"var:{PREFIX}_m254_sunset_cycle"),
            _set("m264_early_waiver_used", 0),
            _set("m264_handoff_outcome", choice),
            _set("m264_accepted_by_frozen", 1),
        ]
        if choice == 1:
            lines += [
                _change("gold_reserved", -20), _change("gold_paid", 20),
                _change("contract_gold_reserved", -20), _change("contract_gold_paid", 20),
                _set("m264_artifact_count", 3),
                _set("m264_documentation_id", f"var:{PREFIX}_m264_documentation_receipt_id"),
                _set("m264_shadowing_id", f"var:{PREFIX}_m264_shadowing_receipt_id"),
                _set("m264_practical_id", f"var:{PREFIX}_m264_practical_receipt_id"),
                _set("m264_documentation_source_object", f"var:{PREFIX}_m264_handoff_documentation_source_object"),
                _set("m264_shadowing_source_object", f"var:{PREFIX}_m264_handoff_shadowing_source_object"),
                _set("m264_practical_source_object", f"var:{PREFIX}_m264_handoff_practical_source_object"),
                _set("m264_documentation_accepted", 1), _set("m264_shadowing_accepted", 1),
                _set("m264_practical_acceptance", 1), _set("m264_payment_settled", 1),
                f"var:zg361_case_{d}_owner = {{ remove_short_term_gold = 20 }}", "add_gold = 20",
            ]
        else:
            lines += [
                _change("gold_reserved", -20), _change("gold_available", 20),
                _change("contract_gold_reserved", -20), _set("m264_artifact_count", 0),
                _set("m264_rejection_reason", f"var:{PREFIX}_m264_handoff_refusal_reason"),
                _set("m264_documentation_accepted", 0), _set("m264_shadowing_accepted", 0),
                _set("m264_practical_acceptance", 0), _set("m264_payment_settled", 0),
                _set("m264_payment_refunded", 20),
            ]
        lines += [
            f"if = {{ limit = {{ trigger_if = {{ limit = {{ has_variable = {PREFIX}_m257_conversion_settled }} NOT = {{ var:{PREFIX}_m257_conversion_settled = 1 }} }} trigger_else = {{ always = yes }} }} change_variable = {{ name = {PREFIX}_shadow_hc_active add = -1 }} change_variable = {{ name = {PREFIX}_shadow_hc_available add = 1 }} }}",
            _set("m264_shadow_hc_released", 1),
            _set("m264_handoff_flow_consumed", 1),
            _set("m264_handoff_flow_active", 0),
        ]
    elif mid == 265:
        if choice == 1:
            lines += [_change("gold_paid", -5), _change("gold_available", 5), _change("contract_gold_paid", -5), _change("contract_gold_recovered", 5), _set("m265_evidence_count", 2), _set("m265_incident_evidence", f"var:{PREFIX}_m259_write_case"), _set("m265_executor_evidence", f"var:{PREFIX}_m261_write_case"), _set("m265_vendor_actor", "$TICKET_SUBJECT$"), _set("m265_liable_manager", "$TICKET_OWNER$"), _set("m265_manager_duty_evidence", f"var:{PREFIX}_m259_write_case"), _set("m265_recovery_payee", "$TICKET_OWNER$"), _set("m265_recovery_source", "$TICKET_SUBJECT$"), _set("m265_liability_total_bps", 10000), _set("m265_actor_identity_verified", 1), _set("m265_suspicion_only", 0), _set("m265_investigation_pending", 0), "remove_short_term_gold = 5", f"var:zg361_case_{d}_owner = {{ add_gold = 5 }}"]
        else:
            lines += [_set("m265_evidence_count", 0), _set("m265_actor_identity_verified", 0), _set("m265_suspicion_only", 1), _set("m265_management_chain_frozen", 1), _set("m265_investigation_pending", 1), _set("m265_recovery_gold", 0), _change("manager_score", -5)]
    # AD: one shared HC reservation, immutable votes, delayed outcome and holds.
    elif mid == 266:
        lines += ["change_variable = { name = zg361_ch_hc_available add = -1 }", "change_variable = { name = zg361_ch_hc_reserved add = 1 }", _set("m266_standard_bar", 70), _set("m266_selected_bar", 70 if choice == 1 else 60), _set("m266_urgency_level", 2 if choice == 1 else 4), _set("m266_hc_receipt", "$TICKET_CASE$"), _set("m266_hc_reservation_active", 1), _set("m266_vacancy_serial", "$TICKET_CASE$"), f"var:zg361_case_{d}_owner = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 1 }} set_variable = {{ name = {PREFIX}_ad_hc_flight_subject value = $TICKET_SUBJECT$ }} set_variable = {{ name = {PREFIX}_ad_hc_flight_cycle value = $TICKET_CYCLE$ }} set_variable = {{ name = {PREFIX}_ad_hc_flight_case value = $TICKET_CASE$ }} }}"]
    elif mid == 267:
        lines += [_set("m267_panel_source_id", "var:zg361_wad_panel_source_id"), _set("m267_panel_source_hash", "var:zg361_wad_panel_source_hash"), _set("m267_vote_count", 3), _set("m267_evidence_count", 3), _set("m267_anchor_before_votes", 0 if choice == 1 else 1), _set("m267_candidate_frozen", f"var:{PREFIX}_m271_candidate"), _set("m267_referral_present", 1), _set("m267_referrer_voted", 0 if choice == 1 else 1), _set("m267_referral_frozen_case", "$TICKET_CASE$")]
        lines += [_set("m267_referral_id", f"var:{PREFIX}_m271_referral_id"), _set("m267_referrer_frozen", f"var:{PREFIX}_m271_referrer"), _set("m267_referral_relationship", f"var:{PREFIX}_m271_relationship_ref"), _set("m267_referral_evidence_receipt", f"var:{PREFIX}_m271_evidence_receipt"), _set("m267_referral_reward", f"var:{PREFIX}_m271_reward_gold"), _set("m267_referrer_excluded_before_seal", 1 if choice == 1 else 0)]
        for slot in (1, 2, 3):
            lines += [_set(f"m267_interviewer_{slot}", f"var:zg361_wad_panel_source_interviewer_{slot}"), _set(f"m267_vote_{slot}", f"var:zg361_wad_panel_source_vote_{slot}"), _set(f"m267_vote_evidence_{slot}", f"var:zg361_wad_panel_source_vote_evidence_{slot}")]
        lines += [_set("m267_runner_up_present", "var:zg361_wad_panel_runner_up_present")]
        lines.append(
            f"if = {{ limit = {{ var:zg361_wad_panel_runner_up_present = 1 }} "
            f"set_variable = {{ name = {PREFIX}_m267_runner_up value = var:zg361_wad_panel_source_runner_up }} "
            f"set_variable = {{ name = {PREFIX}_m267_runner_up_evidence value = var:zg361_wad_panel_source_runner_up_evidence }} }} "
            f"else = {{ remove_variable = {PREFIX}_m267_runner_up remove_variable = {PREFIX}_m267_runner_up_evidence }}"
        )
        if choice == 2:
            lines += [_change("gold_reserved", -5), _change("gold_paid", 5), _change("referral_gold_reserved", -5), _change("referral_gold_paid", 5), _set("m271_internal_owner_credit", 5), _set("m271_reward_paid_before_probation", 1), _set("m271_reward_payee", f"var:{PREFIX}_m271_referrer"), _set("m271_reward_escrowed", 0), f"var:{PREFIX}_m271_referrer = {{ add_gold = 5 }}"]
        # The seal is the commit marker for the complete identity/vote/evidence
        # snapshot, so it must be the last #267 business write.
        lines += [_set("m267_raw_votes_frozen", 1)]
    elif mid == 268:
        lines += [_set("m268_calibration_snapshot", "$TICKET_CASE$"), _set("m268_raw_votes_preserved", 1), _set("m268_adjustment_bound", 20 if choice == 1 else 100), _set("m268_training_required", 1 if choice == 1 else 0)]
    elif mid == 269:
        hired_lines = [_set("m269_not_applicable_no_hire", 0), _set("m269_no_hire_consumed", 0), _set("m269_outcome_settled", 0), _set("m269_outcome_pending", 1), _set("m269_raw_vote_snapshot", 1), _set("m269_attribution_pending", 1), _set("m269_observed_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"), _set("ad_s05_deadline_pending", 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[269]} days = 365 }}"]
        no_hire_lines = [_set("m269_not_applicable_no_hire", 1), _set("m269_outcome_settled", 0), _set("m269_outcome_pending", 0), _set("m269_attribution_pending", 0), _set("m269_refusal_case", f"var:{PREFIX}_m275_object_case"), _set("m269_refusal_reason_id", f"var:{PREFIX}_m275_refusal_reason_id"), _set("m269_no_hire_consumed", 1)]
        lines.append(
            f"if = {{ limit = {{ has_variable = {PREFIX}_m274_hired "
            f"var:{PREFIX}_m274_hired = 1 }}\n{indent(chr(10).join(hired_lines))}\n}}\n"
            f"else = {{\n{indent(chr(10).join(no_hire_lines))}\n}}"
        )
    elif mid == 270:
        lines += [_set("m270_role_class", 1 if choice == 1 else 4), _set("m270_threshold", 75 if choice == 1 else 85), _set("m270_policy_version", "$TICKET_CYCLE$"), _set("m270_raw_votes_rewritten", 0)]
    elif mid == 271:
        lines += [_change("gold_available", -5), _change("gold_reserved", 5), _change("referral_gold_reserved", 5), _set("m271_referral_source_id", "var:zg361_wad_referral_source_id"), _set("m271_referral_source_hash", "var:zg361_wad_referral_source_hash"), _set("m271_candidate", "$TICKET_SUBJECT$"), _set("m271_referral_id", "var:zg361_wad_referral_source_referral_id"), _set("m271_referrer", "var:zg361_wad_referral_source_referrer"), _set("m271_relationship_ref", "var:zg361_wad_referral_source_relationship"), _set("m271_evidence_receipt", "var:zg361_wad_referral_source_evidence_receipt"), _set("m271_reward_gold", 5), _set("m271_referrer_not_candidate", 1), _set("m271_relationship_disclosed", 1 if choice == 1 else 0), _set("m271_referrer_recused_before_vote", 1 if choice == 1 else 0), _set("m271_referrer_vote_policy", 0 if choice == 1 else 1), _set("m271_reward_due_after_probation", 1 if choice == 1 else 0), _set("m271_reward_paid_before_probation", 0), _set("m271_reward_escrowed", 1), f"var:zg361_case_{d}_owner = {{ remove_short_term_gold = 5 }}"]
    elif mid == 272:
        lines += [_change("gold_available", -10), _change("gold_reserved", 10), _change("offer_gold_reserved", 10), _set("m272_offer_candidate", "$TICKET_SUBJECT$"), _set("m272_offer_approver", "$TICKET_OWNER$"), _set("m272_offer_terms_frozen", 1), _set("m272_requested_level", 5 if choice == 1 else 6), _set("m272_cross_team_approver", 1 if choice == 1 else 0), _set("m272_premium_end_cycle", "{ value = $TICKET_CYCLE$ add = 1 }")]
    elif mid == 273:
        lines += [_set("candidate_active", 1), _set("candidate_active_owner", "$TICKET_OWNER$"), _set("candidate_active_case", "$TICKET_CASE$"), _set("m273_candidate_fingerprint", "$TICKET_SUBJECT$"), _set("m273_owner_frozen", "$TICKET_OWNER$"), _set("m273_scout_credit_bps", 3000 if choice == 1 else 10000), _set("m273_hiring_credit_bps", 7000 if choice == 1 else 0), _set("m273_credit_total_bps", 10000), _set("m273_additional_hc_reserved", 0)]
    elif mid == 274:
        lines += [_change("gold_available", -5), _change("gold_reserved", 5), _change("offer_gold_reserved", 5), _set("m274_offer_source_id", "var:zg361_wad_offer_source_id"), _set("m274_offer_source_hash", "var:zg361_wad_offer_source_hash"), _set("m274_offer_response_receipt", "var:zg361_wad_offer_source_response_receipt"), _set("m274_offer_response", choice), _set("m274_counter_used", 1), _set("m274_counter_amount", 5 if choice == 1 else 15), _set("m274_fairness_cap", 10), _set("m274_offer_acceptance_candidate", 1 if choice == 1 else 0), _set("m274_hired", 0)]
        if choice == 1:
            lines += [
                _set("m274_appointed_character", "$TICKET_SUBJECT$"),
                _set("m274_position_type_id", f"var:{PREFIX}_ad_external_position_type_id"),
                _set("m274_position_receipt_id", f"var:{PREFIX}_ad_external_position_receipt_id"),
                _set("m274_position_receipt_hash", f"var:{PREFIX}_ad_external_position_receipt_hash"),
                _set("m274_native_appointment_confirmed", 1),
                _change("gold_reserved", -15), _change("gold_paid", 15),
                _change("offer_gold_reserved", -15), _change("offer_gold_paid", 15),
                "change_variable = { name = zg361_ch_hc_reserved add = -1 }",
                "change_variable = { name = zg361_ch_hc_occupied add = 1 }",
                _set("m266_hc_reservation_active", 0), _set("candidate_active", 0),
                _set("formal_hc_active", 1), _set("formal_hc_active_case", "$TICKET_CASE$"),
                _set("m274_hired", 1), _set("m274_hire_case", "$TICKET_CASE$"),
                _set("m274_probation_due_cycle", "{ value = $TICKET_CYCLE$ add = 1 }"),
                _set("ad_external_appointment_consumed", 1),
                _set("ad_external_appointment_ready", 0),
                f"var:zg361_case_{d}_owner = {{ remove_short_term_gold = 15 set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 0 }} }}",
                "add_gold = 15",
            ]
    elif mid == 275:
        due_add = 1 if choice == 1 else 3
        refusal_lines = [_set("m275_offer_source_id", "var:zg361_wad_offer_source_id"), _set("m275_offer_source_hash", "var:zg361_wad_offer_source_hash"), _set("m275_offer_response_receipt", "var:zg361_wad_offer_source_response_receipt"), _set("m275_refusal", 1), _set("m275_not_applicable_hired", 0), _set("m275_refusal_reason_id", "var:zg361_wad_offer_source_refusal_reason_id"), _set("m275_original_candidate", "$TICKET_SUBJECT$"), _set("m275_hold_start_cycle", "$TICKET_CYCLE$"), _set("m275_hold_due_cycle", f"{{ value = $TICKET_CYCLE$ add = {due_add} }}"), _set("m275_hc_lineage_receipt", "$TICKET_CASE$"), _set("m275_hold_pending", 1), _set("m275_runner_attempt_new_case", 1 if choice == 1 else 0), _set("m275_policy_breach_indefinite_requested", 1 if choice == 2 else 0), f"trigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[275]} days = {90 if choice == 1 else 365} }}"]
        if choice == 1:
            refusal_lines += [_set("m275_runner_up", f"var:{PREFIX}_m267_runner_up"), _set("m275_runner_up_evidence", f"var:{PREFIX}_m267_runner_up_evidence"), _set("m275_runner_reopen_pending", 0)]
        else:
            refusal_lines += [
                _set("m275_reason_remediated", 0),
                f"trigger_event = {{ id = {NAMESPACE}.{REMEDIATION_OPEN_EVENT} days = 1 }}",
            ]
        refusal_lines += [_change("gold_reserved", -15), _change("gold_available", 15), _change("offer_gold_reserved", -15), _change("offer_gold_refunded", 15), _set("candidate_active", 0), f"if = {{ limit = {{ has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 }} change_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_available add = 5 }} set_variable = {{ name = {PREFIX}_m271_reward_refunded value = 1 }} set_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }} var:zg361_case_{d}_owner = {{ add_gold = 5 }} }}"]
        hired_lines = [
            _set("m275_refusal", 0),
            _set("m275_not_applicable_hired", 1),
            _set("m275_hire_case", f"var:{PREFIX}_m274_hire_case"),
            _set("m275_hc_lineage_receipt", f"var:{PREFIX}_m266_hc_receipt"),
            _set("m275_hold_pending", 0),
            _set("m275_hc_held", 0),
            _set("m275_resources_touched", 0),
        ]
        lines.append(
            f"if = {{ limit = {{ has_variable = {PREFIX}_m274_hired "
            f"var:{PREFIX}_m274_hired = 1 }}\n{indent(chr(10).join(hired_lines))}\n}}\n"
            f"else = {{\n{indent(chr(10).join(refusal_lines))}\n}}"
        )
    elif mid == 276:
        lines += [
            _set("m276_rehire_id", f"var:{PREFIX}_ad_external_rehire_id"),
            _set("m276_rehire_candidate", "$TICKET_SUBJECT$"),
            _set("m276_old_case_id", f"var:{PREFIX}_ad_external_rehire_historical_case_id"),
            _set("m276_old_case_hash", f"var:{PREFIX}_ad_external_rehire_historical_case_hash"),
            _set("m276_old_cycle", f"var:{PREFIX}_ad_external_rehire_historical_cycle"),
            _set("m276_growth_evidence_id", f"var:{PREFIX}_ad_external_rehire_growth_evidence_id"),
            _set("m276_growth_evidence_hash", f"var:{PREFIX}_ad_external_rehire_growth_evidence_hash"),
            _set("m276_future_cohort_cycle", f"var:{PREFIX}_ad_external_rehire_future_cohort_cycle"),
            _set("m276_old_history_retained", 1),
            _set("m276_growth_evidence_frozen", 1 if choice == 1 else 0),
            _set("m276_history_wipe_attempt", 0 if choice == 1 else 1),
            _set("m276_hc_touched", 0),
            _set("ad_external_rehire_consumed", 1),
            _set("ad_external_rehire_ready", 0),
        ]
    elif mid == 277:
        lines += [
            "change_variable = { name = zg361_ch_hc_occupied add = -1 }",
            "change_variable = { name = zg361_ch_hc_frozen add = 1 }",
            _set("formal_hc_active", 0),
            _set("m277_pip_case_frozen", "var:zg361_b2_workforce_pip_case_id"),
            _set("m277_pip_case_hash", "var:zg361_b2_workforce_pip_case_hash"),
            _set("m277_pip_closure_receipt_id", "var:zg361_b2_workforce_pip_closure_receipt_id"),
            _set("m277_pip_closure_receipt_hash", "var:zg361_b2_workforce_pip_closure_receipt_hash"),
            _set("m277_exit_receipt_id", f"var:{PREFIX}_ad_external_exit_receipt_id"),
            _set("m277_exit_receipt_hash", f"var:{PREFIX}_ad_external_exit_receipt_hash"),
            _set("m277_position_type_id", f"var:{PREFIX}_m274_position_type_id"),
            _set("m277_former_slot_id", f"var:{PREFIX}_ad_external_exit_former_slot_id"),
            _set("m277_former_hc_lineage", f"var:{PREFIX}_formal_hc_active_case"),
            _set("m277_displaced_subject", "$TICKET_SUBJECT$"),
            _set("m277_displaced_hours", f"var:{PREFIX}_ad_external_exit_displaced_hours"),
            _set("m277_displaced_cost_provenance", f"var:{PREFIX}_ad_external_exit_displaced_cost_receipt"),
            _set("m277_work_proof", 1 if choice == 1 else 0),
            _set("m277_automatic_refill", 0 if choice == 1 else 1),
            _set("m277_vacant_frozen", 1), _set("m277_hc_minted", 0),
            _set("ad_external_pip_exit_consumed", 1),
            _set("ad_external_pip_exit_ready", 0),
            "set_variable = { name = zg361_b2_workforce_pip_consumed value = 1 }",
            "set_variable = { name = zg361_b2_workforce_pip_pending value = 0 }",
        ]
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
        f"{PREFIX}_m{mid}_choice",
        f"{PREFIX}_m{mid}_business_object_created",
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
    object_required_names = [
        "object_type_code",
        f"object_{spec.object_type}",
        "object_owner",
        "object_subject",
        "object_cycle",
        "object_case",
        "object_state",
        "object_id",
        "consumer_contract",
        *(f"resource_{book}" for book in spec.resource_books),
    ]
    if spec.deadline_cycles:
        object_required_names.append("object_due_cycle")
    object_required = "\n".join(
        f"\t\t\t\t\t\thas_variable = {PREFIX}_m{mid}_{name}"
        for name in object_required_names
    )
    object_equal = "\n".join((
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_type_code = {mid}",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_consumer_contract = {mid}",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_owner = var:{PREFIX}_m{mid}_write_owner",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_subject = var:{PREFIX}_m{mid}_write_subject",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_cycle = var:{PREFIX}_m{mid}_write_cycle",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_case = var:{PREFIX}_m{mid}_write_case",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_object_state = var:{PREFIX}_m{mid}_write_state",
    ))
    debt_required = "\n".join(
        f"\t\t\t\t\t\thas_variable = {PREFIX}_m{mid}_debt_{name}"
        for name in (
            "owner", "subject", "cycle", "case", "state", "type_code", "id",
            "consumer_contract", "due_cycle", "open", "consumed", "escalation_count",
        )
    )
    debt_equal = "\n".join((
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_choice = 3",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_open = 1",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_consumed = 0",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_type_code = {mid}",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_consumer_contract = {mid}",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_owner = var:{PREFIX}_m{mid}_write_owner",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_subject = var:{PREFIX}_m{mid}_write_subject",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_cycle = var:{PREFIX}_m{mid}_write_cycle",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_case = var:{PREFIX}_m{mid}_write_case",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_state = var:{PREFIX}_m{mid}_write_state",
        f"\t\t\t\t\tvar:{PREFIX}_m{mid}_debt_id = scope:{PREFIX}_m{mid}_expected_debt_id",
    ))
    return f"""# #{mid:03d} read-side projection; existence gates precede tuple reads.
{PREFIX}_m{mid}_consume_effect = {{
{indent(_debt_id_prelude(mid))}
\tif = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{
{existence}
\t\t\t\t}}
{comparisons}
\t\t\t\ttrigger_if = {{
\t\t\t\t\tlimit = {{ var:{PREFIX}_m{mid}_business_object_created = 1 }}
\t\t\t\t\ttrigger_if = {{
\t\t\t\t\t\tlimit = {{
{object_required}
\t\t\t\t\t\t}}
{object_equal}
\t\t\t\t\t}}
\t\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t\t}}
\t\t\t\ttrigger_else = {{
\t\t\t\t\ttrigger_if = {{
\t\t\t\t\t\tlimit = {{
{debt_required}
\t\t\t\t\t\t}}
{debt_equal}
\t\t\t\t\t}}
\t\t\t\t\ttrigger_else = {{ always = no }}
\t\t\t\t}}
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
\t\tif = {{ limit = {{ var:{PREFIX}_m{mid}_business_object_created = 1 }} set_variable = {{ name = {PREFIX}_m{mid}_object_consumed value = 1 }} set_variable = {{ name = {PREFIX}_m{mid}_consumer_{spec.consumer_key} value = 1 }} }}
\t\telse = {{ set_variable = {{ name = {PREFIX}_m{mid}_debt_visible_to_settlement value = 1 }} }}
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
\tTICKET_STATE = {state}
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
    if d == "ac" and mid == 263:
        return f"""{PREFIX}_ac_schedule_stage_06_deadline_effect = yes
{PREFIX}_m264_begin_handoff_effect = {{
	TICKET_OWNER = var:zg361_case_ac_owner
	TICKET_SUBJECT = this
	TICKET_CYCLE = var:zg361_case_ac_cycle_serial
	TICKET_CASE = var:zg361_case_ac_case_serial
}}"""
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
        return f"{PREFIX}_after_m360_history_gate_effect = yes"
    if d == "al" and mid == 361:
        return f"{PREFIX}_finalize_portfolio_effect = yes"
    if state < 6:
        return f"{PREFIX}_{d}_schedule_stage_{state + 1:02d}_deadline_effect = yes"
    if d == "ac":
        return f"""{PREFIX}_release_abandoned_ac_resources_effect = yes
{PREFIX}_ad_launch_effect = yes"""
    if d == "ad":
        return f"""{PREFIX}_release_abandoned_ad_resources_effect = yes
{PREFIX}_al_launch_effect = yes"""
    next_domain = NEXT_DOMAIN[d]
    if next_domain:
        return f"{PREFIX}_{next_domain}_launch_effect = yes"
    return f"{PREFIX}_finalize_portfolio_effect = yes"


def render_abandoned_resource_release() -> str:
    """Release reservations that no longer have an A/B business flight.

    Route C remains a due policy debt.  It must not, however, strand the
    finite contract/recruitment books forever after the domain case closes.
    A real #275 hold is the one explicit exception and keeps its HC lineage
    until the tuple-guarded future consumer settles it.
    """

    return f"""{PREFIX}_release_abandoned_ac_resources_effect = {{
\tif = {{
\t\tlimit = {{ has_variable = {PREFIX}_contract_gold_reserved var:{PREFIX}_contract_gold_reserved > 0 }}
\t\tset_variable = {{ name = {PREFIX}_ac_release_gold value = var:{PREFIX}_contract_gold_reserved }}
\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = {{ value = var:{PREFIX}_ac_release_gold multiply = -1 }} }}
\t\tchange_variable = {{ name = {PREFIX}_gold_available add = var:{PREFIX}_ac_release_gold }}
\t\tset_variable = {{ name = {PREFIX}_contract_gold_reserved value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_ac_abandoned_contract_refunded value = 1 }}
\t}}
\tif = {{
\t\tlimit = {{ has_variable = {PREFIX}_shadow_hc_active var:{PREFIX}_shadow_hc_active > 0 }}
\t\tset_variable = {{ name = {PREFIX}_ac_release_shadow value = var:{PREFIX}_shadow_hc_active }}
\t\tchange_variable = {{ name = {PREFIX}_shadow_hc_available add = var:{PREFIX}_ac_release_shadow }}
\t\tset_variable = {{ name = {PREFIX}_shadow_hc_active value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_ac_abandoned_shadow_released value = 1 }}
\t}}
}}

{PREFIX}_release_abandoned_ad_resources_effect = {{
\tif = {{
\t\tlimit = {{ has_variable = {PREFIX}_offer_gold_reserved var:{PREFIX}_offer_gold_reserved > 0 }}
\t\tset_variable = {{ name = {PREFIX}_ad_release_offer_gold value = var:{PREFIX}_offer_gold_reserved }}
\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = {{ value = var:{PREFIX}_ad_release_offer_gold multiply = -1 }} }}
\t\tchange_variable = {{ name = {PREFIX}_gold_available add = var:{PREFIX}_ad_release_offer_gold }}
\t\tchange_variable = {{ name = {PREFIX}_offer_gold_refunded add = var:{PREFIX}_ad_release_offer_gold }}
\t\tset_variable = {{ name = {PREFIX}_offer_gold_reserved value = 0 }}
\t}}
\tif = {{
\t\tlimit = {{ has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_gold_reserved var:{PREFIX}_gold_reserved >= 5 }}
\t\tchange_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }}
\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = -5 }}
\t\tchange_variable = {{ name = {PREFIX}_gold_available add = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m271_reward_refunded value = 1 }}
\t\tvar:zg361_case_ad_owner = {{ add_gold = 5 }}
\t}}
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m266_hc_reservation_active
\t\t\tvar:{PREFIX}_m266_hc_reservation_active = 1
\t\t\t{_zero_or_missing(f'{PREFIX}_m275_hold_pending')}
\t\t\thas_variable = zg361_ch_hc_reserved
\t\t\tvar:zg361_ch_hc_reserved >= 1
\t\t}}
\t\tchange_variable = {{ name = zg361_ch_hc_reserved add = -1 }}
\t\tchange_variable = {{ name = zg361_ch_hc_available add = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m266_hc_reservation_active value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_ad_abandoned_hc_released value = 1 }}
\t\tvar:zg361_case_ad_owner = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 0 }} }}
\t}}
\tif = {{ limit = {{ has_variable = {PREFIX}_candidate_active var:{PREFIX}_candidate_active = 1 }} set_variable = {{ name = {PREFIX}_candidate_active value = 0 }} }}
}}"""


def _ad_case_guard(state: int) -> str:
    return f"""zg361_case_kernel_full_guard_trigger = {{
	OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
	CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
	STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
	EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
	EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = {state}
}}"""


def _ad_committed_object_checks(mid: int, choices: tuple[int, ...]) -> list[str]:
    spec = by_id()[mid]
    checks = [
        f"has_variable = {PREFIX}_m{mid}_business_object_created",
        f"has_variable = {PREFIX}_m{mid}_object_owner",
        f"has_variable = {PREFIX}_m{mid}_object_subject",
        f"has_variable = {PREFIX}_m{mid}_object_cycle",
        f"has_variable = {PREFIX}_m{mid}_object_case",
        f"has_variable = {PREFIX}_m{mid}_object_state",
        f"has_variable = {PREFIX}_m{mid}_object_consumed",
        f"has_variable = {PREFIX}_m{mid}_consumer_{spec.consumer_key}",
        f"var:{PREFIX}_m{mid}_business_object_created = 1",
        f"var:{PREFIX}_m{mid}_object_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m{mid}_object_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m{mid}_object_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m{mid}_object_case = $TICKET_CASE$",
        f"var:{PREFIX}_m{mid}_object_state = {spec.state}",
        f"var:{PREFIX}_m{mid}_object_consumed = 1",
        f"var:{PREFIX}_m{mid}_consumer_{spec.consumer_key} = 1",
        "OR = {\n" + "\n".join(indent(receipt_guard(spec, choice)) for choice in choices) + "\n}",
    ]
    return checks


def _ad_committed_debt_checks(mid: int) -> list[str]:
    spec = by_id()[mid]
    checks = [
        f"has_variable = {PREFIX}_m{mid}_business_object_created",
        f"has_variable = {PREFIX}_m{mid}_choice",
        f"has_variable = {PREFIX}_m{mid}_debt_owner",
        f"has_variable = {PREFIX}_m{mid}_debt_subject",
        f"has_variable = {PREFIX}_m{mid}_debt_cycle",
        f"has_variable = {PREFIX}_m{mid}_debt_case",
        f"has_variable = {PREFIX}_m{mid}_debt_state",
        f"has_variable = {PREFIX}_m{mid}_debt_open",
        f"has_variable = {PREFIX}_m{mid}_debt_consumed",
        f"has_variable = {PREFIX}_m{mid}_debt_visible_to_settlement",
        f"has_variable = {PREFIX}_m{mid}_consumed_owner",
        f"has_variable = {PREFIX}_m{mid}_consumed_subject",
        f"has_variable = {PREFIX}_m{mid}_consumed_cycle",
        f"has_variable = {PREFIX}_m{mid}_consumed_case",
        f"has_variable = {PREFIX}_m{mid}_consumed_state",
        f"var:{PREFIX}_m{mid}_business_object_created = 0",
        f"var:{PREFIX}_m{mid}_choice = 3",
        f"var:{PREFIX}_m{mid}_debt_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m{mid}_debt_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m{mid}_debt_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m{mid}_debt_case = $TICKET_CASE$",
        f"var:{PREFIX}_m{mid}_debt_state = {spec.state}",
        f"var:{PREFIX}_m{mid}_debt_open = 1",
        f"var:{PREFIX}_m{mid}_debt_consumed = 0",
        f"var:{PREFIX}_m{mid}_debt_visible_to_settlement = 1",
        f"var:{PREFIX}_m{mid}_consumed_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m{mid}_consumed_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m{mid}_consumed_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m{mid}_consumed_case = $TICKET_CASE$",
        f"var:{PREFIX}_m{mid}_consumed_state = {spec.state}",
        receipt_guard(spec, 3),
    ]
    return checks


def _ad_referral_copy_checks() -> list[str]:
    return [
        f"has_variable = {PREFIX}_m271_referral_source_id",
        f"has_variable = {PREFIX}_m271_referral_source_hash",
        f"has_variable = {PREFIX}_m271_referral_id",
        f"has_variable = {PREFIX}_m271_referrer",
        f"has_variable = {PREFIX}_m271_relationship_ref",
        f"has_variable = {PREFIX}_m271_evidence_receipt",
        f"var:{PREFIX}_m271_referral_source_id = var:zg361_wad_referral_source_id",
        f"var:{PREFIX}_m271_referral_source_hash = var:zg361_wad_referral_source_hash",
        f"var:{PREFIX}_m271_referral_id = var:zg361_wad_referral_source_referral_id",
        f"var:{PREFIX}_m271_referrer = var:zg361_wad_referral_source_referrer",
        f"var:{PREFIX}_m271_relationship_ref = var:zg361_wad_referral_source_relationship",
        f"var:{PREFIX}_m271_evidence_receipt = var:zg361_wad_referral_source_evidence_receipt",
    ]


def _ad_panel_copy_checks() -> list[str]:
    checks = [
        f"has_variable = {PREFIX}_m267_panel_source_id",
        f"has_variable = {PREFIX}_m267_panel_source_hash",
        f"has_variable = {PREFIX}_m267_runner_up_present",
        f"var:{PREFIX}_m267_panel_source_id = var:zg361_wad_panel_source_id",
        f"var:{PREFIX}_m267_panel_source_hash = var:zg361_wad_panel_source_hash",
        f"var:{PREFIX}_m267_runner_up_present = var:zg361_wad_panel_runner_up_present",
    ]
    for slot in (1, 2, 3):
        for field in ("interviewer", "vote", "vote_evidence"):
            checks += [
                f"has_variable = {PREFIX}_m267_{field}_{slot}",
                f"var:{PREFIX}_m267_{field}_{slot} = var:zg361_wad_panel_source_{field}_{slot}",
            ]
    checks.append(
        f"trigger_if = {{ limit = {{ var:zg361_wad_panel_runner_up_present = 1 }} "
        f"has_variable = {PREFIX}_m267_runner_up has_variable = {PREFIX}_m267_runner_up_evidence "
        f"var:{PREFIX}_m267_runner_up = var:zg361_wad_panel_source_runner_up "
        f"var:{PREFIX}_m267_runner_up_evidence = var:zg361_wad_panel_source_runner_up_evidence }} "
        f"trigger_else = {{ NOT = {{ has_variable = {PREFIX}_m267_runner_up }} "
        f"NOT = {{ has_variable = {PREFIX}_m267_runner_up_evidence }} }}"
    )
    return checks


def _ad_offer_copy_checks(mid: int, response: int) -> list[str]:
    checks = [
        f"has_variable = {PREFIX}_m{mid}_offer_source_id",
        f"has_variable = {PREFIX}_m{mid}_offer_source_hash",
        f"has_variable = {PREFIX}_m{mid}_offer_response_receipt",
        f"var:{PREFIX}_m{mid}_offer_source_id = var:zg361_wad_offer_source_id",
        f"var:{PREFIX}_m{mid}_offer_source_hash = var:zg361_wad_offer_source_hash",
        f"var:{PREFIX}_m{mid}_offer_response_receipt = var:zg361_wad_offer_source_response_receipt",
    ]
    if mid == 274:
        checks += [
            f"has_variable = {PREFIX}_m274_offer_response",
            f"var:{PREFIX}_m274_offer_response = {response}",
        ]
    else:
        checks += [
            f"has_variable = {PREFIX}_m275_refusal_reason_id",
            f"var:{PREFIX}_m275_refusal_reason_id = var:zg361_wad_offer_source_refusal_reason_id",
        ]
    return checks


def _render_ad_source_consumer(
    source: str,
    *,
    mid: int,
    terminal: int,
    source_checks: list[str],
    copy_checks: list[str],
    choices: tuple[int, ...],
) -> str:
    p = f"zg361_wad_{source}_source"
    state = 4 if source == "offer" else 1
    common_consumed = _ad_source_common_checks(
        source, state=state, terminal=terminal, pending=0, consumed=1, retired=0
    )
    committed = _ad_committed_object_checks(mid, choices)
    active = [*_ad_case_guard(state).splitlines(), *source_checks, *committed, *copy_checks]
    replay = [*_ad_case_guard(state).splitlines(), *common_consumed, *committed, *copy_checks]
    return f"""{PREFIX}_consume_{source}_source_after_m{mid}_effect = {{
	remove_variable = {PREFIX}_ad_source_status
	remove_variable = {PREFIX}_ad_source_red_code
{indent(_ad_source_hash_prelude(source))}
	if = {{
		limit = {{
{indent(chr(10).join(active), 3)}
		}}
		set_variable = {{ name = {PREFIX}_{source}_source_consumed_id value = var:{p}_id }}
		set_variable = {{ name = {PREFIX}_{source}_source_consumed_hash value = var:{p}_hash }}
		set_variable = {{ name = {p}_pending value = 0 }}
		set_variable = {{ name = {p}_consumed value = 1 }} # source consume commit last
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{
		limit = {{
{indent(chr(10).join(replay), 3)}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 2 }}
	}}
	else_if = {{
		limit = {{ has_variable = {p}_pending var:{p}_pending = 1 }}
		set_variable = {{ name = {PREFIX}_ad_source_red_code value = {mid}41 }}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 4 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_ad_source_status value = 3 }} }}
}}"""


def _render_ad_source_retire(source: str, *, mid: int, terminals: tuple[int, ...]) -> str:
    p = f"zg361_wad_{source}_source"
    state = 4 if source == "offer" else 1
    source_checks = _ad_source_common_checks(source, state=state, terminal=terminals)
    committed = _ad_committed_debt_checks(mid)
    replay = _ad_source_common_checks(
        source, state=state, terminal=terminals, pending=0, consumed=0, retired=1
    ) + [
        f"has_variable = {PREFIX}_{source}_source_retired_id",
        f"has_variable = {PREFIX}_{source}_source_retired_hash",
        f"var:{PREFIX}_{source}_source_retired_id = var:{p}_id",
        f"var:{PREFIX}_{source}_source_retired_hash = var:{p}_hash",
    ]
    return f"""{PREFIX}_retire_{source}_source_after_m{mid}_debt_effect = {{
	remove_variable = {PREFIX}_ad_source_status
	remove_variable = {PREFIX}_ad_source_red_code
{indent(_ad_source_hash_prelude(source))}
	if = {{
		limit = {{
{indent(_ad_case_guard(by_id()[mid].state), 3)}
{indent(chr(10).join(source_checks), 3)}
{indent(chr(10).join(committed), 3)}
		}}
		set_variable = {{ name = {PREFIX}_{source}_source_retired_id value = var:{p}_id }}
		set_variable = {{ name = {PREFIX}_{source}_source_retired_hash value = var:{p}_hash }}
		set_variable = {{ name = {p}_pending value = 0 }}
		set_variable = {{ name = {p}_retired value = 1 }} # never marks consumed
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{
		limit = {{
{indent(chr(10).join(replay), 3)}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_ad_source_status value = 3 }} }}
}}"""


def _ad_dispatch_player_event(event_id: int) -> str:
    return f"""save_scope_as = {PREFIX}_ad_subject
$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_ad_owner }}
save_scope_value_as = {{ name = {PREFIX}_ad_cycle value = $TICKET_CYCLE$ }}
save_scope_value_as = {{ name = {PREFIX}_ad_case value = $TICKET_CASE$ }}
$TICKET_OWNER$ = {{ trigger_event = {{ id = {NAMESPACE}.{event_id} }} }}"""


def render_ad_source_integration() -> str:
    consume_referral = _render_ad_source_consumer(
        "referral", mid=271, terminal=1,
        source_checks=_ad_referral_source_checks(),
        copy_checks=_ad_referral_copy_checks(), choices=(1, 2),
    )
    consume_panel = _render_ad_source_consumer(
        "panel", mid=267, terminal=1,
        source_checks=_ad_panel_source_checks(),
        copy_checks=_ad_panel_copy_checks(), choices=(1, 2),
    )
    consume_offer_accept = _render_ad_source_consumer(
        "offer", mid=274, terminal=1,
        source_checks=_ad_offer_source_checks(response=1),
        copy_checks=_ad_offer_copy_checks(274, 1), choices=(1,),
    )
    consume_offer_refusal = _render_ad_source_consumer(
        "offer", mid=275, terminal=2,
        source_checks=_ad_offer_source_checks(response=2),
        copy_checks=_ad_offer_copy_checks(275, 2), choices=(1, 2),
    )
    retire_referral = _render_ad_source_retire("referral", mid=267, terminals=(1, 2, 3))
    retire_panel = _render_ad_source_retire("panel", mid=267, terminals=(1, 3))
    retire_offer_274 = _render_ad_source_retire("offer", mid=274, terminals=(1, 2))
    retire_offer_275 = _render_ad_source_retire("offer", mid=275, terminals=(2,))

    referral_ready = "\n".join(
        [*_ad_case_guard(1).splitlines(), *_ad_referral_source_checks(disposition=1)]
    )
    referral_na = "\n".join(
        [*_ad_case_guard(1).splitlines(), *_ad_source_common_checks("referral", state=1, terminal=(2, 3))]
    )
    panel_ready = "\n".join(
        [*_ad_case_guard(1).splitlines(), *_ad_panel_source_checks(disposition=1)]
    )
    panel_na = "\n".join(
        [*_ad_case_guard(1).splitlines(), *_ad_source_common_checks("panel", state=1, terminal=3)]
    )
    offer_accept = "\n".join(
        [*_ad_case_guard(4).splitlines(), *_ad_offer_source_checks(response=1)]
    )
    offer_refusal = "\n".join(
        [*_ad_case_guard(4).splitlines(), *_ad_offer_source_checks(response=2)]
    )
    return "\n\n".join((
        consume_referral, consume_panel, consume_offer_accept, consume_offer_refusal,
        retire_referral, retire_panel, retire_offer_274, retire_offer_275,
        f"""# An authorised AI manager cannot display the remaining AD windows after
# a typed referral/panel N/A.  Continue the exact tuple with route C at every
# later stage; these debt routes never consume a real actor source.
{PREFIX}_continue_ai_ad_after_fact_na_effect = {{
	if = {{
		limit = {{
{indent(_ad_case_guard(2), 3)}
			$TICKET_OWNER$ = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }}
		}}
		{PREFIX}_m268_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 2 }}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			{PREFIX}_m270_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 2 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 3 }}
			{PREFIX}_m272_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 3 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 4 }}
			{PREFIX}_m274_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 4 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			{PREFIX}_m275_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 4 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 5 }}
			{PREFIX}_m269_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 5 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 6 }}
			{PREFIX}_m276_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 6 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			{PREFIX}_m277_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 6 }}
		}}
	}}
}}""",
        f"""# A human candidate may refuse an AI manager's offer.  #274-B records the
# rejection, then this exact-tuple continuation records #275 before closing
# the no-hire-only tail.  The pending offer is consumed only by successful
# #275 A/B, never by #274-B itself.
{PREFIX}_continue_ai_ad_after_offer_refusal_effect = {{
	if = {{
		limit = {{
{indent(_ad_case_guard(4), 3)}
			$TICKET_OWNER$ = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_m267_runner_up_present var:{PREFIX}_m267_runner_up_present = 1 }}
			{PREFIX}_m275_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		}}
		else_if = {{
			limit = {{ has_variable = {PREFIX}_m267_runner_up_present var:{PREFIX}_m267_runner_up_present = 0 }}
			{PREFIX}_m275_route_b_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 5 }}
			{PREFIX}_m269_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 6 }}
			{PREFIX}_m276_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 6 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			{PREFIX}_m277_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 6 }}
		}}
	}}
}}""",
        f"""# Product callbacks: WAIT never advances; READY resumes the exact tuple;
# typed N/A records only route-C debt and retires (never consumes) its source.
{PREFIX}_resume_m271_from_referral_source_effect = {{
	remove_variable = {PREFIX}_ad_source_status
{indent(_ad_source_hash_prelude('referral'))}
	if = {{
		limit = {{
{indent(referral_ready, 3)}
		}}
		if = {{
			limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
			{PREFIX}_m271_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		}}
		else = {{
{indent(_ad_dispatch_player_event(271), 3)}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{
		limit = {{
{indent(referral_na, 3)}
		}}
		{PREFIX}_m271_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 1 }}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			{PREFIX}_m267_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 1 }}
		}}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 2 }}
			if = {{
				limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
				{PREFIX}_continue_ai_ad_after_fact_na_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			}}
			else = {{
{indent(_ad_dispatch_player_event(268), 4)}
			}}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{ limit = {{ has_variable = zg361_wad_referral_source_pending var:zg361_wad_referral_source_pending = 0 }} set_variable = {{ name = {PREFIX}_ad_source_status value = 5 }} }}
	else = {{ set_variable = {{ name = {PREFIX}_ad_source_status value = 4 }} }}
}}""",
        f"""{PREFIX}_resume_m267_from_panel_source_effect = {{
	remove_variable = {PREFIX}_ad_source_status
{indent(_ad_source_hash_prelude('panel'))}
	if = {{
		limit = {{
{indent(panel_ready, 3)}
		}}
		if = {{
			limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
			{PREFIX}_m267_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			if = {{ limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 2 }} {PREFIX}_m268_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }} }}
			if = {{ limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }} {PREFIX}_m270_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }} }}
			if = {{ limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 3 }} {PREFIX}_m272_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }} }}
		}}
		else = {{
{indent(_ad_dispatch_player_event(267), 3)}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{
		limit = {{
{indent(panel_na, 3)}
		}}
		{PREFIX}_m267_route_c_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ TICKET_STATE = 1 }}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_ad_state = 2 }}
			if = {{
				limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
				{PREFIX}_continue_ai_ad_after_fact_na_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			}}
			else = {{
{indent(_ad_dispatch_player_event(268), 4)}
			}}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{ limit = {{ has_variable = zg361_wad_panel_source_pending var:zg361_wad_panel_source_pending = 0 }} set_variable = {{ name = {PREFIX}_ad_source_status value = 5 }} }}
	else = {{ set_variable = {{ name = {PREFIX}_ad_source_status value = 4 }} }}
}}""",
        f"""{PREFIX}_resume_m274_from_offer_source_effect = {{
	remove_variable = {PREFIX}_ad_source_status
{indent(_ad_source_hash_prelude('offer'))}
	if = {{
		limit = {{
{indent(offer_accept, 3)}
		}}
		if = {{
			limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
			{APPOINTMENT_WRAPPER} = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			{PREFIX}_queue_m274_appointment_ack_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		}}
		else = {{
{indent(_ad_dispatch_player_event(274), 3)}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{
		limit = {{
{indent(offer_refusal, 3)}
		}}
		{PREFIX}_m274_route_b_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		if = {{
			limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }}
			if = {{
				limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
				{PREFIX}_continue_ai_ad_after_offer_refusal_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = this TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			}}
			else = {{
{indent(_ad_dispatch_player_event(275), 4)}
			}}
		}}
		set_variable = {{ name = {PREFIX}_ad_source_status value = 1 }}
	}}
	else_if = {{ limit = {{ has_variable = zg361_wad_offer_source_pending var:zg361_wad_offer_source_pending = 0 }} set_variable = {{ name = {PREFIX}_ad_source_status value = 5 }} }}
	else = {{ set_variable = {{ name = {PREFIX}_ad_source_status value = 4 }} }}
}}""",
    ))


def render_route_effect(spec: Mechanism, choice: int) -> str:
    mid, d = spec.mid, spec.domain
    letter = "abc"[choice - 1]
    guard = tuple_guard(spec)
    receipts = any_receipt(spec)
    checks = atomic_precheck(spec, choice)
    business = "\n".join(business_effects(spec, choice))
    post_consume = ""
    if mid == 360:
        post_consume = f"""
\t\t\t{PREFIX}_mark_central_m360_source_consumed_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$
\t\t\t\tTICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$
\t\t\t\tTICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    elif mid == 269 and choice == 3:
        post_consume = f"""
\t\t\tif = {{
\t\t\t\tlimit = {{ has_variable = {PREFIX}_m274_hired var:{PREFIX}_m274_hired = 1 }}
\t\t\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_DEBT_CANCEL_EVENT} days = 1 }}
\t\t\t}}"""
    elif mid == 273 and choice in (1, 2):
        post_consume = f"""
\t\t\tzg361_wad_begin_referral_source_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    elif mid == 271 and choice in (1, 2):
        post_consume = f"""
\t\t\t{PREFIX}_consume_referral_source_after_m271_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{ has_variable = {PREFIX}_ad_source_status var:{PREFIX}_ad_source_status = 1 }}
\t\t\t\tzg361_wad_begin_panel_source_effect = {{
\t\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t\t}}
\t\t\t}}"""
    elif mid == 267 and choice in (1, 2):
        post_consume = f"""
\t\t\t{PREFIX}_consume_panel_source_after_m267_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    elif mid == 274 and choice == 1:
        post_consume = f"""
\t\t\t{PREFIX}_consume_offer_source_after_m274_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    elif mid == 275 and choice in (1, 2):
        post_consume = f"""
\t\t\tif = {{
\t\t\t\tlimit = {{ has_variable = {PREFIX}_m275_refusal var:{PREFIX}_m275_refusal = 1 }}
\t\t\t\t{PREFIX}_consume_offer_source_after_m275_effect = {{
\t\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t\t}}
\t\t\t}}"""
    elif mid == 267 and choice == 3:
        post_consume = f"""
\t\t\t{PREFIX}_retire_referral_source_after_m267_debt_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}
\t\t\t{PREFIX}_retire_panel_source_after_m267_debt_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    elif mid in (274, 275) and choice == 3:
        post_consume = f"""
\t\t\t{PREFIX}_retire_offer_source_after_m{mid}_debt_effect = {{
\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t}}"""
    value_prelude = ""
    if choice in (1, 2) and mid in (271, 267, 274, 275):
        source = {271: "referral", 267: "panel", 274: "offer", 275: "offer"}[mid]
        value_prelude = _ad_source_hash_prelude(source) + "\n"
    if mid == 262 and choice in (1, 2):
        value_prelude += f"""{PREFIX}_ac_freeze_m262_host_manager_effect = {{
	TICKET_OWNER = $TICKET_OWNER$
	TICKET_SUBJECT = $TICKET_SUBJECT$
	TICKET_CYCLE = $TICKET_CYCLE$
	TICKET_CASE = $TICKET_CASE$
}}
"""
    if mid == 360:
        value_prelude += (
            indent(_m360_cost_scope_prelude())
            + "\n"
            + f"\tsave_scope_as = {PREFIX}_m360_materialize_subject\n"
            + f"\t$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_materialize_owner }}\n"
            + indent(_central_m360_quota_prelude())
            + "\n"
        )
        if choice in (1, 2):
            value_prelude += indent(_collective_persistent_prelude()) + "\n"
    elif mid == 361:
        value_prelude += indent(_ticket_next_cycle_prelude()) + "\n"
    advance = ""
    # #263 route B and a real #269 hire outcome are future-settled.  Their
    # delayed consumers, rather than the write-side receipt, advance the case.
    if mid in STAGE_LAST[d] and not (
        (mid == 263 and choice == 2) or mid == 269
    ):
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
    elif mid == 269 and choice in (1, 2):
        # A refused offer has no hire-quality clock.  Its explicit N/A object
        # closes state 5 now; a real hire remains in state 5 until evidence is
        # consumed by m269_future_consume_effect.
        barrier = stage_barrier(spec)
        edge = STAGE_LAST[d][mid]
        after = _after_advance(spec)
        deadline = deadline_prefix(d, edge)
        advance = f"""
			if = {{
				limit = {{
					has_variable = {PREFIX}_m269_not_applicable_no_hire
					var:{PREFIX}_m269_not_applicable_no_hire = 1
{indent(barrier, 5)}
				}}
				set_variable = {{ name = {deadline}_pending value = 0 }}
				zg361_case_{d}_advance_{edge:02d}_effect = {{
					TICKET_OWNER = $TICKET_OWNER$
					TICKET_SUBJECT = $TICKET_SUBJECT$
					TICKET_CYCLE = $TICKET_CYCLE$
					TICKET_CASE = $TICKET_CASE$
				}}
				if = {{
					limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
{indent(after, 5)}
				}}
			}}
"""
    elif mid == 269 and choice == 3:
        # A no-hire debt owns no attribution slot and may advance normally.
        # A real hire remains at state 5 until the signed slot has recorded
        # the exact debt/cancel receipt on later hidden frames.
        barrier = stage_barrier(spec)
        edge = STAGE_LAST[d][mid]
        after = _after_advance(spec)
        deadline = deadline_prefix(d, edge)
        advance = f"""
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\tOR = {{
\t\t\t\t\t\tAND = {{
\t\t\t\t\t\t\thas_variable = {PREFIX}_m275_refusal
\t\t\t\t\t\t\tvar:{PREFIX}_m275_refusal = 1
\t\t\t\t\t\t\thas_variable = {PREFIX}_m274_hired
\t\t\t\t\t\t\tvar:{PREFIX}_m274_hired = 0
\t\t\t\t\t\t}}
\t\t\t\t\t\tAND = {{
\t\t\t\t\t\t\thas_variable = {PREFIX}_m274_choice
\t\t\t\t\t\t\tvar:{PREFIX}_m274_choice = 3
\t\t\t\t\t\t\thas_variable = {PREFIX}_m275_choice
\t\t\t\t\t\t\tvar:{PREFIX}_m275_choice = 3
\t\t\t\t\t\t}}
\t\t\t\t\t}}
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
    if mid == 272 and choice in (1, 2):
        advance += f"""
\t\t\tif = {{
\t\t\t\tlimit = {{
\t\t\t\t\thas_variable = {PREFIX}_runtime_applied
\t\t\t\t\tvar:{PREFIX}_runtime_applied = 1
\t\t\t\t\tvar:zg361_case_ad_state = 4
\t\t\t\t}}
\t\t\t\tzg361_wad_begin_offer_response_source_effect = {{
\t\t\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t\t\t}}
\t\t\t}}
"""
    red_code = mid * 10 + choice
    return f"""# #{mid:03d} route {letter.upper()}: guard -> atomic precheck -> receipt -> write -> consumer.
{PREFIX}_m{mid}_route_{letter}_effect = {{
\tremove_variable = {PREFIX}_runtime_applied
\tremove_variable = {PREFIX}_last_red_code
{value_prelude.rstrip()}
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
\t\t\t{PREFIX}_m{mid}_consume_effect = yes{post_consume}
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
\tset_variable = {{ name = {PREFIX}_operation_total value = 40 }}
\tset_variable = {{ name = {PREFIX}_operation_used value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_total value = 400 }}
\tset_variable = {{ name = {PREFIX}_hours_available value = 400 }}
\tset_variable = {{ name = {PREFIX}_hours_output value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_on_call value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_meeting value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_leave value = 0 }}
\tset_variable = {{ name = {PREFIX}_hours_governance value = 0 }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_overtime_pending }} }} set_variable = {{ name = {PREFIX}_overtime_pending value = 0 }} }}
\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_leave_bank }} }} set_variable = {{ name = {PREFIX}_leave_bank value = 0 }} }}
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
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_report_id }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_report_id value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_adopted_cycle }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_adopted_cycle value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_current_effective_cycle }} }} set_variable = {{ name = {PREFIX}_realm_charter_current_effective_cycle value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_report_serial }} }} set_variable = {{ name = {PREFIX}_realm_charter_report_serial value = 0 }} }}
\t\tif = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_realm_charter_id_serial }} }} set_variable = {{ name = {PREFIX}_realm_charter_id_serial value = 0 }} }}
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
\tremove_variable = {PREFIX}_portfolio_terminal_history_accruing
\tremove_variable = {PREFIX}_portfolio_history_cycle_count
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
    def call(spec: Mechanism) -> str:
        effect = APPOINTMENT_WRAPPER if spec.mid == 274 else f"{PREFIX}_m{spec.mid}_route_a_effect"
        return f"""{effect} = {{
\tTICKET_OWNER = scope:{PREFIX}_{domain}_owner
\tTICKET_SUBJECT = scope:{PREFIX}_{domain}_subject
\tTICKET_CYCLE = scope:{PREFIX}_{domain}_cycle
\tTICKET_CASE = scope:{PREFIX}_{domain}_case
}}"""

    if domain == "ad":
        # #273 commits the candidate and opens the real referral producer.
        # Referral/panel/offer callbacks own every later edge, including the
        # native appointment wrapper and its ACK queue.  Replaying the former
        # straight-line #271..#274 tail here would race a pending real actor.
        candidate_index = next(index for index, spec in enumerate(specs) if spec.mid == 273)
        calls = "\n".join(call(spec) for spec in specs[: candidate_index + 1])
    else:
        calls = "\n".join(call(spec) for spec in specs)
    return f"""{PREFIX}_{domain}_run_authorized_ai_effect = {{
\t# The project owner's second AI exception is silent/background-only.
\tif = {{
\t\tlimit = {{ root = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
{indent(calls, 2)}
\t}}
}}"""


def render_m274_postconsume_fact_handoff() -> str:
    return f"""# Subject-scope handoff after the native appointment receipt and
# Workforce #274 have both been consumed.  This is the only core seam that
# arms downstream hire facts; callers must stop unless status is 1/2.
{PREFIX}_m274_postconsume_fact_handoff_effect = {{
\tremove_variable = {PREFIX}_m274_postconsume_handoff_status
\tremove_variable = {PREFIX}_m274_postconsume_handoff_red_code
\tif = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\thas_variable = {PREFIX}_m274_business_object_created
\t\t\thas_variable = {PREFIX}_m274_object_owner
\t\t\thas_variable = {PREFIX}_m274_object_subject
\t\t\thas_variable = {PREFIX}_m274_object_cycle
\t\t\thas_variable = {PREFIX}_m274_object_case
\t\t\thas_variable = {PREFIX}_m274_object_consumed
\t\t\tvar:{PREFIX}_m274_business_object_created = 1
\t\t\tvar:{PREFIX}_m274_object_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_object_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_object_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_object_case = $TICKET_CASE$
\t\t\tvar:{PREFIX}_m274_object_consumed = 1
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_active
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_published
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed_operation
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_owner
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_subject
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_cycle
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_case
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_state
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_result
\t\t\tvar:zg361_workforce_appointment_fact_receipt_active = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_published = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed_operation = 274
\t\t\tvar:zg361_workforce_appointment_fact_receipt_owner = $TICKET_OWNER$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_subject = $TICKET_SUBJECT$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_cycle = $TICKET_CYCLE$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_case = $TICKET_CASE$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_state = 4
\t\t\tvar:zg361_workforce_appointment_fact_receipt_result = 1
\t\t}}
\t\t{PROBATION_ARM_EFFECT} = {{ OWNER = $TICKET_OWNER$ }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tOR = {{
\t\t\t\t\tvar:{PROBATION_STATUS_VAR} = 1
\t\t\t\t\tvar:{PROBATION_STATUS_VAR} = 2
\t\t\t\t}}
\t\t\t}}
\t\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = var:{PROBATION_STATUS_VAR} }}
\t\t}}
\t\telse = {{
\t\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27494 }}
\t\t}}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27493 }}
\t}}
}}"""


def render_m274_native_resume() -> str:
    return f"""# Subject-scope continuation used only by the appointment package's
# hidden single-flight audit.  It replays the exact native receipt tuple, then
# restores the same post-#274 player/authorized-AI paths as the original tick.
{PREFIX}_resume_m274_after_native_appointment_effect = {{
	remove_variable = {PREFIX}_m274_native_resume_status
	remove_variable = {PREFIX}_m274_native_resume_red_code
	if = {{
		limit = {{
			has_variable = {PREFIX}_m274_native_resume_continuation_consumed
			var:{PREFIX}_m274_native_resume_continuation_consumed = 1
			var:{PREFIX}_m274_native_resume_continuation_owner = $TICKET_OWNER$
			var:{PREFIX}_m274_native_resume_continuation_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m274_native_resume_continuation_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m274_native_resume_continuation_case = $TICKET_CASE$
			has_variable = {PREFIX}_m274_business_object_created
			var:{PREFIX}_m274_business_object_created = 1
			var:{PREFIX}_m274_object_owner = $TICKET_OWNER$
			var:{PREFIX}_m274_object_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m274_object_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m274_object_case = $TICKET_CASE$
			var:{PREFIX}_m274_object_consumed = 1
			has_variable = {PREFIX}_m275_business_object_created
			var:{PREFIX}_m275_business_object_created = 1
			var:{PREFIX}_m275_object_owner = $TICKET_OWNER$
			var:{PREFIX}_m275_object_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m275_object_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m275_object_case = $TICKET_CASE$
			var:{PREFIX}_m275_object_consumed = 1
		}}
		set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 2 }}
	}}
	else_if = {{
		limit = {{
			this = $TICKET_SUBJECT$
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ad_owner
				SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial
				CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state
				ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = 4
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes highest_held_title_tier >= tier_duchy }}
			has_variable = zg361_workforce_appointment_fact_receipt_active
			var:zg361_workforce_appointment_fact_receipt_active = 1
			var:zg361_workforce_appointment_fact_receipt_consumed = 0
			var:zg361_workforce_appointment_fact_receipt_published = 1
			var:zg361_workforce_appointment_fact_receipt_owner = $TICKET_OWNER$
			var:zg361_workforce_appointment_fact_receipt_subject = $TICKET_SUBJECT$
			var:zg361_workforce_appointment_fact_receipt_cycle = $TICKET_CYCLE$
			var:zg361_workforce_appointment_fact_receipt_case = $TICKET_CASE$
			var:zg361_workforce_appointment_fact_receipt_state = 4
			var:zg361_workforce_appointment_fact_receipt_result = 1
		}}
		{APPOINTMENT_WRAPPER} = {{
			TICKET_OWNER = $TICKET_OWNER$
			TICKET_SUBJECT = $TICKET_SUBJECT$
			TICKET_CYCLE = $TICKET_CYCLE$
			TICKET_CASE = $TICKET_CASE$
		}}
		if = {{
			limit = {{
				has_variable = {APPOINTMENT_STATUS_VAR}
				var:{APPOINTMENT_STATUS_VAR} = 6
				has_variable = {PREFIX}_runtime_applied
				var:{PREFIX}_runtime_applied = 1
				var:{PREFIX}_m274_object_owner = $TICKET_OWNER$
				var:{PREFIX}_m274_object_subject = $TICKET_SUBJECT$
				var:{PREFIX}_m274_object_cycle = $TICKET_CYCLE$
				var:{PREFIX}_m274_object_case = $TICKET_CASE$
				var:{PREFIX}_m274_object_consumed = 1
			}}
			{PREFIX}_m274_postconsume_fact_handoff_effect = {{
				TICKET_OWNER = $TICKET_OWNER$
				TICKET_SUBJECT = $TICKET_SUBJECT$
				TICKET_CYCLE = $TICKET_CYCLE$
				TICKET_CASE = $TICKET_CASE$
			}}
			if = {{
				limit = {{
					OR = {{
						var:{PREFIX}_m274_postconsume_handoff_status = 1
						var:{PREFIX}_m274_postconsume_handoff_status = 2
					}}
				}}
				{PREFIX}_m275_route_a_effect = {{
					TICKET_OWNER = $TICKET_OWNER$
					TICKET_SUBJECT = $TICKET_SUBJECT$
					TICKET_CYCLE = $TICKET_CYCLE$
					TICKET_CASE = $TICKET_CASE$
				}}
				if = {{
					limit = {{
						has_variable = {PREFIX}_runtime_applied
						var:{PREFIX}_runtime_applied = 1
						var:zg361_case_ad_state = 5
						has_variable = {PREFIX}_m275_business_object_created
						var:{PREFIX}_m275_business_object_created = 1
						var:{PREFIX}_m275_object_owner = $TICKET_OWNER$
						var:{PREFIX}_m275_object_subject = $TICKET_SUBJECT$
						var:{PREFIX}_m275_object_cycle = $TICKET_CYCLE$
						var:{PREFIX}_m275_object_case = $TICKET_CASE$
						var:{PREFIX}_m275_object_consumed = 1
					}}
					set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_consumed value = 1 }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_owner value = $TICKET_OWNER$ }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_subject value = $TICKET_SUBJECT$ }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_cycle value = $TICKET_CYCLE$ }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_case value = $TICKET_CASE$ }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 1 }}
					if = {{
						limit = {{ $TICKET_OWNER$ = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
						set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_mode value = 2 }}
						{PREFIX}_m269_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
						{PREFIX}_m276_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
						{PREFIX}_m277_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
					}}
					else_if = {{
						limit = {{ $TICKET_OWNER$ = {{ is_ai = no zg361_is_celestial_liege_trigger = yes }} }}
						set_variable = {{ name = {PREFIX}_m274_native_resume_continuation_mode value = 1 }}
						$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_ad_owner }}
						save_scope_as = {PREFIX}_ad_subject
						save_scope_value_as = {{ name = {PREFIX}_ad_cycle value = $TICKET_CYCLE$ }}
						save_scope_value_as = {{ name = {PREFIX}_ad_case value = $TICKET_CASE$ }}
						$TICKET_OWNER$ = {{ trigger_event = {{ id = {NAMESPACE}.269 }} }}
					}}
				}}
				else = {{
					set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
					set_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27492 }}
				}}
			}}
			else = {{
				set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
				set_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27493 }}
			}}
		}}
		else_if = {{
			limit = {{ has_variable = {APPOINTMENT_STATUS_VAR} var:{APPOINTMENT_STATUS_VAR} = 5 }}
			set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 5 }}
		}}
		else = {{
			set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
			set_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27491 }}
		}}
	}}
	else = {{
		set_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
		set_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27490 }}
	}}
}}"""


def render_m274_attribution_pipeline() -> str:
    """Render the committed #274 -> probation -> attribution pipeline.

    The older helper renderers above are retained only as source history; this
    renderer is the sole projection included by render_effects().
    """

    return f"""# Queue one subject-root audit after any appointment-wrapper call.
# No appointment value written by that call is read in the same effect chain.
{PREFIX}_queue_m274_appointment_ack_effect = {{
\tremove_variable = {PREFIX}_m274_native_resume_status
\tif = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\tzg361_case_kernel_full_guard_trigger = {{
\t\t\t\tOWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
\t\t\t\tCYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
\t\t\t\tSTATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
\t\t\t\tEXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tEXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
\t\t\t}}
\t\t\t$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes highest_held_title_tier >= tier_duchy }}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {PREFIX}_m274_native_resume_audit_scheduled }}
\t\t\t\tvar:{PREFIX}_m274_native_resume_audit_scheduled = 0
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_pending_owner value = $TICKET_OWNER$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_pending_subject value = $TICKET_SUBJECT$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_pending_cycle value = $TICKET_CYCLE$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_pending_case value = $TICKET_CASE$ }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_NATIVE_ACK_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_audit_scheduled value = 1 }} # commit last
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_native_resume_audit_scheduled = 1
\t\t\tvar:{PREFIX}_m274_native_resume_pending_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_native_resume_pending_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_native_resume_pending_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_native_resume_pending_case = $TICKET_CASE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 5 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27490 }}
\t}}
}}

# The appointment ACK audit either observes a committed #274 receipt, asks the
# wrapper to consume a published native receipt, or waits for the provider.
{PREFIX}_resume_m274_after_native_appointment_effect = {{
\tremove_variable = {PREFIX}_m274_native_resume_status
\tremove_variable = {PREFIX}_m274_native_resume_red_code
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_consumed
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_owner
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_subject
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_cycle
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_case
\t\t\thas_variable = {PREFIX}_m274_native_resume_continuation_mode
\t\t\tvar:{PREFIX}_m274_native_resume_continuation_consumed = 1
\t\t\tvar:{PREFIX}_m274_native_resume_continuation_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_native_resume_continuation_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_native_resume_continuation_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_native_resume_continuation_case = $TICKET_CASE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 2 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\thas_variable = {PREFIX}_m274_business_object_created
\t\t\thas_variable = {PREFIX}_m274_object_owner
\t\t\thas_variable = {PREFIX}_m274_object_subject
\t\t\thas_variable = {PREFIX}_m274_object_cycle
\t\t\thas_variable = {PREFIX}_m274_object_case
\t\t\thas_variable = {PREFIX}_m274_object_consumed
\t\t\tvar:{PREFIX}_m274_business_object_created = 1
\t\t\tvar:{PREFIX}_m274_object_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_object_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_object_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_object_case = $TICKET_CASE$
\t\t\tvar:{PREFIX}_m274_object_consumed = 1
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed_operation
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed_operation = 274
\t\t}}
\t\t{PREFIX}_m274_postconsume_fact_handoff_effect = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_active
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_published
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed
\t\t\tvar:zg361_workforce_appointment_fact_receipt_active = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_published = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed = 0
\t\t\tvar:zg361_workforce_appointment_fact_receipt_owner = $TICKET_OWNER$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_subject = $TICKET_SUBJECT$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_cycle = $TICKET_CYCLE$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_case = $TICKET_CASE$
\t\t}}
\t\t{APPOINTMENT_WRAPPER} = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t}}
\t\t{PREFIX}_queue_m274_appointment_ack_effect = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {APPOINTMENT_STATUS_VAR} }}
\t\t\t\tNOT = {{ var:{APPOINTMENT_STATUS_VAR} = 4 }}
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\t{PREFIX}_queue_m274_appointment_ack_effect = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t}}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_red_code value = 27491 }}
\t}}
}}

# The only post-consume seam.  It arms the persistent career slot and
# probation now, then commits a D+1 audit; the attribution producer is never
# called in this write chain.
{PREFIX}_m274_postconsume_fact_handoff_effect = {{
\tremove_variable = {PREFIX}_m274_postconsume_handoff_status
\tremove_variable = {PREFIX}_m274_postconsume_handoff_red_code
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_completed
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_completed = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_case = $TICKET_CASE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 2 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_case = $TICKET_CASE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\t$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
\t\t\thas_variable = {PREFIX}_m274_business_object_created
\t\t\thas_variable = {PREFIX}_m274_object_owner
\t\t\thas_variable = {PREFIX}_m274_object_subject
\t\t\thas_variable = {PREFIX}_m274_object_cycle
\t\t\thas_variable = {PREFIX}_m274_object_case
\t\t\thas_variable = {PREFIX}_m274_object_consumed
\t\t\thas_variable = {PREFIX}_m274_position_receipt_id
\t\t\thas_variable = {PREFIX}_m274_position_receipt_hash
\t\t\thas_variable = {PREFIX}_m274_position_type_id
\t\t\thas_variable = {PREFIX}_m274_probation_due_cycle
\t\t\tvar:{PREFIX}_m274_business_object_created = 1
\t\t\tvar:{PREFIX}_m274_object_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m274_object_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m274_object_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m274_object_case = $TICKET_CASE$
\t\t\tvar:{PREFIX}_m274_object_consumed = 1
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_active
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_published
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_consumed_operation
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_owner
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_subject
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_cycle
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_case
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_state
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_result
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_id
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_hash
\t\t\thas_variable = zg361_workforce_appointment_fact_receipt_position_type_id
\t\t\tvar:zg361_workforce_appointment_fact_receipt_active = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_published = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_consumed_operation = 274
\t\t\tvar:zg361_workforce_appointment_fact_receipt_owner = $TICKET_OWNER$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_subject = $TICKET_SUBJECT$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_cycle = $TICKET_CYCLE$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_case = $TICKET_CASE$
\t\t\tvar:zg361_workforce_appointment_fact_receipt_state = 4
\t\t\tvar:zg361_workforce_appointment_fact_receipt_result = 1
\t\t\tvar:zg361_workforce_appointment_fact_receipt_id = var:{PREFIX}_m274_position_receipt_id
\t\t\tvar:zg361_workforce_appointment_fact_receipt_hash = var:{PREFIX}_m274_position_receipt_hash
\t\t\tvar:zg361_workforce_appointment_fact_receipt_position_type_id = var:{PREFIX}_m274_position_type_id
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_owner value = $TICKET_OWNER$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_subject value = $TICKET_SUBJECT$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_cycle value = $TICKET_CYCLE$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_case value = $TICKET_CASE$ }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_phase value = 1 }}
\t\tif = {{
\t\t\tlimit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
\t\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_mode value = 2 }}
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_m274_postconsume_handoff_mode value = 1 }} }}
\t\t{CAREER_SLOT_ARM_EFFECT} = {{
\t\t\tTICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
\t\t\tTICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
\t\t}}
\t\t{PROBATION_ARM_EFFECT} = {{ OWNER = $TICKET_OWNER$ }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_PROBATION_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_pending value = 1 }} # commit last
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27493 }}
\t}}
}}

{PREFIX}_m274_audit_probation_and_arm_attribution_effect = {{
\tremove_variable = {PREFIX}_m274_postconsume_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_pending
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_phase
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_owner
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_subject
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_cycle
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_case
\t\t\thas_variable = {PREFIX}_m274_probation_due_cycle
\t\t\thas_variable = {PREFIX}_m274_position_receipt_id
\t\t\thas_variable = {PREFIX}_m274_position_receipt_hash
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\thas_variable = {PROBATION_STATUS_VAR}
\t\t\thas_variable = zg361_workforce_probation_fact_state
\t\t\thas_variable = zg361_workforce_probation_fact_owner
\t\t\thas_variable = zg361_workforce_probation_fact_subject
\t\t\thas_variable = zg361_workforce_probation_fact_hire_cycle
\t\t\thas_variable = zg361_workforce_probation_fact_hire_case
\t\t\thas_variable = zg361_workforce_probation_fact_probation_due_cycle
\t\t\thas_variable = zg361_workforce_probation_fact_position_receipt_id
\t\t\thas_variable = zg361_workforce_probation_fact_position_receipt_hash
\t\t\tOR = {{ var:{PROBATION_STATUS_VAR} = 1 var:{PROBATION_STATUS_VAR} = 2 }}
\t\t\tvar:zg361_workforce_probation_fact_state >= 1
\t\t\tvar:zg361_workforce_probation_fact_owner = var:{PREFIX}_m274_postconsume_handoff_owner
\t\t\tvar:zg361_workforce_probation_fact_subject = this
\t\t\tvar:zg361_workforce_probation_fact_hire_cycle = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\tvar:zg361_workforce_probation_fact_hire_case = var:{PREFIX}_m274_postconsume_handoff_case
\t\t\tvar:zg361_workforce_probation_fact_probation_due_cycle = var:{PREFIX}_m274_probation_due_cycle
\t\t\tvar:zg361_workforce_probation_fact_position_receipt_id = var:{PREFIX}_m274_position_receipt_id
\t\t\tvar:zg361_workforce_probation_fact_position_receipt_hash = var:{PREFIX}_m274_position_receipt_hash
\t\t\thas_variable = zg361_workforce_probation_fact_arm_receipt_id
\t\t\thas_variable = zg361_workforce_probation_fact_arm_receipt_hash
\t\t\tvar:zg361_workforce_probation_fact_arm_receipt_id > 0
\t\t\tvar:zg361_workforce_probation_fact_arm_receipt_hash > 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_phase value = 2 }}
\t\t{ATTRIBUTION_BEGIN_EFFECT} = {{
\t\t\tTICKET_OWNER = var:{PREFIX}_m274_postconsume_handoff_owner
\t\t\tTICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\tTICKET_CASE = var:{PREFIX}_m274_postconsume_handoff_case
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_SIGNATURE_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\thas_variable = {PROBATION_STATUS_VAR}
\t\t\tvar:{PROBATION_STATUS_VAR} = 5
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27494 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\tNOT = {{ has_variable = {PROBATION_STATUS_VAR} }}
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_PROBATION_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27495 }}
\t}}
}}

{PREFIX}_m274_audit_signature_and_dispatch_disposition_effect = {{
\tremove_variable = {PREFIX}_m274_postconsume_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_pending
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_phase
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_owner
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_subject
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_cycle
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_case
\t\t\thas_variable = {PREFIX}_m272_offer_approver
\t\t\thas_variable = {PREFIX}_m267_interviewer_1
\t\t\thas_variable = {PREFIX}_m267_interviewer_2
\t\t\thas_variable = {PREFIX}_m267_interviewer_3
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_1
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_2
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_3
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 2
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\thas_variable = zg361_workforce_attribution_fact_signature_committed
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_case
\t\t\thas_variable = zg361_workforce_attribution_fact_final_approver
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_signer
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_1
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_2
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_3
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_1
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_2
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_3
\t\t\thas_variable = zg361_workforce_attribution_fact_attribution_total_bps
\t\t\tvar:zg361_workforce_attribution_fact_signature_committed = 1
\t\t\tvar:zg361_workforce_attribution_fact_state = 2
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 0
\t\t\tvar:zg361_workforce_attribution_fact_owner = var:{PREFIX}_m274_postconsume_handoff_owner
\t\t\tvar:zg361_workforce_attribution_fact_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_cycle = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\tvar:zg361_workforce_attribution_fact_case = var:{PREFIX}_m274_postconsume_handoff_case
\t\t\tvar:zg361_workforce_attribution_fact_final_approver = var:{PREFIX}_m272_offer_approver
\t\t\tvar:zg361_workforce_attribution_fact_receipt_signer = var:zg361_workforce_attribution_fact_final_approver
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_1 = var:{PREFIX}_m267_interviewer_1
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_2 = var:{PREFIX}_m267_interviewer_2
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_3 = var:{PREFIX}_m267_interviewer_3
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_1 = var:{PREFIX}_m267_vote_evidence_1
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_2 = var:{PREFIX}_m267_vote_evidence_2
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_3 = var:{PREFIX}_m267_vote_evidence_3
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_hash
\t\t\tvar:zg361_workforce_attribution_fact_receipt_id > 0
\t\t\tvar:zg361_workforce_attribution_fact_receipt_hash > 0
\t\t\tvar:zg361_workforce_attribution_fact_attribution_total_bps = 10000
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_phase value = 3 }}
\t\t{PREFIX}_m275_route_a_effect = {{
\t\t\tTICKET_OWNER = var:{PREFIX}_m274_postconsume_handoff_owner
\t\t\tTICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\tTICKET_CASE = var:{PREFIX}_m274_postconsume_handoff_case
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_DISPOSITION_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 2
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\thas_variable = zg361_workforce_attribution_fact_signature_pending
\t\t\tvar:zg361_workforce_attribution_fact_signature_pending = 1
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M274_SIGNATURE_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 2
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\thas_variable = {ATTRIBUTION_STATUS_VAR}
\t\t\tvar:{ATTRIBUTION_STATUS_VAR} = 4
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27496 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27497 }}
\t}}
}}

{PREFIX}_m274_audit_disposition_and_launch_m269_effect = {{
\tremove_variable = {PREFIX}_m274_postconsume_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_pending
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_phase
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_owner
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_subject
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_cycle
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_case
\t\t\thas_variable = {PREFIX}_m274_postconsume_handoff_mode
\t\t\thas_variable = zg361_case_ad_state
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_pending = 1
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_phase = 3
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_subject = this
\t\t\tvar:zg361_case_ad_state = 5
\t\t\thas_variable = {PREFIX}_m275_business_object_created
\t\t\thas_variable = {PREFIX}_m275_object_owner
\t\t\thas_variable = {PREFIX}_m275_object_subject
\t\t\thas_variable = {PREFIX}_m275_object_cycle
\t\t\thas_variable = {PREFIX}_m275_object_case
\t\t\thas_variable = {PREFIX}_m275_object_consumed
\t\t\thas_variable = {PREFIX}_m275_receipt_choice
\t\t\thas_variable = {PREFIX}_m275_not_applicable_hired
\t\t\thas_variable = {PREFIX}_m275_hold_pending
\t\t\tvar:{PREFIX}_m275_business_object_created = 1
\t\t\tvar:{PREFIX}_m275_object_owner = var:{PREFIX}_m274_postconsume_handoff_owner
\t\t\tvar:{PREFIX}_m275_object_subject = this
\t\t\tvar:{PREFIX}_m275_object_cycle = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\tvar:{PREFIX}_m275_object_case = var:{PREFIX}_m274_postconsume_handoff_case
\t\t\tvar:{PREFIX}_m275_object_consumed = 1
\t\t\tvar:{PREFIX}_m275_receipt_choice = 1
\t\t\tvar:{PREFIX}_m275_not_applicable_hired = 1
\t\t\tvar:{PREFIX}_m275_hold_pending = 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_owner value = var:{PREFIX}_m274_postconsume_handoff_owner }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_subject value = this }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_cycle value = var:{PREFIX}_m274_postconsume_handoff_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_case value = var:{PREFIX}_m274_postconsume_handoff_case }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_mode value = var:{PREFIX}_m274_postconsume_handoff_mode }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_completed value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_continuation_consumed value = 1 }} # continuation commit last
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m274_postconsume_handoff_mode = 2 }}
\t\t\t{PREFIX}_m269_route_a_effect = {{
\t\t\t\tTICKET_OWNER = var:{PREFIX}_m274_postconsume_handoff_owner TICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m274_postconsume_handoff_cycle
\t\t\t\tTICKET_CASE = var:{PREFIX}_m274_postconsume_handoff_case
\t\t\t}}
\t\t}}
\t\telse = {{
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_owner = {{ save_scope_as = {PREFIX}_ad_owner }}
\t\t\tsave_scope_as = {PREFIX}_ad_subject
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_cycle value = var:{PREFIX}_m274_postconsume_handoff_cycle }}
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_case value = var:{PREFIX}_m274_postconsume_handoff_case }}
\t\t\tvar:{PREFIX}_m274_postconsume_handoff_owner = {{ trigger_event = {{ id = {NAMESPACE}.269 }} }}
\t\t}}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m274_postconsume_handoff_red_code value = 27498 }}
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
\t\t# Recovery opener is #361-only.  Central's READY-gated public resume is
\t\t# the sole path that may expose #360.
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
\t\t\t\tvar:zg361_case_al_state = 5
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
\t\t\t$SUBJECT$ = {{
\t\t\t\ttrigger_if = {{ limit = {{ has_variable = {PREFIX}_portfolio_cycle }} NOT = {{ var:{PREFIX}_portfolio_cycle = root.var:zg361_review_serial }} }}
\t\t\t\ttrigger_else = {{ always = yes }}
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
\t\t\t{PREFIX}_m264_begin_handoff_effect = {{ TICKET_OWNER = var:{PREFIX}_m263_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m263_write_cycle TICKET_CASE = var:{PREFIX}_m263_write_case }}
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
\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_2
\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_3
\t\t}}
\t\tsave_temporary_scope_value_as = {{
\t\t\tname = {PREFIX}_expected_attribution_bps_1
\t\t\tvalue = {{ value = 10000 subtract = var:{PREFIX}_ad_external_attribution_bps_2 subtract = var:{PREFIX}_ad_external_attribution_bps_3 }}
\t\t}}
\t}}
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t\thas_variable = {PREFIX}_ad_external_outcome_id
\t\t\tvar:{PREFIX}_ad_external_outcome_id > 0
\t\t\thas_variable = {PREFIX}_ad_external_outcome_quality
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_id
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_hash
\t\t\thas_variable = {PREFIX}_ad_external_outcome_evidence_count
\t\t\thas_variable = {PREFIX}_ad_external_outcome_observed_cycle
\t\t\tvar:{PREFIX}_ad_external_outcome_quality >= 1
\t\t\tvar:{PREFIX}_ad_external_outcome_quality <= 4
\t\t\tvar:{PREFIX}_ad_external_outcome_evidence_count >= 1
\t\t\tvar:{PREFIX}_ad_external_outcome_observed_cycle > var:{PREFIX}_m269_write_cycle
\t\t\thas_variable = {PREFIX}_m274_hired
\t\t\tvar:{PREFIX}_m274_hired = 1
\t\t\thas_variable = {PREFIX}_m267_candidate_frozen
\t\t\tvar:{PREFIX}_m267_candidate_frozen = this
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
\t\t\t\thas_variable = {PREFIX}_m267_interviewer_1
\t\t\t\thas_variable = {PREFIX}_m267_interviewer_2
\t\t\t\thas_variable = {PREFIX}_m267_interviewer_3
\t\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_2
\t\t\t\thas_variable = {PREFIX}_ad_external_attribution_bps_3
\t\t\t\tvar:{PREFIX}_ad_external_attribution_bps_2 >= 0
\t\t\t\tvar:{PREFIX}_ad_external_attribution_bps_3 >= 0
\t\t\t\ttrigger_if = {{ limit = {{ var:{PREFIX}_ad_external_outcome_quality = 4 }} var:{PREFIX}_ad_external_attribution_bps_2 = 0 var:{PREFIX}_ad_external_attribution_bps_3 = 0 has_variable = {PREFIX}_ad_external_outcome_exclusion_reason }}
\t\t\t\ttrigger_else = {{ scope:{PREFIX}_expected_attribution_bps_1 >= 0 }}
\t\t\t}}
\t\t\ttrigger_else = {{
\t\t\t\tvar:{PREFIX}_m269_receipt_choice = 2
\t\t\t\thas_variable = {PREFIX}_m272_offer_approver
\t\t\t\tvar:{PREFIX}_m272_offer_approver = var:{PREFIX}_m269_write_owner
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_original_votes_preserved value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_last_outcome_id value = var:{PREFIX}_ad_external_outcome_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_hire_case value = var:{PREFIX}_m269_write_case }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_candidate value = var:{PREFIX}_m267_candidate_frozen }}
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
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_1 value = var:{PREFIX}_m267_interviewer_1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_2 value = var:{PREFIX}_m267_interviewer_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_3 value = var:{PREFIX}_m267_interviewer_3 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_2 value = var:{PREFIX}_ad_external_attribution_bps_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_3 value = var:{PREFIX}_ad_external_attribution_bps_3 }}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{ var:{PREFIX}_ad_external_outcome_quality = 4 }}
\t\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_1 value = 0 }}
\t\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 0 }}
\t\t\t\t\tset_variable = {{ name = {PREFIX}_m269_exclusion_reason value = var:{PREFIX}_ad_external_outcome_exclusion_reason }}
\t\t\t\t}}
\t\t\t\telse = {{
\t\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_1 value = scope:{PREFIX}_expected_attribution_bps_1 }}
\t\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 10000 }}
\t\t\t\t}}
\t\t\t}}
\t\t\telse = {{
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_blamed_final_approver value = var:{PREFIX}_m272_offer_approver }}
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
\t\tzg361_case_ad_advance_05_effect = {{ TICKET_OWNER = var:{PREFIX}_m269_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m269_write_cycle TICKET_CASE = var:{PREFIX}_m269_write_case }}
\t\tif = {{
\t\t\tlimit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 }}
\t\t\t{PREFIX}_ad_schedule_stage_06_deadline_effect = yes
\t\t\tvar:{PREFIX}_m269_write_owner = {{ save_scope_as = {PREFIX}_ad_owner }}
\t\t\tsave_scope_as = {PREFIX}_ad_subject
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_cycle value = var:{PREFIX}_m269_write_cycle }}
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_case value = var:{PREFIX}_m269_write_case }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:{PREFIX}_m269_write_owner = {{ is_ai = yes }} }}
\t\t\t\t{PREFIX}_m276_route_a_effect = {{ TICKET_OWNER = var:{PREFIX}_m269_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m269_write_cycle TICKET_CASE = var:{PREFIX}_m269_write_case }}
\t\t\t\t{PREFIX}_m277_route_a_effect = {{ TICKET_OWNER = var:{PREFIX}_m269_write_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m269_write_cycle TICKET_CASE = var:{PREFIX}_m269_write_case }}
\t\t\t}}
\t\t\telse = {{ var:{PREFIX}_m269_write_owner = {{ trigger_event = {{ id = {NAMESPACE}.276 }} }} }}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ has_variable = {PREFIX}_ad_external_outcome_id }}
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
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m275_receipt_choice = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_runner_reopen_pending value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_runner_attempt_opened value = 0 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_old_attempt_reopened value = 0 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_hold_released value = 0 }}
\t\t\tzg361_p2c_schedule_m275_runner_requisition_effect = {{
\t\t\t\tTICKET_OWNER = var:{PREFIX}_m275_write_owner
\t\t\t\tTICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m275_write_cycle
\t\t\t\tTICKET_CASE = var:{PREFIX}_m275_write_case
\t\t\t}}
\t\t}}
\t\telse = {{
\t\t\tset_variable = {{ name = {PREFIX}_m275_hold_pending value = 0 }}
\t\t\tchange_variable = {{ name = zg361_ch_hc_reserved add = -1 }}
\t\t\tchange_variable = {{ name = zg361_ch_hc_available add = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m266_hc_reservation_active value = 0 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_reason_remediated value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_hold_released value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m275_old_attempt_reopened value = 0 }}
\t\t\tvar:{PREFIX}_m275_write_owner = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_pending value = 0 }} }}
\t\t\ttrigger_event = {{ id = {NAMESPACE}.{REMEDIATION_CONSUME_EVENT} days = 1 }}
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
\t\tvar:{PREFIX}_m355_write_owner = {{ remove_short_term_gold = 10 }}
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


def render_m269_attribution_consumer() -> str:
    """Replace the legacy alias consumer with the signed fact join."""

    return f"""{PREFIX}_m269_future_consume_effect = {{
\tremove_variable = {PREFIX}_future_status
\tif = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 0
\t\t\tvar:{PREFIX}_m269_outcome_settled = 1
\t\t\thas_variable = {PREFIX}_m269_last_outcome_id
\t\t\thas_variable = {PREFIX}_m269_consumed_hire_case
\t\t\thas_variable = {PREFIX}_m269_consumed_candidate
\t\t\thas_variable = {PREFIX}_m269_outcome_evidence_id
\t\t\thas_variable = {PREFIX}_m269_outcome_evidence_hash
\t\t\thas_variable = {PREFIX}_m269_outcome_evidence_count
\t\t\thas_variable = {PREFIX}_m269_final_quality
\t\t\thas_variable = {PREFIX}_m269_outcome_provenance_locked
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_hash
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_id
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_quality
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_id
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_hash
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_count
\t\t\tvar:{PREFIX}_m269_last_outcome_id = var:zg361_workforce_probation_fact_outcome_id
\t\t\tvar:{PREFIX}_m269_consumed_hire_case = var:{PREFIX}_m269_write_case
\t\t\tvar:{PREFIX}_m269_consumed_candidate = this
\t\t\tvar:{PREFIX}_m269_outcome_evidence_id = var:zg361_workforce_probation_fact_outcome_evidence_id
\t\t\tvar:{PREFIX}_m269_outcome_evidence_hash = var:zg361_workforce_probation_fact_outcome_evidence_hash
\t\t\tvar:{PREFIX}_m269_outcome_evidence_count = var:zg361_workforce_probation_fact_outcome_evidence_count
\t\t\tvar:{PREFIX}_m269_final_quality = var:zg361_workforce_probation_fact_outcome_quality
\t\t\tvar:{PREFIX}_m269_outcome_provenance_locked = 1
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ OR = {{ var:{PREFIX}_m269_final_quality = 3 var:{PREFIX}_m269_final_quality = 4 }} }}
\t\t\t\thas_variable = {PREFIX}_m269_outcome_source_kind
\t\t\t\thas_variable = {PREFIX}_m269_outcome_exclusion_reason
\t\t\t\thas_variable = {PREFIX}_m269_external_source_receipt_id
\t\t\t\thas_variable = {PREFIX}_m269_external_source_receipt_hash
\t\t\t\tvar:{PREFIX}_m269_outcome_source_kind = var:zg361_workforce_probation_fact_source_kind
\t\t\t\tvar:{PREFIX}_m269_outcome_exclusion_reason = var:zg361_workforce_probation_fact_outcome_exclusion_reason
\t\t\t\tvar:{PREFIX}_m269_external_source_receipt_id = var:zg361_workforce_probation_fact_source_external_receipt_id
\t\t\t\tvar:{PREFIX}_m269_external_source_receipt_hash = var:zg361_workforce_probation_fact_source_external_receipt_hash
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\thas_variable = {PREFIX}_m269_attribution_signature_receipt_id
\t\t\thas_variable = {PREFIX}_m269_attribution_signature_receipt_hash
\t\t\tvar:{PREFIX}_m269_attribution_signature_receipt_id = var:zg361_workforce_attribution_fact_receipt_id
\t\t\tvar:{PREFIX}_m269_attribution_signature_receipt_hash = var:zg361_workforce_attribution_fact_receipt_hash
\t\t}}
\t\tremove_variable = {PREFIX}_m269_waiting_for_outcome_evidence
\t\tremove_variable = {PREFIX}_m269_waiting_for_attribution_fact
\t\tset_variable = {{ name = {PREFIX}_future_status value = 2 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t\tvar:{PREFIX}_m269_outcome_settled = 0
\t\t\tvar:{PREFIX}_m269_write_state = 5
\t\t\tOR = {{ var:{PREFIX}_m269_receipt_choice = 1 var:{PREFIX}_m269_receipt_choice = 2 }}
\t\t\thas_variable = zg361_workforce_attribution_fact_signature_committed
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_case
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_hash
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_signer
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_1
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_2
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_interviewer_3
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_1
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_2
\t\t\thas_variable = zg361_workforce_attribution_fact_receipt_evidence_3
\t\t\thas_variable = zg361_workforce_attribution_fact_attribution_bps_1
\t\t\thas_variable = zg361_workforce_attribution_fact_attribution_bps_2
\t\t\thas_variable = zg361_workforce_attribution_fact_attribution_bps_3
\t\t\thas_variable = zg361_workforce_attribution_fact_attribution_total_bps
\t\t\thas_variable = {PREFIX}_m272_offer_approver
\t\t\thas_variable = {PREFIX}_m267_interviewer_1
\t\t\thas_variable = {PREFIX}_m267_interviewer_2
\t\t\thas_variable = {PREFIX}_m267_interviewer_3
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_1
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_2
\t\t\thas_variable = {PREFIX}_m267_vote_evidence_3
\t\t\tvar:zg361_workforce_attribution_fact_signature_committed = 1
\t\t\tvar:zg361_workforce_attribution_fact_state = 3
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 1
\t\t\ttrigger_if = {{ limit = {{ has_variable = zg361_workforce_attribution_fact_canceled }} var:zg361_workforce_attribution_fact_canceled = 0 }}
\t\t\ttrigger_else = {{ always = yes }}
\t\t\tvar:zg361_workforce_attribution_fact_owner = var:{PREFIX}_m269_write_owner
\t\t\tvar:zg361_workforce_attribution_fact_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_cycle = var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_workforce_attribution_fact_case = var:{PREFIX}_m269_write_case
\t\t\tvar:zg361_workforce_attribution_fact_receipt_signer = var:{PREFIX}_m272_offer_approver
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_1 = var:{PREFIX}_m267_interviewer_1
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_2 = var:{PREFIX}_m267_interviewer_2
\t\t\tvar:zg361_workforce_attribution_fact_receipt_interviewer_3 = var:{PREFIX}_m267_interviewer_3
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_1 = var:{PREFIX}_m267_vote_evidence_1
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_2 = var:{PREFIX}_m267_vote_evidence_2
\t\t\tvar:zg361_workforce_attribution_fact_receipt_evidence_3 = var:{PREFIX}_m267_vote_evidence_3
\t\t\tvar:zg361_workforce_attribution_fact_attribution_total_bps = 10000
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_hire_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_hire_case
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_probation_receipt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_probation_receipt_hash
\t\t\tvar:zg361_workforce_attribution_fact_consume_hire_cycle = var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_workforce_attribution_fact_consume_hire_case = var:{PREFIX}_m269_write_case
\t\t\thas_variable = zg361_workforce_probation_fact_state
\t\t\thas_variable = zg361_workforce_probation_fact_published
\t\t\thas_variable = zg361_workforce_probation_fact_consumed
\t\t\thas_variable = zg361_workforce_probation_fact_owner
\t\t\thas_variable = zg361_workforce_probation_fact_subject
\t\t\thas_variable = zg361_workforce_probation_fact_hire_cycle
\t\t\thas_variable = zg361_workforce_probation_fact_hire_case
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_id
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_quality
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_id
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_hash
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_evidence_count
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_observed_cycle
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_exclusion_reason
\t\t\thas_variable = zg361_workforce_probation_fact_source_kind
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_dimension_1
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_dimension_2
\t\t\thas_variable = zg361_workforce_probation_fact_outcome_dimension_3
\t\t\thas_variable = zg361_workforce_probation_fact_attribution_bps_1
\t\t\thas_variable = zg361_workforce_probation_fact_attribution_bps_2
\t\t\thas_variable = zg361_workforce_probation_fact_attribution_bps_3
\t\t\thas_variable = zg361_workforce_probation_fact_attribution_receipt_id
\t\t\thas_variable = zg361_workforce_probation_fact_attribution_receipt_hash
\t\t\tvar:zg361_workforce_probation_fact_state = 3
\t\t\tvar:zg361_workforce_probation_fact_published = 1
\t\t\tvar:zg361_workforce_probation_fact_consumed = 0
\t\t\tvar:zg361_workforce_probation_fact_owner = var:{PREFIX}_m269_write_owner
\t\t\tvar:zg361_workforce_probation_fact_subject = this
\t\t\tvar:zg361_workforce_probation_fact_hire_cycle = var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_workforce_probation_fact_hire_case = var:{PREFIX}_m269_write_case
\t\t\tvar:zg361_workforce_probation_fact_outcome_id > 0
\t\t\tOR = {{
\t\t\t\tAND = {{ var:zg361_workforce_probation_fact_source_kind = 1 var:zg361_workforce_probation_fact_outcome_quality = 1 var:zg361_workforce_probation_fact_outcome_exclusion_reason = 0 }}
\t\t\t\tAND = {{ var:zg361_workforce_probation_fact_source_kind = 2 OR = {{ var:zg361_workforce_probation_fact_outcome_quality = 1 var:zg361_workforce_probation_fact_outcome_quality = 2 }} var:zg361_workforce_probation_fact_outcome_exclusion_reason = 0 }}
\t\t\t\tAND = {{
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_kind = 3
\t\t\t\t\tvar:zg361_workforce_probation_fact_outcome_quality = 3
\t\t\t\t\tvar:zg361_workforce_probation_fact_outcome_exclusion_reason = 0
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_owner = var:{PREFIX}_m269_write_owner
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_subject = this
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_receipt_id = var:zg361_workforce_normal_exit_fact_receipt_id
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_receipt_hash = var:zg361_workforce_normal_exit_fact_receipt_hash
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_native_end_reason = 1
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_hc_conservation_verified = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_active = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_sealed = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_consumed = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_actual_exit = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_hc_conservation_verified = 1
\t\t\t\t\tvar:zg361_workforce_normal_exit_fact_receipt_formal_hc_active_after = 0
\t\t\t\t}}
\t\t\t\tAND = {{
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_kind = 4
\t\t\t\t\tvar:zg361_workforce_probation_fact_outcome_quality = 4
\t\t\t\t\tvar:zg361_workforce_probation_fact_outcome_exclusion_reason = 1
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_owner = var:{PREFIX}_m269_write_owner
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_subject = this
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_receipt_id = var:zg361_workforce_exit_fact_role_failure_receipt_id
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_receipt_hash = var:zg361_workforce_exit_fact_role_failure_receipt_hash
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_native_end_reason = 2
\t\t\t\t\tvar:zg361_workforce_probation_fact_source_external_hc_conservation_verified = 1
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_active = 1
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_sealed = 1
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_formal_hc_active = 1
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_conservation_verified = 1
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_authorized = var:zg361_ch_hc_authorized
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_available = var:zg361_ch_hc_available
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_reserved = var:zg361_ch_hc_reserved
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_occupied = var:zg361_ch_hc_occupied
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_frozen = var:zg361_ch_hc_frozen
\t\t\t\t\tvar:zg361_workforce_exit_fact_role_failure_receipt_hc_reclaimed = var:zg361_ch_hc_reclaimed
\t\t\t\t}}
\t\t\t}}
\t\t\tvar:zg361_workforce_probation_fact_outcome_evidence_count >= 1
\t\t\tvar:zg361_workforce_probation_fact_outcome_observed_cycle > var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_workforce_probation_fact_outcome_dimension_1 = var:zg361_workforce_attribution_fact_receipt_evidence_1
\t\t\tvar:zg361_workforce_probation_fact_outcome_dimension_2 = var:zg361_workforce_attribution_fact_receipt_evidence_2
\t\t\tvar:zg361_workforce_probation_fact_outcome_dimension_3 = var:zg361_workforce_attribution_fact_receipt_evidence_3
\t\t\tvar:zg361_workforce_probation_fact_attribution_bps_1 = var:zg361_workforce_attribution_fact_attribution_bps_1
\t\t\tvar:zg361_workforce_probation_fact_attribution_bps_2 = var:zg361_workforce_attribution_fact_attribution_bps_2
\t\t\tvar:zg361_workforce_probation_fact_attribution_bps_3 = var:zg361_workforce_attribution_fact_attribution_bps_3
\t\t\tvar:zg361_workforce_attribution_fact_consume_probation_receipt_id = var:zg361_workforce_probation_fact_attribution_receipt_id
\t\t\tvar:zg361_workforce_attribution_fact_consume_probation_receipt_hash = var:zg361_workforce_probation_fact_attribution_receipt_hash
\t\t\thas_variable = {PREFIX}_m274_hired
\t\t\tvar:{PREFIX}_m274_hired = 1
\t\t\tvar:{PREFIX}_m274_hire_case = var:{PREFIX}_m269_write_case
\t\t\thas_variable = {PREFIX}_formal_hc_active
\t\t\tOR = {{
\t\t\t\tAND = {{
\t\t\t\t\tvar:zg361_workforce_probation_fact_outcome_quality = 3
\t\t\t\t\tvar:{PREFIX}_formal_hc_active = 0
\t\t\t\t}}
\t\t\t\tAND = {{
\t\t\t\t\tOR = {{ var:zg361_workforce_probation_fact_outcome_quality = 1 var:zg361_workforce_probation_fact_outcome_quality = 2 var:zg361_workforce_probation_fact_outcome_quality = 4 }}
\t\t\t\t\tvar:{PREFIX}_formal_hc_active = 1
\t\t\t\t\tvar:{PREFIX}_formal_hc_active_case = var:{PREFIX}_m269_write_case
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_original_votes_preserved value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_last_outcome_id value = var:zg361_workforce_probation_fact_outcome_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_hire_case value = var:{PREFIX}_m269_write_case }}
\t\tset_variable = {{ name = {PREFIX}_m269_consumed_candidate value = this }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_id value = var:zg361_workforce_probation_fact_outcome_evidence_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_hash value = var:zg361_workforce_probation_fact_outcome_evidence_hash }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_evidence_count value = var:zg361_workforce_probation_fact_outcome_evidence_count }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_observed_cycle value = var:zg361_workforce_probation_fact_outcome_observed_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_final_quality value = var:zg361_workforce_probation_fact_outcome_quality }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_source_kind value = var:zg361_workforce_probation_fact_source_kind }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_exclusion_reason value = var:zg361_workforce_probation_fact_outcome_exclusion_reason }}
\t\tif = {{
\t\t\tlimit = {{ OR = {{ var:zg361_workforce_probation_fact_source_kind = 3 var:zg361_workforce_probation_fact_source_kind = 4 }} }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_external_source_receipt_id value = var:zg361_workforce_probation_fact_source_external_receipt_id }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_external_source_receipt_hash value = var:zg361_workforce_probation_fact_source_external_receipt_hash }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_external_source_native_end_reason value = var:zg361_workforce_probation_fact_source_external_native_end_reason }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_provenance_locked value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_signature_receipt_id value = var:zg361_workforce_attribution_fact_receipt_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_signature_receipt_hash value = var:zg361_workforce_attribution_fact_receipt_hash }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_actor value = var:zg361_workforce_attribution_fact_receipt_signer }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_interviewer_1 value = var:zg361_workforce_attribution_fact_receipt_interviewer_1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_interviewer_2 value = var:zg361_workforce_attribution_fact_receipt_interviewer_2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_interviewer_3 value = var:zg361_workforce_attribution_fact_receipt_interviewer_3 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_evidence_1 value = var:zg361_workforce_attribution_fact_receipt_evidence_1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_evidence_2 value = var:zg361_workforce_attribution_fact_receipt_evidence_2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_evidence_3 value = var:zg361_workforce_attribution_fact_receipt_evidence_3 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_bps_1 value = var:zg361_workforce_attribution_fact_attribution_bps_1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_bps_2 value = var:zg361_workforce_attribution_fact_attribution_bps_2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_signed_bps_3 value = var:zg361_workforce_attribution_fact_attribution_bps_3 }}
\t\tset_variable = {{ name = {PREFIX}_m269_probation_receipt_id value = var:zg361_workforce_probation_fact_attribution_receipt_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_probation_receipt_hash value = var:zg361_workforce_probation_fact_attribution_receipt_hash }}
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m269_receipt_choice = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_1 value = var:zg361_workforce_attribution_fact_receipt_evidence_1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_2 value = var:zg361_workforce_attribution_fact_receipt_evidence_2 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_3 value = var:zg361_workforce_attribution_fact_receipt_evidence_3 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_1 value = var:zg361_workforce_attribution_fact_receipt_interviewer_1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_2 value = var:zg361_workforce_attribution_fact_receipt_interviewer_2 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_responsible_interviewer_3 value = var:zg361_workforce_attribution_fact_receipt_interviewer_3 }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_workforce_probation_fact_outcome_quality = 4 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_1 value = 0 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_2 value = 0 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_3 value = 0 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 0 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_exclusion_reason value = var:zg361_workforce_probation_fact_outcome_exclusion_reason }}
\t\t\t}}
\t\t\telse = {{
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_1 value = var:zg361_workforce_attribution_fact_attribution_bps_1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_2 value = var:zg361_workforce_attribution_fact_attribution_bps_2 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_dimension_bps_3 value = var:zg361_workforce_attribution_fact_attribution_bps_3 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 10000 }}
\t\t\t}}
\t\t}}
\t\telse = {{
\t\t\tset_variable = {{ name = {PREFIX}_m269_blamed_final_approver value = var:{PREFIX}_m272_offer_approver }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_approver_blame_bps value = 10000 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_premature_approver_blame value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m269_attribution_total_bps value = 10000 }}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:zg361_workforce_probation_fact_outcome_quality = 4 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_premature_blame_ignored_exclusion value = 1 }}
\t\t\t\tset_variable = {{ name = {PREFIX}_m269_exclusion_reason value = var:zg361_workforce_probation_fact_outcome_exclusion_reason }}
\t\t\t}}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ var:zg361_workforce_probation_fact_outcome_quality = 1 has_variable = {PREFIX}_m271_reward_due_after_probation var:{PREFIX}_m271_reward_due_after_probation = 1 has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 has_variable = {PREFIX}_m271_referrer }}
\t\t\tchange_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }}
\t\t\tchange_variable = {{ name = {PREFIX}_gold_reserved add = -5 }}
\t\t\tchange_variable = {{ name = {PREFIX}_referral_gold_paid add = 5 }}
\t\t\tchange_variable = {{ name = {PREFIX}_gold_paid add = 5 }}
\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_payee value = var:{PREFIX}_m271_referrer }}
\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_settled value = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }}
\t\t\tvar:{PREFIX}_m271_referrer = {{ add_gold = 5 }}
\t\t}}
\t\telse = {{
\t\t\tif = {{ limit = {{ has_variable = {PREFIX}_referral_gold_reserved var:{PREFIX}_referral_gold_reserved >= 5 has_variable = {PREFIX}_m271_reward_escrowed var:{PREFIX}_m271_reward_escrowed = 1 }} change_variable = {{ name = {PREFIX}_referral_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_reserved add = -5 }} change_variable = {{ name = {PREFIX}_gold_available add = 5 }} set_variable = {{ name = {PREFIX}_m271_reward_refunded value = 1 }} set_variable = {{ name = {PREFIX}_m271_reward_escrowed value = 0 }} var:{PREFIX}_m269_write_owner = {{ add_gold = 5 }} }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_requisition_released value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_owner value = var:{PREFIX}_m269_write_owner }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_subject value = this }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_cycle value = var:{PREFIX}_m269_write_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_case value = var:{PREFIX}_m269_write_case }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_phase value = 1 }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_POSTSETTLEMENT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_pending value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_settled value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_future_status value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_outcome_pending value = 0 }} # outcome commit last
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t\tOR = {{
\t\t\t\tAND = {{ has_variable = zg361_workforce_attribution_fact_signature_pending var:zg361_workforce_attribution_fact_signature_pending = 1 }}
\t\t\t\tAND = {{ has_variable = zg361_workforce_attribution_fact_dispatch_pending var:zg361_workforce_attribution_fact_dispatch_pending = 1 }}
\t\t\t\tAND = {{ has_variable = zg361_workforce_probation_fact_state var:zg361_workforce_probation_fact_state <= 2 }}
\t\t\t\tNOT = {{ has_variable = zg361_workforce_probation_fact_outcome_id }}
\t\t\t}}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_waiting_for_attribution_fact value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_future_status value = 5 }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{FUTURE_EVENT[269]} days = 30 }}
\t}}
\telse_if = {{
\t\tlimit = {{
{indent(_future_tuple_guard(269), 3)}
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_future_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_future_red_code value = 2692 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_future_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_future_red_code value = 2691 }}
\t}}
}}"""


def render_future_consumers_integrated() -> str:
    legacy = render_future_consumers()
    start = legacy.index(f"{PREFIX}_m269_future_consume_effect = {{")
    end = legacy.index(f"\n\n{PREFIX}_m275_hold_due_effect = {{", start)
    return legacy[:start] + render_m269_attribution_consumer() + legacy[end:]


def render_m269_attribution_handoffs() -> str:
    return f"""# D+1 relay from canonical result settlement.  Public
# attribution publish accepts no bps; this effect never reads its write result.
{PREFIX}_m269_publish_signed_result_effect = {{
\tremove_variable = {PREFIX}_m269_result_relay_status
\tremove_variable = {PREFIX}_m269_result_relay_red_code
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_result_relay_pending
\t\t\thas_variable = {PREFIX}_m269_result_relay_phase
\t\t\thas_variable = {PREFIX}_m269_result_relay_owner
\t\t\thas_variable = {PREFIX}_m269_result_relay_subject
\t\t\thas_variable = {PREFIX}_m269_result_relay_cycle
\t\t\thas_variable = {PREFIX}_m269_result_relay_case
\t\t\thas_variable = {PREFIX}_m269_result_relay_state
\t\t\thas_variable = {PREFIX}_m269_result_relay_settlement
\t\t\tvar:{PREFIX}_m269_result_relay_pending = 1
\t\t\tvar:{PREFIX}_m269_result_relay_phase = 1
\t\t\tvar:{PREFIX}_m269_result_relay_subject = this
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_case
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_state
\t\t\thas_variable = zg361_workforce_attribution_fact_consume_result_settlement_receipt
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 1
\t\t\tvar:zg361_workforce_attribution_fact_state = 3
\t\t\tvar:zg361_workforce_attribution_fact_owner = var:{PREFIX}_m269_result_relay_owner
\t\t\tvar:zg361_workforce_attribution_fact_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_owner = var:{PREFIX}_m269_result_relay_owner
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_cycle = var:{PREFIX}_m269_result_relay_cycle
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_case = var:{PREFIX}_m269_result_relay_case
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_state = var:{PREFIX}_m269_result_relay_state
\t\t\tvar:zg361_workforce_attribution_fact_consume_result_settlement_receipt = var:{PREFIX}_m269_result_relay_settlement
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_status value = 2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_pending value = 0 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_result_relay_pending
\t\t\thas_variable = {PREFIX}_m269_result_relay_phase
\t\t\thas_variable = {PREFIX}_m269_result_relay_subject
\t\t\tvar:{PREFIX}_m269_result_relay_pending = 1
\t\t\tvar:{PREFIX}_m269_result_relay_phase = 1
\t\t\tvar:{PREFIX}_m269_result_relay_subject = this
\t\t\thas_variable = zg361_workforce_attribution_fact_dispatch_pending
\t\t\tvar:zg361_workforce_attribution_fact_dispatch_pending = 1
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_RESULT_PUBLISH_EVENT} days = 2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\ttrigger_if = {{ limit = {{ has_variable = {PREFIX}_m269_result_relay_pending }} var:{PREFIX}_m269_result_relay_pending = 0 }}
\t\t\ttrigger_else = {{ always = yes }}
{indent(_future_tuple_guard(269), 3)}
\t\t\thas_variable = {PREFIX}_m269_outcome_pending
\t\t\thas_variable = {PREFIX}_m269_outcome_settled
\t\t\tvar:{PREFIX}_m269_outcome_pending = 1
\t\t\tvar:{PREFIX}_m269_outcome_settled = 0
\t\t\tOR = {{ var:{PREFIX}_m269_receipt_choice = 1 var:{PREFIX}_m269_receipt_choice = 2 }}
\t\t\thas_variable = zg361_workforce_attribution_fact_signature_committed
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_case
\t\t\tvar:zg361_workforce_attribution_fact_signature_committed = 1
\t\t\tvar:zg361_workforce_attribution_fact_state = 2
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 0
\t\t\tvar:zg361_workforce_attribution_fact_owner = var:{PREFIX}_m269_write_owner
\t\t\tvar:zg361_workforce_attribution_fact_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_cycle = var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_workforce_attribution_fact_case = var:{PREFIX}_m269_write_case
\t\t\thas_variable = zg361_result_case_owner
\t\t\thas_variable = zg361_result_cycle_serial
\t\t\thas_variable = zg361_result_case_serial
\t\t\thas_variable = zg361_result_case_state
\t\t\thas_variable = zg361_result_settlement_posted_serial
\t\t\thas_variable = zg361_result_grade
\t\t\thas_variable = zg361_result_grade_reason
\t\t\thas_variable = zg361_result_kpi_frozen
\t\t\thas_variable = zg361_result_rank_frozen
\t\t\tvar:zg361_result_case_owner = var:{PREFIX}_m269_write_owner
\t\t\tvar:zg361_result_cycle_serial > var:{PREFIX}_m269_write_cycle
\t\t\tvar:zg361_result_case_serial > 0
\t\t\tOR = {{ var:zg361_result_case_state = 3 var:zg361_result_case_state = 5 }}
\t\t\tvar:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
\t\t\tOR = {{ var:zg361_result_grade = 1 var:zg361_result_grade = 2 var:zg361_result_grade = 3 }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_owner value = var:{PREFIX}_m269_write_owner }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_subject value = this }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_cycle value = var:zg361_result_cycle_serial }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_case value = var:zg361_result_case_serial }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_state value = var:zg361_result_case_state }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_settlement value = var:zg361_result_settlement_posted_serial }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_phase value = 1 }}
\t\t{ATTRIBUTION_PUBLISH_EFFECT} = {{ OWNER = var:{PREFIX}_m269_write_owner }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_RESULT_PUBLISH_EVENT} days = 2 }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_status value = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_pending value = 1 }} # dispatch commit last
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\thas_variable = {ATTRIBUTION_STATUS_VAR}
\t\t\tvar:{ATTRIBUTION_STATUS_VAR} = 4
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_red_code value = 26941 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_status value = 5 }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_RESULT_PUBLISH_EVENT} days = 2 }}
\t}}
}}

# A hired route-C debt closes the signed attribution slot on a later frame.
{PREFIX}_m269_begin_attribution_debt_cancel_effect = {{
\tremove_variable = {PREFIX}_m269_debt_attribution_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_business_object_created
\t\t\thas_variable = {PREFIX}_m269_receipt_choice
\t\t\thas_variable = {PREFIX}_m269_debt_visible_to_settlement
\t\t\thas_variable = {PREFIX}_m269_debt_open
\t\t\thas_variable = {PREFIX}_m269_debt_consumed
\t\t\thas_variable = {PREFIX}_m269_debt_escalation_count
\t\t\thas_variable = {PREFIX}_m269_debt_owner
\t\t\thas_variable = {PREFIX}_m269_debt_subject
\t\t\thas_variable = {PREFIX}_m269_debt_cycle
\t\t\thas_variable = {PREFIX}_m269_debt_case
\t\t\thas_variable = {PREFIX}_m269_debt_state
\t\t\thas_variable = {PREFIX}_m269_debt_type_code
\t\t\thas_variable = {PREFIX}_m269_debt_consumer_contract
\t\t\thas_variable = {PREFIX}_m269_debt_id
\t\t\thas_variable = {PREFIX}_m269_debt_due_cycle
\t\t\tvar:{PREFIX}_m269_business_object_created = 0
\t\t\tvar:{PREFIX}_m269_receipt_choice = 3
\t\t\tvar:{PREFIX}_m269_debt_visible_to_settlement = 1
\t\t\tvar:{PREFIX}_m269_debt_open = 1
\t\t\tvar:{PREFIX}_m269_debt_consumed = 0
\t\t\tvar:{PREFIX}_m269_debt_escalation_count = 0
\t\t\tvar:{PREFIX}_m269_debt_owner = var:zg361_workforce_attribution_fact_owner
\t\t\tvar:{PREFIX}_m269_debt_subject = this
\t\t\tvar:{PREFIX}_m269_debt_cycle = var:zg361_workforce_attribution_fact_cycle
\t\t\tvar:{PREFIX}_m269_debt_case = var:zg361_workforce_attribution_fact_case
\t\t\tvar:{PREFIX}_m269_debt_state = 5
\t\t\tvar:{PREFIX}_m269_debt_type_code = 269
\t\t\tvar:{PREFIX}_m269_debt_consumer_contract = 269
\t\t\thas_variable = zg361_workforce_attribution_fact_signature_committed
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_case
\t\t\tvar:zg361_workforce_attribution_fact_signature_committed = 1
\t\t\tvar:zg361_workforce_attribution_fact_state = 2
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_owner value = var:{PREFIX}_m269_debt_owner }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_subject value = this }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_cycle value = var:{PREFIX}_m269_debt_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_case value = var:{PREFIX}_m269_debt_case }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_id value = var:{PREFIX}_m269_debt_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_due_cycle value = var:{PREFIX}_m269_debt_due_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_escalation value = var:{PREFIX}_m269_debt_escalation_count }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_phase value = 1 }}
\t\t{ATTRIBUTION_CANCEL_EFFECT} = {{ OWNER = var:{PREFIX}_m269_debt_owner }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_DEBT_CANCEL_ACK_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_pending value = 1 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\thas_variable = {ATTRIBUTION_STATUS_VAR}
\t\t\tvar:{ATTRIBUTION_STATUS_VAR} = 4
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_red_code value = 26951 }}
\t}}
\telse = {{ set_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 5 }} }}
}}

{PREFIX}_m269_ack_attribution_debt_cancel_effect = {{
\tremove_variable = {PREFIX}_m269_debt_attribution_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_pending
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_phase
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_owner
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_subject
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_cycle
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_case
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_id
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_due_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_state
\t\t\thas_variable = zg361_workforce_attribution_fact_consumed
\t\t\thas_variable = zg361_workforce_attribution_fact_canceled
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_owner
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_subject
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_case
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_debt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_debt_due_cycle
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_debt_escalation_count
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_m269_receipt_choice
\t\t\thas_variable = {PREFIX}_m269_debt_open
\t\t\thas_variable = {PREFIX}_m269_debt_consumed
\t\t\thas_variable = {PREFIX}_m269_debt_escalation_count
\t\t\tvar:{PREFIX}_m269_debt_attribution_pending = 1
\t\t\tvar:{PREFIX}_m269_debt_attribution_phase = 1
\t\t\tvar:{PREFIX}_m269_debt_attribution_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_state = 3
\t\t\tvar:zg361_workforce_attribution_fact_consumed = 1
\t\t\tvar:zg361_workforce_attribution_fact_canceled = 1
\t\t\tvar:zg361_workforce_attribution_fact_cancel_owner = var:{PREFIX}_m269_debt_attribution_owner
\t\t\tvar:zg361_workforce_attribution_fact_cancel_subject = this
\t\t\tvar:zg361_workforce_attribution_fact_cancel_cycle = var:{PREFIX}_m269_debt_attribution_cycle
\t\t\tvar:zg361_workforce_attribution_fact_cancel_case = var:{PREFIX}_m269_debt_attribution_case
\t\t\tvar:zg361_workforce_attribution_fact_cancel_debt_id = var:{PREFIX}_m269_debt_attribution_id
\t\t\tvar:zg361_workforce_attribution_fact_cancel_debt_due_cycle = var:{PREFIX}_m269_debt_attribution_due_cycle
\t\t\tvar:zg361_workforce_attribution_fact_cancel_debt_escalation_count = 0
\t\t\tvar:zg361_workforce_attribution_fact_cancel_m269_receipt_choice = 3
\t\t\tvar:{PREFIX}_m269_debt_open = 1
\t\t\tvar:{PREFIX}_m269_debt_consumed = 0
\t\t\tvar:{PREFIX}_m269_debt_escalation_count = 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_phase value = 2 }}
\t\tzg361_case_ad_advance_05_effect = {{
\t\t\tTICKET_OWNER = var:{PREFIX}_m269_debt_attribution_owner TICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:{PREFIX}_m269_debt_attribution_cycle
\t\t\tTICKET_CASE = var:{PREFIX}_m269_debt_attribution_case
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_DEBT_ADVANCE_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 5 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_red_code value = 26952 }}
\t}}
}}

{PREFIX}_m269_audit_attribution_debt_advance_effect = {{
\tremove_variable = {PREFIX}_m269_debt_attribution_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_pending
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_phase
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_owner
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_subject
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_cycle
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_case
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_id
\t\t\thas_variable = {PREFIX}_m269_debt_attribution_due_cycle
\t\t\thas_variable = zg361_case_ad_state
\t\t\thas_variable = zg361_case_ad_owner
\t\t\thas_variable = zg361_case_ad_subject
\t\t\thas_variable = zg361_case_ad_cycle_serial
\t\t\thas_variable = zg361_case_ad_case_serial
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_debt_id
\t\t\thas_variable = zg361_workforce_attribution_fact_cancel_debt_escalation_count
\t\t\tvar:{PREFIX}_m269_debt_attribution_pending = 1
\t\t\tvar:{PREFIX}_m269_debt_attribution_phase = 2
\t\t\tvar:{PREFIX}_m269_debt_attribution_subject = this
\t\t\tvar:zg361_case_ad_state = 6
\t\t\tvar:zg361_case_ad_owner = var:{PREFIX}_m269_debt_attribution_owner
\t\t\tvar:zg361_case_ad_subject = this
\t\t\tvar:zg361_case_ad_cycle_serial = var:{PREFIX}_m269_debt_attribution_cycle
\t\t\tvar:zg361_case_ad_case_serial = var:{PREFIX}_m269_debt_attribution_case
\t\t\tvar:zg361_workforce_attribution_fact_cancel_debt_id = var:{PREFIX}_m269_debt_attribution_id
\t\t\tvar:zg361_workforce_attribution_fact_cancel_debt_escalation_count = 0
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_debt_registered_id value = var:{PREFIX}_m269_debt_attribution_id }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_debt_registered_due_cycle value = var:{PREFIX}_m269_debt_attribution_due_cycle }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_debt_registered_escalation value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m269_attribution_debt_registered value = 1 }}
\t\t{PREFIX}_ad_schedule_stage_06_deadline_effect = yes
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_pending value = 0 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m269_debt_attribution_red_code value = 26953 }}
\t}}
}}

# D+1 post-settlement seam for rehire-history integration.  It proves state 6
# on a second frame, captures eligible external growth, or prepares #276 after
# the subject later returns to the immutable old owner.
{PREFIX}_m269_postsettlement_handoff_effect = {{
\tremove_variable = {PREFIX}_m269_postsettlement_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_postsettlement_pending
\t\t\thas_variable = {PREFIX}_m269_postsettlement_phase
\t\t\thas_variable = {PREFIX}_m269_postsettlement_owner
\t\t\thas_variable = {PREFIX}_m269_postsettlement_subject
\t\t\thas_variable = {PREFIX}_m269_postsettlement_cycle
\t\t\thas_variable = {PREFIX}_m269_postsettlement_case
\t\t\thas_variable = {PREFIX}_m269_outcome_settled
\t\t\thas_variable = {PREFIX}_m269_outcome_pending
\t\t\thas_variable = {PREFIX}_m269_write_owner
\t\t\thas_variable = {PREFIX}_m269_write_cycle
\t\t\thas_variable = {PREFIX}_m269_write_case
\t\t\thas_variable = zg361_case_ad_state
\t\t\tvar:{PREFIX}_m269_postsettlement_pending = 1
\t\t\tvar:{PREFIX}_m269_postsettlement_phase = 1
\t\t\tvar:{PREFIX}_m269_postsettlement_subject = this
\t\t\tvar:zg361_case_ad_state = 5
\t\t\tvar:{PREFIX}_m269_outcome_settled = 1
\t\t\tvar:{PREFIX}_m269_outcome_pending = 0
\t\t\tvar:{PREFIX}_m269_postsettlement_owner = var:{PREFIX}_m269_write_owner
\t\t\tvar:{PREFIX}_m269_postsettlement_cycle = var:{PREFIX}_m269_write_cycle
\t\t\tvar:{PREFIX}_m269_postsettlement_case = var:{PREFIX}_m269_write_case
\t\t\thas_variable = {PREFIX}_m269_attribution_signature_receipt_id
\t\t\thas_variable = {PREFIX}_m269_attribution_signature_receipt_hash
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_phase value = 2 }}
\t\t{PROBATION_FINALIZE_EFFECT} = yes
\t\tzg361_case_ad_advance_05_effect = {{
\t\t\tTICKET_OWNER = var:{PREFIX}_m269_postsettlement_owner TICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:{PREFIX}_m269_postsettlement_cycle
\t\t\tTICKET_CASE = var:{PREFIX}_m269_postsettlement_case
\t\t}}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M269_POSTSETTLEMENT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_status value = 5 }}
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m269_postsettlement_pending
\t\t\thas_variable = {PREFIX}_m269_postsettlement_phase
\t\t\thas_variable = {PREFIX}_m269_postsettlement_owner
\t\t\thas_variable = {PREFIX}_m269_postsettlement_subject
\t\t\thas_variable = {PREFIX}_m269_postsettlement_cycle
\t\t\thas_variable = {PREFIX}_m269_postsettlement_case
\t\t\thas_variable = zg361_case_ad_state
\t\t\thas_variable = zg361_case_ad_owner
\t\t\thas_variable = zg361_case_ad_subject
\t\t\thas_variable = zg361_case_ad_cycle_serial
\t\t\thas_variable = zg361_case_ad_case_serial
\t\t\tvar:{PREFIX}_m269_postsettlement_pending = 1
\t\t\tvar:{PREFIX}_m269_postsettlement_phase = 2
\t\t\tvar:{PREFIX}_m269_postsettlement_subject = this
\t\t\tvar:zg361_case_ad_state = 6
\t\t\tvar:zg361_case_ad_owner = var:{PREFIX}_m269_postsettlement_owner
\t\t\tvar:zg361_case_ad_subject = this
\t\t\tvar:zg361_case_ad_cycle_serial = var:{PREFIX}_m269_postsettlement_cycle
\t\t\tvar:zg361_case_ad_case_serial = var:{PREFIX}_m269_postsettlement_case
\t\t}}
\t\t{PREFIX}_ad_schedule_stage_06_deadline_effect = yes
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = zg361_workforce_rehire_fact_state
\t\t\t\tvar:zg361_workforce_rehire_fact_state = 1
\t\t\t}}
\t\t\t{REHIRE_CAPTURE_GROWTH_EFFECT} = yes
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = zg361_workforce_rehire_fact_state
\t\t\t\thas_variable = zg361_workforce_rehire_fact_published
\t\t\t\thas_variable = zg361_workforce_rehire_fact_consumed
\t\t\t\thas_variable = zg361_workforce_rehire_fact_exit_owner
\t\t\t\tvar:zg361_workforce_rehire_fact_state = 2
\t\t\t\tvar:zg361_workforce_rehire_fact_published = 1
\t\t\t\tvar:zg361_workforce_rehire_fact_consumed = 0
\t\t\t\tvar:zg361_workforce_rehire_fact_exit_owner = var:{PREFIX}_m269_postsettlement_owner
\t\t\t}}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_owner value = var:{PREFIX}_m269_postsettlement_owner }}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_subject value = this }}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_cycle value = var:{PREFIX}_m269_postsettlement_cycle }}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_case value = var:{PREFIX}_m269_postsettlement_case }}
\t\t\t{REHIRE_PREPARE_EFFECT} = yes
\t\t\ttrigger_event = {{ id = {NAMESPACE}.{M276_PREPARE_AUDIT_EVENT} days = 1 }}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_pending value = 1 }} # commit last
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_ready value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_status value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_pending value = 0 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m269_postsettlement_red_code value = 26961 }}
\t}}
}}

# D+1 gate between the source package's prepare write and the visible/AI #276
# operation.  Ordinary subjects without a sealed rehire history never enter it.
{PREFIX}_m276_audit_prepared_rehire_effect = {{
\tremove_variable = {PREFIX}_m276_rehire_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\thas_variable = {PREFIX}_m276_rehire_prepare_pending
\t\t\thas_variable = {PREFIX}_m276_rehire_prepare_owner
\t\t\thas_variable = {PREFIX}_m276_rehire_prepare_subject
\t\t\thas_variable = {PREFIX}_m276_rehire_prepare_cycle
\t\t\thas_variable = {PREFIX}_m276_rehire_prepare_case
\t\t\tvar:{PREFIX}_m276_rehire_prepare_pending = 1
\t\t\tvar:{PREFIX}_m276_rehire_prepare_subject = this
\t\t\tzg361_case_kernel_full_guard_trigger = {{
\t\t\t\tOWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
\t\t\t\tCYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
\t\t\t\tSTATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
\t\t\t\tEXPECTED_OWNER = var:{PREFIX}_m276_rehire_prepare_owner EXPECTED_SUBJECT = this
\t\t\t\tEXPECTED_CYCLE = var:{PREFIX}_m276_rehire_prepare_cycle
\t\t\t\tEXPECTED_CASE = var:{PREFIX}_m276_rehire_prepare_case EXPECTED_STATE = 6
\t\t\t}}
\t\t\thas_variable = zg361_workforce_rehire_fact_state
\t\t\thas_variable = zg361_workforce_rehire_fact_published
\t\t\thas_variable = zg361_workforce_rehire_fact_consumed
\t\t\thas_variable = zg361_workforce_rehire_fact_prepared_owner
\t\t\thas_variable = zg361_workforce_rehire_fact_prepared_subject
\t\t\thas_variable = zg361_workforce_rehire_fact_prepared_cycle
\t\t\thas_variable = zg361_workforce_rehire_fact_prepared_case
\t\t\tvar:zg361_workforce_rehire_fact_state = 3
\t\t\tvar:zg361_workforce_rehire_fact_published = 1
\t\t\tvar:zg361_workforce_rehire_fact_consumed = 0
\t\t\tvar:zg361_workforce_rehire_fact_prepared_owner = var:{PREFIX}_m276_rehire_prepare_owner
\t\t\tvar:zg361_workforce_rehire_fact_prepared_subject = this
\t\t\tvar:zg361_workforce_rehire_fact_prepared_cycle = var:{PREFIX}_m276_rehire_prepare_cycle
\t\t\tvar:zg361_workforce_rehire_fact_prepared_case = var:{PREFIX}_m276_rehire_prepare_case
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_prepare_pending value = 0 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 1 }}
\t\tif = {{
\t\t\tlimit = {{ var:{PREFIX}_m276_rehire_prepare_owner = {{ is_ai = yes }} }}
\t\t\t{PREFIX}_m276_route_a_effect = {{
\t\t\t\tTICKET_OWNER = var:{PREFIX}_m276_rehire_prepare_owner TICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m276_rehire_prepare_cycle
\t\t\t\tTICKET_CASE = var:{PREFIX}_m276_rehire_prepare_case
\t\t\t}}
\t\t\t{PREFIX}_queue_m276_rehire_finalize_effect = {{
\t\t\t\tTICKET_OWNER = var:{PREFIX}_m276_rehire_prepare_owner TICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m276_rehire_prepare_cycle
\t\t\t\tTICKET_CASE = var:{PREFIX}_m276_rehire_prepare_case CHOICE = 1
\t\t\t}}
\t\t}}
\t\telse = {{
\t\t\tvar:{PREFIX}_m276_rehire_prepare_owner = {{ save_scope_as = {PREFIX}_ad_owner }}
\t\t\tsave_scope_as = {PREFIX}_ad_subject
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_cycle value = var:{PREFIX}_m276_rehire_prepare_cycle }}
\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_case value = var:{PREFIX}_m276_rehire_prepare_case }}
\t\t\tvar:{PREFIX}_m276_rehire_prepare_owner = {{ trigger_event = {{ id = {NAMESPACE}.276 }} }}
\t\t}}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_red_code value = 27661 }}
\t}}
}}

# Route A/B writes are observed only by a later subject event.  Route C never
# calls this queue because it has not consumed the rehire history.
{PREFIX}_queue_m276_rehire_finalize_effect = {{
\tremove_variable = {PREFIX}_m276_rehire_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\tthis = $TICKET_SUBJECT$
\t\t\tzg361_case_kernel_full_guard_trigger = {{
\t\t\t\tOWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
\t\t\t\tCYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
\t\t\t\tSTATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
\t\t\t\tEXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
\t\t\t\tEXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 6
\t\t\t}}
\t\t\tOR = {{ $CHOICE$ = 1 $CHOICE$ = 2 }}
\t\t\ttrigger_if = {{
\t\t\t\tlimit = {{ has_variable = {PREFIX}_m276_rehire_finalize_pending }}
\t\t\t\tvar:{PREFIX}_m276_rehire_finalize_pending = 0
\t\t\t}}
\t\t\ttrigger_else = {{ always = yes }}
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_owner value = $TICKET_OWNER$ }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_subject value = $TICKET_SUBJECT$ }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_cycle value = $TICKET_CYCLE$ }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_case value = $TICKET_CASE$ }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_choice value = $CHOICE$ }}
\t\tif = {{
\t\t\tlimit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
\t\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_mode value = 2 }}
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_m276_rehire_finalize_mode value = 1 }} }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{M276_FINALIZE_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 5 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_pending value = 1 }} # commit last
\t}}
\telse_if = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m276_rehire_finalize_pending = 1
\t\t\tvar:{PREFIX}_m276_rehire_finalize_owner = $TICKET_OWNER$
\t\t\tvar:{PREFIX}_m276_rehire_finalize_subject = $TICKET_SUBJECT$
\t\t\tvar:{PREFIX}_m276_rehire_finalize_cycle = $TICKET_CYCLE$
\t\t\tvar:{PREFIX}_m276_rehire_finalize_case = $TICKET_CASE$
\t\t\tvar:{PREFIX}_m276_rehire_finalize_choice = $CHOICE$
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 5 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_red_code value = 27662 }}
\t}}
}}

{PREFIX}_m276_finalize_rehire_effect = {{
\tremove_variable = {PREFIX}_m276_rehire_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m276_rehire_finalize_pending = 1
\t\t\tvar:{PREFIX}_m276_rehire_finalize_subject = this
\t\t\tOR = {{ var:{PREFIX}_m276_rehire_finalize_choice = 1 var:{PREFIX}_m276_rehire_finalize_choice = 2 }}
\t\t}}
\t\t{REHIRE_FINALIZE_EFFECT} = yes
\t\ttrigger_event = {{ id = {NAMESPACE}.{M276_FINALIZE_AUDIT_EVENT} days = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 5 }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_red_code value = 27663 }}
\t}}
}}

{PREFIX}_m276_audit_rehire_finalize_effect = {{
\tremove_variable = {PREFIX}_m276_rehire_handoff_status
\tif = {{
\t\tlimit = {{
\t\t\tvar:{PREFIX}_m276_rehire_finalize_pending = 1
\t\t\tvar:{PREFIX}_m276_rehire_finalize_subject = this
\t\t\thas_variable = zg361_workforce_rehire_fact_state
\t\t\thas_variable = zg361_workforce_rehire_fact_consumed
\t\t\thas_variable = zg361_workforce_rehire_fact_consume_owner
\t\t\thas_variable = zg361_workforce_rehire_fact_consume_subject
\t\t\thas_variable = zg361_workforce_rehire_fact_consume_cycle
\t\t\thas_variable = zg361_workforce_rehire_fact_consume_case
\t\t\thas_variable = zg361_workforce_rehire_fact_consume_choice
\t\t\tvar:zg361_workforce_rehire_fact_state = 4
\t\t\tvar:zg361_workforce_rehire_fact_consumed = 1
\t\t\tvar:zg361_workforce_rehire_fact_consume_owner = var:{PREFIX}_m276_rehire_finalize_owner
\t\t\tvar:zg361_workforce_rehire_fact_consume_subject = this
\t\t\tvar:zg361_workforce_rehire_fact_consume_cycle = var:{PREFIX}_m276_rehire_finalize_cycle
\t\t\tvar:zg361_workforce_rehire_fact_consume_case = var:{PREFIX}_m276_rehire_finalize_case
\t\t\tvar:zg361_workforce_rehire_fact_consume_choice = var:{PREFIX}_m276_rehire_finalize_choice
\t\t}}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_completed value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 1 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_finalize_pending value = 0 }} # completion commit last
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = {PREFIX}_ad_external_pip_exit_ready
\t\t\t\tvar:{PREFIX}_ad_external_pip_exit_ready = 1
\t\t\t}}
\t\t\tif = {{
\t\t\t\tlimit = {{ var:{PREFIX}_m276_rehire_finalize_mode = 2 }}
\t\t\t\t{PREFIX}_m277_route_a_effect = {{
\t\t\t\t\tTICKET_OWNER = var:{PREFIX}_m276_rehire_finalize_owner TICKET_SUBJECT = this
\t\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m276_rehire_finalize_cycle
\t\t\t\t\tTICKET_CASE = var:{PREFIX}_m276_rehire_finalize_case
\t\t\t\t}}
\t\t\t}}
\t\t\telse = {{
\t\t\t\tvar:{PREFIX}_m276_rehire_finalize_owner = {{ save_scope_as = {PREFIX}_ad_owner }}
\t\t\t\tsave_scope_as = {PREFIX}_ad_subject
\t\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_cycle value = var:{PREFIX}_m276_rehire_finalize_cycle }}
\t\t\t\tsave_scope_value_as = {{ name = {PREFIX}_ad_case value = var:{PREFIX}_m276_rehire_finalize_case }}
\t\t\t\tvar:{PREFIX}_m276_rehire_finalize_owner = {{ trigger_event = {{ id = {NAMESPACE}.277 }} }}
\t\t\t}}
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_m276_waiting_for_m277_provider value = 1 }} }}
\t}}
\telse = {{
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_status value = 4 }}
\t\tset_variable = {{ name = {PREFIX}_m276_rehire_handoff_red_code value = 27664 }}
\t}}
}}"""


def render_due_debt_consumer(spec: Mechanism) -> str:
    """Consume one route-C debt without pretending that metadata is settlement.

    The delayed event runs on the frozen subject.  It first proves the complete
    debt identity against the original operation write tuple.  Available
    governance capacity repays the debt; otherwise the frozen manager receives
    at most two bounded escalation penalties.  A third failure remains open
    with a typed blocked reason instead of silently disappearing.
    """

    mid = spec.mid
    p = f"{PREFIX}_m{mid}"
    event_id = DEBT_EVENT[mid]
    return f"""{p}_consume_due_debt_effect = {{
	remove_variable = {PREFIX}_future_status
	remove_variable = {PREFIX}_future_red_code
{indent(_debt_id_prelude(mid))}
	if = {{
		limit = {{
			has_variable = {p}_debt_owner
			has_variable = {p}_debt_subject
			has_variable = {p}_debt_cycle
			has_variable = {p}_debt_case
			has_variable = {p}_debt_state
			has_variable = {p}_debt_type_code
			has_variable = {p}_debt_id
			has_variable = {p}_debt_consumer_contract
			has_variable = {p}_debt_due_cycle
			has_variable = {p}_debt_open
			has_variable = {p}_debt_consumed
			has_variable = {p}_debt_escalation_count
			has_variable = {p}_write_owner
			has_variable = {p}_write_subject
			has_variable = {p}_write_cycle
			has_variable = {p}_write_case
			has_variable = {p}_write_state
			has_variable = {p}_business_object_created
			has_variable = {PREFIX}_policy_debt
			var:{p}_debt_open = 1
			var:{p}_debt_consumed = 0
			var:{p}_business_object_created = 0
			var:{p}_debt_type_code = {mid}
			var:{p}_debt_consumer_contract = {mid}
			var:{p}_debt_owner = var:{p}_write_owner
			var:{p}_debt_subject = this
			var:{p}_debt_subject = var:{p}_write_subject
			var:{p}_debt_cycle = var:{p}_write_cycle
			var:{p}_debt_case = var:{p}_write_case
			var:{p}_debt_state = var:{p}_write_state
			var:{p}_debt_id = scope:{PREFIX}_m{mid}_expected_debt_id
			var:{p}_debt_owner = {{
				has_variable = zg361_review_serial
				var:zg361_review_serial >= root.var:{p}_debt_due_cycle
			}}
		}}
		if = {{
			limit = {{
				has_variable = {PREFIX}_hours_available
				has_variable = {PREFIX}_hours_governance
				var:{PREFIX}_hours_available >= 2
				var:{PREFIX}_policy_debt >= 1
				var:{p}_debt_owner = {{ zg361_is_celestial_liege_trigger = yes }}
			}}
			change_variable = {{ name = {PREFIX}_hours_available add = -2 }}
			change_variable = {{ name = {PREFIX}_hours_governance add = 2 }}
			change_variable = {{ name = {PREFIX}_policy_debt add = -1 }}
			set_variable = {{ name = {p}_debt_open value = 0 }}
			set_variable = {{ name = {p}_debt_consumed value = 1 }}
			set_variable = {{ name = {p}_debt_resolution value = 1 }}
			set_variable = {{ name = {p}_debt_settled_cycle value = var:{p}_debt_due_cycle }}
			set_variable = {{ name = {p}_debt_capacity_paid value = 2 }}
			set_variable = {{ name = {PREFIX}_future_status value = 1 }}
		}}
		else_if = {{
			limit = {{
				var:{p}_debt_escalation_count < 2
				var:{p}_debt_owner = {{
					zg361_is_celestial_liege_trigger = yes
					has_variable = {PREFIX}_manager_score
				}}
			}}
			change_variable = {{ name = {p}_debt_escalation_count add = 1 }}
			change_variable = {{ name = {p}_debt_due_cycle add = 1 }}
			set_variable = {{ name = {p}_debt_resolution value = 2 }}
			set_variable = {{ name = {p}_debt_escalated_cycle value = var:{p}_debt_due_cycle }}
			var:{p}_debt_owner = {{ change_variable = {{ name = {PREFIX}_manager_score add = -2 }} }}
			set_variable = {{ name = {PREFIX}_future_status value = 1 }}
			trigger_event = {{ id = {NAMESPACE}.{event_id} days = 365 }}
		}}
		else = {{
			set_variable = {{ name = {p}_debt_resolution value = 3 }}
			set_variable = {{ name = {p}_debt_blocked_reason value = {70000 + mid} }}
			set_variable = {{ name = {PREFIX}_future_red_code value = {70000 + mid} }}
			set_variable = {{ name = {PREFIX}_future_status value = 5 }}
		}}
	}}
	else_if = {{
		limit = {{
			has_variable = {p}_debt_open
			has_variable = {p}_debt_consumed
			var:{p}_debt_open = 0
			var:{p}_debt_consumed = 1
		}}
		set_variable = {{ name = {PREFIX}_future_status value = 2 }}
	}}
	else_if = {{
		limit = {{
			has_variable = {p}_debt_open
			var:{p}_debt_open = 1
			has_variable = {p}_debt_due_cycle
			has_variable = {p}_debt_owner
			var:{p}_debt_owner = {{
				has_variable = zg361_review_serial
				var:zg361_review_serial < root.var:{p}_debt_due_cycle
			}}
		}}
		set_variable = {{ name = {PREFIX}_future_status value = 5 }}
		trigger_event = {{ id = {NAMESPACE}.{event_id} days = 90 }}
	}}
	else = {{
		set_variable = {{ name = {PREFIX}_future_status value = 3 }}
		set_variable = {{ name = {PREFIX}_future_red_code value = {71000 + mid} }}
	}}
}}"""


def render_due_debt_consumers() -> str:
    return "\n\n".join(render_due_debt_consumer(spec) for spec in MECHANISMS)


def render_collective_producer() -> str:
    """Render the only real #360 producer: Central -> B1/MG -> Workforce."""

    shared_fields = (
        "submission_active", "submission_sealed", "submission_consumed",
        "submission_owner", "submission_subject", "submission_cycle",
        "submission_case", "submission_state", "case", "submitted_cycle",
        "cohort_count", "settlement_id", "settlement_hash", "settled", "route",
        "total_members", "total_quota", "forced_count", "exception_count",
        "manager_cost_total", "reform_proposal_id", "reform_effective_cycle",
    )
    cohort_fields = (
        "cohort_id", "manager", "member_count", "member_hash", "agenda_count",
        "agenda_hash", "quota", "all_meet_evidence_id", "forced_count",
        "exception_count", "approver", "manager_cost", "partition_verified",
        "approval_verified", "mg_cycle", "mg_case", "mg_snapshot_source_serial",
        "mg_snapshot_revision", "b1_cycle", "b1_case", "b1_source_id",
        "b1_source_hash",
    )
    identity_fields = (
        "character", "cohort_id", "member_evidence_receipt", "member_evidence_id",
        "member_evidence_hash", "processing_order", "b1_owner", "b1_subject",
        "b1_cycle", "b1_case", "result_owner", "result_subject", "result_cycle",
        "result_case",
    )
    cleanup = [
        *(f"remove_variable = {PREFIX}_al_external_collective_{field}" for field in shared_fields),
        *(
            f"remove_variable = {PREFIX}_al_external_collective_{cohort}_{field}"
            for cohort in (1, 2, 3) for field in cohort_fields
        ),
        *(
            f"remove_variable = {PREFIX}_al_external_collective_{cohort}_{kind}_{slot}_{field}"
            for cohort in (1, 2, 3) for kind in ("forced", "exception")
            for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1)
            for field in identity_fields
        ),
    ]

    central_checks = _central_m360_owner_checks(1)
    for cohort in (1, 2, 3):
        central = f"zg361_p2c_m360_source_c{cohort}_manager"
        central_checks.append(
            f"var:{central} = {{\n{indent(chr(10).join(_central_m360_live_manager_checks(cohort)))}\n}}"
        )
    candidate_slots = [
        (cohort, slot)
        for cohort in (1, 2, 3)
        for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1)
    ]
    for left_index, (lc, ls) in enumerate(candidate_slots):
        for rc, rs in candidate_slots[left_index + 1:]:
            central_checks.append(
                f"trigger_if = {{ limit = {{ var:zg361_p2c_m360_source_c{lc}_quota >= {ls} "
                f"var:zg361_p2c_m360_source_c{rc}_quota >= {rs} }} "
                f"NOT = {{ var:zg361_p2c_m360_source_c{lc}_manager.var:zg361_b1_m360_source_forced_{ls}_character = "
                f"var:zg361_p2c_m360_source_c{rc}_manager.var:zg361_b1_m360_source_forced_{rs}_character }} }} "
                f"trigger_else = {{ always = yes }}"
            )

    def route_materializer(choice: int) -> str:
        letter = "a" if choice == 1 else "b"
        active_kind = "exception" if choice == 1 else "forced"
        writes = [
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_active value = 1 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_sealed value = 1 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_consumed value = 0 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_owner value = $TICKET_OWNER$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_subject value = $TICKET_SUBJECT$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_cycle value = $TICKET_CYCLE$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_case value = $TICKET_CASE$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submission_state value = 4 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_case value = $TICKET_CASE$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_submitted_cycle value = $TICKET_CYCLE$ }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_cohort_count value = 3 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_settlement_id value = {{ value = $TICKET_CASE$ multiply = 1000 add = 360 }} }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_settlement_hash value = {{ value = var:{PREFIX}_al_external_collective_settlement_id multiply = 100000 add = scope:{PREFIX}_m360_materialize_owner.var:zg361_p2c_m360_source_c1_b1_source_hash add = scope:{PREFIX}_m360_materialize_owner.var:zg361_p2c_m360_source_c2_b1_source_hash add = scope:{PREFIX}_m360_materialize_owner.var:zg361_p2c_m360_source_c3_b1_source_hash }} }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_settled value = 0 }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_route value = {choice} }}",
        ]
        for cohort in (1, 2, 3):
            base = f"{PREFIX}_al_external_collective_{cohort}"
            central = f"zg361_p2c_m360_source_c{cohort}"
            manager = f"scope:{PREFIX}_m360_materialize_owner.var:{central}_manager"
            values = {
                "cohort_id": f"{{ value = var:{PREFIX}_al_external_collective_settlement_id multiply = 10 add = {cohort} }}",
                "manager": manager,
                "member_count": f"{manager}.var:zg361_b1_m360_source_member_count",
                "member_hash": f"{manager}.var:zg361_b1_m360_source_member_hash",
                "agenda_count": f"{manager}.var:zg361_b1_m360_source_agenda_count",
                "agenda_hash": f"{manager}.var:zg361_b1_m360_source_agenda_hash",
                "quota": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_quota",
                "all_meet_evidence_id": f"{manager}.var:zg361_b1_m360_source_all_meet_receipt_serial",
                "forced_count": "0" if choice == 1 else f"scope:{PREFIX}_m360_materialize_owner.var:{central}_quota",
                "exception_count": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_quota" if choice == 1 else "0",
                "approver": f"scope:{PREFIX}_m360_materialize_owner" if choice == 1 else "0",
                "manager_cost": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_quota" if choice == 1 else "0",
                "partition_verified": "1",
                "approval_verified": "1" if choice == 1 else "0",
                "mg_cycle": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_cycle",
                "mg_case": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_case",
                "mg_snapshot_source_serial": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_source_serial",
                "mg_snapshot_revision": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_revision",
                "b1_cycle": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_cycle",
                "b1_case": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_case",
                "b1_source_id": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_id",
                "b1_source_hash": f"scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_hash",
            }
            writes.extend(
                f"set_variable = {{ name = {base}_{field} value = {value} }}"
                for field, value in values.items()
            )
            for slot in range(1, MAX_COLLECTIVE_OUTCOMES + 1):
                identity = f"{base}_{active_kind}_{slot}"
                source = f"{manager}.var:zg361_b1_m360_source_forced_{slot}"
                source_values = {
                    "character": f"{source}_character",
                    "cohort_id": f"var:{base}_cohort_id",
                    "member_evidence_receipt": "1",
                    "member_evidence_id": f"{source}_m357_receipt_id",
                    "member_evidence_hash": f"{source}_m357_receipt_hash",
                    "processing_order": f"{source}_processing_order",
                    "b1_owner": f"{source}_b1_owner",
                    "b1_subject": f"{source}_b1_subject",
                    "b1_cycle": f"{source}_b1_cycle",
                    "b1_case": f"{source}_b1_case",
                    "result_owner": f"{source}_result_owner",
                    "result_subject": f"{source}_result_subject",
                    "result_cycle": f"{source}_result_cycle",
                    "result_case": f"{source}_result_case",
                }
                slot_writes = " ".join(
                    f"set_variable = {{ name = {identity}_{field} value = {value} }}"
                    for field, value in source_values.items()
                )
                writes.append(
                    f"if = {{ limit = {{ scope:{PREFIX}_m360_materialize_owner.var:{central}_quota >= {slot} }} {slot_writes} }}"
                )
        writes += [
            f"set_variable = {{ name = {PREFIX}_al_external_collective_total_members value = {{ value = var:{PREFIX}_al_external_collective_1_member_count add = var:{PREFIX}_al_external_collective_2_member_count add = var:{PREFIX}_al_external_collective_3_member_count }} }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_total_quota value = scope:{PREFIX}_m360_materialize_owner.var:zg361_p2c_m360_source_total_quota }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_forced_count value = {'0' if choice == 1 else f'var:{PREFIX}_al_external_collective_total_quota'} }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_exception_count value = {f'var:{PREFIX}_al_external_collective_total_quota' if choice == 1 else '0'} }}",
            f"set_variable = {{ name = {PREFIX}_al_external_collective_manager_cost_total value = {f'var:{PREFIX}_al_external_collective_total_quota' if choice == 1 else '0'} }}",
        ]
        main_checks = [
            f"zg361_case_kernel_full_guard_trigger = {{ OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$ EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4 }}",
            "$TICKET_SUBJECT$ = this",
            "$TICKET_SUBJECT$ = { zg361_is_celestial_liege_trigger = yes }",
            f"{_zero_or_missing(f'{PREFIX}_al_external_collective_submission_active')}",
            f"$TICKET_OWNER$ = {{\n{indent(chr(10).join(central_checks))}\n}}",
        ]
        return f"""# Route {letter.upper()} materializes only product-owned Central/B1 facts.
{PREFIX}_materialize_m360_route_{letter}_from_central_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	remove_variable = {PREFIX}_runtime_applied
	save_scope_as = {PREFIX}_m360_materialize_subject
	$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_materialize_owner }}
{indent(_m360_cost_scope_prelude())}
{indent(_central_m360_quota_prelude())}
{indent(_collective_persistent_prelude())}
	if = {{
		limit = {{
{indent(chr(10).join(main_checks), 3)}
		}}
{indent(chr(10).join(cleanup), 2)}
{indent(chr(10).join(writes), 2)}
{indent(_collective_persistent_prelude(), 2)}
		# Do not expose the draft as committed until all three MG managers and
		# the owner trust book pass the same global preflight used by the route.
		if = {{
			limit = {{
{indent(chr(10).join(_collective_external_checks(choice)), 4)}
			}}
			set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
		}}
		else = {{
{indent(chr(10).join(cleanup), 3)}
			set_variable = {{ name = {PREFIX}_m360_event_queued value = 0 }}
			set_variable = {{ name = {PREFIX}_adapter_status value = 4 }}
			set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = {3604 + choice} }}
		}}
	}}
	else_if = {{
		limit = {{
			$TICKET_SUBJECT$ = this
{indent(chr(10).join(_collective_external_checks(choice)), 3)}
		}}
		set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = {3604 + choice} }} }}
}}"""

    m360_spec = by_id()[360]
    committed_ab_checks = [
        *(f"has_variable = {PREFIX}_al_external_collective_{field}" for field in (
            "submission_active", "submission_sealed", "submission_consumed",
            "submission_owner", "submission_subject", "submission_cycle",
            "submission_case", "submission_state", "settled", "route",
            "cohort_count", "total_quota", "settlement_id", "settlement_hash",
        )),
        f"var:{PREFIX}_al_external_collective_submission_active = 0",
        f"var:{PREFIX}_al_external_collective_submission_sealed = 1",
        f"var:{PREFIX}_al_external_collective_submission_consumed = 1",
        f"var:{PREFIX}_al_external_collective_submission_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_al_external_collective_submission_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_al_external_collective_submission_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_al_external_collective_submission_case = $TICKET_CASE$",
        f"var:{PREFIX}_al_external_collective_submission_state = 4",
        f"var:{PREFIX}_al_external_collective_settled = 1",
        f"var:{PREFIX}_al_external_collective_cohort_count = 3",
        f"var:{PREFIX}_al_external_collective_total_quota = scope:{PREFIX}_m360_materialize_owner.var:zg361_p2c_m360_source_total_quota",
        f"var:{PREFIX}_al_external_collective_settlement_id > 0",
        f"var:{PREFIX}_al_external_collective_settlement_hash > 0",
        f"has_variable = {PREFIX}_m360_business_object_created",
        f"has_variable = {PREFIX}_m360_object_consumed",
        f"has_variable = {PREFIX}_m360_object_owner",
        f"has_variable = {PREFIX}_m360_object_subject",
        f"has_variable = {PREFIX}_m360_object_cycle",
        f"has_variable = {PREFIX}_m360_object_case",
        f"var:{PREFIX}_m360_business_object_created = 1",
        f"var:{PREFIX}_m360_object_consumed = 1",
        f"var:{PREFIX}_m360_object_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m360_object_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m360_object_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m360_object_case = $TICKET_CASE$",
        "OR = {\n"
        + indent(
            "AND = {\n"
            + indent(receipt_guard(m360_spec, 1))
            + f"\n\tvar:{PREFIX}_al_external_collective_route = 1\n}}"
        )
        + "\n"
        + indent(
            "AND = {\n"
            + indent(receipt_guard(m360_spec, 2))
            + f"\n\tvar:{PREFIX}_al_external_collective_route = 2\n}}"
        )
        + "\n}",
    ]
    for cohort in (1, 2, 3):
        base = f"{PREFIX}_al_external_collective_{cohort}"
        central = f"zg361_p2c_m360_source_c{cohort}"
        committed_ab_checks += [
            *(f"has_variable = {base}_{field}" for field in (
                "manager", "quota", "b1_cycle", "b1_case", "b1_source_id",
                "b1_source_hash", "mg_cycle", "mg_case",
                "mg_snapshot_source_serial", "mg_snapshot_revision",
            )),
            f"var:{base}_manager = scope:{PREFIX}_m360_materialize_owner.var:{central}_manager",
            f"var:{base}_quota = scope:{PREFIX}_m360_materialize_owner.var:{central}_quota",
            f"var:{base}_b1_cycle = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_cycle",
            f"var:{base}_b1_case = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_case",
            f"var:{base}_b1_source_id = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_id",
            f"var:{base}_b1_source_hash = scope:{PREFIX}_m360_materialize_owner.var:{central}_b1_source_hash",
            f"var:{base}_mg_cycle = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_cycle",
            f"var:{base}_mg_case = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_case",
            f"var:{base}_mg_snapshot_source_serial = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_source_serial",
            f"var:{base}_mg_snapshot_revision = scope:{PREFIX}_m360_materialize_owner.var:{central}_mg_snapshot_revision",
        ]
    committed_c_checks = [
        receipt_guard(m360_spec, 3),
        f"{_zero_or_missing(f'{PREFIX}_al_external_collective_submission_active')}",
        f"NOT = {{ has_variable = {PREFIX}_al_external_collective_submission_sealed }}",
        f"has_variable = {PREFIX}_m360_choice",
        f"has_variable = {PREFIX}_m360_business_object_created",
        f"has_variable = {PREFIX}_m360_debt_owner",
        f"has_variable = {PREFIX}_m360_debt_subject",
        f"has_variable = {PREFIX}_m360_debt_cycle",
        f"has_variable = {PREFIX}_m360_debt_case",
        f"has_variable = {PREFIX}_m360_debt_state",
        f"has_variable = {PREFIX}_m360_debt_open",
        f"has_variable = {PREFIX}_m360_debt_consumed",
        f"var:{PREFIX}_m360_choice = 3",
        f"var:{PREFIX}_m360_business_object_created = 0",
        f"var:{PREFIX}_m360_debt_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_m360_debt_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_m360_debt_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_m360_debt_case = $TICKET_CASE$",
        f"var:{PREFIX}_m360_debt_state = 4",
        f"var:{PREFIX}_m360_debt_open = 1",
        f"var:{PREFIX}_m360_debt_consumed = 0",
    ]
    committed_route_checks = (
        "trigger_if = {\n"
        "\tlimit = {\n"
        + indent(
            "OR = {\n"
            + indent(receipt_guard(m360_spec, 1))
            + "\n"
            + indent(receipt_guard(m360_spec, 2))
            + "\n}",
            2,
        )
        + "\n\t}\n"
        + indent(chr(10).join(committed_ab_checks))
        + "\n}\ntrigger_else = {\n"
        + indent(chr(10).join(committed_c_checks))
        + "\n}"
    )

    mark = f"""# Central source changes READY -> consumed only after Workforce has
# committed the exact AL tuple.  No other Central field is rewritten.
{PREFIX}_mark_central_m360_source_consumed_effect = {{
	save_scope_as = {PREFIX}_m360_materialize_subject
	$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_materialize_owner }}
{indent(_central_m360_quota_prelude())}
	if = {{
		limit = {{
			$TICKET_SUBJECT$ = this
			$TICKET_OWNER$ = {{
{indent(chr(10).join(_central_m360_owner_checks(1)), 4)}
			}}
{indent(committed_route_checks, 3)}
		}}
		$TICKET_OWNER$ = {{ set_variable = {{ name = zg361_p2c_m360_source_status value = 2 }} }}
	}}
}}"""

    resume_checks = [
        f"zg361_case_kernel_full_guard_trigger = {{ OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$ EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4 }}",
        "$TICKET_SUBJECT$ = this",
        "$TICKET_SUBJECT$ = { zg361_is_celestial_liege_trigger = yes }",
        f"$TICKET_OWNER$ = {{\n{indent(chr(10).join(central_checks))}\n}}",
    ]
    resume = f"""# Public Central resume.  Human managers receive a route-neutral
# event; authorized AI materializes and consumes route A through the same ABI.
{PREFIX}_resume_m360_from_central_source_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	save_scope_as = {PREFIX}_m360_materialize_subject
	$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_materialize_owner }}
{indent(_central_m360_quota_prelude())}
	if = {{
		limit = {{
{indent(chr(10).join(resume_checks), 3)}
		}}
		$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_al_owner }}
		save_scope_as = {PREFIX}_al_subject
		save_scope_value_as = {{ name = {PREFIX}_al_cycle value = $TICKET_CYCLE$ }}
		save_scope_value_as = {{ name = {PREFIX}_al_case value = $TICKET_CASE$ }}
		{PREFIX}_al_schedule_stage_04_deadline_effect = yes
		if = {{
			limit = {{ $TICKET_OWNER$ = {{ is_ai = yes }} }}
			{PREFIX}_materialize_m360_route_a_from_central_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			if = {{
				limit = {{ OR = {{ var:{PREFIX}_adapter_status = 1 var:{PREFIX}_adapter_status = 2 }} }}
				{PREFIX}_m360_route_a_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			}}
		}}
		else_if = {{
			limit = {{ has_variable = {PREFIX}_m360_event_queued var:{PREFIX}_m360_event_queued = 1 var:{PREFIX}_m360_event_owner = $TICKET_OWNER$ var:{PREFIX}_m360_event_subject = $TICKET_SUBJECT$ var:{PREFIX}_m360_event_cycle = $TICKET_CYCLE$ var:{PREFIX}_m360_event_case = $TICKET_CASE$ }}
			set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
		}}
		else = {{
			set_variable = {{ name = {PREFIX}_m360_event_queued value = 1 }}
			set_variable = {{ name = {PREFIX}_m360_event_owner value = $TICKET_OWNER$ }}
			set_variable = {{ name = {PREFIX}_m360_event_subject value = $TICKET_SUBJECT$ }}
			set_variable = {{ name = {PREFIX}_m360_event_cycle value = $TICKET_CYCLE$ }}
			set_variable = {{ name = {PREFIX}_m360_event_case value = $TICKET_CASE$ }}
			set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
			$TICKET_OWNER$ = {{ trigger_event = {{ id = {NAMESPACE}.360 }} }}
		}}
	}}
	else_if = {{
		limit = {{
			$TICKET_SUBJECT$ = this
{indent(any_receipt(m360_spec), 3)}
		}}
		{PREFIX}_mark_central_m360_source_consumed_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		if = {{
			limit = {{ $TICKET_OWNER$ = {{ has_variable = zg361_p2c_m360_source_status var:zg361_p2c_m360_source_status = 2 }} }}
			set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
		}}
		else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3604 }} }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3604 }} }}
}}"""
    return "\n\n".join((route_materializer(1), route_materializer(2), mark, resume))


def render_completed_cycle_ledger() -> str:
    """Own the rolling #357-359 history and the product-generated #361 report."""

    identity_fields = ("owner", "subject", "cycle", "case")
    receipt_fields = tuple(
        f"m{mid}_receipt_{kind}"
        for mid in (357, 358, 359)
        for kind in ("id", "hash")
    )
    ledger_fields = (*identity_fields, *receipt_fields)

    shift_one = "\n".join(
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_{field}_1 value = var:{PREFIX}_completed_cycle_ledger_{field}_2 }}"
        for field in ledger_fields
    )
    shift_two = "\n".join(
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_{field}_2 value = var:{PREFIX}_completed_cycle_ledger_{field}_3 }}"
        for field in ledger_fields
    )

    def slot_writes(slot: int) -> str:
        rows = [
            f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_owner_{slot} value = $TICKET_OWNER$ }}",
            f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_subject_{slot} value = $TICKET_SUBJECT$ }}",
            f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_cycle_{slot} value = $TICKET_CYCLE$ }}",
            f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_case_{slot} value = $TICKET_CASE$ }}",
        ]
        for mid in (357, 358, 359):
            for kind in ("id", "hash"):
                rows.append(
                    f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_m{mid}_receipt_{kind}_{slot} "
                    f"value = scope:{PREFIX}_history_subject.var:{PREFIX}_al_external_m{mid}_receipt_{kind} }}"
                )
        return "\n".join(rows)

    last_writes = [
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_last_owner value = $TICKET_OWNER$ }}",
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_last_subject value = $TICKET_SUBJECT$ }}",
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_last_cycle value = $TICKET_CYCLE$ }}",
        f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_last_case value = $TICKET_CASE$ }}",
    ]
    for mid in (357, 358, 359):
        for kind in ("id", "hash"):
            last_writes.append(
                f"set_variable = {{ name = {PREFIX}_completed_cycle_ledger_last_m{mid}_receipt_{kind} "
                f"value = scope:{PREFIX}_history_subject.var:{PREFIX}_al_external_m{mid}_receipt_{kind} }}"
            )

    source_checks: list[str] = []
    for mid, state in ((357, 2), (358, 3), (359, 3)):
        for field in ("owner", "subject", "cycle", "case", "state", "receipt_id", "receipt_hash"):
            source_checks.append(f"has_variable = {PREFIX}_al_external_m{mid}_{field}")
        source_checks += [
            f"var:{PREFIX}_al_external_m{mid}_owner = $TICKET_OWNER$",
            f"var:{PREFIX}_al_external_m{mid}_subject = $TICKET_SUBJECT$",
            f"var:{PREFIX}_al_external_m{mid}_cycle = $TICKET_CYCLE$",
            f"var:{PREFIX}_al_external_m{mid}_case = $TICKET_CASE$",
            f"var:{PREFIX}_al_external_m{mid}_state = {state}",
            f"var:{PREFIX}_al_external_m{mid}_receipt_id > 0",
            f"var:{PREFIX}_al_external_m{mid}_receipt_hash > 0",
        ]
    source_checks += [
        f"NOT = {{ var:{PREFIX}_al_external_m357_receipt_id = var:{PREFIX}_al_external_m358_receipt_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_m357_receipt_id = var:{PREFIX}_al_external_m359_receipt_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_m358_receipt_id = var:{PREFIX}_al_external_m359_receipt_id }}",
        f"NOT = {{ var:{PREFIX}_al_external_m357_receipt_hash = var:{PREFIX}_al_external_m358_receipt_hash }}",
        f"NOT = {{ var:{PREFIX}_al_external_m357_receipt_hash = var:{PREFIX}_al_external_m359_receipt_hash }}",
        f"NOT = {{ var:{PREFIX}_al_external_m358_receipt_hash = var:{PREFIX}_al_external_m359_receipt_hash }}",
    ]

    idempotent_checks = [
        f"has_variable = {PREFIX}_completed_cycle_ledger_last_{field}"
        for field in ledger_fields
    ] + [
        f"var:{PREFIX}_completed_cycle_ledger_last_owner = $TICKET_OWNER$",
        f"var:{PREFIX}_completed_cycle_ledger_last_subject = $TICKET_SUBJECT$",
        f"var:{PREFIX}_completed_cycle_ledger_last_cycle = $TICKET_CYCLE$",
        f"var:{PREFIX}_completed_cycle_ledger_last_case = $TICKET_CASE$",
    ]
    for mid in (357, 358, 359):
        for kind in ("id", "hash"):
            idempotent_checks.append(
                f"var:{PREFIX}_completed_cycle_ledger_last_m{mid}_receipt_{kind} = "
                f"scope:{PREFIX}_history_subject.var:{PREFIX}_al_external_m{mid}_receipt_{kind}"
            )

    ledger_required: list[str] = []
    ledger_semantics: list[str] = [
        f"var:{PREFIX}_completed_cycle_ledger_count = 3",
        f"var:{PREFIX}_completed_cycle_ledger_cycle_1 < var:{PREFIX}_completed_cycle_ledger_cycle_2",
        f"var:{PREFIX}_completed_cycle_ledger_cycle_2 < var:{PREFIX}_completed_cycle_ledger_cycle_3",
        f"var:{PREFIX}_completed_cycle_ledger_cycle_3 = $TICKET_CYCLE$",
        f"var:{PREFIX}_completed_cycle_ledger_subject_3 = $TICKET_SUBJECT$",
        f"var:{PREFIX}_completed_cycle_ledger_case_3 = $TICKET_CASE$",
    ]
    for slot in (1, 2, 3):
        for field in ledger_fields:
            ledger_required.append(f"has_variable = {PREFIX}_completed_cycle_ledger_{field}_{slot}")
        ledger_semantics += [
            f"var:{PREFIX}_completed_cycle_ledger_owner_{slot} = $TICKET_OWNER$",
            f"var:{PREFIX}_completed_cycle_ledger_cycle_{slot} >= 1",
            f"var:{PREFIX}_completed_cycle_ledger_case_{slot} > 0",
        ]
        for mid in (357, 358, 359):
            ledger_semantics += [
                f"var:{PREFIX}_completed_cycle_ledger_m{mid}_receipt_id_{slot} > 0",
                f"var:{PREFIX}_completed_cycle_ledger_m{mid}_receipt_hash_{slot} > 0",
            ]

    evidence_writes: list[str] = []
    for slot in (1, 2, 3):
        for field in identity_fields:
            evidence_writes.append(
                f"set_variable = {{ name = {PREFIX}_m361_evidence_{field}_{slot} "
                f"value = var:zg361_case_al_owner.var:{PREFIX}_completed_cycle_ledger_{field}_{slot} }}"
            )
        for mid in (357, 358, 359):
            for kind in ("id", "hash"):
                evidence_writes.append(
                    f"set_variable = {{ name = {PREFIX}_m361_evidence_m{mid}_receipt_{kind}_{slot} "
                    f"value = var:zg361_case_al_owner.var:{PREFIX}_completed_cycle_ledger_m{mid}_receipt_{kind}_{slot} }}"
                )

    record = f"""# Product-owned rolling history.  The only source facts are the
# three strict #357-359 receipts already consumed by this live AL case.
{PREFIX}_record_completed_357_359_history_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	save_scope_as = {PREFIX}_history_subject
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}}
			$TICKET_SUBJECT$ = this
{indent(chr(10).join(source_checks), 3)}
			$TICKET_OWNER$ = {{
				zg361_is_celestial_liege_trigger = yes
				trigger_if = {{
					limit = {{ has_variable = {PREFIX}_completed_cycle_ledger_count var:{PREFIX}_completed_cycle_ledger_count > 0 }}
					has_variable = {PREFIX}_completed_cycle_ledger_last_cycle
					var:{PREFIX}_completed_cycle_ledger_last_cycle < $TICKET_CYCLE$
				}}
				trigger_else = {{ always = yes }}
			}}
		}}
		$TICKET_OWNER$ = {{
			if = {{ limit = {{ NOT = {{ has_variable = {PREFIX}_completed_cycle_ledger_count }} }} set_variable = {{ name = {PREFIX}_completed_cycle_ledger_count value = 0 }} }}
			if = {{
				limit = {{ var:{PREFIX}_completed_cycle_ledger_count >= 3 }}
{indent(shift_one, 4)}
{indent(shift_two, 4)}
			}}
			if = {{ limit = {{ var:{PREFIX}_completed_cycle_ledger_count < 3 }} change_variable = {{ name = {PREFIX}_completed_cycle_ledger_count add = 1 }} }}
			if = {{
				limit = {{ var:{PREFIX}_completed_cycle_ledger_count = 1 }}
{indent(slot_writes(1), 4)}
			}}
			else_if = {{
				limit = {{ var:{PREFIX}_completed_cycle_ledger_count = 2 }}
{indent(slot_writes(2), 4)}
			}}
			else = {{
{indent(slot_writes(3), 4)}
			}}
{indent(chr(10).join(last_writes), 3)}
		}}
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else_if = {{
		limit = {{
			$TICKET_SUBJECT$ = this
			$TICKET_OWNER$ = {{
{indent(chr(10).join(idempotent_checks), 4)}
			}}
		}}
		set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3611 }} }}
}}"""

    prepare = f"""# Once the rolling ledger contains three distinct real cycles, this
# product projects its own report and charter IDs.  No caller hash or prefilled
# charter field participates in the decision.
{PREFIX}_prepare_m361_charter_evidence_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 5
			}}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_m361_evidence_ready')}
			$TICKET_OWNER$ = {{
				zg361_is_celestial_liege_trigger = yes
				trigger_if = {{
					limit = {{ exists = liege }}
					NOT = {{ liege = {{ zg361_is_celestial_liege_trigger = yes }} }}
				}}
				trigger_else = {{ always = yes }}
				has_variable = {PREFIX}_realm_charter_current_version
				has_variable = {PREFIX}_realm_charter_current_id
				has_variable = {PREFIX}_realm_charter_current_report_id
				has_variable = {PREFIX}_realm_charter_current_adopted_cycle
				has_variable = {PREFIX}_realm_charter_current_effective_cycle
				has_variable = {PREFIX}_realm_charter_history_count
				has_variable = {PREFIX}_realm_charter_report_serial
				has_variable = {PREFIX}_realm_charter_id_serial
				var:{PREFIX}_realm_charter_history_count = var:{PREFIX}_realm_charter_current_version
{indent(chr(10).join(ledger_required), 4)}
{indent(chr(10).join(ledger_semantics), 4)}
			}}
		}}
		$TICKET_OWNER$ = {{
			change_variable = {{ name = {PREFIX}_realm_charter_report_serial add = 1 }}
			change_variable = {{ name = {PREFIX}_realm_charter_id_serial add = 1 }}
		}}
		set_variable = {{ name = {PREFIX}_m361_evidence_count value = 3 }}
		set_variable = {{ name = {PREFIX}_m361_evidence_ready value = 1 }}
		set_variable = {{ name = {PREFIX}_m361_evidence_consumed value = 0 }}
		set_variable = {{ name = {PREFIX}_m361_evidence_owner value = $TICKET_OWNER$ }}
		set_variable = {{ name = {PREFIX}_m361_evidence_subject value = $TICKET_SUBJECT$ }}
		set_variable = {{ name = {PREFIX}_m361_evidence_cycle value = $TICKET_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_m361_evidence_case value = $TICKET_CASE$ }}
		set_variable = {{ name = {PREFIX}_m361_evidence_state value = 5 }}
		set_variable = {{ name = {PREFIX}_m361_prepared_report_id value = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_report_serial }}
		set_variable = {{ name = {PREFIX}_m361_prepared_charter_id value = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_id_serial }}
		set_variable = {{ name = {PREFIX}_m361_prepared_previous_charter_id value = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_id }}
		set_variable = {{ name = {PREFIX}_m361_prepared_previous_version value = var:zg361_case_al_owner.var:{PREFIX}_realm_charter_current_version }}
		set_variable = {{ name = {PREFIX}_m361_prepared_adopted_cycle value = $TICKET_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_m361_prepared_effective_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }} }}
{indent(chr(10).join(evidence_writes), 2)}
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else_if = {{
		limit = {{
			has_variable = {PREFIX}_m361_evidence_ready
			var:{PREFIX}_m361_evidence_ready = 1
			var:{PREFIX}_m361_evidence_owner = $TICKET_OWNER$
			var:{PREFIX}_m361_evidence_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m361_evidence_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m361_evidence_case = $TICKET_CASE$
			var:{PREFIX}_m361_evidence_state = 5
		}}
		set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3612 }} }}
}}"""

    history_finalize = f"""# The first two distinct cycles have no three-cycle
# report yet.  After #360 they close as an honest history-accruing terminal;
# no #361 receipt, business object, charter or success is fabricated.
{PREFIX}_finalize_history_accruing_effect = {{
	remove_variable = {PREFIX}_runtime_applied
	save_scope_as = {PREFIX}_history_finalize_subject
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = var:zg361_case_al_owner EXPECTED_SUBJECT = this
				EXPECTED_CYCLE = var:zg361_case_al_cycle_serial EXPECTED_CASE = var:zg361_case_al_case_serial
				EXPECTED_STATE = 5
			}}
			var:zg361_case_al_owner = {{
				has_variable = {PREFIX}_completed_cycle_ledger_count
				var:{PREFIX}_completed_cycle_ledger_count >= 1
				var:{PREFIX}_completed_cycle_ledger_count <= 3
				var:{PREFIX}_completed_cycle_ledger_last_owner = this
				var:{PREFIX}_completed_cycle_ledger_last_subject = scope:{PREFIX}_history_finalize_subject
				var:{PREFIX}_completed_cycle_ledger_last_cycle = scope:{PREFIX}_history_finalize_subject.var:zg361_case_al_cycle_serial
				var:{PREFIX}_completed_cycle_ledger_last_case = scope:{PREFIX}_history_finalize_subject.var:zg361_case_al_case_serial
				OR = {{
					var:{PREFIX}_completed_cycle_ledger_count < 3
					AND = {{ exists = liege liege = {{ zg361_is_celestial_liege_trigger = yes }} }}
				}}
			}}
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
			var:{PREFIX}_operation_used = {CHARTER_HISTORY_ACCRUAL_OPERATION_COUNT}
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
				var:{PREFIX}_final_operation_check = {CHARTER_HISTORY_ACCRUAL_OPERATION_COUNT}
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
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state REVISION_VAR = zg361_case_al_revision
				ACTIVE_VAR = zg361_case_al_active TIMELINE_VAR = zg361_case_al_timeline_serial
				FEEDBACK_VAR = zg361_case_al_feedback_revision LAST_HOOK_VAR = zg361_case_al_last_hook
				TICKET_OWNER = var:zg361_case_al_owner TICKET_SUBJECT = this
				TICKET_CYCLE = var:zg361_case_al_cycle_serial TICKET_CASE = var:zg361_case_al_case_serial
				TICKET_STATE = 5 NEXT_STATE = 8 HOOK_ID = 9362 CLOSE_CASE = yes
			}}
			if = {{
				limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 var:zg361_case_al_active = 0 var:zg361_case_al_state = 8 }}
				set_variable = {{ name = {PREFIX}_final_conservation_ok value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_history_accruing value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_history_cycle_count value = var:zg361_case_al_owner.var:{PREFIX}_completed_cycle_ledger_count }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_owned_operations value = {CHARTER_HISTORY_ACCRUAL_OPERATION_COUNT} }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_skipped_charter value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_success value = 0 }}
				set_variable = {{ name = {PREFIX}_portfolio_closed value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_status value = 8 }}
				set_variable = {{ name = {PREFIX}_runtime_applied value = 1 }}
				set_variable = {{ name = {PREFIX}_runtime_status value = 1 }}
				debug_log = "ZG361WE: portfolio closed after #360 while official history accrues"
			}}
			else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 9097 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
		}}
		else = {{
			set_variable = {{ name = {PREFIX}_last_red_code value = 9097 }}
			set_variable = {{ name = {PREFIX}_runtime_status value = 4 }}
			debug_log = "ZG361WE RED: history-accruing conservation failed; AL remains active"
		}}
	}}
	else_if = {{
		limit = {{ has_variable = {PREFIX}_portfolio_terminal_history_accruing var:{PREFIX}_portfolio_terminal_history_accruing = 1 var:{PREFIX}_portfolio_closed = 1 var:{PREFIX}_portfolio_status = 8 var:zg361_case_al_active = 0 }}
		set_variable = {{ name = {PREFIX}_runtime_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 9097 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
}}"""

    gate = f"""# #360 is the history gate: cycles one and two close honestly;
# cycle three (and later rolling windows) alone prepares and exposes #361.
{PREFIX}_after_m360_history_gate_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	save_scope_as = {PREFIX}_history_gate_subject
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = var:zg361_case_al_owner EXPECTED_SUBJECT = this
				EXPECTED_CYCLE = var:zg361_case_al_cycle_serial EXPECTED_CASE = var:zg361_case_al_case_serial
				EXPECTED_STATE = 5
			}}
			var:zg361_case_al_owner = {{
				has_variable = {PREFIX}_completed_cycle_ledger_count
				var:{PREFIX}_completed_cycle_ledger_count >= 1
				var:{PREFIX}_completed_cycle_ledger_count <= 3
				var:{PREFIX}_completed_cycle_ledger_last_owner = this
				var:{PREFIX}_completed_cycle_ledger_last_subject = scope:{PREFIX}_history_gate_subject
				var:{PREFIX}_completed_cycle_ledger_last_cycle = scope:{PREFIX}_history_gate_subject.var:zg361_case_al_cycle_serial
				var:{PREFIX}_completed_cycle_ledger_last_case = scope:{PREFIX}_history_gate_subject.var:zg361_case_al_case_serial
			}}
		}}
		if = {{
			limit = {{
				var:zg361_case_al_owner = {{
					var:{PREFIX}_completed_cycle_ledger_count = 3
					trigger_if = {{ limit = {{ exists = liege }} NOT = {{ liege = {{ zg361_is_celestial_liege_trigger = yes }} }} }}
					trigger_else = {{ always = yes }}
				}}
			}}
			{PREFIX}_prepare_m361_charter_evidence_effect = {{
				TICKET_OWNER = var:zg361_case_al_owner TICKET_SUBJECT = this
				TICKET_CYCLE = var:zg361_case_al_cycle_serial TICKET_CASE = var:zg361_case_al_case_serial
			}}
			if = {{
				limit = {{
					OR = {{ var:{PREFIX}_adapter_status = 1 var:{PREFIX}_adapter_status = 2 }}
					has_variable = {PREFIX}_m361_evidence_ready
					var:{PREFIX}_m361_evidence_ready = 1
					var:{PREFIX}_m361_evidence_owner = var:zg361_case_al_owner
					var:{PREFIX}_m361_evidence_subject = this
					var:{PREFIX}_m361_evidence_cycle = var:zg361_case_al_cycle_serial
					var:{PREFIX}_m361_evidence_case = var:zg361_case_al_case_serial
				}}
				{PREFIX}_al_schedule_stage_05_deadline_effect = yes
				if = {{
					limit = {{ var:zg361_case_al_owner = {{ is_ai = yes zg361_is_celestial_liege_trigger = yes }} }}
					{PREFIX}_m361_route_a_effect = {{
						TICKET_OWNER = var:zg361_case_al_owner TICKET_SUBJECT = this
						TICKET_CYCLE = var:zg361_case_al_cycle_serial TICKET_CASE = var:zg361_case_al_case_serial
					}}
				}}
			}}
			else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 3613 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
		}}
		else = {{ {PREFIX}_finalize_history_accruing_effect = yes }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 3614 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
}}"""

    return "\n\n".join((record, prepare, history_finalize, gate))


def render_al_357_359_receipt_bridge() -> str:
    """Consume three external receipts and advance only their real AL edges.

    The B1/B2 providers remain separate owners.  This effect is deliberately a
    strict adapter: a caller must supply each provider's immutable five-tuple
    plus a nonzero receipt id/hash.  Merely setting a readiness boolean cannot
    move the AL case.
    """

    return f"""# 357-359 are owned outside this module.  This bridge consumes
# their exact receipts; it does not manufacture their underlying decisions.
{PREFIX}_submit_al_357_359_receipts_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 2
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
			$TICKET_OWNER$ = {{
				trigger_if = {{
					limit = {{ has_variable = {PREFIX}_completed_cycle_ledger_count var:{PREFIX}_completed_cycle_ledger_count > 0 }}
					has_variable = {PREFIX}_completed_cycle_ledger_last_cycle
					var:{PREFIX}_completed_cycle_ledger_last_cycle < $TICKET_CYCLE$
				}}
				trigger_else = {{ always = yes }}
			}}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_al_external_stage_receipts_verified')}
			$M357_OWNER$ = $TICKET_OWNER$ $M357_SUBJECT$ = $TICKET_SUBJECT$
			$M357_CYCLE$ = $TICKET_CYCLE$ $M357_CASE$ = $TICKET_CASE$ $M357_STATE$ = 2
			$M358_OWNER$ = $TICKET_OWNER$ $M358_SUBJECT$ = $TICKET_SUBJECT$
			$M358_CYCLE$ = $TICKET_CYCLE$ $M358_CASE$ = $TICKET_CASE$ $M358_STATE$ = 3
			$M359_OWNER$ = $TICKET_OWNER$ $M359_SUBJECT$ = $TICKET_SUBJECT$
			$M359_CYCLE$ = $TICKET_CYCLE$ $M359_CASE$ = $TICKET_CASE$ $M359_STATE$ = 3
			$M357_RECEIPT_ID$ > 0 $M357_RECEIPT_HASH$ > 0
			$M358_RECEIPT_ID$ > 0 $M358_RECEIPT_HASH$ > 0
			$M359_RECEIPT_ID$ > 0 $M359_RECEIPT_HASH$ > 0
			NOT = {{ $M357_RECEIPT_ID$ = $M358_RECEIPT_ID$ }}
			NOT = {{ $M357_RECEIPT_ID$ = $M359_RECEIPT_ID$ }}
			NOT = {{ $M358_RECEIPT_ID$ = $M359_RECEIPT_ID$ }}
			NOT = {{ $M357_RECEIPT_HASH$ = $M358_RECEIPT_HASH$ }}
			NOT = {{ $M357_RECEIPT_HASH$ = $M359_RECEIPT_HASH$ }}
			NOT = {{ $M358_RECEIPT_HASH$ = $M359_RECEIPT_HASH$ }}
		}}
		set_variable = {{ name = {PREFIX}_al_external_m357_owner value = $M357_OWNER$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_subject value = $M357_SUBJECT$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_cycle value = $M357_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_case value = $M357_CASE$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_state value = $M357_STATE$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_receipt_id value = $M357_RECEIPT_ID$ }}
		set_variable = {{ name = {PREFIX}_al_external_m357_receipt_hash value = $M357_RECEIPT_HASH$ }}
		zg361_case_al_advance_02_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
		if = {{
			limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 var:zg361_case_al_state = 3 }}
			set_variable = {{ name = {PREFIX}_al_external_m358_owner value = $M358_OWNER$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_subject value = $M358_SUBJECT$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_cycle value = $M358_CYCLE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_case value = $M358_CASE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_state value = $M358_STATE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_receipt_id value = $M358_RECEIPT_ID$ }}
			set_variable = {{ name = {PREFIX}_al_external_m358_receipt_hash value = $M358_RECEIPT_HASH$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_owner value = $M359_OWNER$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_subject value = $M359_SUBJECT$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_cycle value = $M359_CYCLE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_case value = $M359_CASE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_state value = $M359_STATE$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_receipt_id value = $M359_RECEIPT_ID$ }}
			set_variable = {{ name = {PREFIX}_al_external_m359_receipt_hash value = $M359_RECEIPT_HASH$ }}
			zg361_case_al_advance_03_effect = {{ TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$ TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$ }}
			if = {{
				limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 var:zg361_case_al_state = 4 }}
				{PREFIX}_record_completed_357_359_history_effect = {{
					TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
					TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
				}}
				if = {{
					limit = {{ has_variable = {PREFIX}_adapter_status var:{PREFIX}_adapter_status = 1 }}
					set_variable = {{ name = {PREFIX}_al_external_stage_receipts_verified value = 1 }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_owner value = $TICKET_OWNER$ }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_subject value = $TICKET_SUBJECT$ }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_cycle value = $TICKET_CYCLE$ }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_case value = $TICKET_CASE$ }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_state value = 4 }}
					set_variable = {{ name = {PREFIX}_al_external_receipt_count value = 3 }}
					set_variable = {{ name = {PREFIX}_al_external_last_operation value = 359 }}
					set_variable = {{ name = {PREFIX}_awaiting_al_357_359 value = 0 }}
				}}
				else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3594 }} }}
			}}
			else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3593 }} }}
		}}
		else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3572 }} }}
	}}
	else_if = {{
		limit = {{ has_variable = {PREFIX}_al_external_stage_receipts_verified var:{PREFIX}_al_external_stage_receipts_verified = 1 var:zg361_case_al_state >= 4 }}
		set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 3571 }} }}
}}"""


def render_ac_real_fact_producers() -> str:
    """Produce #262/#264 facts from real characters, events and case objects."""

    current_handoff_objects = "\n".join(_current_object_checks(by_id()[264]))
    return f"""# #262 freezes one real host manager.  Prefer the owner's own
# eligible celestial liege, then the strongest other eligible manager-vassal.
# No candidate means typed blocked; this effect never invents a character.
{PREFIX}_ac_freeze_m262_host_manager_effect = {{
	remove_variable = {PREFIX}_m262_host_selection_status
	remove_variable = {PREFIX}_m262_host_selection_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ac_owner SUBJECT_VAR = zg361_case_ac_subject
				CYCLE_VAR = zg361_case_ac_cycle_serial CASE_VAR = zg361_case_ac_case_serial
				STATE_VAR = zg361_case_ac_state ACTIVE_VAR = zg361_case_ac_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}}
			$TICKET_SUBJECT$ = this
			has_variable = {PREFIX}_m262_host_owner
			has_variable = {PREFIX}_m262_host_subject
			has_variable = {PREFIX}_m262_host_cycle
			has_variable = {PREFIX}_m262_host_case
			has_variable = {PREFIX}_ac_external_secondment_host_manager
			var:{PREFIX}_m262_host_owner = $TICKET_OWNER$
			var:{PREFIX}_m262_host_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m262_host_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m262_host_case = $TICKET_CASE$
			var:{PREFIX}_ac_external_secondment_host_manager = {{ zg361_is_celestial_liege_trigger = yes }}
			NOT = {{ var:{PREFIX}_ac_external_secondment_host_manager = $TICKET_OWNER$ }}
			NOT = {{ var:{PREFIX}_ac_external_secondment_host_manager = $TICKET_SUBJECT$ }}
		}}
		set_variable = {{ name = {PREFIX}_m262_host_selection_status value = 2 }}
	}}
	else_if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ac_owner SUBJECT_VAR = zg361_case_ac_subject
				CYCLE_VAR = zg361_case_ac_cycle_serial CASE_VAR = zg361_case_ac_case_serial
				STATE_VAR = zg361_case_ac_state ACTIVE_VAR = zg361_case_ac_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
			$TICKET_SUBJECT$ = this
		}}
		remove_variable = {PREFIX}_ac_external_secondment_host_manager
		remove_variable = {PREFIX}_m262_host_owner
		remove_variable = {PREFIX}_m262_host_subject
		remove_variable = {PREFIX}_m262_host_cycle
		remove_variable = {PREFIX}_m262_host_case
		save_temporary_scope_as = {PREFIX}_m262_host_subject_scope
		$TICKET_OWNER$ = {{
			save_temporary_scope_as = {PREFIX}_m262_host_owner_scope
			if = {{
				limit = {{ exists = liege liege = {{ zg361_is_celestial_liege_trigger = yes NOT = {{ this = scope:{PREFIX}_m262_host_subject_scope }} }} }}
				liege = {{ save_temporary_scope_as = {PREFIX}_m262_host_candidate_scope }}
			}}
			if = {{
				limit = {{ NOT = {{ exists = scope:{PREFIX}_m262_host_candidate_scope }} }}
				ordered_vassal = {{
					limit = {{ zg361_is_celestial_liege_trigger = yes NOT = {{ this = scope:{PREFIX}_m262_host_subject_scope }} }}
					order_by = stewardship
					position = 0
					save_temporary_scope_as = {PREFIX}_m262_host_candidate_scope
				}}
			}}
		}}
		if = {{
			limit = {{ exists = scope:{PREFIX}_m262_host_candidate_scope }}
			set_variable = {{ name = {PREFIX}_ac_external_secondment_host_manager value = scope:{PREFIX}_m262_host_candidate_scope }}
			set_variable = {{ name = {PREFIX}_m262_host_owner value = $TICKET_OWNER$ }}
			set_variable = {{ name = {PREFIX}_m262_host_subject value = $TICKET_SUBJECT$ }}
			set_variable = {{ name = {PREFIX}_m262_host_cycle value = $TICKET_CYCLE$ }}
			set_variable = {{ name = {PREFIX}_m262_host_case value = $TICKET_CASE$ }}
			set_variable = {{ name = {PREFIX}_m262_host_selection_status value = 1 }}
		}}
		else = {{
			set_variable = {{ name = {PREFIX}_m262_host_selection_status value = 4 }}
			set_variable = {{ name = {PREFIX}_m262_host_selection_blocked_reason value = 2621 }}
		}}
	}}
	else = {{
		set_variable = {{ name = {PREFIX}_m262_host_selection_status value = 4 }}
		set_variable = {{ name = {PREFIX}_m262_host_selection_blocked_reason value = 2622 }}
	}}
}}

# #263 completion opens a genuine subject-owned handoff.  When either actor is
# human, each milestone receipt is generated only by that player's explicit
# response option.  The authorized AI exception executes the same guarded
# milestones in the background and never receives a visible player event.
{PREFIX}_m264_begin_handoff_effect = {{
	remove_variable = {PREFIX}_m264_handoff_status
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ac_owner SUBJECT_VAR = zg361_case_ac_subject
				CYCLE_VAR = zg361_case_ac_cycle_serial CASE_VAR = zg361_case_ac_case_serial
				STATE_VAR = zg361_case_ac_state ACTIVE_VAR = zg361_case_ac_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 6
			}}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_m264_handoff_flow_active')}
{indent(current_handoff_objects, 3)}
		}}
		remove_variable = {PREFIX}_m264_documentation_receipt_id
		remove_variable = {PREFIX}_m264_shadowing_receipt_id
		remove_variable = {PREFIX}_m264_practical_receipt_id
		remove_variable = {PREFIX}_m264_handoff_documentation_source_object
		remove_variable = {PREFIX}_m264_handoff_shadowing_source_object
		remove_variable = {PREFIX}_m264_handoff_practical_source_object
		remove_variable = {PREFIX}_m264_handoff_refusal_reason
		set_variable = {{ name = {PREFIX}_m264_handoff_flow_active value = 1 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_flow_consumed value = 0 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_owner value = $TICKET_OWNER$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_subject value = $TICKET_SUBJECT$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_cycle value = $TICKET_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_case value = $TICKET_CASE$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_contract_id value = var:{PREFIX}_m254_contract_id }}
		set_variable = {{ name = {PREFIX}_m264_handoff_step value = 1 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_response value = 0 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_status value = 1 }}
		{PREFIX}_m264_dispatch_handoff_step_1_effect = yes
	}}
	else = {{ set_variable = {{ name = {PREFIX}_m264_handoff_status value = 4 }} }}
}}

{PREFIX}_m264_dispatch_handoff_step_1_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 1 }}
		save_scope_as = {PREFIX}_m264_handoff_subject_scope
		var:{PREFIX}_m264_handoff_owner = {{ save_scope_as = {PREFIX}_m264_handoff_owner_scope }}
		if = {{ limit = {{ is_ai = no }} trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[1]} }} }}
		else_if = {{ limit = {{ var:{PREFIX}_m264_handoff_owner = {{ is_ai = no }} }} var:{PREFIX}_m264_handoff_owner = {{ trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[1]} }} }} }}
		else = {{ {PREFIX}_m264_complete_documentation_effect = yes }}
	}}
}}

{PREFIX}_m264_dispatch_handoff_step_2_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 2 }}
		save_scope_as = {PREFIX}_m264_handoff_subject_scope
		var:{PREFIX}_m264_handoff_owner = {{ save_scope_as = {PREFIX}_m264_handoff_owner_scope }}
		if = {{ limit = {{ is_ai = no }} trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[2]} }} }}
		else_if = {{ limit = {{ var:{PREFIX}_m264_handoff_owner = {{ is_ai = no }} }} var:{PREFIX}_m264_handoff_owner = {{ trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[2]} }} }} }}
		else = {{ {PREFIX}_m264_complete_shadowing_effect = yes }}
	}}
}}

{PREFIX}_m264_dispatch_handoff_step_3_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 3 }}
		save_scope_as = {PREFIX}_m264_handoff_subject_scope
		var:{PREFIX}_m264_handoff_owner = {{ save_scope_as = {PREFIX}_m264_handoff_owner_scope }}
		if = {{ limit = {{ is_ai = no }} trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[3]} }} }}
		else_if = {{ limit = {{ var:{PREFIX}_m264_handoff_owner = {{ is_ai = no }} }} var:{PREFIX}_m264_handoff_owner = {{ trigger_event = {{ id = {NAMESPACE}.{HANDOFF_EVENT[3]} }} }} }}
		else = {{ {PREFIX}_m264_complete_practical_effect = yes }}
	}}
}}

{PREFIX}_m264_queue_owner_review_effect = {{
	if = {{
		limit = {{
			has_variable = {PREFIX}_m264_handoff_flow_active
			has_variable = {PREFIX}_m264_handoff_flow_consumed
			has_variable = {PREFIX}_m264_handoff_owner
			has_variable = {PREFIX}_m264_handoff_subject
			has_variable = {PREFIX}_m264_handoff_cycle
			has_variable = {PREFIX}_m264_handoff_case
			has_variable = {PREFIX}_m264_handoff_response
			var:{PREFIX}_m264_handoff_flow_active = 1
			var:{PREFIX}_m264_handoff_flow_consumed = 0
			var:{PREFIX}_m264_handoff_subject = this
			OR = {{ var:{PREFIX}_m264_handoff_response = 1 var:{PREFIX}_m264_handoff_response = 2 }}
			var:zg361_case_ac_active = 1
			var:zg361_case_ac_state = 6
			var:zg361_case_ac_owner = var:{PREFIX}_m264_handoff_owner
			var:zg361_case_ac_subject = this
			var:zg361_case_ac_cycle_serial = var:{PREFIX}_m264_handoff_cycle
			var:zg361_case_ac_case_serial = var:{PREFIX}_m264_handoff_case
		}}
		var:{PREFIX}_m264_handoff_owner = {{ save_scope_as = {PREFIX}_ac_owner }}
		save_scope_as = {PREFIX}_ac_subject
		save_scope_value_as = {{ name = {PREFIX}_ac_cycle value = var:{PREFIX}_m264_handoff_cycle }}
		save_scope_value_as = {{ name = {PREFIX}_ac_case value = var:{PREFIX}_m264_handoff_case }}
		set_variable = {{ name = {PREFIX}_m264_handoff_owner_queued value = 1 }}
		if = {{
			limit = {{ var:{PREFIX}_m264_handoff_owner = {{ is_ai = yes }} }}
			if = {{
				limit = {{ var:{PREFIX}_m264_handoff_response = 1 }}
				{PREFIX}_m264_route_a_effect = {{ TICKET_OWNER = var:{PREFIX}_m264_handoff_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m264_handoff_cycle TICKET_CASE = var:{PREFIX}_m264_handoff_case }}
			}}
			else = {{ {PREFIX}_m264_route_b_effect = {{ TICKET_OWNER = var:{PREFIX}_m264_handoff_owner TICKET_SUBJECT = this TICKET_CYCLE = var:{PREFIX}_m264_handoff_cycle TICKET_CASE = var:{PREFIX}_m264_handoff_case }} }}
			if = {{ limit = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }} {PREFIX}_m265_route_a_effect = {{ TICKET_OWNER = var:zg361_case_ac_owner TICKET_SUBJECT = this TICKET_CYCLE = var:zg361_case_ac_cycle_serial TICKET_CASE = var:zg361_case_ac_case_serial }} }}
		}}
		else = {{ var:{PREFIX}_m264_handoff_owner = {{ trigger_event = {{ id = {NAMESPACE}.264 }} }} }}
	}}
}}

{PREFIX}_m264_complete_documentation_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 1 has_variable = {PREFIX}_m261_object_id var:{PREFIX}_m261_object_consumed = 1 }}
		set_variable = {{ name = {PREFIX}_m264_documentation_receipt_id value = {{ value = var:{PREFIX}_m264_handoff_case multiply = 10000 add = 2641 }} }}
		set_variable = {{ name = {PREFIX}_m264_handoff_documentation_source_object value = var:{PREFIX}_m261_object_id }}
		set_variable = {{ name = {PREFIX}_m264_handoff_step value = 2 }}
		trigger_event = {{ id = {NAMESPACE}.{HANDOFF_RELAY_EVENT[2]} days = 30 }}
	}}
}}

{PREFIX}_m264_complete_shadowing_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 2 has_variable = {PREFIX}_m264_documentation_receipt_id has_variable = {PREFIX}_m263_object_id var:{PREFIX}_m263_object_consumed = 1 }}
		set_variable = {{ name = {PREFIX}_m264_shadowing_receipt_id value = {{ value = var:{PREFIX}_m264_handoff_case multiply = 10000 add = 2642 }} }}
		set_variable = {{ name = {PREFIX}_m264_handoff_shadowing_source_object value = var:{PREFIX}_m263_object_id }}
		set_variable = {{ name = {PREFIX}_m264_handoff_step value = 3 }}
		trigger_event = {{ id = {NAMESPACE}.{HANDOFF_RELAY_EVENT[3]} days = 30 }}
	}}
}}

{PREFIX}_m264_complete_practical_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_step = 3 has_variable = {PREFIX}_m264_shadowing_receipt_id has_variable = {PREFIX}_m256_object_id var:{PREFIX}_m256_object_consumed = 1 }}
		set_variable = {{ name = {PREFIX}_m264_practical_receipt_id value = {{ value = var:{PREFIX}_m264_handoff_case multiply = 10000 add = 2643 }} }}
		set_variable = {{ name = {PREFIX}_m264_handoff_practical_source_object value = var:{PREFIX}_m256_object_id }}
		set_variable = {{ name = {PREFIX}_m264_handoff_step value = 4 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_response value = 1 }}
		{PREFIX}_m264_queue_owner_review_effect = yes
	}}
}}

{PREFIX}_m264_refuse_handoff_effect = {{
	if = {{
		limit = {{ var:{PREFIX}_m264_handoff_flow_active = 1 var:{PREFIX}_m264_handoff_flow_consumed = 0 var:{PREFIX}_m264_handoff_subject = this var:{PREFIX}_m264_handoff_response = 0 var:{PREFIX}_m264_handoff_step = $EXPECTED_STEP$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_refusal_reason value = $EXPECTED_STEP$ }}
		set_variable = {{ name = {PREFIX}_m264_handoff_step value = 5 }}
		set_variable = {{ name = {PREFIX}_m264_handoff_response value = 2 }}
		{PREFIX}_m264_queue_owner_review_effect = yes
	}}
}}"""


def render_external_fact_adapters() -> str:
    """Strict product-owned adapters for facts that CK3 must not fabricate."""

    return f"""# Native court-position assignment remains external.  This adapter accepts only
# an already-confirmed appointment receipt bound to the live offer tuple.
{PREFIX}_submit_ad_appointment_receipt_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_ad_external_appointment_ready')}
			has_variable = {PREFIX}_m272_offer_candidate
			has_variable = {PREFIX}_m273_candidate_fingerprint
			var:{PREFIX}_m272_offer_candidate = $TICKET_SUBJECT$
			var:{PREFIX}_m273_candidate_fingerprint = $TICKET_SUBJECT$
			$APPOINTING_OWNER$ = $TICKET_OWNER$
			$APPOINTMENT_CONFIRMED$ = 1
			$POSITION_TYPE_ID$ > 0
			$POSITION_RECEIPT_ID$ > 0
			$POSITION_RECEIPT_HASH$ > 0
		}}
		set_variable = {{ name = {PREFIX}_ad_external_appointment_ready value = 1 }}
		set_variable = {{ name = {PREFIX}_ad_external_appointment_consumed value = 0 }}
		set_variable = {{ name = {PREFIX}_ad_external_appointing_owner value = $APPOINTING_OWNER$ }}
		set_variable = {{ name = {PREFIX}_ad_external_position_type_id value = $POSITION_TYPE_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_position_receipt_id value = $POSITION_RECEIPT_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_position_receipt_hash value = $POSITION_RECEIPT_HASH$ }}
		set_variable = {{ name = {PREFIX}_ad_appointment_receipt_owner value = $TICKET_OWNER$ }}
		set_variable = {{ name = {PREFIX}_ad_appointment_receipt_subject value = $TICKET_SUBJECT$ }}
		set_variable = {{ name = {PREFIX}_ad_appointment_receipt_cycle value = $TICKET_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_ad_appointment_receipt_case value = $TICKET_CASE$ }}
		set_variable = {{ name = {PREFIX}_ad_appointment_receipt_state value = 4 }}
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 2741 }} }}
}}

# Consume the canonical Central recruitment source for #275.  The caller may
# provide only the original five-tuple; runner identity, evidence, new case and
# receipt/hash are joined from Central's committed subject-local source.
# The #266 reservation/receipt and formal HC count remain untouched.  A
# successful consume transfers the existing owner flight from the refused case
# to Central's distinct new case; it never reserves or releases another slot.
{PREFIX}_consume_m275_runner_reopen_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			has_variable = {PREFIX}_m275_runner_reopen_pending
			var:{PREFIX}_m275_runner_reopen_pending = 1
			has_variable = {PREFIX}_m275_business_object_created
			has_variable = {PREFIX}_m275_object_owner
			has_variable = {PREFIX}_m275_object_subject
			has_variable = {PREFIX}_m275_object_cycle
			has_variable = {PREFIX}_m275_object_case
			has_variable = {PREFIX}_m275_object_state
			has_variable = {PREFIX}_m275_object_consumed
			has_variable = {PREFIX}_m275_consumer_resolve_offer_refusal_hc_hold_275
			var:{PREFIX}_m275_business_object_created = 1
			var:{PREFIX}_m275_object_owner = $TICKET_OWNER$
			var:{PREFIX}_m275_object_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m275_object_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m275_object_case = $TICKET_CASE$
			var:{PREFIX}_m275_object_state = 4
			var:{PREFIX}_m275_object_consumed = 1
			var:{PREFIX}_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1
			has_variable = {PREFIX}_m275_receipt_choice
			has_variable = {PREFIX}_m275_refusal
			has_variable = {PREFIX}_m275_not_applicable_hired
			has_variable = {PREFIX}_m275_hold_pending
			has_variable = {PREFIX}_m275_runner_up
			has_variable = {PREFIX}_m275_runner_up_evidence
			has_variable = {PREFIX}_m275_hc_lineage_receipt
			has_variable = {PREFIX}_candidate_active
			has_variable = {PREFIX}_m266_hc_reservation_active
			has_variable = {PREFIX}_m266_hc_receipt
			var:{PREFIX}_m275_receipt_choice = 1
			var:{PREFIX}_m275_refusal = 1
			var:{PREFIX}_m275_not_applicable_hired = 0
			var:{PREFIX}_m275_hold_pending = 1
			var:{PREFIX}_candidate_active = 0
			var:{PREFIX}_m266_hc_reservation_active = 1
			var:{PREFIX}_m266_hc_receipt = var:{PREFIX}_m275_hc_lineage_receipt
			var:{PREFIX}_m275_write_owner = $TICKET_OWNER$
			var:{PREFIX}_m275_write_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m275_write_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m275_write_case = $TICKET_CASE$
			NOT = {{ var:{PREFIX}_m275_runner_up = $TICKET_SUBJECT$ }}
			var:{PREFIX}_m275_runner_up_evidence > 0
			$TICKET_OWNER$ = {{
				has_variable = {PREFIX}_ad_hc_flight_pending
				var:{PREFIX}_ad_hc_flight_pending = 1
				var:{PREFIX}_ad_hc_flight_subject = $TICKET_SUBJECT$
				var:{PREFIX}_ad_hc_flight_cycle = $TICKET_CYCLE$
				var:{PREFIX}_ad_hc_flight_case = $TICKET_CASE$
			}}
			has_variable = zg361_p2c_m275_requisition_committed
			has_variable = zg361_p2c_m275_requisition_pending
			has_variable = zg361_p2c_m275_requisition_consumed
			has_variable = zg361_p2c_m275_requisition_owner
			has_variable = zg361_p2c_m275_requisition_original_subject
			has_variable = zg361_p2c_m275_requisition_source_cycle
			has_variable = zg361_p2c_m275_requisition_source_case
			has_variable = zg361_p2c_m275_requisition_source_state
			has_variable = zg361_p2c_m275_requisition_runner_up
			has_variable = zg361_p2c_m275_requisition_runner_evidence
			has_variable = zg361_p2c_m275_requisition_hc_lineage_receipt
			has_variable = zg361_p2c_m275_requisition_hc_flight_case
			has_variable = zg361_p2c_m275_requisition_new_case
			has_variable = zg361_p2c_m275_requisition_new_state
			has_variable = zg361_p2c_m275_requisition_receipt_id
			has_variable = zg361_p2c_m275_requisition_receipt_hash
			has_variable = zg361_p2c_m275_requisition_opened
			var:zg361_p2c_m275_requisition_committed = 1
			var:zg361_p2c_m275_requisition_pending = 1
			var:zg361_p2c_m275_requisition_consumed = 0
			var:zg361_p2c_m275_requisition_owner = $TICKET_OWNER$
			var:zg361_p2c_m275_requisition_original_subject = $TICKET_SUBJECT$
			var:zg361_p2c_m275_requisition_source_cycle = $TICKET_CYCLE$
			var:zg361_p2c_m275_requisition_source_case = $TICKET_CASE$
			var:zg361_p2c_m275_requisition_source_state = 4
			var:zg361_p2c_m275_requisition_runner_up = var:{PREFIX}_m275_runner_up
			var:zg361_p2c_m275_requisition_runner_evidence = var:{PREFIX}_m275_runner_up_evidence
			var:zg361_p2c_m275_requisition_hc_lineage_receipt = var:{PREFIX}_m275_hc_lineage_receipt
			var:zg361_p2c_m275_requisition_hc_flight_case = $TICKET_CASE$
			var:zg361_p2c_m275_requisition_new_case > 0
			NOT = {{ var:zg361_p2c_m275_requisition_new_case = $TICKET_CASE$ }}
			var:zg361_p2c_m275_requisition_new_state = 1
			var:zg361_p2c_m275_requisition_receipt_id > 0
			var:zg361_p2c_m275_requisition_receipt_hash > 0
			var:zg361_p2c_m275_requisition_opened = 1
		}}
		set_variable = {{ name = {PREFIX}_m275_runner_new_case value = var:zg361_p2c_m275_requisition_new_case }}
		set_variable = {{ name = {PREFIX}_m275_runner_requisition_receipt_id value = var:zg361_p2c_m275_requisition_receipt_id }}
		set_variable = {{ name = {PREFIX}_m275_runner_requisition_receipt_hash value = var:zg361_p2c_m275_requisition_receipt_hash }}
		set_variable = {{ name = {PREFIX}_m275_runner_requisition_candidate value = var:zg361_p2c_m275_requisition_runner_up }}
		set_variable = {{ name = {PREFIX}_m275_runner_requisition_evidence value = var:zg361_p2c_m275_requisition_runner_evidence }}
		set_variable = {{ name = {PREFIX}_candidate_active value = 1 }}
		set_variable = {{ name = {PREFIX}_candidate_active_owner value = $TICKET_OWNER$ }}
		set_variable = {{ name = {PREFIX}_candidate_active_case value = var:zg361_p2c_m275_requisition_new_case }}
		set_variable = {{ name = {PREFIX}_candidate_active_character value = var:zg361_p2c_m275_requisition_runner_up }}
		$TICKET_OWNER$ = {{ set_variable = {{ name = {PREFIX}_ad_hc_flight_case value = root.var:zg361_p2c_m275_requisition_new_case }} }}
		set_variable = {{ name = {PREFIX}_m275_runner_attempt_opened value = 1 }}
		set_variable = {{ name = {PREFIX}_m275_old_attempt_reopened value = 0 }}
		set_variable = {{ name = {PREFIX}_m275_hold_released value = 0 }}
		set_variable = {{ name = {PREFIX}_m275_hold_pending value = 0 }}
		set_variable = {{ name = {PREFIX}_m275_runner_reopen_pending value = 0 }}
		set_variable = {{ name = {PREFIX}_m275_runner_reopen_consumed value = 1 }} # consumer commit last
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else_if = {{
		limit = {{
			has_variable = {PREFIX}_m275_runner_reopen_consumed
			var:{PREFIX}_m275_runner_reopen_consumed = 1
			var:{PREFIX}_m275_object_owner = $TICKET_OWNER$
			var:{PREFIX}_m275_object_subject = $TICKET_SUBJECT$
			var:{PREFIX}_m275_object_cycle = $TICKET_CYCLE$
			var:{PREFIX}_m275_object_case = $TICKET_CASE$
			var:{PREFIX}_m275_object_state = 4
			has_variable = zg361_p2c_m275_requisition_committed
			var:zg361_p2c_m275_requisition_committed = 1
			var:zg361_p2c_m275_requisition_owner = $TICKET_OWNER$
			var:zg361_p2c_m275_requisition_original_subject = $TICKET_SUBJECT$
			var:zg361_p2c_m275_requisition_source_cycle = $TICKET_CYCLE$
			var:zg361_p2c_m275_requisition_source_case = $TICKET_CASE$
			OR = {{
				AND = {{ var:zg361_p2c_m275_requisition_pending = 1 var:zg361_p2c_m275_requisition_consumed = 0 }}
				AND = {{ var:zg361_p2c_m275_requisition_pending = 0 var:zg361_p2c_m275_requisition_consumed = 1 }}
			}}
			var:{PREFIX}_m275_runner_new_case = var:zg361_p2c_m275_requisition_new_case
			var:{PREFIX}_m275_runner_requisition_receipt_id = var:zg361_p2c_m275_requisition_receipt_id
			var:{PREFIX}_m275_runner_requisition_receipt_hash = var:zg361_p2c_m275_requisition_receipt_hash
			var:{PREFIX}_m275_runner_requisition_candidate = var:zg361_p2c_m275_requisition_runner_up
			var:{PREFIX}_m275_runner_requisition_evidence = var:zg361_p2c_m275_requisition_runner_evidence
			var:{PREFIX}_candidate_active = 1
			var:{PREFIX}_candidate_active_owner = $TICKET_OWNER$
			var:{PREFIX}_candidate_active_case = var:zg361_p2c_m275_requisition_new_case
			var:{PREFIX}_candidate_active_character = var:zg361_p2c_m275_requisition_runner_up
			var:{PREFIX}_m275_hold_pending = 0
			var:{PREFIX}_m275_runner_reopen_pending = 0
			var:{PREFIX}_m266_hc_reservation_active = 1
			var:{PREFIX}_m266_hc_receipt = var:zg361_p2c_m275_requisition_hc_lineage_receipt
			$TICKET_OWNER$ = {{
				has_variable = {PREFIX}_ad_hc_flight_pending
				var:{PREFIX}_ad_hc_flight_pending = 1
				var:{PREFIX}_ad_hc_flight_subject = $TICKET_SUBJECT$
				var:{PREFIX}_ad_hc_flight_cycle = $TICKET_CYCLE$
				var:{PREFIX}_ad_hc_flight_case = root.var:zg361_p2c_m275_requisition_new_case
			}}
		}}
		set_variable = {{ name = {PREFIX}_adapter_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 2752 }} }}
}}

# #276 consumes a genuinely older immutable case, never the current case id.
{PREFIX}_submit_m276_rehire_history_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 6
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_ad_external_rehire_ready')}
			$REHIRE_ID$ > 0 $HISTORICAL_CASE_ID$ > 0 $HISTORICAL_CASE_HASH$ > 0
			$HISTORICAL_CYCLE$ < $TICKET_CYCLE$
			NOT = {{ $HISTORICAL_CASE_ID$ = $TICKET_CASE$ }}
			$GROWTH_EVIDENCE_ID$ > 0 $GROWTH_EVIDENCE_HASH$ > 0
			$FUTURE_COHORT_CYCLE$ > $TICKET_CYCLE$
			$HISTORY_RETAINED$ = 1 $MISCONDUCT_HISTORY_RETAINED$ = 1
		}}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_ready value = 1 }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_consumed value = 0 }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_id value = $REHIRE_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_historical_case_id value = $HISTORICAL_CASE_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_historical_case_hash value = $HISTORICAL_CASE_HASH$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_historical_cycle value = $HISTORICAL_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_growth_evidence_id value = $GROWTH_EVIDENCE_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_growth_evidence_hash value = $GROWTH_EVIDENCE_HASH$ }}
		set_variable = {{ name = {PREFIX}_ad_external_rehire_future_cohort_cycle value = $FUTURE_COHORT_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_ad_rehire_history_owner value = $TICKET_OWNER$ }}
		set_variable = {{ name = {PREFIX}_ad_rehire_history_subject value = $TICKET_SUBJECT$ }}
		set_variable = {{ name = {PREFIX}_ad_rehire_history_cycle value = $TICKET_CYCLE$ }}
		set_variable = {{ name = {PREFIX}_ad_rehire_history_case value = $TICKET_CASE$ }}
		set_variable = {{ name = {PREFIX}_ad_rehire_history_state value = 6 }}
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 2761 }} }}
}}

# #277 joins B2's committed one-slot PIP settlement directly with an
# independent native-confirmed exit receipt.  The adapter freezes only the
# native exit half: it never copies, signs or consumes the B2 source.  A/B
# consume both sources atomically after the case-kernel operation receipt;
# route C never enters this adapter or touches either source.
{PREFIX}_submit_m277_closed_pip_exit_effect = {{
	remove_variable = {PREFIX}_adapter_status
	remove_variable = {PREFIX}_adapter_blocked_reason
	if = {{
		limit = {{
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 6
			}}
			$TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_ad_external_pip_exit_ready')}
			has_variable = {PREFIX}_m274_hired
			has_variable = {PREFIX}_m274_position_type_id
			has_variable = {PREFIX}_formal_hc_active
			has_variable = {PREFIX}_formal_hc_active_case
			var:{PREFIX}_m274_hired = 1
			var:{PREFIX}_m274_position_type_id > 0
			var:{PREFIX}_formal_hc_active = 1
			var:{PREFIX}_formal_hc_active_case = $TICKET_CASE$
			has_variable = zg361_b2_workforce_pip_pending
			has_variable = zg361_b2_workforce_pip_consumed
			has_variable = zg361_b2_workforce_pip_owner
			has_variable = zg361_b2_workforce_pip_subject
			has_variable = zg361_b2_workforce_pip_cycle
			has_variable = zg361_b2_workforce_pip_case
			has_variable = zg361_b2_workforce_pip_state
			has_variable = zg361_b2_workforce_pip_case_id
			has_variable = zg361_b2_workforce_pip_case_hash
			has_variable = zg361_b2_workforce_pip_closure_receipt_id
			has_variable = zg361_b2_workforce_pip_closure_receipt_hash
			var:zg361_b2_workforce_pip_pending = 1
			var:zg361_b2_workforce_pip_consumed = 0
			var:zg361_b2_workforce_pip_owner = $TICKET_OWNER$
			var:zg361_b2_workforce_pip_subject = $TICKET_SUBJECT$
			var:zg361_b2_workforce_pip_cycle > 0
			var:zg361_b2_workforce_pip_case > 0
			OR = {{
				var:zg361_b2_workforce_pip_state = 3
				var:zg361_b2_workforce_pip_state = 4
			}}
			var:zg361_b2_workforce_pip_case_id > 0
			var:zg361_b2_workforce_pip_case_hash > 0
			var:zg361_b2_workforce_pip_closure_receipt_id > 0
			var:zg361_b2_workforce_pip_closure_receipt_hash > 0
			NOT = {{ var:zg361_b2_workforce_pip_case_id = var:zg361_b2_workforce_pip_closure_receipt_id }}
			NOT = {{ var:zg361_b2_workforce_pip_case_hash = var:zg361_b2_workforce_pip_closure_receipt_hash }}
			$EXIT_CONFIRMED$ = 1 $EXIT_RECEIPT_ID$ > 0 $EXIT_RECEIPT_HASH$ > 0
			$FORMER_SLOT_ID$ > 0
			$DISPLACED_HOURS$ >= 0 $DISPLACED_COST_RECEIPT$ > 0
			$EXITED_CHARACTER$ = $TICKET_SUBJECT$
			NOT = {{ $EXIT_RECEIPT_ID$ = var:zg361_b2_workforce_pip_case_id }}
			NOT = {{ $EXIT_RECEIPT_ID$ = var:zg361_b2_workforce_pip_closure_receipt_id }}
			NOT = {{ $EXIT_RECEIPT_HASH$ = var:zg361_b2_workforce_pip_case_hash }}
			NOT = {{ $EXIT_RECEIPT_HASH$ = var:zg361_b2_workforce_pip_closure_receipt_hash }}
		}}
		set_variable = {{ name = {PREFIX}_ad_external_pip_exit_ready value = 1 }}
		set_variable = {{ name = {PREFIX}_ad_external_pip_exit_consumed value = 0 }}
		set_variable = {{ name = {PREFIX}_ad_external_exit_receipt_id value = $EXIT_RECEIPT_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_exit_receipt_hash value = $EXIT_RECEIPT_HASH$ }}
		set_variable = {{ name = {PREFIX}_ad_external_exit_former_slot_id value = $FORMER_SLOT_ID$ }}
		set_variable = {{ name = {PREFIX}_ad_external_exit_displaced_hours value = $DISPLACED_HOURS$ }}
		set_variable = {{ name = {PREFIX}_ad_external_exit_displaced_cost_receipt value = $DISPLACED_COST_RECEIPT$ }}
		set_variable = {{ name = {PREFIX}_adapter_status value = 1 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_adapter_status value = 4 }} set_variable = {{ name = {PREFIX}_adapter_blocked_reason value = 2771 }} }}
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


def render_manager_collective_na_finalize() -> str:
    """Close a manager AL case when Central proved three cohorts impossible."""

    return f"""# Public Central structural-N/A seam.  It writes neither #360 nor
# #361 receipt/business object and never creates a sealed collective.
{PREFIX}_finalize_manager_collective_na_effect = {{
	remove_variable = {PREFIX}_runtime_applied
	remove_variable = {PREFIX}_last_red_code
	save_scope_as = {PREFIX}_m360_materialize_subject
	$TICKET_OWNER$ = {{ save_scope_as = {PREFIX}_m360_materialize_owner }}
	if = {{
		limit = {{
			$REASON$ = 360362
			zg361_is_celestial_liege_trigger = yes
			zg361_case_kernel_full_guard_trigger = {{
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}}
			$TICKET_SUBJECT$ = this
			{_zero_or_missing(f'{PREFIX}_al_external_collective_submission_active')}
			$TICKET_OWNER$ = {{
				zg361_is_celestial_liege_trigger = yes
{indent(chr(10).join(_central_m360_owner_checks(7)), 4)}
			}}
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
				OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
				CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
				STATE_VAR = zg361_case_al_state REVISION_VAR = zg361_case_al_revision
				ACTIVE_VAR = zg361_case_al_active TIMELINE_VAR = zg361_case_al_timeline_serial
				FEEDBACK_VAR = zg361_case_al_feedback_revision LAST_HOOK_VAR = zg361_case_al_last_hook
				TICKET_OWNER = $TICKET_OWNER$ TICKET_SUBJECT = $TICKET_SUBJECT$
				TICKET_CYCLE = $TICKET_CYCLE$ TICKET_CASE = $TICKET_CASE$
				TICKET_STATE = 4 NEXT_STATE = 7 HOOK_ID = 9363 CLOSE_CASE = yes
			}}
			if = {{
				limit = {{ has_variable = zg361_case_kernel_applied var:zg361_case_kernel_applied = 1 var:zg361_case_al_active = 0 var:zg361_case_al_state = 7 }}
				set_variable = {{ name = {PREFIX}_final_conservation_ok value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_na value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_reason value = $REASON$ }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_owned_operations value = {NONMANAGER_OPERATION_COUNT} }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_skipped_manager_only value = 2 }}
				set_variable = {{ name = {PREFIX}_portfolio_terminal_success value = 0 }}
				set_variable = {{ name = {PREFIX}_awaiting_al_357_359 value = 0 }}
				set_variable = {{ name = {PREFIX}_m360_event_queued value = 0 }}
				set_variable = {{ name = {PREFIX}_portfolio_closed value = 1 }}
				set_variable = {{ name = {PREFIX}_portfolio_status value = 7 }}
				set_variable = {{ name = {PREFIX}_runtime_applied value = 1 }}
				set_variable = {{ name = {PREFIX}_runtime_status value = 1 }}
				debug_log = "ZG361WE: manager portfolio closed structural N/A without #360/#361"
			}}
			else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 9096 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
		}}
		else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 9096 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
	}}
	else_if = {{
		limit = {{ has_variable = {PREFIX}_portfolio_terminal_na var:{PREFIX}_portfolio_terminal_na = 1 var:{PREFIX}_portfolio_terminal_reason = $REASON$ var:{PREFIX}_portfolio_closed = 1 var:{PREFIX}_portfolio_status = 7 var:zg361_case_al_active = 0 }}
		set_variable = {{ name = {PREFIX}_runtime_status value = 2 }}
	}}
	else = {{ set_variable = {{ name = {PREFIX}_last_red_code value = 9096 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
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
    """Render the historical aggregate in memory as the semantic baseline."""
    validate_specs()
    sections = [
        "# ZhongGuo 361 workforce/endgame: AB/AC/AD plus AL 355/356/360/361.\n"
        f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n"
        f"# Public manager ABI: {PREFIX}_open_portfolio_effect = {{ SUBJECT = <direct vassal> }}.\n"
        "# Stable status: 1=applied, 2=idempotent, 3=stale, 4=typed RED, 5=external dependency, 6=complete, 7=honest N/A terminal, 8=history-accruing terminal.",
        render_portfolio_initialize(),
        render_portfolio_entry(),
        render_al_357_359_receipt_bridge(),
        render_collective_producer(),
        render_completed_cycle_ledger(),
        render_ac_real_fact_producers(),
        render_external_fact_adapters(),
        render_ad_source_integration(),
        render_m274_attribution_pipeline(),
        render_future_consumers_integrated(),
        render_m269_attribution_handoffs(),
        render_due_debt_consumers(),
        render_abandoned_resource_release(),
        render_nonmanager_na_finalize(),
        render_manager_collective_na_finalize(),
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


def _mechanism_effect_names(*mids: int) -> tuple[str, ...]:
    names: list[str] = []
    for mid in mids:
        names.append(f"{PREFIX}_m{mid}_consume_effect")
        names.extend(f"{PREFIX}_m{mid}_route_{letter}_effect" for letter in "abc")
    return tuple(names)


def _due_debt_effect_names(*mids: int) -> tuple[str, ...]:
    return tuple(f"{PREFIX}_m{mid}_consume_due_debt_effect" for mid in mids)


def _deadline_effect_names(domain: str, *states: int) -> tuple[str, ...]:
    names: list[str] = []
    for state in states:
        names.extend((
            f"{PREFIX}_{domain}_schedule_stage_{state:02d}_deadline_effect",
            f"{PREFIX}_{domain}_timeout_stage_{state:02d}_effect",
        ))
    return tuple(names)


EFFECT_GROUPS = (
    EffectGroup(
        "zg361_workforce_endgame_001_portfolio_effects.txt",
        "portfolio initialization and public manager entry",
        ("zg361_we_initialize_portfolio_effect", "zg361_we_open_portfolio_effect"),
    ),
    EffectGroup(
        "zg361_workforce_endgame_002_al_receipt_bridge_effects.txt",
        "B2-owned AL 357-359 receipt submission bridge",
        ("zg361_we_submit_al_357_359_receipts_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_003_m360_central_route_a_materialize_effects.txt",
        "materialize central M360 route A source",
        ("zg361_we_materialize_m360_route_a_from_central_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_004_m360_central_route_b_materialize_effects.txt",
        "materialize central M360 route B source",
        ("zg361_we_materialize_m360_route_b_from_central_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_005_m360_central_source_effects.txt",
        "consume and resume the central M360 source",
        (
            "zg361_we_mark_central_m360_source_consumed_effect",
            "zg361_we_resume_m360_from_central_source_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_006_completed_357_359_history_effects.txt",
        "completed AL 357-359 cycle history ledger",
        ("zg361_we_record_completed_357_359_history_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_007_m361_charter_history_gate_effects.txt",
        "M361 charter evidence and history-accruing gate",
        (
            "zg361_we_prepare_m361_charter_evidence_effect",
            "zg361_we_finalize_history_accruing_effect",
            "zg361_we_after_m360_history_gate_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_008_m264_handoff_effects.txt",
        "AC M264 subject handoff lifecycle",
        (
            "zg361_we_ac_freeze_m262_host_manager_effect",
            "zg361_we_m264_begin_handoff_effect",
            "zg361_we_m264_dispatch_handoff_step_1_effect",
            "zg361_we_m264_dispatch_handoff_step_2_effect",
            "zg361_we_m264_dispatch_handoff_step_3_effect",
            "zg361_we_m264_queue_owner_review_effect",
            "zg361_we_m264_complete_documentation_effect",
            "zg361_we_m264_complete_shadowing_effect",
            "zg361_we_m264_complete_practical_effect",
            "zg361_we_m264_refuse_handoff_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_009a_ad_fact_receipt_pre_rehire_effects.txt",
        "AD fact adapters accepting an already-confirmed appointment receipt and runner reopen fact",
        (
            "zg361_we_submit_ad_appointment_receipt_effect",
            "zg361_we_consume_m275_runner_reopen_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_009b_m276_rehire_history_effects.txt",
        "B2 closure M276 rehire-history receipt",
        ("zg361_we_submit_m276_rehire_history_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_009c_m277_exit_adapter_effects.txt",
        "AD M277 closed-PIP exit adapter",
        ("zg361_we_submit_m277_closed_pip_exit_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_010_ad_source_consume_effects.txt",
        "AD referral panel and offer source consumption",
        (
            "zg361_we_consume_referral_source_after_m271_effect",
            "zg361_we_consume_panel_source_after_m267_effect",
            "zg361_we_consume_offer_source_after_m274_effect",
            "zg361_we_consume_offer_source_after_m275_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_011_ad_source_retire_effects.txt",
        "AD referral panel and offer source debt retirement",
        (
            "zg361_we_retire_referral_source_after_m267_debt_effect",
            "zg361_we_retire_panel_source_after_m267_debt_effect",
            "zg361_we_retire_offer_source_after_m274_debt_effect",
            "zg361_we_retire_offer_source_after_m275_debt_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_012_ad_source_resume_effects.txt",
        "AD source resumption and AI continuations",
        (
            "zg361_we_continue_ai_ad_after_fact_na_effect",
            "zg361_we_continue_ai_ad_after_offer_refusal_effect",
            "zg361_we_resume_m271_from_referral_source_effect",
            "zg361_we_resume_m267_from_panel_source_effect",
            "zg361_we_resume_m274_from_offer_source_effect",
            "zg361_we_queue_m274_appointment_ack_effect",
            "zg361_we_resume_m274_after_native_appointment_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_013_m274_attribution_pipeline_effects.txt",
        "M274 post-consume attribution pipeline",
        (
            "zg361_we_m274_postconsume_fact_handoff_effect",
            "zg361_we_m274_audit_probation_and_arm_attribution_effect",
            "zg361_we_m274_audit_signature_and_dispatch_disposition_effect",
            "zg361_we_m274_audit_disposition_and_launch_m269_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_014a_ac_future_transitions_effects.txt",
        "AC future-cycle transitions",
        (
            "zg361_we_m257_future_consume_effect",
            "zg361_we_m262_secondment_due_effect",
            "zg361_we_m263_extension_due_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_014b_m269_future_consume_effects.txt",
        "B2 closure M269 future consumer",
        ("zg361_we_m269_future_consume_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_014c_m275_hold_due_effects.txt",
        "M275 future hold deadline",
        ("zg361_we_m275_hold_due_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_014d_m355_m356_future_effects.txt",
        "B2 closure M355 target install and M356 cutoff audit",
        (
            "zg361_we_m355_target_install_effect",
            "zg361_we_m356_cutoff_audit_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_014e_m361_future_install_effects.txt",
        "M361 future default install",
        ("zg361_we_m361_future_default_install_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_015a_m269_signed_result_publication_effects.txt",
        "M269 signed attribution-result publication",
        ("zg361_we_m269_publish_signed_result_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_015c_m269_attribution_debt_cancellation_effects.txt",
        "M269 attribution-debt cancellation and stage advance",
        (
            "zg361_we_m269_begin_attribution_debt_cancel_effect",
            "zg361_we_m269_ack_attribution_debt_cancel_effect",
            "zg361_we_m269_audit_attribution_debt_advance_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_015b_m269_postsettlement_handoff_effects.txt",
        "B2 closure M269 post-settlement handoff",
        ("zg361_we_m269_postsettlement_handoff_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_016_m276_rehire_finalize_effects.txt",
        "M276 rehire preparation and finalization",
        (
            "zg361_we_m276_audit_prepared_rehire_effect",
            "zg361_we_queue_m276_rehire_finalize_effect",
            "zg361_we_m276_finalize_rehire_effect",
            "zg361_we_m276_audit_rehire_finalize_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_017_ab_due_debt_stage01_03_effects.txt",
        "AB stage 01-03 due-debt consumers",
        _due_debt_effect_names(242, 243, 244, 245, 246, 247),
    ),
    EffectGroup(
        "zg361_workforce_endgame_018_ab_due_debt_stage04_06_effects.txt",
        "AB stage 04-06 due-debt consumers",
        _due_debt_effect_names(248, 249, 250, 251, 252, 253),
    ),
    EffectGroup(
        "zg361_workforce_endgame_019_ac_due_debt_stage01_03_effects.txt",
        "AC stage 01-03 due-debt consumers",
        _due_debt_effect_names(254, 255, 260, 261, 256, 258, 259),
    ),
    EffectGroup(
        "zg361_workforce_endgame_020_ac_due_debt_stage04_06_effects.txt",
        "AC stage 04-06 due-debt consumers",
        _due_debt_effect_names(257, 262, 263, 264, 265),
    ),
    EffectGroup(
        "zg361_workforce_endgame_021_ad_due_debt_stage01_03_effects.txt",
        "AD stage 01-03 due-debt consumers",
        _due_debt_effect_names(266, 273, 271, 267, 268, 270, 272),
    ),
    EffectGroup(
        "zg361_workforce_endgame_022a_ad_due_debt_stage04_05_effects.txt",
        "AD stage 04-05 due-debt consumers",
        _due_debt_effect_names(274, 275, 269),
    ),
    EffectGroup(
        "zg361_workforce_endgame_022b_ad_due_debt_stage06_effects.txt",
        "B2 closure AD stage 06 due-debt consumers",
        _due_debt_effect_names(276, 277),
    ),
    EffectGroup(
        "zg361_workforce_endgame_023a_al_m355_m356_due_debt_effects.txt",
        "B2 closure AL M355-M356 due-debt consumers",
        _due_debt_effect_names(355, 356),
    ),
    EffectGroup(
        "zg361_workforce_endgame_023b_al_m360_due_debt_effects.txt",
        "AL M360 collective due-debt consumer",
        _due_debt_effect_names(360),
    ),
    EffectGroup(
        "zg361_workforce_endgame_023c_al_m361_due_debt_effects.txt",
        "AL M361 charter due-debt consumer",
        _due_debt_effect_names(361),
    ),
    EffectGroup(
        "zg361_workforce_endgame_024a_abandoned_ac_cleanup_effects.txt",
        "abandoned AC resource release",
        ("zg361_we_release_abandoned_ac_resources_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_024b_ad_nonmanager_terminal_cleanup_effects.txt",
        "B2 closure abandoned AD release and non-manager N/A finalization",
        (
            "zg361_we_release_abandoned_ad_resources_effect",
            "zg361_we_finalize_nonmanager_na_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_024c_manager_collective_cleanup_effects.txt",
        "manager collective N/A finalization and cleanup",
        ("zg361_we_finalize_manager_collective_na_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_024d_portfolio_finalize_effects.txt",
        "cross-domain portfolio finalization",
        ("zg361_we_finalize_portfolio_effect",),
    ),
    EffectGroup(
        "zg361_workforce_endgame_025a_ab_lifecycle_control_effects.txt",
        "AB domain initialization authorized AI and launch lifecycle",
        (
            "zg361_we_ab_initialize_effect",
            "zg361_we_ab_run_authorized_ai_effect",
            "zg361_we_ab_launch_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_025b_ab_subject_read_effects.txt",
        "AB subject-visible revision read",
        ("zg361_we_ab_subject_read_effect",),
    ),
    EffectGroup("zg361_workforce_endgame_026_ab_deadline_stage01_03_effects.txt", "AB stage 01-03 deadlines", _deadline_effect_names("ab", 1, 2, 3)),
    EffectGroup("zg361_workforce_endgame_027_ab_deadline_stage04_06_effects.txt", "AB stage 04-06 deadlines", _deadline_effect_names("ab", 4, 5, 6)),
    EffectGroup(
        "zg361_workforce_endgame_028a_ac_lifecycle_control_effects.txt",
        "AC domain initialization authorized AI and launch lifecycle",
        (
            "zg361_we_ac_initialize_effect",
            "zg361_we_ac_run_authorized_ai_effect",
            "zg361_we_ac_launch_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_028b_ac_subject_read_effects.txt",
        "AC subject-visible revision read",
        ("zg361_we_ac_subject_read_effect",),
    ),
    EffectGroup("zg361_workforce_endgame_029_ac_deadline_stage01_03_effects.txt", "AC stage 01-03 deadlines", _deadline_effect_names("ac", 1, 2, 3)),
    EffectGroup("zg361_workforce_endgame_030_ac_deadline_stage04_06_effects.txt", "AC stage 04-06 deadlines", _deadline_effect_names("ac", 4, 5, 6)),
    EffectGroup(
        "zg361_workforce_endgame_031a_ad_lifecycle_control_effects.txt",
        "AD domain initialization authorized AI and launch lifecycle",
        (
            "zg361_we_ad_initialize_effect",
            "zg361_we_ad_run_authorized_ai_effect",
            "zg361_we_ad_launch_effect",
        ),
    ),
    EffectGroup(
        "zg361_workforce_endgame_031b_ad_subject_read_effects.txt",
        "AD subject-visible revision read",
        ("zg361_we_ad_subject_read_effect",),
    ),
    EffectGroup("zg361_workforce_endgame_032_ad_deadline_stage01_03_effects.txt", "AD stage 01-03 deadlines", _deadline_effect_names("ad", 1, 2, 3)),
    EffectGroup("zg361_workforce_endgame_033a_ad_deadline_stage04_05_effects.txt", "AD stage 04-05 deadlines", _deadline_effect_names("ad", 4, 5)),
    EffectGroup("zg361_workforce_endgame_033b_ad_deadline_stage06_effects.txt", "B2 closure AD stage 06 deadline", _deadline_effect_names("ad", 6)),
    EffectGroup("zg361_workforce_endgame_034a_al_initialize_effects.txt", "B2 closure AL initialization", ("zg361_we_al_initialize_effect",)),
    EffectGroup("zg361_workforce_endgame_034b_al_subject_read_effects.txt", "AL subject read", ("zg361_we_al_subject_read_effect",)),
    EffectGroup(
        "zg361_workforce_endgame_034c_al_ai_launch_effects.txt",
        "B2 closure AL authorized AI and launch controls",
        ("zg361_we_al_run_authorized_ai_effect", "zg361_we_al_launch_effect"),
    ),
    EffectGroup("zg361_workforce_endgame_035a_al_stage01_deadline_effects.txt", "B2 closure AL stage 01 deadline", _deadline_effect_names("al", 1)),
    EffectGroup("zg361_workforce_endgame_035b_al_stage04_m360_deadline_effects.txt", "AL stage 04 M360 collective deadline", _deadline_effect_names("al", 4)),
    EffectGroup("zg361_workforce_endgame_035c_al_stage05_m361_deadline_effects.txt", "AL stage 05 M361 charter deadline", _deadline_effect_names("al", 5)),
    EffectGroup("zg361_workforce_endgame_036_ab_m242_m243_effects.txt", "AB stage 01 mechanisms M242-M243", _mechanism_effect_names(242, 243)),
    EffectGroup("zg361_workforce_endgame_037_ab_m244_m245_effects.txt", "AB stage 02 mechanisms M244-M245", _mechanism_effect_names(244, 245)),
    EffectGroup("zg361_workforce_endgame_038_ab_m246_m247_effects.txt", "AB stage 03 mechanisms M246-M247", _mechanism_effect_names(246, 247)),
    EffectGroup("zg361_workforce_endgame_039_ab_m248_m249_effects.txt", "AB stage 04 mechanisms M248-M249", _mechanism_effect_names(248, 249)),
    EffectGroup("zg361_workforce_endgame_040_ab_m250_m251_effects.txt", "AB stage 05 mechanisms M250-M251", _mechanism_effect_names(250, 251)),
    EffectGroup("zg361_workforce_endgame_041_ab_m252_m253_effects.txt", "AB stage 06 mechanisms M252-M253", _mechanism_effect_names(252, 253)),
    EffectGroup("zg361_workforce_endgame_042_ac_m254_m255_effects.txt", "AC mechanisms M254-M255", _mechanism_effect_names(254, 255)),
    EffectGroup("zg361_workforce_endgame_043_ac_m260_m261_effects.txt", "AC mechanisms M260-M261", _mechanism_effect_names(260, 261)),
    EffectGroup("zg361_workforce_endgame_044_ac_m256_m258_effects.txt", "AC mechanisms M256 and M258", _mechanism_effect_names(256, 258)),
    EffectGroup("zg361_workforce_endgame_045_ac_m259_effects.txt", "AC mechanism M259", _mechanism_effect_names(259)),
    EffectGroup("zg361_workforce_endgame_046a_ac_m257_effects.txt", "AC mechanism M257", _mechanism_effect_names(257)),
    EffectGroup("zg361_workforce_endgame_046b_ac_m262_effects.txt", "AC mechanism M262", _mechanism_effect_names(262)),
    EffectGroup("zg361_workforce_endgame_047_ac_m263_effects.txt", "AC mechanism M263", _mechanism_effect_names(263)),
    EffectGroup("zg361_workforce_endgame_048a_ac_m264_effects.txt", "AC mechanism M264", _mechanism_effect_names(264)),
    EffectGroup("zg361_workforce_endgame_048b_ac_m265_effects.txt", "AC mechanism M265", _mechanism_effect_names(265)),
    EffectGroup("zg361_workforce_endgame_049_ad_m266_m273_effects.txt", "AD mechanisms M266 and M273", _mechanism_effect_names(266, 273)),
    EffectGroup("zg361_workforce_endgame_050a_ad_m271_effects.txt", "AD mechanism M271", _mechanism_effect_names(271)),
    EffectGroup("zg361_workforce_endgame_050b_ad_m267_effects.txt", "AD mechanism M267", _mechanism_effect_names(267)),
    EffectGroup("zg361_workforce_endgame_051_ad_m268_m270_effects.txt", "AD mechanisms M268 and M270", _mechanism_effect_names(268, 270)),
    EffectGroup("zg361_workforce_endgame_052_ad_m272_effects.txt", "AD mechanism M272", _mechanism_effect_names(272)),
    EffectGroup("zg361_workforce_endgame_053a_ad_m274_effects.txt", "AD mechanism M274", _mechanism_effect_names(274)),
    EffectGroup("zg361_workforce_endgame_053b_ad_m275_effects.txt", "AD mechanism M275", _mechanism_effect_names(275)),
    EffectGroup("zg361_workforce_endgame_054_ad_m269_effects.txt", "AD mechanism M269", _mechanism_effect_names(269)),
    EffectGroup("zg361_workforce_endgame_055_ad_m276_m277_effects.txt", "AD mechanisms M276-M277", _mechanism_effect_names(276, 277)),
    EffectGroup("zg361_workforce_endgame_056_al_m355_m356_effects.txt", "AL mechanisms M355-M356", _mechanism_effect_names(355, 356)),
    EffectGroup("zg361_workforce_endgame_057_al_m360_consumer_effects.txt", "AL M360 consumer", ("zg361_we_m360_consume_effect",)),
    EffectGroup("zg361_workforce_endgame_058_al_m360_route_a_effects.txt", "AL M360 route A", ("zg361_we_m360_route_a_effect",)),
    EffectGroup("zg361_workforce_endgame_059_al_m360_route_b_effects.txt", "AL M360 route B", ("zg361_we_m360_route_b_effect",)),
    EffectGroup("zg361_workforce_endgame_060_al_m360_route_c_effects.txt", "AL M360 route C", ("zg361_we_m360_route_c_effect",)),
    EffectGroup(
        "zg361_workforce_endgame_061a_al_m361_consume_route_a_effects.txt",
        "AL M361 consumer and route A",
        ("zg361_we_m361_consume_effect", "zg361_we_m361_route_a_effect"),
    ),
    EffectGroup(
        "zg361_workforce_endgame_061b_al_m361_route_b_c_effects.txt",
        "AL M361 routes B and C",
        ("zg361_we_m361_route_b_effect", "zg361_we_m361_route_c_effect"),
    ),
)

B2_EFFECT_CLOSURE_NAMES = (
    "zg361_we_ad_schedule_stage_06_deadline_effect",
    "zg361_we_ad_timeout_stage_06_effect",
    "zg361_we_al_initialize_effect",
    "zg361_we_al_launch_effect",
    "zg361_we_al_run_authorized_ai_effect",
    "zg361_we_al_schedule_stage_01_deadline_effect",
    "zg361_we_al_timeout_stage_01_effect",
    "zg361_we_finalize_nonmanager_na_effect",
    "zg361_we_m269_future_consume_effect",
    "zg361_we_m269_postsettlement_handoff_effect",
    "zg361_we_m276_audit_prepared_rehire_effect",
    "zg361_we_m276_audit_rehire_finalize_effect",
    "zg361_we_m276_consume_due_debt_effect",
    "zg361_we_m276_consume_effect",
    "zg361_we_m276_finalize_rehire_effect",
    "zg361_we_m276_route_a_effect",
    "zg361_we_m276_route_b_effect",
    "zg361_we_m276_route_c_effect",
    "zg361_we_m277_consume_due_debt_effect",
    "zg361_we_m277_consume_effect",
    "zg361_we_m277_route_a_effect",
    "zg361_we_m277_route_b_effect",
    "zg361_we_m277_route_c_effect",
    "zg361_we_m355_consume_due_debt_effect",
    "zg361_we_m355_consume_effect",
    "zg361_we_m355_route_a_effect",
    "zg361_we_m355_route_b_effect",
    "zg361_we_m355_route_c_effect",
    "zg361_we_m355_target_install_effect",
    "zg361_we_m356_consume_due_debt_effect",
    "zg361_we_m356_consume_effect",
    "zg361_we_m356_cutoff_audit_effect",
    "zg361_we_m356_route_a_effect",
    "zg361_we_m356_route_b_effect",
    "zg361_we_m356_route_c_effect",
    "zg361_we_queue_m276_rehire_finalize_effect",
    "zg361_we_record_completed_357_359_history_effect",
    "zg361_we_release_abandoned_ad_resources_effect",
    "zg361_we_submit_al_357_359_receipts_effect",
    "zg361_we_submit_m276_rehire_history_effect",
)


EVENT_GROUPS = (
    EventGroup(
        "zg361_workforce_endgame_event_001_ab_mechanisms_stage01_03_events.txt",
        "AB stage 01-03 mechanism choices",
        (242, 243, 244, 245, 246, 247),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_002_ab_mechanisms_stage04_06_events.txt",
        "AB stage 04-06 mechanism choices",
        (248, 249, 250, 251, 252, 253),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_003_ac_mechanisms_stage01_03_events.txt",
        "AC stage 01-03 mechanism choices",
        (254, 255, 260, 261, 256, 258, 259),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_004_ac_mechanisms_stage04_06_events.txt",
        "AC stage 04-06 mechanism choices",
        (257, 262, 263, 264, 265),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_005_ad_mechanisms_stage01_03_events.txt",
        "AD stage 01-03 mechanism choices",
        (266, 273, 271, 267, 268, 270, 272),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_006_ad_offer_outcome_events.txt",
        "AD offer appointment refusal and attribution choices",
        (274, 275, 269),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_007_m276_rehire_lifecycle_events.txt",
        "B2 closure M276 rehire lifecycle",
        (276, 5379, 5380, 5381, 6276),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_008_m277_pip_exit_events.txt",
        "B2 closure M277 closed-PIP exit lifecycle",
        (277, 6277),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_009_m355_target_ratchet_events.txt",
        "B2 closure M355 target ratchet lifecycle",
        (355, 5355, 6355),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_010_m356_outcome_timing_events.txt",
        "B2 closure M356 outcome timing lifecycle",
        (356, 5356, 6356),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt",
        "AL M360 collective choice",
        (360,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_011b_al_m361_charter_events.txt",
        "AL M361 charter choice",
        (361,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_012_m264_handoff_events.txt",
        "M264 subject handoff choices and delayed relays",
        (5264, 5265, 5266, 5267, 5268),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_013_ab_deadline_stage01_03_events.txt",
        "AB stage 01-03 deadlines and relays",
        (4201, 4301, 4202, 4302, 4203, 4303),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_014_ab_deadline_stage04_06_events.txt",
        "AB stage 04-06 deadlines and relays",
        (4204, 4304, 4205, 4305, 4206, 4306),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_015_ac_deadline_stage01_03_events.txt",
        "AC stage 01-03 deadlines and relays",
        (4401, 4501, 4402, 4502, 4403, 4503),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_016_ac_deadline_stage04_06_events.txt",
        "AC stage 04-06 deadlines and relays",
        (4404, 4504, 4405, 4505, 4406, 4506),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_017_ad_deadline_stage01_03_events.txt",
        "AD stage 01-03 deadlines and relays",
        (4601, 4701, 4602, 4702, 4603, 4703),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_018_ad_deadline_stage04_05_events.txt",
        "AD stage 04-05 deadlines and relays",
        (4604, 4704, 4605, 4705),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_019_ad_deadline_stage06_events.txt",
        "B2 closure AD stage 06 deadline and relay",
        (4606, 4706),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_020_al_deadline_stage01_events.txt",
        "B2 closure AL stage 01 deadline and relay",
        (4801, 4901),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_021a_al_stage04_m360_deadline_events.txt",
        "AL stage 04 M360 collective deadline and relay",
        (4804, 4904),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_021b_al_stage05_m361_deadline_events.txt",
        "AL stage 05 M361 charter deadline and relay",
        (4805, 4905),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_022_ac_future_transitions_events.txt",
        "AC future-cycle transitions",
        (5257, 5262, 5263),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_023_m269_postsettlement_events.txt",
        "B2 closure M269 post-settlement lifecycle",
        (5269, 5377),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_024_m275_hold_events.txt",
        "M275 future hold deadline",
        (5275,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_025_m361_future_charter_events.txt",
        "M361 future charter installation",
        (5361,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_026_m274_attribution_events.txt",
        "M274 appointment and attribution audit relays",
        (5370, 5371, 5372, 5373),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_027a_m269_attribution_debt_cancellation_events.txt",
        "M269 attribution-debt cancellation and stage-advance relays",
        (5374, 5375, 5376),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_027b_m269_signed_result_publication_events.txt",
        "M269 signed attribution-result publication relay",
        (5378,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_028_m275_remediation_events.txt",
        "M275 remediation commit boundaries",
        (5276, 5277),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_029_ab_debt_stage01_03_events.txt",
        "AB stage 01-03 due-debt callbacks",
        (6242, 6243, 6244, 6245, 6246, 6247),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_030_ab_debt_stage04_06_events.txt",
        "AB stage 04-06 due-debt callbacks",
        (6248, 6249, 6250, 6251, 6252, 6253),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_031_ac_debt_stage01_03_events.txt",
        "AC stage 01-03 due-debt callbacks",
        (6254, 6255, 6256, 6258, 6259, 6260, 6261),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_032_ac_debt_stage04_06_events.txt",
        "AC stage 04-06 due-debt callbacks",
        (6257, 6262, 6263, 6264, 6265),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_033_ad_debt_stage01_03_events.txt",
        "AD stage 01-03 due-debt callbacks",
        (6266, 6267, 6268, 6270, 6271, 6272, 6273),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_034_ad_debt_stage04_05_events.txt",
        "AD stage 04-05 due-debt callbacks",
        (6269, 6274, 6275),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_035a_al_m360_collective_debt_events.txt",
        "AL M360 collective due-debt callback",
        (6360,),
    ),
    EventGroup(
        "zg361_workforce_endgame_event_035b_al_m361_charter_debt_events.txt",
        "AL M361 charter due-debt callback",
        (6361,),
    ),
)

B2_EVENT_CLOSURE_IDS = (
    276, 5379, 5380, 5381, 6276,
    277, 6277,
    355, 5355, 6355,
    356, 5356, 6356,
    5269, 5377,
    4606, 4706,
    4801, 4901,
)


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
    raise ValueError("unterminated quoted string in generated script")


def _skip_comment(text: str, index: int) -> int:
    newline = text.find("\n", index)
    return len(text) if newline < 0 else newline + 1


def _block_end(text: str, open_brace: int) -> int:
    depth = 0
    index = open_brace
    while index < len(text):
        char = text[index]
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("unbalanced generated script block")
        index += 1
    raise ValueError("unterminated generated script block")


def top_level_effect_blocks(payload: bytes | str) -> tuple[tuple[str, str], ...]:
    """Return true top-level assignments using brace depth, never line shape."""
    text = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload.lstrip("\ufeff")
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
        while index < len(text) and (text[index].isalnum() or text[index] in "_."):
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
        blocks.append((name, text[start:end]))
        index = end
    return tuple(blocks)


def _validate_effect_groups(source_blocks: tuple[tuple[str, str], ...]) -> None:
    source_names = tuple(name for name, _ in source_blocks)
    source_rank = {name: rank for rank, name in enumerate(source_names)}
    configured_names = tuple(name for group in EFFECT_GROUPS for name in group.effect_names)
    filenames = tuple(group.filename for group in EFFECT_GROUPS)
    if len(source_names) != HISTORICAL_EFFECT_COUNT:
        raise ValueError(
            f"workforce/endgame source must contain {HISTORICAL_EFFECT_COUNT} top-level effects, "
            f"found {len(source_names)}"
        )
    if len(source_names) != len(set(source_names)):
        raise ValueError("workforce/endgame source contains duplicate top-level effects")
    if len(filenames) != len(set(filenames)):
        raise ValueError("workforce/endgame effect shard filenames must be unique")
    if len(configured_names) != len(set(configured_names)):
        raise ValueError("workforce/endgame effect groups contain duplicate effect names")
    if set(source_names) != set(configured_names):
        missing = sorted(set(source_names) - set(configured_names))
        unexpected = sorted(set(configured_names) - set(source_names))
        raise ValueError(
            "workforce/endgame effect groups must preserve exact source coverage; "
            f"missing={missing}, unexpected={unexpected}"
        )
    for group in EFFECT_GROUPS:
        ranks = tuple(source_rank[name] for name in group.effect_names)
        if ranks != tuple(sorted(ranks)):
            raise ValueError(f"{group.filename} must preserve source order within its purpose shard")
    # Purpose groups may join lifecycle blocks emitted around a separately owned
    # subject-read block. Reordering all blocks by their frozen source rank must
    # still reconstruct the byte-identical 324-block historical aggregate.
    reconstructed_names = tuple(sorted(configured_names, key=source_rank.__getitem__))
    if reconstructed_names != source_names:
        raise ValueError("workforce/endgame effect shards cannot reconstruct global source order")
    b2_closure = set(B2_EFFECT_CLOSURE_NAMES)
    if len(B2_EFFECT_CLOSURE_NAMES) != 40 or len(b2_closure) != 40:
        raise ValueError("B2 workforce closure must contain exactly 40 unique effects")
    selected_b2_groups = [
        group for group in EFFECT_GROUPS if b2_closure.intersection(group.effect_names)
    ]
    mixed_b2_groups = [
        group.filename
        for group in selected_b2_groups
        if not set(group.effect_names).issubset(b2_closure)
    ]
    if mixed_b2_groups:
        raise ValueError(f"B2 workforce closure is mixed with unrelated effects: {mixed_b2_groups}")
    projected_b2_closure = {
        name for group in selected_b2_groups for name in group.effect_names
    }
    if projected_b2_closure != b2_closure:
        raise ValueError(
            "B2 workforce closure shard union must be exact; "
            f"missing={sorted(b2_closure - projected_b2_closure)}, "
            f"extra={sorted(projected_b2_closure - b2_closure)}"
        )
    over_hard = {group.filename for group in EFFECT_GROUPS if len(group.effect_names) > EFFECT_HARD_MAX}
    unknown_exceptions = set(EFFECT_HARD_LIMIT_EXCEPTIONS) - over_hard
    if unknown_exceptions:
        raise ValueError(f"stale workforce/endgame hard-limit exceptions: {sorted(unknown_exceptions)}")
    for filename in sorted(over_hard):
        reason, live_evidence = EFFECT_HARD_LIMIT_EXCEPTIONS.get(filename, ("", ""))
        if not reason.strip() or not live_evidence.strip():
            raise ValueError(
                f"{filename} exceeds {EFFECT_HARD_MAX} effects without a reason and CK3 live-evidence reference"
            )
    for group in EFFECT_GROUPS:
        if not group.effect_names:
            raise ValueError(f"{group.filename} must contain at least one effect")
        if not group.purpose.strip():
            raise ValueError(f"{group.filename} must declare a purpose")


def render_effect_parts() -> dict[str, bytes]:
    source_blocks = top_level_effect_blocks(render_effects())
    _validate_effect_groups(source_blocks)
    by_name = dict(source_blocks)
    parts: dict[str, bytes] = {}
    for group in EFFECT_GROUPS:
        body = "\n\n".join(by_name[name] for name in group.effect_names)
        parts[group.filename] = generated(
            f"# PURPOSE: {group.purpose}.\n"
            f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n\n"
            f"{body}"
        )
    return parts


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
    m360_ready = ""
    if spec.mid == 360:
        owner_checks = [
            *(f"has_variable = zg361_p2c_m360_source_{field}" for field in M360_CENTRAL_GLOBAL_FIELDS),
            "var:zg361_p2c_m360_source_status = 1",
            "var:zg361_p2c_m360_source_reason = 0",
            "var:zg361_p2c_m360_source_owner = this",
            f"var:zg361_p2c_m360_source_subject = scope:{PREFIX}_{d}_subject",
            f"var:zg361_p2c_m360_source_p2c_cycle = scope:{PREFIX}_{d}_cycle",
            f"var:zg361_p2c_m360_source_al_cycle = scope:{PREFIX}_{d}_cycle",
            f"var:zg361_p2c_m360_source_al_case = scope:{PREFIX}_{d}_case",
            "var:zg361_p2c_m360_source_cohort_count = 3",
            "var:zg361_p2c_m360_source_total_quota >= 1",
            f"var:zg361_p2c_m360_source_total_quota <= {MAX_COLLECTIVE_OUTCOMES}",
        ]
        for cohort in (1, 2, 3):
            base = f"zg361_p2c_m360_source_c{cohort}"
            owner_checks.extend(
                f"has_variable = {base}_{field}"
                for field in M360_CENTRAL_COHORT_FIELDS
            )
        owner_checks += [
            f"var:zg361_p2c_m360_source_c1_manager = scope:{PREFIX}_{d}_subject",
            "NOT = { var:zg361_p2c_m360_source_c1_manager = var:zg361_p2c_m360_source_c2_manager }",
            "NOT = { var:zg361_p2c_m360_source_c1_manager = var:zg361_p2c_m360_source_c3_manager }",
            "NOT = { var:zg361_p2c_m360_source_c2_manager = var:zg361_p2c_m360_source_c3_manager }",
        ]
        m360_ready = f"""
scope:{PREFIX}_{d}_owner = {{
{indent(chr(10).join(owner_checks))}
}}
scope:{PREFIX}_{d}_subject = {{
	has_variable = {PREFIX}_m360_event_queued
	var:{PREFIX}_m360_event_queued = 1
	var:{PREFIX}_m360_event_owner = scope:{PREFIX}_{d}_owner
	var:{PREFIX}_m360_event_subject = this
	var:{PREFIX}_m360_event_cycle = scope:{PREFIX}_{d}_cycle
	var:{PREFIX}_m360_event_case = scope:{PREFIX}_{d}_case
	{_zero_or_missing(f'{PREFIX}_al_external_collective_submission_active')}
}}"""
    completed = ""
    if spec.mid == 361:
        completed = f"""
scope:{PREFIX}_{d}_subject = {{
\thas_variable = {PREFIX}_m361_evidence_count
\tvar:{PREFIX}_m361_evidence_count = 3
\thas_variable = {PREFIX}_m361_evidence_ready
\tvar:{PREFIX}_m361_evidence_ready = 1
\thas_variable = {PREFIX}_m361_evidence_consumed
\tvar:{PREFIX}_m361_evidence_consumed = 0
\tvar:{PREFIX}_m361_evidence_owner = scope:{PREFIX}_{d}_owner
\tvar:{PREFIX}_m361_evidence_subject = this
\tvar:{PREFIX}_m361_evidence_cycle = scope:{PREFIX}_{d}_cycle
\tvar:{PREFIX}_m361_evidence_case = scope:{PREFIX}_{d}_case
\thas_variable = {PREFIX}_m361_prepared_report_id
\thas_variable = {PREFIX}_m361_prepared_charter_id
}}"""
    return f"""is_ai = no
exists = scope:{PREFIX}_{d}_owner
exists = scope:{PREFIX}_{d}_subject
exists = scope:{PREFIX}_{d}_cycle
exists = scope:{PREFIX}_{d}_case
this = scope:{PREFIX}_{d}_owner
zg361_is_celestial_liege_trigger = yes{top_gate}{dependency}{m360_ready}{completed}
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
    ticket_state = f"\n\t\t\tTICKET_STATE = {spec.state}" if choice == 3 else ""
    next_mid = event_next_mid(spec)
    next_event = ""
    # #262 opens a due-cycle review; it must not immediately ask #263 in the
    # same cycle.  The hidden due consumer queues that player event later.
    if mid == 274 and next_mid == 275:
        if choice == 1:
            next_event = f"""
	scope:{PREFIX}_{d}_subject = {{
		{PREFIX}_queue_m274_appointment_ack_effect = {{
			TICKET_OWNER = scope:{PREFIX}_{d}_owner
			TICKET_SUBJECT = scope:{PREFIX}_{d}_subject
			TICKET_CYCLE = scope:{PREFIX}_{d}_cycle
			TICKET_CASE = scope:{PREFIX}_{d}_case
		}}
	}}"""
        else:
            next_event = f"""
	if = {{
		limit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }} }}
		trigger_event = {{ id = {NAMESPACE}.275 }}
	}}"""
    elif mid == 275 and next_mid == 269:
        # A refusal has no probation outcome to write back.  Close #269 with
        # its no-hire disposition internally and do not show a contradictory
        # delayed-quality window.  Route C still exposes #269 so debt can
        # cascade honestly when the offer branch itself was deferred.
        next_event = f"""
	if = {{
		limit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 }} }}
		if = {{
			limit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_m275_business_object_created var:{PREFIX}_m275_business_object_created = 1 has_variable = {PREFIX}_m275_object_owner var:{PREFIX}_m275_object_owner = scope:{PREFIX}_{d}_owner has_variable = {PREFIX}_m275_object_subject var:{PREFIX}_m275_object_subject = scope:{PREFIX}_{d}_subject has_variable = {PREFIX}_m275_object_cycle var:{PREFIX}_m275_object_cycle = scope:{PREFIX}_{d}_cycle has_variable = {PREFIX}_m275_object_case var:{PREFIX}_m275_object_case = scope:{PREFIX}_{d}_case has_variable = {PREFIX}_m275_refusal var:{PREFIX}_m275_refusal = 1 }} }}
			scope:{PREFIX}_{d}_subject = {{
				{PREFIX}_m269_route_a_effect = {{
					TICKET_OWNER = scope:{PREFIX}_{d}_owner
					TICKET_SUBJECT = scope:{PREFIX}_{d}_subject
					TICKET_CYCLE = scope:{PREFIX}_{d}_cycle
					TICKET_CASE = scope:{PREFIX}_{d}_case
				}}
			}}
			if = {{
				limit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_{d}_state = 6 }} }}
				trigger_event = {{ id = {NAMESPACE}.276 }}
			}}
		}}
		else = {{ trigger_event = {{ id = {NAMESPACE}.269 }} }}
	}}"""
    elif next_mid is not None and not (
        (mid == 262 and choice in (1, 2))
        or mid == 263
        or (mid in (273, 271, 272) and choice in (1, 2))
    ):
        next_state = by_id()[next_mid].state
        next_event = f"""
\tif = {{
\t\tlimit = {{ scope:{PREFIX}_{d}_subject = {{ has_variable = {PREFIX}_runtime_applied var:{PREFIX}_runtime_applied = 1 var:zg361_case_{d}_state = {next_state} }} }}
\t\ttrigger_event = {{ id = {NAMESPACE}.{next_mid} }}
\t}}"""
    option_trigger = ""
    if mid == 264 and choice in (1, 2):
        option_trigger = f"""
\ttrigger = {{
\t\tscope:{PREFIX}_{d}_subject = {{
\t\t\thas_variable = {PREFIX}_m264_handoff_response
\t\t\tvar:{PREFIX}_m264_handoff_response = {choice}
\t\t}}
\t}}"""
    if mid == 276 and choice in (1, 2):
        return f"""option = {{
\tname = {NAMESPACE}.{mid}.{letter}
\tscope:{PREFIX}_{d}_subject = {{
\t\t{PREFIX}_m{mid}_route_{letter}_effect = {{
\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case
\t\t}}
\t\t{PREFIX}_queue_m276_rehire_finalize_effect = {{
\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case
\t\t\tCHOICE = {choice}
\t\t}}
\t}}
}}"""
    if not (mid == 360 and choice in (1, 2)):
        route_effect = (
            APPOINTMENT_WRAPPER
            if mid == 274 and choice == 1
            else f"{PREFIX}_m{mid}_route_{letter}_effect"
        )
        return f"""option = {{
\tname = {NAMESPACE}.{mid}.{letter}{option_trigger}
\tscope:{PREFIX}_{d}_subject = {{
\t\t{route_effect} = {{
\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case{ticket_state}
\t\t}}
\t}}{next_event}
}}"""
    return f"""option = {{
\tname = {NAMESPACE}.{mid}.{letter}{option_trigger}
\tscope:{PREFIX}_{d}_subject = {{
\t\t{PREFIX}_materialize_m360_route_{letter}_from_central_effect = {{
\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case
\t\t}}
\t\tif = {{
\t\t\tlimit = {{ OR = {{ var:{PREFIX}_adapter_status = 1 var:{PREFIX}_adapter_status = 2 }} }}
\t\t\t{PREFIX}_m360_route_{letter}_effect = {{
\t\t\t\tTICKET_OWNER = scope:{PREFIX}_{d}_owner
\t\t\t\tTICKET_SUBJECT = scope:{PREFIX}_{d}_subject
\t\t\t\tTICKET_CYCLE = scope:{PREFIX}_{d}_cycle
\t\t\t\tTICKET_CASE = scope:{PREFIX}_{d}_case
\t\t\t}}
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_m360_event_queued value = 0 }} set_variable = {{ name = {PREFIX}_runtime_status value = 4 }} }}
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


def render_attribution_integration_events() -> str:
    return f"""{NAMESPACE}.{M274_NATIVE_ACK_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tset_variable = {{ name = {PREFIX}_m274_native_resume_audit_scheduled value = 0 }}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\thas_variable = {PREFIX}_m274_native_resume_pending_owner
\t\t\t\thas_variable = {PREFIX}_m274_native_resume_pending_subject
\t\t\t\thas_variable = {PREFIX}_m274_native_resume_pending_cycle
\t\t\t\thas_variable = {PREFIX}_m274_native_resume_pending_case
\t\t\t\tvar:{PREFIX}_m274_native_resume_pending_subject = this
\t\t\t}}
\t\t\t{PREFIX}_resume_m274_after_native_appointment_effect = {{
\t\t\t\tTICKET_OWNER = var:{PREFIX}_m274_native_resume_pending_owner
\t\t\t\tTICKET_SUBJECT = this
\t\t\t\tTICKET_CYCLE = var:{PREFIX}_m274_native_resume_pending_cycle
\t\t\t\tTICKET_CASE = var:{PREFIX}_m274_native_resume_pending_case
\t\t\t}}
\t\t}}
\t}}
}}

{NAMESPACE}.{M274_PROBATION_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m274_audit_probation_and_arm_attribution_effect = yes }}
}}

{NAMESPACE}.{M274_SIGNATURE_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m274_audit_signature_and_dispatch_disposition_effect = yes }}
}}

{NAMESPACE}.{M274_DISPOSITION_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m274_audit_disposition_and_launch_m269_effect = yes }}
}}

{NAMESPACE}.{M269_DEBT_CANCEL_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m269_begin_attribution_debt_cancel_effect = yes }}
}}

{NAMESPACE}.{M269_DEBT_CANCEL_ACK_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m269_ack_attribution_debt_cancel_effect = yes }}
}}

{NAMESPACE}.{M269_DEBT_ADVANCE_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m269_audit_attribution_debt_advance_effect = yes }}
}}

{NAMESPACE}.{M269_POSTSETTLEMENT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m269_postsettlement_handoff_effect = yes }}
}}

{NAMESPACE}.{M269_RESULT_PUBLISH_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tset_variable = {{ name = {PREFIX}_m269_result_relay_queued value = 0 }}
\t\t{PREFIX}_m269_publish_signed_result_effect = yes
\t}}
}}

{NAMESPACE}.{M276_PREPARE_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m276_audit_prepared_rehire_effect = yes }}
}}

{NAMESPACE}.{M276_FINALIZE_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m276_finalize_rehire_effect = yes }}
}}

{NAMESPACE}.{M276_FINALIZE_AUDIT_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m276_audit_rehire_finalize_effect = yes }}
}}"""


def render_remediation_handoff_events() -> str:
    return f"""# D+1 commit boundaries for the real #275-B remediation fact.
{NAMESPACE}.{REMEDIATION_OPEN_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tzg361_workforce_remediation_fact_open_effect = yes
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tOR = {{
\t\t\t\t\tvar:zg361_workforce_remediation_fact_runtime_status = 1
\t\t\t\t\tvar:zg361_workforce_remediation_fact_runtime_status = 2
\t\t\t\t}}
\t\t\t}}
\t\t\tdebug_log = "ZG361WE: #275 remediation requirement opened from committed route B"
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2752 }} }}
\t}}
}}

{NAMESPACE}.{REMEDIATION_CONSUME_EVENT} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{
\t\tzg361_workforce_remediation_fact_consume_effect = yes
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tOR = {{
\t\t\t\t\tvar:zg361_workforce_remediation_fact_runtime_status = 1
\t\t\t\t\tvar:zg361_workforce_remediation_fact_runtime_status = 2
\t\t\t\t}}
\t\t\t}}
\t\t\tdebug_log = "ZG361WE: #275 remediation receipt consumed after committed HC release"
\t\t}}
\t\telse = {{ set_variable = {{ name = {PREFIX}_future_red_code value = 2753 }} }}
\t}}
}}"""


def render_debt_event(mid: int) -> str:
    return f"""{NAMESPACE}.{DEBT_EVENT[mid]} = {{
	type = character_event
	hidden = yes
	immediate = {{ {PREFIX}_m{mid}_consume_due_debt_effect = yes }}
}}"""


def render_handoff_events() -> str:
    """Three real player choices with two engine-enforced 30-day gaps."""

    step_effect = {
        1: f"{PREFIX}_m264_complete_documentation_effect",
        2: f"{PREFIX}_m264_complete_shadowing_effect",
        3: f"{PREFIX}_m264_complete_practical_effect",
    }
    visible: list[str] = []
    for step in (1, 2, 3):
        visible.append(f"""{NAMESPACE}.{HANDOFF_EVENT[step]} = {{
\ttype = character_event
\ttheme = stewardship
\ttitle = {NAMESPACE}.handoff.{step}.t
\tdesc = {NAMESPACE}.handoff.{step}.desc
\ttrigger = {{
\t\tis_ai = no
\t\texists = scope:{PREFIX}_m264_handoff_subject_scope
\t\texists = scope:{PREFIX}_m264_handoff_owner_scope
\t\tOR = {{
\t\t\tthis = scope:{PREFIX}_m264_handoff_subject_scope
\t\t\tthis = scope:{PREFIX}_m264_handoff_owner_scope
\t\t}}
\t\tscope:{PREFIX}_m264_handoff_subject_scope = {{
\t\t\thas_variable = {PREFIX}_m264_handoff_flow_active
\t\t\tvar:{PREFIX}_m264_handoff_flow_active = 1
\t\t\tvar:{PREFIX}_m264_handoff_flow_consumed = 0
\t\t\tvar:{PREFIX}_m264_handoff_step = {step}
\t\t}}
\t}}
\toption = {{
\t\tname = {NAMESPACE}.handoff.{step}.complete
\t\tscope:{PREFIX}_m264_handoff_subject_scope = {{ {step_effect[step]} = yes }}
\t}}
\toption = {{
\t\tname = {NAMESPACE}.handoff.{step}.refuse
\t\tscope:{PREFIX}_m264_handoff_subject_scope = {{ {PREFIX}_m264_refuse_handoff_effect = {{ EXPECTED_STEP = {step} }} }}
\t}}
}}""")
    relays = [
        f"""{NAMESPACE}.{HANDOFF_RELAY_EVENT[step]} = {{
\ttype = character_event
\thidden = yes
\timmediate = {{ {PREFIX}_m264_dispatch_handoff_step_{step}_effect = yes }}
}}"""
        for step in (2, 3)
    ]
    return "\n\n".join([*visible, *relays])


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
    sections.append(render_handoff_events())
    for domain in ("ab", "ac", "ad", "al"):
        for state in sorted(set(STAGE_LAST[domain].values())):
            sections.append(render_deadline_event(domain, state))
    for mid in FUTURE_EVENT:
        sections.append(render_future_event(mid))
    sections.append(render_attribution_integration_events())
    sections.append(render_remediation_handoff_events())
    for mid in sorted(DEBT_EVENT):
        sections.append(render_debt_event(mid))
    return generated("\n\n".join(sections))


def _validate_event_groups(source_blocks: tuple[tuple[str, str], ...]) -> None:
    source_names = tuple(name for name, _ in source_blocks)
    source_ids = tuple(int(name.removeprefix(f"{NAMESPACE}.")) for name in source_names)
    source_rank = {event_id: rank for rank, event_id in enumerate(source_ids)}
    configured_ids = tuple(event_id for group in EVENT_GROUPS for event_id in group.event_ids)
    filenames = tuple(group.filename for group in EVENT_GROUPS)
    if len(source_ids) != HISTORICAL_EVENT_COUNT:
        raise ValueError(
            f"workforce/endgame source must contain {HISTORICAL_EVENT_COUNT} top-level events, "
            f"found {len(source_ids)}"
        )
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("workforce/endgame source contains duplicate top-level events")
    if len(filenames) != len(set(filenames)):
        raise ValueError("workforce/endgame event shard filenames must be unique")
    if len(configured_ids) != len(set(configured_ids)):
        raise ValueError("workforce/endgame event groups contain duplicate event IDs")
    if set(source_ids) != set(configured_ids):
        missing = sorted(set(source_ids) - set(configured_ids))
        unexpected = sorted(set(configured_ids) - set(source_ids))
        raise ValueError(
            "workforce/endgame event groups must preserve exact source coverage; "
            f"missing={missing}, unexpected={unexpected}"
        )
    for group in EVENT_GROUPS:
        ranks = tuple(source_rank[event_id] for event_id in group.event_ids)
        if ranks != tuple(sorted(ranks)):
            raise ValueError(f"{group.filename} must preserve source order within its purpose shard")
    # Purpose groups deliberately join lifecycle callbacks emitted by different
    # generator sections.  Reconstructing by the frozen source rank proves that
    # the global 149-block order and every block body remain recoverable exactly.
    reconstructed_ids = tuple(sorted(configured_ids, key=source_rank.__getitem__))
    if reconstructed_ids != source_ids:
        raise ValueError("workforce/endgame event shards cannot reconstruct global source order")
    b2_closure = set(B2_EVENT_CLOSURE_IDS)
    if len(B2_EVENT_CLOSURE_IDS) != 19 or len(b2_closure) != 19:
        raise ValueError("B2 workforce closure must contain exactly 19 unique events")
    selected_b2_groups = [
        group for group in EVENT_GROUPS if b2_closure.intersection(group.event_ids)
    ]
    mixed_b2_groups = [
        group.filename
        for group in selected_b2_groups
        if not set(group.event_ids).issubset(b2_closure)
    ]
    if len(selected_b2_groups) != 7:
        raise ValueError(
            f"B2 workforce closure must be exactly seven whole event shards, found {len(selected_b2_groups)}"
        )
    if mixed_b2_groups:
        raise ValueError(f"B2 workforce closure is mixed with unrelated events: {mixed_b2_groups}")
    projected_b2_closure = {
        event_id for group in selected_b2_groups for event_id in group.event_ids
    }
    if projected_b2_closure != b2_closure:
        raise ValueError(
            "B2 workforce closure event-shard union must be exact; "
            f"missing={sorted(b2_closure - projected_b2_closure)}, "
            f"extra={sorted(projected_b2_closure - b2_closure)}"
        )
    over_hard = {group.filename for group in EVENT_GROUPS if len(group.event_ids) > EVENT_HARD_MAX}
    unknown_exceptions = set(EVENT_HARD_LIMIT_EXCEPTIONS) - over_hard
    if unknown_exceptions:
        raise ValueError(f"stale workforce/endgame event hard-limit exceptions: {sorted(unknown_exceptions)}")
    for filename in sorted(over_hard):
        reason, live_evidence = EVENT_HARD_LIMIT_EXCEPTIONS.get(filename, ("", ""))
        if not reason.strip() or not live_evidence.strip():
            raise ValueError(
                f"{filename} exceeds {EVENT_HARD_MAX} events without a reason and CK3 live-evidence reference"
            )
    for group in EVENT_GROUPS:
        if not group.event_ids:
            raise ValueError(f"{group.filename} must contain at least one event")
        if not group.purpose.strip():
            raise ValueError(f"{group.filename} must declare a purpose")


def render_event_parts() -> dict[str, bytes]:
    source_blocks = top_level_effect_blocks(render_events())
    _validate_event_groups(source_blocks)
    by_id = {
        int(name.removeprefix(f"{NAMESPACE}.")): block
        for name, block in source_blocks
    }
    parts: dict[str, bytes] = {}
    for group in EVENT_GROUPS:
        body = "\n\n".join(by_id[event_id] for event_id in group.event_ids)
        parts[group.filename] = generated(
            f"# PURPOSE: {group.purpose}.\n"
            f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n\n"
            f"namespace = {NAMESPACE}\n\n"
            f"{body}"
        )
    return parts


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    validate_specs()
    chinese = language == "simp_chinese"
    rows: list[str] = []
    # Localization remains stable by public ID even when executable semantic
    # dependencies require a non-numeric event order.
    for spec in sorted(MECHANISMS, key=lambda item: item.mid):
        title = spec.title_cn if chinese else spec.title_en
        desc = spec.desc_cn if chinese else spec.desc_en
        routes = spec.routes_cn if chinese else spec.routes_en
        rows += [
            f' {NAMESPACE}.{spec.mid}.t:0 "{esc(title)}"',
            f' {NAMESPACE}.{spec.mid}.desc:0 "{esc(desc)}"',
            *(f' {NAMESPACE}.{spec.mid}.{letter}:0 "{esc(text)}"' for letter, text in zip("abc", routes)),
        ]
    handoff_cn = {
        1: (
            "交接第一关：文档不是空气",
            "交接进入文档签收。只有现在明确提交，系统才会生成绑定本案执行链的真实回执；一句“都在群里”不算知识库。",
            "提交可核验文档，生成签收回执",
            "文档？让下个人自己悟",
        ),
        2: (
            "交接第二关：跟岗不是群里 @ 一下",
            "三十日已经过去。要么完成一轮真实跟岗并留下回执，要么承认这场所谓交接只是把人拉进了群。",
            "完成跟岗，留下第二张回执",
            "拉群已经很给面子了",
        ),
        3: (
            "交接第三关：PPT 不能替系统跑",
            "又过三十日，轮到实操验收。只有把既有交付与现场操作对上，尾款才有资格进入审批。",
            "完成实操验收，提交尾款审批",
            "演示到此为止，拒绝实操",
        ),
    }
    handoff_en = {
        1: (
            "Handoff I: Documentation Is Not Air",
            "The documentation checkpoint is due. Only an explicit submission creates a receipt bound to this case's executor chain; saying 'it is in chat' does not count.",
            "Submit verifiable documentation",
            "Let the next person figure it out",
        ),
        2: (
            "Handoff II: Shadowing Is More Than an @ Mention",
            "Thirty days have passed. Complete real shadowing and leave a receipt, or admit that the handoff was only an invitation to a group chat.",
            "Complete shadowing",
            "The group invitation was enough",
        ),
        3: (
            "Handoff III: Slides Do Not Run the System",
            "Another thirty days have passed. Practical acceptance must match the existing delivery record before final payment can be reviewed.",
            "Complete practical acceptance",
            "End the demo and refuse practice",
        ),
    }
    for step in (1, 2, 3):
        title, desc, complete, refuse = (handoff_cn if chinese else handoff_en)[step]
        rows += [
            f' {NAMESPACE}.handoff.{step}.t:0 "{esc(title)}"',
            f' {NAMESPACE}.handoff.{step}.desc:0 "{esc(desc)}"',
            f' {NAMESPACE}.handoff.{step}.complete:0 "{esc(complete)}"',
            f' {NAMESPACE}.handoff.{step}.refuse:0 "{esc(refuse)}"',
        ]
    return localized(f"l_{language}:\n" + "\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_specs()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / filename: payload
        for filename, payload in render_effect_parts().items()
    }
    rendered.update({
        MOD_ROOT / "events" / filename: payload
        for filename, payload in render_event_parts().items()
    })
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_workforce_endgame_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def unexpected_effect_paths(rendered: dict[Path, bytes]) -> tuple[Path, ...]:
    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    expected = {
        path
        for path in rendered
        if path.parent == effects_dir and path.name != LEGACY_EFFECT_FILENAME
    }
    unexpected = set(effects_dir.glob(EFFECT_SHARD_GLOB)) - expected
    # Keep retired purpose-boundary owners as an explicit --check failure even
    # if a future shard glob is narrowed and would otherwise stop seeing them.
    unexpected.update(path for path in RETIRED_EFFECT_PATHS if path.is_file())
    return tuple(sorted(unexpected))


def unexpected_event_paths(rendered: dict[Path, bytes]) -> tuple[Path, ...]:
    events_dir = MOD_ROOT / "events"
    expected = {path for path in rendered if path.parent == events_dir}
    unexpected = set(events_dir.glob(EVENT_SHARD_GLOB)) - expected
    if LEGACY_EVENT_PATH.is_file():
        unexpected.add(LEGACY_EVENT_PATH)
    unexpected.update(path for path in RETIRED_EVENT_PATHS if path.is_file())
    return tuple(sorted(unexpected))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    unexpected_effects = unexpected_effect_paths(rendered)
    unexpected_events = unexpected_event_paths(rendered)
    if args.check:
        if stale or unexpected_effects or unexpected_events:
            print("RED: stale workforce/endgame generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            for path in unexpected_effects:
                print(f"unexpected effect shard: {path.relative_to(MOD_ROOT)}")
            for path in unexpected_events:
                print(f"unexpected event shard: {path.relative_to(MOD_ROOT)}")
            return 1
        print(f"GREEN: {len(rendered)} workforce/endgame generated files are current ({READINESS})")
        return 0
    for path in (*unexpected_effects, *unexpected_events):
        path.unlink()
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} workforce/endgame runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
