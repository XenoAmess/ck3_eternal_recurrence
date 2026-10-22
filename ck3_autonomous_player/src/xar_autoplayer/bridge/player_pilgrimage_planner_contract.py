"""Finite option identity and JSON state shared by pilgrimage producers/consumers."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypedDict

PilgrimageOptionKey = Literal[
    "pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"
]


class PilgrimagePlannerState(TypedDict):
    stage: int
    selected_option_key: PilgrimageOptionKey | None
    destination_province_id: int | None
    can_select: bool | None
    can_progress: bool | None


@dataclass(frozen=True)
class PilgrimageSourceIdentity:
    native_revision: int
    date_raw: int
    actor_character_id: int


def pilgrimage_source_identity(value: object) -> PilgrimageSourceIdentity:
    if not isinstance(value, Mapping) or not isinstance(value.get("played_character"), Mapping):
        raise ValueError("pilgrimage source requires a native character object")
    revision, date, actor = value.get("native_revision"), value.get("date_raw"), value["played_character"].get("character_id")
    if type(revision) is not int or not 0 < revision < 2**64:
        raise ValueError("pilgrimage source revision must be an exact positive integer")
    if type(date) is not int or not -(2**31) <= date < 2**31:
        raise ValueError("pilgrimage source date must be an exact signed integer")
    if type(actor) is not int or not 0 < actor < 2**32 - 1:
        raise ValueError("pilgrimage source actor must be an exact character identity")
    return PilgrimageSourceIdentity(revision, date, actor)


def parse_pilgrimage_option_key(value: object) -> PilgrimageOptionKey:
    if value == "pilgrimage_type_pious" and type(value) is str:
        return "pilgrimage_type_pious"
    if value == "pilgrimage_type_worldly" and type(value) is str:
        return "pilgrimage_type_worldly"
    if value == "pilgrimage_type_hajj" and type(value) is str:
        return "pilgrimage_type_hajj"
    raise ValueError("pilgrimage option_key must be a supported original option identity")


def parse_pilgrimage_planner_state(value: object) -> PilgrimagePlannerState | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "stage", "selected_option_key", "destination_province_id", "can_select", "can_progress"
    }:
        raise ValueError("pilgrimage planner semantic fields differ")
    stage = value["stage"]
    if type(stage) is not int or not 0 <= stage <= 5:
        raise ValueError("pilgrimage planner stage must be an exact 0..5 integer")
    raw_key = value["selected_option_key"]
    key = None if raw_key is None else parse_pilgrimage_option_key(raw_key)
    province = value["destination_province_id"]
    if province is not None and (type(province) is not int or not 0 <= province < 2**32 - 1):
        raise ValueError("pilgrimage destination must be null or a complete integer identity")
    can_select, can_progress = value["can_select"], value["can_progress"]
    if can_select is not None and type(can_select) is not bool:
        raise ValueError("pilgrimage can_select must be nullable boolean")
    if can_progress is not None and type(can_progress) is not bool:
        raise ValueError("pilgrimage can_progress must be nullable boolean")
    return {"stage": stage, "selected_option_key": key, "destination_province_id": province,
            "can_select": can_select, "can_progress": can_progress}
