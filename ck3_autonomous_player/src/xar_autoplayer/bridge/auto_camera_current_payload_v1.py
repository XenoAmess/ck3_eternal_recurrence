"""Project post-business camera input from one existing semantic publication."""
from __future__ import annotations

from collections.abc import Mapping


def current_camera_payload_v1(service: object, planned: Mapping,
                              outcome: Mapping) -> dict:
    """Read the local cache once; never attach a new date to old army data."""
    before = planned.get("planning_source_frame")
    if not isinstance(before, Mapping) or before.get("status") != "complete":
        raise ValueError("camera current cache lacks a complete planning identity")
    reader = getattr(getattr(service, "driver", None),
                     "take_internal_semantic_snapshot", None)
    if not callable(reader):
        raise ValueError("camera current semantic cache reader unavailable")
    snapshot = reader()
    if not isinstance(snapshot, dict):
        raise ValueError("camera current semantic cache unavailable")
    frame = getattr(service, "_observed_planning_source_frame")(snapshot)
    if frame.get("status") != "complete":
        raise ValueError("camera current semantic cache frame incomplete")
    for key in ("actor_character_id", "episode_run_id", "bridge_pid",
                "connection_generation"):
        if frame.get(key) != before.get(key):
            raise ValueError("camera current cache owner changed")
    if (type(frame.get("bridge_pid")) is not int or frame["bridge_pid"] <= 0):
        raise ValueError("camera current cache Game identity unavailable")
    if any(frame[key] < before[key]
           for key in ("date_raw", "revision", "native_revision")):
        raise ValueError("camera current semantic cache regressed")
    result = outcome.get("result")
    ending_date = result.get("ending_date_raw") if isinstance(result, Mapping) else None
    if ending_date is not None and (
            type(ending_date) is not int or frame["date_raw"] < ending_date):
        raise ValueError("camera current semantic cache predates action end")
    played = snapshot.get("played_character")
    if (snapshot.get("map_ready") is not True or not isinstance(played, Mapping)
            or played.get("alive") is not True):
        raise ValueError("camera current playable map unavailable")
    return getattr(service, "_auto_camera_hotspot_input")(snapshot, frame)
