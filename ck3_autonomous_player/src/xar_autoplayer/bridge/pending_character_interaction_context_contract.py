"""Strict contract for one exact-build pending interaction context."""

from __future__ import annotations

from typing import Final


QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY: Final = (
    "game.command.query-pending-character-interaction-context-v1"
)
QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP: Final = (
    "query-pending-character-interaction-context-v1"
)
ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_CAPABILITY: Final = (
    "game.command.acknowledge-pending-character-interaction"
)
ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP: Final = (
    "acknowledge-pending-character-interaction"
)
PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION: Final = "1.19.0.6"
PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-pending-character-interaction-context-v1"
)
PENDING_CHARACTER_INTERACTION_SPECIAL_WAR_BINDING_V1_CONTRACT: Final = (
    "pending-character-interaction-special-war-binding-v1"
)

_FIELDS: Final = {
    "schema",
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "pending_interaction_id",
    "reason",
    "build",
    "definition",
    "roles",
    "target",
    "send_options",
    "routing",
    "deadline",
    "auto_accept",
    "legality",
    "terms",
    "readiness",
    "provenance",
}
_BUILD_FIELDS: Final = {"version", "exe_sha256"}
_DEFINITION_FIELDS: Final = {
    "canonical_key",
    "deterministic_key_hash",
    "runtime_ordinal",
}
_ROLES_FIELDS: Final = {
    "actor_character_id",
    "recipient_character_id",
    "secondary_actor_character_id",
    "secondary_recipient_character_id",
    "intermediary_character_id",
}
_TARGET_FIELDS: Final = {
    "present",
    "raw_type_index",
    "raw_16_bytes_hex",
    "type_key_status",
    "type_key",
    "type_key_reason",
    "typed_identity_status",
    "typed_identity",
    "typed_identity_reason",
}
_SEND_OPTIONS_FIELDS: Final = {
    "exclusive",
    "definition_count",
    "context_count",
    "rows",
}
_SEND_OPTION_ROW_FIELDS: Final = {
    "native_index",
    "numeric_flag_identifier",
    "selected",
    "is_shown",
    "is_valid",
    "canonical_flag_status",
    "canonical_flag_key",
    "canonical_flag_reason",
}
_ROUTING_FIELDS: Final = {
    "kind",
    "played_character_id",
    "current_responder_role",
    "reply_execution_channel",
    "local_route",
    "auto_accept_notification",
}
_DEADLINE_FIELDS: Final = {
    "age_days",
    "expiration_days",
    "remaining_days",
    "expiry_boundary_status",
}
_STATUS_VALUE_REASON_FIELDS: Final = {"status", "value", "reason"}
_COST_VALUE_FIELDS: Final = {
    "raw_scale",
    "payer_role",
    "application_timing",
    "pending_payment_state",
    "entries",
}
_COST_ENTRY_FIELDS: Final = {"resource_key", "raw"}
_SPECIAL_WAR_VALUE_FIELDS: Final = {
    "special_interaction_kind",
    "absolute_outcome",
    "war_id",
    "actor_war_role",
    "recipient_war_role",
    "binding_source",
}
_COST_RESOURCE_KEYS: Final = (
    "gold",
    "prestige",
    "piety",
    "renown",
    "influence",
    "herd",
    "treasury",
    "treasury_or_gold",
    "merit",
    "barter_goods",
)
_LEGALITY_ITEM_FIELDS: Final = {"status", "allowed", "reason"}
_LEGALITY_KEYS: Final = ("accept", "reject", "block", "acknowledge")
_LEGALITY_FIELDS: Final = set(_LEGALITY_KEYS)
_TERMS_KEYS: Final = (
    "special_war_binding",
    "structured_costs",
    "structured_exchanges",
    "structured_effect_preview",
    "recipient_ai_acceptance_score",
    "recipient_ai_final_decision",
)
_UNAVAILABLE_TERMS_KEYS: Final = _TERMS_KEYS[2:]
_TERMS_FIELDS: Final = {"special_data_present", *_TERMS_KEYS}
_READINESS_BOOL_KEYS: Final = (
    "stable_definition_ready",
    "roles_ready",
    "target_type_key_ready",
    "target_typed_identity_ready",
    "send_options_ready",
    "routing_ready",
    "deadline_ready",
    "auto_accept_ready",
    "reply_legality_ready",
    "generic_costs_ready",
    "special_war_binding_ready",
    "special_outcome_terms_ready",
    "structured_terms_ready",
    "same_frame_ready",
    "interaction_semantic_decision_ready",
)
_READINESS_FIELDS: Final = {*_READINESS_BOOL_KEYS, "not_ready_reasons"}
_PROVENANCE_VALUES: Final = {
    "backend_id": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID,
    "pending_storage_slot_rva": "0x57BF1C8",
    "character_storage_slot_rva": "0x570C130",
    "expiration_days_rva": "0x570F528",
    "local_routing_predicate_rva": "0x1266BA0",
    "reply_validator_rva": "0x26B3540",
    "auto_accept_trigger_evaluator_rva": "0x334C510",
    "cost_evaluator_rva": "0x2CDB7B0",
    "common_war_relation_rva": "0x2610840",
    "target_type_registry_getter_rva": "0x33C52B0",
    "target_type_registry_rva": "0x4FFE290",
    "script_identifier_name_rva": "0x3B58970",
    "reply_primary_vtable_rva": "0x4082930",
    "reply_secondary_vtable_rva": "0x4082900",
    "war_victory_special_vtable_rva": "0x428EEA8",
    "war_white_peace_special_vtable_rva": "0x428EF88",
    "war_defeat_special_vtable_rva": "0x428EF18",
}
_SPECIAL_WAR_UNAVAILABLE_REASONS: Final = {
    "special_war_binding_not_applicable",
    "special_interaction_subtype_opaque",
    "special_interaction_identity_mismatch",
    "special_war_binding_unavailable",
    "special_war_roles_mismatch",
}
_SPECIAL_WAR_PAIRS: Final = {
    "end_war_attacker_victory_interaction": (
        "end_war_attacker_victory_interaction",
        "attacker_victory",
    ),
    "end_war_attacker_white_peace_interaction": (
        "end_war_white_peace_interaction",
        "white_peace",
    ),
    "end_war_attacker_defeat_interaction": (
        "end_war_attacker_defeat_interaction",
        "attacker_defeat",
    ),
}
_TOP_STATUSES: Final = {"available", "unavailable", "invalid"}
_UNAVAILABLE_REASONS: Final = {
    "requires_application_main",
    "state_changed",
    "requires_paused",
    "map_not_ready",
    "unsupported_build",
    "pending_storage_unavailable",
    "pending_generation_mismatch",
    "character_storage_unavailable",
    "played_character_generation_mismatch",
    "pending_roles_unavailable",
    "pending_routing_unavailable",
    "pending_not_routed_to_played_character",
    "pending_reply_state_unavailable",
    "pending_definition_unavailable",
    "pending_target_unavailable",
    "target_type_registry_unavailable",
    "target_type_key_unavailable",
    "send_options_unavailable",
    "send_option_evaluation_unavailable",
    "pending_deadline_unavailable",
    "auto_accept_unavailable",
    "reply_legality_unavailable",
    "structured_costs_unavailable",
    "pending_terms_unavailable",
    "internal_error",
}
_INVALID_REASONS: Final = {
    "invalid_pending_interaction_id",
    "invalid_played_character_id",
    "pending_roles_invalid",
    "pending_routing_invalid",
    "pending_definition_invalid",
    "target_type_registry_drift",
    "target_type_index_out_of_bounds",
    "send_option_count_invalid",
    "send_option_count_mismatch",
    "send_option_storage_invalid",
    "send_option_row_invalid",
    "exclusive_send_option_selection_invalid",
    "pending_deadline_invalid",
    "auto_accept_invalid",
    "reply_validator_semantic_mismatch",
}
_EXPIRY_BOUNDARIES: Final = {
    "not_reached",
    "at_or_past_daily_expiry_queue_threshold",
}


