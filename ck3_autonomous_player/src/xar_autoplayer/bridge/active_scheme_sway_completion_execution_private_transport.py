"""Read copied hidden Sway executing-source records for an exact instance."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, private_g2_query_snapshot_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_build


STEP = "query-sway-completion-execution-v1-private"
SCHEMA = "xar.ck3.sway-completion-execution.v1"
PERMISSION = "allow_private_active_scheme_sway_completion_execution_query"
_CONTEXT_KEYS = {
    "schema", "available", "unavailable_reason", "read_only", "observer_attached",
    "actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence",
    "earliest_sequence", "latest_sequence", "retention_gap", "material_effect_observed",
    "native_terminal_state_observed", "records",
}
_RECORD_KEYS = {
    "sequence", "date_raw", "actor_character_id", "target_character_id",
    "scheme_instance_id", "scheme_instance_generation", "source_branch", "stock_event",
    "executing_input_observed", "exact_scope_join_ready", "phase_result",
    "message_enqueue_observed", "material_effect_observed", "native_terminal_state_observed",
}
_BRANCHES = {
    "hidden_phase_success_source": ("sway_outcome.0001", "success"),
    "hidden_phase_failure_source": ("sway_outcome.0002", "failure"),
}


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_active_scheme_sway_completion_execution_v1(
    value: object, *, snapshot: Mapping[str, object], target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0,
) -> dict[str, object]:
    """Copy native execution facts without deriving material or terminal outcomes."""
    if (not isinstance(value, dict) or set(value) != _CONTEXT_KEYS
            or value["schema"] != SCHEMA):
        raise ValueError("native sway execution schema is malformed")
    bool_keys = (
        "available", "read_only", "observer_attached", "retention_gap",
        "material_effect_observed", "native_terminal_state_observed",
    )
    if (any(type(value[key]) is not bool for key in bool_keys)
            or not isinstance(value["unavailable_reason"], str)
            or value["read_only"] is not True
            or value["material_effect_observed"] is not False
            or value["native_terminal_state_observed"] is not False
            or not _integer(value["actor_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["target_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["scheme_instance_id"], 0, 0xFFFFFFFE)
            or any(not _integer(value[key], 0, 0xFFFFFFFFFFFFFFFF)
                   for key in ("after_sequence", "earliest_sequence", "latest_sequence"))
            or not isinstance(value["records"], list)):
        raise ValueError("native sway execution scalar fields are malformed")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value["actor_character_id"] != actor.get("character_id")
            or value["target_character_id"] != target_character_id
            or value["scheme_instance_id"] != scheme_instance_id
            or value["after_sequence"] != after_sequence):
        raise ValueError("native sway execution differs from its exact query identity")
    records = []
    for record in value["records"]:
        if not isinstance(record, dict) or set(record) != _RECORD_KEYS:
            raise ValueError("native sway execution record schema is malformed")
        branch = _BRANCHES.get(record["source_branch"]) if isinstance(record["source_branch"], str) else None
        if (not _integer(record["sequence"], 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(record["date_raw"], -(1 << 31), (1 << 31) - 1)
                or not _integer(record["scheme_instance_generation"], 0, 255)
                or record["scheme_instance_generation"] != scheme_instance_id >> 24
                or any(type(record[key]) is not int or record[key] != value[key]
                       for key in ("actor_character_id", "target_character_id", "scheme_instance_id"))
                or branch != (record["stock_event"], record["phase_result"])
                or record["executing_input_observed"] is not True
                or record["exact_scope_join_ready"] is not True
                or any(record[key] is not False for key in (
                    "message_enqueue_observed", "material_effect_observed", "native_terminal_state_observed",
                ))):
            raise ValueError("native sway execution record fields are malformed")
        records.append(dict(record))
    return {**value, "records": records}


def query_active_scheme_sway_completion_execution_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if (not _integer(expected_revision, 1, 0xFFFFFFFFFFFFFFFF)
            or not _integer(target_character_id, 1, (1 << 31) - 1)
            or not _integer(scheme_instance_id, 0, 0xFFFFFFFE)
            or not _integer(after_sequence, 0, 0xFFFFFFFFFFFFFFFF)):
        raise ValueError("private sway execution revision/target/full instance/sequence is invalid")
    actor = private_g2_query_snapshot_v1(
        driver, include_native_command_history=False).get("played_character")
    if not isinstance(actor, Mapping) or not _integer(actor.get("character_id"), 1, (1 << 31) - 1):
        raise BridgeUnavailableError("private sway execution lacks the current player identity")
    if actor["character_id"] == target_character_id:
        raise ValueError("private sway execution target must differ from the current player")
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"actor_character_id": actor["character_id"],
                        "target_character_id": target_character_id,
                        "scheme_instance_id": scheme_instance_id,
                        "after_sequence": after_sequence},
        timeout_seconds=timeout_seconds, include_native_command_history=False,
    )
    try:
        build = require_exact_native_build(result.get("build_version"), result.get("executable_sha256"))
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("backend_id") != "native-headless"
                or not _integer(result.get("snapshot_revision"), 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(result.get("date_raw"), -(1 << 31), (1 << 31) - 1)
                or result["snapshot_revision"] != before.get("native_revision")
                or result["date_raw"] != before.get("date_raw")):
            raise ValueError("native sway execution belongs to another build/frame")
        value = normalize_active_scheme_sway_completion_execution_v1(
            result.get("sway_completion_execution"), snapshot=before,
            target_character_id=target_character_id, scheme_instance_id=scheme_instance_id,
            after_sequence=after_sequence,
        )
        if result.get("status") != ("available" if value["available"] else "unavailable"):
            raise ValueError("native sway execution envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        **{key: result[key] for key in (
            "backend_id", "status", "snapshot_revision", "date_raw", "build_version",
            "executable_sha256", "private_build", "advertised",
        )},
    }
