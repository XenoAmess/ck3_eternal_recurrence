#!/usr/bin/env python3
"""Exact credit/project resource-race timeline interrupt contracts."""

from __future__ import annotations

from typing import Final


_CREDIT_PROJECT_RESOURCE_RACE_SAVED_SCOPE_NAMES: Final = (
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
)

_CREDIT_PROJECT_RESOURCE_RACE_CHARACTER_SCOPES: Final = {
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
}


CREDIT_PROJECT_RESOURCE_RACE_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361cp.30": {
        # R212 reached the first itemized credit/project decision. Route A
        # reserves 40 hours for the subject-led project; route B reserves 60
        # for the cross-department project. Route C creates portfolio-wide
        # defer/debt and disables later itemized A/B business routes. Route A
        # is the smallest deterministic mutation that preserves full-tree.
        "date_raw": 53187024,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_RESOURCE_RACE_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_RESOURCE_RACE_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_RESOURCE_RACE_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_RESOURCE_RACE_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
