"""Strict v1 contract for steward Develop County candidate observation.

The contract is intentionally usable before the exact-build candidate reader is
closed.  Production may advertise the query and return a typed unavailable
frame; only the native fixture can currently produce an available frame.
"""

from __future__ import annotations

import re
from typing import Final


QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY: Final = (
    "game.command.query-steward-develop-county-candidates-v1"
)
QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP: Final = (
    "query-steward-develop-county-candidates-v1"
)
STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_GAME_VERSION: Final = "1.19.0.6"
STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-steward-develop-county-candidates-v1"
)
STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE: Final = (
    "exact_build_contract_fixture_pending_live_reader"
)
STEWARD_DEVELOP_COUNTY_TASK_KEY: Final = "task_develop_county"
STEWARD_DEVELOP_COUNTY_TARGET_SELECTION_MODE: Final = (
    "engine_random_unscored"
)

_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "unavailable_reason",
    "snapshot_revision",
    "observed_date_raw",
    "player_character_id",
    "steward_character_id",
    "task_key",
    "shown",
    "valid",
    "task_failure_reason",
    "steward_increase_development_value_raw",
    "current_gold_raw",
    "no_ai_increase_development",
    "has_active_improve_development_directive",
    "target_selection_mode",
    "candidates",
    "same_frame_stable",
    "readiness",
    "provenance",
}
_CANDIDATE_FIELDS: Final = {
    "county_title_id",
    "capital_province_id",
    "holder_character_id",
    "is_player_capital",
    "directly_held_by_player",
    "native_legal",
    "development_level_raw",
    "development_progress_raw",
    "monthly_development_rate_raw",
    "max_development_level_raw",
    "terrain_key",
    "same_culture_as_player",
    "cultural_acceptance_threshold_passed",
}
_PROVENANCE_FIELDS: Final = {
    "game_version",
    "executable_sha256",
    "backend_id",
    "reader_mode",
    "next_reverse_engineering_entry",
}
_PROVENANCE_VALUES: Final = {
    "game_version": STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_GAME_VERSION,
    "executable_sha256": (
        STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_EXECUTABLE_SHA256
    ),
    "backend_id": STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID,
    "reader_mode": "contract_fixture_pending_live_reader",
    "next_reverse_engineering_entry": (
        "task_develop_county_native_candidate_enumerator_and_final_"
        "legality_call"
    ),
}
_UNAVAILABLE_REASONS: Final = {
    "reader_not_implemented",
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "state_changed",
}
_STABLE_KEY = re.compile(r"^[a-z0-9_]+$")


def _int(
    value: object, field: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, field: str) -> int:
    return _int(value, field, minimum=1, maximum=2**31 - 1)


def _int64(value: object, field: str) -> int:
    return _int(value, field, minimum=-(2**63), maximum=2**63 - 1)


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _stable_key(value: object, field: str) -> str:
    if not isinstance(value, str) or _STABLE_KEY.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable lowercase key")
    return value


