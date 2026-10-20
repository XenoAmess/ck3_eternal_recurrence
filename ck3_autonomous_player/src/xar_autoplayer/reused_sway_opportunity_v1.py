"""Permit a fresh Sway opportunity after a source-bound storage reuse.

A missing old instance remains an unknown terminal outcome. The existing formal
consumer still owns the fresh frame, empty slot, legal admission and new UUID.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypeGuard, TypedDict

from .bridge.version_identity import CK3_12004, require_exact_native_build


class ReusedSwayObservationGapV1(TypedDict):
    action_id: str
    actor_character_id: int
    target_character_id: int
    scheme_instance_id: int
    scheme_instance_generation: int
    source_native_revision: int
    source_date_raw: int
    storage_slot_reused: Literal[True]
    instance_terminal_outcome_observed: Literal[False]
    terminal_cause: Literal["unknown"]


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        return None
    return {key: item for key, item in value.items()}


def _integer(value: object) -> TypeGuard[int]:
    return type(value) is int


def _full_id(value: object) -> TypeGuard[int]:
    return type(value) is int and 0 < value < 0xFFFFFFFF


def reused_sway_observation_gap_v1(
    resolved: object, *, actor_character_id: object, date_raw: object,
) -> ReusedSwayObservationGapV1 | None:
    from .sway_formal_consumer import _resolved_instance_identity

    row = _mapping(resolved)
    if (row is None or row.get("status") != "applied"
            or row.get("postcondition_verified") is not True
            or not _integer(actor_character_id)
            or row.get("actor_character_id") != actor_character_id
            or not _integer(date_raw)):
        return None
    terminal = _mapping(row.get("terminal_intervention"))
    if terminal is not None and terminal.get("instance_terminal_outcome_observed") is True:
        return None
    identity = _mapping(_resolved_instance_identity(row))
    observation = _mapping(row.get("latest_instance_observation"))
    if identity is None or observation is None:
        return None
    action = row.get("action_id")
    actor, target = row.get("actor_character_id"), row.get("target_character_id")
    instance, generation = identity.get("scheme_instance_id"), identity.get("scheme_instance_generation")
    revision, date = observation.get("source_native_revision"), observation.get("source_date_raw")
    if (not isinstance(action, str) or not action
            or not _full_id(actor) or not _full_id(target) or actor == target
            or not _full_id(instance) or not _integer(generation)
            or generation != instance >> 24 or not _integer(revision) or revision <= 0
            or not _integer(date) or date > date_raw):
        return None
    original = {"action_id": action, "actor_character_id": actor,
                "target_character_id": target, "scheme_instance_id": instance,
                "scheme_instance_generation": generation}
    if (any(type(observation.get(key)) is not type(item) or observation.get(key) != item
                   for key, item in original.items())
            or observation.get("tracked_instance_active") is not False
            or observation.get("instance_terminal_outcome_observed") is not False):
        return None
    native = _mapping(observation.get("native_observation"))
    if (native is None or native.get("schema") != "xar.ck3.sway_completion.v1"
            or native.get("available") is not True
            or any(type(native.get(key)) is not type(original[key]) or native.get(key) != original[key] for key in (
                "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"))
            or type(native.get("snapshot_revision")) is not int or native.get("snapshot_revision") != revision
            or type(native.get("date_raw")) is not int or native.get("date_raw") != date
            or any(native.get(key) is not item for key, item in {
                "instance_source_observed": True, "instance_present": False,
                "storage_slot_reused": True, "exact_instance_join_ready": False,
                "native_status_observed": False, "native_terminal_state_observed": False,
            }.items()) or native.get("native_status_raw") is not None):
        return None
    try:
        if (require_exact_native_build(native.get("exact_ck3_build"), native.get("exe_sha256")) != CK3_12004
                or require_exact_native_build(observation.get("exact_ck3_build"), observation.get("exe_sha256")) != CK3_12004):
            return None
    except ValueError:
        return None
    return ReusedSwayObservationGapV1(
        action_id=action, actor_character_id=actor, target_character_id=target,
        scheme_instance_id=instance, scheme_instance_generation=generation,
        source_native_revision=revision, source_date_raw=date,
        storage_slot_reused=True, instance_terminal_outcome_observed=False,
        terminal_cause="unknown")


def fresh_empty_sway_slot_after_reuse_v1(
    resolved: object, readback: object,
) -> ReusedSwayObservationGapV1 | None:
    """Called after the formal consumer's unchanged current-frame join."""
    row = _mapping(readback)
    if row is None:
        return None
    gap = reused_sway_observation_gap_v1(
        resolved, actor_character_id=row.get("actor_character_id"), date_raw=row.get("date_raw"))
    if (gap is None or row.get("schema") != "active-scheme-sway-private-read-v1"
            or row.get("target_character_id") != gap["target_character_id"]
            or type(row.get("active_scheme_count")) is not int or row["active_scheme_count"] != 0
            or not isinstance(row.get("active_sway_instances"), list) or row["active_sway_instances"] != []
            or row.get("matching_sway_active") is not False
            or row.get("native_complete_can_send") is not True or row.get("native_legal_now") is not True):
        return None
    try:
        if require_exact_native_build(row.get("exact_ck3_build"), row.get("exe_sha256")) != CK3_12004:
            return None
    except ValueError:
        return None
    return gap
