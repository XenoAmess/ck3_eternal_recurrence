"""Read the played character's native doctrine knowledge; no selection action."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import (
    private_native_schema,
    private_native_build_identity, private_native_provenance,
)
from .version_identity import (
    CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build,
)


STEP = "query-player-religion-doctrine-knowledge-v1"
DOMAIN_KEY = "player_religion_doctrine_knowledge_v1"
SCHEMA = "ck3_12002_played_doctrine_knowledge_v1"
LOOKUP_SCHEMA = "ck3_12002_played_doctrine_knowledge_lookup_v1"
PERMISSION = "allow_private_player_religion_doctrine_knowledge_query"
_COMMON_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
}
_LEARNED_KEYS = _COMMON_KEYS | {"rite_id", "knowledge_source", "learned_rows"}
_LOOKUP_KEYS = _COMMON_KEYS | {
    "requested_doctrine_key", "definition_found", "definition", "native_knows_doctrine",
}
_DEFINITION_KEYS = {"doctrine_key", "group_key", "source"}
_KNOWLEDGE_SOURCES = {"character_extension", "rite_default"}


def _definition(value: object, *, source: str, learned: bool = False) -> None:
    fields = _DEFINITION_KEYS | {"native_knows_doctrine"} if learned else _DEFINITION_KEYS
    if (not isinstance(value, Mapping) or set(value) != fields
            or not isinstance(value.get("doctrine_key"), str)
            or not isinstance(value.get("group_key"), str) or value.get("source") != source
            or (learned and type(value.get("native_knows_doctrine")) is not bool)):
        raise ValueError("native doctrine knowledge definition is malformed")


def normalize_player_religion_doctrine_knowledge_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve learned rows and the native true/false/null lookup distinction."""
    if not isinstance(value, dict):
        raise ValueError("native player doctrine knowledge schema is malformed")
    schema = value.get("schema")
    if (schema not in (private_native_schema(SCHEMA, snapshot), private_native_schema(LOOKUP_SCHEMA, snapshot))
            or set(value) != (_LEARNED_KEYS if schema == private_native_schema(SCHEMA, snapshot) else _LOOKUP_KEYS)):
        raise ValueError("native player doctrine knowledge schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player doctrine knowledge belongs to another build")
    if (type(value["available"]) is not bool or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int or type(value["played_character_id"]) is not int):
        raise ValueError("native player doctrine knowledge scalar fields are malformed")
    reason = value["unavailable_reason"]
    if ((value["available"] and reason is not None)
            or (not value["available"] and (not isinstance(reason, str) or not reason))):
        raise ValueError("native player doctrine knowledge lost its availability reason")
    if schema == private_native_schema(SCHEMA, snapshot):
        rite = value["rite_id"]
        if rite is not None and (type(rite) is not int or not 0 <= rite <= 0xFFFFFFFF):
            raise ValueError("native doctrine knowledge full Rite reference is malformed")
        source = value["knowledge_source"]
        if ((value["available"] and source not in _KNOWLEDGE_SOURCES)
                or (not value["available"] and source is not None)
                or not isinstance(value["learned_rows"], list)):
            raise ValueError("native doctrine knowledge learned scope is malformed")
        for row in value["learned_rows"]:
            _definition(row, source=source, learned=True)
    else:
        key = value["requested_doctrine_key"]
        known = value["native_knows_doctrine"]
        found = value["definition_found"]
        if (not isinstance(key, str) or not key or type(found) is not bool
                or (known is not None and type(known) is not bool)):
            raise ValueError("native doctrine knowledge lookup is malformed")
        if found:
            _definition(value["definition"], source="definition_registry")
            if known is None or value["definition"]["doctrine_key"] != key:
                raise ValueError("native doctrine knowledge lookup lost its native result")
        elif value["definition"] is not None or known is not None:
            raise ValueError("native absent doctrine definition lost its null result")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")):
            raise ValueError("native doctrine knowledge differs from the queried player frame")
    # capture_epoch is the actual owner pump epoch, not snapshot_revision.
    return deepcopy(value)


def query_player_religion_doctrine_knowledge_private_v1(
    driver: object, *, expected_revision: int, doctrine_key: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if doctrine_key is not None and (not isinstance(doctrine_key, str) or not doctrine_key):
        raise ValueError("doctrine_key must be a nonempty string when provided")
    mode = "learned_rows" if doctrine_key is None else "by_key"
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields=None if doctrine_key is None else {"doctrine_key": doctrine_key},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-doctrine-knowledge-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")
                or result.get("query_mode") != mode):
            raise ValueError("native doctrine knowledge envelope differs from the queried build/frame/mode")
        value = normalize_player_religion_doctrine_knowledge_v1(
            result.get("player_religion_doctrine_knowledge"), snapshot=before,
        )
        if (value["schema"] != private_native_schema(
                SCHEMA if mode == "learned_rows" else LOOKUP_SCHEMA, before,
            )
                or (mode == "by_key" and value["requested_doctrine_key"] != doctrine_key)):
            raise ValueError("native doctrine knowledge differs from the requested lookup")
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native doctrine knowledge envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"], "query_mode": mode,
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
