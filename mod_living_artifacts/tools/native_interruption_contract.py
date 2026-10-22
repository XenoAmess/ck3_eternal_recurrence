"""One Root interruption response, including the public checkpoint envelope."""
from __future__ import annotations

from typing import Literal, TypedDict

from acceptance_contract import Pin, field, integer, mapping, require, text


class NativeInterruptionRequest(TypedDict):
    schema: Literal["living-artifacts-native-interruption-request-v1"]
    run_id: str
    machine_id: str
    kind: Literal["event", "interaction"]
    instance_id: int
    date_raw: int
    original_native_frame_record: Pin
    existing_specialist_policy_priority: Literal[True]
    unknown_event_first_displayed_or_interaction_legal_left: Literal[True]
    no_replay_of_unknown: Literal[True]


class CompletedInterruptionResponse(TypedDict):
    schema: Literal["living-artifacts-native-interruption-result-v1"]
    run_id: str
    machine_id: str
    reviewer: str
    kind: Literal["event", "interaction"]
    instance_id: int
    date_raw: int
    native_interruption_continued: Literal[True]
    original_instance_independently_absent: Literal[True]


def completed_interruption_response(request: object, *, reviewer: str) -> CompletedInterruptionResponse:
    """Encode a completed review; the caller retains actual action/absence proof."""
    require(field(request, "schema") == "living-artifacts-native-interruption-request-v1", "Interruption request schema differs")
    kind = field(request, "kind")
    if kind not in ("event", "interaction"):
        raise ValueError("Interruption kind must be event or interaction")
    # Explicit branches narrow the validated runtime string for the field model.
    selected: Literal["event", "interaction"] = "event" if kind == "event" else "interaction"
    return {
        "schema": "living-artifacts-native-interruption-result-v1",
        "run_id": text(field(request, "run_id"), "run ID"),
        "machine_id": text(field(request, "machine_id"), "machine ID"),
        "reviewer": text(reviewer, "Root reviewer"), "kind": selected,
        "instance_id": integer(field(request, "instance_id"), "interruption instance", 1, 2**32 - 1),
        "date_raw": integer(field(request, "date_raw"), "paused game date", 1),
        "native_interruption_continued": True, "original_instance_independently_absent": True,
    }


def parse_completed_interruption(value: object, *, request: NativeInterruptionRequest, reviewer: str) -> CompletedInterruptionResponse:
    """Reject missing envelope/identity fields, extra keys and false-equal IDs."""
    row = mapping(value, "completed native interruption")
    require(set(row) == set(CompletedInterruptionResponse.__required_keys__), "Completed interruption fields differ")
    # Validate the IDs independently: dict equality alone accepts bool/float IDs.
    integer(row["instance_id"], "response interruption instance", 1, 2**32 - 1)
    integer(row["date_raw"], "response paused date", 1)
    expected = completed_interruption_response(request, reviewer=reviewer)
    require(row["native_interruption_continued"] is True and row["original_instance_independently_absent"] is True,
            "Original native interruption was not independently resolved")
    require(row == expected, "Completed interruption crossed scene, reviewer or native instance")
    return expected
