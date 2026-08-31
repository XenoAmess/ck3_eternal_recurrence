#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #276 rehire-history fact producer.

The package defines a fail-closed join between a future canonical *normal*
exit receipt and a later Workforce #269 probation/result receipt.  The existing
#277 provider is a failed-PIP dismissal and is deliberately rejected as a
substitute.  No caller may supply identity, IDs, hashes, booleans or cycles.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
PREFIX = "zg361_workforce_rehire_fact"
NORMAL_EXIT_PREFIX = "zg361_workforce_normal_exit_fact"
PROBATION_PREFIX = "zg361_workforce_probation_fact"
WORKFORCE_PREFIX = "zg361_we"
NAMESPACE = "zg361wrf"
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

# This is the frozen seven-field Career/HC ABI consumed by Workforce #276.
# Values are canonical package fields, not public parameters.
LEGACY_ALIAS_TO_FACT = {
    "rehire_id": "rehire_id",
    "rehire_historical_case_id": "historical_case_id",
    "rehire_historical_case_hash": "historical_case_hash",
    "rehire_historical_cycle": "historical_cycle",
    "rehire_growth_evidence_id": "growth_evidence_id",
    "rehire_growth_evidence_hash": "growth_evidence_hash",
    "rehire_future_cohort_cycle": "future_cohort_cycle",
}

CURRENT_TUPLE_ALIASES = (
    "ad_rehire_history_owner",
    "ad_rehire_history_subject",
    "ad_rehire_history_cycle",
    "ad_rehire_history_case",
    "ad_rehire_history_state",
)

NORMAL_EXIT_REQUIRED_FIELDS = (
    "receipt_active",
    "receipt_sealed",
    "receipt_published",
    "receipt_consumed",
    "receipt_consumed_operation",
    "receipt_owner",
    "receipt_subject",
    "receipt_cycle",
    "receipt_case",
    "receipt_state",
    "receipt_id",
    "receipt_hash",
    "receipt_exit_source_kind",
    "receipt_exit_source_state",
    "receipt_exit_class",
    "receipt_exit_reason_code",
    "receipt_normal_exit_confirmed",
    "receipt_forced",
    "receipt_neutral_record",
    "receipt_actual_exit",
    "receipt_source_hc_release_claimed",
    "receipt_hc_ledger_settled",
    "receipt_hc_authorized_before",
    "receipt_hc_available_before",
    "receipt_hc_reserved_before",
    "receipt_hc_occupied_before",
    "receipt_hc_frozen_before",
    "receipt_hc_reclaimed_before",
    "receipt_hc_authorized_after",
    "receipt_hc_available_after",
    "receipt_hc_reserved_after",
    "receipt_hc_occupied_after",
    "receipt_hc_frozen_after",
    "receipt_hc_reclaimed_after",
    "receipt_hc_destination_frozen",
    "receipt_hc_conservation_verified",
    "receipt_formal_hc_active_before",
    "receipt_formal_hc_active_after",
    "receipt_formal_hc_case",
    "receipt_exit_year",
    "receipt_former_slot_id",
    "receipt_position_type_id",
    "receipt_appointment_receipt_id",
    "receipt_appointment_receipt_hash",
    "receipt_prior_result_owner",
    "receipt_prior_result_subject",
    "receipt_prior_result_cycle",
    "receipt_prior_result_case",
    "receipt_prior_result_state",
    "receipt_prior_result_settlement_receipt",
    "receipt_prior_result_grade",
    "receipt_prior_result_reason",
    "receipt_prior_result_kpi",
    "receipt_prior_result_rank",
    "receipt_prior_result_delivered_year",
    "receipt_prior_result_hash",
    "receipt_prior_pip_present",
    "receipt_displaced_hours",
    "receipt_displaced_cost_receipt",
    "receipt_displaced_cost_hash",
    "receipt_displaced_cost_amount",
    "receipt_native_end_reason",
    "receipt_native_callback_seen",
    "receipt_misconduct_present",
    "receipt_source_object_consumed",
    "receipt_source_receipt_serial",
)

# Prior PIP is history, not normal-exit eligibility.  A subject with no PIP
# must carry an explicit zero discriminator and no synthetic references; a
# subject with a graduated PIP must retain the complete canonical tuple.
NORMAL_EXIT_PIP_REFERENCE_FIELDS = (
    "receipt_prior_pip_owner",
    "receipt_prior_pip_subject",
    "receipt_prior_pip_cycle",
    "receipt_prior_pip_case",
    "receipt_prior_pip_state",
    "receipt_prior_pip_outcome_code",
    "receipt_prior_pip_result_grade",
    "receipt_prior_pip_case_id",
    "receipt_prior_pip_case_hash",
    "receipt_prior_pip_closure_receipt_id",
    "receipt_prior_pip_closure_receipt_hash",
)

# These references are conditional, unlike the always-present discriminator
# above.  A clean exit must not grow made-up misconduct identities; a dirty
# history must carry the canonical case/evidence references intact.
NORMAL_EXIT_MISCONDUCT_REFERENCE_FIELDS = (
    "receipt_misconduct_case_id",
    "receipt_misconduct_case_hash",
    "receipt_misconduct_evidence_id",
    "receipt_misconduct_evidence_hash",
)

PROBATION_REQUIRED_FIELDS = (
    "state",
    "published",
    "consumed",
    "owner",
    "subject",
    "hire_cycle",
    "hire_case",
    "source_kind",
    "source_result_owner",
    "source_result_subject",
    "source_result_cycle",
    "source_result_case",
    "source_result_state",
    "source_result_settlement_receipt",
    "source_result_grade",
    "source_result_reason",
    "source_result_kpi",
    "source_result_rank",
    "outcome_id",
    "outcome_receipt_hash",
    "outcome_quality",
    "outcome_evidence_count",
    "outcome_evidence_id",
    "outcome_evidence_hash",
    "outcome_observed_cycle",
    "consume_receipt_id",
    "consume_receipt_hash",
    "consume_owner",
    "consume_subject",
    "consume_hire_cycle",
    "consume_hire_case",
    "consume_result_cycle",
    "consume_result_case",
    "consume_outcome_id",
    "consume_workforce_choice",
    "consume_workforce_case",
)


def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in textwrap.dedent(text).strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def validate_contract() -> None:
    expected = {
        "rehire_id",
        "rehire_historical_case_id",
        "rehire_historical_case_hash",
        "rehire_historical_cycle",
        "rehire_growth_evidence_id",
        "rehire_growth_evidence_hash",
        "rehire_future_cohort_cycle",
    }
    if set(LEGACY_ALIAS_TO_FACT) != expected or len(LEGACY_ALIAS_TO_FACT) != 7:
        raise ValueError("rehire producer must own exactly the seven frozen aliases")
    if len(NORMAL_EXIT_REQUIRED_FIELDS) != len(set(NORMAL_EXIT_REQUIRED_FIELDS)):
        raise ValueError("normal-exit source field list contains duplicates")
    if len(NORMAL_EXIT_PIP_REFERENCE_FIELDS) != len(set(NORMAL_EXIT_PIP_REFERENCE_FIELDS)):
        raise ValueError("normal-exit PIP reference list contains duplicates")
    if set(NORMAL_EXIT_REQUIRED_FIELDS) & set(NORMAL_EXIT_PIP_REFERENCE_FIELDS):
        raise ValueError("conditional PIP references must not be unconditional fields")
    if len(NORMAL_EXIT_MISCONDUCT_REFERENCE_FIELDS) != len(
        set(NORMAL_EXIT_MISCONDUCT_REFERENCE_FIELDS)
    ):
        raise ValueError("normal-exit misconduct reference list contains duplicates")
    if set(NORMAL_EXIT_REQUIRED_FIELDS) & set(NORMAL_EXIT_MISCONDUCT_REFERENCE_FIELDS):
        raise ValueError("conditional misconduct references must not be unconditional fields")
    if len(PROBATION_REQUIRED_FIELDS) != len(set(PROBATION_REQUIRED_FIELDS)):
        raise ValueError("probation source field list contains duplicates")
    if tuple(LANGUAGES[:2]) != ("english", "simp_chinese") or len(LANGUAGES) != 9:
        raise ValueError("daily localization contract must keep zh/en plus seven placeholders")
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("static package must not claim live readiness")


