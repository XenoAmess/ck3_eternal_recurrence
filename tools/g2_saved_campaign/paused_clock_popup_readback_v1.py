"""UI readback shape only; callers must separately verify the original clock.

True does not prove event readiness, resolution, safe contact or business credit.
The next ordinary policy must query and handle the retained popup independently.
"""


def paused_clock_popup_readback_v1(inner):
    if (not isinstance(inner, dict) or inner.get("paused") is not True
            or inner.get("ordinary_events") != []):
        return False
    event = inner.get("active_event")
    pending = inner.get("pending_character_interaction")
    event_valid = (isinstance(event, dict)
                   and type(event.get("instance_id")) is int
                   and event["instance_id"] > 0
                   and type(event.get("option_count")) is int
                   and event["option_count"] > 0)
    pending_valid = isinstance(pending, dict) and bool(pending)
    popup = event_valid or pending_valid
    return ((event is None or event_valid) and (pending is None or pending_valid)
            and inner.get("final_screen") == (None if popup else "map_hud")
            and inner.get("event_resolution") == ("typed_query_required" if event_valid else "none"))
