"""Independent nullable remaining stock berserker inputs in a V2 knight row."""
from __future__ import annotations

from typing import TypedDict

PHASE_BERSERKER_VALIDITY_INPUTS_LEAF = "phase_berserker_validity_inputs_v1"
BERSERKER_EXCLUSION_TRAIT_KEYS = ("craven", "berserker", "calm")


class PhaseBerserkerValidityInputsV1(TypedDict):
    source_character_id: int
    culture: dict[str, object]
    religion: dict[str, object]
    traits: dict[str, dict[str, object]]


def _object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native berserker {name} schema is malformed")
    return value


def _ref(value: object, name: str, *, nullable: bool = False, resolved: bool = False) -> int | None:
    if nullable and value is None:
        return None
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF or (resolved and value == 0xFFFFFFFF):
        raise ValueError(f"native berserker {name} must preserve its uint32 reference")
    return value


def _state(row: dict[str, object], value: object, name: str) -> None:
    if row["status"] == "available":
        if type(value) is not bool or row["unavailable_reason"] is not None:
            raise ValueError(f"native available berserker {name} requires boolean and no reason")
    elif row["status"] == "unavailable":
        if value is not None or not isinstance(row["unavailable_reason"], str) or not row["unavailable_reason"]:
            raise ValueError(f"native unavailable berserker {name} requires null and reason")
    else:
        raise ValueError(f"native berserker {name} status is malformed")


def _resolution(row: dict[str, object], name: str) -> str:
    value = row["resolution"]
    if value not in ("resolved", "native_fallback", "unresolved"):
        raise ValueError(f"native berserker {name} resolution is malformed")
    return value


def normalize_phase_berserker_validity_inputs_v1(
    value: object, *, expected_character_id: int,
) -> PhaseBerserkerValidityInputsV1 | None:
    if value is None:
        return None
    row = _object(value, {"source_character_id", "culture", "religion", "traits"}, "leaf")
    source = _ref(row["source_character_id"], "source_character_id", resolved=True)
    if source != expected_character_id:
        raise ValueError("native berserker source CharacterID mismatch")
    culture = _object(row["culture"], {
        "status", "raw_culture_id", "culture_id", "resolution", "selected_pillar_keys",
        "heritage_north_germanic", "unavailable_reason",
    }, "culture").copy()
    raw = _ref(culture["raw_culture_id"], "raw_culture_id")
    resolved = _ref(culture["culture_id"], "culture_id", nullable=True, resolved=True)
    resolution = _resolution(culture, "culture")
    if (resolution == "resolved") != (resolved is not None) or (resolved is not None and resolved != raw):
        raise ValueError("native berserker Culture resolution differs from its actual source")
    _state(culture, culture["heritage_north_germanic"], "culture")
    keys = culture["selected_pillar_keys"]
    if culture["status"] == "available":
        if resolution != "resolved" or not isinstance(keys, list) or len(keys) != 5 or any(
            not isinstance(key, str) or len(key.encode("utf-8")) > 4096 for key in keys
        ):
            raise ValueError("native available berserker Culture requires five actual selected pillar keys")
        if culture["heritage_north_germanic"] is not ("heritage_north_germanic" in keys):
            raise ValueError("native berserker heritage differs from actual selected keys")
        culture["selected_pillar_keys"] = keys.copy()
    elif keys is not None:
        raise ValueError("native unavailable berserker Culture cannot publish a complete key set")
    religion = _object(row["religion"], {
        "status", "raw_adopted_rite_id", "rite_id", "raw_faith_id", "faith_id",
        "raw_religion_id", "religion_id", "resolution", "religion_key", "germanic", "unavailable_reason",
    }, "religion").copy()
    for raw_key, resolved_key in (("raw_adopted_rite_id", "rite_id"), ("raw_faith_id", "faith_id"),
                                  ("raw_religion_id", "religion_id")):
        raw_ref = _ref(religion[raw_key], raw_key, nullable=raw_key != "raw_adopted_rite_id")
        resolved_ref = _ref(religion[resolved_key], resolved_key, nullable=True, resolved=True)
        if resolved_ref is not None and resolved_ref != raw_ref:
            raise ValueError("native berserker Religion chain differs from its raw source reference")
    resolution = _resolution(religion, "religion")
    if (resolution == "resolved") != (religion["religion_id"] is not None):
        raise ValueError("native berserker Religion resolution differs from its identity")
    if religion["faith_id"] is not None and religion["rite_id"] is None:
        raise ValueError("native berserker source Faith requires its actual Rite")
    if religion["religion_id"] is not None and religion["faith_id"] is None:
        raise ValueError("native berserker source Religion requires its actual Faith")
    _state(religion, religion["germanic"], "religion")
    key = religion["religion_key"]
    if religion["status"] == "available":
        if resolution != "resolved" or not isinstance(key, str) or len(key.encode("utf-8")) > 4096:
            raise ValueError("native available berserker Religion requires its actual definition key")
        if religion["germanic"] is not (key == "germanic_religion"):
            raise ValueError("native berserker germanic differs from its actual Religion key")
    elif key is not None:
        raise ValueError("native unavailable berserker Religion cannot invent a definition key")
    traits = _object(row["traits"], set(BERSERKER_EXCLUSION_TRAIT_KEYS), "traits")
    normalized_traits = {}
    for key in BERSERKER_EXCLUSION_TRAIT_KEYS:
        trait = _object(traits[key], {"status", "value", "unavailable_reason"}, f"traits.{key}")
        _state(trait, trait["value"], f"traits.{key}")
        normalized_traits[key] = trait.copy()
    return {"source_character_id": source, "culture": culture, "religion": religion, "traits": normalized_traits}
