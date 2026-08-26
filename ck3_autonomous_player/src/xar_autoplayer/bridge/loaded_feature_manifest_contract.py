"""Strict contract for the exact-build loaded feature manifest."""

from __future__ import annotations

from typing import Final


QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY: Final = (
    "game.command.query-loaded-feature-manifest-v1"
)
QUERY_LOADED_FEATURE_MANIFEST_V1_STEP: Final = (
    "query-loaded-feature-manifest-v1"
)
LOADED_FEATURE_MANIFEST_V1_GAME_VERSION: Final = "1.19.0.6"
LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
LOADED_FEATURE_MANIFEST_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-loaded-feature-manifest-v1"
)

_FEATURE_DEFINITIONS: Final = (
    (0x3587, "garments_of_the_hre"),
    (0x3588, "fashion_of_the_abbasid_court"),
    (0x34A7, "the_northern_lords"),
    (0x3538, "hybridize_culture"),
    (0x3539, "diverge_culture"),
    (0x3270, "royal_court"),
    (0x366D, "reform_culture"),
    (0x34DC, "court_artifacts"),
    (0x3773, "the_fate_of_iberia"),
    (0x3608, "friends_and_foes"),
    (0x37CF, "tours_and_tournaments"),
    (0x37CE, "advanced_activities"),
    (0x36C4, "accolades"),
    (0x377A, "legacy_of_persia"),
    (0x35E0, "elegance_of_the_empire"),
    (0x394A, "wards_and_wardens"),
    (0x3B0A, "legends_of_the_dead"),
    (0x3A5B, "legends"),
    (0x3A09, "north_african_attire"),
    (0x3A08, "couture_of_the_capets"),
    (0x3953, "landless_playable"),
    (0x3A00, "admin_gov"),
    (0x3A02, "roads_to_power"),
    (0x3A01, "court_room_view"),
    (0x39DA, "wandering_nobles"),
    (0x3CBB, "west_slavic_attire"),
    (0x3A07, "medieval_monuments"),
    (0x3C98, "khans_of_the_steppe"),
    (0x3CA1, "nomads"),
    (0x3A06, "arctic_attire"),
    (0x39F7, "crowns_of_the_world"),
    (0x3D67, "landless_adventurer"),
    (0x39ED, "coronations"),
    (0x39EE, "all_under_heaven"),
    (0x39EF, "merit_admin"),
    (0x39F0, "advanced_aspirations"),
    (0x39F1, "barter_troops"),
    (0x39DB, "high_medieval_warfare_attire"),
    (0x39DC, "holy_buildings"),
    (0x39DD, "north_pacific_attire"),
    (0x39DE, "east_asian_wonders"),
    (0x39DF, "celestial_court_attire"),
    (0x4101, "symbols_of_authority"),
    (0x4102, "songs_of_the_realm"),
)

_FIELDS: Final = {
    "schema",
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "unavailable_reason",
    "build",
    "effective_feature_flags",
    "script_dlc_keys",
    "entitlements",
    "readiness",
    "provenance",
}
_BUILD_FIELDS: Final = {"version", "exe_sha256"}
_FEATURE_FLAGS_FIELDS: Final = {
    "status",
    "unavailable_reason",
    "native_count",
    "items",
}
_FEATURE_ITEM_FIELDS: Final = {
    "native_index",
    "cstring_id",
    "key",
    "enabled",
}
_SCRIPT_DLC_FIELDS: Final = {
    "status",
    "unavailable_reason",
    "enumerated_count",
    "keys",
}
_ENTITLEMENT_FIELDS: Final = {"status", "unavailable_reason", "items"}
_READINESS_KEYS: Final = (
    "effective_feature_flags_ready",
    "script_dlc_keys_ready",
    "entitlements_ready",
    "same_frame_ready",
    "actionable_ready",
)
_PROVENANCE_VALUES: Final = {
    "feature_root_slot_rva": "0x576CC68",
    "feature_bitset_rva": "root+0x2B0",
    "feature_enum_table_rva": "0x42F7850..0x42F7900",
    "script_dlc_set_rva": "0x5762590",
    "backend_id": LOADED_FEATURE_MANIFEST_V1_BACKEND_ID,
}
_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "feature_root_unavailable",
    "feature_counter_mismatch",
    "feature_registry_drift",
    "script_dlc_set_unavailable",
    "script_dlc_key_invalid",
    "state_changed",
    "internal_error",
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


