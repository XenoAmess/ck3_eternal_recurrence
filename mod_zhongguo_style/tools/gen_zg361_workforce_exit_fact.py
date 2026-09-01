#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the independent real Workforce #277 native-exit fact package.

The #274 appointment position is intentionally bounded and is revoked as soon
as #274 consumes its native appointment receipt.  It therefore cannot witness
a later PIP exit.  This package joins that immutable #274 receipt, appoints a
separate zero-salary native career-slot carrier, keeps it alive through the
probation/PIP lifecycle, and seals #277 only after a new native revoke callback
and a later no-longer-holder postcondition.

The public ABI accepts only the case tuple.  Success bits, receipt IDs, hashes,
former-slot IDs, displaced hours, and cost provenance are all derived from
live package/core state rather than caller parameters.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE -- edit tools/gen_zg361_workforce_exit_fact.py\n"

PREFIX: Final[str] = "zg361_workforce_exit_fact"
NAMESPACE: Final[str] = "zg361workforceexitfact"
POSITION_KEY: Final[str] = f"{PREFIX}_career_slot_court_position"
POSITION_CARRIER_TYPE_ID: Final[int] = 3_612_771
M274_POSITION_KEY: Final[str] = "zg361_workforce_appointment_fact_court_position"
M274_POSITION_TYPE_ID: Final[int] = 3_612_741
REASON_KIND_PIP: Final[int] = 1
READINESS: Final[str] = "ck3-script-static-ready-not-live"

ARM_DISPATCH_EVENT_ID: Final[int] = 9000
ARM_AUDIT_EVENT_ID: Final[int] = 9001
EXIT_DISPATCH_EVENT_ID: Final[int] = 9002
EXIT_AUDIT_EVENT_ID: Final[int] = 9003
PUBLISH_EVENT_ID: Final[int] = 9004
PUBLISH_VERIFY_EVENT_ID: Final[int] = 9005
CLEANUP_REVOKE_EVENT_ID: Final[int] = 9006
ROLE_FAILURE_PUBLISH_EVENT_ID: Final[int] = 9007
ROLE_FAILURE_VERIFY_EVENT_ID: Final[int] = 9008
PROBATION_ROLE_FAILURE_EFFECT: Final[str] = (
    "zg361_workforce_probation_fact_publish_from_role_failure_effect"
)
ROLE_FAILURE_REASON_KIND: Final[int] = 1
ROLE_FAILURE_EXCLUSION_REASON: Final[int] = 1

EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / f"{PREFIX}_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / f"{PREFIX}_events.txt"
POSITION_PATH = (
    MOD_ROOT
    / "common"
    / "court_positions"
    / "types"
    / f"{PREFIX}_court_positions.txt"
)
SPEC_PATH = MOD_ROOT / "docs" / f"{PREFIX}_runtime_spec.md"
LOC_BASENAME = f"{PREFIX}_l_{{language}}.yml"

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


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def render_court_position() -> bytes:
    return generated(
        f"""
# A real, persistent native carrier for the formal-HC career slot.  The
# bounded #274 appointment carrier has already been package-revoked before
# this position is armed; the two lifecycles must never be conflated.
{POSITION_KEY} = {{
    sort_order = 362
    max_available_positions = 100
    minimum_rank = duchy
    skill = stewardship

    opinion = {{ value = 0 }}
    aptitude_level_breakpoints = {{ 20 40 60 80 }}
    aptitude = {{ value = stewardship }}

    is_shown = {{
        has_variable = {PREFIX}_window_open
        var:{PREFIX}_window_open = 1
        government_has_flag = government_is_celestial
        highest_held_title_tier >= tier_duchy
    }}

    valid_position = {{
        government_has_flag = government_is_celestial
        highest_held_title_tier >= tier_duchy
    }}

    is_shown_character = {{
        scope:employee = {{
            is_alive = yes
            is_landed = yes
            liege = scope:liege
            has_variable = {PREFIX}_arm_pending
            var:{PREFIX}_arm_pending = 1
            var:{PREFIX}_arm_owner = scope:liege
            var:{PREFIX}_arm_subject = this
        }}
    }}

    valid_character = {{
        scope:employee = {{
            is_alive = yes
            is_landed = yes
            liege = scope:liege
            OR = {{
                AND = {{
                    has_variable = {PREFIX}_arm_pending
                    var:{PREFIX}_arm_pending = 1
                    var:{PREFIX}_arm_owner = scope:liege
                    var:{PREFIX}_arm_subject = this
                }}
                AND = {{
                    has_variable = {PREFIX}_slot_active
                    var:{PREFIX}_slot_active = 1
                    var:{PREFIX}_slot_owner = scope:liege
                    var:{PREFIX}_slot_subject = this
                }}
            }}
        }}
    }}

    revoke_cost = {{}}
    salary = {{ gold = 0 }}
    received_salary = {{ gold = 0 }}

    on_court_position_received = {{
        scope:employee = {{
            {PREFIX}_on_native_slot_received_effect = yes
        }}
    }}
    on_court_position_revoked = {{
        scope:employee = {{
            {PREFIX}_on_native_slot_ended_effect = {{ END_REASON = 1 }}
        }}
    }}
    on_court_position_invalidated = {{
        scope:employee = {{
            {PREFIX}_on_native_slot_ended_effect = {{ END_REASON = 2 }}
        }}
    }}
    on_court_position_vacated = {{
        scope:employee = {{
            {PREFIX}_on_native_slot_ended_effect = {{ END_REASON = 3 }}
        }}
    }}

    ai_position_score = {{ value = -1000 }}
    ai_candidate_score = {{ value = -1000 }}
}}
"""
    )


