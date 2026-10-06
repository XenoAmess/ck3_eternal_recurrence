"""Current selected release options, native send costs and answer inputs.

Source-only candidate. No release executor or strategy is supplied here.
Acceptance scores are Q100000 operands, not acceptance probabilities.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping

from .prisoner_release_preview_contract_12003 import (
    RELEASE_COST_KEYS_12003, RELEASE_OPTION_KEYS_12003,
)

_ENVELOPE = {
    "private_build", "read_only", "advertised", "action_surface_present", "status",
    "requested_option_mask_bits",
}
_AVAILABLE = _ENVELOPE | {
    "snapshot_id", "public_revision", "native_revision", "proof_epoch", "date_raw",
    "definition", "payload_shape", "roles", "puppet_or_actor_character_id",
    "option_keys", "selected_option_mask_bits", "can_send", "costs", "acceptance",
    "readiness",
}
_READINESS = {
    "definition_ready", "actor_ready", "recipient_ready", "finalized_context_ready",
    "can_send_ready", "costs_ready", "acceptance_ready", "same_frame_ready",
}
_MAX_MASK = (1 << len(RELEASE_OPTION_KEYS_12003)) - 1


def release_option_mask_12003(option_keys: list[str]) -> int:
    if (not isinstance(option_keys, list) or not option_keys
            or any(type(key) is not str or key not in RELEASE_OPTION_KEYS_12003
                   for key in option_keys)
            or len(set(option_keys)) != len(option_keys)):
        raise ValueError("release_option_keys must be distinct current authored keys")
    return sum(1 << RELEASE_OPTION_KEYS_12003.index(key) for key in option_keys)


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def normalize_prisoner_negotiated_preview_12003(
    preview: Mapping[str, object], *, native_revision: int, date_raw: int,
    player_character_id: int, prisoner_character_id: int,
    requested_option_mask_bits: int,
) -> dict[str, object]:
    if (not _integer(native_revision, 1, 2**64 - 1)
            or not _integer(date_raw, -(2**31), 2**31 - 1)
            or not _integer(player_character_id, 1, 2**32 - 1)
            or not _integer(prisoner_character_id, 1, 2**32 - 1)
            or player_character_id == prisoner_character_id
            or not _integer(requested_option_mask_bits, 1, _MAX_MASK)):
        raise ValueError("negotiated release frame or requested mask is malformed")
    if (not isinstance(preview, Mapping)
            or preview.get("private_build") is not True
            or preview.get("read_only") is not True
            or preview.get("advertised") is not False
            or preview.get("action_surface_present") is not False
            or type(preview.get("requested_option_mask_bits")) is not int
            or preview["requested_option_mask_bits"] != requested_option_mask_bits):
        raise ValueError("negotiated release envelope or request binding is malformed")
    if preview.get("status") == "unavailable":
        keys = _ENVELOPE | {"unavailable_reason"}
        reason = preview.get("unavailable_reason")
        if reason == "requested_release_options_not_retained":
            keys |= {"observed_option_mask_bits"}
            if (not _integer(preview.get("observed_option_mask_bits"), 0, _MAX_MASK)
                    or preview["observed_option_mask_bits"] == requested_option_mask_bits):
                raise ValueError("negotiated release observed mask diagnostic is malformed")
        if set(preview) != keys or type(reason) is not str or not reason:
            raise ValueError("negotiated release unavailable input is malformed")
        return copy.deepcopy(dict(preview))
    if preview.get("status") != "available" or set(preview) != _AVAILABLE:
        raise ValueError("negotiated release available fields are malformed")
    if (preview.get("snapshot_id") != f"native:{native_revision}"
            or type(preview.get("public_revision")) is not int
            or preview["public_revision"] != native_revision
            or type(preview.get("native_revision")) is not int
            or preview["native_revision"] != native_revision
            or type(preview.get("date_raw")) is not int or preview["date_raw"] != date_raw
            or not _integer(preview.get("proof_epoch"), 1, 2**64 - 1)):
        raise ValueError("negotiated release differs from its paused native frame")
    definition = preview.get("definition")
    roles = preview.get("roles")
    if (not isinstance(definition, Mapping)
            or set(definition) != {"canonical_key", "deterministic_key_hash", "runtime_ordinal"}
            or definition.get("canonical_key") != "release_from_prison_interaction"
            or not _integer(definition.get("deterministic_key_hash"), 0, 2**32 - 1)
            or not _integer(definition.get("runtime_ordinal"), 0, 2**31 - 1)
            or not isinstance(roles, Mapping)
            or set(roles) != {"actor_character_id", "recipient_character_id"}
            or type(roles.get("actor_character_id")) is not int
            or roles["actor_character_id"] != player_character_id
            or type(roles.get("recipient_character_id")) is not int
            or roles["recipient_character_id"] != prisoner_character_id
            or type(preview.get("puppet_or_actor_character_id")) is not int
            or preview["puppet_or_actor_character_id"] != player_character_id):
        raise ValueError("negotiated release definition or custody roles are malformed")
    if (preview.get("payload_shape") != "two_role_selected_release_options"
            or preview.get("option_keys") != list(RELEASE_OPTION_KEYS_12003)
            or type(preview.get("selected_option_mask_bits")) is not int
            or preview["selected_option_mask_bits"] != requested_option_mask_bits
            or type(preview.get("can_send")) is not bool):
        raise ValueError("negotiated release finalized selection is malformed")
    costs = preview.get("costs")
    if (not isinstance(costs, Mapping)
            or set(costs) != {"raw_scale", "payer_role", "application_timing", "entries"}
            or type(costs.get("raw_scale")) is not int or costs["raw_scale"] != 100_000
            or costs.get("payer_role") != "actor" or costs.get("application_timing") != "on_send"
            or not isinstance(costs.get("entries"), list)
            or len(costs["entries"]) != len(RELEASE_COST_KEYS_12003)):
        raise ValueError("negotiated release on-send costs are malformed")
    for key, entry in zip(RELEASE_COST_KEYS_12003, costs["entries"], strict=True):
        if (not isinstance(entry, Mapping) or set(entry) != {"resource_key", "raw"}
                or entry.get("resource_key") != key
                or not _integer(entry.get("raw"), -(2**63), 2**63 - 1)):
            raise ValueError("negotiated release cost resource or raw amount is malformed")
    acceptance = preview.get("acceptance")
    if not isinstance(acceptance, Mapping) or type(acceptance.get("auto_accept")) is not bool:
        raise ValueError("negotiated release native acceptance is malformed")
    if not preview["can_send"]:
        if (set(acceptance) != {"kind", "auto_accept"}
                or acceptance.get("kind") != "not_evaluated_unsendable"):
            raise ValueError("unsendable release must retain an observed false gate")
    elif acceptance["auto_accept"]:
        if (set(acceptance) != {"kind", "auto_accept", "would_accept_now"}
                or acceptance.get("kind") != "auto_accept"
                or acceptance.get("would_accept_now") is not True):
            raise ValueError("negotiated release actual auto-accept is malformed")
    elif (set(acceptance) != {"kind", "auto_accept", "raw_scale",
                           "recipient_acceptance_score_raw", "recipient_answer_status_raw",
                           "would_accept_now"}
          or acceptance.get("kind") != "native_answer"
          or type(acceptance.get("raw_scale")) is not int or acceptance["raw_scale"] != 100_000
          or not _integer(acceptance.get("recipient_acceptance_score_raw"), -(2**63), 2**63 - 1)
          or not _integer(acceptance.get("recipient_answer_status_raw"), 0, 2)
          or type(acceptance.get("would_accept_now")) is not bool
          or acceptance["would_accept_now"] != (acceptance["recipient_answer_status_raw"] != 2)):
        raise ValueError("negotiated release final native answer is malformed")
    readiness = preview.get("readiness")
    if (not isinstance(readiness, Mapping) or set(readiness) != _READINESS
            or any(readiness.get(key) is not True for key in _READINESS - {"acceptance_ready"})
            or readiness.get("acceptance_ready") is not preview["can_send"]):
        raise ValueError("negotiated release current-input readiness is malformed")
    return copy.deepcopy(dict(preview))