def _normalize_build(value: object) -> dict[str, str]:
    build = _exact_object(value, _BUILD_FIELDS, "build")
    if (
        build.get("version") != LOADED_FEATURE_MANIFEST_V1_GAME_VERSION
        or build.get("exe_sha256")
        != LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
    ):
        raise ValueError("build does not match the frozen exact build")
    return {
        "version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
        "exe_sha256": LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
    }


def _normalize_provenance(value: object) -> dict[str, str]:
    provenance = _exact_object(
        value, set(_PROVENANCE_VALUES), "provenance"
    )
    if any(
        provenance.get(key) != expected
        for key, expected in _PROVENANCE_VALUES.items()
    ):
        raise ValueError("provenance does not match the frozen exact build")
    return dict(_PROVENANCE_VALUES)


def _normalize_readiness(
    value: object,
    *,
    available: bool,
) -> dict[str, bool]:
    readiness = _exact_object(value, set(_READINESS_KEYS), "readiness")
    normalized = {
        key: _bool(readiness.get(key), f"readiness.{key}")
        for key in _READINESS_KEYS
    }
    expected = {
        "effective_feature_flags_ready": available,
        "script_dlc_keys_ready": available,
        "entitlements_ready": False,
        "same_frame_ready": available,
        "actionable_ready": available,
    }
    if normalized != expected:
        raise ValueError("readiness fields disagree with status")
    return normalized


def _normalize_entitlements(value: object) -> dict[str, object]:
    entitlements = _exact_object(
        value, _ENTITLEMENT_FIELDS, "entitlements"
    )
    if entitlements != {
        "status": "unavailable",
        "unavailable_reason": "store_verdict_provenance_unclosed",
        "items": None,
    }:
        raise ValueError("entitlements must remain provenance-unclosed")
    return dict(entitlements)


def _normalize_feature_flags(
    value: object,
    *,
    available: bool,
    unavailable_reason: str | None,
) -> dict[str, object]:
    flags = _exact_object(
        value, _FEATURE_FLAGS_FIELDS, "effective_feature_flags"
    )
    if not available:
        if flags != {
            "status": "unavailable",
            "unavailable_reason": unavailable_reason,
            "native_count": None,
            "items": None,
        }:
            raise ValueError("unavailable feature flags invented native state")
        return dict(flags)
    if (
        flags.get("status") != "available"
        or flags.get("unavailable_reason") is not None
        or flags.get("native_count") != len(_FEATURE_DEFINITIONS)
    ):
        raise ValueError("available feature-flag header is invalid")
    raw_items = flags.get("items")
    if not isinstance(raw_items, list) or len(raw_items) != len(
        _FEATURE_DEFINITIONS
    ):
        raise ValueError("effective feature flags must contain all 44 items")
    items: list[dict[str, object]] = []
    for index, (expected_id, expected_key) in enumerate(
        _FEATURE_DEFINITIONS
    ):
        item = _exact_object(
            raw_items[index],
            _FEATURE_ITEM_FIELDS,
            f"effective_feature_flags.items[{index}]",
        )
        native_index = _int(
            item.get("native_index"),
            f"effective_feature_flags.items[{index}].native_index",
            minimum=0,
            maximum=len(_FEATURE_DEFINITIONS) - 1,
        )
        cstring_id = _int(
            item.get("cstring_id"),
            f"effective_feature_flags.items[{index}].cstring_id",
            minimum=1,
            maximum=2**32 - 1,
        )
        key = _stable_key(
            item.get("key"),
            f"effective_feature_flags.items[{index}].key",
        )
        enabled = _bool(
            item.get("enabled"),
            f"effective_feature_flags.items[{index}].enabled",
        )
        if (
            native_index != index
            or cstring_id != expected_id
            or key != expected_key
        ):
            raise ValueError("effective feature registry does not match v1")
        items.append(
            {
                "native_index": native_index,
                "cstring_id": cstring_id,
                "key": key,
                "enabled": enabled,
            }
        )
    return {
        "status": "available",
        "unavailable_reason": None,
        "native_count": len(_FEATURE_DEFINITIONS),
        "items": items,
    }