def _exact_object(
    value: object,
    fields: set[str],
    name: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _int(
    value: object,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{name} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, name: str) -> int:
    return _int(value, name, minimum=1, maximum=2**31 - 1)


def normalize_pending_interaction_id(
    value: object, name: str = "pending_interaction_id"
) -> int:
    """Normalize CK3's signed int32 generation-bearing component identity."""
    result = _int(value, name, minimum=-(2**31), maximum=2**31 - 1)
    if result == -1:
        raise ValueError(f"{name} must not use CK3's -1 invalid sentinel")
    return result


def _character_id(
    value: object,
    name: str,
    *,
    required: bool,
) -> int:
    result = _int(value, name, minimum=-1, maximum=2**31 - 1)
    if required and result <= 0:
        raise ValueError(f"{name} must be a positive full CharacterID")
    if not required and result == 0:
        raise ValueError(f"{name} must use -1, not zero, for absence")
    return result


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _stable_key(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ValueError(f"{name} must be a non-empty stable key")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} must be valid UTF-8") from error
    if len(encoded) > 1_024:
        raise ValueError(f"{name} exceeds the native stable-key limit")
    return value


def _reason(value: object, name: str) -> str:
    return _stable_key(value, name)


def _normalize_build(value: object) -> dict[str, str]:
    build = _exact_object(value, _BUILD_FIELDS, "build")
    if build != {
        "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
        "exe_sha256": (
            PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ),
    }:
        raise ValueError("build does not match the frozen exact build")
    return dict(build)


def _normalize_provenance(value: object) -> dict[str, str]:
    provenance = _exact_object(
        value, set(_PROVENANCE_VALUES), "provenance"
    )
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("provenance does not match the frozen exact build")
    return dict(_PROVENANCE_VALUES)


def _normalize_legality(
    value: object,
    *,
    available: bool,
    top_reason: str | None,
) -> dict[str, dict[str, object]]:
    legality = _exact_object(value, _LEGALITY_FIELDS, "legality")
    result: dict[str, dict[str, object]] = {}
    for key in _LEGALITY_KEYS:
        item = _exact_object(
            legality.get(key), _LEGALITY_ITEM_FIELDS, f"legality.{key}"
        )
        status = item.get("status")
        allowed = _bool(item.get("allowed"), f"legality.{key}.allowed")
        reason = item.get("reason")
        if available:
            if status != "available":
                raise ValueError(f"legality.{key} must be available")
            if allowed:
                if reason is not None:
                    raise ValueError(
                        f"allowed legality.{key} cannot have a reason"
                    )
            else:
                reason = _reason(reason, f"legality.{key}.reason")
        else:
            if (
                status != "unavailable"
                or allowed
                or reason != top_reason
            ):
                raise ValueError(
                    f"unavailable legality.{key} disagrees with top status"
                )
        result[key] = {
            "status": status,
            "allowed": allowed,
            "reason": reason,
        }
    return result


def _normalize_special_war_binding(
    value: object,
    *,
    definition_key: str,
    special_data_present: bool,
) -> tuple[dict[str, object], bool, str | None]:
    item = _exact_object(
        value,
        _STATUS_VALUE_REASON_FIELDS,
        "terms.special_war_binding",
    )
    status = item.get("status")
    reason_value = item.get("reason")
    if status == "unavailable":
        reason = _reason(reason_value, "terms.special_war_binding.reason")
        if item.get("value") is not None or reason not in (
            _SPECIAL_WAR_UNAVAILABLE_REASONS
        ):
            raise ValueError("special-war binding invented unavailable state")
        known_definition = definition_key in _SPECIAL_WAR_PAIRS
        reason_matches_presence = (
            reason == "special_war_binding_not_applicable"
            and not special_data_present
            and not known_definition
        ) or (
            reason == "special_interaction_subtype_opaque"
            and special_data_present
            and not known_definition
        ) or (
            reason == "special_interaction_identity_mismatch"
            and (special_data_present or known_definition)
        ) or reason == "special_war_binding_unavailable" or (
            reason == "special_war_roles_mismatch"
            and special_data_present
            and known_definition
        )
        if not reason_matches_presence:
            raise ValueError("special-war availability disagrees with special_data")
        return (
            {"status": "unavailable", "value": None, "reason": reason},
            False,
            reason,
        )
    if status != "available" or reason_value is not None or not special_data_present:
        raise ValueError("special-war binding must use a typed status")
    expected_pair = _SPECIAL_WAR_PAIRS.get(definition_key)
    binding = _exact_object(
        item.get("value"),
        _SPECIAL_WAR_VALUE_FIELDS,
        "terms.special_war_binding.value",
    )
    if expected_pair is None or (
        binding.get("special_interaction_kind"),
        binding.get("absolute_outcome"),
    ) != expected_pair:
        raise ValueError("special-war definition/kind/outcome pair drifted")
    actor_role = binding.get("actor_war_role")
    recipient_role = binding.get("recipient_war_role")
    if (actor_role, recipient_role) not in {
        ("primary_attacker", "primary_defender"),
        ("primary_defender", "primary_attacker"),
    }:
        raise ValueError("special-war roles must be opposite primary sides")
    if binding.get("binding_source") != "native_common_war_relation":
        raise ValueError("special-war binding source drifted")
    normalized_binding = {
        "special_interaction_kind": expected_pair[0],
        "absolute_outcome": expected_pair[1],
        "war_id": _positive_int32(
            binding.get("war_id"), "terms.special_war_binding.value.war_id"
        ),
        "actor_war_role": actor_role,
        "recipient_war_role": recipient_role,
        "binding_source": "native_common_war_relation",
    }
    return (
        {"status": "available", "value": normalized_binding, "reason": None},
        True,
        None,
    )


def _normalize_readiness(
    value: object,
    *,
    available: bool,
    target_present: bool,
    special_war_binding_available: bool,
    special_war_binding_reason: str | None,
    top_reason: str | None,
) -> dict[str, object]:
    readiness = _exact_object(value, _READINESS_FIELDS, "readiness")
    result: dict[str, object] = {
        key: _bool(readiness.get(key), f"readiness.{key}")
        for key in _READINESS_BOOL_KEYS
    }
    reasons_value = readiness.get("not_ready_reasons")
    if not isinstance(reasons_value, list):
        raise ValueError("readiness.not_ready_reasons must be a list")
    reasons = [
        _reason(item, f"readiness.not_ready_reasons[{index}]")
        for index, item in enumerate(reasons_value)
    ]
    if len(reasons) != len(set(reasons)):
        raise ValueError("readiness.not_ready_reasons must be unique")
    if not available:
        if any(result.values()) or reasons != [top_reason]:
            raise ValueError("unavailable readiness invented native state")
    else:
        expected = {
            "stable_definition_ready": True,
            "roles_ready": True,
            "target_type_key_ready": True,
            "target_typed_identity_ready": not target_present,
            "send_options_ready": True,
            "routing_ready": True,
            "deadline_ready": True,
            "auto_accept_ready": True,
            "reply_legality_ready": True,
            "generic_costs_ready": True,
            "special_war_binding_ready": special_war_binding_available,
            "special_outcome_terms_ready": False,
            "structured_terms_ready": False,
            "same_frame_ready": True,
            "interaction_semantic_decision_ready": False,
        }
        if result != expected:
            raise ValueError("readiness fields disagree with observed domains")
        expected_reasons = [
            *(
                ["target_generic_scope_payload_identity_not_closed"]
                if target_present
                else []
            ),
            *(
                [special_war_binding_reason]
                if not special_war_binding_available
                else []
            ),
            "special_outcome_terms_unavailable",
            "structured_exchanges_unavailable",
            "structured_effect_preview_unavailable",
        ]
        if reasons != expected_reasons:
            raise ValueError("readiness reasons disagree with observed domains")
    result["not_ready_reasons"] = reasons
    return result


def _normalize_available_frame(
    frame: dict[str, object],
) -> dict[str, object]:
    definition = _exact_object(
        frame.get("definition"), _DEFINITION_FIELDS, "definition"
    )
    normalized_definition = {
        "canonical_key": _stable_key(
            definition.get("canonical_key"), "definition.canonical_key"
        ),
        "deterministic_key_hash": _int(
            definition.get("deterministic_key_hash"),
            "definition.deterministic_key_hash",
            minimum=0,
            maximum=2**32 - 1,
        ),
        "runtime_ordinal": _int(
            definition.get("runtime_ordinal"),
            "definition.runtime_ordinal",
            minimum=0,
            maximum=2**31 - 1,
        ),
    }

    roles = _exact_object(frame.get("roles"), _ROLES_FIELDS, "roles")
    normalized_roles = {
        "actor_character_id": _character_id(
            roles.get("actor_character_id"),
            "roles.actor_character_id",
            required=True,
        ),
        "recipient_character_id": _character_id(
            roles.get("recipient_character_id"),
            "roles.recipient_character_id",
            required=True,
        ),
        "secondary_actor_character_id": _character_id(
            roles.get("secondary_actor_character_id"),
            "roles.secondary_actor_character_id",
            required=False,
        ),
        "secondary_recipient_character_id": _character_id(
            roles.get("secondary_recipient_character_id"),
            "roles.secondary_recipient_character_id",
            required=False,
        ),
        "intermediary_character_id": _character_id(
            roles.get("intermediary_character_id"),
            "roles.intermediary_character_id",
            required=False,
        ),
    }

    target = _exact_object(frame.get("target"), _TARGET_FIELDS, "target")
    present = _bool(target.get("present"), "target.present")
    raw_type_index = _int(
        target.get("raw_type_index"),
        "target.raw_type_index",
        minimum=0,
        maximum=2**16 - 1,
    )
    raw_hex = target.get("raw_16_bytes_hex")
    if not isinstance(raw_hex, str) or len(raw_hex) != 32:
        raise ValueError("target.raw_16_bytes_hex must encode exactly 16 bytes")
    try:
        raw_bytes = bytes.fromhex(raw_hex)
    except ValueError as error:
        raise ValueError("target.raw_16_bytes_hex is not hexadecimal") from error
    if len(raw_bytes) != 16 or int.from_bytes(raw_bytes[:2], "little") != raw_type_index:
        raise ValueError("target raw envelope disagrees with raw_type_index")
    if present != (raw_type_index != 0):
        raise ValueError("target presence disagrees with raw_type_index")
    if not present:
        if any(
            target.get(key) != expected
            for key, expected in {
                "type_key_status": "absent",
                "type_key": None,
                "type_key_reason": None,
                "typed_identity_status": "absent",
                "typed_identity": None,
                "typed_identity_reason": None,
            }.items()
        ):
            raise ValueError("absent target invented a type or identity")
        normalized_target = dict(target)
    else:
        if (
            target.get("type_key_status") != "available"
            or target.get("type_key_reason") is not None
            or target.get("typed_identity_status") != "unavailable"
            or target.get("typed_identity") is not None
            or target.get("typed_identity_reason")
            != "generic_scope_payload_identity_not_closed"
        ):
            raise ValueError("present target violates the typed boundary")
        normalized_target = {
            **target,
            "type_key": _stable_key(target.get("type_key"), "target.type_key"),
        }

    send_options = _exact_object(
        frame.get("send_options"), _SEND_OPTIONS_FIELDS, "send_options"
    )
    exclusive = _bool(send_options.get("exclusive"), "send_options.exclusive")
    definition_count = _int(
        send_options.get("definition_count"),
        "send_options.definition_count",
        minimum=0,
        maximum=256,
    )
    context_count = _int(
        send_options.get("context_count"),
        "send_options.context_count",
        minimum=0,
        maximum=256,
    )
    rows_value = send_options.get("rows")
    if (
        not isinstance(rows_value, list)
        or context_count != definition_count
        or len(rows_value) != definition_count
    ):
        raise ValueError("send-option counts do not describe the full vector")
    rows: list[dict[str, object]] = []
    selected_count = 0
    for index, row_value in enumerate(rows_value):
        row = _exact_object(
            row_value,
            _SEND_OPTION_ROW_FIELDS,
            f"send_options.rows[{index}]",
        )
        native_index = _int(
            row.get("native_index"),
            f"send_options.rows[{index}].native_index",
            minimum=0,
            maximum=max(0, definition_count - 1),
        )
        if native_index != index:
            raise ValueError("send-option rows must use authored native order")
        selected = _bool(
            row.get("selected"), f"send_options.rows[{index}].selected"
        )
        selected_count += int(selected)
        if (
            row.get("canonical_flag_status") != "unavailable"
            or row.get("canonical_flag_key") is not None
            or row.get("canonical_flag_reason")
            != "numeric_flag_identifier_string_mapping_not_closed"
        ):
            raise ValueError("send-option canonical flag identity was invented")
        rows.append(
            {
                "native_index": native_index,
                "numeric_flag_identifier": _int(
                    row.get("numeric_flag_identifier"),
                    f"send_options.rows[{index}].numeric_flag_identifier",
                    minimum=0,
                    maximum=2**31 - 1,
                ),
                "selected": selected,
                "is_shown": _bool(
                    row.get("is_shown"),
                    f"send_options.rows[{index}].is_shown",
                ),
                "is_valid": _bool(
                    row.get("is_valid"),
                    f"send_options.rows[{index}].is_valid",
                ),
                "canonical_flag_status": "unavailable",
                "canonical_flag_key": None,
                "canonical_flag_reason": (
                    "numeric_flag_identifier_string_mapping_not_closed"
                ),
            }
        )
    if exclusive and selected_count > 1:
        raise ValueError("exclusive send options selected more than one row")
    normalized_send_options = {
        "exclusive": exclusive,
        "definition_count": definition_count,
        "context_count": context_count,
        "rows": rows,
    }

    routing = _exact_object(frame.get("routing"), _ROUTING_FIELDS, "routing")
    kind = _int(routing.get("kind"), "routing.kind", minimum=0, maximum=2)
    played_id = _positive_int32(
        routing.get("played_character_id"), "routing.played_character_id"
    )
    expected_role = "intermediary" if kind == 1 else "recipient"
    expected_channel = expected_role
    if (
        routing.get("current_responder_role") != expected_role
        or routing.get("reply_execution_channel") != expected_channel
        or routing.get("local_route") is not True
    ):
        raise ValueError("available routing does not identify the local responder")
    responder_id = normalized_roles[f"{expected_role}_character_id"]
    if responder_id != played_id:
        raise ValueError("routing responder does not equal played CharacterID")
    normalized_routing = {
        "kind": kind,
        "played_character_id": played_id,
        "current_responder_role": expected_role,
        "reply_execution_channel": expected_channel,
        "local_route": True,
        "auto_accept_notification": _bool(
            routing.get("auto_accept_notification"),
            "routing.auto_accept_notification",
        ),
    }

    deadline = _exact_object(frame.get("deadline"), _DEADLINE_FIELDS, "deadline")
    age_days = _int(
        deadline.get("age_days"), "deadline.age_days", minimum=0, maximum=2**31 - 1
    )
    expiration_days = _int(
        deadline.get("expiration_days"),
        "deadline.expiration_days",
        minimum=1,
        maximum=100_000,
    )
    remaining_days = _int(
        deadline.get("remaining_days"),
        "deadline.remaining_days",
        minimum=0,
        maximum=2**31 - 1,
    )
    boundary = deadline.get("expiry_boundary_status")
    expected_remaining = max(0, expiration_days - age_days)
    expected_boundary = (
        "not_reached"
        if age_days < expiration_days
        else "at_or_past_daily_expiry_queue_threshold"
    )
    if (
        remaining_days != expected_remaining
        or boundary != expected_boundary
        or boundary not in _EXPIRY_BOUNDARIES
    ):
        raise ValueError("deadline projection is inconsistent")
    normalized_deadline = {
        "age_days": age_days,
        "expiration_days": expiration_days,
        "remaining_days": remaining_days,
        "expiry_boundary_status": boundary,
    }

    auto_accept = _exact_object(
        frame.get("auto_accept"), _STATUS_VALUE_REASON_FIELDS, "auto_accept"
    )
    if auto_accept.get("status") != "available" or auto_accept.get("reason") is not None:
        raise ValueError("available frame lacks exact auto_accept")
    normalized_auto_accept = {
        "status": "available",
        "value": _bool(auto_accept.get("value"), "auto_accept.value"),
        "reason": None,
    }

    legality = _normalize_legality(frame.get("legality"), available=True, top_reason=None)
    notification = normalized_routing["auto_accept_notification"]
    if notification:
        if legality["acknowledge"]["allowed"] is not True or any(
            legality[key]["allowed"] is not False
            for key in ("accept", "reject", "block")
        ):
            raise ValueError("auto-accept notification must be acknowledge-only")
    elif legality["acknowledge"]["allowed"] is not False:
        raise ValueError("normal interaction cannot acknowledge")
    if normalized_auto_accept["value"] is True and any(
        legality[key]["allowed"] is not False for key in ("reject", "block")
    ):
        raise ValueError("auto_accept cannot permit reject or block")
    if (
        normalized_roles["actor_character_id"]
        == normalized_roles["recipient_character_id"]
        and any(
            legality[key]["allowed"] is not False
            for key in ("reject", "block")
        )
    ):
        raise ValueError("self interaction cannot permit reject or block")

    terms = _exact_object(frame.get("terms"), _TERMS_FIELDS, "terms")
    normalized_terms: dict[str, object] = {
        "special_data_present": _bool(
            terms.get("special_data_present"), "terms.special_data_present"
        )
    }
    (
        normalized_terms["special_war_binding"],
        special_war_binding_available,
        special_war_binding_reason,
    ) = _normalize_special_war_binding(
        terms.get("special_war_binding"),
        definition_key=normalized_definition["canonical_key"],
        special_data_present=normalized_terms["special_data_present"],
    )
    structured_costs = _exact_object(
        terms.get("structured_costs"),
        _STATUS_VALUE_REASON_FIELDS,
        "terms.structured_costs",
    )
    if (
        structured_costs.get("status") != "available"
        or structured_costs.get("reason") is not None
    ):
        raise ValueError("terms.structured_costs must be available")
    cost_value = _exact_object(
        structured_costs.get("value"),
        _COST_VALUE_FIELDS,
        "terms.structured_costs.value",
    )
    if cost_value.get("raw_scale") != 100_000:
        raise ValueError("terms.structured_costs raw scale drifted")
    if (
        cost_value.get("payer_role") != "actor"
        or cost_value.get("application_timing") != "on_send"
        or cost_value.get("pending_payment_state") != "already_applied"
    ):
        raise ValueError("terms.structured_costs payment semantics drifted")
    cost_entries_value = cost_value.get("entries")
    if (
        not isinstance(cost_entries_value, list)
        or len(cost_entries_value) != len(_COST_RESOURCE_KEYS)
    ):
        raise ValueError("terms.structured_costs must contain all ten entries")
    cost_entries: list[dict[str, object]] = []
    for index, expected_key in enumerate(_COST_RESOURCE_KEYS):
        entry = _exact_object(
            cost_entries_value[index],
            _COST_ENTRY_FIELDS,
            f"terms.structured_costs.value.entries[{index}]",
        )
        if entry.get("resource_key") != expected_key:
            raise ValueError("structured-cost resource order drifted")
        cost_entries.append(
            {
                "resource_key": expected_key,
                "raw": _int(
                    entry.get("raw"),
                    f"terms.structured_costs.value.entries[{index}].raw",
                    minimum=-(2**63),
                    maximum=2**63 - 1,
                ),
            }
        )
    normalized_terms["structured_costs"] = {
        "status": "available",
        "value": {
            "raw_scale": 100_000,
            "payer_role": "actor",
            "application_timing": "on_send",
            "pending_payment_state": "already_applied",
            "entries": cost_entries,
        },
        "reason": None,
    }
    for key in _UNAVAILABLE_TERMS_KEYS:
        item = _exact_object(
            terms.get(key), _STATUS_VALUE_REASON_FIELDS, f"terms.{key}"
        )
        if (
            item.get("status") != "unavailable"
            or item.get("value") is not None
        ):
            raise ValueError(f"terms.{key} invented structured semantics")
        normalized_terms[key] = {
            "status": "unavailable",
            "value": None,
            "reason": _reason(item.get("reason"), f"terms.{key}.reason"),
        }

    readiness = _normalize_readiness(
        frame.get("readiness"),
        available=True,
        target_present=present,
        special_war_binding_available=special_war_binding_available,
        special_war_binding_reason=special_war_binding_reason,
        top_reason=None,
    )
    return {
        **frame,
        "definition": normalized_definition,
        "roles": normalized_roles,
        "target": normalized_target,
        "send_options": normalized_send_options,
        "routing": normalized_routing,
        "deadline": normalized_deadline,
        "auto_accept": normalized_auto_accept,
        "legality": legality,
        "terms": normalized_terms,
        "readiness": readiness,
    }


def normalize_pending_character_interaction_context_v1(
    value: object,
    *,
    expected_pending_interaction_id: int,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one full-generation, same-frame pending interaction."""

    expected_id = normalize_pending_interaction_id(
        expected_pending_interaction_id, "expected_pending_interaction_id"
    )
    expected_date = _int(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_native_revision = _int(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    frame = _exact_object(value, _FIELDS, "pending_interaction_context")
    if frame.get("schema") != "pending-character-interaction-context-v1":
        raise ValueError("pending interaction schema is invalid")
    if frame.get("schema_version") != 1 or isinstance(
        frame.get("schema_version"), bool
    ):
        raise ValueError("pending interaction schema_version must be 1")
    status = frame.get("status")
    if status not in _TOP_STATUSES:
        raise ValueError("pending interaction status is invalid")
    revision = _int(
        frame.get("snapshot_revision"),
        "pending_interaction_context.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    date_raw = _int(
        frame.get("date_raw"),
        "pending_interaction_context.date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    pending_id = normalize_pending_interaction_id(
        frame.get("pending_interaction_id"), "pending_interaction_id"
    )
    if revision != expected_native_revision:
        raise ValueError("pending interaction snapshot revision binding changed")
    if date_raw != expected_date:
        raise ValueError("pending interaction date binding changed")
    if pending_id != expected_id:
        raise ValueError("pending interaction full-generation identity changed")
    build = _normalize_build(frame.get("build"))
    provenance = _normalize_provenance(frame.get("provenance"))

    available = status == "available"
    reason_value = frame.get("reason")
    reason: str | None
    if available:
        if reason_value is not None:
            raise ValueError("available pending interaction has a reason")
        reason = None
        normalized = _normalize_available_frame(frame)
    else:
        reason = _reason(reason_value, "reason")
        expected_reasons = (
            _UNAVAILABLE_REASONS
            if status == "unavailable"
            else _INVALID_REASONS
        )
        if reason not in expected_reasons:
            raise ValueError(
                "pending interaction reason disagrees with its status"
            )
        for key in (
            "definition",
            "roles",
            "target",
            "send_options",
            "routing",
            "deadline",
            "auto_accept",
            "terms",
        ):
            if frame.get(key) is not None:
                raise ValueError(f"{status} frame invented {key}")
        legality = _normalize_legality(
            frame.get("legality"), available=False, top_reason=reason
        )
        readiness = _normalize_readiness(
            frame.get("readiness"),
            available=False,
            target_present=False,
            special_war_binding_available=False,
            special_war_binding_reason=None,
            top_reason=reason,
        )
        normalized = {
            **frame,
            "legality": legality,
            "readiness": readiness,
        }
    return {
        **normalized,
        "schema": "pending-character-interaction-context-v1",
        "schema_version": 1,
        "status": status,
        "snapshot_revision": revision,
        "date_raw": date_raw,
        "pending_interaction_id": pending_id,
        "reason": reason,
        "build": build,
        "provenance": provenance,
    }
