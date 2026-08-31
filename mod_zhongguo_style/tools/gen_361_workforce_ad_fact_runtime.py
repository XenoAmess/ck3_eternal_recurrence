#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the product-owned AD referral, panel and offer-response facts.

This package deliberately owns only its new effects, events and localization
projections.  The Workforce core will consume the frozen source ABI in a later
serialized integration; this generator does not edit or regenerate that core.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parents[1]
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_workforce_ad_fact_runtime.py\n"
READINESS = "ck3-script-static-ready-unwired-to-workforce-core"
PREFIX = "zg361_wad"
NAMESPACE = "zg361wad"
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


# Exact replacement map for the sixteen still-self-owned AD loader reads.
# The left side remains historical ledger vocabulary only; this package never
# writes those external aliases.
LEGACY_AD16_MAPPING = {
    "zg361_we_ad_external_referral_id": "zg361_wad_referral_source_referral_id",
    "zg361_we_ad_external_referrer": "zg361_wad_referral_source_referrer",
    "zg361_we_ad_external_referral_relationship": "zg361_wad_referral_source_relationship",
    "zg361_we_ad_external_referral_evidence_receipt": "zg361_wad_referral_source_evidence_receipt",
    "zg361_we_ad_external_interviewer_1": "zg361_wad_panel_source_interviewer_1",
    "zg361_we_ad_external_interviewer_2": "zg361_wad_panel_source_interviewer_2",
    "zg361_we_ad_external_interviewer_3": "zg361_wad_panel_source_interviewer_3",
    "zg361_we_ad_external_vote_1": "zg361_wad_panel_source_vote_1",
    "zg361_we_ad_external_vote_2": "zg361_wad_panel_source_vote_2",
    "zg361_we_ad_external_vote_3": "zg361_wad_panel_source_vote_3",
    "zg361_we_ad_external_vote_evidence_1": "zg361_wad_panel_source_vote_evidence_1",
    "zg361_we_ad_external_vote_evidence_2": "zg361_wad_panel_source_vote_evidence_2",
    "zg361_we_ad_external_vote_evidence_3": "zg361_wad_panel_source_vote_evidence_3",
    "zg361_we_ad_external_runner_up": "zg361_wad_panel_source_runner_up",
    "zg361_we_ad_external_runner_up_evidence": "zg361_wad_panel_source_runner_up_evidence",
    "zg361_we_ad_external_refusal_reason_id": "zg361_wad_offer_source_refusal_reason_id",
}

SOURCE_ENVELOPES = {
    "referral": ("pending", "consumed", "owner", "subject", "cycle", "case", "state", "disposition"),
    "panel": ("pending", "consumed", "owner", "subject", "cycle", "case", "state", "disposition"),
    "offer": ("pending", "consumed", "owner", "subject", "cycle", "case", "state", "response"),
}


def validate_contract() -> None:
    if len(LEGACY_AD16_MAPPING) != 16:
        raise ValueError("AD self-owned mapping must remain exactly sixteen fields")
    if len(set(LEGACY_AD16_MAPPING.values())) != 16:
        raise ValueError("AD source destinations must be unique")
    if tuple(LEGACY_AD16_MAPPING) != (
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
    ):
        raise ValueError("AD16 historical ordering drifted")


def generated(body: str) -> bytes:
    return BOM + (HEADER + f"# readiness: {READINESS}\n\n" + body.strip() + "\n").encode("utf-8")


def localized(body: str) -> bytes:
    return BOM + (body.rstrip() + "\n").encode("utf-8")


def render_panel_slot(slot: int) -> str:
    previous = tuple(range(1, slot))
    previous_scopes = "\n".join(
        f"\tvar:zg361_wad_panel_source_interviewer_{index} = {{ save_temporary_scope_as = zg361_wad_panel_i{index}_scope }}"
        for index in previous
    )
    previous_excludes = "\n".join(
        f"\t\t\t\tNOT = {{ this = scope:zg361_wad_panel_i{index}_scope }}"
        for index in previous
    )
    direct_referrer = ""
    if slot == 1:
        direct_referrer = """
	if = {
		limit = {
			var:zg361_wad_panel_source_referrer_vote_policy = 1
			var:zg361_wad_panel_source_referrer = { zg361_is_celestial_liege_trigger = yes }
			NOT = { var:zg361_wad_panel_source_referrer = this }
		}
		set_variable = { name = zg361_wad_panel_source_interviewer_1 value = var:zg361_wad_panel_source_referrer }
	}
"""
    template = r"""
zg361_wad_select_panel_slot___S___effect = {
	save_temporary_scope_as = zg361_wad_panel_subject_scope
	var:zg361_wad_panel_source_owner = { save_temporary_scope_as = zg361_wad_panel_owner_scope }
	var:zg361_wad_panel_source_referrer = { save_temporary_scope_as = zg361_wad_panel_referrer_scope }
__PREVIOUS_SCOPES____DIRECT_REFERRER__
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_panel_source_interviewer___S__ }
			scope:zg361_wad_panel_owner_scope = {
				zg361_is_celestial_liege_trigger = yes
				NOT = { this = scope:zg361_wad_panel_subject_scope }
				NOT = { this = scope:zg361_wad_panel_referrer_scope }
__PREVIOUS_EXCLUDES__
			}
		}
		set_variable = { name = zg361_wad_panel_source_interviewer___S__ value = scope:zg361_wad_panel_owner_scope }
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_panel_source_interviewer___S__ }
			scope:zg361_wad_panel_owner_scope = {
				exists = liege
				liege = {
					zg361_is_celestial_liege_trigger = yes
					NOT = { this = scope:zg361_wad_panel_subject_scope }
					NOT = { this = scope:zg361_wad_panel_referrer_scope }
__PREVIOUS_EXCLUDES__
				}
			}
		}
		scope:zg361_wad_panel_owner_scope.liege = { save_temporary_scope_as = zg361_wad_panel_candidate___S___scope }
	}
	if = {
		limit = { NOT = { has_variable = zg361_wad_panel_source_interviewer___S__ } }
		scope:zg361_wad_panel_owner_scope = {
			ordered_vassal = {
				limit = {
					zg361_is_celestial_liege_trigger = yes
					NOT = { this = scope:zg361_wad_panel_subject_scope }
					NOT = { this = scope:zg361_wad_panel_referrer_scope }
__PREVIOUS_EXCLUDES__
				}
				order_by = stewardship
				position = 0
				save_temporary_scope_as = zg361_wad_panel_candidate___S___scope
			}
		}
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_panel_source_interviewer___S__ }
			NOT = { exists = scope:zg361_wad_panel_candidate___S___scope }
			scope:zg361_wad_panel_owner_scope = { exists = liege }
		}
		scope:zg361_wad_panel_owner_scope.liege = {
			ordered_vassal = {
				limit = {
					zg361_is_celestial_liege_trigger = yes
					NOT = { this = scope:zg361_wad_panel_subject_scope }
					NOT = { this = scope:zg361_wad_panel_referrer_scope }
__PREVIOUS_EXCLUDES__
				}
				order_by = stewardship
				position = 0
				save_temporary_scope_as = zg361_wad_panel_candidate___S___scope
			}
		}
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_panel_source_interviewer___S__ }
			exists = scope:zg361_wad_panel_candidate___S___scope
		}
		set_variable = { name = zg361_wad_panel_source_interviewer___S__ value = scope:zg361_wad_panel_candidate___S___scope }
	}
}
"""
    return (
        template.replace("__S__", str(slot))
        .replace("__PREVIOUS_SCOPES__", previous_scopes)
        .replace("__PREVIOUS_EXCLUDES__", previous_excludes)
        .replace("__DIRECT_REFERRER__", direct_referrer.rstrip())
        .strip()
    )