def _normalize_script_dlc_keys(
    value: object,
    *,
    available: bool,
    unavailable_reason: str | None,
) -> dict[str, object]:
    dlcs = _exact_object(value, _SCRIPT_DLC_FIELDS, "script_dlc_keys")
    if not available:
        if dlcs != {
            "status": "unavailable",
            "unavailable_reason": unavailable_reason,
            "enumerated_count": None,
            "keys": None,
        }:
            raise ValueError("unavailable script DLC keys invented native state")
        return dict(dlcs)
    if (
        dlcs.get("status") != "available"
        or dlcs.get("unavailable_reason") is not None
    ):
        raise ValueError("available script-DLC header is invalid")
    raw_keys = dlcs.get("keys")
    if not isinstance(raw_keys, list):
        raise ValueError("script_dlc_keys.keys must be a list")
    keys = [
        _stable_key(item, f"script_dlc_keys.keys[{index}]")
        for index, item in enumerate(raw_keys)
    ]
    if keys != sorted(keys, key=lambda item: item.encode("utf-8")):
        raise ValueError("script DLC keys must use UTF-8 bytewise order")
    if len(set(keys)) != len(keys):
        raise ValueError("script DLC keys must be unique")
    count = _int(
        dlcs.get("enumerated_count"),
        "script_dlc_keys.enumerated_count",
        minimum=0,
        maximum=2**31 - 1,
    )
    if count != len(keys):
        raise ValueError("script DLC count does not match the full vector")
    return {
        "status": "available",
        "unavailable_reason": None,
        "enumerated_count": count,
        "keys": keys,
    }


def normalize_loaded_feature_manifest_v1(
    value: object,
    *,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one atomic feature manifest without inferring ownership."""

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
    frame = _exact_object(value, _FIELDS, "loaded_feature_manifest")
    if frame.get("schema") != "loaded-feature-manifest-v1":
        raise ValueError("loaded_feature_manifest.schema is invalid")
    if frame.get("schema_version") != 1 or isinstance(
        frame.get("schema_version"), bool
    ):
        raise ValueError("loaded_feature_manifest.schema_version must be 1")
    status = frame.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("loaded_feature_manifest.status is invalid")
    revision = _int(
        frame.get("snapshot_revision"),
        "loaded_feature_manifest.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    date_raw = _int(
        frame.get("date_raw"),
        "loaded_feature_manifest.date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    if revision != expected_snapshot_revision:
        raise ValueError("loaded-feature snapshot revision binding changed")
    if date_raw != expected_date_raw:
        raise ValueError("loaded-feature date binding changed")

    available = status == "available"
    reason = frame.get("unavailable_reason")
    if available:
        if reason is not None:
            raise ValueError("available loaded-feature manifest has a reason")
    elif reason not in _UNAVAILABLE_REASONS:
        raise ValueError("loaded-feature unavailable_reason is invalid")

    build = _normalize_build(frame.get("build"))
    features = _normalize_feature_flags(
        frame.get("effective_feature_flags"),
        available=available,
        unavailable_reason=reason if isinstance(reason, str) else None,
    )
    dlcs = _normalize_script_dlc_keys(
        frame.get("script_dlc_keys"),
        available=available,
        unavailable_reason=reason if isinstance(reason, str) else None,
    )
    entitlements = _normalize_entitlements(frame.get("entitlements"))
    readiness = _normalize_readiness(
        frame.get("readiness"), available=available
    )
    provenance = _normalize_provenance(frame.get("provenance"))
    return {
        **frame,
        "schema": "loaded-feature-manifest-v1",
        "schema_version": 1,
        "status": status,
        "snapshot_revision": revision,
        "date_raw": date_raw,
        "unavailable_reason": reason,
        "build": build,
        "effective_feature_flags": features,
        "script_dlc_keys": dlcs,
        "entitlements": entitlements,
        "readiness": readiness,
        "provenance": provenance,
    }
