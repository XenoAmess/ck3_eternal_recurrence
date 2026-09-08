#!/usr/bin/env python3
"""Source-reviewed player-manager elimination interrupt contracts."""

from __future__ import annotations

from typing import Final


_ZG361_5_SAVED_SCOPE_NAMES: Final = (
    "zg361_b1_calibration_watchdog_owner",
    "zg361_b1_calibration_watchdog_cycle",
    "zg361_b1_calibration_watchdog_case",
    "zg361_b1_oversight_ticket_owner",
    "zg361_b1_oversight_ticket_cycle",
    "zg361_b1_oversight_ticket_case",
    "zg361_b1_oversight_ticket_state",
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
    "zg361_b2_pip_review_candidate",
    "zg361_b2_support_mentor",
    "zg361_b2_pip_deadline_owner",
    "zg361_b2_pip_deadline_subject",
    "zg361_b2_pip_deadline_cycle",
    "zg361_b2_pip_deadline_case",
    "zg361_b2_pip_deadline_state",
    "zg361_notice_deadline_owner",
    "zg361_notice_deadline_subject",
    "zg361_notice_deadline_cycle",
    "zg361_notice_deadline_case",
    "zg361_notice_deadline_state",
    "zg361_p2c_ticket_manager",
    "zg361_p2c_ticket_cycle",
    "zg361_p2c_ticket_case",
    "zg361_p2c_ticket_stage",
    "zg361_p2c_ticket_identity",
    "zg361_ch_d_event_owner",
    "zg361_ch_d_event_subject",
    "zg361_ch_d_event_cycle",
    "zg361_ch_d_event_case",
    "zg361_comp_result_subject_scope",
    "zg361_comp_open_subject",
    "zg361_p2c_summary_cycle",
    "zg361_p2c_summary_case",
    "zg361_n_elim",
)

_ZG361_5_R293_SAVED_SCOPE_NAMES: Final = (
    *_ZG361_5_SAVED_SCOPE_NAMES[:-1],
    "zg361_cp_e_owner",
    "zg361_cp_e_subject",
    "zg361_cp_e_cross_reviewer",
    "zg361_cp_e_successor_manager",
    "zg361_cp_e_active_manager",
    "zg361_cp_e_historical_owner",
    "zg361_cp_e_cycle",
    "zg361_cp_e_case",
    "zg361_p3_aa_owner",
    "zg361_p3_aa_subject",
    "zg361_p3_aa_cycle",
    "zg361_p3_aa_case",
    "zg361_n_elim",
)

_ZG361_5_R293_CHARACTER_SCOPES: Final = {
    "zg361_b1_calibration_watchdog_owner": 32904,
    "zg361_b1_oversight_ticket_owner": 32904,
    "zg361_b1_reopen_ticket_subject": 45031,
    "zg361_b1_reopen_ticket_owner": 32904,
    "zg361_b2_pip_review_candidate": 27448,
    "zg361_b2_pip_deadline_owner": 32904,
    "zg361_notice_deadline_owner": 32904,
    "zg361_p2c_ticket_manager": 32904,
    "zg361_ch_d_event_owner": 32904,
    "zg361_ch_d_event_subject": 26505,
    "zg361_comp_result_subject_scope": 26347,
    "zg361_comp_open_subject": 26347,
    "zg361_cp_e_owner": 32904,
    "zg361_cp_e_subject": 26505,
    "zg361_cp_e_cross_reviewer": 27448,
    "zg361_cp_e_successor_manager": 32904,
    "zg361_cp_e_active_manager": 32904,
    "zg361_cp_e_historical_owner": 32904,
    "zg361_p3_aa_owner": 32904,
    "zg361_p3_aa_subject": 26505,
}

_ZG361_5_R293_DYNAMIC_CHARACTER_SCOPE_NAMES: Final = (
    "zg361_b2_support_mentor",
    "zg361_b2_pip_deadline_subject",
    "zg361_notice_deadline_subject",
)


