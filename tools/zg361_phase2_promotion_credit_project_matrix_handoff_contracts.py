#!/usr/bin/env python3
"""Exact credit/project J-domain matrix/handoff interrupt contracts."""

from __future__ import annotations

from typing import Final


_CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES: Final = (
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
)

_CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES: Final = {
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
}


CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361cp.63": {
        # R226 opened the J-domain matrix tree. Route A locks 70/30
        # solid/dotted weights, while B locks 50/50 and C opens defer/debt.
        # A/B both retain total weight 100, advance J state 1 -> 2, and use
        # hidden .9262 D+1 to restore .62. A keeps the higher solid weight
        # needed by the following recorded-choice branch and preserves J.
        "date_raw": 53187360,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361cp.62": {
        # R227 reached the recorded matrix choice. Route A records chosen
        # route 1 with zero integrity delta; B records joint route 3 and adds
        # one integrity, while C opens defer/debt. A/B both consume the write,
        # increment the project version, retain J state 2, and use hidden
        # .9265 D+1 to continue to .65. A has the fewest additional writes.
        "date_raw": 53187384,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361cp.65": {
        # R228 reached parachute staffing. Route A keeps team size 10 while
        # importing two staff, retaining eight memory, and adding no audit;
        # B imports three, retains seven, and adds an audit, while C opens
        # defer/debt. A/B both consume the write, increment project version,
        # advance J state 2 -> 3, and schedule .64 D+1. A is least disruptive.
        "date_raw": 53187408,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361cp.64": {
        # R229 reached manager handoff. Route A records both managers,
        # finalizes the handoff, and irreversibly changes active_manager to
        # the successor. Route B records only the old manager, keeps the new
        # manager unrecorded and the handoff pending, and does not migrate
        # active_manager; C opens defer/debt. B advances J 3 -> 4 and .66 D+1.
        "date_raw": 53187432,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "zg361cp.66": {
        # R230 reached strategic cancellation. Route A immediately releases
        # the remaining capacity and closes the project. Route B records the
        # cancellation as pending while preserving the active project and its
        # remaining capacity for the later .132 release; C opens defer/debt.
        # All successful routes keep J state 4 and schedule .67 D+1. B makes
        # the smallest persistent change while retaining the full-tree state.
        "date_raw": 53187456,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES
            if name not in _CREDIT_PROJECT_MATRIX_HANDOFF_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            _CREDIT_PROJECT_MATRIX_HANDOFF_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
}
