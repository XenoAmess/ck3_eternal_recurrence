"""Ordinary AUTO presentation at the existing validated tactical resume point."""
from contextlib import contextmanager

from .native_driver import NativeHeadlessGameplayDriver
from .realm_overview_camera import EXACT_SHA
from .war_hotspot_camera import LandedProvinceIndex, select_war_hotspot


_HOOK = "_ordinary_auto_camera_pre_resume_v1"
_OWNER = ("actor_character_id", "episode_run_id", "bridge_pid", "connection_generation")


@contextmanager
def camera_pre_advance_scope_v1(service, planned):
    """Install one callback only during this ordinary AUTO dispatch; never read."""
    driver = service.driver
    missing = object()
    previous = getattr(driver, _HOOK, missing)
    if (type(driver) is not NativeHeadlessGameplayDriver
            or previous is not missing and previous is not None):
        yield
        return
    used = False

    def before_resume(*, step, current):
        nonlocal used
        receipt = {"schema": "xar.ck3.auto-camera-pre-advance/v1",
                   "status": "skipped", "reason": "unverified_current_frame",
                   "step": step, "new_game_queries": 0,
                   "same_frame_with_gameplay_claim": False}
        if used:
            return {**receipt, "reason": "already_observed_resume_point"}
        used = True
        planning = planned.get("planning_source_frame")
        if not isinstance(planning, dict) or not isinstance(current, dict):
            return receipt
        frame = service._observed_planning_source_frame(current)
        if (planning.get("status") != "complete" or frame.get("status") != "complete"
                or any(frame.get(k) != planning.get(k) for k in _OWNER)
                or type(frame.get("bridge_pid")) is not int or frame["bridge_pid"] <= 0
                or frame.get("date_raw") != planning.get("date_raw")
                or any(type(planning.get(k)) is not int or frame[k] < planning[k]
                       for k in ("revision", "native_revision"))
                or current.get("paused") is not True
                or (current.get("played_character") or {}).get("alive") is not True):
            return receipt
        # Project the actual already captured current snapshot. Never relabel
        # an old planning position with the newer frame/date.
        payload = service._auto_camera_hotspot_input(current, frame)
        if (payload.get("map_ready") is not True or payload.get("mandatory_choice") is True
                or payload.get("has_active_event") is True
                or payload.get("has_pending_interaction") is True):
            return {**receipt, "reason": "mandatory_or_map_unavailable"}
        source = payload["source_build"]
        if (source.get("game_version") != "1.20.0.4"
                or str(source.get("executable_sha256", "")).upper() != EXACT_SHA):
            return {**receipt, "reason": "camera_build_unverified"}
        index = service._war_hotspot_camera_index
        if not isinstance(index, LandedProvinceIndex):
            return {**receipt, "reason": "landed_index_not_already_bound"}
        hotspot = select_war_hotspot({"active_wars": payload["active_wars"]}, index)
        if hotspot is None or hotspot.get("reason") not in {
                "battle", "moving_player_army", "army_destination"}:
            return {**receipt, "reason": "no_known_active_hotspot"}
        scheduled = service._auto_camera_worker.schedule(payload, urgent=True)
        return {**receipt, "status": scheduled.get("status", "unavailable"),
                "reason": "validated_tactical_pre_resume", "source_frame": frame,
                "planning_source_frame": dict(planning), "hotspot": hotspot,
                "camera_schedule": scheduled}

    setattr(driver, _HOOK, before_resume)
    try:
        yield
    finally:
        if previous is missing:
            delattr(driver, _HOOK)
        else:
            setattr(driver, _HOOK, previous)
