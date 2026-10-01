"""Read current Rite and Faith-main-Rite doctrines and boolean parameters."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import (
    private_native_build_identity, private_native_provenance,
)
from .version_identity import (
    CK3_12002, require_exact_native_backend, require_exact_native_build,
)


STEP = "query-player-religion-doctrines-v1"
DOMAIN_KEY = "player_religion_doctrines_v1"
SCHEMA = "ck3_12002_current_doctrines_v1"
PERMISSION = "allow_private_player_religion_doctrines_query"
_COMMON_KEYS = {
    "schema", "available", "unavailable_reason", "capture_epoch", "date_raw",
    "played_character_id",
}
_BUILD_KEYS = {"game_version", "executable_sha256"}


def _full_reference(value: object) -> bool:
    return value is None or (type(value) is int and 0 <= value <= 0xFFFFFFFF)


def _availability(value: Mapping[str, object], *, allow_zero_epoch: bool) -> None:
    epoch = value.get("capture_epoch")
    if (type(value.get("available")) is not bool or type(epoch) is not int
            or not (0 if allow_zero_epoch else 1) <= epoch <= 0xFFFFFFFFFFFFFFFF
            or type(value.get("date_raw")) is not int
            or type(value.get("played_character_id")) is not int):
        raise ValueError("native player religion doctrines scalar fields are malformed")
    reason = value.get("unavailable_reason")
    if ((value["available"] and reason is not None)
            or (not value["available"] and (not isinstance(reason, str) or not reason))):
        raise ValueError("native player religion doctrines lost its availability reason")


def _doctrine_rows(value: object, *, main_rite: bool) -> Mapping[str, object]:
    fields = _COMMON_KEYS | {"rite_id", "faith_id", "rows"}
    schema = "ck3_12002_player_rite_doctrines_v1"
    source = "rite_effective"
    if main_rite:
        fields = fields | {"main_rite_id"}
        schema = "ck3_12002_faith_main_rite_doctrines_v1"
        source = "faith_main_rite"
    if not isinstance(value, Mapping) or set(value) != fields or value.get("schema") != schema:
        raise ValueError("native player religion doctrine scope is malformed")
    _availability(value, allow_zero_epoch=True)
    for key in ("rite_id", "faith_id", "main_rite_id") if main_rite else ("rite_id", "faith_id"):
        if not _full_reference(value.get(key)):
            raise ValueError("native player religion doctrine full reference is malformed")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise ValueError("native player religion doctrine rows are malformed")
    for row in rows:
        if (not isinstance(row, Mapping) or set(row) != {"doctrine_key", "group_key", "source"}
                or not isinstance(row.get("doctrine_key"), str)
                or not isinstance(row.get("group_key"), str) or row.get("source") != source):
            raise ValueError("native player religion doctrine row lost its scope")
    return value


def _parameter_scope(value: object) -> None:
    if value is None:
        return
    if (not isinstance(value, Mapping)
            or set(value) != {"rite_id", "boolean_parameters_complete", "parameters"}
            or not _full_reference(value.get("rite_id"))
            or type(value.get("boolean_parameters_complete")) is not bool
            or not isinstance(value.get("parameters"), list)):
        raise ValueError("native player religion boolean-parameter scope is malformed")
    for parameter in value["parameters"]:
        if (not isinstance(parameter, Mapping) or set(parameter) != {"key", "value"}
                or not isinstance(parameter.get("key"), str) or parameter.get("value") is not True):
            raise ValueError("native player religion boolean-parameter entry is malformed")


def normalize_player_religion_doctrines_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep the producer's two scopes, complete empty bags and typed failures."""
    fields = _COMMON_KEYS | _BUILD_KEYS | {"current_rite", "faith_main_rite", "boolean_parameters"}
    if not isinstance(value, dict) or set(value) != fields or value.get("schema") != SCHEMA:
        raise ValueError("native player religion doctrines schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12002 or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion doctrines belongs to another build")
    _availability(value, allow_zero_epoch=False)
    current = _doctrine_rows(value["current_rite"], main_rite=False)
    main = _doctrine_rows(value["faith_main_rite"], main_rite=True)
    parameters = value["boolean_parameters"]
    parameter_fields = _COMMON_KEYS | _BUILD_KEYS | {"faith_id", "current_rite", "faith_main_rite"}
    if (not isinstance(parameters, Mapping) or set(parameters) != parameter_fields
            or parameters.get("schema") != "ck3_12002_rite_boolean_parameters_v1"
            or require_exact_native_build(parameters.get("game_version"),
                                          parameters.get("executable_sha256")) != build
            or not _full_reference(parameters.get("faith_id"))):
        raise ValueError("native player religion boolean parameters are malformed")
    _availability(parameters, allow_zero_epoch=True)
    _parameter_scope(parameters["current_rite"])
    _parameter_scope(parameters["faith_main_rite"])
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or any(scope["available"] is not True for scope in (current, main, parameters))
                or any(scope[key] != value[key] for scope in (current, main, parameters)
                       for key in ("capture_epoch", "date_raw", "played_character_id"))
                or current["rite_id"] != main["rite_id"]
                or not current["faith_id"] == main["faith_id"] == parameters["faith_id"]):
            raise ValueError("native player religion doctrine scopes differ from the queried frame")
        parameter_current = parameters["current_rite"]
        parameter_main = parameters["faith_main_rite"]
        if (not isinstance(parameter_current, Mapping) or not isinstance(parameter_main, Mapping)
                or parameter_current["rite_id"] != current["rite_id"]
                or parameter_main["rite_id"] != main["main_rite_id"]
                or parameter_current["boolean_parameters_complete"] is not True
                or parameter_main["boolean_parameters_complete"] is not True):
            raise ValueError("native player religion doctrine parameter scopes are incomplete")
    # A failed aggregate retains the provider's reset child values and reason.
    # Its capture epoch remains the owner-pump identity, never snapshot revision.
    return deepcopy(value)


def query_player_religion_doctrines_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-doctrines-v1",
        )
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion doctrines envelope differs from the queried build/frame")
        value = normalize_player_religion_doctrines_v1(
            result.get("player_religion_doctrines"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native player religion doctrines envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
