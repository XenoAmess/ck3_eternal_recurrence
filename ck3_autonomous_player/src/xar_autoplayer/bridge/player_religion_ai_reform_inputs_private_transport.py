"""Read all actual played-actor AI contexts and native schedule inputs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, require_exact_native_backend

STEP = "query-player-religion-ai-reform-inputs-v1"
DOMAIN_KEY = "player_religion_ai_reform_inputs_v1"
SCHEMA = "ck3_12002_player_religion_ai_reform_inputs_v1"
PERMISSION = "allow_private_player_religion_ai_reform_inputs_query"
_CONTEXT_STATUSES = {"bindings_unavailable", "actor_unavailable", "container_unavailable",
                     "observed_no_ai", "observed_controllers"}
_KEYS = {"schema", "available", "unavailable_reason", "capture_epoch", "date_raw",
         "played_character_id", "context_status", "controller_count", "gate_inputs_observation_complete",
         "controller_absence", "context", "schedule_base", "controllers"}


def _mapping(value: object, keys: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native AI reform inputs schema is malformed: {field}")
    return value


def _integer(value: object, low: int, high: int, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native AI reform inputs integer is malformed: {field}")


def _boolean(value: object, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not bool:
        raise ValueError(f"native AI reform inputs bool is malformed: {field}")


def _controller(value: object, *, with_schedule: bool) -> None:
    keys = {"kind", "active_raw", "special_raw"}
    if with_schedule:
        keys |= {"context_index", "schedule"}
    row = _mapping(value, keys, "controller")
    if row["kind"] not in {"ordinary", "player_special"}:
        raise ValueError("native AI reform controller kind is malformed")
    for key in ("active_raw", "special_raw"):
        _integer(row[key], 0, 255, key)
    if with_schedule:
        _integer(row["context_index"], 0, 0xFFFFFFFF, "context_index")
        _schedule(row["schedule"])


def _schedule(value: object) -> None:
    row = _mapping(value, {"status", "ai_status", "current_actor", "native_globals",
                           "actual_ai_cache", "actual_ai_timer"}, "schedule")
    if row["status"] not in {"bindings_unavailable", "actor_unavailable", "configuration_unavailable", "observed"}:
        raise ValueError("native AI schedule status is malformed")
    if row["ai_status"] not in {"not_supplied", "actor_mismatch", "invalid_state", "gates_only", "observed"}:
        raise ValueError("native AI schedule context status is malformed")
    actor = _mapping(row["current_actor"], {"actor_id", "highest_tier", "current_independent_ruler"}, "current_actor")
    _integer(actor["actor_id"], 0, 0xFFFFFFFF, "actor_id", nullable=True)
    _integer(actor["highest_tier"], -(1 << 31), (1 << 31) - 1, "highest_tier", nullable=True)
    _boolean(actor["current_independent_ruler"], "current_independent_ruler", nullable=True)
    globals_row = _mapping(row["native_globals"], {"reformation_enabled", "rare_period_prepare_ticks"}, "native_globals")
    _boolean(globals_row["reformation_enabled"], "reformation_enabled", nullable=True)
    _integer(globals_row["rare_period_prepare_ticks"], -(1 << 31), (1 << 31) - 1, "rare_period_prepare_ticks", nullable=True)
    cache = _mapping(row["actual_ai_cache"], {"available", "ai_government_flags", "ai_independent_flags",
        "ai_active_raw", "ai_special_raw", "cached_independent_ruler", "cached_government_bit6",
        "handler_cache_gates_pass"}, "actual_ai_cache")
    _boolean(cache["available"], "cache.available")
    _integer(cache["ai_government_flags"], 0, 65535, "ai_government_flags", nullable=True)
    for key in ("ai_independent_flags", "ai_active_raw", "ai_special_raw"):
        _integer(cache[key], 0, 255, key, nullable=True)
    for key in ("cached_independent_ruler", "cached_government_bit6", "handler_cache_gates_pass"):
        _boolean(cache[key], key, nullable=True)
    timer = _mapping(row["actual_ai_timer"], {"available", "rare_countdown_prepare_ticks", "rare_selected_raw", "units"}, "actual_ai_timer")
    _boolean(timer["available"], "timer.available")
    _integer(timer["rare_countdown_prepare_ticks"], -(1 << 31), (1 << 31) - 1, "rare_countdown_prepare_ticks", nullable=True)
    _integer(timer["rare_selected_raw"], 0, 255, "rare_selected_raw", nullable=True)
    if timer["units"] != "prepare_invocations":
        raise ValueError("native AI timer units are malformed")


def normalize_player_religion_ai_reform_inputs_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve known absence, every controller, actual false/zero and nulls."""
    row = _mapping(value, _KEYS, "observation")
    if row["schema"] != SCHEMA or row["context_status"] not in _CONTEXT_STATUSES:
        raise ValueError("native player AI reform inputs schema/status is malformed")
    for key in ("available", "gate_inputs_observation_complete"):
        _boolean(row[key], key)
    _integer(row["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(row["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(row["played_character_id"], -(1 << 31), (1 << 31) - 1, "played_character_id")
    _integer(row["controller_count"], 0, 0xFFFFFFFF, "controller_count", nullable=True)
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or actor.get("character_id") != row["played_character_id"]
            or snapshot.get("date_raw") != row["date_raw"]):
        raise ValueError("native AI reform inputs differ from their queried frame")
    if row["available"]:
        if row["unavailable_reason"] is not None:
            raise ValueError("available native AI reform inputs contain an unavailable reason")
    elif not isinstance(row["unavailable_reason"], str) or not row["unavailable_reason"]:
        raise ValueError("unavailable native AI reform inputs lost their reason")
    if row["controller_absence"] not in {None, "no_actual_controller"}:
        raise ValueError("native AI controller absence is malformed")
    context = _mapping(row["context"], {"schema", "status", "available", "actor_id", "actual_holder_count", "controllers"}, "context")
    if context["schema"] != "ck3_12002_reform_ai_context_v1" or context["status"] != row["context_status"]:
        raise ValueError("native AI context schema/status is malformed")
    _boolean(context["available"], "context.available")
    _integer(context["actor_id"], 0, 0xFFFFFFFF, "context.actor_id", nullable=True)
    _integer(context["actual_holder_count"], 0, (1 << 31) - 1, "actual_holder_count")
    if not isinstance(context["controllers"], list):
        raise ValueError("native AI context controllers are malformed")
    for controller in context["controllers"]:
        _controller(controller, with_schedule=False)
    _schedule(row["schedule_base"])
    if row["controllers"] is not None:
        if not isinstance(row["controllers"], list):
            raise ValueError("native AI controller schedules are malformed")
        for controller in row["controllers"]:
            _controller(controller, with_schedule=True)
    return deepcopy(row)


def query_player_religion_ai_reform_inputs_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-ai-reform-inputs-v1")
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native AI reform inputs envelope differs from the queried build/frame")
        value = normalize_player_religion_ai_reform_inputs_v1(result.get("player_religion_ai_reform_inputs"), snapshot=before)
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native AI reform inputs envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