def _provenance(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != _PROVENANCE_FIELDS:
        raise ValueError("provenance must contain exactly the v1 fields")
    if any(value.get(key) != expected for key, expected in _PROVENANCE_VALUES.items()):
        raise ValueError("provenance does not match the frozen exact build")
    return {key: str(value[key]) for key in _PROVENANCE_VALUES}


def _candidate(value: object, index: int) -> dict[str, object]:
    name = f"candidates[{index}]"
    if not isinstance(value, dict) or set(value) != _CANDIDATE_FIELDS:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    native_legal = _bool(value.get("native_legal"), f"{name}.native_legal")
    if native_legal is not True:
        raise ValueError("candidate enumeration may contain only native-legal rows")
    return {
        "county_title_id": _positive_int32(
            value.get("county_title_id"), f"{name}.county_title_id"
        ),
        "capital_province_id": _positive_int32(
            value.get("capital_province_id"), f"{name}.capital_province_id"
        ),
        "holder_character_id": _positive_int32(
            value.get("holder_character_id"), f"{name}.holder_character_id"
        ),
        "is_player_capital": _bool(
            value.get("is_player_capital"), f"{name}.is_player_capital"
        ),
        "directly_held_by_player": _bool(
            value.get("directly_held_by_player"),
            f"{name}.directly_held_by_player",
        ),
        "native_legal": native_legal,
        "development_level_raw": _int(
            value.get("development_level_raw"),
            f"{name}.development_level_raw",
            minimum=0,
            maximum=2**31 - 1,
        ),
        "development_progress_raw": _int64(
            value.get("development_progress_raw"),
            f"{name}.development_progress_raw",
        ),
        "monthly_development_rate_raw": _int64(
            value.get("monthly_development_rate_raw"),
            f"{name}.monthly_development_rate_raw",
        ),
        "max_development_level_raw": _int(
            value.get("max_development_level_raw"),
            f"{name}.max_development_level_raw",
            minimum=0,
            maximum=2**31 - 1,
        ),
        "terrain_key": _stable_key(
            value.get("terrain_key"), f"{name}.terrain_key"
        ),
        "same_culture_as_player": _bool(
            value.get("same_culture_as_player"),
            f"{name}.same_culture_as_player",
        ),
        "cultural_acceptance_threshold_passed": _bool(
            value.get("cultural_acceptance_threshold_passed"),
            f"{name}.cultural_acceptance_threshold_passed",
        ),
    }


def normalize_steward_develop_county_candidates_v1(
    value: object,
    *,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one strict paused frame without reconstructing CK3 rules."""

    expected_observed_date_raw = _int(
        expected_observed_date_raw,
        "expected_observed_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_snapshot_revision = _int(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError(
            "steward develop-county candidates must contain exactly the v1 fields"
        )
    if value.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if value.get("contract_stage") != STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE:
        raise ValueError("contract_stage is invalid")
    if value.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("snapshot_revision does not match the paused frame")
    if value.get("task_key") != STEWARD_DEVELOP_COUNTY_TASK_KEY:
        raise ValueError("task_key is invalid")
    if value.get("target_selection_mode") != STEWARD_DEVELOP_COUNTY_TARGET_SELECTION_MODE:
        raise ValueError("target_selection_mode is invalid")
    provenance = _provenance(value.get("provenance"))
    status = value.get("status")
    candidates_value = value.get("candidates")
    if not isinstance(candidates_value, list):
        raise ValueError("candidates must be a list")

    if status == "unavailable":
        reason = value.get("unavailable_reason")
        if reason not in _UNAVAILABLE_REASONS:
            raise ValueError("unavailable_reason is invalid")
        nullable = (
            "player_character_id",
            "steward_character_id",
            "shown",
            "valid",
            "task_failure_reason",
            "steward_increase_development_value_raw",
            "current_gold_raw",
            "no_ai_increase_development",
            "has_active_improve_development_directive",
        )
        if (
            value.get("observed_date_raw") not in {
                None,
                expected_observed_date_raw,
            }
            or
            any(value.get(name) is not None for name in nullable)
            or candidates_value
            or value.get("same_frame_stable") is not False
            or value.get("readiness") is not False
        ):
            raise ValueError("unavailable frame must not expose partial observations")
        return {
            **value,
            "candidates": [],
            "provenance": provenance,
        }
    if status != "available":
        raise ValueError("status is invalid")
    if value.get("observed_date_raw") != expected_observed_date_raw:
        raise ValueError("observed_date_raw does not match the paused frame")
    if value.get("unavailable_reason") is not None:
        raise ValueError("available frame cannot carry unavailable_reason")
    player_character_id = _positive_int32(
        value.get("player_character_id"), "player_character_id"
    )
    steward_character_id = _positive_int32(
        value.get("steward_character_id"), "steward_character_id"
    )
    shown = _bool(value.get("shown"), "shown")
    valid = _bool(value.get("valid"), "valid")
    failure_reason = value.get("task_failure_reason")
    if shown and valid:
        if failure_reason is not None:
            raise ValueError("valid shown task cannot carry task_failure_reason")
    else:
        failure_reason = _stable_key(failure_reason, "task_failure_reason")
        if candidates_value:
            raise ValueError("invalid or hidden task cannot expose candidates")
    if (
        value.get("same_frame_stable") is not True
        or value.get("readiness") is not True
    ):
        raise ValueError("available frame must be same-frame stable and ready")
    candidates = [
        _candidate(candidate, index)
        for index, candidate in enumerate(candidates_value)
    ]
    title_ids = [int(candidate["county_title_id"]) for candidate in candidates]
    province_ids = [
        int(candidate["capital_province_id"]) for candidate in candidates
    ]
    if len(title_ids) != len(set(title_ids)) or len(province_ids) != len(
        set(province_ids)
    ):
        raise ValueError("candidates must have unique full title and province IDs")
    return {
        **value,
        "player_character_id": player_character_id,
        "steward_character_id": steward_character_id,
        "shown": shown,
        "valid": valid,
        "task_failure_reason": failure_reason,
        "steward_increase_development_value_raw": _int64(
            value.get("steward_increase_development_value_raw"),
            "steward_increase_development_value_raw",
        ),
        "current_gold_raw": _int64(
            value.get("current_gold_raw"), "current_gold_raw"
        ),
        "no_ai_increase_development": _bool(
            value.get("no_ai_increase_development"),
            "no_ai_increase_development",
        ),
        "has_active_improve_development_directive": _bool(
            value.get("has_active_improve_development_directive"),
            "has_active_improve_development_directive",
        ),
        "candidates": candidates,
        "provenance": provenance,
    }


__all__ = [
    "QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY",
    "QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP",
    "STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID",
    "STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE",
    "normalize_steward_develop_county_candidates_v1",
]
