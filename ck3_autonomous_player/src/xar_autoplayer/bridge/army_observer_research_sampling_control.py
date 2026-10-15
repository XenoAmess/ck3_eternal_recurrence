"""Explicit exact4 nine-family retained-observer capture controls.

Capture readiness is distinct from Army readiness and actual observed effects.
No ordinary/full Army query invokes these setters. No pending action is retried.
"""
from __future__ import annotations

from typing import Literal

FAMILIES = (
    "natural_phase", "regular_core", "daily_assault_preparation", "assault_placement",
    "assault_consumer", "assault_group_release", "gathering", "cleanup", "pre_date_prefix",
)
ObserverFamily = Literal[
    "all", "natural_phase", "regular_core", "daily_assault_preparation", "assault_placement",
    "assault_consumer", "assault_group_release", "gathering", "cleanup", "pre_date_prefix",
]
ENABLE_STEP = "enable-army-observer-research-sampling-v1"
DISABLE_STEP = "disable-army-observer-research-sampling-v1"
QUERY_STEP = "query-army-observer-research-sampling-v1"
STATE_KEY = "army_observer_research_sampling_v1"
ARMY_CAPABILITY = "game.command.query-army-strengths-v1"
_STEPS = {ENABLE_STEP, DISABLE_STEP, QUERY_STEP}
_ROW_KEYS = {
    "installed", "available", "capture_enabled", "busy", "clear_completed", "epoch",
    "active_captures", "retained_records", "qualified_records", "status", "readiness",
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def selected_families(observer_family: object) -> tuple[str, ...]:
    require(type(observer_family) is str and observer_family in ("all", *FAMILIES),
            "unknown Army observer sampling family")
    return FAMILIES if observer_family == "all" else (observer_family,)


def normalize_result(payload: object, *, expected_step: str,
                      observer_family: str, allow_scoped_enable_refusal: bool = False) -> dict[str, object]:
    """Check the actual native control receipt without manufacturing a sample."""
    selected = selected_families(observer_family)
    require(type(expected_step) is str and expected_step in _STEPS, "unknown Army observer sampling step")
    require(type(payload) is dict and set(payload) == {
        "step", "accepted", "status", STATE_KEY, "backend_id",
    }, "malformed Army observer sampling envelope")
    require(payload["step"] == expected_step and payload["backend_id"] == "native-headless" and
            type(payload["accepted"]) is bool and type(payload["status"]) is str and
            payload["status"] in {"completed", "incomplete"},
            "malformed Army observer sampling status")
    rows = payload[STATE_KEY]
    require(type(rows) is dict and set(rows) == set(selected), "selected Army observer families differ")
    output = {}
    all_satisfied = True
    for family in selected:
        row = rows[family]
        require(type(row) is dict and set(row) == _ROW_KEYS, "malformed Army observer family row")
        for key in ("installed", "available", "capture_enabled", "busy", "clear_completed"):
            require(type(row[key]) is bool, "Army observer " + key + " must be boolean")
        for key in ("epoch", "active_captures", "retained_records", "qualified_records"):
            require(type(row[key]) is int and 0 <= row[key] <= 2**64 - 1,
                    "Army observer " + key + " must be uint64")
        require(row["qualified_records"] <= row["retained_records"], "qualified Army observations exceed retained")
        require(row["busy"] is (row["active_captures"] > 0), "Army observer busy contradicts active captures")
        require(not row["clear_completed"] or (
            not row["capture_enabled"] and not row["busy"] and row["retained_records"] == 0
        ), "Army observer clear_completed contradicts retained state")
        available = row["installed"] and row["available"]
        status = ("unavailable" if not available else "enabled" if row["capture_enabled"] else
                  "busy" if row["busy"] else "disabled" if row["clear_completed"] else "clear_pending")
        readiness = ("unavailable" if not available else "off" if not row["capture_enabled"] else
                     "inflight" if row["busy"] else "awaiting_sample" if row["qualified_records"] == 0 else
                     "retained_observation")
        require(type(row["status"]) is str and row["status"] == status, "Army observer row status contradicts state")
        require(type(row["readiness"]) is str and row["readiness"] == readiness,
                "Army observer readiness contradicts actual retained state")
        if expected_step == ENABLE_STEP:
            all_satisfied = all_satisfied and available and row["capture_enabled"]
        elif expected_step == DISABLE_STEP:
            all_satisfied = all_satisfied and available and not row["capture_enabled"] and not row["busy"] and row["clear_completed"]
        # A legal query is accepted even if a selected observer is unavailable.
        output[family] = dict(row)
    refused_scope = (allow_scoped_enable_refusal is True and expected_step == ENABLE_STEP and
                     observer_family == "regular_core" and payload["accepted"] is False)
    require(payload["accepted"] is bool(all_satisfied) or refused_scope,
            "aggregate Army observer accepted contradicts actual states")
    require(payload["status"] == ("completed" if payload["accepted"] else "incomplete"),
            "aggregate Army observer status contradicts accepted")
    return {**payload, STATE_KEY: output}


def normalize_regular_core_subject_ids(value: object, *, step: str,
                                       observer_family: str) -> list[int] | None:
    if value is None:
        return None
    require(step == ENABLE_STEP and observer_family == "regular_core",
            "regular_core_full_carmy_ids requires enabling only regular_core")
    require(type(value) is list and 1 <= len(value) <= 64,
            "regular_core_full_carmy_ids must contain 1..64 full CArmy IDs")
    require(all(type(item) is int and -(2**31) <= item <= 2**31 - 1 and item != -1
                for item in value), "regular_core_full_carmy_ids must be signed32 IDs excluding -1")
    require(len(set(value)) == len(value), "regular_core_full_carmy_ids must be unique")
    return list(value)


def execute_control(driver, *, step: str, observer_family: str,
                    expected_revision: int,
                    regular_core_full_carmy_ids: list[int] | None = None) -> dict[str, object]:
    """Use the existing exact4 primitive; outer owner still grants runtime scope."""
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.native_driver import (
        PreSubmissionRevisionMismatchError, UnsupportedStepError, _same_paused_native_frame,
    )
    from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build

    selected_families(observer_family)
    require(type(step) is str and step in _STEPS, "unknown Army observer sampling step")
    scope = normalize_regular_core_subject_ids(regular_core_full_carmy_ids,
                                             step=step, observer_family=observer_family)
    request_fields: dict[str, object] = {"observer_family": observer_family}
    if scope is not None:
        request_fields["regular_core_full_carmy_ids"] = scope
    require(type(expected_revision) is int and expected_revision > 0, "positive public sampling revision required")
    starting = driver.take_internal_semantic_snapshot()
    actor = starting.get("played_character") or {}
    require(starting.get("paused") is True and starting.get("map_ready") is True and
            actor.get("alive") is True and type(actor.get("character_id")) is int and actor["character_id"] > 0,
            "Army observer sampling needs actual paused living map player")
    if starting.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("Army observer sampling source revision is stale")
    diagnostics = starting.get("diagnostics") or {}
    hello = diagnostics.get("hello") or {}
    try:
        build = require_exact_native_build(
            hello.get("expected_ck3_version", hello.get("game_version")),
            hello.get("expected_ck3_sha256", hello.get("executable_sha256")),
        )
        require(build == CK3_12004, "Army observer controls require exact .4")
    except ValueError as error:
        raise BridgeUnavailableError("Army observer sampling requires the frozen exact .4 build") from error
    if ARMY_CAPABILITY not in driver.state.capabilities().get("bridge_capabilities", ()):
        raise UnsupportedStepError("Native does not advertise the Army query capability")
    try:
        raw = driver._execute_primitive_step(
            step, expected_revision=expected_revision,
            required_capability=ARMY_CAPABILITY,
            request_fields=request_fields,
            include_native_command_history=False, internal_semantic_snapshot=True,
        )
        try:
            result = normalize_result(raw, expected_step=step, observer_family=observer_family,
                                      allow_scoped_enable_refusal=scope is not None)
        except ValueError as error:
            raise BridgeUnavailableError("Malformed Army observer sampling receipt: " + str(error)) from error
        current = driver.take_internal_semantic_snapshot()
        current_diagnostics = current.get("diagnostics") or {}
        current_actor = current.get("played_character") or {}
        if (not _same_paused_native_frame(starting, current) or
                current.get("revision") != starting.get("revision") or
                current.get("date_raw") != starting.get("date_raw") or
                current_actor.get("character_id") != actor["character_id"] or
                current_actor.get("alive") is not True or current.get("map_ready") is not True or
                current_diagnostics.get("bridge_pid") != diagnostics.get("bridge_pid")):
            raise BridgeUnavailableError("Army observer sampling crossed its paused player frame")
        result = {
            **result, "observer_family": observer_family,
            "queried_snapshot_id": starting.get("snapshot_id"),
            "queried_revision": starting.get("revision"),
            "queried_native_revision": starting.get("native_revision"),
            "queried_date_raw": starting.get("date_raw"),
            "queried_connection_generation": diagnostics.get("connection_generation"),
            "queried_episode_run_id": starting.get("episode_run_id"),
            "queried_player_character_id": actor["character_id"],
        }
    except Exception as error:
        driver._record_command(step, ok=False, result=None, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if step != QUERY_STEP:
            # A set may already have altered a gate/epoch even if its result is
            # incomplete or lost. Do not reuse the old Army cache afterward.
            with driver._driver_state_lock:
                driver._army_strength_query = None
    driver._record_command(step, ok=result["accepted"], result=result)
    return result


def set_control(driver, enabled: bool, *, observer_family: str, expected_revision: int,
                regular_core_full_carmy_ids: list[int] | None = None):
    require(type(enabled) is bool, "Army observer enabled must be explicit boolean")
    return execute_control(driver, step=ENABLE_STEP if enabled else DISABLE_STEP,
                           observer_family=observer_family, expected_revision=expected_revision,
                           regular_core_full_carmy_ids=regular_core_full_carmy_ids)


def query_control(driver, *, observer_family: str, expected_revision: int):
    return execute_control(driver, step=QUERY_STEP, observer_family=observer_family,
                           expected_revision=expected_revision)


def register_tools(server, driver, read_only_tool) -> None:
    """Register the explicit controls; no generic executor or automatic gate."""
    from typing import Annotated
    from pydantic import Field
    from xar_autoplayer.bridge.driver import UnsupportedStepError

    def ck3_set_army_observer_research_sampling_v1(enabled, observer_family, expected_revision,
                                                 regular_core_full_carmy_ids=None):
        method = getattr(driver, "set_army_observer_research_sampling_v1", None)
        if not callable(method):
            raise UnsupportedStepError("Backend has no Army observer sampling controls")
        kwargs = dict(observer_family=observer_family, expected_revision=expected_revision)
        if regular_core_full_carmy_ids is not None:
            kwargs["regular_core_full_carmy_ids"] = regular_core_full_carmy_ids
        return method(enabled, **kwargs)

    def ck3_query_army_observer_research_sampling_v1(observer_family, expected_revision):
        method = getattr(driver, "query_army_observer_research_sampling_v1", None)
        if not callable(method):
            raise UnsupportedStepError("Backend has no Army observer sampling controls")
        return method(observer_family=observer_family, expected_revision=expected_revision)

    revision = Annotated[int, Field(strict=True, gt=0)]
    full_carmy_id = Annotated[int, Field(strict=True, ge=-(2**31), le=2**31 - 1)]
    subject_ids = Annotated[list[full_carmy_id], Field(strict=True, min_length=1, max_length=64)]
    ck3_set_army_observer_research_sampling_v1.__annotations__ = {
        "enabled": Annotated[bool, Field(strict=True)], "observer_family": ObserverFamily,
        "expected_revision": revision, "regular_core_full_carmy_ids": subject_ids | None,
        "return": dict[str, object],
    }
    ck3_query_army_observer_research_sampling_v1.__annotations__ = {
        "observer_family": ObserverFamily, "expected_revision": revision, "return": dict[str, object],
    }
    server.tool()(ck3_set_army_observer_research_sampling_v1)
    server.tool(annotations=read_only_tool)(ck3_query_army_observer_research_sampling_v1)
