"""Read copied native Sway termination-source pre/post observations."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, require_exact_native_build


STEP = "query-sway-completion-termination-v1-private"
SCHEMA = "xar.ck3.sway-completion-termination.v1"
PERMISSION = "allow_private_active_scheme_sway_completion_termination_query"
_CONTEXT_KEYS = {
    "schema", "available", "unavailable_reason", "read_only", "observer_attached",
    "actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence",
    "earliest_sequence", "latest_sequence", "retention_gap", "session_records_only",
    "material_effect_observed", "records",
}
_RECORD_KEYS = {
    "sequence", "source_class", "date_raw", "actor_character_id", "target_character_id",
    "scheme_instance_id", "scheme_instance_generation", "input_root_scope_kind",
    "executing_source_observed", "pre_status", "pre_owner", "post_read_succeeded",
    "post_instance_present", "post_storage_slot_reused", "post_exact_instance_join_ready",
    "post_status_observed", "post_status", "post_owner", "native_terminal_state_observed",
    "native_terminal_transition_observed", "material_effect_observed", "specific_invalidation_reason",
}
_SOURCE_CLASSES = {
    "end_scheme_command_execute", "authored_end_scheme_false_execute",
    "authored_end_scheme_true_execute",
}
_RECORD_BOOL_KEYS = (
    "executing_source_observed", "post_read_succeeded", "post_instance_present",
    "post_storage_slot_reused", "post_exact_instance_join_ready", "post_status_observed",
    "native_terminal_state_observed", "native_terminal_transition_observed", "material_effect_observed",
)


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_active_scheme_sway_completion_termination_v1(
    value: object, *, snapshot: Mapping[str, object], target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0,
) -> dict[str, object]:
    """Preserve actual source and post-state flags without assigning a cause."""
    if (not isinstance(value, dict) or set(value) != _CONTEXT_KEYS
            or value["schema"] != SCHEMA):
        raise ValueError("native sway termination schema is malformed")
    if (any(type(value[key]) is not bool for key in (
                "available", "read_only", "observer_attached", "retention_gap",
                "session_records_only", "material_effect_observed",
            ))
            or not isinstance(value["unavailable_reason"], str)
            or value["read_only"] is not True or value["session_records_only"] is not True
            or value["material_effect_observed"] is not False
            or not _integer(value["actor_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["target_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["scheme_instance_id"], 0, 0xFFFFFFFE)
            or any(not _integer(value[key], 0, 0xFFFFFFFFFFFFFFFF)
                   for key in ("after_sequence", "earliest_sequence", "latest_sequence"))
            or not isinstance(value["records"], list)):
        raise ValueError("native sway termination scalar fields are malformed")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value["actor_character_id"] != actor.get("character_id")
            or value["target_character_id"] != target_character_id
            or value["scheme_instance_id"] != scheme_instance_id
            or value["after_sequence"] != after_sequence):
        raise ValueError("native sway termination differs from its exact query identity")
    records = []
    for record in value["records"]:
        if not isinstance(record, dict) or set(record) != _RECORD_KEYS:
            raise ValueError("native sway termination record schema is malformed")
        if (not isinstance(record["source_class"], str) or record["source_class"] not in _SOURCE_CLASSES
                or any(type(record[key]) is not bool for key in _RECORD_BOOL_KEYS)
                or record["executing_source_observed"] is not True
                or record["material_effect_observed"] is not False
                or record["specific_invalidation_reason"] is not None
                or not _integer(record["sequence"], 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(record["date_raw"], -(1 << 31), (1 << 31) - 1)
                or not _integer(record["input_root_scope_kind"], 0, 0xFFFF)
                or not _integer(record["pre_status"], -(1 << 31), (1 << 31) - 1)
                or not _integer(record["pre_owner"], 0, 0xFFFFFFFF)
                or not _integer(record["scheme_instance_generation"], 0, 255)
                or record["scheme_instance_generation"] != scheme_instance_id >> 24
                or any(type(record[key]) is not int or record[key] != value[key]
                       for key in ("actor_character_id", "target_character_id", "scheme_instance_id"))):
            raise ValueError("native sway termination record fields are malformed")
        for key, minimum, maximum in (
            ("post_status", -(1 << 31), (1 << 31) - 1),
            ("post_owner", 0, 0xFFFFFFFF),
        ):
            if (record["post_status_observed"] and not _integer(record[key], minimum, maximum)
                    or not record["post_status_observed"] and record[key] is not None):
                raise ValueError("native sway termination nullable post-state is malformed")
        # Source class, observed terminal state and observed transition are
        # separate producer facts. Absence and original return add no cause.
        records.append(dict(record))
    return {**value, "records": records}


def query_active_scheme_sway_completion_termination_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if (not _integer(expected_revision, 1, 0xFFFFFFFFFFFFFFFF)
            or not _integer(target_character_id, 1, (1 << 31) - 1)
            or not _integer(scheme_instance_id, 0, 0xFFFFFFFE)
            or not _integer(after_sequence, 0, 0xFFFFFFFFFFFFFFFF)):
        raise ValueError("private sway termination revision/target/full instance/sequence is invalid")
    actor = driver.take_snapshot().get("played_character")
    if not isinstance(actor, Mapping) or not _integer(actor.get("character_id"), 1, (1 << 31) - 1):
        raise BridgeUnavailableError("private sway termination lacks the current player identity")
    if actor["character_id"] == target_character_id:
        raise ValueError("private sway termination target must differ from the current player")
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"actor_character_id": actor["character_id"],
                        "target_character_id": target_character_id,
                        "scheme_instance_id": scheme_instance_id,
                        "after_sequence": after_sequence},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_build(result.get("build_version"), result.get("executable_sha256"))
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("backend_id") != "native-headless"
                or not _integer(result.get("snapshot_revision"), 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(result.get("date_raw"), -(1 << 31), (1 << 31) - 1)
                or result["snapshot_revision"] != before.get("native_revision")
                or result["date_raw"] != before.get("date_raw")):
            raise ValueError("native sway termination belongs to another build/frame")
        value = normalize_active_scheme_sway_completion_termination_v1(
            result.get("sway_completion_termination"), snapshot=before,
            target_character_id=target_character_id, scheme_instance_id=scheme_instance_id,
            after_sequence=after_sequence,
        )
        if result.get("status") != ("available" if value["available"] else "unavailable"):
            raise ValueError("native sway termination envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        **{key: result[key] for key in (
            "backend_id", "status", "snapshot_revision", "date_raw", "build_version",
            "executable_sha256", "private_build", "advertised",
        )},
    }
