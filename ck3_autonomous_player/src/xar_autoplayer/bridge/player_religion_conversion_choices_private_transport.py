"""Read native Faith choices and the current Faith's Rite membership."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-conversion-choices-v1"
DOMAIN_KEY = "player_religion_conversion_choices_v1"
SCHEMA = "ck3_12002_religion_conversion_choices_v1"
PERMISSION = "allow_private_player_religion_conversion_choices_query"
_COMMON = {"schema", "game_version", "executable_sha256", "available",
           "unavailable_reason", "capture_epoch", "date_raw", "played_character_id"}
_TOP = _COMMON | {"read_only", "faith_choices", "current_faith_rites", "membership_is_legality"}
_FAITH = _COMMON | {"current_faith_id", "candidate_source", "rule_only", "choices"}
_RITES = _COMMON | {"read_only", "faith_id", "rite_ids", "membership_is_legality"}


def _reference(value: object, *, nullable: bool = False) -> bool:
    return ((nullable and value is None)
            or type(value) is int and 0 <= value <= 0xFFFFFFFF)


def _source(value: object, schema: str, keys: set[str], snapshot: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or value["schema"] != private_native_schema(schema, snapshot):
        raise ValueError("native conversion choices schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native conversion choices belong to another connected build")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int or type(value["played_character_id"]) is not int
            or value["available"] and value["unavailable_reason"] is not None
            or not value["available"] and (not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"])):
        raise ValueError("native conversion choices source status is malformed")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping) or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")):
            raise ValueError("native conversion choices differ from their queried player frame")
    return value


def normalize_player_religion_conversion_choices_v1(value: object, *, snapshot: Mapping[str, object]) -> dict[str, object]:
    top = _source(value, private_native_schema(SCHEMA, snapshot), _TOP, snapshot)
    faith = _source(top["faith_choices"], private_native_schema("ck3_12002_faith_conversion_choices_v1", snapshot), _FAITH, snapshot)
    rites = _source(top["current_faith_rites"], private_native_schema("ck3_12002_current_faith_rites_v1", snapshot), _RITES, snapshot)
    if (top["read_only"] is not True or top["membership_is_legality"] is not False
            or rites["read_only"] is not True or rites["membership_is_legality"] is not False
            or faith["rule_only"] is not True or faith["candidate_source"] != "native_world_faith_registry"
            or not _reference(faith["current_faith_id"], nullable=True)
            or not _reference(rites["faith_id"])
            or not isinstance(faith["choices"], list) or not isinstance(rites["rite_ids"], list)
            or any(not _reference(reference) for reference in rites["rite_ids"])):
        raise ValueError("native conversion choices membership fields are malformed")
    for row in faith["choices"]:
        if (not isinstance(row, dict) or set(row) != {"faith_id", "faith_key", "main_rite_id", "native_faith_rule_passes"}
                or not _reference(row["faith_id"]) or not isinstance(row["faith_key"], str)
                or not _reference(row["main_rite_id"], nullable=True)
                or type(row["native_faith_rule_passes"]) is not bool):
            raise ValueError("native Faith choice row is malformed")
    for child in (faith, rites):
        if child["available"] and any(child[key] != top[key] for key in (
                "capture_epoch", "date_raw", "played_character_id")):
            raise ValueError("native conversion choices components crossed their owner frame")
    if top["available"] and (not faith["available"] or not rites["available"]):
        raise ValueError("available native conversion choices lack a source component")
    return deepcopy(top)


def query_player_religion_conversion_choices_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(result.get("game_version"), result.get("executable_sha256"),
                                           result.get("backend_id"), suffix="player-religion-conversion-choices-v1")
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native conversion choices envelope differs from its queried build/frame")
        choices = normalize_player_religion_conversion_choices_v1(result.get("player_religion_conversion_choices"), snapshot=before)
        if result.get("status") != ("observed" if choices["available"] else "unavailable"):
            raise ValueError("native conversion choices envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**choices, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
            "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
            "status": result["status"], "advertised": False}
