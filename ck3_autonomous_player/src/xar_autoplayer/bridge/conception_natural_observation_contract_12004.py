"""Strict copied19b journal contract; no native reads or invocation."""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

BUILD = "1.20.0.4"
SOURCE_PIN = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
JOURNAL_SCHEMA = "xar.ck3.conception-pair-passive-12004.v1"
U32 = (1 << 32) - 1
U64 = (1 << 64) - 1
I64_LOW = -(1 << 63)
I64_HIGH = (1 << 63) - 1

JOURNAL_KEYS = frozenset((
    "schema", "source", "build_version", "source_pin", "image_base",
    "observer_installed", "current_session_guard", "clock_identity",
    "oldest_available_sequence", "latest_sequence", "overwritten_events",
    "unattributed_identity_events", "event_count", "events",
))
EVENT_KEYS = frozenset((
    "journal_sequence", "source_pin", "caller_return_pc", "caller_return_rva",
    "process_id", "thread_id", "before_event", "completed_event",
    "first_character", "second_character", "sample_receiver", "original_r9_modifier",
    "first_before", "second_before", "first_after", "second_after",
    "sample_state_before_2dword", "sample_state_after_2dword", "source_before", "source_after",
    "original_called_once", "original_returned", "original_rax_bits", "original_al",
    "generation_unchanged", "first_post_pending_matches_write_pattern",
    "event_clock_and_thread_match", "duplicate_provider_returns", "duplicate_sample_returns",
    "fixture_origin", "provider", "sample",
))
CLOCK_KEYS = frozenset(("clock_identity", "sequence", "thread_id"))
CHARACTER_KEYS = frozenset((
    "character", "full_id", "magic", "native_sex_1a1", "extended_pointer",
    "extended_288_raw", "extended_288_blocks", "pending_3e8_raw", "pending_3f0_raw",
))
SOURCE_KEYS = frozenset((
    "scalar_5c69ec8_raw", "lower_5c69f00_raw", "upper_5c69f10_raw",
    "actual_original_consumed_values",
))
PARENT_KEYS = frozenset((
    "clock_identity", "parent_scope_id", "process_clock", "thread_id",
    "first_character", "second_character", "first_full_id", "second_full_id", "sample_receiver",
))
PROVIDER_KEYS = frozenset((
    "source", "source_pin", "journal_sequence", "parent", "before_event", "returned_event",
    "process_id", "thread_id", "caller_return_pc", "caller_return_rva", "output_pointer",
    "first_character", "second_character", "mode", "fifth_argument", "output_before", "output_after",
    "first_full_id_before", "second_full_id_before", "first_full_id_after", "second_full_id_after",
    "native_return_bits", "original_returned", "native_return_matches_output",
    "parent_extent_unchanged", "event_clock_and_thread_match", "actual_caller_input_ready",
    "capture_failure_flags",
))
SAMPLE_JOURNAL_KEYS = frozenset((
    "source", "build", "source_pin", "observer_installed", "oldest_available_sequence",
    "latest_sequence", "overwritten_events", "event_count", "events",
))
SAMPLE_KEYS = frozenset((
    "journal_sequence", "source_pin", "parent", "caller_return_rva", "receiver",
    "original_lower", "original_upper", "original_returned", "returned_rax_signed64",
    "state_before_2dword", "state_after_2dword", "state_transition_matches_source",
    "before_event", "returned_event", "threshold_at_sample_signed64", "threshold_capture_ready",
    "comparison_at_sample_passed", "parent_extent_and_generation_unchanged",
    "event_clock_and_thread_match", "sample_within_source_range", "causal_sample_ready",
    "capture_failure_flags", "native_class_name", "loaded_scalar_reconstruction",
))


