"""Copied native kinship for one selected existing prisoner collection row."""
from __future__ import annotations
import copy
from collections.abc import Mapping

_ENVELOPE = {"private_build", "read_only", "advertised", "action_surface_present", "status"}
_AVAILABLE = _ENVELOPE | {
    "snapshot_id", "native_revision", "proof_epoch", "date_raw", "source_ordinal",
    "jailer_character_id", "prisoner_character_id",
    "is_close_family_of_played_character", "is_close_or_extended_family_of_played_character",
}


def normalize_prisoner_native_kinship_12003(
    value: Mapping[str, object], *, native_revision: int, date_raw: int,
    proof_epoch: int, player_character_id: int, prisoner_character_id: int,
    source_ordinal: int, selected_ordinal: int,
) -> dict[str, object]:
    if (
        not isinstance(value, Mapping) or value.get("private_build") is not True
        or value.get("read_only") is not True or value.get("advertised") is not False
        or value.get("action_surface_present") is not False
    ):
        raise ValueError("private prisoner native kinship envelope is malformed")
    if value.get("status") == "unavailable":
        reason = value.get("unavailable_reason")
        if set(value) != _ENVELOPE | {"unavailable_reason"} or not isinstance(reason, str) or not reason:
            raise ValueError("private prisoner native kinship unavailable result is malformed")
        if (reason == "not_evaluated") is (source_ordinal == selected_ordinal):
            raise ValueError("private prisoner native kinship evaluated the wrong ordinal")
        return copy.deepcopy(dict(value))
    if source_ordinal != selected_ordinal or set(value) != _AVAILABLE or value.get("status") != "available":
        raise ValueError("private prisoner native kinship available fields or ordinal are malformed")
    expected = {
        "native_revision": native_revision, "proof_epoch": proof_epoch,
        "date_raw": date_raw, "source_ordinal": source_ordinal,
        "jailer_character_id": player_character_id, "prisoner_character_id": prisoner_character_id,
    }
    if (
        value.get("snapshot_id") != f"native:{native_revision}"
        or any(type(value.get(key)) is not int or value[key] != raw for key, raw in expected.items())
        or any(type(value.get(key)) is not bool for key in (
            "is_close_family_of_played_character", "is_close_or_extended_family_of_played_character",
        ))
    ):
        raise ValueError("private prisoner native kinship differs from actual collection frame or custody")
    return copy.deepcopy(dict(value))
