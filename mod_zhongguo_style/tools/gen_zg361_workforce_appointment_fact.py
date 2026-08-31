#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the native Workforce #274 appointment-fact producer.

The package deliberately owns a single narrow vertical.  It performs one real
CK3 court-position appointment, waits for the engine's
``on_court_position_received`` callback, verifies the resulting holder and
employer, seals one immutable receipt, and only then submits the three legacy
Workforce position aliases.  Caller-supplied booleans, position identifiers,
receipt identifiers, and hashes are not part of the public ABI.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE -- edit tools/gen_zg361_workforce_appointment_fact.py\n"

PREFIX: Final[str] = "zg361_workforce_appointment_fact"
NAMESPACE: Final[str] = "zg361workforceappointmentfact"
POSITION_KEY: Final[str] = f"{PREFIX}_court_position"
POSITION_TYPE_ID: Final[int] = 3_612_741
SOURCE_KIND_COURT_POSITION: Final[int] = 1
AUDIT_EVENT_ID: Final[int] = 9001

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
# This bounded probationary position is intentionally hidden outside the exact
# native request tick.  It is nevertheless a real CK3 court position: the
# engine owns appointment, employer/holder state, revocation and invalidation.
{POSITION_KEY} = {{
    sort_order = 361
    max_available_positions = 1
    minimum_rank = duchy
    skill = stewardship

    opinion = {{ value = 0 }}
    aptitude_level_breakpoints = {{ 20 40 60 80 }}
    aptitude = {{
        value = stewardship
    }}

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
            has_variable = {PREFIX}_eligibility_open
            var:{PREFIX}_eligibility_open = 1
            var:{PREFIX}_pending_owner = scope:liege
        }}
    }}

    valid_character = {{
        scope:employee = {{
            is_alive = yes
            is_landed = yes
            liege = scope:liege
            OR = {{
                AND = {{
                    has_variable = {PREFIX}_eligibility_open
                    var:{PREFIX}_eligibility_open = 1
                    var:{PREFIX}_pending_owner = scope:liege
                }}
                AND = {{
                    has_variable = {PREFIX}_position_active
                    var:{PREFIX}_position_active = 1
                    has_variable = {PREFIX}_receipt_owner
                    var:{PREFIX}_receipt_owner = scope:liege
                }}
            }}
        }}
    }}

    revoke_cost = {{}}
    salary = {{ gold = 0 }}
    received_salary = {{ gold = 0 }}

    on_court_position_received = {{
        scope:employee = {{
            {PREFIX}_on_native_position_received_effect = yes
        }}
    }}
    on_court_position_revoked = {{
        scope:employee = {{
            {PREFIX}_on_native_position_ended_effect = {{ END_REASON = 1 }}
        }}
    }}
    on_court_position_invalidated = {{
        scope:employee = {{
            {PREFIX}_on_native_position_ended_effect = {{ END_REASON = 2 }}
        }}
    }}
    on_court_position_vacated = {{
        scope:employee = {{
            {PREFIX}_on_native_position_ended_effect = {{ END_REASON = 3 }}
        }}
    }}

    # The position is only opened by the exact package request.  The vanilla
    # AI must never independently use it as a generic court vacancy.
    ai_position_score = {{ value = -1000 }}
    ai_candidate_score = {{ value = -1000 }}
}}
"""
    )


def render_effects() -> bytes:
    return generated(
        f"""
# Public subject-scope ABI (same tuple as Workforce #274):
# {PREFIX}_m274_appoint_and_consume_effect = {{
#   TICKET_OWNER = <appointing manager> TICKET_SUBJECT = <subject>
#   TICKET_CYCLE = <cycle> TICKET_CASE = <case>
# }}
#
# Status: 2=idempotent complete, 4=typed RED, 5=real native fact is waiting,
# 6=real appointment fact and Workforce #274 were both consumed.

{PREFIX}_clear_pending_intent_effect = {{
    remove_variable = {PREFIX}_pending_open
    remove_variable = {PREFIX}_pending_owner
    remove_variable = {PREFIX}_pending_subject
    remove_variable = {PREFIX}_pending_cycle
    remove_variable = {PREFIX}_pending_case
    remove_variable = {PREFIX}_pending_state
    remove_variable = {PREFIX}_pending_title
    remove_variable = {PREFIX}_pending_title_tier
    remove_variable = {PREFIX}_pending_hc_case
    remove_variable = {PREFIX}_pending_hc_reserved
    remove_variable = {PREFIX}_pending_offer_object
    remove_variable = {PREFIX}_pending_candidate_object
    remove_variable = {PREFIX}_eligibility_open
}}

# This callback is invoked only by the custom court position's native
# on_court_position_received hook.  No public caller can supply a success bit.
{PREFIX}_on_native_position_received_effect = {{
    if = {{
        limit = {{
            has_variable = {PREFIX}_pending_open
            var:{PREFIX}_pending_open = 1
            has_variable = {PREFIX}_pending_owner
            has_variable = {PREFIX}_pending_subject
            var:{PREFIX}_pending_subject = this
            scope:liege = var:{PREFIX}_pending_owner
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = scope:liege
            }}
        }}
        set_variable = {{ name = {PREFIX}_native_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_native_callback_owner value = scope:liege }}
        set_variable = {{ name = {PREFIX}_native_callback_subject value = this }}
        set_variable = {{ name = {PREFIX}_native_callback_position_type_id value = {POSITION_TYPE_ID} }}
        set_variable = {{ name = {PREFIX}_position_active value = 1 }}
        trigger_event = {{ id = {NAMESPACE}.{AUDIT_EVENT_ID} days = 1 }}
    }}
}}

{PREFIX}_on_native_position_ended_effect = {{
    set_variable = {{ name = {PREFIX}_position_active value = 0 }}
    set_variable = {{ name = {PREFIX}_position_end_reason value = $END_REASON$ }}
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
        }}
        set_variable = {{ name = {PREFIX}_receipt_position_still_active value = 0 }}
    }}
}}

