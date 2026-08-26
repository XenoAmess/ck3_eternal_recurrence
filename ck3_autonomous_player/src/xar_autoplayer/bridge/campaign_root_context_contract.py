"""Strict contract for the exact-build paused campaign root context."""

from __future__ import annotations

from typing import Final


QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY: Final = (
    "game.command.query-campaign-root-context-v1"
)
QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP: Final = (
    "query-campaign-root-context-v1"
)
CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION: Final = "1.19.0.6"
CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
CAMPAIGN_ROOT_CONTEXT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-campaign-root-context-v1"
)

_FIELDS: Final = {
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "local_player_id",
    "player_character_id",
    "player_character_alive",
    "primary_title",
    "capital_province_id",
    "immediate_liege_character_id",
    "top_liege_character_id",
    "independent",
    "government",
    "selected_game_rule_tokens",
    "native_selected_game_rule_token_count",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_PRIMARY_TITLE_FIELDS: Final = {"title_id", "tier_raw", "tier_key"}
_GOVERNMENT_FIELDS: Final = {"key", "flags", "native_flag_count"}
_READINESS_KEYS: Final = (
    "player_identity_ready",
    "primary_title_ready",
    "capital_ready",
    "lieges_ready",
    "government_ready",
    "selected_game_rule_tokens_ready",
    "same_frame_ready",
    "ready",
)
_READINESS_FIELDS: Final = set(_READINESS_KEYS)
_PROVENANCE_FIELDS: Final = {
    "game_version",
    "executable_sha256",
    "backend_id",
    "primary_title_rva",
    "capital_province_rva",
    "immediate_liege_rva",
    "top_liege_rva",
    "government_rva",
    "selected_game_rule_service_slot_rva",
}
_PROVENANCE_VALUES: Final = {
    "game_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
    "executable_sha256": CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
    "backend_id": CAMPAIGN_ROOT_CONTEXT_V1_BACKEND_ID,
    "primary_title_rva": "0x25F3350",
    "capital_province_rva": "0x2606760",
    "immediate_liege_rva": "0x2613480",
    "top_liege_rva": "0x2613600",
    "government_rva": "0x26165B0",
    "selected_game_rule_service_slot_rva": "0x5754B48",
}
_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "player_identity_unavailable",
    "player_character_generation_mismatch",
    "primary_title_unavailable",
    "capital_unavailable",
    "lieges_unavailable",
    "government_flags_unavailable",
    "selected_game_rule_tokens_unavailable",
    "state_changed",
    "internal_error",
}
_TIER_KEYS: Final = {
    1: "barony",
    2: "county",
    3: "duchy",
    4: "kingdom",
    5: "empire",
    6: "hegemony",
}
_UNAVAILABLE_NULL_FIELDS: Final = {
    "local_player_id",
    "player_character_id",
    "player_character_alive",
    "primary_title",
    "capital_province_id",
    "immediate_liege_character_id",
    "top_liege_character_id",
    "independent",
    "government",
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


def _optional_positive_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, name)


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


