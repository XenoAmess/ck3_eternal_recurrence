"""Read native conversion blocker text without interpreting localized reasons."""

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
from .player_religion_conversion_terms_private_transport import (
    _build, _common, _full_rite_id, _integer,
)
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend


STEP = "query-player-religion-conversion-reasons-v1"
DOMAIN_KEY = "player_religion_conversion_reasons_v1"
SCHEMA = "ck3_12002_religion_conversion_reasons_v1"
PERMISSION = "allow_private_player_religion_conversion_reasons_query"
_REASONS_KEYS = {
    "schema", "game_version", "executable_sha256", "read_only", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "current_rite_id", "target_rite_id", "native_paid_validator_passes",
    "native_blocker_text_available", "raw_native_text", "ui_blocker_text",
    "reason_codes_available",
}


def normalize_player_religion_conversion_reasons_v1(
    value: object, *, snapshot: Mapping[str, object], target_rite_id: object,
) -> dict[str, object]:
    """Keep native verdict/text, including legitimate empty text and null reads."""
    target = _full_rite_id(target_rite_id)
    reasons = _common(value, private_native_schema(SCHEMA, snapshot), _REASONS_KEYS)
    _build(reasons, snapshot)
    if (reasons["capture_epoch"] == 0 or reasons["target_rite_id"] != target
            or not _integer(reasons["current_rite_id"], 0, 0xFFFFFFFF)
            or reasons["reason_codes_available"] is not False
            or type(reasons["native_blocker_text_available"]) is not bool
            or (reasons["native_paid_validator_passes"] is not None
                and type(reasons["native_paid_validator_passes"]) is not bool)
            or any(reasons[key] is not None and not isinstance(reasons[key], str)
                   for key in ("raw_native_text", "ui_blocker_text"))):
        raise ValueError("native conversion reasons target or fields are malformed")
    if reasons["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or reasons["played_character_id"] != actor.get("character_id")
                or reasons["date_raw"] != snapshot.get("date_raw")
                or type(reasons["native_paid_validator_passes"]) is not bool
                or reasons["native_blocker_text_available"] is not True
                or any(reasons[key] is None for key in ("raw_native_text", "ui_blocker_text"))):
            raise ValueError("available native conversion reasons lack their player frame or text")
    elif (reasons["native_paid_validator_passes"] is not None
            or reasons["native_blocker_text_available"] is not False
            or any(reasons[key] is not None for key in ("raw_native_text", "ui_blocker_text"))):
        raise ValueError("unavailable native conversion reasons invented a verdict or text")
    return deepcopy(reasons)


def query_player_religion_conversion_reasons_private_v1(
    driver: object, *, expected_revision: int, target_rite_id: object,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    target = _full_rite_id(target_rite_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, request_fields={"target_rite_id": target},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-conversion-reasons-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native conversion reasons envelope differs from its build/frame")
        reasons = normalize_player_religion_conversion_reasons_v1(
            result.get("player_religion_conversion_reasons"), snapshot=before,
            target_rite_id=target,
        )
        if result.get("status") != ("observed" if reasons["available"] else "unavailable"):
            raise ValueError("native conversion reasons envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **reasons, **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "advertised": False,
    }