# The custom office is a bounded native appointment carrier, not a permanent
# second job.  Only this private effect may release it, and it records that the
# disappearance was package-owned so a natural invalidation can never be
# mistaken for a successful settlement release.
{PREFIX}_release_bounded_position_effect = {{
    remove_variable = {PREFIX}_release_command_dispatched
    remove_variable = {PREFIX}_release_command_owner
    if = {{
        limit = {{
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = $EXPECTED_OWNER$
            }}
        }}
        set_variable = {{ name = {PREFIX}_settlement_release_requested value = 1 }}
        set_variable = {{ name = {PREFIX}_settlement_release_reason value = $RELEASE_REASON$ }}
        set_variable = {{ name = {PREFIX}_release_command_dispatched value = 1 }}
        set_variable = {{ name = {PREFIX}_release_command_owner value = $EXPECTED_OWNER$ }}
        revoke_court_position = {POSITION_KEY}
    }}
    if = {{
        limit = {{
            has_variable = {PREFIX}_release_command_dispatched
            var:{PREFIX}_release_command_dispatched = 1
            var:{PREFIX}_release_command_owner = $EXPECTED_OWNER$
            NOT = {{ has_court_position = {POSITION_KEY} }}
        }}
        set_variable = {{ name = {PREFIX}_position_active value = 0 }}
        if = {{
            limit = {{
                has_variable = {PREFIX}_receipt_active
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_owner = $EXPECTED_OWNER$
            }}
            set_variable = {{ name = {PREFIX}_receipt_position_still_active value = 0 }}
            set_variable = {{ name = {PREFIX}_receipt_position_released_by_package value = 1 }}
            set_variable = {{ name = {PREFIX}_receipt_position_release_reason value = $RELEASE_REASON$ }}
        }}
        else = {{
            set_variable = {{ name = {PREFIX}_pending_position_released_by_package value = 1 }}
        }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 5 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27407 }}
    }}
}}

