"""Explicit control of retained Gathering research sampling.

These receipts describe capture state, not military readiness or a completed
natural Gathering phase. Ordinary Army queries never invoke these controls.
"""

from __future__ import annotations

ENABLE_STEP = "enable-army-gathering-research-sampling-v1"
DISABLE_STEP = "disable-army-gathering-research-sampling-v1"
QUERY_STEP = "query-army-gathering-research-sampling-v1"
STATE_KEY = "army_gathering_research_sampling_v1"

_STEPS = {ENABLE_STEP, DISABLE_STEP, QUERY_STEP}
_STATUS = {"enabled", "disabled", "busy", "clear_pending"}
_READINESS = {"off", "inflight", "awaiting_sample", "retained_observation"}
_STATE_KEYS = {
    "capture_enabled", "busy", "clear_completed", "epoch", "active_captures",
    "retained_records", "qualified_records", "readiness",
}


def normalize_army_gathering_research_sampling_result(
    payload: object, *, expected_step: str,
) -> dict[str, object]:
    """Retain the exact small Native state; never turn pending into success."""
    if type(expected_step) is not str or expected_step not in _STEPS:
        raise ValueError("unknown Gathering research sampling step")
    if not isinstance(payload, dict) or set(payload) != {
        "step", "accepted", "status", STATE_KEY, "backend_id",
    }:
        raise ValueError("malformed Gathering research sampling envelope")
    status = payload.get("status")
    if (
        payload.get("step") != expected_step
        or payload.get("backend_id") != "native-headless"
        or type(status) is not str or status not in _STATUS
        or type(payload.get("accepted")) is not bool
    ):
        raise ValueError("malformed Gathering research sampling status")
    expected_accepted = expected_step == QUERY_STEP or status in {"enabled", "disabled"}
    if payload["accepted"] is not expected_accepted:
        raise ValueError("Gathering sampling accepted disagrees with terminal state")
    state = payload.get(STATE_KEY)
    if not isinstance(state, dict) or set(state) != _STATE_KEYS:
        raise ValueError("malformed Gathering research sampling state")
    for key in ("capture_enabled", "busy", "clear_completed"):
        if type(state[key]) is not bool:
            raise ValueError(f"Gathering sampling {key} must be a boolean")
    for key in ("epoch", "active_captures", "retained_records", "qualified_records"):
        if type(state[key]) is not int or not 0 <= state[key] <= 2**64 - 1:
            raise ValueError(f"Gathering sampling {key} must be a uint64")
    if type(state["readiness"]) is not str or state["readiness"] not in _READINESS:
        raise ValueError("unknown Gathering sampling readiness")
    if not state["qualified_records"] <= state["retained_records"] <= 64:
        raise ValueError("Gathering records exceed their retained 64-record journal")
    if state["busy"] is not (state["active_captures"] > 0):
        raise ValueError("Gathering sampling busy disagrees with active captures")
    if state["clear_completed"] and (
        state["capture_enabled"] or state["active_captures"] != 0
        or state["retained_records"] != 0
    ):
        raise ValueError("Gathering sampling clear_completed contradicts retained state")
    observed_status = (
        "enabled" if state["capture_enabled"] else
        "busy" if state["busy"] else
        "disabled" if state["clear_completed"] else "clear_pending"
    )
    if status != observed_status:
        raise ValueError("Gathering sampling status contradicts actual capture state")
    observed_readiness = (
        "off" if not state["capture_enabled"] else
        "inflight" if state["busy"] else
        "awaiting_sample" if state["qualified_records"] == 0 else "retained_observation"
    )
    if state["readiness"] != observed_readiness:
        raise ValueError("Gathering sampling readiness contradicts actual capture state")
    if expected_step != QUERY_STEP and expected_accepted:
        enabled = expected_step == ENABLE_STEP
        if status != ("enabled" if enabled else "disabled"):
            raise ValueError("Gathering sampling state disagrees with requested control")
        if state["capture_enabled"] is not enabled:
            raise ValueError("Gathering sampling capture flag disagrees with accepted control")
        if not enabled and state["clear_completed"] is not True:
            raise ValueError("disabled Gathering sampling did not complete history clearing")
    return {**payload, STATE_KEY: dict(state)}
