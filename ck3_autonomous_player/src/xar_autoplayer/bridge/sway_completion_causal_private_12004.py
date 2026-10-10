"""Validate copied actual4 dynamic Sway parent/end relationships."""

from __future__ import annotations

from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build


COMPLETE_BRANCH = "authored_sway_complete_100_source"
SOURCE_CONTRACT = "sway_child_end_causal_path_12004_v1"
_END_RVAS = {
    "end_scheme_command_execute": 0x299C320,
    "authored_end_scheme_false_execute": 0x2D11B30,
    "authored_end_scheme_true_execute": 0x2D11AD0,
}


def _uint(value: object, bits: int = 64, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value < 1 << bits


def normalize_sway_complete_invocation_12004(
    value: object, record: Mapping[str, object],
) -> dict[str, object]:
    keys = {"observer_session_identity", "owner_thread_id", "toast_invocation_id",
            "branch_source_sequence", "copied_scopes"}
    if (not isinstance(value, dict) or set(value) != keys
            or not _uint(value["observer_session_identity"], minimum=1)
            or not _uint(value["owner_thread_id"], 32, 1)
            or not _uint(value["toast_invocation_id"], minimum=1)
            or not _uint(value["branch_source_sequence"], minimum=1)
            or value["branch_source_sequence"] != record["sequence"]
            or not isinstance(value["copied_scopes"], dict)
            or set(value["copied_scopes"]) != {"root", "owner", "target", "scheme"}):
        raise ValueError("actual4 sway complete invocation is malformed")
    scopes = {}
    identities = {"root": (4, record["actor_character_id"]),
                  "owner": (4, record["actor_character_id"]),
                  "target": (4, record["target_character_id"]),
                  "scheme": (9, record["scheme_instance_id"])}
    for key, (kind, identity) in identities.items():
        token = value["copied_scopes"][key]
        if (not isinstance(token, dict) or set(token) != {"type", "subtype", "reserved", "payload"}
                or not _uint(token["type"], 16) or token["type"] != kind
                or not _uint(token["subtype"], 16) or not _uint(token["reserved"], 32)
                or not _uint(token["payload"]) or token["payload"] & 0xFFFFFFFF != identity):
            raise ValueError("actual4 sway complete copied scope differs from full identity")
        scopes[key] = dict(token)
    return {**value, "copied_scopes": scopes}


def normalize_sway_end_invocation_12004(
    value: object, record: Mapping[str, object],
) -> dict[str, object]:
    keys = {"observer_session_identity", "owner_thread_id", "original_invocation_id",
            "original_rva", "incoming_return_address_observed", "caller_return_rva",
            "original_forwarded_once", "original_returned", "pre_frame_observed",
            "pre_date_raw", "post_frame_observed", "post_date_raw"}
    if (not isinstance(value, dict) or set(value) != keys
            or not _uint(value["observer_session_identity"], minimum=1)
            or not _uint(value["owner_thread_id"], 32, 1)
            or not _uint(value["original_invocation_id"], minimum=1)
            or not _uint(value["original_rva"])
            or value["original_rva"] != _END_RVAS.get(record["source_class"])
            or not _uint(value["caller_return_rva"])
            or any(type(value[key]) is not bool for key in (
                "incoming_return_address_observed", "original_forwarded_once", "original_returned",
                "pre_frame_observed", "post_frame_observed"))
            or value["original_forwarded_once"] is not True
            or value["original_returned"] is not True
            or value["pre_frame_observed"] is not True
            or value["pre_date_raw"] != record["date_raw"]
            or not value["incoming_return_address_observed"] and value["caller_return_rva"] != 0):
        raise ValueError("actual4 sway original end invocation is malformed")
    for observed, date in (("pre_frame_observed", "pre_date_raw"), ("post_frame_observed", "post_date_raw")):
        if (value[observed] and (type(value[date]) is not int or not -(1 << 31) <= value[date] < 1 << 31)
                or not value[observed] and value[date] is not None):
            raise ValueError("actual4 sway original end frame is malformed")
    return dict(value)


def normalize_sway_end_relation_12004(
    value: object, record: Mapping[str, object], invocation: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    keys = {"source_contract", "source_contract_version", "relationship_observed",
            "observer_session_identity", "owner_thread_id", "branch_source_sequence",
            "parent_toast_invocation_id", "end_original_invocation_id", "end_original_rva",
            "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation",
            "native_returns_observed", "native_returns_truncated", "native_return_rvas"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["source_contract"] != SOURCE_CONTRACT
            or type(value["source_contract_version"]) is not int or value["source_contract_version"] != 1
            or value["relationship_observed"] is not True
            or value["native_returns_observed"] is not True
            or value["native_returns_truncated"] is not False
            or not _uint(value["branch_source_sequence"], minimum=1)
            or not _uint(value["parent_toast_invocation_id"], minimum=1)
            or any(type(value[key]) is not int or value[key] != record[key] for key in (
                "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"))
            or any(type(value[key]) is not int or value[key] != invocation[key] for key in (
                "observer_session_identity", "owner_thread_id"))
            or value["end_original_invocation_id"] != invocation["original_invocation_id"]
            or type(value["end_original_invocation_id"]) is not int
            or value["end_original_rva"] != invocation["original_rva"]
            or type(value["end_original_rva"]) is not int
            or record["source_class"] not in ("authored_end_scheme_false_execute", "authored_end_scheme_true_execute")
            or record["input_root_scope_kind"] != 9
            or invocation["incoming_return_address_observed"] is not True
            or invocation["caller_return_rva"] != 0x2D67C04
            or not isinstance(value["native_return_rvas"], list)
            or not 3 <= len(value["native_return_rvas"]) <= 32
            or any(not _uint(rva) for rva in value["native_return_rvas"])
            or value["native_return_rvas"][0] != 0x2D67C04):
        raise ValueError("actual4 sway causal relationship is malformed")
    # The nearest Toast edge is the barrier; an outer match cannot be borrowed.
    returns = value["native_return_rvas"]
    try:
        nearest_toast = returns.index(0x2CC93CC)
        dispatcher = returns.index(0x3766146)
    except ValueError as error:
        raise ValueError("actual4 sway causal relationship lacks native source edges") from error
    if not 0 < dispatcher < nearest_toast:
        raise ValueError("actual4 sway causal relationship crosses the nearest Toast barrier")
    return {**value, "native_return_rvas": list(returns)}


def consume_sway_end_causal_12004(
    *, execution_read: Mapping[str, object], termination_read: Mapping[str, object],
) -> dict[str, object] | None:
    """Join source records by explicit dynamic identity, independently of material."""
    if (execution_read.get("schema") != "xar.ck3.sway-completion-execution.v1"
            or termination_read.get("schema") != "xar.ck3.sway-completion-termination.v1"
            or any(read.get("available") is not True or read.get("retention_gap") is not False
                   for read in (execution_read, termination_read))):
        return None
    for read in (execution_read, termination_read):
        if require_exact_native_build(read.get("build_version"), read.get("executable_sha256")) != CK3_12004:
            return None
    if any(execution_read.get(key) != termination_read.get(key) for key in (
            "actor_character_id", "target_character_id", "scheme_instance_id")):
        return None
    sources = {}
    for record in execution_read["records"]:
        if record["source_branch"] != COMPLETE_BRANCH:
            continue
        if (any(type(record.get(field)) is not int or record[field] != execution_read.get(field)
                for field in ("actor_character_id", "target_character_id", "scheme_instance_id"))
                or type(record.get("scheme_instance_generation")) is not int
                or record["scheme_instance_generation"] != execution_read["scheme_instance_id"] >> 24):
            raise ValueError("actual4 sway completion record differs from its query identity")
        if (record.get("stock_event") is not None or record.get("phase_result") is not None
                or record.get("executing_input_observed") is not True
                or record.get("exact_scope_join_ready") is not True
                or any(record.get(key) is not False for key in (
                    "message_enqueue_observed", "material_effect_observed", "native_terminal_state_observed"))):
            raise ValueError("actual4 sway authored completion source is malformed")
        stamp = normalize_sway_complete_invocation_12004(record.get("native_invocation"), record)
        key = (stamp["observer_session_identity"], stamp["owner_thread_id"],
               stamp["toast_invocation_id"], stamp["branch_source_sequence"])
        if key in sources:
            raise ValueError("actual4 sway completion source dynamic identity is duplicated")
        sources[key] = record
    for record in reversed(termination_read["records"]):
        if "native_invocation" not in record:
            continue
        if (any(type(record.get(field)) is not int or record[field] != termination_read.get(field)
                for field in ("actor_character_id", "target_character_id", "scheme_instance_id"))
                or type(record.get("scheme_instance_generation")) is not int
                or record["scheme_instance_generation"] != termination_read["scheme_instance_id"] >> 24):
            raise ValueError("actual4 sway end record differs from its query identity")
        invocation = normalize_sway_end_invocation_12004(record["native_invocation"], record)
        relation = normalize_sway_end_relation_12004(record.get("cause_relation"), record, invocation)
        if relation is None:
            continue
        key = (relation["observer_session_identity"], relation["owner_thread_id"],
               relation["parent_toast_invocation_id"], relation["branch_source_sequence"])
        parent = sources.get(key)
        if (parent is None or any(parent.get(field) != record.get(field) for field in (
                "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"))
                or type(record.get("pre_status")) is not int or record["pre_status"] != 0
                or type(record.get("post_status")) is not int or record["post_status"] != 1
                or type(record.get("pre_owner")) is not int or record["pre_owner"] != record["actor_character_id"]
                or type(record.get("post_owner")) is not int
                or record["post_owner"] not in (record["actor_character_id"], 0xFFFFFFFF)
                or any(record.get(field) is not True for field in (
                    "executing_source_observed", "post_read_succeeded", "post_instance_present",
                    "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed",
                    "native_terminal_transition_observed"))
                or record.get("post_storage_slot_reused") is not False
                or invocation["post_frame_observed"] is not True
                or invocation["pre_date_raw"] != parent["date_raw"]
                or invocation["post_date_raw"] != invocation["pre_date_raw"]):
            continue
        return {
            "schema": "xar.ck3.sway-end-causal-observation.12004.v1",
            "actor_character_id": record["actor_character_id"],
            "target_character_id": record["target_character_id"],
            "scheme_instance_id": record["scheme_instance_id"],
            "scheme_instance_generation": record["scheme_instance_generation"],
            "cause_key": COMPLETE_BRANCH, "terminal_cause_observed": True,
            "native_status_key": "terminated_attributed", "native_status_raw": 1,
            "native_terminal_transition_observed": True, "material_effect_observed": False,
            "observer_session_identity": relation["observer_session_identity"],
            "owner_thread_id": relation["owner_thread_id"],
            "branch_source_sequence": relation["branch_source_sequence"],
            "parent_toast_invocation_id": relation["parent_toast_invocation_id"],
            "end_original_invocation_id": relation["end_original_invocation_id"],
            "execution_record": dict(parent), "termination_record": dict(record),
        }
    # Honest unknown: a retained terminal alone never obtains a cause key.
    return None
