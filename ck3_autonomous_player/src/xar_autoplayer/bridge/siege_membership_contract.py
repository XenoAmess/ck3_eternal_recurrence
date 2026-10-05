"""Actual Province CUnit occurrences used by the native siege M/K loops."""
from __future__ import annotations

from .public_unit_contract import optional_public_cunit_id


def _id(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a non-negative full int32 ID")
    return value


def normalize_siege_province_unit_occurrences(
    value: object, *, name: str
) -> list[dict[str, object]] | None:
    """Keep failed reads, known exclusion and qualified empty lists distinct.

    The native collection's order and repeated identities are significant;
    this normalizer does not turn it into an army or regiment set.
    """
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a Province occurrence array or null")
    result: list[dict[str, object]] = []
    for index, row in enumerate(value):
        row_name = f"{name}[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{row_name} must be an object")
        occurrence = _id(row.get("occurrence_index"), f"{row_name}.occurrence_index")
        if occurrence != index:
            raise ValueError(f"{row_name} must preserve the native occurrence index")
        unit_id = optional_public_cunit_id(row.get("public_unit_id"), f"{row_name}.public_unit_id")
        army_id = row.get("native_carmy_id")
        if army_id is not None:
            army_id = _id(army_id, f"{row_name}.native_carmy_id")
        eligible = row.get("eligible")
        if eligible is not None and type(eligible) is not bool:
            raise ValueError(f"{row_name}.eligible must be boolean or null")
        regiments = row.get("qualified_regiment_ids")
        if regiments is not None:
            if not isinstance(regiments, list):
                raise ValueError(f"{row_name}.qualified_regiment_ids must be an array or null")
            regiments = [
                _id(item, f"{row_name}.qualified_regiment_ids[{regiment}]")
                for regiment, item in enumerate(regiments)
            ]
        if eligible is True and (unit_id is None or army_id is None):
            raise ValueError(f"{row_name} eligible native input lacks its resolved identities")
        if eligible is False and regiments != []:
            raise ValueError(f"{row_name} excluded occurrence must have no consumed regiments")
        if eligible is None and regiments is not None:
            raise ValueError(f"{row_name} unresolved qualification cannot publish consumed regiments")
        result.append({
            "occurrence_index": occurrence,
            "public_unit_id": unit_id,
            "native_carmy_id": army_id,
            "eligible": eligible,
            "qualified_regiment_ids": regiments,
        })
    return result
