"""Strict optional copied context from the natural actual4 callback/writer seam."""
from __future__ import annotations

_INVOCATION_KEYS = {"invocation_token", "native_thread_id", "nesting_depth",
    "parent_invocation_token", "callback_caller_return_rva", "callback_entry_rva", "receiver_basis"}
_WRITER_KEYS = {"invocation", "army_id", "native_carmy_id", "passed_date_raw64",
    "stock_at_writer_entry_raw", "stock_scale", "receiver_identity_matches", "capture_failure_flags"}


def _integer(value, name, bits=64, unsigned=False, optional=False):
    if optional and value is None:
        return None
    low = 0 if unsigned else -(1 << (bits-1))
    high = (1 << bits)-1 if unsigned else (1 << (bits-1))-1
    if type(value) is not int or not low <= value <= high:
        raise ValueError(name + " has invalid integer width/type")
    return value


def normalize_supply_parent_invocation_v1(value, name="supply_parent_invocation_v1"):
    if not isinstance(value, dict) or set(value) != _INVOCATION_KEYS:
        raise ValueError(name + " has malformed invocation schema")
    out = {key: _integer(value[key], name+"."+key, bits=32 if key in {
        "native_thread_id", "nesting_depth"} else 64, unsigned=True,
        optional=key in {"parent_invocation_token", "callback_caller_return_rva"})
        for key in _INVOCATION_KEYS-{"receiver_basis", "callback_entry_rva"}}
    if (out["invocation_token"] == 0 or out["native_thread_id"] == 0
            or out["nesting_depth"] == 0 or out["parent_invocation_token"] == 0
            or (out["nesting_depth"] == 1) != (out["parent_invocation_token"] is None)
            or out["parent_invocation_token"] == out["invocation_token"]
            or value["callback_entry_rva"] != 0x24E3410
            or type(value["callback_entry_rva"]) is not int
            or value["receiver_basis"] != "actual_24E3410_rcx_carmy"):
        raise ValueError(name + " has invalid source/identity/depth")
    out.update(callback_entry_rva=0x24E3410,receiver_basis=value["receiver_basis"])
    return out


def normalize_supply_parent_writer_context_v1(value, name="supply_parent_context_v1"):
    if not isinstance(value, dict) or set(value) != _WRITER_KEYS:
        raise ValueError(name + " has malformed writer context schema")
    if type(value["receiver_identity_matches"]) is not bool:
        raise ValueError(name + ".receiver_identity_matches must be bool")
    if type(value["stock_scale"]) is not int or value["stock_scale"] != 100000:
        raise ValueError(name + ".stock_scale must be exactly 100000")
    return {
        "invocation": normalize_supply_parent_invocation_v1(value["invocation"],name+".invocation"),
        "army_id": _integer(value["army_id"],name+".army_id",bits=32,optional=True),
        "native_carmy_id": _integer(value["native_carmy_id"],name+".native_carmy_id",bits=32,optional=True),
        "passed_date_raw64": _integer(value["passed_date_raw64"],name+".passed_date_raw64",unsigned=True,optional=True),
        "stock_at_writer_entry_raw": _integer(value["stock_at_writer_entry_raw"],name+".stock_at_writer_entry_raw",optional=True),
        "stock_scale":100000,"receiver_identity_matches":value["receiver_identity_matches"],
        "capture_failure_flags":_integer(value["capture_failure_flags"],name+".capture_failure_flags",bits=32,unsigned=True),
    }
