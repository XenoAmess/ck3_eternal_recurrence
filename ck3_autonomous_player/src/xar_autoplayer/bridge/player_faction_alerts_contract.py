"""Strict v1 contract for paused player-faction alert observations.

The top-level frame can remain available when the exact-build reader has
proved the played-character identity and targeting-faction count but cannot
yet publish targeting rows or county exposures.  Every planner classification
is derived only after all alert components are ready.
"""

from __future__ import annotations

import re
from typing import Final


QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY: Final = (
    "game.command.query-player-faction-alerts-v1"
)
QUERY_PLAYER_FACTION_ALERTS_V1_STEP: Final = "query-player-faction-alerts-v1"
PLAYER_FACTION_ALERTS_V1_GAME_VERSION: Final = "1.19.0.6"
PLAYER_FACTION_ALERTS_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
PLAYER_FACTION_ALERTS_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-player-faction-alerts-v1"
)
PLAYER_FACTION_ALERTS_V1_CONTRACT_STAGE: Final = (
    "targeting_count_live_rows_and_county_fixture_pending_native_readers"
)
PLAYER_FACTION_ALERTS_V1_READER_MODE: Final = (
    "campaign_root_targeting_count_with_fixture_only_details"
)
PLAYER_FACTION_ALERTS_V1_NEXT_REVERSE_ENGINEERING_ENTRY: Final = (
    "faction_alert_targeting_span_and_sub_realm_county_membership_readers"
)
PLAYER_FACTION_ALERTS_V1_TARGETING_ROWS_UNAVAILABLE_REASON: Final = (
    "targeting_rows_native_reader_not_frozen"
)
PLAYER_FACTION_ALERTS_V1_COUNTY_EXPOSURE_UNAVAILABLE_REASON: Final = (
    "county_exposure_native_reader_not_frozen"
)
PLAYER_FACTION_ALERTS_V1_FIXED_POINT_SCALE: Final = 100_000

_FIELDS: Final = {
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "player_character_id",
    "targeting_faction_count",
    "targeting_factions",
    "county_exposures",
    "planner_projection",
    "readiness",
    "component_unavailable_reasons",
    "unavailable_reason",
    "provenance",
}
_TARGETING_FACTION_FIELDS: Final = {
    "faction_id",
    "faction_type_key",
    "target_character_id",
    "leader_character_id",
    "leader_is_human",
    "special_character_id",
    "special_title_id",
    "faction_at_war",
    "faction_war_id",
    "power",
    "power_threshold",
    "discontent",
    "discontent_per_month",
    "months_until_max_discontent",
    "character_member_ids",
    "county_member_title_ids",
    "dangerous_by_stock_rule",
    "danger_reason",
}
_COUNTY_EXPOSURE_FIELDS: Final = {
    "county_title_id",
    "faction_id",
    "faction_type_key",
    "target_character_id",
    "power",
    "power_threshold",
    "dangerous_by_stock_rule",
    "danger_reason",
}
_PLANNER_FIELDS: Final = {
    "status",
    "present",
    "dangerous",
    "dangerous_faction_ids",
    "watch_faction_ids",
    "war_handoff_faction_ids",
    "exposed_county_title_ids",
    "exact_ultimatum_timing_ready",
}
_READINESS_FIELDS: Final = {
    "targeting_count_ready",
    "identity_ready",
    "targeting_rows_ready",
    "county_exposure_ready",
    "stock_dangerous_predicate_ready",
    "same_frame_ready",
    "alert_ready",
    "exact_ultimatum_timing_ready",
}
_COMPONENT_REASON_FIELDS: Final = {"targeting_rows", "county_exposure"}
_PROVENANCE_FIELDS: Final = {
    "game_version",
    "executable_sha256",
    "backend_id",
}
_PROVENANCE_VALUES: Final = {
    "game_version": PLAYER_FACTION_ALERTS_V1_GAME_VERSION,
    "executable_sha256": PLAYER_FACTION_ALERTS_V1_EXECUTABLE_SHA256,
    "backend_id": PLAYER_FACTION_ALERTS_V1_BACKEND_ID,
}
_UNAVAILABLE_REASONS: Final = {
    "reader_not_implemented",
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "state_changed",
}
_STABLE_KEY = re.compile(r"^[a-z0-9_]+$")


def _int(value: object, field: str, *, minimum: int, maximum: int) -> int:
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


def _positive_uint64(value: object, field: str) -> int:
    return _int(value, field, minimum=1, maximum=2**64 - 1)


