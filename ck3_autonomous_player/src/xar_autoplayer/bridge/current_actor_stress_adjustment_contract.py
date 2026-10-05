"""Read the current actor's native stress adjustment without applying it.

The aggregate modifiers are additive Q100000 values. The loss aggregate omits
additional stress-level terms, whereas adjusted_delta_points is the actual
native adjuster's return. Neither is an event-option cost or an after-stress
prediction; callers must bind and observe a separate real event outcome.
"""
from __future__ import annotations

from copy import deepcopy

from .ingame_decisions_open_contract import EXE_SHA256, opening_binding

STEP = "query-current-actor-stress-adjustment-v1"
CAPABILITY = "game.query.current-actor-stress-adjustment.v1"
SCHEMA = "ck3-current-actor-stress-adjustment-v1"
PROOFS = (
    "source_code_pins_verified", "actor_binding_verified", "owner_thread_verified",
    "tls_verified", "frame_verified",
)
NUMBERS = (
    "current_stress_points", "stress_gain_modifier_raw", "stress_loss_modifier_raw",
    "adjusted_delta_points",
)
ENVELOPE_KEYS = {
    "step", "accepted", "status", "read_only", "query_sequence", "snapshot_revision",
    "date_raw", "game_pid", "connection_generation", "current_actor_stress_adjustment",
    "backend_id",
}
PUBLIC_KEYS = {
    *ENVELOPE_KEYS, "queried_snapshot_id", "queried_revision", "queried_native_revision",
    "current_actor_stress_adjustment_ready",
}
PAYLOAD_KEYS = {
    "schema", "status", "source", "read_only", "exact_build", "executable_sha256",
    "snapshot_revision", "date_raw", "game_pid", "connection_generation", "player_character_id",
    "base_amount", *NUMBERS, "modifier_scale", "modifier_semantics",
    "stress_gain_consumer_index", "stress_loss_consumer_index", "native_aggregator_getter_rva",
    "native_modifier_reader_rva", "native_adjuster_rva", *PROOFS,
    "owner_thread_id", "owner_pump_epoch", "unavailable_reason",
    "final_after_stress_prediction_ready", "option_cost_binding_ready",
    "business_postcondition_verified",
}