# Seal a receipt only after both the native callback and the live
# holder/employer postcondition exist.  The real title and the #266 formal-HC
# reservation are copied from the exact pending tuple, never supplied by a
# caller.  A sealed but not-yet-published receipt is retried without re-signing.
{PREFIX}_seal_and_publish_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 4
            var:{PREFIX}_receipt_result = 1
            var:{PREFIX}_receipt_position_type_id = {POSITION_TYPE_ID}
            var:{PREFIX}_receipt_position_source_kind = {SOURCE_KIND_COURT_POSITION}
            var:{PREFIX}_receipt_native_callback_seen = 1
            var:{PREFIX}_receipt_native_holder_postcondition_seen = 1
        }}
        if = {{
            limit = {{ var:{PREFIX}_receipt_published = 0 }}
            if = {{
                limit = {{
                    OR = {{
                        $TICKET_SUBJECT$ = {{
                            has_court_position = {POSITION_KEY}
                            is_court_position_employer = {{
                                court_position = {POSITION_KEY}
                                who = $TICKET_OWNER$
                            }}
                            primary_title = var:{PREFIX}_receipt_title
                            var:{PREFIX}_receipt_title = {{ holder = $TICKET_SUBJECT$ }}
                        }}
                        AND = {{
                            var:{PREFIX}_receipt_position_still_active = 0
                            var:{PREFIX}_receipt_position_released_by_package = 1
                            $TICKET_SUBJECT$ = {{
                                NOT = {{ has_court_position = {POSITION_KEY} }}
                                primary_title = var:{PREFIX}_receipt_title
                                var:{PREFIX}_receipt_title = {{ holder = $TICKET_SUBJECT$ }}
                            }}
                        }}
                    }}
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
                }}
                zg361_we_submit_ad_appointment_receipt_effect = {{
                    TICKET_OWNER = $TICKET_OWNER$
                    TICKET_SUBJECT = $TICKET_SUBJECT$
                    TICKET_CYCLE = $TICKET_CYCLE$
                    TICKET_CASE = $TICKET_CASE$
                    APPOINTING_OWNER = $TICKET_OWNER$
                    APPOINTMENT_CONFIRMED = 1
                    POSITION_TYPE_ID = {POSITION_TYPE_ID}
                    POSITION_RECEIPT_ID = var:{PREFIX}_receipt_id
                    POSITION_RECEIPT_HASH = var:{PREFIX}_receipt_hash
                }}
                if = {{
                    limit = {{
                        has_variable = zg361_we_adapter_status
                        var:zg361_we_adapter_status = 1
                        var:zg361_we_ad_external_position_type_id = {POSITION_TYPE_ID}
                        var:zg361_we_ad_external_position_receipt_id = var:{PREFIX}_receipt_id
                        var:zg361_we_ad_external_position_receipt_hash = var:{PREFIX}_receipt_hash
                        var:zg361_we_ad_appointment_receipt_owner = $TICKET_OWNER$
                        var:zg361_we_ad_appointment_receipt_subject = $TICKET_SUBJECT$
                        var:zg361_we_ad_appointment_receipt_cycle = $TICKET_CYCLE$
                        var:zg361_we_ad_appointment_receipt_case = $TICKET_CASE$
                        var:zg361_we_ad_appointment_receipt_state = 4
                    }}
                    set_variable = {{ name = {PREFIX}_receipt_published value = 1 }}
                    set_variable = {{ name = {PREFIX}_status value = 1 }}
                }}
                else = {{
                    set_variable = {{ name = {PREFIX}_status value = 5 }}
                    set_variable = {{ name = {PREFIX}_red_code value = 27405 }}
                }}
            }}
            else = {{
                set_variable = {{ name = {PREFIX}_status value = 4 }}
                set_variable = {{ name = {PREFIX}_red_code value = 27404 }}
            }}
        }}
        else_if = {{
            limit = {{ var:{PREFIX}_receipt_published = 1 }}
            set_variable = {{ name = {PREFIX}_status value = 1 }}
        }}
        else = {{
            set_variable = {{ name = {PREFIX}_status value = 4 }}
            set_variable = {{ name = {PREFIX}_red_code value = 27404 }}
        }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_pending_open
            var:{PREFIX}_pending_open = 1
            var:{PREFIX}_pending_owner = $TICKET_OWNER$
            var:{PREFIX}_pending_subject = $TICKET_SUBJECT$
            var:{PREFIX}_pending_cycle = $TICKET_CYCLE$
            var:{PREFIX}_pending_case = $TICKET_CASE$
            var:{PREFIX}_pending_state = 4
            has_variable = {PREFIX}_native_callback_seen
            var:{PREFIX}_native_callback_seen = 1
            var:{PREFIX}_native_callback_owner = $TICKET_OWNER$
            var:{PREFIX}_native_callback_subject = $TICKET_SUBJECT$
            var:{PREFIX}_native_callback_position_type_id = {POSITION_TYPE_ID}
            $TICKET_SUBJECT$ = {{
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = $TICKET_OWNER$
                }}
                primary_title = var:{PREFIX}_pending_title
                var:{PREFIX}_pending_title = {{ holder = $TICKET_SUBJECT$ }}
                var:zg361_we_m266_hc_reservation_active = 1
                var:{PREFIX}_pending_hc_case = var:zg361_we_m266_hc_receipt
                var:{PREFIX}_pending_hc_reserved <= var:zg361_ch_hc_reserved
                var:zg361_we_m266_object_owner = $TICKET_OWNER$
                var:zg361_we_m266_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m266_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m266_object_case = $TICKET_CASE$
                var:zg361_we_m266_object_consumed = 1
                var:zg361_we_m272_object_owner = $TICKET_OWNER$
                var:zg361_we_m272_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m272_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m272_object_case = $TICKET_CASE$
                var:zg361_we_m272_object_consumed = 1
                var:zg361_we_m273_object_owner = $TICKET_OWNER$
                var:zg361_we_m273_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m273_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m273_object_case = $TICKET_CASE$
                var:zg361_we_m273_object_consumed = 1
                var:{PREFIX}_pending_offer_object = var:zg361_we_m272_object_id
                var:{PREFIX}_pending_candidate_object = var:zg361_we_m273_object_id
                var:zg361_we_m272_offer_candidate = $TICKET_SUBJECT$
                var:zg361_we_m273_candidate_fingerprint = $TICKET_SUBJECT$
            }}
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
        }}
        set_variable = {{ name = {PREFIX}_receipt_active value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_consumed value = 0 }}
        set_variable = {{ name = {PREFIX}_receipt_published value = 0 }}
        set_variable = {{ name = {PREFIX}_receipt_owner value = $TICKET_OWNER$ }}
        set_variable = {{ name = {PREFIX}_receipt_subject value = $TICKET_SUBJECT$ }}
        set_variable = {{ name = {PREFIX}_receipt_cycle value = $TICKET_CYCLE$ }}
        set_variable = {{ name = {PREFIX}_receipt_case value = $TICKET_CASE$ }}
        set_variable = {{ name = {PREFIX}_receipt_state value = 4 }}
        set_variable = {{ name = {PREFIX}_receipt_result value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_position_type_id value = {POSITION_TYPE_ID} }}
        set_variable = {{ name = {PREFIX}_receipt_position_source_kind value = {SOURCE_KIND_COURT_POSITION} }}
        set_variable = {{ name = {PREFIX}_receipt_title value = var:{PREFIX}_pending_title }}
        set_variable = {{ name = {PREFIX}_receipt_title_tier value = var:{PREFIX}_pending_title_tier }}
        set_variable = {{ name = {PREFIX}_receipt_title_holder value = $TICKET_SUBJECT$ }}
        set_variable = {{ name = {PREFIX}_receipt_hc_case value = var:{PREFIX}_pending_hc_case }}
        set_variable = {{ name = {PREFIX}_receipt_hc_reserved_source value = var:{PREFIX}_pending_hc_reserved }}
        set_variable = {{ name = {PREFIX}_receipt_offer_object value = var:{PREFIX}_pending_offer_object }}
        set_variable = {{ name = {PREFIX}_receipt_candidate_object value = var:{PREFIX}_pending_candidate_object }}
        set_variable = {{ name = {PREFIX}_receipt_native_employer value = $TICKET_OWNER$ }}
        set_variable = {{ name = {PREFIX}_receipt_native_callback_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_native_holder_postcondition_seen value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_position_still_active value = 1 }}
        set_variable = {{ name = {PREFIX}_receipt_id value = {{ value = $TICKET_CASE$ multiply = 1000 add = 274 }} }}
        set_variable = {{ name = {PREFIX}_receipt_hash value = {{ value = $TICKET_CASE$ multiply = 100000 add = $TICKET_CYCLE$ multiply = 10 add = {SOURCE_KIND_COURT_POSITION} }} }}
        {PREFIX}_clear_pending_intent_effect = yes
        {PREFIX}_seal_and_publish_effect = {{
            TICKET_OWNER = $TICKET_OWNER$
            TICKET_SUBJECT = $TICKET_SUBJECT$
            TICKET_CYCLE = $TICKET_CYCLE$
            TICKET_CASE = $TICKET_CASE$
        }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27404 }}
    }}
}}

