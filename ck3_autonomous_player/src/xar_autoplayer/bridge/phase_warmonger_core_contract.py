"""Optional same-combat-query adopted Core Tenet predicate for a knight row."""
from __future__ import annotations

from typing import Literal, TypedDict

PHASE_WARMONGER_CORE_LEAF = "phase_warmonger_core_v1"


class PhaseWarmongerCoreV1(TypedDict):
    status: Literal["available", "unavailable"]
    source_character_id: int
    raw_adopted_rite_id: int
    rite_id: int | None
    rite_resolution: Literal["unresolved", "adopted", "native_fallback"]
    requested_tenet_key: Literal["tenet_warmonger"]
    target_tenet_key: str | None
    warmonger_core_membership: bool | None
    unavailable_reason: str | None


def _uint32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"native phase warmonger {name} must be uint32")
    return value


def normalize_phase_warmonger_core_v1(
    value: object, *, expected_character_id: int
) -> PhaseWarmongerCoreV1 | None:
    if value is None:
        return None
    keys = {
        "status", "source_character_id", "raw_adopted_rite_id", "rite_id", "rite_resolution",
        "requested_tenet_key", "target_tenet_key", "warmonger_core_membership", "unavailable_reason",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("native phase warmonger leaf schema is malformed")
    source = _uint32(value["source_character_id"], "source_character_id")
    if source == 0xFFFFFFFF or source != _uint32(expected_character_id, "expected_character_id"):
        raise ValueError("native phase warmonger source CharacterID mismatch")
    raw = _uint32(value["raw_adopted_rite_id"], "raw_adopted_rite_id")
    rite = value["rite_id"]
    if rite is not None:
        rite = _uint32(rite, "rite_id")
        if rite == 0xFFFFFFFF or rite != raw:
            raise ValueError("native phase warmonger resolved adopted reference is inconsistent")
    resolution = value["rite_resolution"]
    if resolution not in ("unresolved", "adopted", "native_fallback"):
        raise ValueError("native phase warmonger Rite resolution is malformed")
    if (resolution == "adopted") != (rite is not None):
        raise ValueError("native phase warmonger Rite resolution differs from its identity")
    if value["requested_tenet_key"] != "tenet_warmonger":
        raise ValueError("native phase warmonger requested Tenet key differs")
    target = value["target_tenet_key"]
    if target not in (None, "tenet_warmonger"):
        raise ValueError("native phase warmonger resolved Tenet key differs")
    membership = value["warmonger_core_membership"]
    if membership is not None and not isinstance(membership, bool):
        raise ValueError("native phase warmonger membership must be boolean or null")
    status = value["status"]
    reason = value["unavailable_reason"]
    if status == "available":
        if resolution != "adopted" or target is None or membership is None or reason is not None:
            raise ValueError("native available phase warmonger predicate is incomplete")
    elif status == "unavailable":
        if membership is not None or not isinstance(reason, str) or not reason:
            raise ValueError("native unavailable phase warmonger predicate requires null and reason")
    else:
        raise ValueError("native phase warmonger status is malformed")
    return {
        "status": status, "source_character_id": source, "raw_adopted_rite_id": raw,
        "rite_id": rite, "rite_resolution": resolution, "requested_tenet_key": "tenet_warmonger",
        "target_tenet_key": target, "warmonger_core_membership": membership,
        "unavailable_reason": reason,
    }
