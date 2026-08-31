#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #275 remediation-fact producer.

This package intentionally owns no Workforce core, case-kernel, runner, native
provider, or shared-ledger file.  Its public entry is called in subject scope
after a real #275 route-B operation has committed.  The legacy two-field ABI is
published only by the explicit terminal-completion path.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
PREFIX = "zg361_workforce_remediation_fact"
NAMESPACE = "zg361workforceremediationfact"
READINESS = "ck3-script-static-ready-not-live"
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
LEGACY_RECEIPT_ALIAS = "zg361_we_ad_external_m275_remediation_receipt"
LEGACY_REASON_ALIAS = "zg361_we_ad_external_m275_remediated_reason_id"


def generated_script(text: str) -> bytes:
    header = (
        "# GENERATED FILE — edit "
        "tools/zg361_workforce_remediation_fact_gen.py\n"
    )
    return BOM + (header + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.rstrip() + "\n").encode("utf-8")


def render_effects() -> bytes:
    text = r'''
# Public subject-scope ABI.  It accepts no caller-authored identity or result:
# all source facts are joined directly from the committed Workforce #275-B
# business object and its frozen future-consumer tuple.
zg361_workforce_remediation_fact_open_effect = {
	remove_variable = zg361_workforce_remediation_fact_runtime_status
	remove_variable = zg361_workforce_remediation_fact_last_red_code
	if = {
		limit = {
			has_game_rule = zg361_on
			has_variable = zg361_we_m275_business_object_created
			var:zg361_we_m275_business_object_created = 1
			has_variable = zg361_we_m275_object_owner
			has_variable = zg361_we_m275_object_subject
			has_variable = zg361_we_m275_object_cycle
			has_variable = zg361_we_m275_object_case
			has_variable = zg361_we_m275_object_state
			has_variable = zg361_we_m275_object_consumed
			has_variable = zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275
			var:zg361_we_m275_object_subject = this
			var:zg361_we_m275_object_state = 4
			var:zg361_we_m275_object_consumed = 1
			var:zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1
			has_variable = zg361_we_m275_write_owner
			has_variable = zg361_we_m275_write_subject
			has_variable = zg361_we_m275_write_cycle
			has_variable = zg361_we_m275_write_case
			has_variable = zg361_we_m275_write_state
			has_variable = zg361_we_m275_receipt_owner
			has_variable = zg361_we_m275_receipt_subject
			has_variable = zg361_we_m275_receipt_cycle
			has_variable = zg361_we_m275_receipt_case
			has_variable = zg361_we_m275_receipt_state
			has_variable = zg361_we_m275_receipt_choice
			var:zg361_we_m275_write_subject = this
			var:zg361_we_m275_write_owner = var:zg361_we_m275_receipt_owner
			var:zg361_we_m275_write_subject = var:zg361_we_m275_receipt_subject
			var:zg361_we_m275_write_cycle = var:zg361_we_m275_receipt_cycle
			var:zg361_we_m275_write_case = var:zg361_we_m275_receipt_case
			var:zg361_we_m275_write_state = var:zg361_we_m275_receipt_state
			var:zg361_we_m275_receipt_state = 4
			var:zg361_we_m275_receipt_choice = 2
			var:zg361_we_m275_object_owner = var:zg361_we_m275_write_owner
			var:zg361_we_m275_object_cycle = var:zg361_we_m275_write_cycle
			var:zg361_we_m275_object_case = var:zg361_we_m275_write_case
			has_variable = zg361_we_m275_refusal
			var:zg361_we_m275_refusal = 1
			has_variable = zg361_we_m275_not_applicable_hired
			var:zg361_we_m275_not_applicable_hired = 0
			has_variable = zg361_we_m275_hold_pending
			var:zg361_we_m275_hold_pending = 1
			has_variable = zg361_we_m275_reason_remediated
			var:zg361_we_m275_reason_remediated = 0
			has_variable = zg361_we_m275_refusal_reason_id
			var:zg361_we_m275_refusal_reason_id > 0
			has_variable = zg361_we_m275_hold_due_cycle
			var:zg361_we_m275_hold_due_cycle > var:zg361_we_m275_write_cycle
			var:zg361_we_m275_write_cycle > 0
			var:zg361_we_m275_write_case > 0
			var:zg361_we_m275_write_owner = {
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
				var:zg361_review_serial >= prev.var:zg361_we_m275_write_cycle
			}
			trigger_if = {
				limit = { has_variable = zg361_workforce_remediation_fact_status }
				AND = {
					has_variable = zg361_workforce_remediation_fact_status
					has_variable = zg361_workforce_remediation_fact_owner
					has_variable = zg361_workforce_remediation_fact_cycle
					has_variable = zg361_workforce_remediation_fact_case
					has_variable = zg361_workforce_remediation_fact_receipt_status
					has_variable = zg361_workforce_remediation_fact_pending
					has_variable = zg361_workforce_remediation_fact_consumed
					var:zg361_workforce_remediation_fact_receipt_status = 1
					OR = {
						AND = {
							var:zg361_workforce_remediation_fact_status = 2
							var:zg361_workforce_remediation_fact_pending = 0
							var:zg361_workforce_remediation_fact_consumed = 1
						}
						AND = {
							var:zg361_workforce_remediation_fact_status = 3
							var:zg361_workforce_remediation_fact_pending = 0
							var:zg361_workforce_remediation_fact_consumed = 0
						}
					}
					OR = {
						NOT = { var:zg361_workforce_remediation_fact_cycle = var:zg361_we_m275_write_cycle }
						NOT = { var:zg361_workforce_remediation_fact_case = var:zg361_we_m275_write_case }
						NOT = { var:zg361_workforce_remediation_fact_owner = var:zg361_we_m275_write_owner }
					}
				}
			}
			trigger_else = { always = yes }
		}
		# Preserve the previous terminal receipt as a last-receipt audit slot before
		# opening a later real #275 case.  No pending case can be overwritten.
		if = {
			# The outer guard proves any existing slot is an exact terminal receipt
			# that is safe to archive (failure, or completion already consumed).
			limit = { has_variable = zg361_workforce_remediation_fact_status }
			if = {
				limit = { NOT = { has_variable = zg361_workforce_remediation_fact_archive_count } }
				set_variable = { name = zg361_workforce_remediation_fact_archive_count value = 1 }
			}
			else = { change_variable = { name = zg361_workforce_remediation_fact_archive_count add = 1 } }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_owner value = var:zg361_workforce_remediation_fact_receipt_owner }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_subject value = var:zg361_workforce_remediation_fact_receipt_subject }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_cycle value = var:zg361_workforce_remediation_fact_receipt_cycle }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_case value = var:zg361_workforce_remediation_fact_receipt_case }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_result value = var:zg361_workforce_remediation_fact_receipt_result }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_serial value = var:zg361_workforce_remediation_fact_receipt_serial }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_receipt_id value = var:zg361_workforce_remediation_fact_receipt_id }
			set_variable = { name = zg361_workforce_remediation_fact_archive_last_receipt_hash value = var:zg361_workforce_remediation_fact_receipt_hash }
		}
		remove_variable = zg361_we_ad_external_m275_remediation_receipt
		remove_variable = zg361_we_ad_external_m275_remediated_reason_id
		remove_variable = zg361_workforce_remediation_fact_result
		remove_variable = zg361_workforce_remediation_fact_result_actor
		remove_variable = zg361_workforce_remediation_fact_result_cycle
		remove_variable = zg361_workforce_remediation_fact_result_case
		remove_variable = zg361_workforce_remediation_fact_receipt_status
		remove_variable = zg361_workforce_remediation_fact_receipt_id
		remove_variable = zg361_workforce_remediation_fact_receipt_hash
		remove_variable = zg361_workforce_remediation_fact_receipt_owner
		remove_variable = zg361_workforce_remediation_fact_receipt_subject
		remove_variable = zg361_workforce_remediation_fact_receipt_cycle
		remove_variable = zg361_workforce_remediation_fact_receipt_case
		remove_variable = zg361_workforce_remediation_fact_receipt_result
		remove_variable = zg361_workforce_remediation_fact_receipt_reason_id
		remove_variable = zg361_workforce_remediation_fact_receipt_requirement_id
		remove_variable = zg361_workforce_remediation_fact_receipt_serial
		remove_variable = zg361_workforce_remediation_fact_pending
		remove_variable = zg361_workforce_remediation_fact_consumed
		# Compute every consumer of the next serial from the previously committed
		# counter.  Never initialize/change the counter and then read it again in
		# this effect: event-option tooltip pre-evaluation does not guarantee such
		# read-after-write ordering.
		if = {
			limit = { NOT = { has_variable = zg361_workforce_remediation_fact_serial_counter } }
			save_scope_value_as = { name = zg361_workforce_remediation_fact_ticket_requirement value = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_serial value = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_requirement_id value = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_serial_counter value = 1 }
		}
		else = {
			save_scope_value_as = { name = zg361_workforce_remediation_fact_ticket_requirement value = { value = var:zg361_workforce_remediation_fact_serial_counter add = 1 } }
			set_variable = { name = zg361_workforce_remediation_fact_serial value = { value = var:zg361_workforce_remediation_fact_serial_counter add = 1 } }
			set_variable = { name = zg361_workforce_remediation_fact_requirement_id value = { value = var:zg361_workforce_remediation_fact_serial_counter add = 1 } }
			set_variable = { name = zg361_workforce_remediation_fact_serial_counter value = { value = var:zg361_workforce_remediation_fact_serial_counter add = 1 } }
		}
		set_variable = { name = zg361_workforce_remediation_fact_status value = 1 }
		set_variable = { name = zg361_workforce_remediation_fact_owner value = var:zg361_we_m275_write_owner }
		set_variable = { name = zg361_workforce_remediation_fact_subject value = this }
		set_variable = { name = zg361_workforce_remediation_fact_cycle value = var:zg361_we_m275_write_cycle }
		set_variable = { name = zg361_workforce_remediation_fact_case value = var:zg361_we_m275_write_case }
		set_variable = { name = zg361_workforce_remediation_fact_source_state value = 4 }
		set_variable = { name = zg361_workforce_remediation_fact_reason_id value = var:zg361_we_m275_refusal_reason_id }
		# IDs are subject-local monotonic serials.  Global identity is always the
		# frozen owner/subject/cycle/case tuple plus this serial.
		set_variable = { name = zg361_workforce_remediation_fact_requirement_code value = 1 }
		set_variable = { name = zg361_workforce_remediation_fact_requirement_status value = 1 }
		set_variable = { name = zg361_workforce_remediation_fact_requirement_due_cycle value = var:zg361_we_m275_hold_due_cycle }
		set_variable = { name = zg361_workforce_remediation_fact_result value = 0 }
		set_variable = { name = zg361_workforce_remediation_fact_pending value = 0 }
		set_variable = { name = zg361_workforce_remediation_fact_consumed value = 0 }
		set_variable = { name = zg361_workforce_remediation_fact_awaiting_player value = 0 }
		set_variable = { name = zg361_workforce_remediation_fact_blocked_reason value = 0 }
		save_scope_as = zg361_workforce_remediation_fact_ticket_subject
		var:zg361_we_m275_write_owner = { save_scope_as = zg361_workforce_remediation_fact_ticket_owner }
		save_scope_value_as = { name = zg361_workforce_remediation_fact_ticket_cycle value = var:zg361_we_m275_write_cycle }
		save_scope_value_as = { name = zg361_workforce_remediation_fact_ticket_case value = var:zg361_we_m275_write_case }
		save_scope_value_as = { name = zg361_workforce_remediation_fact_ticket_reason value = var:zg361_we_m275_refusal_reason_id }
		if = {
			limit = { var:zg361_we_m275_write_owner = { is_ai = no } }
			set_variable = { name = zg361_workforce_remediation_fact_awaiting_player value = 1 }
			var:zg361_we_m275_write_owner = { trigger_event = { id = zg361workforceremediationfact.1 days = 30 } }
		}
		else = {
			# No observed AI remediation source exists.  Keep the requirement open and
			# publish no terminal fact or legacy alias.
			set_variable = { name = zg361_workforce_remediation_fact_blocked_reason value = 1 }
			debug_log = "ZG361WRF: AI-owned remediation remains open; no result was fabricated"
		}
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 1 }
	}
	else_if = {
		limit = {
			has_variable = zg361_workforce_remediation_fact_status
			var:zg361_workforce_remediation_fact_owner = var:zg361_we_m275_write_owner
			var:zg361_workforce_remediation_fact_subject = this
			var:zg361_workforce_remediation_fact_cycle = var:zg361_we_m275_write_cycle
			var:zg361_workforce_remediation_fact_case = var:zg361_we_m275_write_case
			var:zg361_workforce_remediation_fact_reason_id = var:zg361_we_m275_refusal_reason_id
		}
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 2 }
	}
	else = {
		set_variable = { name = zg361_workforce_remediation_fact_last_red_code value = 27521 }
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 4 }
	}
}

# Internal subject-scope terminal write.  RESULT=1 means the owner explicitly
# confirmed completion; RESULT=2 means the owner explicitly recorded failure.
# The receipt is written once, after the result, and never by the open path.
zg361_workforce_remediation_fact_settle_effect = {
	save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_requested_result value = $RESULT$ }
	save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_expected_terminal_status value = { value = $RESULT$ add = 1 } }
	save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_expected_receipt_id value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10 add = $RESULT$ } }
	save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_expected_receipt_hash value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10000000 add = { value = $RESULT$ multiply = 1000000 } add = { value = var:zg361_workforce_remediation_fact_cycle multiply = 10000 } add = { value = var:zg361_workforce_remediation_fact_case multiply = 100 } add = { value = var:zg361_workforce_remediation_fact_reason_id multiply = 10 } add = $RESULT$ } }
	remove_variable = zg361_workforce_remediation_fact_runtime_status
	remove_variable = zg361_workforce_remediation_fact_last_red_code
	if = {
		limit = {
			OR = {
				scope:zg361_workforce_remediation_fact_requested_result = 1
				scope:zg361_workforce_remediation_fact_requested_result = 2
			}
			has_variable = zg361_workforce_remediation_fact_status
			var:zg361_workforce_remediation_fact_status = 1
			has_variable = zg361_workforce_remediation_fact_requirement_status
			var:zg361_workforce_remediation_fact_requirement_status = 1
			has_variable = zg361_workforce_remediation_fact_owner
			has_variable = zg361_workforce_remediation_fact_subject
			has_variable = zg361_workforce_remediation_fact_cycle
			has_variable = zg361_workforce_remediation_fact_case
			has_variable = zg361_workforce_remediation_fact_source_state
			has_variable = zg361_workforce_remediation_fact_reason_id
			has_variable = zg361_workforce_remediation_fact_requirement_id
			has_variable = zg361_workforce_remediation_fact_requirement_code
			has_variable = zg361_workforce_remediation_fact_requirement_due_cycle
			has_variable = zg361_workforce_remediation_fact_serial
			has_variable = zg361_workforce_remediation_fact_serial_counter
			var:zg361_workforce_remediation_fact_source_state = 4
			var:zg361_workforce_remediation_fact_reason_id > 0
			var:zg361_workforce_remediation_fact_requirement_id = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_requirement_code = 1
			var:zg361_workforce_remediation_fact_serial > 0
			var:zg361_workforce_remediation_fact_serial_counter = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_subject = this
			$ACTOR$ = var:zg361_workforce_remediation_fact_owner
			$ACTOR$ = {
				is_ai = no
				zg361_is_celestial_liege_trigger = yes
				has_variable = zg361_review_serial
				var:zg361_review_serial >= prev.var:zg361_workforce_remediation_fact_cycle
			}
			has_variable = zg361_we_m275_hold_pending
			var:zg361_we_m275_hold_pending = 1
			has_variable = zg361_we_m275_reason_remediated
			var:zg361_we_m275_reason_remediated = 0
			has_variable = zg361_we_m266_hc_reservation_active
			var:zg361_we_m266_hc_reservation_active = 1
			has_variable = zg361_we_m266_hc_receipt
			has_variable = zg361_we_m275_hc_lineage_receipt
			var:zg361_we_m266_hc_receipt = var:zg361_we_m275_hc_lineage_receipt
			var:zg361_we_m275_hc_lineage_receipt = var:zg361_workforce_remediation_fact_case
			has_variable = zg361_ch_hc_reserved
			var:zg361_ch_hc_reserved >= 1
			has_variable = zg361_we_m275_business_object_created
			has_variable = zg361_we_m275_object_owner
			has_variable = zg361_we_m275_object_subject
			has_variable = zg361_we_m275_object_cycle
			has_variable = zg361_we_m275_object_case
			has_variable = zg361_we_m275_object_state
			has_variable = zg361_we_m275_object_consumed
			has_variable = zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275
			var:zg361_we_m275_business_object_created = 1
			var:zg361_we_m275_object_owner = var:zg361_workforce_remediation_fact_owner
			var:zg361_we_m275_object_subject = this
			var:zg361_we_m275_object_cycle = var:zg361_workforce_remediation_fact_cycle
			var:zg361_we_m275_object_case = var:zg361_workforce_remediation_fact_case
			var:zg361_we_m275_object_state = 4
			var:zg361_we_m275_object_consumed = 1
			var:zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1
			has_variable = zg361_we_m275_write_owner
			has_variable = zg361_we_m275_write_subject
			has_variable = zg361_we_m275_write_cycle
			has_variable = zg361_we_m275_write_case
			has_variable = zg361_we_m275_write_state
			has_variable = zg361_we_m275_receipt_choice
			has_variable = zg361_we_m275_receipt_state
			var:zg361_we_m275_receipt_choice = 2
			var:zg361_we_m275_write_owner = var:zg361_workforce_remediation_fact_owner
			var:zg361_we_m275_write_subject = this
			var:zg361_we_m275_write_cycle = var:zg361_workforce_remediation_fact_cycle
			var:zg361_we_m275_write_case = var:zg361_workforce_remediation_fact_case
			var:zg361_we_m275_write_state = 4
			var:zg361_we_m275_receipt_state = 4
			has_variable = zg361_we_m275_hold_due_cycle
			var:zg361_workforce_remediation_fact_requirement_due_cycle = var:zg361_we_m275_hold_due_cycle
			has_variable = zg361_we_m275_refusal_reason_id
			var:zg361_we_m275_refusal_reason_id = var:zg361_workforce_remediation_fact_reason_id
			var:zg361_workforce_remediation_fact_owner = {
				has_variable = zg361_we_ad_hc_flight_pending
				var:zg361_we_ad_hc_flight_pending = 1
				has_variable = zg361_we_ad_hc_flight_subject
				has_variable = zg361_we_ad_hc_flight_cycle
				has_variable = zg361_we_ad_hc_flight_case
				var:zg361_we_ad_hc_flight_subject = prev
				var:zg361_we_ad_hc_flight_cycle = prev.var:zg361_workforce_remediation_fact_cycle
				var:zg361_we_ad_hc_flight_case = prev.var:zg361_workforce_remediation_fact_case
			}
			NOT = { has_variable = zg361_workforce_remediation_fact_receipt_status }
		}
		set_variable = { name = zg361_workforce_remediation_fact_result value = scope:zg361_workforce_remediation_fact_requested_result }
		set_variable = { name = zg361_workforce_remediation_fact_result_actor value = $ACTOR$ }
		set_variable = { name = zg361_workforce_remediation_fact_result_cycle value = var:zg361_workforce_remediation_fact_owner.var:zg361_review_serial }
		set_variable = { name = zg361_workforce_remediation_fact_result_case value = var:zg361_workforce_remediation_fact_case }
		set_variable = { name = zg361_workforce_remediation_fact_requirement_status value = { value = scope:zg361_workforce_remediation_fact_requested_result add = 1 } }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_serial value = var:zg361_workforce_remediation_fact_serial }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_id value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10 add = scope:zg361_workforce_remediation_fact_requested_result } }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_hash value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10000000 add = { value = scope:zg361_workforce_remediation_fact_requested_result multiply = 1000000 } add = { value = var:zg361_workforce_remediation_fact_cycle multiply = 10000 } add = { value = var:zg361_workforce_remediation_fact_case multiply = 100 } add = { value = var:zg361_workforce_remediation_fact_reason_id multiply = 10 } add = scope:zg361_workforce_remediation_fact_requested_result } }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_owner value = var:zg361_workforce_remediation_fact_owner }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_subject value = this }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_cycle value = var:zg361_workforce_remediation_fact_cycle }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_case value = var:zg361_workforce_remediation_fact_case }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_result value = scope:zg361_workforce_remediation_fact_requested_result }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_reason_id value = var:zg361_workforce_remediation_fact_reason_id }
		set_variable = { name = zg361_workforce_remediation_fact_receipt_requirement_id value = var:zg361_workforce_remediation_fact_requirement_id }
		set_variable = { name = zg361_workforce_remediation_fact_awaiting_player value = 0 }
		if = {
			limit = { scope:zg361_workforce_remediation_fact_requested_result = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_status value = 2 }
			set_variable = { name = zg361_workforce_remediation_fact_pending value = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_consumed value = 0 }
		}
		else = {
			set_variable = { name = zg361_workforce_remediation_fact_status value = 3 }
			set_variable = { name = zg361_workforce_remediation_fact_pending value = 0 }
			set_variable = { name = zg361_workforce_remediation_fact_consumed value = 0 }
		}
		if = {
			limit = { scope:zg361_workforce_remediation_fact_requested_result = 1 }
			set_variable = { name = zg361_we_ad_external_m275_remediation_receipt value = 1 }
			set_variable = { name = zg361_we_ad_external_m275_remediated_reason_id value = var:zg361_workforce_remediation_fact_reason_id }
		}
		else = {
			remove_variable = zg361_we_ad_external_m275_remediation_receipt
			remove_variable = zg361_we_ad_external_m275_remediated_reason_id
		}
		# Final constant commit marker: every detailed result/receipt field and the
		# corresponding completion aliases (or explicit failure removals) precede it.
		set_variable = { name = zg361_workforce_remediation_fact_receipt_status value = 1 }
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 1 }
	}
	else_if = {
		limit = {
			has_variable = zg361_workforce_remediation_fact_status
			has_variable = zg361_workforce_remediation_fact_requirement_status
			has_variable = zg361_workforce_remediation_fact_owner
			has_variable = zg361_workforce_remediation_fact_subject
			has_variable = zg361_workforce_remediation_fact_cycle
			has_variable = zg361_workforce_remediation_fact_case
			has_variable = zg361_workforce_remediation_fact_reason_id
			has_variable = zg361_workforce_remediation_fact_requirement_id
			has_variable = zg361_workforce_remediation_fact_serial
			has_variable = zg361_workforce_remediation_fact_result
			has_variable = zg361_workforce_remediation_fact_result_actor
			has_variable = zg361_workforce_remediation_fact_result_cycle
			has_variable = zg361_workforce_remediation_fact_result_case
			has_variable = zg361_workforce_remediation_fact_receipt_status
			has_variable = zg361_workforce_remediation_fact_receipt_owner
			has_variable = zg361_workforce_remediation_fact_receipt_subject
			has_variable = zg361_workforce_remediation_fact_receipt_cycle
			has_variable = zg361_workforce_remediation_fact_receipt_case
			has_variable = zg361_workforce_remediation_fact_receipt_result
			has_variable = zg361_workforce_remediation_fact_receipt_reason_id
			has_variable = zg361_workforce_remediation_fact_receipt_requirement_id
			has_variable = zg361_workforce_remediation_fact_receipt_serial
			has_variable = zg361_workforce_remediation_fact_receipt_id
			has_variable = zg361_workforce_remediation_fact_receipt_hash
			var:zg361_workforce_remediation_fact_receipt_status = 1
			var:zg361_workforce_remediation_fact_status = scope:zg361_workforce_remediation_fact_expected_terminal_status
			var:zg361_workforce_remediation_fact_requirement_status = scope:zg361_workforce_remediation_fact_expected_terminal_status
			var:zg361_workforce_remediation_fact_subject = this
			$ACTOR$ = var:zg361_workforce_remediation_fact_owner
			$ACTOR$ = {
				has_variable = zg361_review_serial
				var:zg361_review_serial >= prev.var:zg361_workforce_remediation_fact_result_cycle
			}
			var:zg361_workforce_remediation_fact_result = scope:zg361_workforce_remediation_fact_requested_result
			var:zg361_workforce_remediation_fact_result_actor = $ACTOR$
			var:zg361_workforce_remediation_fact_result_cycle >= var:zg361_workforce_remediation_fact_cycle
			var:zg361_workforce_remediation_fact_result_case = var:zg361_workforce_remediation_fact_case
			var:zg361_workforce_remediation_fact_receipt_owner = $ACTOR$
			var:zg361_workforce_remediation_fact_receipt_subject = this
			var:zg361_workforce_remediation_fact_receipt_cycle = var:zg361_workforce_remediation_fact_cycle
			var:zg361_workforce_remediation_fact_receipt_case = var:zg361_workforce_remediation_fact_case
			var:zg361_workforce_remediation_fact_receipt_result = scope:zg361_workforce_remediation_fact_requested_result
			var:zg361_workforce_remediation_fact_receipt_reason_id = var:zg361_workforce_remediation_fact_reason_id
			var:zg361_workforce_remediation_fact_receipt_requirement_id = var:zg361_workforce_remediation_fact_requirement_id
			var:zg361_workforce_remediation_fact_receipt_serial = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_receipt_id = scope:zg361_workforce_remediation_fact_expected_receipt_id
			var:zg361_workforce_remediation_fact_receipt_hash = scope:zg361_workforce_remediation_fact_expected_receipt_hash
		}
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 2 }
	}
	else = {
		set_variable = { name = zg361_workforce_remediation_fact_last_red_code value = 27522 }
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 4 }
	}
}

# Optional second integration point, called in subject scope only after the
# Workforce due consumer really released the exact HC lineage.  This turns the
# producer slot from pending to consumed; it cannot manufacture completion.
zg361_workforce_remediation_fact_consume_effect = {
	remove_variable = zg361_workforce_remediation_fact_runtime_status
	remove_variable = zg361_workforce_remediation_fact_last_red_code
	if = {
		limit = {
			has_variable = zg361_workforce_remediation_fact_serial
			has_variable = zg361_workforce_remediation_fact_cycle
			has_variable = zg361_workforce_remediation_fact_case
			has_variable = zg361_workforce_remediation_fact_reason_id
		}
		save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_consume_expected_receipt_id value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10 add = 1 } }
		save_temporary_scope_value_as = { name = zg361_workforce_remediation_fact_consume_expected_receipt_hash value = { value = var:zg361_workforce_remediation_fact_serial multiply = 10000000 add = 1000000 add = { value = var:zg361_workforce_remediation_fact_cycle multiply = 10000 } add = { value = var:zg361_workforce_remediation_fact_case multiply = 100 } add = { value = var:zg361_workforce_remediation_fact_reason_id multiply = 10 } add = 1 } }
		if = {
			limit = {
			has_variable = zg361_workforce_remediation_fact_pending
			has_variable = zg361_workforce_remediation_fact_consumed
			has_variable = zg361_workforce_remediation_fact_status
			var:zg361_workforce_remediation_fact_status = 2
			OR = {
				AND = {
					var:zg361_workforce_remediation_fact_pending = 1
					var:zg361_workforce_remediation_fact_consumed = 0
				}
				AND = {
					var:zg361_workforce_remediation_fact_pending = 0
					var:zg361_workforce_remediation_fact_consumed = 1
				}
			}
			has_variable = zg361_workforce_remediation_fact_owner
			has_variable = zg361_workforce_remediation_fact_subject
			has_variable = zg361_workforce_remediation_fact_cycle
			has_variable = zg361_workforce_remediation_fact_case
			has_variable = zg361_workforce_remediation_fact_source_state
			has_variable = zg361_workforce_remediation_fact_reason_id
			has_variable = zg361_workforce_remediation_fact_requirement_id
			has_variable = zg361_workforce_remediation_fact_requirement_code
			has_variable = zg361_workforce_remediation_fact_requirement_status
			has_variable = zg361_workforce_remediation_fact_requirement_due_cycle
			has_variable = zg361_workforce_remediation_fact_serial
			has_variable = zg361_workforce_remediation_fact_serial_counter
			has_variable = zg361_workforce_remediation_fact_result
			has_variable = zg361_workforce_remediation_fact_result_actor
			has_variable = zg361_workforce_remediation_fact_result_cycle
			has_variable = zg361_workforce_remediation_fact_result_case
			var:zg361_workforce_remediation_fact_subject = this
			var:zg361_workforce_remediation_fact_source_state = 4
			var:zg361_workforce_remediation_fact_reason_id > 0
			var:zg361_workforce_remediation_fact_requirement_id = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_requirement_code = 1
			var:zg361_workforce_remediation_fact_requirement_status = 2
			var:zg361_workforce_remediation_fact_serial_counter = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_result = 1
			var:zg361_workforce_remediation_fact_result_actor = var:zg361_workforce_remediation_fact_owner
			var:zg361_workforce_remediation_fact_result_cycle >= var:zg361_workforce_remediation_fact_cycle
			var:zg361_workforce_remediation_fact_result_case = var:zg361_workforce_remediation_fact_case
			has_variable = zg361_workforce_remediation_fact_receipt_status
			var:zg361_workforce_remediation_fact_receipt_status = 1
			has_variable = zg361_workforce_remediation_fact_receipt_owner
			has_variable = zg361_workforce_remediation_fact_receipt_subject
			has_variable = zg361_workforce_remediation_fact_receipt_cycle
			has_variable = zg361_workforce_remediation_fact_receipt_case
			has_variable = zg361_workforce_remediation_fact_receipt_result
			has_variable = zg361_workforce_remediation_fact_receipt_reason_id
			has_variable = zg361_workforce_remediation_fact_receipt_requirement_id
			has_variable = zg361_workforce_remediation_fact_receipt_serial
			has_variable = zg361_workforce_remediation_fact_receipt_id
			has_variable = zg361_workforce_remediation_fact_receipt_hash
			var:zg361_workforce_remediation_fact_receipt_owner = var:zg361_workforce_remediation_fact_owner
			has_variable = zg361_we_m275_write_owner
			has_variable = zg361_we_m275_write_subject
			has_variable = zg361_we_m275_write_cycle
			has_variable = zg361_we_m275_write_case
			has_variable = zg361_we_m275_write_state
			has_variable = zg361_we_m275_receipt_owner
			has_variable = zg361_we_m275_receipt_subject
			has_variable = zg361_we_m275_receipt_cycle
			has_variable = zg361_we_m275_receipt_case
			has_variable = zg361_we_m275_receipt_state
			has_variable = zg361_we_m275_receipt_choice
			var:zg361_workforce_remediation_fact_owner = var:zg361_we_m275_write_owner
			var:zg361_workforce_remediation_fact_cycle = var:zg361_we_m275_write_cycle
			var:zg361_workforce_remediation_fact_case = var:zg361_we_m275_write_case
			var:zg361_we_m275_write_subject = this
			var:zg361_we_m275_write_state = 4
			var:zg361_we_m275_write_owner = var:zg361_we_m275_receipt_owner
			var:zg361_we_m275_write_subject = var:zg361_we_m275_receipt_subject
			var:zg361_we_m275_write_cycle = var:zg361_we_m275_receipt_cycle
			var:zg361_we_m275_write_case = var:zg361_we_m275_receipt_case
			var:zg361_we_m275_receipt_state = 4
			var:zg361_we_m275_receipt_choice = 2
			has_variable = zg361_we_m275_business_object_created
			has_variable = zg361_we_m275_object_owner
			has_variable = zg361_we_m275_object_subject
			has_variable = zg361_we_m275_object_cycle
			has_variable = zg361_we_m275_object_case
			has_variable = zg361_we_m275_object_state
			has_variable = zg361_we_m275_object_consumed
			has_variable = zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275
			var:zg361_we_m275_business_object_created = 1
			var:zg361_we_m275_object_owner = var:zg361_workforce_remediation_fact_owner
			var:zg361_we_m275_object_subject = this
			var:zg361_we_m275_object_cycle = var:zg361_workforce_remediation_fact_cycle
			var:zg361_we_m275_object_case = var:zg361_workforce_remediation_fact_case
			var:zg361_we_m275_object_state = 4
			var:zg361_we_m275_object_consumed = 1
			var:zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1
			has_variable = zg361_we_m275_refusal_reason_id
			var:zg361_workforce_remediation_fact_receipt_subject = this
			var:zg361_workforce_remediation_fact_receipt_cycle = var:zg361_workforce_remediation_fact_cycle
			var:zg361_workforce_remediation_fact_receipt_case = var:zg361_workforce_remediation_fact_case
			var:zg361_workforce_remediation_fact_receipt_result = 1
			var:zg361_workforce_remediation_fact_receipt_reason_id = var:zg361_workforce_remediation_fact_reason_id
			var:zg361_workforce_remediation_fact_receipt_requirement_id = var:zg361_workforce_remediation_fact_requirement_id
			var:zg361_workforce_remediation_fact_receipt_serial = var:zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_receipt_id = scope:zg361_workforce_remediation_fact_consume_expected_receipt_id
			var:zg361_workforce_remediation_fact_receipt_hash = scope:zg361_workforce_remediation_fact_consume_expected_receipt_hash
			var:zg361_we_m275_refusal_reason_id = var:zg361_workforce_remediation_fact_reason_id
			has_variable = zg361_we_m275_hold_due_cycle
			var:zg361_we_m275_hold_due_cycle = var:zg361_workforce_remediation_fact_requirement_due_cycle
			has_variable = zg361_we_m275_hold_pending
			var:zg361_we_m275_hold_pending = 0
			has_variable = zg361_we_m275_reason_remediated
			var:zg361_we_m275_reason_remediated = 1
			has_variable = zg361_we_m275_hold_released
			var:zg361_we_m275_hold_released = 1
			has_variable = zg361_we_m266_hc_reservation_active
			var:zg361_we_m266_hc_reservation_active = 0
			has_variable = zg361_we_m266_hc_receipt
			has_variable = zg361_we_m275_hc_lineage_receipt
			var:zg361_we_m266_hc_receipt = var:zg361_we_m275_hc_lineage_receipt
			var:zg361_we_m275_hc_lineage_receipt = var:zg361_workforce_remediation_fact_case
			has_variable = zg361_we_ad_external_m275_remediation_receipt
			has_variable = zg361_we_ad_external_m275_remediated_reason_id
			var:zg361_we_ad_external_m275_remediation_receipt = 1
			var:zg361_we_ad_external_m275_remediated_reason_id = var:zg361_workforce_remediation_fact_receipt_reason_id
			var:zg361_workforce_remediation_fact_owner = {
				has_variable = zg361_review_serial
				var:zg361_review_serial >= prev.var:zg361_workforce_remediation_fact_result_cycle
				has_variable = zg361_we_ad_hc_flight_pending
				var:zg361_we_ad_hc_flight_pending = 0
				has_variable = zg361_we_ad_hc_flight_subject
				has_variable = zg361_we_ad_hc_flight_cycle
				has_variable = zg361_we_ad_hc_flight_case
				var:zg361_we_ad_hc_flight_subject = prev
				var:zg361_we_ad_hc_flight_cycle = prev.var:zg361_workforce_remediation_fact_cycle
				var:zg361_we_ad_hc_flight_case = prev.var:zg361_workforce_remediation_fact_case
			}
		}
		if = {
			limit = {
				var:zg361_workforce_remediation_fact_pending = 1
				var:zg361_workforce_remediation_fact_consumed = 0
			}
			set_variable = { name = zg361_workforce_remediation_fact_pending value = 0 }
			set_variable = { name = zg361_workforce_remediation_fact_consumed value = 1 }
			set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 1 }
		}
		else = {
			# Idempotent ACK is available only behind the same exact tuple and HC
			# release postcondition as the first consume.
			set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 2 }
		}
		}
		else = {
			set_variable = { name = zg361_workforce_remediation_fact_last_red_code value = 27523 }
			set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 4 }
		}
	}
	else = {
		set_variable = { name = zg361_workforce_remediation_fact_last_red_code value = 27523 }
		set_variable = { name = zg361_workforce_remediation_fact_runtime_status value = 4 }
	}
}
'''
    return generated_script(text)


