#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #276 canonical normal-exit producer.

The producer routes a real B2 #075 route-A voluntary exit through the existing
long-lived native career-slot carrier.  It revokes that slot *before* #075
calls ``force_step_down_landed_titles``, observes the native revoke callback on
a later frame, then executes the real funded #075 acceptance and seals the
receipt only after its business object is consumed on another later frame.

No caller supplies identity, truth flags, IDs, hashes, result values, exit
reason, or callback success.  The failed-PIP #277 receipt is never accepted as
normal-exit evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap
from typing import Final


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
PREFIX: Final[str] = "zg361_workforce_normal_exit_fact"
NAMESPACE: Final[str] = "zg361workforcenormalexitfact"
EXIT_SLOT_PREFIX: Final[str] = "zg361_workforce_exit_fact"
EXIT_SLOT_POSITION: Final[str] = (
    "zg361_workforce_exit_fact_career_slot_court_position"
)
M075_PREFIX: Final[str] = "zg361_b2_m075"
M274_POSITION_TYPE_ID: Final[int] = 3_612_741
CAREER_SLOT_TYPE_ID: Final[int] = 3_612_771
SOURCE_KIND_M075: Final[int] = 75
EXIT_CLASS_NORMAL: Final[int] = 1
EXIT_REASON_VOLUNTARY_PACKAGE: Final[int] = 1
READINESS: Final[str] = "ck3-script-static-ready-not-live"
HEADER = f"# GENERATED FILE — edit tools/gen_{PREFIX}.py\n"

DISPATCH_EVENT_ID: Final[int] = 9100
AUDIT_EVENT_ID: Final[int] = 9101
FINALIZE_EVENT_ID: Final[int] = 9102
CAPTURE_EVENT_ID: Final[int] = 9103
HC_AUDIT_EVENT_ID: Final[int] = 9104
NOTICE_EVENT_ID: Final[int] = 1
REHIRE_CAPTURE_EXIT_EFFECT: Final[str] = "zg361_workforce_rehire_fact_capture_exit_effect"

