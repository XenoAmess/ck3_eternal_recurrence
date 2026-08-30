#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the B1 cross-cycle performance-season kernel.

The generated CK3 files are intentionally isolated from the legacy settlement
effect.  Existing rewards, penalties and scoreboard publication remain the
single settlement implementation; this kernel supplies persistent rosters,
timed stages, peer records, shadow ratings and a common-superior quota barrier.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from zg361_b1_runtime_data import B1_BINDINGS, validate_b1_bindings


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_b1_runtime.py\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + text.strip() + "\n").encode("utf-8")


def render_effects() -> bytes:
    bindings = "\n".join(
        f"# {row.mechanism_id:03d} {row.stage} {row.scope}: "
        f"{row.meaningful_write} -> {row.consumer}"
        for row in B1_BINDINGS
    )
    body = r'''
# ZhongGuo 361 B1 — persistent performance season and pooled quota kernel
# State: 1 targets, 2 midcycle, 3 peer/evidence, 4 facts, 5 shadow,
#        6 quota ready, 7 calibration, 8 published.

zg361_b1_initialize_subject_case_effect = {
	set_variable = { name = zg361_b1_case_owner value = root }
	set_variable = { name = zg361_b1_cycle_serial value = root.var:zg361_b1_cycle_serial }
	set_variable = { name = zg361_b1_case_serial value = root.var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_case_state value = 1 }
	set_variable = { name = zg361_b1_case_open_year value = current_year }
	set_variable = { name = zg361_b1_roster_included value = 1 }
	set_variable = { name = zg361_b1_roster_amendment value = 0 }
	set_variable = { name = zg361_b1_leaver_route value = 0 }
	set_variable = { name = zg361_b1_goal_version value = 1 }
	set_variable = { name = zg361_b1_goal_direction value = 1 }
	set_variable = { name = zg361_b1_goal_strength value = 100 }
	set_variable = { name = zg361_b1_goal_weight value = 20 }
	set_variable = { name = zg361_b1_goal_grade_cap value = 3 }
	set_variable = { name = zg361_b1_role_scorecard_version value = 1 }
	set_variable = { name = zg361_b1_role_code value = 1 }
	if = {
		limit = { NOT = { is_governor = yes } }
		set_variable = { name = zg361_b1_role_code value = 2 }
		set_variable = { name = zg361_b1_goal_weight value = 10 }
	}
	set_variable = { name = zg361_b1_baseline_raw value = 0 }
	if = {
		limit = { government_has_flag = government_has_merit }
		set_variable = { name = zg361_b1_baseline_raw value = merit_level }
	}
	set_variable = { name = zg361_b1_baseline_adjusted value = var:zg361_b1_baseline_raw }
	set_variable = { name = zg361_b1_difficulty_adjustment value = 0 }
	if = {
		limit = { root = { is_at_war = yes } }
		set_variable = { name = zg361_b1_difficulty_adjustment value = 5 }
	}
	set_variable = { name = zg361_b1_target_rebased value = 0 }
	set_variable = { name = zg361_b1_support_obligation value = 0 }
	set_variable = { name = zg361_b1_midcycle_warning value = 0 }
	set_variable = { name = zg361_b1_feedback_ack value = 0 }
	set_variable = { name = zg361_b1_feedback_objection value = 0 }
	set_variable = { name = zg361_b1_opportunity_grant value = 0 }
	set_variable = { name = zg361_b1_self_submitted value = 0 }
	set_variable = { name = zg361_b1_self_score value = 0 }
	set_variable = { name = zg361_b1_peer_slot_1_filled value = 0 }
	set_variable = { name = zg361_b1_peer_slot_2_filled value = 0 }
	set_variable = { name = zg361_b1_peer_slot_3_filled value = 0 }
	set_variable = { name = zg361_b1_peer_used value = 0 }
	set_variable = { name = zg361_b1_peer_cap value = 3 }
	set_variable = { name = zg361_b1_peer_fatigue value = 0 }
	set_variable = { name = zg361_b1_peer_n value = 0 }
	set_variable = { name = zg361_b1_peer_raw_sum value = 0 }
	set_variable = { name = zg361_b1_peer_normalized_score value = 0 }
	set_variable = { name = zg361_b1_peer_shape value = 0 }
	set_variable = { name = zg361_b1_peer_sealed value = 0 }
	set_variable = { name = zg361_b1_peer_timely_n value = 0 }
	set_variable = { name = zg361_b1_evidence_early value = zg361_kpi_value }
	set_variable = { name = zg361_b1_evidence_mid value = 0 }
	set_variable = { name = zg361_b1_evidence_late value = 0 }
	set_variable = { name = zg361_b1_evidence_late_frozen value = 0 }
	set_variable = { name = zg361_b1_fact_sheet_serial value = 0 }
	set_variable = { name = zg361_b1_fact_closed_year value = 0 }
	set_variable = { name = zg361_b1_shadow_grade value = 0 }
	set_variable = { name = zg361_b1_shadow_evidence_delta value = 0 }
	set_variable = { name = zg361_b1_quota_snapshot value = 0 }
	set_variable = { name = zg361_b1_forced_down value = 0 }
	set_variable = { name = zg361_b1_final_grade value = 0 }
	set_variable = { name = zg361_b1_final_reason value = 0 }
	set_variable = { name = zg361_b1_feedback_debt value = 0 }
	set_variable = { name = zg361_b1_band_order value = 0 }
	set_variable = { name = zg361_b1_reopen_serial value = 0 }
	set_variable = { name = zg361_b1_pending_milestone value = 0 }
	set_variable = { name = zg361_b1_newcomer_route value = 0 }
	set_variable = { name = zg361_b1_peer_use_mode value = root.var:zg361_b1_peer_use_mode }
	remove_variable = zg361_pending_grade
	remove_variable = zg361_rank

	# Configured policy cards select real B1 routes. Unconfigured managers use
	# the evidence-led reference route already initialized above.
	if = {
		limit = { root = { has_variable = zg361_mechanism_002_choice } }
		if = {
			limit = { root.var:zg361_mechanism_002_choice = 2 }
			set_variable = { name = zg361_b1_goal_strength value = 120 }
			change_variable = { name = zg361_b1_goal_weight add = 10 }
		}
		else_if = {
			limit = { root.var:zg361_mechanism_002_choice = 3 }
			set_variable = { name = zg361_b1_goal_strength value = 80 }
			set_variable = { name = zg361_b1_goal_weight value = 5 }
			set_variable = { name = zg361_b1_goal_grade_cap value = 2 }
		}
	}
	if = {
		limit = { root = { has_variable = zg361_mechanism_006_choice } }
		if = {
			limit = { root.var:zg361_mechanism_006_choice != 1 }
			set_variable = { name = zg361_b1_difficulty_adjustment value = 0 }
		}
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_prev_merit_level }
			root = { has_character_flag = zg361_review_baseline_initialized }
		}
		add_character_flag = zg361_newcomer_this_cycle
		set_variable = { name = zg361_b1_newcomer_route value = 1 }
	}
	else = { remove_character_flag = zg361_newcomer_this_cycle }
	# Route choice must run after newcomer detection; applying it against the
	# initialization value 0 would make every configured route a silent no-op.
	if = {
		limit = {
			var:zg361_b1_newcomer_route = 1
			root = { has_variable = zg361_mechanism_041_choice }
		}
		if = {
			limit = { root.var:zg361_mechanism_041_choice = 2 }
			set_variable = { name = zg361_b1_newcomer_route value = 3 }
			remove_character_flag = zg361_newcomer_this_cycle
		}
		else_if = {
			limit = { root.var:zg361_mechanism_041_choice = 3 }
			set_variable = { name = zg361_b1_newcomer_route value = 2 }
		}
	}

	set_variable = { name = zg361_b1_m002_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m005_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m006_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m041_receipt_serial value = var:zg361_b1_case_serial }
}

zg361_b1_open_cycle_effect = {
	if = {
		limit = {
			has_game_rule = zg361_on
			zg361_is_celestial_liege_trigger = yes
			NOT = { has_character_flag = zg361_b1_cycle_active }
			NOT = { has_character_flag = zg361_review_in_progress }
			trigger_if = {
				limit = { has_variable = zg361_b1_cycle_open_year }
				NOT = { var:zg361_b1_cycle_open_year = current_year }
			}
			trigger_else = { always = yes }
		}
		add_character_flag = zg361_b1_cycle_active
		if = {
			limit = { NOT = { has_variable = zg361_b1_cycle_serial } }
			set_variable = { name = zg361_b1_cycle_serial value = 0 }
		}
		if = {
			limit = { NOT = { has_variable = zg361_b1_case_serial } }
			set_variable = { name = zg361_b1_case_serial value = 0 }
		}
		change_variable = { name = zg361_b1_cycle_serial add = 1 }
		change_variable = { name = zg361_b1_case_serial add = 1 }
		set_variable = { name = zg361_b1_cycle_state value = 1 }
		set_variable = { name = zg361_b1_cycle_open_year value = current_year }
		set_variable = { name = zg361_b1_bank_posted_serial value = 0 }
		set_variable = { name = zg361_b1_peer_used value = 0 }
		set_variable = { name = zg361_b1_peer_cap value = 3 }
		set_variable = { name = zg361_b1_peer_fatigue value = 0 }
		set_variable = { name = zg361_b1_peer_use_mode value = 1 }
		set_variable = { name = zg361_b1_allow_rebase value = 1 }
		if = {
			limit = { has_variable = zg361_mechanism_003_choice }
			if = {
				limit = { var:zg361_mechanism_003_choice != 1 }
				set_variable = { name = zg361_b1_allow_rebase value = 0 }
			}
		}
		if = {
			limit = { has_variable = zg361_mechanism_053_choice }
			if = {
				limit = { var:zg361_mechanism_053_choice = 2 }
				set_variable = { name = zg361_b1_peer_use_mode value = 2 }
			}
			else_if = {
				limit = { var:zg361_mechanism_053_choice = 3 }
				set_variable = { name = zg361_b1_peer_use_mode value = 0 }
			}
		}
		set_variable = { name = zg361_b1_m053_receipt_serial value = var:zg361_b1_case_serial }

		if = {
			limit = { has_variable_list = zg361_b1_subjects }
			clear_variable_list = zg361_b1_subjects
		}
		every_vassal = {
			limit = { zg361_is_reviewable_vassal_trigger = yes }
			add_to_list = zg361_b1_subject_candidates
		}
		set_variable = {
			name = zg361_b1_subject_n
			value = { value = list_size:zg361_b1_subject_candidates max = 80 }
		}
		ordered_in_list = {
			list = zg361_b1_subject_candidates
			order_by = primary_title.tier
			max = { value = list_size:zg361_b1_subject_candidates max = 80 }
			zg361_b1_initialize_subject_case_effect = yes
			save_temporary_scope_as = zg361_b1_subject_to_store
			root = {
				add_to_variable_list = {
					name = zg361_b1_subjects
					target = scope:zg361_b1_subject_to_store
				}
			}
		}

		if = {
			limit = { var:zg361_b1_subject_n >= 1 }
			zg361_b1_register_common_superior_bank_effect = yes
			save_scope_as = zg361_b1_ticket_owner
			save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
			save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
			save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
			trigger_event = { id = zg361b1.100 days = 180 }
			debug_log = "ZG361B1: performance season opened"
		}
		else = {
			set_variable = { name = zg361_b1_cycle_state value = 8 }
			remove_character_flag = zg361_b1_cycle_active
			debug_log = "ZG361B1: empty roster closed without settlement"
		}
	}
	else = { debug_log = "ZG361B1: cycle open ignored while another case is active" }
}

zg361_b1_midcycle_dispatcher_effect = {
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = {
				has_variable = zg361_b1_case_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_case_state
			}
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
					var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
					var:zg361_b1_case_state = 1
				}
				# Snapshot the formula without consuming one-shot evidence. The final
				# D+300 compute remains the sole consumer of a skipped-Jingcha penalty.
				set_variable = { name = zg361_b1_evidence_mid value = zg361_kpi_value }
				set_variable = { name = zg361_b1_self_score value = var:zg361_b1_evidence_mid }
				if = {
					limit = { var:zg361_b1_evidence_mid <= 0 }
					set_variable = { name = zg361_b1_midcycle_warning value = 1 }
				}
				if = {
					limit = {
						root = { is_at_war = yes var:zg361_b1_allow_rebase = 1 }
						var:zg361_b1_target_rebased = 0
					}
					set_variable = { name = zg361_b1_target_rebased value = 1 }
					change_variable = { name = zg361_b1_goal_version add = 1 }
					set_variable = { name = zg361_b1_support_obligation value = 1 }
				}
				set_variable = { name = zg361_b1_opportunity_grant value = 1 }
				set_variable = { name = zg361_b1_case_state value = 2 }
				set_variable = { name = zg361_b1_m003_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m046_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	set_variable = { name = zg361_b1_cycle_state value = 2 }
}

zg361_b1_peer_window_dispatcher_effect = {
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = { has_variable = zg361_b1_case_owner }
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_state = 2
				}
				set_variable = { name = zg361_b1_case_state value = 3 }
				set_variable = { name = zg361_b1_self_submitted value = 1 }
				set_variable = { name = zg361_b1_m004_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m007_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m048_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	set_variable = { name = zg361_b1_cycle_state value = 3 }
}

zg361_b1_prepare_facts_effect = {
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = { has_variable = zg361_b1_case_owner }
			if = {
				limit = {
					var:zg361_b1_case_owner = root
					var:zg361_b1_case_state = 3
				}
				set_variable = { name = zg361_b1_peer_normalized_score value = 0 }
				if = {
					limit = { var:zg361_b1_peer_n >= 1 }
					set_variable = {
						name = zg361_b1_peer_normalized_score
						value = { value = var:zg361_b1_peer_raw_sum divide = var:zg361_b1_peer_n max = 10 min = -15 }
					}
				}
				set_variable = { name = zg361_b1_peer_sealed value = 1 }
				set_variable = { name = zg361_b1_evidence_late value = zg361_kpi_value }
				set_variable = { name = zg361_b1_evidence_late_frozen value = 1 }
				set_variable = { name = zg361_b1_m008_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m049_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m050_receipt_serial value = var:zg361_b1_case_serial }
				set_variable = { name = zg361_b1_m052_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
}

zg361_b1_open_shadow_effect = {
	if = {
		limit = { var:zg361_b1_cycle_state = 3 }
		set_variable = { name = zg361_b1_cycle_state value = 4 }
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = { has_variable = zg361_b1_case_owner }
				if = {
					limit = {
						var:zg361_b1_case_owner = root
						var:zg361_b1_case_state = 3
						has_variable = zg361_pending_grade
					}
					set_variable = { name = zg361_b1_case_state value = 4 }
					set_variable = { name = zg361_b1_fact_sheet_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_fact_closed_year value = current_year }
					set_variable = { name = zg361_b1_quota_snapshot value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_shadow_grade value = var:zg361_pending_grade }
					set_variable = { name = zg361_b1_forced_down value = 0 }
					if = {
						limit = { var:zg361_pending_grade < var:zg361_absolute_grade }
						set_variable = { name = zg361_b1_forced_down value = 1 }
					}
					set_variable = { name = zg361_b1_case_state value = 5 }
					set_variable = { name = zg361_b1_m001_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m039_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m040_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m042_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m044_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m047_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m135_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m140_receipt_serial value = var:zg361_b1_case_serial }
					set_variable = { name = zg361_b1_m357_receipt_serial value = var:zg361_b1_case_serial }
				}
			}
		}
		set_variable = { name = zg361_b1_cycle_state value = 5 }
		save_scope_as = zg361_b1_ticket_owner
		save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.103 days = 30 }
		debug_log = "ZG361B1: facts frozen and shadow response opened"
	}
}

zg361_b1_register_common_superior_bank_effect = {
	if = {
		limit = { exists = liege }
		save_temporary_scope_as = zg361_b1_registering_manager
		liege = {
			if = {
				limit = { zg361_is_celestial_liege_trigger = yes }
				save_temporary_scope_as = zg361_b1_bank_owner
				if = {
					limit = {
						trigger_if = {
							limit = { has_variable = zg361_b1_bank_season }
							NOT = { var:zg361_b1_bank_season = current_year }
						}
						trigger_else = { always = yes }
					}
					if = {
						limit = { has_variable_list = zg361_b1_expected_managers }
						clear_variable_list = zg361_b1_expected_managers
					}
					if = {
						limit = { has_variable_list = zg361_b1_ready_managers }
						clear_variable_list = zg361_b1_ready_managers
					}
					set_variable = { name = zg361_b1_bank_season value = current_year }
					if = {
						limit = { NOT = { has_variable = zg361_b1_bank_case_serial } }
						set_variable = { name = zg361_b1_bank_case_serial value = 0 }
					}
					change_variable = { name = zg361_b1_bank_case_serial add = 1 }
					set_variable = { name = zg361_b1_bank_state value = 1 }
					set_variable = { name = zg361_b1_expected_manager_n value = 0 }
					set_variable = { name = zg361_b1_ready_manager_n value = 0 }
					set_variable = { name = zg361_b1_pool_n value = 0 }
					every_vassal = {
						limit = {
							zg361_is_celestial_liege_trigger = yes
							any_vassal = {
								count >= 1
								zg361_is_reviewable_vassal_trigger = yes
							}
						}
						save_temporary_scope_as = zg361_b1_expected_manager
						scope:zg361_b1_bank_owner = {
							add_to_variable_list = {
								name = zg361_b1_expected_managers
								target = scope:zg361_b1_expected_manager
							}
							change_variable = { name = zg361_b1_expected_manager_n add = 1 }
						}
						# Reset ROOT through a one-day character event before calling
						# the manager-owned cycle effect. Direct nested calls would retain
						# the first manager as ROOT and corrupt sibling case ownership.
						trigger_event = { id = zg361b1.90 days = 1 }
					}
					save_scope_as = zg361_b1_bank_ticket_owner
					save_scope_value_as = { name = zg361_b1_bank_ticket_season value = var:zg361_b1_bank_season }
					save_scope_value_as = { name = zg361_b1_bank_ticket_case value = var:zg361_b1_bank_case_serial }
					save_scope_value_as = { name = zg361_b1_bank_ticket_state value = var:zg361_b1_bank_state }
					trigger_event = { id = zg361b1.110 days = 335 }
				}
				scope:zg361_b1_registering_manager = {
					set_variable = { name = zg361_b1_bank_superior value = scope:zg361_b1_bank_owner }
					set_variable = { name = zg361_b1_bank_season value = scope:zg361_b1_bank_owner.var:zg361_b1_bank_season }
				}
			}
		}
	}
}

zg361_b1_submit_quota_book_effect = {
	if = {
		limit = { has_variable = zg361_b1_bank_superior }
		save_temporary_scope_as = zg361_b1_ready_manager
		var:zg361_b1_bank_superior = {
			if = {
				limit = {
					is_alive = yes
					has_variable = zg361_b1_bank_state
					var:zg361_b1_bank_state = 1
					has_variable = zg361_b1_bank_season
					var:zg361_b1_bank_season = scope:zg361_b1_ready_manager.var:zg361_b1_bank_season
				}
				if = {
					limit = {
						trigger_if = {
							limit = { has_variable_list = zg361_b1_ready_managers }
							NOT = {
								is_target_in_variable_list = {
									name = zg361_b1_ready_managers
									target = scope:zg361_b1_ready_manager
								}
							}
						}
						trigger_else = { always = yes }
					}
					add_to_variable_list = {
						name = zg361_b1_ready_managers
						target = scope:zg361_b1_ready_manager
					}
					change_variable = { name = zg361_b1_ready_manager_n add = 1 }
					change_variable = { name = zg361_b1_pool_n add = scope:zg361_b1_ready_manager.var:zg361_cohort_n }
					scope:zg361_b1_ready_manager = {
						set_variable = { name = zg361_b1_bank_posted_serial value = var:zg361_b1_case_serial }
					}
				}
				if = {
					limit = { var:zg361_b1_ready_manager_n >= var:zg361_b1_expected_manager_n }
					save_scope_as = zg361_b1_bank_ticket_owner
					save_scope_value_as = { name = zg361_b1_bank_ticket_season value = var:zg361_b1_bank_season }
					save_scope_value_as = { name = zg361_b1_bank_ticket_case value = var:zg361_b1_bank_case_serial }
					save_scope_value_as = { name = zg361_b1_bank_ticket_state value = var:zg361_b1_bank_state }
					trigger_event = { id = zg361b1.110 days = 1 }
				}
			}
			else = { scope:zg361_b1_ready_manager = { zg361_b1_apply_local_quota_effect = yes } }
		}
	}
	else = { zg361_b1_apply_local_quota_effect = yes }
}

zg361_b1_close_common_superior_bank_effect = {
	set_variable = { name = zg361_b1_bank_state value = 2 }
	set_variable = { name = zg361_b1_pool_cursor value = 0 }
	set_variable = { name = zg361_b1_pool_n value = 0 }
	every_in_list = {
		variable = zg361_b1_ready_managers
		save_temporary_scope_as = zg361_b1_pool_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					var:zg361_b1_case_owner = scope:zg361_b1_pool_manager
					var:zg361_b1_case_state = 5
					has_variable = zg361_pending_grade
				}
				add_to_list = zg361_b1_pool_candidates
				root = { change_variable = { name = zg361_b1_pool_n add = 1 } }
			}
		}
	}
	set_variable = {
		name = zg361_b1_pool_top_slots
		value = { value = var:zg361_b1_pool_n multiply = 0.3 round = yes min = 1 }
	}
	set_variable = { name = zg361_b1_pool_bottom_slots value = 0 }
	if = {
		limit = { var:zg361_b1_pool_n >= 5 }
		set_variable = {
			name = zg361_b1_pool_bottom_slots
			value = { value = var:zg361_b1_pool_n multiply = 0.1 floor = yes min = 1 }
		}
	}
	ordered_in_list = {
		list = zg361_b1_pool_candidates
		order_by = var:zg361_kpi
		max = { value = list_size:zg361_b1_pool_candidates max = 80 }
		root = { change_variable = { name = zg361_b1_pool_cursor add = 1 } }
		set_variable = { name = zg361_rank value = root.var:zg361_b1_pool_cursor }
		set_variable = { name = zg361_b1_pool_rank value = root.var:zg361_b1_pool_cursor }
		set_variable = { name = zg361_pending_grade value = 2 }
		if = {
			limit = { var:zg361_b1_pool_rank <= root.var:zg361_b1_pool_top_slots }
			set_variable = { name = zg361_pending_grade value = 3 }
		}
		set_variable = { name = zg361_last_reviewer value = var:zg361_b1_case_owner }
		set_variable = { name = zg361_last_review_serial value = var:zg361_b1_cycle_serial }
	}
	every_in_list = {
		list = zg361_b1_pool_candidates
		limit = { NOT = { has_character_flag = zg361_newcomer_this_cycle } }
		add_to_list = zg361_b1_pool_bottom_candidates
	}
	set_variable = { name = zg361_b1_pool_bottom_cursor value = 0 }
	ordered_in_list = {
		list = zg361_b1_pool_bottom_candidates
		order_by = var:zg361_b1_pool_rank
		max = { value = list_size:zg361_b1_pool_bottom_candidates max = 80 }
		if = {
			limit = { root.var:zg361_b1_pool_bottom_cursor < root.var:zg361_b1_pool_bottom_slots }
			set_variable = { name = zg361_pending_grade value = 1 }
		}
		root = { change_variable = { name = zg361_b1_pool_bottom_cursor add = 1 } }
	}
	every_in_list = {
		variable = zg361_b1_ready_managers
		set_variable = { name = zg361_pending_375_n value = 0 }
		set_variable = { name = zg361_pending_35_n value = 0 }
		set_variable = { name = zg361_pending_325_n value = 0 }
		set_variable = { name = zg361_top_cut value = root.var:zg361_b1_pool_top_slots }
		set_variable = { name = zg361_top_cut_next value = { value = root.var:zg361_b1_pool_top_slots add = 1 } }
		set_variable = { name = zg361_bottom_slots value = root.var:zg361_b1_pool_bottom_slots }
		save_temporary_scope_as = zg361_b1_allocated_manager
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = {
					has_variable = zg361_b1_case_owner
					var:zg361_b1_case_owner = scope:zg361_b1_allocated_manager
					var:zg361_b1_case_state = 5
					has_variable = zg361_pending_grade
				}
				if = {
					limit = { var:zg361_pending_grade = 3 }
					scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_375_n add = 1 } }
				}
				else_if = {
					limit = { var:zg361_pending_grade = 1 }
					scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_325_n add = 1 } }
				}
				else = { scope:zg361_b1_allocated_manager = { change_variable = { name = zg361_pending_35_n add = 1 } } }
			}
		}
		set_variable = { name = zg361_b1_cycle_state value = 6 }
		set_variable = { name = zg361_b1_m037_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m038_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m138_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m139_receipt_serial value = var:zg361_b1_case_serial }
		# This loop is owned by the common superior, so ROOT is still the
		# superior. Cross one committed event boundary to reset ROOT to this
		# manager before touching manager-owned subject lists or settlement.
		save_scope_as = zg361_b1_ticket_owner
		save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
		save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
		save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
		trigger_event = { id = zg361b1.111 days = 1 }
	}
	set_variable = { name = zg361_b1_m011_receipt_serial value = var:zg361_b1_bank_case_serial }
	set_variable = { name = zg361_b1_m136_receipt_serial value = var:zg361_b1_bank_case_serial }
	set_variable = { name = zg361_b1_m141_receipt_serial value = var:zg361_b1_bank_case_serial }
	debug_log = "ZG361B1: common-superior quota bank closed once"
}

zg361_b1_apply_local_quota_effect = {
	set_variable = { name = zg361_b1_cycle_state value = 6 }
	set_variable = { name = zg361_b1_m038_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m138_receipt_serial value = var:zg361_b1_case_serial }
	zg361_b1_open_calibration_effect = yes
}

zg361_b1_open_calibration_effect = {
	set_variable = { name = zg361_b1_cycle_state value = 7 }
	set_variable = { name = zg361_b1_calibration_attention value = 3 }
	set_variable = { name = zg361_b1_agenda_version value = 1 }
	set_variable = { name = zg361_b1_skip_level_return_used value = 0 }
	set_variable = { name = zg361_b1_dissent_used value = 0 }
	set_variable = { name = zg361_b1_pending_slot_used value = 0 }
	set_variable = { name = zg361_b1_reopen_used value = 0 }
	set_variable = { name = zg361_b1_m009_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m010_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m012_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m043_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m137_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m142_receipt_serial value = var:zg361_b1_case_serial }
	set_variable = { name = zg361_b1_m144_receipt_serial value = var:zg361_b1_case_serial }
	every_in_list = {
		variable = zg361_b1_subjects
		if = {
			limit = { has_variable = zg361_b1_case_owner }
			if = {
				limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 5 }
				set_variable = { name = zg361_b1_case_state value = 7 }
				set_variable = { name = zg361_b1_band_order value = var:zg361_rank }
				set_variable = { name = zg361_b1_m145_receipt_serial value = var:zg361_b1_case_serial }
			}
		}
	}
	if = {
		limit = { is_ai = yes }
		zg361_apply_pending_grades_effect = yes
	}
	else = { trigger_event = { id = zg361.10 days = 1 } }
}

zg361_b1_mark_published_effect = {
	if = {
		limit = { has_character_flag = zg361_b1_cycle_active }
		set_variable = { name = zg361_b1_cycle_state value = 8 }
		set_variable = { name = zg361_b1_m013_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m045_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m051_receipt_serial value = var:zg361_b1_case_serial }
		set_variable = { name = zg361_b1_m143_receipt_serial value = var:zg361_b1_case_serial }
		every_in_list = {
			variable = zg361_b1_subjects
			if = {
				limit = { has_variable = zg361_b1_case_owner }
				if = {
					limit = { var:zg361_b1_case_owner = root var:zg361_b1_case_state = 7 }
					set_variable = { name = zg361_b1_case_state value = 8 }
					if = {
						limit = { has_variable = zg361_last_grade }
						set_variable = { name = zg361_b1_final_grade value = var:zg361_last_grade }
					}
					if = {
						limit = { has_variable = zg361_result_grade_reason }
						set_variable = { name = zg361_b1_final_reason value = var:zg361_result_grade_reason }
					}
					if = {
						limit = { var:zg361_b1_final_grade = 1 var:zg361_b1_midcycle_warning = 0 }
						set_variable = { name = zg361_b1_feedback_debt value = 1 }
					}
				}
			}
		}
		remove_character_flag = zg361_b1_cycle_active
		debug_log = "ZG361B1: performance season published"
	}
}

zg361_b1_submit_peer_recommendation_effect = {
	zg361_b1_submit_peer_positive_effect = yes
}

zg361_b1_submit_peer_positive_effect = {
	if = {
		limit = { var:zg361_b1_peer_used < var:zg361_b1_peer_cap }
		if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_1_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_1_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_1_raw value = 10 }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_2_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_2_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_2_raw value = 10 }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_3_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_3_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_3_raw value = 10 }
			}
		}
		change_variable = { name = zg361_b1_peer_used add = 1 }
		scope:recipient = {
			change_variable = { name = zg361_b1_peer_n add = 1 }
			change_variable = { name = zg361_b1_peer_raw_sum add = 10 }
			change_variable = { name = zg361_b1_peer_timely_n add = 1 }
		}
		debug_log = "ZG361B1: sealed positive peer record submitted"
	}
}

zg361_b1_submit_peer_negative_effect = {
	if = {
		limit = { var:zg361_b1_peer_used < var:zg361_b1_peer_cap }
		if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_1_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_1_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_1_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_1_raw value = -15 }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_2_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_2_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_2_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_2_raw value = -15 }
			}
		}
		else_if = {
			limit = { scope:recipient.var:zg361_b1_peer_slot_3_filled = 0 }
			scope:recipient = {
				set_variable = { name = zg361_b1_peer_slot_3_filled value = 1 }
				set_variable = { name = zg361_b1_peer_slot_3_evaluator value = scope:actor }
				set_variable = { name = zg361_b1_peer_slot_3_raw value = -15 }
			}
		}
		change_variable = { name = zg361_b1_peer_used add = 1 }
		scope:recipient = {
			change_variable = { name = zg361_b1_peer_n add = 1 }
			change_variable = { name = zg361_b1_peer_raw_sum add = -15 }
			change_variable = { name = zg361_b1_peer_timely_n add = 1 }
		}
		debug_log = "ZG361B1: sealed negative peer record submitted"
	}
}
'''
    return generated(bindings + "\n\n" + body)


