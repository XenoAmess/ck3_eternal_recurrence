"""Disabled H3937 target-siege reads after the same-session local collector.

This is a research receipt, not a route, move, combat or date selector. The
caller owns the managed session and its outer source/cleanup proof.
"""

from __future__ import annotations

import copy

from .bridge.native_driver import (
    _canonical_remaining_route,
    _canonical_timed_route,
    _route_contact_hostile_ids,
)
from .bridge.war_contract import (
    QUERY_ARMY_STRENGTHS_STEP,
    army_strength_query_status,
    army_strength_scope,
    normalize_army_strengths,
    normalize_province_local_siege_result,
    normalize_route_contact_horizon,
    preview_move_army_step,
    query_province_local_siege_step,
    query_route_contact_horizon_step,
)
from .errors import AgentError
from .h3937_combined_readonly_queries import (
    ReadOnlyService,
    _complete_published_scope,
    _exact_appended_query,
    collect_h3937_combined_reads_in_session,
)
from .h3937_paused_war_scope_run import (
    ARMY_ID, EXPECTED_DATE_RAW, EXPECTED_EPISODE_RUN_ID, TARGET_PROVINCE_ID,
)
from .h3937_stationary_route_contact_query_run import _same_frame
from .strategy import _primary_defender_siege_relief_assessment


H3937_TARGET_LIVE_AUTHORIZED = False


def _bound_strength_read(
    before: dict[str, object], after: dict[str, object], result: object,
) -> bool:
    if not isinstance(result, dict):
        return False
    try:
        rows = normalize_army_strengths(
            result.get("army_strengths"),
            expected_scope=army_strength_scope(before),
        )
    except (TypeError, ValueError):
        return False
    return bool(
        result.get("step") == QUERY_ARMY_STRENGTHS_STEP
        and result.get("accepted") is True
        and result.get("backend_id") == "native-headless"
        and result.get("status") == "available"
        and army_strength_query_status(rows) == "available"
        and type(result.get("query_sequence")) is int
        and result["query_sequence"] > 0
        and result.get("queried_snapshot_id") == before.get("snapshot_id")
        and result.get("queried_revision") == before.get("revision")
        and result.get("queried_native_revision") == before.get("native_revision")
        and after.get("army_strengths_status") == "available"
        and after.get("army_strengths") == rows
        and after.get("army_strengths_query_sequence") == result["query_sequence"]
        and after.get("army_strengths_queried_snapshot_id") == before.get("snapshot_id")
        and after.get("army_strengths_queried_revision") == before.get("revision")
    )


def _current_siege_target(frame: dict[str, object]) -> dict[str, object] | None:
    players = frame.get("player_armies")
    wars = frame.get("active_wars")
    history = frame.get("native_command_history")
    if not (isinstance(players, list) and isinstance(wars, list)
            and len(wars) == 1 and isinstance(wars[0], dict)
            and isinstance(history, list)):
        return None
    subject = next((row for row in players if isinstance(row, dict)
                    and row.get("army_id") == ARMY_ID), None)
    if not isinstance(subject, dict):
        return None
    selected = _primary_defender_siege_relief_assessment(
        frame, commands=history, active_wars=wars,
        controlled_armies=[subject], pursuit_army=subject,
    )
    target = selected.get("target_province_id")
    enemy_id = selected.get("enemy_army_id")
    if not (selected.get("status") == "forecast_required"
            and type(target) is int and target > 0
            and target != TARGET_PROVINCE_ID
            and type(enemy_id) is int and enemy_id > 0
            and selected.get("army_id") == ARMY_ID):
        return None
    return selected


