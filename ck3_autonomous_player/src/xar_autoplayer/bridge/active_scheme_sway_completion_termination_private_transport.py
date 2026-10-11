"""Read copied native Sway termination-source pre/post observations."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .sway_completion_causal_private_12004 import normalize_sway_end_invocation_12004, normalize_sway_end_relation_12004
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_build


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



_COMMON_NATIVE_END_KEY = "common_native_end"
_COMMON_FAMILY_KEYS = {
    "schema", "source_contract", "available", "unavailable_reason", "read_only",
    "observer_attached", "observer_session_identity", "owner_thread_id",
    "actor_character_id", "target_character_id", "scheme_instance_id",
    "scheme_instance_generation", "after_sequence", "earliest_sequence",
    "latest_sequence", "retention_gap", "session_records_only", "records",
}
_COMMON_RECORD_KEYS = {
    "sequence", "observer_session_identity", "owner_thread_id", "original_invocation_id",
    "callsite_rva", "callee_rva", "call_return_rva", "incoming_return_address_observed",
    "caller_return_rva", "incoming_dl_observed", "incoming_dl_raw_u8", "entry",
    "original_forwarded_once", "original_returned", "returned",
    "return_same_scheme_full_id_observed", "return_same_scheme_full_id",
}
_COMMON_FRAME_KEYS = {
    "scheme_header_observed", "scheme_full_id_observed", "scheme_full_id_raw_u32",
    "scheme_instance_generation_u8", "status_observed", "status_raw_i32",
    "owner_observed", "owner_character_full_id_raw_u32", "other_kind_observed",
    "other_kind_raw_u32", "target_observed", "target_character_full_id_raw_u32",
    "core_frame_observed", "core_frame",
}
_COMMON_CORE_KEYS = {"date_raw", "speed", "paused", "local_player_id", "map_ready",
                     "has_played_character", "played_character_id", "played_character_alive"}


def _normalize_common_native_end_frame_12004(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _COMMON_FRAME_KEYS:
        raise ValueError("common native end frame schema is malformed")
    for key in ("scheme_header_observed", "scheme_full_id_observed", "status_observed",
                "owner_observed", "other_kind_observed", "target_observed", "core_frame_observed"):
        if type(value[key]) is not bool:
            raise ValueError("common native end frame read flag is malformed")
    for flag, key, minimum, maximum in (
        ("scheme_full_id_observed", "scheme_full_id_raw_u32", 0, 0xFFFFFFFF),
        ("scheme_full_id_observed", "scheme_instance_generation_u8", 0, 255),
        ("status_observed", "status_raw_i32", -(1 << 31), (1 << 31) - 1),
        ("owner_observed", "owner_character_full_id_raw_u32", 0, 0xFFFFFFFF),
        ("other_kind_observed", "other_kind_raw_u32", 0, 0xFFFFFFFF),
        ("target_observed", "target_character_full_id_raw_u32", 0, 0xFFFFFFFF),
    ):
        if (value[flag] and not _integer(value[key], minimum, maximum)
                or not value[flag] and value[key] is not None):
            raise ValueError("common native end nullable raw field is malformed")
    if (value["scheme_full_id_observed"]
            and value["scheme_instance_generation_u8"] != value["scheme_full_id_raw_u32"] >> 24):
        raise ValueError("common native end generation differs from its full ID")
    if value["target_observed"] and not (value["other_kind_observed"] and value["other_kind_raw_u32"] == 0):
        raise ValueError("common native end character target has no observed kind0")
    core = value["core_frame"]
    if value["core_frame_observed"]:
        if (not isinstance(core, dict) or set(core) != _COMMON_CORE_KEYS
                or any(not _integer(core[key], -(1 << 31), (1 << 31) - 1)
                       for key in ("date_raw", "speed", "local_player_id", "played_character_id"))
                or any(type(core[key]) is not bool for key in
                       ("paused", "map_ready", "has_played_character", "played_character_alive"))):
            raise ValueError("common native end supplied core frame is malformed")
    elif core is not None:
        raise ValueError("common native end missing core frame was filled")
    return {**value, "core_frame": dict(core) if core is not None else None}


def normalize_sway_common_native_end_12004(
    value: object, context: Mapping[str, object],
) -> dict[str, object]:
    """Preserve the independent common entry/return family without a cause."""
    if (not isinstance(value, dict) or set(value) != _COMMON_FAMILY_KEYS
            or value["schema"] != "xar.ck3.sway-common-native-end.v1"
            or value["source_contract"] != "actual_2a48877_2a4adf0_v1"):
        raise ValueError("common native end family schema is malformed")
    if (any(type(value[key]) is not bool for key in
            ("available", "read_only", "observer_attached", "retention_gap", "session_records_only"))
            or value["read_only"] is not True or value["session_records_only"] is not True
            or not isinstance(value["unavailable_reason"], str)
            or bool(value["unavailable_reason"]) == value["available"]
            or any(not _integer(value[key], 0, 0xFFFFFFFFFFFFFFFF) for key in
                   ("observer_session_identity", "after_sequence", "earliest_sequence", "latest_sequence"))
            or not _integer(value["owner_thread_id"], 0, 0xFFFFFFFF)
            or any(not _integer(value[key], 0, 0xFFFFFFFF) or value[key] != context[key]
                   for key in ("actor_character_id", "target_character_id", "scheme_instance_id"))
            or not _integer(value["scheme_instance_generation"], 0, 255)
            or value["scheme_instance_generation"] != value["scheme_instance_id"] >> 24
            or value["after_sequence"] != 0 or not isinstance(value["records"], list)):
        raise ValueError("common native end family fields are malformed")
    if value["available"] and (not value["observer_attached"]
            or value["observer_session_identity"] == 0 or value["owner_thread_id"] == 0):
        raise ValueError("common native end availability has no admitted session/thread")
    earliest, latest = value["earliest_sequence"], value["latest_sequence"]
    if ((earliest == 0) != (latest == 0) or earliest > latest
            or not value["available"] and value["records"]):
        raise ValueError("common native end independent ring bounds are malformed")
    records = []
    previous_sequence = 0
    for row in value["records"]:
        if not isinstance(row, dict) or set(row) != _COMMON_RECORD_KEYS:
            raise ValueError("common native end record schema is malformed")
        if (any(not _integer(row[key], 1, 0xFFFFFFFFFFFFFFFF) for key in
                ("sequence", "observer_session_identity", "original_invocation_id"))
                or not _integer(row["owner_thread_id"], 1, 0xFFFFFFFF)
                or row["observer_session_identity"] != value["observer_session_identity"]
                or row["owner_thread_id"] != value["owner_thread_id"]
                or not earliest <= row["sequence"] <= latest
                or row["sequence"] <= previous_sequence
                or any(not _integer(row[key], 0, 0xFFFFFFFFFFFFFFFF) or row[key] != rva for key, rva in
                       (("callsite_rva", 0x2A48877), ("callee_rva", 0x2A4ADF0), ("call_return_rva", 0x2A4887C)))
                or any(type(row[key]) is not bool for key in
                       ("incoming_return_address_observed", "incoming_dl_observed", "original_forwarded_once",
                        "original_returned", "return_same_scheme_full_id_observed"))
                or row["incoming_return_address_observed"] is not False or row["caller_return_rva"] is not None):
            raise ValueError("common native end invocation/source provenance is malformed")
        if (row["incoming_dl_observed"] and not _integer(row["incoming_dl_raw_u8"], 0, 255)
                or not row["incoming_dl_observed"] and row["incoming_dl_raw_u8"] is not None):
            raise ValueError("common native end incoming DL was changed or filled")
        entry = _normalize_common_native_end_frame_12004(row["entry"])
        returned = _normalize_common_native_end_frame_12004(row["returned"])
        if (entry["scheme_full_id_observed"] is not True
                or entry["scheme_full_id_raw_u32"] != value["scheme_instance_id"]
                or entry["owner_observed"] is not True
                or entry["owner_character_full_id_raw_u32"] != value["actor_character_id"]
                or entry["target_observed"] is not True
                or entry["target_character_full_id_raw_u32"] != value["target_character_id"]):
            raise ValueError("common native end entry differs from its full query identities")
        same_id = row["return_same_scheme_full_id"]
        if row["return_same_scheme_full_id_observed"]:
            if (type(same_id) is not bool or entry["scheme_header_observed"] is not True
                    or returned["scheme_header_observed"] is not True
                    or entry["scheme_full_id_observed"] is not True
                    or returned["scheme_full_id_observed"] is not True
                    or same_id != (entry["scheme_full_id_raw_u32"] == returned["scheme_full_id_raw_u32"])):
                raise ValueError("common native end full-ID diagnostic is malformed")
        elif same_id is not None:
            raise ValueError("common native end unobserved full-ID diagnostic was filled")
        records.append({**row, "entry": entry, "returned": returned})
        previous_sequence = row["sequence"]
    return {**value, "records": records}


def normalize_active_scheme_sway_completion_termination_v1(
    value: object, *, snapshot: Mapping[str, object], target_character_id: int,
    scheme_instance_id: int, after_sequence: int = 0,
) -> dict[str, object]:
    """Preserve actual source and post-state flags without assigning a cause."""
    if (not isinstance(value, dict) or set(value) not in (_CONTEXT_KEYS, _CONTEXT_KEYS | {_COMMON_NATIVE_END_KEY})
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
        if not isinstance(record, dict) or set(record) not in (_RECORD_KEYS, _RECORD_KEYS | {"native_invocation", "cause_relation"}):
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
        copied = dict(record)
        if "native_invocation" in record:
            copied["native_invocation"] = normalize_sway_end_invocation_12004(record["native_invocation"], record)
            copied["cause_relation"] = normalize_sway_end_relation_12004(record["cause_relation"], record, copied["native_invocation"])
        records.append(copied)
    normalized = {**value, "records": records}
    if _COMMON_NATIVE_END_KEY in value:
        normalized[_COMMON_NATIVE_END_KEY] = normalize_sway_common_native_end_12004(
            value[_COMMON_NATIVE_END_KEY], value,
        )
    return normalized


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
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
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
        if build != CK3_12004 and any("native_invocation" in record for record in value["records"]):
            raise ValueError("original end invocation belongs only to admitted actual4")
        if build != CK3_12004 and _COMMON_NATIVE_END_KEY in value:
            raise ValueError("common native end observation belongs only to admitted actual4")
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