# Begin the one real business action.  The intent tuple opens eligibility but
# is not a receipt and never writes a Workforce external alias.  If vanilla's
# can_appoint preflight fails, it is removed in the same effect.
{PREFIX}_request_native_appointment_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
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
            this = $TICKET_SUBJECT$
            $TICKET_OWNER$ = {{
                zg361_is_celestial_liege_trigger = yes
                highest_held_title_tier >= tier_duchy
            }}
            $TICKET_SUBJECT$ = {{
                is_alive = yes
                is_landed = yes
                liege = $TICKET_OWNER$
                primary_title = {{ holder = $TICKET_SUBJECT$ }}
                NOT = {{ has_court_position = {POSITION_KEY} }}
                has_variable = zg361_we_m266_hc_reservation_active
                var:zg361_we_m266_hc_reservation_active = 1
                has_variable = zg361_we_m266_hc_receipt
                var:zg361_we_m266_hc_receipt = $TICKET_CASE$
                has_variable = zg361_ch_hc_reserved
                var:zg361_ch_hc_reserved >= 1
                has_variable = zg361_we_m266_object_id
                has_variable = zg361_we_m272_object_id
                has_variable = zg361_we_m273_object_id
                var:zg361_we_m266_object_owner = $TICKET_OWNER$
                var:zg361_we_m266_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m266_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m266_object_case = $TICKET_CASE$
                var:zg361_we_m266_object_consumed = 1
                var:zg361_we_m272_object_owner = $TICKET_OWNER$
                var:zg361_we_m272_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m272_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m272_object_case = $TICKET_CASE$
                var:zg361_we_m272_object_consumed = 1
                var:zg361_we_m273_object_owner = $TICKET_OWNER$
                var:zg361_we_m273_object_subject = $TICKET_SUBJECT$
                var:zg361_we_m273_object_cycle = $TICKET_CYCLE$
                var:zg361_we_m273_object_case = $TICKET_CASE$
                var:zg361_we_m273_object_consumed = 1
                var:zg361_we_m272_offer_candidate = $TICKET_SUBJECT$
                var:zg361_we_m273_candidate_fingerprint = $TICKET_SUBJECT$
                OR = {{
                    NOT = {{ has_variable = {PREFIX}_pending_open }}
                    var:{PREFIX}_pending_open = 0
                }}
                OR = {{
                    NOT = {{ has_variable = {PREFIX}_receipt_active }}
                    var:{PREFIX}_receipt_active = 0
                }}
                NOT = {{
                    AND = {{
                        has_variable = {PREFIX}_native_attempt_dispatched
                        var:{PREFIX}_native_attempt_dispatched = 1
                        var:{PREFIX}_native_attempt_owner = $TICKET_OWNER$
                        var:{PREFIX}_native_attempt_subject = $TICKET_SUBJECT$
                        var:{PREFIX}_native_attempt_cycle = $TICKET_CYCLE$
                        var:{PREFIX}_native_attempt_case = $TICKET_CASE$
                    }}
                }}
            }}
        }}
        set_variable = {{ name = {PREFIX}_pending_open value = 1 }}
        set_variable = {{ name = {PREFIX}_pending_owner value = $TICKET_OWNER$ }}
        set_variable = {{ name = {PREFIX}_pending_subject value = $TICKET_SUBJECT$ }}
        set_variable = {{ name = {PREFIX}_pending_cycle value = $TICKET_CYCLE$ }}
        set_variable = {{ name = {PREFIX}_pending_case value = $TICKET_CASE$ }}
        set_variable = {{ name = {PREFIX}_pending_state value = 4 }}
        set_variable = {{ name = {PREFIX}_pending_title value = primary_title }}
        set_variable = {{ name = {PREFIX}_pending_title_tier value = primary_title.tier }}
        set_variable = {{ name = {PREFIX}_pending_hc_case value = var:zg361_we_m266_hc_receipt }}
        set_variable = {{ name = {PREFIX}_pending_hc_reserved value = var:zg361_ch_hc_reserved }}
        set_variable = {{ name = {PREFIX}_pending_offer_object value = var:zg361_we_m272_object_id }}
        set_variable = {{ name = {PREFIX}_pending_candidate_object value = var:zg361_we_m273_object_id }}
        set_variable = {{ name = {PREFIX}_eligibility_open value = 1 }}
        remove_variable = {PREFIX}_native_callback_seen
        remove_variable = {PREFIX}_native_callback_owner
        remove_variable = {PREFIX}_native_callback_subject
        remove_variable = {PREFIX}_native_callback_position_type_id
        $TICKET_OWNER$ = {{ set_variable = {{ name = {PREFIX}_window_open value = 1 }} }}
        if = {{
            limit = {{
                $TICKET_OWNER$ = {{
                    can_appoint_char_to_court_position = {{
                        CHAR = $TICKET_SUBJECT$
                        COURT_POS = {POSITION_KEY}
                    }}
                }}
            }}
            set_variable = {{ name = {PREFIX}_native_attempt_dispatched value = 1 }}
            set_variable = {{ name = {PREFIX}_native_attempt_owner value = $TICKET_OWNER$ }}
            set_variable = {{ name = {PREFIX}_native_attempt_subject value = $TICKET_SUBJECT$ }}
            set_variable = {{ name = {PREFIX}_native_attempt_cycle value = $TICKET_CYCLE$ }}
            set_variable = {{ name = {PREFIX}_native_attempt_case value = $TICKET_CASE$ }}
            $TICKET_OWNER$ = {{
                appoint_court_position = {{
                    recipient = $TICKET_SUBJECT$
                    court_position = {POSITION_KEY}
                }}
            }}
            if = {{
                limit = {{
                    has_variable = {PREFIX}_native_callback_seen
                    var:{PREFIX}_native_callback_seen = 1
                    has_court_position = {POSITION_KEY}
                    is_court_position_employer = {{
                        court_position = {POSITION_KEY}
                        who = $TICKET_OWNER$
                    }}
                }}
                {PREFIX}_seal_and_publish_effect = {{
                    TICKET_OWNER = $TICKET_OWNER$
                    TICKET_SUBJECT = $TICKET_SUBJECT$
                    TICKET_CYCLE = $TICKET_CYCLE$
                    TICKET_CASE = $TICKET_CASE$
                }}
            }}
            else = {{
                set_variable = {{ name = {PREFIX}_status value = 5 }}
                set_variable = {{ name = {PREFIX}_red_code value = 27403 }}
                trigger_event = {{ id = {NAMESPACE}.{AUDIT_EVENT_ID} days = 1 }}
            }}
        }}
        else = {{
            {PREFIX}_clear_pending_intent_effect = yes
            set_variable = {{ name = {PREFIX}_status value = 4 }}
            set_variable = {{ name = {PREFIX}_red_code value = 27402 }}
        }}
        $TICKET_OWNER$ = {{ remove_variable = {PREFIX}_window_open }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_pending_open
            var:{PREFIX}_pending_open = 1
            var:{PREFIX}_pending_owner = $TICKET_OWNER$
            var:{PREFIX}_pending_subject = $TICKET_SUBJECT$
            var:{PREFIX}_pending_cycle = $TICKET_CYCLE$
            var:{PREFIX}_pending_case = $TICKET_CASE$
            has_variable = {PREFIX}_native_attempt_dispatched
            var:{PREFIX}_native_attempt_dispatched = 1
            var:{PREFIX}_native_attempt_owner = $TICKET_OWNER$
            var:{PREFIX}_native_attempt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_native_attempt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_native_attempt_case = $TICKET_CASE$
        }}
        set_variable = {{ name = {PREFIX}_status value = 5 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27403 }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 4
        }}
        {PREFIX}_seal_and_publish_effect = {{
            TICKET_OWNER = $TICKET_OWNER$
            TICKET_SUBJECT = $TICKET_SUBJECT$
            TICKET_CYCLE = $TICKET_CYCLE$
            TICKET_CASE = $TICKET_CASE$
        }}
    }}
    else = {{
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27401 }}
    }}
}}