def render_vote_effect(slot: int) -> str:
    previous_count = slot - 1
    next_action = (
        "zg361_wad_finalize_panel_source_effect = yes"
        if slot == 3
        else "zg361_wad_dispatch_next_vote_effect = yes"
    )
    template = r"""
zg361_wad_submit_panel_vote___S___effect = {
	remove_variable = zg361_wad_runtime_status
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 1
			}
			$TICKET_SUBJECT$ = this
			$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
			$VOTER$ = { zg361_is_celestial_liege_trigger = yes }
			var:zg361_wad_panel_active = 1
			var:zg361_wad_panel_source_owner = $TICKET_OWNER$
			var:zg361_wad_panel_source_subject = this
			var:zg361_wad_panel_source_cycle = $TICKET_CYCLE$
			var:zg361_wad_panel_source_case = $TICKET_CASE$
			var:zg361_wad_panel_vote_count = __PREVIOUS_COUNT__
			var:zg361_wad_panel_source_interviewer___S__ = $VOTER$
			NOT = { has_variable = zg361_wad_panel_source_vote___S__ }
			NOT = { has_variable = zg361_wad_panel_source_vote_evidence___S__ }
			$VOTE$ >= 1
			$VOTE$ <= 3
		}
		$TICKET_OWNER$ = {
			if = { limit = { NOT = { has_variable = zg361_wad_receipt_serial } } set_variable = { name = zg361_wad_receipt_serial value = 0 } }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_vote_receipt___S___value value = var:zg361_wad_receipt_serial }
		}
		set_variable = { name = zg361_wad_panel_source_vote___S__ value = $VOTE$ }
		set_variable = { name = zg361_wad_panel_source_vote_evidence___S__ value = scope:zg361_wad_vote_receipt___S___value }
		set_variable = { name = zg361_wad_panel_vote_receipt_actor___S__ value = $VOTER$ }
		change_variable = { name = zg361_wad_panel_vote_count add = 1 }
		set_variable = { name = zg361_wad_runtime_status value = 1 }
		__NEXT_ACTION__
	}
}
"""
    return (
        template.replace("__S__", str(slot))
        .replace("__PREVIOUS_COUNT__", str(previous_count))
        .replace("__NEXT_ACTION__", next_action)
        .strip()
    )


def render_ai_vote_effect(slot: int) -> str:
    template = r"""
zg361_wad_resolve_ai_panel_vote___S___effect = {
	if = {
		limit = {
			is_ai = yes
			zg361_is_celestial_liege_trigger = yes
			exists = scope:zg361_wad_panel_subject_scope
			this = scope:zg361_wad_panel_actor_scope
		}
		save_temporary_scope_as = zg361_wad_panel_ai_actor_scope
		if = {
			limit = { stewardship >= 12 }
			scope:zg361_wad_panel_subject_scope = {
				zg361_wad_submit_panel_vote___S___effect = {
					TICKET_OWNER = var:zg361_wad_panel_source_owner TICKET_SUBJECT = this
					TICKET_CYCLE = var:zg361_wad_panel_source_cycle TICKET_CASE = var:zg361_wad_panel_source_case
					VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 3
				}
			}
		}
		else_if = {
			limit = { stewardship >= 8 }
			scope:zg361_wad_panel_subject_scope = {
				zg361_wad_submit_panel_vote___S___effect = {
					TICKET_OWNER = var:zg361_wad_panel_source_owner TICKET_SUBJECT = this
					TICKET_CYCLE = var:zg361_wad_panel_source_cycle TICKET_CASE = var:zg361_wad_panel_source_case
					VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 2
				}
			}
		}
		else = {
			scope:zg361_wad_panel_subject_scope = {
				zg361_wad_submit_panel_vote___S___effect = {
					TICKET_OWNER = var:zg361_wad_panel_source_owner TICKET_SUBJECT = this
					TICKET_CYCLE = var:zg361_wad_panel_source_cycle TICKET_CASE = var:zg361_wad_panel_source_case
					VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 1
				}
			}
		}
	}
}
"""
    return template.replace("__S__", str(slot)).strip()


