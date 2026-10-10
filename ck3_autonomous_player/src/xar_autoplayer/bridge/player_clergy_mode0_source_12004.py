"""Decode the optional actual4 clergy source packet from the existing query."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12004, require_exact_native_build


FIELD_NAME = "clergy_mode0_source"
SCHEMA = "xar.ck3.clergy-mode0-source-inputs-12004/v1"
_FIELDS = {
    "schema", "schema_version", "source_executable_sha256", "capture_scope",
    "capture_epoch", "date_raw", "owner_character_id", "candidate_character_id",
    "active_task_id", "incumbent_character_id", "position_key", "input_scope_confirmed",
    "source_read_frame", "sourceproof", "inputs", "generic_trigger",
}
_FRAME_FIELDS = {
    "frame_identity", "snapshot_identity", "native_revision", "query_sequence",
    "proof_epoch", "date_raw", "caller_domain", "caller_snapshot_confirmed", "ready",
}
_PROOF_FIELDS = {
    "producer_rva", "source_projected", "source_ready",
    "native_callee_invocation_observed", "natural_return_witness", "native_calls_added",
}
_INPUT_FIELDS = {
    "owner_id_raw32", "incumbent_id_raw32", "compared_id_raw32", "initial_raw_al",
    "position_raw_al", "final_raw_al", "raw_al", "branch", "unavailable_input",
}
_GENERIC_FIELDS = {
    "software_adapter_invoked", "copied_frame_ready", "copied_inputs_ready",
    "source_value_ready", "scope_root_word", "scope_full_id_payload",
    "evaluation_flag_raw_u8", "raw_al", "unavailable_input",
}


def _object(value: object, fields: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"native clergy source object is malformed: {name}")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"native clergy source integer is malformed: {name}")


def _nullable_integer(value: object, name: str, minimum: int, maximum: int) -> None:
    if value is not None:
        _integer(value, name, minimum, maximum)


def _bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"native clergy source flag is malformed: {name}")


def normalize_player_clergy_mode0_source_12004(
    value: object, *, snapshot: Mapping[str, object], clergy: Mapping[str, object],
) -> dict[str, object] | None:
    """Preserve owned source facts, nullable bytes and their separate proof levels."""
    # An opted-in query can explicitly lack a publishable packet. Absence is
    # handled by the transport and never calls this decoder.
    if value is None:
        return None
    packet = _object(value, _FIELDS, FIELD_NAME)
    if (packet["schema"] != SCHEMA or type(packet["schema_version"]) is not int
            or packet["schema_version"] != 1
            or packet["source_executable_sha256"] != CK3_12004.executable_sha256):
        raise ValueError("native clergy source schema or exact source image is malformed")
    exact = clergy.get("exact_build")
    if (not isinstance(exact, Mapping)
            or require_exact_native_build(exact.get("game_version"), exact.get("executable_sha256"))
            != CK3_12004 or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native clergy source requires the same actual4 query build")
    if (packet["capture_scope"] not in (
            "occupied_seat_mode0_software_projection", "seat_absent", "seat_vacant")
            or packet["position_key"] != "councillor_court_chaplain"):
        raise ValueError("native clergy source capture scope is malformed")
    _bool(packet["input_scope_confirmed"], "input_scope_confirmed")
    _integer(packet["capture_epoch"], "capture_epoch", 0, (1 << 64) - 1)
    for key in ("date_raw", "owner_character_id", "candidate_character_id"):
        _integer(packet[key], key, -(1 << 31), (1 << 31) - 1)
    for key in ("active_task_id", "incumbent_character_id"):
        _nullable_integer(packet[key], key, -(1 << 31), (1 << 31) - 1)
    # These are the same query's copied identifiers, including generation
    # bits. Task raw32 operands below remain independent source inputs.
    if any(packet[key] != clergy.get(key) for key in (
            "capture_epoch", "date_raw", "owner_character_id", "candidate_character_id",
            "active_task_id", "incumbent_character_id")):
        raise ValueError("native clergy source differs from its original query seat")

    frame = _object(packet["source_read_frame"], _FRAME_FIELDS, "source_read_frame")
    for key in ("native_revision", "query_sequence", "proof_epoch"):
        _integer(frame[key], key, 0, (1 << 64) - 1)
    _integer(frame["date_raw"], "source_read_frame.date_raw", -(1 << 31), (1 << 31) - 1)
    _bool(frame["caller_snapshot_confirmed"], "caller_snapshot_confirmed")
    # The current Snapshot/Core/Envelope has no original identity carrier.
    # Counters and the derived candidate snapshot label cannot fill this gap.
    if (frame["frame_identity"] is not None or frame["snapshot_identity"] is not None
            or frame["ready"] is not False
            or frame["caller_domain"] != "player_clergy_appointment_v1"):
        raise ValueError("native clergy source invented an original frame identity")
    if (frame["native_revision"] != snapshot.get("native_revision")
            or frame["proof_epoch"] != packet["capture_epoch"]
            or frame["date_raw"] != packet["date_raw"]):
        raise ValueError("native clergy source query metadata belongs to another frame")

    proof = _object(packet["sourceproof"], _PROOF_FIELDS, "sourceproof")
    _integer(proof["producer_rva"], "producer_rva", 0, (1 << 64) - 1)
    if proof["producer_rva"] != 0x31B4A10:
        raise ValueError("native clergy source producer RVA is malformed")
    for key in ("source_projected", "source_ready"):
        _bool(proof[key], key)
    if any(proof[key] is not False for key in (
            "native_callee_invocation_observed", "natural_return_witness", "native_calls_added")):
        raise ValueError("native clergy source acquired an unsupported natural invocation claim")

    inputs = _object(packet["inputs"], _INPUT_FIELDS, "inputs")
    for key in ("owner_id_raw32", "incumbent_id_raw32", "compared_id_raw32"):
        _nullable_integer(inputs[key], key, 0, (1 << 32) - 1)
    for key in ("initial_raw_al", "position_raw_al", "final_raw_al", "raw_al"):
        _nullable_integer(inputs[key], key, 0, 255)
    if (inputs["branch"] not in (
            "unavailable", "initial_nonzero_returns_zero", "position_zero_returns_zero", "final_raw_al")
            or not isinstance(inputs["unavailable_input"], str)):
        raise ValueError("native clergy source branch or unavailable input is malformed")
    if (inputs["unavailable_input"] == "") is not (inputs["raw_al"] is not None):
        raise ValueError("native clergy source lost its unavailable byte reason")

    generic = _object(packet["generic_trigger"], _GENERIC_FIELDS, "generic_trigger")
    for key in ("software_adapter_invoked", "copied_frame_ready", "copied_inputs_ready", "source_value_ready"):
        _bool(generic[key], key)
    _nullable_integer(generic["scope_root_word"], "scope_root_word", 0, (1 << 16) - 1)
    _nullable_integer(generic["scope_full_id_payload"], "scope_full_id_payload", 0, (1 << 64) - 1)
    for key in ("evaluation_flag_raw_u8", "raw_al"):
        _nullable_integer(generic[key], "generic_trigger." + key, 0, 255)
    if not isinstance(generic["unavailable_input"], str):
        raise ValueError("native clergy generic trigger reason is malformed")
    # No coercion, arithmetic, eligibility or aggregate native_can_fire
    # calculation is performed. Unreached/null facts remain null.
    return deepcopy(packet)


def player_clergy_mode0_source_from_query_12004(
    result: Mapping[str, object], *, snapshot: Mapping[str, object], clergy: Mapping[str, object],
) -> dict[str, object]:
    """Reject a malformed optional sibling without erasing the base observation."""
    if FIELD_NAME not in result:
        return {}
    try:
        return {FIELD_NAME: normalize_player_clergy_mode0_source_12004(
            result[FIELD_NAME], snapshot=snapshot, clergy=clergy)}
    except ValueError as error:
        return {FIELD_NAME: None, FIELD_NAME + "_error": str(error)}