def _bound_preview(
    frame: dict[str, object], result: object, step: str,
    target: int,
) -> list[int] | None:
    if not isinstance(result, dict):
        return None
    diagnostics = frame.get("diagnostics")
    generation = (diagnostics.get("connection_generation")
                  if isinstance(diagnostics, dict) else None)
    preview = result.get("route_preview")
    subject = next((row for row in frame.get("player_armies", [])
                    if isinstance(row, dict) and row.get("army_id") == ARMY_ID), None)
    if not (result.get("step") == step
            and result.get("accepted") is True
            and result.get("status") == "available"
            and result.get("backend_id") == "native-headless"
            and result.get("queried_snapshot_id") == frame.get("snapshot_id")
            and result.get("queried_revision") == frame.get("revision")
            and result.get("queried_native_revision") == frame.get("native_revision")
            and type(generation) is int and generation > 0
            and result.get("queried_connection_generation") == generation
            and result.get("queried_episode_run_id") == EXPECTED_EPISODE_RUN_ID
            and isinstance(subject, dict) and isinstance(preview, dict)
            and preview.get("status") == "available"
            and preview.get("army_id") == ARMY_ID
            and preview.get("origin_province_id") == subject.get("current_province_id")
            and preview.get("target_province_id") == target
            and preview.get("previewed_date_raw") == EXPECTED_DATE_RAW):
        return None
    raw_route = preview.get("route_province_ids")
    if not isinstance(raw_route, list):
        return None
    route = list(raw_route)
    if route and route[0] == subject["current_province_id"]:
        route = route[1:]
    if not route or route[-1] != target or any(
        type(province) is not int or province <= 0 for province in route
    ):
        return None
    return route


def _bound_target_contact(
    frame: dict[str, object], result: object, step: str,
    target: int, hostiles: tuple[int, ...], preview_route: list[int],
) -> bool:
    if not isinstance(result, dict):
        return False
    diagnostics = frame.get("diagnostics")
    generation = (diagnostics.get("connection_generation")
                  if isinstance(diagnostics, dict) else None)
    if not (result.get("step") == step
            and result.get("accepted") is True
            and result.get("status") == "available"
            and result.get("backend_id") == "native-headless"
            and type(result.get("query_sequence")) is int
            and result["query_sequence"] > 0
            and result.get("snapshot_revision") == frame.get("native_revision")
            and result.get("queried_snapshot_id") == frame.get("snapshot_id")
            and result.get("queried_revision") == frame.get("revision")
            and result.get("queried_native_revision") == frame.get("native_revision")
            and type(generation) is int and generation > 0
            and result.get("queried_connection_generation") == generation
            and result.get("queried_episode_run_id") == EXPECTED_EPISODE_RUN_ID):
        return False
    try:
        horizon = normalize_route_contact_horizon(
            result.get("route_contact_horizon"),
            expected_subject_army_id=ARMY_ID,
            expected_target_province_id=target,
            expected_hostile_army_ids=hostiles,
            expected_date_raw=EXPECTED_DATE_RAW,
            expected_snapshot_revision=int(frame["native_revision"]),
        )
    except (TypeError, ValueError):
        return False
    subject = next((row for row in frame.get("player_armies", [])
                    if isinstance(row, dict) and row.get("army_id") == ARMY_ID), None)
    wars = frame.get("active_wars")
    enemies = (wars[0].get("enemy_armies") if isinstance(wars, list)
               and len(wars) == 1 and isinstance(wars[0], dict) else None)
    if not isinstance(subject, dict) or not isinstance(enemies, list):
        return False
    hostile_rows = {row.get("army_id"): row for row in enemies
                    if isinstance(row, dict) and row.get("army_id") in hostiles}
    if len(hostile_rows) != len(hostiles):
        return False
    subject_timed = horizon["subject_route"]
    if (subject_timed["current_province_id"] != subject.get("current_province_id")
            or _canonical_timed_route(subject_timed) != preview_route):
        return False
    for army_id, timed in zip(hostiles, horizon["hostile_routes"]):
        published = hostile_rows[army_id]
        if (timed["current_province_id"] != published.get("current_province_id")
                or _canonical_timed_route(timed)
                != _canonical_remaining_route(published)):
            return False
    inventory = result.get("physical_army_inventory_check")
    return bool(inventory is None or (
        isinstance(inventory, dict) and inventory.get("valid") is True
        and inventory.get("date_or_action_authorized") is False
    ))


