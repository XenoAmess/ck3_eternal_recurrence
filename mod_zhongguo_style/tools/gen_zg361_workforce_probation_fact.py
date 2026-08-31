#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #269 probation/PIP fact producer.

The package does not invent a hire outcome.  A real #274 hire arms one
subject-owned slot.  A later, settled result may publish a pass, while a 3.25
result can only freeze the evidence and wait for B2's unique D+365 PIP
settlement.  The twelve legacy Workforce aliases exist only while the strict
#269 consumer is being called; the canonical source and consumption receipt
remain under this package's prefix.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
PREFIX = "zg361_workforce_probation_fact"
WORKFORCE_PREFIX = "zg361_we"
READINESS = "ck3-script-static-ready-not-live"
HEADER = f"# GENERATED FILE — edit tools/gen_{PREFIX}.py\n"

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

LEGACY_ALIAS_TO_FACT = {
    "attribution_bps_2": "attribution_bps_2",
    "attribution_bps_3": "attribution_bps_3",
    "outcome_dimension_1": "outcome_dimension_1",
    "outcome_dimension_2": "outcome_dimension_2",
    "outcome_dimension_3": "outcome_dimension_3",
    "outcome_evidence_count": "outcome_evidence_count",
    "outcome_evidence_hash": "outcome_evidence_hash",
    "outcome_evidence_id": "outcome_evidence_id",
    "outcome_exclusion_reason": "outcome_exclusion_reason",
    "outcome_id": "outcome_id",
    "outcome_observed_cycle": "outcome_observed_cycle",
    "outcome_quality": "outcome_quality",
}


