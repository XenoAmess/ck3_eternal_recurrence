"""Optional V86 selector/locale observations; no admission is inferred here."""
from __future__ import annotations


SELECTOR_EXTENSION_FIELDS_V86 = frozenset({
    "selector_a_stage1", "selector_a_stage2", "selector_a_stage3",
    "selector_a_selected_source", "selector_a_key_count", "selector_a_key_identities",
    "selector_b_resolution", "selector_b_primary_keys", "selector_b_nested_count",
    "selector_b_nested_keys",
})


def _object(value: object, field: str, fields: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(field + " fields disagree")
    return value


def _int(value: object, field: str, bits: int = 32, unsigned: bool = False):
    if value is None:
        return None
    low, high = (0, 2**bits - 1) if unsigned else (-(2**(bits-1)), 2**(bits-1)-1)
    if type(value) is not int or not low <= value <= high:
        raise ValueError(field + " native integer disagrees")
    return value


def _bool(value: object, field: str):
    if value is not None and type(value) is not bool:
        raise ValueError(field + " must be boolean or null")
    return value


def _text(value: object, field: str, optional: bool = False):
    if optional and value is None:
        return None
    if type(value) is not str:
        raise ValueError(field + " must be a string")
    return value


def _list(value: object, field: str, copy):
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(field + " must be a list or null")
    return [copy(item, f"{field}[{i}]") for i, item in enumerate(value)]


def _resolution(value: object, field: str):
    if value is None:
        return None
    raw = _object(value, field, {"status", "requested_full_id", "selected_full_id", "reason"})
    return {"status": _text(raw["status"], field + ".status"),
            "requested_full_id": _int(raw["requested_full_id"], field + ".requested_full_id", unsigned=True),
            "selected_full_id": _int(raw["selected_full_id"], field + ".selected_full_id", unsigned=True),
            "reason": _text(raw["reason"], field + ".reason", optional=True)}


def _signed_set(value: object, field: str):
    if value is None:
        return None
    raw = _object(value, field, {"native_index", "count", "keys_i32", "reason"})
    return {"native_index": _int(raw["native_index"], field + ".native_index"),
            "count": _int(raw["count"], field + ".count"),
            "keys_i32": _list(raw["keys_i32"], field + ".keys_i32", _int),
            "reason": _text(raw["reason"], field + ".reason", optional=True)}


def normalize_selector_extension_fields_v86(raw: dict, field: str) -> dict:
    copied = {}
    for key in SELECTOR_EXTENSION_FIELDS_V86:
        if key not in raw:
            continue
        value, name = raw[key], field + "." + key
        if key in {"selector_a_stage1", "selector_a_stage2", "selector_a_stage3", "selector_b_resolution"}:
            copied[key] = _resolution(value, name)
        elif key == "selector_a_selected_source":
            copied[key] = _text(value, name)
        elif key == "selector_a_key_identities":
            copied[key] = _list(value, name, _text)
        elif key == "selector_b_primary_keys":
            copied[key] = _signed_set(value, name)
        elif key == "selector_b_nested_keys":
            # Native demanded prefix may stop before the declared nested count.
            copied[key] = _list(value, name, _signed_set)
        else:
            copied[key] = _int(value, name)
    return copied


def normalize_locale_classification_v86(value: object, field: str):
    if value is None:
        return None
    signed = {"first_signed_byte", "locale_max_multibyte", "result_i32"}
    unsigned = {"crt_index", "thread_locale_flags", "flags_mask"}
    booleans = {"thread_state_present", "current_locale_present", "global_locale_present", "selected_locale_present"}
    strings = {"cached_value_api_status", "thread_state_source", "locale_source"}
    raw = _object(value, field, signed | unsigned | booleans | strings | {"status", "ready", "table_element_u16", "reason"})
    copied = {"status": _text(raw["status"], field + ".status"),
              "ready": _bool(raw["ready"], field + ".ready"),
              "reason": _text(raw["reason"], field + ".reason", optional=True)}
    for key in signed:
        copied[key] = _int(raw[key], field + "." + key)
    for key in unsigned:
        copied[key] = _int(raw[key], field + "." + key, unsigned=True)
    for key in booleans:
        copied[key] = _bool(raw[key], field + "." + key)
    for key in strings:
        copied[key] = _text(raw[key], field + "." + key)
    copied["table_element_u16"] = _int(raw["table_element_u16"], field + ".table_element_u16", 16, unsigned=True)
    if (type(copied["ready"]) is not bool or copied["status"] not in {"available", "partial", "unavailable"}
            or copied["ready"] != (copied["status"] == "available")
            or (copied["ready"] and (copied["result_i32"] is None or copied["reason"] is not None))
            or (not copied["ready"] and not copied["reason"])):
        raise ValueError(field + " classification availability disagrees")
    return copied


def normalize_admission_extension_row_v86(raw: dict, field: str, kind: str) -> dict:
    copied = {}
    if kind == "a":
        names = ("property_source", "property_source_native_index")
    elif kind == "b":
        names = ("admission_source", "admission_nested_native_index")
    else:
        names = ("locale_classification",)
    for key in names:
        if key not in raw:
            continue
        if key == "locale_classification":
            copied[key] = normalize_locale_classification_v86(raw[key], field + "." + key)
        elif key.endswith("index"):
            copied[key] = _int(raw[key], field + "." + key)
        else:
            copied[key] = _text(raw[key], field + "." + key)
    return copied