# After the native receipt is published, the existing Workforce #274 route is
# the sole owner of gold/HC settlement.  Ordinarily the probationary position
# is released after that route ACKs.  A D+1 audit may already have released the
# same verified position to keep the slot bounded; the immutable receipt then
# remains consumable, while an unrelated invalidation never qualifies.
{PREFIX}_consume_workforce_m274_effect = {{
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_published = 1
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 4
            var:{PREFIX}_receipt_native_callback_seen = 1
            var:{PREFIX}_receipt_native_holder_postcondition_seen = 1
            OR = {{
                AND = {{
                    var:{PREFIX}_receipt_position_still_active = 1
                    has_court_position = {POSITION_KEY}
                    is_court_position_employer = {{
                        court_position = {POSITION_KEY}
                        who = $TICKET_OWNER$
                    }}
                }}
                AND = {{
                    var:{PREFIX}_receipt_position_still_active = 0
                    var:{PREFIX}_receipt_position_released_by_package = 1
                    NOT = {{ has_court_position = {POSITION_KEY} }}
                }}
            }}
        }}
        if = {{
            limit = {{
                OR = {{
                    AND = {{
                        has_variable = {PREFIX}_workforce_consumer_ack
                        var:{PREFIX}_workforce_consumer_ack = 1
                    }}
                    AND = {{
                        has_variable = zg361_we_m274_business_object_created
                        var:zg361_we_m274_business_object_created = 1
                        var:zg361_we_m274_object_owner = $TICKET_OWNER$
                        var:zg361_we_m274_object_subject = $TICKET_SUBJECT$
                        var:zg361_we_m274_object_cycle = $TICKET_CYCLE$
                        var:zg361_we_m274_object_case = $TICKET_CASE$
                        var:zg361_we_m274_object_state = 4
                        var:zg361_we_m274_object_consumed = 1
                        var:zg361_we_m274_native_appointment_confirmed = 1
                        var:zg361_we_m274_appointed_character = $TICKET_SUBJECT$
                        var:zg361_we_m274_position_type_id = var:{PREFIX}_receipt_position_type_id
                        var:zg361_we_m274_position_receipt_id = var:{PREFIX}_receipt_id
                        var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_receipt_hash
                        var:zg361_we_ad_external_appointment_consumed = 1
                        var:zg361_we_ad_external_appointment_ready = 0
                    }}
                }}
            }}
            set_variable = {{ name = {PREFIX}_workforce_consumer_ack value = 1 }}
        }}
        else = {{
            zg361_we_m274_route_a_effect = {{
                TICKET_OWNER = $TICKET_OWNER$
                TICKET_SUBJECT = $TICKET_SUBJECT$
                TICKET_CYCLE = $TICKET_CYCLE$
                TICKET_CASE = $TICKET_CASE$
            }}
            if = {{
                limit = {{
                    has_variable = zg361_we_runtime_applied
                    var:zg361_we_runtime_applied = 1
                    var:zg361_we_m274_native_appointment_confirmed = 1
                    var:zg361_we_m274_appointed_character = $TICKET_SUBJECT$
                    var:zg361_we_m274_position_type_id = var:{PREFIX}_receipt_position_type_id
                    var:zg361_we_m274_position_receipt_id = var:{PREFIX}_receipt_id
                    var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_receipt_hash
                    var:zg361_we_ad_external_appointment_consumed = 1
                    var:zg361_we_ad_external_appointment_ready = 0
                }}
                set_variable = {{ name = {PREFIX}_workforce_consumer_ack value = 1 }}
            }}
        }}
        if = {{
            limit = {{
                has_variable = {PREFIX}_workforce_consumer_ack
                var:{PREFIX}_workforce_consumer_ack = 1
            }}
            if = {{
                limit = {{
                    var:{PREFIX}_receipt_position_still_active = 1
                    has_court_position = {POSITION_KEY}
                    is_court_position_employer = {{
                        court_position = {POSITION_KEY}
                        who = $TICKET_OWNER$
                    }}
                }}
                {PREFIX}_release_bounded_position_effect = {{
                    EXPECTED_OWNER = $TICKET_OWNER$
                    RELEASE_REASON = 1
                }}
            }}
            if = {{
                limit = {{
                    var:{PREFIX}_receipt_position_still_active = 0
                    var:{PREFIX}_receipt_position_released_by_package = 1
                    NOT = {{ has_court_position = {POSITION_KEY} }}
                }}
                set_variable = {{ name = {PREFIX}_receipt_position_release_joined_by_consumer value = 1 }}
                set_variable = {{ name = {PREFIX}_receipt_consumed value = 1 }}
                set_variable = {{ name = {PREFIX}_receipt_consumed_operation value = 274 }}
                set_variable = {{ name = {PREFIX}_status value = 6 }}
                set_variable = {{ name = zg361_we_runtime_applied value = 1 }}
            }}
            else = {{
                remove_variable = zg361_we_runtime_applied
                set_variable = {{ name = {PREFIX}_status value = 5 }}
                set_variable = {{ name = {PREFIX}_red_code value = 27407 }}
            }}
        }}
        else = {{
            remove_variable = zg361_we_runtime_applied
            set_variable = {{ name = {PREFIX}_status value = 5 }}
            set_variable = {{ name = {PREFIX}_red_code value = 27406 }}
        }}
    }}
    else = {{
        remove_variable = zg361_we_runtime_applied
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27406 }}
    }}
}}