def _object(value: Any, keys: frozenset[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{name} fields differ from the exact source contract")
    return value


def _integer(value: Any, name: str, low: int = 0, high: int = U64, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} is not an exact bounded integer")


def _boolean(value: Any, name: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not bool:
        raise ValueError(f"{name} is not a copied boolean")


def _decimal(value: Any, name: str, low: int, high: int, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if (type(value) is not str or not re.fullmatch(r"-?(0|[1-9][0-9]*)", value)
            or value == "-0" or not low <= int(value) <= high):
        raise ValueError(f"{name} is not a canonical raw64 decimal string")


def _pin(value: Any) -> None:
    if type(value) is not str or value.upper() != SOURCE_PIN:
        raise ValueError("natural conception exact executable source pin changed")


def _clock(value: Any) -> None:
    value = _object(value, CLOCK_KEYS, "clock")
    _integer(value["clock_identity"], "clock identity")
    _integer(value["sequence"], "process clock sequence")
    _integer(value["thread_id"], "clock thread", high=U32, nullable=True)


def _state(value: Any) -> None:
    if value is None:
        return
    if type(value) is not list or len(value) != 2:
        raise ValueError("sample state must retain exactly two DWORDs or null")
    for raw in value:
        _integer(raw, "sample state DWORD", high=U32)


def _character(value: Any, pointer: int) -> None:
    value = _object(value, CHARACTER_KEYS, "Character")
    _integer(value["character"], "Character pointer")
    if value["character"] != pointer:
        raise ValueError("Character copy escaped its original parent argument")
    for name in ("full_id", "magic"):
        _integer(value[name], name, high=U32, nullable=True)
    for name in ("native_sex_1a1", "pending_3e8_raw"):
        _integer(value[name], name, high=255, nullable=True)
    for name in ("extended_pointer", "pending_3f0_raw"):
        _integer(value[name], name, nullable=True)
    _decimal(value["extended_288_raw"], "extended288", 0, U64, nullable=True)
    _boolean(value["extended_288_blocks"], "extended288 branch", nullable=True)


def _source(value: Any) -> None:
    value = _object(value, SOURCE_KEYS, "raw global bookends")
    for name in SOURCE_KEYS - {"actual_original_consumed_values"}:
        _decimal(value[name], name, I64_LOW, I64_HIGH, nullable=True)
    if value["actual_original_consumed_values"] is not False:
        raise ValueError("guarded scalar/clamp copies became consumed MOV values")


def _parent(value: Any, *, provider: bool = False) -> None:
    keys = PARENT_KEYS | {"active"} if provider else PARENT_KEYS
    value = _object(value, keys, "child parent")
    for name in PARENT_KEYS:
        _integer(value[name], name, high=U32 if name in (
            "thread_id", "first_full_id", "second_full_id") else U64)
    if provider:
        _boolean(value["active"], "provider parent active")


def _provider(value: Any, image_base: int) -> None:
    if value is None:
        return
    value = _object(value, PROVIDER_KEYS, "provider child")
    if value["source"] != "natural_original_pair_provider_first_qword":
        raise ValueError("provider source changed")
    _pin(value["source_pin"])
    _parent(value["parent"], provider=True)
    _clock(value["before_event"])
    _clock(value["returned_event"])
    for name in ("journal_sequence", "caller_return_pc", "caller_return_rva", "output_pointer",
                 "first_character", "second_character", "fifth_argument", "native_return_bits"):
        _integer(value[name], name)
    for name in ("process_id", "thread_id", "mode", "capture_failure_flags"):
        _integer(value[name], name, high=U32)
    for name in ("output_before", "output_after"):
        _integer(value[name], name, I64_LOW, I64_HIGH, nullable=True)
    for name in ("first_full_id_before", "second_full_id_before", "first_full_id_after", "second_full_id_after"):
        _integer(value[name], name, high=U32, nullable=True)
    for name in ("original_returned", "native_return_matches_output", "parent_extent_unchanged",
                 "event_clock_and_thread_match", "actual_caller_input_ready"):
        _boolean(value[name], name)
    if value["caller_return_pc"] != image_base + value["caller_return_rva"]:
        raise ValueError("provider raw ReturnAddress and RVA disagree")


def _sample(value: Any) -> None:
    if value is None:
        return
    value = _object(value, SAMPLE_JOURNAL_KEYS, "sample journal")
    if value["source"] != "natural_E46530_original_entry_return" or value["build"] != BUILD:
        raise ValueError("sample exact source/build changed")
    _pin(value["source_pin"])
    _boolean(value["observer_installed"], "sample journal installation copy")
    for name in ("oldest_available_sequence", "latest_sequence", "overwritten_events", "event_count"):
        _integer(value[name], name)
    if type(value["events"]) is not list or len(value["events"]) != 1 or value["event_count"] != 1:
        raise ValueError("attached sample must contain exactly its one copied child event")
    event = _object(value["events"][0], SAMPLE_KEYS, "sample child")
    _pin(event["source_pin"])
    _parent(event["parent"])
    _clock(event["before_event"])
    _clock(event["returned_event"])
    for name in ("journal_sequence", "caller_return_rva", "receiver"):
        _integer(event[name], name)
    for name in ("original_lower", "original_upper", "returned_rax_signed64"):
        _integer(event[name], name, I64_LOW, I64_HIGH)
    _integer(event["threshold_at_sample_signed64"], "captured caller RBX", I64_LOW, I64_HIGH, nullable=True)
    _integer(event["capture_failure_flags"], "sample failure flags", high=U32)
    for name in ("original_returned", "threshold_capture_ready", "parent_extent_and_generation_unchanged",
                 "event_clock_and_thread_match", "sample_within_source_range", "causal_sample_ready"):
        _boolean(event[name], name)
    for name in ("state_transition_matches_source", "comparison_at_sample_passed"):
        _boolean(event[name], name, nullable=True)
    _state(event["state_before_2dword"])
    _state(event["state_after_2dword"])
    if event["native_class_name"] is not None or event["loaded_scalar_reconstruction"] is not None:
        raise ValueError("sample unknown labels became a reconstructed scalar/class")
    if (value["oldest_available_sequence"] != event["journal_sequence"]
            or value["latest_sequence"] != event["journal_sequence"] or value["overwritten_events"] != 0):
        raise ValueError("attached sample metadata differs from its owned child")


def _full_handle(value: Any) -> int:
    # Current public Character handles may be signed; preserve every DWORD bit.
    _integer(value, "expected household full ID", -(1 << 31), U32)
    raw = value & U32
    if raw == U32:
        raise ValueError("invalid household full ID")
    return raw


def normalize_conception_natural_observations_12004(
    value: object, *, expected_first_character_id: int, expected_second_character_id: int,
) -> dict[str, Any] | None:
    """Retain owned wire in native orientation, matched by complete household IDs.

    Null is unavailable; an absent optional key belongs to the caller's old wire.
    False live guards and fixture origin are preserved, never raised to current.
    Malformed schema/types/identity/source pins raise ValueError.
    """
    expected = (_full_handle(expected_first_character_id), _full_handle(expected_second_character_id))
    if value is None:
        return None
    journal = _object(value, JOURNAL_KEYS, "parent journal")
    if (journal["schema"] != JOURNAL_SCHEMA or journal["source"] != "natural_2929B40_original_once"
            or journal["build_version"] != BUILD):
        raise ValueError("parent journal exact source/build changed")
    _pin(journal["source_pin"])
    for name in ("image_base", "clock_identity", "oldest_available_sequence", "latest_sequence",
                 "overwritten_events", "unattributed_identity_events", "event_count"):
        _integer(journal[name], name)
    if journal["image_base"] == 0:
        raise ValueError("parent journal lacks its admitted image base")
    _boolean(journal["observer_installed"], "parent installation copy")
    _boolean(journal["current_session_guard"], "parent current guard")
    if (type(journal["events"]) is not list or len(journal["events"]) > 256
            or journal["event_count"] != len(journal["events"])):
        raise ValueError("parent event count differs from the bounded owned journal")
    oldest, latest = journal["oldest_available_sequence"], journal["latest_sequence"]
    if (oldest == 0) != (latest == 0) or (oldest and oldest > latest):
        raise ValueError("parent retained sequence range is malformed")
    previous = 0
    for raw in journal["events"]:
        event = _object(raw, EVENT_KEYS, "parent event")
        _pin(event["source_pin"])
        for name in ("journal_sequence", "caller_return_pc", "first_character", "second_character", "sample_receiver"):
            _integer(event[name], name)
        _integer(event["caller_return_rva"], "parent caller RVA", nullable=True)
        for name in ("process_id", "thread_id", "duplicate_provider_returns", "duplicate_sample_returns"):
            _integer(event[name], name, high=U32)
        _clock(event["before_event"])
        _clock(event["completed_event"])
        _decimal(event["original_r9_modifier"], "original R9", I64_LOW, I64_HIGH)
        _decimal(event["original_rax_bits"], "original RAX bits", 0, U64, nullable=True)
        _integer(event["original_al"], "original AL", high=255, nullable=True)
        for name in ("original_called_once", "original_returned", "event_clock_and_thread_match", "fixture_origin"):
            _boolean(event[name], name)
        for name in ("generation_unchanged", "first_post_pending_matches_write_pattern"):
            _boolean(event[name], name, nullable=True)
        _state(event["sample_state_before_2dword"])
        _state(event["sample_state_after_2dword"])
        _source(event["source_before"])
        _source(event["source_after"])
        for role in ("first", "second"):
            for phase in ("before", "after"):
                _character(event[role + "_" + phase], event[role + "_character"])
        before = (event["first_before"]["full_id"], event["second_before"]["full_id"])
        after = (event["first_after"]["full_id"], event["second_after"]["full_id"])
        orientations = (expected, expected[::-1])
        before_qualified = all(event[role + "_before"]["magic"] == 0x43686172 for role in ("first", "second"))
        after_qualified = all(event[role + "_after"]["magic"] == 0x43686172 for role in ("first", "second"))
        if not ((before in orientations and before_qualified) or (after in orientations and after_qualified)):
            raise ValueError("retained pair does not match complete household IDs")
        if event["generation_unchanged"] is True and (before != after or not before_qualified or not after_qualified):
            raise ValueError("generation unchanged flag contradicts complete IDs")
        sequence = event["journal_sequence"]
        if not oldest <= sequence <= latest or sequence <= previous:
            raise ValueError("retained parent events are not ordered in their exact sequence range")
        previous = sequence
        rva = event["caller_return_rva"]
        if rva is not None and event["caller_return_pc"] != journal["image_base"] + rva:
            raise ValueError("parent raw ReturnAddress and retained RVA disagree")
        if (event["original_al"] is not None and event["original_rax_bits"] is not None
                and event["original_al"] != int(event["original_rax_bits"]) & 255):
            raise ValueError("parent low AL differs from retained complete RAX")
        _provider(event["provider"], journal["image_base"])
        _sample(event["sample"])
    return deepcopy(journal)