MANAGER_ELIMINATION_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361.5": {
        # R204 reached the player-liege batch-elimination window after manager
        # recovery. The event itself saves and renders zg361_n_elim; all other
        # names are inherited outer product state. Bind the complete observed
        # set and exact character aliases before choosing the least destructive
        # authored route: extend streak<3 candidates and demote only the rest.
        "date_raw": 53186136,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "zg361_b1_calibration_watchdog_owner": 32904,
            "zg361_b1_oversight_ticket_owner": 32904,
            "zg361_b1_reopen_ticket_subject": 45031,
            "zg361_b1_reopen_ticket_owner": 32904,
            "zg361_b2_pip_review_candidate": 27448,
            "zg361_b2_support_mentor": 30434,
            "zg361_b2_pip_deadline_owner": 32904,
            "zg361_b2_pip_deadline_subject": 28667,
            "zg361_notice_deadline_owner": 32904,
            "zg361_notice_deadline_subject": 28667,
            "zg361_p2c_ticket_manager": 32904,
            "zg361_ch_d_event_owner": 32904,
            "zg361_ch_d_event_subject": 26347,
            "zg361_comp_result_subject_scope": 26347,
            "zg361_comp_open_subject": 26347,
        },
        "scope_types": {
            name: "value"
            for name in _ZG361_5_SAVED_SCOPE_NAMES
            if name not in {
                "zg361_b1_calibration_watchdog_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_reopen_ticket_subject",
                "zg361_b1_reopen_ticket_owner",
                "zg361_b2_pip_review_candidate",
                "zg361_b2_support_mentor",
                "zg361_b2_pip_deadline_owner",
                "zg361_b2_pip_deadline_subject",
                "zg361_notice_deadline_owner",
                "zg361_notice_deadline_subject",
                "zg361_p2c_ticket_manager",
                "zg361_ch_d_event_owner",
                "zg361_ch_d_event_subject",
                "zg361_comp_result_subject_scope",
                "zg361_comp_open_subject",
            }
        },
        "saved_scope_name_sets": (_ZG361_5_SAVED_SCOPE_NAMES,),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "scope_variants": ({
            # R293 reached the same visible elimination event after the
            # current B1 publication also left a career-project handoff and
            # Phase3 AA tuple in outer event state. The event-owned
            # zg361_n_elim value remains the final scope and the option shape
            # is unchanged. Bind every inherited alias and the current live
            # subject identities instead of weakening the older R204 shape.
            "saved_scope_names": _ZG361_5_R293_SAVED_SCOPE_NAMES,
            "character_scopes": _ZG361_5_R293_CHARACTER_SCOPES,
            "scope_types": {
                name: "value"
                for name in _ZG361_5_R293_SAVED_SCOPE_NAMES
                if name not in _ZG361_5_R293_CHARACTER_SCOPES
                and name not in _ZG361_5_R293_DYNAMIC_CHARACTER_SCOPE_NAMES
            },
            "unique_character_scope_excludes": {
                name: (32904,)
                for name in _ZG361_5_R293_DYNAMIC_CHARACTER_SCOPE_NAMES
            },
            # PIP and result-notice deadlines are independently scheduled for
            # the subject active in each source effect. R293 happened to carry
            # the same subject in both tokens; R351 proved the legal distinct
            # shape. The support mentor belongs only to the PIP token and must
            # differ from that PIP subject, not an unrelated notice subject.
            "character_scope_matches_any": {
                "zg361_ch_d_event_subject": (
                    "zg361_cp_e_subject",
                    "zg361_p3_aa_subject",
                ),
                "zg361_cp_e_subject": (
                    "zg361_ch_d_event_subject",
                    "zg361_p3_aa_subject",
                ),
                "zg361_p3_aa_subject": (
                    "zg361_ch_d_event_subject",
                    "zg361_cp_e_subject",
                ),
                "zg361_comp_result_subject_scope": (
                    "zg361_comp_open_subject",
                ),
                "zg361_comp_open_subject": (
                    "zg361_comp_result_subject_scope",
                ),
            },
            "character_scope_differs_from": {
                "zg361_b2_support_mentor": (
                    "zg361_b2_pip_deadline_subject",
                ),
            },
        },),
    },
    "zg361.6": {
        # Player-only last elimination appeal. Option 1 is only a 40% chance to
        # retain the career and therefore cannot be a production-path action.
        # Keep the modal open and advance the same CK3 process until authored
        # option 2 (300 gold, deterministic demotion/retention) is enabled.
        # This trigger and choice read character state, not saved scopes. R110
        # observed the completed self-review and shadow-response tickets on
        # this descendant frame, while the older bank ticket had expired; bind
        # those 48 inherited names as the exact current product-window set.
        "date_raw": 53159136,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "saved_scope_name_sets": ((
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
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
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
            "zg361_reviewing_superior",
            "zg361_notice_kpi",
            "zg361_notice_rank",
            "zg361_notice_cohort",
            "zg361_notice_absolute_grade",
            "zg361_notice_deadline_owner",
            "zg361_notice_deadline_subject",
            "zg361_notice_deadline_cycle",
            "zg361_notice_deadline_case",
            "zg361_notice_deadline_state",
        ),),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (0, 2),
                "selection_deferred": True,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 2),
            },
        ),
    },
}
