"""Validate the optional education provider owned by one successful family query.

This decoder reads no file and performs no native query. Its caller has already
validated the original command, exact build, paused frame and export proof.
Guardian identity, Rite parameters and education variables remain unobserved.
"""
from __future__ import annotations

from copy import deepcopy
import json

from .current_first_heir_descendants_v1 import EDUCATION_TRAIT_KEYS, LEAF as DESCENDANTS

LEAF = "current_child_education_provider_inputs_v1"
SOURCE_LEAF = "current_child_education_provider_inputs_source_v1"
UTF8_LIMIT = 65536
_TOP = {
    "schema_version", "read_only", "source", "request_id", "native_revision", "date_raw",
    "played_character_full_id", "heir_character_full_id", "status", "unavailable_reason",
    "roster_complete", "collection_available", "child_observation_complete",
    "m6_inputs_complete", "guardian_role_equivalence_qualified", "queried_education_trait_keys", "rows",
}
_ROW = {
    "child_full_id", "role_source", "occurrence_indices", "education_traits", "culture_parameter",
    "guardian_full_id", "guardian_culture_parameter", "guardian_unavailable_reason",
    "rite_parameters", "rite_unavailable_reason", "education_type", "education_progress",
    "education_variables_unavailable_reason",
}


def _object(value: object, keys: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{name}: native field set changed")
    return value


def _uint(value: object, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < 2**bits:
        raise ValueError(f"{name}: unsigned {bits}-bit value required")
    return value


def _full32(value: object, name: str) -> int:
    if type(value) is not int or not -2**31 <= value < 2**31:
        raise ValueError(f"{name}: signed full32 identity required")
    return value & 0xFFFFFFFF


def _same(value: object, expected: object, name: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise ValueError(f"{name}: same-query binding changed")


def _reason(value: object, name: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name}: unavailable reason required")


def _indices(value: object, name: str) -> list[int]:
    if type(value) is not list or not 0 < len(value) <= 4096:
        raise ValueError(f"{name}: occurrence group unavailable")
    previous = -1
    for index in value:
        index = _uint(index, 32, name)
        if index <= previous:
            raise ValueError(f"{name}: occurrence order changed")
        previous = index
    return value


def _bounded_utf8(value: dict) -> None:
    # Count only this leaf, before any deepcopy. The enclosing sidecar retains
    # its independent read bound; this is not an overall memory-peak claim.
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    try:
        for chunk in encoder.iterencode(value):
            size += len(chunk.encode("utf-8", errors="strict"))
            if size > UTF8_LIMIT:
                raise ValueError("education provider exceeds 65536 UTF8 bytes")
    except (TypeError, UnicodeError, RecursionError) as exc:
        raise ValueError("education provider is not bounded UTF8 JSON") from exc


def _expected_children(
    family: dict, *, revision: int, actor: int, heir: int, date: int,
) -> list[tuple[int, list[int]]]:
    descendants = family.get(DESCENDANTS)
    child_inputs = descendants.get("child_inputs") if type(descendants) is dict else None
    if (type(child_inputs) is not dict or child_inputs.get("status") not in ("available", "partial")
            or descendants.get("status") != "available" or descendants.get("roster_complete") is not True
            or descendants.get("family_present") is not True):
        raise ValueError("education provider lacks the complete same-query child roster")
    frame = {"native_revision": revision, "played_character_id": actor,
             "heir_character_id": None if heir == -1 else heir, "date_raw": date}
    for container in (descendants, child_inputs):
        for key, expected in frame.items():
            if key not in container:
                raise ValueError("education provider child frame key missing")
            _same(container[key], expected, "education provider." + key)
    raw_rows, count = descendants.get("rows"), descendants.get("native_child_count_raw")
    if (type(raw_rows) is not list or type(count) is not int or not 0 <= count <= 4096
            or len(raw_rows) != count or type(descendants.get("data_pointer_present")) is not bool
            or (count > 0 and descendants["data_pointer_present"] is not True)):
        raise ValueError("education provider raw roster proof incomplete")
    groups: dict[int, list[int]] = {}
    classifications: dict[int, tuple[bool, bool]] = {}
    for index, occurrence in enumerate(raw_rows):
        if type(occurrence) is not dict:
            raise ValueError("education provider raw occurrence malformed")
        _same(occurrence.get("occurrence_index"), index, "education provider.occurrence_index")
        full_id = _uint(occurrence.get("raw_character_id"), 32, "education provider.raw_character_id")
        alive, child = occurrence.get("alive"), occurrence.get("child_of_heir")
        if (occurrence.get("generation_valid") is not True or type(alive) is not bool
                or (alive and type(child) is not bool)):
            raise ValueError("education provider raw occurrence classification unavailable")
        classification = (alive, alive and child is True)
        if full_id in classifications and classifications[full_id] != classification:
            raise ValueError("education provider duplicate occurrence classification changed")
        classifications[full_id] = classification
        if classification == (True, True):
            groups.setdefault(full_id, []).append(index)
    rows = child_inputs.get("rows")
    if type(rows) is not list or len(rows) > 256 or len(rows) != len(groups):
        raise ValueError("education provider selected child roster incomplete")
    expected_rows = list(groups.items())
    for row, (full_id, indices) in zip(rows, expected_rows):
        if type(row) is not dict or _full32(row.get("character_id"), "selected child") != full_id:
            raise ValueError("education provider selected child order changed")
        _same(_indices(row.get("occurrence_indices"), "selected child occurrences"),
              indices, "selected child occurrences")
    return expected_rows


def _traits(value: object) -> bool:
    value = _object(value, {"available", "unavailable_reason", "present_trait_keys"}, "education traits")
    available = value["available"]
    if type(available) is not bool:
        raise ValueError("education traits availability must be boolean")
    present, reason = value["present_trait_keys"], value["unavailable_reason"]
    if available:
        if reason is not None or type(present) is not list or len(present) > 25:
            raise ValueError("education traits available contents malformed")
        if (any(type(key) is not str for key in present)
                or present != [key for key in EDUCATION_TRAIT_KEYS if key in present]):
            raise ValueError("education trait key order or membership changed")
    else:
        _reason(reason, "education traits")
        if present is not None:
            raise ValueError("unavailable education traits must retain null")
    return available


def _culture(value: object) -> bool:
    value = _object(value, {"key", "available", "culture_full_id", "value", "unavailable_reason"},
                    "education culture parameter")
    _same(value["key"], "better_ward_education", "education culture key")
    available = value["available"]
    if type(available) is not bool:
        raise ValueError("education culture availability must be boolean")
    witness = value["culture_full_id"]
    if witness is not None:
        _uint(witness, 32, "education culture full ID")
    if available:
        if witness is None or type(value["value"]) is not bool or value["unavailable_reason"] is not None:
            raise ValueError("available education culture contents malformed")
    else:
        _reason(value["unavailable_reason"], "education culture")
        if value["value"] is not None:
            raise ValueError("unavailable education culture value must retain null")
    return available


def validate_current_child_education_provider_inputs_v1(
    value: object, *, family_result: dict, qualified: bool, request_id: str,
    revision: int, actor: int, heir: int, date: int,
) -> dict | None:
    """Return an owned strict leaf; missing/null remains unknown, never known-empty."""
    if value is None:
        return None
    value = _object(value, _TOP, "education provider")
    _bounded_utf8(value)
    if qualified is not True:
        raise ValueError("education provider object lacks qualified captured source")
    if type(family_result) is not dict or "heir_character_id" not in family_result:
        raise ValueError("education provider normalized heir binding missing")
    family_heir = family_result["heir_character_id"]
    if family_heir is not None:
        _full32(family_heir, "normalized heir")
    _same(heir, -1 if family_heir is None else family_heir, "education provider normalized heir")
    for key, expected in (
        ("schema_version", 1), ("read_only", True), ("source", "same_query_actual4_child_education_inputs"),
        ("m6_inputs_complete", False), ("guardian_role_equivalence_qualified", False),
        ("request_id", request_id), ("native_revision", revision), ("date_raw", date),
        ("played_character_full_id", _full32(actor, "played character")),
        ("heir_character_full_id", _full32(heir, "heir character")),
    ):
        _same(value[key], expected, "education provider." + key)
    if type(request_id) is not str or not request_id:
        raise ValueError("education provider original request unavailable")
    if _uint(value["native_revision"], 64, "education provider revision") == 0:
        raise ValueError("education provider native revision must be positive")
    if type(date) is not int or not -2**63 <= date < 2**63:
        raise ValueError("education provider date must be signed int64")
    if (type(value["queried_education_trait_keys"]) is not list
            or value["queried_education_trait_keys"] != list(EDUCATION_TRAIT_KEYS)
            or any(type(key) is not str for key in value["queried_education_trait_keys"])):
        raise ValueError("education provider queried trait catalog changed")
    flags = tuple(value[key] for key in ("roster_complete", "collection_available", "child_observation_complete"))
    states = {"available": (True, True, True), "partial": (True, True, False),
              "unavailable": (False, False, False)}
    status, rows = value["status"], value["rows"]
    if (type(status) is not str or status not in states or any(type(flag) is not bool for flag in flags)
            or flags != states[status] or type(rows) is not list or len(rows) > 256):
        raise ValueError("education provider status or completeness malformed")
    if status == "available":
        if value["unavailable_reason"] is not None:
            raise ValueError("available education provider reason must be null")
    else:
        _reason(value["unavailable_reason"], "education provider")
    if status == "unavailable":
        if rows:
            raise ValueError("unavailable education provider must retain empty unknown rows")
        return deepcopy(value)
    if status == "partial":
        _same(value["unavailable_reason"], "education_child_inputs_partially_observed", "education provider reason")
    expected = _expected_children(family_result, revision=revision, actor=actor, heir=heir, date=date)
    if len(rows) != len(expected):
        raise ValueError("education provider child inventory incomplete")
    all_available = True
    for row, (full_id, indices) in zip(rows, expected):
        row = _object(row, _ROW, "education provider child")
        _same(_uint(row["child_full_id"], 32, "education child full ID"), full_id, "education child full ID")
        _same(row["role_source"], "current_living_actual_child_of_first_heir", "education child role")
        _same(_indices(row["occurrence_indices"], "education child occurrences"), indices, "education child occurrences")
        for key in ("guardian_full_id", "guardian_culture_parameter", "rite_parameters", "education_type", "education_progress"):
            if row[key] is not None:
                raise ValueError("education provider unobserved authoritative field must retain null")
        for key, reason in (
            ("guardian_unavailable_reason", "authoritative_educator_identity_not_observed"),
            ("rite_unavailable_reason", "target_rite_education_parameters_not_observed"),
            ("education_variables_unavailable_reason", "typed_target_variable_value_access_not_wired"),
        ):
            _same(row[key], reason, "education child." + key)
        traits_available = _traits(row["education_traits"])
        culture_available = _culture(row["culture_parameter"])
        all_available = all_available and traits_available and culture_available
    if (status == "available") is not all_available:
        raise ValueError("education provider status differs from trait and culture subreads")
    return deepcopy(value)
