#!/usr/bin/env python3
"""Source-reviewed player career-learning interrupt contracts."""

from __future__ import annotations

from typing import Final


CAREER_LEARNING_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "zg361cl.314": {
        # Player-subject response for the funded relocation package. The
        # event reads its five-part prompt ticket from root variables, not
        # from saved scopes. Route B records a valid response and resumes the
        # stage without moving the player or charging the manager/treasury,
        # making option 2 the bounded minimum-external-side-effect path.
        "date_raw": 53173584,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "saved_scope_name_sets": ((
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
            "zg361_b1_self_ticket_owner",
            "zg361_b1_self_ticket_subject",
            "zg361_b1_self_ticket_cycle",
            "zg361_b1_self_ticket_case",
            "zg361_b1_self_ticket_state",
            "zg361_b1_shadow_ticket_owner",
            "zg361_b1_shadow_ticket_subject",
            "zg361_b1_shadow_ticket_cycle",
            "zg361_b1_shadow_ticket_case",
            "zg361_b1_shadow_ticket_state",
            "zg361_b1_oversight_ticket_owner",
            "zg361_b1_oversight_ticket_cycle",
            "zg361_b1_oversight_ticket_case",
            "zg361_b1_oversight_ticket_state",
            "zg361_b1_pending_continue_owner",
            "zg361_b1_pending_continue_subject",
            "zg361_b1_pending_continue_cycle",
            "zg361_b1_pending_continue_case",
            "zg361_b1_pending_continue_state",
            "zg361_b1_reopen_ticket_subject",
            "zg361_b1_reopen_ticket_owner",
            "zg361_b1_reopen_ticket_cycle",
            "zg361_b1_reopen_ticket_case",
            "zg361_b1_reopen_ticket_state",
            "zg361_b1_reopen_ticket_object",
            "zg361_b1_reopen_ticket_route",
            "zg361_b1_reopen_ticket_hash",
            "zg361_b1_reopen_ticket_reward_hash",
            "zg361_b1_reopen_ticket_book_version",
            "zg361_notice_prompt_owner",
            "zg361_notice_prompt_subject",
            "zg361_notice_prompt_cycle",
            "zg361_notice_prompt_case",
            "zg361_notice_prompt_state",
            "zg361_p2c_ticket_manager",
            "zg361_p2c_ticket_cycle",
            "zg361_p2c_ticket_case",
            "zg361_p2c_ticket_stage",
            "zg361_p2c_ticket_identity",
            "zg361_ch_d_event_owner",
            "zg361_ch_d_event_subject",
            "zg361_ch_d_event_cycle",
            "zg361_ch_d_event_case",
            "zg361_pp_subject_prompt_subject",
            "zg361_pp_subject_prompt_owner",
            "zg361_pp_subject_prompt_cycle",
            "zg361_pp_subject_prompt_case",
            "zg361_pp_subject_prompt_state",
            "zg361_cp_e_owner",
            "zg361_cp_e_subject",
            "zg361_cp_e_cycle",
            "zg361_cp_e_case",
            "zg361_p3_aa_owner",
            "zg361_p3_aa_subject",
            "zg361_p3_aa_cycle",
            "zg361_p3_aa_case",
        ),),
        "boolean_scopes": (),
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
}


__all__ = ["CAREER_LEARNING_TIMELINE_CONTRACTS"]