def render_effects() -> bytes:
    return generated(
        f"""
# Public subject-scope ABI.  All four effects accept only the exact Workforce
# tuple.  In particular, no public caller supplies a success bit, any receipt
# ID/hash, former-slot ID, displaced hours, or cost provenance.

{PREFIX}_clear_arm_pending_effect = {{
    remove_variable = {PREFIX}_arm_pending
    remove_variable = {PREFIX}_arm_owner
    remove_variable = {PREFIX}_arm_subject
    remove_variable = {PREFIX}_arm_cycle
    remove_variable = {PREFIX}_arm_case
    remove_variable = {PREFIX}_arm_state
    remove_variable = {PREFIX}_arm_m274_position_type_id
    remove_variable = {PREFIX}_arm_m274_receipt_id
    remove_variable = {PREFIX}_arm_m274_receipt_hash
    remove_variable = {PREFIX}_arm_request_authorized
    remove_variable = {PREFIX}_arm_request_dispatched
}}

{PREFIX}_clear_exit_pending_effect = {{
    remove_variable = {PREFIX}_exit_pending
    remove_variable = {PREFIX}_exit_owner
    remove_variable = {PREFIX}_exit_subject
    remove_variable = {PREFIX}_exit_cycle
    remove_variable = {PREFIX}_exit_case
    remove_variable = {PREFIX}_exit_state
    remove_variable = {PREFIX}_exit_slot_was_active
    remove_variable = {PREFIX}_exit_former_slot_id
    remove_variable = {PREFIX}_exit_former_slot_hash
    remove_variable = {PREFIX}_exit_position_type_id
    remove_variable = {PREFIX}_exit_carrier_type_id
    remove_variable = {PREFIX}_exit_appointment_receipt_id
    remove_variable = {PREFIX}_exit_appointment_receipt_hash
    remove_variable = {PREFIX}_exit_pip_cycle
    remove_variable = {PREFIX}_exit_pip_case
    remove_variable = {PREFIX}_exit_pip_state
    remove_variable = {PREFIX}_exit_pip_case_id
    remove_variable = {PREFIX}_exit_pip_case_hash
    remove_variable = {PREFIX}_exit_pip_closure_receipt_id
    remove_variable = {PREFIX}_exit_pip_closure_receipt_hash
    remove_variable = {PREFIX}_exit_pip_outcome_code
    remove_variable = {PREFIX}_exit_pip_result_grade
    remove_variable = {PREFIX}_exit_displaced_hours
    remove_variable = {PREFIX}_exit_displaced_cost_amount
    remove_variable = {PREFIX}_exit_displaced_cost_receipt
    remove_variable = {PREFIX}_exit_displaced_cost_hash
    remove_variable = {PREFIX}_exit_hc_occupied_before
    remove_variable = {PREFIX}_exit_hc_frozen_before
    remove_variable = {PREFIX}_exit_request_authorized
    remove_variable = {PREFIX}_exit_request_dispatched
}}

{PREFIX}_clear_role_failure_receipt_effect = {{
    remove_variable = {PREFIX}_role_failure_receipt_active
    remove_variable = {PREFIX}_role_failure_receipt_sealed
    remove_variable = {PREFIX}_role_failure_receipt_published
    remove_variable = {PREFIX}_role_failure_receipt_consumed
    remove_variable = {PREFIX}_role_failure_receipt_owner
    remove_variable = {PREFIX}_role_failure_receipt_subject
    remove_variable = {PREFIX}_role_failure_receipt_hire_cycle
    remove_variable = {PREFIX}_role_failure_receipt_hire_case
    remove_variable = {PREFIX}_role_failure_receipt_state
    remove_variable = {PREFIX}_role_failure_receipt_id
    remove_variable = {PREFIX}_role_failure_receipt_hash
    remove_variable = {PREFIX}_role_failure_receipt_reason_kind
    remove_variable = {PREFIX}_role_failure_receipt_exclusion_reason
    remove_variable = {PREFIX}_role_failure_receipt_former_slot_id
    remove_variable = {PREFIX}_role_failure_receipt_former_slot_hash
    remove_variable = {PREFIX}_role_failure_receipt_position_type_id
    remove_variable = {PREFIX}_role_failure_receipt_carrier_type_id
    remove_variable = {PREFIX}_role_failure_receipt_appointment_receipt_id
    remove_variable = {PREFIX}_role_failure_receipt_appointment_receipt_hash
    remove_variable = {PREFIX}_role_failure_receipt_native_end_reason
    remove_variable = {PREFIX}_role_failure_receipt_observed_cycle
    remove_variable = {PREFIX}_role_failure_receipt_formal_hc_active
    remove_variable = {PREFIX}_role_failure_receipt_hc_authorized
    remove_variable = {PREFIX}_role_failure_receipt_hc_available
    remove_variable = {PREFIX}_role_failure_receipt_hc_reserved
    remove_variable = {PREFIX}_role_failure_receipt_hc_occupied
    remove_variable = {PREFIX}_role_failure_receipt_hc_frozen
    remove_variable = {PREFIX}_role_failure_receipt_hc_reclaimed
    remove_variable = {PREFIX}_role_failure_receipt_hc_conservation_verified
}}

# A natural native invalidation is not a PIP exit.  When it ends the exact
# long-lived slot of a still-active 3.25 probation tuple, however, it is the
# real role/strategy-change exclusion source for canonical #269 quality=4.
# This capture runs before slot_active is cleared by the callback.
{PREFIX}_capture_role_failure_effect = {{
    remove_variable = {PREFIX}_role_failure_status
    if = {{
        limit = {{
            has_variable = {PREFIX}_role_failure_receipt_active
            has_variable = {PREFIX}_role_failure_receipt_sealed
            has_variable = {PREFIX}_role_failure_receipt_former_slot_id
            has_variable = {PREFIX}_role_failure_receipt_former_slot_hash
            var:{PREFIX}_role_failure_receipt_active = 1
            var:{PREFIX}_role_failure_receipt_sealed = 1
            var:{PREFIX}_role_failure_receipt_owner = scope:liege
            var:{PREFIX}_role_failure_receipt_subject = this
            var:{PREFIX}_role_failure_receipt_former_slot_id = var:{PREFIX}_slot_id
            var:{PREFIX}_role_failure_receipt_former_slot_hash = var:{PREFIX}_slot_hash
            var:{PREFIX}_role_failure_receipt_native_end_reason = 2
        }}
        set_variable = {{ name = {PREFIX}_role_failure_status value = 2 }}
    }}
    else_if = {{
        limit = {{
            is_alive = yes
            has_variable = {PREFIX}_slot_active
            has_variable = {PREFIX}_slot_owner
            has_variable = {PREFIX}_slot_subject
            has_variable = {PREFIX}_slot_cycle
            has_variable = {PREFIX}_slot_case
            has_variable = {PREFIX}_slot_state
            has_variable = {PREFIX}_slot_position_type_id
            has_variable = {PREFIX}_slot_carrier_type_id
            has_variable = {PREFIX}_slot_appointment_receipt_id
            has_variable = {PREFIX}_slot_appointment_receipt_hash
            has_variable = {PREFIX}_slot_id
            has_variable = {PREFIX}_slot_hash
            var:{PREFIX}_slot_active = 1
            var:{PREFIX}_slot_owner = scope:liege
            var:{PREFIX}_slot_subject = this
            var:{PREFIX}_slot_cycle > 0
            var:{PREFIX}_slot_case > 0
            var:{PREFIX}_slot_state = 4
            var:{PREFIX}_slot_position_type_id = {M274_POSITION_TYPE_ID}
            var:{PREFIX}_slot_carrier_type_id = {POSITION_CARRIER_TYPE_ID}
            var:{PREFIX}_slot_appointment_receipt_id > 0
            var:{PREFIX}_slot_appointment_receipt_hash > 0
            var:{PREFIX}_slot_id > 0
            var:{PREFIX}_slot_hash > 0
            scope:liege = {{
                is_alive = yes
                is_landed = yes
                zg361_is_celestial_liege_trigger = yes
                has_variable = zg361_review_serial
                var:zg361_review_serial > root.var:{PREFIX}_slot_cycle
            }}
            has_variable = zg361_workforce_probation_fact_state
            has_variable = zg361_workforce_probation_fact_awaiting_pip
            has_variable = zg361_workforce_probation_fact_owner
            has_variable = zg361_workforce_probation_fact_subject
            has_variable = zg361_workforce_probation_fact_hire_cycle
            has_variable = zg361_workforce_probation_fact_hire_case
            has_variable = zg361_workforce_probation_fact_position_receipt_id
            has_variable = zg361_workforce_probation_fact_position_receipt_hash
            var:zg361_workforce_probation_fact_state = 2
            var:zg361_workforce_probation_fact_awaiting_pip = 1
            var:zg361_workforce_probation_fact_owner = scope:liege
            var:zg361_workforce_probation_fact_subject = this
            var:zg361_workforce_probation_fact_hire_cycle = var:{PREFIX}_slot_cycle
            var:zg361_workforce_probation_fact_hire_case = var:{PREFIX}_slot_case
            var:zg361_workforce_probation_fact_position_receipt_id = var:{PREFIX}_slot_appointment_receipt_id
            var:zg361_workforce_probation_fact_position_receipt_hash = var:{PREFIX}_slot_appointment_receipt_hash
            has_variable = zg361_we_m274_hired
            has_variable = zg361_we_m274_hire_case
            has_variable = zg361_we_m274_position_receipt_id
            has_variable = zg361_we_m274_position_receipt_hash
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_hire_case = var:{PREFIX}_slot_case
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_slot_appointment_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_slot_appointment_receipt_hash
            has_variable = zg361_we_m269_outcome_pending
            has_variable = zg361_we_m269_outcome_settled
            var:zg361_we_m269_outcome_pending = 1
            var:zg361_we_m269_outcome_settled = 0
            var:zg361_we_m269_write_owner = scope:liege
            var:zg361_we_m269_write_subject = this
            var:zg361_we_m269_write_cycle = var:{PREFIX}_slot_cycle
            var:zg361_we_m269_write_case = var:{PREFIX}_slot_case
            var:zg361_we_m269_write_state = 5
            has_variable = zg361_we_formal_hc_active
            has_variable = zg361_we_formal_hc_active_case
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_slot_case
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
            AND = {{
                var:zg361_ch_hc_authorized >= {{
                    value = var:zg361_ch_hc_available
                    add = var:zg361_ch_hc_reserved
                    add = var:zg361_ch_hc_occupied
                    add = var:zg361_ch_hc_frozen
                    add = var:zg361_ch_hc_reclaimed
                }}
                var:zg361_ch_hc_authorized <= {{
                    value = var:zg361_ch_hc_available
                    add = var:zg361_ch_hc_reserved
                    add = var:zg361_ch_hc_occupied
                    add = var:zg361_ch_hc_frozen
                    add = var:zg361_ch_hc_reclaimed
                }}
            }}
            OR = {{ NOT = {{ has_variable = {PREFIX}_exit_pending }} var:{PREFIX}_exit_pending = 0 }}
            OR = {{ NOT = {{ has_variable = zg361_workforce_normal_exit_fact_pending }} var:zg361_workforce_normal_exit_fact_pending = 0 }}
            OR = {{ NOT = {{ has_variable = {PREFIX}_cleanup_revoke_requested }} var:{PREFIX}_cleanup_revoke_requested = 0 }}
            OR = {{
                NOT = {{ has_variable = {PREFIX}_role_failure_receipt_active }}
                AND = {{
                    var:{PREFIX}_role_failure_receipt_active = 1
                    var:{PREFIX}_role_failure_receipt_sealed = 1
                    var:{PREFIX}_role_failure_receipt_consumed = 1
                }}
            }}
        }}
        {PREFIX}_clear_role_failure_receipt_effect = yes
        set_variable = {{ name = {PREFIX}_role_failure_receipt_active value = 1 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_published value = 0 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_consumed value = 0 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_subject value = this }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hire_cycle value = var:{PREFIX}_slot_cycle }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hire_case value = var:{PREFIX}_slot_case }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_state value = 4 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_id value = {{ value = var:{PREFIX}_slot_id multiply = 10 add = 2 }} }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hash value = {{ value = var:{PREFIX}_slot_hash multiply = 100000 add = {{ value = var:{PREFIX}_slot_appointment_receipt_hash multiply = 10 }} add = 2 }} }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_reason_kind value = {ROLE_FAILURE_REASON_KIND} }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_exclusion_reason value = {ROLE_FAILURE_EXCLUSION_REASON} }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_former_slot_id value = var:{PREFIX}_slot_id }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_former_slot_hash value = var:{PREFIX}_slot_hash }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_position_type_id value = var:{PREFIX}_slot_position_type_id }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_carrier_type_id value = var:{PREFIX}_slot_carrier_type_id }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_appointment_receipt_id value = var:{PREFIX}_slot_appointment_receipt_id }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_appointment_receipt_hash value = var:{PREFIX}_slot_appointment_receipt_hash }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_native_end_reason value = 2 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_observed_cycle value = scope:liege.var:zg361_review_serial }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_formal_hc_active value = 1 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_authorized value = var:zg361_ch_hc_authorized }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_available value = var:zg361_ch_hc_available }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_reserved value = var:zg361_ch_hc_reserved }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_occupied value = var:zg361_ch_hc_occupied }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_frozen value = var:zg361_ch_hc_frozen }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_reclaimed value = var:zg361_ch_hc_reclaimed }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_hc_conservation_verified value = 1 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_sealed value = 1 }} # commit last
        set_variable = {{ name = {PREFIX}_role_failure_status value = 1 }}
        trigger_event = {{ id = {NAMESPACE}.{ROLE_FAILURE_PUBLISH_EVENT_ID} days = 1 }}
        debug_log = "ZG361WEF: exact native invalidation sealed as role/strategy exclusion source"
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_role_failure_status value = 5 }}
        set_variable = {{ name = {PREFIX}_role_failure_collision value = 1 }}
    }}
}}

{PREFIX}_verify_role_failure_publish_effect = {{
    if = {{
        limit = {{
            var:{PREFIX}_role_failure_receipt_active = 1
            var:{PREFIX}_role_failure_receipt_sealed = 1
            var:{PREFIX}_role_failure_receipt_consumed = 0
            var:{PREFIX}_role_failure_receipt_subject = this
            var:zg361_workforce_probation_fact_state >= 3
            var:zg361_workforce_probation_fact_published = 1
            var:zg361_workforce_probation_fact_subject = this
            var:zg361_workforce_probation_fact_source_kind = 4
            var:zg361_workforce_probation_fact_outcome_quality = 4
            var:zg361_workforce_probation_fact_outcome_exclusion_reason = {ROLE_FAILURE_EXCLUSION_REASON}
            var:zg361_workforce_probation_fact_source_external_owner = var:{PREFIX}_role_failure_receipt_owner
            var:zg361_workforce_probation_fact_source_external_subject = this
            var:zg361_workforce_probation_fact_source_external_cycle = var:{PREFIX}_role_failure_receipt_observed_cycle
            var:zg361_workforce_probation_fact_source_external_case = var:{PREFIX}_role_failure_receipt_hire_case
            var:zg361_workforce_probation_fact_source_external_receipt_id = var:{PREFIX}_role_failure_receipt_id
            var:zg361_workforce_probation_fact_source_external_receipt_hash = var:{PREFIX}_role_failure_receipt_hash
        }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_published value = 1 }}
        set_variable = {{ name = {PREFIX}_role_failure_receipt_consumed value = 1 }}
        set_variable = {{ name = {PREFIX}_role_failure_status value = 4 }}
    }}
    else_if = {{
        limit = {{
            var:{PREFIX}_role_failure_receipt_active = 1
            var:{PREFIX}_role_failure_receipt_sealed = 1
            var:{PREFIX}_role_failure_receipt_published = 1
            var:{PREFIX}_role_failure_receipt_consumed = 1
            var:{PREFIX}_role_failure_receipt_subject = this
        }}
        set_variable = {{ name = {PREFIX}_role_failure_status value = 2 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_role_failure_status value = 5 }}
        set_variable = {{ name = {PREFIX}_role_failure_publish_red value = 1 }}
    }}
}}

# Native receive callback for the long-lived career carrier.  It records only
# callback observation; the already-authorized dispatch schedules the later
# postcondition audit, so a missing callback becomes an explicit audit RED
# instead of leaving the request pending forever.
{PREFIX}_on_native_slot_received_effect = {{
    if = {{
        limit = {{
            has_variable = {PREFIX}_arm_pending
            var:{PREFIX}_arm_pending = 1
            var:{PREFIX}_arm_subject = this
            var:{PREFIX}_arm_owner = scope:liege
            has_variable = {PREFIX}_arm_request_authorized
            var:{PREFIX}_arm_request_authorized = 1
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = scope:liege
            }}
        }}
        set_variable = {{ name = {PREFIX}_native_receive_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_receive_callback_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_receive_callback_subject value = this }}
    }}
}}

# All native end modes are observed.  Only a newly requested revoke
# (END_REASON=1) can later seal a PIP-exit receipt.  Invalidation/vacating and
# package cleanup remain visible RED facts and can never masquerade as #277.
{PREFIX}_on_native_slot_ended_effect = {{
    if = {{
        limit = {{ $END_REASON$ = 2 }}
        {PREFIX}_capture_role_failure_effect = yes
    }}
    set_variable = {{ name = {PREFIX}_slot_active value = 0 }}
    set_variable = {{ name = {PREFIX}_native_last_end_reason value = $END_REASON$ }}
    set_variable = {{ name = {PREFIX}_native_last_end_owner value = scope:liege }}
    set_variable = {{ name = {PREFIX}_native_last_end_subject value = this }}
    if = {{
        limit = {{ $END_REASON$ = 1 }}
        set_variable = {{ name = {PREFIX}_native_revoked_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_revoked_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_revoked_subject value = this }}
    }}
    else_if = {{
        limit = {{ $END_REASON$ = 2 }}
        set_variable = {{ name = {PREFIX}_native_invalidated_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_invalidated_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_invalidated_subject value = this }}
    }}
    else_if = {{
        limit = {{ $END_REASON$ = 3 }}
        set_variable = {{ name = {PREFIX}_native_vacated_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_vacated_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_vacated_subject value = this }}
    }}
    if = {{
        limit = {{
            has_variable = {PREFIX}_exit_pending
            var:{PREFIX}_exit_pending = 1
            var:{PREFIX}_exit_subject = this
            var:{PREFIX}_exit_owner = scope:liege
            has_variable = {PREFIX}_exit_request_authorized
            var:{PREFIX}_exit_request_authorized = 1
            $END_REASON$ = 1
        }}
        set_variable = {{ name = {PREFIX}_native_exit_revoked_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_exit_revoked_callback_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_exit_revoked_callback_subject value = this }}
    }}
    else_if = {{
        limit = {{
            has_variable = zg361_workforce_normal_exit_fact_pending
            var:zg361_workforce_normal_exit_fact_pending = 1
            var:zg361_workforce_normal_exit_fact_pending_subject = this
            var:zg361_workforce_normal_exit_fact_pending_owner = scope:liege
            has_variable = zg361_workforce_normal_exit_fact_request_authorized
            has_variable = zg361_workforce_normal_exit_fact_request_dispatched
            var:zg361_workforce_normal_exit_fact_request_authorized = 1
            var:zg361_workforce_normal_exit_fact_request_dispatched = 1
            $END_REASON$ = 1
        }}
        set_variable = {{ name = zg361_workforce_normal_exit_fact_native_revoke_callback_seen value = 1 }}
        set_variable = {{ name = zg361_workforce_normal_exit_fact_native_revoke_callback_owner value = scope:liege }}
        set_variable = {{ name = zg361_workforce_normal_exit_fact_native_revoke_callback_subject value = this }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_cleanup_revoke_requested
            var:{PREFIX}_cleanup_revoke_requested = 1
        }}
        set_variable = {{ name = {PREFIX}_cleanup_revoke_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_cleanup_revoke_callback_reason value = $END_REASON$ }}
        remove_variable = {PREFIX}_cleanup_revoke_requested
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_unexpected_native_end_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_unexpected_native_end_reason value = $END_REASON$ }}
    }}
}}

# Arm a persistent native career slot only after the exact #274 native
# appointment receipt has been consumed and its bounded carrier has really
# been package-revoked.  This public entry accepts no truth material.
{PREFIX}_arm_from_m274_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_slot_active
            var:{PREFIX}_slot_active = 1
            var:{PREFIX}_slot_owner = $TICKET_OWNER$
            var:{PREFIX}_slot_subject = $TICKET_SUBJECT$
            var:{PREFIX}_slot_cycle = $TICKET_CYCLE$
            var:{PREFIX}_slot_case = $TICKET_CASE$
            var:{PREFIX}_slot_state = 4
            $TICKET_SUBJECT$ = {{
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = $TICKET_OWNER$
                }}
            }}
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else_if = {{
        limit = {{
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
            $TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
            $TICKET_SUBJECT$ = this
            is_alive = yes
            is_landed = yes
            liege = $TICKET_OWNER$
            has_variable = zg361_we_m274_business_object_created
            var:zg361_we_m274_business_object_created = 1
            var:zg361_we_m274_object_owner = $TICKET_OWNER$
            var:zg361_we_m274_object_subject = $TICKET_SUBJECT$
            var:zg361_we_m274_object_cycle = $TICKET_CYCLE$
            var:zg361_we_m274_object_case = $TICKET_CASE$
            var:zg361_we_m274_object_state = 4
            var:zg361_we_m274_object_consumed = 1
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_hire_case = $TICKET_CASE$
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_appointed_character = $TICKET_SUBJECT$
            var:zg361_we_m274_position_type_id = {M274_POSITION_TYPE_ID}
            var:zg361_we_m274_position_receipt_id > 0
            var:zg361_we_m274_position_receipt_hash > 0
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = $TICKET_CASE$
            var:zg361_ch_hc_occupied >= 1
            has_variable = zg361_workforce_appointment_fact_receipt_active
            var:zg361_workforce_appointment_fact_receipt_active = 1
            var:zg361_workforce_appointment_fact_receipt_consumed = 1
            var:zg361_workforce_appointment_fact_receipt_consumed_operation = 274
            var:zg361_workforce_appointment_fact_receipt_owner = $TICKET_OWNER$
            var:zg361_workforce_appointment_fact_receipt_subject = $TICKET_SUBJECT$
            var:zg361_workforce_appointment_fact_receipt_cycle = $TICKET_CYCLE$
            var:zg361_workforce_appointment_fact_receipt_case = $TICKET_CASE$
            var:zg361_workforce_appointment_fact_receipt_state = 4
            var:zg361_workforce_appointment_fact_receipt_result = 1
            var:zg361_workforce_appointment_fact_receipt_position_type_id = {M274_POSITION_TYPE_ID}
            var:zg361_workforce_appointment_fact_receipt_id = var:zg361_we_m274_position_receipt_id
            var:zg361_workforce_appointment_fact_receipt_hash = var:zg361_we_m274_position_receipt_hash
            var:zg361_workforce_appointment_fact_receipt_native_callback_seen = 1
            var:zg361_workforce_appointment_fact_receipt_position_still_active = 0
            var:zg361_workforce_appointment_fact_receipt_position_released_by_package = 1
            var:zg361_workforce_appointment_fact_receipt_position_release_joined_by_consumer = 1
            NOT = {{ has_court_position = {M274_POSITION_KEY} }}
            OR = {{
                NOT = {{ has_variable = {PREFIX}_arm_pending }}
                var:{PREFIX}_arm_pending = 0
            }}
            OR = {{
                NOT = {{ has_variable = {PREFIX}_slot_active }}
                var:{PREFIX}_slot_active = 0
            }}
        }}
        set_variable = {{ name = {PREFIX}_arm_pending value = 1 }}
        set_variable = {{ name = {PREFIX}_arm_owner value = $TICKET_OWNER$ }}
        set_variable = {{ name = {PREFIX}_arm_subject value = $TICKET_SUBJECT$ }}
        set_variable = {{ name = {PREFIX}_arm_cycle value = $TICKET_CYCLE$ }}
        set_variable = {{ name = {PREFIX}_arm_case value = $TICKET_CASE$ }}
        set_variable = {{ name = {PREFIX}_arm_state value = 4 }}
        set_variable = {{ name = {PREFIX}_arm_m274_position_type_id value = var:zg361_we_m274_position_type_id }}
        set_variable = {{ name = {PREFIX}_arm_m274_receipt_id value = var:zg361_we_m274_position_receipt_id }}
        set_variable = {{ name = {PREFIX}_arm_m274_receipt_hash value = var:zg361_we_m274_position_receipt_hash }}
        remove_variable = {PREFIX}_native_receive_callback_seen
        remove_variable = {PREFIX}_native_receive_callback_owner
        remove_variable = {PREFIX}_native_receive_callback_subject
        remove_variable = {PREFIX}_cleanup_revoke_requested
        remove_variable = {PREFIX}_cleanup_revoke_callback_seen
        remove_variable = {PREFIX}_cleanup_revoke_callback_reason
        set_variable = {{ name = {PREFIX}_arm_request_authorized value = 1 }}
        $TICKET_OWNER$ = {{ set_variable = {{ name = {PREFIX}_window_open value = 1 }} }}
        trigger_event = {{ id = {NAMESPACE}.{ARM_DISPATCH_EVENT_ID} days = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27701 }}
    }}
}}

# D+1 native appointment dispatch.  The intent, authorization, and owner-side
# picker flag were committed by the public entry on the prior event boundary,
# so both can_appoint and the native receive callback read stable state.
{PREFIX}_dispatch_native_arm_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_arm_pending
            var:{PREFIX}_arm_pending = 1
            var:{PREFIX}_arm_subject = this
            var:{PREFIX}_arm_state = 4
            has_variable = {PREFIX}_arm_request_authorized
            var:{PREFIX}_arm_request_authorized = 1
            var:{PREFIX}_arm_owner = {{
                zg361_is_celestial_liege_trigger = yes
                has_variable = {PREFIX}_window_open
                var:{PREFIX}_window_open = 1
                can_appoint_char_to_court_position = {{
                    CHAR = root
                    COURT_POS = {POSITION_KEY}
                }}
            }}
            is_alive = yes
            is_landed = yes
            liege = var:{PREFIX}_arm_owner
            var:zg361_we_m274_business_object_created = 1
            var:zg361_we_m274_object_owner = var:{PREFIX}_arm_owner
            var:zg361_we_m274_object_subject = this
            var:zg361_we_m274_object_cycle = var:{PREFIX}_arm_cycle
            var:zg361_we_m274_object_case = var:{PREFIX}_arm_case
            var:zg361_we_m274_object_consumed = 1
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_position_type_id = var:{PREFIX}_arm_m274_position_type_id
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_arm_m274_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_arm_m274_receipt_hash
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_arm_case
            var:zg361_ch_hc_occupied >= 1
            NOT = {{ has_court_position = {M274_POSITION_KEY} }}
            NOT = {{ has_court_position = {POSITION_KEY} }}
        }}
        set_variable = {{ name = {PREFIX}_arm_request_dispatched value = 1 }}
        var:{PREFIX}_arm_owner = {{
            appoint_court_position = {{
                recipient = root
                court_position = {POSITION_KEY}
            }}
            remove_variable = {PREFIX}_window_open
        }}
        trigger_event = {{ id = {NAMESPACE}.{ARM_AUDIT_EVENT_ID} days = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
    }}
    else = {{
        if = {{
            limit = {{ has_variable = {PREFIX}_arm_owner }}
            var:{PREFIX}_arm_owner = {{ remove_variable = {PREFIX}_window_open }}
        }}
        {PREFIX}_clear_arm_pending_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27702 }}
    }}
}}

# D+1 arm audit.  No same-effect read-after-write is used to turn the native
# appointment request into a slot fact.
{PREFIX}_audit_arm_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_arm_pending
            var:{PREFIX}_arm_pending = 1
            var:{PREFIX}_arm_subject = this
            var:{PREFIX}_arm_state = 4
            var:{PREFIX}_arm_request_authorized = 1
            var:{PREFIX}_arm_request_dispatched = 1
            var:{PREFIX}_native_receive_callback_seen = 1
            var:{PREFIX}_native_receive_callback_owner = var:{PREFIX}_arm_owner
            var:{PREFIX}_native_receive_callback_subject = this
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = var:{PREFIX}_arm_owner
            }}
            var:zg361_we_m274_business_object_created = 1
            var:zg361_we_m274_object_owner = var:{PREFIX}_arm_owner
            var:zg361_we_m274_object_subject = this
            var:zg361_we_m274_object_cycle = var:{PREFIX}_arm_cycle
            var:zg361_we_m274_object_case = var:{PREFIX}_arm_case
            var:zg361_we_m274_object_consumed = 1
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_position_type_id = var:{PREFIX}_arm_m274_position_type_id
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_arm_m274_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_arm_m274_receipt_hash
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_arm_case
            var:zg361_ch_hc_occupied >= 1
            var:zg361_workforce_appointment_fact_receipt_consumed = 1
            var:zg361_workforce_appointment_fact_receipt_position_still_active = 0
            var:zg361_workforce_appointment_fact_receipt_position_released_by_package = 1
            var:zg361_workforce_appointment_fact_receipt_position_release_joined_by_consumer = 1
            NOT = {{ has_court_position = {M274_POSITION_KEY} }}
        }}
        set_variable = {{ name = {PREFIX}_slot_active value = 1 }}
        set_variable = {{ name = {PREFIX}_slot_owner value = var:{PREFIX}_arm_owner }}
        set_variable = {{ name = {PREFIX}_slot_subject value = this }}
        set_variable = {{ name = {PREFIX}_slot_cycle value = var:{PREFIX}_arm_cycle }}
        set_variable = {{ name = {PREFIX}_slot_case value = var:{PREFIX}_arm_case }}
        set_variable = {{ name = {PREFIX}_slot_state value = 4 }}
        set_variable = {{ name = {PREFIX}_slot_position_type_id value = var:{PREFIX}_arm_m274_position_type_id }}
        set_variable = {{ name = {PREFIX}_slot_appointment_receipt_id value = var:{PREFIX}_arm_m274_receipt_id }}
        set_variable = {{ name = {PREFIX}_slot_appointment_receipt_hash value = var:{PREFIX}_arm_m274_receipt_hash }}
        set_variable = {{ name = {PREFIX}_slot_carrier_type_id value = {POSITION_CARRIER_TYPE_ID} }}
        set_variable = {{ name = {PREFIX}_slot_id value = {{ value = var:{PREFIX}_arm_m274_receipt_id multiply = 1000 add = 277 }} }}
        set_variable = {{ name = {PREFIX}_slot_hash value = {{ value = var:{PREFIX}_arm_m274_receipt_hash multiply = 1000 add = {POSITION_CARRIER_TYPE_ID} }} }}
        set_variable = {{ name = {PREFIX}_slot_native_receive_seen value = 1 }}
        {PREFIX}_clear_arm_pending_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 1 }}
    }}
    else = {{
        if = {{
            limit = {{
                has_court_position = {POSITION_KEY}
                has_variable = {PREFIX}_arm_owner
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_arm_owner
                }}
            }}
            set_variable = {{ name = {PREFIX}_cleanup_revoke_requested value = 1 }}
            trigger_event = {{ id = {NAMESPACE}.{CLEANUP_REVOKE_EVENT_ID} days = 1 }}
        }}
        else = {{ {PREFIX}_clear_arm_pending_effect = yes }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27703 }}
    }}
}}

# Cleanup also crosses an event boundary.  Its callback therefore observes a
# committed cleanup intent and cannot be confused with an unrequested end.
{PREFIX}_dispatch_cleanup_revoke_effect = {{
    if = {{
        limit = {{
            has_variable = {PREFIX}_cleanup_revoke_requested
            var:{PREFIX}_cleanup_revoke_requested = 1
            has_variable = {PREFIX}_arm_pending
            var:{PREFIX}_arm_pending = 1
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = var:{PREFIX}_arm_owner
            }}
        }}
        var:{PREFIX}_arm_owner = {{
            revoke_court_position = {{
                recipient = root
                court_position = {POSITION_KEY}
            }}
        }}
    }}
    {PREFIX}_clear_arm_pending_effect = yes
    remove_variable = {PREFIX}_cleanup_revoke_requested
    set_variable = {{ name = {PREFIX}_status value = 4 }}
    set_variable = {{ name = {PREFIX}_red_code value = 27703 }}
}}

# Request the actual #277 native exit.  The real B2 PIP closure is joined but
# never consumed here.  Formal HC remains occupied/active throughout native
# revoke and receipt publication; only Workforce #277 may later freeze it.
{PREFIX}_request_closed_pip_exit_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_sealed = 1
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 6
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else_if = {{
        limit = {{
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
                EXPECTED_STATE = 6
            }}
            $TICKET_OWNER$ = {{ zg361_is_celestial_liege_trigger = yes }}
            $TICKET_SUBJECT$ = this
            has_variable = {PREFIX}_slot_active
            var:{PREFIX}_slot_active = 1
            var:{PREFIX}_slot_owner = $TICKET_OWNER$
            var:{PREFIX}_slot_subject = $TICKET_SUBJECT$
            var:{PREFIX}_slot_cycle = $TICKET_CYCLE$
            var:{PREFIX}_slot_case = $TICKET_CASE$
            var:{PREFIX}_slot_state = 4
            var:{PREFIX}_slot_position_type_id = {M274_POSITION_TYPE_ID}
            var:{PREFIX}_slot_appointment_receipt_id = var:zg361_we_m274_position_receipt_id
            var:{PREFIX}_slot_appointment_receipt_hash = var:zg361_we_m274_position_receipt_hash
            var:{PREFIX}_slot_carrier_type_id = {POSITION_CARRIER_TYPE_ID}
            var:{PREFIX}_slot_id > 0
            var:{PREFIX}_slot_hash > 0
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = $TICKET_OWNER$
            }}
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_hire_case = $TICKET_CASE$
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_appointed_character = $TICKET_SUBJECT$
            var:zg361_we_m274_position_type_id = {M274_POSITION_TYPE_ID}
            var:zg361_we_m274_position_receipt_id > 0
            var:zg361_we_m274_position_receipt_hash > 0
            var:zg361_we_m269_outcome_settled = 1
            var:zg361_we_m269_not_applicable_no_hire = 0
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = $TICKET_CASE$
            has_variable = zg361_ch_hc_occupied
            var:zg361_ch_hc_occupied >= 1
            has_variable = zg361_ch_hc_frozen
            has_variable = zg361_we_hours_total
            has_variable = zg361_we_hours_output
            has_variable = zg361_we_hours_on_call
            has_variable = zg361_we_hours_meeting
            has_variable = zg361_we_hours_governance
            var:zg361_we_hours_total >= 0
            var:zg361_we_hours_output >= 0
            var:zg361_we_hours_on_call >= 0
            var:zg361_we_hours_meeting >= 0
            var:zg361_we_hours_governance >= 0
            has_variable = zg361_we_offer_gold_paid
            var:zg361_we_offer_gold_paid > 0
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
            has_variable = zg361_b2_pip_outcome_code
            has_variable = zg361_b2_pip_outcome_result_grade
            var:zg361_b2_workforce_pip_pending = 1
            var:zg361_b2_workforce_pip_consumed = 0
            var:zg361_b2_workforce_pip_owner = $TICKET_OWNER$
            var:zg361_b2_workforce_pip_subject = $TICKET_SUBJECT$
            var:zg361_b2_workforce_pip_cycle > 0
            var:zg361_b2_workforce_pip_case > 0
            var:zg361_b2_workforce_pip_state = 4
            var:zg361_b2_pip_outcome_code = 2
            var:zg361_b2_pip_outcome_result_grade = 1
            var:zg361_b2_workforce_pip_case_id > 0
            var:zg361_b2_workforce_pip_case_hash > 0
            var:zg361_b2_workforce_pip_closure_receipt_id > 0
            var:zg361_b2_workforce_pip_closure_receipt_hash > 0
            NOT = {{ var:zg361_b2_workforce_pip_case_id = var:zg361_b2_workforce_pip_closure_receipt_id }}
            NOT = {{ var:zg361_b2_workforce_pip_case_hash = var:zg361_b2_workforce_pip_closure_receipt_hash }}
            OR = {{
                NOT = {{ has_variable = {PREFIX}_exit_pending }}
                var:{PREFIX}_exit_pending = 0
            }}
        }}
        set_variable = {{ name = {PREFIX}_exit_pending value = 1 }}
        set_variable = {{ name = {PREFIX}_exit_owner value = $TICKET_OWNER$ }}
        set_variable = {{ name = {PREFIX}_exit_subject value = $TICKET_SUBJECT$ }}
        set_variable = {{ name = {PREFIX}_exit_cycle value = $TICKET_CYCLE$ }}
        set_variable = {{ name = {PREFIX}_exit_case value = $TICKET_CASE$ }}
        set_variable = {{ name = {PREFIX}_exit_state value = 6 }}
        set_variable = {{ name = {PREFIX}_exit_slot_was_active value = 1 }}
        set_variable = {{ name = {PREFIX}_exit_former_slot_id value = var:{PREFIX}_slot_id }}
        set_variable = {{ name = {PREFIX}_exit_former_slot_hash value = var:{PREFIX}_slot_hash }}
        set_variable = {{ name = {PREFIX}_exit_position_type_id value = var:zg361_we_m274_position_type_id }}
        set_variable = {{ name = {PREFIX}_exit_carrier_type_id value = var:{PREFIX}_slot_carrier_type_id }}
        set_variable = {{ name = {PREFIX}_exit_appointment_receipt_id value = var:zg361_we_m274_position_receipt_id }}
        set_variable = {{ name = {PREFIX}_exit_appointment_receipt_hash value = var:zg361_we_m274_position_receipt_hash }}
        set_variable = {{ name = {PREFIX}_exit_pip_cycle value = var:zg361_b2_workforce_pip_cycle }}
        set_variable = {{ name = {PREFIX}_exit_pip_case value = var:zg361_b2_workforce_pip_case }}
        set_variable = {{ name = {PREFIX}_exit_pip_state value = var:zg361_b2_workforce_pip_state }}
        set_variable = {{ name = {PREFIX}_exit_pip_case_id value = var:zg361_b2_workforce_pip_case_id }}
        set_variable = {{ name = {PREFIX}_exit_pip_case_hash value = var:zg361_b2_workforce_pip_case_hash }}
        set_variable = {{ name = {PREFIX}_exit_pip_closure_receipt_id value = var:zg361_b2_workforce_pip_closure_receipt_id }}
        set_variable = {{ name = {PREFIX}_exit_pip_closure_receipt_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }}
        set_variable = {{ name = {PREFIX}_exit_pip_outcome_code value = var:zg361_b2_pip_outcome_code }}
        set_variable = {{ name = {PREFIX}_exit_pip_result_grade value = var:zg361_b2_pip_outcome_result_grade }}
        set_variable = {{ name = {PREFIX}_exit_displaced_hours value = {{ value = var:zg361_we_hours_output add = var:zg361_we_hours_on_call add = var:zg361_we_hours_meeting add = var:zg361_we_hours_governance }} }}
        set_variable = {{ name = {PREFIX}_exit_displaced_cost_amount value = var:zg361_we_offer_gold_paid }}
        set_variable = {{ name = {PREFIX}_exit_displaced_cost_receipt value = {{ value = var:zg361_we_m274_position_receipt_id multiply = 1000 add = {{ value = var:zg361_we_offer_gold_paid multiply = 10 }} add = 5 }} }}
        set_variable = {{ name = {PREFIX}_exit_displaced_cost_hash value = {{ value = var:zg361_we_m274_position_receipt_hash multiply = 100000 add = {{ value = var:zg361_we_offer_gold_paid multiply = 100 }} add = 2775 }} }}
        set_variable = {{ name = {PREFIX}_exit_hc_occupied_before value = var:zg361_ch_hc_occupied }}
        set_variable = {{ name = {PREFIX}_exit_hc_frozen_before value = var:zg361_ch_hc_frozen }}
        remove_variable = {PREFIX}_native_exit_revoked_callback_seen
        remove_variable = {PREFIX}_native_exit_revoked_callback_owner
        remove_variable = {PREFIX}_native_exit_revoked_callback_subject
        set_variable = {{ name = {PREFIX}_exit_request_authorized value = 1 }}
        trigger_event = {{ id = {NAMESPACE}.{EXIT_DISPATCH_EVENT_ID} days = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27704 }}
    }}
}}

# D+1 native revoke dispatch.  The complete exit intent and authorization are
# now committed, so the native callback can authenticate this exact request
# without reading values written earlier in its own effect chain.
{PREFIX}_dispatch_native_exit_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_exit_pending
            var:{PREFIX}_exit_pending = 1
            var:{PREFIX}_exit_subject = this
            var:{PREFIX}_exit_state = 6
            has_variable = {PREFIX}_exit_request_authorized
            var:{PREFIX}_exit_request_authorized = 1
            var:{PREFIX}_exit_slot_was_active = 1
            var:{PREFIX}_slot_active = 1
            var:{PREFIX}_slot_owner = var:{PREFIX}_exit_owner
            var:{PREFIX}_slot_subject = this
            var:{PREFIX}_slot_cycle = var:{PREFIX}_exit_cycle
            var:{PREFIX}_slot_case = var:{PREFIX}_exit_case
            var:{PREFIX}_slot_id = var:{PREFIX}_exit_former_slot_id
            var:{PREFIX}_slot_hash = var:{PREFIX}_exit_former_slot_hash
            var:{PREFIX}_slot_carrier_type_id = var:{PREFIX}_exit_carrier_type_id
            var:{PREFIX}_exit_carrier_type_id = {POSITION_CARRIER_TYPE_ID}
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = var:{PREFIX}_exit_owner
            }}
            zg361_case_kernel_full_guard_trigger = {{
                OWNER_VAR = zg361_case_ad_owner
                SUBJECT_VAR = zg361_case_ad_subject
                CYCLE_VAR = zg361_case_ad_cycle_serial
                CASE_VAR = zg361_case_ad_case_serial
                STATE_VAR = zg361_case_ad_state
                ACTIVE_VAR = zg361_case_ad_active
                EXPECTED_OWNER = var:{PREFIX}_exit_owner
                EXPECTED_SUBJECT = this
                EXPECTED_CYCLE = var:{PREFIX}_exit_cycle
                EXPECTED_CASE = var:{PREFIX}_exit_case
                EXPECTED_STATE = 6
            }}
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_hire_case = var:{PREFIX}_exit_case
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_position_type_id = var:{PREFIX}_exit_position_type_id
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_exit_appointment_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_exit_appointment_receipt_hash
            var:zg361_we_m269_outcome_settled = 1
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_exit_case
            var:zg361_ch_hc_occupied = var:{PREFIX}_exit_hc_occupied_before
            var:zg361_ch_hc_frozen = var:{PREFIX}_exit_hc_frozen_before
            var:zg361_b2_workforce_pip_pending = 1
            var:zg361_b2_workforce_pip_consumed = 0
            var:zg361_b2_workforce_pip_owner = var:{PREFIX}_exit_owner
            var:zg361_b2_workforce_pip_subject = this
            var:zg361_b2_workforce_pip_cycle = var:{PREFIX}_exit_pip_cycle
            var:zg361_b2_workforce_pip_case = var:{PREFIX}_exit_pip_case
            var:zg361_b2_workforce_pip_state = 4
            var:zg361_b2_workforce_pip_case_id = var:{PREFIX}_exit_pip_case_id
            var:zg361_b2_workforce_pip_case_hash = var:{PREFIX}_exit_pip_case_hash
            var:zg361_b2_workforce_pip_closure_receipt_id = var:{PREFIX}_exit_pip_closure_receipt_id
            var:zg361_b2_workforce_pip_closure_receipt_hash = var:{PREFIX}_exit_pip_closure_receipt_hash
            var:zg361_b2_pip_outcome_code = 2
            var:zg361_b2_pip_outcome_result_grade = 1
        }}
        set_variable = {{ name = {PREFIX}_exit_request_dispatched value = 1 }}
        var:{PREFIX}_exit_owner = {{
            revoke_court_position = {{
                recipient = root
                court_position = {POSITION_KEY}
            }}
        }}
        trigger_event = {{ id = {NAMESPACE}.{EXIT_AUDIT_EVENT_ID} days = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
    }}
    else = {{
        {PREFIX}_clear_exit_pending_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27709 }}
    }}
}}

# The exit receipt is sealed only on a later event after a fresh native revoke
# callback and no-longer-holder postcondition.  B2 and HC must still be
# untouched at this boundary.
{PREFIX}_audit_exit_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_exit_pending
            var:{PREFIX}_exit_pending = 1
            var:{PREFIX}_exit_subject = this
            var:{PREFIX}_exit_state = 6
            var:{PREFIX}_exit_slot_was_active = 1
            var:{PREFIX}_exit_former_slot_id > 0
            var:{PREFIX}_exit_former_slot_hash > 0
            var:{PREFIX}_exit_position_type_id = {M274_POSITION_TYPE_ID}
            var:{PREFIX}_exit_carrier_type_id = {POSITION_CARRIER_TYPE_ID}
            var:{PREFIX}_exit_appointment_receipt_id > 0
            var:{PREFIX}_exit_appointment_receipt_hash > 0
            has_variable = {PREFIX}_exit_request_authorized
            var:{PREFIX}_exit_request_authorized = 1
            has_variable = {PREFIX}_exit_request_dispatched
            var:{PREFIX}_exit_request_dispatched = 1
            has_variable = {PREFIX}_native_exit_revoked_callback_seen
            var:{PREFIX}_native_exit_revoked_callback_seen = 1
            var:{PREFIX}_native_exit_revoked_callback_owner = var:{PREFIX}_exit_owner
            var:{PREFIX}_native_exit_revoked_callback_subject = this
            NOT = {{ has_court_position = {POSITION_KEY} }}
            var:{PREFIX}_slot_active = 0
            zg361_case_kernel_full_guard_trigger = {{
                OWNER_VAR = zg361_case_ad_owner
                SUBJECT_VAR = zg361_case_ad_subject
                CYCLE_VAR = zg361_case_ad_cycle_serial
                CASE_VAR = zg361_case_ad_case_serial
                STATE_VAR = zg361_case_ad_state
                ACTIVE_VAR = zg361_case_ad_active
                EXPECTED_OWNER = var:{PREFIX}_exit_owner
                EXPECTED_SUBJECT = this
                EXPECTED_CYCLE = var:{PREFIX}_exit_cycle
                EXPECTED_CASE = var:{PREFIX}_exit_case
                EXPECTED_STATE = 6
            }}
            var:zg361_we_m274_hired = 1
            var:zg361_we_m274_hire_case = var:{PREFIX}_exit_case
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_position_type_id = var:{PREFIX}_exit_position_type_id
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_exit_appointment_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_exit_appointment_receipt_hash
            var:zg361_we_m269_outcome_settled = 1
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_exit_case
            var:zg361_ch_hc_occupied = var:{PREFIX}_exit_hc_occupied_before
            var:zg361_ch_hc_frozen = var:{PREFIX}_exit_hc_frozen_before
            var:zg361_b2_workforce_pip_pending = 1
            var:zg361_b2_workforce_pip_consumed = 0
            var:zg361_b2_workforce_pip_owner = var:{PREFIX}_exit_owner
            var:zg361_b2_workforce_pip_subject = this
            var:zg361_b2_workforce_pip_cycle = var:{PREFIX}_exit_pip_cycle
            var:zg361_b2_workforce_pip_case = var:{PREFIX}_exit_pip_case
            var:zg361_b2_workforce_pip_state = var:{PREFIX}_exit_pip_state
            var:zg361_b2_workforce_pip_case_id = var:{PREFIX}_exit_pip_case_id
            var:zg361_b2_workforce_pip_case_hash = var:{PREFIX}_exit_pip_case_hash
            var:zg361_b2_workforce_pip_closure_receipt_id = var:{PREFIX}_exit_pip_closure_receipt_id
            var:zg361_b2_workforce_pip_closure_receipt_hash = var:{PREFIX}_exit_pip_closure_receipt_hash
            var:zg361_b2_pip_outcome_code = var:{PREFIX}_exit_pip_outcome_code
            var:zg361_b2_pip_outcome_result_grade = var:{PREFIX}_exit_pip_result_grade
            var:{PREFIX}_exit_pip_state = 4
            var:{PREFIX}_exit_pip_outcome_code = 2
            var:{PREFIX}_exit_pip_result_grade = 1
            var:{PREFIX}_exit_displaced_hours >= 0
            var:{PREFIX}_exit_displaced_cost_amount > 0
            var:{PREFIX}_exit_displaced_cost_receipt > 0
            var:{PREFIX}_exit_displaced_cost_hash > 0
            OR = {{
                NOT = {{ has_variable = {PREFIX}_receipt_active }}
                var:{PREFIX}_receipt_active = 0
            }}
        }}
        set_variable = {{ name = {PREFIX}_receipt_active value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_consumed value = 0 }}
        set_variable = {{ name = {PREFIX}_receipt_published value = 0 }}
        set_variable = {{ name = {PREFIX}_receipt_owner value = var:{PREFIX}_exit_owner }}
        set_variable = {{ name = {PREFIX}_receipt_subject value = this }}
        set_variable = {{ name = {PREFIX}_receipt_cycle value = var:{PREFIX}_exit_cycle }}
        set_variable = {{ name = {PREFIX}_receipt_case value = var:{PREFIX}_exit_case }}
        set_variable = {{ name = {PREFIX}_receipt_state value = 6 }}
        set_variable = {{ name = {PREFIX}_receipt_reason_kind value = {REASON_KIND_PIP} }}
        set_variable = {{ name = {PREFIX}_receipt_misconduct_present value = 0 }}
        set_variable = {{ name = {PREFIX}_receipt_position_type_id value = var:{PREFIX}_exit_position_type_id }}
        set_variable = {{ name = {PREFIX}_receipt_carrier_type_id value = var:{PREFIX}_exit_carrier_type_id }}
        set_variable = {{ name = {PREFIX}_receipt_appointment_receipt_id value = var:{PREFIX}_exit_appointment_receipt_id }}
        set_variable = {{ name = {PREFIX}_receipt_appointment_receipt_hash value = var:{PREFIX}_exit_appointment_receipt_hash }}
        set_variable = {{ name = {PREFIX}_receipt_former_slot_id value = var:{PREFIX}_exit_former_slot_id }}
        set_variable = {{ name = {PREFIX}_receipt_former_slot_hash value = var:{PREFIX}_exit_former_slot_hash }}
        set_variable = {{ name = {PREFIX}_receipt_pip_cycle value = var:{PREFIX}_exit_pip_cycle }}
        set_variable = {{ name = {PREFIX}_receipt_pip_case value = var:{PREFIX}_exit_pip_case }}
        set_variable = {{ name = {PREFIX}_receipt_pip_state value = var:{PREFIX}_exit_pip_state }}
        set_variable = {{ name = {PREFIX}_receipt_pip_case_id value = var:{PREFIX}_exit_pip_case_id }}
        set_variable = {{ name = {PREFIX}_receipt_pip_case_hash value = var:{PREFIX}_exit_pip_case_hash }}
        set_variable = {{ name = {PREFIX}_receipt_pip_closure_receipt_id value = var:{PREFIX}_exit_pip_closure_receipt_id }}
        set_variable = {{ name = {PREFIX}_receipt_pip_closure_receipt_hash value = var:{PREFIX}_exit_pip_closure_receipt_hash }}
        set_variable = {{ name = {PREFIX}_receipt_pip_outcome_code value = var:{PREFIX}_exit_pip_outcome_code }}
        set_variable = {{ name = {PREFIX}_receipt_pip_result_grade value = var:{PREFIX}_exit_pip_result_grade }}
        set_variable = {{ name = {PREFIX}_receipt_displaced_hours value = var:{PREFIX}_exit_displaced_hours }}
        set_variable = {{ name = {PREFIX}_receipt_displaced_cost_amount value = var:{PREFIX}_exit_displaced_cost_amount }}
        set_variable = {{ name = {PREFIX}_receipt_displaced_cost_receipt value = var:{PREFIX}_exit_displaced_cost_receipt }}
        set_variable = {{ name = {PREFIX}_receipt_displaced_cost_hash value = var:{PREFIX}_exit_displaced_cost_hash }}
        set_variable = {{ name = {PREFIX}_receipt_hc_occupied_before value = var:{PREFIX}_exit_hc_occupied_before }}
        set_variable = {{ name = {PREFIX}_receipt_hc_frozen_before value = var:{PREFIX}_exit_hc_frozen_before }}
        set_variable = {{ name = {PREFIX}_receipt_native_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_native_end_reason value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_id value = {{ value = var:{PREFIX}_exit_pip_closure_receipt_id multiply = 1000 add = 277 }} }}
        set_variable = {{ name = {PREFIX}_receipt_hash value = {{ value = var:{PREFIX}_exit_pip_closure_receipt_hash multiply = 100000 add = {{ value = var:{PREFIX}_exit_appointment_receipt_hash multiply = 10 }} add = var:{PREFIX}_exit_former_slot_hash add = var:{PREFIX}_exit_displaced_hours add = var:{PREFIX}_exit_displaced_cost_amount add = 1 }} }}
        set_variable = {{ name = {PREFIX}_receipt_sealed value = 1 }}
        {PREFIX}_clear_exit_pending_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 1 }}
        trigger_event = {{ id = {NAMESPACE}.{PUBLISH_EVENT_ID} days = 1 }}
    }}
    else = {{
        {PREFIX}_clear_exit_pending_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27705 }}
    }}
}}

# Publish the five legacy #277 fields through the existing strict adapter.
# IDs/hashes are supplied internally from the sealed receipt, never by this
# public package's caller.  Verification is delayed to another event so the
# adapter ACK is not read back in the same effect chain.
{PREFIX}_publish_to_workforce_m277_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_sealed = 1
            var:{PREFIX}_receipt_published = 0
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_subject = this
            var:{PREFIX}_receipt_state = 6
            var:{PREFIX}_receipt_reason_kind = {REASON_KIND_PIP}
            var:{PREFIX}_receipt_misconduct_present = 0
            var:{PREFIX}_receipt_native_callback_seen = 1
            var:{PREFIX}_receipt_native_end_reason = 1
            var:{PREFIX}_receipt_id > 0
            var:{PREFIX}_receipt_hash > 0
            var:{PREFIX}_receipt_former_slot_id > 0
            var:{PREFIX}_receipt_former_slot_hash > 0
            var:{PREFIX}_receipt_carrier_type_id = {POSITION_CARRIER_TYPE_ID}
            var:{PREFIX}_receipt_displaced_hours >= 0
            var:{PREFIX}_receipt_displaced_cost_receipt > 0
            var:zg361_we_formal_hc_active = 1
            var:zg361_we_formal_hc_active_case = var:{PREFIX}_receipt_case
            var:zg361_ch_hc_occupied = var:{PREFIX}_receipt_hc_occupied_before
            var:zg361_ch_hc_frozen = var:{PREFIX}_receipt_hc_frozen_before
            var:zg361_b2_workforce_pip_pending = 1
            var:zg361_b2_workforce_pip_consumed = 0
            var:zg361_b2_workforce_pip_owner = var:{PREFIX}_receipt_owner
            var:zg361_b2_workforce_pip_subject = this
            var:zg361_b2_workforce_pip_cycle = var:{PREFIX}_receipt_pip_cycle
            var:zg361_b2_workforce_pip_case = var:{PREFIX}_receipt_pip_case
            var:zg361_b2_workforce_pip_state = var:{PREFIX}_receipt_pip_state
            var:zg361_b2_workforce_pip_case_id = var:{PREFIX}_receipt_pip_case_id
            var:zg361_b2_workforce_pip_case_hash = var:{PREFIX}_receipt_pip_case_hash
            var:zg361_b2_workforce_pip_closure_receipt_id = var:{PREFIX}_receipt_pip_closure_receipt_id
            var:zg361_b2_workforce_pip_closure_receipt_hash = var:{PREFIX}_receipt_pip_closure_receipt_hash
            var:zg361_b2_pip_outcome_code = var:{PREFIX}_receipt_pip_outcome_code
            var:zg361_b2_pip_outcome_result_grade = var:{PREFIX}_receipt_pip_result_grade
            var:{PREFIX}_receipt_pip_state = 4
            var:{PREFIX}_receipt_pip_outcome_code = 2
            var:{PREFIX}_receipt_pip_result_grade = 1
            NOT = {{ has_court_position = {POSITION_KEY} }}
        }}
        set_variable = {{ name = {PREFIX}_publish_dispatched value = 1 }}
        zg361_we_submit_m277_closed_pip_exit_effect = {{
            TICKET_OWNER = var:{PREFIX}_receipt_owner
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{PREFIX}_receipt_cycle
            TICKET_CASE = var:{PREFIX}_receipt_case
            EXIT_CONFIRMED = 1
            EXIT_RECEIPT_ID = var:{PREFIX}_receipt_id
            EXIT_RECEIPT_HASH = var:{PREFIX}_receipt_hash
            FORMER_SLOT_ID = var:{PREFIX}_receipt_former_slot_id
            DISPLACED_HOURS = var:{PREFIX}_receipt_displaced_hours
            DISPLACED_COST_RECEIPT = var:{PREFIX}_receipt_displaced_cost_receipt
            EXITED_CHARACTER = this
        }}
        trigger_event = {{ id = {NAMESPACE}.{PUBLISH_VERIFY_EVENT_ID} days = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_published = 1
            var:{PREFIX}_receipt_subject = this
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27706 }}
    }}
}}

{PREFIX}_verify_publish_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_publish_dispatched
            var:{PREFIX}_publish_dispatched = 1
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_sealed = 1
            var:{PREFIX}_receipt_published = 0
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_subject = this
            var:zg361_we_adapter_status = 1
            var:zg361_we_ad_external_pip_exit_ready = 1
            var:zg361_we_ad_external_pip_exit_consumed = 0
            var:zg361_we_ad_external_exit_receipt_id = var:{PREFIX}_receipt_id
            var:zg361_we_ad_external_exit_receipt_hash = var:{PREFIX}_receipt_hash
            var:zg361_we_ad_external_exit_former_slot_id = var:{PREFIX}_receipt_former_slot_id
            var:zg361_we_ad_external_exit_displaced_hours = var:{PREFIX}_receipt_displaced_hours
            var:zg361_we_ad_external_exit_displaced_cost_receipt = var:{PREFIX}_receipt_displaced_cost_receipt
            var:zg361_b2_workforce_pip_pending = 1
            var:zg361_b2_workforce_pip_consumed = 0
            var:zg361_we_formal_hc_active = 1
            var:zg361_ch_hc_occupied = var:{PREFIX}_receipt_hc_occupied_before
            var:zg361_ch_hc_frozen = var:{PREFIX}_receipt_hc_frozen_before
        }}
        set_variable = {{ name = {PREFIX}_receipt_published value = 1 }}
        set_variable = {{ name = {PREFIX}_status value = 1 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27707 }}
    }}
}}

# Call only after Workforce #277 A/B has committed on a later event/tick.
# This effect observes exact HC/B2/core postconditions and marks the detailed
# receipt consumed; it never moves HC itself.
{PREFIX}_consume_after_m277_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_sealed = 1
            var:{PREFIX}_receipt_published = 1
            var:{PREFIX}_receipt_consumed = 1
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 6
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_sealed = 1
            var:{PREFIX}_receipt_published = 1
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 6
            var:zg361_we_ad_external_pip_exit_ready = 0
            var:zg361_we_ad_external_pip_exit_consumed = 1
            var:zg361_b2_workforce_pip_pending = 0
            var:zg361_b2_workforce_pip_consumed = 1
            var:zg361_b2_workforce_pip_owner = $TICKET_OWNER$
            var:zg361_b2_workforce_pip_subject = $TICKET_SUBJECT$
            var:zg361_b2_workforce_pip_cycle = var:{PREFIX}_receipt_pip_cycle
            var:zg361_b2_workforce_pip_case = var:{PREFIX}_receipt_pip_case
            var:zg361_b2_workforce_pip_state = var:{PREFIX}_receipt_pip_state
            var:zg361_b2_workforce_pip_case_id = var:{PREFIX}_receipt_pip_case_id
            var:zg361_b2_workforce_pip_case_hash = var:{PREFIX}_receipt_pip_case_hash
            var:zg361_b2_workforce_pip_closure_receipt_id = var:{PREFIX}_receipt_pip_closure_receipt_id
            var:zg361_b2_workforce_pip_closure_receipt_hash = var:{PREFIX}_receipt_pip_closure_receipt_hash
            var:zg361_b2_pip_outcome_code = var:{PREFIX}_receipt_pip_outcome_code
            var:zg361_b2_pip_outcome_result_grade = var:{PREFIX}_receipt_pip_result_grade
            var:{PREFIX}_receipt_pip_state = 4
            var:{PREFIX}_receipt_pip_outcome_code = 2
            var:{PREFIX}_receipt_pip_result_grade = 1
            OR = {{
                zg361_case_kernel_receipt_is_current_trigger = {{
                    RECEIPT_OWNER_VAR = zg361_we_m277_receipt_owner
                    RECEIPT_SUBJECT_VAR = zg361_we_m277_receipt_subject
                    RECEIPT_CYCLE_VAR = zg361_we_m277_receipt_cycle
                    RECEIPT_CASE_VAR = zg361_we_m277_receipt_case
                    RECEIPT_STATE_VAR = zg361_we_m277_receipt_state
                    RECEIPT_CHOICE_VAR = zg361_we_m277_receipt_choice
                    EXPECTED_OWNER = $TICKET_OWNER$
                    EXPECTED_SUBJECT = $TICKET_SUBJECT$
                    EXPECTED_CYCLE = $TICKET_CYCLE$
                    EXPECTED_CASE = $TICKET_CASE$
                    EXPECTED_STATE = 6
                    EXPECTED_CHOICE = 1
                }}
                zg361_case_kernel_receipt_is_current_trigger = {{
                    RECEIPT_OWNER_VAR = zg361_we_m277_receipt_owner
                    RECEIPT_SUBJECT_VAR = zg361_we_m277_receipt_subject
                    RECEIPT_CYCLE_VAR = zg361_we_m277_receipt_cycle
                    RECEIPT_CASE_VAR = zg361_we_m277_receipt_case
                    RECEIPT_STATE_VAR = zg361_we_m277_receipt_state
                    RECEIPT_CHOICE_VAR = zg361_we_m277_receipt_choice
                    EXPECTED_OWNER = $TICKET_OWNER$
                    EXPECTED_SUBJECT = $TICKET_SUBJECT$
                    EXPECTED_CYCLE = $TICKET_CYCLE$
                    EXPECTED_CASE = $TICKET_CASE$
                    EXPECTED_STATE = 6
                    EXPECTED_CHOICE = 2
                }}
            }}
            has_variable = zg361_we_m277_business_object_created
            has_variable = zg361_we_m277_object_consumed
            has_variable = zg361_we_m277_object_id
            has_variable = zg361_we_m277_consumer_record_pip_exit_277
            OR = {{
                var:zg361_we_record_pip_exit_277 = 1
                var:zg361_we_record_pip_exit_277 = 2
            }}
            var:zg361_we_m277_business_object_created = 1
            var:zg361_we_m277_object_type_code = 277
            var:zg361_we_m277_object_pip_exit_vacancy = 1
            var:zg361_we_m277_object_owner = $TICKET_OWNER$
            var:zg361_we_m277_object_subject = $TICKET_SUBJECT$
            var:zg361_we_m277_object_cycle = $TICKET_CYCLE$
            var:zg361_we_m277_object_case = $TICKET_CASE$
            var:zg361_we_m277_object_state = 6
            AND = {{
                var:zg361_we_m277_object_id >= {{ value = $TICKET_CASE$ multiply = 1000 add = 277 }}
                var:zg361_we_m277_object_id <= {{ value = $TICKET_CASE$ multiply = 1000 add = 277 }}
            }}
            var:zg361_we_m277_consumer_contract = 277
            var:zg361_we_m277_object_consumed = 1
            var:zg361_we_m277_consumer_record_pip_exit_277 = 1
            var:zg361_we_m277_consumed_owner = $TICKET_OWNER$
            var:zg361_we_m277_consumed_subject = $TICKET_SUBJECT$
            var:zg361_we_m277_consumed_cycle = $TICKET_CYCLE$
            var:zg361_we_m277_consumed_case = $TICKET_CASE$
            var:zg361_we_m277_consumed_state = 6
            var:zg361_we_m277_exit_receipt_id = var:{PREFIX}_receipt_id
            var:zg361_we_m277_exit_receipt_hash = var:{PREFIX}_receipt_hash
            var:zg361_we_m277_position_type_id = var:{PREFIX}_receipt_position_type_id
            var:zg361_we_m277_former_slot_id = var:{PREFIX}_receipt_former_slot_id
            var:zg361_we_m277_displaced_subject = $TICKET_SUBJECT$
            var:zg361_we_m277_displaced_hours = var:{PREFIX}_receipt_displaced_hours
            var:zg361_we_m277_displaced_cost_provenance = var:{PREFIX}_receipt_displaced_cost_receipt
            var:zg361_we_m277_vacant_frozen = 1
            var:zg361_we_m277_hc_minted = 0
            var:zg361_we_formal_hc_active = 0
            AND = {{
                var:zg361_ch_hc_occupied >= {{ value = var:{PREFIX}_receipt_hc_occupied_before subtract = 1 }}
                var:zg361_ch_hc_occupied <= {{ value = var:{PREFIX}_receipt_hc_occupied_before subtract = 1 }}
            }}
            AND = {{
                var:zg361_ch_hc_frozen >= {{ value = var:{PREFIX}_receipt_hc_frozen_before add = 1 }}
                var:zg361_ch_hc_frozen <= {{ value = var:{PREFIX}_receipt_hc_frozen_before add = 1 }}
            }}
            NOT = {{ has_court_position = {POSITION_KEY} }}
        }}
        set_variable = {{ name = {PREFIX}_receipt_consumed value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_consumed_operation value = 277 }}
        set_variable = {{ name = {PREFIX}_status value = 6 }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 5 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27708 }}
    }}
}}
"""
    )