def collect_h3937_target_reads_in_session(
    service: ReadOnlyService,
) -> dict[str, object]:
    """Read strength, dynamic siege Province, preview and contact; never act."""
    if H3937_TARGET_LIVE_AUTHORIZED is not True:
        raise AgentError("H3937 target read-only collector has no live authorization")
    combined = collect_h3937_combined_reads_in_session(service)
    frames = copy.deepcopy(combined.get("frames", []))
    envelopes = copy.deepcopy(combined.get("envelopes", []))
    steps = list(combined.get("steps", []))
    checks: dict[str, bool] = {"combined_inner_observed": combined.get("observed") is True}
    selected: dict[str, object] | None = None
    route: list[int] | None = None
    error: str | None = None
    try:
        if not checks["combined_inner_observed"] or len(frames) != 3:
            raise AgentError("H3937 local combined read is incomplete")
        current = frames[-1]
        if not isinstance(current, dict):
            raise AgentError("H3937 combined final frame is malformed")
        reobserved = service.snapshot()
        checks["combined_final_snapshot_reobserved"] = (
            isinstance(reobserved, dict) and reobserved == current)
        if not checks["combined_final_snapshot_reobserved"]:
            raise AgentError("H3937 combined final frame changed before target reads")
        current = reobserved
        scope = _complete_published_scope(current)
        if scope is None or scope != combined.get("scope"):
            raise AgentError("H3937 published war scope changed")

        def read(step: str) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
            nonlocal current
            before = current
            steps.append(step)
            result = service.execute_step(step, expected_revision=int(before["revision"]))
            envelopes.append(copy.deepcopy(result))
            after = service.snapshot()
            frames.append(copy.deepcopy(after))
            checks[f"{step}:same_frame"] = _same_frame(before, after)
            checks[f"{step}:scope"] = _complete_published_scope(after) == scope
            checks[f"{step}:history"] = _exact_appended_query(before, after, step, result)
            if not all(checks.values()):
                raise AgentError(f"H3937 {step} changed frame, scope or history")
            current = after
            return before, result, after

        before, strengths, after = read(QUERY_ARMY_STRENGTHS_STEP)
        checks["strengths_same_frame_cache"] = _bound_strength_read(before, after, strengths)
        if not checks["strengths_same_frame_cache"]:
            raise AgentError("H3937 same-frame full published strength is unavailable")
        selected = _current_siege_target(current)
        checks["dynamic_siege_target"] = selected is not None
        if selected is None:
            raise AgentError("H3937 current war has no eligible siege target")
        target = int(selected["target_province_id"])
        province_step = query_province_local_siege_step(target)
        before, province, _ = read(province_step)
        normalized_province = normalize_province_local_siege_result(
            province, expected_step=province_step,
            expected_province_id=target,
            expected_snapshot_revision=int(before["native_revision"]),
            expected_date_raw=EXPECTED_DATE_RAW,
        )
        checks["target_province_available"] = normalized_province["status"] == "available"
        if not checks["target_province_available"]:
            raise AgentError("H3937 target Province siege read is partial")
        preview_step = preview_move_army_step(ARMY_ID, target)
        before, preview, _ = read(preview_step)
        route = _bound_preview(before, preview, preview_step, target)
        checks["full_target_preview_bound"] = route is not None
        if route is None:
            raise AgentError("H3937 target route preview is unavailable")
        hostiles = _route_contact_hostile_ids(current)
        checks["target_hostiles_match_published_scope"] = (
            list(hostiles) == scope["query_eligible_hostile_army_ids"])
        if not checks["target_hostiles_match_published_scope"]:
            raise AgentError("H3937 target hostile roster changed")
        contact_step = query_route_contact_horizon_step(ARMY_ID, target, hostiles)
        before, contact, _ = read(contact_step)
        checks["target_contact_bound"] = _bound_target_contact(
            before, contact, contact_step, target, hostiles, route)
        if not checks["target_contact_bound"]:
            raise AgentError("H3937 target route-contact read is incomplete")
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    observed = error is None and all(checks.values())
    return {
        "schema": "xar.ck3.h3937-target-readonly-inner-v1",
        "observed": observed,
        "status": "READ_ONLY_TARGET_OBSERVED" if observed else "RED",
        "combined": combined,
        "selected_siege": selected,
        "target_route_province_ids": route,
        "frames": frames,
        "envelopes": envelopes,
        "steps": steps,
        "query_attempts": len(steps),
        "checks": checks,
        "error": error,
        "outer_session_cleanup_verified": False,
        "physical_army_inventory_completeness_proven": False,
        "first_hop_contact_observed": False,
        "participant_scope_proven": False,
        "forecast_qualified": False,
        "action_authorized": False,
        "date_advance_authorized": False,
        "gameplay_actions": 0,
    }
