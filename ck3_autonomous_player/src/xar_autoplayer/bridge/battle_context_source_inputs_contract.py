"""Current exact .3 source operands, independently from prepared context.

Native row order, snapshot-local definition identities and raw signed words
are retained. The optional enclosing field distinguishes older producers
from an explicitly null source observation. No branch applies native writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .battle_context_admissions_v86_contract import (
    SELECTOR_EXTENSION_FIELDS_V86,
    normalize_admission_extension_row_v86,
    normalize_selector_extension_fields_v86,
)

if TYPE_CHECKING:
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativeWeightedContributionRequest12003,
    )


_SPAN_NAMES = (
    "selected_lifestyle_span", "selected_dynasty_span", "selected_house_span",
    "selected_house_extra_span",
)


def _dict(value: object, field: str, fields: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field} must contain exactly {sorted(fields)}")
    return value


def _integer(value: object, field: str, bits: int, *, unsigned: bool = False) -> int:
    minimum = 0 if unsigned else -(2 ** (bits - 1))
    maximum = 2**bits - 1 if unsigned else 2 ** (bits - 1) - 1
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{field} must be a native {'unsigned' if unsigned else 'signed'}{bits} integer")
    return value


def _number(value: object, field: str, bits: int, *, unsigned: bool = False) -> int | None:
    return None if value is None else _integer(value, field, bits, unsigned=unsigned)


def _boolean(value: object, field: str, *, optional: bool = False) -> bool | None:
    if optional and value is None:
        return None
    if type(value) is not bool:
        raise ValueError(f"{field} must be a boolean{' or null' if optional else ''}")
    return value


def _string(value: object, field: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if type(value) is not str or not value:
        raise ValueError(f"{field} must be a nonempty string{' or null' if optional else ''}")
    return value


def _numbers(value: object, field: str, bits: int, *, unsigned: bool = False) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list or null")
    return [_integer(item, f"{field}[{i}]", bits, unsigned=unsigned)
            for i, item in enumerate(value)]


def _properties(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "keys_count", "values_count", "keys_u16", "values_q64", "reason",
    })
    return {
        "keys_count": _number(raw["keys_count"], field + ".keys_count", 32),
        "values_count": _number(raw["values_count"], field + ".values_count", 32),
        "keys_u16": _numbers(raw["keys_u16"], field + ".keys_u16", 16, unsigned=True),
        "values_q64": _numbers(raw["values_q64"], field + ".values_q64", 64),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }


def _properties_ready(block: dict[str, object] | None) -> bool:
    if block is None:
        return False
    count = block["keys_count"]
    if count == 0:
        return True
    if type(count) is not int or count < 0:
        return False
    keys, values = block["keys_u16"], block["values_q64"]
    # +74 is provenance; native 2438850 consumes +C keys and corresponding
    # values. A zero +C exits before arrays or +74 are needed.
    return (isinstance(keys, list) and len(keys) >= count
            and isinstance(values, list) and len(values) >= count)


def _resolution(value: object, field: str) -> dict[str, object]:
    raw = _dict(value, field, {
        "status", "requested_full_id", "selected_full_id", "reason",
    })
    return {
        "status": _string(raw["status"], field + ".status"),
        "requested_full_id": _number(raw["requested_full_id"], field + ".requested_full_id", 32, unsigned=True),
        "selected_full_id": _number(raw["selected_full_id"], field + ".selected_full_id", 32, unsigned=True),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }


def _span(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, field, {"selected_source", "count", "rows", "reason"})
    count = _number(raw["count"], field + ".count", 32)
    rows = raw["rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".rows must be a list or null")
        copied = []
        for i, item in enumerate(rows):
            name = f"{field}.rows[{i}]"
            row = _dict(item, name, {"native_index", "definition_identity", "weight_q64"})
            native_index = _integer(row["native_index"], name + ".native_index", 32)
            if native_index != i:
                raise ValueError(name + ".native_index disagrees with native row order")
            copied.append({
                "native_index": native_index,
                "definition_identity": _string(row["definition_identity"], name + ".definition_identity", optional=True),
                "weight_q64": _number(row["weight_q64"], name + ".weight_q64", 64),
            })
        rows = copied
    return {
        "selected_source": _string(raw["selected_source"], field + ".selected_source"),
        "count": count, "rows": rows,
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }


def _availability(raw: dict[str, object], field: str) -> tuple[str, bool, str | None]:
    status = raw["status"]
    ready = _boolean(raw["ready"], field + ".ready")
    reason = _string(raw["reason"], field + ".reason", optional=True)
    if status not in {"available", "partial", "unavailable"}:
        raise ValueError(field + ".status is invalid")
    if (status == "available") != ready or (ready and reason is not None) or (not ready and reason is None):
        raise ValueError(field + " availability disagrees")
    return status, ready, reason


def _pre_291e210_1640(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", "army_selection", "army_key_f4_raw",
        "army_field_120_raw", "army_field_124_raw", "second_selection",
        "second_field_174_raw", "admitted", "property_block", "unavailable_reason",
    })
    status, ready, reason = _availability({
        "status": raw["status"], "ready": raw["ready"],
        "reason": raw["unavailable_reason"],
    }, field)
    normalized = {
        "status": status, "ready": ready,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
        "unavailable_reason": reason,
    }
    for key in ("army_selection", "second_selection"):
        selected = _string(raw[key], field + "." + key, optional=True)
        if selected not in {None, "registry_full_id", "native_fallback"}:
            raise ValueError(field + "." + key + " is invalid")
        normalized[key] = selected
    for key in ("army_key_f4_raw", "army_field_120_raw", "army_field_124_raw",
                "second_field_174_raw"):
        normalized[key] = _number(raw[key], field + "." + key, 32)
    first, second = normalized["army_field_120_raw"], normalized["second_field_174_raw"]
    actual = False if first == -1 else (first == second if first is not None and second is not None else None)
    if normalized["admitted"] != actual:
        raise ValueError(field + ".admitted disagrees with the exact DWORD predicate")
    if first == -1 and any(normalized[key] is not None for key in (
        "army_field_124_raw", "second_selection", "second_field_174_raw",
    )):
        raise ValueError(field + " early false branch contains undemanded second operands")
    if actual is not True and normalized["property_block"] is not None:
        raise ValueError(field + " provider block requires true admission")
    complete = (normalized["army_selection"] is not None and actual is not None
                and (first == -1 or normalized["second_selection"] is not None)
                and (not actual or _properties_ready(normalized["property_block"])))
    if ready != complete:
        raise ValueError(field + " availability disagrees with consumed native operands")
    return normalized


def _branch_291e210(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "component_present", "first_relation_resolution",
        "second_relation_resolution", "house_resolution", "house_extra_enabled",
        *_SPAN_NAMES, "definition_blocks", "reason",
    })
    status, ready, reason = _availability(raw, field)
    definitions = raw["definition_blocks"]
    if not isinstance(definitions, list):
        raise ValueError(field + ".definition_blocks must be a list")
    blocks = []
    seen = set()
    for i, value in enumerate(definitions):
        name = f"{field}.definition_blocks[{i}]"
        block = _dict(value, name, {"definition_identity", "properties"})
        identity = _string(block["definition_identity"], name + ".definition_identity")
        if identity in seen:
            raise ValueError(name + ".definition_identity is not distinct")
        seen.add(identity)
        blocks.append({"definition_identity": identity,
                       "properties": _properties(block["properties"], name + ".properties")})
    normalized = {
        "status": status, "ready": ready,
        "component_present": _boolean(raw["component_present"], field + ".component_present", optional=True),
        "house_extra_enabled": _boolean(raw["house_extra_enabled"], field + ".house_extra_enabled", optional=True),
        "definition_blocks": blocks, "reason": reason,
    }
    for key in ("first_relation_resolution", "second_relation_resolution", "house_resolution"):
        normalized[key] = _resolution(raw[key], field + "." + key)
    for key in _SPAN_NAMES:
        normalized[key] = _span(raw[key], field + "." + key)
    if ready and not _a_consumed_ready(normalized):
        raise ValueError(field + " available branch lacks consumed native operands")
    return normalized


def _a_consumed_ready(branch: dict[str, object]) -> bool:
    gate = branch["house_extra_enabled"]
    if type(gate) is not bool or type(branch["component_present"]) is not bool:
        return False
    blocks = {item["definition_identity"]: item["properties"]
              for item in branch["definition_blocks"]}
    # The current census observes all four actually selected headers, including
    # the disabled fourth span's native static header. The emitter itself skips
    # that fourth call when the gate is false.
    for key in _SPAN_NAMES:
        span = branch[key]
        if span is None or span["count"] is None:
            return False
        count = span["count"]
        if count <= 0:
            continue
        rows = span["rows"]
        if rows is None or len(rows) < count:
            return False
        for row in rows[:count]:
            identity = row["definition_identity"]
            if (identity is None or row["weight_q64"] is None
                    or not _properties_ready(blocks.get(identity))):
                return False
    return True


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise ValueError(field + " must be a string")
    return value


def _raw_rows(value: object, field: str, normalize) -> list[dict[str, object]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(field + " must be a list or null")
    copied = []
    for i, row in enumerate(value):
        name = f"{field}[{i}]"
        normalized = normalize(row, name)
        if normalized["native_index"] != i:
            raise ValueError(name + ".native_index disagrees with native row order")
        copied.append(normalized)
    return copied


def _conditional_a(value: object, field: str) -> dict[str, object]:
    fields = {
        "native_index", "key_identity", "key_object_id", "key_object_magic",
        "property_block", "admitted", "reason",
    }
    if isinstance(value, dict):
        fields.update(set(value) & {'property_source', 'property_source_native_index'})
    raw = _dict(value, field, fields)
    normalized = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "key_identity": _string(raw["key_identity"], field + ".key_identity", optional=True),
        "key_object_id": _number(raw["key_object_id"], field + ".key_object_id", 32, unsigned=True),
        "key_object_magic": _number(raw["key_object_magic"], field + ".key_object_magic", 32, unsigned=True),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    normalized.update(normalize_admission_extension_row_v86(raw, field, 'a'))
    return normalized


def _conditional_b(value: object, field: str) -> dict[str, object]:
    fields = {
        "native_index", "key_i32", "property_block", "admitted", "reason",
    }
    if isinstance(value, dict):
        fields.update(set(value) & {'admission_source', 'admission_nested_native_index'})
    raw = _dict(value, field, fields)
    normalized = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "key_i32": _number(raw["key_i32"], field + ".key_i32", 32),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    normalized.update(normalize_admission_extension_row_v86(raw, field, 'b'))
    return normalized


def _conditional_c(value: object, field: str) -> dict[str, object]:
    fields = {
        "native_index", "source_key_u32", "masked_index_u32", "resolver_count_i32",
        "selected_native_fallback", "invert_u8", "property_block",
        "resolved_condition_identity", "condition_source", "condition_length",
        "condition_capacity", "condition_bytes", "first_signed_byte",
        "classifier_mode_i32", "classifier_result_i32", "condition_token_id", "admitted",
        "token_origin", "lookup_status", "reason",
    }
    if isinstance(value, dict):
        fields.update(set(value) & {'locale_classification'})
    raw = _dict(value, field, fields)
    normalized = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "source_key_u32": _number(raw["source_key_u32"], field + ".source_key_u32", 32, unsigned=True),
        "masked_index_u32": _number(raw["masked_index_u32"], field + ".masked_index_u32", 32, unsigned=True),
        "resolver_count_i32": _number(raw["resolver_count_i32"], field + ".resolver_count_i32", 32),
        "selected_native_fallback": _boolean(raw["selected_native_fallback"], field + ".selected_native_fallback", optional=True),
        "invert_u8": _number(raw["invert_u8"], field + ".invert_u8", 8, unsigned=True),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
        "resolved_condition_identity": _string(raw["resolved_condition_identity"], field + ".resolved_condition_identity", optional=True),
        "condition_source": _text(raw["condition_source"], field + ".condition_source"),
        "condition_length": _number(raw["condition_length"], field + ".condition_length", 32),
        "condition_capacity": _number(raw["condition_capacity"], field + ".condition_capacity", 64, unsigned=True),
        "condition_bytes": _numbers(raw["condition_bytes"], field + ".condition_bytes", 8, unsigned=True),
        "first_signed_byte": _number(raw["first_signed_byte"], field + ".first_signed_byte", 32),
        "classifier_mode_i32": _number(raw["classifier_mode_i32"], field + ".classifier_mode_i32", 32),
        "classifier_result_i32": _number(raw["classifier_result_i32"], field + ".classifier_result_i32", 32),
        "condition_token_id": _number(raw["condition_token_id"], field + ".condition_token_id", 32),
        "admitted": _boolean(raw["admitted"], field + ".admitted", optional=True),
        "token_origin": _text(raw["token_origin"], field + ".token_origin"),
        "lookup_status": _text(raw["lookup_status"], field + ".lookup_status"),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    normalized.update(normalize_admission_extension_row_v86(raw, field, 'c'))
    return normalized


def _source_row(value: object, field: str) -> dict[str, object]:
    raw = _dict(value, field, {
        "native_index", "source_identity", "base_properties",
        "auxiliary_410_provenance", "auxiliary_retained_identity", "auxiliary_retained_present", "auxiliary_tag_u32",
        "conditional_a_count", "conditional_b_count", "conditional_c_count",
        "conditional_a_rows", "conditional_b_rows", "conditional_c_rows", "reason",
    })
    normalized = {
        "native_index": _integer(raw["native_index"], field + ".native_index", 32),
        "source_identity": _string(raw["source_identity"], field + ".source_identity", optional=True),
        "base_properties": _properties(raw["base_properties"], field + ".base_properties"),
        "auxiliary_410_provenance": _text(raw["auxiliary_410_provenance"], field + ".auxiliary_410_provenance"),
        "auxiliary_retained_identity": _string(raw["auxiliary_retained_identity"], field + ".auxiliary_retained_identity", optional=True),
        "auxiliary_retained_present": _boolean(raw["auxiliary_retained_present"], field + ".auxiliary_retained_present", optional=True),
        "auxiliary_tag_u32": _number(raw["auxiliary_tag_u32"], field + ".auxiliary_tag_u32", 32, unsigned=True),
        "reason": _string(raw["reason"], field + ".reason", optional=True),
    }
    for kind, normalize in (("a", _conditional_a), ("b", _conditional_b), ("c", _conditional_c)):
        count_key, rows_key = f"conditional_{kind}_count", f"conditional_{kind}_rows"
        normalized[count_key] = _number(raw[count_key], field + "." + count_key, 32)
        normalized[rows_key] = _raw_rows(raw[rows_key], field + "." + rows_key, normalize)
    return normalized


def _branch_291d7e0(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    fields = {
        "status", "ready", "base_inputs_ready", "component_present",
        "selected_source", "source_count", "source_rows",
        "conditional_a_fallback_properties", "government_token_count",
        "government_token_ids_i32", "government_source", "condition_registry_guard",
        "condition_fallback_guard", "token_manager_present", "reason",
    }
    if isinstance(value, dict):
        fields.update(set(value) & SELECTOR_EXTENSION_FIELDS_V86)
    raw = _dict(value, field, fields)
    status, ready, reason = _availability(raw, field)
    # Base-copy arrays keep their independent +28C/+2F4 headers. The A
    # append-executor's empty-key shortcut is deliberately not applied here.
    normalized = {
        "status": status, "ready": ready,
        "base_inputs_ready": _boolean(raw["base_inputs_ready"], field + ".base_inputs_ready"),
        "component_present": _boolean(raw["component_present"], field + ".component_present", optional=True),
        "selected_source": _text(raw["selected_source"], field + ".selected_source"),
        "source_count": _number(raw["source_count"], field + ".source_count", 32),
        "source_rows": _raw_rows(raw["source_rows"], field + ".source_rows", _source_row),
        "conditional_a_fallback_properties": _properties(raw["conditional_a_fallback_properties"], field + ".conditional_a_fallback_properties"),
        "government_token_count": _number(raw["government_token_count"], field + ".government_token_count", 32),
        "government_token_ids_i32": _numbers(raw["government_token_ids_i32"], field + ".government_token_ids_i32", 32),
        "government_source": _text(raw["government_source"], field + ".government_source"),
        "condition_registry_guard": _number(raw["condition_registry_guard"], field + ".condition_registry_guard", 32),
        "condition_fallback_guard": _number(raw["condition_fallback_guard"], field + ".condition_fallback_guard", 32),
        "token_manager_present": _boolean(raw["token_manager_present"], field + ".token_manager_present", optional=True),
        "reason": reason,
    }
    if normalized["base_inputs_ready"] != _b_base_ready(normalized):
        raise ValueError(field + " base-copy availability disagrees with independently observed arrays")
    if ready != _b_consumed_ready(normalized):
        raise ValueError(field + " conditional availability disagrees with observed admission inputs")
    normalized.update(normalize_selector_extension_fields_v86(raw, field))
    return normalized


def _b_base_ready(branch: dict[str, object]) -> bool:
    count = branch["source_count"]
    if type(branch["component_present"]) is not bool or count is None:
        return False
    if count <= 0:
        return True
    rows = branch["source_rows"]
    if rows is None or len(rows) < count:
        return False
    for row in rows[:count]:
        block = row["base_properties"]
        if row["source_identity"] is None or block is None:
            return False
        for count_key, array_key in (("keys_count", "keys_u16"), ("values_count", "values_q64")):
            native_count, values = block[count_key], block[array_key]
            if native_count is None or native_count < 0 or values is None or len(values) < native_count:
                return False
    return True


def _b_consumed_ready(branch: dict[str, object]) -> bool:
    if not branch["base_inputs_ready"]:
        return False
    source_count = branch["source_count"]
    if source_count <= 0:
        return True
    for source in branch["source_rows"][:source_count]:
        for kind in ("a", "b", "c"):
            count, rows = source[f"conditional_{kind}_count"], source[f"conditional_{kind}_rows"]
            if count is None or rows is None:
                return False
            if count <= 0:
                continue
            if len(rows) < count:
                return False
            for row in rows[:count]:
                admitted = row["admitted"]
                if type(admitted) is not bool:
                    return False
                if kind == "c":
                    government_count, government_tokens = branch["government_token_count"], branch["government_token_ids_i32"]
                    if (row["condition_token_id"] is None or row["invert_u8"] is None
                            or government_count is None or government_tokens is None
                            or len(government_tokens) < max(0, government_count)):
                        return False
                if admitted and not _properties_ready(row["property_block"]):
                    return False
    return True


def _post_availability(raw: dict[str, object], field: str) -> tuple[str, bool, str | None]:
    return _availability({"status": raw["status"], "ready": raw["ready"],
                          "reason": raw["unavailable_reason"]}, field)


def _post_guarded630(value: object, field: str) -> dict[str, object]:
    raw = _dict(value, field, {
        "status", "ready", "carrier_1b0_present", "carrier280_present", "selection",
        "selected_field38_raw", "character68_signed", "threshold_signed",
        "admitted", "property_block", "unavailable_reason",
    })
    status, ready, reason = _post_availability(raw, field)
    normalized = {
        "status": status, "ready": ready, "unavailable_reason": reason,
        "selection": _string(raw["selection"], field + ".selection", optional=True),
        "selected_field38_raw": _number(raw["selected_field38_raw"], field + ".selected_field38_raw", 32),
        "character68_signed": _number(raw["character68_signed"], field + ".character68_signed", 16),
        "threshold_signed": _number(raw["threshold_signed"], field + ".threshold_signed", 32),
        "property_block": _properties(raw["property_block"], field + ".property_block"),
    }
    for key in ("carrier_1b0_present", "carrier280_present", "admitted"):
        normalized[key] = _boolean(raw[key], field + "." + key, optional=True)
    carrier, nested = normalized["carrier_1b0_present"], normalized["carrier280_present"]
    expected_selection = ("native_fallback5D1E308" if carrier is False or (carrier is True and nested is False)
                          else "carrier280_qword8" if carrier is True and nested is True else None)
    if normalized["selection"] != expected_selection:
        raise ValueError(field + ".selection disagrees with current pointer guards")
    magic, signed, threshold = (normalized["selected_field38_raw"],
                                normalized["character68_signed"], normalized["threshold_signed"])
    admitted = None if magic is None else (False if magic != 0x4744624F else
               signed >= threshold if signed is not None and threshold is not None else None)
    if normalized["admitted"] != admitted:
        raise ValueError(field + ".admitted disagrees with native magic/signed comparison")
    if magic is not None and magic != 0x4744624F and (signed is not None or threshold is not None):
        raise ValueError(field + " wrong magic contains undemanded signed operands")
    if admitted is not True and normalized["property_block"] is not None:
        raise ValueError(field + " property block requires true admission")
    consumed = (expected_selection is not None and admitted is not None
                and (not admitted or _properties_ready(normalized["property_block"])))
    if ready != consumed:
        raise ValueError(field + " availability disagrees with demanded operands")
    return normalized


def _post_carrier40(value: object, field: str) -> dict[str, object]:
    raw = _dict(value, field, {
        "status", "ready", "carrier_1b0_present", "carrier288_present",
        "admitted", "property_block", "unavailable_reason",
    })
    status, ready, reason = _post_availability(raw, field)
    normalized = {"status": status, "ready": ready, "unavailable_reason": reason,
                  "property_block": _properties(raw["property_block"], field + ".property_block")}
    for key in ("carrier_1b0_present", "carrier288_present", "admitted"):
        normalized[key] = _boolean(raw[key], field + "." + key, optional=True)
    carrier, nested = normalized["carrier_1b0_present"], normalized["carrier288_present"]
    admitted = False if carrier is False else nested if carrier is True else None
    if normalized["admitted"] != admitted:
        raise ValueError(field + ".admitted disagrees with native pointer guards")
    if carrier is False and nested is not None:
        raise ValueError(field + " null carrier contains undemanded +288 operand")
    if admitted is not True and normalized["property_block"] is not None:
        raise ValueError(field + " property block requires true admission")
    consumed = admitted is not None and (not admitted or _properties_ready(normalized["property_block"]))
    if ready != consumed:
        raise ValueError(field + " availability disagrees with demanded operands")
    return normalized


def _post_ordered_d8(value: object, field: str) -> dict[str, object]:
    raw = _dict(value, field, {
        "status", "ready", "carrier_1c0_present", "header_selection",
        "source_array_present", "source_count_raw", "occurrences", "unavailable_reason",
    })
    status, ready, reason = _post_availability(raw, field)
    carrier = _boolean(raw["carrier_1c0_present"], field + ".carrier_1c0_present", optional=True)
    selected = _string(raw["header_selection"], field + ".header_selection", optional=True)
    expected = None if carrier is None else "carrier_1c0_plus200" if carrier else "inline_static54E7270"
    if selected != expected:
        raise ValueError(field + ".header_selection disagrees with current carrier")
    count = _number(raw["source_count_raw"], field + ".source_count_raw", 32)
    array_present = _boolean(raw["source_array_present"], field + ".source_array_present", optional=True)
    rows = raw["occurrences"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(field + ".occurrences must be a list or null")
        copied = []
        for i, row in enumerate(rows):
            name = f"{field}.occurrences[{i}]"
            row = _dict(row, name, {"source_index", "source_identity", "property_block", "unavailable_reason"})
            index = _integer(row["source_index"], name + ".source_index", 32)
            if index != i:
                raise ValueError(name + ".source_index disagrees with stored occurrence order")
            copied.append({
                "source_index": index,
                "source_identity": _string(row["source_identity"], name + ".source_identity", optional=True),
                "property_block": _properties(row["property_block"], name + ".property_block"),
                "unavailable_reason": _string(row["unavailable_reason"], name + ".unavailable_reason", optional=True),
            })
        rows = copied
    consumed = (carrier is not None and array_present is not None
                and count is not None and count >= 0 and rows is not None and len(rows) == count
                and (count == 0 or array_present is True)
                and all(row["source_identity"] is not None and _properties_ready(row["property_block"]) for row in rows))
    if ready != consumed:
        raise ValueError(field + " availability disagrees with stored source occurrences")
    return {
        "status": status, "ready": ready, "carrier_1c0_present": carrier,
        "header_selection": selected, "source_array_present": array_present,
        "source_count_raw": count, "occurrences": rows, "unavailable_reason": reason,
    }


def _post_291d7e0_sources(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, field, {
        "status", "ready", "character_id", "guarded630", "carrier40", "ordered_d8", "unavailable_reason",
    })
    status, ready, reason = _post_availability(raw, field)
    normalized = {
        "status": status, "ready": ready, "unavailable_reason": reason,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "guarded630": _post_guarded630(raw["guarded630"], field + ".guarded630"),
        "carrier40": _post_carrier40(raw["carrier40"], field + ".carrier40"),
        "ordered_d8": _post_ordered_d8(raw["ordered_d8"], field + ".ordered_d8"),
    }
    if ready != all(normalized[key]["ready"] for key in ("guarded630", "carrier40", "ordered_d8")):
        raise ValueError(field + " availability disagrees with independent current source leaves")
    return normalized


def normalize_current_context_source_inputs(
    value: object, field: str = "current_context_source_inputs",
) -> dict[str, object] | None:
    """Copy current native source census, keeping nulls and independent readiness."""
    if value is None:
        return None
    fields = {"status", "ready", "character_id", "branch_291e210", "reason"}
    if isinstance(value, dict) and "branch_291d7e0" in value:
        fields.add("branch_291d7e0")
    if isinstance(value, dict) and "pre_291e210_1640" in value:
        fields.add("pre_291e210_1640")
    if isinstance(value, dict) and "post_291d7e0_sources" in value:
        fields.add("post_291d7e0_sources")
    if isinstance(value, dict) and "later_direct_291c3fb_44c" in value:
        fields.add("later_direct_291c3fb_44c")
    if isinstance(value, dict) and "helper_291f0a0" in value:
        fields.add("helper_291f0a0")
    if isinstance(value, dict) and "later_helpers_291f550_291f940" in value:
        fields.add("later_helpers_291f550_291f940")
    if isinstance(value, dict) and "tail_direct_291c5b7_291cc49" in value:
        fields.add("tail_direct_291c5b7_291cc49")
    for optional in ("tail_prefix_2753860_2922530", "middle_helpers_291f260_291fb10",
                     "trait_stage_291d460", "absent_recipient_inputs", "helper_2922070"):
        if isinstance(value, dict) and optional in value:
            fields.add(optional)
    raw = _dict(value, field, fields)
    status, ready, reason = _availability(raw, field)
    normalized = {
        "status": status, "ready": ready,
        "character_id": _integer(raw["character_id"], field + ".character_id", 32),
        "branch_291e210": _branch_291e210(raw["branch_291e210"], field + ".branch_291e210"),
        "reason": reason,
    }
    if "branch_291d7e0" in raw:
        normalized["branch_291d7e0"] = _branch_291d7e0(
            raw["branch_291d7e0"], field + ".branch_291d7e0")
    if "pre_291e210_1640" in raw:
        pre = _pre_291e210_1640(raw["pre_291e210_1640"], field + ".pre_291e210_1640")
        if pre is not None and pre["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".pre_291e210_1640 character disagrees with source actor")
        normalized["pre_291e210_1640"] = pre
    if "post_291d7e0_sources" in raw:
        post = _post_291d7e0_sources(raw["post_291d7e0_sources"], field + ".post_291d7e0_sources")
        if post is not None and post["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".post_291d7e0_sources character disagrees with source actor")
        normalized["post_291d7e0_sources"] = post
    if "later_direct_291c3fb_44c" in raw:
        from .battle_person_later_direct_contract import normalize_later_direct_291c3fb_44c
        later = normalize_later_direct_291c3fb_44c(
            raw["later_direct_291c3fb_44c"], field + ".later_direct_291c3fb_44c")
        if later is not None and later["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".later_direct_291c3fb_44c character disagrees with source actor")
        normalized["later_direct_291c3fb_44c"] = later
    if "helper_291f0a0" in raw:
        from .battle_person_helper_291f0a0_contract import normalize_helper_291f0a0
        helper = normalize_helper_291f0a0(raw["helper_291f0a0"], field + ".helper_291f0a0")
        if helper is not None and helper["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".helper_291f0a0 character disagrees with source actor")
        normalized["helper_291f0a0"] = helper
    if "later_helpers_291f550_291f940" in raw:
        from .battle_person_remaining_helpers_contract import normalize_later_helpers_291f550_291f940
        later = normalize_later_helpers_291f550_291f940(
            raw["later_helpers_291f550_291f940"], field + ".later_helpers_291f550_291f940")
        if later is not None and later["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".later_helpers_291f550_291f940 character disagrees with source actor")
        normalized["later_helpers_291f550_291f940"] = later
    if "tail_direct_291c5b7_291cc49" in raw:
        from .battle_person_tail_direct_contract import normalize_tail_direct_291c5b7_291cc49
        tail = normalize_tail_direct_291c5b7_291cc49(
            raw["tail_direct_291c5b7_291cc49"], field + ".tail_direct_291c5b7_291cc49")
        if tail is not None and tail["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".tail_direct_291c5b7_291cc49 character disagrees with source actor")
        normalized["tail_direct_291c5b7_291cc49"] = tail
    if "tail_prefix_2753860_2922530" in raw:
        from .battle_person_tail_prefix_contract import normalize_tail_prefix_2753860_2922530
        tail = normalize_tail_prefix_2753860_2922530(
            raw["tail_prefix_2753860_2922530"], field + ".tail_prefix_2753860_2922530")
        if tail is not None and tail["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".tail_prefix_2753860_2922530 character disagrees with source actor")
        normalized["tail_prefix_2753860_2922530"] = tail
    if "middle_helpers_291f260_291fb10" in raw:
        from .battle_person_middle_helpers_contract import normalize_middle_helpers_291f260_291fb10
        middle = normalize_middle_helpers_291f260_291fb10(
            raw["middle_helpers_291f260_291fb10"], field + ".middle_helpers_291f260_291fb10")
        if middle is not None and middle["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".middle_helpers_291f260_291fb10 character disagrees with source actor")
        normalized["middle_helpers_291f260_291fb10"] = middle
    if "trait_stage_291d460" in raw:
        from .battle_person_trait_stage_291d460_contract import normalize_trait_stage_291d460
        trait = normalize_trait_stage_291d460(
            raw["trait_stage_291d460"], field + ".trait_stage_291d460")
        if trait is not None and trait["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".trait_stage_291d460 character disagrees with source actor")
        normalized["trait_stage_291d460"] = trait
    if "absent_recipient_inputs" in raw:
        from .battle_person_absent_recipient_contract import normalize_absent_recipient_inputs
        absent = normalize_absent_recipient_inputs(
            raw["absent_recipient_inputs"], field + ".absent_recipient_inputs")
        if absent is not None and absent["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".absent_recipient_inputs character disagrees with source actor")
        normalized["absent_recipient_inputs"] = absent
    if "helper_2922070" in raw:
        from .battle_person_helper_2922070_contract import normalize_helper_2922070
        helper = normalize_helper_2922070(raw["helper_2922070"], field + ".helper_2922070")
        if helper is not None and helper["character_id"] != normalized["character_id"]:
            raise ValueError(field + ".helper_2922070 character disagrees with source actor")
        normalized["helper_2922070"] = helper
    return normalized


def emit_pre_291e210_1640_requests_from_current_source_inputs_12003(
    normalized_section: dict[str, object] | None,
) -> tuple[NativeWeightedContributionRequest12003, ...]:
    """Emit the unit request after 291D1D0 and before A (then B).

    This observes no baseline and performs no append. Current final storage
    cannot supply the required before-stage baseline for a later assembler.
    """
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativeWeightedContributionRequest12003,
    )

    value = None if normalized_section is None else normalized_section.get("pre_291e210_1640")
    branch = _pre_291e210_1640(value, "pre_291e210_1640")
    if branch is None or not branch["ready"]:
        raise ValueError("Required native input unavailable: pre_291e210_1640")
    if not branch["admitted"]:
        return ()
    return (NativeWeightedContributionRequest12003(
        source_ordinal=0, source_name="pre_291e210_1640", first_row_index=0,
        row_count=1, definition_identity="provider1640",
        base_property_block=value["property_block"], weight_q64=100000,
    ),)


def emit_post_291d7e0_requests_from_current_source_inputs_12003(
    normalized_section: dict[str, object] | None,
) -> tuple[NativeWeightedContributionRequest12003, ...]:
    """Emit guarded630, carrier40, then every orderedD8 occurrence after B.

    Empty blocks and duplicate occurrences remain separate unit requests. No
    stage baseline, current-final append, model rebuild or Entry is inferred.
    """
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativeWeightedContributionRequest12003,
    )

    value = None if normalized_section is None else normalized_section.get("post_291d7e0_sources")
    branch = _post_291d7e0_sources(value, "post_291d7e0_sources")
    if branch is None or not branch["ready"]:
        raise ValueError("Required native input unavailable: post_291d7e0_sources")
    requests = []
    for ordinal, name in ((1, "guarded630"), (2, "carrier40")):
        if branch[name]["admitted"]:
            requests.append(NativeWeightedContributionRequest12003(
                ordinal, "post_291d7e0_" + name, 0, 1,
                "post_291d7e0_" + name, value[name]["property_block"], 100000,
            ))
    for row in value["ordered_d8"]["occurrences"]:
        requests.append(NativeWeightedContributionRequest12003(
            3, "post_291d7e0_ordered_d8", row["source_index"], 1,
            row["source_identity"], row["property_block"], 100000,
        ))
    return tuple(requests)


def emit_291e210_requests_from_current_source_inputs_12003(
    normalized_section: dict[str, object] | None,
) -> tuple[NativeWeightedContributionRequest12003, ...]:
    """Adapt actual A fields to the adopted pure emitter; B readiness is separate.

    Actual PropertyContainer snapshot dictionaries pass through by reference.
    This emits append requests and does not apply them to a context baseline.
    """
    from ..simulation.battle_context_preparation_branch_291e210_12003 import (
        NativePreparationSourceRow12003,
        NativePreparationSourceSpan12003,
        emit_291e210_contribution_requests_12003,
    )

    if normalized_section is None or normalized_section.get("branch_291e210") is None:
        raise ValueError("Required native input unavailable: branch_291e210")
    branch = normalized_section["branch_291e210"]
    if not branch["ready"] or not _a_consumed_ready(branch):
        raise ValueError("Required native input unavailable: branch_291e210 consumed operands")
    blocks = {item["definition_identity"]: item["properties"]
              for item in branch["definition_blocks"]}

    def span(key: str) -> NativePreparationSourceSpan12003 | None:
        actual = branch[key]
        if actual is None:
            return None
        rows = actual["rows"]
        copied = None if rows is None else tuple(
            NativePreparationSourceRow12003(
                definition_identity=row["definition_identity"],
                weight_q64=row["weight_q64"],
                base_property_block=blocks.get(row["definition_identity"]),
            ) for row in rows
        )
        return NativePreparationSourceSpan12003(count=actual["count"], rows=copied)

    return emit_291e210_contribution_requests_12003(
        span(_SPAN_NAMES[0]), span(_SPAN_NAMES[1]), span(_SPAN_NAMES[2]),
        branch["house_extra_enabled"], span(_SPAN_NAMES[3]),
    )
