#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B2 delivery, appeal, justice, and first PIP CK3 slice.

The generated runtime deliberately reuses the hand-written result-case
settlement and receipt-based refund effects.  It adds case-bound consumers
around those proven writes; it does not duplicate the money/merit ledger.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from zg361_b2_runtime_data import B2_BINDINGS, validate_b2_bindings


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_b2_runtime.py\n"
WIRED_IDS = (
    tuple(range(14, 18))
    + tuple(range(69, 82))
    + (358, 359)
)
INTERFACE_IDS = (69,)


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + (text.strip() + "\n").encode("utf-8")


def validate_wired_scope() -> None:
    validate_b2_bindings()
    available = {binding.mechanism_id for binding in B2_BINDINGS}
    if len(WIRED_IDS) != 19 or len(set(WIRED_IDS)) != 19:
        raise ValueError("B2 CK3 slice must contain exactly nineteen IDs")
    if not set(WIRED_IDS) <= available:
        raise ValueError("B2 CK3 slice contains an unknown binding")
    if INTERFACE_IDS != (69,):
        raise ValueError("069 is the only pre-existing interface in this slice")


def render_effects() -> bytes:
    return generated(r'''
# ZhongGuo 361 B2 — delivery, appeal justice and first PIP product runtime.
#
# State is stored on the assessed official.  Every timed event freezes owner,
# subject, cycle, case and expected state.  Existing zg361_effects.txt remains
# the only implementation of 3.25 settlement and receipt-bounded refund.

# ---------------------------------------------------------------------------
# Result freeze and delivery adapters: #069, #072, #081.
# ---------------------------------------------------------------------------

zg361_b2_on_result_frozen_effect = {
	if = {
		limit = {
			has_variable = zg361_result_case_owner
			has_variable = zg361_result_cycle_serial
			has_variable = zg361_result_case_serial
			has_variable = zg361_result_case_state
		}
		# A later, freshly frozen result by the same owner is the only automatic
		# source of "new fact" for a pending retaliation observation.  Merely
		# reusing the appealed result never authorizes a harsher action.
		if = {
			limit = {
				has_variable = zg361_b2_retaliation_state
				var:zg361_b2_retaliation_state = 1
				has_variable = zg361_b2_retaliation_subject
				var:zg361_b2_retaliation_subject = this
				has_variable = zg361_b2_retaliation_owner
				var:zg361_b2_retaliation_owner = var:zg361_result_case_owner
				has_variable = zg361_b2_retaliation_cycle
				var:zg361_result_cycle_serial > var:zg361_b2_retaliation_cycle
			}
			set_variable = { name = zg361_b2_retaliation_new_fact value = 1 }
			set_variable = { name = zg361_b2_retaliation_new_fact_cycle value = var:zg361_result_cycle_serial }
		}
		set_variable = { name = zg361_b2_case_owner value = var:zg361_result_case_owner }
		set_variable = { name = zg361_b2_case_subject value = this }
		set_variable = { name = zg361_b2_case_cycle value = var:zg361_result_cycle_serial }
		set_variable = { name = zg361_b2_case_serial value = var:zg361_result_case_serial }
		set_variable = { name = zg361_b2_notice_state value = 1 } # prepared
		set_variable = { name = zg361_b2_notice_reason value = var:zg361_result_grade_reason }
		set_variable = { name = zg361_b2_delivery_year value = 0 }
		set_variable = { name = zg361_b2_appeal_state value = 0 }
		set_variable = { name = zg361_b2_case_feedback_revision value = 1 }

		# A new result case resets its own B2 rows, but a one-year retaliation
		# observation has separate identity and survives the next result freeze.
		set_variable = { name = zg361_b2_m014_state value = 0 }
		set_variable = { name = zg361_b2_m015_state value = 0 }
		set_variable = { name = zg361_b2_m016_state value = 0 }
		set_variable = { name = zg361_b2_m017_state value = 0 }
		set_variable = { name = zg361_b2_m069_state value = 1 }
		set_variable = { name = zg361_b2_m069_receipt_serial value = 0 }
		set_variable = { name = zg361_b2_m071_state value = 0 }
		set_variable = { name = zg361_b2_m073_state value = 0 }
		set_variable = { name = zg361_b2_m074_state value = 0 }
		set_variable = { name = zg361_b2_m075_state value = 0 }
		set_variable = { name = zg361_b2_m076_state value = 0 }
		set_variable = { name = zg361_b2_m077_state value = 0 }
		set_variable = { name = zg361_b2_m078_state value = 0 }
		set_variable = { name = zg361_b2_m079_state value = 0 }
		set_variable = { name = zg361_b2_m080_state value = 0 }
		set_variable = { name = zg361_b2_m358_state value = 0 }
		set_variable = { name = zg361_b2_m359_state value = 0 }

		zg361_b2_m072_lock_pre_delivery_access_effect = yes
		zg361_b2_m081_project_case_access_effect = yes
		debug_log = "ZG361B2: result-bound justice case prepared"
	}
}

zg361_b2_m072_lock_pre_delivery_access_effect = {
	set_variable = { name = zg361_b2_m072_state value = 1 }
	set_variable = { name = zg361_b2_m072_acl_version value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m072_pre_delivery_reads value = 0 }
	set_variable = { name = zg361_b2_m072_headstart_days value = 0 }
	set_variable = { name = zg361_b2_m072_receipt_serial value = var:zg361_b2_case_serial }
}

# The existing personal-statement decision is the real read entry point.  A
# pre-delivery attempt is logged once and remains summary-only; a delivered
# case records one lawful subject read without minting a second consequence.
zg361_b2_record_case_access_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_m072_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_notice_state = 1
			var:zg361_b2_m072_pre_delivery_reads = 0
		}
		set_variable = { name = zg361_b2_m072_pre_delivery_reads value = 1 }
		set_variable = { name = zg361_b2_m072_reader value = this }
		set_variable = { name = zg361_b2_m072_source value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m072_read_year value = current_year }
		set_variable = { name = zg361_b2_m072_state value = 2 }
		set_variable = { name = zg361_b2_m081_omitted_before_delivery value = 1 }
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_leak_deadline_owner }
		save_scope_as = zg361_b2_leak_deadline_subject
		save_scope_value_as = { name = zg361_b2_leak_deadline_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_leak_deadline_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_leak_deadline_state value = var:zg361_b2_m072_state }
		trigger_event = { id = zg361b2.121 days = 30 }
	}
	else_if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_m081_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_notice_state >= 3
		}
		set_variable = { name = zg361_b2_m081_subject_read_receipt value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m081_last_read_year value = current_year }
	}
}

zg361_b2_m081_project_case_access_effect = {
	set_variable = { name = zg361_b2_m081_state value = 1 }
	set_variable = { name = zg361_b2_m081_access_level value = 1 } # subject summary
	set_variable = { name = zg361_b2_m081_visible_fields value = 4 }
	set_variable = { name = zg361_b2_m081_correction_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_m081_receipt_serial value = var:zg361_b2_case_serial }
}

zg361_b2_on_notice_delivered_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_case_owner
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			has_variable = zg361_b2_case_subject
			var:zg361_b2_case_subject = this
			has_variable = zg361_b2_case_cycle
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			has_variable = zg361_b2_case_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			has_variable = zg361_b2_notice_state
			var:zg361_b2_notice_state = 1
			var:zg361_result_case_state = 3
			var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
		}
		zg361_b2_m069_record_delivery_effect = yes
		zg361_b2_m072_close_access_log_effect = yes
		zg361_b2_m081_publish_case_projection_effect = yes
		zg361_b2_m015_open_pip_effect = yes
		debug_log = "ZG361B2: delivered result consumed by justice runtime"
	}
	else = { debug_log = "ZG361B2: stale delivered-result adapter ignored" }
}

zg361_b2_m069_record_delivery_effect = {
	set_variable = { name = zg361_b2_notice_state value = 3 } # delivered/appeal open
	set_variable = { name = zg361_b2_delivery_year value = current_year }
	set_variable = { name = zg361_b2_delivery_method value = var:zg361_result_delivery_method }
	set_variable = { name = zg361_b2_m069_state value = 3 }
	set_variable = { name = zg361_b2_m069_receipt_serial value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m069_appeal_clock_open value = 1 }
	if = {
		limit = {
			has_variable = zg361_result_delivery_witness
			var:zg361_result_delivery_witness_receipt = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_m069_witness value = var:zg361_result_delivery_witness }
		set_variable = { name = zg361_b2_m069_witness_receipt value = var:zg361_result_delivery_witness_receipt }
	}
}

zg361_b2_m072_close_access_log_effect = {
	if = {
		limit = { var:zg361_b2_m072_pre_delivery_reads > 0 }
		set_variable = { name = zg361_b2_m072_headstart_days value = 7 }
		set_variable = { name = zg361_b2_m072_investigation_result value = 0 }
	}
	else = {
		set_variable = { name = zg361_b2_m072_state value = 3 }
		set_variable = { name = zg361_b2_m072_investigation_result value = 0 }
	}
}

zg361_b2_m081_publish_case_projection_effect = {
	set_variable = { name = zg361_b2_m081_state value = 3 }
	if = {
		limit = { has_variable = zg361_result_objection_recorded }
		set_variable = { name = zg361_b2_m081_access_level value = 2 }
		set_variable = { name = zg361_b2_m081_visible_fields value = 8 }
	}
	else = {
		set_variable = { name = zg361_b2_m081_access_level value = 1 }
		set_variable = { name = zg361_b2_m081_visible_fields value = 4 }
	}
}

# ---------------------------------------------------------------------------
# #015–#017: bounded PIP opened only after the existing settlement receipt.
# ---------------------------------------------------------------------------

zg361_b2_m015_open_pip_effect = {
	if = {
		limit = {
			var:zg361_result_grade = 1
			var:zg361_b2_m015_state = 0
		}
		set_variable = { name = zg361_b2_pip_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_pip_subject value = this }
		set_variable = { name = zg361_b2_pip_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_pip_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_pip_state value = 1 } # acknowledgement pending
		set_variable = { name = zg361_b2_pip_task_kind value = 3 } # collaboration/default
		if = {
			limit = { is_governor = yes }
			set_variable = { name = zg361_b2_pip_task_kind value = 1 } # governance, subject-controllable
		}
		else_if = {
			limit = { highest_held_title_tier >= tier_county }
			set_variable = { name = zg361_b2_pip_task_kind value = 2 } # local capability
		}
		set_variable = { name = zg361_b2_pip_task_controllable value = 1 }
		set_variable = { name = zg361_b2_pip_refusal_receipt value = 0 }
		set_variable = { name = zg361_b2_m015_state value = 1 }
		set_variable = { name = zg361_b2_m015_receipt_serial value = var:zg361_b2_pip_case }
		if = {
			limit = { is_ai = yes }
			zg361_b2_accept_pip_effect = yes
		}
		else = {
			var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_pip_prompt_owner }
			save_scope_as = zg361_b2_pip_prompt_subject
			save_scope_value_as = { name = zg361_b2_pip_prompt_cycle value = var:zg361_b2_pip_cycle }
			save_scope_value_as = { name = zg361_b2_pip_prompt_case value = var:zg361_b2_pip_case }
			save_scope_value_as = { name = zg361_b2_pip_prompt_state value = var:zg361_b2_pip_state }
			trigger_event = { id = zg361b2.40 days = 2 }
		}
	}
}

zg361_b2_accept_pip_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_subject = this
			var:zg361_b2_pip_state = 1
			var:zg361_b2_m015_receipt_serial = var:zg361_b2_pip_case
		}
		set_variable = { name = zg361_b2_pip_state value = 2 } # executing
		set_variable = { name = zg361_b2_m015_state value = 2 }
		zg361_b2_m016_commit_support_effect = yes
		zg361_b2_schedule_pip_deadline_effect = yes
	}
}

zg361_b2_negotiate_pip_effect = {
	if = {
		limit = { var:zg361_b2_pip_state = 1 }
		set_variable = { name = zg361_b2_pip_goal_revision_used value = 1 }
		set_variable = { name = zg361_b2_pip_state value = 2 }
		set_variable = { name = zg361_b2_m015_state value = 2 }
		zg361_b2_m016_commit_support_effect = yes
		zg361_b2_schedule_pip_deadline_effect = yes
	}
}

zg361_b2_refuse_pip_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_state = 1
			var:zg361_b2_pip_refusal_receipt = 0
		}
		set_variable = { name = zg361_b2_pip_refusal_receipt value = var:zg361_b2_pip_case }
		set_variable = { name = zg361_b2_pip_state value = 5 } # refused terminal
		set_variable = { name = zg361_b2_m015_state value = 5 }
		set_variable = { name = zg361_b2_next_cycle_pip_refusal_evidence value = 1 }
		# Refusal is next-cycle evidence only; it does not settle another current penalty.
		debug_log = "ZG361B2: PIP refusal recorded without current-cycle double penalty"
	}
}

zg361_b2_m016_commit_support_effect = {
	save_temporary_scope_as = zg361_b2_support_subject
	set_variable = { name = zg361_b2_pip_support_reserved value = 0 }
	var:zg361_b2_pip_owner = {
		if = {
			limit = { NOT = { has_variable = zg361_b2_pip_capacity_used } }
			set_variable = { name = zg361_b2_pip_capacity_used value = 0 }
		}
		if = {
			limit = { var:zg361_b2_pip_capacity_used < 2 }
			change_variable = { name = zg361_b2_pip_capacity_used add = 1 }
			scope:zg361_b2_support_subject = {
				set_variable = { name = zg361_b2_pip_support_reserved value = 1 }
				set_variable = { name = zg361_b2_pip_support_hours value = 1 }
				set_variable = { name = zg361_b2_pip_support_absent value = 0 }
				set_variable = { name = zg361_b2_m016_state value = 2 }
				set_variable = { name = zg361_b2_m016_receipt_serial value = var:zg361_b2_pip_case }
			}
		}
	}
	if = {
		limit = { var:zg361_b2_pip_support_reserved = 0 }
		set_variable = { name = zg361_b2_pip_support_hours value = 0 }
		set_variable = { name = zg361_b2_pip_support_absent value = 1 }
		set_variable = { name = zg361_b2_m016_state value = 1 }
		set_variable = { name = zg361_b2_m016_receipt_serial value = var:zg361_b2_pip_case }
	}
}

zg361_b2_release_pip_support_effect = {
	if = {
		limit = {
			var:zg361_b2_pip_support_reserved = 1
			var:zg361_b2_m016_receipt_serial = var:zg361_b2_pip_case
		}
		var:zg361_b2_pip_owner = {
			if = {
				limit = { has_variable = zg361_b2_pip_capacity_used var:zg361_b2_pip_capacity_used >= 1 }
				change_variable = { name = zg361_b2_pip_capacity_used add = -1 }
			}
		}
		set_variable = { name = zg361_b2_pip_support_reserved value = 0 }
		set_variable = { name = zg361_b2_pip_support_released value = 1 }
	}
}

zg361_b2_schedule_pip_deadline_effect = {
	var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_pip_deadline_owner }
	save_scope_as = zg361_b2_pip_deadline_subject
	save_scope_value_as = { name = zg361_b2_pip_deadline_cycle value = var:zg361_b2_pip_cycle }
	save_scope_value_as = { name = zg361_b2_pip_deadline_case value = var:zg361_b2_pip_case }
	save_scope_value_as = { name = zg361_b2_pip_deadline_state value = var:zg361_b2_pip_state }
	trigger_event = { id = zg361b2.100 days = 365 }
}

zg361_b2_resolve_pip_due_effect = {
	if = {
		limit = {
			has_variable = zg361_result_cycle_serial
			var:zg361_result_cycle_serial > var:zg361_b2_pip_cycle
			has_variable = zg361_last_grade
			var:zg361_last_grade >= 2
		}
		set_variable = { name = zg361_b2_pip_state value = 3 } # graduated
		set_variable = { name = zg361_b2_m015_state value = 3 }
		set_variable = { name = zg361_b2_m016_state value = 3 }
		set_variable = { name = zg361_b2_pip_graduation_receipt value = var:zg361_b2_pip_case }
		remove_character_modifier = zg361_pip
		if = {
			limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 1 }
			change_variable = { name = zg361_streak_bottom add = -1 }
		}
		zg361_b2_release_pip_support_effect = yes
	}
	else = {
		set_variable = { name = zg361_b2_pip_state value = 4 } # failed/timeout
		set_variable = { name = zg361_b2_m015_state value = 4 }
		set_variable = { name = zg361_b2_m016_state value = 4 }
		if = {
			limit = { var:zg361_b2_pip_support_absent = 1 }
			set_variable = { name = zg361_b2_pip_no_support_liability value = 1 }
			var:zg361_b2_pip_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
		zg361_b2_release_pip_support_effect = yes
		zg361_b2_m017_open_disposition_effect = yes
	}
}

zg361_b2_m017_open_disposition_effect = {
	if = {
		limit = { var:zg361_b2_pip_state = 4 var:zg361_b2_m017_state = 0 }
		set_variable = { name = zg361_b2_m017_state value = 1 }
		set_variable = { name = zg361_b2_m017_receipt_serial value = var:zg361_b2_pip_case }
		zg361_b2_m074_open_redundancy_offer_effect = yes
		if = {
			limit = { is_ai = yes }
			if = {
				limit = {
					age >= 60
					var:zg361_b2_m074_redundancy_eligible = 1
				}
				zg361_b2_m074_accept_redundancy_effect = yes
			}
			else_if = {
				limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 3 }
				zg361_b2_m074_reject_redundancy_effect = yes
				zg361_ai_elimination_effect = yes
			}
			else = {
				zg361_b2_m074_reject_redundancy_effect = yes
				zg361_eliminate_extend_effect = yes
			}
			set_variable = { name = zg361_b2_m017_state value = 3 }
		}
		else = {
			var:zg361_b2_pip_owner = { save_scope_as = zg361_b2_disposition_owner }
			save_scope_as = zg361_b2_disposition_subject
			save_scope_value_as = { name = zg361_b2_disposition_cycle value = var:zg361_b2_pip_cycle }
			save_scope_value_as = { name = zg361_b2_disposition_case value = var:zg361_b2_pip_case }
			save_scope_value_as = { name = zg361_b2_disposition_state value = var:zg361_b2_m017_state }
			trigger_event = { id = zg361b2.110 days = 1 }
		}
	}
}

# ---------------------------------------------------------------------------
# #014/#070/#077/#358 appeal opening and target-bound observation.
# ---------------------------------------------------------------------------

zg361_b2_on_appeal_filed_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_notice_state = 3
			var:zg361_result_case_state = 3
			var:zg361_result_appeal_open = 1
			var:zg361_b2_m014_state = 0
		}
		set_variable = { name = zg361_b2_appeal_state value = 1 }
		set_variable = { name = zg361_b2_appeal_reason value = 1 }
		if = {
			limit = { has_variable = zg361_result_objection_recorded }
			set_variable = { name = zg361_b2_appeal_reason value = 2 }
		}
		else_if = {
			limit = { var:zg361_b2_m072_headstart_days > 0 }
			set_variable = { name = zg361_b2_appeal_reason value = 3 }
		}
		else_if = {
			limit = { var:zg361_result_grade_reason = 5 }
			set_variable = { name = zg361_b2_appeal_reason value = 4 }
		}
		set_variable = { name = zg361_b2_appeal_evidence_revision value = var:zg361_b2_case_feedback_revision }
		set_variable = { name = zg361_b2_m014_headstart_days value = var:zg361_b2_m072_headstart_days }
		set_variable = { name = zg361_b2_m014_state value = 1 }
		set_variable = { name = zg361_b2_m014_receipt_serial value = var:zg361_b2_case_serial }
		zg361_b2_m070_open_observation_effect = yes
		zg361_b2_m077_assign_reviewer_effect = yes
		zg361_b2_m358_freeze_non_aggravation_effect = yes
		debug_log = "ZG361B2: target-bound appeal case opened"
	}
	else = { debug_log = "ZG361B2: duplicate or stale appeal filing ignored" }
}

zg361_b2_m070_open_observation_effect = {
	set_variable = { name = zg361_b2_retaliation_owner value = var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_retaliation_subject value = this }
	set_variable = { name = zg361_b2_retaliation_cycle value = var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_retaliation_case value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_retaliation_state value = 1 }
	set_variable = { name = zg361_b2_retaliation_new_fact value = 0 }
	set_variable = { name = zg361_b2_retaliation_suspended_n value = 0 }
	set_variable = { name = zg361_b2_m070_state value = 1 }
	set_variable = { name = zg361_b2_m070_receipt_serial value = var:zg361_b2_case_serial }
	var:zg361_b2_retaliation_owner = { save_scope_as = zg361_b2_retaliation_deadline_owner }
	save_scope_as = zg361_b2_retaliation_deadline_subject
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_cycle value = var:zg361_b2_retaliation_cycle }
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_case value = var:zg361_b2_retaliation_case }
	save_scope_value_as = { name = zg361_b2_retaliation_deadline_state value = var:zg361_b2_retaliation_state }
	trigger_event = { id = zg361b2.120 days = 365 }
}

zg361_b2_m077_assign_reviewer_effect = {
	set_variable = { name = zg361_b2_m077_state value = 1 }
	set_variable = { name = zg361_b2_m077_independent value = 0 }
	var:zg361_b2_case_owner = {
		if = {
			limit = { exists = liege liege = { is_alive = yes } }
			liege = { save_temporary_scope_as = zg361_b2_independent_reviewer }
		}
	}
	if = {
		limit = { exists = scope:zg361_b2_independent_reviewer }
		set_variable = { name = zg361_b2_m077_reviewer value = scope:zg361_b2_independent_reviewer }
		set_variable = { name = zg361_b2_m077_independent value = 1 }
	}
	else = { set_variable = { name = zg361_b2_m077_reviewer value = var:zg361_b2_case_owner } }
	set_variable = { name = zg361_b2_m077_quality_bonus value = 0 }
	if = {
		limit = { var:zg361_b2_m077_independent = 1 }
		set_variable = { name = zg361_b2_m077_quality_bonus value = 10 }
	}
	set_variable = { name = zg361_b2_m077_recusal_subject_used value = 0 }
	set_variable = { name = zg361_b2_m077_recusal_owner_used value = 0 }
	set_variable = { name = zg361_b2_m077_receipt_serial value = var:zg361_b2_case_serial }
}

zg361_b2_m358_freeze_non_aggravation_effect = {
	set_variable = { name = zg361_b2_m358_state value = 1 }
	set_variable = { name = zg361_b2_m358_original_grade value = var:zg361_result_grade }
	set_variable = { name = zg361_b2_m358_original_treasury value = var:zg361_result_treasury_paid }
	set_variable = { name = zg361_b2_m358_original_gold value = var:zg361_result_gold_paid }
	set_variable = { name = zg361_b2_m358_original_merit value = var:zg361_result_merit_paid }
	set_variable = { name = zg361_b2_m358_original_salary value = var:zg361_result_salary_cut_active }
	set_variable = { name = zg361_b2_m358_aggravated value = 0 }
	set_variable = { name = zg361_b2_m358_receipt_serial value = var:zg361_b2_case_serial }
}

# ---------------------------------------------------------------------------
# Appeal outcomes, responsibility/fairness consumers, and public escalation.
# ---------------------------------------------------------------------------

zg361_b2_on_appeal_upheld_effect = {
	if = {
		limit = {
			var:zg361_b2_m014_state = 1
			var:zg361_b2_m014_receipt_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_m014_state value = 4 }
		set_variable = { name = zg361_b2_appeal_state value = 4 }
		set_variable = { name = zg361_b2_m014_outcome value = 2 }
		set_variable = { name = zg361_result_appeal_open value = 0 }
		set_variable = { name = zg361_result_case_state value = 4 }
		set_variable = { name = zg361_result_appeal_outcome value = 2 }
		set_variable = { name = zg361_b2_m077_state value = 4 }
		zg361_b2_m078_update_fairness_effect = yes
		zg361_b2_m358_close_non_aggravation_effect = yes
		zg361_b2_m071_open_escalation_effect = yes
	}
}

zg361_b2_on_appeal_expired_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_b2_m069_receipt_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_notice_state value = 4 }
		set_variable = { name = zg361_b2_m069_state value = 4 }
		set_variable = { name = zg361_b2_m069_appeal_clock_open value = 0 }
		if = {
			limit = { var:zg361_b2_m014_state = 1 }
			set_variable = { name = zg361_b2_m014_state value = 5 }
			set_variable = { name = zg361_b2_appeal_state value = 5 }
		}
		# Existing AI-manager elimination resumes only after the ninety-day
		# appeal window really closes; the settlement-day D+2 shortcut is gated.
		if = {
			limit = {
				is_ai = no
				has_variable = zg361_streak_bottom
				var:zg361_streak_bottom >= 2
				var:zg361_result_case_owner = liege
				var:zg361_result_case_owner = { is_ai = yes is_alive = yes }
			}
			trigger_event = { id = zg361.6 days = 1 }
		}
	}
}

zg361_b2_on_appeal_corrected_effect = {
	if = {
		limit = {
			var:zg361_b2_case_subject = this
			var:zg361_b2_case_owner = var:zg361_result_case_owner
			var:zg361_b2_case_cycle = var:zg361_result_cycle_serial
			var:zg361_b2_case_serial = var:zg361_result_case_serial
			var:zg361_result_case_state = 5
			var:zg361_result_refund_posted_serial = var:zg361_result_case_serial
		}
		set_variable = { name = zg361_b2_notice_state value = 5 }
		set_variable = { name = zg361_b2_appeal_state value = 3 }
		set_variable = { name = zg361_b2_m014_state value = 3 }
		set_variable = { name = zg361_b2_m014_outcome value = 1 }
		set_variable = { name = zg361_b2_m077_state value = 3 }
		zg361_b2_m076_allocate_liability_effect = yes
		zg361_b2_m078_update_fairness_effect = yes
		zg361_b2_m358_close_non_aggravation_effect = yes
		zg361_b2_m359_open_quota_return_effect = yes
		debug_log = "ZG361B2: appeal correction consumed actual refund receipt"
	}
}

zg361_b2_m076_allocate_liability_effect = {
	save_temporary_scope_as = zg361_b2_liability_subject
	set_variable = { name = zg361_b2_m076_state value = 3 }
	set_variable = { name = zg361_b2_m076_direct_share value = 70 }
	set_variable = { name = zg361_b2_m076_system_share value = 30 }
	set_variable = { name = zg361_b2_m076_share_total value = 100 }
	set_variable = { name = zg361_b2_m076_receipt_serial value = var:zg361_b2_case_serial }
	var:zg361_b2_case_owner = {
		change_variable = { name = zg361_b2_management_debt add = 1 }
		set_variable = { name = zg361_b2_management_debt_source_case value = scope:zg361_b2_liability_subject.var:zg361_b2_case_serial }
	}
}

zg361_b2_m078_update_fairness_effect = {
	save_temporary_scope_as = zg361_b2_fairness_subject
	set_variable = { name = zg361_b2_m078_state value = 3 }
	set_variable = { name = zg361_b2_m078_receipt_serial value = var:zg361_b2_case_serial }
	var:zg361_b2_case_owner = {
		change_variable = { name = zg361_b2_fairness_reviewed_n add = 1 }
		if = {
			limit = { scope:zg361_b2_fairness_subject.var:zg361_b2_appeal_state = 3 }
			change_variable = { name = zg361_b2_fairness_corrected_n add = 1 }
		}
		set_variable = { name = zg361_b2_fairness_denominator value = var:zg361_b2_fairness_reviewed_n }
		set_variable = { name = zg361_b2_fairness_numerator value = 0 }
		if = {
			limit = { has_variable = zg361_b2_fairness_corrected_n }
			set_variable = { name = zg361_b2_fairness_numerator value = var:zg361_b2_fairness_corrected_n }
		}
		set_variable = { name = zg361_b2_fairness_small_sample value = 0 }
		if = {
			limit = { var:zg361_b2_fairness_denominator < 5 }
			set_variable = { name = zg361_b2_fairness_small_sample value = 1 }
		}
		if = {
			limit = {
				has_variable = zg361_b2_fairness_corrected_n
				var:zg361_b2_fairness_corrected_n >= 2
				var:zg361_b2_fairness_denominator >= 5
			}
			set_variable = { name = zg361_b2_fairness_anomaly_open value = 1 }
		}
	}
}

zg361_b2_m358_close_non_aggravation_effect = {
	if = {
		limit = {
			var:zg361_b2_m358_state = 1
			var:zg361_b2_m358_receipt_serial = var:zg361_b2_case_serial
			var:zg361_result_grade >= var:zg361_b2_m358_original_grade
			var:zg361_result_treasury_paid <= var:zg361_b2_m358_original_treasury
			var:zg361_result_gold_paid <= var:zg361_b2_m358_original_gold
			var:zg361_result_merit_paid <= var:zg361_b2_m358_original_merit
		}
		set_variable = { name = zg361_b2_m358_state value = 3 }
		set_variable = { name = zg361_b2_m358_aggravated value = 0 }
	}
	else = {
		set_variable = { name = zg361_b2_m358_state value = 4 }
		set_variable = { name = zg361_b2_m358_aggravated value = 1 }
		debug_log = "ZG361B2: non-aggravation invariant failed"
	}
}

zg361_b2_m071_open_escalation_effect = {
	set_variable = { name = zg361_b2_m071_state value = 1 }
	set_variable = { name = zg361_b2_m071_receipt_serial value = var:zg361_b2_case_serial }
	if = {
		limit = { is_ai = no }
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_escalation_owner }
		save_scope_as = zg361_b2_escalation_subject
		save_scope_value_as = { name = zg361_b2_escalation_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_escalation_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_escalation_state value = var:zg361_b2_m071_state }
		trigger_event = { id = zg361b2.50 days = 1 }
		if = {
			limit = { has_variable = zg361_streak_bottom var:zg361_streak_bottom >= 2 }
			var:zg361_b2_case_owner = { save_scope_as = zg361_b2_exit_offer_owner }
			save_scope_as = zg361_b2_exit_offer_subject
			save_scope_value_as = { name = zg361_b2_exit_offer_cycle value = var:zg361_b2_case_cycle }
			save_scope_value_as = { name = zg361_b2_exit_offer_case value = var:zg361_b2_case_serial }
			save_scope_value_as = { name = zg361_b2_exit_offer_state value = var:zg361_b2_m014_state }
			trigger_event = { id = zg361b2.60 days = 2 }
		}
	}
	else = { set_variable = { name = zg361_b2_m071_state value = 4 } }
}

zg361_b2_publish_evidence_escalation_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 2 }
		set_variable = { name = zg361_b2_m071_evidence_strength value = 1 }
		if = {
			limit = { var:zg361_b2_m081_visible_fields >= 8 }
			set_variable = { name = zg361_b2_m071_evidence_strength value = 2 }
		}
		set_variable = { name = zg361_b2_m071_publication_identity value = this }
		set_variable = {
			name = zg361_b2_m071_evidence_hash
			value = {
				value = var:zg361_b2_case_serial
				multiply = 10
				add = var:zg361_b2_appeal_evidence_revision
			}
		}
		set_variable = { name = zg361_b2_m071_factcheck_state value = 1 }
		var:zg361_b2_case_owner = { save_scope_as = zg361_b2_factcheck_owner }
		save_scope_as = zg361_b2_factcheck_subject
		save_scope_value_as = { name = zg361_b2_factcheck_cycle value = var:zg361_b2_case_cycle }
		save_scope_value_as = { name = zg361_b2_factcheck_case value = var:zg361_b2_case_serial }
		save_scope_value_as = { name = zg361_b2_factcheck_state value = var:zg361_b2_m071_factcheck_state }
		trigger_event = { id = zg361b2.141 days = 30 }
		add_prestige = { value = 0 subtract = 50 }
		zg361_b2_m079_open_skip_level_effect = yes
		zg361_b2_m080_open_metric_defect_effect = yes
	}
}

zg361_b2_publish_anonymous_report_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 3 }
		zg361_b2_m073_triage_report_effect = yes
	}
}

zg361_b2_defer_escalation_effect = {
	if = {
		limit = { var:zg361_b2_m071_state = 1 }
		set_variable = { name = zg361_b2_m071_state value = 4 }
		set_variable = { name = zg361_b2_m071_policy_debt value = 1 }
	}
}

zg361_b2_m073_triage_report_effect = {
	set_variable = { name = zg361_b2_m073_state value = 2 }
	set_variable = { name = zg361_b2_m073_receipt_serial value = var:zg361_b2_case_serial }
	set_variable = { name = zg361_b2_m073_provenance value = this }
	set_variable = {
		name = zg361_b2_m073_material_hash
		value = {
			value = var:zg361_b2_case_serial
			multiply = 10
			add = var:zg361_b2_appeal_reason
		}
	}
	set_variable = { name = zg361_b2_m073_truth_finding value = 0 }
	if = {
		limit = {
			OR = {
				has_variable = zg361_result_objection_recorded
				var:zg361_result_grade_reason > 0
			}
		}
		set_variable = { name = zg361_b2_m073_public_interest value = 1 }
		set_variable = { name = zg361_b2_m073_truth_finding value = 1 }
		set_variable = { name = zg361_b2_m073_protected value = 1 }
		set_variable = { name = zg361_b2_m073_state value = 3 }
		zg361_b2_m080_open_metric_defect_effect = yes
	}
	else = {
		set_variable = { name = zg361_b2_m073_malicious value = 1 }
		set_variable = { name = zg361_b2_m073_truth_finding value = 2 }
		set_variable = { name = zg361_b2_m073_state value = 4 }
		add_prestige = { value = 0 subtract = 50 }
	}
}

# ---------------------------------------------------------------------------
# #074 honest redundancy and #075 voluntary exit. Both transfer only from an
# actually funded owner treasury and release HC only after an actual exit.
# ---------------------------------------------------------------------------

zg361_b2_m074_open_redundancy_offer_effect = {
	if = {
		limit = { var:zg361_b2_m074_state = 0 }
		set_variable = { name = zg361_b2_m074_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m074_subject value = this }
		set_variable = { name = zg361_b2_m074_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m074_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m074_state value = 1 }
		set_variable = { name = zg361_b2_m074_reason value = 1 } # organizational redundancy
		set_variable = { name = zg361_b2_m074_offer_gold value = 50 }
		set_variable = { name = zg361_b2_m074_redundancy_eligible value = 0 }
		set_variable = { name = zg361_b2_m074_treasury_paid value = 0 }
		set_variable = { name = zg361_b2_m074_personal_received value = 0 }
		set_variable = { name = zg361_b2_m074_actual_exit value = 0 }
		set_variable = { name = zg361_b2_m074_hc_released value = 0 }
		set_variable = { name = zg361_b2_m074_receipt_serial value = var:zg361_b2_case_serial }
		if = {
			limit = {
				var:zg361_b2_m074_owner = {
					government_has_flag = government_has_treasury
					treasury >= 50
				}
			}
			set_variable = { name = zg361_b2_m074_redundancy_eligible value = 1 }
		}
	}
}

zg361_b2_m074_accept_redundancy_effect = {
	if = {
		limit = {
			var:zg361_b2_m074_owner = var:zg361_b2_case_owner
			var:zg361_b2_m074_subject = this
			var:zg361_b2_m074_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m074_case = var:zg361_b2_case_serial
			var:zg361_b2_m074_state = 1
			var:zg361_b2_m074_redundancy_eligible = 1
			var:zg361_b2_m074_receipt_serial = var:zg361_b2_m074_case
			var:zg361_b2_m074_owner = {
				government_has_flag = government_has_treasury
				treasury >= 50
			}
		}
		var:zg361_b2_m074_owner = { remove_treasury = 50 }
		add_gold = 50
		set_variable = { name = zg361_b2_m074_treasury_paid value = 50 }
		set_variable = { name = zg361_b2_m074_personal_received value = 50 }
		set_variable = { name = zg361_b2_m074_neutral_record value = 1 }
		set_variable = { name = zg361_b2_m074_actual_exit value = 1 }
		set_variable = { name = zg361_b2_m074_hc_released value = 1 }
		set_variable = { name = zg361_b2_m074_state value = 3 }
		var:zg361_b2_m074_owner = { save_scope_as = zg361_b2_redundancy_audit_owner }
		save_scope_as = zg361_b2_redundancy_audit_subject
		save_scope_value_as = { name = zg361_b2_redundancy_audit_cycle value = var:zg361_b2_m074_cycle }
		save_scope_value_as = { name = zg361_b2_redundancy_audit_case value = var:zg361_b2_m074_case }
		save_scope_value_as = { name = zg361_b2_redundancy_audit_state value = var:zg361_b2_m074_state }
		trigger_event = { id = zg361b2.171 days = 30 }
		force_step_down_landed_titles = yes
	}
}

zg361_b2_m074_reject_redundancy_effect = {
	if = {
		limit = { var:zg361_b2_m074_state = 1 }
		set_variable = { name = zg361_b2_m074_state value = 5 }
		set_variable = { name = zg361_b2_m074_redundancy_eligible value = 0 }
	}
}

zg361_b2_m075_open_exit_offer_effect = {
	if = {
		limit = { var:zg361_b2_m075_state = 0 }
		set_variable = { name = zg361_b2_m075_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m075_subject value = this }
		set_variable = { name = zg361_b2_m075_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m075_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m075_state value = 1 }
		set_variable = { name = zg361_b2_m075_offer_gold value = 50 }
		set_variable = { name = zg361_b2_m075_receipt_serial value = var:zg361_b2_case_serial }
		var:zg361_b2_m075_owner = { save_scope_as = zg361_b2_exit_deadline_owner }
		save_scope_as = zg361_b2_exit_deadline_subject
		save_scope_value_as = { name = zg361_b2_exit_deadline_cycle value = var:zg361_b2_m075_cycle }
		save_scope_value_as = { name = zg361_b2_exit_deadline_case value = var:zg361_b2_m075_case }
		save_scope_value_as = { name = zg361_b2_exit_deadline_state value = var:zg361_b2_m075_state }
		trigger_event = { id = zg361b2.61 days = 30 }
	}
}

zg361_b2_m075_accept_exit_offer_effect = {
	if = {
		limit = {
			var:zg361_b2_m075_owner = var:zg361_b2_case_owner
			var:zg361_b2_m075_subject = this
			var:zg361_b2_m075_cycle = var:zg361_b2_case_cycle
			var:zg361_b2_m075_case = var:zg361_b2_case_serial
			var:zg361_b2_m075_state = 1
			var:zg361_b2_m075_receipt_serial = var:zg361_b2_case_serial
			var:zg361_b2_case_owner = {
				government_has_flag = government_has_treasury
				treasury >= 50
			}
		}
		var:zg361_b2_case_owner = { remove_treasury = 50 }
		add_gold = 50
		set_variable = { name = zg361_b2_m075_treasury_paid value = 50 }
		set_variable = { name = zg361_b2_m075_personal_received value = 50 }
		set_variable = { name = zg361_b2_m075_state value = 3 }
		set_variable = { name = zg361_b2_m075_neutral_record value = 1 }
		set_variable = { name = zg361_b2_m075_actual_exit value = 1 }
		set_variable = { name = zg361_b2_m075_hc_released value = 1 }
		force_step_down_landed_titles = yes
	}
}

zg361_b2_m075_reject_exit_offer_effect = {
	if = {
		limit = { var:zg361_b2_m075_state = 1 }
		set_variable = { name = zg361_b2_m075_state value = 4 }
		# Refusal moves to ordinary PIP/appeal and transfers no resource.
	}
}

# ---------------------------------------------------------------------------
# #079/#080: skip-level investigation and a target-bound metric-defect ticket.
# ---------------------------------------------------------------------------

zg361_b2_m079_open_skip_level_effect = {
	set_variable = { name = zg361_b2_m079_state value = 1 }
	set_variable = { name = zg361_b2_m079_receipt_serial value = var:zg361_b2_case_serial }
	var:zg361_b2_case_owner = {
		if = {
			limit = { exists = liege liege = { is_alive = yes } }
			liege = { save_temporary_scope_as = zg361_b2_skip_level_reviewer }
		}
	}
	if = {
		limit = { exists = scope:zg361_b2_skip_level_reviewer }
		set_variable = { name = zg361_b2_m079_reviewer value = scope:zg361_b2_skip_level_reviewer }
		set_variable = { name = zg361_b2_m079_seat_reserved value = 0 }
		save_temporary_scope_as = zg361_b2_skip_subject
		scope:zg361_b2_skip_level_reviewer = {
			if = {
				limit = { NOT = { has_variable = zg361_b2_skip_seats_used } }
				set_variable = { name = zg361_b2_skip_seats_used value = 0 }
			}
			if = {
				limit = { var:zg361_b2_skip_seats_used < 2 }
				change_variable = { name = zg361_b2_skip_seats_used add = 1 }
				scope:zg361_b2_skip_subject = { set_variable = { name = zg361_b2_m079_seat_reserved value = 1 } }
			}
		}
		if = {
			limit = { var:zg361_b2_m079_seat_reserved = 1 }
			scope:zg361_b2_skip_level_reviewer = { save_scope_as = zg361_b2_skip_deadline_owner }
			save_scope_as = zg361_b2_skip_deadline_subject
			save_scope_value_as = { name = zg361_b2_skip_deadline_cycle value = var:zg361_b2_case_cycle }
			save_scope_value_as = { name = zg361_b2_skip_deadline_case value = var:zg361_b2_case_serial }
			save_scope_value_as = { name = zg361_b2_skip_deadline_state value = var:zg361_b2_m079_state }
			trigger_event = { id = zg361b2.140 days = 30 }
		}
		else = { set_variable = { name = zg361_b2_m079_state value = 4 } }
	}
	else = { set_variable = { name = zg361_b2_m079_state value = 4 } }
}

zg361_b2_m079_release_seat_effect = {
	if = {
		limit = {
			var:zg361_b2_m079_seat_reserved = 1
			has_variable = zg361_b2_m079_reviewer
		}
		var:zg361_b2_m079_reviewer = {
			if = {
				limit = { has_variable = zg361_b2_skip_seats_used var:zg361_b2_skip_seats_used >= 1 }
				change_variable = { name = zg361_b2_skip_seats_used add = -1 }
			}
		}
		set_variable = { name = zg361_b2_m079_seat_reserved value = 0 }
		set_variable = { name = zg361_b2_m079_seat_released value = 1 }
	}
}

zg361_b2_m080_open_metric_defect_effect = {
	if = {
		limit = { var:zg361_b2_m080_state = 0 }
		set_variable = { name = zg361_b2_m080_state value = 1 }
		set_variable = { name = zg361_b2_m080_owner value = var:zg361_b2_case_owner }
		set_variable = { name = zg361_b2_m080_subject value = this }
		set_variable = { name = zg361_b2_m080_cycle value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m080_case value = var:zg361_b2_case_serial }
		set_variable = { name = zg361_b2_m080_metric_version value = var:zg361_b2_case_cycle }
		set_variable = { name = zg361_b2_m080_receipt_serial value = var:zg361_b2_case_serial }
		var:zg361_b2_m080_owner = { save_scope_as = zg361_b2_metric_deadline_owner }
		save_scope_as = zg361_b2_metric_deadline_subject
		save_scope_value_as = { name = zg361_b2_metric_deadline_cycle value = var:zg361_b2_m080_cycle }
		save_scope_value_as = { name = zg361_b2_metric_deadline_case value = var:zg361_b2_m080_case }
		save_scope_value_as = { name = zg361_b2_metric_deadline_state value = var:zg361_b2_m080_state }
		trigger_event = { id = zg361b2.150 days = 90 }
	}
}

# ---------------------------------------------------------------------------
# #070/#074/#358 adverse-action gate.  Core disposition effects call prepare,
# execute only when allowed, then call finish.  A new fact creates and serves a
# distinct misconduct notice instead of aggravating the appealed case.
# ---------------------------------------------------------------------------

zg361_b2_prepare_adverse_action_effect = {
	set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
	if = {
		limit = {
			has_variable = zg361_b2_separate_action_authorized
			var:zg361_b2_separate_action_authorized = 1
		}
		set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
	}
	else_if = {
		# The base result itself grants a ninety-day appeal window.  No D+2
		# elimination may outrun that window even before the subject files.
		limit = {
			has_variable = zg361_result_appeal_open
			var:zg361_result_appeal_open = 1
			has_variable = zg361_result_case_state
			var:zg361_result_case_state = 3
			NOT = { has_variable = zg361_b2_retaliation_state }
		}
		set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
		set_variable = { name = zg361_b2_m074_state value = 2 }
		set_variable = { name = zg361_b2_m074_reason value = 4 } # appeal window pending
		set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
		set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
		debug_log = "ZG361B2: adverse action held until base appeal window closes"
	}
	else_if = {
		limit = {
			has_variable = zg361_b2_retaliation_state
			var:zg361_b2_retaliation_state = 1
			var:zg361_b2_retaliation_subject = this
		}
		if = {
			limit = { var:zg361_b2_retaliation_new_fact = 1 }
			set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
			set_variable = { name = zg361_b2_m070_finding value = 2 } # new fact, separate case
			set_variable = { name = zg361_b2_m074_state value = 3 }
			set_variable = { name = zg361_b2_m074_reason value = 1 }
			zg361_b2_m358_open_separate_case_effect = yes
			if = {
				limit = { is_ai = yes }
				zg361_b2_deliver_separate_case_effect = yes
				set_variable = { name = zg361_b2_separate_action_authorized value = 1 }
				set_variable = { name = zg361_b2_adverse_action_allowed value = 1 }
			}
		}
		else = {
			set_variable = { name = zg361_b2_adverse_action_allowed value = 0 }
			change_variable = { name = zg361_b2_retaliation_suspended_n add = 1 }
			set_variable = { name = zg361_b2_m070_finding value = 1 } # pending independent review
			set_variable = { name = zg361_b2_m074_state value = 2 }
			set_variable = { name = zg361_b2_m074_reason value = 2 }
			set_variable = { name = zg361_b2_m074_disguised_performance_exit value = 1 }
			set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
			var:zg361_b2_retaliation_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			debug_log = "ZG361B2: unsupported post-appeal adverse action suspended"
		}
	}
	else = {
		set_variable = { name = zg361_b2_m074_state value = 1 }
		set_variable = { name = zg361_b2_m074_reason value = 3 }
	}
	set_variable = { name = zg361_b2_m074_receipt_serial value = var:zg361_result_case_serial }
}

zg361_b2_finish_adverse_action_effect = {
	remove_variable = zg361_b2_pending_adverse_action
	remove_variable = zg361_b2_adverse_action_allowed
	remove_variable = zg361_b2_separate_action_authorized
}

zg361_b2_cancel_blocked_action_effect = {
	remove_variable = zg361_b2_adverse_action_allowed
	if = {
		limit = { NOT = { has_variable = zg361_b2_separate_notice_state } }
		remove_variable = zg361_b2_pending_adverse_action
	}
}

zg361_b2_m358_open_separate_case_effect = {
	if = {
		limit = { var:zg361_b2_m358_state >= 1 }
		set_variable = { name = zg361_b2_m358_separate_case value = { value = var:zg361_b2_case_serial add = 100000 } }
		set_variable = { name = zg361_b2_separate_notice_owner value = var:zg361_b2_retaliation_owner }
		set_variable = { name = zg361_b2_separate_notice_subject value = this }
		set_variable = { name = zg361_b2_separate_notice_cycle value = var:zg361_b2_retaliation_cycle }
		set_variable = { name = zg361_b2_separate_notice_case value = var:zg361_b2_m358_separate_case }
		set_variable = { name = zg361_b2_separate_notice_state value = 1 }
		set_variable = { name = zg361_b2_m358_state value = 2 }
		if = {
			limit = { is_ai = no }
			var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_prompt_owner }
			save_scope_as = zg361_b2_separate_prompt_subject
			save_scope_value_as = { name = zg361_b2_separate_prompt_cycle value = var:zg361_b2_separate_notice_cycle }
			save_scope_value_as = { name = zg361_b2_separate_prompt_case value = var:zg361_b2_separate_notice_case }
			save_scope_value_as = { name = zg361_b2_separate_prompt_state value = var:zg361_b2_separate_notice_state }
			trigger_event = { id = zg361b2.160 days = 1 }
		}
	}
}

zg361_b2_deliver_separate_case_effect = {
	if = {
		limit = {
			OR = {
				var:zg361_b2_separate_notice_state = 1
				var:zg361_b2_separate_notice_state = 2
			}
		}
		set_variable = { name = zg361_b2_separate_notice_state value = 3 }
		set_variable = { name = zg361_b2_separate_delivery_receipt value = var:zg361_b2_separate_notice_case }
		set_variable = { name = zg361_b2_separate_appeal_open value = 1 }
		var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_deadline_owner }
		save_scope_as = zg361_b2_separate_deadline_subject
		save_scope_value_as = { name = zg361_b2_separate_deadline_cycle value = var:zg361_b2_separate_notice_cycle }
		save_scope_value_as = { name = zg361_b2_separate_deadline_case value = var:zg361_b2_separate_notice_case }
		save_scope_value_as = { name = zg361_b2_separate_deadline_state value = var:zg361_b2_separate_notice_state }
		trigger_event = { id = zg361b2.162 days = 90 }
	}
}

zg361_b2_execute_pending_adverse_action_effect = {
	if = {
		limit = {
			var:zg361_b2_separate_notice_state = 3
			var:zg361_b2_separate_delivery_receipt = var:zg361_b2_separate_notice_case
			has_variable = zg361_b2_pending_adverse_action
		}
		set_variable = { name = zg361_b2_separate_action_authorized value = 1 }
		if = { limit = { var:zg361_b2_pending_adverse_action = 1 } zg361_eliminate_purge_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 2 } zg361_eliminate_stepdown_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 3 } zg361_eliminate_demote_effect = yes }
		else_if = { limit = { var:zg361_b2_pending_adverse_action = 4 } zg361_eliminate_extend_effect = yes }
	}
}

# ---------------------------------------------------------------------------
# #359 quota return: reserve, boundary review/redelivery, or next-cycle debt.
# ---------------------------------------------------------------------------

zg361_b2_m359_open_quota_return_effect = {
	if = {
		limit = { var:zg361_b2_m359_state = 0 }
		set_variable = { name = zg361_b2_m359_state value = 1 }
		set_variable = { name = zg361_b2_m359_receipt_serial value = var:zg361_b2_case_serial }
		if = {
			limit = {
				var:zg361_b2_case_owner = { is_ai = no zg361_is_celestial_liege_trigger = yes }
			}
			var:zg361_b2_case_owner = { save_scope_as = zg361_b2_quota_return_owner }
			save_scope_as = zg361_b2_quota_return_subject
			save_scope_value_as = { name = zg361_b2_quota_return_cycle value = var:zg361_b2_case_cycle }
			save_scope_value_as = { name = zg361_b2_quota_return_case value = var:zg361_b2_case_serial }
			save_scope_value_as = { name = zg361_b2_quota_return_state value = var:zg361_b2_m359_state }
			var:zg361_b2_case_owner = { trigger_event = { id = zg361b2.130 days = 1 } }
		}
		else = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

zg361_b2_m359_consume_reserve_effect = {
	save_temporary_scope_as = zg361_b2_reserve_subject
	var:zg361_b2_case_owner = {
		if = {
			limit = { has_variable = zg361_b2_quota_reserve var:zg361_b2_quota_reserve >= 1 }
			change_variable = { name = zg361_b2_quota_reserve add = -1 }
			scope:zg361_b2_reserve_subject = {
				set_variable = { name = zg361_b2_m359_state value = 2 }
				set_variable = { name = zg361_b2_m359_route value = 1 }
				set_variable = { name = zg361_b2_m359_reserved_consumed value = 1 }
			}
		}
	}
}

zg361_b2_m359_post_next_cycle_debt_effect = {
	if = {
		limit = { var:zg361_b2_m359_state = 1 }
		save_temporary_scope_as = zg361_b2_quota_debt_subject
		set_variable = { name = zg361_b2_m359_state value = 2 }
		set_variable = { name = zg361_b2_m359_route value = 3 }
		set_variable = { name = zg361_b2_m359_debt_added value = 1 }
		var:zg361_b2_case_owner = {
			change_variable = { name = zg361_b2_quota_debt add = 1 }
			set_variable = { name = zg361_b2_quota_debt_due_cycle value = { value = scope:zg361_b2_quota_debt_subject.var:zg361_b2_case_cycle add = 1 } }
			set_variable = { name = zg361_b2_quota_debt_source_case value = scope:zg361_b2_quota_debt_subject.var:zg361_b2_case_serial }
		}
	}
}

zg361_b2_m359_open_boundary_review_effect = {
	if = {
		limit = { var:zg361_b2_m359_state = 1 }
		save_temporary_scope_as = zg361_b2_corrected_subject
		var:zg361_b2_case_owner = { save_temporary_scope_as = zg361_b2_boundary_owner }
		var:zg361_b2_case_owner = {
			ordered_vassal = {
				limit = {
					NOT = { this = scope:zg361_b2_corrected_subject }
					has_variable = zg361_result_case_owner
					var:zg361_result_case_owner = scope:zg361_b2_boundary_owner
					has_variable = zg361_result_cycle_serial
					var:zg361_result_cycle_serial = scope:zg361_b2_corrected_subject.var:zg361_b2_case_cycle
					has_variable = zg361_result_grade
					var:zg361_result_grade = 2
				}
				order_by = var:zg361_result_rank_frozen
				position = 0
				save_scope_as = zg361_b2_boundary_subject
			}
		}
		if = {
			limit = { exists = scope:zg361_b2_boundary_subject }
			set_variable = { name = zg361_b2_m359_state value = 2 }
			set_variable = { name = zg361_b2_m359_route value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_subject value = scope:zg361_b2_boundary_subject }
			set_variable = { name = zg361_b2_m359_corrected_grade_before value = 1 }
			set_variable = { name = zg361_b2_m359_corrected_grade_after value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_grade_before value = 2 }
			set_variable = { name = zg361_b2_m359_boundary_grade_after value = 1 }
			scope:zg361_b2_boundary_subject = { zg361_b2_prepare_boundary_redelivery_effect = yes }
		}
		else = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

zg361_b2_prepare_boundary_redelivery_effect = {
	set_variable = { name = zg361_b2_redelivery_source_subject value = scope:zg361_b2_corrected_subject }
	set_variable = { name = zg361_b2_redelivery_owner value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_owner }
	set_variable = { name = zg361_b2_redelivery_subject value = this }
	set_variable = { name = zg361_b2_redelivery_cycle value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_cycle }
	set_variable = { name = zg361_b2_redelivery_case value = { value = scope:zg361_b2_corrected_subject.var:zg361_b2_case_serial add = 200000 } }
	set_variable = { name = zg361_b2_redelivery_state value = 1 }
	set_variable = { name = zg361_b2_redelivery_contested value = 0 }
	set_variable = { name = zg361_b2_redelivery_receipt value = 0 }
	if = {
		limit = { is_ai = yes }
		set_variable = { name = zg361_b2_redelivery_method value = 4 }
		zg361_b2_deliver_boundary_notice_effect = yes
	}
	else = {
		var:zg361_b2_redelivery_owner = { save_scope_as = zg361_b2_redelivery_prompt_owner }
		save_scope_as = zg361_b2_redelivery_prompt_subject
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_cycle value = var:zg361_b2_redelivery_cycle }
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_case value = var:zg361_b2_redelivery_case }
		save_scope_value_as = { name = zg361_b2_redelivery_prompt_state value = var:zg361_b2_redelivery_state }
		trigger_event = { id = zg361b2.131 days = 1 }
	}
}

zg361_b2_deliver_boundary_notice_effect = {
	if = {
		limit = {
			OR = {
				var:zg361_b2_redelivery_state = 1
				var:zg361_b2_redelivery_state = 2
			}
		}
		set_variable = { name = zg361_b2_redelivery_state value = 3 }
		set_variable = { name = zg361_b2_redelivery_receipt value = var:zg361_b2_redelivery_case }
		zg361_b2_apply_boundary_redelivery_effect = yes
	}
}

zg361_b2_contest_boundary_notice_effect = {
	if = {
		limit = {
			var:zg361_b2_redelivery_state = 3
			var:zg361_b2_redelivery_receipt = var:zg361_b2_redelivery_case
		}
		set_variable = { name = zg361_b2_redelivery_contested value = 1 }
		set_variable = { name = zg361_b2_redelivery_state value = 4 }
		set_variable = { name = zg361_result_objection_recorded value = 1 }
		zg361_b2_on_appeal_filed_effect = yes
	}
}

zg361_b2_apply_boundary_redelivery_effect = {
	if = {
		limit = {
			var:zg361_b2_redelivery_state = 3
			var:zg361_b2_redelivery_receipt = var:zg361_b2_redelivery_case
			var:zg361_result_case_owner = var:zg361_b2_redelivery_owner
			var:zg361_result_cycle_serial = var:zg361_b2_redelivery_cycle
			var:zg361_result_grade = 2
			var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
		}
		remove_character_modifier = zg361_grade_35
		set_variable = { name = zg361_last_grade value = 1 }
		set_variable = { name = zg361_result_grade value = 1 }
		set_variable = { name = zg361_result_grade_reason value = 9 }
		set_variable = { name = zg361_result_case_state value = 3 }
		set_variable = { name = zg361_result_delivery_method value = var:zg361_b2_redelivery_method }
		set_variable = { name = zg361_result_delivered_year value = current_year }
		set_variable = { name = zg361_result_settlement_posted_serial value = 0 }
		set_variable = { name = zg361_result_refund_posted_serial value = 0 }
		set_variable = { name = zg361_result_treasury_paid value = 0 }
		set_variable = { name = zg361_result_gold_paid value = 0 }
		set_variable = { name = zg361_result_merit_paid value = 0 }
		set_variable = { name = zg361_result_treasury_refunded value = 0 }
		set_variable = { name = zg361_result_gold_refunded value = 0 }
		set_variable = { name = zg361_result_merit_refunded value = 0 }
		set_variable = { name = zg361_result_salary_cut_active value = 0 }
		set_variable = { name = zg361_result_appeal_open value = 0 }
		save_temporary_scope_as = zg361_b2_adjusted_boundary_subject
		var:zg361_b2_redelivery_owner = {
			if = {
				limit = {
					has_variable = zg361_review_serial
					var:zg361_review_serial = scope:zg361_b2_adjusted_boundary_subject.var:zg361_b2_redelivery_cycle
					has_variable = zg361_last_35_n
					var:zg361_last_35_n >= 1
				}
				change_variable = { name = zg361_last_35_n add = -1 }
				change_variable = { name = zg361_last_325_n add = 1 }
			}
			set_variable = { name = zg361_b2_scoreboard_redelivery_dirty value = 1 }
		}
		var:zg361_b2_redelivery_source_subject = {
			set_variable = { name = zg361_b2_m359_state value = 3 }
			set_variable = { name = zg361_b2_m359_redelivery_subject value = scope:zg361_b2_adjusted_boundary_subject }
			set_variable = { name = zg361_b2_m359_redelivery_receipt value = scope:zg361_b2_adjusted_boundary_subject.var:zg361_b2_redelivery_case }
		}
		# Reuse the proven product settlement and appeal/refund chain.  The
		# redelivery receipt authorizes this reset once; all actual money/merit
		# writes and the new D+90 appeal timer remain owned by the core effect.
		zg361_b2_on_result_frozen_effect = yes
		zg361_settle_delivered_325_effect = yes
	}
}

zg361_b2_apply_due_quota_debt_effect = {
	if = {
		limit = {
			has_variable = zg361_b2_quota_debt
			var:zg361_b2_quota_debt >= 1
			has_variable = zg361_b2_quota_debt_due_cycle
			var:zg361_review_serial >= var:zg361_b2_quota_debt_due_cycle
			trigger_if = {
				limit = { has_variable = zg361_b2_quota_debt_consumed_cycle }
				NOT = { var:zg361_b2_quota_debt_consumed_cycle = var:zg361_review_serial }
			}
			trigger_else = { always = yes }
		}
		change_variable = { name = zg361_bottom_slots add = var:zg361_b2_quota_debt }
		set_variable = { name = zg361_b2_quota_debt_consumed_slots value = var:zg361_b2_quota_debt }
		set_variable = { name = zg361_b2_quota_debt value = 0 }
		set_variable = { name = zg361_b2_quota_debt_consumed_cycle value = var:zg361_review_serial }
		debug_log = "ZG361B2: next-cycle quota debt consumed once"
	}
}

# Management responsibility and metric-risk debts are consumed by the next
# real KPI computation of that manager, never by the appealed subject's case.
zg361_b2_consume_management_debt_effect = {
	if = {
		limit = { has_variable = zg361_b2_management_debt var:zg361_b2_management_debt >= 1 }
		set_variable = { name = zg361_b2_management_debt_applied value = { value = var:zg361_b2_management_debt multiply = 10 max = 30 } }
		change_variable = { name = zg361_evidence_organization subtract = var:zg361_b2_management_debt_applied }
		change_variable = { name = zg361_kpi subtract = var:zg361_b2_management_debt_applied }
		set_variable = { name = zg361_b2_management_debt value = 0 }
		set_variable = { name = zg361_b2_management_debt_consumed_year value = current_year }
	}
}
''')


