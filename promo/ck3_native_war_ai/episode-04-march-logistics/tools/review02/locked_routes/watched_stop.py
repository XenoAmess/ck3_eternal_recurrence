"""Pure watched-stop checks shared by offline replay and staged Root helpers.

No transport or game operations. The production clock functions are compiled
from their pinned definitions; importing the Windows Driver is unnecessary.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile


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


def _production_source(path: Path, expected_sha256: str):
    """Select historical bytes by the archive's whole-file SHA, never by date."""
    current = path.read_bytes()
    current_sha = hashlib.sha256(current).hexdigest()
    relative = Path("docs/ck3-native-ai/evidence/episode04-locked-route-clock-source-12004/SOURCE-INDEX.json")
    for root in Path(__file__).resolve().parents:
        manifest_path = root/relative
        if not manifest_path.is_file():
            continue
        manifest_raw = manifest_path.read_bytes()
        require(len(manifest_raw) <= 16384, "frozen production source index exceeds bound")
        manifest = json.loads(manifest_raw)
        require(manifest.get("schema") == "episode04.locked-route.frozen-production-source.v1", "frozen production source index schema differs")
        entry = manifest.get("sources", {}).get(expected_sha256)
        if entry is None:
            break
        ref = entry["artifact"]
        require(Path(ref["path"]).name == ref["path"] and ref["member"] == "native_driver.py", "frozen source must be the named local artifact")
        artifact_path = manifest_path.parent/ref["path"]
        require(artifact_path.stat().st_size == ref["bytes"] and ref["bytes"] <= 1024*1024, "frozen source archive size differs")
        artifact = artifact_path.read_bytes()
        require(hashlib.sha256(artifact).hexdigest() == ref["sha256"], "frozen source archive SHA differs")
        with zipfile.ZipFile(io.BytesIO(artifact)) as archive:
            require(archive.namelist() == [ref["member"]], "frozen source archive membership differs")
            info = archive.getinfo(ref["member"])
            require(info.file_size == entry["source_bytes"] and info.file_size <= 4*1024*1024, "frozen production source size differs")
            raw = archive.read(ref["member"])
        require(hashlib.sha256(raw).hexdigest() == expected_sha256, "frozen production source pin changed")
        return raw, str(relative.parent/ref["path"])+"!"+ref["member"], {
            "selection": "archived_whole_file_sha256", "source_commit": entry["source_commit"],
            "source_path": entry["source_path"], "source_sha256": expected_sha256,
            "source_bytes": len(raw), "artifact": {"path": str(relative.parent/ref["path"]), **{key:ref[key] for key in ("bytes","sha256","member")}},
            "current_repository_source_sha256": current_sha,
            "current_repository_source_matches_archive": current_sha == expected_sha256,
            "historical_source_reinterpreted_with_current_code": False,
        }
    require(current_sha == expected_sha256, "production clock source pin changed and no exact frozen source is available")
    return current, str(path), {"selection": "current_exact_whole_file_sha256", "source_commit": None,
        "source_sha256": expected_sha256, "current_repository_source_sha256": current_sha,
        "current_repository_source_matches_archive": True, "historical_source_reinterpreted_with_current_code": False}


def production_clock(path: Path, expected_sha256: str):
    """Use exact existing production definitions in a bounded, speed-3 namespace.

    Only the four pure validators and their literal reason table are compiled.
    The Driver's exception class is mapped to this tool's ValueError subclass;
    no accepted result changes. Readiness at speeds4/5 is outside this adapter.
    """
    raw, source_label, resolution = _production_source(path, expected_sha256)
    source = raw.decode("utf-8-sig")
    tree = ast.parse(source, filename=source_label)
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
    exec(compile(ast.Module(body=selected, type_ignores=[]), source_label, "exec"), namespace)
    pins = {getattr(node, "name", "_TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS"):
            hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest() for node in selected}
    return SimpleNamespace(**{name: namespace[name] for name in names}, source_resolution=resolution), pins


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
