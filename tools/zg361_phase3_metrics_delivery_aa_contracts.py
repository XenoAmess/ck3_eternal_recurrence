#!/usr/bin/env python3
"""Exact Phase 3 metrics-delivery AA interrupt contracts."""

from __future__ import annotations

from typing import Final


PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES: Final = (
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
    "zg361_p3_aa_owner",
    "zg361_p3_aa_subject",
    "zg361_p3_aa_cycle",
    "zg361_p3_aa_case",
)

PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES: Final = {
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
    "zg361_p3_aa_owner": 32904,
    "zg361_p3_aa_subject": 26505,
}

PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE: Final = (
    ("zg361p3.229", 53187744),
    ("zg361p3.230", 53187768),
    ("zg361p3.231", 53187792),
    ("zg361p3.232", 53187816),
    ("zg361p3.233", 53187840),
    ("zg361p3.234", 53187864),
    ("zg361p3.235", 53187888),
    ("zg361p3.236", 53187912),
    ("zg361p3.237", 53187936),
    ("zg361p3.240", 53187960),
    ("zg361p3.238", 53187984),
    ("zg361p3.239", 53188008),
    ("zg361p3.241", 53188032),
)

PHASE3_METRICS_DELIVERY_AA_STAGE_BARRIERS: Final = (
    (230, 1),
    (233, 2),
    (237, 3),
    (240, 4),
    (239, 5),
    (241, 6),
)

PHASE3_METRICS_DELIVERY_AA_ROUTE_VECTOR: Final = tuple(
    (event_key, 1, 0)
    for event_key, _date_raw in PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
)


def _itemized_contract(date_raw: int) -> dict[str, object]:
    return {
        "date_raw": date_raw,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES
            if name not in PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    }


PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "zg361p3.9000": {
        # R240 reached the Phase 3 portfolio-mode selector after R finalized.
        # A/B/C select frozen batch policies; D sets mode 4 and preserves the
        # original itemized 35-card route, beginning with .229 at D+1.
        "date_raw": 53187720,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES
            if name not in PHASE3_METRICS_DELIVERY_AA_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            PHASE3_METRICS_DELIVERY_AA_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 4,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    # .229 is frozen from the R241 live frame. The remaining dates are the
    # source-proven static schedule: itemized mode queues each next card at
    # D+1. They deliberately do not claim or bind future event instances.
    **{
        event_key: _itemized_contract(date_raw)
        for event_key, date_raw in PHASE3_METRICS_DELIVERY_AA_ITEMIZED_SCHEDULE
    },
}
