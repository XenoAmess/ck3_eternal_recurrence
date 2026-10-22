"""One validated JSON contract for the exact .4 four-trait observation."""
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Literal, TypeAlias, TypedDict

TraitKey: TypeAlias = Literal["pilgrim", "hajjaj", "lifestyle_scholar", "lifestyle_mystic"]
TRAIT_KEYS: tuple[TraitKey, ...] = ("pilgrim", "hajjaj", "lifestyle_scholar", "lifestyle_mystic")
SCHEMA = "ck3_12004_player_pilgrimage_traits_v1"


class PilgrimageTraitRow(TypedDict):
    trait_key: TraitKey
    has_track: bool
    present: bool | None
    experience_raw: int | None


class _PilgrimageTraitFields(TypedDict):
    schema: Literal["ck3_12004_player_pilgrimage_traits_v1"]
    read_only: Literal[True]
    capture_epoch: str
    date_raw: int
    played_character_id: int
    raw_scale: Literal[100000]
    traits: list[PilgrimageTraitRow]


class AvailablePlayerPilgrimageTraits(_PilgrimageTraitFields):
    available: Literal[True]
    unavailable_reason: None


class UnavailablePlayerPilgrimageTraits(_PilgrimageTraitFields):
    available: Literal[False]
    unavailable_reason: str


PlayerPilgrimageTraits: TypeAlias = AvailablePlayerPilgrimageTraits | UnavailablePlayerPilgrimageTraits


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("pilgrimage trait JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("pilgrimage trait JSON field must be a string")
        result[key] = item
    return result


def _integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("pilgrimage trait exact integer required in range")
    return value


def normalize_player_pilgrimage_traits_v1(
    value: object, *, current_context: Mapping[str, object],
) -> PlayerPilgrimageTraits | None:
    """Validate before constructing the shared model; retain explicit null."""
    if value is None:
        return None
    raw = _object(value)
    if set(raw) != {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
                    "date_raw", "played_character_id", "raw_scale", "traits"}:
        raise ValueError("pilgrimage trait fields differ from the contract")
    if (raw["schema"] != SCHEMA or raw["read_only"] is not True
            or current_context.get("schema") != "ck3_12004_religion_context_v1"
            or type(raw["raw_scale"]) is not int or raw["raw_scale"] != 100000):
        raise ValueError("pilgrimage trait schema/build/scale differs")
    available = raw["available"]
    if type(available) is not bool:
        raise ValueError("pilgrimage trait availability must be boolean")
    epoch = raw["capture_epoch"]
    if (not isinstance(epoch, str) or re.fullmatch(r"[1-9][0-9]{0,19}", epoch) is None
            or int(epoch) > 2**64 - 1
            or int(epoch) != _integer(current_context.get("capture_epoch"), 1, 2**64 - 1)):
        raise ValueError("pilgrimage trait owner epoch is not its canonical uint64 identity")
    date = _integer(raw["date_raw"], -(2**31), 2**31 - 1)
    actor = _integer(raw["played_character_id"], 1, 2**31 - 1)
    if (date != _integer(current_context.get("date_raw"), -(2**31), 2**31 - 1)
            or actor != _integer(current_context.get("played_character_id"), 1, 2**31 - 1)):
        raise ValueError("pilgrimage trait actor/date differ from their owner frame")
    reason = raw["unavailable_reason"]
    if available:
        if reason is not None or current_context.get("available") is not True:
            raise ValueError("available pilgrimage traits lack an available owner context")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("unavailable pilgrimage traits require an actual reason")
    rows = raw["traits"]
    if not isinstance(rows, list) or len(rows) != len(TRAIT_KEYS):
        raise ValueError("pilgrimage traits require exactly four ordered rows")
    parsed: list[PilgrimageTraitRow] = []
    for index, key in enumerate(TRAIT_KEYS):
        row = _object(rows[index])
        if set(row) != {"trait_key", "has_track", "present", "experience_raw"}:
            raise ValueError("pilgrimage trait row fields differ")
        has_track = index != 1
        if row["trait_key"] != key or row["has_track"] is not has_track:
            raise ValueError("pilgrimage trait definition/order/track identity differs")
        present = row["present"]
        xp = row["experience_raw"]
        if available:
            if type(present) is not bool:
                raise ValueError("available pilgrimage traits require observed presence")
            if present and has_track:
                xp = _integer(xp, 0, 100 * 100000)
            elif xp is not None:
                raise ValueError("absent or untracked pilgrimage traits have no XP")
        elif present is not None or xp is not None:
            raise ValueError("unavailable pilgrimage traits cannot retain partial observations")
        # All dynamic values have been checked; construct rather than cast.
        parsed.append({"trait_key": key, "has_track": has_track,
                       "present": present if isinstance(present, bool) else None,
                       "experience_raw": xp if type(xp) is int else None})
    fields: _PilgrimageTraitFields = {"schema": "ck3_12004_player_pilgrimage_traits_v1", "read_only": True,
        "capture_epoch": epoch, "date_raw": date, "played_character_id": actor,
        "raw_scale": 100000, "traits": parsed}
    if available:
        return {**fields, "available": True, "unavailable_reason": None}
    if not isinstance(reason, str):
        raise ValueError("unavailable pilgrimage trait reason required")
    return {**fields, "available": False, "unavailable_reason": reason}
