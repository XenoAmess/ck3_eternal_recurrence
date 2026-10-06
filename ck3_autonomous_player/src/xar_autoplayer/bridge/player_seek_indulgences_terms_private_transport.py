"""Read native ordinary indulgence visibility and final eligibility for one recipient."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-seek-indulgences-terms-v1"
DOMAIN_KEY = "player_seek_indulgences_terms_v1"
SCHEMA = "ck3_12003_player_seek_indulgences_terms_v1"
PERMISSION = "allow_private_player_religion_context_query"
DEFINITION_KEY = "seek_indulgences_interaction"
_ROLES = frozenset((
    "effective_actor_id", "effective_recipient_id", "secondary_actor_id",
    "secondary_recipient_id", "intermediary_id", "sixth_role_id",
))
_TOP_KEYS = frozenset((
    "schema", "game_version", "executable_sha256", "read_only", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "definition_key", "definition_stable_hash", "identity", "options", "shown", "can_send",
))


def _integer(value: object, *, minimum: int, maximum: int, field: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"native indulgence integer is malformed: {field}")
    return value


def _recipient(value: object) -> int:
    return _integer(value, minimum=0, maximum=0xFFFFFFFE, field="recipient_character_id")


def _group(value: Mapping[str, object], key: str, fields: frozenset[str]) -> dict[str, object]:
    group = value.get(key)
    if (not isinstance(group, dict) or set(group) != {"available", "reason"} | fields
            or type(group.get("available")) is not bool):
        raise ValueError(f"native indulgence sample group is malformed: {key}")
    reason = group["reason"]
    if (group["available"] and reason not in (None, "none")) or (
            not group["available"] and (type(reason) is not str or not reason or reason == "none")):
        raise ValueError(f"native indulgence sample reason is malformed: {key}")
    return group


def normalize_player_seek_indulgences_terms_v1(
    value: object, *, snapshot: Mapping[str, object], recipient_character_id: int,
) -> dict[str, object]:
    """Retain native false and typed sample failures without deriving an action gate."""
    requested = _recipient(recipient_character_id)
    if not isinstance(value, dict) or set(value) != _TOP_KEYS or value.get("schema") != SCHEMA:
        raise ValueError("native indulgence terms schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native indulgence terms belong to another build")
    actor = snapshot.get("played_character")
    actor_id = _recipient(value["played_character_id"])
    date_raw = _integer(value["date_raw"], minimum=-(2**31), maximum=2**31 - 1, field="date_raw")
    _integer(value["capture_epoch"], minimum=1, maximum=2**64 - 1, field="capture_epoch")
    if (not isinstance(actor, Mapping) or type(actor.get("character_id")) is not int
            or actor_id != actor["character_id"] or type(snapshot.get("date_raw")) is not int
            or date_raw != snapshot["date_raw"] or value["read_only"] is not True
            or type(value["available"]) is not bool):
        raise ValueError("native indulgence terms differ from the queried player frame")
    if value["definition_key"] != DEFINITION_KEY:
        raise ValueError("native indulgence terms contain another interaction")
    if value["definition_stable_hash"] is not None:
        _integer(value["definition_stable_hash"], minimum=0, maximum=2**32 - 1,
                 field="definition_stable_hash")
    elif value["available"]:
        raise ValueError("available native indulgence terms lack their definition hash")
    reason = value["unavailable_reason"]
    if (value["available"] and reason not in (None, "none")) or (
            not value["available"] and (type(reason) is not str or not reason or reason == "none")):
        raise ValueError("native indulgence terms lost their source availability reason")

    identity = _group(value, "identity", _ROLES | {"requested_recipient_character_id"})
    if _recipient(identity["requested_recipient_character_id"]) != requested:
        raise ValueError("native indulgence terms differ from the requested recipient")
    for role in _ROLES:
        scalar = identity[role]
        if scalar is not None:
            _integer(scalar, minimum=-(2**31), maximum=2**31 - 1, field=role)
        if identity["available"] and scalar is None:
            raise ValueError(f"native indulgence sampled identity role is null: {role}")
        if not identity["available"] and scalar is not None:
            raise ValueError(f"native indulgence unsampled identity role is not null: {role}")

    options = _group(value, "options", frozenset(("declared_count", "selected_count", "all_unselected")))
    for field in ("declared_count", "selected_count"):
        if options[field] is not None:
            _integer(options[field], minimum=0, maximum=2**32 - 1, field=field)
    if options["all_unselected"] is not None and type(options["all_unselected"]) is not bool:
        raise ValueError("native indulgence option-selection sample is malformed")
    if options["available"] and (options["declared_count"] is None
            or options["selected_count"] is None or options["all_unselected"] is None
            or options["selected_count"] > options["declared_count"]
            or options["all_unselected"] is not (options["selected_count"] == 0)):
        raise ValueError("native indulgence option readback is malformed")
    if not options["available"] and any(options[field] is not None for field in (
            "declared_count", "selected_count", "all_unselected")):
        raise ValueError("native indulgence unsampled option values are not null")
    for key in ("shown", "can_send"):
        group = _group(value, key, frozenset(("value",)))
        if (group["available"] and type(group["value"]) is not bool) or (
                not group["available"] and group["value"] is not None):
            raise ValueError(f"native indulgence boolean sample is malformed: {key}")
    complete = (all(value[key]["available"] for key in ("identity", "options", "shown", "can_send"))
                and options["all_unselected"] is True)
    if value["available"] and not complete:
        raise ValueError("available native indulgence terms have an unsampled group")
    return dict(value)


def query_player_seek_indulgences_terms_private_v1(
    driver: object, *, expected_revision: int, recipient_character_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    requested = _recipient(recipient_character_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision,
        request_fields={"recipient_character_id": requested}, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"), result.get("backend_id"),
            suffix="player-seek-indulgences-terms-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or type(result.get("snapshot_revision")) is not int
                or result["snapshot_revision"] != before["native_revision"]
                or type(result.get("date_raw")) is not int
                or result["date_raw"] != before.get("date_raw")):
            raise ValueError("native indulgence envelope differs from the queried build/frame")
        value = normalize_player_seek_indulgences_terms_v1(
            result.get("player_seek_indulgences_terms"), snapshot=before,
            recipient_character_id=requested,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native indulgence envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