def render_events() -> bytes:
    text = r'''
namespace = zg361workforceremediationfact

# The only visible producer is the exact owner of the frozen #275 refusal.
# A missing/stale ticket prevents the event; it never falls back to a default.
zg361workforceremediationfact.1 = {
	type = character_event
	theme = stewardship
	title = zg361workforceremediationfact.1.t
	desc = zg361workforceremediationfact.1.desc
	trigger = {
		is_ai = no
		zg361_is_celestial_liege_trigger = yes
		exists = scope:zg361_workforce_remediation_fact_ticket_owner
		exists = scope:zg361_workforce_remediation_fact_ticket_subject
		exists = scope:zg361_workforce_remediation_fact_ticket_cycle
		exists = scope:zg361_workforce_remediation_fact_ticket_case
		exists = scope:zg361_workforce_remediation_fact_ticket_reason
		exists = scope:zg361_workforce_remediation_fact_ticket_requirement
		this = scope:zg361_workforce_remediation_fact_ticket_owner
		scope:zg361_workforce_remediation_fact_ticket_subject = {
			has_variable = zg361_workforce_remediation_fact_status
			has_variable = zg361_workforce_remediation_fact_requirement_id
			has_variable = zg361_workforce_remediation_fact_serial
			var:zg361_workforce_remediation_fact_status = 1
			var:zg361_workforce_remediation_fact_owner = root
			var:zg361_workforce_remediation_fact_subject = this
			var:zg361_workforce_remediation_fact_cycle = scope:zg361_workforce_remediation_fact_ticket_cycle
			var:zg361_workforce_remediation_fact_case = scope:zg361_workforce_remediation_fact_ticket_case
			var:zg361_workforce_remediation_fact_reason_id = scope:zg361_workforce_remediation_fact_ticket_reason
			var:zg361_workforce_remediation_fact_requirement_id = scope:zg361_workforce_remediation_fact_ticket_requirement
			var:zg361_workforce_remediation_fact_serial = scope:zg361_workforce_remediation_fact_ticket_requirement
			has_variable = zg361_we_m275_hold_pending
			var:zg361_we_m275_hold_pending = 1
			var:zg361_we_m275_receipt_choice = 2
		}
	}
	option = {
		name = zg361workforceremediationfact.1.complete
		scope:zg361_workforce_remediation_fact_ticket_subject = {
			zg361_workforce_remediation_fact_settle_effect = { ACTOR = root RESULT = 1 }
		}
	}
	option = {
		name = zg361workforceremediationfact.1.fail
		scope:zg361_workforce_remediation_fact_ticket_subject = {
			zg361_workforce_remediation_fact_settle_effect = { ACTOR = root RESULT = 2 }
		}
	}
}
'''
    return generated_script(text)


