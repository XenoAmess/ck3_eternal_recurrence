"""Release opportunity selection after an independently observed storage reuse.

This is historical observation loss, never a terminal outcome. The caller still
needs the existing fresh target query and complete native empty-slot/legal checks
before a new UUID can enter the original once-only consumer.
"""
from collections.abc import Mapping

from .bridge.version_identity import CK3_12004, require_exact_native_build


def reused_sway_observation_gap_v1(resolved, *, actor_character_id, date_raw):
    from .sway_formal_consumer import _resolved_instance_identity

    if (not isinstance(resolved, Mapping) or resolved.get("status") != "applied"
            or resolved.get("postcondition_verified") is not True
            or type(actor_character_id) is not int
            or resolved.get("actor_character_id") != actor_character_id
            or type(date_raw) is not int):
        return None
    terminal = resolved.get("terminal_intervention")
    if (isinstance(terminal, Mapping)
            and terminal.get("instance_terminal_outcome_observed") is True):
        return None
    identity = _resolved_instance_identity(resolved)
    observation = resolved.get("latest_instance_observation")
    if not isinstance(identity, Mapping) or not isinstance(observation, Mapping):
        return None
    original = {key: resolved.get(key) for key in (
        "action_id", "actor_character_id", "target_character_id")}
    original.update({key: identity.get(key) for key in (
        "scheme_instance_id", "scheme_instance_generation")})
    if (not isinstance(original["action_id"], str) or not original["action_id"]
            or any(type(original[key]) is not int or not 0 < original[key] < 0xFFFFFFFF
                   for key in ("actor_character_id", "target_character_id", "scheme_instance_id"))
            or original["actor_character_id"] == original["target_character_id"]
            or type(original["scheme_instance_generation"]) is not int
            or original["scheme_instance_generation"] != original["scheme_instance_id"] >> 24
            or any(observation.get(key) != value for key, value in original.items())
            or observation.get("tracked_instance_active") is not False
            or observation.get("instance_terminal_outcome_observed") is not False
            or type(observation.get("source_native_revision")) is not int
            or observation["source_native_revision"] <= 0
            or type(observation.get("source_date_raw")) is not int
            or observation["source_date_raw"] > date_raw):
        return None
    native = observation.get("native_observation")
    if (not isinstance(native, Mapping) or native.get("schema") != "xar.ck3.sway_completion.v1"
            or native.get("available") is not True
            or any(native.get(key) != original[key] for key in (
                "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"))
            or native.get("snapshot_revision") != observation["source_native_revision"]
            or native.get("date_raw") != observation["source_date_raw"]
            or any(native.get(key) is not value for key, value in {
                "instance_source_observed": True, "instance_present": False,
                "storage_slot_reused": True, "exact_instance_join_ready": False,
                "native_status_observed": False, "native_terminal_state_observed": False,
            }.items())
            or native.get("native_status_raw") is not None):
        return None
    try:
        if (require_exact_native_build(native.get("exact_ck3_build"), native.get("exe_sha256")) != CK3_12004
                or require_exact_native_build(observation.get("exact_ck3_build"), observation.get("exe_sha256")) != CK3_12004):
            return None
    except ValueError:
        return None
    return {**original, "source_native_revision": observation["source_native_revision"],
            "source_date_raw": observation["source_date_raw"],
            "storage_slot_reused": True, "instance_terminal_outcome_observed": False,
            "terminal_cause": "unknown"}


def fresh_empty_sway_slot_after_reuse_v1(resolved, readback):
    """Called only after the formal consumer's unchanged current-frame join."""
    if not isinstance(readback, Mapping):
        return None
    gap = reused_sway_observation_gap_v1(resolved,
        actor_character_id=readback.get("actor_character_id"), date_raw=readback.get("date_raw"))
    if (gap is None or readback.get("schema") != "active-scheme-sway-private-read-v1"
            or readback.get("target_character_id") != gap["target_character_id"]
            or type(readback.get("active_scheme_count")) is not int
            or readback["active_scheme_count"] != 0
            or not isinstance(readback.get("active_sway_instances"), list)
            or readback["active_sway_instances"] != []
            or readback.get("matching_sway_active") is not False
            or readback.get("native_complete_can_send") is not True
            or readback.get("native_legal_now") is not True):
        return None
    try:
        if require_exact_native_build(readback.get("exact_ck3_build"), readback.get("exe_sha256")) != CK3_12004:
            return None
    except ValueError:
        return None
    return gap
