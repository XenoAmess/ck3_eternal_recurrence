#!/usr/bin/env python3
"""Exact Phase 3 metrics-delivery AG interrupt contracts."""

from __future__ import annotations

from typing import Final


PHASE3_METRICS_DELIVERY_AG_SAVED_SCOPE_NAMES: Final = (
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
    "zg361_p3_ag_owner",
    "zg361_p3_ag_subject",
    "zg361_p3_ag_cycle",
    "zg361_p3_ag_case",
)

PHASE3_METRICS_DELIVERY_AG_CHARACTER_SCOPES: Final = {
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
    "zg361_p3_ag_owner": 32904,
    "zg361_p3_ag_subject": 26505,
}

PHASE3_METRICS_DELIVERY_AG_ITEMIZED_SCHEDULE: Final = (
    ("zg361p3.301", 53188056),
    ("zg361p3.302", 53188080),
    ("zg361p3.303", 53188104),
    ("zg361p3.304", 53188128),
    ("zg361p3.305", 53188152),
    ("zg361p3.306", 53188176),
    ("zg361p3.307", 53188200),
    ("zg361p3.308", 53188224),
    ("zg361p3.309", 53188248),
    ("zg361p3.310", 53188272),
    ("zg361p3.311", 53188296),
)

PHASE3_METRICS_DELIVERY_AG_STAGE_BARRIERS: Final = (
    (302, 1),
    (304, 2),
    (306, 3),
    (310, 4),
    (311, 5),
)

PHASE3_METRICS_DELIVERY_AG_ROUTE_VECTOR: Final = tuple(
    (event_key, 1, 0)
    for event_key, _date_raw in PHASE3_METRICS_DELIVERY_AG_ITEMIZED_SCHEDULE
)


def _itemized_contract(date_raw: int) -> dict[str, object]:
    return {
        "date_raw": date_raw,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": PHASE3_METRICS_DELIVERY_AG_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in PHASE3_METRICS_DELIVERY_AG_SAVED_SCOPE_NAMES
            if name not in PHASE3_METRICS_DELIVERY_AG_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            PHASE3_METRICS_DELIVERY_AG_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    }


PHASE3_METRICS_DELIVERY_AG_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    # .301 is frozen from the R242 live frame. The remaining dates are the
    # source-proven static schedule: every successful A route queues the next
    # visible card at D+1. No predicted contract binds a future instance ID.
    event_key: _itemized_contract(date_raw)
    for event_key, date_raw in PHASE3_METRICS_DELIVERY_AG_ITEMIZED_SCHEDULE
}
