"""Frozen native identities for the shared pilgrimage filming adapter."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

LegacyCase = Literal["faith-engine-e02-d1-ordinary-pilgrimage-v1"]
MechanismCase = Literal["faith-engine-e02-pilgrimage-mechanism-v2"]
OptionKey = Literal["pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"]
LEGACY_CASE: LegacyCase = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
MECHANISM_CASE: MechanismCase = "faith-engine-e02-pilgrimage-mechanism-v2"


@dataclass(frozen=True)
class PilgrimageIdentity:
    case: LegacyCase | MechanismCase
    actor_character_id: int
    date_raw: int
    faith_id: int
    rite_id: int | None
    option_key: OptionKey


def _integer(value: object, label: str, low: int = 0) -> int:
    if type(value) is not int or not low <= value < 2**32 - 1:
        raise ValueError(label + " must be a frozen exact integer identity")
    return value


def pilgrimage_identity(value: object) -> PilgrimageIdentity:
    if not isinstance(value, Mapping):
        raise ValueError("pilgrimage contract must be an object")
    actor = _integer(value.get("expected_actor_character_id"), "actor", 1)
    date = _integer(value.get("prior_scene_date_raw"), "date", 1)
    if value.get("case") == LEGACY_CASE:
        if value.get("schema") != "faith-engine-e02-d1-ordinary-pilgrimage-case-v1":
            raise ValueError("legacy D1 contract schema differs")
        if any(key in value for key in ("option_key", "expected_faith_id", "expected_rite_id")):
            raise ValueError("legacy D1 contract cannot acquire mechanism overrides")
        return PilgrimageIdentity(LEGACY_CASE, actor, date, 13, 0, "pilgrimage_type_pious")
    if value.get("case") != MECHANISM_CASE or value.get("schema") != "faith-engine-e02-pilgrimage-mechanism-case-v2":
        raise ValueError("unknown pilgrimage case/schema")
    if not {"option_key", "expected_faith_id", "expected_rite_id"} <= value.keys():
        raise ValueError("mechanism contract requires actual faith, nullable rite and option")
    faith = _integer(value["expected_faith_id"], "faith", 1)
    raw_rite = value["expected_rite_id"]
    rite = None if raw_rite is None else _integer(raw_rite, "rite")
    key = value["option_key"]
    if key == "pilgrimage_type_pious":
        option: OptionKey = "pilgrimage_type_pious"
    elif key == "pilgrimage_type_worldly":
        option = "pilgrimage_type_worldly"
    elif key == "pilgrimage_type_hajj":
        option = "pilgrimage_type_hajj"
    else:
        raise ValueError("unsupported original pilgrimage option identity")
    return PilgrimageIdentity(MECHANISM_CASE, actor, date, faith, rite, option)
