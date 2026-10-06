"""Optional same-combat-query adopted Rite Boolean-parameter leaf.

The leaf belongs to its commander/knight Character occurrence.  It does not
describe the Faith's main Rite or add a combat/forecast completeness gate.
"""

from __future__ import annotations

from typing import Literal, TypedDict


INVALID_PHASE_RITE_REF = 0xFFFFFFFF
PHASE_RITE_PARAMETERS_LEAF = "phase_rite_parameters_v1"


class PhaseRiteParametersV1(TypedDict):
    status: Literal["available", "absent", "unavailable"]
    source_character_id: int
    raw_adopted_rite_id: int
    rite_id: int | None
    faith_id: int | None
    boolean_parameters_complete: bool
    boolean_parameter_keys: list[str]
    unavailable_reason: str | None


def _uint32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"native phase Rite {name} must be uint32")
    return value


def _resolved_ref(value: object, name: str) -> int | None:
    if value is None:
        return None
    ref = _uint32(value, name)
    if ref == INVALID_PHASE_RITE_REF:
        raise ValueError(f"native phase Rite {name} must null the absent reference")
    return ref


def normalize_phase_rite_parameters_v1(
    value: object, *, expected_character_id: int | None
) -> PhaseRiteParametersV1 | None:
    """Normalize an optional leaf without converting missing reads to false.

    ``None`` is the old packet's unpublished leaf. Reference zero and the
    full generation bits are legal; only FFFFFFFF represents an absent Rite.
    A complete Rite can have an observed absent source Faith (``faith_id=None``).
    """

    if value is None:
        return None
    keys = {
        "status", "source_character_id", "raw_adopted_rite_id", "rite_id",
        "faith_id", "boolean_parameters_complete", "boolean_parameter_keys",
        "unavailable_reason",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("native phase Rite parameter leaf schema is malformed")
    status = value["status"]
    if status not in ("available", "absent", "unavailable"):
        raise ValueError("native phase Rite parameter status is malformed")
    source = _uint32(value["source_character_id"], "source_character_id")
    if source == INVALID_PHASE_RITE_REF or source != _uint32(expected_character_id, "expected_character_id"):
        raise ValueError("native phase Rite source CharacterID mismatch")
    raw = _uint32(value["raw_adopted_rite_id"], "raw_adopted_rite_id")
    rite = _resolved_ref(value["rite_id"], "rite_id")
    faith = _resolved_ref(value["faith_id"], "faith_id")
    complete = value["boolean_parameters_complete"]
    if not isinstance(complete, bool):
        raise ValueError("native phase Rite boolean_parameters_complete must be boolean")
    parameters = value["boolean_parameter_keys"]
    if not isinstance(parameters, list) or any(not isinstance(key, str) or not key for key in parameters):
        raise ValueError("native phase Rite Boolean keys must be nonempty strings")
    if len(parameters) != len(set(parameters)):
        raise ValueError("native phase Rite Boolean keys contain duplicates")
    reason = value["unavailable_reason"]
    if rite is not None and rite != raw:
        raise ValueError("native phase Rite resolved ID differs from the adopted reference")
    if status == "available":
        if raw == INVALID_PHASE_RITE_REF or rite is None or not complete or reason is not None:
            raise ValueError("native available phase Rite parameters are incomplete")
    elif status == "absent":
        if raw != INVALID_PHASE_RITE_REF or rite is not None or faith is not None or complete or parameters or reason is not None:
            raise ValueError("native absent phase Rite parameters are inconsistent")
    elif complete or parameters or not isinstance(reason, str) or not reason:
        raise ValueError("native unavailable phase Rite parameters require an empty incomplete set and reason")
    return {
        "status": status,
        "source_character_id": source,
        "raw_adopted_rite_id": raw,
        "rite_id": rite,
        "faith_id": faith,
        "boolean_parameters_complete": complete,
        "boolean_parameter_keys": list(parameters),
        "unavailable_reason": reason,
    }