{PREFIX}_m274_appoint_and_consume_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    remove_variable = zg361_we_runtime_applied
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 1
            var:{PREFIX}_receipt_owner = $TICKET_OWNER$
            var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
            var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
            var:{PREFIX}_receipt_case = $TICKET_CASE$
            var:{PREFIX}_receipt_state = 4
            var:{PREFIX}_receipt_result = 1
            var:zg361_we_m274_native_appointment_confirmed = 1
            var:zg361_we_m274_position_receipt_id = var:{PREFIX}_receipt_id
            var:zg361_we_m274_position_receipt_hash = var:{PREFIX}_receipt_hash
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else = {{
        {PREFIX}_request_native_appointment_effect = {{
            TICKET_OWNER = $TICKET_OWNER$
            TICKET_SUBJECT = $TICKET_SUBJECT$
            TICKET_CYCLE = $TICKET_CYCLE$
            TICKET_CASE = $TICKET_CASE$
        }}
        if = {{
            limit = {{
                has_variable = {PREFIX}_receipt_active
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_consumed = 0
                var:{PREFIX}_receipt_published = 1
                var:{PREFIX}_receipt_owner = $TICKET_OWNER$
                var:{PREFIX}_receipt_subject = $TICKET_SUBJECT$
                var:{PREFIX}_receipt_cycle = $TICKET_CYCLE$
                var:{PREFIX}_receipt_case = $TICKET_CASE$
            }}
            {PREFIX}_consume_workforce_m274_effect = {{
                TICKET_OWNER = $TICKET_OWNER$
                TICKET_SUBJECT = $TICKET_SUBJECT$
                TICKET_CYCLE = $TICKET_CYCLE$
                TICKET_CASE = $TICKET_CASE$
            }}
        }}
    }}
}}

# D+1 is only a reconciliation attempt for callback ordering or save/load.  It
# cannot turn the request intent into success without the native callback and
# live position postcondition.  A later central retry of the public wrapper is
# required to consume #274 if publication finished after the original tick.
{PREFIX}_audit_pending_effect = {{
    remove_variable = {PREFIX}_status
    remove_variable = {PREFIX}_red_code
    if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 1
            var:{PREFIX}_receipt_subject = this
        }}
        set_variable = {{ name = {PREFIX}_status value = 2 }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_published = 1
            var:{PREFIX}_receipt_subject = this
        }}
        if = {{
            limit = {{
                var:{PREFIX}_receipt_position_still_active = 1
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_receipt_owner
                }}
            }}
            {PREFIX}_release_bounded_position_effect = {{
                EXPECTED_OWNER = var:{PREFIX}_receipt_owner
                RELEASE_REASON = 2
            }}
        }}
        if = {{
            limit = {{
                var:{PREFIX}_receipt_position_still_active = 0
                var:{PREFIX}_receipt_position_released_by_package = 1
                NOT = {{ has_court_position = {POSITION_KEY} }}
            }}
            set_variable = {{ name = {PREFIX}_status value = 5 }}
        }}
        else = {{
            set_variable = {{ name = {PREFIX}_status value = 4 }}
            set_variable = {{ name = {PREFIX}_red_code value = 27407 }}
        }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_pending_open
            var:{PREFIX}_pending_open = 1
            has_variable = {PREFIX}_pending_owner
            has_variable = {PREFIX}_pending_subject
            has_variable = {PREFIX}_pending_cycle
            has_variable = {PREFIX}_pending_case
            var:{PREFIX}_pending_subject = this
            has_variable = {PREFIX}_native_callback_seen
            var:{PREFIX}_native_callback_seen = 1
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = var:{PREFIX}_pending_owner
            }}
        }}
        {PREFIX}_seal_and_publish_effect = {{
            TICKET_OWNER = var:{PREFIX}_pending_owner
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{PREFIX}_pending_cycle
            TICKET_CASE = var:{PREFIX}_pending_case
        }}
        if = {{
            limit = {{
                NOT = {{
                    AND = {{
                        has_variable = {PREFIX}_receipt_active
                        var:{PREFIX}_receipt_active = 1
                        var:{PREFIX}_receipt_subject = this
                    }}
                }}
                has_variable = {PREFIX}_pending_open
                var:{PREFIX}_pending_open = 1
                has_variable = {PREFIX}_pending_owner
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_pending_owner
                }}
            }}
            {PREFIX}_release_bounded_position_effect = {{
                EXPECTED_OWNER = var:{PREFIX}_pending_owner
                RELEASE_REASON = 3
            }}
            {PREFIX}_clear_pending_intent_effect = yes
            set_variable = {{ name = {PREFIX}_status value = 4 }}
            if = {{
                limit = {{ NOT = {{ has_variable = {PREFIX}_red_code }} }}
                set_variable = {{ name = {PREFIX}_red_code value = 27404 }}
            }}
        }}
        if = {{
            limit = {{
                has_variable = {PREFIX}_receipt_active
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_subject = this
                var:{PREFIX}_receipt_position_still_active = 1
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_receipt_owner
                }}
            }}
            {PREFIX}_release_bounded_position_effect = {{
                EXPECTED_OWNER = var:{PREFIX}_receipt_owner
                RELEASE_REASON = 2
            }}
        }}
        if = {{
            limit = {{
                has_variable = {PREFIX}_receipt_active
                var:{PREFIX}_receipt_active = 1
                var:{PREFIX}_receipt_position_still_active = 0
                var:{PREFIX}_receipt_position_released_by_package = 1
                NOT = {{ has_court_position = {POSITION_KEY} }}
            }}
            set_variable = {{ name = {PREFIX}_status value = 5 }}
        }}
    }}
    else_if = {{
        limit = {{
            has_variable = {PREFIX}_receipt_active
            var:{PREFIX}_receipt_active = 1
            var:{PREFIX}_receipt_consumed = 0
            var:{PREFIX}_receipt_published = 0
            var:{PREFIX}_receipt_subject = this
            has_court_position = {POSITION_KEY}
            is_court_position_employer = {{
                court_position = {POSITION_KEY}
                who = var:{PREFIX}_receipt_owner
            }}
        }}
        {PREFIX}_seal_and_publish_effect = {{
            TICKET_OWNER = var:{PREFIX}_receipt_owner
            TICKET_SUBJECT = this
            TICKET_CYCLE = var:{PREFIX}_receipt_cycle
            TICKET_CASE = var:{PREFIX}_receipt_case
        }}
        if = {{
            limit = {{
                var:{PREFIX}_receipt_position_still_active = 1
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_receipt_owner
                }}
            }}
            {PREFIX}_release_bounded_position_effect = {{
                EXPECTED_OWNER = var:{PREFIX}_receipt_owner
                RELEASE_REASON = 2
            }}
        }}
        if = {{
            limit = {{
                var:{PREFIX}_receipt_position_still_active = 0
                var:{PREFIX}_receipt_position_released_by_package = 1
                NOT = {{ has_court_position = {POSITION_KEY} }}
            }}
            set_variable = {{ name = {PREFIX}_status value = 5 }}
        }}
    }}
    else = {{
        if = {{
            limit = {{
                has_variable = {PREFIX}_pending_open
                var:{PREFIX}_pending_open = 1
                has_variable = {PREFIX}_pending_owner
                has_court_position = {POSITION_KEY}
                is_court_position_employer = {{
                    court_position = {POSITION_KEY}
                    who = var:{PREFIX}_pending_owner
                }}
            }}
            {PREFIX}_release_bounded_position_effect = {{
                EXPECTED_OWNER = var:{PREFIX}_pending_owner
                RELEASE_REASON = 3
            }}
        }}
        {PREFIX}_clear_pending_intent_effect = yes
        set_variable = {{ name = {PREFIX}_status value = 4 }}
        set_variable = {{ name = {PREFIX}_red_code value = 27403 }}
    }}
}}
"""
    )


def render_events() -> bytes:
    return generated(
        f"""
