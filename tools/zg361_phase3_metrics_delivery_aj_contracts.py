#!/usr/bin/env python3
"""Exact Phase 3 metrics-delivery AJ interrupt contracts."""

from __future__ import annotations

from typing import Final


PHASE3_METRICS_DELIVERY_AJ_SAVED_SCOPE_NAMES: Final = (
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
    "zg361_p3_aj_owner",
    "zg361_p3_aj_subject",
    "zg361_p3_aj_cycle",
    "zg361_p3_aj_case",
)

PHASE3_METRICS_DELIVERY_AJ_CHARACTER_SCOPES: Final = {
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
    "zg361_p3_aj_owner": 32904,
    "zg361_p3_aj_subject": 26505,
}

PHASE3_METRICS_DELIVERY_AJ_ITEMIZED_SCHEDULE: Final = (
    ("zg361p3.334", 53188320),
    ("zg361p3.335", 53188344),
    ("zg361p3.336", 53188368),
    ("zg361p3.338", 53188392),
    ("zg361p3.339", 53188416),
    ("zg361p3.340", 53188440),
    ("zg361p3.342", 53188464),
    ("zg361p3.337", 53188488),
    ("zg361p3.341", 53188512),
    ("zg361p3.343", 53188536),
    ("zg361p3.344", 53188560),
)

PHASE3_METRICS_DELIVERY_AJ_STAGE_BARRIERS: Final = (
    (335, 1),
    (338, 2),
    (339, 3),
    (342, 4),
    (341, 5),
    (343, 6),
    (344, 7),
)

PHASE3_METRICS_DELIVERY_AJ_ROUTE_VECTOR: Final = tuple(
    (event_key, 2, 1) if event_key == "zg361p3.336" else (event_key, 1, 0)
    for event_key, _date_raw in PHASE3_METRICS_DELIVERY_AJ_ITEMIZED_SCHEDULE
)


def _itemized_contract(
    date_raw: int,
    selected_option_number: int,
    selected_native_option_index: int,
) -> dict[str, object]:
    return {
        "date_raw": date_raw,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": PHASE3_METRICS_DELIVERY_AJ_CHARACTER_SCOPES,
        "scope_types": {
            name: "value"
            for name in PHASE3_METRICS_DELIVERY_AJ_SAVED_SCOPE_NAMES
            if name not in PHASE3_METRICS_DELIVERY_AJ_CHARACTER_SCOPES
        },
        "saved_scope_name_sets": (
            PHASE3_METRICS_DELIVERY_AJ_SAVED_SCOPE_NAMES,
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": selected_option_number,
        "selected_native_option_index": selected_native_option_index,
    }


PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    # .334 is frozen from the R243 live frame. The remaining dates are the
    # source-proven static D+1 schedule and bind no predicted instance ID.
    event_key: _itemized_contract(date_raw, option_number, native_index)
    for (event_key, date_raw), (
        route_event_key,
        option_number,
        native_index,
    ) in zip(
        PHASE3_METRICS_DELIVERY_AJ_ITEMIZED_SCHEDULE,
        PHASE3_METRICS_DELIVERY_AJ_ROUTE_VECTOR,
        strict=True,
    )
    if event_key == route_event_key
}