def render_effects() -> bytes:
    validate_contract()
    panel_slots = "\n\n".join(render_panel_slot(slot) for slot in (1, 2, 3))
    vote_effects = "\n\n".join(render_vote_effect(slot) for slot in (1, 2, 3))
    ai_vote_effects = "\n\n".join(render_ai_vote_effect(slot) for slot in (1, 2, 3))
    body = r"""
# Public entry 1/3.  Called in the candidate/subject scope after the current
# #273 object is consumed while AD remains in state 1.
zg361_wad_begin_referral_source_effect = {
	remove_variable = zg361_wad_runtime_status
	remove_variable = zg361_wad_runtime_blocked_reason
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 1
			}
			$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
			$TICKET_SUBJECT$ = this
			has_variable = zg361_we_m273_business_object_created
			has_variable = zg361_we_m273_object_owner
			has_variable = zg361_we_m273_object_subject
			has_variable = zg361_we_m273_object_cycle
			has_variable = zg361_we_m273_object_case
			has_variable = zg361_we_m273_object_state
			has_variable = zg361_we_m273_object_consumed
			has_variable = zg361_we_m273_candidate_fingerprint
			var:zg361_we_m273_business_object_created = 1
			var:zg361_we_m273_object_owner = $TICKET_OWNER$
			var:zg361_we_m273_object_subject = this
			var:zg361_we_m273_object_cycle = $TICKET_CYCLE$
			var:zg361_we_m273_object_case = $TICKET_CASE$
			var:zg361_we_m273_object_state = 1
			var:zg361_we_m273_object_consumed = 1
			var:zg361_we_m273_candidate_fingerprint = this
			trigger_if = { limit = { has_variable = zg361_wad_referral_source_pending } var:zg361_wad_referral_source_pending = 0 }
			trigger_else = { always = yes }
		}
		remove_variable = zg361_wad_referral_source_referral_id
		remove_variable = zg361_wad_referral_source_referrer
		remove_variable = zg361_wad_referral_source_relationship
		remove_variable = zg361_wad_referral_source_evidence_receipt
		set_variable = { name = zg361_wad_referral_flow_active value = 1 }
		set_variable = { name = zg361_wad_referral_source_pending value = 0 }
		set_variable = { name = zg361_wad_referral_source_consumed value = 0 }
		set_variable = { name = zg361_wad_referral_source_owner value = $TICKET_OWNER$ }
		set_variable = { name = zg361_wad_referral_source_subject value = this }
		set_variable = { name = zg361_wad_referral_source_cycle value = $TICKET_CYCLE$ }
		set_variable = { name = zg361_wad_referral_source_case value = $TICKET_CASE$ }
		set_variable = { name = zg361_wad_referral_source_state value = 1 }
		set_variable = { name = zg361_wad_referral_source_disposition value = 0 }
		set_variable = { name = zg361_wad_runtime_status value = 1 }
		zg361_wad_select_real_referrer_effect = yes
	}
	else_if = {
		limit = {
			var:zg361_wad_referral_source_pending = 1
			var:zg361_wad_referral_source_owner = $TICKET_OWNER$
			var:zg361_wad_referral_source_subject = this
			var:zg361_wad_referral_source_cycle = $TICKET_CYCLE$
			var:zg361_wad_referral_source_case = $TICKET_CASE$
			var:zg361_wad_referral_source_state = 1
		}
		set_variable = { name = zg361_wad_runtime_status value = 2 }
	}
	else = { set_variable = { name = zg361_wad_runtime_status value = 4 } set_variable = { name = zg361_wad_runtime_blocked_reason value = 2711 } }
}

zg361_wad_select_real_referrer_effect = {
	save_scope_as = zg361_wad_referral_subject_scope
	var:zg361_wad_referral_source_owner = { save_scope_as = zg361_wad_referral_owner_scope }
	ordered_close_family_member = {
		limit = {
			is_alive = yes is_adult = yes
			zg361_is_celestial_liege_trigger = yes
			NOT = { this = scope:zg361_wad_referral_subject_scope }
		}
		order_by = diplomacy
		position = 0
		save_scope_as = zg361_wad_referral_actor_scope
	}
	if = {
		limit = { exists = scope:zg361_wad_referral_actor_scope }
		set_variable = { name = zg361_wad_referral_source_referrer value = scope:zg361_wad_referral_actor_scope }
		set_variable = { name = zg361_wad_referral_source_relationship value = 1 }
	}
	if = {
		limit = { NOT = { exists = scope:zg361_wad_referral_actor_scope } }
		ordered_relation = {
			type = friend
			limit = {
				is_alive = yes is_adult = yes
				zg361_is_celestial_liege_trigger = yes
				NOT = { this = scope:zg361_wad_referral_subject_scope }
			}
			order_by = diplomacy
			position = 0
			save_scope_as = zg361_wad_referral_actor_scope
		}
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_referral_source_referrer }
			exists = scope:zg361_wad_referral_actor_scope
		}
		set_variable = { name = zg361_wad_referral_source_referrer value = scope:zg361_wad_referral_actor_scope }
		set_variable = { name = zg361_wad_referral_source_relationship value = 2 }
	}
	if = {
		limit = {
			NOT = { has_variable = zg361_wad_referral_source_referrer }
			liege = scope:zg361_wad_referral_owner_scope
			scope:zg361_wad_referral_owner_scope = { zg361_is_celestial_liege_trigger = yes }
			NOT = { scope:zg361_wad_referral_owner_scope = scope:zg361_wad_referral_subject_scope }
		}
		set_variable = { name = zg361_wad_referral_source_referrer value = scope:zg361_wad_referral_owner_scope }
		set_variable = { name = zg361_wad_referral_source_relationship value = 3 }
	}
	if = {
		limit = {
			has_variable = zg361_wad_referral_source_referrer
			var:zg361_wad_referral_source_referrer = { zg361_is_celestial_liege_trigger = yes }
			NOT = { var:zg361_wad_referral_source_referrer = this }
		}
		zg361_wad_dispatch_referral_response_effect = yes
	}
	else = {
		set_variable = { name = zg361_wad_referral_flow_active value = 0 }
		set_variable = { name = zg361_wad_referral_source_pending value = 1 }
		set_variable = { name = zg361_wad_referral_source_disposition value = 3 }
	}
}

zg361_wad_dispatch_referral_response_effect = {
	if = {
		limit = {
			var:zg361_wad_referral_flow_active = 1
			var:zg361_wad_referral_source_subject = this
			var:zg361_wad_referral_source_disposition = 0
		}
		save_scope_as = zg361_wad_referral_subject_scope
		var:zg361_wad_referral_source_referrer = {
			save_scope_as = zg361_wad_referral_actor_scope
			if = { limit = { is_ai = no } trigger_event = { id = zg361wad.1 } }
			else = {
				scope:zg361_wad_referral_subject_scope = {
					zg361_wad_submit_referral_effect = {
						TICKET_OWNER = var:zg361_wad_referral_source_owner TICKET_SUBJECT = this
						TICKET_CYCLE = var:zg361_wad_referral_source_cycle TICKET_CASE = var:zg361_wad_referral_source_case
						REFERRER = scope:zg361_wad_referral_actor_scope
					}
				}
			}
		}
	}
}

zg361_wad_submit_referral_effect = {
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 1
			}
			$TICKET_SUBJECT$ = this
			$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
			$REFERRER$ = { zg361_is_celestial_liege_trigger = yes }
			var:zg361_wad_referral_flow_active = 1
			var:zg361_wad_referral_source_owner = $TICKET_OWNER$
			var:zg361_wad_referral_source_subject = this
			var:zg361_wad_referral_source_cycle = $TICKET_CYCLE$
			var:zg361_wad_referral_source_case = $TICKET_CASE$
			var:zg361_wad_referral_source_referrer = $REFERRER$
			NOT = { $REFERRER$ = this }
			var:zg361_wad_referral_source_relationship >= 1
			var:zg361_wad_referral_source_relationship <= 3
		}
		$TICKET_OWNER$ = {
			if = { limit = { NOT = { has_variable = zg361_wad_receipt_serial } } set_variable = { name = zg361_wad_receipt_serial value = 0 } }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_referral_object_value value = var:zg361_wad_receipt_serial }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_referral_receipt_value value = var:zg361_wad_receipt_serial }
		}
		set_variable = { name = zg361_wad_referral_source_referral_id value = scope:zg361_wad_referral_object_value }
		set_variable = { name = zg361_wad_referral_source_evidence_receipt value = scope:zg361_wad_referral_receipt_value }
		set_variable = { name = zg361_wad_referral_source_pending value = 1 }
		set_variable = { name = zg361_wad_referral_source_consumed value = 0 }
		set_variable = { name = zg361_wad_referral_source_disposition value = 1 }
		set_variable = { name = zg361_wad_referral_flow_active value = 0 }
	}
}

zg361_wad_decline_referral_effect = {
	if = {
		limit = {
			var:zg361_wad_referral_flow_active = 1
			var:zg361_wad_referral_source_subject = this
			var:zg361_wad_referral_source_referrer = $REFERRER$
			NOT = { $REFERRER$ = this }
		}
		remove_variable = zg361_wad_referral_source_referral_id
		remove_variable = zg361_wad_referral_source_evidence_receipt
		set_variable = { name = zg361_wad_referral_source_pending value = 1 }
		set_variable = { name = zg361_wad_referral_source_consumed value = 0 }
		set_variable = { name = zg361_wad_referral_source_disposition value = 2 }
		set_variable = { name = zg361_wad_referral_flow_active value = 0 }
	}
}

# Public entry 2/3.  Called after a current #271 A/B object is consumed.  It
# freezes real managers, a real alternate candidate when one exists, and then
# asks every frozen interviewer for their own vote.
zg361_wad_begin_panel_source_effect = {
	remove_variable = zg361_wad_runtime_status
	remove_variable = zg361_wad_runtime_blocked_reason
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 1
			}
			$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
			$TICKET_SUBJECT$ = this
			has_variable = zg361_we_m271_business_object_created
			has_variable = zg361_we_m271_object_owner
			has_variable = zg361_we_m271_object_subject
			has_variable = zg361_we_m271_object_cycle
			has_variable = zg361_we_m271_object_case
			has_variable = zg361_we_m271_object_state
			has_variable = zg361_we_m271_object_consumed
			has_variable = zg361_we_m271_referrer
			has_variable = zg361_we_m271_referrer_vote_policy
			var:zg361_we_m271_business_object_created = 1
			var:zg361_we_m271_object_owner = $TICKET_OWNER$
			var:zg361_we_m271_object_subject = this
			var:zg361_we_m271_object_cycle = $TICKET_CYCLE$
			var:zg361_we_m271_object_case = $TICKET_CASE$
			var:zg361_we_m271_object_state = 1
			var:zg361_we_m271_object_consumed = 1
			var:zg361_we_m271_referrer = { zg361_is_celestial_liege_trigger = yes }
			NOT = { var:zg361_we_m271_referrer = this }
			var:zg361_we_m271_referrer_vote_policy >= 0
			var:zg361_we_m271_referrer_vote_policy <= 1
			trigger_if = { limit = { has_variable = zg361_wad_panel_source_pending } var:zg361_wad_panel_source_pending = 0 }
			trigger_else = { always = yes }
		}
		remove_variable = zg361_wad_panel_source_interviewer_1
		remove_variable = zg361_wad_panel_source_interviewer_2
		remove_variable = zg361_wad_panel_source_interviewer_3
		remove_variable = zg361_wad_panel_source_vote_1
		remove_variable = zg361_wad_panel_source_vote_2
		remove_variable = zg361_wad_panel_source_vote_3
		remove_variable = zg361_wad_panel_source_vote_evidence_1
		remove_variable = zg361_wad_panel_source_vote_evidence_2
		remove_variable = zg361_wad_panel_source_vote_evidence_3
		remove_variable = zg361_wad_panel_source_runner_up
		remove_variable = zg361_wad_panel_source_runner_up_evidence
		set_variable = { name = zg361_wad_panel_active value = 0 }
		set_variable = { name = zg361_wad_panel_source_pending value = 0 }
		set_variable = { name = zg361_wad_panel_source_consumed value = 0 }
		set_variable = { name = zg361_wad_panel_source_owner value = $TICKET_OWNER$ }
		set_variable = { name = zg361_wad_panel_source_subject value = this }
		set_variable = { name = zg361_wad_panel_source_cycle value = $TICKET_CYCLE$ }
		set_variable = { name = zg361_wad_panel_source_case value = $TICKET_CASE$ }
		set_variable = { name = zg361_wad_panel_source_state value = 1 }
		set_variable = { name = zg361_wad_panel_source_disposition value = 0 }
		set_variable = { name = zg361_wad_panel_source_referrer value = var:zg361_we_m271_referrer }
		set_variable = { name = zg361_wad_panel_source_referrer_vote_policy value = var:zg361_we_m271_referrer_vote_policy }
		set_variable = { name = zg361_wad_panel_vote_count value = 0 }
		set_variable = { name = zg361_wad_runtime_status value = 1 }
		zg361_wad_freeze_real_panel_effect = yes
	}
	else_if = {
		limit = {
			var:zg361_wad_panel_source_pending = 1
			var:zg361_wad_panel_source_owner = $TICKET_OWNER$
			var:zg361_wad_panel_source_subject = this
			var:zg361_wad_panel_source_cycle = $TICKET_CYCLE$
			var:zg361_wad_panel_source_case = $TICKET_CASE$
			var:zg361_wad_panel_source_state = 1
		}
		set_variable = { name = zg361_wad_runtime_status value = 2 }
	}
	else = { set_variable = { name = zg361_wad_runtime_status value = 4 } set_variable = { name = zg361_wad_runtime_blocked_reason value = 2671 } }
}

__PANEL_SLOTS__

zg361_wad_freeze_real_panel_effect = {
	save_temporary_scope_as = zg361_wad_panel_subject_scope
	var:zg361_wad_panel_source_owner = { save_temporary_scope_as = zg361_wad_panel_owner_scope }
	zg361_wad_select_panel_slot_1_effect = yes
	zg361_wad_select_panel_slot_2_effect = yes
	zg361_wad_select_panel_slot_3_effect = yes
	if = { limit = { has_variable = zg361_wad_panel_source_interviewer_1 } var:zg361_wad_panel_source_interviewer_1 = { save_temporary_scope_as = zg361_wad_panel_i1_scope } }
	if = { limit = { has_variable = zg361_wad_panel_source_interviewer_2 } var:zg361_wad_panel_source_interviewer_2 = { save_temporary_scope_as = zg361_wad_panel_i2_scope } }
	if = { limit = { has_variable = zg361_wad_panel_source_interviewer_3 } var:zg361_wad_panel_source_interviewer_3 = { save_temporary_scope_as = zg361_wad_panel_i3_scope } }
	scope:zg361_wad_panel_owner_scope = {
		ordered_vassal = {
			limit = {
				zg361_is_reviewable_vassal_trigger = yes
				NOT = { this = scope:zg361_wad_panel_subject_scope }
				NOT = { this = scope:zg361_wad_panel_i1_scope }
				NOT = { this = scope:zg361_wad_panel_i2_scope }
				NOT = { this = scope:zg361_wad_panel_i3_scope }
				trigger_if = { limit = { has_variable = zg361_we_candidate_active } var:zg361_we_candidate_active = 0 }
				trigger_else = { always = yes }
				trigger_if = { limit = { has_variable = zg361_we_formal_hc_active } var:zg361_we_formal_hc_active = 0 }
				trigger_else = { always = yes }
			}
			order_by = stewardship
			position = 0
			save_temporary_scope_as = zg361_wad_runner_up_scope
		}
	}
	if = {
		limit = { exists = scope:zg361_wad_runner_up_scope }
		set_variable = { name = zg361_wad_panel_source_runner_up value = scope:zg361_wad_runner_up_scope }
		set_variable = { name = zg361_wad_panel_runner_up_present value = 1 }
		var:zg361_wad_panel_source_owner = {
			if = { limit = { NOT = { has_variable = zg361_wad_receipt_serial } } set_variable = { name = zg361_wad_receipt_serial value = 0 } }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_runner_up_receipt_value value = var:zg361_wad_receipt_serial }
		}
		set_variable = { name = zg361_wad_panel_source_runner_up_evidence value = scope:zg361_wad_runner_up_receipt_value }
	}
	else = { set_variable = { name = zg361_wad_panel_runner_up_present value = 0 } }
	if = {
		limit = {
			has_variable = zg361_wad_panel_source_interviewer_1
			has_variable = zg361_wad_panel_source_interviewer_2
			has_variable = zg361_wad_panel_source_interviewer_3
			var:zg361_wad_panel_source_interviewer_1 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:zg361_wad_panel_subject_scope } }
			var:zg361_wad_panel_source_interviewer_2 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:zg361_wad_panel_subject_scope } }
			var:zg361_wad_panel_source_interviewer_3 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:zg361_wad_panel_subject_scope } }
			NOT = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_interviewer_2 }
			NOT = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_interviewer_3 }
			NOT = { var:zg361_wad_panel_source_interviewer_2 = var:zg361_wad_panel_source_interviewer_3 }
			trigger_if = {
				limit = { var:zg361_wad_panel_source_referrer_vote_policy = 0 }
				NOT = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_referrer }
				NOT = { var:zg361_wad_panel_source_interviewer_2 = var:zg361_wad_panel_source_referrer }
				NOT = { var:zg361_wad_panel_source_interviewer_3 = var:zg361_wad_panel_source_referrer }
			}
			trigger_else = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_referrer }
		}
		set_variable = { name = zg361_wad_panel_active value = 1 }
		zg361_wad_dispatch_next_vote_effect = yes
	}
	else = {
		remove_variable = zg361_wad_panel_source_interviewer_1
		remove_variable = zg361_wad_panel_source_interviewer_2
		remove_variable = zg361_wad_panel_source_interviewer_3
		remove_variable = zg361_wad_panel_source_runner_up
		remove_variable = zg361_wad_panel_source_runner_up_evidence
		set_variable = { name = zg361_wad_panel_runner_up_present value = 0 }
		set_variable = { name = zg361_wad_panel_source_pending value = 1 }
		set_variable = { name = zg361_wad_panel_source_consumed value = 0 }
		set_variable = { name = zg361_wad_panel_source_disposition value = 3 }
		set_variable = { name = zg361_wad_panel_active value = 0 }
	}
}

zg361_wad_dispatch_next_vote_effect = {
	if = {
		limit = { var:zg361_wad_panel_active = 1 var:zg361_wad_panel_source_subject = this }
		save_scope_as = zg361_wad_panel_subject_scope
		if = {
			limit = { var:zg361_wad_panel_vote_count = 0 }
			var:zg361_wad_panel_source_interviewer_1 = {
				save_scope_as = zg361_wad_panel_actor_scope
				if = { limit = { is_ai = no } trigger_event = { id = zg361wad.11 } }
				else = { zg361_wad_resolve_ai_panel_vote_1_effect = yes }
			}
		}
		else_if = {
			limit = { var:zg361_wad_panel_vote_count = 1 }
			var:zg361_wad_panel_source_interviewer_2 = {
				save_scope_as = zg361_wad_panel_actor_scope
				if = { limit = { is_ai = no } trigger_event = { id = zg361wad.12 } }
				else = { zg361_wad_resolve_ai_panel_vote_2_effect = yes }
			}
		}
		else_if = {
			limit = { var:zg361_wad_panel_vote_count = 2 }
			var:zg361_wad_panel_source_interviewer_3 = {
				save_scope_as = zg361_wad_panel_actor_scope
				if = { limit = { is_ai = no } trigger_event = { id = zg361wad.13 } }
				else = { zg361_wad_resolve_ai_panel_vote_3_effect = yes }
			}
		}
	}
}

__VOTE_EFFECTS__

__AI_VOTE_EFFECTS__

zg361_wad_finalize_panel_source_effect = {
	if = {
		limit = {
			var:zg361_wad_panel_active = 1
			var:zg361_wad_panel_vote_count = 3
			has_variable = zg361_wad_panel_source_vote_1
			has_variable = zg361_wad_panel_source_vote_2
			has_variable = zg361_wad_panel_source_vote_3
			has_variable = zg361_wad_panel_source_vote_evidence_1
			has_variable = zg361_wad_panel_source_vote_evidence_2
			has_variable = zg361_wad_panel_source_vote_evidence_3
			var:zg361_wad_panel_vote_receipt_actor_1 = var:zg361_wad_panel_source_interviewer_1
			var:zg361_wad_panel_vote_receipt_actor_2 = var:zg361_wad_panel_source_interviewer_2
			var:zg361_wad_panel_vote_receipt_actor_3 = var:zg361_wad_panel_source_interviewer_3
			NOT = { var:zg361_wad_panel_source_vote_evidence_1 = var:zg361_wad_panel_source_vote_evidence_2 }
			NOT = { var:zg361_wad_panel_source_vote_evidence_1 = var:zg361_wad_panel_source_vote_evidence_3 }
			NOT = { var:zg361_wad_panel_source_vote_evidence_2 = var:zg361_wad_panel_source_vote_evidence_3 }
		}
		set_variable = { name = zg361_wad_panel_source_pending value = 1 }
		set_variable = { name = zg361_wad_panel_source_consumed value = 0 }
		set_variable = { name = zg361_wad_panel_source_disposition value = 1 }
		set_variable = { name = zg361_wad_panel_active value = 0 }
	}
}

# Public entry 3/3.  The candidate answers their own offer.  A human candidate
# always receives their own event; an AI candidate silently accepts under the
# already-authorized manager-owned AI path.
zg361_wad_begin_offer_response_source_effect = {
	remove_variable = zg361_wad_runtime_status
	remove_variable = zg361_wad_runtime_blocked_reason
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
				CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
				STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
				EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
			}
			$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
			$TICKET_SUBJECT$ = this
			has_variable = zg361_we_m272_business_object_created
			has_variable = zg361_we_m272_object_owner
			has_variable = zg361_we_m272_object_subject
			has_variable = zg361_we_m272_object_cycle
			has_variable = zg361_we_m272_object_case
			has_variable = zg361_we_m272_object_consumed
			var:zg361_we_m272_business_object_created = 1
			var:zg361_we_m272_object_owner = $TICKET_OWNER$
			var:zg361_we_m272_object_subject = this
			var:zg361_we_m272_object_cycle = $TICKET_CYCLE$
			var:zg361_we_m272_object_case = $TICKET_CASE$
			var:zg361_we_m272_object_consumed = 1
			trigger_if = { limit = { has_variable = zg361_wad_offer_source_pending } var:zg361_wad_offer_source_pending = 0 }
			trigger_else = { always = yes }
		}
		remove_variable = zg361_wad_offer_source_refusal_reason_id
		remove_variable = zg361_wad_offer_source_response_receipt
		set_variable = { name = zg361_wad_offer_flow_active value = 1 }
		set_variable = { name = zg361_wad_offer_source_pending value = 0 }
		set_variable = { name = zg361_wad_offer_source_consumed value = 0 }
		set_variable = { name = zg361_wad_offer_source_owner value = $TICKET_OWNER$ }
		set_variable = { name = zg361_wad_offer_source_subject value = this }
		set_variable = { name = zg361_wad_offer_source_cycle value = $TICKET_CYCLE$ }
		set_variable = { name = zg361_wad_offer_source_case value = $TICKET_CASE$ }
		set_variable = { name = zg361_wad_offer_source_state value = 4 }
		set_variable = { name = zg361_wad_offer_source_response value = 0 }
		set_variable = { name = zg361_wad_runtime_status value = 1 }
		if = { limit = { is_ai = no } trigger_event = { id = zg361wad.20 } }
		else = { zg361_wad_accept_offer_effect = { RESPONDENT = this } }
	}
	else_if = {
		limit = {
			var:zg361_wad_offer_source_pending = 1
			var:zg361_wad_offer_source_owner = $TICKET_OWNER$
			var:zg361_wad_offer_source_subject = this
			var:zg361_wad_offer_source_cycle = $TICKET_CYCLE$
			var:zg361_wad_offer_source_case = $TICKET_CASE$
			var:zg361_wad_offer_source_state = 4
		}
		set_variable = { name = zg361_wad_runtime_status value = 2 }
	}
	else = { set_variable = { name = zg361_wad_runtime_status value = 4 } set_variable = { name = zg361_wad_runtime_blocked_reason value = 2742 } }
}

zg361_wad_accept_offer_effect = {
	if = {
		limit = {
			var:zg361_wad_offer_flow_active = 1
			var:zg361_wad_offer_source_subject = this
			$RESPONDENT$ = this
			var:zg361_wad_offer_source_response = 0
		}
		var:zg361_wad_offer_source_owner = {
			if = { limit = { NOT = { has_variable = zg361_wad_receipt_serial } } set_variable = { name = zg361_wad_receipt_serial value = 0 } }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_offer_receipt_value value = var:zg361_wad_receipt_serial }
		}
		set_variable = { name = zg361_wad_offer_source_response_receipt value = scope:zg361_wad_offer_receipt_value }
		set_variable = { name = zg361_wad_offer_source_response value = 1 }
		set_variable = { name = zg361_wad_offer_source_pending value = 1 }
		set_variable = { name = zg361_wad_offer_source_consumed value = 0 }
		set_variable = { name = zg361_wad_offer_flow_active value = 0 }
	}
}

zg361_wad_refuse_offer_effect = {
	if = {
		limit = {
			var:zg361_wad_offer_flow_active = 1
			var:zg361_wad_offer_source_subject = this
			$RESPONDENT$ = this
			var:zg361_wad_offer_source_response = 0
			$REASON$ >= 1
			$REASON$ <= 3
		}
		var:zg361_wad_offer_source_owner = {
			if = { limit = { NOT = { has_variable = zg361_wad_receipt_serial } } set_variable = { name = zg361_wad_receipt_serial value = 0 } }
			change_variable = { name = zg361_wad_receipt_serial add = 1 }
			save_scope_value_as = { name = zg361_wad_offer_receipt_value value = var:zg361_wad_receipt_serial }
		}
		set_variable = { name = zg361_wad_offer_source_response_receipt value = scope:zg361_wad_offer_receipt_value }
		set_variable = { name = zg361_wad_offer_source_refusal_reason_id value = $REASON$ }
		set_variable = { name = zg361_wad_offer_source_response value = 2 }
		set_variable = { name = zg361_wad_offer_source_pending value = 1 }
		set_variable = { name = zg361_wad_offer_source_consumed value = 0 }
		set_variable = { name = zg361_wad_offer_flow_active value = 0 }
	}
}
"""
    body = (
        body.replace("__PANEL_SLOTS__", panel_slots)
        .replace("__VOTE_EFFECTS__", vote_effects)
        .replace("__AI_VOTE_EFFECTS__", ai_vote_effects)
    )
    return generated(body)