def clean(text: str) -> str:
    """Normalize indentation while keeping generated CK3 source stable."""

    return "\n".join(line.rstrip() for line in textwrap.dedent(text).strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def validate_contract() -> None:
    expected = {
        "attribution_bps_2",
        "attribution_bps_3",
        "outcome_dimension_1",
        "outcome_dimension_2",
        "outcome_dimension_3",
        "outcome_evidence_count",
        "outcome_evidence_hash",
        "outcome_evidence_id",
        "outcome_exclusion_reason",
        "outcome_id",
        "outcome_observed_cycle",
        "outcome_quality",
    }
    if set(LEGACY_ALIAS_TO_FACT) != expected:
        raise ValueError("probation producer must own exactly the 12 frozen aliases")
    if len(LEGACY_ALIAS_TO_FACT) != 12:
        raise ValueError("probation alias count drifted")
    if tuple(LANGUAGES[:2]) != ("english", "simp_chinese") or len(LANGUAGES) != 9:
        raise ValueError("daily localization contract must keep zh/en plus seven placeholders")
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("static package must not claim live readiness")


def _alias_fragments() -> dict[str, str]:
    set_lines = []
    clear_lines = []
    missing_lines = []
    exact_lines = []
    for alias, fact in LEGACY_ALIAS_TO_FACT.items():
        legacy = f"{WORKFORCE_PREFIX}_ad_external_{alias}"
        canonical = f"{PREFIX}_{fact}"
        set_lines.append(f"set_variable = {{ name = {legacy} value = var:{canonical} }}")
        clear_lines.append(f"remove_variable = {legacy}")
        missing_lines.append(f"has_variable = {legacy}")
        exact_lines.extend(
            (
                f"has_variable = {legacy}",
                f"var:{legacy} = var:{canonical}",
            )
        )
    return {
        "ALIAS_SET": "\n".join(" " * 8 + line for line in set_lines),
        "ALIAS_CLEAR": "\n".join(" " * 8 + line for line in clear_lines),
        "ALIAS_MISSING": "\n".join(" " * 20 + line for line in missing_lines),
        "ALIAS_EXACT": "\n".join(" " * 16 + line for line in exact_lines),
    }


def render_effects() -> bytes:
    fragments = _alias_fragments()
    template = r'''
    # ZhongGuo 361 Workforce probation/PIP outcome fact producer for #269.
    # Scope ABI for all three public hooks:
    #   current scope (this) = the real hired subject; $OWNER$ = the real #274 owner.
    #   ROOT is deliberately ignored and conveys no authority or identity.
    # Result hook additionally requires actual attribution bps from the caller;
    # the three dimensions are copied from #267's sealed vote-evidence receipts.

    @P@_arm_hire_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_arm_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_arm_owner_scope }
        if = {
            limit = {
                scope:@P@_arm_subject_scope = { is_alive = yes }
                scope:@P@_arm_owner_scope = {
                    is_alive = yes
                    is_landed = yes
                    zg361_is_celestial_liege_trigger = yes
                }
                has_variable = @W@_m274_write_owner
                has_variable = @W@_m274_write_subject
                has_variable = @W@_m274_write_cycle
                has_variable = @W@_m274_write_case
                has_variable = @W@_m274_write_state
                has_variable = @W@_m274_hired
                has_variable = @W@_m274_hire_case
                has_variable = @W@_m274_probation_due_cycle
                has_variable = @W@_m274_native_appointment_confirmed
                has_variable = @W@_m274_position_receipt_id
                has_variable = @W@_m274_position_receipt_hash
                var:@W@_m274_write_owner = scope:@P@_arm_owner_scope
                var:@W@_m274_write_subject = this
                var:@W@_m274_write_state = 4
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@W@_m274_write_case
                var:@W@_m274_probation_due_cycle > var:@W@_m274_write_cycle
                var:@W@_m274_native_appointment_confirmed = 1
                var:@W@_m274_position_receipt_id > 0
                var:@W@_m274_position_receipt_hash > 0
                OR = {
                    NOT = { has_variable = @P@_state }
                    var:@P@_state = 0
                }
            }
            set_variable = { name = @P@_owner value = scope:@P@_arm_owner_scope }
            set_variable = { name = @P@_subject value = this }
            set_variable = { name = @P@_hire_cycle value = var:@W@_m274_write_cycle }
            set_variable = { name = @P@_hire_case value = var:@W@_m274_write_case }
            set_variable = { name = @P@_probation_due_cycle value = var:@W@_m274_probation_due_cycle }
            set_variable = { name = @P@_position_receipt_id value = var:@W@_m274_position_receipt_id }
            set_variable = { name = @P@_position_receipt_hash value = var:@W@_m274_position_receipt_hash }
            set_variable = {
                name = @P@_arm_receipt_id
                value = { value = var:@W@_m274_write_case multiply = 1000 add = 274 }
            }
            set_variable = {
                name = @P@_arm_receipt_hash
                value = {
                    value = var:@W@_m274_position_receipt_hash
                    add = { value = var:@W@_m274_write_cycle multiply = 1000 }
                    add = var:@W@_m274_write_case
                    add = 274
                }
            }
            set_variable = { name = @P@_state value = 1 } # armed, no outcome yet
            set_variable = { name = @P@_adapter_status value = 1 }
            debug_log = "ZG361WPF: real m274 hire armed; no outcome has been inferred"
        }
        else_if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_probation_due_cycle
                has_variable = @P@_position_receipt_id
                has_variable = @P@_position_receipt_hash
                var:@P@_state >= 1
                var:@P@_owner = scope:@P@_arm_owner_scope
                var:@P@_subject = this
                var:@P@_hire_cycle = var:@W@_m274_write_cycle
                var:@P@_hire_case = var:@W@_m274_write_case
                var:@P@_probation_due_cycle = var:@W@_m274_probation_due_cycle
                var:@P@_position_receipt_id = var:@W@_m274_position_receipt_id
                var:@P@_position_receipt_hash = var:@W@_m274_position_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 } # exact arm replay
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 1001 }
            debug_log = "ZG361WPF RED 1001: arm lacks a real m274 hire or collides with another fact"
        }
    }

    # Pending hook 1.  Call immediately after the canonical result settlement
    # while current scope is the subject.  Idempotency key:
    # owner/subject + hire cycle/case + result cycle/case/state/settlement +
    # grade/reason/KPI/rank + three #267 evidence IDs + attribution bps.
    @P@_publish_from_result_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_result_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_result_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_attribution_bps_1
            value = {
                value = 10000
                subtract = $ATTRIBUTION_BPS_2$
                subtract = $ATTRIBUTION_BPS_3$
            }
        }
        if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_source_result_owner
                has_variable = @P@_source_result_subject
                has_variable = @P@_source_result_cycle
                has_variable = @P@_source_result_case
                has_variable = @P@_source_result_state
                has_variable = @P@_source_result_settlement_receipt
                has_variable = @P@_source_result_grade
                has_variable = @P@_source_result_reason
                has_variable = @P@_source_result_kpi
                has_variable = @P@_source_result_rank
                has_variable = @P@_outcome_dimension_1
                has_variable = @P@_outcome_dimension_2
                has_variable = @P@_outcome_dimension_3
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                var:@P@_state >= 2
                var:@P@_owner = scope:@P@_result_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_owner = scope:@P@_result_owner_scope
                var:@P@_source_result_subject = this
                var:@P@_source_result_cycle = var:zg361_result_cycle_serial
                var:@P@_source_result_case = var:zg361_result_case_serial
                var:@P@_source_result_state = var:zg361_result_case_state
                var:@P@_source_result_settlement_receipt = var:zg361_result_settlement_posted_serial
                var:@P@_source_result_grade = var:zg361_result_grade
                var:@P@_source_result_reason = var:zg361_result_grade_reason
                var:@P@_source_result_kpi = var:zg361_result_kpi_frozen
                var:@P@_source_result_rank = var:zg361_result_rank_frozen
                var:@P@_outcome_dimension_1 = var:@W@_m267_vote_evidence_1
                var:@P@_outcome_dimension_2 = var:@W@_m267_vote_evidence_2
                var:@P@_outcome_dimension_3 = var:@W@_m267_vote_evidence_3
                var:@P@_attribution_bps_2 = $ATTRIBUTION_BPS_2$
                var:@P@_attribution_bps_3 = $ATTRIBUTION_BPS_3$
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = {
                limit = { var:@P@_state = 3 }
                @P@_schedule_consume_effect = yes
            }
            else_if = {
                limit = { var:@P@_state = 4 }
                set_variable = { name = @P@_adapter_status value = 4 }
            }
        }
        else_if = {
            limit = {
                var:@P@_state = 1
                var:@P@_owner = scope:@P@_result_owner_scope
                var:@P@_subject = this
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_probation_due_cycle
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                var:zg361_result_case_owner = scope:@P@_result_owner_scope
                var:zg361_result_cycle_serial >= var:@P@_probation_due_cycle
                var:zg361_result_cycle_serial > var:@P@_hire_cycle
                OR = {
                    var:zg361_result_case_state = 3
                    var:zg361_result_case_state = 5
                }
                var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
                var:zg361_result_case_serial > 0
                OR = {
                    var:zg361_result_grade = 1
                    var:zg361_result_grade = 2
                    var:zg361_result_grade = 3
                }
                scope:@P@_result_owner_scope = {
                    has_variable = zg361_review_serial
                    var:zg361_review_serial >= scope:@P@_result_subject_scope.var:zg361_result_cycle_serial
                }
                has_variable = @W@_m269_outcome_pending
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_write_owner = scope:@P@_result_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_m274_hire_case = var:@P@_hire_case
                var:@W@_m267_candidate_frozen = this
                var:@W@_m267_raw_votes_frozen = 1
                has_variable = @W@_m267_interviewer_1
                has_variable = @W@_m267_interviewer_2
                has_variable = @W@_m267_interviewer_3
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_2 }
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_3 }
                NOT = { var:@W@_m267_interviewer_2 = var:@W@_m267_interviewer_3 }
                has_variable = @W@_m267_vote_evidence_1
                has_variable = @W@_m267_vote_evidence_2
                has_variable = @W@_m267_vote_evidence_3
                var:@W@_m267_vote_evidence_1 > 0
                var:@W@_m267_vote_evidence_2 > 0
                var:@W@_m267_vote_evidence_3 > 0
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_2 }
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_3 }
                NOT = { var:@W@_m267_vote_evidence_2 = var:@W@_m267_vote_evidence_3 }
                $ATTRIBUTION_BPS_2$ >= 0
                $ATTRIBUTION_BPS_3$ >= 0
                scope:@P@_expected_attribution_bps_1 >= 0
            }
            set_variable = { name = @P@_source_result_owner value = scope:@P@_result_owner_scope }
            set_variable = { name = @P@_source_result_subject value = this }
            set_variable = { name = @P@_source_result_cycle value = var:zg361_result_cycle_serial }
            set_variable = { name = @P@_source_result_case value = var:zg361_result_case_serial }
            set_variable = { name = @P@_source_result_state value = var:zg361_result_case_state }
            set_variable = { name = @P@_source_result_settlement_receipt value = var:zg361_result_settlement_posted_serial }
            set_variable = { name = @P@_source_result_grade value = var:zg361_result_grade }
            set_variable = { name = @P@_source_result_reason value = var:zg361_result_grade_reason }
            set_variable = { name = @P@_source_result_kpi value = var:zg361_result_kpi_frozen }
            set_variable = { name = @P@_source_result_rank value = var:zg361_result_rank_frozen }
            set_variable = { name = @P@_outcome_dimension_1 value = var:@W@_m267_vote_evidence_1 }
            set_variable = { name = @P@_outcome_dimension_2 value = var:@W@_m267_vote_evidence_2 }
            set_variable = { name = @P@_outcome_dimension_3 value = var:@W@_m267_vote_evidence_3 }
            set_variable = { name = @P@_attribution_bps_2 value = $ATTRIBUTION_BPS_2$ }
            set_variable = { name = @P@_attribution_bps_3 value = $ATTRIBUTION_BPS_3$ }
            set_variable = { name = @P@_attribution_bps_1 value = scope:@P@_expected_attribution_bps_1 }
            set_variable = {
                name = @P@_attribution_receipt_id
                value = { value = var:zg361_result_case_serial multiply = 1000 add = 269 }
            }
            set_variable = {
                name = @P@_attribution_receipt_hash
                value = {
                    value = var:@W@_m267_vote_evidence_1 multiply = 100000
                    add = { value = var:@W@_m267_vote_evidence_2 multiply = 1000 }
                    add = var:@W@_m267_vote_evidence_3
                    add = { value = $ATTRIBUTION_BPS_2$ multiply = 10 }
                    add = $ATTRIBUTION_BPS_3$
                }
            }
            if = {
                limit = { var:zg361_result_grade = 1 }
                set_variable = { name = @P@_awaiting_pip value = 1 }
                set_variable = { name = @P@_state value = 2 }
                set_variable = { name = @P@_adapter_status value = 3 }
                debug_log = "ZG361WPF: settled 3.25 frozen; real B2 PIP settlement is still required"
            }
            else = {
                set_variable = { name = @P@_source_kind value = 1 } # ordinary settled result
                set_variable = { name = @P@_outcome_quality value = 1 } # pass derived from grade 2/3
                set_variable = { name = @P@_outcome_evidence_count value = 1 }
                set_variable = { name = @P@_outcome_evidence_id value = var:zg361_result_settlement_posted_serial }
                set_variable = {
                    name = @P@_outcome_evidence_hash
                    value = {
                        value = var:zg361_result_case_serial multiply = 1000000
                        add = { value = var:zg361_result_cycle_serial multiply = 10000 }
                        add = { value = var:zg361_result_grade multiply = 1000 }
                        add = { value = var:zg361_result_grade_reason multiply = 10 }
                        add = 269
                    }
                }
                set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_result_cycle_serial }
                set_variable = { name = @P@_outcome_exclusion_reason value = 0 } # typed not-excluded conclusion
                @P@_publish_canonical_effect = yes
            }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 2001 }
            debug_log = "ZG361WPF RED 2001: result hook lacks exact hire/result/attribution provenance"
        }
    }

    # Pending hook 2.  Call immediately after B2 publishes its unique Workforce
    # PIP settlement, current scope still the subject.  Idempotency key:
    # frozen result key + B2 PIP five-tuple/route/task + settlement/outcome/result
    # tuple + exactly derived B2 case and closure receipt IDs/hashes.
    @P@_publish_from_pip_settlement_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_pip_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_pip_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_case_receipt_id
            value = {
                value = var:zg361_b2_pip_case
                multiply = 1000
                add = 15
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_case_receipt_hash
            value = {
                value = var:zg361_b2_pip_case
                multiply = 100000
                add = { value = var:zg361_b2_pip_cycle multiply = 1000 }
                add = { value = var:zg361_b2_pip_policy_route multiply = 100 }
                add = { value = var:zg361_b2_pip_task_kind multiply = 10 }
                add = var:zg361_b2_pip_state
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_closure_receipt_id
            value = {
                value = var:zg361_b2_pip_settlement_receipt
                multiply = 1000
                add = 17
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_closure_receipt_hash
            value = {
                value = scope:@P@_expected_pip_case_receipt_hash
                add = { value = var:zg361_b2_pip_outcome_result_case multiply = 100000 }
                add = { value = var:zg361_b2_pip_outcome_result_cycle multiply = 1000 }
                add = { value = var:zg361_b2_pip_outcome_code multiply = 100 }
                add = { value = var:zg361_b2_pip_state multiply = 10 }
                add = 17
            }
        }
        if = {
            limit = {
                var:@P@_state >= 3
                var:@P@_source_kind = 2
                var:@P@_owner = scope:@P@_pip_owner_scope
                var:@P@_subject = this
                var:@P@_source_pip_owner = scope:@P@_pip_owner_scope
                var:@P@_source_pip_subject = this
                var:@P@_source_pip_cycle = var:zg361_b2_pip_cycle
                var:@P@_source_pip_case = var:zg361_b2_pip_case
                var:@P@_source_pip_state = var:zg361_b2_pip_state
                var:@P@_source_pip_policy_route = var:zg361_b2_pip_policy_route
                var:@P@_source_pip_task_kind = var:zg361_b2_pip_task_kind
                var:@P@_source_pip_settlement_receipt = var:zg361_b2_pip_settlement_receipt
                var:@P@_source_pip_outcome_code = var:zg361_b2_pip_outcome_code
                var:@P@_source_pip_result_cycle = var:zg361_b2_pip_outcome_result_cycle
                var:@P@_source_pip_result_case = var:zg361_b2_pip_outcome_result_case
                var:@P@_source_pip_result_grade = var:zg361_b2_pip_outcome_result_grade
                var:@P@_source_pip_case_receipt_id = var:zg361_b2_workforce_pip_case_id
                var:@P@_source_pip_case_receipt_hash = var:zg361_b2_workforce_pip_case_hash
                var:@P@_source_pip_closure_receipt_id = var:zg361_b2_workforce_pip_closure_receipt_id
                var:@P@_source_pip_closure_receipt_hash = var:zg361_b2_workforce_pip_closure_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = {
                limit = { var:@P@_state = 3 }
                @P@_schedule_consume_effect = yes
            }
            else = { set_variable = { name = @P@_adapter_status value = 4 } }
        }
        else_if = {
            limit = {
                var:@P@_state = 2
                var:@P@_awaiting_pip = 1
                var:@P@_owner = scope:@P@_pip_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_grade = 1
                var:@P@_source_result_owner = scope:@P@_pip_owner_scope
                var:@P@_source_result_subject = this
                has_variable = zg361_b2_pip_owner
                has_variable = zg361_b2_pip_subject
                has_variable = zg361_b2_pip_cycle
                has_variable = zg361_b2_pip_case
                has_variable = zg361_b2_pip_state
                has_variable = zg361_b2_pip_policy_route
                has_variable = zg361_b2_pip_task_kind
                has_variable = zg361_b2_pip_settlement_receipt
                has_variable = zg361_b2_pip_outcome_code
                has_variable = zg361_b2_pip_outcome_result_cycle
                has_variable = zg361_b2_pip_outcome_result_case
                has_variable = zg361_b2_pip_outcome_result_grade
                var:zg361_b2_pip_owner = scope:@P@_pip_owner_scope
                var:zg361_b2_pip_subject = this
                var:zg361_b2_pip_cycle = var:@P@_source_result_cycle
                var:zg361_b2_pip_case > 0
                OR = {
                    var:zg361_b2_pip_policy_route = 1
                    var:zg361_b2_pip_policy_route = 2
                }
                var:zg361_b2_pip_task_kind > 0
                var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
                var:zg361_b2_pip_outcome_result_cycle > var:zg361_b2_pip_cycle
                var:zg361_b2_pip_outcome_result_cycle >= var:@P@_probation_due_cycle
                var:zg361_b2_pip_outcome_result_case > 0
                OR = {
                    AND = {
                        var:zg361_b2_pip_state = 3
                        var:zg361_b2_pip_outcome_code = 1
                        var:zg361_b2_pip_outcome_result_grade >= 2
                        var:zg361_b2_pip_outcome_result_grade <= 3
                    }
                    AND = {
                        var:zg361_b2_pip_state = 4
                        var:zg361_b2_pip_outcome_code = 2
                        var:zg361_b2_pip_outcome_result_grade = 1
                    }
                }
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
                var:zg361_b2_workforce_pip_owner = scope:@P@_pip_owner_scope
                var:zg361_b2_workforce_pip_subject = this
                var:zg361_b2_workforce_pip_cycle = var:zg361_b2_pip_cycle
                var:zg361_b2_workforce_pip_case = var:zg361_b2_pip_case
                var:zg361_b2_workforce_pip_state = var:zg361_b2_pip_state
                var:zg361_b2_workforce_pip_case_id = scope:@P@_expected_pip_case_receipt_id
                var:zg361_b2_workforce_pip_case_hash = scope:@P@_expected_pip_case_receipt_hash
                var:zg361_b2_workforce_pip_closure_receipt_id = scope:@P@_expected_pip_closure_receipt_id
                var:zg361_b2_workforce_pip_closure_receipt_hash = scope:@P@_expected_pip_closure_receipt_hash
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_write_owner = scope:@P@_pip_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
            }
            set_variable = { name = @P@_source_kind value = 2 }
            set_variable = { name = @P@_source_pip_owner value = scope:@P@_pip_owner_scope }
            set_variable = { name = @P@_source_pip_subject value = this }
            set_variable = { name = @P@_source_pip_cycle value = var:zg361_b2_pip_cycle }
            set_variable = { name = @P@_source_pip_case value = var:zg361_b2_pip_case }
            set_variable = { name = @P@_source_pip_state value = var:zg361_b2_pip_state }
            set_variable = { name = @P@_source_pip_policy_route value = var:zg361_b2_pip_policy_route }
            set_variable = { name = @P@_source_pip_task_kind value = var:zg361_b2_pip_task_kind }
            set_variable = { name = @P@_source_pip_settlement_receipt value = var:zg361_b2_pip_settlement_receipt }
            set_variable = { name = @P@_source_pip_outcome_code value = var:zg361_b2_pip_outcome_code }
            set_variable = { name = @P@_source_pip_result_cycle value = var:zg361_b2_pip_outcome_result_cycle }
            set_variable = { name = @P@_source_pip_result_case value = var:zg361_b2_pip_outcome_result_case }
            set_variable = { name = @P@_source_pip_result_grade value = var:zg361_b2_pip_outcome_result_grade }
            set_variable = { name = @P@_source_pip_case_receipt_id value = var:zg361_b2_workforce_pip_case_id }
            set_variable = { name = @P@_source_pip_case_receipt_hash value = var:zg361_b2_workforce_pip_case_hash }
            set_variable = { name = @P@_source_pip_closure_receipt_id value = var:zg361_b2_workforce_pip_closure_receipt_id }
            set_variable = { name = @P@_source_pip_closure_receipt_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }
            if = {
                limit = { var:zg361_b2_pip_outcome_code = 1 }
                set_variable = { name = @P@_outcome_quality value = 1 } # graduated: pass
            }
            else = {
                set_variable = { name = @P@_outcome_quality value = 2 } # failed: mismatch, not attrition
            }
            set_variable = { name = @P@_outcome_evidence_count value = 2 }
            set_variable = { name = @P@_outcome_evidence_id value = var:zg361_b2_workforce_pip_closure_receipt_id }
            set_variable = { name = @P@_outcome_evidence_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }
            set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_b2_pip_outcome_result_cycle }
            set_variable = { name = @P@_outcome_exclusion_reason value = 0 } # typed not-excluded conclusion
            set_variable = { name = @P@_awaiting_pip value = 0 }
            @P@_publish_canonical_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3001 }
            debug_log = "ZG361WPF RED 3001: PIP hook lacks the unique B2 settlement or collides with a published result"
        }
    }

    # Internal commit: issue one owner-monotonic outcome ID only after a real
    # source guard has populated every canonical payload field.
    @P@_publish_canonical_effect = {
        var:@P@_owner = { save_temporary_scope_as = @P@_publish_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_commit_expected_attribution_bps_1
            value = {
                value = 10000
                subtract = var:@P@_attribution_bps_2
                subtract = var:@P@_attribution_bps_3
            }
        }
        if = {
            limit = {
                OR = { var:@P@_source_kind = 1 var:@P@_source_kind = 2 }
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_source_result_cycle
                has_variable = @P@_source_result_case
                has_variable = @P@_outcome_dimension_1
                has_variable = @P@_outcome_dimension_2
                has_variable = @P@_outcome_dimension_3
                has_variable = @P@_attribution_bps_1
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                has_variable = @P@_attribution_receipt_id
                has_variable = @P@_attribution_receipt_hash
                has_variable = @P@_outcome_quality
                has_variable = @P@_outcome_evidence_count
                has_variable = @P@_outcome_evidence_id
                has_variable = @P@_outcome_evidence_hash
                has_variable = @P@_outcome_observed_cycle
                has_variable = @P@_outcome_exclusion_reason
                exists = scope:@P@_publish_owner_scope
                var:@P@_subject = this
                var:@P@_outcome_observed_cycle > var:@P@_hire_cycle
                var:@P@_outcome_evidence_count >= 1
                var:@P@_outcome_evidence_id > 0
                var:@P@_outcome_evidence_hash > 0
                OR = { var:@P@_outcome_quality = 1 var:@P@_outcome_quality = 2 }
                var:@P@_outcome_exclusion_reason = 0
                var:@P@_attribution_bps_1 = scope:@P@_commit_expected_attribution_bps_1
                OR = {
                    NOT = { has_variable = @P@_outcome_id }
                    var:@P@_outcome_id = 0
                }
            }
            scope:@P@_publish_owner_scope = {
                if = {
                    limit = { NOT = { has_variable = @P@_owner_outcome_serial } }
                    set_variable = { name = @P@_owner_outcome_serial value = 0 }
                }
                change_variable = { name = @P@_owner_outcome_serial add = 1 }
            }
            set_variable = { name = @P@_outcome_id value = scope:@P@_publish_owner_scope.var:@P@_owner_outcome_serial }
            set_variable = {
                name = @P@_outcome_receipt_hash
                value = {
                    value = var:@P@_outcome_id multiply = 1000000
                    add = { value = var:@P@_hire_case multiply = 10000 }
                    add = { value = var:@P@_source_result_case multiply = 100 }
                    add = { value = var:@P@_source_kind multiply = 10 }
                    add = var:@P@_outcome_quality
                }
            }
            set_variable = { name = @P@_published value = 1 }
            set_variable = { name = @P@_consumed value = 0 }
            set_variable = { name = @P@_state value = 3 }
            set_variable = { name = @P@_adapter_status value = 1 }
            # Normalize ROOT to the subject through a hidden character event
            # before invoking Workforce's legacy future consumer.
            @P@_schedule_consume_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3101 }
            debug_log = "ZG361WPF RED 3101: canonical outcome commit rejected incomplete truth"
        }
    }

    # Materialize all twelve legacy aliases only after both the source fact and
    # the exact Workforce #269 pending consumer are ready.  Missing readiness
    # leaves aliases absent, so Workforce continues to fail closed.
    @P@_materialize_and_consume_effect = {
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_consume_subject_scope
        var:@P@_owner = { save_temporary_scope_as = @P@_consume_owner_scope }
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                exists = scope:@P@_consume_owner_scope
                var:@P@_subject = this
                scope:@P@_consume_owner_scope = {
                    has_variable = zg361_review_serial
                    var:zg361_review_serial >= scope:@P@_consume_subject_scope.var:@P@_probation_due_cycle
                    var:zg361_review_serial >= scope:@P@_consume_subject_scope.var:@P@_outcome_observed_cycle
                }
                has_variable = @W@_m269_outcome_pending
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_outcome_settled = 0
                var:@W@_m269_write_owner = scope:@P@_consume_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@P@_hire_case
                var:@W@_m267_candidate_frozen = this
                var:@W@_formal_hc_active = 1
                var:@W@_formal_hc_active_case = var:@P@_hire_case
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            if = {
                limit = { NOT = { has_variable = @W@_ad_external_outcome_id } }
    @ALIAS_SET@
                set_variable = { name = @P@_legacy_aliases_materialized value = 1 }
            }
            @W@_m269_future_consume_effect = yes
            if = {
                limit = {
                    var:@W@_m269_outcome_settled = 1
                    var:@W@_m269_outcome_pending = 0
                    var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                    var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                    var:@W@_m269_consumed_candidate = this
                    var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                    var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                    var:@W@_m269_final_quality = var:@P@_outcome_quality
                }
                @P@_finalize_consumption_receipt_effect = yes
            }
            else = {
                set_variable = { name = @P@_adapter_status value = 5 }
                set_variable = { name = @P@_red_code value = 4003 }
                debug_log = "ZG361WPF RED 4003: Workforce m269 did not acknowledge the exact outcome"
            }
        }
        else_if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@W@_m269_outcome_settled = 1
                var:@W@_m269_outcome_pending = 0
                var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                var:@W@_m269_consumed_candidate = this
                var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                var:@W@_m269_final_quality = var:@P@_outcome_quality
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            @P@_finalize_consumption_receipt_effect = yes
        }
        else_if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@P@_owner = { has_variable = zg361_review_serial }
            }
            set_variable = { name = @P@_adapter_status value = 3 }
            @P@_schedule_consume_retry_effect = yes
        }
        else_if = {
            limit = { var:@P@_state = 4 var:@P@_consumed = 1 }
            set_variable = { name = @P@_adapter_status value = 4 }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 4001 }
            debug_log = "ZG361WPF RED 4001: source exists but exact Workforce consumer tuple is unavailable"
        }
    }

    @P@_schedule_consume_effect = {
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_consumed = 0
                OR = {
                    NOT = { has_variable = @P@_retry_pending }
                    var:@P@_retry_pending = 0
                }
            }
            set_variable = { name = @P@_retry_pending value = 1 }
            trigger_event = { id = zg361wpf.1 days = 1 }
        }
    }

    @P@_schedule_consume_retry_effect = {
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_consumed = 0
                OR = {
                    NOT = { has_variable = @P@_retry_pending }
                    var:@P@_retry_pending = 0
                }
            }
            set_variable = { name = @P@_retry_pending value = 1 }
            trigger_event = { id = zg361wpf.1 days = 90 }
        }
    }

    @P@_finalize_consumption_receipt_effect = {
        var:@P@_owner = { save_temporary_scope_as = @P@_receipt_owner_scope }
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                exists = scope:@P@_receipt_owner_scope
                var:@P@_subject = this
                var:@W@_m269_outcome_settled = 1
                var:@W@_m269_outcome_pending = 0
                var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                var:@W@_m269_consumed_candidate = this
                var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                var:@W@_m269_final_quality = var:@P@_outcome_quality
                has_variable = @W@_m269_receipt_choice
                OR = {
                    var:@W@_m269_receipt_choice = 1
                    var:@W@_m269_receipt_choice = 2
                }
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            scope:@P@_receipt_owner_scope = {
                if = {
                    limit = { NOT = { has_variable = @P@_owner_consume_serial } }
                    set_variable = { name = @P@_owner_consume_serial value = 0 }
                }
                change_variable = { name = @P@_owner_consume_serial add = 1 }
            }
            set_variable = { name = @P@_consume_receipt_id value = scope:@P@_receipt_owner_scope.var:@P@_owner_consume_serial }
            set_variable = {
                name = @P@_consume_receipt_hash
                value = {
                    value = var:@P@_outcome_id multiply = 1000000
                    add = { value = var:@P@_hire_case multiply = 10000 }
                    add = { value = var:@P@_source_result_case multiply = 100 }
                    add = { value = var:@W@_m269_receipt_choice multiply = 10 }
                    add = 1
                }
            }
            set_variable = { name = @P@_consume_owner value = scope:@P@_receipt_owner_scope }
            set_variable = { name = @P@_consume_subject value = this }
            set_variable = { name = @P@_consume_hire_cycle value = var:@P@_hire_cycle }
            set_variable = { name = @P@_consume_hire_case value = var:@P@_hire_case }
            set_variable = { name = @P@_consume_result_cycle value = var:@P@_source_result_cycle }
            set_variable = { name = @P@_consume_result_case value = var:@P@_source_result_case }
            set_variable = { name = @P@_consume_outcome_id value = var:@P@_outcome_id }
            set_variable = { name = @P@_consume_workforce_choice value = var:@W@_m269_receipt_choice }
            set_variable = { name = @P@_consume_workforce_case value = var:@W@_m269_consumed_hire_case }
            set_variable = { name = @P@_consumed value = 1 }
            set_variable = { name = @P@_published value = 1 }
            set_variable = { name = @P@_retry_pending value = 0 }
            set_variable = { name = @P@_state value = 4 }
            set_variable = { name = @P@_adapter_status value = 4 }
    @ALIAS_CLEAR@
            if = {
                limit = { is_ai = no }
                trigger_event = { id = zg361wpf.2 days = 1 }
            }
            debug_log = "ZG361WPF: canonical outcome consumed once by Workforce m269"
        }
        else_if = {
            limit = { var:@P@_state = 4 var:@P@_consumed = 1 }
            set_variable = { name = @P@_adapter_status value = 4 }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 4101 }
        }
    }
    '''
    # Dedent the static template before inserting column-sensitive generated
    # alias fragments; otherwise their zero-column placeholders would pin the
    # whole CK3 file four spaces to the right.
    template = clean(template)
    for key, value in fragments.items():
        template = template.replace(f"@{key}@", value)
    template = template.replace("@P@", PREFIX).replace("@W@", WORKFORCE_PREFIX)
    return generated(template)


def render_events() -> bytes:
    return generated(
        r'''
        namespace = zg361wpf

        # A retry never publishes truth.  It only replays the strict consumer
        # for a canonical fact that one of the two real producer hooks wrote.
        zg361wpf.1 = {
            type = character_event
            hidden = yes
            immediate = {
                set_variable = { name = zg361_workforce_probation_fact_retry_pending value = 0 }
                zg361_workforce_probation_fact_materialize_and_consume_effect = yes
            }
        }

        # Subject-only informational receipt.  AI subjects never receive a
        # player event; manager authority is neither requested nor granted.
        zg361wpf.2 = {
            type = character_event
            title = zg361wpf.2.t
            desc = zg361wpf.2.desc
            trigger = {
                is_ai = no
                has_variable = zg361_workforce_probation_fact_state
                has_variable = zg361_workforce_probation_fact_consumed
                has_variable = zg361_workforce_probation_fact_consume_subject
                var:zg361_workforce_probation_fact_state = 4
                var:zg361_workforce_probation_fact_consumed = 1
                var:zg361_workforce_probation_fact_consume_subject = this
            }
            option = {
                name = zg361wpf.2.a
                set_variable = { name = zg361_workforce_probation_fact_notice_seen value = 1 }
            }
        }
        '''
    )


def localization_rows(language: str) -> list[str]:
    english = language != "simp_chinese"
    if english:
        title = "Probation outcome receipt"
        desc = (
            "A later settled performance result, and where required the unique PIP settlement, "
            "has been bound to this real hire. Workforce #269 consumed the same outcome once."
        )
        option = "Keep the receipt with the hire case."
    else:
        title = "试用期结局回执"
        desc = "后续正式绩效结算，以及适用时唯一的 PIP 结算，已经绑定到这次真实录用。Workforce #269 只消费了同一结局一次。"
        option = "把回执归入本次录用案。"
    return [
        f"l_{language}:",
        f' zg361wpf.2.t:0 "{title}"',
        f' zg361wpf.2.desc:0 "{desc}"',
        f' zg361wpf.2.a:0 "{option}"',
    ]


def render_localization(language: str) -> bytes:
    source = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / f"{PREFIX}_effects.txt": render_effects(),
        MOD_ROOT / "events" / f"{PREFIX}_events.txt": render_events(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"{PREFIX}_l_{language}.yml"
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
            print("RED: stale Workforce probation fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: Workforce probation fact generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce probation fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
