"""Explicit, process-local research gate for the private AUTO Army scalar wire.

This control never submits a game action. A same-frame rich/private comparison
must complete before ``use`` can be selected; reconnecting or changing the
played actor/episode invalidates that comparison.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .driver import BridgeUnavailableError, UnsupportedStepError


CAPABILITY = "game.command.query-army-strengths-private-auto-scalar-v1"
Mode = Literal["off", "compare", "use"]


def _binding(snapshot: object) -> tuple[object, ...]:
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise BridgeUnavailableError("private Army scalar control needs a paused map frame")
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(actor, dict) or not isinstance(diagnostics, dict):
        raise BridgeUnavailableError("private Army scalar source identity is unavailable")
    character_id = actor.get("character_id")
    episode = snapshot.get("episode_run_id")
    pid = diagnostics.get("bridge_pid")
    generation = diagnostics.get("connection_generation")
    hello = diagnostics.get("hello")
    if (type(character_id) is not int or character_id <= 0 or actor.get("alive") is not True
            or not isinstance(episode, str) or not episode
            or type(pid) is not int or pid <= 0
            or type(generation) is not int or generation <= 0
            or not isinstance(hello, dict)):
        raise BridgeUnavailableError("private Army scalar source identity is incomplete")
    return (pid, generation, character_id, episode,
            hello.get("game_adapter_id"), hello.get("game_build"))


def _capability(snapshot: dict[str, object]) -> bool:
    diagnostics = snapshot["diagnostics"]
    hello = diagnostics["hello"]
    advertised = hello.get("capabilities")
    return isinstance(advertised, list) and CAPABILITY in advertised


def _current_frame(driver, expected_revision: int) -> tuple[dict[str, object], tuple[object, ...]]:
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    snapshot = driver.take_internal_semantic_snapshot()
    if snapshot.get("revision") != expected_revision:
        raise BridgeUnavailableError("private Army scalar control source revision changed")
    return snapshot, _binding(snapshot)


def _readback(driver, snapshot: dict[str, object], binding: tuple[object, ...]) -> dict[str, object]:
    with driver._driver_state_lock:
        mode = getattr(driver, "_army_private_scalar_ab_mode", "off")
        certificate = getattr(driver, "_army_private_scalar_ab_certificate", None)
    return {
        "status": "configured", "mode": mode,
        "comparison_verified_for_current_identity": certificate == binding,
        "native_capability_advertised": _capability(snapshot),
        "source_revision": snapshot["revision"],
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_native_revision": snapshot["native_revision"],
        "source_date_raw": snapshot["date_raw"],
        "game_pid": binding[0], "connection_generation": binding[1],
        "actor_character_id": binding[2], "episode_run_id": binding[3],
        "business_actions_submitted": 0,
    }


def set_control(driver, mode: str, *, expected_revision: int) -> dict[str, object]:
    if mode not in ("off", "compare", "use") or type(mode) is not str:
        raise ValueError("private Army scalar mode must be off, compare or use")
    snapshot, binding = _current_frame(driver, expected_revision)
    if mode != "off" and not _capability(snapshot):
        raise UnsupportedStepError("native private Army scalar capability is unavailable")
    with driver._driver_state_lock:
        certificate = getattr(driver, "_army_private_scalar_ab_certificate", None)
        armed = getattr(driver, "_army_private_scalar_ab_armed_binding", None)
        if mode == "use" and (certificate != binding or armed != binding):
            raise BridgeUnavailableError("same-identity rich/private Army comparison is required before use")
        driver._army_private_scalar_ab_mode = mode
        if mode != "use":
            driver._army_private_scalar_ab_certificate = None
            driver._army_private_scalar_ab_armed_binding = binding if mode == "compare" else None
    return _readback(driver, snapshot, binding)


def query_control(driver, *, expected_revision: int) -> dict[str, object]:
    snapshot, binding = _current_frame(driver, expected_revision)
    selected_mode(driver, snapshot)
    return _readback(driver, snapshot, binding)


def compare_control(driver, *, expected_revision: int) -> dict[str, object]:
    """Run both already guarded readonly Army queries before any AUTO turn."""
    snapshot, _ = _current_frame(driver, expected_revision)
    if selected_mode(driver, snapshot) != "compare":
        raise BridgeUnavailableError("private Army scalar comparison is not armed")
    result = driver.query_army_strengths(
        expected_revision=expected_revision, _auto_core_only=True,
    )
    status = query_control(driver, expected_revision=expected_revision)
    if status["comparison_verified_for_current_identity"] is not True:
        raise BridgeUnavailableError("private Army scalar comparison was not retained")
    return {"status": "same_frame_equal", "rich_result": result,
            "control": status, "business_actions_submitted": 0}


def selected_mode(driver, snapshot: dict[str, object]) -> str:
    """Cheap AUTO hot-path check; never assembles public capabilities."""
    with driver._driver_state_lock:
        mode = getattr(driver, "_army_private_scalar_ab_mode", "off")
        certificate = getattr(driver, "_army_private_scalar_ab_certificate", None)
        armed = getattr(driver, "_army_private_scalar_ab_armed_binding", None)
    if mode == "off":
        return "off"
    try:
        binding = _binding(snapshot)
        if not _capability(snapshot):
            raise BridgeUnavailableError("private Army scalar capability disappeared")
    except BridgeUnavailableError:
        disable(driver)
        return "off"
    if armed != binding or (mode == "use" and certificate != binding):
        disable(driver)
        return "off"
    return mode


def mark_compared(driver, snapshot: dict[str, object]) -> None:
    binding = _binding(snapshot)
    with driver._driver_state_lock:
        if (getattr(driver, "_army_private_scalar_ab_mode", "off") != "compare"
                or getattr(driver, "_army_private_scalar_ab_armed_binding", None) != binding):
            raise BridgeUnavailableError("private Army scalar comparison mode changed")
        driver._army_private_scalar_ab_certificate = binding


def disable(driver) -> None:
    with driver._driver_state_lock:
        driver._army_private_scalar_ab_mode = "off"
        driver._army_private_scalar_ab_certificate = None
        driver._army_private_scalar_ab_armed_binding = None


def register_tools(server, driver, read_only_tool) -> None:
    def ck3_set_army_private_auto_scalar_ab_v1(mode, expected_revision):
        method = getattr(driver, "set_army_private_auto_scalar_ab_v1", None)
        if not callable(method):
            raise UnsupportedStepError("Backend has no private Army scalar AB control")
        return method(mode, expected_revision=expected_revision)

    def ck3_query_army_private_auto_scalar_ab_v1(expected_revision):
        method = getattr(driver, "query_army_private_auto_scalar_ab_v1", None)
        if not callable(method):
            raise UnsupportedStepError("Backend has no private Army scalar AB control")
        return method(expected_revision=expected_revision)

    def ck3_compare_army_private_auto_scalar_ab_v1(expected_revision):
        if (not callable(getattr(driver, "query_army_strengths", None))
                or not callable(getattr(driver, "set_army_private_auto_scalar_ab_v1", None))):
            raise UnsupportedStepError("Backend has no private Army scalar comparison")
        return compare_control(driver, expected_revision=expected_revision)

    revision = Annotated[int, Field(strict=True, gt=0)]
    ck3_set_army_private_auto_scalar_ab_v1.__annotations__ = {
        "mode": Mode, "expected_revision": revision, "return": dict[str, object],
    }
    ck3_query_army_private_auto_scalar_ab_v1.__annotations__ = {
        "expected_revision": revision, "return": dict[str, object],
    }
    ck3_compare_army_private_auto_scalar_ab_v1.__annotations__ = {
        "expected_revision": revision, "return": dict[str, object],
    }
    server.tool()(ck3_set_army_private_auto_scalar_ab_v1)
    server.tool(annotations=read_only_tool)(ck3_query_army_private_auto_scalar_ab_v1)
    server.tool(annotations=read_only_tool)(ck3_compare_army_private_auto_scalar_ab_v1)