def render_events() -> bytes:
    return generated(r'''
namespace = zg361b1

# Common-superior season synchronization. The delayed character event resets
# ROOT to each sibling manager; the cycle-open guard makes replays harmless.
zg361b1.90 = {
	type = character_event
	hidden = yes
	immediate = { zg361_b1_open_cycle_effect = yes }
}

# D+180: check-in and one evidence-backed target reset.
zg361b1.100 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_ticket_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_cycle_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 1
				}
				zg361_b1_midcycle_dispatcher_effect = yes
				save_scope_as = zg361_b1_ticket_owner
				save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
				save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
				save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
				trigger_event = { id = zg361b1.101 days = 60 }
			}
			else = { debug_log = "ZG361B1: stale midcycle ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete midcycle ticket ignored" }
	}
}

# D+240: open the bounded three-slot peer/self-evidence window.
zg361b1.101 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 2
				}
				zg361_b1_peer_window_dispatcher_effect = yes
				save_scope_as = zg361_b1_ticket_owner
				save_scope_value_as = { name = zg361_b1_ticket_cycle value = var:zg361_b1_cycle_serial }
				save_scope_value_as = { name = zg361_b1_ticket_case value = var:zg361_b1_case_serial }
				save_scope_value_as = { name = zg361_b1_ticket_state value = var:zg361_b1_cycle_state }
				trigger_event = { id = zg361b1.102 days = 60 }
			}
			else = { debug_log = "ZG361B1: stale peer-window ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete peer-window ticket ignored" }
	}
}

# D+300: seal peer records, then enter the existing ranking engine. The engine
# opens a real shadow window instead of settling immediately when B1 is active.
zg361b1.102 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 3
				}
				zg361_b1_prepare_facts_effect = yes
				zg361_run_review_effect = yes
			}
			else = { debug_log = "ZG361B1: stale facts ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete facts ticket ignored" }
	}
}

# D+330: close shadow evidence and post the manager's quota book.
zg361b1.103 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = { exists = scope:zg361_b1_ticket_owner has_variable = zg361_b1_cycle_state }
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 5
				}
				set_variable = { name = zg361_b1_cycle_state value = 6 }
				zg361_b1_submit_quota_book_effect = yes
			}
			else = { debug_log = "ZG361B1: stale shadow-close ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete shadow-close ticket ignored" }
	}
}

# Common-superior close: either all expected managers are ready, or the frozen
# deadline expires. Both routes share owner/season/case/state and close once.
zg361b1.110 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_bank_ticket_owner
				has_variable = zg361_b1_bank_season
				has_variable = zg361_b1_bank_case_serial
				has_variable = zg361_b1_bank_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_bank_ticket_owner
					var:zg361_b1_bank_season = scope:zg361_b1_bank_ticket_season
					var:zg361_b1_bank_case_serial = scope:zg361_b1_bank_ticket_case
					var:zg361_b1_bank_state = scope:zg361_b1_bank_ticket_state
					var:zg361_b1_bank_state = 1
				}
				if = {
					limit = { has_variable_list = zg361_b1_ready_managers }
					zg361_b1_close_common_superior_bank_effect = yes
				}
				else = {
					# A deadline may legitimately outlive every expected manager.
					# Close the bank without evaluating an unset ready list.
					set_variable = { name = zg361_b1_bank_state value = 2 }
					debug_log = "ZG361B1: common-superior bank closed with no ready managers"
				}
			}
			else = { debug_log = "ZG361B1: stale common-superior bank ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete common-superior bank ticket ignored" }
	}
}

# Common-superior allocation has just written manager-owned receipts, but the
# closing event's ROOT is the superior. Reset ROOT to the allocated manager and
# validate its immutable case token before entering calibration/settlement.
zg361b1.111 = {
	type = character_event
	hidden = yes
	immediate = {
		if = {
			limit = {
				exists = scope:zg361_b1_ticket_owner
				has_variable = zg361_b1_cycle_serial
				has_variable = zg361_b1_case_serial
				has_variable = zg361_b1_cycle_state
			}
			if = {
				limit = {
					this = scope:zg361_b1_ticket_owner
					var:zg361_b1_cycle_serial = scope:zg361_b1_ticket_cycle
					var:zg361_b1_case_serial = scope:zg361_b1_ticket_case
					var:zg361_b1_cycle_state = scope:zg361_b1_ticket_state
					var:zg361_b1_cycle_state = 6
				}
				zg361_b1_open_calibration_effect = yes
			}
			else = { debug_log = "ZG361B1: stale manager-calibration ticket ignored" }
		}
		else = { debug_log = "ZG361B1: incomplete manager-calibration ticket ignored" }
	}
}
''')


def outputs() -> dict[Path, bytes]:
    validate_b1_bindings()
    return {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_b1_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_b1_runtime_events.txt": render_events(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    if args.check:
        if stale:
            print("RED: stale B1 generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: B1 generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} B1 runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
