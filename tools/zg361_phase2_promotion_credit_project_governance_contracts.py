#!/usr/bin/env python3
"""Exact credit/project R-domain governance interrupt contracts."""

from __future__ import annotations

from typing import Final


_CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES: Final = (
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
    "zg361_cp_e_owner",
    "zg361_cp_e_subject",
    "zg361_cp_e_cross_reviewer",
    "zg361_cp_e_successor_manager",
    "zg361_cp_e_active_manager",
    "zg361_cp_e_historical_owner",
    "zg361_cp_e_cycle",
    "zg361_cp_e_case",
    "zg361_cp_i_owner",
    "zg361_cp_i_subject",
    "zg361_cp_i_cross_reviewer",
    "zg361_cp_i_successor_manager",
    "zg361_cp_i_active_manager",
    "zg361_cp_i_historical_owner",
    "zg361_cp_i_cycle",
    "zg361_cp_i_case",
    "zg361_cp_j_owner",
    "zg361_cp_j_subject",
    "zg361_cp_j_cross_reviewer",
    "zg361_cp_j_successor_manager",
    "zg361_cp_j_active_manager",
    "zg361_cp_j_historical_owner",
    "zg361_cp_j_cycle",
    "zg361_cp_j_case",
    "zg361_cp_r_owner",
    "zg361_cp_r_subject",
    "zg361_cp_r_cross_reviewer",
    "zg361_cp_r_successor_manager",
    "zg361_cp_r_active_manager",
    "zg361_cp_r_historical_owner",
    "zg361_cp_r_cycle",
    "zg361_cp_r_case",
)

_CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES: Final = {
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
    "zg361_ch_d_event_subject": 26505,
    "zg361_comp_result_subject_scope": 26347,
    "zg361_comp_open_subject": 26347,
    "zg361_cp_e_owner": 32904,
    "zg361_cp_e_subject": 26505,
    "zg361_cp_e_cross_reviewer": 27448,
    "zg361_cp_e_successor_manager": 32904,
    "zg361_cp_e_active_manager": 32904,
    "zg361_cp_e_historical_owner": 32904,
    "zg361_cp_i_owner": 32904,
    "zg361_cp_i_subject": 26505,
    "zg361_cp_i_cross_reviewer": 27448,
    "zg361_cp_i_successor_manager": 32904,
    "zg361_cp_i_active_manager": 32904,
    "zg361_cp_i_historical_owner": 32904,
    "zg361_cp_j_owner": 32904,
    "zg361_cp_j_subject": 26505,
    "zg361_cp_j_cross_reviewer": 27448,
    "zg361_cp_j_successor_manager": 32904,
    "zg361_cp_j_active_manager": 32904,
    "zg361_cp_j_historical_owner": 32904,
    "zg361_cp_r_owner": 32904,
    "zg361_cp_r_subject": 26505,
    "zg361_cp_r_cross_reviewer": 27448,
    "zg361_cp_r_successor_manager": 32904,
    "zg361_cp_r_active_manager": 32904,
    "zg361_cp_r_historical_owner": 32904,
}


CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361cp.131": {
        # R234 opened R-domain project-track governance. Routes A/B have the
        # same resource footprint and both preserve registry ownership on the
        # project winner plus metric ownership on the subject. A records track
        # 1, B records track 2, while C opens defer/debt. Choose A as the
        # deterministic minimum; it advances R 1 -> 2 and schedules .129 D+1.
        "date_raw": 53187528,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361cp.129": {
        # R235 reached the promotion queue. Route A queues the subject without
        # awarding a promotion or changing the free/used slot counters; route
        # B consumes a free slot and awards immediately, while C opens debt.
        # Choose A to preserve capacity. R remains at state 2 and hidden .9334
        # restores visible .134 D+1.
        "date_raw": 53187552,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361cp.134": {
        # R236 reached shared-metric ownership. Routes A/B share the same
        # resource footprint, contributor subject and cross-review dependency;
        # A keeps the sole metric owner on the subject, while B assigns it to
        # the manager. C opens defer/debt. Choose A to preserve subject
        # ownership; it advances R 2 -> 3 and schedules .130 D+1.
        "date_raw": 53187576,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_GOVERNANCE_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_GOVERNANCE_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
