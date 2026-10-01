"""Read copied selected Sway invalidation notification inputs for a full ID."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, require_exact_native_build


STEP = "query-sway-completion-invalidation-reason-v1-private"
SCHEMA = "xar.ck3.sway-invalidation-notification-source.v1"
PERMISSION = "allow_private_active_scheme_sway_completion_invalidation_reason_query"
_OUTCOME_KEYS = (
    "message_enqueue_observed", "render_observed", "material_effect_observed",
    "native_end_cause_observed", "native_terminal_state_observed",
)
_CONTEXT_KEYS = {
    "schema", "available", "unavailable_reason", "read_only", "observer_attached",
    "actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence",
    "earliest_sequence", "latest_sequence", "retention_gap", "session_records_only",
    *_OUTCOME_KEYS, "records",
}
_RECORD_KEYS = {
    "sequence", "source_branch", "authored_command", "authored_title", "authored_reason_key",
    "date_raw", "actor_character_id", "target_character_id", "scheme_instance_id",
    "scheme_instance_generation", "root_scope_kind", "scheme_scope_kind",
    "selected_notification_branch_observed", "exact_scope_join_ready", *_OUTCOME_KEYS,
}
_BRANCH_KEYS = {
    "target_dead_notification_source": "sway_invalidated_dead",
    "out_of_range_notification_source": "scheme_target_not_in_diplomatic_range",
    "opaque_existing_stock_notification_source": "sway_invalidated_war",
}


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_active_scheme_sway_completion_invalidation_reason_v1(
    value: object, *, snapshot: Mapping[str, object], target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0,
) -> dict[str, object]:
    """Copy the selected authored branch without deriving a universal end cause."""
    if (not isinstance(value, dict) or set(value) != _CONTEXT_KEYS
            or value["schema"] != SCHEMA):
        raise ValueError("native sway invalidation notification schema is malformed")
    if (any(type(value[key]) is not bool for key in (
                "available", "read_only", "observer_attached", "retention_gap", "session_records_only",
            ))
            or any(value[key] is not False for key in _OUTCOME_KEYS)
            or not isinstance(value["unavailable_reason"], str)
            or value["read_only"] is not True or value["session_records_only"] is not True
            or not _integer(value["actor_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["target_character_id"], 1, (1 << 31) - 1)
            or not _integer(value["scheme_instance_id"], 0, 0xFFFFFFFE)
            or any(not _integer(value[key], 0, 0xFFFFFFFFFFFFFFFF)
                   for key in ("after_sequence", "earliest_sequence", "latest_sequence"))
            or not isinstance(value["records"], list)):
        raise ValueError("native sway invalidation notification scalar fields are malformed")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value["actor_character_id"] != actor.get("character_id")
            or value["target_character_id"] != target_character_id
            or value["scheme_instance_id"] != scheme_instance_id
            or value["after_sequence"] != after_sequence):
        raise ValueError("native sway invalidation notification differs from its exact query identity")
    records = []
    for record in value["records"]:
        if not isinstance(record, dict) or set(record) != _RECORD_KEYS:
            raise ValueError("native sway invalidation notification record schema is malformed")
        reason = _BRANCH_KEYS.get(record["source_branch"]) if isinstance(record["source_branch"], str) else None
        if (reason is None or record["authored_reason_key"] != reason
                or record["authored_command"] != "send_interface_toast"
                or record["authored_title"] != "sway_invalidated_title"
                or not _integer(record["sequence"], 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(record["date_raw"], -(1 << 31), (1 << 31) - 1)
                or not _integer(record["scheme_instance_generation"], 0, 255)
                or record["scheme_instance_generation"] != scheme_instance_id >> 24
                or type(record["root_scope_kind"]) is not int or record["root_scope_kind"] != 4
                or type(record["scheme_scope_kind"]) is not int or record["scheme_scope_kind"] != 9
                or any(type(record[key]) is not int or record[key] != value[key]
                       for key in ("actor_character_id", "target_character_id", "scheme_instance_id"))
                or record["selected_notification_branch_observed"] is not True
                or record["exact_scope_join_ready"] is not True
                or any(record[key] is not False for key in _OUTCOME_KEYS)):
            raise ValueError("native sway invalidation notification record fields are malformed")
        # This is selected notification input. Keep the opaque stock key opaque;
        # no render/history/material, current status or universal cause is added.
        records.append(dict(record))
    return {**value, "records": records}


def query_active_scheme_sway_completion_invalidation_reason_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if (not _integer(expected_revision, 1, 0xFFFFFFFFFFFFFFFF)
            or not _integer(target_character_id, 1, (1 << 31) - 1)
            or not _integer(scheme_instance_id, 0, 0xFFFFFFFE)
            or not _integer(after_sequence, 0, 0xFFFFFFFFFFFFFFFF)):
        raise ValueError("private sway invalidation revision/target/full instance/sequence is invalid")
    actor = driver.take_snapshot().get("played_character")
    if not isinstance(actor, Mapping) or not _integer(actor.get("character_id"), 1, (1 << 31) - 1):
        raise BridgeUnavailableError("private sway invalidation lacks the current player identity")
    if actor["character_id"] == target_character_id:
        raise ValueError("private sway invalidation target must differ from the current player")
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
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("backend_id") != "native-headless"
                or not _integer(result.get("snapshot_revision"), 1, 0xFFFFFFFFFFFFFFFF)
                or not _integer(result.get("date_raw"), -(1 << 31), (1 << 31) - 1)
                or result["snapshot_revision"] != before.get("native_revision")
                or result["date_raw"] != before.get("date_raw")):
            raise ValueError("native sway invalidation notification belongs to another build/frame")
        value = normalize_active_scheme_sway_completion_invalidation_reason_v1(
            result.get("sway_completion_invalidation_reason"), snapshot=before,
            target_character_id=target_character_id, scheme_instance_id=scheme_instance_id,
            after_sequence=after_sequence,
        )
        if result.get("status") != ("available" if value["available"] else "unavailable"):
            raise ValueError("native sway invalidation notification envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        **{key: result[key] for key in (
            "backend_id", "status", "snapshot_revision", "date_raw", "build_version",
            "executable_sha256", "private_build", "advertised",
        )},
    }
