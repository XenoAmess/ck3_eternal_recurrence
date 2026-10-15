"""Pure watched-stop checks shared by offline replay and staged Root helpers.

No transport or game operations. The production clock functions are compiled
from their pinned definitions; importing the Windows Driver is unnecessary.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace


class StopEvidenceError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise StopEvidenceError(message)


def status_query_arguments():
    """Readonly status can itself publish a revision; never pin an earlier one."""
    return {"step": "research-query-tactical-daily-sentinel-v1", "expected_revision": None}


def paused_after_advancement(snapshot, starting_date_raw):
    """A still-paused pre-Resume publication does not complete a watched stop."""
    date = snapshot.get("date_raw")
    return (snapshot.get("paused") is True and type(date) is int
            and type(starting_date_raw) is int and date > starting_date_raw)


def same_stopped_army(original, fresh, army_id):
    """Refresh only the readonly publication while preserving the stopped Army."""
    require(original.get("date_raw") == fresh.get("date_raw"), "stopped date changed")
    require(fresh.get("paused") is True and fresh.get("map_ready") is True,
            "fresh stop is not a paused map")
    rows = [[a for a in s.get("player_armies", []) if a.get("army_id") == army_id]
            for s in (original, fresh)]
    require(all(len(r) == 1 for r in rows), "stopped Army absent or ambiguous")
    fields = ("army_id", "owner_character_id", "controllable", "current_province_id",
              "route_province_ids", "route_read_status", "route_source_count", "in_combat", "retreating")
    require(all(rows[0][0].get(k) == rows[1][0].get(k) for k in fields), "stopped Army changed")


def production_clock(path: Path, expected_sha256: str):
    """Use exact existing production definitions in a bounded, speed-3 namespace.

    Only the four pure validators and their literal reason table are compiled.
    The Driver's exception class is mapped to this tool's ValueError subclass;
    no accepted result changes. Readiness at speeds4/5 is outside this adapter.
    """
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, "production clock source pin changed")
    source = raw.decode("utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    names = {"_normalize_tactical_daily_sentinel_status", "_validate_tactical_daily_sentinel_arm",
             "_validate_tactical_daily_sentinel_stop", "_noncombat_sentinel_scope_speed_live_ready"}
    selected = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node); found.add(node.name)
        if isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id == "_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS" for n in node.targets):
            ast.literal_eval(node.value)
            selected.append(node); found.add("_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS")
    require(found == names | {"_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS"}, "production pure clock definitions missing")
    namespace = {"copy": copy, "BridgeUnavailableError": StopEvidenceError, "_BATTLE_SPEED_READINESS": {}}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    pins = {getattr(node, "name", "_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS"):
            hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest() for node in selected}
    return SimpleNamespace(**{name: namespace[name] for name in names}), pins


def check_clock(native, *, before, after, arm_body, status_body, watch_army_id, speed=3):
    """Reuse production Arm/stop validation without inventing one-day receipts."""
    require(speed == 3, "only recorded committed-route speed3 is supported")
    require(native._noncombat_sentinel_scope_speed_live_ready("committed_route", speed), "scope speed readiness closed")
    require(before.get("paused") is True and after.get("paused") is True
            and before.get("map_ready") is True and after.get("map_ready") is True, "paused map boundaries missing")
    require(before.get("episode_run_id") == after.get("episode_run_id"), "episode changed")
    actors = [s.get("played_character") or {} for s in (before, after)]
    require(actors[0].get("character_id") == actors[1].get("character_id")
            and all(a.get("alive") is True for a in actors), "living actor changed")
    for key in ("bridge_pid", "connection_generation"):
        require(before.get("diagnostics", {}).get(key) == after.get("diagnostics", {}).get(key), "process boundary changed")
    require(not after.get("active_event") and not after.get("pending_character_interaction"), "unhandled modal boundary")
    start = before["date_raw"]; end = after["date_raw"]
    require(paused_after_advancement(after, start), "pre-advance paused poll is not completion")
    arm = native._normalize_tactical_daily_sentinel_status(arm_body["tactical_daily_sentinel"])
    stop = native._normalize_tactical_daily_sentinel_status(status_body["tactical_daily_sentinel"])
    target = arm["target_date_raw"]
    native._validate_tactical_daily_sentinel_arm(arm_body, arm, arm_step=arm_body["step"],
        starting_date_raw=start, target_date_raw=target, speed=speed, mode="terminal_or_sentinel",
        watch_army_ids=(watch_army_id,), sentinel_scope="committed_route")
    native._validate_tactical_daily_sentinel_stop(stop, arm_status=arm, starting_date_raw=start,
        target_date_raw=target, ending_date_raw=end, elapsed_days=(end-start)//24, speed=speed,
        mode="terminal_or_sentinel", watch_army_ids=(watch_army_id,))
    require(set(stop["trigger_reasons"]) <= {"date_deadline", "army_position_changed", "route_target_changed"},
            "unexpected combat/modal/identity reason")
    return {"state": stop["state"], "generation": stop["generation"], "starting_date_raw": start,
            "actual_ending_date_raw": end, "declared_deadline_date_raw": target,
            "completed_daily_ticks": stop["completed_daily_ticks"], "trigger_reasons": stop["trigger_reasons"],
            "one_day_sampling_claim": False, "actual_arrival_requires_independent_card_frames": True}