def render_events() -> bytes:
    return generated(r'''
namespace = zg361b2

# #015 acknowledgement. Visible events are player-only; AI subjects take the
# same effects silently at the call site.
zg361b2.40 = {
	type = character_event
	theme = vassal
	title = zg361b2.40.t
	desc = zg361b2.40.desc
	trigger = {
		is_ai = no
		has_game_rule = zg361_on
		exists = scope:zg361_b2_pip_prompt_owner
		exists = scope:zg361_b2_pip_prompt_subject
		this = scope:zg361_b2_pip_prompt_subject
		var:zg361_b2_pip_owner = scope:zg361_b2_pip_prompt_owner
		var:zg361_b2_pip_subject = scope:zg361_b2_pip_prompt_subject
		var:zg361_b2_pip_cycle = scope:zg361_b2_pip_prompt_cycle
		var:zg361_b2_pip_case = scope:zg361_b2_pip_prompt_case
		var:zg361_b2_pip_state = scope:zg361_b2_pip_prompt_state
		var:zg361_b2_pip_state = 1
	}
	option = { name = zg361b2.40.a zg361_b2_accept_pip_effect = yes }
	option = { name = zg361b2.40.b zg361_b2_negotiate_pip_effect = yes }
	option = { name = zg361b2.40.c zg361_b2_refuse_pip_effect = yes }
}

# #071/#073 escalation after an upheld appeal.
zg361b2.50 = {
	type = character_event
	theme = vassal
	title = zg361b2.50.t
	desc = zg361b2.50.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_escalation_owner
		exists = scope:zg361_b2_escalation_subject
		this = scope:zg361_b2_escalation_subject
		var:zg361_b2_case_owner = scope:zg361_b2_escalation_owner
		var:zg361_b2_case_subject = scope:zg361_b2_escalation_subject
		var:zg361_b2_case_cycle = scope:zg361_b2_escalation_cycle
		var:zg361_b2_case_serial = scope:zg361_b2_escalation_case
		var:zg361_b2_m071_state = scope:zg361_b2_escalation_state
		var:zg361_b2_m071_state = 1
	}
	option = { name = zg361b2.50.a zg361_b2_publish_evidence_escalation_effect = yes }
	option = { name = zg361b2.50.b zg361_b2_publish_anonymous_report_effect = yes }
	option = { name = zg361b2.50.c zg361_b2_defer_escalation_effect = yes }
}

# #075 voluntary exit; the option is absent unless the frozen owner can fund
# the exact fifty-treasury / fifty-personal-gold transfer.
zg361b2.60 = {
	type = character_event
	theme = vassal
	title = zg361b2.60.t
	desc = zg361b2.60.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_exit_offer_owner
		exists = scope:zg361_b2_exit_offer_subject
		this = scope:zg361_b2_exit_offer_subject
		var:zg361_b2_case_owner = scope:zg361_b2_exit_offer_owner
		var:zg361_b2_case_subject = scope:zg361_b2_exit_offer_subject
		var:zg361_b2_case_cycle = scope:zg361_b2_exit_offer_cycle
		var:zg361_b2_case_serial = scope:zg361_b2_exit_offer_case
		var:zg361_b2_m014_state = scope:zg361_b2_exit_offer_state
		var:zg361_b2_m014_state = 4
	}
	immediate = { zg361_b2_m075_open_exit_offer_effect = yes }
	option = {
		name = zg361b2.60.a
		trigger = {
			var:zg361_b2_case_owner = {
				government_has_flag = government_has_treasury
				treasury >= 50
			}
		}
		zg361_b2_m075_accept_exit_offer_effect = yes
	}
	option = { name = zg361b2.60.b zg361_b2_m075_reject_exit_offer_effect = yes }
}

zg361b2.61 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_exit_deadline_owner
				exists = scope:zg361_b2_exit_deadline_subject
				this = scope:zg361_b2_exit_deadline_subject
				var:zg361_b2_m075_owner = scope:zg361_b2_exit_deadline_owner
				var:zg361_b2_m075_subject = scope:zg361_b2_exit_deadline_subject
				var:zg361_b2_m075_cycle = scope:zg361_b2_exit_deadline_cycle
				var:zg361_b2_m075_case = scope:zg361_b2_exit_deadline_case
				var:zg361_b2_m075_state = scope:zg361_b2_exit_deadline_state
				var:zg361_b2_m075_state = 1
			}
			set_variable = { name = zg361_b2_m075_state value = 5 }
			set_variable = { name = zg361_b2_m075_expired value = 1 }
		}
		else = { debug_log = "ZG361B2: stale voluntary-exit D+30 ticket ignored" }
	}
}

# #015/#016 D+365 outcome. Every component of the immutable ticket must match.
zg361b2.100 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_pip_deadline_owner
				exists = scope:zg361_b2_pip_deadline_subject
				this = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_owner = scope:zg361_b2_pip_deadline_owner
				var:zg361_b2_pip_subject = scope:zg361_b2_pip_deadline_subject
				var:zg361_b2_pip_cycle = scope:zg361_b2_pip_deadline_cycle
				var:zg361_b2_pip_case = scope:zg361_b2_pip_deadline_case
				var:zg361_b2_pip_state = scope:zg361_b2_pip_deadline_state
				var:zg361_b2_pip_state = 2
			}
			zg361_b2_resolve_pip_due_effect = yes
		}
		else = { debug_log = "ZG361B2: stale PIP D+365 ticket ignored" }
	}
}

# #017 bounded post-PIP disposition; any active appeal observation still passes
# through the common adverse-action gate in the four core disposition effects.
zg361b2.110 = {
	type = character_event
	theme = vassal
	title = zg361b2.110.t
	desc = zg361b2.110.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_disposition_owner
		exists = scope:zg361_b2_disposition_subject
		this = scope:zg361_b2_disposition_subject
		var:zg361_b2_pip_owner = scope:zg361_b2_disposition_owner
		var:zg361_b2_pip_subject = scope:zg361_b2_disposition_subject
		var:zg361_b2_pip_cycle = scope:zg361_b2_disposition_cycle
		var:zg361_b2_pip_case = scope:zg361_b2_disposition_case
		var:zg361_b2_m017_state = scope:zg361_b2_disposition_state
		var:zg361_b2_m017_state = 1
	}
	option = {
		name = zg361b2.110.a
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_extend_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = { set_variable = { name = zg361_b2_m017_state value = 3 } }
	}
	option = {
		name = zg361b2.110.b
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_demote_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = { set_variable = { name = zg361_b2_m017_state value = 3 } }
	}
	option = {
		name = zg361b2.110.c
		zg361_b2_m074_reject_redundancy_effect = yes
		zg361_eliminate_stepdown_effect = yes
		if = {
			limit = { has_variable = zg361_b2_pending_adverse_action }
			set_variable = { name = zg361_b2_m017_state value = 2 }
		}
		else = { set_variable = { name = zg361_b2_m017_state value = 3 } }
	}
	option = {
		name = zg361b2.110.d
		trigger = {
			var:zg361_b2_m074_state = 1
			var:zg361_b2_m074_redundancy_eligible = 1
			var:zg361_b2_m074_owner = {
				government_has_flag = government_has_treasury
				treasury >= 50
			}
		}
		zg361_b2_m074_accept_redundancy_effect = yes
		set_variable = { name = zg361_b2_m017_state value = 3 }
	}
}

# #070 target-bound one-year anti-retaliation observation.
zg361b2.120 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_retaliation_deadline_owner
				exists = scope:zg361_b2_retaliation_deadline_subject
				this = scope:zg361_b2_retaliation_deadline_subject
				var:zg361_b2_retaliation_owner = scope:zg361_b2_retaliation_deadline_owner
				var:zg361_b2_retaliation_subject = scope:zg361_b2_retaliation_deadline_subject
				var:zg361_b2_retaliation_cycle = scope:zg361_b2_retaliation_deadline_cycle
				var:zg361_b2_retaliation_case = scope:zg361_b2_retaliation_deadline_case
				var:zg361_b2_retaliation_state = scope:zg361_b2_retaliation_deadline_state
				var:zg361_b2_retaliation_state = 1
			}
			set_variable = { name = zg361_b2_retaliation_state value = 4 }
			set_variable = { name = zg361_b2_m070_state value = 4 }
			set_variable = { name = zg361_b2_m070_observed_years value = 1 }
		}
		else = { debug_log = "ZG361B2: stale retaliation D+365 ticket ignored" }
	}
}

# #072 a logged pre-delivery read receives one target-bound D+30 source finding.
zg361b2.121 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_leak_deadline_owner
				exists = scope:zg361_b2_leak_deadline_subject
				this = scope:zg361_b2_leak_deadline_subject
				var:zg361_b2_case_owner = scope:zg361_b2_leak_deadline_owner
				var:zg361_b2_case_subject = scope:zg361_b2_leak_deadline_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_leak_deadline_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_leak_deadline_case
				var:zg361_b2_m072_state = scope:zg361_b2_leak_deadline_state
				var:zg361_b2_m072_state = 2
				var:zg361_b2_m072_receipt_serial = var:zg361_b2_case_serial
			}
			set_variable = { name = zg361_b2_m072_state value = 3 }
			set_variable = { name = zg361_b2_m072_investigation_result value = 1 }
			set_variable = { name = zg361_b2_m072_source_finding value = var:zg361_b2_m072_source }
			var:zg361_b2_case_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
		}
		else = { debug_log = "ZG361B2: stale pre-delivery access D+30 ticket ignored" }
	}
}

# #359 player-manager quota return decision. Counts and barons can be the saved
# subject, but only an eligible celestial manager can ever receive this GUI.
zg361b2.130 = {
	type = character_event
	theme = realm
	title = zg361b2.130.t
	desc = zg361b2.130.desc
	trigger = {
		is_ai = no
		zg361_is_celestial_liege_trigger = yes
		exists = scope:zg361_b2_quota_return_owner
		exists = scope:zg361_b2_quota_return_subject
		this = scope:zg361_b2_quota_return_owner
		scope:zg361_b2_quota_return_subject = {
			var:zg361_b2_case_owner = scope:zg361_b2_quota_return_owner
			var:zg361_b2_case_subject = scope:zg361_b2_quota_return_subject
			var:zg361_b2_case_cycle = scope:zg361_b2_quota_return_cycle
			var:zg361_b2_case_serial = scope:zg361_b2_quota_return_case
			var:zg361_b2_m359_state = scope:zg361_b2_quota_return_state
			var:zg361_b2_m359_state = 1
		}
	}
	option = {
		name = zg361b2.130.a
		trigger = { has_variable = zg361_b2_quota_reserve var:zg361_b2_quota_reserve >= 1 }
		scope:zg361_b2_quota_return_subject = { zg361_b2_m359_consume_reserve_effect = yes }
	}
	option = {
		name = zg361b2.130.b
		scope:zg361_b2_quota_return_subject = { zg361_b2_m359_open_boundary_review_effect = yes }
	}
	option = {
		name = zg361b2.130.c
		scope:zg361_b2_quota_return_subject = { zg361_b2_m359_post_next_cycle_debt_effect = yes }
	}
}

# #359 fresh boundary notice. Refusal freezes a distinct D+7 witness ticket.
zg361b2.131 = {
	type = character_event
	theme = vassal
	title = zg361b2.131.t
	desc = zg361b2.131.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_redelivery_prompt_owner
		exists = scope:zg361_b2_redelivery_prompt_subject
		this = scope:zg361_b2_redelivery_prompt_subject
		var:zg361_b2_redelivery_owner = scope:zg361_b2_redelivery_prompt_owner
		var:zg361_b2_redelivery_subject = scope:zg361_b2_redelivery_prompt_subject
		var:zg361_b2_redelivery_cycle = scope:zg361_b2_redelivery_prompt_cycle
		var:zg361_b2_redelivery_case = scope:zg361_b2_redelivery_prompt_case
		var:zg361_b2_redelivery_state = scope:zg361_b2_redelivery_prompt_state
		var:zg361_b2_redelivery_state = 1
	}
	option = {
		name = zg361b2.131.a
		set_variable = { name = zg361_b2_redelivery_method value = 1 }
		zg361_b2_deliver_boundary_notice_effect = yes
	}
	option = {
		name = zg361b2.131.b
		set_variable = { name = zg361_b2_redelivery_method value = 2 }
		set_variable = { name = zg361_result_objection_recorded value = 1 }
		zg361_b2_deliver_boundary_notice_effect = yes
		zg361_b2_contest_boundary_notice_effect = yes
	}
	option = {
		name = zg361b2.131.c
		set_variable = { name = zg361_b2_redelivery_state value = 2 }
		set_variable = { name = zg361_b2_redelivery_method value = 3 }
		var:zg361_b2_redelivery_owner = {
			if = {
				limit = { exists = liege liege = { is_alive = yes } }
				liege = { save_scope_as = zg361_b2_redelivery_witness }
			}
			else = { save_scope_as = zg361_b2_redelivery_witness }
		}
		set_variable = { name = zg361_b2_redelivery_witness_identity value = scope:zg361_b2_redelivery_witness }
		var:zg361_b2_redelivery_owner = { save_scope_as = zg361_b2_redelivery_witness_owner }
		save_scope_as = zg361_b2_redelivery_witness_subject
		save_scope_value_as = { name = zg361_b2_redelivery_witness_cycle value = var:zg361_b2_redelivery_cycle }
		save_scope_value_as = { name = zg361_b2_redelivery_witness_case value = var:zg361_b2_redelivery_case }
		save_scope_value_as = { name = zg361_b2_redelivery_witness_state value = var:zg361_b2_redelivery_state }
		trigger_event = { id = zg361b2.132 days = 7 }
	}
}

zg361b2.132 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_redelivery_witness_owner
				exists = scope:zg361_b2_redelivery_witness_subject
				exists = scope:zg361_b2_redelivery_witness
				this = scope:zg361_b2_redelivery_witness_subject
				var:zg361_b2_redelivery_owner = scope:zg361_b2_redelivery_witness_owner
				var:zg361_b2_redelivery_subject = scope:zg361_b2_redelivery_witness_subject
				var:zg361_b2_redelivery_cycle = scope:zg361_b2_redelivery_witness_cycle
				var:zg361_b2_redelivery_case = scope:zg361_b2_redelivery_witness_case
				var:zg361_b2_redelivery_state = scope:zg361_b2_redelivery_witness_state
				var:zg361_b2_redelivery_state = 2
				var:zg361_b2_redelivery_witness_identity = scope:zg361_b2_redelivery_witness
			}
			set_variable = { name = zg361_b2_redelivery_witness_receipt value = var:zg361_b2_redelivery_case }
			set_variable = { name = zg361_result_delivery_witness value = scope:zg361_b2_redelivery_witness }
			set_variable = { name = zg361_result_delivery_witness_receipt value = var:zg361_result_case_serial }
			zg361_b2_deliver_boundary_notice_effect = yes
		}
		else = { debug_log = "ZG361B2: stale boundary D+7 witness ticket ignored" }
	}
}

# #079 D+30 independent skip-level result.
zg361b2.140 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_skip_deadline_owner
				exists = scope:zg361_b2_skip_deadline_subject
				this = scope:zg361_b2_skip_deadline_subject
				var:zg361_b2_m079_reviewer = scope:zg361_b2_skip_deadline_owner
				var:zg361_b2_case_subject = scope:zg361_b2_skip_deadline_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_skip_deadline_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_skip_deadline_case
				var:zg361_b2_m079_state = scope:zg361_b2_skip_deadline_state
				var:zg361_b2_m079_state = 1
			}
			zg361_b2_m079_release_seat_effect = yes
			if = {
				limit = { var:zg361_b2_m071_evidence_strength >= 2 }
				set_variable = { name = zg361_b2_m079_state value = 3 }
				set_variable = { name = zg361_result_case_state value = 3 }
				set_variable = { name = zg361_result_appeal_open value = 1 }
				set_variable = { name = zg361_b2_m014_state value = 1 }
				zg361_appeal_regrade_to_35_effect = yes
			}
			else = { set_variable = { name = zg361_b2_m079_state value = 4 } }
		}
		else = { debug_log = "ZG361B2: stale skip-level D+30 ticket ignored" }
	}
}

# #071 one public packet creates exactly one D+30 fact-check result.
zg361b2.141 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_factcheck_owner
				exists = scope:zg361_b2_factcheck_subject
				this = scope:zg361_b2_factcheck_subject
				var:zg361_b2_case_owner = scope:zg361_b2_factcheck_owner
				var:zg361_b2_case_subject = scope:zg361_b2_factcheck_subject
				var:zg361_b2_case_cycle = scope:zg361_b2_factcheck_cycle
				var:zg361_b2_case_serial = scope:zg361_b2_factcheck_case
				var:zg361_b2_m071_factcheck_state = scope:zg361_b2_factcheck_state
				var:zg361_b2_m071_factcheck_state = 1
			}
			if = {
				limit = { var:zg361_b2_m071_evidence_strength >= 2 }
				set_variable = { name = zg361_b2_m071_factcheck_state value = 3 }
				set_variable = { name = zg361_b2_m071_factcheck_outcome value = 1 }
				add_prestige = 25
			}
			else = {
				set_variable = { name = zg361_b2_m071_factcheck_state value = 4 }
				set_variable = { name = zg361_b2_m071_factcheck_outcome value = 2 }
				add_prestige = { value = 0 subtract = 25 }
			}
		}
		else = { debug_log = "ZG361B2: stale public fact-check D+30 ticket ignored" }
	}
}

# #080 D+90 metric defect review writes a repair or an accepted-risk debt.
zg361b2.150 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_metric_deadline_owner
				exists = scope:zg361_b2_metric_deadline_subject
				this = scope:zg361_b2_metric_deadline_subject
				var:zg361_b2_m080_owner = scope:zg361_b2_metric_deadline_owner
				var:zg361_b2_m080_subject = scope:zg361_b2_metric_deadline_subject
				var:zg361_b2_m080_cycle = scope:zg361_b2_metric_deadline_cycle
				var:zg361_b2_m080_case = scope:zg361_b2_metric_deadline_case
				var:zg361_b2_m080_state = scope:zg361_b2_metric_deadline_state
				var:zg361_b2_m080_state = 1
			}
			if = {
				limit = {
					OR = {
						var:zg361_b2_m073_protected = 1
						var:zg361_b2_case_owner = { has_variable = zg361_b2_fairness_anomaly_open }
					}
				}
				set_variable = { name = zg361_b2_m080_state value = 3 }
				set_variable = { name = zg361_b2_m080_metric_repaired value = 1 }
				set_variable = { name = zg361_b2_m080_subject_contribution value = 1 }
			}
			else = {
				set_variable = { name = zg361_b2_m080_state value = 4 }
				set_variable = { name = zg361_b2_m080_accepted_risk value = 1 }
				var:zg361_b2_m080_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			}
		}
		else = { debug_log = "ZG361B2: stale metric D+90 ticket ignored" }
	}
}

# #358 separately served new-fact action; refusal creates a D+7 witnessed
# delivery, while an objection holds execution through the D+90 review.
zg361b2.160 = {
	type = character_event
	theme = vassal
	title = zg361b2.160.t
	desc = zg361b2.160.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_b2_separate_prompt_owner
		exists = scope:zg361_b2_separate_prompt_subject
		this = scope:zg361_b2_separate_prompt_subject
		var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_prompt_owner
		var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_prompt_subject
		var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_prompt_cycle
		var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_prompt_case
		var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_prompt_state
		var:zg361_b2_separate_notice_state = 1
	}
	option = {
		name = zg361b2.160.a
		set_variable = { name = zg361_b2_separate_delivery_method value = 1 }
		zg361_b2_deliver_separate_case_effect = yes
		zg361_b2_execute_pending_adverse_action_effect = yes
	}
	option = {
		name = zg361b2.160.b
		set_variable = { name = zg361_b2_separate_delivery_method value = 2 }
		set_variable = { name = zg361_b2_separate_objection value = 1 }
		zg361_b2_deliver_separate_case_effect = yes
	}
	option = {
		name = zg361b2.160.c
		set_variable = { name = zg361_b2_separate_notice_state value = 2 }
		set_variable = { name = zg361_b2_separate_delivery_method value = 3 }
		var:zg361_b2_separate_notice_owner = {
			if = {
				limit = { exists = liege liege = { is_alive = yes } }
				liege = { save_scope_as = zg361_b2_separate_witness }
			}
			else = { save_scope_as = zg361_b2_separate_witness }
		}
		set_variable = { name = zg361_b2_separate_witness_identity value = scope:zg361_b2_separate_witness }
		var:zg361_b2_separate_notice_owner = { save_scope_as = zg361_b2_separate_witness_owner }
		save_scope_as = zg361_b2_separate_witness_subject
		save_scope_value_as = { name = zg361_b2_separate_witness_cycle value = var:zg361_b2_separate_notice_cycle }
		save_scope_value_as = { name = zg361_b2_separate_witness_case value = var:zg361_b2_separate_notice_case }
		save_scope_value_as = { name = zg361_b2_separate_witness_state value = var:zg361_b2_separate_notice_state }
		trigger_event = { id = zg361b2.161 days = 7 }
	}
}

zg361b2.161 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_separate_witness_owner
				exists = scope:zg361_b2_separate_witness_subject
				exists = scope:zg361_b2_separate_witness
				this = scope:zg361_b2_separate_witness_subject
				var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_witness_owner
				var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_witness_subject
				var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_witness_cycle
				var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_witness_case
				var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_witness_state
				var:zg361_b2_separate_notice_state = 2
				var:zg361_b2_separate_witness_identity = scope:zg361_b2_separate_witness
			}
			set_variable = { name = zg361_b2_separate_witness_receipt value = var:zg361_b2_separate_notice_case }
			zg361_b2_deliver_separate_case_effect = yes
			zg361_b2_execute_pending_adverse_action_effect = yes
		}
		else = { debug_log = "ZG361B2: stale separate-case D+7 witness ticket ignored" }
	}
}

zg361b2.162 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_separate_deadline_owner
				exists = scope:zg361_b2_separate_deadline_subject
				this = scope:zg361_b2_separate_deadline_subject
				var:zg361_b2_separate_notice_owner = scope:zg361_b2_separate_deadline_owner
				var:zg361_b2_separate_notice_subject = scope:zg361_b2_separate_deadline_subject
				var:zg361_b2_separate_notice_cycle = scope:zg361_b2_separate_deadline_cycle
				var:zg361_b2_separate_notice_case = scope:zg361_b2_separate_deadline_case
				var:zg361_b2_separate_notice_state = scope:zg361_b2_separate_deadline_state
				var:zg361_b2_separate_notice_state = 3
			}
			set_variable = { name = zg361_b2_separate_appeal_open value = 0 }
			set_variable = { name = zg361_b2_separate_notice_state value = 4 }
			if = {
				limit = { has_variable = zg361_b2_separate_objection }
				set_variable = { name = zg361_b2_separate_review_outcome value = 2 }
				remove_variable = zg361_b2_pending_adverse_action
			}
			else = { set_variable = { name = zg361_b2_separate_review_outcome value = 1 } }
		}
		else = { debug_log = "ZG361B2: stale separate-case D+90 ticket ignored" }
	}
}

# #074 D+30 conservation audit: exit and HC release are accepted only beside
# the exact public-treasury debit and personal-gold credit.
zg361b2.171 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b2_redundancy_audit_owner
				exists = scope:zg361_b2_redundancy_audit_subject
				this = scope:zg361_b2_redundancy_audit_subject
				var:zg361_b2_m074_owner = scope:zg361_b2_redundancy_audit_owner
				var:zg361_b2_m074_subject = scope:zg361_b2_redundancy_audit_subject
				var:zg361_b2_m074_cycle = scope:zg361_b2_redundancy_audit_cycle
				var:zg361_b2_m074_case = scope:zg361_b2_redundancy_audit_case
				var:zg361_b2_m074_state = scope:zg361_b2_redundancy_audit_state
				var:zg361_b2_m074_state = 3
			}
			if = {
				limit = {
					var:zg361_b2_m074_treasury_paid = 50
					var:zg361_b2_m074_personal_received = 50
					var:zg361_b2_m074_actual_exit = 1
					var:zg361_b2_m074_hc_released = 1
				}
				set_variable = { name = zg361_b2_m074_state value = 4 }
				set_variable = { name = zg361_b2_m074_audit_receipt value = var:zg361_b2_m074_case }
			}
			else = {
				set_variable = { name = zg361_b2_m074_state value = 6 }
				set_variable = { name = zg361_b2_m074_reversal_liability value = 1 }
				var:zg361_b2_m074_owner = { change_variable = { name = zg361_b2_management_debt add = 1 } }
			}
		}
		else = { debug_log = "ZG361B2: stale redundancy D+30 audit ticket ignored" }
	}
}
''')


