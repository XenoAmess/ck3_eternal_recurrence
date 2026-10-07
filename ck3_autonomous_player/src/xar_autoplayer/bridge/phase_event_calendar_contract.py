"""Optional V2 roster calendar conditions for exact CK3 1.20.0.4.

This readonly leaf observes a loaded interval and two character calendar
conditions. It supplies neither native event eligibility/selection/order nor
loaded phase effects, and does not change the V2 composition or model gates.
"""

from __future__ import annotations

import copy


PHASE_EVENT_CALENDAR_LEAF = "phase_event_calendar_observation_v1"
PHASE_EVENT_CALENDAR_SCOPE = "v2_roster_character_calendar_condition"
PHASE_EVENT_CALENDAR_CK3_SHA256 = (
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
)
_UINT32_MASK = 0xFFFFFFFF
_NATIVE_DATE_EPOCH = 0x029C55A8
_ROOT_KEYS = {
    "schema_version", "scope", "status", "date_low32", "next_date_low32",
    "day_index", "next_day_index", "loaded_interval_days_raw",
    "loaded_interval_source_closed", "calendar_predicate_source_closed",
    "complete_phase_effects_ready", "source_ck3_sha256", "unavailable_reason",
    "occurrences",
}
_OCCURRENCE_KEYS = {
    "occurrence_index", "character_id", "source_public_cunit_id",
    "source_native_carmy_id", "source_regiment_id", "encounter_role",
    "phase_role", "current_calendar_predicate", "next_day_calendar_predicate",
    "current_remainder_raw", "next_remainder_raw",
}


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _nullable_integer(
    value: object, name: str, minimum: int, maximum: int,
) -> int | None:
    return None if value is None else _integer(value, name, minimum, maximum)


def _native_day_index(date_low32: int) -> int:
    difference = (date_low32 - _NATIVE_DATE_EPOCH) & _UINT32_MASK
    signed = difference if difference < 0x80000000 else difference - 0x100000000
    return signed // 24 if signed >= 0 else -((-signed) // 24)


def _expected_occurrences(armies: list[dict[str, object]]) -> list[dict[str, object]]:
    occurrences: list[dict[str, object]] = []
    for army in armies:
        source = {
            "source_public_cunit_id": army["army_id"],
            "source_native_carmy_id": army["native_carmy_id"],
            "encounter_role": army["encounter_role"],
        }
        commander = army.get("commander")
        if isinstance(commander, dict) and commander.get("status") == "available":
            occurrences.append({
                **source, "occurrence_index": len(occurrences),
                "character_id": commander["character_id"],
                "source_regiment_id": None, "phase_role": "commander",
            })
        knights = army.get("knights")
        members = knights.get("members") if isinstance(knights, dict) else None
        for member in members if isinstance(members, list) else []:
            occurrences.append({
                **source, "occurrence_index": len(occurrences),
                "character_id": member["character_id"],
                "source_regiment_id": member["source_regiment_id"],
                "phase_role": "knight",
            })
    return occurrences


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "schema_version": 1, "scope": PHASE_EVENT_CALENDAR_SCOPE,
        "status": "unavailable", "date_low32": None, "next_date_low32": None,
        "day_index": None, "next_day_index": None,
        "loaded_interval_days_raw": None, "loaded_interval_source_closed": False,
        "calendar_predicate_source_closed": False,
        "complete_phase_effects_ready": False,
        "source_ck3_sha256": PHASE_EVENT_CALENDAR_CK3_SHA256,
        "unavailable_reason": f"phase_event_calendar_fragment_invalid: {reason}",
        "occurrences": [],
    }


