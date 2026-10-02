"""Develop County observations with distinct legacy AI and .3 material profiles.

The .3 reader publishes native player-realm task/location predicates and current
county growth. Its readiness describes the observation, including observed
false predicates, rather than task assignment or proposed-task growth.
"""

from __future__ import annotations

import re
from typing import Final

from .campaign_root_context_contract import _normalize_council_progress
from .version_identity import CK3_12003


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
STEWARD_DEVELOP_COUNTY_12003_MATERIAL_STAGE: Final = (
    "native_player_realm_develop_county_material_v1"
)

_MATERIAL_FIELDS: Final = {
    "schema_version", "contract_stage", "status", "unavailable_reason",
    "snapshot_revision", "observed_date_raw", "player_character_id",
    "steward_character_id", "task_key", "shown", "valid",
    "task_failure_reason", "current_active_task_binding",
    "candidate_collection_scope", "candidate_collection_complete",
    "candidates", "same_frame_stable", "readiness", "provenance",
}
_MATERIAL_CANDIDATE_FIELDS: Final = {
    "county_title_id", "capital_province_id", "holder_character_id",
    "is_player_capital", "directly_held_by_player",
    "native_collection_ordinal", "native_target_valid",
    "monthly_development_rate", "development_progress",
}
_MATERIAL_BINDING_FIELDS: Final = {
    "position_key", "incumbent_character_id", "task_key",
    "task_type", "target", "frozen", "progress",
}
_MATERIAL_PROVENANCE_VALUES: Final = {
    "game_version": CK3_12003.game_version,
    "executable_sha256": CK3_12003.executable_sha256,
    "backend_id": "ck3-1.20.0.3-native-steward-develop-county-material-v1",
    "reader_mode": "native_player_realm_enumerator_predicates_and_current_growth",
    "next_reverse_engineering_entry": (
        "native_develop_county_ai_inputs_and_proposed_task_growth"
    ),
}

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


def _material_fixed_point(value: object, name: str) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"{name} must contain raw and scale")
    if type(value.get("scale")) is not int or value["scale"] != 100_000:
        raise ValueError(f"{name}.scale must be the native Q100000 scale")
    return {"raw": _int64(value.get("raw"), f"{name}.raw"), "scale": 100_000}


def _material_identity(value: object, name: str) -> int:
    """Retain a full-generation native character or title identity."""
    return _int(value, name, minimum=1, maximum=2**32 - 1)


def _material_binding(value: object, steward_id: int) -> dict[str, object]:
    name = "current_active_task_binding"
    if not isinstance(value, dict) or set(value) != _MATERIAL_BINDING_FIELDS:
        raise ValueError(f"{name} must contain exactly the root position fields")
    if value.get("position_key") != "councillor_steward":
        raise ValueError(f"{name} must bind the Steward position")
    if value.get("incumbent_character_id") != steward_id:
        raise ValueError(f"{name} must bind the observed Steward")
    task_type = value.get("task_type")
    if task_type not in {"general", "county", "court"}:
        raise ValueError(f"{name}.task_type is invalid")
    target = value.get("target")
    if task_type == "general":
        if target is not None:
            raise ValueError(f"{name} general task must not expose a target")
    else:
        identity = "province_id" if task_type == "county" else "character_id"
        kind = "province" if task_type == "county" else "character"
        if not isinstance(target, dict) or set(target) != {"kind", identity}:
            raise ValueError(f"{name}.target is invalid")
        if target.get("kind") != kind:
            raise ValueError(f"{name}.target kind is invalid")
        normalize_identity = _positive_int32 if task_type == "county" else _material_identity
        target = {
            "kind": kind,
            identity: normalize_identity(target[identity], f"{name}.target.{identity}"),
        }
    return {
        **value,
        "task_key": _stable_key(value.get("task_key"), f"{name}.task_key"),
        "target": target,
        "frozen": _bool(value.get("frozen"), f"{name}.frozen"),
        "progress": _normalize_council_progress(
            value.get("progress"), f"{name}.progress"
        ),
    }