def render_english_localization() -> bytes:
    return localized(r'''
l_english:
 zg361b2.40.t:0 "A Measured Recovery Plan"
 zg361b2.40.desc:0 "The notice is settled. Its recovery plan now asks for one controllable task and records the support promised beside it. Refusal is evidence for a later review, not another punishment today."
 zg361b2.40.a:0 "Accept the plan and its support."
 zg361b2.40.b:0 "Revise the goal once, then begin."
 zg361b2.40.c:0 "Refuse, and let only the next cycle judge it."
 zg361b2.50.t:0 "After the Appeal"
 zg361b2.50.desc:0 "The ruling stands, yet the pattern behind it may deserve a wider record. You may publish the evidence, file a protected report, or leave a policy debt for another day."
 zg361b2.50.a:0 "Publish the bounded evidence packet."
 zg361b2.50.b:0 "File a protected anonymous report."
 zg361b2.50.c:0 "Defer escalation and record the debt."
 zg361b2.60.t:0 "A Neutral Departure"
 zg361b2.60.desc:0 "A voluntary exit is offered without changing the appeal ruling. If accepted, fifty from the public treasury becomes exactly fifty personal gold; an unfunded promise cannot be signed."
 zg361b2.60.a:0 "Accept the funded neutral exit."
 zg361b2.60.b:0 "Remain under the ordinary process."
 zg361b2.110.t:0 "PIP Disposition"
 zg361b2.110.desc:0 "The bounded recovery period has closed without graduation. Choose one recorded disposition; any live appeal safeguard still applies."
 zg361b2.110.a:0 "Extend support for one final cycle."
 zg361b2.110.b:0 "Demote, but retain the official."
 zg361b2.110.c:0 "Offer an orderly retirement."
 zg361b2.110.d:0 "Accept a funded, neutral redundancy exit."
 zg361b2.130.t:0 "Return the Corrected Quota"
 zg361b2.130.desc:0 "A corrected appeal releases one bottom-slot obligation. Consume a reserve, reopen the boundary with fresh notice and appeal, or post the obligation to the next real review."
 zg361b2.130.a:0 "Consume one frozen reserve slot."
 zg361b2.130.b:0 "Reopen and re-serve the boundary case."
 zg361b2.130.c:0 "Post one slot to the next cycle."
 zg361b2.131.t:0 "Fresh Boundary Notice"
 zg361b2.131.desc:0 "A corrected case has moved the quota boundary. This is a new notice with its own receipt and ninety-day challenge window; it does not borrow the old appeal."
 zg361b2.131.a:0 "Acknowledge the new notice."
 zg361b2.131.b:0 "Acknowledge and contest it."
 zg361b2.131.c:0 "Refuse signature; require witnessed delivery."
 zg361b2.160.t:0 "Separate Misconduct Notice"
 zg361b2.160.desc:0 "A later fact cannot be folded into the appealed result. It arrives as a separate notice, with a separate receipt and its own challenge window."
 zg361b2.160.a:0 "Acknowledge the separate notice."
 zg361b2.160.b:0 "Acknowledge and object."
 zg361b2.160.c:0 "Refuse signature; require a witness."
 zg361b2.statement.prepared:0 "B2 case: prepared; detailed evidence remains locked before delivery."
 zg361b2.statement.delivered:0 "B2 case: delivered with a bounded receipt and appeal deadline."
 zg361b2.statement.appeal:0 "B2 appeal: target-bound review is active."
 zg361b2.statement.corrected:0 "B2 appeal: corrected; actual posted receipts were reversed once."
 zg361b2.statement.pip:0 "B2 recovery plan: active with a bounded support commitment."
 zg361b2.statement.retaliation:0 "B2 safeguard: one-year target-bound adverse-action observation is active."
''')