def render_events() -> bytes:
    return generated(
        f"""
namespace = {NAMESPACE}

{NAMESPACE}.{ARM_DISPATCH_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_dispatch_native_arm_effect = yes }}
}}

{NAMESPACE}.{ARM_AUDIT_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_audit_arm_effect = yes }}
}}

{NAMESPACE}.{EXIT_DISPATCH_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_dispatch_native_exit_effect = yes }}
}}

{NAMESPACE}.{EXIT_AUDIT_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_audit_exit_effect = yes }}
}}

{NAMESPACE}.{PUBLISH_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_publish_to_workforce_m277_effect = yes }}
}}

{NAMESPACE}.{PUBLISH_VERIFY_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_verify_publish_effect = yes }}
}}

{NAMESPACE}.{CLEANUP_REVOKE_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_dispatch_cleanup_revoke_effect = yes }}
}}

{NAMESPACE}.{ROLE_FAILURE_PUBLISH_EVENT_ID} = {{
    type = character_event
    hidden = yes
    trigger = {{
        var:{PREFIX}_role_failure_receipt_active = 1
        var:{PREFIX}_role_failure_receipt_sealed = 1
        var:{PREFIX}_role_failure_receipt_consumed = 0
        var:{PREFIX}_role_failure_receipt_subject = this
    }}
    immediate = {{
        {PROBATION_ROLE_FAILURE_EFFECT} = yes
        trigger_event = {{ id = {NAMESPACE}.{ROLE_FAILURE_VERIFY_EVENT_ID} days = 1 }}
    }}
}}

{NAMESPACE}.{ROLE_FAILURE_VERIFY_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{ {PREFIX}_verify_role_failure_publish_effect = yes }}
}}
"""
    )