def _int64(value: object, field: str) -> int:
    return _int(value, field, minimum=-(2**63), maximum=2**63 - 1)


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _nullable_bool(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return _bool(value, field)


def _stable_key(value: object, field: str) -> str:
    if not isinstance(value, str) or _STABLE_KEY.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable lowercase key")
    return value


def _nullable_stable_key(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _stable_key(value, field)


def _nullable_positive_int32(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, field)


def _nullable_positive_uint64(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_uint64(value, field)


def _fixed_point(
    value: object, field: str, *, non_negative: bool = False
) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"{field} must contain exactly raw and scale")
    raw = _int64(value.get("raw"), f"{field}.raw")
    scale = _int(
        value.get("scale"),
        f"{field}.scale",
        minimum=1,
        maximum=2**31 - 1,
    )
    if scale != PLAYER_FACTION_ALERTS_V1_FIXED_POINT_SCALE:
        raise ValueError(f"{field}.scale must match the frozen exact build")
    if non_negative and raw < 0:
        raise ValueError(f"{field}.raw must be non-negative")
    return {"raw": raw, "scale": scale}


def _sorted_unique_ids(
    value: object,
    field: str,
    *,
    uint64: bool = False,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    validator = _positive_uint64 if uint64 else _positive_int32
    ids = [validator(item, f"{field}[{index}]") for index, item in enumerate(value)]
    if ids != sorted(set(ids)):
        raise ValueError(f"{field} must be sorted and unique")
    return ids


def _provenance(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != _PROVENANCE_FIELDS:
        raise ValueError("provenance must contain exactly the v1 fields")
    if any(value.get(key) != expected for key, expected in _PROVENANCE_VALUES.items()):
        raise ValueError("provenance does not match the frozen exact build")
    return {key: str(value[key]) for key in _PROVENANCE_VALUES}


def _targeting_faction(value: object, index: int) -> dict[str, object]:
    field = f"targeting_factions[{index}]"
    if not isinstance(value, dict) or set(value) != _TARGETING_FACTION_FIELDS:
        raise ValueError(f"{field} must contain exactly the v1 fields")
    faction_at_war = _bool(value.get("faction_at_war"), f"{field}.faction_at_war")
    war_id = _nullable_positive_int32(
        value.get("faction_war_id"), f"{field}.faction_war_id"
    )
    if not faction_at_war and war_id is not None:
        raise ValueError(f"{field}.faction_war_id requires faction_at_war")
    dangerous = _bool(
        value.get("dangerous_by_stock_rule"),
        f"{field}.dangerous_by_stock_rule",
    )
    danger_reason = _stable_key(
        value.get("danger_reason"), f"{field}.danger_reason"
    )
    months = value.get("months_until_max_discontent")
    if months is not None:
        months = _int(
            months,
            f"{field}.months_until_max_discontent",
            minimum=0,
            maximum=2**31 - 1,
        )
    leader_character_id = _nullable_positive_int32(
        value.get("leader_character_id"), f"{field}.leader_character_id"
    )
    leader_is_human = _bool(
        value.get("leader_is_human"), f"{field}.leader_is_human"
    )
    if leader_character_id is None and leader_is_human:
        raise ValueError(f"{field}.leader_is_human requires a leader identity")
    faction_type_key = _stable_key(
        value.get("faction_type_key"), f"{field}.faction_type_key"
    )
    discontent_per_month = _fixed_point(
        value.get("discontent_per_month"),
        f"{field}.discontent_per_month",
    )
    if leader_is_human:
        expected_dangerous = True
        expected_reason = "human_faction_leader"
    elif faction_type_key == "peasant_faction" and months is not None and months <= 12:
        expected_dangerous = True
        expected_reason = "peasant_ultimatum_within_12_months"
    elif faction_type_key == "peasant_faction":
        expected_dangerous = False
        expected_reason = "peasant_ultimatum_not_within_12_months"
    elif faction_type_key != "peasant_faction" and discontent_per_month["raw"] > 0:
        expected_dangerous = True
        expected_reason = "non_peasant_discontent_increasing"
    else:
        expected_dangerous = False
        expected_reason = "non_peasant_discontent_not_increasing"
    if dangerous is not expected_dangerous or danger_reason != expected_reason:
        raise ValueError(f"{field} stock dangerous result is inconsistent")
    return {
        "faction_id": _positive_int32(value.get("faction_id"), f"{field}.faction_id"),
        "faction_type_key": faction_type_key,
        "target_character_id": _positive_int32(
            value.get("target_character_id"), f"{field}.target_character_id"
        ),
        "leader_character_id": leader_character_id,
        "leader_is_human": leader_is_human,
        "special_character_id": _nullable_positive_int32(
            value.get("special_character_id"), f"{field}.special_character_id"
        ),
        "special_title_id": _nullable_positive_int32(
            value.get("special_title_id"), f"{field}.special_title_id"
        ),
        "faction_at_war": faction_at_war,
        "faction_war_id": war_id,
        "power": _fixed_point(value.get("power"), f"{field}.power", non_negative=True),
        "power_threshold": _fixed_point(
            value.get("power_threshold"),
            f"{field}.power_threshold",
            non_negative=True,
        ),
        "discontent": _fixed_point(
            value.get("discontent"), f"{field}.discontent", non_negative=True
        ),
        "discontent_per_month": discontent_per_month,
        "months_until_max_discontent": months,
        "character_member_ids": _sorted_unique_ids(
            value.get("character_member_ids"), f"{field}.character_member_ids"
        ),
        "county_member_title_ids": _sorted_unique_ids(
            value.get("county_member_title_ids"),
            f"{field}.county_member_title_ids",
        ),
        "dangerous_by_stock_rule": dangerous,
        "danger_reason": danger_reason,
    }


def _county_exposure(value: object, index: int) -> dict[str, object]:
    field = f"county_exposures[{index}]"
    if not isinstance(value, dict) or set(value) != _COUNTY_EXPOSURE_FIELDS:
        raise ValueError(f"{field} must contain exactly the v1 fields")
    dangerous = _bool(
        value.get("dangerous_by_stock_rule"),
        f"{field}.dangerous_by_stock_rule",
    )
    danger_reason = _nullable_stable_key(
        value.get("danger_reason"), f"{field}.danger_reason"
    )
    faction_type_key = _stable_key(
        value.get("faction_type_key"), f"{field}.faction_type_key"
    )
    target_character_id = _positive_int32(
        value.get("target_character_id"), f"{field}.target_character_id"
    )
    power = _fixed_point(
        value.get("power"), f"{field}.power", non_negative=True
    )
    threshold = _fixed_point(
        value.get("power_threshold"),
        f"{field}.power_threshold",
        non_negative=True,
    )
    if (
        faction_type_key != "populist_faction"
        or power["raw"] <= threshold["raw"]
        or not dangerous
        or danger_reason
        != "player_county_in_powerful_liege_targeting_populist_faction"
    ):
        raise ValueError(f"{field} is not a stock dangerous county exposure")
    return {
        "county_title_id": _positive_int32(
            value.get("county_title_id"), f"{field}.county_title_id"
        ),
        "faction_id": _positive_int32(
            value.get("faction_id"), f"{field}.faction_id"
        ),
        "faction_type_key": faction_type_key,
        "target_character_id": target_character_id,
        "power": power,
        "power_threshold": threshold,
        "dangerous_by_stock_rule": dangerous,
        "danger_reason": danger_reason,
    }


def _readiness(value: object) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != _READINESS_FIELDS:
        raise ValueError("readiness must contain exactly the v1 fields")
    readiness = {key: _bool(value.get(key), f"readiness.{key}") for key in _READINESS_FIELDS}
    if readiness["exact_ultimatum_timing_ready"]:
        raise ValueError("exact ultimatum timing is not ready in v1")
    return readiness


def _component_reasons(value: object) -> dict[str, str | None]:
    if not isinstance(value, dict) or set(value) != _COMPONENT_REASON_FIELDS:
        raise ValueError(
            "component_unavailable_reasons must contain exactly the v1 fields"
        )
    return {
        key: _nullable_stable_key(value.get(key), f"component_unavailable_reasons.{key}")
        for key in _COMPONENT_REASON_FIELDS
    }


def _planner_projection(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _PLANNER_FIELDS:
        raise ValueError("planner_projection must contain exactly the v1 fields")
    status = value.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("planner_projection.status is invalid")
    projection = {
        "status": status,
        "present": _nullable_bool(value.get("present"), "planner_projection.present"),
        "dangerous": _nullable_bool(
            value.get("dangerous"), "planner_projection.dangerous"
        ),
        "dangerous_faction_ids": _sorted_unique_ids(
            value.get("dangerous_faction_ids"),
            "planner_projection.dangerous_faction_ids",
        ),
        "watch_faction_ids": _sorted_unique_ids(
            value.get("watch_faction_ids"),
            "planner_projection.watch_faction_ids",
        ),
        "war_handoff_faction_ids": _sorted_unique_ids(
            value.get("war_handoff_faction_ids"),
            "planner_projection.war_handoff_faction_ids",
        ),
        "exposed_county_title_ids": _sorted_unique_ids(
            value.get("exposed_county_title_ids"),
            "planner_projection.exposed_county_title_ids",
        ),
        "exact_ultimatum_timing_ready": _bool(
            value.get("exact_ultimatum_timing_ready"),
            "planner_projection.exact_ultimatum_timing_ready",
        ),
    }
    if projection["exact_ultimatum_timing_ready"]:
        raise ValueError("planner projection cannot claim exact ultimatum timing")
    if status == "unavailable" and (
        projection["present"] is not None
        or projection["dangerous"] is not None
        or any(
            projection[name]
            for name in (
                "dangerous_faction_ids",
                "watch_faction_ids",
                "war_handoff_faction_ids",
                "exposed_county_title_ids",
            )
        )
    ):
        raise ValueError("unavailable planner projection must not guess alerts")
    if status == "available" and (
        projection["present"] is None or projection["dangerous"] is None
    ):
        raise ValueError("available planner projection requires boolean summary")
    return projection


def normalize_player_faction_alerts_v1(
    value: object,
    *,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate and normalize one exact paused faction-alert frame."""

    expected_date_raw = _int(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_snapshot_revision = _positive_uint64(
        expected_snapshot_revision, "expected_snapshot_revision"
    )
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("player faction alerts must contain exactly the v1 fields")
    if value.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if value.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("snapshot_revision does not match the paused frame")
    provenance = _provenance(value.get("provenance"))
    readiness = _readiness(value.get("readiness"))
    reasons = _component_reasons(value.get("component_unavailable_reasons"))
    planner = _planner_projection(value.get("planner_projection"))
    targeting_value = value.get("targeting_factions")
    exposures_value = value.get("county_exposures")
    if not isinstance(targeting_value, list) or not isinstance(exposures_value, list):
        raise ValueError("faction rows and county exposures must be lists")

    status = value.get("status")
    if status == "unavailable":
        if value.get("unavailable_reason") not in _UNAVAILABLE_REASONS:
            raise ValueError("unavailable_reason is invalid")
        if (
            value.get("date_raw") not in {None, expected_date_raw}
            or value.get("player_character_id") is not None
            or value.get("targeting_faction_count") is not None
            or targeting_value
            or exposures_value
            or any(readiness.values())
            or planner["status"] != "unavailable"
            or any(reason is not None for reason in reasons.values())
        ):
            raise ValueError("unavailable frame must not expose partial observations")
        return {
            **value,
            "planner_projection": planner,
            "readiness": readiness,
            "component_unavailable_reasons": reasons,
            "provenance": provenance,
        }
    if status != "available":
        raise ValueError("status is invalid")
    if value.get("unavailable_reason") is not None:
        raise ValueError("available frame cannot carry unavailable_reason")
    if value.get("date_raw") != expected_date_raw:
        raise ValueError("date_raw does not match the paused frame")
    if not (
        readiness["identity_ready"]
        and readiness["targeting_count_ready"]
        and readiness["same_frame_ready"]
    ):
        raise ValueError("available frame requires same-frame identity and targeting count")

    player_character_id = _positive_int32(
        value.get("player_character_id"), "player_character_id"
    )
    targeting_count = _int(
        value.get("targeting_faction_count"),
        "targeting_faction_count",
        minimum=0,
        maximum=2**31 - 1,
    )
    targeting = (
        [_targeting_faction(row, index) for index, row in enumerate(targeting_value)]
        if readiness["targeting_rows_ready"]
        else []
    )
    if readiness["targeting_rows_ready"]:
        if reasons["targeting_rows"] is not None:
            raise ValueError("ready targeting rows cannot carry an unavailable reason")
        faction_ids = [int(row["faction_id"]) for row in targeting]
        if faction_ids != sorted(set(faction_ids)):
            raise ValueError("targeting faction rows must have sorted unique identities")
        if len(targeting) != targeting_count:
            raise ValueError("targeting rows must match targeting_faction_count")
        if any(
            int(row["target_character_id"]) != player_character_id
            for row in targeting
        ):
            raise ValueError("targeting faction target must be the played character")
    elif (
        targeting_value
        or reasons["targeting_rows"]
        != PLAYER_FACTION_ALERTS_V1_TARGETING_ROWS_UNAVAILABLE_REASON
    ):
        raise ValueError("unready targeting rows must be empty and explain why")

    exposures = (
        [_county_exposure(row, index) for index, row in enumerate(exposures_value)]
        if readiness["county_exposure_ready"]
        else []
    )
    if readiness["county_exposure_ready"]:
        if reasons["county_exposure"] is not None:
            raise ValueError("ready county exposure cannot carry an unavailable reason")
        exposure_ids = [int(row["county_title_id"]) for row in exposures]
        if exposure_ids != sorted(set(exposure_ids)):
            raise ValueError("county exposures must have sorted unique county identities")
        if any(
            int(row["target_character_id"]) == player_character_id
            for row in exposures
        ):
            raise ValueError("county exposure target must not be the played character")
    elif (
        exposures_value
        or reasons["county_exposure"]
        != PLAYER_FACTION_ALERTS_V1_COUNTY_EXPOSURE_UNAVAILABLE_REASON
    ):
        raise ValueError("unready county exposure must be empty and explain why")

    expected_alert_ready = (
        readiness["targeting_rows_ready"]
        and readiness["county_exposure_ready"]
        and readiness["stock_dangerous_predicate_ready"]
        and readiness["same_frame_ready"]
    )
    if readiness["alert_ready"] is not expected_alert_ready:
        raise ValueError("alert_ready must be derived from the ready components")
    if readiness["stock_dangerous_predicate_ready"] is not readiness[
        "targeting_rows_ready"
    ]:
        raise ValueError("stock dangerous predicate readiness must match targeting rows")

    if readiness["alert_ready"]:
        expected_dangerous = sorted(
            int(row["faction_id"])
            for row in targeting
            if bool(row["dangerous_by_stock_rule"])
            and not bool(row["faction_at_war"])
        )
        expected_watch = sorted(
            int(row["faction_id"])
            for row in targeting
            if not bool(row["dangerous_by_stock_rule"])
            and not bool(row["faction_at_war"])
        )
        expected_war = sorted(
            int(row["faction_id"])
            for row in targeting
            if bool(row["faction_at_war"])
        )
        expected_exposed = sorted(
            int(row["county_title_id"])
            for row in exposures
            if bool(row["dangerous_by_stock_rule"])
        )
        expected_present = bool(targeting or exposures)
        expected_danger = bool(expected_dangerous or expected_exposed)
        expected_projection = {
            "status": "available",
            "present": expected_present,
            "dangerous": expected_danger,
            "dangerous_faction_ids": expected_dangerous,
            "watch_faction_ids": expected_watch,
            "war_handoff_faction_ids": expected_war,
            "exposed_county_title_ids": expected_exposed,
            "exact_ultimatum_timing_ready": False,
        }
        if planner != expected_projection:
            raise ValueError("planner projection is not derived from the ready rows")
    elif planner["status"] != "unavailable":
        raise ValueError("unready alert components require unavailable planner projection")

    return {
        **value,
        "player_character_id": player_character_id,
        "targeting_faction_count": targeting_count,
        "targeting_factions": targeting,
        "county_exposures": exposures,
        "planner_projection": planner,
        "readiness": readiness,
        "component_unavailable_reasons": reasons,
        "provenance": provenance,
    }


def validate_player_faction_war_handoffs_v1(
    value: dict[str, object], active_wars: object
) -> None:
    """Require every published faction-war identity in the same active-war set."""

    rows = value.get("targeting_factions")
    if not isinstance(rows, list):
        raise ValueError("normalized targeting_factions must be a list")
    referenced = {
        int(war_id)
        for row in rows
        if isinstance(row, dict)
        and (war_id := row.get("faction_war_id")) is not None
    }
    if not referenced:
        return
    if not isinstance(active_wars, list):
        raise ValueError("faction war handoff requires same-frame active_wars")
    active_ids = {
        int(war_id)
        for row in active_wars
        if isinstance(row, dict)
        and not isinstance((war_id := row.get("war_id")), bool)
        and isinstance(war_id, int)
        and 1 <= war_id <= 2**31 - 1
    }
    missing = sorted(referenced - active_ids)
    if missing:
        raise ValueError(
            "faction war handoff identities are absent from active_wars: "
            + ",".join(str(war_id) for war_id in missing)
        )


__all__ = [
    "PLAYER_FACTION_ALERTS_V1_BACKEND_ID",
    "PLAYER_FACTION_ALERTS_V1_EXECUTABLE_SHA256",
    "PLAYER_FACTION_ALERTS_V1_FIXED_POINT_SCALE",
    "PLAYER_FACTION_ALERTS_V1_CONTRACT_STAGE",
    "QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY",
    "QUERY_PLAYER_FACTION_ALERTS_V1_STEP",
    "normalize_player_faction_alerts_v1",
    "validate_player_faction_war_handoffs_v1",
]