def _source_has(prefix: str, fields: tuple[str, ...], spaces: int = 12) -> str:
    return "\n".join(" " * spaces + f"has_variable = {prefix}_{field}" for field in fields)


def _legacy_fragments() -> dict[str, str]:
    has_lines: list[str] = []
    exact_lines: list[str] = []
    set_lines: list[str] = []
    clear_lines: list[str] = []
    for alias, fact in LEGACY_ALIAS_TO_FACT.items():
        legacy = f"{WORKFORCE_PREFIX}_ad_external_{alias}"
        canonical = f"{PREFIX}_{fact}"
        has_lines.append(f"has_variable = {legacy}")
        exact_lines.extend((f"has_variable = {legacy}", f"var:{legacy} = var:{canonical}"))
        set_lines.append(f"set_variable = {{ name = {legacy} value = var:{canonical} }}")
        clear_lines.append(f"remove_variable = {legacy}")
    clear_lines.extend(f"remove_variable = {WORKFORCE_PREFIX}_{name}" for name in CURRENT_TUPLE_ALIASES)
    return {
        "LEGACY_HAS": "\n".join(" " * 20 + line for line in has_lines),
        "LEGACY_EXACT": "\n".join(" " * 12 + line for line in exact_lines),
        "LEGACY_SET": "\n".join(" " * 8 + line for line in set_lines),
        "LEGACY_CLEAR": "\n".join(" " * 4 + line for line in clear_lines),
    }