def _material_candidate(value: object, index: int) -> dict[str, object]:
    name = f"candidates[{index}]"
    if not isinstance(value, dict) or set(value) != _MATERIAL_CANDIDATE_FIELDS:
        raise ValueError(f"{name} must contain exactly the material fields")
    progress = value.get("development_progress")
    if not isinstance(progress, dict) or set(progress) != {"current", "maximum"}:
        raise ValueError(f"{name}.development_progress is invalid")
    return {
        **value,
        **{
            field: _material_identity(value.get(field), f"{name}.{field}")
            for field in ("county_title_id", "holder_character_id")
        },
        "capital_province_id": _positive_int32(
            value.get("capital_province_id"), f"{name}.capital_province_id"
        ),
        **{
            field: _bool(value.get(field), f"{name}.{field}")
            for field in (
                "is_player_capital", "directly_held_by_player", "native_target_valid"
            )
        },
        "native_collection_ordinal": _int(
            value.get("native_collection_ordinal"), f"{name}.native_collection_ordinal",
            minimum=0, maximum=2**32 - 1,
        ),
        "monthly_development_rate": _material_fixed_point(
            value.get("monthly_development_rate"), f"{name}.monthly_development_rate",
        ),
        "development_progress": {
            key: _material_fixed_point(progress[key], f"{name}.development_progress.{key}")
            for key in ("current", "maximum")
        },
    }


def _normalize_material(
    value: dict[str, object], *, expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    if set(value) != _MATERIAL_FIELDS:
        raise ValueError("Develop County material must contain exactly the observed fields")
    if value.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if value.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("snapshot_revision does not match the paused frame")
    if value.get("task_key") != STEWARD_DEVELOP_COUNTY_TASK_KEY:
        raise ValueError("task_key is invalid")
    if value.get("candidate_collection_scope") != "player_realm":
        raise ValueError("candidate_collection_scope must be player_realm")
    provenance = value.get("provenance")
    if not isinstance(provenance, dict) or provenance != _MATERIAL_PROVENANCE_VALUES:
        raise ValueError("material provenance does not match the exact .3 reader")
    candidates = value.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    if value.get("status") == "unavailable":
        _stable_key(value.get("unavailable_reason"), "unavailable_reason")
        if (
            value.get("observed_date_raw") not in {None, expected_observed_date_raw}
            or any(value.get(field) is not None for field in (
                "player_character_id", "steward_character_id", "shown", "valid",
                "task_failure_reason", "current_active_task_binding",
            ))
            or candidates
            or any(value.get(field) is not False for field in (
                "candidate_collection_complete", "same_frame_stable", "readiness",
            ))
        ):
            raise ValueError("unavailable material must not invent an observed collection")
        return {**value, "candidates": [], "provenance": dict(provenance)}
    if value.get("status") != "available":
        raise ValueError("status is invalid")
    if value.get("unavailable_reason") is not None:
        raise ValueError("available material cannot carry unavailable_reason")
    if value.get("observed_date_raw") != expected_observed_date_raw:
        raise ValueError("observed_date_raw does not match the paused frame")
    if any(value.get(field) is not True for field in (
        "candidate_collection_complete", "same_frame_stable", "readiness",
    )):
        raise ValueError("available material requires a complete stable observation")
    owner = _material_identity(value.get("player_character_id"), "player_character_id")
    steward = _material_identity(value.get("steward_character_id"), "steward_character_id")
    shown = _bool(value.get("shown"), "shown")
    valid = _bool(value.get("valid"), "valid")
    reason = value.get("task_failure_reason")
    if shown and valid:
        if reason is not None:
            raise ValueError("valid shown task cannot carry task_failure_reason")
    elif reason != ("task_not_shown" if not shown else "task_invalid") or candidates:
        raise ValueError("observed blocked task must preserve its reason and empty collection")
    return {
        **value,
        "player_character_id": owner,
        "steward_character_id": steward,
        "shown": shown, "valid": valid,
        "current_active_task_binding": _material_binding(
            value.get("current_active_task_binding"), steward
        ),
        "candidates": [
            _material_candidate(row, index) for index, row in enumerate(candidates)
        ],
        "provenance": dict(provenance),
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
    if (
        isinstance(value, dict)
        and value.get("contract_stage") == STEWARD_DEVELOP_COUNTY_12003_MATERIAL_STAGE
    ):
        return _normalize_material(
            value, expected_observed_date_raw=expected_observed_date_raw,
            expected_snapshot_revision=expected_snapshot_revision,
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
    "STEWARD_DEVELOP_COUNTY_12003_MATERIAL_STAGE",
    "normalize_steward_develop_county_candidates_v1",
]