def render_vote_event(slot: int) -> str:
    options = []
    for letter, vote in zip("abc", (3, 2, 1)):
        options.append(
            f"""option = {{
\tname = zg361wad.vote.{letter}
\tscope:zg361_wad_panel_subject_scope = {{
\t\tzg361_wad_submit_panel_vote_{slot}_effect = {{
\t\t\tTICKET_OWNER = var:zg361_wad_panel_source_owner TICKET_SUBJECT = this
\t\t\tTICKET_CYCLE = var:zg361_wad_panel_source_cycle TICKET_CASE = var:zg361_wad_panel_source_case
\t\t\tVOTER = scope:zg361_wad_panel_actor_scope VOTE = {vote}
\t\t}}
\t}}
}}"""
        )
    return f"""zg361wad.{10 + slot} = {{
\ttype = character_event
\ttitle = zg361wad.vote.t
\tdesc = zg361wad.vote.desc
\ttrigger = {{
\t\tis_ai = no
\t\texists = scope:zg361_wad_panel_subject_scope
\t\texists = scope:zg361_wad_panel_actor_scope
\t\tthis = scope:zg361_wad_panel_actor_scope
\t\tscope:zg361_wad_panel_subject_scope = {{
\t\t\tvar:zg361_wad_panel_active = 1
\t\t\tvar:zg361_wad_panel_vote_count = {slot - 1}
\t\t\tvar:zg361_wad_panel_source_interviewer_{slot} = root
\t\t}}
\t}}
\n{chr(10).join(options)}
}}"""


