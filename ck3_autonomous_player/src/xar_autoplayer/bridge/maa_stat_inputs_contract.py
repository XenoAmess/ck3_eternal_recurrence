"""Typed optional wire for actual .3 MAA getter source operands."""
from __future__ import annotations

from .ordinary_stat_inputs_contract import _object, _integer

STAT_NAMES = ("max_size", "siege_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw")
ENV_NAMES = ("type_terrain", "type_definition", "type_province", "linked_terrain", "linked_definition", "linked_province")
FIELDS = frozenset(("status", "source_target_province_id", "source_regiment_full_id",
    "selected_character_full_id", "character_resolution", "inner_type_is_gdbo", "selector_mode",
    "selected_type_class", "type_bases", "selected_properties", "class_row_present",
    "class_add_keys_u16", "class_mult_keys_u16", "culture_full_id", "government_index",
    "government_rows", "global_rows", "extra_properties", "extra_add_keys_u16", "extra_mult_keys_u16",
    "extra_title_full_id", "extra_holder_full_id", "holder_piety_rank", "selected_government_byte_4d6",
    "selector_factor_q64", "linked_character_full_ids", "accolade_blocks", "definition620_present",
    "environment_components", "fallback_ordinary_bases", "scale", "unavailable_reason"))


def _bool(value, name):
    if value is not None and type(value) is not bool:
        raise ValueError(f"native {name} must be bool or null")
    return value


def _keys(value, size, name):
    if value is None:
        return None
    if (not isinstance(value, list) or (size is not None and len(value) != size) or
            any(type(key) is not int or not 0 <= key <= 65535 for key in value)):
        raise ValueError(f"native {name} must contain actual U16 keys")
    return list(value)


def _stats(value, name):
    if value is None:
        return None
    row = _object(value, STAT_NAMES, name)
    out = {key: _integer(row[key], 32 if i == 0 else 64, name + "." + key)
           for i, key in enumerate(STAT_NAMES)}
    if any(item is None for item in out.values()):
        raise ValueError(f"native {name} lacks an actual six-vector")
    return out


def _properties(value, name):
    if value is None:
        return None
    row = _object(value, {"count", "keys_u16", "values_q64"}, name)
    count = _integer(row["count"], 32, name + ".count")
    keys = _keys(row["keys_u16"], None, name + ".keys_u16")
    values = row["values_q64"]
    if not isinstance(values, list):
        raise ValueError(f"native {name}.values_q64 differs")
    values = [_integer(item, 64, name + ".values_q64") for item in values]
    if count is None or count < 0 or keys is None or len(keys) != count or len(values) != count or any(item is None for item in values):
        raise ValueError(f"native {name} has incomplete property arrays")
    return {"count": count, "keys_u16": keys, "values_q64": values}


def _culture(value, name):
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"native {name} differs")
    result = []
    for index, value_row in enumerate(value):
        path = name + "[" + str(index) + "]"
        row = _object(value_row, {"definition_index", "row_index", "definition_is_gdbo",
            "definition_matches_selected_type", "class_filter", "stats"}, path)
        result.append({key: (_stats(row[key], path + ".stats") if key == "stats" else
            _bool(row[key], path + "." + key) if key.startswith("definition_") and key != "definition_index" else
            _integer(row[key], 32, path + "." + key)) for key in row})
    return result