def _loc_rows(language: str) -> dict[str, str]:
    english = {
        POSITION_KEY: "361 Formal Career Slot",
        f"{POSITION_KEY}_desc": (
            "A zero-salary native carrier for a confirmed formal-HC appointment. "
            "It remains until a real PIP exit revokes the slot."
        ),
    }
    chinese = {
        POSITION_KEY: "三六一正式在岗编制",
        f"{POSITION_KEY}_desc": (
            "已由原生任命确认的正式 HC 在岗载体，不另发俸禄；只有真实 PIP 离任撤职后才结束。"
        ),
    }
    return chinese if language == "simp_chinese" else english


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    rows = [f"l_{language}:"]
    for key, value in _loc_rows(language).items():
        rows.append(f' {key}:0 "{_escape(value)}"')
    return localized("\n".join(rows))


def render_spec() -> bytes:
    return localized(
        f"""
<!-- GENERATED FILE -- edit tools/gen_zg361_workforce_exit_fact.py -->
# Workforce #277 Career/native exit 真实事实包

状态：**CK3 script core-wired/static-ready; not loader-live or production-live**。本包由共享 Workforce core 的 #274 post-consume seam 调用 arm；其余生成器、脚本、事件、court position、九语言结构投影与 L0 仍由本包独立维护。简体中文与英文为日常开发原创，其余七语只是英文结构占位。

## 1. 为什么不能复用 #274 的撤职回调

`zg361_workforce_appointment_fact_court_position` 是 #274 的有界任命载体。#274 operation ACK 后，它会被 package-owned `revoke_court_position` 立即清理；D+1 audit 最迟也会清理。因此那次 callback 只证明“任命载体已收口”，绝不证明数轮之后发生了 PIP 离任。

本包新增真实、零俸禄、长期存在的 `{POSITION_KEY}`。公开 `arm_from_m274_effect` 只在以下事实同时成立后冻结任命 intent：#274 business object 已消费；`m274_native_appointment_confirmed=1`；#274 immutable receipt 的 owner/subject/cycle/case/type/id/hash 全吻合；旧有界岗位已由 package revoke 且已不存在；formal HC 仍 occupied。D+1 dispatch 重新核验这些已提交事实并执行原生任命；收到 `on_court_position_received` 后再等 D+1 holder/employer postcondition，才封存 active career slot。失败清理也先提交 cleanup intent，再由下一事件执行 revoke，避免 callback 读取同一 effect chain 刚写入的授权位。它不是新 HC，也不改变 gold/hours/HC。

## 2. 真实 #277 native exit

公开 `request_closed_pip_exit_effect` 只接收 `TICKET_OWNER/TICKET_SUBJECT/TICKET_CYCLE/TICKET_CASE`。它要求同一 career slot 仍被 subject 持有、formal HC 仍 active/occupied、#269 outcome 已结算，并 join B2 已提交但未消费的一格 PIP closed source。它只冻结完整 intent 与 provenance；D+1 dispatch 重验同一 slot/B2/HC 后，才对长期 carrier 执行一次原生 `revoke_court_position`。callback 读取的是前一事件已提交的 pending/authorization，D+1 audit 再要求 dispatch 位、fresh revoked callback 和岗位确已消失，整条链没有 same-effect read-after-write 充当成功证据。

court-position 三类结束 callback 都会被观察：revoked=`1`、invalidated=`2`、vacated=`3`。只有本次 exact intent 之后的新 revoked callback（reason=1），再加 D+1 `NOT has_court_position`，才能 seal #277 exit。旧 #274 callback、B2 ACK、调用方 bool、自然 invalidation/vacate、仅“岗位变量被清零”都不能封 #277 receipt。另有一个严格分离的 role-failure receipt：仅当 still-alive subject 的 exact long-lived slot 在未请求 exit/normal-exit/cleanup 时发生 native invalidation=`2`，且同一 3.25 probation、#274 appointment、#269 pending、formal-HC tuple 与六分区守恒全吻合，才会在 callback 清空 active 前冻结 slot/hash/appointment/review-cycle 及 HC partition provenance。它在 D+1 调用 probation canonical quality=4 exclusion hook，再在后一日核 exact publish 后消费；它不释放 HC、绝不冒充实际离职。

## 3. 五个 #277 字段及其 provenance

| legacy field | 本包 immutable source |
|---|---|
| `zg361_we_ad_external_exit_receipt_id` | `{PREFIX}_receipt_id`，由真实 B2 closure receipt 派生 |
| `zg361_we_ad_external_exit_receipt_hash` | `{PREFIX}_receipt_hash`，绑定 B2 closure、#274 appointment、hours/cost |
| `zg361_we_ad_external_exit_former_slot_id` | `{PREFIX}_receipt_former_slot_id`，由真实 native holder/employer 确认后封存的 package-owned 稳定 slot lineage；不是声称读取了 CK3 未暴露的实例 GUID |
| `zg361_we_ad_external_exit_displaced_hours` | `{PREFIX}_receipt_displaced_hours`，冻结 Workforce ledger 中 output+on-call+meeting+governance 的真实已用工时，不含 leave |
| `zg361_we_ad_external_exit_displaced_cost_receipt` | `{PREFIX}_receipt_displaced_cost_receipt`，绑定 #274 native appointment receipt 与实际 `offer_gold_paid`；另保存 amount/hash |

receipt 永久保留 `active/sealed/published/consumed`、owner/subject/cycle/case/state=6、#274 position/receipt lineage、B2 PIP cycle/case/state/case+closure IDs/hashes、outcome code/result grade、native callback reason、HC before snapshot 与上述 provenance。`reason_kind=1` 只表示 **失败 PIP exit**：必须为 B2 state=4、outcome_code=2、result_grade=1；state=3 graduation 不会撤职，也不能生成本 receipt。`misconduct_present=0` 是真实“不存在此来源”，本包不会伪造 misconduct ID/hash；本 receipt 同样不能冒充正常离职或外部成长。

## 4. 发布与消费顺序

seal 后的下一事件才调用既有严格 `zg361_we_submit_m277_closed_pip_exit_effect`，再下一事件核验五个 legacy alias；公开调用方从未传入成功位或 ID/hash。adapter 必需的 `EXIT_CONFIRMED=1` 只由本包在 sealed receipt、fresh native revoked callback 与 no-longer-holder guard 已全部成立后内部提供，并非外部事实输入。此时 B2 仍 `pending=1/consumed=0`，formal HC 与 occupied/frozen 必须和撤职前完全相同。也就是说 native 岗位结束不等于先释放 HC。

未来 core 应在 `receipt_published=1` 后才开放 #277 A/B/C。#277 A/B 的 operation receipt 成功后，必须在下一事件/帧调用 `consume_after_m277_effect`；它只观察而不修改：case-kernel receipt 的 choice 必须为 1/2，m277 business object 已创建且其 owner/subject/cycle/case/state/id/type 全吻合，object 已由 contract 277 消费并留有专用 consumer marker；legacy exit source 与 B2 source 已由 core 消费、`formal_hc_active=0`、occupied 恰减一、frozen 恰加一、m277 五字段与 immutable receipt 完全一致。随后它只把 detailed receipt 的 `consumed` 从 0 改为 1。B2 ACK 或 m277 记账字段本身不能冒充真实 operation。真实离任发生在 refill-policy 选择之前；route C 不会撤销既成离任，但必须让 exit/B2 source 保持未消费，且不得再次 revoke。typed RED 或 stale tuple 则不得启动 native exit、发布或消费。

## 5. ABI 与 readiness

公开入口：

```text
{PREFIX}_arm_from_m274_effect = {{ TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }}
{PREFIX}_request_closed_pip_exit_effect = {{ TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }}
{PREFIX}_publish_to_workforce_m277_effect = yes
{PREFIX}_consume_after_m277_effect = {{ TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }}
```

当前 core 已在 #274 exact post-consume seam 调用 arm；request/consume 与 #277 玩家事件等待 publish ACK 的链仍待另一工作包闭合，所以本包仍是 `core-wired / static-ready / not live`。正常离职对同一 carrier 的合法撤任会由 exact normal-exit authorization branch 识别，不再同时写 unexpected end；它仍不能冒充失败 PIP #277。role/strategy invalidation 则只发布 quality=4 的 exclusion，不改 gold/hours/HC。L0 只证明 deterministic generation、BOM、九语结构、真实 native action/callback 门、D+1 分阶段、不可 caller 伪造、B2/HC 守恒与详细 receipt 合同；loader、存读档、paused MCP snapshot 与多周期实机仍待批量验收。
"""
    )


def validate_contract() -> None:
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("isolated exit fact must not claim live readiness")
    if M274_POSITION_TYPE_ID != 3_612_741:
        raise ValueError("#274 native position identity drifted")
    if POSITION_CARRIER_TYPE_ID == M274_POSITION_TYPE_ID:
        raise ValueError("the persistent carrier must not impersonate the bounded #274 type")
    if len(LANGUAGES) != 9 or len(set(LANGUAGES)) != 9:
        raise ValueError("exactly nine unique CK3 localization projections are required")


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered: dict[Path, bytes] = {
        EFFECTS_PATH: render_effects(),
        EVENTS_PATH: render_events(),
        POSITION_PATH: render_court_position(),
        SPEC_PATH: render_spec(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT
            / "localization"
            / language
            / LOC_BASENAME.format(language=language)
        ] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [
        path
        for path, payload in rendered.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if args.check:
        if stale:
            print("RED: stale Workforce exit-fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print(
            f"GREEN: {len(rendered)} Workforce exit-fact files are current "
            f"({READINESS})"
        )
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce exit-fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