LANGUAGES: Final[tuple[str, ...]] = (
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

RESULT_FIELDS: Final[tuple[str, ...]] = (
    "case_owner",
    "cycle_serial",
    "case_serial",
    "case_state",
    "settlement_posted_serial",
    "grade",
    "grade_reason",
    "kpi_frozen",
    "rank_frozen",
    "delivered_year",
)

M075_PRE_FIELDS: Final[tuple[str, ...]] = (
    "owner",
    "subject",
    "cycle",
    "case",
    "state",
    "route",
    "offer_gold",
    "receipt_serial",
    "object_owner",
    "object_subject",
    "object_cycle",
    "object_receipt_case",
    "object_state",
    "object_route",
    "object_active",
    "object_consumed",
)

PIP_REFERENCE_FIELDS: Final[tuple[str, ...]] = (
    "owner",
    "subject",
    "cycle",
    "case",
    "state",
    "outcome_code",
    "result_grade",
    "case_id",
    "case_hash",
    "closure_receipt_id",
    "closure_receipt_hash",
)

RECEIPT_ALWAYS_FIELDS: Final[tuple[str, ...]] = (
    "active",
    "sealed",
    "published",
    "consumed",
    "consumed_operation",
    "owner",
    "subject",
    "cycle",
    "case",
    "state",
    "id",
    "hash",
    "exit_source_kind",
    "exit_source_state",
    "exit_class",
    "exit_reason_code",
    "normal_exit_confirmed",
    "forced",
    "neutral_record",
    "actual_exit",
    "source_hc_release_claimed",
    "hc_ledger_settled",
    "hc_authorized_before",
    "hc_available_before",
    "hc_reserved_before",
    "hc_occupied_before",
    "hc_frozen_before",
    "hc_reclaimed_before",
    "hc_authorized_after",
    "hc_available_after",
    "hc_reserved_after",
    "hc_occupied_after",
    "hc_frozen_after",
    "hc_reclaimed_after",
    "hc_destination_frozen",
    "hc_conservation_verified",
    "formal_hc_active_before",
    "formal_hc_active_after",
    "formal_hc_case",
    "exit_year",
    "former_slot_id",
    "position_type_id",
    "carrier_type_id",
    "appointment_receipt_id",
    "appointment_receipt_hash",
    "prior_result_owner",
    "prior_result_subject",
    "prior_result_cycle",
    "prior_result_case",
    "prior_result_state",
    "prior_result_settlement_receipt",
    "prior_result_grade",
    "prior_result_reason",
    "prior_result_kpi",
    "prior_result_rank",
    "prior_result_delivered_year",
    "prior_result_hash",
    "prior_pip_present",
    "displaced_hours",
    "displaced_cost_receipt",
    "displaced_cost_hash",
    "displaced_cost_amount",
    "native_end_reason",
    "native_callback_seen",
    "misconduct_present",
    "source_object_consumed",
    "source_receipt_serial",
)


def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in textwrap.dedent(text).strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def validate_contract() -> None:
    for name, values in (
        ("languages", LANGUAGES),
        ("result fields", RESULT_FIELDS),
        ("m075 fields", M075_PRE_FIELDS),
        ("PIP references", PIP_REFERENCE_FIELDS),
        ("receipt fields", RECEIPT_ALWAYS_FIELDS),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {name}")
    if len(LANGUAGES) != 9 or LANGUAGES[:2] != ("english", "simp_chinese"):
        raise ValueError("daily localization must be zh/en plus seven placeholders")
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("normal-exit package must not claim live readiness")
    if SOURCE_KIND_M075 == 277:
        raise ValueError("failed-PIP #277 can never be the normal-exit source")


def _has(prefix: str, fields: tuple[str, ...], spaces: int = 12) -> str:
    return "\n".join(" " * spaces + f"has_variable = {prefix}_{field}" for field in fields)


def render_effects() -> bytes:
    template = r'''
    # Subject-centric canonical normal-exit fact for Workforce #276.
    # Public ABI is parameterless.  The caller may request the real workflow,
    # but may not assert identity, result, reason, callback success, ID or hash.

    @P@_clear_pending_effect = {
        remove_variable = @P@_pending
        remove_variable = @P@_pending_owner
        remove_variable = @P@_pending_subject
        remove_variable = @P@_pending_cycle
        remove_variable = @P@_pending_case
        remove_variable = @P@_pending_source_state
        remove_variable = @P@_pending_source_receipt_serial
        remove_variable = @P@_pending_result_owner
        remove_variable = @P@_pending_result_cycle
        remove_variable = @P@_pending_result_case
        remove_variable = @P@_pending_result_state
        remove_variable = @P@_pending_result_settlement_receipt
        remove_variable = @P@_pending_result_grade
        remove_variable = @P@_pending_result_reason
        remove_variable = @P@_pending_result_kpi
        remove_variable = @P@_pending_result_rank
        remove_variable = @P@_pending_result_delivered_year
        remove_variable = @P@_pending_result_hash
        remove_variable = @P@_pending_pip_present
        remove_variable = @P@_pending_pip_owner
        remove_variable = @P@_pending_pip_cycle
        remove_variable = @P@_pending_pip_case
        remove_variable = @P@_pending_pip_state
        remove_variable = @P@_pending_pip_outcome_code
        remove_variable = @P@_pending_pip_result_grade
        remove_variable = @P@_pending_pip_case_id
        remove_variable = @P@_pending_pip_case_hash
        remove_variable = @P@_pending_pip_closure_receipt_id
        remove_variable = @P@_pending_pip_closure_receipt_hash
        remove_variable = @P@_pending_slot_id
        remove_variable = @P@_pending_slot_cycle
        remove_variable = @P@_pending_slot_case
        remove_variable = @P@_pending_position_type_id
        remove_variable = @P@_pending_carrier_type_id
        remove_variable = @P@_pending_appointment_receipt_id
        remove_variable = @P@_pending_appointment_receipt_hash
        remove_variable = @P@_pending_displaced_hours
        remove_variable = @P@_pending_hc_authorized_before
        remove_variable = @P@_pending_hc_available_before
        remove_variable = @P@_pending_hc_reserved_before
        remove_variable = @P@_pending_hc_occupied_before
        remove_variable = @P@_pending_hc_frozen_before
        remove_variable = @P@_pending_hc_reclaimed_before
        remove_variable = @P@_pending_hc_migration_authorized
        remove_variable = @P@_pending_cost_receipt
        remove_variable = @P@_pending_cost_hash
        remove_variable = @P@_pending_cost_amount
        remove_variable = @P@_request_authorized
        remove_variable = @P@_request_dispatched
        remove_variable = @P@_native_revoke_callback_seen
        remove_variable = @P@_native_revoke_callback_owner
        remove_variable = @P@_native_revoke_callback_subject
        remove_variable = @P@_native_callback_verified
        remove_variable = @P@_native_end_reason
        remove_variable = @P@_exit_observed_year
    }

    # Entry point for the B2 #075 route-A option.  It must replace the current
    # direct accept call: the native career slot is revoked first so the later
    # landed-title step-down cannot turn this into an invalidation callback.
    @P@_begin_from_m075_offer_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                has_variable = @P@_receipt_active
                var:@P@_receipt_active = 1
                var:@P@_receipt_sealed = 1
                var:@P@_receipt_published = 1
                var:@P@_receipt_consumed = 1
                var:@P@_receipt_consumed_operation = @SOURCE_KIND@
                var:@P@_receipt_subject = this
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else_if = {
            limit = {
    @M075_HAS@
                var:@M@_owner = { is_alive = yes is_landed = yes zg361_is_celestial_liege_trigger = yes }
                var:@M@_subject = this
                var:@M@_cycle > 0
                var:@M@_case > 0
                var:@M@_state = 1
                var:@M@_route = 1
                var:@M@_offer_gold = 50
                var:@M@_receipt_serial = var:@M@_case
                var:@M@_object_owner = var:@M@_owner
                var:@M@_object_subject = this
                var:@M@_object_cycle = var:@M@_cycle
                var:@M@_object_receipt_case = var:@M@_case
                var:@M@_object_route = 1
                var:@M@_object_active = 1
                var:@M@_object_consumed = 0
                has_variable = zg361_b2_case_owner
                has_variable = zg361_b2_case_subject
                has_variable = zg361_b2_case_cycle
                has_variable = zg361_b2_case_serial
                var:zg361_b2_case_owner = var:@M@_owner
                var:zg361_b2_case_subject = this
                var:zg361_b2_case_cycle = var:@M@_cycle
                var:zg361_b2_case_serial = var:@M@_case
                var:@M@_owner = { government_has_flag = government_has_treasury treasury >= 50 }
                OR = { NOT = { has_variable = @M@_coercion_evidence } var:@M@_coercion_evidence = 0 }
                OR = { NOT = { has_variable = @M@_procedural_redundancy } var:@M@_procedural_redundancy = 0 }
                OR = { NOT = { has_variable = @M@_reclassification_due } var:@M@_reclassification_due = 0 }
                OR = { NOT = { has_variable = @M@_refused_without_transfer } var:@M@_refused_without_transfer = 0 }
                OR = { NOT = { has_variable = @M@_expired } var:@M@_expired = 0 }
    @RESULT_HAS@
                var:zg361_result_case_owner = var:@M@_owner
                var:zg361_result_cycle_serial = var:@M@_cycle
                var:zg361_result_case_serial = var:@M@_case
                OR = { var:zg361_result_case_state = 3 var:zg361_result_case_state = 5 }
                var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
                var:zg361_result_grade = 1
                var:zg361_result_delivered_year > 0
                var:zg361_result_delivered_year <= current_year
                OR = {
                    AND = {
                        OR = { NOT = { has_variable = zg361_b2_pip_state } var:zg361_b2_pip_state = 0 }
                        OR = { NOT = { has_variable = zg361_b2_workforce_pip_pending } var:zg361_b2_workforce_pip_pending = 0 }
                    }
                    AND = {
                        has_variable = zg361_b2_pip_owner
                        has_variable = zg361_b2_pip_subject
                        has_variable = zg361_b2_pip_cycle
                        has_variable = zg361_b2_pip_case
                        has_variable = zg361_b2_pip_state
                        has_variable = zg361_b2_pip_outcome_code
                        has_variable = zg361_b2_pip_outcome_result_grade
                        has_variable = zg361_b2_pip_graduation_receipt
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
                        var:zg361_b2_pip_owner = var:@M@_owner
                        var:zg361_b2_pip_subject = this
                        var:zg361_b2_pip_cycle > 0
                        var:zg361_b2_pip_case > 0
                        var:zg361_b2_pip_state = 3
                        var:zg361_b2_pip_outcome_code = 1
                        OR = { var:zg361_b2_pip_outcome_result_grade = 2 var:zg361_b2_pip_outcome_result_grade = 3 }
                        var:zg361_b2_pip_graduation_receipt = var:zg361_b2_pip_case
                        var:zg361_b2_workforce_pip_pending = 1
                        var:zg361_b2_workforce_pip_consumed = 0
                        var:zg361_b2_workforce_pip_owner = var:zg361_b2_pip_owner
                        var:zg361_b2_workforce_pip_subject = this
                        var:zg361_b2_workforce_pip_cycle = var:zg361_b2_pip_cycle
                        var:zg361_b2_workforce_pip_case = var:zg361_b2_pip_case
                        var:zg361_b2_workforce_pip_state = 3
                        var:zg361_b2_workforce_pip_case_id > 0
                        var:zg361_b2_workforce_pip_case_hash > 0
                        var:zg361_b2_workforce_pip_closure_receipt_id > 0
                        var:zg361_b2_workforce_pip_closure_receipt_hash > 0
                        NOT = { var:zg361_b2_workforce_pip_case_id = var:zg361_b2_workforce_pip_closure_receipt_id }
                        NOT = { var:zg361_b2_workforce_pip_case_hash = var:zg361_b2_workforce_pip_closure_receipt_hash }
                    }
                }
                OR = { NOT = { has_variable = zg361_b2_m073_malicious } var:zg361_b2_m073_malicious = 0 }
                has_variable = @S@_slot_active
                has_variable = @S@_slot_owner
                has_variable = @S@_slot_subject
                has_variable = @S@_slot_cycle
                has_variable = @S@_slot_case
                has_variable = @S@_slot_state
                has_variable = @S@_slot_position_type_id
                has_variable = @S@_slot_appointment_receipt_id
                has_variable = @S@_slot_appointment_receipt_hash
                has_variable = @S@_slot_carrier_type_id
                has_variable = @S@_slot_id
                var:@S@_slot_active = 1
                var:@S@_slot_owner = var:@M@_owner
                var:@S@_slot_subject = this
                var:@S@_slot_cycle > 0
                var:@S@_slot_case > 0
                var:@S@_slot_state = 4
                var:@S@_slot_position_type_id = @POSITION_TYPE@
                var:@S@_slot_appointment_receipt_id > 0
                var:@S@_slot_appointment_receipt_hash > 0
                var:@S@_slot_carrier_type_id = @CARRIER_TYPE@
                var:@S@_slot_id > 0
                has_court_position = @POSITION@
                is_court_position_employer = { court_position = @POSITION@ who = var:@M@_owner }
                OR = { NOT = { has_variable = @S@_exit_pending } var:@S@_exit_pending = 0 }
                OR = { NOT = { has_variable = @S@_receipt_active } var:@S@_receipt_active = 0 }
                OR = { NOT = { has_variable = @P@_pending } var:@P@_pending = 0 }
                OR = { NOT = { has_variable = @P@_receipt_active } var:@P@_receipt_active = 0 }
                has_variable = zg361_we_hours_output
                has_variable = zg361_we_hours_on_call
                has_variable = zg361_we_hours_meeting
                has_variable = zg361_we_hours_governance
                var:zg361_we_hours_output >= 0
                var:zg361_we_hours_on_call >= 0
                var:zg361_we_hours_meeting >= 0
                var:zg361_we_hours_governance >= 0
                var:zg361_we_formal_hc_active = 1
                var:zg361_we_formal_hc_active_case = var:@S@_slot_case
                has_variable = zg361_ch_hc_authorized
                has_variable = zg361_ch_hc_available
                has_variable = zg361_ch_hc_reserved
                has_variable = zg361_ch_hc_occupied
                has_variable = zg361_ch_hc_frozen
                has_variable = zg361_ch_hc_reclaimed
                var:zg361_ch_hc_authorized >= 1
                var:zg361_ch_hc_available >= 0
                var:zg361_ch_hc_reserved >= 0
                var:zg361_ch_hc_occupied >= 1
                var:zg361_ch_hc_frozen >= 0
                var:zg361_ch_hc_reclaimed >= 0
                var:zg361_ch_hc_authorized = {
                    value = var:zg361_ch_hc_available
                    add = var:zg361_ch_hc_reserved
                    add = var:zg361_ch_hc_occupied
                    add = var:zg361_ch_hc_frozen
                    add = var:zg361_ch_hc_reclaimed
                }
            }
            set_variable = { name = @P@_pending value = 1 }
            set_variable = { name = @P@_pending_owner value = var:@M@_owner }
            set_variable = { name = @P@_pending_subject value = this }
            set_variable = { name = @P@_pending_cycle value = var:@M@_cycle }
            set_variable = { name = @P@_pending_case value = var:@M@_case }
            set_variable = { name = @P@_pending_source_state value = var:@M@_state }
            set_variable = { name = @P@_pending_source_receipt_serial value = var:@M@_receipt_serial }
            set_variable = { name = @P@_pending_result_owner value = var:zg361_result_case_owner }
            set_variable = { name = @P@_pending_result_cycle value = var:zg361_result_cycle_serial }
            set_variable = { name = @P@_pending_result_case value = var:zg361_result_case_serial }
            set_variable = { name = @P@_pending_result_state value = var:zg361_result_case_state }
            set_variable = { name = @P@_pending_result_settlement_receipt value = var:zg361_result_settlement_posted_serial }
            set_variable = { name = @P@_pending_result_grade value = var:zg361_result_grade }
            set_variable = { name = @P@_pending_result_reason value = var:zg361_result_grade_reason }
            set_variable = { name = @P@_pending_result_kpi value = var:zg361_result_kpi_frozen }
            set_variable = { name = @P@_pending_result_rank value = var:zg361_result_rank_frozen }
            set_variable = { name = @P@_pending_result_delivered_year value = var:zg361_result_delivered_year }
            set_variable = {
                name = @P@_pending_result_hash
                value = {
                    value = var:zg361_result_case_serial multiply = 100000
                    add = { value = var:zg361_result_cycle_serial multiply = 100 }
                    add = { value = var:zg361_result_grade_reason multiply = 10 }
                    add = var:zg361_result_case_state
                }
            }
            if = {
                limit = { has_variable = zg361_b2_pip_state var:zg361_b2_pip_state = 3 }
                set_variable = { name = @P@_pending_pip_present value = 1 }
                set_variable = { name = @P@_pending_pip_owner value = var:zg361_b2_pip_owner }
                set_variable = { name = @P@_pending_pip_cycle value = var:zg361_b2_pip_cycle }
                set_variable = { name = @P@_pending_pip_case value = var:zg361_b2_pip_case }
                set_variable = { name = @P@_pending_pip_state value = 3 }
                set_variable = { name = @P@_pending_pip_outcome_code value = 1 }
                set_variable = { name = @P@_pending_pip_result_grade value = var:zg361_b2_pip_outcome_result_grade }
                set_variable = { name = @P@_pending_pip_case_id value = var:zg361_b2_workforce_pip_case_id }
                set_variable = { name = @P@_pending_pip_case_hash value = var:zg361_b2_workforce_pip_case_hash }
                set_variable = { name = @P@_pending_pip_closure_receipt_id value = var:zg361_b2_workforce_pip_closure_receipt_id }
                set_variable = { name = @P@_pending_pip_closure_receipt_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }
            }
            else = { set_variable = { name = @P@_pending_pip_present value = 0 } }
            set_variable = { name = @P@_pending_slot_id value = var:@S@_slot_id }
            set_variable = { name = @P@_pending_slot_cycle value = var:@S@_slot_cycle }
            set_variable = { name = @P@_pending_slot_case value = var:@S@_slot_case }
            set_variable = { name = @P@_pending_position_type_id value = var:@S@_slot_position_type_id }
            set_variable = { name = @P@_pending_carrier_type_id value = var:@S@_slot_carrier_type_id }
            set_variable = { name = @P@_pending_appointment_receipt_id value = var:@S@_slot_appointment_receipt_id }
            set_variable = { name = @P@_pending_appointment_receipt_hash value = var:@S@_slot_appointment_receipt_hash }
            set_variable = { name = @P@_pending_displaced_hours value = { value = var:zg361_we_hours_output add = var:zg361_we_hours_on_call add = var:zg361_we_hours_meeting add = var:zg361_we_hours_governance } }
            set_variable = { name = @P@_pending_hc_authorized_before value = var:zg361_ch_hc_authorized }
            set_variable = { name = @P@_pending_hc_available_before value = var:zg361_ch_hc_available }
            set_variable = { name = @P@_pending_hc_reserved_before value = var:zg361_ch_hc_reserved }
            set_variable = { name = @P@_pending_hc_occupied_before value = var:zg361_ch_hc_occupied }
            set_variable = { name = @P@_pending_hc_frozen_before value = var:zg361_ch_hc_frozen }
            set_variable = { name = @P@_pending_hc_reclaimed_before value = var:zg361_ch_hc_reclaimed }
            set_variable = { name = @P@_pending_cost_amount value = 50 }
            set_variable = { name = @P@_pending_cost_receipt value = { value = var:@M@_receipt_serial multiply = 1000 add = 75 } }
            set_variable = { name = @P@_pending_cost_hash value = { value = var:@S@_slot_appointment_receipt_hash multiply = 100000 add = { value = var:@M@_receipt_serial multiply = 100 } add = 75 } }
            set_variable = { name = @P@_request_authorized value = 1 }
            set_variable = { name = @P@_status value = 5 }
            trigger_event = { id = @N@.@DISPATCH@ days = 1 }
            debug_log = "ZG361WNEF: #075 normal-exit intent frozen; awaiting native revoke dispatch"
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 27651 }
            debug_log = "ZG361WNEF RED 27651: no exact funded route-A #075 offer, 3.25 case, or active native career slot"
        }
    }

    # D+1 dispatch.  The existing career carrier's callback changes slot_active
    # to zero; the normal-exit package does not fabricate that callback bit.
    @P@_dispatch_native_revoke_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                var:@P@_pending = 1
                var:@P@_pending_subject = this
                var:@P@_request_authorized = 1
                var:@M@_owner = var:@P@_pending_owner
                var:@M@_subject = this
                var:@M@_cycle = var:@P@_pending_cycle
                var:@M@_case = var:@P@_pending_case
                var:@M@_state = 1
                var:@M@_route = 1
                var:@M@_object_active = 1
                var:@M@_object_consumed = 0
                var:zg361_b2_case_owner = var:@P@_pending_owner
                var:zg361_b2_case_subject = this
                var:zg361_b2_case_cycle = var:@P@_pending_cycle
                var:zg361_b2_case_serial = var:@P@_pending_case
                var:@M@_owner = { government_has_flag = government_has_treasury treasury >= 50 }
                var:zg361_result_case_owner = var:@P@_pending_result_owner
                var:zg361_result_cycle_serial = var:@P@_pending_result_cycle
                var:zg361_result_case_serial = var:@P@_pending_result_case
                var:zg361_result_case_state = var:@P@_pending_result_state
                var:zg361_result_settlement_posted_serial = var:@P@_pending_result_settlement_receipt
                var:zg361_result_grade = 1
                var:@S@_slot_active = 1
                var:@S@_slot_owner = var:@P@_pending_owner
                var:@S@_slot_subject = this
                var:@S@_slot_id = var:@P@_pending_slot_id
                has_court_position = @POSITION@
                is_court_position_employer = { court_position = @POSITION@ who = var:@P@_pending_owner }
                OR = { NOT = { has_variable = @S@_exit_pending } var:@S@_exit_pending = 0 }
                OR = { NOT = { has_variable = @S@_receipt_active } var:@S@_receipt_active = 0 }
            }
            set_variable = { name = @P@_request_dispatched value = 1 }
            revoke_court_position = @POSITION@
            set_variable = { name = @P@_status value = 5 }
            trigger_event = { id = @N@.@AUDIT@ days = 1 }
        }
        else = {
            @P@_clear_pending_effect = yes
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 27652 }
            debug_log = "ZG361WNEF RED 27652: native revoke dispatch lost its exact pre-exit tuple"
        }
    }

    # D+1 native audit.  Only END_REASON=1 plus the actual no-longer-holder
    # postcondition may advance.  Then the real B2 #075 effect performs its
    # funded transfer and landed-title step-down; its writes are read next day.
    @P@_audit_native_then_accept_m075_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                var:@P@_pending = 1
                var:@P@_pending_subject = this
                var:@P@_request_authorized = 1
                var:@P@_request_dispatched = 1
                var:@S@_slot_active = 0
                var:@S@_native_last_end_reason = 1
                var:@S@_native_last_end_owner = var:@P@_pending_owner
                var:@S@_native_last_end_subject = this
                var:@S@_native_revoked_seen = 1
                var:@S@_native_revoked_owner = var:@P@_pending_owner
                var:@S@_native_revoked_subject = this
                var:@P@_native_revoke_callback_seen = 1
                var:@P@_native_revoke_callback_owner = var:@P@_pending_owner
                var:@P@_native_revoke_callback_subject = this
                NOT = { has_court_position = @POSITION@ }
                var:@M@_owner = var:@P@_pending_owner
                var:@M@_subject = this
                var:@M@_cycle = var:@P@_pending_cycle
                var:@M@_case = var:@P@_pending_case
                var:@M@_state = 1
                var:@M@_route = 1
                var:@M@_offer_gold = 50
                var:@M@_object_owner = var:@P@_pending_owner
                var:@M@_object_subject = this
                var:@M@_object_cycle = var:@P@_pending_cycle
                var:@M@_object_receipt_case = var:@P@_pending_case
                var:@M@_object_route = 1
                var:@M@_object_active = 1
                var:@M@_object_consumed = 0
                var:zg361_b2_case_owner = var:@P@_pending_owner
                var:zg361_b2_case_subject = this
                var:zg361_b2_case_cycle = var:@P@_pending_cycle
                var:zg361_b2_case_serial = var:@P@_pending_case
                var:@M@_owner = { government_has_flag = government_has_treasury treasury >= 50 }
                var:zg361_result_case_owner = var:@P@_pending_result_owner
                var:zg361_result_cycle_serial = var:@P@_pending_result_cycle
                var:zg361_result_case_serial = var:@P@_pending_result_case
                var:zg361_result_case_state = var:@P@_pending_result_state
                var:zg361_result_settlement_posted_serial = var:@P@_pending_result_settlement_receipt
                var:zg361_result_grade = 1
            }
            set_variable = { name = @P@_native_callback_verified value = 1 }
            set_variable = { name = @P@_native_end_reason value = 1 }
            set_variable = { name = @P@_exit_observed_year value = current_year }
            set_variable = { name = @P@_state value = 2 }
            trigger_event = { id = @N@.@FINALIZE@ days = 1 }
            zg361_b2_m075_accept_exit_offer_effect = yes
            set_variable = { name = @P@_status value = 5 }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 27653 }
            debug_log = "ZG361WNEF RED 27653: requested native revoke callback or #075 prestate was not observed"
        }
    }

    # D+1 #075 audit and the only HC mutation point.  A normal departure turns
    # one occupied position into a frozen vacancy, matching #277 semantics;
    # it does not make the vacancy automatically recruitable.  Receipt sealing
    # waits for a later frame to observe the committed partition.
    @P@_migrate_hc_partition_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                var:@P@_state = 2
                var:@P@_pending = 1
                var:@P@_pending_subject = this
                var:@P@_native_callback_verified = 1
                var:@P@_native_end_reason = 1
                var:@P@_exit_observed_year > 0
                var:@P@_exit_observed_year <= current_year
                var:@S@_slot_active = 0
                NOT = { has_court_position = @POSITION@ }
                var:@M@_owner = var:@P@_pending_owner
                var:@M@_subject = this
                var:@M@_cycle = var:@P@_pending_cycle
                var:@M@_case = var:@P@_pending_case
                var:@M@_state = 3
                var:@M@_route = 1
                var:@M@_offer_gold = 50
                var:@M@_receipt_serial = var:@P@_pending_source_receipt_serial
                var:@M@_treasury_paid = 50
                var:@M@_personal_received = 50
                var:@M@_neutral_record = 1
                var:@M@_actual_exit = 1
                var:@M@_hc_released = 1
                var:@M@_object_owner = var:@P@_pending_owner
                var:@M@_object_subject = this
                var:@M@_object_cycle = var:@P@_pending_cycle
                var:@M@_object_receipt_case = var:@P@_pending_case
                var:@M@_object_route = 1
                var:@M@_object_active = 0
                var:@M@_object_consumed = 1
                var:@M@_consumer_receipt_case = var:@P@_pending_case
                OR = { NOT = { has_variable = @M@_coercion_evidence } var:@M@_coercion_evidence = 0 }
                OR = { NOT = { has_variable = @M@_procedural_redundancy } var:@M@_procedural_redundancy = 0 }
                OR = { NOT = { has_variable = @M@_reclassification_due } var:@M@_reclassification_due = 0 }
                var:zg361_result_case_owner = var:@P@_pending_result_owner
                var:zg361_result_cycle_serial = var:@P@_pending_result_cycle
                var:zg361_result_case_serial = var:@P@_pending_result_case
                var:zg361_result_case_state = var:@P@_pending_result_state
                var:zg361_result_settlement_posted_serial = var:@P@_pending_result_settlement_receipt
                var:zg361_result_grade = 1
                var:@P@_pending_hc_authorized_before >= 1
                var:@P@_pending_hc_available_before >= 0
                var:@P@_pending_hc_reserved_before >= 0
                var:@P@_pending_hc_occupied_before >= 1
                var:@P@_pending_hc_frozen_before >= 0
                var:@P@_pending_hc_reclaimed_before >= 0
                var:@P@_pending_hc_authorized_before = {
                    value = var:@P@_pending_hc_available_before
                    add = var:@P@_pending_hc_reserved_before
                    add = var:@P@_pending_hc_occupied_before
                    add = var:@P@_pending_hc_frozen_before
                    add = var:@P@_pending_hc_reclaimed_before
                }
                var:zg361_we_formal_hc_active = 1
                var:zg361_we_formal_hc_active_case = var:@P@_pending_slot_case
                var:zg361_ch_hc_authorized = var:@P@_pending_hc_authorized_before
                var:zg361_ch_hc_available = var:@P@_pending_hc_available_before
                var:zg361_ch_hc_reserved = var:@P@_pending_hc_reserved_before
                var:zg361_ch_hc_occupied = var:@P@_pending_hc_occupied_before
                var:zg361_ch_hc_frozen = var:@P@_pending_hc_frozen_before
                var:zg361_ch_hc_reclaimed = var:@P@_pending_hc_reclaimed_before
                OR = { NOT = { has_variable = @P@_receipt_active } var:@P@_receipt_active = 0 }
            }
            set_variable = { name = @P@_pending_hc_migration_authorized value = 1 }
            change_variable = { name = zg361_ch_hc_occupied add = -1 }
            change_variable = { name = zg361_ch_hc_frozen add = 1 }
            set_variable = { name = zg361_we_formal_hc_active value = 0 }
            set_variable = { name = @P@_state value = 3 }
            set_variable = { name = @P@_status value = 5 }
            trigger_event = { id = @N@.@HC_AUDIT@ days = 1 }
            debug_log = "ZG361WNEF: #075 exit migrated occupied HC into a frozen vacancy; awaiting D+1 conservation audit"
        }
        else_if = {
            limit = {
                var:@P@_receipt_active = 1
                var:@P@_receipt_sealed = 1
                var:@P@_receipt_published = 1
                var:@P@_receipt_consumed = 1
                var:@P@_receipt_consumed_operation = @SOURCE_KIND@
                var:@P@_receipt_subject = this
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 27654 }
            debug_log = "ZG361WNEF RED 27654: #075 poststate or pre-migration HC partition was not exact"
        }
    }

    # D+1 partition audit and receipt seal.  No receipt can exist until every
    # formal HC bin is observed in its expected post-migration state and the
    # authorized total is conserved.  The former active-case marker remains as
    # lineage, while formal_hc_active itself must be zero.
    @P@_audit_hc_then_finalize_receipt_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_pending = 1
                var:@P@_pending_subject = this
                var:@P@_pending_hc_migration_authorized = 1
                var:@P@_native_callback_verified = 1
                var:@P@_native_end_reason = 1
                var:@P@_exit_observed_year > 0
                var:@P@_exit_observed_year <= current_year
                var:@S@_slot_active = 0
                NOT = { has_court_position = @POSITION@ }
                var:@M@_owner = var:@P@_pending_owner
                var:@M@_subject = this
                var:@M@_cycle = var:@P@_pending_cycle
                var:@M@_case = var:@P@_pending_case
                var:@M@_state = 3
                var:@M@_route = 1
                var:@M@_offer_gold = 50
                var:@M@_receipt_serial = var:@P@_pending_source_receipt_serial
                var:@M@_treasury_paid = 50
                var:@M@_personal_received = 50
                var:@M@_neutral_record = 1
                var:@M@_actual_exit = 1
                var:@M@_hc_released = 1
                var:@M@_object_owner = var:@P@_pending_owner
                var:@M@_object_subject = this
                var:@M@_object_cycle = var:@P@_pending_cycle
                var:@M@_object_receipt_case = var:@P@_pending_case
                var:@M@_object_route = 1
                var:@M@_object_active = 0
                var:@M@_object_consumed = 1
                var:@M@_consumer_receipt_case = var:@P@_pending_case
                var:zg361_result_case_owner = var:@P@_pending_result_owner
                var:zg361_result_cycle_serial = var:@P@_pending_result_cycle
                var:zg361_result_case_serial = var:@P@_pending_result_case
                var:zg361_result_case_state = var:@P@_pending_result_state
                var:zg361_result_settlement_posted_serial = var:@P@_pending_result_settlement_receipt
                var:zg361_result_grade = 1
                has_variable = @P@_pending_hc_authorized_before
                has_variable = @P@_pending_hc_available_before
                has_variable = @P@_pending_hc_reserved_before
                has_variable = @P@_pending_hc_occupied_before
                has_variable = @P@_pending_hc_frozen_before
                has_variable = @P@_pending_hc_reclaimed_before
                has_variable = zg361_ch_hc_authorized
                has_variable = zg361_ch_hc_available
                has_variable = zg361_ch_hc_reserved
                has_variable = zg361_ch_hc_occupied
                has_variable = zg361_ch_hc_frozen
                has_variable = zg361_ch_hc_reclaimed
                has_variable = zg361_we_formal_hc_active
                has_variable = zg361_we_formal_hc_active_case
                var:@P@_pending_hc_authorized_before >= 1
                var:@P@_pending_hc_available_before >= 0
                var:@P@_pending_hc_reserved_before >= 0
                var:@P@_pending_hc_occupied_before >= 1
                var:@P@_pending_hc_frozen_before >= 0
                var:@P@_pending_hc_reclaimed_before >= 0
                var:@P@_pending_hc_authorized_before = {
                    value = var:@P@_pending_hc_available_before
                    add = var:@P@_pending_hc_reserved_before
                    add = var:@P@_pending_hc_occupied_before
                    add = var:@P@_pending_hc_frozen_before
                    add = var:@P@_pending_hc_reclaimed_before
                }
                var:zg361_ch_hc_authorized = var:@P@_pending_hc_authorized_before
                var:zg361_ch_hc_available = var:@P@_pending_hc_available_before
                var:zg361_ch_hc_reserved = var:@P@_pending_hc_reserved_before
                var:zg361_ch_hc_occupied = { value = var:@P@_pending_hc_occupied_before subtract = 1 }
                var:zg361_ch_hc_frozen = { value = var:@P@_pending_hc_frozen_before add = 1 }
                var:zg361_ch_hc_reclaimed = var:@P@_pending_hc_reclaimed_before
                var:zg361_ch_hc_authorized = {
                    value = var:zg361_ch_hc_available
                    add = var:zg361_ch_hc_reserved
                    add = var:zg361_ch_hc_occupied
                    add = var:zg361_ch_hc_frozen
                    add = var:zg361_ch_hc_reclaimed
                }
                var:zg361_we_formal_hc_active = 0
                var:zg361_we_formal_hc_active_case = var:@P@_pending_slot_case
                OR = { NOT = { has_variable = @P@_receipt_active } var:@P@_receipt_active = 0 }
            }
            if = {
                limit = { has_variable = @P@_subject_receipt_serial }
                save_temporary_scope_value_as = { name = @P@_next_receipt_serial value = { value = var:@P@_subject_receipt_serial add = 1 } }
            }
            else = { save_temporary_scope_value_as = { name = @P@_next_receipt_serial value = 1 } }
            set_variable = { name = @P@_receipt_active value = 1 }
            set_variable = { name = @P@_receipt_sealed value = 1 }
            set_variable = { name = @P@_receipt_published value = 1 }
            set_variable = { name = @P@_receipt_consumed value = 1 }
            set_variable = { name = @P@_receipt_consumed_operation value = @SOURCE_KIND@ }
            set_variable = { name = @P@_receipt_owner value = var:@P@_pending_owner }
            set_variable = { name = @P@_receipt_subject value = this }
            set_variable = { name = @P@_receipt_cycle value = var:@P@_pending_cycle }
            set_variable = { name = @P@_receipt_case value = var:@P@_pending_case }
            set_variable = { name = @P@_receipt_state value = 6 }
            set_variable = { name = @P@_receipt_id value = { value = var:@P@_pending_source_receipt_serial multiply = 100000 add = { value = scope:@P@_next_receipt_serial multiply = 10 } add = 5 } }
            set_variable = { name = @P@_receipt_hash value = { value = var:@P@_pending_result_hash multiply = 100000 add = { value = var:@P@_pending_appointment_receipt_hash multiply = 100 } add = { value = scope:@P@_next_receipt_serial multiply = 10 } add = 1 } }
            set_variable = { name = @P@_receipt_exit_source_kind value = @SOURCE_KIND@ }
            set_variable = { name = @P@_receipt_exit_source_state value = 3 }
            set_variable = { name = @P@_receipt_exit_class value = @EXIT_CLASS@ }
            set_variable = { name = @P@_receipt_exit_reason_code value = @EXIT_REASON@ }
            set_variable = { name = @P@_receipt_normal_exit_confirmed value = 1 }
            set_variable = { name = @P@_receipt_forced value = 0 }
            set_variable = { name = @P@_receipt_neutral_record value = 1 }
            set_variable = { name = @P@_receipt_actual_exit value = 1 }
            set_variable = { name = @P@_receipt_source_hc_release_claimed value = 1 }
            set_variable = { name = @P@_receipt_hc_ledger_settled value = 1 }
            set_variable = { name = @P@_receipt_hc_authorized_before value = var:@P@_pending_hc_authorized_before }
            set_variable = { name = @P@_receipt_hc_available_before value = var:@P@_pending_hc_available_before }
            set_variable = { name = @P@_receipt_hc_reserved_before value = var:@P@_pending_hc_reserved_before }
            set_variable = { name = @P@_receipt_hc_occupied_before value = var:@P@_pending_hc_occupied_before }
            set_variable = { name = @P@_receipt_hc_frozen_before value = var:@P@_pending_hc_frozen_before }
            set_variable = { name = @P@_receipt_hc_reclaimed_before value = var:@P@_pending_hc_reclaimed_before }
            set_variable = { name = @P@_receipt_hc_authorized_after value = var:zg361_ch_hc_authorized }
            set_variable = { name = @P@_receipt_hc_available_after value = var:zg361_ch_hc_available }
            set_variable = { name = @P@_receipt_hc_reserved_after value = var:zg361_ch_hc_reserved }
            set_variable = { name = @P@_receipt_hc_occupied_after value = var:zg361_ch_hc_occupied }
            set_variable = { name = @P@_receipt_hc_frozen_after value = var:zg361_ch_hc_frozen }
            set_variable = { name = @P@_receipt_hc_reclaimed_after value = var:zg361_ch_hc_reclaimed }
            set_variable = { name = @P@_receipt_hc_destination_frozen value = 1 }
            set_variable = { name = @P@_receipt_hc_conservation_verified value = 1 }
            set_variable = { name = @P@_receipt_formal_hc_active_before value = 1 }
            set_variable = { name = @P@_receipt_formal_hc_active_after value = 0 }
            set_variable = { name = @P@_receipt_formal_hc_case value = var:@P@_pending_slot_case }
            set_variable = { name = @P@_receipt_exit_year value = var:@P@_exit_observed_year }
            set_variable = { name = @P@_receipt_former_slot_id value = var:@P@_pending_slot_id }
            set_variable = { name = @P@_receipt_position_type_id value = var:@P@_pending_position_type_id }
            set_variable = { name = @P@_receipt_carrier_type_id value = var:@P@_pending_carrier_type_id }
            set_variable = { name = @P@_receipt_appointment_receipt_id value = var:@P@_pending_appointment_receipt_id }
            set_variable = { name = @P@_receipt_appointment_receipt_hash value = var:@P@_pending_appointment_receipt_hash }
            set_variable = { name = @P@_receipt_prior_result_owner value = var:@P@_pending_result_owner }
            set_variable = { name = @P@_receipt_prior_result_subject value = this }
            set_variable = { name = @P@_receipt_prior_result_cycle value = var:@P@_pending_result_cycle }
            set_variable = { name = @P@_receipt_prior_result_case value = var:@P@_pending_result_case }
            set_variable = { name = @P@_receipt_prior_result_state value = var:@P@_pending_result_state }
            set_variable = { name = @P@_receipt_prior_result_settlement_receipt value = var:@P@_pending_result_settlement_receipt }
            set_variable = { name = @P@_receipt_prior_result_grade value = 1 }
            set_variable = { name = @P@_receipt_prior_result_reason value = var:@P@_pending_result_reason }
            set_variable = { name = @P@_receipt_prior_result_kpi value = var:@P@_pending_result_kpi }
            set_variable = { name = @P@_receipt_prior_result_rank value = var:@P@_pending_result_rank }
            set_variable = { name = @P@_receipt_prior_result_delivered_year value = var:@P@_pending_result_delivered_year }
            set_variable = { name = @P@_receipt_prior_result_hash value = var:@P@_pending_result_hash }
            set_variable = { name = @P@_receipt_prior_pip_present value = var:@P@_pending_pip_present }
            if = {
                limit = { var:@P@_pending_pip_present = 1 }
                set_variable = { name = @P@_receipt_prior_pip_owner value = var:@P@_pending_pip_owner }
                set_variable = { name = @P@_receipt_prior_pip_subject value = this }
                set_variable = { name = @P@_receipt_prior_pip_cycle value = var:@P@_pending_pip_cycle }
                set_variable = { name = @P@_receipt_prior_pip_case value = var:@P@_pending_pip_case }
                set_variable = { name = @P@_receipt_prior_pip_state value = 3 }
                set_variable = { name = @P@_receipt_prior_pip_outcome_code value = 1 }
                set_variable = { name = @P@_receipt_prior_pip_result_grade value = var:@P@_pending_pip_result_grade }
                set_variable = { name = @P@_receipt_prior_pip_case_id value = var:@P@_pending_pip_case_id }
                set_variable = { name = @P@_receipt_prior_pip_case_hash value = var:@P@_pending_pip_case_hash }
                set_variable = { name = @P@_receipt_prior_pip_closure_receipt_id value = var:@P@_pending_pip_closure_receipt_id }
                set_variable = { name = @P@_receipt_prior_pip_closure_receipt_hash value = var:@P@_pending_pip_closure_receipt_hash }
            }
            set_variable = { name = @P@_receipt_displaced_hours value = var:@P@_pending_displaced_hours }
            set_variable = { name = @P@_receipt_displaced_cost_receipt value = var:@P@_pending_cost_receipt }
            set_variable = { name = @P@_receipt_displaced_cost_hash value = var:@P@_pending_cost_hash }
            set_variable = { name = @P@_receipt_displaced_cost_amount value = var:@P@_pending_cost_amount }
            set_variable = { name = @P@_receipt_native_end_reason value = 1 }
            set_variable = { name = @P@_receipt_native_callback_seen value = 1 }
            set_variable = { name = @P@_receipt_misconduct_present value = 0 }
            set_variable = { name = @P@_receipt_source_object_consumed value = 1 }
            set_variable = { name = @P@_receipt_source_receipt_serial value = var:@P@_pending_source_receipt_serial }
            set_variable = { name = @P@_subject_receipt_serial value = scope:@P@_next_receipt_serial }
            @P@_clear_pending_effect = yes
            set_variable = { name = @P@_state value = 4 }
            set_variable = { name = @P@_status value = 1 }
            trigger_event = { id = @N@.@CAPTURE@ days = 1 }
            if = { limit = { is_ai = no } trigger_event = { id = @N@.@NOTICE@ days = 1 } }
            debug_log = "ZG361WNEF: canonical funded #075 normal-exit receipt sealed after HC conservation audit"
        }
        else_if = {
            limit = {
                var:@P@_receipt_active = 1
                var:@P@_receipt_sealed = 1
                var:@P@_receipt_published = 1
                var:@P@_receipt_consumed = 1
                var:@P@_receipt_consumed_operation = @SOURCE_KIND@
                var:@P@_receipt_subject = this
                var:@P@_receipt_hc_ledger_settled = 1
                var:@P@_receipt_hc_conservation_verified = 1
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 27655 }
            debug_log = "ZG361WNEF RED 27655: post-migration HC partition failed D+1 conservation or lineage audit"
        }
    }
    '''
    replacements = {
        "P": PREFIX,
        "N": NAMESPACE,
        "S": EXIT_SLOT_PREFIX,
        "M": M075_PREFIX,
        "POSITION": EXIT_SLOT_POSITION,
        "POSITION_TYPE": str(M274_POSITION_TYPE_ID),
        "CARRIER_TYPE": str(CAREER_SLOT_TYPE_ID),
        "SOURCE_KIND": str(SOURCE_KIND_M075),
        "EXIT_CLASS": str(EXIT_CLASS_NORMAL),
        "EXIT_REASON": str(EXIT_REASON_VOLUNTARY_PACKAGE),
        "DISPATCH": str(DISPATCH_EVENT_ID),
        "AUDIT": str(AUDIT_EVENT_ID),
        "FINALIZE": str(FINALIZE_EVENT_ID),
        "HC_AUDIT": str(HC_AUDIT_EVENT_ID),
        "CAPTURE": str(CAPTURE_EVENT_ID),
        "NOTICE": str(NOTICE_EVENT_ID),
        "M075_HAS": _has(M075_PREFIX, M075_PRE_FIELDS, 16),
        "RESULT_HAS": _has("zg361_result", RESULT_FIELDS, 16),
    }
    template = clean(template)
    for key, value in replacements.items():
        template = template.replace(f"@{key}@", value)
    return generated(template)


def render_events() -> bytes:
    return generated(
        f'''
        namespace = {NAMESPACE}

        {NAMESPACE}.{DISPATCH_EVENT_ID} = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_pending
                var:{PREFIX}_pending = 1
                var:{PREFIX}_pending_subject = this
                var:{PREFIX}_request_authorized = 1
            }}
            immediate = {{ {PREFIX}_dispatch_native_revoke_effect = yes }}
        }}

        {NAMESPACE}.{AUDIT_EVENT_ID} = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_pending
                var:{PREFIX}_pending = 1
                var:{PREFIX}_pending_subject = this
                var:{PREFIX}_request_dispatched = 1
            }}
            immediate = {{ {PREFIX}_audit_native_then_accept_m075_effect = yes }}
        }}

        {NAMESPACE}.{FINALIZE_EVENT_ID} = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_pending
                var:{PREFIX}_pending = 1
                var:{PREFIX}_pending_subject = this
                var:{PREFIX}_state = 2
            }}
            immediate = {{ {PREFIX}_migrate_hc_partition_effect = yes }}
        }}

        {NAMESPACE}.{HC_AUDIT_EVENT_ID} = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_pending
                var:{PREFIX}_pending = 1
                var:{PREFIX}_pending_subject = this
                var:{PREFIX}_pending_hc_migration_authorized = 1
                var:{PREFIX}_state = 3
            }}
            immediate = {{ {PREFIX}_audit_hc_then_finalize_receipt_effect = yes }}
        }}

        {NAMESPACE}.{CAPTURE_EVENT_ID} = {{
            type = character_event
            hidden = yes
            trigger = {{
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_sealed = 1
                var:{PREFIX}_receipt_published = 1
                var:{PREFIX}_receipt_consumed = 1
                var:{PREFIX}_receipt_subject = this
            }}
            immediate = {{ {REHIRE_CAPTURE_EXIT_EFFECT} = yes }}
        }}

        {NAMESPACE}.{NOTICE_EVENT_ID} = {{
            type = character_event
            title = {NAMESPACE}.{NOTICE_EVENT_ID}.t
            desc = {NAMESPACE}.{NOTICE_EVENT_ID}.desc
            trigger = {{
                is_ai = no
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_sealed = 1
                var:{PREFIX}_receipt_consumed = 1
                var:{PREFIX}_receipt_subject = this
                var:{PREFIX}_receipt_exit_source_kind = {SOURCE_KIND_M075}
            }}
            option = {{
                name = {NAMESPACE}.{NOTICE_EVENT_ID}.a
                set_variable = {{ name = {PREFIX}_notice_seen value = 1 }}
            }}
        }}
        '''
    )


def localization_rows(language: str) -> list[str]:
    if language == "simp_chinese":
        title = "正常离职履历封存"
        desc = "旧 3.25、真实离职补偿与原生职业槽撤任均已落账。旧案不会因为离开公司就自动美颜。"
        option = "人走了，账还在。"
    else:
        title = "Normal-exit history sealed"
        desc = (
            "The old 3.25 result, funded exit package, and native career-slot revocation are now sealed. "
            "Leaving did not airbrush the old record."
        )
        option = "The employee left; the ledger did not."
    return [
        f"l_{language}:",
        f' {NAMESPACE}.{NOTICE_EVENT_ID}.t:0 "{title}"',
        f' {NAMESPACE}.{NOTICE_EVENT_ID}.desc:0 "{desc}"',
        f' {NAMESPACE}.{NOTICE_EVENT_ID}.a:0 "{option}"',
    ]


def render_localization(language: str) -> bytes:
    source = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered = {
        MOD_ROOT / "common/scripted_effects" / f"{PREFIX}_effects.txt": render_effects(),
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
            print("RED: stale Workforce normal-exit fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: Workforce normal-exit fact generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce normal-exit fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
