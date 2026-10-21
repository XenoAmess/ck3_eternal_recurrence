"""Strictly retain a native pause/resume ACK's original protocol request ID.

The binding is diagnostic only. Existing accepted/status and state checks remain
owned by the driver; an ACK does not establish observed execution or completion.
"""
from __future__ import annotations

from typing import TypedDict


class TimelineControlAckBindingV1(TypedDict):
    native_request_id: str


def _field(source: object, key: str) -> object:
    # JSON values leave this untrusted boundary as object, never unchecked Any.
    if type(source) is dict:
        value: object = source.get(key)
        return value
    return None


def normalize_timeline_control_ack_v1(
    frame: object, *, expected_step: str, expected_request_id: str,
) -> TimelineControlAckBindingV1:
    """Bind the success envelope without reinterpreting its action result."""
    if type(expected_request_id) is not str or not expected_request_id:
        raise ValueError("timeline control expected request_id must be a non-empty string")
    if type(expected_step) is not str or expected_step not in {"pause-map", "resume-map"}:
        raise ValueError("timeline control ACK requires pause-map or resume-map")
    protocol = _field(frame, "protocol_version")
    request_id = _field(frame, "request_id")
    frame_type = _field(frame, "type")
    if (type(frame) is not dict or type(frame_type) is not str or frame_type != "command_result"
            or type(protocol) is not int or protocol != 1
            or type(request_id) is not str or request_id != expected_request_id
            or _field(frame, "ok") is not True):
        raise ValueError("timeline control ACK envelope does not match its original request")
    result = _field(frame, "result")
    step = _field(result, "step")
    if (type(result) is not dict or type(step) is not str or step != expected_step
            or "request_id" in result or "native_request_id" in result):
        raise ValueError("timeline control ACK result has invalid step or identity aliases")
    return TimelineControlAckBindingV1(native_request_id=request_id)