ENGLISH = {
    "title": "The Vacancy Still Remembers",
    "desc": (
        "Thirty days have passed since the offer was refused. The held position "
        "may be released only if you record what the refusal exposed and whether "
        "that exact condition was actually corrected. A plan, a promise, or an "
        "empty checkbox is not a completion receipt."
    ),
    "complete": "Record the corrective action as completed and verified",
    "fail": "Record that the corrective action failed",
}
CHINESE = {
    "title": "空缺仍记得那次拒绝",
    "desc": (
        "录用被拒已经三十日。只有把那次拒绝暴露的问题逐项记清，并确认同一个问题确已整改，冻结编制才有资格释放。"
        "计划、承诺和一枚空勾都不是完成回执。"
    ),
    "complete": "确认整改已完成并通过核验",
    "fail": "如实记录整改失败",
}


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    values = CHINESE if language == "simp_chinese" else ENGLISH
    rows = [
        f"l_{language}:",
        f' {NAMESPACE}.1.t:0 "{esc(values["title"])}"',
        f' {NAMESPACE}.1.desc:0 "{esc(values["desc"])}"',
        f' {NAMESPACE}.1.complete:0 "{esc(values["complete"])}"',
        f' {NAMESPACE}.1.fail:0 "{esc(values["fail"])}"',
    ]
    return localized("\n".join(rows))