def _lexical_key_vector(value: object, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result = [
        _stable_key(item, f"{name}[{index}]")
        for index, item in enumerate(value)
    ]
    if result != sorted(result, key=lambda item: item.encode("utf-8")):
        raise ValueError(f"{name} must use UTF-8 bytewise lexical order")
    # Deliberately do not deduplicate. Native multiplicity is part of the ABI.
    return result


def _normalize_readiness(
    value: object,
    *,
    available: bool,
) -> dict[str, bool]:
    readiness = _exact_object(value, _READINESS_FIELDS, "readiness")
    normalized = {
        key: _bool(readiness.get(key), f"readiness.{key}")
        for key in _READINESS_KEYS
    }
    if any(flag is not available for flag in normalized.values()):
        raise ValueError("readiness fields disagree with status")
    return normalized


def _normalize_provenance(value: object) -> dict[str, str]:
    provenance = _exact_object(value, _PROVENANCE_FIELDS, "provenance")
    if any(
        provenance.get(key) != expected
        for key, expected in _PROVENANCE_VALUES.items()
    ):
        raise ValueError("provenance does not match the frozen exact build")
    return {
        key: str(provenance[key])
        for key in _PROVENANCE_VALUES
    }


def normalize_campaign_root_context_v1(
    value: object,
    *,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one atomic campaign root frame without inventing absences."""

    expected_date_raw = _int(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_snapshot_revision = _int(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    frame = _exact_object(value, _FIELDS, "campaign_root_context")
    if frame.get("schema_version") != 1:
        raise ValueError("campaign_root_context.schema_version must be 1")
    status = frame.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("campaign_root_context.status is invalid")
    revision = _int(
        frame.get("snapshot_revision"),
        "campaign_root_context.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    date_raw = _int(
        frame.get("date_raw"),
        "campaign_root_context.date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    if revision != expected_snapshot_revision:
        raise ValueError("campaign root snapshot revision binding changed")
    if date_raw != expected_date_raw:
        raise ValueError("campaign root date binding changed")
    provenance = _normalize_provenance(frame.get("provenance"))
    available = status == "available"
    readiness = _normalize_readiness(
        frame.get("readiness"), available=available
    )
    reason = frame.get("unavailable_reason")

    tokens = _lexical_key_vector(
        frame.get("selected_game_rule_tokens"),
        "selected_game_rule_tokens",
    )
    token_count = _int(
        frame.get("native_selected_game_rule_token_count"),
        "native_selected_game_rule_token_count",
        minimum=0,
        maximum=2**31 - 1,
    )
    if token_count != len(tokens):
        raise ValueError("selected token count does not match the full vector")

    if not available:
        if reason not in _UNAVAILABLE_REASONS:
            raise ValueError("campaign_root_context unavailable_reason is invalid")
        if any(frame.get(field) is not None for field in _UNAVAILABLE_NULL_FIELDS):
            raise ValueError("unavailable campaign root invented root state")
        if tokens or token_count != 0:
            raise ValueError("unavailable campaign root invented rule tokens")
        return {
            **frame,
            "selected_game_rule_tokens": tokens,
            "native_selected_game_rule_token_count": token_count,
            "readiness": readiness,
            "provenance": provenance,
        }

    if reason is not None:
        raise ValueError("available campaign root has unavailable_reason")
    local_player_id = _int(
        frame.get("local_player_id"),
        "local_player_id",
        minimum=0,
        maximum=2**31 - 1,
    )
    player_character_id = _positive_int32(
        frame.get("player_character_id"), "player_character_id"
    )
    player_character_alive = _bool(
        frame.get("player_character_alive"), "player_character_alive"
    )

    primary_value = frame.get("primary_title")
    primary_title: dict[str, object] | None
    if primary_value is None:
        primary_title = None
    else:
        primary = _exact_object(
            primary_value, _PRIMARY_TITLE_FIELDS, "primary_title"
        )
        title_id = _positive_int32(primary.get("title_id"), "primary_title.title_id")
        tier_raw = _int(
            primary.get("tier_raw"),
            "primary_title.tier_raw",
            minimum=1,
            maximum=6,
        )
        if primary.get("tier_key") != _TIER_KEYS[tier_raw]:
            raise ValueError("primary_title tier pair is invalid")
        primary_title = {
            **primary,
            "title_id": title_id,
            "tier_raw": tier_raw,
            "tier_key": _TIER_KEYS[tier_raw],
        }

    capital_province_id = _optional_positive_int32(
        frame.get("capital_province_id"), "capital_province_id"
    )
    immediate_liege_id = _optional_positive_int32(
        frame.get("immediate_liege_character_id"),
        "immediate_liege_character_id",
    )
    top_liege_id = _positive_int32(
        frame.get("top_liege_character_id"), "top_liege_character_id"
    )
    independent = _bool(frame.get("independent"), "independent")
    if independent is not (immediate_liege_id is None):
        raise ValueError("independent and immediate liege disagree")
    if immediate_liege_id == player_character_id:
        raise ValueError("self immediate liege must be canonicalized to absent")
    if independent and top_liege_id != player_character_id:
        raise ValueError("independent top liege must equal the player character")
    if not independent and top_liege_id == player_character_id:
        raise ValueError("vassal top liege cannot equal the player character")

    government_value = frame.get("government")
    government: dict[str, object] | None
    if government_value is None:
        government = None
    else:
        government_frame = _exact_object(
            government_value, _GOVERNMENT_FIELDS, "government"
        )
        government_key = _stable_key(government_frame.get("key"), "government.key")
        flags = _lexical_key_vector(
            government_frame.get("flags"), "government.flags"
        )
        flag_count = _int(
            government_frame.get("native_flag_count"),
            "government.native_flag_count",
            minimum=0,
            maximum=2**31 - 1,
        )
        if flag_count != len(flags):
            raise ValueError("government flag count does not match the full span")
        government = {
            **government_frame,
            "key": government_key,
            "flags": flags,
            "native_flag_count": flag_count,
        }

    return {
        **frame,
        "local_player_id": local_player_id,
        "player_character_id": player_character_id,
        "player_character_alive": player_character_alive,
        "primary_title": primary_title,
        "capital_province_id": capital_province_id,
        "immediate_liege_character_id": immediate_liege_id,
        "top_liege_character_id": top_liege_id,
        "independent": independent,
        "government": government,
        "selected_game_rule_tokens": tokens,
        "native_selected_game_rule_token_count": token_count,
        "readiness": readiness,
        "unavailable_reason": None,
        "provenance": provenance,
    }
