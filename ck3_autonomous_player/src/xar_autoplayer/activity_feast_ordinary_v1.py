"""Connect ordinary Feast configuration to the existing typed stock primitives."""

from __future__ import annotations

OPEN_STEP = "open-activity-feast-planner-v1-private"


def configure_feast_ordinary_v1(driver, service, *, province_id: int) -> dict[str, object]:
    # Import at execution time: native_auto_run constructs GameplayBridgeService.
    # These helpers retain their exact native receipts and existing same-frame
    # postconditions; this route does not synthesize a planner or Confirm receipt.
    from .native_auto_run import (
        _compact_binding, _open_private_activity_feast_planner_once,
        _read_private_activity_feast_stage1_option_once,
        _confirm_private_activity_feast_stage1_once,
        _read_private_activity_feast_stage2_option_once,
        _read_private_activity_feast_stage2_location_once,
        _select_private_activity_feast_stage2_destination_once,
    )

    before = _compact_binding(driver.capabilities(), service.snapshot())
    common = {"service": service, "before": before, "turn_index": 0}
    opened = _open_private_activity_feast_planner_once(driver, **common)
    option = _read_private_activity_feast_stage1_option_once(
        driver, open_observation=opened, **common)
    if option["selected_option"]["generic_feast_confirm_ready"] is not True:
        return {"step": OPEN_STEP, "status": "configuration_held",
                "accepted": False, "postcondition_verified": False,
                "no_activity_started": True, "open": opened, "stage1_option": option}
    confirmed = _confirm_private_activity_feast_stage1_once(
        driver, option_observation=option, **common)
    stage2 = _read_private_activity_feast_stage2_option_once(
        driver, confirm_observation=confirmed, **common)
    location = _read_private_activity_feast_stage2_location_once(
        driver, confirm_observation=confirmed, option_observation=stage2,
        candidate_province_ids=(province_id,), **common)
    if not any(row["province_id"] == province_id and row["can_select"] is True
               for row in location["location"]["candidates"]):
        return {"step": OPEN_STEP, "status": "configuration_held",
                "accepted": False, "postcondition_verified": False,
                "no_activity_started": True, "open": opened, "stage1_option": option,
                "stage1_confirm": confirmed, "stage2_option": stage2, "location": location}
    destination = _select_private_activity_feast_stage2_destination_once(
        driver, location_observation=location, province_id=province_id, **common)
    return {"step": OPEN_STEP, "status": "configured_stage_five",
            "accepted": True, "postcondition_verified": True,
            "no_activity_started": True, "open": opened, "stage1_option": option,
            "stage1_confirm": confirmed, "stage2_option": stage2,
            "location": location, "destination": destination}