namespace = {NAMESPACE}

# Reconcile native callback ordering and save/load without creating a success
# fact.  The effect remains fail-closed unless the engine callback and live
# holder/employer postcondition both exist.
{NAMESPACE}.{AUDIT_EVENT_ID} = {{
    type = character_event
    hidden = yes
    immediate = {{
        {PREFIX}_audit_pending_effect = yes
    }}
}}
"""
    )


def _localization_rows(language: str) -> dict[str, str]:
    english = {
        POSITION_KEY: "361 Probationary Appointment",
        f"{POSITION_KEY}_desc": (
            "A bounded probationary office for a real 361 recruitment settlement. CK3 creates it "
            "through native appointment; exact Workforce consumption or the next-day audit releases it."
        ),
    }
    chinese = {
        POSITION_KEY: "三六一试任编制",
        f"{POSITION_KEY}_desc": (
            "用于三六一招聘交割的有界试任岗位。CK3 原生任命成功后岗位才成立；"
            "同案 Workforce 回执消费后立即原生撤任，阻断时最迟由次日审计释放。"
        ),
    }
    return chinese if language == "simp_chinese" else english


def render_localization(language: str) -> bytes:
    rows = _localization_rows(language)
    body = [f"l_{language}:"]
    for key, value in rows.items():
        body.append(f' {key}:0 "{value.replace(chr(34), chr(92) + chr(34))}"')
    return localized("\n".join(body))


def render_spec() -> bytes:
    return generated(
        f"""
# Workforce #274 native appointment fact runtime contract

Status: **CK3 script static-ready; not loader-live or production-live.**

This independent package retires only the three legacy Native/Career
appointment aliases consumed by Workforce #274:

```text
zg361_we_ad_external_position_type_id
zg361_we_ad_external_position_receipt_id
zg361_we_ad_external_position_receipt_hash
```

## Truth source and business action

The public subject-scope ABI is:

```text
{PREFIX}_m274_appoint_and_consume_effect = {{
  TICKET_OWNER = <appointing owner>
  TICKET_SUBJECT = <subject>
  TICKET_CYCLE = <cycle>
  TICKET_CASE = <case>
}}
```

It accepts no caller claim that an appointment succeeded and accepts no
caller-provided position type, receipt id, hash, title or HC source.  It first
joins the current AD state-4 case with the consumed #266 requisition, #272
offer and #273 candidate objects.  The subject must be the appointing owner's
living landed direct vassal, must still hold the frozen primary title, and the
same #266 formal-HC reservation must remain active.

The only write action is CK3's native `appoint_court_position` for
`{POSITION_KEY}`.  Exact-build 1.19.0.6 source documentation in
`game/common/court_positions/types/_court_positions.info` says this effect
requires the recipient's liege to be the employer and exposes
`on_court_position_received` with `scope:liege` and `scope:employee`.
`game/common/scripted_triggers/00_court_position_triggers.txt` requires
`can_appoint_char_to_court_position` before the effect.  This package follows
both contracts.

