"""Explicit campaign trial for the existing proof-bound exact route day only."""
from __future__ import annotations

from dataclasses import dataclass


SCHEMA = "xar.ck3.contact-free-exact-route-speed-trial/v1"
SCOPE = "contact_free_typed_route_exact_one_day"


@dataclass(frozen=True)
class _Trial:
    campaign_id: str
    trial_id: str
    start_date_raw: int
    endpoint_date_raw: int
    speed: int = 5


def _baseline(driver) -> None:
    if (type(getattr(driver, "route_contact_timeline_speed", None)) is not int
            or driver.route_contact_timeline_speed != 3
            or getattr(driver, "route_contact_effective_timeline_speed", None) != 3
            or getattr(driver, "allow_route_contact_high_speed_ab", None) is not False):
        raise ValueError("route-only speed trial requires global route speed3 and high-speed A/B false")


def _campaign(driver, campaign_id: str) -> dict:
    value = getattr(driver, "_campaign_clock_deadline_v1", None)
    if (not isinstance(value, dict)
            or value.get("schema") != "xar.ck3.campaign-clock-deadline/v1"
            or value.get("campaign_id") != campaign_id
            or type(value.get("start_date_raw")) is not int
            or type(value.get("endpoint_date_raw")) is not int):
        raise ValueError("route-only speed trial requires the same explicitly configured campaign deadline")
    return value


def _description(trial: _Trial) -> dict:
    return {"schema": SCHEMA, "scope": SCOPE, "campaign_id": trial.campaign_id,
            "trial_id": trial.trial_id, "requested_speed": trial.speed,
            "qualification_status": "controlled_trial_pending_live", "live_ready": False,
            "attempt_limit": 1,
            "global_route_speed": 3, "global_high_speed_ab": False,
            "native_army_watch_claimed": False, "policy_choices_changed": False}


def configure_v1(driver, *, campaign_id: str, trial_id: str, speed: int = 5) -> dict:
    """Configure once without a native call or any production-ready claim."""
    if (type(speed) is not int or speed != 5
            or not isinstance(campaign_id, str) or not campaign_id.strip()
            or not isinstance(trial_id, str) or not trial_id.strip()
            or len(trial_id) > 160):
        raise ValueError("route-only trial needs explicit campaign/trial identities and speed5")
    _baseline(driver)
    campaign = _campaign(driver, campaign_id)
    trial = _Trial(campaign_id, trial_id, campaign["start_date_raw"], campaign["endpoint_date_raw"])
    previous = getattr(driver, "_contact_free_exact_route_speed_trial_v1", None)
    if previous is not None and previous != trial:
        raise ValueError("a driver cannot replace its route-only trial identity")
    if previous is None:
        driver._contact_free_exact_route_speed_trial_consumed_v1 = False
    driver._contact_free_exact_route_speed_trial_v1 = trial
    return _description(trial)


def select_v1(driver, starting: dict, proof: dict, *, fallback_speed: int) -> dict | None:
    """Called only after the existing complete same-frame proof validation."""
    trial = getattr(driver, "_contact_free_exact_route_speed_trial_v1", None)
    if trial is None:
        return None
    if type(trial) is not _Trial:
        raise ValueError("route-only trial configuration is not the explicit validated type")
    _baseline(driver)
    campaign = _campaign(driver, trial.campaign_id)
    if (campaign["start_date_raw"], campaign["endpoint_date_raw"]) != (
            trial.start_date_raw, trial.endpoint_date_raw):
        raise ValueError("route-only trial campaign date identity changed")

    selected, status = fallback_speed, "not_contact_free"
    if proof.get("proof_kind") == "contact_free":
        from . import native_driver as n
        capabilities = driver.state.capabilities()
        native = set(capabilities.get("bridge_capabilities", ()))
        steps = set(capabilities.get("action_steps", ()))
        required = n._TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES | {
            n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY, n.QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY}
        hint = starting.get("top_exclusive_modal_choice_hint")
        if getattr(driver, "_contact_free_exact_route_speed_trial_consumed_v1", None) is not False:
            status = "controlled_trial_attempt_exhausted"
        elif type(starting.get("date_raw")) is int and starting["date_raw"] >= trial.endpoint_date_raw:
            status = "campaign_endpoint_reached"
        elif not required <= native or not {"set-speed-5", "resume-map", "pause-map"} <= steps:
            status = "native_clock_or_speed_capability_missing"
        elif (starting.get("paused") is not True or starting.get("map_ready") is not True
                or starting.get("active_event") is not None
                or starting.get("pending_character_interaction") is not None
                or isinstance(hint, dict) and hint.get("status") == "present"):
            status = "player_decision_or_map_boundary"
        else:
            selected, status = trial.speed, "selected_controlled_trial"
            # Consume before any setter/Arm/resume. Unknown or failed actions
            # must never cause another high-speed attempt or token replay.
            driver._contact_free_exact_route_speed_trial_consumed_v1 = True
    diagnostics = starting.get("diagnostics")
    return {**_description(trial), "selection_status": status, "selected_speed": selected,
            "attempt_ordinal": 1 if status == "selected_controlled_trial" else None,
            "attempts_used": int(driver._contact_free_exact_route_speed_trial_consumed_v1 is True),
            "proof_kind": proof.get("proof_kind"), "subject_army_id": proof.get("subject_army_id"),
            "target_province_id": proof.get("target_province_id"),
            "hostile_army_ids": list(proof.get("hostile_army_ids", ())),
            "source_snapshot_id": starting.get("snapshot_id"),
            "source_revision": starting.get("revision"), "source_native_revision": starting.get("native_revision"),
            "source_date_raw": starting.get("date_raw"), "source_episode_run_id": starting.get("episode_run_id"),
            "source_connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None}


def receipt_v1(selection: dict, result: dict) -> dict:
    """Record the actual existing clock result; never grant independent credit."""
    return {**selection, "actual_timeline_speed": result.get("timeline_speed"),
            "actual_elapsed_days": result.get("elapsed_days"),
            "actual_progress_status": result.get("progress_status"),
            "exact_day_native_clock_present": isinstance(result.get("exact_day_native_clock"), dict),
            "calendar_or_business_credit_inferred": False}