def render_events() -> bytes:
    vote_events = "\n\n".join(render_vote_event(slot) for slot in (1, 2, 3))
    body = r"""
namespace = zg361wad

zg361wad.1 = {
	type = character_event
	title = zg361wad.referral.t
	desc = zg361wad.referral.desc
	trigger = {
		is_ai = no
		exists = scope:zg361_wad_referral_subject_scope
		exists = scope:zg361_wad_referral_actor_scope
		this = scope:zg361_wad_referral_actor_scope
		scope:zg361_wad_referral_subject_scope = {
			var:zg361_wad_referral_flow_active = 1
			var:zg361_wad_referral_source_referrer = root
		}
	}
	option = {
		name = zg361wad.referral.submit
		scope:zg361_wad_referral_subject_scope = {
			zg361_wad_submit_referral_effect = {
				TICKET_OWNER = var:zg361_wad_referral_source_owner TICKET_SUBJECT = this
				TICKET_CYCLE = var:zg361_wad_referral_source_cycle TICKET_CASE = var:zg361_wad_referral_source_case
				REFERRER = scope:zg361_wad_referral_actor_scope
			}
		}
	}
	option = {
		name = zg361wad.referral.decline
		scope:zg361_wad_referral_subject_scope = {
			zg361_wad_decline_referral_effect = { REFERRER = scope:zg361_wad_referral_actor_scope }
		}
	}
}

__VOTE_EVENTS__

zg361wad.20 = {
	type = character_event
	title = zg361wad.offer.t
	desc = zg361wad.offer.desc
	trigger = {
		is_ai = no
		var:zg361_wad_offer_flow_active = 1
		var:zg361_wad_offer_source_subject = this
		var:zg361_wad_offer_source_state = 4
	}
	option = { name = zg361wad.offer.accept zg361_wad_accept_offer_effect = { RESPONDENT = this } }
	option = { name = zg361wad.offer.refuse_pay zg361_wad_refuse_offer_effect = { RESPONDENT = this REASON = 1 } }
	option = { name = zg361wad.offer.refuse_role zg361_wad_refuse_offer_effect = { RESPONDENT = this REASON = 2 } }
	option = { name = zg361wad.offer.refuse_move zg361_wad_refuse_offer_effect = { RESPONDENT = this REASON = 3 } }
}
""".replace("__VOTE_EVENTS__", vote_events)
    return generated(body)