The position is a zero-salary native **probationary settlement office** with
exactly one slot per employer.  It is visible/eligible in the appointment
picker only during the exact request tick, is restricted to celestial
duke-or-higher employers, and has a negative AI vacancy score so vanilla AI
cannot independently fill it.  The project's authorized celestial-manager AI
path may call the same exact ABI.  After Workforce #274 consumes the matching
receipt, the package immediately uses native `revoke_court_position` and
requires the position to be absent before marking its receipt consumed.  A
next-day one-shot audit releases an acknowledged native position even when the
adapter/consumer remains blocked.  The package records that release only when
its own verified revoke command made the position absent; native invalidation,
vacation or death cannot be relabelled as package-owned release.  One slot plus
this bounded teardown prevents permanent occupation or stacking.

`is_shown` provides a static picker-visibility boundary, not live UI proof.
Until a CK3 artifact checks every character/court surface, this package does
**not** claim zero UI impact: while a request is pending or externally blocked,
the held probationary position may still appear on a character detail or other
engine-owned position surface.  Successful same-tick settlement releases it;
otherwise the next-day audit attempts the same native release.  This is a
static lifecycle contract, not live proof that every CK3 surface hides it or
that the delayed event always executes on the target build.

This proves one real, bounded probationary court-position appointment and an
immutable historical receipt that the appointment occurred; it deliberately
does not claim the subject still holds that temporary office after settlement.
An exact-tuple dispatch tombstone prevents a replay from appointing again even
when callback evidence was lost and the audit had to fail closed.  It
does not prove promotion to an unrelated vanilla title, ministry or council
seat; the frozen primary title is provenance and a holder postcondition, not a
claim that this package granted that title.

## Receipt boundary

The request tuple is intent only.  It cannot set the three external aliases.
A receipt may be sealed only after all of these facts exist together:

1. the custom position's engine-owned `on_court_position_received` callback;
2. the subject actually has `{POSITION_KEY}`;
3. `is_court_position_employer` names the frozen appointing owner;
4. owner, subject, cycle, case and state still match the live AD case;
5. primary-title holder and the exact #266 HC lineage still match.

The immutable receipt freezes owner, subject, cycle, case, state=4, result=1,
position type id `{POSITION_TYPE_ID}`, source kind
`{SOURCE_KIND_COURT_POSITION}`, primary-title scope/tier/holder, #266 HC case
and reserved amount, #272 offer object and #273 candidate object, native
employer, callback/holder postconditions, deterministic id/hash, bounded native
release provenance, publication state and one-time consumption.
The id/hash are derived inside the package after the callback; they are not
cryptographic signatures and are never accepted from a caller.

Only then does the package call the existing strict
`zg361_we_submit_ad_appointment_receipt_effect`.  The three legacy aliases are
written by that existing adapter, not by the request action.  The wrapper calls
`zg361_we_m274_route_a_effect` only from a sealed native receipt: either the
verified position is still held, or this package's own bounded revoke already
released it.  It marks its receipt consumed only after Workforce copies the
same type/id/hash, sets `ad_external_appointment_consumed=1`, and the temporary
position is absent with package-owned release provenance.
Duplicate delivery is status 2 and does not appoint again;
wrong tuple, source collision or missing native postcondition is typed RED;
callback ordering may return status 5 and requires a later central retry.

## Integration and readiness

The existing Workforce #274 player option and authorized AI path still call
`zg361_we_m274_route_a_effect` directly: one call is in the generated player
event and one is in the generated authorized-AI effect.  The integration owner
must replace both calls with this package's wrapper using the same four
arguments.  No
Workforce generator, central runtime, runner, native bridge or provider file is
modified by this package.

Static generation/tests prove the command/callback/postcondition ordering,
five-field/source binding, absence of caller-supplied success, one-time receipt,
alias publication through the strict adapter, route-consumption join, BOM/key
parity and reproducibility.  There is no new CK3 loader log, paused snapshot,
save/load result, named MCP action/query or live employer/holder evidence.
Readiness therefore remains `ck3-script-static-ready-not-live`.

## External producer ledger replacement lines

The shared ledger is intentionally not edited by this isolated package.  Its
integration owner should replace the three Native/Career appointment debt rows
with the following status lines:

```text
zg361_we_ad_external_position_type_id — real custom court-position callback producer; static-ready, awaiting #274 caller wiring and loader/live proof
zg361_we_ad_external_position_receipt_id — sealed once after callback + employer/holder/title/HC postconditions; static-ready, awaiting #274 caller wiring and loader/live proof
zg361_we_ad_external_position_receipt_hash — same immutable receipt tuple checksum, never caller-supplied; static-ready, awaiting #274 caller wiring and loader/live proof
```

## L0 commands

```powershell
py tools/gen_zg361_workforce_appointment_fact.py --check
py tools/test_zg361_workforce_appointment_fact.py -v
py -O tools/test_zg361_workforce_appointment_fact.py -v
py tools/validate_local.py
```
"""
    )


def outputs() -> dict[Path, bytes]:
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


def validate_contract() -> None:
    if POSITION_TYPE_ID <= 0:
        raise ValueError("position type id must be positive")
    if SOURCE_KIND_COURT_POSITION != 1:
        raise ValueError("court-position source kind is frozen at 1")
    if len(LANGUAGES) != 9 or len(set(LANGUAGES)) != 9:
        raise ValueError("exactly nine localization structures are required")
    effects = render_effects().decode("utf-8-sig")
    if effects.count("appoint_court_position = {") != 1:
        raise ValueError("the package must own exactly one native appointment action")
    if effects.count("APPOINTMENT_CONFIRMED = 1") != 1:
        raise ValueError("the native callback finalizer must publish one hard-coded confirmation")
    for alias in (
        "zg361_we_ad_external_position_type_id",
        "zg361_we_ad_external_position_receipt_id",
        "zg361_we_ad_external_position_receipt_hash",
    ):
        if f"set_variable = {{ name = {alias}" in effects:
            raise ValueError(f"request package must not write legacy alias directly: {alias}")


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    validate_contract()
    write_outputs(check=args.check)
    if args.check:
        print("GREEN: Workforce appointment fact generated files are current")
    else:
        print(f"GREEN: generated {len(outputs())} Workforce appointment fact files")


if __name__ == "__main__":
    main()