def render_effects() -> bytes:
    fragments = _legacy_fragments()
    template = r'''
    # Workforce #276 subject-centric immutable rehire history.
    # Public ABI: every effect is invoked as `... = yes` in subject scope.
    # No caller supplies owner, subject, cycle, case, ID, hash or truth flag.

    # First causal edge: capture only a canonical NORMAL exit.  The currently
    # implemented #277 exit provider is a failed-PIP dismissal and is
    # intentionally not referenced anywhere in this package.  Only the
    # independent, funded B2 #075 normal-exit producer may satisfy this seam.
    @P@_capture_exit_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
    @NORMAL_EXIT_HAS@
                var:@E@_receipt_active = 1
                var:@E@_receipt_sealed = 1
                var:@E@_receipt_published = 1
                var:@E@_receipt_consumed = 1
                var:@E@_receipt_consumed_operation = 75
                var:@E@_receipt_subject = this
                var:@E@_receipt_cycle > 0
                var:@E@_receipt_case > 0
                var:@E@_receipt_state = 6
                var:@E@_receipt_id > 0
                var:@E@_receipt_hash > 0
                var:@E@_receipt_exit_source_kind = 75
                var:@E@_receipt_exit_source_state = 3
                var:@E@_receipt_exit_class = 1
                var:@E@_receipt_exit_reason_code = 1
                var:@E@_receipt_normal_exit_confirmed = 1
                var:@E@_receipt_forced = 0
                var:@E@_receipt_neutral_record = 1
                var:@E@_receipt_actual_exit = 1
                var:@E@_receipt_source_hc_release_claimed = 1
                var:@E@_receipt_hc_ledger_settled = 1
                var:@E@_receipt_hc_authorized_before >= 1
                var:@E@_receipt_hc_available_before >= 0
                var:@E@_receipt_hc_reserved_before >= 0
                var:@E@_receipt_hc_occupied_before >= 1
                var:@E@_receipt_hc_frozen_before >= 0
                var:@E@_receipt_hc_reclaimed_before >= 0
                var:@E@_receipt_hc_authorized_after = var:@E@_receipt_hc_authorized_before
                var:@E@_receipt_hc_available_after = var:@E@_receipt_hc_available_before
                var:@E@_receipt_hc_reserved_after = var:@E@_receipt_hc_reserved_before
                var:@E@_receipt_hc_occupied_after = { value = var:@E@_receipt_hc_occupied_before subtract = 1 }
                var:@E@_receipt_hc_frozen_after = { value = var:@E@_receipt_hc_frozen_before add = 1 }
                var:@E@_receipt_hc_reclaimed_after = var:@E@_receipt_hc_reclaimed_before
                var:@E@_receipt_hc_authorized_before = {
                    value = var:@E@_receipt_hc_available_before
                    add = var:@E@_receipt_hc_reserved_before
                    add = var:@E@_receipt_hc_occupied_before
                    add = var:@E@_receipt_hc_frozen_before
                    add = var:@E@_receipt_hc_reclaimed_before
                }
                var:@E@_receipt_hc_authorized_after = {
                    value = var:@E@_receipt_hc_available_after
                    add = var:@E@_receipt_hc_reserved_after
                    add = var:@E@_receipt_hc_occupied_after
                    add = var:@E@_receipt_hc_frozen_after
                    add = var:@E@_receipt_hc_reclaimed_after
                }
                var:@E@_receipt_hc_destination_frozen = 1
                var:@E@_receipt_hc_conservation_verified = 1
                var:@E@_receipt_formal_hc_active_before = 1
                var:@E@_receipt_formal_hc_active_after = 0
                var:@E@_receipt_formal_hc_case > 0
                var:@E@_receipt_source_object_consumed = 1
                var:@E@_receipt_source_receipt_serial = var:@E@_receipt_case
                var:@E@_receipt_exit_year > 0
                var:@E@_receipt_exit_year <= current_year
                var:@E@_receipt_former_slot_id > 0
                var:@E@_receipt_position_type_id > 0
                var:@E@_receipt_appointment_receipt_id > 0
                var:@E@_receipt_appointment_receipt_hash > 0
                var:@E@_receipt_prior_result_owner = var:@E@_receipt_owner
                var:@E@_receipt_prior_result_subject = this
                var:@E@_receipt_prior_result_cycle > 0
                var:@E@_receipt_prior_result_cycle <= var:@E@_receipt_cycle
                var:@E@_receipt_prior_result_case > 0
                OR = { var:@E@_receipt_prior_result_state = 3 var:@E@_receipt_prior_result_state = 5 }
                var:@E@_receipt_prior_result_settlement_receipt = var:@E@_receipt_prior_result_case
                var:@E@_receipt_prior_result_grade = 1
                var:@E@_receipt_prior_result_delivered_year > 0
                var:@E@_receipt_prior_result_delivered_year <= var:@E@_receipt_exit_year
                var:@E@_receipt_prior_result_hash > 0
                OR = {
                    AND = {
                        var:@E@_receipt_prior_pip_present = 0
                        NOT = { has_variable = @E@_receipt_prior_pip_owner }
                        NOT = { has_variable = @E@_receipt_prior_pip_subject }
                        NOT = { has_variable = @E@_receipt_prior_pip_cycle }
                        NOT = { has_variable = @E@_receipt_prior_pip_case }
                        NOT = { has_variable = @E@_receipt_prior_pip_state }
                        NOT = { has_variable = @E@_receipt_prior_pip_outcome_code }
                        NOT = { has_variable = @E@_receipt_prior_pip_result_grade }
                        NOT = { has_variable = @E@_receipt_prior_pip_case_id }
                        NOT = { has_variable = @E@_receipt_prior_pip_case_hash }
                        NOT = { has_variable = @E@_receipt_prior_pip_closure_receipt_id }
                        NOT = { has_variable = @E@_receipt_prior_pip_closure_receipt_hash }
                    }
                    AND = {
                        var:@E@_receipt_prior_pip_present = 1
                        has_variable = @E@_receipt_prior_pip_owner
                        has_variable = @E@_receipt_prior_pip_subject
                        has_variable = @E@_receipt_prior_pip_cycle
                        has_variable = @E@_receipt_prior_pip_case
                        has_variable = @E@_receipt_prior_pip_state
                        has_variable = @E@_receipt_prior_pip_outcome_code
                        has_variable = @E@_receipt_prior_pip_result_grade
                        has_variable = @E@_receipt_prior_pip_case_id
                        has_variable = @E@_receipt_prior_pip_case_hash
                        has_variable = @E@_receipt_prior_pip_closure_receipt_id
                        has_variable = @E@_receipt_prior_pip_closure_receipt_hash
                        var:@E@_receipt_prior_pip_owner = var:@E@_receipt_owner
                        var:@E@_receipt_prior_pip_subject = this
                        var:@E@_receipt_prior_pip_cycle > 0
                        var:@E@_receipt_prior_pip_case > 0
                        var:@E@_receipt_prior_pip_state = 3
                        var:@E@_receipt_prior_pip_outcome_code = 1
                        OR = { var:@E@_receipt_prior_pip_result_grade = 2 var:@E@_receipt_prior_pip_result_grade = 3 }
                        var:@E@_receipt_prior_pip_case_id > 0
                        var:@E@_receipt_prior_pip_case_hash > 0
                        var:@E@_receipt_prior_pip_closure_receipt_id > 0
                        var:@E@_receipt_prior_pip_closure_receipt_hash > 0
                        NOT = { var:@E@_receipt_prior_pip_case_id = var:@E@_receipt_prior_pip_closure_receipt_id }
                        NOT = { var:@E@_receipt_prior_pip_case_hash = var:@E@_receipt_prior_pip_closure_receipt_hash }
                    }
                }
                var:@E@_receipt_displaced_hours >= 0
                var:@E@_receipt_displaced_cost_receipt > 0
                var:@E@_receipt_displaced_cost_hash > 0
                var:@E@_receipt_displaced_cost_amount >= 0
                var:@E@_receipt_native_end_reason = 1
                var:@E@_receipt_native_callback_seen = 1
                OR = {
                    AND = {
                        var:@E@_receipt_misconduct_present = 0
                        NOT = { has_variable = @E@_receipt_misconduct_case_id }
                        NOT = { has_variable = @E@_receipt_misconduct_case_hash }
                        NOT = { has_variable = @E@_receipt_misconduct_evidence_id }
                        NOT = { has_variable = @E@_receipt_misconduct_evidence_hash }
                    }
                    AND = {
                        var:@E@_receipt_misconduct_present = 1
                        has_variable = @E@_receipt_misconduct_case_id
                        has_variable = @E@_receipt_misconduct_case_hash
                        has_variable = @E@_receipt_misconduct_evidence_id
                        has_variable = @E@_receipt_misconduct_evidence_hash
                        var:@E@_receipt_misconduct_case_id > 0
                        var:@E@_receipt_misconduct_case_hash > 0
                        var:@E@_receipt_misconduct_evidence_id > 0
                        var:@E@_receipt_misconduct_evidence_hash > 0
                    }
                }
                var:@E@_receipt_owner = { is_alive = yes is_landed = yes zg361_is_celestial_liege_trigger = yes }
                OR = { NOT = { has_variable = @P@_state } var:@P@_state = 0 }
                NOT = {
                    OR = {
                        has_variable = @P@_exit_receipt_id
                        has_variable = @P@_historical_case_id
                        has_variable = @P@_growth_evidence_id
                        has_variable = @P@_rehire_id
                    }
                }
            }
            set_variable = { name = @P@_subject value = this }
            set_variable = { name = @P@_exit_owner value = var:@E@_receipt_owner }
            set_variable = { name = @P@_exit_cycle value = var:@E@_receipt_cycle }
            set_variable = { name = @P@_exit_case value = var:@E@_receipt_case }
            set_variable = { name = @P@_exit_state value = 6 }
            set_variable = { name = @P@_exit_receipt_id value = var:@E@_receipt_id }
            set_variable = { name = @P@_exit_receipt_hash value = var:@E@_receipt_hash }
            set_variable = { name = @P@_exit_class value = var:@E@_receipt_exit_class }
            set_variable = { name = @P@_exit_former_slot_id value = var:@E@_receipt_former_slot_id }
            set_variable = { name = @P@_exit_position_type_id value = var:@E@_receipt_position_type_id }
            set_variable = { name = @P@_exit_appointment_receipt_id value = var:@E@_receipt_appointment_receipt_id }
            set_variable = { name = @P@_exit_appointment_receipt_hash value = var:@E@_receipt_appointment_receipt_hash }
            set_variable = { name = @P@_exit_hc_authorized_before value = var:@E@_receipt_hc_authorized_before }
            set_variable = { name = @P@_exit_hc_available_before value = var:@E@_receipt_hc_available_before }
            set_variable = { name = @P@_exit_hc_reserved_before value = var:@E@_receipt_hc_reserved_before }
            set_variable = { name = @P@_exit_hc_occupied_before value = var:@E@_receipt_hc_occupied_before }
            set_variable = { name = @P@_exit_hc_frozen_before value = var:@E@_receipt_hc_frozen_before }
            set_variable = { name = @P@_exit_hc_reclaimed_before value = var:@E@_receipt_hc_reclaimed_before }
            set_variable = { name = @P@_exit_hc_authorized_after value = var:@E@_receipt_hc_authorized_after }
            set_variable = { name = @P@_exit_hc_available_after value = var:@E@_receipt_hc_available_after }
            set_variable = { name = @P@_exit_hc_reserved_after value = var:@E@_receipt_hc_reserved_after }
            set_variable = { name = @P@_exit_hc_occupied_after value = var:@E@_receipt_hc_occupied_after }
            set_variable = { name = @P@_exit_hc_frozen_after value = var:@E@_receipt_hc_frozen_after }
            set_variable = { name = @P@_exit_hc_reclaimed_after value = var:@E@_receipt_hc_reclaimed_after }
            set_variable = { name = @P@_exit_hc_destination_frozen value = 1 }
            set_variable = { name = @P@_exit_hc_conservation_verified value = 1 }
            set_variable = { name = @P@_exit_formal_hc_active_before value = 1 }
            set_variable = { name = @P@_exit_formal_hc_active_after value = 0 }
            set_variable = { name = @P@_exit_formal_hc_case value = var:@E@_receipt_formal_hc_case }
            set_variable = { name = @P@_old_result_owner value = var:@E@_receipt_prior_result_owner }
            set_variable = { name = @P@_old_result_cycle value = var:@E@_receipt_prior_result_cycle }
            set_variable = { name = @P@_old_result_case value = var:@E@_receipt_prior_result_case }
            set_variable = { name = @P@_old_result_state value = var:@E@_receipt_prior_result_state }
            set_variable = { name = @P@_old_result_settlement_receipt value = var:@E@_receipt_prior_result_settlement_receipt }
            set_variable = { name = @P@_old_result_grade value = var:@E@_receipt_prior_result_grade }
            set_variable = { name = @P@_old_result_reason value = var:@E@_receipt_prior_result_reason }
            set_variable = { name = @P@_old_result_kpi value = var:@E@_receipt_prior_result_kpi }
            set_variable = { name = @P@_old_result_rank value = var:@E@_receipt_prior_result_rank }
            set_variable = { name = @P@_old_result_delivered_year value = var:@E@_receipt_prior_result_delivered_year }
            set_variable = { name = @P@_old_result_hash value = var:@E@_receipt_prior_result_hash }
            set_variable = { name = @P@_exit_pip_present value = var:@E@_receipt_prior_pip_present }
            if = {
                limit = { var:@E@_receipt_prior_pip_present = 1 }
                set_variable = { name = @P@_exit_pip_owner value = var:@E@_receipt_prior_pip_owner }
                set_variable = { name = @P@_exit_pip_cycle value = var:@E@_receipt_prior_pip_cycle }
                set_variable = { name = @P@_exit_pip_case value = var:@E@_receipt_prior_pip_case }
                set_variable = { name = @P@_exit_pip_state value = var:@E@_receipt_prior_pip_state }
                set_variable = { name = @P@_exit_pip_outcome_code value = var:@E@_receipt_prior_pip_outcome_code }
                set_variable = { name = @P@_exit_pip_result_grade value = var:@E@_receipt_prior_pip_result_grade }
                set_variable = { name = @P@_exit_pip_case_id value = var:@E@_receipt_prior_pip_case_id }
                set_variable = { name = @P@_exit_pip_case_hash value = var:@E@_receipt_prior_pip_case_hash }
                set_variable = { name = @P@_exit_pip_closure_receipt_id value = var:@E@_receipt_prior_pip_closure_receipt_id }
                set_variable = { name = @P@_exit_pip_closure_receipt_hash value = var:@E@_receipt_prior_pip_closure_receipt_hash }
            }
            set_variable = { name = @P@_exit_displaced_hours value = var:@E@_receipt_displaced_hours }
            set_variable = { name = @P@_exit_displaced_cost_receipt value = var:@E@_receipt_displaced_cost_receipt }
            set_variable = { name = @P@_exit_displaced_cost_hash value = var:@E@_receipt_displaced_cost_hash }
            set_variable = { name = @P@_exit_displaced_cost_amount value = var:@E@_receipt_displaced_cost_amount }
            set_variable = { name = @P@_exit_observed_year value = var:@E@_receipt_exit_year }
            set_variable = { name = @P@_normal_exit_verified value = 1 }
            set_variable = { name = @P@_pip_history_retained value = 1 }
            set_variable = { name = @P@_misconduct_present value = var:@E@_receipt_misconduct_present }
            if = {
                limit = { var:@E@_receipt_misconduct_present = 1 }
                set_variable = { name = @P@_misconduct_case_id value = var:@E@_receipt_misconduct_case_id }
                set_variable = { name = @P@_misconduct_case_hash value = var:@E@_receipt_misconduct_case_hash }
                set_variable = { name = @P@_misconduct_evidence_id value = var:@E@_receipt_misconduct_evidence_id }
                set_variable = { name = @P@_misconduct_evidence_hash value = var:@E@_receipt_misconduct_evidence_hash }
            }
            set_variable = { name = @P@_misconduct_history_retained value = 1 }
            set_variable = { name = @P@_exit_history_hash value = var:@E@_receipt_prior_result_hash }
            set_variable = { name = @P@_state value = 1 }
            set_variable = { name = @P@_status value = 1 }
            debug_log = "ZG361WRF: canonical normal exit frozen; awaiting later external #269 growth"
        }
        else_if = {
            limit = {
                has_variable = @P@_state
                var:@P@_state >= 1
                var:@P@_subject = this
                var:@P@_exit_owner = var:@E@_receipt_owner
                var:@P@_exit_cycle = var:@E@_receipt_cycle
                var:@P@_exit_case = var:@E@_receipt_case
                var:@P@_exit_receipt_id = var:@E@_receipt_id
                var:@P@_exit_receipt_hash = var:@E@_receipt_hash
                var:@P@_exit_class = 1
                var:@P@_exit_hc_authorized_before = var:@E@_receipt_hc_authorized_before
                var:@P@_exit_hc_available_before = var:@E@_receipt_hc_available_before
                var:@P@_exit_hc_reserved_before = var:@E@_receipt_hc_reserved_before
                var:@P@_exit_hc_occupied_before = var:@E@_receipt_hc_occupied_before
                var:@P@_exit_hc_frozen_before = var:@E@_receipt_hc_frozen_before
                var:@P@_exit_hc_reclaimed_before = var:@E@_receipt_hc_reclaimed_before
                var:@P@_exit_hc_authorized_after = var:@E@_receipt_hc_authorized_after
                var:@P@_exit_hc_available_after = var:@E@_receipt_hc_available_after
                var:@P@_exit_hc_reserved_after = var:@E@_receipt_hc_reserved_after
                var:@P@_exit_hc_occupied_after = var:@E@_receipt_hc_occupied_after
                var:@P@_exit_hc_frozen_after = var:@E@_receipt_hc_frozen_after
                var:@P@_exit_hc_reclaimed_after = var:@E@_receipt_hc_reclaimed_after
                var:@P@_exit_hc_destination_frozen = 1
                var:@P@_exit_hc_conservation_verified = 1
                var:@P@_exit_formal_hc_active_before = 1
                var:@P@_exit_formal_hc_active_after = 0
                var:@P@_exit_formal_hc_case = var:@E@_receipt_formal_hc_case
                var:@P@_old_result_case = var:@E@_receipt_prior_result_case
                var:@P@_old_result_hash = var:@E@_receipt_prior_result_hash
                var:@P@_exit_pip_present = var:@E@_receipt_prior_pip_present
                OR = {
                    AND = {
                        var:@P@_exit_pip_present = 0
                        NOT = { has_variable = @P@_exit_pip_owner }
                        NOT = { has_variable = @P@_exit_pip_cycle }
                        NOT = { has_variable = @P@_exit_pip_case }
                        NOT = { has_variable = @P@_exit_pip_state }
                        NOT = { has_variable = @P@_exit_pip_outcome_code }
                        NOT = { has_variable = @P@_exit_pip_result_grade }
                        NOT = { has_variable = @P@_exit_pip_case_id }
                        NOT = { has_variable = @P@_exit_pip_case_hash }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_id }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_hash }
                        NOT = { has_variable = @E@_receipt_prior_pip_owner }
                        NOT = { has_variable = @E@_receipt_prior_pip_subject }
                        NOT = { has_variable = @E@_receipt_prior_pip_cycle }
                        NOT = { has_variable = @E@_receipt_prior_pip_case }
                        NOT = { has_variable = @E@_receipt_prior_pip_state }
                        NOT = { has_variable = @E@_receipt_prior_pip_outcome_code }
                        NOT = { has_variable = @E@_receipt_prior_pip_result_grade }
                        NOT = { has_variable = @E@_receipt_prior_pip_case_id }
                        NOT = { has_variable = @E@_receipt_prior_pip_case_hash }
                        NOT = { has_variable = @E@_receipt_prior_pip_closure_receipt_id }
                        NOT = { has_variable = @E@_receipt_prior_pip_closure_receipt_hash }
                    }
                    AND = {
                        var:@P@_exit_pip_present = 1
                        var:@P@_exit_pip_owner = var:@E@_receipt_prior_pip_owner
                        var:@P@_exit_pip_cycle = var:@E@_receipt_prior_pip_cycle
                        var:@P@_exit_pip_case = var:@E@_receipt_prior_pip_case
                        var:@P@_exit_pip_state = var:@E@_receipt_prior_pip_state
                        var:@P@_exit_pip_outcome_code = var:@E@_receipt_prior_pip_outcome_code
                        var:@P@_exit_pip_result_grade = var:@E@_receipt_prior_pip_result_grade
                        var:@P@_exit_pip_case_id = var:@E@_receipt_prior_pip_case_id
                        var:@P@_exit_pip_case_hash = var:@E@_receipt_prior_pip_case_hash
                        var:@P@_exit_pip_closure_receipt_id = var:@E@_receipt_prior_pip_closure_receipt_id
                        var:@P@_exit_pip_closure_receipt_hash = var:@E@_receipt_prior_pip_closure_receipt_hash
                    }
                }
                var:@P@_misconduct_present = var:@E@_receipt_misconduct_present
                OR = {
                    AND = {
                        var:@P@_misconduct_present = 0
                        NOT = { has_variable = @P@_misconduct_case_id }
                        NOT = { has_variable = @P@_misconduct_case_hash }
                        NOT = { has_variable = @P@_misconduct_evidence_id }
                        NOT = { has_variable = @P@_misconduct_evidence_hash }
                        NOT = { has_variable = @E@_receipt_misconduct_case_id }
                        NOT = { has_variable = @E@_receipt_misconduct_case_hash }
                        NOT = { has_variable = @E@_receipt_misconduct_evidence_id }
                        NOT = { has_variable = @E@_receipt_misconduct_evidence_hash }
                    }
                    AND = {
                        var:@P@_misconduct_present = 1
                        has_variable = @P@_misconduct_case_id
                        has_variable = @P@_misconduct_case_hash
                        has_variable = @P@_misconduct_evidence_id
                        has_variable = @P@_misconduct_evidence_hash
                        has_variable = @E@_receipt_misconduct_case_id
                        has_variable = @E@_receipt_misconduct_case_hash
                        has_variable = @E@_receipt_misconduct_evidence_id
                        has_variable = @E@_receipt_misconduct_evidence_hash
                        var:@P@_misconduct_case_id > 0
                        var:@P@_misconduct_case_hash > 0
                        var:@P@_misconduct_evidence_id > 0
                        var:@P@_misconduct_evidence_hash > 0
                        var:@P@_misconduct_case_id = var:@E@_receipt_misconduct_case_id
                        var:@P@_misconduct_case_hash = var:@E@_receipt_misconduct_case_hash
                        var:@P@_misconduct_evidence_id = var:@E@_receipt_misconduct_evidence_id
                        var:@P@_misconduct_evidence_hash = var:@E@_receipt_misconduct_evidence_hash
                    }
                }
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 5 }
            set_variable = { name = @P@_red_code value = 27611 }
            debug_log = "ZG361WRF RED 27611: canonical normal-exit provider is absent, stale or colliding"
        }
    }

    # Second causal edge: seal growth only from a fully consumed canonical
    # probation/result receipt.  The growth employer must differ from the old
    # exit owner, so pre-exit/current-employer evidence cannot masquerade as
    # outside growth.  State=1 proves the exit hook happened first.
    @P@_capture_growth_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_subject
                has_variable = @P@_exit_owner
                has_variable = @P@_exit_case
                has_variable = @P@_old_result_cycle
                has_variable = @P@_old_result_case
                has_variable = @P@_old_result_hash
                has_variable = @P@_old_result_grade
                has_variable = @P@_exit_pip_present
                has_variable = @P@_normal_exit_verified
                has_variable = @P@_exit_receipt_id
                has_variable = @P@_exit_receipt_hash
                has_variable = @P@_exit_history_hash
                has_variable = @P@_exit_observed_year
                has_variable = @P@_exit_class
                has_variable = @P@_exit_hc_authorized_before
                has_variable = @P@_exit_hc_available_before
                has_variable = @P@_exit_hc_reserved_before
                has_variable = @P@_exit_hc_occupied_before
                has_variable = @P@_exit_hc_frozen_before
                has_variable = @P@_exit_hc_reclaimed_before
                has_variable = @P@_exit_hc_authorized_after
                has_variable = @P@_exit_hc_available_after
                has_variable = @P@_exit_hc_reserved_after
                has_variable = @P@_exit_hc_occupied_after
                has_variable = @P@_exit_hc_frozen_after
                has_variable = @P@_exit_hc_reclaimed_after
                has_variable = @P@_exit_hc_destination_frozen
                has_variable = @P@_exit_hc_conservation_verified
                has_variable = @P@_exit_formal_hc_active_before
                has_variable = @P@_exit_formal_hc_active_after
                has_variable = @P@_exit_formal_hc_case
                has_variable = @P@_pip_history_retained
                has_variable = @P@_misconduct_present
                has_variable = @P@_misconduct_history_retained
                var:@P@_state = 1
                var:@P@_subject = this
                var:@P@_exit_class = 1
                var:@P@_exit_hc_authorized_before = var:@P@_exit_hc_authorized_after
                var:@P@_exit_hc_available_before = var:@P@_exit_hc_available_after
                var:@P@_exit_hc_reserved_before = var:@P@_exit_hc_reserved_after
                var:@P@_exit_hc_occupied_after = { value = var:@P@_exit_hc_occupied_before subtract = 1 }
                var:@P@_exit_hc_frozen_after = { value = var:@P@_exit_hc_frozen_before add = 1 }
                var:@P@_exit_hc_reclaimed_before = var:@P@_exit_hc_reclaimed_after
                var:@P@_exit_hc_authorized_before = {
                    value = var:@P@_exit_hc_available_before
                    add = var:@P@_exit_hc_reserved_before
                    add = var:@P@_exit_hc_occupied_before
                    add = var:@P@_exit_hc_frozen_before
                    add = var:@P@_exit_hc_reclaimed_before
                }
                var:@P@_exit_hc_authorized_after = {
                    value = var:@P@_exit_hc_available_after
                    add = var:@P@_exit_hc_reserved_after
                    add = var:@P@_exit_hc_occupied_after
                    add = var:@P@_exit_hc_frozen_after
                    add = var:@P@_exit_hc_reclaimed_after
                }
                var:@P@_exit_hc_destination_frozen = 1
                var:@P@_exit_hc_conservation_verified = 1
                var:@P@_exit_formal_hc_active_before = 1
                var:@P@_exit_formal_hc_active_after = 0
                var:@P@_exit_formal_hc_case > 0
                var:@P@_normal_exit_verified = 1
                var:@P@_old_result_grade = 1
                var:@P@_pip_history_retained = 1
                OR = {
                    AND = {
                        var:@P@_exit_pip_present = 0
                        NOT = { has_variable = @P@_exit_pip_owner }
                        NOT = { has_variable = @P@_exit_pip_cycle }
                        NOT = { has_variable = @P@_exit_pip_case }
                        NOT = { has_variable = @P@_exit_pip_state }
                        NOT = { has_variable = @P@_exit_pip_outcome_code }
                        NOT = { has_variable = @P@_exit_pip_result_grade }
                        NOT = { has_variable = @P@_exit_pip_case_id }
                        NOT = { has_variable = @P@_exit_pip_case_hash }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_id }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_hash }
                    }
                    AND = {
                        var:@P@_exit_pip_present = 1
                        has_variable = @P@_exit_pip_owner
                        has_variable = @P@_exit_pip_cycle
                        has_variable = @P@_exit_pip_case
                        has_variable = @P@_exit_pip_state
                        has_variable = @P@_exit_pip_outcome_code
                        has_variable = @P@_exit_pip_result_grade
                        has_variable = @P@_exit_pip_case_id
                        has_variable = @P@_exit_pip_case_hash
                        has_variable = @P@_exit_pip_closure_receipt_id
                        has_variable = @P@_exit_pip_closure_receipt_hash
                        var:@P@_exit_pip_owner = var:@P@_exit_owner
                        var:@P@_exit_pip_cycle > 0
                        var:@P@_exit_pip_case > 0
                        var:@P@_exit_pip_state = 3
                        var:@P@_exit_pip_outcome_code = 1
                        OR = { var:@P@_exit_pip_result_grade = 2 var:@P@_exit_pip_result_grade = 3 }
                        var:@P@_exit_pip_case_id > 0
                        var:@P@_exit_pip_case_hash > 0
                        var:@P@_exit_pip_closure_receipt_id > 0
                        var:@P@_exit_pip_closure_receipt_hash > 0
                    }
                }
                var:@P@_misconduct_history_retained = 1
                OR = {
                    AND = {
                        var:@P@_misconduct_present = 0
                        NOT = { has_variable = @P@_misconduct_case_id }
                        NOT = { has_variable = @P@_misconduct_case_hash }
                        NOT = { has_variable = @P@_misconduct_evidence_id }
                        NOT = { has_variable = @P@_misconduct_evidence_hash }
                    }
                    AND = {
                        var:@P@_misconduct_present = 1
                        has_variable = @P@_misconduct_case_id
                        has_variable = @P@_misconduct_case_hash
                        has_variable = @P@_misconduct_evidence_id
                        has_variable = @P@_misconduct_evidence_hash
                        var:@P@_misconduct_case_id > 0
                        var:@P@_misconduct_case_hash > 0
                        var:@P@_misconduct_evidence_id > 0
                        var:@P@_misconduct_evidence_hash > 0
                    }
                }
                var:@P@_exit_observed_year < current_year
    @PROBATION_HAS@
                var:@Q@_state = 4
                var:@Q@_published = 1
                var:@Q@_consumed = 1
                var:@Q@_subject = this
                var:@Q@_consume_subject = this
                var:@Q@_owner = var:@Q@_consume_owner
                NOT = { var:@Q@_owner = var:@P@_exit_owner }
                var:@Q@_source_result_owner = var:@Q@_owner
                var:@Q@_source_result_subject = this
                var:@Q@_hire_cycle = var:@Q@_consume_hire_cycle
                var:@Q@_hire_case = var:@Q@_consume_hire_case
                var:@Q@_source_result_cycle = var:@Q@_consume_result_cycle
                var:@Q@_source_result_case = var:@Q@_consume_result_case
                OR = { var:@Q@_source_result_state = 3 var:@Q@_source_result_state = 5 }
                var:@Q@_source_result_settlement_receipt = var:@Q@_source_result_case
                OR = { var:@Q@_source_result_grade = 1 var:@Q@_source_result_grade = 2 var:@Q@_source_result_grade = 3 }
                var:@Q@_outcome_id = var:@Q@_consume_outcome_id
                var:@Q@_hire_case = var:@Q@_consume_workforce_case
                var:@Q@_outcome_id > 0
                var:@Q@_outcome_receipt_hash > 0
                OR = { var:@Q@_outcome_quality = 1 var:@Q@_outcome_quality = 2 }
                var:@Q@_outcome_evidence_count >= 1
                var:@Q@_outcome_evidence_id > 0
                var:@Q@_outcome_evidence_hash > 0
                var:@Q@_consume_receipt_id > 0
                var:@Q@_consume_receipt_hash > 0
                OR = { var:@Q@_consume_workforce_choice = 1 var:@Q@_consume_workforce_choice = 2 }
                NOT = { var:@Q@_hire_case = var:@P@_exit_case }
                NOT = { var:@Q@_hire_case = var:@P@_old_result_case }
                NOT = { var:@Q@_outcome_evidence_id = var:@P@_exit_receipt_id }
                NOT = { var:@Q@_outcome_evidence_hash = var:@P@_exit_receipt_hash }
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                has_variable = zg361_result_delivered_year
                var:zg361_result_case_owner = var:@Q@_owner
                var:zg361_result_cycle_serial = var:@Q@_source_result_cycle
                var:zg361_result_case_serial = var:@Q@_source_result_case
                var:zg361_result_case_state = var:@Q@_source_result_state
                var:zg361_result_settlement_posted_serial = var:@Q@_source_result_settlement_receipt
                var:zg361_result_grade = var:@Q@_source_result_grade
                var:zg361_result_grade_reason = var:@Q@_source_result_reason
                var:zg361_result_kpi_frozen = var:@Q@_source_result_kpi
                var:zg361_result_rank_frozen = var:@Q@_source_result_rank
                var:zg361_result_delivered_year = current_year
                var:zg361_result_delivered_year > var:@P@_exit_observed_year
                has_variable = @W@_m269_object_consumed
                has_variable = @W@_m269_write_owner
                has_variable = @W@_m269_write_subject
                has_variable = @W@_m269_write_cycle
                has_variable = @W@_m269_write_case
                has_variable = @W@_m269_write_state
                has_variable = @W@_m269_receipt_owner
                has_variable = @W@_m269_receipt_subject
                has_variable = @W@_m269_receipt_cycle
                has_variable = @W@_m269_receipt_case
                has_variable = @W@_m269_receipt_state
                has_variable = @W@_m269_receipt_choice
                has_variable = @W@_m269_outcome_settled
                has_variable = @W@_m269_outcome_pending
                has_variable = @W@_m269_outcome_provenance_locked
                has_variable = @W@_m269_last_outcome_id
                has_variable = @W@_m269_consumed_hire_case
                has_variable = @W@_m269_consumed_candidate
                has_variable = @W@_m269_outcome_evidence_id
                has_variable = @W@_m269_outcome_evidence_hash
                has_variable = @W@_m269_outcome_observed_cycle
                has_variable = @W@_m269_final_quality
                var:@W@_m269_object_consumed = 1
                var:@W@_m269_write_owner = var:@Q@_owner
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@Q@_hire_cycle
                var:@W@_m269_write_case = var:@Q@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_m269_receipt_owner = var:@Q@_owner
                var:@W@_m269_receipt_subject = this
                var:@W@_m269_receipt_cycle = var:@Q@_hire_cycle
                var:@W@_m269_receipt_case = var:@Q@_hire_case
                var:@W@_m269_receipt_state = 5
                var:@W@_m269_receipt_choice = var:@Q@_consume_workforce_choice
                var:@W@_m269_outcome_settled = 1
                var:@W@_m269_outcome_pending = 0
                var:@W@_m269_outcome_provenance_locked = 1
                var:@W@_m269_last_outcome_id = var:@Q@_outcome_id
                var:@W@_m269_consumed_hire_case = var:@Q@_hire_case
                var:@W@_m269_consumed_candidate = this
                var:@W@_m269_outcome_evidence_id = var:@Q@_outcome_evidence_id
                var:@W@_m269_outcome_evidence_hash = var:@Q@_outcome_evidence_hash
                var:@W@_m269_outcome_observed_cycle = var:@Q@_outcome_observed_cycle
                var:@W@_m269_final_quality = var:@Q@_outcome_quality
            }
            if = {
                limit = { has_variable = @P@_subject_history_serial }
                save_temporary_scope_value_as = {
                    name = @P@_next_subject_history_serial
                    value = { value = var:@P@_subject_history_serial add = 1 }
                }
            }
            else = {
                save_temporary_scope_value_as = { name = @P@_next_subject_history_serial value = 1 }
            }
            set_variable = {
                name = @P@_rehire_id
                value = {
                    value = var:@P@_exit_case multiply = 1000000
                    add = { value = var:@Q@_outcome_id multiply = 1000 }
                    add = { value = scope:@P@_next_subject_history_serial multiply = 10 }
                    add = 6
                }
            }
            set_variable = { name = @P@_historical_case_id value = var:@P@_old_result_case }
            set_variable = { name = @P@_historical_case_hash value = var:@P@_exit_history_hash }
            set_variable = { name = @P@_historical_cycle value = var:@P@_old_result_cycle }
            set_variable = { name = @P@_growth_owner value = var:@Q@_owner }
            set_variable = { name = @P@_growth_hire_cycle value = var:@Q@_hire_cycle }
            set_variable = { name = @P@_growth_hire_case value = var:@Q@_hire_case }
            set_variable = { name = @P@_growth_result_cycle value = var:@Q@_source_result_cycle }
            set_variable = { name = @P@_growth_result_case value = var:@Q@_source_result_case }
            set_variable = { name = @P@_growth_source_kind value = var:@Q@_source_kind }
            set_variable = { name = @P@_growth_outcome_id value = var:@Q@_outcome_id }
            set_variable = { name = @P@_growth_outcome_receipt_hash value = var:@Q@_outcome_receipt_hash }
            set_variable = { name = @P@_growth_quality value = var:@Q@_outcome_quality }
            set_variable = { name = @P@_growth_evidence_count value = var:@Q@_outcome_evidence_count }
            set_variable = { name = @P@_growth_evidence_id value = var:@Q@_outcome_evidence_id }
            set_variable = { name = @P@_growth_evidence_hash value = var:@Q@_outcome_evidence_hash }
            set_variable = { name = @P@_growth_observed_cycle value = var:@Q@_outcome_observed_cycle }
            set_variable = { name = @P@_growth_consume_receipt_id value = var:@Q@_consume_receipt_id }
            set_variable = { name = @P@_growth_consume_receipt_hash value = var:@Q@_consume_receipt_hash }
            set_variable = { name = @P@_growth_workforce_choice value = var:@Q@_consume_workforce_choice }
            set_variable = { name = @P@_old_history_retained value = 1 }
            set_variable = { name = @P@_pip_history_retained value = 1 }
            set_variable = { name = @P@_misconduct_history_retained value = 1 }
            set_variable = { name = @P@_subject_history_serial value = scope:@P@_next_subject_history_serial }
            set_variable = { name = @P@_published value = 1 }
            set_variable = { name = @P@_consumed value = 0 }
            set_variable = { name = @P@_state value = 2 }
            set_variable = { name = @P@_status value = 1 }
            debug_log = "ZG361WRF: old exit and later external #269 outcome sealed as one immutable history"
        }
        else_if = {
            limit = {
                has_variable = @P@_state
                var:@P@_state >= 2
                var:@P@_subject = this
                var:@P@_growth_owner = var:@Q@_owner
                var:@P@_growth_hire_case = var:@Q@_hire_case
                var:@P@_growth_result_case = var:@Q@_source_result_case
                var:@P@_growth_outcome_id = var:@Q@_outcome_id
                var:@P@_growth_evidence_id = var:@Q@_outcome_evidence_id
                var:@P@_growth_evidence_hash = var:@Q@_outcome_evidence_hash
                var:@P@_growth_consume_receipt_id = var:@Q@_consume_receipt_id
                var:@P@_growth_consume_receipt_hash = var:@Q@_consume_receipt_hash
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 5 }
            set_variable = { name = @P@_red_code value = 27621 }
            debug_log = "ZG361WRF RED 27621: later external #269 growth receipt missing, stale or colliding"
        }
    }

    # Private cleanup removes only this package's transient legacy envelope.
    # Canonical old case, PIP, native exit and growth fields are never removed.
    @P@_clear_legacy_envelope_effect = {
    @LEGACY_CLEAR@
        set_variable = { name = @P@_legacy_aliases_materialized value = 0 }
    }

    # Current #276 scheduling is derived from the exact old owner's current AD
    # case.  It creates only a future cohort cycle; the six historical/evidence
    # aliases remain copies of the two immutable source receipts.
    @P@_prepare_m276_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        save_temporary_scope_value_as = {
            name = @P@_next_future_cohort_cycle
            value = { value = var:zg361_case_ad_cycle_serial add = 1 }
        }
        if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_published
                has_variable = @P@_consumed
                has_variable = @P@_subject
                has_variable = @P@_exit_owner
                has_variable = @P@_historical_case_id
                has_variable = @P@_historical_case_hash
                has_variable = @P@_historical_cycle
                has_variable = @P@_growth_evidence_id
                has_variable = @P@_growth_evidence_hash
                has_variable = @P@_normal_exit_verified
                has_variable = @P@_old_result_grade
                has_variable = @P@_exit_pip_present
                has_variable = @P@_pip_history_retained
                has_variable = @P@_misconduct_present
                has_variable = @P@_misconduct_history_retained
                has_variable = zg361_case_ad_owner
                has_variable = zg361_case_ad_subject
                has_variable = zg361_case_ad_cycle_serial
                has_variable = zg361_case_ad_case_serial
                has_variable = zg361_case_ad_state
                has_variable = zg361_case_ad_active
                var:@P@_state = 2
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@P@_subject = this
                var:@P@_normal_exit_verified = 1
                var:@P@_old_result_grade = 1
                var:@P@_pip_history_retained = 1
                OR = {
                    AND = {
                        var:@P@_exit_pip_present = 0
                        NOT = { has_variable = @P@_exit_pip_owner }
                        NOT = { has_variable = @P@_exit_pip_cycle }
                        NOT = { has_variable = @P@_exit_pip_case }
                        NOT = { has_variable = @P@_exit_pip_state }
                        NOT = { has_variable = @P@_exit_pip_outcome_code }
                        NOT = { has_variable = @P@_exit_pip_result_grade }
                        NOT = { has_variable = @P@_exit_pip_case_id }
                        NOT = { has_variable = @P@_exit_pip_case_hash }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_id }
                        NOT = { has_variable = @P@_exit_pip_closure_receipt_hash }
                    }
                    AND = {
                        var:@P@_exit_pip_present = 1
                        has_variable = @P@_exit_pip_owner
                        has_variable = @P@_exit_pip_cycle
                        has_variable = @P@_exit_pip_case
                        has_variable = @P@_exit_pip_state
                        has_variable = @P@_exit_pip_outcome_code
                        has_variable = @P@_exit_pip_result_grade
                        has_variable = @P@_exit_pip_case_id
                        has_variable = @P@_exit_pip_case_hash
                        has_variable = @P@_exit_pip_closure_receipt_id
                        has_variable = @P@_exit_pip_closure_receipt_hash
                        var:@P@_exit_pip_owner = var:@P@_exit_owner
                        var:@P@_exit_pip_cycle > 0
                        var:@P@_exit_pip_case > 0
                        var:@P@_exit_pip_state = 3
                        var:@P@_exit_pip_outcome_code = 1
                        OR = { var:@P@_exit_pip_result_grade = 2 var:@P@_exit_pip_result_grade = 3 }
                        var:@P@_exit_pip_case_id > 0
                        var:@P@_exit_pip_case_hash > 0
                        var:@P@_exit_pip_closure_receipt_id > 0
                        var:@P@_exit_pip_closure_receipt_hash > 0
                    }
                }
                var:@P@_misconduct_history_retained = 1
                OR = {
                    AND = {
                        var:@P@_misconduct_present = 0
                        NOT = { has_variable = @P@_misconduct_case_id }
                        NOT = { has_variable = @P@_misconduct_case_hash }
                        NOT = { has_variable = @P@_misconduct_evidence_id }
                        NOT = { has_variable = @P@_misconduct_evidence_hash }
                    }
                    AND = {
                        var:@P@_misconduct_present = 1
                        has_variable = @P@_misconduct_case_id
                        has_variable = @P@_misconduct_case_hash
                        has_variable = @P@_misconduct_evidence_id
                        has_variable = @P@_misconduct_evidence_hash
                        var:@P@_misconduct_case_id > 0
                        var:@P@_misconduct_case_hash > 0
                        var:@P@_misconduct_evidence_id > 0
                        var:@P@_misconduct_evidence_hash > 0
                    }
                }
                var:zg361_case_ad_subject = this
                var:zg361_case_ad_owner = var:@P@_exit_owner
                var:zg361_case_ad_owner = { is_alive = yes is_landed = yes zg361_is_celestial_liege_trigger = yes }
                var:zg361_case_ad_state = 6
                var:zg361_case_ad_active = 1
                var:@P@_historical_cycle < var:zg361_case_ad_cycle_serial
                NOT = { var:@P@_historical_case_id = var:zg361_case_ad_case_serial }
                var:@P@_historical_case_id = var:@P@_old_result_case
                var:@P@_historical_case_hash = var:@P@_exit_history_hash
                var:@P@_growth_evidence_id > 0
                var:@P@_growth_evidence_hash > 0
                NOT = {
                    OR = {
    @LEGACY_HAS@
                    }
                }
            }
            set_variable = { name = @P@_future_cohort_cycle value = scope:@P@_next_future_cohort_cycle }
    @LEGACY_SET@
            set_variable = { name = @P@_legacy_aliases_materialized value = 1 }
            @W@_submit_m276_rehire_history_effect = {
                TICKET_OWNER = var:zg361_case_ad_owner
                TICKET_SUBJECT = this
                TICKET_CYCLE = var:zg361_case_ad_cycle_serial
                TICKET_CASE = var:zg361_case_ad_case_serial
                REHIRE_ID = var:@P@_rehire_id
                HISTORICAL_CASE_ID = var:@P@_historical_case_id
                HISTORICAL_CASE_HASH = var:@P@_historical_case_hash
                HISTORICAL_CYCLE = var:@P@_historical_cycle
                GROWTH_EVIDENCE_ID = var:@P@_growth_evidence_id
                GROWTH_EVIDENCE_HASH = var:@P@_growth_evidence_hash
                FUTURE_COHORT_CYCLE = var:@P@_future_cohort_cycle
                HISTORY_RETAINED = 1
                MISCONDUCT_HISTORY_RETAINED = 1
            }
            if = {
                limit = {
                    has_variable = @W@_adapter_status
                    var:@W@_adapter_status = 1
                    var:@W@_ad_external_rehire_ready = 1
                    var:@W@_ad_external_rehire_consumed = 0
                    var:@W@_ad_external_rehire_id = var:@P@_rehire_id
                    var:@W@_ad_external_rehire_historical_case_id = var:@P@_historical_case_id
                    var:@W@_ad_external_rehire_historical_case_hash = var:@P@_historical_case_hash
                    var:@W@_ad_external_rehire_historical_cycle = var:@P@_historical_cycle
                    var:@W@_ad_external_rehire_growth_evidence_id = var:@P@_growth_evidence_id
                    var:@W@_ad_external_rehire_growth_evidence_hash = var:@P@_growth_evidence_hash
                    var:@W@_ad_external_rehire_future_cohort_cycle = var:@P@_future_cohort_cycle
                    var:@W@_ad_rehire_history_owner = var:zg361_case_ad_owner
                    var:@W@_ad_rehire_history_subject = this
                    var:@W@_ad_rehire_history_cycle = var:zg361_case_ad_cycle_serial
                    var:@W@_ad_rehire_history_case = var:zg361_case_ad_case_serial
                    var:@W@_ad_rehire_history_state = 6
                }
                set_variable = { name = @P@_prepared_owner value = var:zg361_case_ad_owner }
                set_variable = { name = @P@_prepared_subject value = this }
                set_variable = { name = @P@_prepared_cycle value = var:zg361_case_ad_cycle_serial }
                set_variable = { name = @P@_prepared_case value = var:zg361_case_ad_case_serial }
                set_variable = { name = @P@_state value = 3 }
                set_variable = { name = @P@_status value = 1 }
            }
            else = {
                @P@_clear_legacy_envelope_effect = yes
                set_variable = { name = @P@_status value = 5 }
                set_variable = { name = @P@_red_code value = 27632 }
            }
        }
        else_if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@P@_legacy_aliases_materialized = 1
                var:@P@_prepared_subject = this
                var:@P@_prepared_owner = var:zg361_case_ad_owner
                var:@P@_prepared_cycle = var:zg361_case_ad_cycle_serial
                var:@P@_prepared_case = var:zg361_case_ad_case_serial
                var:@W@_ad_external_rehire_ready = 1
                var:@W@_ad_external_rehire_consumed = 0
    @LEGACY_EXACT@
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 5 }
            set_variable = { name = @P@_red_code value = 27631 }
            debug_log = "ZG361WRF RED 27631: immutable history or exact old-owner #276 case is unavailable"
        }
    }

    # Call only after Workforce route A/B returned.  The exact operation
    # receipt and seven business outputs are the acknowledgement.  Route C did
    # not consume history and therefore cannot finalize this record.
    @P@_finalize_m276_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@P@_legacy_aliases_materialized = 1
                var:@P@_prepared_subject = this
                var:@W@_ad_external_rehire_ready = 0
                var:@W@_ad_external_rehire_consumed = 1
    @LEGACY_EXACT@
                has_variable = @W@_m276_object_consumed
                has_variable = @W@_m276_object_owner
                has_variable = @W@_m276_object_subject
                has_variable = @W@_m276_object_cycle
                has_variable = @W@_m276_object_case
                has_variable = @W@_m276_object_state
                has_variable = @W@_m276_object_id
                var:@W@_m276_object_consumed = 1
                var:@W@_m276_object_owner = var:@P@_prepared_owner
                var:@W@_m276_object_subject = this
                var:@W@_m276_object_cycle = var:@P@_prepared_cycle
                var:@W@_m276_object_case = var:@P@_prepared_case
                var:@W@_m276_object_state = 6
                var:@W@_m276_object_id > 0
                has_variable = @W@_m276_receipt_owner
                has_variable = @W@_m276_receipt_subject
                has_variable = @W@_m276_receipt_cycle
                has_variable = @W@_m276_receipt_case
                has_variable = @W@_m276_receipt_state
                has_variable = @W@_m276_receipt_choice
                var:@W@_m276_receipt_owner = var:@P@_prepared_owner
                var:@W@_m276_receipt_subject = this
                var:@W@_m276_receipt_cycle = var:@P@_prepared_cycle
                var:@W@_m276_receipt_case = var:@P@_prepared_case
                var:@W@_m276_receipt_state = 6
                OR = { var:@W@_m276_receipt_choice = 1 var:@W@_m276_receipt_choice = 2 }
                var:@W@_m276_rehire_id = var:@P@_rehire_id
                var:@W@_m276_rehire_candidate = this
                var:@W@_m276_old_case_id = var:@P@_historical_case_id
                var:@W@_m276_old_case_hash = var:@P@_historical_case_hash
                var:@W@_m276_old_cycle = var:@P@_historical_cycle
                var:@W@_m276_growth_evidence_id = var:@P@_growth_evidence_id
                var:@W@_m276_growth_evidence_hash = var:@P@_growth_evidence_hash
                var:@W@_m276_future_cohort_cycle = var:@P@_future_cohort_cycle
                var:@W@_m276_old_history_retained = 1
                var:@W@_m276_hc_touched = 0
                OR = {
                    AND = { var:@W@_m276_receipt_choice = 1 var:@W@_m276_growth_evidence_frozen = 1 var:@W@_m276_history_wipe_attempt = 0 }
                    AND = { var:@W@_m276_receipt_choice = 2 var:@W@_m276_growth_evidence_frozen = 0 var:@W@_m276_history_wipe_attempt = 1 }
                }
            }
            if = {
                limit = { has_variable = @P@_subject_consume_serial }
                save_temporary_scope_value_as = {
                    name = @P@_next_subject_consume_serial
                    value = { value = var:@P@_subject_consume_serial add = 1 }
                }
            }
            else = {
                save_temporary_scope_value_as = { name = @P@_next_subject_consume_serial value = 1 }
            }
            set_variable = { name = @P@_consume_receipt_id value = scope:@P@_next_subject_consume_serial }
            set_variable = {
                name = @P@_consume_receipt_hash
                value = {
                    value = var:@P@_rehire_id multiply = 1000000
                    add = { value = var:@P@_prepared_case multiply = 1000 }
                    add = { value = var:@W@_m276_receipt_choice multiply = 10 }
                    add = 6
                }
            }
            set_variable = { name = @P@_consume_owner value = var:@P@_prepared_owner }
            set_variable = { name = @P@_consume_subject value = this }
            set_variable = { name = @P@_consume_cycle value = var:@P@_prepared_cycle }
            set_variable = { name = @P@_consume_case value = var:@P@_prepared_case }
            set_variable = { name = @P@_consume_choice value = var:@W@_m276_receipt_choice }
            set_variable = { name = @P@_subject_consume_serial value = scope:@P@_next_subject_consume_serial }
            @P@_clear_legacy_envelope_effect = yes
            set_variable = { name = @P@_consumed value = 1 }
            set_variable = { name = @P@_state value = 4 }
            set_variable = { name = @P@_status value = 4 }
            if = { limit = { is_ai = no } trigger_event = { id = @N@.1 days = 1 } }
            debug_log = "ZG361WRF: Workforce #276 consumed the immutable history once"
        }
        else_if = {
            limit = {
                var:@P@_state = 4
                var:@P@_published = 1
                var:@P@_consumed = 1
                var:@P@_consume_subject = this
            }
            set_variable = { name = @P@_status value = 4 }
        }
        else = {
            set_variable = { name = @P@_status value = 5 }
            set_variable = { name = @P@_red_code value = 27641 }
            debug_log = "ZG361WRF RED 27641: Workforce #276 acknowledgement is absent or does not match"
        }
    }
    '''
    template = clean(template)
    replacements = {
        **fragments,
        "NORMAL_EXIT_HAS": _source_has(NORMAL_EXIT_PREFIX, NORMAL_EXIT_REQUIRED_FIELDS, 12),
        "PROBATION_HAS": _source_has(PROBATION_PREFIX, PROBATION_REQUIRED_FIELDS, 12),
    }
    for key, value in replacements.items():
        template = template.replace(f"@{key}@", value)
    template = (
        template.replace("@P@", PREFIX)
        .replace("@E@", NORMAL_EXIT_PREFIX)
        .replace("@Q@", PROBATION_PREFIX)
        .replace("@W@", WORKFORCE_PREFIX)
        .replace("@N@", NAMESPACE)
    )
    return generated(template)


