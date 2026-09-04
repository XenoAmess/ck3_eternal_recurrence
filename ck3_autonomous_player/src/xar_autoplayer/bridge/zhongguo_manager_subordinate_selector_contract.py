"""Typed contract for the provider-observed ZhongGuo B3 selector."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-manager-subordinate-selector-v1"
)
QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP: Final = (
    "query-zhongguo-manager-subordinate-selector-v1"
)
QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP}-"
)
ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_KIND_V1: Final = (
    "zg361-bounded-ai-direct-manager-selection-v1"
)
ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_GAME_VERSION_V1: Final = "1.19.0.6"
ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_EXE_SHA256_V1: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)

_NONCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_FRAME_KEYS = {
    "schema_version",
    "status",
    "selector_kind",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "provider_observed",
    "selection",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_SELECTION_KEYS = {
    "manager_character_id",
    "subordinate_character_id",
    "manager_contract_id",
    "subordinate_contract_id",
    "manager_primary_title_id",
    "manager_primary_title_tier_raw",
    "manager_primary_title_tier_key",
    "manager_government_key",
}
_READINESS_KEYS = {
    "exact_build_ready",
    "player_binding_ready",
    "relationship_enumeration_ready",
    "manager_eligibility_ready",
    "direct_subordinate_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE = {
    "game_version": ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_GAME_VERSION_V1,
    "executable_sha256": ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_EXE_SHA256_V1,
    "subject_contract_storage_slot_rva": "0x570CCA0",
    "subject_contract_fallback_slot_rva": "0x570CC50",
    "immediate_liege_rva": "0x2613480",
    "primary_title_rva": "0x25F3350",
    "effective_government_rva": "0x26165B0",
    "is_human_player_rva": "0x28BCEB0",
}
_UNAVAILABLE_REASONS = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "native_relationship_enumeration_unavailable",
    "no_bounded_ai_direct_manager",
    "bounded_ai_manager_has_no_direct_subordinate",
    "state_changed",
    "internal_error",
}
_TIER_KEYS = {3: "duchy", 4: "kingdom", 5: "empire", 6: "hegemony"}


@dataclass(frozen=True, slots=True)
class ZhongguoManagerSubordinateSelectorQueryV1:
    request_nonce: str


def validate_manager_subordinate_selector_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a 1-64 byte ASCII token")
    return value


def query_zhongguo_manager_subordinate_selector_v1_step(
    request_nonce: object,
) -> str:
    nonce = validate_manager_subordinate_selector_nonce_v1(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP_PREFIX}"
        f"{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_manager_subordinate_selector_v1_step(
    step: object,
) -> ZhongguoManagerSubordinateSelectorQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP_PREFIX
    ):
        return None
    encoded = step.removeprefix(
        QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP_PREFIX
    )
    if not encoded or len(encoded) % 2:
        return None
    try:
        nonce = bytes.fromhex(encoded).decode("ascii")
        nonce = validate_manager_subordinate_selector_nonce_v1(nonce)
    except (UnicodeDecodeError, ValueError):
        return None
    if nonce.encode("ascii").hex() != encoded:
        return None
    return ZhongguoManagerSubordinateSelectorQueryV1(nonce)


def _int(value: object, name: str, *, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in range")
    return value


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def normalize_native_zhongguo_manager_subordinate_selector_v1(
    value: object,
    *,
    expected_query: ZhongguoManagerSubordinateSelectorQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    frame = _exact(value, _FRAME_KEYS, "selector frame")
    if frame["schema_version"] != 1:
        raise ValueError("selector frame has an unsupported schema")
    if frame["selector_kind"] != ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_KIND_V1:
        raise ValueError("selector kind drifted")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("selector nonce drifted")
    if frame["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("selector native revision drifted")
    if frame["date_raw"] != expected_date_raw:
        raise ValueError("selector date drifted")
    if frame["player_character_id"] != expected_player_character_id:
        raise ValueError("selector player drifted")
    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(item, bool) for item in readiness.values()):
        raise ValueError("selector readiness must be boolean")
    provenance = _exact(frame["provenance"], set(_PROVENANCE), "provenance")
    if provenance != _PROVENANCE:
        raise ValueError("selector exact-build provenance drifted")

    if frame["status"] == "unavailable":
        if (
            frame["unavailable_reason"] not in _UNAVAILABLE_REASONS
            or frame["provider_observed"] is not False
            or frame["selection"] is not None
            or readiness["ready"] is not False
        ):
            raise ValueError("selector unavailable frame leaks a candidate")
        return dict(frame)
    if (
        frame["status"] != "available"
        or frame["unavailable_reason"] is not None
        or frame["provider_observed"] is not True
        or frame["paused"] is not True
        or any(item is not True for item in readiness.values())
    ):
        raise ValueError("selector available frame is not fully observed")
    selection = _exact(frame["selection"], _SELECTION_KEYS, "selection")
    positive_ids = (
        "manager_character_id",
        "subordinate_character_id",
        "manager_contract_id",
        "subordinate_contract_id",
        "manager_primary_title_id",
    )
    for key in positive_ids:
        _int(selection[key], key, minimum=1, maximum=2**31 - 1)
    if selection["manager_character_id"] == selection["subordinate_character_id"]:
        raise ValueError("selector manager and subordinate must differ")
    tier = _int(
        selection["manager_primary_title_tier_raw"],
        "manager_primary_title_tier_raw",
        minimum=3,
        maximum=6,
    )
    if selection["manager_primary_title_tier_key"] != _TIER_KEYS[tier]:
        raise ValueError("selector title tier key disagrees with raw tier")
    if selection["manager_government_key"] != "celestial_government":
        raise ValueError("selector manager is not celestial government")
    return dict(frame)


__all__ = [
    "QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY",
    "QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP",
    "QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_STEP_PREFIX",
    "ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_KIND_V1",
    "ZhongguoManagerSubordinateSelectorQueryV1",
    "normalize_native_zhongguo_manager_subordinate_selector_v1",
    "parse_query_zhongguo_manager_subordinate_selector_v1_step",
    "query_zhongguo_manager_subordinate_selector_v1_step",
    "validate_manager_subordinate_selector_nonce_v1",
]
