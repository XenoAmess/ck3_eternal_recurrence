"""Normalize observed current draft creation terms for exact mapped builds.

This nested component describes the current draft's UI comparison and native
command branch. Neither is final action legality or an executed action result.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity, private_native_schema
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build


COMPONENT_KEY = "current_draft_creation_terms"
READINESS_KEY = "current_draft_creation_terms_ready"
SCHEMA = "ck3_12003_current_draft_creation_terms_v1"
_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "source_rite_id",
    "source_faith_id", "source_main_rite_id", "actor_faith_id",
    "draft_divergence_raw", "faith_creation_threshold_raw",
    "divergence_results_in_faith_creation", "native_create_faith_or_reform", "raw_scale",
}
_REFERENCE_KEYS = (
    "source_rite_id", "source_faith_id", "source_main_rite_id", "actor_faith_id",
)
_RAW_KEYS = ("draft_divergence_raw", "faith_creation_threshold_raw")
_BOOL_KEYS = (
    "divergence_results_in_faith_creation", "native_create_faith_or_reform",
)


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native draft creation terms integer is malformed: {field}")


def normalize_current_draft_creation_terms12003(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve native zero, false, separate full IDs, and observed absence.

    The shared reform-context normalizer additionally checks this component's
    capture epoch against its composed owner. A semantic snapshot's native
    revision is not the owner's capture epoch.
    """
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native current draft creation terms schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native current draft creation terms belongs to another build")
    if type(value["available"]) is not bool:
        raise ValueError("native current draft creation terms availability is malformed")
    _integer(value["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], 0, 0xFFFFFFFF, "played_character_id")
    if type(value["raw_scale"]) is not int or value["raw_scale"] != 100000:
        raise ValueError("native current draft creation terms scale is malformed")
    for key in _REFERENCE_KEYS:
        if value[key] is not None:
            _integer(value[key], 0, 0xFFFFFFFF, key)
    for key in _RAW_KEYS:
        if value[key] is not None:
            _integer(value[key], -(1 << 63), (1 << 63) - 1, key)
    for key in _BOOL_KEYS:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native draft creation terms bool is malformed: {key}")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or type(actor.get("character_id")) is not int
                or actor["character_id"] != value["played_character_id"]
                or type(snapshot.get("date_raw")) is not int
                or snapshot["date_raw"] != value["date_raw"]
                or snapshot.get("paused") is not True
                or value["unavailable_reason"] is not None):
            raise ValueError("native current draft creation terms differs from its queried frame")
        if any(value[key] is None for key in _REFERENCE_KEYS + _RAW_KEYS + _BOOL_KEYS):
            raise ValueError("available native draft creation terms lost an actual value")
        # This is the UI thunk's signed >= comparison against the loaded define.
        # The native command branch uses actor Faith and remains independent.
        if value["divergence_results_in_faith_creation"] is not (
                value["draft_divergence_raw"] >= value["faith_creation_threshold_raw"]):
            raise ValueError("native draft creation terms lost its signed UI comparison")
    else:
        reason = value["unavailable_reason"]
        if not isinstance(reason, str) or not reason:
            raise ValueError("unavailable native draft creation terms lost its reason")
        if any(value[key] is not None for key in _REFERENCE_KEYS + _RAW_KEYS + _BOOL_KEYS):
            raise ValueError("unavailable native draft creation terms was filled")
    return deepcopy(value)
