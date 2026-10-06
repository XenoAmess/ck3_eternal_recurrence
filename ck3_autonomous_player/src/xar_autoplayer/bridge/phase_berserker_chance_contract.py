"""Independent source-root chance operands in an optional V2 knight leaf."""
from __future__ import annotations

from .phase_berserker_validity_contract import _object, _ref, _state

PHASE_BERSERKER_CHANCE_INPUTS_LEAF = "phase_berserker_chance_inputs_v1"
DIRECT_CHANCE_TRAIT_KEYS = ("wrathful", "giant", "impatient", "sadistic", "brave", "ambitious",
                            "content", "compassionate", "temperate", "lazy", "patient")
WOUND_TRAIT_KEYS = ("wounded_1", "wounded_2", "wounded_3")
MAIM_TRAIT_KEYS = ("one_legged", "disfigured", "one_eyed", "maimed")
CHANCE_TRAIT_KEYS = DIRECT_CHANCE_TRAIT_KEYS + WOUND_TRAIT_KEYS + MAIM_TRAIT_KEYS


def _bool_value(value: object, name: str) -> dict[str, object]:
    row = _object(value, {"status", "value", "unavailable_reason"}, name)
    _state(row, row["value"], name)
    return row.copy()


def _perk(value: object, key: str) -> dict[str, object]:
    row = _object(value, {"definition_key", "presence"}, key)
    if row["definition_key"] not in (None, key):
        raise ValueError(f"native berserker chance {key} definition key differs")
    presence = _bool_value(row["presence"], key)
    if presence["status"] == "available" and row["definition_key"] is None:
        raise ValueError(f"native available berserker chance {key} requires its actual definition")
    return {"definition_key": row["definition_key"], "presence": presence}


def _resolution(value, raw, resolved, name):
    if value not in ("unresolved", "resolved", "absent", "native_fallback"):
        raise ValueError(f"native berserker chance {name} resolution differs")
    if (value == "resolved") != (resolved is not None) or (resolved is not None and resolved != raw):
        raise ValueError(f"native berserker chance {name} full identity differs")
    if value == "absent" and raw not in (None, 0xFFFFFFFF):
        raise ValueError(f"native berserker chance {name} absence differs")


def normalize_phase_berserker_chance_inputs_v1(value: object, *, expected_character_id: int):
    if value is None:
        return None
    row = _object(value, {"source_character_id", "is_ai", "stalwart", "dynasty", "acclaimed", "traits"}, "chance leaf")
    source = _ref(row["source_character_id"], "source_character_id", resolved=True)
    if source != expected_character_id:
        raise ValueError("native berserker chance source CharacterID mismatch")
    identity = _bool_value(row["is_ai"], "is_ai")
    stalwart = _perk(row["stalwart"], "stalwart_leader_perk")
    dynasty = _object(row["dynasty"], {"raw_house_id", "house_id", "raw_dynasty_id", "dynasty_id",
                      "house_resolution", "dynasty_resolution", "warfare_legacy_3"}, "dynasty").copy()
    for raw_key, resolved_key in (("raw_house_id", "house_id"), ("raw_dynasty_id", "dynasty_id")):
        raw = _ref(dynasty[raw_key], raw_key, nullable=raw_key != "raw_house_id")
        resolved = _ref(dynasty[resolved_key], resolved_key, nullable=True, resolved=True)
        _resolution(dynasty[resolved_key.replace("_id", "_resolution")], raw, resolved, resolved_key)
    if dynasty["dynasty_id"] is not None and dynasty["house_id"] is None:
        raise ValueError("native berserker chance Dynasty requires its source House")
    dynasty["warfare_legacy_3"] = _perk(dynasty["warfare_legacy_3"], "warfare_legacy_3")
    warfare = dynasty["warfare_legacy_3"]["presence"]["value"]
    if warfare is not None and dynasty["dynasty_resolution"] not in ("resolved", "absent"):
        raise ValueError("native berserker chance warfare presence requires resolved/absent Dynasty")
    if warfare is True and dynasty["dynasty_resolution"] != "resolved":
        raise ValueError("native berserker chance warfare cannot be owned by an absent Dynasty")
    acclaimed = _object(row["acclaimed"], {"raw_accolade_id", "accolade_id", "resolution", "is_acclaimed"}, "acclaimed").copy()
    raw = _ref(acclaimed["raw_accolade_id"], "raw_accolade_id", nullable=True)
    resolved = _ref(acclaimed["accolade_id"], "accolade_id", nullable=True, resolved=True)
    _resolution(acclaimed["resolution"], raw, resolved, "accolade")
    acclaimed["is_acclaimed"] = _bool_value(acclaimed["is_acclaimed"], "is_acclaimed")
    observed = acclaimed["is_acclaimed"]["value"]
    if observed is not None and acclaimed["resolution"] != ("resolved" if observed else "absent"):
        raise ValueError("native berserker chance acclaimed predicate differs from actual identity")
    traits = _object(row["traits"], set(CHANCE_TRAIT_KEYS), "chance traits")
    return {"source_character_id": source, "is_ai": identity, "stalwart": stalwart,
            "dynasty": dynasty, "acclaimed": acclaimed,
            "traits": {key: _bool_value(traits[key], f"traits.{key}") for key in CHANCE_TRAIT_KEYS}}
