"""Validate the current-build, read-only unconditional prisoner release input.

Can Send, compact auto-accept and on-send resource costs are observed inputs.
This contract does not qualify release effects or issue a release command.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping


RELEASE_OPTION_KEYS_12003 = (
    "demand_conversion", "renounce_claims", "banish", "gain_hook",
    "take_vows", "change_prison", "make_puppet", "become_executioner",
    "recruit", "disfigure", "blind", "castrate", "demand_admin",
)
RELEASE_COST_KEYS_12003 = (
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods",
)
_ENVELOPE_KEYS = {
    "private_build", "read_only", "advertised", "action_surface_present",
    "status",
}
_UNAVAILABLE_KEYS = _ENVELOPE_KEYS | {"unavailable_reason"}
_AVAILABLE_KEYS = _ENVELOPE_KEYS | {
    "snapshot_id", "public_revision", "native_revision", "proof_epoch",
    "date_raw", "definition", "payload_shape", "roles",
    "unconditional_prisoner_release", "can_send", "costs", "acceptance",
    "readiness", "option_keys", "selected_option_mask_bits",
    "puppet_or_actor_character_id",
}
_READINESS_KEYS = {
    "definition_ready", "actor_ready", "recipient_ready",
    "finalized_context_ready", "can_send_ready", "costs_ready",
    "acceptance_ready", "same_frame_ready",
}


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_prisoner_release_preview_12003(
    preview: Mapping[str, object], *, native_revision: int, date_raw: int,
    player_character_id: int, prisoner_character_id: int,
) -> dict[str, object]:
    """Return a detached validated copy; preserve an observed false Can Send.

    Unavailable results retain their native reason and six-field legacy shape.
    Malformed available inputs raise ValueError rather than becoming a refusal.
    """
    if (
        not _integer(native_revision, 1, 2**64 - 1)
        or not _integer(date_raw, -(2**31), 2**31 - 1)
        or not _integer(player_character_id, 1, 2**32 - 1)
        or not _integer(prisoner_character_id, 1, 2**32 - 1)
        or player_character_id == prisoner_character_id
    ):
        raise ValueError("private release preview paused-frame binding is malformed")
    if (
        not isinstance(preview, Mapping)
        or preview.get("private_build") is not True
        or preview.get("read_only") is not True
        or preview.get("advertised") is not False
        or preview.get("action_surface_present") is not False
    ):
        raise ValueError("private release preview envelope is malformed")
    if preview.get("status") == "unavailable":
        if (
            set(preview) != _UNAVAILABLE_KEYS
            or not isinstance(preview.get("unavailable_reason"), str)
            or not preview["unavailable_reason"]
        ):
            raise ValueError("private release unavailable preview is malformed")
        return copy.deepcopy(dict(preview))
    if preview.get("status") != "available" or set(preview) != _AVAILABLE_KEYS:
        raise ValueError("private release available preview fields are malformed")
    if (
        preview.get("snapshot_id") != f"native:{native_revision}"
        or type(preview.get("public_revision")) is not int
        or preview["public_revision"] != native_revision
        or type(preview.get("native_revision")) is not int
        or preview["native_revision"] != native_revision
        or not _integer(preview.get("proof_epoch"), 1, 2**64 - 1)
        or type(preview.get("date_raw")) is not int
        or preview["date_raw"] != date_raw
    ):
        raise ValueError("private release preview differs from its paused native frame")
    definition = preview.get("definition")
    if (
        not isinstance(definition, Mapping)
        or set(definition) != {
            "canonical_key", "deterministic_key_hash", "runtime_ordinal",
        }
        or definition.get("canonical_key") != "release_from_prison_interaction"
        or not _integer(definition.get("deterministic_key_hash"), 0, 2**32 - 1)
        or not _integer(definition.get("runtime_ordinal"), 0, 2**31 - 1)
    ):
        raise ValueError("private release definition identity is malformed")
    roles = preview.get("roles")
    if (
        not isinstance(roles, Mapping)
        or set(roles) != {"actor_character_id", "recipient_character_id"}
        or type(roles.get("actor_character_id")) is not int
        or roles["actor_character_id"] != player_character_id
        or type(roles.get("recipient_character_id")) is not int
        or roles["recipient_character_id"] != prisoner_character_id
        or type(preview.get("puppet_or_actor_character_id")) is not int
        or preview["puppet_or_actor_character_id"] != player_character_id
    ):
        raise ValueError("private release preview roles differ from actual player custody")
    if (
        preview.get("payload_shape") != "two_role_all_release_options_off"
        or preview.get("unconditional_prisoner_release") is not True
        or type(preview.get("can_send")) is not bool
        or not isinstance(preview.get("option_keys"), list)
        or preview["option_keys"] != list(RELEASE_OPTION_KEYS_12003)
        or type(preview.get("selected_option_mask_bits")) is not int
        or preview["selected_option_mask_bits"] != 0
    ):
        raise ValueError("private release preview is not the current thirteen-option ordinary path")
    costs = preview.get("costs")
    if (
        not isinstance(costs, Mapping)
        or set(costs) != {"raw_scale", "payer_role", "application_timing", "entries"}
        or type(costs.get("raw_scale")) is not int
        or costs["raw_scale"] != 100_000
        or costs.get("payer_role") != "actor"
        or costs.get("application_timing") != "on_send"
        or not isinstance(costs.get("entries"), list)
        or len(costs["entries"]) != len(RELEASE_COST_KEYS_12003)
    ):
        raise ValueError("private release on-send resource costs are malformed")
    for resource_key, entry in zip(RELEASE_COST_KEYS_12003, costs["entries"], strict=True):
        if (
            not isinstance(entry, Mapping)
            or set(entry) != {"resource_key", "raw"}
            or entry.get("resource_key") != resource_key
            or not _integer(entry.get("raw"), -(2**63), 2**63 - 1)
        ):
            raise ValueError("private release resource order or raw cost is malformed")
    acceptance = preview.get("acceptance")
    if (
        not isinstance(acceptance, Mapping)
        or set(acceptance) != {"kind", "auto_accept", "would_accept_now"}
        or acceptance.get("kind") != "auto_accept"
        or acceptance.get("auto_accept") is not True
        or acceptance.get("would_accept_now") is not True
    ):
        raise ValueError("private release compact native auto-accept is malformed")
    readiness = preview.get("readiness")
    if (
        not isinstance(readiness, Mapping)
        or set(readiness) != _READINESS_KEYS
        or any(readiness.get(key) is not True for key in _READINESS_KEYS)
    ):
        raise ValueError("private release final input readiness is malformed")
    return copy.deepcopy(dict(preview))