def render_events() -> bytes:
    return generated(
        f'''
        namespace = {NAMESPACE}

        # Subject-only archive notice.  It grants no manager action and is
        # never shown to an AI subject.
        {NAMESPACE}.1 = {{
            type = character_event
            title = {NAMESPACE}.1.t
            desc = {NAMESPACE}.1.desc
            trigger = {{
                is_ai = no
                has_variable = {PREFIX}_state
                has_variable = {PREFIX}_published
                has_variable = {PREFIX}_consumed
                has_variable = {PREFIX}_consume_subject
                var:{PREFIX}_state = 4
                var:{PREFIX}_published = 1
                var:{PREFIX}_consumed = 1
                var:{PREFIX}_consume_subject = this
            }}
            option = {{
                name = {NAMESPACE}.1.a
                set_variable = {{ name = {PREFIX}_notice_seen value = 1 }}
            }}
        }}
        '''
    )


def localization_rows(language: str) -> list[str]:
    if language == "simp_chinese":
        title = "回聘履历封存"
        desc = "旧离任案、PIP 引用与后来真实绩效证据均已保留。回聘只开启未来考察，不会清零旧 3.25，也不会凭新成果自动保送。"
        option = "旧账不删，新账照算。"
    else:
        title = "Rehire history sealed"
        desc = (
            "The old exit case, its PIP references, and later real performance evidence remain intact. "
            "Rehire opens only a future review; neither the old low grade nor the new result is erased."
        )
        option = "Keep both ledgers intact."
    return [
        f"l_{language}:",
        f' {NAMESPACE}.1.t:0 "{title}"',
        f' {NAMESPACE}.1.desc:0 "{desc}"',
        f' {NAMESPACE}.1.a:0 "{option}"',
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
            print("RED: stale Workforce rehire fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: Workforce rehire fact generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce rehire fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
