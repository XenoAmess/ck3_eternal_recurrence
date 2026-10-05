"""True CCreateMAARegimentCommand personal readonly permission and final raw quote."""
from __future__ import annotations


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _optional_integer(value: object, name: str) -> int | None:
    return None if value is None else _integer(value, name, -(2**31), 2**31 - 1)


def _bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be bool")
    return value


def _reason(value: object) -> str | None:
    if value is not None and (not isinstance(value, str) or not value):
        raise ValueError("native MAA unavailable_reason must be a nonempty string or null")
    return value


def _quote(value: object) -> dict[str, object]:
    fields = {"context", "status", "unavailable_reason", "resource_scale", "resources_raw"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("regular personal quote fields are invalid")
    if value["context"] != "regular_personal_create" or value["status"] not in {"available", "unavailable"}:
        raise ValueError("regular personal quote context/status is invalid")
    scale = _integer(value["resource_scale"], "resource_scale", 100000, 100000)
    raw = value["resources_raw"]
    if raw is not None:
        if not isinstance(raw, list) or len(raw) != 10:
            raise ValueError("regular personal quote requires ten signed native resource slots")
        raw = [_integer(item, "native raw resource", -(2**63), 2**63 - 1) for item in raw]
    reason = _reason(value["unavailable_reason"])
    if value["status"] == "available" and (raw is None or reason is not None):
        raise ValueError("available regular quote requires observed resources")
    return {"context": value["context"], "status": value["status"],
            "unavailable_reason": reason, "resource_scale": scale, "resources_raw": raw}


def _type(value: object) -> dict[str, object]:
    fields = {"type_key", "type_index", "inputs_ready", "unavailable_reason",
              "effective_quantity", "can_create", "regular_personal_quote"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("regular MAA type fields are invalid")
    if not isinstance(value["type_key"], str) or not value["type_key"]:
        raise ValueError("native MAA type_key must be a nonempty native key")
    can_create = value["can_create"]
    if can_create is not None:
        can_create = _bool(can_create, "can_create")
    return {"type_key": value["type_key"],
            "type_index": _integer(value["type_index"], "type_index", -1, 2**31 - 1),
            "inputs_ready": _bool(value["inputs_ready"], "inputs_ready"),
            "unavailable_reason": _reason(value["unavailable_reason"]),
            "effective_quantity": _optional_integer(value["effective_quantity"], "effective_quantity"),
            "can_create": can_create, "regular_personal_quote": _quote(value["regular_personal_quote"])}


def normalize_native_maa_recruitment_inputs_v1(value: object) -> dict[str, object] | None:
    """Preserve native false, default -1, raw zero and unread null without recomputing policy."""
    if value is None:
        return None
    fields = {"schema_version", "status", "unavailable_reason", "owner_character_id", "creation_kind",
              "creation_scope", "command_class", "title_id", "requested_quantity", "pay_cost",
              "catalog_observed", "types_in_native_order", "missing_type_keys"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("regular native MAA input fields are invalid")
    version = _integer(value["schema_version"], "schema_version", 1, 1)
    if value["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError("regular native MAA status is invalid")
    if value["creation_scope"] != "regular_personal" or value["command_class"] != "CCreateMAARegimentCommand":
        raise ValueError("regular native MAA scope/class is invalid")
    rows, missing = value["types_in_native_order"], value["missing_type_keys"]
    if not isinstance(rows, list) or not isinstance(missing, list) or any(
            not isinstance(key, str) or not key for key in missing):
        raise ValueError("native MAA catalog arrays are invalid")
    return {"schema_version": version, "status": value["status"],
            "unavailable_reason": _reason(value["unavailable_reason"]),
            "owner_character_id": _optional_integer(value["owner_character_id"], "owner_character_id"),
            "creation_kind": _integer(value["creation_kind"], "creation_kind", 1, 1),
            "creation_scope": value["creation_scope"], "command_class": value["command_class"],
            "title_id": _integer(value["title_id"], "title_id", -1, -1),
            "requested_quantity": _integer(value["requested_quantity"], "requested_quantity", -1, -1),
            "pay_cost": _bool(value["pay_cost"], "pay_cost"),
            "catalog_observed": _bool(value["catalog_observed"], "catalog_observed"),
            "types_in_native_order": [_type(row) for row in rows], "missing_type_keys": list(missing)}
