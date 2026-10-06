"""Normalize additive current persistent-regiment and actual Army-role inputs."""

from __future__ import annotations

from collections.abc import Mapping


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _available(value: Mapping[str, object], subject: str) -> None:
    if type(value.get("available")) is not bool:
        raise ValueError(f"native holy-order {subject} availability is malformed")
    reason = value.get("unavailable_reason")
    if (value["available"] and reason is not None) or (
        not value["available"] and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError(f"native holy-order {subject} unavailable reason is malformed")


def normalize_holy_order_current_reinforcement_v1(
    value: object, *, employer_id: object, played_character_id: int,
) -> object:
    """Retain source occurrences, actual raw refs and both native predicates."""
    if not isinstance(value, Mapping) or value.get("fraction_scale") != 100000:
        raise ValueError("native holy-order reinforcement family is malformed")
    _available(value, "reinforcement")
    count = value.get("source_count")
    if count is not None and not _integer(count, -(1 << 31), (1 << 31) - 1):
        raise ValueError("native holy-order persistent roster count is malformed")
    rows = value.get("rows")
    if not isinstance(rows, list) or (value["available"] and count != len(rows)):
        raise ValueError("native holy-order persistent roster occurrences are malformed")
    for index, row in enumerate(rows):
        if (not isinstance(row, Mapping) or row.get("source_index") != index
                or not _integer(row.get("persistent_regiment_id"), 0, 0xFFFFFFFF)
                or type(row.get("resolved")) is not bool):
            raise ValueError("native holy-order persistent identity is malformed")
        _available(row, "persistent regiment")
        for key, low, high in (
            ("owner_character_id", 0, 0xFFFFFFFF),
            ("monthly_replenishment_fraction_raw", -(1 << 63), (1 << 63) - 1),
            ("native_months_to_full", -(1 << 31), (1 << 31) - 1),
        ):
            field = row.get(key)
            if field is not None and not _integer(field, low, high):
                raise ValueError(f"native holy-order persistent input is malformed: {key}")
            if row["available"] and row["resolved"] and field is None:
                raise ValueError(f"available native holy-order persistent input is absent: {key}")
        chunks = row.get("chunks")
        if not isinstance(chunks, list) or (row["resolved"] and row["available"] and len(chunks) != 7):
            raise ValueError("native holy-order persistent chunks are malformed")
        if not row["resolved"] and (chunks or any(row.get(key) is not None for key in (
            "owner_character_id", "monthly_replenishment_fraction_raw", "native_months_to_full"
        ))):
            raise ValueError("unresolved native holy-order reference has actual regiment inputs")
        for chunk_index, chunk in enumerate(chunks):
            if not isinstance(chunk, Mapping) or chunk.get("chunk_index") != chunk_index:
                raise ValueError("native holy-order chunk ordinal is malformed")
            _available(chunk, "reinforcement chunk")
            for key, low, high in (
                ("maximum_soldiers", -(1 << 31), (1 << 31) - 1),
                ("current_soldiers", -(1 << 31), (1 << 31) - 1),
                ("persistent_regiment_id", 0, 0xFFFFFFFF),
                ("native_chunk_index", -(1 << 31), (1 << 31) - 1),
                ("army_regiment_id", 0, 0xFFFFFFFF),
                ("pending_raw", 0, 255),
                ("state_raw", -(1 << 31), (1 << 31) - 1),
            ):
                field = chunk.get(key)
                if (field is not None and not _integer(field, low, high)) or (
                    chunk["available"] and field is None
                ):
                    raise ValueError(f"native holy-order chunk input is malformed: {key}")
            for key in ("native_can_replenish", "native_chunk_can_replenish"):
                field = chunk.get(key)
                if (field is not None and type(field) is not bool) or (
                    chunk["available"] and type(field) is not bool
                ):
                    raise ValueError(f"native holy-order independent predicate is malformed: {key}")
    roles = value.get("army_roles")
    if (not isinstance(roles, Mapping) or type(roles.get("applies_to_player")) is not bool
            or roles["applies_to_player"] != (employer_id == played_character_id)):
        raise ValueError("native holy-order Army-role scope is malformed")
    _available(roles, "Army roles")
    role_rows = roles.get("rows")
    if not isinstance(role_rows, list) or (not roles["applies_to_player"] and role_rows):
        raise ValueError("native holy-order Army-role occurrences are malformed")
    for index, role in enumerate(role_rows):
        if (not isinstance(role, Mapping) or role.get("association_index") != index
                or not _integer(role.get("army_regiment_id"), 0, 0xFFFFFFFF)
                or any(type(role.get(key)) is not bool for key in ("army_resolved", "unit_resolved"))):
            raise ValueError("native holy-order Army-role identity is malformed")
        _available(role, "Army role")
        for key in ("native_carmy_id", "commander_character_id", "public_army_id", "unit_carmy_backlink", "owner_character_id"):
            field = role.get(key)
            if field is not None and not _integer(field, 0, 0xFFFFFFFF):
                raise ValueError(f"native holy-order Army-role reference is malformed: {key}")
        if role["available"] and role["army_resolved"] and any(role.get(key) is None for key in (
            "native_carmy_id", "commander_character_id", "public_army_id"
        )):
            raise ValueError("available native holy-order Army fields are incomplete")
        if role["unit_resolved"] and (not role["army_resolved"] or role.get("owner_character_id") is None):
            raise ValueError("native holy-order actual Unit owner is incomplete")
    return value
