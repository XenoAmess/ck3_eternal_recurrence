"""Read the native state of an exact Sway instance, including retained terminals."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, require_exact_native_build


STEP = "query-sway-completion-v1-private"
SCHEMA = "xar.ck3.sway_completion.v1"
PERMISSION = "allow_private_active_scheme_sway_completion_query"
_CONTEXT_KEYS = {
    "schema", "schema_version", "build_version", "executable_sha256", "adapter_id",
    "private_build", "read_only", "advertised", "available", "unavailable_reason",
    "snapshot_revision", "date_raw", "actor_character_id", "target_character_id",
    "scheme_instance_id", "scheme_instance_generation", "native_source_kind",
    "current_instance_retention", "instance_source_observed", "instance_present",
    "storage_slot_reused", "exact_instance_join_ready", "native_owner_raw",
    "owner_matches_actor", "owner_cleared", "native_status_observed",
    "native_status_raw", "native_status_key", "native_terminal_state_observed",
    "native_success_chance_observed", "native_success_chance_raw",
    "native_success_chance_scale", "native_success_chance_unit",
    "terminal_cause_observed", "terminal_cause",
}
_CAN_CONTINUE_KEYS = {"native_can_continue_observed", "native_can_continue"}
_BOOL_KEYS = (
    "private_build", "read_only", "advertised", "available", "instance_source_observed",
    "instance_present", "storage_slot_reused", "exact_instance_join_ready",
    "owner_matches_actor", "owner_cleared", "native_status_observed",
    "native_terminal_state_observed", "native_success_chance_observed",
    "terminal_cause_observed",
)
_STRING_KEYS = (
    "unavailable_reason", "native_source_kind", "current_instance_retention",
    "native_status_key", "native_success_chance_unit", "terminal_cause",
)


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_active_scheme_sway_completion_v1(
    value: object, *, snapshot: Mapping[str, object],
    target_character_id: int, scheme_instance_id: int,
) -> dict[str, object]:
    """Copy actual terminal/absence/chance facts without assigning a cause."""
    if (not isinstance(value, dict)
            or set(value) not in (_CONTEXT_KEYS, _CONTEXT_KEYS | _CAN_CONTINUE_KEYS)
            or value["schema"] != SCHEMA):
        raise ValueError("native sway completion schema is malformed")
    build = require_exact_native_build(value["build_version"], value["executable_sha256"])
    if (build != CK3_12002 or build != private_native_build_identity(snapshot)
            or value["adapter_id"] != "ck3-1.20.0.2-msvc-x64"
            or type(value["schema_version"]) is not int or value["schema_version"] != 1):
        raise ValueError("native sway completion belongs to another build/schema")
    if (any(type(value[key]) is not bool for key in _BOOL_KEYS)
            or any(not isinstance(value[key], str) for key in _STRING_KEYS)
            or value["private_build"] is not True or value["read_only"] is not True
            or value["advertised"] is not False
            or not _integer(value["snapshot_revision"], 1, 0xFFFFFFFFFFFFFFFF)
            or not _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1)
            or not _integer(value["actor_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["target_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["scheme_instance_id"], 0, 0xFFFFFFFE)
            or not _integer(value["scheme_instance_generation"], 0, 255)
            or type(value["native_success_chance_scale"]) is not int
            or value["native_success_chance_scale"] != 100000
            or value["native_success_chance_unit"] != "percent"):
        raise ValueError("native sway completion scalar fields are malformed")
    for key, minimum, maximum in (
        ("native_owner_raw", 0, 0xFFFFFFFF),
        ("native_status_raw", -(1 << 31), (1 << 31) - 1),
        ("native_success_chance_raw", -(1 << 63), (1 << 63) - 1),
    ):
        if value[key] is not None and not _integer(value[key], minimum, maximum):
            raise ValueError(f"native sway completion nullable native value is malformed: {key}")
    if "native_can_continue_observed" in value:
        observed = value["native_can_continue_observed"]
        can_continue = value["native_can_continue"]
        if (type(observed) is not bool
                or (observed and type(can_continue) is not bool)
                or (not observed and can_continue is not None)):
            raise ValueError("native sway completion continue observation is malformed")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value["actor_character_id"] != actor.get("character_id")
            or value["target_character_id"] != target_character_id
            or value["scheme_instance_id"] != scheme_instance_id
            or value["snapshot_revision"] != snapshot.get("native_revision")
            or value["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native sway completion differs from its exact instance/player frame")
    # Native status 1 is an observed terminated row, shared by cancel and end.
    # Absent/reused storage, phase bookkeeping and current chance provide no
    # terminal cause. Preserve the producer's facts and nullable raw values.
    return dict(value)


def query_active_scheme_sway_completion_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    scheme_instance_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if (not _integer(target_character_id, 1, (1 << 31) - 1)
            or not _integer(scheme_instance_id, 0, 0xFFFFFFFE)):
        raise ValueError("private sway completion target/full instance ID is invalid")
    actor = driver.take_snapshot().get("played_character")
    if not isinstance(actor, Mapping) or not _integer(actor.get("character_id"), 1, (1 << 31) - 1):
        raise BridgeUnavailableError("private sway completion lacks the current player identity")
    if actor["character_id"] == target_character_id:
        raise ValueError("private sway completion target must differ from the current player")
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"actor_character_id": actor["character_id"],
                        "target_character_id": target_character_id,
                        "scheme_instance_id": scheme_instance_id},
        timeout_seconds=timeout_seconds,
    )
    try:
        if result.get("backend_id") != "native-headless":
            raise ValueError("native sway completion backend is malformed")
        value = normalize_active_scheme_sway_completion_v1(
            result.get("sway_completion"), snapshot=before,
            target_character_id=target_character_id, scheme_instance_id=scheme_instance_id,
        )
        if result.get("status") != ("available" if value["available"] else "unavailable"):
            raise ValueError("native sway completion envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "backend_id": result["backend_id"], "status": result["status"],
    }
