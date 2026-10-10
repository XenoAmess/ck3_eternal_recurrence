"""Pure conditional projection of supplied actual4 compiled-effect inputs.

This module reads no native state and runs no effect. Its input is supplied by
the same-query producer; an available projection proves argument arithmetic,
not that the conditional call happened or that any history changed.
"""
from __future__ import annotations

from collections.abc import Mapping

INPUT_SCHEMA = "xar.army-compiled-effect-context-supplied/1"
INPUT_BASIS = "same_query_conditional_supplied"
ROUTES = {
    0x2639CA4: (0x2639C9F, "army_1d8_at_call_plus_40", 0x40),
    0x24DD7B6: (0x24DD7B1, "army_1d8_saved_at_24dd657_plus_230", 0x230),
}


def _integer(value: object, bits: int, signed: bool = False) -> bool:
    low = -(1 << (bits - 1)) if signed else 0
    high = (1 << (bits - int(signed))) - 1
    return type(value) is int and low <= value <= high


def compiled_effect_seed_12004(seed_i32: int) -> int:
    """Actual 37652B0 nonnegative branch; every operation wraps to U32."""
    if not _integer(seed_i32, 32, True) or seed_i32 < 0:
        raise ValueError("Nonnegative native I32 context seed required")
    mask = 0xFFFFFFFF
    value = (0x5EA6BA9F - seed_i32 * 0x4AD685B3) & mask
    value = ((value ^ (value >> 8)) + 0x68E31DA4) & mask
    value = (value ^ ((value << 8) & mask)) & mask
    value = (value * 0x1B56C4E9) & mask
    value ^= value >> 8
    value = (value * 0x92D68CA2) & mask
    return value ^ (value >> 8)


def project_army_compiled_effect_context_12004(supplied: Mapping | None) -> dict:
    """Keep missing fields unknown; never backfill from a different query."""
    result = {
        "projection_kind": "army_compiled_effect_context_12004",
        "status": "unavailable",
        "input_basis": INPUT_BASIS,
        "binding": None,
        "wrapper_rva": "0x3765760",
        "seed_constructor_rva": "0x37652B0",
        "dispatcher_rva": "0x3765E50",
        "route": None,
        "caller_return_rva": None,
        "conditional_receiver": None,
        "conditional_scope": {},
        "conditional_dispatch_context": {
            "root_alias": "supplied_caller_context",
            "actor_alias": None,
            "third_alias": "supplied_caller_context",
            "environment": "wrapper_owned_support118",
            "flag_u8": None,
            "rng_object": "wrapper_owned_seed_pair",
        },
        "seed_branch": "unknown",
        "conditional_rng_seed_u32": None,
        "conditional_rng_counter_u32": None,
        "argument_projection_ready": False,
        "missing_inputs": [],
        "unavailable_reason": "same_query_compiled_effect_inputs_absent",
        "actual_invocation_observed": False,
        "history_append_observed": False,
        "callee_effects_ready": False,
        "direct_receiver_store_in_wrapper": False,
        "full_daily_ready": False,
        "full_monthly_ready": False,
        "native_calls_executed": 0,
        "native_writes_executed": 0,
    }
    if supplied is None:
        return result
    if (not isinstance(supplied, Mapping)
            or supplied.get("schema") != INPUT_SCHEMA
            or supplied.get("input_basis") != INPUT_BASIS):
        result["unavailable_reason"] = "supplied_input_schema_or_basis_invalid"
        return result
    binding = supplied.get("binding")
    if (not isinstance(binding, Mapping)
            or not isinstance(binding.get("snapshot_id"), str)
            or not binding["snapshot_id"]
            or not _integer(binding.get("revision"), 64)
            or not _integer(binding.get("native_revision"), 64)):
        result["unavailable_reason"] = "same_query_binding_unavailable"
        return result
    result["binding"] = {
        key: binding[key] for key in ("snapshot_id", "revision", "native_revision")
    }
    missing = []
    return_rva = supplied.get("caller_return_rva")
    route = ROUTES.get(return_rva) if _integer(return_rva, 32) else None
    if route is None:
        missing.append("caller_return_rva")
    else:
        call, basis, offset = route
        result["caller_return_rva"] = return_rva
        result["route"] = {
            "callsite_rva": call,
            "receiver_basis": basis,
            "definition_member_offset": offset,
            "call_occurrence_claimed": False,
        }
    for key in ("compiled_receiver_token", "caller_context_token"):
        value = supplied.get(key)
        if not _integer(value, 64) or value == 0:
            missing.append(key)
    if "compiled_receiver_token" not in missing:
        result["conditional_receiver"] = {
            "compiled_receiver_token": supplied["compiled_receiver_token"],
            "typed_receiver_basis": "actual_caller_embedded_compiled_effect_receiver",
        }
    widths = (("scope_kind_u16", 16, False),
              ("scope_payload_u64", 64, False),
              ("scope_seed_i32", 32, True))
    scope = result["conditional_scope"]
    for key, bits, signed in widths:
        value = supplied.get(key)
        if not _integer(value, bits, signed):
            missing.append(key)
            scope[key] = None
        else:
            scope[key] = value
    if scope["scope_kind_u16"] is not None and scope["scope_kind_u16"] != 27:
        missing.append("scope_kind_u16_must_match_actual_army_kind27")
    if (scope["scope_payload_u64"] is not None
            and (scope["scope_payload_u64"] > 0xFFFFFFFF
                 or scope["scope_payload_u64"] == 0xFFFFFFFF)):
        missing.append("scope_payload_u64_must_be_valid_zero_extended_army_full_id")
    flag = supplied.get("evaluation_flag_u8")
    if not _integer(flag, 8):
        missing.append("evaluation_flag_u8")
    else:
        result["conditional_dispatch_context"]["flag_u8"] = flag
    seed = scope["scope_seed_i32"]
    if seed is not None:
        if seed >= 0:
            result["seed_branch"] = "nonnegative_context_seed"
            result["conditional_rng_seed_u32"] = compiled_effect_seed_12004(seed)
            result["conditional_rng_counter_u32"] = 0
        else:
            result["seed_branch"] = "negative_context_seed_native_fallback"
            missing.extend(("actual_393ee20_fallback_seed",
                            "actual_effect_key_registry_branch_and_37651f0_effects"))
    result["missing_inputs"] = missing
    result["argument_projection_ready"] = not missing
    result["status"] = "partial" if missing else "available"
    result["unavailable_reason"] = "conditional_input_partial" if missing else None
    return result