def render_simp_chinese_localization() -> bytes:
    return localized(r'''
l_simp_chinese:
 zg361b2.40.t:0 "有界改进计划"
 zg361b2.40.desc:0 "结果已经送达。改进计划只要求一项本人可控制的任务，并把上级承诺的支持一并记入案卷。拒绝只会成为下一轮证据，不会在今天再罚一次。"
 zg361b2.40.a:0 "接受计划及配套支持。"
 zg361b2.40.b:0 "修改一次目标，然后开始执行。"
 zg361b2.40.c:0 "拒绝，并只让下一轮评价此事。"
 zg361b2.50.t:0 "申诉之后"
 zg361b2.50.desc:0 "裁决已经作出，但背后的模式也许值得留下更广的记录。你可以公开有界证据、提交受保护报告，或把政策债留待以后处理。"
 zg361b2.50.a:0 "公开这份有界证据包。"
 zg361b2.50.b:0 "匿名提交受保护报告。"
 zg361b2.50.c:0 "暂不升级，但记下一笔政策债。"
 zg361b2.60.t:0 "中性离任"
 zg361b2.60.desc:0 "你可以在不改变申诉裁决的前提下自愿离任。若接受，地方国库的五十会精确转成个人五十金币；没有资金的承诺不能签字。"
 zg361b2.60.a:0 "接受已有资金保障的中性离任。"
 zg361b2.60.b:0 "留下，继续走普通程序。"
 zg361b2.110.t:0 "改进期处置"
 zg361b2.110.desc:0 "有界改进期结束，但尚未达成毕业条件。请选择一项留痕处置；仍在生效的申诉保护不会因此消失。"
 zg361b2.110.a:0 "再延长一个周期的支持。"
 zg361b2.110.b:0 "降岗留用。"
 zg361b2.110.c:0 "安排有序致仕。"
 zg361b2.110.d:0 "接受已有资金保障的中性裁撤离任。"
 zg361b2.130.t:0 "回流改判后的配额"
 zg361b2.130.desc:0 "一次申诉改判释放了一个末档义务。你可以消耗预留名额、重新划定边界并重新送达，或把义务记到下一次真实考核。"
 zg361b2.130.a:0 "消耗一个已冻结的预留名额。"
 zg361b2.130.b:0 "重开边界案并重新送达。"
 zg361b2.130.c:0 "把一个名额记入下一周期。"
 zg361b2.131.t:0 "新的边界通知"
 zg361b2.131.desc:0 "申诉改判移动了配额边界。这是一份有独立收据和九十日异议窗口的新通知，不会借用旧申诉。"
 zg361b2.131.a:0 "签收新的通知。"
 zg361b2.131.b:0 "签收但提出异议。"
 zg361b2.131.c:0 "拒绝签字，要求见证送达。"
 zg361b2.160.t:0 "独立失当通知"
 zg361b2.160.desc:0 "后续新事实不能塞回正在申诉的结果。它必须作为独立通知送达，并拥有独立收据与异议窗口。"
 zg361b2.160.a:0 "签收独立通知。"
 zg361b2.160.b:0 "签收但提出异议。"
 zg361b2.160.c:0 "拒绝签字，要求见证。"
 zg361b2.statement.prepared:0 "B2 案卷：已准备；正式送达前，详细证据仍受访问控制。"
 zg361b2.statement.delivered:0 "B2 案卷：已送达，并冻结有界收据与申诉期限。"
 zg361b2.statement.appeal:0 "B2 申诉：绑定对象的复核正在进行。"
 zg361b2.statement.corrected:0 "B2 申诉：已改判；实际入账的扣款只反冲一次。"
 zg361b2.statement.pip:0 "B2 改进计划：执行中，并已记录有界支持承诺。"
 zg361b2.statement.retaliation:0 "B2 保护：为期一年的绑定对象不利行动观察正在生效。"
''')


def render_english_placeholder_localization(language: str) -> bytes:
    english = render_english_localization().decode("utf-8-sig")
    return localized(english.replace("l_english:", f"l_{language}:", 1))


def outputs() -> dict[Path, bytes]:
    validate_wired_scope()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_b2_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_b2_runtime_events.txt": render_events(),
        MOD_ROOT / "localization" / "english" / "zg361_b2_l_english.yml": render_english_localization(),
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_b2_l_simp_chinese.yml": render_simp_chinese_localization(),
    }
    for language in (
        "french",
        "german",
        "japanese",
        "korean",
        "polish",
        "russian",
        "spanish",
    ):
        rendered[
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_b2_l_{language}.yml"
        ] = render_english_placeholder_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    if args.check:
        if stale:
            print("RED: stale B2 generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: B2 generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} B2 runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