def normalize_phase_event_calendar_observation_v1(
    value: object, *, armies: list[dict[str, object]],
) -> dict[str, object] | None:
    """Retain absent/failed/zero observations independently of V2 readiness.

    Provenance is the supplied V2 roster, commander followed by each Knight
    role per Army, with no deduplication or claim about native event order.
    Full CharacterID zero and its generation bits are preserved.
    """
    if value is None:
        return None
    try:
        if not isinstance(value, dict) or set(value) != _ROOT_KEYS:
            raise ValueError("root keys are malformed")
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ValueError("schema_version must be 1")
        if value["scope"] != PHASE_EVENT_CALENDAR_SCOPE:
            raise ValueError("scope is malformed")
        if value["status"] not in ("available", "partial", "unavailable"):
            raise ValueError("status is malformed")
        if value["source_ck3_sha256"] != PHASE_EVENT_CALENDAR_CK3_SHA256:
            raise ValueError("source is not the exact actual4 executable")
        for field in ("loaded_interval_source_closed", "calendar_predicate_source_closed"):
            if type(value[field]) is not bool:
                raise ValueError(f"{field} must be bool")
        if value["complete_phase_effects_ready"] is not False:
            raise ValueError("complete_phase_effects_ready must remain false")
        reason = value["unavailable_reason"]
        if reason is not None and (type(reason) is not str or not reason):
            raise ValueError("unavailable_reason must be a nonempty string or null")
        normalized = dict(value)
        for field in ("date_low32", "next_date_low32", "loaded_interval_days_raw"):
            normalized[field] = _nullable_integer(value[field], field, 0, _UINT32_MASK)
        for field in ("day_index", "next_day_index"):
            normalized[field] = _nullable_integer(value[field], field, -(2**31), 2**31 - 1)
        date = normalized["date_low32"]
        next_date = normalized["next_date_low32"]
        if next_date is not None and (date is None or next_date != ((date + 24) & _UINT32_MASK)):
            raise ValueError("next_date_low32 differs from wrapped current date+24")
        calendar_closed = value["calendar_predicate_source_closed"]
        for date_field, day_field in (("date_low32", "day_index"),
                                      ("next_date_low32", "next_day_index")):
            day, observed_date = normalized[day_field], normalized[date_field]
            if day is not None and (not calendar_closed or observed_date is None
                                     or day != _native_day_index(observed_date)):
                raise ValueError(f"{day_field} differs from the admitted native producer")
        interval = normalized["loaded_interval_days_raw"]
        if interval is not None and not value["loaded_interval_source_closed"]:
            raise ValueError("loaded interval lacks its independent source closure")
        rows = value["occurrences"]
        expected = _expected_occurrences(armies)
        if not isinstance(rows, list) or len(rows) != len(expected):
            raise ValueError("occurrences differ from the complete V2 role roster")
        normalized_rows = []
        all_predicates_observed = True
        for index, (row, source) in enumerate(zip(rows, expected, strict=True)):
            if not isinstance(row, dict) or set(row) != _OCCURRENCE_KEYS:
                raise ValueError(f"occurrences[{index}] keys are malformed")
            item = dict(row)
            for field in ("occurrence_index", "source_public_cunit_id"):
                item[field] = _integer(row[field], field, 0, 2**31 - 1)
            item["character_id"] = _integer(row["character_id"], "character_id", 0, _UINT32_MASK)
            for field in ("source_native_carmy_id", "source_regiment_id"):
                item[field] = _nullable_integer(row[field], field, 0, 2**31 - 1)
            if any(item[field] != expected_value for field, expected_value in source.items()):
                raise ValueError(f"occurrences[{index}] changes V2 role provenance")
            for day_field, remainder_field, predicate_field in (
                ("day_index", "current_remainder_raw", "current_calendar_predicate"),
                ("next_day_index", "next_remainder_raw", "next_day_calendar_predicate"),
            ):
                remainder = _nullable_integer(row[remainder_field], remainder_field, 0, _UINT32_MASK)
                predicate = row[predicate_field]
                if predicate is not None and type(predicate) is not bool:
                    raise ValueError(f"{predicate_field} must be bool or null")
                if (remainder is None) != (predicate is None):
                    raise ValueError(f"{predicate_field} and its remainder must be observed together")
                ready = (calendar_closed and value["loaded_interval_source_closed"]
                         and interval is not None and interval > 0
                         and normalized[day_field] is not None)
                if remainder is not None:
                    if not ready:
                        raise ValueError(f"{predicate_field} lacks observed nonzero calendar operands")
                    expected_remainder = ((item["character_id"] + normalized[day_field]) & _UINT32_MASK) % interval
                    if remainder != expected_remainder or predicate is not (remainder == 0):
                        raise ValueError(f"{predicate_field} differs from unsigned FullCharacterID calendar DIV")
                else:
                    all_predicates_observed = False
                item[remainder_field], item[predicate_field] = remainder, predicate
            normalized_rows.append(item)
        normalized["occurrences"] = normalized_rows
        complete = (value["loaded_interval_source_closed"] and calendar_closed
                    and interval is not None and interval > 0
                    and all(normalized[field] is not None for field in (
                        "date_low32", "next_date_low32", "day_index", "next_day_index"))
                    and all_predicates_observed)
        if value["status"] == "available" and (not complete or reason is not None):
            raise ValueError("available calendar fragment is incomplete")
        if interval == 0 and value["status"] != "partial":
            raise ValueError("observed interval zero must remain a partial fragment")
        if value["status"] != "available" and reason is None:
            raise ValueError("partial/unavailable calendar fragment requires its own reason")
        return copy.deepcopy(normalized)
    except (ValueError, KeyError, TypeError) as error:
        return _unavailable(str(error))