def normalize_maa_stat_inputs_v1(value, *, name):
    row = _object(value, FIELDS, name)
    status = row["status"]
    if status not in {"available", "unavailable"} or row["scale"] != 100000:
        raise ValueError(f"native {name} status/scale differs")
    out = {"status": status, "scale": 100000}
    ints = ("source_target_province_id", "source_regiment_full_id", "selected_character_full_id",
        "selected_type_class", "culture_full_id", "government_index", "extra_title_full_id",
        "extra_holder_full_id", "holder_piety_rank", "selected_government_byte_4d6", "selector_factor_q64")
    for key in ints:
        out[key] = _integer(row[key], 64 if key == "selector_factor_q64" else 32, name + "." + key)
    for key in ("inner_type_is_gdbo", "selector_mode", "class_row_present", "definition620_present"):
        out[key] = _bool(row[key], name + "." + key)
    resolution = row["character_resolution"]
    if resolution not in {None, "generation_resolved", "native_fallback"}:
        raise ValueError(f"native {name}.character_resolution differs")
    out["character_resolution"] = resolution
    out["type_bases"] = _stats(row["type_bases"], name + ".type_bases")
    for key in ("selected_properties", "extra_properties"):
        out[key] = _properties(row[key], name + "." + key)
    for key in ("class_add_keys_u16", "class_mult_keys_u16", "extra_add_keys_u16", "extra_mult_keys_u16"):
        out[key] = _keys(row[key], 5 if key.startswith("extra") else 6, name + "." + key)
    for key in ("government_rows", "global_rows"):
        out[key] = _culture(row[key], name + "." + key)
    linked = row["linked_character_full_ids"]
    if linked is not None and not isinstance(linked, list):
        raise ValueError(f"native {name}.linked_character_full_ids differs")
    out["linked_character_full_ids"] = (None if linked is None else
        [_integer(item, 32, name + ".linked_character_full_ids") for item in linked])
    blocks = row["accolade_blocks"]
    if blocks is not None and not isinstance(blocks, list):
        raise ValueError(f"native {name}.accolade_blocks differs")
    out["accolade_blocks"] = None if blocks is None else []
    for i, value_block in enumerate(blocks or ()):
        path = name + ".accolade_blocks[" + str(i) + "]"
        block = _object(value_block, {"linked_index", "character_full_id", "accolade_full_id",
            "row_index", "level", "properties"}, path)
        out["accolade_blocks"].append({key: (_properties(block[key], path + ".properties") if key == "properties"
            else _integer(block[key], 32, path + "." + key)) for key in block})
    env = _object(row["environment_components"], ENV_NAMES, name + ".environment_components")
    out["environment_components"] = {key: _stats(env[key], name + ".environment_components." + key) for key in ENV_NAMES}
    bases = _object(row["fallback_ordinary_bases"], STAT_NAMES[1:], name + ".fallback_ordinary_bases")
    out["fallback_ordinary_bases"] = {key: _integer(bases[key], 64, name + ".fallback_ordinary_bases." + key) for key in STAT_NAMES[1:]}
    reason = row["unavailable_reason"]
    if status == "unavailable":
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"native unavailable {name} lacks reason")
    else:
        required = ["source_target_province_id", "source_regiment_full_id", "selected_character_full_id",
            "character_resolution", "inner_type_is_gdbo", "selected_properties", "selector_mode"]
        if out["inner_type_is_gdbo"] is False:
            if any(item is None for item in out["fallback_ordinary_bases"].values()):
                raise ValueError(f"native available {name} lacks ordinary fallback bases")
        else:
            required += ["selected_type_class", "type_bases", "class_row_present", "culture_full_id",
                "government_index", "government_rows", "global_rows", "selected_government_byte_4d6",
                "linked_character_full_ids", "accolade_blocks", "definition620_present"]
            if out["class_row_present"] is True:
                required += ["class_add_keys_u16", "class_mult_keys_u16", "extra_properties",
                    "extra_add_keys_u16", "extra_mult_keys_u16", "extra_title_full_id", "extra_holder_full_id", "holder_piety_rank"]
            if out["selector_mode"] is True:
                required += ["selector_factor_q64"]
            for key in ENV_NAMES:
                if key in {"type_definition", "linked_definition"} and out["definition620_present"] is False:
                    continue
                if out["environment_components"][key] is None:
                    raise ValueError(f"native available {name} lacks actual environment vector {key}")
            cls = out["selected_type_class"]
            for culture_rows in (out["government_rows"], out["global_rows"]):
                for culture_row in culture_rows or ():
                    if ((not culture_row["definition_is_gdbo"] or culture_row["definition_matches_selected_type"]) and
                            culture_row["class_filter"] in {-1, cls} and culture_row["stats"] is None):
                        raise ValueError(f"native available {name} lacks admitted culture row")
        if any(out[key] is None for key in required) or reason is not None:
            raise ValueError(f"native available {name} lacks demanded source operands")
    out["unavailable_reason"] = reason
    return out
