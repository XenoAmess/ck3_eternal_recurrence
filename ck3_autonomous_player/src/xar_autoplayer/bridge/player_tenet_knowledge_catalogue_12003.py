"""Preserve the played actor's independent native Tenet knowledge inputs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity, private_native_schema
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build


SCHEMA = "ck3_12003_player_tenet_knowledge_catalogue_v1"
SIBLING_KEY = "player_tenet_knowledge_catalogue"
_SCOPE = "actual_played_character_extra_c8_and_prophet_inputs"
_FORMULA = "extra_c8_membership_or_prophet_perk"
_KEYS = {
    "schema", "game_version", "executable_sha256", "scope", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "has_character_extension", "extra_collection_source",
    "extra_collection_complete", "extra_tenet_keys", "loaded_registry_complete",
    "loaded_definition_count", "native_has_prophet", "knowledge_inputs_complete",
    "knowledge_formula", "rows",
}
_ROW_KEYS = {"source_index", "tenet_key", "native_extra_knowledge", "knowledge"}
_COMPLETE_FLAGS = (
    "extra_collection_complete", "loaded_registry_complete", "knowledge_inputs_complete",
)
_DEPENDENT_KEYS = (
    "has_character_extension", "extra_collection_source", "extra_tenet_keys",
    "loaded_definition_count", "native_has_prophet", "rows",
)
_UNAVAILABLE_REASONS = {
    "bindings_unavailable", "played_character_unavailable", "frame_not_paused",
    "tenet_database_unavailable", "tenet_definition_collection_unavailable",
    "tenet_definition_key_unavailable", "actor_extra_collection_unavailable",
    "extra_tenet_definition_key_unavailable", "prophet_definition_unavailable",
    "actor_perks_collection_unavailable", "state_changed",
    "knowledge_native_read_unavailable",
}


def _uint32(value: object) -> bool:
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def normalize_player_tenet_knowledge_catalogue_12003(
    value: object, *, snapshot: Mapping[str, object],
    tenet_rows: Mapping[str, object],
) -> dict[str, object]:
    """Bind the complete catalogue to its real owner, without deriving legality."""
    if (not isinstance(value, dict) or set(value) != _KEYS
            or value["schema"] != private_native_schema(SCHEMA, snapshot) or value["scope"] != _SCOPE
            or value["knowledge_formula"] != _FORMULA):
        raise ValueError("native player Tenet knowledge catalogue schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if (build not in (CK3_12003, CK3_12004)
            or require_exact_native_build(
                tenet_rows.get("game_version"), tenet_rows.get("executable_sha256"),
            ) != build or private_native_build_identity(snapshot) != build):
        raise ValueError("native player Tenet knowledge catalogue belongs to another build")
    if (type(value["available"]) is not bool
            or any(type(value[key]) is not bool or value[key] != value["available"]
                   for key in _COMPLETE_FLAGS)
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or not -0x80000000 <= value["date_raw"] <= 0x7FFFFFFF
            or not _uint32(value["played_character_id"])):
        raise ValueError("native player Tenet knowledge catalogue scalar fields are malformed")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or not _uint32(actor.get("character_id"))
            or type(snapshot.get("date_raw")) is not int
            or type(tenet_rows.get("capture_epoch")) is not int
            or type(tenet_rows.get("date_raw")) is not int
            or not _uint32(tenet_rows.get("played_character_id"))
            or value["played_character_id"] != actor["character_id"]
            or value["played_character_id"] != tenet_rows["played_character_id"]
            or value["date_raw"] != snapshot["date_raw"]
            or value["date_raw"] != tenet_rows["date_raw"]
            or value["capture_epoch"] != tenet_rows["capture_epoch"]):
        raise ValueError("native player Tenet knowledge catalogue differs from its queried frame")
    if value["available"]:
        if (value["unavailable_reason"] is not None
                or type(value["has_character_extension"]) is not bool
                or value["extra_collection_source"] != (
                    "character_extension_c8" if value["has_character_extension"]
                    else "native_default_collection")
                or type(value["extra_tenet_keys"]) is not list
                or any(type(key) is not str or not key for key in value["extra_tenet_keys"])
                or not _uint32(value["loaded_definition_count"])
                or type(value["native_has_prophet"]) is not bool
                or type(value["rows"]) is not list
                or len(value["rows"]) != value["loaded_definition_count"]):
            raise ValueError("native player Tenet knowledge catalogue observations are malformed")
        for index, row in enumerate(value["rows"]):
            if (not isinstance(row, dict) or set(row) != _ROW_KEYS
                    or not _uint32(row["source_index"]) or row["source_index"] != index
                    or type(row["tenet_key"]) is not str or not row["tenet_key"]
                    or type(row["native_extra_knowledge"]) is not bool
                    or type(row["knowledge"]) is not bool
                    or row["knowledge"] != (
                        row["native_extra_knowledge"] or value["native_has_prophet"])):
                raise ValueError("native player Tenet knowledge catalogue row is malformed")
    elif (type(value["unavailable_reason"]) is not str
            or value["unavailable_reason"] not in _UNAVAILABLE_REASONS
            or any(value[key] is not None for key in _DEPENDENT_KEYS)):
        raise ValueError("native player Tenet knowledge catalogue lost its typed unavailable observation")
    # Native pointer membership is retained; literal key membership is not a
    # substitute. Complete empty collections and false observations stay real.
    # The registry and extra collection each keep their order and duplicates.
    return deepcopy(value)
