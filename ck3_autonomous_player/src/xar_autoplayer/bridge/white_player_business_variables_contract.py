"""Decode fixed current-player White variables; preserve absence and Q100000 types.

This observes character variables, independently of GUI visibility. It does not
observe rendered text, button.down, a price scriptvalue or UI acceptance.
"""
from __future__ import annotations

from copy import deepcopy

from .ingame_decisions_open_contract import opening_binding

STEP = "query-white-player-business-variables-v1"
CAPABILITY = "game.command.query-white-player-business-variables-v1"
SCHEMA = "ck3-native-white-player-business-variables-v1"
FIXED_SCALE = 100000
VARIABLE_KEYS = (
    "ervc_cc_female", "ervc_cc_age", "ervc_cc_diplomacy", "ervc_cc_martial",
    "ervc_cc_stewardship", "ervc_cc_intrigue", "ervc_cc_learning", "ervc_cc_prowess",
)
_PROOFS = (
    "owner_thread_verified", "frame_verified", "source_abi_pins_verified",
    "player_scope_verified", "stable_two_pass_values",
)
_UNSUPPORTED = (
    "rendered_text_available", "selected_down_available", "scriptvalue_price_available",
)
_NUMBERS = {
    "game_pid": (1, 2**32 - 1), "native_revision": (1, 2**64 - 1),
    "connection_generation": (1, 2**64 - 1),
    "played_character_id": (-1, 2**31 - 1), "date_raw": (-2**31, 2**31 - 1),
    "application_thread_id": (0, 2**32 - 1), "application_pump_epoch": (0, 2**64 - 1),
    "application_tls_context": (0, 2**64 - 1), "variable_context": (0, 2**64 - 1),
    "character_address": (0, 2**64 - 1),
}
_WIRE_KEYS = {
    "schema", "step", "available", "all_eight_numeric_integers", "fields",
    "fixed_scale", "status", "unavailable_reason", *_PROOFS, *_UNSUPPORTED, *_NUMBERS,
}
_FIELD_KEYS = {"present", "actual_kind", "actual_payload", "fixed_raw", "integer_value"}


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"invalid actual White {name}")
    return value


def business_binding(snapshot: object) -> dict[str, object]:
    """Require actual .3 paused/alive/no-event provenance, never a script actor ID."""
    binding = opening_binding(snapshot)
    if "active_event" not in snapshot or snapshot["active_event"] is not None:
        raise ValueError("White business query requires actual no-event snapshot")
    if not isinstance(binding["episode_run_id"], str) or not binding["episode_run_id"]:
        raise ValueError("White business query requires actual episode identity")
    for name in ("game_pid", "native_revision", "connection_generation", "played_character_id", "date_raw"):
        minimum, maximum = _NUMBERS[name]
        if name == "played_character_id": minimum = 1
        _integer(binding[name], name, minimum, maximum)
    return binding


def normalize_white_player_business_variables(raw: object, binding: dict[str, object]) -> dict[str, object]:
    """Validate the actual native DTO without assigning defaults or GUI credit."""
    if not isinstance(raw, dict) or set(raw) not in (_WIRE_KEYS, _WIRE_KEYS | {"backend_id"}):
        raise ValueError("malformed fixed White business variable DTO")
    if raw.get("backend_id", "native-headless") != "native-headless":
        raise ValueError("White business variables require native backend")
    if raw["schema"] != SCHEMA or raw["step"] != STEP:
        raise ValueError("wrong native White business schema/step")
    for name in ("available", "all_eight_numeric_integers", *_PROOFS, *_UNSUPPORTED):
        if type(raw[name]) is not bool:
            raise ValueError(f"White business lacks actual boolean {name}")
    if any(raw[name] for name in _UNSUPPORTED):
        raise ValueError("variable observation cannot grant text/down/price availability")
    if type(raw["fixed_scale"]) is not int or raw["fixed_scale"] != FIXED_SCALE:
        raise ValueError("White business variable scale is not Q100000")
    for name, (minimum, maximum) in _NUMBERS.items():
        _integer(raw[name], name, minimum, maximum)
    for name in ("native_revision", "connection_generation", "game_pid"):
        if raw[name] != binding[name]:
            raise ValueError(f"native White business changed {name}")
    fields = raw["fields"]
    if not isinstance(fields, dict) or set(fields) != set(VARIABLE_KEYS):
        raise ValueError("White business DTO must contain exactly eight fixed keys")
    for name in VARIABLE_KEYS:
        field = fields[name]
        if not isinstance(field, dict) or set(field) != _FIELD_KEYS or type(field["present"]) is not bool:
            raise ValueError(f"malformed actual White variable {name}")
        if not field["present"]:
            if any(field[key] is not None for key in _FIELD_KEYS - {"present"}):
                raise ValueError(f"absent White variable {name} carries a value")
            continue
        kind = _integer(field["actual_kind"], name + ".actual_kind", 0, 2**16 - 1)
        payload = _integer(field["actual_payload"], name + ".actual_payload", -2**63, 2**63 - 1)
        if kind != 1:
            if field["fixed_raw"] is not None or field["integer_value"] is not None:
                raise ValueError(f"nonnumeric White variable {name} has numeric projection")
        else:
            fixed = _integer(field["fixed_raw"], name + ".fixed_raw", -2**63, 2**63 - 1)
            if fixed != payload:
                raise ValueError(f"White variable {name} fixed payload disagrees")
            expected = payload // FIXED_SCALE if payload % FIXED_SCALE == 0 else None
            value = field["integer_value"]
            if (expected is None and value is not None) or (expected is not None and
                    (_integer(value, name + ".integer_value", -2**63, 2**63 - 1) != expected)):
                raise ValueError(f"White variable {name} integer encoding disagrees")
    if raw["available"]:
        if any(raw[name] is not True for name in _PROOFS):
            raise ValueError("available White business values lack owner/ABI/scope/two-pass/frame proof")
        for name in ("played_character_id", "date_raw"):
            if raw[name] != binding[name]:
                raise ValueError(f"native White business changed {name}")
        for name in ("application_thread_id", "application_pump_epoch", "application_tls_context",
                     "variable_context", "character_address"):
            if raw[name] == 0:
                raise ValueError(f"available White business values lack actual {name}")
        if raw["status"] != "observed_business_variables" or raw["unavailable_reason"] != "":
            raise ValueError("available White business status is inconsistent")
        all_integers = all(field["present"] and field["integer_value"] is not None for field in fields.values())
        if raw["all_eight_numeric_integers"] != all_integers:
            raise ValueError("White all-eight numeric integer qualification is inconsistent")
    else:
        if (raw["status"] != "unavailable" or not isinstance(raw["unavailable_reason"], str)
                or not raw["unavailable_reason"] or raw["all_eight_numeric_integers"]
                or any(field["present"] for field in fields.values())):
            raise ValueError("unavailable White observation leaks values or lacks actual refusal")
        if raw["played_character_id"] not in (-1, binding["played_character_id"]) or raw["date_raw"] not in (0, binding["date_raw"]):
            raise ValueError("unavailable White observation crossed actor/date binding")
    return deepcopy(raw)