def render_spec() -> bytes:
    text = f'''<!-- GENERATED FILE — edit tools/zg361_workforce_remediation_fact_gen.py -->
# Workforce #275 remediation fact 独立生产者合同

状态：`{READINESS}`。本包只负责旧 Workforce #275-B remediation 两字段债务；不修改 Workforce core、#360、runner、CK3 1.19.0.6 bridge/provider 或共享 external-producer ledger。

## 1. 所有权与入口

- 生成器：`tools/zg361_workforce_remediation_fact_gen.py`
- effects：`common/scripted_effects/zg361_workforce_remediation_fact_effects.txt`
- events：`events/zg361_workforce_remediation_fact_events.txt`
- localization：`localization/*/zg361_workforce_remediation_fact_l_*.yml`
- 测试：`tools/zg361_workforce_remediation_fact_test.py`
- 两个公开 ABI 都在 subject scope：`zg361_workforce_remediation_fact_open_effect = yes` 打开真实 requirement；`zg361_workforce_remediation_fact_consume_effect = yes` 只在 Workforce 已释放 exact HC 后确认消费。

调用点必须位于 `zg361_we_m275_route_b_effect` 成功、`zg361_we_runtime_applied=1` **已经提交后的下一事件/帧**，不能在写 #275 tuple 的同一 effect 链里立即读取；入口不接收 caller 自报的 owner/subject/cycle/case/reason/result，而是直接 join 已提交的 #275 business object、future write/receipt tuple、`choice=2`、真实 hold 与 refusal reason。当前独立包不修改 Workforce generator，所以中央接线前仍是 static-ready，不能声称 production reachable。

## 2. 真实整改事实

打开时只冻结 requirement：owner、subject、source cycle/case/state、拒绝理由、与 core `hold_due_cycle` 相同的截止周期，以及 subject-local 只增 requirement ID。首次 ID 为 1；后续 serial、requirement ID 与 delayed-event ticket 都分别从此前已提交的 counter 计算同一个 next value，不读取本 effect 刚写的值。打开、排队或 AI blocked 状态都不会写 completion alias。

玩家 owner 在 30 日后的唯一事件中明确选择：

1. `RESULT=1`：整改完成并核验；
2. `RESULT=2`：整改失败。

两条终态都只生成一次 receipt，并冻结 `receipt_owner/subject/cycle/case/result/reason_id/requirement_id/serial/id/hash`。每个 subject 的新 exact case 使用只增 serial；ID 由 serial/result 组成，hash 还折叠冻结的 cycle/case/reason/result。owner/subject 是 receipt tuple 的 opaque identity 字段，不伪装成可算数 hash；ID/hash 从不单独充当全局身份，也不接受 caller 参数。相同终态重放 idempotent；改变 result 的重放、过期 tuple、错误 actor 或缺 core hold 都 typed RED 且不改 receipt。完成结果另发布 `pending=1/consumed=0`；失败结果保持二者为零。

AI owner 没有可观察的整改完成 producer，因此只保留 open requirement 与 blocked reason；不自动选择完成或失败，也不写旧 alias。

## 3. 旧 alias 投影

旧 consumer 仍读取：

```text
{LEGACY_RECEIPT_ALIAS}
{LEGACY_REASON_ALIAS}
```

只有 `RESULT=1` 成功落下一次性 detailed receipt 时才投影 `receipt=1`，并把 reason alias 写成冻结的同案 refusal reason；所有详细字段与 alias 都写完后才落最终常量 commit marker。`RESULT=2` 先写完整失败 receipt、明确移除两 alias，再落同一 marker。代码中不存在用零值、计划、排队、AI 默认或超时冒充整改完成的路径。

## 4. Readiness 与待接 ABI

静态测试只证明生成可复现、BOM/九语结构、真实 source guard、玩家 owner 两个终态、receipt 一次性与 legacy alias 只在完成分支写入。它没有 CK3 parser、事件点击、30 日 scheduler、存读档或 paused snapshot 证据。

集成者需从 #275 route B 成功分支排入下一事件/帧，并在该已提交边界的 subject scope 调用：

```text
zg361_workforce_remediation_fact_open_effect = yes
```

并在 #275 due consumer 已实际完成 `reserved→available`、`hold_pending=0`、`reason_remediated=1` 后调用：

```text
zg361_workforce_remediation_fact_consume_effect = yes
```

第二个 effect 只会在同一 owner/subject/cycle/case/result/reason/requirement/serial/id/hash 与 exact HC release postcondition 全部成立时，把 detailed receipt 的 `pending=1/consumed=0` 改成 `0/1`；同一精确事实重放只回 idempotent ACK，不能制造 completion。

上游 `zg361_we_ad_external_refusal_reason_id` 仍是账本中的另一项 producer debt；本包只绑定 #275 已冻结的非零 reason，不把该上游 alias 的存在升级为来源真值。

然后运行新 loader 差集与 MCP-first paused acceptance：验证玩家 owner 完成会在到期 consumer 释放 exact HC lineage；失败、AI、缺事件响应与 stale ticket 都保持 hold 且不产生 alias。OCR 不参与真值或 GREEN 判定。

## 5. 建议 shared ledger 更新（本包不直接修改）

把 Career/HC remediation 2 项从“缺 producer”改为“独立真实 producer static-ready，等待 Workforce 成功分支接 ABI 与 loader/live 证明”；不得在接线或实机前从剩余债务数字中扣除，也不得把 alias setter 的静态存在称为完成整改。
'''
    return text.encode("utf-8")


def validate_contract() -> None:
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("this isolated producer must not claim live readiness")
    if len(LANGUAGES) != 9 or len(set(LANGUAGES)) != 9:
        raise ValueError("exactly nine unique CK3 localization projections are required")
    if not LEGACY_RECEIPT_ALIAS.endswith("remediation_receipt"):
        raise ValueError("legacy receipt alias drifted")
    if not LEGACY_REASON_ALIAS.endswith("remediated_reason_id"):
        raise ValueError("legacy reason alias drifted")


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered: dict[Path, bytes] = {
        MOD_ROOT / "common" / "scripted_effects" / f"{PREFIX}_effects.txt": render_effects(),
        MOD_ROOT / "events" / f"{PREFIX}_events.txt": render_events(),
        MOD_ROOT / "docs" / f"{PREFIX}_spec.md": render_spec(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT
            / "localization"
            / language
            / f"{PREFIX}_l_{language}.yml"
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
            print("RED: stale Workforce remediation-fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print(
            f"GREEN: {len(rendered)} Workforce remediation-fact files are current "
            f"({READINESS})"
        )
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce remediation-fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