def _integer(value: object, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def validate_base_amount(value: object) -> int:
    return _integer(value, -300, 300, "base_amount")


def stress_query_binding(snapshot: object, expected_revision: object) -> dict[str, object]:
    revision = _integer(expected_revision, 0, 2**64 - 1, "expected_revision")
    binding = opening_binding(snapshot)
    if (snapshot.get("revision") != revision or type(snapshot.get("revision")) is not int
            or snapshot.get("diagnostics", {}).get("connected") is not True
            or snapshot.get("one_life_terminal_reason") is not None):
        raise ValueError("stress query requires the current connected public revision")
    _integer(binding["native_revision"], 1, 2**64 - 1, "native_revision")
    _integer(binding["connection_generation"], 1, 2**64 - 1, "connection_generation")
    _integer(binding["game_pid"], 1, 2**32 - 1, "game_pid")
    _integer(binding["played_character_id"], 1, 2**31 - 1, "played_character_id")
    _integer(binding["date_raw"], -(2**31), 2**31 - 1, "date_raw")
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("stress query lacks an actual snapshot identity")
    stress = snapshot.get("played_character", {}).get("stress_points")
    if stress is not None:
        _integer(stress, 0, 2**31 - 1, "snapshot stress_points")
    return {**binding, "revision": revision, "snapshot_id": snapshot_id,
            "observed_stress_points": stress}


def same_stress_query_frame(before: dict[str, object], after: object,
                            binding: dict[str, object]) -> bool:
    try:
        later = stress_query_binding(after, binding["revision"])
    except (ValueError, TypeError, AttributeError):
        return False
    fields = ("speed", "paused", "map_ready", "local_player_id", "episode_character_id",
              "played_character", "active_event", "pending_character_interaction")
    return later == binding and all(after.get(key) == before.get(key) for key in fields)


def normalize_native_stress_query(raw: object, binding: dict[str, object],
                                  base_amount: int) -> dict[str, object]:
    validate_base_amount(base_amount)
    if (not isinstance(raw, dict) or set(raw) != ENVELOPE_KEYS
            or raw.get("step") != STEP or raw.get("accepted") is not True
            or raw.get("read_only") is not True or raw.get("backend_id") != "native-headless"
            or raw.get("status") not in {"available", "unavailable"}):
        raise ValueError("malformed native stress-query envelope")
    _integer(raw.get("query_sequence"), 1, 2**64 - 1, "query_sequence")
    for key, expected in (
        ("snapshot_revision", binding["native_revision"]), ("date_raw", binding["date_raw"]),
        ("game_pid", binding["game_pid"]), ("connection_generation", binding["connection_generation"]),
    ):
        if type(raw.get(key)) is not int or raw[key] != expected:
            raise ValueError(f"stress-query envelope {key} changed")
    value = raw.get("current_actor_stress_adjustment")
    if not isinstance(value, dict) or set(value) != PAYLOAD_KEYS:
        raise ValueError("malformed native stress-adjustment payload")
    constants = {
        "schema": SCHEMA, "source": "native_current_actor_stress_consumer_1.20.0.3",
        "read_only": True, "exact_build": "1.20.0.3", "status": raw["status"],
        "modifier_scale": 100000, "modifier_semantics": "additive_increment",
        "stress_gain_consumer_index": 143, "stress_loss_consumer_index": 144,
        "native_aggregator_getter_rva": "0x28C3AE0", "native_modifier_reader_rva": "0x2303700",
        "native_adjuster_rva": "0x28BC800", "base_amount": base_amount,
        "snapshot_revision": binding["native_revision"], "date_raw": binding["date_raw"],
        "game_pid": binding["game_pid"], "connection_generation": binding["connection_generation"],
        "player_character_id": binding["played_character_id"],
        "final_after_stress_prediction_ready": False, "option_cost_binding_ready": False,
        "business_postcondition_verified": False,
    }
    for key, expected in constants.items():
        if type(value.get(key)) is not type(expected) or value[key] != expected:
            raise ValueError(f"native stress-adjustment {key} is mismatched")
    if (not isinstance(value.get("executable_sha256"), str)
            or value["executable_sha256"].lower() != EXE_SHA256):
        raise ValueError("native stress-adjustment exact image is mismatched")
    for key in PROOFS:
        if type(value.get(key)) is not bool:
            raise ValueError(f"native stress-adjustment proof {key} is malformed")
    minimum = 1 if raw["status"] == "available" else 0
    _integer(value.get("owner_thread_id"), minimum, 2**32 - 1, "owner_thread_id")
    _integer(value.get("owner_pump_epoch"), minimum, 2**64 - 1, "owner_pump_epoch")
    if raw["status"] == "available":
        if value.get("unavailable_reason") is not None or any(value[key] is not True for key in PROOFS):
            raise ValueError("available native stress-adjustment lacks actual proofs")
        _integer(value["current_stress_points"], 0, 2**31 - 1, "current_stress_points")
        if (binding["observed_stress_points"] is not None
                and value["current_stress_points"] != binding["observed_stress_points"]):
            raise ValueError("native stress read disagrees with its actual snapshot")
        _integer(value["adjusted_delta_points"], -(2**31), 2**31 - 1, "adjusted_delta_points")
        for key in ("stress_gain_modifier_raw", "stress_loss_modifier_raw"):
            _integer(value[key], -(2**63), 2**63 - 1, key)
    elif (any(value[key] is not None for key in NUMBERS)
          or not isinstance(value.get("unavailable_reason"), str)
          or not 1 <= len(value["unavailable_reason"]) <= 512):
        raise ValueError("unavailable native stress-adjustment must preserve all-null values and reason")
    return deepcopy(raw)


def project_stress_query(raw: object, binding: dict[str, object], base_amount: int) -> dict[str, object]:
    result = normalize_native_stress_query(raw, binding, base_amount)
    return {**result, "queried_snapshot_id": binding["snapshot_id"],
            "queried_revision": binding["revision"], "queried_native_revision": binding["native_revision"],
            "current_actor_stress_adjustment_ready": result["status"] == "available"}


def normalize_public_stress_query(raw: object, binding: dict[str, object], base_amount: int) -> dict[str, object]:
    if not isinstance(raw, dict) or set(raw) != PUBLIC_KEYS:
        raise ValueError("malformed public stress-query result")
    native = normalize_native_stress_query({key: raw[key] for key in ENVELOPE_KEYS}, binding, base_amount)
    expected = project_stress_query(native, binding, base_amount)
    for key in PUBLIC_KEYS - ENVELOPE_KEYS:
        if type(raw.get(key)) is not type(expected[key]) or raw[key] != expected[key]:
            raise ValueError(f"public stress-query binding {key} changed")
    return deepcopy(raw)
