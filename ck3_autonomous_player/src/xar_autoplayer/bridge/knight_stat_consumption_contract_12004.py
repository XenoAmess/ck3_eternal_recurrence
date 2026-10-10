"""Exact4 knight consumption and optional observed physical Entry writeback."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _boolean, _dict, _integer, _number, _string,
)
from .version_identity import CK3_12004, require_exact_native_build

KNIGHT_STAT_CONSUMPTION_LEAF = "knight_stat_consumption_v1"
SCHEMA = "xar.ck3.knight-stat-consumption-12004-v1"
_CAPACITY = 32
_PC_FIELDS = {
    "ready", "reason", "admitted", "identity", "count_i32", "properties",
    "weight_q100000",
}
_CONTEXT_FIELDS = {
    "property_key", "caller_return_rva", "selected_character_id",
    "selected_character_identity", "context_identity", "operand_raw", "consumed_pc",
    "preparation_capture_sequence", "preparation_model_identity",
    "preparation_context_identity", "preparation_owner_character_id",
    "context_matches_preparation", "owner_matches_preparation",
    "pc_matches_preparation_post", "reason",
}
_STAGE_SCHEMA = "xar.ck3.entry-selected-receiver-stage-12004-v1"
_CI_RETURN_RVAS = (
    0x2C06B03, 0x2C06B51, 0x2C06B8D, 0x2C06BC4, 0x2C06BFB,
    0x2C06C32, 0x2C06C69, 0x2C06CA0, 0x2C06CD7,
)
_STAGE_BOOLEANS = {
    "exact_consumed_callsite", "exact_capture_build", "preparation_capture_observed",
    "preparation_capture_complete", "preparation_raw_counts_ready",
    "completed_preparation_lineage_proven",
}
_STAGE_COMPARISONS = {
    "capture_sequence_matches_record", "exact_preparation_source_return",
    "selected_matches_capture_identity", "selected_matches_capture_id",
    "selected_matches_model_owner_identity", "selected_matches_model_owner_id",
    "getter_matches_capture_context", "getter_matches_preparation_model_inline",
    "completion_on_consumption_thread", "completed_post_pc_matches_consumed",
}
_STAGE_IDENTITIES = {
    "linked_character_identity", "selected_character_identity", "getter_context_identity",
    "preparation_character_identity", "preparation_model_identity",
    "preparation_context_identity", "preparation_owner_character_identity",
}
_STAGE_IDS = {"linked_character_id", "selected_character_id", "preparation_owner_character_id"}
_STAGE_FIELDS = {
    "schema", "property_key", "consumed_return_rva", "observation_stage",
    "preparation_stage", "preparation_stage_observed_mask", "preparation_capture_sequence",
    "preparation_source_return_rva", "preparation_capture_thread_id",
    "preparation_completion_thread_id", "consumption_thread_id", "reason",
    *_STAGE_BOOLEANS, *_STAGE_COMPARISONS, *_STAGE_IDENTITIES, *_STAGE_IDS,
}
_TRANSFER_SCHEMA = "xar.ck3.knight-installed-transfer-lineage-12004-v1"
_TRANSFER_CAPTURE_SCHEMA = "xar.ck3.person-installed-transfer-capture-12004-v1"
_TRANSFER_RELATIONSHIPS = {
    "transfer_completed_before_getter", "selected_matches_transfer_owner",
    "getter_matches_installed_context",
}
_TRANSFER_SNAPSHOT_IDENTITIES = {
    "model_a_owner_identity", "model_b_owner_identity", "observed_owner_identity",
    "carrier_identity", "installed_model_identity", "installed_model_owner_identity",
    "matching_installed_inline_context_identity",
}
_TRANSFER_SNAPSHOT_IDS = {
    "model_a_owner_character_id", "model_b_owner_character_id", "observed_owner_character_id",
}
_TRANSFER_SNAPSHOT_FLAGS = {
    "installed_owner_matches_observed_owner", "installed_model_is_a", "installed_model_is_b",
}
_TRANSFER_PREPARATION_IDENTITIES = {
    "preparation_character_identity", "preparation_model_identity",
    "preparation_context_identity", "preparation_owner_character_identity",
}
_TRANSFER_STAGE_FLAGS = {
    "preparation_model_is_b", "preparation_owner_matches_before", "preparation_owner_matches_after",
    "before_after_owner_generation_equal", "event_clock_and_thread_match", "completion_ordered_after_begin",
}
_TRANSFER_UNPROVEN_FLAGS = {
    "generic_postimages_complete", "transfer_to_entry_association_proven",
    "observer_model_write_performed", "full_person_ready", "entry_ready",
}
_OUTPUT_RAW_FIELDS = (
    "siege_value_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw",
)
_EVENT_FIELDS = {
    "sequence", "thread_id", "observed_date_raw", "wrapper_caller_return_rva",
    "origin", "regiment_id", "target_province_id", "linked_character_id",
    "linked_character_identity", "linked_prowess_points", "loaded_damage_multiplier",
    "loaded_toughness_multiplier", "output_cache_identity", "native_return_identity",
    "contexts", "observed_output", "entry_association_proven", "capture_reason",
}
_WRITEBACK_FIELDS = {
    "writer_sequence", "entry_identity", "province_identity", "regiment_id",
    "province_id", "original_return_value", "entry_cache",
    "output_cache_identity_matches_entry", "wrapper_output_comparison_ready",
    "wrapper_output_field_matches", "wrapper_output_matches_entry_cache",
    "regiment_member_at_query", "reason",
}
_QUERY_FIELDS = {
    "schema", "build_version", "executable_sha256", "configured", "observer_installed",
    "oldest_available_sequence", "latest_sequence", "overwritten_events", "events", "reason",
}


def _raw64(value: object, path: str, *, unsigned: bool = False,
           optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    if type(value) is str:
        digits = value if unsigned else value[1:] if value.startswith("-") else value
        if not digits or not digits.isascii() or not digits.isdecimal():
            raise ValueError(path + " must retain a native decimal64 string or integer")
        value = int(value, 10)
    return _integer(value, path, 64, unsigned=unsigned)


def _identity(value: object, path: str, *, optional: bool = True) -> int | None:
    if value is None and optional:
        return None
    if type(value) is str and value.startswith(("0x", "0X")):
        digits = value[2:]
        if not digits or any(char not in "0123456789abcdefABCDEF" for char in digits):
            raise ValueError(path + " must be a native identity integer or hexadecimal string")
        value = int(digits, 16)
    return _raw64(value, path, unsigned=True, optional=optional)


def _array(value: object, path: str) -> list:
    if not isinstance(value, list):
        raise ValueError(path + " must preserve native occurrence order")
    return value


def _pc(value: object, path: str) -> dict[str, object]:
    raw = _dict(value, path, _PC_FIELDS)
    result = {
        "ready": _boolean(raw["ready"], path + ".ready"),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
        "admitted": _boolean(raw["admitted"], path + ".admitted", optional=True),
        "identity": _identity(raw["identity"], path + ".identity"),
        "count_i32": _number(raw["count_i32"], path + ".count_i32", 32),
        "weight_q100000": _raw64(raw["weight_q100000"], path + ".weight_q100000"),
    }
    if result["weight_q100000"] != 0:
        raise ValueError(path + " weight differs from the existing aggregate PC copy")
    block = raw["properties"]
    if block is not None:
        block = _dict(block, path + ".properties", {"keys_u16", "values_q64"})
        keys = block["keys_u16"]
        values = block["values_q64"]
        block = {
            "keys_u16": None if keys is None else [
                _integer(key, f"{path}.properties.keys_u16[{index}]", 16, unsigned=True)
                for index, key in enumerate(_array(keys, path + ".properties.keys_u16"))
            ],
            "values_q64": None if values is None else [
                _raw64(item, f"{path}.properties.values_q64[{index}]")
                for index, item in enumerate(_array(values, path + ".properties.values_q64"))
            ],
        }
        count = result["count_i32"]
        if count is not None and count >= 0 and any(
            block[key] is not None and len(block[key]) > count
            for key in ("keys_u16", "values_q64")
        ):
            raise ValueError(path + " physical arrays exceed the observed PC count")
    result["properties"] = block
    if result["ready"] and result["admitted"] is True:
        count = result["count_i32"]
        if (result["identity"] is None or count is None or count < 0 or block is None
                or block["keys_u16"] is None or block["values_q64"] is None
                or len(block["keys_u16"]) != count or len(block["values_q64"]) != count):
            raise ValueError(path + " ready admitted PC lacks its actual counted properties")
    return result


def _preparation_stage_lineage(value: object, row: dict, path: str) -> dict | None:
    if value is None:
        return None
    raw = _dict(value, path, _STAGE_FIELDS)
    if raw["schema"] != _STAGE_SCHEMA:
        raise ValueError(path + " requires the actual4 selected-receiver stage schema")
    result = {
        "schema": _STAGE_SCHEMA,
        "property_key": _integer(raw["property_key"], path + ".property_key", 16, unsigned=True),
        "consumed_return_rva": _raw64(raw["consumed_return_rva"], path + ".consumed_return_rva", unsigned=True),
        "preparation_capture_sequence": _raw64(raw["preparation_capture_sequence"], path + ".preparation_capture_sequence", unsigned=True),
        "preparation_source_return_rva": _raw64(raw["preparation_source_return_rva"], path + ".preparation_source_return_rva", unsigned=True, optional=True),
        "preparation_stage_observed_mask": _integer(raw["preparation_stage_observed_mask"], path + ".preparation_stage_observed_mask", 8, unsigned=True),
        "consumption_thread_id": _integer(raw["consumption_thread_id"], path + ".consumption_thread_id", 32, unsigned=True),
        "observation_stage": _string(raw["observation_stage"], path + ".observation_stage"),
        "preparation_stage": _string(raw["preparation_stage"], path + ".preparation_stage"),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }
    for field in _STAGE_BOOLEANS | _STAGE_COMPARISONS:
        result[field] = _boolean(raw[field], path + "." + field,
                                 optional=field in _STAGE_COMPARISONS)
    for field in _STAGE_IDENTITIES:
        result[field] = _identity(raw[field], path + "." + field)
    for field in _STAGE_IDS | {"preparation_capture_thread_id", "preparation_completion_thread_id"}:
        result[field] = _number(raw[field], path + "." + field, 32, unsigned=True)
    for field, row_field in (
        ("property_key", "property_key"), ("consumed_return_rva", "caller_return_rva"),
        ("selected_character_id", "selected_character_id"),
        ("selected_character_identity", "selected_character_identity"),
        ("getter_context_identity", "context_identity"),
    ):
        if result[field] != row[row_field]:
            raise ValueError(path + "." + field + " differs from this actual consumed Ci")
    if (result["observation_stage"] != "actual_effectiveness_context_return"
            or result["preparation_stage"] not in {
                "unobserved", "open_native_six_stage_capture", "paused_same_thread_six_stage_completion"}
            or result["preparation_stage_observed_mask"] > 0x3F):
        raise ValueError(path + " changed its actual observation stage")
    exact_call = row["caller_return_rva"] == _CI_RETURN_RVAS[row["property_key"] - 0xC1]
    if result["exact_consumed_callsite"] is not exact_call:
        raise ValueError(path + " exact callsite flag differs from its observed return")
    if result["completed_preparation_lineage_proven"]:
        if (not all(result[field] is True for field in
                    _STAGE_BOOLEANS | _STAGE_COMPARISONS)
                or result["preparation_stage"] != "paused_same_thread_six_stage_completion"
                or result["preparation_stage_observed_mask"] != 0x3F
                or result["preparation_capture_sequence"] == 0
                or result["preparation_capture_sequence"] != row["preparation_capture_sequence"]
                or result["preparation_source_return_rva"] != 0x291CEA9
                or result["reason"] is not None
                or not row["consumed_pc"]["ready"]):
            raise ValueError(path + " completed proof lacks its owned completion facts")
        selected, context = row["selected_character_identity"], row["context_identity"]
        model = result["preparation_model_identity"]
        if (selected in (None, 0) or context in (None, 0) or model in (None, 0)
                or selected != result["preparation_character_identity"]
                or selected != result["preparation_owner_character_identity"]
                or row["selected_character_id"] is None
                or row["selected_character_id"] != result["preparation_owner_character_id"]
                or row["selected_character_id"] != row["preparation_owner_character_id"]
                or model != row["preparation_model_identity"]
                or context != result["preparation_context_identity"]
                or context != row["preparation_context_identity"]
                or context != model + 0x10
                or row["consumed_pc"]["identity"] != context + 0x68
                or result["consumption_thread_id"] == 0
                or result["preparation_capture_thread_id"] != result["consumption_thread_id"]
                or result["preparation_completion_thread_id"] != result["consumption_thread_id"]):
            raise ValueError(path + " completed proof differs from this Ci's receiver or thread")
    return result


def _capture_at_consumption(value: object, row: dict, path: str) -> dict | None:
    from .battle_person_six_stage_capture_12004 import normalize_person_six_stage_capture_12004

    try:
        capture = normalize_person_six_stage_capture_12004(value)
    except ValueError as error:
        raise ValueError(path + ": " + str(error)) from error
    lineage = row.get("preparation_stage_lineage")
    if capture is None or lineage is None:
        return capture
    for field, captured in (
        ("preparation_capture_observed", capture["capture_observed"]),
        ("preparation_capture_complete", capture["capture_complete"]),
        ("preparation_raw_counts_ready", capture["raw_counts_ready"]),
        ("preparation_capture_sequence", capture["capture_sequence"]),
        ("preparation_capture_thread_id", capture["capture_thread_id"]),
        ("preparation_completion_thread_id", capture["query_thread_id"]),
        ("preparation_character_identity", _identity(capture["character_identity"], path)),
        ("preparation_context_identity", _identity(capture["context_identity"], path)),
        ("preparation_source_return_rva", _identity(capture["source_return_rva"], path)),
        ("preparation_stage_observed_mask", sum(1 << stage["index"]
                                               for stage in capture["stages"] if stage["observed"])),
    ):
        if lineage[field] != captured:
            raise ValueError(path + " differs from the capture used by this Ci's lineage")
    preparation = capture.get("preparation_model")
    if preparation is not None:
        for field, captured in (
            ("preparation_model_identity", _identity(preparation["model_identity"], path)),
            ("preparation_owner_character_identity", _identity(preparation["owner_character_identity"], path)),
            ("preparation_owner_character_id", preparation["owner_character_id"]),
        ):
            if lineage[field] != captured:
                raise ValueError(path + " differs from this Ci's captured Model owner")
    if lineage["completed_preparation_lineage_proven"]:
        post = capture.get("post_six_aggregate")
        pc = row["consumed_pc"]
        if (not capture["configured"] or not capture["historical_capture"]
                or capture["character_id"] != row["selected_character_id"]
                or preparation is None or not preparation["observed"] or not preparation["ready"]
                or post is None or not post["observed"] or not post["pc"]["ready"]
                or _identity(post["pc"]["identity"], path) != pc["identity"]
                or post["pc"]["count_i32"] != pc["count_i32"]
                or post["pc"]["properties"] != pc["properties"]):
            raise ValueError(path + " completed proof lacks this Ci's exact owned post PC")
    return capture


def _natural_event(value: object, path: str) -> dict:
    raw = _dict(value, path, {"clock_identity", "sequence", "thread_id"})
    return {
        "clock_identity": _identity(raw["clock_identity"], path + ".clock_identity", optional=False),
        "sequence": _raw64(raw["sequence"], path + ".sequence", unsigned=True),
        "thread_id": _number(raw["thread_id"], path + ".thread_id", 32, unsigned=True),
    }


def _transfer_snapshot(value: object, path: str) -> dict:
    fields = _TRANSFER_SNAPSHOT_IDENTITIES | _TRANSFER_SNAPSHOT_IDS | _TRANSFER_SNAPSHOT_FLAGS
    raw = _dict(value, path, fields)
    result = {field: _identity(raw[field], path + "." + field)
              for field in _TRANSFER_SNAPSHOT_IDENTITIES}
    result.update({field: _number(raw[field], path + "." + field, 32, unsigned=True)
                   for field in _TRANSFER_SNAPSHOT_IDS})
    result.update({field: _boolean(raw[field], path + "." + field, optional=True)
                   for field in _TRANSFER_SNAPSHOT_FLAGS})
    return result


def _transfer_preparation(value: object, path: str) -> dict:
    fields = _TRANSFER_PREPARATION_IDENTITIES | {
        "observed", "preparation_capture_complete", "preparation_capture_sequence",
        "preparation_capture_thread_id", "preparation_completion_thread_id",
        "preparation_owner_character_id",
    }
    raw = _dict(value, path, fields)
    result = {field: _identity(raw[field], path + "." + field)
              for field in _TRANSFER_PREPARATION_IDENTITIES}
    result.update({field: _boolean(raw[field], path + "." + field)
                   for field in ("observed", "preparation_capture_complete")})
    result["preparation_capture_sequence"] = _raw64(
        raw["preparation_capture_sequence"], path + ".preparation_capture_sequence", unsigned=True)
    result.update({field: _number(raw[field], path + "." + field, 32, unsigned=True)
                   for field in ("preparation_capture_thread_id", "preparation_completion_thread_id",
                                 "preparation_owner_character_id")})
    return result


def _transfer_record(value: object, path: str) -> dict:
    raw = _dict(value, path, {"record_sequence", "offline_fixture", "stage"})
    fields = _TRANSFER_STAGE_FLAGS | _TRANSFER_UNPROVEN_FLAGS | {
        "observation_stage", "observed", "original_called", "original_returned", "reason",
        "model_a_identity", "model_b_identity", "original_return_rva",
        "before_event", "completed_event", "preparation", "before", "after",
    }
    source = _dict(raw["stage"], path + ".stage", fields)
    stage = {
        "observation_stage": _string(source["observation_stage"], path + ".stage.observation_stage"),
        "reason": _string(source["reason"], path + ".stage.reason"),
        "before_event": _natural_event(source["before_event"], path + ".stage.before_event"),
        "completed_event": _natural_event(source["completed_event"], path + ".stage.completed_event"),
        "preparation": _transfer_preparation(source["preparation"], path + ".stage.preparation"),
        "before": _transfer_snapshot(source["before"], path + ".stage.before"),
        "after": _transfer_snapshot(source["after"], path + ".stage.after"),
    }
    for field in ("model_a_identity", "model_b_identity", "original_return_rva"):
        stage[field] = _identity(source[field], path + ".stage." + field, optional=False)
    for field in _TRANSFER_STAGE_FLAGS | _TRANSFER_UNPROVEN_FLAGS | {
        "observed", "original_called", "original_returned",
    }:
        stage[field] = _boolean(source[field], path + ".stage." + field,
                                optional=field in _TRANSFER_STAGE_FLAGS)
    if (stage["observation_stage"] != "actual_paired_transfer_return"
            or any(stage[field] for field in _TRANSFER_UNPROVEN_FLAGS)):
        raise ValueError(path + " installed identity capture cannot grant whole postimages or Entry")
    return {
        "record_sequence": _raw64(raw["record_sequence"], path + ".record_sequence", unsigned=True),
        "offline_fixture": _boolean(raw["offline_fixture"], path + ".offline_fixture"),
        "stage": stage,
    }


def _transfer_capture_at_consumption(value: object, path: str) -> dict:
    fields = {
        "schema", "build_version", "executable_sha256", "historical_capture", "configured",
        "installed", "install_failure_flags", "request_filtered", "snapshot_revision", "observed_date_raw",
        "requested_receiver_count", "unresolved_receiver_count", "latest_record_sequence",
        "overwritten_records", "records",
    }
    raw = _dict(value, path, fields)
    if (raw["schema"] != _TRANSFER_CAPTURE_SCHEMA
            or require_exact_native_build(raw["build_version"], raw["executable_sha256"]) != CK3_12004):
        raise ValueError(path + " requires the exact owned actual4 installed-transfer capture")
    result = {field: _string(raw[field], path + "." + field)
              for field in ("schema", "build_version", "executable_sha256")}
    for field in ("historical_capture", "configured", "installed", "request_filtered"):
        result[field] = _boolean(raw[field], path + "." + field)
    for field in ("install_failure_flags", "requested_receiver_count", "unresolved_receiver_count"):
        result[field] = _integer(raw[field], path + "." + field, 32, unsigned=True)
    for field in ("latest_record_sequence", "overwritten_records"):
        result[field] = _raw64(raw[field], path + "." + field, unsigned=True)
    result["snapshot_revision"] = _raw64(
        raw["snapshot_revision"], path + ".snapshot_revision", unsigned=True, optional=True)
    result["observed_date_raw"] = _raw64(raw["observed_date_raw"], path + ".observed_date_raw", optional=True)
    records = _array(raw["records"], path + ".records")
    # These are defaults of the local single-record serialization envelope,
    # not the later query's installation status, counters or snapshot frame.
    if (not result["historical_capture"] or len(records) != 1
            or any(result[field] for field in (
                "configured", "installed", "request_filtered", "install_failure_flags",
                "requested_receiver_count", "unresolved_receiver_count", "latest_record_sequence",
                "overwritten_records"))
            or result["snapshot_revision"] is not None or result["observed_date_raw"] is not None):
        raise ValueError(path + " must preserve the before-getter owned single-record envelope")
    result["records"] = [_transfer_record(records[0], path + ".records[0]")]
    return result


def _installed_transfer_lineage(value: object, row: dict, path: str) -> dict | None:
    if value is None:
        return None
    optional = {"capture_at_consumption"} if isinstance(value, dict) and "capture_at_consumption" in value else set()
    raw = _dict(value, path, _TRANSFER_RELATIONSHIPS | optional | {
        "schema", "observation_stage", "getter_begin_event", "getter_completed_event",
        "installed_identity_associated", "reason",
    })
    if raw["schema"] != _TRANSFER_SCHEMA or raw["observation_stage"] != "actual_consumed_getter_return":
        raise ValueError(path + " requires the actual consumed getter transfer-lineage schema")
    result = {
        "schema": _TRANSFER_SCHEMA,
        "observation_stage": raw["observation_stage"],
        "getter_begin_event": _natural_event(raw["getter_begin_event"], path + ".getter_begin_event"),
        "getter_completed_event": _natural_event(raw["getter_completed_event"], path + ".getter_completed_event"),
        "installed_identity_associated": _boolean(raw["installed_identity_associated"], path + ".installed_identity_associated"),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }
    result.update({field: _boolean(raw[field], path + "." + field, optional=True)
                   for field in _TRANSFER_RELATIONSHIPS})
    if "capture_at_consumption" not in raw:
        if result["installed_identity_associated"] or any(
                result[field] is not None for field in _TRANSFER_RELATIONSHIPS):
            raise ValueError(path + " association lacks its before-getter owned transfer record")
        return result
    capture = _transfer_capture_at_consumption(raw["capture_at_consumption"], path + ".capture_at_consumption")
    result["capture_at_consumption"] = capture
    stage = capture["records"][0]["stage"]
    before, after = stage["before"], stage["after"]
    events = (stage["before_event"], stage["completed_event"],
              result["getter_begin_event"], result["getter_completed_event"])
    clock, thread = events[0]["clock_identity"], events[0]["thread_id"]
    ordered = (clock != 0 and thread not in (None, 0)
               and all(event["clock_identity"] == clock and event["thread_id"] == thread for event in events)
               and 0 < events[0]["sequence"] < events[1]["sequence"] < events[2]["sequence"] < events[3]["sequence"])
    selected, full_id = row["selected_character_identity"], row["selected_character_id"]
    owner_matches = (selected not in (None, 0) and full_id is not None
                     and selected == before["model_b_owner_identity"] == before["observed_owner_identity"]
                     == after["observed_owner_identity"] == after["installed_model_owner_identity"]
                     and full_id == before["model_b_owner_character_id"] == before["observed_owner_character_id"]
                     == after["observed_owner_character_id"])
    model, context = stage["model_a_identity"], row["context_identity"]
    context_matches = (model != 0 and context not in (None, 0)
                       and after["installed_model_identity"] == model
                       and after["installed_model_is_a"] is True
                       and after["installed_owner_matches_observed_owner"] is True
                       and selected not in (None, 0) and full_id is not None
                       and selected == after["installed_model_owner_identity"] == after["model_a_owner_identity"]
                       and full_id == after["model_a_owner_character_id"]
                       and context == model + 0x10 == after["matching_installed_inline_context_identity"])
    facts = dict(zip(("transfer_completed_before_getter", "selected_matches_transfer_owner",
                      "getter_matches_installed_context"), (ordered, owner_matches, context_matches)))
    if any(result[field] is True and not facts[field] for field in _TRANSFER_RELATIONSHIPS):
        raise ValueError(path + " relationship differs from this Ci's owned clock or receiver facts")
    if result["installed_identity_associated"] and (
            not all(result[field] is True for field in _TRANSFER_RELATIONSHIPS)
            or not stage["observed"] or not stage["original_called"] or not stage["original_returned"]
            or stage["original_return_rva"] != 0x2A3DC49
            or row["caller_return_rva"] != _CI_RETURN_RVAS[row["property_key"] - 0xC1]):
        raise ValueError(path + " association lacks an exact observed transfer and consumed callsite")
    return result


def _context(value: object, path: str) -> dict[str, object]:
    optional_fields = (set(value) & {"preparation_stage_lineage", "preparation_capture_at_consumption",
                                   "installed_transfer_lineage"}
                       if isinstance(value, dict) else set())
    raw = _dict(value, path, _CONTEXT_FIELDS | optional_fields)
    key = _integer(raw["property_key"], path + ".property_key", 16, unsigned=True)
    if not 0xC1 <= key <= 0xC9:
        raise ValueError(path + " property key is outside the nine actual knight Ci calls")
    result = {
        "property_key": key,
        "caller_return_rva": _raw64(raw["caller_return_rva"], path + ".caller_return_rva", unsigned=True),
        "selected_character_id": _number(raw["selected_character_id"], path + ".selected_character_id", 32, unsigned=True),
        "selected_character_identity": _identity(raw["selected_character_identity"], path + ".selected_character_identity"),
        "context_identity": _identity(raw["context_identity"], path + ".context_identity"),
        "operand_raw": _raw64(raw["operand_raw"], path + ".operand_raw", optional=True),
        "consumed_pc": _pc(raw["consumed_pc"], path + ".consumed_pc"),
        "preparation_capture_sequence": _raw64(raw["preparation_capture_sequence"], path + ".preparation_capture_sequence", unsigned=True, optional=True),
        "preparation_model_identity": _identity(raw["preparation_model_identity"], path + ".preparation_model_identity"),
        "preparation_context_identity": _identity(raw["preparation_context_identity"], path + ".preparation_context_identity"),
        "preparation_owner_character_id": _number(raw["preparation_owner_character_id"], path + ".preparation_owner_character_id", 32, unsigned=True),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }
    for field in ("context_matches_preparation", "owner_matches_preparation",
                  "pc_matches_preparation_post"):
        result[field] = _boolean(raw[field], path + "." + field, optional=True)
    for flag, left, right in (
        ("context_matches_preparation", "context_identity", "preparation_context_identity"),
        ("owner_matches_preparation", "selected_character_id", "preparation_owner_character_id"),
    ):
        if (result[flag] is not None and result[left] is not None and result[right] is not None
                and result[flag] != (result[left] == result[right])):
            raise ValueError(path + "." + flag + " disagrees with its observed identities")
    if "preparation_stage_lineage" in raw:
        result["preparation_stage_lineage"] = _preparation_stage_lineage(
            raw["preparation_stage_lineage"], result, path + ".preparation_stage_lineage")
    if "preparation_capture_at_consumption" in raw:
        result["preparation_capture_at_consumption"] = _capture_at_consumption(
            raw["preparation_capture_at_consumption"], result, path + ".preparation_capture_at_consumption")
    if "installed_transfer_lineage" in raw:
        result["installed_transfer_lineage"] = _installed_transfer_lineage(
            raw["installed_transfer_lineage"], result, path + ".installed_transfer_lineage")
    return result


def _output(value: object, path: str) -> dict[str, object]:
    raw = _dict(value, path, {"ready", "max_size", "reason", *_OUTPUT_RAW_FIELDS})
    result = {
        "ready": _boolean(raw["ready"], path + ".ready"),
        "max_size": _number(raw["max_size"], path + ".max_size", 32),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }
    for field in _OUTPUT_RAW_FIELDS:
        result[field] = _raw64(raw[field], path + "." + field, optional=True)
    if result["ready"] and any(result[field] is None for field in ("max_size", *_OUTPUT_RAW_FIELDS)):
        raise ValueError(path + " ready output lacks one of its six observed native fields")
    return result


def _physical_entry_writeback(value: object, path: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _dict(value, path, _WRITEBACK_FIELDS)
    matches = _array(raw["wrapper_output_field_matches"], path + ".wrapper_output_field_matches")
    if len(matches) != 6:
        raise ValueError(path + " must retain the six native output comparison slots")
    return {
        "writer_sequence": _raw64(raw["writer_sequence"], path + ".writer_sequence", unsigned=True),
        "entry_identity": _identity(raw["entry_identity"], path + ".entry_identity", optional=False),
        "province_identity": _identity(raw["province_identity"], path + ".province_identity", optional=False),
        "regiment_id": _number(raw["regiment_id"], path + ".regiment_id", 32, unsigned=True),
        "province_id": _number(raw["province_id"], path + ".province_id", 32),
        "original_return_value": _raw64(raw["original_return_value"], path + ".original_return_value", unsigned=True),
        "entry_cache": _output(raw["entry_cache"], path + ".entry_cache"),
        "output_cache_identity_matches_entry": _boolean(raw["output_cache_identity_matches_entry"], path + ".output_cache_identity_matches_entry"),
        "wrapper_output_comparison_ready": _boolean(raw["wrapper_output_comparison_ready"], path + ".wrapper_output_comparison_ready"),
        "wrapper_output_field_matches": [
            _boolean(match, f"{path}.wrapper_output_field_matches[{index}]", optional=True)
            for index, match in enumerate(matches)
        ],
        "wrapper_output_matches_entry_cache": _boolean(raw["wrapper_output_matches_entry_cache"], path + ".wrapper_output_matches_entry_cache", optional=True),
        "regiment_member_at_query": _boolean(raw["regiment_member_at_query"], path + ".regiment_member_at_query", optional=True),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }


def _event(value: object, path: str) -> dict[str, object]:
    optional_fields = ({"physical_entry_writeback"}
                       if isinstance(value, dict) and "physical_entry_writeback" in value else set())
    raw = _dict(value, path, _EVENT_FIELDS | optional_fields)
    result = {
        "sequence": _raw64(raw["sequence"], path + ".sequence", unsigned=True),
        "thread_id": _integer(raw["thread_id"], path + ".thread_id", 32, unsigned=True),
        "observed_date_raw": _number(raw["observed_date_raw"], path + ".observed_date_raw", 32),
        "wrapper_caller_return_rva": _raw64(raw["wrapper_caller_return_rva"], path + ".wrapper_caller_return_rva", unsigned=True, optional=True),
        "origin": _string(raw["origin"], path + ".origin"),
        "linked_character_id": _number(raw["linked_character_id"], path + ".linked_character_id", 32, unsigned=True),
        "linked_character_identity": _identity(raw["linked_character_identity"], path + ".linked_character_identity"),
        "output_cache_identity": _identity(raw["output_cache_identity"], path + ".output_cache_identity", optional=False),
        "native_return_identity": _identity(raw["native_return_identity"], path + ".native_return_identity"),
        "entry_association_proven": _boolean(raw["entry_association_proven"], path + ".entry_association_proven"),
        "capture_reason": _string(raw["capture_reason"], path + ".capture_reason", optional=True),
        "physical_entry_writeback": _physical_entry_writeback(
            raw.get("physical_entry_writeback"), path + ".physical_entry_writeback"),
    }
    if result["origin"] not in {"bridge_query_scratch", "native_wrapper_output_unclassified",
                                "native_physical_entry_writer"}:
        raise ValueError(path + " contains an unknown native output origin")
    if result["entry_association_proven"] and (
        result["origin"] != "native_physical_entry_writer"
        or result["physical_entry_writeback"] is None
    ):
        raise ValueError(path + " Entry association requires its observed physical writer sidecar")
    for field in ("regiment_id", "target_province_id", "linked_prowess_points",
                  "loaded_damage_multiplier", "loaded_toughness_multiplier"):
        result[field] = _number(raw[field], path + "." + field, 32)
    contexts = _array(raw["contexts"], path + ".contexts")
    if len(contexts) > 9:
        raise ValueError(path + " exceeds the nine actual knight Ci calls")
    result["contexts"] = [
        _context(context, f"{path}.contexts[{index}]")
        for index, context in enumerate(contexts)
    ]
    for index, row in enumerate(result["contexts"]):
        transfer = row.get("installed_transfer_lineage")
        if transfer is not None:
            for field in ("getter_begin_event", "getter_completed_event"):
                if transfer[field]["thread_id"] != result["thread_id"]:
                    raise ValueError(f"{path}.contexts[{index}].installed_transfer_lineage.{field}"
                                     + " differs from its actual wrapper thread")
        lineage = row.get("preparation_stage_lineage")
        if lineage is None:
            continue
        for field, event_field in (("linked_character_id", "linked_character_id"),
                                   ("linked_character_identity", "linked_character_identity"),
                                   ("consumption_thread_id", "thread_id")):
            if lineage[field] != result[event_field]:
                raise ValueError(f"{path}.contexts[{index}].preparation_stage_lineage.{field}"
                                 + " differs from its actual wrapper event")
    keys = [context["property_key"] for context in result["contexts"]]
    if any(left >= right for left, right in zip(keys, keys[1:])):
        raise ValueError(path + " changed native Ci call order or repeated a consumed property")
    result["observed_output"] = _output(raw["observed_output"], path + ".observed_output")
    return result


def normalize_knight_stat_consumption_12004(
    value: object, path: str = KNIGHT_STAT_CONSUMPTION_LEAF,
) -> dict[str, object] | None:
    """Keep captured truth and optional absence; do not infer gameplay readiness."""
    if value is None:
        return None
    raw = _dict(value, path, _QUERY_FIELDS)
    if raw["schema"] != SCHEMA:
        raise ValueError(path + " schema is not the actual4 knight consumption contract")
    if require_exact_native_build(raw["build_version"], raw["executable_sha256"]) != CK3_12004:
        raise ValueError(path + " requires the exact actual4 build identity")
    result = {
        "schema": SCHEMA,
        "build_version": _string(raw["build_version"], path + ".build_version"),
        "executable_sha256": _string(raw["executable_sha256"], path + ".executable_sha256"),
        "configured": _boolean(raw["configured"], path + ".configured"),
        "observer_installed": _boolean(raw["observer_installed"], path + ".observer_installed"),
        "reason": _string(raw["reason"], path + ".reason", optional=True),
    }
    for field in ("oldest_available_sequence", "latest_sequence", "overwritten_events"):
        result[field] = _raw64(raw[field], path + "." + field, unsigned=True)
    events = _array(raw["events"], path + ".events")
    if len(events) > _CAPACITY:
        raise ValueError(path + " events exceed the native owned ring capacity")
    result["events"] = [_event(event, f"{path}.events[{index}]")
                        for index, event in enumerate(events)]
    oldest, latest = result["oldest_available_sequence"], result["latest_sequence"]
    if oldest > latest:
        raise ValueError(path + " retained sequence bounds disagree")
    previous = 0
    for event in result["events"]:
        sequence = event["sequence"]
        if sequence <= previous or sequence < oldest or sequence > latest:
            raise ValueError(path + " event sequence disagrees with retained native order/bounds")
        previous = sequence
    return result
