"""Map the exact 1.20.0.3 county-conversion sibling of the clergy query."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, require_exact_native_build


SCHEMA = "xar.ck3.county-conversion/v1"
_KEYS = {
    "schema", "schema_version", "exact_build", "status", "failure", "capture_epoch",
    "date_raw", "owner_character_id", "owner_rite_id", "position_present",
    "incumbent_character_id", "incumbent_rite_id", "active_task_id", "current_task_key",
    "current_task_type", "current_progress_kind", "current_task_frozen",
    "current_percentage_progress_raw", "percentage_progress_maximum_raw",
    "fixed_point_scale", "current_conversion_monthly_rate_raw",
    "current_target_province_id", "current_target_county_title_id",
    "current_target_county_rite_id", "task_key", "native_task_shown", "native_task_valid",
    "candidate_collection_evaluated", "candidate_collection_complete", "candidate_count",
    "candidates", "action_eligibility_complete",
}
_CANDIDATE_KEYS = {
    "native_collection_ordinal", "province_id", "county_title_id", "holder_character_id",
    "county_rite_id", "directly_held_by_player", "native_target_valid",
    "native_monthly_rate_raw", "native_monthly_rate_scale",
}


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native county conversion integer is malformed: {field}")


def _nullable_integer(value: object, low: int, high: int, field: str) -> None:
    if value is not None:
        _integer(value, low, high, field)


def normalize_player_county_conversion_v1(
    value: object, *, snapshot: Mapping[str, object], clergy: Mapping[str, object],
) -> dict[str, object]:
    """Preserve raw rates, generation-bearing Rite IDs and independent statuses."""
    if (not isinstance(value, dict) or set(value) != _KEYS
            or value["schema"] != SCHEMA or type(value["schema_version"]) is not int
            or value["schema_version"] != 1):
        raise ValueError("native county conversion schema is malformed")
    exact = value["exact_build"]
    if (not isinstance(exact, dict)
            or set(exact) != {"game_version", "steam_build", "executable_sha256"}
            or type(exact["steam_build"]) is not int or exact["steam_build"] != 25652598):
        raise ValueError("native county conversion exact build is malformed")
    build = require_exact_native_build(exact["game_version"], exact["executable_sha256"])
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native county conversion belongs to another build")
    if (value["status"] not in ("available", "unavailable")
            or not isinstance(value["failure"], str) or not value["failure"]
            or value["task_key"] != "task_conversion"
            or not isinstance(value["current_task_key"], str)
            or value["action_eligibility_complete"] is not False
            or type(value["fixed_point_scale"]) is not int or value["fixed_point_scale"] != 100000
            or type(value["percentage_progress_maximum_raw"]) is not int
            or value["percentage_progress_maximum_raw"] != 10000000):
        raise ValueError("native county conversion status is malformed")
    _integer(value["capture_epoch"], 0, (1 << 64) - 1, "capture_epoch")
    for key in ("date_raw", "owner_character_id"):
        _integer(value[key], -(1 << 31), (1 << 31) - 1, key)
    for key in (
        "incumbent_character_id", "active_task_id", "current_task_type",
        "current_progress_kind", "current_target_province_id", "current_target_county_title_id",
    ):
        _nullable_integer(value[key], -(1 << 31), (1 << 31) - 1, key)
    for key in ("owner_rite_id", "incumbent_rite_id", "current_target_county_rite_id"):
        _nullable_integer(value[key], 0, 0xFFFFFFFF, key)
    for key in ("current_percentage_progress_raw", "current_conversion_monthly_rate_raw"):
        _nullable_integer(value[key], -(1 << 63), (1 << 63) - 1, key)
    for key in ("position_present", "candidate_collection_evaluated", "candidate_collection_complete"):
        if type(value[key]) is not bool:
            raise ValueError(f"native county conversion boolean is malformed: {key}")
    for key in ("current_task_frozen", "native_task_shown", "native_task_valid"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native county conversion nullable boolean is malformed: {key}")
    _integer(value["candidate_count"], 0, 0xFFFFFFFF, "candidate_count")
    candidates = value["candidates"]
    if not isinstance(candidates, list) or value["candidate_count"] != len(candidates):
        raise ValueError("native county conversion candidate collection is malformed")
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != _CANDIDATE_KEYS:
            raise ValueError("native county conversion candidate schema is malformed")
        _integer(candidate["native_collection_ordinal"], 0, 0xFFFFFFFF, "native_collection_ordinal")
        for key in ("province_id", "county_title_id", "holder_character_id"):
            _integer(candidate[key], -(1 << 31), (1 << 31) - 1, key)
        _nullable_integer(candidate["county_rite_id"], 0, 0xFFFFFFFF, "county_rite_id")
        _nullable_integer(candidate["native_monthly_rate_raw"], -(1 << 63), (1 << 63) - 1,
                          "native_monthly_rate_raw")
        for key in ("directly_held_by_player", "native_target_valid"):
            if type(candidate[key]) is not bool:
                raise ValueError(f"native county conversion candidate boolean is malformed: {key}")
        if type(candidate["native_monthly_rate_scale"]) is not int or candidate["native_monthly_rate_scale"] != 100000:
            raise ValueError("native county conversion candidate scale is malformed")
    if value["status"] == "available":
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["owner_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["failure"] != "none" or value["capture_epoch"] == 0
                or (clergy.get("status") == "available"
                    and value["capture_epoch"] != clergy.get("capture_epoch"))):
            raise ValueError("native county conversion differs from its queried player frame")
    # A rejected target, a legal empty collection, a frozen current task and a
    # failed component retain their own raw fields. Rates remain separate from
    # percentage progress; no destination Rite, action readiness or ETA is inferred.
    return deepcopy(value)