LOCALIZATION_EN = {
    "referral.t": "A Referral Must Have an Author",
    "referral.desc": "You are the named referrer for this candidate. Submit the relationship openly and leave a case-bound receipt, or decline; nobody else may sign in your place.",
    "referral.submit": "Submit my referral and disclose the relationship",
    "referral.decline": "I did not make this referral",
    "vote.t": "Seal Your Own Interview Vote",
    "vote.desc": "You are one of three distinct managers on this panel. Record your own judgment before any debrief; the receipt binds this vote to you and this candidate.",
    "vote.a": "Strong evidence: advance the candidate",
    "vote.b": "Mixed evidence: keep the candidate under review",
    "vote.c": "Insufficient evidence: do not advance",
    "offer.t": "The Offer Is Yours to Answer",
    "offer.desc": "The terms have reached you personally. Accept them, or refuse for the reason that actually blocks this appointment; the manager cannot answer on your behalf.",
    "offer.accept": "Accept the offer",
    "offer.refuse_pay": "Refuse: compensation is inadequate",
    "offer.refuse_role": "Refuse: the role or authority is wrong",
    "offer.refuse_move": "Refuse: relocation or reporting terms are unacceptable",
}

LOCALIZATION_CN = {
    "referral.t": "内推必须有亲笔署名",
    "referral.desc": "你是这名候选人的实名内推人。请公开关系并留下绑定本案的回执，或者明确否认；任何经理都不能替你落款。",
    "referral.submit": "提交我的内推，并公开关系",
    "referral.decline": "这份内推不是我提交的",
    "vote.t": "封存你自己的面试票",
    "vote.desc": "你是三名互不相同的经理评委之一。复盘开始前，请亲自写下判断；回执会把这张票与你和候选人一并冻结。",
    "vote.a": "证据充分：推进候选人",
    "vote.b": "证据混合：继续审查",
    "vote.c": "证据不足：不予推进",
    "offer.t": "这份 Offer 只能由你回答",
    "offer.desc": "条款已经送到你本人面前。接受，或如实写下阻止任命的原因；经理不能替你回答。",
    "offer.accept": "接受 Offer",
    "offer.refuse_pay": "拒绝：报酬不足",
    "offer.refuse_role": "拒绝：岗位或权限不符",
    "offer.refuse_move": "拒绝：调动或报到条件不可接受",
}


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    values = LOCALIZATION_CN if language == "simp_chinese" else LOCALIZATION_EN
    rows = [f"l_{language}:"]
    for key, value in values.items():
        rows.append(f' zg361wad.{key}:0 "{esc(value)}"')
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_workforce_ad_fact_runtime_effects.txt": render_effects(),
        MOD_ROOT / "events" / "zg361_workforce_ad_fact_runtime_events.txt": render_events(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"zg361_workforce_ad_fact_l_{language}.yml"
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
            print("RED: stale Workforce AD fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print(f"GREEN: {len(rendered)} Workforce AD fact files are current ({READINESS})")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce AD fact runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
